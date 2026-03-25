"""
Fahrzeuganlage API – Fahrzeugschein-OCR (AWS Bedrock) + Scan-Archiv + Dublettencheck.
Phase 1 MVP: Upload → OCR → editierbare Maske → Copy nach Locosoft.
"""

import os
import re
import json
import logging
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user

from api.db_connection import get_db
from api.db_utils import db_session

logger = logging.getLogger(__name__)

# Blueprint
fahrzeuganlage_api = Blueprint(
    "fahrzeuganlage_api", __name__, url_prefix="/api/fahrzeuganlage"
)


@fahrzeuganlage_api.before_request
def _require_fahrzeuganlage_feature():
    """Einheitlicher Zugriffsschutz für alle Fahrzeuganlage-API-Endpunkte (immer JSON)."""
    if not getattr(current_user, "is_authenticated", False):
        return jsonify({"error": "Nicht angemeldet"}), 401
    if not (hasattr(current_user, "can_access_feature") and current_user.can_access_feature("fahrzeuganlage")):
        return jsonify({"error": "Keine Berechtigung für Fahrzeuganlage"}), 403


@fahrzeuganlage_api.errorhandler(Exception)
def _json_error(e):
    """Stellt sicher, dass Fehler als JSON zurückgegeben werden (kein HTML). Keine Exception-Details an Client (Sicherheit)."""
    logger.exception("Fahrzeuganlage API Fehler")
    return jsonify({"error": "Interner Fehler (Details nur im Server-Log)"}), 500

# Upload-Verzeichnis (DSGVO: lokal auf Server)
UPLOAD_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "uploads", "fahrzeugscheine"
)


