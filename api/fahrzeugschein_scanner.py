"""
Fahrzeugschein-Scanner via AWS Bedrock (Claude) – OCR für Zulassungsbescheinigung Teil 1 (ZB1).
DSGVO: Verarbeitung in eu-central-1 (Frankfurt).
Erstzulassung (EZ) ist kritisch – Prompt und Nachbearbeitung darauf ausgerichtet.
"""

import json
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

SCAN_PROMPT = """Analysiere diesen deutschen Fahrzeugschein (Zulassungsbescheinigung Teil 1, ZB1).
Extrahiere ALLE Felder präzise. Antworte AUSSCHLIESSLICH mit validem JSON, kein Markdown, keine Erklärung.

=== OBERSTE PRIORITÄT: VIN (FIN) und Erstzulassung (EZ) ===
Der ZB1 hat eine Zwei-Spalten-Struktur: links Bezeichnungen (A., B., C., D., E., …), rechts die Werte. Lies VIN und EZ NUR aus der jeweiligen Zeile.

1) fin (VIN/FIN) – KRITISCH:
   - NUR das Feld „E. Fahrzeug-Identifizierungsnummer“: In der Zeile, in der links „E.“ bzw. „Fahrzeug-Identifizierungsnummer“ steht, steht rechts die VIN. GENAU diese 17 Zeichen übernehmen.
   - VIN ist weltweit immer genau 17 Zeichen (ISO 3779): nur Buchstaben A–H, J–N, P–R, T–Z und Ziffern 0–9 (keine I, O, Q).
   - NICHT verwenden: Barcode-Nummer, andere lange Nummern auf dem Schein, Nummer aus einer anderen Zeile. Wenn unsicher: Zeile mit „E.“ suchen und nur den Wert in dieser Zeile nehmen.
   - Zeichen GENAU ablesen – auf dem ZB1 oft verwechselt: C und S, G und Z, 0 (Ziffer) und Z (Buchstabe), 0 und O, 1 und I, 5 und S, 8 und B. Jeden der 17 Zeichen einzeln prüfen; bei VW-VINs kommen S und Z oft vor – auch Z nicht als 0 lesen.

2) erstzulassung (EZ) – KRITISCH:
   - NUR das Feld „B. Datum der ersten Zulassung“: In der Zeile, in der links „B.“ bzw. „Datum der ersten Zulassung“ steht, steht rechts das Datum. Format TT.MM.JJJJ. Genau dieses Datum verwenden.
   - NICHT verwenden: Ausstellungsdatum des Dokuments (oft links oben), „nächste HU“, „Gültig bis“ oder irgendein anderes Datum. Nur das Datum in der Zeile von „B. Datum der ersten Zulassung“.
   - Auf dem ZB1 werden die Ziffern 3 und 5 (und ggf. 8) im Datum oft verwechselt – Monat (MM) und Tag (TT) einzeln genau prüfen (z. B. 05 nicht als 03 lesen).

=== JSON-Ausgabe ===
{
    "kennzeichen": "...",
    "fin": "...",
    "erstzulassung": "TT.MM.JJJJ",
    "marke": "...",
    "handelsbezeichnung": "...",
    "typ_variante_version": "...",
    "hsn": "...",
    "tsn": "...",
    "hubraum_ccm": 0,
    "leistung_kw": 0,
    "kraftstoff": "Benzin|Diesel|Elektro|Hybrid|...",
    "farbe": "...",
    "fahrzeugklasse": "M1|...",
    "aufbauart": "...",
    "sitze": 0,
    "zulaessige_gesamtmasse_kg": 0,
    "naechste_hu": "MM/JJJJ",
    "halter": {
        "nachname": "...",
        "vorname": "...",
        "strasse": "...",
        "plz": "...",
        "ort": "..."
    },
    "confidence": {
        "fin": 0.99,
        "kennzeichen": 0.98,
        "halter": 0.95,
        "gesamt": 0.97
    }
}

Weitere Felder:
- kennzeichen: Feld „A. Amtliches Kennzeichen“ (Kfz-Kennzeichen, z.B. „BI VL 9568“). NICHT Aktenzeichen oder andere Nummern.
- hsn: NUR die 4-stellige HSN (z.B. 0603) aus dem HSN-Feld des ZB1.
- tsn: NUR die genau 3 Zeichen TSN (z.B. CQO, CKX) aus dem TSN-Feld – Buchstaben und/oder Ziffern, insgesamt genau 3. NICHT die lange Typ/Variante/Version-Zeile (z.B. e13*2018/858*00140*03 oder andere lange Codes) verwenden; die steht woanders. TSN ist immer 3 Zeichen.
- Datum erstzulassung TT.MM.JJJJ, naechste_hu MM/JJJJ.
- Bei unlesbar: null; confidence 0.0."""

