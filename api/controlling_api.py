"""
Controlling API - BWA und weitere Controlling-Funktionen
=========================================================
Erstellt: 2025-12-02
Version: 1.2 - 8932xx aus indirekten Kosten ausgeschlossen (Doppelzählung Fix)
Updated: TAG 117 - Migration auf db_session
"""

from flask import Blueprint, jsonify, request
from datetime import datetime

# Zentrale DB-Utilities (TAG117 + TAG136 + TAG179)
from api.db_utils import db_session, row_to_dict, rows_to_list, locosoft_session, get_guv_filter
from api.db_connection import convert_placeholders, sql_placeholder

controlling_api = Blueprint('controlling_api', __name__)

# =============================================================================
# KONTEN-RANGES (TAG 179: Zentrale Definitionen)
# =============================================================================

# Konten-Bereiche für BWA-Berechnungen
KONTO_RANGES = {
    'umsatz': (800000, 889999),
    'umsatz_sonder': (893200, 893299),  # Sonderumsatz (z.B. 8932xx)
    'einsatz': (700000, 799999),
    'kosten': (400000, 499999),
    'neutral': (200000, 299999),  # Neutrales Ergebnis
}

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


def get_konto_bezeichnung(conn, konto: int, subsidiary: int = 1) -> str:
    """
    Holt Kontobezeichnung aus loco_nominal_accounts (Locosoft Stammdaten).

    Parameter:
    - conn: Datenbankverbindung
    - konto: Kontonummer (z.B. 830001)
    - subsidiary: 1=Stellantis, 2=Hyundai (Standard: 1)

    Rückgabe: Erlösart z.B. "VE GM OT an Kunde Mechanik"
    """
    cursor = conn.cursor()

    # 1. Aus Locosoft Konten-Stammdaten (exakte Firma)
    cursor.execute(convert_placeholders("""
        SELECT account_description
        FROM loco_nominal_accounts
        WHERE nominal_account_number = %s
          AND subsidiary_to_company_ref = %s
        LIMIT 1
    """), (konto, subsidiary))
    result = cursor.fetchone()

    if result and result['account_description']:
        return result['account_description']

    # 2. Fallback: Andere Subsidiary probieren
    cursor.execute(convert_placeholders("""
        SELECT account_description
        FROM loco_nominal_accounts
        WHERE nominal_account_number = %s
        LIMIT 1
    """), (konto,))
    result = cursor.fetchone()

    if result and result['account_description']:
        return result['account_description']

    # 3. Fallback: Generische Bezeichnung
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

MONAT_NAMEN = {
    1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
    5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
    9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
}


def build_firma_standort_filter(firma: str, standort: str):
    """
    Baut Firma/Standort-Filter für BWA-Queries.

    TAG157: WICHTIG - Unterschiedliche Zuordnungslogik!
    - Umsatz (8xxxxx): via branch_number (1=DEG, 3=LAN)
    - Einsatz (7xxxxx): via Konto-Endziffer (6. Ziffer: 1=DEG, 2=LAN)
    - Kosten (4xxxxx): via branch_number (1=DEG, 3=LAN) - NICHT über 6. Ziffer!
    - subsidiary_to_company_ref 2 = Hyundai (separate Firma)

    TAG167: Neuer Filter "deg-both" für Deggendorf (Stellantis+Hyundai)
    TAG171: Fix - Wenn firma='0' (Alle) und standort='2' (Landau), automatisch Stellantis filtern

    Returns:
        tuple: (firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, standort_name)
    """
    firma_filter_umsatz = ""
    firma_filter_einsatz = ""  # TAG157: Separater Filter für Einsatz!
    firma_filter_kosten = ""
    standort_name = "Alle"

    # TAG182: Fix - Gesamtsumme (firma=0, standort=0) sollte Summe der drei Einzelbetriebe sein
    # Deggendorf (Stellantis + Hyundai) + Landau (Stellantis) + Hyundai (separat)
    # = (branch=1 AND subsidiary=1) OR (branch=2 AND subsidiary=2) OR (branch=3 AND subsidiary=1)
    if firma == '0' and standort == '0':
        # Gesamtsumme: Alle drei Betriebe kombinieren
        # Umsatz: Deggendorf (branch=1, subsidiary=1) + Hyundai (branch=2, subsidiary=2) + Landau (branch=3, subsidiary=1)
        firma_filter_umsatz = "AND ((branch_number = 1 AND subsidiary_to_company_ref = 1) OR (branch_number = 2 AND subsidiary_to_company_ref = 2) OR (branch_number = 3 AND subsidiary_to_company_ref = 1))"
        # Einsatz: Deggendorf (6. Ziffer='1', subsidiary=1) + Hyundai (6. Ziffer='1', subsidiary=2) + Landau (branch=3, subsidiary=1)
        # TAG182: Fix - 74xxxx Konten mit 6. Ziffer='2' und branch=1 gehören zu Deggendorf, müssen eingeschlossen werden!
        # Deggendorf: (6. Ziffer='1' OR (74xxxx AND branch=1)) AND subsidiary=1 AND branch != 3 (um Doppelzählung mit Landau zu vermeiden)
        # Landau: branch=3 AND subsidiary=1
        # Hyundai: 6. Ziffer='1' AND subsidiary=2
        firma_filter_einsatz = """AND (
            ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
            OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
            OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
        )"""
        # Kosten: Deggendorf (6. Ziffer='1', subsidiary=1) + Hyundai (6. Ziffer='1', subsidiary=2) + Landau (6. Ziffer='2', subsidiary=1)
        # TAG182: Landau Kosten verwenden 6. Ziffer='2', nicht branch_number=3!
        firma_filter_kosten = "AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1))"
        standort_name = "Gesamtsumme (Deggendorf + Landau + Hyundai)"
    # TAG171: Fix - Wenn "Alle Firmen" aber spezifischer Standort, automatisch Firma setzen
    # Landau gehört zu Stellantis, also wenn standort='2' oder standort='3' und firma='0', dann firma='1' verwenden
    elif firma == '0' and (standort == '2' or standort == '3'):
        # Landau gehört zu Stellantis (standort='2' oder '3' für API-Kompatibilität)
        firma = '1'
        standort = '2'  # Normalisiere auf '2' für interne Logik
    elif firma == '0' and standort == '1':
        # Deggendorf hat sowohl Stellantis als auch Hyundai → deg-both verwenden
        standort = 'deg-both'

    # TAG167: Spezialfall: Deggendorf (Stellantis+Hyundai)
    if standort == 'deg-both':
        # Deggendorf: Stellantis (branch=1, subsidiary=1) + Hyundai (branch=2, subsidiary=2)
        # TAG171: Fix - Hyundai verwendet 6. Ziffer '1' (wie Stellantis), nicht '2'!
        # Für Einsatz/Kosten: Beide verwenden 6. Ziffer '1', daher: 6. Ziffer='1' AND subsidiary IN (1,2)
        firma_filter_umsatz = "AND ((branch_number = 1 AND subsidiary_to_company_ref = 1) OR (branch_number = 2 AND subsidiary_to_company_ref = 2))"
        firma_filter_einsatz = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)"
        firma_filter_kosten = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)"
        standort_name = "Deggendorf (Stellantis+Hyundai)"
    elif firma == '1':
        # Stellantis (Autohaus Greiner)
        firma_filter_umsatz = "AND subsidiary_to_company_ref = 1"
        firma_filter_einsatz = "AND subsidiary_to_company_ref = 1"
        firma_filter_kosten = "AND subsidiary_to_company_ref = 1"
        standort_name = "Stellantis (DEG+LAN)"
        if standort == '1':
            # Deggendorf: branch_number=1 für Umsatz, Konto-Endziffer=1 für Einsatz
            # TAG182: Fix - Kosten mit branch=1 aber 6. Ziffer='2' gehören zu Landau, nicht Deggendorf!
            # Problem: Kosten mit branch=1 UND 6. Ziffer='2' wurden doppelt gezählt
            # TAG182: Fix - Einsatz muss auch 74xxxx Konten mit branch=1 einschließen!
            # TAG182: Fix - Konten mit branch=3 müssen ausgeschlossen werden (gehören zu Landau)!
            firma_filter_umsatz += " AND branch_number = 1"
            firma_filter_einsatz += " AND (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND branch_number != 3"
            # Kosten: branch=1 UND 6. Ziffer='1' (nicht '2', die gehören zu Landau!)
            firma_filter_kosten += " AND branch_number = 1 AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
            standort_name = "Deggendorf"
        elif standort == '2':
            # Landau: branch_number=3 für Umsatz UND Einsatz (TAG182: HAR-Analyse zeigt Einsatz-Differenz!)
            # TAG182: Fix - Einsatz-Filter auf branch_number=3 geändert (wie Umsatz)
            # Problem: 6. Ziffer='2' Filter zeigt 15.180€ mehr als Cognos → branch_number=3 verwenden
            firma_filter_umsatz += " AND branch_number = 3"
            firma_filter_einsatz += " AND branch_number = 3"  # TAG182: Geändert von 6. Ziffer='2' zu branch_number=3
            # Kosten: branch_number=3 für ALLES (konsistent mit Umsatz/Einsatz)
            firma_filter_kosten += " AND branch_number = 3"
            standort_name = "Landau"
    elif firma == '2':
        # Hyundai (Auto Greiner) - separate Firma
        # TAG182: Hyundai hat branch_number=2 für Umsatz, 6. Ziffer='1' für Einsatz UND Kosten (wie Deggendorf Opel)
        # TAG182: Fix - Kosten-Filter auf 6. Ziffer='1' geändert (nicht branch_number=2)!
        firma_filter_umsatz = "AND branch_number = 2 AND subsidiary_to_company_ref = 2"
        firma_filter_einsatz = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2"
        firma_filter_kosten = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2"  # TAG182: Geändert von branch_number=2 zu 6. Ziffer='1'
        standort_name = "Hyundai"

    return firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, standort_name


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

        with db_session() as conn:
            cursor = conn.cursor()

            # Prüfen ob Daten existieren (nur für Gesamtansicht)
            cursor.execute(convert_placeholders("""
                SELECT position, betrag
                FROM bwa_monatswerte
                WHERE jahr = %s AND monat = %s
            """), (jahr, monat))

            rows = cursor.fetchall()

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

            # Vorjahr berechnen (auch bei DB-Daten)
            vorjahr_werte = _berechne_bwa_werte(cursor, monat, jahr - 1, firma, standort)

            # YTD (Jahr bis aktueller Monat) berechnen
            ytd_werte = _berechne_bwa_ytd(cursor, monat, jahr, firma, standort)
            ytd_vorjahr = _berechne_bwa_ytd(cursor, monat, jahr - 1, firma, standort)

            # Abweichungen berechnen
            abweichungen = {}
            for key in ['umsatz', 'db1', 'db2', 'db3', 'betriebsergebnis', 'unternehmensergebnis']:
                aktuell = data.get(key, 0)
                vj = vorjahr_werte.get(key, 0)
                if vj != 0:
                    abweichungen[key] = round((aktuell - vj) / abs(vj) * 100, 1)
                else:
                    abweichungen[key] = 0 if aktuell == 0 else 100.0

            # YTD Abweichungen
            ytd_abweichungen = {}
            for key in ['umsatz', 'db1', 'db2', 'db3', 'betriebsergebnis', 'unternehmensergebnis']:
                aktuell = ytd_werte.get(key, 0)
                vj = ytd_vorjahr.get(key, 0)
                if vj != 0:
                    ytd_abweichungen[key] = round((aktuell - vj) / abs(vj) * 100, 1)
                else:
                    ytd_abweichungen[key] = 0 if aktuell == 0 else 100.0

            return jsonify({
                'status': 'ok',
                'data': data,
                'vorjahr': vorjahr_werte,
                'abweichungen': abweichungen,
                'ytd': ytd_werte,
                'ytd_vorjahr': ytd_vorjahr,
                'ytd_abweichungen': ytd_abweichungen,
                'source': 'database'
            })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


