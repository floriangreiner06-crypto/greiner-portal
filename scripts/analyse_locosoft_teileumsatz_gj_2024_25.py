#!/usr/bin/env python3
"""
Analyse: Teileumsatz für Geschäftsjahr 2024/25 aus Locosoft

Zweck:
- Filtert verrechnete Teile (parts mit is_invoiced = true)
- Filtert generierten Teileumsatz (parts.sum und invoices.part_amount_net)
- Zeitraum: 01.09.2024 - 31.08.2025 (Geschäftsjahr 2024/25)

Ausgabe:
- CSV-Datei mit detaillierten Daten
- Konsolen-Output mit Zusammenfassung

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
    Konvertiert Geschäftsjahr-String (z.B. '2024/25') in Datumsbereich.
    
    Geschäftsjahr startet am 1. September:
    - GJ 2024/25 = 01.09.2024 - 31.08.2025
    
    Args:
        gj_string: z.B. '2024/25'
    
    Returns:
        (von_datum, bis_datum)
    """
    gj_start_jahr = int(gj_string.split('/')[0])
    von_datum = date(gj_start_jahr, 9, 1)  # 1. September
    bis_datum = date(gj_start_jahr + 1, 9, 1)  # 1. September nächstes Jahr (exklusiv)
    
    return von_datum, bis_datum


