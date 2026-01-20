#!/usr/bin/env python3
"""
Analyse: Neuwagenverkauf nach Marken für Geschäftsjahr 2023/24 aus Locosoft

Zweck:
- Filtert Neuwagenverkäufe (dealer_vehicles mit out_invoice_type = 7)
- Gruppiert nach Marken (make_number)
- Zeitraum: 01.09.2024 - 31.08.2025 (Geschäftsjahr 2023/24)

Ausgabe:
- CSV-Datei mit detaillierten Daten
- Konsolen-Output mit Zusammenfassung nach Marken

Erstellt: TAG 198
"""

import sys
import os
from datetime import date, datetime
from typing import Optional, Dict, Any, List

# Projekt-Root zum Python-Pfad hinzufügen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor
import csv


def get_geschaeftsjahr_datum(gj_string: str) -> tuple[date, date]:
    """
    Konvertiert Geschäftsjahr-String (z.B. '2023/24') in Datumsbereich.
    
    Geschäftsjahr startet am 1. September:
    - GJ 2023/24 = 01.09.2024 - 31.08.2025
    
    Args:
        gj_string: z.B. '2023/24'
    
    Returns:
        (von_datum, bis_datum)
    """
    gj_start_jahr = int(gj_string.split('/')[0])
    von_datum = date(gj_start_jahr, 9, 1)  # 1. September
    bis_datum = date(gj_start_jahr + 1, 9, 1)  # 1. September nächstes Jahr (exklusiv)
    
    return von_datum, bis_datum


