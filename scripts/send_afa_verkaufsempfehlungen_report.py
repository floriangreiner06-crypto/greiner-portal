#!/usr/bin/env python3
"""
AfA Verkaufsempfehlungen – E-Mail-Report (20 älteste Fahrzeuge)
===============================================================
VFW & Mietwagen: 20 älteste nach Standzeit mit Empfehlung (Liquidität, Auktion, Mindestpreis).
HTML-Body + PDF-Anhang. Empfänger: report_subscriptions (afa_verkaufsempfehlungen_report).
Schedule: 20:15 Mo–Fr (nach AfA Bestand 20:00).

Workstream: Controlling
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
DASHBOARD_URL = 'http://drive/controlling/afa/verkaufsempfehlungen'


def _fmt_eur(val):
    if val is None:
        return '–'
    try:
        return f"{float(val):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return '–'


def _empfehlung_css_class(empfehlung):
    """CSS-Klasse für Empfehlungstext (inline style für E-Mail)."""
    if not empfehlung:
        return ''
    e = (empfehlung or '').lower()
    if 'zwang' in e or 'zinsenrückholung' in e:
        return 'color: #b02a37; font-weight: bold;'
    if 'aktiv vermarkten' in e or 'auktion' in e:
        return 'color: #198754;'
    if 'mindestpreis' in e or 'jetzt verkaufen' in e:
        return 'color: #0d6efd;'
    if 'prüfen' in e:
        return 'color: #fd7e14;'
    return ''


def get_report_data():
    """20 älteste Fahrzeuge (Standzeit absteigend) aus AfA API."""
    from api.afa_api import _get_verkaufsempfehlungen_liste
    liste = _get_verkaufsempfehlungen_liste()
    sorted_list = sorted(
        liste,
        key=lambda f: (f.get('standzeit_tage') is None, -(f.get('standzeit_tage') or 0))
    )
    return sorted_list[:20]


def build_email_html(top20, stichtag_str):
    """HTML-Body für E-Mail (Tabelle 20 älteste + Liquiditäts-Hinweis)."""
    rows = []
    for i, f in enumerate(top20, 1):
        bezeichnung = (f.get('fahrzeug_bezeichnung') or '–')[:50]
        tage = f.get('standzeit_tage')
        tage_str = str(tage) if tage is not None else '–'
        buch = _fmt_eur(f.get('buchwert'))
        empfehlung = (f.get('empfehlung') or '–')
        style = _empfehlung_css_class(empfehlung)
        cell_style = f"border: 1px solid #dee2e6; padding: 8px 10px; {style}" if style else "border: 1px solid #dee2e6; padding: 8px 10px;"
        rows.append(f"""
            <tr>
                <td style="border: 1px solid #dee2e6; padding: 8px 10px;">{i}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px 10px;">{bezeichnung}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px 10px; text-align: right;">{tage_str}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px 10px; text-align: right;">{buch}</td>
                <td style="{cell_style}">{empfehlung}</td>
            </tr>""")

    tabelle = f"""
        <table style="border-collapse: collapse; width: 100%; font-size: 13px;">
            <thead>
                <tr>
                    <th style="border: 1px solid #dee2e6; padding: 8px 10px; background: #343a40; color: #fff;">#</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px 10px; background: #343a40; color: #fff;">Bezeichnung</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px 10px; background: #343a40; color: #fff; text-align: right;">Tage</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px 10px; background: #343a40; color: #fff; text-align: right;">Buchwert (€)</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px 10px; background: #343a40; color: #fff;">Empfehlung</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>"""

    html = f"""
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Verkaufsempfehlungen AfA</title></head>
<body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.5; color: #333; max-width: 720px; margin: 0 auto; padding: 16px;">
    <h1 style="margin: 0; font-size: 20px; color: #0d6efd;">Greiner DRIVE — Verkaufsempfehlungen</h1>
    <p style="margin: 4px 0 0 0; font-size: 13px; color: #6c757d;">VFW & Mietwagen · 20 älteste Fahrzeuge nach Standzeit</p>
    <p style="margin: 16px 0 0 0;"><strong>Rascher Umschlag und gezielte Vermarktung verbessern Ihren Liquiditätszugang und den Cashflow.</strong> Jedes verkaufte Fahrzeug setzt Buchwert frei, reduziert Zinslast und schafft Spielraum für Neubeschaffung.</p>
    <p style="margin: 12px 0 16px 0;">Die <strong>20 ältesten Fahrzeuge</strong> (längste Standzeit) mit Empfehlung. Bitte priorisieren Sie die rot markierten Positionen — hier ist die Zinsenrückholung sonst gefährdet.</p>
    {tabelle}
    <p style="margin-top: 20px;"><a href="{DASHBOARD_URL}" style="color: #0d6efd;">Verkaufsempfehlungen im Portal öffnen</a></p>
    <p style="color: #6c757d; font-size: 12px;">Stand: {stichtag_str} · DRIVE Portal – AfA Verkaufsempfehlungen</p>
</body>
</html>"""
    return html


def send_reports(connector, test_email=None):
    """Sendet den Verkaufsempfehlungen-Report an alle Abonnenten (oder test_email)."""
    from reports.registry import get_subscriber_emails
    from api.afa_verkaufsempfehlungen_pdf import generate_verkaufsempfehlungen_20_pdf

    if test_email:
        to_emails = [test_email.strip()]
    else:
        to_emails = get_subscriber_emails('afa_verkaufsempfehlungen_report')

    if not to_emails:
        return 0

    top20 = get_report_data()
    stichtag = date.today()
    stichtag_str = stichtag.strftime('%d.%m.%Y')
    body_html = build_email_html(top20, stichtag_str)
    betreff = f"DRIVE Verkaufsempfehlungen — 20 älteste Fahrzeuge & Liquidität · {stichtag_str}"

    pdf_bytes = generate_verkaufsempfehlungen_20_pdf()
    attachments = []
    if pdf_bytes:
        attachments.append({
            'name': f"DRIVE_Verkaufsempfehlungen_20_aelteste_{stichtag.strftime('%Y-%m-%d')}.pdf",
            'content': pdf_bytes,
        })

    connector.send_mail(
        sender_email=ABSENDER,
        to_emails=to_emails,
        subject=betreff,
        body_html=body_html,
        attachments=attachments if attachments else None,
    )
    return len(to_emails)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='AfA Verkaufsempfehlungen Report (20 älteste) versenden')
    parser.add_argument('--force', action='store_true', help='Ignoriere Zeitprüfung')
    parser.add_argument('--test-email', type=str, help='Nur an diese E-Mail senden')
    args = parser.parse_args()

    jetzt = datetime.now()
    stichtag_str = jetzt.strftime('%d.%m.%Y %H:%M')
    print(f"\n{'='*60}")
    print(f"AFA VERKAUFSEMPFEHLUNGEN REPORT – {stichtag_str}")
    if args.test_email:
        print(f"TEST: Nur an {args.test_email}")
    print(f"{'='*60}")

    try:
        from api.graph_mail_connector import GraphMailConnector
        connector = GraphMailConnector()
        count = send_reports(connector, test_email=args.test_email)
        if count > 0:
            print(f"Erfolg: {count} E-Mail(s) gesendet.")
        else:
            print("Keine Empfänger. Bitte unter Admin → Einstellungen → E-Mail Reports Abonnenten anlegen.")
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
