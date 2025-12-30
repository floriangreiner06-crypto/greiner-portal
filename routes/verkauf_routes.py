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


@verkauf_bp.route('/lieferforecast')
def lieferforecast():
    """Lieferforecast - Geplante Fahrzeugauslieferungen

    Zeigt geplante Kundenauslieferungen mit Umsatzprognose.
    Datenquelle: Locosoft readmission_date (geplante Lieferung an Kunden)
    """
    return render_template('verkauf_lieferforecast.html', now=datetime.now())


@verkauf_bp.route('/budget')
@verkauf_bp.route('/planung')
def budget_planung():
    """Budget-Planung NW/GW (TAG 143)

    Interaktive Jahresplanung für Verkaufsleitung:
    - Benchmark-Vorschläge aus Locosoft-Historiedaten
    - Editierbare Ziele pro Monat/Standort
    - IST vs PLAN Vergleich
    """
    return render_template('verkauf_budget.html', now=datetime.now())


@verkauf_bp.route('/eautoseller-bestand')
def eautoseller_bestand():
    """eAutoseller Live-Bestand Dashboard
    
    Zeigt aktuelle Fahrzeuge auf Hof mit Standzeit-Analyse
    """
    return render_template('verkauf_eautoseller_bestand.html', now=datetime.now())
