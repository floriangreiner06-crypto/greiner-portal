#!/usr/bin/env python3
"""
LOCOSOFT KOMPLETT-MIRROR nach SQLite
=====================================
Version: 1.1
Datum: 2025-11-28 (wiederhergestellt)

Spiegelt ALLE Locosoft-Tabellen nach SQLite.
Prefix: loco_ (vermeidet Konflikte mit eigenen Tabellen)

Verwendung:
    python locosoft_mirror.py                    # Alle Tabellen
    python locosoft_mirror.py --tables journal_accountings,vehicles
    python locosoft_mirror.py --min-rows 100     # Nur Tabellen mit >100 Zeilen
    python locosoft_mirror.py --dry-run          # Nur zeigen, nicht syncen

Cron (empfohlen):
    # Taeglich 20:00 Uhr (nach Locosoft 18-Uhr-Sync)
    0 20 * * * cd /opt/greiner-portal && venv/bin/python3 scripts/sync/locosoft_mirror.py --min-rows 100 >> logs/locosoft_mirror.log 2>&1
"""

import os
import sys
import json
import argparse
import psycopg2
import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal

# =============================================================================
# KONFIGURATION
# =============================================================================

CREDENTIALS_PATH = '/opt/greiner-portal/config/credentials.json'
SQLITE_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

# Prefix fuer gespiegelte Tabellen
TABLE_PREFIX = 'loco_'

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

# PostgreSQL -> SQLite Typ-Mapping
TYPE_MAP = {
    'bigint': 'INTEGER',
    'integer': 'INTEGER',
    'smallint': 'INTEGER',
    'boolean': 'INTEGER',
    'real': 'REAL',
    'double precision': 'REAL',
    'numeric': 'REAL',
    'text': 'TEXT',
    'character varying': 'TEXT',
    'character': 'TEXT',
    'varchar': 'TEXT',
    'date': 'TEXT',
    'timestamp without time zone': 'TEXT',
    'timestamp with time zone': 'TEXT',
    'time without time zone': 'TEXT',
    'time with time zone': 'TEXT',
    'interval': 'TEXT',
    'bytea': 'BLOB',
    'json': 'TEXT',
    'jsonb': 'TEXT',
    'uuid': 'TEXT',
    'inet': 'TEXT',
    'cidr': 'TEXT',
    'macaddr': 'TEXT',
    'bit': 'TEXT',
    'bit varying': 'TEXT',
    'money': 'REAL',
    'xml': 'TEXT',
    'point': 'TEXT',
    'line': 'TEXT',
    'lseg': 'TEXT',
    'box': 'TEXT',
    'path': 'TEXT',
    'polygon': 'TEXT',
    'circle': 'TEXT',
    'ARRAY': 'TEXT',
}

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

def connect_postgres() -> psycopg2.extensions.connection:
    """Verbindung zu Locosoft PostgreSQL"""
    creds = get_locosoft_credentials()
    return psycopg2.connect(
        host=creds['host'],
        port=creds['port'],
        database=creds['database'],
        user=creds['user'],
        password=creds['password']
    )

def connect_sqlite() -> sqlite3.Connection:
    """Verbindung zu SQLite"""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=10000")
    return conn

# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def convert_value(val: Any) -> Any:
    """Konvertiert PostgreSQL-Werte fuer SQLite"""
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, timedelta):
        # timedelta als Sekunden speichern
        return val.total_seconds()
    if isinstance(val, (list, dict)):
        return json.dumps(val)
    if isinstance(val, bytes):
        return val
    return val

def get_all_tables(pg_conn) -> List[Dict]:
    """Alle Tabellen mit Zeilenanzahl aus PostgreSQL holen"""
    cursor = pg_conn.cursor()
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
        cursor.execute(f"SELECT COUNT(*) FROM {view_name}")
        row_count = cursor.fetchone()[0]
        tables.append({'name': view_name, 'rows': row_count, 'is_view': True})
        log(f"VIEW '{view_name}' hinzugefügt: {row_count:,} Zeilen")
    
    return tables

def get_table_columns(pg_conn, table_name: str) -> List[Dict]:
    """Spalten einer Tabelle mit Typen holen"""
    cursor = pg_conn.cursor()
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    return [{'name': row[0], 'type': row[1], 'nullable': row[2] == 'YES'} for row in cursor.fetchall()]

def map_pg_type_to_sqlite(pg_type: str) -> str:
    """PostgreSQL-Typ zu SQLite-Typ konvertieren"""
    pg_type_lower = pg_type.lower()
    
    # Array-Typen
    if pg_type_lower.endswith('[]') or 'array' in pg_type_lower:
        return 'TEXT'
    
    # Exaktes Mapping
    if pg_type_lower in TYPE_MAP:
        return TYPE_MAP[pg_type_lower]
    
    # Teilweise Matches
    for pg_pattern, sqlite_type in TYPE_MAP.items():
        if pg_pattern in pg_type_lower:
            return sqlite_type
    
    # Default
    return 'TEXT'

# =============================================================================
# SYNC-FUNKTIONEN
# =============================================================================

def create_sqlite_table(sqlite_conn, table_name: str, columns: List[Dict]):
    """SQLite-Tabelle erstellen (DROP + CREATE)"""
    cursor = sqlite_conn.cursor()
    sqlite_table = f"{TABLE_PREFIX}{table_name}"
    
    # Drop falls existiert
    cursor.execute(f"DROP TABLE IF EXISTS {sqlite_table}")
    
    # CREATE Statement bauen
    col_defs = []
    for col in columns:
        sqlite_type = map_pg_type_to_sqlite(col['type'])
        col_defs.append(f'"{col["name"]}" {sqlite_type}')
    
    create_sql = f'CREATE TABLE {sqlite_table} ({", ".join(col_defs)})'
    cursor.execute(create_sql)
    sqlite_conn.commit()

