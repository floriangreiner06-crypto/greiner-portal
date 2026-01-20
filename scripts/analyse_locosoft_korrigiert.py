#!/usr/bin/env python3
"""
Korrigierte Analyse der Locosoft CSV-Datei
Ziel: Locosoft-Logik für St-Anteil nachvollziehen

WICHTIG: Die CSV-Spalten sind verschoben!
- "Dauer" = Auftrag (Nummer)
- "Auftrag" = Position (Text)
- "Pos. Art Text" = AuAW (Vorgabezeit)
- "AuAW" = AW-Ant. (AW-Anteil in Minuten)
- "AW-Ant." = St-Ant. (St-Anteil in Prozent!)
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
    print("LOCOSOFT CSV ANALYSE - St-Anteil Logik (KORRIGIERT)")
    print("="*80)
    print()
    
    # Lese CSV ohne Header, dann manuell zuordnen
    print(f"📂 Lese CSV: {file_path}")
    print()
    
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
    # Tatsächliche Struktur:
    # Spalte 0: prefix (leer)
    # Spalte 1: MA (leer bei Fortsetzung)
    # Spalte 2: Name (kann Zeit enthalten bei Fortsetzung)
    # Spalte 3: von
    # Spalte 4: bis
    # Spalte 5: flag/Dauer (0:32 = Dauer in Minuten!)
    # Spalte 6: Dauer/Auftrag (312553 = Auftrag Nummer)
    # Spalte 7: Auftrag/Position (1,02 W... = Position Text)
    # Spalte 8: Pos. Art Text/AuAW (0:24 = AuAW)
    # Spalte 9: AuAW (0:24 = auch AuAW?)
    # Spalte 10: AW-Ant. (0:32 = AW-Anteil in Minuten)
    # Spalte 11: St-Ant. (75,0% = St-Anteil in Prozent!)
    # Spalte 12: %Lstgrad (4:56 = Leistungsgrad?)
    df.columns = ['prefix', 'MA', 'Name', 'von', 'bis', 'dauer_min_str', 'auftrag_nummer', 'position_text', 'auaw1', 'auaw2', 'aw_ant_min_str', 'st_ant_pct_str', 'lstgrad', 'Anwes.', 'Produkt.', 'Pause']
    
    print(f"✅ CSV geladen: {len(df)} Zeilen, {len(df.columns)} Spalten")
    print()
    
    # Filtere nur Zeilen mit Stempelungen
    # Eine Stempelung hat: von, bis, dauer_min_str, auftrag_nummer
    stempelungen = df[
        (df['von'].notna()) &
        (df['von'].astype(str).str.contains(':', na=False, regex=False)) &
        (~df['von'].astype(str).str.contains('KOMMT|GEHT', na=False, case=False)) &
        (df['bis'].notna()) &
        (df['bis'].astype(str).str.strip() != '') &
        (df['auftrag_nummer'].notna()) &
        (df['auftrag_nummer'].astype(str).str.strip() != '') &
        (~df['auftrag_nummer'].astype(str).str.contains('Mitarb|Meister|Arbeitszeit', na=False, case=False))
    ].copy()
    
    print(f"📊 Stempelungen gefunden: {len(stempelungen)} Zeilen")
    print()
    
    if len(stempelungen) == 0:
        print("❌ Keine Stempelungen gefunden!")
        return
    
    # Korrigierte Spalten-Zuordnung
    stempelungen['auftrag_nummer'] = stempelungen['auftrag_nummer'].astype(str).str.strip()
    stempelungen['position_text'] = stempelungen['position_text'].astype(str).str.strip()
    stempelungen['dauer_min'] = stempelungen['dauer_min_str'].apply(parse_zeit)  # Spalte 5 = Dauer in Minuten
    stempelungen['auaw_min'] = stempelungen['auaw1'].apply(parse_zeit)  # Spalte 8 = AuAW
    stempelungen['aw_ant_min'] = stempelungen['aw_ant_min_str'].apply(parse_zeit)  # Spalte 10 = AW-Anteil in Minuten
    stempelungen['st_ant_pct'] = stempelungen['st_ant_pct_str'].apply(parse_prozent)  # Spalte 11 = St-Anteil in Prozent!
    
    # Dauer ist bereits in Spalte 5 (dauer_min_str), wird oben geparst
    
    # Filtere nur Zeilen mit Daten
    stempelungen_clean = stempelungen[
        (stempelungen['dauer_min'] > 0) |
        (stempelungen['auaw_min'] > 0) |
        (stempelungen['aw_ant_min'] > 0) |
        (stempelungen['st_ant_pct'] > 0)
    ].copy()
    
    print(f"📊 Stempelungen mit Daten: {len(stempelungen_clean)} Zeilen")
    print()
    
    # Analysiere St-Anteil
    print("="*80)
    print("ANALYSE: St-Anteil")
    print("="*80)
    print()
    
    # Zeilen mit St-Anteil in Prozent
    st_ant_prozent = stempelungen_clean[stempelungen_clean['st_ant_pct'] > 0].copy()
    print(f"Zeilen mit St-Anteil in Prozent: {len(st_ant_prozent)}")
    print()
    
    # Zeige Beispiele
    if len(st_ant_prozent) > 0:
        print("Beispiele mit St-Anteil:")
        print("-"*80)
        for idx, row in st_ant_prozent.head(15).iterrows():
            ma = str(row['MA']).strip()
            if not ma or ma == 'nan':
                # Suche vorherige Zeile mit MA
                for prev_idx in range(idx-1, max(0, idx-10), -1):
                    prev_ma = str(df.iloc[prev_idx]['MA']).strip()
                    if prev_ma and prev_ma != 'nan' and prev_ma.isdigit():
                        ma = prev_ma
                        break
            
            print(f"MA: {ma}, Auftrag: {row['auftrag_nummer']}, Pos: {row['position_text'][:50]}")
            print(f"  von: {row['von']}, bis: {row['bis']}, Dauer: {row['dauer_min']:.1f} Min")
            print(f"  AuAW: {row['auaw_min']:.1f} Min")
            print(f"  AW-Ant.: {row['aw_ant_min']:.1f} Min")
            print(f"  St-Ant.: {row['st_ant_pct']:.1f}%")
            
            # Berechne St-Anteil in Minuten aus Prozent
            if row['dauer_min'] > 0:
                st_ant_min_calc = row['dauer_min'] * (row['st_ant_pct'] / 100.0)
                print(f"  St-Anteil (berechnet aus %): {st_ant_min_calc:.1f} Min")
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
        'anzahl': 0
    })
    
    current_ma = None
    for idx, row in stempelungen_clean.iterrows():
        ma = str(row['MA']).strip()
        if ma and ma != 'nan' and ma.isdigit():
            current_ma = int(ma)
        
        if current_ma:
            mechaniker_sums[current_ma]['dauer_sum'] += row['dauer_min']
            mechaniker_sums[current_ma]['auaw_sum'] += row['auaw_min']
            mechaniker_sums[current_ma]['aw_ant_sum'] += row['aw_ant_min']
            
            # St-Anteil in Minuten aus Prozent berechnen
            if row['st_ant_pct'] > 0 and row['dauer_min'] > 0:
                st_ant_min = row['dauer_min'] * (row['st_ant_pct'] / 100.0)
                mechaniker_sums[current_ma]['st_ant_min_sum'] += st_ant_min
            
            mechaniker_sums[current_ma]['anzahl'] += 1
    
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
        print()
    
    # Speichere in CSV für weitere Analyse
    output_file = '/opt/greiner-portal/scripts/locosoft_analyse_export.csv'
    stempelungen_clean.to_csv(output_file, index=False, encoding='utf-8')
    print(f"✅ Daten exportiert nach: {output_file}")
    print()

if __name__ == '__main__':
    main()
