"""
Unternehmensplan API - Endpoints für 1%-Rendite Dashboard
=========================================================

TAG157: Gesamtunternehmensplanung mit Gap-Analyse

Author: Claude AI + Florian Greiner
Date: 2026-01-02
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from api.unternehmensplan_data import (
    get_current_geschaeftsjahr,
    get_gj_months,
    get_ist_daten,
    get_plan_daten,
    get_gap_analyse,
    get_kumulierte_ytd_ansicht,
    get_letzter_abgeschlossener_monat,
    save_plan,
    BEREICHE
)

unternehmensplan_bp = Blueprint('unternehmensplan', __name__, url_prefix='/api/unternehmensplan')


@unternehmensplan_bp.route('/health')
def health():
    """Health Check"""
    return jsonify({
        'status': 'ok',
        'modul': 'unternehmensplan',
        'geschaeftsjahr': get_current_geschaeftsjahr(),
        'letzter_abgeschlossener_monat': '/'.join(map(str, get_letzter_abgeschlossener_monat()))
    })


@unternehmensplan_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Haupt-Dashboard für 1%-Rendite Übersicht

    Query-Params:
        gj: Geschäftsjahr (default: aktuell)
        standort: 0=Alle (default), 1=DEG, 2=HYU, 3=LAN

    Returns:
        - ist: IST-Daten aus TEK (inkl. vorläufiger Monate für tägliche Aktualisierung)
        - gap: Gap-Analyse zum 1%-Ziel
        - bereiche: Auflistung nach Kostenstellen
    """
    gj = request.args.get('gj', get_current_geschaeftsjahr())
    standort = int(request.args.get('standort', 0))

    try:
        # TAG162: Immer alle Monate mit Daten anzeigen (für tägliche Aktualisierung)
        ist = get_ist_daten(gj, standort, nur_abgeschlossene=False)
        gap = get_gap_analyse(gj, standort)

        return jsonify({
            'geschaeftsjahr': gj,
            'standort': standort,
            'datenstand': ist.get('datenstand'),
            'ist': ist,
            'gap': gap,
            'bereiche': BEREICHE,
            'ziel_rendite': 1.0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@unternehmensplan_bp.route('/ist')
@login_required
def ist_daten():
    """
    IST-Daten aus TEK für das Geschäftsjahr

    Query-Params:
        gj: Geschäftsjahr
        standort: 0-3
        vorläufig: true = inkl. laufender Monat (ohne finale Kosten)
    """
    gj = request.args.get('gj', get_current_geschaeftsjahr())
    standort = int(request.args.get('standort', 0))
    vorlaeufig = request.args.get('vorlaeufig', 'false').lower() == 'true'

    try:
        ist = get_ist_daten(gj, standort, nur_abgeschlossene=not vorlaeufig)
        return jsonify(ist)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@unternehmensplan_bp.route('/gap')
@login_required
def gap_analyse():
    """
    Gap-Analyse: IST vs 1%-Ziel mit Handlungsempfehlungen

    Query-Params:
        gj: Geschäftsjahr
        standort: 0-3
    """
    gj = request.args.get('gj', get_current_geschaeftsjahr())
    standort = int(request.args.get('standort', 0))

    try:
        gap = get_gap_analyse(gj, standort)
        return jsonify(gap)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@unternehmensplan_bp.route('/plan', methods=['GET'])
@login_required
def plan_abrufen():
    """
    Gespeicherte Plandaten abrufen

    Query-Params:
        gj: Geschäftsjahr
        standort: 0-3
    """
    gj = request.args.get('gj', get_current_geschaeftsjahr())
    standort = int(request.args.get('standort', 0))

    try:
        plan = get_plan_daten(gj, standort)
        return jsonify(plan)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@unternehmensplan_bp.route('/plan', methods=['POST'])
@login_required
def plan_speichern():
    """
    Plan speichern

    Body:
        geschaeftsjahr: str
        standort: int
        monate: Dict[monat, Dict[bereich, {umsatz, einsatz, db1, kosten}]]
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Keine Daten übermittelt'}), 400

    gj = data.get('geschaeftsjahr', get_current_geschaeftsjahr())
    standort = data.get('standort', 0)
    plan_data = data.get('monate', {})

    if not plan_data:
        return jsonify({'error': 'Keine Monatsdaten'}), 400

    try:
        save_plan(gj, standort, plan_data, current_user.username)
        return jsonify({
            'success': True,
            'message': f'Plan für GJ {gj} gespeichert',
            'monate': len(plan_data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@unternehmensplan_bp.route('/monate')
@login_required
def monate():
    """Liste der Monate im Geschäftsjahr"""
    gj = request.args.get('gj', get_current_geschaeftsjahr())
    return jsonify(get_gj_months(gj))


@unternehmensplan_bp.route('/bereiche')
@login_required
def bereiche():
    """Liste der verfügbaren Bereiche/Kostenstellen"""
    return jsonify({
        'bereiche': BEREICHE,
        'beschreibung': {
            'NW': 'Neuwagen (KST 10)',
            'GW': 'Gebrauchtwagen (KST 20)',
            'Teile': 'Teile & Zubehör (KST 30)',
            'Werkstatt': 'Werkstatt/Lohn (KST 40)',
            'Sonstige': 'Sonstige Erlöse (KST 60)'
        },
        'ziel_margen': {
            'NW': 8.0,
            'GW': 5.0,
            'Teile': 28.0,
            'Werkstatt': 55.0,
            'Sonstige': 50.0
        }
    })


@unternehmensplan_bp.route('/ytd')
@login_required
def ytd_kumuliert():
    """
    Kumulierte YTD-Ansicht für 1%-Ziel-Tracking (TAG162)

    Zeigt monatliche Entwicklung mit:
    - Einzelmonatswerte + kumulierte Werte
    - 1%-Ziel-Erreichung pro Monat
    - Trend über Zeit
    - Jahresendprognose basierend auf bisheriger Performance
    - Notwendige Verbesserung pro Monat um Ziel zu erreichen

    Query-Params:
        gj: Geschäftsjahr (default: aktuell)
        standort: 0=Alle, 1=DEG, 2=HYU, 3=LAN

    Returns:
        - monate: Liste mit Einzel- und kumulierten Werten
        - ytd: Aktuelle YTD-Zusammenfassung
        - durchschnitt_monat: Monatliche Durchschnittswerte
        - prognose_jahresende: Hochrechnung auf 12 Monate
        - verbesserung_noetig: Was fehlt noch pro Monat
    """
    gj = request.args.get('gj', get_current_geschaeftsjahr())
    standort = int(request.args.get('standort', 0))

    try:
        ytd = get_kumulierte_ytd_ansicht(gj, standort)
        return jsonify(ytd)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
