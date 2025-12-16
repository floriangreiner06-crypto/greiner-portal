"""
Zentrale Datenbank-Utilities für Greiner Portal
================================================
Erstellt: TAG 117 - Code-Qualitäts-Refactoring

Diese Datei zentralisiert alle DB-Verbindungen und vermeidet:
- 11x duplizierte get_db() Funktionen
- 6x duplizierte get_locosoft_connection() Funktionen
- Connection Leaks bei Exceptions

Verwendung:
    from api.db_utils import db_session, locosoft_session, row_to_dict, rows_to_list

    # SQLite
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ...")
        data = rows_to_list(cursor.fetchall())
    # Connection wird automatisch geschlossen!

    # PostgreSQL (Locosoft)
    with locosoft_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ...")
"""

import sqlite3
import os
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# =============================================================================
# KONFIGURATION
# =============================================================================

# SQLite Pfad - nutzt Environment oder Fallback
SQLITE_DB_PATH = os.getenv(
    'SQLITE_DB_PATH',
    '/opt/greiner-portal/data/greiner_controlling.db'
)

# Für lokale Entwicklung (Windows)
if os.name == 'nt' and not os.path.exists(SQLITE_DB_PATH):
    # Relativer Pfad für Windows-Entwicklung
    _base = os.path.dirname(os.path.dirname(__file__))
    SQLITE_DB_PATH = os.path.join(_base, 'data', 'greiner_controlling.db')


# =============================================================================
# SQLITE VERBINDUNGEN
# =============================================================================

def get_db() -> sqlite3.Connection:
    """
    Erstellt SQLite-Verbindung mit row_factory.

    WARNUNG: Bevorzuge db_session() Context Manager für automatisches Cleanup!

    Returns:
        sqlite3.Connection mit Row-Factory
    """
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_session():
    """
    Context Manager für sichere SQLite-Verbindung.

    Schließt Connection automatisch, auch bei Exceptions.

    Usage:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            data = cursor.fetchall()
        # Connection ist hier garantiert geschlossen

    Yields:
        sqlite3.Connection mit Row-Factory
    """
    conn = None
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        if conn:
            conn.close()


# =============================================================================
# POSTGRESQL (LOCOSOFT) VERBINDUNGEN
# =============================================================================

def get_locosoft_connection():
    """
    Erstellt PostgreSQL-Verbindung zu Locosoft.

    WARNUNG: Bevorzuge locosoft_session() Context Manager für automatisches Cleanup!

    Liest Credentials aus /opt/greiner-portal/config/.env

    Returns:
        psycopg2.connection

    Raises:
        FileNotFoundError: Wenn .env nicht gefunden
        KeyError: Wenn Credentials fehlen
        psycopg2.OperationalError: Bei Verbindungsfehler
    """
    import psycopg2

    # .env Pfad ermitteln
    env_path = os.getenv('GREINER_ENV_PATH', '/opt/greiner-portal/config/.env')

    # Für lokale Entwicklung
    if os.name == 'nt' or not os.path.exists(env_path):
        _base = os.path.dirname(os.path.dirname(__file__))
        env_path = os.path.join(_base, 'config', '.env')

    if not os.path.exists(env_path):
        raise FileNotFoundError(f".env nicht gefunden: {env_path}")

    # .env parsen
    env = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip()

    # Pflichtfelder prüfen
    required = ['LOCOSOFT_HOST', 'LOCOSOFT_PORT', 'LOCOSOFT_DATABASE',
                'LOCOSOFT_USER', 'LOCOSOFT_PASSWORD']
    missing = [k for k in required if k not in env]
    if missing:
        raise KeyError(f"Fehlende .env Einträge: {missing}")

    return psycopg2.connect(
        host=env['LOCOSOFT_HOST'],
        port=int(env['LOCOSOFT_PORT']),
        database=env['LOCOSOFT_DATABASE'],
        user=env['LOCOSOFT_USER'],
        password=env['LOCOSOFT_PASSWORD'],
        connect_timeout=10,  # Timeout bei Netzwerkproblemen
        options='-c statement_timeout=60000'  # 60s Query-Timeout
    )


@contextmanager
def locosoft_session():
    """
    Context Manager für sichere Locosoft PostgreSQL-Verbindung.

    Schließt Connection automatisch, auch bei Exceptions.

    Usage:
        with locosoft_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM mitarbeiter")
            data = cursor.fetchall()
        # Connection ist hier garantiert geschlossen

    Yields:
        psycopg2.connection
    """
    conn = None
    try:
        conn = get_locosoft_connection()
        yield conn
    finally:
        if conn:
            conn.close()


# =============================================================================
# ROW CONVERTER UTILITIES
# =============================================================================

def row_to_dict(row: sqlite3.Row) -> Optional[Dict[str, Any]]:
    """
    Konvertiert sqlite3.Row zu Dictionary.

    Args:
        row: sqlite3.Row Objekt oder None

    Returns:
        Dictionary mit Spalten als Keys, oder None wenn row None ist
    """
    return dict(row) if row else None


def rows_to_list(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    """
    Konvertiert Liste von sqlite3.Row zu Liste von Dictionaries.

    Args:
        rows: Liste von sqlite3.Row Objekten

    Returns:
        Liste von Dictionaries
    """
    return [dict(row) for row in rows] if rows else []


# =============================================================================
# QUERY HELPERS
# =============================================================================

def execute_query(query: str, params: tuple = (), fetchone: bool = False) -> Any:
    """
    Führt SELECT-Query aus und gibt Ergebnis zurück.

    Convenience-Funktion für einfache Queries.

    Args:
        query: SQL Query String
        params: Query-Parameter (Tuple)
        fetchone: True für einzelnes Ergebnis, False für Liste

    Returns:
        Dict (fetchone=True) oder List[Dict] (fetchone=False)
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetchone:
            return row_to_dict(cursor.fetchone())
        return rows_to_list(cursor.fetchall())


def execute_write(query: str, params: tuple = ()) -> int:
    """
    Führt INSERT/UPDATE/DELETE aus und committed.

    Args:
        query: SQL Query String
        params: Query-Parameter (Tuple)

    Returns:
        Anzahl betroffener Zeilen (rowcount)
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount
