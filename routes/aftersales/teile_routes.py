"""
After Sales - Teile Routes
==========================
Redirects zu /werkstatt/... (TAG 130 - Konsolidierung)

Canonical Routes sind jetzt in werkstatt_routes.py:
- /werkstatt/teilebestellungen
- /werkstatt/preisradar
- /werkstatt/bestellung/<id>
"""
from flask import Blueprint, redirect, url_for
from decorators.auth_decorators import login_required

bp = Blueprint('aftersales_teile', __name__, url_prefix='/aftersales/teile')


@bp.route('/bestellungen')
@login_required
def bestellungen():
    """Redirect → /werkstatt/teilebestellungen"""
    return redirect(url_for('werkstatt.werkstatt_teilebestellungen'))


@bp.route('/bestellung/<bestellnummer>')
@login_required
def bestellung_detail(bestellnummer):
    """TAG173: Direktes Rendering statt Redirect"""
    from flask import render_template
    return render_template('aftersales/bestellung_detail.html', bestellnummer=bestellnummer)


@bp.route('/preisradar')
@login_required
def preisradar():
    """Redirect → /werkstatt/preisradar"""
    return redirect(url_for('werkstatt.werkstatt_preisradar'))
