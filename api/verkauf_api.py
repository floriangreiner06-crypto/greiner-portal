"""
Verkauf REST API
Auftragseingang und Auslieferungen nach Verkäufern und Fahrzeugart
"""

from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime, date
from typing import Dict, List

# Blueprint erstellen
verkauf_api = Blueprint('verkauf_api', __name__, url_prefix='/api/verkauf')

def get_db():
    """Datenbank-Verbindung"""
    conn = sqlite3.connect('/opt/greiner-portal/data/greiner_controlling.db')
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================================
# AUFTRAGSEINGANG (bestehend)
# ============================================================================

@verkauf_api.route('/auftragseingang', methods=['GET'])
def get_auftragseingang():
    """
    GET /api/verkauf/auftragseingang?month=11&year=2025

    Liefert Auftragseingang nach Verkäufern
    - heute: Aufträge vom aktuellen Tag
    - periode: Kumuliert für gewählten Monat
    """
    try:
        # Parameter
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)

        conn = get_db()
        cursor = conn.cursor()

        # 1. Aufträge HEUTE
        cursor.execute("""
            SELECT
                s.salesman_number,
                COALESCE(e.first_name || ' ' || e.last_name, 'Verkäufer #' || s.salesman_number || ' (nicht in LocoSoft)') as verkaufer_name,
                CASE
                    WHEN s.dealer_vehicle_type IN ('N', 'V') THEN 'NW'
                    WHEN s.dealer_vehicle_type IN ('D', 'G', 'T') THEN 'GW'
                    ELSE 'Sonstige'
                END as fahrzeugart,
                COUNT(*) as anzahl
            FROM sales s
            LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
            WHERE DATE(s.out_sales_contract_date) = DATE('now')
              AND s.salesman_number IS NOT NULL
            GROUP BY s.salesman_number, verkaufer_name, fahrzeugart
        """)
        heute_raw = cursor.fetchall()

        # 2. Aufträge PERIODE (ganzer Monat)
        cursor.execute("""
            SELECT
                s.salesman_number,
                COALESCE(e.first_name || ' ' || e.last_name, 'Verkäufer #' || s.salesman_number || ' (nicht in LocoSoft)') as verkaufer_name,
                CASE
                    WHEN s.dealer_vehicle_type IN ('N', 'V') THEN 'NW'
                    WHEN s.dealer_vehicle_type IN ('D', 'G', 'T') THEN 'GW'
                    ELSE 'Sonstige'
                END as fahrzeugart,
                COUNT(*) as anzahl
            FROM sales s
            LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
            WHERE strftime('%Y', s.out_sales_contract_date) = ?
              AND strftime('%m', s.out_sales_contract_date) = ?
              AND s.salesman_number IS NOT NULL
            GROUP BY s.salesman_number, verkaufer_name, fahrzeugart
        """, (str(year), f"{month:02d}"))
        periode_raw = cursor.fetchall()

        # 3. Alle Verkäufer (für vollständige Tabelle)
        cursor.execute("""
            SELECT DISTINCT
                s.salesman_number,
                COALESCE(e.first_name || ' ' || e.last_name, 'Verkäufer #' || s.salesman_number || ' (nicht in LocoSoft)') as verkaufer_name
            FROM sales s
            LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
            WHERE s.salesman_number IS NOT NULL
            ORDER BY verkaufer_name
        """)
        alle_verkaeufer = [dict(row) for row in cursor.fetchall()]

        conn.close()

        # Daten aggregieren
        heute_data = aggregate_verkaufer_daten(heute_raw)
        periode_data = aggregate_verkaufer_daten(periode_raw)

        return jsonify({
            'success': True,
            'month': month,
            'year': year,
            'heute': heute_data['verkaeufer'],
            'periode': periode_data['verkaeufer'],
            'summe_heute': heute_data['summe'],
            'summe_periode': periode_data['summe'],
            'alle_verkaeufer': alle_verkaeufer
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# AUFTRAGSEINGANG DETAIL (NEU)
# ============================================================================

@verkauf_api.route('/auftragseingang/summary', methods=['GET'])
def get_auftragseingang_summary():
    """
    GET /api/verkauf/auftragseingang/summary?month=11&year=2025
    GET /api/verkauf/auftragseingang/summary?day=2025-11-11
    
    Liefert Zusammenfassung nach Marke und Fahrzeugtyp für Auftragseingang
    """
    try:
        day = request.args.get('day', '')
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Zeit-Filter aufbauen
        if day:
            where_clause = "WHERE DATE(s.out_sales_contract_date) = ?"
            params = [day]
        else:
            where_clause = """
                WHERE strftime('%Y', s.out_sales_contract_date) = ?
                  AND strftime('%m', s.out_sales_contract_date) = ?
            """
            params = [str(year), f"{month:02d}"]
        
        # Zusammenfassung nach Marke
        cursor.execute(f"""
            SELECT
                s.make_number,
                COUNT(*) as gesamt,
                SUM(CASE WHEN s.dealer_vehicle_type = 'N' THEN 1 ELSE 0 END) as neu,
                SUM(CASE WHEN s.dealer_vehicle_type IN ('T', 'V') THEN 1 ELSE 0 END) as test_vorfuehr,
                SUM(CASE WHEN s.dealer_vehicle_type IN ('G', 'D') THEN 1 ELSE 0 END) as gebraucht,
                SUM(s.out_sale_price) as umsatz_gesamt
            FROM sales s
            {where_clause}
            GROUP BY s.make_number
        """, params)
        
        summary = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'day': day if day else None,
            'month': month if not day else None,
            'year': year,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@verkauf_api.route('/auftragseingang/detail', methods=['GET'])
def get_auftragseingang_detail():
    """
    GET /api/verkauf/auftragseingang/detail?month=11&year=2025&location=&verkaufer=
    GET /api/verkauf/auftragseingang/detail?day=2025-11-11&location=&verkaufer=
    
    Liefert detaillierte Aufschlüsselung nach Verkäufer und Modellen
    Unterstützt sowohl Monats- als auch Tages-Filter
    """
    try:
        # Parameter
        day = request.args.get('day', '')  # Format: YYYY-MM-DD
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        location = request.args.get('location', '')
        verkaufer = request.args.get('verkaufer', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Basis-Query mit dynamischen Filtern
        where_clauses = ["s.salesman_number IS NOT NULL"]
        params = []
        
        # Zeit-Filter: Tag ODER Monat
        if day:
            # Tages-Filter
            where_clauses.append("DATE(s.out_sales_contract_date) = ?")
            params.append(day)
        else:
            # Monats-Filter (Fallback)
            where_clauses.append("strftime('%Y', s.out_sales_contract_date) = ?")
            where_clauses.append("strftime('%m', s.out_sales_contract_date) = ?")
            params.extend([str(year), f"{month:02d}"])
        
        # Standort-Filter
        if location:
            where_clauses.append("s.out_subsidiary = ?")
            params.append(int(location))
        
        # Verkäufer-Filter
        if verkaufer:
            where_clauses.append("s.salesman_number = ?")
            params.append(int(verkaufer))
        
        where_sql = " AND ".join(where_clauses)
        
        # Verkäufer mit Details
        cursor.execute(f"""
            SELECT
                s.salesman_number,
                COALESCE(e.first_name || ' ' || e.last_name, 'Verkäufer #' || s.salesman_number || ' (nicht in LocoSoft)') as verkaufer_name,
                s.dealer_vehicle_type,
                s.model_description,
                COUNT(*) as anzahl
            FROM sales s
            LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
            WHERE {where_sql}
            GROUP BY s.salesman_number, verkaufer_name, s.dealer_vehicle_type, s.model_description
            ORDER BY verkaufer_name, s.dealer_vehicle_type, s.model_description
        """, params)
        
        rows = cursor.fetchall()
        conn.close()
        
        # Aggregiere nach Verkäufer
        verkaufer_dict = {}
        
        for row in rows:
            vk_nr = row['salesman_number']
            vk_name = row['verkaufer_name']
            typ = row['dealer_vehicle_type']
            modell = row['model_description'] or 'Unbekannt'
            anzahl = row['anzahl']
            
            if vk_nr not in verkaufer_dict:
                verkaufer_dict[vk_nr] = {
                    'verkaufer_nummer': vk_nr,
                    'verkaufer_name': vk_name,
                    'neu': [],
                    'test_vorfuehr': [],
                    'gebraucht': [],
                    'summe_neu': 0,
                    'summe_test_vorfuehr': 0,
                    'summe_gebraucht': 0,
                    'summe_gesamt': 0
                }
            
            modell_info = {'modell': modell, 'anzahl': anzahl}
            
            if typ == 'N':
                verkaufer_dict[vk_nr]['neu'].append(modell_info)
                verkaufer_dict[vk_nr]['summe_neu'] += anzahl
            elif typ in ('T', 'V'):
                verkaufer_dict[vk_nr]['test_vorfuehr'].append(modell_info)
                verkaufer_dict[vk_nr]['summe_test_vorfuehr'] += anzahl
            elif typ in ('G', 'D'):
                verkaufer_dict[vk_nr]['gebraucht'].append(modell_info)
                verkaufer_dict[vk_nr]['summe_gebraucht'] += anzahl
            
            verkaufer_dict[vk_nr]['summe_gesamt'] += anzahl
        
        # Liste erstellen
        verkaufer_list = list(verkaufer_dict.values())
        
        return jsonify({
            'success': True,
            'day': day if day else None,
            'month': month if not day else None,
            'year': year,
            'verkaufer': verkaufer_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# AUSLIEFERUNGEN DETAIL (NEU)
# ============================================================================

@verkauf_api.route('/auslieferung/summary', methods=['GET'])
def get_auslieferung_summary():
    """
    GET /api/verkauf/auslieferung/summary?month=11&year=2025
    GET /api/verkauf/auslieferung/summary?day=2025-11-11
    
    Liefert Zusammenfassung nach Marke und Fahrzeugtyp für Auslieferungen
    Basiert auf Rechnungsdatum (out_invoice_date)
    """
    try:
        day = request.args.get('day', '')
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Zeit-Filter aufbauen (Rechnungsdatum!)
        if day:
            where_clause = """
                WHERE DATE(s.out_invoice_date) = ?
                  AND s.out_invoice_date IS NOT NULL
            """
            params = [day]
        else:
            where_clause = """
                WHERE strftime('%Y', s.out_invoice_date) = ?
                  AND strftime('%m', s.out_invoice_date) = ?
                  AND s.out_invoice_date IS NOT NULL
            """
            params = [str(year), f"{month:02d}"]
        
        # Zusammenfassung nach Marke (Rechnungsdatum!)
        cursor.execute(f"""
            SELECT
                s.make_number,
                COUNT(*) as gesamt,
                SUM(CASE WHEN s.dealer_vehicle_type = 'N' THEN 1 ELSE 0 END) as neu,
                SUM(CASE WHEN s.dealer_vehicle_type IN ('T', 'V') THEN 1 ELSE 0 END) as test_vorfuehr,
                SUM(CASE WHEN s.dealer_vehicle_type IN ('G', 'D') THEN 1 ELSE 0 END) as gebraucht,
                SUM(s.out_sale_price) as umsatz_gesamt
            FROM sales s
            {where_clause}
            GROUP BY s.make_number
        """, params)
        
        summary = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'day': day if day else None,
            'month': month if not day else None,
            'year': year,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@verkauf_api.route('/auslieferung/detail', methods=['GET'])
def get_auslieferung_detail():
    """
    GET /api/verkauf/auslieferung/detail?month=11&year=2025&location=&verkaufer=
    GET /api/verkauf/auslieferung/detail?day=2025-11-11&location=&verkaufer=
    
    Liefert detaillierte Aufschlüsselung der Auslieferungen nach Verkäufer und Modellen
    Basiert auf Rechnungsdatum (out_invoice_date)
    Unterstützt sowohl Monats- als auch Tages-Filter
    """
    try:
        # Parameter
        day = request.args.get('day', '')  # Format: YYYY-MM-DD
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        location = request.args.get('location', '')
        verkaufer = request.args.get('verkaufer', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Basis-Query mit dynamischen Filtern
        where_clauses = [
            "s.salesman_number IS NOT NULL",
            "s.out_invoice_date IS NOT NULL"
        ]
        params = []
        
        # Zeit-Filter: Tag ODER Monat (auf Rechnungsdatum!)
        if day:
            # Tages-Filter
            where_clauses.append("DATE(s.out_invoice_date) = ?")
            params.append(day)
        else:
            # Monats-Filter (Fallback)
            where_clauses.append("strftime('%Y', s.out_invoice_date) = ?")
            where_clauses.append("strftime('%m', s.out_invoice_date) = ?")
            params.extend([str(year), f"{month:02d}"])
        
        # Standort-Filter
        if location:
            where_clauses.append("s.out_subsidiary = ?")
            params.append(int(location))
        
        # Verkäufer-Filter
        if verkaufer:
            where_clauses.append("s.salesman_number = ?")
            params.append(int(verkaufer))
        
        where_sql = " AND ".join(where_clauses)
        
        # Verkäufer mit Details (Rechnungsdatum!)
        cursor.execute(f"""
            SELECT
                s.salesman_number,
                COALESCE(e.first_name || ' ' || e.last_name, 'Verkäufer #' || s.salesman_number || ' (nicht in LocoSoft)') as verkaufer_name,
                s.dealer_vehicle_type,
                s.model_description,
                COUNT(*) as anzahl
            FROM sales s
            LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
            WHERE {where_sql}
            GROUP BY s.salesman_number, verkaufer_name, s.dealer_vehicle_type, s.model_description
            ORDER BY verkaufer_name, s.dealer_vehicle_type, s.model_description
        """, params)
        
        rows = cursor.fetchall()
        conn.close()
        
        # Aggregiere nach Verkäufer (gleiche Logik wie Auftragseingang)
        verkaufer_dict = {}
        
        for row in rows:
            vk_nr = row['salesman_number']
            vk_name = row['verkaufer_name']
            typ = row['dealer_vehicle_type']
            modell = row['model_description'] or 'Unbekannt'
            anzahl = row['anzahl']
            
            if vk_nr not in verkaufer_dict:
                verkaufer_dict[vk_nr] = {
                    'verkaufer_nummer': vk_nr,
                    'verkaufer_name': vk_name,
                    'neu': [],
                    'test_vorfuehr': [],
                    'gebraucht': [],
                    'summe_neu': 0,
                    'summe_test_vorfuehr': 0,
                    'summe_gebraucht': 0,
                    'summe_gesamt': 0
                }
            
            modell_info = {'modell': modell, 'anzahl': anzahl}
            
            if typ == 'N':
                verkaufer_dict[vk_nr]['neu'].append(modell_info)
                verkaufer_dict[vk_nr]['summe_neu'] += anzahl
            elif typ in ('T', 'V'):
                verkaufer_dict[vk_nr]['test_vorfuehr'].append(modell_info)
                verkaufer_dict[vk_nr]['summe_test_vorfuehr'] += anzahl
            elif typ in ('G', 'D'):
                verkaufer_dict[vk_nr]['gebraucht'].append(modell_info)
                verkaufer_dict[vk_nr]['summe_gebraucht'] += anzahl
            
            verkaufer_dict[vk_nr]['summe_gesamt'] += anzahl
        
        # Liste erstellen
        verkaufer_list = list(verkaufer_dict.values())
        
        return jsonify({
            'success': True,
            'day': day if day else None,
            'month': month if not day else None,
            'year': year,
            'verkaufer': verkaufer_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def aggregate_verkaufer_daten(raw_data):
    """Aggregiert Rohdaten zu Verkäufer-Struktur"""
    verkaeufer = {}
    summe = {'NW': 0, 'GW': 0, 'gesamt': 0}

    for row in raw_data:
        vk_nr = row['salesman_number']
        vk_name = row['verkaufer_name']
        fahrzeugart = row['fahrzeugart']
        anzahl = row['anzahl']

        if vk_nr not in verkaeufer:
            verkaeufer[vk_nr] = {
                'nummer': vk_nr,
                'name': vk_name,
                'NW': 0,
                'GW': 0,
                'gesamt': 0
            }

        verkaeufer[vk_nr][fahrzeugart] = anzahl
        verkaeufer[vk_nr]['gesamt'] += anzahl

        summe[fahrzeugart] += anzahl
        summe['gesamt'] += anzahl

    return {
        'verkaeufer': verkaeufer,
        'summe': summe
    }


@verkauf_api.route('/health', methods=['GET'])
def health():
    """Health Check"""
    return jsonify({'status': 'ok', 'service': 'verkauf_api'})


@verkauf_api.route('/verkaufer', methods=['GET'])
def get_verkaufer_liste():
    """
    GET /api/verkauf/verkaufer
    
    Liefert Liste aller Verkäufer (auch ohne LocoSoft-Match)
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT
                s.salesman_number as nummer,
                COALESCE(
                    e.first_name || ' ' || e.last_name,
                    'Verkäufer #' || s.salesman_number || ' (nicht in LocoSoft)'
                ) as name
            FROM sales s
            LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
            WHERE s.salesman_number IS NOT NULL
            ORDER BY 
                CASE 
                    WHEN e.first_name IS NOT NULL THEN 0 
                    ELSE 1 
                END,
                name
        """)
        
        verkaufer = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'verkaufer': verkaufer
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
