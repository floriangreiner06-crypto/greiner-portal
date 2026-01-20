#!/usr/bin/env python3
"""
Analyse: Teileumschlag und Fahrzeug-Standzeiten für beide Geschäftsjahre

Zweck:
- Teileumschlag: Umsatz / Durchschnittlicher Lagerwert
- Fahrzeug-Standzeiten: Durchschnittliche Standzeit für NW und GW
- Zeitraum: 01.09.2023 - 31.08.2025 (beide Geschäftsjahre)

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


def berechne_teileumschlag(
    cursor,
    von_datum: date,
    bis_datum: date
) -> Dict[str, float]:
    """
    Berechnet Teileumschlag für einen Zeitraum.
    
    Teileumschlag = (Umsatz × 12) / Durchschnittlicher Lagerwert
    
    Oder alternativ:
    Teileumschlag = Umsatz / (Lagerwert / 12)
    
    Args:
        cursor: Datenbank-Cursor
        von_datum: Startdatum
        bis_datum: Enddatum
    
    Returns:
        dict mit 'umsatz', 'lagerwert_durchschnitt', 'umschlag'
    """
    # Teileumsatz (aus invoices)
    cursor.execute("""
        SELECT COALESCE(SUM(i.part_amount_net), 0) as umsatz
        FROM invoices i
        WHERE i.invoice_date >= %s AND i.invoice_date < %s
          AND i.is_canceled = false
          AND i.part_amount_net > 0
    """, (von_datum, bis_datum))
    umsatz = float(cursor.fetchone()[0] or 0)
    
    # Durchschnittlicher Lagerwert (aus parts_stock)
    # Wir nehmen den Durchschnitt über den Zeitraum
    # Vereinfacht: Aktueller Lagerwert (könnte auch monatlich gemittelt werden)
    cursor.execute("""
        SELECT 
            COALESCE(SUM(ps.stock_level * ps.usage_value), 0) as lagerwert_gesamt,
            COUNT(DISTINCT ps.stock_no) as anzahl_betriebe
        FROM parts_stock ps
        JOIN parts_master pm ON ps.part_number = pm.part_number
        WHERE ps.stock_level > 0
          AND pm.parts_type NOT IN (1, 60, 65)  -- AT-Teile ausschließen
          AND UPPER(pm.description) NOT LIKE '%KAUTION%'
          AND UPPER(pm.description) NOT LIKE '%RUECKLAUFTEIL%'
    """)
    row = cursor.fetchone()
    lagerwert_gesamt = float(row[0] or 0) if row else 0.0
    
    # Teileumschlag berechnen
    # Formel: (Umsatz / Anzahl Monate) × 12 / Lagerwert
    # Oder: Umsatz × 12 / (Lagerwert × Anzahl Monate)
    monate_anzahl = (bis_datum.year - von_datum.year) * 12 + (bis_datum.month - von_datum.month)
    if monate_anzahl == 0:
        monate_anzahl = 1
    
    umsatz_pro_monat = umsatz / monate_anzahl
    umsatz_jahr = umsatz_pro_monat * 12
    
    umschlag = (umsatz_jahr / lagerwert_gesamt) if lagerwert_gesamt > 0 else 0.0
    
    return {
        'umsatz': round(umsatz, 2),
        'umsatz_pro_monat': round(umsatz_pro_monat, 2),
        'umsatz_jahr': round(umsatz_jahr, 2),
        'lagerwert_durchschnitt': round(lagerwert_gesamt, 2),
        'umschlag': round(umschlag, 2)
    }


def berechne_standzeiten(
    cursor,
    von_datum: date,
    bis_datum: date,
    fahrzeugtyp: str
) -> Dict[str, float]:
    """
    Berechnet durchschnittliche Standzeiten für verkaufte Fahrzeuge.
    
    Standzeit = out_invoice_date - in_arrival_date (in Tagen)
    
    Args:
        cursor: Datenbank-Cursor
        von_datum: Startdatum
        bis_datum: Enddatum
        fahrzeugtyp: 'NW' oder 'GW'
    
    Returns:
        dict mit 'anzahl', 'standzeit_durchschnitt', 'standzeit_median'
    """
    # Typ-Filter
    if fahrzeugtyp == 'NW':
        typ_filter = "dealer_vehicle_type IN ('N', 'V')"  # Neuwagen + Vorführwagen
    elif fahrzeugtyp == 'GW':
        typ_filter = "dealer_vehicle_type IN ('G', 'D', 'L')"  # Gebrauchtwagen + Demo + Leihfahrzeug
    else:
        return {'anzahl': 0, 'standzeit_durchschnitt': 0.0, 'standzeit_median': 0.0}
    
    # Durchschnittliche Standzeit für verkaufte Fahrzeuge
    cursor.execute(f"""
        SELECT 
            COUNT(*) as anzahl,
            AVG(out_invoice_date - in_arrival_date) as standzeit_durchschnitt
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND in_arrival_date IS NOT NULL
          AND {typ_filter}
    """, (von_datum, bis_datum))
    
    row = cursor.fetchone()
    anzahl = int(row[0] or 0) if row else 0
    standzeit_durchschnitt = float(row[1] or 0) if row and row[1] else 0.0
    
    # Median berechnen (für robustere Statistik)
    cursor.execute(f"""
        SELECT 
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (out_invoice_date - in_arrival_date)) as standzeit_median
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND in_arrival_date IS NOT NULL
          AND {typ_filter}
    """, (von_datum, bis_datum))
    
    row_median = cursor.fetchone()
    standzeit_median = float(row_median[0] or 0) if row_median and row_median[0] else 0.0
    
    return {
        'anzahl': anzahl,
        'standzeit_durchschnitt': round(standzeit_durchschnitt, 1),
        'standzeit_median': round(standzeit_median, 1)
    }


def hole_kennzahlen(
    gj_string: str
) -> Dict[str, Any]:
    """
    Holt Teileumschlag und Standzeiten für Geschäftsjahr.
    
    Args:
        gj_string: z.B. '2024/25'
    
    Returns:
        dict mit monatlichen Daten
    """
    von_datum, bis_datum = get_geschaeftsjahr_datum(gj_string)
    monate = get_monatliche_zeitraeume(von_datum, bis_datum)
    
    with locosoft_session() as conn:
        cursor = conn.cursor()
        
        monatsdaten = []
        gesamt_teile_umsatz = 0.0
        gesamt_nw_anzahl = 0
        gesamt_nw_standzeit_sum = 0.0
        gesamt_gw_anzahl = 0
        gesamt_gw_standzeit_sum = 0.0
        
        for monat in monate:
            # Teileumschlag
            teile_data = berechne_teileumschlag(
                cursor,
                monat['von'],
                monat['bis']
            )
            
            # Standzeiten NW
            nw_data = berechne_standzeiten(
                cursor,
                monat['von'],
                monat['bis'],
                'NW'
            )
            
            # Standzeiten GW
            gw_data = berechne_standzeiten(
                cursor,
                monat['von'],
                monat['bis'],
                'GW'
            )
            
            monatsdaten.append({
                **monat,
                **teile_data,
                'nw_anzahl': nw_data['anzahl'],
                'nw_standzeit_durchschnitt': nw_data['standzeit_durchschnitt'],
                'nw_standzeit_median': nw_data['standzeit_median'],
                'gw_anzahl': gw_data['anzahl'],
                'gw_standzeit_durchschnitt': gw_data['standzeit_durchschnitt'],
                'gw_standzeit_median': gw_data['standzeit_median']
            })
            
            # Gesamtwerte akkumulieren
            gesamt_teile_umsatz += teile_data['umsatz']
            gesamt_nw_anzahl += nw_data['anzahl']
            if nw_data['anzahl'] > 0:
                gesamt_nw_standzeit_sum += nw_data['standzeit_durchschnitt'] * nw_data['anzahl']
            gesamt_gw_anzahl += gw_data['anzahl']
            if gw_data['anzahl'] > 0:
                gesamt_gw_standzeit_sum += gw_data['standzeit_durchschnitt'] * gw_data['anzahl']
        
        # Gesamtwerte berechnen
        # Teileumschlag gesamt
        lagerwert_gesamt = monatsdaten[0]['lagerwert_durchschnitt'] if monatsdaten else 0.0
        monate_anzahl = len(monate)
        umsatz_pro_monat = gesamt_teile_umsatz / monate_anzahl if monate_anzahl > 0 else 0.0
        umsatz_jahr = umsatz_pro_monat * 12
        umschlag_gesamt = (umsatz_jahr / lagerwert_gesamt) if lagerwert_gesamt > 0 else 0.0
        
        # Standzeiten gesamt (gewichteter Durchschnitt)
        nw_standzeit_gesamt = (gesamt_nw_standzeit_sum / gesamt_nw_anzahl) if gesamt_nw_anzahl > 0 else 0.0
        gw_standzeit_gesamt = (gesamt_gw_standzeit_sum / gesamt_gw_anzahl) if gesamt_gw_anzahl > 0 else 0.0
        
        return {
            'gj_string': gj_string,
            'von_datum': von_datum.isoformat(),
            'bis_datum': bis_datum.isoformat(),
            'monate': monatsdaten,
            'gesamt': {
                'teile_umsatz': round(gesamt_teile_umsatz, 2),
                'teile_umsatz_pro_monat': round(umsatz_pro_monat, 2),
                'teile_umsatz_jahr': round(umsatz_jahr, 2),
                'teile_lagerwert': round(lagerwert_gesamt, 2),
                'teile_umschlag': round(umschlag_gesamt, 2),
                'nw_anzahl': gesamt_nw_anzahl,
                'nw_standzeit_durchschnitt': round(nw_standzeit_gesamt, 1),
                'gw_anzahl': gesamt_gw_anzahl,
                'gw_standzeit_durchschnitt': round(gw_standzeit_gesamt, 1)
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
        'teile_umsatz',
        'teile_lagerwert',
        'teile_umschlag',
        'nw_anzahl',
        'nw_standzeit_durchschnitt',
        'nw_standzeit_median',
        'gw_anzahl',
        'gw_standzeit_durchschnitt',
        'gw_standzeit_median',
        'teile_umsatz_vj',
        'teile_lagerwert_vj',
        'teile_umschlag_vj',
        'nw_anzahl_vj',
        'nw_standzeit_durchschnitt_vj',
        'gw_anzahl_vj',
        'gw_standzeit_durchschnitt_vj',
        'teile_umschlag_diff',
        'nw_standzeit_diff',
        'gw_standzeit_diff'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=spalten)
        writer.writeheader()
        
        for monat in aktuell['monate']:
            gj_monat = monat['gj_monat']
            
            # Vorjahres-Daten finden
            vj_monat = None
            for vj_m in vorjahr['monate']:
                if vj_m['gj_monat'] == gj_monat:
                    vj_monat = vj_m
                    break
            
            row = {
                'gj_monat': gj_monat,
                'gj_monat_name': monat['gj_monat_name'],
                'kal_monat': monat['kal_monat'],
                'kal_jahr': monat['kal_jahr'],
                'kal_monat_name': monat['kal_monat_name'],
                'teile_umsatz': monat.get('umsatz', 0),
                'teile_lagerwert': monat.get('lagerwert_durchschnitt', 0),
                'teile_umschlag': monat.get('umschlag', 0),
                'nw_anzahl': monat.get('nw_anzahl', 0),
                'nw_standzeit_durchschnitt': monat.get('nw_standzeit_durchschnitt', 0),
                'nw_standzeit_median': monat.get('nw_standzeit_median', 0),
                'gw_anzahl': monat.get('gw_anzahl', 0),
                'gw_standzeit_durchschnitt': monat.get('gw_standzeit_durchschnitt', 0),
                'gw_standzeit_median': monat.get('gw_standzeit_median', 0),
            }
            
            if vj_monat:
                row['teile_umsatz_vj'] = vj_monat.get('umsatz', 0)
                row['teile_lagerwert_vj'] = vj_monat.get('lagerwert_durchschnitt', 0)
                row['teile_umschlag_vj'] = vj_monat.get('umschlag', 0)
                row['nw_anzahl_vj'] = vj_monat.get('nw_anzahl', 0)
                row['nw_standzeit_durchschnitt_vj'] = vj_monat.get('nw_standzeit_durchschnitt', 0)
                row['gw_anzahl_vj'] = vj_monat.get('gw_anzahl', 0)
                row['gw_standzeit_durchschnitt_vj'] = vj_monat.get('gw_standzeit_durchschnitt', 0)
                
                # Differenzen
                row['teile_umschlag_diff'] = round(monat.get('umschlag', 0) - vj_monat.get('umschlag', 0), 2)
                row['nw_standzeit_diff'] = round(monat.get('nw_standzeit_durchschnitt', 0) - vj_monat.get('nw_standzeit_durchschnitt', 0), 1)
                row['gw_standzeit_diff'] = round(monat.get('gw_standzeit_durchschnitt', 0) - vj_monat.get('gw_standzeit_durchschnitt', 0), 1)
            else:
                row['teile_umsatz_vj'] = 0
                row['teile_lagerwert_vj'] = 0
                row['teile_umschlag_vj'] = 0
                row['nw_anzahl_vj'] = 0
                row['nw_standzeit_durchschnitt_vj'] = 0
                row['gw_anzahl_vj'] = 0
                row['gw_standzeit_durchschnitt_vj'] = 0
                row['teile_umschlag_diff'] = 0
                row['nw_standzeit_diff'] = 0
                row['gw_standzeit_diff'] = 0
            
            writer.writerow(row)
    
    print(f"✅ CSV exportiert: {output_file}")


def main():
    """Hauptfunktion."""
    print("=" * 80)
    print("TEILEUMSCHLAG UND FAHRZEUG-STANDZEITEN")
    print("=" * 80)
    print()
    
    # Beide Geschäftsjahre
    gj_strings = ["2023/24", "2024/25"]
    
    ergebnisse = {}
    
    for gj_string in gj_strings:
        print(f"📅 Analysiere Geschäftsjahr: {gj_string}")
        print()
        
        print("🔍 Lade Daten...")
        ergebnisse[gj_string] = hole_kennzahlen(gj_string)
        
        zus = ergebnisse[gj_string]['gesamt']
        print()
        print(f"ZUSAMMENFASSUNG {gj_string}:")
        print(f"  Teileumsatz:        {zus['teile_umsatz']:>12,.2f} €")
        print(f"  Teileumsatz/Jahr:   {zus['teile_umsatz_jahr']:>12,.2f} €")
        print(f"  Lagerwert:          {zus['teile_lagerwert']:>12,.2f} €")
        print(f"  Teileumschlag:      {zus['teile_umschlag']:>12,.2f}")
        print(f"  NW Anzahl:          {zus['nw_anzahl']:>12,} Stk")
        print(f"  NW Standzeit (Ø):   {zus['nw_standzeit_durchschnitt']:>12,.1f} Tage")
        print(f"  GW Anzahl:          {zus['gw_anzahl']:>12,} Stk")
        print(f"  GW Standzeit (Ø):  {zus['gw_standzeit_durchschnitt']:>12,.1f} Tage")
        print()
    
    # Vergleich
    print("=" * 80)
    print("VERGLEICH 2023/24 vs. 2024/25")
    print("=" * 80)
    print()
    
    akt = ergebnisse['2024/25']['gesamt']
    vj = ergebnisse['2023/24']['gesamt']
    
    print("Teileumschlag:")
    print(f"  2023/24: {vj['teile_umschlag']:.2f}")
    print(f"  2024/25: {akt['teile_umschlag']:.2f}")
    print(f"  Differenz: {akt['teile_umschlag'] - vj['teile_umschlag']:+.2f} ({((akt['teile_umschlag'] / vj['teile_umschlag'] - 1) * 100) if vj['teile_umschlag'] > 0 else 0:+.1f}%)")
    print()
    
    print("NW Standzeit:")
    print(f"  2023/24: {vj['nw_standzeit_durchschnitt']:.1f} Tage")
    print(f"  2024/25: {akt['nw_standzeit_durchschnitt']:.1f} Tage")
    print(f"  Differenz: {akt['nw_standzeit_durchschnitt'] - vj['nw_standzeit_durchschnitt']:+.1f} Tage")
    print()
    
    print("GW Standzeit:")
    print(f"  2023/24: {vj['gw_standzeit_durchschnitt']:.1f} Tage")
    print(f"  2024/25: {akt['gw_standzeit_durchschnitt']:.1f} Tage")
    print(f"  Differenz: {akt['gw_standzeit_durchschnitt'] - vj['gw_standzeit_durchschnitt']:+.1f} Tage")
    print()
    
    # CSV exportieren
    output_file = "scripts/teileumschlag_standzeiten_vergleich.csv"
    exportiere_csv(ergebnisse['2024/25'], ergebnisse['2023/24'], output_file)
    
    print()
    print("=" * 80)
    print("✅ Analyse abgeschlossen!")
    print("=" * 80)


if __name__ == '__main__':
    main()
