#!/usr/bin/env python3
"""
BUDGET PLANUNG API - Verkaufsplanung NW/GW
==========================================
Einfache, verkaufsleiter-freundliche Budget-Planung.

DATENBANKEN:
- IST-Daten: PostgreSQL Locosoft (10.80.80.8:5432/loco_auswertung_db)
  → dealer_vehicles Tabelle
- PLAN-Daten: PostgreSQL DRIVE Portal (127.0.0.1:5432/drive_portal)
  → budget_plan Tabelle

Features:
- Automatische Benchmarks aus Locosoft-Historiedaten
- Saisonalität berücksichtigt (Vorjahres-Verteilung)
- Interaktive Anpassung (Wachstum 0-20%)
- IST vs PLAN mit Ampel-System

Endpoints:
- GET  /api/budget/dashboard              - Übersicht aktuelles Jahr
- GET  /api/budget/benchmark/<jahr>       - Smarte Benchmark-Vorschläge
- GET  /api/budget/plan/<jahr>            - Gespeicherte Planung
- POST /api/budget/plan/<jahr>            - Planung speichern
- POST /api/budget/plan/<jahr>/apply-benchmark - Benchmark übernehmen
- GET  /api/budget/vergleich/<jahr>       - IST vs PLAN
- GET  /api/budget/verkaufer/<jahr>       - Pro Verkäufer

Author: Claude
Date: 2025-12-29 (TAG 143)
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, jsonify, request
from psycopg2.extras import RealDictCursor

from api.db_connection import get_db
from api.db_utils import get_locosoft_connection

logger = logging.getLogger(__name__)

budget_bp = Blueprint('budget', __name__, url_prefix='/api/budget')

MONATE = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

# Standort-Mapping (Locosoft out_subsidiary)
STANDORTE = {
    1: {'name': 'Deggendorf Opel', 'kurz': 'DEG'},
    2: {'name': 'Deggendorf Hyundai', 'kurz': 'HYU'},
    3: {'name': 'Landau', 'kurz': 'LAN'}
}


# ============================================================================
# DB-TABELLEN (PostgreSQL - drive_portal DB)
# ============================================================================

def init_budget_tables():
    """
    Erstellt Budget-Tabellen in PostgreSQL (drive_portal).

    Tabelle: budget_plan
    - Speichert Verkaufsziele pro Jahr/Monat/Standort/Typ (NW/GW)
    - UPSERT via ON CONFLICT für Updates
    """
    conn = get_db()  # PostgreSQL via DB_TYPE=postgresql
    cursor = conn.cursor()

    # PostgreSQL-Syntax: SERIAL, DECIMAL, TIMESTAMP, ON CONFLICT
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budget_plan (
            id SERIAL PRIMARY KEY,
            jahr INTEGER NOT NULL,
            monat INTEGER NOT NULL,
            standort INTEGER NOT NULL,
            typ VARCHAR(2) NOT NULL CHECK (typ IN ('NW', 'GW')),
            stueck_plan INTEGER DEFAULT 0,
            umsatz_plan DECIMAL(15,2) DEFAULT 0,
            db1_plan DECIMAL(15,2) DEFAULT 0,
            marge_plan DECIMAL(5,2) DEFAULT 0,
            kommentar TEXT,
            erstellt_von VARCHAR(100),
            erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(jahr, monat, standort, typ)
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_budget_jahr ON budget_plan(jahr)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_budget_jahr_standort ON budget_plan(jahr, standort)')
    conn.commit()
    conn.close()
    logger.info("PostgreSQL: Budget-Tabellen initialisiert (drive_portal.budget_plan)")


# ============================================================================
# LOCOSOFT IST-DATEN
# ============================================================================

def get_ist_daten_locosoft(jahr, standort=None):
    """Holt IST-Verkaufsdaten aus Locosoft."""
    conn = get_locosoft_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT
            monat,
            standort,
            typ,
            SUM(stueck) as stueck,
            SUM(umsatz) as umsatz,
            AVG(avg_preis) as avg_preis
        FROM (
            SELECT
                EXTRACT(MONTH FROM out_invoice_date)::int as monat,
                out_subsidiary as standort,
                CASE
                    WHEN dealer_vehicle_type IN ('N', 'V') THEN 'NW'
                    WHEN dealer_vehicle_type IN ('D', 'G') THEN 'GW'
                END as typ,
                1 as stueck,
                COALESCE(out_sale_price, 0) as umsatz,
                COALESCE(out_sale_price, 0) as avg_preis
            FROM dealer_vehicles
            WHERE EXTRACT(YEAR FROM out_invoice_date) = %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('N', 'V', 'D', 'G')
    """
    params = [jahr]

    if standort:
        query += " AND out_subsidiary = %s"
        params.append(standort)

    query += """
        ) sub
        GROUP BY monat, standort, typ
        ORDER BY monat, standort, typ
    """

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return rows


