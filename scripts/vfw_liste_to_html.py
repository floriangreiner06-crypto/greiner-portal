#!/usr/bin/env python3
"""
Erstellt aus der VFW-CSV eine sauber formatierte HTML-Tabelle.
Verwendung: python scripts/vfw_liste_to_html.py [csv-pfad] [html-pfad]
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "docs" / "vfw_lohnsteuer_2023_2024.csv"
DEFAULT_HTML = ROOT / "docs" / "vfw_lohnsteuer_2023_2024.html"

# Spalten für Tabelle (Reihenfolge + deutsche Überschrift); leere = auslassen
SPALTEN = [
    ("standort_name", "Standort"),
    ("kennzeichen", "Kennzeichen"),
    ("kom_nr", "Kom.Nr."),
    ("vfw_status", "Status"),
    ("marke", "Marke"),
    ("modell", "Modell"),
    ("ez", "EZ"),
    ("km", "km"),
    ("antriebsart", "Antriebsart"),
    ("upe_brutto", "UPE brutto (€)"),
    ("geldwert_vorteil_monat", "1 % / Monat (€)"),
    ("versteuerung_hinweis", "Versteuerung"),
    ("eingang", "Eingang"),
    ("abmeldung", "Abmeldung"),
    ("verkauft_am", "Verkauft am"),
]


def fmt_num(val):
    if val is None or val == "":
        return ""
    try:
        f = float(val)
        if f == 0 and "preis" in str(val):
            return ""
        return f"{f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return str(val) if val else ""


def fmt_int(val):
    if val is None or val == "":
        return ""
    try:
        return f"{int(float(val)):,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(val) if val else ""


def row_value(key, val):
    if key == "upe_brutto" or key == "geldwert_vorteil_monat":
        return fmt_num(val) if val else ""
    if key == "km":
        return fmt_int(val) if val else ""
    if key in ("listenpreis_netto", "empf_vk_preis", "modell_netto_preis") and val:
        return fmt_num(val)
    return (val or "").strip()


def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    html_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_HTML
    if not csv_path.exists():
        print(f"CSV nicht gefunden: {csv_path}")
        sys.exit(1)

    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    headers = [label for _, label in SPALTEN]
    col_keys = [key for key, _ in SPALTEN]

    html = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Vorführwagen 2023/2024 – Lohnsteuerprüfung</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: 'Segoe UI', system-ui, sans-serif; margin: 1rem 1.5rem; background: #f5f5f5; color: #222; }
    h1 { font-size: 1.35rem; margin-bottom: 0.25rem; }
    .meta { color: #555; font-size: 0.9rem; margin-bottom: 1rem; }
    .wrap { overflow-x: auto; background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    table { width: 100%; border-collapse: collapse; min-width: 900px; }
    th { text-align: left; padding: 0.6rem 0.5rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.02em; color: #444; background: #e8e8e8; border-bottom: 2px solid #ccc; white-space: nowrap; }
    td { padding: 0.45rem 0.5rem; font-size: 0.85rem; border-bottom: 1px solid #eee; vertical-align: top; }
    tr:nth-child(even) { background: #fafafa; }
    tr:hover { background: #f0f7ff; }
    td.num { text-align: right; font-variant-numeric: tabular-nums; }
    .status-v { color: #0a5; }
    .status-x { color: #c60; }
    @media print { body { background: #fff; } .wrap { box-shadow: none; } }
  </style>
</head>
<body>
  <h1>Vorführwagen 2023/2024 (Lohnsteuerprüfung)</h1>
  <p class="meta">Stand: """ + datetime.now().strftime("%d.%m.%Y") + """ · """ + str(len(rows)) + """ Fahrzeuge mit &gt; 1.000 km (Kom.Nr. T/V = unverkauft, Jahreswg.Kz. X = verkauft)</p>
  <div class="wrap">
    <table>
      <thead><tr>
"""
    for h in headers:
        html += f"        <th>{h}</th>\n"
    html += "      </tr></thead>\n      <tbody>\n"

    for r in rows:
        html += "      <tr>\n"
        for i, key in enumerate(col_keys):
            val = row_value(key, r.get(key))
            cls = " num" if key in ("upe_brutto", "geldwert_vorteil_monat", "km") else ""
            if key == "vfw_status":
                if "Verkauft" in (val or ""):
                    cls += " status-x"
                else:
                    cls += " status-v"
            html += f'        <td class="{cls.strip()}">{val or ""}</td>\n'
        html += "      </tr>\n"
    html += """      </tbody>
    </table>
  </div>
</body>
</html>
"""
    html_path.parent.mkdir(parents=True, exist_ok=True)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML erstellt: {html_path} ({len(rows)} Zeilen)")


if __name__ == "__main__":
    main()
