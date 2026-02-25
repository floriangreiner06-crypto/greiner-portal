#!/usr/bin/env python3
"""
AfA Bestand Abgleich – E-Mail-Report
====================================
Abgleich AfA-Bestand DRIVE vs. Locosoft:
- Neue Fahrzeuge in Locosoft (noch nicht in AfA) → bitte prüfen/importieren
- DRIVE aktiv, Locosoft verkauft → bitte Abgang in DRIVE prüfen

Empfänger: report_subscriptions (Report afa_bestand_report).
Schedule: 20:00 Mo–Fr (nach Locosoft-Update ca. 18–19 Uhr).

Workstream: Controlling | 2026-02-25
"""

import sys
import os

sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')

try:
    from dotenv import load_dotenv
    load_dotenv('/opt/greiner-portal/.env')
    load_dotenv('/opt/greiner-portal/config/.env', override=True)
except ImportError:
    pass

from datetime import datetime, date

ABSENDER = 'drive@auto-greiner.de'
DASHBOARD_URL = 'http://drive/controlling/afa'


def format_euro(val):
    """Betrag als Euro-String."""
    if val is None:
        return '–'
    try:
        return f"{float(val):,.2f} €".replace(',', ' ')
    except (TypeError, ValueError):
        return str(val)


def get_report_data():
    """Lädt Kandidaten (neu in Locosoft) und Abgangs-Kontrolle (DRIVE vs. Locosoft)."""
    from api.afa_api import get_locosoft_kandidaten_data, get_abgangs_kontrolle_data
    kandidaten = get_locosoft_kandidaten_data()
    abgang_data = get_abgangs_kontrolle_data()
    return {
        'kandidaten': kandidaten,
        'abgang_pruefen': abgang_data['abgang_pruefen'],
    }


def build_email_html(data, stichtag_str):
    """Erstellt HTML-Body für den AfA-Bestand-Report."""
    kandidaten = data.get('kandidaten') or []
    abgang_pruefen = data.get('abgang_pruefen') or []

    # Tabelle: Neue Fahrzeuge in Locosoft
    if kandidaten:
        rows_neu = []
        for k in kandidaten:
            rows_neu.append(f"""
                <tr>
                    <td style="padding: 6px 8px;">{k.get('kennzeichen') or '–'}</td>
                    <td style="padding: 6px 8px;">{k.get('vin') or '–'}</td>
                    <td style="padding: 6px 8px;">{k.get('fahrzeug_bezeichnung') or '–'}</td>
                    <td style="padding: 6px 8px;">{k.get('fahrzeugart') or '–'}</td>
                    <td style="padding: 6px 8px;">{k.get('anschaffungsdatum') or '–'}</td>
                    <td style="padding: 6px 8px; text-align: right;">{format_euro(k.get('anschaffungskosten_netto'))}</td>
                </tr>""")
        tabelle_neu = f"""
        <table style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <thead>
                <tr style="background: #0d6efd; color: white;">
                    <th style="padding: 8px; text-align: left;">Kennzeichen</th>
                    <th style="padding: 8px; text-align: left;">VIN</th>
                    <th style="padding: 8px; text-align: left;">Bezeichnung</th>
                    <th style="padding: 8px;">Art</th>
                    <th style="padding: 8px;">Anschaffung</th>
                    <th style="padding: 8px; text-align: right;">EK netto</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows_neu)}
            </tbody>
        </table>"""
        section_neu = f"""
        <h3 style="color: #0d6efd;">Neue Fahrzeuge in Locosoft (noch nicht in AfA DRIVE)</h3>
        <p>Diese Fahrzeuge stehen im Locosoft-Bestand (VFW/Mietwagen) und sind noch nicht im AfA-Modul erfasst. Bitte im AfA-Dashboard prüfen und ggf. importieren.</p>
        {tabelle_neu}
        """
    else:
        section_neu = """
        <h3 style="color: #0d6efd;">Neue Fahrzeuge in Locosoft</h3>
        <p>Keine neuen Fahrzeuge – alle relevanten VFW/Mietwagen aus Locosoft sind bereits in AfA erfasst.</p>
        """

    # Tabelle: Bitte Abgang in DRIVE prüfen
    if abgang_pruefen:
        rows_abgang = []
        for a in abgang_pruefen:
            rows_abgang.append(f"""
                <tr>
                    <td style="padding: 6px 8px;">{a.get('kennzeichen') or '–'}</td>
                    <td style="padding: 6px 8px;">{a.get('vin') or '–'}</td>
                    <td style="padding: 6px 8px;">{a.get('fahrzeug_bezeichnung') or '–'}</td>
                    <td style="padding: 6px 8px;">{a.get('locosoft_out_invoice_date') or '–'}</td>
                </tr>""")
        tabelle_abgang = f"""
        <table style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <thead>
                <tr style="background: #dc3545; color: white;">
                    <th style="padding: 8px; text-align: left;">Kennzeichen</th>
                    <th style="padding: 8px; text-align: left;">VIN</th>
                    <th style="padding: 8px; text-align: left;">Bezeichnung</th>
                    <th style="padding: 8px;">Locosoft Rechnungsdatum</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows_abgang)}
            </tbody>
        </table>"""
        section_abgang = f"""
        <h3 style="color: #dc3545;">Bitte Abgang in DRIVE prüfen</h3>
        <p>Diese Fahrzeuge sind in DRIVE noch als <strong>aktiv</strong>, in Locosoft aber bereits als verkauft gebucht (Rechnungsdatum gesetzt). Bitte Abgang im AfA-Modul erfassen.</p>
        {tabelle_abgang}
        """
    else:
        section_abgang = """
        <h3 style="color: #198754;">Bitte Abgang in DRIVE prüfen</h3>
        <p>Keine offenen Abgänge – alle in Locosoft als verkauft gebuchten Fahrzeuge sind in DRIVE abgeglichen.</p>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>AfA Bestand Abgleich</title></head>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2>AfA Bestand Abgleich DRIVE / Locosoft</h2>
    <p>Stichtag: <strong>{stichtag_str}</strong></p>
    <p>Locosoft-Daten werden täglich ca. 18–19 Uhr aktualisiert. Dieses Report basiert auf dem Abgleich AfA-Bestand DRIVE mit dem Locosoft-Bestand.</p>
    <hr style="margin: 20px 0;" />
    {section_neu}
    <hr style="margin: 20px 0;" />
    {section_abgang}
    <p style="margin-top: 24px;"><a href="{DASHBOARD_URL}" style="color: #0d6efd;">AfA-Dashboard im Portal öffnen</a></p>
    <p style="color: #6c757d; font-size: 12px;">DRIVE Portal – AfA Bestand Report</p>
</body>
</html>"""
    return html


