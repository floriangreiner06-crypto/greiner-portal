"""
Bankenspiegel Utilities - Zentrale Funktionen
=============================================
TAG 180: Automatische Snapshot-Erstellung bei Saldo-Import
"""

from api.db_utils import db_session, row_to_dict
from api.db_connection import sql_placeholder


def create_snapshot_from_saldo(konto_id, stichtag, saldo, cursor=None):
    """
    Erstellt automatisch einen Snapshot in konto_snapshots basierend auf einem importierten Saldo.
    
    Args:
        konto_id: ID des Kontos
        stichtag: Datum des Saldos (date oder string 'YYYY-MM-DD')
        saldo: Saldo-Wert (float)
        cursor: Optional - DB-Cursor (wenn None, wird neue Connection erstellt)
    
    Returns:
        dict: {'created': bool, 'updated': bool, 'kreditlinie': float}
    
    TAG 180: Wird automatisch von MT940 und HVB PDF Import aufgerufen
    """
    ph = sql_placeholder()
    
    # Wenn kein Cursor übergeben, eigene Connection erstellen
    if cursor is None:
        with db_session() as conn:
            cursor = conn.cursor()
            result = _create_snapshot_internal(cursor, konto_id, stichtag, saldo, ph)
            conn.commit()
            return result
    else:
        # Cursor wurde übergeben (z.B. aus Import-Script)
        return _create_snapshot_internal(cursor, konto_id, stichtag, saldo, ph)


def _create_snapshot_internal(cursor, konto_id, stichtag, saldo, ph):
    """Interne Funktion für Snapshot-Erstellung"""
    # Kreditlinie aus konten-Tabelle holen
    cursor.execute(f"""
        SELECT kreditlinie 
        FROM konten 
        WHERE id = {ph}
    """, (konto_id,))
    
    konto_row = cursor.fetchone()
    kreditlinie = None
    if konto_row:
        konto_dict = row_to_dict(konto_row)
        kreditlinie = float(konto_dict['kreditlinie']) if konto_dict.get('kreditlinie') else None
    
    # Prüfe ob Snapshot für diesen Stichtag bereits existiert
    cursor.execute(f"""
        SELECT id FROM konto_snapshots 
        WHERE konto_id = {ph} AND stichtag = {ph}
    """, (konto_id, stichtag))
    
    existing = cursor.fetchone()
    
    if existing:
        # Update
        snapshot_id = row_to_dict(existing)['id']
        cursor.execute(f"""
            UPDATE konto_snapshots 
            SET kapitalsaldo = {ph},
                kreditlinie = {ph}
            WHERE id = {ph}
        """, (saldo, kreditlinie, snapshot_id))
        return {'created': False, 'updated': True, 'kreditlinie': kreditlinie}
    else:
        # Insert
        cursor.execute(f"""
            INSERT INTO konto_snapshots 
            (konto_id, stichtag, kapitalsaldo, kreditlinie)
            VALUES ({ph}, {ph}, {ph}, {ph})
        """, (konto_id, stichtag, saldo, kreditlinie))
        return {'created': True, 'updated': False, 'kreditlinie': kreditlinie}
