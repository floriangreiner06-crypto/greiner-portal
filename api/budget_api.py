#!/usr/bin/env python3
"""
BUDGET PLANUNG API - Verkaufsplanung NW/GW mit DB1-Fokus
=========================================================
Profit-orientierte Budget-Planung für Verkaufsleitung.

DATENBANKEN:
- IST-Daten: PostgreSQL Locosoft (10.80.80.8:5432/loco_auswertung_db)
  → dealer_vehicles Tabelle
- PLAN-Daten: PostgreSQL DRIVE Portal (127.0.0.1:5432/drive_portal)
  → budget_plan Tabelle

JAHRESABSCHLUSS-ERKENNTNISSE (GJ 09/24-08/25):
┌─────────────┬──────────┬────────────┬───────────┬────────────┐
│ Gesellschaft│ Umsatz   │ Gewinn     │ NW-Marge  │ GW-Marge   │
├─────────────┼──────────┼────────────┼───────────┼────────────┤
│ Auto Greiner│ 10.87 M€ │ +163k€     │ 7.1%      │ 10.1%      │
│ (Hyundai)   │          │ (-52% VJ)  │           │ ★ ZIEL     │
├─────────────┼──────────┼────────────┼───────────┼────────────┤
│ Autohaus Gr.│ 18.64 M€ │ +193k€     │ 4.9%      │ 0.7%       │
│ (Opel)      │          │ (+478% VJ) │           │ ⚠ KRITISCH │
└─────────────┴──────────┴────────────┴───────────┴────────────┘

GLOBALCUBE IST 2024 (aus Planung_2025.xlsx extrahiert, TAG 155):
┌────────────┬───────┬────────────┬─────────────┬──────────┐
│ Bereich    │ Stück │ Umsatz     │ Bruttoertrag│ BE/Fzg   │
├────────────┼───────┼────────────┼─────────────┼──────────┤
│ Neuwagen   │ 535   │ €14.58 Mio │ €1.69 Mio   │ €3.165   │
│ Gebrauchtw.│ 615   │ €9.88 Mio  │ €1.10 Mio   │ €1.795   │
├────────────┼───────┼────────────┼─────────────┼──────────┤
│ GESAMT     │ 1.150 │ €24.46 Mio │ €2.80 Mio   │ €2.432   │
└────────────┴───────┴────────────┴─────────────┴──────────┘

ZIEL-MARGEN (basierend auf Analyse):
- NW Opel:    4.5% → 6.0% (Ziel)
- NW Hyundai: 7.1% → 7.5% (Optimierung)
- GW Opel:    0.7% → 6.0% (KRITISCH - muss drastisch steigen!)
- GW Hyundai: 10.1% (halten)

Features:
- DB1 (Deckungsbeitrag 1) als Hauptkennzahl statt nur Stückzahlen
- Margen-Warnsystem (Rot <5%, Gelb 5-7%, Grün >7%)
- VKL-Provisionsrechner basierend auf DB1
- Automatische Benchmarks aus Locosoft mit Profit-Fokus
- 5-Fragen-Wizard für einfache Budget-Planung (TAG 155)

Endpoints:
- GET  /api/budget/dashboard              - Übersicht mit DB1
- GET  /api/budget/benchmark/<jahr>       - Smarte Benchmark-Vorschläge
- GET  /api/budget/plan/<jahr>            - Gespeicherte Planung
- POST /api/budget/plan/<jahr>            - Planung speichern
- POST /api/budget/plan/<jahr>/apply-benchmark - Benchmark übernehmen
- GET  /api/budget/vergleich/<jahr>       - IST vs PLAN mit Profit
- GET  /api/budget/verkaufer/<jahr>       - Pro Verkäufer mit DB1
- GET  /api/budget/margen-analyse         - Margen-Warnung pro Standort
- GET  /api/budget/vkl-provision          - VKL-Provisionsrechner
- GET  /api/budget/wizard/<typ>           - 5-Fragen-Wizard (TAG 155)
- GET  /api/budget/globalcube-ist/<jahr>  - IST aus GlobalCube Excel (TAG 155)

Author: Claude
Date: 2025-12-29 (TAG 143 - DB1-Erweiterung)
Update: 2026-01-02 (TAG 155 - 5-Fragen-Wizard)
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
    1: {'name': 'Deggendorf Opel', 'kurz': 'DEG', 'marke': 'opel'},
    2: {'name': 'Deggendorf Hyundai', 'kurz': 'HYU', 'marke': 'hyundai'},
    3: {'name': 'Landau', 'kurz': 'LAN', 'marke': 'opel'}  # Landau = Opel
}

# Ziel-Margen basierend auf Jahresabschluss-Analyse (GJ 09/24-08/25)
# IST-Werte aus Bilanz: Opel GW 0.7% (!), Hyundai GW 10.1%
ZIEL_MARGEN = {
    'opel': {
        'nw': {'min': 5.0, 'ziel': 6.0, 'ist_gj24': 4.9},
        'gw': {'min': 5.0, 'ziel': 6.0, 'ist_gj24': 0.7}  # KRITISCH!
    },
    'hyundai': {
        'nw': {'min': 6.0, 'ziel': 7.5, 'ist_gj24': 7.1},
        'gw': {'min': 8.0, 'ziel': 10.0, 'ist_gj24': 10.1}  # Benchmark
    }
}

# VKL-Provisions-Staffelung (% vom DB1)
VKL_PROVISION_STAFFEL = [
    {'ab_db1': 0, 'provision_pct': 5.0},      # Basis
    {'ab_db1': 50000, 'provision_pct': 7.5},   # Ab 50k DB1
    {'ab_db1': 100000, 'provision_pct': 10.0}, # Ab 100k DB1
    {'ab_db1': 150000, 'provision_pct': 12.5}  # Top-Performer
]


def get_margen_ampel(marge_pct, marke='opel', typ='gw'):
    """
    Berechnet Ampelfarbe für Marge.

    Returns: 'rot' | 'gelb' | 'gruen'
    """
    ziel = ZIEL_MARGEN.get(marke, ZIEL_MARGEN['opel']).get(typ, {'min': 5, 'ziel': 7})

    if marge_pct < ziel['min']:
        return 'rot'
    elif marge_pct < ziel['ziel']:
        return 'gelb'
    else:
        return 'gruen'


def berechne_vkl_provision(db1_summe):
    """
    Berechnet VKL-Provision basierend auf DB1-Staffel.

    Returns: dict mit provision_pct, provision_betrag, stufe
    """
    provision_pct = 5.0
    stufe = 1

    for i, s in enumerate(VKL_PROVISION_STAFFEL):
        if db1_summe >= s['ab_db1']:
            provision_pct = s['provision_pct']
            stufe = i + 1

    return {
        'db1_summe': db1_summe,
        'provision_pct': provision_pct,
        'provision_betrag': round(db1_summe * provision_pct / 100, 2),
        'stufe': stufe,
        'naechste_stufe': VKL_PROVISION_STAFFEL[stufe]['ab_db1'] if stufe < len(VKL_PROVISION_STAFFEL) else None
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
# MARGEN-ANALYSE (PROFIT-FOKUS)
# ============================================================================

@budget_bp.route('/margen-analyse')
def margen_analyse():
    """
    Detaillierte Margen-Analyse pro Standort/Marke.
    Zeigt IST vs ZIEL mit Warnsystem.

    Basiert auf Jahresabschluss-Erkenntnissen:
    - Opel GW: 0.7% (KRITISCH!) → Ziel: 6%
    - Hyundai GW: 10.1% (Benchmark)
    """
    jahr = request.args.get('jahr', datetime.now().year, type=int)

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Verkaufsdaten aus DRIVE Portal sales Tabelle (hat deckungsbeitrag = DB1)
        cursor.execute("""
            SELECT
                out_subsidiary as standort,
                CASE
                    WHEN make_number = 40 THEN 'opel'
                    WHEN make_number = 27 THEN 'hyundai'
                    ELSE 'andere'
                END as marke,
                CASE
                    WHEN dealer_vehicle_type IN ('N', 'V') THEN 'nw'
                    ELSE 'gw'
                END as typ,
                COUNT(*) as stueck,
                COALESCE(SUM(out_sale_price), 0) as umsatz,
                COALESCE(SUM(deckungsbeitrag), 0) as db1
            FROM sales
            WHERE EXTRACT(YEAR FROM out_invoice_date) = %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('N', 'V', 'D', 'G')
            GROUP BY out_subsidiary, 2, 3
            ORDER BY standort, marke, typ
        """, (jahr,))

        rows = cursor.fetchall()
        conn.close()

        # Strukturieren nach Standort
        analyse = {}

        for row in rows:
            s_id = row['standort']
            marke = row['marke']
            typ = row['typ']

            if s_id not in analyse:
                s_info = STANDORTE.get(s_id, {'name': f'Standort {s_id}', 'kurz': f'S{s_id}', 'marke': 'opel'})
                analyse[s_id] = {
                    'standort_id': s_id,
                    'name': s_info['name'],
                    'kurz': s_info['kurz'],
                    'marken': {}
                }

            if marke not in analyse[s_id]['marken']:
                analyse[s_id]['marken'][marke] = {'nw': None, 'gw': None}

            umsatz = float(row['umsatz'])
            db1 = float(row['db1'])
            marge = (db1 / umsatz * 100) if umsatz > 0 else 0

            # Ziel-Marge holen
            ziel_info = ZIEL_MARGEN.get(marke, ZIEL_MARGEN['opel']).get(typ, {'min': 5, 'ziel': 7, 'ist_gj24': 5})

            analyse[s_id]['marken'][marke][typ] = {
                'stueck': int(row['stueck']),
                'umsatz': umsatz,
                'db1': db1,
                'marge_pct': round(marge, 2),
                'marge_ziel': ziel_info['ziel'],
                'marge_ist_gj24': ziel_info['ist_gj24'],
                'ampel': get_margen_ampel(marge, marke, typ),
                'delta_ziel': round(marge - ziel_info['ziel'], 2),
                'potential_eur': round((ziel_info['ziel'] - marge) / 100 * umsatz, 0) if marge < ziel_info['ziel'] else 0
            }

        # Warnungen sammeln
        warnungen = []
        for s_id, s_data in analyse.items():
            for marke, m_data in s_data['marken'].items():
                for typ in ['nw', 'gw']:
                    if m_data[typ] and m_data[typ]['ampel'] == 'rot':
                        warnungen.append({
                            'standort': s_data['name'],
                            'marke': marke.upper(),
                            'typ': typ.upper(),
                            'marge_ist': m_data[typ]['marge_pct'],
                            'marge_ziel': m_data[typ]['marge_ziel'],
                            'potential': m_data[typ]['potential_eur'],
                            'message': f"{s_data['kurz']} {marke.upper()} {typ.upper()}: Marge nur {m_data[typ]['marge_pct']:.1f}% (Ziel: {m_data[typ]['marge_ziel']}%)"
                        })

        return jsonify({
            'success': True,
            'data': {
                'jahr': jahr,
                'standorte': analyse,
                'ziel_margen': ZIEL_MARGEN,
                'warnungen': warnungen,
                'kritisch': len([w for w in warnungen if w['marge_ist'] < 3])
            }
        })

    except Exception as e:
        logger.error(f"Margen-Analyse Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# VKL-PROVISIONSRECHNER
# ============================================================================

@budget_bp.route('/vkl-provision')
def vkl_provision():
    """
    Berechnet VKL-Provision basierend auf DB1.

    Query-Parameter:
    - jahr: Planjahr
    - verkaufer: (optional) Verkäufer-Nummer für individuell
    """
    jahr = request.args.get('jahr', datetime.now().year, type=int)
    verkaufer_nr = request.args.get('verkaufer', type=int)

    try:
        conn = get_db()
        cursor = conn.cursor()

        # DB1 pro Verkäufer aus DRIVE Portal sales Tabelle
        query = """
            SELECT
                salesman_number as verkaufer_nr,
                out_subsidiary as standort,
                COUNT(*) as stueck,
                COALESCE(SUM(out_sale_price), 0) as umsatz,
                COALESCE(SUM(deckungsbeitrag), 0) as db1
            FROM sales
            WHERE EXTRACT(YEAR FROM out_invoice_date) = %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('N', 'V', 'D', 'G')
              AND salesman_number IS NOT NULL
        """
        params = [jahr]

        if verkaufer_nr:
            query += " AND salesman_number = %s"
            params.append(verkaufer_nr)

        query += """
            GROUP BY salesman_number, out_subsidiary
            ORDER BY db1 DESC
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Aggregieren nach Verkäufer
        verkaufer = {}
        for row in rows:
            vnr = row['verkaufer_nr']
            if vnr not in verkaufer:
                verkaufer[vnr] = {
                    'verkaufer_nr': vnr,
                    'stueck': 0,
                    'umsatz': 0,
                    'db1': 0,
                    'standorte': []
                }

            verkaufer[vnr]['stueck'] += int(row['stueck'])
            verkaufer[vnr]['umsatz'] += float(row['umsatz'])
            verkaufer[vnr]['db1'] += float(row['db1'])
            verkaufer[vnr]['standorte'].append(row['standort'])

        # Provision berechnen
        result = []
        for vnr, v_data in verkaufer.items():
            prov = berechne_vkl_provision(v_data['db1'])
            result.append({
                **v_data,
                'marge_pct': round(v_data['db1'] / v_data['umsatz'] * 100, 2) if v_data['umsatz'] > 0 else 0,
                'provision': prov
            })

        # Sortieren nach DB1
        result = sorted(result, key=lambda x: x['db1'], reverse=True)

        # Gesamt-Provision berechnen
        gesamt_db1 = sum(v['db1'] for v in result)
        gesamt_provision = berechne_vkl_provision(gesamt_db1)

        return jsonify({
            'success': True,
            'data': {
                'jahr': jahr,
                'verkaufer': result,
                'staffel': VKL_PROVISION_STAFFEL,
                'gesamt': {
                    'stueck': sum(v['stueck'] for v in result),
                    'umsatz': sum(v['umsatz'] for v in result),
                    'db1': gesamt_db1,
                    'provision': gesamt_provision
                }
            }
        })

    except Exception as e:
        logger.error(f"VKL-Provision Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# JAHRESABSCHLUSS-REFERENZ
# ============================================================================

@budget_bp.route('/jahresabschluss-referenz')
def jahresabschluss_referenz():
    """
    Liefert die Referenzwerte aus dem Jahresabschluss GJ 09/24-08/25.
    Für Dashboard-Anzeige und Benchmark-Vergleich.
    """
    return jsonify({
        'success': True,
        'data': {
            'geschaeftsjahr': '09/2024 - 08/2025',
            'gesellschaften': {
                'auto_greiner': {
                    'name': 'Auto Greiner GmbH & Co. KG',
                    'marke': 'Hyundai',
                    'standort_id': 2,
                    'umsatz_gesamt': 10870000,
                    'gewinn': 163000,
                    'gewinn_vj_delta_pct': -52,
                    'nw_umsatz': 5800000,
                    'nw_marge_pct': 7.1,
                    'gw_umsatz': 3450000,
                    'gw_marge_pct': 10.1,
                    'zinsaufwand': 43000
                },
                'autohaus_greiner': {
                    'name': 'Autohaus Greiner GmbH & Co. KG',
                    'marke': 'Opel',
                    'standort_id': 1,
                    'umsatz_gesamt': 18640000,
                    'gewinn': 193000,
                    'gewinn_vj_delta_pct': 478,
                    'nw_umsatz': 9800000,
                    'nw_marge_pct': 4.9,
                    'gw_umsatz': 6520000,
                    'gw_marge_pct': 0.7,  # KRITISCH!
                    'zinsaufwand': 279000,
                    'warnung': 'GW-Marge kritisch niedrig (0.7%)'
                }
            },
            'erkenntnisse': [
                'Opel GW-Marge mit 0.7% kritisch - 46k DB1 auf 6.5M Umsatz',
                'Hyundai GW-Marge mit 10.1% als Benchmark',
                'Zinsbelastung Opel €279k vs Hyundai €43k',
                'Verwaltungsumlage von 600k auf 870k gestiegen',
                'Hyundai Gewinn -52% trotz stabiler Margen (Stückzahlen-Rückgang)'
            ],
            'ziele_2026': {
                'opel_gw_marge': 6.0,
                'opel_nw_marge': 6.0,
                'hyundai_gw_marge': 10.0,
                'hyundai_nw_marge': 7.5
            }
        }
    })


# ============================================================================
# HEALTH CHECK
# ============================================================================

@budget_bp.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'module': 'budget',
        'version': '2.0-db1',
        'standorte': STANDORTE,
        'marken': MARKEN,
        'ziel_margen': ZIEL_MARGEN
    })


