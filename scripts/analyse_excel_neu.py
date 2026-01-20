#!/usr/bin/env python3
"""
NEUE ANALYSE: Excel-Daten komplett neu analysieren
Keine vorgefertigten Annahmen - nur die Daten sprechen lassen
"""

import pandas as pd
import sys
from pathlib import Path
from typing import Dict, List, Any
import re

def parse_zeit(zeit_str: str) -> float:
    """Konvertiert Zeit-String (z.B. '1:06' oder '1:06:00') in Minuten"""
    if pd.isna(zeit_str) or str(zeit_str).strip() == '':
        return 0.0
    
    try:
        parts = str(zeit_str).strip().split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60.0
        else:
            return float(zeit_str)
    except:
        return 0.0


def find_excel_files(base_path: str) -> List[str]:
    """Findet alle Excel/CSV-Dateien im Verzeichnis"""
    files = []
    base = Path(base_path)
    
    if not base.exists():
        return files
    
    # Suche CSV
    for f in base.glob("*.csv"):
        files.append(str(f))
    
    # Suche Excel
    for f in base.glob("*.xlsx"):
        files.append(str(f))
    for f in base.glob("*.xls"):
        files.append(str(f))
    
    return sorted(files, reverse=True)  # Neueste zuerst


def read_excel_file(file_path: str) -> pd.DataFrame:
    """Liest Excel/CSV-Datei mit verschiedenen Encodings"""
    encodings = ['latin-1', 'iso-8859-1', 'cp1252', 'windows-1252', 'utf-8']
    separators = ['\t', ';', ',']
    
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


