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
from flask_login import login_required, current_user
from datetime import datetime, date
from typing import Dict, List
import json
import time
from pathlib import Path

# Zentrale DB-Utilities (für interne Aufträge)
from api.db_utils import locosoft_session, db_session

# SSOT Data Module
from api.verkauf_data import VerkaufData

# Blueprint erstellen
verkauf_api = Blueprint('verkauf_api', __name__, url_prefix='/api/verkauf')

# TAG 181: Import für NW-Pipeline
from api.fahrzeug_data import FahrzeugData


# ============================================================================
# Verkäufer-Filter: Rolle "verkauf" nur eigene Daten, Filter nicht auflösbar
# ============================================================================

def _get_current_user_salesman_number():
    """Locosoft-Mitarbeiternummer (VKB) des eingeloggten Users für Verkäufer-Filter."""
    if not current_user.is_authenticated:
        return None
    username = getattr(current_user, 'username', '') or ''
    ldap_username = username.split('@')[0] if '@' in username else username
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT lem.locosoft_id
            FROM ldap_employee_mapping lem
            JOIN employees e ON lem.employee_id = e.id
            WHERE lem.ldap_username = %s AND e.aktiv = true
        """, (ldap_username,))
        row = cur.fetchone()
    if row and row[0] is not None:
        return int(row[0])
    return None


def _filter_mode_force_own(feature: str):
    """True wenn für aktuelle Rolle + Feature nur eigene Daten (Filter nicht auflösbar)."""
    if not current_user.is_authenticated:
        return False
    from api.feature_filter_mode import get_filter_mode
    role = getattr(current_user, 'portal_role', '') or 'mitarbeiter'
    return get_filter_mode(role, feature) == 'own_only'


# Interne Kundennummern (Autohaus Greiner selbst)
# 3000001 = Autohaus Greiner GmbH (Opel/Stellantis)
# 3000002 = Auto Greiner GmbH & Co. KG (Hyundai)
INTERNE_KUNDEN = (3000001, 3000002)

_MOTOCOST_DIR = Path(__file__).resolve().parent.parent / 'data' / 'imports' / 'motocost'
_MOTOCOST_LATEST_FILE = _MOTOCOST_DIR / 'latest.json'


def _can_access_motocost() -> bool:
    """Motocost-View: vorerst für VKL/GF/Admin über bestehendes Feature."""
    return bool(
        hasattr(current_user, 'can_access_feature')
        and current_user.can_access_feature('verkauf_dashboard')
    )


def _normalize_motocost_rows(raw):
    """Normalisiert die importierten Zeilen auf eine robuste Standard-Struktur."""
    if not isinstance(raw, list):
        raise ValueError('Erwartet JSON-Array mit Fahrzeugzeilen')

    normalized = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        normalized.append({
            'bild': row.get('Bild') or row.get('bild') or '',
            'marke': row.get('Marke') or row.get('marke') or '',
            'modell': row.get('Modell') or row.get('modell') or '',
            'preis': row.get('Preis') or row.get('preis'),
            'mwst': row.get('MwSt') or row.get('mwst') or '',
            'rabatt': row.get('Rabatt') or row.get('rabatt'),
            'marge': row.get('Marge') or row.get('marge'),
            'p10': row.get('P10') or row.get('p10'),
            'median': row.get('Median') or row.get('median'),
            'anzahl': row.get('Anzahl') or row.get('anzahl'),
            'plattform': row.get('Plattform') or row.get('plattform') or '',
            'verkaufsart': row.get('Verkaufsart') or row.get('verkaufsart') or '',
            'problem': row.get('Problem') or row.get('problem') or '',
            'ez': row.get('EZ') or row.get('ez') or '',
            'km': row.get('KM') or row.get('km'),
            'kraftstoff': row.get('Kraftstoff') or row.get('kraftstoff') or '',
            'getriebe': row.get('Getriebe') or row.get('getriebe') or '',
            'ps': row.get('PS') or row.get('ps'),
            'karosserie': row.get('Karosserie') or row.get('karosserie') or '',
            'land': row.get('Land') or row.get('land') or '',
            'start': row.get('Start') or row.get('start') or '',
            'ende': row.get('Ende') or row.get('ende') or '',
            'link': row.get('Link') or row.get('link') or '',
            'bestandsnummer': row.get('Bestandsnummer') or row.get('bestandsnummer') or '',
            'problembeschreibung': row.get('Problembeschreibung') or row.get('problembeschreibung') or '',
            'modellbeschreibung': row.get('Modellbeschreibung') or row.get('modellbeschreibung') or '',
        })
    return normalized


def _load_motocost_rows_and_meta():
    if not _MOTOCOST_LATEST_FILE.exists():
        return [], {'available': False}
    with _MOTOCOST_LATEST_FILE.open('r', encoding='utf-8') as fh:
        payload = json.load(fh)
    rows = payload.get('rows') if isinstance(payload, dict) else payload
    rows = _normalize_motocost_rows(rows)
    meta = payload.get('meta', {}) if isinstance(payload, dict) else {}
    return rows, {**meta, 'available': True}


def _as_float(value):
    if value is None or value == '':
        return None
    try:
        return float(value)
    except Exception:
        return None


def _as_int(value):
    if value is None or value == '':
        return None
    try:
        return int(float(value))
    except Exception:
        return None


def _extract_year(value):
    """EZ kann Epoch-ms oder String sein (z. B. MM/YYYY)."""
    if value is None or value == '':
        return None
    # Epoch milliseconds
    if isinstance(value, (int, float)) and value > 1000000000:
        try:
            return datetime.fromtimestamp(float(value) / 1000.0).year
        except Exception:
            return None
    text = str(value).strip()
    if not text:
        return None
    if len(text) >= 4 and text[:4].isdigit():
        return int(text[:4])
    if '/' in text:
        tail = text.split('/')[-1]
        if tail.isdigit() and len(tail) == 4:
            return int(tail)
    if text.isdigit() and len(text) == 4:
        return int(text)
    return None


def _contains_any(value, selected):
    if not selected:
        return True
    val = (value or '').strip().lower()
    return val in selected


def _split_multi(param_name):
    raw = (request.args.get(param_name, '') or '').strip()
    if not raw:
        return []
    return [x.strip().lower() for x in raw.split(',') if x.strip()]


def _build_motocost_filter_options(rows):
    def uniq(key):
        vals = sorted({str(r.get(key) or '').strip() for r in rows if str(r.get(key) or '').strip()})
        return vals[:500]
    return {
        'plattformen': uniq('plattform'),
        'verkaufsarten': uniq('verkaufsart'),
        'probleme': uniq('problem'),
        'laender': uniq('land'),
        'marken': uniq('marke'),
        'modelle': uniq('modell'),
        'kraftstoff': uniq('kraftstoff'),
        'getriebe': uniq('getriebe'),
        'karosserie': uniq('karosserie'),
        'mwst': uniq('mwst'),
    }


def _apply_motocost_filters(rows):
    text_modell = (request.args.get('modell_text', '') or '').strip().lower()
    page = max(1, request.args.get('page', 1, type=int) or 1)
    page_size = min(200, max(10, request.args.get('page_size', 50, type=int) or 50))

    plattform = _split_multi('plattform')
    verkaufsart = _split_multi('verkaufsart')
    problem = _split_multi('problem')
    land = _split_multi('land')
    marke = _split_multi('marke')
    kraftstoff = _split_multi('kraftstoff')
    getriebe = _split_multi('getriebe')
    karosserie = _split_multi('karosserie')
    mwst = _split_multi('mwst')

    km_bis = _as_int(request.args.get('km_bis'))
    ez_ab = _as_int(request.args.get('ez_ab'))
    marge_ab = _as_float(request.args.get('marge_ab'))
    preis_ab = _as_float(request.args.get('preis_ab'))
    preis_bis = _as_float(request.args.get('preis_bis'))

    filtered = []
    for row in rows:
        if not _contains_any(row.get('plattform'), plattform):
            continue
        if not _contains_any(row.get('verkaufsart'), verkaufsart):
            continue
        if not _contains_any(row.get('problem'), problem):
            continue
        if not _contains_any(row.get('land'), land):
            continue
        if not _contains_any(row.get('marke'), marke):
            continue
        if not _contains_any(row.get('kraftstoff'), kraftstoff):
            continue
        if not _contains_any(row.get('getriebe'), getriebe):
            continue
        if not _contains_any(row.get('karosserie'), karosserie):
            continue
        if not _contains_any(row.get('mwst'), mwst):
            continue

        if text_modell and text_modell not in str(row.get('modell') or '').lower():
            continue

        km = _as_int(row.get('km'))
        if km_bis is not None and (km is None or km > km_bis):
            continue

        jahr = _extract_year(row.get('ez'))
        if ez_ab is not None and (jahr is None or jahr < ez_ab):
            continue

        marge = _as_float(row.get('marge'))
        if marge_ab is not None and (marge is None or marge < marge_ab):
            continue

        preis = _as_float(row.get('preis'))
        if preis_ab is not None and (preis is None or preis < preis_ab):
            continue
        if preis_bis is not None and (preis is None or preis > preis_bis):
            continue

        filtered.append(row)

    filtered.sort(key=lambda r: (_as_float(r.get('marge')) is None, -(_as_float(r.get('marge')) or 0)))

    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = filtered[start:end]
    return page_rows, total, page, page_size


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

    Liefert Auftragseingang nach Verkäufern.
    Rolle „verkauf“: nur eigener Verkäufer, Filter nicht auflösbar.
    """
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    location = request.args.get('location', type=int)
    verkaufer = request.args.get('verkaufer', type=int)
    if _filter_mode_force_own('auftragseingang'):
        verkaufer = _get_current_user_salesman_number()
    result = VerkaufData.get_auftragseingang(month=month, year=year, location=location, verkaufer=verkaufer)

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
    Rolle „verkauf“: nur eigener Verkäufer.
    """
    day = request.args.get('day', '') or None
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    location = request.args.get('location', type=int)
    verkaufer = request.args.get('verkaufer', type=int)
    if _filter_mode_force_own('auftragseingang'):
        verkaufer = _get_current_user_salesman_number()
    result = VerkaufData.get_auftragseingang_summary(day=day, month=month, year=year, location=location, verkaufer=verkaufer)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@verkauf_api.route('/auftragseingang/detail', methods=['GET'])
@login_required
def get_auftragseingang_detail():
    """
    GET /api/verkauf/auftragseingang/detail?month=11&year=2025&location=&verkaufer=
    Rolle „verkauf“: nur eigener Verkäufer, Filter nicht auflösbar.
    """
    day = request.args.get('day', '') or None
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    location = request.args.get('location', type=int)
    verkaufer = request.args.get('verkaufer', type=int)
    if _filter_mode_force_own('auftragseingang'):
        verkaufer = _get_current_user_salesman_number()

    result = VerkaufData.get_auftragseingang_detail(
        day=day, month=month, year=year,
        location=location, verkaufer=verkaufer
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
    Rolle „verkauf“: nur eigener Verkäufer.
    """
    day = request.args.get('day', '') or None
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    verkaufer = request.args.get('verkaufer', type=int)
    if _filter_mode_force_own('auslieferungen'):
        verkaufer = _get_current_user_salesman_number()
    result = VerkaufData.get_auslieferung_summary(day=day, month=month, year=year, verkaufer=verkaufer)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@verkauf_api.route('/auslieferung/detail', methods=['GET'])
@login_required
def get_auslieferung_detail():
    """
    GET /api/verkauf/auslieferung/detail?month=11&year=2025&location=&verkaufer=&vin=
    Rolle „verkauf“: nur eigener Verkäufer, Filter nicht auflösbar.
    """
    day = request.args.get('day', '') or None
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    location = request.args.get('location', type=int)
    verkaufer = request.args.get('verkaufer', type=int)
    vin_search = request.args.get('vin', '') or None
    if _filter_mode_force_own('auslieferungen'):
        verkaufer = _get_current_user_salesman_number()

    result = VerkaufData.get_auslieferung_detail(
        day=day, month=month, year=year,
        location=location, verkaufer=verkaufer, vin_search=vin_search
    )

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


# ============================================================================
# AUFTRAGSEINGANG FAHRZEUGE (Nutzt gleiche Logik wie Detail)
# ============================================================================

@verkauf_api.route('/auftragseingang/fahrzeuge', methods=['GET'])
@login_required
def get_auftragseingang_fahrzeuge():
    """
    GET /api/verkauf/auftragseingang/fahrzeuge?month=11&year=2025&location=&verkaufer=&vin=
    Rolle „verkauf“: nur eigener Verkäufer.
    """
    day = request.args.get('day', '') or None
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    location = request.args.get('location', type=int)
    verkaufer = request.args.get('verkaufer', type=int)
    vin_search = request.args.get('vin', '') or None
    if _filter_mode_force_own('auftragseingang'):
        verkaufer = _get_current_user_salesman_number()

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


