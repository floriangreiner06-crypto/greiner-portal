#!/usr/bin/env python3
"""
WERKSTATT LIVE API - Echtzeit-Daten direkt aus Locosoft
========================================================
Holt aktuelle Werkstatt-Aufträge und Stempelungen LIVE
aus der Locosoft PostgreSQL-Datenbank.

Endpoints:
- GET /api/werkstatt/live/auftraege - Offene Aufträge
- GET /api/werkstatt/live/dashboard - Kombinierte Übersicht
- GET /api/werkstatt/live/auftrag/<nr> - Einzelner Auftrag mit Details

Author: Claude
Date: 2025-12-05 (TAG 92)
"""

import os
import sys
from datetime import datetime, timedelta, time
from flask import Blueprint, jsonify, request
import logging

# Zentrale DB-Utilities (TAG 117 + TAG 127 + TAG 136)
from api.db_utils import locosoft_session, get_locosoft_connection, get_portal_absences, db_session, row_to_dict
from api.db_connection import get_db_type

# Für RealDictCursor
from psycopg2.extras import RealDictCursor

# Gudat Client für Disposition (TAG 125)
sys.path.insert(0, '/opt/greiner-portal/tools')
try:
    from gudat_client import GudatClient
    GUDAT_AVAILABLE = True
except ImportError:
    GUDAT_AVAILABLE = False

# Logging
logger = logging.getLogger(__name__)

# Blueprint
werkstatt_live_bp = Blueprint('werkstatt_live', __name__, url_prefix='/api/werkstatt/live')

# get_locosoft_connection() wird jetzt aus db_utils importiert (TAG 117)


# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def format_datetime(dt):
    """Formatiert datetime für JSON"""
    if dt is None:
        return None
    return dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)


BETRIEB_NAMEN = {
    1: 'Deggendorf',
    2: 'Hyundai DEG',
    3: 'Landau'
}

# TAG 153: Gudat-Disposition aus gudat_data.py
# Migration-Plan: docs/GUDAT_TO_LOCOSOFT_MIGRATION.md
from api.gudat_data import GudatData, get_gudat_disposition

# Azubis - stempeln nur Anwesenheit, keine Aufträge
# Diese werden vom Leerlauf-Alarm UND Leistungs-Ranking ausgenommen
AZUBI_MA_NUMMERN = [5025, 5026, 5028]  # Wagner, Suttner, Thammer

# Nicht-produktive Mechaniker (Werkstattmeister, etc.)
# Diese werden vom Leerlauf-Alarm ausgenommen
NICHT_PRODUKTIV_MA = [5005]  # Scheingraber (Werkstattmeister)

# Kombinierte Ausschlussliste
LEERLAUF_AUSNAHMEN = AZUBI_MA_NUMMERN + NICHT_PRODUKTIV_MA

# Pausenzeiten - Mittagspause wird aus Laufzeit rausgerechnet
PAUSE_START = time(12, 0)   # 12:00 Uhr
PAUSE_ENDE = time(13, 0)    # 13:00 Uhr
PAUSE_DAUER_MIN = 60        # 60 Minuten

# Arbeitszeiten - Außerhalb = keine Leerlauf-Warnung
ARBEITSZEIT_START = time(6, 30)   # 06:30 Uhr
ARBEITSZEIT_ENDE = time(18, 0)    # 18:00 Uhr


def berechne_netto_laufzeit(start_time):
    """
    Berechnet die Netto-Arbeitszeit abzüglich Mittagspause.
    Wenn ein Auftrag über die Mittagspause läuft, wird diese abgezogen.
    """
    jetzt = datetime.now()
    start = start_time
    
    brutto_min = (jetzt - start).total_seconds() / 60
    
    # Pause heute
    heute = jetzt.date()
    pause_start_dt = datetime.combine(heute, PAUSE_START)
    pause_ende_dt = datetime.combine(heute, PAUSE_ENDE)
    
    # Prüfe ob Auftrag über Pause läuft
    if start < pause_start_dt and jetzt > pause_ende_dt:
        # Auftrag lief über komplette Pause → 60 min abziehen
        netto_min = brutto_min - PAUSE_DAUER_MIN
    elif start >= pause_start_dt and start < pause_ende_dt:
        # Auftrag in Pause gestartet → Start auf Pause-Ende setzen
        netto_min = (jetzt - pause_ende_dt).total_seconds() / 60
        if netto_min < 0:
            netto_min = 0
    elif jetzt > pause_start_dt and jetzt <= pause_ende_dt and start < pause_start_dt:
        # Jetzt ist Pause, Auftrag lief vorher → nur Zeit bis Pause-Start
        netto_min = (pause_start_dt - start).total_seconds() / 60
    else:
        # Keine Pause-Überschneidung
        netto_min = brutto_min
    
    return int(max(0, netto_min))


# =============================================================================
# API ENDPOINTS
# =============================================================================

@werkstatt_live_bp.route('/health', methods=['GET'])
def health_check():
    """Health-Check für die Live-API"""
    try:
        conn = get_locosoft_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'database': 'locosoft connected'
        })
    except Exception as e:
        logger.exception("Health-Check fehlgeschlagen")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/leistung', methods=['GET'])
def get_leistung_live():
    """
    LIVE Mechaniker-Leistungsübersicht direkt aus Locosoft.

    **TAG 148 REFACTORING:** Nutzt jetzt werkstatt_data.py (Single Source of Truth)
    Vorher: 270 Zeilen SQL direkt in API
    Nachher: 50 Zeilen - nutzt WerkstattData.get_mechaniker_leistung()

    Query-Parameter:
    - zeitraum: heute|woche|monat|vormonat|quartal|jahr|custom
    - von: Startdatum (bei custom)
    - bis: Enddatum (bei custom)
    - betrieb: alle|1|2|3
    - sort: leistungsgrad|stempelzeit|aw|auftraege
    - inkl_ehemalige: 0|1
    """
    try:
        from api.werkstatt_data import WerkstattData

        zeitraum = request.args.get('zeitraum', 'monat')
        von = request.args.get('von')
        bis = request.args.get('bis')
        betrieb_param = request.args.get('betrieb', 'alle')
        sort_by = request.args.get('sort', 'leistungsgrad')
        inkl_ehemalige = request.args.get('inkl_ehemalige', '0') == '1'

        # Datumsbereich berechnen
        heute = datetime.now().date()
        if zeitraum == 'heute':
            datum_von = datum_bis = heute
        elif zeitraum == 'woche':
            datum_von = heute - timedelta(days=heute.weekday())
            datum_bis = heute
        elif zeitraum == 'monat':
            datum_von = heute.replace(day=1)
            datum_bis = heute
        elif zeitraum == 'vormonat':
            erster_aktuell = heute.replace(day=1)
            letzter_vormonat = erster_aktuell - timedelta(days=1)
            datum_von = letzter_vormonat.replace(day=1)
            datum_bis = letzter_vormonat
        elif zeitraum == 'quartal':
            quartal_start_monat = ((heute.month - 1) // 3) * 3 + 1
            datum_von = heute.replace(month=quartal_start_monat, day=1)
            datum_bis = heute
        elif zeitraum == 'jahr':
            datum_von = heute.replace(month=1, day=1)
            datum_bis = heute
        elif zeitraum == 'custom' and von and bis:
            datum_von = datetime.strptime(von, '%Y-%m-%d').date()
            datum_bis = datetime.strptime(bis, '%Y-%m-%d').date()
        else:
            datum_von = heute.replace(day=1)
            datum_bis = heute

        # Betrieb-Parameter konvertieren
        betrieb = int(betrieb_param) if betrieb_param and betrieb_param != 'alle' else None

        # ===================================================================
        # HAUPTDATEN VON WERKSTATT_DATA.PY HOLEN (Single Source of Truth!)
        # ===================================================================
        data = WerkstattData.get_mechaniker_leistung(
            von=datum_von,
            bis=datum_bis,
            betrieb=betrieb,
            inkl_ehemalige=inkl_ehemalige,
            sort_by=sort_by
        )

        # Trend holen (letzte 14 Tage)
        trend = WerkstattData.get_leistung_trend(
            von=heute - timedelta(days=14),
            bis=heute
        )

        # Response aufbauen (Format muss mit altem Endpoint kompatibel sein!)
        return jsonify({
            'success': True,
            'source': 'LIVE_V2',  # V2 = nutzt werkstatt_data.py
            'zeitraum': {
                'von': data['zeitraum']['von'],
                'bis': data['zeitraum']['bis'],
                'label': zeitraum
            },
            'betrieb': betrieb_param,
            'mechaniker': data['mechaniker'],
            'anzahl_mechaniker': data['anzahl_mechaniker'],
            'anzahl_tage': data['anzahl_tage'],
            'gesamt_auftraege': data['gesamt']['auftraege'],
            'gesamt_stempelzeit': data['gesamt']['stempelzeit'],
            'gesamt_anwesenheit': data['gesamt']['anwesenheit'],
            'gesamt_aw': data['gesamt']['aw'],
            'gesamt_umsatz': data['gesamt']['umsatz'],
            'gesamt_leistungsgrad': data['gesamt']['leistungsgrad'],
            'gesamt_produktivitaet': data['gesamt']['produktivitaet'],
            'trend': trend
        })

    except Exception as e:
        logger.exception("Fehler bei LIVE Leistungsübersicht")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/auftraege', methods=['GET'])
def get_offene_auftraege():
    """
    Holt alle offenen Werkstatt-Aufträge LIVE aus Locosoft.

    TAG 149 REFACTORING: Nutzt werkstatt_data.py (Single Source of Truth)
    Vorher: 113 Zeilen SQL direkt in API
    Nachher: 30 Zeilen - nutzt WerkstattData.get_offene_auftraege()

    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    - tage: Wie viele Tage zurück (default: 7)
    - nur_offen: true/false (default: true)
    """
    try:
        from api.werkstatt_data import WerkstattData

        # Parameter parsen
        subsidiary = request.args.get('subsidiary', type=int)
        tage = request.args.get('tage', 7, type=int)
        nur_offen = request.args.get('nur_offen', 'true').lower() == 'true'

        # HAUPTDATEN VON WERKSTATT_DATA.PY HOLEN
        data = WerkstattData.get_offene_auftraege(
            betrieb=subsidiary,
            tage_zurueck=tage,
            nur_offen=nur_offen
        )

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',  # Marker: nutzt werkstatt_data.py
            'timestamp': datetime.now().isoformat(),
            'filter': {
                'subsidiary': subsidiary,
                'tage': tage,
                'nur_offen': nur_offen
            },
            'anzahl': data['anzahl'],
            'auftraege': data['auftraege']
        })

    except Exception as e:
        logger.exception("Fehler beim Laden der Aufträge")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/dashboard', methods=['GET'])
def get_live_dashboard():
    """
    Kombinierte Dashboard-Übersicht für LIVE-Monitoring.

    TAG 149 REFACTORING: Nutzt werkstatt_data.py (Single Source of Truth)
    Vorher: 140 Zeilen SQL direkt in API
    Nachher: 25 Zeilen - nutzt WerkstattData.get_dashboard_stats()
    """
    try:
        from api.werkstatt_data import WerkstattData

        # HAUPTDATEN VON WERKSTATT_DATA.PY HOLEN
        data = WerkstattData.get_dashboard_stats()

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',  # Marker: nutzt werkstatt_data.py
            'timestamp': datetime.now().isoformat(),
            'dashboard': data
        })

    except Exception as e:
        logger.exception("Fehler beim Laden des Dashboards")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/stempeluhr', methods=['GET'])
