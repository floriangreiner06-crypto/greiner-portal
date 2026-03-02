"""
Cashflow-/Liquiditätsvorschau – SSOT für Projektion
====================================================
Phase 1: Saldo heute + Transaktionen (IST) + Tilgungen über einen Zeitraum.
Kein neues Datenmodell; nutzt v_aktuelle_kontostaende, transaktionen, tilgungen.

Workstream: Controlling
"""

from datetime import date, timedelta
from api.db_utils import db_session, row_to_dict, rows_to_list


def get_cashflow_vorschau(tage=60):
    """
    Projektion: Laufender Saldo für die nächsten `tage` Tage.

    - Start: Gesamtsaldo aus v_aktuelle_kontostaende (alle aktiven Konten).
    - Pro Tag: + Transaktionen (betrag, bereits in transaktionen) − Tilgungen (faellig_am, betrag).
    - Ausgabe: Zeitreihe mit datum, saldo, einnahmen, ausgaben, tilgungen.

    Returns:
        dict mit:
        - start_saldo: float
        - neuester_stand: date oder None (letztes Salden-Update)
        - tage: int
        - reihe: list of { datum, saldo, einnahmen, ausgaben, tilgungen }
    """
    heute = date.today()
    ende = heute + timedelta(days=tage)

    with db_session() as conn:
        cursor = conn.cursor()

        # 1. Gesamtsaldo heute (View: id = Konto-ID, saldo, letztes_update)
        cursor.execute("""
            SELECT
                COALESCE(SUM(saldo), 0) AS gesamtsaldo,
                MAX(letztes_update)::date AS neuester_stand
            FROM v_aktuelle_kontostaende
        """)
        row = row_to_dict(cursor.fetchone())
        start_saldo = float(row.get('gesamtsaldo') or 0)
        neuester_stand = row.get('neuester_stand')

        # 2. Transaktionen im Zeitraum (pro Tag: Summe betrag)
        cursor.execute("""
            SELECT
                buchungsdatum AS datum,
                COALESCE(SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END), 0) AS einnahmen,
                COALESCE(SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END), 0) AS ausgaben
            FROM transaktionen
            WHERE buchungsdatum >= %s AND buchungsdatum <= %s
            GROUP BY buchungsdatum
            ORDER BY buchungsdatum
        """, (heute, ende))
        trans_by_date = {}
        for d in rows_to_list(cursor.fetchall(), cursor):
            dt = d.get('datum')
            if dt:
                if hasattr(dt, 'date'):
                    dt = dt.date()
                trans_by_date[dt] = {
                    'einnahmen': float(d.get('einnahmen') or 0),
                    'ausgaben': float(d.get('ausgaben') or 0),
                }

        # 3. Tilgungen im Zeitraum (pro Tag: Summe betrag)
        cursor.execute("""
            SELECT
                faellig_am AS datum,
                COALESCE(SUM(betrag), 0) AS tilgungen
            FROM tilgungen
            WHERE faellig_am >= %s AND faellig_am <= %s
            GROUP BY faellig_am
            ORDER BY faellig_am
        """, (heute, ende))
        tilg_by_date = {}
        for d in rows_to_list(cursor.fetchall(), cursor):
            dt = d.get('datum')
            if dt:
                if hasattr(dt, 'date'):
                    dt = dt.date()
                tilg_by_date[dt] = float(d.get('tilgungen') or 0)

    # 4. Zeitreihe aufbauen: ein Tag = Vortag-Saldo + Einnahmen − Ausgaben − Tilgungen
    reihe = []
    saldo = start_saldo
    for i in range(tage + 1):
        d = heute + timedelta(days=i)
        trans = trans_by_date.get(d, {'einnahmen': 0.0, 'ausgaben': 0.0})
        einnahmen = trans['einnahmen']
        ausgaben = trans['ausgaben']
        tilgungen = tilg_by_date.get(d, 0.0)
        # Saldo: + Einnahmen, − Ausgaben, − Tilgungen
        saldo = saldo + einnahmen - ausgaben - tilgungen
        reihe.append({
            'datum': d.isoformat(),
            'saldo': round(saldo, 2),
            'einnahmen': round(einnahmen, 2),
            'ausgaben': round(ausgaben, 2),
            'tilgungen': round(tilgungen, 2),
        })

    neuester_str = None
    if neuester_stand:
        neuester_str = neuester_stand.isoformat() if hasattr(neuester_stand, 'isoformat') else str(neuester_stand)

    return {
        'start_saldo': round(start_saldo, 2),
        'neuester_stand': neuester_str,
        'tage': tage,
        'reihe': reihe,
    }
