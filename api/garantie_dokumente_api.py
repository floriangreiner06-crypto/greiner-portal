"""
API: Garantie-Dokumente (Handbücher, Richtlinien, Rundschreiben)
================================================================
Liste aus DB, Upload für berechtigte User, PDF-Auslieferung aus Upload-Ordner oder Legacy-Sync.
"""
import os
import re
import logging
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user

from api.db_connection import get_db

logger = logging.getLogger(__name__)

bp = Blueprint("garantie_dokumente_api", __name__, url_prefix="/api/garantie")


def _upload_dir():
    """Pfad zum Upload-Verzeichnis (data/uploads/garantie)."""
    root = current_app.root_path if current_app else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "data", "uploads", "garantie")


def _legacy_dir():
    """Pfad zum Legacy-Sync-Verzeichnis (docs/.../garantie)."""
    root = current_app.root_path if current_app else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "docs", "workstreams", "werkstatt", "garantie")


def get_garantie_pdf_path(filename: str) -> str | None:
    """
    Gibt den Dateipfad für ein Garantie-PDF zurück.
    Zuerst data/uploads/garantie, dann Legacy docs/.../garantie.
    """
    basename = os.path.basename(filename).strip()
    if not basename or not basename.lower().endswith(".pdf"):
        return None
    for base_dir in (_upload_dir(), _legacy_dir()):
        path = os.path.join(base_dir, basename)
        if os.path.isfile(path):
            return path
    return None


def _can_upload():
    """Darf der aktuelle User Dokumente hochladen? (admin oder Feature garantie_dokumente_upload)"""
    if not current_user.is_authenticated:
        return False
    if hasattr(current_user, "can_access_feature"):
        if current_user.can_access_feature("admin"):
            return True
        if current_user.can_access_feature("garantie_dokumente_upload"):
            return True
    return False


def _safe_filename(name: str) -> str:
    """Nur erlaubte Zeichen für Dateinamen (PDF)."""
    name = (name or "").strip()
    if not name.lower().endswith(".pdf"):
        name = name + ".pdf" if name else "dokument.pdf"
    # Erlaubt: Buchstaben, Ziffern, Leerzeichen, Punkt, Bindestrich, Unterstrich
    base = os.path.splitext(name)[0]
    ext = os.path.splitext(name)[1].lower()
    base = re.sub(r"[^\w\s.\-]", "", base)
    base = base.strip() or "dokument"
    return base[:240] + ext


@bp.route("/dokumente", methods=["GET"])
@login_required
def list_dokumente():
    """
    GET /api/garantie/dokumente
    Liste aller Garantie-Dokumente aus DB mit vorhanden=True/False (Datei auf Server).
    Optional: typ=handbuch|richtlinie|rundschreiben, marke=...
    """
    typ = request.args.get("typ")
    marke = request.args.get("marke")
    try:
        conn = get_db()
        cursor = conn.cursor()
        sql = "SELECT id, dateiname, titel, marke, stand, typ, created_at, created_by FROM garantie_dokumente WHERE 1=1"
        params = []
        if typ:
            sql += " AND typ = %s"
            params.append(typ)
        if marke:
            sql += " AND (marke ILIKE %s OR marke IS NULL)"
            params.append(f"%{marke}%")
        sql += " ORDER BY typ, marke NULLS LAST, titel"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        upload_dir = _upload_dir()
        legacy_dir = _legacy_dir()
        result = []
        for row in rows:
            r = dict(row) if hasattr(row, "keys") else {
                "id": row[0], "dateiname": row[1], "titel": row[2], "marke": row[3],
                "stand": row[4], "typ": row[5], "created_at": row[6].isoformat() if row[6] else None,
                "created_by": row[7],
            }
            path_upload = os.path.join(upload_dir, row[1])
            path_legacy = os.path.join(legacy_dir, row[1])
            r["vorhanden"] = os.path.isfile(path_upload) or os.path.isfile(path_legacy)
            result.append(r)
        return jsonify({"success": True, "dokumente": result, "can_upload": _can_upload()})
    except Exception as e:
        logger.exception("Garantie-Dokumente Liste: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/dokumente/upload", methods=["POST"])
@login_required
def upload_dokument():
    """
    POST /api/garantie/dokumente/upload
    Form: file (PDF), titel, marke, stand, typ (handbuch|richtlinie|rundschreiben).
    Nur für User mit admin oder garantie_dokumente_upload.
    """
    if not _can_upload():
        return jsonify({"success": False, "error": "Keine Berechtigung zum Hochladen"}), 403

    if "file" not in request.files:
        return jsonify({"success": False, "error": "Keine Datei angegeben"}), 400
    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"success": False, "error": "Keine Datei ausgewählt"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"success": False, "error": "Nur PDF-Dateien erlaubt"}), 400

    titel = (request.form.get("titel") or file.filename).strip() or "Dokument"
    marke = (request.form.get("marke") or "").strip() or None
    stand = (request.form.get("stand") or "").strip() or None
    typ = (request.form.get("typ") or "handbuch").strip().lower()
    if typ not in ("handbuch", "richtlinie", "rundschreiben"):
        typ = "handbuch"

    dateiname = _safe_filename(file.filename)
    upload_dir = _upload_dir()
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, dateiname)

    try:
        file.save(file_path)
    except Exception as e:
        logger.exception("Garantie-Upload Speichern: %s", e)
        return jsonify({"success": False, "error": "Datei konnte nicht gespeichert werden"}), 500

    username = getattr(current_user, "username", None) or getattr(current_user, "name", None) or "unknown"
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO garantie_dokumente (dateiname, titel, marke, stand, typ, created_by, updated_at, updated_by)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
            ON CONFLICT (dateiname) DO UPDATE SET
                titel = EXCLUDED.titel,
                marke = EXCLUDED.marke,
                stand = EXCLUDED.stand,
                typ = EXCLUDED.typ,
                updated_at = NOW(),
                updated_by = EXCLUDED.updated_by
            """,
            (dateiname, titel, marke, stand, typ, username, username),
        )
        conn.commit()
        cursor.execute("SELECT id, dateiname, titel, marke, stand, typ FROM garantie_dokumente WHERE dateiname = %s", (dateiname,))
        row = cursor.fetchone()
        conn.close()
        out = {"id": row[0], "dateiname": row[1], "titel": row[2], "marke": row[3], "stand": row[4], "typ": row[5]}
        return jsonify({"success": True, "dokument": out})
    except Exception as e:
        logger.exception("Garantie-Dokument DB: %s", e)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return jsonify({"success": False, "error": "Datenbankfehler"}), 500
