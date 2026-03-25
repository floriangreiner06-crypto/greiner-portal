"""
Verkauf REST API
Auftragseingang und Auslieferungen nach Verkäufern und Fahrzeugart

VERSION 3.0 - Refaktoriert mit verkauf_data.py als SSOT
- Alle Datenlogik ausgelagert nach api/verkauf_data.py
- API-Layer nur noch für HTTP-Handling
- NEU TAG83: Interne Werkstattaufträge aus Locosoft (LIVE!)
Updated: TAG 159 - Refactoring auf Data-Module Pattern
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required
from datetime import datetime, date
from typing import Dict, List

# Zentrale DB-Utilities (für interne Aufträge)
from api.db_utils import locosoft_session

# SSOT Data Module
from api.verkauf_data import VerkaufData

# Blueprint erstellen
verkauf_api = Blueprint('verkauf_api', __name__, url_prefix='/api/verkauf')

# TAG 181: Import für NW-Pipeline
from api.fahrzeug_data import FahrzeugData


# Interne Kundennummern (Autohaus Greiner selbst)
# 3000001 = Autohaus Greiner GmbH (Opel/Stellantis)
# 3000002 = Auto Greiner GmbH & Co. KG (Hyundai)
INTERNE_KUNDEN = (3000001, 3000002)


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
    """
    vin = request.args.get('vin', '').strip().upper()

    if not vin:
        return jsonify({'error': 'VIN Parameter fehlt'}), 400

    try:
        with locosoft_session() as conn:
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
    """
    data = request.get_json()
    if not data or 'vins' not in data:
        return jsonify({'error': 'vins Array fehlt'}), 400

    vins = [v.strip().upper() for v in data['vins'] if v]

    if not vins:
        return jsonify({'success': True, 'ergebnis': {}})

    try:
        with locosoft_session() as conn:
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

            return jsonify({'success': True, 'ergebnis': ergebnis})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# AUFTRAGSEINGANG (Delegiert an VerkaufData)
# ============================================================================

@verkauf_api.route('/auftragseingang', methods=['GET'])
@login_required
def get_auftragseingang():
    """
    GET /api/verkauf/auftragseingang?month=11&year=2025&location=1

    Liefert Auftragseingang nach Verkäufern
    - heute: Aufträge vom aktuellen Tag
    - periode: Kumuliert für gewählten Monat
    - location: Standort-Filter (1, 2, 3)
    """
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    location = request.args.get('location', type=int)

    result = VerkaufData.get_auftragseingang(month=month, year=year, location=location)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


# ============================================================================
# AUFTRAGSEINGANG DETAIL (Delegiert an VerkaufData)
# ============================================================================

@verkauf_api.route('/auftragseingang/summary', methods=['GET'])
@login_required
def get_auftragseingang_summary():
    """
    GET /api/verkauf/auftragseingang/summary?month=11&year=2025&location=1
    GET /api/verkauf/auftragseingang/summary?day=2025-11-11&location=1

    Liefert Zusammenfassung nach Marke und Fahrzeugtyp für Auftragseingang
    - location: Standort-Filter (1, 2, 3)
    """
    day = request.args.get('day', '') or None
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    location = request.args.get('location', type=int)
    zeitraum = request.args.get('zeitraum', 'month')

    result = VerkaufData.get_auftragseingang_summary(
        day=day, month=month, year=year, location=location, zeitraum=zeitraum
    )

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@verkauf_api.route('/auftragseingang/detail', methods=['GET'])
@login_required
def get_auftragseingang_detail():
    """
    GET /api/verkauf/auftragseingang/detail?month=11&year=2025&location=&verkaufer=
    GET /api/verkauf/auftragseingang/detail?day=2025-11-11&location=&verkaufer=

    Liefert detaillierte Aufschlüsselung nach Verkäufer und Modellen
    """
    day = request.args.get('day', '') or None
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    location = request.args.get('location', type=int)
    verkaufer = request.args.get('verkaufer', type=int)
    zeitraum = request.args.get('zeitraum', 'month')

    result = VerkaufData.get_auftragseingang_detail(
        day=day, month=month, year=year,
        location=location, verkaufer=verkaufer, zeitraum=zeitraum
    )

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


# ============================================================================
# AUSLIEFERUNGEN (Delegiert an VerkaufData)
# ============================================================================

@verkauf_api.route('/auslieferung/summary', methods=['GET'])
@login_required
def get_auslieferung_summary():
    """
    GET /api/verkauf/auslieferung/summary?month=11&year=2025
    GET /api/verkauf/auslieferung/summary?day=2025-11-11

    Liefert Zusammenfassung nach Marke und Fahrzeugtyp für Auslieferungen
    """
    day = request.args.get('day', '') or None
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    zeitraum = request.args.get('zeitraum', 'month')

    result = VerkaufData.get_auslieferung_summary(
        day=day, month=month, year=year, zeitraum=zeitraum
    )

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@verkauf_api.route('/auslieferung/detail', methods=['GET'])
@login_required
def get_auslieferung_detail():
    """
    GET /api/verkauf/auslieferung/detail?month=11&year=2025&location=&verkaufer=&vin=

    Liefert EINZELFAHRZEUGE mit VIN und DB-Daten
    """
    day = request.args.get('day', '') or None
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    location = request.args.get('location', type=int)
    verkaufer = request.args.get('verkaufer', type=int)
    vin_search = request.args.get('vin', '') or None
    zeitraum = request.args.get('zeitraum', 'month')

    result = VerkaufData.get_auslieferung_detail(
        day=day, month=month, year=year,
        location=location, verkaufer=verkaufer, vin_search=vin_search, zeitraum=zeitraum
    )

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


# ============================================================================
# AUFTRAGSEINGANG FAHRZEUGE (Nutzt gleiche Logik wie Detail)
# ============================================================================

@verkauf_api.route('/auftragseingang/fahrzeuge', methods=['GET'])
def get_auftragseingang_fahrzeuge():
    """
    GET /api/verkauf/auftragseingang/fahrzeuge?month=11&year=2025&location=&verkaufer=&vin=

    Liefert EINZELFAHRZEUGE für Auftragseingang (nutzt Detail-Endpoint intern)
    """
    day = request.args.get('day', '') or None
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    location = request.args.get('location', type=int)
    verkaufer = request.args.get('verkaufer', type=int)
    vin_search = request.args.get('vin', '') or None

    # Nutzt die gleiche Detail-Funktion
    result = VerkaufData.get_auftragseingang_detail(
        day=day, month=month, year=year,
        location=location, verkaufer=verkaufer
    )

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@verkauf_api.route('/health', methods=['GET'])
def health():
    """Health Check"""
    return jsonify({'status': 'ok', 'service': 'verkauf_api', 'version': '3.0-data-module'})


@verkauf_api.route('/verkaufer', methods=['GET'])
@login_required
def get_verkaufer_liste():
    """
    GET /api/verkauf/verkaufer

    Liefert Liste aller Verkäufer
    """
    result = VerkaufData.get_verkaufer_liste()

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


# ============================================================================
# LIEFERFORECAST (Delegiert an VerkaufData)
# ============================================================================

@verkauf_api.route('/lieferforecast', methods=['GET'])
def get_lieferforecast():
    """
    GET /api/verkauf/lieferforecast?von=2025-12-22&bis=2025-12-31&standort=all

    Liefert geplante Fahrzeugauslieferungen mit DB1-Prognose
    """
    von = request.args.get('von', date.today().strftime('%Y-%m-%d'))
    bis = request.args.get('bis')
    # TAG 177: Standort-ID (1, 2, 3) statt 'all', 'DEG', 'LAN'
    standort_param = request.args.get('standort', type=int)
    konsolidiert = request.args.get('konsolidiert', 'false').lower() == 'true'
    
    # Mapping: Standort-ID -> Legacy-Format
    # DEG = Deggendorf (Standort 1+2 zusammen, konsolidiert)
    # LAN = Landau (Standort 3)
    if standort_param == 1:
        if konsolidiert:
            standort = 'DEG'  # Service Deggendorf (konsolidiert: 1+2)
        else:
            standort = 'DEG'  # Deggendorf Opel (auch DEG für API)
    elif standort_param == 2:
        standort = 'DEG'  # Hyundai DEG (auch DEG)
    elif standort_param == 3:
        standort = 'LAN'
    else:
        standort = 'all'

    result = VerkaufData.get_lieferforecast(von=von, bis=bis, standort=standort)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


# ============================================================================
# VIN EINKAUFSINFORMATIONEN (NEU TAG193)
# ============================================================================

@verkauf_api.route('/vin-einkauf', methods=['GET'])
def get_vin_einkauf_info():
    """
    GET /api/verkauf/vin-einkauf?vin=VXEYCBPFCNG019171
    
    Liefert für eine VIN:
    - Einkaufender Verkäufer (in_buy_salesman_number)
    - Kreditor/Lieferant (buyer_customer_no, falls is_supplier = true)
    - Ex-Halter (previous_owner_number aus vehicles/dealer_vehicles)
    - Einkaufsrechnung (in_buy_invoice_no, in_buy_invoice_no_date)
    - Einkaufsbestellung (in_buy_order_no, in_buy_order_no_date)
    - Einkaufspreis (in_buy_list_price)
    
    Direkt aus Locosoft PostgreSQL.
    """
    vin = request.args.get('vin', '').strip().upper()
    
    if not vin:
        return jsonify({'error': 'VIN Parameter fehlt'}), 400
    
    try:
        with locosoft_session() as conn:
            cursor = conn.cursor()
            
            # 1. Hole Fahrzeug-Daten aus dealer_vehicles (inkl. Einkaufsrechnung und Ex-Halter)
            cursor.execute("""
                SELECT
                    dv.dealer_vehicle_number,
                    dv.dealer_vehicle_type,
                    dv.in_buy_salesman_number,
                    dv.buyer_customer_no,
                    dv.in_buy_invoice_no,
                    dv.in_buy_invoice_no_date,
                    dv.in_buy_order_no,
                    dv.in_buy_order_no_date,
                    dv.in_buy_edp_order_no,
                    dv.in_buy_edp_order_no_date,
                    dv.in_buy_list_price,
                    dv.in_arrival_date,
                    COALESCE(dv.previous_owner_number, v.previous_owner_number) as previous_owner_number,
                    v.previous_owner_counter,
                    v.vin,
                    v.free_form_model_text as modell
                FROM dealer_vehicles dv
                LEFT JOIN vehicles v
                    ON dv.dealer_vehicle_number = v.dealer_vehicle_number
                    AND dv.dealer_vehicle_type = v.dealer_vehicle_type
                WHERE UPPER(v.vin) = %s
                ORDER BY dv.created_date DESC NULLS LAST
                LIMIT 1
            """, (vin,))
            
            row = cursor.fetchone()
            
            if not row:
                return jsonify({
                    'success': False,
                    'error': f'VIN {vin} nicht gefunden',
                    'vin': vin
                }), 404
            
            dealer_vehicle_number = row[0]
            dealer_vehicle_type = row[1]
            in_buy_salesman_number = row[2]
            buyer_customer_no = row[3]
            in_buy_invoice_no = row[4]
            in_buy_invoice_no_date = row[5]
            in_buy_order_no = row[6]
            in_buy_order_no_date = row[7]
            in_buy_edp_order_no = row[8]
            in_buy_edp_order_no_date = row[9]
            in_buy_list_price = row[10]
            in_arrival_date = row[11]
            previous_owner_number = row[12]
            previous_owner_counter = row[13]
            vin_found = row[14]
            modell = row[15]
            
            result = {
                'success': True,
                'vin': vin_found,
                'modell': modell,
                'dealer_vehicle_number': dealer_vehicle_number,
                'dealer_vehicle_type': dealer_vehicle_type,
                'einkaufender_verkaeufer': None,
                'kreditor_lieferant': None,
                'ex_halter': None,
                'einkaufsrechnung': None,
                'einkaufsbestellung': None,
                'ek_preis': float(in_buy_list_price) if in_buy_list_price else None,
                'eingangsdatum': str(in_arrival_date) if in_arrival_date else None
            }
            
            # 2. Hole einkaufenden Verkäufer (falls vorhanden)
            if in_buy_salesman_number:
                cursor.execute("""
                    SELECT
                        employee_number,
                        name
                    FROM employees_history
                    WHERE employee_number = %s
                      AND is_latest_record = true
                    LIMIT 1
                """, (in_buy_salesman_number,))
                
                verkaufer_row = cursor.fetchone()
                if verkaufer_row:
                    result['einkaufender_verkaeufer'] = {
                        'nummer': verkaufer_row[0],
                        'name': verkaufer_row[1] or f'Verkäufer #{verkaufer_row[0]}'
                    }
            
            # 3. Hole Kreditor/Lieferant (falls buyer_customer_no vorhanden und is_supplier = true)
            if buyer_customer_no:
                cursor.execute("""
                    SELECT
                        customer_number,
                        COALESCE(family_name || ', ' || first_name, family_name, first_name, 'Unbekannt') as name,
                        is_supplier
                    FROM customers_suppliers
                    WHERE customer_number = %s
                    LIMIT 1
                """, (buyer_customer_no,))
                
                kreditor_row = cursor.fetchone()
                if kreditor_row:
                    is_supplier = kreditor_row[2]
                    if is_supplier:
                        result['kreditor_lieferant'] = {
                            'kundennummer': kreditor_row[0],
                            'name': kreditor_row[1] or f'Kreditor #{kreditor_row[0]}',
                            'is_supplier': True
                        }
                    else:
                        # buyer_customer_no ist vorhanden, aber kein Lieferant
                        result['kreditor_lieferant'] = {
                            'kundennummer': kreditor_row[0],
                            'name': kreditor_row[1] or f'Kunde #{kreditor_row[0]}',
                            'is_supplier': False,
                            'hinweis': 'buyer_customer_no vorhanden, aber kein Lieferant (is_supplier = false)'
                        }
            
            # 4. Einkaufsrechnung
            if in_buy_invoice_no:
                result['einkaufsrechnung'] = {
                    'rechnungsnummer': in_buy_invoice_no,
                    'rechnungsdatum': str(in_buy_invoice_no_date) if in_buy_invoice_no_date else None
                }
            
            # 5. Einkaufsbestellung
            if in_buy_order_no or in_buy_edp_order_no:
                result['einkaufsbestellung'] = {
                    'bestellnummer': in_buy_order_no,
                    'bestelldatum': str(in_buy_order_no_date) if in_buy_order_no_date else None,
                    'edp_bestellnummer': in_buy_edp_order_no,
                    'edp_bestelldatum': str(in_buy_edp_order_no_date) if in_buy_edp_order_no_date else None
                }
            
            # 6. Ex-Halter (previous_owner_number)
            if previous_owner_number:
                cursor.execute("""
                    SELECT
                        customer_number,
                        COALESCE(family_name || ', ' || first_name, family_name, first_name, 'Unbekannt') as name,
                        home_street,
                        home_city,
                        zip_code,
                        country_code,
                        is_supplier
                    FROM customers_suppliers
                    WHERE customer_number = %s
                    LIMIT 1
                """, (previous_owner_number,))
                
                ex_halter_row = cursor.fetchone()
                if ex_halter_row:
                    ex_halter_data = {
                        'kundennummer': ex_halter_row[0],
                        'name': ex_halter_row[1],
                        'adresse': ex_halter_row[2],
                        'ort': ex_halter_row[3],
                        'plz': ex_halter_row[4],
                        'land': ex_halter_row[5],
                        'ist_lieferant': bool(ex_halter_row[6]),
                        'anzahl_vorbesitzer': previous_owner_counter or 1,
                        'telefonnummern': []
                    }
                    
                    # Hole Telefonnummern
                    cursor.execute("""
                        SELECT
                            com_type,
                            phone_number,
                            address
                        FROM customer_com_numbers
                        WHERE customer_number = %s
                        ORDER BY counter
                    """, (previous_owner_number,))
                    
                    telefon_rows = cursor.fetchall()
                    for tel_row in telefon_rows:
                        if tel_row[1]:  # phone_number vorhanden
                            ex_halter_data['telefonnummern'].append({
                                'typ': tel_row[0] or 't',
                                'nummer': tel_row[1],
                                'adresse': tel_row[2]
                            })
                    
                    result['ex_halter'] = ex_halter_data
            
            return jsonify(result)
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================================
# VERKÄUFER PERFORMANCE (NEU TAG159)
# ============================================================================

@verkauf_api.route('/performance', methods=['GET'])
def get_verkaufer_performance():
    """
    GET /api/verkauf/performance?month=12&year=2025&verkaufer=123

    Liefert Performance-Kennzahlen pro Verkäufer
    """
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    verkaufer = request.args.get('verkaufer', type=int)

    result = VerkaufData.get_verkaufer_performance(
        month=month, year=year, verkaufer=verkaufer
    )

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@verkauf_api.route('/nw-pipeline', methods=['GET'])
def get_nw_pipeline():
    """
    GET /api/verkauf/nw-pipeline?standort=1
    
    TAG 181: NW-Pipeline nach Kategorien aufgeteilt für Verkaufsleitung/GL.
    Kategorien:
    - bestellt: Bestellt aber noch nicht eingetroffen
    - verkauft: Mit Vertrag aber noch nicht fakturiert
    - lager: Eingetroffen aber noch nicht verkauft
    """
    from flask_login import current_user
    
    # Prüfe Berechtigung
    if not (current_user.can_access_feature('admin') or 
            current_user.can_access_feature('verkauf')):
        return jsonify({'error': 'Keine Berechtigung'}), 403
    
    standort = request.args.get('standort', type=int)
    
    try:
        result = FahrzeugData.get_nw_pipeline_kategorisiert(standort=standort)
        return jsonify({
            'success': True,
            **result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
