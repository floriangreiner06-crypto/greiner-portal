#!/usr/bin/env python3
"""
Analysiert Locosoft Zeit-Daten aus Excel/CSV-Dateien
Vergleicht mit unseren Berechnungen und Locosoft-Werten
"""

import pandas as pd
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
from datetime import datetime

def parse_zeit(zeit_str: str) -> float:
    """Konvertiert Zeit-String (z.B. '1:06' oder '1:06:00') in Stunden"""
    if pd.isna(zeit_str) or str(zeit_str).strip() == '' or str(zeit_str).strip() == 'nan':
        return 0.0
    
    try:
        zeit_str = str(zeit_str).strip()
        # Entferne '>' oder andere Präfixe
        if zeit_str.startswith('>'):
            return 0.0
        
        parts = zeit_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) + int(parts[1]) / 60.0
        elif len(parts) == 3:
            return int(parts[0]) + int(parts[1]) / 60.0 + int(parts[2]) / 3600.0
        else:
            return float(zeit_str)
    except:
        return 0.0


def read_locosoft_csv_verbessert(file_path: str) -> pd.DataFrame:
    """Liest Locosoft CSV-Datei mit verbessertem Parsing"""
    
    with open(file_path, 'r', encoding='latin-1') as f:
        lines = f.readlines()
    
    # Finde Header-Zeile
    header_row = None
    for i, line in enumerate(lines):
        if 'MA' in line and 'von' in line and 'bis' in line:
            header_row = i
            break
    
    if header_row is None:
        raise ValueError("Header-Zeile nicht gefunden!")
    
    # Lese CSV ab Header
    df = pd.read_csv(
        file_path,
        encoding='latin-1',
        sep='\t',
        skiprows=header_row,
        skipinitialspace=True,
        on_bad_lines='skip',
        low_memory=False
    )
    
    # Bereinige Spaltennamen
    df.columns = [c.strip() for c in df.columns]
    
    return df


def extrahiere_ma_daten(df: pd.DataFrame, ma_nr: int) -> pd.DataFrame:
    """Extrahiert alle Daten für einen bestimmten Mitarbeiter"""
    
    # Finde MA-Spalte
    ma_col = None
    for col in df.columns:
        if 'MA' in col and 'Border' not in col:
            ma_col = col
            break
    
    if ma_col is None:
        ma_col = df.columns[0]
    
    # Finde Start-Zeile für MA
    start_idx = None
    for idx, row in df.iterrows():
        val = str(row[ma_col]).strip()
        if val == str(ma_nr) or str(ma_nr) in val:
            start_idx = idx
            break
    
    if start_idx is None:
        return pd.DataFrame()
    
    # Finde End-Zeile (nächste MA-Nummer oder Ende)
    end_idx = len(df)
    for idx in range(start_idx + 1, len(df)):
        val = str(df.iloc[idx][ma_col]).strip()
        if val and val.isdigit() and val != str(ma_nr):
            end_idx = idx
            break
    
    return df.iloc[start_idx:end_idx].copy()


