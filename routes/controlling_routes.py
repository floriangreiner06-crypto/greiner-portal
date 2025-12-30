from flask import Blueprint, render_template, jsonify, request
from decorators.auth_decorators import login_required
import re
from datetime import datetime, date, timedelta
import calendar
import psycopg2.extras

# TAG 136: PostgreSQL-Migration - Nutze db_utils fÃ¼r Portal-DB
from api.db_utils import db_session, row_to_dict, rows_to_list, locosoft_session
from api.db_connection import convert_placeholders, sql_placeholder, get_db_type

# =============================================================================
# WERKTAGE-BERECHNUNG (TAG121)
# =============================================================================

# Bayerische Feiertage 2025
FEIERTAGE_2025 = [
    datetime(2025, 1, 1),    # Neujahr
    datetime(2025, 1, 6),    # Heilige Drei KÃ¶nige
    datetime(2025, 4, 18),   # Karfreitag
    datetime(2025, 4, 21),   # Ostermontag
    datetime(2025, 5, 1),    # Tag der Arbeit
    datetime(2025, 5, 29),   # Christi Himmelfahrt
    datetime(2025, 6, 9),    # Pfingstmontag
    datetime(2025, 6, 19),   # Fronleichnam
    datetime(2025, 8, 15),   # MariÃ¤ Himmelfahrt
    datetime(2025, 10, 3),   # Tag der Deutschen Einheit
    datetime(2025, 11, 1),   # Allerheiligen
    datetime(2025, 12, 25),  # 1. Weihnachtstag
    datetime(2025, 12, 26),  # 2. Weihnachtstag
]


def get_werktage(start_date, end_date, include_end=False):
    """Berechnet Werktage zwischen zwei Daten (Mo-Fr, ohne Feiertage)"""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

    if not include_end:
        end_date = end_date - timedelta(days=1)

    werktage = 0
    current = start_date

    while current <= end_date:
        if current.weekday() < 5 and current not in FEIERTAGE_2025:
            werktage += 1
        current += timedelta(days=1)

    return werktage


def get_werktage_monat(jahr, monat):
    """Berechnet Werktage im Monat: {gesamt, vergangen, verbleibend, fortschritt_prozent}"""
    erster_tag = datetime(jahr, monat, 1)
    letzter_tag = datetime(jahr, monat, calendar.monthrange(jahr, monat)[1])
    heute = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    werktage_gesamt = get_werktage(erster_tag, letzter_tag, include_end=True)

    if heute.year == jahr and heute.month == monat:
        werktage_vergangen = get_werktage(erster_tag, heute, include_end=True)
        werktage_verbleibend = werktage_gesamt - werktage_vergangen
    else:
        werktage_vergangen = werktage_gesamt
        werktage_verbleibend = 0

    fortschritt = (werktage_vergangen / werktage_gesamt * 100) if werktage_gesamt > 0 else 100

    return {
        'gesamt': werktage_gesamt,
        'vergangen': werktage_vergangen,
        'verbleibend': werktage_verbleibend,
        'fortschritt_prozent': round(fortschritt, 1),
        'ist_aktueller_monat': heute.year == jahr and heute.month == monat,
    }


def get_db():
    """
    TAG 136: Portal-DB Verbindung via db_utils (SQLite oder PostgreSQL).
    Gibt direkte Connection zurÃ¼ck (MUSS manuell geschlossen werden!).
    FÃ¼r neue Code: Bevorzuge db_session() Context Manager.
    """
    from api.db_connection import get_db as get_portal_db
    return get_portal_db()


def get_locosoft_db():
    """PostgreSQL-Verbindung zu externer Locosoft DB (10.80.80.8)"""
    return locosoft_session()


# =============================================================================
# MODELL-NORMALISIERUNG fÃ¼r Locosoft
# =============================================================================
# Extrahiert Basis-Modellname aus detaillierten Locosoft-Bezeichnungen

MODELL_MAPPING = {
    # Opel/Stellantis
    'astra': 'Astra',
    'corsa': 'Corsa',
    'mokka': 'Mokka',
    'grandland': 'Grandland',
    'crossland': 'Crossland',
    'combo': 'Combo',
    'vivaro': 'Vivaro',
    'movano': 'Movano',
    'zafira': 'Zafira',
    'frontera': 'Frontera',
    # Leapmotor
    'b10': 'Leapmotor B10',
    't03': 'Leapmotor T03',
    'c10': 'Leapmotor C10',
    # Hyundai
    'kona': 'Kona',
    'tucson': 'Tucson',
    'i10': 'i10',
    'i20': 'i20',
    'i30': 'i30',
    'ioniq': 'Ioniq',
    'inster': 'Inster',
    'santa': 'Santa Fe',
    'bayon': 'Bayon',
    'staria': 'Staria',
}


def normalisiere_locosoft_modell(description: str) -> str:
    """
    Extrahiert Basis-Modellname aus Locosoft models.description.

    Beispiele:
    - "Astra, Sports Tourer, Edition, 1.5 Diesel" -> "Astra"
    - "KONA SX2 (MY26) 1.6 T-GDI..." -> "Kona"
    - "B10 BEV Design Promax" -> "Leapmotor B10"
    """
    if not description:
        return 'Sonstige'

    # Lowercase fÃ¼r Matching
    desc_lower = description.lower().strip()

    # Bekannte Modelle suchen
    for key, name in MODELL_MAPPING.items():
        if desc_lower.startswith(key) or f' {key}' in desc_lower or f'/{key}' in desc_lower:
            return name

    # Fallback: Erstes Wort (bis Komma, Klammer oder Leerzeichen)
    match = re.match(r'^([A-Za-z0-9]+)', description)
    if match:
        return match.group(1)

    return 'Sonstige'


def normalisiere_fibu_modell(modell: str) -> str:
    """
    Normalisiert FiBu-Modellname zum gleichen Format wie Locosoft.

    Beispiele:
    - "IONIQ5" -> "Ioniq"
    - "IONIQ 6" -> "Ioniq"
    - "SantaFe" -> "Santa Fe"
    - "T03" -> "Leapmotor T03"
    """
    if not modell:
        return 'Sonstige'

    # Lowercase fÃ¼r Matching
    modell_lower = modell.lower().strip()

    # Bekannte Modelle suchen
    for key, name in MODELL_MAPPING.items():
        if modell_lower.startswith(key) or f' {key}' in modell_lower or modell_lower == key:
            return name

    # Spezialfall: IONIQ5, IONIQ6, IONIQ9 -> Ioniq
    if modell_lower.startswith('ioniq'):
        return 'Ioniq'

    # Spezialfall: SantaFe -> Santa Fe (zusammengeschrieben)
    if 'santafe' in modell_lower or 'santa' in modell_lower:
        return 'Santa Fe'

    # Fallback: Ersten Buchstaben groÃŸ, Rest klein
    return modell.strip()


def get_stueckzahlen_locosoft(von: str, bis: str, bereich: str = '1-NW', firma: str = '0', standort: str = '0') -> dict:
    """
    Holt Fahrzeug-StÃ¼ckzahlen aus Locosoft dealer_vehicles.

    Returns: {
        'modelle': {
            'Astra': {'stueck': 6, 'gesamt_vk': 220000, 'avg_vk': 36666},
            'Corsa': {'stueck': 4, 'gesamt_vk': 80000, 'avg_vk': 20000},
            ...
        },
        'gesamt_stueck': 10
    }
    """
    try:
        # Fahrzeugtyp basierend auf Bereich
        fzg_typ = 'N' if bereich == '1-NW' else 'G'  # N=Neuwagen, G=Gebrauchtwagen

        # Standort-Filter (location in dealer_vehicles)
        # Locosoft locations: DEGO=Deggendorf Opel, DEGH=Deggendorf Hyundai, LANO=Landau Opel
        standort_filter = ""
        if firma == '1':  # Stellantis (Opel/Leapmotor)
            standort_filter = "AND dv.location IN ('DEGO', 'LANO')"  # Beide Stellantis-Standorte
            if standort == '1':
                standort_filter = "AND dv.location = 'DEGO'"  # Nur Deggendorf
            elif standort == '2':
                standort_filter = "AND dv.location = 'LANO'"  # Nur Landau
        elif firma == '2':  # Hyundai
            standort_filter = "AND dv.location = 'DEGH'"  # Hyundai-Standort

        # locosoft_session() ist ein Context Manager!
        with locosoft_session() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # out_invoice_date statt out_sales_contract_date fÃ¼r Matching mit FiBu
            cur.execute(f"""
                SELECT
                    COALESCE(m.description, 'Unbekannt') as modell_raw,
                    COUNT(*) as stueck,
                    SUM(dv.out_sale_price) as gesamt_vk_raw,
                    AVG(dv.out_sale_price) as avg_vk_raw
                FROM dealer_vehicles dv
                JOIN vehicles v ON v.internal_number = dv.vehicle_number
                LEFT JOIN models m ON v.model_code = m.model_code AND v.make_number = m.make_number
                WHERE dv.out_invoice_date >= %s
                  AND dv.out_invoice_date < %s
                  AND dv.dealer_vehicle_type = %s
                  AND dv.out_sale_price > 0
                  {standort_filter}
                GROUP BY m.description
                ORDER BY stueck DESC
            """, (von, bis, fzg_typ))

            rows = cur.fetchall()
            cur.close()

        # Nach Basis-Modell gruppieren (auÃŸerhalb des with-Blocks)
        modelle = {}
        gesamt_stueck = 0

        for row in rows:
            basis_modell = normalisiere_locosoft_modell(row['modell_raw'])

            if basis_modell not in modelle:
                modelle[basis_modell] = {
                    'stueck': 0,
                    'gesamt_vk': 0,
                    'varianten': []
                }

            modelle[basis_modell]['stueck'] += row['stueck']
            modelle[basis_modell]['gesamt_vk'] += float(row['gesamt_vk_raw'] or 0) / 100.0  # Cent -> Euro
            modelle[basis_modell]['varianten'].append(row['modell_raw'])
            gesamt_stueck += row['stueck']

        # Durchschnitts-VK berechnen
        for m in modelle.values():
            m['avg_vk'] = round(m['gesamt_vk'] / m['stueck'], 2) if m['stueck'] > 0 else 0
            m['gesamt_vk'] = round(m['gesamt_vk'], 2)

        return {
            'modelle': modelle,
            'gesamt_stueck': gesamt_stueck
        }

    except Exception as e:
        import traceback
        print(f"[STUECK] Locosoft-Abfrage fehlgeschlagen: {e}")
        traceback.print_exc()
        return {'modelle': {}, 'gesamt_stueck': 0, 'error': str(e)}


controlling_bp = Blueprint('controlling', __name__, url_prefix='/controlling')

# =============================================================================
# KONSTANTEN: MA-VERTEILUNG FÃœR UMLAGE
# =============================================================================
# Wird dynamisch aus DB geladen, aber als Fallback hier definiert
DEFAULT_MA_VERTEILUNG = {
    '0': 11,   # Verwaltung (wird umgelegt)
    '12': 19,  # Verkauf (NW+GW)
    '3': 30,   # Service
    '6': 11    # Teile
}

# =============================================================================
# UMLAGE-KONTEN (interne Verrechnung zwischen Stellantis und Hyundai)
# =============================================================================
# Diese Konten sind "linke Tasche, rechte Tasche" - heben sich auf Konzernebene auf
# Bei Einzelbetrachtung verzerren sie die echte Performance
#
# ERLÃ–SE bei Stellantis (Autohaus Greiner bekommt):
#   817051 = Kostenumlage NW        ~12.500 â‚¬/Monat
#   827051 = Kostenumlage GW        ~12.500 â‚¬/Monat  
#   837051 = Kostenumlage Werkstatt ~12.500 â‚¬/Monat
#   847051 = Kostenumlage Teile     ~12.500 â‚¬/Monat
#   SUMME:                          ~50.000 â‚¬/Monat
#
# KOSTEN bei Hyundai (Auto Greiner zahlt) - als HABEN gebucht!
#   498001 = Kostenumlage Haupt     ~50.000 â‚¬/Monat
#   415001 = Kostenumlage Personal  ~ 5.000 â‚¬/Monat (+ echte Personalkosten SOLL)
#   440001 = Kostenumlage Miete     ~ 2.500 â‚¬/Monat (+ echte Mietkosten SOLL)
#   461001 = Kostenumlage Versich.  ~   500 â‚¬/Monat (+ echte Versicherungen SOLL)
#   462001 = Kostenumlage BeitrÃ¤ge  ~   500 â‚¬/Monat (+ echte BeitrÃ¤ge SOLL)
#   SUMME:                          ~58.500 â‚¬/Monat
#
# WICHTIG: Die Konten 415001, 440001, 461001, 462001 haben DOPPELTE Verwendung:
#   - Echte Kosten (SOLL-Buchungen): Miete Fischer, Lohn/Gehalt, etc.
#   - Interne Umlage (HABEN-Buchungen): "Kostenumlage AH Greiner"
# Daher filtern wir nach BUCHUNGSTEXT, nicht nur nach Kontonummer!
#
UMLAGE_ERLOESE_KONTEN = [817051, 827051, 837051, 847051]
UMLAGE_KOSTEN_KONTEN = [498001]  # Haupt-Umlage-Konto (nur HABEN-Buchungen)

# Buchungstexte die als Umlage identifiziert werden (fÃ¼r HABEN-Buchungen auf Kostenkonten)
UMLAGE_BUCHUNGSTEXTE = ['Kostenumlage AH Greiner', 'Kostenumlage Auto Greiner', 'Kostenumlage']

