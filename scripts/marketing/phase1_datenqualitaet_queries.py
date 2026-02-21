#!/usr/bin/env python3
"""
Werkstatt-Potenzial Call-Agent / Verschleißreparatur – Phase 1: Datenqualität.
Führt die 4 SQL-Queries auf Locosoft (read-only) aus. Korrigierte Spalten:
- orders: number (nicht order_number), vehicle_number, order_date, order_mileage
- vehicles: internal_number (nicht vehicle_number), make_number
- labours: order_number → JOIN orders ON o.number = l.order_number
- customers_suppliers: first_name, family_name; Telefon über customer_com_numbers
"""

import sys
sys.path.insert(0, "/opt/greiner-portal")

from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor


def run():
    with locosoft_session() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        print("=" * 80)
        print("Query 1 – km-Stand Qualität (orders, letzte 3 Jahre)")
        print("=" * 80)
        cur.execute("""
            SELECT
                COUNT(*) AS total_orders,
                COUNT(NULLIF(order_mileage, 0)) AS with_mileage,
                ROUND(COUNT(NULLIF(order_mileage, 0)) * 100.0 / NULLIF(COUNT(*), 0), 1) AS pct,
                COUNT(DISTINCT vehicle_number) AS unique_vehicles,
                COUNT(DISTINCT CASE WHEN order_mileage > 0 THEN vehicle_number END) AS vehicles_with_km
            FROM orders
            WHERE order_date >= CURRENT_DATE - INTERVAL '3 years'
        """)
        for k, v in cur.fetchone().items():
            print(f"  {k}: {v}")

        print("\n" + "=" * 80)
        print("Query 2 – Fahrzeuge mit mehreren km-Messungen (letzte 5 Jahre)")
        print("=" * 80)
        cur.execute("""
            SELECT
                cnt_measurements,
                COUNT(*) AS fahrzeuge
            FROM (
                SELECT vehicle_number, COUNT(*) AS cnt_measurements
                FROM orders
                WHERE order_mileage > 0 AND order_date >= CURRENT_DATE - INTERVAL '5 years'
                GROUP BY vehicle_number
            ) x
            GROUP BY cnt_measurements
            ORDER BY cnt_measurements
        """)
        for r in cur.fetchall():
            print(f"  {r['cnt_measurements']} Messungen: {r['fahrzeuge']} Fahrzeuge")

        print("\n" + "=" * 80)
        print("Query 3 – Top-40 text_line für Bremsarbeiten (Hyundai + Opel, 3 Jahre)")
        print("=" * 80)
        cur.execute("""
            SELECT
                l.text_line,
                m.description AS marke,
                COUNT(*) AS anzahl
            FROM labours l
            JOIN orders o ON o.number = l.order_number
            JOIN vehicles v ON v.internal_number = o.vehicle_number
            JOIN makes m ON m.make_number = v.make_number
            WHERE v.make_number IN (27, 40)
              AND (LOWER(l.text_line) LIKE '%%brems%%' OR LOWER(l.text_line) LIKE '%%brake%%')
              AND o.order_date >= CURRENT_DATE - INTERVAL '3 years'
            GROUP BY l.text_line, m.description
            ORDER BY anzahl DESC
            LIMIT 40
        """)
        for r in cur.fetchall():
            txt = (r['text_line'] or '')[:55]
            print(f"  {r['anzahl']:5} | {r['marke'] or '':12} | {txt}")

        print("\n" + "=" * 80)
        print("Query 4 – Top-40 text_line für Batterie/Zahnriemen/Steuerkette/Reifen (3 Jahre)")
        print("=" * 80)
        cur.execute("""
            SELECT
                l.text_line,
                COUNT(*) AS anzahl
            FROM labours l
            JOIN orders o ON o.number = l.order_number
            JOIN vehicles v ON v.internal_number = o.vehicle_number
            WHERE v.make_number IN (27, 40)
              AND (
                LOWER(l.text_line) LIKE '%%batterie%%'
                OR LOWER(l.text_line) LIKE '%%zahnriemen%%'
                OR LOWER(l.text_line) LIKE '%%steuerkette%%'
                OR LOWER(l.text_line) LIKE '%%reifen%%'
              )
              AND o.order_date >= CURRENT_DATE - INTERVAL '3 years'
            GROUP BY l.text_line
            ORDER BY anzahl DESC
            LIMIT 40
        """)
        for r in cur.fetchall():
            txt = (r['text_line'] or '')[:60]
            print(f"  {r['anzahl']:5} | {txt}")

        print("\n" + "=" * 80)
        print("Ende Phase-1-Queries")
        print("=" * 80)


if __name__ == "__main__":
    run()