def _berechne_bwa_werte(cursor, monat: int, jahr: int, firma: str = '0', standort: str = '0'):
    """
    Interne Funktion: BWA-Werte für einen Monat berechnen.

    Returns:
        dict mit allen BWA-Positionen oder None bei Fehler
    """
    datum_von = f"{jahr}-{monat:02d}-01"
    if monat == 12:
        datum_bis = f"{jahr+1}-01-01"
    else:
        datum_bis = f"{jahr}-{monat+1:02d}-01"

    # Filter bauen (TAG157: Jetzt mit separatem Einsatz-Filter!)
    firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, standort_name = build_firma_standort_filter(firma, standort)

    # WICHTIG: G&V-Abschlussbuchungen ausschließen (verfälschen BWA!)
    # TAG 179: Zentrale Funktion verwenden
    from api.db_utils import get_guv_filter
    guv_filter = get_guv_filter()

    # Umsatz
    # TAG 179: Konten-Ranges zentral verwenden
    umsatz_range = KONTO_RANGES['umsatz']
    umsatz_sonder_range = KONTO_RANGES['umsatz_sonder']
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND ((nominal_account_number BETWEEN {umsatz_range[0]} AND {umsatz_range[1]})
               OR (nominal_account_number BETWEEN {umsatz_sonder_range[0]} AND {umsatz_sonder_range[1]}))
          {firma_filter_umsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    umsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)

    # Einsatz (TAG157: firma_filter_einsatz für korrekte Standort-Zuordnung!)
    # TAG182: Landau verwendet jetzt branch_number=3 (nicht mehr 6. Ziffer='2')
    # TAG 179: Konten-Ranges zentral verwenden
    einsatz_range = KONTO_RANGES['einsatz']
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN {einsatz_range[0]} AND {einsatz_range[1]}
          {firma_filter_einsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    einsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)

    # Variable Kosten
    # TAG182: Landau - 6. Ziffer='2' für Kosten (nicht branch_number=3, da Kosten hauptsächlich branch=1 haben)!
    # TAG182: Hyundai - 8910xx AUSSCHLIESSEN (negativer Wert, reduziert Kosten fälschlicherweise)
    # TAG182: Deggendorf - Nur 6. Ziffer='1' verwenden (nicht branch=1 AND 6. Ziffer='1'), da es Variable Kosten mit branch=3 gibt!
    if standort == '2' and firma == '1':
        variable_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
        variable_8910xx_include = True  # Landau: 8910xx einschließen
    elif standort == '1' and firma == '1':
        # Deggendorf: Nur 6. Ziffer='1' verwenden (nicht branch=1 AND 6. Ziffer='1'), da es Variable Kosten mit branch=3 gibt!
        variable_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1"
        variable_8910xx_include = True  # Deggendorf: 8910xx einschließen
    elif firma == '2':
        # Hyundai: 8910xx AUSSCHLIESSEN (sollte nicht in Variablen Kosten sein)
        variable_kosten_filter = firma_filter_kosten
        variable_8910xx_include = False
    else:
        variable_kosten_filter = firma_filter_kosten
        variable_8910xx_include = True  # Stellantis/Alle: 8910xx einschließen
    
    # Variable Kosten Query - 8910xx bedingt einschließen
    variable_kosten_where = """
          AND (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR (nominal_account_number BETWEEN 455000 AND 456999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR (nominal_account_number BETWEEN 487000 AND 487099
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR nominal_account_number BETWEEN 491000 AND 497899"""
    
    if variable_8910xx_include:
        variable_kosten_where += """
            OR nominal_account_number BETWEEN 891000 AND 891099"""
    
    variable_kosten_where += """
          )"""
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          {variable_kosten_where}
          {variable_kosten_filter}
          {guv_filter}
    """), (datum_von, datum_bis))
    variable = float(row_to_dict(cursor.fetchone())['wert'] or 0)

    # Direkte Kosten
    # TAG182: Landau - 6. Ziffer='2' für Kosten (nicht branch_number=3, da Kosten hauptsächlich branch=1 haben)!
    if standort == '2' and firma == '1':
        direkte_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
    else:
        direkte_kosten_filter = firma_filter_kosten
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND NOT (
            nominal_account_number = 410021
            OR nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR nominal_account_number BETWEEN 489000 AND 489999
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
          {direkte_kosten_filter}
          {guv_filter}
    """), (datum_von, datum_bis))
    direkte = float(row_to_dict(cursor.fetchone())['wert'] or 0)

    # Indirekte Kosten
    # TAG182: Landau - 6. Ziffer='2' für Kosten (nicht branch_number=3, da Kosten hauptsächlich branch=1 haben)!
    if standort == '2' and firma == '1':
        indirekte_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
    else:
        indirekte_kosten_filter = firma_filter_kosten
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (
            (nominal_account_number BETWEEN 400000 AND 499999
             AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR (nominal_account_number BETWEEN 424000 AND 424999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR (nominal_account_number BETWEEN 438000 AND 438999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR nominal_account_number BETWEEN 498000 AND 499999
            OR (nominal_account_number BETWEEN 891000 AND 896999
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
                AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
          )
          {indirekte_kosten_filter}
          {guv_filter}
    """), (datum_von, datum_bis))
    indirekte = float(row_to_dict(cursor.fetchone())['wert'] or 0)

    # Neutrales Ergebnis
    # TAG 179: Konten-Ranges zentral verwenden
    neutral_range = KONTO_RANGES['neutral']
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN {neutral_range[0]} AND {neutral_range[1]}
          {firma_filter_umsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    neutral = float(row_to_dict(cursor.fetchone())['wert'] or 0)

    # Berechnungen
    db1 = umsatz - einsatz
    db2 = db1 - variable
    db3 = db2 - direkte
    be = db3 - indirekte
    ue = be + neutral

    return {
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


def _berechne_stueckzahlen_erweitert(monat: int, jahr: int, firma: str = '0', standort: str = '0'):
    """
    TAG 181: Berechnet NW und GW Stückzahlen in erweiterter Struktur.
    
    Erweiterte Struktur mit 4 Werten:
    - Monat (aktuelles Jahr, aktueller Monat)
    - Jahr (aktuelles Jahr, kumuliert vom WJ-Start)
    - VJ Monat (Vorjahr, gleicher Monat)
    - VJ Jahr (Vorjahr, kumuliert vom WJ-Start)
    
    NW: dealer_vehicle_type IN ('N', 'T', 'V')
    GW: dealer_vehicle_type IN ('G', 'D', 'L')
    
    Args:
        monat: int (1-12)
        jahr: int (z.B. 2025)
        firma: '0'=Alle, '1'=Stellantis, '2'=Hyundai
        standort: '0'=Alle, '1'=Deggendorf, '2'=Landau, 'deg-both'=Deggendorf konsolidiert
    
    Returns: {
        'nw': {'monat': int, 'jahr': int, 'vj_monat': int, 'vj_jahr': int},
        'gw': {'monat': int, 'jahr': int, 'vj_monat': int, 'vj_jahr': int}
    }
    """
    from datetime import datetime
    from api.standort_utils import build_locosoft_filter_verkauf
    
    # Standort-Parameter mappen (firma/standort → standort int)
    standort_int = 0
    nur_stellantis = False
    
    if standort == 'deg-both':
        # Deggendorf konsolidiert: beide Firmen
        standort_int = 1
        nur_stellantis = False
    elif standort == '1':
        # Deggendorf: abhängig von firma
        standort_int = 1
        nur_stellantis = (firma == '1')
    elif standort == '2':
        # Landau: immer Stellantis
        standort_int = 3
        nur_stellantis = True
    elif firma == '2':
        # Hyundai: Standort 2
        standort_int = 2
        nur_stellantis = False
    elif firma == '1':
        # Stellantis: Standort 1 (Deggendorf) oder 3 (Landau)
        if standort == '0':
            standort_int = 0  # Alle
        else:
            standort_int = 1 if standort == '1' else 3
        nur_stellantis = True
    else:
        # Alle
        standort_int = 0
        nur_stellantis = False
    
    location_filter = build_locosoft_filter_verkauf(standort_int, nur_stellantis)
    
    # Wirtschaftsjahr-Start berechnen (1. September)
    WJ_START_MONAT = 9
    
    # Aktuelles Jahr: Monat
    monat_von = f"{jahr}-{monat:02d}-01"
    if monat == 12:
        monat_bis = f"{jahr+1}-01-01"
    else:
        monat_bis = f"{jahr}-{monat+1:02d}-01"
    
    # Aktuelles Jahr: Jahr (kumuliert vom WJ-Start)
    if monat >= WJ_START_MONAT:
        jahr_von = f"{jahr}-{WJ_START_MONAT:02d}-01"
    else:
        jahr_von = f"{jahr-1}-{WJ_START_MONAT:02d}-01"
    jahr_bis = monat_bis  # Bis Ende des aktuellen Monats
    
    # Vorjahr: Monat (gleicher Monat)
    vj_monat_von = f"{jahr-1}-{monat:02d}-01"
    if monat == 12:
        vj_monat_bis = f"{jahr}-01-01"
    else:
        vj_monat_bis = f"{jahr-1}-{monat+1:02d}-01"
    
    # Vorjahr: Jahr (kumuliert vom WJ-Start)
    if monat >= WJ_START_MONAT:
        vj_jahr_von = f"{jahr-1}-{WJ_START_MONAT:02d}-01"
    else:
        vj_jahr_von = f"{jahr-2}-{WJ_START_MONAT:02d}-01"
    vj_jahr_bis = vj_monat_bis  # Bis Ende des VJ-Monats
    
    nw_monat = 0
    nw_jahr = 0
    nw_vj_monat = 0
    nw_vj_jahr = 0
    gw_monat = 0
    gw_jahr = 0
    gw_vj_monat = 0
    gw_vj_jahr = 0
    
    try:
        with locosoft_session() as conn_loco:
            cursor_loco = conn_loco.cursor()
            
            # NW Monat (aktuell)
            cursor_loco.execute(f"""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('N', 'T', 'V')
                  {location_filter}
            """, (monat_von, monat_bis))
            row = cursor_loco.fetchone()
            nw_monat = int(row[0] or 0) if row else 0
            
            # NW Jahr (aktuell, kumuliert)
            cursor_loco.execute(f"""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('N', 'T', 'V')
                  {location_filter}
            """, (jahr_von, jahr_bis))
            row = cursor_loco.fetchone()
            nw_jahr = int(row[0] or 0) if row else 0
            
            # NW VJ Monat
            cursor_loco.execute(f"""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('N', 'T', 'V')
                  {location_filter}
            """, (vj_monat_von, vj_monat_bis))
            row = cursor_loco.fetchone()
            nw_vj_monat = int(row[0] or 0) if row else 0
            
            # NW VJ Jahr (kumuliert)
            cursor_loco.execute(f"""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('N', 'T', 'V')
                  {location_filter}
            """, (vj_jahr_von, vj_jahr_bis))
            row = cursor_loco.fetchone()
            nw_vj_jahr = int(row[0] or 0) if row else 0
            
            # GW Monat (aktuell)
            cursor_loco.execute(f"""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('G', 'D', 'L')
                  {location_filter}
            """, (monat_von, monat_bis))
            row = cursor_loco.fetchone()
            gw_monat = int(row[0] or 0) if row else 0
            
            # GW Jahr (aktuell, kumuliert)
            cursor_loco.execute(f"""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('G', 'D', 'L')
                  {location_filter}
            """, (jahr_von, jahr_bis))
            row = cursor_loco.fetchone()
            gw_jahr = int(row[0] or 0) if row else 0
            
            # GW VJ Monat
            cursor_loco.execute(f"""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('G', 'D', 'L')
                  {location_filter}
            """, (vj_monat_von, vj_monat_bis))
            row = cursor_loco.fetchone()
            gw_vj_monat = int(row[0] or 0) if row else 0
            
            # GW VJ Jahr (kumuliert)
            cursor_loco.execute(f"""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('G', 'D', 'L')
                  {location_filter}
            """, (vj_jahr_von, vj_jahr_bis))
            row = cursor_loco.fetchone()
            gw_vj_jahr = int(row[0] or 0) if row else 0
            
    except Exception as e:
        print(f"Fehler bei Stückzahl-Berechnung: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: 0
    
    return {
        'nw': {
            'monat': nw_monat,
            'jahr': nw_jahr,
            'vj_monat': nw_vj_monat,
            'vj_jahr': nw_vj_jahr
        },
        'gw': {
            'monat': gw_monat,
            'jahr': gw_jahr,
            'vj_monat': gw_vj_monat,
            'vj_jahr': gw_vj_jahr
        }
    }


def _berechne_stueckzahlen(datum_von: str, datum_bis: str, firma: str = '0', standort: str = '0'):
    """
    TAG 177: Berechnet NW und GW Stückzahlen aus dealer_vehicles (analog Globalcube).
    
    NW: dealer_vehicle_type IN ('N', 'T', 'V')
    GW: dealer_vehicle_type IN ('G', 'D', 'L')
    
    Args:
        datum_von, datum_bis: Datumsbereich
        firma: '0'=Alle, '1'=Stellantis, '2'=Hyundai
        standort: '0'=Alle, '1'=Deggendorf, '2'=Landau, 'deg-both'=Deggendorf konsolidiert
    
    Returns: {'nw': int, 'gw': int}
    """
    from api.standort_utils import build_locosoft_filter_verkauf
    
    # Standort-Parameter mappen (firma/standort → standort int)
    standort_int = 0
    nur_stellantis = False
    
    if standort == 'deg-both':
        # Deggendorf konsolidiert: beide Firmen
        standort_int = 1
        nur_stellantis = False
    elif standort == '1':
        # Deggendorf: abhängig von firma
        standort_int = 1
        nur_stellantis = (firma == '1')
    elif standort == '2':
        # Landau: immer Stellantis
        standort_int = 3
        nur_stellantis = True
    elif firma == '2':
        # Hyundai: Standort 2
        standort_int = 2
        nur_stellantis = False
    elif firma == '1':
        # Stellantis: Standort 1 (Deggendorf) oder 3 (Landau)
        if standort == '0':
            standort_int = 0  # Alle
        else:
            standort_int = 1 if standort == '1' else 3
        nur_stellantis = True
    else:
        # Alle
        standort_int = 0
        nur_stellantis = False
    
    location_filter = build_locosoft_filter_verkauf(standort_int, nur_stellantis)
    
    nw_stueck = 0
    gw_stueck = 0
    
    try:
        with locosoft_session() as conn_loco:
            cursor_loco = conn_loco.cursor()
            
            # NW Stückzahl: N, T, V (analog Globalcube)
            cursor_loco.execute(f"""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('N', 'T', 'V')
                  {location_filter}
            """, (datum_von, datum_bis))
            row = cursor_loco.fetchone()
            nw_stueck = int(row[0] or 0) if row else 0
            
            # GW Stückzahl: G, D, L (analog Globalcube)
            cursor_loco.execute(f"""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('G', 'D', 'L')
                  {location_filter}
            """, (datum_von, datum_bis))
            row = cursor_loco.fetchone()
            gw_stueck = int(row[0] or 0) if row else 0
            
    except Exception as e:
        print(f"Fehler bei Stückzahl-Berechnung: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: 0
    
    return {'nw': nw_stueck, 'gw': gw_stueck}


def _berechne_bwa_ytd(cursor, bis_monat: int, jahr: int, firma: str = '0', standort: str = '0'):
    """
    BWA Year-to-Date: Kumuliert vom Wirtschaftsjahr-Start bis zum angegebenen Monat.

    WICHTIG: Abweichendes Wirtschaftsjahr - Start am 1. September!
    - September-Dezember: WJ beginnt am 01.09. desselben Jahres
    - Januar-August: WJ beginnt am 01.09. des Vorjahres

    Returns:
        dict mit kumulierten BWA-Positionen
    """
    # Abweichendes Wirtschaftsjahr: Start am 1. September
    WJ_START_MONAT = 9  # September

    if bis_monat >= WJ_START_MONAT:
        # September-Dezember: WJ-Start ist 01.09. desselben Jahres
        wj_start_jahr = jahr
    else:
        # Januar-August: WJ-Start ist 01.09. des Vorjahres
        wj_start_jahr = jahr - 1

    datum_von = f"{wj_start_jahr}-{WJ_START_MONAT:02d}-01"

    if bis_monat == 12:
        datum_bis = f"{jahr+1}-01-01"
    else:
        datum_bis = f"{jahr}-{bis_monat+1:02d}-01"

    # Filter bauen (TAG157: Jetzt mit separatem Einsatz-Filter!)
    firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, _ = build_firma_standort_filter(firma, standort)

    # WICHTIG: G&V-Abschlussbuchungen ausschließen (verfälschen BWA!)
    # TAG 179: Zentrale Funktion verwenden
    from api.db_utils import get_guv_filter
    guv_filter = get_guv_filter()

    # Umsatz YTD
    # TAG182: Hyundai verwendet 800000-899999 (inkl. 89xxxx), nicht nur bis 889999!
    # TAG182: Für Gesamtsumme (firma=0, standort=0) muss Hyundai's 89xxxx (außer 8932xx) eingeschlossen werden!
    if firma == '0' and standort == '0':
        # Gesamtsumme: Deggendorf+Landau (800000-889999 + 893200-893299) + Hyundai (800000-899999 außer 8932xx)
        umsatz_range_filter = """AND (
            ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
            OR ((nominal_account_number BETWEEN 800000 AND 899999) AND NOT (nominal_account_number BETWEEN 893200 AND 893299) AND branch_number = 2 AND subsidiary_to_company_ref = 2)
        )"""
    elif firma == '2':
        # Hyundai: Alle 8xxxxx (inkl. 89xxxx, außer 8932xx)
        umsatz_range_filter = "AND ((nominal_account_number BETWEEN 800000 AND 899999) AND NOT (nominal_account_number BETWEEN 893200 AND 893299))"
    else:
        # Stellantis/Alle: 800000-889999 + 893200-893299
        umsatz_range_filter = "AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))"
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          {umsatz_range_filter}
          {firma_filter_umsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    umsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)

    # Einsatz YTD (TAG157: firma_filter_einsatz für korrekte Standort-Zuordnung!)
    # TAG182: Landau verwendet jetzt branch_number=3 (nicht mehr 6. Ziffer='2')
    # TAG 179: Konten-Ranges zentral verwenden
    einsatz_range = KONTO_RANGES['einsatz']
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN {einsatz_range[0]} AND {einsatz_range[1]}
          {firma_filter_einsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    einsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)

    # Variable Kosten YTD
    # TAG182: Landau - 6. Ziffer='2' für Kosten (nicht branch_number=3, da Kosten hauptsächlich branch=1 haben)!
    # TAG182: Hyundai - 8910xx AUSSCHLIESSEN (negativer Wert, reduziert Kosten fälschlicherweise)
    # TAG182: Deggendorf - Nur 6. Ziffer='1' verwenden (nicht branch=1 AND 6. Ziffer='1'), da es Variable Kosten mit branch=3 gibt!
    # TAG182: Für Gesamtsumme (firma=0, standort=0) muss 8910xx für Hyundai ausgeschlossen werden!
    if firma == '0' and standort == '0':
        # Gesamtsumme: Deggendorf (6. Ziffer='1', subsidiary=1, mit 8910xx) + Landau (6. Ziffer='2', subsidiary=1, mit 8910xx) + Hyundai (6. Ziffer='1', subsidiary=2, OHNE 8910xx)
        variable_kosten_filter_ytd = """AND (
            (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1)
            OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
            OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2 AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
        )"""
        variable_8910xx_include_ytd = True  # Gesamtsumme: 8910xx für Deggendorf+Landau einschließen, aber für Hyundai ausschließen (via Filter)
    elif standort == '2' and firma == '1':
        variable_kosten_filter_ytd = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
        variable_8910xx_include_ytd = True  # Landau: 8910xx einschließen
    elif standort == '1' and firma == '1':
        # Deggendorf: Nur 6. Ziffer='1' verwenden (nicht branch=1 AND 6. Ziffer='1'), da es Variable Kosten mit branch=3 gibt!
        variable_kosten_filter_ytd = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1"
        variable_8910xx_include_ytd = True  # Deggendorf: 8910xx einschließen
    elif firma == '2':
        # Hyundai: 8910xx AUSSCHLIESSEN (sollte nicht in Variablen Kosten sein)
        variable_kosten_filter_ytd = firma_filter_kosten
        variable_8910xx_include_ytd = False
    else:
        variable_kosten_filter_ytd = firma_filter_kosten
        variable_8910xx_include_ytd = True  # Stellantis/Alle: 8910xx einschließen
    
    # Variable Kosten YTD Query - 8910xx bedingt einschließen
    variable_kosten_where_ytd = """
          AND (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR (nominal_account_number BETWEEN 455000 AND 456999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR (nominal_account_number BETWEEN 487000 AND 487099
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR nominal_account_number BETWEEN 491000 AND 497899"""
    
    if variable_8910xx_include_ytd:
        variable_kosten_where_ytd += """
            OR nominal_account_number BETWEEN 891000 AND 891099"""
    
    variable_kosten_where_ytd += """
          )"""
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          {variable_kosten_where_ytd}
          {variable_kosten_filter_ytd}
          {guv_filter}
    """), (datum_von, datum_bis))
    variable = float(row_to_dict(cursor.fetchone())['wert'] or 0)

    # Direkte Kosten YTD
    # TAG182: Landau - 6. Ziffer='2' für Kosten (nicht branch_number=3, da Kosten hauptsächlich branch=1 haben)!
    if standort == '2' and firma == '1':
        direkte_kosten_filter_ytd = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
    else:
        direkte_kosten_filter_ytd = firma_filter_kosten
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND NOT (
            nominal_account_number = 410021
            OR nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR nominal_account_number BETWEEN 489000 AND 489999
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
          {direkte_kosten_filter_ytd}
          {guv_filter}
    """), (datum_von, datum_bis))
    direkte = float(row_to_dict(cursor.fetchone())['wert'] or 0)

    # Indirekte Kosten YTD
    # TAG182: Landau - 6. Ziffer='2' für Kosten (nicht branch_number=3, da Kosten hauptsächlich branch=1 haben)!
    if standort == '2' and firma == '1':
        indirekte_kosten_filter_ytd = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
    else:
        indirekte_kosten_filter_ytd = firma_filter_kosten
    
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (
            (nominal_account_number BETWEEN 400000 AND 499999
             AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR (nominal_account_number BETWEEN 424000 AND 424999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR (nominal_account_number BETWEEN 438000 AND 438999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR nominal_account_number BETWEEN 498000 AND 499999
            OR (nominal_account_number BETWEEN 891000 AND 896999
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
                AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
            OR (nominal_account_number BETWEEN 489000 AND 489999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
          )
          AND NOT (
            nominal_account_number = 410021
            OR nominal_account_number BETWEEN 411000 AND 411999
            OR (nominal_account_number BETWEEN 489000 AND 489999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
          )
          {indirekte_kosten_filter_ytd}
          {guv_filter}
    """), (datum_von, datum_bis))
    indirekte = float(row_to_dict(cursor.fetchone())['wert'] or 0)

    # Neutrales Ergebnis YTD
    # TAG 179: Konten-Ranges zentral verwenden
    neutral_range = KONTO_RANGES['neutral']
    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN {neutral_range[0]} AND {neutral_range[1]}
          {firma_filter_umsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    neutral = float(row_to_dict(cursor.fetchone())['wert'] or 0)

    # Berechnungen
    db1 = umsatz - einsatz
    db2 = db1 - variable
    db3 = db2 - direkte
    be = db3 - indirekte
    ue = be + neutral

    # TAG 177: Bereiche für YTD berechnen (wie in get_bwa_v2)
    bereiche = []
    for bereich_key, config in sorted(BEREICHE_CONFIG.items(), key=lambda x: x[1]['order']):
        werte = _berechne_bereich_werte(
            cursor, bereich_key, config, datum_von, datum_bis,
            firma_filter_umsatz, guv_filter, firma_filter_einsatz
        )
        bereiche.append({
            'key': bereich_key,
            'name': config['name'],
            **werte
        })
    
    # TAG 177: Stückzahlen für YTD Vorjahr berechnen
    stueckzahlen_ytd_vj = _berechne_stueckzahlen(datum_von, datum_bis, firma, standort)
    # Stückzahlen zu NW und GW Bereichen hinzufügen
    for bereich in bereiche:
        if bereich['key'] == 'NW':
            bereich['stueck'] = stueckzahlen_ytd_vj['nw']
        elif bereich['key'] == 'GW':
            bereich['stueck'] = stueckzahlen_ytd_vj['gw']
        else:
            bereich['stueck'] = 0

    return {
        'umsatz': round(umsatz, 2),
        'einsatz': round(einsatz, 2),
        'db1': round(db1, 2),
        'bereiche': bereiche,
        'variable_kosten': round(variable, 2),
        'db2': round(db2, 2),
        'direkte_kosten': round(direkte, 2),
        'db3': round(db3, 2),
        'indirekte_kosten': round(indirekte, 2),
        'betriebsergebnis': round(be, 2),
        'neutrales_ergebnis': round(neutral, 2),
        'unternehmensergebnis': round(ue, 2)
    }


def berechne_bwa_live(monat: int, jahr: int, firma: str = '0', standort: str = '0'):
    """
    BWA live aus loco_journal_accountings berechnen.
    Inkl. Vorjahres-Vergleich für Quick Win Dashboard.

    Parameter:
        monat, jahr: Zeitraum
        firma: 0=Alle, 1=Stellantis, 2=Hyundai
        standort: 0=Alle, 1=Deggendorf, 2=Landau
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()

            # Filter bauen (für standort_name) - TAG157: 4 Rückgabewerte
            _, _, _, standort_name = build_firma_standort_filter(firma, standort)

            # Aktueller Monat berechnen
            werte = _berechne_bwa_werte(cursor, monat, jahr, firma, standort)

            # Vorjahr berechnen
            vorjahr_werte = _berechne_bwa_werte(cursor, monat, jahr - 1, firma, standort)

            # Abweichungen berechnen
            abweichungen = {}
            for key in ['umsatz', 'db1', 'db2', 'db3', 'betriebsergebnis', 'unternehmensergebnis']:
                aktuell = werte.get(key, 0)
                vj = vorjahr_werte.get(key, 0)
                if vj != 0:
                    abweichungen[key] = round((aktuell - vj) / abs(vj) * 100, 1)
                else:
                    abweichungen[key] = 0 if aktuell == 0 else 100.0

            # YTD (Jahr bis aktueller Monat) berechnen
            ytd_werte = _berechne_bwa_ytd(cursor, monat, jahr, firma, standort)
            ytd_vorjahr = _berechne_bwa_ytd(cursor, monat, jahr - 1, firma, standort)

            # YTD Abweichungen
            ytd_abweichungen = {}
            for key in ['umsatz', 'db1', 'db2', 'db3', 'betriebsergebnis', 'unternehmensergebnis']:
                aktuell = ytd_werte.get(key, 0)
                vj = ytd_vorjahr.get(key, 0)
                if vj != 0:
                    ytd_abweichungen[key] = round((aktuell - vj) / abs(vj) * 100, 1)
                else:
                    ytd_abweichungen[key] = 0 if aktuell == 0 else 100.0

            data = {
                'monat': monat,
                'monat_name': MONAT_NAMEN.get(monat, str(monat)),
                'jahr': jahr,
                'firma': firma,
                'standort': standort,
                'standort_name': standort_name,
                **werte
            }

            return jsonify({
                'status': 'ok',
                'data': data,
                'vorjahr': vorjahr_werte,
                'abweichungen': abweichungen,
                'ytd': ytd_werte,
                'ytd_vorjahr': ytd_vorjahr,
                'ytd_abweichungen': ytd_abweichungen,
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
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM bwa_monatswerte")
            row = row_to_dict(cursor.fetchone())
            count = row['cnt'] if row else 0

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

        # Subsidiary für loco_nominal_accounts
        subsidiary = 2 if firma == '2' else 1  # 1=Stellantis, 2=Hyundai

        if not monat or not jahr:
            heute = datetime.now()
            monat = monat or heute.month
            jahr = jahr or heute.year

        datum_von = f"{jahr}-{monat:02d}-01"
        if monat == 12:
            datum_bis = f"{jahr+1}-01-01"
        else:
            datum_bis = f"{jahr}-{monat+1:02d}-01"

        # Filter bauen (TAG157: Jetzt mit separatem Einsatz-Filter!)
        firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, standort_name = build_firma_standort_filter(firma, standort)

        # Position -> SQL-Filter Mapping
        # 'filter_type': 'umsatz' = nutzt firma_filter_umsatz
        # 'filter_type': 'einsatz' = nutzt firma_filter_einsatz (TAG157: Konto-Endziffer!)
        # 'filter_type': 'kosten' = nutzt firma_filter_kosten
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
                'filter_type': 'einsatz'  # TAG157: Eigener Filter mit Konto-Endziffer!
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
        # TAG157: Separater Einsatz-Filter für korrekte Standort-Zuordnung
        if pf['filter_type'] == 'kosten':
            aktiver_filter = firma_filter_kosten
        elif pf['filter_type'] == 'einsatz':
            aktiver_filter = firma_filter_einsatz
        else:
            aktiver_filter = firma_filter_umsatz

        with db_session() as conn:
            cursor = conn.cursor()

            # =====================================================================
            # EBENE: BUCHUNGEN (Detail für ein Konto)
            # =====================================================================
            if ebene == 'buchungen' and konto:
                cursor.execute(convert_placeholders(f"""
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
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number = %s
                      {aktiver_filter}
                    ORDER BY accounting_date, document_number
                """), (datum_von, datum_bis, konto))

                buchungen = cursor.fetchall()

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

                cursor.execute(convert_placeholders(f"""
                    SELECT
                        nominal_account_number as konto,
                        MIN(posting_text) as bezeichnung,
                        SUM({pf['vorzeichen']}) / 100.0 as betrag,
                        COUNT(*) as buchungen_anzahl
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND {pf['where']}
                      AND {konto_filter}
                      {aktiver_filter}
                    GROUP BY nominal_account_number
                    HAVING SUM({pf['vorzeichen']}) != 0
                    ORDER BY ABS(SUM({pf['vorzeichen']})) DESC
                """), (datum_von, datum_bis))

                konten = cursor.fetchall()

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
                        'bezeichnung': get_konto_bezeichnung(conn, row['konto'], subsidiary),
                        'betrag': round(row['betrag'], 2),
                        'buchungen_anzahl': row['buchungen_anzahl']
                    } for row in konten],
                    'summe': round(summe, 2),
                    'anzahl_konten': len(konten)
                })

            # =====================================================================
            # EBENE: GRUPPEN (Zusammenfassung nach 2-stelligem Präfix)
            # =====================================================================
            cursor.execute(convert_placeholders(f"""
                SELECT
                    substr(CAST(nominal_account_number AS TEXT), 1, 2) as gruppe,
                    SUM({pf['vorzeichen']}) / 100.0 as betrag,
                    COUNT(DISTINCT nominal_account_number) as anzahl_konten,
                    COUNT(*) as buchungen_anzahl
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND {pf['where']}
                  {aktiver_filter}
                GROUP BY substr(CAST(nominal_account_number AS TEXT), 1, 2)
                HAVING SUM({pf['vorzeichen']}) != 0
                ORDER BY ABS(SUM({pf['vorzeichen']})) DESC
            """), (datum_von, datum_bis))

            gruppen_rows = cursor.fetchall()

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


# =============================================================================
# BWA v2 API - Erweiterte Struktur mit Bruttoerträgen nach Bereichen
# =============================================================================

# Bereichs-Konfiguration nach erweiterter Struktur
# Jeder Bereich hat Erlös-Konten (8x) und Einsatz-Konten (7x)
BEREICHE_CONFIG = {
    'NW': {
        'name': 'Neuwagen',
        'erlos_prefix': '81',    # 81xxxx = Erlöse NW
        'einsatz_prefix': '71',  # 71xxxx = Einsatz NW
        'order': 1
    },
    'GW': {
        'name': 'Gebrauchtwagen',
        'erlos_prefix': '82',
        'einsatz_prefix': '72',
        'order': 2
    },
    'ME': {
        'name': 'Mechanik',
        'erlos_prefix': '84',    # 84xxxx = Lohn (inkl. Mechanik, Karosserie, Lack)
        'einsatz_prefix': '74',
        'order': 3
    },
    'TZ': {
        'name': 'Teile & Zubehör',
        'erlos_prefix': '83',
        'einsatz_prefix': '73',
        'order': 4
    },
    'MW': {
        'name': 'Mietwagen',
        'erlos_range': (860000, 869999),  # 86xxxx = Sonstige Erlöse (Mietwagen)
        'einsatz_range': (760000, 769999),
        'order': 5
    },
    'SO': {
        'name': 'Sonstige',
        'erlos_range': (850000, 859999),  # 85xxxx = Lack, 88xxxx = Vermietung
        'einsatz_range': (750000, 759999),
        'order': 6
    }
}


def _berechne_bereich_werte(cursor, bereich: str, config: dict, datum_von: str, datum_bis: str,
                            firma_filter_umsatz: str, guv_filter: str, firma_filter_einsatz: str = None):
    """
    Berechnet Erlös, Einsatz und Bruttoertrag für einen Bereich.
    TAG157: Separater Einsatz-Filter für korrekte Standort-Zuordnung.
    """
    # TAG157: Fallback für Abwärtskompatibilität
    if firma_filter_einsatz is None:
        firma_filter_einsatz = firma_filter_umsatz

    # Erlöse
    if 'erlos_prefix' in config:
        prefix = config['erlos_prefix']
        erlos_where = f"nominal_account_number BETWEEN {prefix}0000 AND {prefix}9999"
    else:
        range_start, range_end = config['erlos_range']
        erlos_where = f"nominal_account_number BETWEEN {range_start} AND {range_end}"

    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND {erlos_where}
          {firma_filter_umsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    erlos = float(row_to_dict(cursor.fetchone())['wert'] or 0)

    # Einsatz (TAG157: firma_filter_einsatz für korrekte Standort-Zuordnung!)
    if 'einsatz_prefix' in config:
        prefix = config['einsatz_prefix']
        einsatz_where = f"nominal_account_number BETWEEN {prefix}0000 AND {prefix}9999"
    else:
        range_start, range_end = config['einsatz_range']
        einsatz_where = f"nominal_account_number BETWEEN {range_start} AND {range_end}"

    cursor.execute(convert_placeholders(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND {einsatz_where}
          {firma_filter_einsatz}
          {guv_filter}
    """), (datum_von, datum_bis))
    einsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)

    bruttoertrag = erlos - einsatz

    return {
        'erlos': round(erlos, 2),
        'einsatz': round(einsatz, 2),
        'bruttoertrag': round(bruttoertrag, 2)
    }


@controlling_api.route('/api/controlling/bwa/v2', methods=['GET'])
def get_bwa_v2():
    """
    BWA v2 - Erweiterte Struktur mit Bruttoerträgen nach Bereichen.

    Struktur wie GlobalCube:
    - Umsatzerlöse (Gesamt)
    - Einsatzwerte (Gesamt)
    - Bruttoertrag 1 - NW (Neuwagen)
    - Bruttoertrag 2 - GW (Gebrauchtwagen)
    - Bruttoertrag 3 - ME (Mechanik)
    - Bruttoertrag 4 - TZ (Teile & Zubehör)
    - Bruttoertrag 5 - MW (Mietwagen)
    - Bruttoertrag 6 - SO (Sonstige)
    - Variable Kosten
    - Gesamt (DB2)

    Query-Parameter:
        monat: int (1-12)
        jahr: int (z.B. 2025)
        firma: 0=Alle, 1=Stellantis, 2=Hyundai
        standort: 0=Alle, 1=Deggendorf, 2=Landau (nur bei Firma 1)
    """
    try:
        # TAG 177: Monat/Jahr als String parsen (kann von Select kommen)
        monat_str = request.args.get('monat', '')
        jahr_str = request.args.get('jahr', '')
        try:
            monat = int(monat_str) if monat_str else None
            jahr = int(jahr_str) if jahr_str else None
        except (ValueError, TypeError):
            monat = None
            jahr = None
        
        firma = request.args.get('firma', '0')
        standort = request.args.get('standort', '0')
        kst_param = request.args.get('kst', '')  # TAG 181: KST-Filter (komma-separiert, z.B. "1,2,3")
        
        # TAG182: Landau-Spezialfall: standort='3' normalisieren zu standort='2'
        if standort == '3' and firma == '0':
            standort = '2'
            firma = '1'

        if not monat or not jahr:
            heute = datetime.now()
            monat = monat or heute.month
            jahr = jahr or heute.year

        datum_von = f"{jahr}-{monat:02d}-01"
        if monat == 12:
            datum_bis = f"{jahr+1}-01-01"
        else:
            datum_bis = f"{jahr}-{monat+1:02d}-01"

        # Filter bauen (TAG157: Jetzt mit separatem Einsatz-Filter!)
        firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, standort_name = build_firma_standort_filter(firma, standort)
        # TAG 179: Zentrale Funktion verwenden
        from api.db_utils import get_guv_filter
        guv_filter = get_guv_filter()
        
        # TAG 181: KST-Filter bauen (nur für Kosten-Konten 4xxxxx)
        kst_filter = ''
        kst_params = []
        if kst_param:
            kst_list = [k.strip() for k in kst_param.split(',') if k.strip()]
            if kst_list:
                kst_filter = f"AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ({','.join(['%s'] * len(kst_list))})"
                kst_params = kst_list
        
        # Direkte und indirekte KST-Filter vorbereiten
        direkte_kst_filter = ''
        direkte_kst_params = []
        indirekte_kst_filter = ''
        
        if kst_filter:
            # Direkte Kosten: Nur KST 1-7 aus dem Filter
            # TAG 181: KST-Mapping korrigiert: 1=NW, 2=GW, 3=Service, 6=T+Z, 7=Mietwagen
            kst_direkt = [k for k in kst_params if k in ['1','2','3','6','7']]  # KST 4 und 5 entfernt (nicht verwendet)
            if kst_direkt:
                direkte_kst_filter = f"AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ({','.join(['%s'] * len(kst_direkt))})"
                direkte_kst_params = kst_direkt
            else:
                # Keine direkten KSTs ausgewählt -> 0
                direkte_kst_filter = "AND 1=0"  # Immer false
        else:
            # Kein Filter -> alle KST 1-7 (KST 4 und 5 existieren nicht in Locosoft)
            direkte_kst_filter = "AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7')"
        
        if kst_filter:
            # Indirekte Kosten: Wenn KST 0 ausgewählt, dann indirekte Kosten anzeigen
            if '0' in kst_params:
                # Indirekte Kosten mit KST 0 oder spezielle Konten
                indirekte_kst_filter = """AND (
                (nominal_account_number BETWEEN 400000 AND 499999
                 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
                OR (nominal_account_number BETWEEN 424000 AND 424999
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                OR (nominal_account_number BETWEEN 438000 AND 438999
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                OR nominal_account_number BETWEEN 498000 AND 499999
                OR (nominal_account_number BETWEEN 891000 AND 896999
                    AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
                    AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
                OR (nominal_account_number BETWEEN 489000 AND 489999
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
              )
              AND NOT (
                nominal_account_number = 410021
                OR nominal_account_number BETWEEN 411000 AND 411999
                OR (nominal_account_number BETWEEN 489000 AND 489999
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
              )"""
            else:
                # Keine KST 0 ausgewählt -> nur spezielle Konten (ohne KST 0)
                indirekte_kst_filter = """AND (
                    (nominal_account_number BETWEEN 424000 AND 424999
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                    OR (nominal_account_number BETWEEN 438000 AND 438999
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                    OR nominal_account_number BETWEEN 498000 AND 499999
                    OR (nominal_account_number BETWEEN 891000 AND 896999
                        AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
                        AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
                    OR (nominal_account_number BETWEEN 489000 AND 489999
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
                  )
                  AND NOT (
                    nominal_account_number = 410021
                    OR nominal_account_number BETWEEN 411000 AND 411999
                    OR (nominal_account_number BETWEEN 489000 AND 489999
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                  )"""
        else:
            # Kein Filter -> alle indirekten Kosten
            indirekte_kst_filter = """AND (
                (nominal_account_number BETWEEN 400000 AND 499999
                 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
                OR (nominal_account_number BETWEEN 424000 AND 424999
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                OR (nominal_account_number BETWEEN 438000 AND 438999
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                OR nominal_account_number BETWEEN 498000 AND 499999
                OR (nominal_account_number BETWEEN 891000 AND 896999
                    AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
                    AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
                OR (nominal_account_number BETWEEN 489000 AND 489999
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
              )
              AND NOT (
                nominal_account_number = 410021
                OR nominal_account_number BETWEEN 411000 AND 411999
                OR (nominal_account_number BETWEEN 489000 AND 489999
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
              )"""

        with db_session() as conn:
            cursor = conn.cursor()

            # Gesamt-Umsatz (alle 8er Konten)
            # TAG182: Für Gesamtsumme (firma=0, standort=0) muss Hyundai's 89xxxx (außer 8932xx) eingeschlossen werden!
            # Deggendorf+Landau: 800000-889999 + 893200-893299
            # Hyundai: 800000-899999 (außer 8932xx)
            # Gesamtsumme: Kombination beider
            if firma == '0' and standort == '0':
                # Gesamtsumme: Deggendorf+Landau (800000-889999 + 893200-893299) + Hyundai (800000-899999 außer 8932xx)
                umsatz_range_gesamt = """AND (
                    ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
                    OR ((nominal_account_number BETWEEN 800000 AND 899999) AND NOT (nominal_account_number BETWEEN 893200 AND 893299) AND branch_number = 2 AND subsidiary_to_company_ref = 2)
                )"""
            else:
                # Einzelbetrieb: Standard-Filter
                if firma == '2':
                    # Hyundai: Alle 8xxxxx (inkl. 89xxxx, außer 8932xx)
                    umsatz_range_gesamt = "AND ((nominal_account_number BETWEEN 800000 AND 899999) AND NOT (nominal_account_number BETWEEN 893200 AND 893299))"
                else:
                    # Stellantis/Alle: 800000-889999 + 893200-893299
                    umsatz_range_gesamt = "AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))"
            
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  {umsatz_range_gesamt}
                  {firma_filter_umsatz}
                  {guv_filter}
            """), (datum_von, datum_bis))
            umsatz_gesamt = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            # Gesamt-Einsatz (alle 7er Konten) - TAG157: firma_filter_einsatz!
            # TAG182: Landau verwendet jetzt branch_number=3 (nicht mehr 6. Ziffer='2')
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 700000 AND 799999
                  {firma_filter_einsatz}
                  {guv_filter}
            """), (datum_von, datum_bis))
            einsatz_gesamt = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            db1_gesamt = umsatz_gesamt - einsatz_gesamt

            # TAG 181: KST-Filter auf Bereiche anwenden
            # KST-Mapping korrigiert nach Buchhaltung:
            # - Für Kosten (4xxxxx): 5. Ziffer: 1=NW, 2=GW, 3=Service, 6=T+Z, 7=Mietwagen
            # - Für Umsatz/Einsatz (7xxxxx/8xxxxx): 6. Ziffer (Filialcode = Kostenstelle)
            #   ABER: Wir filtern Bereiche nach Präfix (81xxxx, 82xxxx), nicht nach KST!
            #   Daher: KST-Filter für Bereiche ist nur relevant für Kosten, nicht für Umsatz/Einsatz
            kst_zu_bereich = {
                '1': 'NW',  # Neuwagen
                '2': 'GW',  # Gebrauchtwagen
                '3': 'ME',  # Service/Werkstatt
                '6': 'TZ',  # Teile & Zubehör (KST 6, nicht 4!)
                '7': 'MW'   # Mietwagen (KST 7, nicht 5!)
            }
            
            # Wenn KST-Filter aktiv, nur relevante Bereiche anzeigen
            relevante_bereiche = None
            if kst_params:
                relevante_bereiche = set()
                for kst in kst_params:
                    if kst in kst_zu_bereich:
                        relevante_bereiche.add(kst_zu_bereich[kst])
                # Wenn nur KST 0 oder 7 ausgewählt, keine Bereiche anzeigen (nur Gemeinkosten/Verwaltung)
                if not relevante_bereiche:
                    relevante_bereiche = set()  # Leer = keine Bereiche
            
            # Bruttoerträge pro Bereich berechnen (TAG157: Mit separatem Einsatz-Filter!)
            bereiche = []
            for bereich_key, config in sorted(BEREICHE_CONFIG.items(), key=lambda x: x[1]['order']):
                # TAG 181: KST-Filter - nur relevante Bereiche anzeigen
                if relevante_bereiche is not None and bereich_key not in relevante_bereiche:
                    continue
                    
                werte = _berechne_bereich_werte(
                    cursor, bereich_key, config, datum_von, datum_bis,
                    firma_filter_umsatz, guv_filter, firma_filter_einsatz
                )
                bereiche.append({
                    'key': bereich_key,
                    'name': config['name'],
                    **werte
                })
            
            # TAG 181: Stückzahlen in erweiterter Struktur berechnen (Monat, Jahr, VJ Monat, VJ Jahr)
            stueckzahlen = _berechne_stueckzahlen_erweitert(monat, jahr, firma, standort)
            # Stückzahlen zu NW und GW Bereichen hinzufügen
            for bereich in bereiche:
                if bereich['key'] == 'NW':
                    bereich['stueck'] = stueckzahlen['nw']
                elif bereich['key'] == 'GW':
                    bereich['stueck'] = stueckzahlen['gw']
                else:
                    bereich['stueck'] = {'monat': 0, 'jahr': 0, 'vj_monat': 0, 'vj_jahr': 0}

            # Variable Kosten
            # TAG182: Landau - 6. Ziffer='2' für Kosten (nicht branch_number=3, da Kosten hauptsächlich branch=1 haben)!
            # TAG182: Hyundai - 8910xx AUSSCHLIESSEN (negativer Wert, reduziert Kosten fälschlicherweise)
            # TAG182: Für Gesamtsumme (firma=0, standort=0) muss 8910xx für Hyundai ausgeschlossen werden!
            if firma == '0' and standort == '0':
                # Gesamtsumme: Deggendorf (6. Ziffer='1', subsidiary=1, mit 8910xx) + Landau (6. Ziffer='2', subsidiary=1, mit 8910xx) + Hyundai (6. Ziffer='1', subsidiary=2, OHNE 8910xx)
                variable_kosten_filter = """AND (
                    (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1)
                    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
                    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2 AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
                )"""
                variable_8910xx_include = True  # Gesamtsumme: 8910xx für Deggendorf+Landau einschließen, aber für Hyundai ausschließen (via Filter)
            elif standort == '2' and firma == '1':
                variable_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
                variable_8910xx_include = True  # Landau: 8910xx einschließen
            elif firma == '2':
                # Hyundai: 8910xx AUSSCHLIESSEN (sollte nicht in Variablen Kosten sein)
                variable_kosten_filter = firma_filter_kosten
                variable_8910xx_include = False
            else:
                variable_kosten_filter = firma_filter_kosten
                variable_8910xx_include = True  # Stellantis/Alle: 8910xx einschließen
            
            # Variable Kosten Query - 8910xx bedingt einschließen
            variable_kosten_where = """
                  AND (
                    nominal_account_number BETWEEN 415100 AND 415199
                    OR nominal_account_number BETWEEN 435500 AND 435599
                    OR (nominal_account_number BETWEEN 455000 AND 456999
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                    OR (nominal_account_number BETWEEN 487000 AND 487099
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                    OR nominal_account_number BETWEEN 491000 AND 497899"""
            
            if variable_8910xx_include:
                variable_kosten_where += """
                    OR nominal_account_number BETWEEN 891000 AND 891099"""
            
            variable_kosten_where += """
                  )"""
            
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  {variable_kosten_where}
                  {variable_kosten_filter}
                  {guv_filter}
                  {kst_filter}
            """), (datum_von, datum_bis) + tuple(kst_params))
            variable_kosten = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            db2 = db1_gesamt - variable_kosten

            # Direkte Kosten (Abteilungsbezogen - letzte Ziffer 1-7)
            # TAG182: Landau - 6. Ziffer='2' für Kosten (nicht branch_number=3, da Kosten hauptsächlich branch=1 haben)!
            if standort == '2' and firma == '1':
                direkte_kosten_filter_landau = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
            else:
                direkte_kosten_filter_landau = firma_filter_kosten
            
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 400000 AND 489999
                  {direkte_kst_filter}
          AND NOT (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR (nominal_account_number BETWEEN 489000 AND 489999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
                  {direkte_kosten_filter_landau}
                  {guv_filter}
            """), (datum_von, datum_bis) + tuple(direkte_kst_params))
            direkte_kosten = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            db3 = db2 - direkte_kosten

            # Indirekte Kosten (Gemeinkosten - letzte Ziffer 0 oder spezielle Konten)
            # TAG182: Landau - 6. Ziffer='2' für Kosten (nicht branch_number=3, da Kosten hauptsächlich branch=1 haben)!
            if standort == '2' and firma == '1':
                indirekte_kosten_filter_landau = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
            else:
                indirekte_kosten_filter_landau = firma_filter_kosten
            
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  {indirekte_kst_filter}
                  AND NOT (
                    nominal_account_number = 410021
                    OR nominal_account_number BETWEEN 411000 AND 411999
                    OR (nominal_account_number BETWEEN 489000 AND 489999
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                  )
                  {indirekte_kosten_filter_landau}
                  {guv_filter}
            """), (datum_von, datum_bis))
            indirekte_kosten = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            betriebsergebnis = db3 - indirekte_kosten

            # Neutrales Ergebnis (Konten 2xxxxx)
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 200000 AND 299999
                  {firma_filter_umsatz}
                  {guv_filter}
            """), (datum_von, datum_bis))
            neutrales_ergebnis = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            unternehmensergebnis = betriebsergebnis + neutrales_ergebnis

            # Vorjahr berechnen (gleicher Monat)
            vorjahr_datum_von = f"{jahr-1}-{monat:02d}-01"
            if monat == 12:
                vorjahr_datum_bis = f"{jahr}-01-01"
            else:
                vorjahr_datum_bis = f"{jahr-1}-{monat+1:02d}-01"

            # Vorjahr Gesamt-Umsatz
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND ((nominal_account_number BETWEEN 800000 AND 889999)
                       OR (nominal_account_number BETWEEN 893200 AND 893299))
                  {firma_filter_umsatz}
                  {guv_filter}
            """), (vorjahr_datum_von, vorjahr_datum_bis))
            vj_umsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            # Vorjahr Gesamt-Einsatz (TAG157: firma_filter_einsatz!)
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 700000 AND 799999
                  {firma_filter_einsatz}
                  {guv_filter}
            """), (vorjahr_datum_von, vorjahr_datum_bis))
            vj_einsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            vj_db1 = vj_umsatz - vj_einsatz

            # Vorjahr Bereiche (TAG157: Mit separatem Einsatz-Filter!)
            vj_bereiche = []
            for bereich_key, config in sorted(BEREICHE_CONFIG.items(), key=lambda x: x[1]['order']):
                # TAG 181: KST-Filter - nur relevante Bereiche anzeigen
                if relevante_bereiche is not None and bereich_key not in relevante_bereiche:
                    continue
                    
                werte = _berechne_bereich_werte(
                    cursor, bereich_key, config, vorjahr_datum_von, vorjahr_datum_bis,
                    firma_filter_umsatz, guv_filter, firma_filter_einsatz
                )
                vj_bereiche.append({
                    'key': bereich_key,
                    'name': config['name'],
                    **werte
                })
            
            # TAG 181: Stückzahlen für Vorjahr in erweiterter Struktur berechnen
            stueckzahlen_vorjahr = _berechne_stueckzahlen_erweitert(monat, jahr - 1, firma, standort)
            # Stückzahlen zu NW und GW Bereichen hinzufügen (erweiterte Struktur)
            for bereich in vj_bereiche:
                if bereich['key'] == 'NW':
                    bereich['stueck'] = stueckzahlen_vorjahr['nw']['monat']  # VJ Monat (einfache Zahl für Vorjahr)
                elif bereich['key'] == 'GW':
                    bereich['stueck'] = stueckzahlen_vorjahr['gw']['monat']  # VJ Monat (einfache Zahl für Vorjahr)
                else:
                    bereich['stueck'] = 0

            # Vorjahr Variable Kosten
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
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
                  {guv_filter}
                  {kst_filter}
            """), (vorjahr_datum_von, vorjahr_datum_bis) + tuple(kst_params))
            vj_variable = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            vj_db2 = vj_db1 - vj_variable

            # Vorjahr Direkte Kosten
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 400000 AND 489999
                  {direkte_kst_filter}
          AND NOT (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR (nominal_account_number BETWEEN 489000 AND 489999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
                  {firma_filter_kosten}
                  {guv_filter}
            """), (vorjahr_datum_von, vorjahr_datum_bis) + tuple(direkte_kst_params))
            vj_direkte = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            vj_db3 = vj_db2 - vj_direkte

            # Vorjahr Indirekte Kosten
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  {indirekte_kst_filter}
                  {firma_filter_kosten}
                  {guv_filter}
            """), (vorjahr_datum_von, vorjahr_datum_bis))
            vj_indirekte = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            vj_be = vj_db3 - vj_indirekte

            # Vorjahr Neutrales Ergebnis
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 200000 AND 299999
                  {firma_filter_umsatz}
                  {guv_filter}
            """), (vorjahr_datum_von, vorjahr_datum_bis))
            vj_neutral = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            vj_ue = vj_be + vj_neutral

            # YTD (Wirtschaftsjahr Sep-Aug) berechnen
            WJ_START_MONAT = 9
            if monat >= WJ_START_MONAT:
                wj_start_jahr = jahr
            else:
                wj_start_jahr = jahr - 1
            ytd_datum_von = f"{wj_start_jahr}-{WJ_START_MONAT:02d}-01"

            # YTD Umsatz
            # TAG182: Hyundai verwendet 800000-899999 (inkl. 89xxxx), nicht nur bis 889999!
            # TAG182: Für Gesamtsumme (firma=0, standort=0) muss Hyundai's 89xxxx (außer 8932xx) eingeschlossen werden!
            if firma == '0' and standort == '0':
                # Gesamtsumme: Deggendorf+Landau (800000-889999 + 893200-893299) + Hyundai (800000-899999 außer 8932xx)
                ytd_umsatz_range_filter = """AND (
                    ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
                    OR ((nominal_account_number BETWEEN 800000 AND 899999) AND NOT (nominal_account_number BETWEEN 893200 AND 893299) AND branch_number = 2 AND subsidiary_to_company_ref = 2)
                )"""
            elif firma == '2':
                # Hyundai: Alle 8xxxxx (inkl. 89xxxx, außer 8932xx)
                ytd_umsatz_range_filter = "AND ((nominal_account_number BETWEEN 800000 AND 899999) AND NOT (nominal_account_number BETWEEN 893200 AND 893299))"
            else:
                # Stellantis/Alle: 800000-889999 + 893200-893299
                ytd_umsatz_range_filter = "AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))"
            
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  {ytd_umsatz_range_filter}
                  {firma_filter_umsatz}
                  {guv_filter}
            """), (ytd_datum_von, datum_bis))
            ytd_umsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            # YTD Einsatz (TAG157: firma_filter_einsatz!)
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 700000 AND 799999
                  {firma_filter_einsatz}
                  {guv_filter}
            """), (ytd_datum_von, datum_bis))
            ytd_einsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            ytd_db1 = ytd_umsatz - ytd_einsatz

            # YTD Bereiche (TAG157: Mit separatem Einsatz-Filter!)
            ytd_bereiche = []
            for bereich_key, config in sorted(BEREICHE_CONFIG.items(), key=lambda x: x[1]['order']):
                # TAG 181: KST-Filter - nur relevante Bereiche anzeigen
                if relevante_bereiche is not None and bereich_key not in relevante_bereiche:
                    continue
                    
                werte = _berechne_bereich_werte(
                    cursor, bereich_key, config, ytd_datum_von, datum_bis,
                    firma_filter_umsatz, guv_filter, firma_filter_einsatz
                )
                ytd_bereiche.append({
                    'key': bereich_key,
                    'name': config['name'],
                    **werte
                })

            # YTD Variable Kosten
            # TAG182: Landau - ALLE Kosten mit 6. Ziffer='2' AND subsidiary_to_company_ref = 1 (nicht branch_number=3!)
            # TAG182: Hyundai - 8910xx AUSSCHLIESSEN (negativer Wert, reduziert Kosten fälschlicherweise)
            # TAG182: Deggendorf - Nur 6. Ziffer='1' verwenden (nicht branch=1 AND 6. Ziffer='1'), da es Variable Kosten mit branch=3 gibt!
            # TAG182: Für Gesamtsumme (firma=0, standort=0) muss 8910xx für Hyundai ausgeschlossen werden!
            if firma == '0' and standort == '0':
                # Gesamtsumme: Deggendorf (6. Ziffer='1', subsidiary=1, mit 8910xx) + Landau (6. Ziffer='2', subsidiary=1, mit 8910xx) + Hyundai (6. Ziffer='1', subsidiary=2, OHNE 8910xx)
                ytd_variable_kosten_filter = """AND (
                    (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1)
                    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
                    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2 AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
                )"""
                ytd_variable_8910xx_include = True  # Gesamtsumme: 8910xx für Deggendorf+Landau einschließen, aber für Hyundai ausschließen (via Filter)
            elif standort == '2' and firma == '1':
                ytd_variable_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
                ytd_variable_8910xx_include = True  # Landau: 8910xx einschließen
            elif standort == '1' and firma == '1':
                # Deggendorf: Nur 6. Ziffer='1' verwenden (nicht branch=1 AND 6. Ziffer='1'), da es Variable Kosten mit branch=3 gibt!
                ytd_variable_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1"
                ytd_variable_8910xx_include = True  # Deggendorf: 8910xx einschließen
            elif firma == '2':
                # Hyundai: 8910xx AUSSCHLIESSEN (sollte nicht in Variablen Kosten sein)
                ytd_variable_kosten_filter = firma_filter_kosten
                ytd_variable_8910xx_include = False
            else:
                ytd_variable_kosten_filter = firma_filter_kosten
                ytd_variable_8910xx_include = True  # Stellantis/Alle: 8910xx einschließen
            
            # YTD Variable Kosten Query - 8910xx bedingt einschließen
            ytd_variable_kosten_where = """
                  AND (
                    nominal_account_number BETWEEN 415100 AND 415199
                    OR nominal_account_number BETWEEN 435500 AND 435599
                    OR (nominal_account_number BETWEEN 455000 AND 456999
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                    OR (nominal_account_number BETWEEN 487000 AND 487099
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                    OR nominal_account_number BETWEEN 491000 AND 497899"""
            
            if ytd_variable_8910xx_include:
                ytd_variable_kosten_where += """
                    OR nominal_account_number BETWEEN 891000 AND 891099"""
            
            ytd_variable_kosten_where += """
                  )"""
            
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  {ytd_variable_kosten_where}
                  {ytd_variable_kosten_filter}
                  {guv_filter}
                  {kst_filter}
            """), (ytd_datum_von, datum_bis) + tuple(kst_params))
            ytd_variable = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            ytd_db2 = ytd_db1 - ytd_variable
            
            # TAG 181: Stückzahlen für YTD in erweiterter Struktur berechnen
            stueckzahlen_ytd = _berechne_stueckzahlen_erweitert(monat, jahr, firma, standort)
            # Stückzahlen zu NW und GW Bereichen hinzufügen (erweiterte Struktur für YTD)
            # TAG182: Korrektur - vollständige Struktur verwenden, nicht nur 'jahr'
            for bereich in ytd_bereiche:
                if bereich['key'] == 'NW':
                    bereich['stueck'] = stueckzahlen_ytd['nw']  # Vollständige Struktur: {monat, jahr, vj_monat, vj_jahr}
                elif bereich['key'] == 'GW':
                    bereich['stueck'] = stueckzahlen_ytd['gw']  # Vollständige Struktur: {monat, jahr, vj_monat, vj_jahr}
                else:
                    bereich['stueck'] = {'monat': 0, 'jahr': 0, 'vj_monat': 0, 'vj_jahr': 0}

            # YTD Direkte Kosten
            # TAG182: Landau - 6. Ziffer='2' für Kosten (nicht branch_number=3, da Kosten hauptsächlich branch=1 haben)!
            if standort == '2' and firma == '1':
                ytd_direkte_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
            else:
                ytd_direkte_kosten_filter = firma_filter_kosten
            
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 400000 AND 489999
                  {direkte_kst_filter}
          AND NOT (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR (nominal_account_number BETWEEN 489000 AND 489999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
                  {ytd_direkte_kosten_filter}
                  {guv_filter}
            """), (ytd_datum_von, datum_bis) + tuple(direkte_kst_params))
            ytd_direkte = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            ytd_db3 = ytd_db2 - ytd_direkte

            # YTD Indirekte Kosten
            # TAG182: Landau - 6. Ziffer='2' für Kosten (nicht branch_number=3, da Kosten hauptsächlich branch=1 haben)!
            if standort == '2' and firma == '1':
                ytd_indirekte_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
            else:
                ytd_indirekte_kosten_filter = firma_filter_kosten
            
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  {indirekte_kst_filter}
                  AND NOT (
                    nominal_account_number = 410021
                    OR nominal_account_number BETWEEN 411000 AND 411999
                    OR (nominal_account_number BETWEEN 489000 AND 489999
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                  )
                  {ytd_indirekte_kosten_filter}
                  {guv_filter}
            """), (ytd_datum_von, datum_bis))
            ytd_indirekte = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            ytd_be = ytd_db3 - ytd_indirekte

            # YTD Neutrales Ergebnis
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 200000 AND 299999
                  {firma_filter_umsatz}
                  {guv_filter}
            """), (ytd_datum_von, datum_bis))
            ytd_neutral = float(row_to_dict(cursor.fetchone())['wert'] or 0)

            ytd_ue = ytd_be + ytd_neutral

            # TAG 181: YTD Vorjahr berechnen (für Vergleich)
            ytd_vorjahr_daten = _berechne_bwa_ytd(cursor, monat, jahr - 1, firma, standort)
            ytd_vorjahr_umsatz = ytd_vorjahr_daten.get('umsatz', 0)
            ytd_vorjahr_einsatz = ytd_vorjahr_daten.get('einsatz', 0)
            ytd_vorjahr_db1 = ytd_vorjahr_daten.get('db1', 0)
            ytd_vorjahr_bereiche = ytd_vorjahr_daten.get('bereiche', [])
            # TAG 181: KST-Filter auf YTD Vorjahr-Bereiche anwenden
            if relevante_bereiche is not None:
                ytd_vorjahr_bereiche = [b for b in ytd_vorjahr_bereiche if b.get('key') in relevante_bereiche]
            ytd_vorjahr_variable = ytd_vorjahr_daten.get('variable_kosten', 0)
            ytd_vorjahr_db2 = ytd_vorjahr_daten.get('db2', 0)
            ytd_vorjahr_direkte = ytd_vorjahr_daten.get('direkte_kosten', 0)
            ytd_vorjahr_db3 = ytd_vorjahr_daten.get('db3', 0)
            ytd_vorjahr_indirekte = ytd_vorjahr_daten.get('indirekte_kosten', 0)
            ytd_vorjahr_be = ytd_vorjahr_daten.get('betriebsergebnis', 0)
            ytd_vorjahr_neutral = ytd_vorjahr_daten.get('neutrales_ergebnis', 0)
            ytd_vorjahr_ue = ytd_vorjahr_daten.get('unternehmensergebnis', 0)
            
            # TAG 181: Stückzahlen für YTD Vorjahr in erweiterter Struktur berechnen
            stueckzahlen_ytd_vorjahr = _berechne_stueckzahlen_erweitert(monat, jahr - 1, firma, standort)
            # Stückzahlen zu NW und GW Bereichen hinzufügen (erweiterte Struktur für YTD Vorjahr)
            # TAG182: Korrektur - vollständige Struktur verwenden, nicht nur 'jahr'
            for bereich in ytd_vorjahr_bereiche:
                if bereich['key'] == 'NW':
                    bereich['stueck'] = stueckzahlen_ytd_vorjahr['nw']  # Vollständige Struktur: {monat, jahr, vj_monat, vj_jahr}
                elif bereich['key'] == 'GW':
                    bereich['stueck'] = stueckzahlen_ytd_vorjahr['gw']  # Vollständige Struktur: {monat, jahr, vj_monat, vj_jahr}
                else:
                    bereich['stueck'] = {'monat': 0, 'jahr': 0, 'vj_monat': 0, 'vj_jahr': 0}

            # Wirtschaftsjahr-Fortschritt berechnen (Sep-Aug = 12 Monate)
            if monat >= WJ_START_MONAT:
                wj_monat = monat - WJ_START_MONAT + 1  # Sep=1, Okt=2, ...
            else:
                wj_monat = monat + (12 - WJ_START_MONAT + 1)  # Jan=5, Feb=6, ...
            wj_progress = round(wj_monat / 12 * 100, 1)

            return jsonify({
                'status': 'ok',
                'monat': monat,
                'monat_name': MONAT_NAMEN.get(monat, str(monat)),
                'jahr': jahr,
                'standort_name': standort_name,
                'wj_monat': wj_monat,
                'wj_progress': wj_progress,
                'aktuell': {
                    'umsatz': round(umsatz_gesamt, 2),
                    'einsatz': round(einsatz_gesamt, 2),
                    'db1': round(db1_gesamt, 2),
                    'bereiche': bereiche,
                    'variable_kosten': round(variable_kosten, 2),
                    'db2': round(db2, 2),
                    'direkte_kosten': round(direkte_kosten, 2),
                    'db3': round(db3, 2),
                    'indirekte_kosten': round(indirekte_kosten, 2),
                    'betriebsergebnis': round(betriebsergebnis, 2),
                    'neutrales_ergebnis': round(neutrales_ergebnis, 2),
                    'unternehmensergebnis': round(unternehmensergebnis, 2)
                },
                'vorjahr': {
                    'umsatz': round(vj_umsatz, 2),
                    'einsatz': round(vj_einsatz, 2),
                    'db1': round(vj_db1, 2),
                    'bereiche': vj_bereiche,
                    'variable_kosten': round(vj_variable, 2),
                    'db2': round(vj_db2, 2),
                    'direkte_kosten': round(vj_direkte, 2),
                    'db3': round(vj_db3, 2),
                    'indirekte_kosten': round(vj_indirekte, 2),
                    'betriebsergebnis': round(vj_be, 2),
                    'neutrales_ergebnis': round(vj_neutral, 2),
                    'unternehmensergebnis': round(vj_ue, 2)
                },
                'ytd': {
                    'umsatz': round(ytd_umsatz, 2),
                    'einsatz': round(ytd_einsatz, 2),
                    'db1': round(ytd_db1, 2),
                    'bereiche': ytd_bereiche,
                    'variable_kosten': round(ytd_variable, 2),
                    'db2': round(ytd_db2, 2),
                    'direkte_kosten': round(ytd_direkte, 2),
                    'db3': round(ytd_db3, 2),
                    'indirekte_kosten': round(ytd_indirekte, 2),
                    'betriebsergebnis': round(ytd_be, 2),
                    'neutrales_ergebnis': round(ytd_neutral, 2),
                    'unternehmensergebnis': round(ytd_ue, 2)
                },
                'stueckzahlen': stueckzahlen,
                'ytd_vorjahr': {
                    'umsatz': round(ytd_vorjahr_umsatz, 2),
                    'einsatz': round(ytd_vorjahr_einsatz, 2),
                    'db1': round(ytd_vorjahr_db1, 2),
                    'bereiche': ytd_vorjahr_bereiche,
                    'variable_kosten': round(ytd_vorjahr_variable, 2),
                    'db2': round(ytd_vorjahr_db2, 2),
                    'direkte_kosten': round(ytd_vorjahr_direkte, 2),
                    'db3': round(ytd_vorjahr_db3, 2),
                    'indirekte_kosten': round(ytd_vorjahr_indirekte, 2),
                    'betriebsergebnis': round(ytd_vorjahr_be, 2),
                    'neutrales_ergebnis': round(ytd_vorjahr_neutral, 2),
                    'unternehmensergebnis': round(ytd_vorjahr_ue, 2)
                },
                'filter': {
                    'firma': firma,
                    'standort': standort,
                    'standort_name': standort_name
                }
            })

    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


