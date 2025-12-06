"""
Werkstatt Routes
================
Flask Routes für Werkstatt-Modul

Erstellt: 2025-12-04 (TAG 90)
Aktualisiert: 2025-12-06 (TAG 98) - ML-Integration
"""

from flask import Blueprint, render_template
from decorators.auth_decorators import login_required, feature_required

werkstatt_routes = Blueprint('werkstatt', __name__)


@werkstatt_routes.route('/werkstatt/')
@werkstatt_routes.route('/werkstatt/uebersicht')
@login_required
def werkstatt_uebersicht():
    """Werkstatt Leistungsübersicht"""
    return render_template('aftersales/werkstatt_uebersicht.html')


@werkstatt_routes.route('/werkstatt/live')
@login_required
def werkstatt_live():
    """Werkstatt Live-Übersicht (offene Aufträge)"""
    return render_template('aftersales/werkstatt_live.html')


@werkstatt_routes.route('/werkstatt/auftraege')
@login_required
def werkstatt_auftraege():
    """Werkstatt Aufträge mit ML-Analyse - TAG 98"""
    return render_template('aftersales/werkstatt_auftraege.html')


@werkstatt_routes.route('/werkstatt/stempeluhr')
@login_required
def werkstatt_stempeluhr():
    """Stempeluhr LIVE"""
    return render_template('aftersales/werkstatt_stempeluhr.html')


@werkstatt_routes.route('/werkstatt/stempeluhr/monitor')
@login_required
def werkstatt_stempeluhr_monitor():
    """Stempeluhr Monitor (Vollbild)"""
    return render_template('aftersales/werkstatt_stempeluhr_monitor.html')


@werkstatt_routes.route('/werkstatt/tagesbericht')
@login_required
def werkstatt_tagesbericht():
    """Werkstatt Tagesbericht"""
    return render_template('aftersales/werkstatt_tagesbericht.html')


@werkstatt_routes.route('/werkstatt/serviceberater')
@login_required
def werkstatt_serviceberater():
    """Serviceberater Übersicht"""
    return render_template('aftersales/serviceberater.html')


@werkstatt_routes.route('/werkstatt/teilebestellungen')
@login_required
def werkstatt_teilebestellungen():
    """Teilebestellungen"""
    return render_template('aftersales/teilebestellungen.html')


@werkstatt_routes.route('/werkstatt/bestellung/<int:bestellung_id>')
@login_required
def werkstatt_bestellung_detail(bestellung_id):
    """Bestellungs-Detail"""
    return render_template('aftersales/bestellung_detail.html', bestellung_id=bestellung_id)


@werkstatt_routes.route('/werkstatt/preisradar')
@login_required
def werkstatt_preisradar():
    """Preisradar"""
    return render_template('aftersales/preisradar.html')
