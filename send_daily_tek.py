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

from datetime import datetime, date, timedelta
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
    Holt TEK-Daten - TAG204: Direkt über controlling_data + manuelle Ergänzungen
    Nutzt die gleiche Logik wie die Web-Oberfläche - garantiert konsistente Daten!

    TAG146: Ursprünglich HTTP API-Call
    TAG204: Geändert auf controlling_data + manuelle Heute-Daten/Stückzahlen

    standort: None=Alle, 'DEG'=Deggendorf, 'LAN'=Landau
    """
    from datetime import date, timedelta
    from api.controlling_data import get_tek_data as get_tek_data_direct
    from routes.controlling_routes import get_stueckzahlen_locosoft, get_werktage_monat
    from api.db_utils import get_locosoft_connection
    import psycopg2.extras

    heute = date.today()
    if not monat:
        monat = heute.month
    if not jahr:
        jahr = heute.year

    # Standort-Mapping
    if standort == 'DEG':
        firma = '1'  # Stellantis
        standort_api = '1'  # Deggendorf
        standort_name = 'Deggendorf'
    elif standort == 'LAN':
        firma = '1'  # Stellantis
        standort_api = '2'  # Landau
        standort_name = 'Landau'
    else:
        firma = '0'  # Alle
        standort_api = '0'  # Alle
        standort_name = 'Gesamt'

    # TAG204: Hole TEK-Daten direkt aus DB (ohne API-Auth)
    try:
        tek_data = get_tek_data_direct(
            monat=monat,
            jahr=jahr,
            firma=firma,
            standort=standort_api,
            modus='teil',
            umlage='mit'
        )
        
        # TAG204: Hole zusätzlich Heute-Daten (wenn im aktuellen Monat)
        heute_bereiche = {}
        if heute.year == jahr and heute.month == monat:
            heute_str = heute.isoformat()
            morgen_str = (heute + timedelta(days=1)).isoformat()
            
            # Firma-Filter für Locosoft
            firma_filter_umsatz = ""
            firma_filter_einsatz = ""
            if firma == '1':
                firma_filter_umsatz = "AND subsidiary_to_company_ref = 1"
                firma_filter_einsatz = "AND subsidiary_to_company_ref = 1"
                if standort_api == '1':
                    firma_filter_umsatz += " AND branch_number = 1"
                    firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
                elif standort_api == '2':
                    firma_filter_umsatz += " AND branch_number = 3"
                    firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
            elif firma == '2':
                firma_filter_umsatz = "AND subsidiary_to_company_ref = 2"
                firma_filter_einsatz = "AND subsidiary_to_company_ref = 2"
            
            with get_locosoft_connection() as loco_conn:
                loco_cur = loco_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Tagesumsatz PRO BEREICH (Heute)
                loco_cur.execute(f"""
                    SELECT
                        CASE
                            WHEN nominal_account_number BETWEEN 810000 AND 819999 THEN '1-NW'
                            WHEN nominal_account_number BETWEEN 820000 AND 829999 THEN '2-GW'
                            WHEN nominal_account_number BETWEEN 830000 AND 839999 THEN '3-Teile'
                            WHEN nominal_account_number BETWEEN 840000 AND 849999 THEN '4-Lohn'
                            WHEN nominal_account_number BETWEEN 860000 AND 869999 THEN '5-Sonst'
                            ELSE '9-Andere'
                        END as bereich,
                        COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
                    FROM journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN 800000 AND 899999
                      {firma_filter_umsatz}
                    GROUP BY bereich
                """, (heute_str, morgen_str))
                heute_umsatz_bereich = {r['bereich']: float(r['umsatz'] or 0) for r in loco_cur.fetchall()}
                
                # Tageseinsatz PRO BEREICH (Heute)
                loco_cur.execute(f"""
                    SELECT
                        CASE
                            WHEN nominal_account_number BETWEEN 710000 AND 719999 THEN '1-NW'
                            WHEN nominal_account_number BETWEEN 720000 AND 729999 THEN '2-GW'
                            WHEN nominal_account_number BETWEEN 730000 AND 739999 THEN '3-Teile'
                            WHEN nominal_account_number BETWEEN 740000 AND 749999 THEN '4-Lohn'
                            WHEN nominal_account_number BETWEEN 760000 AND 769999 THEN '5-Sonst'
                            ELSE '9-Andere'
                        END as bereich,
                        COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as einsatz
                    FROM journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN 700000 AND 799999
                      {firma_filter_einsatz}
                    GROUP BY bereich
                """, (heute_str, morgen_str))
                heute_einsatz_bereich = {r['bereich']: float(r['einsatz'] or 0) for r in loco_cur.fetchall()}
                
                # Pro Bereich zusammenführen (Heute)
                for bkey in ['1-NW', '2-GW', '3-Teile', '4-Lohn', '5-Sonst']:
                    h_umsatz = heute_umsatz_bereich.get(bkey, 0)
                    h_einsatz = heute_einsatz_bereich.get(bkey, 0)
                    heute_bereiche[bkey] = {
                        'umsatz': round(h_umsatz, 2),
                        'db1': round(h_umsatz - h_einsatz, 2)
                    }
                
                loco_cur.close()
        
        # TAG204: Stückzahlen holen
        von = f"{jahr}-{monat:02d}-01"
        bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"
        stueck_nw = get_stueckzahlen_locosoft(von, bis, '1-NW', firma, standort_api)
        stueck_gw = get_stueckzahlen_locosoft(von, bis, '2-GW', firma, standort_api)
        
        # TAG204: Werktage für Prognose
        werktage_info = get_werktage_monat(jahr, monat)
        
    except Exception as e:
        print(f"❌ FEHLER beim Abrufen der TEK-Daten: {e}")
        import traceback
        traceback.print_exc()
        raise

    # TAG204: Bereiche konvertieren - ERWEITERT mit Heute-Daten und Stückzahlen
    bereiche = []
    bereich_mapping = {'1-NW': '1-NW', '2-GW': '2-GW', '3-Teile': '3-Teile', '4-Lohn': '4-Lohn', '5-Sonst': '5-Sonst'}
    
    for b in tek_data.get('bereiche', []):
        bkey = bereich_mapping.get(b.get('id', ''), '')
        if not bkey:
            continue
        
        # Heute-Daten (immer anzeigen, auch wenn 0)
        hb = heute_bereiche.get(bkey, {})
        heute_umsatz = round(hb.get('umsatz', 0), 2)
        heute_db1 = round(hb.get('db1', 0), 2)
        
        # Stückzahlen
        stueck = 0
        db1_pro_stueck = 0
        if bkey == '1-NW':
            stueck = stueck_nw.get('gesamt_stueck', 0)
            if stueck > 0:
                db1_pro_stueck = round(b.get('db1', 0) / stueck, 2)
        elif bkey == '2-GW':
            stueck = stueck_gw.get('gesamt_stueck', 0)
            if stueck > 0:
                db1_pro_stueck = round(b.get('db1', 0) / stueck, 2)
        
        bereich_dict = {
            'bereich': bkey,
            'umsatz': round(b.get('umsatz', 0), 2),
            'einsatz': round(b.get('einsatz', 0), 2),
            'db1': round(b.get('db1', 0), 2),
            'marge': round(b.get('marge', 0), 1),
            'heute_umsatz': heute_umsatz,  # TAG204: Heute-Erlöse
            'heute_db1': heute_db1,  # TAG204: Heute-DB1
            'stueck': stueck,  # TAG204: Stückzahlen (nur NW/GW)
            'db1_pro_stueck': db1_pro_stueck  # TAG204: DB1/Stk
        }
        bereiche.append(bereich_dict)
    
    # Monat-Anzeige
    monat_namen = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
                   'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
    monat_display = f"{monat_namen[monat]} {jahr}"
    if standort:
        monat_display = f"{standort_name} - {monat_display}"
    
    # Daten aus tek_data extrahieren
    gesamt = tek_data.get('gesamt', {})
    vm = tek_data.get('vm', {})
    vj = tek_data.get('vj', {})

    # TAG204: Filter-Info für Drill-Downs speichern
    return {
        'datum': heute.strftime('%d.%m.%Y'),
        'monat': monat_display,
        'standort': standort,
        'standort_name': standort_name,
        'firma': firma,  # TAG204: Für Drill-Down APIs
        'standort_api': standort_api,  # TAG204: Für Drill-Down APIs
        'monat_num': monat,  # TAG204: Für Drill-Down APIs
        'jahr_num': jahr,  # TAG204: Für Drill-Down APIs
        'gesamt': {
            'umsatz': round(gesamt.get('umsatz', 0), 2),
            'einsatz': round(gesamt.get('einsatz', 0), 2),
            'db1': round(gesamt.get('db1', 0), 2),
            'marge': round(gesamt.get('marge', 0), 1),
            'prognose': round(gesamt.get('prognose', 0), 2),
            'breakeven': round(gesamt.get('breakeven', 0), 2),
            'breakeven_abstand': round(gesamt.get('breakeven_diff', 0), 2)
        },
        'bereiche': bereiche,  # TAG204: Jetzt mit heute_umsatz, heute_db1, stueck, db1_pro_stueck
        'vormonat': {
            'db1': round(vm.get('db1', 0), 2),
            'marge': round(vm.get('marge', 0), 1)
        },
        'vorjahr': {
            'db1': round(vj.get('db1', 0), 2),
            'marge': round(vj.get('marge', 0), 1)
        }
    }


def format_euro(value):
    """Formatiert als Euro"""
    try:
        v = float(value)
        if abs(v) >= 1000:
            return f"{v/1000:,.1f}k".replace(",", "X").replace(".", ",").replace("X", ".")
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
    """
    Erstellt HTML-Body für Gesamt-Report - TAG204: OPTION A - KPI-CARDS DESIGN
    
    Moderne, mobile-friendly Darstellung mit:
    - 4 KPI-Cards für Gesamt-KPIs
    - Kompakte Abteilungsübersicht mit Farbcodierung
    - Heute vs. Monat kumuliert klar getrennt
    """
    gesamt = data['gesamt']
    
    # Gesamt-Summen berechnen
    gesamt_heute_umsatz = sum(b.get('heute_umsatz', 0) for b in data['bereiche'])
    gesamt_heute_db1 = sum(b.get('heute_db1', 0) for b in data['bereiche'])
    gesamt_monat_umsatz = sum(b.get('umsatz', 0) for b in data['bereiche'])
    gesamt_monat_db1 = gesamt['db1']
    
    # Breakeven-Status
    breakeven_status = "POSITIV" if gesamt['breakeven_abstand'] >= 0 else "KRITISCH"
    breakeven_color = "#28a745" if gesamt['breakeven_abstand'] >= 0 else "#dc3545"
    breakeven_prefix = "+" if gesamt['breakeven_abstand'] >= 0 else ""

    # TAG204: KST-Mapping
    KST_MAPPING = {
        '1-NW': {'kst': '1', 'name': 'Neuwagen', 'order': 1, 'show_stueck': True, 'icon': '🚗'},
        '2-GW': {'kst': '2', 'name': 'Gebrauchtwagen', 'order': 2, 'show_stueck': True, 'icon': '🚙'},
        '4-Lohn': {'kst': '3', 'name': 'Service/Werkstatt', 'order': 3, 'show_stueck': False, 'icon': '🔧'},
        '3-Teile': {'kst': '6', 'name': 'Teile & Zubehör', 'order': 4, 'show_stueck': False, 'icon': '📦'},
        '5-Sonst': {'kst': '7', 'name': 'Sonstige', 'order': 5, 'show_stueck': False, 'icon': '📋'}
    }
    
    # Bereiche nach KST-Reihenfolge sortieren
    bereiche_sorted = sorted(
        data['bereiche'],
        key=lambda b: KST_MAPPING.get(b['bereich'], {}).get('order', 99)
    )
    
    # Abteilungen-Cards generieren
    abteilungen_cards = ""
    
    for b in bereiche_sorted:
        bkey = b['bereich']
        cfg = KST_MAPPING.get(bkey, {'kst': '-', 'name': bkey, 'show_stueck': False, 'icon': '📊'})
        
        # Heute-Daten (immer anzeigen, auch wenn 0)
        heute_umsatz = b.get('heute_umsatz', 0)
        heute_db1 = b.get('heute_db1', 0)
        
        # Monat-Daten
        monat_umsatz = b.get('umsatz', 0)
        monat_db1 = b.get('db1', 0)
        
        # Stück (nur bei NW/GW)
        stueck = b.get('stueck', 0) if cfg['show_stueck'] else None
        stueck_info = f" | {stueck} Stück" if stueck and stueck > 0 else ""
        
        # Farbcodierung basierend auf DB1 (vereinfacht)
        # Grün: DB1 > 0, Gelb: DB1 = 0, Rot: DB1 < 0
        if monat_db1 > 0:
            card_bg = "#d4edda"
            card_border = "#28a745"
            status_icon = "🟢"
        elif monat_db1 == 0:
            card_bg = "#fff3cd"
            card_border = "#ffc107"
            status_icon = "🟡"
        else:
            card_bg = "#f8d7da"
            card_border = "#dc3545"
            status_icon = "🔴"
        
        abteilungen_cards += f"""
        <div style="background: {card_bg}; border-left: 4px solid {card_border}; padding: 15px; margin: 10px 0; border-radius: 4px;">
            <div style="font-size: 18px; font-weight: bold; margin-bottom: 10px;">
                {cfg['icon']} {cfg['name']} (KST {cfg['kst']}){stueck_info} {status_icon}
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                <tr>
                    <td style="padding: 5px 0; color: #666;">Heute:</td>
                    <td style="padding: 5px 0; text-align: right; font-weight: bold;">{format_euro(heute_umsatz)} € Erlöse</td>
                    <td style="padding: 5px 0; text-align: right; font-weight: bold;">{format_euro(heute_db1)} € DB1</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0; color: #666;">Monat:</td>
                    <td style="padding: 5px 0; text-align: right;">{format_euro(monat_umsatz)} € Erlöse</td>
                    <td style="padding: 5px 0; text-align: right; font-weight: bold;">{format_euro(monat_db1)} € DB1</td>
                </tr>
            </table>
        </div>"""

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 700px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #0066cc, #004499); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">📊 TEK - Tägliche Erfolgskontrolle</h1>
            <p style="margin: 10px 0 0; opacity: 0.9;">{data['monat']} | Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr</p>
        </div>

        <!-- KPI Cards (4 Cards für Gesamt-KPIs) -->
        <div style="background: white; padding: 20px; border-left: 1px solid #ddd; border-right: 1px solid #ddd;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="text-align: center; padding: 15px; width: 50%; border-right: 1px solid #eee;">
                        <div style="font-size: 28px; font-weight: bold; color: #0066cc;">{format_euro(gesamt_heute_umsatz)}</div>
                        <div style="font-size: 12px; color: #666; text-transform: uppercase; margin-top: 5px;">Erlöse Heute</div>
                    </td>
                    <td style="text-align: center; padding: 15px; width: 50%;">
                        <div style="font-size: 28px; font-weight: bold; color: #28a745;">{format_euro(gesamt_heute_db1)}</div>
                        <div style="font-size: 12px; color: #666; text-transform: uppercase; margin-top: 5px;">DB1 Heute</div>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center; padding: 15px; border-right: 1px solid #eee; border-top: 1px solid #eee;">
                        <div style="font-size: 28px; font-weight: bold; color: #0066cc;">{format_euro(gesamt_monat_umsatz)}</div>
                        <div style="font-size: 12px; color: #666; text-transform: uppercase; margin-top: 5px;">Erlöse Monat</div>
                    </td>
                    <td style="text-align: center; padding: 15px; border-top: 1px solid #eee;">
                        <div style="font-size: 28px; font-weight: bold; color: #28a745;">{format_euro(gesamt_monat_db1)}</div>
                        <div style="font-size: 12px; color: #666; text-transform: uppercase; margin-top: 5px;">DB1 Monat</div>
                    </td>
                </tr>
            </table>
        </div>

        <!-- Zusatz-KPIs -->
        <div style="background: white; padding: 15px; border-left: 1px solid #ddd; border-right: 1px solid #ddd; border-top: 1px solid #ddd;">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                <tr>
                    <td style="padding: 8px; color: #666;">Marge:</td>
                    <td style="padding: 8px; text-align: right; font-weight: bold; font-size: 16px;">{gesamt['marge']:.1f}%</td>
                </tr>
                <tr>
                    <td style="padding: 8px; color: #666;">Prognose:</td>
                    <td style="padding: 8px; text-align: right; font-weight: bold;">{format_euro(gesamt['prognose'])} €</td>
                </tr>
                <tr>
                    <td style="padding: 8px; color: #666;">Breakeven-Abstand:</td>
                    <td style="padding: 8px; text-align: right; font-weight: bold; color: {breakeven_color};">
                        {breakeven_prefix}{format_euro(gesamt['breakeven_abstand'])} € ({breakeven_status})
                    </td>
                </tr>
            </table>
        </div>

        <!-- Abteilungen -->
        <div style="background: white; padding: 20px; border-left: 1px solid #ddd; border-right: 1px solid #ddd; border-top: 1px solid #ddd;">
            <h2 style="margin: 0 0 15px 0; font-size: 18px; color: #333;">📋 Abteilungen</h2>
            {abteilungen_cards}
        </div>

        <!-- Footer -->
        <div style="background: white; padding: 15px; border-left: 1px solid #ddd; border-right: 1px solid #ddd; border-top: 1px solid #ddd; border-radius: 0 0 10px 10px;">
            <p style="margin: 0 0 10px 0; color: #666; font-size: 0.9rem;">Details im PDF-Anhang.</p>
            <p style="margin: 0; color: #999; font-size: 11px; border-top: 1px solid #eee; padding-top: 10px;">
                Automatisch generiert von DRIVE<br>
                <a href="http://drive.auto-greiner.de/controlling/tek" style="color: #0066cc; text-decoration: none;">→ In DRIVE öffnen</a>
            </p>
        </div>

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
    """
    Erstellt HTML-Body für Bereichs-Report - TAG204: VEREINFACHT
    Entfernt: Status "Ziel erreicht", Ziel-Marge
    Zeigt nur: DB1, Marge, Umsatz, Einsatz, Heute-Daten
    """
    BEREICH_NAMEN = {
        '1-NW': 'Neuwagen', '2-GW': 'Gebrauchtwagen',
        '3-Teile': 'Teile', '4-Lohn': 'Werkstatt', '5-Sonst': 'Sonstige'
    }

    bereich_name = BEREICH_NAMEN.get(bereich_key, bereich_key)
    marge = bereich_data.get('marge', 0)
    
    # Heute-Daten (immer anzeigen, auch wenn 0)
    heute_umsatz = bereich_data.get('heute_umsatz', 0)
    heute_db1 = bereich_data.get('heute_db1', 0)
    
    # Stück (nur bei NW/GW)
    stueck = bereich_data.get('stueck', 0)
    stueck_display = f" | Stück (Monat): {stueck}" if stueck > 0 else ""
    db1_pro_stueck = bereich_data.get('db1_pro_stueck', 0)
    db1_stk_display = f" | DB1/Stk: {format_euro(db1_pro_stueck)}" if db1_pro_stueck > 0 else ""

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px;">
        <h2 style="color: #0066cc; margin-bottom: 5px;">TEK {bereich_name}</h2>
        <p style="color: #666; margin-top: 0;">{data['monat']} | Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr</p>

        <!-- Haupt-KPIs -->
        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <tr style="background: #0066cc; color: white;">
                <th style="padding: 15px; text-align: center;">DB1</th>
                <th style="padding: 15px; text-align: center;">Marge</th>
            </tr>
            <tr style="background: #f5f5f5;">
                <td style="padding: 15px; text-align: center; font-size: 24px; font-weight: bold;">{format_euro(bereich_data['db1'])} EUR</td>
                <td style="padding: 15px; text-align: center; font-size: 24px; font-weight: bold;">{marge:.1f}%</td>
            </tr>
        </table>

        <!-- Heute-Daten -->
        <h3 style="color: #333; margin-top: 25px; font-size: 16px;">📅 Heute</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr>
                <td style="padding: 8px; background: #f0f0f0;">Erlöse:</td>
                <td style="padding: 8px; text-align: right; font-weight: bold;">{format_euro(heute_umsatz)} EUR</td>
            </tr>
            <tr>
                <td style="padding: 8px; background: #f0f0f0;">DB1:</td>
                <td style="padding: 8px; text-align: right; font-weight: bold;">{format_euro(heute_db1)} EUR</td>
            </tr>
        </table>

        <!-- Monat-Daten -->
        <h3 style="color: #333; margin-top: 25px; font-size: 16px;">📊 Monat kumuliert</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr>
                <td style="padding: 8px; background: #f0f0f0;">Umsatz:</td>
                <td style="padding: 8px; text-align: right; font-weight: bold;">{format_euro(bereich_data['umsatz'])} EUR</td>
            </tr>
            <tr>
                <td style="padding: 8px; background: #f0f0f0;">Einsatz:</td>
                <td style="padding: 8px; text-align: right;">{format_euro(bereich_data['einsatz'])} EUR</td>
            </tr>
            <tr>
                <td style="padding: 8px; background: #f0f0f0;">DB1:</td>
                <td style="padding: 8px; text-align: right; font-weight: bold;">{format_euro(bereich_data['db1'])} EUR</td>
            </tr>
            {f'<tr><td style="padding: 8px; background: #f0f0f0;">DB1/Stück:</td><td style="padding: 8px; text-align: right;">{format_euro(db1_pro_stueck)} EUR</td></tr>' if db1_pro_stueck > 0 else ''}
            {f'<tr><td style="padding: 8px; background: #f0f0f0;">Stück:</td><td style="padding: 8px; text-align: right;">{stueck}</td></tr>' if stueck > 0 else ''}
        </table>

        <p style="margin-top: 20px;">Details im PDF-Anhang.</p>

        <p style="color: #999; font-size: 11px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
            Automatisch generiert von DRIVE<br>
            <a href="http://drive.auto-greiner.de/controlling/tek" style="color: #0066cc;">In DRIVE öffnen</a>
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
