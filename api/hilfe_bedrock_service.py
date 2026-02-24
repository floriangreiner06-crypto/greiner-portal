# -*- coding: utf-8 -*-
"""
Hilfe „Mit KI erweitern“ – zuerst LM Studio (RZ), Fallback AWS Bedrock.
Nutzt Kontext-Registry für fachliche SSOT-Snippets.
Workstream: Hilfe | 2026-02-24
"""
import logging

logger = logging.getLogger(__name__)

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


# Kontext-Registry: Schlüsselwörter (lower) -> Kontext für KI (fachliche SSOT-Beschreibung).
# Entspricht docs/workstreams/Hilfe/hilfe_ki_kontext_registry.md
HILFE_KI_KONTEXT_REGISTRY = {
    "tek": """Die TEK (Tägliche Erfolgskontrolle) im DRIVE zeigt tägliche Kennzahlen für Umsatz, Einsatz, DB1 (Deckungsbeitrag 1), Marge und eine Breakeven-Prognose. Alle Berechnungen kommen aus einer zentralen Quelle (api/controlling_data.py).
- **Umsatz:** Tagesumsatz aus Locosoft (Fahrzeugverkauf, Werkstatt, Teile etc.), Konten 800000–889999.
- **Einsatz (4-Lohn im laufenden Monat):** Im laufenden Monat wird der **rollierende 6-Monats-Schnitt** verwendet: Einsatz_aktuell = Umsatz_aktuell × (Einsatz_6M / Umsatz_6M). Grund: Die FIBU (74xxxx) ist im laufenden Monat oft noch nicht voll gebucht; so bleibt die Marge aussagekräftig. In abgeschlossenen Monaten kommt der Einsatz direkt aus den Buchungen.
- **DB1:** Deckungsbeitrag 1 = Umsatz minus variable Kosten (Einsatz).
- **Breakeven-Prognose:** Ab welchem Umsatz die Kosten gedeckt sind. Berechnung: (1) **BWA-Kosten:** 3-Monats-Schnitt der Kosten (variable, direkte, indirekte) aus Locosoft, ggf. anteilig nach Umsatz je Firma. (2) **Werktage:** Echte Werktage (Mo–Fr, ohne bayerische Feiertage) für den Monat. **Datenstichtag:** Locosoft liefert abends; vor 19:00 Uhr zählt „vergangen“ nur bis gestern (damit morgens die verbleibenden Werktage stimmen). (3) **DB1 pro Werktag** = BWA-Kosten des Monats / Werktage gesamt. (4) **Hochrechnung DB1** = (aktueller DB1 / vergangene Werktage) × Werktage gesamt. (5) **Breakeven-Schwelle** = BWA-Kosten des Monats; der Vergleich „aktueller DB1 vs. Kosten“ und „hochgerechneter DB1 vs. Kosten“ ergibt die Ampel (grün/gelb/rot) und die Lücke (Gap).
Wenn du einen Hilfe-Artikel zu TEK oder Breakeven erweiterst, ergänze einen kurzen Abschnitt „So berechnet das DRIVE …“ mit diesen Punkten (rollierender Schnitt für Einsatz, BWA-Kosten 3-Monats-Schnitt, Werktage mit Stichtag 19:00, Hochrechnung über Werktage), ohne Code zu zitieren.""",
    "urlaub": """Urlaubsplaner im DRIVE: Anspruch und Resturlaub kommen aus der Mitarbeiterverwaltung (Portal). Resturlaub = min(Portal-View-Rest, Anspruch − Locosoft-Urlaub); Krankheit mindert den Resturlaub nicht. Genehmiger werden über AD-Gruppen (z. B. „Genehmiger für Urlaub Disposition“ oder GRP_Urlaub_Genehmiger_*) und Team (AD manager bzw. Abteilung) ermittelt. Bei Genehmigung: E-Mail an HR und Mitarbeiter, optional Eintrag in Outlook-Kalender (drive@ und Mitarbeiter-Kalender).""",
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
    # Timeout 60s für längere Artikel-Erweiterung (LM Studio Default 30s oft zu knapp)
    out = lm_studio_client.chat_completion(
        messages=messages,
        model=None,
        max_tokens=2048,
        temperature=0.3,
        timeout=60,
    )
    if not out:
        logger.info("hilfe_ki: LM Studio chat_completion lieferte nichts (Timeout/Netzwerk/Modell?).")
        return None
    out = out.strip()
    if not out:
        logger.info("hilfe_ki: LM Studio antwortete mit leerem Text.")
        return None
    return {"inhalt": out, "kontext_verwendet": kontext_verwendet, "backend": "lm_studio"}


def _get_bedrock_client_and_model():
    """
    SSOT wie Fahrzeugschein: dieselbe credentials.json und dieselbe Client/Model-ID.
    Gibt (client, model_id) oder (None, None) zurück.
    """
    from api.fahrzeuganlage_api import _load_bedrock_credentials
    creds = _load_bedrock_credentials()
    if not creds or not creds.get("secret_access_key"):
        return None, None
    from api.fahrzeugschein_scanner import FahrzeugscheinScanner
    scanner = FahrzeugscheinScanner(creds)
    return scanner.client, scanner.model_id


def erweitern_mit_ki(artikel_titel: str, aktueller_inhalt: str, tags: str = None) -> dict:
    """
    Erweitert den Hilfe-Artikel per KI. Zuerst LM Studio (RZ), bei Fehler Fallback Bedrock.
    Returns: {"inhalt": "<markdown>", "kontext_verwendet": bool, "backend": "lm_studio"|"bedrock"} oder {"error": "<msg>"}.
    """
    # 1. Versuch: LM Studio (RZ)
    result = _erweitern_mit_lm_studio(artikel_titel, aktueller_inhalt, tags)
    if result:
        logger.info("hilfe_ki: Erweiterung via LM Studio (RZ) erfolgreich")
        return result

    logger.warning(
        "hilfe_ki: LM Studio (RZ) lieferte keine Antwort – Fallback auf Bedrock. "
        "LM Studio prüfen: Server erreichbar? (config: api_url, default_model, timeout)"
    )

    # 2. Fallback: Bedrock
    if not BOTO3_AVAILABLE:
        return {"error": "Weder LM Studio (RZ) erreichbar noch boto3 installiert."}
    client, model_id = _get_bedrock_client_and_model()
    if not client or not model_id:
        return {"error": "LM Studio (RZ) nicht erreichbar und AWS Bedrock nicht konfiguriert (config/credentials.json → aws_bedrock)."}

    system_prompt, user_prompt, kontext_verwendet = _build_erweitern_prompts(artikel_titel, aktueller_inhalt, tags)
    try:
        response = client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            system=[{"text": system_prompt}],
            inferenceConfig={"maxTokens": 4096, "temperature": 0.3},
        )
        output = (response.get("output") or {}).get("message") or {}
        content = output.get("content") or []
        if not content:
            return {"error": "Keine Antwort von der KI erhalten (Bedrock)."}
        inhalt = (content[0].get("text") or "").strip()
        if not inhalt:
            return {"error": "Leere Antwort von Bedrock."}
        return {"inhalt": inhalt, "kontext_verwendet": kontext_verwendet, "backend": "bedrock"}
    except Exception as e:
        logger.exception("hilfe_bedrock erweitern_mit_ki: %s", e)
        err_msg = str(e)
        # Verständliche Meldung, wenn Bedrock-Konto nicht freigeschaltet ist
        if "Access to Bedrock models is not allowed for this account" in err_msg or "ValidationException" in err_msg:
            return {
                "error": (
                    "LM Studio (RZ) war nicht erreichbar; Bedrock-Fallback fehlgeschlagen: "
                    "Zugriff auf Bedrock ist für dieses AWS-Konto nicht freigeschaltet. "
                    "Bitte LM Studio prüfen (Server in config/credentials.json → lm_studio, z. B. 46.229.10.1:4433) "
                    "oder beim AWS Support Bedrock für das Konto anfragen."
                )
            }
        return {"error": err_msg}
     "Bitte LM Studio prüfen (Server in config/credentials.json → lm_studio, z. B. 46.229.10.1:4433) "
                    "oder beim AWS Support Bedrock für das Konto anfragen."
                )
            }
        return {"error": err_msg}
