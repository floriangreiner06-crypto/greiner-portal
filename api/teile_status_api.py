#!/usr/bin/env python3
"""
TEILE-STATUS API - Übersicht fehlende Teile auf offenen Aufträgen
=================================================================
Zeigt welche Aufträge auf Teile warten und wann diese voraussichtlich
geliefert werden (basierend auf historischen Lieferzeiten).

Endpoints:
- GET /api/teile/status - Übersicht fehlende Teile
- GET /api/teile/auftrag/<nr> - Detail für einen Auftrag
- GET /api/teile/lieferanten - Lieferanten mit Ø Lieferzeiten
- GET /api/teile/kritisch - Kritische Aufträge (lange wartend, hoher Wert)

Author: Claude
Date: 2025-12-07 (TAG 100)
"""

import os
import sys
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
import logging
from psycopg2.extras import RealDictCursor

# Zentrale DB-Utilities (TAG117)
from api.db_utils import get_locosoft_connection, get_db as get_sqlite_connection

# Logging
logger = logging.getLogger(__name__)

# Blueprint
teile_status_bp = Blueprint('teile_status', __name__, url_prefix='/api/teile')


# Lieferanten-Lieferzeiten (aus Analyse TAG 100)
# Wird beim Start geladen und gecacht
LIEFERZEITEN_CACHE = {}


def load_lieferzeiten():
    """Lädt durchschnittliche Lieferzeiten pro Lieferant aus Portal-DB (PostgreSQL)"""
    global LIEFERZEITEN_CACHE
    try:
        conn = get_sqlite_connection()  # Jetzt eigentlich PostgreSQL via db_connection
        cur = conn.cursor()

        # TAG 139: PostgreSQL-kompatible Syntax
        cur.execute("""
            WITH auftrag_teile AS (
                SELECT p.part_number, o.order_date
                FROM loco_parts p
                JOIN loco_orders o ON p.order_number = o.number
                WHERE o.order_date >= CURRENT_DATE - INTERVAL '180 days'
            ),
            erste_lieferung AS (
                SELECT part_number, MIN(delivery_note_date) as lieferdatum, supplier_number
                FROM loco_parts_inbound_delivery_notes
                WHERE delivery_note_date >= CURRENT_DATE - INTERVAL '180 days'
                GROUP BY part_number
            )
            SELECT
                el.supplier_number,
                ROUND(AVG(EXTRACT(EPOCH FROM (el.lieferdatum - at.order_date)) / 86400.0)::numeric, 1) as avg_tage,
                COUNT(*) as anzahl
            FROM auftrag_teile at
            JOIN erste_lieferung el ON at.part_number = el.part_number
            WHERE el.lieferdatum >= at.order_date
            AND EXTRACT(EPOCH FROM (el.lieferdatum - at.order_date)) / 86400.0 BETWEEN 0 AND 30
            GROUP BY el.supplier_number
            HAVING COUNT(*) >= 10
        """)
        
        # TAG 139: Index-Zugriff statt Dict (kein RealDictCursor mehr)
        for row in cur.fetchall():
            LIEFERZEITEN_CACHE[row[0]] = {  # supplier_number
                'avg_tage': row[1],  # avg_tage
                'anzahl': row[2]     # anzahl
            }
        
        conn.close()
        logger.info(f"Lieferzeiten geladen: {len(LIEFERZEITEN_CACHE)} Lieferanten")
        
    except Exception as e:
        logger.warning(f"Konnte Lieferzeiten nicht laden: {e}")
        # Fallback-Werte
        LIEFERZEITEN_CACHE = {
            7702309: {'avg_tage': 9.2, 'anzahl': 4573},   # BTZ
            7000001: {'avg_tage': 9.6, 'anzahl': 2145},   # Hyundai
            7702435: {'avg_tage': 8.4, 'anzahl': 943},    # EFA
        }


# Beim Import laden
load_lieferzeiten()


