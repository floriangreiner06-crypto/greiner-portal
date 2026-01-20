#!/usr/bin/env python3
"""
Analyse: DB2-Entwicklung für alle Bereiche (Geschäftsjahr 2024/25)

Zweck:
- DB2 = DB1 - Variable Kosten für alle Bereiche
- Bereiche: NW, GW, Teile, Werkstatt, Sonstige
- Monatliche Entwicklung mit Vorjahresvergleich
- Zeitraum: 01.09.2024 - 31.08.2025 (Geschäftsjahr 2024/25)

WICHTIG - KONTEXT:
- Variable Kosten haben komplexe Standort-Filter in der BWA
- Für Gesamtsumme (alle Betriebe) verwenden wir vereinfachte Logik
- 8910xx: Für Hyundai ausschließen, für Deggendorf/Landau einschließen
- Diese Analyse zeigt GESAMTKOSTEN ohne Standort-Verteilung

Ausgabe:
- CSV-Datei mit monatlichen Daten
- Konsolen-Output mit Zusammenfassung

Erstellt: TAG 198
"""

import sys
import os
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List
from calendar import month_name

# Projekt-Root zum Python-Pfad hinzufügen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.db_utils import locosoft_session, get_guv_filter
from psycopg2.extras import RealDictCursor
import csv


def get_geschaeftsjahr_datum(gj_string: str) -> tuple[date, date]:
    """
    Konvertiert Geschäftsjahr-String (z.B. '2024/25') in Datumsbereich.
    
    Geschäftsjahr startet am 1. September:
    - GJ 2024/25 = 01.09.2024 - 31.08.2025
    
    Args:
        gj_string: z.B. '2024/25'
    
    Returns:
        (von_datum, bis_datum)
    """
    gj_start_jahr = int(gj_string.split('/')[0])
    von_datum = date(gj_start_jahr, 9, 1)  # 1. September
    bis_datum = date(gj_start_jahr + 1, 9, 1)  # 1. September nächstes Jahr (exklusiv)
    
    return von_datum, bis_datum


def get_monatliche_zeitraeume(von_datum: date, bis_datum: date) -> List[Dict]:
    """
    Erstellt Liste von monatlichen Zeiträumen für Geschäftsjahr.
    
    Args:
        von_datum: Startdatum (1. September)
        bis_datum: Enddatum (1. September nächstes Jahr)
    
    Returns:
        Liste von Dicts mit 'gj_monat', 'von', 'bis', 'kal_monat', 'kal_jahr'
    """
    monate = []
    current = von_datum
    
    gj_monat = 1
    while current < bis_datum:
        # Nächstes Monatsende
        if current.month == 12:
            next_month = date(current.year + 1, 1, 1)
        else:
            next_month = date(current.year, current.month + 1, 1)
        
        monate.append({
            'gj_monat': gj_monat,
            'gj_monat_name': f"GJ-Monat {gj_monat}",
            'von': current,
            'bis': min(next_month, bis_datum),
            'kal_monat': current.month,
            'kal_jahr': current.year,
            'kal_monat_name': month_name[current.month]
        })
        
        current = next_month
        gj_monat += 1
    
    return monate


