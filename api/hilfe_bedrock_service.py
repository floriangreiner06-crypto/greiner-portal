# -*- coding: utf-8 -*-
"""
Hilfe „Mit KI erweitern“ – nur LM Studio (RZ). Bedrock auskommentiert.
Nutzt Kontext-Registry für fachliche SSOT-Snippets.
Workstream: Hilfe | 2026-02-24
"""
import logging

logger = logging.getLogger(__name__)

# Bedrock für Hilfe-KI auskommentiert – nur noch LM Studio
# try:
#     import boto3
#     BOTO3_AVAILABLE = True
# except ImportError:
#     BOTO3_AVAILABLE = False


# Kontext-Registry: Schlüsselwörter (lower) -> Kontext für KI (fachliche SSOT-Beschreibung).
# Entspricht docs/workstreams/Hilfe/hilfe_ki_kontext_registry.md (Letzte Prüfung: 2026-03-19)
HILFE_KI_KONTEXT_REGISTRY = {
    "tek": """Die TEK (Tägliche Erfolgskontrolle) im DRIVE zeigt tägliche Kennzahlen für Umsatz, Einsatz, DB1 (Deckungsbeitrag 1), Marge und eine Breakeven-Prognose. Alle Berechnungen kommen aus einer zentralen Quelle (api/controlling_data.py).
- **Umsatz:** Tagesumsatz aus Locosoft (Fahrzeugverkauf, Werkstatt, Teile etc.), Konten 800000–889999.
- **Einsatz (4-Lohn im laufenden Monat):** Im laufenden Monat wird der **rollierende 6-Monats-Schnitt** verwendet: Einsatz_aktuell = Umsatz_aktuell × (Einsatz_6M / Umsatz_6M). Grund: Die FIBU (74xxxx) ist im laufenden Monat oft noch nicht voll gebucht; so bleibt die Marge aussagekräftig. In abgeschlossenen Monaten kommt der Einsatz direkt aus den Buchungen.
- **DB1:** Deckungsbeitrag 1 = Umsatz minus variable Kosten (Einsatz).
- **Stückzahlen NW/GW:** Aus FIBU (loco_journal_accountings), Summe der pro Konto distinct vehicle_reference für Erlöse 81xxxx (NW) und 82xxxx (GW) – gleiche Quelle wie die Detail-Ansicht (Übersicht = Detail); Portal und E-Mail-Report konsistent.
- **Breakeven-Prognose:** Breakeven-Schwelle = 4-Monats-Schnitt der BWA-Kosten (unverändert). Die **Prognose (Hochrechnung)** wird **immer** aus dem aktuellen Monat berechnet: (aktueller DB1 / vergangene Werktage) × Werktage gesamt (wie GlobalCube); es gibt keinen Vormonats-Durchschnitt mehr. (1) **BWA-Kosten:** 4-Monats-Schnitt der Kosten (variable, direkte, indirekte) aus Locosoft – letzte 4 abgeschlossene Kalendermonate, ggf. anteilig nach Umsatz je Firma. (2) **Werktage:** Echte Werktage (Mo–Fr, ohne bayerische Feiertage). **Datenstichtag:** Locosoft liefert abends; vor 19:00 Uhr zählt „vergangen“ nur bis gestern. (3) **DB1 pro Werktag** = BWA-Kosten des Monats / Werktage gesamt. (4) **Hochrechnung DB1** = (aktueller DB1 / vergangene Werktage) × Werktage gesamt. (5) Ampel (grün/gelb/rot) und Gap aus aktueller DB1 und hochgerechneter DB1 vs. Breakeven-Schwelle.
Wenn du einen Hilfe-Artikel zu TEK oder Breakeven erweiterst, ergänze einen kurzen Abschnitt „So berechnet das DRIVE …“ mit diesen Punkten (rollierender Schnitt für Einsatz, Stückzahlen aus FIBU wie Detail, BWA-Kosten 4-Monats-Schnitt, Prognose immer aus aktuellem Monat, Werktage mit Stichtag 19:00), ohne Code zu zitieren.""",
    "urlaub": """Urlaubsplaner im DRIVE: Anspruch und Resturlaub kommen ausschließlich aus der Mitarbeiterverwaltung (Portal-View); Locosoft fließt nicht mehr in die Resturlaubsberechnung ein. Krankheit mindert den Resturlaub nicht. Teilzeit: Nicht-Arbeitstage (Arbeitszeitmodell work_weekdays) werden im Planer grau dargestellt und bei Urlaubsantrag nicht vom Kontingent abgezogen (contingent_days). Genehmiger (AD-Gruppen, z. B. GRP_Urlaub_Genehmiger_*) dürfen für ihr Team auch Urlaub eintragen und stornieren. Kategorie „kein Samstagsdienst (Info)“: reine Info, kein Urlaubstag-Abzug. Bei Genehmigung: E-Mail an HR und Mitarbeiter, optional Outlook-Kalender (drive@ und Mitarbeiter-Kalender).""",
}
# Weitere Schlüsselwörter verweisen auf denselben TEK-Kontext
for _key in ("breakeven", "erfolgskontrolle", "kennzahlen", "einsatz", "db1", "deckungsbeitrag"):
    if _key not in HILFE_KI_KONTEXT_REGISTRY:
        HILFE_KI_KONTEXT_REGISTRY[_key] = HILFE_KI_KONTEXT_REGISTRY["tek"]
for _key in ("resturlaub", "urlaubsplaner", "genehmiger", "urlaubsantrag"):
    if _key not in HILFE_KI_KONTEXT_REGISTRY:
        HILFE_KI_KONTEXT_REGISTRY[_key] = HILFE_KI_KONTEXT_REGISTRY["urlaub"]


