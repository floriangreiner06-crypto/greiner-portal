#!/usr/bin/env python3
"""
PostgreSQL Migration Verification
==================================
TAG 135: Vergleicht SQLite und PostgreSQL Datenbanken

Verwendung:
    python3 verify_migration.py [--fix-sequences]
"""

import sys
import os
sys.path.insert(0, '/opt/greiner-portal')

import sqlite3
import argparse
from datetime import datetime

# PostgreSQL optional
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


# Konfiguration
SQLITE_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
PG_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'drive_portal',
    'user': 'drive_user',
    'password': 'DrivePortal2024'
}


def get_sqlite_connection():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_pg_connection():
    if not PSYCOPG2_AVAILABLE:
        raise ImportError("psycopg2 nicht installiert")
    return psycopg2.connect(**PG_CONFIG)


def get_sqlite_tables():
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def get_pg_tables():
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def get_table_count(db_type, table_name):
    try:
        if db_type == 'sqlite':
            conn = get_sqlite_connection()
        else:
            conn = get_pg_connection()

        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        return f"ERROR: {e}"


def verify_migration():
    print("=" * 60)
    print("PostgreSQL Migration Verification")
    print(f"Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Prüfe Verfügbarkeit
    print("\n[1] Prüfe Verbindungen...")

    # SQLite
    try:
        conn = get_sqlite_connection()
        conn.close()
        print("  ✓ SQLite: OK")
    except Exception as e:
        print(f"  ✗ SQLite: {e}")
        return False

    # PostgreSQL
    if not PSYCOPG2_AVAILABLE:
        print("  ✗ PostgreSQL: psycopg2 nicht installiert")
        return False

    try:
        conn = get_pg_connection()
        conn.close()
        print("  ✓ PostgreSQL: OK")
    except Exception as e:
        print(f"  ✗ PostgreSQL: {e}")
        return False

    # Tabellen vergleichen
    print("\n[2] Vergleiche Tabellen...")

    sqlite_tables = set(get_sqlite_tables())
    pg_tables = set(get_pg_tables())

    # SQLite-spezifische Tabellen ignorieren
    ignore_tables = {'sqlite_sequence'}
    sqlite_tables -= ignore_tables

    missing_in_pg = sqlite_tables - pg_tables
    extra_in_pg = pg_tables - sqlite_tables

    if missing_in_pg:
        print(f"  ⚠ Fehlen in PostgreSQL: {missing_in_pg}")
    if extra_in_pg:
        print(f"  ℹ Zusätzlich in PostgreSQL: {extra_in_pg}")

    common_tables = sqlite_tables & pg_tables
    print(f"  Gemeinsame Tabellen: {len(common_tables)}")

    # Zeilenzahlen vergleichen
    print("\n[3] Vergleiche Zeilenzahlen...")

    mismatches = []
    for table in sorted(common_tables):
        sqlite_count = get_table_count('sqlite', table)
        pg_count = get_table_count('postgresql', table)

        if isinstance(sqlite_count, str) or isinstance(pg_count, str):
            print(f"  ⚠ {table}: SQLite={sqlite_count}, PG={pg_count}")
            continue

        if sqlite_count == pg_count:
            print(f"  ✓ {table}: {sqlite_count} Zeilen")
        else:
            print(f"  ✗ {table}: SQLite={sqlite_count}, PG={pg_count}")
            mismatches.append((table, sqlite_count, pg_count))

    # Zusammenfassung
    print("\n" + "=" * 60)
    if not mismatches and not missing_in_pg:
        print("✓ MIGRATION ERFOLGREICH")
        print("Alle Tabellen und Zeilenzahlen stimmen überein.")
        return True
    else:
        print("⚠ MIGRATION UNVOLLSTÄNDIG")
        if missing_in_pg:
            print(f"  - {len(missing_in_pg)} Tabellen fehlen in PostgreSQL")
        if mismatches:
            print(f"  - {len(mismatches)} Tabellen haben unterschiedliche Zeilenzahlen")
        return False


def fix_sequences():
    """Korrigiert PostgreSQL Sequences nach Migration"""
    print("\n[4] Korrigiere Sequences...")

    conn = get_pg_connection()
    cursor = conn.cursor()

    # Alle Tabellen mit Serial/Identity Spalten
    cursor.execute("""
        SELECT
            t.table_name,
            c.column_name
        FROM information_schema.tables t
        JOIN information_schema.columns c
            ON t.table_name = c.table_name
        WHERE t.table_schema = 'public'
            AND c.column_default LIKE 'nextval%'
    """)

    sequences = cursor.fetchall()

    for table_name, column_name in sequences:
        try:
            # Max-Wert ermitteln und Sequence setzen
            cursor.execute(f"""
                SELECT setval(
                    pg_get_serial_sequence('{table_name}', '{column_name}'),
                    COALESCE((SELECT MAX({column_name}) FROM {table_name}), 1)
                )
            """)
            print(f"  ✓ {table_name}.{column_name}: Sequence korrigiert")
        except Exception as e:
            print(f"  ✗ {table_name}.{column_name}: {e}")

    conn.commit()
    conn.close()
    print("  Sequences aktualisiert.")


def main():
    parser = argparse.ArgumentParser(description='PostgreSQL Migration Verification')
    parser.add_argument('--fix-sequences', action='store_true',
                        help='Korrigiert Sequences nach Migration')
    args = parser.parse_args()

    success = verify_migration()

    if args.fix_sequences:
        fix_sequences()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
