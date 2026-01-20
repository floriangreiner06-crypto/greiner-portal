"""
Werkstatt API - Leistungsübersicht
==================================
REST API für Werkstatt-Mechaniker-Leistungsdaten

Endpoints:
- GET /api/werkstatt/leistung - Mechaniker-Leistungsdaten
- GET /api/werkstatt/mechaniker/<nr> - Detail für einen Mechaniker
- GET /api/werkstatt/trend - Leistungsgrad-Trend über Zeit

Erstellt: 2025-12-04 (TAG 90)
Updated: TAG 117 - Migration auf db_session
Updated: TAG 136 - PostgreSQL-kompatibel
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from flask_login import login_required
import logging

# Zentrale DB-Utilities (TAG117, TAG136: PostgreSQL-kompatibel)
from api.db_utils import db_session, row_to_dict, rows_to_list
from api.db_connection import convert_placeholders, get_db_type

# SSOT: KPI-Berechnungen (TAG 181)
from utils.kpi_definitions import berechne_anwesenheitsgrad_fuer_mechaniker_liste

logger = logging.getLogger(__name__)

werkstatt_api = Blueprint('werkstatt_api', __name__, url_prefix='/api/werkstatt')


def get_date_range(zeitraum, von=None, bis=None):
    """Berechnet Datumsbereich basierend auf Zeitraum-Parameter"""
    heute = datetime.now().date()

    if zeitraum == 'heute':
        return heute.isoformat(), heute.isoformat()
    elif zeitraum == 'woche':
        montag = heute - timedelta(days=heute.weekday())
        return montag.isoformat(), heute.isoformat()
    elif zeitraum == 'monat':
        start = heute.replace(day=1)
        return start.isoformat(), heute.isoformat()
    elif zeitraum == 'vormonat':
        erster_aktuell = heute.replace(day=1)
        letzter_vormonat = erster_aktuell - timedelta(days=1)
        erster_vormonat = letzter_vormonat.replace(day=1)
        return erster_vormonat.isoformat(), letzter_vormonat.isoformat()
    elif zeitraum == 'quartal':
        quartal_start_monat = ((heute.month - 1) // 3) * 3 + 1
        start = heute.replace(month=quartal_start_monat, day=1)
        return start.isoformat(), heute.isoformat()
    elif zeitraum == 'jahr':
        start = heute.replace(month=1, day=1)
        return start.isoformat(), heute.isoformat()
    elif zeitraum == 'custom' and von and bis:
        return von, bis
    else:
        start = heute.replace(day=1)
        return start.isoformat(), heute.isoformat()


@werkstatt_api.route('/leistung', methods=['GET'])
def get_leistung():
    """GET /api/werkstatt/leistung - Mechaniker-Leistungsdaten"""
    try:
        zeitraum = request.args.get('zeitraum', 'monat')
        von = request.args.get('von')
        bis = request.args.get('bis')
        betrieb = request.args.get('betrieb', 'alle')
        sort = request.args.get('sort', 'leistungsgrad')
        inkl_ehemalige = request.args.get('inkl_ehemalige', '0') == '1'

        datum_von, datum_bis = get_date_range(zeitraum, von, bis)
        
        # TAG 190: Verwende WerkstattData.get_mechaniker_leistung() für Locosoft-konforme Berechnung
        from api.werkstatt_data import WerkstattData
        from datetime import datetime
        
        betrieb_nr = None
        if betrieb and betrieb != 'alle':
            betrieb_nr = int(betrieb)
        
        von_date = datetime.fromisoformat(datum_von).date()
        bis_date = datetime.fromisoformat(datum_bis).date()
        
        data = WerkstattData.get_mechaniker_leistung(
            von=von_date,
            bis=bis_date,
            betrieb=betrieb_nr,
            inkl_ehemalige=inkl_ehemalige,
            sort_by=sort
        )
        
        # Konvertiere zu altem Format für Frontend-Kompatibilität
        # SSOT TAG 196: Alle Werte werden von der API berechnet, Dashboard zeigt nur an!
        #              Keine Berechnungen mehr im Dashboard - alle Werte in benötigter Einheit zurückgeben
        mechaniker = []
        for m in data['mechaniker']:
            vorgabezeit_min = m.get('vorgabezeit', 0)  # AW-Anteil in Minuten (immer vorhanden)
            mechaniker.append({
                'mechaniker_nr': m['mechaniker_nr'],
                'name': m['name'],
                'ist_aktiv': m['ist_aktiv'],
                'tage': m['tage'],
                'auftraege': m['auftraege'],
                'stempelzeit': m['stempelzeit'],  # St-Anteil in Minuten (für interne Berechnungen)
                'anwesenheit': m['anwesenheit'],  # Echte Anwesenheit in Minuten (für interne Berechnungen)
                'vorgabezeit': vorgabezeit_min,  # AW-Anteil in Minuten (für interne Berechnungen)
                'stempelzeit_std': round(m['stempelzeit'] / 60, 1),  # St-Anteil in Stunden (SSOT - für Dashboard-Anzeige)
                'anwesenheit_std': round(m['anwesenheit'] / 60, 1),  # Anwesenheit in Stunden (SSOT - für Dashboard-Anzeige)
                'vorgabezeit_std': round(vorgabezeit_min / 60, 1),  # AW-Anteil in Stunden (SSOT - für Dashboard-Anzeige)
                'aw': m['aw'],  # AW-Einheiten (SSOT - von API berechnet)
                'umsatz': m['umsatz'],
                'leistungsgrad': m['leistungsgrad'],
                'produktivitaet': m['produktivitaet']
            })
        
        # Sortierung (falls nicht bereits sortiert)
        if sort == 'leistungsgrad':
            mechaniker.sort(key=lambda x: x['leistungsgrad'] or 0, reverse=True)
        elif sort == 'stempelzeit':
            mechaniker.sort(key=lambda x: x['stempelzeit'] or 0, reverse=True)
        elif sort == 'aw':
            mechaniker.sort(key=lambda x: x['aw'] or 0, reverse=True)
        elif sort == 'auftraege':
            mechaniker.sort(key=lambda x: x['auftraege'] or 0, reverse=True)

        # Gesamt-KPIs aus data verwenden
        gesamt = data.get('gesamt', {})
        anzahl_tage = data.get('anzahl_tage', 0)

        # Anwesenheitsgrad für Mechaniker-Liste berechnen (TAG 181 - SSOT)
        from utils.kpi_definitions import berechne_anwesenheitsgrad_fuer_mechaniker_liste
        gesamt_anwesenheitsgrad, mechaniker = berechne_anwesenheitsgrad_fuer_mechaniker_liste(mechaniker)
        
        # FIX TAG 196: Gesamt-KPIs für die ANGEZEIGTEN Mechaniker berechnen, nicht für alle!
        # Das Dashboard zeigt nur die Top 10 (oder gefilterten) Mechaniker,
        # daher müssen die Gesamtwerte für diese Mechaniker berechnet werden.
        gesamt_auftraege = sum(m.get('auftraege', 0) for m in mechaniker)
        gesamt_stempelzeit = sum(m.get('stempelzeit', 0) for m in mechaniker)  # St-Anteil in Minuten
        gesamt_anwesenheit = sum(m.get('anwesenheit', 0) for m in mechaniker)  # Echte Anwesenheit in Minuten
        gesamt_aw = sum(m.get('aw', 0) for m in mechaniker)  # AW-Einheiten
        gesamt_vorgabezeit = sum(m.get('vorgabezeit', m.get('aw', 0) * 6.0) for m in mechaniker)  # AW-Anteil in Minuten
        gesamt_umsatz = sum(m.get('umsatz', 0) for m in mechaniker)
        
        # Gesamt-Leistungsgrad und Produktivität für angezeigte Mechaniker berechnen
        if gesamt_stempelzeit > 0 and gesamt_vorgabezeit > 0:
            gesamt_leistungsgrad = round(gesamt_vorgabezeit / gesamt_stempelzeit * 100, 1)
        else:
            gesamt_leistungsgrad = None
            
        if gesamt_stempelzeit > 0 and gesamt_anwesenheit > 0:
            if gesamt_stempelzeit > gesamt_anwesenheit:
                gesamt_produktivitaet = 100.0  # Cap auf 100%
            else:
                gesamt_produktivitaet = round(gesamt_stempelzeit / gesamt_anwesenheit * 100, 1)
        else:
            gesamt_produktivitaet = None

        with db_session() as conn:
            cursor = conn.cursor()

            # Trend-Daten (letzte 14 Tage)
            # TAG 136: date('now', '-14 days') -> CURRENT_DATE - INTERVAL für PostgreSQL
            if get_db_type() == 'postgresql':
                datum_filter = "datum >= CURRENT_DATE - INTERVAL '14 days'"
            else:
                datum_filter = "datum >= date('now', '-14 days')"
            trend_query = f"""
                SELECT
                    datum,
                    ROUND(SUM(vorgabezeit_aw) * 6.0 / NULLIF(SUM(stempelzeit_min), 0) * 100, 1) as leistungsgrad
                FROM werkstatt_leistung_daily
                WHERE {datum_filter}
            """
            trend_params = []
            if betrieb and betrieb != 'alle':
                betrieb_nr = int(betrieb)
                if betrieb_nr == 1:
                    trend_query += " AND (betrieb_nr = 1 OR betrieb_nr IS NULL OR betrieb_nr = 0)"
                else:
                    trend_query += " AND betrieb_nr = %s"
                    trend_params.append(betrieb_nr)
            trend_query += " GROUP BY datum ORDER BY datum"

            cursor.execute(convert_placeholders(trend_query), trend_params)
            trend = rows_to_list(cursor.fetchall())

            # SOLL-KAPAZITÄT MIT ABWESENHEITEN
            AW_PRO_TAG = 80

            arbeitstage = 0
            von_date = datetime.strptime(datum_von, '%Y-%m-%d').date()
            bis_date = datetime.strptime(datum_bis, '%Y-%m-%d').date()
            current = von_date
            while current <= bis_date:
                if current.weekday() < 5:
                    arbeitstage += 1
                current += timedelta(days=1)

            # TAG 136: is_latest_record ist BOOLEAN in PostgreSQL, INTEGER in SQLite
            is_latest_check = "e.is_latest_record = true" if get_db_type() == 'postgresql' else "e.is_latest_record = 1"
            mech_query = f"""
                SELECT COUNT(DISTINCT e.employee_number) as anzahl
                FROM loco_employees e
                JOIN loco_employees_group_mapping g ON e.employee_number = g.employee_number
                WHERE g.grp_code = 'MON'
                AND {is_latest_check}
                AND (e.leave_date IS NULL OR e.leave_date > ?)
                AND e.employee_number NOT IN (
                    SELECT employee_number FROM loco_employees_group_mapping
                    WHERE grp_code IN ('A-W', 'A-L', 'A-K')
                )
            """
            mech_params = [datum_bis]
            if betrieb and betrieb != 'alle':
                betrieb_nr = int(betrieb)
                if betrieb_nr == 1:
                    mech_query += " AND (e.subsidiary = 1 OR e.subsidiary IS NULL OR e.subsidiary = 0)"
                else:
                    mech_query += " AND e.subsidiary = %s"
                    mech_params.append(betrieb_nr)

            cursor.execute(convert_placeholders(mech_query), mech_params)
            mech_row = cursor.fetchone()
            basis_mechaniker = (row_to_dict(mech_row) if mech_row else {}).get('anzahl', 0) or 0

            abwesenheit_query = f"""
                SELECT COUNT(*) as tage
                FROM loco_absence_calendar ac
                JOIN loco_employees e ON ac.employee_number = e.employee_number
                JOIN loco_employees_group_mapping g ON e.employee_number = g.employee_number
                WHERE ac.date >= ? AND ac.date <= ?
                AND g.grp_code = 'MON'
                AND {is_latest_check}
                AND e.employee_number NOT IN (
                    SELECT employee_number FROM loco_employees_group_mapping
                    WHERE grp_code IN ('A-W', 'A-L', 'A-K')
                )
            """
            abwesenheit_params = [datum_von, datum_bis]
            if betrieb and betrieb != 'alle':
                betrieb_nr = int(betrieb)
                if betrieb_nr == 1:
                    abwesenheit_query += " AND (e.subsidiary = 1 OR e.subsidiary IS NULL OR e.subsidiary = 0)"
                else:
                    abwesenheit_query += " AND e.subsidiary = %s"
                    abwesenheit_params.append(betrieb_nr)

            try:
                cursor.execute(convert_placeholders(abwesenheit_query), abwesenheit_params)
                abw_row = cursor.fetchone()
                abwesenheitstage = (row_to_dict(abw_row) if abw_row else {}).get('tage', 0) or 0
            except:
                abwesenheitstage = 0

            soll_kapazitaet_aw = (arbeitstage * basis_mechaniker * AW_PRO_TAG) - (abwesenheitstage * AW_PRO_TAG)
            soll_kapazitaet_aw = max(0, soll_kapazitaet_aw)
            vorgabe_aw_soll = soll_kapazitaet_aw

            # SVS: Durchschnittlicher Verrechnungssatz (extern, ohne Karosserie, 6 Monate rollierend)
            from api.werkstatt_data import berechne_durchschnittlichen_verrechnungssatz
            
            betrieb_nr = None
            if betrieb and betrieb != 'alle' and betrieb != '1,2':
                try:
                    betrieb_nr = int(betrieb)
                except:
                    betrieb_nr = None
            
            svs_info = berechne_durchschnittlichen_verrechnungssatz(betrieb=betrieb_nr, monate=6)
            svs = svs_info.get('svs', 119.0)
            svs_quelle = svs_info.get('quelle', 'fallback')

            gesamt_effizienz = round(gesamt_leistungsgrad * gesamt_produktivitaet / 100, 1) if gesamt_leistungsgrad and gesamt_produktivitaet else 0
            gesamt_stempelzeit_std = gesamt_stempelzeit / 60 if gesamt_stempelzeit else 0
            # FIX TAG 196: verlorene_std basiert auf Vorgabezeit, nicht Stempelzeit
            # verlorene_std = (Vorgabezeit - Stempelzeit) wenn Leistungsgrad < 100%
            gesamt_vorgabezeit_std = (gesamt.get('vorgabezeit', gesamt_aw * 6.0) / 60) if gesamt_aw else 0
            verlorene_std = gesamt_vorgabezeit_std * (1 - gesamt_leistungsgrad / 100) if gesamt_leistungsgrad else 0
            entgangener_umsatz = verlorene_std * svs
            realisierter_svs = round(gesamt_umsatz / gesamt_stempelzeit_std, 2) if gesamt_stempelzeit_std > 0 and gesamt_umsatz else svs
            std_pro_durchgang = round(gesamt_stempelzeit_std / gesamt_auftraege, 2) if gesamt_auftraege > 0 else 0

            # TAG 199: Benchmark-Vergleiche (SSOT: utils.kpi_definitions)
            from utils.kpi_definitions import vergleiche_mit_markt
            benchmarks = {
                'leistungsgrad': vergleiche_mit_markt(gesamt_leistungsgrad, 'leistungsgrad'),
                'produktivitaet': vergleiche_mit_markt(gesamt_produktivitaet, 'auslastungsgrad'),  # Produktivität = Auslastungsgrad
                'anwesenheitsgrad': vergleiche_mit_markt(gesamt_anwesenheitsgrad, 'anwesenheitsgrad'),
                'effizienz': vergleiche_mit_markt(gesamt_effizienz, 'effizienz'),
                'stundensatz': vergleiche_mit_markt(realisierter_svs, 'stundensatz_durchschnitt'),
                'stunden_pro_durchgang': vergleiche_mit_markt(std_pro_durchgang, 'stunden_pro_durchgang'),
            }

        return jsonify({
            'success': True,
            'zeitraum': {'von': datum_von, 'bis': datum_bis, 'label': zeitraum},
            'betrieb': betrieb,
            'mechaniker': mechaniker,
            'anzahl_mechaniker': len(mechaniker),
            'anzahl_tage': anzahl_tage,
            'gesamt_auftraege': gesamt_auftraege,
            'gesamt_stempelzeit': gesamt_stempelzeit,
            'gesamt_anwesenheit': gesamt_anwesenheit,
            'gesamt_aw': gesamt_aw,
            'gesamt_umsatz': gesamt_umsatz,
            'gesamt_leistungsgrad': gesamt_leistungsgrad,
            'gesamt_produktivitaet': gesamt_produktivitaet,
            'avg_std_pro_tag': round(gesamt_stempelzeit / anzahl_tage / 60, 1) if anzahl_tage > 0 else 0,
            'avg_auftraege_pro_tag': round(gesamt_auftraege / anzahl_tage, 1) if anzahl_tage > 0 else 0,
            'gesamt': {
                'leistungsgrad': gesamt_leistungsgrad,
                'produktivitaet': gesamt_produktivitaet,
                'anwesenheitsgrad': gesamt_anwesenheitsgrad,  # TAG 181
                'effizienz': gesamt_effizienz,
                'stempelzeit': gesamt_stempelzeit,
                'anwesenheit': gesamt_anwesenheit,
                'vorgabezeit': gesamt_vorgabezeit,  # FIX TAG 196: AW-Anteil in Minuten (NEU!)
                'auftraege': gesamt_auftraege,
                'aw': gesamt_aw,
                'umsatz': round(gesamt_umsatz, 2),
                'svs': svs,
                'svs_quelle': svs_quelle,
                'svs_zeitraum': svs_info.get('zeitraum', {}),
                'realisierter_svs': realisierter_svs,
                'bezahlt_h': round(sum(m.get('bezahlt_h', 0) for m in mechaniker), 1),  # TAG 181
                'anwesend_h': round(sum(m.get('anwesend_h', 0) for m in mechaniker), 1),  # TAG 181
                'verlorene_std': round(verlorene_std, 1),
                'entgangener_umsatz': round(entgangener_umsatz, 2),
                'std_pro_durchgang': std_pro_durchgang,
                'tage': anzahl_tage,
                'soll_kapazitaet_aw': soll_kapazitaet_aw,
                'vorgabe_aw_soll': vorgabe_aw_soll,
                'basis_mechaniker': basis_mechaniker,
                'arbeitstage': arbeitstage,
                'abwesenheitstage': abwesenheitstage
            },
            'benchmarks': benchmarks,  # TAG 199: Marktvergleiche
            'trend': trend
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@werkstatt_api.route('/mechaniker/<int:mechaniker_nr>', methods=['GET'])
def get_mechaniker_detail(mechaniker_nr):
    """GET /api/werkstatt/mechaniker/<nr> - Detail für einen Mechaniker"""
    try:
        zeitraum = request.args.get('zeitraum', 'monat')
        von = request.args.get('von')
        bis = request.args.get('bis')

        datum_von, datum_bis = get_date_range(zeitraum, von, bis)

        with db_session() as conn:
            cursor = conn.cursor()

            cursor.execute(convert_placeholders("""
                SELECT
                    datum,
                    anzahl_auftraege as auftraege,
                    stempelzeit_min as stempelzeit,
                    vorgabezeit_aw as aw,
                    leistungsgrad,
                    umsatz
                FROM werkstatt_leistung_daily
                WHERE mechaniker_nr = %s
                AND datum >= ? AND datum <= ?
                ORDER BY datum DESC
            """), [mechaniker_nr, datum_von, datum_bis])
            tage = rows_to_list(cursor.fetchall())

            # TAG 188: Aufträge nach Mechaniker-Nr filtern (JOIN mit loco_labours)
            # WICHTIG: Nur Aufträge mit Stempelzeit > 0 anzeigen
            # Nur Aufträge, bei denen dieser Mechaniker tatsächlich gearbeitet hat (via loco_labours)
            cursor.execute(convert_placeholders("""
                SELECT DISTINCT
                    a.rechnungs_datum,
                    a.rechnungs_nr,
                    a.auftrags_nr,
                    a.kennzeichen,
                    a.summe_aw,
                    a.summe_stempelzeit_min,
                    a.leistungsgrad,
                    a.lohn_netto
                FROM werkstatt_auftraege_abgerechnet a
                INNER JOIN loco_labours l ON a.rechnungs_nr = l.invoice_number
                    AND a.rechnungs_typ = l.invoice_type
                    AND l.mechanic_no = %s
                    AND l.mechanic_no IS NOT NULL
                WHERE a.rechnungs_datum >= ? AND a.rechnungs_datum <= ?
                    AND a.summe_stempelzeit_min > 0
                ORDER BY a.rechnungs_datum DESC
                LIMIT 200
            """), [mechaniker_nr, datum_von, datum_bis])
            auftraege = rows_to_list(cursor.fetchall())

            return jsonify({
                'success': True,
                'mechaniker_nr': mechaniker_nr,
                'tage': tage,
                'auftraege': auftraege
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@werkstatt_api.route('/schlechteste-auftraege', methods=['GET'])
def get_schlechteste_auftraege():
    """GET /api/werkstatt/schlechteste-auftraege"""
    try:
        zeitraum = request.args.get('zeitraum', 'monat')
        von = request.args.get('von')
        bis = request.args.get('bis')
        betrieb = request.args.get('betrieb', 'alle')
        limit = request.args.get('limit', 3, type=int)
        min_stempelzeit = request.args.get('min_stempelzeit', 30, type=int)

        datum_von, datum_bis = get_date_range(zeitraum, von, bis)

        with db_session() as conn:
            cursor = conn.cursor()

            query = """
                WITH auftraege_mit_mechaniker AS (
                    SELECT DISTINCT
                        a.rechnungs_datum,
                        a.rechnungs_nr,
                        a.auftrags_nr,
                        a.kennzeichen,
                        a.betrieb,
                        a.summe_aw,
                        a.summe_stempelzeit_min,
                        a.leistungsgrad,
                        a.lohn_netto,
                        l.mechanic_no as mechaniker_nr,
                        e.name as mechaniker_name
                    FROM werkstatt_auftraege_abgerechnet a
                    JOIN loco_labours l ON a.rechnungs_nr = l.invoice_number
                        AND a.rechnungs_typ = l.invoice_type
                    LEFT JOIN loco_employees e ON l.mechanic_no = e.employee_number
                        AND e.is_latest_record = {'true' if get_db_type() == 'postgresql' else '1'}
                    WHERE a.rechnungs_datum >= ? AND a.rechnungs_datum <= ?
                    AND a.leistungsgrad IS NOT NULL
                    AND a.leistungsgrad > 0
                    AND a.leistungsgrad < 500
                    AND a.summe_stempelzeit_min >= ?
                    AND l.mechanic_no IS NOT NULL
                    AND l.mechanic_no > 0
            """
            params = [datum_von, datum_bis, min_stempelzeit]

            if betrieb and betrieb != 'alle':
                query += " AND a.betrieb = %s"
                params.append(int(betrieb))

            query += """
                ),
                ranked AS (
                    SELECT *,
                        ROW_NUMBER() OVER (PARTITION BY mechaniker_nr ORDER BY leistungsgrad ASC) as rang
                    FROM auftraege_mit_mechaniker
                )
                SELECT mechaniker_nr, mechaniker_name, rechnungs_datum, rechnungs_nr, auftrags_nr,
                       kennzeichen, summe_aw, summe_stempelzeit_min, leistungsgrad, lohn_netto, rang
                FROM ranked WHERE rang <= ?
                ORDER BY mechaniker_name, rang
            """
            params.append(limit)

            cursor.execute(convert_placeholders(query), params)
            rows = rows_to_list(cursor.fetchall())

            mechaniker_auftraege = {}
            for row in rows:
                mech_nr = row['mechaniker_nr']
                if mech_nr not in mechaniker_auftraege:
                    mechaniker_auftraege[mech_nr] = {
                        'mechaniker_nr': mech_nr,
                        'mechaniker_name': row['mechaniker_name'],
                        'auftraege': []
                    }
                mechaniker_auftraege[mech_nr]['auftraege'].append({
                    'rang': row['rang'],
                    'datum': row['rechnungs_datum'],
                    'rechnungs_nr': row['rechnungs_nr'],
                    'auftrags_nr': row['auftrags_nr'],
                    'kennzeichen': row['kennzeichen'],
                    'aw': row['summe_aw'],
                    'stempelzeit': row['summe_stempelzeit_min'],
                    'leistungsgrad': row['leistungsgrad'],
                    'lohn': row['lohn_netto']
                })

            return jsonify({
                'success': True,
                'zeitraum': {'von': datum_von, 'bis': datum_bis},
                'min_stempelzeit': min_stempelzeit,
                'limit_pro_mechaniker': limit,
                'mechaniker': list(mechaniker_auftraege.values())
            })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@werkstatt_api.route('/trend', methods=['GET'])
def get_trend():
    """GET /api/werkstatt/trend - Leistungsgrad-Trend"""
    try:
        tage = request.args.get('tage', 30, type=int)
        betrieb = request.args.get('betrieb', 'alle')

        with db_session() as conn:
            cursor = conn.cursor()

            AW_PRO_TAG = 80

            # TAG 136: date('now', '-X days') -> CURRENT_DATE - INTERVAL für PostgreSQL
            if get_db_type() == 'postgresql':
                datum_filter = f"datum >= CURRENT_DATE - INTERVAL '{tage} days'"
                params = []
            else:
                datum_filter = "datum >= date('now', ?)"
                params = [f'-{tage} days']

            query = f"""
                SELECT
                    datum,
                    COUNT(DISTINCT mechaniker_nr) as mechaniker,
                    SUM(anzahl_auftraege) as auftraege,
                    SUM(stempelzeit_min) as stempelzeit,
                    SUM(anwesenheit_min) as anwesenheit,
                    SUM(vorgabezeit_aw) as aw,
                    ROUND(SUM(vorgabezeit_aw) * 6.0 / NULLIF(SUM(stempelzeit_min), 0) * 100, 1) as leistungsgrad,
                    ROUND(SUM(stempelzeit_min) / NULLIF(SUM(anwesenheit_min), 0) * 100, 1) as auslastung
                FROM werkstatt_leistung_daily
                WHERE {datum_filter}
            """

            if betrieb and betrieb != 'alle':
                betrieb_nr = int(betrieb)
                if betrieb_nr == 1:
                    query += " AND (betrieb_nr = 1 OR betrieb_nr IS NULL OR betrieb_nr = 0)"
                else:
                    query += " AND betrieb_nr = %s"
                    params.append(betrieb_nr)

            query += " GROUP BY datum ORDER BY datum"

            cursor.execute(convert_placeholders(query), params)
            trend_raw = rows_to_list(cursor.fetchall())

            # Basis-Mechaniker zählen - TAG 136: PostgreSQL-kompatibel
            is_latest = "true" if get_db_type() == 'postgresql' else "1"
            leave_check = "CURRENT_DATE" if get_db_type() == 'postgresql' else "date('now')"
            mech_query = f"""
                SELECT COUNT(DISTINCT e.employee_number) as anzahl
                FROM loco_employees e
                JOIN loco_employees_group_mapping g ON e.employee_number = g.employee_number
                WHERE g.grp_code = 'MON'
                AND e.is_latest_record = {is_latest}
                AND (e.leave_date IS NULL OR e.leave_date > {leave_check})
                AND e.employee_number NOT IN (
                    SELECT employee_number FROM loco_employees_group_mapping
                    WHERE grp_code IN ('A-W', 'A-L', 'A-K')
                )
            """
            mech_params = []
            if betrieb and betrieb != 'alle':
                betrieb_nr = int(betrieb)
                if betrieb_nr == 1:
                    mech_query += " AND (e.subsidiary = 1 OR e.subsidiary IS NULL OR e.subsidiary = 0)"
                else:
                    mech_query += " AND e.subsidiary = %s"
                    mech_params.append(betrieb_nr)

            cursor.execute(convert_placeholders(mech_query), mech_params)
            mech_row = cursor.fetchone()
            basis_mechaniker = (row_to_dict(mech_row) if mech_row else {}).get('anzahl', 0) or 0

            trend = []
            for t in trend_raw:
                datum = t['datum']

                # TAG 136: datum kann ein date-Objekt sein in PostgreSQL
                if hasattr(datum, 'isoformat'):
                    datum_str = datum.isoformat()
                    datum_obj = datum
                else:
                    datum_str = str(datum)
                    datum_obj = datetime.strptime(datum_str, '%Y-%m-%d').date()
                ist_wochenende = datum_obj.weekday() >= 5

                cursor.execute(convert_placeholders("""
                    SELECT name FROM holidays
                    WHERE date = %s AND bundesland = 'Bayern'
                """), [datum_str])
                feiertag_row = cursor.fetchone()
                ist_feiertag = feiertag_row is not None

                ist_werktag = not ist_wochenende and not ist_feiertag

                if ist_werktag:
                    abw_query = f"""
                        SELECT COUNT(DISTINCT ac.employee_number) as abwesend
                        FROM loco_absence_calendar ac
                        JOIN loco_employees e ON ac.employee_number = e.employee_number
                        JOIN loco_employees_group_mapping g ON e.employee_number = g.employee_number
                        WHERE ac.date = %s
                        AND g.grp_code = 'MON'
                        AND e.is_latest_record = {is_latest}
                        AND e.employee_number NOT IN (
                            SELECT employee_number FROM loco_employees_group_mapping
                            WHERE grp_code IN ('A-W', 'A-L', 'A-K')
                        )
                    """
                    abw_params = [datum_str]
                    if betrieb and betrieb != 'alle':
                        betrieb_nr = int(betrieb)
                        if betrieb_nr == 1:
                            abw_query += " AND (e.subsidiary = 1 OR e.subsidiary IS NULL OR e.subsidiary = 0)"
                        else:
                            abw_query += " AND e.subsidiary = %s"
                            abw_params.append(betrieb_nr)

                    try:
                        cursor.execute(convert_placeholders(abw_query), abw_params)
                        abw_row = cursor.fetchone()
                        abwesend = (row_to_dict(abw_row) if abw_row else {}).get('abwesend', 0) or 0
                    except:
                        abwesend = 0

                    mechaniker_anwesend = max(0, basis_mechaniker - abwesend)
                    soll_kapazitaet_aw = mechaniker_anwesend * AW_PRO_TAG
                else:
                    continue

                trend.append({
                    'datum': datum_str,  # TAG 136: Immer String zurückgeben
                    'mechaniker': t['mechaniker'],
                    'auftraege': t['auftraege'],
                    'stempelzeit': t['stempelzeit'],
                    'anwesenheit': t['anwesenheit'],
                    'aw': t['aw'],
                    'leistungsgrad': t['leistungsgrad'],
                    'auslastung': t['auslastung'],
                    'mechaniker_anwesend': mechaniker_anwesend,
                    'mechaniker_soll': basis_mechaniker,
                    'abwesend': abwesend,
                    'soll_kapazitaet_aw': soll_kapazitaet_aw,
                    'ist_werktag': True
                })

            return jsonify({
                'success': True,
                'trend': trend,
                'basis_mechaniker': basis_mechaniker
            })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@werkstatt_api.route('/problemfaelle', methods=['GET'])
def get_problemfaelle():
    """GET /api/werkstatt/problemfaelle - Aufträge mit niedrigem LG"""
    try:
        zeitraum = request.args.get('zeitraum', 'monat')
        betrieb = request.args.get('betrieb', 'alle')
        max_lg = request.args.get('max_lg', 70, type=float)
        min_stempelzeit = request.args.get('min_stempelzeit', 30, type=int)
        von = request.args.get('von')
        bis = request.args.get('bis')

        if zeitraum == 'custom' and von and bis:
            datum_von = von
            datum_bis = bis
        else:
            heute = datetime.now().date()

            if zeitraum == 'heute':
                datum_von = datum_bis = heute.isoformat()
            elif zeitraum == 'woche':
                datum_von = (heute - timedelta(days=heute.weekday())).isoformat()
                datum_bis = heute.isoformat()
            elif zeitraum == 'monat':
                datum_von = heute.replace(day=1).isoformat()
                datum_bis = heute.isoformat()
            elif zeitraum == 'vormonat':
                erster_aktuell = heute.replace(day=1)
                letzter_vormonat = erster_aktuell - timedelta(days=1)
                datum_von = letzter_vormonat.replace(day=1).isoformat()
                datum_bis = letzter_vormonat.isoformat()
            elif zeitraum == 'quartal':
                quartal_monat = ((heute.month - 1) // 3) * 3 + 1
                datum_von = heute.replace(month=quartal_monat, day=1).isoformat()
                datum_bis = heute.isoformat()
            elif zeitraum == 'jahr':
                datum_von = heute.replace(month=1, day=1).isoformat()
                datum_bis = heute.isoformat()
            else:
                datum_von = heute.replace(day=1).isoformat()
                datum_bis = heute.isoformat()

        with db_session() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    w.rechnungs_datum as datum,
                    w.auftrags_nr,
                    w.kennzeichen,
                    w.serviceberater_nr as mechaniker_nr,
                    w.serviceberater_name as mechaniker_name,
                    w.summe_aw as vorgabe_aw,
                    w.summe_stempelzeit_min as gestempelt_min,
                    ROUND(w.summe_aw * 6.0 / NULLIF(w.summe_stempelzeit_min, 0) * 100, 1) as leistungsgrad,
                    w.betrieb as betrieb_nr,
                    CASE w.betrieb
                        WHEN 1 THEN 'Deggendorf'
                        WHEN 3 THEN 'Landau'
                        ELSE 'Unbekannt'
                    END as betrieb_name
                FROM werkstatt_auftraege_abgerechnet w
                WHERE w.rechnungs_datum BETWEEN ? AND ?
                  AND w.summe_stempelzeit_min >= ?
                  AND w.summe_aw > 0
                  AND w.storniert = 0
                  AND (w.summe_aw * 6.0 / NULLIF(w.summe_stempelzeit_min, 0) * 100) < ?
            """
            params = [datum_von, datum_bis, min_stempelzeit, max_lg]

            if betrieb and betrieb != 'alle':
                betrieb_nr = int(betrieb)
                if betrieb_nr == 1:
                    query += " AND (w.betrieb = 1 OR w.betrieb IS NULL OR w.betrieb = 0)"
                else:
                    query += " AND w.betrieb = %s"
                    params.append(betrieb_nr)

            query += " ORDER BY leistungsgrad ASC LIMIT 200"

            cursor.execute(query, params)
            auftraege = [dict(row) for row in cursor.fetchall()]

            total_verlust_aw = 0
            total_lg = 0
            for a in auftraege:
                if a['leistungsgrad'] and a['gestempelt_min'] and a['vorgabe_aw']:
                    vorgabe_min = a['vorgabe_aw'] * 6
                    verlust_min = a['gestempelt_min'] - vorgabe_min
                    if verlust_min > 0:
                        total_verlust_aw += verlust_min / 6
                    total_lg += a['leistungsgrad']

            avg_lg = total_lg / len(auftraege) if auftraege else 0

            return jsonify({
                'success': True,
                'auftraege': auftraege,
                'anzahl': len(auftraege),
                'statistik': {
                    'durchschnitt_lg': round(avg_lg, 1),
                    'total_verlust_aw': round(total_verlust_aw, 1)
                },
                'filter': {
                    'zeitraum': zeitraum,
                    'datum_von': datum_von,
                    'datum_bis': datum_bis,
                    'max_lg': max_lg,
                    'min_stempelzeit': min_stempelzeit,
                    'betrieb': betrieb
                }
            })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@werkstatt_api.route('/meine-employee-nr', methods=['GET'])
