"""
Verkauf REST API
Auftragseingang nach Verkäufern und Fahrzeugart
"""

from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime, date
from typing import Dict, List

# Blueprint erstellen

def get_db_connection():
    """Erstellt SQLite Datenbankverbindung"""
    import sqlite3
    conn = sqlite3.connect('data/greiner_controlling.db')
    conn.row_factory = sqlite3.Row
    return conn

verkauf_api = Blueprint('verkauf_api', __name__, url_prefix='/api/verkauf')

def get_db():
    """Datenbank-Verbindung"""
    conn = sqlite3.connect('/opt/greiner-portal/data/greiner_controlling.db')
    conn.row_factory = sqlite3.Row
    return conn

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
                e.first_name || ' ' || e.last_name as verkaufer_name,
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
                e.first_name || ' ' || e.last_name as verkaufer_name,
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
                e.first_name || ' ' || e.last_name as verkaufer_name
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

# ============================================================================
# ERWEITERTE ENDPOINTS FÜR WUNSCHLISTEN-FEATURES
# ============================================================================


@verkauf_api.route('/auftragseingang/detail', methods=['GET'])
def get_auftragseingang_detail():
    """
    Detaillierter Auftragseingang mit Modellen
    
    Query-Parameter:
    - month: Monat (1-12)
    - year: Jahr (z.B. 2025)
    - location: Standort (Deggendorf/Landau a.d. Isar, optional)
    """
    try:
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        location = request.args.get('location', type=str)  # Optional
        
        if not month or not year:
            return jsonify({'error': 'month und year erforderlich'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query mit Modell-Details
        query = """
            SELECT 
                s.salesman_number,
                e.first_name || ' ' || e.last_name as verkaufer_name,
                s.make_number,
                CASE s.make_number 
                    WHEN 40 THEN 'Opel'
                    WHEN 27 THEN 'Hyundai'
                    ELSE 'Andere'
                END as marke,
                s.dealer_vehicle_type,
                CASE 
                    WHEN s.dealer_vehicle_type = 'N' THEN 'Neuwagen'
                    WHEN s.dealer_vehicle_type IN ('T', 'V') THEN 'Test/Vorführ'
                    WHEN s.dealer_vehicle_type IN ('G', 'D') THEN 'Gebraucht'
                    ELSE 'Sonstige'
                END as kategorie,
                s.model_description,
                COUNT(*) as anzahl,
                SUM(s.out_sale_price) as umsatz,
                SUM(s.netto_price) as netto_umsatz
            FROM sales s
            LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
            WHERE strftime('%Y', s.out_sales_contract_date) = ?
              AND strftime('%m', s.out_sales_contract_date) = ?
        """
        
        params = [str(year), f'{month:02d}']
        
        # Optional: Nach Verkäufer-Standort filtern
        if location:
            query += " AND e.location = ?"
            params.append(location)
        
        query += """
            GROUP BY s.salesman_number, s.make_number, s.dealer_vehicle_type, s.model_description
            ORDER BY verkaufer_name, kategorie, anzahl DESC
        """
        
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'salesman_number': row[0],
                'verkaufer_name': row[1],
                'make_number': row[2],
                'marke': row[3],
                'typ': row[4],
                'kategorie': row[5],
                'modell': row[6],
                'anzahl': row[7],
                'umsatz': float(row[8]) if row[8] else 0,
                'netto_umsatz': float(row[9]) if row[9] else 0
            })
        
        conn.close()
        
        # Gruppieren nach Verkäufer
        verkaufer_data = {}
        for item in results:
            vk_nr = item['salesman_number']
            if vk_nr not in verkaufer_data:
                verkaufer_data[vk_nr] = {
                    'salesman_number': vk_nr,
                    'verkaufer_name': item['verkaufer_name'],
                    'neu': [],
                    'test_vorfuehr': [],
                    'gebraucht': [],
                    'summe_neu': 0,
                    'summe_test_vorfuehr': 0,
                    'summe_gebraucht': 0,
                    'summe_gesamt': 0
                }
            
            # Nach Kategorie sortieren
            if item['kategorie'] == 'Neuwagen':
                verkaufer_data[vk_nr]['neu'].append(item)
                verkaufer_data[vk_nr]['summe_neu'] += item['anzahl']
            elif item['kategorie'] == 'Test/Vorführ':
                verkaufer_data[vk_nr]['test_vorfuehr'].append(item)
                verkaufer_data[vk_nr]['summe_test_vorfuehr'] += item['anzahl']
            elif item['kategorie'] == 'Gebraucht':
                verkaufer_data[vk_nr]['gebraucht'].append(item)
                verkaufer_data[vk_nr]['summe_gebraucht'] += item['anzahl']
            
            verkaufer_data[vk_nr]['summe_gesamt'] += item['anzahl']
        
        return jsonify({
            'month': month,
            'year': year,
            'location': location,
            'verkaufer': list(verkaufer_data.values())
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@verkauf_api.route('/auftragseingang/summary', methods=['GET'])
def get_auftragseingang_summary():
    """
    Zusammenfassung für Opel und Hyundai getrennt
    
    Query-Parameter:
    - month: Monat (1-12)
    - year: Jahr (z.B. 2025)
    """
    try:
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        
        if not month or not year:
            return jsonify({'error': 'month und year erforderlich'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Zusammenfassung pro Marke
        cursor.execute("""
            SELECT 
                s.make_number,
                CASE s.make_number 
                    WHEN 40 THEN 'Opel'
                    WHEN 27 THEN 'Hyundai'
                    ELSE 'Andere'
                END as marke,
                COUNT(*) as gesamt,
                SUM(CASE WHEN s.dealer_vehicle_type = 'N' THEN 1 ELSE 0 END) as neu,
                SUM(CASE WHEN s.dealer_vehicle_type IN ('T','V') THEN 1 ELSE 0 END) as test_vorfuehr,
                SUM(CASE WHEN s.dealer_vehicle_type IN ('G','D') THEN 1 ELSE 0 END) as gebraucht,
                COUNT(DISTINCT s.salesman_number) as anzahl_verkaufer,
                SUM(s.out_sale_price) as umsatz_gesamt
            FROM sales s
            WHERE strftime('%Y', s.out_sales_contract_date) = ?
              AND strftime('%m', s.out_sales_contract_date) = ?
            GROUP BY s.make_number
            ORDER BY marke
        """, [str(year), f'{month:02d}'])
        
        summary = []
        for row in cursor.fetchall():
            summary.append({
                'make_number': row[0],
                'marke': row[1],
                'gesamt': row[2],
                'neu': row[3],
                'test_vorfuehr': row[4],
                'gebraucht': row[5],
                'anzahl_verkaufer': row[6],
                'umsatz_gesamt': float(row[7]) if row[7] else 0
            })
        
        conn.close()
        
        return jsonify({
            'month': month,
            'year': year,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# AUSLIEFERUNGS-ENDPOINTS (TAG 19)
# ============================================================================

@verkauf_api.route('/auslieferung/detail', methods=['GET'])
def get_auslieferung_detail():
    """
    Detaillierte Auslieferungsliste mit Modellen
    
    Query-Parameter:
    - month: Monat (1-12)
    - year: Jahr (z.B. 2025)
    - location: Standort (Deggendorf/Landau a.d. Isar, optional)
    
    UNTERSCHIED zu auftragseingang:
    - Verwendet out_invoice_date statt out_sales_contract_date
    - Nur Fahrzeuge MIT Rechnung (ausgeliefert)
    """
    try:
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        location = request.args.get('location', type=str)

        if not month or not year:
            return jsonify({'error': 'month und year erforderlich'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                s.salesman_number,
                e.first_name || ' ' || e.last_name as verkaufer_name,
                s.make_number,
                CASE s.make_number
                    WHEN 40 THEN 'Opel'
                    WHEN 27 THEN 'Hyundai'
                    ELSE 'Andere'
                END as marke,
                s.dealer_vehicle_type,
                CASE
                    WHEN s.dealer_vehicle_type = 'N' THEN 'Neuwagen'
                    WHEN s.dealer_vehicle_type IN ('T', 'V') THEN 'Test/Vorführ'
                    WHEN s.dealer_vehicle_type IN ('G', 'D') THEN 'Gebraucht'
                    ELSE 'Sonstige'
                END as kategorie,
                s.model_description,
                COUNT(*) as anzahl,
                SUM(s.out_sale_price) as umsatz,
                SUM(s.netto_price) as netto_umsatz
            FROM sales s
            LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
            WHERE s.out_invoice_date IS NOT NULL
              AND strftime('%Y', s.out_invoice_date) = ?
              AND strftime('%m', s.out_invoice_date) = ?
        """

        params = [str(year), f'{month:02d}']

        if location:
            query += " AND e.location = ?"
            params.append(location)

        query += """
            GROUP BY s.salesman_number, s.make_number, s.dealer_vehicle_type, s.model_description
            ORDER BY verkaufer_name, kategorie, anzahl DESC
        """

        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            results.append({
                'salesman_number': row[0],
                'verkaufer_name': row[1],
                'make_number': row[2],
                'marke': row[3],
                'typ': row[4],
                'kategorie': row[5],
                'modell': row[6],
                'anzahl': row[7],
                'umsatz': float(row[8]) if row[8] else 0,
                'netto_umsatz': float(row[9]) if row[9] else 0
            })

        conn.close()

        verkaufer_data = {}
        for item in results:
            vk_nr = item['salesman_number']
            if vk_nr not in verkaufer_data:
                verkaufer_data[vk_nr] = {
                    'salesman_number': vk_nr,
                    'verkaufer_name': item['verkaufer_name'],
                    'neu': [],
                    'test_vorfuehr': [],
                    'gebraucht': [],
                    'summe_neu': 0,
                    'summe_test_vorfuehr': 0,
                    'summe_gebraucht': 0,
                    'summe_gesamt': 0
                }

            if item['kategorie'] == 'Neuwagen':
                verkaufer_data[vk_nr]['neu'].append(item)
                verkaufer_data[vk_nr]['summe_neu'] += item['anzahl']
            elif item['kategorie'] == 'Test/Vorführ':
                verkaufer_data[vk_nr]['test_vorfuehr'].append(item)
                verkaufer_data[vk_nr]['summe_test_vorfuehr'] += item['anzahl']
            elif item['kategorie'] == 'Gebraucht':
                verkaufer_data[vk_nr]['gebraucht'].append(item)
                verkaufer_data[vk_nr]['summe_gebraucht'] += item['anzahl']

            verkaufer_data[vk_nr]['summe_gesamt'] += item['anzahl']

        return jsonify({
            'month': month,
            'year': year,
            'location': location,
            'verkaufer': list(verkaufer_data.values())
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@verkauf_api.route('/auslieferung/summary', methods=['GET'])
def get_auslieferung_summary():
    """
    Zusammenfassung für Auslieferungen (Opel und Hyundai getrennt)
    
    Query-Parameter:
    - month: Monat (1-12)
    - year: Jahr (z.B. 2025)
    """
    try:
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)

        if not month or not year:
            return jsonify({'error': 'month und year erforderlich'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                s.make_number,
                CASE s.make_number
                    WHEN 40 THEN 'Opel'
                    WHEN 27 THEN 'Hyundai'
                    ELSE 'Andere'
                END as marke,
                COUNT(*) as gesamt,
                SUM(CASE WHEN s.dealer_vehicle_type = 'N' THEN 1 ELSE 0 END) as neu,
                SUM(CASE WHEN s.dealer_vehicle_type IN ('T','V') THEN 1 ELSE 0 END) as test_vorfuehr,
                SUM(CASE WHEN s.dealer_vehicle_type IN ('G','D') THEN 1 ELSE 0 END) as gebraucht,
                COUNT(DISTINCT s.salesman_number) as anzahl_verkaufer,
                SUM(s.out_sale_price) as umsatz_gesamt
            FROM sales s
            WHERE s.out_invoice_date IS NOT NULL
              AND strftime('%Y', s.out_invoice_date) = ?
              AND strftime('%m', s.out_invoice_date) = ?
            GROUP BY s.make_number
            ORDER BY marke
        """, [str(year), f'{month:02d}'])

        summary = []
        for row in cursor.fetchall():
            summary.append({
                'make_number': row[0],
                'marke': row[1],
                'gesamt': row[2],
                'neu': row[3],
                'test_vorfuehr': row[4],
                'gebraucht': row[5],
                'anzahl_verkaufer': row[6],
                'umsatz_gesamt': float(row[7]) if row[7] else 0
            })

        conn.close()

        return jsonify({
            'month': month,
            'year': year,
            'summary': summary
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
