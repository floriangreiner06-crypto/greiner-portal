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

# Logging
logger = logging.getLogger(__name__)

# Blueprint
werkstatt_live_bp = Blueprint('werkstatt_live', __name__, url_prefix='/api/werkstatt/live')

# Locosoft Connection
import psycopg2
from psycopg2.extras import RealDictCursor


def get_locosoft_connection():
    """Erstellt Verbindung zu Locosoft PostgreSQL"""
    # .env Werte direkt aus Environment oder aus Datei
    from dotenv import load_dotenv
    
    # Versuche .env zu laden (falls nicht schon geladen)
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    
    return psycopg2.connect(
        host=os.getenv('LOCOSOFT_HOST'),
        port=os.getenv('LOCOSOFT_PORT', 5432),
        database=os.getenv('LOCOSOFT_DATABASE'),
        user=os.getenv('LOCOSOFT_USER'),
        password=os.getenv('LOCOSOFT_PASSWORD')
    )


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

# Azubis - stempeln nur Anwesenheit, keine Aufträge
# Diese werden vom Leerlauf-Alarm ausgenommen
AZUBI_MA_NUMMERN = [5028, 5026]  # Thammer, Suttner

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
    Ersetzt den SQLite-Mirror-basierten Endpoint.
    
    Query-Parameter:
    - zeitraum: heute|woche|monat|vormonat|quartal|jahr|custom
    - von: Startdatum (bei custom)
    - bis: Enddatum (bei custom)  
    - betrieb: alle|1|2|3
    - sort: leistungsgrad|stempelzeit|aw|auftraege
    - inkl_ehemalige: 0|1
    """
    try:
        zeitraum = request.args.get('zeitraum', 'monat')
        von = request.args.get('von')
        bis = request.args.get('bis')
        betrieb = request.args.get('betrieb', 'alle')
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
        
        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Mechaniker-Leistung LIVE aus Locosoft (DEDUPLIZIERT!)
        query = """
            WITH 
            -- Stempelzeit pro Mechaniker/Tag (DEDUPLIZIERT!)
            stempel_dedupliziert AS (
                SELECT 
                    employee_number,
                    DATE(start_time) as datum,
                    SUM(minuten) as stempel_min,
                    COUNT(DISTINCT order_number) as auftraege
                FROM (
                    SELECT DISTINCT ON (employee_number, start_time, end_time)
                        employee_number,
                        order_number,
                        start_time,
                        end_time,
                        EXTRACT(EPOCH FROM (end_time - start_time)) / 60 as minuten
                    FROM times
                    WHERE type = 2
                      AND end_time IS NOT NULL
                      AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
                ) dedup
                GROUP BY employee_number, DATE(start_time)
            ),
            -- Anwesenheit pro Mechaniker/Tag
            anwesenheit AS (
                SELECT 
                    employee_number,
                    DATE(start_time) as datum,
                    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as anwesend_min
                FROM times
                WHERE type = 1
                  AND end_time IS NOT NULL
                  AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
                GROUP BY employee_number, DATE(start_time)
            ),
            -- Verrechnete AW pro Mechaniker (aus Rechnungen im Zeitraum)
            aw_verrechnet AS (
                SELECT 
                    l.mechanic_no as employee_number,
                    SUM(l.time_units) as aw,
                    SUM(l.net_price_in_order) as umsatz
                FROM labours l
                JOIN invoices i ON l.invoice_number = i.invoice_number AND l.invoice_type = i.invoice_type
                WHERE i.invoice_date >= %s AND i.invoice_date <= %s
                  AND l.is_invoiced = true
                  AND l.mechanic_no IS NOT NULL
                  
                GROUP BY l.mechanic_no
            ),
            -- Mechaniker-Aggregation
            mechaniker_summen AS (
                SELECT 
                    COALESCE(s.employee_number, a.employee_number, aw.employee_number) as employee_number,
                    COUNT(DISTINCT COALESCE(s.datum, a.datum)) as tage,
                    COALESCE(SUM(s.auftraege), 0) as auftraege,
                    COALESCE(SUM(s.stempel_min), 0) as stempelzeit,
                    COALESCE(SUM(a.anwesend_min), 0) as anwesenheit,
                    COALESCE(MAX(aw.aw), 0) as aw,
                    COALESCE(MAX(aw.umsatz), 0) as umsatz
                FROM stempel_dedupliziert s
                FULL OUTER JOIN anwesenheit a ON s.employee_number = a.employee_number AND s.datum = a.datum
                LEFT JOIN aw_verrechnet aw ON COALESCE(s.employee_number, a.employee_number) = aw.employee_number
                GROUP BY COALESCE(s.employee_number, a.employee_number, aw.employee_number)
            )
            SELECT 
                ms.employee_number as mechaniker_nr,
                eh.name as name,
                eh.subsidiary as betrieb,
                ms.tage,
                ms.auftraege,
                ROUND(ms.stempelzeit::numeric, 0) as stempelzeit,
                ROUND(ms.anwesenheit::numeric, 0) as anwesenheit,
                ROUND(ms.aw::numeric, 1) as aw,
                ROUND(ms.umsatz::numeric, 2) as umsatz,
                CASE 
                    WHEN ms.stempelzeit > 0 AND ms.aw > 0 
                    THEN ROUND((ms.aw * 6 / ms.stempelzeit * 100)::numeric, 1)
                    ELSE NULL
                END as leistungsgrad,
                CASE 
                    WHEN ms.anwesenheit > 0 AND ms.stempelzeit > 0
                    THEN ROUND((ms.stempelzeit / ms.anwesenheit * 100)::numeric, 1)
                    ELSE NULL
                END as produktivitaet,
                CASE WHEN eh.leave_date IS NULL OR eh.leave_date > CURRENT_DATE THEN true ELSE false END as ist_aktiv
            FROM mechaniker_summen ms
            JOIN employees_history eh ON ms.employee_number = eh.employee_number AND eh.is_latest_record = true
            WHERE ms.employee_number BETWEEN 5000 AND 5999
              AND (ms.stempelzeit > 0 OR ms.aw > 0)
        """
        
        params = [datum_von, datum_bis, datum_von, datum_bis, datum_von, datum_bis]
        
        # Filter
        conditions = []
        if betrieb and betrieb != 'alle':
            conditions.append(f"eh.subsidiary = {int(betrieb)}")
        if not inkl_ehemalige:
            conditions.append("(eh.leave_date IS NULL OR eh.leave_date > CURRENT_DATE)")
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        # Sortierung
        sort_map = {
            'leistungsgrad': 'leistungsgrad DESC NULLS LAST',
            'stempelzeit': 'stempelzeit DESC',
            'aw': 'aw DESC',
            'auftraege': 'auftraege DESC'
        }
        query += f" ORDER BY {sort_map.get(sort_by, 'leistungsgrad DESC NULLS LAST')}"
        
        cur.execute(query, params)
        mechaniker = cur.fetchall()
        
        # Gesamt-KPIs
        gesamt_auftraege = sum(int(m['auftraege'] or 0) for m in mechaniker)
        gesamt_stempelzeit = sum(float(m['stempelzeit'] or 0) for m in mechaniker)
        gesamt_anwesenheit = sum(float(m['anwesenheit'] or 0) for m in mechaniker)
        gesamt_aw = sum(float(m['aw'] or 0) for m in mechaniker)
        gesamt_umsatz = sum(float(m['umsatz'] or 0) for m in mechaniker)
        
        gesamt_leistungsgrad = round(gesamt_aw * 6 / gesamt_stempelzeit * 100, 1) if gesamt_stempelzeit > 0 else 0
        gesamt_produktivitaet = round(gesamt_stempelzeit / gesamt_anwesenheit * 100, 1) if gesamt_anwesenheit > 0 else 0
        
        # Anzahl Arbeitstage
        cur.execute("""
            SELECT COUNT(DISTINCT DATE(start_time)) as count 
            FROM times 
            WHERE type = 2 AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
        """, [datum_von, datum_bis])
        anzahl_tage = cur.fetchone()['count'] or 0
        
        # Trend (letzte 14 Tage)
        cur.execute("""
            WITH stempel_trend AS (
                SELECT 
                    DATE(start_time) as datum,
                    SUM(minuten) as stempel_min
                FROM (
                    SELECT DISTINCT ON (employee_number, start_time, end_time)
                        start_time,
                        EXTRACT(EPOCH FROM (end_time - start_time)) / 60 as minuten
                    FROM times
                    WHERE type = 2 AND end_time IS NOT NULL
                      AND start_time >= CURRENT_DATE - 14
                ) dedup
                GROUP BY DATE(start_time)
            ),
            aw_trend AS (
                SELECT 
                    i.invoice_date as datum,
                    SUM(l.time_units) as aw
                FROM labours l
                JOIN invoices i ON l.invoice_number = i.invoice_number AND l.invoice_type = i.invoice_type
                WHERE i.invoice_date >= CURRENT_DATE - 14
                  AND l.is_invoiced = true AND l.mechanic_no IS NOT NULL
                GROUP BY i.invoice_date
            )
            SELECT 
                s.datum,
                ROUND((COALESCE(a.aw, 0) * 6 / NULLIF(s.stempel_min, 0) * 100)::numeric, 1) as leistungsgrad
            FROM stempel_trend s
            LEFT JOIN aw_trend a ON s.datum = a.datum
            ORDER BY s.datum
        """)
        trend = [{'datum': str(r['datum']), 'leistungsgrad': float(r['leistungsgrad'] or 0)} for r in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'source': 'LIVE',
            'zeitraum': {
                'von': str(datum_von),
                'bis': str(datum_bis),
                'label': zeitraum
            },
            'betrieb': betrieb,
            'mechaniker': [
                {
                    'mechaniker_nr': m['mechaniker_nr'],
                    'name': m['name'],
                    'betrieb': m['betrieb'],
                    'ist_aktiv': m['ist_aktiv'],
                    'tage': int(m['tage'] or 0),
                    'auftraege': int(m['auftraege'] or 0),
                    'stempelzeit': float(m['stempelzeit'] or 0),
                    'anwesenheit': float(m['anwesenheit'] or 0),
                    'aw': float(m['aw'] or 0),
                    'umsatz': float(m['umsatz'] or 0),
                    'leistungsgrad': float(m['leistungsgrad']) if m['leistungsgrad'] else None,
                    'produktivitaet': float(m['produktivitaet']) if m['produktivitaet'] else None
                } for m in mechaniker
            ],
            'anzahl_mechaniker': len(mechaniker),
            'anzahl_tage': anzahl_tage,
            'gesamt_auftraege': gesamt_auftraege,
            'gesamt_stempelzeit': gesamt_stempelzeit,
            'gesamt_anwesenheit': gesamt_anwesenheit,
            'gesamt_aw': round(gesamt_aw, 1),
            'gesamt_umsatz': round(gesamt_umsatz, 2),
            'gesamt_leistungsgrad': gesamt_leistungsgrad,
            'gesamt_produktivitaet': gesamt_produktivitaet,
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
    Holt alle offenen Werkstatt-Aufträge LIVE aus Locosoft
    
    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    - tage: Wie viele Tage zurück (default: 7)
    - nur_offen: true/false (default: true)
    """
    try:
        subsidiary = request.args.get('subsidiary', type=int)
        tage = request.args.get('tage', 7, type=int)
        nur_offen = request.args.get('nur_offen', 'true').lower() == 'true'
        
        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Basis-Query
        query = """
            SELECT 
                o.number as auftrag_nr,
                o.subsidiary as betrieb,
                o.order_date as auftrag_datum,
                o.order_taking_employee_no as serviceberater_nr,
                eh.name as serviceberater_name,
                o.vehicle_number,
                v.license_plate as kennzeichen,
                m.description as marke,
                COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name) as kunde,
                o.urgency as dringlichkeit,
                o.has_open_positions as ist_offen,
                o.has_closed_positions as hat_abgeschlossene,
                o.estimated_inbound_time as geplant_eingang,
                o.estimated_outbound_time as geplant_fertig
            FROM orders o
            LEFT JOIN employees_history eh ON o.order_taking_employee_no = eh.employee_number 
                AND eh.is_latest_record = true
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
            WHERE o.order_date >= CURRENT_DATE - INTERVAL '%s days'
        """
        
        params = [tage]
        
        if nur_offen:
            query += " AND o.has_open_positions = true"
        
        if subsidiary:
            query += " AND o.subsidiary = %s"
            params.append(subsidiary)
        
        query += " ORDER BY o.order_date DESC LIMIT 100"
        
        cur.execute(query, params)
        auftraege = cur.fetchall()
        
        # Für jeden Auftrag die Vorgabezeiten und Mechaniker holen
        result = []
        for auftrag in auftraege:
            # Labours (Arbeitspositionen) holen
            cur.execute("""
                SELECT 
                    COALESCE(SUM(time_units), 0) as total_aw,
                    STRING_AGG(DISTINCT CAST(mechanic_no AS TEXT), ', ') as mechaniker
                FROM labours 
                WHERE order_number = %s AND time_units > 0
            """, [auftrag['auftrag_nr']])
            
            labour_info = cur.fetchone()
            
            result.append({
                'auftrag_nr': auftrag['auftrag_nr'],
                'betrieb': auftrag['betrieb'],
                'betrieb_name': BETRIEB_NAMEN.get(auftrag['betrieb'], '?'),
                'datum': format_datetime(auftrag['auftrag_datum']),
                'uhrzeit': auftrag['auftrag_datum'].strftime('%H:%M') if auftrag['auftrag_datum'] else None,
                'serviceberater': auftrag['serviceberater_name'] or f"MA {auftrag['serviceberater_nr']}",
                'serviceberater_nr': auftrag['serviceberater_nr'],
                'kennzeichen': auftrag['kennzeichen'],
                'marke': auftrag['marke'],
                'kunde': auftrag['kunde'],
                'dringlichkeit': auftrag['dringlichkeit'],
                'ist_offen': auftrag['ist_offen'],
                'hat_abgeschlossene': auftrag['hat_abgeschlossene'],
                'geplant_fertig': format_datetime(auftrag['geplant_fertig']),
                'vorgabe_aw': float(labour_info['total_aw'] or 0),
                'mechaniker': labour_info['mechaniker']
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'filter': {
                'subsidiary': subsidiary,
                'tage': tage,
                'nur_offen': nur_offen
            },
            'anzahl': len(result),
            'auftraege': result
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
    Kombinierte Dashboard-Übersicht für LIVE-Monitoring
    """
    try:
        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Offene Aufträge pro Betrieb
        cur.execute("""
            SELECT 
                subsidiary as betrieb,
                COUNT(*) as anzahl_offen,
                COUNT(CASE WHEN urgency >= 4 THEN 1 END) as anzahl_dringend
            FROM orders 
            WHERE has_open_positions = true
              AND order_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY subsidiary
            ORDER BY subsidiary
        """)
        auftraege_pro_betrieb = cur.fetchall()
        
        # 2. Heutige Aufträge Statistik
        cur.execute("""
            SELECT 
                COUNT(*) as gesamt,
                COUNT(CASE WHEN has_open_positions = true AND has_closed_positions = false THEN 1 END) as offen,
                COUNT(CASE WHEN has_closed_positions = true THEN 1 END) as fertig,
                COUNT(CASE WHEN has_open_positions = true AND has_closed_positions = true THEN 1 END) as teilweise
            FROM orders 
            WHERE DATE(order_date) = CURRENT_DATE
        """)
        heute_stats = cur.fetchone()
        
        # 3. Aktive Mechaniker (mit zugeordneten offenen Aufträgen)
        cur.execute("""
            SELECT 
                l.mechanic_no,
                eh.name as name,
                eh.subsidiary as betrieb,
                COUNT(DISTINCT l.order_number) as anzahl_auftraege,
                COALESCE(SUM(l.time_units), 0) as summe_aw
            FROM labours l
            JOIN orders o ON l.order_number = o.number
            LEFT JOIN employees_history eh ON l.mechanic_no = eh.employee_number 
                AND eh.is_latest_record = true
            WHERE l.mechanic_no IS NOT NULL
              AND o.has_open_positions = true
              AND o.order_date >= CURRENT_DATE - INTERVAL '2 days'
            GROUP BY l.mechanic_no, eh.name, eh.subsidiary
            ORDER BY anzahl_auftraege DESC
        """)
        aktive_mechaniker = cur.fetchall()
        
        # 4. Serviceberater mit offenen Aufträgen
        cur.execute("""
            SELECT 
                o.order_taking_employee_no as sb_nr,
                eh.name as sb_name,
                COUNT(*) as anzahl_offen
            FROM orders o
            LEFT JOIN employees_history eh ON o.order_taking_employee_no = eh.employee_number 
                AND eh.is_latest_record = true
            WHERE o.has_open_positions = true
              AND o.order_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY o.order_taking_employee_no, eh.name
            ORDER BY anzahl_offen DESC
            LIMIT 10
        """)
        serviceberater = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'dashboard': {
                'auftraege_pro_betrieb': [
                    {
                        'betrieb': r['betrieb'],
                        'betrieb_name': BETRIEB_NAMEN.get(r['betrieb'], '?'),
                        'anzahl_offen': r['anzahl_offen'],
                        'anzahl_dringend': r['anzahl_dringend']
                    } for r in auftraege_pro_betrieb
                ],
                'heute': {
                    'gesamt': heute_stats['gesamt'],
                    'offen': heute_stats['offen'],
                    'fertig': heute_stats['fertig'],
                    'teilweise': heute_stats['teilweise']
                },
                'aktive_mechaniker': [
                    {
                        'mechaniker_nr': r['mechanic_no'],
                        'name': r['name'] or f"MA {r['mechanic_no']}",
                        'betrieb': r['betrieb'],
                        'anzahl_auftraege': r['anzahl_auftraege'],
                        'summe_aw': float(r['summe_aw'])
                    } for r in aktive_mechaniker
                ],
                'serviceberater': [
                    {
                        'sb_nr': r['sb_nr'],
                        'name': r['sb_name'] or f"MA {r['sb_nr']}",
                        'anzahl_offen': r['anzahl_offen']
                    } for r in serviceberater
                ]
            }
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
    LIVE Stempeluhr-Übersicht für Mechaniker (TAG 101 v2)
    
    DUAL-FILTER für Cross-Betrieb Arbeit:
    - Bei subsidiary=1 oder 3: Filter nach MITARBEITER-Betrieb
    - Bei subsidiary=2 (Hyundai): Filter nach AUFTRAGS-Betrieb
      (weil Hyundai keine eigenen Mechaniker hat - die Stellantis-MA machen das!)
    
    Neues Feature:
    - cross_betrieb Flag wenn MA aus anderem Betrieb an Auftrag arbeitet
    - auftrag_betrieb + auftrag_betrieb_name im Response
    
    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    """
    try:
        # TAG 109: Unterstütze komma-separierte subsidiary-Werte (z.B. "1,2" für Deggendorf)
        subsidiary_param = request.args.get('subsidiary', '')
        subsidiaries = []
        if subsidiary_param:
            for s in subsidiary_param.split(','):
                if s.strip().isdigit():
                    subsidiaries.append(int(s.strip()))
        # Einzelwert für Rückwärtskompatibilität, None bei mehreren
        subsidiary = subsidiaries[0] if len(subsidiaries) == 1 else None
        
        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # =====================================================================
        # 1. PRODUKTIVE STEMPELUNGEN (Auftrag > 31)
        # =====================================================================
        # NEU: Auch o.subsidiary (Auftrags-Betrieb) mit abfragen!
        produktiv_query = """
            WITH aktuelle_stempelungen AS (
                SELECT DISTINCT ON (t.employee_number)
                    t.employee_number,
                    t.order_number,
                    t.start_time,
                    -- TAG 112: Aktuelle Session + bereits abgeschlossene Zeit auf diesem Auftrag (Saldo)
                    EXTRACT(EPOCH FROM (NOW() - t.start_time))/60 
                    + COALESCE((
                        SELECT SUM(dur) FROM (
                            SELECT DISTINCT ON (start_time, end_time) duration_minutes as dur
                            FROM times t2 
                            WHERE t2.order_number = t.order_number 
                              AND t2.employee_number = t.employee_number
                              AND t2.end_time IS NOT NULL
                              AND t2.type = 2
                        ) dedup
                    ), 0) as laufzeit_min
                FROM times t
                WHERE t.end_time IS NULL
                  AND t.type = 2
                  AND t.order_number > 31
                  AND DATE(t.start_time) = CURRENT_DATE
                ORDER BY t.employee_number, t.start_time DESC
            )
            SELECT 
                a.employee_number,
                eh.name as mechaniker,
                eh.subsidiary as ma_betrieb,
                o.subsidiary as auftrag_betrieb,
                a.order_number,
                a.start_time,
                ROUND(a.laufzeit_min::numeric, 0) as laufzeit_min,
                COALESCE(l.vorgabe_aw, 0) as vorgabe_aw,
                COALESCE(l.vorgabe_aw * 6, 0) as vorgabe_min,
                l.auftrags_art,
                o.order_taking_employee_no as sb_nr,
                sb.name as sb_name,
                v.license_plate as kennzeichen,
                m.description as marke
            FROM aktuelle_stempelungen a
            LEFT JOIN employees_history eh ON a.employee_number = eh.employee_number 
                AND eh.is_latest_record = true
            LEFT JOIN orders o ON a.order_number = o.number
            LEFT JOIN employees_history sb ON o.order_taking_employee_no = sb.employee_number
                AND sb.is_latest_record = true
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN LATERAL (
                SELECT SUM(time_units) as vorgabe_aw,
                       MAX(labour_type) as auftrags_art  -- TAG 112: W=Werkstatt, etc.
                FROM labours 
                WHERE order_number = a.order_number 
                  AND mechanic_no = a.employee_number
            ) l ON true
            WHERE 1=1
        """
        
        # DUAL-FILTER LOGIK (TAG 109: subsidiaries als Liste)
        if subsidiaries:
            if len(subsidiaries) == 1 and subsidiaries[0] == 2:
                # Nur Hyundai: Filter nach AUFTRAGS-Betrieb
                produktiv_query += " AND o.subsidiary = %s"
                produktiv_query += " ORDER BY a.start_time"
                cur.execute(produktiv_query, [subsidiaries[0]])
            elif len(subsidiaries) == 1:
                # Einzelner Betrieb (1 oder 3): Filter nach MITARBEITER-Betrieb
                produktiv_query += " AND eh.subsidiary = %s"
                produktiv_query += " ORDER BY a.start_time"
                cur.execute(produktiv_query, [subsidiaries[0]])
            else:
                # Mehrere Betriebe (z.B. 1,2 = Deggendorf): Filter nach MITARBEITER-Betrieb
                placeholders = ','.join(['%s'] * len(subsidiaries))
                produktiv_query += f" AND eh.subsidiary IN ({placeholders})"
                produktiv_query += " ORDER BY a.start_time"
                cur.execute(produktiv_query, subsidiaries)
        else:
            produktiv_query += " ORDER BY a.start_time"
            cur.execute(produktiv_query)
        
        produktiv = cur.fetchall()
        
        # =====================================================================
        # 2. LEERLAUF-STEMPELUNGEN (Auftrag 31 = echter Leerlauf!)
        # =====================================================================
        leerlauf_query = """
            WITH leerlauf_stempelungen AS (
                SELECT DISTINCT ON (t.employee_number)
                    t.employee_number,
                    t.start_time,
                    EXTRACT(EPOCH FROM (NOW() - t.start_time))/60 as leerlauf_minuten
                FROM times t
                WHERE t.end_time IS NULL
                  AND t.type = 2
                  AND t.order_number = 31
                  AND DATE(t.start_time) = CURRENT_DATE
                ORDER BY t.employee_number, t.start_time DESC
            )
            SELECT 
                ls.employee_number,
                eh.name,
                eh.subsidiary,
                ls.start_time as leerlauf_seit,
                ROUND(ls.leerlauf_minuten::numeric, 0) as leerlauf_minuten
            FROM leerlauf_stempelungen ls
            JOIN employees_history eh ON ls.employee_number = eh.employee_number
                AND eh.is_latest_record = true
            WHERE eh.leave_date IS NULL
              AND eh.subsidiary > 0
        """
        
        # Leerlauf: Immer nach MA-Betrieb filtern (TAG 109: subsidiaries als Liste)
        if subsidiaries:
            if len(subsidiaries) == 1 and subsidiaries[0] == 2:
                # Nur Hyundai: Keine Leerlauf-Anzeige (haben keine eigenen MA)
                cur.execute("SELECT 1 WHERE false")
            elif len(subsidiaries) == 1:
                # Einzelner Betrieb (1 oder 3)
                leerlauf_query += " AND eh.subsidiary = %s"
                leerlauf_query += " ORDER BY ls.leerlauf_minuten DESC"
                cur.execute(leerlauf_query, [subsidiaries[0]])
            else:
                # Mehrere Betriebe (z.B. 1,2 = Deggendorf)
                placeholders = ','.join(['%s'] * len(subsidiaries))
                leerlauf_query += f" AND eh.subsidiary IN ({placeholders})"
                leerlauf_query += " ORDER BY ls.leerlauf_minuten DESC"
                cur.execute(leerlauf_query, subsidiaries)
        else:
            leerlauf_query += " ORDER BY eh.subsidiary, ls.leerlauf_minuten DESC"
            cur.execute(leerlauf_query)
        
        leerlauf_raw = cur.fetchall()
        
        # Ausnahmen filtern
        leerlauf = [r for r in leerlauf_raw if r['employee_number'] not in LEERLAUF_AUSNAHMEN]
        
        # Außerhalb Arbeitszeit = kein Leerlauf
        jetzt_zeit = datetime.now().time()
        ist_arbeitszeit = ARBEITSZEIT_START <= jetzt_zeit <= ARBEITSZEIT_ENDE
        ist_pausenzeit = PAUSE_START <= jetzt_zeit <= PAUSE_ENDE  # TAG 112: Mittagspause 12:00-13:00
        if not ist_arbeitszeit:
            leerlauf = []
        
        # =====================================================================
        # 3. ABWESENDE MECHANIKER
        # =====================================================================
        abwesend_query = """
            SELECT 
                ac.employee_number,
                eh.name,
                eh.subsidiary,
                ac.reason as grund
            FROM absence_calendar ac
            JOIN employees_history eh ON ac.employee_number = eh.employee_number
                AND eh.is_latest_record = true
            WHERE ac.date = CURRENT_DATE
              AND ac.employee_number BETWEEN 5000 AND 5999
              AND eh.leave_date IS NULL
              AND eh.subsidiary > 0
        """
        
        # Abwesend: Bei Hyundai leer (TAG 109: subsidiaries als Liste)
        if subsidiaries:
            if len(subsidiaries) == 1 and subsidiaries[0] == 2:
                # Nur Hyundai: Keine Abwesend-Anzeige
                cur.execute("SELECT 1 WHERE false")
            elif len(subsidiaries) == 1:
                # Einzelner Betrieb
                abwesend_query += " AND eh.subsidiary = %s"
                abwesend_query += " ORDER BY eh.name"
                cur.execute(abwesend_query, [subsidiaries[0]])
            else:
                # Mehrere Betriebe (z.B. 1,2 = Deggendorf)
                placeholders = ','.join(['%s'] * len(subsidiaries))
                abwesend_query += f" AND eh.subsidiary IN ({placeholders})"
                abwesend_query += " ORDER BY eh.name"
                cur.execute(abwesend_query, subsidiaries)
        else:
            abwesend_query += " ORDER BY eh.subsidiary, eh.name"
            cur.execute(abwesend_query)
        
        abwesend = cur.fetchall()
        
        # =====================================================================
        # 4. PAUSIERT / WARTET - TAG 112
        # Mechaniker die heute produktiv waren aber gerade keine offene Stempelung haben
        # =====================================================================
        pausiert_query = """
            WITH 
            -- MA die heute type=2 gestempelt haben (produktiv)
            heute_gearbeitet AS (
                SELECT DISTINCT employee_number
                FROM times
                WHERE type = 2
                  AND DATE(start_time) = CURRENT_DATE
                  AND order_number > 31
            ),
            -- MA die gerade eine offene Stempelung haben
            aktuell_aktiv AS (
                SELECT DISTINCT employee_number
                FROM times
                WHERE end_time IS NULL
                  AND DATE(start_time) = CURRENT_DATE
            ),
            -- MA die abwesend sind
            abwesend_heute AS (
                SELECT DISTINCT employee_number
                FROM absence_calendar
                WHERE date = CURRENT_DATE
            ),
            -- Letzte abgeschlossene Stempelung pro MA
            letzte_stempelung AS (
                SELECT DISTINCT ON (employee_number)
                    employee_number,
                    order_number as letzter_auftrag,
                    end_time as pausiert_seit
                FROM times
                WHERE type = 2
                  AND DATE(start_time) = CURRENT_DATE
                  AND end_time IS NOT NULL
                  AND order_number > 31
                ORDER BY employee_number, end_time DESC
            ),
            -- Tagesarbeit pro MA (dedupliziert)
            tagesarbeit AS (
                SELECT 
                    employee_number,
                    SUM(dur) as heute_min,
                    COUNT(DISTINCT auftrag) as heute_auftraege
                FROM (
                    SELECT DISTINCT ON (employee_number, start_time, end_time)
                        employee_number,
                        order_number as auftrag,
                        duration_minutes as dur
                    FROM times
                    WHERE type = 2
                      AND DATE(start_time) = CURRENT_DATE
                      AND end_time IS NOT NULL
                      AND order_number > 31
                ) dedup
                GROUP BY employee_number
            )
            SELECT 
                hg.employee_number,
                eh.name,
                eh.subsidiary,
                ls.letzter_auftrag,
                ls.pausiert_seit,
                COALESCE(ta.heute_min, 0) as heute_min,
                COALESCE(ta.heute_auftraege, 0) as heute_auftraege
            FROM heute_gearbeitet hg
            JOIN employees_history eh ON hg.employee_number = eh.employee_number AND eh.is_latest_record = true
            LEFT JOIN letzte_stempelung ls ON hg.employee_number = ls.employee_number
            LEFT JOIN tagesarbeit ta ON hg.employee_number = ta.employee_number
            WHERE hg.employee_number NOT IN (SELECT employee_number FROM aktuell_aktiv)
              AND hg.employee_number NOT IN (SELECT employee_number FROM abwesend_heute)
              AND eh.leave_date IS NULL
              AND eh.subsidiary > 0
        """
        
        # Filter nach Betrieb
        if subsidiaries:
            if len(subsidiaries) == 1 and subsidiaries[0] == 2:
                cur.execute("SELECT 1 WHERE false")
            elif len(subsidiaries) == 1:
                pausiert_query += " AND eh.subsidiary = %s ORDER BY ls.pausiert_seit DESC"
                cur.execute(pausiert_query, [subsidiaries[0]])
            else:
                placeholders = ','.join(['%s'] * len(subsidiaries))
                pausiert_query += f" AND eh.subsidiary IN ({placeholders}) ORDER BY ls.pausiert_seit DESC"
                cur.execute(pausiert_query, subsidiaries)
        else:
            pausiert_query += " ORDER BY eh.subsidiary, ls.pausiert_seit DESC"
            cur.execute(pausiert_query)
        
        pausiert = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # =====================================================================
        # 4. RESPONSE MIT CROSS-BETRIEB INFO
        # =====================================================================
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'ist_arbeitszeit': ist_arbeitszeit,
            'ist_pausenzeit': ist_pausenzeit,  # TAG 112
            'filter': {
                'subsidiary': subsidiary_param,  # Original-Parameter (z.B. "1,2")
                'subsidiaries': subsidiaries,    # Als Liste [1, 2]
                'filter_modus': 'deggendorf_gesamt' if set(subsidiaries) == {1, 2} else ('auftrags_betrieb' if subsidiaries == [2] else 'mitarbeiter_betrieb'),
                'hinweis': 'Deggendorf (Stellantis + Hyundai)' if set(subsidiaries) == {1, 2} else ('Hyundai hat keine eigenen Mechaniker' if subsidiaries == [2] else None)
            },
            'aktive_mechaniker': [
                {
                    'employee_number': r['employee_number'],
                    'name': r['mechaniker'] or f"MA {r['employee_number']}",
                    'betrieb': r['ma_betrieb'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['ma_betrieb'], '?'),
                    'auftrag_betrieb': r['auftrag_betrieb'],
                    'auftrag_betrieb_name': BETRIEB_NAMEN.get(r['auftrag_betrieb'], '?'),
                    # NEU: Flag wenn MA aus anderem Betrieb arbeitet
                    'cross_betrieb': r['ma_betrieb'] != r['auftrag_betrieb'],
                    'order_number': r['order_number'],
                    'serviceberater': r['sb_name'] or f"MA {r['sb_nr']}" if r['sb_nr'] else None,
                    'serviceberater_nr': r['sb_nr'],
                    'kennzeichen': r['kennzeichen'],
                    'marke': r['marke'],
                    'start_time': format_datetime(r['start_time']),
                    'start_uhrzeit': r['start_time'].strftime('%H:%M') if r['start_time'] else None,
                    'laufzeit_min': int(r['laufzeit_min'] or 0),  # TAG 112: SQL-Saldo verwenden
                    'vorgabe_aw': float(r['vorgabe_aw'] or 0),
                    'vorgabe_min': int(r['vorgabe_min'] or 0),
                    'auftrags_art': r.get('auftrags_art') or '-',  # TAG 112: W=Werkstatt, T=Teile, etc.
                    'fortschritt_prozent': int(
                        (r['laufzeit_min'] / (r['vorgabe_aw'] * 6) * 100)
                        if r['laufzeit_min'] and r['vorgabe_aw'] and r['vorgabe_aw'] > 0 
                        else 0
                    ),
                    'status': 'produktiv'
                } for r in produktiv
            ],
            'leerlauf_mechaniker': [
                {
                    'employee_number': r['employee_number'],
                    'name': r['name'] or f"MA {r['employee_number']}",
                    'betrieb': r['subsidiary'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], '?'),
                    'leerlauf_minuten': int(r['leerlauf_minuten']) if r['leerlauf_minuten'] else 0,
                    'leerlauf_seit': r['leerlauf_seit'].strftime('%H:%M') if r.get('leerlauf_seit') else None,
                    'status': 'leerlauf',
                    'ist_echt': True
                } for r in leerlauf
            ],
            'abwesend_mechaniker': [
                {
                    'employee_number': r['employee_number'],
                    'name': r['name'] or f"MA {r['employee_number']}",
                    'betrieb': r['subsidiary'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], '?'),
                    'grund': r['grund'],
                    'status': 'abwesend'
                } for r in abwesend
            ],
            # TAG 112: Neue Kategorie für Mechaniker die pausieren/warten
            'pausiert_mechaniker': [
                {
                    'employee_number': r['employee_number'],
                    'name': r['name'] or f"MA {r['employee_number']}",
                    'betrieb': r['subsidiary'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], '?'),
                    'letzter_auftrag': r['letzter_auftrag'],
                    'pausiert_seit': r['pausiert_seit'].strftime('%H:%M') if r.get('pausiert_seit') else None,
                    'heute_min': int(r['heute_min'] or 0),
                    'heute_auftraege': int(r['heute_auftraege'] or 0),
                    'status': 'pausiert'
                } for r in pausiert
            ],
            'summary': {
                'produktiv': len(produktiv),
                'leerlauf': len(leerlauf),
                'pausiert': len(pausiert),
                'abwesend': len(abwesend),
                'gesamt': len(produktiv) + len(leerlauf) + len(pausiert) + len(abwesend)
            }
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
    Tagesbericht zur Kontrolle: Stempelungen, Zuweisungen, Überschreitungen
    
    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    - datum: Datum im Format YYYY-MM-DD (default: heute)
    """
    try:
        subsidiary = request.args.get('subsidiary', type=int)
        datum_str = request.args.get('datum')
        
        if datum_str:
            datum = datetime.strptime(datum_str, '%Y-%m-%d').date()
        else:
            datum = datetime.now().date()
        
        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. STEMPELUNG OHNE VORGABE
        query1 = """
            WITH stempelungen AS (
                SELECT DISTINCT ON (employee_number)
                    employee_number, order_number, start_time,
                    -- TAG 112: Saldo = aktuelle Session + abgeschlossene Zeiten
                    EXTRACT(EPOCH FROM (NOW() - start_time))/60 
                    + COALESCE((
                        SELECT SUM(duration_minutes) 
                        FROM times t2 
                        WHERE t2.order_number = times.order_number 
                          AND t2.employee_number = times.employee_number
                          AND t2.end_time IS NOT NULL
                          AND t2.type = 2
                    ), 0) as laufzeit_min
                FROM times
                WHERE type = 2 AND DATE(start_time) = %s
                  AND end_time IS NULL
                ORDER BY employee_number, start_time DESC
            ),
            mechaniker_aw AS (
                SELECT order_number, mechanic_no, SUM(time_units) as zugewiesene_aw
                FROM labours
                WHERE mechanic_no IS NOT NULL
                GROUP BY order_number, mechanic_no
            )
            SELECT 
                s.employee_number,
                eh.name as mechaniker,
                eh.subsidiary,
                s.order_number,
                s.start_time,
                ROUND(s.laufzeit_min::numeric, 0) as gestempelt_min,
                COALESCE(m.zugewiesene_aw, 0) as zugewiesene_aw
            FROM stempelungen s
            JOIN employees_history eh ON s.employee_number = eh.employee_number AND eh.is_latest_record = true
            LEFT JOIN mechaniker_aw m ON s.order_number = m.order_number AND s.employee_number = m.mechanic_no
            WHERE COALESCE(m.zugewiesene_aw, 0) = 0
        """
        params1 = [datum]
        if subsidiary:
            query1 += " AND eh.subsidiary = %s"
            params1.append(subsidiary)
        query1 += " ORDER BY s.laufzeit_min DESC"
        
        cur.execute(query1, params1)
        ohne_vorgabe = cur.fetchall()
        
        # 2. MECHANIKER-ZUORDNUNG PRÜFEN
        query2 = """
            WITH stempelungen AS (
                SELECT DISTINCT ON (employee_number)
                    employee_number, order_number
                FROM times
                WHERE type = 2 AND DATE(start_time) = %s AND end_time IS NULL
                ORDER BY employee_number, start_time DESC
            ),
            auftrags_aw AS (
                SELECT order_number, mechanic_no, SUM(time_units) as aw
                FROM labours
                WHERE time_units > 0 AND mechanic_no IS NOT NULL
                GROUP BY order_number, mechanic_no
            )
            SELECT 
                s.order_number,
                s.employee_number as gestempelt_nr,
                eh1.name as gestempelt_name,
                eh1.subsidiary,
                a.mechanic_no as zugewiesen_nr,
                eh2.name as zugewiesen_name,
                a.aw as zugewiesene_aw
            FROM stempelungen s
            JOIN auftrags_aw a ON s.order_number = a.order_number AND s.employee_number != a.mechanic_no
            JOIN employees_history eh1 ON s.employee_number = eh1.employee_number AND eh1.is_latest_record = true
            JOIN employees_history eh2 ON a.mechanic_no = eh2.employee_number AND eh2.is_latest_record = true
            WHERE a.aw > 0
        """
        params2 = [datum]
        if subsidiary:
            query2 += " AND eh1.subsidiary = %s"
            params2.append(subsidiary)
        query2 += " ORDER BY a.aw DESC"
        
        cur.execute(query2, params2)
        falsche_zuweisung = cur.fetchall()
        
        # 3. AKTUELLE STEMPELUNGEN MIT VORGABE-CHECK
        query3 = """
            WITH aktive_stempelungen AS (
                SELECT DISTINCT ON (employee_number)
                    employee_number, order_number, start_time
                FROM times
                WHERE type = 2 
                  AND DATE(start_time) = %s 
                  AND end_time IS NULL
                ORDER BY employee_number, start_time DESC
            ),
            vorgaben AS (
                SELECT order_number, mechanic_no, SUM(time_units) as vorgabe_aw
                FROM labours
                WHERE mechanic_no IS NOT NULL AND time_units > 0
                GROUP BY order_number, mechanic_no
            )
            SELECT 
                s.employee_number,
                eh.name as mechaniker,
                eh.subsidiary,
                s.order_number,
                s.start_time,
                COALESCE(v.vorgabe_aw, 0) as vorgabe_aw
            FROM aktive_stempelungen s
            LEFT JOIN vorgaben v ON s.order_number = v.order_number AND s.employee_number = v.mechanic_no
            JOIN employees_history eh ON s.employee_number = eh.employee_number AND eh.is_latest_record = true
            WHERE 1=1
        """
        params3 = [datum]
        if subsidiary:
            query3 += " AND eh.subsidiary = %s"
            params3.append(subsidiary)
        query3 += " ORDER BY s.start_time"
        
        cur.execute(query3, params3)
        aktive_raw = cur.fetchall()
        
        # Netto-Laufzeit berechnen und Überschreitungen filtern
        ueberschritten = []
        alle_aktiv = []
        
        for r in aktive_raw:
            ist_min = berechne_netto_laufzeit(r['start_time']) if r['start_time'] else 0
            vorgabe_min = int(r['vorgabe_aw'] * 6) if r['vorgabe_aw'] else 0
            prozent = int(ist_min / vorgabe_min * 100) if vorgabe_min > 0 else 0
            
            eintrag = {
                'employee_number': r['employee_number'],
                'mechaniker': r['mechaniker'],
                'betrieb': r['subsidiary'],
                'order_number': r['order_number'],
                'start_uhrzeit': r['start_time'].strftime('%H:%M') if r['start_time'] else None,
                'ist_min': ist_min,
                'vorgabe_min': vorgabe_min,
                'vorgabe_aw': float(r['vorgabe_aw'] or 0),
                'prozent': prozent
            }
            
            alle_aktiv.append(eintrag)
            
            if prozent >= 100:
                ueberschritten.append(eintrag)
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'datum': str(datum),
            'filter': {'subsidiary': subsidiary},
            'ohne_vorgabe': [
                {
                    'employee_number': r['employee_number'],
                    'mechaniker': r['mechaniker'],
                    'betrieb': r['subsidiary'],
                    'order_number': r['order_number'],
                    'start_uhrzeit': r['start_time'].strftime('%H:%M') if r['start_time'] else None,
                    'gestempelt_min': int(r['gestempelt_min'] or 0),
                    'zugewiesene_aw': float(r['zugewiesene_aw'] or 0)
                } for r in ohne_vorgabe
            ],
            'falsche_zuweisung': [
                {
                    'order_number': r['order_number'],
                    'betrieb': r['subsidiary'],
                    'gestempelt_nr': r['gestempelt_nr'],
                    'gestempelt_name': r['gestempelt_name'],
                    'zugewiesen_nr': r['zugewiesen_nr'],
                    'zugewiesen_name': r['zugewiesen_name'],
                    'zugewiesene_aw': float(r['zugewiesene_aw'] or 0)
                } for r in falsche_zuweisung
            ],
            'ueberschritten': sorted(ueberschritten, key=lambda x: x['prozent'], reverse=True),
            'alle_aktiv': alle_aktiv,
            'summary': {
                'ohne_vorgabe': len(ohne_vorgabe),
                'falsche_zuweisung': len(falsche_zuweisung),
                'ueberschritten': len(ueberschritten),
                'aktiv_gesamt': len(alle_aktiv)
            }
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
            -- Labours: Vorgabe + Mechaniker + AW-Preis aus charge_types
            labour_summen AS (
                SELECT 
                    l.order_number,
                    SUM(l.time_units) as vorgabe_aw,
                    SUM(l.net_price_in_order) as vorgabe_eur,
                    STRING_AGG(DISTINCT eh.name, ', ') as mechaniker_namen,
                    -- Gewichteter AW-Preis aus charge_types (Verrechnungssatz)
                    CASE 
                        WHEN SUM(l.time_units) > 0 THEN
                            ROUND((SUM(l.time_units * COALESCE(ct.timeunit_rate, 0)) / SUM(l.time_units))::numeric, 2)
                        ELSE 0
                    END as aw_preis_db
                FROM labours l
                LEFT JOIN employees_history eh ON l.mechanic_no = eh.employee_number 
                    AND eh.is_latest_record = true
                LEFT JOIN charge_types ct ON l.charge_type = ct.type AND ct.subsidiary = 1
                WHERE l.order_number IN (SELECT order_number FROM heute_rechnungen)
                  AND l.mechanic_no IS NOT NULL
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
                ROUND(COALESCE(l.vorgabe_aw, 0)::numeric, 1) as vorgabe_aw,
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
        
        query += " ORDER BY (COALESCE(s.gestempelt_min, 0) / 6 - COALESCE(l.vorgabe_aw, 0)) DESC"
        
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
            
            auftraege.append({
                'order_number': r['order_number'],
                'invoice_number': r['invoice_number'],
                'invoice_type': r['invoice_type'],
                'betrieb': r['subsidiary'],
                'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], '?'),
                'rechnung_eur': rechnung_eur,
                'vorgabe_aw': vorgabe_aw,
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
    """
    try:
        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Auftrag-Kopfdaten
        cur.execute("""
            SELECT 
                o.number as auftrag_nr,
                o.subsidiary as betrieb,
                o.order_date,
                o.order_taking_employee_no as serviceberater_nr,
                eh.name as serviceberater_name,
                o.vehicle_number,
                v.license_plate as kennzeichen,
                v.vin,
                m.description as marke,
                mo.description as modell,
                v.mileage_km as km_stand,
                COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name) as kunde,
                cs.customer_number as kunden_nr,
                o.urgency,
                o.has_open_positions,
                o.has_closed_positions,
                o.estimated_inbound_time,
                o.estimated_outbound_time
            FROM orders o
            LEFT JOIN employees_history eh ON o.order_taking_employee_no = eh.employee_number 
                AND eh.is_latest_record = true
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN models mo ON v.make_number = mo.make_number AND v.model_code = mo.model_code
            LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
            WHERE o.number = %s
        """, [auftrag_nr])
        
        auftrag = cur.fetchone()
        
        if not auftrag:
            return jsonify({
                'success': False,
                'error': f'Auftrag {auftrag_nr} nicht gefunden'
            }), 404
        
        # Arbeitspositionen (Labours)
        cur.execute("""
            SELECT 
                l.order_position,
                l.mechanic_no,
                mech.name as mechaniker_name,
                l.time_units as vorgabe_aw,
                l.text_line as beschreibung,
                l.is_invoiced as abgerechnet,
                l.charge_type,
                l.labour_type
            FROM labours l
            LEFT JOIN employees_history mech ON l.mechanic_no = mech.employee_number 
                AND mech.is_latest_record = true
            WHERE l.order_number = %s
            ORDER BY l.order_position, l.order_position_line
        """, [auftrag_nr])
        
        positionen = cur.fetchall()
        
        # Teile
        cur.execute("""
            SELECT 
                p.order_position,
                p.part_number as teilenummer,
                p.text_line as bezeichnung,
                p.amount as menge,
                p.sum as betrag,
                p.is_invoiced as abgerechnet
            FROM parts p
            WHERE p.order_number = %s
            ORDER BY p.order_position
        """, [auftrag_nr])
        
        teile = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Summen berechnen
        total_aw = sum(float(p['vorgabe_aw'] or 0) for p in positionen)
        total_teile = sum(float(p['betrag'] or 0) for p in teile)
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'auftrag': {
                'auftrag_nr': auftrag['auftrag_nr'],
                'betrieb': auftrag['betrieb'],
                'betrieb_name': BETRIEB_NAMEN.get(auftrag['betrieb'], '?'),
                'datum': format_datetime(auftrag['order_date']),
                'serviceberater': auftrag['serviceberater_name'],
                'serviceberater_nr': auftrag['serviceberater_nr'],
                'fahrzeug': {
                    'kennzeichen': auftrag['kennzeichen'],
                    'vin': auftrag['vin'],
                    'marke': auftrag['marke'],
                    'modell': auftrag['modell'],
                    'km_stand': auftrag['km_stand']
                },
                'kunde': auftrag['kunde'],
                'kunden_nr': auftrag['kunden_nr'],
                'status': {
                    'ist_offen': auftrag['has_open_positions'],
                    'hat_abgeschlossene': auftrag['has_closed_positions'],
                    'dringlichkeit': auftrag['urgency']
                },
                'planung': {
                    'eingang': format_datetime(auftrag['estimated_inbound_time']),
                    'fertig': format_datetime(auftrag['estimated_outbound_time'])
                },
                'summen': {
                    'total_aw': total_aw,
                    'anzahl_positionen': len(positionen),
                    'teile_betrag': total_teile
                }
            },
            'positionen': [
                {
                    'position': p['order_position'],
                    'mechaniker_nr': p['mechanic_no'],
                    'mechaniker': p['mechaniker_name'] or (f"MA {p['mechanic_no']}" if p['mechanic_no'] else 'Nicht zugeordnet'),
                    'vorgabe_aw': float(p['vorgabe_aw'] or 0),
                    'beschreibung': p['beschreibung'],
                    'abgerechnet': p['abgerechnet'],
                    'typ': p['labour_type']
                } for p in positionen
            ],
            'teile': [
                {
                    'position': t['order_position'],
                    'teilenummer': t['teilenummer'],
                    'bezeichnung': t['bezeichnung'],
                    'menge': float(t['menge'] or 0),
                    'betrag': float(t['betrag'] or 0),
                    'abgerechnet': t['abgerechnet']
                } for t in teile
            ]
        })
        
    except Exception as e:
        logger.exception(f"Fehler beim Laden von Auftrag {auftrag_nr}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/kapazitaet', methods=['GET'])
def get_kapazitaetsplanung():
    """
    Kapazitätsplanung Werkstatt: Offene Arbeit vs. verfügbare Kapazität
    
    Berechnet:
    - Summe aller vorbereiteten/offenen Aufträge in AW
    - Anzahl anwesender Mechaniker (abzgl. Urlaub/Krank)
    - Verfügbare Tageskapazität in AW
    - Auslastungsgrad in Prozent
    
    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 3) - Hinweis: Betrieb 2 (Hyundai) hat keine eigene Werkstatt
    - tage: Wie viele Tage Aufträge berücksichtigen (default: 7)
    
    Hinweis zur Firmenstruktur:
    - Betrieb 1 = Deggendorf (Opel/Stellantis) - macht auch Hyundai-Werkstattarbeit
    - Betrieb 2 = Hyundai DEG - NUR Verkauf, keine eigenen Mechaniker
    - Betrieb 3 = Landau (Opel/Stellantis)
    """
    try:
        subsidiary = request.args.get('subsidiary', type=int)
        tage = request.args.get('tage', 7, type=int)
        
        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        heute = datetime.now().date()
        today_dow = datetime.now().weekday()  # 0=Montag, 4=Freitag
        
        # =====================================================================
        # 1. VERFÜGBARE MECHANIKER MIT ARBEITSZEITEN
        # =====================================================================
        # Fix: is_latest_record ist in Locosoft nicht gepflegt, daher DISTINCT ON
        
        mechaniker_query = """
            WITH aktuelle_arbeitszeiten AS (
                SELECT DISTINCT ON (employee_number, dayofweek)
                    employee_number,
                    dayofweek,
                    work_duration,
                    worktime_start,
                    worktime_end
                FROM employees_worktimes
                ORDER BY employee_number, dayofweek, validity_date DESC
            ),
            abwesende AS (
                SELECT employee_number, reason, type
                FROM absence_calendar
                WHERE date = CURRENT_DATE
            )
            SELECT 
                eh.employee_number,
                eh.name,
                eh.subsidiary,
                eh.mechanic_number,
                aw.work_duration,
                aw.worktime_start,
                aw.worktime_end,
                ab.reason as abwesenheit_grund,
                ab.type as abwesenheit_typ,
                CASE WHEN ab.employee_number IS NOT NULL THEN true ELSE false END as ist_abwesend
            FROM employees_history eh
            LEFT JOIN aktuelle_arbeitszeiten aw 
                ON eh.employee_number = aw.employee_number
                AND aw.dayofweek = %s
            LEFT JOIN abwesende ab ON eh.employee_number = ab.employee_number
            WHERE eh.is_latest_record = true
              AND eh.employee_number BETWEEN 5000 AND 5999
              AND eh.mechanic_number IS NOT NULL
              AND eh.subsidiary > 0
              AND (eh.leave_date IS NULL OR eh.leave_date > CURRENT_DATE)
        """
        
        params = [today_dow]
        
        if subsidiary:
            mechaniker_query += " AND eh.subsidiary = %s"
            params.append(subsidiary)
        
        mechaniker_query += " ORDER BY eh.subsidiary, eh.name"
        
        cur.execute(mechaniker_query, params)
        mechaniker_raw = cur.fetchall()
        
        # Mechaniker aufbereiten
        mechaniker = []
        total_stunden = 0
        total_stunden_verfuegbar = 0
        anwesend_count = 0
        abwesend_count = 0
        
        for m in mechaniker_raw:
            stunden = float(m['work_duration']) if m['work_duration'] else 8.0  # Fallback 8h
            total_stunden += stunden
            
            if not m['ist_abwesend']:
                total_stunden_verfuegbar += stunden
                anwesend_count += 1
            else:
                abwesend_count += 1
            
            mechaniker.append({
                'employee_number': m['employee_number'],
                'name': m['name'],
                'betrieb': m['subsidiary'],
                'betrieb_name': BETRIEB_NAMEN.get(m['subsidiary'], '?'),
                'arbeitszeit_h': stunden,
                'arbeitszeit_von': f"{int(m['worktime_start'] or 8):02d}:{int(((m['worktime_start'] or 8) % 1) * 60):02d}" if m['worktime_start'] else '08:00',
                'arbeitszeit_bis': f"{int(m['worktime_end'] or 16):02d}:{int(((m['worktime_end'] or 16) % 1) * 60):02d}" if m['worktime_end'] else '16:00',
                'ist_abwesend': m['ist_abwesend'],
                'abwesenheit_grund': m['abwesenheit_grund'] or m['abwesenheit_typ']
            })
        
        kapazitaet_aw = total_stunden_verfuegbar * 6  # 1h = 6 AW
        
        # =====================================================================
        # 2. OFFENE AUFTRÄGE MIT VORGABE-AW
        # =====================================================================
        
        auftraege_query = """
            SELECT 
                o.number as auftrag_nr,
                o.subsidiary as betrieb,
                o.estimated_inbound_time as bringen,
                o.estimated_outbound_time as abholen,
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
              AND o.order_date >= CURRENT_DATE - INTERVAL '%s days'
        """
        
        auftraege_params = [tage]
        
        if subsidiary:
            auftraege_query += " AND o.subsidiary = %s"
            auftraege_params.append(subsidiary)
        
        auftraege_query += """
            GROUP BY o.number, o.subsidiary, o.estimated_inbound_time, o.estimated_outbound_time,
                     o.urgency, v.license_plate, m.description, cs.family_name
            HAVING COALESCE(SUM(l.time_units), 0) > 0
            ORDER BY o.estimated_inbound_time NULLS LAST
        """
        
        cur.execute(auftraege_query, auftraege_params)
        auftraege_raw = cur.fetchall()
        
        # Aufträge nach Kategorie sortieren
        auftraege_heute = []
        auftraege_geplant = []
        auftraege_ohne_termin = []
        total_aw = 0
        total_aw_heute = 0
        
        for a in auftraege_raw:
            aw = float(a['vorgabe_aw'])
            total_aw += aw
            
            auftrag = {
                'auftrag_nr': a['auftrag_nr'],
                'betrieb': a['betrieb'],
                'betrieb_name': BETRIEB_NAMEN.get(a['betrieb'], '?'),
                'kennzeichen': a['kennzeichen'],
                'marke': a['marke'],
                'kunde': a['kunde'],
                'vorgabe_aw': aw,
                'anzahl_positionen': a['anzahl_positionen'],
                'bringen': a['bringen'].strftime('%d.%m. %H:%M') if a['bringen'] else None,
                'bringen_uhrzeit': a['bringen'].strftime('%H:%M') if a['bringen'] else None,
                'abholen': a['abholen'].strftime('%d.%m. %H:%M') if a['abholen'] else None,
                'dringend': a['urgency'] and a['urgency'] >= 4
            }
            
            if a['bringen'] and a['bringen'].date() == heute:
                auftraege_heute.append(auftrag)
                total_aw_heute += aw
            elif a['bringen']:
                auftraege_geplant.append(auftrag)
            else:
                auftraege_ohne_termin.append(auftrag)
        
        # =====================================================================
        # 3. KAPAZITÄT PRO BETRIEB
        # =====================================================================
        
        cur.execute("""
            WITH aktuelle_arbeitszeiten AS (
                SELECT DISTINCT ON (employee_number, dayofweek)
                    employee_number,
                    dayofweek,
                    work_duration
                FROM employees_worktimes
                ORDER BY employee_number, dayofweek, validity_date DESC
            ),
            abwesende AS (
                SELECT employee_number
                FROM absence_calendar
                WHERE date = CURRENT_DATE
            )
            SELECT 
                eh.subsidiary,
                COUNT(*) as anzahl_mechaniker,
                COUNT(*) FILTER (WHERE ab.employee_number IS NULL) as anwesend,
                COALESCE(SUM(COALESCE(aw.work_duration, 8)) FILTER (WHERE ab.employee_number IS NULL), 0) as stunden,
                COALESCE(SUM(COALESCE(aw.work_duration, 8)) FILTER (WHERE ab.employee_number IS NULL), 0) * 6 as aw
            FROM employees_history eh
            LEFT JOIN aktuelle_arbeitszeiten aw 
                ON eh.employee_number = aw.employee_number
                AND aw.dayofweek = %s
            LEFT JOIN abwesende ab ON eh.employee_number = ab.employee_number
            WHERE eh.is_latest_record = true
              AND eh.employee_number BETWEEN 5000 AND 5999
              AND eh.mechanic_number IS NOT NULL
              AND eh.subsidiary > 0
              AND (eh.leave_date IS NULL OR eh.leave_date > CURRENT_DATE)
            GROUP BY eh.subsidiary
            ORDER BY eh.subsidiary
        """, [today_dow])
        
        betriebe_raw = cur.fetchall()
        betriebe = [
            {
                'subsidiary': b['subsidiary'],
                'name': BETRIEB_NAMEN.get(b['subsidiary'], f"Betrieb {b['subsidiary']}"),
                'mechaniker_gesamt': b['anzahl_mechaniker'],
                'mechaniker_anwesend': b['anwesend'],
                'kapazitaet_h': float(b['stunden']),
                'kapazitaet_aw': float(b['aw'])
            } for b in betriebe_raw
        ]
        
        # =====================================================================
        # 4. AUSLASTUNG BERECHNEN
        # =====================================================================
        
        if kapazitaet_aw > 0:
            auslastung_gesamt = (total_aw / kapazitaet_aw) * 100
            auslastung_heute = (total_aw_heute / kapazitaet_aw) * 100
            tage_arbeit = total_aw / kapazitaet_aw
        else:
            auslastung_gesamt = 0
            auslastung_heute = 0
            tage_arbeit = 0
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'datum': str(heute),
            'wochentag': ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'][today_dow],
            'filter': {
                'subsidiary': subsidiary,
                'tage': tage
            },
            
            # Kapazität
            'kapazitaet': {
                'mechaniker_gesamt': len(mechaniker),
                'mechaniker_anwesend': anwesend_count,
                'mechaniker_abwesend': abwesend_count,
                'stunden_verfuegbar': total_stunden_verfuegbar,
                'aw_verfuegbar': kapazitaet_aw,
                'pro_betrieb': betriebe
            },
            
            # Offene Arbeit
            'arbeit': {
                'total_aw': round(total_aw, 1),
                'total_stunden': round(total_aw / 6, 1),
                'anzahl_auftraege': len(auftraege_raw),
                'heute_aw': round(total_aw_heute, 1),
                'heute_anzahl': len(auftraege_heute)
            },
            
            # Auslastung
            'auslastung': {
                'prozent_gesamt': round(auslastung_gesamt, 1),
                'prozent_heute': round(auslastung_heute, 1),
                'tage_arbeit': round(tage_arbeit, 1),
                'status': 'kritisch' if auslastung_gesamt > 150 else 'hoch' if auslastung_gesamt > 100 else 'normal' if auslastung_gesamt > 50 else 'niedrig'
            },
            
            # Details
            'mechaniker': mechaniker,
            'auftraege_heute': auftraege_heute,
            'auftraege_geplant': auftraege_geplant[:20],  # Max 20
            'auftraege_ohne_termin': auftraege_ohne_termin[:20]  # Max 20
        })
        
    except Exception as e:
        logger.exception("Fehler bei Kapazitätsplanung")
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
        import sqlite3
        from datetime import timedelta
        
        tage_vorschau = request.args.get('tage', 10, type=int)
        subsidiary = request.args.get('subsidiary', type=int)
        
        conn_loco = get_locosoft_connection()
        cur_loco = conn_loco.cursor(cursor_factory=RealDictCursor)
        
        # SQLite für Servicebox
        sqlite_path = '/opt/greiner-portal/data/greiner_controlling.db'
        conn_sqlite = sqlite3.connect(sqlite_path)
        conn_sqlite.row_factory = sqlite3.Row
        cur_sqlite = conn_sqlite.cursor()
        
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
        cur_sqlite.execute("""
            SELECT 
                b.bestellnummer,
                b.bestelldatum,
                b.lokale_nr,
                b.match_kunde_name as kunde,
                COUNT(p.id) as anzahl_positionen,
                SUM(p.summe_inkl_mwst) as gesamtwert,
                (SELECT COUNT(*) FROM teile_lieferscheine tl 
                 WHERE tl.servicebox_bestellnr = b.bestellnummer 
                   AND tl.locosoft_zugebucht = 1) as zugebucht_count,
                (SELECT COUNT(*) FROM teile_lieferscheine tl 
                 WHERE tl.servicebox_bestellnr = b.bestellnummer) as lieferschein_count
            FROM stellantis_bestellungen b
            LEFT JOIN stellantis_positionen p ON b.id = p.bestellung_id
            WHERE b.bestelldatum >= date('now', '-30 days')
            GROUP BY b.id
            HAVING zugebucht_count < anzahl_positionen OR lieferschein_count = 0
            ORDER BY b.bestelldatum DESC
            LIMIT 20
        """)
        
        offene_bestellungen_raw = cur_sqlite.fetchall()
        
        offene_servicebox = [{
            'bestellnummer': b['bestellnummer'],
            'bestelldatum': b['bestelldatum'],
            'lokale_nr': b['lokale_nr'],
            'kunde': b['kunde'],
            'anzahl_positionen': b['anzahl_positionen'],
            'gesamtwert': round(float(b['gesamtwert'] or 0), 2),
            'status': 'bestellt' if b['lieferschein_count'] == 0 else 'teilweise_geliefert',
            'zugebucht': b['zugebucht_count'] or 0,
            'geliefert': b['lieferschein_count'] or 0
        } for b in offene_bestellungen_raw]
        
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
        
        cur_loco.close()
        conn_loco.close()
        cur_sqlite.close()
        conn_sqlite.close()
        
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
        # =====================================================================
        query = """
            WITH aktive_stempelungen AS (
                SELECT DISTINCT ON (order_number)
                    order_number,
                    employee_number as aktiv_mechaniker_nr,
                    start_time as stempel_start,
                    -- TAG 112: Saldo = aktuelle Session + abgeschlossene Zeiten des MA auf diesem Auftrag
                    EXTRACT(EPOCH FROM (NOW() - start_time))/60 
                    + COALESCE((
                        SELECT SUM(duration_minutes) 
                        FROM times t2 
                        WHERE t2.order_number = times.order_number 
                          AND t2.employee_number = times.employee_number
                          AND t2.end_time IS NOT NULL
                          AND t2.type = 2
                    ), 0) as laufzeit_min
                FROM times
                WHERE end_time IS NULL
                  AND type = 2
                  AND DATE(start_time) = CURRENT_DATE
                ORDER BY order_number, start_time DESC
            ),
            stempel_summen AS (
                SELECT 
                    order_number,
                    SUM(EXTRACT(EPOCH FROM (COALESCE(end_time, NOW()) - start_time))/60) as gestempelt_min,
                    COUNT(DISTINCT employee_number) as anzahl_mechaniker
                FROM times
                WHERE type = 2
                  AND start_time >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY order_number
            )
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
                mech.name as mechaniker_name,
                ast.aktiv_mechaniker_nr,
                ast.stempel_start,
                ast.laufzeit_min as aktiv_laufzeit_min,
                COALESCE(ss.gestempelt_min, 0) / 6.0 as gestempelt_aw,
                COALESCE(ss.gestempelt_min, 0) as gestempelt_min
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
                    MAX(mechanic_no) as mechaniker_nr
                FROM labours 
                WHERE order_number = o.number AND time_units > 0
            ) l ON true
            LEFT JOIN employees_history mech ON l.mechaniker_nr = mech.employee_number 
                AND mech.is_latest_record = true
            LEFT JOIN aktive_stempelungen ast ON o.number = ast.order_number
            LEFT JOIN stempel_summen ss ON o.number = ss.order_number
            WHERE o.order_date >= CURRENT_DATE - INTERVAL '%s days'
        """
        
        params = [tage, tage]
        
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
        # 2. ML-VORHERSAGEN HINZUFÜGEN
        # =====================================================================
        ml_predictions = {}
        mechaniker_effizienz = {}
        
        if mit_ml:
            try:
                import pickle
                import pandas as pd
                import numpy as np
                
                MODEL_DIR = "/opt/greiner-portal/data/ml/models"
                
                # Modell laden - V2 mit bereinigten Trainingsdaten (TAG 98)
                model_path = f"{MODEL_DIR}/auftragsdauer_model_v2.pkl"
                encoder_path = f"{MODEL_DIR}/label_encoders_v2.pkl"
                
                # Fallback auf V1 falls V2 nicht existiert
                if not os.path.exists(model_path):
                    model_path = f"{MODEL_DIR}/auftragsdauer_model.pkl"
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
                                # Feature-Vektor erstellen
                                vorgabe_aw = float(auftrag['vorgabe_aw'])
                                mechaniker_nr = auftrag['mechaniker_nr'] or auftrag['aktiv_mechaniker_nr'] or 5008
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
                                else:
                                    wochentag, monat, start_stunde = 1, 6, 8
                                
                                # Encodieren
                                try:
                                    marke_encoded = encoders['marke'].transform([marke])[0]
                                except:
                                    marke_encoded = 0
                                
                                try:
                                    mechaniker_encoded = encoders['mechaniker'].transform([str(mechaniker_nr)])[0]
                                except:
                                    mechaniker_encoded = 0
                                
                                # Feature-Vektor
                                features = pd.DataFrame([[
                                    vorgabe_aw,
                                    mechaniker_encoded,
                                    betrieb,
                                    wochentag,
                                    monat,
                                    start_stunde,
                                    marke_encoded,
                                    fahrzeug_alter,
                                    km_stand
                                ]], columns=[
                                    'vorgabe_aw', 'mechaniker_encoded', 'betrieb', 'wochentag', 'monat',
                                    'start_stunde', 'marke_encoded', 'fahrzeug_alter_jahre', 'km_stand'
                                ])
                                
                                # Vorhersage
                                vorhersage_min = model.predict(features)[0]
                                vorhersage_aw = vorhersage_min / 10.0  # 1 AW = 10 min
                                
                                ml_predictions[auftrag['auftrag_nr']] = {
                                    'vorhersage_aw': round(vorhersage_aw, 1),
                                    'vorhersage_min': round(vorhersage_min, 0),
                                    'potenzial_aw': round(vorhersage_aw - vorgabe_aw, 1),
                                    'potenzial_prozent': round((vorhersage_aw - vorgabe_aw) / vorgabe_aw * 100, 1) if vorgabe_aw > 0 else 0
                                }
                                
                            except Exception as ml_err:
                                logger.debug(f"ML-Fehler für Auftrag {auftrag['auftrag_nr']}: {ml_err}")
                    
                    # Mechaniker-Effizienz aus Trainingsdaten
                    data_path = "/opt/greiner-portal/data/ml/auftraege_mit_zeiten_v2.csv"
                    if os.path.exists(data_path):
                        df = pd.read_csv(data_path)
                        eff = df.groupby('mechaniker_nr').agg({
                            'ist_dauer_min': 'mean',
                            'vorgabe_aw': 'mean'
                        }).reset_index()
                        eff['effizienz'] = (eff['vorgabe_aw'] * 10) / eff['ist_dauer_min'] * 100
                        for _, row in eff.iterrows():
                            mechaniker_effizienz[int(row['mechaniker_nr'])] = round(row['effizienz'], 1)
                    
            except Exception as e:
                logger.warning(f"ML-Integration fehlgeschlagen: {e}")
        
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
                
                # ML-Vorhersage
                'ml_vorhersage_aw': ml_vorhersage,
                'ml_potenzial_aw': ml_potenzial if ml_vorhersage else None,
                'ml_potenzial_prozent': ml.get('potenzial_prozent'),
                'ml_status': ml_status,
                'ml_status_icon': ml_status_icon,
                
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
