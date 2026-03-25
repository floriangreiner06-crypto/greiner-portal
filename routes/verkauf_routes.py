"""
Verkauf Routes
HTML-Seiten für Verkaufsbereich
"""
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from datetime import datetime
from utils.standort_filter_helpers import parse_standort_params

verkauf_bp = Blueprint('verkauf', __name__, url_prefix='/verkauf')


@verkauf_bp.route('/auftragseingang')
def auftragseingang():
    """Auftragseingang Dashboard"""
    # TAG 177: Standort-Filter aus URL lesen
    standort, konsolidiert = parse_standort_params(request)
    
    return render_template('verkauf_auftragseingang.html', 
                         now=datetime.now(),
                         standort=standort,
                         konsolidiert=konsolidiert)


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
    standort, konsolidiert = parse_standort_params(request)
    return render_template(
        'verkauf_auslieferung_detail.html',
        now=datetime.now(),
        standort=standort,
        konsolidiert=konsolidiert
    )


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
    # TAG 177: Standort-Filter aus URL lesen
    standort, konsolidiert = parse_standort_params(request)
    
    return render_template('verkauf_lieferforecast.html', 
                         now=datetime.now(),
                         standort=standort,
                         konsolidiert=konsolidiert)


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


@verkauf_bp.route('/zielplanung')
@login_required
def zielplanung():
    """Verkäufer-Zielplanung (Kalenderjahr)

    NW/GW-Ziele pro Verkäufer: Konzernziele minus Pool Handelsgeschäft,
    Verteilung nach historischer Leistung (Referenzjahr). History 2023–2025.
    Zugriff: wie Budget-Planung (VKL/GF).
    """
    if current_user.portal_role not in ('admin', 'geschaeftsleitung', 'verkauf_leitung'):
        from flask import abort
        abort(403)
    return render_template('verkauf_zielplanung.html', now=datetime.now())


@verkauf_bp.route('/zielplanung/verkaeufer/<int:mitarbeiter_nr>')
@login_required
def zielplanung_verkaeufer_detail(mitarbeiter_nr):
    """Detailansicht eines Verkäufers für Planungsgespräch – nur diese Person, Vorjahr + Vorschlag + Bearbeitung."""
    if current_user.portal_role not in ('admin', 'geschaeftsleitung', 'verkauf_leitung'):
        from flask import abort
        abort(403)
    jahr = request.args.get('jahr', type=int) or datetime.now().year
    referenz_jahr = request.args.get('referenz_jahr', type=int) or max(2024, jahr - 1)
    return render_template(
        'verkauf_zielplanung_detail.html',
        mitarbeiter_nr=mitarbeiter_nr,
        jahr=jahr,
        referenz_jahr=referenz_jahr,
    )


@verkauf_bp.route('/budget/wizard')
@verkauf_bp.route('/planung/wizard')
def budget_wizard():
    """Budget-Wizard - 5 Fragen statt 50 Zeilen (TAG 155)

    Vereinfachte Budget-Planung für Abteilungsleiter:
    - 5 geführte Fragen mit Slider-Eingaben
    - Vorjahres-Benchmarks als Vorschläge
    - Automatische Monatsverteilung (Saisonalisierung)
    - Gamification mit Bewertungen
    """
    # TAG 177: Standort-Filter aus URL lesen
    standort, konsolidiert = parse_standort_params(request)
    
    return render_template('verkauf_budget_wizard.html', 
                         now=datetime.now(),
                         standort=standort,
                         konsolidiert=konsolidiert)


@verkauf_bp.route('/eautoseller-bestand')
def eautoseller_bestand():
    """eAutoseller Live-Bestand Dashboard

    Zeigt aktuelle Fahrzeuge auf Hof mit Standzeit-Analyse
    """
    return render_template('verkauf_eautoseller_bestand.html', now=datetime.now())


@verkauf_bp.route('/profitabilitaet')
def profitabilitaet():
    """Profitabilitäts-Dashboard (TAG 219) – DB pro Fahrzeug, Standkosten, Netto-Profitabilität"""
    standort, konsolidiert = parse_standort_params(request)
    return render_template(
        'verkauf_profitabilitaet.html',
        now=datetime.now(),
        standort=standort,
        konsolidiert=konsolidiert,
    )


@verkauf_bp.route('/gw-bestand')
@verkauf_bp.route('/gw-dashboard')
def gw_dashboard():
    """GW-Bestand Dashboard (TAG 160)

    Zeigt Gebrauchtwagen-Bestand mit Standzeit-Analyse:
    - Standzeit-Kategorien (Ampel)
    - Problemfaelle (>90 Tage)
    - Fahrzeugliste mit Filter
    - Daten direkt aus Locosoft
    """
    # TAG 177: Standort-Filter aus URL lesen
    standort, konsolidiert = parse_standort_params(request)
    
    return render_template('verkauf_gw_dashboard.html', 
                         now=datetime.now(),
                         standort=standort,
                         konsolidiert=konsolidiert)
