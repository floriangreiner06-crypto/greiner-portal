"""
Werkstatt Routes
================
Flask Routes für Werkstatt-Modul

Erstellt: 2025-12-04 (TAG 90)
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
