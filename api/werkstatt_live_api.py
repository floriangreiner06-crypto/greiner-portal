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

# SSOT: Standort/Betriebsnamen
from api.standort_utils import BETRIEB_NAMEN

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

# TAG 213: Cache-Utilities für Performance-Optimierung
from api.cache_utils import cache_stempeluhr

# get_locosoft_connection() wird jetzt aus db_utils importiert (TAG 117)


# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def format_datetime(dt):
    """Formatiert datetime für JSON"""
    if dt is None:
        return None
    return dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)

# Gudat Credentials (TAG 125)
GUDAT_CONFIG = {
    'username': 'florian.greiner@auto-greiner.de',
    'password': 'Hyundai2025!'
}

def get_gudat_disposition(target_date=None):
    """
    Holt Werkstatt-Disposition aus Gudat (workshopTasks).
    Returns dict: {mechaniker_name: [tasks]}
    """
    if not GUDAT_AVAILABLE:
        logger.warning("GudatClient nicht verfügbar")
        return {}

    from datetime import date
    if target_date is None:
        target_date = date.today().isoformat()
    elif hasattr(target_date, 'isoformat'):
        target_date = target_date.isoformat()

    try:
        client = GudatClient(GUDAT_CONFIG['username'], GUDAT_CONFIG['password'])
        if not client.login():
            logger.error("Gudat Login fehlgeschlagen")
            return {}

        # GraphQL Query für workshopTasks
        query = """
        query GetWorkshopTasks($page: Int!, $itemsPerPage: Int!, $where: QueryWorkshopTasksWhereWhereConditions) {
          workshopTasks(first: $itemsPerPage, page: $page, where: $where) {
            data {
              id
              start_date
              work_load
              work_state
              description
              workshopService { id name }
              resource { id name }
              dossier {
                id
                vehicle { id license_plate }
                orders { id number }
              }
            }
          }
        }
        """

        variables = {
            "page": 1,
            "itemsPerPage": 200,
            "where": {
                "AND": [{"column": "START_DATE", "operator": "EQ", "value": target_date}]
            }
        }

        response = client.session.post(
            f"{GudatClient.BASE_URL}/graphql",
            json={"operationName": "GetWorkshopTasks", "query": query, "variables": variables},
            headers={
                'Accept': 'application/json',
                'X-XSRF-TOKEN': client._get_xsrf(),
                'Content-Type': 'application/json'
            }
        )

        data = response.json()
        if 'errors' in data:
            logger.error(f"Gudat GraphQL Fehler: {data['errors']}")
            return {}

        tasks = data.get('data', {}).get('workshopTasks', {}).get('data', [])

        # Gruppiere nach Mechaniker (resource.name)
        by_mechanic = {}
        for task in tasks:
            resource = task.get('resource')
            if not resource:
                continue
            mech_name = resource.get('name', '').strip()
            if not mech_name:
                continue

            # Dossier-Daten extrahieren
            dossier = task.get('dossier') or {}
            vehicle = dossier.get('vehicle') or {}
            orders = dossier.get('orders') or []

            # TAG 126: start_date aus Gudat extrahieren für korrekte Zeitpositionierung
            gudat_start = task.get('start_date')  # Format: "2025-12-18 10:30:00"

            task_data = {
                'gudat_id': task.get('id'),
                'kennzeichen': vehicle.get('license_plate', ''),
                'auftrag_nr': orders[0].get('number') if orders else None,
                'vorgabe_aw': float(task.get('work_load') or 0),
                'status': task.get('work_state', ''),
                'beschreibung': task.get('description', ''),
                'service': (task.get('workshopService') or {}).get('name', ''),
                'start_date': gudat_start  # Echte Startzeit aus Gudat
            }

            if mech_name not in by_mechanic:
                by_mechanic[mech_name] = []
            by_mechanic[mech_name].append(task_data)

        logger.info(f"Gudat: {len(tasks)} Tasks für {len(by_mechanic)} Mechaniker geladen")
        return by_mechanic

    except Exception as e:
        logger.error(f"Gudat Fehler: {e}")
        return {}

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
PAUSE_ENDE = time(12, 45)   # 12:45 Uhr
PAUSE_DAUER_MIN = 45        # 45 Minuten

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
@cache_stempeluhr(ttl=10)  # TAG 213: Cache mit 10 Sekunden TTL
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

        # Pausenzeit-Check (12:00-12:45)
        jetzt_zeit = datetime.now().time()
        ist_pausenzeit = time(12, 0) <= jetzt_zeit <= time(12, 45)

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
    Für Sensibilisierung von Serviceberatern und Fakturisten.
    
    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    - datum: Datum im Format YYYY-MM-DD (default: heute)
    - typ: alle|extern|intern (default: alle)
           extern = nur externe Kunden (echte Werkstattaufträge)
           intern = nur interne Aufträge (eigene Fahrzeuge)
    """
    try:
        subsidiary = request.args.get('subsidiary', type=int)
        datum_str = request.args.get('datum')
        typ_filter = request.args.get('typ', 'alle')  # alle, extern, intern
        
        if datum_str:
            datum = datetime.strptime(datum_str, '%Y-%m-%d').date()
        else:
            datum = datetime.now().date()
        
        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Heute abgerechnete Werkstatt-Aufträge
        # WICHTIG: Ausschluss von Fahrzeugverkäufen (invoice_type 7, 8)
        # Nur echte Werkstattarbeit: invoice_type 2, 4, 5, 6
        query = """
            WITH heute_rechnungen AS (
                SELECT 
                    i.order_number,
                    i.invoice_number,
                    i.invoice_type,
                    i.invoice_date,
                    i.job_amount_net,
                    i.subsidiary,
                    i.creating_employee,
                    o.order_customer as kunden_nr
                FROM invoices i
                LEFT JOIN orders o ON i.order_number = o.number
                WHERE DATE(i.invoice_date) = %s
                  AND i.invoice_type IN (2, 4, 5, 6)  -- Keine Fahrzeugverkäufe (7, 8)!
                  AND i.job_amount_net > 0
                  AND i.is_canceled = false
            ),
            -- Labours: ALLE AW des Auftrags (TAG 120 - Fix für unvollständige Abrechnungen)
            labour_summen AS (
                SELECT
                    l.order_number,
                    -- Gesamt-AW: ALLE Positionen (auch ohne Mechaniker-Zuordnung)
                    SUM(l.time_units) as gesamt_aw,
                    -- Fakturierte AW: Nur die bereits abgerechneten
                    SUM(CASE WHEN l.is_invoiced THEN l.time_units ELSE 0 END) as fakturiert_aw,
                    -- Offene AW: Noch nicht abgerechnet
                    SUM(CASE WHEN NOT l.is_invoiced THEN l.time_units ELSE 0 END) as offen_aw,
                    -- Zugeordnete AW (mit Mechaniker)
                    SUM(CASE WHEN l.mechanic_no IS NOT NULL THEN l.time_units ELSE 0 END) as zugeordnet_aw,
                    -- Nicht zugeordnete AW (ohne Mechaniker)
                    SUM(CASE WHEN l.mechanic_no IS NULL THEN l.time_units ELSE 0 END) as nicht_zugeordnet_aw,
                    SUM(l.net_price_in_order) as vorgabe_eur,
                    STRING_AGG(DISTINCT eh.name, ', ') as mechaniker_namen,
                    -- Gewichteter AW-Preis aus charge_types (Verrechnungssatz)
                    CASE
                        WHEN SUM(l.time_units) > 0 THEN
                            ROUND((SUM(l.time_units * COALESCE(ct.timeunit_rate, 0)) / NULLIF(SUM(l.time_units), 0))::numeric, 2)
                        ELSE 0
                    END as aw_preis_db,
                    -- Vollständig abgerechnet?
                    CASE
                        WHEN SUM(CASE WHEN NOT l.is_invoiced THEN l.time_units ELSE 0 END) > 0 THEN false
                        ELSE true
                    END as vollstaendig_abgerechnet
                FROM labours l
                LEFT JOIN employees_history eh ON l.mechanic_no = eh.employee_number
                    AND eh.is_latest_record = true
                LEFT JOIN charge_types ct ON l.charge_type = ct.type AND ct.subsidiary = 1
                WHERE l.order_number IN (SELECT order_number FROM heute_rechnungen)
                GROUP BY l.order_number
            ),
            -- Stempelungen: Gesamt-Zeit für diese Aufträge (DEDUPLIZIERT!)
            stempel_summen AS (
                SELECT 
                    order_number,
                    SUM(minuten) as gestempelt_min
                FROM (
                    SELECT DISTINCT ON (order_number, employee_number, start_time, end_time)
                        order_number,
                        EXTRACT(EPOCH FROM (COALESCE(end_time, NOW()) - start_time)) / 60 as minuten
                    FROM times
                    WHERE type = 2
                      AND order_number IN (SELECT order_number FROM heute_rechnungen)
                ) dedup
                GROUP BY order_number
            ),
            -- Auftragsdetails
            auftrags_details AS (
                SELECT 
                    o.number as order_number,
                    o.order_date,
                    o.order_taking_employee_no as sb_nr,
                    sb.name as sb_name,
                    v.license_plate as kennzeichen,
                    m.description as marke,
                    COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name, 'Unbekannt') as kunde,
                    cs.customer_number as kunden_nr,
                    -- Intern-Erkennung: Kundennummer 3000001 oder Name enthält 'intern'
                    CASE 
                        WHEN cs.customer_number = 3000001 THEN true
                        WHEN LOWER(cs.family_name) LIKE '%%intern%%' THEN true
                        WHEN LOWER(cs.family_name) LIKE '%%greiner%%' AND LOWER(cs.family_name) LIKE '%%auto%%' THEN true
                        ELSE false
                    END as ist_intern
                FROM orders o
                LEFT JOIN employees_history sb ON o.order_taking_employee_no = sb.employee_number
                    AND sb.is_latest_record = true
                LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
                LEFT JOIN makes m ON v.make_number = m.make_number
                LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
                WHERE o.number IN (SELECT order_number FROM heute_rechnungen)
            )
            SELECT
                r.order_number,
                r.invoice_number,
                r.invoice_type,
                r.subsidiary,
                ROUND(r.job_amount_net::numeric, 2) as rechnung_eur,
                -- TAG 120: Alle AW anzeigen (nicht nur zugeordnete)
                ROUND(COALESCE(l.gesamt_aw, 0)::numeric, 1) as vorgabe_aw,
                ROUND(COALESCE(l.fakturiert_aw, 0)::numeric, 1) as fakturiert_aw,
                ROUND(COALESCE(l.offen_aw, 0)::numeric, 1) as offen_aw,
                COALESCE(l.vollstaendig_abgerechnet, true) as vollstaendig_abgerechnet,
                ROUND(COALESCE(l.vorgabe_eur, 0)::numeric, 2) as vorgabe_eur,
                ROUND(COALESCE(l.aw_preis_db, 0)::numeric, 2) as aw_preis_db,
                ROUND(COALESCE(s.gestempelt_min, 0)::numeric / 6, 1) as gestempelt_aw,
                ROUND(COALESCE(s.gestempelt_min, 0)::numeric, 0) as gestempelt_min,
                l.mechaniker_namen,
                a.sb_name,
                a.sb_nr,
                a.kennzeichen,
                a.marke,
                a.kunde,
                a.kunden_nr,
                a.ist_intern,
                a.order_date
            FROM heute_rechnungen r
            LEFT JOIN labour_summen l ON r.order_number = l.order_number
            LEFT JOIN stempel_summen s ON r.order_number = s.order_number
            LEFT JOIN auftrags_details a ON r.order_number = a.order_number
            WHERE 1=1
        """
        
        params = [datum]
        
        # Betrieb-Filter
        if subsidiary:
            query += " AND r.subsidiary = %s"
            params.append(subsidiary)
        
        # Intern/Extern Filter
        if typ_filter == 'extern':
            query += " AND a.ist_intern = false"
        elif typ_filter == 'intern':
            query += " AND a.ist_intern = true"
        
        query += " ORDER BY (COALESCE(s.gestempelt_min, 0) / 6 - COALESCE(l.gesamt_aw, 0)) DESC"
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        # Nachkalkulation berechnen
        auftraege = []
        total_rechnung = 0
        total_vorgabe_aw = 0
        total_gestempelt_aw = 0
        total_verlust = 0
        probleme = 0
        
        for r in rows:
            vorgabe_aw = float(r['vorgabe_aw'] or 0)
            gestempelt_aw = float(r['gestempelt_aw'] or 0)
            rechnung_eur = float(r['rechnung_eur'] or 0)
            
            # Differenz berechnen
            diff_aw = gestempelt_aw - vorgabe_aw
            
            # AW-Preis aus charge_types (DB-Verrechnungssatz) verwenden
            aw_preis_db = float(r.get('aw_preis_db') or 0)
            
            if aw_preis_db > 0:
                # Verrechnungssatz aus Datenbank
                aw_preis = aw_preis_db
                verlust_eur = diff_aw * aw_preis
            elif vorgabe_aw > 0:
                # Fallback: AW-Preis aus Rechnung ableiten
                aw_preis = rechnung_eur / vorgabe_aw
                verlust_eur = diff_aw * aw_preis
            else:
                aw_preis = 0
                verlust_eur = 0
            
            # Leistungsgrad (Vorgabe / Gestempelt * 100)
            if gestempelt_aw > 0:
                leistungsgrad = vorgabe_aw / gestempelt_aw * 100
            else:
                leistungsgrad = 0
            
            # Status bestimmen
            if diff_aw <= 0:
                status = 'ok'  # Schneller als Vorgabe
            elif diff_aw <= 2:
                status = 'warnung'  # Leicht über Vorgabe
            else:
                status = 'kritisch'  # Deutlich über Vorgabe
                probleme += 1
            
            # TAG 120: Neue Felder für Abrechnungs-Status
            fakturiert_aw = float(r.get('fakturiert_aw') or 0)
            offen_aw = float(r.get('offen_aw') or 0)
            vollstaendig = r.get('vollstaendig_abgerechnet', True)

            auftraege.append({
                'order_number': r['order_number'],
                'invoice_number': r['invoice_number'],
                'invoice_type': r['invoice_type'],
                'betrieb': r['subsidiary'],
                'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], '?'),
                'rechnung_eur': rechnung_eur,
                'vorgabe_aw': vorgabe_aw,
                # TAG 120: Aufschlüsselung AW-Status
                'fakturiert_aw': fakturiert_aw,
                'offen_aw': offen_aw,
                'vollstaendig_abgerechnet': vollstaendig,
                'gestempelt_aw': gestempelt_aw,
                'gestempelt_min': int(r['gestempelt_min'] or 0),
                'diff_aw': round(diff_aw, 1),
                'aw_preis': round(aw_preis, 2),
                'verlust_eur': round(verlust_eur, 2),
                'leistungsgrad': round(leistungsgrad, 1),
                'status': status,
                'mechaniker': r['mechaniker_namen'],
                'serviceberater': r['sb_name'] or f"MA {r['sb_nr']}" if r['sb_nr'] else None,
                'serviceberater_nr': r['sb_nr'],
                'kennzeichen': r['kennzeichen'],
                'marke': r['marke'],
                'kunde': r['kunde'],
                'kunden_nr': r['kunden_nr'],
                'ist_intern': r['ist_intern'],
                'auftragsdatum': r['order_date'].strftime('%d.%m.%Y') if r['order_date'] else None
            })
            
            total_rechnung += rechnung_eur
            total_vorgabe_aw += vorgabe_aw
            total_gestempelt_aw += gestempelt_aw
            if verlust_eur > 0:
                total_verlust += verlust_eur

        # TAG 120: Unvollständig abgerechnete Aufträge zählen
        unvollstaendig = sum(1 for a in auftraege if not a.get('vollstaendig_abgerechnet', True))

        # Gesamt-Leistungsgrad
        if total_gestempelt_aw > 0:
            gesamt_leistungsgrad = total_vorgabe_aw / total_gestempelt_aw * 100
        else:
            gesamt_leistungsgrad = 0
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'datum': str(datum),
            'filter': {
                'subsidiary': subsidiary,
                'typ': typ_filter
            },
            'auftraege': auftraege,
            'summary': {
                'anzahl_rechnungen': len(auftraege),
                'anzahl_probleme': probleme,
                'anzahl_unvollstaendig': unvollstaendig,  # TAG 120: Nicht vollständig abgerechnete Aufträge
                'total_rechnung_eur': round(total_rechnung, 2),
                'total_vorgabe_aw': round(total_vorgabe_aw, 1),
                'total_gestempelt_aw': round(total_gestempelt_aw, 1),
                'total_diff_aw': round(total_gestempelt_aw - total_vorgabe_aw, 1),
                'total_verlust_eur': round(total_verlust, 2),
                'gesamt_leistungsgrad': round(gesamt_leistungsgrad, 1)
            }
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
    TAG 181: GUDAT-Rückfragen hinzugefügt
    """
    try:
        from api.werkstatt_data import WerkstattData
        from api.arbeitskarte_api import hole_arbeitskarte_daten

        data = WerkstattData.get_auftrag_detail(auftrag_nr)

        if not data.get('success', True):
            logger.warning(f"Auftrag {auftrag_nr} nicht gefunden: {data.get('error', 'Unbekannter Fehler')}")
            return jsonify({
                'success': False,
                'error': data.get('error', f'Auftrag {auftrag_nr} nicht gefunden')
            }), 404

        # Hole GUDAT-Daten (inkl. Rückfragen)
        try:
            gudat_daten = hole_arbeitskarte_daten(auftrag_nr)
            if gudat_daten and gudat_daten.get('gudat'):
                gudat = gudat_daten.get('gudat')
                rueckfragen = gudat.get('rueckfragen', [])
                logger.info(f"GUDAT-Daten für Auftrag {auftrag_nr}: {len(rueckfragen)} Rückfragen gefunden")
                data['gudat'] = gudat
            else:
                logger.debug(f"Keine GUDAT-Daten für Auftrag {auftrag_nr}")
        except Exception as e:
            logger.warning(f"Fehler beim Holen von GUDAT-Daten für Auftrag {auftrag_nr}: {e}")
            import traceback
            traceback.print_exc()
            # Nicht kritisch - Auftrag-Daten trotzdem zurückgeben

        return jsonify({
            'success': True,
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

    Ruft /api/gudat/workload auf und transformiert die Daten
    ins Format das das Frontend erwartet.

    TAG122: Echte Werkstatt-Kapazität = nur interne Mechanik-Teams:
    - Allgemeine Reparatur (ID 2)
    - Diagnosetechnik (ID 3)
    - NW/GW (ID 5)
    """
    import requests

    # Interne Mechanik-Teams (echte Werkstatt-Kapazität)
    INTERNE_TEAMS = {2, 3, 5}  # Allgemeine Reparatur, Diagnosetechnik, NW/GW

    try:
        # Lokalen Gudat-API Endpunkt aufrufen
        response = requests.get(
            'http://localhost:5000/api/gudat/workload',
            timeout=10
        )

        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Gudat API Fehler: {response.status_code}'
            }), response.status_code

        data = response.json()

        if 'error' in data:
            return jsonify({
                'success': False,
                'error': data['error']
            }), 400

        # Wochen-Daten holen
        week_response = requests.get(
            'http://localhost:5000/api/gudat/workload/week',
            timeout=10
        )
        week_data = week_response.json() if week_response.status_code == 200 else {}

        # TAG122: Nur interne Teams für Kapazität zählen
        teams = data.get('teams', [])
        interne_teams = [t for t in teams if t.get('id') in INTERNE_TEAMS]

        # Kapazität nur aus internen Teams berechnen
        intern_kapazitaet = sum(t.get('capacity', 0) for t in interne_teams)
        intern_geplant = sum(t.get('planned', 0) for t in interne_teams)
        intern_frei = sum(t.get('free', 0) for t in interne_teams)
        intern_auslastung = round((intern_geplant / intern_kapazitaet * 100), 1) if intern_kapazitaet > 0 else 0

        # Status basierend auf Auslastung
        if intern_auslastung >= 90:
            status = 'critical'
        elif intern_auslastung >= 70:
            status = 'warning'
        else:
            status = 'ok'

        # Transformiere ins Frontend-Format
        result = {
            'success': True,
            'kapazitaet': intern_kapazitaet,  # TAG122: Nur interne Teams
            'geplant': intern_geplant,
            'frei': intern_frei,
            'auslastung': intern_auslastung,
            'status': status,
            'teams': teams,  # Alle Teams für Detail-Ansicht
            'interne_teams': interne_teams,  # TAG122: Nur Mechanik
            'woche': week_data.get('days', []),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            # TAG122: Zusätzliche Info
            'hinweis': 'Kapazität = nur Allgemeine Reparatur + Diagnosetechnik + NW/GW'
        }

        return jsonify(result)

    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Gudat API Timeout'
        }), 504
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': 'Gudat API nicht erreichbar'
        }), 503
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
        # FIX TAG 200: Context Manager korrekt verwenden
        portal_context = db_session()
        conn_portal = portal_context.__enter__()
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
        
        # TAG 200: Problematische AVG-Aufträge VOR dem Schließen der Connections holen
        avg_problematisch = get_avg_problematische_auftraege_safe(cur_loco, subsidiary)
        
        # TAG 200: Alle offenen Aufträge VOR dem Schließen der Connections holen
        offene_auftraege = get_alle_offene_auftraege_safe(cur_loco, subsidiary)

        # FIX TAG 200: Connections korrekt schließen
        try:
            cur_loco.close()
            conn_loco.close()
        except:
            pass
        
        try:
            cur_portal.close()
            portal_context.__exit__(None, None, None)  # Context Manager korrekt beenden
        except:
            pass
        
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
            },
            
            # TAG 200: Problematische AVG-Aufträge (abgerechnet oder Termin vorbei)
            'avg_problematisch': avg_problematisch,
            
            # TAG 200: Alle offenen Aufträge (zur Validierung gegen CSV)
            'offene_auftraege': offene_auftraege
        })
        
    except Exception as e:
        logger.exception("Fehler bei Kapazitäts-Forecast")
        # FIX TAG 200: Connections auch bei Fehler schließen
        try:
            if 'cur_loco' in locals():
                cur_loco.close()
            if 'conn_loco' in locals():
                conn_loco.close()
            if 'cur_portal' in locals():
                cur_portal.close()
            if 'conn_portal' in locals() and 'portal_context' in locals():
                portal_context.__exit__(None, None, None)
        except:
            pass
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def get_avg_problematische_auftraege_safe(cur_loco, subsidiary=None):
    """
    TAG 200: Wrapper für get_avg_problematische_auftraege mit Fehlerbehandlung
    """
    try:
        return get_avg_problematische_auftraege(cur_loco, subsidiary)
    except Exception as e:
        logger.warning(f"Fehler bei get_avg_problematische_auftraege: {e}")
        return {
            'abgerechnet': {'anzahl': 0, 'auftraege': []},
            'termin_vorbei': {'anzahl': 0, 'auftraege': []},
            'gesamt_problematisch': 0
        }


def get_avg_problematische_auftraege(cur_loco, subsidiary=None):
    """
    TAG 200: Findet problematische AVG-Aufträge
    - Abgerechnet, aber haben noch AVG-Grund
    - Termin vorbei, aber nicht abgerechnet
    """
    from datetime import date
    heute = date.today()
    
    # Import BETRIEB_NAMEN (bereits oben importiert)
    
    # Abgerechnete Aufträge mit AVG-Grund
    # TAG 200: has_open_positions kann true sein auch wenn abgerechnet (wenn noch offene Positionen existieren)
    # Wir prüfen explizit ob eine Rechnung existiert
    abgerechnet_query = """
        SELECT DISTINCT
            o.number as auftrag_nr,
            o.subsidiary as betrieb,
            o.clearing_delay_type as avg_code,
            cdt.description as avg_text,
            i.invoice_number,
            i.invoice_date,
            COALESCE(SUM(l.time_units), 0) as vorgabe_aw
        FROM orders o
        LEFT JOIN clearing_delay_types cdt ON o.clearing_delay_type = cdt.type
        JOIN invoices i ON o.number = i.order_number
        LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
        WHERE o.clearing_delay_type IS NOT NULL
          AND o.clearing_delay_type != ''
          AND i.is_canceled = false
          AND o.has_open_positions = true  -- Nur offene Aufträge (können trotzdem teilweise abgerechnet sein)
    """
    
    if subsidiary:
        abgerechnet_query += " AND o.subsidiary = %s"
        cur_loco.execute(abgerechnet_query + " GROUP BY o.number, o.subsidiary, o.clearing_delay_type, cdt.description, i.invoice_number, i.invoice_date", [subsidiary])
    else:
        abgerechnet_query += " GROUP BY o.number, o.subsidiary, o.clearing_delay_type, cdt.description, i.invoice_number, i.invoice_date"
        cur_loco.execute(abgerechnet_query)
    
    abgerechnet = cur_loco.fetchall()
    
    # Termin vorbei, nicht abgerechnet
    termin_vorbei_query = """
        SELECT DISTINCT
            o.number as auftrag_nr,
            o.subsidiary as betrieb,
            o.clearing_delay_type as avg_code,
            cdt.description as avg_text,
            o.estimated_inbound_time as bringen_termin,
            COALESCE(SUM(l.time_units), 0) as vorgabe_aw
        FROM orders o
        LEFT JOIN clearing_delay_types cdt ON o.clearing_delay_type = cdt.type
        LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
        WHERE o.has_open_positions = true
          AND o.clearing_delay_type IS NOT NULL
          AND o.clearing_delay_type != ''
          AND DATE(o.estimated_inbound_time) < CURRENT_DATE
          AND NOT EXISTS (
              SELECT 1 FROM invoices i 
              WHERE i.order_number = o.number 
              AND i.is_canceled = false
          )
    """
    
    if subsidiary:
        termin_vorbei_query += " AND o.subsidiary = %s"
        cur_loco.execute(termin_vorbei_query + " GROUP BY o.number, o.subsidiary, o.clearing_delay_type, cdt.description, o.estimated_inbound_time", [subsidiary])
    else:
        termin_vorbei_query += " GROUP BY o.number, o.subsidiary, o.clearing_delay_type, cdt.description, o.estimated_inbound_time"
        cur_loco.execute(termin_vorbei_query)
    
    termin_vorbei = cur_loco.fetchall()
    
    # Formatieren
    abgerechnet_liste = [{
        'auftrag_nr': a['auftrag_nr'],
        'betrieb': a['betrieb'],
        'betrieb_name': BETRIEB_NAMEN.get(a['betrieb'], '?'),
        'avg_code': a['avg_code'],
        'avg_text': a['avg_text'] or 'Unbekannt',
        'invoice_number': a['invoice_number'],
        'invoice_date': a['invoice_date'].strftime('%d.%m.%Y') if a['invoice_date'] else None,
        'vorgabe_aw': float(a['vorgabe_aw'] or 0),
        'problem': 'abgerechnet'
    } for a in abgerechnet]
    
    termin_vorbei_liste = [{
        'auftrag_nr': a['auftrag_nr'],
        'betrieb': a['betrieb'],
        'betrieb_name': BETRIEB_NAMEN.get(a['betrieb'], '?'),
        'avg_code': a['avg_code'],
        'avg_text': a['avg_text'] or 'Unbekannt',
        'bringen_termin': a['bringen_termin'].strftime('%d.%m.%Y') if a['bringen_termin'] else None,
        'tage_vorbei': (heute - a['bringen_termin'].date()).days if a['bringen_termin'] else 0,
        'vorgabe_aw': float(a['vorgabe_aw'] or 0),
        'problem': 'termin_vorbei'
    } for a in termin_vorbei]
    
    # TAG 200: Abgerechnete Aufträge werden nicht mehr angezeigt
    # (AVG-Grund bleibt nach Abrechnung erhalten, wird nicht mehr bearbeitet)
    # Nur Aufträge mit Termin vorbei sind relevant
    return {
        'abgerechnet': {
            'anzahl': len(abgerechnet_liste),
            'auftraege': []  # Nicht mehr anzeigen
        },
        'termin_vorbei': {
            'anzahl': len(termin_vorbei_liste),
            'auftraege': termin_vorbei_liste[:50]  # Max 50
        },
        'gesamt_problematisch': len(termin_vorbei_liste)  # Nur Termin vorbei zählt
    }


def get_alle_offene_auftraege_safe(cur_loco, subsidiary=None, serviceberater_nr=None, min_alter_tage=None):
    """
    TAG 200: Wrapper für get_alle_offene_auftraege mit Fehlerbehandlung
    """
    try:
        return get_alle_offene_auftraege(cur_loco, subsidiary, serviceberater_nr, min_alter_tage)
    except Exception as e:
        logger.warning(f"Fehler bei get_alle_offene_auftraege: {e}")
        return {
            'anzahl': 0,
            'summe_aw': 0,
            'summe_gesamt': 0,
            'auftraege': []
        }


def get_alle_offene_auftraege(cur_loco, subsidiary=None, serviceberater_nr=None, min_alter_tage=None):
    """
    TAG 200: Holt alle offenen Aufträge aus Locosoft
    Struktur entspricht der CSV-Datei zur Validierung
    
    Args:
        cur_loco: Locosoft Cursor
        subsidiary: Betrieb (optional)
        serviceberater_nr: Serviceberater-Nummer (optional)
        min_alter_tage: Mindestalter in Tagen (optional)
    """
    from datetime import date, timedelta
    heute = date.today()
    
    query = """
        SELECT
            o.number as auftrag_nr,
            o.subsidiary as betrieb,
            o.order_date as auftrag_datum,
            o.clearing_delay_type as avg_code,
            cdt.description as avg_text,
            o.order_taking_employee_no as serviceberater_nr,
            sb.name as serviceberater_name,
            cs.customer_number as kunden_nr,
            COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name) as kunde,
            v.license_plate as kennzeichen,
            m.description as marke,
            v.first_registration_date as erstzulassung,
            v.internal_number as fahrzeug_nr,
            v.mileage_km as km_stand,
            o.urgency as dringlichkeit,
            COALESCE(SUM(l.time_units), 0) as vorgabe_aw,
            COUNT(DISTINCT CASE WHEN NOT l.is_invoiced THEN l.order_position END) as anzahl_unfakt_arbeitspositionen,
            COUNT(DISTINCT CASE WHEN NOT l.is_invoiced AND l.labour_type IN ('P', 'PT') THEN l.order_position END) as anzahl_unfakt_fz_positionen,
            COUNT(DISTINCT CASE WHEN NOT l.is_invoiced AND l.labour_type = 'ET' THEN l.order_position END) as anzahl_unfakt_et_positionen,
            COALESCE(SUM(CASE WHEN NOT l.is_invoiced THEN l.net_price_in_order ELSE 0 END), 0) as summe_lohn,
            COALESCE(SUM(CASE WHEN NOT l.is_invoiced AND l.labour_type = 'ET' THEN l.net_price_in_order ELSE 0 END), 0) as summe_et,
            COALESCE(SUM(CASE WHEN NOT l.is_invoiced THEN l.net_price_in_order ELSE 0 END), 0) as gesamtsumme,
            o.estimated_inbound_time as termin_bringen,
            o.estimated_outbound_time as termin_abholen
        FROM orders o
        LEFT JOIN clearing_delay_types cdt ON o.clearing_delay_type = cdt.type
        LEFT JOIN employees_history sb ON o.order_taking_employee_no = sb.employee_number
            AND sb.is_latest_record = true
        LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
        LEFT JOIN makes m ON v.make_number = m.make_number
        LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
        LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
        WHERE o.has_open_positions = true
          AND o.order_date >= CURRENT_DATE - INTERVAL '90 days'  -- Letzte 90 Tage
    """
    
    params = []
    
    if subsidiary:
        query += " AND o.subsidiary = %s"
        params.append(subsidiary)
    
    if serviceberater_nr:
        query += " AND o.order_taking_employee_no = %s"
        params.append(serviceberater_nr)
    
    if min_alter_tage and min_alter_tage > 0:
        min_datum = heute - timedelta(days=min_alter_tage)
        query += " AND o.order_date <= %s"
        params.append(min_datum)
        query += """
            GROUP BY o.number, o.subsidiary, o.order_date, o.clearing_delay_type, cdt.description,
                     o.order_taking_employee_no, sb.name, cs.customer_number, cs.family_name, cs.first_name,
                     v.license_plate, m.description, v.first_registration_date, v.internal_number, 
                     v.mileage_km, o.urgency, o.estimated_inbound_time, o.estimated_outbound_time
            ORDER BY o.order_date DESC, o.number DESC
            LIMIT 200
        """
        cur_loco.execute(query, params)
    else:
        query += """
            GROUP BY o.number, o.subsidiary, o.order_date, o.clearing_delay_type, cdt.description,
                     o.order_taking_employee_no, sb.name, cs.customer_number, cs.family_name, cs.first_name,
                     v.license_plate, m.description, v.first_registration_date, v.internal_number, 
                     v.mileage_km, o.urgency, o.estimated_inbound_time, o.estimated_outbound_time
            ORDER BY o.order_date DESC, o.number DESC
            LIMIT 200
        """
        cur_loco.execute(query, params)
    
    auftraege_raw = cur_loco.fetchall()
    
    auftraege_liste = []
    for a in auftraege_raw:
        auftrag_datum_raw = a['auftrag_datum']
        # Konvertiere datetime zu date falls nötig
        if auftrag_datum_raw:
            if hasattr(auftrag_datum_raw, 'date'):
                auftrag_datum_date = auftrag_datum_raw.date()
            else:
                auftrag_datum_date = auftrag_datum_raw
            tage_alt = (heute - auftrag_datum_date).days
        else:
            auftrag_datum_date = None
            tage_alt = 0
        
        auftraege_liste.append({
            'auftrag_nr': a['auftrag_nr'],
            'betrieb': a['betrieb'],
            'betrieb_name': BETRIEB_NAMEN.get(a['betrieb'], '?'),
            'auftrag_datum': auftrag_datum_raw.strftime('%d.%m.%Y') if auftrag_datum_raw else None,
            'tage_alt': tage_alt,
            'avg_code': a['avg_code'],
            'avg_text': a['avg_text'] or None,
            'serviceberater_nr': a['serviceberater_nr'],
            'serviceberater_name': a['serviceberater_name'],
            'kunden_nr': a['kunden_nr'],
            'kunde': a['kunde'] or 'Unbekannt',
            'kennzeichen': a['kennzeichen'],
            'marke': a['marke'],
            'erstzulassung': a['erstzulassung'].strftime('%d.%m.%Y') if a['erstzulassung'] else None,
            'fahrzeug_nr': a['fahrzeug_nr'],
            'km_stand': int(a['km_stand'] or 0),
            'dringlichkeit': a['dringlichkeit'],
            'vorgabe_aw': round(float(a['vorgabe_aw'] or 0), 1),
            'anzahl_unfakt_arbeitspositionen': int(a['anzahl_unfakt_arbeitspositionen'] or 0),
            'anzahl_unfakt_fz_positionen': int(a['anzahl_unfakt_fz_positionen'] or 0),
            'anzahl_unfakt_et_positionen': int(a['anzahl_unfakt_et_positionen'] or 0),
            'summe_lohn': round(float(a['summe_lohn'] or 0), 2),
            'summe_et': round(float(a['summe_et'] or 0), 2),
            'gesamtsumme': round(float(a['gesamtsumme'] or 0), 2),
            'termin_bringen': a['termin_bringen'].strftime('%d.%m.%Y %H:%M') if a['termin_bringen'] else None,
            'termin_abholen': a['termin_abholen'].strftime('%d.%m.%Y %H:%M') if a['termin_abholen'] else None
        })
    
    return {
        'anzahl': len(auftraege_liste),
        'summe_aw': round(sum(a['vorgabe_aw'] for a in auftraege_liste), 1),
        'summe_gesamt': round(sum(a['gesamtsumme'] for a in auftraege_liste), 2),
        'auftraege': auftraege_liste
    }


# ============================================================================
# HEUTE LIVE - Echte Zahlen von heute (Stempelungen + Verrechnet)
# ============================================================================

@werkstatt_live_bp.route('/heute', methods=['GET'])
def get_heute_live():
    """
    GET /api/werkstatt/live/heute
    
    Zeigt ECHTE Zahlen von HEUTE:
    - Gestempelte Stunden/AW
    - Verrechnete AW und Umsatz
    - Aktive Mechaniker
    - Produktivität
    
    Das ist der Unterschied zum FORECAST:
    - FORECAST = Was ist geplant (Termine)
    - HEUTE LIVE = Was passiert wirklich (Stempelungen)
    
    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1=Deggendorf, 3=Landau)
    """
    try:
        subsidiary = request.args.get('subsidiary', type=int)
        heute = datetime.now().date()
        
        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # ===== 1. ANWESENHEIT HEUTE (order_number = 0) =====
        # order_number = 0 ist die Anwesenheits-Stempelung (Kommen/Gehen)
        # Das ist die ECHTE Arbeitszeit der Mechaniker!
        anwesenheit_query = """
            SELECT 
                COUNT(DISTINCT employee_number) as mechaniker,
                COALESCE(ROUND(SUM(duration_minutes)::numeric / 60, 1), 0) as stunden
            FROM times 
            WHERE DATE(start_time) = CURRENT_DATE
            AND DATE(end_time) = CURRENT_DATE
            AND employee_number BETWEEN 5000 AND 5999
            AND order_number = 0
        """
        if subsidiary:
            # TODO: Anwesenheit hat keinen subsidiary - erstmal ohne Filter
            pass
        cur.execute(anwesenheit_query)
        anwesenheit = cur.fetchone()
        
        # ===== 2. PRODUKTIVE ARBEIT HEUTE (order_number > 0) =====
        # Auftragsarbeit - dedupliziert nach Mechaniker/Auftrag/Startzeit
        stempel_query = """
            SELECT 
                COUNT(DISTINCT sub.order_number) as auftraege,
                COUNT(DISTINCT sub.employee_number) as mechaniker,
                COALESCE(ROUND(SUM(sub.stunden)::numeric, 1), 0) as stunden,
                COALESCE(ROUND(SUM(sub.stunden)::numeric * 6, 1), 0) as aw
            FROM (
                SELECT employee_number, order_number, start_time, 
                       MAX(duration_minutes)/60.0 as stunden
                FROM times 
                WHERE DATE(start_time) = CURRENT_DATE
                AND DATE(end_time) = CURRENT_DATE
                AND employee_number BETWEEN 5000 AND 5999
                AND order_number > 0
                GROUP BY employee_number, order_number, start_time
            ) sub
        """
        if subsidiary:
            stempel_query = """
                SELECT 
                    COUNT(DISTINCT sub.order_number) as auftraege,
                    COUNT(DISTINCT sub.employee_number) as mechaniker,
                    COALESCE(ROUND(SUM(sub.stunden)::numeric, 1), 0) as stunden,
                    COALESCE(ROUND(SUM(sub.stunden)::numeric * 6, 1), 0) as aw
                FROM (
                    SELECT t.employee_number, t.order_number, t.start_time, 
                           MAX(t.duration_minutes)/60.0 as stunden
                    FROM times t
                    JOIN orders o ON t.order_number = o.number
                    WHERE DATE(t.start_time) = CURRENT_DATE
                    AND DATE(t.end_time) = CURRENT_DATE
                    AND t.employee_number BETWEEN 5000 AND 5999
                    AND t.order_number > 0
                    AND o.subsidiary = %s
                    GROUP BY t.employee_number, t.order_number, t.start_time
                ) sub
            """
            cur.execute(stempel_query, (subsidiary,))
        else:
            cur.execute(stempel_query)
        
        gestempelt = cur.fetchone()
        
        # ===== 2. AKTIV GESTEMPELT (gerade am arbeiten) =====
        aktiv_query = """
            SELECT 
                t.employee_number,
                e.name as mechaniker_name,
                t.order_number,
                t.start_time,
                v.license_plate as kennzeichen
            FROM times t
            JOIN employees_history e ON t.employee_number = e.employee_number AND e.is_latest_record = true
            LEFT JOIN orders o ON t.order_number = o.number
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            WHERE DATE(t.start_time) = CURRENT_DATE
            AND t.end_time IS NULL
            ORDER BY t.start_time DESC
        """
        cur.execute(aktiv_query)
        aktiv_raw = cur.fetchall()
        
        # Duplikate entfernen (nach employee_number gruppieren)
        aktiv_dict = {}
        for row in aktiv_raw:
            emp_no = row['employee_number']
            if emp_no not in aktiv_dict:
                aktiv_dict[emp_no] = {
                    'employee_number': emp_no,
                    'name': row['mechaniker_name'],
                    'order_number': row['order_number'],
                    'kennzeichen': row['kennzeichen'],
                    'seit': row['start_time'].strftime('%H:%M') if row['start_time'] else None
                }
        aktiv_gestempelt = list(aktiv_dict.values())
        
        # ===== 3. VERRECHNET HEUTE (Werkstatt, ohne Fahrzeugverkauf) =====
        # invoice_type 8 = Fahrzeugverkauf (ausschließen!)
        verrechnet_query = """
            SELECT 
                COUNT(*) as rechnungen,
                COALESCE(ROUND(SUM(job_amount_net)::numeric, 2), 0) as lohn_netto,
                COALESCE(ROUND(SUM(part_amount_net)::numeric, 2), 0) as teile_netto,
                COALESCE(ROUND(SUM(total_net)::numeric, 2), 0) as gesamt_netto
            FROM invoices
            WHERE DATE(invoice_date) = CURRENT_DATE
            AND is_canceled = false
            AND invoice_type NOT IN (8)
        """
        if subsidiary:
            verrechnet_query = """
                SELECT 
                    COUNT(*) as rechnungen,
                    COALESCE(ROUND(SUM(job_amount_net)::numeric, 2), 0) as lohn_netto,
                    COALESCE(ROUND(SUM(part_amount_net)::numeric, 2), 0) as teile_netto,
                    COALESCE(ROUND(SUM(total_net)::numeric, 2), 0) as gesamt_netto
                FROM invoices
                WHERE DATE(invoice_date) = CURRENT_DATE
                AND is_canceled = false
                AND invoice_type NOT IN (8)
                AND subsidiary = %s
            """
            cur.execute(verrechnet_query, (subsidiary,))
        else:
            cur.execute(verrechnet_query)
        
        verrechnet = cur.fetchone()
        
        # ===== 4. VERRECHNET AW HEUTE =====
        aw_query = """
            SELECT 
                COUNT(DISTINCT l.order_number) as auftraege,
                COALESCE(ROUND(SUM(l.time_units)::numeric, 1), 0) as aw_verrechnet
            FROM invoices i
            JOIN labours l ON i.order_number = l.order_number
            WHERE DATE(i.invoice_date) = CURRENT_DATE
            AND i.is_canceled = false
            AND i.invoice_type NOT IN (8)
            AND l.is_invoiced = true
        """
        if subsidiary:
            aw_query = """
                SELECT 
                    COUNT(DISTINCT l.order_number) as auftraege,
                    COALESCE(ROUND(SUM(l.time_units)::numeric, 1), 0) as aw_verrechnet
                FROM invoices i
                JOIN labours l ON i.order_number = l.order_number
                WHERE DATE(i.invoice_date) = CURRENT_DATE
                AND i.is_canceled = false
                AND i.invoice_type NOT IN (8)
                AND l.is_invoiced = true
                AND i.subsidiary = %s
            """
            cur.execute(aw_query, (subsidiary,))
        else:
            cur.execute(aw_query)
        
        aw_verrechnet = cur.fetchone()
        
        # ===== 5. KAPAZITÄT HEUTE (für Auslastungs-Berechnung) =====
        # Mechaniker = employee_number 5000-5999
        kapazitaet_query = """
            WITH aktuelle_arbeitszeiten AS (
                SELECT DISTINCT ON (employee_number, dayofweek)
                    employee_number, dayofweek, work_duration
                FROM employees_worktimes
                ORDER BY employee_number, dayofweek, validity_date DESC
            )
            SELECT 
                COUNT(DISTINCT eh.employee_number) as mechaniker_gesamt,
                COALESCE(SUM(COALESCE(aw.work_duration, 8)), 0) as stunden_kapazitaet
            FROM employees_history eh
            LEFT JOIN aktuelle_arbeitszeiten aw 
                ON eh.employee_number = aw.employee_number 
                AND aw.dayofweek = EXTRACT(DOW FROM CURRENT_DATE)
            LEFT JOIN absence_calendar ab 
                ON eh.employee_number = ab.employee_number 
                AND ab.date = CURRENT_DATE
            WHERE eh.is_latest_record = true
            AND eh.employee_number BETWEEN 5000 AND 5999
            AND eh.leave_date IS NULL
            AND ab.employee_number IS NULL
        """
        if subsidiary:
            kapazitaet_query = kapazitaet_query.replace(
                "AND ab.employee_number IS NULL",
                f"AND ab.employee_number IS NULL AND eh.subsidiary = {subsidiary}"
            )
        
        cur.execute(kapazitaet_query)
        kapazitaet = cur.fetchone()
        
        kapazitaet_aw = float(kapazitaet['stunden_kapazitaet'] or 0) * 6  # Stunden → AW
        mechaniker_anwesend = int(kapazitaet['mechaniker_gesamt'] or 0)
        
        # ===== BERECHNUNGEN =====
        # Anwesenheit = echte Arbeitszeit
        anwesend_stunden = float(anwesenheit['stunden'] or 0)
        anwesend_mechaniker = int(anwesenheit['mechaniker'] or 0)
        
        # Produktive Arbeit
        produktiv_aw = float(gestempelt['aw'] or 0)
        produktiv_stunden = float(gestempelt['stunden'] or 0)
        produktiv_auftraege = int(gestempelt['auftraege'] or 0)
        
        # Verrechnet
        verrechnet_aw_val = float(aw_verrechnet['aw_verrechnet'] or 0)
        
        # Kapazität basiert auf anwesenden Mechanikern
        # Wenn noch keiner ausgestempelt: nehme die Kapazitäts-Query
        if anwesend_mechaniker > 0:
            kapazitaet_stunden = anwesend_mechaniker * 8.0  # Soll-Stunden
            kapazitaet_aw = kapazitaet_stunden * 6
        else:
            kapazitaet_stunden = float(kapazitaet['stunden_kapazitaet'] or 0)
            kapazitaet_aw = kapazitaet_stunden * 6
        
        # Produktivität = Anwesenheit / Soll-Kapazität
        # (Nicht die gestempelten AW, sondern die echte Anwesenheitszeit)
        produktivitaet = round((anwesend_stunden / kapazitaet_stunden * 100) if kapazitaet_stunden > 0 else 0, 1)
        
        # Status basierend auf Produktivität (110% = Ziel!)
        if produktivitaet >= 110:
            status = 'optimal'
            status_text = 'Ziel erreicht! 🎯'
            status_icon = '🟢'
        elif produktivitaet >= 90:
            status = 'gut'
            status_text = 'Gut unterwegs'
            status_icon = '🟢'
        elif produktivitaet >= 50:
            status = 'normal'
            status_text = 'Normal'
            status_icon = '🔵'
        else:
            status = 'niedrig'
            status_text = 'Unterausgelastet'
            status_icon = '🔵'
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'datum': str(heute),
            'datum_formatiert': heute.strftime('%d.%m.%Y'),
            'filter': {
                'subsidiary': subsidiary
            },
            
            # ANWESENHEIT (echte Arbeitszeit)
            'anwesenheit': {
                'mechaniker': anwesend_mechaniker,
                'stunden': anwesend_stunden,
                'aw': round(anwesend_stunden * 6, 1)
            },
            
            # PRODUKTIVE ARBEIT (Aufträge)
            'produktiv': {
                'auftraege': produktiv_auftraege,
                'stunden': produktiv_stunden,
                'aw': produktiv_aw
            },
            
            # AKTUELL AKTIV (gerade am arbeiten)
            'aktiv': {
                'anzahl': len(aktiv_gestempelt),
                'mechaniker': aktiv_gestempelt[:20]  # Max 20
            },
            
            # VERRECHNET (Umsatz)
            'verrechnet': {
                'rechnungen': int(verrechnet['rechnungen'] or 0),
                'auftraege': int(aw_verrechnet['auftraege'] or 0),
                'aw': float(verrechnet_aw_val),
                'lohn_netto': float(verrechnet['lohn_netto'] or 0),
                'teile_netto': float(verrechnet['teile_netto'] or 0),
                'gesamt_netto': float(verrechnet['gesamt_netto'] or 0)
            },
            
            # KAPAZITÄT
            'kapazitaet': {
                'mechaniker': anwesend_mechaniker if anwesend_mechaniker > 0 else mechaniker_anwesend,
                'stunden_soll': kapazitaet_stunden,
                'aw': kapazitaet_aw
            },
            
            # PRODUKTIVITÄT (Anwesenheit vs Soll)
            'produktivitaet': {
                'prozent': produktivitaet,
                'status': status,
                'status_text': status_text,
                'status_icon': status_icon,
                'ziel': 110  # 110% ist das Ziel!
            }
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

                    # Prüfe welche Features das Modell erwartet
                    model_features = list(model.feature_names_in_) if hasattr(model, 'feature_names_in_') else []
                    logger.debug(f"DRIVE: Modell erwartet {len(model_features)} Features: {model_features}")
                    
                    # Vorhersage für jeden Auftrag
                    for auftrag in auftraege_raw:
                        if auftrag['vorgabe_aw'] and auftrag['vorgabe_aw'] > 0:
                            try:
                                vorgabe_aw = float(auftrag['vorgabe_aw'])
                                betrieb = auftrag['betrieb'] or 1
                                marke = auftrag['marke'] or 'Opel'
                                km_stand = float(auftrag['km_stand'] or 50000)
                                fahrzeug_alter = float(auftrag['fahrzeug_alter'] or 3)
                                mech_nr = auftrag.get('mechaniker_nr') or auftrag.get('aktiv_mechaniker_nr')

                                # Datum-Features
                                auftrag_datum = auftrag['auftrag_datum']
                                if auftrag_datum:
                                    wochentag = auftrag_datum.weekday()
                                    monat = auftrag_datum.month
                                    start_stunde = auftrag_datum.hour if auftrag_datum.hour > 0 else 8
                                else:
                                    wochentag, monat, start_stunde = 1, 6, 8

                                # Kategorische Features encodieren
                                try:
                                    marke_encoded = encoders['marke'].transform([marke])[0]
                                except:
                                    marke_encoded = 0

                                # Mechaniker encodieren (falls Encoder vorhanden)
                                try:
                                    if 'mechaniker' in encoders and mech_nr:
                                        mechaniker_encoded = encoders['mechaniker'].transform([mech_nr])[0]
                                    else:
                                        mechaniker_encoded = 0
                                except:
                                    mechaniker_encoded = 0

                                # Feature-Vektor basierend auf Modell-Anforderungen
                                # Modell erwartet: vorgabe_aw, mechaniker_encoded, betrieb, wochentag, monat, start_stunde, marke_encoded, fahrzeug_alter_jahre, km_stand
                                if model_features and len(model_features) == 9:
                                    # V2 Modell (9 Features)
                                    features = pd.DataFrame([[
                                        vorgabe_aw,            # 1. vorgabe_aw
                                        mechaniker_encoded,    # 2. mechaniker_encoded
                                        betrieb,               # 3. betrieb
                                        wochentag,             # 4. wochentag
                                        monat,                 # 5. monat
                                        start_stunde,          # 6. start_stunde
                                        marke_encoded,         # 7. marke_encoded
                                        fahrzeug_alter,        # 8. fahrzeug_alter_jahre
                                        km_stand               # 9. km_stand
                                    ]], columns=model_features)
                                else:
                                    # Fallback: V5 Modell (21 Features) - falls Modell doch mehr Features erwartet
                                    soll_dauer_min = vorgabe_aw * 6
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
                                    
                                    kalenderwoche = auftrag_datum.isocalendar()[1] if auftrag_datum else 25
                                    anzahl_positionen = int(auftrag.get('anzahl_positionen', 1) or 1)
                                    anzahl_teile = int(auftrag.get('anzahl_teile', 0) or 0)
                                    charge_type = int(auftrag.get('charge_type', 10) or 10)
                                    urgency = int(auftrag.get('urgency', 0) or 0)
                                    power_kw = float(auftrag.get('power_kw', 74) or 74)
                                    cubic_capacity = float(auftrag.get('cubic_capacity', 1200) or 1200)
                                    
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
                                        1.0,                   # 16. productivity_factor
                                        10.0,                  # 17. years_experience
                                        0,                     # 18. meister
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
    Anwesenheits-Report V2 (TAG 130): Wer hat heute gearbeitet?

    Basiert auf Type 2 (produktive Stempelungen) + Type 1 für Historie.
    Type 1 nur für vergangene Tage zuverlässig (wird erst bei Ausstempeln geschrieben).

    Parameter:
    - datum: YYYY-MM-DD (default: heute)
    - subsidiary: 1=DEG, 2=Hyundai, 3=Landau (optional)
    """
    try:
        datum = request.args.get('datum', datetime.now().strftime('%Y-%m-%d'))
        subsidiary = request.args.get('subsidiary')
        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Alle Mechaniker mit Type 2 (produktiv) + Type 1 (Anwesenheit) am gewählten Tag
        cur.execute('''
            WITH stempelungen AS (
                SELECT
                    t.employee_number,
                    MIN(t.start_time) as erster_start,
                    MAX(COALESCE(t.end_time, NOW())) as letztes_ende,
                    COUNT(DISTINCT t.order_number) FILTER (WHERE t.order_number != ALL(ARRAY[39406,220710,313666])) as anzahl_auftraege,
                    SUM(EXTRACT(EPOCH FROM (COALESCE(t.end_time, NOW()) - t.start_time))/60)
                        FILTER (WHERE t.order_number != ALL(ARRAY[39406,220710,313666])) as produktiv_min,
                    SUM(EXTRACT(EPOCH FROM (COALESCE(t.end_time, NOW()) - t.start_time))/60)
                        FILTER (WHERE t.order_number = ANY(ARRAY[39406,220710,313666])) as leerlauf_min,
                    MAX(CASE WHEN t.end_time IS NULL THEN t.order_number END) as aktiver_auftrag,
                    MAX(CASE WHEN t.end_time IS NULL THEN t.start_time END) as aktiv_seit
                FROM times t
                WHERE DATE(t.start_time) = %s
                  AND t.type = 2
                  AND t.employee_number BETWEEN 5000 AND 5999
                GROUP BY t.employee_number
            ),
            anwesenheit AS (
                SELECT
                    t.employee_number,
                    MIN(t.start_time) as anwesend_ab,
                    MAX(t.end_time) as anwesend_bis,
                    ROUND(SUM(EXTRACT(EPOCH FROM (t.end_time - t.start_time))/60)::numeric) as anwesend_min
                FROM times t
                WHERE DATE(t.start_time) = %s
                  AND t.type = 1
                  AND t.employee_number BETWEEN 5000 AND 5999
                GROUP BY t.employee_number
            ),
            alle_mechaniker AS (
                SELECT DISTINCT
                    eh.employee_number,
                    eh.name,
                    eh.subsidiary,
                    CASE eh.subsidiary
                        WHEN 1 THEN 'Deggendorf'
                        WHEN 2 THEN 'Hyundai'
                        WHEN 3 THEN 'Landau'
                    END as betrieb
                FROM employees_history eh
                WHERE eh.is_latest_record = true
                  AND eh.employee_number BETWEEN 5000 AND 5999
                  AND (eh.leave_date IS NULL OR eh.leave_date > %s::date)
                  AND eh.subsidiary IN (1, 2, 3)
            ),
            abwesenheiten AS (
                SELECT
                    ac.employee_number,
                    ac.reason,
                    ac.type as abwesenheit_typ
                FROM absence_calendar ac
                WHERE ac.date = %s::date
            )
            SELECT
                m.employee_number,
                m.name,
                m.subsidiary,
                m.betrieb,
                s.erster_start,
                s.letztes_ende,
                COALESCE(s.anzahl_auftraege, 0) as anzahl_auftraege,
                COALESCE(ROUND(s.produktiv_min::numeric), 0) as produktiv_min,
                COALESCE(ROUND(s.leerlauf_min::numeric), 0) as leerlauf_min,
                s.aktiver_auftrag,
                s.aktiv_seit,
                a.anwesend_ab,
                a.anwesend_bis,
                COALESCE(a.anwesend_min, 0) as anwesend_min,
                CASE WHEN s.employee_number IS NOT NULL THEN true ELSE false END as hat_gearbeitet,
                ab.reason as abwesenheit_grund,
                ab.abwesenheit_typ
            FROM alle_mechaniker m
            LEFT JOIN stempelungen s ON m.employee_number = s.employee_number
            LEFT JOIN anwesenheit a ON m.employee_number = a.employee_number
            LEFT JOIN abwesenheiten ab ON m.employee_number = ab.employee_number
            ORDER BY m.betrieb, m.name
        ''', (datum, datum, datum, datum))

        alle = cur.fetchall()
        cur.close()
        conn.close()

        # Filter nach Betrieb
        if subsidiary:
            alle = [m for m in alle if str(m['subsidiary']) == str(subsidiary)]

        # Kategorisieren
        anwesend = []
        abwesend = []
        aktiv = []

        for m in alle:
            entry = {
                'employee_number': m['employee_number'],
                'name': m['name'],
                'betrieb': m['betrieb'],
                'erster_start': m['erster_start'].strftime('%H:%M') if m['erster_start'] else None,
                'letztes_ende': m['letztes_ende'].strftime('%H:%M') if m['letztes_ende'] else None,
                'anzahl_auftraege': m['anzahl_auftraege'],
                'produktiv_min': int(m['produktiv_min']),
                'produktiv_std': round(m['produktiv_min'] / 60, 1),
                'leerlauf_min': int(m['leerlauf_min'] or 0),
                'aktiver_auftrag': m['aktiver_auftrag'],
                'aktiv_seit': m['aktiv_seit'].strftime('%H:%M') if m['aktiv_seit'] else None,
                'anwesend_ab': m['anwesend_ab'].strftime('%H:%M') if m['anwesend_ab'] else None,
                'anwesend_bis': m['anwesend_bis'].strftime('%H:%M') if m['anwesend_bis'] else None,
                'anwesend_min': int(m['anwesend_min'] or 0),
                'anwesend_std': round((m['anwesend_min'] or 0) / 60, 1),
                'abwesenheit_grund': m['abwesenheit_grund'],
                'abwesenheit_typ': m['abwesenheit_typ']
            }
            if m['hat_gearbeitet']:
                anwesend.append(entry)
                if m['aktiver_auftrag']:
                    aktiv.append(entry)
            else:
                abwesend.append(entry)

        total_produktiv = sum(m['produktiv_min'] for m in anwesend)
        total_leerlauf = sum(m['leerlauf_min'] for m in anwesend)

        return jsonify({
            'success': True,
            'datum': datum,
            'timestamp': datetime.now().isoformat(),
            'anwesend': anwesend,
            'abwesend': abwesend,
            'aktiv': aktiv,
            'statistik': {
                'total_mechaniker': len(alle),
                'anwesend': len(anwesend),
                'abwesend': len(abwesend),
                'gerade_aktiv': len(aktiv),
                'produktiv_std': round(total_produktiv / 60, 1),
                'leerlauf_std': round(total_leerlauf / 60, 1)
            }
        })
    except Exception as e:
        logger.exception("Fehler bei Anwesenheits-Report V2")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ANWESENHEITS-REPORT V1 (Legacy) - TAG 116
