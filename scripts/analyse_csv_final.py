#!/usr/bin/env python3
# FINALE CSV-ANALYSE: Finde die ECHTE Formel
import pandas as pd
import numpy as np

csv_file = '/opt/greiner-portal/scripts/locosoft_analyse_export.csv'
df = pd.read_csv(csv_file, encoding='utf-8', sep=',')

df['dauer_min'] = pd.to_numeric(df['dauer_min'], errors='coerce')
df['st_ant_pct'] = pd.to_numeric(df['st_ant_pct'], errors='coerce')
df['auaw_min'] = pd.to_numeric(df['auaw_min'], errors='coerce')
df['aw_ant_min'] = pd.to_numeric(df['aw_ant_min'], errors='coerce')

df_valid = df[(df['dauer_min'] > 0)].copy()
df_valid['st_ant_min'] = df_valid['dauer_min'] * (df_valid['st_ant_pct'] / 100)

# Prüfe: Gibt es Positionen OHNE AW mit St-Anteil > 0?
df_ohne_aw = df_valid[(df_valid['auaw_min'] == 0) & (df_valid['st_ant_pct'] > 0)].copy()

print('Positionen OHNE AW mit St-Anteil > 0:')
print(f'  Anzahl: {len(df_ohne_aw)}')
if len(df_ohne_aw) > 0:
    st_ant_sum = df_ohne_aw['st_ant_min'].sum()
    dauer_sum = df_ohne_aw['dauer_min'].sum()
    print(f'  Summe St-Anteil: {st_ant_sum:.0f} Min')
    print(f'  Summe Dauer: {dauer_sum:.0f} Min')
    print()
    print('Erste 10 Beispiele:')
    print(df_ohne_aw[['dauer_min', 'auaw_min', 'st_ant_pct', 'st_ant_min']].head(10))
else:
    print('  Keine! Positionen OHNE AW haben St-Anteil = 0')
    print()
    print('Das bedeutet: Die Formel funktioniert nur für Positionen MIT AW!')
    print()
    print('Teste: St-Anteil = Dauer × (AuAW / Gesamt-AuAW) für Positionen MIT AW')
    print('  + Positionen OHNE AW werden NICHT berücksichtigt')
    
    df_mit_aw = df_valid[df_valid['auaw_min'] > 0].copy()
    df_mit_aw['gesamt_auaw'] = df_mit_aw.groupby(['von', 'bis'])['auaw_min'].transform('sum')
    df_mit_aw['st_ant_formel'] = df_mit_aw['dauer_min'] * (df_mit_aw['auaw_min'] / df_mit_aw['gesamt_auaw'])
    
    st_ant_formel_sum = df_mit_aw['st_ant_formel'].sum()
    st_ant_csv_sum = df_valid['st_ant_min'].sum()
    
    print(f'  Formel Summe: {st_ant_formel_sum:.0f} Min')
    print(f'  CSV Summe: {st_ant_csv_sum:.0f} Min')
    diff = abs(st_ant_formel_sum - st_ant_csv_sum)
    diff_pct = (diff / st_ant_csv_sum * 100) if st_ant_csv_sum > 0 else 0
    print(f'  Differenz: {diff:.0f} Min ({diff_pct:.1f}%)')
