#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyundai Finance CSV Import - FIXED
===================================
Angepasst an korrekte DB-Struktur
"""

import os
import sys
import csv
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
CSV_DIR = '/mnt/buchhaltung/Kontoauszüge/HyundaiFinance'

def parse_german_decimal(value):
    if not value or value == '':
        return 0.0
    try:
        value = str(value).replace('.', '').replace(',', '.')
        return float(value)
    except:
        return 0.0

def parse_date(date_str):
    if not date_str or date_str == '':
        return None
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%Y-%m-%d')
    except:
        return None

def get_latest_csv():
    csv_files = list(Path(CSV_DIR).glob('stockList_*.csv'))
    if not csv_files:
        return None
    return max(csv_files, key=lambda p: p.stat().st_mtime)

def import_hyundai_finance(csv_file=None, dry_run=False):
    print("\n" + "="*70)
    print("📥 HYUNDAI FINANCE - FAHRZEUGFINANZIERUNGEN IMPORT")
    print("="*70)
    
    if csv_file:
        csv_path = Path(csv_file)
    else:
        csv_path = get_latest_csv()
    
    if not csv_path or not csv_path.exists():
        print(f"❌ Keine CSV-Datei gefunden!")
        print(f"   Verzeichnis: {CSV_DIR}")
        return False
    
    print(f"📄 CSV-Datei: {csv_path.name}")
    print(f"📂 Pfad: {csv_path}")
    print(f"📅 Datum: {datetime.fromtimestamp(csv_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not dry_run:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
    
    vehicles = []
    
    print("\n📖 Lese CSV-Datei...")
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        for row in reader:
            try:
                vin = row.get('VIN', '').strip()
                if not vin or len(vin) != 17:
                    continue
                
                finanzierungsnummer = row.get('Finanzierungsnr.', '').strip()
                finanzierungsstatus = row.get('Finanzierungsstatus', '').strip()
                dokumentstatus = row.get('Dokumentenstatus', '').strip()
                
                # Beträge
                original_betrag = abs(parse_german_decimal(row.get('Finanz.-Betrag, €', '0')))
                saldo = parse_german_decimal(row.get('Saldo, €', '0'))
                aktueller_saldo = abs(saldo)
                abbezahlt = original_betrag - aktueller_saldo
                
                # Daten
                rechnungsdatum = parse_date(row.get('Rechnungsdatum', ''))
                vertragsbeginn = parse_date(row.get('Finanzierungsbeginn', ''))
                endfaelligkeit = parse_date(row.get('Finanzierungsende', ''))
                zins_startdatum = parse_date(row.get('Zinsbeginn', ''))
                
                # Fahrzeugdaten
                modell = row.get('Modell', '').strip()
                hersteller = row.get('Hersteller', '').strip()
                produkt = row.get('Produkt', '').strip()
                
                # Berechne Alter in Tagen
                alter_tage = 0
                if vertragsbeginn:
                    try:
                        start = datetime.strptime(vertragsbeginn, '%Y-%m-%d')
                        alter_tage = (datetime.now() - start).days
                    except:
                        pass
                
                vehicle = {
                    'vin': vin,
                    'finanzierungsnummer': finanzierungsnummer,
                    'finanzierungsstatus': finanzierungsstatus,
                    'dokumentstatus': dokumentstatus,
                    'original_betrag': original_betrag,
                    'aktueller_saldo': aktueller_saldo,
                    'abbezahlt': abbezahlt,
                    'vertragsbeginn': vertragsbeginn,
                    'endfaelligkeit': endfaelligkeit,
                    'zins_startdatum': zins_startdatum,
                    'alter_tage': alter_tage,
                    'modell': modell,
                    'hersteller': hersteller,
                    'rrdi': 'Hyundai',  # Äquivalent zu OPEL bei Santander
                    'produktfamilie': produkt
                }
                
                vehicles.append(vehicle)
                
            except Exception as e:
                continue
    
    print(f"   ✅ {len(vehicles)} Fahrzeuge gelesen")
    
    # Statistiken
    total_original = sum(v['original_betrag'] for v in vehicles)
    total_saldo = sum(v['aktueller_saldo'] for v in vehicles)
    total_abbezahlt = sum(v['abbezahlt'] for v in vehicles)
    prozent = (total_abbezahlt / total_original * 100) if total_original > 0 else 0
    
    print(f"\n📊 STATISTIKEN:")
    print(f"   Fahrzeuge:          {len(vehicles)}")
    print(f"   Original-Betrag:    {total_original:>12,.2f} €")
    print(f"   Aktueller Saldo:    {total_saldo:>12,.2f} €")
    print(f"   Abbezahlt:          {total_abbezahlt:>12,.2f} € ({prozent:.1f}%)")
    
    print(f"\n📋 ERSTE 5 FAHRZEUGE:")
    for i, v in enumerate(vehicles[:5], 1):
        print(f"   {i}. {v['vin']}")
        print(f"      Modell:       {v['modell'][:50]}")
        print(f"      Original:     {v['original_betrag']:>10,.2f} €")
        print(f"      Saldo:        {v['aktueller_saldo']:>10,.2f} €")
        print(f"      Status:       {v['finanzierungsstatus']}")
        print()
    
    if dry_run:
        print(f"\n🧪 DRY-RUN - Kein Import in Datenbank")
        return True
    
    print(f"\n💾 IMPORT IN DATENBANK...")
    
    try:
        # Lösche alte Hyundai-Einträge
        cursor.execute("DELETE FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Hyundai Finance'")
        deleted = cursor.rowcount
        print(f"   🗑️  {deleted} alte Einträge gelöscht")
        
        # Insert neue Daten - KORREKTE Spaltennamen!
        insert_count = 0
        for v in vehicles:
            cursor.execute("""
                INSERT INTO fahrzeugfinanzierungen (
                    finanzinstitut,
                    rrdi,
                    produktfamilie,
                    vin,
                    modell,
                    alter_tage,
                    vertragsbeginn,
                    endfaelligkeit,
                    aktueller_saldo,
                    original_betrag,
                    abbezahlt,
                    finanzierungsnummer,
                    finanzierungsstatus,
                    dokumentstatus,
                    zins_startdatum,
                    datei_quelle,
                    import_datum
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'Hyundai Finance',
                v['rrdi'],
                v['produktfamilie'],
                v['vin'],
                v['modell'],
                v['alter_tage'],
                v['vertragsbeginn'],
                v['endfaelligkeit'],
                v['aktueller_saldo'],
                v['original_betrag'],
                v['abbezahlt'],
                v['finanzierungsnummer'],
                v['finanzierungsstatus'],
                v['dokumentstatus'],
                v['zins_startdatum'],
                csv_path.name,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            insert_count += 1
        
        conn.commit()
        print(f"   ✅ {insert_count} Fahrzeuge importiert")
        
        # Verify
        cursor.execute("""
            SELECT COUNT(*), SUM(aktueller_saldo), SUM(original_betrag)
            FROM fahrzeugfinanzierungen 
            WHERE finanzinstitut = 'Hyundai Finance'
        """)
        count, saldo, original = cursor.fetchone()
        
        print(f"\n✅ IMPORT ERFOLGREICH!")
        print(f"   Fahrzeuge in DB:  {count}")
        print(f"   Gesamtsaldo:      {saldo:,.2f} €")
        print(f"   Original-Betrag:  {original:,.2f} €")
        
        # Zeige alle Banken
        print(f"\n📊 ÜBERSICHT ALLE BANKEN:")
        cursor.execute("""
            SELECT 
                finanzinstitut, 
                COUNT(*) as anzahl,
                SUM(aktueller_saldo) as saldo,
                SUM(original_betrag) as original
            FROM fahrzeugfinanzierungen
            GROUP BY finanzinstitut
            ORDER BY finanzinstitut
        """)
        
        total_count = 0
        total_saldo = 0
        total_original = 0
        
        for bank, cnt, saldo, original in cursor.fetchall():
            print(f"   {bank:20s} {cnt:3d} Fz.  Saldo: {saldo:>12,.2f} €  Original: {original:>12,.2f} €")
            total_count += cnt
            total_saldo += saldo or 0
            total_original += original or 0
        
        print(f"   {'-'*80}")
        print(f"   {'GESAMT':20s} {total_count:3d} Fz.  Saldo: {total_saldo:>12,.2f} €  Original: {total_original:>12,.2f} €")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ FEHLER beim Import: {str(e)}")
        if not dry_run:
            conn.rollback()
            conn.close()
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Import Hyundai Finance CSV')
    parser.add_argument('--csv', help='Pfad zur CSV-Datei (optional)')
    parser.add_argument('--dry-run', action='store_true', help='Nur anzeigen, nicht importieren')
    args = parser.parse_args()
    
    success = import_hyundai_finance(csv_file=args.csv, dry_run=args.dry_run)
    
    print("\n" + "="*70)
    if success:
        print("✅ IMPORT ABGESCHLOSSEN")
    else:
        print("❌ IMPORT FEHLGESCHLAGEN")
    print("="*70 + "\n")
    
    sys.exit(0 if success else 1)
