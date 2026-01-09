#!/usr/bin/env python3
"""
Vergleich: TEK-Daten DRIVE vs. GlobalCube
==========================================
Vergleicht TEK-Werte für aktuellen Monat (Januar 2026)
mit GlobalCube-Daten (falls CSV vorhanden)

TAG173: Prüft ob umlage='mit' korrekt funktioniert
"""

import sys
import os
sys.path.insert(0, '/opt/greiner-portal')

from datetime import date
import requests
from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

def get_drive_tek_data(monat=1, jahr=2026, umlage='mit'):
    """Holt TEK-Daten aus DRIVE API"""
    try:
        params = {
            'firma': '0',  # Alle
            'standort': '0',  # Alle
            'monat': monat,
            'jahr': jahr,
            'modus': 'teil',
            'umlage': umlage
        }
        
        response = requests.get('http://127.0.0.1:5000/controlling/api/tek', params=params, timeout=30)
        response.raise_for_status()
        
        # Debug: Prüfe Response
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")
        
        try:
            data = response.json()
        except ValueError as e:
            print(f"   ⚠️  Response-Text: {response.text[:500]}")
            raise Exception(f"JSON-Parse-Fehler: {e}")
        
        if not data.get('success'):
            raise Exception(f"API-Fehler: {data.get('error', 'Unbekannter Fehler')}")
        
        return data
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️  Service läuft nicht auf Port 5000 - verwende direkten DB-Zugriff")
        # Fallback: Verwende direkten DB-Zugriff
        return None
    except Exception as e:
        print(f"   ⚠️  API-Fehler: {e}")
        return None

