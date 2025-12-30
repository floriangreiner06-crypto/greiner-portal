"""
Database Connection Layer - SQLite/PostgreSQL Dual-Mode
========================================================
TAG 135: PostgreSQL-Migration mit Rollback-Möglichkeit

Konfiguration via Environment-Variablen oder .env:
    DB_TYPE=sqlite|postgresql  (default: sqlite)
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=drive_portal
    DB_USER=drive_user
    DB_PASSWORD=xxx

Verwendung:
    from api.db_connection import get_db, get_db_type

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees")
    rows = cursor.fetchall()
    conn.close()

Rollback:
    1. In .env: DB_TYPE=sqlite setzen
    2. Service neustarten
    3. Fertig - alle Queries gehen wieder an SQLite
"""

import os
import sqlite3
from typing import Optional, Any
from contextlib import contextmanager

# Versuche psycopg2 zu importieren (optional)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, NamedTupleCursor
    import psycopg2.extensions
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


# =============================================================================
# HYBRID ROW - Unterstützt Index UND Dict Zugriff (TAG 139)
# =============================================================================

class HybridRow:
    """
    Row-Klasse die sowohl Index-Zugriff (row[0]) als auch Dict-Zugriff (row['name']) unterstützt.
    Löst das Problem unterschiedlicher Zugriffsmuster im Code.
    """
    __slots__ = ('_values', '_keys')

    def __init__(self, values, keys):
        object.__setattr__(self, '_values', tuple(values))
        object.__setattr__(self, '_keys', tuple(keys))

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        elif isinstance(key, str):
            try:
                idx = self._keys.index(key)
                return self._values[idx]
            except ValueError:
                raise KeyError(key)
        raise TypeError(f"Invalid key type: {type(key)}")

    def __len__(self):
        return len(self._values)

    def __iter__(self):
        return iter(self._values)

    def get(self, key, default=None):
        try:
            return self[key]
        except (KeyError, IndexError):
            return default

    def keys(self):
        return self._keys

    def values(self):
        return self._values

    def items(self):
        return zip(self._keys, self._values)

    def __repr__(self):
        return f"HybridRow({dict(zip(self._keys, self._values))})"


class HybridCursor:
    """
    Wrapper-Cursor der HybridRow zurückgibt statt Tuple.
    Unterstützt sowohl Index als auch Dict Zugriff.
    """
    def __init__(self, cursor):
        self._cursor = cursor
        self._description = None

    def execute(self, query, params=None):
        result = self._cursor.execute(query, params)
        self._description = self._cursor.description
        return result

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        keys = [desc[0] for desc in self._description] if self._description else []
        return HybridRow(row, keys)

    def fetchall(self):
        rows = self._cursor.fetchall()
        if not rows:
            return []
        keys = [desc[0] for desc in self._description] if self._description else []
        return [HybridRow(row, keys) for row in rows]

    def fetchmany(self, size=None):
        rows = self._cursor.fetchmany(size)
        if not rows:
            return []
        keys = [desc[0] for desc in self._description] if self._description else []
        return [HybridRow(row, keys) for row in rows]

    @property
    def description(self):
        return self._cursor.description

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return getattr(self._cursor, 'lastrowid', None)

    def close(self):
        return self._cursor.close()

    def __iter__(self):
        return iter(self.fetchall())


class HybridConnection:
    """
    Wrapper-Connection der automatisch HybridCursor zurückgibt.
    """
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return HybridCursor(self._conn.cursor())

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

# =============================================================================
# KONFIGURATION
# =============================================================================

# Defaults
SQLITE_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
SQLITE_PATH_LOCAL = os.path.join(os.path.dirname(__file__), '..', 'data', 'greiner_controlling.db')

# Environment-Variablen laden (falls dotenv verfügbar)
try:
    from dotenv import load_dotenv
    load_dotenv('/opt/greiner-portal/config/.env')
except ImportError:
    pass

# Konfiguration aus Environment
DB_TYPE = os.getenv('DB_TYPE', 'sqlite').lower()
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME', 'drive_portal')
DB_USER = os.getenv('DB_USER', 'drive_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')


# =============================================================================
# SQLITE ROW FACTORY (Dict-like access)
# =============================================================================

