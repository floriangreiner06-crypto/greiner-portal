"""
Controlling API - BWA und weitere Controlling-Funktionen
=========================================================
Erstellt: 2025-12-02
Version: 1.2 - 8932xx aus indirekten Kosten ausgeschlossen (Doppelzählung Fix)
"""

from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime

controlling_api = Blueprint('controlling_api', __name__)

# =============================================================================
# SKR51-Kontobezeichnungen (Autohaus-Kontenrahmen)
# =============================================================================
SKR51_KONTOBEZEICHNUNGEN = {
    # Umsatz Neuwagen (81xxxx)
    810111: 'NW VE Privatkunde bar/überw.',
    810151: 'NW VE Privatkunde Leasing',
    810211: 'NW VE Privatkunde Finanzierung',
    810311: 'NW VE Gewerbekunde bar/überw.',
    810351: 'NW VE Gewerbekunde Leasing',
    810411: 'NW VE Gewerbekunde Finanzierung',
    810511: 'NW VE Großkunde bar/überw.',
    810551: 'NW VE Großkunde Leasing',
    810611: 'NW VE Großkunde Finanzierung',
    810811: 'NW VE an Händler',
    810831: 'NW VE Gewerbekunde Leasing',
    810911: 'NW VE Sonstige',
    811111: 'NW Herstellerprämien',
    811211: 'NW Bonusprämien',
    813211: 'NW Sonderprämien/Boni',
    817001: 'NW Innenumsatz',
    817051: 'NW Kostenumlage intern',
    
    # Umsatz Gebrauchtwagen (82xxxx)
    820111: 'GW VE Privatkunde bar/überw.',
    820151: 'GW VE Privatkunde Leasing',
    820211: 'GW VE Privatkunde Finanzierung',
    820311: 'GW VE Gewerbekunde bar/überw.',
    820351: 'GW VE Gewerbekunde Leasing',
    820411: 'GW VE Gewerbekunde Finanzierung',
    820511: 'GW VE an Händler',
    820611: 'GW VE Sonstige',
    821111: 'GW Prämien/Boni',
    827001: 'GW Innenumsatz',
    827051: 'GW Kostenumlage intern',
    
    # Umsatz Teile/Zubehör (83xxxx)
    830111: 'Teile VE Werkstatt extern',
    830211: 'Teile VE Thekenverkauf',
    830311: 'Teile VE an Händler',
    830411: 'Teile VE Zubehör',
    830511: 'Teile VE Sonstige',
    837001: 'Teile Innenumsatz',
    
    # Umsatz Lohn/Werkstatt (84xxxx)
    840111: 'Lohn VE Kundendienst',
    840211: 'Lohn VE Reparatur',
    840311: 'Lohn VE Garantie',
    840411: 'Lohn VE Interne Arbeiten',
    840511: 'Lohn VE Karosserie',
    840611: 'Lohn VE Lackierung',
    847001: 'Lohn Innenumsatz',
    
    # Sonstige Umsatz (86xxxx)
    860111: 'Mietwagen Erlöse',
    860211: 'Versicherungsprovision',
    860311: 'Finanzierungsprovision',
    860411: 'Leasingprovision',
    860511: 'Sonstige Provisionen',
    860611: 'Sonstige Erlöse',
    
    # Einsatz Neuwagen (71xxxx)
    710111: 'NW EK Privatkunde',
    710151: 'NW EK Leasing',
    710211: 'NW EK Finanzierung',
    710311: 'NW EK Gewerbekunde',
    710351: 'NW EK Gewerbe Leasing',
    710411: 'NW EK Gewerbe Finanzierung',
    710511: 'NW EK Großkunde',
    710811: 'NW EK an Händler',
    710831: 'NW EK Gewerbe Leasing',
    710911: 'NW EK Sonstige',
    710101: 'NW Wareneinsatz',
    717501: 'NW Zulassung/Überführung',
    717001: 'NW Innenumsatz EK',
    
    # Einsatz Gebrauchtwagen (72xxxx)
    720111: 'GW EK Privatkunde',
    720151: 'GW EK Leasing',
    720211: 'GW EK Finanzierung',
    720311: 'GW EK Gewerbekunde',
    720411: 'GW EK an Händler',
    720511: 'GW EK Sonstige',
    720101: 'GW Wareneinsatz',
    727001: 'GW Innenumsatz EK',
    727501: 'GW Zulassung/Überführung',
    
    # Einsatz Teile (73xxxx)
    730111: 'Teile EK Werkstatt',
    730211: 'Teile EK Theke',
    730311: 'Teile EK Händler',
    730411: 'Teile EK Zubehör',
    730101: 'Teile Wareneinsatz',
    737001: 'Teile Innenumsatz EK',
    
    # Einsatz Lohn (74xxxx)
    740111: 'Lohn EK Kundendienst',
    740211: 'Lohn EK Reparatur',
    740311: 'Lohn EK Garantie',
    740411: 'Lohn EK Intern',
    740101: 'Lohn Einsatz',
    747001: 'Lohn Innenumsatz EK',
    
    # Sonstiger Einsatz (76xxxx)
    760111: 'Mietwagen Einsatz',
    760211: 'Sonstiger Einsatz',
    
    # Kosten (4xxxxx) - wichtigste
    410001: 'Gehälter Verwaltung',
    410011: 'Gehälter Verkauf NW',
    410021: 'Gehälter Verkauf GW',
    410031: 'Gehälter Service',
    410061: 'Gehälter Teile',
    420001: 'Sozialabgaben Verwaltung',
    420011: 'Sozialabgaben Verkauf NW',
    420021: 'Sozialabgaben Verkauf GW',
    420031: 'Sozialabgaben Service',
    420061: 'Sozialabgaben Teile',
    440001: 'AfA Gebäude',
    440011: 'AfA Maschinen',
    440021: 'AfA Fahrzeuge',
    440031: 'AfA BGA',
    450011: 'Kfz-Kosten Verkauf NW',
    450021: 'Kfz-Kosten Verkauf GW',
    450031: 'Kfz-Kosten Service',
    460001: 'Energie/Heizung',
    460011: 'Strom',
    470001: 'Reparaturen Gebäude',
    470011: 'Reparaturen Maschinen',
    480001: 'Miete/Leasing',
    480011: 'Versicherungen',
    480021: 'Telefon/Internet',
    480031: 'Büromaterial',
    490001: 'Provisionen',
    491011: 'Provision NW Verkauf',
    491021: 'Provision GW Verkauf',
}


