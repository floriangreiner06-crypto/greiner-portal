#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ServiceBox → PostgreSQL Matching Script
Version: TAG173 - PostgreSQL Migration

Gleicht ServiceBox-Bestellungen mit PostgreSQL-DB ab:
- Kundennummer → customers_suppliers (Name, Adresse)
- VIN → sales (Fahrzeug-Details)

USAGE:
    python3 match_servicebox.py
    python3 match_servicebox.py --dry-run
"""

import os
import sys
import json
import argparse
from datetime import datetime

# PostgreSQL Connection
sys.path.insert(0, '/opt/greiner-portal')
from api.db_connection import get_db, sql_placeholder

BASE_DIR = "/opt/greiner-portal"
INPUT_FILE = f"{BASE_DIR}/logs/servicebox_bestellungen_details_final.json"  # TAG173: Korrigierter Pfad
OUTPUT_FILE = f"{BASE_DIR}/logs/servicebox_matched.json"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_matcher.log"

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

# ============================================================================
# POSTGRESQL-ABFRAGEN
# ============================================================================

def get_db_connection():
    """PostgreSQL-Verbindung"""
    try:
        conn = get_db()
        log(f"✅ PostgreSQL-Verbindung hergestellt")
        return conn
    except Exception as e:
        log(f"❌ PostgreSQL-Fehler: {e}")
        return None

def lookup_kunde(conn, kundennummer):
    """
    Sucht Kunden in PostgreSQL nach Kundennummer.
    Tabelle: customers_suppliers
    """
    if not kundennummer:
        return {'gefunden': False}
    
    try:
        cursor = conn.cursor()
        ph = sql_placeholder()
        
        cursor.execute(f"""
            SELECT 
                customer_no,
                short_name,
                long_name
            FROM customers_suppliers
            WHERE customer_no = {ph}
            LIMIT 1
        """, (int(kundennummer),))
        
        row = cursor.fetchone()
        
        if row:
            return {
                'gefunden': True,
                'kundennummer': str(row['customer_no']),
                'name': row['long_name'] or row['short_name'] or f"Kunde {kundennummer}",
                'kurzname': row['short_name']
            }
        else:
            return {'gefunden': False, 'kundennummer': kundennummer}
    
    except Exception as e:
        log(f"Kunden-Lookup Fehler ({kundennummer}): {e}")
        return {'gefunden': False, 'error': str(e)}

def lookup_fahrzeug_by_vin(conn, vin):
    """
    Sucht Fahrzeug in PostgreSQL nach VIN.
    Tabelle: sales (enthält VIN, Modell, Kunde)
    """
    if not vin:
        return {'gefunden': False}
    
    try:
        cursor = conn.cursor()
        ph = sql_placeholder()
        
        cursor.execute(f"""
            SELECT 
                vin,
                model_description,
                make_number,
                dealer_vehicle_type,
                buyer_customer_no,
                out_sales_contract_date,
                out_sale_price,
                salesman_number,
                mileage_km
            FROM sales
            WHERE UPPER(vin) = UPPER({ph})
            ORDER BY out_sales_contract_date DESC NULLS LAST
            LIMIT 1
        """, (vin,))
        
        row = cursor.fetchone()
        
        if row:
            # Marke aus make_number mappen
            marke_map = {1: 'Opel', 2: 'Chevrolet', 3: 'Cadillac', 10: 'Hyundai'}
            marke = marke_map.get(row['make_number'], f"Marke {row['make_number']}")
            
            # Fahrzeugtyp
            typ_map = {'N': 'Neuwagen', 'G': 'Gebrauchtwagen', 'V': 'Vorführwagen', 'T': 'Tageszulassung'}
            fzg_typ = typ_map.get(row['dealer_vehicle_type'], row['dealer_vehicle_type'])
            
            return {
                'gefunden': True,
                'vin': row['vin'],
                'modell': row['model_description'],
                'marke': marke,
                'fahrzeugtyp': fzg_typ,
                'kundennummer': str(row['buyer_customer_no']) if row['buyer_customer_no'] else None,
                'verkaufsdatum': row['out_sales_contract_date'],
                'preis': row['out_sale_price'],
                'km_stand': row['mileage_km']
            }
        else:
            return {'gefunden': False, 'vin': vin}
    
    except Exception as e:
        log(f"⚠️ Fahrzeug-Lookup Fehler ({vin}): {e}")
        return {'gefunden': False, 'error': str(e)}

def check_tables_exist(conn):
    """Prüft ob benötigte Tabellen existieren"""
    cursor = conn.cursor()
    
    tables_needed = ['customers_suppliers', 'sales']
    tables_found = []
    
    for table in tables_needed:
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = %s
        """, (table,))
        if cursor.fetchone():
            tables_found.append(table)
    
    return tables_found, [t for t in tables_needed if t not in tables_found]