# DEAKTIVIERT TAG 122: Type 1 nur als abgeschlossene Einträge verfügbar
# ============================================================

@werkstatt_live_bp.route('/anwesenheit/legacy', methods=['GET'])
def get_anwesenheit_report():
    """
    Anwesenheits-Report: Wer hat eingestempelt, wer nicht?

    HINWEIS TAG 122: Dieser Report ist während der Arbeitszeit unzuverlässig!
    Locosoft exportiert Type 1 Einträge erst nach Feierabend (wenn end_time gesetzt).

    Karenzzeit: +5 Minuten nach Sollzeit (08:00)
    Früh: Vor 07:50
    """
    try:
        subsidiary = request.args.get('subsidiary')
        
        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Mechaniker die HEUTE produktiv gestempelt haben (Type 2)
        cur.execute('''
            WITH produktiv_heute AS (
                SELECT DISTINCT 
                    t.employee_number,
                    MIN(t.start_time) as erste_produktiv,
                    MAX(COALESCE(t.end_time, NOW())) as letzte_produktiv,
                    COUNT(DISTINCT t.order_number) as anzahl_auftraege
                FROM times t
                WHERE DATE(t.start_time) = CURRENT_DATE
                  AND t.type = 2
                  AND t.employee_number BETWEEN 5000 AND 5999
                GROUP BY t.employee_number
            ),
            anwesend_heute AS (
                SELECT DISTINCT 
                    t.employee_number,
                    MIN(t.start_time) as erste_anwesend,
                    MAX(COALESCE(t.end_time, NOW())) as letzte_anwesend
                FROM times t
                WHERE DATE(t.start_time) = CURRENT_DATE
                  AND t.type = 1
                  AND t.employee_number BETWEEN 5000 AND 5999
                GROUP BY t.employee_number
            )
            SELECT 
                p.employee_number,
                eh.name,
                eh.subsidiary,
                CASE eh.subsidiary 
                    WHEN 1 THEN 'Deggendorf'
                    WHEN 2 THEN 'Hyundai'
                    WHEN 3 THEN 'Landau'
                    ELSE 'Unbekannt'
                END as betrieb_name,
                p.erste_produktiv,
                p.letzte_produktiv,
                p.anzahl_auftraege,
                a.erste_anwesend,
                a.letzte_anwesend,
                CASE WHEN a.employee_number IS NULL THEN true ELSE false END as vergessen
            FROM produktiv_heute p
            LEFT JOIN anwesend_heute a ON p.employee_number = a.employee_number
            JOIN employees_history eh ON p.employee_number = eh.employee_number 
                AND eh.is_latest_record = true
            WHERE (eh.leave_date IS NULL OR eh.leave_date > CURRENT_DATE)
        ''')
        
        alle = cur.fetchall()
        
        # Filter nach Betrieb
        if subsidiary:
            alle = [m for m in alle if str(m['subsidiary']) == str(subsidiary)]
        
        # Kategorisieren
        vergessen = []  # Type 2 ohne Type 1
        korrekt = []    # Type 1 + Type 2
        frueh = []      # Type 1 vor 07:50
        spaet = []      # Type 1 nach 08:05 (mit Karenz)
        
        for m in alle:
            entry = {
                'employee_number': m['employee_number'],
                'name': m['name'],
                'betrieb': m['betrieb_name'],
                'erste_produktiv': m['erste_produktiv'].strftime('%H:%M') if m['erste_produktiv'] else None,
                'erste_anwesend': m['erste_anwesend'].strftime('%H:%M') if m['erste_anwesend'] else None,
                'produktiv_auftraege': m['anzahl_auftraege']
            }
            
            if m['vergessen']:
                vergessen.append(entry)
            else:
                korrekt.append(entry)
                
                # Prüfe Zeitpunkt
                if m['erste_anwesend']:
                    zeit = m['erste_anwesend'].time()
                    from datetime import time as dt_time
                    
                    # Früh: vor 07:50
                    if zeit < dt_time(7, 50):
                        frueh.append(entry)
                    # Spät: nach 08:05 (08:00 + 5 Min Karenz)
                    elif zeit > dt_time(8, 5):
                        spaet.append(entry)
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'vergessen': vergessen,
            'korrekt': korrekt,
            'frueh': frueh,
            'spaet': spaet,
            'statistik': {
                'total_produktiv': len(alle),
                'vergessen': len(vergessen),
                'korrekt': len(korrekt),
                'frueh': len(frueh),
                'spaet': len(spaet)
            }
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

    Vergleicht gestempelte Zeit mit abgerechneter Zeit pro Charge Type.
    Fokus auf Charge Type 60 (Kulanz) - größter Verlustposten!

    Query-Parameter:
    - wochen: Anzahl Wochen zurück (default: 4)
    - subsidiary: Betrieb filtern (optional)
    """
    try:
        wochen = int(request.args.get('wochen', 4))
        subsidiary = request.args.get('subsidiary')

        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Charge Type Beschreibungen
        CHARGE_TYPES = {
            10: 'Kunde',
            11: 'Kunde (Rabatt)',
            15: 'Garantie Hersteller',
            16: 'Garantie Händler',
            40: 'Garantie',
            60: 'Kulanz',
            90: 'Intern'
        }

        subsidiary_filter = "AND o.subsidiary = %s" if subsidiary else ""
        params = [wochen]
        if subsidiary:
            params.append(int(subsidiary))

        query = f'''
        WITH unique_times AS (
            SELECT DISTINCT order_number, employee_number, start_time, end_time, duration_minutes
            FROM times
            WHERE order_number > 0
              AND duration_minutes > 0
              AND start_time >= NOW() - INTERVAL '%s weeks'
        ),
        gestempelt AS (
            SELECT order_number, SUM(duration_minutes) as stempel_min
            FROM unique_times GROUP BY order_number
        ),
        abgerechnet AS (
            SELECT order_number,
                   MAX(charge_type) as charge_type,
                   SUM(time_units * 6) as abrechn_min
            FROM labours
            WHERE time_units > 0 AND order_number > 0
            GROUP BY order_number
        )
        SELECT
            a.charge_type,
            COUNT(*) as anzahl_auftraege,
            ROUND(SUM(g.stempel_min) / 60.0, 1) as gestempelt_std,
            ROUND(SUM(a.abrechn_min) / 60.0, 1) as abgerechnet_std,
            ROUND((SUM(g.stempel_min) - SUM(a.abrechn_min)) / 60.0, 1) as differenz_std,
            ROUND(100.0 * (SUM(g.stempel_min) - SUM(a.abrechn_min)) / NULLIF(SUM(a.abrechn_min), 0), 1) as differenz_pct
        FROM gestempelt g
        JOIN abgerechnet a ON g.order_number = a.order_number
        JOIN orders o ON g.order_number = o.number
        WHERE o.order_date >= NOW() - INTERVAL '%s weeks'
        {subsidiary_filter}
        GROUP BY a.charge_type
        ORDER BY differenz_std DESC
        '''

        cur.execute(query, params + params[:1])
        by_type = cur.fetchall()

        # Top 20 Verlust-Aufträge (Kulanz)
        query_top = f'''
        WITH unique_times AS (
            -- TAG 211: Konsistente Deduplizierung - sekundengleiche Stempelzeiten desselben Mechanikers auf demselben Auftrag nur einmal
            SELECT DISTINCT ON (employee_number, order_number, start_time, end_time)
                order_number, employee_number, start_time, end_time, duration_minutes
            FROM times 
            WHERE order_number > 0 
              AND duration_minutes > 0 
              AND type = 2
              AND end_time IS NOT NULL
              AND start_time >= NOW() - INTERVAL '%s weeks'
            ORDER BY employee_number, order_number, start_time, end_time
        ),
        gestempelt AS (
            SELECT order_number, SUM(duration_minutes) as stempel_min FROM unique_times GROUP BY order_number
        ),
        abgerechnet AS (
            SELECT order_number, MAX(charge_type) as charge_type, SUM(time_units * 6) as abrechn_min
            FROM labours WHERE time_units > 0 GROUP BY order_number
        )
        SELECT
            g.order_number,
            o.order_date,
            a.charge_type,
            v.license_plate as kennzeichen,
            ROUND(g.stempel_min) as gestempelt_min,
            ROUND(a.abrechn_min) as abgerechnet_min,
            ROUND(g.stempel_min - a.abrechn_min) as verlust_min
        FROM gestempelt g
        JOIN abgerechnet a ON g.order_number = a.order_number
        JOIN orders o ON g.order_number = o.number
        LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
        WHERE g.stempel_min > a.abrechn_min
          AND a.charge_type = 60
          {subsidiary_filter}
        ORDER BY (g.stempel_min - a.abrechn_min) DESC
        LIMIT 20
        '''

        cur.execute(query_top, params)
        top_verluste = cur.fetchall()

        cur.close()
        conn.close()

        # Statistiken berechnen
        total_gestempelt = sum(float(r['gestempelt_std'] or 0) for r in by_type)
        total_abgerechnet = sum(float(r['abgerechnet_std'] or 0) for r in by_type)
        total_differenz = sum(float(r['differenz_std'] or 0) for r in by_type)

        # Ergebnis formatieren
        result_by_type = []
        for r in by_type:
            ct = r['charge_type']
            result_by_type.append({
                'charge_type': ct,
                'charge_type_name': CHARGE_TYPES.get(ct, f'Typ {ct}'),
                'anzahl_auftraege': r['anzahl_auftraege'],
                'gestempelt_std': float(r['gestempelt_std'] or 0),
                'abgerechnet_std': float(r['abgerechnet_std'] or 0),
                'differenz_std': float(r['differenz_std'] or 0),
                'differenz_pct': float(r['differenz_pct'] or 0),
                'verlust_eur': round(float(r['differenz_std'] or 0) * 85, 0) if r['differenz_std'] and r['differenz_std'] > 0 else 0
            })

        return jsonify({
            'success': True,
            'zeitraum_wochen': wochen,
            'statistik': {
                'gestempelt_std': round(total_gestempelt, 1),
                'abgerechnet_std': round(total_abgerechnet, 1),
                'differenz_std': round(total_differenz, 1),
                'verlust_eur': round(total_differenz * 85, 0) if total_differenz > 0 else 0,
                'stundensatz': 85
            },
            'by_charge_type': result_by_type,
            'top_verluste_kulanz': [
                {
                    'auftrag_nr': r['order_number'],
                    'datum': r['order_date'].isoformat() if r['order_date'] else None,
                    'kennzeichen': r['kennzeichen'],
                    'gestempelt_min': r['gestempelt_min'],
                    'abgerechnet_min': r['abgerechnet_min'],
                    'verlust_min': r['verlust_min'],
                    'verlust_eur': round(r['verlust_min'] / 60 * 85, 0)
                }
                for r in top_verluste
            ]
        })

    except Exception as e:
        logger.exception("Fehler bei Kulanz-Monitoring")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# DRIVE TAGES-BRIEFING - TAG 119
# Morgen-Report für Werkstattleiter
# ============================================================

@werkstatt_live_bp.route('/drive/briefing', methods=['GET'])
def get_drive_briefing():
    """
    DRIVE Tages-Briefing: Was erwartet uns heute?

    Parameter:
    - datum: ISO-Datum (YYYY-MM-DD), default: heute
    - subsidiary: Betrieb-Filter (optional)

    Zeigt:
    - Aufträge für gewähltes Datum mit ML-Vorhersage
    - Unterbewertete Aufträge (ML > Vorgabe)
    - Garantie-Aufträge mit Warnung
    - Realistische Tagesauslastung
    """
    try:
        import json as json_lib
        import pickle
        from datetime import datetime as dt

        # Datum-Parameter (default: heute)
        datum_str = request.args.get('datum')
        if datum_str:
            try:
                selected_date = dt.strptime(datum_str, '%Y-%m-%d').date()
            except ValueError:
                selected_date = dt.now().date()
        else:
            selected_date = dt.now().date()

        subsidiary = request.args.get('subsidiary')

        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Labour Corrections laden
        corrections_path = "/opt/greiner-portal/data/ml/labour_corrections.json"
        labour_corrections = {}
        if os.path.exists(corrections_path):
            with open(corrections_path, 'r') as f:
                labour_corrections = json_lib.load(f)

        subsidiary_filter = "AND o.subsidiary = %s" if subsidiary else ""
        params = [selected_date, selected_date]  # Für die beiden Datum-Vergleiche
        if subsidiary:
            params.append(int(subsidiary))

        query = f'''
        SELECT
            o.number as auftrag_nr,
            o.subsidiary as betrieb,
            o.order_date,
            o.estimated_inbound_time,
            o.estimated_outbound_time,
            v.license_plate as kennzeichen,
            m.description as marke,
            COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name) as kunde,
            l.total_aw as vorgabe_aw,
            l.labour_type,
            l.charge_type,
            o.has_open_positions as ist_offen
        FROM orders o
        LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
        LEFT JOIN makes m ON v.make_number = m.make_number
        LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
        LEFT JOIN LATERAL (
            SELECT
                SUM(time_units) as total_aw,
                MAX(labour_type) as labour_type,
                MAX(charge_type) as charge_type
            FROM labours WHERE order_number = o.number AND time_units > 0
        ) l ON true
        WHERE DATE(o.estimated_inbound_time) = %s
           OR (DATE(o.order_date) = %s AND o.has_open_positions = true)
        {subsidiary_filter}
        ORDER BY o.estimated_inbound_time, o.order_date
        '''

        cur.execute(query, params)
        auftraege_raw = cur.fetchall()

        cur.close()
        conn.close()

        # ML-Vorhersagen und Kategorisierung
        auftraege = []
        total_vorgabe = 0
        total_ml = 0
        garantie_count = 0
        unterbewertet_count = 0
        kritisch = []
        garantie_auftraege = []

        for a in auftraege_raw:
            vorgabe_aw = float(a['vorgabe_aw'] or 0)
            labour_type = a['labour_type'] or 'W'

            # Correction Factor
            correction = labour_corrections.get('by_type', {}).get(labour_type, 1.0)

            # ML-Vorhersage (vereinfacht: Vorgabe * Correction)
            ml_aw = round(vorgabe_aw * correction, 1)
            potenzial = round(ml_aw - vorgabe_aw, 1)

            total_vorgabe += vorgabe_aw
            total_ml += ml_aw

            ist_garantie = labour_type == 'G'
            ist_unterbewertet = potenzial > 1.0

            if ist_garantie:
                garantie_count += 1
            if ist_unterbewertet:
                unterbewertet_count += 1

            auftrag = {
                'auftrag_nr': a['auftrag_nr'],
                'betrieb': a['betrieb'],
                'kennzeichen': a['kennzeichen'],
                'marke': a['marke'],
                'kunde': a['kunde'],
                'termin': a['estimated_inbound_time'].strftime('%H:%M') if a['estimated_inbound_time'] else None,
                'vorgabe_aw': vorgabe_aw,
                'ml_aw': ml_aw,
                'potenzial_aw': potenzial,
                'labour_type': labour_type,
                'ist_garantie': ist_garantie,
                'ist_unterbewertet': ist_unterbewertet,
                'correction_factor': correction
            }

            auftraege.append(auftrag)

            if ist_unterbewertet and potenzial > 2.0:
                kritisch.append(auftrag)
            if ist_garantie:
                garantie_auftraege.append(auftrag)

        # Sortiere kritische nach Potenzial
        kritisch.sort(key=lambda x: x['potenzial_aw'], reverse=True)

        return jsonify({
            'success': True,
            'datum': selected_date.isoformat(),
            'ist_heute': selected_date == dt.now().date(),
            'uhrzeit': dt.now().strftime('%H:%M'),
            'zusammenfassung': {
                'anzahl_auftraege': len(auftraege),
                'vorgabe_aw_gesamt': round(total_vorgabe, 1),
                'ml_aw_gesamt': round(total_ml, 1),
                'differenz_aw': round(total_ml - total_vorgabe, 1),
                'differenz_prozent': round((total_ml - total_vorgabe) / total_vorgabe * 100, 1) if total_vorgabe > 0 else 0,
                'garantie_auftraege': garantie_count,
                'unterbewertet_auftraege': unterbewertet_count,
                'kritisch_auftraege': len(kritisch)
            },
            'warnungen': {
                'kritisch': kritisch[:5],  # Top 5 kritische
                'garantie': garantie_auftraege[:5]  # Top 5 Garantie
            },
            'alle_auftraege': auftraege,
            'empfehlung': f"Plane +{round(total_ml - total_vorgabe, 0)} AW mehr ein als Herstellervorgabe!" if total_ml > total_vorgabe else "Kapazität ausreichend."
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
    DRIVE Kapazitätsplanung: Realistische Auslastung

    TAG 122: Jetzt MIT Abwesenheiten aus absence_calendar!

    Zeigt Kapazität pro Tag mit:
    - Herstellervorgabe (SOLL)
    - DRIVE-Korrektur (realistisch)
    - Aufteilung nach Lohnart (G/W/I)
    - Mechaniker-Verfügbarkeit (Abwesenheiten berücksichtigt)
    """
    try:
        import json as json_lib

        tage = int(request.args.get('tage', 7))
        subsidiary = request.args.get('subsidiary')

        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Labour Corrections laden
        corrections_path = "/opt/greiner-portal/data/ml/labour_corrections.json"
        labour_corrections = {}
        if os.path.exists(corrections_path):
            with open(corrections_path, 'r') as f:
                labour_corrections = json_lib.load(f)

        correction_g = labour_corrections.get('by_type', {}).get('G', 1.24)
        correction_w = labour_corrections.get('by_type', {}).get('W', 0.94)
        correction_i = labour_corrections.get('by_type', {}).get('I', 1.08)

        # =====================================================================
        # TAG 122: Mechaniker-Kapazität mit Abwesenheiten
        # =====================================================================
        # 1. Aktive Mechaniker pro Betrieb (5000-5999, ohne leave_date)
        cur.execute("""
            SELECT
                subsidiary as betrieb,
                COUNT(DISTINCT employee_number) as anzahl_mechaniker
            FROM (
                SELECT DISTINCT ON (employee_number)
                    employee_number, subsidiary
                FROM employees_history
                WHERE employee_number BETWEEN 5000 AND 5999
                  AND leave_date IS NULL
                ORDER BY employee_number, validity_date DESC
            ) aktive
            GROUP BY subsidiary
        """)
        mechaniker_pro_betrieb = {r['betrieb']: r['anzahl_mechaniker'] for r in cur.fetchall()}
        logger.debug(f"DRIVE: Mechaniker pro Betrieb: {mechaniker_pro_betrieb}")

        # 2. Abwesenheiten pro Tag/Betrieb (nächste X Tage)
        cur.execute("""
            WITH aktive_mechaniker AS (
                SELECT DISTINCT ON (employee_number)
                    employee_number, subsidiary
                FROM employees_history
                WHERE employee_number BETWEEN 5000 AND 5999
                  AND leave_date IS NULL
                ORDER BY employee_number, validity_date DESC
            )
            SELECT
                ac.date as tag,
                am.subsidiary as betrieb,
                COUNT(*) as anzahl_abwesend,
                SUM(ac.day_contingent) as tage_abwesend,
                STRING_AGG(DISTINCT ac.reason, ', ') as gruende
            FROM absence_calendar ac
            JOIN aktive_mechaniker am ON ac.employee_number = am.employee_number
            WHERE ac.date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '%s days'
            GROUP BY ac.date, am.subsidiary
            ORDER BY ac.date, am.subsidiary
        """, [tage])
        abwesenheiten_raw = cur.fetchall()

        # Abwesenheiten als Dict: {(tag, betrieb): {'anzahl': X, 'tage': Y, 'gruende': 'Url, Krn'}}
        abwesenheiten = {}
        for r in abwesenheiten_raw:
            key = (r['tag'].isoformat(), r['betrieb'])
            abwesenheiten[key] = {
                'anzahl': r['anzahl_abwesend'],
                'tage': float(r['tage_abwesend'] or 0),
                'gruende': r['gruende'] or ''
            }

        # AW pro Mechaniker pro Tag (Basis für Kapazitätsberechnung)
        AW_PRO_MECHANIKER = 10  # ca. 10 AW pro Mechaniker pro Tag

        subsidiary_filter = "AND o.subsidiary = %s" if subsidiary else ""
        params = [tage]
        if subsidiary:
            params.append(int(subsidiary))

        query = f'''
        SELECT
            DATE(COALESCE(o.estimated_inbound_time, o.order_date)) as tag,
            o.subsidiary as betrieb,
            COUNT(*) as anzahl_auftraege,
            SUM(CASE WHEN l.labour_type = 'G' THEN l.total_aw ELSE 0 END) as aw_garantie,
            SUM(CASE WHEN l.labour_type = 'W' THEN l.total_aw ELSE 0 END) as aw_werkstatt,
            SUM(CASE WHEN l.labour_type = 'I' THEN l.total_aw ELSE 0 END) as aw_intern,
            SUM(CASE WHEN l.labour_type NOT IN ('G', 'W', 'I') OR l.labour_type IS NULL THEN l.total_aw ELSE 0 END) as aw_sonstige,
            SUM(l.total_aw) as aw_gesamt
        FROM orders o
        LEFT JOIN LATERAL (
            SELECT SUM(time_units) as total_aw, MAX(labour_type) as labour_type
            FROM labours WHERE order_number = o.number AND time_units > 0
        ) l ON true
        WHERE DATE(COALESCE(o.estimated_inbound_time, o.order_date)) BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '%s days'
          AND o.has_open_positions = true
        {subsidiary_filter}
        GROUP BY DATE(COALESCE(o.estimated_inbound_time, o.order_date)), o.subsidiary
        ORDER BY tag, betrieb
        '''

        cur.execute(query, params)
        rows = cur.fetchall()

        cur.close()
        conn.close()

        # Kapazität pro Betrieb (Basis ohne Abwesenheiten)
        # BETRIEB_NAMEN wird jetzt aus standort_utils importiert (SSOT)

        result = []
        for r in rows:
            aw_g = float(r['aw_garantie'] or 0)
            aw_w = float(r['aw_werkstatt'] or 0)
            aw_i = float(r['aw_intern'] or 0)
            aw_s = float(r['aw_sonstige'] or 0)
            aw_gesamt = float(r['aw_gesamt'] or 0)

            # DRIVE-Korrektur anwenden
            aw_g_korrigiert = aw_g * correction_g
            aw_w_korrigiert = aw_w * correction_w
            aw_i_korrigiert = aw_i * correction_i
            aw_drive = aw_g_korrigiert + aw_w_korrigiert + aw_i_korrigiert + aw_s

            betrieb = r['betrieb']
            tag_str = r['tag'].isoformat()

            # TAG 122: Dynamische Kapazität basierend auf Mechaniker-Anzahl
            gesamt_mechaniker = mechaniker_pro_betrieb.get(betrieb, 0)
            basis_kapazitaet = gesamt_mechaniker * AW_PRO_MECHANIKER

            # Abwesenheiten für diesen Tag/Betrieb
            abw_key = (tag_str, betrieb)
            abw_info = abwesenheiten.get(abw_key, {'anzahl': 0, 'tage': 0, 'gruende': ''})
            abwesend_tage = abw_info['tage']  # Summe der day_contingent (0.5 = halber Tag)

            # Reduzierte Kapazität
            verfuegbare_mechaniker = gesamt_mechaniker - abwesend_tage
            kapazitaet = max(0, round(verfuegbare_mechaniker * AW_PRO_MECHANIKER))

            # Auslastung berechnen (Division by Zero vermeiden)
            auslastung_hersteller = round(aw_gesamt / kapazitaet * 100, 1) if kapazitaet > 0 else 0
            auslastung_drive = round(aw_drive / kapazitaet * 100, 1) if kapazitaet > 0 else 0

            result.append({
                'tag': tag_str,
                'wochentag': r['tag'].strftime('%A'),
                'betrieb': betrieb,
                'betrieb_name': BETRIEB_NAMEN.get(betrieb, '?'),
                'anzahl_auftraege': r['anzahl_auftraege'],
                'kapazitaet_aw': kapazitaet,
                'kapazitaet_basis_aw': basis_kapazitaet,  # Ohne Abwesenheiten
                'mechaniker': {
                    'gesamt': gesamt_mechaniker,
                    'abwesend': abw_info['anzahl'],
                    'abwesend_tage': round(abwesend_tage, 1),
                    'verfuegbar': round(verfuegbare_mechaniker, 1),
                    'gruende': abw_info['gruende']
                },
                'hersteller': {
                    'gesamt_aw': round(aw_gesamt, 1),
                    'garantie_aw': round(aw_g, 1),
                    'werkstatt_aw': round(aw_w, 1),
                    'intern_aw': round(aw_i, 1),
                    'auslastung_pct': auslastung_hersteller
                },
                'drive': {
                    'gesamt_aw': round(aw_drive, 1),
                    'garantie_aw': round(aw_g_korrigiert, 1),
                    'werkstatt_aw': round(aw_w_korrigiert, 1),
                    'intern_aw': round(aw_i_korrigiert, 1),
                    'auslastung_pct': auslastung_drive
                },
                'differenz_aw': round(aw_drive - aw_gesamt, 1),
                'warnung': auslastung_drive > 90  # >90% = Warnung
            })

        return jsonify({
            'success': True,
            'korrekturfaktoren': {
                'G': correction_g,
                'W': correction_w,
                'I': correction_i
            },
            'mechaniker_pro_betrieb': mechaniker_pro_betrieb,
            'aw_pro_mechaniker': AW_PRO_MECHANIKER,
            'tage': result
        })

    except Exception as e:
        logger.exception("Fehler bei DRIVE Kapazität")
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

        # 4b. GUDAT Disposition holen (TAG 125)
        gudat_disposition = get_gudat_disposition(datum)

        # Name-Mapping: Gudat "Vorname Nachname" → Locosoft "Nachname, Vorname"
        def match_gudat_name(locosoft_name, gudat_names):
            """Findet passenden Gudat-Namen für Locosoft-Namen"""
            if not locosoft_name:
                return None
            # Locosoft: "Reitmeier, Tobias" → parts = ["Reitmeier", "Tobias"]
            parts = [p.strip() for p in locosoft_name.split(',')]
            if len(parts) >= 2:
                nachname, vorname = parts[0], parts[1].split()[0]  # Nur erster Vorname
                # Gudat: "Tobias Reitmeier"
                gudat_pattern1 = f"{vorname} {nachname}"
                gudat_pattern2 = f"{nachname} {vorname}"
                for gn in gudat_names:
                    gn_lower = gn.lower()
                    if gudat_pattern1.lower() == gn_lower or gudat_pattern2.lower() == gn_lower:
                        return gn
                    # Fuzzy: enthält Vor- und Nachname
                    if vorname.lower() in gn_lower and nachname.lower() in gn_lower:
                        return gn
            return None

        # Gudat-Mechaniker-Mapping erstellen
        gudat_to_locosoft = {}
        for mech in mechaniker_list:
            matched = match_gudat_name(mech['name'], gudat_disposition.keys())
            if matched:
                gudat_to_locosoft[mech['employee_number']] = gudat_disposition[matched]

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
                # TAG 213 FIX: None-Safe für kennzeichen
                kz = (gt.get('kennzeichen') or '').replace(' ', '').replace('-', '').upper()
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


