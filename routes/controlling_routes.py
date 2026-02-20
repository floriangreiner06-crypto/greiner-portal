from flask import Blueprint, render_template, jsonify, request, abort
from flask_login import current_user
from decorators.auth_decorators import login_required
import re
from datetime import datetime, date, timedelta
import calendar
import psycopg2.extras

# TAG 136: PostgreSQL-Migration - Nutze db_utils für Portal-DB
from api.db_utils import db_session, row_to_dict, rows_to_list, locosoft_session, get_guv_filter
from api.db_connection import convert_placeholders, sql_placeholder, get_db_type, get_db, get_db

# TAG 146: Wiederverwendbares TEK-Datenmodul (100% Konsistenz mit Reports!)
# SSOT: Breakeven/Prognose in api.controlling_data (eine Logik für Portal + PDF)
from api.controlling_data import get_tek_data, berechne_breakeven_prognose, berechne_breakeven_prognose_standort
from utils.werktage import get_werktage, get_werktage_monat

# get_db() wird jetzt direkt aus api.db_connection importiert (SSOT)



def get_locosoft_db():
    """PostgreSQL-Verbindung zu externer Locosoft DB (10.80.80.8)"""
    return locosoft_session()


# =============================================================================
# MODELL-NORMALISIERUNG für Locosoft
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

    # Lowercase für Matching
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

    # Lowercase für Matching
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

    # Fallback: Ersten Buchstaben groß, Rest klein
    return modell.strip()


