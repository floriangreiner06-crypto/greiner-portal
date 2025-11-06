#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zentrale Credentials-Verwaltung für Greiner Portal
===================================================
Lädt DB-Credentials aus verschiedenen Quellen (Priorität von oben nach unten):
1. Umgebungsvariablen (höchste Priorität)
2. .env Datei
3. config.py (falls vorhanden)
4. Hardcoded Fallback aus app.py

Usage in anderen Scripts:
    from credentials import get_locosoft_config, get_sqlite_path
    
    # PostgreSQL (LocoSoft)
    config = get_locosoft_config()
    conn = psycopg2.connect(**config)
    
    # SQLite (Greiner Portal)
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

# Projekt-Root ermitteln
PROJECT_ROOT = Path(__file__).parent
if not PROJECT_ROOT.exists():
    PROJECT_ROOT = Path.cwd()

# .env Datei laden (falls vorhanden)
ENV_FILE = PROJECT_ROOT / '.env'


def load_env_file():
    """Lädt .env Datei falls vorhanden"""
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Entferne Quotes falls vorhanden
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value


# Lade .env beim Import
load_env_file()


def get_locosoft_config() -> Dict[str, str]:
    """
    Gibt LocoSoft PostgreSQL Konfiguration zurück.
    
    Priorität:
    1. Umgebungsvariablen (LOCOSOFT_HOST, LOCOSOFT_PORT, etc.)
    2. .env Datei
    3. Hardcoded aus app.py
    
    Returns:
        Dict mit Keys: host, port, database, user, password
    """
    config = {
        'host': os.getenv('LOCOSOFT_HOST', '10.80.80.8'),
        'port': int(os.getenv('LOCOSOFT_PORT', '5432')),
        'database': os.getenv('LOCOSOFT_DATABASE', 'loco_auswertung_db'),
        'user': os.getenv('LOCOSOFT_USER', 'loco_auswertung_benutzer'),
        'password': os.getenv('LOCOSOFT_PASSWORD', 'loco')
    }
    return config


def get_sqlite_path() -> Path:
    """
    Gibt Pfad zur SQLite-Datenbank zurück.
    
    Returns:
        Path zur greiner_controlling.db
    """
    db_name = os.getenv('SQLITE_DATABASE', 'greiner_controlling.db')
    db_path = PROJECT_ROOT / db_name
    return db_path


def get_project_root() -> Path:
    """Gibt Projekt-Root-Verzeichnis zurück"""
    return PROJECT_ROOT


def get_import_folder() -> Path:
    """Gibt Stellantis-Import-Ordner zurück"""
    folder_name = os.getenv('STELLANTIS_IMPORT_FOLDER', 'stellantis_import')
    import_folder = PROJECT_ROOT / folder_name
    return import_folder


def get_backup_folder() -> Path:
    """Gibt Backup-Ordner zurück"""
    folder_name = os.getenv('BACKUP_FOLDER', 'backups')
    backup_folder = PROJECT_ROOT / folder_name
    return backup_folder


def get_flask_config() -> Dict[str, any]:
    """
    Gibt Flask-Konfiguration zurück.
    
    Returns:
        Dict mit Flask-Settings
    """
    return {
        'host': os.getenv('FLASK_HOST', '0.0.0.0'),
        'port': int(os.getenv('FLASK_PORT', '5000')),
        'debug': os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        'secret_key': os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    }


def print_config_info():
    """Zeigt aktuelle Konfiguration (Debug-Funktion)"""
    print("\n" + "="*80)
    print("🔧 AKTUELLE KONFIGURATION")
    print("="*80)
    
    print("\n📁 Projekt-Pfade:")
    print(f"   Root:           {get_project_root()}")
    print(f"   SQLite DB:      {get_sqlite_path()}")
    print(f"   Import-Ordner:  {get_import_folder()}")
    print(f"   Backup-Ordner:  {get_backup_folder()}")
    
    print("\n🐘 LocoSoft PostgreSQL:")
    config = get_locosoft_config()
    for key, value in config.items():
        if key == 'password':
            # Passwort nur teilweise zeigen
            display = value[:2] + '*' * (len(value)-4) + value[-2:] if len(value) > 4 else '****'
        else:
            display = value
        print(f"   {key:12} = {display}")
    
    print("\n🌐 Flask:")
    flask_config = get_flask_config()
    for key, value in flask_config.items():
        if key == 'secret_key':
            display = value[:10] + '...' if len(value) > 10 else value
        else:
            display = value
        print(f"   {key:12} = {display}")
    
    print("\n📄 Quelle:")
    if ENV_FILE.exists():
        print(f"   ✅ .env Datei vorhanden: {ENV_FILE}")
    else:
        print(f"   ⚠️  .env Datei nicht vorhanden (Fallback-Werte)")
        print(f"   💡 Erstelle .env Datei für bessere Konfiguration!")
    
    print("="*80)


# Für direkte Ausführung
if __name__ == '__main__':
    print_config_info()
    
    # Test DB-Verbindung
    print("\n🔍 TESTE DB-VERBINDUNGEN...")
    
    # SQLite
    print("\n1. SQLite:")
    db_path = get_sqlite_path()
    if db_path.exists():
        print(f"   ✅ Datenbank gefunden: {db_path}")
        print(f"   Größe: {db_path.stat().st_size / 1024 / 1024:.1f} MB")
    else:
        print(f"   ❌ Datenbank nicht gefunden: {db_path}")
    
    # PostgreSQL
    print("\n2. PostgreSQL (LocoSoft):")
    try:
        import psycopg2
        config = get_locosoft_config()
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   ✅ Verbindung erfolgreich!")
        print(f"   Version: {version[:50]}...")
        cursor.close()
        conn.close()
    except ImportError:
        print("   ⚠️  psycopg2 nicht installiert")
    except Exception as e:
        print(f"   ❌ Verbindungsfehler: {e}")
