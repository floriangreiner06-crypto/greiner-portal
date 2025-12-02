from flask import Blueprint, render_template, jsonify
from decorators.auth_decorators import login_required
import sqlite3
from datetime import datetime, date, timedelta
import calendar

def get_db():
    """SQLite-Verbindung herstellen"""
    conn = sqlite3.connect('data/greiner_controlling.db')
    conn.row_factory = sqlite3.Row
    return conn

controlling_bp = Blueprint('controlling', __name__, url_prefix='/controlling')

@controlling_bp.route('/dashboard')
@login_required
def dashboard():
    """Executive Controlling Dashboard - The Hero Page"""
    return render_template('controlling/dashboard.html',
                         page_title='Controlling Dashboard',
                         active_page='controlling')

@controlling_bp.route('/bwa')
@login_required
def bwa():
    """BWA - Betriebswirtschaftliche Auswertung (validiert gegen GlobalCube)"""
    return render_template('controlling/bwa.html',
                         page_title='BWA',
                         active_page='controlling')

@controlling_bp.route('/api/overview', methods=['GET'])
@login_required
def api_overview():
    """Dashboard Overview mit Multi-Entity-Support"""
    from flask import request
    
    try:
        db = get_db()
        include_gesellschafter = request.args.get('include_gesellschafter', 'false').lower() == 'true'
        
        # KPI 1: Operative Liquidität (Autohaus)
        operative_liq = db.execute("""
            SELECT COALESCE(SUM(saldo), 0)
            FROM v_aktuelle_kontostaende
            WHERE anzeige_gruppe = 'autohaus'
              AND ist_operativ = 1
        """).fetchone()[0] or 0
        
        # KPI 1b: Kreditlinien
        kreditlinien = db.execute("""
            SELECT COALESCE(SUM(ABS(kreditlinie)), 0)
            FROM v_aktuelle_kontostaende
            WHERE anzeige_gruppe = 'autohaus'
              AND ist_operativ = 1
              AND kreditlinie IS NOT NULL
        """).fetchone()[0] or 0
        
        # Verfügbare Fahrzeug-Linien
        fahrzeug_linien = db.execute("""
            SELECT COALESCE(SUM(original_betrag - aktueller_saldo), 0)
            FROM fahrzeugfinanzierungen
            WHERE aktiv = 1
        """).fetchone()[0] or 0
        
        verfuegbare_liq = operative_liq + kreditlinien + fahrzeug_linien
        
        # KPI 2: Zinsen (12 Monate)
        zinsen = db.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM fibu_buchungen
            WHERE buchungstyp = 'zinsen'
              AND debit_credit = 'S'
              AND accounting_date >= date('now', '-12 months')
        """).fetchone()[0] or 0
        
        # KPI 3: Einkauf
        einkauf = db.execute("""
            SELECT 
                COUNT(*) as anzahl,
                COALESCE(SUM(aktueller_saldo), 0) as summe
            FROM fahrzeugfinanzierungen
            WHERE aktiv = 1
        """).fetchone()
        
        # KPI 4: Umsatz (12 Monate)
        umsatz = db.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM fibu_buchungen
            WHERE nominal_account BETWEEN 800000 AND 899999
              AND debit_credit = 'H'
              AND accounting_date >= date('now', '-12 months')
        """).fetchone()[0] or 0
        
        # Optional: Gesellschafter
        gesellschafter_saldo = None
        if include_gesellschafter:
            gesellschafter_saldo = db.execute("""
                SELECT COALESCE(SUM(saldo), 0)
                FROM v_aktuelle_kontostaende
                WHERE anzeige_gruppe = 'gesellschafter'
            """).fetchone()[0]
        
        response = {
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
            'gesellschafter': {
                'saldo': float(gesellschafter_saldo) if gesellschafter_saldo is not None else None
            } if include_gesellschafter else None,
            'timestamp': datetime.now().isoformat()
        }
        
        db.close()
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@controlling_bp.route('/api/trends')
@login_required
def api_trends():
    """API: 6-Monats-Trends"""
    # TODO: Implement in Phase 2
    return jsonify({"status": "coming_soon"})


