#!/usr/bin/env python3
"""
Analyse: Verrechnete Stunden und Umsatz für Geschäftsjahr 2024/25 aus Locosoft

Zweck:
- Filtert verrechnete Stunden (labours mit is_invoiced = true)
- Filtert generierten Umsatz (invoices.job_amount_net)
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


def hole_verrechnete_stunden_umsatz(
    von_datum: date,
    bis_datum: date,
    betrieb: Optional[int] = None
) -> Dict[str, Any]:
    """
    Holt verrechnete Stunden und Umsatz aus Locosoft.
    
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
        
        # Detaillierte Abfrage: Alle verrechneten Positionen
        query = """
            SELECT
                i.invoice_date,
                i.invoice_number,
                i.invoice_type,
                i.subsidiary,
                i.order_number,
                l.order_position,
                l.order_position_line,
                l.time_units as aw,
                l.time_units * 6.0 / 60.0 as stunden,  -- 1 AW = 6 Min = 0.1 Std
                l.net_price_in_order as umsatz_position,
                l.charge_type,
                l.labour_type,
                l.mechanic_no,
                eh.name as mechaniker_name,
                o.order_date,
                o.order_taking_employee_no as sb_nr,
                sb.name as sb_name,
                v.license_plate as kennzeichen,
                m.description as marke,
                COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name, 'Unbekannt') as kunde
            FROM labours l
            JOIN invoices i ON l.invoice_number = i.invoice_number 
                AND l.invoice_type = i.invoice_type
            LEFT JOIN orders o ON l.order_number = o.number
            LEFT JOIN employees_history eh ON l.mechanic_no = eh.employee_number
                AND eh.is_latest_record = true
            LEFT JOIN employees_history sb ON o.order_taking_employee_no = sb.employee_number
                AND sb.is_latest_record = true
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
            WHERE i.invoice_date >= %s 
              AND i.invoice_date < %s
              AND l.is_invoiced = true
              AND i.is_canceled = false
              AND l.time_units > 0
              {betrieb_filter}
            ORDER BY i.invoice_date, i.invoice_number, l.order_position, l.order_position_line
        """.format(betrieb_filter=betrieb_filter)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Zusammenfassung berechnen
        gesamt_aw = sum(float(row['aw'] or 0) for row in rows)
        gesamt_stunden = sum(float(row['stunden'] or 0) for row in rows)
        gesamt_umsatz = sum(float(row['umsatz_position'] or 0) for row in rows)
        
        # Alternative: Umsatz aus invoices (pro Rechnung, nicht pro Position)
        # Dies könnte abweichen, wenn eine Rechnung mehrere Positionen hat
        query_rechnungen = """
            SELECT
                COUNT(DISTINCT i.invoice_number || '-' || i.invoice_type) as anzahl_rechnungen,
                SUM(i.job_amount_net) as umsatz_rechnungen
            FROM invoices i
            WHERE i.invoice_date >= %s 
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.job_amount_net > 0
              {betrieb_filter}
        """.format(betrieb_filter=betrieb_filter)
        
        cursor.execute(query_rechnungen, params)
        rechnung_row = cursor.fetchone()
        
        return {
            'zusammenfassung': {
                'von_datum': von_datum.isoformat(),
                'bis_datum': bis_datum.isoformat(),
                'betrieb': betrieb,
                'anzahl_positionen': len(rows),
                'anzahl_rechnungen': int(rechnung_row['anzahl_rechnungen'] or 0) if rechnung_row else 0,
                'gesamt_aw': round(gesamt_aw, 2),
                'gesamt_stunden': round(gesamt_stunden, 2),
                'gesamt_umsatz_positionen': round(gesamt_umsatz, 2),
                'gesamt_umsatz_rechnungen': round(float(rechnung_row['umsatz_rechnungen'] or 0), 2) if rechnung_row else 0.0,
                'durchschnittlicher_stundensatz': round(gesamt_umsatz / gesamt_stunden, 2) if gesamt_stunden > 0 else 0.0
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
        'aw',
        'stunden',
        'umsatz_position',
        'charge_type',
        'labour_type',
        'mechanic_no',
        'mechaniker_name',
        'order_date',
        'sb_nr',
        'sb_name',
        'kennzeichen',
        'marke',
        'kunde'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=spalten, extrasaction='ignore')
        writer.writeheader()
        
        for row in daten:
            # DictRow zu normalem Dict konvertieren
            row_dict = dict(row)
            # Numerische Werte runden
            if 'aw' in row_dict and row_dict['aw']:
                row_dict['aw'] = round(float(row_dict['aw']), 2)
            if 'stunden' in row_dict and row_dict['stunden']:
                row_dict['stunden'] = round(float(row_dict['stunden']), 2)
            if 'umsatz_position' in row_dict and row_dict['umsatz_position']:
                row_dict['umsatz_position'] = round(float(row_dict['umsatz_position']), 2)
            
            writer.writerow(row_dict)
    
    print(f"✅ CSV exportiert: {output_file}")


def main():
    """Hauptfunktion."""
    print("=" * 80)
    print("LOCOSOFT ANALYSE: Verrechnete Stunden und Umsatz GJ 2024/25")
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
    result = hole_verrechnete_stunden_umsatz(von_datum, bis_datum, betrieb=None)
    
    zus = result['zusammenfassung']
    print()
    print("=" * 80)
    print("ZUSAMMENFASSUNG (Alle Betriebe)")
    print("=" * 80)
    print(f"Zeitraum:           {zus['von_datum']} - {zus['bis_datum']}")
    print(f"Anzahl Positionen:  {zus['anzahl_positionen']:,}")
    print(f"Anzahl Rechnungen:  {zus['anzahl_rechnungen']:,}")
    print(f"Gesamt AW:          {zus['gesamt_aw']:,.2f} AW")
    print(f"Gesamt Stunden:     {zus['gesamt_stunden']:,.2f} Std")
    print(f"Umsatz (Positionen): {zus['gesamt_umsatz_positionen']:,.2f} €")
    print(f"Umsatz (Rechnungen): {zus['gesamt_umsatz_rechnungen']:,.2f} €")
    print(f"Stundensatz (Ø):     {zus['durchschnittlicher_stundensatz']:.2f} €/Std")
    print()
    
    # CSV exportieren
    output_file = f"scripts/locosoft_gj_{gj_string.replace('/', '_')}_alle_betriebe.csv"
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
        result_betrieb = hole_verrechnete_stunden_umsatz(von_datum, bis_datum, betrieb=betrieb_nr)
        
        zus_b = result_betrieb['zusammenfassung']
        print(f"   Positionen:  {zus_b['anzahl_positionen']:,}")
        print(f"   Rechnungen:  {zus_b['anzahl_rechnungen']:,}")
        print(f"   AW:          {zus_b['gesamt_aw']:,.2f} AW")
        print(f"   Stunden:     {zus_b['gesamt_stunden']:,.2f} Std")
        print(f"   Umsatz:      {zus_b['gesamt_umsatz_positionen']:,.2f} €")
        print(f"   Stundensatz: {zus_b['durchschnittlicher_stundensatz']:.2f} €/Std")
        
        # CSV pro Betrieb
        output_file_betrieb = f"scripts/locosoft_gj_{gj_string.replace('/', '_')}_betrieb_{betrieb_nr}.csv"
        exportiere_csv(result_betrieb['daten'], output_file_betrieb)
    
    print()
    print("=" * 80)
    print("✅ Analyse abgeschlossen!")
    print("=" * 80)


if __name__ == '__main__':
    main()
