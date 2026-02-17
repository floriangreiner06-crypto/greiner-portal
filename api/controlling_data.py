"""
TEK Datenmodul - Wiederverwendbare Geschäftslogik
==================================================
Kapselt die TEK-Datenabfrage-Logik für Nutzung in:
- Web-UI (controlling_routes.py)
- E-Mail-Reports (send_daily_tek.py)
- PDF (pdf_generator.py)

TAG146: Saubere Trennung von Daten und Präsentation
SSOT: Breakeven/Prognose (berechne_breakeven_prognose) – eine Logik für Portal und PDF.

Author: Claude AI + Florian Greiner
Date: 2025-12-30
"""

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from api.db_utils import db_session, row_to_dict, get_guv_filter
from api.db_connection import convert_placeholders, get_db_type
from utils.werktage import get_werktage_monat


def get_tek_data(monat=None, jahr=None, firma='0', standort='0', modus='teil', umlage='mit'):
    """
    Holt TEK-Daten aus der Locosoft-Datenbank

    Args:
        monat: Monat (1-12), default: aktueller Monat
        jahr: Jahr (YYYY), default: aktuelles Jahr
        firma: '0'=Alle, '1'=Stellantis, '2'=Hyundai
        standort: '0'=Alle, '1'=Deggendorf, '2'=Landau (nur bei firma='1')
        modus: 'teil'=Teilkosten/DB1, 'voll'=Vollkosten/Breakeven
        umlage: 'mit'=Standard, 'ohne'=Umlage-Konten ausschließen

    Returns:
        dict mit Keys:
        - bereiche: Liste von Bereichen mit umsatz, einsatz, db1, marge
        - gesamt: Gesamt-KPIs (db1, marge, prognose, breakeven, breakeven_diff)
        - vm: Vormonat-Vergleich (db1, marge)
        - vj: Vorjahr-Vergleich (db1, marge - NUR bis zum gleichen Tag!)
    """
    heute = date.today()
    if not monat:
        monat = heute.month
    if not jahr:
        jahr = heute.year

    von = f"{jahr}-{monat:02d}-01"
    bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"

    # Filter bauen (TAG157: firma_filter_einsatz für Einsatz = 6. Ziffer bei Stellantis)
    firma_filter_umsatz = ""   # Für Umsatz: branch_number
    firma_filter_kosten = ""   # Für Kosten: 6. Ziffer der Kontonummer
    firma_filter_einsatz = ""  # Für Einsatz: 6. Ziffer (SSOT wie Portal)

    if firma == '1':
        # Stellantis (Autohaus Greiner)
        firma_filter_umsatz = "AND subsidiary_to_company_ref = 1"
        firma_filter_kosten = "AND subsidiary_to_company_ref = 1"
        firma_filter_einsatz = "AND subsidiary_to_company_ref = 1"
        if standort == '1':
            # Deggendorf
            firma_filter_umsatz += " AND branch_number = 1"
            firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
            firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
        elif standort == '2':
            # Landau
            firma_filter_umsatz += " AND branch_number = 3"
            firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
            firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
    elif firma == '2':
        # Hyundai
        firma_filter_umsatz = "AND subsidiary_to_company_ref = 2"
        firma_filter_kosten = "AND subsidiary_to_company_ref = 2"
        firma_filter_einsatz = "AND subsidiary_to_company_ref = 2"

    # Umlage-Filter (TAG146: Option zum Ausschalten interner Umlagen)
    umlage_erloese_filter = ""
    umlage_kosten_filter = ""
    if umlage == 'ohne':
        umlage_konten_str = '817051,827051,837051,847051'  # Umlage-Erlöse
        umlage_erloese_filter = f"AND nominal_account_number NOT IN ({umlage_konten_str})"
        umlage_kosten_filter = """AND NOT (
            debit_or_credit = 'H'
            AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0'
            AND (posting_text LIKE '%Kostenumlage%' OR posting_text LIKE '%kostenumlage%')
        )"""

    # G&V-Abschluss wie in BWA. 743002 (EW Fremdleistungen Landau) einschließen – Globalcube schließt es fälschlich aus (Mapping nicht angepasst).
    guv_filter = get_guv_filter()

    with db_session() as conn:
        cursor = conn.cursor()

        # =================================================================
        # BEREICHE: Umsatz, Einsatz, DB1, Marge
        # =================================================================

        # Umsatz pro Bereich (mit G&V-Filter wie BWA)
        # Clean Park 847301 aus 4-Lohn ausgliedern – eigene KST, wird am Ende des Berichts separat geführt
        cursor.execute(f"""
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
            WHERE accounting_date >= %s AND accounting_date < %s
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
              {firma_filter_umsatz}
              {umlage_erloese_filter}
              {guv_filter}
            GROUP BY bereich
        """, (von, bis))
        umsatz_dict = {r['bereich']: float(r['umsatz'] or 0) for r in cursor.fetchall()}

        # Einsatz pro Bereich (G&V-Filter; Clean Park 747301 aus 4-Lohn ausgliedern; 743002 einschließen)
        cursor.execute(f"""
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
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 700000 AND 799999
              {firma_filter_einsatz}
              {guv_filter}
            GROUP BY bereich
        """, (von, bis))
        einsatz_dict = {r['bereich']: float(r['einsatz'] or 0) for r in cursor.fetchall()}

        # Bereiche zusammenführen
        bereiche = []
        for bkey in ['1-NW', '2-GW', '3-Teile', '4-Lohn', '5-Sonst']:
            umsatz = umsatz_dict.get(bkey, 0)
            einsatz = einsatz_dict.get(bkey, 0)
            db1 = umsatz - einsatz
            marge = (db1 / umsatz * 100) if umsatz > 0 else 0
            bereiche.append({
                'id': bkey,
                'umsatz': round(umsatz, 2),
                'einsatz': round(einsatz, 2),
                'db1': round(db1, 2),
                'marge': round(marge, 1)
            })

        # TAG 219: 4-Lohn im laufenden Monat – kalkulatorischer Einsatz (Method B, 6-Monats-Quote)
        # Im laufenden Monat ist FIBU-Einsatz 74xxxx oft noch nicht voll gebucht → Marge würde verfälscht.
        # Einsatz kalk = Umsatz_aktuell × (Einsatz_6M / Umsatz_6M); DB1/Marge daraus.
        heute_ref = heute if isinstance(heute, date) else date.today()
        ist_laufender_monat = (jahr == heute_ref.year and monat == heute_ref.month)
        if ist_laufender_monat:
            werkstatt_item = next((b for b in bereiche if b['id'] == '4-Lohn'), None)
            werkstatt_umsatz = werkstatt_item['umsatz'] if werkstatt_item else 0
            if werkstatt_item and werkstatt_umsatz > 0:
                bis_6m = date(jahr, monat, 1)
                von_6m = bis_6m
                for _ in range(6):
                    von_6m = (von_6m - timedelta(days=1)).replace(day=1)
                von_6m_str = von_6m.strftime('%Y-%m-%d')
                bis_6m_str = bis_6m.strftime('%Y-%m-%d')
                cursor.execute(f"""
                    SELECT COALESCE(SUM(CASE WHEN nominal_account_number BETWEEN 840000 AND 849999 AND nominal_account_number != 847301 AND debit_or_credit = 'H' THEN posted_value
                               WHEN nominal_account_number BETWEEN 840000 AND 849999 AND nominal_account_number != 847301 AND debit_or_credit = 'S' THEN -posted_value ELSE 0 END) / 100.0, 0) as umsatz
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                    {firma_filter_umsatz}
                    {guv_filter}
                """, (von_6m_str, bis_6m_str))
                row_umsatz = cursor.fetchone()
                umsatz_6m = float(row_to_dict(row_umsatz).get('umsatz', 0) or 0) if row_umsatz else 0
                cursor.execute(f"""
                    SELECT COALESCE(SUM(CASE WHEN nominal_account_number BETWEEN 740000 AND 749999 AND nominal_account_number != 747301 AND debit_or_credit = 'S' THEN posted_value
                               WHEN nominal_account_number BETWEEN 740000 AND 749999 AND nominal_account_number != 747301 AND debit_or_credit = 'H' THEN -posted_value ELSE 0 END) / 100.0, 0) as einsatz
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                    {firma_filter_umsatz}
                    {guv_filter}
                """, (von_6m_str, bis_6m_str))
                row_einsatz = cursor.fetchone()
                einsatz_6m = float(row_to_dict(row_einsatz).get('einsatz', 0) or 0) if row_einsatz else 0
                einsatz_quote_6m = (einsatz_6m / umsatz_6m) if umsatz_6m > 0 else 0.36
                gesamt_einsatz = round(werkstatt_umsatz * einsatz_quote_6m, 2)
                werkstatt_db1 = werkstatt_umsatz - gesamt_einsatz
                werkstatt_marge = round((werkstatt_db1 / werkstatt_umsatz * 100), 1)
                werkstatt_item['einsatz'] = gesamt_einsatz
                werkstatt_item['db1'] = round(werkstatt_db1, 2)
                werkstatt_item['marge'] = werkstatt_marge
                werkstatt_item['einsatz_kalk'] = gesamt_einsatz
                werkstatt_item['db1_kalk'] = round(werkstatt_db1, 2)
                werkstatt_item['marge_kalk'] = werkstatt_marge
                werkstatt_item['hinweis'] = f"Einsatz kalk. (6M-Quote {round(einsatz_quote_6m*100)}%): {round(gesamt_einsatz/1000)}k"

        # Gesamt: Bereiche (4-Lohn ohne Clean Park) + Clean Park 847301/747301 + 9-Andere (wie Portal)
        # Portal (controlling_routes) addiert 6-8932 und 9-Andere zu totals; hier nur 9-Andere (8932 landet in 9-Andere)
        total_umsatz = sum(b['umsatz'] for b in bereiche)
        total_einsatz = sum(b['einsatz'] for b in bereiche)
        total_umsatz += float(umsatz_dict.get('9-Andere', 0) or 0)
        total_einsatz += float(einsatz_dict.get('9-Andere', 0) or 0)
        cursor.execute(f"""
            SELECT
                COALESCE(SUM(CASE WHEN nominal_account_number = 847301 AND debit_or_credit = 'H' THEN posted_value WHEN nominal_account_number = 847301 AND debit_or_credit = 'S' THEN -posted_value ELSE 0 END) / 100.0, 0) as cp_umsatz,
                COALESCE(SUM(CASE WHEN nominal_account_number = 747301 AND debit_or_credit = 'S' THEN posted_value WHEN nominal_account_number = 747301 AND debit_or_credit = 'H' THEN -posted_value ELSE 0 END) / 100.0, 0) as cp_einsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND (nominal_account_number = 847301 OR nominal_account_number = 747301)
              {firma_filter_umsatz}
              {guv_filter}
        """, (von, bis))
        cp_row = cursor.fetchone()
        cp_umsatz = float(cp_row['cp_umsatz'] or 0) if cp_row else 0
        cp_einsatz = float(cp_row['cp_einsatz'] or 0) if cp_row else 0
        total_umsatz += cp_umsatz
        total_einsatz += cp_einsatz
        total_db1 = total_umsatz - total_einsatz
        total_marge = (total_db1 / total_umsatz * 100) if total_umsatz > 0 else 0

        # =================================================================
        # VORMONAT-VERGLEICH (kompletter Vormonat)
        # =================================================================

        vm_monat, vm_jahr = (12, jahr - 1) if monat == 1 else (monat - 1, jahr)
        vm_von = f"{vm_jahr}-{vm_monat:02d}-01"
        vm_bis = f"{vm_jahr}-{vm_monat+1:02d}-01" if vm_monat < 12 else f"{vm_jahr+1}-01-01"

        cursor.execute(f"""
            SELECT
                COALESCE(SUM(CASE WHEN debit_or_credit = 'H' AND nominal_account_number BETWEEN 800000 AND 889999
                             THEN posted_value ELSE 0 END) / 100.0, 0) as umsatz,
                COALESCE(SUM(CASE WHEN debit_or_credit = 'S' AND nominal_account_number BETWEEN 700000 AND 799999
                             THEN posted_value ELSE 0 END) / 100.0, 0) as einsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              {firma_filter_umsatz}
              {umlage_erloese_filter}
              {guv_filter}
        """, (vm_von, vm_bis))
        vm_row = cursor.fetchone()
        vm_umsatz = float(vm_row['umsatz'] or 0)
        vm_einsatz = float(vm_row['einsatz'] or 0)
        vm_db1 = vm_umsatz - vm_einsatz
        vm_marge = (vm_db1 / vm_umsatz * 100) if vm_umsatz > 0 else 0

        # =================================================================
        # VORJAHR-VERGLEICH (TAG146 FIX: NUR bis zum gleichen Tag!)
        # =================================================================

        vj_jahr = jahr - 1
        # WICHTIG: Gleicher Zeitraum wie aktuell (z.B. 1. Dez bis 30. Dez)
        # Nicht den GANZEN Monat, sondern nur bis heute!
        vj_von = f"{vj_jahr}-{monat:02d}-01"
        if monat == heute.month and jahr == heute.year:
            # Aktueller Monat: Vergleiche bis zum gleichen Tag
            # +1 Tag weil SQL WHERE < (nicht <=) nutzt
            vj_bis = f"{vj_jahr}-{monat:02d}-{heute.day+1:02d}"
        else:
            # Vergangener Monat: Kompletter Monat
            vj_bis = f"{vj_jahr}-{monat+1:02d}-01" if monat < 12 else f"{vj_jahr+1}-01-01"

        cursor.execute(f"""
            SELECT
                COALESCE(SUM(CASE WHEN debit_or_credit = 'H' AND nominal_account_number BETWEEN 800000 AND 889999
                             THEN posted_value ELSE 0 END) / 100.0, 0) as umsatz,
                COALESCE(SUM(CASE WHEN debit_or_credit = 'S' AND nominal_account_number BETWEEN 700000 AND 799999
                             THEN posted_value ELSE 0 END) / 100.0, 0) as einsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              {firma_filter_umsatz}
              {umlage_erloese_filter}
              {guv_filter}
        """, (vj_von, vj_bis))
        vj_row = cursor.fetchone()
        vj_umsatz = float(vj_row['umsatz'] or 0)
        vj_einsatz = float(vj_row['einsatz'] or 0)
        vj_db1 = vj_umsatz - vj_einsatz
        vj_marge = (vj_db1 / vj_umsatz * 100) if vj_umsatz > 0 else 0

    # SSOT: Breakeven/Prognose wie Portal (BWA-Kosten, echte Werktage)
    prognose_result = berechne_breakeven_prognose(
        monat, jahr, total_db1,
        firma_filter_umsatz, firma_filter_kosten,
        anteilige_kosten=False,
        firma_filter_einsatz=firma_filter_einsatz
    )
    prognose = round((prognose_result.get('hochrechnung_db1') or 0), 2)
    breakeven = round(prognose_result.get('breakeven_schwelle') or 0, 2)
    werktage = prognose_result.get('werktage')  # Für PDF/E-Mail: vergangen, verbleibend, gesamt (Datenstichtag)

    # Rückgabe im einheitlichen Format
    return {
        'bereiche': bereiche,
        'gesamt': {
            'umsatz': round(total_umsatz, 2),
            'einsatz': round(total_einsatz, 2),
            'db1': round(total_db1, 2),
            'marge': round(total_marge, 1),
            'prognose': prognose,
            'breakeven': breakeven,
            'breakeven_diff': round(total_db1 - breakeven, 2),
            'werktage': werktage,
        },
        'vm': {  # Vormonat
            'db1': round(vm_db1, 2),
            'marge': round(vm_marge, 1)
        },
        'vj': {  # Vorjahr (NUR bis zum gleichen Tag!)
            'db1': round(vj_db1, 2),
            'marge': round(vj_marge, 1)
        }
    }