@login_required
def get_meine_employee_nr():
    """
    Gibt die Locosoft employee_number des aktuell eingeloggten Users zurück.
    Für Modal-Benachrichtigungen bei Überschreitungen.
    
    TAG 171: Serviceberater-Modal
    """
    try:
        from api.vacation_api import get_employee_from_session
        
        employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not employee_data or not employee_data.get('locosoft_id'):
            return jsonify({
                'success': False,
                'error': 'Keine employee_number gefunden'
            }), 404
        
        return jsonify({
            'success': True,
            'employee_number': employee_data['locosoft_id'],
            'ldap_username': ldap_username
        })
    
    except Exception as e:
        logger.exception("Fehler beim Holen der employee_number")
        return jsonify({'success': False, 'error': str(e)}), 500


@werkstatt_api.route('/health', methods=['GET'])
def health_check():
    """Health Check Endpoint"""
    try:
        with db_session() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM werkstatt_leistung_daily")
            count_daily = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM werkstatt_auftraege_abgerechnet")
            count_auftraege = cursor.fetchone()[0]

            cursor.execute("SELECT MAX(datum) FROM werkstatt_leistung_daily")
            last_date = cursor.fetchone()[0]

            cursor.execute("PRAGMA table_info(werkstatt_leistung_daily)")
            columns = [r[1] for r in cursor.fetchall()]
            has_betrieb = 'betrieb_nr' in columns

            return jsonify({
                'status': 'healthy',
                'werkstatt_leistung_daily': count_daily,
                'werkstatt_auftraege_abgerechnet': count_auftraege,
                'last_sync': last_date,
                'betrieb_filter_available': has_betrieb
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@werkstatt_api.route('/mechaniker/<int:mechaniker_nr>/stempelzeit-analyse', methods=['GET'])
@login_required
def get_stempelzeit_analyse(mechaniker_nr):
    """
    GET /api/werkstatt/mechaniker/<nr>/stempelzeit-analyse
    Detaillierte Tagesanalyse der Stempelzeiten für einen Mechaniker.
    """
    try:
        from datetime import date
        from api.werkstatt_data import WerkstattData
        
        # Zeitraum-Parameter
        zeitraum = request.args.get('zeitraum', 'monat')
        von_param = request.args.get('von')
        bis_param = request.args.get('bis')
        
        # Datumsbereich berechnen
        datum_von, datum_bis = get_date_range(zeitraum, von_param, bis_param)
        von = date.fromisoformat(datum_von)
        bis = date.fromisoformat(datum_bis)
        
        # Analyse holen
        analyse = WerkstattData.get_mechaniker_stempelzeit_analyse(
            mechaniker_nr=mechaniker_nr,
            von=von,
            bis=bis
        )
        
        if 'error' in analyse:
            return jsonify({
                'status': 'error',
                'error': analyse['error']
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': analyse
        })
        
    except Exception as e:
        logger.error(f"Fehler in get_stempelzeit_analyse: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