def berechne_db1_bereich(
    cursor,
    von_datum: date,
    bis_datum: date,
    bereich: str,
    guv_filter: str
) -> Dict[str, float]:
    """
    Berechnet DB1 für einen Bereich.
    
    DB1 = Umsatz - Einsatz
    
    Args:
        cursor: Datenbank-Cursor
        von_datum: Startdatum
        bis_datum: Enddatum
        bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
        guv_filter: G&V-Filter
    
    Returns:
        dict mit 'umsatz', 'einsatz', 'db1'
    """
    # Umsatz je nach Bereich
    if bereich == 'NW':
        umsatz_query = """
            SELECT COALESCE(SUM(i.total_net), 0) as umsatz
            FROM invoices i
            WHERE i.invoice_date >= %s AND i.invoice_date < %s
              AND i.invoice_type = 7
              AND i.is_canceled = false
        """
    elif bereich == 'GW':
        umsatz_query = """
            SELECT COALESCE(SUM(i.total_net), 0) as umsatz
            FROM invoices i
            WHERE i.invoice_date >= %s AND i.invoice_date < %s
              AND i.invoice_type = 8
              AND i.is_canceled = false
        """
    elif bereich == 'Teile':
        umsatz_query = """
            SELECT COALESCE(SUM(i.part_amount_net), 0) as umsatz
            FROM invoices i
            WHERE i.invoice_date >= %s AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.part_amount_net > 0
        """
    elif bereich == 'Werkstatt':
        umsatz_query = """
            SELECT COALESCE(SUM(i.job_amount_net), 0) as umsatz
            FROM invoices i
            WHERE i.invoice_date >= %s AND i.invoice_date < %s
              AND i.invoice_type IN (2, 4, 5, 6)
              AND i.is_canceled = false
              AND i.job_amount_net > 0
        """
    elif bereich == 'Sonstige':
        umsatz_query = """
            SELECT COALESCE(SUM(i.total_net), 0) as umsatz
            FROM invoices i
            WHERE i.invoice_date >= %s AND i.invoice_date < %s
              AND i.invoice_type NOT IN (2, 4, 5, 6, 7, 8)
              AND i.is_canceled = false
        """
    else:
        return {'umsatz': 0.0, 'einsatz': 0.0, 'db1': 0.0}
    
    cursor.execute(umsatz_query, (von_datum, bis_datum))
    umsatz = float(cursor.fetchone()[0] or 0)
    
    # Einsatz je nach Bereich (aus journal_accountings)
    if bereich == 'NW':
        einsatz_query = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as einsatz
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 817000 AND 817999
              {guv_filter}
        """
    elif bereich == 'GW':
        einsatz_query = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as einsatz
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 827000 AND 827999
              {guv_filter}
        """
    elif bereich == 'Teile':
        einsatz_query = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as einsatz
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 837000 AND 837999
              {guv_filter}
        """
    elif bereich == 'Werkstatt':
        einsatz_query = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as einsatz
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 847000 AND 847999
              {guv_filter}
        """
    elif bereich == 'Sonstige':
        einsatz_query = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as einsatz
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 800000 AND 899999
              AND NOT (nominal_account_number BETWEEN 817000 AND 817999)
              AND NOT (nominal_account_number BETWEEN 827000 AND 827999)
              AND NOT (nominal_account_number BETWEEN 837000 AND 837999)
              AND NOT (nominal_account_number BETWEEN 847000 AND 847999)
              AND NOT (nominal_account_number BETWEEN 890000 AND 899999)
              {guv_filter}
        """
    else:
        einsatz = 0.0
        db1 = umsatz - einsatz
        return {
            'umsatz': round(umsatz, 2),
            'einsatz': round(einsatz, 2),
            'db1': round(db1, 2)
        }
    
    cursor.execute(einsatz_query, (von_datum, bis_datum))
    einsatz = float(cursor.fetchone()[0] or 0)
    
    db1 = umsatz - einsatz
    
    return {
        'umsatz': round(umsatz, 2),
        'einsatz': round(einsatz, 2),
        'db1': round(db1, 2)
    }


def berechne_variable_kosten_bereich(
    cursor,
    von_datum: date,
    bis_datum: date,
    bereich: str,
    guv_filter: str
) -> float:
    """
    Berechnet Variable Kosten für einen Bereich.
    
    Variable Kosten werden nach KST (Kostenstelle) zugeordnet:
    - NW: KST 1 (5. Ziffer = '1')
    - GW: KST 2 (5. Ziffer = '2')
    - Teile: KST 3 (5. Ziffer = '3')
    - Werkstatt: KST 4 (5. Ziffer = '4') - aber nicht in Locosoft, daher 0
    - Sonstige: KST 6,7 (5. Ziffer = '6' oder '7')
    
    WICHTIG:
    - Für Gesamtsumme: Deggendorf (6. Ziffer='1', subsidiary=1) + Landau (6. Ziffer='2', subsidiary=1) + Hyundai (6. Ziffer='1', subsidiary=2, OHNE 8910xx)
    - 8910xx: Für Deggendorf+Landau einschließen, für Hyundai ausschließen
    
    Kontenbereiche:
    - 4151xx: Provisionen
    - 4355xx: Werbekosten
    - 455xxx (KST 1-7): Variable Kosten
    - 487xxx (KST 1-7): Variable Kosten
    - 491xxx-497899: Variable Kosten
    - 8910xx: Optional (nur Deggendorf+Landau)
    
    Args:
        cursor: Datenbank-Cursor
        von_datum: Startdatum
        bis_datum: Enddatum
        bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
        guv_filter: G&V-Filter
    
    Returns:
        Variable Kosten für diesen Bereich als float
    """
    # KST-Mapping
    kst_mapping = {
        'NW': ['1'],
        'GW': ['2'],
        'Teile': ['3'],
        'Werkstatt': [],  # KST 4 nicht in Locosoft
        'Sonstige': ['6', '7']
    }
    
    kst_liste = kst_mapping.get(bereich, [])
    
    if not kst_liste:
        # Werkstatt hat keine Variable Kosten in Locosoft
        return 0.0
    
    # KST-Filter aufbauen
    kst_filter = "AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('" + "','".join(kst_liste) + "')"
    
    # Variable Kosten für Gesamtsumme mit KST-Filter
    # Filter: Deggendorf (6. Ziffer='1', subsidiary=1) + Landau (6. Ziffer='2', subsidiary=1) + Hyundai (6. Ziffer='1', subsidiary=2, OHNE 8910xx)
    query = f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as variable
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR (nominal_account_number BETWEEN 455000 AND 456999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR (nominal_account_number BETWEEN 487000 AND 487099
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            OR nominal_account_number BETWEEN 491000 AND 497899
            OR (nominal_account_number BETWEEN 891000 AND 891099
                AND (
                    (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1)
                    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
                ))
          )
          {kst_filter}
          AND (
            (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1)
            OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
            OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2 
                AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
          )
          {guv_filter}
    """
    
    cursor.execute(query, (von_datum, bis_datum))
    variable = float(cursor.fetchone()[0] or 0)
    
    return round(variable, 2)