def get_stempeluhr_live():
    """
    LIVE Stempeluhr-Übersicht für Mechaniker.

    TAG 149 REFACTORING: Nutzt werkstatt_data.py (Single Source of Truth)
    Vorher: 570 Zeilen SQL direkt in API
    Nachher: 60 Zeilen - nutzt WerkstattData.get_stempeluhr()

    DUAL-FILTER für Cross-Betrieb Arbeit:
    - Bei subsidiary=1 oder 3: Filter nach MITARBEITER-Betrieb
    - Bei subsidiary=2 (Hyundai): Filter nach AUFTRAGS-Betrieb

    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3 oder komma-separiert z.B. "1,2")
    """
    try:
        from api.werkstatt_data import WerkstattData

        # TAG 109: Unterstütze komma-separierte subsidiary-Werte (z.B. "1,2" für Deggendorf)
        subsidiary_param = request.args.get('subsidiary', '')
        subsidiaries = []
        if subsidiary_param:
            for s in subsidiary_param.split(','):
                if s.strip().isdigit():
                    subsidiaries.append(int(s.strip()))

        # HAUPTDATEN VON WERKSTATT_DATA.PY HOLEN
        data = WerkstattData.get_stempeluhr(subsidiaries=subsidiaries if subsidiaries else None)

        # Pausenzeit-Check (12:00-13:00)
        jetzt_zeit = datetime.now().time()
        ist_pausenzeit = time(12, 0) <= jetzt_zeit <= time(13, 0)

        # Filter-Modus bestimmen
        if set(subsidiaries) == {1, 2}:
            filter_modus = 'deggendorf_gesamt'
            hinweis = 'Deggendorf (Stellantis + Hyundai)'
        elif subsidiaries == [2]:
            filter_modus = 'auftrags_betrieb'
            hinweis = 'Hyundai hat keine eigenen Mechaniker'
        else:
            filter_modus = 'mitarbeiter_betrieb'
            hinweis = None

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',  # Marker: nutzt werkstatt_data.py
            'timestamp': datetime.now().isoformat(),
            'ist_arbeitszeit': data['ist_arbeitszeit'],
            'ist_pausenzeit': ist_pausenzeit,
            'filter': {
                'subsidiary': subsidiary_param,
                'subsidiaries': subsidiaries,
                'filter_modus': filter_modus,
                'hinweis': hinweis
            },
            'aktive_mechaniker': data['aktive_mechaniker'],
            'leerlauf_mechaniker': data['leerlauf_mechaniker'],
            'abwesend_mechaniker': data['abwesend_mechaniker'],
            'pausiert_mechaniker': data['pausiert_mechaniker'],
            'feierabend_mechaniker': data['feierabend_mechaniker'],
            'summary': data['summary']
        })

    except Exception as e:
        logger.exception("Fehler beim Laden der Stempeluhr")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/tagesbericht', methods=['GET'])
def get_tagesbericht():
    """
    Tagesbericht zur Kontrolle: Stempelungen, Zuweisungen, Ueberschreitungen

    TAG 150: Refaktoriert - nutzt WerkstattData.get_tagesbericht()
    Vorher: 220 LOC | Nachher: 35 LOC

    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    - datum: Datum im Format YYYY-MM-DD (default: heute)
    """
    try:
        from api.werkstatt_data import WerkstattData

        subsidiary = request.args.get('subsidiary', type=int)
        datum_str = request.args.get('datum')

        datum = None
        if datum_str:
            datum = datetime.strptime(datum_str, '%Y-%m-%d').date()

        data = WerkstattData.get_tagesbericht(datum=datum, betrieb=subsidiary)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            'timestamp': datetime.now().isoformat(),
            **data
        })

    except Exception as e:
        logger.exception("Fehler beim Erstellen des Tagesberichts")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/nachkalkulation', methods=['GET'])
