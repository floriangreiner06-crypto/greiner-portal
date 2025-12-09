"""
Hyundai Finance CSV Import - MIT ZINSBERECHNUNG
================================================
Version: TAG 78
Zinssatz: 4,68% p.a. (aus ek_finanzierung_konditionen)
"""
import os
import sys
import csv
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
CSV_DIR = '/mnt/buchhaltung/Buchhaltung/Kontoauszüge/HyundaiFinance'

# Hyundai Zinssatz aus DB (ek_finanzierung_konditionen TAG 77)
HYUNDAI_ZINSSATZ = 4.68  # Prozent p.a.

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

def berechne_zinsen(saldo, zinsbeginn_str):
    """
    Berechnet Zinsen seit Zinsbeginn
    
    Args:
        saldo: Aktueller Saldo (positiv)
        zinsbeginn_str: Zinsbeginn als 'YYYY-MM-DD'
    
    Returns:
        tuple: (zinsen_gesamt, zinsen_monat, tage_seit_zinsbeginn)
    """
    if not zinsbeginn_str or saldo <= 0:
        return 0.0, 0.0, 0
    
    try:
        zinsbeginn = datetime.strptime(zinsbeginn_str, '%Y-%m-%d')
        heute = datetime.now()
        
        # Nur Zinsen wenn Zinsbeginn in der Vergangenheit
        if zinsbeginn > heute:
            return 0.0, 0.0, 0
        
        tage = (heute - zinsbeginn).days
        
        # Zinsen = Saldo × Zinssatz × Tage / 365
        zinsen_gesamt = saldo * (HYUNDAI_ZINSSATZ / 100) * tage / 365
        
        # Monatszinsen (30 Tage)
        zinsen_monat = saldo * (HYUNDAI_ZINSSATZ / 100) * 30 / 365
        
        return round(zinsen_gesamt, 2), round(zinsen_monat, 2), tage
    except:
        return 0.0, 0.0, 0

def get_latest_csv():
    csv_files = list(Path(CSV_DIR).glob('stockList_*.csv'))
    if not csv_files:
        return None
    return max(csv_files, key=lambda p: p.stat().st_mtime)

def import_hyundai_finance(csv_file=None, dry_run=False):
    print("\n" + "="*70)
    print("📥 HYUNDAI FINANCE - FAHRZEUGFINANZIERUNGEN IMPORT (MIT ZINSEN)")
    print("="*70)
    print(f"💰 Zinssatz: {HYUNDAI_ZINSSATZ}% p.a.")
    
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
    total_zinsen = 0.0
    fz_mit_zinsen = 0
    
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
                
                # Berechne Alter in Tagen (seit Vertragsbeginn)
                alter_tage = 0
                if vertragsbeginn:
                    try:
                        start = datetime.strptime(vertragsbeginn, '%Y-%m-%d')
                        alter_tage = (datetime.now() - start).days
                    except:
                        pass
                
                # === NEU: ZINSEN BERECHNEN ===
                zinsen_gesamt, zinsen_monat, zins_tage = berechne_zinsen(aktueller_saldo, zins_startdatum)
                
                if zinsen_gesamt > 0:
                    total_zinsen += zinsen_gesamt
                    fz_mit_zinsen += 1
                
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
                    'zins_tage': zins_tage,  # NEU
                    'zinsen_gesamt': zinsen_gesamt,  # NEU
                    'zinsen_monat': zinsen_monat,  # NEU
                    'modell': modell,
                    'hersteller': hersteller,
                    'rrdi': 'Hyundai',
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
    
    # === NEU: ZINSEN-STATISTIK ===
    print(f"\n💰 ZINSEN (berechnet mit {HYUNDAI_ZINSSATZ}% p.a.):")
    print(f"   Fahrzeuge mit Zinsen: {fz_mit_zinsen}")
    print(f"   Zinsen GESAMT:        {total_zinsen:>12,.2f} €")
    print(f"   Zinsen pro Monat:     {total_zinsen / max(1, fz_mit_zinsen) * 30 / 365 * fz_mit_zinsen:>12,.2f} € (geschätzt)")
    
    print(f"\n📋 TOP 5 FAHRZEUGE MIT HÖCHSTEN ZINSEN:")
    sorted_by_zinsen = sorted(vehicles, key=lambda x: x['zinsen_gesamt'], reverse=True)[:5]
    for i, v in enumerate(sorted_by_zinsen, 1):
        print(f"   {i}. {v['vin'][-8:]}")
        print(f"      Modell:       {v['modell'][:45]}")
        print(f"      Saldo:        {v['aktueller_saldo']:>10,.2f} €")
        print(f"      Zinsbeginn:   {v['zins_startdatum'] or 'n/a'} ({v['zins_tage']} Tage)")
        print(f"      Zinsen:       {v['zinsen_gesamt']:>10,.2f} €")
    
    if dry_run:
        print(f"\n🔍 DRY-RUN - Keine Änderungen in DB")
        return True
    
    # Import in DB
    try:
        print(f"\n💾 IMPORT IN DATENBANK...")
        
        # Alte Hyundai-Einträge löschen
        cursor.execute("DELETE FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Hyundai Finance'")
        deleted = cursor.rowcount
        print(f"   🗑️  {deleted} alte Einträge gelöscht")
        
        # Neue einfügen
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
                    zinsen_gesamt,
                    zinsen_letzte_periode,
                    datei_quelle,
                    import_datum
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                v['zinsen_gesamt'],  # NEU
                v['zinsen_monat'],   # NEU (als "letzte Periode" = Monatszins)
                csv_path.name,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            insert_count += 1
        
        conn.commit()
        print(f"   ✅ {insert_count} Fahrzeuge importiert")
        
        # Verify
        cursor.execute("""
            SELECT COUNT(*), SUM(aktueller_saldo), SUM(original_betrag), SUM(zinsen_gesamt)
            FROM fahrzeugfinanzierungen
            WHERE finanzinstitut = 'Hyundai Finance'
        """)
        count, saldo, original, zinsen = cursor.fetchone()
        print(f"\n✅ IMPORT ERFOLGREICH!")
        print(f"   Fahrzeuge in DB:  {count}")
        print(f"   Gesamtsaldo:      {saldo:,.2f} €")
        print(f"   Original-Betrag:  {original:,.2f} €")
        print(f"   Zinsen (ber.):    {zinsen:,.2f} €")
        
        # Zeige alle Banken
        print(f"\n📊 ÜBERSICHT ALLE BANKEN:")
        cursor.execute("""
            SELECT 
                finanzinstitut,
                COUNT(*) as anzahl,
                SUM(aktueller_saldo) as saldo,
                SUM(original_betrag) as original,
                SUM(zinsen_gesamt) as zinsen
            FROM fahrzeugfinanzierungen
            GROUP BY finanzinstitut
            ORDER BY finanzinstitut
        """)
        
        total_count = 0
        total_saldo = 0
        total_original = 0
        total_zinsen = 0
        
        for bank, cnt, saldo, original, zinsen in cursor.fetchall():
            zinsen = zinsen or 0
            print(f"   {bank:20s} {cnt:3d} Fz.  Saldo: {saldo:>12,.2f} €  Zinsen: {zinsen:>8,.2f} €")
            total_count += cnt
            total_saldo += saldo or 0
            total_original += original or 0
            total_zinsen += zinsen
        
        print(f"   {'-'*75}")
        print(f"   {'GESAMT':20s} {total_count:3d} Fz.  Saldo: {total_saldo:>12,.2f} €  Zinsen: {total_zinsen:>8,.2f} €")
        
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
