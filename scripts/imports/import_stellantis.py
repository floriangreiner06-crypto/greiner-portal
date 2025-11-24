#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Import mit Credentials-Integration und Multi-Account-Unterstützung
Liest Passwörter aus config/credentials.json
Version: 2.1 - Fix: Nur neueste ZIP pro RRDI, finanzinstitut gesetzt
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


def get_latest_zips_per_rrdi(source_path):
    """Gibt nur die neueste ZIP-Datei pro RRDI zurück"""
    all_zips = sorted(glob.glob(f"{source_path}/WHSKRELI_*.zip"),
                      key=os.path.getmtime, reverse=True)
    
    zip_files = []
    seen_rrdi = set()
    
    for z in all_zips:
        filename = os.path.basename(z)
        parts = filename.split('_')
        if len(parts) >= 2:
            rrdi = parts[1]
            if rrdi not in seen_rrdi:
                seen_rrdi.add(rrdi)
                zip_files.append(z)
    
    return zip_files


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
print("📦 STELLANTIS-IMPORT (nur neueste ZIP pro RRDI)")
print("="*80 + "\n")

TEMP_DIR = tempfile.mkdtemp()

try:
    # ZIP-Dateien finden - NUR NEUESTE PRO RRDI
    zip_files = get_latest_zips_per_rrdi(STELLANTIS_PATH)

    if not zip_files:
        print("⚠️  Keine ZIP-Dateien gefunden")
        sys.exit(0)

    print(f"ZIP-Dateien zu verarbeiten: {len(zip_files)}")
    for z in zip_files:
        print(f"  → {os.path.basename(z)}")
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
                        excel_files.append((os.path.join(TEMP_DIR, name), rrdi))
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

    # NUR Stellantis löschen (nicht Santander/Hyundai!)
    c.execute("DELETE FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Stellantis'")
    deleted = c.rowcount
    print(f"🗑️  {deleted} alte Stellantis-Fahrzeuge gelöscht\n")

    stats = {'neu': 0}

    # Excel verarbeiten
    for excel_path, rrdi in excel_files:
        print(f"📋 Verarbeite RRDI: {rrdi}")

        try:
            # WICHTIG: skiprows=6, Sheet='Vertragsbestand', Spalten 3-15
            df = pd.read_excel(excel_path, sheet_name='Vertragsbestand', skiprows=6)
        except Exception as e:
            print(f"   ⚠️  Fehler beim Lesen: {e}")
            continue

        if df.empty:
            print(f"   ⚠️  Leeres Sheet, überspringe")
            continue

        # Erste 3 Spalten sind leer, nimm Spalten 3-15
        if len(df.columns) < 16:
            print(f"   ⚠️  Zu wenig Spalten ({len(df.columns)}), überspringe")
            continue
            
        relevant_cols = df.columns[3:16]
        df = df[relevant_cols]

        # Spalten umbenennen (13 Spalten)
        df.columns = ['produktfamilie', 'vin', 'modell', 'alter_tage',
                      'col_7_leer', 'zinsfreiheit_tage', 'vertragsbeginn',
                      'col_10_leer', 'aktueller_saldo', 'original_betrag',
                      'rrdi_col', 'steuer_id', 'gruppe']

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

            c.execute("""
                INSERT OR REPLACE INTO fahrzeugfinanzierungen
                (finanzinstitut, rrdi, produktfamilie, vin, modell, alter_tage, zinsfreiheit_tage,
                 vertragsbeginn, aktueller_saldo, original_betrag, import_datum, aktiv)
                VALUES ('Stellantis', ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 1)
            """, (
                rrdi, produktfamilie, vin, modell, alter_tage, zinsfreiheit_tage,
                vertragsbeginn, aktueller_saldo, original_betrag
            ))
            stats['neu'] += 1

        count_rrdi = stats['neu'] - count_before
        conn.commit()
        print(f"   ✓ {count_rrdi} Fahrzeuge importiert")

    # ========================================
    # ZINSEN BERECHNEN für Stellantis (9,03% p.a.)
    # ========================================
    print("\n📊 Berechne Zinsen für Fahrzeuge über Zinsfreiheit...")
    
    STELLANTIS_ZINSSATZ = 9.03  # % p.a.
    
    c.execute("""
        UPDATE fahrzeugfinanzierungen
        SET 
            zinsen_gesamt = ROUND(aktueller_saldo * ? / 100 * (alter_tage - zinsfreiheit_tage) / 365.0, 2),
            zinsen_letzte_periode = ROUND(aktueller_saldo * ? / 100 * 30 / 365.0, 2),
            zins_startdatum = date(vertragsbeginn, '+' || zinsfreiheit_tage || ' days')
        WHERE finanzinstitut = 'Stellantis'
          AND alter_tage > zinsfreiheit_tage
    """, (STELLANTIS_ZINSSATZ, STELLANTIS_ZINSSATZ))
    
    updated = c.rowcount
    conn.commit()
    print(f"   ✓ {updated} Fahrzeuge mit Zinsen aktualisiert")
    
    # Zinsen-Summary
    c.execute("""
        SELECT COUNT(*), ROUND(SUM(aktueller_saldo),0), ROUND(SUM(zinsen_gesamt),2)
        FROM fahrzeugfinanzierungen
        WHERE finanzinstitut = 'Stellantis' AND zinsen_gesamt > 0
    """)
    cnt, saldo, zinsen = c.fetchone()
    if cnt:
        print(f"   → {cnt} Fz mit {saldo:,.0f} € Saldo = {zinsen:,.2f} € Zinsen")

    # Statistik - nur Stellantis
    print("\n" + "="*60)
    print("📊 STELLANTIS ERGEBNIS:")
    print("="*60)
    
    c.execute("""
        SELECT rrdi, COUNT(*), ROUND(SUM(aktueller_saldo), 2)
        FROM fahrzeugfinanzierungen 
        WHERE finanzinstitut = 'Stellantis'
        GROUP BY rrdi
    """)

    total_fz = 0
    total_saldo = 0
    for rrdi, cnt, saldo in c.fetchall():
        total_fz += cnt
        total_saldo += (saldo or 0)
        print(f"  {rrdi}: {cnt:>3} Fz | {(saldo or 0):>15,.2f} €")

    print(f"  {'─'*45}")
    print(f"  STELLANTIS: {total_fz:>3} Fz | {total_saldo:>15,.2f} €")
    
    # Gesamtübersicht alle Institute
    print("\n" + "="*60)
    print("📊 GESAMTÜBERSICHT ALLE INSTITUTE:")
    print("="*60)
    
    c.execute("""
        SELECT finanzinstitut, COUNT(*), ROUND(SUM(aktueller_saldo), 2)
        FROM fahrzeugfinanzierungen 
        GROUP BY finanzinstitut
    """)
    
    gesamt_fz = 0
    gesamt_saldo = 0
    for institut, cnt, saldo in c.fetchall():
        gesamt_fz += cnt
        gesamt_saldo += (saldo or 0)
        print(f"  {institut}: {cnt:>3} Fz | {(saldo or 0):>15,.2f} €")
    
    print(f"  {'─'*45}")
    print(f"  GESAMT: {gesamt_fz:>3} Fz | {gesamt_saldo:>15,.2f} €")
    print("="*60 + "\n")

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
