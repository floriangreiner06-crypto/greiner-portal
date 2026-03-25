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
from api.db_utils import get_locosoft_connection
from reports.auftragseingang_report_builder import build_auftragseingang_report_package

# ============================================================================
# KONFIGURATION
# ============================================================================

REPORT_TYPE = 'auftragseingang'  # ID in der Report-Registry
ABSENDER = "drive@auto-greiner.de"

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

        package = build_auftragseingang_report_package(heute)
        meta = package["meta"]
        print(f"📅 Tag: {package['datum_display']}")
        print(f"📆 Monat: {package['monat_display']}")
        print(f"\n📊 Heute: {meta['tag_gesamt']} Aufträge (NW: {meta['tag_nw']}, T/V: {meta['tag_tv']}, GW: {meta['tag_gw']})")
        print(f"📈 Monat: {meta['monat_gesamt']} Aufträge (NW: {meta['monat_nw']}, T/V: {meta['monat_tv']}, GW: {meta['monat_gw']})")
        print(f"   PDF erstellt: {len(package['pdf_bytes'])} Bytes")

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
            subject=package["subject"],
            body_html=package["body_html"],
            attachments=[{
                "name": package["filename"],
                "content": package["pdf_bytes"],
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
