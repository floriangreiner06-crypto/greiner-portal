#!/usr/bin/env python3
"""
Stückzahl-Analyse 2025 nach Mitarbeiter aus Locosoft
====================================================
Liest dealer_vehicles für Kalenderjahr 2025 aus, gruppiert nach Verkäufer
(out_salesman_number_1), ermittelt NW- und GW-Stück und schreibt eine
CSV + Konsolenübersicht. Namen aus employees_history.

Verwendung:
  python3 scripts/verkauf/stueckzahl_analyse_2025_nach_mitarbeiter.py

Output:
  - Konsole: Tabelle mit Mitarbeiter-Nr., Name, NW, GW, Summe
  - CSV: docs/workstreams/verkauf/Stueckzahl_2025_nach_Mitarbeiter.csv
"""

import os
import sys
import csv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from api.db_utils import get_locosoft_connection
from psycopg2.extras import RealDictCursor

JAHR = 2025
OUTPUT_CSV = "docs/workstreams/verkauf/Stueckzahl_2025_nach_Mitarbeiter.csv"


def main():
    conn = get_locosoft_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            dv.out_salesman_number_1 AS mitarbeiter_nr,
            eh.name AS mitarbeiter_name,
            eh.subsidiary AS standort,
            COUNT(*) FILTER (WHERE dv.dealer_vehicle_type IN ('N', 'V')) AS nw_stueck,
            COUNT(*) FILTER (WHERE dv.dealer_vehicle_type IN ('D', 'G')) AS gw_stueck
        FROM dealer_vehicles dv
        LEFT JOIN employees_history eh
            ON eh.employee_number = dv.out_salesman_number_1
            AND eh.is_latest_record = true
        WHERE EXTRACT(YEAR FROM dv.out_invoice_date) = %s
          AND dv.out_invoice_date IS NOT NULL
          AND dv.dealer_vehicle_type IN ('N', 'V', 'D', 'G')
          AND dv.out_salesman_number_1 IS NOT NULL
        GROUP BY dv.out_salesman_number_1, eh.name, eh.subsidiary
        ORDER BY (COUNT(*) FILTER (WHERE dv.dealer_vehicle_type IN ('N', 'V'))
                  + COUNT(*) FILTER (WHERE dv.dealer_vehicle_type IN ('D', 'G'))) DESC
    """, (JAHR,))

    rows = cur.fetchall()
    conn.close()

    # Standort-Labels
    standort_name = {1: "DEG", 2: "HYU", 3: "LAN", None: "-"}

    data = []
    for r in rows:
        nw = int(r["nw_stueck"] or 0)
        gw = int(r["gw_stueck"] or 0)
        data.append({
            "mitarbeiter_nr": r["mitarbeiter_nr"],
            "name": (r.get("mitarbeiter_name") or "").strip() or f"Verkäufer #{r['mitarbeiter_nr']}",
            "standort": standort_name.get(r.get("standort"), str(r.get("standort") or "")),
            "nw_stueck": nw,
            "gw_stueck": gw,
            "summe_stueck": nw + gw,
        })

    # Konsole
    print(f"\nStückzahl-Analyse {JAHR} nach Mitarbeiter (Locosoft dealer_vehicles)\n")
    print(f"{'Nr':>6}  {'Name':<30}  {'Standort':>8}  {'NW':>6}  {'GW':>6}  {'Summe':>6}")
    print("-" * 72)
    gesamt_nw = 0
    gesamt_gw = 0
    for d in data:
        print(f"{d['mitarbeiter_nr']:>6}  {d['name']:<30}  {d['standort']:>8}  {d['nw_stueck']:>6}  {d['gw_stueck']:>6}  {d['summe_stueck']:>6}")
        gesamt_nw += d["nw_stueck"]
        gesamt_gw += d["gw_stueck"]
    print("-" * 72)
    print(f"{'':>6}  {'GESAMT':<30}  {'':>8}  {gesamt_nw:>6}  {gesamt_gw:>6}  {gesamt_nw + gesamt_gw:>6}\n")

    # CSV
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    csv_path = os.path.join(base, OUTPUT_CSV)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["mitarbeiter_nr", "name", "standort", "nw_stueck", "gw_stueck", "summe_stueck"])
        w.writeheader()
        w.writerows(data)
    print(f"CSV geschrieben: {csv_path}")
    print("\nNächster Schritt: Du gibst an, wer aktiv ist und wer dem Pool 'Handelsgeschäft' zuzuordnen ist.\n")


if __name__ == "__main__":
    main()