def _load_bedrock_credentials():
    """Lädt aws_bedrock aus config/credentials.json."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "config", "credentials.json"
    )
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("aws_bedrock")
    except Exception as e:
        logger.warning("aws_bedrock aus credentials.json nicht geladen: %s", e)
        return None


def _load_dat_config():
    """Lädt DAT-Konfiguration: zuerst Umgebung (config/.env), optional Override aus credentials.json."""
    cfg = {
        "base_url": os.environ.get("DAT_URL", "").rstrip("/"),
        "username": os.environ.get("DAT_USER", ""),
        "password": os.environ.get("DAT_PASSWORD", ""),
        "customer_number": os.environ.get("DAT_CUSTOMER_NUMBER", ""),
    }
    path = os.path.join(os.path.dirname(__file__), "..", "config", "credentials.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            dat = data.get("dat_vin") or data.get("dat")
            if isinstance(dat, dict):
                if dat.get("base_url"):
                    cfg["base_url"] = dat["base_url"].rstrip("/")
                if dat.get("username"):
                    cfg["username"] = dat["username"]
                if dat.get("password"):
                    cfg["password"] = dat["password"]
                if dat.get("customer_number") is not None:
                    cfg["customer_number"] = str(dat["customer_number"])
                if dat.get("token"):
                    cfg["token"] = dat["token"].strip()
        except Exception as e:
            logger.debug("DAT-Config aus credentials.json: %s", e)
    return cfg


def _ocr_result_to_row(ocr: dict, image_path: str, scanned_by: str):
    """Mappt OCR-JSON auf DB-Spalten (flach)."""
    halter = ocr.get("halter") or {}
    conf = ocr.get("confidence") or {}
    gesamt = conf.get("gesamt")
    return {
        "scanned_by": scanned_by,
        "image_path": image_path,
        "kennzeichen": ocr.get("kennzeichen"),
        "fin": ocr.get("fin"),
        "erstzulassung": ocr.get("erstzulassung"),
        "marke": ocr.get("marke"),
        "handelsbezeichnung": ocr.get("handelsbezeichnung"),
        "typ_variante_version": ocr.get("typ_variante_version"),
        "hsn": ocr.get("hsn"),
        "tsn": ocr.get("tsn"),
        "hubraum_ccm": ocr.get("hubraum_ccm"),
        "leistung_kw": ocr.get("leistung_kw"),
        "kraftstoff": ocr.get("kraftstoff"),
        "farbe": ocr.get("farbe"),
        "naechste_hu": ocr.get("naechste_hu"),
        "halter_name": halter.get("nachname"),
        "halter_vorname": halter.get("vorname"),
        "halter_strasse": halter.get("strasse"),
        "halter_plz": halter.get("plz"),
        "halter_ort": halter.get("ort"),
        "status": "scanned",
        "ocr_confidence": gesamt if isinstance(gesamt, (int, float)) else None,
        "raw_ocr_response": json.dumps(ocr, ensure_ascii=False),
        "processing_region": "LM Studio (RZ)" if (ocr.get("_usage") or {}).get("backend") == "lm_studio" else "eu-central-1",
    }


def _row_to_dict(row):
    """HybridRow oder dict → dict für JSON."""
    if hasattr(row, "keys"):
        return {k: row.get(k) for k in row.keys()}
    return dict(row) if row else None


def _serialize_scan(row):
    """Scan-Zeile für JSON (Datetime → ISO string)."""
    d = _row_to_dict(row)
    if not d:
        return None
    for key in list(d.keys()):
        v = d[key]
        if hasattr(v, "isoformat"):
            d[key] = v.isoformat()
    return d


@fahrzeuganlage_api.route("/health", methods=["GET"])
@login_required
def health():
    """Health-Check: Bedrock + DB."""
    result = {"bedrock": False, "db": False}
    creds = _load_bedrock_credentials()
    if creds and creds.get("secret_access_key", "").strip() not in (
        "",
        ">>> HIER SECRET KEY EINTRAGEN <<<",
        ">>> HIER EINTRAGEN <<<",
    ):
        try:
            from api.fahrzeugschein_scanner import FahrzeugscheinScanner

            scanner = FahrzeugscheinScanner(creds)
            result["bedrock"] = scanner.health_check()
        except Exception as e:
            logger.exception("Bedrock health check failed")
            # Keine Exception-Details an Client (Risiko: nie Credentials in str(e) durchreichen)
            result["bedrock_error"] = "Bedrock nicht erreichbar (Details nur im Server-Log)"
    else:
        result["bedrock_error"] = "aws_bedrock nicht konfiguriert (Secret Key fehlt)"
    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM fahrzeugschein_scans LIMIT 1")
            cur.fetchone()
        result["db"] = True
    except Exception as e:
        logger.exception("DB health check failed")
        result["db_error"] = "Datenbank nicht erreichbar (Details nur im Server-Log)"
    return jsonify(result)


def _pdf_first_page_to_image_bytes(pdf_path: str):
    """Konvertiert die erste Seite eines PDFs in PNG-Bytes (für OCR). Erfordert PyMuPDF (pip install pymupdf)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise RuntimeError("PDF-Unterstützung erfordert PyMuPDF: pip install pymupdf")
    doc = fitz.open(pdf_path)
    try:
        if len(doc) == 0:
            raise ValueError("PDF hat keine Seiten")
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)  # 2x für bessere OCR
        return pix.tobytes("png")
    finally:
        doc.close()


