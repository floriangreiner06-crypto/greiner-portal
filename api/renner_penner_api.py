#!/usr/bin/env python3
"""
RENNER & PENNER API - Lagerumschlag-Analyse für Teile
======================================================
Identifiziert schnell- und langsamdrehende Teile im Lager.

Kategorien:
- RENNER: Hohe Umschlagshäufigkeit, niedrige Reichweite
- PENNER: Langsamdreher, hohe Kapitalbindung
- LEICHEN: Kein Verkauf seit 24+ Monaten

Endpoints:
- GET /api/lager/renner-penner - Hauptübersicht mit Kategorien
- GET /api/lager/renner - Nur Schnelldreher
- GET /api/lager/penner - Nur Langsamdreher
- GET /api/lager/leichen - Lagerleichen (24+ Monate kein Verkauf)
- GET /api/lager/statistik - Zusammenfassung Lagerwert/Kategorien
- GET /api/lager/export - CSV-Export

Author: Claude
Date: 2025-12-28 (TAG 141)
"""

import os
import sys
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, Response
import logging
from psycopg2.extras import RealDictCursor
import csv

# SSOT: Standort/Betriebsnamen
from api.standort_utils import BETRIEB_NAMEN
import io

# Zentrale DB-Utilities
from api.db_utils import get_locosoft_connection

# Logging
logger = logging.getLogger(__name__)

# Blueprint
renner_penner_bp = Blueprint('renner_penner', __name__, url_prefix='/api/lager')


# Teile-Typen (aus Locosoft)
PARTS_TYPE_NAMES = {
    0: 'Opel/Stellantis',
    1: 'Opel AT',
    5: 'Hyundai',
    6: 'Hyundai Zubehör',
    10: 'Fremdteil',
    30: 'Öl/Schmierstoff',
    60: 'Opel (AT)',
    65: 'Hyundai (AT)'
}

# BETRIEB_NAMEN wird jetzt aus standort_utils importiert (SSOT)


def kategorisiere_teil(row):
    """
    Kategorisiert ein Teil basierend auf Umschlag und Reichweite.

    Returns: dict mit kategorie, status_icon, prioritaet, empfehlung
    """
    bestand = float(row['bestand'] or 0)
    verkauf_12m = float(row['verkauf_12m'] or 0)
    lagerwert = float(row['lagerwert'] or 0)
    tage_seit_abgang = row['tage_seit_abgang']

    # Monatlicher Durchschnittsverkauf
    verkauf_monat = verkauf_12m / 12 if verkauf_12m > 0 else 0

    # Reichweite in Monaten (wie lange reicht der Bestand?)
    reichweite = bestand / verkauf_monat if verkauf_monat > 0 else 999

    # Umschlagshäufigkeit (Verkäufe / Bestand pro Jahr)
    umschlag = verkauf_12m / bestand if bestand > 0 else 0

    result = {
        'reichweite_monate': round(reichweite, 1) if reichweite < 999 else None,
        'umschlag_jahr': round(umschlag, 2),
        'verkauf_monat_avg': round(verkauf_monat, 2)
    }

    # LEICHE: Kein Verkauf seit 24+ Monaten UND Bestand > 0
    if tage_seit_abgang and tage_seit_abgang > 730:
        result['kategorie'] = 'leiche'
        result['status_icon'] = '💀'
        result['prioritaet'] = 1
        result['empfehlung'] = 'Sofort handeln! Rückgabe an Lieferant oder Abschreibung prüfen'
        return result

    # PENNER: Kein/kaum Verkauf oder sehr lange Reichweite
    if tage_seit_abgang and tage_seit_abgang > 365:
        result['kategorie'] = 'penner'
        result['status_icon'] = '🔴'
        result['prioritaet'] = 2
        result['empfehlung'] = 'Abverkauf oder Rückgabe prüfen'
        return result

    # PENNER nur bei hoher Reichweite, wenn NICHT kürzlich verkauft (Bugfix: Teile mit
    # letztem Abgang z.B. heute sind aktive Läufer, keine Ladenhüter)
    if reichweite > 24:
        tage_ok = tage_seit_abgang is None or tage_seit_abgang > 90
        if tage_ok:
            result['kategorie'] = 'penner'
            result['status_icon'] = '🔴'
            result['prioritaet'] = 2
            result['empfehlung'] = 'Bestand zu hoch - Abverkauf prüfen'
            return result
        # Kürzlich verkauft (≤90 Tage) trotz hoher Reichweite → normal, nur Hinweis
        result['kategorie'] = 'normal'
        result['status_icon'] = '🟡'
        result['prioritaet'] = 4
        result['empfehlung'] = 'Bestand hoch, Abverkauf aktiv - beobachten'
        return result

    # RENNER: Hoher Umschlag oder niedrige Reichweite
    if umschlag > 6 or (reichweite < 2 and verkauf_monat > 0):
        result['kategorie'] = 'renner'
        result['status_icon'] = '🟢'
        result['prioritaet'] = 3
        result['empfehlung'] = 'Nachbestellen prüfen - geringer Bestand!'
        return result

    if reichweite < 3:
        result['kategorie'] = 'renner'
        result['status_icon'] = '🟢'
        result['prioritaet'] = 3
        result['empfehlung'] = 'Bestand niedrig - Nachbestellung empfohlen'
        return result

    # NORMAL: Alles andere
    result['kategorie'] = 'normal'
    result['status_icon'] = '🟡'
    result['prioritaet'] = 4
    result['empfehlung'] = 'Bestand ok'

    return result


