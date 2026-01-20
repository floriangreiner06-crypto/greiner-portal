#!/usr/bin/env python3
# Analysiere Zeit-Strings und Prozentwerte in der CSV
import pandas as pd
import re

csv_file = '/opt/greiner-portal/scripts/locosoft_analyse_export.csv'
df = pd.read_csv(csv_file, encoding='utf-8', sep=',')

# Konvertiere
df['dauer_min'] = pd.to_numeric(df['dauer_min'], errors='coerce')
df['st_ant_pct'] = pd.to_numeric(df['st_ant_pct'], errors='coerce')
df['auaw_min'] = pd.to_numeric(df['auaw_min'], errors='coerce')
df['aw_ant_min'] = pd.to_numeric(df['aw_ant_min'], errors='coerce')

# Parse Zeit-Strings (z.B. "0:32" = 32 Min, "1:30" = 90 Min)
def parse_time_str(time_str):
    if pd.isna(time_str) or time_str == '--' or time_str == '':
        return 0
    time_str = str(time_str).strip()
    # Format: "H:MM" oder "HH:MM"
    parts = time_str.split(':')
    if len(parts) == 2:
        try:
            hours = int(parts[0])
            minutes = int(parts[1])
            return hours * 60 + minutes
        except:
            return 0
    return 0

# Parse Prozent-String (z.B. "75,0%" = 75.0)
def parse_pct_str(pct_str):
    if pd.isna(pct_str) or pct_str == '--' or pct_str == '':
        return 0
    pct_str = str(pct_str).strip()
    # Entferne Anführungszeichen und Leerzeichen
    pct_str = pct_str.replace('"', '').replace("'", '').strip()
    # Entferne % und ersetze Komma durch Punkt
    pct_str = pct_str.replace('%', '').replace(',', '.')
    try:
        return float(pct_str)
    except:
        return 0

# Parse Zeit-Strings
df['dauer_min_parsed'] = df['dauer_min_str'].apply(parse_time_str)
df['aw_ant_min_parsed'] = df['aw_ant_min_str'].apply(parse_time_str)
df['st_ant_pct_parsed'] = df['st_ant_pct_str'].apply(parse_pct_str)

# Berechne St-Anteil in Minuten aus Prozent
df['st_ant_min_calc'] = df['dauer_min'] * (df['st_ant_pct'] / 100)

# Prüfe: Gibt es eine direkte St-Anteil-Minuten-Spalte?
print('='*80)
print('ZEIT-STRING-ANALYSE')
print('='*80)
print()

# Vergleiche dauer_min mit dauer_min_parsed
print('Dauer-Vergleich:')
print(f'  dauer_min (numerisch): {df["dauer_min"].sum():.0f} Min')
print(f'  dauer_min_parsed (aus String): {df["dauer_min_parsed"].sum():.0f} Min')
print(f'  Differenz: {abs(df["dauer_min"].sum() - df["dauer_min_parsed"].sum()):.0f} Min')
print()

# Vergleiche aw_ant_min mit aw_ant_min_parsed
print('AW-Anteil-Vergleich:')
print(f'  aw_ant_min (numerisch): {df["aw_ant_min"].sum():.0f} Min')
print(f'  aw_ant_min_parsed (aus String): {df["aw_ant_min_parsed"].sum():.0f} Min')
print(f'  Differenz: {abs(df["aw_ant_min"].sum() - df["aw_ant_min_parsed"].sum()):.0f} Min')
print()

# Prüfe: Gibt es eine Spalte mit St-Anteil in Minuten direkt?
# Suche nach Spalten, die "St-Anteil" oder "Stmp" enthalten könnten
print('St-Anteil-Analyse:')
print(f'  st_ant_pct (numerisch): Durchschnitt {df["st_ant_pct"].mean():.1f}%')
print(f'  st_ant_pct_parsed (aus String): Durchschnitt {df["st_ant_pct_parsed"].mean():.1f}%')
print(f'  st_ant_min_calc (Dauer × %): {df["st_ant_min_calc"].sum():.0f} Min')
print()

