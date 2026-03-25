#!/usr/bin/env python3
"""
Locosoft Potenzialanalyse für Werkstattauslastung / Marketing
==============================================================
Analysen aus docs/workstreams/marketing/WERKSTATT_AUSLASTUNG_LOCOSOFT_KUNDENFAHRZEUGE_VORSCHLAG.md:
- Analyse 5: Datenqualität (Abdeckung HU/Inspektion/Historie)
- Analyse 1: HU/AU-Potenzial (Fälligkeit; Mengenplanung für Veact)
- Analyse 2: Reaktivierung (lange kein Werkstattbesuch)
- Stichprobe: labour_number/labour_operation_id für Inspektion (Opel/Hyundai)

Locosoft read-only (10.80.80.8). Standorte: 1=DEG Opel, 2=HYU Hyundai, 3=LAN.
"""

import sys
from datetime import date, timedelta

sys.path.insert(0, "/opt/greiner-portal")

from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor

HEUTE = date.today()
STANDORT_NAMES = {0: "Betrieb 0 (ohne/offen)", 1: "DEG Opel", 2: "HYU Hyundai", 3: "LAN"}


def run():
    with locosoft_session() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # ---- Analyse 5: Datenqualität ----
        print("=" * 80)
        print("ANALYSE 5: DATENQUALITÄT (Kundenfahrzeuge)")
        print("=" * 80)

        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE v.is_customer_vehicle = true AND v.owner_number IS NOT NULL) AS kundenfahrzeuge_mit_halter,
                COUNT(*) FILTER (WHERE v.is_customer_vehicle = true AND v.next_general_inspection_date IS NOT NULL) AS mit_hu_datum,
                COUNT(*) FILTER (WHERE v.is_customer_vehicle = true AND v.next_emission_test_date IS NOT NULL) AS mit_au_datum,
                COUNT(*) FILTER (WHERE v.is_customer_vehicle = true AND v.next_service_date IS NOT NULL) AS mit_inspektion_datum,
                COUNT(*) FILTER (WHERE v.is_customer_vehicle = true AND v.next_service_km IS NOT NULL AND v.next_service_km > 0) AS mit_inspektion_km,
                COUNT(*) FILTER (WHERE v.is_customer_vehicle = true AND v.mileage_km IS NOT NULL AND v.mileage_km > 0) AS mit_km_stand,
                COUNT(*) FILTER (WHERE v.is_customer_vehicle = true AND v.first_registration_date IS NOT NULL) AS mit_erstzulassung
            FROM vehicles v
            WHERE v.is_customer_vehicle = true
        """)
        row = cur.fetchone()
        gesamt = row["kundenfahrzeuge_mit_halter"] or 0
        print(f"\nKundenfahrzeuge (is_customer_vehicle=true, mit owner_number): {gesamt}")

        if gesamt:
            for key, label in [
                ("mit_hu_datum", "next_general_inspection_date (HU)"),
                ("mit_au_datum", "next_emission_test_date (AU)"),
                ("mit_inspektion_datum", "next_service_date"),
                ("mit_inspektion_km", "next_service_km > 0"),
                ("mit_km_stand", "mileage_km > 0"),
                ("mit_erstzulassung", "first_registration_date"),
            ]:
                n = row[key] or 0
                pct = round(100 * n / gesamt, 1)
                print(f"  {label}: {n} ({pct} %)")

        # Wie viele Kundenfahrzeuge haben mind. 1 Werkstatt-Auftrag (orders)?
        cur.execute("""
            SELECT COUNT(DISTINCT v.internal_number) AS anzahl
            FROM vehicles v
            INNER JOIN orders o ON o.vehicle_number = v.internal_number
            INNER JOIN invoices i ON i.order_number = o.number
            WHERE v.is_customer_vehicle = true
              AND i.invoice_type IN (2, 3, 6)
              AND i.is_canceled = false
        """)
        mit_auftrag = (cur.fetchone() or {}).get("anzahl") or 0
        print(f"\nKundenfahrzeuge mit mind. 1 Werkstatt-Auftrag (Rechnung): {mit_auftrag} ({round(100 * mit_auftrag / max(gesamt, 1), 1)} %)")

        # ---- Analyse 1: HU/AU-Potenzial ----
        print("\n" + "=" * 80)
        print("ANALYSE 1: HU/AU-POTENZIAL (Fälligkeit)")
        print("=" * 80)

        # Mit gepflegtem next_general_inspection_date
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE v.next_general_inspection_date <= %s + INTERVAL '1 month') AS fällig_0_1_monat,
                COUNT(*) FILTER (WHERE v.next_general_inspection_date > %s + INTERVAL '1 month' AND v.next_general_inspection_date <= %s + INTERVAL '3 months') AS fällig_1_3_monate,
                COUNT(*) FILTER (WHERE v.next_general_inspection_date > %s + INTERVAL '3 months' AND v.next_general_inspection_date <= %s + INTERVAL '6 months') AS fällig_3_6_monate
            FROM vehicles v
            WHERE v.is_customer_vehicle = true
              AND v.owner_number IS NOT NULL
              AND v.next_general_inspection_date IS NOT NULL
        """, (HEUTE, HEUTE, HEUTE, HEUTE, HEUTE))
        hu = cur.fetchone()
        if hu:
            print(f"\nHU (next_general_inspection_date gepflegt):")
            print(f"  Fällig 0–1 Monat:   {(hu['fällig_0_1_monat'] or 0)}")
            print(f"  Fällig 1–3 Monate: {(hu['fällig_1_3_monate'] or 0)}")
            print(f"  Fällig 3–6 Monate: {(hu['fällig_3_6_monate'] or 0)}")

        # Fahrzeuge ohne HU-Datum, EZ mind. 2 Jahre her (grobe HU-relevant für Nachpflege)
        vor_2j = HEUTE - timedelta(days=730)
        cur.execute("""
            SELECT COUNT(*) AS anzahl
            FROM vehicles v
            WHERE v.is_customer_vehicle = true
              AND v.owner_number IS NOT NULL
              AND v.next_general_inspection_date IS NULL
              AND v.first_registration_date IS NOT NULL
              AND v.first_registration_date <= %s
        """, (vor_2j,))
        hu_schaetzung = (cur.fetchone() or {}).get("anzahl") or 0
        print(f"\nFahrzeuge ohne HU-Datum, EZ mind. 2 Jahre (Nachpflege-Potenzial): {hu_schaetzung}")

        # ---- Analyse 2: Reaktivierung (lange kein Werkstattbesuch) ----
        print("\n" + "=" * 80)
        print("ANALYSE 2: REAKTIVIERUNG (lange kein Werkstattbesuch)")
        print("=" * 80)

        grenze_12 = HEUTE - timedelta(days=365)
        grenze_18 = HEUTE - timedelta(days=18*30)
        grenze_24 = HEUTE - timedelta(days=730)

        cur.execute("""
            WITH letzter_auftrag AS (
                SELECT o.vehicle_number,
                       MAX(i.invoice_date) AS letztes_datum
                FROM orders o
                INNER JOIN invoices i ON i.order_number = o.number
                WHERE i.invoice_type IN (2, 3, 6)
                  AND i.is_canceled = false
                GROUP BY o.vehicle_number
            )
            SELECT
                v.subsidiary,
                COUNT(*) FILTER (WHERE la.letztes_datum IS NULL OR la.letztes_datum < %s) AS ueber_12_monate,
                COUNT(*) FILTER (WHERE la.letztes_datum IS NULL OR la.letztes_datum < %s) AS ueber_18_monate,
                COUNT(*) FILTER (WHERE la.letztes_datum IS NULL OR la.letztes_datum < %s) AS ueber_24_monate
            FROM vehicles v
            LEFT JOIN letzter_auftrag la ON la.vehicle_number = v.internal_number
            WHERE v.is_customer_vehicle = true
              AND v.owner_number IS NOT NULL
            GROUP BY v.subsidiary
            ORDER BY v.subsidiary
        """, (grenze_12, grenze_18, grenze_24))

        for row in cur.fetchall():
            sub = row["subsidiary"]
            name = STANDORT_NAMES.get(sub, f"Betrieb {sub}")
            print(f"\n{name}:")
            print(f"  > 12 Monate kein Besuch: {(row['ueber_12_monate'] or 0)}")
            print(f"  > 18 Monate kein Besuch: {(row['ueber_18_monate'] or 0)}")
            print(f"  > 24 Monate kein Besuch: {(row['ueber_24_monate'] or 0)}")

        # ---- Analyse 3: Nächste Inspektion (Datum / km) ----
        print("\n" + "=" * 80)
        print("ANALYSE 3: NÄCHSTE INSPEKTION (next_service_date / next_service_km)")
        print("=" * 80)

        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE v.next_service_date IS NOT NULL AND v.next_service_date <= %s + INTERVAL '1 month') AS inspektion_0_1_monat,
                COUNT(*) FILTER (WHERE v.next_service_date IS NOT NULL AND v.next_service_date > %s + INTERVAL '1 month' AND v.next_service_date <= %s + INTERVAL '3 months') AS inspektion_1_3_monate,
                COUNT(*) FILTER (WHERE v.next_service_date IS NOT NULL AND v.next_service_date > %s + INTERVAL '3 months' AND v.next_service_date <= %s + INTERVAL '6 months') AS inspektion_3_6_monate,
                COUNT(*) FILTER (WHERE v.next_service_km IS NOT NULL AND v.next_service_km > 0 AND v.mileage_km IS NOT NULL AND v.mileage_km >= v.next_service_km) AS inspektion_km_erreicht
            FROM vehicles v
            WHERE v.is_customer_vehicle = true
              AND v.owner_number IS NOT NULL
        """, (HEUTE, HEUTE, HEUTE, HEUTE, HEUTE))
        ins = cur.fetchone()
        if ins:
            print(f"\nNach next_service_date (gepflegte Fahrzeuge):")
            print(f"  Fällig 0–1 Monat:   {(ins['inspektion_0_1_monat'] or 0)}")
            print(f"  Fällig 1–3 Monate:  {(ins['inspektion_1_3_monate'] or 0)}")
            print(f"  Fällig 3–6 Monate:  {(ins['inspektion_3_6_monate'] or 0)}")
            print(f"\nNach next_service_km (km-Stand bereits erreicht/überschritten): {(ins['inspektion_km_erreicht'] or 0)}")

        # ---- Analyse 4: Reifen / Kundenräder (tire_storage) ----
        print("\n" + "=" * 80)
        print("ANALYSE 4: REIFEN / KUNDENRÄDER (tire_storage)")
        print("=" * 80)
        cur.execute("""
            SELECT
                COUNT(*) AS faelle,
                COUNT(customer_number) AS mit_kunde,
                COUNT(vehicle_number) AS mit_fahrzeug,
                COUNT(*) FILTER (WHERE is_historic = false OR is_historic IS NULL) AS nicht_historisch
            FROM tire_storage
        """)
        tr = cur.fetchone()
        cur.execute("SELECT COUNT(*) AS n FROM tire_storage_wheels")
        n_wheels = (cur.fetchone() or {}).get("n") or 0
        print(f"\n  tire_storage: {(tr['faelle'] or 0)} Fälle, davon {(tr['mit_fahrzeug'] or 0)} mit vehicle_number, {(tr['nicht_historisch'] or 0)} nicht historisch")
        print(f"  tire_storage_wheels: {n_wheels} Einträge (Räder/Reifen)")

        # ---- Opel/Hyundai in makes (für Inspektionserkennung) ----
        print("\n" + "=" * 80)
        print("MAKES: Opel / Hyundai (make_number für Inspektionslogik)")
        print("=" * 80)
        cur.execute("""
            SELECT make_number, description
            FROM makes
            WHERE description ILIKE '%%opel%%' OR description ILIKE '%%hyundai%%'
            ORDER BY description
        """)
        for r in cur.fetchall():
            print(f"  make_number={r['make_number']}  description={r['description']}")

        # ---- Stichprobe: Inspektion labour_number / labour_operation_id (Opel/Hyundai) ----
        print("\n" + "=" * 80)
        print("STICHPROBE: INSPEKTION – labour_operation_id / labour_number (Opel vs Hyundai)")
        print("=" * 80)

        cur.execute("""
            SELECT m.make_number, m.description AS marke,
                   l.labour_operation_id, l.text_line,
                   COUNT(*) AS anzahl
            FROM labours l
            INNER JOIN orders o ON l.order_number = o.number
            INNER JOIN vehicles v ON o.vehicle_number = v.internal_number
            INNER JOIN makes m ON v.make_number = m.make_number
            INNER JOIN invoices i ON i.order_number = l.order_number
                AND i.invoice_type = l.invoice_type AND i.invoice_number = l.invoice_number
            WHERE i.is_canceled = false
              AND i.invoice_date >= %s - INTERVAL '2 years'
              AND (LOWER(l.text_line) LIKE '%%inspektion%%' OR LOWER(l.text_line) LIKE '%%wartung%%')
              AND LOWER(l.text_line) NOT LIKE '%%hauptuntersuchung%%'
              AND LOWER(l.text_line) NOT LIKE '%%hu %%'
              AND (m.make_number = 40 OR m.make_number = 27)  /* 40=Opel, 27=Hyundai */
            GROUP BY m.make_number, m.description, l.labour_operation_id, l.text_line
            ORDER BY marke, anzahl DESC
            LIMIT 40
        """, (HEUTE,))
        rows = cur.fetchall()
        print(f"\nTop-40 Inspektion/Wartung-Positionen (Opel/Hyundai, letzte 2 Jahre):")
        for r in rows:
            op = (r.get("labour_operation_id") or "")[:20]
            txt = (r.get("text_line") or "")[:50]
            print(f"  {r.get('marke','')[:12]:12} | op_id={op:20} | {r.get('anzahl',0):5}x | {txt}")

        print("\n" + "=" * 80)
        print("Ende Locosoft Potenzialanalyse")
        print("=" * 80)


if __name__ == "__main__":
    run()
