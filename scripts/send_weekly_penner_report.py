#!/usr/bin/env python3
"""
Penner Verkaufschancen - Wöchentlicher E-Mail Report

Sendet jeden Montag um 7:00 Uhr die Top 20 Verkaufschancen an Matthias.
Basis: Penner-Teile mit gecachten Marktpreisen und hoher Verkaufschance.

Schedule (Celery Beat):
0 7 * * 1 (Montags um 7:00 Uhr)
Task: celery_app.tasks.email_penner_weekly

Version: 1.0 (TAG 142)
"""

import sys
import os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')

from datetime import datetime, date
from decimal import Decimal

# ============================================================================
# KONFIGURATION
# ============================================================================

ABSENDER = "drive@auto-greiner.de"
REPORT_TYPE = "penner_weekly"  # Für Reports Registry

# Standard-Empfänger (falls keine in Registry)
# WICHTIG: E-Mail-Adressen aus Active Directory (mit Umlauten!)
DEFAULT_EMPFAENGER = [
    "matthias.könig@auto-greiner.de",   # Matthias König (Serviceleiter/T&Z) - aus AD
    "florian.greiner@auto-greiner.de"   # Florian Greiner (GF) - aus AD
]


def get_db():
    """Datenbank-Verbindung via db_connection"""
    from api.db_connection import get_db as get_portal_db
    return get_portal_db()


def get_empfaenger():
    """
    Holt Empfänger aus Reports Registry oder nutzt Standard.
    """
    try:
        from reports.registry import get_subscribers
        subs = get_subscribers(REPORT_TYPE)
        if subs:
            return [s.get('email') for s in subs if s.get('email')]
    except Exception as e:
        print(f"  Info: Reports Registry nicht verfügbar ({e}), nutze Standard-Empfänger")

    return DEFAULT_EMPFAENGER


