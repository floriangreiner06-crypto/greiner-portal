#!/usr/bin/env python3
"""
Täglicher Auftragseingang-Report per E-Mail (Mo–Fr).

Daten und Layout: reports.auftragseingang_report_builder (SSOT = VerkaufData),
identisch zum Admin-Testversand.

Schedule: Celery Beat / 17:15 – Task celery_app.tasks.email_auftragseingang
"""

import os
import sys

sys.path.insert(0, "/opt/greiner-portal")
os.chdir("/opt/greiner-portal")

from datetime import date, datetime

from api.db_utils import get_locosoft_connection

REPORT_TYPE = "auftragseingang"
ABSENDER = "drive@auto-greiner.de"


def is_holiday(check_date=None):
    """Feiertag laut Locosoft year_calendar (TAG 136)."""
    if check_date is None:
        check_date = date.today()

    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT is_public_holid
            FROM year_calendar
            WHERE date = %s
        """,
            (check_date,),
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return row[0] is True
        return False
    except Exception as e:
        print(f"⚠️  Fehler bei Feiertags-Check: {e}")
        return False


def get_subscribers():
    try:
        from reports.registry import get_subscriber_emails

        return get_subscriber_emails(REPORT_TYPE)
    except Exception as e:
        print(f"WARNUNG: Konnte Subscriber nicht aus DB laden: {e}")
        return []


def main():
    print(f"\n{'=' * 60}")
    print(f"AUFTRAGSEINGANG DAILY REPORT - {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'=' * 60}")

    heute = date.today()
    if is_holiday(heute):
        print(f"🎄 Heute ({heute.strftime('%d.%m.%Y')}) ist ein Feiertag - kein Report-Versand")
        print(f"{'=' * 60}\n")
        return 0

    if heute.weekday() >= 5:
        print("📅 Wochenende - kein Report-Versand")
        print(f"{'=' * 60}\n")
        return 0

    empfaenger = get_subscribers()
    print(f"Empfänger aus DB: {len(empfaenger)}")

    if not empfaenger:
        print("KEINE EMPFÄNGER konfiguriert! Bitte in Admin → Reports hinzufügen.")
        print(f"{'=' * 60}\n")
        return 0

    try:
        from api.graph_mail_connector import GraphMailConnector
        from reports.auftragseingang_report_builder import build_auftragseingang_report_package

        print("📦 Baue Report-Paket (VerkaufData / Builder)...")
        pkg = build_auftragseingang_report_package(heute)
        meta = pkg.get("meta") or {}

        print(
            f"📊 Heute: {meta.get('tag_gesamt', 0)} AE "
            f"(NW {meta.get('tag_nw', 0)}, T/V {meta.get('tag_tv', 0)}, GW {meta.get('tag_gw', 0)})"
        )
        print(
            f"📈 Monat: {meta.get('monat_gesamt', 0)} AE "
            f"(NW {meta.get('monat_nw', 0)}, T/V {meta.get('monat_tv', 0)}, GW {meta.get('monat_gw', 0)})"
        )
        print(f"📄 PDF: {len(pkg['pdf_bytes'])} Bytes")

        print("\nSende E-Mail...")
        print(f"   Absender: {ABSENDER}")
        for emp in empfaenger:
            print(f"   - {emp}")

        connector = GraphMailConnector()
        connector.send_mail(
            sender_email=ABSENDER,
            to_emails=empfaenger,
            subject=pkg["subject"],
            body_html=pkg["body_html"],
            attachments=[
                {
                    "name": pkg["filename"],
                    "content": pkg["pdf_bytes"],
                    "content_type": "application/pdf",
                }
            ],
        )

        print("\nERFOLG! E-Mail gesendet.")
        print(f"\n{'=' * 60}\n")
        return 0

    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback

        traceback.print_exc()
        print(f"\n{'=' * 60}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
