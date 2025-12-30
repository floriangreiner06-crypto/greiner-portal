#!/usr/bin/env python3
"""
TEK Daily Report - Tägliche Erfolgskontrolle per E-Mail

Versendet täglich TEK-Reports mit verschiedenen Varianten:
- Gesamt-Report: Alle Bereiche (für Geschäftsleitung)
- Filiale-Report: Alle Bereiche eines Standorts (für Filialleiter wie Rolf)
- Bereichs-Reports: Einzelne Bereiche (für Abteilungsleiter)

Report-Typen in Registry:
- tek_daily: Gesamt-Report
- tek_filiale: Standort-Report für Filialleiter
- tek_nw, tek_gw, tek_teile, tek_werkstatt: Bereichs-Reports

Schedule (Celery Beat):
30 19 * * 1-5 (Mo-Fr um 19:30 Uhr - nach Locosoft-Mirror um 19:00)
Task: celery_app.tasks.email_tek_daily

Version: 3.1 (TAG146) - 19:30 Uhr wegen Locosoft-Mirror um 19:00
"""

import sys
import os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')

from datetime import datetime, date
from scripts.tek_api_helper import get_tek_data_from_api
from api.db_utils import db_session, row_to_dict, get_locosoft_connection
from api.db_connection import sql_placeholder, get_db_type

# ============================================================================
# KONFIGURATION
# ============================================================================

# Alle TEK Report-Typen
TEK_REPORT_TYPES = {
    'tek_daily': {'name': 'TEK Gesamt', 'type': 'gesamt'},
    'tek_filiale': {'name': 'TEK Filiale', 'type': 'filiale'},
    'tek_nw': {'name': 'TEK Neuwagen', 'type': 'bereich', 'bereich_key': '1-NW'},
    'tek_gw': {'name': 'TEK Gebrauchtwagen', 'type': 'bereich', 'bereich_key': '2-GW'},
    'tek_teile': {'name': 'TEK Teile', 'type': 'bereich', 'bereich_key': '3-Teile'},
    'tek_werkstatt': {'name': 'TEK Werkstatt', 'type': 'bereich', 'bereich_key': '4-Lohn'},
}

ABSENDER = "drive@auto-greiner.de"

# Monatsnamen
MONATE = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
          'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']


def get_db():
    """Datenbank-Verbindung via db_connection (TAG 136/140)"""
    from api.db_connection import get_db as get_portal_db
    return get_portal_db()