def analyse_st_anteil_logik(df: pd.DataFrame, mechaniker_nr: int = None):
    """Analysiert die St-Anteil-Berechnung aus Excel-Daten"""
    
    print(f"\n{'='*100}")
    print("ANALYSE: St-Anteil-Berechnung")
    print(f"{'='*100}\n")
    
    # Finde relevante Spalten
    cols = df.columns.tolist()
    print(f"Spalten: {cols}\n")
    
    # Finde Spalten
    ma_col = None
    auftrag_col = None
    pos_col = None
    dauer_col = None
    st_anteil_col = None
    aw_anteil_col = None
    auaw_col = None
    
    for col in cols:
        col_lower = col.lower()
        if col_lower in ['ma', 'mitarbeiter', 'employee']:
            ma_col = col
        elif 'auftrag' in col_lower and 'pos' not in col_lower:
            auftrag_col = col
        elif 'pos' in col_lower and ('art' in col_lower or 'text' in col_lower):
            pos_col = col
        elif 'dauer' in col_lower:
            dauer_col = col
        elif 'st-ant' in col_lower or 'stempelanteil' in col_lower:
            st_anteil_col = col
        elif 'aw-ant' in col_lower or 'aw-anteil' in col_lower:
            aw_anteil_col = col
        elif 'auaw' in col_lower or 'auftrags-aw' in col_lower:
            auaw_col = col
    
    print(f"Gefundene Spalten:")
    print(f"  MA: {ma_col}")
    print(f"  Auftrag: {auftrag_col}")
    print(f"  Position: {pos_col}")
    print(f"  Dauer: {dauer_col}")
    print(f"  St-Anteil: {st_anteil_col}")
    print(f"  AW-Anteil: {aw_anteil_col}")
    print(f"  AuAW: {auaw_col}\n")
    
    if not all([ma_col, auftrag_col, dauer_col, st_anteil_col]):
        print("❌ Wichtige Spalten fehlen!")
        return
    
    # Filtere nur Zeilen mit Daten
    df_clean = df.dropna(subset=[ma_col, auftrag_col])
    df_clean = df_clean[df_clean[auftrag_col].astype(str).str.isdigit()]
    
    if mechaniker_nr:
        df_clean = df_clean[df_clean[ma_col].astype(str) == str(mechaniker_nr)]
    
    print(f"Zeilen mit Daten: {len(df_clean)}\n")
    
    # Analysiere Beispiele
    print("BEISPIEL-ANALYSEN:\n")
    print("-" * 100)
    
    # Gruppiere nach Auftrag/Zeit
    if 'von' in cols and 'bis' in cols:
        group_cols = [ma_col, auftrag_col, 'von', 'bis']
    else:
        group_cols = [ma_col, auftrag_col]
    
    for idx, row in df_clean.head(20).iterrows():
        ma = row[ma_col]
        auftrag = row[auftrag_col]
        dauer = parse_zeit(row.get(dauer_col, 0))
        st_anteil = parse_zeit(row.get(st_anteil_col, 0))
        aw_anteil = parse_zeit(row.get(aw_anteil_col, 0))
        auaw = parse_zeit(row.get(auaw_col, 0))
        pos = row.get(pos_col, '')
        
        if dauer > 0 and st_anteil > 0:
            verhaeltnis = st_anteil / dauer
            print(f"MA {ma}, Auftrag {auftrag}, Pos {pos}")
            print(f"  Dauer: {dauer:.1f} Min, St-Anteil: {st_anteil:.1f} Min, Verhältnis: {verhaeltnis:.3f}")
            if auaw > 0:
                print(f"  AuAW: {auaw:.1f} Min, AW-Anteil: {aw_anteil:.1f} Min")
            print()
    
    # Analysiere: Wenn mehrere Positionen gleiche Zeit haben
    print("\n" + "="*100)
    print("ANALYSE: Mehrere Positionen mit gleicher Zeit")
    print("="*100 + "\n")
    
    if 'von' in cols and 'bis' in cols:
        # Gruppiere nach Mechaniker, Auftrag, von, bis
        grouped = df_clean.groupby([ma_col, auftrag_col, 'von', 'bis'])
    else:
        grouped = df_clean.groupby([ma_col, auftrag_col])
    
    for (ma, auftrag, *rest), group in list(grouped)[:10]:
        if len(group) > 1:
            dauer = parse_zeit(group.iloc[0].get(dauer_col, 0))
            st_anteil_sum = group[st_anteil_col].apply(parse_zeit).sum()
            aw_anteil_sum = group[aw_anteil_col].apply(parse_zeit).sum() if aw_anteil_col else 0
            auaw_sum = group[auaw_col].apply(parse_zeit).sum() if auaw_col else 0
            
            print(f"MA {ma}, Auftrag {auftrag}, {len(group)} Positionen, Dauer: {dauer:.1f} Min")
            print(f"  St-Anteil Summe: {st_anteil_sum:.1f} Min")
            print(f"  AW-Anteil Summe: {aw_anteil_sum:.1f} Min")
            print(f"  AuAW Summe: {auaw_sum:.1f} Min")
            if dauer > 0:
                print(f"  Verhältnis St-Anteil/Dauer: {st_anteil_sum/dauer:.3f}")
            print()


def main():
    # Suche Excel-Dateien
    search_paths = [
        '/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/locosoft_zeit',
        '/mnt/greiner-portal-sync/locosoft_zeit',
        '/opt/greiner-portal/data/locosoft_zeit',
    ]
    
    files = []
    for path in search_paths:
        found = find_excel_files(path)
        files.extend(found)
        if found:
            print(f"✓ Gefunden in {path}: {len(found)} Dateien")
    
    if not files:
        print("❌ Keine Excel/CSV-Dateien gefunden!")
        print(f"Gesucht in: {search_paths}")
        return
    
    print(f"\n{'='*100}")
    print(f"GEFUNDENE DATEIEN: {len(files)}")
    print(f"{'='*100}\n")
    
    # Analysiere alle Dateien
    for file_path in files[:5]:  # Erste 5 Dateien
        try:
            print(f"\n{'#'*100}")
            print(f"ANALYSIERE: {Path(file_path).name}")
            print(f"{'#'*100}\n")
            
            df = read_excel_file(file_path)
            print(f"✓ Gelesen: {len(df)} Zeilen, {len(df.columns)} Spalten\n")
            
            # Analysiere für verschiedene Mechaniker
            if 'MA' in df.columns or any('ma' in str(c).lower() for c in df.columns):
                analyse_st_anteil_logik(df, mechaniker_nr=5007)
                analyse_st_anteil_logik(df, mechaniker_nr=5018)
            
        except Exception as e:
            print(f"❌ Fehler bei {file_path}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
