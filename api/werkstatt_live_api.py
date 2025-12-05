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
    LIVE Stempeluhr-Übersicht für Mechaniker
    Zeigt wer gerade an welchem Auftrag arbeitet mit Fortschritt.
    
    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    """
    try:
        subsidiary = request.args.get('subsidiary', type=int)
        
        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Aktive Stempelungen (dedupliziert pro Mechaniker)
        # INKL. Serviceberater des Auftrags
        query = """
            WITH aktuelle_stempelungen AS (
                SELECT DISTINCT ON (t.employee_number)
                    t.employee_number,
                    t.order_number,
                    t.start_time,
                    EXTRACT(EPOCH FROM (NOW() - t.start_time))/60 as laufzeit_min
                FROM times t
                WHERE t.end_time IS NULL
                  AND t.type = 2
                  AND DATE(t.start_time) = CURRENT_DATE
                ORDER BY t.employee_number, t.start_time DESC
            )
            SELECT 
                a.employee_number,
                eh.name as mechaniker,
                eh.subsidiary as betrieb,
                a.order_number,
                a.start_time,
                ROUND(a.laufzeit_min::numeric, 0) as laufzeit_min,
                COALESCE(l.vorgabe_aw, 0) as vorgabe_aw,
                COALESCE(l.vorgabe_aw * 6, 0) as vorgabe_min,
                CASE 
                    WHEN COALESCE(l.vorgabe_aw, 0) = 0 THEN 0
                    ELSE ROUND((a.laufzeit_min / (l.vorgabe_aw * 6) * 100)::numeric, 0)
                END as fortschritt_prozent,
                o.order_date,
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
                SELECT SUM(time_units) as vorgabe_aw
                FROM labours 
                WHERE order_number = a.order_number 
                  AND mechanic_no = a.employee_number
            ) l ON true
        """
        
        if subsidiary:
            query += " WHERE eh.subsidiary = %s"
            query += " ORDER BY a.start_time"
            cur.execute(query, [subsidiary])
        else:
            query += " ORDER BY a.start_time"
            cur.execute(query)
        
        aktive = cur.fetchall()
        
        # Mechaniker ohne aktive Stempelung (Leerlauf)
        # NUR aktive Mitarbeiter (leave_date IS NULL) UND subsidiary > 0 (echte Mechaniker)
        # MIT Leerlauf-Dauer (seit letzter Abstempelung)
        leerlauf_query = """
            WITH aktive_stempelungen AS (
                SELECT DISTINCT employee_number
                FROM times
                WHERE end_time IS NULL
                  AND type = 2
                  AND DATE(start_time) = CURRENT_DATE
            ),
            heutige_abwesenheiten AS (
                SELECT DISTINCT employee_number
                FROM absence_calendar
                WHERE date = CURRENT_DATE
            ),
            aktive_mechaniker AS (
                SELECT DISTINCT employee_number, name, subsidiary
                FROM employees_history
                WHERE is_latest_record = true
                  AND employee_number BETWEEN 5000 AND 5999
                  AND leave_date IS NULL
                  AND subsidiary > 0
            ),
            letzte_abstempelung AS (
                SELECT DISTINCT ON (employee_number)
                    employee_number,
                    end_time,
                    EXTRACT(EPOCH FROM (NOW() - end_time))/60 as leerlauf_minuten
                FROM times
                WHERE type = 2
                  AND DATE(start_time) = CURRENT_DATE
                  AND end_time IS NOT NULL
                ORDER BY employee_number, end_time DESC
            )
            SELECT 
                am.employee_number, 
                am.name, 
                am.subsidiary,
                la.end_time as letzte_abstempelung,
                COALESCE(ROUND(la.leerlauf_minuten::numeric, 0), -1) as leerlauf_minuten
            FROM aktive_mechaniker am
            LEFT JOIN aktive_stempelungen ast ON am.employee_number = ast.employee_number
            LEFT JOIN heutige_abwesenheiten ha ON am.employee_number = ha.employee_number
            LEFT JOIN letzte_abstempelung la ON am.employee_number = la.employee_number
            WHERE ast.employee_number IS NULL
              AND ha.employee_number IS NULL
        """
        
        if subsidiary:
            leerlauf_query += " AND am.subsidiary = %s"
            leerlauf_query += " ORDER BY am.name"
            cur.execute(leerlauf_query, [subsidiary])
        else:
            leerlauf_query += " ORDER BY am.subsidiary, am.name"
            cur.execute(leerlauf_query)
        
        leerlauf = cur.fetchall()
        
        # Azubis und nicht-produktive MA aus Leerlauf entfernen
        leerlauf = [r for r in leerlauf if r['employee_number'] not in LEERLAUF_AUSNAHMEN]
        
        # Abwesende Mechaniker heute
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
        
        if subsidiary:
            abwesend_query += " AND eh.subsidiary = %s"
            abwesend_query += " ORDER BY eh.name"
            cur.execute(abwesend_query, [subsidiary])
        else:
            abwesend_query += " ORDER BY eh.subsidiary, eh.name"
            cur.execute(abwesend_query)
        
        abwesend = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'filter': {'subsidiary': subsidiary},
            'aktive_mechaniker': [
                {
                    'employee_number': r['employee_number'],
                    'name': r['mechaniker'] or f"MA {r['employee_number']}",
                    'betrieb': r['betrieb'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['betrieb'], '?'),
                    'order_number': r['order_number'],
                    'serviceberater': r['sb_name'] or f"MA {r['sb_nr']}" if r['sb_nr'] else None,
                    'serviceberater_nr': r['sb_nr'],
                    'kennzeichen': r['kennzeichen'],
                    'marke': r['marke'],
                    'start_time': format_datetime(r['start_time']),
                    'start_uhrzeit': r['start_time'].strftime('%H:%M') if r['start_time'] else None,
                    # Netto-Laufzeit (Pause abgezogen)
                    'laufzeit_min': berechne_netto_laufzeit(r['start_time']) if r['start_time'] else 0,
                    'vorgabe_aw': float(r['vorgabe_aw'] or 0),
                    'vorgabe_min': int(r['vorgabe_min'] or 0),
                    # Fortschritt mit Netto-Laufzeit berechnen
                    'fortschritt_prozent': int(
                        (berechne_netto_laufzeit(r['start_time']) / (r['vorgabe_aw'] * 6) * 100)
                        if r['start_time'] and r['vorgabe_aw'] and r['vorgabe_aw'] > 0 
                        else 0
                    )
                } for r in aktive
            ],
            'leerlauf_mechaniker': [
                {
                    'employee_number': r['employee_number'],
                    'name': r['name'] or f"MA {r['employee_number']}",
                    'betrieb': r['subsidiary'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], '?'),
                    'leerlauf_minuten': int(r['leerlauf_minuten']) if r['leerlauf_minuten'] else -1,
                    'letzte_abstempelung': r['letzte_abstempelung'].strftime('%H:%M') if r.get('letzte_abstempelung') else None,
                    'nie_gestempelt': r['leerlauf_minuten'] == -1 or r['leerlauf_minuten'] is None
                } for r in leerlauf
            ],
            'abwesend_mechaniker': [
                {
                    'employee_number': r['employee_number'],
                    'name': r['name'] or f"MA {r['employee_number']}",
                    'betrieb': r['subsidiary'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], '?'),
                    'grund': r['grund']
                } for r in abwesend
            ],
            'summary': {
                'aktiv': len(aktive),
                'leerlauf': len(leerlauf),
                'abwesend': len(abwesend),
                'gesamt': len(aktive) + len(leerlauf) + len(abwesend)
            }
        })
        
    except Exception as e:
        logger.exception("Fehler beim Laden der Stempeluhr")
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
