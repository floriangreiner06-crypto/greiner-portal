#!/usr/bin/env python3
"""
Analyse: DB1-Entwicklung für alle Bereiche (Geschäftsjahr 2024/25)

Zweck:
- DB1 = Umsatz - Einsatz für alle Bereiche
- Bereiche: NW, GW, Teile, Werkstatt, Sonstige
- Monatliche Entwicklung mit Vorjahresvergleich
- Zeitraum: 01.09.2024 - 31.08.2025 (Geschäftsjahr 2024/25)

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
        # Neuwagen: invoice_type = 7
        umsatz_query = """
            SELECT COALESCE(SUM(i.total_net), 0) as umsatz
            FROM invoices i
            WHERE i.invoice_date >= %s AND i.invoice_date < %s
              AND i.invoice_type = 7
              AND i.is_canceled = false
        """
    elif bereich == 'GW':
        # Gebrauchtwagen: invoice_type = 8
        umsatz_query = """
            SELECT COALESCE(SUM(i.total_net), 0) as umsatz
            FROM invoices i
            WHERE i.invoice_date >= %s AND i.invoice_date < %s
              AND i.invoice_type = 8
              AND i.is_canceled = false
        """
    elif bereich == 'Teile':
        # Teile: part_amount_net aus invoices
        umsatz_query = """
            SELECT COALESCE(SUM(i.part_amount_net), 0) as umsatz
            FROM invoices i
            WHERE i.invoice_date >= %s AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.part_amount_net > 0
        """
    elif bereich == 'Werkstatt':
        # Werkstatt: job_amount_net aus invoices (invoice_type 2, 4, 5, 6)
        umsatz_query = """
            SELECT COALESCE(SUM(i.job_amount_net), 0) as umsatz
            FROM invoices i
            WHERE i.invoice_date >= %s AND i.invoice_date < %s
              AND i.invoice_type IN (2, 4, 5, 6)
              AND i.is_canceled = false
              AND i.job_amount_net > 0
        """
    elif bereich == 'Sonstige':
        # Sonstige: alle anderen invoice_types (nicht 2,4,5,6,7,8)
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
    # NW: Konten 817xxx
    # GW: Konten 827xxx
    # Teile: Konten 837xxx
    # Werkstatt: Konten 847xxx
    # Sonstige: andere 8xxxxx (außer 89xxxx)
    
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
        # Sonstige: 8xxxxx außer 81xxx-84xxx und 89xxx
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


def hole_db1_entwicklung(
    gj_string: str,
    vorjahr: bool = False
) -> Dict[str, Any]:
    """
    Holt DB1-Entwicklung für alle Bereiche.
    
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
        bereichs_gesamt = {bereich: {'umsatz': 0.0, 'einsatz': 0.0, 'db1': 0.0} for bereich in bereiche}
        
        for monat in monate:
            for bereich in bereiche:
                db1_data = berechne_db1_bereich(
                    cursor,
                    monat['von'],
                    monat['bis'],
                    bereich,
                    guv_filter
                )
                
                bereichs_daten[bereich].append({
                    **monat,
                    **db1_data
                })
                
                # Gesamtwerte akkumulieren
                bereichs_gesamt[bereich]['umsatz'] += db1_data['umsatz']
                bereichs_gesamt[bereich]['einsatz'] += db1_data['einsatz']
                bereichs_gesamt[bereich]['db1'] += db1_data['db1']
        
        # Gesamtwerte runden
        for bereich in bereiche:
            bereichs_gesamt[bereich]['umsatz'] = round(bereichs_gesamt[bereich]['umsatz'], 2)
            bereichs_gesamt[bereich]['einsatz'] = round(bereichs_gesamt[bereich]['einsatz'], 2)
            bereichs_gesamt[bereich]['db1'] = round(bereichs_gesamt[bereich]['db1'], 2)
        
        return {
            'gj_string': gj_string_vj,
            'von_datum': von_datum.isoformat(),
            'bis_datum': bis_datum.isoformat(),
            'monate': monate,
            'bereiche': bereichs_daten,
            'gesamt': bereichs_gesamt
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
        'nw_umsatz', 'nw_einsatz', 'nw_db1',
        'nw_umsatz_vj', 'nw_einsatz_vj', 'nw_db1_vj',
        'nw_db1_diff', 'nw_db1_diff_prozent',
        'gw_umsatz', 'gw_einsatz', 'gw_db1',
        'gw_umsatz_vj', 'gw_einsatz_vj', 'gw_db1_vj',
        'gw_db1_diff', 'gw_db1_diff_prozent',
        'teile_umsatz', 'teile_einsatz', 'teile_db1',
        'teile_umsatz_vj', 'teile_einsatz_vj', 'teile_db1_vj',
        'teile_db1_diff', 'teile_db1_diff_prozent',
        'werkstatt_umsatz', 'werkstatt_einsatz', 'werkstatt_db1',
        'werkstatt_umsatz_vj', 'werkstatt_einsatz_vj', 'werkstatt_db1_vj',
        'werkstatt_db1_diff', 'werkstatt_db1_diff_prozent',
        'sonstige_umsatz', 'sonstige_einsatz', 'sonstige_db1',
        'sonstige_umsatz_vj', 'sonstige_einsatz_vj', 'sonstige_db1_vj',
        'sonstige_db1_diff', 'sonstige_db1_diff_prozent'
    ]
    
    # Vorjahres-Daten nach GJ-Monat indexieren
    vj_dict = {m['gj_monat']: m for m in vorjahr['monate']}
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=spalten)
        writer.writeheader()
        
        for monat in aktuell['monate']:
            gj_monat = monat['gj_monat']
            vj_monat = vj_dict.get(gj_monat, {})
            
            row = {
                'gj_monat': gj_monat,
                'gj_monat_name': monat['gj_monat_name'],
                'kal_monat': monat['kal_monat'],
                'kal_jahr': monat['kal_jahr'],
                'kal_monat_name': monat['kal_monat_name'],
            }
            
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
                
                row[f'{bereich_lower}_umsatz'] = akt_bereich.get('umsatz', 0)
                row[f'{bereich_lower}_einsatz'] = akt_bereich.get('einsatz', 0)
                row[f'{bereich_lower}_db1'] = akt_bereich.get('db1', 0)
                row[f'{bereich_lower}_umsatz_vj'] = vj_bereich.get('umsatz', 0)
                row[f'{bereich_lower}_einsatz_vj'] = vj_bereich.get('einsatz', 0)
                row[f'{bereich_lower}_db1_vj'] = vj_bereich.get('db1', 0)
                
                # Differenz
                vj_db1 = vj_bereich.get('db1', 0)
                akt_db1 = akt_bereich.get('db1', 0)
                diff = akt_db1 - vj_db1
                diff_prozent = (diff / vj_db1 * 100) if vj_db1 != 0 else 0
                
                row[f'{bereich_lower}_db1_diff'] = round(diff, 2)
                row[f'{bereich_lower}_db1_diff_prozent'] = round(diff_prozent, 2)
            
            writer.writerow(row)
    
    print(f"✅ CSV exportiert: {output_file}")


