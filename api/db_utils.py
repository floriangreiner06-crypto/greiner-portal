"""
Zentrale Datenbank-Utilities für Greiner Portal
================================================
Erstellt: TAG 117 - Code-Qualitäts-Refactoring
Aktualisiert: TAG 136 - PostgreSQL Migration (nutzt db_connection.py)

ARCHITEKTUR:
- db_connection.py: Niedrig-Level (Verbindungen, SQL-Helpers, Placeholders)
- db_utils.py: Hoch-Level (Business-Logik, KPI-Queries, Query-Helpers)

Verwendung:
    from api.db_utils import db_session, locosoft_session, row_to_dict, rows_to_list

    # Portal-Datenbank (SQLite oder PostgreSQL je nach Konfiguration)
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ...")
        data = rows_to_list(cursor.fetchall())
    # Connection wird automatisch geschlossen!

    # Locosoft PostgreSQL (EXTERNE Datenbank)
    with locosoft_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ...")
"""

import os
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# Import von db_connection für Dual-Mode Support
from api.db_connection import (
    get_db as get_portal_db,
    get_db_context,
    get_db_type,
    convert_placeholders,
    sql_placeholder
)

# =============================================================================
# PORTAL-DATENBANK VERBINDUNGEN (nutzt db_connection.py)
# =============================================================================

def get_db():
    """
    Erstellt Portal-Datenbankverbindung (SQLite oder PostgreSQL).

    TAG 136: Nutzt jetzt db_connection.py für Dual-Mode Support.

    WARNUNG: Bevorzuge db_session() Context Manager für automatisches Cleanup!

    Returns:
        Connection-Objekt (sqlite3.Connection oder psycopg2.connection)
    """
    return get_portal_db()


@contextmanager
def db_session():
    """
    Context Manager für sichere Portal-Datenbankverbindung.

    TAG 136: Nutzt jetzt db_connection.py - funktioniert mit SQLite UND PostgreSQL.

    Schließt Connection automatisch, auch bei Exceptions.

    Usage:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            data = cursor.fetchall()
        # Connection ist hier garantiert geschlossen

    Yields:
        Connection-Objekt (sqlite3.Connection oder psycopg2.connection)
    """
    with get_db_context() as conn:
        yield conn


# =============================================================================
# LOCOSOFT POSTGRESQL (EXTERNE Datenbank - 10.80.80.8)
# =============================================================================