def analysiere_ma_5007_07_01_26():
    """Analysiert MA 5007 am 07.01.26 aus Locosoft-Daten"""
    
    file_path = '/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/locosoft_zeit/Stempelzeiten-Übersicht 07.01.26.csv'
    
    if not Path(file_path).exists():
        print(f"❌ Datei nicht gefunden: {file_path}")
        return
    
    print(f"\n{'='*100}")
    print("ANALYSE: MA 5007 (Reitmeier) - 07.01.2026")
    print(f"{'='*100}\n")
    
    df = read_locosoft_csv_verbessert(file_path)
    print(f"✓ Gelesen: {len(df)} Zeilen, {len(df.columns)} Spalten")
    print(f"Spalten: {list(df.columns)}\n")
    
    # Extrahiere MA 5007 Daten
    df_5007 = extrahiere_ma_daten(df, 5007)
    print(f"✓ MA 5007: {len(df_5007)} Zeilen\n")
    
    if len(df_5007) == 0:
        print("❌ Keine Daten für MA 5007 gefunden!")
        return
    
    # Finde relevante Spalten
    von_col = None
    bis_col = None
    dauer_col = None
    auftrag_col = None
    st_anteil_col = None
    aw_anteil_col = None
    anwes_col = None
    
    for col in df_5007.columns:
        col_lower = col.lower()
        if 'von' in col_lower and not von_col:
            von_col = col
        elif 'bis' in col_lower and not bis_col:
            bis_col = col
        elif 'dauer' in col_lower and not dauer_col:
            dauer_col = col
        elif 'auftrag' in col_lower and 'pos' not in col_lower and not auftrag_col:
            auftrag_col = col
        elif 'st-ant' in col_lower and not st_anteil_col:
            st_anteil_col = col
        elif 'aw-ant' in col_lower and not aw_anteil_col:
            aw_anteil_col = col
        elif 'anwes' in col_lower and not anwes_col:
            anwes_col = col
    
    print("Gefundene Spalten:")
    print(f"  von: {von_col}")
    print(f"  bis: {bis_col}")
    print(f"  Dauer: {dauer_col}")
    print(f"  Auftrag: {auftrag_col}")
    print(f"  St-Anteil: {st_anteil_col}")
    print(f"  AW-Anteil: {aw_anteil_col}")
    print(f"  Anwesenheit: {anwes_col}")
    print()
    
    # Erstelle strukturierte Daten
    stempelungen = []
    
    for idx, row in df_5007.iterrows():
        # Erste Zeile: MA-Info
        if idx == df_5007.index[0]:
            continue
        
        # Extrahiere Daten
        von = str(row.get(von_col, '')).strip() if von_col else ''
        bis = str(row.get(bis_col, '')).strip() if bis_col else ''
        dauer = parse_zeit(row.get(dauer_col, 0)) if dauer_col else 0
        auftrag = str(row.get(auftrag_col, '')).strip() if auftrag_col else ''
        st_anteil = parse_zeit(row.get(st_anteil_col, 0)) if st_anteil_col else 0
        aw_anteil = parse_zeit(row.get(aw_anteil_col, 0)) if aw_anteil_col else 0
        anwes = parse_zeit(row.get(anwes_col, 0)) if anwes_col else 0
        
        # Überspringe leere Zeilen
        if not von and not bis and dauer == 0:
            continue
        
        stempelungen.append({
            'von': von,
            'bis': bis,
            'dauer': dauer,
            'auftrag': auftrag,
            'st_anteil': st_anteil,
            'aw_anteil': aw_anteil,
            'anwes': anwes
        })
    
    print(f"✓ {len(stempelungen)} Stempelungen gefunden\n")
    
    # Zeige alle Stempelungen
    print("=" * 100)
    print("ALLE STEMPELUNGEN (MA 5007, 07.01.2026):")
    print("=" * 100)
    print(f"{'von':<10} {'bis':<10} {'Dauer':<10} {'Auftrag':<10} {'St-Ant.':<10} {'AW-Ant.':<10}")
    print("-" * 100)
    
    for s in stempelungen:
        print(f"{s['von']:<10} {s['bis']:<10} {s['dauer']:<10.2f} {s['auftrag']:<10} {s['st_anteil']:<10.2f} {s['aw_anteil']:<10.2f}")
    
    print()
    
    # Gesamt-Summen
    print("=" * 100)
    print("GESAMT-SUMMEN (MA 5007, 07.01.2026):")
    print("=" * 100)
    
    dauer_gesamt = sum(s['dauer'] for s in stempelungen)
    st_anteil_gesamt = sum(s['st_anteil'] for s in stempelungen)
    aw_anteil_gesamt = sum(s['aw_anteil'] for s in stempelungen)
    anwes_gesamt = sum(s['anwes'] for s in stempelungen)
    
    print(f"Dauer (Gesamt): {dauer_gesamt:.2f} Std")
    print(f"St-Anteil (Gesamt): {st_anteil_gesamt:.2f} Std")
    print(f"AW-Anteil (Gesamt): {aw_anteil_gesamt:.2f} Std")
    print(f"Anwesenheit (Gesamt): {anwes_gesamt:.2f} Std")
    print()
    
    # Vergleich mit Locosoft-Werten
    print("=" * 100)
    print("VERGLEICH MIT LOCOSOFT-WERTEN (aus Screenshot):")
    print("=" * 100)
    print("Locosoft:")
    print("  DEGO: 9:06 Std (9.10 Std)")
    print("  DEGH: 3:59 Std (3.98 Std)")
    print("  GESAMT: 13:05 Std (13.08 Std)")
    print()
    print(f"Unsere Berechnung (Summe aller St-Ant.): {st_anteil_gesamt:.2f} Std")
    print(f"Abweichung: {st_anteil_gesamt - 13.08:.2f} Std ({((st_anteil_gesamt - 13.08) / 13.08 * 100):.1f}%)")
    print()
    
    # Gruppiere nach Auftrag
    print("=" * 100)
    print("STEMPELUNGEN NACH AUFTRAG:")
    print("=" * 100)
    
    auftraege = {}
    for s in stempelungen:
        auftrag = s['auftrag']
        if auftrag and auftrag.isdigit():
            if auftrag not in auftraege:
                auftraege[auftrag] = {'dauer': 0, 'st_anteil': 0, 'aw_anteil': 0, 'anzahl': 0}
            auftraege[auftrag]['dauer'] += s['dauer']
            auftraege[auftrag]['st_anteil'] += s['st_anteil']
            auftraege[auftrag]['aw_anteil'] += s['aw_anteil']
            auftraege[auftrag]['anzahl'] += 1
    
    for auftrag, data in sorted(auftraege.items()):
        print(f"Auftrag {auftrag}: {data['anzahl']} Stempelungen")
        print(f"  Dauer: {data['dauer']:.2f} Std")
        print(f"  St-Anteil: {data['st_anteil']:.2f} Std")
        print(f"  AW-Anteil: {data['aw_anteil']:.2f} Std")
        print()


def main():
    """Hauptfunktion"""
    print("=" * 100)
    print("LOCOSOFT ZEIT-DATEN ANALYSE (VERBESSERT)")
    print("=" * 100)
    
    # Analysiere MA 5007 am 07.01.26
    analysiere_ma_5007_07_01_26()


if __name__ == '__main__':
    main()