# ============================================================================
# GLOBALCUBE IST-DATEN 2024 (aus Planung_2025.xlsx extrahiert)
# ============================================================================

# Extrahiert am 2026-01-02 aus GlobalCube Export
GLOBALCUBE_IST_2024 = {
    'NW': {
        'gesamt': {
            'stueck': 535,
            'umsatz': 14582964,
            'einsatzwerte': 12889851,
            'bruttoertrag': 1693113,
            'variable_kosten': 577592,
            'direkte_kosten': 288996,
            'betriebsergebnis': 826525
        },
        'standorte': {
            1: {'stueck': 255, 'umsatz': 6522397, 'bruttoertrag': 950130, 'betriebsergebnis': 410705, 'name': 'Deggendorf'},
            2: {'stueck': 234, 'umsatz': 6921270, 'bruttoertrag': 695724, 'betriebsergebnis': 472041, 'name': 'DEG HYU'},
            3: {'stueck': 46, 'umsatz': 1139297, 'bruttoertrag': 47259, 'betriebsergebnis': -56221, 'name': 'Landau'}
        },
        'variable_kosten_detail': {
            'fixum_prov_soz': 291090,
            'provisionen': 66700,
            'fertigmachen': 59260,
            'kulanz': 66943,
            'training': 9023,
            'fahrzeugkosten': 31203,
            'werbung': 53374
        },
        'kpis': {
            'umsatz_pro_fzg': 27258,
            'bruttoertrag_pro_fzg': 3165,
            'bruttoertrag_marge': 11.6,
            'variable_kosten_quote': 34.1
        }
    },
    'GW': {
        'gesamt': {
            'stueck': 615,
            'umsatz': 9881621,
            'einsatzwerte': 8777536,
            'bruttoertrag': 1104085,
            'variable_kosten': 282453,
            'direkte_kosten': 273269,
            'betriebsergebnis': 548363
        },
        'standorte': {
            1: {'stueck': 295, 'umsatz': 4658178, 'bruttoertrag': 595550, 'betriebsergebnis': 244596, 'name': 'Deggendorf'},
            2: {'stueck': 163, 'umsatz': 2885582, 'bruttoertrag': 357285, 'betriebsergebnis': 270273, 'name': 'DEG HYU'},
            3: {'stueck': 157, 'umsatz': 2337861, 'bruttoertrag': 151249, 'betriebsergebnis': 33494, 'name': 'Landau'}
        },
        'variable_kosten_detail': {
            'fixum_prov_soz': 174636,
            'provisionen': 38012,
            'fertigmachen': 270,
            'kulanz': 38022,
            'training': 225,
            'fahrzeugkosten': 14601,
            'werbung': 16688
        },
        'kpis': {
            'umsatz_pro_fzg': 16068,
            'bruttoertrag_pro_fzg': 1795,
            'bruttoertrag_marge': 11.2,
            'variable_kosten_quote': 25.6
        }
    }
}