# ============================================================================
# DASHBOARD
# ============================================================================

@budget_bp.route('/dashboard')
def dashboard():
    """Übersicht: Aktuelles Jahr IST vs PLAN."""
    jahr = request.args.get('jahr', datetime.now().year, type=int)

    try:
        # IST-Daten
        ist_rows = get_ist_daten_locosoft(jahr)

        # Strukturieren nach Monat
        result = {
            'jahr': jahr,
            'monate': {},
            'gesamt': {
                'nw': {'ist_stueck': 0, 'plan_stueck': 0},
                'gw': {'ist_stueck': 0, 'plan_stueck': 0}
            }
        }

        for m in range(1, 13):
            result['monate'][m] = {
                'monat': m,
                'name': MONATE[m-1],
                'nw': {'ist_stueck': 0, 'ist_umsatz': 0, 'plan_stueck': 0, 'plan_umsatz': 0},
                'gw': {'ist_stueck': 0, 'ist_umsatz': 0, 'plan_stueck': 0, 'plan_umsatz': 0}
            }

        for row in ist_rows:
            m = row['monat']
            typ = row['typ'].lower()
            if m in result['monate']:
                result['monate'][m][typ]['ist_stueck'] += int(row['stueck'])
                result['monate'][m][typ]['ist_umsatz'] += float(row['umsatz'])

        # PLAN-Daten laden
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT monat, typ, SUM(stueck_plan) as stueck, SUM(umsatz_plan) as umsatz
            FROM budget_plan
            WHERE jahr = %s
            GROUP BY monat, typ
        ''', (jahr,))
        plan_rows = cursor.fetchall()
        conn.close()

        for row in plan_rows:
            m = row['monat']
            typ = row['typ'].lower()
            if m in result['monate']:
                result['monate'][m][typ]['plan_stueck'] = int(row['stueck'] or 0)
                result['monate'][m][typ]['plan_umsatz'] = float(row['umsatz'] or 0)

        # Summen
        for m_data in result['monate'].values():
            result['gesamt']['nw']['ist_stueck'] += m_data['nw']['ist_stueck']
            result['gesamt']['nw']['plan_stueck'] += m_data['nw']['plan_stueck']
            result['gesamt']['gw']['ist_stueck'] += m_data['gw']['ist_stueck']
            result['gesamt']['gw']['plan_stueck'] += m_data['gw']['plan_stueck']

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        logger.error(f"Dashboard Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# SMARTE BENCHMARKS
# ============================================================================

@budget_bp.route('/benchmark/<int:jahr>')
def benchmark(jahr):
    """
    Generiert smarte Benchmark-Vorschläge:
    1. Basiert auf Vorjahr (Saisonalität)
    2. Berücksichtigt Trend der letzten 2 Jahre
    3. Wachstumsziel einstellbar
    """
    wachstum = request.args.get('wachstum', 5, type=float) / 100  # Default: 5%
    standort = request.args.get('standort', type=int)

    try:
        vorjahr = jahr - 1
        vorvorjahr = jahr - 2

        # Vorjahres-Daten
        vj_daten = get_ist_daten_locosoft(vorjahr, standort)
        vvj_daten = get_ist_daten_locosoft(vorvorjahr, standort)

        # Strukturieren
        vorjahr_monate = {}
        vorvorjahr_monate = {}

        for m in range(1, 13):
            vorjahr_monate[m] = {'nw': 0, 'gw': 0, 'nw_umsatz': 0, 'gw_umsatz': 0}
            vorvorjahr_monate[m] = {'nw': 0, 'gw': 0}

        for row in vj_daten:
            m = row['monat']
            typ = row['typ'].lower()
            vorjahr_monate[m][typ] = int(row['stueck'])
            vorjahr_monate[m][f'{typ}_umsatz'] = float(row['umsatz'])

        for row in vvj_daten:
            m = row['monat']
            typ = row['typ'].lower()
            vorvorjahr_monate[m][typ] = int(row['stueck'])

        # Jahrestrend berechnen (Vorjahr vs Vorvorjahr)
        vj_nw_total = sum(m['nw'] for m in vorjahr_monate.values())
        vj_gw_total = sum(m['gw'] for m in vorjahr_monate.values())
        vvj_nw_total = sum(m['nw'] for m in vorvorjahr_monate.values())
        vvj_gw_total = sum(m['gw'] for m in vorvorjahr_monate.values())

        trend_nw = (vj_nw_total / vvj_nw_total - 1) if vvj_nw_total > 0 else 0
        trend_gw = (vj_gw_total / vvj_gw_total - 1) if vvj_gw_total > 0 else 0

        # Benchmark berechnen
        result = {
            'jahr': jahr,
            'vorjahr': vorjahr,
            'wachstum_pct': wachstum * 100,
            'trend_nw_pct': round(trend_nw * 100, 1),
            'trend_gw_pct': round(trend_gw * 100, 1),
            'monate': {},
            'gesamt': {
                'nw': {'vorjahr': vj_nw_total, 'benchmark': 0, 'avg_preis': 0},
                'gw': {'vorjahr': vj_gw_total, 'benchmark': 0, 'avg_preis': 0}
            }
        }

        total_nw_umsatz = sum(m.get('nw_umsatz', 0) for m in vorjahr_monate.values())
        total_gw_umsatz = sum(m.get('gw_umsatz', 0) for m in vorjahr_monate.values())

        avg_nw_preis = total_nw_umsatz / vj_nw_total if vj_nw_total > 0 else 30000
        avg_gw_preis = total_gw_umsatz / vj_gw_total if vj_gw_total > 0 else 18000

        for m in range(1, 13):
            vj = vorjahr_monate[m]

            # Benchmark = Vorjahr × (1 + Wachstum)
            nw_benchmark = round(vj['nw'] * (1 + wachstum))
            gw_benchmark = round(vj['gw'] * (1 + wachstum))

            # Umsatz-Benchmark basierend auf Durchschnittspreis
            nw_umsatz_benchmark = round(nw_benchmark * avg_nw_preis)
            gw_umsatz_benchmark = round(gw_benchmark * avg_gw_preis)

            result['monate'][m] = {
                'monat': m,
                'name': MONATE[m-1],
                'nw': {
                    'vorjahr': vj['nw'],
                    'benchmark': nw_benchmark,
                    'umsatz_benchmark': nw_umsatz_benchmark
                },
                'gw': {
                    'vorjahr': vj['gw'],
                    'benchmark': gw_benchmark,
                    'umsatz_benchmark': gw_umsatz_benchmark
                }
            }

            result['gesamt']['nw']['benchmark'] += nw_benchmark
            result['gesamt']['gw']['benchmark'] += gw_benchmark

        result['gesamt']['nw']['avg_preis'] = round(avg_nw_preis)
        result['gesamt']['gw']['avg_preis'] = round(avg_gw_preis)

        # Empfehlung
        result['empfehlung'] = {
            'nw_jahr': result['gesamt']['nw']['benchmark'],
            'gw_jahr': result['gesamt']['gw']['benchmark'],
            'nw_monat_avg': round(result['gesamt']['nw']['benchmark'] / 12),
            'gw_monat_avg': round(result['gesamt']['gw']['benchmark'] / 12),
            'hinweis': f"Basierend auf {vorjahr} + {wachstum*100:.0f}% Wachstum. Trend {vorvorjahr}→{vorjahr}: NW {trend_nw*100:+.1f}%, GW {trend_gw*100:+.1f}%"
        }

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        logger.error(f"Benchmark Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# PLAN SPEICHERN/LADEN
# ============================================================================

@budget_bp.route('/plan/<int:jahr>')
def get_plan(jahr):
    """Holt gespeicherte Planung."""
    standort = request.args.get('standort', type=int)

    try:
        conn = get_db()
        cursor = conn.cursor()

        query = '''
            SELECT monat, standort, typ, stueck_plan, umsatz_plan, db1_plan, marge_plan, kommentar
            FROM budget_plan
            WHERE jahr = %s
        '''
        params = [jahr]

        if standort:
            query += ' AND standort = %s'
            params.append(standort)

        query += ' ORDER BY monat, standort, typ'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        result = {'jahr': jahr, 'monate': {}}

        for m in range(1, 13):
            result['monate'][m] = {
                'monat': m,
                'name': MONATE[m-1],
                'standorte': {}
            }
            for s_id in STANDORTE.keys():
                result['monate'][m]['standorte'][s_id] = {
                    'name': STANDORTE[s_id]['name'],
                    'nw': {'stueck': 0, 'umsatz': 0},
                    'gw': {'stueck': 0, 'umsatz': 0}
                }

        for row in rows:
            m = row['monat']
            s = row['standort']
            typ = row['typ'].lower()

            if m in result['monate'] and s in result['monate'][m]['standorte']:
                result['monate'][m]['standorte'][s][typ] = {
                    'stueck': int(row['stueck_plan'] or 0),
                    'umsatz': float(row['umsatz_plan'] or 0),
                    'db1': float(row['db1_plan'] or 0),
                    'marge': float(row['marge_plan'] or 0)
                }

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        logger.error(f"Plan laden Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@budget_bp.route('/plan/<int:jahr>', methods=['POST'])
def save_plan(jahr):
    """Speichert Planung."""
    try:
        data = request.get_json()
        user = data.get('user', 'system')
        monate = data.get('monate', {})

        conn = get_db()
        cursor = conn.cursor()

        for monat_key, monat_data in monate.items():
            monat = int(monat_key)

            for standort_key, standort_data in monat_data.get('standorte', {}).items():
                standort = int(standort_key)

                for typ in ['nw', 'gw']:
                    typ_data = standort_data.get(typ, {})
                    stueck = typ_data.get('stueck', 0)
                    umsatz = typ_data.get('umsatz', 0)
                    db1 = typ_data.get('db1', 0)
                    marge = typ_data.get('marge', 0)

                    cursor.execute('''
                        INSERT INTO budget_plan (jahr, monat, standort, typ, stueck_plan, umsatz_plan, db1_plan, marge_plan, erstellt_von)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (jahr, monat, standort, typ)
                        DO UPDATE SET
                            stueck_plan = EXCLUDED.stueck_plan,
                            umsatz_plan = EXCLUDED.umsatz_plan,
                            db1_plan = EXCLUDED.db1_plan,
                            marge_plan = EXCLUDED.marge_plan,
                            erstellt_von = EXCLUDED.erstellt_von,
                            erstellt_am = CURRENT_TIMESTAMP
                    ''', (jahr, monat, standort, typ.upper(), stueck, umsatz, db1, marge, user))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': f'Plan {jahr} gespeichert'})

    except Exception as e:
        logger.error(f"Plan speichern Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@budget_bp.route('/plan/<int:jahr>/apply-benchmark', methods=['POST'])
def apply_benchmark(jahr):
    """Wendet Benchmark als Plan an."""
    try:
        data = request.get_json()
        wachstum = data.get('wachstum', 5)
        user = data.get('user', 'system')

        # Benchmark holen
        from flask import current_app
        with current_app.test_request_context(f'/api/budget/benchmark/{jahr}?wachstum={wachstum}'):
            response = benchmark(jahr)
            benchmark_data = response.get_json()

        if not benchmark_data.get('success'):
            return jsonify({'success': False, 'error': 'Benchmark nicht verfügbar'})

        # Für jeden Standort speichern (gleichmäßig verteilt als Basis)
        conn = get_db()
        cursor = conn.cursor()

        for m_key, m_data in benchmark_data['data']['monate'].items():
            monat = int(m_key)

            # Benchmark auf Standorte verteilen (basierend auf 2024-Verteilung)
            # DEG Opel: ~45%, HYU: ~30%, LAN: ~25%
            verteilung = {1: 0.45, 2: 0.30, 3: 0.25}

            for standort, anteil in verteilung.items():
                for typ in ['nw', 'gw']:
                    stueck = round(m_data[typ]['benchmark'] * anteil)
                    umsatz = round(m_data[typ]['umsatz_benchmark'] * anteil)

                    cursor.execute('''
                        INSERT INTO budget_plan (jahr, monat, standort, typ, stueck_plan, umsatz_plan, erstellt_von)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (jahr, monat, standort, typ)
                        DO UPDATE SET
                            stueck_plan = EXCLUDED.stueck_plan,
                            umsatz_plan = EXCLUDED.umsatz_plan,
                            erstellt_von = EXCLUDED.erstellt_von,
                            erstellt_am = CURRENT_TIMESTAMP
                    ''', (jahr, monat, standort, typ.upper(), stueck, umsatz, user))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Benchmark mit {wachstum}% Wachstum als Plan für {jahr} übernommen'
        })

    except Exception as e:
        logger.error(f"Benchmark anwenden Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# VERGLEICH IST vs PLAN
# ============================================================================

@budget_bp.route('/vergleich/<int:jahr>')
def vergleich(jahr):
    """Vergleich IST vs PLAN mit Abweichungen."""
    try:
        ist_rows = get_ist_daten_locosoft(jahr)

        # PLAN laden
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT monat, standort, typ, stueck_plan, umsatz_plan
            FROM budget_plan WHERE jahr = %s
        ''', (jahr,))
        plan_rows = cursor.fetchall()
        conn.close()

        # Strukturieren
        result = {'jahr': jahr, 'monate': {}, 'gesamt': {}}

        for m in range(1, 13):
            result['monate'][m] = {
                'monat': m,
                'name': MONATE[m-1],
                'nw': {'ist': 0, 'plan': 0, 'diff': 0, 'diff_pct': 0},
                'gw': {'ist': 0, 'plan': 0, 'diff': 0, 'diff_pct': 0}
            }

        # IST einfügen
        for row in ist_rows:
            m = row['monat']
            typ = row['typ'].lower()
            if m in result['monate']:
                result['monate'][m][typ]['ist'] += int(row['stueck'])

        # PLAN einfügen
        for row in plan_rows:
            m = row['monat']
            typ = row['typ'].lower()
            if m in result['monate']:
                result['monate'][m][typ]['plan'] += int(row['stueck_plan'] or 0)

        # Abweichungen berechnen
        for m_data in result['monate'].values():
            for typ in ['nw', 'gw']:
                ist = m_data[typ]['ist']
                plan = m_data[typ]['plan']
                m_data[typ]['diff'] = ist - plan
                m_data[typ]['diff_pct'] = round((ist / plan - 1) * 100, 1) if plan > 0 else 0
                m_data[typ]['ampel'] = 'gruen' if ist >= plan else ('gelb' if ist >= plan * 0.9 else 'rot')

        # Jahressummen
        result['gesamt'] = {
            'nw': {
                'ist': sum(m['nw']['ist'] for m in result['monate'].values()),
                'plan': sum(m['nw']['plan'] for m in result['monate'].values())
            },
            'gw': {
                'ist': sum(m['gw']['ist'] for m in result['monate'].values()),
                'plan': sum(m['gw']['plan'] for m in result['monate'].values())
            }
        }

        for typ in ['nw', 'gw']:
            g = result['gesamt'][typ]
            g['diff'] = g['ist'] - g['plan']
            g['diff_pct'] = round((g['ist'] / g['plan'] - 1) * 100, 1) if g['plan'] > 0 else 0

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        logger.error(f"Vergleich Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# VERKÄUFER-STATISTIK
# ============================================================================

@budget_bp.route('/verkaufer/<int:jahr>')
def verkaufer_stats(jahr):
    """Verkaufsstatistik pro Verkäufer."""
    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                out_salesman_number_1 as verkaufer_nr,
                CASE
                    WHEN dealer_vehicle_type IN ('N', 'V') THEN 'NW'
                    ELSE 'GW'
                END as typ,
                COUNT(*) as stueck,
                SUM(out_sale_price) as umsatz
            FROM dealer_vehicles
            WHERE EXTRACT(YEAR FROM out_invoice_date) = %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('N', 'V', 'D', 'G')
              AND out_salesman_number_1 IS NOT NULL
            GROUP BY out_salesman_number_1, CASE WHEN dealer_vehicle_type IN ('N', 'V') THEN 'NW' ELSE 'GW' END
            ORDER BY stueck DESC
        """, (jahr,))

        rows = cursor.fetchall()
        conn.close()

        # Gruppieren nach Verkäufer
        verkaufer = {}
        for row in rows:
            vnr = row['verkaufer_nr']
            if vnr not in verkaufer:
                verkaufer[vnr] = {'nr': vnr, 'nw': 0, 'gw': 0, 'nw_umsatz': 0, 'gw_umsatz': 0}

            typ = row['typ'].lower()
            verkaufer[vnr][typ] = int(row['stueck'])
            verkaufer[vnr][f'{typ}_umsatz'] = float(row['umsatz'] or 0)

        # Sortieren nach Gesamt-Stück
        verkaufer_list = sorted(
            verkaufer.values(),
            key=lambda x: x['nw'] + x['gw'],
            reverse=True
        )

        return jsonify({
            'success': True,
            'data': {
                'jahr': jahr,
                'verkaufer': verkaufer_list,
                'gesamt': {
                    'nw': sum(v['nw'] for v in verkaufer_list),
                    'gw': sum(v['gw'] for v in verkaufer_list)
                }
            }
        })

    except Exception as e:
        logger.error(f"Verkäufer-Stats Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# MARKEN-STATISTIK (Opel, Hyundai, Andere)
# ============================================================================

MARKEN = {
    40: 'Opel',
    27: 'Hyundai'
}

@budget_bp.route('/marken/<int:jahr>')
def marken_stats(jahr):
    """Verkaufsstatistik pro Marke (Opel, Hyundai, Andere)."""
    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                CASE
                    WHEN out_make_number = 40 THEN 'opel'
                    WHEN out_make_number = 27 THEN 'hyundai'
                    ELSE 'andere'
                END as marke,
                CASE
                    WHEN dealer_vehicle_type IN ('N', 'V') THEN 'nw'
                    ELSE 'gw'
                END as typ,
                COUNT(*) as stueck,
                COALESCE(SUM(out_sale_price), 0) as umsatz
            FROM dealer_vehicles
            WHERE EXTRACT(YEAR FROM out_invoice_date) = %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('N', 'V', 'D', 'G')
            GROUP BY 1, 2
            ORDER BY marke, typ
        """, (jahr,))

        rows = cursor.fetchall()
        conn.close()

        # Strukturieren
        marken = {
            'opel': {'nw': 0, 'gw': 0, 'nw_umsatz': 0, 'gw_umsatz': 0},
            'hyundai': {'nw': 0, 'gw': 0, 'nw_umsatz': 0, 'gw_umsatz': 0},
            'andere': {'nw': 0, 'gw': 0, 'nw_umsatz': 0, 'gw_umsatz': 0}
        }

        for row in rows:
            m = row['marke']
            t = row['typ']
            marken[m][t] = int(row['stueck'])
            marken[m][f'{t}_umsatz'] = float(row['umsatz'])

        # Totals berechnen
        for m in marken.values():
            m['gesamt'] = m['nw'] + m['gw']
            m['umsatz_gesamt'] = m['nw_umsatz'] + m['gw_umsatz']

        return jsonify({
            'success': True,
            'data': {
                'jahr': jahr,
                'marken': marken,
                'gesamt': {
                    'nw': sum(m['nw'] for m in marken.values()),
                    'gw': sum(m['gw'] for m in marken.values()),
                    'umsatz': sum(m['umsatz_gesamt'] for m in marken.values())
                }
            }
        })

    except Exception as e:
        logger.error(f"Marken-Stats Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@budget_bp.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'module': 'budget',
        'standorte': STANDORTE,
        'marken': MARKEN
    })


# Tabellen initialisieren
try:
    init_budget_tables()
except Exception as e:
    logger.warning(f"Budget-Tabellen Init: {e}")
