"""
Ertragsvorschau Data Layer (SSOT)
==================================
Erstellt: 2026-03-30 | Workstream: Controlling

Zentrale Datenquelle für Dashboard und Bank-Report.
Alle Funktionen liefern fertig aufbereitete Dicts.
"""

import logging
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger('ertragsvorschau_data')


def _aktuelles_gj() -> str:
    """Bestimmt das aktuelle Geschäftsjahr."""
    heute = date.today()
    if heute.month >= 9:
        return f"{heute.year}/{str(heute.year + 1)[-2:]}"
    return f"{heute.year - 1}/{str(heute.year)[-2:]}"


def _vorjahres_gj(gj: str) -> str:
    """Bestimmt das Vorjahres-GJ."""
    start = int(gj.split('/')[0])
    return f"{start - 1}/{str(start)[-2:]}"


def _gj_monate(gj: str) -> list:
    """Liefert die 12 Kalendermonate eines GJ als (jahr, monat)-Tupel.

    '2025/26' → [(2025,9), (2025,10), ..., (2025,12), (2026,1), ..., (2026,8)]
    """
    start = int(gj.split('/')[0])
    monate = []
    for m in range(9, 13):
        monate.append((start, m))
    for m in range(1, 9):
        monate.append((start + 1, m))
    return monate


def _gj_start_ende(gj: str) -> tuple:
    """Liefert Start- und End-Datum eines GJ."""
    start = int(gj.split('/')[0])
    return date(start, 9, 1), date(start + 1, 8, 31)