def main():
    """Hauptfunktion."""
    print("=" * 80)
    print("DB1-ENTWICKLUNG FÜR ALLE BEREICHE")
    print("=" * 80)
    print()
    
    # Geschäftsjahr 2024/25
    gj_string = "2024/25"
    
    print(f"📅 Analysiere Geschäftsjahr: {gj_string}")
    print()
    
    # Aktuelles Jahr
    print("🔍 Lade aktuelle DB1-Daten...")
    aktuell = hole_db1_entwicklung(gj_string, vorjahr=False)
    
    # Vorjahr
    print("🔍 Lade Vorjahres-DB1-Daten...")
    vorjahr = hole_db1_entwicklung(gj_string, vorjahr=True)
    
    print()
    print("=" * 80)
    print("ZUSAMMENFASSUNG")
    print("=" * 80)
    print()
    
    bereiche = ['NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige']
    
    for bereich in bereiche:
        akt = aktuell['gesamt'][bereich]
        vj = vorjahr['gesamt'][bereich]
        
        diff_umsatz = akt['umsatz'] - vj['umsatz']
        diff_einsatz = akt['einsatz'] - vj['einsatz']
        diff_db1 = akt['db1'] - vj['db1']
        
        print(f"{bereich}:")
        print(f"  Umsatz:   {akt['umsatz']:>12,.2f} € (VJ: {vj['umsatz']:>12,.2f} €, {diff_umsatz:+.2f} €)")
        print(f"  Einsatz:  {akt['einsatz']:>12,.2f} € (VJ: {vj['einsatz']:>12,.2f} €, {diff_einsatz:+.2f} €)")
        print(f"  DB1:      {akt['db1']:>12,.2f} € (VJ: {vj['db1']:>12,.2f} €, {diff_db1:+.2f} €, {diff_db1/vj['db1']*100 if vj['db1'] != 0 else 0:+.1f}%)")
        print()
    
    # CSV exportieren
    output_file = f"scripts/db1_entwicklung_gj_{gj_string.replace('/', '_')}.csv"
    exportiere_csv(aktuell, vorjahr, output_file)
    
    print()
    print("=" * 80)
    print("✅ Analyse abgeschlossen!")
    print("=" * 80)


if __name__ == '__main__':
    main()
