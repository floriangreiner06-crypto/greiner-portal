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


# SSOT: DB-Verbindung
from api.db_connection import get_db


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

        # Betreff mit Status (Abstand = Prognose - Breakeven, wie im PDF)
        gesamt = data['gesamt']
        abstand = (gesamt.get('prognose', gesamt.get('db1', 0)) - gesamt.get('breakeven', 0))
        status = "+" if abstand >= 0 else ""
        betreff = f"TEK {data['monat']} | DB1: {format_euro(gesamt['db1'])} | {status}{format_euro(abstand)} vs BE"

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
    # Empfänger mit Standort DEG/LAN + "Alle Standorte" (None) bekommen den jeweiligen Report
    for standort in ['DEG', 'LAN']:
        empfaenger = list(subscribers.get(standort, []))
        alle = subscribers.get(None) or []
        for e in alle:
            if e not in empfaenger:
                empfaenger.append(e)
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


def send_verkauf_reports(connector, heute, test_email=None):
    """
    Sendet TEK Verkauf-Reports (NW+GW kombiniert) - TAG 215
    Für Verkaufsleitung - alle Standorte.
    """
    from api.pdf_generator import generate_tek_verkauf_pdf
    from api.standort_utils import STANDORT_NAMEN

    if test_email:
        subscribers = {None: [test_email], 'DEG': [test_email], 'LAN': [test_email]}
        print(f"  TEST-MODUS: Sende Verkauf-Reports an {test_email}")
    else:
        subscribers = get_subscribers_for_report('tek_verkauf')
    
    total = sum(len(v) for v in subscribers.values())
    if total == 0:
        print("  Keine Empfänger für tek_verkauf")
        return 0

    emails_sent = 0

    # Verarbeite nach Standort
    standorte = []
    if subscribers.get(None):
        standorte.append((None, subscribers[None], 'Gesamt'))
    if subscribers.get('DEG'):
        standorte.append(('DEG', subscribers['DEG'], 'Deggendorf'))
    if subscribers.get('LAN'):
        standorte.append(('LAN', subscribers['LAN'], 'Landau'))

    for standort, empfaenger, standort_name in standorte:
        print(f"\n    [Verkauf {standort_name}] Lade Daten...")
        data = get_tek_data(standort=standort)

        print(f"    [Verkauf {standort_name}] Generiere PDF...")
        pdf_bytes = generate_tek_verkauf_pdf(data, standort_name)

        # Betreff
        nw = next((b for b in data.get('bereiche', []) if b.get('bereich') == '1-NW'), None)
        gw = next((b for b in data.get('bereiche', []) if b.get('bereich') == '2-GW'), None)
        verkauf_db1 = (nw.get('db1', 0) if nw else 0) + (gw.get('db1', 0) if gw else 0)
        betreff = f"TEK Verkauf{standort_name if standort_name != 'Gesamt' else ''} | DB: {format_euro(verkauf_db1)} | {data.get('monat', 'Aktueller Monat')}"

        body_html = build_verkauf_email_html(data, standort_name)

        suffix = f"_{standort}" if standort else ""
        dateiname = f"TEK_Verkauf{suffix}_{heute.strftime('%Y%m%d')}.pdf"

        print(f"    [Verkauf {standort_name}] Sende an {len(empfaenger)} Empfänger...")
        connector.send_mail(
            sender_email=ABSENDER,
            to_emails=empfaenger,
            subject=betreff,
            body_html=body_html,
            attachments=[{"name": dateiname, "content": pdf_bytes, "content_type": "application/pdf"}]
        )
        emails_sent += len(empfaenger)
        print(f"    [Verkauf {standort_name}] OK!")

    return emails_sent


