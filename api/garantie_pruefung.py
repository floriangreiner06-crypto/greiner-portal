"""
Garantie-Prüfung (Option A: Fester Kontext + LM Studio)
========================================================
Prüft einen Garantieauftrag anhand der Bedingungen-Kontext-Dateien pro Marke.
Ausgabe: Checkliste (Prüfpunkte erfüllt/fehlt) + Empfehlung (Freitext).
"""
import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Kontext-Dateien: data/garantie_kontext/<key>.md
KONTEXT_KEYS = ("allgemein", "stellantis", "hyundai", "leapmotor")


def _kontext_dir(app=None):
    """Pfad zum Kontext-Verzeichnis data/garantie_kontext."""
    if app:
        root = app.root_path
    else:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "data", "garantie_kontext")


def _marke_to_key(marke: Optional[str]) -> str:
    """UI-Marke (opel, hyundai, alle, …) auf Kontext-Datei-Key mappen."""
    if not marke or not str(marke).strip():
        return "allgemein"
    m = str(marke).strip().lower()
    if m in ("opel", "stellantis", "opel / stellantis"):
        return "stellantis"
    if m == "hyundai":
        return "hyundai"
    if m == "leapmotor":
        return "leapmotor"
    return "allgemein"


def get_garantie_kontext(marke: Optional[str], app=None) -> str:
    """
    Lädt den Bedingungen-Kontext für die gegebene Marke.
    Fallback: allgemein.md, wenn markenspezifische Datei fehlt.
    """
    key = _marke_to_key(marke)
    base_dir = _kontext_dir(app)
    for k in (key, "allgemein"):
        path = os.path.join(base_dir, f"{k}.md")
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.warning("Garantie-Kontext %s lesen: %s", path, e)
    return "Keine Garantie-Bedingungen geladen. Prüfe anhand der üblichen Punkte: Diagnose dokumentiert, Fotos/Belege vorhanden, Garantieakte angelegt, Fristen beachtet."


def _auftragsdaten_texte(arbeitskarte_daten: dict, garantieakte_existiert: bool) -> str:
    """Baut einen strukturierten Text aus Auftrags- und Arbeitskarten-Daten für den KI-Prompt."""
    loco = arbeitskarte_daten.get("locosoft") or {}
    gudat = arbeitskarte_daten.get("gudat") or {}
    auftrag = loco.get("auftrag") or {}
    fahrzeug = loco.get("fahrzeug") or {}
    kunde = loco.get("kunde") or {}
    positionen = loco.get("positionen") or []
    tasks = gudat.get("tasks") or []

    diagnose = ""
    for t in tasks:
        if t.get("description"):
            diagnose = t.get("description", "").strip()
            break
    if not diagnose and auftrag.get("job_beschreibung"):
        diagnose = (auftrag.get("job_beschreibung") or "").strip()
    if not diagnose and positionen:
        erste_mit_text = next((p.get("text_line") for p in positionen if p.get("text_line")), "")
        if erste_mit_text:
            diagnose = erste_mit_text[:500]

    positionen_texte = "\n".join(
        [f"Pos {p.get('position')}: {p.get('text_line', '-')}" for p in positionen[:15]]
    )
    anzahl_anhänge = 0
    if gudat.get("dossier_id"):
        # GUDAT liefert ggf. documents – hier vereinfacht: Dossier vorhanden = Anhänge möglich
        anzahl_anhänge = 1 if diagnose else 0  # Platzhalter; bei Bedarf aus GUDAT documents auslesen

    lines = [
        f"Auftragsnummer: {arbeitskarte_daten.get('order_number', '-')}",
        f"Datum: {auftrag.get('datum', '-')}",
        f"Kunde: {kunde.get('name', '-')}",
        f"Fahrzeug: {fahrzeug.get('marke_modell', '-')}",
        f"Kennzeichen: {fahrzeug.get('kennzeichen', '-')}",
        f"VIN: {fahrzeug.get('vin', '-')}",
        f"Diagnose vorhanden: {'Ja' if diagnose else 'Nein'}",
        f"Diagnose (Auszug): {diagnose[:600] if diagnose else '-'}",
        f"Garantieakte angelegt: {'Ja' if garantieakte_existiert else 'Nein'}",
        f"Gudat-Dossier: {'Ja' if gudat.get('dossier_id') else 'Nein'}",
        f"Arbeitspositionen (Dokumentation):\n{positionen_texte if positionen_texte else '-'}",
    ]
    return "\n".join(lines)