def get_konto_bezeichnung(konto: int, posting_text: str = None) -> str:
    """
    Holt Kontobezeichnung: Erst SKR51-Mapping, dann posting_text, dann Generic
    """
    # 1. SKR51 Mapping
    if konto in SKR51_KONTOBEZEICHNUNGEN:
        return SKR51_KONTOBEZEICHNUNGEN[konto]
    
    # 2. posting_text falls sinnvoll
    if posting_text and posting_text.strip() and not posting_text.startswith('Konto '):
        return posting_text[:50]
    
    # 3. Generische Bezeichnung basierend auf Kontonummer
    prefix = str(konto)[:2]
    gruppen_namen = {
        '81': 'Erlöse Neuwagen', '82': 'Erlöse Gebrauchtwagen',
        '83': 'Erlöse Teile', '84': 'Erlöse Lohn',
        '85': 'Erlöse Lack', '86': 'Sonstige Erlöse',
        '71': 'Einsatz Neuwagen', '72': 'Einsatz Gebrauchtwagen',
        '73': 'Einsatz Teile', '74': 'Einsatz Lohn',
        '41': 'Personalkosten', '42': 'Sozialabgaben',
        '43': 'Sonst. Personalkosten', '44': 'Abschreibungen',
        '45': 'Fahrzeugkosten', '46': 'Material/Energie',
        '47': 'Reparaturen', '48': 'Sonstige Kosten',
        '49': 'Provisionen/Umlagen',
    }
    gruppe = gruppen_namen.get(prefix, '')
    return f"{gruppe} ({konto})" if gruppe else f"Konto {konto}"

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

