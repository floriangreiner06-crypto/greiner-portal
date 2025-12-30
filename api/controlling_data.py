"""
TEK Datenmodul - Wiederverwendbare Geschäftslogik
==================================================
Kapselt die TEK-Datenabfrage-Logik für Nutzung in:
- Web-UI (controlling_routes.py)
- E-Mail-Reports (send_daily_tek.py)
- Andere Scripts

TAG146: Saubere Trennung von Daten und Präsentation
Garantiert 100% Konsistenz zwischen Web-UI und Reports!

Author: Claude AI + Florian Greiner
Date: 2025-12-30
"""

from datetime import date, timedelta
from api.db_utils import db_session, row_to_dict


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

    # Filter bauen
    firma_filter_umsatz = ""   # Für Umsatz/Einsatz: branch_number
    firma_filter_kosten = ""   # Für Kosten: letzte Ziffer der Kontonummer

    if firma == '1':
        # Stellantis (Autohaus Greiner)
        firma_filter_umsatz = "AND subsidiary_to_company_ref = 1"
        firma_filter_kosten = "AND subsidiary_to_company_ref = 1"
        if standort == '1':
            # Deggendorf
            firma_filter_umsatz += " AND branch_number = 1"
            firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
        elif standort == '2':
            # Landau
            firma_filter_umsatz += " AND branch_number = 3"
            firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
    elif firma == '2':
        # Hyundai
        firma_filter_umsatz = "AND subsidiary_to_company_ref = 2"
        firma_filter_kosten = "AND subsidiary_to_company_ref = 2"

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

    with db_session() as conn:
        cursor = conn.cursor()

        # =================================================================
        # BEREICHE: Umsatz, Einsatz, DB1, Marge
        # =================================================================

        # Umsatz pro Bereich
        cursor.execute(f"""
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
            WHERE accounting_date >= %s AND accounting_date < %s
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
              {firma_filter_umsatz}
              {umlage_erloese_filter}
            GROUP BY bereich
        """, (von, bis))
        umsatz_dict = {r['bereich']: float(r['umsatz'] or 0) for r in cursor.fetchall()}

        # Einsatz pro Bereich
        cursor.execute(f"""
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
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 700000 AND 799999
              {firma_filter_umsatz}
            GROUP BY bereich
        """, (von, bis))
        einsatz_dict = {r['bereich']: float(r['einsatz'] or 0) for r in cursor.fetchall()}

        # TAG147 FIX: Kalkulatorische Lohnkosten ENTFERNT
        # Global Cube rechnet OHNE kalkulatorische Aufschläge
        # Die 40%-Regel war FALSCH und führte zu 25k € Abweichung

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

        # Gesamt
        total_umsatz = sum(b['umsatz'] for b in bereiche)
        total_einsatz = sum(b['einsatz'] for b in bereiche)
        total_db1 = total_umsatz - total_einsatz
        total_marge = (total_db1 / total_umsatz * 100) if total_umsatz > 0 else 0

        # =================================================================
        # BREAKEVEN & PROGNOSE
        # =================================================================

        # Breakeven: 3-Monats-Durchschnitt der Kosten
        cursor.execute(f"""
            SELECT
                COALESCE(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0, 0) as kosten
            FROM loco_journal_accountings
            WHERE accounting_date >= CURRENT_DATE - INTERVAL '3 months'
              AND accounting_date < CURRENT_DATE
              AND nominal_account_number BETWEEN 400000 AND 499999
              {firma_filter_kosten}
              {umlage_kosten_filter}
        """)
        kosten_3m = float(cursor.fetchone()['kosten'] or 0)
        breakeven = kosten_3m / 3

        # Prognose: Hochrechnung auf Basis bisheriger Buchungstage
        cursor.execute(f"""
            SELECT COUNT(DISTINCT accounting_date) as tage
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 700000 AND 899999
              {firma_filter_umsatz}
        """, (von, bis))
        tage_mit_daten = cursor.fetchone()['tage'] or 1
        werktage = 22  # Durchschnittliche Werktage pro Monat
        prognose = (total_db1 / tage_mit_daten) * werktage if tage_mit_daten > 0 else total_db1

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
        """, (vj_von, vj_bis))
        vj_row = cursor.fetchone()
        vj_umsatz = float(vj_row['umsatz'] or 0)
        vj_einsatz = float(vj_row['einsatz'] or 0)
        vj_db1 = vj_umsatz - vj_einsatz
        vj_marge = (vj_db1 / vj_umsatz * 100) if vj_umsatz > 0 else 0

    # Rückgabe im einheitlichen Format
    return {
        'bereiche': bereiche,
        'gesamt': {
            'umsatz': round(total_umsatz, 2),
            'einsatz': round(total_einsatz, 2),
            'db1': round(total_db1, 2),
            'marge': round(total_marge, 1),
            'prognose': round(prognose, 2),
            'breakeven': round(breakeven, 2),
            'breakeven_diff': round(total_db1 - breakeven, 2)
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
