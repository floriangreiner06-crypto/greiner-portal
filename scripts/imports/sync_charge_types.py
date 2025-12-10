#!/usr/bin/env python3
"""
SYNC CHARGE TYPES - Locosoft → SQLite
======================================
Synchronisiert Berechnungsarten (charge_types) von Locosoft nach SQLite.

Tabellen:
- charge_types_sync: Alle Berechnungsarten mit AW-Preisen
- charge_type_descriptions_sync: Beschreibungen

Aufruf:
    python sync_charge_types.py           # Normaler Sync
    python sync_charge_types.py --force   # Neu erstellen
    python sync_charge_types.py --show    # Nur anzeigen

Author: Claude
Date: 2025-12-09 (TAG 110)
"""

import os
import sys
import sqlite3
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pfade
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'greiner_controlling.db'

# Dotenv laden
sys.path.insert(0, str(PROJECT_ROOT))
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / 'config' / '.env')


def get_locosoft_connection():
    """Verbindung zu Locosoft PostgreSQL"""
    import psycopg2
    return psycopg2.connect(
        host=os.getenv('LOCOSOFT_HOST'),
        port=os.getenv('LOCOSOFT_PORT', 5432),
        database=os.getenv('LOCOSOFT_DATABASE'),
        user=os.getenv('LOCOSOFT_USER'),
        password=os.getenv('LOCOSOFT_PASSWORD')
    )


def get_sqlite_connection():
    """Verbindung zu SQLite"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn: sqlite3.Connection, force: bool = False):
    """Erstellt die Sync-Tabellen in SQLite"""
    cursor = conn.cursor()
    
    if force:
        logger.info("🗑️  Lösche bestehende Tabellen...")
        cursor.execute("DROP TABLE IF EXISTS charge_types_sync")
        cursor.execute("DROP TABLE IF EXISTS charge_type_descriptions_sync")
    
    # Haupttabelle: charge_types_sync
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS charge_types_sync (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type INTEGER NOT NULL,
            subsidiary INTEGER NOT NULL,
            timeunit_rate REAL,
            department INTEGER,
            
            -- Berechnete Felder
            stundensatz REAL,
            kategorie TEXT,
            abteilung_name TEXT,
            
            -- Sync-Info
            synced_at TEXT NOT NULL,
            
            UNIQUE(type, subsidiary)
        )
    """)
    
    # Beschreibungen: charge_type_descriptions_sync
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS charge_type_descriptions_sync (
            type INTEGER PRIMARY KEY,
            description TEXT,
            synced_at TEXT NOT NULL
        )
    """)
    
    # Index für schnelle Abfragen
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_charge_types_subsidiary 
        ON charge_types_sync(subsidiary)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_charge_types_department 
        ON charge_types_sync(department)
    """)
    
    conn.commit()
    logger.info("✅ Tabellen erstellt/geprüft")


def get_kategorie(charge_type: int) -> str:
    """Ermittelt Kategorie für charge_type"""
    kategorien = {
        10: 'werkstatt_mechanik',
        11: 'werkstatt_wartung',
        15: 'werkstatt_elektrik',
        16: 'elektrofahrzeug',
        18: 'elektrofahrzeug_karosserie',
        12: 'leasing_alphabet',
        13: 'leasing_stellantis_bank',
        14: 'leasing_allgemein',
        17: 'leasing_ofl_ald',
        20: 'karosserie',
        30: 'lackierung',
        40: 'intern',
        88: 'intern_tuev',
        60: 'garantie',
        68: 'kulanz_gw',
        69: 'kulanz_nw',
        72: 'garantie_greiner',
        90: 'fremdleistung',
        91: 'fremdleistung_garantie',
    }
    
    # Bereichs-basierte Kategorien
    if charge_type in kategorien:
        return kategorien[charge_type]
    elif 20 <= charge_type < 30:
        return 'karosserie'
    elif 30 <= charge_type < 40:
        return 'lackierung'
    elif 40 <= charge_type < 50:
        return 'intern'
    elif 60 <= charge_type < 70:
        return 'garantie'
    elif 90 <= charge_type < 100:
        return 'fremdleistung'
    elif 50 <= charge_type < 60 or 70 <= charge_type < 90:
        return 'erloese_sonstige'
    else:
        return 'sonstige'


def get_abteilung_name(department: int) -> str:
    """Ermittelt Abteilungsname"""
    namen = {
        1: 'Werkstatt',
        2: 'Karosserie',
        3: 'Lackierung',
        4: 'Intern',
        6: 'Garantie',
        9: 'Fremdleistung'
    }
    return namen.get(department, f'Abteilung {department}' if department else 'Unbekannt')


