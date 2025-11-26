#!/usr/bin/env python3
"""
Täglicher Auftragseingang Report
Versendet täglich um 17:15 Uhr per E-Mail

Empfänger:
- peter.greiner@auto-greiner.de
- rolf.sterr@auto-greiner.de
- anton.suess@auto-greiner.de
- florian.greiner@auto-greiner.de
- margit.loibl@auto-greiner.de
- jennifer.bielmeier@auto-greiner.de

Cronjob:
15 17 * * 1-5 /opt/greiner-portal/venv/bin/python /opt/greiner-portal/scripts/send_daily_auftragseingang.py >> /opt/greiner-portal/logs/auftragseingang_mail.log 2>&1
"""

import sys
import os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')

import sqlite3
from datetime import datetime, date

# Empfänger-Liste
EMPFAENGER = [
    "peter.greiner@auto-greiner.de",
    "rolf.sterr@auto-greiner.de",
    "anton.suess@auto-greiner.de",
    "florian.greiner@auto-greiner.de",
    "margit.loibl@auto-greiner.de",
    "jennifer.bielmeier@auto-greiner.de"
]

ABSENDER = "drive@auto-greiner.de"

# Monatsnamen
MONATE = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
          'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']


def get_db():
    """SQLite Datenbank-Verbindung"""
    conn = sqlite3.connect('/opt/greiner-portal/data/greiner_controlling.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_auftragseingang_data(day=None, month=None, year=None):
    """Holt Auftragseingang-Daten aus der Datenbank"""
    conn = get_db()
    cursor = conn.cursor()
    
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
    
    cursor.execute(f"""
        SELECT
            s.salesman_number,
            COALESCE(e.first_name || ' ' || e.last_name, 'Verkäufer #' || s.salesman_number) as verkaufer_name,
            s.dealer_vehicle_type,
            COALESCE(s.out_sale_price, 0) as umsatz
        FROM sales s
        LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
        WHERE {where_sql}
        ORDER BY verkaufer_name
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
    
    for vk in verkaufer_dict.values():
        vk['umsatz_gesamt'] = round(vk['umsatz_gesamt'], 2)
    
    return list(verkaufer_dict.values())


def format_currency(value):
    """Formatiert als Euro"""
    try:
        return f"{float(value):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00 €"


def main():
    print(f"\n{'='*60}")
    print(f"📧 AUFTRAGSEINGANG DAILY REPORT - {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}")
    
    try:
        from api.graph_mail_connector import GraphMailConnector
        from api.pdf_generator import generate_auftragseingang_komplett_pdf
        
        # Datum
        heute = date.today()
        heute_str = heute.strftime('%Y-%m-%d')
        datum_display = heute.strftime('%d.%m.%Y')
        monat = heute.month
        jahr = heute.year
        monat_display = f"{MONATE[monat]} {jahr}"
        
        print(f"📅 Tag: {datum_display}")
        print(f"📆 Monat: {monat_display}")
        
        # Daten laden
        tag_data = get_auftragseingang_data(day=heute_str)
        monat_data = get_auftragseingang_data(month=monat, year=jahr)
        
        # Summen berechnen
        tag_gesamt = sum(v.get('summe_gesamt', 0) for v in tag_data)
        monat_gesamt = sum(v.get('summe_gesamt', 0) for v in monat_data)
        tag_umsatz = sum(v.get('umsatz_gesamt', 0) for v in tag_data)
        monat_umsatz = sum(v.get('umsatz_gesamt', 0) for v in monat_data)
        
        print(f"\n📊 Heute: {tag_gesamt} Aufträge ({format_currency(tag_umsatz)})")
        print(f"📈 Monat: {monat_gesamt} Aufträge ({format_currency(monat_umsatz)})")
        
        # PDF generieren
        print("\n📄 Generiere PDF...")
        pdf_bytes = generate_auftragseingang_komplett_pdf(
            tag_data=tag_data,
            monat_data=monat_data,
            datum_display=datum_display,
            monat_display=monat_display
        )
        print(f"   PDF erstellt: {len(pdf_bytes)} Bytes")
        
        # E-Mail erstellen
        dateiname = f"Auftragseingang_{heute.strftime('%Y%m%d')}.pdf"
        betreff = f"📊 Auftragseingang {datum_display} - Heute: {tag_gesamt} | Monat: {monat_gesamt}"
        
        # HTML-Body
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px;">
            <h2 style="color: #0066cc; margin-bottom: 5px;">📊 Auftragseingang</h2>
            <p style="color: #666; margin-top: 0;">Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr</p>
            
            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <tr style="background: #333; color: white;">
                    <th style="padding: 12px; text-align: left;"></th>
                    <th style="padding: 12px; text-align: center;">NW</th>
                    <th style="padding: 12px; text-align: center;">T/V</th>
                    <th style="padding: 12px; text-align: center;">GW</th>
                    <th style="padding: 12px; text-align: center;">Gesamt</th>
                    <th style="padding: 12px; text-align: right;">Umsatz</th>
                </tr>
                <tr style="background: #e6f2ff;">
                    <td style="padding: 12px; font-weight: bold;">📅 Heute ({datum_display})</td>
                    <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold; color: #28a745;">{sum(v.get('summe_neu', 0) for v in tag_data)}</td>
                    <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold; color: #ffc107;">{sum(v.get('summe_test_vorfuehr', 0) for v in tag_data)}</td>
                    <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold; color: #6c757d;">{sum(v.get('summe_gebraucht', 0) for v in tag_data)}</td>
                    <td style="padding: 12px; text-align: center; font-size: 20px; font-weight: bold;">{tag_gesamt}</td>
                    <td style="padding: 12px; text-align: right; font-weight: bold;">{format_currency(tag_umsatz)}</td>
                </tr>
                <tr style="background: #fff3cd;">
                    <td style="padding: 12px; font-weight: bold;">📆 {monat_display}</td>
                    <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold; color: #28a745;">{sum(v.get('summe_neu', 0) for v in monat_data)}</td>
                    <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold; color: #ffc107;">{sum(v.get('summe_test_vorfuehr', 0) for v in monat_data)}</td>
                    <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold; color: #6c757d;">{sum(v.get('summe_gebraucht', 0) for v in monat_data)}</td>
                    <td style="padding: 12px; text-align: center; font-size: 20px; font-weight: bold;">{monat_gesamt}</td>
                    <td style="padding: 12px; text-align: right; font-weight: bold;">{format_currency(monat_umsatz)}</td>
                </tr>
            </table>
            
            <p>Details im PDF-Anhang.</p>
            
            <p style="color: #999; font-size: 11px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
                Automatisch generiert von Greiner Portal DRIVE<br>
                <a href="https://drive.auto-greiner.de/verkauf/auftragseingang" style="color: #0066cc;">→ Im Portal öffnen</a>
            </p>
        </body>
        </html>
        """
        
        # Mail senden
        print(f"\n📧 Sende E-Mail...")
        print(f"   Absender: {ABSENDER}")
        print(f"   Empfänger: {len(EMPFAENGER)} Personen")
        
        connector = GraphMailConnector()
        connector.send_mail(
            sender_email=ABSENDER,
            to_emails=EMPFAENGER,
            subject=betreff,
            body_html=body_html,
            attachments=[{
                "name": dateiname,
                "content": pdf_bytes,
                "content_type": "application/pdf"
            }]
        )
        
        print(f"\n✅ ERFOLG! E-Mail gesendet an:")
        for emp in EMPFAENGER:
            print(f"   - {emp}")
        
        print(f"\n{'='*60}\n")
        return 0
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n{'='*60}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