# Zweiter, fokussierter Prompt nur für die VIN – für präzisere Zeichenerkennung (kritisch für Neuanlage)
VIN_ONLY_PROMPT = """Dieses Bild zeigt einen deutschen Fahrzeugschein (ZB1). Gib NUR die 17 Zeichen der Fahrzeug-Identifizierungsnummer (Feld E) aus, ohne Leerzeichen, ohne Erklärung. Nur die 17 Zeichen. Häufige Lesefehler: C/S, G/Z, und Z (Buchstabe) nicht als 0 (Ziffer) lesen – jeden Buchstaben einzeln genau prüfen. Antworte nur mit den 17 Zeichen."""


# VIN (ISO 3779): I, O, Q sind nicht erlaubt – typische OCR-Verwechslung mit 1, 0
VIN_FORBIDDEN_TO_VALID = str.maketrans("IOQ", "100")

# Transliteration für Checkdigit (ISO 3779): A=1..H=8, J=1..N=5, P=7, R=9, S=2..Z=9; Ziffern unverändert
VIN_TRANSLIT = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
    "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9,
}
for d in "0123456789":
    VIN_TRANSLIT[d] = int(d)
# Gewichte Position 1–17 (Position 9 = Checkdigit hat Gewicht 0)
VIN_WEIGHTS = (8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2)

# Typische OCR-Verwechslungen für Auto-Korrektur (0 und Z auf dem Schein oft verwechselt)
VIN_CONFUSION_PAIRS = [("C", "S"), ("G", "Z"), ("S", "C"), ("Z", "G"), ("B", "8"), ("8", "B"), ("5", "S"), ("S", "5"), ("0", "Z"), ("Z", "0")]


def _vin_check_digit(vin17: str) -> str:
    """Berechnet den gültigen Checkdigit für Position 9 (ISO 3779). Bei Rest 10 → 'X'."""
    if not vin17 or len(vin17) != 17:
        return ""
    total = 0
    for i, c in enumerate(vin17.upper()):
        if c not in VIN_TRANSLIT:
            return ""
        total += VIN_TRANSLIT[c] * VIN_WEIGHTS[i]
    r = total % 11
    return "X" if r == 10 else str(r)


def _vin_valid(vin17: str) -> bool:
    """Prüft, ob die VIN einen gültigen Checkdigit an Position 9 hat (ISO 3779)."""
    if not vin17 or len(vin17) != 17:
        return False
    expected = _vin_check_digit(vin17)
    return expected != "" and vin17[8].upper() == expected


def _vin_try_correct_at(vin_upper: str, positions: list[int]) -> str | None:
    """Versucht an den gegebenen Positionen (0-based) je eine Ersetzung aus VIN_CONFUSION_PAIRS. Rekursion für mehrere Stellen."""
    if not positions:
        return vin_upper if _vin_valid(vin_upper) else None
    pos = positions[0]
    rest = positions[1:]
    for a, b in VIN_CONFUSION_PAIRS:
        if vin_upper[pos] != a and vin_upper[pos] != b:
            continue
        replacement = b if vin_upper[pos] == a else a
        candidate = vin_upper[:pos] + replacement + vin_upper[pos + 1 :]
        if rest:
            result = _vin_try_correct_at(candidate, rest)
            if result:
                return result
        elif _vin_valid(candidate):
            return candidate
    return None


