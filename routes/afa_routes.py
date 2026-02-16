"""
AfA-Modul Routes — Vorführwagen/Mietwagen (Controlling)
========================================================
Erstellt: 2026-02-16 | Workstream: Controlling
Berechtigung: controlling oder admin
"""

from flask import Blueprint, render_template, abort
from flask_login import current_user
from decorators.auth_decorators import login_required

afa_bp = Blueprint('afa', __name__, url_prefix='/controlling')


@afa_bp.route('/afa')
@login_required
def afa_dashboard():
    """AfA-Dashboard: Vorführwagen und Mietwagen — monatliche Abschreibung."""
    if not (current_user.can_access_feature('controlling') or current_user.can_access_feature('admin')):
        abort(403)
    return render_template(
        'controlling/afa_dashboard.html',
        page_title='AfA Vorführwagen / Mietwagen',
        active_page='controlling',
    )