# =============================================================================
# BWA v2 Drill-Down API - Detailansicht für Bereiche und Kostenarten
# =============================================================================

# SKR51 Kontenbezeichnungen (häufig verwendete Konten)
SKR51_KONTEN = {
    # Erlöse Neuwagen
    810100: "Fahrzeugerlöse NW", 810200: "Fahrzeugerlöse NW Hyundai",
    811100: "Ersatzteil-Erlöse NW", 812100: "Zubehör-Erlöse NW",
    # Erlöse Gebrauchtwagen
    820100: "Fahrzeugerlöse GW", 821100: "Ersatzteil-Erlöse GW",
    # Erlöse Teile
    830100: "Ersatzteil-Erlöse Theke", 830200: "Ersatzteil-Erlöse Werkstatt",
    831100: "Zubehör-Erlöse", 832100: "Reifen-Erlöse",
    # Erlöse Mechanik
    840100: "Lohn-Erlöse Mechanik", 840200: "Lohn-Erlöse Karosserie",
    841100: "Lohn-Erlöse Lack", 842100: "Lohn-Erlöse Service",
    # Erlöse Sonstige
    860100: "Mietwagen-Erlöse", 880100: "Sonstige Erlöse",
    893200: "Zinserträge",
    # Einsatz Neuwagen
    710100: "Fahrzeugeinsatz NW", 711100: "Ersatzteil-Einsatz NW",
    # Einsatz Gebrauchtwagen
    720100: "Fahrzeugeinsatz GW", 721100: "Ersatzteil-Einsatz GW",
    # Einsatz Teile
    730100: "Ersatzteil-Einsatz", 731100: "Zubehör-Einsatz",
    # Einsatz Mechanik
    740100: "Lohn-Einsatz Fremdleistungen", 741100: "Material-Einsatz",
    # Variable Kosten
    415100: "Garantie-Aufwand", 435500: "Kfz-Kosten Vorführwagen",
    455100: "Werbekosten", 487000: "Versicherungen",
    491000: "Provisionen", 492000: "Boni und Prämien",
    # Direkte Kosten
    400100: "Personalkosten", 401000: "Gehälter",
    420100: "Raumkosten", 430100: "Fahrzeugkosten",
    # Indirekte Kosten
    400000: "Personalkosten Gemein", 420000: "Raumkosten Gemein",
    430000: "Fahrzeugkosten Gemein", 440000: "Verwaltungskosten",
    891000: "Abschreibungen", 895000: "Zinsen und ähnliche Aufwendungen",
    # Neutrales Ergebnis
    200000: "Neutrale Erträge", 260000: "Sonstige Erträge",
    270000: "Periodenfremde Erträge", 280000: "Außerordentliche Erträge",
}