def _vin_auto_correct_one_char(vin17: str) -> str | None:
    """Versucht einen einzigen OCR-Fehler zu korrigieren (C/S, G/Z, B/8, 5/S). Gibt korrigierte VIN zurück oder None."""
    if not vin17 or len(vin17) != 17:
        return None
    if _vin_valid(vin17):
        return vin17
    vin_upper = vin17.upper()
    # Zuerst: Position 9 (Checkdigit) durch berechneten Wert ersetzen – oft falsch gelesen
    correct_check = _vin_check_digit(vin_upper)
    if correct_check and vin_upper[8] != correct_check:
        candidate = vin_upper[:8] + correct_check + vin_upper[9:]
        if _vin_valid(candidate):
            logger.info("VIN Auto-Korrektur (Checkdigit): %s → %s", vin17, candidate)
            return candidate
    # Dann: An jeder Position typische Verwechslungen durchprobieren (1 Zeichen)
    for pos in range(17):
        result = _vin_try_correct_at(vin_upper, [pos])
        if result:
            logger.info("VIN Auto-Korrektur (1 Zeichen): %s → %s", vin17, result)
            return result
    # Bis zu 2 Zeichen korrigieren (typisch: CG→SZ o.ä.)
    for i in range(17):
        for j in range(i + 1, 17):
            result = _vin_try_correct_at(vin_upper, [i, j])
            if result:
                logger.info("VIN Auto-Korrektur (2 Zeichen): %s → %s", vin17, result)
                return result
    return None


def _normalize_vin(raw: str):
    """Normalisiert VIN: Leerzeichen/Bindestriche entfernen, I/O/Q → 1/0/0 (ISO 3779), max. 17 Zeichen."""
    if not raw or not isinstance(raw, str):
        return None
    s = re.sub(r"[\s\-\.]", "", raw.strip().upper())
    if not s:
        return None
    s = s[:17]
    s = s.translate(VIN_FORBIDDEN_TO_VALID)
    return s if re.match(r"^[A-HJ-NPR-Z0-9]+$", s) else None


# Prompt für VIN-Entschlüsselung (nur Text, kein Bild): WMI + Modelljahr aus Struktur (ISO 3779)
VIN_DECODE_PROMPT = """Du bist ein VIN-Experte (ISO 3779). Decodiere diese 17-stellige Fahrzeug-Identifizierungsnummer (VIN) soweit möglich aus der Struktur.

VIN-Struktur (Kurz): Zeichen 1–3 = WMI (World Manufacturer Identifier), 4–8 = VDS, 9 = Prüfziffer, 10 = Modelljahr-Code, 11 = Werk, 12–17 = Seriennummer.
Modelljahr-Code (Position 10): A=1980, B=1981, … Y=2000, 1=2001, … 9=2009, A=2010, B=2011, … P=2023, R=2024, usw. (I,O,Q,U,Z nicht verwendet.)

Antworte NUR mit einem einzigen JSON-Objekt, kein Markdown, keine Erklärung:
{
  "wmi": "erste 3 Zeichen der VIN",
  "hersteller_hinweis": "bekannter Hersteller/Marke für diesen WMI (z.B. WVW=Volkswagen, WBA=BMW, ZFA=Fiat) oder null wenn unbekannt",
  "modelljahr": "Jahr aus Position 10 (z.B. 2023) oder null",
  "werk_hinweis": "optional: Hinweis zu Position 11 (Werk) wenn bekannt, sonst weglassen",
  "hinweis": "kurzer Satz auf Deutsch: was aus der VIN ablesbar ist (z.B. 'VW, Modelljahr ca. 2023')"
}

Wenn die VIN nicht genau 17 Zeichen hat oder ungültige Zeichen enthält, antworte mit: {"fehler": "VIN muss 17 Zeichen haben (ISO 3779)."}"""


