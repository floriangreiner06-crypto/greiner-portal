"""
After Sales - Garantie Routes
- Garantie Live-Dashboard mit Handlungsempfehlungen
- Garantieaufträge-Übersicht (TAG 181)
- Garantie Handbücher & Richtlinien (Phase 1 Wissensbasis)
"""
import os
import re
from flask import Blueprint, render_template, jsonify, request, send_file, current_app
from datetime import datetime
from decorators.auth_decorators import login_required
from flask_login import current_user

bp = Blueprint('aftersales_garantie', __name__, url_prefix='/aftersales/garantie')

# Verzeichnis Garantie-Handbücher (Sync: F:\...\Server\docs\workstreams\werkstatt\garantie)
def _garantie_handbuecher_dir():
    root = current_app.root_path if current_app else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(root, 'docs', 'workstreams', 'werkstatt', 'garantie')

# Erwartete Handbücher für die Übersichtsseite (Dateiname, Anzeigetitel, Marke/Bereich)
GARANTIE_HANDBUECHER = [
    {'datei': 'Garantie-Richtlinie Stand 01-2026.pdf', 'titel': 'Garantie-Richtlinie', 'marke': 'Übergreifend', 'stand': '01/2026'},
    {'datei': 'Garantie-Richtlinie Hyundai Stand 02-2024.pdf', 'titel': 'Garantie-Richtlinie Hyundai', 'marke': 'Hyundai', 'stand': '02/2024'},
    {'datei': 'Garantie-Handbuch Opel Stand Mai 2025.pdf', 'titel': 'Garantie-Handbuch Opel', 'marke': 'Opel / Stellantis', 'stand': 'Mai 2025'},
    {'datei': 'Garantiehandbuch Leapmotor.pdf', 'titel': 'Garantiehandbuch Leapmotor', 'marke': 'Leapmotor', 'stand': ''},
]

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


@bp.route('/handbuecher')
@login_required
def garantie_handbuecher():
    """
    Garantie – Handbücher & Richtlinien (Phase 1 Wissensbasis).
    Liste der Handbücher mit Links zum Download.
    """
    base_dir = _garantie_handbuecher_dir()
    handbuecher = []
    for h in GARANTIE_HANDBUECHER:
        path = os.path.join(base_dir, h['datei'])
        handbuecher.append({
            'datei': h['datei'],
            'titel': h['titel'],
            'marke': h['marke'],
            'stand': h['stand'],
            'vorhanden': os.path.isfile(path),
        })
    return render_template('aftersales/garantie_handbuecher.html', handbuecher=handbuecher)


@bp.route('/handbuch/<path:filename>')
@login_required
def garantie_handbuch_pdf(filename):
    """
    Stellt ein Garantie-Handbuch-PDF aus dem Sync-Verzeichnis bereit.
    Nur sichere Dateinamen (alphanumerisch, Leerzeichen, Bindestrich, Unterstrich, Punkt) erlaubt.
    """
    # Path-Traversal verhindern: nur Basename, nur .pdf
    basename = os.path.basename(filename).strip()
    if not basename.lower().endswith('.pdf'):
        return jsonify({'error': 'Nur PDF-Dateien erlaubt'}), 400
    if not re.match(r'^[a-zA-Z0-9 ._\-]+\.pdf$', basename):
        return jsonify({'error': 'Ungültiger Dateiname'}), 400
    path = os.path.join(_garantie_handbuecher_dir(), basename)
    if not os.path.isfile(path):
        return jsonify({'error': 'Datei nicht gefunden'}), 404
    return send_file(
        path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=basename,
    )


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