def get_base_query():
    """Basis-Query für Lagerbestand mit Kategorisierung.

    WICHTIG: Ausgeschlossen werden:
    - parts_type 1, 60, 65 = AT-Teile (Austauschteile/Garantie-Rückläufer)
    - Teile mit "KAUTION" oder "RUECKLAUFTEIL" in Beschreibung (Pfand/Garantie)
    """
    return """
        WITH lager_analyse AS (
            SELECT
                ps.part_number,
                pm.description,
                pm.parts_type,
                ps.stock_no as betrieb,
                ps.stock_level as bestand,
                ps.usage_value as ek_preis,
                pm.rr_price as vk_preis,
                ROUND((ps.stock_level * ps.usage_value)::numeric, 2) as lagerwert,
                ps.sales_current_year as verkauf_aktuell,
                ps.sales_previous_year as verkauf_vorjahr,
                -- Verkauf letzte 12 Monate (gewichtet)
                COALESCE(ps.sales_current_year, 0) +
                    (COALESCE(ps.sales_previous_year, 0) *
                     (EXTRACT(MONTH FROM CURRENT_DATE)::numeric / 12)) as verkauf_12m,
                ps.last_outflow_date as letzter_abgang,
                ps.last_inflow_date as letzter_zugang,
                -- PostgreSQL: DATE - DATE = INTEGER (Tage)
                (CURRENT_DATE - ps.last_outflow_date) as tage_seit_abgang,
                ps.minimum_stock_level as mindestbestand
            FROM parts_stock ps
            JOIN parts_master pm ON ps.part_number = pm.part_number
            WHERE ps.stock_level > 0
            -- Garantie/Gewährleistung ausschließen:
            AND pm.parts_type NOT IN (1, 60, 65)  -- AT-Teile (Austausch/Garantie)
            AND UPPER(pm.description) NOT LIKE '%KAUTION%'  -- Pfand-Teile
            AND UPPER(pm.description) NOT LIKE '%RUECKLAUFTEIL%'  -- Garantie-Rückläufer
            AND UPPER(pm.description) NOT LIKE '%ALTT%WERT%'  -- Altteil-Wert
        )
        SELECT * FROM lager_analyse
    """