def hole_teileumsatz(
    von_datum: date,
    bis_datum: date,
    betrieb: Optional[int] = None
) -> Dict[str, Any]:
    """
    Holt Teileumsatz aus Locosoft.
    
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
            betrieb_filter = "AND i.subsidiary = %s"
            params.append(betrieb)
        
        # Detaillierte Abfrage: Alle verrechneten Teilepositionen
        query = """
            SELECT
                i.invoice_date,
                i.invoice_number,
                i.invoice_type,
                i.subsidiary,
                i.order_number,
                p.order_position,
                p.order_position_line,
                p.part_number,
                p.amount as menge,
                p.sum as umsatz_position,
                p.rebate_percent,
                p.goodwill_percent,
                p.parts_type,
                p.text_line as bezeichnung,
                p.stock_no,
                p.stock_removal_date,
                p.mechanic_no,
                eh.name as mechaniker_name,
                o.order_date,
                o.order_taking_employee_no as sb_nr,
                sb.name as sb_name,
                v.license_plate as kennzeichen,
                m.description as marke,
                COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name, 'Unbekannt') as kunde,
                pm.description as teile_bezeichnung,
                pm.rr_price as vk_preis
            FROM parts p
            JOIN invoices i ON p.invoice_number = i.invoice_number 
                AND p.invoice_type = i.invoice_type
            LEFT JOIN orders o ON p.order_number = o.number
            LEFT JOIN employees_history eh ON p.mechanic_no = eh.employee_number
                AND eh.is_latest_record = true
            LEFT JOIN employees_history sb ON o.order_taking_employee_no = sb.employee_number
                AND sb.is_latest_record = true
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
            LEFT JOIN parts_master pm ON p.part_number = pm.part_number
            WHERE i.invoice_date >= %s 
              AND i.invoice_date < %s
              AND p.is_invoiced = true
              AND i.is_canceled = false
              AND p.sum > 0
              {betrieb_filter}
            ORDER BY i.invoice_date, i.invoice_number, p.order_position, p.order_position_line
        """.format(betrieb_filter=betrieb_filter)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Zusammenfassung berechnen
        gesamt_menge = sum(float(row['menge'] or 0) for row in rows)
        gesamt_umsatz = sum(float(row['umsatz_position'] or 0) for row in rows)
        anzahl_teilepositionen = len(rows)
        
        # Alternative: Teileumsatz aus invoices (pro Rechnung, nicht pro Position)
        query_rechnungen = """
            SELECT
                COUNT(DISTINCT i.invoice_number || '-' || i.invoice_type) as anzahl_rechnungen,
                SUM(i.part_amount_net) as umsatz_rechnungen_netto,
                SUM(i.part_amount_gross) as umsatz_rechnungen_brutto
            FROM invoices i
            WHERE i.invoice_date >= %s 
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.part_amount_net > 0
              {betrieb_filter}
        """.format(betrieb_filter=betrieb_filter)
        
        cursor.execute(query_rechnungen, params)
        rechnung_row = cursor.fetchone()
        
        # Durchschnittlicher Preis pro Teil
        durchschnittspreis = round(gesamt_umsatz / gesamt_menge, 2) if gesamt_menge > 0 else 0.0
        
        return {
            'zusammenfassung': {
                'von_datum': von_datum.isoformat(),
                'bis_datum': bis_datum.isoformat(),
                'betrieb': betrieb,
                'anzahl_teilepositionen': anzahl_teilepositionen,
                'anzahl_rechnungen': int(rechnung_row['anzahl_rechnungen'] or 0) if rechnung_row else 0,
                'gesamt_menge': round(gesamt_menge, 2),
                'gesamt_umsatz_positionen': round(gesamt_umsatz, 2),
                'gesamt_umsatz_rechnungen_netto': round(float(rechnung_row['umsatz_rechnungen_netto'] or 0), 2) if rechnung_row else 0.0,
                'gesamt_umsatz_rechnungen_brutto': round(float(rechnung_row['umsatz_rechnungen_brutto'] or 0), 2) if rechnung_row else 0.0,
                'durchschnittspreis_pro_teil': durchschnittspreis
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
        'invoice_date',
        'invoice_number',
        'invoice_type',
        'subsidiary',
        'order_number',
        'order_position',
        'order_position_line',
        'part_number',
        'menge',
        'umsatz_position',
        'rebate_percent',
        'goodwill_percent',
        'parts_type',
        'bezeichnung',
        'stock_no',
        'stock_removal_date',
        'mechanic_no',
        'mechaniker_name',
        'order_date',
        'sb_nr',
        'sb_name',
        'kennzeichen',
        'marke',
        'kunde',
        'teile_bezeichnung',
        'vk_preis'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=spalten, extrasaction='ignore')
        writer.writeheader()
        
        for row in daten:
            # DictRow zu normalem Dict konvertieren
            row_dict = dict(row)
            # Numerische Werte runden
            if 'menge' in row_dict and row_dict['menge']:
                row_dict['menge'] = round(float(row_dict['menge']), 2)
            if 'umsatz_position' in row_dict and row_dict['umsatz_position']:
                row_dict['umsatz_position'] = round(float(row_dict['umsatz_position']), 2)
            if 'rebate_percent' in row_dict and row_dict['rebate_percent']:
                row_dict['rebate_percent'] = round(float(row_dict['rebate_percent']), 2)
            if 'goodwill_percent' in row_dict and row_dict['goodwill_percent']:
                row_dict['goodwill_percent'] = round(float(row_dict['goodwill_percent']), 2)
            if 'vk_preis' in row_dict and row_dict['vk_preis']:
                row_dict['vk_preis'] = round(float(row_dict['vk_preis']), 2)
            
            writer.writerow(row_dict)
    
    print(f"✅ CSV exportiert: {output_file}")


def main():
    """Hauptfunktion."""
    print("=" * 80)
    print("LOCOSOFT ANALYSE: Teileumsatz GJ 2024/25")
    print("=" * 80)
    print()
    
    # Geschäftsjahr 2024/25
    gj_string = "2024/25"
    von_datum, bis_datum = get_geschaeftsjahr_datum(gj_string)
    
    print(f"📅 Geschäftsjahr: {gj_string}")
    print(f"   Zeitraum: {von_datum} bis {bis_datum} (exklusiv)")
    print()
    
    # Alle Betriebe
    print("🔍 Analysiere alle Betriebe...")
    result = hole_teileumsatz(von_datum, bis_datum, betrieb=None)
    
    zus = result['zusammenfassung']
    print()
    print("=" * 80)
    print("ZUSAMMENFASSUNG (Alle Betriebe)")
    print("=" * 80)
    print(f"Zeitraum:                    {zus['von_datum']} - {zus['bis_datum']}")
    print(f"Anzahl Teilepositionen:      {zus['anzahl_teilepositionen']:,}")
    print(f"Anzahl Rechnungen:           {zus['anzahl_rechnungen']:,}")
    print(f"Gesamt Menge:               {zus['gesamt_menge']:,.2f} Stk")
    print(f"Umsatz (Positionen):        {zus['gesamt_umsatz_positionen']:,.2f} €")
    print(f"Umsatz (Rechnungen Netto):  {zus['gesamt_umsatz_rechnungen_netto']:,.2f} €")
    print(f"Umsatz (Rechnungen Brutto):  {zus['gesamt_umsatz_rechnungen_brutto']:,.2f} €")
    print(f"Durchschnittspreis (Ø):     {zus['durchschnittspreis_pro_teil']:.2f} €/Stk")
    print()
    
    # CSV exportieren
    output_file = f"scripts/locosoft_teileumsatz_gj_{gj_string.replace('/', '_')}_alle_betriebe.csv"
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
        result_betrieb = hole_teileumsatz(von_datum, bis_datum, betrieb=betrieb_nr)
        
        zus_b = result_betrieb['zusammenfassung']
        print(f"   Positionen:  {zus_b['anzahl_teilepositionen']:,}")
        print(f"   Rechnungen:  {zus_b['anzahl_rechnungen']:,}")
        print(f"   Menge:       {zus_b['gesamt_menge']:,.2f} Stk")
        print(f"   Umsatz:      {zus_b['gesamt_umsatz_positionen']:,.2f} €")
        print(f"   Ø Preis:     {zus_b['durchschnittspreis_pro_teil']:.2f} €/Stk")
        
        # CSV pro Betrieb
        output_file_betrieb = f"scripts/locosoft_teileumsatz_gj_{gj_string.replace('/', '_')}_betrieb_{betrieb_nr}.csv"
        exportiere_csv(result_betrieb['daten'], output_file_betrieb)
    
    print()
    print("=" * 80)
    print("✅ Analyse abgeschlossen!")
    print("=" * 80)


if __name__ == '__main__':
    main()