# Branchen-Benchmarks (DEKRA, ZDK, DAT Report)
BRANCHEN_BENCHMARKS = {
    'NW': {
        'bruttoertrag_pro_fzg': {'min': 1500, 'max': 2500, 'einheit': '€'},
        'bruttoertrag_marge': {'min': 7, 'max': 10, 'einheit': '%'},
        'variable_kosten_quote': {'min': 25, 'max': 35, 'einheit': '%'}
    },
    'GW': {
        'bruttoertrag_pro_fzg': {'min': 2000, 'max': 3500, 'einheit': '€'},
        'bruttoertrag_marge': {'min': 12, 'max': 15, 'einheit': '%'},
        'variable_kosten_quote': {'min': 20, 'max': 28, 'einheit': '%'}
    }
}

# Saisonalisierung (% pro Monat)
SAISONALISIERUNG = {
    'NW': [6.5, 7.0, 10.5, 9.5, 9.0, 8.5, 7.5, 7.0, 9.0, 9.5, 9.0, 7.0],
    'GW': [7.0, 7.5, 9.5, 9.0, 9.0, 8.5, 8.0, 7.5, 8.5, 9.0, 8.5, 8.0]
}


@budget_bp.route('/globalcube-ist/<int:jahr>')
def globalcube_ist(jahr):
    """
    GlobalCube IST-Daten für ein Jahr (aktuell nur 2024 verfügbar).

    Returns: Vollständige Daten aus Planung_2025.xlsx
    """
    if jahr != 2024:
        return jsonify({
            'success': False,
            'error': f'IST-Daten nur für 2024 verfügbar (aus GlobalCube Export)'
        }), 404

    typ = request.args.get('typ', '').upper()  # 'NW' oder 'GW'
    standort = request.args.get('standort', type=int)

    if typ and typ in GLOBALCUBE_IST_2024:
        data = GLOBALCUBE_IST_2024[typ].copy()
        if standort and standort in data['standorte']:
            data['standort_detail'] = data['standorte'][standort]
        return jsonify({'success': True, 'data': data, 'typ': typ, 'jahr': jahr})
    else:
        return jsonify({
            'success': True,
            'data': GLOBALCUBE_IST_2024,
            'jahr': jahr,
            'quelle': 'GlobalCube Planung_2025.xlsx',
            'extrahiert': '2026-01-02'
        })