def get_top_verkaufschancen(limit=20):
    """
    Holt Top N Verkaufschancen aus dem Marktpreis-Cache.

    Returns:
        list: Teile mit Marktdaten, sortiert nach Verkaufschance
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                part_number,
                beschreibung,
                bestand,
                ek_preis,
                vk_preis,
                lagerwert,
                tage_seit_abgang,
                preis_min,
                preis_max,
                preis_avg,
                empf_verkaufspreis,
                empf_plattform,
                verkaufschance,
                anzahl_angebote,
                anzahl_quellen,
                abgefragt_am
            FROM penner_marktpreise
            WHERE verkaufschance IN ('hoch', 'mittel')
              AND empf_verkaufspreis > 0
            ORDER BY
                CASE verkaufschance
                    WHEN 'hoch' THEN 1
                    WHEN 'mittel' THEN 2
                    ELSE 3
                END,
                lagerwert DESC
            LIMIT %s
        """, (limit,))

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        teile = []
        for row in rows:
            teil = dict(zip(columns, row))
            # Decimal zu float konvertieren
            for key in ['ek_preis', 'vk_preis', 'lagerwert', 'preis_min', 'preis_max',
                       'preis_avg', 'empf_verkaufspreis']:
                if teil.get(key) is not None:
                    teil[key] = float(teil[key])
            teile.append(teil)

        return teile

    except Exception as e:
        print(f"  Fehler beim Laden der Verkaufschancen: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_statistik():
    """
    Holt Statistiken aus dem Marktpreis-Cache.
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                COUNT(*) as gesamt,
                SUM(CASE WHEN verkaufschance = 'hoch' THEN 1 ELSE 0 END) as hoch,
                SUM(CASE WHEN verkaufschance = 'mittel' THEN 1 ELSE 0 END) as mittel,
                SUM(CASE WHEN verkaufschance = 'gering' THEN 1 ELSE 0 END) as gering,
                SUM(CASE WHEN verkaufschance = 'keine' THEN 1 ELSE 0 END) as keine,
                SUM(lagerwert) as total_lagerwert,
                SUM(CASE WHEN verkaufschance IN ('hoch', 'mittel') THEN lagerwert ELSE 0 END) as verkaufbar_lagerwert,
                MAX(abgefragt_am) as letzte_abfrage
            FROM penner_marktpreise
        """)

        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        stats = dict(zip(columns, row))

        # Decimal zu float
        for key in ['total_lagerwert', 'verkaufbar_lagerwert']:
            if stats.get(key) is not None:
                stats[key] = float(stats[key])

        return stats

    except Exception as e:
        print(f"  Fehler beim Laden der Statistik: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()


def format_euro(value):
    """Formatiert als Euro"""
    try:
        v = float(value)
        if abs(v) >= 1000:
            return f"{v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"


def format_date(dt):
    """Formatiert Datetime"""
    if dt is None:
        return "-"
    if isinstance(dt, str):
        return dt[:10]
    return dt.strftime('%d.%m.%Y')


def build_email_html(teile, stats):
    """
    Erstellt HTML-Body für den Report.
    """
    heute = datetime.now()

    # Statistik-Zeile
    stats_gesamt = stats.get('gesamt', 0)
    stats_hoch = stats.get('hoch', 0)
    stats_mittel = stats.get('mittel', 0)
    stats_lagerwert = stats.get('total_lagerwert', 0)
    stats_verkaufbar = stats.get('verkaufbar_lagerwert', 0)

    # Teile-Tabelle bauen
    teile_html = ""
    for i, teil in enumerate(teile):
        bg = '#f9f9f9' if i % 2 == 0 else '#ffffff'

        # Chance-Badge Farbe
        chance = teil.get('verkaufschance', 'unbekannt')
        if chance == 'hoch':
            chance_color = '#28a745'
            chance_text = 'HOCH'
        elif chance == 'mittel':
            chance_color = '#ffc107'
            chance_text = 'MITTEL'
        else:
            chance_color = '#6c757d'
            chance_text = chance.upper()

        # Marge berechnen
        empf_vk = teil.get('empf_verkaufspreis', 0) or 0
        ek = teil.get('ek_preis', 0) or 0
        marge_prozent = ((empf_vk - ek) / ek * 100) if ek > 0 else 0

        teile_html += f"""
        <tr style="background: {bg};">
            <td style="padding: 8px; font-weight: bold;">{teil.get('part_number', '-')}</td>
            <td style="padding: 8px;">{teil.get('beschreibung', '-')[:40]}</td>
            <td style="padding: 8px; text-align: right;">{teil.get('bestand', 0)}</td>
            <td style="padding: 8px; text-align: right;">{format_euro(teil.get('lagerwert', 0))}</td>
            <td style="padding: 8px; text-align: right; color: #28a745; font-weight: bold;">{format_euro(empf_vk)}</td>
            <td style="padding: 8px; text-align: center;">
                <span style="background: {chance_color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">{chance_text}</span>
            </td>
            <td style="padding: 8px; text-align: right;">{teil.get('tage_seit_abgang', 0)} Tage</td>
        </tr>
        """

    # Gesamtes HTML
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 900px; margin: 0 auto;">
        <h2 style="color: #0066cc; margin-bottom: 5px;">Penner Verkaufschancen - Wochenreport</h2>
        <p style="color: #666; margin-top: 0;">KW {heute.isocalendar()[1]} | Stand: {heute.strftime('%d.%m.%Y %H:%M')} Uhr</p>

        <!-- Statistik-Karten -->
        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <tr>
                <td style="padding: 15px; background: #e9f5e9; text-align: center; border-radius: 8px 0 0 8px;">
                    <div style="font-size: 24px; font-weight: bold; color: #28a745;">{stats_hoch}</div>
                    <div style="color: #666; font-size: 12px;">Hohe Chance</div>
                </td>
                <td style="padding: 15px; background: #fff8e6; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #ffc107;">{stats_mittel}</div>
                    <div style="color: #666; font-size: 12px;">Mittlere Chance</div>
                </td>
                <td style="padding: 15px; background: #e6f3ff; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #0066cc;">{format_euro(stats_verkaufbar)}</div>
                    <div style="color: #666; font-size: 12px;">Verkaufbarer Wert</div>
                </td>
                <td style="padding: 15px; background: #f0f0f0; text-align: center; border-radius: 0 8px 8px 0;">
                    <div style="font-size: 24px; font-weight: bold; color: #666;">{stats_gesamt}</div>
                    <div style="color: #666; font-size: 12px;">Teile analysiert</div>
                </td>
            </tr>
        </table>

        <h3 style="color: #333; margin-top: 25px;">Top {len(teile)} Verkaufschancen</h3>

        <table style="border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 13px;">
            <tr style="background: #0066cc; color: white;">
                <th style="padding: 10px; text-align: left;">Teilenummer</th>
                <th style="padding: 10px; text-align: left;">Beschreibung</th>
                <th style="padding: 10px; text-align: right;">Bestand</th>
                <th style="padding: 10px; text-align: right;">Lagerwert</th>
                <th style="padding: 10px; text-align: right;">Empf. VK</th>
                <th style="padding: 10px; text-align: center;">Chance</th>
                <th style="padding: 10px; text-align: right;">Lagerzeit</th>
            </tr>
            {teile_html}
        </table>

        <div style="background: #f5f5f5; padding: 15px; margin-top: 20px; border-radius: 8px;">
            <strong>Empfehlung:</strong> Die Teile mit "HOCH" haben gute Marktpreise und sollten priorisiert
            auf eBay Kleinanzeigen oder Daparto eingestellt werden.
        </div>

        <p style="margin-top: 20px;">
            <a href="http://drive.auto-greiner.de/werkstatt/renner-penner"
               style="background: #0066cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                Zum Dashboard
            </a>
        </p>

        <p style="color: #999; font-size: 11px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
            Automatisch generiert von DRIVE - Greiner Portal<br>
            Marktpreise werden nachts automatisch von eBay und Daparto abgefragt.
        </p>
    </body>
    </html>
    """

    return html


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Penner Verkaufschancen Wochenreport')
    parser.add_argument('--force', action='store_true', help='Ignoriere Wochenend-Check')
    parser.add_argument('--test-email', type=str, help='Report an Test-Adresse senden')
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"PENNER VERKAUFSCHANCEN - WOCHENREPORT")
    print(f"{datetime.now().strftime('%d.%m.%Y %H:%M')}")
    if args.force:
        print("FORCE-MODUS aktiv")
    if args.test_email:
        print(f"TEST-MODUS - Sende an: {args.test_email}")
    print(f"{'='*60}")

    heute = date.today()

    # Nur Montags senden (außer --force)
    if not args.force and heute.weekday() != 0:  # 0 = Montag
        print(f"Heute ist kein Montag ({heute.strftime('%A')}) - kein Report")
        print(f"{'='*60}\n")
        return 0

    try:
        # Daten laden
        print("\n[1] Lade Top-Verkaufschancen...")
        teile = get_top_verkaufschancen(limit=20)
        print(f"    {len(teile)} Teile gefunden")

        if not teile:
            print("    WARNUNG: Keine Verkaufschancen gefunden!")
            print("    Bitte prüfen ob der Nacht-Job läuft.")
            print(f"{'='*60}\n")
            return 0

        print("\n[2] Lade Statistik...")
        stats = get_statistik()
        print(f"    {stats.get('gesamt', 0)} Teile im Cache")
        print(f"    {stats.get('hoch', 0)} mit hoher Chance")
        print(f"    {stats.get('mittel', 0)} mit mittlerer Chance")

        print("\n[3] Erstelle E-Mail...")
        html_body = build_email_html(teile, stats)

        # Empfänger
        if args.test_email:
            empfaenger = [args.test_email]
        else:
            empfaenger = get_empfaenger()

        print(f"    Empfänger: {', '.join(empfaenger)}")

        # Betreff
        betreff = f"Penner Verkaufschancen KW{heute.isocalendar()[1]} | {stats.get('hoch', 0)} mit hoher Chance | {format_euro(stats.get('verkaufbar_lagerwert', 0))} verkaufbar"

        print("\n[4] Sende E-Mail...")
        from api.graph_mail_connector import GraphMailConnector
        connector = GraphMailConnector()

        connector.send_mail(
            sender_email=ABSENDER,
            to_emails=empfaenger,
            subject=betreff,
            body_html=html_body
        )

        print(f"    OK! E-Mail an {len(empfaenger)} Empfänger gesendet.")

        print(f"\n{'='*60}")
        print(f"ERFOLG!")
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