@fahrzeuganlage_api.route("/scan", methods=["POST"])
@login_required
def scan():
    """Bild oder PDF hochladen, OCR ausführen, in DB speichern."""
    file = request.files.get("image") or request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "Kein Bild/PDF angehängt"}), 400
    ext = (os.path.splitext(file.filename)[1] or "").lower()
    if ext not in (".jpg", ".jpeg", ".png", ".pdf"):
        return jsonify({"error": "Nur JPG, PNG oder PDF erlaubt"}), 400
    if ext == ".pdf":
        media_type = "image/png"  # PDF wird als erste Seite → PNG an Scanner übergeben
    else:
        media_type = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    try:
        file.save(file_path)
        if ext == ".pdf":
            image_bytes = _pdf_first_page_to_image_bytes(file_path)
        else:
            image_bytes = open(file_path, "rb").read()
    except Exception as e:
        logger.exception("Speichern/Verarbeiten des Uploads fehlgeschlagen")
        return jsonify({"error": str(e)}), 500
    # Zuerst LM Studio (Vision), bei Fehler Fallback Bedrock
    from api.fahrzeugschein_scanner import scan_with_lm_studio

    ocr = scan_with_lm_studio(image_bytes, media_type=media_type)
    if ocr is None:
        creds = _load_bedrock_credentials()
        if creds and creds.get("secret_access_key") and "EINTRAGEN" not in (creds.get("secret_access_key") or ""):
            try:
                from api.fahrzeugschein_scanner import FahrzeugscheinScanner
                scanner = FahrzeugscheinScanner(creds)
                ocr = scanner.scan(image_bytes, media_type=media_type)
            except Exception as e:
                logger.exception("OCR (Bedrock-Fallback) fehlgeschlagen: %s", e)
                return jsonify({"error": f"OCR fehlgeschlagen: {e}"}), 500
        if ocr is None:
            return jsonify({
                "error": "OCR fehlgeschlagen: LM Studio (Vision) nicht erreichbar oder ohne gültige Antwort; Bedrock nicht verfügbar oder nicht konfiguriert. Bitte config/credentials.json → lm_studio (vision_model z. B. qwen/qwen3-vl-4b) prüfen."
            }), 503
    rel_path = os.path.join("fahrzeugscheine", safe_name)  # Originaldatei (JPG/PNG/PDF)
    row_data = _ocr_result_to_row(
        ocr, rel_path, getattr(current_user, "username", "") or ""
    )
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO fahrzeugschein_scans (
                scanned_by, image_path, kennzeichen, fin, erstzulassung,
                marke, handelsbezeichnung, typ_variante_version, hsn, tsn,
                hubraum_ccm, leistung_kw, kraftstoff, farbe, naechste_hu,
                halter_name, halter_vorname, halter_strasse, halter_plz, halter_ort,
                status, ocr_confidence, raw_ocr_response, processing_region
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id
            """,
            (
                row_data["scanned_by"],
                row_data["image_path"],
                row_data["kennzeichen"],
                row_data["fin"],
                row_data["erstzulassung"],
                row_data["marke"],
                row_data["handelsbezeichnung"],
                row_data["typ_variante_version"],
                row_data["hsn"],
                row_data["tsn"],
                row_data["hubraum_ccm"],
                row_data["leistung_kw"],
                row_data["kraftstoff"],
                row_data["farbe"],
                row_data["naechste_hu"],
                row_data["halter_name"],
                row_data["halter_vorname"],
                row_data["halter_strasse"],
                row_data["halter_plz"],
                row_data["halter_ort"],
                row_data["status"],
                row_data["ocr_confidence"],
                row_data["raw_ocr_response"],
                row_data["processing_region"],
            ),
        )
        row = cur.fetchone()
        scan_id = row[0] if row else None
        conn.commit()
    out = _ocr_result_to_row(ocr, rel_path, row_data["scanned_by"])
    out["halter"] = ocr.get("halter")
    out["confidence"] = ocr.get("confidence")
    return jsonify({"id": scan_id, "data": out}), 201


@fahrzeuganlage_api.route("/scan/<int:scan_id>", methods=["GET"])
@login_required
def get_scan(scan_id):
    """Einzelnen Scan abrufen."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM fahrzeugschein_scans WHERE id = %s", (scan_id,)
        )
        row = cur.fetchone()
    if not row:
        return jsonify({"error": "Scan nicht gefunden"}), 404
    return jsonify(_serialize_scan(row))


