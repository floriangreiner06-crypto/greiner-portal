"""
Zentrale Datenbank-Utilities für Greiner Portal
================================================
Erstellt: TAG 117 - Code-Qualitäts-Refactoring
Aktualisiert: TAG 136 - PostgreSQL Migration (nutzt db_connection.py)
Aktualisiert: TAG 179 - G&V-Filter zentralisiert

ARCHITEKTUR:
- db_connection.py: Niedrig-Level (Verbindungen, SQL-Helpers, Placeholders)
- db_utils.py: Hoch-Level (Business-Logik, KPI-Queries, Query-Helpers)

Verwendung:
    from api.db_utils import db_session, locosoft_session, row_to_dict, rows_to_list, get_guv_filter

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
    """
    return get_portal_db()


@contextmanager
def db_session():
    """
    Context Manager für Portal-Datenbankverbindungen.

    Automatisches Cleanup (commit/rollback/close).

    Beispiel:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
            conn.commit()
    """
    with get_db_context() as conn:
        yield conn


# =============================================================================
# LOCOSOFT DATENBANK VERBINDUNGEN (EXTERNE PostgreSQL)
# =============================================================================

def get_locosoft_connection():
    """
    Erstellt Verbindung zur externen Locosoft PostgreSQL-Datenbank.

    WARNUNG: Bevorzuge locosoft_session() Context Manager für automatisches Cleanup!

    Konfiguration:
    - Host: 10.80.80.8:5432
    - Database: loco_auswertung_db
    - User: loco_auswertung_benutzer
    - Password: loco (aus credentials.json)
    """
    import psycopg2
    import json

    credentials_path = '/opt/greiner-portal/config/credentials.json'
    if os.path.exists(credentials_path):
        with open(credentials_path, 'r') as f:
            creds = json.load(f)
            locosoft_creds = creds.get('locosoft_postgresql', {})
    else:
        # Fallback
        locosoft_creds = {
            'host': '10.80.80.8',
            'port': 5432,
            'database': 'loco_auswertung_db',
            'user': 'loco_auswertung_benutzer',
            'password': 'loco'
        }

    return psycopg2.connect(
        host=locosoft_creds.get('host', '10.80.80.8'),
        port=locosoft_creds.get('port', 5432),
        database=locosoft_creds.get('database', 'loco_auswertung_db'),
        user=locosoft_creds.get('user', 'loco_auswertung_benutzer'),
        password=locosoft_creds.get('password', 'loco')
    )


@contextmanager
def locosoft_session():
    """
    Context Manager für Locosoft-Datenbankverbindungen.

    Automatisches Cleanup (commit/rollback/close).

    Beispiel:
        with locosoft_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ... FROM journal_accountings ...")
    """
    conn = None
    try:
        conn = get_locosoft_connection()
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


# =============================================================================
# ROW CONVERSION HELPERS
# =============================================================================

def row_to_dict(row, cursor=None) -> Optional[Dict[str, Any]]:
    """
    Konvertiert Datenbank-Row zu Dictionary.

    Unterstützt sowohl SQLite (Row) als auch PostgreSQL (RealDictRow/HybridRow).

    TAG 136: PostgreSQL HybridRow unterstützt sowohl row[0] als auch row['name'].
    """
    if row is None:
        return None

    # PostgreSQL RealDictRow oder HybridRow
    if hasattr(row, 'keys'):
        return dict(row)

    # SQLite Row oder Tuple
    if cursor and hasattr(cursor, 'description') and cursor.description:
        return {desc[0]: row[i] for i, desc in enumerate(cursor.description)}
    elif isinstance(row, (tuple, list)):
        # Fallback: Numerische Keys
        return {i: val for i, val in enumerate(row)}

    return row


def rows_to_list(rows: List, cursor=None) -> List[Dict[str, Any]]:
    """
    Konvertiert Liste von Rows zu Liste von Dictionaries.

    Beispiel:
        rows = cursor.fetchall()
        data = rows_to_list(rows, cursor)
    """
    return [row_to_dict(row, cursor) for row in rows if row is not None]


