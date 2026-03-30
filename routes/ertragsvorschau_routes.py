"""
Ertragsvorschau Routes — Dashboard + Admin
============================================
Erstellt: 2026-03-30 | Workstream: Controlling
"""

from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

ertragsvorschau_bp = Blueprint('ertragsvorschau', __name__, url_prefix='/controlling/ertragsvorschau')


@ertragsvorschau_bp.route('/')
@login_required
def dashboard():
    """Ertragsvorschau Dashboard."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('ertragsvorschau')):
        abort(403)
    return render_template('controlling/ertragsvorschau_dashboard.html')


@ertragsvorschau_bp.route('/admin')
@login_required
def admin():
    """JA-Import Admin."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('ertragsvorschau')):
        abort(403)
    return render_template('controlling/ertragsvorschau_admin.html')