@fahrzeuganlage_api.route("/scan/<int:scan_id>", methods=["PUT"])
@login_required
def update_scan(scan_id):
    """Scan-Daten nach manueller Korrektur aktualisieren."""
    data = request.get_json(silent=True) or {}
    allowed = {
        "kennzeichen", "fin", "erstzulassung", "marke", "handelsbezeichnung",
        "typ_variante_version", "hsn", "tsn", "hubraum_ccm", "leistung_kw",
        "kraftstoff", "farbe", "naechste_hu", "halter_name", "halter_vorname",
        "halter_strasse", "halter_plz", "halter_ort", "notes",
    }
    updates = {k: data.get(k) for k in allowed if k in data}
    if not updates:
        return jsonify({"error": "Keine erlaubten Felder"}), 400
    set_clause = ", ".join(f"{k} = %s" for k in updates)
    params = list(updates.values()) + [scan_id]
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE fahrzeugschein_scans SET {set_clause} WHERE id = %s",
            params,
        )
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Scan nicht gefunden"}), 404
        cur.execute("SELECT * FROM fahrzeugschein_scans WHERE id = %s", (scan_id,))
        row = cur.fetchone()
    return jsonify(_serialize_scan(row))


@fahrzeuganlage_api.route("/history", methods=["GET"])
@login_required
def history():
    """Letzte Scans (Pagination)."""
    limit = min(int(request.args.get("limit", 50)), 100)
    offset = max(0, int(request.args.get("offset", 0)))
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, scan_date, kennzeichen, fin, marke, handelsbezeichnung,
                   halter_name, halter_vorname, status, ocr_confidence
            FROM fahrzeugschein_scans
            ORDER BY scan_date DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        rows = cur.fetchall()
    return jsonify({"items": [_serialize_scan(r) for r in rows]})


def _loco_row_to_compare(row):
    """Mappt loco_vehicles-Zeile (+ loco_makes) auf Vergleichs-Felder (wie Scan)."""
    def g(k):
        if hasattr(row, "get"):
            return row.get(k)
        return None
    first_reg = g("first_registration_date")
    if first_reg and hasattr(first_reg, "strftime"):
        first_reg = first_reg.strftime("%d.%m.%Y")
    elif first_reg is not None:
        s = str(first_reg).strip()
        if len(s) >= 10 and s[4] == "-" and s[7] == "-":  # YYYY-MM-DD
            first_reg = s[8:10] + "." + s[5:7] + "." + s[0:4]
        else:
            first_reg = s
    # Marke: aus loco_makes.description (JOIN), Fallback free_form_make_text
    marke = (g("make_description") or g("free_form_make_text") or "").strip()
    return {
        "vehicle_number": g("internal_number"),
        "kennzeichen": (g("license_plate") or "").strip(),
        "fin": (g("vin") or "").strip(),
        "marke": marke,
        "handelsbezeichnung": (g("free_form_model_text") or "").strip(),
        "erstzulassung": first_reg or "",
        "hsn": str(g("german_kba_hsn") or "").strip(),
        "tsn": str(g("german_kba_tsn") or "").strip(),
        "hubraum_ccm": g("cubic_capacity"),
        "leistung_kw": g("power_kw"),
        "farbe": (g("body_paint_description") or "").strip(),
    }


def _normalize_kennzeichen(kz: str) -> str:
    """Kennzeichen für Abgleich: Leerzeichen entfernt, groß."""
    if not kz or not isinstance(kz, str):
        return ""
    return (kz.strip().upper().replace(" ", "").replace("-", "") or "")


