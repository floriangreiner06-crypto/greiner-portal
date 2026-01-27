#!/usr/bin/env python3
"""
Analyse: Auslieferungen in der Pipeline

Findet verkaufte/bestellte Fahrzeuge aus Locosoft, die noch nicht ausgeliefert wurden:
- Verkaufsdatum vorhanden (out_sales_contract_date IS NOT NULL)
- ABER kein Rechnungsdatum (out_invoice_date IS NULL)
- ODER Rechnungsdatum in der Zukunft (out_invoice_date > CURRENT_DATE)

Diese Fahrzeuge sind "in der Pipeline" - verkauft, aber noch nicht fakturiert/ausgeliefert.

Erstellt: TAG 207
"""

import sys
import os
from datetime import date
from typing import Optional, Dict, Any, List

# Projekt-Root zum Python-Pfad hinzufügen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor


def finde_auslieferungen_pipeline(
    standort: Optional[int] = None,
    nur_neuwagen: bool = False,
    nur_gebrauchtwagen: bool = False
) -> Dict[str, Any]:
    """
    Findet Auslieferungen in der Pipeline (verkauft, aber noch nicht fakturiert).
    
    Pipeline = Fahrzeuge mit:
    - out_sales_contract_date IS NOT NULL (verkauft/bestellt)
    - out_invoice_date IS NULL ODER out_invoice_date > CURRENT_DATE (noch nicht ausgeliefert)
    
    Args:
        standort: Optional - Standort-Filter (1=DEG, 2=HYU, 3=LAN)
        nur_neuwagen: Optional - Nur Neuwagen (dealer_vehicle_type = 'N')
        nur_gebrauchtwagen: Optional - Nur Gebrauchtwagen (dealer_vehicle_type = 'G')
    
    Returns:
        Dict mit 'fahrzeuge' (Liste) und 'statistik'
    """
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Standort-Filter
        standort_filter = ""
        params = []
        if standort:
            standort_filter = "AND dv.out_subsidiary = %s"
            params.append(standort)
        
        # Auftragsvorlauf = verkauft, aber noch nicht ausgeliefert
        # Verkaufs-Kriterien: out_sales_contract_date IS NOT NULL (verkauft/bestellt)
        typ_filter = ""
        if nur_neuwagen:
            typ_filter = "AND dv.dealer_vehicle_type = 'N'"
        elif nur_gebrauchtwagen:
            typ_filter = "AND dv.dealer_vehicle_type = 'G'"
        
        # Rechnungsdatum-Bedingung: NULL oder in der Zukunft
        query = f"""
            SELECT
                dv.dealer_vehicle_number,
                dv.dealer_vehicle_type,
                dv.out_subsidiary as standort,
                dv.out_sales_contract_date as verkaufsdatum,
                dv.out_invoice_date as rechnungsdatum,
                dv.out_invoice_number,
                dv.out_sale_price as verkaufspreis,
                dv.out_sale_type as verkaufstyp,
                dv.out_make_number as marke_nr,
                m.description as marke_name,
                dv.out_model_code as modell_code,
                mod.description as modell_name,
                dv.out_license_plate as kennzeichen,
                v.vin,
                dv.mileage_km as kilometerstand,
                dv.in_subsidiary as lager_standort,
                dv.in_arrival_date as ankunftsdatum,
                dv.buyer_customer_no as kunde_nr,
                COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name, 'Unbekannt') as kunde_name,
                dv.out_salesman_number_1 as verkaufer_nr_1,
                vk1.name as verkaufer_name_1,
                CASE
                    WHEN dv.out_invoice_date IS NULL THEN 'Kein Rechnungsdatum'
                    WHEN dv.out_invoice_date > CURRENT_DATE THEN 'Rechnungsdatum in Zukunft'
                    ELSE 'OK'
                END as status
            FROM dealer_vehicles dv
            LEFT JOIN makes m ON dv.out_make_number = m.make_number
            LEFT JOIN models mod ON dv.out_make_number = mod.make_number 
                AND dv.out_model_code = mod.model_code
            LEFT JOIN vehicles v ON dv.vehicle_number = v.internal_number
            LEFT JOIN employees_history vk1 ON dv.out_salesman_number_1 = vk1.employee_number
                AND vk1.is_latest_record = true
            LEFT JOIN customers_suppliers cs ON dv.buyer_customer_no = cs.customer_number
            WHERE dv.out_sales_contract_date IS NOT NULL
              AND (dv.out_invoice_date IS NULL OR dv.out_invoice_date > CURRENT_DATE)
              {standort_filter}
              {typ_filter}
            ORDER BY 
                CASE 
                    WHEN dv.out_invoice_date IS NULL THEN 1
                    ELSE 2
                END,
                dv.out_sales_contract_date DESC NULLS LAST,
                dv.out_make_number,
                dv.dealer_vehicle_number
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        fahrzeuge = []
        statistik = {
            'gesamt': len(rows),
            'ohne_rechnung': 0,
            'rechnung_zukunft': 0,
            'nach_standort': {},
            'nach_typ': {}
        }
        
        for row in rows:
            fahrzeug = dict(row)
            fahrzeuge.append(fahrzeug)
            
            # Statistik
            if fahrzeug['rechnungsdatum'] is None:
                statistik['ohne_rechnung'] += 1
            else:
                statistik['rechnung_zukunft'] += 1
            
            # Nach Standort
            standort_key = fahrzeug['standort'] or 'Unbekannt'
            statistik['nach_standort'][standort_key] = statistik['nach_standort'].get(standort_key, 0) + 1
            
            # Nach Typ
            typ_key = fahrzeug['dealer_vehicle_type'] or 'Unbekannt'
            statistik['nach_typ'][typ_key] = statistik['nach_typ'].get(typ_key, 0) + 1
        
        return {
            'fahrzeuge': fahrzeuge,
            'statistik': statistik
        }


def main():
    """Hauptfunktion für Kommandozeilen-Nutzung"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Findet Auslieferungen im Auftragsvorlauf (verkauft, aber noch nicht ausgeliefert)'
    )
    parser.add_argument(
        '--standort',
        type=int,
        choices=[1, 2, 3],
        help='Standort-Filter: 1=DEG, 2=HYU, 3=LAN'
    )
    parser.add_argument(
        '--nur-neuwagen',
        action='store_true',
        help='Nur Neuwagen (dealer_vehicle_type = N)'
    )
    parser.add_argument(
        '--nur-gebrauchtwagen',
        action='store_true',
        help='Nur Gebrauchtwagen (dealer_vehicle_type = G)'
    )
    parser.add_argument(
        '--csv',
        action='store_true',
        help='Ausgabe als CSV'
    )
    
    args = parser.parse_args()
    
    # Validierung
    if args.nur_neuwagen and args.nur_gebrauchtwagen:
        print("FEHLER: --nur-neuwagen und --nur-gebrauchtwagen können nicht gleichzeitig verwendet werden!")
        sys.exit(1)
    
    # Daten abrufen
    result = finde_auslieferungen_pipeline(
        standort=args.standort,
        nur_neuwagen=args.nur_neuwagen,
        nur_gebrauchtwagen=args.nur_gebrauchtwagen
    )
    
    fahrzeuge = result['fahrzeuge']
    statistik = result['statistik']
    
    # Ausgabe
    if args.csv:
        # CSV-Ausgabe
        import csv
        import sys
        
        if not fahrzeuge:
            print("Keine Fahrzeuge gefunden.")
            return
        
        fieldnames = [
            'dealer_vehicle_number', 'dealer_vehicle_type', 'standort',
            'verkaufsdatum', 'rechnungsdatum', 'rechnungsnummer',
            'verkaufspreis', 'verkaufstyp', 'marke_name', 'modell_name',
            'kennzeichen', 'vin', 'kilometerstand', 'kunde_name',
            'verkaufer_name_1', 'status'
        ]
        
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        
        for fzg in fahrzeuge:
            writer.writerow({
                'dealer_vehicle_number': fzg.get('dealer_vehicle_number'),
                'dealer_vehicle_type': fzg.get('dealer_vehicle_type'),
                'standort': fzg.get('standort'),
                'verkaufsdatum': fzg.get('verkaufsdatum'),
                'rechnungsdatum': fzg.get('rechnungsdatum'),
                'rechnungsnummer': fzg.get('out_invoice_number'),
                'verkaufspreis': fzg.get('verkaufspreis'),
                'verkaufstyp': fzg.get('verkaufstyp'),
                'marke_name': fzg.get('marke_name'),
                'modell_name': fzg.get('modell_name'),
                'kennzeichen': fzg.get('kennzeichen'),
                'vin': fzg.get('vin'),
                'kilometerstand': fzg.get('kilometerstand'),
                'kunde_name': fzg.get('kunde_name'),
                'verkaufer_name_1': fzg.get('verkaufer_name_1'),
                'status': fzg.get('status')
            })
    else:
        # Text-Ausgabe
        print(f"\n{'='*80}")
        print(f"AUSLIEFERUNGEN IM AUFTRAGSVORLAUF (Pipeline)")
        print(f"{'='*80}\n")
        print(f"Fahrzeuge die verkauft sind, aber noch nicht ausgeliefert wurden")
        print(f"(Verkaufsdatum vorhanden, aber kein Rechnungsdatum oder Rechnungsdatum in Zukunft)\n")
        
        print(f"Statistik:")
        print(f"  Gesamt: {statistik['gesamt']}")
        print(f"  Ohne Rechnungsdatum: {statistik['ohne_rechnung']}")
        print(f"  Rechnungsdatum in Zukunft: {statistik['rechnung_zukunft']}")
        print(f"\n  Nach Standort:")
        for standort, anzahl in sorted(statistik['nach_standort'].items(), key=lambda x: str(x[0])):
            print(f"    {standort}: {anzahl}")
        print(f"\n  Nach Typ:")
        for typ, anzahl in sorted(statistik['nach_typ'].items(), key=lambda x: str(x[0])):
            typ_name = {'N': 'Neuwagen', 'G': 'Gebrauchtwagen', 'D': 'Demo', 'T': 'Tausch', 'V': 'Vorführ'}.get(typ, typ)
            print(f"    {typ} ({typ_name}): {anzahl}")
        
        if fahrzeuge:
            print(f"\n{'='*80}")
            print(f"DETAILS (erste 20):")
            print(f"{'='*80}\n")
            
            for i, fzg in enumerate(fahrzeuge[:20], 1):
                print(f"{i}. {fzg.get('marke_name', '?')} {fzg.get('modell_name', '?')}")
                print(f"   VIN: {fzg.get('vin', '?')}")
                print(f"   Typ: {fzg.get('dealer_vehicle_type', '?')} | Standort: {fzg.get('standort', '?')}")
                print(f"   Verkaufsdatum: {fzg.get('verkaufsdatum', '?')}")
                print(f"   Rechnungsdatum: {fzg.get('rechnungsdatum', 'KEIN')}")
                print(f"   Status: {fzg.get('status', '?')}")
                print(f"   Kunde: {fzg.get('kunde_name', '?')}")
                print(f"   Verkäufer: {fzg.get('verkaufer_name_1', '?')}")
                print()
            
            if len(fahrzeuge) > 20:
                print(f"... und {len(fahrzeuge) - 20} weitere Fahrzeuge")
        else:
            print("\nKeine Fahrzeuge gefunden.")


if __name__ == '__main__':
    main()