def get_context_for_artikel(titel: str, tags: str) -> str:
    """
    Ermittelt den fachlichen Kontext für einen Artikel anhand von Titel und Tags.
    Returns: Kontext-Text oder leerer String.
    """
    titel_lower = (titel or "").lower()
    tags_list = [t.strip().lower() for t in (tags or "").split(",") if t.strip()]
    for key, context in HILFE_KI_KONTEXT_REGISTRY.items():
        if key in tags_list:
            return context
        if key in titel_lower:
            return context
    return ""


def _build_erweitern_prompts(artikel_titel: str, aktueller_inhalt: str, tags: str = None):
    """Baut System- und User-Prompt für Artikel-Erweiterung. Returns (system_prompt, user_prompt, kontext_verwendet)."""
    kontext = get_context_for_artikel(artikel_titel, tags or "")
    system_prompt = """Du bist ein Redakteur für das interne Unternehmensportal DRIVE (Autohaus Greiner).
Deine Aufgabe: Hilfe-Artikel in deutscher Sprache erweitern. Behalte die bestehende Struktur (z. B. Kurz-Antwort, Wichtige Begriffe) bei.
Antworte NUR mit dem erweiterten Markdown-Text, keine Erklärungen außerhalb des Artikels."""

    user_parts = [
        "Erweitere den folgenden Hilfe-Artikel um fehlende fachliche Details (z. B. wie Kennzahlen berechnet werden).",
        "Titel des Artikels: " + (artikel_titel or "(ohne Titel)"),
        "",
        "--- Aktueller Inhalt (Markdown) ---",
        aktueller_inhalt or "(leer)",
        "--- Ende ---",
    ]
    if kontext:
        user_parts.insert(
            1,
            "Nutze ausschließlich den folgenden fachlichen Kontext aus unserem System (SSOT) für Berechnungsdetails:\n\n" + kontext + "\n\n"
        )
    user_prompt = "\n\n".join(user_parts)
    return system_prompt, user_prompt, bool(kontext)


def _erweitern_mit_lm_studio(artikel_titel: str, aktueller_inhalt: str, tags: str = None) -> dict | None:
    """
    Versucht Artikel-Erweiterung über LM Studio (RZ). Returns dict mit inhalt/kontext_verwendet/backend
    oder None bei Fehler/nicht verfügbar.
    """
    try:
        from api.ai_api import lm_studio_client
    except Exception as e:
        logger.debug("LM Studio nicht verfügbar: %s", e)
        return None
    system_prompt, user_prompt, kontext_verwendet = _build_erweitern_prompts(artikel_titel, aktueller_inhalt, tags)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    # Timeout 90s für längere Artikel-Erweiterung
    out = lm_studio_client.chat_completion(
        messages=messages,
        model=None,
        max_tokens=2048,
        temperature=0.3,
        timeout=90,
    )
    if not out:
        logger.info("hilfe_ki: LM Studio chat_completion lieferte nichts (Timeout/Netzwerk/Modell?).")
        return None
    out = out.strip()
    if not out:
        logger.info("hilfe_ki: LM Studio antwortete mit leerem Text.")
        return None
    return {"inhalt": out, "kontext_verwendet": kontext_verwendet, "backend": "lm_studio"}


# def _get_bedrock_client_and_model():
#     """SSOT wie Fahrzeugschein: dieselbe credentials.json und Client/Model-ID. Gibt (client, model_id) oder (None, None)."""
#     from api.fahrzeuganlage_api import _load_bedrock_credentials
#     creds = _load_bedrock_credentials()
#     if not creds or not creds.get("secret_access_key"):
#         return None, None
#     from api.fahrzeugschein_scanner import FahrzeugscheinScanner
#     scanner = FahrzeugscheinScanner(creds)
#     return scanner.client, scanner.model_id


def erweitern_mit_ki(artikel_titel: str, aktueller_inhalt: str, tags: str = None) -> dict:
    """
    Erweitert den Hilfe-Artikel per KI – nur LM Studio (RZ). Bedrock auskommentiert.
    Returns: {"inhalt": "<markdown>", "kontext_verwendet": bool, "backend": "lm_studio"} oder {"error": "<msg>"}.
    """
    result = _erweitern_mit_lm_studio(artikel_titel, aktueller_inhalt, tags)
    if result:
        logger.info("hilfe_ki: Erweiterung via LM Studio (RZ) erfolgreich")
        return result

    logger.warning(
        "hilfe_ki: LM Studio (RZ) lieferte keine Antwort. "
        "LM Studio prüfen: Server erreichbar? (config: api_url, default_model, timeout=90)"
    )
    return {
        "error": (
            "LM Studio (RZ) hat keine Antwort geliefert (Timeout oder Server nicht erreichbar). "
            "Bitte Server in config/credentials.json → lm_studio prüfen (z. B. 46.229.10.1:4433), Timeout 90 s."
        )
    }

    # --- Bedrock-Fallback auskommentiert (nur noch LM Studio für Hilfe-KI) ---
    # if not BOTO3_AVAILABLE:
    #     return {"error": "Weder LM Studio erreichbar noch boto3 installiert."}
    # client, model_id = _get_bedrock_client_and_model()
    # if not client or not model_id:
    #     return {"error": "LM Studio nicht erreichbar und AWS Bedrock nicht konfiguriert."}
    # system_prompt, user_prompt, kontext_verwendet = _build_erweitern_prompts(...)
    # try:
    #     response = client.converse(...)
    #     ...
    # except Exception as e: ...