def decode_vin_with_bedrock(client, model_id: str, vin17: str) -> dict | None:
    """Entschlüsselt eine VIN per AWS Bedrock (nur Text, kein Bild): WMI, Hersteller-Hinweis, Modelljahr.
    Gibt ein Dict mit hersteller_hinweis, modelljahr, hinweis etc. zurück oder None bei Fehler.
    """
    if not vin17 or len(vin17) != 17 or not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin17.upper()):
        return None
    vin17 = vin17.upper()
    try:
        resp = client.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": VIN_DECODE_PROMPT + "\n\nVIN: " + vin17,
                        }
                    ],
                }
            ],
            inferenceConfig={"maxTokens": 256, "temperature": 0.0},
        )
        text = (resp.get("output") or {}).get("message") or {}
        content = (text.get("content") or [])
        if not content:
            return None
        raw = (content[0].get("text") or "").strip()
        if "```" in raw:
            for part in raw.split("```"):
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    raw = part
                    break
        data = json.loads(raw)
        if data.get("fehler"):
            return {"fehler": data["fehler"]}
        return {
            "wmi": data.get("wmi"),
            "hersteller_hinweis": data.get("hersteller_hinweis"),
            "modelljahr": data.get("modelljahr"),
            "werk_hinweis": data.get("werk_hinweis"),
            "hinweis": data.get("hinweis"),
        }
    except Exception as e:
        logger.warning("VIN-Decode (Bedrock) fehlgeschlagen: %s", e)
        return None


def scan_with_lm_studio(image_bytes: bytes, media_type: str = "image/jpeg") -> dict | None:
    """
    Fahrzeugschein-OCR via LM Studio (Vision-Modell). Gleiche Struktur wie FahrzeugscheinScanner.scan().
    Returns dict mit fin, erstzulassung, halter, etc. oder None bei Fehler.
    """
    try:
        import base64
        from api.ai_api import lm_studio_client
    except Exception as e:
        logger.debug("LM Studio für Fahrzeugschein nicht verfügbar: %s", e)
        return None
    mt = media_type or "image/jpeg"
    b64 = base64.b64encode(image_bytes).decode("ascii")
    out = lm_studio_client.chat_completion_vision(b64, mt, SCAN_PROMPT, max_tokens=1024, temperature=0.0, timeout=90)
    if not out or not out.strip():
        return None
    result_text = out.strip()
    if "```" in result_text:
        for part in result_text.split("```"):
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                result_text = part
                break
    try:
        data = json.loads(result_text)
    except json.JSONDecodeError as e:
        logger.warning("LM Studio OCR: Kein gültiges JSON: %s", e)
        return None
    data["_usage"] = {"backend": "lm_studio"}
    # VIN normalisieren (wie Bedrock-Pfad)
    fin = data.get("fin")
    if fin is not None and isinstance(fin, str):
        normalized = _normalize_vin(fin)
        if normalized and len(normalized) == 17:
            if not _vin_valid(normalized):
                corrected = _vin_auto_correct_one_char(normalized)
                if corrected:
                    normalized = corrected
            data["fin"] = normalized
        else:
            fallback = re.sub(r"[\s\-\.]", "", fin.strip().upper())[:17]
            data["fin"] = fallback if fallback else None
    # Zweiter Call nur VIN (fokussiert)
    fin_primary = data.get("fin")
    vin_only = _scan_vin_only_lm_studio(image_bytes, mt)
    if vin_only and len(vin_only) == 17:
        data["fin"] = vin_only
        if vin_only != fin_primary:
            logger.info("VIN aus LM Studio VIN-Only übernommen: %s -> %s", fin_primary, vin_only)
    # Erstzulassung: Zukunft = OCR-Fehler
    ez = data.get("erstzulassung")
    if ez and isinstance(ez, str):
        ez_parsed = _parse_ez_date(ez.strip())
        if ez_parsed and ez_parsed > datetime.now().date():
            logger.warning("Erstzulassung in Zukunft (%s) – auf null gesetzt", ez)
            data["erstzulassung"] = None
    # TSN genau 3 Zeichen
    tsn = data.get("tsn")
    if tsn is not None and isinstance(tsn, str):
        tsn_clean = tsn.strip()
        if len(tsn_clean) > 3:
            data["tsn"] = None
        elif len(tsn_clean) == 3:
            data["tsn"] = tsn_clean.upper()
    return data