def get_nachkalkulation():
    """
    Auftrags-Nachkalkulation: Vergleich Vorgabe vs. Gestempelt vs. Verrechnet

    TAG 151: Refaktoriert - nutzt WerkstattData.get_nachkalkulation()
    Vorher: 297 LOC | Nachher: 35 LOC

    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    - datum: Datum im Format YYYY-MM-DD (default: heute)
    - typ: alle|extern|intern
    """
    try:
        from api.werkstatt_data import WerkstattData

        subsidiary = request.args.get('subsidiary', type=int)
        datum_str = request.args.get('datum')
        typ_filter = request.args.get('typ', 'alle')

        datum = None
        if datum_str:
            datum = datetime.strptime(datum_str, '%Y-%m-%d').date()

        data = WerkstattData.get_nachkalkulation(datum=datum, betrieb=subsidiary, typ=typ_filter)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            'timestamp': datetime.now().isoformat(),
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei Nachkalkulation")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/auftrag/<int:auftrag_nr>', methods=['GET'])
def get_auftrag_detail(auftrag_nr):
    """
    Detailansicht eines einzelnen Auftrags mit allen Positionen

    TAG 150: Refaktoriert - nutzt WerkstattData.get_auftrag_detail()
    Vorher: 165 LOC | Nachher: 30 LOC
    """
    try:
        from api.werkstatt_data import WerkstattData

        data = WerkstattData.get_auftrag_detail(auftrag_nr)

        if not data.get('success', True):
            return jsonify(data), 404

        return jsonify({
            'source': 'LIVE_V2',
            'timestamp': datetime.now().isoformat(),
            **data
        })

    except Exception as e:
        logger.exception(f"Fehler beim Laden von Auftrag {auftrag_nr}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/problemfaelle', methods=['GET'])
def get_problemfaelle_live():
    """
    Problemfaelle: Auftraege mit niedrigem Leistungsgrad

    TAG 150: Refaktoriert - nutzt WerkstattData.get_problemfaelle()
    Vorher: 210 LOC | Nachher: 40 LOC

    Query-Parameter:
    - zeitraum: heute|woche|monat|vormonat|quartal|jahr|custom
    - von/bis: Datumsbereich fuer custom
    - betrieb: 1|3|alle
    - max_lg: Maximaler Leistungsgrad (default: 70)
    - min_stempelzeit: Minimale Stempelzeit in Minuten (default: 30)
    """
    try:
        from api.werkstatt_data import WerkstattData

        zeitraum = request.args.get('zeitraum', 'monat')
        betrieb = request.args.get('betrieb')
        max_lg = request.args.get('max_lg', 70, type=float)
        min_stempelzeit = request.args.get('min_stempelzeit', 30, type=int)
        von = request.args.get('von')
        bis = request.args.get('bis')

        # Betrieb-Konvertierung
        betrieb_int = None
        if betrieb and betrieb != 'alle':
            betrieb_int = int(betrieb)

        data = WerkstattData.get_problemfaelle(
            zeitraum=zeitraum,
            betrieb=betrieb_int,
            max_lg=max_lg,
            min_stempelzeit=min_stempelzeit,
            von=von,
            bis=bis
        )

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei Problemfaelle-Abfrage")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/kapazitaet', methods=['GET'])
def get_kapazitaetsplanung():
    """
    Kapazitätsplanung Werkstatt: Offene Arbeit vs. verfügbare Kapazität.

    TAG 149 REFACTORING: Nutzt werkstatt_data.py (Single Source of Truth)
    Vorher: 310 Zeilen SQL direkt in API
    Nachher: 35 Zeilen - nutzt WerkstattData.get_kapazitaetsplanung()

    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 3) - Hinweis: Betrieb 2 hat keine Werkstatt
    - tage: Wie viele Tage Aufträge berücksichtigen (default: 7)
    """
    try:
        from api.werkstatt_data import WerkstattData

        subsidiary = request.args.get('subsidiary', type=int)
        tage = request.args.get('tage', 7, type=int)

        # HAUPTDATEN VON WERKSTATT_DATA.PY HOLEN
        data = WerkstattData.get_kapazitaetsplanung(
            betrieb=subsidiary,
            tage=tage
        )

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',  # Marker: nutzt werkstatt_data.py
            'timestamp': datetime.now().isoformat(),
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei Kapazitätsplanung")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# GUDAT TEAM-KAPAZITÄT (TAG 118)
# Proxy zur Gudat API für das Kapazitätsplanungs-Widget
# =============================================================================

@werkstatt_live_bp.route('/gudat/kapazitaet', methods=['GET'])
def get_gudat_kapazitaet():
    """
    Proxy für Gudat Kapazitäts-Daten

    TAG 153: Refaktoriert - nutzt GudatData.get_kapazitaet()
    Vorher: 100 LOC | Nachher: 15 LOC
    """
    try:
        from api.gudat_data import GudatData

        data = GudatData.get_kapazitaet()

        if not data.get('success'):
            return jsonify(data), 503

        return jsonify(data)

    except Exception as e:
        logger.exception("Fehler bei Gudat Kapazität")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/forecast', methods=['GET'])
def get_kapazitaets_forecast():
    """
    MEGA Kapazitäts-Forecast: Vorausschau auf die nächsten Arbeitstage
    
    Features:
    - Tagesweise Kapazität vs. geplante Arbeit
    - Berücksichtigt geplante Abwesenheiten (Urlaub etc.)
    - Warnung bei unverplanten Aufträgen (ohne Termin)
    - Warnung bei überfälligen Aufträgen
    - Teile-Status: Locosoft Lager + Servicebox Bestellungen
    
    Query-Parameter:
    - tage: Anzahl Tage Vorschau (default: 10)
    - subsidiary: Filter nach Betrieb (1, 3)
    """
    try:
        from datetime import timedelta

        tage_vorschau = request.args.get('tage', 10, type=int)
        subsidiary = request.args.get('subsidiary', type=int)

        conn_loco = get_locosoft_connection()
        cur_loco = conn_loco.cursor(cursor_factory=RealDictCursor)

        # Portal-DB für Servicebox (TAG 136: PostgreSQL-kompatibel)
        conn_portal = db_session().__enter__()
        cur_portal = conn_portal.cursor()
        
        heute = datetime.now().date()
        
        # =====================================================================
        # 1. ARBEITSTAGE ERMITTELN (ohne Wochenende, mit Feiertagen)
        # =====================================================================
        
        # Feiertage aus Locosoft holen
        cur_loco.execute("""
            SELECT date FROM year_calendar 
            WHERE is_public_holid = true 
              AND date >= CURRENT_DATE 
              AND date <= CURRENT_DATE + INTERVAL '%s days'
        """, [tage_vorschau + 14])  # Extra Puffer für Wochenenden
        
        feiertage = set(row['date'] for row in cur_loco.fetchall())
        
        # Arbeitstage berechnen
        arbeitstage = []
        check_date = heute
        while len(arbeitstage) < tage_vorschau:
            # Wochenende überspringen (5=Sa, 6=So)
            if check_date.weekday() < 5 and check_date not in feiertage:
                arbeitstage.append(check_date)
            check_date += timedelta(days=1)
        
        # =====================================================================
        # 2. KAPAZITÄT PRO TAG (mit geplanten Abwesenheiten)
        # =====================================================================
        
        tages_forecast = []
        
        for tag in arbeitstage:
            dow = tag.weekday()  # 0=Mo, 4=Fr
            
            # Mechaniker mit Arbeitszeiten für diesen Wochentag
            kapa_query = """
                WITH aktuelle_arbeitszeiten AS (
                    SELECT DISTINCT ON (employee_number, dayofweek)
                        employee_number,
                        dayofweek,
                        work_duration
                    FROM employees_worktimes
                    ORDER BY employee_number, dayofweek, validity_date DESC
                ),
                abwesende_tag AS (
                    SELECT employee_number, reason, type
                    FROM absence_calendar
                    WHERE date = %s
                )
                SELECT 
                    eh.employee_number,
                    eh.name,
                    eh.subsidiary,
                    COALESCE(aw.work_duration, 8) as stunden,
                    ab.reason as abwesenheit_grund,
                    CASE WHEN ab.employee_number IS NOT NULL THEN true ELSE false END as ist_abwesend
                FROM employees_history eh
                LEFT JOIN aktuelle_arbeitszeiten aw 
                    ON eh.employee_number = aw.employee_number
                    AND aw.dayofweek = %s
                LEFT JOIN abwesende_tag ab ON eh.employee_number = ab.employee_number
                WHERE eh.is_latest_record = true
                  AND eh.employee_number BETWEEN 5000 AND 5999
                  AND eh.mechanic_number IS NOT NULL
                  AND eh.subsidiary > 0
                  AND (eh.leave_date IS NULL OR eh.leave_date > %s)
            """
            
            kapa_params = [tag, dow, tag]
            if subsidiary:
                kapa_query += " AND eh.subsidiary = %s"
                kapa_params.append(subsidiary)
            
            cur_loco.execute(kapa_query, kapa_params)
            mechaniker_tag = cur_loco.fetchall()
            
            anwesend = [m for m in mechaniker_tag if not m['ist_abwesend']]
            abwesend = [m for m in mechaniker_tag if m['ist_abwesend']]
            
            kapazitaet_h = sum(float(m['stunden']) for m in anwesend)
            kapazitaet_aw = kapazitaet_h * 6
            
            # Geplante Aufträge für diesen Tag
            auftraege_query = """
                SELECT 
                    o.number as auftrag_nr,
                    o.subsidiary as betrieb,
                    o.estimated_inbound_time as bringen,
                    o.estimated_outbound_time as abholen,
                    o.urgency,
                    v.license_plate as kennzeichen,
                    COALESCE(SUM(l.time_units), 0) as vorgabe_aw
                FROM orders o
                LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
                LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
                WHERE o.has_open_positions = true
                  AND DATE(o.estimated_inbound_time) = %s
            """
            
            auftraege_params = [tag]
            if subsidiary:
                auftraege_query += " AND o.subsidiary = %s"
                auftraege_params.append(subsidiary)
            
            auftraege_query += """
                GROUP BY o.number, o.subsidiary, o.estimated_inbound_time, 
                         o.estimated_outbound_time, o.urgency, v.license_plate
            """
            
            cur_loco.execute(auftraege_query, auftraege_params)
            auftraege_tag = cur_loco.fetchall()
            
            geplant_aw = sum(float(a['vorgabe_aw']) for a in auftraege_tag)
            
            # Auslastung berechnen
            if kapazitaet_aw > 0:
                auslastung = (geplant_aw / kapazitaet_aw) * 100
            else:
                auslastung = 0
            
            # Status bestimmen
            if auslastung > 120:
                status = 'kritisch'
                status_icon = '🔴'
            elif auslastung > 90:
                status = 'hoch'
                status_icon = '🟠'
            elif auslastung > 50:
                status = 'normal'
                status_icon = '🟢'
            else:
                status = 'niedrig'
                status_icon = '🔵'
            
            tages_forecast.append({
                'datum': str(tag),
                'datum_formatiert': tag.strftime('%a %d.%m.'),
                'wochentag': ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'][dow],
                'ist_heute': tag == heute,
                'mechaniker_anwesend': len(anwesend),
                'mechaniker_abwesend': len(abwesend),
                'abwesende': [{'name': m['name'], 'grund': m['abwesenheit_grund']} for m in abwesend],
                'kapazitaet_h': kapazitaet_h,
                'kapazitaet_aw': kapazitaet_aw,
                'geplant_aw': geplant_aw,
                'geplant_anzahl': len(auftraege_tag),
                'auslastung_prozent': round(auslastung, 1),
                'freie_kapazitaet_aw': max(0, kapazitaet_aw - geplant_aw),
                'status': status,
                'status_icon': status_icon
            })
        
        # =====================================================================
        # 3. UNVERPLANTE AUFTRÄGE (ohne Bringen-Termin)
        # =====================================================================
        
        unverplant_query = """
            SELECT 
                o.number as auftrag_nr,
                o.subsidiary as betrieb,
                o.order_date,
                o.urgency,
                v.license_plate as kennzeichen,
                m.description as marke,
                COALESCE(cs.family_name, 'Unbekannt') as kunde,
                COALESCE(SUM(l.time_units), 0) as vorgabe_aw,
                COUNT(DISTINCT l.order_position) as anzahl_positionen
            FROM orders o
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
            LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
            WHERE o.has_open_positions = true
              AND o.estimated_inbound_time IS NULL
              AND o.order_date >= CURRENT_DATE - INTERVAL '30 days'
        """
        
        if subsidiary:
            unverplant_query += " AND o.subsidiary = %s"
        
        unverplant_query += """
            GROUP BY o.number, o.subsidiary, o.order_date, o.urgency, 
                     v.license_plate, m.description, cs.family_name
            HAVING COALESCE(SUM(l.time_units), 0) > 0
            ORDER BY o.urgency DESC NULLS LAST, o.order_date ASC
        """
        
        if subsidiary:
            cur_loco.execute(unverplant_query, [subsidiary])
        else:
            cur_loco.execute(unverplant_query)
        
        unverplante = cur_loco.fetchall()
        
        unverplante_auftraege = [{
            'auftrag_nr': a['auftrag_nr'],
            'betrieb': a['betrieb'],
            'betrieb_name': BETRIEB_NAMEN.get(a['betrieb'], '?'),
            'kennzeichen': a['kennzeichen'],
            'marke': a['marke'],
            'kunde': a['kunde'],
            'vorgabe_aw': float(a['vorgabe_aw']),
            'anzahl_positionen': a['anzahl_positionen'],
            'auftragsdatum': a['order_date'].strftime('%d.%m.%Y') if a['order_date'] else None,
            'dringend': a['urgency'] and a['urgency'] >= 4
        } for a in unverplante]
        
        summe_unverplant_aw = sum(a['vorgabe_aw'] for a in unverplante_auftraege)
        
        # =====================================================================
        # 4. ÜBERFÄLLIGE AUFTRÄGE (Termin in Vergangenheit)
        # =====================================================================
        
        ueberfaellig_query = """
            SELECT 
                o.number as auftrag_nr,
                o.subsidiary as betrieb,
                o.estimated_inbound_time as bringen,
                o.estimated_outbound_time as abholen,
                o.urgency,
                v.license_plate as kennzeichen,
                m.description as marke,
                COALESCE(cs.family_name, 'Unbekannt') as kunde,
                COALESCE(SUM(l.time_units), 0) as vorgabe_aw
            FROM orders o
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
            LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
            WHERE o.has_open_positions = true
              AND DATE(o.estimated_inbound_time) < CURRENT_DATE
        """
        
        if subsidiary:
            ueberfaellig_query += " AND o.subsidiary = %s"
        
        ueberfaellig_query += """
            GROUP BY o.number, o.subsidiary, o.estimated_inbound_time, 
                     o.estimated_outbound_time, o.urgency, v.license_plate, 
                     m.description, cs.family_name
            ORDER BY o.estimated_inbound_time ASC
        """
        
        if subsidiary:
            cur_loco.execute(ueberfaellig_query, [subsidiary])
        else:
            cur_loco.execute(ueberfaellig_query)
        
        ueberfaellige = cur_loco.fetchall()
        
        ueberfaellige_auftraege = [{
            'auftrag_nr': a['auftrag_nr'],
            'betrieb': a['betrieb'],
            'betrieb_name': BETRIEB_NAMEN.get(a['betrieb'], '?'),
            'kennzeichen': a['kennzeichen'],
            'marke': a['marke'],
            'kunde': a['kunde'],
            'vorgabe_aw': float(a['vorgabe_aw'] or 0),
            'bringen': a['bringen'].strftime('%d.%m.%Y %H:%M') if a['bringen'] else None,
            'tage_ueberfaellig': (heute - a['bringen'].date()).days if a['bringen'] else 0,
            'dringend': a['urgency'] and a['urgency'] >= 4
        } for a in ueberfaellige]
        
        # =====================================================================
        # 5. TEILE-STATUS (Locosoft Lager + Servicebox Bestellungen)
        # =====================================================================
        
        # Aufträge mit fehlenden Teilen aus Locosoft
        teile_query = """
            SELECT 
                o.number as auftrag_nr,
                o.subsidiary as betrieb,
                o.estimated_inbound_time as bringen,
                v.license_plate as kennzeichen,
                COUNT(DISTINCT p.part_number) as teile_gesamt,
                COUNT(DISTINCT CASE WHEN COALESCE(ps.stock_level, 0) > 0 THEN p.part_number END) as teile_auf_lager,
                COALESCE(SUM(l.time_units), 0) as vorgabe_aw
            FROM orders o
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN parts p ON o.number = p.order_number
            LEFT JOIN parts_stock ps ON p.part_number = ps.part_number AND ps.stock_no = 1
            LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
            WHERE o.has_open_positions = true
              AND o.order_date >= CURRENT_DATE - INTERVAL '30 days'
        """
        
        if subsidiary:
            teile_query += " AND o.subsidiary = %s"
        
        teile_query += """
            GROUP BY o.number, o.subsidiary, o.estimated_inbound_time, v.license_plate
            HAVING COUNT(DISTINCT p.part_number) > 0
               AND COUNT(DISTINCT CASE WHEN COALESCE(ps.stock_level, 0) > 0 THEN p.part_number END) 
                   < COUNT(DISTINCT p.part_number)
            ORDER BY o.estimated_inbound_time NULLS LAST
        """
        
        if subsidiary:
            cur_loco.execute(teile_query, [subsidiary])
        else:
            cur_loco.execute(teile_query)
        
        teile_fehlen = cur_loco.fetchall()
        
        auftraege_teile_fehlen = [{
            'auftrag_nr': t['auftrag_nr'],
            'betrieb': t['betrieb'],
            'betrieb_name': BETRIEB_NAMEN.get(t['betrieb'], '?'),
            'kennzeichen': t['kennzeichen'],
            'vorgabe_aw': float(t['vorgabe_aw'] or 0),
            'teile_auf_lager': t['teile_auf_lager'],
            'teile_gesamt': t['teile_gesamt'],
            'teile_fehlen': t['teile_gesamt'] - t['teile_auf_lager'],
            'bringen': t['bringen'].strftime('%d.%m.') if t['bringen'] else 'Kein Termin'
        } for t in teile_fehlen]
        
        # Offene Servicebox-Bestellungen (noch nicht zugebucht)
        # TAG 136: PostgreSQL-kompatibel
        if get_db_type() == 'postgresql':
            date_filter = "b.bestelldatum >= CURRENT_DATE - INTERVAL '30 days'"
        else:
            date_filter = "b.bestelldatum >= date('now', '-30 days')"

        cur_portal.execute(f"""
            SELECT
                b.bestellnummer,
                b.bestelldatum,
                b.lokale_nr,
                b.match_kunde_name as kunde,
                COUNT(p.id) as anzahl_positionen,
                COALESCE(SUM(p.summe_inkl_mwst), 0) as gesamtwert,
                (SELECT COUNT(*) FROM teile_lieferscheine tl
                 WHERE tl.servicebox_bestellnr = b.bestellnummer
                   AND tl.locosoft_zugebucht = true) as zugebucht_count,
                (SELECT COUNT(*) FROM teile_lieferscheine tl
                 WHERE tl.servicebox_bestellnr = b.bestellnummer) as lieferschein_count
            FROM stellantis_bestellungen b
            LEFT JOIN stellantis_positionen p ON b.id = p.bestellung_id
            WHERE {date_filter}
            GROUP BY b.id, b.bestellnummer, b.bestelldatum, b.lokale_nr, b.match_kunde_name
            HAVING (SELECT COUNT(*) FROM teile_lieferscheine tl
                    WHERE tl.servicebox_bestellnr = b.bestellnummer
                      AND tl.locosoft_zugebucht = true) < COUNT(p.id)
                OR (SELECT COUNT(*) FROM teile_lieferscheine tl
                    WHERE tl.servicebox_bestellnr = b.bestellnummer) = 0
            ORDER BY b.bestelldatum DESC
            LIMIT 20
        """)
        
        offene_bestellungen_raw = cur_portal.fetchall()

        offene_servicebox = []
        for b in offene_bestellungen_raw:
            b_dict = row_to_dict(b)
            offene_servicebox.append({
                'bestellnummer': b_dict['bestellnummer'],
                'bestelldatum': b_dict['bestelldatum'],
                'lokale_nr': b_dict['lokale_nr'],
                'kunde': b_dict['kunde'],
                'anzahl_positionen': b_dict['anzahl_positionen'],
                'gesamtwert': round(float(b_dict['gesamtwert'] or 0), 2),
                'status': 'bestellt' if b_dict['lieferschein_count'] == 0 else 'teilweise_geliefert',
                'zugebucht': b_dict['zugebucht_count'] or 0,
                'geliefert': b_dict['lieferschein_count'] or 0
            })
        
        # =====================================================================
        # 6. ZUSAMMENFASSUNG & WARNUNGEN
        # =====================================================================
        
        warnungen = []
        
        if len(unverplante_auftraege) > 0:
            warnungen.append({
                'typ': 'unverplant',
                'icon': '📋',
                'text': f"{len(unverplante_auftraege)} Aufträge ohne Termin ({summe_unverplant_aw:.0f} AW)",
                'severity': 'warning'
            })
        
        if len(ueberfaellige_auftraege) > 0:
            warnungen.append({
                'typ': 'ueberfaellig',
                'icon': '⏰',
                'text': f"{len(ueberfaellige_auftraege)} überfällige Aufträge",
                'severity': 'danger'
            })
        
        if len(auftraege_teile_fehlen) > 0:
            warnungen.append({
                'typ': 'teile_fehlen',
                'icon': '🔧',
                'text': f"{len(auftraege_teile_fehlen)} Aufträge warten auf Teile",
                'severity': 'warning'
            })
        
        if len(offene_servicebox) > 0:
            warnungen.append({
                'typ': 'servicebox_offen',
                'icon': '📦',
                'text': f"{len(offene_servicebox)} offene Servicebox-Bestellungen",
                'severity': 'info'
            })
        
        # Tage mit kritischer Auslastung
        kritische_tage = [t for t in tages_forecast if t['status'] == 'kritisch']
        if kritische_tage:
            warnungen.append({
                'typ': 'ueberbucht',
                'icon': '🔴',
                'text': f"{len(kritische_tage)} Tage überbucht (>120%)",
                'severity': 'danger'
            })
        
        # Gesamtkapazität nächste Woche
        kapazitaet_woche = sum(t['kapazitaet_aw'] for t in tages_forecast[:5])
        geplant_woche = sum(t['geplant_aw'] for t in tages_forecast[:5])

        # =====================================================================
        # 7. AVG - ABRECHNUNGS-VERZÖGERUNGS-GRÜNDE (TAG 124)
        # =====================================================================

        avg_query = """
            SELECT
                o.clearing_delay_type as avg_code,
                cdt.description as avg_text,
                COUNT(*) as anzahl,
                COALESCE(SUM(l.time_units), 0) as summe_aw
            FROM orders o
            LEFT JOIN clearing_delay_types cdt ON o.clearing_delay_type = cdt.type
            LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
            WHERE o.has_open_positions = true
              AND o.clearing_delay_type IS NOT NULL
              AND o.clearing_delay_type != ''
        """

        if subsidiary:
            avg_query += " AND o.subsidiary = %s"

        avg_query += """
            GROUP BY o.clearing_delay_type, cdt.description
            ORDER BY anzahl DESC
        """

        if subsidiary:
            cur_loco.execute(avg_query, [subsidiary])
        else:
            cur_loco.execute(avg_query)

        avg_raw = cur_loco.fetchall()

        avg_statistik = [{
            'code': a['avg_code'],
            'text': a['avg_text'] or 'Unbekannt',
            'anzahl': a['anzahl'],
            'summe_aw': float(a['summe_aw'] or 0)
        } for a in avg_raw]

        avg_gesamt = sum(a['anzahl'] for a in avg_statistik)
        avg_aw_gesamt = sum(a['summe_aw'] for a in avg_statistik)

        cur_loco.close()
        conn_loco.close()
        cur_portal.close()
        conn_portal.close()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'datum': str(heute),
            'filter': {
                'subsidiary': subsidiary,
                'tage_vorschau': tage_vorschau
            },
            
            # Tages-Forecast
            'forecast': tages_forecast,
            
            # Warnungen
            'warnungen': warnungen,
            'anzahl_warnungen': len(warnungen),
            
            # Unverplante Aufträge
            'unverplant': {
                'anzahl': len(unverplante_auftraege),
                'summe_aw': round(summe_unverplant_aw, 1),
                'auftraege': unverplante_auftraege[:15]  # Max 15
            },
            
            # Überfällige Aufträge
            'ueberfaellig': {
                'anzahl': len(ueberfaellige_auftraege),
                'auftraege': ueberfaellige_auftraege[:10]  # Max 10
            },
            
            # Teile-Status
            'teile': {
                'auftraege_warten_auf_teile': len(auftraege_teile_fehlen),
                'auftraege': auftraege_teile_fehlen[:10],  # Max 10
                'offene_servicebox_bestellungen': len(offene_servicebox),
                'servicebox': offene_servicebox[:10]  # Max 10
            },
            
            # Wochen-Zusammenfassung
            'woche': {
                'kapazitaet_aw': kapazitaet_woche,
                'geplant_aw': geplant_woche,
                'auslastung_prozent': round((geplant_woche / kapazitaet_woche * 100) if kapazitaet_woche > 0 else 0, 1),
                'freie_kapazitaet_aw': kapazitaet_woche - geplant_woche
            },

            # AVG - Abrechnungs-Verzögerungs-Gründe (TAG 124)
            'avg': {
                'gesamt_auftraege': avg_gesamt,
                'gesamt_aw': round(avg_aw_gesamt, 1),
                'statistik': avg_statistik
            }
        })
        
    except Exception as e:
        logger.exception("Fehler bei Kapazitäts-Forecast")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# HEUTE LIVE - Echte Zahlen von heute (Stempelungen + Verrechnet)