# =============================================================================
# BREAKEVEN-PROGNOSE (SSOT – eine Logik für Portal und PDF)
# =============================================================================

def berechne_breakeven_prognose_standort(monat: int, jahr: int, aktueller_db1: float,
                                         firma_filter_umsatz: str, firma_filter_kosten: str,
                                         firma_filter_einsatz: str = None) -> dict:
    """
    Berechnet Breakeven-Prognose für einen spezifischen Standort.
    Kosten nach 6. Ziffer der Kontonummer; Umsatz/Einsatz nach branch_number.
    """
    if firma_filter_einsatz is None:
        firma_filter_einsatz = firma_filter_umsatz

    von = f"{jahr}-{monat:02d}-01"
    bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"
    heute = date.today()
    now = datetime.now()
    stichtag = heute if now.hour >= 19 else (heute - timedelta(days=1))
    vor_3_monaten = (heute - relativedelta(months=3)).isoformat()
    heute_str = heute.isoformat()

    with db_session() as conn:
        cursor = conn.cursor()
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
        kosten_pro_monat = (variable_3m + direkte_3m) / 3

        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
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
              {firma_filter_einsatz}
        """), (von, bis))
        row = cursor.fetchone()
        operativ_einsatz = float(row_to_dict(row).get('einsatz') or 0) if row else 0
        operativ_db1 = operativ_umsatz - operativ_einsatz

        cursor.execute(convert_placeholders(f"""
            SELECT COUNT(DISTINCT accounting_date) as tage
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 700000 AND 899999
              {firma_filter_einsatz}
        """), (von, bis))
        row = cursor.fetchone()
        tage_mit_daten = int(row_to_dict(row).get('tage') or 0) if row else 0

    werktage = get_werktage_monat(jahr, monat, stichtag=stichtag)
    werktage_gesamt = werktage['gesamt']
    werktage_vergangen = werktage['vergangen']
    if tage_mit_daten >= 5:
        # Wie GlobalCube: (DB1 / vergangene Werktage) × Werktage gesamt
        divisor = werktage_vergangen if werktage_vergangen > 0 else max(tage_mit_daten, 1)
        hochrechnung_db1 = (aktueller_db1 / divisor) * werktage_gesamt
    else:
        hochrechnung_db1 = aktueller_db1

    if aktueller_db1 >= kosten_pro_monat:
        status, ampel = 'positiv', 'gruen'
    elif hochrechnung_db1 >= kosten_pro_monat:
        status, ampel = 'auf_kurs', 'gelb'
    else:
        status, ampel = 'kritisch', 'rot'

    return {
        'kosten_3m_schnitt': {'variable': round(variable_3m / 3, 2), 'direkte': round(direkte_3m / 3, 2), 'gesamt': round(kosten_pro_monat, 2)},
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
                               anteilige_kosten: bool = True, firma_filter_einsatz: str = None) -> dict:
    """
    SSOT: Breakeven-Prognose (BWA-Kosten, echte Werktage). Nutzung: Portal + get_tek_data (PDF/E-Mail).
    Datenstichtag: Vor 19:00 Uhr zählt „vergangen“ nur bis gestern (Locosoft liefert abends).
    """
    if firma_filter_kosten is None:
        firma_filter_kosten = firma_filter_umsatz
    if firma_filter_einsatz is None:
        firma_filter_einsatz = firma_filter_umsatz

    von = f"{jahr}-{monat:02d}-01"
    bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"
    heute = date.today()
    # TEK-Datenstichtag: Locosoft kommt abends. Vor 19:00 = Stichtag gestern → 9 verbleibende WT morgens.
    now = datetime.now()
    stichtag = heute if now.hour >= 19 else (heute - timedelta(days=1))
    vor_3_monaten = (heute - relativedelta(months=3)).isoformat()
    heute_str = heute.isoformat()

    umsatz_anteil = 1.0
    umsatz_firma = 0
    umsatz_gesamt = 0
    if anteilige_kosten:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number BETWEEN 800000 AND 889999
                  {firma_filter_umsatz}
            """), (vor_3_monaten, heute_str))
            row = cursor.fetchone()
            umsatz_firma = float(row_to_dict(row).get('umsatz') or 0) if row else 0
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
        variable_3m = variable_3m_gesamt * umsatz_anteil
        direkte_3m = direkte_3m_gesamt * umsatz_anteil
        indirekte_3m = indirekte_3m_gesamt * umsatz_anteil
        kosten_pro_monat = (variable_3m + direkte_3m + indirekte_3m) / 3

        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
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
              {firma_filter_einsatz}
        """), (von, bis))
        row = cursor.fetchone()
        operativ_einsatz = float(row_to_dict(row).get('einsatz') or 0) if row else 0
        operativ_db1 = operativ_umsatz - operativ_einsatz

        cursor.execute(convert_placeholders(f"""
            SELECT COUNT(DISTINCT accounting_date) as tage
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 700000 AND 899999
              {firma_filter_einsatz}
        """), (von, bis))
        row = cursor.fetchone()
        tage_mit_daten = int(row_to_dict(row).get('tage') or 0) if row else 0

    werktage = get_werktage_monat(jahr, monat, stichtag=stichtag)
    werktage_gesamt = werktage['gesamt']
    werktage_vergangen = werktage['vergangen']
    tage_im_monat = werktage_gesamt

    hochrechnung_db1 = None
    prognose_methode = None
    db1_3m_schnitt = None
    if tage_mit_daten < 5:
        vor_3m_start = (datetime.strptime(von, '%Y-%m-%d') - relativedelta(months=3)).strftime('%Y-%m-%d')
        if get_db_type() == 'postgresql':
            monat_expr = "TO_CHAR(accounting_date, 'YYYY-MM')"
        else:
            monat_expr = "strftime('%Y-%m', accounting_date)"
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_placeholders(f"""
                SELECT {monat_expr} as monat,
                    SUM(CASE WHEN nominal_account_number BETWEEN 800000 AND 889999 OR nominal_account_number BETWEEN 893200 AND 893299
                        THEN CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END ELSE 0 END) / 100.0 as umsatz,
                    SUM(CASE WHEN nominal_account_number BETWEEN 700000 AND 799999
                        THEN CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END ELSE 0 END) / 100.0 as einsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  {firma_filter_umsatz}
                GROUP BY {monat_expr}
                ORDER BY monat DESC
                LIMIT 3
            """), (vor_3m_start, von))
            db1_3m_rows = [row_to_dict(r) for r in cursor.fetchall()]
        if db1_3m_rows and len(db1_3m_rows) >= 2:
            db1_werte = [float(row.get('umsatz') or 0) - float(row.get('einsatz') or 0) for row in db1_3m_rows]
            db1_3m_schnitt = sum(db1_werte) / len(db1_werte)
            hochrechnung_db1 = db1_3m_schnitt
            prognose_methode = 'gleitend_3m'
        else:
            prognose_methode = 'keine_daten'
    else:
        # Referenz GlobalCube: Prognose = (DB1 / vergangene Werktage) × Werktage gesamt.
        # Divisor = werktage_vergangen (nicht tage_mit_daten), sonst wird Prognose zu schlecht.
        divisor = werktage_vergangen if werktage_vergangen > 0 else max(tage_mit_daten, 1)
        hochrechnung_db1 = (aktueller_db1 / divisor) * werktage_gesamt
        prognose_methode = 'hochrechnung'

    if aktueller_db1 >= kosten_pro_monat:
        status, ampel = 'positiv', 'gruen'
    elif hochrechnung_db1 and hochrechnung_db1 >= kosten_pro_monat:
        status, ampel = 'auf_kurs', 'gelb'
    else:
        status, ampel = 'kritisch', 'rot'

    db1_pro_werktag = kosten_pro_monat / werktage_gesamt if werktage_gesamt > 0 else 0
    db1_soll_bis_heute = db1_pro_werktag * werktage_vergangen
    UMLAGE_SCHLUESSEL = {'1-NW': 0.40, '2-GW': 0.20, '3-Teile': 0.25, '4-Lohn': 0.15, '5-Sonst': 0.0}
    breakeven_bereiche = {bereich: round(kosten_pro_monat * anteil, 2) for bereich, anteil in UMLAGE_SCHLUESSEL.items()}

    return {
        'kosten_3m_schnitt': {'variable': round(variable_3m / 3, 2), 'direkte': round(direkte_3m / 3, 2), 'indirekte': round(indirekte_3m / 3, 2), 'gesamt': round(kosten_pro_monat, 2)},
        'breakeven_schwelle': round(kosten_pro_monat, 2),
        'aktueller_db1': round(aktueller_db1, 2),
        'operativer_db1': round(operativ_db1, 2),
        'tage_mit_daten': tage_mit_daten,
        'tage_im_monat': tage_im_monat,
        'prognose_methode': prognose_methode,
        'db1_3m_schnitt': round(db1_3m_schnitt, 2) if db1_3m_schnitt else None,
        'hochrechnung_db1': round(hochrechnung_db1, 2) if hochrechnung_db1 else None,
        'hochrechnung_be': round(hochrechnung_db1 - kosten_pro_monat, 2) if hochrechnung_db1 else None,
        'gap': round(aktueller_db1 - kosten_pro_monat, 2),
        'gap_prozent': round((aktueller_db1 - kosten_pro_monat) / kosten_pro_monat * 100, 1) if kosten_pro_monat > 0 else 0,
        'status': status,
        'ampel': ampel,
        'hinweis_umlage': tage_mit_daten < 5,
        'werktage': {'gesamt': werktage_gesamt, 'vergangen': werktage_vergangen, 'verbleibend': werktage['verbleibend'], 'fortschritt_prozent': werktage['fortschritt_prozent']},
        'db1_soll_bis_heute': round(db1_soll_bis_heute, 2),
        'db1_pro_werktag': round(db1_pro_werktag, 2),
        'breakeven_bereiche': breakeven_bereiche,
        'umlage_schluessel': {k: round(v * 100, 0) for k, v in UMLAGE_SCHLUESSEL.items()},
        'kostenverteilung': {'anteilig': anteilige_kosten, 'umsatz_anteil': round(umsatz_anteil * 100, 1), 'umsatz_firma_3m': round(umsatz_firma, 2), 'umsatz_gesamt_3m': round(umsatz_gesamt, 2), 'kosten_gesamt_3m': round(kosten_3m_gesamt / 3, 2)},
    }