def _scan_vin_only_lm_studio(image_bytes: bytes, media_type: str) -> str | None:
    """VIN-only-Call via LM Studio (Vision). Gibt normalisierte 17-Zeichen-VIN oder None zurück."""
    try:
        from api.ai_api import lm_studio_client
        import base64
        b64 = base64.b64encode(image_bytes).decode("ascii")
        mt = media_type or "image/jpeg"
        out = lm_studio_client.chat_completion_vision(b64, mt, VIN_ONLY_PROMPT, max_tokens=64, temperature=0.0, timeout=30)
        if not out:
            return None
        raw = re.sub(r"[^A-HJ-NPR-Z0-9]", "", out.strip().upper())[:17]
        if len(raw) < 17:
            return None
        raw = raw[:17].translate(VIN_FORBIDDEN_TO_VALID)
        if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", raw):
            return None
        if not _vin_valid(raw):
            corrected = _vin_auto_correct_one_char(raw)
            if corrected:
                raw = corrected
        return raw
    except Exception as e:
        logger.warning("VIN-Only (LM Studio) fehlgeschlagen: %s", e)
        return None


def _scan_vin_only(client, model_id: str, image_bytes: bytes, fmt: str) -> str | None:
    """Zweiter Bedrock-Call: Nur 17-Zeichen-VIN aus Feld E lesen. Gibt normalisierte VIN oder None zurück."""
    try:
        resp = client.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"image": {"format": fmt, "source": {"bytes": image_bytes}}},
                        {"text": VIN_ONLY_PROMPT},
                    ],
                }
            ],
            inferenceConfig={"maxTokens": 64, "temperature": 0.0},
        )
        text = (resp.get("output") or {}).get("message") or {}
        content = (text.get("content") or [])
        if not content:
            return None
        raw = content[0].get("text") or ""
        raw = re.sub(r"[^A-HJ-NPR-Z0-9]", "", raw.strip().upper())[:17]
        if len(raw) < 17:
            return None
        raw = raw[:17].translate(VIN_FORBIDDEN_TO_VALID)
        if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", raw):
            return None
        if not _vin_valid(raw):
            corrected = _vin_auto_correct_one_char(raw)
            if corrected:
                raw = corrected
        return raw
    except Exception as e:
        logger.warning("VIN-Only-Call fehlgeschlagen: %s", e)
        return None