@budget_bp.route('/wizard/<typ>')
def wizard(typ):
    """
    5-Fragen-Wizard für einfache Budget-Planung.

    Args:
        typ: 'NW' oder 'GW'

    Returns:
        JSON mit 5 Wizard-Fragen und Vorschlägen
    """
    typ = typ.upper()
    if typ not in ['NW', 'GW']:
        return jsonify({'success': False, 'error': 'Typ muss NW oder GW sein'}), 400

    standort = request.args.get('standort', type=int)
    planjahr = request.args.get('jahr', datetime.now().year + 1, type=int)

    # IST-Daten laden
    ist = GLOBALCUBE_IST_2024.get(typ, {})
    if standort and standort in ist.get('standorte', {}):
        ist_detail = ist['standorte'][standort]
        standort_name = ist_detail.get('name', f'Standort {standort}')
    else:
        ist_detail = ist.get('gesamt', {})
        standort_name = 'AH Greiner Gesamt'
        standort = None

    benchmarks = BRANCHEN_BENCHMARKS.get(typ, {})
    kpis = ist.get('kpis', {})

    # KPIs für Standort berechnen
    stueck = ist_detail.get('stueck', 100)
    umsatz = ist_detail.get('umsatz', 0)
    bruttoertrag = ist_detail.get('bruttoertrag', 0)
    be_pro_fzg = round(bruttoertrag / stueck) if stueck else 0
    umsatz_pro_fzg = round(umsatz / stueck) if stueck else 0

    # 5 Wizard-Fragen
    fragen = [
        {
            'nummer': 1,
            'titel': 'Stückzahl-Ziel',
            'frage': f'Wie viele {typ}-Fahrzeuge möchten Sie {planjahr} verkaufen?',
            'icon': '🚗',
            'typ_feld': 'slider',
            'feld': 'stueck',
            'vorjahr': stueck,
            'minimum': int(stueck * 0.8),
            'maximum': int(stueck * 1.2),
            'default': int(stueck * 1.03),
            'schritt': 5,
            'einheit': 'Fahrzeuge',
            'info': f'2024: {stueck} Fahrzeuge ({standort_name})'
        },
        {
            'nummer': 2,
            'titel': 'Bruttoertrag pro Fahrzeug',
            'frage': 'Welchen Bruttoertrag pro Fahrzeug streben Sie an?',
            'icon': '💰',
            'typ_feld': 'slider',
            'feld': 'bruttoertrag_pro_fzg',
            'vorjahr': be_pro_fzg,
            'minimum': benchmarks.get('bruttoertrag_pro_fzg', {}).get('min', 1500),
            'maximum': int(be_pro_fzg * 1.2),
            'default': be_pro_fzg,
            'schritt': 50,
            'einheit': '€',
            'benchmark': benchmarks.get('bruttoertrag_pro_fzg', {}),
            'info': f'2024: €{be_pro_fzg:,} | Branche: €{benchmarks.get("bruttoertrag_pro_fzg", {}).get("min", 0):,}-{benchmarks.get("bruttoertrag_pro_fzg", {}).get("max", 0):,}',
            'bewertung': 'excellent' if be_pro_fzg > benchmarks.get('bruttoertrag_pro_fzg', {}).get('max', 9999) else (
                'gut' if be_pro_fzg >= benchmarks.get('bruttoertrag_pro_fzg', {}).get('min', 0) else 'kritisch'
            )
        },
        {
            'nummer': 3,
            'titel': 'Variable Kosten-Quote',
            'frage': 'Wie hoch soll die variable Kostenquote sein?',
            'icon': '📊',
            'typ_feld': 'slider',
            'feld': 'variable_kosten_quote',
            'vorjahr': kpis.get('variable_kosten_quote', 30),
            'minimum': 15,
            'maximum': 45,
            'default': min(kpis.get('variable_kosten_quote', 30), benchmarks.get('variable_kosten_quote', {}).get('max', 35)),
            'schritt': 1,
            'einheit': '%',
            'benchmark': benchmarks.get('variable_kosten_quote', {}),
            'info': f'2024: {kpis.get("variable_kosten_quote", 0):.1f}% | Ziel: <{benchmarks.get("variable_kosten_quote", {}).get("max", 35)}%',
            'invertiert': True
        },
        {
            'nummer': 4,
            'titel': 'Wachstumsstrategie',
            'frage': 'Welche Strategie verfolgen Sie?',
            'icon': '🎯',
            'typ_feld': 'auswahl',
            'feld': 'strategie',
            'optionen': [
                {'wert': 'konservativ', 'label': 'Konservativ', 'beschreibung': 'Fokus auf Stabilität, 0% Wachstum', 'faktor': 1.00},
                {'wert': 'moderat', 'label': 'Moderat', 'beschreibung': 'Leichtes Wachstum, +3%', 'faktor': 1.03},
                {'wert': 'ambitioniert', 'label': 'Ambitioniert', 'beschreibung': 'Aggressives Wachstum, +5-7%', 'faktor': 1.05}
            ],
            'default': 'moderat'
        },
        {
            'nummer': 5,
            'titel': 'Bestätigung & Monatsverteilung',
            'frage': 'Prüfen Sie die Zusammenfassung und bestätigen Sie den Plan.',
            'icon': '✅',
            'typ_feld': 'bestaetigung',
            'feld': 'bestaetigt',
            'zusammenfassung': True,
            'info': 'Der Plan wird automatisch auf Monate verteilt (Saisonalisierung)',
            'saisonalisierung': SAISONALISIERUNG.get(typ, [8.33] * 12)
        }
    ]

    # Empfehlungen basierend auf Standort
    empfehlungen = []
    if standort == 3:  # Landau
        empfehlungen.append({
            'prioritaet': 1,
            'icon': '⚠️',
            'titel': 'Standort Landau kritisch',
            'text': f'{typ} Betriebsergebnis 2024: €{ist_detail.get("betriebsergebnis", 0):,}',
            'massnahme': 'Volumen erhöhen oder Kostenstruktur anpassen'
        })

    if be_pro_fzg > benchmarks.get('bruttoertrag_pro_fzg', {}).get('max', 9999):
        empfehlungen.append({
            'prioritaet': 3,
            'icon': '⭐',
            'titel': 'Exzellente Marge',
            'text': f'€{be_pro_fzg:,}/Fzg übertrifft Branchenschnitt deutlich!',
            'massnahme': 'Niveau halten, Stückzahl-Potenzial prüfen'
        })

    return jsonify({
        'success': True,
        'typ': typ,
        'standort': standort,
        'standort_name': standort_name,
        'planjahr': planjahr,
        'fragen': fragen,
        'ist_2024': ist_detail,
        'kpis': kpis,
        'benchmarks': benchmarks,
        'empfehlungen': empfehlungen
    })