# ============================================================================

@werkstatt_live_bp.route('/heute', methods=['GET'])
def get_heute_live():
    """
    Echte Zahlen von heute: Gestempelt, Verrechnet, Aktive Mechaniker

    TAG 151: Refaktoriert - nutzt WerkstattData.get_heute_live()
    Vorher: 330 LOC | Nachher: 30 LOC

    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    """
    try:
        from api.werkstatt_data import WerkstattData

        subsidiary = request.args.get('subsidiary', type=int)

        data = WerkstattData.get_heute_live(betrieb=subsidiary)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            'timestamp': datetime.now().isoformat(),
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei HEUTE LIVE")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# AUFTRÄGE ENRICHED - Kombiniert Locosoft + ML + Gudat (TAG 98)
# ============================================================================

@werkstatt_live_bp.route('/auftraege-enriched', methods=['GET'])
def get_auftraege_enriched():
    """
    MEGA-Endpoint: Offene Aufträge mit ML-Vorhersage und Gudat-Terminen
    
    Kombiniert:
    - Locosoft: Aufträge, Vorgabe-AW, Stempelungen, Mechaniker
    - ML: Vorhersage der tatsächlichen Dauer
    - Gudat: Geplante Termine (falls vorhanden)
    
    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    - tage: Wie viele Tage zurück (default: 7)
    - nur_offen: true/false (default: true)
    - mit_ml: ML-Vorhersage einbeziehen (default: true)
    - mit_gudat: Gudat-Termine matchen (default: true)
    
    Response pro Auftrag:
    {
        "auftrag_nr": 219379,
        "kennzeichen": "DEG-X 212",
        "kunde": "Stadler, Werner",
        "vorgabe_aw": 3.5,
        "gestempelt_aw": 2.1,
        "mechaniker_nr": 5008,
        "mechaniker_name": "Patrick Ebner",
        "ml_vorhersage_aw": 4.2,
        "ml_potenzial_aw": 0.7,
        "ml_status": "unterbewertet",
        "gudat_termin": "2025-12-09T07:00:00",
        "gudat_team": "Allgemeine Reparatur"
    }
    """
    try:
        subsidiary = request.args.get('subsidiary', type=int)
        tage = request.args.get('tage', 7, type=int)
        nur_offen = request.args.get('nur_offen', 'true').lower() == 'true'
        mit_ml = request.args.get('mit_ml', 'true').lower() == 'true'
        mit_gudat = request.args.get('mit_gudat', 'true').lower() == 'true'
        
        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # =====================================================================
        # 1. OFFENE AUFTRÄGE AUS LOCOSOFT
        # TAG 122: times-Tabelle existiert nicht in loco_auswertung_db
        # Verwende labours für Zeitschätzungen statt Stempeluhr-Daten
        # =====================================================================
        query = """
            SELECT
                o.number as auftrag_nr,
                o.subsidiary as betrieb,
                o.order_date as auftrag_datum,
                o.order_taking_employee_no as serviceberater_nr,
                sb.name as serviceberater_name,
                o.vehicle_number,
                v.license_plate as kennzeichen,
                m.description as marke,
                mo.description as modell,
                v.mileage_km as km_stand,
                COALESCE(
                    EXTRACT(YEAR FROM AGE(NOW(), v.first_registration_date)),
                    EXTRACT(YEAR FROM NOW()) - v.production_year,
                    3
                ) as fahrzeug_alter,
                COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name) as kunde,
                o.urgency as dringlichkeit,
                o.has_open_positions as ist_offen,
                o.has_closed_positions as hat_abgeschlossene,
                o.estimated_inbound_time as geplant_eingang,
                o.estimated_outbound_time as geplant_fertig,
                COALESCE(l.total_aw, 0) as vorgabe_aw,
                l.mechaniker_nr,
                l.labour_type,
                l.labour_operation_id,
                l.charge_type,
                mech.name as mechaniker_name,
                -- TAG 122: Ohne times-Tabelle keine aktiven Stempelungen verfügbar
                NULL::integer as aktiv_mechaniker_nr,
                NULL::timestamp as stempel_start,
                NULL::numeric as aktiv_laufzeit_min,
                -- Geschätzte Zeit basierend auf abgerechneten labours (is_invoiced)
                COALESCE(l_done.abgerechnet_aw, 0) as gestempelt_aw,
                COALESCE(l_done.abgerechnet_aw, 0) * 6.0 as gestempelt_min
            FROM orders o
            LEFT JOIN employees_history sb ON o.order_taking_employee_no = sb.employee_number
                AND sb.is_latest_record = true
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN models mo ON v.make_number = mo.make_number AND v.model_code = mo.model_code
            LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
            LEFT JOIN LATERAL (
                SELECT
                    SUM(time_units) as total_aw,
                    MAX(mechanic_no) as mechaniker_nr,
                    MAX(labour_type) as labour_type,
                    MAX(labour_operation_id) as labour_operation_id,
                    MAX(charge_type) as charge_type
                FROM labours
                WHERE order_number = o.number AND time_units > 0
            ) l ON true
            LEFT JOIN employees_history mech ON l.mechaniker_nr = mech.employee_number
                AND mech.is_latest_record = true
            -- TAG 122: Bereits abgerechnete AW als "gestempelt"
            LEFT JOIN LATERAL (
                SELECT SUM(time_units) as abgerechnet_aw
                FROM labours
                WHERE order_number = o.number AND is_invoiced = true
            ) l_done ON true
            WHERE o.order_date >= CURRENT_DATE - INTERVAL '%s days'
        """

        params = [tage]
        
        if nur_offen:
            query += " AND o.has_open_positions = true"
        
        if subsidiary:
            query += " AND o.subsidiary = %s"
            params.append(subsidiary)
        
        query += " ORDER BY o.order_date DESC LIMIT 200"
        
        cur.execute(query, params)
        auftraege_raw = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # =====================================================================
        # 2. ML-VORHERSAGEN HINZUFÜGEN (DRIVE V5.1 - TAG 119)
        # =====================================================================
        # DRIVE = Data-driven Real-time Intelligence for Vehicle Excellence
        # Projekt von Florian Greiner für Autohaus Greiner
        # V5.1: + Labour Correction Factors (G=1.24x, W=0.94x, I=1.08x)
        # =====================================================================
        ml_predictions = {}
        mechaniker_effizienz = {}
        labour_corrections = {}

        if mit_ml:
            try:
                import pickle
                import pandas as pd
                import numpy as np
                import json as json_lib

                MODEL_DIR = "/opt/greiner-portal/data/ml/models"
                ML_DATA_DIR = "/opt/greiner-portal/data/ml"

                # DRIVE V5.1: Labour Correction Factors laden
                corrections_path = f"{ML_DATA_DIR}/labour_corrections.json"
                if os.path.exists(corrections_path):
                    with open(corrections_path, 'r') as f:
                        labour_corrections = json_lib.load(f)
                    logger.debug(f"DRIVE: Labour Corrections geladen ({len(labour_corrections.get('by_operation', {}))} Ops)")

                # DRIVE V5 Modell laden (TAG 119 - qualitätsgeprüfte Stempeluhr-Daten)
                # Symlink zeigt auf aktuellstes Modell
                model_path = f"{MODEL_DIR}/auftragsdauer_model.pkl"
                encoder_path = f"{MODEL_DIR}/label_encoders_v2_tag119.pkl"

                # Fallback auf ältere Version
                if not os.path.exists(encoder_path):
                    encoder_path = f"{MODEL_DIR}/label_encoders.pkl"

                if os.path.exists(model_path) and os.path.exists(encoder_path):
                    with open(model_path, 'rb') as f:
                        model = pickle.load(f)
                    with open(encoder_path, 'rb') as f:
                        encoders = pickle.load(f)

                    # Vorhersage für jeden Auftrag
                    for auftrag in auftraege_raw:
                        if auftrag['vorgabe_aw'] and auftrag['vorgabe_aw'] > 0:
                            try:
                                # === DRIVE V5 Feature-Vektor (21 Features) ===
                                vorgabe_aw = float(auftrag['vorgabe_aw'])
                                soll_dauer_min = vorgabe_aw * 6  # 1 AW = 6 Minuten
                                betrieb = auftrag['betrieb'] or 1
                                marke = auftrag['marke'] or 'Opel'
                                km_stand = float(auftrag['km_stand'] or 50000)
                                fahrzeug_alter = float(auftrag['fahrzeug_alter'] or 3)

                                # Datum-Features
                                auftrag_datum = auftrag['auftrag_datum']
                                if auftrag_datum:
                                    wochentag = auftrag_datum.weekday()
                                    monat = auftrag_datum.month
                                    start_stunde = auftrag_datum.hour if auftrag_datum.hour > 0 else 8
                                    kalenderwoche = auftrag_datum.isocalendar()[1]
                                else:
                                    wochentag, monat, start_stunde, kalenderwoche = 1, 6, 8, 25

                                # Kategorische Features encodieren
                                try:
                                    marke_encoded = encoders['marke'].transform([marke])[0]
                                except:
                                    marke_encoded = 0

                                try:
                                    auftragstyp = auftrag.get('auftragstyp', 'X') or 'X'
                                    auftragstyp_encoded = encoders['auftragstyp'].transform([auftragstyp])[0]
                                except:
                                    auftragstyp_encoded = 0

                                try:
                                    labour_type = auftrag.get('labour_type', 'W') or 'W'
                                    labour_type_encoded = encoders['labour_type'].transform([labour_type])[0]
                                except:
                                    labour_type_encoded = 0

                                # Defaults für Features die nicht live verfügbar sind
                                anzahl_positionen = int(auftrag.get('anzahl_positionen', 1) or 1)
                                anzahl_teile = int(auftrag.get('anzahl_teile', 0) or 0)
                                charge_type = int(auftrag.get('charge_type', 10) or 10)
                                urgency = int(auftrag.get('urgency', 0) or 0)
                                power_kw = float(auftrag.get('power_kw', 74) or 74)
                                cubic_capacity = float(auftrag.get('cubic_capacity', 1200) or 1200)
                                productivity_factor = 1.0  # Default
                                years_experience = 10.0    # Default
                                meister = 0                # Default

                                # === DRIVE V5 Feature-Vektor (21 Features, exakte Reihenfolge!) ===
                                features = pd.DataFrame([[
                                    soll_dauer_min,        # 1. soll_dauer_min
                                    vorgabe_aw,            # 2. soll_aw
                                    betrieb,               # 3. betrieb
                                    anzahl_positionen,     # 4. anzahl_positionen
                                    anzahl_teile,          # 5. anzahl_teile
                                    charge_type,           # 6. charge_type
                                    urgency,               # 7. urgency
                                    wochentag,             # 8. wochentag
                                    monat,                 # 9. monat
                                    start_stunde,          # 10. start_stunde
                                    kalenderwoche,         # 11. kalenderwoche
                                    power_kw,              # 12. power_kw
                                    cubic_capacity,        # 13. cubic_capacity
                                    km_stand,              # 14. km_stand
                                    fahrzeug_alter,        # 15. fahrzeug_alter_jahre
                                    productivity_factor,   # 16. productivity_factor
                                    years_experience,      # 17. years_experience
                                    meister,               # 18. meister
                                    marke_encoded,         # 19. marke_encoded
                                    auftragstyp_encoded,   # 20. auftragstyp_encoded
                                    labour_type_encoded    # 21. labour_type_encoded
                                ]], columns=[
                                    'soll_dauer_min', 'soll_aw', 'betrieb', 'anzahl_positionen', 'anzahl_teile',
                                    'charge_type', 'urgency', 'wochentag', 'monat', 'start_stunde', 'kalenderwoche',
                                    'power_kw', 'cubic_capacity', 'km_stand', 'fahrzeug_alter_jahre',
                                    'productivity_factor', 'years_experience', 'meister',
                                    'marke_encoded', 'auftragstyp_encoded', 'labour_type_encoded'
                                ])

                                # DRIVE V5 Vorhersage
                                vorhersage_min = model.predict(features)[0]

                                # === DRIVE V5.1: Labour Correction Factor anwenden ===
                                # Hierarchie: 1) Op+Type, 2) Op, 3) Type, 4) 1.0
                                labour_op = str(auftrag.get('labour_operation_id') or '').strip()
                                labour_t = str(auftrag.get('labour_type') or 'W').strip()

                                correction_factor = 1.0
                                correction_source = 'default'

                                if labour_corrections:
                                    # 1. Exakter Match: Op + Type
                                    if labour_op and labour_op in labour_corrections.get('by_operation_and_type', {}):
                                        if labour_t in labour_corrections['by_operation_and_type'][labour_op]:
                                            correction_factor = labour_corrections['by_operation_and_type'][labour_op][labour_t]['factor']
                                            correction_source = f'{labour_op}+{labour_t}'

                                    # 2. Fallback: Operation aggregiert
                                    if correction_source == 'default' and labour_op in labour_corrections.get('by_operation', {}):
                                        correction_factor = labour_corrections['by_operation'][labour_op]
                                        correction_source = labour_op

                                    # 3. Fallback: Type global (G=1.24, W=0.94, I=1.08)
                                    if correction_source == 'default' and labour_t in labour_corrections.get('by_type', {}):
                                        correction_factor = labour_corrections['by_type'][labour_t]
                                        correction_source = f'type:{labour_t}'

                                # Korrigierte Vorhersage
                                vorhersage_min_korrigiert = vorhersage_min * correction_factor
                                vorhersage_aw = vorhersage_min_korrigiert / 6.0  # 1 AW = 6 Minuten

                                # Potenzial = Differenz ML vs Herstellervorgabe
                                potenzial_aw = vorhersage_aw - vorgabe_aw
                                potenzial_prozent = (potenzial_aw / vorgabe_aw * 100) if vorgabe_aw > 0 else 0

                                ml_predictions[auftrag['auftrag_nr']] = {
                                    'vorhersage_aw': round(vorhersage_aw, 1),
                                    'vorhersage_min': round(vorhersage_min_korrigiert, 0),
                                    'potenzial_aw': round(potenzial_aw, 1),
                                    'potenzial_prozent': round(potenzial_prozent, 1),
                                    'correction_factor': round(correction_factor, 2),
                                    'correction_source': correction_source,
                                    'konfidenz': 'V5.1'  # Modell-Version für Debugging
                                }

                            except Exception as ml_err:
                                logger.debug(f"DRIVE ML-Fehler für Auftrag {auftrag['auftrag_nr']}: {ml_err}")

                    # Mechaniker-Effizienz aus V5 Trainingsdaten
                    data_path = "/opt/greiner-portal/data/ml/auftraege_features_v5.csv"
                    if os.path.exists(data_path):
                        df = pd.read_csv(data_path)
                        eff = df.groupby('mechaniker_nr').agg({
                            'ist_dauer_min': 'mean',
                            'soll_dauer_min': 'mean',
                            'effizienz_ratio': 'mean'
                        }).reset_index()
                        # Effizienz = SOLL/IST * 100 (höher = schneller als Vorgabe)
                        eff['effizienz'] = (eff['soll_dauer_min'] / eff['ist_dauer_min']) * 100
                        for _, row in eff.iterrows():
                            mechaniker_effizienz[int(row['mechaniker_nr'])] = round(row['effizienz'], 1)

            except Exception as e:
                logger.warning(f"DRIVE ML-Integration fehlgeschlagen: {e}")
        
        # =====================================================================
        # 3. GUDAT-TERMINE MATCHEN
        # =====================================================================
        gudat_termine = {}
        
        if mit_gudat:
            try:
                # Gudat-Client importieren
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
                from gudat_client import GudatClient
                import json
                
                # Credentials laden
                config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'credentials.json')
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                gudat_config = config.get('external_systems', {}).get('gudat', {})
                username = gudat_config.get('username')
                password = gudat_config.get('password')
                
                if username and password:
                    client = GudatClient(username, password)
                    if client.login():
                        # GraphQL-Query für Termine der nächsten 7 Tage
                        graphql_query = """
                        {
                            appointments(first: 100, where: {
                                column: START_DATE_TIME,
                                operator: GTE,
                                value: "%s"
                            }) {
                                data {
                                    id
                                    start_date_time
                                    end_date_time
                                    type
                                    dossier {
                                        id
                                        orders {
                                            id
                                            number
                                        }
                                        vehicle {
                                            license_plate
                                        }
                                    }
                                }
                            }
                        }
                        """ % datetime.now().strftime('%Y-%m-%d')
                        
                        response = client._api_request('POST', '/graphql', json={'query': graphql_query})
                        
                        if response.status_code == 200:
                            data = response.json()
                            appointments = data.get('data', {}).get('appointments', {}).get('data', [])
                            
                            for apt in appointments:
                                dossier = apt.get('dossier') or {}
                                orders = dossier.get('orders') or []
                                for order in orders:
                                    order_nr = order.get('number')
                                    if order_nr:
                                        gudat_termine[int(order_nr)] = {
                                            'termin_start': apt.get('start_date_time'),
                                            'termin_ende': apt.get('end_date_time'),
                                            'typ': apt.get('type'),
                                            'kennzeichen': (dossier.get('vehicle') or {}).get('license_plate')
                                        }
                        
            except Exception as e:
                logger.warning(f"Gudat-Integration fehlgeschlagen: {e}")
        
        # =====================================================================
        # 4. ERGEBNISSE ZUSAMMENFÜHREN
        # =====================================================================
        result = []
        
        for a in auftraege_raw:
            auftrag_nr = a['auftrag_nr']
            vorgabe_aw = float(a['vorgabe_aw'] or 0)
            gestempelt_aw = float(a['gestempelt_aw'] or 0)
            
            # ML-Daten
            ml = ml_predictions.get(auftrag_nr, {})
            ml_vorhersage = ml.get('vorhersage_aw')
            ml_potenzial = ml.get('potenzial_aw', 0)
            
            # ML-Status bestimmen
            if ml_vorhersage:
                if ml_potenzial > 1.0:
                    ml_status = 'unterbewertet'  # ML sagt: dauert deutlich länger
                    ml_status_icon = '🔴'
                elif ml_potenzial > 0.3:
                    ml_status = 'leicht_unterbewertet'
                    ml_status_icon = '🟡'
                elif ml_potenzial < -0.5:
                    ml_status = 'überbewertet'  # ML sagt: geht schneller
                    ml_status_icon = '🟢'
                else:
                    ml_status = 'ok'
                    ml_status_icon = '⚪'
            else:
                ml_status = None
                ml_status_icon = None
            
            # Gudat-Daten
            gudat = gudat_termine.get(auftrag_nr, {})
            
            # Mechaniker-Effizienz
            mech_nr = a['mechaniker_nr'] or a['aktiv_mechaniker_nr']
            mech_eff = mechaniker_effizienz.get(mech_nr) if mech_nr else None
            
            # Live-Status
            ist_aktiv = a['aktiv_mechaniker_nr'] is not None
            
            # Fortschritt berechnen
            if ist_aktiv and vorgabe_aw > 0:
                fortschritt_prozent = round(gestempelt_aw / vorgabe_aw * 100, 0)
            else:
                fortschritt_prozent = 0
            
            result.append({
                # Basis-Daten
                'auftrag_nr': auftrag_nr,
                'betrieb': a['betrieb'],
                'betrieb_name': BETRIEB_NAMEN.get(a['betrieb'], '?'),
                'datum': format_datetime(a['auftrag_datum']),
                'kennzeichen': a['kennzeichen'],
                'marke': a['marke'],
                'modell': a['modell'],
                'kunde': a['kunde'],
                'serviceberater': a['serviceberater_name'],
                'dringlichkeit': a['dringlichkeit'],
                
                # Status
                'ist_offen': a['ist_offen'],
                'ist_aktiv': ist_aktiv,
                'fortschritt_prozent': fortschritt_prozent,
                
                # Vorgabe & Stempelung
                'vorgabe_aw': vorgabe_aw,
                'gestempelt_aw': round(gestempelt_aw, 1),
                'gestempelt_min': int(a['gestempelt_min'] or 0),
                'rest_aw': round(max(0, vorgabe_aw - gestempelt_aw), 1),
                
                # Mechaniker
                'mechaniker_nr': mech_nr,
                'mechaniker_name': a['mechaniker_name'] or (f"MA {mech_nr}" if mech_nr else None),
                'mechaniker_effizienz': mech_eff,
                
                # ML-Vorhersage (DRIVE V5.1)
                'ml_vorhersage_aw': ml_vorhersage,
                'ml_potenzial_aw': ml_potenzial if ml_vorhersage else None,
                'ml_potenzial_prozent': ml.get('potenzial_prozent'),
                'ml_status': ml_status,
                'ml_status_icon': ml_status_icon,
                'ml_correction_factor': ml.get('correction_factor'),
                'ml_correction_source': ml.get('correction_source'),
                'ml_version': ml.get('konfidenz'),
                
                # Gudat-Termin
                'gudat_termin': gudat.get('termin_start'),
                'gudat_termin_ende': gudat.get('termin_ende'),
                'gudat_typ': gudat.get('typ'),
                'hat_gudat_termin': len(gudat) > 0,
                
                # Geplante Zeiten aus Locosoft
                'geplant_eingang': format_datetime(a['geplant_eingang']),
                'geplant_fertig': format_datetime(a['geplant_fertig'])
            })
        
        # =====================================================================
        # 5. STATISTIKEN
        # =====================================================================
        total_vorgabe = sum(a['vorgabe_aw'] for a in result)
        total_gestempelt = sum(a['gestempelt_aw'] for a in result)
        aktive_auftraege = sum(1 for a in result if a['ist_aktiv'])
        unterbewertet = sum(1 for a in result if a['ml_status'] == 'unterbewertet')
        mit_gudat = sum(1 for a in result if a['hat_gudat_termin'])
        
        # Potenzial berechnen (Summe aller unterbewerteten Aufträge)
        ml_potenzial_summe = sum(
            a['ml_potenzial_aw'] for a in result 
            if a['ml_potenzial_aw'] and a['ml_potenzial_aw'] > 0
        )
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'filter': {
                'subsidiary': subsidiary,
                'tage': tage,
                'nur_offen': nur_offen,
                'mit_ml': mit_ml,
                'mit_gudat': mit_gudat
            },
            'statistik': {
                'anzahl_auftraege': len(result),
                'aktive_auftraege': aktive_auftraege,
                'total_vorgabe_aw': round(total_vorgabe, 1),
                'total_gestempelt_aw': round(total_gestempelt, 1),
                'ml_unterbewertet': unterbewertet,
                'ml_potenzial_aw': round(ml_potenzial_summe, 1),
                'mit_gudat_termin': mit_gudat
            },
            'auftraege': result
        })
        
    except Exception as e:
        logger.exception("Fehler bei auftraege-enriched")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# ANWESENHEITS-REPORT V2 - TAG 130
