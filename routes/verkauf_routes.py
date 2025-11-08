"""
Verkauf Routes
HTML-Seiten für Verkaufsbereich
"""

from flask import Blueprint, render_template
from datetime import datetime

verkauf_bp = Blueprint('verkauf', __name__, url_prefix='/verkauf')

@verkauf_bp.route('/auftragseingang')
def auftragseingang():
    """Auftragseingang Dashboard"""
    return render_template('verkauf_auftragseingang.html', now=datetime.now())

@verkauf_bp.route('/auftragseingang/detail')
def auftragseingang_detail():
    """Detail-Ansicht mit Modellen"""
    return render_template('verkauf_auftragseingang_detail.html')
@verkauf_bp.route('/auslieferung/detail')
def auslieferung_detail():
    """Detail-Ansicht Auslieferungen mit Modellen"""
    return render_template('verkauf_auslieferung_detail.html', now=datetime.now())