@werkstatt_live_bp.route('/meine-ueberschreitungen', methods=['GET'])
def meine_ueberschreitungen():
    """
    GET /api/werkstatt/live/meine-ueberschreitungen
    
    Prüft ob der aktuelle User (Serviceberater) betroffene Überschreitungen hat.
    Wird für globales Modal verwendet.
    """
    try:
        from flask_login import current_user
        from api.werkstatt_data import WerkstattData
        from datetime import date
        
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Nicht angemeldet'}), 401
        
        # Hole Employee-Nummer des aktuellen Users
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Hole LDAP-Username
            user_id = getattr(current_user, 'id', None)
            if not user_id:
                return jsonify({'success': False, 'error': 'Keine User-ID gefunden'}), 401
            
            cursor.execute("""
                SELECT username FROM users WHERE id = %s
            """, (user_id,))
            user_row = cursor.fetchone()
            
            if not user_row:
                return jsonify({'success': False, 'error': 'User nicht gefunden'}), 404
            
            ldap_username = user_row[0].split('@')[0] if '@' in user_row[0] else user_row[0]
            
            # Hole Locosoft-ID aus ldap_employee_mapping
            cursor.execute("""
                SELECT lem.locosoft_id
                FROM ldap_employee_mapping lem
                JOIN employees e ON lem.employee_id = e.id
                WHERE lem.ldap_username = %s AND e.aktiv = true
            """, (ldap_username,))
            
            mapping_row = cursor.fetchone()
            if not mapping_row or not mapping_row[0]:
                return jsonify({
                    'success': True,
                    'hat_ueberschreitungen': False,
                    'message': 'Keine Employee-Nummer zugeordnet'
                })
            
            meine_employee_nr = mapping_row[0]
            logger.info(f"Meine-Überschreitungen: User {ldap_username} hat Employee-Nr {meine_employee_nr}")
        
        # Fallback-User Mapping
        FALLBACK_USER_BY_BETRIEB = {
            1: [3007],  # Deggendorf: Matthias König
            2: [3007],  # Deggendorf Hyundai: Matthias König
            3: [1003, 4002]  # Landau: Rolf Sterr + Leonhard Keidl
        }
        
        # Stempeluhr-Daten holen (nur heute, alle Betriebe)
        stempeluhr_data = WerkstattData.get_stempeluhr(
            datum=date.today(),
            subsidiaries=None  # Alle Betriebe
        )
        
        # ZUSÄTZLICH: Prüfe auch abgeschlossene Aufträge von heute mit Überschreitungen
        # (get_stempeluhr zeigt nur aktive Stempelungen)
        ueberschritten_abgeschlossen = []
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Hole alle Aufträge von heute, die überschritten sind (auch abgeschlossene)
            cursor.execute("""
                WITH gestempelt_heute AS (
                    SELECT 
                        t.order_number,
                        SUM(EXTRACT(EPOCH FROM (COALESCE(t.end_time, NOW()) - t.start_time)) / 60) as gestempelt_min
                    FROM times t
                    WHERE DATE(t.start_time) = CURRENT_DATE
                      AND t.order_number > 0
                      AND t.type = 2
                    GROUP BY t.order_number
                ),
                vorgabe_aw AS (
                    SELECT 
                        l.order_number,
                        SUM(l.time_units) as vorgabe_aw
                    FROM labours l
                    WHERE l.time_units > 0
                    GROUP BY l.order_number
                )
                SELECT 
                    g.order_number,
                    g.gestempelt_min,
                    v.vorgabe_aw,
                    (g.gestempelt_min / (v.vorgabe_aw * 6) * 100) as fortschritt_prozent,
                    o.order_taking_employee_no as serviceberater_nr
                FROM gestempelt_heute g
                JOIN vorgabe_aw v ON g.order_number = v.order_number
                JOIN orders o ON g.order_number = o.number
                WHERE v.vorgabe_aw > 0
                  AND (g.gestempelt_min / (v.vorgabe_aw * 6) * 100) > 100
            """)
            
            for row in cursor.fetchall():
                ueberschritten_abgeschlossen.append({
                    'order_number': row['order_number'],
                    'gestempelt_min': row['gestempelt_min'],
                    'vorgabe_aw': row['vorgabe_aw'],
                    'fortschritt_prozent': row['fortschritt_prozent'],
                    'serviceberater_nr': row['serviceberater_nr']
                })
        
        if not stempeluhr_data.get('success'):
            # Wenn Stempeluhr-Daten nicht verfügbar, nutze nur abgeschlossene
            ueberschritten = ueberschritten_abgeschlossen
        else:
            aktive_mechaniker = stempeluhr_data.get('aktive_mechaniker', [])
            ueberschritten_aktiv = []
            for m in aktive_mechaniker:
                fortschritt = m.get('fortschritt_prozent', 0)
                if fortschritt > 100:
                    ueberschritten_aktiv.append({
                        'order_number': m.get('order_number'),
                        'gestempelt_min': m.get('laufzeit_min', 0),
                        'vorgabe_aw': m.get('vorgabe_aw', 0),
                        'fortschritt_prozent': fortschritt,
                        'serviceberater_nr': m.get('serviceberater_nr')
                    })
            
            # Kombiniere aktive und abgeschlossene Überschreitungen
            auftrag_nrs_aktiv = {m.get('order_number') for m in ueberschritten_aktiv}
            ueberschritten = ueberschritten_aktiv + [
                u for u in ueberschritten_abgeschlossen 
                if u['order_number'] not in auftrag_nrs_aktiv
            ]
        
        logger.info(f"Meine-Überschreitungen: {len(ueberschritten)} Überschreitungen gefunden ({len(ueberschritten_abgeschlossen)} abgeschlossen)")
        
        if not ueberschritten:
            return jsonify({
                'success': True,
                'hat_ueberschreitungen': False,
                'message': 'Keine Überschreitungen gefunden'
            })
        
        # Prüfe ob aktuelle User betroffen ist
        betroffene_auftraege = []
        
        for ueberschritt in ueberschritten:
            auftrag_nr = ueberschritt.get('order_number')
            if not auftrag_nr:
                continue
            
            try:
                auftrag_detail = WerkstattData.get_auftrag_detail(auftrag_nr)
                if not auftrag_detail.get('success'):
                    continue
                
                auftrag = auftrag_detail['auftrag']
                serviceberater_nr = auftrag.get('serviceberater_nr')
                betrieb = auftrag.get('betrieb')
                
                # Konvertiere zu int für Vergleich (falls None oder String)
                serviceberater_nr_int = int(serviceberater_nr) if serviceberater_nr else None
                meine_employee_nr_int = int(meine_employee_nr) if meine_employee_nr else None
                
                ist_betroffen = False
                
                # Fall 1: Serviceberater zugeordnet → Prüfe ob aktueller User = Serviceberater
                if serviceberater_nr_int and meine_employee_nr_int and serviceberater_nr_int == meine_employee_nr_int:
                    ist_betroffen = True
                    logger.info(f"Auftrag {auftrag_nr}: Serviceberater {serviceberater_nr_int} = User {meine_employee_nr_int} → BETROFFEN")
                # Fall 2: Kein Serviceberater → Prüfe ob aktueller User = Fallback-User
                elif not serviceberater_nr_int and betrieb and meine_employee_nr_int:
                    fallback_users = FALLBACK_USER_BY_BETRIEB.get(betrieb, [])
                    if meine_employee_nr_int in fallback_users:
                        ist_betroffen = True
                        logger.info(f"Auftrag {auftrag_nr}: Kein SB, User {meine_employee_nr_int} ist Fallback für Betrieb {betrieb} → BETROFFEN")
                else:
                    logger.debug(f"Auftrag {auftrag_nr}: SB={serviceberater_nr_int}, User={meine_employee_nr_int}, Betrieb={betrieb} → NICHT betroffen")
                
                if ist_betroffen:
                    s = auftrag.get('summen', {})
                    f = auftrag.get('fahrzeug', {})
                    
                    # WICHTIG: Verwende die gestempelte Zeit von HEUTE (aus ueberschritt), nicht aus get_auftrag_detail
                    # get_auftrag_detail summiert ALLE Stempelungen (auch von anderen Tagen)
                    gestempelt_min_heute = ueberschritt.get('gestempelt_min', 0)
                    vorgabe_aw = ueberschritt.get('vorgabe_aw', 0)
                    vorgabe_min = vorgabe_aw * 6
                    
                    # Falls nicht in ueberschritt vorhanden, nutze get_auftrag_detail als Fallback
                    if gestempelt_min_heute == 0:
                        gestempelt_min_heute = s.get('gestempelt_min', 0)
                    if vorgabe_aw == 0:
                        vorgabe_aw = s.get('total_aw', 0)
                        vorgabe_min = vorgabe_aw * 6
                    
                    diff_min = gestempelt_min_heute - vorgabe_min
                    diff_prozent = (gestempelt_min_heute / vorgabe_min * 100) if vorgabe_min > 0 else 0
                    
                    # NUR wenn tatsächlich überschritten (>100%), dann hinzufügen
                    if diff_prozent <= 100:
                        logger.debug(f"Auftrag {auftrag_nr}: {diff_prozent:.1f}% ist KEINE Überschreitung - überspringe")
                        continue
                    
                    # Hole Mechaniker-Namen für diesen Auftrag (von heute)
                    mechaniker_namen = []
                    with locosoft_session() as conn_mech:
                        cursor_mech = conn_mech.cursor(cursor_factory=RealDictCursor)
                        cursor_mech.execute("""
                            SELECT DISTINCT e.name
                            FROM times t
                            JOIN employees_history e ON t.employee_number = e.employee_number
                                AND e.is_latest_record = true
                            WHERE t.order_number = %s
                              AND DATE(t.start_time) = CURRENT_DATE
                              AND t.type = 2
                            ORDER BY e.name
                        """, (auftrag_nr,))
                        mechaniker_rows = cursor_mech.fetchall()
                        mechaniker_namen = [r['name'] for r in mechaniker_rows]
                    
                    # Formatiere Auftragsdatum
                    auftragsdatum_str = auftrag.get('datum', '')  # get_auftrag_detail gibt 'datum' zurück
                    
                    betroffene_auftraege.append({
                        'auftrag_nr': auftrag_nr,
                        'fahrzeug': {
                            'kennzeichen': f.get('kennzeichen', '-'),
                            'marke': f.get('marke', ''),
                            'modell': f.get('modell', '')
                        },
                        'betrieb': betrieb,
                        'betrieb_name': BETRIEB_NAMEN.get(betrieb, 'Unbekannt'),
                        'gestempelt_min': gestempelt_min_heute,
                        'vorgabe_min': vorgabe_min,
                        'diff_min': diff_min,
                        'diff_prozent': diff_prozent,
                        'hat_serviceberater': bool(serviceberater_nr and serviceberater_nr > 0),
                        'serviceberater_nr': serviceberater_nr,
                        'serviceberater_name': auftrag.get('serviceberater_name', ''),
                        'auftragsdatum': auftragsdatum_str,
                        'mechaniker': mechaniker_namen
                    })
                    
                    # Nur ersten betroffenen Auftrag zurückgeben (Modal zeigt nur einen)
                    break
                    
            except Exception as e:
                logger.warning(f"Fehler beim Prüfen von Auftrag {auftrag_nr}: {e}")
                continue
        
        if betroffene_auftraege:
            return jsonify({
                'success': True,
                'hat_ueberschreitungen': True,
                'auftrag': betroffene_auftraege[0]  # Erster betroffener Auftrag
            })
        else:
            return jsonify({
                'success': True,
                'hat_ueberschreitungen': False,
                'message': 'Keine Überschreitungen für Sie gefunden'
            })
    
    except Exception as e:
        logger.exception("Fehler bei meine-ueberschreitungen")
        return jsonify({'success': False, 'error': str(e)}), 500


