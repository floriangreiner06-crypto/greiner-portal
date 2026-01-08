"""
Detaillierte Analyse: Global Cube CSV Version 18
================================================
Analysiert die detaillierte Aufschlüsselung der Global Cube BWA
"""

import csv
import os
import sys

sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session

csv_file_path = '/home/ag-admin/Downloads/F.03 BWA Vorjahres-Vergleich (18).csv'

print("=" * 100)
print("Detaillierte Analyse: Global Cube CSV Version 18")
print("=" * 100)

# Versuche die CSV-Datei zu lesen
try:
    # Versuche verschiedene Encodings
    encodings = ['utf-16', 'utf-8', 'latin-1', 'cp1252']
    csv_data = None
    
    for encoding in encodings:
        try:
            with open(csv_file_path, 'r', encoding=encoding) as file:
                # Versuche verschiedene Delimiter
                for delimiter in ['\t', ',', ';']:
                    file.seek(0)
                    reader = csv.reader(file, delimiter=delimiter)
                    lines = list(reader)
                    if len(lines) > 0 and len(lines[0]) > 5:
                        csv_data = lines
                        print(f"✅ CSV erfolgreich gelesen: Encoding={encoding}, Delimiter='{delimiter}'")
                        break
                if csv_data:
                    break
        except Exception as e:
            continue
    
    if not csv_data:
        print("❌ Konnte CSV-Datei nicht lesen. Versuche alternative Pfade...")
        # Versuche Windows-Pfad
        csv_file_path_win = 'c:\\Users\\florian.greiner\\Downloads\\F.03 BWA Vorjahres-Vergleich (18).csv'
        print(f"   Versuche: {csv_file_path_win}")
        print("   (Datei muss auf Server kopiert werden)")
        sys.exit(1)
    
    print(f"\nCSV hat {len(csv_data)} Zeilen")
    
    # Zeige die ersten 20 Zeilen zur Strukturanalyse
    print("\n" + "=" * 100)
    print("CSV-Struktur (erste 20 Zeilen):")
    print("=" * 100)
    for i, line in enumerate(csv_data[:20]):
        # Zeige nur nicht-leere Spalten
        non_empty = [f"[{j}] '{col.strip()}'" for j, col in enumerate(line) if col.strip()]
        if non_empty:
            print(f"Zeile {i+1}: {', '.join(non_empty[:10])}")  # Erste 10 Spalten
    
    # Suche nach NW und GW Stückzahlen
    print("\n" + "=" * 100)
    print("Suche nach NW und GW Stückzahlen:")
    print("=" * 100)
    
    # Zeile 4 sollte "Neuwagen Stk." sein
    if len(csv_data) > 3:
        nw_line = csv_data[3]  # Index 3 = Zeile 4
        print(f"\nZeile 4 (Neuwagen Stk.):")
        for j, col in enumerate(nw_line):
            if col.strip():
                print(f"  Spalte {j}: '{col.strip()}'")
        
        # Suche nach "Jahr" Spalte (sollte die kumulierten Werte enthalten)
        # Basierend auf vorherigen Analysen sollte Spalte 17 oder ähnlich sein
        print(f"\n  Mögliche Jahreswerte:")
        for j in [15, 16, 17, 18, 19, 20]:
            if j < len(nw_line) and nw_line[j].strip():
                try:
                    # Versuche Zahl zu extrahieren
                    val_str = nw_line[j].strip().replace('.', '').replace(',', '.')
                    val = float(val_str)
                    print(f"    Spalte {j}: {val:.2f}")
                except:
                    print(f"    Spalte {j}: '{nw_line[j].strip()}'")
    
    # Zeile 13 sollte "Gebrauchtwagen Stk." sein
    if len(csv_data) > 12:
        gw_line = csv_data[12]  # Index 12 = Zeile 13
        print(f"\nZeile 13 (Gebrauchtwagen Stk.):")
        for j, col in enumerate(gw_line):
            if col.strip():
                print(f"  Spalte {j}: '{col.strip()}'")
        
        print(f"\n  Mögliche Jahreswerte:")
        for j in [15, 16, 17, 18, 19, 20]:
            if j < len(gw_line) and gw_line[j].strip():
                try:
                    val_str = gw_line[j].strip().replace('.', '').replace(',', '.')
                    val = float(val_str)
                    print(f"    Spalte {j}: {val:.2f}")
                except:
                    print(f"    Spalte {j}: '{gw_line[j].strip()}'")
    
    # Zeile 14 sollte "GW Kunden" sein
    if len(csv_data) > 13:
        gw_kunden_line = csv_data[13]  # Index 13 = Zeile 14
        print(f"\nZeile 14 (GW Kunden):")
        for j, col in enumerate(gw_kunden_line):
            if col.strip():
                print(f"  Spalte {j}: '{col.strip()}'")
        
        print(f"\n  Mögliche Jahreswerte:")
        for j in [15, 16, 17, 18, 19, 20]:
            if j < len(gw_kunden_line) and gw_kunden_line[j].strip():
                try:
                    val_str = gw_kunden_line[j].strip().replace('.', '').replace(',', '.')
                    val = float(val_str)
                    print(f"    Spalte {j}: {val:.2f}")
                except:
                    print(f"    Spalte {j}: '{gw_kunden_line[j].strip()}'")
    
    # Extrahiere die Werte
    print("\n" + "=" * 100)
    print("Extraktion der Global Cube Werte:")
    print("=" * 100)
    
    # Basierend auf der Struktur: Spalte 17 sollte "Jahr" sein
    # Aber wir müssen die richtige Spalte finden
    header_line = csv_data[2] if len(csv_data) > 2 else None
    if header_line:
        print("\nHeader-Zeile (Zeile 3):")
        for j, col in enumerate(header_line):
            if col.strip():
                print(f"  Spalte {j}: '{col.strip()}'")
                if 'jahr' in col.lower() or 'kumuliert' in col.lower():
                    print(f"    ⭐ Mögliche 'Jahr'-Spalte gefunden!")
    
    # Versuche Werte zu extrahieren
    globalcube_nw = None
    globalcube_gw = None
    globalcube_gw_kunden = None
    
    # Suche nach "Jahr" Spalte
    jahr_spalte = None
    if header_line:
        for j, col in enumerate(header_line):
            if col.strip() and ('jahr' in col.lower() or 'kumuliert' in col.lower()):
                jahr_spalte = j
                break
    
    if jahr_spalte is None:
        # Fallback: Spalte 17 (basierend auf vorherigen Analysen)
        jahr_spalte = 17
    
    print(f"\nVerwende Spalte {jahr_spalte} für Jahreswerte")
    
    # Extrahiere NW
    if len(csv_data) > 3:
        nw_val_str = csv_data[3][jahr_spalte].strip() if jahr_spalte < len(csv_data[3]) else ""
        if nw_val_str:
            try:
                globalcube_nw = float(nw_val_str.replace('.', '').replace(',', '.'))
                print(f"  NW (Jahr): {globalcube_nw:.2f} Stk.")
            except:
                print(f"  NW: Konnte nicht extrahieren: '{nw_val_str}'")
    
    # Extrahiere GW
    if len(csv_data) > 12:
        gw_val_str = csv_data[12][jahr_spalte].strip() if jahr_spalte < len(csv_data[12]) else ""
        if gw_val_str:
            try:
                globalcube_gw = float(gw_val_str.replace('.', '').replace(',', '.'))
                print(f"  GW (Jahr): {globalcube_gw:.2f} Stk.")
            except:
                print(f"  GW: Konnte nicht extrahieren: '{gw_val_str}'")
    
    # Extrahiere GW Kunden
    if len(csv_data) > 13:
        gw_kunden_val_str = csv_data[13][jahr_spalte].strip() if jahr_spalte < len(csv_data[13]) else ""
        if gw_kunden_val_str:
            try:
                globalcube_gw_kunden = float(gw_kunden_val_str.replace('.', '').replace(',', '.'))
                print(f"  GW Kunden (Jahr): {globalcube_gw_kunden:.2f} Stk.")
            except:
                print(f"  GW Kunden: Konnte nicht extrahieren: '{gw_kunden_val_str}'")
    
    # Vergleich mit DRIVE BWA
    if globalcube_nw and globalcube_gw:
        print("\n" + "=" * 100)
        print("Vergleich mit DRIVE BWA:")
        print("=" * 100)
        
        gj_von = "2024-09-01"
        gj_bis = "2025-09-01"
        
        with locosoft_session() as conn:
            cursor = conn.cursor()
            
            # NW (N+T+V)
            cursor.execute("""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('N', 'T', 'V')
            """, (gj_von, gj_bis))
            drive_nw = int(cursor.fetchone()[0] or 0)
            
            # GW (D+G+L)
            cursor.execute("""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('D', 'G', 'L')
            """, (gj_von, gj_bis))
            drive_gw = int(cursor.fetchone()[0] or 0)
            
            # GW nur G
            cursor.execute("""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type = 'G'
            """, (gj_von, gj_bis))
            drive_gw_g = int(cursor.fetchone()[0] or 0)
            
            # GW Kunden (nur G, ohne D+L?)
            # Oder vielleicht nur bestimmte Verkaufsarten?
            
            print(f"\nNW:")
            print(f"  Global Cube: {globalcube_nw:.2f} Stk.")
            print(f"  DRIVE (N+T+V): {drive_nw} Stk.")
            print(f"  Differenz: {drive_nw - globalcube_nw:+.2f} Stk. ({(drive_nw - globalcube_nw) / globalcube_nw * 100:+.2f}%)")
            
            print(f"\nGW:")
            print(f"  Global Cube: {globalcube_gw:.2f} Stk.")
            print(f"  DRIVE (D+G+L): {drive_gw} Stk.")
            print(f"  DRIVE (nur G): {drive_gw_g} Stk.")
            print(f"  Differenz (D+G+L): {drive_gw - globalcube_gw:+.2f} Stk. ({(drive_gw - globalcube_gw) / globalcube_gw * 100:+.2f}%)")
            print(f"  Differenz (nur G): {drive_gw_g - globalcube_gw:+.2f} Stk. ({(drive_gw_g - globalcube_gw) / globalcube_gw * 100:+.2f}%)")
            
            if globalcube_gw_kunden:
                print(f"\nGW Kunden (Global Cube): {globalcube_gw_kunden:.2f} Stk.")
                print(f"  Differenz zu GW (nur G): {drive_gw_g - globalcube_gw_kunden:+.2f} Stk.")
                print(f"  Differenz zu GW (D+G+L): {drive_gw - globalcube_gw_kunden:+.2f} Stk.")
    
except FileNotFoundError:
    print(f"❌ Datei nicht gefunden: {csv_file_path}")
    print("\nBitte kopiere die CSV-Datei auf den Server:")
    print(f"  scp \"c:\\Users\\florian.greiner\\Downloads\\F.03 BWA Vorjahres-Vergleich (18).csv\" ag-admin@10.80.80.20:/home/ag-admin/Downloads/")
except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()

