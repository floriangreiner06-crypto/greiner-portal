#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hilfe-Vollständigkeit gegen Code prüfen (KI/Bedrock).
Vergleicht Portal-Module (Code-Inventar) mit vorhandenen Hilfe-Kategorien und -Artikeln,
ruft AWS Bedrock auf und gibt einen Report mit Lücken und Artikelvorschlägen aus.

Verwendung (aus Projektroot):
  python scripts/hilfe_vollstaendigkeit_check.py
  python scripts/hilfe_vollstaendigkeit_check.py --out docs/workstreams/Hilfe/VOLLSTAENDIGKEIT_REPORT.md

Voraussetzung: config/credentials.json mit aws_bedrock (region, access_key_id, secret_access_key, model_id).
Workstream: Hilfe | 2026-02-24
"""

import os
import sys
import json
import argparse

# Projektroot für Imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.chdir(PROJECT_ROOT)

# Code-Inventar (aus Phase-0-Analyse; bei neuen Modulen ergänzen)
CODE_INVENTAR = [
    {"modul": "Dashboard / Start", "route": "/, /start, /dashboard", "beschreibung": "Startseite, rollenbasierte Weiterleitung"},
    {"modul": "Urlaubsplaner", "route": "/urlaubsplaner, /urlaubsplaner/v2, /urlaubsplaner/chef, /urlaubsplaner/admin", "beschreibung": "Urlaub beantragen, Genehmigung, Chef-Übersicht, Admin"},
    {"modul": "Mitarbeiterverwaltung", "route": "/admin/mitarbeiterverwaltung", "beschreibung": "Digitale Personalakte, Vertrag, Arbeitszeit, Urlaubseinstellungen"},
    {"modul": "Organigramm", "route": "/admin/organigramm", "beschreibung": "Vertretungsregeln, Abwesenheitsgrenzen"},
    {"modul": "Bankenspiegel", "route": "/bankenspiegel/", "beschreibung": "Konten, Transaktionen, Zeitverlauf"},
    {"modul": "Controlling", "route": "/controlling/", "beschreibung": "BWA, TEK, KST-Ziele, AfA, OPOS, Finanzreporting, Kundenzentrale, Unternehmensplan"},
    {"modul": "Verkauf", "route": "/verkauf/", "beschreibung": "Auftragseingang, Profitabilität, Auslieferung, eAutoSeller, Budget, GW-Dashboard, Leasys"},
    {"modul": "Verkäufer-Zielplanung", "route": "Navi", "beschreibung": "Zielplanung Kalenderjahr, NW/GW"},
    {"modul": "Provision", "route": "/provision/", "beschreibung": "Provisionsmodul, Meine Übersicht, Config (Admin)"},
    {"modul": "Werkstatt & Service", "route": "Werkstatt, Aftersales", "beschreibung": "Stempeluhr, Live, Aufträge, Kapazität, Fahrzeuganlage, Renner/Penner, Teile-Status, Reparaturpotenzial, Unfall"},
    {"modul": "Serviceberater / Mein Bereich", "route": "/mein-bereich, /aftersales/", "beschreibung": "Persönlicher Bereich, Werkstatt-Übersicht, Stempeluhr, Teile, Garantie"},
    {"modul": "Garantie", "route": "/aftersales/garantie/", "beschreibung": "Garantie-Aufträge, Handbücher, Live-Dashboard"},
    {"modul": "Teile / Lager", "route": "Aftersales Teile", "beschreibung": "Bestellungen, Renner/Penner"},
    {"modul": "WhatsApp", "route": "/whatsapp/", "beschreibung": "Verkauf-Chat, Teile-Nachrichten, Kontakte"},
    {"modul": "Fahrzeuganlage", "route": "Navi", "beschreibung": "Fahrzeugschein-OCR, Anlage"},
    {"modul": "Planung", "route": "Planung-Routes", "beschreibung": "Abteilungsleiter-Planung, Gewinnplanung V2, Stundensatz, Freigabe"},
    {"modul": "KST-Ziele", "route": "/controlling/kst_ziele", "beschreibung": "Kostenstellen-Ziele"},
    {"modul": "OPOS", "route": "/controlling/opos", "beschreibung": "Offene Posten"},
    {"modul": "Jahresprämie", "route": "/jahrespraemie/", "beschreibung": "Jahresprämie, Berechnung, Kulanz"},
    {"modul": "Marketing Potenzial", "route": "/marketing/potenzial", "beschreibung": "Predictive Scoring"},
    {"modul": "Admin", "route": "/admin/", "beschreibung": "Rechte, Celery, User-Dashboard-Config, Provision-Config, ServiceBox-Zugang"},
    {"modul": "Einkaufsfinanzierung / Zinsen", "route": "Controlling/Finanzen", "beschreibung": "Zinsen, Leasys"},
    {"modul": "Ersatzwagen", "route": "Test-UI", "beschreibung": "Ersatzwagen-Kalender (PoC)"},
]


def load_bedrock_credentials():
    path = os.path.join(PROJECT_ROOT, "config", "credentials.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("aws_bedrock")


def get_hilfe_from_db():
    """Lädt Kategorien und Artikel aus der DB."""
    from api.db_utils import db_session, rows_to_list, row_to_dict

    kategorien = []
    artikel_pro_kategorie = {}
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, slug FROM hilfe_kategorien WHERE aktiv = true ORDER BY sort_order, name")
        kategorien = rows_to_list(cur.fetchall(), cur)
        cur.execute("""
            SELECT a.id, a.titel, a.slug, k.name AS kategorie_name, k.slug AS kategorie_slug
            FROM hilfe_artikel a
            JOIN hilfe_kategorien k ON k.id = a.kategorie_id
            WHERE a.aktiv = true
            ORDER BY k.sort_order, a.sort_order, a.titel
        """)
        rows = cur.fetchall()
        for row in rows:
            r = row_to_dict(row, cur)
            kat = (r or {}).get("kategorie_name") or (r or {}).get("kategorie_slug") or "?"
            if kat not in artikel_pro_kategorie:
                artikel_pro_kategorie[kat] = []
            artikel_pro_kategorie[kat].append((r or {}).get("titel") or (r or {}).get("slug") or "")
    return kategorien, artikel_pro_kategorie


def build_prompt(code_lines, hilfe_text):
    return f"""Du bist ein Redaktions-Assistent für das interne Mitarbeiter-Portal "DRIVE" (Autohaus Greiner). Deine Aufgabe: die Vollständigkeit der Hilfe-Dokumentation gegen die tatsächlich im Portal vorhandenen Module prüfen.