# Basiert auf Type 2 (produktiv) statt Type 1 (anwesend)
# Type 2 ist sofort verfügbar, Type 1 erst nach Feierabend
# ============================================================

@werkstatt_live_bp.route('/anwesenheit', methods=['GET'])
def get_anwesenheit_v2():
    """
    Anwesenheits-Report V2: Wer hat heute gearbeitet?

    TAG 151: Refaktoriert - nutzt WerkstattData.get_anwesenheit()
    Vorher: 160 LOC | Nachher: 35 LOC

    Query-Parameter:
    - datum: Datum im Format YYYY-MM-DD (default: heute)
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    """
    try:
        from api.werkstatt_data import WerkstattData

        datum_str = request.args.get('datum')
        subsidiary = request.args.get('subsidiary', type=int)

        datum = None
        if datum_str:
            datum = datetime.strptime(datum_str, '%Y-%m-%d').date()

        data = WerkstattData.get_anwesenheit(datum=datum, betrieb=subsidiary)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            'timestamp': datetime.now().isoformat(),
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei Anwesenheits-Report V2")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# ANWESENHEITS-REPORT V1 (Legacy) - TAG 116
# DEAKTIVIERT TAG 122: Type 1 nur als abgeschlossene Einträge verfügbar
# ============================================================

