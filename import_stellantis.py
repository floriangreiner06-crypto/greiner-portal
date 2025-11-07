# -*- coding: utf-8 -*-
"""
Stellantis Import mit Credentials-Integration und Multi-Account-Unterstützung
Liest Passwörter aus config/credentials.json
Version: 2.1 - Vollständig korrigiert
"""

import sqlite3
import zipfile
import pandas as pd
import os
import shutil
import tempfile
import glob
import sys
import json
from pathlib import Path
from datetime import datetime

# Konfiguration
DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
CREDENTIALS_PATH = '/opt/greiner-portal/config/credentials.json'


def load_stellantis_config():
    """Lädt Stellantis-Konfiguration aus credentials.json"""
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"⚠️  Credentials-Datei nicht gefunden: {CREDENTIALS_PATH}")
        sys.exit(1)

    with open(CREDENTIALS_PATH, 'r') as f:
        credentials = json.load(f)

    if 'external_systems' not in credentials or 'stellantis' not in credentials['external_systems']:
        print("⚠️  Stellantis-Config fehlt in credentials.json")
        sys.exit(1)

    config = credentials['external_systems']['stellantis']

    if 'accounts' not in config:
        print("⚠️  'accounts' fehlt in Stellantis-Config")
        sys.exit(1)

    if 'source_path' not in config:
        config['source_path'] = '/mnt/buchhaltung/Buchhaltung/Kontoauszüge/Stellantis'

    return config


def get_password_for_zip(zip_filename, stellantis_config):
    """Ermittelt das richtige Passwort basierend auf RRDI im Dateinamen"""
    accounts = stellantis_config['accounts']

    for rrdi, account_config in accounts.items():
        if rrdi in zip_filename:
            password = account_config['zip_password'].encode('utf-8')
            return password, rrdi

    print(f"⚠️  Kein RRDI in '{zip_filename}' erkannt")
    return None, None


# Stellantis-Config laden
print("📋 Lade Stellantis-Konfiguration aus credentials.json...")
try:
    stellantis_config = load_stellantis_config()
    STELLANTIS_PATH = stellantis_config['source_path']
    print(f"✓ Konfiguration geladen")
    print(f"  Quelle: {STELLANTIS_PATH}")
    print(f"  Accounts: {', '.join(stellantis_config['accounts'].keys())}")