def get_ma_verteilung(standort: str = '0') -> dict:
    """
    Holt aktuelle MA-Verteilung aus der employees-Tabelle
    TAG 136: PostgreSQL-kompatibel - nutzt intern db_session()
    Mapping: department_name -> Kostenstelle

    Parameter:
    - standort: '0'=Alle, '1'=Deggendorf, '3'=Landau
    """
    standort_filter = ""
    if standort == '1':
        standort_filter = "AND location = 'Deggendorf'"
    elif standort == '3':
        standort_filter = "AND location = 'Landau a.d. Isar'"

    # TAG 136: PostgreSQL verwendet BOOLEAN, daher 'true' statt 1
    active_check = "active = true" if get_db_type() == 'postgresql' else "active = 1"

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                CASE
                    WHEN department_name IN ('Verkauf', 'Verkauf NW', 'Verkauf GW', 'Disposition', 'Fahrzeuge') THEN '12'
                    WHEN department_name IN ('Werkstatt', 'Service', 'Service & Empfang', 'Serviceberater', 'Hol- und Bringservice') THEN '3'
                    WHEN department_name IN ('Teile', 'Lager', 'Lager & Teile', 'Teile und ZubehÃ¶r') THEN '6'
                    WHEN department_name IN ('Verwaltung', 'Buchhaltung', 'GeschÃ¤ftsleitung', 'GeschÃ¤ftsfÃ¼hrung', 'CRM', 'Marketing', 'Call-Center', 'Kundenzentrale') THEN '0'
                    ELSE '9'
                END as kst,
                COUNT(*) as anzahl
            FROM employees
            WHERE {active_check}
            {standort_filter}
            GROUP BY kst
        """)
        result = cursor.fetchall()

    verteilung = {row_to_dict(row)['kst']: int(row_to_dict(row)['anzahl']) for row in result}
    return verteilung if verteilung else DEFAULT_MA_VERTEILUNG


@controlling_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('controlling/dashboard.html',
                         page_title='Controlling Dashboard',
                         active_page='controlling')

@controlling_bp.route('/bwa')
@login_required
def bwa():
    """BWA Dashboard - Hauptversion (TAG144: v2 ist jetzt Standard)"""
    return render_template('controlling/bwa_v2.html',
                         page_title='BWA',
                         active_page='controlling')


@controlling_bp.route('/bwa/archiv')
@login_required
def bwa_archiv():
    """BWA Archiv - Alte ausführliche Version (TAG144: v1 ins Archiv)"""
    return render_template('controlling/bwa_v1.html',
                         page_title='BWA Archiv (v1)',
                         active_page='controlling')

@controlling_bp.route('/tek')
@login_required
def tek_dashboard():
    """TEK Dashboard - Hauptversion (TAG140: v2 ist jetzt Standard)"""
    return render_template('controlling/tek_dashboard_v2.html',
                         page_title='Tägliche Erfolgskontrolle',
                         active_page='controlling')


@controlling_bp.route('/tek/archiv')
@login_required
def tek_dashboard_archiv():
    """TEK Archiv - Alte ausführliche Version (TAG140: v1 ins Archiv)"""
    return render_template('controlling/tek_dashboard.html',
                         page_title='TEK Archiv (v1)',
                         active_page='controlling')


# =============================================================================
# HELPER: Umsatz/Einsatz pro Bereich fÃ¼r beliebigen Zeitraum
# =============================================================================

def get_bereich_daten(von: str, bis: str, firma_filter_umsatz: str, umlage_erloese_filter: str = '') -> dict:
    """
    Holt Umsatz und Einsatz pro Bereich fÃ¼r einen Zeitraum.
    TAG 136: PostgreSQL-kompatibel
    Returns: {'1-NW': {'umsatz': X, 'einsatz': Y}, ...}
    """
    with db_session() as conn:
        cursor = conn.cursor()

        # UMSATZ
        cursor.execute(convert_placeholders(f"""
            SELECT
                CASE
                    WHEN nominal_account_number BETWEEN 810000 AND 819999 THEN '1-NW'
                    WHEN nominal_account_number BETWEEN 820000 AND 829999 THEN '2-GW'
                    WHEN nominal_account_number BETWEEN 830000 AND 839999 THEN '3-Teile'
                    WHEN nominal_account_number BETWEEN 840000 AND 849999 THEN '4-Lohn'
                    WHEN nominal_account_number BETWEEN 860000 AND 869999 THEN '5-Sonst'
                    ELSE '9-Andere'
                END as bereich,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
              {firma_filter_umsatz}
              {umlage_erloese_filter}
            GROUP BY bereich
        """), (von, bis))
        umsatz_rows = [row_to_dict(r) for r in cursor.fetchall()]

        # EINSATZ
        cursor.execute(convert_placeholders(f"""
            SELECT
                CASE
                    WHEN nominal_account_number BETWEEN 710000 AND 719999 THEN '1-NW'
                    WHEN nominal_account_number BETWEEN 720000 AND 729999 THEN '2-GW'
                    WHEN nominal_account_number BETWEEN 730000 AND 739999 THEN '3-Teile'
                    WHEN nominal_account_number BETWEEN 740000 AND 749999 THEN '4-Lohn'
                    WHEN nominal_account_number BETWEEN 760000 AND 769999 THEN '5-Sonst'
                    ELSE '9-Andere'
                END as bereich,
                SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as einsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 700000 AND 799999
              {firma_filter_umsatz}
            GROUP BY bereich
        """), (von, bis))
        einsatz_rows = [row_to_dict(r) for r in cursor.fetchall()]

    result = {}
    for bkey in ['1-NW', '2-GW', '3-Teile', '4-Lohn', '5-Sonst']:
        umsatz = next((float(r['umsatz'] or 0) for r in umsatz_rows if r['bereich'] == bkey), 0)
        einsatz = next((float(r['einsatz'] or 0) for r in einsatz_rows if r['bereich'] == bkey), 0)
        db1 = umsatz - einsatz
        result[bkey] = {
            'umsatz': round(umsatz, 2),
            'einsatz': round(einsatz, 2),
            'db1': round(db1, 2)
        }

    return result


def get_werkstatt_produktivitaet(von: str, bis: str, betrieb: str = '0') -> dict:
    """
    Holt Werkstatt-ProduktivitÃ¤t (EW) fÃ¼r kalkulatorischen Einsatz.

    NUTZT ZENTRALE BERECHNUNG aus api/werkstatt_api.py (werkstatt_leistung_daily)
    = Single Source of Truth fÃ¼r Werkstatt-KPIs
    TAG 136: PostgreSQL-kompatibel

    Returns: {
        'produktivitaet': 75.5,  # EW in %
        'leistungsgrad': 90.0,
        'stempelzeit_min': 12000,
        'anwesenheit_min': 16000,
        'vorgabezeit_aw': 1800
    }
    """
    try:
        from api.db_utils import db_session, row_to_dict
        from api.db_connection import sql_placeholder

        # TAG 136: PostgreSQL-Placeholder
        ph = sql_placeholder()

        with db_session() as conn:
            cursor = conn.cursor()

            # Betrieb-Filter (gleiche Logik wie werkstatt_api.py)
            betrieb_filter = ""
            params = [von, bis]
            if betrieb == '1':
                betrieb_filter = "AND (betrieb_nr = 1 OR betrieb_nr IS NULL OR betrieb_nr = 0)"
            elif betrieb == '2':
                betrieb_filter = f"AND betrieb_nr = {ph}"
                params.append(2)

            cursor.execute(f"""
                SELECT
                    SUM(stempelzeit_min) as stempelzeit,
                    SUM(anwesenheit_min) as anwesenheit,
                    SUM(vorgabezeit_aw) as vorgabe_aw,
                    SUM(umsatz) as umsatz
                FROM werkstatt_leistung_daily
                WHERE datum >= {ph} AND datum < {ph}
                  AND mechaniker_nr IS NOT NULL
                  AND stempelzeit_min > 0
                  {betrieb_filter}
            """, params)

            row = cursor.fetchone()
            result = row_to_dict(row) if row else None

            if not result or not result.get('stempelzeit'):
                return {'produktivitaet': 75.0, 'leistungsgrad': 85.0}

            stempelzeit = result.get('stempelzeit') or 0
            anwesenheit = result.get('anwesenheit') or 0
            vorgabe_aw = result.get('vorgabe_aw') or 0
            umsatz = result.get('umsatz') or 0

            # GLEICHE FORMELN wie werkstatt_api.py:
            # ProduktivitÃ¤t = Stempelzeit / Anwesenheit * 100
            # Leistungsgrad = Vorgabezeit_AW * 6 / Stempelzeit * 100 (6 Min pro AW)
            # TAG 136: PostgreSQL gibt decimal.Decimal zurÃ¼ck, muss zu float gecastet werden
            stempelzeit = float(stempelzeit) if stempelzeit else 0
            anwesenheit = float(anwesenheit) if anwesenheit else 0
            vorgabe_aw = float(vorgabe_aw) if vorgabe_aw else 0
            produktivitaet = round(stempelzeit / anwesenheit * 100, 1) if anwesenheit > 0 else 75.0
            leistungsgrad = round(vorgabe_aw * 6.0 / stempelzeit * 100, 1) if stempelzeit > 0 else 85.0

            return {
                'produktivitaet': produktivitaet,
                'leistungsgrad': leistungsgrad,
                'stempelzeit_min': stempelzeit,
                'anwesenheit_min': anwesenheit,
                'vorgabezeit_aw': vorgabe_aw,
                'umsatz_werkstatt': umsatz
            }

    except Exception as e:
        print(f"Werkstatt-ProduktivitÃ¤t Fehler: {e}")
        import traceback
        traceback.print_exc()
        return {'produktivitaet': 75.0, 'leistungsgrad': 85.0}


# =============================================================================
# TEK API - TÃ¤gliche Erfolgskontrolle
# =============================================================================

@controlling_bp.route('/api/tek')
@login_required
def api_tek():
    """
    API: TEK-Daten mit umschaltbarem Modus
    
    Parameter:
    - modus: 'teil' (Teilkosten/DB1) oder 'voll' (Vollkosten/BE)
    - firma: 0=Alle, 1=Stellantis(DEG+LAN), 2=Hyundai
    - standort: 0=Alle, 1=Deggendorf, 3=Landau (nur bei Firma 1)
    - monat, jahr: Zeitraum
    - umlage: 'mit' (Standard) oder 'ohne' - Interne Umlage neutralisieren
    
    Umlage-Bereinigung:
    - Bei 'ohne' werden die internen Umlage-Konten herausgerechnet
    - Betrifft: 817051, 827051, 837051, 847051 (ErlÃ¶se) und 498001 (Kosten)
    - Zeigt die "echte" operative Performance ohne Konzern-interne Verrechnungen
    
    Firmenstruktur:
    - subsidiary=1, branch=1: Autohaus Greiner Deggendorf (DEGO)
    - subsidiary=1, branch=3: Autohaus Greiner Landau (LANO)
    - subsidiary=2, branch=2: Auto Greiner Hyundai (DEGH)
    """
    try:
        firma = request.args.get('firma', '0')
        standort = request.args.get('standort', '0')  # 0=Alle, 1=DEG, 3=LAN
        monat = request.args.get('monat', type=int)
        jahr = request.args.get('jahr', type=int)
        modus = request.args.get('modus', 'teil')  # 'teil' oder 'voll'
        umlage = request.args.get('umlage', 'mit')  # 'mit' oder 'ohne'

        heute = date.today()
        if not monat:
            monat = heute.month
        if not jahr:
            jahr = heute.year

        von = f"{jahr}-{monat:02d}-01"
        bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"

        # TAG 136: PostgreSQL-kompatibel - Placeholder-Funktion
        ph = sql_placeholder()  # Returns ? fÃ¼r SQLite, %s fÃ¼r PostgreSQL
        
        # Filter bauen
        # WICHTIG: FÃ¼r Umsatz/Einsatz (7/8xxxxx) gilt branch_number
        #          FÃ¼r Kosten (4xxxxx) gilt die letzte Ziffer der Kontonummer!
        #          - Letzte Ziffer 1 = Deggendorf
        #          - Letzte Ziffer 2 = Landau
        #          - subsidiary_to_company_ref 2 = Hyundai (separate Firma)
        
        firma_filter = ""
        firma_filter_umsatz = ""   # FÃ¼r Umsatz/Einsatz: branch_number
        firma_filter_kosten = ""   # FÃ¼r Kosten: letzte Ziffer der Kontonummer
        standort_name = "Alle"
        standort_code = standort  # FÃ¼r MA-Verteilung
        
        if firma == '1':
            # Stellantis (Autohaus Greiner)
            firma_filter = "AND subsidiary_to_company_ref = 1"
            firma_filter_umsatz = "AND subsidiary_to_company_ref = 1"
            firma_filter_kosten = "AND subsidiary_to_company_ref = 1"
            standort_name = "Stellantis (DEG+LAN)"
            if standort == '1':
                # Deggendorf: branch_number=1 fÃ¼r Umsatz, letzte Ziffer=1 fÃ¼r Kosten
                firma_filter_umsatz += " AND branch_number = 1"
                firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
                standort_name = "Deggendorf"
                standort_code = '1'
            elif standort == '2':  # Landau (frÃ¼her '3' fÃ¼r branch, jetzt '2' fÃ¼r Konto-Endung)
                # Landau: branch_number=3 fÃ¼r Umsatz, letzte Ziffer=2 fÃ¼r Kosten
                firma_filter_umsatz += " AND branch_number = 3"
                firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
                standort_name = "Landau"
                standort_code = '3'  # FÃ¼r MA-Verteilung in employees (location='Landau')
        elif firma == '2':
            # Hyundai (Auto Greiner) - separate Firma
            firma_filter = "AND subsidiary_to_company_ref = 2"
            firma_filter_umsatz = "AND subsidiary_to_company_ref = 2"
            firma_filter_kosten = "AND subsidiary_to_company_ref = 2"
            standort_name = "Hyundai"
        
        # =====================================================================
        # UMLAGE-FILTER: Bei 'ohne' werden Umlage-Konten ausgeschlossen
        # =====================================================================
        umlage_erloese_filter = ""
        umlage_kosten_filter = ""
        umlage_betrag = 0
        umlage_kosten_betrag = 0
        
        if umlage == 'ohne':
            # Umlage-ErlÃ¶se aus Umsatz ausschlieÃŸen (die 4 Umlage-Konten)
            umlage_konten_str = ','.join(map(str, UMLAGE_ERLOESE_KONTEN))
            umlage_erloese_filter = f"AND nominal_account_number NOT IN ({umlage_konten_str})"

            # Umlage-Kosten ausschlieÃŸen: OPTION C = Buchungstext-basiert + KST 0
            # Filtert nur HABEN-Buchungen mit "Kostenumlage" im Text auf KST 0 (Verwaltung)
            # Dies schlieÃŸt 498001 (50k), 415001, 440001, 461001, 462001 aus
            # ABER behÃ¤lt 415011, 415021, 415031, 415061 (echte Kosten auf KST 1-6)!
            umlage_kosten_filter = """AND NOT (
                debit_or_credit = 'H'
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0'
                AND (posting_text LIKE '%%Kostenumlage%%'
                     OR posting_text LIKE '%%kostenumlage%%')
            )"""

            # Berechne Umlage-Betrag fÃ¼r Info-Anzeige (ErlÃ¶s-Seite)
            with db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(convert_placeholders(f"""
                    SELECT COALESCE(SUM(
                        CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                    )/100.0, 0) as betrag
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND nominal_account_number IN ({umlage_konten_str})
                      {firma_filter_umsatz}
                """), (von, bis))
                umlage_result = cursor.fetchone()
                if umlage_result:
                    umlage_result = row_to_dict(umlage_result)
                    umlage_betrag = float(umlage_result['betrag'] or 0)

                # Berechne auch den Kosten-Filter-Betrag fÃ¼r Info (nur KST 0)
                cursor.execute(convert_placeholders(f"""
                    SELECT COALESCE(SUM(
                        CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                    )/100.0, 0) as betrag
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND debit_or_credit = 'H'
                      AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0'
                      AND (posting_text LIKE '%%Kostenumlage%%' OR posting_text LIKE '%%kostenumlage%%')
                      AND nominal_account_number BETWEEN 400000 AND 499999
                      {firma_filter_kosten}
                """), (von, bis))
                umlage_kosten_result = cursor.fetchone()
                if umlage_kosten_result:
                    umlage_kosten_result = row_to_dict(umlage_kosten_result)
                    umlage_kosten_betrag = abs(float(umlage_kosten_result['betrag'] or 0))

        # =====================================================================
        # UMSATZ/EINSATZ NACH BEREICHEN - TAG 136: PostgreSQL-kompatibel
        # =====================================================================
        with db_session() as conn:
            cursor = conn.cursor()

            # UMSATZ NACH BEREICHEN (branch_number fÃ¼r Standort-Filter)
            cursor.execute(convert_placeholders(f"""
                SELECT
                    CASE
                        WHEN nominal_account_number BETWEEN 810000 AND 819999 THEN '1-NW'
                        WHEN nominal_account_number BETWEEN 820000 AND 829999 THEN '2-GW'
                        WHEN nominal_account_number BETWEEN 830000 AND 839999 THEN '3-Teile'
                        WHEN nominal_account_number BETWEEN 840000 AND 849999 THEN '4-Lohn'
                        WHEN nominal_account_number BETWEEN 860000 AND 869999 THEN '5-Sonst'
                        WHEN nominal_account_number BETWEEN 893200 AND 893299 THEN '6-8932'
                        ELSE '9-Andere'
                    END as bereich,
                    SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND ((nominal_account_number BETWEEN 800000 AND 889999)
                       OR (nominal_account_number BETWEEN 893200 AND 893299))
                  {firma_filter_umsatz}
                  {umlage_erloese_filter}
                GROUP BY bereich
            """), (von, bis))
            umsatz_rows = cursor.fetchall()

            # EINSATZ NACH BEREICHEN (branch_number fÃ¼r Standort-Filter)
            cursor.execute(convert_placeholders(f"""
                SELECT
                    CASE
                        WHEN nominal_account_number BETWEEN 710000 AND 719999 THEN '1-NW'
                        WHEN nominal_account_number BETWEEN 720000 AND 729999 THEN '2-GW'
                        WHEN nominal_account_number BETWEEN 730000 AND 739999 THEN '3-Teile'
                        WHEN nominal_account_number BETWEEN 740000 AND 749999 THEN '4-Lohn'
                        WHEN nominal_account_number BETWEEN 760000 AND 769999 THEN '5-Sonst'
                        ELSE '9-Andere'
                    END as bereich,
                    SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as einsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number BETWEEN 700000 AND 799999
                  {firma_filter_umsatz}
                GROUP BY bereich
            """), (von, bis))
            einsatz_rows = cursor.fetchall()

        umsatz_dict = {row_to_dict(r)['bereich']: float(row_to_dict(r)['umsatz'] or 0) for r in umsatz_rows}
        einsatz_dict = {row_to_dict(r)['bereich']: float(row_to_dict(r)['einsatz'] or 0) for r in einsatz_rows}
        
        # =====================================================================
        # VOLLKOSTEN (nur wenn modus='voll')
        # Verwendet firma_filter_kosten fÃ¼r Kosten-Konten (4xxxxx)
        # TAG 136: berechne_vollkosten nutzt jetzt intern db_session()
        # =====================================================================
        kosten_data = None
        if modus == 'voll':
            kosten_data = berechne_vollkosten(von, bis, firma_filter_kosten, standort_code, umlage_kosten_filter)
        
        # =====================================================================
        # BEREICHE ZUSAMMENFÃœHREN
        # =====================================================================
        bereich_namen = {
            '1-NW': 'Neuwagen', '2-GW': 'Gebrauchtwagen',
            '3-Teile': 'Teile/Service', '4-Lohn': 'Werkstattlohn', '5-Sonst': 'Sonstige'
        }
        
        # Mapping: TEK-Bereich â†’ FIBU-Kostenstelle (5. Stelle)
        bereich_zu_kst = {
            '1-NW': '1',      # Neuwagen
            '2-GW': '2',      # Gebrauchtwagen
            '3-Teile': '6',   # Teile = KST 6
            '4-Lohn': '3',    # Werkstattlohn = Service = KST 3
            '5-Sonst': '7'    # Sonstige
        }
        
        bereiche = {}
        totals = {'umsatz': 0, 'einsatz': 0, 'variable': 0, 'direkte': 0, 'umlage': 0}
        
        for bkey in ['1-NW', '2-GW', '3-Teile', '4-Lohn', '5-Sonst']:
            u = umsatz_dict.get(bkey, 0)
            e = einsatz_dict.get(bkey, 0)
            db1 = u - e
            marge = (db1 / u * 100) if u > 0 else 0
            
            bereich = {
                'name': bereich_namen[bkey],
                'umsatz': round(u, 2),
                'einsatz': round(e, 2),
                'db1': round(db1, 2),
                'marge': round(marge, 1)
            }
            
            # Vollkosten-Erweiterung
            if kosten_data:
                kst = bereich_zu_kst.get(bkey, '0')
                var = kosten_data['variable'].get(kst, 0)
                dir_k = kosten_data['direkte'].get(kst, 0)
                uml = kosten_data['umlage_verteilt'].get(kst, 0)
                
                db2 = db1 - var
                db3 = db2 - dir_k
                be = db3 - uml
                
                bereich.update({
                    'variable_kosten': round(var, 2),
                    'db2': round(db2, 2),
                    'direkte_kosten': round(dir_k, 2),
                    'db3': round(db3, 2),
                    'umlage': round(uml, 2),
                    'be': round(be, 2)
                })
                
                totals['variable'] += var
                totals['direkte'] += dir_k
                totals['umlage'] += uml
            
            bereiche[bkey] = bereich
            totals['umsatz'] += u
            totals['einsatz'] += e
        
        # Andere UmsÃ¤tze/EinsÃ¤tze addieren
        totals['umsatz'] += umsatz_dict.get('6-8932', 0) + umsatz_dict.get('9-Andere', 0)
        totals['einsatz'] += einsatz_dict.get('9-Andere', 0)

        total_db1 = totals['umsatz'] - totals['einsatz']

        gesamt = {
            'umsatz': round(totals['umsatz'], 2),
            'einsatz': round(totals['einsatz'], 2),
            'db1': round(total_db1, 2),
            'marge': round((total_db1 / totals['umsatz'] * 100) if totals['umsatz'] > 0 else 0, 1)
        }

        if kosten_data:
            total_db2 = total_db1 - totals['variable']
            total_db3 = total_db2 - totals['direkte']
            total_be = total_db3 - totals['umlage']

            gesamt.update({
                'variable_kosten': round(totals['variable'], 2),
                'db2': round(total_db2, 2),
                'direkte_kosten': round(totals['direkte'], 2),
                'db3': round(total_db3, 2),
                'umlage': round(totals['umlage'], 2),
                'indirekte_gesamt': round(kosten_data['indirekte_gesamt'], 2),
                'be': round(total_be, 2)
            })

        # =====================================================================
        # VM/VJ PRO BEREICH (fÃ¼r Teile und Werkstatt Tabs)
        # =====================================================================
        vm_monat_calc, vm_jahr_calc = (12, jahr - 1) if monat == 1 else (monat - 1, jahr)
        vm_von_bereich = f"{vm_jahr_calc}-{vm_monat_calc:02d}-01"
        vm_bis_bereich = f"{vm_jahr_calc}-{vm_monat_calc+1:02d}-01" if vm_monat_calc < 12 else f"{vm_jahr_calc+1}-01-01"

        vj_von_bereich = f"{jahr-1}-{monat:02d}-01"
        vj_bis_bereich = f"{jahr-1}-{monat+1:02d}-01" if monat < 12 else f"{jahr}-01-01"

        # VM-Daten pro Bereich holen
        vm_bereiche = get_bereich_daten(vm_von_bereich, vm_bis_bereich, firma_filter_umsatz, umlage_erloese_filter)
        vj_bereiche = get_bereich_daten(vj_von_bereich, vj_bis_bereich, firma_filter_umsatz, umlage_erloese_filter)

        # VM/VJ zu jedem Bereich hinzufÃ¼gen
        for bkey in bereiche:
            vm_b = vm_bereiche.get(bkey, {})
            vj_b = vj_bereiche.get(bkey, {})
            bereiche[bkey]['vm_umsatz'] = vm_b.get('umsatz', 0)
            bereiche[bkey]['vm_db1'] = vm_b.get('db1', 0)
            bereiche[bkey]['vj_umsatz'] = vj_b.get('umsatz', 0)
            bereiche[bkey]['vj_db1'] = vj_b.get('db1', 0)

        # =====================================================================
        # STÃœCKZAHLEN FÃœR NW/GW (aus dealer_vehicles)
        # =====================================================================
        stueck_nw = get_stueckzahlen_locosoft(von, bis, '1-NW', firma, standort)
        stueck_gw = get_stueckzahlen_locosoft(von, bis, '2-GW', firma, standort)

        # VM-StÃ¼ckzahlen
        vm_stueck_nw = get_stueckzahlen_locosoft(vm_von_bereich, vm_bis_bereich, '1-NW', firma, standort)
        vm_stueck_gw = get_stueckzahlen_locosoft(vm_von_bereich, vm_bis_bereich, '2-GW', firma, standort)

        # VJ-StÃ¼ckzahlen
        vj_stueck_nw = get_stueckzahlen_locosoft(vj_von_bereich, vj_bis_bereich, '1-NW', firma, standort)
        vj_stueck_gw = get_stueckzahlen_locosoft(vj_von_bereich, vj_bis_bereich, '2-GW', firma, standort)

        # StÃ¼ckzahlen zu Bereichen hinzufÃ¼gen
        if '1-NW' in bereiche:
            bereiche['1-NW']['stueck'] = stueck_nw.get('gesamt_stueck', 0)
            bereiche['1-NW']['vm_stueck'] = vm_stueck_nw.get('gesamt_stueck', 0)
            bereiche['1-NW']['vj_stueck'] = vj_stueck_nw.get('gesamt_stueck', 0)
            # DB1/StÃ¼ck berechnen
            if bereiche['1-NW']['stueck'] > 0:
                bereiche['1-NW']['db1_pro_stueck'] = round(bereiche['1-NW']['db1'] / bereiche['1-NW']['stueck'], 2)
            else:
                bereiche['1-NW']['db1_pro_stueck'] = 0

        if '2-GW' in bereiche:
            bereiche['2-GW']['stueck'] = stueck_gw.get('gesamt_stueck', 0)
            bereiche['2-GW']['vm_stueck'] = vm_stueck_gw.get('gesamt_stueck', 0)
            bereiche['2-GW']['vj_stueck'] = vj_stueck_gw.get('gesamt_stueck', 0)
            # DB1/StÃ¼ck berechnen
            if bereiche['2-GW']['stueck'] > 0:
                bereiche['2-GW']['db1_pro_stueck'] = round(bereiche['2-GW']['db1'] / bereiche['2-GW']['stueck'], 2)
            else:
                bereiche['2-GW']['db1_pro_stueck'] = 0

        # Gesamt-StÃ¼ckzahlen
        gesamt_stueck = stueck_nw.get('gesamt_stueck', 0) + stueck_gw.get('gesamt_stueck', 0)
        gesamt_vm_stueck = vm_stueck_nw.get('gesamt_stueck', 0) + vm_stueck_gw.get('gesamt_stueck', 0)
        gesamt_vj_stueck = vj_stueck_nw.get('gesamt_stueck', 0) + vj_stueck_gw.get('gesamt_stueck', 0)

        # StÃ¼ckzahlen zum Gesamt-Objekt hinzufÃ¼gen
        gesamt['stueck'] = gesamt_stueck
        gesamt['stueck_nw'] = stueck_nw.get('gesamt_stueck', 0)
        gesamt['stueck_gw'] = stueck_gw.get('gesamt_stueck', 0)
        if gesamt_stueck > 0:
            gesamt['db1_pro_stueck'] = round(total_db1 / gesamt_stueck, 2)
        else:
            gesamt['db1_pro_stueck'] = 0

        # =====================================================================
        # WERKSTATT-EINSATZ (TAG 140: Rollierender 3-Vormonate Durchschnitt)
        # =====================================================================
        # Die FIBU (74xxxx) enthält:
        # - 740xxx: Lohnkosten - erst nach Monatsabschluss gebucht!
        # - 743xxx: Teile-Einsatz
        # - 747xxx: Fremdleistungen
        #
        # Im laufenden Monat fehlen Lohn + Fremdleistungen (werden erst später gebucht).
        # Lösung: Rollierender Durchschnitt der letzten 3 abgeschlossenen Monate.
        #
        # Mechaniker-Produktivität holen (für Info-Anzeige)
        betrieb_fuer_ws = firma if firma in ['1', '2'] else '0'
        ws_produktivitaet = get_werkstatt_produktivitaet(von, bis, betrieb_fuer_ws)

        werkstatt_umsatz = bereiche.get('4-Lohn', {}).get('umsatz', 0)
        werkstatt_einsatz_fibu = bereiche.get('4-Lohn', {}).get('einsatz', 0)

        # Produktivität (EW) aus Stempeluhr-Daten - nur für Info
        produktivitaet = ws_produktivitaet.get('produktivitaet', 75.0)
        leistungsgrad = ws_produktivitaet.get('leistungsgrad', 85.0)

        # TAG 140: Prüfen ob laufender Monat (Lohn+Fremdleistungen fehlen noch)
        heute = datetime.now()
        ist_laufender_monat = bis >= heute.strftime('%Y-%m-%d')

        if '4-Lohn' in bereiche and werkstatt_umsatz > 0:
            if ist_laufender_monat:
                # Rollierenden LOHN-Anteil aus den letzten 3 Monaten berechnen
                # NUR Konten 740xxx (Lohn) - Fremdleistungen (747xxx) sind bereits in FIBU gebucht!
                # Zeitraum: 3 abgeschlossene Vormonate (z.B. für Dez: Sep, Okt, Nov)
                erster_vormonat = (heute.replace(day=1) - timedelta(days=1)).replace(day=1)
                drei_monate_vorher = (erster_vormonat - timedelta(days=89)).replace(day=1)  # ~3 Monate zurück

                with db_session() as conn:
                    cursor = conn.cursor()
                    # NUR Lohn (740xxx) der letzten 3 Monate - NICHT Fremdleistungen!
                    cursor.execute(convert_placeholders("""
                        SELECT
                            SUM(CASE WHEN nominal_account_number BETWEEN 740000 AND 742999
                                     AND debit_or_credit = 'S' THEN posted_value
                                     WHEN nominal_account_number BETWEEN 740000 AND 742999
                                     AND debit_or_credit = 'H' THEN -posted_value
                                     ELSE 0 END) / 100.0 as lohn,
                            SUM(CASE WHEN nominal_account_number BETWEEN 840000 AND 849999
                                     AND debit_or_credit = 'H' THEN posted_value
                                     WHEN nominal_account_number BETWEEN 840000 AND 849999
                                     AND debit_or_credit = 'S' THEN -posted_value
                                     ELSE 0 END) / 100.0 as umsatz
                        FROM loco_journal_accountings
                        WHERE accounting_date >= ? AND accounting_date < ?
                    """), (drei_monate_vorher.strftime('%Y-%m-%d'), erster_vormonat.strftime('%Y-%m-%d')))
                    row = cursor.fetchone()
                    r = row_to_dict(row, cursor)

                hist_lohn = float(r['lohn'] or 0) if r else 0
                hist_umsatz = float(r['umsatz'] or 0) if r else 0
                lohn_anteil = (hist_lohn / hist_umsatz) if hist_umsatz > 0 else 0.25

                # Kalkulatorischen Lohn-Zuschlag auf aktuellen Umsatz anwenden
                kalk_lohn_einsatz = round(werkstatt_umsatz * lohn_anteil, 2)
                gesamt_einsatz = werkstatt_einsatz_fibu + kalk_lohn_einsatz
                werkstatt_db1 = werkstatt_umsatz - gesamt_einsatz
                werkstatt_marge = round((werkstatt_db1 / werkstatt_umsatz * 100), 1)

                bereiche['4-Lohn']['einsatz_kalk'] = gesamt_einsatz
                bereiche['4-Lohn']['einsatz_lohn_kalk'] = kalk_lohn_einsatz
                bereiche['4-Lohn']['einsatz_teile'] = werkstatt_einsatz_fibu
                bereiche['4-Lohn']['db1_kalk'] = round(werkstatt_db1, 2)
                bereiche['4-Lohn']['marge_kalk'] = werkstatt_marge
                bereiche['4-Lohn']['hinweis'] = f"FIBU: {round(werkstatt_einsatz_fibu/1000)}k + Lohn kalk. ({round(lohn_anteil*100)}%): {round(kalk_lohn_einsatz/1000)}k"
            else:
                # Abgeschlossener Monat: Nur FIBU-Werte (Lohn+FL sind bereits gebucht)
                werkstatt_db1 = werkstatt_umsatz - werkstatt_einsatz_fibu
                werkstatt_marge = round((werkstatt_db1 / werkstatt_umsatz * 100), 1)

                bereiche['4-Lohn']['db1'] = round(werkstatt_db1, 2)
                bereiche['4-Lohn']['marge'] = werkstatt_marge
                fibu_einsatz_quote = round((werkstatt_einsatz_fibu / werkstatt_umsatz * 100), 1)
                bereiche['4-Lohn']['hinweis'] = f"FIBU komplett: {round(werkstatt_einsatz_fibu/1000)}k ({fibu_einsatz_quote}% vom Umsatz)"

            bereiche['4-Lohn']['produktivitaet'] = produktivitaet
            bereiche['4-Lohn']['leistungsgrad'] = leistungsgrad

        # =====================================================================
        # FIRMEN-VERGLEICH - TAG 136: PostgreSQL-kompatibel
        # =====================================================================
        firmen = None
        if firma == '0':
            firmen = {}
            with db_session() as conn:
                cursor = conn.cursor()
                for f_id, f_name in [('1', 'Stellantis'), ('2', 'Hyundai')]:
                    cursor.execute(convert_placeholders("""
                        SELECT SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
                        FROM loco_journal_accountings
                        WHERE accounting_date >= ? AND accounting_date < ?
                          AND ((nominal_account_number BETWEEN 800000 AND 889999)
                               OR (nominal_account_number BETWEEN 893200 AND 893299))
                          AND subsidiary_to_company_ref = ?
                    """), (von, bis, f_id))
                    row = cursor.fetchone()
                    f_umsatz = float(row_to_dict(row)['umsatz'] or 0) if row else 0

                    cursor.execute(convert_placeholders("""
                        SELECT SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as einsatz
                        FROM loco_journal_accountings
                        WHERE accounting_date >= ? AND accounting_date < ?
                          AND nominal_account_number BETWEEN 700000 AND 799999
                          AND subsidiary_to_company_ref = ?
                    """), (von, bis, f_id))
                    row = cursor.fetchone()
                    f_einsatz = float(row_to_dict(row)['einsatz'] or 0) if row else 0

                    f_db1 = f_umsatz - f_einsatz
                    firmen[f_id] = {
                        'name': f_name,
                        'umsatz': round(f_umsatz, 2),
                        'einsatz': round(f_einsatz, 2),
                        'db1': round(f_db1, 2),
                        'marge': round((f_db1 / f_umsatz * 100) if f_umsatz > 0 else 0, 1)
                    }

        # =====================================================================
        # VORMONAT (Umsatz/Einsatz -> firma_filter_umsatz) - TAG 136
        # =====================================================================
        vm_monat, vm_jahr = (12, jahr - 1) if monat == 1 else (monat - 1, jahr)
        vm_von = f"{vm_jahr}-{vm_monat:02d}-01"
        vm_bis = f"{vm_jahr}-{vm_monat+1:02d}-01" if vm_monat < 12 else f"{vm_jahr+1}-01-01"

        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_placeholders(f"""
                SELECT SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
                  {firma_filter_umsatz}
            """), (vm_von, vm_bis))
            row = cursor.fetchone()
            vm_umsatz = float(row_to_dict(row)['umsatz'] or 0) if row else 0

            cursor.execute(convert_placeholders(f"""
                SELECT SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as einsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number BETWEEN 700000 AND 799999
                  {firma_filter_umsatz}
            """), (vm_von, vm_bis))
            row = cursor.fetchone()
            vm_einsatz = float(row_to_dict(row)['einsatz'] or 0) if row else 0

        vm_db1 = vm_umsatz - vm_einsatz

        # =====================================================================
        # VORJAHR (kompletter Monat - Vergleich mit Hochrechnung) - TAG 136
        # =====================================================================
        vj_jahr = jahr - 1
        vj_von = f"{vj_jahr}-{monat:02d}-01"
        vj_bis = f"{vj_jahr}-{monat+1:02d}-01" if monat < 12 else f"{vj_jahr+1}-01-01"

        with db_session() as conn:
            cursor = conn.cursor()
            # Kompletter Vorjahres-Monat (fÃ¼r Vergleich mit Hochrechnung)
            cursor.execute(convert_placeholders(f"""
                SELECT SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
                  {firma_filter_umsatz}
            """), (vj_von, vj_bis))
            row = cursor.fetchone()
            vj_umsatz = float(row_to_dict(row)['umsatz'] or 0) if row else 0

            cursor.execute(convert_placeholders(f"""
                SELECT SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as einsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number BETWEEN 700000 AND 799999
                  {firma_filter_umsatz}
            """), (vj_von, vj_bis))
            row = cursor.fetchone()
            vj_einsatz = float(row_to_dict(row)['einsatz'] or 0) if row else 0

        vj_db1 = vj_umsatz - vj_einsatz

        # =====================================================================
        # BREAKEVEN-PROGNOSE - TAG 136: nutzt jetzt intern db_session()
        # ECHTE KOSTEN - keine anteilige Verteilung!
        # Hyundai ist nur eine formaljuristische HÃ¼lle ohne eigene Kostenstruktur.
        # Die echten Kosten werden Ã¼ber firma_filter_kosten zugeordnet.
        # =====================================================================
        prognose = berechne_breakeven_prognose(monat, jahr, total_db1, firma_filter_umsatz, firma_filter_kosten, anteilige_kosten=False)

        # =====================================================================
        # STANDORT-BREAKEVENS (nur wenn Alle Firmen oder Stellantis)
        # Kosten werden nach 6. Ziffer der Kontonummer gefiltert:
        #   Ziffer 1 = Deggendorf, Ziffer 2 = Landau
        # =====================================================================
        standort_breakevens = None
        if firma in ['0', '1'] and standort == '0':
            with db_session() as conn:
                cursor = conn.cursor()

                # Deggendorf: branch_number=1 fÃ¼r Umsatz, 6. Ziffer=1 fÃ¼r Kosten
                cursor.execute(convert_placeholders("""
                    SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
                      AND branch_number = 1
                """), (von, bis))
                dego_umsatz = float(row_to_dict(cursor.fetchone()).get('umsatz') or 0)

                cursor.execute(convert_placeholders("""
                    SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as einsatz
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND nominal_account_number BETWEEN 700000 AND 799999
                      AND branch_number = 1
                """), (von, bis))
                dego_einsatz = float(row_to_dict(cursor.fetchone()).get('einsatz') or 0)
                dego_db1 = dego_umsatz - dego_einsatz

                # Landau: branch_number=3 fÃ¼r Umsatz, 6. Ziffer=2 fÃ¼r Kosten
                cursor.execute(convert_placeholders("""
                    SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
                      AND branch_number = 3
                """), (von, bis))
                lano_umsatz = float(row_to_dict(cursor.fetchone()).get('umsatz') or 0)

                cursor.execute(convert_placeholders("""
                    SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as einsatz
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND nominal_account_number BETWEEN 700000 AND 799999
                      AND branch_number = 3
                """), (von, bis))
                lano_einsatz = float(row_to_dict(cursor.fetchone()).get('einsatz') or 0)
                lano_db1 = lano_umsatz - lano_einsatz

            # Werktage aus Gesamt-Prognose
            werktage_info = prognose.get('werktage', {}) if prognose else {}

            # Breakeven mit standortspezifischem Kosten-Filter
            # Deggendorf: 6. Ziffer = 1
            dego_prognose = berechne_breakeven_prognose_standort(
                monat, jahr, dego_db1,
                " AND branch_number = 1",
                " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
            )
            # Landau: 6. Ziffer = 2
            lano_prognose = berechne_breakeven_prognose_standort(
                monat, jahr, lano_db1,
                " AND branch_number = 3",
                " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
            )

            standort_breakevens = {
                'deggendorf': {
                    'name': 'Deggendorf',
                    'db1': round(dego_db1, 2),
                    'prognose': dego_prognose
                },
                'landau': {
                    'name': 'Landau',
                    'db1': round(lano_db1, 2),
                    'prognose': lano_prognose
                }
            }

        # =====================================================================
        # TAGESWERTE - Aktueller Tag (nur wenn aktueller Monat)
        # =====================================================================
        heute = date.today()
        heute_daten = None
        heute_bereiche = {}
        if heute.year == jahr and heute.month == monat:
            heute_str = heute.isoformat()
            morgen_str = (heute + timedelta(days=1)).isoformat()

            with locosoft_session() as loco_conn:
                loco_cur = loco_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

                # Tagesumsatz GESAMT
                loco_cur.execute(f"""
                    SELECT
                        COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
                    FROM journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN 800000 AND 899999
                      {firma_filter_umsatz}
                """, (heute_str, morgen_str))
                heute_umsatz = float(loco_cur.fetchone()['umsatz'] or 0)

                # Tageseinsatz GESAMT
                loco_cur.execute(f"""
                    SELECT
                        COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as einsatz
                    FROM journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN 700000 AND 799999
                      {firma_filter_umsatz}
                """, (heute_str, morgen_str))
                heute_einsatz = float(loco_cur.fetchone()['einsatz'] or 0)

                # Tagesumsatz PRO BEREICH
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

                # Tageseinsatz PRO BEREICH
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
                      {firma_filter_umsatz}
                    GROUP BY bereich
                """, (heute_str, morgen_str))
                heute_einsatz_bereich = {r['bereich']: float(r['einsatz'] or 0) for r in loco_cur.fetchall()}

                loco_cur.close()

            # Pro Bereich zusammenfÃ¼hren
            for bkey in ['1-NW', '2-GW', '3-Teile', '4-Lohn', '5-Sonst']:
                h_umsatz = heute_umsatz_bereich.get(bkey, 0)
                h_einsatz = heute_einsatz_bereich.get(bkey, 0)
                heute_bereiche[bkey] = {
                    'umsatz': round(h_umsatz, 2),
                    'db1': round(h_umsatz - h_einsatz, 2)
                }

            heute_db1 = heute_umsatz - heute_einsatz
            heute_daten = {
                'datum': heute_str,
                'wochentag': ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'][heute.weekday()],
                'umsatz': round(heute_umsatz, 2),
                'einsatz': round(heute_einsatz, 2),
                'db1': round(heute_db1, 2)
            }

        # Heute-Daten in Bereiche einfÃ¼gen
        if heute_bereiche:
            for bkey in bereiche:
                if bkey in heute_bereiche:
                    bereiche[bkey]['heute_umsatz'] = heute_bereiche[bkey]['umsatz']
                    bereiche[bkey]['heute_db1'] = heute_bereiche[bkey]['db1']

        monat_namen = ['', 'Januar', 'Februar', 'MÃ¤rz', 'April', 'Mai', 'Juni',
                       'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
        
        response = {
            'success': True,
            'modus': modus,
            'filter': {
                'firma': firma,
                'firma_name': standort_name,
                'standort': standort,
                'monat': monat,
                'monat_name': monat_namen[monat],
                'jahr': jahr,
                'von': von,
                'bis': bis,
                'umlage': umlage,
                'umlage_bereinigt': umlage == 'ohne',
                'umlage_betrag_erloese': round(umlage_betrag, 2) if umlage == 'ohne' else None,
                'umlage_betrag_kosten': round(umlage_kosten_betrag, 2) if umlage == 'ohne' else None
            },
            'gesamt': gesamt,
            'bereiche': bereiche,
            'firmen': firmen,
            'vormonat': {
                'monat': vm_monat, 'monat_name': monat_namen[vm_monat], 'jahr': vm_jahr,
                'umsatz': round(vm_umsatz, 2), 'einsatz': round(vm_einsatz, 2),
                'db1': round(vm_db1, 2), 'marge': round((vm_db1 / vm_umsatz * 100) if vm_umsatz > 0 else 0, 1),
                'stueck': gesamt_vm_stueck
            },
            'veraenderung': {
                'umsatz': round(totals['umsatz'] - vm_umsatz, 2),
                'umsatz_prozent': round((totals['umsatz'] - vm_umsatz) / vm_umsatz * 100, 1) if vm_umsatz > 0 else 0,
                'db1': round(total_db1 - vm_db1, 2),
                'db1_prozent': round((total_db1 - vm_db1) / abs(vm_db1) * 100, 1) if vm_db1 != 0 else 0
            },
            'vorjahr': {
                'jahr': vj_jahr,
                'umsatz': round(vj_umsatz, 2),
                'einsatz': round(vj_einsatz, 2),
                'db1': round(vj_db1, 2),
                'marge': round((vj_db1 / vj_umsatz * 100) if vj_umsatz > 0 else 0, 1),
                'vergleich_db1': round(total_db1 - vj_db1, 2),
                'vergleich_db1_prozent': round((total_db1 - vj_db1) / abs(vj_db1) * 100, 1) if vj_db1 != 0 else 0,
                'stueck': gesamt_vj_stueck
            },
            'prognose': prognose,
            'standort_breakevens': standort_breakevens,
            'heute': heute_daten,
            'timestamp': datetime.now().isoformat()
        }

        if kosten_data:
            response['kosten_details'] = {
                'ma_verteilung': kosten_data['ma_verteilung'],
                'umlage_schluessel': kosten_data['umlage_schluessel']
            }
        
        return jsonify(response), 200
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


# =============================================================================
# TEK DRILL-DOWN API - Kontendetails pro Bereich
# =============================================================================

# SKR51-Kontobezeichnungen (Autohaus-Kontenrahmen)
SKR51_KONTOBEZEICHNUNGEN = {
    # Umsatz Neuwagen (81xxxx)
    810111: 'NW VE Privatkunde bar/Ã¼berw.',
    810151: 'NW VE Privatkunde Leasing',
    810211: 'NW VE Privatkunde Finanzierung',
    810311: 'NW VE Gewerbekunde bar/Ã¼berw.',
    810351: 'NW VE Gewerbekunde Leasing',
    810411: 'NW VE Gewerbekunde Finanzierung',
    810511: 'NW VE GroÃŸkunde bar/Ã¼berw.',
    810551: 'NW VE GroÃŸkunde Leasing',
    810611: 'NW VE GroÃŸkunde Finanzierung',
    810811: 'NW VE an HÃ¤ndler',
    810831: 'NW VE Gewerbekunde Leasing',
    810911: 'NW VE Sonstige',
    811111: 'NW HerstellerprÃ¤mien',
    811211: 'NW BonusprÃ¤mien',
    813211: 'NW SonderprÃ¤mien/Boni',
    817001: 'NW Innenumsatz',
    817051: 'NW Kostenumlage intern',
    
    # Umsatz Gebrauchtwagen (82xxxx)
    820111: 'GW VE Privatkunde bar/Ã¼berw.',
    820151: 'GW VE Privatkunde Leasing',
    820211: 'GW VE Privatkunde Finanzierung',
    820311: 'GW VE Gewerbekunde bar/Ã¼berw.',
    820351: 'GW VE Gewerbekunde Leasing',
    820411: 'GW VE Gewerbekunde Finanzierung',
    820511: 'GW VE an HÃ¤ndler',
    820611: 'GW VE Sonstige',
    821111: 'GW PrÃ¤mien/Boni',
    827001: 'GW Innenumsatz',
    827051: 'GW Kostenumlage intern',
    
    # Umsatz Teile/ZubehÃ¶r (83xxxx)
    830111: 'Teile VE Werkstatt extern',
    830211: 'Teile VE Thekenverkauf',
    830311: 'Teile VE an HÃ¤ndler',
    830411: 'Teile VE ZubehÃ¶r',
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
    860111: 'Mietwagen ErlÃ¶se',
    860211: 'Versicherungsprovision',
    860311: 'Finanzierungsprovision',
    860411: 'Leasingprovision',
    860511: 'Sonstige Provisionen',
    860611: 'Sonstige ErlÃ¶se',
    
    # Einsatz Neuwagen (71xxxx)
    710111: 'NW EK Privatkunde',
    710151: 'NW EK Leasing',
    710211: 'NW EK Finanzierung',
    710311: 'NW EK Gewerbekunde',
    710351: 'NW EK Gewerbe Leasing',
    710411: 'NW EK Gewerbe Finanzierung',
    710511: 'NW EK GroÃŸkunde',
    710811: 'NW EK an HÃ¤ndler',
    710831: 'NW EK Gewerbe Leasing',
    710911: 'NW EK Sonstige',
    710101: 'NW Wareneinsatz',
    717501: 'NW Zulassung/ÃœberfÃ¼hrung',
    717001: 'NW Innenumsatz EK',
    
    # Einsatz Gebrauchtwagen (72xxxx)
    720111: 'GW EK Privatkunde',
    720151: 'GW EK Leasing',
    720211: 'GW EK Finanzierung',
    720311: 'GW EK Gewerbekunde',
    720411: 'GW EK an HÃ¤ndler',
    720511: 'GW EK Sonstige',
    720101: 'GW Wareneinsatz',
    727001: 'GW Innenumsatz EK',
    727501: 'GW Zulassung/ÃœberfÃ¼hrung',
    
    # Einsatz Teile (73xxxx)
    730111: 'Teile EK Werkstatt',
    730211: 'Teile EK Theke',
    730311: 'Teile EK HÃ¤ndler',
    730411: 'Teile EK ZubehÃ¶r',
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
}

def get_konto_bezeichnung(db, konto: int, subsidiary: int = 1) -> str:
    """
    Holt Kontobezeichnung aus loco_nominal_accounts (Locosoft Stammdaten).
    TAG 136: PostgreSQL-kompatibel

    Parameter:
    - db: Datenbankverbindung
    - konto: Kontonummer (z.B. 830001)
    - subsidiary: 1=Stellantis, 2=Hyundai (Standard: 1)

    RÃ¼ckgabe: ErlÃ¶sart z.B. "VE GM OT an Kunde Mechanik"
    """
    cursor = db.cursor()

    # 1. Aus Locosoft Konten-Stammdaten
    cursor.execute(convert_placeholders("""
        SELECT account_description
        FROM loco_nominal_accounts
        WHERE nominal_account_number = ?
          AND subsidiary_to_company_ref = ?
        LIMIT 1
    """), (konto, subsidiary))
    result = cursor.fetchone()

    if result:
        result = row_to_dict(result)
        if result.get('account_description'):
            return result['account_description']

    # 2. Fallback: Andere Subsidiary probieren
    cursor.execute(convert_placeholders("""
        SELECT account_description
        FROM loco_nominal_accounts
        WHERE nominal_account_number = ?
        LIMIT 1
    """), (konto,))
    result = cursor.fetchone()

    if result:
        result = row_to_dict(result)
        if result.get('account_description'):
            return result['account_description']

    # 3. Fallback: Generische Bezeichnung
    prefix = str(konto)[:2]
    gruppen_namen = {
        '81': 'ErlÃ¶se Neuwagen', '82': 'ErlÃ¶se Gebrauchtwagen',
        '83': 'ErlÃ¶se Teile', '84': 'ErlÃ¶se Lohn',
        '71': 'Einsatz Neuwagen', '72': 'Einsatz Gebrauchtwagen',
        '73': 'Einsatz Teile', '74': 'Einsatz Lohn',
    }
    gruppe = gruppen_namen.get(prefix, '')
    return f"{gruppe} ({konto})" if gruppe else f"Konto {konto}"

@controlling_bp.route('/api/tek/detail')
@login_required
def api_tek_detail():
    """
    API: Drill-Down fÃ¼r TEK-Bereiche - Hierarchisch (Gruppen -> Konten -> Buchungen)
    
    Parameter:
    - bereich: '1-NW', '2-GW', '3-Teile', '4-Lohn', '5-Sonst'
    - firma, standort, monat, jahr: Filter (wie bei /api/tek)
    - ebene: 'gruppen' (Standard), 'konten', oder 'buchungen'
    - gruppe: (optional) 2-stelliges PrÃ¤fix fÃ¼r Konten-Detail (z.B. '81')
    - konto: (optional) FÃ¼r Buchungs-Details eines bestimmten Kontos
    - typ: 'umsatz' oder 'einsatz' (fÃ¼r Konten/Buchungen)
    """
    try:
        bereich = request.args.get('bereich', '2-GW')
        firma = request.args.get('firma', '0')
        standort = request.args.get('standort', '0')
        monat = request.args.get('monat', type=int)
        jahr = request.args.get('jahr', type=int)
        ebene = request.args.get('ebene', 'gruppen')  # 'gruppen', 'konten', 'buchungen'
        gruppe = request.args.get('gruppe', '')  # z.B. '81', '71'
        konto = request.args.get('konto', type=int)
        typ = request.args.get('typ', 'umsatz')  # 'umsatz' oder 'einsatz'
        
        heute = date.today()
        if not monat:
            monat = heute.month
        if not jahr:
            jahr = heute.year
        
        von = f"{jahr}-{monat:02d}-01"
        bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"
        
        db = get_db()
        
        # Firma/Standort-Filter bauen
        firma_filter = ""
        subsidiary = 1  # Default: Stellantis
        if firma == '1':
            firma_filter = "AND subsidiary_to_company_ref = 1"
            subsidiary = 1
            if standort == '1':
                firma_filter += " AND branch_number = 1"
            elif standort == '2':
                firma_filter += " AND branch_number = 3"
        elif firma == '2':
            firma_filter = "AND subsidiary_to_company_ref = 2"
            subsidiary = 2
        
        # Bereichs-Mapping: TEK-Bereich -> Konten-Ranges
        bereich_konten = {
            '1-NW': {'umsatz': (810000, 819999), 'einsatz': (710000, 719999)},
            '2-GW': {'umsatz': (820000, 829999), 'einsatz': (720000, 729999)},
            '3-Teile': {'umsatz': (830000, 839999), 'einsatz': (730000, 739999)},
            '4-Lohn': {'umsatz': (840000, 849999), 'einsatz': (740000, 749999)},
            '5-Sonst': {'umsatz': (860000, 869999), 'einsatz': (760000, 769999)}
        }
        
        # Gruppen-Bezeichnungen (SKR51)
        gruppen_namen = {
            # Umsatz
            '81': 'ErlÃ¶se Neuwagen', '82': 'ErlÃ¶se Gebrauchtwagen', 
            '83': 'ErlÃ¶se Teile', '84': 'ErlÃ¶se Lohn',
            '85': 'ErlÃ¶se Lack', '86': 'Sonstige ErlÃ¶se', '88': 'ErlÃ¶se Vermietung',
            '89': 'Sonstige betriebliche ErtrÃ¤ge',
            # Einsatz
            '71': 'Einsatz Neuwagen', '72': 'Einsatz Gebrauchtwagen',
            '73': 'Einsatz Teile', '74': 'Einsatz Lohn',
            '75': 'Einsatz Lack', '76': 'Sonstiger Einsatz', '78': 'Einsatz Vermietung',
        }
        
        if bereich not in bereich_konten:
            return jsonify({'success': False, 'error': f'Unbekannter Bereich: {bereich}'}), 400
        
        ranges = bereich_konten[bereich]
        
        # =====================================================================
        # EBENE: BUCHUNGEN (Detail fÃ¼r ein Konto)
        # =====================================================================
        if ebene == 'buchungen' and konto:
            # Vorzeichen basierend auf Kontotyp
            if str(konto).startswith('7'):
                vorzeichen = "CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END"
            else:
                vorzeichen = "CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END"

            cursor = db.cursor()
            cursor.execute(convert_placeholders(f"""
                SELECT
                    accounting_date as datum,
                    document_number as beleg_nr,
                    COALESCE(NULLIF(posting_text, ''), NULLIF(free_form_accounting_text, ''), NULLIF(contra_account_text, ''), '-') as buchungstext,
                    {vorzeichen} / 100.0 as betrag,
                    debit_or_credit as soll_haben,
                    vehicle_reference as fahrzeug,
                    customer_number as kunden_nr,
                    invoice_number as rechnung_nr
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number = ?
                  {firma_filter}
                ORDER BY accounting_date, document_number
            """), (von, bis, konto))
            buchungen = [row_to_dict(r) for r in cursor.fetchall()]

            db.close()

            return jsonify({
                'success': True,
                'ebene': 'buchungen',
                'konto': konto,
                'buchungen': [{
                    'datum': str(row['datum']),
                    'beleg_nr': row['beleg_nr'],
                    'buchungstext': row['buchungstext'],
                    'betrag': round(float(row['betrag'] or 0), 2),
                    'soll_haben': row['soll_haben'],
                    'fahrzeug': row['fahrzeug'] or '',
                    'kunden_nr': row['kunden_nr'] or '',
                    'rechnung_nr': row['rechnung_nr'] or ''
                } for row in buchungen],
                'anzahl': len(buchungen)
            }), 200
        
        # =====================================================================
        # EBENE: KONTEN (Detail fÃ¼r eine Gruppe, z.B. '81')
        # =====================================================================
        if ebene == 'konten' and gruppe:
            # Bestimme Range und Vorzeichen basierend auf Typ
            if typ == 'einsatz':
                konto_range = ranges['einsatz']
                vorzeichen = "CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END"
            else:
                konto_range = ranges['umsatz']
                vorzeichen = "CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END"

            cursor = db.cursor()
            # TAG 136: PostgreSQL erlaubt kein HAVING mit Alias, nutze Subquery
            cursor.execute(convert_placeholders(f"""
                SELECT * FROM (
                    SELECT
                        nominal_account_number as konto,
                        MIN(posting_text) as bezeichnung,
                        SUM({vorzeichen}) / 100.0 as betrag,
                        COUNT(*) as buchungen_anzahl
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND nominal_account_number BETWEEN ? AND ?
                      AND substr(CAST(nominal_account_number AS TEXT), 1, 2) = ?
                      {firma_filter}
                    GROUP BY nominal_account_number
                ) sub WHERE betrag != 0
                ORDER BY ABS(betrag) DESC
            """), (von, bis, konto_range[0], konto_range[1], gruppe))
            konten = [row_to_dict(r) for r in cursor.fetchall()]

            summe = sum(float(row['betrag'] or 0) for row in konten)
            gruppe_name = gruppen_namen.get(gruppe, f'Gruppe {gruppe}')

            # Konten mit Bezeichnungen aus loco_nominal_accounts
            konten_liste = [{
                'konto': row['konto'],
                'bezeichnung': get_konto_bezeichnung(db, row['konto'], subsidiary),
                'betrag': round(float(row['betrag'] or 0), 2),
                'buchungen_anzahl': int(row['buchungen_anzahl'])
            } for row in konten]

            db.close()

            return jsonify({
                'success': True,
                'ebene': 'konten',
                'bereich': bereich,
                'typ': typ,
                'gruppe': gruppe,
                'gruppe_name': gruppe_name,
                'konten': konten_liste,
                'summe': round(summe, 2),
                'anzahl_konten': len(konten_liste)
            }), 200
        
        # =====================================================================
        # EBENE: GRUPPEN (Standard - 2-stellige Kontengruppen) TAG 136
        # =====================================================================
        def hole_gruppen(konto_range, vorzeichen_typ, mit_konten=False):
            if vorzeichen_typ == 'einsatz':
                vorzeichen = "CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END"
            else:
                vorzeichen = "CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END"

            cursor = db.cursor()
            # TAG 136: PostgreSQL erlaubt kein HAVING mit Alias, nutze Subquery
            cursor.execute(convert_placeholders(f"""
                SELECT * FROM (
                    SELECT
                        substr(CAST(nominal_account_number AS TEXT), 1, 2) as gruppe,
                        SUM({vorzeichen}) / 100.0 as betrag,
                        COUNT(DISTINCT nominal_account_number) as anzahl_konten,
                        COUNT(*) as buchungen_anzahl
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND nominal_account_number BETWEEN ? AND ?
                      {firma_filter}
                    GROUP BY substr(CAST(nominal_account_number AS TEXT), 1, 2)
                ) sub WHERE betrag != 0
                ORDER BY ABS(betrag) DESC
            """), (von, bis, konto_range[0], konto_range[1]))
            rows = [row_to_dict(r) for r in cursor.fetchall()]

            ergebnis = []
            for row in rows:
                g = {
                    'gruppe': row['gruppe'],
                    'name': gruppen_namen.get(row['gruppe'], f"Gruppe {row['gruppe']}"),
                    'betrag': round(float(row['betrag'] or 0), 2),
                    'anzahl_konten': int(row['anzahl_konten']),
                    'buchungen_anzahl': int(row['buchungen_anzahl'])
                }

                # Optional: Einzelkonten fÃ¼r Drill-Down laden
                if mit_konten:
                    cursor.execute(convert_placeholders(f"""
                        SELECT * FROM (
                            SELECT
                                j.nominal_account_number as konto,
                                COALESCE(n.account_description, MIN(j.posting_text)) as bezeichnung,
                                SUM({vorzeichen}) / 100.0 as betrag,
                                COUNT(*) as buchungen_anzahl
                            FROM loco_journal_accountings j
                            LEFT JOIN loco_nominal_accounts n
                                ON j.nominal_account_number = n.nominal_account_number
                                AND j.subsidiary_to_company_ref = n.subsidiary_to_company_ref
                            WHERE j.accounting_date >= ? AND j.accounting_date < ?
                              AND j.nominal_account_number BETWEEN ? AND ?
                              AND substr(CAST(j.nominal_account_number AS TEXT), 1, 2) = ?
                              {firma_filter.replace('subsidiary_to_company_ref', 'j.subsidiary_to_company_ref').replace('branch_number', 'j.branch_number')}
                            GROUP BY j.nominal_account_number, n.account_description
                        ) sub WHERE betrag != 0
                        ORDER BY ABS(betrag) DESC
                    """), (von, bis, konto_range[0], konto_range[1], row['gruppe']))
                    konten_rows = [row_to_dict(kr) for kr in cursor.fetchall()]
                    g['konten'] = [{
                        'konto': kr['konto'],
                        'bezeichnung': kr['bezeichnung'] or '',
                        'betrag': round(float(kr['betrag'] or 0), 2),
                        'buchungen_anzahl': int(kr['buchungen_anzahl'])
                    } for kr in konten_rows]

                ergebnis.append(g)

            return ergebnis
        
        # Umsatz-Gruppen (mit Einzelkonten fÃ¼r Drill-Down)
        umsatz_gruppen = hole_gruppen(ranges['umsatz'], 'umsatz', mit_konten=True)
        umsatz_summe = sum(g['betrag'] for g in umsatz_gruppen)

        # Einsatz-Gruppen (mit Einzelkonten fÃ¼r Drill-Down)
        einsatz_gruppen = hole_gruppen(ranges['einsatz'], 'einsatz', mit_konten=True)
        einsatz_summe = sum(g['betrag'] for g in einsatz_gruppen)

        db1 = umsatz_summe - einsatz_summe

        # =====================================================================
        # FAHRZEUG-GRUPPIERUNG nach Modell + Absatzweg (nur fÃ¼r NW, GW)
        # TAG 136: Nutzt bestehende parse_modell_aus_kontobezeichnung Logik
        # Format Kontobezeichnung: "NW VE Corsa an Kd Leas" -> Modell, Kundentyp, Verkaufsart
        # =====================================================================
        fahrzeuge = []
        absatzwege = []
        if bereich in ['1-NW', '2-GW']:
            cursor = db.cursor()

            # Nach Modell und Absatzweg gruppieren
            modell_stats = {}
            absatzweg_stats = {}

            # 1. Umsatz-Konten holen (mit Kontobezeichnung aus loco_nominal_accounts)
            cursor.execute(convert_placeholders(f"""
                SELECT
                    j.nominal_account_number as konto,
                    COALESCE(n.account_description, MIN(j.posting_text)) as bezeichnung,
                    SUM(CASE WHEN j.debit_or_credit = 'H' THEN j.posted_value ELSE -j.posted_value END) / 100.0 as betrag,
                    COUNT(DISTINCT SUBSTRING(j.vehicle_reference FROM 'FG:([A-Z0-9]+)')) as stueck
                FROM loco_journal_accountings j
                LEFT JOIN loco_nominal_accounts n
                    ON j.nominal_account_number = n.nominal_account_number
                    AND j.subsidiary_to_company_ref = n.subsidiary_to_company_ref
                WHERE j.accounting_date >= ? AND j.accounting_date < ?
                  AND j.nominal_account_number BETWEEN ? AND ?
                  {firma_filter.replace('subsidiary_to_company_ref', 'j.subsidiary_to_company_ref').replace('branch_number', 'j.branch_number')}
                GROUP BY j.nominal_account_number, n.account_description
            """), (von, bis, ranges['umsatz'][0], ranges['umsatz'][1]))

            for row in cursor.fetchall():
                r = row_to_dict(row)
                konto = r.get('konto', 0)
                bezeichnung = r.get('bezeichnung', '') or ''
                betrag = float(r.get('betrag', 0) or 0)
                stueck = int(r.get('stueck', 0) or 0)

                parsed = parse_modell_aus_kontobezeichnung(bezeichnung)
                modell = normalisiere_fibu_modell(parsed['modell'])
                kundentyp = normalisiere_kundentyp(parsed['kundentyp'])
                verkaufsart = normalisiere_verkaufsart(parsed['verkaufsart'])

                # Modell-Statistik (Umsatz) mit Konten-Details fÃ¼r Drill-Down
                if modell not in modell_stats:
                    modell_stats[modell] = {'modell': modell, 'stueck': 0, 'umsatz': 0, 'einsatz': 0, 'konten': []}
                modell_stats[modell]['stueck'] += stueck
                modell_stats[modell]['umsatz'] += betrag
                modell_stats[modell]['konten'].append({
                    'konto': konto,
                    'bezeichnung': bezeichnung,
                    'umsatz': betrag,
                    'einsatz': 0,
                    'stueck': stueck
                })

                # Absatzweg-Statistik (Umsatz) mit Konten fÃ¼r Drill-Down
                absatzweg = f"{kundentyp} {verkaufsart}".strip() or 'Sonstige'
                if absatzweg not in absatzweg_stats:
                    absatzweg_stats[absatzweg] = {'absatzweg': absatzweg, 'stueck': 0, 'umsatz': 0, 'einsatz': 0, 'konten': []}
                absatzweg_stats[absatzweg]['stueck'] += stueck
                absatzweg_stats[absatzweg]['umsatz'] += betrag
                absatzweg_stats[absatzweg]['konten'].append({
                    'konto': konto,
                    'bezeichnung': bezeichnung,
                    'umsatz': betrag,
                    'einsatz': 0,
                    'stueck': stueck
                })

            # 2. Einsatz-Konten holen (mit Kontobezeichnung aus loco_nominal_accounts)
            cursor.execute(convert_placeholders(f"""
                SELECT
                    j.nominal_account_number as konto,
                    COALESCE(n.account_description, MIN(j.posting_text)) as bezeichnung,
                    SUM(CASE WHEN j.debit_or_credit = 'S' THEN j.posted_value ELSE -j.posted_value END) / 100.0 as betrag
                FROM loco_journal_accountings j
                LEFT JOIN loco_nominal_accounts n
                    ON j.nominal_account_number = n.nominal_account_number
                    AND j.subsidiary_to_company_ref = n.subsidiary_to_company_ref
                WHERE j.accounting_date >= ? AND j.accounting_date < ?
                  AND j.nominal_account_number BETWEEN ? AND ?
                  {firma_filter.replace('subsidiary_to_company_ref', 'j.subsidiary_to_company_ref').replace('branch_number', 'j.branch_number')}
                GROUP BY j.nominal_account_number, n.account_description
            """), (von, bis, ranges['einsatz'][0], ranges['einsatz'][1]))

            for row in cursor.fetchall():
                r = row_to_dict(row)
                bezeichnung = r.get('bezeichnung', '') or ''
                betrag = float(r.get('betrag', 0) or 0)

                parsed = parse_modell_aus_kontobezeichnung(bezeichnung)
                modell = normalisiere_fibu_modell(parsed['modell'])
                kundentyp = normalisiere_kundentyp(parsed['kundentyp'])
                verkaufsart = normalisiere_verkaufsart(parsed['verkaufsart'])

                konto = r.get('konto', '')

                # Modell-Statistik (Einsatz) - auch anlegen wenn nur Einsatz ohne Umsatz!
                if modell not in modell_stats:
                    modell_stats[modell] = {'modell': modell, 'stueck': 0, 'umsatz': 0, 'einsatz': 0, 'konten': []}
                modell_stats[modell]['einsatz'] += betrag
                # Auch Einsatz-Konten zum Drill-Down hinzufÃ¼gen
                modell_stats[modell]['konten'].append({
                    'konto': konto,
                    'bezeichnung': bezeichnung,
                    'umsatz': 0,
                    'einsatz': betrag,
                    'stueck': 0
                })

                # Absatzweg-Statistik (Einsatz) - auch anlegen wenn nur Einsatz ohne Umsatz!
                absatzweg = f"{kundentyp} {verkaufsart}".strip() or 'Sonstige'
                if absatzweg not in absatzweg_stats:
                    absatzweg_stats[absatzweg] = {'absatzweg': absatzweg, 'stueck': 0, 'umsatz': 0, 'einsatz': 0, 'konten': []}
                absatzweg_stats[absatzweg]['einsatz'] += betrag
                # Auch Einsatz-Konten zum Drill-Down hinzufÃ¼gen
                absatzweg_stats[absatzweg]['konten'].append({
                    'konto': konto,
                    'bezeichnung': bezeichnung,
                    'umsatz': 0,
                    'einsatz': betrag,
                    'stueck': 0
                })

            # Modelle in Liste umwandeln (mit DB1 und Einzelkonten fÃ¼r Drill-Down)
            fahrzeuge = [
                {
                    'modell': m['modell'],
                    'stueck': m['stueck'],
                    'umsatz': round(m['umsatz'], 2),
                    'einsatz': round(m['einsatz'], 2),
                    'db1': round(m['umsatz'] - m['einsatz'], 2),
                    'db1_pro_stueck': round((m['umsatz'] - m['einsatz']) / m['stueck'], 2) if m['stueck'] > 0 else 0,
                    'konten': m.get('konten', [])  # Einzelkonten fÃ¼r Drill-Down
                }
                for m in modell_stats.values() if m['umsatz'] > 0 or m['einsatz'] > 0
            ]
            # Intelligente Sortierung: Echte Modelle oben (alphabetisch), Sammelposten unten
            def sortkey_modell(item):
                m = item['modell'].lower()
                # Diese Begriffe ans Ende sortieren
                nachrangig = ['sonstig', 'umlage', 'erlÃ¶s', 'erloes', 'kosten', 'zubehÃ¶r', 'zubehoer',
                              'garantie', 'bonus', 'prÃ¤mie', 'praemie', 'provision', 'rabatt']
                for begriff in nachrangig:
                    if begriff in m:
                        return (1, item['modell'])  # Nach hinten
                return (0, item['modell'])  # Normale alphabetische Sortierung
            fahrzeuge.sort(key=sortkey_modell)

            # Absatzwege in Liste umwandeln (mit DB1 und Konten fÃ¼r Drill-Down)
            absatzwege = [
                {
                    'absatzweg': a['absatzweg'],
                    'stueck': a['stueck'],
                    'umsatz': round(a['umsatz'], 2),
                    'einsatz': round(a['einsatz'], 2),
                    'db1': round(a['umsatz'] - a['einsatz'], 2),
                    'db1_pro_stueck': round((a['umsatz'] - a['einsatz']) / a['stueck'], 2) if a['stueck'] > 0 else 0,
                    'konten': a.get('konten', [])  # Einzelkonten fÃ¼r Drill-Down
                }
                for a in absatzweg_stats.values() if a['umsatz'] > 0 or a['einsatz'] > 0
            ]
            absatzwege.sort(key=lambda x: x['absatzweg'])  # Alphabetisch nach Absatzweg

        db.close()

        return jsonify({
            'success': True,
            'ebene': 'gruppen',
            'bereich': bereich,
            'filter': {
                'firma': firma,
                'standort': standort,
                'monat': monat,
                'jahr': jahr,
                'von': von,
                'bis': bis
            },
            'umsatz': {
                'gruppen': umsatz_gruppen,
                'summe': round(umsatz_summe, 2),
                'anzahl_gruppen': len(umsatz_gruppen),
                'gesamt': round(umsatz_summe, 2)
            },
            'einsatz': {
                'gruppen': einsatz_gruppen,
                'summe': round(einsatz_summe, 2),
                'anzahl_gruppen': len(einsatz_gruppen),
                'gesamt': round(einsatz_summe, 2)
            },
            'db1': round(db1, 2),
            'fahrzeuge': fahrzeuge,   # TAG 136: Modell-Gruppierung
            'absatzwege': absatzwege  # TAG 136: Absatzweg-Gruppierung (Kundentyp + Verkaufsart)
        }), 200
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


# =============================================================================
# TEK MODELL-ANSICHT - FahrzeugstÃ¼cke nach Modell gruppiert
# =============================================================================

def parse_modell_aus_kontobezeichnung(bezeichnung: str) -> dict:
    """
    Extrahiert Modell, Kundentyp und Verkaufsart aus Kontobezeichnung.

    Format NW: "NW VE [Modell] an [Kundentyp] [Verkaufsart]"
    Format GW: "VE GW aus [Herkunft] an [Kundentyp] [Verkaufsart]"

    Beispiele NW:
    - "NW VE Corsa an Kd Leas" -> {modell: "Corsa", kundentyp: "Kd", verkaufsart: "Leas"}
    - "NW EW Astra an Gewkd Kauf" -> {modell: "Astra", kundentyp: "Gewkd", verkaufsart: "Kauf"}

    Beispiele GW:
    - "VE GW aus Eint an Kd reg" -> {modell: "GW Eintausch", kundentyp: "Kd", verkaufsart: "reg", herkunft: "Eintausch"}
    - "VE GW aus Zuk an Kd reg" -> {modell: "GW Zukauf", kundentyp: "Kd", verkaufsart: "reg", herkunft: "Zukauf"}
    """
    if not bezeichnung:
        return {'modell': 'Sonstige', 'kundentyp': '', 'verkaufsart': '', 'herkunft': '', 'raw': bezeichnung}

    bez = bezeichnung.strip()

    # GW-Sonderbehandlung: "VE GW aus [Herkunft] an ..." oder "VE GW a.Rent/VW Kd reg"
    import re
    gw_match = re.match(r'(?:VE |EW )?GW (?:aus |a\.)?([\w/]+)\s+(?:an\s+)?(.+)', bez)
    if gw_match:
        herkunft_raw = gw_match.group(1)
        rest = gw_match.group(2).strip()

        # Herkunft normalisieren
        herkunft_mapping = {
            'Eint': 'Eintausch',
            'Zuk': 'Zukauf',
            'Leasing': 'Leasing',
            'Rent/VW': 'Rent/Vermitwg',
            'Rent': 'Rent/Vermitwg'
        }
        herkunft = herkunft_mapping.get(herkunft_raw, herkunft_raw)
        modell = f"GW {herkunft}"

        # Kundentyp und Verkaufsart parsen (gleiche Logik wie NW)
        kundentyp = ''
        verkaufsart = ''
        kundentyp_patterns = [
            ('Gewerbekd ', 'Gewerbe'),
            ('Gewdkd ', 'Gewerbe'),   # Tippfehler in Locosoft
            ('Gewkd ', 'Gewerbe'),
            ('GroÃŸkunden ', 'GroÃŸkunde'),
            ('GroÃŸkd ', 'GroÃŸkunde'),
            ('Kunden ', 'Privat'),
            ('KD ', 'Privat'),
            ('Kd ', 'Privat'),
            ('HÃ¤ndler ', 'HÃ¤ndler'),
        ]
        for pattern, typ in kundentyp_patterns:
            if rest.startswith(pattern) or f' {pattern}' in f' {rest}':
                kundentyp = typ
                rest = rest.replace(pattern.strip(), '').strip()
                break
        verkaufsart = rest.strip()

        return {
            'modell': modell,
            'kundentyp': kundentyp,
            'verkaufsart': verkaufsart,
            'herkunft': herkunft,
            'raw': bezeichnung
        }

    # NW-Verarbeitung: Prefixe entfernen
    for prefix in ['NW VE ', 'NW EW ', 'GW VE ', 'GW EW ', 'VE ', 'EW ']:
        if bez.startswith(prefix):
            bez = bez[len(prefix):]
            break

    # Bekannte Kundentypen (inkl. Tippfehler-Varianten aus Locosoft)
    # Reihenfolge wichtig: lÃ¤ngere zuerst, um "Gewerbekd" vor "Gewkd" zu matchen
    kundentyp_patterns = [
        ('Gewerbekd ', 'Gewerbe'),
        ('Gewdkd ', 'Gewerbe'),   # Tippfehler in Locosoft
        ('Gewkd ', 'Gewerbe'),
        ('GroÃŸkunden ', 'GroÃŸkunde'),
        ('GroÃŸkd ', 'GroÃŸkunde'),
        ('Kunden ', 'Privat'),
        ('KD ', 'Privat'),
        ('Kd ', 'Privat'),
        ('HÃ¤ndler ', 'HÃ¤ndler'),
    ]

    # Split bei " an " (z.B. "Combo Van an Gewkd Kauf")
    if ' an ' in bez:
        teile = bez.split(' an ', 1)
        modell = teile[0].strip()
        rest = teile[1].strip() if len(teile) > 1 else ''

        # Kundentyp und Verkaufsart parsen
        kundentyp = ''
        verkaufsart = ''
        for pattern, typ in kundentyp_patterns:
            if rest.startswith(pattern) or f' {pattern}' in f' {rest}':
                kundentyp = typ
                rest = rest.replace(pattern.strip(), '').strip()
                break

        verkaufsart = rest.strip()
        return {
            'modell': modell,
            'kundentyp': kundentyp,
            'verkaufsart': verkaufsart,
            'herkunft': '',
            'raw': bezeichnung
        }

    # Kein " an " - aber vielleicht Format "Combo Van Gewkd Kauf" (ohne "an")
    # Suche Kundentyp-Pattern im String
    kundentyp = ''
    verkaufsart = ''
    modell = bez

    for pattern, typ in kundentyp_patterns:
        # Suche Pattern (mit Leerzeichen davor fÃ¼r Wortgrenze)
        idx = bez.find(f' {pattern.strip()}')
        if idx == -1:
            idx = bez.find(pattern.strip())  # Am Anfang?
        if idx != -1:
            # Modell ist alles vor dem Kundentyp
            modell = bez[:idx].strip()
            rest = bez[idx:].strip()
            kundentyp = typ
            # Rest nach Kundentyp ist Verkaufsart
            rest = rest.replace(pattern.strip(), '').strip()
            verkaufsart = rest
            break

    # Verkaufsart normalisieren falls gefunden
    if verkaufsart:
        return {
            'modell': modell,
            'kundentyp': kundentyp,
            'verkaufsart': verkaufsart,
            'herkunft': '',
            'raw': bezeichnung
        }

    # Nichts gefunden - gesamter Text als Modell
    return {'modell': bez, 'kundentyp': '', 'verkaufsart': '', 'herkunft': '', 'raw': bezeichnung}


def normalisiere_kundentyp(kundentyp: str) -> str:
    """Normalisiert Kundentyp-Bezeichnungen"""
    if not kundentyp:
        return 'Sonstige'
    # Bereits normalisiert?
    if kundentyp in ['Privat', 'Gewerbe', 'GroÃŸkunde', 'HÃ¤ndler', 'Sonstige']:
        return kundentyp
    # Mapping fÃ¼r Rohwerte aus Kontobezeichnung
    mapping = {
        'Kunden': 'Privat',
        'Kd': 'Privat',
        'KD': 'Privat',
        'Gewkd': 'Gewerbe',
        'Gewdkd': 'Gewerbe',  # Tippfehler in Locosoft
        'Gewerbekd': 'Gewerbe',
        'GroÃŸkd': 'GroÃŸkunde',
        'GroÃŸkunden': 'GroÃŸkunde',
        'HÃ¤ndler': 'HÃ¤ndler'
    }
    return mapping.get(kundentyp, kundentyp)


def normalisiere_verkaufsart(verkaufsart: str) -> str:
    """Normalisiert Verkaufsart-Bezeichnungen"""
    va = verkaufsart.lower()
    if 'leas' in va:
        return 'Leasing'
    elif 'kauf' in va or 'bar' in va:
        return 'Kauf'
    elif 'finanz' in va:
        return 'Finanzierung'
    return verkaufsart or 'Sonstige'


def kategorisiere_modell(modell: str) -> tuple:
    """
    Kategorisiert Modellnamen fÃ¼r bessere Gruppierung.

    Returns: (kategorie, sortierung)
        - kategorie: 'Fahrzeuge', 'VorfÃ¼hrwagen', 'Sonstige Fzg', 'NebenerlÃ¶se', 'Unbekannt'
        - sortierung: Zahl fÃ¼r Reihenfolge (1=oben, 5=unten)
    """
    if not modell:
        return ('Unbekannt', 5)

    m_lower = modell.lower()

    # Bekannte Fahrzeug-Modelle (aus MODELL_MAPPING)
    bekannte_modelle = ['astra', 'corsa', 'mokka', 'grandland', 'crossland', 'combo',
                        'vivaro', 'movano', 'zafira', 'frontera', 'leapmotor',
                        'kona', 'tucson', 'i10', 'i20', 'i30', 'ioniq', 'inster',
                        'santa', 'bayon', 'staria']

    for bm in bekannte_modelle:
        if bm in m_lower:
            return ('Fahrzeuge', 1)

    # VorfÃ¼hrwagen
    if 'vfw' in m_lower or 'vorfÃ¼hr' in m_lower:
        return ('VorfÃ¼hrwagen', 2)

    # Sonstige Fahrzeuge
    if 'sonst' in m_lower and ('fzg' in m_lower or 'pkw' in m_lower or 'nw' in m_lower or 'gw' in m_lower):
        return ('Sonstige Fzg', 3)

    # NebenerlÃ¶se (keine Fahrzeuge)
    if any(x in m_lower for x in ['umlage', 'zulassung', 'prov.', 'provision', 'garantie',
                                   'givit', 'finanz', 'sonst.verk', 'sonst.erl']):
        return ('NebenerlÃ¶se', 4)

    # Unbekannte Konten (nur Kontonummer)
    if modell.startswith('Konto ') or modell.isdigit():
        return ('Unbekannt', 5)

    # Fallback: Als Fahrzeug behandeln
    return ('Fahrzeuge', 1)


def get_fibu_modell_daten(von: str, bis: str, bereich: str, firma: str, standort: str, subsidiary: int) -> dict:
    """
    Holt FiBu-Daten fÃ¼r einen Zeitraum, gruppiert nach Modell.
    TAG 136: PostgreSQL-kompatibel

    Returns: dict mit {modell_name: {'umsatz': X, 'einsatz': Y, 'db1': Z}}
    """
    db = get_db()  # Eigene Verbindung erstellen
    cursor = db.cursor()

    # Firma/Standort-Filter
    firma_filter = ""
    if firma == '1':
        firma_filter = "AND j.subsidiary_to_company_ref = 1"
        if standort == '1':
            firma_filter += " AND j.branch_number = 1"
        elif standort == '2':
            firma_filter += " AND j.branch_number = 3"
    elif firma == '2':
        firma_filter = "AND j.subsidiary_to_company_ref = 2"

    # Bereichs-Konten
    bereich_konten = {
        '1-NW': {'umsatz': (810000, 819999), 'einsatz': (710000, 719999)},
        '2-GW': {'umsatz': (820000, 829999), 'einsatz': (720000, 729999)},
    }
    ranges = bereich_konten.get(bereich, bereich_konten['1-NW'])

    # Umsatz - TAG 136: PostgreSQL erlaubt kein HAVING mit Alias
    cursor.execute(convert_placeholders(f"""
        SELECT * FROM (
            SELECT
                j.nominal_account_number as konto,
                COALESCE(n.account_description, 'Konto ' || CAST(j.nominal_account_number AS TEXT)) as bezeichnung,
                SUM(CASE WHEN j.debit_or_credit = 'H' THEN j.posted_value ELSE -j.posted_value END) / 100.0 as betrag
            FROM loco_journal_accountings j
            LEFT JOIN loco_nominal_accounts n
                ON j.nominal_account_number = n.nominal_account_number
                AND n.subsidiary_to_company_ref = ?
            WHERE j.accounting_date >= ? AND j.accounting_date < ?
              AND j.nominal_account_number BETWEEN ? AND ?
              {firma_filter}
            GROUP BY j.nominal_account_number, n.account_description
        ) sub WHERE betrag != 0
    """), (subsidiary, von, bis, ranges['umsatz'][0], ranges['umsatz'][1]))
    umsatz_konten = [row_to_dict(r) for r in cursor.fetchall()]

    # Einsatz
    cursor.execute(convert_placeholders(f"""
        SELECT * FROM (
            SELECT
                j.nominal_account_number as konto,
                COALESCE(n.account_description, 'Konto ' || CAST(j.nominal_account_number AS TEXT)) as bezeichnung,
                SUM(CASE WHEN j.debit_or_credit = 'S' THEN j.posted_value ELSE -j.posted_value END) / 100.0 as betrag
            FROM loco_journal_accountings j
            LEFT JOIN loco_nominal_accounts n
                ON j.nominal_account_number = n.nominal_account_number
                AND n.subsidiary_to_company_ref = ?
            WHERE j.accounting_date >= ? AND j.accounting_date < ?
              AND j.nominal_account_number BETWEEN ? AND ?
              {firma_filter}
            GROUP BY j.nominal_account_number, n.account_description
        ) sub WHERE betrag != 0
    """), (subsidiary, von, bis, ranges['einsatz'][0], ranges['einsatz'][1]))
    einsatz_konten = [row_to_dict(r) for r in cursor.fetchall()]

    # Nach Modell gruppieren
    modell_daten = {}

    for row in umsatz_konten:
        parsed = parse_modell_aus_kontobezeichnung(row['bezeichnung'])
        modell = normalisiere_fibu_modell(parsed['modell'])
        if modell not in modell_daten:
            modell_daten[modell] = {'umsatz': 0, 'einsatz': 0}
        modell_daten[modell]['umsatz'] += float(row['betrag'] or 0)

    for row in einsatz_konten:
        parsed = parse_modell_aus_kontobezeichnung(row['bezeichnung'])
        modell = normalisiere_fibu_modell(parsed['modell'])
        if modell not in modell_daten:
            modell_daten[modell] = {'umsatz': 0, 'einsatz': 0}
        modell_daten[modell]['einsatz'] += float(row['betrag'] or 0)

    # DB1 berechnen
    for modell in modell_daten:
        modell_daten[modell]['db1'] = modell_daten[modell]['umsatz'] - modell_daten[modell]['einsatz']

    db.close()
    return modell_daten


@controlling_bp.route('/api/tek/modelle')
@login_required
def api_tek_modelle():
    """
    API: TEK-Daten gruppiert nach Fahrzeugmodell

    Zeigt Umsatz, Einsatz und DB1 pro Fahrzeugmodell an.
    Das Modell wird aus der Kontobezeichnung extrahiert.

    Parameter:
    - bereich: '1-NW' oder '2-GW' (Standard: '1-NW')
    - firma: 0=Alle, 1=Stellantis, 2=Hyundai
    - standort: 0=Alle, 1=Deggendorf, 2=Landau
    - monat, jahr: Zeitraum
    - gruppierung: 'modell' (Standard), 'modell_kundentyp', 'modell_verkaufsart', 'detail'
    """
    try:
        bereich = request.args.get('bereich', '1-NW')
        firma = request.args.get('firma', '0')
        standort = request.args.get('standort', '0')
        monat = request.args.get('monat', type=int)
        jahr = request.args.get('jahr', type=int)
        gruppierung = request.args.get('gruppierung', 'modell')  # modell, modell_kundentyp, modell_verkaufsart, detail

        heute = date.today()
        if not monat:
            monat = heute.month
        if not jahr:
            jahr = heute.year

        # Aktueller Monat
        von = f"{jahr}-{monat:02d}-01"
        bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"

        # Vormonat berechnen
        vm_monat = monat - 1 if monat > 1 else 12
        vm_jahr = jahr if monat > 1 else jahr - 1
        vm_von = f"{vm_jahr}-{vm_monat:02d}-01"
        vm_bis = f"{vm_jahr}-{vm_monat+1:02d}-01" if vm_monat < 12 else f"{vm_jahr+1}-01-01"

        # Vorjahr (gleicher Monat)
        vj_von = f"{jahr-1}-{monat:02d}-01"
        vj_bis = f"{jahr-1}-{monat+1:02d}-01" if monat < 12 else f"{jahr}-01-01"

        db = get_db()
        cursor = db.cursor()

        # Firma/Standort-Filter
        firma_filter = ""
        subsidiary = 1
        if firma == '1':
            firma_filter = "AND j.subsidiary_to_company_ref = 1"
            subsidiary = 1
            if standort == '1':
                firma_filter += " AND j.branch_number = 1"
            elif standort == '2':
                firma_filter += " AND j.branch_number = 3"
        elif firma == '2':
            firma_filter = "AND j.subsidiary_to_company_ref = 2"
            subsidiary = 2

        # Bereichs-Konten
        bereich_konten = {
            '1-NW': {'umsatz': (810000, 819999), 'einsatz': (710000, 719999)},
            '2-GW': {'umsatz': (820000, 829999), 'einsatz': (720000, 729999)},
        }

        if bereich not in bereich_konten:
            db.close()
            return jsonify({'success': False, 'error': f'Bereich {bereich} nicht unterstÃ¼tzt fÃ¼r Modell-Ansicht'}), 400

        ranges = bereich_konten[bereich]

        # =====================================================================
        # UMSATZ pro Konto (mit Bezeichnung aus loco_nominal_accounts) TAG 136
        # =====================================================================
        cursor.execute(convert_placeholders(f"""
            SELECT * FROM (
                SELECT
                    j.nominal_account_number as konto,
                    COALESCE(n.account_description, 'Konto ' || CAST(j.nominal_account_number AS TEXT)) as bezeichnung,
                    SUM(CASE WHEN j.debit_or_credit = 'H' THEN j.posted_value ELSE -j.posted_value END) / 100.0 as betrag,
                    COUNT(*) as buchungen
                FROM loco_journal_accountings j
                LEFT JOIN loco_nominal_accounts n
                    ON j.nominal_account_number = n.nominal_account_number
                    AND n.subsidiary_to_company_ref = ?
                WHERE j.accounting_date >= ? AND j.accounting_date < ?
                  AND j.nominal_account_number BETWEEN ? AND ?
                  {firma_filter}
                GROUP BY j.nominal_account_number, n.account_description
            ) sub WHERE betrag != 0
        """), (subsidiary, von, bis, ranges['umsatz'][0], ranges['umsatz'][1]))
        umsatz_konten = [row_to_dict(r) for r in cursor.fetchall()]

        # =====================================================================
        # EINSATZ pro Konto
        # =====================================================================
        cursor.execute(convert_placeholders(f"""
            SELECT * FROM (
                SELECT
                    j.nominal_account_number as konto,
                    COALESCE(n.account_description, 'Konto ' || CAST(j.nominal_account_number AS TEXT)) as bezeichnung,
                    SUM(CASE WHEN j.debit_or_credit = 'S' THEN j.posted_value ELSE -j.posted_value END) / 100.0 as betrag,
                    COUNT(*) as buchungen
                FROM loco_journal_accountings j
                LEFT JOIN loco_nominal_accounts n
                    ON j.nominal_account_number = n.nominal_account_number
                    AND n.subsidiary_to_company_ref = ?
                WHERE j.accounting_date >= ? AND j.accounting_date < ?
                  AND j.nominal_account_number BETWEEN ? AND ?
                  {firma_filter}
                GROUP BY j.nominal_account_number, n.account_description
            ) sub WHERE betrag != 0
        """), (subsidiary, von, bis, ranges['einsatz'][0], ranges['einsatz'][1]))
        einsatz_konten = [row_to_dict(r) for r in cursor.fetchall()]

        db.close()

        # =====================================================================
        # Modell extrahieren und gruppieren
        # =====================================================================
        modell_daten = {}  # Key: modell (oder modell+kundentyp etc.)

        # Umsatz verarbeiten
        for row in umsatz_konten:
            parsed = parse_modell_aus_kontobezeichnung(row['bezeichnung'])
            modell = normalisiere_fibu_modell(parsed['modell'])  # Normalisieren fÃ¼r Locosoft-Match
            kundentyp = normalisiere_kundentyp(parsed['kundentyp'])
            verkaufsart = normalisiere_verkaufsart(parsed['verkaufsart'])

            # Key basierend auf Gruppierung
            if gruppierung == 'modell':
                key = modell
            elif gruppierung == 'modell_kundentyp':
                key = f"{modell}|{kundentyp}"
            elif gruppierung == 'modell_verkaufsart':
                key = f"{modell}|{verkaufsart}"
            else:  # detail
                key = f"{modell}|{kundentyp}|{verkaufsart}"

            if key not in modell_daten:
                modell_daten[key] = {
                    'modell': modell,
                    'kundentyp': kundentyp if gruppierung != 'modell' else None,
                    'verkaufsart': verkaufsart if gruppierung in ['modell_verkaufsart', 'detail'] else None,
                    'umsatz': 0,
                    'einsatz': 0,
                    'buchungen_umsatz': 0,
                    'buchungen_einsatz': 0,
                    'konten_umsatz': [],
                    'konten_einsatz': []
                }

            modell_daten[key]['umsatz'] += row['betrag']
            modell_daten[key]['buchungen_umsatz'] += row['buchungen']
            modell_daten[key]['konten_umsatz'].append(row['konto'])

        # Einsatz verarbeiten
        for row in einsatz_konten:
            parsed = parse_modell_aus_kontobezeichnung(row['bezeichnung'])
            modell = normalisiere_fibu_modell(parsed['modell'])  # Normalisieren fÃ¼r Locosoft-Match
            kundentyp = normalisiere_kundentyp(parsed['kundentyp'])
            verkaufsart = normalisiere_verkaufsart(parsed['verkaufsart'])

            # Key basierend auf Gruppierung
            if gruppierung == 'modell':
                key = modell
            elif gruppierung == 'modell_kundentyp':
                key = f"{modell}|{kundentyp}"
            elif gruppierung == 'modell_verkaufsart':
                key = f"{modell}|{verkaufsart}"
            else:  # detail
                key = f"{modell}|{kundentyp}|{verkaufsart}"

            if key not in modell_daten:
                modell_daten[key] = {
                    'modell': modell,
                    'kundentyp': kundentyp if gruppierung != 'modell' else None,
                    'verkaufsart': verkaufsart if gruppierung in ['modell_verkaufsart', 'detail'] else None,
                    'umsatz': 0,
                    'einsatz': 0,
                    'buchungen_umsatz': 0,
                    'buchungen_einsatz': 0,
                    'konten_umsatz': [],
                    'konten_einsatz': []
                }

            modell_daten[key]['einsatz'] += row['betrag']
            modell_daten[key]['buchungen_einsatz'] += row['buchungen']
            modell_daten[key]['konten_einsatz'].append(row['konto'])

        # =====================================================================
        # DB1 und Marge berechnen, als Liste formatieren
        # =====================================================================
        modelle_liste = []
        for key, daten in modell_daten.items():
            db1 = daten['umsatz'] - daten['einsatz']
            marge = (db1 / daten['umsatz'] * 100) if daten['umsatz'] > 0 else 0

            # Kategorie ermitteln
            kategorie, sort_order = kategorisiere_modell(daten['modell'])

            eintrag = {
                'modell': daten['modell'],
                'kategorie': kategorie,
                'kategorie_sort': sort_order,
                'umsatz': round(daten['umsatz'], 2),
                'einsatz': round(daten['einsatz'], 2),
                'db1': round(db1, 2),
                'marge': round(marge, 1),
                'buchungen': daten['buchungen_umsatz'] + daten['buchungen_einsatz'],
                'konten_anzahl': len(set(daten['konten_umsatz'] + daten['konten_einsatz']))
            }

            if daten['kundentyp']:
                eintrag['kundentyp'] = daten['kundentyp']
            if daten['verkaufsart']:
                eintrag['verkaufsart'] = daten['verkaufsart']

            modelle_liste.append(eintrag)

        # =====================================================================
        # LOCOSOFT STÃœCKZAHLEN holen und mit FiBu-Daten mergen
        # =====================================================================
        stueckzahlen = get_stueckzahlen_locosoft(von, bis, bereich, firma, standort)
        gesamt_stueck = stueckzahlen.get('gesamt_stueck', 0)

        # StÃ¼ckzahlen zu den Modellen hinzufÃ¼gen (Fuzzy-Match nach Modellname)
        for eintrag in modelle_liste:
            modell_name = eintrag['modell']
            stueck_info = stueckzahlen['modelle'].get(modell_name)

            if stueck_info:
                eintrag['stueck'] = stueck_info['stueck']
                eintrag['avg_vk'] = stueck_info['avg_vk']
                # Durchschnitts-DB pro Fahrzeug berechnen
                if stueck_info['stueck'] > 0:
                    eintrag['avg_db1'] = round(eintrag['db1'] / stueck_info['stueck'], 2)
                else:
                    eintrag['avg_db1'] = 0
            else:
                # Kein Match in Locosoft gefunden
                eintrag['stueck'] = None
                eintrag['avg_vk'] = None
                eintrag['avg_db1'] = None

        # =====================================================================
        # VERGLEICHSDATEN: Vormonat und Vorjahr
        # =====================================================================
        # Vormonat-Daten holen
        vm_daten = get_fibu_modell_daten(vm_von, vm_bis, bereich, firma, standort, subsidiary)
        vm_stueck = get_stueckzahlen_locosoft(vm_von, vm_bis, bereich, firma, standort)

        # Vorjahr-Daten holen
        vj_daten = get_fibu_modell_daten(vj_von, vj_bis, bereich, firma, standort, subsidiary)
        vj_stueck = get_stueckzahlen_locosoft(vj_von, vj_bis, bereich, firma, standort)

        # Vergleichswerte zu jedem Modell hinzufÃ¼gen
        for eintrag in modelle_liste:
            modell_name = eintrag['modell']

            # Vormonat
            vm = vm_daten.get(modell_name, {})
            eintrag['vm_umsatz'] = round(vm.get('umsatz', 0), 2)
            eintrag['vm_db1'] = round(vm.get('db1', 0), 2)
            vm_s = vm_stueck.get('modelle', {}).get(modell_name, {})
            eintrag['vm_stueck'] = vm_s.get('stueck') if vm_s else None

            # Vorjahr
            vj = vj_daten.get(modell_name, {})
            eintrag['vj_umsatz'] = round(vj.get('umsatz', 0), 2)
            eintrag['vj_db1'] = round(vj.get('db1', 0), 2)
            vj_s = vj_stueck.get('modelle', {}).get(modell_name, {})
            eintrag['vj_stueck'] = vj_s.get('stueck') if vj_s else None

        # Nach Kategorie sortieren, dann nach Umsatz innerhalb der Kategorie
        modelle_liste.sort(key=lambda x: (x['kategorie_sort'], -x['umsatz']))

        # Gesamt aktueller Monat
        gesamt_umsatz = sum(m['umsatz'] for m in modelle_liste)
        gesamt_einsatz = sum(m['einsatz'] for m in modelle_liste)
        gesamt_db1 = gesamt_umsatz - gesamt_einsatz
        gesamt_marge = (gesamt_db1 / gesamt_umsatz * 100) if gesamt_umsatz > 0 else 0

        # Gesamt Vormonat
        gesamt_vm_umsatz = sum(m['vm_umsatz'] for m in modelle_liste)
        gesamt_vm_db1 = sum(m['vm_db1'] for m in modelle_liste)
        gesamt_vm_stueck = vm_stueck.get('gesamt_stueck', 0)

        # Gesamt Vorjahr
        gesamt_vj_umsatz = sum(m['vj_umsatz'] for m in modelle_liste)
        gesamt_vj_db1 = sum(m['vj_db1'] for m in modelle_liste)
        gesamt_vj_stueck = vj_stueck.get('gesamt_stueck', 0)

        monat_namen = ['', 'Januar', 'Februar', 'MÃ¤rz', 'April', 'Mai', 'Juni',
                       'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']

        return jsonify({
            'success': True,
            'bereich': bereich,
            'bereich_name': 'Neuwagen' if bereich == '1-NW' else 'Gebrauchtwagen',
            'gruppierung': gruppierung,
            'filter': {
                'firma': firma,
                'standort': standort,
                'monat': monat,
                'monat_name': monat_namen[monat],
                'jahr': jahr,
                'von': von,
                'bis': bis
            },
            'vergleich': {
                'vormonat': {
                    'monat': vm_monat,
                    'monat_name': monat_namen[vm_monat],
                    'jahr': vm_jahr,
                    'von': vm_von,
                    'bis': vm_bis
                },
                'vorjahr': {
                    'monat': monat,
                    'monat_name': monat_namen[monat],
                    'jahr': jahr - 1,
                    'von': vj_von,
                    'bis': vj_bis
                }
            },
            'modelle': modelle_liste,
            'anzahl_modelle': len(modelle_liste),
            'gesamt': {
                'umsatz': round(gesamt_umsatz, 2),
                'einsatz': round(gesamt_einsatz, 2),
                'db1': round(gesamt_db1, 2),
                'marge': round(gesamt_marge, 1),
                'stueck': gesamt_stueck,
                'vm_umsatz': round(gesamt_vm_umsatz, 2),
                'vm_db1': round(gesamt_vm_db1, 2),
                'vm_stueck': gesamt_vm_stueck,
                'vj_umsatz': round(gesamt_vj_umsatz, 2),
                'vj_db1': round(gesamt_vj_db1, 2),
                'vj_stueck': gesamt_vj_stueck
            },
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


# =============================================================================
# VOLLKOSTEN-BERECHNUNG
# =============================================================================

def berechne_vollkosten(von: str, bis: str, firma_filter: str, standort: str = '0', umlage_kosten_filter: str = '') -> dict:
    """
    Berechnet Vollkosten nach Kostenstellen (5. Stelle der Kontonummer)
    TAG 136: PostgreSQL-kompatibel - nutzt intern db_session()

    Kostenstellen (5. Stelle):
    - 0 = Verwaltung/Indirekt (wird umgelegt)
    - 1 = Neuwagen
    - 2 = Gebrauchtwagen
    - 3 = Service/Mechanik
    - 6 = Teile
    - 7 = Mietwagen/Sonstige

    Umlage nach MA-SchlÃ¼ssel aus employees-Tabelle (gefiltert nach Standort)

    Parameter:
    - umlage_kosten_filter: Optionaler Filter um Umlage-Kosten auszuschlieÃŸen (498001)
    """

    # MA-Verteilung holen (mit Standort-Filter)
    ma_verteilung = get_ma_verteilung(standort)

    # Produktive KST (ohne Verwaltung)
    produktiv_kst = ['12', '3', '6']  # 12=Verkauf(1+2), 3=Service, 6=Teile
    produktiv_ma = sum(ma_verteilung.get(k, 0) for k in produktiv_kst)

    # Umlage-SchlÃ¼ssel berechnen
    umlage_schluessel = {}
    for kst in produktiv_kst:
        ma = ma_verteilung.get(kst, 0)
        umlage_schluessel[kst] = round(ma / produktiv_ma * 100, 1) if produktiv_ma > 0 else 0

    with db_session() as conn:
        cursor = conn.cursor()

        # =========================================================================
        # VARIABLE KOSTEN nach KST (5. Stelle)
        # Konten: 4151xx, 4355xx, 455-456xx, 487xx, 491-497xx
        # HINWEIS: umlage_kosten_filter auch hier anwenden fÃ¼r Konsistenz
        # =========================================================================
        variable_sql = convert_placeholders(f"""
            SELECT
                substr(CAST(nominal_account_number AS TEXT), 5, 1) as kst,
                SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as summe
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND (nominal_account_number BETWEEN 415100 AND 415199
                   OR nominal_account_number BETWEEN 435500 AND 435599
                   OR (nominal_account_number BETWEEN 455000 AND 456999 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                   OR (nominal_account_number BETWEEN 487000 AND 487099 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                   OR nominal_account_number BETWEEN 491000 AND 497899)
              {firma_filter}
              {umlage_kosten_filter}
            GROUP BY kst
        """)

        cursor.execute(variable_sql, (von, bis))
        variable_rows = cursor.fetchall()
        variable = {row_to_dict(r)['kst']: float(row_to_dict(r)['summe'] or 0) for r in variable_rows}

        # =========================================================================
        # DIREKTE KOSTEN nach KST (nur KST 1-7, ohne Variable)
        # Konten: 40-48xxxx mit KST != 0
        # WICHTIG: umlage_kosten_filter filtert HABEN-Buchungen mit "Kostenumlage" Text
        #          (z.B. auf 440001, 415001, etc.) - diese haben negative Werte!
        # =========================================================================
        direkte_sql = convert_placeholders(f"""
            SELECT
                substr(CAST(nominal_account_number AS TEXT), 5, 1) as kst,
                SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as summe
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 400000 AND 489999
              AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
              AND NOT (nominal_account_number BETWEEN 415100 AND 415199
                       OR nominal_account_number BETWEEN 424000 AND 424999
                       OR nominal_account_number BETWEEN 435500 AND 435599
                       OR nominal_account_number BETWEEN 438000 AND 438999
                       OR nominal_account_number BETWEEN 455000 AND 456999
                       OR nominal_account_number BETWEEN 487000 AND 487099
                       OR nominal_account_number BETWEEN 491000 AND 497999)
              {firma_filter}
              {umlage_kosten_filter}
            GROUP BY kst
        """)

        cursor.execute(direkte_sql, (von, bis))
        direkte_rows = cursor.fetchall()
        direkte = {row_to_dict(r)['kst']: float(row_to_dict(r)['summe'] or 0) for r in direkte_rows}

        # =========================================================================
        # INDIREKTE KOSTEN (KST 0 = Verwaltung)
        # WICHTIG: umlage_kosten_filter wird hier angewendet um Konto 498001 auszuschlieÃŸen
        #          wenn "ohne Umlage" gewÃ¤hlt ist. Sonst werden die internen Umlagen
        #          (50.000 â‚¬/Monat als HABEN gebucht) die Kosten negativ machen!
        # =========================================================================
        indirekte_sql = convert_placeholders(f"""
            SELECT SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as summe
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND ((nominal_account_number BETWEEN 400000 AND 499999
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
                   OR (nominal_account_number BETWEEN 424000 AND 424999
                       AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                   OR (nominal_account_number BETWEEN 438000 AND 438999
                       AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                   OR nominal_account_number BETWEEN 498000 AND 499999
                   OR (nominal_account_number BETWEEN 891000 AND 896999
                       AND NOT (nominal_account_number BETWEEN 893200 AND 893299)))
              {firma_filter}
              {umlage_kosten_filter}
        """)

        cursor.execute(indirekte_sql, (von, bis))
        row = cursor.fetchone()
        indirekte_gesamt = float(row_to_dict(row)['summe'] or 0) if row else 0
    
    # =========================================================================
    # UMLAGE VERTEILEN nach MA-SchlÃ¼ssel
    # =========================================================================
    umlage_verteilt = {}
    for kst in produktiv_kst:
        anteil = umlage_schluessel.get(kst, 0) / 100
        umlage_verteilt[kst] = indirekte_gesamt * anteil
    
    # KST 1+2 zusammenfassen fÃ¼r Verkauf (wird in API auf NW/GW aufgeteilt)
    # FÃ¼r TEK: 1=NW, 2=GW brauchen separate Werte
    # Aufteilung 1/2 nach Umsatz-VerhÃ¤ltnis wÃ¤re ideal, hier erstmal 50/50
    if '12' in umlage_verteilt:
        verkauf_umlage = umlage_verteilt['12']
        umlage_verteilt['1'] = verkauf_umlage * 0.5
        umlage_verteilt['2'] = verkauf_umlage * 0.5
    
    # Variable/Direkte fÃ¼r 1+2 auch aufteilen
    for d in [variable, direkte]:
        if '1' in d and '2' in d:
            pass  # Schon getrennt
        elif '1' not in d and '2' not in d:
            # Keine Daten fÃ¼r 1 oder 2
            d['1'] = 0
            d['2'] = 0
    
    return {
        'variable': variable,
        'direkte': direkte,
        'indirekte_gesamt': indirekte_gesamt,
        'umlage_verteilt': umlage_verteilt,
        'ma_verteilung': ma_verteilung,
        'umlage_schluessel': umlage_schluessel
    }


# =============================================================================
# BREAKEVEN-PROGNOSE
# =============================================================================

def berechne_breakeven_prognose_standort(monat: int, jahr: int, aktueller_db1: float,
                                          firma_filter_umsatz: str, firma_filter_kosten: str) -> dict:
    """
    Berechnet Breakeven-Prognose fÃ¼r einen spezifischen Standort.

    Unterschied zu berechne_breakeven_prognose:
    - Kosten werden nach 6. Ziffer der Kontonummer gefiltert (Standort-spezifisch)
    - Umsatz/Einsatz nach branch_number gefiltert

    Parameter:
    - firma_filter_umsatz: Filter fÃ¼r Umsatz/Einsatz (z.B. " AND branch_number = 1")
    - firma_filter_kosten: Filter fÃ¼r Kosten (z.B. " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'")
    """
    from dateutil.relativedelta import relativedelta

    von = f"{jahr}-{monat:02d}-01"
    bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"

    heute = date.today()
    vor_3_monaten = (heute - relativedelta(months=3)).isoformat()
    heute_str = heute.isoformat()

    with db_session() as conn:
        cursor = conn.cursor()

        # Kosten fÃ¼r diesen Standort (mit Filter auf 6. Ziffer der Kontonummer)
        # Nur direkte Kosten des Standorts - keine Umlagen
        cursor.execute(convert_placeholders(f"""
            SELECT
                COALESCE(SUM(CASE
                    WHEN (nominal_account_number BETWEEN 415100 AND 415199
                          OR nominal_account_number BETWEEN 435500 AND 435599
                          OR (nominal_account_number BETWEEN 455000 AND 456999 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                          OR (nominal_account_number BETWEEN 487000 AND 487099 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                          OR nominal_account_number BETWEEN 491000 AND 497899)
                    THEN CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END ELSE 0 END) / 100.0, 0) as variable,

                COALESCE(SUM(CASE
                    WHEN (nominal_account_number BETWEEN 400000 AND 489999
                          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
                          AND NOT (nominal_account_number BETWEEN 415100 AND 415199
                                   OR nominal_account_number BETWEEN 424000 AND 424999
                                   OR nominal_account_number BETWEEN 435500 AND 435599
                                   OR nominal_account_number BETWEEN 438000 AND 438999
                                   OR nominal_account_number BETWEEN 455000 AND 456999
                                   OR nominal_account_number BETWEEN 487000 AND 487099
                                   OR nominal_account_number BETWEEN 491000 AND 497999))
                    THEN CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END ELSE 0 END) / 100.0, 0) as direkte
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
            {firma_filter_kosten}
        """), (vor_3_monaten, heute_str))
        row = cursor.fetchone()
        kosten_3m = row_to_dict(row) if row else {}

        variable_3m = float(kosten_3m.get('variable') or 0)
        direkte_3m = float(kosten_3m.get('direkte') or 0)
        kosten_pro_monat = (variable_3m + direkte_3m) / 3  # Nur direkte Kosten, keine Umlagen

        # Umsatz/Einsatz fÃ¼r diesen Standort
        cursor.execute(convert_placeholders(f"""
            SELECT
                COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
              AND nominal_account_number NOT BETWEEN 498000 AND 498999
              {firma_filter_umsatz}
        """), (von, bis))
        row = cursor.fetchone()
        operativ_umsatz = float(row_to_dict(row).get('umsatz') or 0) if row else 0

        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as einsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 700000 AND 799999
              {firma_filter_umsatz}
        """), (von, bis))
        row = cursor.fetchone()
        operativ_einsatz = float(row_to_dict(row).get('einsatz') or 0) if row else 0

        operativ_db1 = operativ_umsatz - operativ_einsatz

        # Buchungstage
        cursor.execute(convert_placeholders(f"""
            SELECT COUNT(DISTINCT accounting_date) as tage
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 700000 AND 899999
              {firma_filter_umsatz}
        """), (von, bis))
        row = cursor.fetchone()
        tage_mit_daten = int(row_to_dict(row).get('tage') or 0) if row else 0

    # Werktage
    werktage = get_werktage_monat(jahr, monat)
    werktage_gesamt = werktage['gesamt']

    # Hochrechnung
    if tage_mit_daten >= 5:
        hochrechnung_db1 = (operativ_db1 / tage_mit_daten) * werktage_gesamt
    else:
        hochrechnung_db1 = aktueller_db1  # Fallback: Aktueller Wert

    # Status
    if aktueller_db1 >= kosten_pro_monat:
        status, ampel = 'positiv', 'gruen'
    elif hochrechnung_db1 >= kosten_pro_monat:
        status, ampel = 'auf_kurs', 'gelb'
    else:
        status, ampel = 'kritisch', 'rot'

    return {
        'kosten_3m_schnitt': {
            'variable': round(variable_3m / 3, 2),
            'direkte': round(direkte_3m / 3, 2),
            'gesamt': round(kosten_pro_monat, 2)
        },
        'breakeven_schwelle': round(kosten_pro_monat, 2),
        'aktueller_db1': round(aktueller_db1, 2),
        'operativer_db1': round(operativ_db1, 2),
        'tage_mit_daten': tage_mit_daten,
        'hochrechnung_db1': round(hochrechnung_db1, 2),
        'hochrechnung_be': round(hochrechnung_db1 - kosten_pro_monat, 2),
        'gap': round(aktueller_db1 - kosten_pro_monat, 2),
        'status': status,
        'ampel': ampel,
    }


def berechne_breakeven_prognose(monat: int, jahr: int, aktueller_db1: float,
                                 firma_filter_umsatz: str, firma_filter_kosten: str = None,
                                 anteilige_kosten: bool = True) -> dict:
    """
    Berechnet Breakeven-Prognose
    TAG 136: PostgreSQL-kompatibel - nutzt intern db_session()
    TAG 136+: Anteilige Kostenverteilung nach Umsatz-Anteil

    Parameter:
    - firma_filter_umsatz: Filter fÃ¼r Umsatz/Einsatz-Konten (7/8xxxxx) - nutzt branch_number
    - firma_filter_kosten: Filter fÃ¼r Kosten-Konten (4xxxxx) - nutzt letzte Ziffer
    - anteilige_kosten: True = Kosten anteilig nach Umsatz verteilen (fÃ¼r Firmen ohne eigene Kostenkonten)

    Logik:
    - < 5 Buchungstage: Gleitender Durchschnitt (Ã˜ DB1 der letzten 3 Monate)
    - >= 5 Buchungstage: Normale Hochrechnung basierend auf aktuellem DB1/Tag
    """
    from dateutil.relativedelta import relativedelta

    # Fallback: Wenn kein separater Kosten-Filter, verwende Umsatz-Filter
    if firma_filter_kosten is None:
        firma_filter_kosten = firma_filter_umsatz

    von = f"{jahr}-{monat:02d}-01"
    bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"

    # TAG 136: Python-basierte Datumsberechnung statt SQLite date()
    heute = date.today()
    vor_3_monaten = (heute - relativedelta(months=3)).isoformat()
    heute_str = heute.isoformat()

    # =========================================================================
    # ANTEILIGE KOSTENVERTEILUNG (TAG136+)
    # Berechne Umsatz-Anteil dieser Firma vs. Gesamt fÃ¼r faire Kostenverteilung
    # =========================================================================
    umsatz_anteil = 1.0  # Default: 100% der Kosten
    umsatz_firma = 0
    umsatz_gesamt = 0

    if anteilige_kosten:
        with db_session() as conn:
            cursor = conn.cursor()

            # Umsatz dieser Firma (3 Monate)
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number BETWEEN 800000 AND 889999
                  {firma_filter_umsatz}
            """), (vor_3_monaten, heute_str))
            row = cursor.fetchone()
            umsatz_firma = float(row_to_dict(row).get('umsatz') or 0) if row else 0

            # Gesamtumsatz aller Firmen (3 Monate)
            cursor.execute(convert_placeholders("""
                SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number BETWEEN 800000 AND 889999
            """), (vor_3_monaten, heute_str))
            row = cursor.fetchone()
            umsatz_gesamt = float(row_to_dict(row).get('umsatz') or 0) if row else 0

            if umsatz_gesamt > 0:
                umsatz_anteil = umsatz_firma / umsatz_gesamt

    with db_session() as conn:
        cursor = conn.cursor()

        # 3-Monats-Durchschnitt Kosten (GESAMT, wird dann anteilig verteilt)
        # Wenn anteilige_kosten=True: KEINE firma_filter_kosten, sondern Gesamtkosten!
        kosten_filter = "" if anteilige_kosten else firma_filter_kosten
        cursor.execute(convert_placeholders(f"""
            SELECT
                COALESCE(SUM(CASE
                    WHEN (nominal_account_number BETWEEN 415100 AND 415199
                          OR nominal_account_number BETWEEN 435500 AND 435599
                          OR (nominal_account_number BETWEEN 455000 AND 456999 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                          OR (nominal_account_number BETWEEN 487000 AND 487099 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                          OR nominal_account_number BETWEEN 491000 AND 497899)
                    THEN CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END ELSE 0 END) / 100.0, 0) as variable,

                COALESCE(SUM(CASE
                    WHEN (nominal_account_number BETWEEN 400000 AND 489999
                          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
                          AND NOT (nominal_account_number BETWEEN 415100 AND 415199
                                   OR nominal_account_number BETWEEN 424000 AND 424999
                                   OR nominal_account_number BETWEEN 435500 AND 435599
                                   OR nominal_account_number BETWEEN 438000 AND 438999
                                   OR nominal_account_number BETWEEN 455000 AND 456999
                                   OR nominal_account_number BETWEEN 487000 AND 487099
                                   OR nominal_account_number BETWEEN 491000 AND 497999))
                    THEN CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END ELSE 0 END) / 100.0, 0) as direkte,

                COALESCE(SUM(CASE
                    WHEN ((nominal_account_number BETWEEN 400000 AND 499999 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0' AND nominal_account_number != 498001)
                          OR (nominal_account_number BETWEEN 424000 AND 424999 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                          OR (nominal_account_number BETWEEN 438000 AND 438999 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                          OR (nominal_account_number BETWEEN 891000 AND 896999 AND NOT (nominal_account_number BETWEEN 893200 AND 893299)))
                    THEN CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END ELSE 0 END) / 100.0, 0) as indirekte
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
            {kosten_filter}
        """), (vor_3_monaten, heute_str))
        row = cursor.fetchone()
        kosten_3m = row_to_dict(row) if row else {}

        variable_3m_gesamt = float(kosten_3m.get('variable') or 0)
        direkte_3m_gesamt = float(kosten_3m.get('direkte') or 0)
        indirekte_3m_gesamt = float(kosten_3m.get('indirekte') or 0)
        kosten_3m_gesamt = variable_3m_gesamt + direkte_3m_gesamt + indirekte_3m_gesamt

        # Anteilige Verteilung nach Umsatz-Anteil
        variable_3m = variable_3m_gesamt * umsatz_anteil
        direkte_3m = direkte_3m_gesamt * umsatz_anteil
        indirekte_3m = indirekte_3m_gesamt * umsatz_anteil
        kosten_pro_monat = (variable_3m + direkte_3m + indirekte_3m) / 3

        # Operativer DB1 (ohne Umlagen) - verwendet firma_filter_umsatz
        cursor.execute(convert_placeholders(f"""
            SELECT
                COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
              AND nominal_account_number NOT BETWEEN 498000 AND 498999
              {firma_filter_umsatz}
        """), (von, bis))
        row = cursor.fetchone()
        operativ_umsatz = float(row_to_dict(row).get('umsatz') or 0) if row else 0

        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as einsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 700000 AND 799999
              {firma_filter_umsatz}
        """), (von, bis))
        row = cursor.fetchone()
        operativ_einsatz = float(row_to_dict(row).get('einsatz') or 0) if row else 0

        operativ_db1 = operativ_umsatz - operativ_einsatz

        # Hochrechnung - Tage mit Daten (Umsatz-basiert)
        cursor.execute(convert_placeholders(f"""
            SELECT COUNT(DISTINCT accounting_date) as tage
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 700000 AND 899999
              {firma_filter_umsatz}
        """), (von, bis))
        row = cursor.fetchone()
        tage_mit_daten = int(row_to_dict(row).get('tage') or 0) if row else 0

    # Werktage statt Kalendertage (TAG121)
    werktage = get_werktage_monat(jahr, monat)
    werktage_gesamt = werktage['gesamt']
    werktage_vergangen = werktage['vergangen']

    # Alte Variablen fÃ¼r KompatibilitÃ¤t
    tage_im_monat = werktage_gesamt  # Jetzt Werktage statt 31

    # =========================================================================
    # PROGNOSE-METHODE: Gleitender Durchschnitt vs. Hochrechnung
    # =========================================================================
    hochrechnung_db1 = None
    prognose_methode = None
    db1_3m_schnitt = None

    if tage_mit_daten < 5:
        # GLEITENDER DURCHSCHNITT: Ã˜ DB1 der letzten 3 abgeschlossenen Monate
        # TAG 136: PostgreSQL-kompatibel - TO_CHAR statt strftime
        vor_3m_start = (datetime.strptime(von, '%Y-%m-%d') - relativedelta(months=3)).strftime('%Y-%m-%d')

        # PostgreSQL: TO_CHAR, SQLite: strftime
        if get_db_type() == 'postgresql':
            monat_expr = "TO_CHAR(accounting_date, 'YYYY-MM')"
        else:
            monat_expr = "strftime('%Y-%m', accounting_date)"

        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_placeholders(f"""
                SELECT
                    {monat_expr} as monat,
                    SUM(CASE
                        WHEN nominal_account_number BETWEEN 800000 AND 889999
                             OR nominal_account_number BETWEEN 893200 AND 893299
                        THEN CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END
                        ELSE 0
                    END) / 100.0 as umsatz,
                    SUM(CASE
                        WHEN nominal_account_number BETWEEN 700000 AND 799999
                        THEN CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END
                        ELSE 0
                    END) / 100.0 as einsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= ?
                  AND accounting_date < ?
                  {firma_filter_umsatz}
                GROUP BY {monat_expr}
                ORDER BY monat DESC
                LIMIT 3
            """), (vor_3m_start, von))
            db1_3m_rows = [row_to_dict(r) for r in cursor.fetchall()]

        if db1_3m_rows and len(db1_3m_rows) >= 2:
            # Berechne DB1 pro Monat
            db1_werte = [float(row.get('umsatz') or 0) - float(row.get('einsatz') or 0) for row in db1_3m_rows]
            db1_3m_schnitt = sum(db1_werte) / len(db1_werte)
            hochrechnung_db1 = db1_3m_schnitt
            prognose_methode = 'gleitend_3m'
        else:
            # Fallback: Keine ausreichenden Daten
            prognose_methode = 'keine_daten'
    else:
        # NORMALE HOCHRECHNUNG: Basierend auf aktuellem DB1/Tag
        hochrechnung_db1 = (operativ_db1 / tage_mit_daten) * tage_im_monat
        prognose_methode = 'hochrechnung'

    # Status bestimmen
    if aktueller_db1 >= kosten_pro_monat:
        status, ampel = 'positiv', 'gruen'
    elif hochrechnung_db1 and hochrechnung_db1 >= kosten_pro_monat:
        status, ampel = 'auf_kurs', 'gelb'
    else:
        status, ampel = 'kritisch', 'rot'

    # Berechne Soll-DB1 bis heute basierend auf Werktagen
    db1_pro_werktag = kosten_pro_monat / werktage_gesamt if werktage_gesamt > 0 else 0
    db1_soll_bis_heute = db1_pro_werktag * werktage_vergangen

    # =========================================================================
    # BREAKEVEN PRO BEREICH (TAG132)
    # Umlage-SchlÃ¼ssel: Anteil an indirekten Kosten pro Abteilung
    # Basierend auf Hybrid aus Umsatz- und DB1-Anteil
    # =========================================================================
    UMLAGE_SCHLUESSEL = {
        '1-NW': 0.40,     # 40% - Hoher Umsatz, Personalbedarf
        '2-GW': 0.20,     # 20% - Mittlerer Umsatz
        '3-Teile': 0.25,  # 25% - Lager, Logistik
        '4-Lohn': 0.15,   # 15% - Werkstatt relativ autark
        '5-Sonst': 0.0
    }

    breakeven_bereiche = {}
    for bereich, anteil in UMLAGE_SCHLUESSEL.items():
        breakeven_bereiche[bereich] = round(kosten_pro_monat * anteil, 2)

    return {
        'kosten_3m_schnitt': {
            'variable': round(variable_3m / 3, 2),
            'direkte': round(direkte_3m / 3, 2),
            'indirekte': round(indirekte_3m / 3, 2),
            'gesamt': round(kosten_pro_monat, 2)
        },
        'breakeven_schwelle': round(kosten_pro_monat, 2),  # Ã˜ 3 Monate
        'aktueller_db1': round(aktueller_db1, 2),
        'operativer_db1': round(operativ_db1, 2),
        'tage_mit_daten': tage_mit_daten,
        'tage_im_monat': tage_im_monat,  # Jetzt Werktage!
        'prognose_methode': prognose_methode,  # 'gleitend_3m', 'hochrechnung', 'keine_daten'
        'db1_3m_schnitt': round(db1_3m_schnitt, 2) if db1_3m_schnitt else None,
        'hochrechnung_db1': round(hochrechnung_db1, 2) if hochrechnung_db1 else None,
        'hochrechnung_be': round(hochrechnung_db1 - kosten_pro_monat, 2) if hochrechnung_db1 else None,
        'gap': round(aktueller_db1 - kosten_pro_monat, 2),
        'gap_prozent': round((aktueller_db1 - kosten_pro_monat) / kosten_pro_monat * 100, 1) if kosten_pro_monat > 0 else 0,
        'status': status,
        'ampel': ampel,
        'hinweis_umlage': tage_mit_daten < 5,  # True = gleitender Durchschnitt aktiv
        # Werktage-Infos (TAG121)
        'werktage': {
            'gesamt': werktage_gesamt,
            'vergangen': werktage_vergangen,
            'verbleibend': werktage['verbleibend'],
            'fortschritt_prozent': werktage['fortschritt_prozent'],
        },
        'db1_soll_bis_heute': round(db1_soll_bis_heute, 2),
        'db1_pro_werktag': round(db1_pro_werktag, 2),
        # Breakeven pro Bereich (TAG132)
        'breakeven_bereiche': breakeven_bereiche,
        'umlage_schluessel': {k: round(v * 100, 0) for k, v in UMLAGE_SCHLUESSEL.items()},
        # Anteilige Kostenverteilung (TAG136+)
        'kostenverteilung': {
            'anteilig': anteilige_kosten,
            'umsatz_anteil': round(umsatz_anteil * 100, 1),  # z.B. 67.3%
            'umsatz_firma_3m': round(umsatz_firma, 2),
            'umsatz_gesamt_3m': round(umsatz_gesamt, 2),
            'kosten_gesamt_3m': round(kosten_3m_gesamt / 3, 2),  # Ã˜ pro Monat
        },
    }


# =============================================================================
# WEITERE API-ENDPOINTS
# =============================================================================

@controlling_bp.route('/api/overview', methods=['GET'])
@login_required
def api_overview():
    """TAG 136: PostgreSQL-kompatibel via db_session()"""
    try:
        include_gesellschafter = request.args.get('include_gesellschafter', 'false').lower() == 'true'

        # TAG 136: PostgreSQL verwendet BOOLEAN, SQLite verwendet 1/0
        aktiv_check = "aktiv = true" if get_db_type() == 'postgresql' else "aktiv = 1"
        ist_operativ_check = "ist_operativ = true" if get_db_type() == 'postgresql' else "ist_operativ = 1"

        # TAG 136: Datumsfunktion fÃ¼r PostgreSQL/SQLite
        if get_db_type() == 'postgresql':
            date_12_months_ago = "NOW() - INTERVAL '12 months'"
        else:
            date_12_months_ago = "date('now', '-12 months')"

        with db_session() as conn:
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT COALESCE(SUM(saldo), 0) FROM v_aktuelle_kontostaende
                WHERE anzeige_gruppe = 'autohaus' AND {ist_operativ_check}
            """)
            row = cursor.fetchone()
            operative_liq = float(row[0] if isinstance(row, (list, tuple)) else row['coalesce']) or 0

            cursor.execute(f"""
                SELECT COALESCE(SUM(ABS(kreditlinie)), 0) FROM v_aktuelle_kontostaende
                WHERE anzeige_gruppe = 'autohaus' AND {ist_operativ_check} AND kreditlinie IS NOT NULL
            """)
            row = cursor.fetchone()
            kreditlinien = float(row[0] if isinstance(row, (list, tuple)) else row['coalesce']) or 0

            cursor.execute(f"""
                SELECT COALESCE(SUM(original_betrag - aktueller_saldo), 0)
                FROM fahrzeugfinanzierungen WHERE {aktiv_check}
            """)
            row = cursor.fetchone()
            fahrzeug_linien = float(row[0] if isinstance(row, (list, tuple)) else row['coalesce']) or 0

            verfuegbare_liq = operative_liq + kreditlinien + fahrzeug_linien

            cursor.execute(f"""
                SELECT COALESCE(SUM(amount), 0) FROM fibu_buchungen
                WHERE buchungstyp = 'zinsen' AND debit_credit = 'S' AND accounting_date >= {date_12_months_ago}
            """)
            row = cursor.fetchone()
            zinsen = float(row[0] if isinstance(row, (list, tuple)) else row['coalesce']) or 0

            cursor.execute(f"""
                SELECT COUNT(*) as anzahl, COALESCE(SUM(aktueller_saldo), 0) as summe
                FROM fahrzeugfinanzierungen WHERE {aktiv_check}
            """)
            einkauf_row = cursor.fetchone()
            einkauf = row_to_dict(einkauf_row) if einkauf_row else {'anzahl': 0, 'summe': 0}

            cursor.execute(f"""
                SELECT COALESCE(SUM(amount), 0) FROM fibu_buchungen
                WHERE nominal_account BETWEEN 800000 AND 899999 AND debit_credit = 'H'
                AND accounting_date >= {date_12_months_ago}
            """)
            row = cursor.fetchone()
            umsatz = float(row[0] if isinstance(row, (list, tuple)) else row['coalesce']) or 0

            gesellschafter_saldo = None
            if include_gesellschafter:
                cursor.execute("""
                    SELECT COALESCE(SUM(saldo), 0) FROM v_aktuelle_kontostaende WHERE anzeige_gruppe = 'gesellschafter'
                """)
                row = cursor.fetchone()
                gesellschafter_saldo = float(row[0] if isinstance(row, (list, tuple)) else row['coalesce'])
        
        # TAG 136: einkauf ist jetzt ein Dict
        return jsonify({
            'liquiditaet': {
                'operativ': float(operative_liq),
                'kreditlinien': float(kreditlinien),
                'verfuegbar': float(verfuegbare_liq),
                'nutzungsgrad': round((operative_liq / verfuegbare_liq * 100), 1) if verfuegbare_liq > 0 else 0
            },
            'zinsen': float(zinsen),
            'einkauf': {
                'anzahl_fahrzeuge': int(einkauf.get('anzahl', 0) or 0),
                'finanzierungssumme': float(einkauf.get('summe', 0) or 0)
            },
            'umsatz': float(umsatz),
            'gesellschafter': {'saldo': float(gesellschafter_saldo)} if gesellschafter_saldo is not None else None,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@controlling_bp.route('/api/trends')
@login_required
def api_trends():
    return jsonify({"status": "coming_soon"})
