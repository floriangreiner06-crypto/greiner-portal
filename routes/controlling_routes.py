"""
GREINER DRIVE - CONTROLLING MODULE
Executive Dashboard & Financial Analytics
"""
from flask import Blueprint, render_template, jsonify
from decorators.auth_decorators import login_required
import sqlite3
from datetime import datetime

controlling_bp = Blueprint('controlling', __name__, url_prefix='/controlling')

@controlling_bp.route('/dashboard')
@login_required
def dashboard():
    """Executive Controlling Dashboard - The Hero Page"""
    return render_template('controlling/dashboard.html',
                          page_title='Controlling Dashboard',
                          active_page='controlling')

@controlling_bp.route('/api/overview')
@login_required
def api_overview():
    """API: Executive Overview Metrics"""
    db = sqlite3.connect('data/greiner_controlling.db')
    db.row_factory = sqlite3.Row
    c = db.cursor()
    
    # KPI 1: OPERATIVE LIQUIDITÄT (Kontokorrent + Girokonto, OHNE Darlehen)
    c.execute("""
        SELECT COALESCE(SUM(saldo), 0) as liquiditaet
        FROM v_aktuelle_kontostaende
        WHERE kontotyp IN ('Girokonto', 'Kontokorrent')
        AND kontoname NOT LIKE '%Darlehen%'
        AND kontoname NOT LIKE '%Festgeld%'
    """)
    liquiditaet = c.fetchone()['liquiditaet']
    
    # KPI 2: ZINSEN (letzte 12 Monate aus FIBU)
    c.execute("""
        SELECT COALESCE(ABS(SUM(amount)), 0) as zinsen
        FROM fibu_buchungen
        WHERE buchungstyp = 'zinsen' 
        AND debit_credit = 'S'
        AND accounting_date >= date('now', '-12 months')
    """)
    zinsen = c.fetchone()['zinsen']
    
    # KPI 3: EINKAUFSFINANZIERUNG
    c.execute("""
        SELECT 
            COUNT(*) as anzahl,
            COALESCE(SUM(aktueller_saldo), 0) as saldo
        FROM fahrzeugfinanzierungen
    """)
    einkauf = dict(c.fetchone())
    
    # KPI 4: UMSATZ (Erlöse aus FIBU - BWA Zeile 1)
    # Sachkonten 800xx, 810xx = Erlöse
    c.execute("""
        SELECT COALESCE(SUM(amount), 0) as umsatz
        FROM fibu_buchungen
        WHERE nominal_account BETWEEN 800000 AND 819999
        AND debit_credit = 'H'
        AND accounting_date >= date('now', '-12 months')
    """)
    umsatz = c.fetchone()['umsatz']
    
    db.close()
    
    return jsonify({
        'liquiditaet': round(liquiditaet, 2),
        'zinsen': round(zinsen, 2),
        'einkauf': {
            'anzahl': einkauf['anzahl'],
            'saldo': round(einkauf['saldo'], 2)
        },
        'umsatz': round(umsatz, 2),
        'timestamp': datetime.now().isoformat()
    })

@controlling_bp.route('/api/trends')
@login_required
def api_trends():
    """API: 6-Monats-Trends"""
    # TODO: Implement in Phase 2
    return jsonify({"status": "coming_soon"})