def get_stueckzahlen_locosoft(von: str, bis: str, bereich: str = '1-NW', firma: str = '0', standort: str = '0') -> dict:
    """
    Holt Fahrzeug-Stückzahlen aus Locosoft dealer_vehicles.
    
    TAG167 FIX: Stückzahlen aus dealer_vehicles (tatsächliche Auslieferungen),
    NICHT aus journal_accountings (nur bereits gebuchte Verkäufe)!
    
    Grund: dealer_vehicles zeigt alle fakturierten Auslieferungen sofort,
    während journal_accountings nur bereits gebuchte Verkäufe enthält.
    Die FIBU-Buchungen kommen oft verzögert (z.B. bei Monatsabschluss).

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

            # TAG176: Nur fakturierte Fahrzeuge bis HEUTE zählen (keine zukünftigen Fakturierungen!)
            # Primäres Datum: COALESCE(out_invoice_date, out_sales_contract_date)
            heute_str = date.today().isoformat()
            bis_effektiv = min(bis, heute_str)
            # Explizit: Rechnungs-/Vertragsdatum darf nicht in der Zukunft liegen (Absicherung)
            cur.execute(f"""
                SELECT
                    COALESCE(m.description, 'Unbekannt') as modell_raw,
                    COUNT(*) as stueck,
                    SUM(dv.out_sale_price) as gesamt_vk_raw,
                    AVG(dv.out_sale_price) as avg_vk_raw
                FROM dealer_vehicles dv
                JOIN vehicles v ON v.internal_number = dv.vehicle_number
                LEFT JOIN models m ON v.model_code = m.model_code AND v.make_number = m.make_number
                WHERE dv.dealer_vehicle_type = %s
                  AND dv.out_sale_price > 0
                  AND COALESCE(dv.out_invoice_date, dv.out_sales_contract_date) >= %s
                  AND COALESCE(dv.out_invoice_date, dv.out_sales_contract_date) <= %s
                  AND COALESCE(dv.out_invoice_date, dv.out_sales_contract_date)::date <= CURRENT_DATE
                  {standort_filter}
                GROUP BY m.description
                ORDER BY stueck DESC
            """, (fzg_typ, von, bis_effektiv))

            rows = cur.fetchall()
            cur.close()

        # Nach Basis-Modell gruppieren (außerhalb des with-Blocks)
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
# KONSTANTEN: MA-VERTEILUNG FÜR UMLAGE
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
# ERLÖSE bei Stellantis (Autohaus Greiner bekommt):
#   817051 = Kostenumlage NW        ~12.500 €/Monat
#   827051 = Kostenumlage GW        ~12.500 €/Monat  
#   837051 = Kostenumlage Werkstatt ~12.500 €/Monat
#   847051 = Kostenumlage Teile     ~12.500 €/Monat
#   SUMME:                          ~50.000 €/Monat
#
# KOSTEN bei Hyundai (Auto Greiner zahlt) - als HABEN gebucht!
#   498001 = Kostenumlage Haupt     ~50.000 €/Monat
#   415001 = Kostenumlage Personal  ~ 5.000 €/Monat (+ echte Personalkosten SOLL)
#   440001 = Kostenumlage Miete     ~ 2.500 €/Monat (+ echte Mietkosten SOLL)
#   461001 = Kostenumlage Versich.  ~   500 €/Monat (+ echte Versicherungen SOLL)
#   462001 = Kostenumlage Beiträge  ~   500 €/Monat (+ echte Beiträge SOLL)
#   SUMME:                          ~58.500 €/Monat
#
# WICHTIG: Die Konten 415001, 440001, 461001, 462001 haben DOPPELTE Verwendung:
#   - Echte Kosten (SOLL-Buchungen): Miete Fischer, Lohn/Gehalt, etc.
#   - Interne Umlage (HABEN-Buchungen): "Kostenumlage AH Greiner"
# Daher filtern wir nach BUCHUNGSTEXT, nicht nur nach Kontonummer!
#
UMLAGE_ERLOESE_KONTEN = [817051, 827051, 837051, 847051]
UMLAGE_KOSTEN_KONTEN = [498001]  # Haupt-Umlage-Konto (nur HABEN-Buchungen)

# Buchungstexte die als Umlage identifiziert werden (für HABEN-Buchungen auf Kostenkonten)
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
                    WHEN department_name IN ('Teile', 'Lager', 'Lager & Teile', 'Teile und Zubehör') THEN '6'
                    WHEN department_name IN ('Verwaltung', 'Buchhaltung', 'Geschäftsleitung', 'Geschäftsführung', 'CRM', 'Marketing', 'Call-Center', 'Kundenzentrale') THEN '0'
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

@controlling_bp.route('/finanzreporting')
@login_required
def finanzreporting():
    """Finanzreporting Cube Dashboard"""
    return render_template('controlling/finanzreporting_cube.html')

@controlling_bp.route('/kontenmapping')
@login_required
def kontenmapping():
    """Kontenmapping-Export und -Bearbeitung für Buchhaltung"""
    return render_template('controlling/kontenmapping.html',
                         page_title='Kontenmapping',
                         active_page='controlling')

@controlling_bp.route('/bwa')
@login_required
def bwa():
    """BWA Dashboard - Hauptversion (TAG144: v2 ist jetzt Standard)"""
    # TAG 177: Standort-Filter aus URL lesen
    from utils.standort_filter_helpers import parse_standort_params
    standort, konsolidiert = parse_standort_params(request)
    
    # Firma automatisch aus Standort ableiten (wenn nicht explizit gesetzt)
    firma = request.args.get('firma')
    if not firma and standort:
        # Standort 1 (Deggendorf Opel) oder 3 (Landau Opel) → Firma 1 (Stellantis)
        # Standort 2 (Deggendorf Hyundai) → Firma 2 (Hyundai)
        if standort in [1, 3]:
            firma = '1'  # Stellantis
        elif standort == 2:
            firma = '2'  # Hyundai
        else:
            firma = '0'  # Alle
    elif not firma:
        firma = '0'  # Alle
    
    return render_template('controlling/bwa_v2.html',
                         page_title='BWA',
                         active_page='controlling',
                         standort=standort,
                         konsolidiert=konsolidiert,
                         firma=firma)


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
    # TAG 177: Standort-Filter aus URL lesen
    from utils.standort_filter_helpers import parse_standort_params
    standort, konsolidiert = parse_standort_params(request)
    
    # Firma automatisch aus Standort ableiten (wenn nicht explizit gesetzt)
    firma = request.args.get('firma')
    if not firma and standort:
        # Standort 1 (Deggendorf Opel) oder 3 (Landau) → Firma 1 (Stellantis)
        # Standort 2 (Hyundai DEG) → Firma 2 (Hyundai)
        if standort in [1, 3]:
            firma = '1'  # Stellantis
        elif standort == 2:
            firma = '2'  # Hyundai
        else:
            firma = '0'  # Alle
    elif not firma:
        firma = '0'  # Alle
    
    return render_template('controlling/tek_dashboard_v2.html',
                         page_title='Tägliche Erfolgskontrolle',
                         active_page='controlling',
                         standort=standort,
                         konsolidiert=konsolidiert,
                         firma=firma)


@controlling_bp.route('/tek/archiv')
@login_required
def tek_dashboard_archiv():
    """TEK Archiv - Alte ausführliche Version (TAG140: v1 ins Archiv)"""
    return render_template('controlling/tek_dashboard.html',
                         page_title='TEK Archiv (v1)',
                         active_page='controlling')


@controlling_bp.route('/unternehmensplan')
@controlling_bp.route('/rendite')
@login_required
def unternehmensplan_dashboard():
    """Unternehmensplan - 1% Rendite Dashboard (TAG157)

    Gesamtunternehmensplanung über alle Kostenstellen:
    - IST vs PLAN über alle Bereiche (NW, GW, Teile, Werkstatt, Sonstige)
    - Gap-Analyse zum 1%-Renditeziel
    - Prognose bis Geschäftsjahresende
    - Handlungsempfehlungen pro Bereich
    """
    # TAG 177: Standort-Filter aus URL lesen
    from utils.standort_filter_helpers import parse_standort_params
    standort, konsolidiert = parse_standort_params(request)
    
    # Firma automatisch aus Standort ableiten (wenn nicht explizit gesetzt)
    firma = request.args.get('firma')
    if not firma and standort:
        # Standort 1 (Deggendorf Opel) oder 3 (Landau Opel) → Firma 1 (Stellantis)
        # Standort 2 (Deggendorf Hyundai) → Firma 2 (Hyundai)
        if standort in [1, 3]:
            firma = '1'  # Stellantis
        elif standort == 2:
            firma = '2'  # Hyundai
        else:
            firma = '0'  # Alle
    elif not firma:
        firma = '0'  # Alle
    
    return render_template('controlling/unternehmensplan.html',
                         page_title='Unternehmensplan - 1% Rendite',
                         active_page='controlling',
                         standort=standort,
                         konsolidiert=konsolidiert,
                         firma=firma)


@controlling_bp.route('/kundenzentrale')
@login_required
def kundenzentrale_dashboard():
    """Kundenzentrale Tagesziel Dashboard (TAG 164)
    
    Tägliches Fakturierungsziel für Kundenzentrale:
    - Heute fakturiert vs. Tagesziel
    - Filterbar nach Standorten (Deggendorf, Landau)
    - Aufschlüsselung nach Bereichen
    """
    return render_template('controlling/kundenzentrale.html',
                         page_title='Kundenzentrale - Tagesziel',
                         active_page='controlling')


@controlling_bp.route('/kst-ziele')
@controlling_bp.route('/ziele')
@login_required
def kst_ziele_dashboard():
    """KST-Ziele Tagesstatus Dashboard (TAG161)

    Kostenstellen-Zielplanung mit Tagesstatus:
    - IST vs SOLL pro Bereich mit Hochrechnung
    - Daumen hoch/runter Status
    - Handlungsempfehlungen
    """
    # TAG 177: Standort-Filter aus URL lesen
    from utils.standort_filter_helpers import parse_standort_params
    standort, konsolidiert = parse_standort_params(request)
    
    return render_template('controlling/kst_ziele.html',
                         page_title='KST-Ziele Tagesstatus',
                         active_page='controlling',
                         standort=standort,
                         konsolidiert=konsolidiert)


@controlling_bp.route('/opos')
@login_required
def opos_dashboard():
    """Offene Posten (OPOS) – Liste offener Debitorenposten, gruppierbar nach Verkäufer."""
    if not current_user.can_access_feature('opos'):
        abort(403)
    return render_template('controlling/opos.html',
                         page_title='Offene Posten (OPOS)',
                         active_page='controlling')


# =============================================================================
# HELPER: Umsatz/Einsatz pro Bereich für beliebigen Zeitraum
# =============================================================================

def get_bereich_daten(von: str, bis: str, firma_filter_umsatz: str, umlage_erloese_filter: str = '', firma_filter_einsatz: str = None) -> dict:
    """
    Holt Umsatz und Einsatz pro Bereich für einen Zeitraum.
    TAG 136: PostgreSQL-kompatibel
    TAG 157: firma_filter_einsatz für korrekte Standort-Zuordnung (Konto-Endziffer)
    Abgleich mit get_tek_data: G&V-Filter, Clean Park (847301/747301) aus 4-Lohn ausgenommen.
    Returns: {'1-NW': {'umsatz': X, 'einsatz': Y, 'db1': Z}, ...}
    """
    # TAG157: Wenn kein separater Einsatz-Filter, nutze Umsatz-Filter (Abwärtskompatibilität)
    if firma_filter_einsatz is None:
        firma_filter_einsatz = firma_filter_umsatz
    guv_filter = get_guv_filter()
    with db_session() as conn:
        cursor = conn.cursor()

        # UMSATZ (wie get_tek_data: G&V-Filter, Clean Park 847301 nicht in 4-Lohn)
        cursor.execute(convert_placeholders(f"""
            SELECT
                CASE
                    WHEN nominal_account_number BETWEEN 810000 AND 819999 THEN '1-NW'
                    WHEN nominal_account_number BETWEEN 820000 AND 829999 THEN '2-GW'
                    WHEN nominal_account_number BETWEEN 830000 AND 839999 THEN '3-Teile'
                    WHEN nominal_account_number BETWEEN 840000 AND 849999 AND nominal_account_number != 847301 THEN '4-Lohn'
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
              {guv_filter}
            GROUP BY bereich
        """), (von, bis))
        umsatz_rows = [row_to_dict(r) for r in cursor.fetchall()]

        # EINSATZ (TAG157; G&V-Filter; Clean Park 747301 nicht in 4-Lohn)
        cursor.execute(convert_placeholders(f"""
            SELECT
                CASE
                    WHEN nominal_account_number BETWEEN 710000 AND 719999 THEN '1-NW'
                    WHEN nominal_account_number BETWEEN 720000 AND 729999 THEN '2-GW'
                    WHEN nominal_account_number BETWEEN 730000 AND 739999 THEN '3-Teile'
                    WHEN nominal_account_number BETWEEN 740000 AND 749999 AND nominal_account_number != 747301 THEN '4-Lohn'
                    WHEN nominal_account_number BETWEEN 760000 AND 769999 THEN '5-Sonst'
                    ELSE '9-Andere'
                END as bereich,
                SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as einsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 700000 AND 799999
              {firma_filter_einsatz}
              {guv_filter}
            GROUP BY bereich
        """), (von, bis))
        einsatz_rows = [row_to_dict(r) for r in cursor.fetchall()]

    result = {}
    for bkey in ['1-NW', '2-GW', '3-Teile', '4-Lohn', '5-Sonst']:
        umsatz = next((float(r['umsatz'] or 0) for r in umsatz_rows if r['bereich'] == bkey), 0)
        einsatz = next((float(r['einsatz'] or 0) for r in einsatz_rows if r['bereich'] == bkey), 0)
        db1 = umsatz - einsatz
        marge = (db1 / umsatz * 100) if umsatz > 0 else 0
        result[bkey] = {
            'umsatz': round(umsatz, 2),
            'einsatz': round(einsatz, 2),
            'db1': round(db1, 2),
            'marge': round(marge, 1)
        }

    return result


def get_werkstatt_produktivitaet(von: str, bis: str, betrieb: str = '0') -> dict:
    """
    Holt Werkstatt-Produktivität (EW) für kalkulatorischen Einsatz.

    NUTZT ZENTRALE BERECHNUNG aus api/werkstatt_api.py (werkstatt_leistung_daily)
    = Single Source of Truth für Werkstatt-KPIs
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
            # Produktivität = Stempelzeit / Anwesenheit * 100
            # Leistungsgrad = Vorgabezeit_AW * 6 / Stempelzeit * 100 (6 Min pro AW)
            # TAG 136: PostgreSQL gibt decimal.Decimal zurück, muss zu float gecastet werden
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
        print(f"Werkstatt-Produktivität Fehler: {e}")
        import traceback
        traceback.print_exc()
        return {'produktivitaet': 75.0, 'leistungsgrad': 85.0}


