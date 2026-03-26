"""
Mail API - E-Mail-Versand aus dem Portal
Greiner Portal DRIVE

Endpoints:
- POST /api/mail/auftragseingang/send - Auftragseingang als PDF versenden
- GET /api/mail/test - Graph API Verbindung testen
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, date, timedelta

# Lokale Imports
from .graph_mail_connector import GraphMailConnector
from reports.auftragseingang_report_builder import build_auftragseingang_report_package

mail_api = Blueprint('mail_api', __name__, url_prefix='/api/mail')


@mail_api.route('/auftragseingang/send', methods=['POST'])
def send_auftragseingang_report():
    """
    POST /api/mail/auftragseingang/send
    
    Body:
    {
        "empfaenger": ["email1@auto-greiner.de", "email2@auto-greiner.de"],
        "zeitraum": "tag" oder "monat",
        "datum": "2025-11-26" (für Tag) oder null für heute,
        "monat": 11 (für Monat),
        "jahr": 2025,
        "absender": "florian.greiner@auto-greiner.de"
    }
    """
    try:
        data = request.get_json()
        
        empfaenger = data.get('empfaenger', [])
        if not empfaenger:
            return jsonify({'error': 'Keine Empfänger angegeben'}), 400
        
        zeitraum = data.get('zeitraum', 'tag')
        absender = data.get('absender')
        
        if not absender:
            return jsonify({'error': 'Kein Absender angegeben'}), 400
        
        # Stichtag bestimmen:
        # - zeitraum=tag -> exaktes Datum
        # - zeitraum=monat -> letzter Tag des Monats (oder heute, falls aktueller Monat)
        if zeitraum == 'tag':
            datum = data.get('datum') or datetime.now().strftime('%Y-%m-%d')
            anchor_date = datetime.strptime(datum, '%Y-%m-%d').date()
        else:
            jahr = data.get('jahr', datetime.now().year)
            monat = data.get('monat', datetime.now().month)
            if monat == 12:
                first_next_month = date(jahr + 1, 1, 1)
            else:
                first_next_month = date(jahr, monat + 1, 1)
            last_day_of_month = first_next_month - timedelta(days=1)
            anchor_date = min(date.today(), last_day_of_month)

        package = build_auftragseingang_report_package(anchor_date)
        
        # E-Mail senden
        connector = GraphMailConnector()
        
        connector.send_mail(
            sender_email=absender,
            to_emails=empfaenger,
            subject=package['subject'],
            body_html=package['body_html'],
            attachments=[{
                "name": package['filename'],
                "content": package['pdf_bytes'],
                "content_type": "application/pdf"
            }]
        )
        
        return jsonify({
            'success': True,
            'message': f'Report an {len(empfaenger)} Empfänger gesendet',
            'empfaenger': empfaenger,
            'datum': package['datum_display'],
            'anzahl_fahrzeuge': package['meta']['tag_gesamt']
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@mail_api.route('/test', methods=['GET'])
def test_mail_connection():
    """
    GET /api/mail/test
    
    Testet die Graph API Verbindung
    """
    try:
        connector = GraphMailConnector()
        success, message = connector.test_connection()
        
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@mail_api.route('/health', methods=['GET'])
def health():
    """Health Check"""
    return jsonify({
        'status': 'ok',
        'service': 'mail_api',
        'version': '1.0'
    })
