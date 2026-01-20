#!/usr/bin/env python3
"""
Analyse: Kostenentwicklung für Geschäftsjahr 2024/25 aus Locosoft

Zweck:
- Monatliche Kostenentwicklung für Betriebsversammlung
- Gesamtkosten (Variable + Direkte + Indirekte)
- Vergleich zum Vorjahr
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


def berechne_kosten_monat(
    cursor,
    von_datum: date,
    bis_datum: date,
    guv_filter: str
) -> Dict[str, float]:
    """
    Berechnet Kosten für einen Monat.
    
    Args:
        cursor: Datenbank-Cursor
        von_datum: Startdatum
        bis_datum: Enddatum
        guv_filter: G&V-Filter (aus get_guv_filter())
    
    Returns:
        dict mit 'variable', 'direkte', 'indirekte', 'gesamt'
    """
    # Variable Kosten
    # WICHTIG: Für Gesamtkosten keine Standort-Filter (alle Betriebe zusammen)
    cursor.execute(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
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
          )
          {guv_filter}
    """, (von_datum, bis_datum))
    variable = float(cursor.fetchone()[0] or 0)
    
    # Direkte Kosten
    cursor.execute(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND NOT (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
          {guv_filter}
    """, (von_datum, bis_datum))
    direkte = float(cursor.fetchone()[0] or 0)
    
    # Indirekte Kosten
    cursor.execute(f"""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
        )/100.0, 0) as wert
        FROM journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND (
            (nominal_account_number BETWEEN 400000 AND 499999
             AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR (nominal_account_number BETWEEN 424000 AND 424999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR (nominal_account_number BETWEEN 438000 AND 438999
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR nominal_account_number BETWEEN 498000 AND 499999
            OR (nominal_account_number BETWEEN 891000 AND 896999
                AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
          )
          {guv_filter}
    """, (von_datum, bis_datum))
    indirekte = float(cursor.fetchone()[0] or 0)
    
    gesamt = variable + direkte + indirekte
    
    return {
        'variable': round(variable, 2),
        'direkte': round(direkte, 2),
        'indirekte': round(indirekte, 2),
        'gesamt': round(gesamt, 2)
    }


def hole_kostenentwicklung(
    gj_string: str,
    vorjahr: bool = False
) -> Dict[str, Any]:
    """
    Holt Kostenentwicklung für Geschäftsjahr.
    
    Args:
        gj_string: z.B. '2024/25'
        vorjahr: Wenn True, hole Vorjahres-Daten
    
    Returns:
        dict mit monatlichen Daten
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
    
    with locosoft_session() as conn:
        cursor = conn.cursor()
        
        monatsdaten = []
        for monat in monate:
            kosten = berechne_kosten_monat(
                cursor,
                monat['von'],
                monat['bis'],
                guv_filter
            )
            
            monatsdaten.append({
                **monat,
                **kosten
            })
        
        # Gesamtwerte
        gesamt_variable = sum(m['variable'] for m in monatsdaten)
        gesamt_direkte = sum(m['direkte'] for m in monatsdaten)
        gesamt_indirekte = sum(m['indirekte'] for m in monatsdaten)
        gesamt_gesamt = sum(m['gesamt'] for m in monatsdaten)
        
        return {
            'gj_string': gj_string_vj,
            'von_datum': von_datum.isoformat(),
            'bis_datum': bis_datum.isoformat(),
            'monate': monatsdaten,
            'gesamt': {
                'variable': round(gesamt_variable, 2),
                'direkte': round(gesamt_direkte, 2),
                'indirekte': round(gesamt_indirekte, 2),
                'gesamt': round(gesamt_gesamt, 2)
            }
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
        'variable_kosten',
        'direkte_kosten',
        'indirekte_kosten',
        'gesamt_kosten',
        'variable_kosten_vj',
        'direkte_kosten_vj',
        'indirekte_kosten_vj',
        'gesamt_kosten_vj',
        'differenz_gesamt',
        'differenz_prozent'
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
                'variable_kosten': monat['variable'],
                'direkte_kosten': monat['direkte'],
                'indirekte_kosten': monat['indirekte'],
                'gesamt_kosten': monat['gesamt'],
                'variable_kosten_vj': vj_monat.get('variable', 0),
                'direkte_kosten_vj': vj_monat.get('direkte', 0),
                'indirekte_kosten_vj': vj_monat.get('indirekte', 0),
                'gesamt_kosten_vj': vj_monat.get('gesamt', 0),
            }
            
            # Differenz berechnen
            vj_gesamt = vj_monat.get('gesamt', 0)
            diff = monat['gesamt'] - vj_gesamt
            diff_prozent = (diff / vj_gesamt * 100) if vj_gesamt > 0 else 0
            
            row['differenz_gesamt'] = round(diff, 2)
            row['differenz_prozent'] = round(diff_prozent, 2)
            
            writer.writerow(row)
    
    print(f"✅ CSV exportiert: {output_file}")


def main():
    """Hauptfunktion."""
    print("=" * 80)
    print("KOSTENENTWICKLUNG FÜR BETRIEBSVERSAMMLUNG")
    print("=" * 80)
    print()
    
    # Geschäftsjahr 2024/25
    gj_string = "2024/25"
    
    print(f"📅 Analysiere Geschäftsjahr: {gj_string}")
    print()
    
    # Aktuelles Jahr
    print("🔍 Lade aktuelle Kosten...")
    aktuell = hole_kostenentwicklung(gj_string, vorjahr=False)
    
    # Vorjahr
    print("🔍 Lade Vorjahres-Kosten...")
    vorjahr = hole_kostenentwicklung(gj_string, vorjahr=True)
    
    print()
    print("=" * 80)
    print("ZUSAMMENFASSUNG")
    print("=" * 80)
    print()
    print(f"Geschäftsjahr {aktuell['gj_string']}:")
    print(f"  Variable Kosten:  {aktuell['gesamt']['variable']:>12,.2f} €")
    print(f"  Direkte Kosten:    {aktuell['gesamt']['direkte']:>12,.2f} €")
    print(f"  Indirekte Kosten:  {aktuell['gesamt']['indirekte']:>12,.2f} €")
    print(f"  GESAMTKOSTEN:      {aktuell['gesamt']['gesamt']:>12,.2f} €")
    print()
    print(f"Geschäftsjahr {vorjahr['gj_string']} (Vorjahr):")
    print(f"  Variable Kosten:  {vorjahr['gesamt']['variable']:>12,.2f} €")
    print(f"  Direkte Kosten:    {vorjahr['gesamt']['direkte']:>12,.2f} €")
    print(f"  Indirekte Kosten:  {vorjahr['gesamt']['indirekte']:>12,.2f} €")
    print(f"  GESAMTKOSTEN:      {vorjahr['gesamt']['gesamt']:>12,.2f} €")
    print()
    
    # Differenz
    diff_variable = aktuell['gesamt']['variable'] - vorjahr['gesamt']['variable']
    diff_direkte = aktuell['gesamt']['direkte'] - vorjahr['gesamt']['direkte']
    diff_indirekte = aktuell['gesamt']['indirekte'] - vorjahr['gesamt']['indirekte']
    diff_gesamt = aktuell['gesamt']['gesamt'] - vorjahr['gesamt']['gesamt']
    
    print("Differenz (Aktuell - Vorjahr):")
    print(f"  Variable Kosten:  {diff_variable:>12,.2f} € ({diff_variable/vorjahr['gesamt']['variable']*100:+.1f}%)")
    print(f"  Direkte Kosten:    {diff_direkte:>12,.2f} € ({diff_direkte/vorjahr['gesamt']['direkte']*100:+.1f}%)")
    print(f"  Indirekte Kosten:  {diff_indirekte:>12,.2f} € ({diff_indirekte/vorjahr['gesamt']['indirekte']*100:+.1f}%)")
    print(f"  GESAMTKOSTEN:      {diff_gesamt:>12,.2f} € ({diff_gesamt/vorjahr['gesamt']['gesamt']*100:+.1f}%)")
    print()
    
    # Monatliche Übersicht
    print("=" * 80)
    print("MONATLICHE ÜBERSICHT")
    print("=" * 80)
    print(f"{'GJ-Monat':<10} {'Kalender':<15} {'Gesamtkosten':>15} {'Vorjahr':>15} {'Differenz':>15} {'%':>8}")
    print("-" * 80)
    
    vj_dict = {m['gj_monat']: m for m in vorjahr['monate']}
    for monat in aktuell['monate']:
        gj_monat = monat['gj_monat']
        vj_monat = vj_dict.get(gj_monat, {})
        vj_gesamt = vj_monat.get('gesamt', 0)
        diff = monat['gesamt'] - vj_gesamt
        diff_prozent = (diff / vj_gesamt * 100) if vj_gesamt > 0 else 0
        
        print(f"{gj_monat:<10} {monat['kal_monat_name']} {monat['kal_jahr']:<4} {monat['gesamt']:>15,.2f} € {vj_gesamt:>15,.2f} € {diff:>15,.2f} € {diff_prozent:>7.1f}%")
    
    print()
    
    # CSV exportieren
    output_file = f"scripts/kostenentwicklung_gj_{gj_string.replace('/', '_')}.csv"
    exportiere_csv(aktuell, vorjahr, output_file)
    
    print()
    print("=" * 80)
    print("✅ Analyse abgeschlossen!")
    print("=" * 80)


if __name__ == '__main__':
    main()
