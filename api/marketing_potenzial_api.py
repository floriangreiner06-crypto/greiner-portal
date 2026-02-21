"""
Marketing Potenzial API – Predictive Scoring (Verschleißreparatur Call-Agent)
============================================================================
Liest vehicle_repair_scores + vehicle_km_estimates aus drive_portal.
Anreicherung Halter/Telefon aus Locosoft (vehicles.owner_number → customers_suppliers, customer_com_numbers).
Berechtigung: Feature 'marketing_potenzial' (in Rechteverwaltung vergeben).
"""

import csv
import io
from flask import Blueprint, jsonify, request, Response
from flask_login import current_user

from api.db_utils import db_session, locosoft_session

marketing_potenzial_api = Blueprint('marketing_potenzial_api', __name__)


def _enrich_holder_phone(vehicle_numbers):
    """
    Liest aus Locosoft: Halter (first_name, family_name) und eine Telefonnummer pro Kunde.
    Returns: dict vehicle_number -> {'holder_name': str, 'holder_phone': str}
    """
    if not vehicle_numbers:
        return {}
    vehicle_numbers = list(set(vehicle_numbers))
    result = {vn: {'holder_name': '', 'holder_phone': ''} for vn in vehicle_numbers}
    try:
        with locosoft_session() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT internal_number, owner_number FROM vehicles WHERE internal_number = ANY(%s)",
                (vehicle_numbers,)
            )
            v2owner = {r[0]: r[1] for r in cur.fetchall() if r[1] is not None}
            owner_numbers = list(set(v2owner.values()))
            if not owner_numbers:
                return result
            cur.execute(
                """SELECT customer_number, TRIM(COALESCE(first_name, '') || ' ' || COALESCE(family_name, ''))
                   FROM customers_suppliers WHERE customer_number = ANY(%s)""",
                (owner_numbers,)
            )
            owner_name = {r[0]: (r[1] or '').strip() or '-' for r in cur.fetchall()}
            cur.execute(
                """SELECT DISTINCT ON (customer_number) customer_number, phone_number
                   FROM customer_com_numbers
                   WHERE customer_number = ANY(%s) AND phone_number IS NOT NULL AND TRIM(phone_number) != ''
                   ORDER BY customer_number, counter""",
                (owner_numbers,)
            )
            owner_phone = {r[0]: (r[1] or '').strip() for r in cur.fetchall()}
            for vn, owner in v2owner.items():
                result[vn]['holder_name'] = owner_name.get(owner, '') or '-'
                result[vn]['holder_phone'] = owner_phone.get(owner, '') or ''
    except Exception:
        pass
    return result


def _check_access():
    if not current_user.is_authenticated:
        return False, 401
    if not current_user.can_access_feature('marketing_potenzial'):
        return False, 403
    return True, None


def _mileage_to_km(val):
    """Werte > 500k aus Locosoft als Meter interpretieren."""
    if val is None:
        return None
    if val > 500_000:
        return int(val / 1000)
    return val


