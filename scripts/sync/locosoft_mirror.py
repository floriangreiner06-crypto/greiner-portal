#!/usr/bin/env python3
"""
LOCOSOFT KOMPLETT-MIRROR nach PostgreSQL
=========================================
Version: 2.0
Datum: 2025-12-23 (TAG 136 - PostgreSQL Migration)

Spiegelt ALLE Locosoft-Tabellen nach UNSERE PostgreSQL-Datenbank.
Prefix: loco_ (vermeidet Konflikte mit eigenen Tabellen)

QUELLE: Locosoft PostgreSQL (10.80.80.8)
ZIEL:   Greiner Portal PostgreSQL (127.0.0.1/drive_portal)

Verwendung:
    python locosoft_mirror.py                    # Alle Tabellen
    python locosoft_mirror.py --tables journal_accountings,vehicles
    python locosoft_mirror.py --min-rows 100     # Nur Tabellen mit >100 Zeilen
    python locosoft_mirror.py --dry-run          # Nur zeigen, nicht syncen

Celery Schedule:
    Taeglich 19:00 Uhr (nach Locosoft-Sync)
"""

import os
import sys
import json
import argparse
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal

# Projekt-Pfad für Imports
sys.path.insert(0, '/opt/greiner-portal')

# =============================================================================
# KONFIGURATION
# =============================================================================

CREDENTIALS_PATH = '/opt/greiner-portal/config/credentials.json'

# Prefix fuer gespiegelte Tabellen
TABLE_PREFIX = 'loco_'

# Ziel-Datenbank (unsere PostgreSQL)
TARGET_DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'drive_portal',
    'user': 'drive_user',
    'password': 'DrivePortal2024'
}

# Versuche .env zu laden für Konfiguration
try:
    from dotenv import load_dotenv
    load_dotenv('/opt/greiner-portal/config/.env')
    TARGET_DB_CONFIG = {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'drive_portal'),
        'user': os.getenv('DB_USER', 'drive_user'),
        'password': os.getenv('DB_PASSWORD', 'DrivePortal2024')
    }
except ImportError:
    pass

# Tabellen die NICHT gespiegelt werden sollen (zu gross oder irrelevant)
SKIP_TABLES = [
    'model_options_code',      # 1.7 Mio - Konfigurator
    'model_options_outside',   # 1.5 Mio - Konfigurator
    'model_options_inside',    # 182k - Konfigurator
    'model_options_trim',      # 60k - Konfigurator
    'models',                  # 112k - Konfigurator
    'model_to_fuels',          # 55k - Konfigurator
    'parts_to_vehicles',       # Sehr gross
]

# VIEWs die ZUSÄTZLICH gespiegelt werden sollen
# (werden standardmäßig nicht erfasst, da nur BASE TABLE)
INCLUDE_VIEWS = [
    'times',                   # Stempelzeiten - KRITISCH für Werkstatt-Dashboard!
    'employees',               # Mitarbeiter-View
]

# =============================================================================
# LOGGING
# =============================================================================

def log(msg: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

# =============================================================================
# DATENBANKVERBINDUNGEN
# =============================================================================

def get_locosoft_credentials() -> dict:
    """Locosoft-Credentials aus config laden"""
    with open(CREDENTIALS_PATH, 'r') as f:
        creds = json.load(f)
    return creds['databases']['locosoft']

def connect_locosoft() -> psycopg2.extensions.connection:
    """Verbindung zu Locosoft PostgreSQL (QUELLE)"""
    creds = get_locosoft_credentials()
    return psycopg2.connect(
        host=creds['host'],
        port=creds['port'],
        database=creds['database'],
        user=creds['user'],
        password=creds['password']
    )

def connect_target() -> psycopg2.extensions.connection:
    """Verbindung zu unserer PostgreSQL (ZIEL)"""
    return psycopg2.connect(**TARGET_DB_CONFIG)

# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def convert_value(val: Any) -> Any:
    """Konvertiert Werte für PostgreSQL-Insert"""
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, timedelta):
        # timedelta als Intervall-String speichern
        total_seconds = val.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    if isinstance(val, (list, dict)):
        return json.dumps(val)
    return val

def get_all_tables(source_conn) -> List[Dict]:
    """Alle Tabellen mit Zeilenanzahl aus Locosoft holen"""
    cursor = source_conn.cursor()
    cursor.execute("""
        SELECT
            t.table_name,
            COALESCE(s.n_live_tup, 0) as row_count
        FROM information_schema.tables t
        LEFT JOIN pg_stat_user_tables s ON t.table_name = s.relname
        WHERE t.table_schema = 'public'
        AND t.table_type = 'BASE TABLE'
        ORDER BY COALESCE(s.n_live_tup, 0) DESC
    """)
    tables = [{'name': row[0], 'rows': row[1]} for row in cursor.fetchall()]

    # VIEWs hinzufügen (aus INCLUDE_VIEWS Liste)
    for view_name in INCLUDE_VIEWS:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {view_name}")
            row_count = cursor.fetchone()[0]
            tables.append({'name': view_name, 'rows': row_count, 'is_view': True})
            log(f"VIEW '{view_name}' hinzugefuegt: {row_count:,} Zeilen")
        except Exception as e:
            log(f"VIEW '{view_name}' nicht gefunden: {e}", "WARN")

    return tables

