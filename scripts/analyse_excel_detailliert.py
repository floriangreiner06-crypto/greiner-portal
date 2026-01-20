#!/usr/bin/env python3
"""
Detaillierte Analyse der Excel-Daten - versteht die echte Locosoft-Logik
"""

import pandas as pd
import sys
from pathlib import Path
from collections import defaultdict

def parse_zeit(zeit_str):
    """Konvertiert Zeit-String in Minuten"""
    if pd.isna(zeit_str) or str(zeit_str).strip() in ['', '--', 'NaN', '-""-']:
        return 0.0
    try:
        parts = str(zeit_str).strip().split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 60 + int(parts[1])
        return float(zeit_str) * 60
    except:
        return 0.0


def analyse_excel(file_path):
    """Analysiert Excel-Datei detailliert"""
    
    # Lese CSV
    with open(file_path, 'r', encoding='latin-1') as f:
        lines = f.readlines()
        header_row = None
        for i, line in enumerate(lines[:20]):
            if 'von' in line.lower() and 'bis' in line.lower() and 'auftrag' in line.lower():
                header_row = i
                break
        
        if header_row is None:
            header_row = 5
    
    df = pd.read_csv(
        file_path,
        encoding='latin-1',
        sep='\t',
        skiprows=header_row,
        skipinitialspace=True,
        on_bad_lines='skip',
        low_memory=False
    )
    
    df.columns = df.columns.str.strip()
    
    # Filtere nur Zeilen mit Auftrag
    df_clean = df[
        (df['Auftrag'].notna()) & 
        (df['Auftrag'] != '') &
        (df['Auftrag'].astype(str).str.isdigit())
    ].copy()
    
    print(f"\n{'='*100}")
    print(f"ANALYSE: {Path(file_path).name}")
    print(f"{'='*100}\n")
    print(f"Zeilen mit Auftrag: {len(df_clean)}\n")
    
    # Analysiere: Mehrere Positionen mit gleicher Zeit (von/bis)
    print("="*100)
    print("ANALYSE: Mehrere Positionen mit gleicher Zeit (von/bis)")
    print("="*100 + "\n")
    
    # Gruppiere nach MA, Auftrag, von, bis
    grouped = df_clean.groupby(['MA', 'Auftrag', 'von', 'bis'])
    
    beispiele = []
    for (ma, auftrag, von, bis), group in grouped:
        if len(group) > 1:  # Mehrere Positionen
            dauer = parse_zeit(group.iloc[0]['Dauer'])
            st_anteil_sum = group['St-Ant.'].apply(parse_zeit).sum()
            aw_anteil_sum = group['AW-Ant.'].apply(parse_zeit).sum()
            auaw_sum = group['AuAW'].apply(parse_zeit).sum()
            
            beispiele.append({
                'ma': ma,
                'auftrag': auftrag,
                'von': von,
                'bis': bis,
                'dauer': dauer,
                'anzahl_pos': len(group),
                'st_anteil_sum': st_anteil_sum,
                'aw_anteil_sum': aw_anteil_sum,
                'auaw_sum': auaw_sum,
                'positions': group[['Pos. Art Text', 'St-Ant.', 'AW-Ant.', 'AuAW']].to_dict('records')
            })
    
    # Zeige Beispiele
    for i, bsp in enumerate(beispiele[:10]):
        print(f"Beispiel {i+1}:")
        print(f"  MA: {bsp['ma']}")
        print(f"  Auftrag: {bsp['auftrag']}")
        print(f"  Zeit: {bsp['von']} - {bsp['bis']}")
        print(f"  Dauer: {bsp['dauer']:.1f} Min")
        print(f"  Anzahl Positionen: {bsp['anzahl_pos']}")
        print(f"  St-Anteil Summe: {bsp['st_anteil_sum']:.1f} Min")
        print(f"  AW-Anteil Summe: {bsp['aw_anteil_sum']:.1f} Min")
        print(f"  AuAW Summe: {bsp['auaw_sum']:.1f} Min")
        print(f"  Verhältnis St-Anteil/Dauer: {bsp['st_anteil_sum']/bsp['dauer']:.3f}" if bsp['dauer'] > 0 else "  Verhältnis: N/A")
        print(f"  Positionen:")
        for pos in bsp['positions']:
            st = parse_zeit(pos.get('St-Ant.', 0))
            aw = parse_zeit(pos.get('AW-Ant.', 0))
            auaw = parse_zeit(pos.get('AuAW', 0))
            print(f"    - {pos.get('Pos. Art Text', '')}: St-Ant={st:.1f} Min, AW-Ant={aw:.1f} Min, AuAW={auaw:.1f} Min")
        print()
    
    # Analysiere: Wie wird St-Anteil berechnet?
    print("="*100)
    print("ANALYSE: St-Anteil-Berechnung")
    print("="*100 + "\n")
    
    # Fall 1: Eine Position
    print("Fall 1: Eine Position pro Stempelung")
    print("-"*100)
    einzelne = df_clean[df_clean.groupby(['MA', 'Auftrag', 'von', 'bis'])['MA'].transform('count') == 1]
    if len(einzelne) > 0:
        for idx, row in einzelne.head(5).iterrows():
            dauer = parse_zeit(row['Dauer'])
            st_anteil = parse_zeit(row['St-Ant.'])
            auaw = parse_zeit(row['AuAW'])
            aw_anteil = parse_zeit(row['AW-Ant.'])
            
            print(f"  Auftrag {row['Auftrag']}, Pos {row['Pos. Art Text']}")
            print(f"    Dauer: {dauer:.1f} Min, St-Anteil: {st_anteil:.1f} Min")
            if dauer > 0:
                print(f"    Verhältnis: {st_anteil/dauer:.3f}")
            if auaw > 0:
                print(f"    AuAW: {auaw:.1f} Min, AW-Anteil: {aw_anteil:.1f} Min")
            print()
    
    # Fall 2: Mehrere Positionen
    print("\nFall 2: Mehrere Positionen pro Stempelung")
    print("-"*100)
    for bsp in beispiele[:5]:
        print(f"  Auftrag {bsp['auftrag']}, {bsp['anzahl_pos']} Positionen, Dauer: {bsp['dauer']:.1f} Min")
        print(f"    St-Anteil Summe: {bsp['st_anteil_sum']:.1f} Min")
        if bsp['dauer'] > 0:
            print(f"    Verhältnis St-Anteil/Dauer: {bsp['st_anteil_sum']/bsp['dauer']:.3f}")
        
        # Prüfe ob St-Anteil nach AW verteilt wird
        if bsp['auaw_sum'] > 0:
            print(f"    AuAW Summe: {bsp['auaw_sum']:.1f} Min")
            for pos in bsp['positions']:
                st = parse_zeit(pos.get('St-Ant.', 0))
                auaw = parse_zeit(pos.get('AuAW', 0))
                if auaw > 0 and bsp['auaw_sum'] > 0:
                    erwartet = bsp['dauer'] * (auaw / bsp['auaw_sum'])
                    print(f"      Pos {pos.get('Pos. Art Text', '')[:50]}: St-Ant={st:.1f} Min, AuAW={auaw:.1f} Min, Erwartet={erwartet:.1f} Min")
        print()
    
    # Summiere für Mechaniker
    print("="*100)
    print("SUMMEN PRO MECHANIKER")
    print("="*100 + "\n")
    
    for ma in df_clean['MA'].unique()[:5]:
        ma_data = df_clean[df_clean['MA'] == ma]
        st_sum = ma_data['St-Ant.'].apply(parse_zeit).sum()
        aw_sum = ma_data['AW-Ant.'].apply(parse_zeit).sum()
        
        print(f"{ma}:")
        print(f"  St-Anteil Summe: {st_sum:.1f} Min ({st_sum/60:.2f} h)")
        print(f"  AW-Anteil Summe: {aw_sum:.1f} Min ({aw_sum/60:.2f} h)")
        if st_sum > 0:
            lg = (aw_sum / st_sum) * 100
            print(f"  Leistungsgrad: {lg:.1f}%")
        print()


if __name__ == '__main__':
    file_path = '/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/locosoft_zeit/Stempelzeiten-Übersicht 01.01.26 - 15.01.26.csv'
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    analyse_excel(file_path)