@marketing_potenzial_api.route('/api/marketing/potenzial/detail/<int:vehicle_number>', methods=['GET'])
def detail(vehicle_number):
    """
    GET /api/marketing/potenzial/detail/<vehicle_number>
    Kunden- und Fahrzeugdaten aus Locosoft für das Info-Modal.
    """
    ok, err = _check_access()
    if not ok:
        return jsonify({'error': 'Nicht berechtigt'}), err
    try:
        with locosoft_session() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    v.internal_number, v.license_plate, v.vin,
                    v.first_registration_date, v.production_year,
                    v.mileage_km, v.odometer_reading_date,
                    v.next_service_date, v.next_service_km,
                    v.owner_number, v.subsidiary,
                    COALESCE(m.description, v.free_form_make_text) AS make,
                    v.free_form_model_text AS model
                FROM vehicles v
                LEFT JOIN makes m ON m.make_number = v.make_number
                WHERE v.internal_number = %s
            """, (vehicle_number,))
            row = cur.fetchone()
            if not row:
                return jsonify({
                    'vehicle': None,
                    'customer': None,
                    'last_invoice': None,
                    'not_found': True,
                    'message': 'Zu dieser Fzg-Nr. sind in Locosoft keine Stammdaten (mehr) vorhanden. Möglicherweise wurde das Fahrzeug ausgebucht oder die Nummer stammt aus einer älteren Auswertung.'
                }), 200
            vehicle = {
                'vehicle_number': row[0],
                'license_plate': row[1] or '',
                'vin': row[2] or '',
                'first_registration_date': row[3].isoformat() if row[3] else None,
                'production_year': int(row[4]) if row[4] is not None else None,
                'mileage_km': _mileage_to_km(row[5]),
                'odometer_reading_date': row[6].isoformat() if row[6] else None,
                'next_service_date': row[7].isoformat() if row[7] else None,
                'next_service_km': _mileage_to_km(row[8]) if row[8] else None,
                'owner_number': row[9],
                'subsidiary': row[10],
                'make': row[11] or '',
                'model': row[12] or '',
            }
            owner_number = row[9]
            customer = None
            if owner_number:
                cur.execute("""
                    SELECT customer_number, name_prefix, first_name, family_name, name_postfix,
                           home_street, zip_code, home_city, country_code
                    FROM customers_suppliers WHERE customer_number = %s
                """, (owner_number,))
                cust_row = cur.fetchone()
                if cust_row:
                    customer = {
                        'customer_number': cust_row[0],
                        'name_prefix': cust_row[1] or '',
                        'first_name': cust_row[2] or '',
                        'family_name': cust_row[3] or '',
                        'name_postfix': cust_row[4] or '',
                        'full_name': ' '.join(
                            filter(None, [cust_row[1], cust_row[2], cust_row[3], cust_row[4]])
                        ).strip() or '-',
                        'home_street': cust_row[5] or '',
                        'zip_code': cust_row[6] or '',
                        'home_city': cust_row[7] or '',
                        'country_code': cust_row[8] or '',
                        'phones': [],
                        'emails': [],
                    }
                    cur.execute("""
                        SELECT com_type, phone_number, address
                        FROM customer_com_numbers
                        WHERE customer_number = %s
                        ORDER BY counter
                    """, (owner_number,))
                    for ct, phone, addr in cur.fetchall():
                        if phone and str(phone).strip():
                            customer['phones'].append(str(phone).strip())
                        if addr and str(addr).strip() and '@' in str(addr):
                            customer['emails'].append(str(addr).strip())
            # Letzte Rechnung (Auftragsrechnung) für dieses Fahrzeug
            cur.execute("""
                SELECT invoice_type, invoice_number, invoice_date, service_date,
                       order_number, total_net, total_gross, odometer_reading
                FROM invoices
                WHERE vehicle_number = %s
                  AND (is_canceled IS NOT TRUE OR is_canceled IS NULL)
                ORDER BY invoice_date DESC NULLS LAST
                LIMIT 1
            """, (vehicle_number,))
            inv_row = cur.fetchone()
            last_invoice = None
            if inv_row:
                last_invoice = {
                    'invoice_type': inv_row[0],
                    'invoice_number': inv_row[1],
                    'invoice_date': inv_row[2].isoformat() if inv_row[2] else None,
                    'service_date': inv_row[3].isoformat() if inv_row[3] else None,
                    'order_number': inv_row[4],
                    'total_net': float(inv_row[5]) if inv_row[5] is not None else None,
                    'total_gross': float(inv_row[6]) if inv_row[6] is not None else None,
                    'odometer_reading': _mileage_to_km(inv_row[7]) if inv_row[7] is not None else None,
                }
            return jsonify({'vehicle': vehicle, 'customer': customer, 'last_invoice': last_invoice})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@marketing_potenzial_api.route('/api/marketing/potenzial/categories', methods=['GET'])
def list_categories():
    """GET /api/marketing/potenzial/categories – Reparaturkategorien."""
    ok, err = _check_access()
    if not ok:
        return jsonify({'error': 'Nicht berechtigt'}), err
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT category_id, name, interval_km, interval_years
            FROM repair_categories
            ORDER BY category_id
        """)
        rows = cur.fetchall()
    items = [
        {
            'category_id': r[0],
            'name': r[1],
            'interval_km': r[2],
            'interval_years': r[3],
        }
        for r in rows
    ]
    return jsonify({'categories': items})