class SQLiteRow(sqlite3.Row):
    """Erweiterte Row-Klasse für dict-ähnlichen Zugriff"""
    def get(self, key, default=None):
        try:
            return self[key]
        except (IndexError, KeyError):
            return default


def dict_factory(cursor, row):
    """Factory für dict-Rückgabe bei SQLite"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


# =============================================================================
# HAUPTFUNKTIONEN
# =============================================================================

def get_db_type() -> str:
    """Aktuellen Datenbank-Typ zurückgeben"""
    return DB_TYPE


def get_db(use_dict_cursor: bool = True):
    """
    Datenbank-Verbindung holen (SQLite oder PostgreSQL).

    Args:
        use_dict_cursor: Bei True werden Rows als Dict zurückgegeben

    Returns:
        Connection-Objekt (sqlite3.Connection oder psycopg2.connection)
    """
    if DB_TYPE == 'postgresql':
        return _get_postgresql_connection(use_dict_cursor)
    else:
        return _get_sqlite_connection(use_dict_cursor)


def _get_sqlite_connection(use_dict_cursor: bool = True):
    """SQLite-Verbindung herstellen"""
    # Prüfe verschiedene Pfade
    db_path = SQLITE_PATH
    if not os.path.exists(db_path):
        if os.path.exists(SQLITE_PATH_LOCAL):
            db_path = SQLITE_PATH_LOCAL

    conn = sqlite3.connect(db_path)

    if use_dict_cursor:
        conn.row_factory = sqlite3.Row

    return conn


def _get_postgresql_connection(use_dict_cursor: bool = True):
    """PostgreSQL-Verbindung herstellen"""
    if not PSYCOPG2_AVAILABLE:
        raise ImportError(
            "psycopg2 nicht installiert. "
            "Bitte 'pip install psycopg2-binary' ausführen oder DB_TYPE=sqlite setzen."
        )

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    # TAG 139: HybridConnection wrappen für Index UND Dict Zugriff
    # HybridRow unterstützt: row[0] (Index) UND row['name'] (Dict)
    return HybridConnection(conn)


@contextmanager
def get_db_context(use_dict_cursor: bool = True):
    """
    Context Manager für automatisches Connection-Handling.

    Verwendung:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
        # Connection wird automatisch geschlossen
    """
    conn = get_db(use_dict_cursor)
    try:
        yield conn
    finally:
        conn.close()


# =============================================================================
# SQL COMPATIBILITY HELPERS
# =============================================================================

def sql_now() -> str:
    """
    Gibt das aktuelle Datum/Zeit SQL-Fragment zurück.
    SQLite: datetime('now')
    PostgreSQL: NOW()
    """
    if DB_TYPE == 'postgresql':
        return "NOW()"
    return "datetime('now')"


def sql_date(column: str) -> str:
    """
    Extrahiert das Datum aus einem Timestamp.
    SQLite: DATE(column)
    PostgreSQL: column::DATE
    """
    if DB_TYPE == 'postgresql':
        return f"{column}::DATE"
    return f"DATE({column})"


def sql_year(column: str) -> str:
    """
    Extrahiert das Jahr aus einem Datum.
    SQLite: strftime('%Y', column)
    PostgreSQL: EXTRACT(YEAR FROM column)
    """
    if DB_TYPE == 'postgresql':
        return f"EXTRACT(YEAR FROM {column})"
    return f"strftime('%Y', {column})"


def sql_month(column: str) -> str:
    """
    Extrahiert den Monat aus einem Datum.
    SQLite: strftime('%m', column)
    PostgreSQL: EXTRACT(MONTH FROM column)
    """
    if DB_TYPE == 'postgresql':
        return f"EXTRACT(MONTH FROM {column})"
    return f"strftime('%m', {column})"


def sql_day(column: str) -> str:
    """
    Extrahiert den Tag aus einem Datum.
    SQLite: strftime('%d', column)
    PostgreSQL: EXTRACT(DAY FROM column)
    """
    if DB_TYPE == 'postgresql':
        return f"EXTRACT(DAY FROM {column})"
    return f"strftime('%d', {column})"


def sql_format_date(column: str, format_str: str) -> str:
    """
    Formatiert ein Datum.
    SQLite: strftime(format, column)
    PostgreSQL: TO_CHAR(column, format)

    ACHTUNG: Format-Strings unterscheiden sich!
    SQLite: %Y-%m-%d
    PostgreSQL: YYYY-MM-DD
    """
    if DB_TYPE == 'postgresql':
        # Konvertiere SQLite-Format zu PostgreSQL-Format
        pg_format = format_str.replace('%Y', 'YYYY').replace('%m', 'MM').replace('%d', 'DD')
        pg_format = pg_format.replace('%H', 'HH24').replace('%M', 'MI').replace('%S', 'SS')
        return f"TO_CHAR({column}, '{pg_format}')"
    return f"strftime('{format_str}', {column})"


def sql_coalesce(*args) -> str:
    """COALESCE - funktioniert in beiden DBs gleich"""
    return f"COALESCE({', '.join(str(a) for a in args)})"


def sql_ifnull(column: str, default: Any) -> str:
    """
    NULL-Ersetzung.
    SQLite: IFNULL(column, default)
    PostgreSQL: COALESCE(column, default)
    """
    if DB_TYPE == 'postgresql':
        return f"COALESCE({column}, {default})"
    return f"IFNULL({column}, {default})"


def sql_concat(*args) -> str:
    """
    String-Verkettung.
    Beide: column1 || column2
    """
    return " || ".join(str(a) for a in args)


def sql_placeholder() -> str:
    """
    Placeholder für prepared statements.
    SQLite: ?
    PostgreSQL: %s
    """
    if DB_TYPE == 'postgresql':
        return "%s"
    return "?"


def convert_placeholders(sql: str) -> str:
    """
    Konvertiert ? zu %s für PostgreSQL.

    Verwendung:
        sql = "SELECT * FROM users WHERE id = ? AND name = ?"
        sql = convert_placeholders(sql)
        cursor.execute(sql, (1, 'Test'))
    """
    if DB_TYPE == 'postgresql':
        return sql.replace('?', '%s')
    return sql


# =============================================================================
# STATUS & INFO
# =============================================================================

def get_db_info() -> dict:
    """Gibt Informationen zur aktuellen DB-Konfiguration zurück"""
    info = {
        'type': DB_TYPE,
        'psycopg2_available': PSYCOPG2_AVAILABLE,
    }

    if DB_TYPE == 'postgresql':
        info.update({
            'host': DB_HOST,
            'port': DB_PORT,
            'database': DB_NAME,
            'user': DB_USER,
        })
    else:
        info['path'] = SQLITE_PATH if os.path.exists(SQLITE_PATH) else SQLITE_PATH_LOCAL

    return info


def test_connection() -> dict:
    """Testet die Datenbankverbindung"""
    result = {
        'success': False,
        'type': DB_TYPE,
        'message': ''
    }

    try:
        conn = get_db()
        cursor = conn.cursor()

        if DB_TYPE == 'postgresql':
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            result['version'] = version[0] if version else 'Unknown'
        else:
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()
            result['version'] = version[0] if version else 'Unknown'

        conn.close()
        result['success'] = True
        result['message'] = f"Verbindung zu {DB_TYPE} erfolgreich"

    except Exception as e:
        result['message'] = f"Fehler: {str(e)}"

    return result


# =============================================================================
# MIGRATION HELPERS
# =============================================================================

def is_postgresql_ready() -> bool:
    """Prüft ob PostgreSQL-Datenbank bereit ist"""
    if not PSYCOPG2_AVAILABLE:
        return False

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.close()
        return True
    except Exception:
        return False


def switch_to_postgresql():
    """
    Wechselt zur PostgreSQL-Datenbank.
    Setzt DB_TYPE global (nur für aktuelle Session).
    Für permanenten Wechsel: .env anpassen
    """
    global DB_TYPE

    if not PSYCOPG2_AVAILABLE:
        raise ImportError("psycopg2 nicht installiert")

    if not is_postgresql_ready():
        raise ConnectionError("PostgreSQL-Datenbank nicht erreichbar")

    DB_TYPE = 'postgresql'
    return True


def switch_to_sqlite():
    """
    Wechselt zur SQLite-Datenbank (Rollback).
    Setzt DB_TYPE global (nur für aktuelle Session).
    """
    global DB_TYPE
    DB_TYPE = 'sqlite'
    return True
