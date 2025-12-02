from flask import Blueprint, render_template, jsonify
from decorators.auth_decorators import login_required
import sqlite3
from datetime import datetime

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
        """).fetchone()[0]
        
        # KPI 1b: Kreditlinien
        kreditlinien = db.execute("""
            SELECT COALESCE(SUM(ABS(kreditlinie)), 0)
            FROM v_aktuelle_kontostaende
            WHERE anzeige_gruppe = 'autohaus'
              AND ist_operativ = 1
              AND kreditlinie IS NOT NULL
        """).fetchone()[0]
        # Verfügbare Fahrzeug-Linien
        fahrzeug_linien = db.execute("""
            SELECT COALESCE(SUM(original_betrag - aktueller_saldo), 0)
            FROM fahrzeugfinanzierungen
            WHERE aktiv = 1
        """).fetchone()[0]
        verfuegbare_liq = operative_liq + kreditlinien + fahrzeug_linien
        
        # KPI 2: Zinsen (12 Monate)
        zinsen = db.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM fibu_buchungen
            WHERE buchungstyp = 'zinsen'
              AND debit_credit = 'S'
              AND accounting_date >= date('now', '-12 months')
        """).fetchone()[0]
        
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
        """).fetchone()[0]
        
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
                'anzahl_fahrzeuge': einkauf[0],
                'finanzierungssumme': float(einkauf[1])
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
# TEK - Tägliche Erfolgskontrolle
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
    """API: TEK-Daten (Umsatz, Einsatz, DB1 nach Bereichen)"""
    from flask import request
    
    try:
        firma = request.args.get('firma', '0')  # 0=Alle, 1=Opel, 2=Hyundai
        von = request.args.get('von', '2024-09-01')
        bis = request.args.get('bis', '2025-08-31')
        
        db = get_db()
        
        # Basis-Filter für Firma
        firma_filter = ""
        if firma != '0':
            firma_filter = f"AND subsidiary_to_company_ref = {firma}"
        
        # Umsatz nach Bereichen (8xxxxx) - inkl. 86 für Sonstige
        umsatz_sql = f"""
            SELECT 
                CASE 
                    WHEN nominal_account_number BETWEEN 810000 AND 819999 THEN '1-NW'
                    WHEN nominal_account_number BETWEEN 820000 AND 829999 THEN '2-GW'
                    WHEN nominal_account_number BETWEEN 830000 AND 839999 THEN '3-Teile'
                    WHEN nominal_account_number BETWEEN 840000 AND 849999 THEN '4-Lohn'
                    WHEN nominal_account_number BETWEEN 860000 AND 869999 THEN '5-Sonstige'
                END as bereich,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value/100.0 ELSE -posted_value/100.0 END) as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date BETWEEN ? AND ?
              AND (nominal_account_number BETWEEN 810000 AND 849999 OR nominal_account_number BETWEEN 860000 AND 869999)
              {firma_filter}
            GROUP BY bereich
            ORDER BY bereich
        """
        
        # Einsatz nach Bereichen (7xxxxx) - inkl. 76 für Sonstige
        einsatz_sql = f"""
            SELECT 
                CASE 
                    WHEN nominal_account_number BETWEEN 710000 AND 719999 THEN '1-NW'
                    WHEN nominal_account_number BETWEEN 720000 AND 729999 THEN '2-GW'
                    WHEN nominal_account_number BETWEEN 730000 AND 739999 THEN '3-Teile'
                    WHEN nominal_account_number BETWEEN 740000 AND 749999 THEN '4-Lohn'
                    WHEN nominal_account_number BETWEEN 760000 AND 769999 THEN '5-Sonstige'
                END as bereich,
                SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value/100.0 ELSE -posted_value/100.0 END) as einsatz
            FROM loco_journal_accountings
            WHERE accounting_date BETWEEN ? AND ?
              AND (nominal_account_number BETWEEN 710000 AND 749999 OR nominal_account_number BETWEEN 760000 AND 769999)
              {firma_filter}
            GROUP BY bereich
            ORDER BY bereich
        """
        
        umsatz_rows = db.execute(umsatz_sql, (von, bis)).fetchall()
        einsatz_rows = db.execute(einsatz_sql, (von, bis)).fetchall()
        
        # In Dict umwandeln
        umsatz_dict = {row['bereich']: row['umsatz'] for row in umsatz_rows if row['bereich']}
        einsatz_dict = {row['bereich']: row['einsatz'] for row in einsatz_rows if row['bereich']}
        
        # Bereiche zusammenführen
        # TODO: Konten für Produktivlöhne in FIBU erfragen - aktuell 40% Pauschale wie GlobalCube
        LOHN_PAUSCHALE = 0.40  # 40% vom Lohn-Umsatz als Einsatz
        
        bereiche = {}
        total_umsatz = 0
        total_einsatz = 0
        total_db1 = 0
        
        for bereich in ['1-NW', '2-GW', '3-Teile', '4-Lohn', '5-Sonstige']:
            u = umsatz_dict.get(bereich, 0) or 0
            
            # Lohn-Bereich: 40% Pauschale statt gebuchter Einsatz
            if bereich == '4-Lohn':
                e = u * LOHN_PAUSCHALE
            else:
                e = einsatz_dict.get(bereich, 0) or 0
            
            db1 = u - e
            
            bereiche[bereich] = {
                'umsatz': round(u, 2),
                'einsatz': round(e, 2),
                'db1': round(db1, 2)
            }
            
            total_umsatz += u
            total_einsatz += e
            total_db1 += db1
        
        marge = (total_db1 / total_umsatz * 100) if total_umsatz > 0 else 0
        
        # Firmen-Vergleich (wenn Gesamt gewählt)
        firmen = None
        if firma == '0':
            firmen = {}
            for f_id in ['1', '2']:
                f_umsatz = db.execute("""
                    SELECT SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value/100.0 ELSE -posted_value/100.0 END)
                    FROM loco_journal_accountings
                    WHERE accounting_date BETWEEN ? AND ?
                      AND (nominal_account_number BETWEEN 810000 AND 849999 OR nominal_account_number BETWEEN 860000 AND 869999)
                      AND subsidiary_to_company_ref = ?
                """, (von, bis, f_id)).fetchone()[0] or 0
                
                f_einsatz = db.execute("""
                    SELECT SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value/100.0 ELSE -posted_value/100.0 END)
                    FROM loco_journal_accountings
                    WHERE accounting_date BETWEEN ? AND ?
                      AND (nominal_account_number BETWEEN 710000 AND 749999 OR nominal_account_number BETWEEN 760000 AND 769999)
                      AND subsidiary_to_company_ref = ?
                """, (von, bis, f_id)).fetchone()[0] or 0
                
                f_db1 = f_umsatz - f_einsatz
                f_marge = (f_db1 / f_umsatz * 100) if f_umsatz > 0 else 0
                
                firmen[f_id] = {
                    'umsatz': round(f_umsatz, 2),
                    'einsatz': round(f_einsatz, 2),
                    'db1': round(f_db1, 2),
                    'marge': round(f_marge, 1)
                }
        
        response = {
            'success': True,
            'filter': {
                'firma': firma,
                'von': von,
                'bis': bis
            },
            'umsatz': round(total_umsatz, 2),
            'einsatz': round(total_einsatz, 2),
            'db1': round(total_db1, 2),
            'marge': round(marge, 1),
            'bereiche': bereiche,
            'firmen': firmen,
            'timestamp': datetime.now().isoformat()
        }
        
        db.close()
        return jsonify(response), 200
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# =============================================================================
# BWA - Betriebswirtschaftliche Auswertung (GlobalCube F.03)
# =============================================================================

@controlling_bp.route('/bwa')
@login_required
def bwa_dashboard():
    """BWA Dashboard - Vollkostenrechnung (GlobalCube F.03 Ersatz)"""
    return render_template('controlling/bwa_dashboard.html',
                         page_title='BWA - Betriebswirtschaftliche Auswertung',
                         active_page='controlling')


@controlling_bp.route('/api/bwa')
@login_required
def api_bwa():
    """API: BWA-Daten (DB1→DB2→DB3→Betriebsergebnis)"""
    from flask import request
    
    try:
        firma = request.args.get('firma', '0')
        von = request.args.get('von', '2025-10-01')
        bis = request.args.get('bis', '2025-10-31')
        
        db = get_db()
        
        firma_filter = ""
        if firma != '0':
            firma_filter = f"AND subsidiary_to_company_ref = {firma}"
        
        # =================================================================
        # UMSATZ (81-84, 86, 88 - OHNE 89xxxxx da nicht operativ)
        # =================================================================
        umsatz = db.execute(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value/100.0 
                                     ELSE -posted_value/100.0 END), 0)
            FROM loco_journal_accountings
            WHERE accounting_date BETWEEN ? AND ?
              AND nominal_account_number BETWEEN 800000 AND 889999
              {firma_filter}
        """, (von, bis)).fetchone()[0] or 0
        
        # =================================================================
        # EINSATZ (7xxxxx)
        # =================================================================
        einsatz = db.execute(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value/100.0 
                                     ELSE -posted_value/100.0 END), 0)
            FROM loco_journal_accountings
            WHERE accounting_date BETWEEN ? AND ?
              AND nominal_account_number BETWEEN 700000 AND 799999
              {firma_filter}
        """, (von, bis)).fetchone()[0] or 0
        
        db1 = umsatz - einsatz
        
        # =================================================================
        # VARIABLE KOSTEN (lt. GlobalCube Mapping)
        # WICHTIG: Nur Stelle5 != '0' (Kostenstelle variabel, nicht indirekt)
        # + 4151xx = Provisionen
        # =================================================================
        variable_kosten_sql = f"""
            SELECT 
                CASE 
                    WHEN nominal_account_number BETWEEN 415100 AND 415199 THEN 'provisionen'
                    WHEN nominal_account_number BETWEEN 491000 AND 491999 THEN 'fertigmachen'
                    WHEN nominal_account_number BETWEEN 492000 AND 494999 THEN 'fixum_prov'
                    WHEN nominal_account_number BETWEEN 497000 AND 497999 THEN 'kulanz'
                    WHEN nominal_account_number BETWEEN 435000 AND 435999 THEN 'training'
                    WHEN nominal_account_number BETWEEN 455000 AND 457999 THEN 'fahrzeugkosten'
                    WHEN nominal_account_number BETWEEN 487000 AND 488999 THEN 'werbekosten'
                    ELSE NULL
                END as kategorie,
                SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value/100.0 
                         ELSE -posted_value/100.0 END) as betrag
            FROM loco_journal_accountings
            WHERE accounting_date BETWEEN ? AND ?
              AND substr(nominal_account_number, 5, 1) != '0'
              AND (nominal_account_number BETWEEN 415100 AND 415199
                   OR nominal_account_number BETWEEN 435000 AND 435999
                   OR nominal_account_number BETWEEN 455000 AND 457999
                   OR nominal_account_number BETWEEN 487000 AND 488999
                   OR nominal_account_number BETWEEN 491000 AND 497999)
              AND nominal_account_number NOT BETWEEN 498000 AND 498999
              {firma_filter}
            GROUP BY kategorie
            HAVING kategorie IS NOT NULL
        """
        
        var_kosten_rows = db.execute(variable_kosten_sql, (von, bis)).fetchall()
        
        variable_kosten = {
            'provisionen': 0, 'fertigmachen': 0, 'fixum_prov': 0, 'kulanz': 0,
            'training': 0, 'fahrzeugkosten': 0, 'werbekosten': 0
        }
        for row in var_kosten_rows:
            if row['kategorie'] in variable_kosten:
                variable_kosten[row['kategorie']] = round(row['betrag'] or 0, 2)
        
        variable_kosten_summe = sum(variable_kosten.values())
        db2 = db1 - variable_kosten_summe
        
        # =================================================================
        # DIREKTE KOSTEN (Produktivlöhne - 4150xx und 4152xx-4159xx)
        # OHNE 4151xx da diese Provisionen sind (bereits in Variable Kosten)
        # =================================================================
        direkte_kosten = db.execute(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value/100.0 
                                     ELSE -posted_value/100.0 END), 0)
            FROM loco_journal_accountings
            WHERE accounting_date BETWEEN ? AND ?
              AND nominal_account_number BETWEEN 415000 AND 415999
              AND nominal_account_number NOT BETWEEN 415100 AND 415199
              {firma_filter}
        """, (von, bis)).fetchone()[0] or 0
        
        db3 = db2 - direkte_kosten
        
        # =================================================================
        # INDIREKTE KOSTEN
        # = Alle 4xxxxx MINUS:
        #   - Variable Kosten (bereits abgezogen, nur Stelle5 != 0)
        #   - Direkte Kosten (415xxx ohne 4151xx)
        # Einfacher: Alle 4xxxxx mit Stelle5 = '0' (indirekte Kostenstelle)
        #            PLUS Rest der Konten die nicht variabel/direkt sind
        # =================================================================
        indirekte_kosten = db.execute(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value/100.0 
                                     ELSE -posted_value/100.0 END), 0)
            FROM loco_journal_accountings
            WHERE accounting_date BETWEEN ? AND ?
              AND nominal_account_number BETWEEN 400000 AND 499999
              AND nominal_account_number NOT BETWEEN 415000 AND 415999  -- direkte Löhne
              AND NOT (substr(nominal_account_number, 5, 1) != '0' 
                       AND (nominal_account_number BETWEEN 435000 AND 435999
                            OR nominal_account_number BETWEEN 455000 AND 457999
                            OR nominal_account_number BETWEEN 487000 AND 488999
                            OR nominal_account_number BETWEEN 491000 AND 497999)
                       AND nominal_account_number NOT BETWEEN 498000 AND 498999)
              {firma_filter}
        """, (von, bis)).fetchone()[0] or 0
        
        betriebsergebnis = db3 - indirekte_kosten
        
        # =================================================================
        # NEUTRALES ERGEBNIS (Sonstige Erträge/Aufwendungen - 5xxxxx, 6xxxxx)
        # =================================================================
        neutrales_ergebnis = db.execute(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value/100.0 
                                     ELSE -posted_value/100.0 END), 0)
            FROM loco_journal_accountings
            WHERE accounting_date BETWEEN ? AND ?
              AND (nominal_account_number BETWEEN 500000 AND 599999
                   OR nominal_account_number BETWEEN 600000 AND 699999)
              {firma_filter}
        """, (von, bis)).fetchone()[0] or 0
        
        unternehmensergebnis = betriebsergebnis + neutrales_ergebnis
        
        # =================================================================
        # BEREICHE (für DB1 Aufschlüsselung)
        # =================================================================
        bereiche_sql = f"""
            SELECT 
                CASE 
                    WHEN nominal_account_number BETWEEN 810000 AND 819999 THEN '1-NW'
                    WHEN nominal_account_number BETWEEN 820000 AND 829999 THEN '2-GW'
                    WHEN nominal_account_number BETWEEN 830000 AND 839999 THEN '3-Teile'
                    WHEN nominal_account_number BETWEEN 840000 AND 849999 THEN '4-Lohn'
                    WHEN nominal_account_number BETWEEN 860000 AND 869999 THEN '5-Sonstige'
                END as bereich,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value/100.0 ELSE -posted_value/100.0 END) as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date BETWEEN ? AND ?
              AND (nominal_account_number BETWEEN 810000 AND 849999 
                   OR nominal_account_number BETWEEN 860000 AND 869999)
              {firma_filter}
            GROUP BY bereich
        """
        
        einsatz_bereiche_sql = f"""
            SELECT 
                CASE 
                    WHEN nominal_account_number BETWEEN 710000 AND 719999 THEN '1-NW'
                    WHEN nominal_account_number BETWEEN 720000 AND 729999 THEN '2-GW'
                    WHEN nominal_account_number BETWEEN 730000 AND 739999 THEN '3-Teile'
                    WHEN nominal_account_number BETWEEN 740000 AND 749999 THEN '4-Lohn'
                    WHEN nominal_account_number BETWEEN 760000 AND 769999 THEN '5-Sonstige'
                END as bereich,
                SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value/100.0 ELSE -posted_value/100.0 END) as einsatz
            FROM loco_journal_accountings
            WHERE accounting_date BETWEEN ? AND ?
              AND (nominal_account_number BETWEEN 710000 AND 749999 
                   OR nominal_account_number BETWEEN 760000 AND 769999)
              {firma_filter}
            GROUP BY bereich
        """
        
        umsatz_rows = db.execute(bereiche_sql, (von, bis)).fetchall()
        einsatz_rows = db.execute(einsatz_bereiche_sql, (von, bis)).fetchall()
        
        umsatz_dict = {row['bereich']: row['umsatz'] for row in umsatz_rows if row['bereich']}
        einsatz_dict = {row['bereich']: row['einsatz'] for row in einsatz_rows if row['bereich']}
        
        bereiche = {}
        for b in ['1-NW', '2-GW', '3-Teile', '4-Lohn', '5-Sonstige']:
            u = umsatz_dict.get(b, 0) or 0
            e = einsatz_dict.get(b, 0) or 0
            bereiche[b] = {
                'umsatz': round(u, 2),
                'einsatz': round(e, 2),
                'db1': round(u - e, 2)
            }
        
        # Margen berechnen
        marge_db1 = (db1 / umsatz * 100) if umsatz > 0 else 0
        marge_db2 = (db2 / umsatz * 100) if umsatz > 0 else 0
        marge_db3 = (db3 / umsatz * 100) if umsatz > 0 else 0
        marge_betriebserg = (betriebsergebnis / umsatz * 100) if umsatz > 0 else 0
        marge_unternergebnis = (unternehmensergebnis / umsatz * 100) if umsatz > 0 else 0
        
        db.close()
        
        return jsonify({
            'success': True,
            'filter': {'firma': firma, 'von': von, 'bis': bis},
            'umsatz': round(umsatz, 2),
            'einsatz': round(einsatz, 2),
            'db1': round(db1, 2),
            'marge_db1': round(marge_db1, 1),
            'variable_kosten': variable_kosten,
            'variable_kosten_summe': round(variable_kosten_summe, 2),
            'db2': round(db2, 2),
            'marge_db2': round(marge_db2, 1),
            'direkte_kosten_summe': round(direkte_kosten, 2),
            'db3': round(db3, 2),
            'marge_db3': round(marge_db3, 1),
            'indirekte_kosten_summe': round(indirekte_kosten, 2),
            'betriebsergebnis': round(betriebsergebnis, 2),
            'marge_betriebserg': round(marge_betriebserg, 1),
            'neutrales_ergebnis': round(neutrales_ergebnis, 2),
            'unternehmensergebnis': round(unternehmensergebnis, 2),
            'marge_unternergebnis': round(marge_unternergebnis, 1),
            'bereiche': bereiche,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
