#!/usr/bin/env python3
"""
Update konto_snapshots mit Zinssätzen
======================================
Liest PDFs nochmal und trägt Zinssätze nach
"""

import sys
import re
import sqlite3
from pathlib import Path
import pdfplumber

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

def extract_zinssatz(pdf_path):
    """Extrahiert Zinssatz aus PDF"""
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()
    
    # Suche alle %-Werte
    prozente = re.findall(r'(\d+,\d+)\s*%', text)
    
    # Der erste sollte der Zinssatz sein (normalerweise ~4%)
    if prozente:
        zins_str = prozente[0].replace(',', '.')
        return float(zins_str)
    
    return None

def main():
    print("=" * 70)
    print("UPDATE SNAPSHOTS MIT ZINSSÄTZEN")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Hole alle Snapshots ohne Zinssatz
    cursor.execute("""
        SELECT id, stichtag, pdf_quelle
        FROM konto_snapshots
        WHERE konto_id = 23 AND (zinssatz IS NULL OR zinssatz = 0)
        ORDER BY stichtag
    """)
    
    snapshots = cursor.fetchall()
    print(f"Gefunden: {len(snapshots)} Snapshots ohne Zinssatz\n")
    
    pdf_dir = Path('/mnt/buchhaltung/Buchhaltung/Kontoauszüge/Genobank Darlehenskonten')
    updated = 0
    errors = 0
    
    for snap_id, stichtag, pdf_quelle in snapshots:
        pdf_path = pdf_dir / pdf_quelle
        
        print(f"📄 {stichtag} | {pdf_quelle[:50]}...", end=' ')
        
        if not pdf_path.exists():
            print("❌ PDF nicht gefunden")
            errors += 1
            continue
        
        try:
            zinssatz = extract_zinssatz(pdf_path)
            
            if zinssatz:
                cursor.execute("""
                    UPDATE konto_snapshots
                    SET zinssatz = ?
                    WHERE id = ?
                """, (zinssatz, snap_id))
                print(f"✅ {zinssatz:.5f}%")
                updated += 1
            else:
                print("⚠️  Kein Zinssatz gefunden")
        
        except Exception as e:
            print(f"❌ {str(e)[:40]}")
            errors += 1
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"✅ Aktualisiert: {updated}")
    print(f"❌ Fehler:       {errors}")
    
    # Zeige Ergebnis
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as anzahl,
            AVG(zinssatz) as avg_zins,
            MIN(zinssatz) as min_zins,
            MAX(zinssatz) as max_zins
        FROM konto_snapshots
        WHERE konto_id = 23 AND zinssatz IS NOT NULL
    """)
    
    row = cursor.fetchone()
    if row and row[0] > 0:
        print(f"\n📊 ZINSSÄTZE:")
        print(f"  Snapshots mit Zinssatz: {row[0]}")
        print(f"  Durchschnitt: {row[1]:.5f}%")
        print(f"  Min: {row[2]:.5f}%")
        print(f"  Max: {row[3]:.5f}%")
    
    conn.close()
    print("\n✅ Fertig!\n")

if __name__ == '__main__':
    main()
