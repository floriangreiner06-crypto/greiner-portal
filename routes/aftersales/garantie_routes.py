"""
After Sales - Garantie Routes
- Garantie Live-Dashboard mit Handlungsempfehlungen
- Garantieaufträge-Übersicht (TAG 181)
"""
from flask import Blueprint, render_template, jsonify, request
from datetime import datetime
from decorators.auth_decorators import login_required
from flask_login import current_user

bp = Blueprint('aftersales_garantie', __name__, url_prefix='/aftersales/garantie')

@bp.route('/live-dashboard-mockup')
@bp.route('/live-dashboard-mockup/<int:order_number>')
@login_required
def live_dashboard_mockup(order_number=None):
    """
    Garantie Live-Dashboard Mockup
    Zeigt Handlungsempfehlungen für optimale Abrechnung
    """
    # Mockup-Daten (später aus API)
    mockup_data = {
        'order_number': order_number or 220345,
        'invoice_date': datetime.now().strftime('%Y-%m-%d'),
        'serviceberater': 'Salmansberger, Valentin',
        'mechaniker': 'Müller, Thomas',
        'kennzeichen': 'SR-YY 22E',
        'marke': 'Hyundai',
        'modell': 'IONIQ 5',
        'kunde': 'König, Dietmar Friedrich',
        'vorgabe_aw': 3.0,
        'gestempelt_aw': 3.8,
        'gestempelt_min': 23,
        'aktueller_lohn': 27.80,
        'potenzial': 15.17,
        'status': 'in_arbeit'
    }
    
    return render_template('aftersales/garantie_live_dashboard_mockup.html',
                         data=mockup_data,
                         now=datetime.now())

@bp.route('/auftraege')
@login_required
def garantie_auftraege_uebersicht():
    """
    Übersicht aller offenen Garantieaufträge mit Garantieakte-Status.
    """
    return render_template('aftersales/garantie_auftraege_uebersicht.html')


@bp.route('/api/live-dashboard/<int:order_number>')
@login_required
def api_live_dashboard(order_number):
    """
    API-Endpoint für Live-Dashboard Daten
    (Wird später implementiert mit echten Daten aus Locosoft)
    """
    # TODO: Echte Daten aus Locosoft holen
    # TODO: Empfehlungen berechnen
    # TODO: Status prüfen
    
    return jsonify({
        'success': True,
        'order_number': order_number,
        'message': 'API-Endpoint wird noch implementiert',
        'data': {
            'vorgabe_aw': 3.0,
            'gestempelt_aw': 3.8,
            'aktueller_lohn': 27.80,
            'potenzial': 15.17,
            'empfehlungen': [
                {
                    'typ': 'kritisch',
                    'titel': 'GDS-Grundprüfung (BASICA00) fehlt',
                    'text': 'Die GDS-Grundprüfung wurde noch nicht eingereicht.',
                    'wert': 8.43,
                    'aktionen': ['basica00_hinzufuegen', 'mehr_infos']
                },
                {
                    'typ': 'wichtig',
                    'titel': 'TT-Zeit möglich (0.8 AW)',
                    'text': 'Gestempelte Zeit ist höher als Vorgabe.',
                    'wert': 6.74,
                    'aktionen': ['tt_zeit_hinzufuegen', 'automatisch_berechnen']
                }
            ]
        }
    })