def _get_konto_bezeichnung(konto: int) -> str:
    """Liefert die Bezeichnung für ein SKR51-Konto."""
    # Exakte Übereinstimmung
    if konto in SKR51_KONTEN:
        return SKR51_KONTEN[konto]

    # Generische Bezeichnung basierend auf Kontenklasse
    prefix = str(konto)[:2]
    kontenklassen = {
        '81': 'Erlöse Neuwagen',
        '82': 'Erlöse Gebrauchtwagen',
        '83': 'Erlöse Teile',
        '84': 'Erlöse Mechanik/Lohn',
        '85': 'Erlöse Lack/Karosserie',
        '86': 'Erlöse Mietwagen',
        '88': 'Sonstige Erlöse',
        '89': 'Sonstige betriebliche Erträge',
        '71': 'Einsatz Neuwagen',
        '72': 'Einsatz Gebrauchtwagen',
        '73': 'Einsatz Teile',
        '74': 'Einsatz Mechanik',
        '75': 'Einsatz Lack/Karosserie',
        '76': 'Einsatz Mietwagen',
        '40': 'Personalkosten',
        '41': 'Personalnebenkosten',
        '42': 'Raumkosten',
        '43': 'Fahrzeugkosten',
        '44': 'Verwaltungskosten',
        '45': 'Werbekosten',
        '46': 'Versicherungen',
        '47': 'Reparaturen/Instandhaltung',
        '48': 'Sonstige Kosten',
        '49': 'Provisionen/Boni',
        '20': 'Neutrale Erträge',
        '21': 'Zinserträge',
        '26': 'Sonstige neutrale Erträge',
        '27': 'Periodenfremde Erträge',
    }

    return kontenklassen.get(prefix, f"Konto {konto}")