# ============================================================================
# MATCHING-LOGIK
# ============================================================================

def match_bestellung(conn, bestellung):
    """
    Matcht eine ServiceBox-Bestellung mit PostgreSQL.
    
    Priorität:
    1. VIN → Fahrzeug + Kunde
    2. Kundennummer → Kunde
    """
    
    match_result = {
        'matched': False,
        'match_typ': None,
        'kunde': None,
        'fahrzeug': None,
        'confidence': 0
    }
    
    parsed = bestellung.get('parsed', {})
    kundennummer = parsed.get('kundennummer')
    vin = parsed.get('vin')
    
    # 1. VIN-Match (höchste Priorität)
    if vin:
        fzg_result = lookup_fahrzeug_by_vin(conn, vin)
        if fzg_result.get('gefunden'):
            match_result['matched'] = True
            match_result['match_typ'] = 'vin'
            match_result['fahrzeug'] = fzg_result
            match_result['confidence'] = 95
            
            # Kunde aus Fahrzeug laden
            fzg_kdnr = fzg_result.get('kundennummer')
            if fzg_kdnr:
                kunde = lookup_kunde(conn, fzg_kdnr)
                if kunde.get('gefunden'):
                    match_result['kunde'] = kunde
            
            return match_result
    
    # 2. Kundennummer-Match
    if kundennummer:
        kunde_result = lookup_kunde(conn, kundennummer)
        if kunde_result.get('gefunden'):
            match_result['matched'] = True
            match_result['match_typ'] = 'kundennummer'
            match_result['kunde'] = kunde_result
            match_result['confidence'] = 85
            return match_result
    
    return match_result