def send_reports(connector, test_email=None):
    """Sendet den AfA-Bestand-Report an alle Abonnenten (oder test_email)."""
    from reports.registry import get_subscriber_emails

    if test_email:
        to_emails = [test_email.strip()]
    else:
        to_emails = get_subscriber_emails('afa_bestand_report')

    if not to_emails:
        return 0

    data = get_report_data()
    stichtag = date.today()
    stichtag_str = stichtag.strftime('%d.%m.%Y')
    body_html = build_email_html(data, stichtag_str)
    betreff = f"DRIVE AfA: Bestandsabgleich DRIVE/Locosoft – {stichtag_str}"

    connector.send_mail(
        sender_email=ABSENDER,
        to_emails=to_emails,
        subject=betreff,
        body_html=body_html,
    )
    return len(to_emails)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='AfA Bestand Abgleich Report versenden')
    parser.add_argument('--force', action='store_true', help='Ignoriere Zeitprüfung (z. B. für Test)')
    parser.add_argument('--test-email', type=str, help='Nur an diese E-Mail-Adresse senden')
    args = parser.parse_args()

    jetzt = datetime.now()
    stichtag_str = jetzt.strftime('%d.%m.%Y %H:%M')
    print(f"\n{'='*60}")
    print(f"AFA BESTAND REPORT – {stichtag_str}")
    if args.test_email:
        print(f"TEST-MODUS: Sende nur an {args.test_email}")
    print(f"{'='*60}")

    # Optional: erst nach 19:00 senden (nach Locosoft-Update)
    if not args.force and jetzt.hour < 19:
        print("Hinweis: Locosoft wird ca. 18–19 Uhr befüllt. Für aktuellen Abgleich nach 19:00 senden (oder --force).")

    try:
        from api.graph_mail_connector import GraphMailConnector
        connector = GraphMailConnector()
        count = send_reports(connector, test_email=args.test_email)
        if count > 0:
            print(f"Erfolg: {count} E-Mail(s) gesendet.")
        else:
            print("Keine Empfänger eingetragen. Bitte unter Report-Verwaltung Abonnenten für 'AfA Bestand Abgleich' anlegen.")
        print(f"{'='*60}\n")
        return 0
    except Exception as e:
        print(f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