# =============================================================================
# QUERY HELPERS
# =============================================================================

def execute_query(query: str, params: tuple = (), fetchone: bool = False) -> Any:
    """
    Führt SELECT-Query aus und gibt Ergebnis zurück.

    Beispiel:
        result = execute_query("SELECT * FROM employees WHERE id = %s", (1,), fetchone=True)
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(convert_placeholders(query), params)
        if fetchone:
            return row_to_dict(cursor.fetchone(), cursor)
        return rows_to_list(cursor.fetchall(), cursor)


def execute_write(query: str, params: tuple = ()) -> int:
    """
    Führt INSERT/UPDATE/DELETE-Query aus und gibt Anzahl betroffener Zeilen zurück.

    Beispiel:
        affected = execute_write("UPDATE employees SET active = true WHERE id = %s", (1,))
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(convert_placeholders(query), params)
        conn.commit()
        return cursor.rowcount


# =============================================================================
# PORTAL ABWESENHEITEN (Urlaubsplaner)
# =============================================================================

def get_portal_absences(datum: str = None) -> dict:
    """
    Holt Abwesenheiten aus Portal-DB für ein bestimmtes Datum.

    Returns:
        dict: {(datum, locosoft_id): {employee_id, name, reason, ...}}
    """
    from datetime import date, datetime
    from api.db_connection import convert_placeholders

    if datum is None:
        datum = date.today().isoformat()

    result = {}
    VACATION_TYPE_TO_REASON = {
        1: 'vac',  # Urlaub
        2: 'ill',  # Krank
        3: 'edu',  # Fortbildung
        4: 'oth'   # Sonstiges
    }

    # TAG 136: PostgreSQL verwendet BOOLEAN, SQLite verwendet 1/0
    aktiv_check = "e.aktiv = true" if get_db_type() == 'postgresql' else "e.aktiv = true"

    with db_session() as conn:
        cursor = conn.cursor()
        ph = sql_placeholder()
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
            WHERE vb.booking_date = {ph}
              AND vb.status = 'approved'
              AND {aktiv_check}
        """
        cursor.execute(query, (datum,))

        for row in cursor.fetchall():
            row_dict = row_to_dict(row, cursor)
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


def get_portal_absences_for_range(start_date: str, end_date: str) -> dict:
    """
    Holt Abwesenheiten aus Portal-DB für einen Zeitraum.

    Returns:
        dict: {(datum, locosoft_id): {employee_id, name, reason, ...}}
    """
    from api.db_connection import convert_placeholders, sql_placeholder

    result = {}
    VACATION_TYPE_TO_REASON = {
        1: 'vac',  # Urlaub
        2: 'ill',  # Krank
        3: 'edu',  # Fortbildung
        4: 'oth'   # Sonstiges
    }

    # TAG 136: PostgreSQL verwendet BOOLEAN, SQLite verwendet 1/0
    aktiv_check = "e.aktiv = true" if get_db_type() == 'postgresql' else "e.aktiv = true"

    with db_session() as conn:
        cursor = conn.cursor()
        ph = sql_placeholder()
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
            row_dict = row_to_dict(row, cursor)
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


# =============================================================================
# BWA & CONTROLLING HELPER FUNCTIONS
# =============================================================================

def get_guv_filter() -> str:
    """
    G&V-Abschluss-Filter für BWA-Berechnungen
    
    Schließt G&V-Abschlussbuchungen aus, die die BWA verfälschen würden.
    
    TAG 179: Zentrale Funktion zur Vermeidung von Redundanzen.
    
    Returns:
        SQL-Filter-String: "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
    Beispiel:
        from api.db_utils import get_guv_filter
        guv_filter = get_guv_filter()
        cursor.execute(f"SELECT ... FROM loco_journal_accountings WHERE ... {guv_filter}")
    """
    # TAG 136: %% escaped für PostgreSQL (sonst als Placeholder interpretiert)
    return "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