def is_holiday(check_date=None):
    """
    Prüft ob ein Datum ein Feiertag ist (aus Locosoft year_calendar)
    TAG 136: Feiertagskalender-Integration

    Returns: True wenn Feiertag, False wenn Arbeitstag
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
        return False  # Im Fehlerfall trotzdem senden


def get_tek_data(monat=None, jahr=None, standort=None):
    """
    Wrapper für get_tek_data_from_api (TAG146: API-basiert statt DB-Queries)

    ALTE VERSION: 230 Zeilen komplexe DB-Queries
    NEUE VERSION: 1 Zeile API-Call → 100% konsistent mit DRIVE Web-UI!
    """
    return get_tek_data_from_api(monat, jahr, standort)


def format_euro(value):
    """Formatiert als Euro (deutsches Format - TAG146: OHNE 'k'-Notation!)"""
    try:
        v = float(value)
        # Deutsches Format: 1.500 € statt 1,5k
        return f"{v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0"


def get_subscribers_for_report(report_type):
    """
    Holt Empfänger für einen Report-Typ, gruppiert nach Standort.
    TAG140: Unterstützt jetzt alle TEK Report-Typen.

    Returns: dict mit standort -> [emails]
    """
    try:
        from reports.registry import get_subscribers

        # Alle Subscriber für diesen Report
        all_subs = get_subscribers(report_type)

        # Nach Standort gruppieren
        by_standort = {
            None: [],   # Alle Standorte
            'DEG': [],
            'LAN': []
        }

        for sub in all_subs:
            standort = sub.get('standort')
            email = sub.get('email')

            if standort is None or standort == '':
                # Empfänger für ALLE Standorte
                by_standort[None].append(email)
            elif standort in by_standort:
                by_standort[standort].append(email)

        return by_standort

    except Exception as e:
        print(f"WARNUNG: Konnte Subscriber für {report_type} nicht laden: {e}")
        return {None: [], 'DEG': [], 'LAN': []}


def get_subscribers_by_standort():
    """Legacy-Funktion für Kompatibilität - nutzt tek_daily"""
    return get_subscribers_for_report('tek_daily')


def send_gesamt_reports(connector, heute, test_email=None):
    """
    Sendet TEK Gesamt-Reports (tek_daily).
    Für Geschäftsleitung - alle Bereiche.
    """
    from api.pdf_generator import generate_tek_daily_pdf

    if test_email:
        # Test-Modus: Nur an Test-Adresse
        subscribers = {None: [test_email]}
        print(f"  TEST-MODUS: Sende nur an {test_email}")
    else:
        subscribers = get_subscribers_for_report('tek_daily')
    total = sum(len(v) for v in subscribers.values())

    if total == 0:
        print("  Keine Empfänger für tek_daily")
        return 0

    emails_sent = 0

    # Verarbeite nach Standort
    standorte = []
    if subscribers.get(None):
        standorte.append((None, subscribers[None]))
    for st in ['DEG', 'LAN']:
        if subscribers.get(st):
            standorte.append((st, subscribers[st]))

    for standort, empfaenger in standorte:
        standort_name = standort or 'Gesamt'
        print(f"\n    [{standort_name}] Lade Daten...")
        data = get_tek_data(standort=standort)

        print(f"    [{standort_name}] Generiere PDF...")
        pdf_bytes = generate_tek_daily_pdf(data)

        # Betreff mit Status
        gesamt = data['gesamt']
        status = "+" if gesamt['breakeven_abstand'] >= 0 else ""
        betreff = f"TEK {data['monat']} | DB1: {format_euro(gesamt['db1'])} | {status}{format_euro(gesamt['breakeven_abstand'])} vs BE"

        # HTML-Body erstellen
        body_html = build_gesamt_email_html(data)

        # Senden
        suffix = f"_{standort}" if standort else ""
        dateiname = f"TEK{suffix}_{heute.strftime('%Y%m%d')}.pdf"

        print(f"    [{standort_name}] Sende an {len(empfaenger)} Empfänger...")
        connector.send_mail(
            sender_email=ABSENDER,
            to_emails=empfaenger,
            subject=betreff,
            body_html=body_html,
            attachments=[{"name": dateiname, "content": pdf_bytes, "content_type": "application/pdf"}]
        )
        emails_sent += len(empfaenger)
        print(f"    [{standort_name}] OK!")

    return emails_sent


def send_filiale_reports(connector, heute, test_email=None):
    """
    Sendet TEK Filiale-Reports (tek_filiale).
    Für Filialleiter wie Rolf - alle Bereiche eines Standorts.
    """
    from api.pdf_generator import generate_tek_filiale_pdf

    if test_email:
        # Test-Modus: Beide Standorte an Test-Adresse
        subscribers = {'DEG': [test_email], 'LAN': [test_email]}
        print(f"  TEST-MODUS: Sende beide Filiale-Reports an {test_email}")
    else:
        subscribers = get_subscribers_for_report('tek_filiale')
    total = sum(len(v) for v in subscribers.values())

    if total == 0:
        print("  Keine Empfänger für tek_filiale")
        return 0

    emails_sent = 0

    # Filiale-Reports nur für Standorte sinnvoll (DEG, LAN)
    for standort in ['DEG', 'LAN']:
        empfaenger = subscribers.get(standort, [])
        if not empfaenger:
            continue

        print(f"\n    [Filiale {standort}] Lade Daten...")
        data = get_tek_data(standort=standort)

        print(f"    [Filiale {standort}] Generiere PDF...")
        pdf_bytes = generate_tek_filiale_pdf(data)

        gesamt = data['gesamt']
        betreff = f"TEK Filiale {data['standort_name']} | DB1: {format_euro(gesamt['db1'])} | {data['monat'].split(' - ')[-1]}"

        body_html = build_filiale_email_html(data)

        dateiname = f"TEK_Filiale_{standort}_{heute.strftime('%Y%m%d')}.pdf"

        print(f"    [Filiale {standort}] Sende an {len(empfaenger)} Empfänger...")
        connector.send_mail(
            sender_email=ABSENDER,
            to_emails=empfaenger,
            subject=betreff,
            body_html=body_html,
            attachments=[{"name": dateiname, "content": pdf_bytes, "content_type": "application/pdf"}]
        )
        emails_sent += len(empfaenger)
        print(f"    [Filiale {standort}] OK!")

    return emails_sent


def send_bereich_reports(connector, heute, report_type, bereich_key, test_email=None):
    """
    Sendet TEK Bereichs-Reports (tek_nw, tek_gw, tek_teile, tek_werkstatt).
    Für Abteilungsleiter - nur ein spezifischer Bereich.
    """
    from api.pdf_generator import generate_tek_bereich_pdf

    BEREICH_NAMEN = {
        '1-NW': 'Neuwagen', '2-GW': 'Gebrauchtwagen',
        '3-Teile': 'Teile', '4-Lohn': 'Werkstatt', '5-Sonst': 'Sonstige'
    }

    if test_email:
        # Test-Modus: Nur an Test-Adresse
        subscribers = {None: [test_email]}
        print(f"  TEST-MODUS: Sende {report_type} an {test_email}")
    else:
        subscribers = get_subscribers_for_report(report_type)
    total = sum(len(v) for v in subscribers.values())

    if total == 0:
        print(f"  Keine Empfänger für {report_type}")
        return 0

    emails_sent = 0
    bereich_name = BEREICH_NAMEN.get(bereich_key, bereich_key)

    # Verarbeite nach Standort
    standorte = []
    if subscribers.get(None):
        standorte.append((None, subscribers[None]))
    for st in ['DEG', 'LAN']:
        if subscribers.get(st):
            standorte.append((st, subscribers[st]))

    for standort, empfaenger in standorte:
        standort_name = standort or 'Gesamt'
        print(f"\n    [{bereich_name} {standort_name}] Lade Daten...")
        data = get_tek_data(standort=standort)

        # Bereichs-Daten extrahieren
        bereich_data = None
        for b in data.get('bereiche', []):
            if b.get('bereich') == bereich_key:
                bereich_data = b
                break

        if not bereich_data:
            print(f"    [{bereich_name} {standort_name}] Keine Daten!")
            continue

        print(f"    [{bereich_name} {standort_name}] Generiere PDF...")
        pdf_bytes = generate_tek_bereich_pdf(data, bereich_key)

        betreff = f"TEK {bereich_name} | DB1: {format_euro(bereich_data['db1'])} | Marge: {bereich_data['marge']:.1f}%"

        body_html = build_bereich_email_html(data, bereich_key, bereich_data)

        suffix = f"_{standort}" if standort else ""
        dateiname = f"TEK_{bereich_name.replace(' ', '')}{suffix}_{heute.strftime('%Y%m%d')}.pdf"

        print(f"    [{bereich_name} {standort_name}] Sende an {len(empfaenger)} Empfänger...")
        connector.send_mail(
            sender_email=ABSENDER,
            to_emails=empfaenger,
            subject=betreff,
            body_html=body_html,
            attachments=[{"name": dateiname, "content": pdf_bytes, "content_type": "application/pdf"}]
        )
        emails_sent += len(empfaenger)
        print(f"    [{bereich_name} {standort_name}] OK!")

    return emails_sent


def build_gesamt_email_html(data):
    """Erstellt HTML-Body für Gesamt-Report"""
    gesamt = data['gesamt']
    status_color = "#28a745" if gesamt['breakeven_abstand'] >= 0 else "#dc3545"
    status_text = "POSITIV" if gesamt['breakeven_abstand'] >= 0 else "KRITISCH"
    status_prefix = "+" if gesamt['breakeven_abstand'] >= 0 else ""

    bereich_namen = {
        '1-NW': 'Neuwagen', '2-GW': 'Gebrauchtwagen',
        '3-Teile': 'Teile', '4-Lohn': 'Werkstatt', '5-Sonst': 'Sonstige'
    }

    bereiche_html = ""
    for i, b in enumerate(data['bereiche']):
        bg = '#f9f9f9' if i % 2 == 0 else '#ffffff'
        bereiche_html += f"""
        <tr style="background: {bg};">
            <td style="padding: 8px;">{bereich_namen.get(b['bereich'], b['bereich'])}</td>
            <td style="padding: 8px; text-align: right;">{format_euro(b['umsatz'])} EUR</td>
            <td style="padding: 8px; text-align: right;">{format_euro(b['db1'])} EUR</td>
            <td style="padding: 8px; text-align: center;">{b['marge']:.1f}%</td>
        </tr>"""

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 650px;">
        <h2 style="color: #0066cc; margin-bottom: 5px;">TEK - Tägliche Erfolgskontrolle</h2>
        <p style="color: #666; margin-top: 0;">{data['monat']} | Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr</p>

        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <tr style="background: #0066cc; color: white;">
                <th style="padding: 12px; text-align: center;">DB1 aktuell</th>
                <th style="padding: 12px; text-align: center;">Marge</th>
                <th style="padding: 12px; text-align: center;">Prognose</th>
                <th style="padding: 12px; text-align: center;">Breakeven</th>
            </tr>
            <tr style="background: #f5f5f5;">
                <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold;">{format_euro(gesamt['db1'])} EUR</td>
                <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold;">{gesamt['marge']:.1f}%</td>
                <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold;">{format_euro(gesamt['prognose'])} EUR</td>
                <td style="padding: 12px; text-align: center; font-size: 18px; font-weight: bold;">{format_euro(gesamt['breakeven'])} EUR</td>
            </tr>
        </table>

        <div style="background: {status_color}; color: white; padding: 15px; text-align: center; font-size: 16px; font-weight: bold; margin: 15px 0;">
            {status_prefix}{format_euro(gesamt['breakeven_abstand'])} EUR vs. Breakeven ({status_text})
        </div>

        <h3 style="color: #333; margin-top: 25px;">Bereiche</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr style="background: #333; color: white;">
                <th style="padding: 8px; text-align: left;">Bereich</th>
                <th style="padding: 8px; text-align: right;">Umsatz</th>
                <th style="padding: 8px; text-align: right;">DB1</th>
                <th style="padding: 8px; text-align: center;">Marge</th>
            </tr>
            {bereiche_html}
        </table>

        <p style="margin-top: 20px;">Details im PDF-Anhang.</p>

        <p style="color: #999; font-size: 11px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
            Automatisch generiert von DRIVE<br>
            <a href="http://drive.auto-greiner.de/controlling/tek" style="color: #0066cc;">In DRIVE öffnen</a>
        </p>
    </body>
    </html>
    """


