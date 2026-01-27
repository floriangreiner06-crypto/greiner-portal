#!/usr/bin/env python3
"""
Analysiert Locosoft Zeit-Daten aus Excel/CSV-Dateien
Vergleicht mit unseren Berechnungen und Locosoft-Werten
"""

import pandas as pd
import sys
from pathlib import Path
from typing import Dict, List, Any
import re
from datetime import datetime

def parse_zeit(zeit_str: str) -> float:
    """Konvertiert Zeit-String (z.B. '1:06' oder '1:06:00') in Stunden"""
    if pd.isna(zeit_str) or str(zeit_str).strip() == '':
        return 0.0
    
    try:
        parts = str(zeit_str).strip().split(':')
        if len(parts) == 2:
            return int(parts[0]) + int(parts[1]) / 60.0
        elif len(parts) == 3:
            return int(parts[0]) + int(parts[1]) / 60.0 + int(parts[2]) / 3600.0
        else:
            return float(zeit_str)
    except:
        return 0.0


def read_locosoft_csv(file_path: str) -> pd.DataFrame:
    """Liest Locosoft CSV-Datei"""
    encodings = ['latin-1', 'iso-8859-1', 'cp1252', 'windows-1252', 'utf-8']
    separators = [';', '\t', ',']
    
    for enc in encodings:
        for sep in separators:
            try:
                # Suche Header-Zeile
                with open(file_path, 'r', encoding=enc, errors='ignore') as f:
                    lines = f.readlines()
                    header_row = None
                    for i, line in enumerate(lines[:20]):
                        if 'von' in line.lower() and 'bis' in line.lower() and 'auftrag' in line.lower():
                            header_row = i
                            break
                    
                    if header_row is None:
                        header_row = 4  # Fallback
                
                df = pd.read_csv(
                    file_path,
                    encoding=enc,
                    sep=sep,
                    skiprows=header_row,
                    skipinitialspace=True,
                    on_bad_lines='skip',
                    low_memory=False
                )
                
                # Bereinige Spaltennamen
                df.columns = df.columns.str.strip()
                
                return df
            except Exception as e:
                continue
    
    raise ValueError(f"Konnte Datei nicht lesen: {file_path}")


def analyse_ma_5007_07_01_26():
    """Analysiert MA 5007 am 07.01.26 aus Locosoft-Daten"""
    
    file_path = '/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/locosoft_zeit/Stempelzeiten-Übersicht 07.01.26.csv'
    
    if not Path(file_path).exists():
        print(f"❌ Datei nicht gefunden: {file_path}")
        return
    
    print(f"\n{'='*100}")
    print("ANALYSE: MA 5007 (Reitmeier) - 07.01.2026")
    print(f"{'='*100}\n")
    
    df = read_locosoft_csv(file_path)
    print(f"✓ Gelesen: {len(df)} Zeilen, {len(df.columns)} Spalten")
    print(f"Spalten: {list(df.columns)}\n")
    
    # Filtere MA 5007
    if 'MA' not in df.columns:
        print("❌ Spalte 'MA' nicht gefunden!")
        return
    
    df_5007 = df[df['MA'].astype(str) == '5007'].copy()
    print(f"✓ MA 5007: {len(df_5007)} Zeilen\n")
    
    if len(df_5007) == 0:
        print("❌ Keine Daten für MA 5007 gefunden!")
        return
    
    # Zeige alle Spalten
    print("Verfügbare Spalten:")
    for col in df_5007.columns:
        print(f"  - {col}")
    print()
    
    # Analysiere St-Anteil nach Betrieb
    if 'Auftrag' in df_5007.columns:
        # Gruppiere nach Auftrag
        print("Stempelungen nach Auftrag:")
        print("-" * 100)
        
        for auftrag in df_5007['Auftrag'].unique():
            df_auftrag = df_5007[df_5007['Auftrag'] == auftrag]
            
            dauer_sum = df_auftrag['Dauer'].apply(parse_zeit).sum() if 'Dauer' in df_auftrag.columns else 0
            st_anteil_sum = df_auftrag['St-Ant.'].apply(parse_zeit).sum() if 'St-Ant.' in df_auftrag.columns else 0
            aw_anteil_sum = df_auftrag['AW-Ant.'].apply(parse_zeit).sum() if 'AW-Ant.' in df_auftrag.columns else 0
            
            print(f"Auftrag {auftrag}: {len(df_auftrag)} Positionen")
            print(f"  Dauer (Summe): {dauer_sum:.2f} Std")
            print(f"  St-Anteil (Summe): {st_anteil_sum:.2f} Std")
            print(f"  AW-Anteil (Summe): {aw_anteil_sum:.2f} Std")
            print()
    
    # Gesamt-Summen
    print("=" * 100)
    print("GESAMT-SUMMEN (MA 5007, 07.01.2026):")
    print("=" * 100)
    
    if 'St-Ant.' in df_5007.columns:
        st_anteil_gesamt = df_5007['St-Ant.'].apply(parse_zeit).sum()
        print(f"St-Anteil (Gesamt): {st_anteil_gesamt:.2f} Std")
    
    if 'AW-Ant.' in df_5007.columns:
        aw_anteil_gesamt = df_5007['AW-Ant.'].apply(parse_zeit).sum()
        print(f"AW-Anteil (Gesamt): {aw_anteil_gesamt:.2f} Std")
    
    if 'Anwes.' in df_5007.columns:
        anwes_gesamt = df_5007['Anwes.'].apply(parse_zeit).sum()
        print(f"Anwesenheit (Gesamt): {anwes_gesamt:.2f} Std")
    
    print()
    
    # Vergleich mit Locosoft-Werten
    print("=" * 100)
    print("VERGLEICH MIT LOCOSOFT-WERTEN:")
    print("=" * 100)
    print("Locosoft (aus Screenshot):")
    print("  DEGO: 9:06 Std (9.10 Std)")
    print("  DEGH: 3:59 Std (3.98 Std)")
    print("  GESAMT: 13:05 Std (13.08 Std)")
    print()
    
    if 'St-Ant.' in df_5007.columns:
        st_anteil_gesamt = df_5007['St-Ant.'].apply(parse_zeit).sum()
        print(f"Unsere Berechnung (Summe aller St-Ant.): {st_anteil_gesamt:.2f} Std")
        print(f"Abweichung: {st_anteil_gesamt - 13.08:.2f} Std")
    
    print()
    
    # Zeige alle Zeilen
    print("=" * 100)
    print("ALLE STEMPELUNGEN (MA 5007, 07.01.2026):")
    print("=" * 100)
    
    cols_to_show = ['MA', 'Auftrag', 'von', 'bis', 'Dauer', 'St-Ant.', 'AW-Ant.']
    available_cols = [c for c in cols_to_show if c in df_5007.columns]
    
    print(df_5007[available_cols].to_string())
    print()


def main():
    """Hauptfunktion"""
    print("=" * 100)
    print("LOCOSOFT ZEIT-DATEN ANALYSE")
    print("=" * 100)
    
    # Analysiere MA 5007 am 07.01.26
    analyse_ma_5007_07_01_26()


if __name__ == '__main__':
    main()
