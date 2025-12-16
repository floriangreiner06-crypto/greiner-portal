#!/usr/bin/env python3
"""
WERKSTATT TAGESBERICHT - EMAIL REPORT
=====================================
Sendet täglich einen kompakten Werkstatt-Tagesbericht per E-Mail.
Nutzt die bestehenden API-Endpoints für konsistente Daten.

WICHTIG: Alle KPI-Berechnungen kommen aus utils/kpi_definitions.py!

Verwendung:
    python3 werkstatt_tagesbericht_email.py [--datum YYYY-MM-DD] [--betrieb 1|3] [--test]

Author: Claude
Date: 2025-12-09 (TAG 110)
Updated: 2025-12-16 (TAG 120) - Azubis ausgeschlossen, Auftragsnummern bei Warnungen, Link-Fix
"""

import os
import sys
import argparse
import requests
from datetime import datetime, date
import logging

# Pfad für Imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from api.graph_mail_connector import GraphMailConnector
from utils.kpi_definitions import (
    format_euro,
    format_prozent,
    bewerte_leistungsgrad,
    bewerte_produktivitaet
)

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BETRIEB_NAMEN = {1: 'Deggendorf', 2: 'Hyundai DEG', 3: 'Landau'}

# Empfänger-Konfiguration
EMAIL_CONFIG = {
    'absender': 'drive@auto-greiner.de',
    'empfaenger': {
        1: ['florian.greiner@auto-greiner.de'],
        3: ['florian.greiner@auto-greiner.de'],
        'alle': ['florian.greiner@auto-greiner.de']
    }
}

# API Base URL (lokal)
API_BASE = 'http://localhost:5000/api/werkstatt/live'

# Portal URL
PORTAL_URL = 'http://drive.auto-greiner.de'