def build_filiale_email_html(data):
    """Erstellt HTML-Body für Filiale-Report"""
    gesamt = data['gesamt']
    standort_name = data.get('standort_name', 'Filiale')

    bereich_namen = {
        '1-NW': 'Neuwagen', '2-GW': 'Gebrauchtwagen',
        '3-Teile': 'Teile', '4-Lohn': 'Werkstatt', '5-Sonst': 'Sonstige'
    }

    bereiche_html = ""
    for i, b in enumerate(data['bereiche']):
        bg = '#f9f9f9' if i % 2 == 0 else '#ffffff'
        bereiche_html += f"""
        <tr style="background: {bg};">
            <td style="padding: 8px;">{bereich_namen.get(b['bereich'], b['bereich'])}</td>
            <td style="padding: 8px; text-align: right;">{format_euro(b['db1'])} EUR</td>
            <td style="padding: 8px; text-align: center;">{b['marge']:.1f}%</td>
        </tr>"""

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px;">
        <h2 style="color: #0066cc; margin-bottom: 5px;">TEK Filiale {standort_name}</h2>
        <p style="color: #666; margin-top: 0;">{data['monat'].split(' - ')[-1]} | Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr</p>

        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <tr style="background: #0066cc; color: white;">
                <th style="padding: 12px; text-align: center;">DB1</th>
                <th style="padding: 12px; text-align: center;">Marge</th>
                <th style="padding: 12px; text-align: center;">Prognose</th>
            </tr>
            <tr style="background: #f5f5f5;">
                <td style="padding: 12px; text-align: center; font-size: 20px; font-weight: bold;">{format_euro(gesamt['db1'])} EUR</td>
                <td style="padding: 12px; text-align: center; font-size: 20px; font-weight: bold;">{gesamt['marge']:.1f}%</td>
                <td style="padding: 12px; text-align: center; font-size: 20px; font-weight: bold;">{format_euro(gesamt['prognose'])} EUR</td>
            </tr>
        </table>

        <h3 style="color: #333;">Bereiche</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr style="background: #333; color: white;">
                <th style="padding: 8px; text-align: left;">Bereich</th>
                <th style="padding: 8px; text-align: right;">DB1</th>
                <th style="padding: 8px; text-align: center;">Marge</th>
            </tr>
            {bereiche_html}
        </table>

        <p style="margin-top: 20px;">Details im PDF-Anhang.</p>

        <p style="color: #999; font-size: 11px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
            Automatisch generiert von DRIVE
        </p>
    </body>
    </html>
    """


def build_bereich_email_html(data, bereich_key, bereich_data):
    """Erstellt HTML-Body für Bereichs-Report"""
    BEREICH_NAMEN = {
        '1-NW': 'Neuwagen', '2-GW': 'Gebrauchtwagen',
        '3-Teile': 'Teile', '4-Lohn': 'Werkstatt', '5-Sonst': 'Sonstige'
    }
    BENCHMARKS = {
        '1-NW': 12, '2-GW': 10, '3-Teile': 32, '4-Lohn': 50, '5-Sonst': 10
    }

    bereich_name = BEREICH_NAMEN.get(bereich_key, bereich_key)
    ziel_marge = BENCHMARKS.get(bereich_key, 10)
    marge = bereich_data.get('marge', 0)

    if marge >= ziel_marge:
        status_color = "#28a745"
        status_text = "Ziel erreicht"
    elif marge >= ziel_marge * 0.7:
        status_color = "#ffc107"
        status_text = "Warnung"
    else:
        status_color = "#dc3545"
        status_text = "Unter Ziel"

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 550px;">
        <h2 style="color: #0066cc; margin-bottom: 5px;">TEK {bereich_name}</h2>
        <p style="color: #666; margin-top: 0;">{data['monat']} | Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr</p>

        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <tr style="background: #0066cc; color: white;">
                <th style="padding: 15px; text-align: center;">DB1</th>
                <th style="padding: 15px; text-align: center;">Marge</th>
                <th style="padding: 15px; text-align: center;">Status</th>
            </tr>
            <tr style="background: #f5f5f5;">
                <td style="padding: 15px; text-align: center; font-size: 24px; font-weight: bold;">{format_euro(bereich_data['db1'])} EUR</td>
                <td style="padding: 15px; text-align: center; font-size: 24px; font-weight: bold;">{marge:.1f}%</td>
                <td style="padding: 15px; text-align: center; font-size: 16px; font-weight: bold; color: {status_color};">{status_text}</td>
            </tr>
        </table>

        <table style="border-collapse: collapse; width: 100%; margin: 15px 0;">
            <tr>
                <td style="padding: 8px; background: #f0f0f0;">Umsatz:</td>
                <td style="padding: 8px; text-align: right;">{format_euro(bereich_data['umsatz'])} EUR</td>
            </tr>
            <tr>
                <td style="padding: 8px; background: #f0f0f0;">Einsatz:</td>
                <td style="padding: 8px; text-align: right;">{format_euro(bereich_data['einsatz'])} EUR</td>
            </tr>
            <tr>
                <td style="padding: 8px; background: #f0f0f0;">Ziel-Marge:</td>
                <td style="padding: 8px; text-align: right;">{ziel_marge}%</td>
            </tr>
        </table>

        <p style="margin-top: 20px;">Details im PDF-Anhang.</p>

        <p style="color: #999; font-size: 11px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
            Automatisch generiert von DRIVE
        </p>
    </body>
    </html>
    """


