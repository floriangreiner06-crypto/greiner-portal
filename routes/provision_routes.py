"""
Provisionsmodul – HTML-Views.
Live-Preview: Daten kommen ausschließlich aus provision_service (SSOT).
"""
from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from datetime import datetime

provision_bp = Blueprint('provision', __name__, url_prefix='/provision')


@provision_bp.route('/meine')
@login_required
def meine():
    """Meine Provision – Zugriff nur mit Feature „provision“."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('provision')):
        abort(403)
    now = datetime.now()
    default_monat = now.strftime('%Y-%m')
    return render_template('provision/provision_meine.html', default_monat=default_monat)


@provision_bp.route('/dashboard')
@login_required
def dashboard():
    """Provisions-Dashboard (VKL) – Zugriff nur mit Feature „provision_vkl“."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('provision_vkl')):
        abort(403)
    now = datetime.now()
    default_monat = now.strftime('%Y-%m')
    return render_template('provision/provision_dashboard.html', default_monat=default_monat)


@provision_bp.route('/detail/<int:lauf_id>')
@login_required
def detail(lauf_id):
    """Detail eines Provisionslaufs (Positionen, ggf. Einspruch)."""
    return render_template('provision/provision_detail.html', lauf_id=lauf_id)