# ============================================================================
# MOTOCOST IMPORT (Workaround ohne API-Key)
# ============================================================================

@verkauf_api.route('/motocost/data', methods=['GET'])
@login_required
def get_motocost_data():
    """
    GET /api/verkauf/motocost/data
    Liefert zuletzt importierte Motocost-Zeilen aus lokalem JSON.
    """
    try:
        if not _can_access_motocost():
            return jsonify({'success': False, 'error': 'Kein Zugriff'}), 403
        rows, meta = _load_motocost_rows_and_meta()
        return jsonify({'success': True, 'rows': rows, 'meta': meta})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@verkauf_api.route('/motocost/search', methods=['GET'])
@login_required
def search_motocost_data():
    """
    GET /api/verkauf/motocost/search?...Filter...
    Serverseitige Filterung + Paging + Benchmark-Messung.
    """
    t0 = time.perf_counter()
    try:
        if not _can_access_motocost():
            return jsonify({'success': False, 'error': 'Kein Zugriff'}), 403

        rows, meta = _load_motocost_rows_and_meta()
        page_rows, total, page, page_size = _apply_motocost_filters(rows)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

        return jsonify({
            'success': True,
            'rows': page_rows,
            'meta': meta,
            'total': total,
            'page': page,
            'page_size': page_size,
            'elapsed_ms': elapsed_ms,
            'filter_options': _build_motocost_filter_options(rows),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@verkauf_api.route('/motocost/import', methods=['POST'])
@login_required
def import_motocost_data():
    """
    POST /api/verkauf/motocost/import
    Akzeptiert JSON-Datei-Upload (multipart: file) ODER JSON-Body mit {"rows":[...]}.
    """
    try:
        if not _can_access_motocost():
            return jsonify({'success': False, 'error': 'Kein Zugriff'}), 403

        incoming_rows = None
        if 'file' in request.files:
            file = request.files.get('file')
            if not file or not file.filename:
                return jsonify({'success': False, 'error': 'Keine Datei empfangen'}), 400
            raw_payload = json.loads(file.read().decode('utf-8'))
            incoming_rows = raw_payload.get('rows') if isinstance(raw_payload, dict) else raw_payload
        else:
            body = request.get_json(silent=True) or {}
            incoming_rows = body.get('rows') if isinstance(body, dict) else body

        rows = _normalize_motocost_rows(incoming_rows)
        if not rows:
            return jsonify({'success': False, 'error': 'Keine verwertbaren Fahrzeugzeilen gefunden'}), 400

        _MOTOCOST_DIR.mkdir(parents=True, exist_ok=True)
        now_iso = datetime.now().isoformat(timespec='seconds')
        payload = {
            'meta': {
                'imported_at': now_iso,
                'imported_by': getattr(current_user, 'username', 'unbekannt'),
                'row_count': len(rows),
            },
            'rows': rows,
        }
        with _MOTOCOST_LATEST_FILE.open('w', encoding='utf-8') as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)

        # Historie-Datei für Rückfall bei Demo
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        history_file = _MOTOCOST_DIR / f'motocost_{stamp}.json'
        with history_file.open('w', encoding='utf-8') as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)

        return jsonify({
            'success': True,
            'message': f'{len(rows)} Zeilen importiert',
            'meta': payload['meta'],
            'path': str(_MOTOCOST_LATEST_FILE),
        })
    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': 'Ungültiges JSON-Format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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
# VERKAUFSLEITER-DASHBOARD (Aggregat, SSOT)
# ============================================================================

@verkauf_api.route('/dashboard-vkl', methods=['GET'])
@login_required
def get_dashboard_vkl():
    """
    GET /api/verkauf/dashboard-vkl
    KPIs für VKL/GF/Admin; AfA und EKF nur bei passendem Feature.
    """
    try:
        if not (
            hasattr(current_user, 'can_access_feature')
            and current_user.can_access_feature('verkauf_dashboard')
        ):
            return jsonify({'success': False, 'error': 'Kein Zugriff'}), 403
        include_afa = current_user.can_access_feature('afa_verkaufsempfehlungen')
        include_ekf = current_user.can_access_feature('einkaufsfinanzierung')
        from api.verkauf_vkl_dashboard_service import build_vkl_dashboard_payload

        ytd_mode = (request.args.get('ytd_mode', 'calendar') or 'calendar').lower()
        if ytd_mode not in ('calendar', 'fiscal'):
            ytd_mode = 'calendar'
        data = build_vkl_dashboard_payload(include_afa=include_afa, include_ekf=include_ekf, ytd_mode=ytd_mode)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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
