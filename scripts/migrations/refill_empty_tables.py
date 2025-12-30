#!/usr/bin/env python3
"""
Refill Empty Tables
===================
TAG 135: Befüllt existierende aber leere PostgreSQL-Tabellen mit SQLite-Daten

Verwendung:
    python3 refill_empty_tables.py
"""

import sys
import os
import sqlite3
import re
from datetime import datetime

sys.path.insert(0, '/opt/greiner-portal')

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extras import execute_batch
except ImportError:
    print("ERROR: psycopg2 nicht installiert.")
    sys.exit(1)


SQLITE_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
PG_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'drive_portal',
    'user': 'drive_user',
    'password': 'DrivePortal2024'
}

BATCH_SIZE = 1000


def get_sqlite_conn():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_pg_conn():
    return psycopg2.connect(**PG_CONFIG)


def clean_value(value, col_type: str):
    """Bereinigt Werte für PostgreSQL"""
    if value is None:
        return None

    if 'DATE' in col_type.upper() or 'TIMESTAMP' in col_type.upper():
        if isinstance(value, str):
            if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                try:
                    parts = value.split('-')
                    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                    if month > 12 or month < 1 or day > 31 or day < 1:
                        return None
                    if year < 1900 or year > 2100:
                        return None
                except:
                    return None
            elif re.match(r'^\d{2}\.\d{2}\.\d{4}', value):
                try:
                    parts = value.split('.')
                    day, month, year = parts[0], parts[1], parts[2][:4]
                    return f"{year}-{month}-{day}"
                except:
                    return None
            elif value == '' or value.lower() == 'null':
                return None

    # Boolean-Konvertierung
    if col_type.upper() == 'BOOLEAN':
        if isinstance(value, int):
            return value == 1
        if isinstance(value, str):
            return value.lower() in ('1', 'true', 'yes')

    return value


def get_table_columns(pg_conn, table_name):
    """Holt Spalteninformationen aus PostgreSQL"""
    cursor = pg_conn.cursor()
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    return cursor.fetchall()


def migrate_table_data(sqlite_conn, pg_conn, table_name: str, columns: list) -> int:
    """Migriert Daten einer Tabelle"""
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    col_names = [c[0] for c in columns]
    col_types = {c[0]: c[1] for c in columns}

    try:
        sqlite_cur.execute(f'SELECT * FROM "{table_name}"')
    except Exception as e:
        print(f"  SQLite Fehler: {e}")
        return 0

    rows = sqlite_cur.fetchall()
    if not rows:
        return 0

    # Prüfe ob SQLite die gleichen Spalten hat
    sqlite_cols = [desc[0] for desc in sqlite_cur.description]

    # Nur gemeinsame Spalten migrieren
    common_cols = [c for c in col_names if c in sqlite_cols]
    if not common_cols:
        print(f"  Keine gemeinsamen Spalten gefunden!")
        return 0

    col_list = ", ".join(f'"{c}"' for c in common_cols)
    placeholders = ", ".join(["%s"] * len(common_cols))
    insert_sql = f'INSERT INTO "{table_name}" ({col_list}) VALUES ({placeholders})'

    batch = []
    inserted = 0
    errors = 0

    for row in rows:
        cleaned_row = []
        for col_name in common_cols:
            col_idx = sqlite_cols.index(col_name)
            val = clean_value(row[col_idx], col_types.get(col_name, 'TEXT'))
            cleaned_row.append(val)
        batch.append(tuple(cleaned_row))

        if len(batch) >= BATCH_SIZE:
            try:
                execute_batch(pg_cur, insert_sql, batch)
                pg_conn.commit()
                inserted += len(batch)
            except Exception as e:
                pg_conn.rollback()
                for single_row in batch:
                    try:
                        pg_cur.execute(insert_sql, single_row)
                        pg_conn.commit()
                        inserted += 1
                    except Exception as e2:
                        pg_conn.rollback()
                        errors += 1
            batch = []

    if batch:
        try:
            execute_batch(pg_cur, insert_sql, batch)
            pg_conn.commit()
            inserted += len(batch)
        except:
            pg_conn.rollback()
            for single_row in batch:
                try:
                    pg_cur.execute(insert_sql, single_row)
                    pg_conn.commit()
                    inserted += 1
                except:
                    pg_conn.rollback()
                    errors += 1

    if errors > 0:
        print(f"    ({errors} Zeilen mit Fehlern übersprungen)")

    return inserted


def get_empty_tables():
    """Findet Tabellen die in PostgreSQL leer sind aber in SQLite Daten haben"""
    sqlite_conn = get_sqlite_conn()
    pg_conn = get_pg_conn()

    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    # PostgreSQL Tabellen
    pg_cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    pg_tables = [row[0] for row in pg_cur.fetchall()]

    empty_tables = []

    for table in pg_tables:
        # PostgreSQL Zeilenzahl
        pg_cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        pg_count = pg_cur.fetchone()[0]

        if pg_count == 0:
            # SQLite Zeilenzahl
            try:
                sqlite_cur.execute(f'SELECT COUNT(*) FROM "{table}"')
                sqlite_count = sqlite_cur.fetchone()[0]

                if sqlite_count > 0:
                    empty_tables.append((table, sqlite_count))
            except:
                pass  # Tabelle existiert nicht in SQLite

    sqlite_conn.close()
    pg_conn.close()

    return empty_tables


def main():
    print("=" * 60)
    print("Refill Empty PostgreSQL Tables")
    print(f"Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    empty = get_empty_tables()
    print(f"\n[1] {len(empty)} leere Tabellen mit Daten in SQLite gefunden")

    if not empty:
        print("Keine leeren Tabellen!")
        return

    for table, count in empty:
        print(f"    - {table}: {count} Zeilen in SQLite")

    sqlite_conn = get_sqlite_conn()
    pg_conn = get_pg_conn()

    success = 0
    total_rows = 0

    print(f"\n[2] Befülle Tabellen...")

    for i, (table_name, sqlite_count) in enumerate(empty, 1):
        print(f"\n  [{i}/{len(empty)}] {table_name}...", end=" ", flush=True)

        try:
            columns = get_table_columns(pg_conn, table_name)
            rows = migrate_table_data(sqlite_conn, pg_conn, table_name, columns)
            print(f"{rows}/{sqlite_count} Zeilen", end="")
            total_rows += rows

            if rows > 0:
                print(" ✓")
                success += 1
            else:
                print(" (keine Daten)")

        except Exception as e:
            print(f"FEHLER: {e}")
            pg_conn.rollback()

    sqlite_conn.close()
    pg_conn.close()

    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"  Erfolgreich befüllt: {success} Tabellen")
    print(f"  Gesamt Zeilen: {total_rows:,}")
    print("=" * 60)


if __name__ == '__main__':
    main()
