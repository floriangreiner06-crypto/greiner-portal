"""
Verkauf REST API
Auftragseingang und Auslieferungen nach Verkäufern und Fahrzeugart

VERSION 2.3 - Mit Deduplizierungs-Filter + VIN-Suche + Einzelfahrzeuge + Interne Aufträge
- Verhindert Doppelzählungen bei N→T/V Umsetzungen
- Regel: Wenn T oder V existiert, ignoriere N für dieselbe VIN am gleichen Datum
- VIN-Filter für Suche
- Einzelfahrzeuge statt Aggregation für bessere Lesbarkeit
- NEU TAG83: Interne Werkstattaufträge aus Locosoft (LIVE!)
"""

from flask import Blueprint, jsonify, request
import sqlite3
import psycopg2
from datetime import datetime, date
from typing import Dict, List

# Blueprint erstellen
verkauf_api = Blueprint('verkauf_api', __name__, url_prefix='/api/verkauf')

def get_db():
    """SQLite Datenbank-Verbindung"""
    conn = sqlite3.connect('/opt/greiner-portal/data/greiner_controlling.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_locosoft_connection():
    """Verbindung zu Locosoft PostgreSQL (LIVE!)"""
    env = {}
    with open('/opt/greiner-portal/config/.env', 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                env[k] = v
    
    return psycopg2.connect(
        host=env['LOCOSOFT_HOST'],
        port=int(env['LOCOSOFT_PORT']),
        database=env['LOCOSOFT_DATABASE'],
        user=env['LOCOSOFT_USER'],
        password=env['LOCOSOFT_PASSWORD']
    )


# Interne Kundennummern (Autohaus Greiner selbst)
# 3000001 = Autohaus Greiner GmbH (Opel/Stellantis)
# 3000002 = Auto Greiner GmbH & Co. KG (Hyundai)
INTERNE_KUNDEN = (3000001, 3000002)


# ============================================================================
# DEDUP-FILTER (Konstante für alle Queries)
# ============================================================================
DEDUP_FILTER = """
    AND NOT EXISTS (
        SELECT 1 
        FROM sales s2 
        WHERE s2.vin = s.vin 
            AND s2.out_sales_contract_date = s.out_sales_contract_date
            AND s2.dealer_vehicle_type IN ('T', 'V')
            AND s.dealer_vehicle_type = 'N'
    )
"""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def aggregate_verkaufer_daten(rows):
    """Aggregiert Rohdaten nach Verkäufer"""
    verkaufer_dict = {}
    summe = {'nw': 0, 'gw': 0, 'gesamt': 0}
    
    for row in rows:
        vk_nr = row['salesman_number']
        vk_name = row['verkaufer_name']
        art = row['fahrzeugart']
        anzahl = row['anzahl']
        
        if vk_nr not in verkaufer_dict:
            verkaufer_dict[vk_nr] = {
                'nummer': vk_nr,
                'name': vk_name,
                'nw': 0,
                'gw': 0,
                'gesamt': 0
            }
        
        if art == 'NW':
            verkaufer_dict[vk_nr]['nw'] += anzahl
            summe['nw'] += anzahl
        elif art == 'GW':
            verkaufer_dict[vk_nr]['gw'] += anzahl
            summe['gw'] += anzahl
        
        verkaufer_dict[vk_nr]['gesamt'] += anzahl
        summe['gesamt'] += anzahl
    
    return {
        'verkaeufer': list(verkaufer_dict.values()),
        'summe': summe
    }


# ============================================================================
# INTERNE WERKSTATTAUFTRÄGE (NEU TAG83 - LIVE aus Locosoft!)
# ============================================================================

@verkauf_api.route('/interne-auftraege', methods=['GET'])
def get_interne_auftraege():
    """
    GET /api/verkauf/interne-auftraege?vin=VXKUHZKXXS4251027
    
    Liefert offene interne Werkstattaufträge für eine VIN.
    Direkt aus Locosoft PostgreSQL (LIVE-Daten!)
    Inkl. Auftragswert und Positionstexte.
    
    Response:
    {
        "vin": "VXKUHZKXXS4251027",
        "anzahl_offen": 1,
        "auftraege": [
            {
                "nummer": 38989,
                "datum": "2025-11-25",
                "wert": 156.50,
                "positionen": ["Ablieferungs-Check", "Kunde:Grill"]
            }
        ]
    }
    """
    vin = request.args.get('vin', '').strip().upper()
    
    if not vin:
        return jsonify({'error': 'VIN Parameter fehlt'}), 400
    
    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor()
        
        # 1. Offene Aufträge holen
        cursor.execute("""
            SELECT 
                o.number as auftragsnummer,
                o.order_date,
                o.order_customer,
                o.has_open_positions,
                o.has_closed_positions
            FROM orders o
            JOIN vehicles v 
                ON o.dealer_vehicle_number = v.dealer_vehicle_number
                AND o.dealer_vehicle_type = v.dealer_vehicle_type
            WHERE UPPER(v.vin) = %s
              AND o.order_customer IN %s
              AND o.has_open_positions = true
            ORDER BY o.order_date DESC
        """, (vin, INTERNE_KUNDEN))
        
        orders = cursor.fetchall()
        
        auftraege = []
        gesamt_wert = 0
        
        for order in orders:
            order_nr = order[0]
            
            # 2. Arbeitspositionen (labours) - NUR NICHT-FAKTURIERTE!
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(net_price_in_order), 0) as summe_arbeit,
                    array_agg(DISTINCT text_line) FILTER (WHERE text_line IS NOT NULL AND text_line != '') as texte
                FROM labours
                WHERE order_number = %s
                  AND is_invoiced = false
            """, (order_nr,))
            labour_row = cursor.fetchone()
            summe_arbeit = float(labour_row[0]) if labour_row[0] else 0
            labour_texte = labour_row[1] if labour_row[1] else []
            
            # 3. Ersatzteile (parts) - NUR NICHT-FAKTURIERTE!
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(sum), 0) as summe_teile,
                    array_agg(DISTINCT text_line) FILTER (WHERE text_line IS NOT NULL AND text_line != '') as texte
                FROM parts
                WHERE order_number = %s
                  AND is_invoiced = false
            """, (order_nr,))
            parts_row = cursor.fetchone()
            summe_teile = float(parts_row[0]) if parts_row[0] else 0
            parts_texte = parts_row[1] if parts_row[1] else []
            
            # Kombinieren
            wert = round(summe_arbeit + summe_teile, 2)
            gesamt_wert += wert
            
            # Texte zusammenführen (nur die ersten paar)
            alle_texte = labour_texte + parts_texte
            # Filtern: nur sinnvolle Texte, max 5
            texte_gefiltert = [t for t in alle_texte if t and len(t) > 2][:5]
            
            auftraege.append({
                'nummer': order_nr,
                'datum': str(order[1])[:10] if order[1] else None,
                'kunde': order[2],
                'offen': order[3],
                'wert': wert,
                'wert_arbeit': round(summe_arbeit, 2),
                'wert_teile': round(summe_teile, 2),
                'positionen': texte_gefiltert
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'vin': vin,
            'anzahl_offen': len(auftraege),
            'gesamt_wert': round(gesamt_wert, 2),
            'auftraege': auftraege
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@verkauf_api.route('/interne-auftraege/bulk', methods=['POST'])
def get_interne_auftraege_bulk():
    """
    POST /api/verkauf/interne-auftraege/bulk
    Body: {"vins": ["VIN1", "VIN2", ...]}
    
    Liefert offene interne Aufträge für mehrere VINs auf einmal.
    Effizienter als einzelne Abfragen.
    Inkl. Wert und Positionstexte.
    
    Response:
    {
        "ergebnis": {
            "VIN1": {"anzahl_offen": 1, "gesamt_wert": 39.0, "auftraege": [...]},
            "VIN2": {"anzahl_offen": 0, "gesamt_wert": 0, "auftraege": []}
        }
    }
    """
    data = request.get_json()
    if not data or 'vins' not in data:
        return jsonify({'error': 'vins Array fehlt'}), 400
    
    vins = [v.strip().upper() for v in data['vins'] if v]
    
    if not vins:
        return jsonify({'success': True, 'ergebnis': {}})
    
    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor()
        
        # 1. Alle offenen Aufträge für alle VINs holen
        cursor.execute("""
            SELECT 
                UPPER(v.vin) as vin,
                o.number as auftragsnummer,
                o.order_date,
                o.order_customer,
                o.has_open_positions
            FROM orders o
            JOIN vehicles v 
                ON o.dealer_vehicle_number = v.dealer_vehicle_number
                AND o.dealer_vehicle_type = v.dealer_vehicle_type
            WHERE UPPER(v.vin) IN %s
              AND o.order_customer IN %s
              AND o.has_open_positions = true
            ORDER BY v.vin, o.order_date DESC
        """, (tuple(vins), INTERNE_KUNDEN))
        
        orders = cursor.fetchall()
        
        # Sammle alle Auftragsnummern für Bulk-Abfrage der Positionen
        order_numbers = [row[1] for row in orders]
        
        # 2. Alle Arbeitspositionen in einer Query - NUR NICHT-FAKTURIERTE!
        labour_data = {}
        if order_numbers:
            cursor.execute("""
                SELECT 
                    order_number,
                    COALESCE(SUM(net_price_in_order), 0) as summe,
                    array_agg(DISTINCT text_line) FILTER (WHERE text_line IS NOT NULL AND text_line != '') as texte
                FROM labours
                WHERE order_number IN %s
                  AND is_invoiced = false
                GROUP BY order_number
            """, (tuple(order_numbers),))
            for row in cursor.fetchall():
                labour_data[row[0]] = {
                    'summe': float(row[1]) if row[1] else 0,
                    'texte': row[2] if row[2] else []
                }
        
        # 3. Alle Ersatzteile in einer Query - NUR NICHT-FAKTURIERTE!
        parts_data = {}
        if order_numbers:
            cursor.execute("""
                SELECT 
                    order_number,
                    COALESCE(SUM(sum), 0) as summe,
                    array_agg(DISTINCT text_line) FILTER (WHERE text_line IS NOT NULL AND text_line != '') as texte
                FROM parts
                WHERE order_number IN %s
                  AND is_invoiced = false
                GROUP BY order_number
            """, (tuple(order_numbers),))
            for row in cursor.fetchall():
                parts_data[row[0]] = {
                    'summe': float(row[1]) if row[1] else 0,
                    'texte': row[2] if row[2] else []
                }
        
        # Ergebnis nach VIN gruppieren
        ergebnis = {vin: {'anzahl_offen': 0, 'gesamt_wert': 0, 'auftraege': []} for vin in vins}
        
        for row in orders:
            vin = row[0]
            order_nr = row[1]
            
            if vin in ergebnis:
                # Werte aus den Bulk-Abfragen holen
                labour = labour_data.get(order_nr, {'summe': 0, 'texte': []})
                parts = parts_data.get(order_nr, {'summe': 0, 'texte': []})
                
                wert = round(labour['summe'] + parts['summe'], 2)
                
                # Texte zusammenführen (max 5)
                alle_texte = labour['texte'] + parts['texte']
                texte_gefiltert = [t for t in alle_texte if t and len(t) > 2][:5]
                
                ergebnis[vin]['auftraege'].append({
                    'nummer': order_nr,
                    'datum': str(row[2])[:10] if row[2] else None,
                    'kunde': row[3],
                    'wert': wert,
                    'wert_arbeit': round(labour['summe'], 2),
                    'wert_teile': round(parts['summe'], 2),
                    'positionen': texte_gefiltert
                })
                ergebnis[vin]['anzahl_offen'] += 1
                ergebnis[vin]['gesamt_wert'] += wert
        
        # Runden
        for vin in ergebnis:
            ergebnis[vin]['gesamt_wert'] = round(ergebnis[vin]['gesamt_wert'], 2)
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'ergebnis': ergebnis})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# AUFTRAGSEINGANG (bestehend - mit Dedup-Filter)
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
        cursor.execute(f"""
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
              {DEDUP_FILTER}
            GROUP BY s.salesman_number, verkaufer_name, fahrzeugart
        """)
        heute_raw = cursor.fetchall()

        # 2. Aufträge PERIODE (ganzer Monat)
        cursor.execute(f"""
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
              {DEDUP_FILTER}
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
# AUFTRAGSEINGANG DETAIL (mit Dedup-Filter)
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
            where_clause = f"WHERE DATE(s.out_sales_contract_date) = ? {DEDUP_FILTER}"
            params = [day]
        else:
            where_clause = f"""
                WHERE strftime('%Y', s.out_sales_contract_date) = ?
                  AND strftime('%m', s.out_sales_contract_date) = ?
                  {DEDUP_FILTER}
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

        # Dedup-Filter hinzufügen
        where_clauses.append("""
            NOT EXISTS (
                SELECT 1 
                FROM sales s2 
                WHERE s2.vin = s.vin 
                    AND s2.out_sales_contract_date = s.out_sales_contract_date
                    AND s2.dealer_vehicle_type IN ('T', 'V')
                    AND s.dealer_vehicle_type = 'N'
            )
        """)

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
# AUSLIEFERUNGEN DETAIL (NEU V2.2 - mit VIN + Einzelfahrzeuge)
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
            where_clause = f"""
                WHERE DATE(s.out_invoice_date) = ?
                  AND s.out_invoice_date IS NOT NULL
                  {DEDUP_FILTER}
            """
            params = [day]
        else:
            where_clause = f"""
                WHERE strftime('%Y', s.out_invoice_date) = ?
                  AND strftime('%m', s.out_invoice_date) = ?
                  AND s.out_invoice_date IS NOT NULL
                  {DEDUP_FILTER}
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
    GET /api/verkauf/auslieferung/detail?month=11&year=2025&location=&verkaufer=&vin=
    GET /api/verkauf/auslieferung/detail?day=2025-11-11&location=&verkaufer=&vin=

    VERSION 2.2: Liefert EINZELFAHRZEUGE (nicht aggregiert) für bessere Lesbarkeit
    - Inkl. VIN für Suche und Anzeige
    - Inkl. Deckungsbeitrag-Daten
    - Basiert auf Rechnungsdatum (out_invoice_date)
    """
    try:
        # Parameter
        day = request.args.get('day', '')  # Format: YYYY-MM-DD
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        location = request.args.get('location', '')
        verkaufer = request.args.get('verkaufer', '')
        vin_search = request.args.get('vin', '')  # NEU: VIN-Suche

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
            where_clauses.append("DATE(s.out_invoice_date) = ?")
            params.append(day)
        else:
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

        # NEU: VIN-Filter (Teilsuche)
        if vin_search:
            where_clauses.append("s.vin LIKE ?")
            params.append(f"%{vin_search}%")

        # Dedup-Filter hinzufügen
        where_clauses.append("""
            NOT EXISTS (
                SELECT 1
                FROM sales s2
                WHERE s2.vin = s.vin
                    AND s2.out_sales_contract_date = s.out_sales_contract_date
                    AND s2.dealer_vehicle_type IN ('T', 'V')
                    AND s.dealer_vehicle_type = 'N'
            )
        """)

        where_sql = " AND ".join(where_clauses)

        # EINZELFAHRZEUGE abrufen (nicht aggregiert!)
        cursor.execute(f"""
            SELECT
                s.salesman_number,
                COALESCE(e.first_name || ' ' || e.last_name, 'Verkäufer #' || s.salesman_number || ' (nicht in LocoSoft)') as verkaufer_name,
                s.dealer_vehicle_type,
                s.model_description,
                s.vin,
                s.out_invoice_date,
                COALESCE(s.out_sale_price, 0) as umsatz,
                COALESCE(s.deckungsbeitrag, 0) as deckungsbeitrag,
                COALESCE(s.db_prozent, 0) as db_prozent
            FROM sales s
            LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
            WHERE {where_sql}
            ORDER BY verkaufer_name, s.dealer_vehicle_type, s.model_description
        """, params)

        rows = cursor.fetchall()
        conn.close()

        # Aggregiere nach Verkäufer mit EINZELFAHRZEUGEN
        verkaufer_dict = {}

        for row in rows:
            vk_nr = row['salesman_number']
            vk_name = row['verkaufer_name']
            typ = row['dealer_vehicle_type']
            modell = row['model_description'] or 'Unbekannt'
            vin = row['vin'] or ''
            invoice_date = row['out_invoice_date']
            umsatz = row['umsatz'] or 0
            db = row['deckungsbeitrag'] or 0
            db_prozent = row['db_prozent'] or 0

            if vk_nr not in verkaufer_dict:
                verkaufer_dict[vk_nr] = {
                    'verkaufer_nummer': vk_nr,
                    'verkaufer_name': vk_name,
                    'fahrzeuge': [],  # NEU: Einzelfahrzeuge statt Kategorien
                    'summe_neu': 0,
                    'summe_test_vorfuehr': 0,
                    'summe_gebraucht': 0,
                    'summe_gesamt': 0,
                    'umsatz_gesamt': 0,
                    'db_gesamt': 0
                }

            # Einzelfahrzeug-Info
            fahrzeug_info = {
                'typ': typ,
                'modell': modell,
                'vin': vin,
                'vin_kurz': vin[-8:] if len(vin) >= 8 else vin,  # Letzte 8 Zeichen
                'datum': invoice_date,
                'umsatz': round(umsatz, 2),
                'deckungsbeitrag': round(db, 2),
                'db_prozent': round(db_prozent, 2)
            }

            verkaufer_dict[vk_nr]['fahrzeuge'].append(fahrzeug_info)

            # Summen aktualisieren
            if typ == 'N':
                verkaufer_dict[vk_nr]['summe_neu'] += 1
            elif typ in ('T', 'V'):
                verkaufer_dict[vk_nr]['summe_test_vorfuehr'] += 1
            elif typ in ('G', 'D'):
                verkaufer_dict[vk_nr]['summe_gebraucht'] += 1

            verkaufer_dict[vk_nr]['summe_gesamt'] += 1
            verkaufer_dict[vk_nr]['umsatz_gesamt'] += umsatz
            verkaufer_dict[vk_nr]['db_gesamt'] += db

        # DB% für Gesamt berechnen
        for vk_data in verkaufer_dict.values():
            if vk_data['umsatz_gesamt'] > 0:
                vk_data['db_prozent_gesamt'] = round(
                    (vk_data['db_gesamt'] / (vk_data['umsatz_gesamt'] / 1.19)) * 100, 2
                )
            else:
                vk_data['db_prozent_gesamt'] = 0
            
            # Runden
            vk_data['umsatz_gesamt'] = round(vk_data['umsatz_gesamt'], 2)
            vk_data['db_gesamt'] = round(vk_data['db_gesamt'], 2)

        # Liste erstellen und nach Name sortieren
        verkaufer_list = sorted(
            verkaufer_dict.values(), 
            key=lambda x: x['verkaufer_name']
        )

        return jsonify({
            'success': True,
            'day': day if day else None,
            'month': month if not day else None,
            'year': year,
            'vin_filter': vin_search if vin_search else None,
            'verkaufer': verkaufer_list
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# AUFTRAGSEINGANG FAHRZEUGE (NEU TAG83 - Einzelfahrzeuge mit VIN)
# ============================================================================

@verkauf_api.route('/auftragseingang/fahrzeuge', methods=['GET'])
def get_auftragseingang_fahrzeuge():
    """
    GET /api/verkauf/auftragseingang/fahrzeuge?month=11&year=2025&location=&verkaufer=&vin=
    GET /api/verkauf/auftragseingang/fahrzeuge?day=2025-11-25&location=&verkaufer=&vin=

    NEU TAG83: Liefert EINZELFAHRZEUGE (nicht aggregiert) für Auftragseingang
    - Inkl. VIN für WA-Badge
    - Basiert auf Vertragsdatum (out_sales_contract_date)
    """
    try:
        # Parameter
        day = request.args.get('day', '')  # Format: YYYY-MM-DD
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        location = request.args.get('location', '')
        verkaufer = request.args.get('verkaufer', '')
        vin_search = request.args.get('vin', '')

        conn = get_db()
        cursor = conn.cursor()

        # Basis-Query mit dynamischen Filtern
        where_clauses = ["s.salesman_number IS NOT NULL"]
        params = []

        # Zeit-Filter: Tag ODER Monat (auf Vertragsdatum!)
        if day:
            where_clauses.append("DATE(s.out_sales_contract_date) = ?")
            params.append(day)
        else:
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

        # VIN-Filter (Teilsuche)
        if vin_search:
            where_clauses.append("s.vin LIKE ?")
            params.append(f"%{vin_search}%")

        # Dedup-Filter hinzufügen
        where_clauses.append("""
            NOT EXISTS (
                SELECT 1
                FROM sales s2
                WHERE s2.vin = s.vin
                    AND s2.out_sales_contract_date = s.out_sales_contract_date
                    AND s2.dealer_vehicle_type IN ('T', 'V')
                    AND s.dealer_vehicle_type = 'N'
            )
        """)

        where_sql = " AND ".join(where_clauses)

        # EINZELFAHRZEUGE abrufen (nicht aggregiert!)
        cursor.execute(f"""
            SELECT
                s.salesman_number,
                COALESCE(e.first_name || ' ' || e.last_name, 'Verkäufer #' || s.salesman_number || ' (nicht in LocoSoft)') as verkaufer_name,
                s.dealer_vehicle_type,
                s.model_description,
                s.vin,
                s.out_sales_contract_date,
                COALESCE(s.out_sale_price, 0) as umsatz
            FROM sales s
            LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
            WHERE {where_sql}
            ORDER BY verkaufer_name, s.dealer_vehicle_type, s.model_description
        """, params)

        rows = cursor.fetchall()
        conn.close()

        # Aggregiere nach Verkäufer mit EINZELFAHRZEUGEN
        verkaufer_dict = {}

        for row in rows:
            vk_nr = row['salesman_number']
            vk_name = row['verkaufer_name']
            typ = row['dealer_vehicle_type']
            modell = row['model_description'] or 'Unbekannt'
            vin = row['vin'] or ''
            contract_date = row['out_sales_contract_date']
            umsatz = row['umsatz'] or 0

            if vk_nr not in verkaufer_dict:
                verkaufer_dict[vk_nr] = {
                    'verkaufer_nummer': vk_nr,
                    'verkaufer_name': vk_name,
                    'fahrzeuge': [],
                    'summe_neu': 0,
                    'summe_test_vorfuehr': 0,
                    'summe_gebraucht': 0,
                    'summe_gesamt': 0,
                    'umsatz_gesamt': 0
                }

            # Einzelfahrzeug-Info
            fahrzeug_info = {
                'typ': typ,
                'modell': modell,
                'vin': vin,
                'vin_kurz': vin[-8:] if len(vin) >= 8 else vin,
                'datum': contract_date,
                'umsatz': round(umsatz, 2)
            }

            verkaufer_dict[vk_nr]['fahrzeuge'].append(fahrzeug_info)

            # Summen aktualisieren
            if typ == 'N':
                verkaufer_dict[vk_nr]['summe_neu'] += 1
            elif typ in ('T', 'V'):
                verkaufer_dict[vk_nr]['summe_test_vorfuehr'] += 1
            elif typ in ('G', 'D'):
                verkaufer_dict[vk_nr]['summe_gebraucht'] += 1

            verkaufer_dict[vk_nr]['summe_gesamt'] += 1
            verkaufer_dict[vk_nr]['umsatz_gesamt'] += umsatz

        # Runden
        for vk_data in verkaufer_dict.values():
            vk_data['umsatz_gesamt'] = round(vk_data['umsatz_gesamt'], 2)

        # Liste erstellen und nach Name sortieren
        verkaufer_list = sorted(
            verkaufer_dict.values(),
            key=lambda x: x['verkaufer_name']
        )

        return jsonify({
            'success': True,
            'day': day if day else None,
            'month': month if not day else None,
            'year': year,
            'vin_filter': vin_search if vin_search else None,
            'verkaufer': verkaufer_list
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@verkauf_api.route('/health', methods=['GET'])
def health():
    """Health Check"""
    return jsonify({'status': 'ok', 'service': 'verkauf_api', 'version': '2.4-wa-frontend'})


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