def hole_neuwagen_verkaeufe(
    von_datum: date,
    bis_datum: date,
    betrieb: Optional[int] = None
) -> Dict[str, Any]:
    """
    Holt Neuwagenverkäufe aus Locosoft.
    
    Args:
        von_datum: Startdatum (inklusive)
        bis_datum: Enddatum (exklusiv)
        betrieb: Betriebsnummer (1=DEG, 2=HYU, 3=LAN), None = alle
    
    Returns:
        dict mit Zusammenfassung und detaillierten Daten
    """
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Filter aufbauen
        betrieb_filter = ""
        params = [von_datum, bis_datum]
        
        if betrieb:
            betrieb_filter = "AND dv.out_subsidiary = %s"
            params.append(betrieb)
        
        # Detaillierte Abfrage: Alle Neuwagenverkäufe
        # invoice_type = 7 = Neuwagenverkauf
        query = """
            SELECT
                dv.out_sales_contract_date as verkaufsdatum,
                dv.out_invoice_date as rechnungsdatum,
                dv.out_invoice_number,
                dv.out_invoice_type,
                dv.out_subsidiary as betrieb,
                dv.dealer_vehicle_type,
                dv.dealer_vehicle_number,
                dv.out_sale_price as verkaufspreis,
                dv.out_sale_type as verkaufstyp,
                dv.out_make_number as marke_nr,
                m.description as marke_name,
                dv.out_model_code as modell_code,
                mod.description as modell_name,
                dv.out_license_plate as kennzeichen,
                v.vin,
                dv.mileage_km as kilometerstand,
                dv.out_salesman_number_1 as verkaufer_nr_1,
                vk1.name as verkaufer_name_1,
                dv.out_salesman_number_2 as verkaufer_nr_2,
                vk2.name as verkaufer_name_2,
                dv.buyer_customer_no as kunde_nr,
                COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name, 'Unbekannt') as kunde_name,
                dv.calc_basic_charge as fahrzeuggrundpreis,
                dv.calc_accessory as zubehoer,
                dv.calc_extra_expenses as fracht_brief_neben,
                COALESCE(i.full_vat_value, 0) + COALESCE(i.reduced_vat_value, 0) as mwst,
                i.total_net as netto_gesamt,
                i.total_gross as brutto_gesamt
            FROM dealer_vehicles dv
            LEFT JOIN makes m ON dv.out_make_number = m.make_number
            LEFT JOIN models mod ON dv.out_make_number = mod.make_number 
                AND dv.out_model_code = mod.model_code
            LEFT JOIN vehicles v ON dv.vehicle_number = v.internal_number
            LEFT JOIN employees_history vk1 ON dv.out_salesman_number_1 = vk1.employee_number
                AND vk1.is_latest_record = true
            LEFT JOIN employees_history vk2 ON dv.out_salesman_number_2 = vk2.employee_number
                AND vk2.is_latest_record = true
            LEFT JOIN customers_suppliers cs ON dv.buyer_customer_no = cs.customer_number
            LEFT JOIN invoices i ON dv.out_invoice_type = i.invoice_type
                AND dv.out_invoice_number::integer = i.invoice_number
            WHERE dv.out_sales_contract_date >= %s 
              AND dv.out_sales_contract_date < %s
              AND dv.out_invoice_type = 7  -- Neuwagenverkauf
              AND dv.out_sales_contract_date IS NOT NULL
              {betrieb_filter}
            ORDER BY dv.out_sales_contract_date, dv.out_make_number, dv.dealer_vehicle_number
        """.format(betrieb_filter=betrieb_filter)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Zusammenfassung nach Marken berechnen
        marken_summen = {}
        gesamt_anzahl = len(rows)
        gesamt_umsatz = 0.0
        
        for row in rows:
            marke_nr = row['marke_nr'] or 0
            marke_name = row['marke_name'] or 'Unbekannt'
            umsatz = float(row['verkaufspreis'] or 0)
            
            if marke_nr not in marken_summen:
                marken_summen[marke_nr] = {
                    'marke_nr': marke_nr,
                    'marke_name': marke_name,
                    'anzahl': 0,
                    'umsatz': 0.0
                }
            
            marken_summen[marke_nr]['anzahl'] += 1
            marken_summen[marke_nr]['umsatz'] += umsatz
            gesamt_umsatz += umsatz
        
        return {
            'zusammenfassung': {
                'von_datum': von_datum.isoformat(),
                'bis_datum': bis_datum.isoformat(),
                'betrieb': betrieb,
                'gesamt_anzahl': gesamt_anzahl,
                'gesamt_umsatz': round(gesamt_umsatz, 2),
                'marken_summen': {k: {
                    'marke_nr': v['marke_nr'],
                    'marke_name': v['marke_name'],
                    'anzahl': v['anzahl'],
                    'umsatz': round(v['umsatz'], 2)
                } for k, v in marken_summen.items()}
            },
            'daten': rows
        }


def exportiere_csv(daten: List[Dict], output_file: str):
    """
    Exportiert Daten als CSV.
    
    Args:
        daten: Liste von Dictionaries (Zeilen)
        output_file: Pfad zur CSV-Datei
    """
    if not daten:
        print(f"⚠️  Keine Daten zum Exportieren!")
        return
    
    # Spalten definieren
    spalten = [
        'verkaufsdatum',
        'rechnungsdatum',
        'out_invoice_number',
        'out_invoice_type',
        'betrieb',
        'dealer_vehicle_type',
        'dealer_vehicle_number',
        'verkaufspreis',
        'verkaufstyp',
        'marke_nr',
        'marke_name',
        'modell_code',
        'modell_name',
        'kennzeichen',
        'vin',
        'kilometerstand',
        'verkaufer_nr_1',
        'verkaufer_name_1',
        'verkaufer_nr_2',
        'verkaufer_name_2',
        'kunde_nr',
        'kunde_name',
        'fahrzeuggrundpreis',
        'zubehoer',
        'fracht_brief_neben',
        'mwst',
        'netto_gesamt',
        'brutto_gesamt'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=spalten, extrasaction='ignore')
        writer.writeheader()
        
        for row in daten:
            # DictRow zu normalem Dict konvertieren
            row_dict = dict(row)
            # Numerische Werte runden
            for key in ['verkaufspreis', 'fahrzeuggrundpreis', 'zubehoer', 'fracht_brief_neben', 
                       'mwst', 'netto_gesamt', 'brutto_gesamt']:
                if key in row_dict and row_dict[key]:
                    row_dict[key] = round(float(row_dict[key]), 2)
            
            writer.writerow(row_dict)
    
    print(f"✅ CSV exportiert: {output_file}")