def sync_table(pg_conn, sqlite_conn, table_name: str, columns: List[Dict], batch_size: int = 10000) -> int:
    """Tabelle von PostgreSQL nach SQLite kopieren"""
    pg_cursor = pg_conn.cursor()
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_table = f"{TABLE_PREFIX}{table_name}"
    
    # Alle Daten lesen
    col_names = [f'"{c["name"]}"' for c in columns]
    pg_cursor.execute(f'SELECT {",".join(col_names)} FROM {table_name}')
    
    # In Batches einfuegen
    placeholders = ','.join(['?' for _ in columns])
    col_names_sqlite = [f'"{c["name"]}"' for c in columns]
    insert_sql = f'INSERT INTO {sqlite_table} ({",".join(col_names_sqlite)}) VALUES ({placeholders})'
    
    total = 0
    while True:
        rows = pg_cursor.fetchmany(batch_size)
        if not rows:
            break
        
        # Werte konvertieren
        converted_rows = []
        for row in rows:
            converted_rows.append(tuple(convert_value(val) for val in row))
        
        sqlite_cursor.executemany(insert_sql, converted_rows)
        total += len(rows)
        
        if total % 50000 == 0:
            log(f"  ... {total:,} Zeilen")
            sqlite_conn.commit()
    
    sqlite_conn.commit()
    return total

def create_indexes(sqlite_conn, table_name: str):
    """Standard-Indizes erstellen"""
    cursor = sqlite_conn.cursor()
    sqlite_table = f"{TABLE_PREFIX}{table_name}"
    
    # Typische Index-Felder
    index_candidates = [
        'id', 'document_number', 'customer_number', 'vehicle_reference',
        'accounting_date', 'document_date', 'subsidiary_to_company_ref',
        'branch_number', 'nominal_account_number', 'employee_number',
        'invoice_date', 'order_date', 'vin', 'license_plate'
    ]
    
    # Pruefen welche Spalten existieren
    cursor.execute(f"PRAGMA table_info({sqlite_table})")
    existing_cols = {row[1] for row in cursor.fetchall()}
    
    for col in index_candidates:
        if col in existing_cols:
            idx_name = f"idx_{sqlite_table}_{col}"
            try:
                cursor.execute(f'CREATE INDEX IF NOT EXISTS {idx_name} ON {sqlite_table}("{col}")')
            except Exception:
                pass  # Index existiert bereits oder Fehler - ignorieren
    
    sqlite_conn.commit()

# =============================================================================
# HAUPTFUNKTION
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Locosoft -> SQLite Mirror')
    parser.add_argument('--tables', type=str, help='Komma-separierte Liste von Tabellen')
    parser.add_argument('--min-rows', type=int, default=0, help='Nur Tabellen mit mindestens X Zeilen')
    parser.add_argument('--dry-run', action='store_true', help='Nur anzeigen, nicht syncen')
    parser.add_argument('--no-skip', action='store_true', help='Auch uebersprungene Tabellen syncen')
    args = parser.parse_args()
    
    log("=" * 60)
    log("LOCOSOFT KOMPLETT-MIRROR")
    log(f"Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)
    
    # Verbindungen
    log("Verbinde zu Locosoft PostgreSQL...")
    pg_conn = connect_postgres()
    
    log("Verbinde zu SQLite...")
    sqlite_conn = connect_sqlite()
    
    # Tabellen ermitteln
    if args.tables:
        table_names = [t.strip() for t in args.tables.split(',')]
        tables = [{'name': t, 'rows': '?'} for t in table_names]
    else:
        log("Ermittle alle Tabellen...")
        tables = get_all_tables(pg_conn)
    
    # Filtern
    if args.min_rows > 0:
        tables = [t for t in tables if t['rows'] >= args.min_rows]
    
    if not args.no_skip:
        tables = [t for t in tables if t['name'] not in SKIP_TABLES]
    
    log(f"Zu syncende Tabellen: {len(tables)}")
    
    if args.dry_run:
        log("\n=== DRY-RUN - Keine Aenderungen ===")
        total_rows = 0
        for t in tables:
            log(f"  {t['name']}: {t['rows']:,} Zeilen")
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
            columns = get_table_columns(pg_conn, table_name)
            if not columns:
                log(f"  Keine Spalten gefunden - uebersprungen")
                continue
            
            # Tabelle erstellen
            create_sqlite_table(sqlite_conn, table_name, columns)
            
            # Daten kopieren
            rows = sync_table(pg_conn, sqlite_conn, table_name, columns)
            
            # Indizes erstellen
            create_indexes(sqlite_conn, table_name)
            
            log(f"  OK: {rows:,} Zeilen")
            stats['success'] += 1
            stats['rows'] += rows
            
        except Exception as e:
            log(f"  FEHLER: {e}", "ERROR")
            errors.append(f"{table_name}: {e}")
            stats['failed'] += 1
    
    # Zusammenfassung
    log("\n" + "=" * 60)
    log("ZUSAMMENFASSUNG")
    log("=" * 60)
    log(f"Tabellen synchronisiert: {stats['success']}")
    log(f"Zeilen gesamt:           {stats['rows']:,}")
    
    if errors:
        log(f"\nFehler ({len(errors)}):", "ERROR")
        for err in errors:
            log(f"  - {err}", "ERROR")
    
    log("\nMirror abgeschlossen!")
    
    # Cleanup
    pg_conn.close()
    sqlite_conn.close()

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