def send_service_reports(connector, heute, test_email=None):
    """
    Sendet TEK Service-Reports (Teile+Werkstatt kombiniert) - TAG 215
    Für Service-Leitung - alle Standorte.
    """
    from api.pdf_generator import generate_tek_service_pdf

    if test_email:
        subscribers = {None: [test_email], 'DEG': [test_email], 'LAN': [test_email]}
        print(f"  TEST-MODUS: Sende Service-Reports an {test_email}")
    else:
        subscribers = get_subscribers_for_report('tek_service')
    
    total = sum(len(v) for v in subscribers.values())
    if total == 0:
        print("  Keine Empfänger für tek_service")
        return 0

    emails_sent = 0

    # Verarbeite nach Standort
    standorte = []
    if subscribers.get(None):
        standorte.append((None, subscribers[None], 'Gesamt'))
    if subscribers.get('DEG'):
        standorte.append(('DEG', subscribers['DEG'], 'Deggendorf'))
    if subscribers.get('LAN'):
        standorte.append(('LAN', subscribers['LAN'], 'Landau'))

    for standort, empfaenger, standort_name in standorte:
        print(f"\n    [Service {standort_name}] Lade Daten...")
        data = get_tek_data(standort=standort)

        print(f"    [Service {standort_name}] Generiere PDF...")
        pdf_bytes = generate_tek_service_pdf(data, standort_name)

        # Betreff
        teile = next((b for b in data.get('bereiche', []) if b.get('bereich') == '3-Teile'), None)
        werkstatt = next((b for b in data.get('bereiche', []) if b.get('bereich') == '4-Lohn'), None)
        service_db1 = (teile.get('db1', 0) if teile else 0) + (werkstatt.get('db1', 0) if werkstatt else 0)
        betreff = f"TEK Service{standort_name if standort_name != 'Gesamt' else ''} | DB: {format_euro(service_db1)} | {data.get('monat', 'Aktueller Monat')}"

        body_html = build_service_email_html(data, standort_name)

        suffix = f"_{standort}" if standort else ""
        dateiname = f"TEK_Service{suffix}_{heute.strftime('%Y%m%d')}.pdf"

        print(f"    [Service {standort_name}] Sende an {len(empfaenger)} Empfänger...")
        connector.send_mail(
            sender_email=ABSENDER,
            to_emails=empfaenger,
            subject=betreff,
            body_html=body_html,
            attachments=[{"name": dateiname, "content": pdf_bytes, "content_type": "application/pdf"}]
        )
        emails_sent += len(empfaenger)
        print(f"    [Service {standort_name}] OK!")

    return emails_sent


