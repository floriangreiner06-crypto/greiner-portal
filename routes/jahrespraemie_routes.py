#!/usr/bin/env python3
"""
Routes: Jahresprämie
===================
Frontend-Routes für das Jahresprämie-Modul
Zugriff: nur GL und Vanessa Groll
"""

from functools import wraps
from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

jahrespraemie_bp = Blueprint('jahrespraemie', __name__, url_prefix='/jahrespraemie')

_JAHRESPRAEMIE_EXTRA_USERS = {
    'vanessa.groll@auto-greiner.de',
}


def _darf_jahrespraemie():
    """GL oder Vanessa Groll"""
    if not current_user.is_authenticated:
        return False
    if current_user.can_access_feature('jahrespraemie'):
        return True
    username = (getattr(current_user, 'username', '') or '').lower()
    return username in _JAHRESPRAEMIE_EXTRA_USERS


def jahrespraemie_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _darf_jahrespraemie():
            abort(403)
        return f(*args, **kwargs)
    return decorated


@jahrespraemie_bp.route('/')
@login_required
@jahrespraemie_required
def index():
    """Übersicht aller Berechnungen"""
    return render_template('jahrespraemie/index.html')


@jahrespraemie_bp.route('/neu')
@login_required
@jahrespraemie_required
def neu():
    """Neue Berechnung anlegen"""
    return render_template('jahrespraemie/neu.html')


@jahrespraemie_bp.route('/<int:id>')
@login_required
@jahrespraemie_required
def berechnung(id):
    """Berechnung bearbeiten (Hauptansicht)"""
    return render_template('jahrespraemie/berechnung.html', berechnung_id=id)


@jahrespraemie_bp.route('/<int:id>/mitarbeiter')
@login_required
@jahrespraemie_required
def mitarbeiter(id):
    """Mitarbeiter-Übersicht"""
    return render_template('jahrespraemie/mitarbeiter.html', berechnung_id=id)


@jahrespraemie_bp.route('/<int:id>/kulanz')
@login_required
@jahrespraemie_required
def kulanz(id):
    """Kulanz verwalten"""
    return render_template('jahrespraemie/kulanz.html', berechnung_id=id)


@jahrespraemie_bp.route('/<int:id>/export')
@login_required
@jahrespraemie_required
def export(id):
    """Export-Optionen"""
    return render_template('jahrespraemie/export.html', berechnung_id=id)