# =============================================================================
# TEK - Tägliche Erfolgskontrolle (100% validiert gegen BWA)
# =============================================================================

@controlling_bp.route('/tek')
@login_required
def tek_dashboard():
    """TEK Dashboard - Tägliche Erfolgskontrolle (GlobalCube F.04 Ersatz)"""
    return render_template('controlling/tek_dashboard.html',
                         page_title='Tägliche Erfolgskontrolle',
                         active_page='controlling')


@controlling_bp.route('/api/tek')
@login_required
def api_tek():
    """
    API: TEK-Daten (Umsatz, Einsatz, DB1 nach Bereichen) + Breakeven-Prognose
    
    100% validiert gegen BWA November 2025:
    - Umsatz: 2.603.946,04 € ✓
    - Einsatz: 2.233.979,84 € ✓
    - DB1: 369.966,20 € ✓
    """
    from flask import request
    
    try:
        firma = request.args.get('firma', '0')  # 0=Alle, 1=Stellantis, 2=Hyundai
        monat = request.args.get('monat', type=int)
        jahr = request.args.get('jahr', type=int)
        
        # Default: Aktueller Monat
        heute = date.today()
        if not monat:
            monat = heute.month
        if not jahr:
            jahr = heute.year
        
        # Datumsbereich
        von = f"{jahr}-{monat:02d}-01"
        if monat == 12:
            bis = f"{jahr+1}-01-01"
        else:
            bis = f"{jahr}-{monat+1:02d}-01"
        
        db = get_db()
        
        # Firma-Filter
        firma_filter = ""
        if firma != '0':
            firma_filter = f"AND subsidiary_to_company_ref = {firma}"
        
        # =====================================================================
        # UMSATZ NACH BEREICHEN (80-88xxxx + 8932xx)
        # =====================================================================
        umsatz_sql = f"""
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
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value 
                         ELSE -posted_value END) / 100.0 as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
              {firma_filter}
            GROUP BY bereich
            ORDER BY bereich
        """
        
        # =====================================================================
        # EINSATZ NACH BEREICHEN (70-79xxxx)
        # =====================================================================
        einsatz_sql = f"""
            SELECT 
                CASE 
                    WHEN nominal_account_number BETWEEN 710000 AND 719999 THEN '1-NW'
                    WHEN nominal_account_number BETWEEN 720000 AND 729999 THEN '2-GW'
                    WHEN nominal_account_number BETWEEN 730000 AND 739999 THEN '3-Teile'
                    WHEN nominal_account_number BETWEEN 740000 AND 749999 THEN '4-Lohn'
                    WHEN nominal_account_number BETWEEN 760000 AND 769999 THEN '5-Sonst'
                    ELSE '9-Andere'
                END as bereich,
                SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value 
                         ELSE -posted_value END) / 100.0 as einsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 700000 AND 799999
              {firma_filter}
            GROUP BY bereich
            ORDER BY bereich
        """
        
        umsatz_rows = db.execute(umsatz_sql, (von, bis)).fetchall()
        einsatz_rows = db.execute(einsatz_sql, (von, bis)).fetchall()
        
        # In Dict umwandeln
        umsatz_dict = {row['bereich']: row['umsatz'] or 0 for row in umsatz_rows}
        einsatz_dict = {row['bereich']: row['einsatz'] or 0 for row in einsatz_rows}
        
        # =====================================================================
        # BEREICHE ZUSAMMENFÜHREN
        # =====================================================================
        bereich_namen = {
            '1-NW': 'Neuwagen',
            '2-GW': 'Gebrauchtwagen',
            '3-Teile': 'Teile/Service',
            '4-Lohn': 'Werkstattlohn',
            '5-Sonst': 'Sonstige'
        }
        
        bereiche = {}
        total_umsatz = 0
        total_einsatz = 0
        
        for bereich_key in ['1-NW', '2-GW', '3-Teile', '4-Lohn', '5-Sonst']:
            u = umsatz_dict.get(bereich_key, 0)
            e = einsatz_dict.get(bereich_key, 0)
            db1 = u - e
            marge = (db1 / u * 100) if u > 0 else 0
            
            bereiche[bereich_key] = {
                'name': bereich_namen[bereich_key],
                'umsatz': round(u, 2),
                'einsatz': round(e, 2),
                'db1': round(db1, 2),
                'marge': round(marge, 1)
            }
            
            total_umsatz += u
            total_einsatz += e
        
        # 8932xx und Andere zum Gesamt-Umsatz addieren
        total_umsatz += umsatz_dict.get('6-8932', 0)
        total_umsatz += umsatz_dict.get('9-Andere', 0)
        total_einsatz += einsatz_dict.get('9-Andere', 0)
        
        total_db1 = total_umsatz - total_einsatz
        total_marge = (total_db1 / total_umsatz * 100) if total_umsatz > 0 else 0
        
        # =====================================================================
        # FIRMEN-VERGLEICH (wenn Alle gewählt)
        # =====================================================================
        firmen = None
        if firma == '0':
            firmen = {}
            for f_id, f_name in [('1', 'Stellantis'), ('2', 'Hyundai')]:
                f_umsatz = db.execute("""
                    SELECT SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value 
                                    ELSE -posted_value END) / 100.0
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND ((nominal_account_number BETWEEN 800000 AND 889999)
                           OR (nominal_account_number BETWEEN 893200 AND 893299))
                      AND subsidiary_to_company_ref = ?
                """, (von, bis, f_id)).fetchone()[0] or 0
                
                f_einsatz = db.execute("""
                    SELECT SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value 
                                    ELSE -posted_value END) / 100.0
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND nominal_account_number BETWEEN 700000 AND 799999
                      AND subsidiary_to_company_ref = ?
                """, (von, bis, f_id)).fetchone()[0] or 0
                
                f_db1 = f_umsatz - f_einsatz
                f_marge = (f_db1 / f_umsatz * 100) if f_umsatz > 0 else 0
                
                firmen[f_id] = {
                    'name': f_name,
                    'umsatz': round(f_umsatz, 2),
                    'einsatz': round(f_einsatz, 2),
                    'db1': round(f_db1, 2),
                    'marge': round(f_marge, 1)
                }
        
        # =====================================================================
        # VORMONAT VERGLEICH
        # =====================================================================
        if monat == 1:
            vm_monat = 12
            vm_jahr = jahr - 1
        else:
            vm_monat = monat - 1
            vm_jahr = jahr
        
        vm_von = f"{vm_jahr}-{vm_monat:02d}-01"
        if vm_monat == 12:
            vm_bis = f"{vm_jahr+1}-01-01"
        else:
            vm_bis = f"{vm_jahr}-{vm_monat+1:02d}-01"
        
        vm_umsatz = db.execute(f"""
            SELECT SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value 
                            ELSE -posted_value END) / 100.0
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
              {firma_filter}
        """, (vm_von, vm_bis)).fetchone()[0] or 0
        
        vm_einsatz = db.execute(f"""
            SELECT SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value 
                            ELSE -posted_value END) / 100.0
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 700000 AND 799999
              {firma_filter}
        """, (vm_von, vm_bis)).fetchone()[0] or 0
        
        vm_db1 = vm_umsatz - vm_einsatz
        vm_marge = (vm_db1 / vm_umsatz * 100) if vm_umsatz > 0 else 0
        
        # =====================================================================
        # BREAKEVEN-PROGNOSE (12-Monats-Durchschnitt Kosten)
        # =====================================================================
        prognose = berechne_breakeven_prognose(db, monat, jahr, total_db1, firma_filter)
        
        db.close()
        
        # Monatsnamen
        monat_namen = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
                       'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
        
        response = {
            'success': True,
            'filter': {
                'firma': firma,
                'firma_name': 'Alle' if firma == '0' else ('Stellantis' if firma == '1' else 'Hyundai'),
                'monat': monat,
                'monat_name': monat_namen[monat],
                'jahr': jahr,
                'von': von,
                'bis': bis
            },
            'gesamt': {
                'umsatz': round(total_umsatz, 2),
                'einsatz': round(total_einsatz, 2),
                'db1': round(total_db1, 2),
                'marge': round(total_marge, 1)
            },
            'bereiche': bereiche,
            'firmen': firmen,
            'vormonat': {
                'monat': vm_monat,
                'monat_name': monat_namen[vm_monat],
                'jahr': vm_jahr,
                'umsatz': round(vm_umsatz, 2),
                'einsatz': round(vm_einsatz, 2),
                'db1': round(vm_db1, 2),
                'marge': round(vm_marge, 1)
            },
            'veraenderung': {
                'umsatz': round(total_umsatz - vm_umsatz, 2),
                'umsatz_prozent': round((total_umsatz - vm_umsatz) / vm_umsatz * 100, 1) if vm_umsatz > 0 else 0,
                'db1': round(total_db1 - vm_db1, 2),
                'db1_prozent': round((total_db1 - vm_db1) / abs(vm_db1) * 100, 1) if vm_db1 != 0 else 0
            },
            'prognose': prognose,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


def berechne_breakeven_prognose(db, monat: int, jahr: int, aktueller_db1: float, firma_filter: str) -> dict:
    """
    Berechnet Breakeven-Prognose basierend auf:
    - 12-Monats-Durchschnitt der Kosten (Variable + Direkte + Indirekte)
    - Hochrechnung des aktuellen Monats (operativ, ohne Umlagen)
    """
    heute = date.today()
    
    # =========================================================================
    # 12-MONATS-DURCHSCHNITT KOSTEN (aus BWA-Logik)
    # =========================================================================
    kosten_12m = db.execute(f"""
        SELECT 
            -- Variable Kosten
            COALESCE(SUM(CASE 
                WHEN (nominal_account_number BETWEEN 415100 AND 415199
                      OR nominal_account_number BETWEEN 435500 AND 435599
                      OR (nominal_account_number BETWEEN 455000 AND 456999 
                          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                      OR (nominal_account_number BETWEEN 487000 AND 487099 
                          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                      OR nominal_account_number BETWEEN 491000 AND 497899)
                THEN CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                ELSE 0 END) / 100.0, 0) as variable,
            
            -- Direkte Kosten
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
                THEN CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                ELSE 0 END) / 100.0, 0) as direkte,
            
            -- Indirekte Kosten (OHNE 8932xx!)
            COALESCE(SUM(CASE 
                WHEN ((nominal_account_number BETWEEN 400000 AND 499999 
                       AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
                      OR (nominal_account_number BETWEEN 424000 AND 424999 
                          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                      OR (nominal_account_number BETWEEN 438000 AND 438999 
                          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                      OR nominal_account_number BETWEEN 498000 AND 499999
                      OR (nominal_account_number BETWEEN 891000 AND 896999
                          AND NOT (nominal_account_number BETWEEN 893200 AND 893299)))
                THEN CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                ELSE 0 END) / 100.0, 0) as indirekte
        FROM loco_journal_accountings
        WHERE accounting_date >= date('now', '-12 months')
          AND accounting_date < date('now')
          {firma_filter}
    """).fetchone()
    
    variable_12m = kosten_12m['variable'] or 0
    direkte_12m = kosten_12m['direkte'] or 0
    indirekte_12m = kosten_12m['indirekte'] or 0
    
    # Durchschnitt pro Monat
    kosten_pro_monat = (variable_12m + direkte_12m + indirekte_12m) / 12
    
    # =========================================================================
    # OPERATIVER DB1 (ohne Umlage-Konten 498xxx)
    # Für faire Hochrechnung am Monatsanfang
    # =========================================================================
    von = f"{jahr}-{monat:02d}-01"
    if monat == 12:
        bis = f"{jahr+1}-01-01"
    else:
        bis = f"{jahr}-{monat+1:02d}-01"
    
    # Operativer Umsatz (ohne 498xxx)
    operativ_result = db.execute(f"""
        SELECT 
            COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
        FROM loco_journal_accountings
        WHERE accounting_date >= ? AND accounting_date < ?
          AND ((nominal_account_number BETWEEN 800000 AND 889999)
               OR (nominal_account_number BETWEEN 893200 AND 893299))
          AND nominal_account_number NOT BETWEEN 498000 AND 498999
          {firma_filter}
    """, (von, bis)).fetchone()
    operativ_umsatz = operativ_result['umsatz'] or 0
    
    # Operativer Einsatz
    operativ_einsatz_result = db.execute(f"""
        SELECT 
            COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as einsatz
        FROM loco_journal_accountings
        WHERE accounting_date >= ? AND accounting_date < ?
          AND nominal_account_number BETWEEN 700000 AND 799999
          {firma_filter}
    """, (von, bis)).fetchone()
    operativ_einsatz = operativ_einsatz_result['einsatz'] or 0
    
    operativ_db1 = operativ_umsatz - operativ_einsatz
    
    # =========================================================================
    # HOCHRECHNUNG AKTUELLER MONAT
    # =========================================================================
    # Anzahl Tage mit Buchungen im aktuellen Monat
    tage_mit_daten = db.execute(f"""
        SELECT COUNT(DISTINCT accounting_date) as tage
        FROM loco_journal_accountings
        WHERE accounting_date >= ? AND accounting_date < ?
          AND nominal_account_number BETWEEN 700000 AND 899999
          {firma_filter}
    """, (von, bis)).fetchone()['tage'] or 0
    
    # Tage im Monat
    tage_im_monat = calendar.monthrange(jahr, monat)[1]
    
    # Hochrechnung nur wenn min. 3 Tage Daten
    if tage_mit_daten >= 3:
        db1_pro_tag = operativ_db1 / tage_mit_daten
        hochrechnung_db1 = db1_pro_tag * tage_im_monat
    else:
        hochrechnung_db1 = None  # Nicht aussagekräftig
    
    # =========================================================================
    # BREAKEVEN-STATUS
    # =========================================================================
    # Aktueller Monat: Vergleich DB1 vs. Ø-Kosten
    if aktueller_db1 >= kosten_pro_monat:
        status = 'positiv'
        ampel = 'gruen'
    elif hochrechnung_db1 and hochrechnung_db1 >= kosten_pro_monat:
        status = 'auf_kurs'
        ampel = 'gelb'
    else:
        status = 'kritisch'
        ampel = 'rot'
    
    # Benötigter DB1 für Breakeven
    db1_fuer_breakeven = kosten_pro_monat
    
    # Gap zum Breakeven
    gap = aktueller_db1 - kosten_pro_monat
    
    return {
        'kosten_12m_schnitt': {
            'variable': round(variable_12m / 12, 2),
            'direkte': round(direkte_12m / 12, 2),
            'indirekte': round(indirekte_12m / 12, 2),
            'gesamt': round(kosten_pro_monat, 2)
        },
        'breakeven_schwelle': round(db1_fuer_breakeven, 2),
        'aktueller_db1': round(aktueller_db1, 2),
        'operativer_db1': round(operativ_db1, 2),
        'tage_mit_daten': tage_mit_daten,
        'tage_im_monat': tage_im_monat,
        'hochrechnung_db1': round(hochrechnung_db1, 2) if hochrechnung_db1 else None,
        'hochrechnung_be': round(hochrechnung_db1 - kosten_pro_monat, 2) if hochrechnung_db1 else None,
        'gap': round(gap, 2),
        'gap_prozent': round(gap / kosten_pro_monat * 100, 1) if kosten_pro_monat > 0 else 0,
        'status': status,
        'ampel': ampel,
        'hinweis_umlage': tage_mit_daten < 5
    }
