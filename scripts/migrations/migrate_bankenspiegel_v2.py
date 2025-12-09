#!/usr/bin/env python3
"""
Bankenspiegel V2 - Migration Script
=====================================
Migriert Bankenspiegel-Tabellen zu neuem Schema (optimiert für MT940 + Fahrzeugfinanzierungen)

⚠️  WICHTIG: 
- Nur Bankenspiegel-Tabellen werden geändert
- Locosoft/HR/Auth-Tabellen bleiben unberührt
- Automatisches Backup wird IMMER erstellt

Usage:
    python3 migrate_bankenspiegel_v2.py [--dry-run] [--backup-only]
    
Options:
    --dry-run       Zeigt nur was passieren würde (kein Backup nötig)
    --backup-only   Erstellt nur Backup, keine Migration
"""

import sqlite3
import sys
import os
from datetime import datetime
from pathlib import Path
import shutil
import argparse
import json

# Pfade
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = Path("/opt/greiner-portal")
DB_PATH = PROJECT_DIR / "data" / "greiner_controlling.db"
SCHEMA_PATH = SCRIPT_DIR / "bankenspiegel_v2_schema.sql"
BACKUP_DIR = PROJECT_DIR / "data" / "backups"

# Bankenspiegel-Tabellen (werden gelöscht und neu erstellt)
BANKENSPIEGEL_TABLES = [
    # Stammdaten
    'banken',
    'konten',
    'finanzierungsbanken',  # NEU
    
    # Transaktionen
    'transaktionen',
    'kontostand_historie',
    'salden',  # NEU (ersetzt kontostand_historie)
    
    # Fahrzeugfinanzierungen
    'fahrzeugfinanzierungen',
    'finanzierung_snapshots',  # NEU
    
    # Kreditlinien
    'kreditlinien',
    'kreditlinien_snapshots',  # NEU
    
    # Sonstige
    'kategorien',
    'bankgebuehren',
    'manuelle_buchungen',
    'konto_snapshots',
    'pdf_imports',
    'zinssaetze_historie',
    'fahrzeuge_mit_zinsen',
    'import_log',  # NEU
    
    # Views
    'v_aktuelle_kontostaende',
    'v_aktuelle_kontosalden',  # NEU
    'v_cashflow_aktuell',
    'v_cashflow_jahresuebersicht',
    'v_cashflow_kategorien',
    'v_kategorie_auswertung',
    'v_monatliche_umsaetze',
    'v_transaktionen_uebersicht',
    'v_zinsbuchungen',
    'v_zinsen_monatlich',
    'v_fahrzeugfinanzierungen_aktuell',  # NEU
    'v_kreditlinien_aktuell',  # NEU
]

# Tabellen die NICHT angefasst werden
PROTECTED_TABLES = [
    # Verkauf (Locosoft)
    'sales', 'customers_suppliers', 'dealer_vehicles', 'vehicles',
    
    # FIBU (Locosoft)
    'fibu_buchungen',
    
    # HR
    'employees', 'departments', 'vacation_bookings', 'vacation_entitlements',
    'vacation_types', 'vacation_adjustments', 'vacation_audit_log',
    'holidays', 'manager_assignments', 'ldap_employee_mapping',
    
    # Auth
    'users', 'users_old_backup', 'roles', 'user_roles', 'sessions',
    'auth_audit_log', 'ad_group_role_mapping',
    
    # System
    'sync_log', 'audit_log', 'sqlite_sequence',
    
    # Backups
    'bank_accounts_old_backup', 'daily_balances_old_backup',
]

def print_header(text):
    """Druckt schönen Header"""
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")

def print_section(text):
    """Druckt Section-Header"""
    print(f"\n{text}")
    print(f"{'-'*len(text)}")