BETRIEB_NAMEN = {
    1: 'Deggendorf',
    2: 'Hyundai DEG', 
    3: 'Landau'
}


# =============================================================================
# API ENDPOINTS
# =============================================================================

@teile_status_bp.route('/health', methods=['GET'])
def health_check():
    """Health-Check"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'lieferzeiten_cache': len(LIEFERZEITEN_CACHE)
    })


@teile_status_bp.route('/status', methods=['GET'])
def get_teile_status():
    """
    GET /api/teile/status
    
    Übersicht aller offenen Aufträge mit fehlenden Teilen.
    
    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    - min_wert: Mindest-Teilewert in Euro (default: 20)
    - min_tage: Mindest-Wartezeit in Tagen (default: 0)
    - limit: Max. Anzahl Ergebnisse (default: 100)
    - sort: tage_desc|wert_desc|teile_desc (default: tage_desc)
    """
    try:
        subsidiary = request.args.get('subsidiary', type=int)
        min_wert = request.args.get('min_wert', 20, type=float)
        min_tage = request.args.get('min_tage', 0, type=int)
        limit = request.args.get('limit', 100, type=int)
        sort = request.args.get('sort', 'tage_desc')
        
        conn = get_locosoft_connection()
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            WITH fehlende_teile AS (
                -- Teile die WIRKLICH fehlen:
                -- Nicht genug auf Lager für die benötigte Menge
                SELECT 
                    p.order_number,
                    p.part_number,
                    p.text_line as bezeichnung,
                    p.amount as menge,
                    p.sum as wert,
                    p.sum / NULLIF(p.amount, 0) as stueckpreis
                FROM parts p
                LEFT JOIN parts_stock ps ON p.part_number = ps.part_number
                WHERE p.amount > 0
                AND (ps.stock_level IS NULL OR ps.stock_level < p.amount)
            )
            SELECT 
                o.number as auftrag_nr,
                o.subsidiary as betrieb,
                o.order_date as auftragsdatum,
                EXTRACT(DAY FROM NOW() - o.order_date)::int as tage_offen,
                v.license_plate as kennzeichen,
                m.description as marke,
                COALESCE(cs.family_name || ' ' || COALESCE(cs.first_name, ''), cs.family_name, 'Unbekannt') as kunde,
                o.order_taking_employee_no as sb_nr,
                sb.name as serviceberater,
                COUNT(DISTINCT ft.part_number) as anzahl_fehlende_teile,
                ROUND(SUM(ft.wert)::numeric, 2) as teile_wert_gesamt,
                ROUND(AVG(ft.stueckpreis)::numeric, 2) as avg_stueckpreis,
                STRING_AGG(DISTINCT ft.part_number, ', ' ORDER BY ft.part_number) as teilenummern
            FROM orders o
            JOIN fehlende_teile ft ON o.number = ft.order_number
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
            LEFT JOIN employees_history sb ON o.order_taking_employee_no = sb.employee_number 
                AND sb.is_latest_record = true
            WHERE o.has_open_positions = true
            AND ft.stueckpreis >= %s
        """
        
        params = [min_wert]
        
        if subsidiary:
            query += " AND o.subsidiary = %s"
            params.append(subsidiary)
        
        query += """
            GROUP BY o.number, o.subsidiary, o.order_date, v.license_plate, m.description,
                     cs.family_name, cs.first_name, o.order_taking_employee_no, sb.name
            HAVING EXTRACT(DAY FROM NOW() - o.order_date) >= %s
        """
        params.append(min_tage)
        
        # Sortierung
        if sort == 'wert_desc':
            query += " ORDER BY teile_wert_gesamt DESC"
        elif sort == 'teile_desc':
            query += " ORDER BY anzahl_fehlende_teile DESC"
        else:  # tage_desc (default)
            query += " ORDER BY tage_offen DESC"
        
        query += " LIMIT %s"
        params.append(limit)
        
        cur.execute(query, params)
        auftraege = cur.fetchall()
        
        # Zusammenfassung - Teile mit zu wenig Lagerbestand
        cur.execute("""
            SELECT 
                COUNT(DISTINCT o.number) as auftraege_gesamt,
                COUNT(DISTINCT p.part_number) as teile_gesamt,
                ROUND(SUM(p.sum)::numeric, 2) as wert_gesamt
            FROM orders o
            JOIN parts p ON o.number = p.order_number
            LEFT JOIN parts_stock ps ON p.part_number = ps.part_number
            WHERE o.has_open_positions = true
            AND p.amount > 0
            AND (ps.stock_level IS NULL OR ps.stock_level < p.amount)
            AND p.sum / NULLIF(p.amount, 0) >= %s
        """, [min_wert])
        summary = cur.fetchone()
        
        cur.close()
        conn.close()
        
        # Kategorisierung
        kritisch = []      # > 30 Tage oder > 1000€
        warnung = []       # > 14 Tage oder > 500€
        normal = []        # Rest
        
        for a in auftraege:
            auftrag = {
                'auftrag_nr': a['auftrag_nr'],
                'betrieb': a['betrieb'],
                'betrieb_name': BETRIEB_NAMEN.get(a['betrieb'], '?'),
                'auftragsdatum': a['auftragsdatum'].strftime('%d.%m.%Y') if a['auftragsdatum'] else None,
                'tage_offen': a['tage_offen'],
                'kennzeichen': a['kennzeichen'],
                'marke': a['marke'],
                'kunde': a['kunde'],
                'serviceberater': a['serviceberater'],
                'anzahl_fehlende_teile': a['anzahl_fehlende_teile'],
                'teile_wert': float(a['teile_wert_gesamt'] or 0),
                'teilenummern': a['teilenummern']
            }
            
            # Kategorisierung
            if a['tage_offen'] > 30 or float(a['teile_wert_gesamt'] or 0) > 1000:
                auftrag['status'] = 'kritisch'
                auftrag['status_icon'] = '🔴'
                kritisch.append(auftrag)
            elif a['tage_offen'] > 14 or float(a['teile_wert_gesamt'] or 0) > 500:
                auftrag['status'] = 'warnung'
                auftrag['status_icon'] = '🟡'
                warnung.append(auftrag)
            else:
                auftrag['status'] = 'normal'
                auftrag['status_icon'] = '🟢'
                normal.append(auftrag)
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'filter': {
                'subsidiary': subsidiary,
                'min_wert': min_wert,
                'min_tage': min_tage,
                'sort': sort
            },
            'summary': {
                'auftraege_gesamt': summary['auftraege_gesamt'],
                'teile_gesamt': summary['teile_gesamt'],
                'wert_gesamt': float(summary['wert_gesamt'] or 0),
                'kritisch': len(kritisch),
                'warnung': len(warnung),
                'normal': len(normal)
            },
            'auftraege': {
                'kritisch': kritisch,
                'warnung': warnung,
                'normal': normal[:20]  # Nur Top 20 normale
            }
        })
        
    except Exception as e:
        logger.exception("Fehler bei Teile-Status")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@teile_status_bp.route('/auftrag/<int:auftrag_nr>', methods=['GET'])