@controlling_api.route('/api/controlling/bwa/v2/drilldown', methods=['GET'])
def get_bwa_v2_drilldown():
    """
    Drill-Down Details für BWA v2.

    Query-Parameter:
        typ: 'bereich' | 'variable' | 'direkte' | 'indirekte' | 'neutral'
        bereich: NW/GW/ME/TZ/MW/SO (nur bei typ=bereich)
        monat: int (1-12)
        jahr: int (z.B. 2025)
        firma: 0=Alle, 1=Stellantis, 2=Hyundai
        standort: 0=Alle, 1=Deggendorf, 2=Landau
    """
    try:
        typ = request.args.get('typ', 'bereich')
        bereich = request.args.get('bereich', 'NW')
        monat = request.args.get('monat', type=int)
        jahr = request.args.get('jahr', type=int)
        firma = request.args.get('firma', '0')
        standort = request.args.get('standort', '0')

        if not monat or not jahr:
            heute = datetime.now()
            monat = monat or heute.month
            jahr = jahr or heute.year

        datum_von = f"{jahr}-{monat:02d}-01"
        if monat == 12:
            datum_bis = f"{jahr+1}-01-01"
        else:
            datum_bis = f"{jahr}-{monat+1:02d}-01"

        # TAG157: Jetzt mit separatem Einsatz-Filter!
        firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, standort_name = build_firma_standort_filter(firma, standort)
        # TAG 179: Zentrale Funktion verwenden
        guv_filter = get_guv_filter()

        # Subsidiary für Kontobezeichnungen: 1=Stellantis, 2=Hyundai
        subsidiary = 2 if firma == '2' else 1

        with db_session() as conn:
            cursor = conn.cursor()

            details = []
            titel = ""
            summe = 0

            if typ == 'umsatz':
                # Alle Umsatzerlöse (8xxxxx) - gruppiert nach Kostenstellen
                titel = "Umsatzerlöse nach Kostenstellen"
                cursor.execute(convert_placeholders(f"""
                    SELECT
                        nominal_account_number as konto,
                        SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN 800000 AND 899999
                      {firma_filter_umsatz}
                      {guv_filter}
                    GROUP BY nominal_account_number
                    HAVING ABS(SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)) > 0
                    ORDER BY nominal_account_number
                """), (datum_von, datum_bis))

                # Bereich-Mapping basierend auf Konto-Präfix (erste 2 Ziffern)
                # SKR51: 81=NW, 82=GW, 83=TZ, 84=ME, 86=MW, 88/89=SO
                def get_bereich_from_konto(konto):
                    prefix = str(konto)[:2]
                    mapping = {
                        '81': ('NW', 'Neuwagen', 1),
                        '82': ('GW', 'Gebrauchtwagen', 2),
                        '83': ('TZ', 'Teile & Zubehör', 3),
                        '84': ('ME', 'Werkstatt (ME)', 4),
                        '85': ('MW', 'Miete/Waschen', 5),
                        '86': ('MW', 'Miete/Waschen', 5),
                        '87': ('SO', 'Sonstige', 6),
                        '88': ('SO', 'Sonstige', 6),
                        '89': ('SO', 'Sonstige', 6),
                    }
                    return mapping.get(prefix, ('SO', 'Sonstige', 99))

                for row in cursor.fetchall():
                    r = row_to_dict(row)
                    konto = r['konto']
                    wert = float(r['wert'] or 0)
                    bereich_code, bereich_name, bereich_order = get_bereich_from_konto(konto)
                    details.append({
                        'konto': konto,
                        'bezeichnung': get_konto_bezeichnung(conn, konto, subsidiary),
                        'wert': round(wert, 2),
                        'typ': 'Erlös',
                        'bereich': bereich_code,
                        'bereich_name': bereich_name,
                        'bereich_order': bereich_order
                    })
                    summe += wert

                # Nach Bereich sortieren, dann nach Wert
                details.sort(key=lambda x: (x['bereich_order'], -x['wert']))

            elif typ == 'einsatz':
                # Alle Einsatzwerte (7xxxxx) - TAG157: firma_filter_einsatz!
                titel = "Einsatzwerte"
                cursor.execute(convert_placeholders(f"""
                    SELECT
                        nominal_account_number as konto,
                        SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN 700000 AND 799999
                      {firma_filter_einsatz}
                      {guv_filter}
                    GROUP BY nominal_account_number
                    HAVING ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)) > 0
                    ORDER BY wert DESC
                """), (datum_von, datum_bis))

                for row in cursor.fetchall():
                    r = row_to_dict(row)
                    konto = r['konto']
                    wert = float(r['wert'] or 0)
                    details.append({
                        'konto': konto,
                        'bezeichnung': get_konto_bezeichnung(conn, konto, subsidiary),
                        'wert': round(wert, 2),
                        'typ': 'Einsatz'
                    })
                    summe += wert

            elif typ == 'bereich':
                # Bereich-Details: Erlös + Einsatz pro Modell matchen mit DB% und Stück
                config = BEREICHE_CONFIG.get(bereich)
                if not config:
                    return jsonify({'status': 'error', 'message': f'Unbekannter Bereich: {bereich}'}), 400

                titel = f"Bruttoertrag {config['name']} ({bereich})"

                # Erlös-Prefix und Einsatz-Prefix bestimmen
                if 'erlos_prefix' in config:
                    erlos_prefix = config['erlos_prefix']
                    einsatz_prefix = config['einsatz_prefix']
                    erlos_where = f"nominal_account_number BETWEEN {erlos_prefix}0000 AND {erlos_prefix}9999"
                    einsatz_where = f"nominal_account_number BETWEEN {einsatz_prefix}0000 AND {einsatz_prefix}9999"
                else:
                    erlos_start, erlos_end = config['erlos_range']
                    einsatz_start, einsatz_end = config['einsatz_range']
                    erlos_where = f"nominal_account_number BETWEEN {erlos_start} AND {erlos_end}"
                    einsatz_where = f"nominal_account_number BETWEEN {einsatz_start} AND {einsatz_end}"

                # Query: Erlös pro Modell mit Stückzahl
                cursor.execute(convert_placeholders(f"""
                    SELECT
                        nominal_account_number as konto,
                        SUBSTRING(CAST(nominal_account_number AS TEXT), 3, 4) as modell_key,
                        SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert,
                        COUNT(DISTINCT CASE WHEN vehicle_reference IS NOT NULL AND vehicle_reference != ''
                              THEN vehicle_reference END) as stueck
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND {erlos_where}
                      {firma_filter_umsatz}
                      {guv_filter}
                    GROUP BY nominal_account_number
                    HAVING ABS(SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)) > 0
                    ORDER BY wert DESC
                """), (datum_von, datum_bis))

                erlos_data = {}
                for row in cursor.fetchall():
                    r = row_to_dict(row)
                    modell_key = r['modell_key']
                    erlos_data[modell_key] = {
                        'konto': r['konto'],
                        'wert': float(r['wert'] or 0),
                        'stueck': int(r['stueck'] or 0)
                    }

                # Query: Einsatz pro Modell
                cursor.execute(convert_placeholders(f"""
                    SELECT
                        nominal_account_number as konto,
                        SUBSTRING(CAST(nominal_account_number AS TEXT), 3, 4) as modell_key,
                        SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND {einsatz_where}
                      {firma_filter_umsatz}
                      {guv_filter}
                    GROUP BY nominal_account_number
                    HAVING ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)) > 0
                """), (datum_von, datum_bis))

                einsatz_data = {}
                for row in cursor.fetchall():
                    r = row_to_dict(row)
                    modell_key = r['modell_key']
                    einsatz_data[modell_key] = {
                        'konto': r['konto'],
                        'wert': float(r['wert'] or 0)
                    }

                # Matching: Pro Modell Erlös + Einsatz kombinieren
                erlos_gesamt = 0
                einsatz_gesamt = 0

                for modell_key, erlos in erlos_data.items():
                    erloes_wert = erlos['wert']
                    einsatz = einsatz_data.get(modell_key)
                    einsatz_wert = -einsatz['wert'] if einsatz else 0  # Einsatz als negativ
                    db = erloes_wert + einsatz_wert
                    db_pct = (db / erloes_wert * 100) if erloes_wert != 0 else 0
                    stueck = erlos['stueck']
                    db_pro_stueck = (db / stueck) if stueck > 0 else None

                    details.append({
                        'konto': erlos['konto'],
                        'bezeichnung': get_konto_bezeichnung(conn, erlos['konto'], subsidiary),
                        'wert': round(erloes_wert, 2),
                        'einsatz': round(einsatz_wert, 2),
                        'db': round(db, 2),
                        'db_pct': round(db_pct, 1),
                        'stueck': stueck,
                        'db_pro_stueck': round(db_pro_stueck, 0) if db_pro_stueck else None,
                        'typ': 'Erlös'
                    })

                    erlos_gesamt += erloes_wert
                    einsatz_gesamt += einsatz_wert

                # Sortiere nach Erlös absteigend
                details.sort(key=lambda x: x['wert'], reverse=True)
                summe = erlos_gesamt + einsatz_gesamt  # DB1 Gesamt

            elif typ == 'variable':
                titel = "Variable Kosten"
                cursor.execute(convert_placeholders(f"""
                    SELECT
                        nominal_account_number as konto,
                        SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND (
                        nominal_account_number BETWEEN 415100 AND 415199
                        OR nominal_account_number BETWEEN 435500 AND 435599
                        OR (nominal_account_number BETWEEN 455000 AND 456999
                            AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                        OR (nominal_account_number BETWEEN 487000 AND 487099
                            AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                        OR nominal_account_number BETWEEN 491000 AND 497899
                        OR nominal_account_number BETWEEN 891000 AND 891099
                      )
                      {firma_filter_kosten}
                      {guv_filter}
                    GROUP BY nominal_account_number
                    HAVING ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)) > 0
                    ORDER BY wert DESC
                """), (datum_von, datum_bis))

                for row in cursor.fetchall():
                    r = row_to_dict(row)
                    konto = r['konto']
                    wert = float(r['wert'] or 0)
                    details.append({
                        'konto': konto,
                        'bezeichnung': get_konto_bezeichnung(conn, konto, subsidiary),
                        'wert': round(wert, 2),
                        'typ': 'Kosten'
                    })
                    summe += wert

            elif typ == 'direkte':
                titel = "Direkte Kosten (Abteilungsbezogen)"
                cursor.execute(convert_placeholders(f"""
                    SELECT
                        nominal_account_number as konto,
                        SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN 400000 AND 489999
                      AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND NOT (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR (nominal_account_number BETWEEN 489000 AND 489999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
                      {firma_filter_kosten}
                      {guv_filter}
                    GROUP BY nominal_account_number
                    HAVING ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)) > 0
                    ORDER BY wert DESC
                """), (datum_von, datum_bis))

                for row in cursor.fetchall():
                    r = row_to_dict(row)
                    konto = r['konto']
                    wert = float(r['wert'] or 0)
                    details.append({
                        'konto': konto,
                        'bezeichnung': get_konto_bezeichnung(conn, konto, subsidiary),
                        'wert': round(wert, 2),
                        'typ': 'Kosten'
                    })
                    summe += wert

            elif typ == 'indirekte':
                titel = "Indirekte Kosten (Gemeinkosten)"
                cursor.execute(convert_placeholders(f"""
                    SELECT
                        nominal_account_number as konto,
                        SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND (
                        (nominal_account_number BETWEEN 400000 AND 499999
                         AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
                        OR (nominal_account_number BETWEEN 424000 AND 424999
                            AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                        OR (nominal_account_number BETWEEN 438000 AND 438999
                            AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                        OR nominal_account_number BETWEEN 498000 AND 499999
                        OR (nominal_account_number BETWEEN 891000 AND 896999
                            AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
                            AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
                      )
                      {firma_filter_kosten}
                      {guv_filter}
                    GROUP BY nominal_account_number
                    HAVING ABS(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)) > 0
                    ORDER BY wert DESC
                """), (datum_von, datum_bis))

                for row in cursor.fetchall():
                    r = row_to_dict(row)
                    konto = r['konto']
                    wert = float(r['wert'] or 0)
                    details.append({
                        'konto': konto,
                        'bezeichnung': get_konto_bezeichnung(conn, konto, subsidiary),
                        'wert': round(wert, 2),
                        'typ': 'Kosten'
                    })
                    summe += wert

            elif typ == 'neutral':
                titel = "Neutrales Ergebnis"
                cursor.execute(convert_placeholders(f"""
                    SELECT
                        nominal_account_number as konto,
                        SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as wert
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN 200000 AND 299999
                      {firma_filter_umsatz}
                      {guv_filter}
                    GROUP BY nominal_account_number
                    HAVING ABS(SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)) > 0
                    ORDER BY wert DESC
                """), (datum_von, datum_bis))

                for row in cursor.fetchall():
                    r = row_to_dict(row)
                    konto = r['konto']
                    wert = float(r['wert'] or 0)
                    details.append({
                        'konto': konto,
                        'bezeichnung': get_konto_bezeichnung(conn, konto, subsidiary),
                        'wert': round(wert, 2),
                        'typ': 'Ertrag' if wert > 0 else 'Aufwand'
                    })
                    summe += wert

            return jsonify({
                'status': 'ok',
                'titel': titel,
                'monat_name': MONAT_NAMEN.get(monat, str(monat)),
                'jahr': jahr,
                'details': details,
                'summe': round(summe, 2),
                'anzahl': len(details)
            })

    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500