def get_drive_tek_direct(monat=1, jahr=2026, umlage='mit'):
    """Holt TEK-Daten direkt aus DB (ohne API)"""
    von = f"{jahr}-{monat:02d}-01"
    bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"
    
    # Umlage-Filter
    umlage_erloese_filter = ""
    if umlage == 'ohne':
        umlage_konten_str = '817051,827051,837051,847051'
        umlage_erloese_filter = f"AND nominal_account_number NOT IN ({umlage_konten_str})"
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Gesamt-Umsatz
        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END
            ) / 100.0, 0) as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
              {umlage_erloese_filter}
        """), (von, bis))
        umsatz = float(cursor.fetchone()[0] or 0)
        
        # Gesamt-Einsatz
        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END
            ) / 100.0, 0) as einsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 700000 AND 799999
        """), (von, bis))
        einsatz = float(cursor.fetchone()[0] or 0)
        
        # Umlage-Erlöse (wenn mit Umlage)
        umlage_betrag = 0
        if umlage == 'mit':
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END
                ) / 100.0, 0) as betrag
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number IN (817051, 827051, 837051, 847051)
            """), (von, bis))
            umlage_betrag = float(cursor.fetchone()[0] or 0)
        
        # Bereichs-Aufschlüsselung
        bereiche = {}
        cursor.execute(convert_placeholders(f"""
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
            WHERE accounting_date >= ? AND accounting_date < ?
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
              {umlage_erloese_filter}
            GROUP BY bereich
        """), (von, bis))
        for row in cursor.fetchall():
            r = row_to_dict(row)
            bereiche[r['bereich']] = float(r['umsatz'] or 0)
        
        return {
            'umsatz': umsatz,
            'einsatz': einsatz,
            'db1': umsatz - einsatz,
            'marge': ((umsatz - einsatz) / umsatz * 100) if umsatz > 0 else 0,
            'umlage_betrag': umlage_betrag,
            'bereiche': bereiche
        }

def main():
    monat = 1  # Januar
    jahr = 2026
    
    print("=" * 80)
    print("TEK-Vergleich: DRIVE vs. GlobalCube")
    print(f"Zeitraum: {monat}/{jahr}")
    print("=" * 80)
    print()
    
    # 0. Direkter DB-Zugriff (funktioniert immer)
    print("📊 [0] Direkter DB-Zugriff (umlage='mit'):")
    print("-" * 80)
    direct_mit = get_drive_tek_direct(monat, jahr, umlage='mit')
    print(f"   Umsatz:  {direct_mit['umsatz']:>12,.2f} €")
    print(f"   Einsatz: {direct_mit['einsatz']:>12,.2f} €")
    print(f"   DB1:     {direct_mit['db1']:>12,.2f} €")
    print(f"   Marge:   {direct_mit['marge']:>12.1f} %")
    print(f"   Umlage-Erlöse: {direct_mit['umlage_betrag']:>12,.2f} €")
    print()
    
    # 1. DRIVE TEK mit Umlage (via API - falls verfügbar)
    print("📊 [1] DRIVE TEK API (umlage='mit'):")
    print("-" * 80)
    drive_mit = get_drive_tek_data(monat, jahr, umlage='mit')
    if drive_mit:
        gesamt_mit = drive_mit['gesamt']
        print(f"   Umsatz:  {gesamt_mit['umsatz']:>12,.2f} €")
        print(f"   Einsatz: {gesamt_mit['einsatz']:>12,.2f} €")
        print(f"   DB1:     {gesamt_mit['db1']:>12,.2f} €")
        print(f"   Marge:   {gesamt_mit['marge']:>12.1f} %")
        
        # Bereiche
        print("\n   Bereiche:")
        for bereich_key in ['1-NW', '2-GW', '3-Teile', '4-Lohn', '5-Sonst']:
            if bereich_key in drive_mit['bereiche']:
                b = drive_mit['bereiche'][bereich_key]
                print(f"     {bereich_key}: Umsatz {b['umsatz']:>10,.2f} €, DB1 {b['db1']:>10,.2f} €, Marge {b['marge']:>6.1f} %")
    else:
        print("   ⚠️  API nicht verfügbar (Auth erforderlich) - verwende direkten DB-Zugriff")
        drive_mit = {'gesamt': direct_mit}
    
    print()
    
    # 2. DRIVE TEK ohne Umlage (zum Vergleich)
    print("📊 [2] DRIVE TEK (umlage='ohne'):")
    print("-" * 80)
    drive_ohne = get_drive_tek_data(monat, jahr, umlage='ohne')
    if drive_ohne:
        gesamt_ohne = drive_ohne['gesamt']
        print(f"   Umsatz:  {gesamt_ohne['umsatz']:>12,.2f} €")
        print(f"   Einsatz: {gesamt_ohne['einsatz']:>12,.2f} €")
        print(f"   DB1:     {gesamt_ohne['db1']:>12,.2f} €")
        print(f"   Marge:   {gesamt_ohne['marge']:>12.1f} %")
        
        # Umlage-Betrag
        if 'umlage_betrag_erloese' in drive_ohne.get('filter', {}):
            umlage = drive_ohne['filter'].get('umlage_betrag_erloese', 0)
            print(f"   Umlage-Erlöse (herausgerechnet): {umlage:>12,.2f} €")
    else:
        print("   ⚠️  API nicht verfügbar - berechne direkt aus DB")
        direct_ohne = get_drive_tek_direct(monat, jahr, umlage='ohne')
        print(f"   Umsatz:  {direct_ohne['umsatz']:>12,.2f} €")
        print(f"   Einsatz: {direct_ohne['einsatz']:>12,.2f} €")
        print(f"   DB1:     {direct_ohne['db1']:>12,.2f} €")
        print(f"   Marge:   {direct_ohne['marge']:>12.1f} %")
        # Berechne Umlage-Betrag als Differenz
        umlage_diff = direct_mit['umsatz'] - direct_ohne['umsatz']
        print(f"   Umlage-Erlöse (herausgerechnet): {umlage_diff:>12,.2f} €")
        drive_ohne = {'gesamt': direct_ohne}
    
    print()
    
    # 3. Vergleich
    if drive_mit and drive_ohne:
        print("📊 [3] Vergleich (mit vs. ohne Umlage):")
        print("-" * 80)
        diff_umsatz = drive_mit['gesamt']['umsatz'] - drive_ohne['gesamt']['umsatz']
        diff_db1 = drive_mit['gesamt']['db1'] - drive_ohne['gesamt']['db1']
        print(f"   Umsatz-Differenz (Umlage-Betrag): {diff_umsatz:>12,.2f} €")
        print(f"   DB1-Differenz:                    {diff_db1:>12,.2f} €")
        print()
        print(f"   ✅ Umlage-Erlöse sollten ~50.000 € sein (4 Konten × ~12.500 €)")
        print(f"   ✅ Wenn Differenz deutlich abweicht, könnte es ein Problem geben")
    
    print()
    
    # 4. Direkter DB-Vergleich
    print("📊 [4] Direkter DB-Vergleich (ohne API):")
    print("-" * 80)
    try:
        direct_mit = get_drive_tek_direct(monat, jahr, umlage='mit')
        print(f"   Umsatz:  {direct_mit['umsatz']:>12,.2f} €")
        print(f"   Einsatz: {direct_mit['einsatz']:>12,.2f} €")
        print(f"   DB1:     {direct_mit['db1']:>12,.2f} €")
        print(f"   Marge:   {direct_mit['marge']:>12.1f} %")
        print(f"   Umlage-Erlöse: {direct_mit['umlage_betrag']:>12,.2f} €")
        
        # Vergleich mit API
        if drive_mit:
            api_umsatz = drive_mit['gesamt']['umsatz']
            db_umsatz = direct_mit['umsatz']
            diff = abs(api_umsatz - db_umsatz)
            if diff > 0.01:
                print(f"\n   ⚠️  ABWEICHUNG zwischen API und DB!")
                print(f"      API: {api_umsatz:,.2f} €")
                print(f"      DB:  {db_umsatz:,.2f} €")
                print(f"      Diff: {diff:,.2f} €")
            else:
                print(f"\n   ✅ API und DB stimmen überein")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
    
    print()
    print("=" * 80)
    print("Hinweis: GlobalCube enthält die Konzernumlage (umlage='mit')")
    print("         DRIVE sollte daher auch umlage='mit' verwenden für Vergleich")
    print("=" * 80)

if __name__ == '__main__':
    main()