def hole_api_daten(datum: date, subsidiary: int = None) -> dict:
    """
    Holt Daten von den bestehenden API-Endpoints.
    Das garantiert konsistente Zahlen mit dem Portal.

    Die API berechnet die KPIs bereits korrekt mit den zentralen Formeln!
    """
    result = {
        'datum': datum,
        'datum_formatiert': datum.strftime('%d.%m.%Y'),
        'wochentag': ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'][datum.weekday()],
        'betrieb': subsidiary,
        'betrieb_name': BETRIEB_NAMEN.get(subsidiary, 'Alle Betriebe'),
        'kpis': {},
        'mechaniker_ranking': [],
        'nachkalkulation': [],
        'probleme': []
    }

    try:
        # 1. Leistung (Monat für Ranking) - API schließt Azubis bereits aus!
        params = {'zeitraum': 'monat'}
        if subsidiary:
            params['betrieb'] = subsidiary

        resp = requests.get(f'{API_BASE}/leistung', params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            result['kpis']['mechaniker_anwesend'] = data.get('anzahl_mechaniker', 0)
            result['kpis']['leistungsgrad_monat'] = data.get('gesamt_leistungsgrad', 0)
            result['kpis']['umsatz_lohn'] = data.get('gesamt_umsatz', 0)

            # Top 5 Mechaniker (Azubis bereits von API ausgeschlossen)
            for m in data.get('mechaniker', [])[:5]:
                result['mechaniker_ranking'].append({
                    'name': m.get('name', f"MA {m.get('mechaniker_nr')}"),
                    'betrieb': BETRIEB_NAMEN.get(m.get('betrieb'), '?'),
                    'auftraege': m.get('auftraege', 0),
                    'aw': m.get('aw', 0),
                    'leistungsgrad': m.get('leistungsgrad', 0)
                })

        # 2. Nachkalkulation (Heute) - HAUPTQUELLE für Tages-KPIs!
        params = {'datum': datum.strftime('%Y-%m-%d')}
        if subsidiary:
            params['subsidiary'] = subsidiary

        resp = requests.get(f'{API_BASE}/nachkalkulation', params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            summary = data.get('summary', {})

            # KPIs direkt aus der API - KEINE eigene Berechnung!
            result['kpis']['auftraege_abgerechnet'] = summary.get('anzahl_rechnungen', 0)
            result['kpis']['entgangener_umsatz'] = summary.get('total_verlust_eur', 0)
            result['kpis']['verrechnet_aw'] = summary.get('total_vorgabe_aw', 0)
            result['kpis']['gestempelt_aw'] = summary.get('total_gestempelt_aw', 0)
            result['kpis']['leistungsgrad_heute'] = summary.get('gesamt_leistungsgrad', 0)

            # Top 5 Aufträge mit entgangenem Umsatz
            for a in data.get('auftraege', []):
                if a.get('verlust_eur', 0) > 0:
                    result['nachkalkulation'].append({
                        'auftrag_nr': a.get('order_number'),
                        'kennzeichen': a.get('kennzeichen'),
                        'kunde': a.get('kunde'),
                        'mechaniker': a.get('mechaniker'),
                        'vorgabe_aw': a.get('vorgabe_aw', 0),
                        'gestempelt_aw': a.get('gestempelt_aw', 0),
                        'entgangener_umsatz': a.get('verlust_eur', 0),
                        'leistungsgrad': a.get('leistungsgrad', 0)
                    })

            # Nur Top 5 behalten, sortiert nach entgangenem Umsatz
            result['nachkalkulation'] = sorted(
                result['nachkalkulation'],
                key=lambda x: x['entgangener_umsatz'],
                reverse=True
            )[:5]

        # 3. Tagesbericht (Probleme) - MIT Auftragsnummern!
        resp = requests.get(f'{API_BASE}/tagesbericht', params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            summary = data.get('summary', {})

            # Listen mit Auftragsnummern direkt aus API
            ohne_vorgabe_liste = data.get('ohne_vorgabe', [])
            ueberschritten_liste = data.get('ueberschritten', [])

            ohne_vorgabe_count = summary.get('ohne_vorgabe', 0)
            ueberschritten_count = summary.get('ueberschritten', 0)

            if ohne_vorgabe_count > 0:
                # Auftragsnummern aus der Liste holen
                ohne_vorgabe_nummern = [
                    str(a.get('order_number', '?'))
                    for a in ohne_vorgabe_liste
                ][:5]  # Max 5 anzeigen
                nummern_text = f" ({', '.join(ohne_vorgabe_nummern)})" if ohne_vorgabe_nummern else ""
                result['probleme'].append({
                    'icon': '⚠️',
                    'text': f'{ohne_vorgabe_count} Aufträge ohne AW-Vorgabe{nummern_text}',
                    'severity': 'warning'
                })

            if ueberschritten_count > 0:
                # Auftragsnummern aus der Liste holen
                ueberschritten_nummern = [
                    str(a.get('order_number', '?'))
                    for a in ueberschritten_liste
                ][:5]  # Max 5 anzeigen
                nummern_text = f" ({', '.join(ueberschritten_nummern)})" if ueberschritten_nummern else ""
                result['probleme'].append({
                    'icon': '⏰',
                    'text': f'{ueberschritten_count} Aufträge mit Vorgabe-Überschreitung{nummern_text}',
                    'severity': 'warning'
                })

        # Weitere Probleme basierend auf KPIs (nutze zentrale Bewertung!)
        lg = result['kpis'].get('leistungsgrad_heute', 0)
        bewertung = bewerte_leistungsgrad(lg if lg > 0 else None)

        if bewertung['status'] == 'kritisch':
            result['probleme'].append({
                'icon': '📉',
                'text': f"Leistungsgrad nur {format_prozent(lg)} (Ziel: ≥85%)",
                'severity': 'danger'
            })

        entgangen = result['kpis'].get('entgangener_umsatz', 0)
        if entgangen > 500:
            result['probleme'].append({
                'icon': '💸',
                'text': f"Entgangener Umsatz: {format_euro(entgangen)}",
                'severity': 'danger'
            })

    except Exception as e:
        logger.error(f"Fehler beim API-Abruf: {e}")

    return result


def erstelle_email_html(daten: dict) -> str:
    """
    Erstellt den HTML-Body für die E-Mail.
    Nutzt zentrale Formatierungsfunktionen aus utils/kpi_definitions.py
    """
    kpis = daten['kpis']

    # Leistungsgrad heute mit zentraler Bewertung
    lg = kpis.get('leistungsgrad_heute', 0)
    lg_bewertung = bewerte_leistungsgrad(lg if lg > 0 else None)
    lg_color = lg_bewertung['farbe']
    lg_status = lg_bewertung['icon']

    # Probleme-HTML
    probleme_html = ""
    if daten['probleme']:
        probleme_items = "".join([
            f"<li style='margin: 5px 0;'>{p['icon']} {p['text']}</li>"
            for p in daten['probleme']
        ])
        probleme_html = f"""
        <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 15px; margin: 20px 0;">
            <strong style="color: #856404;">⚠️ Aufmerksamkeit erforderlich:</strong>
            <ul style="margin: 10px 0 0 20px; padding: 0;">{probleme_items}</ul>
        </div>
        """

    # Mechaniker-Ranking mit zentraler Bewertung
    ranking_rows = ""
    for i, m in enumerate(daten['mechaniker_ranking'][:5], 1):
        medal = ['🥇', '🥈', '🥉', '4.', '5.'][i-1]
        lg_m = m['leistungsgrad'] or 0
        lg_m_bewertung = bewerte_leistungsgrad(lg_m if lg_m > 0 else None)
        ranking_rows += f"""
        <tr>
            <td style="padding: 8px; text-align: center;">{medal}</td>
            <td style="padding: 8px;">{m['name']}</td>
            <td style="padding: 8px; text-align: center;">{m['auftraege']}</td>
            <td style="padding: 8px; text-align: center;">{m['aw']:.1f}</td>
            <td style="padding: 8px; text-align: center; font-weight: bold; color: {lg_m_bewertung['farbe']};">{format_prozent(lg_m)}</td>
        </tr>
        """

    # Nachkalkulation (Top 5 mit entgangenem Umsatz)
    nachkalk_rows = ""
    for n in daten['nachkalkulation'][:5]:
        nachkalk_rows += f"""
        <tr>
            <td style="padding: 8px; font-family: monospace;">{n['auftrag_nr']}</td>
            <td style="padding: 8px;">{n['kennzeichen'] or '-'}</td>
            <td style="padding: 8px;">{n['mechaniker'] or '-'}</td>
            <td style="padding: 8px; text-align: right;">{n['vorgabe_aw']:.1f}</td>
            <td style="padding: 8px; text-align: right;">{n['gestempelt_aw']:.1f}</td>
            <td style="padding: 8px; text-align: right; color: #dc3545; font-weight: bold;">{format_euro(n['entgangener_umsatz'])}</td>
        </tr>
        """

    # Entgangener Umsatz-Highlight
    entgangen = kpis.get('entgangener_umsatz', 0)
    entgangen_html = ""
    if entgangen > 0:
        entgangen_html = f"""
        <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; margin: 0; text-align: center;">
            <span style="font-size: 14px; color: #721c24;">💸 Entgangener Umsatz durch Überzeiten:</span>
            <span style="font-size: 24px; font-weight: bold; color: #dc3545; margin-left: 10px;">{format_euro(entgangen)}</span>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #333; max-width: 700px; margin: 0 auto; padding: 20px; background: #f5f5f5;">

        <!-- Header -->
        <div style="background: linear-gradient(135deg, #1a5f7a, #2e8b57); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">🔧 Werkstatt Tagesbericht</h1>
            <p style="margin: 10px 0 0; opacity: 0.9;">{daten['wochentag']}, {daten['datum_formatiert']} • {daten['betrieb_name']}</p>
        </div>

        <!-- KPI Strip -->
        <div style="background: white; padding: 20px; border-left: 1px solid #ddd; border-right: 1px solid #ddd;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="text-align: center; padding: 15px; width: 25%;">
                        <div style="font-size: 32px; font-weight: bold; color: #1a5f7a;">{kpis.get('mechaniker_anwesend', 0)}</div>
                        <div style="font-size: 12px; color: #666; text-transform: uppercase;">Mechaniker</div>
                    </td>
                    <td style="text-align: center; padding: 15px; width: 25%;">
                        <div style="font-size: 32px; font-weight: bold; color: #2e8b57;">{kpis.get('auftraege_abgerechnet', 0)}</div>
                        <div style="font-size: 12px; color: #666; text-transform: uppercase;">Aufträge</div>
                    </td>
                    <td style="text-align: center; padding: 15px; width: 25%;">
                        <div style="font-size: 32px; font-weight: bold; color: {lg_color};">{format_prozent(lg)}</div>
                        <div style="font-size: 12px; color: #666; text-transform: uppercase;">Leistungsgrad</div>
                    </td>
                    <td style="text-align: center; padding: 15px; width: 25%;">
                        <div style="font-size: 24px; font-weight: bold; color: #333;">{format_euro(kpis.get('umsatz_lohn', 0))}</div>
                        <div style="font-size: 12px; color: #666; text-transform: uppercase;">Umsatz (Monat)</div>
                    </td>
                </tr>
            </table>
        </div>

        <!-- Entgangener Umsatz-Highlight -->
        {entgangen_html}

        <!-- Probleme -->
        {probleme_html}

        <!-- Mechaniker Ranking (Monat) -->
        <div style="background: white; padding: 20px; border: 1px solid #ddd; margin-top: 20px; border-radius: 8px;">
            <h2 style="margin: 0 0 15px; font-size: 18px; color: #333;">🏆 Top Mechaniker (Monat)</h2>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <thead>
                    <tr style="background: #f5f5f5;">
                        <th style="padding: 10px; text-align: center; width: 40px;"></th>
                        <th style="padding: 10px; text-align: left;">Name</th>
                        <th style="padding: 10px; text-align: center;">Auftr.</th>
                        <th style="padding: 10px; text-align: center;">AW</th>
                        <th style="padding: 10px; text-align: center;">LG</th>
                    </tr>
                </thead>
                <tbody>
                    {ranking_rows if ranking_rows else '<tr><td colspan="5" style="padding: 15px; text-align: center; color: #999;">Keine Daten</td></tr>'}
                </tbody>
            </table>
        </div>

        <!-- Nachkalkulation -->
        {"" if not daten['nachkalkulation'] else f'''
        <div style="background: white; padding: 20px; border: 1px solid #ddd; margin-top: 20px; border-radius: 8px;">
            <h2 style="margin: 0 0 15px; font-size: 18px; color: #333;">📊 Aufträge mit entgangenem Umsatz (Top 5)</h2>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead>
                    <tr style="background: #f5f5f5;">
                        <th style="padding: 8px; text-align: left;">Auftrag</th>
                        <th style="padding: 8px; text-align: left;">Kz.</th>
                        <th style="padding: 8px; text-align: left;">Mech.</th>
                        <th style="padding: 8px; text-align: right;">Vorg.</th>
                        <th style="padding: 8px; text-align: right;">Gest.</th>
                        <th style="padding: 8px; text-align: right;">Entg. Umsatz</th>
                    </tr>
                </thead>
                <tbody>
                    {nachkalk_rows}
                </tbody>
            </table>
        </div>
        '''}

        <!-- Footer -->
        <div style="background: #333; color: #999; padding: 15px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px;">
            <p style="margin: 0;">
                Automatisch generiert von <strong style="color: white;">Greiner DRIVE</strong><br>
                {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr
            </p>
            <p style="margin: 10px 0 0;">
                <a href="{PORTAL_URL}/werkstatt/uebersicht" style="color: #4da6ff;">📊 Vollständigen Bericht im Portal ansehen</a>
            </p>
        </div>

    </body>
    </html>
    """

    return html


def sende_tagesbericht(datum: date = None, subsidiary: int = None, test_mode: bool = False):
    """
    Hauptfunktion: Holt Daten und sendet E-Mail.
    """
    if datum is None:
        datum = date.today()

    logger.info(f"=== Werkstatt Tagesbericht für {datum} ===")

    # Daten von API holen
    logger.info("Hole Daten von API...")
    daten = hole_api_daten(datum, subsidiary)

    logger.info(f"  Mechaniker: {daten['kpis'].get('mechaniker_anwesend', 0)}")
    logger.info(f"  Aufträge: {daten['kpis'].get('auftraege_abgerechnet', 0)}")
    logger.info(f"  Leistungsgrad: {format_prozent(daten['kpis'].get('leistungsgrad_heute', 0))}")
    logger.info(f"  Entgangener Umsatz: {format_euro(daten['kpis'].get('entgangener_umsatz', 0))}")

    # HTML erstellen
    html_body = erstelle_email_html(daten)

    # Empfänger bestimmen
    if subsidiary and subsidiary in EMAIL_CONFIG['empfaenger']:
        empfaenger = EMAIL_CONFIG['empfaenger'][subsidiary]
    else:
        empfaenger = EMAIL_CONFIG['empfaenger']['alle']

    absender = EMAIL_CONFIG['absender']
    betreff = f"🔧 Werkstatt Tagesbericht - {daten['datum_formatiert']} ({daten['betrieb_name']})"

    if test_mode:
        logger.info(f"TEST-MODUS: E-Mail würde gesendet an {empfaenger}")
        logger.info(f"  Betreff: {betreff}")
        # HTML speichern für Vorschau
        preview_path = f"/tmp/werkstatt_tagesbericht_{datum}.html"
        with open(preview_path, 'w', encoding='utf-8') as f:
            f.write(html_body)
        logger.info(f"  HTML-Vorschau gespeichert: {preview_path}")
        return True

    # E-Mail senden
    logger.info(f"Sende E-Mail an {empfaenger}...")

    try:
        connector = GraphMailConnector()
        connector.send_mail(
            sender_email=absender,
            to_emails=empfaenger,
            subject=betreff,
            body_html=html_body
        )
        logger.info("✅ E-Mail erfolgreich gesendet!")
        return True

    except Exception as e:
        logger.error(f"❌ Fehler beim Senden: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Werkstatt Tagesbericht per E-Mail senden')
    parser.add_argument('--datum', type=str, help='Datum im Format YYYY-MM-DD (default: heute)')
    parser.add_argument('--betrieb', type=int, choices=[1, 3], help='Betrieb (1=Deggendorf, 3=Landau)')
    parser.add_argument('--test', action='store_true', help='Test-Modus (keine E-Mail senden)')

    args = parser.parse_args()

    datum = None
    if args.datum:
        datum = datetime.strptime(args.datum, '%Y-%m-%d').date()

    success = sende_tagesbericht(
        datum=datum,
        subsidiary=args.betrieb,
        test_mode=args.test
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
