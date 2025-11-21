"""
After Sales - Teilebestellungen Routes
Stellantis ServiceBox Integration
"""
from flask import Blueprint, render_template, request, jsonify
from decorators.auth_decorators import login_required

bp = Blueprint('aftersales_teile', __name__, url_prefix='/aftersales/teile')

@bp.route('/bestellungen')
@login_required
def bestellungen():
    """Teilebestellungen Übersicht"""
    return render_template('aftersales/teilebestellungen.html')

@bp.route('/bestellung/<bestellnummer>')
@login_required
def bestellung_detail(bestellnummer):
    """Bestellung Detail-Ansicht"""
    return render_template('aftersales/bestellung_detail.html', bestellnummer=bestellnummer)
