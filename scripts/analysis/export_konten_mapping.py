#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Konten-Mapping (Sachkonten 800000–899999)
================================================
Workstream: controlling

Liest aus PostgreSQL (drive_portal), exportiert Sachkonten aus fibu_buchungen
als CSV für Kontenmapping-Auswertung.

Verwendung (auf dem Server aus Projektroot):
  python scripts/analysis/export_konten_mapping.py

Erfordert: Projekt-Umgebung (psycopg2, config/.env bzw. .env für DB-Zugang)
"""

import csv
import os
import sys

# Projektroot für Imports (falls aus scripts/analysis/ gestartet)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# DB-Verbindung aus Projekt
from api.db_connection import get_db

# Pfade
EXPORT_DIR = os.path.join(PROJECT_ROOT, "data", "exports")
EXPORT_FILE = os.path.join(EXPORT_DIR, "konten_mapping_export.csv")

# Sachkonten-Bereich (Umsatzkonten)
KONTO_VON = 800000
KONTO_BIS = 899999


def run():
    conn = get_db()
    cur = conn.cursor()

    # Eine Zeile pro Konto; Beschreibung aus loco_nominal_accounts; Kategorie = häufigster Wert
    cur.execute("""
        SELECT
            f.nominal_account AS konto,
            (SELECT n.account_description
             FROM loco_nominal_accounts n
             WHERE n.nominal_account_number = f.nominal_account
             LIMIT 1) AS account_description,
            TRIM(COALESCE(
                (SELECT MODE() WITHIN GROUP (ORDER BY f2.kategorie_erweitert)
                 FROM fibu_buchungen f2
                 WHERE f2.nominal_account = f.nominal_account
                   AND f2.nominal_account BETWEEN %s AND %s),
                ''
            )) AS category,
            COUNT(*)::integer AS anzahl_buchungen,
            COALESCE(SUM(CASE WHEN f.debit_credit = 'S' THEN f.amount ELSE 0 END), 0) AS summe_soll,
            COALESCE(SUM(CASE WHEN f.debit_credit = 'H' THEN f.amount ELSE 0 END), 0) AS summe_haben,
            COALESCE(SUM(CASE WHEN f.debit_credit = 'S' THEN f.amount WHEN f.debit_credit = 'H' THEN -f.amount ELSE 0 END), 0) AS netto
        FROM fibu_buchungen f
        WHERE f.nominal_account BETWEEN %s AND %s
        GROUP BY f.nominal_account
        ORDER BY f.nominal_account
    """, (KONTO_VON, KONTO_BIS, KONTO_VON, KONTO_BIS))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    # CSV-Header (Spaltennamen wie gewünscht)
    fieldnames = [
        "Konto",
        "Beschreibung",
        "Aktuelle_Kategorie",
        "Anzahl_Buchungen",
        "Summe_Soll",
        "Summe_Haben",
        "Netto",
    ]

    os.makedirs(EXPORT_DIR, exist_ok=True)

    with open(EXPORT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "Konto": row[0] if hasattr(row, "__getitem__") else row["konto"],
                "Beschreibung": (row[1] or "") if hasattr(row, "__getitem__") else (row.get("account_description") or ""),
                "Aktuelle_Kategorie": (row[2] or "") if hasattr(row, "__getitem__") else (row.get("category") or ""),
                "Anzahl_Buchungen": row[3] if hasattr(row, "__getitem__") else row["anzahl_buchungen"],
                "Summe_Soll": round(float(row[4] or 0), 2) if hasattr(row, "__getitem__") else round(float(row.get("summe_soll") or 0), 2),
                "Summe_Haben": round(float(row[5] or 0), 2) if hasattr(row, "__getitem__") else round(float(row.get("summe_haben") or 0), 2),
                "Netto": round(float(row[6] or 0), 2) if hasattr(row, "__getitem__") else round(float(row.get("netto") or 0), 2),
            })

    print(f"Export: {EXPORT_FILE}")
    print(f"Anzahl Zeilen: {len(rows)}")

    # --- Konsolenausgabe ---

    # a) Zusammenfassung nach Kategorie (Konten, Buchungen, Soll, Haben)
    by_cat = {}
    for row in rows:
        konto = row[0] if hasattr(row, "__getitem__") else row["konto"]
        desc = (row[1] or "") if hasattr(row, "__getitem__") else (row.get("account_description") or "")
        cat = (row[2] or "(ohne Kategorie)") if hasattr(row, "__getitem__") else (row.get("category") or "(ohne Kategorie)")
        n = row[3] if hasattr(row, "__getitem__") else row["anzahl_buchungen"]
        soll = float(row[4] or 0) if hasattr(row, "__getitem__") else float(row.get("summe_soll") or 0)
        haben = float(row[5] or 0) if hasattr(row, "__getitem__") else float(row.get("summe_haben") or 0)
        if cat not in by_cat:
            by_cat[cat] = {"konten": set(), "buchungen": 0, "soll": 0.0, "haben": 0.0}
        by_cat[cat]["konten"].add(konto)
        by_cat[cat]["buchungen"] += n
        by_cat[cat]["soll"] += soll
        by_cat[cat]["haben"] += haben

    print("\n--- Zusammenfassung nach Kategorie ---")
    for cat in sorted(by_cat.keys()):
        v = by_cat[cat]
        print(f"  {cat}: {len(v['konten'])} Konten, {v['buchungen']} Buchungen, Soll {v['soll']:,.2f}, Haben {v['haben']:,.2f}")

    # b) 817xxx und 827xxx mit Kategorie – WARNUNG falls "wareneinsatz"
    warn_817_827 = []
    for row in rows:
        konto = row[0] if hasattr(row, "__getitem__") else row["konto"]
        cat = (row[2] or "") if hasattr(row, "__getitem__") else (row.get("category") or "")
        if cat and "wareneinsatz" in (cat or "").lower():
            if (817000 <= konto <= 817999) or (827000 <= konto <= 827999):
                warn_817_827.append((konto, cat))
    if warn_817_827:
        print("\n--- WARNUNG: 817xxx/827xxx mit Kategorie 'wareneinsatz' ---")
        for k, c in sorted(warn_817_827):
            print(f"  Konto {k}: {c}")
    else:
        print("\n--- 817xxx/827xxx mit Kategorie 'wareneinsatz': keine ---")

    # c) Konten ohne Kategorie (NULL oder leer)
    ohne_kat = []
    for row in rows:
        konto = row[0] if hasattr(row, "__getitem__") else row["konto"]
        cat = row[2] if hasattr(row, "__getitem__") else row.get("category")
        if cat is None or (isinstance(cat, str) and cat.strip() == ""):
            ohne_kat.append(konto)
    if ohne_kat:
        print("\n--- Konten ohne Kategorie (NULL oder leer) ---")
        for k in sorted(set(ohne_kat)):
            print(f"  {k}")
    else:
        print("\n--- Konten ohne Kategorie: keine ---")


if __name__ == "__main__":
    run()
