#!/usr/bin/env python3
"""
Analysiert Locosoft Stempelzeiten-Übersicht Excel-Dateien
um die Berechnung von Stempelanteil und AW-Anteil zu verstehen.

Datum: 2026-01-16 (TAG 194)
"""

import pandas as pd
import sys
from pathlib import Path

def analyse_stempelzeiten_excel(file_path):
    """Analysiert eine Locosoft Stempelzeiten-Übersicht Excel-Datei"""
    
    print(f"Analysiere Datei: {file_path}")
    print("=" * 80)
    
    # Versuche verschiedene Encodings und Separatoren
    encodings = ['latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']
    separators = ['\t', ';', ',']
    
    df = None
    for enc in encodings:
        for sep in separators:
            try:
                # Lese CSV mit verschiedenen Optionen
                # Suche nach der Header-Zeile (enthält "von", "bis", "Auftrag", etc.)
                with open(file_path, 'r', encoding=enc) as f:
                    lines = f.readlines()
                    header_row = None
                    for i, line in enumerate(lines):
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
                    on_bad_lines='skip'
                )
                print(f"✓ Erfolgreich gelesen mit Encoding: {enc}, Separator: '{sep}', Header-Zeile: {header_row}")
                break
            except Exception as e:
                continue
        if df is not None:
            break
    
    if df is None:
        print("❌ Konnte Datei nicht lesen")
        return
    
    print(f"\nSpalten: {list(df.columns)}")
    print(f"Zeilen: {len(df)}")
    
    # Bereinige Spaltennamen
    df.columns = df.columns.str.strip()
    
    # Zeige erste Zeilen
    print("\n" + "=" * 80)
    print("ERSTE 10 ZEILEN:")
    print("=" * 80)
    print(df.head(10).to_string())
    
    # Analysiere wichtige Spalten
    print("\n" + "=" * 80)
    print("ANALYSE:")
    print("=" * 80)
    
    # Finde relevante Spalten
    aw_anteil_col = None
    st_anteil_col = None
    leistungsgrad_col = None
    auftrag_col = None
    pos_col = None
    ma_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'aw-ant' in col_lower or 'aw-anteil' in col_lower:
            aw_anteil_col = col
        elif 'st-ant' in col_lower or 'stempelanteil' in col_lower or 'st-anteil' in col_lower:
            st_anteil_col = col
        elif 'lstgrad' in col_lower or 'leistungsgrad' in col_lower or '%lstgrad' in col_lower:
            leistungsgrad_col = col
        elif 'auftrag' in col_lower and 'pos' not in col_lower:
            auftrag_col = col
        elif 'pos' in col_lower and 'art' in col_lower:
            pos_col = col
        elif col_lower in ['ma', 'mitarbeiter', 'employee']:
            ma_col = col
    
    print(f"AW-Anteil Spalte: {aw_anteil_col}")
    print(f"St-Anteil Spalte: {st_anteil_col}")
    print(f"Leistungsgrad Spalte: {leistungsgrad_col}")
    print(f"Auftrag Spalte: {auftrag_col}")
    print(f"Position Spalte: {pos_col}")
    print(f"MA Spalte: {ma_col}")
    
    # Filtere nur Zeilen mit Daten (nicht leer)
    if auftrag_col and ma_col:
        df_filtered = df[
            (df[auftrag_col].notna()) & 
            (df[auftrag_col] != '') &
            (df[ma_col].notna()) &
            (df[ma_col] != '')
        ].copy()
        
        print(f"\nGefilterte Zeilen (mit Auftrag und MA): {len(df_filtered)}")
        
        # Zeige Beispiele
        if len(df_filtered) > 0:
            print("\n" + "=" * 80)
            print("BEISPIELE (erste 20 Zeilen mit Daten):")
            print("=" * 80)
            
            relevant_cols = [ma_col, auftrag_col]
            if pos_col:
                relevant_cols.append(pos_col)
            if aw_anteil_col:
                relevant_cols.append(aw_anteil_col)
            if st_anteil_col:
                relevant_cols.append(st_anteil_col)
            if leistungsgrad_col:
                relevant_cols.append(leistungsgrad_col)
            
            print(df_filtered[relevant_cols].head(20).to_string())
            
            # Analysiere spezifische Mechaniker
            print("\n" + "=" * 80)
            print("ANALYSE FÜR MECHANIKER 5018 (Jan Majer):")
            print("=" * 80)
            
            if ma_col:
                jan_data = df_filtered[df_filtered[ma_col].astype(str).str.contains('5018|Majer', na=False)]
                if len(jan_data) > 0:
                    print(f"Gefundene Zeilen: {len(jan_data)}")
                    print(jan_data[relevant_cols].head(10).to_string())
                    
                    # Summiere AW-Anteil und St-Anteil
                    if aw_anteil_col and st_anteil_col:
                        print("\n" + "=" * 80)
                        print("SUMMEN FÜR MECHANIKER 5018:")
                        print("=" * 80)
                        
                        # Konvertiere Zeit-Strings zu Minuten
                        def time_to_minutes(time_str):
                            if pd.isna(time_str) or time_str == '' or str(time_str).strip() == '--' or str(time_str).strip() == 'NaN':
                                return 0
                            try:
                                time_str = str(time_str).strip()
                                if ':' in time_str:
                                    parts = time_str.split(':')
                                    if len(parts) == 2:
                                        return int(parts[0]) * 60 + int(parts[1])
                                    elif len(parts) == 3:  # Stunden:Minuten:Sekunden
                                        return int(parts[0]) * 60 + int(parts[1])
                                # Versuche als Float (Stunden)
                                return float(time_str) * 60
                            except Exception as e:
                                return 0
                        
                        jan_data = jan_data.copy()  # Fix für SettingWithCopyWarning
                        jan_data['aw_anteil_min'] = jan_data[aw_anteil_col].apply(time_to_minutes)
                        jan_data['st_anteil_min'] = jan_data[st_anteil_col].apply(time_to_minutes)
                        
                        total_aw_anteil = jan_data['aw_anteil_min'].sum()
                        total_st_anteil = jan_data['st_anteil_min'].sum()
                        
                        print(f"Gesamt AW-Anteil: {total_aw_anteil} Min = {total_aw_anteil/60:.2f} Stunden")
                        print(f"Gesamt St-Anteil: {total_st_anteil} Min = {total_st_anteil/60:.2f} Stunden")
                        
                        if total_st_anteil > 0:
                            leistungsgrad = (total_aw_anteil / total_st_anteil) * 100
                            print(f"Berechneter Leistungsgrad: {leistungsgrad:.1f}%")
    
    # Speichere Analyse
    output_file = '/tmp/stempelzeiten_analyse.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Analyse von: {file_path}\n")
        f.write("=" * 80 + "\n")
        f.write(f"Spalten: {list(df.columns)}\n")
        f.write(f"Zeilen: {len(df)}\n")
        f.write("\nErste 50 Zeilen:\n")
        f.write(df.head(50).to_string())
    
    print(f"\n✓ Analyse gespeichert in: {output_file}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Default: Neueste Datei von gestern
        file_path = '/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/locosoft_zeit/Stempelzeiten-Übersicht 01.01.26 - 15.01.26.csv'
    
    analyse_stempelzeiten_excel(file_path)