def sync_from_locosoft():
    """Hauptsync-Funktion: Locosoft → SQLite"""
    logger.info("🔄 Starte Sync: Locosoft → SQLite")
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Locosoft-Daten holen
    logger.info("📥 Lade Daten aus Locosoft...")
    pg_conn = get_locosoft_connection()
    pg_cursor = pg_conn.cursor()
    
    # charge_types
    pg_cursor.execute("""
        SELECT type, subsidiary, timeunit_rate, department
        FROM charge_types
        ORDER BY subsidiary, type
    """)
    charge_types = pg_cursor.fetchall()
    logger.info(f"   {len(charge_types)} charge_types geladen")
    
    # charge_type_descriptions
    pg_cursor.execute("""
        SELECT type, description
        FROM charge_type_descriptions
        ORDER BY type
    """)
    descriptions = pg_cursor.fetchall()
    logger.info(f"   {len(descriptions)} Beschreibungen geladen")
    
    pg_cursor.close()
    pg_conn.close()
    
    # In SQLite speichern
    logger.info("💾 Speichere in SQLite...")
    sqlite_conn = get_sqlite_connection()
    sqlite_cursor = sqlite_conn.cursor()
    
    # charge_types_sync
    inserted_ct = 0
    updated_ct = 0
    
    for row in charge_types:
        type_nr, subsidiary, timeunit_rate, department = row
        
        # Berechnete Felder
        stundensatz = float(timeunit_rate) * 10 if timeunit_rate else None
        kategorie = get_kategorie(type_nr)
        abteilung_name = get_abteilung_name(department)
        
        # Upsert
        sqlite_cursor.execute("""
            INSERT INTO charge_types_sync 
                (type, subsidiary, timeunit_rate, department, stundensatz, kategorie, abteilung_name, synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(type, subsidiary) DO UPDATE SET
                timeunit_rate = excluded.timeunit_rate,
                department = excluded.department,
                stundensatz = excluded.stundensatz,
                kategorie = excluded.kategorie,
                abteilung_name = excluded.abteilung_name,
                synced_at = excluded.synced_at
        """, (
            type_nr, subsidiary, 
            float(timeunit_rate) if timeunit_rate else None,
            department, stundensatz, kategorie, abteilung_name, now
        ))
        
        if sqlite_cursor.rowcount > 0:
            inserted_ct += 1
    
    # charge_type_descriptions_sync
    inserted_desc = 0
    
    for row in descriptions:
        type_nr, description = row
        
        sqlite_cursor.execute("""
            INSERT INTO charge_type_descriptions_sync (type, description, synced_at)
            VALUES (?, ?, ?)
            ON CONFLICT(type) DO UPDATE SET
                description = excluded.description,
                synced_at = excluded.synced_at
        """, (type_nr, description, now))
        
        if sqlite_cursor.rowcount > 0:
            inserted_desc += 1
    
    sqlite_conn.commit()
    sqlite_conn.close()
    
    logger.info(f"✅ Sync abgeschlossen:")
    logger.info(f"   charge_types: {inserted_ct} Einträge")
    logger.info(f"   descriptions: {inserted_desc} Einträge")
    
    return {
        'charge_types': inserted_ct,
        'descriptions': inserted_desc,
        'timestamp': now
    }


def show_current_data():
    """Zeigt aktuellen Stand in SQLite"""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("CHARGE TYPES IN SQLITE (mit AW-Preis > 0)")
    print("=" * 80)
    
    cursor.execute("""
        SELECT 
            ct.type,
            ctd.description,
            ct.timeunit_rate as aw_preis,
            ct.stundensatz,
            ct.subsidiary as betrieb,
            ct.abteilung_name,
            ct.kategorie
        FROM charge_types_sync ct
        LEFT JOIN charge_type_descriptions_sync ctd ON ct.type = ctd.type
        WHERE ct.timeunit_rate > 0
        ORDER BY ct.subsidiary, ct.type
    """)
    
    rows = cursor.fetchall()
    
    current_betrieb = None
    for row in rows:
        if row['betrieb'] != current_betrieb:
            current_betrieb = row['betrieb']
            betrieb_name = {1: 'Deggendorf', 2: 'Hyundai DEG', 3: 'Landau'}.get(current_betrieb, f'Betrieb {current_betrieb}')
            print(f"\n--- {betrieb_name} ---")
            print(f"{'Type':>4} | {'Beschreibung':<35} | {'AW-Preis':>8} | {'€/Std':>8} | {'Kategorie':<25}")
            print("-" * 95)
        
        print(f"{row['type']:>4} | {(row['description'] or '-')[:35]:<35} | {row['aw_preis']:>8.2f} | {row['stundensatz']:>8.2f} | {row['kategorie']:<25}")
    
    # Statistik
    cursor.execute("SELECT COUNT(*) FROM charge_types_sync")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT MAX(synced_at) FROM charge_types_sync")
    last_sync = cursor.fetchone()[0]
    
    print(f"\n{'=' * 80}")
    print(f"Gesamt: {total} Einträge | Letzter Sync: {last_sync}")
    print("=" * 80)
    
    conn.close()


def main():
    parser = argparse.ArgumentParser(description='Sync charge_types von Locosoft nach SQLite')
    parser.add_argument('--force', action='store_true', help='Tabellen neu erstellen')
    parser.add_argument('--show', action='store_true', help='Nur aktuellen Stand anzeigen')
    args = parser.parse_args()
    
    # SQLite-Tabellen erstellen
    sqlite_conn = get_sqlite_connection()
    create_tables(sqlite_conn, force=args.force)
    sqlite_conn.close()
    
    if args.show:
        show_current_data()
        return
    
    # Sync ausführen
    result = sync_from_locosoft()
    
    # Ergebnis anzeigen
    show_current_data()
    
    print(f"\n✅ Sync erfolgreich: {result['charge_types']} charge_types, {result['descriptions']} descriptions")


if __name__ == '__main__':
    main()