# =============================================================================
# TEK API - Tägliche Erfolgskontrolle
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
    - Betrifft: 817051, 827051, 837051, 847051 (Erlöse) und 498001 (Kosten)
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

        # Für Breakeven/Prognose: "3 Monate zurück" (wird in berechne_breakeven_prognose* referenziert)
        from dateutil.relativedelta import relativedelta
        _heute = date.today()
        drei_monate_vorher = (_heute - relativedelta(months=3)).replace(day=1).strftime('%Y-%m-%d')

        # TAG 136: PostgreSQL-kompatibel - Placeholder-Funktion
        ph = sql_placeholder()  # Returns ? für SQLite, %s für PostgreSQL
        
        # Filter bauen
        # WICHTIG (TAG157 FIX): Locosoft verwendet unterschiedliche Standort-Zuordnungen:
        #          - Umsatz (8xxxxx): branch_number (1=DEG, 3=LAN) oder subsidiary (2=HYU)
        #          - Einsatz (7xxxxx): Konto-Endziffer (6. Stelle: 1=DEG, 2=LAN) oder subsidiary (2=HYU)
        #          - Kosten (4xxxxx): Konto-Endziffer (6. Stelle: 1=DEG, 2=LAN) oder subsidiary (2=HYU)

        firma_filter = ""
        firma_filter_umsatz = ""   # Für Umsatz: branch_number
        firma_filter_einsatz = ""  # Für Einsatz: Konto-Endziffer! (TAG157) - IMMER initialisieren!
        firma_filter_kosten = ""   # Für Kosten: Konto-Endziffer
        standort_name = "Alle"
        standort_code = standort  # Für MA-Verteilung

        # TAG167: firma_filter_einsatz IMMER initialisieren (auch bei firma='0')
        # Fallback für get_bereich_daten() falls nicht gesetzt
        if firma == '1':
            # Stellantis (Autohaus Greiner)
            firma_filter = "AND subsidiary_to_company_ref = 1"
            firma_filter_umsatz = "AND subsidiary_to_company_ref = 1"
            firma_filter_einsatz = "AND subsidiary_to_company_ref = 1"
            firma_filter_kosten = "AND subsidiary_to_company_ref = 1"
            standort_name = "Stellantis (DEG+LAN)"
            if standort == '1':
                # Deggendorf: branch_number=1 für Umsatz, Konto-Endziffer=1 für Einsatz/Kosten
                firma_filter_umsatz += " AND branch_number = 1"
                firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
                firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
                standort_name = "Deggendorf"
                standort_code = '1'
            elif standort == '2':  # Landau (früher '3' für branch, jetzt '2' für Konto-Endung)
                # Landau: branch_number=3 für Umsatz, Konto-Endziffer=2 für Einsatz/Kosten
                firma_filter_umsatz += " AND branch_number = 3"
                firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
                firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
                standort_name = "Landau"
                standort_code = '3'  # Für MA-Verteilung in employees (location='Landau')
        elif firma == '2':
            # Hyundai (Auto Greiner) - separate Firma
            firma_filter = "AND subsidiary_to_company_ref = 2"
            firma_filter_umsatz = "AND subsidiary_to_company_ref = 2"
            firma_filter_einsatz = "AND subsidiary_to_company_ref = 2"
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
            # Umlage-Erlöse aus Umsatz ausschließen (die 4 Umlage-Konten)
            umlage_konten_str = ','.join(map(str, UMLAGE_ERLOESE_KONTEN))
            umlage_erloese_filter = f"AND nominal_account_number NOT IN ({umlage_konten_str})"

            # Umlage-Kosten ausschließen: OPTION C = Buchungstext-basiert + KST 0
            # Filtert nur HABEN-Buchungen mit "Kostenumlage" im Text auf KST 0 (Verwaltung)
            # Dies schließt 498001 (50k), 415001, 440001, 461001, 462001 aus
            # ABER behält 415011, 415021, 415031, 415061 (echte Kosten auf KST 1-6)!
            umlage_kosten_filter = """AND NOT (
                debit_or_credit = 'H'
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0'
                AND (posting_text LIKE '%%Kostenumlage%%'
                     OR posting_text LIKE '%%kostenumlage%%')
            )"""

            # Berechne Umlage-Betrag für Info-Anzeige (Erlös-Seite)
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

                # Berechne auch den Kosten-Filter-Betrag für Info (nur KST 0)
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
        # SSOT: Alle TEK-KPIs aus get_tek_data (4-Lohn = rollierender Schnitt)
        api_data = get_tek_data(monat=monat, jahr=jahr, firma=firma, standort=standort, modus=modus, umlage=umlage)
        bereich_namen = {
            '1-NW': 'Neuwagen', '2-GW': 'Gebrauchtwagen',
            '3-Teile': 'Teile/Service', '4-Lohn': 'Werkstattlohn', '5-Sonst': 'Sonstige'
        }
        bereiche = {}
        for b in api_data['bereiche']:
            bkey = b.get('id', '')
            umsatz = b.get('umsatz')
            einsatz = b.get('einsatz')
            if umsatz is None:
                umsatz = 0
            if einsatz is None:
                einsatz = 0
            umsatz = float(umsatz)
            einsatz = float(einsatz)
            db1_val = b.get('db1')
            db1 = float(db1_val) if db1_val is not None else (umsatz - einsatz)
            marge_val = b.get('marge')
            marge = float(marge_val) if marge_val is not None else ((db1 / umsatz * 100) if umsatz else 0)
            bereiche[bkey] = {
                'name': bereich_namen.get(bkey, bkey),
                'umsatz': round(umsatz, 2),
                'einsatz': round(einsatz, 2),
                'db1': round(db1, 2),
                'marge': round(marge, 1),
                'hinweis': b.get('hinweis'),
                'einsatz_kalk': b.get('einsatz_kalk'),
                'db1_kalk': b.get('db1_kalk'),
                'marge_kalk': b.get('marge_kalk'),
            }
        gesamt = dict(api_data['gesamt'])
        total_db1 = gesamt['db1']
        kosten_data = None

        # =====================================================================
        # VOLLKOSTEN (nur modus='voll'): get_tek_data liefert nur Teilkosten
        # =====================================================================
        if modus == 'voll':
            kosten_data = berechne_vollkosten(von, bis, firma_filter_kosten, standort_code, umlage_kosten_filter)
            # Vollkosten in Bereiche/Gesamt aus get_tek_data mergen â†’ FIBU-Kostenstelle (5. Stelle)
            bereich_zu_kst = {'1-NW': '1', '2-GW': '2', '3-Teile': '6', '4-Lohn': '3', '5-Sonst': '7'}
            totals_var = totals_dir = totals_uml = 0
            for bkey in ['1-NW', '2-GW', '3-Teile', '4-Lohn', '5-Sonst']:
                if bkey not in bereiche:
                    continue
                kst = bereich_zu_kst.get(bkey, '0')
                var = kosten_data['variable'].get(kst, 0)
                dir_k = kosten_data['direkte'].get(kst, 0)
                uml = kosten_data['umlage_verteilt'].get(kst, 0)
                db1 = bereiche[bkey]['db1']
                db2 = db1 - var
                db3 = db2 - dir_k
                be = db3 - uml
                bereiche[bkey].update({
                    'variable_kosten': round(var, 2),
                    'db2': round(db2, 2),
                    'direkte_kosten': round(dir_k, 2),
                    'db3': round(db3, 2),
                    'umlage': round(uml, 2),
                    'be': round(be, 2)
                })
                totals_var += var
                totals_dir += dir_k
                totals_uml += uml
            total_db2 = total_db1 - totals_var
            total_db3 = total_db2 - totals_dir
            total_be = total_db3 - totals_uml
            gesamt.update({
                'variable_kosten': round(totals_var, 2),
                'db2': round(total_db2, 2),
                'direkte_kosten': round(totals_dir, 2),
                'db3': round(total_db3, 2),
                'umlage': round(totals_uml, 2),
                'indirekte_gesamt': round(kosten_data['indirekte_gesamt'], 2),
                'be': round(total_be, 2)
            })

        # =====================================================================
        # VM/VJ PRO BEREICH (gleicher Zeitraum: erste N Tage / bis gleicher Tag)
        # =====================================================================
        vm_monat_calc, vm_jahr_calc = (12, jahr - 1) if monat == 1 else (monat - 1, jahr)
        vm_von_bereich = f"{vm_jahr_calc}-{vm_monat_calc:02d}-01"
        # VM: bei aktuellem Monat nur erste N Tage (N = heute.day), sonst voller Vormonat
        if monat == heute.month and jahr == heute.year:
            last_day_vm = calendar.monthrange(vm_jahr_calc, vm_monat_calc)[1]
            n_tage_vm = min(heute.day, last_day_vm)
            vm_ende = date(vm_jahr_calc, vm_monat_calc, n_tage_vm) + timedelta(days=1)
            vm_bis_bereich = vm_ende.strftime("%Y-%m-%d")
        else:
            vm_bis_bereich = f"{vm_jahr_calc}-{vm_monat_calc+1:02d}-01" if vm_monat_calc < 12 else f"{vm_jahr_calc+1}-01-01"

        # VJ pro Bereich: bei aktuellem Monat nur bis gleicher Tag (wie get_tek_data), sonst voller Monat
        vj_jahr_bereich = jahr - 1
        vj_von_bereich = f"{vj_jahr_bereich}-{monat:02d}-01"
        if monat == heute.month and jahr == heute.year:
            vj_bis_bereich = f"{vj_jahr_bereich}-{monat:02d}-{heute.day+1:02d}"
        else:
            vj_bis_bereich = f"{vj_jahr_bereich}-{monat+1:02d}-01" if monat < 12 else f"{vj_jahr_bereich+1}-01-01"

        # VM-Daten pro Bereich holen (TAG157: firma_filter_einsatz für korrekte Standort-Zuordnung!)
        vm_bereiche = get_bereich_daten(vm_von_bereich, vm_bis_bereich, firma_filter_umsatz, umlage_erloese_filter, firma_filter_einsatz)
        vj_bereiche = get_bereich_daten(vj_von_bereich, vj_bis_bereich, firma_filter_umsatz, umlage_erloese_filter, firma_filter_einsatz)

        # VM/VJ zu jedem Bereich hinzufügen
        for bkey in bereiche:
            vm_b = vm_bereiche.get(bkey, {})
            vj_b = vj_bereiche.get(bkey, {})
            bereiche[bkey]['vm_umsatz'] = vm_b.get('umsatz', 0)
            bereiche[bkey]['vm_db1'] = vm_b.get('db1', 0)
            bereiche[bkey]['vj_umsatz'] = vj_b.get('umsatz', 0)
            bereiche[bkey]['vj_db1'] = vj_b.get('db1', 0)

        # =====================================================================
        # STÜCKZAHLEN FÜR NW/GW (aus dealer_vehicles)
        # =====================================================================
        stueck_nw = get_stueckzahlen_locosoft(von, bis, '1-NW', firma, standort)
        stueck_gw = get_stueckzahlen_locosoft(von, bis, '2-GW', firma, standort)

        # VM-Stückzahlen
        vm_stueck_nw = get_stueckzahlen_locosoft(vm_von_bereich, vm_bis_bereich, '1-NW', firma, standort)
        vm_stueck_gw = get_stueckzahlen_locosoft(vm_von_bereich, vm_bis_bereich, '2-GW', firma, standort)

        # VJ-Stückzahlen
        vj_stueck_nw = get_stueckzahlen_locosoft(vj_von_bereich, vj_bis_bereich, '1-NW', firma, standort)
        vj_stueck_gw = get_stueckzahlen_locosoft(vj_von_bereich, vj_bis_bereich, '2-GW', firma, standort)

        # Stückzahlen zu Bereichen hinzufügen
        if '1-NW' in bereiche:
            bereiche['1-NW']['stueck'] = stueck_nw.get('gesamt_stueck', 0)
            bereiche['1-NW']['vm_stueck'] = vm_stueck_nw.get('gesamt_stueck', 0)
            bereiche['1-NW']['vj_stueck'] = vj_stueck_nw.get('gesamt_stueck', 0)
            # DB1/Stück berechnen
            if bereiche['1-NW']['stueck'] > 0:
                bereiche['1-NW']['db1_pro_stueck'] = round(bereiche['1-NW']['db1'] / bereiche['1-NW']['stueck'], 2)
            else:
                bereiche['1-NW']['db1_pro_stueck'] = 0

        if '2-GW' in bereiche:
            bereiche['2-GW']['stueck'] = stueck_gw.get('gesamt_stueck', 0)
            bereiche['2-GW']['vm_stueck'] = vm_stueck_gw.get('gesamt_stueck', 0)
            bereiche['2-GW']['vj_stueck'] = vj_stueck_gw.get('gesamt_stueck', 0)
            # DB1/Stück berechnen
            if bereiche['2-GW']['stueck'] > 0:
                bereiche['2-GW']['db1_pro_stueck'] = round(bereiche['2-GW']['db1'] / bereiche['2-GW']['stueck'], 2)
            else:
                bereiche['2-GW']['db1_pro_stueck'] = 0

        # Gesamt-Stückzahlen
        gesamt_stueck = stueck_nw.get('gesamt_stueck', 0) + stueck_gw.get('gesamt_stueck', 0)
        gesamt_vm_stueck = vm_stueck_nw.get('gesamt_stueck', 0) + vm_stueck_gw.get('gesamt_stueck', 0)
        gesamt_vj_stueck = vj_stueck_nw.get('gesamt_stueck', 0) + vj_stueck_gw.get('gesamt_stueck', 0)

        # Stückzahlen zum Gesamt-Objekt hinzufügen
        gesamt['stueck'] = gesamt_stueck
        gesamt['stueck_nw'] = stueck_nw.get('gesamt_stueck', 0)
        gesamt['stueck_gw'] = stueck_gw.get('gesamt_stueck', 0)
        
        # TAG176: DB1/Stk für GESAMT nur aus NW+GW berechnen (nicht Gesamt-DB1 inkl. Teile/Werkstatt!)
        # Nur der DB1 von Fahrzeugen (NW+GW) durch die Fahrzeug-Stückzahl teilen
        db1_nw_gw = 0
        if '1-NW' in bereiche:
            db1_nw_gw += bereiche['1-NW'].get('db1', 0)
        if '2-GW' in bereiche:
            db1_nw_gw += bereiche['2-GW'].get('db1', 0)
        
        if gesamt_stueck > 0:
            gesamt['db1_pro_stueck'] = round(db1_nw_gw / gesamt_stueck, 2)
        else:
            gesamt['db1_pro_stueck'] = 0

        # 4-Lohn aus get_tek_data (SSOT, inkl. rollierender Schnitt). Nur Produktivität ergänzen.
        betrieb_fuer_ws = firma if firma in ['1', '2'] else '0'
        ws_produktivitaet = get_werkstatt_produktivitaet(von, bis, betrieb_fuer_ws)
        if '4-Lohn' in bereiche:
            bereiche['4-Lohn']['produktivitaet'] = ws_produktivitaet.get('produktivitaet', 75.0)
            bereiche['4-Lohn']['leistungsgrad'] = ws_produktivitaet.get('leistungsgrad', 85.0)

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
        # VORMONAT (gleicher Zeitraum: erste N Tage wie aktueller Monat) - TAG 136
        # =====================================================================
        vm_monat, vm_jahr = (12, jahr - 1) if monat == 1 else (monat - 1, jahr)
        vm_von = f"{vm_jahr}-{vm_monat:02d}-01"
        if monat == heute.month and jahr == heute.year:
            last_day_vm = calendar.monthrange(vm_jahr, vm_monat)[1]
            n_tage_vm = min(heute.day, last_day_vm)
            vm_ende = date(vm_jahr, vm_monat, n_tage_vm) + timedelta(days=1)
            vm_bis = vm_ende.strftime("%Y-%m-%d")
        else:
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

            # TAG157: firma_filter_einsatz für korrekte Standort-Zuordnung!
            cursor.execute(convert_placeholders(f"""
                SELECT SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as einsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number BETWEEN 700000 AND 799999
                  {firma_filter_einsatz}
            """), (vm_von, vm_bis))
            row = cursor.fetchone()
            vm_einsatz = float(row_to_dict(row)['einsatz'] or 0) if row else 0

        vm_db1 = vm_umsatz - vm_einsatz

        # =====================================================================
        # VORJAHR (bei aktuellem Monat: bis gleicher Tag wie SSOT) - TAG 136
        # =====================================================================
        vj_jahr = jahr - 1
        vj_von = f"{vj_jahr}-{monat:02d}-01"
        if monat == heute.month and jahr == heute.year:
            vj_bis = f"{vj_jahr}-{monat:02d}-{heute.day+1:02d}"
        else:
            vj_bis = f"{vj_jahr}-{monat+1:02d}-01" if monat < 12 else f"{vj_jahr+1}-01-01"

        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_placeholders(f"""
                SELECT SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
                  {firma_filter_umsatz}
            """), (vj_von, vj_bis))
            row = cursor.fetchone()
            vj_umsatz = float(row_to_dict(row)['umsatz'] or 0) if row else 0

            # TAG157: firma_filter_einsatz für korrekte Standort-Zuordnung!
            cursor.execute(convert_placeholders(f"""
                SELECT SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as einsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number BETWEEN 700000 AND 799999
                  {firma_filter_einsatz}
            """), (vj_von, vj_bis))
            row = cursor.fetchone()
            vj_einsatz = float(row_to_dict(row)['einsatz'] or 0) if row else 0

        vj_db1 = vj_umsatz - vj_einsatz

        # =====================================================================
        # BREAKEVEN-PROGNOSE - TAG 136: nutzt jetzt intern db_session()
        # ECHTE KOSTEN - keine anteilige Verteilung!
        # Hyundai ist nur eine formaljuristische Hülle ohne eigene Kostenstruktur.
        # Die echten Kosten werden über firma_filter_kosten zugeordnet.
        # TAG157: firma_filter_einsatz für korrekte Standort-Zuordnung!
        # =====================================================================
        prognose = api_data.get('prognose_detail') or {}

        # =====================================================================
        # STANDORT-BREAKEVENS (nur wenn Alle Firmen oder Stellantis)
        # Kosten werden nach 6. Ziffer der Kontonummer gefiltert:
        #   Ziffer 1 = Deggendorf, Ziffer 2 = Landau
        # =====================================================================
        standort_breakevens = None
        if firma in ['0', '1'] and standort == '0':
            # SSOT: Standort-DB1 aus get_tek_data (gleiche Logik wie Gesamt)
            data_dego = get_tek_data(monat=monat, jahr=jahr, firma='1', standort='1', modus=modus, umlage=umlage)
            data_lano = get_tek_data(monat=monat, jahr=jahr, firma='1', standort='2', modus=modus, umlage=umlage)
            dego_db1 = data_dego['gesamt']['db1']
            lano_db1 = data_lano['gesamt']['db1']

            # Werktage aus Gesamt-Prognose
            werktage_info = prognose.get('werktage', {}) if prognose else {}

            # Breakeven mit standortspezifischem Kosten-Filter
            # Deggendorf: 6. Ziffer = 1
            dego_prognose = berechne_breakeven_prognose_standort(
                monat, jahr, dego_db1,
                " AND branch_number = 1",
                " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'",
                " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
            )
            # Landau: 6. Ziffer = 2
            lano_prognose = berechne_breakeven_prognose_standort(
                monat, jahr, lano_db1,
                " AND branch_number = 3",
                " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'",
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
        # TAGESWERTE - Letzte zwei Werktage nebeneinander (TAG198)
        # =====================================================================
        # TAG198: Nur Werktage anzeigen, aktueller Tag erst nach 19:00 Uhr
        jetzt = datetime.now()
        aktuelle_stunde = jetzt.hour
        
        # TAG198: Aktueller Tag erst nach 19:00 Uhr anzeigen (nach Locosoft Update)
        if aktuelle_stunde >= 19:
            heute = jetzt.date()
        else:
            # Vor 19:00 Uhr: Zeige gestern als "heute"
            heute = (jetzt - timedelta(days=1)).date()
        
        # TAG198: Nur Werktage anzeigen (Mo-Fr)
        # Finde letzten Werktag (heute oder davor)
        while heute.weekday() >= 5:  # 5=Samstag, 6=Sonntag
            heute = heute - timedelta(days=1)
        
        # Vortag: Letzter Werktag vor "heute"
        vortag = heute - timedelta(days=1)
        while vortag.weekday() >= 5:  # Nur Werktage
            vortag = vortag - timedelta(days=1)
        
        morgen = heute + timedelta(days=1)  # Morgen (für Datumsbereich)
        
        heute_daten = None
        vortag_daten = None
        heute_bereiche = {}
        vortag_bereiche = {}
        
        # Hole Daten für beide Tage (wenn im aktuellen Monat)
        if heute.year == jahr and heute.month == monat:
            heute_str = heute.isoformat()
            morgen_str = morgen.isoformat()
            
            with locosoft_session() as loco_conn:
                loco_cur = loco_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # =================================================================
                # HEUTE (neuester Tag)
                # =================================================================
                # Tagesumsatz GESAMT (Heute)
                loco_cur.execute(f"""
                    SELECT
                        COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
                    FROM journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN 800000 AND 899999
                      {firma_filter_umsatz if firma_filter_umsatz else ''}
                """, (heute_str, morgen_str))
                heute_umsatz = float(loco_cur.fetchone()['umsatz'] or 0)
                
                # Tageseinsatz GESAMT (Heute)
                loco_cur.execute(f"""
                    SELECT
                        COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as einsatz
                    FROM journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN 700000 AND 799999
                      {firma_filter_einsatz if firma_filter_einsatz else ''}
                """, (heute_str, morgen_str))
                heute_einsatz = float(loco_cur.fetchone()['einsatz'] or 0)
                
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
                      {firma_filter_umsatz if firma_filter_umsatz else ''}
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
                      {firma_filter_einsatz if firma_filter_einsatz else ''}
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
                
                heute_db1 = heute_umsatz - heute_einsatz
                heute_daten = {
                    'datum': heute_str,
                    'datum_formatiert': heute.strftime('%d.%m.'),
                    'wochentag': ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'][heute.weekday()],
                    'umsatz': round(heute_umsatz, 2),
                    'einsatz': round(heute_einsatz, 2),
                    'db1': round(heute_db1, 2)
                }
                
                # =================================================================
                # VORTAG (vorletzter Tag)
                # =================================================================
                if vortag.year == jahr and vortag.month == monat:
                    vortag_str = vortag.isoformat()
                    
                    # Tagesumsatz GESAMT (Vortag)
                    loco_cur.execute(f"""
                        SELECT
                            COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
                        FROM journal_accountings
                        WHERE accounting_date >= %s AND accounting_date < %s
                          AND nominal_account_number BETWEEN 800000 AND 899999
                          {firma_filter_umsatz if firma_filter_umsatz else ''}
                    """, (vortag_str, heute_str))
                    vortag_umsatz = float(loco_cur.fetchone()['umsatz'] or 0)
                    
                    # Tageseinsatz GESAMT (Vortag)
                    loco_cur.execute(f"""
                        SELECT
                            COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as einsatz
                        FROM journal_accountings
                        WHERE accounting_date >= %s AND accounting_date < %s
                          AND nominal_account_number BETWEEN 700000 AND 799999
                          {firma_filter_einsatz if firma_filter_einsatz else ''}
                    """, (vortag_str, heute_str))
                    vortag_einsatz = float(loco_cur.fetchone()['einsatz'] or 0)
                    
                    # Tagesumsatz PRO BEREICH (Vortag)
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
                          {firma_filter_umsatz if firma_filter_umsatz else ''}
                        GROUP BY bereich
                    """, (vortag_str, heute_str))
                    vortag_umsatz_bereich = {r['bereich']: float(r['umsatz'] or 0) for r in loco_cur.fetchall()}
                    
                    # Tageseinsatz PRO BEREICH (Vortag)
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
                          {firma_filter_einsatz if firma_filter_einsatz else ''}
                        GROUP BY bereich
                    """, (vortag_str, heute_str))
                    vortag_einsatz_bereich = {r['bereich']: float(r['einsatz'] or 0) for r in loco_cur.fetchall()}
                    
                    # Pro Bereich zusammenführen (Vortag)
                    for bkey in ['1-NW', '2-GW', '3-Teile', '4-Lohn', '5-Sonst']:
                        v_umsatz = vortag_umsatz_bereich.get(bkey, 0)
                        v_einsatz = vortag_einsatz_bereich.get(bkey, 0)
                        vortag_bereiche[bkey] = {
                            'umsatz': round(v_umsatz, 2),
                            'db1': round(v_umsatz - v_einsatz, 2)
                        }
                    
                    vortag_db1 = vortag_umsatz - vortag_einsatz
                    vortag_daten = {
                        'datum': vortag_str,
                        'datum_formatiert': vortag.strftime('%d.%m.'),
                        'wochentag': ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'][vortag.weekday()],
                        'umsatz': round(vortag_umsatz, 2),
                        'einsatz': round(vortag_einsatz, 2),
                        'db1': round(vortag_db1, 2)
                    }
                
                loco_cur.close()
        
        # Daten in Bereiche einfügen
        if heute_bereiche:
            for bkey in bereiche:
                if bkey in heute_bereiche:
                    bereiche[bkey]['heute_umsatz'] = heute_bereiche[bkey]['umsatz']
                    bereiche[bkey]['heute_db1'] = heute_bereiche[bkey]['db1']
        
        if vortag_bereiche:
            for bkey in bereiche:
                if bkey in vortag_bereiche:
                    bereiche[bkey]['vortag_umsatz'] = vortag_bereiche[bkey]['umsatz']
                    bereiche[bkey]['vortag_db1'] = vortag_bereiche[bkey]['db1']
        
        # TAG176: Beide Tage sind jetzt geholt (heute_daten, vortag_daten)
        # Daten sind bereits in bereiche eingefügt

        monat_namen = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
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
                'umsatz': round(gesamt['umsatz'] - vm_umsatz, 2),
                'umsatz_prozent': round((gesamt['umsatz'] - vm_umsatz) / vm_umsatz * 100, 1) if vm_umsatz > 0 else 0,
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
            'heute': heute_daten,  # Neuester Tag (z.B. 09.01.)
            'vortag': vortag_daten,  # Vorletzter Tag (z.B. 08.01.) - TAG176
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
}