def main():
    import argparse
    parser = argparse.ArgumentParser(description='TEK Daily Reports versenden')
    parser.add_argument('--force', action='store_true', help='Ignoriere Wochenend-/Feiertags-Check')
    parser.add_argument('--test-email', type=str, help='Alle Reports an diese Test-Adresse senden')
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"TEK DAILY REPORTS - {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    if args.force:
        print(f"FORCE-MODUS - Ignoriere Wochenend/Feiertags-Check")
    if args.test_email:
        print(f"TEST-MODUS - Alle Reports an: {args.test_email}")
    print(f"{'='*60}")

    # TAG 136: Feiertagskalender-Check
    heute = date.today()
    if not args.force and is_holiday(heute):
        print(f"Heute ({heute.strftime('%d.%m.%Y')}) ist ein Feiertag - kein Report-Versand")
        print(f"{'='*60}\n")
        return 0

    # Wochenend-Check (zusätzliche Sicherheit)
    if not args.force and heute.weekday() >= 5:  # 5=Sa, 6=So
        print(f"Wochenende - kein Report-Versand")
        print(f"{'='*60}\n")
        return 0

    try:
        from api.graph_mail_connector import GraphMailConnector
        connector = GraphMailConnector()
        total_sent = 0
        test_email = args.test_email  # None wenn nicht im Test-Modus

        # 1. TEK Gesamt-Reports (tek_daily)
        print("\n[1] TEK GESAMT-REPORTS (tek_daily)")
        count = send_gesamt_reports(connector, heute, test_email)
        total_sent += count
        print(f"    -> {count} E-Mails")

        # 2. TEK Filiale-Reports (tek_filiale) - für Filialleiter wie Rolf
        print("\n[2] TEK FILIALE-REPORTS (tek_filiale)")
        count = send_filiale_reports(connector, heute, test_email)
        total_sent += count
        print(f"    -> {count} E-Mails")

        # 3. TEK Bereichs-Reports
        for report_type, config in TEK_REPORT_TYPES.items():
            if config['type'] == 'bereich':
                print(f"\n[3] TEK BEREICH: {config['name']} ({report_type})")
                count = send_bereich_reports(connector, heute, report_type, config['bereich_key'], test_email)
                total_sent += count
                print(f"    -> {count} E-Mails")

        print(f"\n{'='*60}")
        print(f"ERFOLG! Insgesamt {total_sent} E-Mails gesendet.")
        print(f"{'='*60}\n")
        return 0

    except Exception as e:
        print(f"\nFEHLER: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n{'='*60}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