=== PORTAL-MODULE (aus Code/Features) ===
{code_lines}

=== AKTUELLE HILFE (Kategorien und Artikel) ===
{hilfe_text}

=== AUFGABE ===
1. Vergleiche die beiden Listen.
2. Nenne LÜCKEN: Module oder wichtige Funktionen, die in der Hilfe fehlen oder nur sehr knapp (z. B. nur ein allgemeiner Titel) abgedeckt sind.
3. Schlage für jede Lücke konkrete HILFE-ARTIKEL vor: Titel (als Frage, z. B. "Wie …?"), und die passende bestehende Hilfe-Kategorie (nur aus der Liste oben verwenden).
4. Priorisiere: Was ist wichtig für viele Nutzer (z. B. Login, Urlaub), was ist Nischen-Feature?
5. Ausgabe in diesem Format (Markdown):

## Lücken (Modul/Feature ohne oder mit schwacher Hilfe)
- **Modul/Feature:** … | **Vorschlag Artikel:** "Titel?" | **Kategorie:** … | **Priorität:** hoch/mittel/niedrig

## Kurz: Fehlende Kategorien (falls ein Modul ganz fehlt)
- …

## Zusammenfassung
- Anzahl Lücken: …
- Top-3 empfohlene neue Artikel: …

Antworte nur mit dem Report, ohne Einleitung."""


def call_bedrock(credentials, prompt_text):
    try:
        import boto3
    except ImportError:
        raise RuntimeError("boto3 nicht installiert – pip install boto3")
    client = boto3.client(
        "bedrock-runtime",
        region_name=credentials["region"],
        aws_access_key_id=credentials["access_key_id"],
        aws_secret_access_key=credentials["secret_access_key"],
    )
    model_id = credentials.get("model_id", "eu.anthropic.claude-sonnet-4-5-20250929-v1:0")
    response = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt_text}]}],
        inferenceConfig={"maxTokens": 2048, "temperature": 0.3},
    )
    return response["output"]["message"]["content"][0]["text"]


def main():
    parser = argparse.ArgumentParser(description="Hilfe-Vollständigkeit gegen Code prüfen (Bedrock)")
    parser.add_argument("--out", "-o", help="Report in Datei schreiben (z. B. .../VOLLSTAENDIGKEIT_REPORT.md)")
    parser.add_argument("--no-ki", action="store_true", help="Nur Code vs. Hilfe ausgeben, ohne Bedrock-Aufruf")
    args = parser.parse_args()

    # Code-Inventar als Text
    code_lines = "\n".join(
        f"- {m['modul']} | Route: {m['route']} | {m['beschreibung']}"
        for m in CODE_INVENTAR
    )

    # Hilfe aus DB
    try:
        kategorien, artikel_pro_kategorie = get_hilfe_from_db()
    except Exception as e:
        print("Fehler beim Laden der Hilfe aus der DB:", e, file=sys.stderr)
        sys.exit(1)

    hilfe_parts = ["Kategorien: " + ", ".join(k.get("name") or k.get("slug") or "" for k in kategorien)]
    for kat, titel_list in artikel_pro_kategorie.items():
        hilfe_parts.append(f"\n{kat}: " + " | ".join(titel_list))
    hilfe_text = "\n".join(hilfe_parts)

    if args.no_ki:
        print("=== CODE-INVENTAR ===")
        print(code_lines)
        print("\n=== HILFE (DB) ===")
        print(hilfe_text)
        return

    creds = load_bedrock_credentials()
    if not creds:
        print("Fehler: config/credentials.json oder aws_bedrock nicht gefunden.", file=sys.stderr)
        sys.exit(1)

    prompt = build_prompt(code_lines, hilfe_text)
    print("Rufe Bedrock auf …", file=sys.stderr)
    try:
        report = call_bedrock(creds, prompt)
    except Exception as e:
        print("Bedrock-Fehler:", e, file=sys.stderr)
        sys.exit(1)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write("# Hilfe-Vollständigkeit vs. Code (KI-Report)\n\n")
            f.write("Erzeugt von scripts/hilfe_vollstaendigkeit_check.py\n\n")
            f.write(report)
        print("Report geschrieben:", args.out)
    else:
        print(report)


if __name__ == "__main__":
    main()