# ============================================================================
# HAUPTPROGRAMM
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='ServiceBox → SQLite Matcher')
    parser.add_argument('--input', default=INPUT_FILE, help='Input JSON-Datei')
    parser.add_argument('--output', default=OUTPUT_FILE, help='Output JSON-Datei')
    parser.add_argument('--dry-run', action='store_true', help='Nur testen')
    args = parser.parse_args()
    
    log("\n" + "="*80)
    log("🔗 SERVICEBOX → POSTGRESQL MATCHER")
    log("="*80)
    
    # Input laden
    log(f"\n📂 Lade Input: {args.input}")
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
        bestellungen = data.get('bestellungen', [])
        log(f"   ✅ {len(bestellungen)} Bestellungen geladen")
    except FileNotFoundError:
        log(f"   ❌ Datei nicht gefunden: {args.input}")
        log(f"   ℹ️  Scraper läuft vermutlich noch - später erneut versuchen")
        return False
    except Exception as e:
        log(f"   ❌ Fehler: {e}")
        return False
    
    # PostgreSQL-Verbindung
    conn = get_db_connection()
    if not conn:
        return False
    
    # Tabellen prüfen
    found, missing = check_tables_exist(conn)
    log(f"   📋 Tabellen gefunden: {', '.join(found)}")
    if missing:
        log(f"   ⚠️ Tabellen fehlen: {', '.join(missing)}")
    
    # Statistik vorher
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM customers_suppliers")
    kunden_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sales WHERE vin IS NOT NULL")
    sales_count = cursor.fetchone()[0]
    log(f"   📊 Kunden in DB: {kunden_count}")
    log(f"   📊 Verkäufe mit VIN: {sales_count}")
    
    # Matching durchführen
    log("\n🔍 STARTE MATCHING...")
    log("-"*80)
    
    stats = {
        'total': len(bestellungen),
        'matched': 0,
        'unmatched': 0,
        'mit_kunde': 0,
        'mit_fahrzeug': 0,
        'by_type': {
            'vin': 0,
            'kundennummer': 0
        }
    }
    
    matched_bestellungen = []
    
    for idx, bestellung in enumerate(bestellungen, 1):
        # TAG173: Unterstütze beide Formate (nummer oder bestellnummer)
        best_nr = bestellung.get('bestellnummer') or bestellung.get('nummer', 'UNKNOWN')
        
        if not args.dry_run:
            match = match_bestellung(conn, bestellung)
        else:
            parsed = bestellung.get('parsed', {})
            match = {
                'matched': bool(parsed.get('vin') or parsed.get('kundennummer')),
                'match_typ': 'vin' if parsed.get('vin') else ('kundennummer' if parsed.get('kundennummer') else None),
                'confidence': 0,
                'kunde': None,
                'fahrzeug': None
            }
        
        bestellung['locosoft_match'] = match
        matched_bestellungen.append(bestellung)
        
        if match['matched']:
            stats['matched'] += 1
            if match.get('match_typ'):
                stats['by_type'][match['match_typ']] = stats['by_type'].get(match['match_typ'], 0) + 1
            if match.get('kunde'):
                stats['mit_kunde'] += 1
            if match.get('fahrzeug'):
                stats['mit_fahrzeug'] += 1
            
            kunde_name = match.get('kunde', {}).get('name', '-') if match.get('kunde') else '-'
            if idx <= 30 or idx % 100 == 0:
                log(f"[{idx}/{stats['total']}] {best_nr} ✅ {match['match_typ']} → {kunde_name}")
        else:
            stats['unmatched'] += 1
            if idx <= 10:
                log(f"[{idx}/{stats['total']}] {best_nr} ❌ kein Match")
    
    # Ergebnisse speichern
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'version': 'v3_postgresql_matched',  # TAG173: PostgreSQL
        'statistik': stats,
        'bestellungen': matched_bestellungen
    }
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
    
    log(f"\n✅ Gespeichert: {args.output}")
    
    # CSV mit Kunden-Info
    csv_file = args.output.replace('.json', '_kunden.csv')
    try:
        import csv
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow([
                'Bestellnummer', 'Datum', 'ServiceBox_KdNr', 'ServiceBox_VIN',
                'Match_Typ', 'Kunde_Name', 
                'Fahrzeug_Marke', 'Fahrzeug_Modell', 'Positionen', 'Summe'
            ])
            
            for b in matched_bestellungen:
                match = b.get('locosoft_match', {})
                kunde = match.get('kunde', {})
                fzg = match.get('fahrzeug', {})
                
                writer.writerow([
                    b.get('bestellnummer', ''),
                    b.get('historie', {}).get('bestelldatum', ''),
                    b.get('parsed', {}).get('kundennummer', ''),
                    b.get('parsed', {}).get('vin', ''),
                    match.get('match_typ', ''),
                    kunde.get('name', '') if kunde else '',
                    fzg.get('marke', '') if fzg else '',
                    fzg.get('modell', '') if fzg else '',
                    len(b.get('positionen', [])),
                    b.get('summen', {}).get('inkl_mwst', '')
                ])
        
        log(f"✅ CSV mit Kunden: {csv_file}")
    except Exception as e:
        log(f"⚠️ CSV-Fehler: {e}")
    
    # Statistik
    log(f"\n{'='*80}")
    log(f"📊 MATCHING-STATISTIK:")
    log(f"   - Bestellungen gesamt: {stats['total']}")
    log(f"   - Gematcht: {stats['matched']} ({stats['matched']/max(stats['total'],1)*100:.1f}%)")
    log(f"   - Nicht gematcht: {stats['unmatched']}")
    log(f"\n   Mit Daten angereichert:")
    log(f"   - Mit Kunde: {stats['mit_kunde']}")
    log(f"   - Mit Fahrzeug: {stats['mit_fahrzeug']}")
    log(f"\n   Nach Match-Typ:")
    for typ, count in stats['by_type'].items():
        if count > 0:
            log(f"   - {typ}: {count}")
    log(f"{'='*80}")
    
    conn.close()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