def build_gesamt_email_html(data):
    """Erstellt HTML-Body für Gesamt-Report.
    Breakeven-Abstand wie im PDF: Prognose minus Breakeven (nicht DB1 aktuell), damit E-Mail und Anhang übereinstimmen.
    """
    gesamt = data['gesamt']
    # Wie im PDF: Abstand = Prognose - Breakeven (nicht DB1 aktuell - Breakeven aus der API)
    prognose = gesamt.get('prognose', gesamt.get('db1', 0))
    breakeven = gesamt.get('breakeven', 0)
    abstand_prognose = prognose - breakeven
    status_color = "#28a745" if abstand_prognose >= 0 else "#dc3545"
    status_text = "ÜBER Breakeven (Prognose)" if abstand_prognose >= 0 else "UNTER Breakeven (Prognose)"
    status_prefix = "+" if abstand_prognose >= 0 else ""

    bereich_namen = {
        '1-NW': 'Neuwagen', '2-GW': 'Gebrauchtwagen',
        '3-Teile': 'Teile', '4-Lohn': 'Werkstatt', '5-Sonst': 'Sonstige'
    }

    bereiche_html = ""
    for i, b in enumerate(data['bereiche']):
        bg = '#f9f9f9' if i % 2 == 0 else '#ffffff'
        # Stück nur für NW/GW, sonst "-"
        stueck_display = str(b.get('stueck', 0)) if b.get('bereich') in ('1-NW', '2-GW') else "–"
        bereiche_html += f"""
        <tr style="background: {bg};">
            <td style="padding: 8px;">{bereich_namen.get(b['bereich'], b['bereich'])}</td>
            <td style="padding: 8px; text-align: right;">{stueck_display}</td>
            <td style="padding: 8px; text-align: right;">{format_euro(b['umsatz'])} EUR</td>
            <td style="padding: 8px; text-align: right;">{format_euro(b['einsatz'])} EUR</td>
            <td style="padding: 8px; text-align: right;">{format_euro(b['db1'])} EUR</td>
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
            {status_prefix}{format_euro(abstand_prognose)} EUR {status_text}
        </div>

        <h3 style="color: #333; margin-top: 25px;">Bereiche</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr style="background: #333; color: white;">
                <th style="padding: 8px; text-align: left;">Bereich</th>
                <th style="padding: 8px; text-align: right;">Stück</th>
                <th style="padding: 8px; text-align: right;">Erlös</th>
                <th style="padding: 8px; text-align: right;">Einsatz</th>
                <th style="padding: 8px; text-align: right;">DB</th>
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
                <td style="padding: 8px; background: #f0f0f0;">Erlös:</td>
                <td style="padding: 8px; text-align: right;">{format_euro(bereich_data['umsatz'])} EUR</td>
            </tr>
            <tr>
                <td style="padding: 8px; background: #f0f0f0;">Einsatz:</td>
                <td style="padding: 8px; text-align: right;">{format_euro(bereich_data['einsatz'])} EUR</td>
            </tr>
            <tr>
                <td style="padding: 8px; background: #f0f0f0;">DB:</td>
                <td style="padding: 8px; text-align: right;">{format_euro(bereich_data['db1'])} EUR</td>
            </tr>
        </table>

        <p style="margin-top: 20px;">Details im PDF-Anhang.</p>

        <p style="color: #999; font-size: 11px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
            Automatisch generiert von DRIVE
        </p>
    </body>
    </html>
    """


