#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIBU-Export Analyse - Finde die fehlenden 181k €!
==================================================

Analysiert die FIBUEXPO-BUCHUNGEN.csv von Locosoft und vergleicht
mit unserer v2.2 Kategorisierung um die fehlenden Kosten zu finden.

Author: Claude (TAG 46)
Date: 2025-11-15
"""

import csv
import sqlite3
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# Pfade
PROJECT_ROOT = Path("/opt/greiner-portal")
CSV_FILE = PROJECT_ROOT / "FIBUEXPO-BUCHUNGEN.csv"
SQLITE_DB = PROJECT_ROOT / "data" / "greiner_controlling.db"

def parse_csv():
    """
    Liest die FIBUEXPO-BUCHUNGEN.csv und aggregiert nach Sachkonto
    
    Returns:
        dict: {sachkonto: {'soll': float, 'haben': float, 'netto': float}}
    """
    print("📥 Lese FIBUEXPO-BUCHUNGEN.csv...")
    
    konten = defaultdict(lambda: {'soll': 0.0, 'haben': 0.0, 'netto': 0.0})
    
    with open(CSV_FILE, 'r', encoding='latin-1') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        zeilen_gesamt = 0
        zeilen_sep_okt = 0
        
        for row in reader:
            zeilen_gesamt += 1
            
            # Nur 331W Zeilen (Buchungen)
            if not row.get('331H', '').startswith('331W'):
                # Erste Spalte checken
                first_val = list(row.values())[0] if row else ''
                if not first_val.startswith('331W'):
                    continue
            
            # Datum parsen (Spalte "Belegdatum")
            datum_str = row.get('Belegdatum', '').strip()
            if not datum_str:
                # Erste Spalte nach dem Marker könnte Datum sein
                vals = list(row.values())
                if len(vals) > 1:
                    datum_str = vals[1].strip()
            
            if not datum_str:
                continue
                
            try:
                # Datum Format: DD.MM.YYYY
                datum = datetime.strptime(datum_str, '%d.%m.%Y').date()
            except:
                continue
            
            # Nur Sep + Okt 2025
            if not (datum.year == 2025 and datum.month in [9, 10]):
                continue
            
            zeilen_sep_okt += 1
            
            # Sachkonto (Spalte "Kontonummer")
            konto_str = row.get('Kontonummer', '').strip()
            if not konto_str:
                # Könnte an anderer Stelle sein
                vals = list(row.values())
                if len(vals) > 6:
                    konto_str = vals[6].strip()
            
            try:
                konto = int(konto_str)
            except:
                continue
            
            # Betrag (Spalte "Buchbetrag")
            betrag_str = row.get('Buchbetrag', '').strip()
            if not betrag_str:
                vals = list(row.values())
                if len(vals) > 12:
                    betrag_str = vals[12].strip()
            
            try:
                betrag = float(betrag_str.replace(',', '.'))
            except:
                continue
            
            # Soll/Haben (Spalte "Soll/Haben")
            sh = row.get('Soll/Haben', '').strip()
            if not sh:
                vals = list(row.values())
                if len(vals) > 13:
                    sh = vals[13].strip()
            
            # Aggregieren
            if sh == 'S':
                konten[konto]['soll'] += betrag
                konten[konto]['netto'] += betrag
            elif sh == 'H':
                konten[konto]['haben'] += betrag
                konten[konto]['netto'] -= betrag
    
    print(f"✅ CSV gelesen:")
    print(f"   Zeilen gesamt: {zeilen_gesamt:,}")
    print(f"   Sep+Okt 2025:  {zeilen_sep_okt:,}")
    print(f"   Konten:        {len(konten):,}")
    print()
    
    return dict(konten)

def get_our_kategorisierung():
    """
    Holt unsere v2.2 Kategorisierung aus SQLite
    
    Returns:
        dict: {sachkonto: kategorie}
    """
    print("📥 Lade unsere Kategorisierung aus SQLite...")
    
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT 
            nominal_account,
            kategorie_erweitert
        FROM fibu_buchungen
        WHERE accounting_date >= '2025-09-01'
          AND accounting_date <= '2025-10-31'
    """)
    
    kategorien = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    
    print(f"✅ {len(kategorien):,} Konten kategorisiert")
    print()
    
    return kategorien

def analyze():
    """
    Hauptanalyse: Findet die fehlenden Kosten
    """
    print("=" * 80)
    print("FIBU-EXPORT ANALYSE - FINDE DIE FEHLENDEN 181k €")
    print("=" * 80)
    print()
    
    # CSV einlesen
    csv_konten = parse_csv()
    
    # Unsere Kategorisierung
    unsere_kat = get_our_kategorisierung()
    
    # Analyse: Welche Bilanz-Konten mit Netto-Soll > 5.000 € fehlen?
    print("🔍 ANALYSE: Bilanz-Konten mit Netto-SOLL > 5.000 €")
    print("   (= potenzielle Kosten die wir als 'bilanz' kategorisiert haben)")
    print()
    print(f"{'Konto':<10} {'Kategorie':<30} {'Soll':>15} {'Haben':>15} {'Netto':>15}")
    print("-" * 90)
    
    verdaechtige = []
    
    for konto, werte in sorted(csv_konten.items()):
        netto = werte['netto']
        
        # Nur Konten mit Netto-Soll > 5.000 €
        if netto < 5000:
            continue
        
        # Kategorie aus unserer DB
        kategorie = unsere_kat.get(konto, 'UNBEKANNT')
        
        # Nur Bilanz-Konten interessant!
        if kategorie == 'bilanz':
            verdaechtige.append((konto, werte['soll'], werte['haben'], netto))
            print(f"{konto:<10} {kategorie:<30} {werte['soll']:>15,.2f} {werte['haben']:>15,.2f} {netto:>15,.2f}")
    
    print()
    print(f"📊 SUMME DER VERDÄCHTIGEN BILANZ-KONTEN:")
    summe_netto = sum(v[3] for v in verdaechtige)
    print(f"   {len(verdaechtige)} Konten mit Netto-Soll > 5.000 €")
    print(f"   Gesamt-Netto: {summe_netto:,.2f} €")
    print()
    
    # Top 20 anzeigen
    print("🎯 TOP 20 VERDÄCHTIGE (nach Netto-Soll):")
    print()
    for konto, soll, haben, netto in sorted(verdaechtige, key=lambda x: x[3], reverse=True)[:20]:
        print(f"   {konto:<10} Soll: {soll:>12,.2f} € | Haben: {haben:>12,.2f} € | Netto: {netto:>12,.2f} €")
    
    print()
    print("=" * 80)
    print("✅ ANALYSE ABGESCHLOSSEN")
    print("=" * 80)

if __name__ == "__main__":
    try:
        analyze()
    except Exception as e:
        print()
        print("❌ FEHLER:")
        print(f"  {e}")
        import traceback
        traceback.print_exc()
        exit(1)
