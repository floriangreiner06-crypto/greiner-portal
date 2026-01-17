#!/usr/bin/env python3
"""
Analysiert die Locosoft CSV-Datei für Dezember (Tobias 5007)
und vergleicht die Werte mit DRIVE und Locosoft-UI.

Datum: 2026-01-XX
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict

# Projekt-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor


def parse_zeit(zeit_str):
    """Konvertiert Zeit-String (HH:MM) in Minuten"""
    if pd.isna(zeit_str) or str(zeit_str).strip() in ['', '--', '-""-', 'nan', '                     ']:
        return 0.0
    try:
        zeit_str = str(zeit_str).strip()
        if ':' in zeit_str:
            parts = zeit_str.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
        return 0.0
    except:
        return 0.0


def parse_prozent(prozent_str):
    """Konvertiert Prozent-String in Float"""
    if pd.isna(prozent_str) or str(prozent_str).strip() in ['', '--', '-""-', 'nan']:
        return 0.0
    try:
        prozent_str = str(prozent_str).strip().replace(',', '.').replace('%', '')
        return float(prozent_str)
    except:
        return 0.0


def parse_datum(datum_str):
    """Konvertiert Datum-String in date-Objekt"""
    if pd.isna(datum_str):
        return None
    try:
        # Format: "01.12.25 Mo."
        datum_str = str(datum_str).strip()
        if '.' in datum_str:
            parts = datum_str.split('.')
            if len(parts) >= 3:
                tag = int(parts[0])
                monat = int(parts[1])
                jahr = int(parts[2].split()[0])  # "25" aus "25 Mo."
                if jahr < 100:
                    jahr += 2000
                return date(jahr, monat, tag)
    except:
        pass
    return None


def analyse_csv_dezember_tobias():
    """Analysiert CSV für Tobias (5007) im Dezember"""
    
    file_path = '/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/locosoft_zeit/Stempelzeiten-Übersicht 01.12.25 - 15.01.26.csv'
    mechaniker_nr = 5007
    von = date(2025, 12, 1)
    bis = date(2025, 12, 8)
    
    print("="*80)
    print("CSV-ANALYSE: Tobias (5007) - Dezember 2025")
    print("="*80)
    print()
    print(f"📂 Datei: {file_path}")
    print(f"👤 Mechaniker: {mechaniker_nr}")
    print(f"📅 Zeitraum: {von} bis {bis}")
    print()
    
    # Lese CSV
    print("📖 Lese CSV-Datei...")
    try:
        df = pd.read_csv(
            file_path,
            encoding='latin-1',
            sep='\t',
            skiprows=4,
            skipinitialspace=True,
            on_bad_lines='skip',
            low_memory=False,
            header=None
        )
        
        # Spalten manuell zuordnen (verschoben!)
        df.columns = ['prefix', 'MA', 'Name', 'von', 'bis', 'dauer_min_str', 'auftrag_nummer', 
                      'position_text', 'auaw1', 'auaw2', 'aw_ant_min_str', 'st_ant_pct_str', 
                      'lstgrad', 'Anwes.', 'Produkt.', 'Pause']
        
        print(f"✅ CSV geladen: {len(df)} Zeilen, {len(df.columns)} Spalten")
        print()
        
    except Exception as e:
        print(f"❌ Fehler beim Lesen der CSV: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Filtere Zeilen für Tobias (5007)
    print("🔍 Filtere Zeilen für Tobias (5007)...")
    
    # Suche nach 5007 in allen Spalten
    tobias_mask = df.astype(str).apply(lambda x: x.str.contains('5007', na=False)).any(axis=1)
    tobias_zeilen = df[tobias_mask].copy()
    
    print(f"📊 Gefunden: {len(tobias_zeilen)} Zeilen mit '5007'")
    if len(tobias_zeilen) > 0:
        print("Erste 5 Zeilen mit 5007:")
        for i, (idx, row) in enumerate(tobias_zeilen.head(5).iterrows(), 1):
            print(f"  {i}. Zeile {idx}: MA={row['MA']}, Name={row['Name']}")
    print()
    
    # Extrahiere Stempelungen (haben von, bis, dauer_min_str, auftrag_nummer)
    stempelungen = []
    aktueller_ma = None
    aktueller_name = None
    aktuelles_datum = None
    
    for idx, row in df.iterrows():
        # Prüfe alle Spalten nach 5007
        row_str = ' '.join([str(x) for x in row.values if pd.notna(x)])
        if '5007' in row_str:
            # Versuche MA-Nummer zu extrahieren
            for col in ['MA', 'Name', 'prefix']:
                val = str(row[col]).strip() if pd.notna(row[col]) else ''
                if '5007' in val:
                    aktueller_ma = 5007
                    aktueller_name = str(row['Name']).strip() if pd.notna(row['Name']) else ''
                    break
        
        ma_str = str(row['MA']).strip() if pd.notna(row['MA']) else ''
        name_str = str(row['Name']).strip() if pd.notna(row['Name']) else ''
        von_str = str(row['von']).strip() if pd.notna(row['von']) else ''
        bis_str = str(row['bis']).strip() if pd.notna(row['bis']) else ''
        dauer_str = str(row['dauer_min_str']).strip() if pd.notna(row['dauer_min_str']) else ''
        auftrag_str = str(row['auftrag_nummer']).strip() if pd.notna(row['auftrag_nummer']) else ''
        
        # Prüfe ob neue MA-Zeile
        if ma_str.isdigit() and int(ma_str) == 5007:
            aktueller_ma = 5007
            aktueller_name = name_str
            aktuelles_datum = parse_datum(name_str)
        
        # Prüfe ob Datum in Name (z.B. "01.12.25 Mo.")
        if aktueller_ma == 5007:
            datum = parse_datum(name_str)
            if datum is not None:
                aktuelles_datum = datum
        
        # Prüfe ob Stempelung (hat von, bis, dauer, auftrag)
        if (aktueller_ma == 5007 and 
            ':' in von_str and ':' in bis_str and 
            ':' in dauer_str and auftrag_str != '' and auftrag_str.isdigit() and
            aktuelles_datum is not None and
            von <= aktuelles_datum <= bis):
            
            dauer_min = parse_zeit(dauer_str)
            aw_ant_min = parse_zeit(row['aw_ant_min_str']) if pd.notna(row['aw_ant_min_str']) else 0
            st_ant_pct = parse_prozent(row['st_ant_pct_str']) if pd.notna(row['st_ant_pct_str']) else 0
            lstgrad_str = str(row['lstgrad']).strip() if pd.notna(row['lstgrad']) else ''
            
            stempelungen.append({
                'datum': aktuelles_datum,
                'von': von_str,
                'bis': bis_str,
                'dauer_min': dauer_min,
                'auftrag': auftrag_str,
                'position': str(row['position_text']).strip() if pd.notna(row['position_text']) else '',
                'aw_ant_min': aw_ant_min,
                'st_ant_pct': st_ant_pct,
                'st_ant_min': dauer_min * (st_ant_pct / 100) if st_ant_pct > 0 else 0,
                'lstgrad': lstgrad_str
            })
    
    print(f"📊 Stempelungen gefunden: {len(stempelungen)}")
    print()
    
    # Summiere Werte
    gesamt_dauer = sum(s['dauer_min'] for s in stempelungen)
    gesamt_aw_ant = sum(s['aw_ant_min'] for s in stempelungen)
    gesamt_st_ant = sum(s['st_ant_min'] for s in stempelungen)
    
    print("="*80)
    print("📊 SUMMEN AUS CSV:")
    print("="*80)
    print(f"  Dauer (Gesamt): {gesamt_dauer:.0f} Min ({gesamt_dauer/60:.2f} h)")
    print(f"  AW-Anteil: {gesamt_aw_ant:.0f} Min ({gesamt_aw_ant/60:.2f} h) = {gesamt_aw_ant/6:.1f} AW")
    print(f"  Stmp.Anteil: {gesamt_st_ant:.0f} Min ({gesamt_st_ant/60:.2f} h)")
    if gesamt_st_ant > 0:
        leistungsgrad_csv = (gesamt_aw_ant / gesamt_st_ant) * 100
        print(f"  Leistungsgrad: {leistungsgrad_csv:.1f}%")
    print()
    
    # Vergleich mit Locosoft-UI (aus Screenshot)
    print("="*80)
    print("📊 VERGLEICH MIT LOCOSOFT-UI (aus Screenshot):")
    print("="*80)
    locosoft_aw_min = 85 * 60 + 6  # 85:06
    locosoft_st_min = 142 * 60 + 23  # 142:23
    locosoft_lg = 59.8
    
    print(f"  AW-Anteil:")
    print(f"    CSV: {gesamt_aw_ant:.0f} Min ({gesamt_aw_ant/60:.2f} h)")
    print(f"    Locosoft-UI: {locosoft_aw_min} Min ({locosoft_aw_min/60:.2f} h)")
    print(f"    Abweichung: {gesamt_aw_ant - locosoft_aw_min:+.0f} Min ({((gesamt_aw_ant - locosoft_aw_min) / locosoft_aw_min * 100):+.1f}%)")
    print()
    print(f"  Stmp.Anteil:")
    print(f"    CSV: {gesamt_st_ant:.0f} Min ({gesamt_st_ant/60:.2f} h)")
    print(f"    Locosoft-UI: {locosoft_st_min} Min ({locosoft_st_min/60:.2f} h)")
    print(f"    Abweichung: {gesamt_st_ant - locosoft_st_min:+.0f} Min ({((gesamt_st_ant - locosoft_st_min) / locosoft_st_min * 100):+.1f}%)")
    print()
    print(f"  Leistungsgrad:")
    if gesamt_st_ant > 0:
        print(f"    CSV: {leistungsgrad_csv:.1f}%")
    print(f"    Locosoft-UI: {locosoft_lg:.1f}%")
    if gesamt_st_ant > 0:
        print(f"    Abweichung: {leistungsgrad_csv - locosoft_lg:+.1f}%")
    print()
    
    # Zeige erste 10 Stempelungen
    print("="*80)
    print("📋 ERSTE 10 STEMPELUNGEN:")
    print("="*80)
    for i, s in enumerate(stempelungen[:10], 1):
        print(f"  {i}. {s['datum']} | {s['von']} - {s['bis']} | Auftrag: {s['auftrag']} | "
              f"Dauer: {s['dauer_min']:.0f} Min | AW-Ant: {s['aw_ant_min']:.0f} Min | "
              f"St-Ant: {s['st_ant_pct']:.1f}% ({s['st_ant_min']:.0f} Min)")
    print()
    
    return {
        'csv_aw_min': gesamt_aw_ant,
        'csv_st_min': gesamt_st_ant,
        'csv_lg': leistungsgrad_csv if gesamt_st_ant > 0 else None,
        'locosoft_aw_min': locosoft_aw_min,
        'locosoft_st_min': locosoft_st_min,
        'locosoft_lg': locosoft_lg,
        'stempelungen': stempelungen
    }


if __name__ == '__main__':
    analyse_csv_dezember_tobias()