def build_verkauf_email_html(data, standort_name: str = None):
    """Erstellt HTML-Body für Verkauf-Report (NW+GW) – detailliert wie TEK Gesamt (Kernkennzahlen + Bereiche im Detail)."""
    nw = next((b for b in data.get('bereiche', []) if b.get('bereich') == '1-NW'), None)
    gw = next((b for b in data.get('bereiche', []) if b.get('bereich') == '2-GW'), None)

    verkauf_umsatz = (nw.get('umsatz', 0) if nw else 0) + (gw.get('umsatz', 0) if gw else 0)
    verkauf_einsatz = (nw.get('einsatz', 0) if nw else 0) + (gw.get('einsatz', 0) if gw else 0)
    verkauf_db1 = verkauf_umsatz - verkauf_einsatz
    verkauf_marge = (verkauf_db1 / verkauf_umsatz * 100) if verkauf_umsatz > 0 else 0
    verkauf_stueck = (nw.get('stueck', 0) if nw else 0) + (gw.get('stueck', 0) if gw else 0)
    verkauf_db1_stk = (verkauf_db1 / verkauf_stueck) if verkauf_stueck > 0 else 0
    verkauf_heute_umsatz = (nw.get('heute_umsatz', 0) if nw else 0) + (gw.get('heute_umsatz', 0) if gw else 0)
    verkauf_heute_db1 = (nw.get('heute_db1', 0) if nw else 0) + (gw.get('heute_db1', 0) if gw else 0)

    # Kernkennzahlen-Tabelle (wie im PDF)
    kpi_rows = f"""
            <tr><td style="padding: 8px; background: #f0f0f0;">Erlös (Monat):</td><td style="padding: 8px; text-align: right;">{format_euro(verkauf_umsatz)} EUR</td></tr>
            <tr><td style="padding: 8px; background: #f9f9f9;">Einsatz (Monat):</td><td style="padding: 8px; text-align: right;">{format_euro(verkauf_einsatz)} EUR</td></tr>
            <tr><td style="padding: 8px; background: #f0f0f0;">DB1 (Monat):</td><td style="padding: 8px; text-align: right;">{format_euro(verkauf_db1)} EUR</td></tr>
            <tr><td style="padding: 8px; background: #f9f9f9;">Marge:</td><td style="padding: 8px; text-align: right;">{verkauf_marge:.1f}%</td></tr>
            <tr><td style="padding: 8px; background: #f0f0f0;">Stück (Monat):</td><td style="padding: 8px; text-align: right;">{verkauf_stueck}</td></tr>
            <tr><td style="padding: 8px; background: #f9f9f9;">DB1/Stück:</td><td style="padding: 8px; text-align: right;">{format_euro(verkauf_db1_stk)} EUR</td></tr>
            <tr><td style="padding: 8px; background: #f0f0f0;">Erlös (Heute):</td><td style="padding: 8px; text-align: right;">{format_euro(verkauf_heute_umsatz)} EUR</td></tr>
            <tr><td style="padding: 8px; background: #f9f9f9;">DB1 (Heute):</td><td style="padding: 8px; text-align: right;">{format_euro(verkauf_heute_db1)} EUR</td></tr>"""

    # Bereiche im Detail: Neuwagen, Gebrauchtwagen, GESAMT
    def detail_row(name, b):
        if b is None:
            return ""
        u, e, d = b.get('umsatz', 0), b.get('einsatz', 0), b.get('db1', 0)
        m = (d / u * 100) if u else 0
        stk = b.get('stueck', 0)
        db1_stk = b.get('db1_pro_stueck', 0) or (d / stk if stk else 0)
        return f"""
        <tr style="background: #f9f9f9;">
            <td style="padding: 8px;">{name}</td>
            <td style="padding: 8px; text-align: right;">{stk}</td>
            <td style="padding: 8px; text-align: right;">{format_euro(u)} EUR</td>
            <td style="padding: 8px; text-align: right;">{format_euro(e)} EUR</td>
            <td style="padding: 8px; text-align: right;">{format_euro(d)} EUR</td>
            <td style="padding: 8px; text-align: right;">{m:.1f}%</td>
            <td style="padding: 8px; text-align: right;">{format_euro(db1_stk)} EUR</td>
        </tr>"""
    nw_row = detail_row('Neuwagen', nw)
    gw_row = detail_row('Gebrauchtwagen', gw)
    gesamt_row = f"""
        <tr style="background: #333; color: white; font-weight: bold;">
            <td style="padding: 8px;">GESAMT</td>
            <td style="padding: 8px; text-align: right;">{verkauf_stueck}</td>
            <td style="padding: 8px; text-align: right;">{format_euro(verkauf_umsatz)} EUR</td>
            <td style="padding: 8px; text-align: right;">{format_euro(verkauf_einsatz)} EUR</td>
            <td style="padding: 8px; text-align: right;">{format_euro(verkauf_db1)} EUR</td>
            <td style="padding: 8px; text-align: right;">{verkauf_marge:.1f}%</td>
            <td style="padding: 8px; text-align: right;">{format_euro(verkauf_db1_stk)} EUR</td>
        </tr>"""

    standort_suffix = f" {standort_name}" if standort_name and standort_name != 'Gesamt' else ""

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 650px;">
        <h2 style="color: #0066cc; margin-bottom: 5px;">TEK Verkauf{standort_suffix}</h2>
        <p style="color: #666; margin-top: 0;">{data.get('monat', 'Aktueller Monat')} | Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr</p>

        <h3 style="color: #333; margin-top: 20px;">Kernkennzahlen</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            {kpi_rows}
        </table>

        <h3 style="color: #333; margin-top: 25px;">Bereiche im Detail</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr style="background: #333; color: white;">
                <th style="padding: 8px; text-align: left;">Bereich</th>
                <th style="padding: 8px; text-align: right;">Stück</th>
                <th style="padding: 8px; text-align: right;">Erlös</th>
                <th style="padding: 8px; text-align: right;">Einsatz</th>
                <th style="padding: 8px; text-align: right;">DB1</th>
                <th style="padding: 8px; text-align: right;">Marge</th>
                <th style="padding: 8px; text-align: right;">DB1/Stk</th>
            </tr>
            {nw_row}{gw_row}{gesamt_row}
        </table>

        <p style="margin-top: 20px;">Weitere Details im PDF-Anhang.</p>

        <p style="color: #999; font-size: 11px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
            Automatisch generiert von DRIVE<br>
            <a href="http://drive.auto-greiner.de/controlling/tek" style="color: #0066cc;">In DRIVE öffnen</a>
        </p>
    </body>
    </html>
    """


def build_service_email_html(data, standort_name: str = None):
    """Erstellt HTML-Body für Service-Report (Teile+Werkstatt) - TAG 215"""
    teile = next((b for b in data.get('bereiche', []) if b.get('bereich') == '3-Teile'), None)
    werkstatt = next((b for b in data.get('bereiche', []) if b.get('bereich') == '4-Lohn'), None)
    
    service_umsatz = (teile.get('umsatz', 0) if teile else 0) + (werkstatt.get('umsatz', 0) if werkstatt else 0)
    service_einsatz = (teile.get('einsatz', 0) if teile else 0) + (werkstatt.get('einsatz', 0) if werkstatt else 0)
    service_db1 = service_umsatz - service_einsatz
    service_marge = (service_db1 / service_umsatz * 100) if service_umsatz > 0 else 0
    
    standort_suffix = f" {standort_name}" if standort_name and standort_name != 'Gesamt' else ""
    
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px;">
        <h2 style="color: #0066cc; margin-bottom: 5px;">TEK Service{standort_suffix}</h2>
        <p style="color: #666; margin-top: 0;">{data.get('monat', 'Aktueller Monat')} | Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr</p>

        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <tr style="background: #0066cc; color: white;">
                <th style="padding: 12px; text-align: right;">Erlös</th>
                <th style="padding: 12px; text-align: right;">Einsatz</th>
                <th style="padding: 12px; text-align: right;">DB</th>
            </tr>
            <tr style="background: #f5f5f5;">
                <td style="padding: 12px; text-align: right; font-size: 18px; font-weight: bold;">{format_euro(service_umsatz)} EUR</td>
                <td style="padding: 12px; text-align: right; font-size: 18px; font-weight: bold;">{format_euro(service_einsatz)} EUR</td>
                <td style="padding: 12px; text-align: right; font-size: 18px; font-weight: bold;">{format_euro(service_db1)} EUR</td>
            </tr>
        </table>

        <table style="border-collapse: collapse; width: 100%; margin: 15px 0;">
            <tr>
                <td style="padding: 8px; background: #f0f0f0;">Marge:</td>
                <td style="padding: 8px; text-align: right;">{service_marge:.1f}%</td>
            </tr>
        </table>

        <p style="margin-top: 20px;">Details im PDF-Anhang.</p>

        <p style="color: #999; font-size: 11px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
            Automatisch generiert von DRIVE
        </p>
    </body>
    </html>
    """


