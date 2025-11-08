"""
Verkauf REST API
Auftragseingang nach Verkäufern und Fahrzeugart
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