def get_aggregated_by_part_query():
    """Wie get_base_query(), aber pro Teilenummer aggregiert (alle Standorte zusammengefasst).

    Jede Teilenummer erscheint nur einmal → genau eine Kategorie (kein „sowohl Renner als auch Penner“).
    """
    return """
        WITH lager_analyse AS (
            SELECT
                ps.part_number,
                pm.description,
                pm.parts_type,
                ps.stock_no as betrieb,
                ps.stock_level as bestand,
                ps.usage_value as ek_preis,
                pm.rr_price as vk_preis,
                ROUND((ps.stock_level * ps.usage_value)::numeric, 2) as lagerwert,
                ps.sales_current_year as verkauf_aktuell,
                ps.sales_previous_year as verkauf_vorjahr,
                COALESCE(ps.sales_current_year, 0) +
                    (COALESCE(ps.sales_previous_year, 0) *
                     (EXTRACT(MONTH FROM CURRENT_DATE)::numeric / 12)) as verkauf_12m,
                ps.last_outflow_date as letzter_abgang,
                (CURRENT_DATE - ps.last_outflow_date) as tage_seit_abgang,
                ps.minimum_stock_level as mindestbestand
            FROM parts_stock ps
            JOIN parts_master pm ON ps.part_number = pm.part_number
            WHERE ps.stock_level > 0
            AND pm.parts_type NOT IN (1, 60, 65)
            AND UPPER(pm.description) NOT LIKE '%KAUTION%'
            AND UPPER(pm.description) NOT LIKE '%RUECKLAUFTEIL%'
            AND UPPER(pm.description) NOT LIKE '%ALTT%WERT%'
        )
        SELECT
            part_number,
            description,
            parts_type,
            SUM(bestand)::numeric as bestand,
            SUM(lagerwert)::numeric as lagerwert,
            MAX(ek_preis)::numeric as ek_preis,
            MAX(vk_preis)::numeric as vk_preis,
            SUM(verkauf_aktuell)::numeric as verkauf_aktuell,
            SUM(verkauf_vorjahr)::numeric as verkauf_vorjahr,
            SUM(verkauf_12m)::numeric as verkauf_12m,
            MAX(letzter_abgang) as letzter_abgang,
            (CURRENT_DATE - MAX(letzter_abgang)) as tage_seit_abgang,
            SUM(mindestbestand)::numeric as mindestbestand
        FROM lager_analyse
        GROUP BY part_number, description, parts_type
    """


# =============================================================================
# API ENDPOINTS
# =============================================================================

@renner_penner_bp.route('/health', methods=['GET'])
def health_check():
    """Health-Check"""
    return jsonify({
        'status': 'ok',
        'service': 'Renner & Penner API',
        'timestamp': datetime.now().isoformat()
    })