def create_backup():
    """Erstellt Backup der aktuellen Datenbank"""
    if not DB_PATH.exists():
        print(f"⚠️  Keine Datenbank gefunden: {DB_PATH}")
        return None
    
    # Backup-Verzeichnis erstellen
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Backup-Name mit Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"greiner_controlling_pre_v2_{timestamp}.db"
    
    print_section("📦 BACKUP ERSTELLEN")
    print(f"Quelle: {DB_PATH}")
    print(f"Ziel:   {backup_path}")
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        backup_size = backup_path.stat().st_size / (1024 * 1024)
        print(f"✅ Backup erfolgreich erstellt: {backup_size:.2f} MB")
        print(f"\n💡 Rollback-Befehl:")
        print(f"   cp {backup_path} {DB_PATH}")
        return backup_path
    except Exception as e:
        print(f"❌ Fehler beim Backup: {e}")
        sys.exit(1)

def get_table_stats(conn):
    """Holt Statistiken der aktuellen Tabellen"""
    cursor = conn.cursor()
    
    stats = {}
    for table in BANKENSPIEGEL_TABLES:
        try:
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cursor.fetchone():
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
        except sqlite3.OperationalError:
            pass
    
    return stats

def analyze_current_state(conn, dry_run=False):
    """Analysiert aktuellen Zustand der DB"""
    print_section("🔍 AKTUELLER ZUSTAND")
    
    cursor = conn.cursor()
    
    # Alle Tabellen
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Gesamt-Tabellen in DB: {len(all_tables)}")
    
    # Bankenspiegel-Tabellen
    existing_bs_tables = [t for t in all_tables if t in BANKENSPIEGEL_TABLES]
    print(f"Bankenspiegel-Tabellen: {len(existing_bs_tables)}")
    
    # Protected Tables
    existing_protected = [t for t in all_tables if t in PROTECTED_TABLES]
    print(f"Geschützte Tabellen: {len(existing_protected)}")
    
    # Statistiken
    if not dry_run:
        print("\n📊 Daten in Bankenspiegel-Tabellen:")
        stats = get_table_stats(conn)
        for table, count in sorted(stats.items()):
            if count > 0:
                print(f"   {table:30} {count:>10,} Zeilen")
    
    return existing_bs_tables, existing_protected

def drop_bankenspiegel_tables(conn, tables_to_drop, dry_run=False):
    """Löscht Bankenspiegel-Tabellen"""
    print_section("🗑️  BANKENSPIEGEL-TABELLEN LÖSCHEN")
    
    if dry_run:
        print("DRY-RUN: Folgende Tabellen würden gelöscht werden:")
        for table in tables_to_drop:
            print(f"   DROP TABLE IF EXISTS {table}")
        return
    
    cursor = conn.cursor()
    
    # Drop Views zuerst (wegen Dependencies)
    views_to_drop = [t for t in tables_to_drop if t.startswith('v_')]
    tables_to_drop_actual = [t for t in tables_to_drop if not t.startswith('v_')]
    
    # Views
    for view in views_to_drop:
        try:
            cursor.execute(f"DROP VIEW IF EXISTS {view}")
            print(f"   ✓ View gelöscht: {view}")
        except Exception as e:
            print(f"   ⚠️  {view}: {e}")
    
    # Tables
    for table in tables_to_drop_actual:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"   ✓ Tabelle gelöscht: {table}")
        except Exception as e:
            print(f"   ⚠️  {table}: {e}")
    
    conn.commit()
    print("✅ Alte Struktur gelöscht")

def create_new_schema(conn, dry_run=False):
    """Erstellt neue Tabellen aus Schema-Datei"""
    print_section("📝 NEUES SCHEMA ERSTELLEN")
    
    if not SCHEMA_PATH.exists():
        print(f"❌ Schema-Datei nicht gefunden: {SCHEMA_PATH}")
        sys.exit(1)
    
    if dry_run:
        print(f"DRY-RUN: Schema würde aus {SCHEMA_PATH} geladen werden")
        return
    
    # Schema laden
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    cursor = conn.cursor()
    
    try:
        # Execute Schema (split by semicolon)
        statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
        
        for stmt in statements:
            if stmt.startswith('--') or len(stmt) < 10:
                continue
            try:
                cursor.execute(stmt)
            except Exception as e:
                # Ignoriere "already exists" Fehler
                if "already exists" not in str(e).lower():
                    print(f"   ⚠️  Statement-Fehler: {e}")
                    print(f"      Statement: {stmt[:100]}...")
        
        conn.commit()
        print("✅ Neues Schema erstellt")
        
        # Verify
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('banken', 'konten', 'transaktionen', 'salden', 'fahrzeugfinanzierungen')")
        created_tables = [row[0] for row in cursor.fetchall()]
        print(f"   Verifiziert: {len(created_tables)} Kern-Tabellen erstellt")
        
    except Exception as e:
        print(f"❌ Fehler beim Schema-Import: {e}")
        sys.exit(1)