@werkstatt_live_bp.route('/automatisch-verteilte-stempelungen', methods=['GET'])
def get_automatisch_verteilte_stempelungen():
    """
    Identifiziert Aufträge mit automatisch verteilten Stempelungen (Mehrfachstempelungen).
    
    Diese Aufträge sollten vom Serviceleiter geprüft und ggf. manuell korrigiert werden.
    
    Query-Parameter:
        betrieb: Betrieb-ID (1=DEGO, 2=DEGH, 3=LANO, None=alle)
        tage_zurueck: Wie viele Tage zurück (default: 30)
        min_lines: Mindestanzahl Lines für Mehrfachstempelung (default: 3)
    
    Returns:
        JSON mit Liste der betroffenen Aufträge und Details
    """
    from api.werkstatt_data import WerkstattData
    
    try:
        betrieb = request.args.get('betrieb', type=int)
        tage_zurueck = request.args.get('tage_zurueck', default=30, type=int)
        min_lines = request.args.get('min_lines', default=3, type=int)
        
        data = WerkstattData.get_automatisch_verteilte_stempelungen(
            betrieb=betrieb,
            tage_zurueck=tage_zurueck,
            min_lines=min_lines
        )
        
        return jsonify(data)
    
    except Exception as e:
        logger.exception("Fehler bei automatisch-verteilte-stempelungen")
        return jsonify({'success': False, 'error': str(e)}), 500