@werkstatt_live_bp.route('/anwesenheit/legacy', methods=['GET'])
def get_anwesenheit_report():
    """
    Anwesenheits-Report Legacy: Type 1 basiert

    TAG 151: Refaktoriert - nutzt WerkstattData.get_anwesenheit_legacy()
    Vorher: 130 LOC | Nachher: 25 LOC
    """
    try:
        from api.werkstatt_data import WerkstattData

        subsidiary = request.args.get('subsidiary', type=int)

        data = WerkstattData.get_anwesenheit_legacy(betrieb=subsidiary)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            'timestamp': datetime.now().isoformat(),
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei Anwesenheits-Report")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# DRIVE KULANZ-MONITORING - TAG 119
# Zeigt nicht abgerechnete Arbeitszeit (Revenue Leakage)
# ============================================================

@werkstatt_live_bp.route('/drive/kulanz-monitoring', methods=['GET'])
def get_kulanz_monitoring():
    """
    DRIVE Kulanz-Monitoring: Wo verlieren wir Geld?

    TAG 151: Refaktoriert - nutzt WerkstattData.get_kulanz_monitoring()
    Vorher: 160 LOC | Nachher: 25 LOC

    Query-Parameter:
    - wochen: Anzahl Wochen zurueck (default: 4)
    - subsidiary: Betrieb filtern (optional)
    """
    try:
        from api.werkstatt_data import WerkstattData

        wochen = int(request.args.get('wochen', 4))
        subsidiary = request.args.get('subsidiary', type=int)

        data = WerkstattData.get_kulanz_monitoring(wochen=wochen, betrieb=subsidiary)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei Kulanz-Monitoring")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# DRIVE TAGES-BRIEFING - TAG 119
# Morgen-Report für Werkstattleiter
# ============================================================

@werkstatt_live_bp.route('/drive/briefing', methods=['GET'])
def get_drive_briefing():
    """
    DRIVE Tages-Briefing: 5-Minuten-Ueberblick fuer Werkstattleiter

    TAG 152: Refaktoriert - nutzt WerkstattData.get_drive_briefing()
    Vorher: 165 LOC | Nachher: 30 LOC
    """
    try:
        from api.werkstatt_data import WerkstattData

        subsidiary = request.args.get('subsidiary', type=int)

        data = WerkstattData.get_drive_briefing(betrieb=subsidiary)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei DRIVE Briefing")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# DRIVE KAPAZITÄT MIT G-FAKTOR - TAG 119
# Erweitert Kapazitätsplanung mit DRIVE-Korrekturen
# ============================================================

@werkstatt_live_bp.route('/drive/kapazitaet', methods=['GET'])
def get_drive_kapazitaet():
    """
    DRIVE Kapazitaetsplanung: Realistische Auslastung

    TAG 152: Refaktoriert - nutzt WerkstattData.get_drive_kapazitaet()
    Vorher: 210 LOC | Nachher: 35 LOC
    """
    try:
        from api.werkstatt_data import WerkstattData

        wochen = int(request.args.get('wochen', 4))
        subsidiary = request.args.get('subsidiary', type=int)

        data = WerkstattData.get_drive_kapazitaet(wochen=wochen, betrieb=subsidiary)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei DRIVE Kapazitaet")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# WERKSTATT LIVE-BOARD (TAG 125)
# Gantt-ähnliche Ansicht: Wer arbeitet gerade an was?
# Hybrid: Geplante Aufträge (aus Disposition) + Live-Stempelstatus
# =============================================================================