def get_konto_bezeichnung(db, konto: int, subsidiary: int = 1) -> str:
    """
    Holt Kontobezeichnung aus loco_nominal_accounts (Locosoft Stammdaten).
    TAG 136: PostgreSQL-kompatibel

    Parameter:
    - db: Datenbankverbindung
    - konto: Kontonummer (z.B. 830001)
    - subsidiary: 1=Stellantis, 2=Hyundai (Standard: 1)

    Rückgabe: Erlösart z.B. "VE GM OT an Kunde Mechanik"
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
        '81': 'Erlöse Neuwagen', '82': 'Erlöse Gebrauchtwagen',
        '83': 'Erlöse Teile', '84': 'Erlöse Lohn',
        '71': 'Einsatz Neuwagen', '72': 'Einsatz Gebrauchtwagen',
        '73': 'Einsatz Teile', '74': 'Einsatz Lohn',
    }
    gruppe = gruppen_namen.get(prefix, '')
    return f"{gruppe} ({konto})" if gruppe else f"Konto {konto}"

@controlling_bp.route('/api/tek/detail')
@login_required
def api_tek_detail():
    """
    API: Drill-Down für TEK-Bereiche - Hierarchisch (Gruppen -> Konten -> Buchungen)
    
    Parameter:
    - bereich: '1-NW', '2-GW', '3-Teile', '4-Lohn', '5-Sonst'
    - firma, standort, monat, jahr: Filter (wie bei /api/tek)
    - ebene: 'gruppen' (Standard), 'konten', oder 'buchungen'
    - gruppe: (optional) 2-stelliges Präfix für Konten-Detail (z.B. '81')
    - konto: (optional) Für Buchungs-Details eines bestimmten Kontos
    - typ: 'umsatz' oder 'einsatz' (für Konten/Buchungen)
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
        
        # Firma/Standort-Filter bauen (Umsatz: branch_number, Einsatz: Konto-Endziffer wie Haupt-TEK)
        firma_filter = ""
        firma_filter_umsatz = ""
        firma_filter_einsatz = ""
        subsidiary = 1  # Default: Stellantis
        if firma == '1':
            firma_filter = "AND subsidiary_to_company_ref = 1"
            firma_filter_umsatz = "AND subsidiary_to_company_ref = 1"
            firma_filter_einsatz = "AND subsidiary_to_company_ref = 1"
            subsidiary = 1
            if standort == '1':
                firma_filter += " AND branch_number = 1"
                firma_filter_umsatz += " AND branch_number = 1"
                firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
            elif standort == '2':
                firma_filter += " AND branch_number = 3"
                firma_filter_umsatz += " AND branch_number = 3"
                firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
        elif firma == '2':
            firma_filter = "AND subsidiary_to_company_ref = 2"
            firma_filter_umsatz = "AND subsidiary_to_company_ref = 2"
            firma_filter_einsatz = "AND subsidiary_to_company_ref = 2"
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
            '81': 'Erlöse Neuwagen', '82': 'Erlöse Gebrauchtwagen', 
            '83': 'Erlöse Teile', '84': 'Erlöse Lohn',
            '85': 'Erlöse Lack', '86': 'Sonstige Erlöse', '88': 'Erlöse Vermietung',
            '89': 'Sonstige betriebliche Erträge',
            # Einsatz
            '71': 'Einsatz Neuwagen', '72': 'Einsatz Gebrauchtwagen',
            '73': 'Einsatz Teile', '74': 'Einsatz Lohn',
            '75': 'Einsatz Lack', '76': 'Sonstiger Einsatz', '78': 'Einsatz Vermietung',
        }
        
        if bereich not in bereich_konten:
            return jsonify({'success': False, 'error': f'Unbekannter Bereich: {bereich}'}), 400
        
        ranges = bereich_konten[bereich]
        
        # =====================================================================
        # EBENE: BUCHUNGEN (Detail für ein Konto)
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
        # EBENE: KONTEN (Detail für eine Gruppe, z.B. '81')
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

                # Optional: Einzelkonten für Drill-Down laden
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
        
        # Umsatz-Gruppen (mit Einzelkonten für Drill-Down)
        umsatz_gruppen = hole_gruppen(ranges['umsatz'], 'umsatz', mit_konten=True)
        umsatz_summe = sum(g['betrag'] for g in umsatz_gruppen)

        # Einsatz-Gruppen (mit Einzelkonten für Drill-Down)
        einsatz_gruppen = hole_gruppen(ranges['einsatz'], 'einsatz', mit_konten=True)
        einsatz_summe = sum(g['betrag'] for g in einsatz_gruppen)

        # 4-Lohn: Im laufenden Monat Einsatz Gruppe 74 kalkuliert (Method B, 6-Monats-Quote)
        # damit "Einsatz Lohn" in der Detail-Tabelle nicht 0 € anzeigt
        if bereich == '4-Lohn':
            werkstatt_umsatz = next((g['betrag'] for g in umsatz_gruppen if g['gruppe'] == '84'), 0)
            heute_d = date.today()
            bis_d = datetime.strptime(bis, '%Y-%m-%d').date()
            ist_laufender_monat = bis_d >= heute_d
            if ist_laufender_monat and werkstatt_umsatz > 0:
                aktueller_monat_start = heute_d.replace(day=1)
                bis_6m = aktueller_monat_start
                von_6m = bis_6m
                for _ in range(6):
                    von_6m = (von_6m - timedelta(days=1)).replace(day=1)
                cursor = db.cursor()
                cursor.execute(convert_placeholders("""
                    SELECT SUM(CASE WHEN nominal_account_number BETWEEN 840000 AND 849999 AND debit_or_credit = 'H' THEN posted_value
                                       WHEN nominal_account_number BETWEEN 840000 AND 849999 AND debit_or_credit = 'S' THEN -posted_value ELSE 0 END) / 100.0 as umsatz
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                    """ + firma_filter_umsatz), (von_6m.strftime('%Y-%m-%d'), bis_6m.strftime('%Y-%m-%d')))
                row = cursor.fetchone()
                umsatz_6m = float((row_to_dict(row, cursor) or {}).get('umsatz') or 0)
                cursor.execute(convert_placeholders("""
                    SELECT SUM(CASE WHEN nominal_account_number BETWEEN 740000 AND 749999 AND debit_or_credit = 'S' THEN posted_value
                                       WHEN nominal_account_number BETWEEN 740000 AND 749999 AND debit_or_credit = 'H' THEN -posted_value ELSE 0 END) / 100.0 as einsatz
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                    """ + firma_filter_einsatz), (von_6m.strftime('%Y-%m-%d'), bis_6m.strftime('%Y-%m-%d')))
                row = cursor.fetchone()
                einsatz_6m = float((row_to_dict(row, cursor) or {}).get('einsatz') or 0)
                einsatz_quote_6m = (einsatz_6m / umsatz_6m) if umsatz_6m > 0 else 0.36
                einsatz_kalk_74 = round(werkstatt_umsatz * einsatz_quote_6m, 2)
                # Gruppe 74 in einsatz_gruppen setzen oder anlegen
                gr74 = next((g for g in einsatz_gruppen if g['gruppe'] == '74'), None)
                if gr74:
                    gr74['betrag'] = einsatz_kalk_74
                    gr74['kalkuliert'] = True
                else:
                    einsatz_gruppen.append({
                        'gruppe': '74',
                        'name': gruppen_namen.get('74', 'Einsatz Lohn'),
                        'betrag': einsatz_kalk_74,
                        'anzahl_konten': 0,
                        'buchungen_anzahl': 0,
                        'konten': [],
                        'kalkuliert': True
                    })
                einsatz_summe = sum(g['betrag'] for g in einsatz_gruppen)
            elif werkstatt_umsatz > 0:
                # Abgeschlossener Monat: 74 aus FIBU; Markierung entfernen
                for g in einsatz_gruppen:
                    g.pop('kalkuliert', None)

        db1 = umsatz_summe - einsatz_summe

        # =====================================================================
        # FAHRZEUG-GRUPPIERUNG nach Modell + Absatzweg (nur für NW, GW)
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

                # Modell-Statistik (Umsatz) mit Konten-Details für Drill-Down
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

                # Absatzweg-Statistik (Umsatz) mit Konten für Drill-Down
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
                # Auch Einsatz-Konten zum Drill-Down hinzufügen
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
                # Auch Einsatz-Konten zum Drill-Down hinzufügen
                absatzweg_stats[absatzweg]['konten'].append({
                    'konto': konto,
                    'bezeichnung': bezeichnung,
                    'umsatz': 0,
                    'einsatz': betrag,
                    'stueck': 0
                })

            # Modelle in Liste umwandeln (mit DB1 und Einzelkonten für Drill-Down)
            fahrzeuge = [
                {
                    'modell': m['modell'],
                    'stueck': m['stueck'],
                    'umsatz': round(m['umsatz'], 2),
                    'einsatz': round(m['einsatz'], 2),
                    'db1': round(m['umsatz'] - m['einsatz'], 2),
                    'db1_pro_stueck': round((m['umsatz'] - m['einsatz']) / m['stueck'], 2) if m['stueck'] > 0 else 0,
                    'konten': m.get('konten', [])  # Einzelkonten für Drill-Down
                }
                for m in modell_stats.values() if m['umsatz'] > 0 or m['einsatz'] > 0
            ]
            # Intelligente Sortierung: Echte Modelle oben (alphabetisch), Sammelposten unten
            def sortkey_modell(item):
                m = item['modell'].lower()
                # Diese Begriffe ans Ende sortieren
                nachrangig = ['sonstig', 'umlage', 'erlös', 'erloes', 'kosten', 'zubehör', 'zubehoer',
                              'garantie', 'bonus', 'prämie', 'praemie', 'provision', 'rabatt']
                for begriff in nachrangig:
                    if begriff in m:
                        return (1, item['modell'])  # Nach hinten
                return (0, item['modell'])  # Normale alphabetische Sortierung
            fahrzeuge.sort(key=sortkey_modell)

            # Absatzwege in Liste umwandeln (mit DB1 und Konten für Drill-Down)
            absatzwege = [
                {
                    'absatzweg': a['absatzweg'],
                    'stueck': a['stueck'],
                    'umsatz': round(a['umsatz'], 2),
                    'einsatz': round(a['einsatz'], 2),
                    'db1': round(a['umsatz'] - a['einsatz'], 2),
                    'db1_pro_stueck': round((a['umsatz'] - a['einsatz']) / a['stueck'], 2) if a['stueck'] > 0 else 0,
                    'konten': a.get('konten', [])  # Einzelkonten für Drill-Down
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
# TEK MODELL-ANSICHT - Fahrzeugstücke nach Modell gruppiert
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
            ('Großkunden ', 'Großkunde'),
            ('Großkd ', 'Großkunde'),
            ('Kunden ', 'Privat'),
            ('KD ', 'Privat'),
            ('Kd ', 'Privat'),
            ('Händler ', 'Händler'),
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
    # Reihenfolge wichtig: längere zuerst, um "Gewerbekd" vor "Gewkd" zu matchen
    kundentyp_patterns = [
        ('Gewerbekd ', 'Gewerbe'),
        ('Gewdkd ', 'Gewerbe'),   # Tippfehler in Locosoft
        ('Gewkd ', 'Gewerbe'),
        ('Großkunden ', 'Großkunde'),
        ('Großkd ', 'Großkunde'),
        ('Kunden ', 'Privat'),
        ('KD ', 'Privat'),
        ('Kd ', 'Privat'),
        ('Händler ', 'Händler'),
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
        # Suche Pattern (mit Leerzeichen davor für Wortgrenze)
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
    if kundentyp in ['Privat', 'Gewerbe', 'Großkunde', 'Händler', 'Sonstige']:
        return kundentyp
    # Mapping für Rohwerte aus Kontobezeichnung
    mapping = {
        'Kunden': 'Privat',
        'Kd': 'Privat',
        'KD': 'Privat',
        'Gewkd': 'Gewerbe',
        'Gewdkd': 'Gewerbe',  # Tippfehler in Locosoft
        'Gewerbekd': 'Gewerbe',
        'Großkd': 'Großkunde',
        'Großkunden': 'Großkunde',
        'Händler': 'Händler'
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
    Kategorisiert Modellnamen für bessere Gruppierung.

    Returns: (kategorie, sortierung)
        - kategorie: 'Fahrzeuge', 'Vorführwagen', 'Sonstige Fzg', 'Nebenerlöse', 'Unbekannt'
        - sortierung: Zahl für Reihenfolge (1=oben, 5=unten)
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

    # Vorführwagen
    if 'vfw' in m_lower or 'vorführ' in m_lower:
        return ('Vorführwagen', 2)

    # Sonstige Fahrzeuge
    if 'sonst' in m_lower and ('fzg' in m_lower or 'pkw' in m_lower or 'nw' in m_lower or 'gw' in m_lower):
        return ('Sonstige Fzg', 3)

    # Nebenerlöse (keine Fahrzeuge)
    if any(x in m_lower for x in ['umlage', 'zulassung', 'prov.', 'provision', 'garantie',
                                   'givit', 'finanz', 'sonst.verk', 'sonst.erl']):
        return ('Nebenerlöse', 4)

    # Unbekannte Konten (nur Kontonummer)
    if modell.startswith('Konto ') or modell.isdigit():
        return ('Unbekannt', 5)

    # Fallback: Als Fahrzeug behandeln
    return ('Fahrzeuge', 1)


def get_fibu_modell_daten(von: str, bis: str, bereich: str, firma: str, standort: str, subsidiary: int) -> dict:
    """
    Holt FiBu-Daten für einen Zeitraum, gruppiert nach Modell.
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
            return jsonify({'success': False, 'error': f'Bereich {bereich} nicht unterstützt für Modell-Ansicht'}), 400

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
            modell = normalisiere_fibu_modell(parsed['modell'])  # Normalisieren für Locosoft-Match
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
            modell = normalisiere_fibu_modell(parsed['modell'])  # Normalisieren für Locosoft-Match
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
        # LOCOSOFT STÜCKZAHLEN holen und mit FiBu-Daten mergen
        # =====================================================================
        stueckzahlen = get_stueckzahlen_locosoft(von, bis, bereich, firma, standort)
        gesamt_stueck = stueckzahlen.get('gesamt_stueck', 0)

        # Stückzahlen zu den Modellen hinzufügen (Fuzzy-Match nach Modellname)
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

        # Vergleichswerte zu jedem Modell hinzufügen
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

        monat_namen = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
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

    Umlage nach MA-Schlüssel aus employees-Tabelle (gefiltert nach Standort)

    Parameter:
    - umlage_kosten_filter: Optionaler Filter um Umlage-Kosten auszuschließen (498001)
    """

    # MA-Verteilung holen (mit Standort-Filter)
    ma_verteilung = get_ma_verteilung(standort)

    # Produktive KST (ohne Verwaltung)
    produktiv_kst = ['12', '3', '6']  # 12=Verkauf(1+2), 3=Service, 6=Teile
    produktiv_ma = sum(ma_verteilung.get(k, 0) for k in produktiv_kst)

    # Umlage-Schlüssel berechnen
    umlage_schluessel = {}
    for kst in produktiv_kst:
        ma = ma_verteilung.get(kst, 0)
        umlage_schluessel[kst] = round(ma / produktiv_ma * 100, 1) if produktiv_ma > 0 else 0

    with db_session() as conn:
        cursor = conn.cursor()

        # =========================================================================
        # VARIABLE KOSTEN nach KST (5. Stelle)
        # Konten: 4151xx, 4355xx, 455-456xx, 487xx, 491-497xx
        # HINWEIS: umlage_kosten_filter auch hier anwenden für Konsistenz
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
        # WICHTIG: umlage_kosten_filter wird hier angewendet um Konto 498001 auszuschließen
        #          wenn "ohne Umlage" gewählt ist. Sonst werden die internen Umlagen
        #          (50.000 €/Monat als HABEN gebucht) die Kosten negativ machen!
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
    # UMLAGE VERTEILEN nach MA-Schlüssel
    # =========================================================================
    umlage_verteilt = {}
    for kst in produktiv_kst:
        anteil = umlage_schluessel.get(kst, 0) / 100
        umlage_verteilt[kst] = indirekte_gesamt * anteil
    
    # KST 1+2 zusammenfassen für Verkauf (wird in API auf NW/GW aufgeteilt)
    # Für TEK: 1=NW, 2=GW brauchen separate Werte
    # Aufteilung 1/2 nach Umsatz-Verhältnis wäre ideal, hier erstmal 50/50
    if '12' in umlage_verteilt:
        verkauf_umlage = umlage_verteilt['12']
        umlage_verteilt['1'] = verkauf_umlage * 0.5
        umlage_verteilt['2'] = verkauf_umlage * 0.5
    
    # Variable/Direkte für 1+2 auch aufteilen
    for d in [variable, direkte]:
        if '1' in d and '2' in d:
            pass  # Schon getrennt
        elif '1' not in d and '2' not in d:
            # Keine Daten für 1 oder 2
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

        # TAG 136: Datumsfunktion für PostgreSQL/SQLite
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


@controlling_bp.route('/auswertung-zeiterfassung')
@login_required
def auswertung_zeiterfassung():
    """Auswertung Zeiterfassung - Tabellarische Darstellung für alle Mitarbeiter"""
    from api.werkstatt_data import WerkstattData
    from datetime import date, timedelta
    
    # Zeitraum-Parameter
    zeitraum = request.args.get('zeitraum', 'monat')
    betrieb_param = request.args.get('betrieb', 'alle')
    
    # Datumsbereich berechnen
    heute = date.today()
    if zeitraum == 'heute':
        datum_von = datum_bis = heute
    elif zeitraum == 'woche':
        datum_von = heute - timedelta(days=heute.weekday())
        datum_bis = heute
    elif zeitraum == 'monat':
        datum_von = heute.replace(day=1)
        datum_bis = heute
    elif zeitraum == 'vormonat':
        erster_aktuell = heute.replace(day=1)
        letzter_vormonat = erster_aktuell - timedelta(days=1)
        datum_von = letzter_vormonat.replace(day=1)
        datum_bis = letzter_vormonat
    elif zeitraum == 'quartal':
        quartal_start_monat = ((heute.month - 1) // 3) * 3 + 1
        datum_von = heute.replace(month=quartal_start_monat, day=1)
        datum_bis = heute
    elif zeitraum == 'jahr':
        datum_von = heute.replace(month=1, day=1)
        datum_bis = heute
    else:
        datum_von = heute.replace(day=1)
        datum_bis = heute
    
    # Betrieb-Parameter
    betrieb = int(betrieb_param) if betrieb_param and betrieb_param != 'alle' else None
    
    # Daten holen
    try:
        analyse = WerkstattData.get_alle_mitarbeiter_stempelzeit_analyse(
            von=datum_von,
            bis=datum_bis,
            betrieb=betrieb,
            nur_aktive=True
        )
        
        return render_template(
            'controlling/auswertung_zeiterfassung.html',
            analyse=analyse,
            zeitraum=zeitraum,
            betrieb=betrieb_param,
            datum_von=datum_von.isoformat(),
            datum_bis=datum_bis.isoformat()
        )
    except Exception as e:
        return render_template(
            'controlling/auswertung_zeiterfassung.html',
            error=str(e),
            zeitraum=zeitraum,
            betrieb=betrieb_param
        )