@renner_penner_bp.route('/renner-penner', methods=['GET'])
def get_renner_penner():
    """
    GET /api/lager/renner-penner

    Hauptübersicht aller Teile mit Kategorisierung.

    Query-Parameter:
    - betrieb: Filter nach Betrieb (1, 2, 3)
    - marke: Filter nach Teile-Typ (0=Opel, 5=Hyundai, 10=Fremd, etc.)
    - kategorie: renner|penner|leiche|normal (optional)
    - min_wert: Mindest-Lagerwert in Euro (default: 50)
    - sort: lagerwert|reichweite|umschlag|tage (default: lagerwert)
    - limit: Max. Anzahl (default: 200)
    """
    try:
        betrieb = request.args.get('betrieb', type=int)
        marke = request.args.get('marke', type=int)
        kategorie_filter = request.args.get('kategorie')
        min_wert = request.args.get('min_wert', 50, type=float)
        sort = request.args.get('sort', 'lagerwert')
        limit = request.args.get('limit', 200, type=int)

        conn = get_locosoft_connection()
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Ohne Betriebsfilter: pro Teilenummer aggregieren (alle Standorte), damit jede Nummer nur in einer Kategorie landet
        if betrieb:
            query = get_base_query()
            where_clauses = [f"lagerwert >= {min_wert}", f"betrieb = {betrieb}"]
            if marke is not None:
                where_clauses.append(f"parts_type = {marke}")
            query += " WHERE " + " AND ".join(where_clauses)
        else:
            query = "SELECT * FROM (" + get_aggregated_by_part_query().strip() + ") agg WHERE lagerwert >= " + str(min_wert)
            if marke is not None:
                query += f" AND parts_type = {marke}"

        sort_map = {
            'lagerwert': 'lagerwert DESC',
            'reichweite': 'tage_seit_abgang DESC NULLS LAST',
            'umschlag': 'verkauf_12m DESC',
            'tage': 'tage_seit_abgang DESC NULLS LAST'
        }
        query += f" ORDER BY {sort_map.get(sort, 'lagerwert DESC')}"
        query += f" LIMIT {limit * 3}"

        cur.execute(query)
        rows = cur.fetchall()

        # Kategorisierung
        renner = []
        penner = []
        leichen = []
        normal = []

        for row in rows:
            rb = row.get('betrieb')
            teil = {
                'part_number': row['part_number'],
                'beschreibung': row['description'],
                'marke': PARTS_TYPE_NAMES.get(row['parts_type'], f"Typ {row['parts_type']}"),
                'parts_type': row['parts_type'],
                'betrieb': rb,
                'betrieb_name': BETRIEB_NAMEN.get(rb, '?') if rb is not None else 'Alle Standorte',
                'bestand': float(row['bestand'] or 0),
                'ek_preis': float(row['ek_preis'] or 0),
                'vk_preis': float(row['vk_preis'] or 0),
                'lagerwert': float(row['lagerwert'] or 0),
                'verkauf_aktuell': float(row['verkauf_aktuell'] or 0),
                'verkauf_vorjahr': float(row['verkauf_vorjahr'] or 0),
                'verkauf_12m': float(row['verkauf_12m'] or 0),
                'letzter_abgang': row['letzter_abgang'].strftime('%d.%m.%Y') if row.get('letzter_abgang') else None,
                'tage_seit_abgang': row.get('tage_seit_abgang'),
                'mindestbestand': float(row['mindestbestand'] or 0)
            }

            # Kategorisierung hinzufügen
            kat = kategorisiere_teil(row)
            teil.update(kat)

            # In richtige Liste einsortieren
            if teil['kategorie'] == 'renner':
                renner.append(teil)
            elif teil['kategorie'] == 'penner':
                penner.append(teil)
            elif teil['kategorie'] == 'leiche':
                leichen.append(teil)
            else:
                normal.append(teil)

        # Optional nach Kategorie filtern
        if kategorie_filter:
            if kategorie_filter == 'renner':
                result_list = renner[:limit]
            elif kategorie_filter == 'penner':
                result_list = penner[:limit]
            elif kategorie_filter == 'leiche':
                result_list = leichen[:limit]
            else:
                result_list = normal[:limit]
        else:
            result_list = None

        cur.close()
        conn.close()

        # Zusammenfassung
        alle_teile = renner + penner + leichen + normal

        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'filter': {
                'betrieb': betrieb,
                'marke': marke,
                'kategorie': kategorie_filter,
                'min_wert': min_wert,
                'sort': sort
            },
            'summary': {
                'total_teile': len(alle_teile),
                'total_lagerwert': round(sum(t['lagerwert'] for t in alle_teile), 2),
                'renner': {
                    'anzahl': len(renner),
                    'lagerwert': round(sum(t['lagerwert'] for t in renner), 2)
                },
                'penner': {
                    'anzahl': len(penner),
                    'lagerwert': round(sum(t['lagerwert'] for t in penner), 2)
                },
                'leichen': {
                    'anzahl': len(leichen),
                    'lagerwert': round(sum(t['lagerwert'] for t in leichen), 2)
                },
                'normal': {
                    'anzahl': len(normal),
                    'lagerwert': round(sum(t['lagerwert'] for t in normal), 2)
                }
            },
            'teile': result_list if result_list else {
                'renner': renner[:50],
                'penner': penner[:50],
                'leichen': leichen[:50],
                'normal': normal[:20]
            }
        })

    except Exception as e:
        logger.exception("Fehler bei Renner/Penner Analyse")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@renner_penner_bp.route('/renner', methods=['GET'])
def get_renner():
    """
    GET /api/lager/renner

    Nur Schnelldreher - Teile die nachbestellt werden sollten.
    Sortiert nach niedrigster Reichweite.
    """
    try:
        betrieb = request.args.get('betrieb', type=int)
        limit = request.args.get('limit', 50, type=int)

        conn = get_locosoft_connection()
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = get_base_query()
        where = ["lagerwert >= 20", "verkauf_12m > 0"]

        if betrieb:
            where.append(f"betrieb = {betrieb}")

        query += " WHERE " + " AND ".join(where)
        query += " ORDER BY verkauf_12m DESC LIMIT 500"

        cur.execute(query)
        rows = cur.fetchall()

        renner = []
        for row in rows:
            kat = kategorisiere_teil(row)
            if kat['kategorie'] == 'renner':
                teil = {
                    'part_number': row['part_number'],
                    'beschreibung': row['description'],
                    'marke': PARTS_TYPE_NAMES.get(row['parts_type'], '?'),
                    'bestand': float(row['bestand'] or 0),
                    'lagerwert': float(row['lagerwert'] or 0),
                    'verkauf_12m': float(row['verkauf_12m'] or 0),
                    'reichweite_monate': kat['reichweite_monate'],
                    'umschlag_jahr': kat['umschlag_jahr'],
                    'empfehlung': kat['empfehlung'],
                    'status_icon': kat['status_icon']
                }
                renner.append(teil)

                if len(renner) >= limit:
                    break

        # Nach Reichweite sortieren (niedrigste zuerst = dringend)
        renner.sort(key=lambda x: x['reichweite_monate'] or 0)

        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'anzahl': len(renner),
            'beschreibung': 'Schnelldreher - niedrige Reichweite, Nachbestellung prüfen',
            'renner': renner
        })

    except Exception as e:
        logger.exception("Fehler bei Renner-Abfrage")
        return jsonify({'success': False, 'error': str(e)}), 500


