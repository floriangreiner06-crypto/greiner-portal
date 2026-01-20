#!/usr/bin/env python3
"""
Vollständige Analyse der Locosoft CSV-Datei
Ziel: Locosoft-Logik für St-Anteil nachvollziehen
"""

import pandas as pd
import re
from datetime import datetime
from collections import defaultdict
import sys

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
    if pd.isna(prozent_str) or str(prozent_str).strip() in ['', '--', '-""-', 'nan', '                     ']:
        return 0.0
    try:
        prozent_str = str(prozent_str).strip().replace(',', '.').replace('%', '')
        return float(prozent_str)
    except:
        return 0.0

def main():
    file_path = '/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/locosoft_zeit/Stempelzeiten-Übersicht 01.10.25 - 08.01.26.csv'
    
    print("="*80)
    print("LOCOSOFT CSV ANALYSE - St-Anteil Logik")
    print("="*80)
    print()
    
    # Lese CSV
    print(f"📂 Lese CSV: {file_path}")
    print()
    
    # Lese mit Tab-Separator, skip erste 4 Zeilen (Header ist in Zeile 4, 0-indexed)
    df = pd.read_csv(
        file_path,
        encoding='latin-1',
        sep='\t',
        skiprows=4,
        skipinitialspace=True,
        on_bad_lines='skip',
        low_memory=False
    )
    
    # Bereinige Spalten-Namen
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace(r'^<@@B[^>]*>', '', regex=True).str.strip()
    
    # Manuelle Spalten-Zuordnung (erste Spalte ist leer wegen Präfix)
    # Spalten: '', 'MA', 'Name', 'von', 'bis', 'Unnamed: 5', 'Dauer', 'Auftrag', 'Pos. Art Text', ...
    # Wir verwenden die tatsächlichen Spalten-Namen
    
    print(f"✅ CSV geladen: {len(df)} Zeilen, {len(df.columns)} Spalten")
    print(f"Spalten: {list(df.columns[:15])}")
    print()
    
    # Filtere nur Zeilen mit Stempelungen
    # Eine Stempelung hat: von, bis, Dauer, Auftrag (nicht leer)
    stempelungen = df[
        (df['von'].notna()) &
        (df['von'].astype(str).str.contains(':', na=False, regex=False)) &
        (~df['von'].astype(str).str.contains('KOMMT|GEHT', na=False, case=False)) &
        (df['bis'].notna()) &
        (df['bis'].astype(str).str.contains(':', na=False, regex=False)) &
        (~df['bis'].astype(str).str.contains('KOMMT|GEHT', na=False, case=False)) &
        (df['Dauer'].notna()) &
        (df['Dauer'].astype(str).str.contains(':', na=False, regex=False)) &
        (df['Auftrag'].notna()) &
        (df['Auftrag'].astype(str).str.strip() != '') &
        (~df['Auftrag'].astype(str).str.contains('Arbeitszeit|Mitarb|Meister', na=False, case=False))
    ].copy()
    
    print(f"📊 Stempelungen gefunden: {len(stempelungen)} Zeilen")
    print()
    
    if len(stempelungen) == 0:
        print("❌ Keine Stempelungen gefunden! Prüfe Filter...")
        print()
        print("Erste 20 Zeilen mit MA oder Zeit:")
        for idx in range(min(20, len(df))):
            row = df.iloc[idx]
            ma = str(row.get('MA', '')).strip()
            von = str(row.get('von', '')).strip()
            bis = str(row.get('bis', '')).strip()
            dauer = str(row.get('Dauer', '')).strip()
            auftrag = str(row.get('Auftrag', '')).strip()
            if ma or ':' in von or ':' in bis or ':' in dauer or auftrag:
                print(f"  Zeile {idx}: MA={ma}, von={von}, bis={bis}, Dauer={dauer}, Auftrag={auftrag}")
        return
    
    # Konvertiere Daten
    stempelungen['dauer_min'] = stempelungen['Dauer'].apply(parse_zeit)
    stempelungen['auaw_min'] = stempelungen['AuAW'].apply(parse_zeit)
    stempelungen['aw_ant_min'] = stempelungen['AW-Ant.'].apply(parse_zeit)
    stempelungen['st_ant_min'] = stempelungen['St-Ant.'].apply(parse_zeit)
    stempelungen['st_ant_pct'] = stempelungen['St-Ant.'].apply(parse_prozent)
    stempelungen['lstgrad_pct'] = stempelungen['%Lstgrad'].apply(parse_prozent)
    
    # Filtere nur Zeilen mit Daten
    stempelungen_clean = stempelungen[
        (stempelungen['dauer_min'] > 0) |
        (stempelungen['auaw_min'] > 0) |
        (stempelungen['aw_ant_min'] > 0) |
        (stempelungen['st_ant_min'] > 0) |
        (stempelungen['st_ant_pct'] > 0)
    ].copy()
    
    print(f"📊 Stempelungen mit Daten: {len(stempelungen_clean)} Zeilen")
    print()
    
    # Analysiere St-Anteil
    print("="*80)
    print("ANALYSE: St-Anteil")
    print("="*80)
    print()
    
    # Zeilen mit St-Anteil in Minuten
    st_ant_minuten = stempelungen_clean[stempelungen_clean['st_ant_min'] > 0].copy()
    print(f"Zeilen mit St-Anteil in Minuten: {len(st_ant_minuten)}")
    
    # Zeilen mit St-Anteil in Prozent
    st_ant_prozent = stempelungen_clean[stempelungen_clean['st_ant_pct'] > 0].copy()
    print(f"Zeilen mit St-Anteil in Prozent: {len(st_ant_prozent)}")
    print()
    
    # Zeige Beispiele
    if len(st_ant_minuten) > 0:
        print("Beispiele mit St-Anteil in Minuten:")
        print("-"*80)
        for idx, row in st_ant_minuten.head(10).iterrows():
            print(f"MA: {row['MA']}, Auftrag: {row['Auftrag']}, Pos: {row['Pos. Art Text']}")
            print(f"  Dauer: {row['Dauer']} ({row['dauer_min']:.1f} Min)")
            print(f"  AuAW: {row['AuAW']} ({row['auaw_min']:.1f} Min)")
            print(f"  AW-Ant.: {row['AW-Ant.']} ({row['aw_ant_min']:.1f} Min)")
            print(f"  St-Ant.: {row['St-Ant.']} ({row['st_ant_min']:.1f} Min)")
            print(f"  %Lstgrad: {row['%Lstgrad']} ({row['lstgrad_pct']:.1f}%)")
            print()
    
    if len(st_ant_prozent) > 0:
        print("Beispiele mit St-Anteil in Prozent:")
        print("-"*80)
        for idx, row in st_ant_prozent.head(10).iterrows():
            print(f"MA: {row['MA']}, Auftrag: {row['Auftrag']}, Pos: {row['Pos. Art Text']}")
            print(f"  Dauer: {row['Dauer']} ({row['dauer_min']:.1f} Min)")
            print(f"  AuAW: {row['AuAW']} ({row['auaw_min']:.1f} Min)")
            print(f"  AW-Ant.: {row['AW-Ant.']} ({row['aw_ant_min']:.1f} Min)")
            print(f"  St-Ant.: {row['St-Ant.']} ({row['st_ant_pct']:.1f}%)")
            print(f"  %Lstgrad: {row['%Lstgrad']} ({row['lstgrad_pct']:.1f}%)")
            print()
    
    # Gruppiere nach Mechaniker
    print("="*80)
    print("SUMMEN PRO MECHANIKER")
    print("="*80)
    print()
    
    # Summiere St-Anteil pro Mechaniker
    mechaniker_sums = defaultdict(lambda: {
        'dauer_sum': 0.0,
        'auaw_sum': 0.0,
        'aw_ant_sum': 0.0,
        'st_ant_min_sum': 0.0,
        'st_ant_pct_sum': 0.0,
        'st_ant_pct_count': 0,
        'anzahl': 0
    })
    
    for idx, row in stempelungen_clean.iterrows():
        ma = str(row['MA']).strip()
        if ma and ma != 'nan' and ma.isdigit():
            ma_num = int(ma)
            mechaniker_sums[ma_num]['dauer_sum'] += row['dauer_min']
            mechaniker_sums[ma_num]['auaw_sum'] += row['auaw_min']
            mechaniker_sums[ma_num]['aw_ant_sum'] += row['aw_ant_min']
            mechaniker_sums[ma_num]['st_ant_min_sum'] += row['st_ant_min']
            if row['st_ant_pct'] > 0:
                mechaniker_sums[ma_num]['st_ant_pct_sum'] += row['st_ant_pct']
                mechaniker_sums[ma_num]['st_ant_pct_count'] += 1
            mechaniker_sums[ma_num]['anzahl'] += 1
    
    # Zeige Top 10 Mechaniker
    print("Top 10 Mechaniker (nach St-Anteil Summe):")
    print("-"*80)
    sorted_mechs = sorted(mechaniker_sums.items(), key=lambda x: x[1]['st_ant_min_sum'], reverse=True)
    
    for ma, data in sorted_mechs[:10]:
        print(f"MA {ma}:")
        print(f"  Anzahl Zeilen: {data['anzahl']}")
        print(f"  Dauer Summe: {data['dauer_sum']:.1f} Min ({data['dauer_sum']/60:.2f} h)")
        print(f"  AuAW Summe: {data['auaw_sum']:.1f} Min ({data['auaw_sum']/60:.2f} h)")
        print(f"  AW-Ant. Summe: {data['aw_ant_sum']:.1f} Min ({data['aw_ant_sum']/60:.2f} h)")
        print(f"  St-Ant. Summe: {data['st_ant_min_sum']:.1f} Min ({data['st_ant_min_sum']/60:.2f} h)")
        if data['st_ant_pct_count'] > 0:
            print(f"  St-Ant. Prozent (Ø): {data['st_ant_pct_sum']/data['st_ant_pct_count']:.1f}%")
        print()
    
    # Speichere in CSV für weitere Analyse
    output_file = '/opt/greiner-portal/scripts/locosoft_analyse_export.csv'
    stempelungen_clean.to_csv(output_file, index=False, encoding='utf-8')
    print(f"✅ Daten exportiert nach: {output_file}")
    print()

if __name__ == '__main__':
    main()