MONAT_NAMEN = {
    1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
    5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
    9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def build_firma_standort_filter(firma: str, standort: str):
    """
    Baut Firma/Standort-Filter für BWA-Queries.
    
    WICHTIG: Für Umsatz/Einsatz (7/8xxxxx) gilt branch_number
             Für Kosten (4xxxxx) gilt die letzte Ziffer der Kontonummer!
             - Letzte Ziffer 1 = Deggendorf
             - Letzte Ziffer 2 = Landau
             - subsidiary_to_company_ref 2 = Hyundai (separate Firma)
    
    Returns:
        tuple: (firma_filter_umsatz, firma_filter_kosten, standort_name)
    """
    firma_filter_umsatz = ""
    firma_filter_kosten = ""
    standort_name = "Alle"
    
    if firma == '1':
        # Stellantis (Autohaus Greiner)
        firma_filter_umsatz = "AND subsidiary_to_company_ref = 1"
        firma_filter_kosten = "AND subsidiary_to_company_ref = 1"
        standort_name = "Stellantis (DEG+LAN)"
        if standort == '1':
            # Deggendorf: branch_number=1 für Umsatz, letzte Ziffer=1 für Kosten
            firma_filter_umsatz += " AND branch_number = 1"
            firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
            standort_name = "Deggendorf"
        elif standort == '2':
            # Landau: branch_number=3 für Umsatz, letzte Ziffer=2 für Kosten
            firma_filter_umsatz += " AND branch_number = 3"
            firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
            standort_name = "Landau"
    elif firma == '2':
        # Hyundai (Auto Greiner) - separate Firma
        firma_filter_umsatz = "AND subsidiary_to_company_ref = 2"
        firma_filter_kosten = "AND subsidiary_to_company_ref = 2"
        standort_name = "Hyundai"
    
    return firma_filter_umsatz, firma_filter_kosten, standort_name


@controlling_api.route('/api/controlling/bwa', methods=['GET'])
def get_bwa():
    """
    BWA-Daten für einen Monat abrufen.
    
    Query-Parameter:
        monat: int (1-12)
        jahr: int (z.B. 2025)
        firma: 0=Alle, 1=Stellantis, 2=Hyundai
        standort: 0=Alle, 1=Deggendorf, 2=Landau (nur bei Firma 1)
    
    Returns:
        JSON mit allen BWA-Positionen
    """
    try:
        monat = request.args.get('monat', type=int)
        jahr = request.args.get('jahr', type=int)
        firma = request.args.get('firma', '0')
        standort = request.args.get('standort', '0')
        
        if not monat or not jahr:
            heute = datetime.now()
            monat = monat or heute.month
            jahr = jahr or heute.year
        
        # Bei Filter immer live berechnen
        if firma != '0' or standort != '0':
            return berechne_bwa_live(monat, jahr, firma, standort)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Prüfen ob Daten existieren (nur für Gesamtansicht)
        cursor.execute("""
            SELECT position, betrag 
            FROM bwa_monatswerte 
            WHERE jahr = ? AND monat = ?
        """, (jahr, monat))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            # Keine gespeicherten Daten - live berechnen
            return berechne_bwa_live(monat, jahr, firma, standort)
        
        # Daten aus DB
        data = {
            'monat': monat,
            'monat_name': MONAT_NAMEN.get(monat, str(monat)),
            'jahr': jahr
        }
        
        for row in rows:
            data[row['position']] = row['betrag']
        
        return jsonify({
            'status': 'ok',
            'data': data,
            'source': 'database'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


def berechne_bwa_live(monat: int, jahr: int, firma: str = '0', standort: str = '0'):
    """
    BWA live aus loco_journal_accountings berechnen.
    
    Parameter:
        monat, jahr: Zeitraum
        firma: 0=Alle, 1=Stellantis, 2=Hyundai
        standort: 0=Alle, 1=Deggendorf, 2=Landau
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        datum_von = f"{jahr}-{monat:02d}-01"
        if monat == 12:
            datum_bis = f"{jahr+1}-01-01"
        else:
            datum_bis = f"{jahr}-{monat+1:02d}-01"
        
        # Filter bauen
        firma_filter_umsatz, firma_filter_kosten, standort_name = build_firma_standort_filter(firma, standort)
        
        # Umsatz (verwendet firma_filter_umsatz)
        cursor.execute(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
            )/100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
              {firma_filter_umsatz}
        """, (datum_von, datum_bis))
        umsatz = cursor.fetchone()[0] or 0
        
        # Einsatz (verwendet firma_filter_umsatz)
        cursor.execute(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 700000 AND 799999
              {firma_filter_umsatz}
        """, (datum_von, datum_bis))
        einsatz = cursor.fetchone()[0] or 0
        
        # Variable Kosten (verwendet firma_filter_kosten)
        cursor.execute(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND (
                nominal_account_number BETWEEN 415100 AND 415199
                OR nominal_account_number BETWEEN 435500 AND 435599
                OR (nominal_account_number BETWEEN 455000 AND 456999 
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                OR (nominal_account_number BETWEEN 487000 AND 487099 
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                OR nominal_account_number BETWEEN 491000 AND 497899
              )
              {firma_filter_kosten}
        """, (datum_von, datum_bis))
        variable = cursor.fetchone()[0] or 0
        
        # Direkte Kosten (verwendet firma_filter_kosten)
        cursor.execute(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 400000 AND 489999
              AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
              AND NOT (
                nominal_account_number BETWEEN 415100 AND 415199
                OR nominal_account_number BETWEEN 424000 AND 424999
                OR nominal_account_number BETWEEN 435500 AND 435599
                OR nominal_account_number BETWEEN 438000 AND 438999
                OR nominal_account_number BETWEEN 455000 AND 456999
                OR nominal_account_number BETWEEN 487000 AND 487099
                OR nominal_account_number BETWEEN 491000 AND 497999
              )
              {firma_filter_kosten}
        """, (datum_von, datum_bis))
        direkte = cursor.fetchone()[0] or 0
        
        # Indirekte Kosten (verwendet firma_filter_kosten, OHNE 8932xx - das ist Umsatz!)
        cursor.execute(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND (
                (nominal_account_number BETWEEN 400000 AND 499999 
                 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
                OR (nominal_account_number BETWEEN 424000 AND 424999 
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                OR (nominal_account_number BETWEEN 438000 AND 438999 
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                OR nominal_account_number BETWEEN 498000 AND 499999
                OR (nominal_account_number BETWEEN 891000 AND 896999
                    AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
              )
              {firma_filter_kosten}
        """, (datum_von, datum_bis))
        indirekte = cursor.fetchone()[0] or 0
        
        # Neutrales Ergebnis (20-29xxxx inkl. kalk. Kosten/Rückstellungen, firma_filter_umsatz)
        cursor.execute(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
            )/100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 200000 AND 299999
              {firma_filter_umsatz}
        """, (datum_von, datum_bis))
        neutral = cursor.fetchone()[0] or 0
        
        conn.close()
        
        # Berechnungen
        db1 = umsatz - einsatz
        db2 = db1 - variable
        db3 = db2 - direkte
        be = db3 - indirekte
        ue = be + neutral
        
        data = {
            'monat': monat,
            'monat_name': MONAT_NAMEN.get(monat, str(monat)),
            'jahr': jahr,
            'firma': firma,
            'standort': standort,
            'standort_name': standort_name,
            'umsatz': round(umsatz, 2),
            'einsatz': round(einsatz, 2),
            'db1': round(db1, 2),
            'variable': round(variable, 2),
            'db2': round(db2, 2),
            'direkte': round(direkte, 2),
            'db3': round(db3, 2),
            'indirekte': round(indirekte, 2),
            'betriebsergebnis': round(be, 2),
            'neutral': round(neutral, 2),
            'unternehmensergebnis': round(ue, 2)
        }
        
        return jsonify({
            'status': 'ok',
            'data': data,
            'source': 'live',
            'filter': {
                'firma': firma,
                'standort': standort,
                'standort_name': standort_name
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@controlling_api.route('/api/controlling/bwa/health', methods=['GET'])
def bwa_health():
    """Health-Check für BWA-API."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM bwa_monatswerte")
        count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'module': 'bwa',
            'records': count,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@controlling_api.route('/api/controlling/bwa/detail', methods=['GET'])
def get_bwa_detail():
    """
    BWA Drill-Down - Kontendetails für eine Position.
    
    Query-Parameter:
        position: str ('umsatz', 'einsatz', 'variable', 'direkte', 'indirekte', 'neutral')
        monat: int (1-12)
        jahr: int (z.B. 2025)
        firma: 0=Alle, 1=Stellantis, 2=Hyundai
        standort: 0=Alle, 1=Deggendorf, 2=Landau (nur bei Firma 1)
        ebene: 'gruppen' (Standard), 'konten', oder 'buchungen'
        gruppe: str (optional, z.B. '81' für Konten-Detail einer Gruppe)
        konto: int (optional, für Buchungs-Details)
    """
    try:
        position = request.args.get('position', 'umsatz')
        monat = request.args.get('monat', type=int)
        jahr = request.args.get('jahr', type=int)
        firma = request.args.get('firma', '0')
        standort = request.args.get('standort', '0')
        ebene = request.args.get('ebene', 'gruppen')  # 'gruppen', 'konten', 'buchungen'
        gruppe = request.args.get('gruppe', '')  # z.B. '81', '8101'
        konto = request.args.get('konto', type=int)
        
        if not monat or not jahr:
            heute = datetime.now()
            monat = monat or heute.month
            jahr = jahr or heute.year
        
        datum_von = f"{jahr}-{monat:02d}-01"
        if monat == 12:
            datum_bis = f"{jahr+1}-01-01"
        else:
            datum_bis = f"{jahr}-{monat+1:02d}-01"
        
        # Filter bauen
        firma_filter_umsatz, firma_filter_kosten, standort_name = build_firma_standort_filter(firma, standort)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Position -> SQL-Filter Mapping
        # 'filter_type': 'umsatz' = nutzt firma_filter_umsatz, 'kosten' = nutzt firma_filter_kosten
        position_filter = {
            'umsatz': {
                'where': """((nominal_account_number BETWEEN 800000 AND 889999)
                            OR (nominal_account_number BETWEEN 893200 AND 893299))""",
                'vorzeichen': "CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END",
                'filter_type': 'umsatz'
            },
            'einsatz': {
                'where': "nominal_account_number BETWEEN 700000 AND 799999",
                'vorzeichen': "CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END",
                'filter_type': 'umsatz'
            },
            'variable': {
                'where': """(
                    nominal_account_number BETWEEN 415100 AND 415199
                    OR nominal_account_number BETWEEN 435500 AND 435599
                    OR (nominal_account_number BETWEEN 455000 AND 456999 
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                    OR (nominal_account_number BETWEEN 487000 AND 487099 
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                    OR nominal_account_number BETWEEN 491000 AND 497899
                )""",
                'vorzeichen': "CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END",
                'filter_type': 'kosten'
            },
            'direkte': {
                'where': """(
                    nominal_account_number BETWEEN 400000 AND 489999
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
                    AND NOT (
                        nominal_account_number BETWEEN 415100 AND 415199
                        OR nominal_account_number BETWEEN 424000 AND 424999
                        OR nominal_account_number BETWEEN 435500 AND 435599
                        OR nominal_account_number BETWEEN 438000 AND 438999
                        OR nominal_account_number BETWEEN 455000 AND 456999
                        OR nominal_account_number BETWEEN 487000 AND 487099
                        OR nominal_account_number BETWEEN 491000 AND 497999
                    )
                )""",
                'vorzeichen': "CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END",
                'filter_type': 'kosten'
            },
            'indirekte': {
                'where': """(
                    (nominal_account_number BETWEEN 400000 AND 499999 
                     AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
                    OR (nominal_account_number BETWEEN 424000 AND 424999 
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                    OR (nominal_account_number BETWEEN 438000 AND 438999 
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                    OR nominal_account_number BETWEEN 498000 AND 499999
                    OR (nominal_account_number BETWEEN 891000 AND 896999
                        AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
                )""",
                'vorzeichen': "CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END",
                'filter_type': 'kosten'
            },
            'neutral': {
                'where': "nominal_account_number BETWEEN 200000 AND 299999",
                'vorzeichen': "CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END",
                'filter_type': 'umsatz'
            }
        }
        
        # Gruppen-Bezeichnungen (SKR51)
        gruppen_namen = {
            # Umsatz
            '81': 'Erlöse Neuwagen', '82': 'Erlöse Gebrauchtwagen', 
            '83': 'Erlöse Teile', '84': 'Erlöse Lohn',
            '85': 'Erlöse Lack', '86': 'Sonstige Erlöse', '88': 'Erlöse Vermietung',
            '89': 'Sonstige betriebliche Erträge',
            # Einsatz
            '71': 'Einsatz Neuwagen', '72': 'Einsatz Gebrauchtwagen',
            '73': 'Einsatz Teile', '74': 'Einsatz Lohn',
            '75': 'Einsatz Lack', '76': 'Sonstiger Einsatz', '78': 'Einsatz Vermietung',
            # Kosten
            '41': 'Personalkosten', '42': 'Sozialabgaben', '43': 'Sonst. Personalkosten',
            '44': 'Abschreibungen', '45': 'Fahrzeugkosten', '46': 'Material/Energie',
            '47': 'Reparaturen', '48': 'Sonstige Kosten', '49': 'Provisionen/Umlagen',
            # Neutral
            '20': 'Zinsen', '21': 'Zinserträge', '22': 'Sonstige Finanzen',
            '23': 'AO Erträge', '24': 'AO Aufwendungen', '25': 'Steuern',
        }
        
        if position not in position_filter:
            return jsonify({'status': 'error', 'message': f'Unbekannte Position: {position}'}), 400
        
        pf = position_filter[position]
        
        # Den richtigen Firma-Filter basierend auf Position wählen
        if pf['filter_type'] == 'kosten':
            aktiver_filter = firma_filter_kosten
        else:
            aktiver_filter = firma_filter_umsatz
        
        # =====================================================================
        # EBENE: BUCHUNGEN (Detail für ein Konto)
        # =====================================================================
        if ebene == 'buchungen' and konto:
            cursor.execute(f"""
                SELECT 
                    accounting_date as datum,
                    document_number as beleg_nr,
                    COALESCE(NULLIF(posting_text, ''), NULLIF(free_form_accounting_text, ''), NULLIF(contra_account_text, ''), '-') as buchungstext,
                    {pf['vorzeichen']} / 100.0 as betrag,
                    debit_or_credit as soll_haben,
                    vehicle_reference as fahrzeug,
                    customer_number as kunden_nr,
                    invoice_number as rechnung_nr
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number = ?
                  {aktiver_filter}
                ORDER BY accounting_date, document_number
            """, (datum_von, datum_bis, konto))
            
            buchungen = cursor.fetchall()
            conn.close()
            
            return jsonify({
                'status': 'ok',
                'ebene': 'buchungen',
                'position': position,
                'konto': konto,
                'buchungen': [{
                    'datum': row['datum'],
                    'beleg_nr': row['beleg_nr'],
                    'buchungstext': row['buchungstext'],
                    'betrag': round(row['betrag'], 2),
                    'soll_haben': row['soll_haben'],
                    'fahrzeug': row['fahrzeug'] or '',
                    'kunden_nr': row['kunden_nr'] or '',
                    'rechnung_nr': row['rechnung_nr'] or ''
                } for row in buchungen],
                'anzahl': len(buchungen)
            })
        
        # =====================================================================
        # EBENE: KONTEN (Detail für eine Gruppe, z.B. '81' oder '8101')
        # =====================================================================
        if ebene == 'konten' and gruppe:
            gruppe_len = len(gruppe)
            
            # Filter für die Gruppe
            if gruppe_len == 2:
                konto_filter = f"substr(CAST(nominal_account_number AS TEXT), 1, 2) = '{gruppe}'"
            elif gruppe_len == 4:
                konto_filter = f"substr(CAST(nominal_account_number AS TEXT), 1, 4) = '{gruppe}'"
            else:
                konto_filter = f"CAST(nominal_account_number AS TEXT) LIKE '{gruppe}%'"
            
            cursor.execute(f"""
                SELECT 
                    nominal_account_number as konto,
                    MIN(posting_text) as bezeichnung,
                    SUM({pf['vorzeichen']}) / 100.0 as betrag,
                    COUNT(*) as buchungen_anzahl
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND {pf['where']}
                  AND {konto_filter}
                  {aktiver_filter}
                GROUP BY nominal_account_number
                HAVING betrag != 0
                ORDER BY ABS(betrag) DESC
            """, (datum_von, datum_bis))
            
            konten = cursor.fetchall()
            conn.close()
            
            summe = sum(row['betrag'] for row in konten)
            gruppe_name = gruppen_namen.get(gruppe[:2], f'Gruppe {gruppe}')
            
            return jsonify({
                'status': 'ok',
                'ebene': 'konten',
                'position': position,
                'gruppe': gruppe,
                'gruppe_name': gruppe_name,
                'filter': {
                    'monat': monat,
                    'monat_name': MONAT_NAMEN.get(monat, str(monat)),
                    'jahr': jahr
                },
                'konten': [{
                    'konto': row['konto'],
                    'bezeichnung': get_konto_bezeichnung(row['konto'], row['bezeichnung']),
                    'betrag': round(row['betrag'], 2),
                    'buchungen_anzahl': row['buchungen_anzahl']
                } for row in konten],
                'summe': round(summe, 2),
                'anzahl_konten': len(konten)
            })
        
        # =====================================================================
        # EBENE: GRUPPEN (Zusammenfassung nach 2-stelligem Präfix)
        # =====================================================================
        cursor.execute(f"""
            SELECT 
                substr(CAST(nominal_account_number AS TEXT), 1, 2) as gruppe,
                SUM({pf['vorzeichen']}) / 100.0 as betrag,
                COUNT(DISTINCT nominal_account_number) as anzahl_konten,
                COUNT(*) as buchungen_anzahl
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND {pf['where']}
              {aktiver_filter}
            GROUP BY gruppe
            HAVING betrag != 0
            ORDER BY ABS(betrag) DESC
        """, (datum_von, datum_bis))
        
        gruppen_rows = cursor.fetchall()
        conn.close()
        
        summe = sum(row['betrag'] for row in gruppen_rows)
        
        gruppen = []
        for row in gruppen_rows:
            g = row['gruppe']
            gruppen.append({
                'gruppe': g,
                'name': gruppen_namen.get(g, f'Gruppe {g}'),
                'betrag': round(row['betrag'], 2),
                'anzahl_konten': row['anzahl_konten'],
                'buchungen_anzahl': row['buchungen_anzahl']
            })
        
        return jsonify({
            'status': 'ok',
            'ebene': 'gruppen',
            'position': position,
            'filter': {
                'monat': monat,
                'monat_name': MONAT_NAMEN.get(monat, str(monat)),
                'jahr': jahr,
                'datum_von': datum_von,
                'datum_bis': datum_bis,
                'firma': firma,
                'standort': standort,
                'standort_name': standort_name
            },
            'gruppen': gruppen,
            'summe': round(summe, 2),
            'anzahl_gruppen': len(gruppen)
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500
