"""
Marketing Routes – Werkstatt-Potenzial (Predictive Scoring / Call-Agent)
==========================================================================
Erstellt: 2026-02-21 | Workstream: Marketing
"""

from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

marketing_bp = Blueprint('marketing', __name__)


@marketing_bp.route('/marketing/potenzial')
@login_required
def potenzial_page():
    """Werkstatt-Potenzial – priorisierte Liste für Call-Agent / Catch-Export."""
    if not current_user.can_access_feature('marketing_potenzial'):
        abort(403)
    return render_template('marketing/potenzial.html')