def hole_db2_entwicklung(
    gj_string: str,
    vorjahr: bool = False
) -> Dict[str, Any]:
    """
    Holt DB2-Entwicklung für alle Bereiche.
    
    DB2 = DB1 - Variable Kosten
    
    Args:
        gj_string: z.B. '2024/25'
        vorjahr: Wenn True, hole Vorjahres-Daten
    
    Returns:
        dict mit monatlichen Daten für alle Bereiche
    """
    if vorjahr:
        # Vorjahr berechnen
        gj_start_jahr = int(gj_string.split('/')[0]) - 1
        gj_string_vj = f"{gj_start_jahr}/{gj_start_jahr + 1 - 2000}"
    else:
        gj_string_vj = gj_string
    
    von_datum, bis_datum = get_geschaeftsjahr_datum(gj_string_vj)
    monate = get_monatliche_zeitraeume(von_datum, bis_datum)
    
    guv_filter = get_guv_filter()
    
    bereiche = ['NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige']
    
    with locosoft_session() as conn:
        cursor = conn.cursor()
        
        bereichs_daten = {bereich: [] for bereich in bereiche}
        bereichs_gesamt = {bereich: {'umsatz': 0.0, 'einsatz': 0.0, 'db1': 0.0, 'variable': 0.0, 'db2': 0.0} for bereich in bereiche}
        
        # Variable Kosten gesamt (für Validierung)
        gesamt_variable = 0.0
        
        for monat in monate:
            # DB1 und Variable Kosten pro Bereich
            for bereich in bereiche:
                db1_data = berechne_db1_bereich(
                    cursor,
                    monat['von'],
                    monat['bis'],
                    bereich,
                    guv_filter
                )
                
                # Variable Kosten direkt für diesen Bereich
                variable_bereich = berechne_variable_kosten_bereich(
                    cursor,
                    monat['von'],
                    monat['bis'],
                    bereich,
                    guv_filter
                )
                
                db2 = db1_data['db1'] - variable_bereich
                
                bereichs_daten[bereich].append({
                    **monat,
                    'umsatz': db1_data['umsatz'],
                    'einsatz': db1_data['einsatz'],
                    'db1': db1_data['db1'],
                    'variable': variable_bereich,
                    'db2': round(db2, 2)
                })
                
                bereichs_gesamt[bereich]['umsatz'] += db1_data['umsatz']
                bereichs_gesamt[bereich]['einsatz'] += db1_data['einsatz']
                bereichs_gesamt[bereich]['db1'] += db1_data['db1']
                bereichs_gesamt[bereich]['variable'] += variable_bereich
                bereichs_gesamt[bereich]['db2'] += db2
                
                gesamt_variable += variable_bereich
        
        # Gesamtwerte runden
        for bereich in bereiche:
            bereichs_gesamt[bereich]['umsatz'] = round(bereichs_gesamt[bereich]['umsatz'], 2)
            bereichs_gesamt[bereich]['einsatz'] = round(bereichs_gesamt[bereich]['einsatz'], 2)
            bereichs_gesamt[bereich]['db1'] = round(bereichs_gesamt[bereich]['db1'], 2)
            bereichs_gesamt[bereich]['variable'] = round(bereichs_gesamt[bereich]['variable'], 2)
            bereichs_gesamt[bereich]['db2'] = round(bereichs_gesamt[bereich]['db2'], 2)
        
        return {
            'gj_string': gj_string_vj,
            'von_datum': von_datum.isoformat(),
            'bis_datum': bis_datum.isoformat(),
            'monate': monate,
            'bereiche': bereichs_daten,
            'gesamt': bereichs_gesamt,
            'gesamt_variable': round(gesamt_variable, 2)
        }


