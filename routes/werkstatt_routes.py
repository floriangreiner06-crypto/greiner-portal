"""
Werkstatt Routes
================
Flask Routes für Werkstatt-Modul

Erstellt: 2025-12-04 (TAG 90)
Aktualisiert: 2025-12-06 (TAG 98) - ML-Integration
Aktualisiert: 2025-12-09 - Cockpit Route hinzugefügt
Aktualisiert: 2025-12-12 (TAG 116) - Kapazitätsplanung + Anwesenheits-Report
"""

from flask import Blueprint, render_template
from decorators.auth_decorators import login_required

werkstatt_routes = Blueprint('werkstatt', __name__)


@werkstatt_routes.route('/werkstatt/')
@werkstatt_routes.route('/werkstatt/uebersicht')
@login_required
def werkstatt_uebersicht():
    """Werkstatt Leistungsübersicht"""
    return render_template('aftersales/werkstatt_uebersicht.html')


@werkstatt_routes.route('/werkstatt/cockpit')
@login_required
def werkstatt_cockpit():
    """Werkstatt Cockpit - Ampel-System mit Live-Status"""
    return render_template('aftersales/werkstatt_cockpit.html')


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


# HINWEIS: /werkstatt/stempeluhr/monitor ist in app.py definiert (Token-Auth, kein Login)


@werkstatt_routes.route('/werkstatt/tagesbericht')
@login_required
def werkstatt_tagesbericht():
    """Werkstatt Tagesbericht"""
    return render_template('aftersales/werkstatt_tagesbericht.html')


@werkstatt_routes.route('/werkstatt/teile-status')
@login_required
def werkstatt_teile_status():
    """Teile-Status - Kritische Teile für Werkstattaufträge"""
    return render_template('aftersales/werkstatt_teile_status.html')


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


# ============================================================
# TAG 116: Kapazitätsplanung (ausgelagert aus Dashboard)
# ============================================================

@werkstatt_routes.route('/aftersales/kapazitaet')
@werkstatt_routes.route('/aftersales/kapazitaetsplanung')
@login_required
def kapazitaetsplanung():
    """Kapazitätsplanung - Forecast, Gudat, ML-Analyse"""
    return render_template('aftersales/kapazitaetsplanung.html')


@werkstatt_routes.route('/werkstatt/anwesenheit')
@login_required
def werkstatt_anwesenheit():
    """Anwesenheits-Report - Wer hat (nicht) eingestempelt?"""
    return render_template('aftersales/werkstatt_anwesenheit.html')


# ============================================================
# TAG 119: DRIVE - ML-basierte Werkstatt-Optimierung
# ============================================================

@werkstatt_routes.route('/werkstatt/drive/briefing')
@login_required
def drive_briefing():
    """DRIVE Morgen-Briefing für Werkstattleiter"""
    return render_template('aftersales/drive_briefing.html')


@werkstatt_routes.route('/werkstatt/drive/kulanz')
@login_required
def drive_kulanz():
    """DRIVE Kulanz-Monitor - Revenue Leakage Dashboard"""
    return render_template('aftersales/drive_kulanz.html')


@werkstatt_routes.route('/werkstatt/drive/kapazitaet')
@login_required
def drive_kapazitaet():
    """DRIVE ML-Kapazität mit Korrekturfaktoren"""
    return render_template('aftersales/drive_kapazitaet.html')
