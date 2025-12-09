#!/usr/bin/env python3
"""
Export aktuelles Datenbank-Schema als Markdown.

Verwendung:
    python3 export_db_schema.py > docs/DB_SCHEMA_AKTUELL.md
    
Oder mit Locosoft:
    python3 export_db_schema.py --locosoft > docs/DB_SCHEMA_LOCOSOFT.md
    
Oder beides:
    python3 export_db_schema.py --all
"""

import sqlite3
import psycopg2
import os
import sys
from datetime import datetime
from pathlib import Path

# Pfade
SQLITE_DB = "/opt/greiner-portal/data/greiner_controlling.db"
DOCS_DIR = "/opt/greiner-portal/docs"

# Locosoft Credentials aus .env
def get_locosoft_config():
    env_path = "/opt/greiner-portal/config/.env"
    config = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value.strip('"').strip("'")
    return {
        'host': config.get('LOCOSOFT_HOST', '10.80.80.8'),
        'port': config.get('LOCOSOFT_PORT', '5432'),
        'database': config.get('LOCOSOFT_DB', 'loco_auswertung_db'),
        'user': config.get('LOCOSOFT_USER', 'loco_auswertung_benutzer'),
        'password': config.get('LOCOSOFT_PASSWORD', '')
    }


def export_sqlite_schema():
    """Exportiert SQLite Schema als Markdown."""
    
    output = []
    output.append("# 🗄️ SQLITE DATENBANK-SCHEMA (AUTO-GENERIERT)")
    output.append("")
    output.append(f"**Generiert:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append(f"**Datenbank:** `{SQLITE_DB}`")
    output.append("")
    output.append("⚠️ **Diese Datei wird automatisch generiert - nicht manuell editieren!**")
    output.append("")
    output.append("---")
    output.append("")
    
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    
    # Alle Tabellen holen
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [row[0] for row in c.fetchall()]
    
    # Übersicht
    output.append("## 📋 TABELLEN-ÜBERSICHT")
    output.append("")
    output.append(f"**Anzahl Tabellen:** {len(tables)}")
    output.append("")
    output.append("| Tabelle | Spalten | Zeilen |")
    output.append("|---------|---------|--------|")
    
    table_info = {}
    for table in tables:
        c.execute(f"PRAGMA table_info({table})")
        columns = c.fetchall()
        c.execute(f"SELECT COUNT(*) FROM {table}")
        count = c.fetchone()[0]
        table_info[table] = {'columns': columns, 'count': count}
        output.append(f"| `{table}` | {len(columns)} | {count:,} |")
    
    output.append("")
    output.append("---")
    output.append("")
    
    # Detail pro Tabelle
    output.append("## 📊 TABELLEN-DETAILS")
    output.append("")
    
    for table in tables:
        info = table_info[table]
        output.append(f"### `{table}` ({info['count']:,} Zeilen)")
        output.append("")
        output.append("| Spalte | Typ | NotNull | Default | PK |")
        output.append("|--------|-----|---------|---------|-----|")
        
        for col in info['columns']:
            cid, name, dtype, notnull, default, pk = col
            notnull_str = "✓" if notnull else ""
            pk_str = "🔑" if pk else ""
            default_str = str(default) if default else ""
            output.append(f"| `{name}` | {dtype or 'TEXT'} | {notnull_str} | {default_str} | {pk_str} |")
        
        # Indizes
        c.execute(f"PRAGMA index_list({table})")
        indexes = c.fetchall()
        if indexes:
            output.append("")
            output.append("**Indizes:**")
            for idx in indexes:
                idx_name = idx[1]
                c.execute(f"PRAGMA index_info({idx_name})")
                idx_cols = [row[2] for row in c.fetchall()]
                output.append(f"- `{idx_name}`: {', '.join(idx_cols)}")
        
        output.append("")
    
    # Views
    c.execute("SELECT name, sql FROM sqlite_master WHERE type='view' ORDER BY name")
    views = c.fetchall()
    
    if views:
        output.append("---")
        output.append("")
        output.append("## 👁️ VIEWS")
        output.append("")
        for view_name, view_sql in views:
            output.append(f"### `{view_name}`")
            output.append("")
            output.append("```sql")
            output.append(view_sql or "-- SQL nicht verfügbar")
            output.append("```")
            output.append("")
    
    conn.close()
    return "\n".join(output)


def export_locosoft_schema():
    """Exportiert Locosoft PostgreSQL Schema als Markdown."""
    
    output = []
    output.append("# 🐘 LOCOSOFT POSTGRESQL-SCHEMA (AUTO-GENERIERT)")
    output.append("")
    output.append(f"**Generiert:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("")
    output.append("⚠️ **Diese Datei wird automatisch generiert - nicht manuell editieren!**")
    output.append("")
    output.append("---")
    output.append("")
    
    try:
        config = get_locosoft_config()
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        c = conn.cursor()
        
        # Alle Tabellen im public Schema
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row[0] for row in c.fetchall()]
        
        output.append("## 📋 TABELLEN-ÜBERSICHT")
        output.append("")
        output.append(f"**Anzahl Tabellen:** {len(tables)}")
        output.append("")
        output.append("| Tabelle | Spalten | Zeilen (ca.) |")
        output.append("|---------|---------|--------------|")
        
        table_info = {}
        for table in tables:
            # Spalten
            c.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """, (table,))
            columns = c.fetchall()
            
            # Zeilenanzahl (Schätzung für Performance)
            try:
                c.execute(f"SELECT reltuples::bigint FROM pg_class WHERE relname = %s", (table,))
                count = c.fetchone()[0] or 0
            except:
                count = 0
            
            table_info[table] = {'columns': columns, 'count': count}
            output.append(f"| `{table}` | {len(columns)} | {int(count):,} |")
        
        output.append("")
        output.append("---")
        output.append("")
        
        # Detail pro Tabelle
        output.append("## 📊 TABELLEN-DETAILS")
        output.append("")
        
        for table in tables:
            info = table_info[table]
            output.append(f"### `{table}` (~{int(info['count']):,} Zeilen)")
            output.append("")
            output.append("| Spalte | Typ | Nullable | Default |")
            output.append("|--------|-----|----------|---------|")
            
            for col in info['columns']:
                name, dtype, nullable, default = col
                nullable_str = "" if nullable == 'YES' else "NOT NULL"
                default_str = str(default)[:30] if default else ""
                output.append(f"| `{name}` | {dtype} | {nullable_str} | {default_str} |")
            
            output.append("")
        
        conn.close()
        
    except Exception as e:
        output.append(f"❌ **Fehler bei Locosoft-Verbindung:** {e}")
        output.append("")
        output.append("Prüfe:")
        output.append("- VPN-Verbindung")
        output.append("- Credentials in `/opt/greiner-portal/config/.env`")
    
    return "\n".join(output)


def main():
    args = sys.argv[1:]
    
    if '--help' in args or '-h' in args:
        print(__doc__)
        return
    
    # Verzeichnis erstellen falls nötig
    Path(DOCS_DIR).mkdir(parents=True, exist_ok=True)
    
    if '--locosoft' in args:
        # Nur Locosoft
        schema = export_locosoft_schema()
        print(schema)
        
    elif '--all' in args:
        # Beide in separate Dateien
        sqlite_schema = export_sqlite_schema()
        with open(f"{DOCS_DIR}/DB_SCHEMA_SQLITE.md", 'w') as f:
            f.write(sqlite_schema)
        print(f"✅ SQLite Schema exportiert: {DOCS_DIR}/DB_SCHEMA_SQLITE.md")
        
        locosoft_schema = export_locosoft_schema()
        with open(f"{DOCS_DIR}/DB_SCHEMA_LOCOSOFT.md", 'w') as f:
            f.write(locosoft_schema)
        print(f"✅ Locosoft Schema exportiert: {DOCS_DIR}/DB_SCHEMA_LOCOSOFT.md")
        
    else:
        # Default: nur SQLite
        schema = export_sqlite_schema()
        print(schema)


if __name__ == "__main__":
    main()