# Prüfe: Gibt es eine Beziehung zwischen aw_ant_min und st_ant_min?
# St-Anteil = AW-Anteil / Leistungsgrad?
if 'lstgrad' in df.columns:
    # Parse lstgrad (kann Zeit-String oder Prozent sein)
    df['lstgrad_parsed'] = df['lstgrad'].apply(parse_time_str)
    df['lstgrad_pct'] = pd.to_numeric(df['lstgrad'], errors='coerce')
    
    print('Leistungsgrad-Analyse:')
    print(f'  lstgrad (Zeit-String): {df["lstgrad_parsed"].sum():.0f} Min')
    print(f'  lstgrad (numerisch): {df["lstgrad_pct"].sum():.0f}')
    print()

# Teste: St-Anteil = AW-Anteil / (Leistungsgrad / 100)?
# Aber wir brauchen Leistungsgrad in Prozent, nicht als Zeit
# Leistungsgrad = (AW-Anteil / St-Anteil) × 100
# Also: St-Anteil = AW-Anteil / (Leistungsgrad / 100)

# Prüfe: Gibt es eine Spalte, die direkt St-Anteil in Minuten zeigt?
# Suche nach Spalten mit "Anwes." oder "Produkt." - vielleicht ist dort St-Anteil?
print('Weitere Spalten-Analyse:')
if 'Anwes.' in df.columns:
    df['anwes_parsed'] = df['Anwes.'].apply(parse_time_str)
    print(f'  Anwes. (Zeit-String): {df["anwes_parsed"].sum():.0f} Min')
if 'Produkt.' in df.columns:
    df['produkt_parsed'] = df['Produkt.'].apply(parse_time_str)
    print(f'  Produkt. (Zeit-String): {df["produkt_parsed"].sum():.0f} Min')
print()

# FINALE FORMEL-TESTE
print('='*80)
print('FORMEL-TESTS')
print('='*80)
print()

# Teste: St-Anteil = Dauer × (AuAW / Gesamt-AuAW pro Stempelung)
df_valid = df[df['dauer_min'] > 0].copy()
df_valid['gesamt_auaw'] = df_valid.groupby(['von', 'bis'])['auaw_min'].transform('sum')

df_valid_mit_aw = df_valid[df_valid['auaw_min'] > 0].copy()
df_valid_mit_aw['st_ant_formel'] = df_valid_mit_aw['dauer_min'] * (df_valid_mit_aw['auaw_min'] / df_valid_mit_aw['gesamt_auaw'])

st_ant_formel_sum = df_valid_mit_aw['st_ant_formel'].sum()
st_ant_csv_sum = df_valid['st_ant_min_calc'].sum()

print(f'1. Formel: St-Anteil = Dauer × (AuAW / Gesamt-AuAW)')
print(f'   Summe: {st_ant_formel_sum:.0f} Min')
print(f'   CSV Summe: {st_ant_csv_sum:.0f} Min')
print(f'   Differenz: {abs(st_ant_formel_sum - st_ant_csv_sum):.0f} Min ({abs(st_ant_formel_sum - st_ant_csv_sum)/st_ant_csv_sum*100:.1f}%)')
print()

# Teste: St-Anteil = AW-Anteil / (Leistungsgrad / 100)
# Aber wir haben Leistungsgrad nicht direkt - wir können ihn berechnen
# Leistungsgrad = (AW-Anteil / St-Anteil) × 100
# Also: St-Anteil = AW-Anteil / (Leistungsgrad / 100)

# Prüfe: Gibt es eine direkte Beziehung?
# Vielleicht ist "Anwes." oder "Produkt." der St-Anteil?
if 'Anwes.' in df.columns:
    st_ant_anwes = df_valid['anwes_parsed'].sum()
    print(f'2. St-Anteil = Anwes. (Zeit-String)')
    print(f'   Summe: {st_ant_anwes:.0f} Min')
    print(f'   CSV Summe: {st_ant_csv_sum:.0f} Min')
    print(f'   Differenz: {abs(st_ant_anwes - st_ant_csv_sum):.0f} Min ({abs(st_ant_anwes - st_ant_csv_sum)/st_ant_csv_sum*100:.1f}%)')
    print()