def check_locosoft_mirror_completed():
    """
    Prüft ob Locosoft Mirror heute erfolgreich abgeschlossen wurde.
    TAG 181: Sicherheitsprüfung für TEK-Versand
    
    Returns: True wenn Mirror heute erfolgreich war, False sonst
    """
    try:
        import redis
        from datetime import datetime, timezone
        import json
        
        # Redis Client für Result Backend (DB 1)
        redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=False)
        
        # Suche nach Locosoft Mirror Task-Ergebnissen
        pattern = 'celery-task-meta-*'
        keys = redis_client.keys(pattern)
        
        heute = date.today()
        heute_str = heute.strftime('%Y-%m-%d')
        
        # Durchsuche die letzten Keys
        for key in keys[:500]:  # Maximal 500 Keys prüfen
            try:
                meta_data = redis_client.get(key)
                if not meta_data:
                    continue
                
                if isinstance(meta_data, bytes):
                    meta_data = meta_data.decode('utf-8')
                
                data = json.loads(meta_data)
                
                # Prüfe ob es der Locosoft Mirror Task ist
                task_name = data.get('task_name', '')
                if 'locosoft_mirror' not in task_name:
                    continue
                
                # Prüfe Status
                status = data.get('status', '')
                if status != 'SUCCESS':
                    continue
                
                # Prüfe Datum
                date_done = data.get('date_done')
                if date_done:
                    # Parse ISO-Format
                    if 'T' in date_done:
                        task_date = date_done.split('T')[0]
                        if task_date == heute_str:
                            return True
            except (json.JSONDecodeError, UnicodeDecodeError, KeyError, ValueError):
                continue
        
        return False
    except Exception as e:
        print(f"⚠️  Warnung: Konnte Locosoft Mirror-Status nicht prüfen: {e}")
        return False  # Im Fehlerfall erlauben (nicht blockieren)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='TEK Daily Reports versenden')
    parser.add_argument('--force', action='store_true', help='Ignoriere Wochenend-/Feiertags-Check und Zeitprüfung')
    parser.add_argument('--test-email', type=str, help='Alle Reports an diese Test-Adresse senden')
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"TEK DAILY REPORTS - {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    if args.force:
        print(f"FORCE-MODUS - Ignoriere Wochenend/Feiertags-Check und Zeitprüfung")
    if args.test_email:
        print(f"TEST-MODUS - Alle Reports an: {args.test_email}")
    print(f"{'='*60}")

    # TAG 181: Zeitprüfung - TEK sollte erst nach 19:00 Uhr gesendet werden
    # (nach Locosoft PostgreSQL Update und Locosoft Mirror)
    jetzt = datetime.now()
    if not args.force and jetzt.hour < 19:
        print(f"⚠️  WARNUNG: Es ist {jetzt.strftime('%H:%M')} Uhr - TEK sollte erst nach 19:00 Uhr gesendet werden")
        print(f"    (nach Locosoft PostgreSQL Update und Locosoft Mirror)")
        print(f"    Verwende --force um trotzdem zu senden")
        print(f"{'='*60}\n")
        return 1

    # TAG 181: Prüfe ob Locosoft Mirror heute erfolgreich war
    # TAG 186: Bei Prüfungsfehler trotzdem senden (mit Warnung), nur bei explizitem Fehler blockieren
    if not args.force:
        try:
            mirror_completed = check_locosoft_mirror_completed()
            if not mirror_completed:
                print(f"⚠️  WARNUNG: Locosoft Mirror wurde heute noch nicht erfolgreich abgeschlossen")
                print(f"    TEK-Daten könnten veraltet sein!")
                print(f"    Sende trotzdem (Prüfung könnte fehlgeschlagen sein)")
                print(f"    Verwende --force um diese Warnung zu unterdrücken")
            else:
                print(f"✅ Locosoft Mirror heute erfolgreich abgeschlossen - Daten sind aktuell")
        except Exception as e:
            print(f"⚠️  WARNUNG: Konnte Locosoft Mirror-Status nicht prüfen: {e}")
            print(f"    Sende trotzdem (Prüfung fehlgeschlagen)")

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

        # 4. TEK Verkauf-Reports (NW+GW kombiniert) - TAG 215
        print("\n[4] TEK VERKAUF-REPORTS (NW+GW)")
        count = send_verkauf_reports(connector, heute, test_email)
        total_sent += count
        print(f"    -> {count} E-Mails")

        # 5. TEK Service-Reports (Teile+Werkstatt kombiniert) - TAG 215
        print("\n[5] TEK SERVICE-REPORTS (Teile+Werkstatt)")
        count = send_service_reports(connector, heute, test_email)
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