except Exception as e:
    print(f"✗ Fehler: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("📦 STELLANTIS-IMPORT MIT MULTI-ACCOUNT-UNTERSTÜTZUNG")
print("="*80 + "\n")

TEMP_DIR = tempfile.mkdtemp()

try:
    # ZIP-Dateien finden und nach RRDI gruppieren
    all_zip_files = sorted(glob.glob(f"{STELLANTIS_PATH}/WHSKRELI_*.zip"),
                          key=os.path.getmtime, reverse=True)

    if not all_zip_files:
        print("⚠️  Keine ZIP-Dateien gefunden")
        sys.exit(0)

    # Nur die NEUESTE Datei pro RRDI auswählen
    zip_files_by_rrdi = {}
    for zip_file in all_zip_files:
        zip_filename = os.path.basename(zip_file)
        # RRDI aus Dateiname extrahieren (z.B. DE0154X, DE08250)
        for rrdi in stellantis_config['accounts'].keys():
            if rrdi in zip_filename:
                if rrdi not in zip_files_by_rrdi:
                    zip_files_by_rrdi[rrdi] = zip_file
                break
    
    zip_files = list(zip_files_by_rrdi.values())
    
    print(f"Gefundene RRDIs: {len(zip_files)}")
    for rrdi, zip_file in zip_files_by_rrdi.items():
        print(f"  → {rrdi}: {os.path.basename(zip_file)}")
    print()

    # Extrahieren
    excel_files = []
    for zip_file in zip_files:
        zip_filename = os.path.basename(zip_file)
        print(f"📂 Extrahiere: {zip_filename}")

        password_bytes, rrdi = get_password_for_zip(zip_filename, stellantis_config)

        if password_bytes is None:
            print(f"   ✗ Kein passendes Passwort, überspringe")
            continue

        print(f"   → RRDI: {rrdi}")

        try:
            with zipfile.ZipFile(zip_file, 'r') as zf:
                for name in zf.namelist():
                    if name.endswith('.xlsx'):
                        zf.extract(name, TEMP_DIR, pwd=password_bytes)
                        excel_files.append({
                            'path': os.path.join(TEMP_DIR, name),
                            'filename': name,
                            'rrdi': rrdi
                        })
                        print(f"   ✓ {name}")
        except RuntimeError as e:
            if "password" in str(e).lower():
                print(f"   ✗ Falsches Passwort für RRDI {rrdi}")
                continue
            else:
                raise

    if not excel_files:
        print("\n⚠️  Keine Excel-Dateien extrahiert")
        sys.exit(1)

    print(f"\n📊 Excel-Dateien zu verarbeiten: {len(excel_files)}\n")

    # Datenbank
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("DELETE FROM fahrzeugfinanzierungen")
    print("🗑️  Alte Fahrzeugdaten gelöscht\n")

    stats = {'neu': 0}

    # Excel verarbeiten
    for excel_info in excel_files:
        excel_path = excel_info['path']
        excel_filename = excel_info['filename']
        rrdi = excel_info['rrdi']
        
        print(f"📋 Verarbeite RRDI: {rrdi}")

        # WICHTIG: skiprows=6, Sheet='Vertragsbestand', Spalten 3-15
        df = pd.read_excel(excel_path, sheet_name='Vertragsbestand', skiprows=6)

        # Erste 3 Spalten sind leer, nimm Spalten 3-15
        relevant_cols = df.columns[3:16]
        df = df[relevant_cols]

        # Spalten umbenennen (13 Spalten)
        df.columns = ['produktfamilie', 'vin', 'modell', 'alter_tage',
                      'col_7_leer', 'zinsfreiheit_tage', 'vertragsbeginn',
                      'col_10_leer', 'aktueller_saldo', 'original_betrag',
                      'rrdi_excel', 'steuer_id', 'gruppe']

        # Leere Zeilen entfernen
        df = df.dropna(subset=['vin'])

        count_before = stats['neu']

        # In DB speichern
        for _, row in df.iterrows():
            produktfamilie = str(row['produktfamilie']) if pd.notna(row['produktfamilie']) else None
            vin = str(row['vin']) if pd.notna(row['vin']) else None
            modell = str(row['modell']) if pd.notna(row['modell']) else None
            alter_tage = int(row['alter_tage']) if pd.notna(row['alter_tage']) else None
            zinsfreiheit_tage = int(row['zinsfreiheit_tage']) if pd.notna(row['zinsfreiheit_tage']) else None
            vertragsbeginn = str(row['vertragsbeginn'])[:10] if pd.notna(row['vertragsbeginn']) else None
            aktueller_saldo = float(row['aktueller_saldo']) if pd.notna(row['aktueller_saldo']) else 0
            original_betrag = float(row['original_betrag']) if pd.notna(row['original_betrag']) else 0

            # Schema aus Session Tag 12:
            # (rrdi, produktfamilie, vin, modell, alter_tage, zinsfreiheit_tage, 
            #  vertragsbeginn, aktueller_saldo, original_betrag, import_datum, datei_quelle)
            c.execute("""
                INSERT INTO fahrzeugfinanzierungen 
                (rrdi, produktfamilie, vin, modell, alter_tage, zinsfreiheit_tage, 
                 vertragsbeginn, aktueller_saldo, original_betrag, import_datum, datei_quelle)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
            """, (
                rrdi, produktfamilie, vin, modell, alter_tage, zinsfreiheit_tage,
                vertragsbeginn, aktueller_saldo, original_betrag, excel_filename
            ))
            stats['neu'] += 1

        count_rrdi = stats['neu'] - count_before
        conn.commit()
        print(f"   ✓ {count_rrdi} Fahrzeuge importiert")

    # Statistik
    c.execute("SELECT rrdi, COUNT(*), SUM(aktueller_saldo) FROM fahrzeugfinanzierungen GROUP BY rrdi")

    print("\n📊 ERGEBNIS:\n")
    total_fz = 0
    total_saldo = 0
    for rrdi, cnt, saldo in c.fetchall():
        total_fz += cnt
        total_saldo += (saldo or 0)
        print(f"{rrdi}: {cnt:>3} Fz | {(saldo or 0):>15,.2f} €")

    print(f"\n{'─'*50}")
    print(f"GESAMT: {total_fz} Fz | {total_saldo:>15,.2f} €")
    print("="*80 + "\n")

    conn.close()
    print("✅ Stellantis-Import erfolgreich abgeschlossen!\n")

except Exception as e:
    print(f"\n❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