def _parse_ez_date(s: str):
    """Parst TT.MM.JJJJ oder TT.MM.JJ; gibt date oder None."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    # TT.MM.JJJJ
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", s)
    if m:
        try:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).date()
        except ValueError:
            return None
    # TT.MM.JJ
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{2})$", s)
    if m:
        try:
            y = int(m.group(3))
            year = 2000 + y if y < 100 else 1900 + y
            return datetime(year, int(m.group(2)), int(m.group(1))).date()
        except ValueError:
            return None
    return None


class FahrzeugscheinScanner:
    """DSGVO-konforme Fahrzeugschein-OCR via AWS Bedrock (eu-central-1)."""

    def __init__(self, credentials: dict):
        if not BOTO3_AVAILABLE:
            raise RuntimeError("boto3 nicht installiert – pip install boto3")
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=credentials["region"],
            aws_access_key_id=credentials["access_key_id"],
            aws_secret_access_key=credentials["secret_access_key"],
        )
        self.model_id = credentials.get(
            "model_id", "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
        )

    def scan(self, image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
        """Scannt ein Fahrzeugschein-Bild und gibt strukturierte Daten zurück."""
        fmt = (media_type or "image/jpeg").split("/")[-1]
        if fmt == "jpg":
            fmt = "jpeg"
        response = self.client.converse(
            modelId=self.model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "image": {
                                "format": fmt,
                                "source": {"bytes": image_bytes},
                            }
                        },
                        {"text": SCAN_PROMPT},
                    ],
                }
            ],
            inferenceConfig={"maxTokens": 1024, "temperature": 0.0},
        )
        result_text = response["output"]["message"]["content"][0]["text"]
        # Optional: Strip markdown code fence if model returns ```json ... ```
        if "```" in result_text:
            for part in result_text.split("```"):
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    result_text = part
                    break
        data = json.loads(result_text)
        data["_usage"] = {
            "input_tokens": response["usage"]["inputTokens"],
            "output_tokens": response["usage"]["outputTokens"],
        }
        # VIN aus Haupt-OCR
        fin = data.get("fin")
        if fin is not None and isinstance(fin, str):
            normalized = _normalize_vin(fin)
            if normalized and len(normalized) == 17:
                if normalized != fin.strip().upper().replace(" ", "").replace("-", ""):
                    logger.debug("VIN normalisiert (Leerzeichen/IOQ-Korrektur): %s -> %s", fin[:20], normalized)
                if not _vin_valid(normalized):
                    corrected = _vin_auto_correct_one_char(normalized)
                    if corrected:
                        normalized = corrected
                data["fin"] = normalized
            else:
                fallback = fin.strip().upper()
                fallback = re.sub(r"[\s\-\.]", "", fallback)[:17]
                data["fin"] = fallback if fallback else None
        # Kritisch für Neuanlage: Zweiter Bedrock-Call nur für VIN (fokussierte Zeichenerkennung)
        fin_primary = data.get("fin")
        vin_only = _scan_vin_only(self.client, self.model_id, image_bytes, fmt)
        if vin_only and len(vin_only) == 17:
            data["fin"] = vin_only
            if vin_only != fin_primary:
                logger.info("VIN aus zweitem VIN-Only-Call übernommen: %s -> %s", fin_primary, vin_only)
        # Erstzulassung: Plausibilität prüfen – Datum in der Zukunft = typischer OCR-Fehler (falsches Feld gelesen)
        ez = data.get("erstzulassung")
        if ez and isinstance(ez, str):
            ez_parsed = _parse_ez_date(ez.strip())
            if ez_parsed and ez_parsed > datetime.now().date():
                logger.warning("Erstzulassung im Zukunft (%s) – vermutlich falsches Feld (z.B. Ausstellungsdatum), auf null gesetzt", ez)
                data["erstzulassung"] = None
        # TSN ist immer genau 3 Zeichen – längere Werte stammen meist aus falschem Feld (z.B. Typ/Variante)
        tsn = data.get("tsn")
        if tsn is not None and isinstance(tsn, str):
            tsn_clean = tsn.strip()
            if len(tsn_clean) > 3:
                logger.warning("TSN mit >3 Zeichen verworfen (vermutlich falsches Feld): %s", tsn_clean[:20])
                data["tsn"] = None
            elif len(tsn_clean) == 3:
                data["tsn"] = tsn_clean.upper()
        return data

    def health_check(self) -> bool:
        """Prüft die Verbindung zu AWS Bedrock."""
        try:
            response = self.client.converse(
                modelId=self.model_id,
                messages=[
                    {"role": "user", "content": [{"text": "Antworte nur: OK"}]}
                ],
                inferenceConfig={"maxTokens": 10, "temperature": 0.0},
            )
            text = response["output"]["message"]["content"][0]["text"]
            return "OK" in (text or "")
        except Exception as e:
            logger.error("Bedrock health check failed: %s", e)
            return False
