#!/usr/bin/env python3
"""
Stückzahl-Analyse nach Mitarbeiter aus Locosoft (mehrere Jahre)
===============================================================
Liest dealer_vehicles pro Kalenderjahr aus, gruppiert nach Verkäufer
(out_salesman_number_1), ermittelt NW- und GW-Stück. Namen aus employees_history.
Gleiche Logik für 2023, 2024, 2025 – zur Überprüfung und für spätere Frontend-History.

Verwendung:
  python3 scripts/verkauf/stueckzahl_analyse_nach_mitarbeiter.py              # 2023, 2024, 2025
  python3 scripts/verkauf/stueckzahl_analyse_nach_mitarbeiter.py 2024 2025    # nur diese Jahre

Output pro Jahr:
  - Konsole: Tabelle mit Mitarbeiter-Nr., Name, Standort, NW, GW, Summe
  - CSV: docs/workstreams/verkauf/Stueckzahl_<JAHR>_nach_Mitarbeiter.csv
"""

import os
import sys
import csv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from api.db_utils import get_locosoft_connection
from psycopg2.extras import RealDictCursor

OUTPUT_DIR = "docs/workstreams/verkauf"
STANDORT_NAME = {1: "DEG", 2: "HYU", 3: "LAN", None: "-"}


def run_for_jahr(jahr: int, base_path: str) -> list:
    """Abfrage Locosoft für ein Jahr, gibt Liste von Dicts zurück und schreibt CSV."""
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
    """, (jahr,))

    rows = cur.fetchall()
    conn.close()

    data = []
    for r in rows:
        nw = int(r["nw_stueck"] or 0)
        gw = int(r["gw_stueck"] or 0)
        data.append({
            "jahr": jahr,
            "mitarbeiter_nr": r["mitarbeiter_nr"],
            "name": (r.get("mitarbeiter_name") or "").strip() or f"Verkäufer #{r['mitarbeiter_nr']}",
            "standort": STANDORT_NAME.get(r.get("standort"), str(r.get("standort") or "")),
            "nw_stueck": nw,
            "gw_stueck": gw,
            "summe_stueck": nw + gw,
        })

    # CSV mit Jahr-Spalte (für spätere History-Aggregation)
    csv_path = os.path.join(base_path, OUTPUT_DIR, f"Stueckzahl_{jahr}_nach_Mitarbeiter.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["jahr", "mitarbeiter_nr", "name", "standort", "nw_stueck", "gw_stueck", "summe_stueck"],
        )
        w.writeheader()
        w.writerows(data)

    return data


def main():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    # Jahre: aus Argumente oder Default 2023, 2024, 2025
    if len(sys.argv) > 1:
        jahre = []
        for a in sys.argv[1:]:
            try:
                jahre.append(int(a))
            except ValueError:
                print(f"Überspringe ungültiges Jahr: {a}")
        if not jahre:
            jahre = [2023, 2024, 2025]
    else:
        jahre = [2023, 2024, 2025]

    jahre.sort()
    csv_paths = []

    for jahr in jahre:
        data = run_for_jahr(jahr, base_path)

        gesamt_nw = sum(d["nw_stueck"] for d in data)
        gesamt_gw = sum(d["gw_stueck"] for d in data)

        print(f"\nStückzahl-Analyse {jahr} nach Mitarbeiter (Locosoft dealer_vehicles)")
        print(f"{'Nr':>6}  {'Name':<30}  {'Standort':>8}  {'NW':>6}  {'GW':>6}  {'Summe':>6}")
        print("-" * 72)
        for d in data:
            print(f"{d['mitarbeiter_nr']:>6}  {d['name']:<30}  {d['standort']:>8}  {d['nw_stueck']:>6}  {d['gw_stueck']:>6}  {d['summe_stueck']:>6}")
        print("-" * 72)
        print(f"{'':>6}  {'GESAMT':<30}  {'':>8}  {gesamt_nw:>6}  {gesamt_gw:>6}  {gesamt_nw + gesamt_gw:>6}")

        csv_path = os.path.join(base_path, OUTPUT_DIR, f"Stueckzahl_{jahr}_nach_Mitarbeiter.csv")
        csv_paths.append(csv_path)

    print("\n" + "=" * 72)
    print("CSV-Dateien (für Überprüfung und Frontend-History):")
    for p in csv_paths:
        print(f"  {p}")
    print()


if __name__ == "__main__":
    main()
