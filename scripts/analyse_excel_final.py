#!/usr/bin/env python3
"""
FINAL: Analysiert Excel-Daten um die echte Locosoft-Logik zu verstehen
Basierend auf den Hinweisen des Benutzers:
- Ein Mechaniker kann bei einem Auftrag mit gängigen Tätigkeiten gleich 3 Positionen auf 1 mal anstoppen
- Dann wird die Realzeit gleichmäßig auf die drei Vorgabezeiten verteilt
- Stoppen mehrere auf einen Auftrag auf verschiedene Positionen, dann gilt die Vorgabezeit/AW der Position
- Gibt es keine Vorgabe, wird anteilig nach Realzeit verteilt
"""

import pandas as pd
import sys
from collections import defaultdict

def parse_zeit(s):
    if pd.isna(s) or str(s).strip() in ['', '--', '-""-', 'nan']:
        return 0.0
    try:
        parts = str(s).strip().split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return 0.0
    except:
        return 0.0

file_path = '/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/locosoft_zeit/Stempelzeiten-Übersicht 01.01.26 - 15.01.26.csv'

df = pd.read_csv(
    file_path,
    encoding='latin-1',
    sep='\t',
    skiprows=5,
    skipinitialspace=True,
    on_bad_lines='skip',
    low_memory=False
)

df.columns = df.columns.str.strip()

# Filtere nur Zeilen mit Auftrag (Zahl) und MA
df_clean = df[
    (df['Auftrag'].notna()) &
    (df['Auftrag'].astype(str).str.match(r'^\d+$', na=False)) &
    (df['MA'].notna()) &
    (df['MA'].astype(str).str.strip() != '')
].copy()

print(f"Zeilen mit Auftrag und MA: {len(df_clean)}\n")

# Analysiere: Mehrere Positionen mit gleicher Zeit
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

print(f"Gefundene Beispiele mit mehreren Positionen: {len(beispiele)}\n")

# Analysiere Beispiele
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
    
    if bsp['dauer'] > 0:
        print(f"  Verhältnis St-Anteil/Dauer: {bsp['st_anteil_sum']/bsp['dauer']:.3f}")
    
    print(f"  Positionen:")
    for pos in bsp['positions']:
        st = parse_zeit(pos.get('St-Ant.', 0))
        aw = parse_zeit(pos.get('AW-Ant.', 0))
        auaw = parse_zeit(pos.get('AuAW', 0))
        pos_text = str(pos.get('Pos. Art Text', ''))[:60]
        print(f"    - {pos_text}")
        print(f"      St-Ant: {st:.1f} Min, AW-Ant: {aw:.1f} Min, AuAW: {auaw:.1f} Min")
        
        # Prüfe ob St-Anteil nach AuAW verteilt wird
        if bsp['auaw_sum'] > 0 and bsp['dauer'] > 0:
            erwartet = bsp['dauer'] * (auaw / bsp['auaw_sum'])
            print(f"      Erwartet (nach AuAW): {erwartet:.1f} Min, Tatsächlich: {st:.1f} Min, Diff: {abs(st - erwartet):.1f} Min")
    
    print()

# Summiere für Mechaniker 5007 und 5018
print("="*100)
print("SUMMEN PRO MECHANIKER")
print("="*100 + "\n")

for ma_name in ['Reitmeier', 'Majer']:
    ma_data = df_clean[df_clean['MA'].astype(str).str.contains(ma_name, na=False, case=False)]
    if len(ma_data) > 0:
        st_sum = ma_data['St-Ant.'].apply(parse_zeit).sum()
        aw_sum = ma_data['AW-Ant.'].apply(parse_zeit).sum()
        
        print(f"{ma_data.iloc[0]['MA']}:")
        print(f"  St-Anteil Summe: {st_sum:.1f} Min ({st_sum/60:.2f} h)")
        print(f"  AW-Anteil Summe: {aw_sum:.1f} Min ({aw_sum/60:.2f} h)")
        if st_sum > 0:
            lg = (aw_sum / st_sum) * 100
            print(f"  Leistungsgrad: {lg:.1f}%")
        print()
