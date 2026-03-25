"""
Cashflow-/Liquiditätsvorschau – SSOT für Projektion & IST-Cashflow
==================================================================
Phase 1: Saldo heute + Transaktionen (IST) + Tilgungen über einen Zeitraum.
IST-Cashflow: Einnahmen/Ausgaben pro Monat aus transaktionen (Vergangenheit).

Kein neues Datenmodell; nutzt v_aktuelle_kontostaende, transaktionen, tilgungen.
Workstream: Controlling
"""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from api.db_utils import db_session, row_to_dict, rows_to_list

# Interne Transfers aus Cashflow ausblenden (wie Bankenspiegel-Dashboard)
_TRANSFER_FILTER = """
    AND NOT (
        verwendungszweck LIKE '%%Autohaus Greiner%%Autohaus Greiner%%'
        OR verwendungszweck LIKE '%%Umbuchung%%'
        OR verwendungszweck LIKE '%%Einlage%%'
        OR verwendungszweck LIKE '%%Rückzahlung Einlage%%'
    )
"""


def get_cashflow_ist(monate=12):
    """
    IST-Cashflow: Einnahmen und Ausgaben pro Monat (Vergangenheit).

    Nutzt transaktionen; interne Transfers (Umbuchungen, Einlagen) werden
    ausgeblendet, damit nur „echte“ Zu- und Abflüsse zählen.

    Args:
        monate: Anzahl Monate zurück (default: 12).

    Returns:
        dict mit:
        - monate: int
        - reihe: list of { monat (YYYY-MM), einnahmen, ausgaben, saldo, anzahl }
    """
    heute = date.today()
    start = heute - relativedelta(months=monate - 1)
    start = start.replace(day=1)  # Erster des Monats

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                TO_CHAR(buchungsdatum, 'YYYY-MM') AS monat,
                COALESCE(SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END), 0) AS einnahmen,
                COALESCE(SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END), 0) AS ausgaben,
                COUNT(*) AS anzahl
            FROM transaktionen
            WHERE buchungsdatum >= %s AND buchungsdatum <= %s
            """ + _TRANSFER_FILTER + """
            GROUP BY TO_CHAR(buchungsdatum, 'YYYY-MM')
            ORDER BY monat
        """, (start, heute))
        rows = rows_to_list(cursor.fetchall(), cursor)

    reihe = []
    for d in rows:
        einnahmen = float(d.get('einnahmen') or 0)
        ausgaben = float(d.get('ausgaben') or 0)
        reihe.append({
            'monat': d.get('monat'),
            'einnahmen': round(einnahmen, 2),
            'ausgaben': round(ausgaben, 2),
            'saldo': round(einnahmen - ausgaben, 2),
            'anzahl': int(d.get('anzahl') or 0),
        })

    return {'monate': monate, 'reihe': reihe}


# Vergangenheit (Tage) für Durchschnitt „erwartete Einnahmen pro Tag“
_TAGE_DURCHSCHNITT_EINNAHMEN = 90


def get_cashflow_vorschau(tage=60):
    """
    Projektion: Laufender Saldo für die nächsten `tage` Tage.

    - Start: Gesamtsaldo aus v_aktuelle_kontostaende (alle aktiven Konten).
    - Pro Tag: + Transaktionen (IST) + erwartete Einnahmen (nur Locosoft: Fz netto + Werkstatt) − Ausgaben − Tilgungen.
    - Erwartete Einnahmen: ausschließlich aus Locosoft (Fahrzeug netto nach Ablöse, Werkstatt). Kein Ø/Tag.

    Returns:
        dict mit: start_saldo, neuester_stand, tage, erwartete_einnahmen_quelle, hinweis_durchschnitt_vergangenheit,
        reihe (erwartete_einnahmen, erwartete_fahrzeug_netto, erwartete_werkstatt).
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

        # 4. Hinweis: Ø Einnahmen/Tag Vergangenheit (nur Anzeige, geht nicht in Saldo ein)
        von_durchschnitt = heute - timedelta(days=_TAGE_DURCHSCHNITT_EINNAHMEN)
        cursor.execute("""
            SELECT COALESCE(SUM(betrag), 0) AS summe
            FROM transaktionen
            WHERE buchungsdatum >= %s AND buchungsdatum < %s AND betrag > 0
            """ + _TRANSFER_FILTER,
            (von_durchschnitt, heute),
        )
        row_avg = cursor.fetchone()
        summe_einnahmen = float(row_avg[0] if row_avg else 0)
        hinweis_durchschnitt = round(summe_einnahmen / _TAGE_DURCHSCHNITT_EINNAHMEN, 2) if _TAGE_DURCHSCHNITT_EINNAHMEN else 0.0

    # 5. Erwartete Einnahmen aus Locosoft (Fahrzeug netto + Werkstatt), nur Daten – kein Schnitt
    from api.cashflow_erwartung_locosoft import get_erwartete_einnahmen_gesamt
    loco = get_erwartete_einnahmen_gesamt(heute, ende)
    pro_tag = loco.get("pro_tag") or {}

    # 5b. Erwartete wiederkehrende Ausgaben aus Transaktionen-Historie (Löhne/Gehälter, Miete, Steuern, Zinsen …)
    from api.cashflow_erwartung_ausgaben import get_erwartete_ausgaben_gesamt
    ausgaben_data = get_erwartete_ausgaben_gesamt(heute, ende, monate_historie=12)
    erwartete_ausgaben_pro_tag = ausgaben_data.get("pro_tag") or {}
    wiederkehrende_muster = ausgaben_data.get("muster") or []

    # 6. Zeitreihe: Saldo + Einnahmen (IST) + erwartete Einnahmen (Locosoft) − Ausgaben − Tilgungen − erwartete Ausgaben
    reihe = []
    saldo = start_saldo
    for i in range(tage + 1):
        d = heute + timedelta(days=i)
        datum_iso = d.isoformat()
        trans = trans_by_date.get(d, {'einnahmen': 0.0, 'ausgaben': 0.0})
        einnahmen = trans['einnahmen']
        ausgaben = trans['ausgaben']
        tilgungen = tilg_by_date.get(d, 0.0)
        tag_data = pro_tag.get(datum_iso) or {}
        erwartet = float(tag_data.get("erwartete_einnahmen") or 0)
        fz_netto = float(tag_data.get("fahrzeug_netto") or 0)
        wst = float(tag_data.get("werkstatt") or 0)
        ausgaben_erw = erwartete_ausgaben_pro_tag.get(datum_iso) or {}
        erwartete_ausgaben = float(ausgaben_erw.get("erwartete_ausgaben") or 0)
        saldo = saldo + einnahmen + erwartet - ausgaben - tilgungen - erwartete_ausgaben
        reihe.append({
            'datum': datum_iso,
            'saldo': round(saldo, 2),
            'einnahmen': round(einnahmen, 2),
            'ausgaben': round(ausgaben, 2),
            'erwartete_einnahmen': round(erwartet, 2),
            'erwartete_fahrzeug_netto': round(fz_netto, 2),
            'erwartete_werkstatt': round(wst, 2),
            'tilgungen': round(tilgungen, 2),
            'erwartete_ausgaben': round(erwartete_ausgaben, 2),
            'erwartete_ausgaben_details': ausgaben_erw.get("details") or [],
        })

    neuester_str = None
    if neuester_stand:
        neuester_str = neuester_stand.isoformat() if hasattr(neuester_stand, 'isoformat') else str(neuester_stand)

    return {
        'start_saldo': round(start_saldo, 2),
        'neuester_stand': neuester_str,
        'tage': tage,
        'erwartete_einnahmen_pro_tag': 0,
        'erwartete_einnahmen_quelle': 'locosoft',
        'tage_durchschnitt': None,
        'hinweis_durchschnitt_vergangenheit': hinweis_durchschnitt,
        'wiederkehrende_ausgaben_muster': wiederkehrende_muster,
        'reihe': reihe,
    }