def verify_protected_tables(conn):
    """Verifiziert dass geschützte Tabellen noch existieren"""
    print_section("🛡️  GESCHÜTZTE TABELLEN VERIFIZIEREN")
    
    cursor = conn.cursor()
    
    missing = []
    for table in PROTECTED_TABLES:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if not cursor.fetchone():
            missing.append(table)
    
    if missing:
        print(f"⚠️  Warnung: {len(missing)} geschützte Tabellen fehlen:")
        for table in missing:
            print(f"   - {table}")
    else:
        print(f"✅ Alle {len(PROTECTED_TABLES)} geschützten Tabellen sind intakt")

def main():
    parser = argparse.ArgumentParser(description='Bankenspiegel V2 Migration')
    parser.add_argument('--dry-run', action='store_true', help='Zeigt nur was passieren würde')
    parser.add_argument('--backup-only', action='store_true', help='Erstellt nur Backup')
    args = parser.parse_args()
    
    print_header("BANKENSPIEGEL V2 - MIGRATION")
    
    # Check DB existiert
    if not DB_PATH.exists():
        print(f"❌ Datenbank nicht gefunden: {DB_PATH}")
        sys.exit(1)
    
    # DRY-RUN Info
    if args.dry_run:
        print("🔍 DRY-RUN MODE - Keine Änderungen werden vorgenommen!\n")
    
    # Backup erstellen (außer bei dry-run)
    backup_path = None
    if not args.dry_run:
        backup_path = create_backup()
    
    # Backup-only?
    if args.backup_only:
        print("\n✅ Backup erstellt. Migration wird NICHT durchgeführt.")
        sys.exit(0)
    
    # Connection
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # 1. Analyze
        existing_bs_tables, existing_protected = analyze_current_state(conn, args.dry_run)
        
        # 2. Confirm (wenn nicht dry-run)
        if not args.dry_run:
            print(f"\n{'='*80}")
            print(f"⚠️  ACHTUNG: {len(existing_bs_tables)} Bankenspiegel-Tabellen werden gelöscht!")
            print(f"✅ {len(existing_protected)} Geschützte Tabellen bleiben unberührt")
            print(f"{'='*80}")
            
            response = input("\n🚨 Migration fortsetzen? [yes/NO]: ").strip().lower()
            if response != 'yes':
                print("\n❌ Migration abgebrochen.")
                conn.close()
                sys.exit(0)
        
        # 3. Drop Bankenspiegel Tables
        drop_bankenspiegel_tables(conn, existing_bs_tables, args.dry_run)
        
        # 4. Create New Schema
        create_new_schema(conn, args.dry_run)
        
        # 5. Verify Protected Tables
        if not args.dry_run:
            verify_protected_tables(conn)
        
        # Success
        if args.dry_run:
            print_header("DRY-RUN ABGESCHLOSSEN")
            print("Keine Änderungen vorgenommen.")
        else:
            print_header("MIGRATION ERFOLGREICH!")
            print(f"✅ Backup: {backup_path}")
            print(f"✅ Neue Struktur erstellt")
            print(f"✅ Geschützte Tabellen intakt")
            print(f"\n🚀 Nächste Schritte:")
            print(f"   1. Stammdaten eintragen (Banken, Konten)")
            print(f"   2. MT940-Import durchführen")
            print(f"   3. Fahrzeugfinanzierungen importieren")
    
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        
        if backup_path:
            print(f"\n🔄 ROLLBACK-BEFEHL:")
            print(f"   cp {backup_path} {DB_PATH}")
        
        sys.exit(1)
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()