def get_locosoft_connection():
    """
    Erstellt PostgreSQL-Verbindung zu Locosoft (EXTERNE Datenbank).

    Dies ist NICHT unsere Portal-DB, sondern die externe Locosoft-DB!

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
        connect_timeout=10,
        options='-c statement_timeout=60000'
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

def row_to_dict(row, cursor=None) -> Optional[Dict[str, Any]]:
    """
    Konvertiert DB-Row zu Dictionary.

    TAG 139: Funktioniert jetzt mit allen Row-Typen:
    - HybridRow (hat keys() und items())
    - sqlite3.Row (hat dict() Support)
    - psycopg2 RealDictRow (ist dict-like)
    - psycopg2 tuple (braucht cursor.description)

    Args:
        row: Row-Objekt oder None
        cursor: Optional - Cursor für Spaltennamen bei Tuples

    Returns:
        Dictionary mit Spalten als Keys, oder None wenn row None ist
    """
    if row is None:
        return None

    # Bereits ein dict
    if isinstance(row, dict):
        return dict(row)

    # HybridRow, sqlite3.Row - unterstützen keys() und items()
    if hasattr(row, 'keys') and hasattr(row, 'items'):
        return dict(row.items())

    # sqlite3.Row mit nur keys()
    if hasattr(row, 'keys'):
        return {k: row[k] for k in row.keys()}

    # Tuple - braucht cursor.description für Spaltennamen
    if isinstance(row, tuple) and cursor is not None:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

    # Fallback: Wenn tuple ohne cursor, versuche keys() zu erzwingen
    # (Kann bei NamedTuple funktionieren)
    if hasattr(row, '_asdict'):
        return row._asdict()

    # Letzter Fallback: Als dict casten (für unbekannte Row-Typen)
    try:
        return dict(row)
    except (TypeError, ValueError):
        # Kann nicht konvertiert werden - als None zurückgeben
        return None


def rows_to_list(rows: List, cursor=None) -> List[Dict[str, Any]]:
    """
    Konvertiert Liste von DB-Rows zu Liste von Dictionaries.

    TAG 139: Unterstützt jetzt auch cursor für Tuple-Rows.

    Args:
        rows: Liste von Row-Objekten
        cursor: Optional - Cursor für Spaltennamen bei Tuples

    Returns:
        Liste von Dictionaries
    """
    if not rows:
        return []
    return [row_to_dict(row, cursor) for row in rows]


# =============================================================================
# QUERY HELPERS (mit PostgreSQL-Kompatibilität)
# =============================================================================

def execute_query(query: str, params: tuple = (), fetchone: bool = False) -> Any:
    """
    Führt SELECT-Query aus und gibt Ergebnis zurück.

    TAG 136: Konvertiert ? zu %s für PostgreSQL automatisch.
    TAG 139: Übergibt cursor für Tuple-zu-Dict Konvertierung.

    Args:
        query: SQL Query String (kann ? als Placeholder nutzen)
        params: Query-Parameter (Tuple)
        fetchone: True für einzelnes Ergebnis, False für Liste

    Returns:
        Dict (fetchone=True) oder List[Dict] (fetchone=False)
    """
    query = convert_placeholders(query)
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetchone:
            return row_to_dict(cursor.fetchone(), cursor)
        return rows_to_list(cursor.fetchall(), cursor)


def execute_write(query: str, params: tuple = ()) -> int:
    """
    Führt INSERT/UPDATE/DELETE aus und committed.

    TAG 136: Konvertiert ? zu %s für PostgreSQL automatisch.

    Args:
        query: SQL Query String (kann ? als Placeholder nutzen)
        params: Query-Parameter (Tuple)

    Returns:
        Anzahl betroffener Zeilen (rowcount)
    """
    query = convert_placeholders(query)
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount


# =============================================================================
# PORTAL ABWESENHEITEN (TAG 127 - Business Logik)
# =============================================================================

# Mapping vacation_type_id -> Locosoft absence reason
VACATION_TYPE_TO_REASON = {
    1: 'Url',   # Urlaubstag (beantragt)
    2: 'Url',   # Urlaubstag (genehmigt)
    5: 'Krn',   # Krankheit
    6: 'ZA.',   # Ausgleichstag (Zeitausgleich)
    7: 'Elt',   # Elternzeit
    9: 'Sem',   # Schulung
    11: 'Snd',  # Sonderurlaub
    12: 'Sem',  # Seminar
}


def get_portal_absences(datum: str = None) -> dict:
    """
    Holt Abwesenheiten aus dem Portal (vacation_bookings).

    TAG 127: Diese Funktion wird von Werkstatt-APIs genutzt um
    Portal-Abwesenheiten (ZA, Krank, etc.) mit Locosoft-Daten zu kombinieren.
    TAG 136: PostgreSQL-kompatibel.

    Args:
        datum: Datum im Format 'YYYY-MM-DD', Default: heute

    Returns:
        Dict mit locosoft_id als Key:
        {
            5008: {
                'employee_id': 123,
                'name': 'Ebner, Patrick',
                'locosoft_id': 5008,
                'reason': 'ZA.',
                'vacation_type': 'Ausgleichstag',
                'day_part': 'full',
                'source': 'portal'
            },
            ...
        }
    """
    from datetime import date

    if datum is None:
        datum = date.today().isoformat()

    result = {}
    ph = sql_placeholder()  # ? oder %s je nach DB
    # TAG 136: PostgreSQL verwendet BOOLEAN, SQLite verwendet 1/0
    aktiv_check = "e.aktiv = true" if get_db_type() == 'postgresql' else "e.aktiv = true"

    with db_session() as conn:
        cursor = conn.cursor()
        query = f"""
            SELECT
                vb.employee_id,
                e.first_name || ' ' || e.last_name as name,
                lem.locosoft_id,
                vb.vacation_type_id,
                vt.name as vacation_type,
                vb.day_part,
                vb.status
            FROM vacation_bookings vb
            JOIN employees e ON vb.employee_id = e.id
            LEFT JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
            LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
            WHERE vb.booking_date = {ph}
              AND vb.status = 'approved'
              AND {aktiv_check}
        """
        cursor.execute(query, (datum,))

        for row in cursor.fetchall():
            row_dict = row_to_dict(row)
            locosoft_id = row_dict['locosoft_id']
            if locosoft_id:
                result[locosoft_id] = {
                    'employee_id': row_dict['employee_id'],
                    'name': row_dict['name'],
                    'locosoft_id': locosoft_id,
                    'reason': VACATION_TYPE_TO_REASON.get(row_dict['vacation_type_id'], 'sns'),
                    'vacation_type': row_dict['vacation_type'] or 'Abwesend',
                    'day_part': row_dict['day_part'],
                    'source': 'portal'
                }

    return result


def get_portal_absences_for_range(start_date: str, end_date: str) -> dict:
    """
    Holt Portal-Abwesenheiten für einen Datumsbereich.

    TAG 136: PostgreSQL-kompatibel.

    Args:
        start_date: Start-Datum 'YYYY-MM-DD'
        end_date: End-Datum 'YYYY-MM-DD'

    Returns:
        Dict mit (datum, locosoft_id) als Key:
        {
            ('2025-12-19', 5008): {...},
            ...
        }
    """
    result = {}
    ph = sql_placeholder()
    # TAG 136: PostgreSQL verwendet BOOLEAN, SQLite verwendet 1/0
    aktiv_check = "e.aktiv = true" if get_db_type() == 'postgresql' else "e.aktiv = true"

    with db_session() as conn:
        cursor = conn.cursor()
        query = f"""
            SELECT
                vb.booking_date,
                vb.employee_id,
                e.first_name || ' ' || e.last_name as name,
                lem.locosoft_id,
                vb.vacation_type_id,
                vt.name as vacation_type,
                vb.day_part
            FROM vacation_bookings vb
            JOIN employees e ON vb.employee_id = e.id
            LEFT JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
            LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
            WHERE vb.booking_date BETWEEN {ph} AND {ph}
              AND vb.status = 'approved'
              AND {aktiv_check}
        """
        cursor.execute(query, (start_date, end_date))

        for row in cursor.fetchall():
            row_dict = row_to_dict(row)
            locosoft_id = row_dict['locosoft_id']
            if locosoft_id:
                key = (row_dict['booking_date'], locosoft_id)
                result[key] = {
                    'employee_id': row_dict['employee_id'],
                    'name': row_dict['name'],
                    'locosoft_id': locosoft_id,
                    'reason': VACATION_TYPE_TO_REASON.get(row_dict['vacation_type_id'], 'sns'),
                    'vacation_type': row_dict['vacation_type'] or 'Abwesend',
                    'day_part': row_dict['day_part'],
                    'source': 'portal'
                }

    return result