@werkstatt_live_bp.route('/board', methods=['GET'])
def get_werkstatt_liveboard():
    """
    Werkstatt Live-Board: Echtzeit-Übersicht aller Mechaniker und ihrer Aufträge.

    HYBRID-ANSATZ:
    1. Geplante Aufträge aus Disposition (orders + labours) - Was ist für heute geplant?
    2. Live-Stempelstatus (times) - Wer arbeitet GERADE an was?

    Zeigt für jeden Mechaniker:
    - Geplante Aufträge für heute (aus Disposition)
    - Live-Status: Aktuell in Arbeit (grün pulsierend)
    - Abgeschlossene Aufträge (lila)
    - Urlaub/Krank Status

    Query-Parameter:
    - betrieb: 1=DEG, 2=Hyundai, 3=Landau (optional, default=alle)
    - datum: YYYY-MM-DD (optional, default=heute)

    Returns:
        JSON mit Mechaniker-Liste und ihren Zeitblöcken + Eingangs-Liste
    """
    try:
        # Parameter
        # TAG 126: Standort-Filter erweitert
        # betrieb=1 → Nur Deggendorf (subsidiary 1)
        # betrieb=deg → Deggendorf + Hyundai (subsidiary 1 + 2)
        # betrieb=3 → Nur Landau (subsidiary 3)
        betrieb_param = request.args.get('betrieb', '')
        datum_str = request.args.get('datum')

        # Betrieb-Filter parsen
        betrieb_subsidiaries = None
        if betrieb_param:
            if betrieb_param.lower() == 'deg':
                betrieb_subsidiaries = [1, 2]  # Deggendorf + Hyundai
            elif betrieb_param == '1':
                betrieb_subsidiaries = [1]  # Nur Deggendorf
            elif betrieb_param == '3':
                betrieb_subsidiaries = [3]  # Nur Landau

        if datum_str:
            try:
                datum = datetime.strptime(datum_str, '%Y-%m-%d').date()
            except ValueError:
                datum = datetime.now().date()
        else:
            datum = datetime.now().date()

        conn = get_locosoft_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Keine Datenbankverbindung'}), 500

        cur = conn.cursor(cursor_factory=RealDictCursor)

        # 1. Alle AKTIVEN Mechaniker holen (mit Gruppen-Filter für Werkstatt)
        # Nutze employees_history mit is_latest_record um ausgeschiedene MA zu filtern
        # TAG 126: Azubis (A-%) und Werkstattleiter (5005) ausfiltern für Kiosk-Ansicht
        mechaniker_query = """
            SELECT DISTINCT
                eh.employee_number,
                eh.name,
                egm.grp_code,
                eh.subsidiary
            FROM employees_history eh
            JOIN employees_group_mapping egm ON eh.employee_number = egm.employee_number
            WHERE egm.grp_code IN ('MON', 'LAK')
              AND egm.grp_code NOT LIKE 'A-%%'
              AND eh.employee_number != 5005
              AND eh.is_latest_record = true
              AND eh.leave_date IS NULL
        """
        params = []

        if betrieb_subsidiaries:
            placeholders = ','.join(['%s'] * len(betrieb_subsidiaries))
            mechaniker_query += f" AND eh.subsidiary IN ({placeholders})"
            params.extend(betrieb_subsidiaries)

        mechaniker_query += " ORDER BY eh.subsidiary, eh.name"

        cur.execute(mechaniker_query, params)
        mechaniker_list = cur.fetchall()

        # 2. Abwesenheiten für heute holen
        cur.execute("""
            SELECT ac.employee_number, at.description as grund
            FROM absence_calendar ac
            JOIN absence_types at ON ac.type = at.type
            WHERE ac.date = %s
        """, [datum])
        abwesenheiten = {row['employee_number']: row['grund'] for row in cur.fetchall()}

        # TAG 127: Portal-Abwesenheiten hinzufügen (ZA, Krank aus Urlaubsplaner)
        try:
            portal_absences = get_portal_absences(datum)
            for emp_nr, absence in portal_absences.items():
                if emp_nr not in abwesenheiten:
                    abwesenheiten[emp_nr] = f"{absence['vacation_type']} (Portal)"
        except Exception as e:
            logger.warning(f"Portal-Abwesenheiten für Liveboard: {e}")

        # 3. GEPLANTE AUFTRÄGE für heute (aus Disposition)
        # TAG 127: NUR Aufträge wo BRINGEN = heute
        # Alte Aufträge (bringen früher) werden nicht mehr angezeigt
        cur.execute("""
            SELECT DISTINCT
                o.number as auftrag_nr,
                v.license_plate as kennzeichen,
                COALESCE(cs.family_name, '') || ' ' || COALESCE(cs.first_name, '') as kunde,
                v.free_form_make_text as marke,
                o.estimated_inbound_time as bringen,
                o.estimated_outbound_time as abholen,
                o.subsidiary,
                l.mechanic_no,
                SUM(l.time_units) OVER (PARTITION BY o.number, l.mechanic_no) as vorgabe_aw,
                o.has_open_positions as ist_offen
            FROM orders o
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
            LEFT JOIN labours l ON o.number = l.order_number
            WHERE DATE(o.estimated_inbound_time) = %s
        """, [datum])
        geplante_auftraege_raw = cur.fetchall()

        # Gruppieren nach Mechaniker
        geplant_pro_mechaniker = {}
        unverplante_auftraege = []

        for a in geplante_auftraege_raw:
            auftrag_data = {
                'auftrag_nr': a['auftrag_nr'],
                'kennzeichen': a['kennzeichen'] or '',
                'kunde': (a['kunde'] or '').strip(),
                'marke': a['marke'] or '',
                'bringen': a['bringen'].strftime('%H:%M') if a['bringen'] else None,
                'bringen_ts': a['bringen'].isoformat() if a['bringen'] else None,
                'abholen': a['abholen'].strftime('%H:%M') if a['abholen'] else None,
                'abholen_ts': a['abholen'].isoformat() if a['abholen'] else None,
                'vorgabe_aw': float(a['vorgabe_aw'] or 0),
                'subsidiary': a['subsidiary'],
                'typ': 'geplant',
                'ist_fertig': not a['ist_offen']  # TAG 126: Fertig wenn nicht mehr offen
            }

            # TAG 127: Aufträge von früheren Tagen nicht als "geplant" anzeigen
            # Wenn bringen nicht heute ist, wird der Auftrag ausgeblendet
            # (unabhängig von ist_fertig - alte offene Aufträge sind Datenpflege-Problem)
            bringen_heute = a['bringen'] and a['bringen'].date() == datum
            if not bringen_heute:
                continue

            mech_nr = a['mechanic_no']
            if mech_nr:
                if mech_nr not in geplant_pro_mechaniker:
                    geplant_pro_mechaniker[mech_nr] = []
                # Duplikate vermeiden
                if not any(x['auftrag_nr'] == auftrag_data['auftrag_nr'] for x in geplant_pro_mechaniker[mech_nr]):
                    geplant_pro_mechaniker[mech_nr].append(auftrag_data)
            else:
                # Unverplant (kein Mechaniker zugewiesen)
                # TAG 126: Betrieb-Filter auch auf unverplante anwenden
                if betrieb_subsidiaries and a['subsidiary'] not in betrieb_subsidiaries:
                    continue
                if not any(x['auftrag_nr'] == auftrag_data['auftrag_nr'] for x in unverplante_auftraege):
                    unverplante_auftraege.append(auftrag_data)

        # 4. LIVE-STEMPELUNGEN für heute (wer arbeitet GERADE an was)
        cur.execute("""
            SELECT DISTINCT ON (t.employee_number, t.order_number)
                t.employee_number,
                t.order_number,
                t.start_time,
                t.end_time,
                t.duration_minutes
            FROM times t
            WHERE DATE(t.start_time) = %s
              AND t.type = 2
            ORDER BY t.employee_number, t.order_number, t.start_time DESC
        """, [datum])
        live_stempelungen = cur.fetchall()

        # Gruppieren nach Mechaniker
        live_pro_mechaniker = {}
        for s in live_stempelungen:
            emp = s['employee_number']
            if emp not in live_pro_mechaniker:
                live_pro_mechaniker[emp] = []
            live_pro_mechaniker[emp].append({
                'auftrag_nr': s['order_number'],
                'start': s['start_time'].strftime('%H:%M') if s['start_time'] else None,
                'start_ts': s['start_time'].isoformat() if s['start_time'] else None,
                'ende': s['end_time'].strftime('%H:%M') if s['end_time'] else None,
                'ende_ts': s['end_time'].isoformat() if s['end_time'] else None,
                'dauer_min': s['duration_minutes'] or 0,
                'ist_aktiv': s['end_time'] is None,
                '_start_time': s['start_time']  # Für Verwaist-Check
            })

        # TAG 126: Verwaiste offene Stempelungen als nicht-aktiv markieren
        # Wenn ein MA nach einer offenen Stempelung andere Aufträge beendet hat,
        # ist die offene Stempelung "verwaist" und nicht mehr aktiv
        for emp, stempelungen in live_pro_mechaniker.items():
            # Finde neueste abgeschlossene Stempelung
            abgeschlossene = [s for s in stempelungen if s['ende'] is not None]
            if abgeschlossene:
                # Sortiere nach Startzeit um das nächste Ende zu finden
                abgeschlossene_sorted = sorted(abgeschlossene, key=lambda x: x['_start_time'])
                for s in stempelungen:
                    if s['ist_aktiv']:
                        # Finde die nächste abgeschlossene Stempelung nach dieser offenen
                        naechste = next(
                            (a for a in abgeschlossene_sorted if a['_start_time'] > s['_start_time']),
                            None
                        )
                        if naechste:
                            # Verwaiste Stempelung: Ende setzen auf Start der nächsten
                            s['ist_aktiv'] = False
                            s['ende'] = naechste['_start_time'].strftime('%H:%M')
                            s['ende_ts'] = naechste['_start_time'].isoformat()
                            # Dauer nachträglich berechnen
                            dauer = (naechste['_start_time'] - s['_start_time']).total_seconds() / 60
                            s['dauer_min'] = int(dauer)
                            s['ist_verwaist'] = True  # Markierung für UI
            # Cleanup: _start_time entfernen
            for s in stempelungen:
                del s['_start_time']

        # 4a. Auftragsdetails für alle Live-Stempelungen holen (inkl. AW aus labours)
        alle_live_auftraege = list(set(s['order_number'] for s in live_stempelungen))
        auftrags_details = {}
        if alle_live_auftraege:
            placeholders = ','.join(['%s'] * len(alle_live_auftraege))
            cur.execute(f"""
                SELECT
                    o.number as auftrag_nr,
                    v.license_plate as kennzeichen,
                    COALESCE(cs.family_name, '') || ' ' || COALESCE(cs.first_name, '') as kunde,
                    v.free_form_make_text as marke,
                    COALESCE(l.gesamt_aw, 0) as vorgabe_aw,
                    o.has_open_positions as ist_offen
                FROM orders o
                LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
                LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
                LEFT JOIN (
                    SELECT order_number, SUM(time_units) as gesamt_aw
                    FROM labours
                    WHERE time_units > 0
                    GROUP BY order_number
                ) l ON o.number = l.order_number
                WHERE o.number IN ({placeholders})
            """, alle_live_auftraege)
            for row in cur.fetchall():
                auftrags_details[row['auftrag_nr']] = {
                    'kennzeichen': row['kennzeichen'] or '',
                    'kunde': (row['kunde'] or '').strip(),
                    'marke': row['marke'] or '',
                    'vorgabe_aw': float(row['vorgabe_aw'] or 0),
                    'ist_fertig': not row['ist_offen']
                }

        
        # ================================================================
        # TAG 153: GUDAT-INTEGRATION - MIGRATION VORBEREITET
        # Nutzt noch lokale Funktionen, später auf GudatData umstellen:
        # - GudatData.create_mechaniker_mapping() statt match_gudat_name()
        # - GudatData.merge_zeitbloecke() statt inline Merge-Logik
        # Siehe: docs/GUDAT_TO_LOCOSOFT_MIGRATION.md
        # ================================================================
        # 4b. GUDAT Disposition holen (TAG 125)
        gudat_disposition = get_gudat_disposition(datum)

        # TAG 154: Gudat-Mechaniker-Mapping über GudatData (vorher ~30 LOC)
        gudat_to_locosoft = GudatData.create_mechaniker_mapping(mechaniker_list, gudat_disposition)

        # 5. Mechaniker-Daten zusammenführen
        result_mechaniker = []

        for mech in mechaniker_list:
            emp_nr = mech['employee_number']
            abwesend_grund = abwesenheiten.get(emp_nr)

            # Geplante Aufträge für diesen Mechaniker
            geplante = geplant_pro_mechaniker.get(emp_nr, [])

            # Live-Stempelungen für diesen Mechaniker
            live = live_pro_mechaniker.get(emp_nr, [])

            # Aktiver Auftrag (aus Live-Stempelungen)
            aktiver_auftrag = next((l for l in live if l['ist_aktiv']), None)

            # Zeitblöcke: Kombination aus geplant + live
            zeitbloecke = []

            # Geplante Aufträge hinzufügen
            for g in geplante:
                # Prüfen ob dieser Auftrag schon gestempelt wird
                live_match = next((l for l in live if l['auftrag_nr'] == g['auftrag_nr']), None)

                zb = {
                    'auftrag_nr': g['auftrag_nr'],
                    'kennzeichen': g['kennzeichen'],
                    'kunde': g['kunde'],
                    'marke': g['marke'],
                    'vorgabe_aw': g['vorgabe_aw'],
                    'bringen': g['bringen'],
                    'abholen': g['abholen'],
                    'typ': 'geplant',
                    'ist_fertig': g.get('ist_fertig', False)  # TAG 126: Fertig-Symbol
                }

                if live_match:
                    # Auftrag wird gerade bearbeitet
                    zb['start'] = live_match['start']
                    zb['start_ts'] = live_match['start_ts']
                    zb['ende'] = live_match['ende']
                    zb['ende_ts'] = live_match['ende_ts']
                    zb['ist_aktiv'] = live_match['ist_aktiv']
                    zb['dauer_min'] = live_match['dauer_min']
                    zb['typ'] = 'aktiv' if live_match['ist_aktiv'] else 'bearbeitet'
                else:
                    # Noch nicht angefangen
                    zb['start'] = g['bringen']
                    zb['start_ts'] = g['bringen_ts']
                    zb['ende'] = g['abholen']
                    zb['ende_ts'] = g['abholen_ts']
                    zb['ist_aktiv'] = False
                    zb['dauer_min'] = 0

                zeitbloecke.append(zb)

            # Live-Aufträge die NICHT in geplant sind (Ad-hoc Arbeiten)
            for l in live:
                if not any(z['auftrag_nr'] == l['auftrag_nr'] for z in zeitbloecke):
                    # Details aus Locosoft holen (falls verfügbar)
                    details = auftrags_details.get(l['auftrag_nr'], {})
                    zeitbloecke.append({
                        'auftrag_nr': l['auftrag_nr'],
                        'kennzeichen': details.get('kennzeichen', ''),
                        'kunde': details.get('kunde', ''),
                        'marke': details.get('marke', ''),
                        'vorgabe_aw': details.get('vorgabe_aw', 0),
                        'start': l['start'],
                        'start_ts': l['start_ts'],
                        'ende': l['ende'],
                        'ende_ts': l['ende_ts'],
                        'ist_aktiv': l['ist_aktiv'],
                        'dauer_min': l['dauer_min'],
                        'typ': 'aktiv' if l['ist_aktiv'] else 'bearbeitet',
                        'ist_fertig': details.get('ist_fertig', False)  # TAG 126: Fertig-Symbol
                    })

            # GUDAT Disposition hinzufügen (TAG 125)
            gudat_tasks = gudat_to_locosoft.get(emp_nr, [])

            # Finde letzte Endzeit aus bestehenden Zeitblöcken für Gudat-Stacking
            gudat_start_time = datetime.combine(datum, time(8, 0))  # Default 08:00
            for zb in zeitbloecke:
                if zb.get('ende_ts'):
                    try:
                        ende_dt = datetime.fromisoformat(zb['ende_ts'])
                        if ende_dt > gudat_start_time:
                            gudat_start_time = ende_dt
                    except:
                        pass

            for gt in gudat_tasks:
                # Prüfen ob dieser Auftrag schon in zeitbloecke ist
                auftrag_nr = gt.get('auftrag_nr')
                existing = next((z for z in zeitbloecke if z.get('auftrag_nr') == auftrag_nr), None)
                if existing:
                    # Gudat-Daten in bestehenden Block mergen (AW, Kennzeichen falls leer)
                    if not existing.get('kennzeichen') and gt.get('kennzeichen'):
                        existing['kennzeichen'] = gt.get('kennzeichen')
                    if not existing.get('vorgabe_aw') and gt.get('vorgabe_aw'):
                        existing['vorgabe_aw'] = gt.get('vorgabe_aw')
                    # TAG 126: Gudat-Startzeit hat Vorrang (aktuellere Disposition!)
                    if gt.get('start_date') and not existing.get('ist_aktiv'):
                        try:
                            start_str = gt['start_date'].replace('T', ' ')
                            gudat_time = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
                            existing['start'] = gudat_time.strftime('%H:%M')
                            existing['start_ts'] = gudat_time.isoformat()
                            # Ende neu berechnen
                            aw = existing.get('vorgabe_aw') or gt.get('vorgabe_aw') or 2
                            dauer = max(int(aw * 6), 30)
                            ende_time = gudat_time + timedelta(minutes=dauer)
                            existing['ende'] = ende_time.strftime('%H:%M')
                            existing['ende_ts'] = ende_time.isoformat()
                        except (ValueError, TypeError):
                            pass
                    continue  # Nicht nochmal hinzufügen
                # Auch prüfen ob Kennzeichen schon drin ist
                kz = gt.get('kennzeichen', '').replace(' ', '').replace('-', '').upper()
                if kz:
                    existing_by_kz = next(
                        (z for z in zeitbloecke
                         if (z.get('kennzeichen') or '').replace(' ', '').replace('-', '').upper() == kz),
                        None
                    )
                    if existing_by_kz:
                        # TAG 126: Auch hier Gudat-Zeit übernehmen
                        if gt.get('start_date') and not existing_by_kz.get('ist_aktiv'):
                            try:
                                start_str = gt['start_date'].replace('T', ' ')
                                gudat_time = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
                                existing_by_kz['start'] = gudat_time.strftime('%H:%M')
                                existing_by_kz['start_ts'] = gudat_time.isoformat()
                                aw = existing_by_kz.get('vorgabe_aw') or gt.get('vorgabe_aw') or 2
                                dauer = max(int(aw * 6), 30)
                                ende_time = gudat_time + timedelta(minutes=dauer)
                                existing_by_kz['ende'] = ende_time.strftime('%H:%M')
                                existing_by_kz['ende_ts'] = ende_time.isoformat()
                            except (ValueError, TypeError):
                                pass
                        continue  # Schon vorhanden

                # TAG 126: Echte Startzeit aus Gudat verwenden (falls vorhanden)
                task_start_time = gudat_start_time  # Fallback
                if gt.get('start_date'):
                    try:
                        # Gudat Format: "2025-12-18 10:30:00" oder "2025-12-18T10:30:00"
                        start_str = gt['start_date'].replace('T', ' ')
                        task_start_time = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        pass  # Bei Fehler Fallback verwenden

                # Geschätzte Dauer: AW * 6 Minuten (oder min 30 Min)
                aw = gt.get('vorgabe_aw', 0) or 2
                dauer_min = max(int(aw * 6), 30)
                task_ende_time = task_start_time + timedelta(minutes=dauer_min)

                zeitbloecke.append({
                    'auftrag_nr': auftrag_nr,
                    'kennzeichen': gt.get('kennzeichen', ''),
                    'kunde': '',
                    'marke': '',
                    'vorgabe_aw': gt.get('vorgabe_aw', 0),
                    'beschreibung': gt.get('beschreibung', ''),
                    'service': gt.get('service', ''),
                    'gudat_status': gt.get('status', ''),
                    'start': task_start_time.strftime('%H:%M'),
                    'start_ts': task_start_time.isoformat(),
                    'ende': task_ende_time.strftime('%H:%M'),
                    'ende_ts': task_ende_time.isoformat(),
                    'ist_aktiv': False,
                    'dauer_min': dauer_min,
                    'typ': 'gudat_geplant'
                })

                # Für Fallback: nächster Task ohne Gudat-Zeit startet nach diesem
                if task_ende_time > gudat_start_time:
                    gudat_start_time = task_ende_time

            # Sortieren nach Startzeit/Bringen
            zeitbloecke.sort(key=lambda x: x.get('start_ts') or x.get('bringen_ts') or '')

            # Gesamte Arbeitszeit berechnen
            gesamt_minuten = sum(zb.get('dauer_min', 0) for zb in zeitbloecke if not zb.get('ist_aktiv'))
            if aktiver_auftrag and aktiver_auftrag.get('start_ts'):
                start_dt = datetime.fromisoformat(aktiver_auftrag['start_ts'])
                laufzeit = (datetime.now() - start_dt).total_seconds() / 60
                gesamt_minuten += laufzeit

            # Gesamt-AW geplant
            gesamt_aw_geplant = sum(zb.get('vorgabe_aw', 0) for zb in zeitbloecke)

            # TAG 126: Leerlauf-Zeit berechnen (für Warnung)
            leerlauf_minuten = 0
            nie_gestempelt = True
            if aktiver_auftrag:
                # Hat aktiven Auftrag = kein Leerlauf
                leerlauf_minuten = 0
                nie_gestempelt = False
            elif zeitbloecke:
                # Finde letzte beendete Stempelung
                beendete = [zb for zb in zeitbloecke if zb.get('ende_ts') and not zb.get('ist_aktiv')]
                if beendete:
                    nie_gestempelt = False
                    letzte_ende = max(datetime.fromisoformat(zb['ende_ts']) for zb in beendete)
                    leerlauf_minuten = (datetime.now() - letzte_ende).total_seconds() / 60

            # Kurznamen ableiten: "Nachname, Vorname" -> "Vorname"
            full_name = mech['name'] or ''
            if ',' in full_name:
                short_name = full_name.split(',')[1].strip().split()[0]  # Vorname
            else:
                short_name = full_name.split()[0] if full_name else '?'

            result_mechaniker.append({
                'employee_number': emp_nr,
                'name': mech['name'],
                'short_name': short_name,
                'betrieb': mech['subsidiary'],
                'betrieb_name': BETRIEB_NAMEN.get(mech['subsidiary'], '?'),
                'gruppe': mech['grp_code'],
                'ist_abwesend': abwesend_grund is not None,
                'abwesend_grund': abwesend_grund,
                'zeitbloecke': zeitbloecke,
                'aktiver_auftrag': aktiver_auftrag,
                'anzahl_auftraege': len(zeitbloecke),
                'gesamt_minuten': round(gesamt_minuten),
                'gesamt_aw_geplant': round(gesamt_aw_geplant, 1),
                'leerlauf_minuten': round(leerlauf_minuten),
                'nie_gestempelt': nie_gestempelt
            })

        cur.close()
        conn.close()

        # Nach Betrieb gruppieren
        betriebe = {}
        for m in result_mechaniker:
            b = m['betrieb']
            if b not in betriebe:
                betriebe[b] = {
                    'betrieb': b,
                    'name': BETRIEB_NAMEN.get(b, '?'),
                    'mechaniker': []
                }
            betriebe[b]['mechaniker'].append(m)

        # Gudat-Stats
        gudat_tasks_total = sum(len(tasks) for tasks in gudat_disposition.values())
        gudat_matched = len(gudat_to_locosoft)

        return jsonify({
            'success': True,
            'datum': datum.isoformat(),
            'timestamp': datetime.now().isoformat(),
            'betriebe': list(betriebe.values()),
            'mechaniker': result_mechaniker,
            'eingang': unverplante_auftraege,  # Unverplante Aufträge (Eingangs-Liste)
            'gesamt_mechaniker': len(result_mechaniker),
            'gesamt_aktiv': sum(1 for m in result_mechaniker if m['aktiver_auftrag']),
            'gesamt_abwesend': sum(1 for m in result_mechaniker if m['ist_abwesend']),
            'gesamt_unverplant': len(unverplante_auftraege),
            'gudat_geladen': gudat_tasks_total > 0,
            'gudat_tasks': gudat_tasks_total,
            'gudat_mechaniker_matched': gudat_matched
        })

    except Exception as e:
        logger.exception("Fehler bei Werkstatt Live-Board")
        return jsonify({'success': False, 'error': str(e)}), 500