def get_table_columns(source_conn, table_name: str) -> List[Dict]:
    """Spalten einer Tabelle mit Typen holen"""
    cursor = source_conn.cursor()
    cursor.execute("""
        SELECT column_name, data_type, is_nullable,
               character_maximum_length, numeric_precision, numeric_scale
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    return [{
        'name': row[0],
        'type': row[1],
        'nullable': row[2] == 'YES',
        'max_length': row[3],
        'precision': row[4],
        'scale': row[5]
    } for row in cursor.fetchall()]

def map_pg_type(col: Dict) -> str:
    """PostgreSQL-Typ für Zieltabelle bestimmen"""
    pg_type = col['type'].lower()

    # Array-Typen als JSONB speichern
    if pg_type.endswith('[]') or 'array' in pg_type:
        return 'JSONB'

    # Numerische Typen
    if pg_type in ('bigint', 'integer', 'smallint'):
        return pg_type.upper()
    if pg_type in ('real', 'double precision'):
        return pg_type.upper()
    if pg_type == 'numeric':
        if col['precision'] and col['scale']:
            return f"NUMERIC({col['precision']},{col['scale']})"
        return 'NUMERIC'

    # Text-Typen
    if pg_type in ('text', 'json', 'jsonb', 'xml'):
        return 'TEXT'
    if pg_type in ('character varying', 'varchar'):
        if col['max_length']:
            return f"VARCHAR({col['max_length']})"
        return 'TEXT'
    if pg_type == 'character':
        return f"CHAR({col['max_length'] or 1})"

    # Datum/Zeit-Typen (direkt übernehmen)
    if pg_type in ('date', 'time without time zone', 'time with time zone',
                   'timestamp without time zone', 'timestamp with time zone',
                   'interval'):
        return pg_type.upper()

    # Boolean
    if pg_type == 'boolean':
        return 'BOOLEAN'

    # Binär
    if pg_type == 'bytea':
        return 'BYTEA'

    # UUID
    if pg_type == 'uuid':
        return 'UUID'

    # Default: TEXT
    return 'TEXT'

# =============================================================================
# SYNC-FUNKTIONEN
# =============================================================================

def create_target_table(target_conn, table_name: str, columns: List[Dict]):
    """PostgreSQL-Tabelle in Ziel-DB erstellen (DROP + CREATE)"""
    cursor = target_conn.cursor()
    target_table = f"{TABLE_PREFIX}{table_name}"

    # Drop falls existiert
    cursor.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
        sql.Identifier(target_table)
    ))

    # CREATE Statement bauen
    col_defs = []
    for col in columns:
        pg_type = map_pg_type(col)
        null_str = "" if col['nullable'] else " NOT NULL"
        col_defs.append(f'"{col["name"]}" {pg_type}{null_str}')

    create_sql = f'CREATE TABLE "{target_table}" ({", ".join(col_defs)})'
    cursor.execute(create_sql)
    target_conn.commit()

def sync_table(source_conn, target_conn, table_name: str, columns: List[Dict], batch_size: int = 5000) -> int:
    """Tabelle von Locosoft nach unserer PostgreSQL kopieren"""
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    target_table = f"{TABLE_PREFIX}{table_name}"

    # Alle Daten lesen
    col_names = [f'"{c["name"]}"' for c in columns]
    source_cursor.execute(f'SELECT {",".join(col_names)} FROM "{table_name}"')

    # Insert vorbereiten
    placeholders = ','.join(['%s' for _ in columns])
    col_names_target = [f'"{c["name"]}"' for c in columns]
    insert_sql = f'INSERT INTO "{target_table}" ({",".join(col_names_target)}) VALUES ({placeholders})'

    total = 0
    while True:
        rows = source_cursor.fetchmany(batch_size)
        if not rows:
            break

        # Werte konvertieren
        converted_rows = []
        for row in rows:
            converted_rows.append(tuple(convert_value(val) for val in row))

        # Batch-Insert
        execute_batch(target_cursor, insert_sql, converted_rows, page_size=1000)
        total += len(rows)

        if total % 50000 == 0:
            log(f"  ... {total:,} Zeilen")
            target_conn.commit()

    target_conn.commit()
    return total

def create_indexes(target_conn, table_name: str, columns: List[Dict]):
    """Standard-Indizes erstellen"""
    cursor = target_conn.cursor()
    target_table = f"{TABLE_PREFIX}{table_name}"

    # Typische Index-Felder
    index_candidates = [
        'id', 'document_number', 'customer_number', 'vehicle_reference',
        'accounting_date', 'document_date', 'subsidiary_to_company_ref',
        'branch_number', 'nominal_account_number', 'employee_number',
        'invoice_date', 'order_date', 'vin', 'license_plate',
        'work_start', 'work_end', 'created_timestamp'
    ]

    # Pruefen welche Spalten existieren
    existing_cols = {col['name'] for col in columns}

    for col in index_candidates:
        if col in existing_cols:
            idx_name = f"idx_{target_table}_{col}"
            try:
                cursor.execute(f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON "{target_table}"("{col}")')
            except Exception as e:
                log(f"  Index {idx_name} Fehler: {e}", "WARN")

    target_conn.commit()

# =============================================================================
# HAUPTFUNKTION
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Locosoft -> PostgreSQL Mirror')
    parser.add_argument('--tables', type=str, help='Komma-separierte Liste von Tabellen')
    parser.add_argument('--min-rows', type=int, default=0, help='Nur Tabellen mit mindestens X Zeilen')
    parser.add_argument('--dry-run', action='store_true', help='Nur anzeigen, nicht syncen')
    parser.add_argument('--no-skip', action='store_true', help='Auch uebersprungene Tabellen syncen')
    args = parser.parse_args()

    log("=" * 60)
    log("LOCOSOFT KOMPLETT-MIRROR (PostgreSQL -> PostgreSQL)")
    log(f"Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)
    log(f"QUELLE: Locosoft PostgreSQL ({get_locosoft_credentials()['host']})")
    log(f"ZIEL:   Greiner Portal PostgreSQL ({TARGET_DB_CONFIG['host']}:{TARGET_DB_CONFIG['port']}/{TARGET_DB_CONFIG['database']})")
    log("=" * 60)

    # Verbindungen
    log("\nVerbinde zu Locosoft PostgreSQL (QUELLE)...")
    source_conn = connect_locosoft()

    log("Verbinde zu Greiner Portal PostgreSQL (ZIEL)...")
    target_conn = connect_target()

    # Tabellen ermitteln
    if args.tables:
        table_names = [t.strip() for t in args.tables.split(',')]
        tables = [{'name': t, 'rows': '?'} for t in table_names]
    else:
        log("Ermittle alle Tabellen aus Locosoft...")
        tables = get_all_tables(source_conn)

    # Filtern
    if args.min_rows > 0:
        tables = [t for t in tables if isinstance(t['rows'], int) and t['rows'] >= args.min_rows]

    if not args.no_skip:
        tables = [t for t in tables if t['name'] not in SKIP_TABLES]

    log(f"Zu syncende Tabellen: {len(tables)}")

    if args.dry_run:
        log("\n=== DRY-RUN - Keine Aenderungen ===")
        total_rows = 0
        for t in tables:
            rows_str = f"{t['rows']:,}" if isinstance(t['rows'], int) else t['rows']
            log(f"  {t['name']}: {rows_str} Zeilen")
            total_rows += t['rows'] if isinstance(t['rows'], int) else 0
        log(f"\nGesamt: {total_rows:,} Zeilen")
        return

    # Sync durchfuehren
    log("\n" + "=" * 60)
    log("SYNC STARTEN")
    log("=" * 60)

    stats = {'success': 0, 'failed': 0, 'rows': 0}
    errors = []

    for i, table in enumerate(tables, 1):
        table_name = table['name']
        log(f"\n[{i}/{len(tables)}] {table_name}...")

        try:
            # Spalten holen
            columns = get_table_columns(source_conn, table_name)
            if not columns:
                log(f"  Keine Spalten gefunden - uebersprungen")
                continue

            # Tabelle erstellen
            create_target_table(target_conn, table_name, columns)

            # Daten kopieren
            rows = sync_table(source_conn, target_conn, table_name, columns)

            # Indizes erstellen
            create_indexes(target_conn, table_name, columns)

            log(f"  OK: {rows:,} Zeilen")
            stats['success'] += 1
            stats['rows'] += rows

        except Exception as e:
            log(f"  FEHLER: {e}", "ERROR")
            errors.append(f"{table_name}: {e}")
            stats['failed'] += 1
            target_conn.rollback()

    # Zusammenfassung
    log("\n" + "=" * 60)
    log("ZUSAMMENFASSUNG")
    log("=" * 60)
    log(f"Tabellen synchronisiert: {stats['success']}")
    log(f"Tabellen fehlgeschlagen: {stats['failed']}")
    log(f"Zeilen gesamt:           {stats['rows']:,}")

    if errors:
        log(f"\nFehler ({len(errors)}):", "ERROR")
        for err in errors:
            log(f"  - {err}", "ERROR")

    log("\nMirror abgeschlossen!")

    # Cleanup
    source_conn.close()
    target_conn.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log("\nAbgebrochen durch Benutzer", "WARN")
        sys.exit(1)
    except Exception as e:
        log(f"Unerwarteter Fehler: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
