"""
Carloop Datenmodelle
====================
PostgreSQL-Tabellen für Carloop-Reservierungen.

Erstellt: TAG 131 (2025-12-20)
TAG142: Umgestellt auf PostgreSQL via api.db_connection
"""
import os
from datetime import datetime, date
from typing import List, Dict, Optional
import logging

from api.db_connection import get_db, convert_placeholders

logger = logging.getLogger(__name__)

# get_db() wird jetzt direkt aus api.db_connection importiert (SSOT)


def init_carloop_tables():
    """
    Erstellt Carloop-Tabellen falls nicht vorhanden.
    TAG142: PostgreSQL-kompatibel (SERIAL statt AUTOINCREMENT)
    """
    conn = get_db()
    cursor = conn.cursor()

    # Reservierungen-Tabelle
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carloop_reservierungen (
            id SERIAL PRIMARY KEY,
            reservierung_id TEXT UNIQUE NOT NULL,
            kennzeichen TEXT NOT NULL,
            fahrzeug_modell TEXT,
            kunde_name TEXT,
            kunde_nr TEXT,
            von TIMESTAMP NOT NULL,
            bis TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'reserviert',
            tarif TEXT,
            bemerkung TEXT,
            carloop_url TEXT,
            locosoft_termin_nr INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sync_status TEXT DEFAULT 'pending'
        )
    ''')

    # Fahrzeuge-Mapping Tabelle
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carloop_fahrzeuge (
            id SERIAL PRIMARY KEY,
            kennzeichen TEXT UNIQUE NOT NULL,
            modell TEXT,
            locosoft_nr INTEGER,
            aktiv INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Index für schnelle Suche
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_carloop_res_von ON carloop_reservierungen(von)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_carloop_res_kennzeichen ON carloop_reservierungen(kennzeichen)')

    conn.commit()
    conn.close()
    logger.info("Carloop-Tabellen initialisiert")


def upsert_reservierung(res: Dict) -> int:
    """
    Fügt Reservierung ein oder aktualisiert sie.
    TAG142: PostgreSQL-kompatibel mit RETURNING id
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO carloop_reservierungen
            (reservierung_id, kennzeichen, fahrzeug_modell, kunde_name, kunde_nr,
             von, bis, status, tarif, bemerkung, carloop_url, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT(reservierung_id) DO UPDATE SET
            kennzeichen = excluded.kennzeichen,
            fahrzeug_modell = excluded.fahrzeug_modell,
            kunde_name = excluded.kunde_name,
            kunde_nr = excluded.kunde_nr,
            von = excluded.von,
            bis = excluded.bis,
            status = excluded.status,
            tarif = excluded.tarif,
            bemerkung = excluded.bemerkung,
            carloop_url = excluded.carloop_url,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id
    ''', (
        res.get('reservierung_id'),
        res.get('kennzeichen'),
        res.get('fahrzeug_modell'),
        res.get('kunde_name'),
        res.get('kunde_nr'),
        res.get('von'),
        res.get('bis'),
        res.get('status'),
        res.get('tarif'),
        res.get('bemerkung'),
        res.get('carloop_url'),
    ))

    result = cursor.fetchone()
    row_id = result[0] if result else None
    conn.commit()
    conn.close()
    return row_id


def get_reservierungen(von: date = None, bis: date = None, kennzeichen: str = None) -> List[Dict]:
    """
    Holt Reservierungen aus DB.
    TAG142: PostgreSQL-kompatibel
    """
    conn = get_db()
    cursor = conn.cursor()

    query = 'SELECT * FROM carloop_reservierungen WHERE 1=1'
    params = []

    if von:
        query += ' AND DATE(bis) >= %s'
        params.append(von.isoformat())
    if bis:
        query += ' AND DATE(von) <= %s'
        params.append(bis.isoformat())
    if kennzeichen:
        query += ' AND kennzeichen = %s'
        params.append(kennzeichen)

    query += ' ORDER BY von ASC'

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    # HybridRow unterstützt dict-Zugriff
    return [dict(row) for row in rows]


def get_reservierungen_by_datum(datum: date) -> List[Dict]:
    """Holt alle Reservierungen für einen Tag."""
    return get_reservierungen(von=datum, bis=datum)


def upsert_fahrzeug(kennzeichen: str, modell: str, locosoft_nr: int = None):
    """
    Fügt Fahrzeug ein oder aktualisiert es.
    TAG142: PostgreSQL-kompatibel
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO carloop_fahrzeuge (kennzeichen, modell, locosoft_nr)
        VALUES (%s, %s, %s)
        ON CONFLICT(kennzeichen) DO UPDATE SET
            modell = excluded.modell,
            locosoft_nr = COALESCE(excluded.locosoft_nr, carloop_fahrzeuge.locosoft_nr)
    ''', (kennzeichen, modell, locosoft_nr))

    conn.commit()
    conn.close()


def get_fahrzeuge() -> List[Dict]:
    """
    Holt alle Fahrzeuge.
    TAG142: PostgreSQL-kompatibel
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM carloop_fahrzeuge WHERE aktiv = 1 ORDER BY kennzeichen')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# Tabellen beim Import initialisieren
try:
    init_carloop_tables()
except Exception as e:
    logger.warning(f"Carloop-Tabellen konnten nicht initialisiert werden: {e}")