def main():
    """Hauptfunktion."""
    print("=" * 80)
    print("LOCOSOFT ANALYSE: Neuwagenverkauf nach Marken GJ 2023/24")
    print("=" * 80)
    print()
    
    # Geschäftsjahr 2023/24
    gj_string = "2023/24"
    von_datum, bis_datum = get_geschaeftsjahr_datum(gj_string)
    
    print(f"📅 Geschäftsjahr: {gj_string}")
    print(f"   Zeitraum: {von_datum} bis {bis_datum} (exklusiv)")
    print()
    
    # Alle Betriebe
    print("🔍 Analysiere alle Betriebe...")
    result = hole_neuwagen_verkaeufe(von_datum, bis_datum, betrieb=None)
    
    zus = result['zusammenfassung']
    print()
    print("=" * 80)
    print("ZUSAMMENFASSUNG (Alle Betriebe)")
    print("=" * 80)
    print(f"Zeitraum:           {zus['von_datum']} - {zus['bis_datum']}")
    print(f"Gesamt Anzahl:      {zus['gesamt_anzahl']:,} Fahrzeuge")
    print(f"Gesamt Umsatz:      {zus['gesamt_umsatz']:,.2f} €")
    print()
    print("NACH MARKEN:")
    print("-" * 80)
    
    # Nach Marken sortieren (nach Umsatz)
    marken_liste = sorted(zus['marken_summen'].values(), key=lambda x: x['umsatz'], reverse=True)
    for marke in marken_liste:
        print(f"{marke['marke_name']:20s} | {marke['anzahl']:4d} Stk | {marke['umsatz']:>12,.2f} €")
    
    print()
    
    # CSV exportieren
    output_file = f"scripts/locosoft_neuwagen_gj_{gj_string.replace('/', '_')}_alle_betriebe.csv"
    exportiere_csv(result['daten'], output_file)
    
    # Pro Betrieb
    print()
    print("=" * 80)
    print("NACH BETRIEBEN")
    print("=" * 80)
    
    betriebe = {
        1: "Deggendorf (Opel)",
        2: "Deggendorf (Hyundai)",
        3: "Landau"
    }
    
    for betrieb_nr, betrieb_name in betriebe.items():
        print()
        print(f"📊 {betrieb_name} (Betrieb {betrieb_nr})...")
        result_betrieb = hole_neuwagen_verkaeufe(von_datum, bis_datum, betrieb=betrieb_nr)
        
        zus_b = result_betrieb['zusammenfassung']
        print(f"   Anzahl:     {zus_b['gesamt_anzahl']:,} Fahrzeuge")
        print(f"   Umsatz:     {zus_b['gesamt_umsatz']:,.2f} €")
        print(f"   Nach Marken:")
        marken_liste_b = sorted(zus_b['marken_summen'].values(), key=lambda x: x['umsatz'], reverse=True)
        for marke in marken_liste_b:
            print(f"      {marke['marke_name']:20s} | {marke['anzahl']:4d} Stk | {marke['umsatz']:>12,.2f} €")
        
        # CSV pro Betrieb
        output_file_betrieb = f"scripts/locosoft_neuwagen_gj_{gj_string.replace('/', '_')}_betrieb_{betrieb_nr}.csv"
        exportiere_csv(result_betrieb['daten'], output_file_betrieb)
    
    print()
    print("=" * 80)
    print("✅ Analyse abgeschlossen!")
    print("=" * 80)


if __name__ == '__main__':
    main()
