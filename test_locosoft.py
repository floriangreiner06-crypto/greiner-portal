#!/usr/bin/env python3
"""
============================================================================
LOCOSOFT VERBINDUNGSTEST (mit .env Support)
============================================================================
Erstellt: 06.11.2025
Zweck: Teste Verbindung zu Locosoft PostgreSQL
Server: 10.80.80.8:5432
Liest Credentials automatisch aus config/.env
============================================================================
"""

import sys
import os
import psycopg2
from pathlib import Path

def log(message, level="INFO"):
    """Simple logging"""
    print(f"[{level:5}] {message}")

def load_env_file(env_path='config/.env'):
    """Liest .env Datei und gibt Dictionary zurück"""
    env_vars = {}
    
    if not Path(env_path).exists():
        log(f"⚠️  .env Datei nicht gefunden: {env_path}", "WARN")
        return env_vars
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Kommentare und leere Zeilen überspringen
            if not line or line.startswith('#'):
                continue
            # Key=Value splitten
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars

def test_locosoft_connection():
    """Teste Verbindung zu Locosoft PostgreSQL"""
    
    log("=" * 70)
    log("LOCOSOFT VERBINDUNGSTEST")
    log("=" * 70)
    log("")
    
    # .env Datei laden
    log("Lade Credentials aus config/.env...")
    env = load_env_file('config/.env')
    
    if not env:
        log("❌ Keine .env Datei gefunden!", "ERROR")
        return False
    
    log("✅ .env Datei geladen")
    log("")
    
    # Locosoft Credentials aus .env
    LOCOSOFT_CONFIG = {
        'host': env.get('LOCOSOFT_HOST', '10.80.80.8'),
        'port': int(env.get('LOCOSOFT_PORT', 5432)),
        'database': env.get('LOCOSOFT_DATABASE', 'loco_auswertung_db'),
        'user': env.get('LOCOSOFT_USER', 'loco_auswertung_benutzer'),
        'password': env.get('LOCOSOFT_PASSWORD', '')
    }
    
    if not LOCOSOFT_CONFIG['password']:
        log("❌ Kein Passwort in .env gefunden!", "ERROR")
        log("   Füge hinzu: LOCOSOFT_PASSWORD=...", "ERROR")
        return False
    
    log("Verbindungsparameter:")
    log(f"  Host:     {LOCOSOFT_CONFIG['host']}")
    log(f"  Port:     {LOCOSOFT_CONFIG['port']}")
    log(f"  Database: {LOCOSOFT_CONFIG['database']}")
    log(f"  User:     {LOCOSOFT_CONFIG['user']}")
    log(f"  Password: {'*' * len(LOCOSOFT_CONFIG['password'])}")
    log("")
    
    try:
        log("Verbinde zu Locosoft PostgreSQL...")
        
        conn = psycopg2.connect(
            host=LOCOSOFT_CONFIG['host'],
            port=LOCOSOFT_CONFIG['port'],
            database=LOCOSOFT_CONFIG['database'],
            user=LOCOSOFT_CONFIG['user'],
            password=LOCOSOFT_CONFIG['password'],
            connect_timeout=10
        )
        
        log("✅ Verbindung erfolgreich!", "SUCCESS")
        log("")
        
        # Test-Query
        cursor = conn.cursor()
        
        # PostgreSQL Version
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        log(f"PostgreSQL Version:")
        log(f"  {version[:80]}...")
        log("")
        
        # Verfügbare Tabellen prüfen
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        log(f"Verfügbare Tabellen: {len(tables)}")
        log("")
        
        # Suche nach Mitarbeiter-Tabellen
        employee_tables = [
            t[0] for t in tables 
            if any(keyword in t[0].lower() for keyword in ['employee', 'mitarbeiter', 'personal', 'staff'])
        ]
        
        if employee_tables:
            log("🎯 MITARBEITER-TABELLEN GEFUNDEN:")
            log("")
            for table in employee_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    log(f"  📋 {table}: {count} Einträge")
                    
                    # Spalten anzeigen
                    cursor.execute(f"""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = '{table}'
                        ORDER BY ordinal_position
                        LIMIT 10
                    """)
                    columns = cursor.fetchall()
                    log(f"     Spalten:")
                    for col_name, col_type in columns:
                        log(f"       • {col_name} ({col_type})")
                    log("")
                except Exception as e:
                    log(f"  ⚠️  {table}: Fehler beim Lesen - {e}")
        else:
            log("⚠️  Keine offensichtliche Mitarbeiter-Tabelle gefunden")
            log("")
            log("📋 Alle verfügbaren Tabellen (erste 30):")
            for i, table in enumerate(tables[:30], 1):
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    log(f"  {i:2}. {table[0]:40} ({count:6} Einträge)")
                except:
                    log(f"  {i:2}. {table[0]:40} (Fehler)")
        
        log("")
        log("=" * 70)
        log("✅ TEST ERFOLGREICH!", "SUCCESS")
        log("=" * 70)
        log("")
        log("NÄCHSTE SCHRITTE:")
        log("  1. Mitarbeiter-Tabelle identifiziert?")
        log("  2. Wichtige Spalten notiert?")
        log("  3. Weiter mit Mitarbeiter-Sync-Script")
        log("")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        log("", "ERROR")
        log("❌ VERBINDUNGSFEHLER!", "ERROR")
        log("", "ERROR")
        log(f"Fehler: {e}", "ERROR")
        log("", "ERROR")
        log("Mögliche Ursachen:", "ERROR")
        log("  1. Falsches Passwort", "ERROR")
        log("  2. Server nicht erreichbar (10.80.80.8)", "ERROR")
        log("  3. Firewall blockiert Port 5432", "ERROR")
        log("  4. PostgreSQL-Service läuft nicht", "ERROR")
        log("", "ERROR")
        return False
        
    except Exception as e:
        log("", "ERROR")
        log(f"❌ Unerwarteter Fehler: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    log("Prüfe psycopg2...")
    try:
        import psycopg2
        log("✅ psycopg2 ist installiert")
        log("")
    except ImportError:
        log("❌ psycopg2 fehlt!", "ERROR")
        log("Installation: pip install psycopg2-binary", "ERROR")
        log("")
        sys.exit(1)
    
    success = test_locosoft_connection()
    sys.exit(0 if success else 1)