@renner_penner_bp.route('/penner', methods=['GET'])
def get_penner():
    """
    GET /api/lager/penner

    Langsamdreher - hohe Kapitalbindung, kaum Verkauf.
    Sortiert nach höchstem Lagerwert.
    """
    try:
        betrieb = request.args.get('betrieb', type=int)
        min_wert = request.args.get('min_wert', 100, type=float)
        limit = request.args.get('limit', 50, type=int)

        conn = get_locosoft_connection()
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = get_base_query()
        where = [f"lagerwert >= {min_wert}"]

        if betrieb:
            where.append(f"betrieb = {betrieb}")

        query += " WHERE " + " AND ".join(where)
        query += " ORDER BY tage_seit_abgang DESC NULLS LAST, lagerwert DESC LIMIT 500"

        cur.execute(query)
        rows = cur.fetchall()

        penner = []
        for row in rows:
            kat = kategorisiere_teil(row)
            if kat['kategorie'] in ['penner', 'leiche']:
                teil = {
                    'part_number': row['part_number'],
                    'beschreibung': row['description'],
                    'marke': PARTS_TYPE_NAMES.get(row['parts_type'], '?'),
                    'bestand': float(row['bestand'] or 0),
                    'lagerwert': float(row['lagerwert'] or 0),
                    'verkauf_12m': float(row['verkauf_12m'] or 0),
                    'letzter_abgang': row['letzter_abgang'].strftime('%d.%m.%Y') if row['letzter_abgang'] else 'Nie',
                    'tage_seit_abgang': row['tage_seit_abgang'],
                    'kategorie': kat['kategorie'],
                    'empfehlung': kat['empfehlung'],
                    'status_icon': kat['status_icon']
                }
                penner.append(teil)

                if len(penner) >= limit:
                    break

        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'anzahl': len(penner),
            'beschreibung': 'Langsamdreher - hohe Kapitalbindung, Abverkauf/Rückgabe prüfen',
            'lagerwert_gesamt': round(sum(p['lagerwert'] for p in penner), 2),
            'penner': penner
        })

    except Exception as e:
        logger.exception("Fehler bei Penner-Abfrage")
        return jsonify({'success': False, 'error': str(e)}), 500


