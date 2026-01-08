"""
Stundensatz-Kalkulation API
============================
TAG 169: API für Stundensatz-Kalkulation mit BWA-Daten
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required
from datetime import date
from api.db_utils import db_session, locosoft_session
from api.db_connection import convert_placeholders

try:
    from api.controlling_api import build_firma_standort_filter
except ImportError:
    def build_firma_standort_filter(firma, standort):
        if standort == 1:
            umsatz = "AND ((branch_number = 1 AND subsidiary_to_company_ref = 1) OR (branch_number = 2 AND subsidiary_to_company_ref = 2))"
            einsatz = "AND ((SUBSTRING(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1) OR (SUBSTRING(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 2))"
            kosten = einsatz
        elif standort == 2:
            umsatz = "AND subsidiary_to_company_ref = 2"
            einsatz = "AND subsidiary_to_company_ref = 2"
            kosten = einsatz
        elif standort == 3:
            umsatz = "AND branch_number = 3 AND subsidiary_to_company_ref = 1"
            einsatz = "AND SUBSTRING(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
            kosten = einsatz
        else:
            umsatz = einsatz = kosten = ""
        return umsatz, einsatz, kosten, f"Standort {standort}"

stundensatz_api = Blueprint('stundensatz_api', __name__)


@stundensatz_api.route('/api/stundensatz/kalkulation', methods=['GET'])
@login_required
def get_stundensatz_kalkulation():
    """
    Lädt Stundensatz-Kalkulation für alle Standorte.
    
    Query-Params:
        - geschaeftsjahr: z.B. '2024/25' (optional, default: Vorjahr)
        - standort: 1, 2, oder 3 (optional, default: alle)
    """
    geschaeftsjahr = request.args.get('geschaeftsjahr')
    standort_param = request.args.get('standort', type=int)
    
    # Geschäftsjahr bestimmen
    if geschaeftsjahr:
        try:
            vj_gj_start = int(geschaeftsjahr.split('/')[0])
        except:
            vj_gj_start = date.today().year - 1
    else:
        # Vorjahr als Default
        heute = date.today()
        if heute.month >= 9:
            vj_gj_start = heute.year - 1
        else:
            vj_gj_start = heute.year - 2
    
    vj_von = f"{vj_gj_start}-09-01"
    vj_bis = f"{vj_gj_start + 1}-09-01"
    
    result = {
        'geschaeftsjahr': f"{vj_gj_start}/{str(vj_gj_start + 1)[2:]}",
        'von': vj_von,
        'bis': vj_bis,
        'standorte': {}
    }
    
    standorte = [1, 2, 3] if not standort_param else [standort_param]
    standort_namen = {1: 'Deggendorf', 2: 'Hyundai DEG', 3: 'Landau'}
    
    for standort in standorte:
        standort_data = lade_bwa_werkstatt_daten(standort, vj_von, vj_bis)
        result['standorte'][standort] = {
            'name': standort_namen[standort],
            **standort_data
        }
    
    return jsonify(result)


def lade_bwa_werkstatt_daten(standort: int, vj_von: str, vj_bis: str):
    """
    Lädt BWA-Daten für Werkstatt aus loco_journal_accountings.
    """
    result = {
        'umsatz': 0,
        'einsatz': 0,
        'db1': 0,
        'variable_kosten': 0,
        'direkte_kosten': 0,
        'db2': 0,
        'stunden_verkauft': 0,
        'stundensatz': 0,
        'kosten_pro_stunde': 0,
        'db1_pro_stunde': 0,
        'db2_pro_stunde': 0
    }
    
    firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, _ = build_firma_standort_filter('1', str(standort))
    
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            
            # 1. Umsatz (840000-849999)
            cursor.execute(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as umsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 840000 AND 849999
                  {firma_filter_umsatz}
            """, (vj_von, vj_bis))
            row = cursor.fetchone()
            result['umsatz'] = float(row[0] or 0) if row else 0
            
            # 2. Einsatz (740000-749999)
            cursor.execute(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as einsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 740000 AND 749999
                  {firma_filter_einsatz}
            """, (vj_von, vj_bis))
            row = cursor.fetchone()
            result['einsatz'] = float(row[0] or 0) if row else 0
            
            # 3. DB1 = Umsatz - Einsatz
            result['db1'] = result['umsatz'] - result['einsatz']
            
            # 4. Variable Kosten (415xxx, 435xxx, 455xxx-456xxx, 487xxx, 491xxx-497xxx mit KST 3)
            variable_konten = [
                (415000, 415999),
                (435000, 435999),
                (455000, 456999),
                (487000, 487999),
                (491000, 497999),
            ]
            
            variable_kosten_sum = 0
            for von, bis in variable_konten:
                cursor.execute(f"""
                    SELECT COALESCE(SUM(
                        CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                    )/100.0, 0) as kosten
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN %s AND %s
                      AND CAST(SUBSTRING(CAST(nominal_account_number AS TEXT), 5, 1) AS INTEGER) = 3
                      {firma_filter_kosten}
                """, (vj_von, vj_bis, von, bis))
                row = cursor.fetchone()
                variable_kosten_sum += float(row[0] or 0) if row else 0
            
            result['variable_kosten'] = variable_kosten_sum
            
            # 5. Direkte Kosten (4xxxxx mit KST 3, ohne Variable)
            cursor.execute(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as kosten
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 400000 AND 499999
                  AND CAST(SUBSTRING(CAST(nominal_account_number AS TEXT), 5, 1) AS INTEGER) = 3
                  AND NOT (
                      (nominal_account_number BETWEEN 415000 AND 415999) OR
                      (nominal_account_number BETWEEN 435000 AND 435999) OR
                      (nominal_account_number BETWEEN 455000 AND 456999) OR
                      (nominal_account_number BETWEEN 487000 AND 487999) OR
                      (nominal_account_number BETWEEN 491000 AND 497999)
                  )
                  {firma_filter_kosten}
            """, (vj_von, vj_bis))
            row = cursor.fetchone()
            result['direkte_kosten'] = float(row[0] or 0) if row else 0
            
            # 6. DB2 = DB1 - Variable Kosten - Direkte Kosten
            result['db2'] = result['db1'] - result['variable_kosten'] - result['direkte_kosten']
            
            # 7. Stunden verkauft (aus labours, AW zu Stunden) - aus Locosoft!
            with locosoft_session() as conn_loco:
                cursor_loco = conn_loco.cursor()
                cursor_loco.execute(f"""
                    SELECT COALESCE(SUM(l.time_units), 0) as aw_verkauft
                    FROM labours l
                    JOIN invoices i ON l.invoice_number = i.invoice_number 
                        AND l.invoice_type = i.invoice_type
                    JOIN orders o ON l.order_number = o.number
                    WHERE i.invoice_date >= %s AND i.invoice_date < %s
                      AND l.is_invoiced = true
                      AND i.is_canceled = false
                      AND o.subsidiary = {standort if standort in [1, 2] else 1}
                """, (vj_von, vj_bis))
                row = cursor_loco.fetchone()
                aw_verkauft = float(row[0] or 0) if row else 0
                result['stunden_verkauft'] = aw_verkauft / 6.0  # AW zu Stunden
            
            # 8. Stundensatz = Umsatz / Stunden
            if result['stunden_verkauft'] > 0:
                result['stundensatz'] = result['umsatz'] / result['stunden_verkauft']
                result['kosten_pro_stunde'] = (result['variable_kosten'] + result['direkte_kosten']) / result['stunden_verkauft']
                result['db1_pro_stunde'] = result['db1'] / result['stunden_verkauft']
                result['db2_pro_stunde'] = result['db2'] / result['stunden_verkauft']
            
    except Exception as e:
        print(f"Fehler beim Laden der BWA-Daten: {e}")
        import traceback
        traceback.print_exc()
    
    return result