@fahrzeuganlage_api.route("/vin-decode", methods=["GET", "POST"])
@login_required
def vin_decode():
    """Manuelle VIN-Eingabe: prüfen, ggf. korrigieren (Checkdigit/OCR-Fehler) und per AWS Bedrock (Claude) entschlüsseln.
    Liefert: korrigierte VIN, Validität, Decode-Hinweise (WMI, Hersteller, Modelljahr).
    """
    raw = None
    if request.method == "POST" and request.is_json:
        raw = (request.get_json() or {}).get("vin")
    if raw is None:
        raw = request.args.get("vin") or ""
    raw = (raw or "").strip()
    if not raw:
        return jsonify({"error": "Parameter vin fehlt"}), 400

    from api.fahrzeugschein_scanner import (
        _normalize_vin,
        _vin_auto_correct_one_char,
        _vin_valid,
        decode_vin_with_bedrock,
    )

    normalized = _normalize_vin(raw)
    if not normalized or len(normalized) != 17:
        return jsonify({
            "vin": None,
            "valid": False,
            "error": "VIN muss 17 Zeichen haben (nur A–H, J–N, P–R, T–Z und 0–9).",
            "decode": None,
        })

    corrected = _vin_auto_correct_one_char(normalized) or normalized
    valid = _vin_valid(corrected)

    decode = None
    creds = _load_bedrock_credentials()
    if creds and creds.get("secret_access_key", "").strip() not in ("", ">>> HIER SECRET KEY EINTRAGEN <<<", ">>> HIER EINTRAGEN <<<"):
        try:
            from api.fahrzeugschein_scanner import FahrzeugscheinScanner
            scanner = FahrzeugscheinScanner(creds)
            decode = decode_vin_with_bedrock(scanner.client, scanner.model_id, corrected)
        except Exception as e:
            logger.warning("VIN-Decode (Bedrock) in Route: %s", e)
            decode = {"fehler": str(e)}

    return jsonify({
        "vin": corrected,
        "valid": valid,
        "corrected": corrected != raw.replace(" ", "").replace("-", "").upper().strip(),
        "decode": decode,
    })


@fahrzeuganlage_api.route("/dat-vin-lookup", methods=["GET", "POST"])
@login_required
def dat_vin_lookup():
    """VIN bei DAT (SilverDAT myClaim) abfragen – liefert Marke, Handelsbezeichnung, HSN/TSN, DAT-Europa-Code.
    Pro Abruf fallen Kosten an (z. B. ~1 €). Konfiguration: DAT_URL, DAT_USER, DAT_PASSWORD in config/.env.
    """
    raw = None
    if request.method == "POST" and request.is_json:
        raw = (request.get_json() or {}).get("vin")
    if raw is None:
        raw = request.args.get("vin") or ""
    raw = (raw or "").strip()
    if not raw:
        return jsonify({"success": False, "error": "Parameter vin fehlt"}), 400

    from api.fahrzeugschein_scanner import _normalize_vin, _vin_auto_correct_one_char

    normalized = _normalize_vin(raw)
    if not normalized or len(normalized) != 17:
        return jsonify({"success": False, "error": "VIN muss 17 Zeichen haben (gültige Zeichen A–H, J–N, P–R, T–Z, 0–9)."})

    vin17 = _vin_auto_correct_one_char(normalized) or normalized

    cfg = _load_dat_config()
    if not cfg.get("base_url") or not cfg.get("username") or not cfg.get("password"):
        return jsonify({
            "success": False,
            "error": "DAT nicht konfiguriert. Bitte DAT_URL, DAT_USER und DAT_PASSWORD in config/.env setzen.",
        })

    try:
        from api.dat_vin_client import DatVinClient
        client = DatVinClient(cfg)
        result = client.vin_lookup(vin17)
    except Exception as e:
        logger.exception("DAT VIN-Lookup fehlgeschlagen")
        return jsonify({"success": False, "error": str(e)})

    return jsonify(result)


