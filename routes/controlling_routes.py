from flask import Blueprint, render_template, jsonify, request
from decorators.auth_decorators import login_required
import sqlite3
from datetime import datetime, date, timedelta
import calendar

# =============================================================================
# WERKTAGE-BERECHNUNG (TAG121)
# =============================================================================

# Bayerische Feiertage 2025
FEIERTAGE_2025 = [
    datetime(2025, 1, 1),    # Neujahr
    datetime(2025, 1, 6),    # Heilige Drei Könige
    datetime(2025, 4, 18),   # Karfreitag
    datetime(2025, 4, 21),   # Ostermontag
    datetime(2025, 5, 1),    # Tag der Arbeit
    datetime(2025, 5, 29),   # Christi Himmelfahrt
    datetime(2025, 6, 9),    # Pfingstmontag
    datetime(2025, 6, 19),   # Fronleichnam
    datetime(2025, 8, 15),   # Mariä Himmelfahrt
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
    """SQLite-Verbindung herstellen"""
    conn = sqlite3.connect('data/greiner_controlling.db')
    conn.row_factory = sqlite3.Row
    return conn

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

def get_ma_verteilung(db, standort: str = '0') -> dict:
    """
    Holt aktuelle MA-Verteilung aus der employees-Tabelle
    Mapping: department_name -> Kostenstelle
    
    Parameter:
    - standort: '0'=Alle, '1'=Deggendorf, '3'=Landau
    """
    standort_filter = ""
    if standort == '1':
        standort_filter = "AND location = 'Deggendorf'"
    elif standort == '3':
        standort_filter = "AND location = 'Landau a.d. Isar'"
    
    result = db.execute(f"""
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
        WHERE active = 1
        {standort_filter}
        GROUP BY kst
    """).fetchall()
    
    verteilung = {row['kst']: row['anzahl'] for row in result}
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
    return render_template('controlling/bwa.html',
                         page_title='BWA',
                         active_page='controlling')

@controlling_bp.route('/tek')
@login_required
def tek_dashboard():
    return render_template('controlling/tek_dashboard.html',
                         page_title='Tägliche Erfolgskontrolle',
                         active_page='controlling')


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
        
        db = get_db()
        
        # Filter bauen
        # WICHTIG: Für Umsatz/Einsatz (7/8xxxxx) gilt branch_number
        #          Für Kosten (4xxxxx) gilt die letzte Ziffer der Kontonummer!
        #          - Letzte Ziffer 1 = Deggendorf
        #          - Letzte Ziffer 2 = Landau
        #          - subsidiary_to_company_ref 2 = Hyundai (separate Firma)
        
        firma_filter = ""
        firma_filter_umsatz = ""   # Für Umsatz/Einsatz: branch_number
        firma_filter_kosten = ""   # Für Kosten: letzte Ziffer der Kontonummer
        standort_name = "Alle"
        standort_code = standort  # Für MA-Verteilung
        
        if firma == '1':
            # Stellantis (Autohaus Greiner)
            firma_filter = "AND subsidiary_to_company_ref = 1"
            firma_filter_umsatz = "AND subsidiary_to_company_ref = 1"
            firma_filter_kosten = "AND subsidiary_to_company_ref = 1"
            standort_name = "Stellantis (DEG+LAN)"
            if standort == '1':
                # Deggendorf: branch_number=1 für Umsatz, letzte Ziffer=1 für Kosten
                firma_filter_umsatz += " AND branch_number = 1"
                firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
                standort_name = "Deggendorf"
                standort_code = '1'
            elif standort == '2':  # Landau (früher '3' für branch, jetzt '2' für Konto-Endung)
                # Landau: branch_number=3 für Umsatz, letzte Ziffer=2 für Kosten
                firma_filter_umsatz += " AND branch_number = 3"
                firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
                standort_name = "Landau"
                standort_code = '3'  # Für MA-Verteilung in employees (location='Landau')
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
                AND (posting_text LIKE '%Kostenumlage%' 
                     OR posting_text LIKE '%kostenumlage%')
            )"""
            
            # Berechne Umlage-Betrag für Info-Anzeige (Erlös-Seite)
            umlage_result = db.execute(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as betrag
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number IN ({umlage_konten_str})
                  {firma_filter_umsatz}
            """, (von, bis)).fetchone()
            umlage_betrag = umlage_result['betrag'] if umlage_result else 0
            
            # Berechne auch den Kosten-Filter-Betrag für Info (nur KST 0)
            umlage_kosten_result = db.execute(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as betrag
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND debit_or_credit = 'H'
                  AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0'
                  AND (posting_text LIKE '%Kostenumlage%' OR posting_text LIKE '%kostenumlage%')
                  AND nominal_account_number BETWEEN 400000 AND 499999
                  {firma_filter_kosten}
            """, (von, bis)).fetchone()
            umlage_kosten_betrag = abs(umlage_kosten_result['betrag']) if umlage_kosten_result else 0
        
        # =====================================================================
        # UMSATZ NACH BEREICHEN (branch_number für Standort-Filter)
        # =====================================================================
        umsatz_rows = db.execute(f"""
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
        """, (von, bis)).fetchall()
        
        # =====================================================================
        # EINSATZ NACH BEREICHEN (branch_number für Standort-Filter)
        # =====================================================================
        einsatz_rows = db.execute(f"""
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
        """, (von, bis)).fetchall()
        
        umsatz_dict = {r['bereich']: r['umsatz'] or 0 for r in umsatz_rows}
        einsatz_dict = {r['bereich']: r['einsatz'] or 0 for r in einsatz_rows}
        
        # =====================================================================
        # VOLLKOSTEN (nur wenn modus='voll')
        # Verwendet firma_filter_kosten für Kosten-Konten (4xxxxx)
        # =====================================================================
        kosten_data = None
        if modus == 'voll':
            kosten_data = berechne_vollkosten(db, von, bis, firma_filter_kosten, standort_code, umlage_kosten_filter)
        
        # =====================================================================
        # BEREICHE ZUSAMMENFÜHREN
        # =====================================================================
        bereich_namen = {
            '1-NW': 'Neuwagen', '2-GW': 'Gebrauchtwagen',
            '3-Teile': 'Teile/Service', '4-Lohn': 'Werkstattlohn', '5-Sonst': 'Sonstige'
        }
        
        # Mapping: TEK-Bereich → FIBU-Kostenstelle (5. Stelle)
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
        
        # Andere Umsätze/Einsätze addieren
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
        # FIRMEN-VERGLEICH
        # =====================================================================
        firmen = None
        if firma == '0':
            firmen = {}
            for f_id, f_name in [('1', 'Stellantis'), ('2', 'Hyundai')]:
                f_umsatz = db.execute("""
                    SELECT SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND ((nominal_account_number BETWEEN 800000 AND 889999)
                           OR (nominal_account_number BETWEEN 893200 AND 893299))
                      AND subsidiary_to_company_ref = ?
                """, (von, bis, f_id)).fetchone()[0] or 0
                
                f_einsatz = db.execute("""
                    SELECT SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND nominal_account_number BETWEEN 700000 AND 799999
                      AND subsidiary_to_company_ref = ?
                """, (von, bis, f_id)).fetchone()[0] or 0
                
                f_db1 = f_umsatz - f_einsatz
                firmen[f_id] = {
                    'name': f_name,
                    'umsatz': round(f_umsatz, 2),
                    'einsatz': round(f_einsatz, 2),
                    'db1': round(f_db1, 2),
                    'marge': round((f_db1 / f_umsatz * 100) if f_umsatz > 0 else 0, 1)
                }
        
        # =====================================================================
        # VORMONAT (Umsatz/Einsatz -> firma_filter_umsatz)
        # =====================================================================
        vm_monat, vm_jahr = (12, jahr - 1) if monat == 1 else (monat - 1, jahr)
        vm_von = f"{vm_jahr}-{vm_monat:02d}-01"
        vm_bis = f"{vm_jahr}-{vm_monat+1:02d}-01" if vm_monat < 12 else f"{vm_jahr+1}-01-01"
        
        vm_umsatz = db.execute(f"""
            SELECT SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
              {firma_filter_umsatz}
        """, (vm_von, vm_bis)).fetchone()[0] or 0
        
        vm_einsatz = db.execute(f"""
            SELECT SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 700000 AND 799999
              {firma_filter_umsatz}
        """, (vm_von, vm_bis)).fetchone()[0] or 0
        
        vm_db1 = vm_umsatz - vm_einsatz
        
        # =====================================================================
        # BREAKEVEN-PROGNOSE
        # Verwendet firma_filter_umsatz für Umsatz, firma_filter_kosten für Kosten
        # =====================================================================
        prognose = berechne_breakeven_prognose(db, monat, jahr, total_db1, firma_filter_umsatz, firma_filter_kosten)
        
        db.close()
        
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
                'db1': round(vm_db1, 2), 'marge': round((vm_db1 / vm_umsatz * 100) if vm_umsatz > 0 else 0, 1)
            },
            'veraenderung': {
                'umsatz': round(totals['umsatz'] - vm_umsatz, 2),
                'umsatz_prozent': round((totals['umsatz'] - vm_umsatz) / vm_umsatz * 100, 1) if vm_umsatz > 0 else 0,
                'db1': round(total_db1 - vm_db1, 2),
                'db1_prozent': round((total_db1 - vm_db1) / abs(vm_db1) * 100, 1) if vm_db1 != 0 else 0
            },
            'prognose': prognose,
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
        
        # Firma/Standort-Filter bauen
        firma_filter = ""
        if firma == '1':
            firma_filter = "AND subsidiary_to_company_ref = 1"
            if standort == '1':
                firma_filter += " AND branch_number = 1"
            elif standort == '2':
                firma_filter += " AND branch_number = 3"
        elif firma == '2':
            firma_filter = "AND subsidiary_to_company_ref = 2"
        
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
            
            buchungen = db.execute(f"""
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
            """, (von, bis, konto)).fetchall()
            
            db.close()
            
            return jsonify({
                'success': True,
                'ebene': 'buchungen',
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
            
            konten = db.execute(f"""
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
                HAVING betrag != 0
                ORDER BY ABS(betrag) DESC
            """, (von, bis, konto_range[0], konto_range[1], gruppe)).fetchall()
            
            db.close()
            
            summe = sum(row['betrag'] for row in konten)
            gruppe_name = gruppen_namen.get(gruppe, f'Gruppe {gruppe}')
            
            return jsonify({
                'success': True,
                'ebene': 'konten',
                'bereich': bereich,
                'typ': typ,
                'gruppe': gruppe,
                'gruppe_name': gruppe_name,
                'konten': [{
                    'konto': row['konto'],
                    'bezeichnung': get_konto_bezeichnung(row['konto'], row['bezeichnung']),
                    'betrag': round(row['betrag'], 2),
                    'buchungen_anzahl': row['buchungen_anzahl']
                } for row in konten],
                'summe': round(summe, 2),
                'anzahl_konten': len(konten)
            }), 200
        
        # =====================================================================
        # EBENE: GRUPPEN (Standard - 2-stellige Kontengruppen)
        # =====================================================================
        def hole_gruppen(konto_range, vorzeichen_typ):
            if vorzeichen_typ == 'einsatz':
                vorzeichen = "CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END"
            else:
                vorzeichen = "CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END"
            
            rows = db.execute(f"""
                SELECT 
                    substr(CAST(nominal_account_number AS TEXT), 1, 2) as gruppe,
                    SUM({vorzeichen}) / 100.0 as betrag,
                    COUNT(DISTINCT nominal_account_number) as anzahl_konten,
                    COUNT(*) as buchungen_anzahl
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number BETWEEN ? AND ?
                  {firma_filter}
                GROUP BY gruppe
                HAVING betrag != 0
                ORDER BY ABS(betrag) DESC
            """, (von, bis, konto_range[0], konto_range[1])).fetchall()
            
            return [{
                'gruppe': row['gruppe'],
                'name': gruppen_namen.get(row['gruppe'], f"Gruppe {row['gruppe']}"),
                'betrag': round(row['betrag'], 2),
                'anzahl_konten': row['anzahl_konten'],
                'buchungen_anzahl': row['buchungen_anzahl']
            } for row in rows]
        
        # Umsatz-Gruppen
        umsatz_gruppen = hole_gruppen(ranges['umsatz'], 'umsatz')
        umsatz_summe = sum(g['betrag'] for g in umsatz_gruppen)
        
        # Einsatz-Gruppen
        einsatz_gruppen = hole_gruppen(ranges['einsatz'], 'einsatz')
        einsatz_summe = sum(g['betrag'] for g in einsatz_gruppen)
        
        db1 = umsatz_summe - einsatz_summe
        
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
                'anzahl_gruppen': len(umsatz_gruppen)
            },
            'einsatz': {
                'gruppen': einsatz_gruppen,
                'summe': round(einsatz_summe, 2),
                'anzahl_gruppen': len(einsatz_gruppen)
            },
            'db1': round(db1, 2)
        }), 200
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


# =============================================================================
# VOLLKOSTEN-BERECHNUNG
# =============================================================================

def berechne_vollkosten(db, von: str, bis: str, firma_filter: str, standort: str = '0', umlage_kosten_filter: str = '') -> dict:
    """
    Berechnet Vollkosten nach Kostenstellen (5. Stelle der Kontonummer)
    
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
    ma_verteilung = get_ma_verteilung(db, standort)
    
    # Produktive KST (ohne Verwaltung)
    produktiv_kst = ['12', '3', '6']  # 12=Verkauf(1+2), 3=Service, 6=Teile
    produktiv_ma = sum(ma_verteilung.get(k, 0) for k in produktiv_kst)
    
    # Umlage-Schlüssel berechnen
    umlage_schluessel = {}
    for kst in produktiv_kst:
        ma = ma_verteilung.get(kst, 0)
        umlage_schluessel[kst] = round(ma / produktiv_ma * 100, 1) if produktiv_ma > 0 else 0
    
    # =========================================================================
    # VARIABLE KOSTEN nach KST (5. Stelle)
    # Konten: 4151xx, 4355xx, 455-456xx, 487xx, 491-497xx
    # HINWEIS: umlage_kosten_filter auch hier anwenden für Konsistenz
    # =========================================================================
    variable_sql = f"""
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
    """
    
    variable_rows = db.execute(variable_sql, (von, bis)).fetchall()
    variable = {r['kst']: r['summe'] or 0 for r in variable_rows}
    
    # =========================================================================
    # DIREKTE KOSTEN nach KST (nur KST 1-7, ohne Variable)
    # Konten: 40-48xxxx mit KST != 0
    # WICHTIG: umlage_kosten_filter filtert HABEN-Buchungen mit "Kostenumlage" Text
    #          (z.B. auf 440001, 415001, etc.) - diese haben negative Werte!
    # =========================================================================
    direkte_sql = f"""
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
    """
    
    direkte_rows = db.execute(direkte_sql, (von, bis)).fetchall()
    direkte = {r['kst']: r['summe'] or 0 for r in direkte_rows}
    
    # =========================================================================
    # INDIREKTE KOSTEN (KST 0 = Verwaltung)
    # WICHTIG: umlage_kosten_filter wird hier angewendet um Konto 498001 auszuschließen
    #          wenn "ohne Umlage" gewählt ist. Sonst werden die internen Umlagen
    #          (50.000 €/Monat als HABEN gebucht) die Kosten negativ machen!
    # =========================================================================
    indirekte_sql = f"""
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
    """
    
    indirekte_gesamt = db.execute(indirekte_sql, (von, bis)).fetchone()['summe'] or 0
    
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
# BREAKEVEN-PROGNOSE
# =============================================================================

def berechne_breakeven_prognose(db, monat: int, jahr: int, aktueller_db1: float, 
                                 firma_filter_umsatz: str, firma_filter_kosten: str = None) -> dict:
    """
    Berechnet Breakeven-Prognose
    
    Parameter:
    - firma_filter_umsatz: Filter für Umsatz/Einsatz-Konten (7/8xxxxx) - nutzt branch_number
    - firma_filter_kosten: Filter für Kosten-Konten (4xxxxx) - nutzt letzte Ziffer
    
    Logik:
    - < 5 Buchungstage: Gleitender Durchschnitt (Ø DB1 der letzten 3 Monate)
    - >= 5 Buchungstage: Normale Hochrechnung basierend auf aktuellem DB1/Tag
    """
    # Fallback: Wenn kein separater Kosten-Filter, verwende Umsatz-Filter
    if firma_filter_kosten is None:
        firma_filter_kosten = firma_filter_umsatz
    
    von = f"{jahr}-{monat:02d}-01"
    bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"
    
    # 12-Monats-Durchschnitt Kosten (verwendet firma_filter_kosten für Kosten-Konten)
    kosten_12m = db.execute(f"""
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
                WHEN ((nominal_account_number BETWEEN 400000 AND 499999 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
                      OR (nominal_account_number BETWEEN 424000 AND 424999 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                      OR (nominal_account_number BETWEEN 438000 AND 438999 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                      OR nominal_account_number BETWEEN 498000 AND 499999
                      OR (nominal_account_number BETWEEN 891000 AND 896999 AND NOT (nominal_account_number BETWEEN 893200 AND 893299)))
                THEN CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END ELSE 0 END) / 100.0, 0) as indirekte
        FROM loco_journal_accountings
        WHERE accounting_date >= date('now', '-12 months') AND accounting_date < date('now')
        {firma_filter_kosten}
    """).fetchone()
    
    variable_12m = kosten_12m['variable'] or 0
    direkte_12m = kosten_12m['direkte'] or 0
    indirekte_12m = kosten_12m['indirekte'] or 0
    kosten_pro_monat = (variable_12m + direkte_12m + indirekte_12m) / 12
    
    # Operativer DB1 (ohne Umlagen) - verwendet firma_filter_umsatz
    operativ = db.execute(f"""
        SELECT 
            COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
        FROM loco_journal_accountings
        WHERE accounting_date >= ? AND accounting_date < ?
          AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
          AND nominal_account_number NOT BETWEEN 498000 AND 498999
          {firma_filter_umsatz}
    """, (von, bis)).fetchone()
    
    operativ_einsatz = db.execute(f"""
        SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as einsatz
        FROM loco_journal_accountings
        WHERE accounting_date >= ? AND accounting_date < ?
          AND nominal_account_number BETWEEN 700000 AND 799999
          {firma_filter_umsatz}
    """, (von, bis)).fetchone()
    
    operativ_db1 = (operativ['umsatz'] or 0) - (operativ_einsatz['einsatz'] or 0)
    
    # Hochrechnung - Tage mit Daten (Umsatz-basiert)
    tage_mit_daten = db.execute(f"""
        SELECT COUNT(DISTINCT accounting_date) as tage
        FROM loco_journal_accountings
        WHERE accounting_date >= ? AND accounting_date < ?
          AND nominal_account_number BETWEEN 700000 AND 899999
          {firma_filter_umsatz}
    """, (von, bis)).fetchone()['tage'] or 0

    # Werktage statt Kalendertage (TAG121)
    werktage = get_werktage_monat(jahr, monat)
    werktage_gesamt = werktage['gesamt']
    werktage_vergangen = werktage['vergangen']

    # Alte Variablen für Kompatibilität
    tage_im_monat = werktage_gesamt  # Jetzt Werktage statt 31
    
    # =========================================================================
    # PROGNOSE-METHODE: Gleitender Durchschnitt vs. Hochrechnung
    # =========================================================================
    hochrechnung_db1 = None
    prognose_methode = None
    db1_3m_schnitt = None
    
    if tage_mit_daten < 5:
        # GLEITENDER DURCHSCHNITT: Ø DB1 der letzten 3 abgeschlossenen Monate
        # (ohne Umlagen für faire Vergleichbarkeit) - verwendet firma_filter_umsatz
        db1_3m = db.execute(f"""
            SELECT 
                strftime('%Y-%m', accounting_date) as monat,
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
            WHERE accounting_date >= date(?, '-3 months')
              AND accounting_date < ?
              {firma_filter_umsatz}
            GROUP BY monat
            ORDER BY monat DESC
            LIMIT 3
        """, (von, von)).fetchall()
        
        if db1_3m and len(db1_3m) >= 2:
            # Berechne DB1 pro Monat
            db1_werte = [(row['umsatz'] or 0) - (row['einsatz'] or 0) for row in db1_3m]
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

    return {
        'kosten_12m_schnitt': {
            'variable': round(variable_12m / 12, 2),
            'direkte': round(direkte_12m / 12, 2),
            'indirekte': round(indirekte_12m / 12, 2),
            'gesamt': round(kosten_pro_monat, 2)
        },
        'breakeven_schwelle': round(kosten_pro_monat, 2),
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
    }


# =============================================================================
# WEITERE API-ENDPOINTS
# =============================================================================

@controlling_bp.route('/api/overview', methods=['GET'])
@login_required
def api_overview():
    try:
        db = get_db()
        include_gesellschafter = request.args.get('include_gesellschafter', 'false').lower() == 'true'
        
        operative_liq = db.execute("""
            SELECT COALESCE(SUM(saldo), 0) FROM v_aktuelle_kontostaende
            WHERE anzeige_gruppe = 'autohaus' AND ist_operativ = 1
        """).fetchone()[0] or 0
        
        kreditlinien = db.execute("""
            SELECT COALESCE(SUM(ABS(kreditlinie)), 0) FROM v_aktuelle_kontostaende
            WHERE anzeige_gruppe = 'autohaus' AND ist_operativ = 1 AND kreditlinie IS NOT NULL
        """).fetchone()[0] or 0
        
        fahrzeug_linien = db.execute("""
            SELECT COALESCE(SUM(original_betrag - aktueller_saldo), 0)
            FROM fahrzeugfinanzierungen WHERE aktiv = 1
        """).fetchone()[0] or 0
        
        verfuegbare_liq = operative_liq + kreditlinien + fahrzeug_linien
        
        zinsen = db.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM fibu_buchungen
            WHERE buchungstyp = 'zinsen' AND debit_credit = 'S' AND accounting_date >= date('now', '-12 months')
        """).fetchone()[0] or 0
        
        einkauf = db.execute("""
            SELECT COUNT(*) as anzahl, COALESCE(SUM(aktueller_saldo), 0) as summe
            FROM fahrzeugfinanzierungen WHERE aktiv = 1
        """).fetchone()
        
        umsatz = db.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM fibu_buchungen
            WHERE nominal_account BETWEEN 800000 AND 899999 AND debit_credit = 'H'
            AND accounting_date >= date('now', '-12 months')
        """).fetchone()[0] or 0
        
        gesellschafter_saldo = None
        if include_gesellschafter:
            gesellschafter_saldo = db.execute("""
                SELECT COALESCE(SUM(saldo), 0) FROM v_aktuelle_kontostaende WHERE anzeige_gruppe = 'gesellschafter'
            """).fetchone()[0]
        
        db.close()
        
        return jsonify({
            'liquiditaet': {
                'operativ': float(operative_liq),
                'kreditlinien': float(kreditlinien),
                'verfuegbar': float(verfuegbare_liq),
                'nutzungsgrad': round((operative_liq / verfuegbare_liq * 100), 1) if verfuegbare_liq > 0 else 0
            },
            'zinsen': float(zinsen),
            'einkauf': {
                'anzahl_fahrzeuge': einkauf[0] if einkauf else 0,
                'finanzierungssumme': float(einkauf[1]) if einkauf else 0
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