@budget_bp.route('/wizard/<typ>/berechnen', methods=['POST'])
def wizard_berechnen(typ):
    """
    Berechnet Budget aus Wizard-Eingaben.

    Body:
        stueck: Geplante Stückzahl
        bruttoertrag_pro_fzg: Geplanter BE/Fzg
        variable_kosten_quote: Geplante VK-Quote
        strategie: konservativ|moderat|ambitioniert

    Returns:
        Vollständiger Jahresplan mit Monatsverteilung
    """
    typ = typ.upper()
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'Keine Daten'}), 400

    stueck = data.get('stueck', 0)
    be_pro_fzg = data.get('bruttoertrag_pro_fzg', 2000)
    vk_quote = data.get('variable_kosten_quote', 30)
    strategie = data.get('strategie', 'moderat')

    # Berechnungen
    bruttoertrag = stueck * be_pro_fzg
    variable_kosten = bruttoertrag * vk_quote / 100
    db1 = bruttoertrag - variable_kosten

    # Umsatz schätzen (basierend auf 2024 Verhältnis)
    ist = GLOBALCUBE_IST_2024.get(typ, {}).get('kpis', {})
    marge_vorjahr = ist.get('bruttoertrag_marge', 10) / 100
    umsatz = bruttoertrag / marge_vorjahr if marge_vorjahr > 0 else bruttoertrag * 10

    # Jahresplan
    jahresplan = {
        'stueck': stueck,
        'umsatz': round(umsatz),
        'bruttoertrag': bruttoertrag,
        'variable_kosten': round(variable_kosten),
        'db1': round(db1),
        'be_pro_fzg': be_pro_fzg,
        'vk_quote': vk_quote,
        'strategie': strategie
    }

    # Monatsverteilung
    saison = SAISONALISIERUNG.get(typ, [8.33] * 12)
    monate = []
    monatsnamen = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

    for i, prozent in enumerate(saison):
        faktor = prozent / 100
        monate.append({
            'monat': i + 1,
            'name': monatsnamen[i],
            'prozent': prozent,
            'stueck': round(stueck * faktor),
            'umsatz': round(umsatz * faktor),
            'bruttoertrag': round(bruttoertrag * faktor),
            'db1': round(db1 * faktor)
        })

    return jsonify({
        'success': True,
        'typ': typ,
        'jahresplan': jahresplan,
        'monate': monate,
        'saisonalisierung': saison
    })