@renner_penner_bp.route('/leichen', methods=['GET'])
def get_leichen():
    """
    GET /api/lager/leichen

    Lagerleichen - kein Verkauf seit 24+ Monaten.
    Diese binden Kapital ohne Aussicht auf Verkauf.
    """
    try:
        betrieb = request.args.get('betrieb', type=int)
        min_wert = request.args.get('min_wert', 50, type=float)
        limit = request.args.get('limit', 100, type=int)

        conn = get_locosoft_connection()
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                ps.part_number,
                pm.description,
                pm.parts_type,
                ps.stock_no as betrieb,
                ps.stock_level as bestand,
                ps.usage_value as ek_preis,
                ROUND((ps.stock_level * ps.usage_value)::numeric, 2) as lagerwert,
                ps.last_outflow_date as letzter_abgang,
                ps.last_inflow_date as letzter_zugang,
                (CURRENT_DATE - ps.last_outflow_date) as tage_seit_abgang
            FROM parts_stock ps
            JOIN parts_master pm ON ps.part_number = pm.part_number
            WHERE ps.stock_level > 0
            AND (
                ps.last_outflow_date < CURRENT_DATE - INTERVAL '730 days'
                OR ps.last_outflow_date IS NULL
            )
            AND (ps.stock_level * ps.usage_value) >= %s
            -- Garantie/Gewährleistung ausschließen:
            AND pm.parts_type NOT IN (1, 60, 65)
            AND UPPER(pm.description) NOT LIKE '%%KAUTION%%'
            AND UPPER(pm.description) NOT LIKE '%%RUECKLAUFTEIL%%'
            AND UPPER(pm.description) NOT LIKE '%%ALTT%%WERT%%'
        """
        params = [min_wert]

        if betrieb:
            query += " AND ps.stock_no = %s"
            params.append(betrieb)

        query += " ORDER BY lagerwert DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, params)
        rows = cur.fetchall()

        leichen = []
        total_wert = 0

        for row in rows:
            wert = float(row['lagerwert'] or 0)
            total_wert += wert

            leichen.append({
                'part_number': row['part_number'],
                'beschreibung': row['description'],
                'marke': PARTS_TYPE_NAMES.get(row['parts_type'], '?'),
                'betrieb': row['betrieb'],
                'betrieb_name': BETRIEB_NAMEN.get(row['betrieb'], '?'),
                'bestand': float(row['bestand'] or 0),
                'lagerwert': wert,
                'letzter_abgang': row['letzter_abgang'].strftime('%d.%m.%Y') if row['letzter_abgang'] else 'Nie',
                'letzter_zugang': row['letzter_zugang'].strftime('%d.%m.%Y') if row['letzter_zugang'] else 'Nie',
                'tage_seit_abgang': row['tage_seit_abgang'] or 9999,
                'status_icon': '💀',
                'empfehlung': 'Sofort Rückgabe/Abschreibung prüfen!'
            })

        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'anzahl': len(leichen),
            'lagerwert_gesamt': round(total_wert, 2),
            'beschreibung': 'Lagerleichen - kein Verkauf seit 24+ Monaten, bindet Kapital',
            'leichen': leichen
        })

    except Exception as e:
        logger.exception("Fehler bei Leichen-Abfrage")
        return jsonify({'success': False, 'error': str(e)}), 500


@renner_penner_bp.route('/statistik', methods=['GET'])
def get_statistik():
    """
    GET /api/lager/statistik

    Zusammenfassung: Lagerwert nach Kategorien und Marken.
    """
    try:
        conn = get_locosoft_connection()
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Gesamt-Statistik
        # In PostgreSQL: DATE - DATE = INTEGER (Tage), kein EXTRACT nötig
        cur.execute("""
            SELECT
                COUNT(DISTINCT ps.part_number) as anzahl_artikel,
                ROUND(SUM(ps.stock_level)::numeric, 0) as stueck_gesamt,
                ROUND(SUM(ps.stock_level * ps.usage_value)::numeric, 2) as lagerwert_gesamt,
                ROUND(AVG(CURRENT_DATE - ps.last_outflow_date)::numeric, 0) as avg_tage_seit_abgang
            FROM parts_stock ps
            WHERE ps.stock_level > 0
            AND ps.last_outflow_date IS NOT NULL
        """)
        gesamt = cur.fetchone()

        # Nach Marke/Teile-Typ
        cur.execute("""
            SELECT
                pm.parts_type,
                COUNT(DISTINCT ps.part_number) as anzahl,
                ROUND(SUM(ps.stock_level * ps.usage_value)::numeric, 2) as lagerwert
            FROM parts_stock ps
            JOIN parts_master pm ON ps.part_number = pm.part_number
            WHERE ps.stock_level > 0
            GROUP BY pm.parts_type
            ORDER BY lagerwert DESC
        """)
        nach_marke = []
        for row in cur.fetchall():
            nach_marke.append({
                'parts_type': row['parts_type'],
                'marke': PARTS_TYPE_NAMES.get(row['parts_type'], f"Typ {row['parts_type']}"),
                'anzahl': row['anzahl'],
                'lagerwert': float(row['lagerwert'] or 0)
            })

        # Nach Betrieb
        cur.execute("""
            SELECT
                ps.stock_no as betrieb,
                COUNT(DISTINCT ps.part_number) as anzahl,
                ROUND(SUM(ps.stock_level * ps.usage_value)::numeric, 2) as lagerwert
            FROM parts_stock ps
            WHERE ps.stock_level > 0
            GROUP BY ps.stock_no
            ORDER BY lagerwert DESC
        """)
        nach_betrieb = []
        for row in cur.fetchall():
            nach_betrieb.append({
                'betrieb': row['betrieb'],
                'betrieb_name': BETRIEB_NAMEN.get(row['betrieb'], f"Betrieb {row['betrieb']}"),
                'anzahl': row['anzahl'],
                'lagerwert': float(row['lagerwert'] or 0)
            })

        # Leichen-Wert (24+ Monate)
        cur.execute("""
            SELECT
                COUNT(*) as anzahl,
                ROUND(SUM(ps.stock_level * ps.usage_value)::numeric, 2) as lagerwert
            FROM parts_stock ps
            WHERE ps.stock_level > 0
            AND (ps.last_outflow_date < CURRENT_DATE - INTERVAL '730 days' OR ps.last_outflow_date IS NULL)
        """)
        leichen_stats = cur.fetchone()

        # Penner-Wert (12-24 Monate)
        cur.execute("""
            SELECT
                COUNT(*) as anzahl,
                ROUND(SUM(ps.stock_level * ps.usage_value)::numeric, 2) as lagerwert
            FROM parts_stock ps
            WHERE ps.stock_level > 0
            AND ps.last_outflow_date BETWEEN CURRENT_DATE - INTERVAL '730 days' AND CURRENT_DATE - INTERVAL '365 days'
        """)
        penner_stats = cur.fetchone()

        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'gesamt': {
                'anzahl_artikel': gesamt['anzahl_artikel'],
                'stueck_gesamt': float(gesamt['stueck_gesamt'] or 0),
                'lagerwert_gesamt': float(gesamt['lagerwert_gesamt'] or 0),
                'avg_tage_seit_abgang': int(gesamt['avg_tage_seit_abgang'] or 0)
            },
            'probleme': {
                'leichen': {
                    'anzahl': leichen_stats['anzahl'],
                    'lagerwert': float(leichen_stats['lagerwert'] or 0),
                    'beschreibung': '24+ Monate ohne Verkauf'
                },
                'penner': {
                    'anzahl': penner_stats['anzahl'],
                    'lagerwert': float(penner_stats['lagerwert'] or 0),
                    'beschreibung': '12-24 Monate ohne Verkauf'
                }
            },
            'nach_marke': nach_marke,
            'nach_betrieb': nach_betrieb
        })

    except Exception as e:
        logger.exception("Fehler bei Lager-Statistik")
        return jsonify({'success': False, 'error': str(e)}), 500


@renner_penner_bp.route('/marktcheck/<path:teilenummer>', methods=['GET'])
def marktcheck(teilenummer):
    """
    GET /api/lager/marktcheck/<teilenummer>

    Prüft Marktpreise für ein Teil bei externen Quellen.
    Hilft zu entscheiden ob Penner-Teile noch verkäuflich sind.
    """
    import urllib.parse
    import requests
    from bs4 import BeautifulSoup

    results = {
        'success': True,
        'teilenummer': teilenummer,
        'timestamp': datetime.now().isoformat(),
        'quellen': []
    }

    # Teilenummer URL-safe machen
    tnr_encoded = urllib.parse.quote(teilenummer)
    tnr_clean = teilenummer.replace(' ', '').replace('-', '')

    # 1. eBay Kleinanzeigen Suche
    try:
        ebay_url = f"https://www.ebay-kleinanzeigen.de/s-autoteile-reifen/{tnr_clean}/k0c210"
        results['quellen'].append({
            'name': 'eBay Kleinanzeigen',
            'url': ebay_url,
            'typ': 'gebraucht',
            'hinweis': 'Gebrauchtteile-Markt - manuell prüfen'
        })
    except:
        pass

    # 2. eBay.de (Neu + Gebraucht)
    try:
        ebay_de_url = f"https://www.ebay.de/sch/i.html?_nkw={tnr_encoded}&_sacat=131090"
        results['quellen'].append({
            'name': 'eBay.de',
            'url': ebay_de_url,
            'typ': 'neu+gebraucht',
            'hinweis': 'Auktionen und Sofortkauf'
        })
    except:
        pass

    # 3. Daparto (Preisvergleich)
    try:
        daparto_url = f"https://www.daparto.de/Suche?q={tnr_encoded}"
        results['quellen'].append({
            'name': 'Daparto',
            'url': daparto_url,
            'typ': 'neu',
            'hinweis': 'Preisvergleich Neuteile'
        })
    except:
        pass

    # 4. Autoteile-Markt.de
    try:
        atm_url = f"https://www.autoteile-markt.de/suche?q={tnr_encoded}"
        results['quellen'].append({
            'name': 'Autoteile-Markt.de',
            'url': atm_url,
            'typ': 'gebraucht',
            'hinweis': 'Verwerter und Gebrauchtteile'
        })
    except:
        pass

    # 5. Google Shopping
    try:
        google_url = f"https://www.google.de/search?q={tnr_encoded}+autoteil&tbm=shop"
        results['quellen'].append({
            'name': 'Google Shopping',
            'url': google_url,
            'typ': 'neu',
            'hinweis': 'Preisvergleich alle Shops'
        })
    except:
        pass

    # Locosoft-Daten zum Teil holen
    try:
        conn = get_locosoft_connection()
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                pm.part_number,
                pm.description,
                pm.rr_price as vk_preis,
                ps.usage_value as ek_preis,
                ps.stock_level as bestand,
                ROUND((ps.stock_level * ps.usage_value)::numeric, 2) as lagerwert
            FROM parts_master pm
            LEFT JOIN parts_stock ps ON pm.part_number = ps.part_number
            WHERE pm.part_number = %s
            LIMIT 1
        """, [teilenummer])

        teil = cur.fetchone()
        if teil:
            results['teil'] = {
                'part_number': teil['part_number'],
                'beschreibung': teil['description'],
                'vk_preis_locosoft': float(teil['vk_preis'] or 0),
                'ek_preis': float(teil['ek_preis'] or 0),
                'bestand': float(teil['bestand'] or 0),
                'lagerwert': float(teil['lagerwert'] or 0)
            }

        cur.close()
        conn.close()
    except Exception as e:
        results['teil_error'] = str(e)

    return jsonify(results)


