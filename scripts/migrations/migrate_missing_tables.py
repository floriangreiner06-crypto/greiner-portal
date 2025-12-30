#!/usr/bin/env python3
"""
Migrate Missing Tables Only
============================
TAG 135: Migriert nur fehlende Tabellen ohne Schema-Reset

Verwendung:
    python3 migrate_missing_tables.py
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
    print("ERROR: psycopg2 nicht installiert. pip install psycopg2-binary")
    sys.exit(1)


# Konfiguration
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


def sqlite_type_to_pg(sqlite_type: str) -> str:
    """Konvertiert SQLite-Typen zu PostgreSQL-Typen"""
    t = sqlite_type.upper() if sqlite_type else 'TEXT'

    mappings = {
        'INTEGER': 'INTEGER',
        'INT': 'INTEGER',
        'BIGINT': 'BIGINT',
        'REAL': 'DOUBLE PRECISION',
        'FLOAT': 'DOUBLE PRECISION',
        'DOUBLE': 'DOUBLE PRECISION',
        'NUMERIC': 'NUMERIC',
        'DECIMAL': 'NUMERIC',
        'TEXT': 'TEXT',
        'VARCHAR': 'VARCHAR',
        'CHAR': 'CHAR',
        'BLOB': 'BYTEA',
        'BOOLEAN': 'BOOLEAN',
        'DATE': 'DATE',
        'DATETIME': 'TIMESTAMP',
        'TIMESTAMP': 'TIMESTAMP',
        'TIME': 'TIME',
    }

    if t in mappings:
        return mappings[t]

    for sqlite_t, pg_t in mappings.items():
        if t.startswith(sqlite_t):
            return t.replace(sqlite_t, pg_t)

    return 'TEXT'


def get_table_schema(sqlite_conn, table_name: str) -> tuple:
    """Gibt (columns, primary_key) für eine Tabelle zurück"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = []
    primary_keys = []

    for row in cursor.fetchall():
        col_name = row[1]
        col_type = row[2] or 'TEXT'
        not_null = row[3]
        default_val = row[4]
        is_pk = row[5]

        pg_type = sqlite_type_to_pg(col_type)

        col_def = {
            'name': col_name,
            'type': pg_type,
            'not_null': not_null,
            'default': default_val,
            'is_pk': is_pk
        }
        columns.append(col_def)

        if is_pk:
            primary_keys.append(col_name)

    return columns, primary_keys


def create_pg_table(pg_conn, table_name: str, columns: list, primary_keys: list):
    """Erstellt eine Tabelle in PostgreSQL"""
    cursor = pg_conn.cursor()

    # Drop existing (nur diese Tabelle, nicht alle)
    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')

    col_defs = []
    for col in columns:
        col_def = f'"{col["name"]}" {col["type"]}'

        if col['not_null'] and col['name'] not in primary_keys:
            col_def += ' NOT NULL'

        if col['default'] is not None:
            default_val = str(col['default'])
            if 'CURRENT_TIMESTAMP' in default_val.upper():
                col_def += ' DEFAULT CURRENT_TIMESTAMP'
            elif col['type'] == 'BOOLEAN':
                if default_val in ('1', '1.0', 'true', 'True', 'TRUE'):
                    col_def += ' DEFAULT TRUE'
                elif default_val in ('0', '0.0', 'false', 'False', 'FALSE'):
                    col_def += ' DEFAULT FALSE'
            elif default_val != '':
                col_def += f" DEFAULT {default_val}"

        col_defs.append(col_def)

    if primary_keys:
        col_defs.append(f'PRIMARY KEY ({", ".join(f"{pk}" for pk in primary_keys)})')

    create_sql = f'CREATE TABLE "{table_name}" (\n  ' + ',\n  '.join(col_defs) + '\n)'

    try:
        cursor.execute(create_sql)
        pg_conn.commit()
        return True
    except Exception as e:
        print(f"  ERROR creating table: {e}")
        pg_conn.rollback()
        return False


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
                    if month > 12 or day > 31:
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

    return value


def migrate_table_data(sqlite_conn, pg_conn, table_name: str, columns: list) -> int:
    """Migriert Daten einer Tabelle"""
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    col_names = [c['name'] for c in columns]
    sqlite_cur.execute(f'SELECT * FROM "{table_name}"')

    rows = sqlite_cur.fetchall()
    if not rows:
        return 0

    col_types = {c['name']: c['type'] for c in columns}
    insert_sql = f'INSERT INTO "{table_name}" ({", ".join(f"{c}" for c in col_names)}) VALUES ({", ".join(["%s"] * len(col_names))})'

    batch = []
    inserted = 0
    errors = 0

    for row in rows:
        cleaned_row = []
        for i, col_name in enumerate(col_names):
            val = clean_value(row[i], col_types[col_name])
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
                    except:
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


def get_missing_tables():
    """Findet Tabellen die in SQLite existieren aber nicht in PostgreSQL"""
    sqlite_conn = get_sqlite_conn()
    pg_conn = get_pg_conn()

    # SQLite Tabellen
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    sqlite_tables = set(row[0] for row in sqlite_cur.fetchall() if row[0] != 'sqlite_sequence')

    # PostgreSQL Tabellen
    pg_cur = pg_conn.cursor()
    pg_cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    pg_tables = set(row[0] for row in pg_cur.fetchall())

    sqlite_conn.close()
    pg_conn.close()

    return sqlite_tables - pg_tables


def main():
    print("=" * 60)
    print("Migrate Missing Tables")
    print(f"Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    missing = get_missing_tables()
    print(f"\n[1] {len(missing)} fehlende Tabellen gefunden")

    if not missing:
        print("Keine fehlenden Tabellen!")
        return

    sqlite_conn = get_sqlite_conn()
    pg_conn = get_pg_conn()

    success = 0
    failed = 0
    total_rows = 0

    for i, table_name in enumerate(sorted(missing), 1):
        print(f"\n  [{i}/{len(missing)}] {table_name}...", end=" ", flush=True)

        try:
            columns, primary_keys = get_table_schema(sqlite_conn, table_name)

            if not create_pg_table(pg_conn, table_name, columns, primary_keys):
                failed += 1
                continue

            rows = migrate_table_data(sqlite_conn, pg_conn, table_name, columns)
            print(f"{rows} Zeilen", end="")
            total_rows += rows

            print(" ✓")
            success += 1

        except Exception as e:
            print(f"FEHLER: {e}")
            failed += 1
            pg_conn.rollback()

    sqlite_conn.close()
    pg_conn.close()

    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"  Erfolgreich: {success} Tabellen")
    print(f"  Fehlgeschlagen: {failed} Tabellen")
    print(f"  Gesamt Zeilen: {total_rows:,}")
    print("=" * 60)


if __name__ == '__main__':
    main()