def get_guv_daten(geschaeftsjahr: str = None, gesellschaft: str = 'autohaus') -> dict:
    """Monatliche GuV aus fibu_guv_monatswerte.

    Args:
        geschaeftsjahr: z.B. '2025/26' (default: aktuelles GJ)
        gesellschaft: 'autohaus', 'auto' oder 'gruppe' (konsolidiert = autohaus + auto)

    Returns:
        {
            'geschaeftsjahr': '2025/26',
            'monate': [
                {'monat': 9, 'jahr': 2025, 'label': 'Sep 25',
                 'erloese': 123456, 'we': -98765, 'rohertrag': 24691,
                 'personal': -21000, 'sonst_aufwand': -5000,
                 'ebit': -1309, 'zinsen': -1500, 'ebt': -2809,
                 'rohertrag_marge': 20.0},
                ...
            ],
            'kumuliert': { ... gleiche Felder, summiert ... },
            'vj_kumuliert': { ... Vorjahreszeitraum ... },
            'delta_vj': { ... Differenz zum VJ ... }
        }
    """
    from api.db_utils import db_session

    if not geschaeftsjahr:
        geschaeftsjahr = _aktuelles_gj()

    vj = _vorjahres_gj(geschaeftsjahr)

    with db_session() as conn:
        cursor = conn.cursor()

        # Alle Monatswerte für aktuelles + Vorjahres-GJ
        if gesellschaft == 'gruppe':
            # Konsolidiert: Summe aus autohaus + auto
            cursor.execute("""
                SELECT geschaeftsjahr, monat, bereich, SUM(betrag_cent) as betrag_cent
                FROM fibu_guv_monatswerte
                WHERE geschaeftsjahr IN (%s, %s)
                  AND gesellschaft IN ('autohaus', 'auto')
                GROUP BY geschaeftsjahr, monat, bereich
                ORDER BY geschaeftsjahr, monat, bereich
            """, (geschaeftsjahr, vj))
        else:
            cursor.execute("""
                SELECT geschaeftsjahr, monat, bereich, betrag_cent
                FROM fibu_guv_monatswerte
                WHERE geschaeftsjahr IN (%s, %s)
                  AND gesellschaft = %s
                ORDER BY geschaeftsjahr, monat, bereich
            """, (geschaeftsjahr, vj, gesellschaft))

        rows = cursor.fetchall()

    # Daten strukturieren: {(gj, monat): {bereich: betrag_cent}}
    daten = {}
    for row in rows:
        key = (row[0], row[1])
        if key not in daten:
            daten[key] = {}
        daten[key][row[2]] = row[3]

    def _berechne_monat(monat_daten: dict) -> dict:
        ws = monat_daten.get('werkstatt_erloese', 0)
        te = monat_daten.get('teile_erloese', 0)
        se = monat_daten.get('sonst_erloese', 0)
        fe = monat_daten.get('fz_erloese', 0)
        erloese = ws + te + se + fe

        ww = monat_daten.get('we_werkstatt', 0)
        wt = monat_daten.get('we_teile', 0)
        wso = monat_daten.get('we_sonstige', 0)
        we = ww + wt + wso

        rohertrag = erloese + we  # we ist negativ
        personal = monat_daten.get('personal', 0)
        sonst = monat_daten.get('sonst_aufwand', 0)

        na = monat_daten.get('neutral_aufwand', 0)
        ne = monat_daten.get('neutral_ertrag', 0)

        ebit = rohertrag + personal + sonst + na + ne

        za = monat_daten.get('zinsen_aufwand', 0)
        ze = monat_daten.get('zinsen_ertrag', 0)
        zinsen = za + ze

        ebt = ebit + zinsen

        marge = round(rohertrag / erloese * 100, 1) if erloese else 0

        return {
            'erloese': round(erloese / 100),
            'we': round(we / 100),
            'rohertrag': round(rohertrag / 100),
            'rohertrag_marge': marge,
            'personal': round(personal / 100),
            'sonst_aufwand': round(sonst / 100),
            'ebit': round(ebit / 100),
            'zinsen': round(zinsen / 100),
            'ebt': round(ebt / 100),
            # Detail-Erlöse
            'werkstatt_erloese': round(ws / 100),
            'teile_erloese': round(te / 100),
            'fz_erloese': round(fe / 100),
            'sonst_erloese': round(se / 100),
        }

    # Aktuelle Monate aufbauen
    gj_monate = _gj_monate(geschaeftsjahr)
    monate = []
    monatslabels = ['', 'Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

    for jahr, monat in gj_monate:
        key = (geschaeftsjahr, monat)
        if key in daten:
            m = _berechne_monat(daten[key])
            m['monat'] = monat
            m['jahr'] = jahr
            m['label'] = f"{monatslabels[monat]} {str(jahr)[-2:]}"
            monate.append(m)

    # Unvollständigen letzten Monat erkennen
    # Regel: Wenn der letzte Datenmonat = aktueller Kalendermonat → immer unvollständig
    # (Lohn/Gehalt wird erst zum Monatsende/Anfang nächster Monat gebucht)
    # Unvollständiger Monat wird in der Tabelle ANGEZEIGT aber aus der KUMULIERUNG AUSGESCHLOSSEN
    if monate:
        letzter = monate[-1]
        heute = date.today()
        if letzter['jahr'] == heute.year and letzter['monat'] == heute.month:
            monate[-1]['unvollstaendig'] = True
            logger.info(f"  Monat {letzter['label']} als unvollständig markiert (laufender Monat) — nicht in Kumulierung")

    # Kumuliert: NUR abgeschlossene Monate (ohne unvollständigen letzten Monat)
    kum_felder = ['erloese', 'we', 'rohertrag', 'personal', 'sonst_aufwand', 'ebit', 'zinsen', 'ebt',
                  'werkstatt_erloese', 'teile_erloese', 'fz_erloese', 'sonst_erloese']

    abgeschlossene = [m for m in monate if not m.get('unvollstaendig')]
    kumuliert = {f: sum(m.get(f, 0) for m in abgeschlossene) for f in kum_felder}
    kumuliert['rohertrag_marge'] = round(kumuliert['rohertrag'] / kumuliert['erloese'] * 100, 1) if kumuliert['erloese'] else 0
    kumuliert['anzahl_monate'] = len(abgeschlossene)
    kumuliert['hat_unvollstaendigen_monat'] = any(m.get('unvollstaendig') for m in monate)

    # Vorjahr: gleiche abgeschlossene Monate (nicht den unvollständigen)
    bisherige_monate_nummern = [m['monat'] for m in abgeschlossene]
    vj_monate_data = []
    for jahr, monat in _gj_monate(vj):
        if monat not in bisherige_monate_nummern:
            continue
        key = (vj, monat)
        if key in daten:
            vj_monate_data.append(_berechne_monat(daten[key]))

    vj_kumuliert = {f: sum(m.get(f, 0) for m in vj_monate_data) for f in kum_felder}
    vj_kumuliert['rohertrag_marge'] = round(vj_kumuliert['rohertrag'] / vj_kumuliert['erloese'] * 100, 1) if vj_kumuliert.get('erloese') else 0

    # Delta
    delta = {}
    for f in kum_felder:
        delta[f] = kumuliert.get(f, 0) - vj_kumuliert.get(f, 0)
    delta['erloese_pct'] = round(delta['erloese'] / vj_kumuliert['erloese'] * 100, 1) if vj_kumuliert.get('erloese') else 0

    return {
        'geschaeftsjahr': geschaeftsjahr,
        'monate': monate,
        'kumuliert': kumuliert,
        'vj_kumuliert': vj_kumuliert,
        'delta_vj': delta
    }


def get_verkauf_daten(geschaeftsjahr: str = None) -> dict:
    """Fahrzeugverkauf aus Portal sales-Tabelle.

    Hinweis: Die sales-Tabelle hat keine gesellschaft-Spalte. Fahrzeugverkäufe
    werden auf Gruppenebene verwaltet. Die Daten zeigen daher immer das
    Gesamtunternehmen unabhängig von einer gesellschaft-Auswahl.
    """
    from api.db_utils import db_session

    if not geschaeftsjahr:
        geschaeftsjahr = _aktuelles_gj()

    gj_start, gj_ende = _gj_start_ende(geschaeftsjahr)
    vj = _vorjahres_gj(geschaeftsjahr)
    vj_start, vj_ende = _gj_start_ende(vj)

    with db_session() as conn:
        cursor = conn.cursor()

        # Auslieferungen pro Monat
        cursor.execute("""
            SELECT
                EXTRACT(YEAR FROM out_invoice_date)::int AS jahr,
                EXTRACT(MONTH FROM out_invoice_date)::int AS monat,
                COUNT(*) AS stueck,
                SUM(COALESCE(rechnungsbetrag_netto, 0))::bigint AS umsatz_netto,
                SUM(COALESCE(deckungsbeitrag, 0))::bigint AS db,
                SUM(CASE WHEN dealer_vehicle_type IN ('N','T') THEN 1 ELSE 0 END) AS nw,
                SUM(CASE WHEN dealer_vehicle_type = 'G' THEN 1 ELSE 0 END) AS gw
            FROM sales
            WHERE out_invoice_date >= %s AND out_invoice_date <= %s
              AND out_invoice_date IS NOT NULL
            GROUP BY 1, 2
            ORDER BY 1, 2
        """, (gj_start, gj_ende))
        auslieferungen = [dict(zip(['jahr', 'monat', 'stueck', 'umsatz_netto', 'db', 'nw', 'gw'], row)) for row in cursor.fetchall()]

        # Auftragseingang pro Monat
        cursor.execute("""
            SELECT
                EXTRACT(YEAR FROM out_sales_contract_date)::int AS jahr,
                EXTRACT(MONTH FROM out_sales_contract_date)::int AS monat,
                COUNT(*) AS auftraege,
                SUM(CASE WHEN dealer_vehicle_type IN ('N','T') THEN 1 ELSE 0 END) AS nw,
                SUM(CASE WHEN dealer_vehicle_type = 'G' THEN 1 ELSE 0 END) AS gw
            FROM sales
            WHERE out_sales_contract_date >= %s AND out_sales_contract_date <= %s
            GROUP BY 1, 2
            ORDER BY 1, 2
        """, (gj_start, gj_ende))
        auftragseingang = [dict(zip(['jahr', 'monat', 'auftraege', 'nw', 'gw'], row)) for row in cursor.fetchall()]

        # Auftragsbestand (Pipeline)
        cursor.execute("""
            SELECT
                COUNT(*) AS gesamt,
                SUM(CASE WHEN dealer_vehicle_type IN ('N','T') THEN 1 ELSE 0 END) AS nw,
                SUM(CASE WHEN dealer_vehicle_type = 'G' THEN 1 ELSE 0 END) AS gw
            FROM sales
            WHERE out_sales_contract_date IS NOT NULL
              AND out_invoice_date IS NULL
              AND out_sales_contract_date >= %s
        """, (str(gj_start.year - 1) + '-01-01',))
        pipeline_row = cursor.fetchone()
        pipeline = {'gesamt': pipeline_row[0] or 0, 'nw': pipeline_row[1] or 0, 'gw': pipeline_row[2] or 0}

        # VJ Auslieferungen (gleicher Zeitraum)
        bisherige_monate = [a['monat'] for a in auslieferungen]
        if bisherige_monate:
            # Gleiche Monate im VJ
            cursor.execute("""
                SELECT
                    COUNT(*) AS stueck,
                    SUM(COALESCE(rechnungsbetrag_netto, 0))::bigint AS umsatz_netto,
                    SUM(COALESCE(deckungsbeitrag, 0))::bigint AS db
                FROM sales
                WHERE out_invoice_date >= %s AND out_invoice_date <= %s
                  AND out_invoice_date IS NOT NULL
                  AND EXTRACT(MONTH FROM out_invoice_date)::int = ANY(%s)
            """, (vj_start, vj_ende, bisherige_monate))
            vj_row = cursor.fetchone()
            vj_auslieferungen = {'stueck': vj_row[0] or 0, 'umsatz_netto': vj_row[1] or 0, 'db': vj_row[2] or 0}
        else:
            vj_auslieferungen = {'stueck': 0, 'umsatz_netto': 0, 'db': 0}

    # Kumuliert
    kum = {
        'stueck': sum(a['stueck'] for a in auslieferungen),
        'umsatz_netto': sum(a['umsatz_netto'] for a in auslieferungen),
        'db': sum(a['db'] for a in auslieferungen),
        'nw': sum(a['nw'] for a in auslieferungen),
        'gw': sum(a['gw'] for a in auslieferungen),
    }

    return {
        'geschaeftsjahr': geschaeftsjahr,
        'auslieferungen': auslieferungen,
        'auftragseingang': auftragseingang,
        'pipeline': pipeline,
        'kumuliert': kum,
        'vj_kumuliert': vj_auslieferungen,
        'delta_stueck_pct': round((kum['stueck'] - vj_auslieferungen['stueck']) / vj_auslieferungen['stueck'] * 100, 1) if vj_auslieferungen['stueck'] else 0
    }


def get_service_daten(geschaeftsjahr: str = None, gesellschaft: str = 'autohaus') -> dict:
    """Werkstatt + Teile: Erlöse/Rohertrag aus FIBU + Aufträge aus Locosoft.

    Args:
        geschaeftsjahr: z.B. '2025/26' (default: aktuelles GJ)
        gesellschaft: 'autohaus', 'auto' oder 'gruppe' (konsolidiert = autohaus + auto)

    Hinweis: Locosoft-Auftragsdaten (orders) haben keine gesellschaft-Spalte und
    werden daher ungefiltert geladen (Gesamtunternehmen).
    """
    from api.db_utils import db_session, get_locosoft_connection

    if not geschaeftsjahr:
        geschaeftsjahr = _aktuelles_gj()

    vj = _vorjahres_gj(geschaeftsjahr)
    gj_start, gj_ende = _gj_start_ende(geschaeftsjahr)
    vj_start, vj_ende = _gj_start_ende(vj)

    # FIBU-Daten (Erlöse/WE) aus Sync-Tabelle
    with db_session() as conn:
        cursor = conn.cursor()
        if gesellschaft == 'gruppe':
            # Konsolidiert: Summe aus autohaus + auto
            cursor.execute("""
                SELECT geschaeftsjahr, monat, bereich, SUM(betrag_cent) as betrag_cent
                FROM fibu_guv_monatswerte
                WHERE geschaeftsjahr IN (%s, %s)
                  AND gesellschaft IN ('autohaus', 'auto')
                  AND bereich IN ('werkstatt_erloese', 'teile_erloese', 'we_werkstatt', 'we_teile')
                GROUP BY geschaeftsjahr, monat, bereich
            """, (geschaeftsjahr, vj))
        else:
            cursor.execute("""
                SELECT geschaeftsjahr, monat, bereich, betrag_cent
                FROM fibu_guv_monatswerte
                WHERE geschaeftsjahr IN (%s, %s)
                  AND gesellschaft = %s
                  AND bereich IN ('werkstatt_erloese', 'teile_erloese', 'we_werkstatt', 'we_teile')
            """, (geschaeftsjahr, vj, gesellschaft))
        fibu_rows = cursor.fetchall()

    # Strukturieren
    fibu = {}
    for row in fibu_rows:
        key = (row[0], row[1])
        if key not in fibu:
            fibu[key] = {}
        fibu[key][row[2]] = row[3]

    # Monate aufbauen
    monate = []
    for jahr, monat in _gj_monate(geschaeftsjahr):
        key = (geschaeftsjahr, monat)
        if key not in fibu:
            continue
        d = fibu[key]
        ws_e = d.get('werkstatt_erloese', 0)
        ws_we = d.get('we_werkstatt', 0)
        te_e = d.get('teile_erloese', 0)
        te_we = d.get('we_teile', 0)

        monate.append({
            'monat': monat, 'jahr': jahr,
            'ws_erloese': round(ws_e / 100),
            'ws_rohertrag': round((ws_e + ws_we) / 100),
            'ws_marge': round((ws_e + ws_we) / ws_e * 100, 1) if ws_e else 0,
            'teile_erloese': round(te_e / 100),
            'teile_rohertrag': round((te_e + te_we) / 100),
            'teile_marge': round((te_e + te_we) / te_e * 100, 1) if te_e else 0,
        })

    # Werkstatt-Aufträge aus Locosoft (live)
    auftraege = []
    try:
        loco_conn = get_locosoft_connection()
        if loco_conn:
            loco_cursor = loco_conn.cursor()
            loco_cursor.execute("""
                SELECT
                    EXTRACT(YEAR FROM order_date)::int AS jahr,
                    EXTRACT(MONTH FROM order_date)::int AS monat,
                    COUNT(DISTINCT number || '-' || subsidiary) AS auftraege
                FROM orders
                WHERE order_date >= %s AND order_date <= %s
                GROUP BY 1, 2
                ORDER BY 1, 2
            """, (gj_start, gj_ende))
            auftraege = [dict(zip(['jahr', 'monat', 'auftraege'], row)) for row in loco_cursor.fetchall()]
            loco_conn.close()
    except Exception as e:
        logger.warning(f"Locosoft-Aufträge nicht abrufbar: {e}")

    # VJ-Kumuliert
    bisherige_monate = [m['monat'] for m in monate]
    vj_ws_e = vj_ws_re = vj_te_e = vj_te_re = 0
    for jahr, monat in _gj_monate(vj):
        if monat not in bisherige_monate:
            continue
        key = (vj, monat)
        if key in fibu:
            d = fibu[key]
            vj_ws_e += d.get('werkstatt_erloese', 0)
            vj_ws_re += d.get('werkstatt_erloese', 0) + d.get('we_werkstatt', 0)
            vj_te_e += d.get('teile_erloese', 0)
            vj_te_re += d.get('teile_erloese', 0) + d.get('we_teile', 0)

    return {
        'geschaeftsjahr': geschaeftsjahr,
        'monate': monate,
        'auftraege': auftraege,
        'kumuliert': {
            'ws_erloese': sum(m['ws_erloese'] for m in monate),
            'ws_rohertrag': sum(m['ws_rohertrag'] for m in monate),
            'teile_erloese': sum(m['teile_erloese'] for m in monate),
            'teile_rohertrag': sum(m['teile_rohertrag'] for m in monate),
            'auftraege': sum(a['auftraege'] for a in auftraege),
        },
        'vj_kumuliert': {
            'ws_erloese': round(vj_ws_e / 100),
            'ws_rohertrag': round(vj_ws_re / 100),
            'teile_erloese': round(vj_te_e / 100),
            'teile_rohertrag': round(vj_te_re / 100),
        }
    }


def get_standzeiten_daten() -> dict:
    """Standzeiten + Finanzierungsvolumen aus fahrzeugfinanzierungen.

    Hinweis: fahrzeugfinanzierungen hat keine gesellschaft-Spalte. Fahrzeugfinanzierungen
    werden auf Gruppenebene verwaltet. Die Daten zeigen daher immer das
    Gesamtunternehmen unabhängig von einer gesellschaft-Auswahl.
    """
    from api.db_utils import db_session

    with db_session() as conn:
        cursor = conn.cursor()

        # Aktive Finanzierungen nach Bank
        cursor.execute("""
            SELECT
                COALESCE(finanzinstitut, import_quelle, 'Unbekannt') AS bank,
                COUNT(*) AS anzahl,
                SUM(COALESCE(aktueller_saldo, 0))::bigint AS saldo,
                AVG(COALESCE(alter_tage, alter_finanzierung_tage, 0))::int AS avg_standzeit,
                SUM(COALESCE(zinsen_gesamt, 0))::bigint AS zinsen
            FROM fahrzeugfinanzierungen
            WHERE aktiv = true
            GROUP BY 1
            ORDER BY 3 DESC
        """)
        nach_bank = [dict(zip(['bank', 'anzahl', 'saldo', 'avg_standzeit', 'zinsen'], row)) for row in cursor.fetchall()]

        # Standzeit-Verteilung
        cursor.execute("""
            SELECT
                CASE
                    WHEN COALESCE(alter_tage, alter_finanzierung_tage, 0) <= 30 THEN '0-30'
                    WHEN COALESCE(alter_tage, alter_finanzierung_tage, 0) <= 60 THEN '31-60'
                    WHEN COALESCE(alter_tage, alter_finanzierung_tage, 0) <= 90 THEN '61-90'
                    WHEN COALESCE(alter_tage, alter_finanzierung_tage, 0) <= 180 THEN '91-180'
                    WHEN COALESCE(alter_tage, alter_finanzierung_tage, 0) <= 365 THEN '181-365'
                    ELSE '>365'
                END AS klasse,
                COUNT(*) AS anzahl,
                SUM(COALESCE(aktueller_saldo, 0))::bigint AS saldo
            FROM fahrzeugfinanzierungen
            WHERE aktiv = true
            GROUP BY 1
            ORDER BY MIN(COALESCE(alter_tage, alter_finanzierung_tage, 0))
        """)
        verteilung = [dict(zip(['klasse', 'anzahl', 'saldo'], row)) for row in cursor.fetchall()]

    gesamt_anzahl = sum(b['anzahl'] for b in nach_bank)
    gesamt_saldo = sum(b['saldo'] for b in nach_bank)

    return {
        'nach_bank': nach_bank,
        'verteilung': verteilung,
        'gesamt': {'anzahl': gesamt_anzahl, 'saldo': gesamt_saldo}
    }


def get_eigenkapital_entwicklung(geschaeftsjahr: str = None, gesellschaft: str = 'autohaus') -> dict:
    """EK-Entwicklung: Letzter JA + laufendes Ergebnis - Entnahmen.

    Args:
        geschaeftsjahr: z.B. '2025/26' (default: aktuelles GJ)
        gesellschaft: 'autohaus', 'auto' oder 'gruppe'
    """
    from api.db_utils import db_session

    if not geschaeftsjahr:
        geschaeftsjahr = _aktuelles_gj()

    with db_session() as conn:
        cursor = conn.cursor()

        # Letzter JA (Vorjahr)
        vj = _vorjahres_gj(geschaeftsjahr)
        cursor.execute("""
            SELECT eigenkapital, ek_quote, jahresergebnis
            FROM jahresabschluss_daten
            WHERE geschaeftsjahr = %s AND gesellschaft = %s
        """, (vj, gesellschaft))
        ja_row = cursor.fetchone()

        ek_letzter_ja = ja_row[0] if ja_row else None

        # Laufendes Ergebnis: bereinigten EBT aus GuV verwenden (unvollst. Monat korrigiert)
        pass  # wird unten aus get_guv_daten geholt

    guv = get_guv_daten(geschaeftsjahr, gesellschaft=gesellschaft)
    laufendes_ergebnis = guv['kumuliert'].get('ebt', 0)

    with db_session() as conn:
        cursor = conn.cursor()

        # Entnahmen
        if gesellschaft == 'gruppe':
            cursor.execute("""
                SELECT SUM(betrag_cent)
                FROM fibu_guv_monatswerte
                WHERE geschaeftsjahr = %s AND bereich = 'entnahmen'
                  AND gesellschaft IN ('autohaus', 'auto')
            """, (geschaeftsjahr,))
        else:
            cursor.execute("""
                SELECT SUM(betrag_cent)
                FROM fibu_guv_monatswerte
                WHERE geschaeftsjahr = %s AND bereich = 'entnahmen'
                  AND gesellschaft = %s
            """, (geschaeftsjahr, gesellschaft))
        ent_row = cursor.fetchone()
        entnahmen = round(abs(ent_row[0] or 0) / 100) if ent_row else 0

        # Historische EK-Zeitreihe
        cursor.execute("""
            SELECT geschaeftsjahr, eigenkapital, ek_quote
            FROM jahresabschluss_daten
            WHERE gesellschaft = %s
            ORDER BY geschaeftsjahr
        """, (gesellschaft,))
        zeitreihe = [dict(zip(['geschaeftsjahr', 'eigenkapital', 'ek_quote'], row)) for row in cursor.fetchall()]

    # EK-Schätzung: EK_JA + laufendes_ergebnis - Entnahmen (in TEUR)
    ek_schaetzung = None
    if ek_letzter_ja is not None:
        ek_schaetzung = round(float(ek_letzter_ja) + laufendes_ergebnis / 1000 - entnahmen / 1000, 1)
    elif gesellschaft == 'gruppe':
        # Fallback: Gruppe-EK als Summe der Einzelgesellschaften
        ek_ah = get_eigenkapital_entwicklung(geschaeftsjahr, gesellschaft='autohaus')
        ek_ag = get_eigenkapital_entwicklung(geschaeftsjahr, gesellschaft='auto')
        if ek_ah.get('ek_schaetzung_teur') is not None and ek_ag.get('ek_schaetzung_teur') is not None:
            ek_schaetzung = round(ek_ah['ek_schaetzung_teur'] + ek_ag['ek_schaetzung_teur'], 1)
            ek_letzter_ja_sum = (ek_ah.get('ek_letzter_ja') or 0) + (ek_ag.get('ek_letzter_ja') or 0)
            ek_letzter_ja = ek_letzter_ja_sum
            # Zeitreihe aus Summe beider Gesellschaften aufbauen
            ah_zr = {z['geschaeftsjahr']: z for z in ek_ah.get('zeitreihe', [])}
            ag_zr = {z['geschaeftsjahr']: z for z in ek_ag.get('zeitreihe', [])}
            alle_gjs = sorted(set(list(ah_zr.keys()) + list(ag_zr.keys())))
            zeitreihe = []
            for gj_key in alle_gjs:
                ek_sum = (float(ah_zr[gj_key]['eigenkapital']) if gj_key in ah_zr and ah_zr[gj_key]['eigenkapital'] else 0) + \
                         (float(ag_zr[gj_key]['eigenkapital']) if gj_key in ag_zr and ag_zr[gj_key]['eigenkapital'] else 0)
                zeitreihe.append({'geschaeftsjahr': gj_key, 'eigenkapital': round(ek_sum, 1), 'ek_quote': None})
            logger.info(f"  Gruppe-EK als Summe: AH {ek_ah['ek_schaetzung_teur']} + AG {ek_ag['ek_schaetzung_teur']} = {ek_schaetzung}")

    return {
        'ek_letzter_ja': float(ek_letzter_ja) if ek_letzter_ja else None,
        'laufendes_ergebnis_eur': laufendes_ergebnis,
        'entnahmen_eur': entnahmen,
        'ek_schaetzung_teur': ek_schaetzung,
        'zeitreihe': zeitreihe,
        'basis_gj': vj
    }


def get_prognose(geschaeftsjahr: str = None, gesellschaft: str = 'autohaus') -> dict:
    """Lineare Hochrechnung auf 12 Monate.

    Args:
        geschaeftsjahr: z.B. '2025/26' (default: aktuelles GJ)
        gesellschaft: 'autohaus', 'auto' oder 'gruppe'
    """
    if not geschaeftsjahr:
        geschaeftsjahr = _aktuelles_gj()

    guv = get_guv_daten(geschaeftsjahr, gesellschaft=gesellschaft)
    # Fahrzeugverkauf hat keine gesellschaft-Spalte → zeigt Gesamtunternehmen
    verkauf = get_verkauf_daten(geschaeftsjahr)

    anz_monate = guv['kumuliert'].get('anzahl_monate', 0)
    if anz_monate == 0:
        return {'hinweis': 'Noch keine Daten für Hochrechnung'}

    faktor = 12 / anz_monate

    return {
        'methode': 'linear',
        'basis_monate': anz_monate,
        'umsatz_prognose': round(guv['kumuliert']['erloese'] * faktor),
        'ebit_prognose': round(guv['kumuliert']['ebit'] * faktor),
        'ebt_prognose': round(guv['kumuliert']['ebt'] * faktor),
        'fz_stueck_prognose': round(verkauf['kumuliert']['stueck'] * faktor),
    }


def get_mehrjahresvergleich(gesellschaft: str = 'autohaus') -> list:
    """Alle importierten Jahresabschlüsse als Zeitreihe.

    Args:
        gesellschaft: 'autohaus', 'auto' oder 'gruppe'
    """
    from api.db_utils import db_session

    with db_session() as conn:
        cursor = conn.cursor()

        if gesellschaft == 'gruppe':
            # Summe aus autohaus + auto pro GJ
            cursor.execute("""
                SELECT geschaeftsjahr, stichtag,
                    SUM(bilanzsumme) as bilanzsumme,
                    SUM(eigenkapital) as eigenkapital,
                    NULL as ek_quote,
                    SUM(umsatz) as umsatz,
                    NULL as rohertrag_pct,
                    SUM(personalaufwand) as personalaufwand,
                    SUM(abschreibungen) as abschreibungen,
                    SUM(zinsergebnis) as zinsergebnis,
                    SUM(betriebsergebnis) as betriebsergebnis,
                    SUM(jahresergebnis) as jahresergebnis,
                    SUM(cashflow_geschaeft) as cashflow_geschaeft,
                    SUM(cashflow_invest) as cashflow_invest,
                    SUM(cashflow_finanz) as cashflow_finanz,
                    SUM(finanzmittel_jahresende) as finanzmittel_jahresende,
                    SUM(verbindlichkeiten) as verbindlichkeiten,
                    SUM(rueckstellungen) as rueckstellungen
                FROM jahresabschluss_daten
                WHERE gesellschaft IN ('autohaus', 'auto')
                GROUP BY geschaeftsjahr, stichtag
                HAVING COUNT(*) = 2
                ORDER BY geschaeftsjahr DESC
            """)
        else:
            cursor.execute("""
                SELECT geschaeftsjahr, stichtag, bilanzsumme, eigenkapital, ek_quote,
                       umsatz, rohertrag_pct, personalaufwand, abschreibungen,
                       zinsergebnis, betriebsergebnis, jahresergebnis,
                       cashflow_geschaeft, cashflow_invest, cashflow_finanz,
                       finanzmittel_jahresende, verbindlichkeiten, rueckstellungen
                FROM jahresabschluss_daten
                WHERE gesellschaft = %s
                ORDER BY geschaeftsjahr DESC
            """, (gesellschaft,))

        spalten = ['geschaeftsjahr', 'stichtag', 'bilanzsumme', 'eigenkapital', 'ek_quote',
                   'umsatz', 'rohertrag_pct', 'personalaufwand', 'abschreibungen',
                   'zinsergebnis', 'betriebsergebnis', 'jahresergebnis',
                   'cashflow_geschaeft', 'cashflow_invest', 'cashflow_finanz',
                   'finanzmittel_jahresende', 'verbindlichkeiten', 'rueckstellungen']

        rows = [dict(zip(spalten, row)) for row in cursor.fetchall()]

        # Recalculate EK-Quote for Gruppe (since we SUM'd the components)
        if gesellschaft == 'gruppe':
            for row in rows:
                if row.get('eigenkapital') is not None and row.get('bilanzsumme') and row['bilanzsumme'] != 0:
                    row['ek_quote'] = row['eigenkapital'] / row['bilanzsumme'] * 100
                else:
                    row['ek_quote'] = None

        return rows


def get_gesamtbild(geschaeftsjahr: str = None, gesellschaft: str = 'autohaus') -> dict:
    """Orchestriert alle Datenquellen zu einem Gesamtpaket (SSOT).

    Args:
        geschaeftsjahr: z.B. '2025/26' (default: aktuelles GJ)
        gesellschaft: 'autohaus', 'auto' oder 'gruppe'
    """
    if not geschaeftsjahr:
        geschaeftsjahr = _aktuelles_gj()

    return {
        'geschaeftsjahr': geschaeftsjahr,
        'gesellschaft': gesellschaft,
        'stichtag': str(date.today()),
        'guv': get_guv_daten(geschaeftsjahr, gesellschaft=gesellschaft),
        # Fahrzeugverkauf und Standzeiten haben keine gesellschaft-Spalte → Gesamtunternehmen
        'verkauf': get_verkauf_daten(geschaeftsjahr),
        'service': get_service_daten(geschaeftsjahr, gesellschaft=gesellschaft),
        'standzeiten': get_standzeiten_daten(),
        'eigenkapital': get_eigenkapital_entwicklung(geschaeftsjahr, gesellschaft=gesellschaft),
        'prognose': get_prognose(geschaeftsjahr, gesellschaft=gesellschaft),
        'mehrjahresvergleich': get_mehrjahresvergleich(gesellschaft=gesellschaft),
    }