@marketing_potenzial_api.route('/api/marketing/potenzial/stats', methods=['GET'])
def stats():
    """GET /api/marketing/potenzial/stats – Anzahl nach Priorität/Kategorie."""
    ok, err = _check_access()
    if not ok:
        return jsonify({'error': 'Nicht berechtigt'}), err
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT priority, COUNT(*) FROM vehicle_repair_scores GROUP BY priority
        """)
        by_priority = {r[0]: r[1] for r in cur.fetchall()}
        cur.execute("""
            SELECT category_id, COUNT(*) FROM vehicle_repair_scores GROUP BY category_id
        """)
        by_category = {r[0]: r[1] for r in cur.fetchall()}
        cur.execute("SELECT COUNT(*) FROM vehicle_km_estimates")
        vehicles_with_km = cur.fetchone()[0]
    return jsonify({
        'by_priority': by_priority,
        'by_category': by_category,
        'vehicles_with_km_estimate': vehicles_with_km,
    })


@marketing_potenzial_api.route('/api/marketing/potenzial/list', methods=['GET'])
def list_scores():
    """
    GET /api/marketing/potenzial/list
    Query: subsidiary (int), category_id, priority, confidence (HIGH|MEDIUM|LOW), limit (default 500).
    """
    ok, err = _check_access()
    if not ok:
        return jsonify({'error': 'Nicht berechtigt'}), err
    subsidiary = request.args.get('subsidiary', type=int)
    category_id = request.args.get('category_id')
    priority = request.args.get('priority')
    confidence = request.args.get('confidence')
    limit = min(request.args.get('limit', 500, type=int), 5000)

    conditions = ["1=1"]
    params = []
    if subsidiary is not None:
        conditions.append("s.subsidiary = %s")
        params.append(subsidiary)
    if category_id:
        conditions.append("s.category_id = %s")
        params.append(category_id)
    if priority:
        conditions.append("s.priority = %s")
        params.append(priority)
    if confidence:
        conditions.append("e.confidence = %s")
        params.append(confidence)
    params.append(limit)

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                s.vehicle_number, s.category_id, s.subsidiary,
                s.last_service_date, s.last_service_km, s.estimated_current_km,
                s.km_since_service, s.years_since_service, s.score_combined,
                s.priority, s.recommended_action,
                e.confidence, e.km_per_year_estimate
            FROM vehicle_repair_scores s
            LEFT JOIN vehicle_km_estimates e ON e.vehicle_number = s.vehicle_number
            WHERE """ + " AND ".join(conditions) + """
            ORDER BY s.priority DESC, s.score_combined DESC NULLS LAST
            LIMIT %s
        """, params)
        rows = cur.fetchall()

    items = []
    for r in rows:
        items.append({
            'vehicle_number': r[0],
            'category_id': r[1],
            'subsidiary': r[2],
            'last_service_date': r[3].isoformat() if r[3] else None,
            'last_service_km': r[4],
            'estimated_current_km': r[5],
            'km_since_service': r[6],
            'years_since_service': round(r[7], 1) if r[7] is not None else None,
            'score_combined': round(r[8], 2) if r[8] is not None else None,
            'priority': r[9],
            'recommended_action': r[10],
            'confidence': r[11],
            'km_per_year_estimate': r[12],
        })
    vehicle_numbers = [it['vehicle_number'] for it in items]
    enrich = _enrich_holder_phone(vehicle_numbers)
    for it in items:
        vn = it['vehicle_number']
        it['holder_name'] = enrich.get(vn, {}).get('holder_name', '')
        it['holder_phone'] = enrich.get(vn, {}).get('holder_phone', '')
    return jsonify({'items': items, 'count': len(items)})


@marketing_potenzial_api.route('/api/marketing/potenzial/export.csv', methods=['GET'])
def export_csv():
    """
    GET /api/marketing/potenzial/export.csv
    Gleiche Filter wie list (subsidiary, category_id, priority, confidence); limit max 10000.
    """
    ok, err = _check_access()
    if not ok:
        return Response('Nicht berechtigt', status=err)
    subsidiary = request.args.get('subsidiary', type=int)
    category_id = request.args.get('category_id')
    priority = request.args.get('priority')
    confidence = request.args.get('confidence')
    limit = min(request.args.get('limit', 5000, type=int), 10000)

    conditions = ["1=1"]
    params = []
    if subsidiary is not None:
        conditions.append("s.subsidiary = %s")
        params.append(subsidiary)
    if category_id:
        conditions.append("s.category_id = %s")
        params.append(category_id)
    if priority:
        conditions.append("s.priority = %s")
        params.append(priority)
    if confidence:
        conditions.append("e.confidence = %s")
        params.append(confidence)
    params.append(limit)

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                s.vehicle_number, s.category_id, s.subsidiary,
                s.last_service_date, s.last_service_km, s.estimated_current_km,
                s.km_since_service, s.years_since_service, s.score_combined,
                s.priority, s.recommended_action,
                e.confidence, e.km_per_year_estimate
            FROM vehicle_repair_scores s
            LEFT JOIN vehicle_km_estimates e ON e.vehicle_number = s.vehicle_number
            WHERE """ + " AND ".join(conditions) + """
            ORDER BY s.priority DESC, s.score_combined DESC NULLS LAST
            LIMIT %s
        """, params)
        rows = cur.fetchall()

    vehicle_numbers = [r[0] for r in rows]
    enrich = _enrich_holder_phone(vehicle_numbers)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        'vehicle_number', 'category_id', 'subsidiary', 'holder_name', 'holder_phone',
        'last_service_date', 'last_service_km', 'estimated_current_km',
        'km_since_service', 'years_since_service', 'score_combined',
        'priority', 'recommended_action', 'confidence', 'km_per_year_estimate'
    ])
    for r in rows:
        vn = r[0]
        hn = enrich.get(vn, {}).get('holder_name', '')
        hp = enrich.get(vn, {}).get('holder_phone', '')
        writer.writerow([
            vn, r[1], r[2], hn, hp,
            r[3].isoformat() if r[3] else '',
            r[4], r[5], r[6], round(r[7], 2) if r[7] is not None else '',
            round(r[8], 2) if r[8] is not None else '', r[9], r[10] or '', r[11], r[12]
        ])
    return Response(
        buf.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=marketing_potenzial_scores.csv'}
    )