def exportiere_csv(aktuell: Dict, vorjahr: Dict, output_file: str):
    """
    Exportiert Daten als CSV.
    
    Args:
        aktuell: Daten für aktuelles Geschäftsjahr
        vorjahr: Daten für Vorjahr
        output_file: Pfad zur CSV-Datei
    """
    spalten = [
        'gj_monat',
        'gj_monat_name',
        'kal_monat',
        'kal_jahr',
        'kal_monat_name',
        'nw_db1', 'nw_variable', 'nw_db2',
        'nw_db1_vj', 'nw_variable_vj', 'nw_db2_vj',
        'nw_db2_diff', 'nw_db2_diff_prozent',
        'gw_db1', 'gw_variable', 'gw_db2',
        'gw_db1_vj', 'gw_variable_vj', 'gw_db2_vj',
        'gw_db2_diff', 'gw_db2_diff_prozent',
        'teile_db1', 'teile_variable', 'teile_db2',
        'teile_db1_vj', 'teile_variable_vj', 'teile_db2_vj',
        'teile_db2_diff', 'teile_db2_diff_prozent',
        'werkstatt_db1', 'werkstatt_variable', 'werkstatt_db2',
        'werkstatt_db1_vj', 'werkstatt_variable_vj', 'werkstatt_db2_vj',
        'werkstatt_db2_diff', 'werkstatt_db2_diff_prozent',
        'sonstige_db1', 'sonstige_variable', 'sonstige_db2',
        'sonstige_db1_vj', 'sonstige_variable_vj', 'sonstige_db2_vj',
        'sonstige_db2_diff', 'sonstige_db2_diff_prozent',
        'gesamt_variable', 'gesamt_variable_vj'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=spalten)
        writer.writeheader()
        
        for monat in aktuell['monate']:
            gj_monat = monat['gj_monat']
            
            row = {
                'gj_monat': gj_monat,
                'gj_monat_name': monat['gj_monat_name'],
                'kal_monat': monat['kal_monat'],
                'kal_jahr': monat['kal_jahr'],
                'kal_monat_name': monat['kal_monat_name'],
            }
            
            # Variable Kosten gesamt für diesen Monat
            akt_variable_gesamt = 0.0
            vj_variable_gesamt = 0.0
            
            # Für jeden Bereich
            for bereich in ['NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige']:
                bereich_lower = bereich.lower()
                
                # Aktuelle Daten
                if gj_monat <= len(aktuell['bereiche'][bereich]):
                    akt_bereich = aktuell['bereiche'][bereich][gj_monat - 1]
                else:
                    akt_bereich = {}
                
                # Vorjahres-Daten
                if gj_monat <= len(vorjahr['bereiche'][bereich]):
                    vj_bereich = vorjahr['bereiche'][bereich][gj_monat - 1]
                else:
                    vj_bereich = {}
                
                row[f'{bereich_lower}_db1'] = akt_bereich.get('db1', 0)
                row[f'{bereich_lower}_variable'] = akt_bereich.get('variable', 0)
                row[f'{bereich_lower}_db2'] = akt_bereich.get('db2', 0)
                row[f'{bereich_lower}_db1_vj'] = vj_bereich.get('db1', 0)
                row[f'{bereich_lower}_variable_vj'] = vj_bereich.get('variable', 0)
                row[f'{bereich_lower}_db2_vj'] = vj_bereich.get('db2', 0)
                
                akt_variable_gesamt += akt_bereich.get('variable', 0)
                vj_variable_gesamt += vj_bereich.get('variable', 0)
                
                # Differenz
                vj_db2 = vj_bereich.get('db2', 0)
                akt_db2 = akt_bereich.get('db2', 0)
                diff = akt_db2 - vj_db2
                diff_prozent = (diff / vj_db2 * 100) if vj_db2 != 0 else 0
                
                row[f'{bereich_lower}_db2_diff'] = round(diff, 2)
                row[f'{bereich_lower}_db2_diff_prozent'] = round(diff_prozent, 2)
            
            row['gesamt_variable'] = round(akt_variable_gesamt, 2)
            row['gesamt_variable_vj'] = round(vj_variable_gesamt, 2)
            
            writer.writerow(row)
    
    print(f"✅ CSV exportiert: {output_file}")