@budget_bp.route('/wizard/<typ>/speichern', methods=['POST'])
def wizard_speichern(typ):
    """
    Speichert Budget-Plan aus Wizard in die Datenbank.

    Body:
        stueck: Geplante Stückzahl
        bruttoertrag_pro_fzg: Geplanter BE/Fzg
        variable_kosten_quote: Geplante VK-Quote
        strategie: konservativ|moderat|ambitioniert
        standort: Optional - Standort-ID (1, 2, 3)
        jahr: Optional - Planjahr (default: aktuelles Jahr + 1)
        user: Optional - Benutzername

    Returns:
        Erfolgs-/Fehlermeldung mit gespeichertem Plan
    """
    typ = typ.upper()
    if typ not in ['NW', 'GW']:
        return jsonify({'success': False, 'error': 'Typ muss NW oder GW sein'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Keine Daten'}), 400

    try:
        # Parameter extrahieren
        stueck = data.get('stueck', 0)
        be_pro_fzg = data.get('bruttoertrag_pro_fzg', 2000)
        vk_quote = data.get('variable_kosten_quote', 30)
        strategie = data.get('strategie', 'moderat')
        standort = data.get('standort')  # None = alle Standorte
        jahr = data.get('jahr', datetime.now().year + 1)
        user = data.get('user', 'wizard')

        # Berechnungen
        bruttoertrag = stueck * be_pro_fzg
        variable_kosten = bruttoertrag * vk_quote / 100
        db1 = bruttoertrag - variable_kosten

        # Umsatz schätzen
        ist = GLOBALCUBE_IST_2024.get(typ, {}).get('kpis', {})
        marge_vorjahr = ist.get('bruttoertrag_marge', 10) / 100
        umsatz = bruttoertrag / marge_vorjahr if marge_vorjahr > 0 else bruttoertrag * 10

        # Monatsverteilung berechnen
        saison = SAISONALISIERUNG.get(typ, [8.33] * 12)

        conn = get_db()
        cursor = conn.cursor()

        # Standort-Verteilung (wenn kein spezifischer Standort)
        if standort:
            standorte_verteilung = {standort: 1.0}
        else:
            # Basierend auf 2024-Verteilung
            if typ == 'NW':
                standorte_verteilung = {1: 0.48, 2: 0.44, 3: 0.08}  # DEG, HYU, LAN
            else:  # GW
                standorte_verteilung = {1: 0.48, 2: 0.26, 3: 0.26}

        gespeicherte_plaene = []

        for s_id, s_anteil in standorte_verteilung.items():
            for monat_idx, prozent in enumerate(saison):
                monat = monat_idx + 1
                faktor = prozent / 100

                monat_stueck = round(stueck * faktor * s_anteil)
                monat_umsatz = round(umsatz * faktor * s_anteil)
                monat_db1 = round(db1 * faktor * s_anteil)

                # Marge berechnen
                marge = (monat_db1 / monat_umsatz * 100) if monat_umsatz > 0 else 0

                cursor.execute('''
                    INSERT INTO budget_plan (jahr, monat, standort, typ, stueck_plan, umsatz_plan, db1_plan, marge_plan, erstellt_von, kommentar)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (jahr, monat, standort, typ)
                    DO UPDATE SET
                        stueck_plan = EXCLUDED.stueck_plan,
                        umsatz_plan = EXCLUDED.umsatz_plan,
                        db1_plan = EXCLUDED.db1_plan,
                        marge_plan = EXCLUDED.marge_plan,
                        erstellt_von = EXCLUDED.erstellt_von,
                        kommentar = EXCLUDED.kommentar,
                        erstellt_am = CURRENT_TIMESTAMP
                ''', (
                    jahr, monat, s_id, typ,
                    monat_stueck, monat_umsatz, monat_db1, round(marge, 2),
                    user, f'Wizard: {strategie}'
                ))

            gespeicherte_plaene.append({
                'standort': s_id,
                'standort_name': STANDORTE.get(s_id, {}).get('name', f'Standort {s_id}'),
                'stueck': round(stueck * s_anteil),
                'umsatz': round(umsatz * s_anteil),
                'db1': round(db1 * s_anteil)
            })

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'{typ}-Budget für {jahr} erfolgreich gespeichert',
            'typ': typ,
            'jahr': jahr,
            'jahresplan': {
                'stueck': stueck,
                'umsatz': round(umsatz),
                'bruttoertrag': bruttoertrag,
                'db1': round(db1),
                'strategie': strategie
            },
            'standorte': gespeicherte_plaene
        })

    except Exception as e:
        logger.error(f"Wizard speichern Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@budget_bp.route('/wizard-plaene')
def wizard_plaene():
    """
    Gibt alle gespeicherten Wizard-Pläne zurück.

    Query-Params:
        jahr: Optional - Planjahr (default: aktuelles Jahr + 1)

    Returns:
        Liste aller Pläne gruppiert nach Typ und Standort
    """
    jahr = request.args.get('jahr', datetime.now().year + 1, type=int)

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                typ,
                standort,
                SUM(stueck_plan) as stueck_gesamt,
                SUM(umsatz_plan) as umsatz_gesamt,
                SUM(db1_plan) as db1_gesamt,
                AVG(marge_plan) as marge_avg,
                MAX(erstellt_am) as letzte_aenderung,
                MAX(erstellt_von) as erstellt_von,
                MAX(kommentar) as kommentar
            FROM budget_plan
            WHERE jahr = %s
            GROUP BY typ, standort
            ORDER BY typ, standort
        ''', (jahr,))

        rows = cursor.fetchall()
        conn.close()

        plaene = []
        for row in rows:
            standort_name = STANDORTE.get(row['standort'], {}).get('name', f'Standort {row["standort"]}')
            plaene.append({
                'typ': row['typ'],
                'standort': row['standort'],
                'standort_name': standort_name,
                'stueck': int(row['stueck_gesamt'] or 0),
                'umsatz': float(row['umsatz_gesamt'] or 0),
                'db1': float(row['db1_gesamt'] or 0),
                'marge': round(float(row['marge_avg'] or 0), 2),
                'letzte_aenderung': row['letzte_aenderung'].isoformat() if row['letzte_aenderung'] else None,
                'erstellt_von': row['erstellt_von'],
                'strategie': row['kommentar'].replace('Wizard: ', '') if row['kommentar'] else None
            })

        # Zusammenfassung
        zusammenfassung = {
            'NW': {'stueck': 0, 'umsatz': 0, 'db1': 0},
            'GW': {'stueck': 0, 'umsatz': 0, 'db1': 0}
        }
        for p in plaene:
            if p['typ'] in zusammenfassung:
                zusammenfassung[p['typ']]['stueck'] += p['stueck']
                zusammenfassung[p['typ']]['umsatz'] += p['umsatz']
                zusammenfassung[p['typ']]['db1'] += p['db1']

        return jsonify({
            'success': True,
            'jahr': jahr,
            'plaene': plaene,
            'zusammenfassung': zusammenfassung,
            'anzahl': len(plaene)
        })

    except Exception as e:
        logger.error(f"Wizard-Pläne laden Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Tabellen initialisieren
try:
    init_budget_tables()
except Exception as e:
    logger.warning(f"Budget-Tabellen Init: {e}")