@renner_penner_bp.route('/export', methods=['GET'])
def export_csv():
    """
    GET /api/lager/export

    CSV-Export für Excel.

    Query-Parameter:
    - kategorie: renner|penner|leiche|alle (default: alle)
    - betrieb: Filter nach Betrieb
    - min_wert: Mindest-Lagerwert (default: 50)
    """
    try:
        kategorie = request.args.get('kategorie', 'alle')
        betrieb = request.args.get('betrieb', type=int)
        min_wert = request.args.get('min_wert', 50, type=float)

        conn = get_locosoft_connection()
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = get_base_query()
        where = [f"lagerwert >= {min_wert}"]

        if betrieb:
            where.append(f"betrieb = {betrieb}")

        query += " WHERE " + " AND ".join(where)
        query += " ORDER BY lagerwert DESC LIMIT 5000"

        cur.execute(query)
        rows = cur.fetchall()

        # CSV erstellen
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        # Header
        writer.writerow([
            'Teilenummer', 'Beschreibung', 'Marke', 'Betrieb', 'Kategorie',
            'Bestand', 'EK-Preis', 'Lagerwert', 'Verkauf 12M',
            'Reichweite (Monate)', 'Umschlag/Jahr', 'Letzter Abgang',
            'Tage seit Abgang', 'Empfehlung'
        ])

        # Daten
        for row in rows:
            kat = kategorisiere_teil(row)

            # Kategorie-Filter
            if kategorie != 'alle' and kat['kategorie'] != kategorie:
                continue

            writer.writerow([
                row['part_number'],
                row['description'],
                PARTS_TYPE_NAMES.get(row['parts_type'], '?'),
                BETRIEB_NAMEN.get(row['betrieb'], '?'),
                kat['kategorie'].upper(),
                str(float(row['bestand'] or 0)).replace('.', ','),
                str(float(row['ek_preis'] or 0)).replace('.', ','),
                str(float(row['lagerwert'] or 0)).replace('.', ','),
                str(float(row['verkauf_12m'] or 0)).replace('.', ','),
                str(kat['reichweite_monate'] or '').replace('.', ','),
                str(kat['umschlag_jahr'] or 0).replace('.', ','),
                row['letzter_abgang'].strftime('%d.%m.%Y') if row['letzter_abgang'] else '',
                row['tage_seit_abgang'] or '',
                kat['empfehlung']
            ])

        cur.close()
        conn.close()

        # Response
        output.seek(0)
        filename = f"renner_penner_{kategorie}_{datetime.now().strftime('%Y%m%d')}.csv"

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'text/csv; charset=utf-8-sig'
            }
        )

    except Exception as e:
        logger.exception("Fehler bei CSV-Export")
        return jsonify({'success': False, 'error': str(e)}), 500
