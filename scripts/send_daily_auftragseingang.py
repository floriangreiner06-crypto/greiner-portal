#!/usr/bin/env python3
"""
Täglicher Auftragseingang Report (OHNE Umsatz/DB - nur Stückzahlen!)
Versendet täglich um 17:15 Uhr per E-Mail

Schedule (Celery Beat):
15 17 * * 1-5 (Mo-Fr um 17:15 Uhr)
Task: celery_app.tasks.email_auftragseingang

Version: 2.2 (TAG146) - PostgreSQL Connection-Fix + EXTRACT statt strftime
"""

import sys
import os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')

from datetime import datetime, date
from api.db_utils import db_session, row_to_dict, get_locosoft_connection
from api.db_connection import sql_placeholder, get_db_type

# ============================================================================
# KONFIGURATION
# ============================================================================

REPORT_TYPE = 'auftragseingang'  # ID in der Report-Registry
ABSENDER = "drive@auto-greiner.de"

# Monatsnamen
MONATE = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
          'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']


def get_db():
    """Datenbank-Verbindung (TAG 146 PostgreSQL Fix)"""
    from api.db_connection import get_db as get_db_conn
    return get_db_conn()


def is_holiday(check_date=None):
    """
    Prüft ob ein Datum ein Feiertag ist (aus Locosoft year_calendar)
    TAG 136: Feiertagskalender-Integration
    """
    if check_date is None:
        check_date = date.today()

    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT is_public_holid
            FROM year_calendar
            WHERE date = %s
        """, (check_date,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            return row[0] == True
        return False

    except Exception as e:
        print(f"⚠️  Fehler bei Feiertags-Check: {e}")
        return False


def get_auftragseingang_data(day=None, month=None, year=None):
    """Holt Auftragseingang-Daten aus der Datenbank (NUR Stückzahlen, KEIN Umsatz)"""
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
        where_clauses.append("DATE(s.out_sales_contract_date) = %s")
        params.append(day)
    else:
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
        where_clauses.append("EXTRACT(YEAR FROM s.out_sales_contract_date) = %s")
        where_clauses.append("EXTRACT(MONTH FROM s.out_sales_contract_date) = %s")
        params.extend([str(year), str(month)])

    where_sql = " AND ".join(where_clauses)

    cursor.execute(f"""
        SELECT
            s.salesman_number,
            COALESCE(e.first_name || ' ' || e.last_name, 'Verkäufer #' || s.salesman_number) as verkaufer_name,
            s.dealer_vehicle_type
        FROM sales s
        LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
        WHERE {where_sql}
        ORDER BY verkaufer_name
    """, params)

    rows = cursor.fetchall()
    conn.close()

    # Nach Verkäufer aggregieren (NUR Stückzahlen)
    verkaufer_dict = {}

    for row in rows:
        vk_nr = row['salesman_number']
        vk_name = row['verkaufer_name']
        typ = row['dealer_vehicle_type']

        if vk_nr not in verkaufer_dict:
            verkaufer_dict[vk_nr] = {
                'verkaufer_nummer': vk_nr,
                'verkaufer_name': vk_name,
                'summe_neu': 0,
                'summe_test_vorfuehr': 0,
                'summe_gebraucht': 0,
                'summe_gesamt': 0
            }

        if typ == 'N':
            verkaufer_dict[vk_nr]['summe_neu'] += 1
        elif typ in ('T', 'V'):
            verkaufer_dict[vk_nr]['summe_test_vorfuehr'] += 1
        elif typ in ('G', 'D'):
            verkaufer_dict[vk_nr]['summe_gebraucht'] += 1

        verkaufer_dict[vk_nr]['summe_gesamt'] += 1

    return list(verkaufer_dict.values())


def get_subscribers():
    """Holt Empfänger aus der DB"""
    try:
        from reports.registry import get_subscriber_emails
        return get_subscriber_emails(REPORT_TYPE)
    except Exception as e:
        print(f"WARNUNG: Konnte Subscriber nicht aus DB laden: {e}")
        return []


def main():
    print(f"\n{'='*60}")
    print(f"AUFTRAGSEINGANG DAILY REPORT - {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}")

    # TAG 136: Feiertagskalender-Check
    heute = date.today()
    if is_holiday(heute):
        print(f"🎄 Heute ({heute.strftime('%d.%m.%Y')}) ist ein Feiertag - kein Report-Versand")
        print(f"{'='*60}\n")
        return 0

    # Wochenend-Check (zusätzliche Sicherheit)
    if heute.weekday() >= 5:
        print(f"📅 Wochenende - kein Report-Versand")
        print(f"{'='*60}\n")
        return 0

    # Empfänger aus DB holen
    empfaenger = get_subscribers()
    print(f"Empfänger aus DB: {len(empfaenger)}")

    if not empfaenger:
        print("KEINE EMPFÄNGER konfiguriert! Bitte in Admin → Reports hinzufügen.")
        print(f"{'='*60}\n")
        return 0

    try:
        from api.graph_mail_connector import GraphMailConnector
        from api.pdf_generator import generate_auftragseingang_komplett_pdf

        # Datum (heute bereits oben definiert)
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

        # Summen berechnen (NUR Stückzahlen)
        tag_gesamt = sum(v.get('summe_gesamt', 0) for v in tag_data)
        monat_gesamt = sum(v.get('summe_gesamt', 0) for v in monat_data)
        
        tag_nw = sum(v.get('summe_neu', 0) for v in tag_data)
        tag_tv = sum(v.get('summe_test_vorfuehr', 0) for v in tag_data)
        tag_gw = sum(v.get('summe_gebraucht', 0) for v in tag_data)
        
        monat_nw = sum(v.get('summe_neu', 0) for v in monat_data)
        monat_tv = sum(v.get('summe_test_vorfuehr', 0) for v in monat_data)
        monat_gw = sum(v.get('summe_gebraucht', 0) for v in monat_data)

        print(f"\n📊 Heute: {tag_gesamt} Aufträge (NW: {tag_nw}, T/V: {tag_tv}, GW: {tag_gw})")
        print(f"📈 Monat: {monat_gesamt} Aufträge (NW: {monat_nw}, T/V: {monat_tv}, GW: {monat_gw})")

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

        # HTML-Body (OHNE Umsatz-Spalte!)
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px;">
            <h2 style="color: #0066cc; margin-bottom: 5px;">📊 Auftragseingang</h2>
            <p style="color: #666; margin-top: 0;">Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr</p>

            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <tr style="background: #333; color: white;">
                    <th style="padding: 12px; text-align: left;"></th>
                    <th style="padding: 12px; text-align: center;">Neuwagen</th>
                    <th style="padding: 12px; text-align: center;">Test/Vorführ</th>
                    <th style="padding: 12px; text-align: center;">Gebraucht</th>
                    <th style="padding: 12px; text-align: center;">GESAMT</th>
                </tr>
                <tr style="background: #e6f2ff;">
                    <td style="padding: 12px; font-weight: bold;">📅 Heute ({datum_display})</td>
                    <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold; color: #28a745;">{tag_nw}</td>
                    <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold; color: #ffc107;">{tag_tv}</td>
                    <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold; color: #6c757d;">{tag_gw}</td>
                    <td style="padding: 12px; text-align: center; font-size: 22px; font-weight: bold; color: #0066cc;">{tag_gesamt}</td>
                </tr>
                <tr style="background: #fff3cd;">
                    <td style="padding: 12px; font-weight: bold;">📆 {monat_display}</td>
                    <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold; color: #28a745;">{monat_nw}</td>
                    <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold; color: #ffc107;">{monat_tv}</td>
                    <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold; color: #6c757d;">{monat_gw}</td>
                    <td style="padding: 12px; text-align: center; font-size: 22px; font-weight: bold; color: #0066cc;">{monat_gesamt}</td>
                </tr>
            </table>

            <p>Details im PDF-Anhang.</p>

            <p style="color: #999; font-size: 11px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
                Automatisch generiert von DRIVE<br>
                <a href="http://drive.auto-greiner.de/verkauf/auftragseingang" style="color: #0066cc;">In DRIVE öffnen</a>
            </p>
        </body>
        </html>
        """

        # Mail senden
        print(f"\nSende E-Mail...")
        print(f"   Absender: {ABSENDER}")
        print(f"   Empfänger: {len(empfaenger)} Personen")
        for emp in empfaenger:
            print(f"   - {emp}")

        connector = GraphMailConnector()
        connector.send_mail(
            sender_email=ABSENDER,
            to_emails=empfaenger,
            subject=betreff,
            body_html=body_html,
            attachments=[{
                "name": dateiname,
                "content": pdf_bytes,
                "content_type": "application/pdf"
            }]
        )

        print(f"\nERFOLG! E-Mail gesendet.")

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
