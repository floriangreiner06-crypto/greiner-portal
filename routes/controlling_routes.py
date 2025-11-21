from flask import Blueprint, render_template, jsonify
from decorators.auth_decorators import login_required
import sqlite3
from datetime import datetime

def get_db():
    """SQLite-Verbindung herstellen"""
    conn = sqlite3.connect('data/greiner_controlling.db')
    conn.row_factory = sqlite3.Row
    return conn

controlling_bp = Blueprint('controlling', __name__, url_prefix='/controlling')

@controlling_bp.route('/dashboard')
@login_required
def dashboard():
    """Executive Controlling Dashboard - The Hero Page"""
    return render_template('controlling/dashboard.html',
                         page_title='Controlling Dashboard',
                         active_page='controlling')

@controlling_bp.route('/api/overview', methods=['GET'])
@login_required
def api_overview():
    """Dashboard Overview mit Multi-Entity-Support"""
    from flask import request
    
    try:
        db = get_db()
        include_gesellschafter = request.args.get('include_gesellschafter', 'false').lower() == 'true'
        
        # KPI 1: Operative Liquidität (Autohaus)
        operative_liq = db.execute("""
            SELECT COALESCE(SUM(saldo), 0)
            FROM v_aktuelle_kontostaende
            WHERE anzeige_gruppe = 'autohaus'
              AND ist_operativ = 1
        """).fetchone()[0]
        
        # KPI 1b: Kreditlinien
        kreditlinien = db.execute("""
            SELECT COALESCE(SUM(ABS(kreditlinie)), 0)
            FROM v_aktuelle_kontostaende
            WHERE anzeige_gruppe = 'autohaus'
              AND ist_operativ = 1
              AND kreditlinie IS NOT NULL
        """).fetchone()[0]
        # Verfügbare Fahrzeug-Linien
        fahrzeug_linien = db.execute("""
            SELECT COALESCE(SUM(original_betrag - aktueller_saldo), 0)
            FROM fahrzeugfinanzierungen
            WHERE aktiv = 1
        """).fetchone()[0]
        verfuegbare_liq = operative_liq + kreditlinien + fahrzeug_linien
        
        # KPI 2: Zinsen (12 Monate)
        zinsen = db.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM fibu_buchungen
            WHERE buchungstyp = 'zinsen'
              AND debit_credit = 'S'
              AND accounting_date >= date('now', '-12 months')
        """).fetchone()[0]
        
        # KPI 3: Einkauf
        einkauf = db.execute("""
            SELECT 
                COUNT(*) as anzahl,
                COALESCE(SUM(aktueller_saldo), 0) as summe
            FROM fahrzeugfinanzierungen
            WHERE aktiv = 1
        """).fetchone()
        
        # KPI 4: Umsatz (12 Monate)
        umsatz = db.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM fibu_buchungen
            WHERE nominal_account BETWEEN 800000 AND 899999
              AND debit_credit = 'H'
              AND accounting_date >= date('now', '-12 months')
        """).fetchone()[0]
        
        # Optional: Gesellschafter
        gesellschafter_saldo = None
        if include_gesellschafter:
            gesellschafter_saldo = db.execute("""
                SELECT COALESCE(SUM(saldo), 0)
                FROM v_aktuelle_kontostaende
                WHERE anzeige_gruppe = 'gesellschafter'
            """).fetchone()[0]
        
        response = {
            'liquiditaet': {
                'operativ': float(operative_liq),
                'kreditlinien': float(kreditlinien),
                'verfuegbar': float(verfuegbare_liq),
                'nutzungsgrad': round((operative_liq / verfuegbare_liq * 100), 1) if verfuegbare_liq > 0 else 0
            },
            'zinsen': float(zinsen),
            'einkauf': {
                'anzahl_fahrzeuge': einkauf[0],
                'finanzierungssumme': float(einkauf[1])
            },
            'umsatz': float(umsatz),
            'gesellschafter': {
                'saldo': float(gesellschafter_saldo) if gesellschafter_saldo is not None else None
            } if include_gesellschafter else None,
            'timestamp': datetime.now().isoformat()
        }
        
        db.close()
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@controlling_bp.route('/api/trends')
@login_required
def api_trends():
    """API: 6-Monats-Trends"""
    # TODO: Implement in Phase 2
    return jsonify({"status": "coming_soon"})