def get_auftrag_teile(auftrag_nr):
    """
    GET /api/teile/auftrag/<nr>
    
    Detail-Ansicht: Alle fehlenden Teile für einen Auftrag
    mit erwarteter Lieferzeit.
    """
    try:
        conn = get_locosoft_connection()
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Auftragskopf
        cur.execute("""
            SELECT 
                o.number as auftrag_nr,
                o.subsidiary as betrieb,
                o.order_date,
                v.license_plate as kennzeichen,
                m.description as marke,
                mo.description as modell,
                COALESCE(cs.family_name || ' ' || COALESCE(cs.first_name, ''), cs.family_name) as kunde,
                sb.name as serviceberater
            FROM orders o
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN models mo ON v.make_number = mo.make_number AND v.model_code = mo.model_code
            LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
            LEFT JOIN employees_history sb ON o.order_taking_employee_no = sb.employee_number 
                AND sb.is_latest_record = true
            WHERE o.number = %s
        """, [auftrag_nr])
        
        auftrag = cur.fetchone()
        if not auftrag:
            return jsonify({'success': False, 'error': 'Auftrag nicht gefunden'}), 404
        
        # Fehlende Teile - MIT echtem Lagerbestand-Check
        # Teile sind "fehlend" wenn: Nicht genug auf Lager
        cur.execute("""
            SELECT 
                p.part_number,
                p.text_line as bezeichnung,
                p.amount as menge,
                ROUND(p.sum::numeric, 2) as wert,
                ROUND((p.sum / NULLIF(p.amount, 0))::numeric, 2) as stueckpreis,
                COALESCE(ps.stock_level, 0) as lagerbestand,
                p.parts_type
            FROM parts p
            LEFT JOIN parts_stock ps ON p.part_number = ps.part_number
            WHERE p.order_number = %s
            AND p.amount > 0
            AND (ps.stock_level IS NULL OR ps.stock_level < p.amount)
            ORDER BY p.sum DESC
        """, [auftrag_nr])
        
        teile = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Lieferanten und erwartete Lieferzeit ermitteln (aus SQLite)
        teile_mit_prognose = []
        conn_sqlite = get_sqlite_connection()
        cur_sqlite = conn_sqlite.cursor()
        
        for teil in teile:
            teil_dict = {
                'part_number': teil['part_number'],
                'bezeichnung': teil['bezeichnung'],
                'menge': float(teil['menge'] or 0),
                'wert': float(teil['wert'] or 0),
                'stueckpreis': float(teil['stueckpreis'] or 0),
                'lagerbestand': float(teil['lagerbestand'] or 0)
            }
            
            # Lieferant aus letzter Lieferung ermitteln
            cur_sqlite.execute("""
                SELECT supplier_number, MAX(delivery_note_date) as letzte_lieferung
                FROM loco_parts_inbound_delivery_notes
                WHERE part_number = %s
                GROUP BY supplier_number
                ORDER BY letzte_lieferung DESC
                LIMIT 1
            """, [teil['part_number']])
            
            lieferant = cur_sqlite.fetchone()
            if lieferant:
                supplier_nr = lieferant['supplier_number']
                teil_dict['lieferant_nr'] = supplier_nr
                
                # Lieferanten-Name
                cur_sqlite.execute("""
                    SELECT family_name FROM loco_customers_suppliers
                    WHERE customer_number = %s
                """, [supplier_nr])
                name_row = cur_sqlite.fetchone()
                teil_dict['lieferant_name'] = name_row['family_name'] if name_row else f"Lieferant {supplier_nr}"
                
                # Erwartete Lieferzeit
                if supplier_nr in LIEFERZEITEN_CACHE:
                    avg_tage = LIEFERZEITEN_CACHE[supplier_nr]['avg_tage']
                    teil_dict['lieferzeit_tage'] = avg_tage
                    teil_dict['lieferzeit_prognose'] = (datetime.now() + timedelta(days=avg_tage)).strftime('%d.%m.%Y')
                else:
                    teil_dict['lieferzeit_tage'] = 10  # Default
                    teil_dict['lieferzeit_prognose'] = (datetime.now() + timedelta(days=10)).strftime('%d.%m.%Y')
            else:
                teil_dict['lieferant_nr'] = None
                teil_dict['lieferant_name'] = 'Unbekannt'
                teil_dict['lieferzeit_tage'] = None
                teil_dict['lieferzeit_prognose'] = None
            
            teile_mit_prognose.append(teil_dict)
        
        conn_sqlite.close()
        
        # Früheste mögliche Fertigstellung
        max_lieferzeit = max((t['lieferzeit_tage'] or 0) for t in teile_mit_prognose) if teile_mit_prognose else 0
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'auftrag': {
                'auftrag_nr': auftrag['auftrag_nr'],
                'betrieb': auftrag['betrieb'],
                'betrieb_name': BETRIEB_NAMEN.get(auftrag['betrieb'], '?'),
                'auftragsdatum': auftrag['order_date'].strftime('%d.%m.%Y') if auftrag['order_date'] else None,
                'kennzeichen': auftrag['kennzeichen'],
                'marke': auftrag['marke'],
                'modell': auftrag['modell'],
                'kunde': auftrag['kunde'],
                'serviceberater': auftrag['serviceberater']
            },
            'fehlende_teile': teile_mit_prognose,
            'anzahl_fehlend': len(teile_mit_prognose),
            'wert_gesamt': sum(t['wert'] for t in teile_mit_prognose),
            'frueheste_fertigstellung': {
                'tage': max_lieferzeit,
                'datum': (datetime.now() + timedelta(days=max_lieferzeit)).strftime('%d.%m.%Y') if max_lieferzeit else None
            }
        })
        
    except Exception as e:
        logger.exception(f"Fehler bei Auftrag {auftrag_nr}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@teile_status_bp.route('/lieferanten', methods=['GET'])
def get_lieferanten_stats():
    """
    GET /api/teile/lieferanten
    
    Lieferanten-Übersicht mit durchschnittlichen Lieferzeiten.
    """
    try:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        
        # TAG 139: PostgreSQL-kompatible Syntax
        cur.execute("""
            WITH auftrag_teile AS (
                SELECT p.part_number, o.order_date
                FROM loco_parts p
                JOIN loco_orders o ON p.order_number = o.number
                WHERE o.order_date >= CURRENT_DATE - INTERVAL '180 days'
            ),
            erste_lieferung AS (
                SELECT part_number, MIN(delivery_note_date) as lieferdatum, supplier_number
                FROM loco_parts_inbound_delivery_notes
                WHERE delivery_note_date >= CURRENT_DATE - INTERVAL '180 days'
                GROUP BY part_number
            ),
            stats AS (
                SELECT
                    el.supplier_number,
                    ROUND(AVG(EXTRACT(EPOCH FROM (el.lieferdatum - at.order_date)) / 86400.0)::numeric, 1) as avg_tage,
                    MIN(EXTRACT(EPOCH FROM (el.lieferdatum - at.order_date)) / 86400.0) as min_tage,
                    MAX(EXTRACT(EPOCH FROM (el.lieferdatum - at.order_date)) / 86400.0) as max_tage,
                    COUNT(*) as anzahl
                FROM auftrag_teile at
                JOIN erste_lieferung el ON at.part_number = el.part_number
                WHERE el.lieferdatum >= at.order_date
                AND EXTRACT(EPOCH FROM (el.lieferdatum - at.order_date)) / 86400.0 BETWEEN 0 AND 30
                GROUP BY el.supplier_number
                HAVING COUNT(*) >= 10
            )
            SELECT 
                s.supplier_number,
                COALESCE(cs.family_name, 'Unbekannt') as name,
                s.avg_tage,
                s.min_tage,
                s.max_tage,
                s.anzahl,
                CASE 
                    WHEN s.avg_tage <= 5 THEN 'express'
                    WHEN s.avg_tage <= 8 THEN 'schnell'
                    WHEN s.avg_tage <= 12 THEN 'normal'
                    ELSE 'langsam'
                END as kategorie
            FROM stats s
            LEFT JOIN loco_customers_suppliers cs ON s.supplier_number = cs.customer_number
            ORDER BY s.anzahl DESC
        """)
        
        lieferanten = []
        for row in cur.fetchall():
            lieferanten.append({
                'supplier_number': row[0],
                'name': row[1],
                'avg_tage': row[2],
                'min_tage': int(row[3]) if row[3] else 0,
                'max_tage': int(row[4]) if row[4] else 0,
                'anzahl_lieferungen': row[5],
                'kategorie': row[6],
                'kategorie_icon': {
                    'express': '🟢',
                    'schnell': '🟢', 
                    'normal': '🟡',
                    'langsam': '🔴'
                }.get(row[6], '⚪')
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'lieferanten': lieferanten,
            'anzahl': len(lieferanten)
        })
        
    except Exception as e:
        logger.exception("Fehler bei Lieferanten-Stats")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@teile_status_bp.route('/kritisch', methods=['GET'])
def get_kritische_auftraege():
    """
    GET /api/teile/kritisch
    
    Nur kritische Aufträge: > 30 Tage wartend ODER > 1000€ Teilewert
    Für schnellen Überblick auf Dashboard.
    """
    try:
        subsidiary = request.args.get('subsidiary', type=int)
        
        conn = get_locosoft_connection()
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            WITH fehlende_teile AS (
                -- Kritische: Nur echte Fehlteile (nicht genug auf Lager)
                SELECT 
                    p.order_number,
                    COUNT(DISTINCT p.part_number) as anzahl_teile,
                    SUM(p.sum) as wert
                FROM parts p
                LEFT JOIN parts_stock ps ON p.part_number = ps.part_number
                WHERE p.amount > 0
                AND (ps.stock_level IS NULL OR ps.stock_level < p.amount)
                AND p.sum / NULLIF(p.amount, 0) >= 20
                GROUP BY p.order_number
            )
            SELECT 
                o.number as auftrag_nr,
                o.subsidiary as betrieb,
                o.order_date,
                EXTRACT(DAY FROM NOW() - o.order_date)::int as tage_offen,
                v.license_plate as kennzeichen,
                m.description as marke,
                COALESCE(cs.family_name, 'Unbekannt') as kunde,
                ft.anzahl_teile,
                ROUND(ft.wert::numeric, 2) as teile_wert
            FROM orders o
            JOIN fehlende_teile ft ON o.number = ft.order_number
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
            WHERE o.has_open_positions = true
            AND (
                EXTRACT(DAY FROM NOW() - o.order_date) > 30
                OR ft.wert > 1000
            )
        """
        
        params = []
        if subsidiary:
            query += " AND o.subsidiary = %s"
            params.append(subsidiary)
        
        query += " ORDER BY tage_offen DESC LIMIT 50"
        
        cur.execute(query, params)
        auftraege = cur.fetchall()
        
        cur.close()
        conn.close()
        
        result = []
        for a in auftraege:
            result.append({
                'auftrag_nr': a['auftrag_nr'],
                'betrieb': a['betrieb'],
                'betrieb_name': BETRIEB_NAMEN.get(a['betrieb'], '?'),
                'auftragsdatum': a['order_date'].strftime('%d.%m.%Y') if a['order_date'] else None,
                'tage_offen': a['tage_offen'],
                'kennzeichen': a['kennzeichen'],
                'marke': a['marke'],
                'kunde': a['kunde'],
                'anzahl_teile': a['anzahl_teile'],
                'teile_wert': float(a['teile_wert'] or 0)
            })
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'anzahl_kritisch': len(result),
            'auftraege': result
        })
        
    except Exception as e:
        logger.exception("Fehler bei kritischen Aufträgen")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@teile_status_bp.route('/reload-cache', methods=['POST'])
def reload_lieferzeiten_cache():
    """Lieferzeiten-Cache neu laden"""
    try:
        load_lieferzeiten()
        return jsonify({
            'success': True,
            'message': f'Cache neu geladen: {len(LIEFERZEITEN_CACHE)} Lieferanten'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
