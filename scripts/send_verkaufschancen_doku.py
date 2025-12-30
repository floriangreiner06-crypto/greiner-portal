#!/usr/bin/env python3
"""
Sendet die Verkaufschancen-Dokumentation an Matthias und Florian.
Einmaliges Script für TAG 142.
"""

import sys
import os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')

from datetime import datetime

ABSENDER = "drive@auto-greiner.de"
EMPFAENGER = [
    "matthias.könig@auto-greiner.de",   # Matthias König (aus AD)
    "florian.greiner@auto-greiner.de"   # Florian Greiner (aus AD)
]

def build_email_html():
    return """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 700px; margin: 0 auto;">
        <h2 style="color: #0066cc;">Neues Feature: Penner-Verkaufschancen Dashboard</h2>

        <p>Hallo Matthias, hallo Florian,</p>

        <p>wir haben ein neues Feature im DRIVE Portal implementiert: Das <strong>Verkaufschancen-Dashboard</strong>
        hilft euch, Ladenhüter aus dem Lager zu verkaufen.</p>

        <h3 style="color: #333; margin-top: 25px;">Was ist neu?</h3>

        <table style="border-collapse: collapse; width: 100%; margin: 15px 0;">
            <tr style="background: #e9f5e9;">
                <td style="padding: 12px; border-left: 4px solid #28a745;">
                    <strong>Automatische Marktpreise</strong><br>
                    <span style="color: #666;">Nachts werden Preise von eBay und Daparto automatisch abgefragt</span>
                </td>
            </tr>
            <tr style="background: #fff8e6;">
                <td style="padding: 12px; border-left: 4px solid #ffc107;">
                    <strong>Verkaufsempfehlungen</strong><br>
                    <span style="color: #666;">Ampel-System zeigt, welche Teile die beste Verkaufschance haben</span>
                </td>
            </tr>
            <tr style="background: #e6f3ff;">
                <td style="padding: 12px; border-left: 4px solid #0066cc;">
                    <strong>Lagerkosten eingerechnet</strong><br>
                    <span style="color: #666;">10% p.a. Lagerkosten werden bei der Preisempfehlung berücksichtigt</span>
                </td>
            </tr>
            <tr style="background: #f5f5f5;">
                <td style="padding: 12px; border-left: 4px solid #666;">
                    <strong>Wöchentlicher Report</strong><br>
                    <span style="color: #666;">Jeden Montag um 7:00 Uhr bekommt ihr die Top 20 per E-Mail</span>
                </td>
            </tr>
        </table>

        <h3 style="color: #333; margin-top: 25px;">Wie funktioniert die Lagerkosten-Berechnung?</h3>

        <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <strong>Beispiel:</strong><br>
            - EK-Preis: 100 EUR<br>
            - Liegt seit: 2 Jahren<br>
            - Lagerkosten: 100 x 2 x 10% = <strong>20 EUR</strong><br>
            - Mindestpreis: 100 + 20 = <strong>120 EUR</strong><br>
            <br>
            Wenn Marktpreis bei 150 EUR liegt, empfehlen wir <strong>135 EUR</strong>.<br>
            Deine Marge nach Lagerkosten: 135 - 120 = <strong>15 EUR</strong>
        </div>

        <h3 style="color: #333; margin-top: 25px;">Zugang zum Dashboard</h3>

        <p style="margin: 20px 0;">
            <a href="http://drive.auto-greiner.de/werkstatt/renner-penner"
               style="background: #0066cc; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                Zum Verkaufschancen-Dashboard
            </a>
        </p>

        <p>Dann auf den Tab <strong>"Verkaufschancen"</strong> klicken.</p>

        <h3 style="color: #333; margin-top: 25px;">Anleitung</h3>

        <ol style="line-height: 1.8;">
            <li>Tab "Verkaufschancen" öffnen</li>
            <li>Nach "Grün" (Hohe Chance) filtern - diese Teile haben die beste Verkaufschance</li>
            <li>Auf "Marktcheck" klicken um direkt zu eBay zu springen</li>
            <li>Teil zum empfohlenen Preis einstellen</li>
        </ol>

        <p style="margin-top: 25px;">Bei Fragen einfach melden!</p>

        <p style="color: #999; font-size: 11px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
            Automatisch generiert von DRIVE - TAG 142<br>
            29.12.2025
        </p>
    </body>
    </html>
    """


def main():
    print(f"\n{'='*60}")
    print(f"VERKAUFSCHANCEN DOKUMENTATION - E-MAIL")
    print(f"{datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}")

    try:
        from api.graph_mail_connector import GraphMailConnector
        connector = GraphMailConnector()

        betreff = "Neues DRIVE Feature: Penner-Verkaufschancen mit automatischen Marktpreisen"
        html_body = build_email_html()

        print(f"\nSende an: {', '.join(EMPFAENGER)}")

        connector.send_mail(
            sender_email=ABSENDER,
            to_emails=EMPFAENGER,
            subject=betreff,
            body_html=html_body
        )

        print(f"\nERFOLG! E-Mail gesendet.")
        print(f"{'='*60}\n")
        return 0

    except Exception as e:
        print(f"\nFEHLER: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
