"""
Verkauf Routes
HTML-Seiten für Verkaufsbereich
"""
from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user
from datetime import datetime
from utils.standort_filter_helpers import parse_standort_params

verkauf_bp = Blueprint('verkauf', __name__, url_prefix='/verkauf')


def _verkauf_verkaeufer_context(feature: str):
    """Kontext für Verkäufer-Ansicht inkl. Filter-Modus (own_only / own_default / all_filterable)."""
    if not current_user.is_authenticated:
        return {'restrict_to_own_salesman': False, 'salesman_number': None, 'salesman_name': None, 'filter_mode': 'all_filterable'}
    from api.feature_filter_mode import get_filter_mode
    role = getattr(current_user, 'portal_role', '') or 'mitarbeiter'
    filter_mode = get_filter_mode(role, feature)
    restrict = (filter_mode == 'own_only')
    if not restrict and filter_mode != 'own_default':
        return {'restrict_to_own_salesman': False, 'salesman_number': None, 'salesman_name': None, 'filter_mode': filter_mode}
    from api.db_utils import db_session
    username = getattr(current_user, 'username', '') or ''
    ldap_username = username.split('@')[0] if '@' in username else username
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT lem.locosoft_id, e.first_name || ' ' || e.last_name as name
            FROM ldap_employee_mapping lem
            JOIN employees e ON lem.employee_id = e.id
            WHERE lem.ldap_username = %s AND e.aktiv = true
        """, (ldap_username,))
        row = cur.fetchone()
    if not row or row[0] is None:
        return {'restrict_to_own_salesman': restrict, 'salesman_number': None, 'salesman_name': None, 'filter_mode': filter_mode}
    return {
        'restrict_to_own_salesman': restrict,
        'salesman_number': int(row[0]),
        'salesman_name': (row[1] or '').strip() or f'Verkäufer #{row[0]}',
        'filter_mode': filter_mode,
    }


@verkauf_bp.route('/dashboard')
@login_required
def verkaufsleiter_dashboard():
    """Verkaufsleiter-Dashboard (VKL, GF, Admin) – Feature verkauf_dashboard."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('verkauf_dashboard')):
        abort(403)
    return render_template('verkauf_dashboard.html', now=datetime.now())


@verkauf_bp.route('/zielauswertung')
@login_required
def zielauswertung():
    """Kompakte Zielauswertung (Trend gegen Werktage) für VKL/GF/Admin."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('verkauf_dashboard')):
        abort(403)
    return render_template('verkauf_zielauswertung.html', now=datetime.now())


@verkauf_bp.route('/auftragseingang')
@login_required
def auftragseingang():
    """Auftragseingang Dashboard. Filter-Modus aus Rechteverwaltung (nur eigene / auflösbar / alle)."""
    standort, konsolidiert = parse_standort_params(request)
    ctx = _verkauf_verkaeufer_context('auftragseingang')
    return render_template('verkauf_auftragseingang.html',
                         now=datetime.now(),
                         standort=standort,
                         konsolidiert=konsolidiert,
                         **ctx)


@verkauf_bp.route('/auftragseingang/detail')
@login_required
def auftragseingang_detail():
    """Auftragseingang Detail-Ansicht
    
    Zeigt Aufträge aufgeschlüsselt nach Verkäufer und Modellen
    """
    return render_template('verkauf_auftragseingang_detail.html', now=datetime.now())


@verkauf_bp.route('/auslieferung/detail')
@login_required
def auslieferung_detail():
    """Auslieferungen Detail-Ansicht. Filter-Modus aus Rechteverwaltung."""
    ctx = _verkauf_verkaeufer_context('auslieferungen')
    return render_template('verkauf_auslieferung_detail.html', now=datetime.now(), **ctx)


@verkauf_bp.route('/leasys-kalkulator')
@login_required
def leasys_kalkulator():
    """Leasys Kalkulator – Zugriff nur mit Feature „leasys“."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('leasys')):
        abort(403)
    return render_template('leasys_kalkulator.html', now=datetime.now())


@verkauf_bp.route('/lieferforecast')
@login_required
def lieferforecast():
    """Lieferforecast – Zugriff nur mit Feature „planung“."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('planung')):
        abort(403)
    standort, konsolidiert = parse_standort_params(request)
    return render_template('verkauf_lieferforecast.html', 
                         now=datetime.now(),
                         standort=standort,
                         konsolidiert=konsolidiert)


@verkauf_bp.route('/budget')
@verkauf_bp.route('/planung')
@login_required
def budget_planung():
    """Budget-Planung NW/GW – Zugriff nur mit Feature „planung“."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('planung')):
        abort(403)
    return render_template('verkauf_budget.html', now=datetime.now())


@verkauf_bp.route('/zielplanung')
@login_required
def zielplanung():
    """Verkäufer-Zielplanung – Zugriff nur mit Feature „verkaeufer_zielplanung“."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('verkaeufer_zielplanung')):
        abort(403)
    return render_template('verkauf_zielplanung.html', now=datetime.now())


@verkauf_bp.route('/zielplanung/verkaeufer/<int:mitarbeiter_nr>')
@login_required
def zielplanung_verkaeufer_detail(mitarbeiter_nr):
    """Detailansicht Verkäufer-Zielplanung – nur mit Feature „verkaeufer_zielplanung“."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('verkaeufer_zielplanung')):
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
@login_required
def budget_wizard():
    """Budget-Wizard – Zugriff nur mit Feature „planung“."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('planung')):
        abort(403)
    # TAG 177: Standort-Filter aus URL lesen
    standort, konsolidiert = parse_standort_params(request)
    
    return render_template('verkauf_budget_wizard.html', 
                         now=datetime.now(),
                         standort=standort,
                         konsolidiert=konsolidiert)


@verkauf_bp.route('/eautoseller-bestand')
@login_required
def eautoseller_bestand():
    """eAutoseller Live-Bestand Dashboard. Zugriff nur mit Feature „eautoseller“."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('eautoseller')):
        abort(403)
    return render_template('verkauf_eautoseller_bestand.html', now=datetime.now())


@verkauf_bp.route('/motocost')
@login_required
def motocost_dashboard():
    """Motocost Aufkauf-Ansicht (Workaround via JSON-Import)."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('verkauf_dashboard')):
        abort(403)
    return render_template('verkauf_motocost.html', now=datetime.now())


@verkauf_bp.route('/landau-90-tage-test')
@login_required
def landau_90_tage_test():
    """Testseite für den 90-Tage-Maßnahmenplan Landau (Vertrieb + Kundensicht)."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('verkauf_dashboard')):
        abort(403)
    return render_template('verkauf_landau_90_tage_test.html', now=datetime.now())


@verkauf_bp.route('/profitabilitaet')
@login_required
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
@login_required
def gw_dashboard():
    """GW-Bestand Dashboard – Zugriff nur mit Feature „gw_standzeit“."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('gw_standzeit')):
        abort(403)
    # TAG 177: Standort-Filter aus URL lesen
    standort, konsolidiert = parse_standort_params(request)
    
    return render_template('verkauf_gw_dashboard.html', 
                         now=datetime.now(),
                         standort=standort,
                         konsolidiert=konsolidiert)
