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
    """Auftragseingang Detail-Ansicht
    
    Zeigt Aufträge aufgeschlüsselt nach Verkäufer und Modellen
    """
    return render_template('verkauf_auftragseingang_detail.html', now=datetime.now())


@verkauf_bp.route('/auslieferung/detail')
def auslieferung_detail():
    """Auslieferungen Detail-Ansicht
    
    Zeigt ausgelieferte Fahrzeuge aufgeschlüsselt nach Verkäufer und Modellen
    Basiert auf Rechnungsdatum
    """
    return render_template('verkauf_auslieferung_detail.html', now=datetime.now())


@verkauf_bp.route('/leasys-kalkulator')
def leasys_kalkulator():
    """Leasys Kalkulator - Fahrzeugsuche mit Preisen"""
    return render_template('leasys_kalkulator.html', now=datetime.now())