@fahrzeuganlage_api.route("/check-duplicate", methods=["GET"])
@login_required
def check_duplicate():
    """Dublettencheck gegen Locosoft (loco_vehicles). Bei Treffer: Locosoft-Daten für Vergleich zurückgeben.
    Fallback: Kein Treffer per FIN/Kennzeichen → Suche nur per Kennzeichen (normalisiert), damit bei
    falsch erkannter VIN trotzdem die Locosoft-Dublette angezeigt und VIN übernommen werden kann."""
    fin = (request.args.get("fin") or "").strip()
    kennzeichen = (request.args.get("kennzeichen") or "").strip()
    if not fin and not kennzeichen:
        return jsonify({"exists": False, "message": "FIN oder Kennzeichen angeben"})
    sql_base = """
            SELECT v.internal_number, v.vin, v.license_plate,
                   COALESCE(NULLIF(TRIM(m.description), ''), v.free_form_make_text) AS make_description,
                   v.free_form_make_text, v.free_form_model_text,
                   v.first_registration_date, v.german_kba_hsn, v.german_kba_tsn,
                   v.cubic_capacity, v.power_kw, v.body_paint_description
            FROM loco_vehicles v
            LEFT JOIN loco_makes m ON m.make_number = v.make_number
    """
    matched_by = "fin_or_kennzeichen"
    with db_session() as conn:
        cur = conn.cursor()
        try:
            if fin and kennzeichen:
                cur.execute(
                    sql_base + """
                    WHERE (v.vin IS NOT NULL AND TRIM(v.vin) = %s)
                       OR (v.license_plate IS NOT NULL AND TRIM(v.license_plate) = %s)
                    LIMIT 1
                    """,
                    (fin, kennzeichen),
                )
            elif fin:
                cur.execute(
                    sql_base + """
                    WHERE v.vin IS NOT NULL AND TRIM(v.vin) = %s
                    LIMIT 1
                    """,
                    (fin,),
                )
            else:
                cur.execute(
                    sql_base + """
                    WHERE v.license_plate IS NOT NULL AND TRIM(v.license_plate) = %s
                    LIMIT 1
                    """,
                    (kennzeichen,),
                )
            rows = cur.fetchall()
            # Fallback 1: Kein Treffer, aber Kennzeichen vorhanden → nur nach Kennzeichen suchen (normalisiert)
            if not rows and kennzeichen:
                kz_norm = _normalize_kennzeichen(kennzeichen)
                if kz_norm:
                    cur.execute(
                        sql_base + """
                        WHERE v.license_plate IS NOT NULL
                          AND REPLACE(REPLACE(TRIM(UPPER(v.license_plate)), ' ', ''), '-', '') = %s
                        LIMIT 2
                        """,
                        (kz_norm,),
                    )
                    rows_fallback = cur.fetchall()
                    if len(rows_fallback) == 1:
                        rows = rows_fallback
                        matched_by = "kennzeichen"
            # Fallback 2: VIN um 1–2 Zeichen falsch (typisch OCR: C/S, G/Z) → Fuzzy-VIN-Suche (PostgreSQL fuzzystrmatch)
            if not rows and fin:
                fin_clean = re.sub(r"[\s\-\.]", "", fin.strip().upper())
                if len(fin_clean) == 17:
                    try:
                        cur.execute(
                            sql_base + """
                            WHERE v.vin IS NOT NULL AND LENGTH(TRIM(v.vin)) = 17
                              AND levenshtein(TRIM(v.vin), %s) <= 2
                            LIMIT 2
                            """,
                            (fin_clean,),
                        )
                        rows_vin = cur.fetchall()
                        if len(rows_vin) == 1:
                            rows = rows_vin
                            matched_by = "vin_fuzzy"
                    except Exception:
                        pass  # fuzzystrmatch evtl. nicht installiert
        except Exception as e:
            logger.warning("Dublettencheck loco_vehicles fehlgeschlagen: %s", e)
            return jsonify({"exists": False, "error": str(e)})
    if not rows:
        return jsonify({"exists": False})
    first = rows[0]
    vn = first.get("internal_number") if hasattr(first, "get") else first[0]
    locosoft_data = _loco_row_to_compare(first)
    return jsonify({
        "exists": True,
        "vehicle_number": vn,
        "locosoft_data": locosoft_data,
        "matched_by": matched_by,
    })
