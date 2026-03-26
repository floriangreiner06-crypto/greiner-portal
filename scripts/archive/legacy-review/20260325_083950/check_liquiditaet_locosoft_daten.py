#!/usr/bin/env python3
"""
Datenprüfung Locosoft für Liquiditätsvorschau: erwartete Einnahmen aus
Fahrzeugaufträgen/-rechnungen und Werkstattaufträgen/-rechnungen.

Läuft gegen Locosoft-PostgreSQL; optional Ablöse-Check gegen Portal (fahrzeugfinanzierungen).
Ausgabe: Zählungen, Summen, Stichproben für Einschätzung der Hochrechnung.

Aufruf: aus Projektroot /opt/greiner-portal
  python scripts/check_liquiditaet_locosoft_daten.py [--tage 60]
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, timedelta

# Projektroot für Imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    parser = argparse.ArgumentParser(description="Locosoft-Daten für Liquiditäts-Einnahmen prüfen")
    parser.add_argument("--tage", type=int, default=60, help="Projektionszeitraum in Tagen (default: 60)")
    args = parser.parse_args()
    heute = date.today()
    ende = heute + timedelta(days=args.tage)

    from api.db_utils import locosoft_session, rows_to_list
    from psycopg2.extras import RealDictCursor

    print("=" * 70)
    print("Liquiditätsvorschau – Datenprüfung Locosoft (Fahrzeug & Werkstatt)")
    print(f"Zeitraum: {heute} bis {ende} ({args.tage} Tage)")
    print("=" * 70)

    try:
        with locosoft_session() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # ---- 1. Fahrzeug: Auftrag, noch nicht in Rechnung ----
            cur.execute("""
                SELECT
                    COUNT(*) AS anzahl,
                    COALESCE(SUM(dv.out_estimated_invoice_value), 0) AS summe_geschätzt,
                    COALESCE(SUM(dv.out_sale_price), 0) AS summe_verkaufspreis
                FROM dealer_vehicles dv
                WHERE dv.out_sales_contract_date IS NOT NULL
                  AND dv.out_invoice_date IS NULL
            """)
            row = cur.fetchone()
            n_auftrag = row["anzahl"] or 0
            sum_gesch = float(row["summe_geschätzt"] or 0)
            sum_vk = float(row["summe_verkaufspreis"] or 0)
            print("\n1. Fahrzeug – Auftrag, noch nicht in Rechnung (out_sales_contract_date gesetzt, out_invoice_date NULL)")
            print(f"   Anzahl: {n_auftrag} | Summe out_estimated_invoice_value: {sum_gesch:,.2f} € | Summe out_sale_price: {sum_vk:,.2f} €")

            # Stichprobe: 3 Zeilen mit Betrag
            cur.execute("""
                SELECT dv.dealer_vehicle_type, dv.dealer_vehicle_number,
                       dv.out_sales_contract_date, dv.out_estimated_invoice_value, dv.out_sale_price
                FROM dealer_vehicles dv
                WHERE dv.out_sales_contract_date IS NOT NULL AND dv.out_invoice_date IS NULL
                ORDER BY dv.out_sales_contract_date DESC NULLS LAST
                LIMIT 5
            """)
            sample = rows_to_list(cur.fetchall(), cur)
            if sample:
                print("   Stichprobe (bis 5):")
                for s in sample:
                    print(f"     {s.get('dealer_vehicle_type')} #{s.get('dealer_vehicle_number')} Vertrag {s.get('out_sales_contract_date')} geschätzt={s.get('out_estimated_invoice_value')} VK={s.get('out_sale_price')}")

            # ---- 2. Fahrzeug: Bereits in Rechnung, Rechnungsdatum im Zeitraum (Zahlung ausstehend) ----
            cur.execute("""
                SELECT
                    COUNT(*) AS anzahl,
                    COALESCE(SUM(dv.out_sale_price), 0) AS summe
                FROM dealer_vehicles dv
                WHERE dv.out_invoice_date IS NOT NULL
                  AND dv.out_invoice_date >= %s AND dv.out_invoice_date <= %s
            """, (heute, ende))
            row = cur.fetchone()
            n_rechnung = row["anzahl"] or 0
            sum_rechnung = float(row["summe"] or 0)
            print("\n2. Fahrzeug – Bereits in Rechnung, Rechnungsdatum im Zeitraum (erwarteter Zahlungseingang)")
            print(f"   Anzahl: {n_rechnung} | Summe out_sale_price: {sum_rechnung:,.2f} €")

            # ---- 3. NW Lieferforecast-Stil: vehicles.readmission_date im Zeitraum ----
            cur.execute("""
                SELECT COUNT(*) AS anzahl
                FROM vehicles v
                WHERE v.readmission_date IS NOT NULL
                  AND v.readmission_date >= %s AND v.readmission_date <= %s
                  AND v.dealer_vehicle_type IN ('N', 'V', 'T')
            """, (heute, ende))
            n_readmission = cur.fetchone()["anzahl"] or 0
            print("\n3. NW – Geplante Lieferungen (vehicles.readmission_date im Zeitraum, Typ N/V/T)")
            print(f"   Anzahl: {n_readmission}")

            # ---- 4. Werkstatt: Offene Aufträge (labours nicht vollständig fakturiert), Summe net_price_in_order ----
            cur.execute("""
                SELECT
                    COUNT(DISTINCT l.order_number) AS anzahl_auftraege,
                    COALESCE(SUM(l.net_price_in_order), 0) AS summe_netto
                FROM labours l
                WHERE l.is_invoiced = false
            """)
            row = cur.fetchone()
            n_wst_offen = row["anzahl_auftraege"] or 0
            sum_wst_offen = float(row["summe_netto"] or 0)
            print("\n4. Werkstatt – Offene Positionen (labours.is_invoiced = false)")
            print(f"   Anzahl Aufträge (distinct): {n_wst_offen} | Summe net_price_in_order: {sum_wst_offen:,.2f} €")

            # Optional: nur Aufträge mit order_date/estimated_outbound_time im Zeitraum
            cur.execute("""
                SELECT
                    COUNT(DISTINCT o.number) AS anzahl,
                    COALESCE(SUM(l.net_price_in_order), 0) AS summe
                FROM orders o
                JOIN labours l ON l.order_number = o.number AND l.is_invoiced = false
                WHERE (o.order_date::date BETWEEN %s AND %s)
                   OR (o.estimated_outbound_time::date BETWEEN %s AND %s)
            """, (heute, ende, heute, ende))
            row = cur.fetchone()
            n_wst_zeitraum = row["anzahl"] or 0
            sum_wst_zeitraum = float(row["summe"] or 0)
            print(f"   Davon mit order_date oder estimated_outbound_time im Zeitraum: {n_wst_zeitraum} Aufträge, Summe: {sum_wst_zeitraum:,.2f} €")

            # ---- 5. Werkstatt: Rechnungen mit invoice_date im Zeitraum ----
            # invoice_type: 2,3,4,5,6 = Werkstatt (laut Konzept)
            cur.execute("""
                SELECT
                    COUNT(*) AS anzahl,
                    COALESCE(SUM(total_net), 0) AS summe
                FROM invoices
                WHERE invoice_date >= %s AND invoice_date <= %s
                  AND is_canceled = false
                  AND invoice_type IN (2, 3, 4, 5, 6)
            """, (heute, ende))
            row = cur.fetchone()
            n_wst_rechnung = row["anzahl"] or 0
            sum_wst_rechnung = float(row["summe"] or 0)
            print("\n5. Werkstatt – Rechnungen mit Rechnungsdatum im Zeitraum (invoice_type 2,3,4,5,6)")
            print(f"   Anzahl: {n_wst_rechnung} | Summe total_net: {sum_wst_rechnung:,.2f} €")

            # ---- 6. VIN-Verfügbarkeit für Ablöse-Check (dealer_vehicles -> vehicles) ----
            cur.execute("""
                SELECT COUNT(*) AS mit_vin
                FROM dealer_vehicles dv
                JOIN vehicles v ON v.internal_number = dv.vehicle_number
                    AND v.dealer_vehicle_type = dv.dealer_vehicle_type
                    AND v.dealer_vehicle_number = dv.dealer_vehicle_number
                WHERE dv.out_sales_contract_date IS NOT NULL AND dv.out_invoice_date IS NULL
            """)
            mit_vin = cur.fetchone()["mit_vin"] or 0
            print("\n6. Fahrzeug-Aufträge (noch nicht in Rechnung) – mit VIN (Join zu vehicles) für Ablöse-Check")
            print(f"   Davon mit VIN zuordenbar: {mit_vin} von {n_auftrag}")

    except Exception as e:
        print(f"\nFehler: {e}")
        raise

    print("\n" + "=" * 70)
    print("Hinweis: Einschätzung und Empfehlung siehe docs/workstreams/controlling/Liquiditaet/EINSCHAETZUNG_EINNAHMEN_HOCHRECHNUNG_FZ_WST.md")
    print("=" * 70)


if __name__ == "__main__":
    main()
