#!/usr/bin/env python3
"""
Routes: Jahresprämie
===================
Frontend-Routes für das Jahresprämie-Modul
"""

from flask import Blueprint, render_template
from flask_login import login_required

jahrespraemie_bp = Blueprint('jahrespraemie', __name__, url_prefix='/jahrespraemie')


@jahrespraemie_bp.route('/')
@login_required
def index():
    """Übersicht aller Berechnungen"""
    return render_template('jahrespraemie/index.html')


@jahrespraemie_bp.route('/neu')
@login_required
def neu():
    """Neue Berechnung anlegen"""
    return render_template('jahrespraemie/neu.html')


@jahrespraemie_bp.route('/<int:id>')
@login_required
def berechnung(id):
    """Berechnung bearbeiten (Hauptansicht)"""
    return render_template('jahrespraemie/berechnung.html', berechnung_id=id)


@jahrespraemie_bp.route('/<int:id>/mitarbeiter')
@login_required
def mitarbeiter(id):
    """Mitarbeiter-Übersicht"""
    return render_template('jahrespraemie/mitarbeiter.html', berechnung_id=id)


@jahrespraemie_bp.route('/<int:id>/kulanz')
@login_required
def kulanz(id):
    """Kulanz verwalten"""
    return render_template('jahrespraemie/kulanz.html', berechnung_id=id)


@jahrespraemie_bp.route('/<int:id>/export')
@login_required
def export(id):
    """Export-Optionen"""
    return render_template('jahrespraemie/export.html', berechnung_id=id)