def run_garantie_pruefung(order_number: int, marke: Optional[str] = None, app=None) -> dict:
    """
    Führt die Garantie-Prüfung für einen Auftrag aus (Option A: fester Kontext + LM Studio).

    Returns:
        {
            "success": bool,
            "checkliste": [{"punkt": str, "erfuellt": bool, "hinweis": str}],
            "empfehlung": str,
            "marke_verwendet": str,
            "error": str | None
        }
    """
    from api.arbeitskarte_api import hole_arbeitskarte_daten
    from api.garantie_auftraege_api import get_garantieakte_metadata

    arbeitskarte_daten = hole_arbeitskarte_daten(order_number)
    if not arbeitskarte_daten:
        return {"success": False, "checkliste": [], "empfehlung": "", "marke_verwendet": "", "error": f"Auftrag {order_number} nicht gefunden."}

    # Marke aus Request oder aus subsidiary ableiten
    if not marke:
        brand = arbeitskarte_daten.get("brand") or "hyundai"
        marke = "stellantis" if brand == "stellantis" else "hyundai"
    marke_key = _marke_to_key(marke)

    kunde_name = (arbeitskarte_daten.get("locosoft") or {}).get("kunde") or {}
    kunde_name = kunde_name.get("name", "") if isinstance(kunde_name, dict) else ""
    subsidiary = arbeitskarte_daten.get("subsidiary")
    akte_meta = get_garantieakte_metadata(order_number, kunde_name, subsidiary)
    garantieakte_existiert = akte_meta.get("existiert", False)

    kontext = get_garantie_kontext(marke, app)
    auftragsdaten = _auftragsdaten_texte(arbeitskarte_daten, garantieakte_existiert)

    system_content = (
        "Du bist ein Experte für Garantie-Abrechnung im Autohaus. "
        "Prüfe den Garantieauftrag anhand der angegebenen Bedingungen. "
        "Antworte ausschließlich mit einem gültigen JSON-Objekt. Erfinde keine Fakten."
    )
    user_content = f"""Garantie-Bedingungen (Referenz für die Prüfung):

{kontext}

---

Auftragsdaten:

{auftragsdaten}

---

Aufgabe: Prüfe den Auftrag anhand der Bedingungen. Antworte NUR mit einem JSON-Objekt in genau diesem Format (kein anderer Text):
{{
  "checkliste": [
    {{ "punkt": "Kurzer Prüfpunkt (z.B. Diagnose dokumentiert)", "erfuellt": true oder false, "hinweis": "Kurzer Hinweis falls nicht erfüllt" }}
  ],
  "empfehlung": "Eine kurze, konkrete Empfehlung auf Deutsch: Was fehlt oder was ist der nächste Schritt?"
}}
"""

    try:
        from api.ai_api import lm_studio_client
    except ImportError:
        logger.exception("LM Studio Client nicht importierbar")
        return {"success": False, "checkliste": [], "empfehlung": "", "marke_verwendet": marke_key, "error": "KI-Server (LM Studio) nicht verfügbar."}

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content[:12000]},  # Token-Limit grob begrenzen
    ]
    try:
        response = lm_studio_client.chat_completion(
            messages=messages,
            max_tokens=800,
            temperature=0.2,
            timeout=90,
        )
    except Exception as e:
        logger.exception("LM Studio Aufruf Garantie-Prüfung: %s", e)
        return {"success": False, "checkliste": [], "empfehlung": "", "marke_verwendet": marke_key, "error": f"KI-Server antwortet nicht: {e}"}

    if not response or not str(response).strip():
        return {
            "success": False,
            "checkliste": [],
            "empfehlung": "",
            "marke_verwendet": marke_key,
            "error": (
                "LM Studio hat keine gültige Antwort geliefert. "
                "In den Logs steht oft die genaue Ursache (z. B. HTTP 400 = Anfrage abgelehnt). "
                "Häufig: Modell in LM Studio nicht geladen, oder Modellname in config/credentials.json → lm_studio.default_model "
                "stimmt nicht mit dem in LM Studio geladenen Modell. Logs: journalctl -u greiner-portal -n 50"
            ),
        }

    response_clean = str(response).strip()
    if response_clean.startswith("```"):
        lines = response_clean.split("\n")
        response_clean = "\n".join(lines[1:-1]) if len(lines) > 2 else response_clean
        if response_clean.startswith("json"):
            response_clean = response_clean[4:].strip()

    try:
        result = json.loads(response_clean)
        checkliste = result.get("checkliste")
        if not isinstance(checkliste, list):
            checkliste = []
        empfehlung = result.get("empfehlung") or ""
        return {
            "success": True,
            "checkliste": checkliste,
            "empfehlung": empfehlung,
            "marke_verwendet": marke_key,
            "error": None,
        }
    except json.JSONDecodeError as e:
        logger.warning("Garantie-Prüfung JSON-Parse fehlgeschlagen: %s", e)
        return {
            "success": True,
            "checkliste": [],
            "empfehlung": response_clean[:500] if response_clean else "Keine strukturierte Antwort.",
            "marke_verwendet": marke_key,
            "error": None,
        }
