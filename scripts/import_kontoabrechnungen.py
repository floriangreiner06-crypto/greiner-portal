#!/usr/bin/env python3
"""
Kontoabrechnungs-Parser für Darlehenskonten
============================================
Extrahiert aus Quartalsabrechnungen:
- Stichtag
- Kapitalsaldo
- Zinssatz
- Kreditlinie
"""

import sys
import re
import sqlite3
from pathlib import Path
from datetime import datetime
import pdfplumber

sys.path.insert(0, '/opt/greiner-portal')

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

def parse_kontoabrechnung(pdf_path):
    """Parst eine Kontoabrechnung und extrahiert Daten"""
    
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()
    
    data = {
        'stichtag': None,
        'kapitalsaldo': None,
        'kreditlinie': None,
        'zinssatz': None,
        'pdf_quelle': Path(pdf_path).name
    }
    
    # Stichtag extrahieren: "per 31.10.2025"
    match = re.search(r'per (\d{2})\.(\d{2})\.(\d{4})', text)
    if match:
        data['stichtag'] = f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    
    # Kapitalsaldo: "EUR -824.000,00" oder "EUR 824.000,00"
    match = re.search(r'Kapitalsaldo am.*?EUR\s+([-]?\d{1,3}(?:\.\d{3})*,\d{2})', text)
    if match:
        betrag_str = match.group(1).replace('.', '').replace(',', '.')
        data['kapitalsaldo'] = float(betrag_str)
    
    # Kreditlinie: "EUR 824.000,00"
    match = re.search(r'Kontoüberziehungsmöglichkeit:\s*EUR\s+(\d{1,3}(?:\.\d{3})*,\d{2})', text)
    if match:
        betrag_str = match.group(1).replace('.', '').replace(',', '.')
        data['kreditlinie'] = -float(betrag_str)  # NEGATIV speichern!
    
    # Zinssatz: "4,15900 % p.a."
    match = re.search(r'Sollzinssatz.*?(\d+,\d+)\s*%\s*p\.a\.', text)
    if match:
        zins_str = match.group(1).replace(',', '.')
        data['zinssatz'] = float(zins_str)
    
    return data

def import_snapshot(konto_id, data, conn):
    """Schreibt Snapshot in DB"""
    
    if not data['stichtag']:
        return False
    
    # Ausnutzung berechnen
    ausnutzung = None
    if data['kapitalsaldo'] and data['kreditlinie']:
        ausnutzung = abs(data['kapitalsaldo']) / abs(data['kreditlinie']) * 100
    
    cursor = conn.cursor()
    
    # Check ob schon vorhanden
    cursor.execute("""
        SELECT id FROM konto_snapshots 
        WHERE konto_id = ? AND stichtag = ?
    """, (konto_id, data['stichtag']))
    
    if cursor.fetchone():
        return False  # Skip Duplikat
    
    # Insert
    cursor.execute("""
        INSERT INTO konto_snapshots (
            konto_id, stichtag, kapitalsaldo, kreditlinie,
            ausnutzung_prozent, zinssatz, zinstyp, pdf_quelle
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        konto_id,
        data['stichtag'],
        data['kapitalsaldo'],
        data['kreditlinie'],
        ausnutzung,
        data['zinssatz'],
        'Soll',  # Darlehen = Sollzinsen
        data['pdf_quelle']
    ))
    
    conn.commit()
    return True

def main():
    print("=" * 70)
    print("IMPORT KONTOABRECHNUNGEN - 3700057908 Darlehen")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    konto_id = 23  # 3700057908
    
    # Alle Kontoabrechnung-PDFs finden
    pdf_dir = Path('/mnt/buchhaltung/Buchhaltung/Kontoauszüge/Genobank Darlehenskonten')
    pdfs = sorted(pdf_dir.glob('3700057908*Kontoabrechnung*.pdf'))
    
    print(f"Gefunden: {len(pdfs)} Kontoabrechnungen\n")
    
    imported = 0
    skipped = 0
    errors = 0
    
    for pdf in pdfs:
        print(f"📄 {pdf.name[:60]}...", end=' ')
        
        try:
            data = parse_kontoabrechnung(pdf)
            
            if import_snapshot(konto_id, data, conn):
                print(f"✅ {data['stichtag']} | Saldo: {data['kapitalsaldo']:,.0f} | Zins: {data['zinssatz']:.3f}%")
                imported += 1
            else:
                print("⏭️  Duplikat")
                skipped += 1
                
        except Exception as e:
            print(f"❌ {str(e)[:40]}")
            errors += 1
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"✅ Importiert: {imported}")
    print(f"⏭️  Duplikate:  {skipped}")
    print(f"❌ Fehler:     {errors}")
    
    # Status anzeigen
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*), 
               MIN(stichtag), 
               MAX(stichtag),
               AVG(zinssatz),
               AVG(ausnutzung_prozent)
        FROM konto_snapshots 
        WHERE konto_id = ?
    """, (konto_id,))
    
    row = cursor.fetchone()
    if row and row[0] > 0:
        count, min_date, max_date, avg_zins, avg_ausnutzung = row
        
        print("\n📊 KONTO-SNAPSHOTS:")
        print(f"  Anzahl: {count}")
        print(f"  Zeitraum: {min_date} bis {max_date}")
        print(f"  Ø Zinssatz: {avg_zins:.3f}%")
        print(f"  Ø Ausnutzung: {avg_ausnutzung:.1f}%")
    
    conn.close()
    print("\n✅ Fertig!\n")

if __name__ == '__main__':
    main()