def main():
    """Hauptfunktion."""
    print("=" * 80)
    print("DB2-ENTWICKLUNG FÜR ALLE BEREICHE")
    print("=" * 80)
    print()
    print("ℹ️  HINWEIS:")
    print("    Variable Kosten werden nach KST (Kostenstelle) zugeordnet:")
    print("    - NW: KST 1, GW: KST 2, Teile: KST 3, Sonstige: KST 6/7")
    print("    - Werkstatt: Keine Variable Kosten in Locosoft (KST 4 nicht vorhanden)")
    print("    - Für Gesamtsumme: Alle Betriebe zusammen (Deggendorf + Landau + Hyundai)")
    print()
    
    # Geschäftsjahr 2024/25
    gj_string = "2024/25"
    
    print(f"📅 Analysiere Geschäftsjahr: {gj_string}")
    print()
    
    # Aktuelles Jahr
    print("🔍 Lade aktuelle DB2-Daten...")
    aktuell = hole_db2_entwicklung(gj_string, vorjahr=False)
    
    # Vorjahr
    print("🔍 Lade Vorjahres-DB2-Daten...")
    vorjahr = hole_db2_entwicklung(gj_string, vorjahr=True)
    
    print()
    print("=" * 80)
    print("ZUSAMMENFASSUNG")
    print("=" * 80)
    print()
    print(f"Gesamt Variable Kosten: {aktuell['gesamt_variable']:,.2f} € (VJ: {vorjahr['gesamt_variable']:,.2f} €)")
    print()
    
    bereiche = ['NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige']
    
    for bereich in bereiche:
        akt = aktuell['gesamt'][bereich]
        vj = vorjahr['gesamt'][bereich]
        
        diff_db1 = akt['db1'] - vj['db1']
        diff_variable = akt['variable'] - vj['variable']
        diff_db2 = akt['db2'] - vj['db2']
        
        print(f"{bereich}:")
        print(f"  DB1:      {akt['db1']:>12,.2f} € (VJ: {vj['db1']:>12,.2f} €, {diff_db1:+.2f} €)")
        print(f"  Variable: {akt['variable']:>12,.2f} € (VJ: {vj['variable']:>12,.2f} €, {diff_variable:+.2f} €)")
        print(f"  DB2:      {akt['db2']:>12,.2f} € (VJ: {vj['db2']:>12,.2f} €, {diff_db2:+.2f} €, {diff_db2/vj['db2']*100 if vj['db2'] != 0 else 0:+.1f}%)")
        print()
    
    # CSV exportieren
    output_file = f"scripts/db2_entwicklung_gj_{gj_string.replace('/', '_')}.csv"
    exportiere_csv(aktuell, vorjahr, output_file)
    
    print()
    print("=" * 80)
    print("EINSCHÄTZUNG")
    print("=" * 80)
    print()
    print("✅ VALIDE FÜR GESAMTKOSTEN:")
    print("   - Variable Kosten: Direkt aus Locosoft journal_accountings")
    print("   - Zuordnung nach KST (Kostenstelle): NW=KST1, GW=KST2, Teile=KST3, Sonstige=KST6/7")
    print("   - Filter-Logik: Deggendorf + Landau + Hyundai (ohne 8910xx für Hyundai)")
    print("   - G&V-Filter: Korrekt angewendet")
    print("   - Kontenbereiche: 4151xx, 4355xx, 455xxx, 487xxx, 491xxx-497899, 8910xx (bedingt)")
    print()
    print("⚠️  EINSCHRÄNKUNGEN:")
    print("   - Werkstatt: Keine Variable Kosten in Locosoft (KST 4 nicht vorhanden)")
    print("   - Standort-spezifische Verteilung: Für Gesamtsumme alle Betriebe zusammen")
    print("   - BWA-Bugs: Standort-Filter können in BWA abweichen (6. Ziffer vs. branch_number)")
    print("   - Für Präsentation: Gesamtwerte sind valide, Standort-Verteilung kann abweichen")
    print()
    print("📊 BEKANNTE BWA-BUGS (TAG 182, 186):")
    print("   - Variable Kosten: Komplexe Standort-Filter (6. Ziffer für Deggendorf/Landau)")
    print("   - 8910xx: Muss für Hyundai ausgeschlossen werden (Erträge, nicht Kosten)")
    print("   - Landau: branch_number=3 ODER 6. Ziffer='2' (unterschiedliche Logik)")
    print("   - Diese Analyse verwendet vereinfachte Logik für Gesamtsumme")
    print()
    print("=" * 80)
    print("✅ Analyse abgeschlossen!")
    print("=" * 80)


if __name__ == '__main__':
    main()
