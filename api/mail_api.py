"""
Mail API - E-Mail-Versand aus dem Portal
Greiner Portal DRIVE

Endpoints:
- POST /api/mail/auftragseingang/send - Auftragseingang als PDF versenden
- GET /api/mail/test - Graph API Verbindung testen
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import sqlite3

# Lokale Imports
from .graph_mail_connector import GraphMailConnector
from .pdf_generator import generate_auftragseingang_pdf

mail_api = Blueprint('mail_api', __name__, url_prefix='/api/mail')


def get_db():
    """SQLite Datenbank-Verbindung"""
    conn = sqlite3.connect('/opt/greiner-portal/data/greiner_controlling.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_auftragseingang_data(day=None, month=None, year=None):
    """
    Holt Auftragseingang-Daten aus der Datenbank
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Basis-Filter
    where_clauses = ["s.salesman_number IS NOT NULL"]
    params = []
    
    # Dedup-Filter
    dedup_filter = """
        NOT EXISTS (
            SELECT 1 
            FROM sales s2 
            WHERE s2.vin = s.vin 
                AND s2.out_sales_contract_date = s.out_sales_contract_date
                AND s2.dealer_vehicle_type IN ('T', 'V')
                AND s.dealer_vehicle_type = 'N'
        )
    """
    where_clauses.append(dedup_filter)
    
    if day:
        where_clauses.append("DATE(s.out_sales_contract_date) = ?")
        params.append(day)
    else:
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
        where_clauses.append("strftime('%Y', s.out_sales_contract_date) = ?")
        where_clauses.append("strftime('%m', s.out_sales_contract_date) = ?")
        params.extend([str(year), f"{month:02d}"])
    
    where_sql = " AND ".join(where_clauses)
    
    # Query
    cursor.execute(f"""
        SELECT
            s.salesman_number,
            COALESCE(e.first_name || ' ' || e.last_name, 'Verkäufer #' || s.salesman_number) as verkaufer_name,
            s.dealer_vehicle_type,
            s.model_description,
            s.vin,
            s.out_sales_contract_date,
            COALESCE(s.out_sale_price, 0) as umsatz
        FROM sales s
        LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
        WHERE {where_sql}
        ORDER BY verkaufer_name, s.dealer_vehicle_type
    """, params)
    
    rows = cursor.fetchall()
    conn.close()
    
    # Nach Verkäufer aggregieren
    verkaufer_dict = {}
    
    for row in rows:
        vk_nr = row['salesman_number']
        vk_name = row['verkaufer_name']
        typ = row['dealer_vehicle_type']
        umsatz = row['umsatz'] or 0
        
        if vk_nr not in verkaufer_dict:
            verkaufer_dict[vk_nr] = {
                'verkaufer_nummer': vk_nr,
                'verkaufer_name': vk_name,
                'summe_neu': 0,
                'summe_test_vorfuehr': 0,
                'summe_gebraucht': 0,
                'summe_gesamt': 0,
                'umsatz_gesamt': 0
            }
        
        if typ == 'N':
            verkaufer_dict[vk_nr]['summe_neu'] += 1
        elif typ in ('T', 'V'):
            verkaufer_dict[vk_nr]['summe_test_vorfuehr'] += 1
        elif typ in ('G', 'D'):
            verkaufer_dict[vk_nr]['summe_gebraucht'] += 1
        
        verkaufer_dict[vk_nr]['summe_gesamt'] += 1
        verkaufer_dict[vk_nr]['umsatz_gesamt'] += umsatz
    
    # Runden
    for vk in verkaufer_dict.values():
        vk['umsatz_gesamt'] = round(vk['umsatz_gesamt'], 2)
    
    return sorted(verkaufer_dict.values(), key=lambda x: x['verkaufer_name'])


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
        
        # Daten laden
        if zeitraum == 'tag':
            datum = data.get('datum') or datetime.now().strftime('%Y-%m-%d')
            verkaufer_list = get_auftragseingang_data(day=datum)
            datum_display = datetime.strptime(datum, '%Y-%m-%d').strftime('%d.%m.%Y')
            zeitraum_display = 'Tag'
        else:
            jahr = data.get('jahr', datetime.now().year)
            monat = data.get('monat', datetime.now().month)
            verkaufer_list = get_auftragseingang_data(month=monat, year=jahr)
            monate = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
                     'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
            datum_display = f"{monate[monat]} {jahr}"
            zeitraum_display = 'Monat'
        
        # Zusammenfassung berechnen
        summary = {
            'neu': sum(v.get('summe_neu', 0) for v in verkaufer_list),
            'test_vorfuehr': sum(v.get('summe_test_vorfuehr', 0) for v in verkaufer_list),
            'gebraucht': sum(v.get('summe_gebraucht', 0) for v in verkaufer_list),
            'gesamt': sum(v.get('summe_gesamt', 0) for v in verkaufer_list),
            'umsatz_gesamt': sum(v.get('umsatz_gesamt', 0) for v in verkaufer_list)
        }
        
        pdf_data = {
            'datum': datum_display,
            'zeitraum': zeitraum_display,
            'summary': summary,
            'verkaufer': verkaufer_list
        }
        
        # PDF generieren
        pdf_bytes = generate_auftragseingang_pdf(pdf_data)
        
        # E-Mail senden
        connector = GraphMailConnector()
        
        if zeitraum == 'tag':
            dateiname = f"Auftragseingang_{datum.replace('-', '')}.pdf"
        else:
            dateiname = f"Auftragseingang_{jahr}_{monat:02d}.pdf"
        
        betreff = f"Auftragseingang {datum_display}"
        
        # Währung formatieren
        def fmt_eur(val):
            return f"{val:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #0066cc;">Auftragseingang - {datum_display}</h2>
            <p>Im Anhang finden Sie den aktuellen Auftragseingang-Report.</p>
            
            <table style="border-collapse: collapse; margin: 20px 0; width: 100%; max-width: 500px;">
                <tr style="background: #0066cc; color: white;">
                    <th style="padding: 12px; text-align: center;">Neuwagen</th>
                    <th style="padding: 12px; text-align: center;">Test/Vorführ</th>
                    <th style="padding: 12px; text-align: center;">Gebraucht</th>
                    <th style="padding: 12px; text-align: center;">GESAMT</th>
                </tr>
                <tr style="text-align: center; font-size: 24px; font-weight: bold; background: #e6f2ff;">
                    <td style="padding: 15px; color: #28a745;">{summary['neu']}</td>
                    <td style="padding: 15px; color: #ffc107;">{summary['test_vorfuehr']}</td>
                    <td style="padding: 15px; color: #6c757d;">{summary['gebraucht']}</td>
                    <td style="padding: 15px; color: #333;">{summary['gesamt']}</td>
                </tr>
                <tr style="text-align: center; background: #f5f5f5;">
                    <td colspan="4" style="padding: 10px; font-size: 16px;">
                        <strong>Gesamtumsatz: {fmt_eur(summary['umsatz_gesamt'])}</strong>
                    </td>
                </tr>
            </table>
            
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                Automatisch generiert von Greiner Portal DRIVE<br>
                {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr
            </p>
        </body>
        </html>
        """
        
        connector.send_mail(
            sender_email=absender,
            to_emails=empfaenger,
            subject=betreff,
            body_html=body_html,
            attachments=[{
                "name": dateiname,
                "content": pdf_bytes,
                "content_type": "application/pdf"
            }]
        )
        
        return jsonify({
            'success': True,
            'message': f'Report an {len(empfaenger)} Empfänger gesendet',
            'empfaenger': empfaenger,
            'datum': datum_display,
            'anzahl_fahrzeuge': summary['gesamt']
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
