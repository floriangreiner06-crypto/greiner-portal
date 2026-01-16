#!/usr/bin/env python3
"""
Detaillierte BWA Position-für-Position Analyse
==============================================
TAG 196: Analysiert alle BWA-Positionen und vergleicht mit GlobalCube

Ziel: Identifizieren der Ursache für 50.100,63 € Differenz im Betriebsergebnis (Dezember 2025)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.db_connection import get_db, convert_placeholders
from api.db_utils import db_session, row_to_dict, get_locosoft_connection
from api.controlling_api import _berechne_bwa_werte, _berechne_bwa_ytd, build_firma_standort_filter
from api.db_utils import get_guv_filter
from datetime import datetime

# GlobalCube Referenzwerte (aus Dokumentation TAG 188)
GLOBALCUBE_DEZEMBER_2025 = {
    'umsatz': None,  # Wird aus Analyse ermittelt
    'einsatz': None,
    'db1': None,
    'variable': None,
    'db2': None,
    'direkte': None,
    'db3': None,
    'indirekte': None,
    'betriebsergebnis': -116248.00,
    'neutral': None,
    'unternehmensergebnis': None
}

GLOBALCUBE_YTD_DEZEMBER_2025 = {
    'umsatz': None,
    'einsatz': None,
    'db1': None,
    'variable': None,
    'db2': None,
    'direkte': 659229.00,  # Aus TAG 182 Dokumentation
    'db3': None,
    'indirekte': 838944.00,  # Aus TAG 182 Dokumentation
    'betriebsergebnis': -245733.00,
    'neutral': None,
    'unternehmensergebnis': None
}


def format_currency(value):
    """Formatiert Betrag als Währung"""
    if value is None:
        return "N/A"
    return f"{value:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.')


def analyze_position(position_name, drive_value, globalcube_value=None):
    """Analysiert eine einzelne Position"""
    diff = None
    diff_pct = None
    
    if globalcube_value is not None and drive_value is not None:
        diff = drive_value - globalcube_value
        if globalcube_value != 0:
            diff_pct = (diff / abs(globalcube_value)) * 100
    
    status = "✅"
    if diff is not None:
        if abs(diff) > 1000:
            status = "🚨"
        elif abs(diff) > 100:
            status = "⚠️"
        elif abs(diff) > 10:
            status = "⚠️"
    
    print(f"\n{position_name}:")
    print(f"  DRIVE:      {format_currency(drive_value)}")
    if globalcube_value is not None:
        print(f"  GlobalCube:  {format_currency(globalcube_value)}")
        print(f"  Differenz:   {format_currency(diff)} ({diff_pct:+.2f}%)" if diff_pct is not None else f"  Differenz:   {format_currency(diff)}")
    print(f"  Status:     {status}")
    
    return {
        'position': position_name,
        'drive': drive_value,
        'globalcube': globalcube_value,
        'diff': diff,
        'diff_pct': diff_pct,
        'status': status
    }


def analyze_konten_detail(cursor, position_name, konto_ranges, datum_von, datum_bis, 
                          firma_filter, guv_filter, debit_credit_logic):
    """
    Analysiert einzelne Kontenbereiche für eine Position
    
    Args:
        cursor: DB-Cursor
        position_name: Name der Position (z.B. "Variable Kosten")
        konto_ranges: Liste von (von, bis) Tupeln für Kontenbereiche
        datum_von: Startdatum
        datum_bis: Enddatum
        firma_filter: Firma-Filter SQL
        guv_filter: G&V-Filter SQL
        debit_credit_logic: SQL-Logic für Debit/Credit (z.B. "CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END")
    """
    print(f"\n{'='*80}")
    print(f"DETAILLIERTE ANALYSE: {position_name}")
    print(f"{'='*80}")
    
    total = 0
    konten_details = []
    
    for von, bis in konto_ranges:
        query = f"""
            SELECT 
                nominal_account_number as konto,
                SUM({debit_credit_logic})/100.0 as wert,
                COUNT(*) as anzahl_buchungen
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN {von} AND {bis}
              {firma_filter}
              {guv_filter}
            GROUP BY nominal_account_number
            HAVING ABS(SUM({debit_credit_logic})) > 0
            ORDER BY ABS(SUM({debit_credit_logic})) DESC
            LIMIT 20
        """
        
        cursor.execute(convert_placeholders(query), (datum_von, datum_bis))
        rows = cursor.fetchall()
        
        bereich_summe = 0
        for row in rows:
            r = row_to_dict(row)
            konto = r['konto']
            wert = float(r['wert'] or 0)
            anzahl = int(r['anzahl_buchungen'] or 0)
            bereich_summe += wert
            
            konten_details.append({
                'konto': konto,
                'wert': wert,
                'anzahl': anzahl
            })
        
        if bereich_summe != 0:
            print(f"\n  Kontenbereich {von}-{bis}: {format_currency(bereich_summe)}")
            total += bereich_summe
    
    print(f"\n  GESAMT {position_name}: {format_currency(total)}")
    
    return total, konten_details


def main():
    """Hauptfunktion"""
    print("="*80)
    print("DETAILLIERTE BWA POSITION-FÜR-POSITION ANALYSE")
    print("TAG 196 - Dezember 2025")
    print("="*80)
    
    monat = 12
    jahr = 2025
    firma = '0'  # Alle
    standort = '0'  # Alle
    
    datum_von = f"{jahr}-{monat:02d}-01"
    datum_bis = f"{jahr+1}-01-01"
    
    print(f"\nAnalyse für: {monat}/{jahr}")
    print(f"Zeitraum: {datum_von} bis {datum_bis}")
    print(f"Filter: Firma={firma}, Standort={standort}")
    
    # Filter bauen
    firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, standort_name = build_firma_standort_filter(firma, standort)
    guv_filter = get_guv_filter()
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # 1. Gesamt-BWA berechnen
        print(f"\n{'='*80}")
        print("1. GESAMT-BWA WERTE")
        print(f"{'='*80}")
        
        bwa_werte = _berechne_bwa_werte(cursor, monat, jahr, firma, standort)
        bwa_ytd = _berechne_bwa_ytd(cursor, monat, jahr, firma, standort)
        
        results = []
        
        # Monat Dezember 2025
        print(f"\n{'='*80}")
        print("MONAT DEZEMBER 2025")
        print(f"{'='*80}")
        
        results.append(analyze_position("Umsatz", bwa_werte.get('umsatz')))
        results.append(analyze_position("Einsatz", bwa_werte.get('einsatz')))
        results.append(analyze_position("DB1 (Umsatz - Einsatz)", bwa_werte.get('db1')))
        results.append(analyze_position("Variable Kosten", bwa_werte.get('variable')))
        results.append(analyze_position("DB2 (DB1 - Variable)", bwa_werte.get('db2')))
        results.append(analyze_position("Direkte Kosten", bwa_werte.get('direkte')))
        results.append(analyze_position("DB3 (DB2 - Direkte)", bwa_werte.get('db3')))
        results.append(analyze_position("Indirekte Kosten", bwa_werte.get('indirekte')))
        results.append(analyze_position("Betriebsergebnis", bwa_werte.get('betriebsergebnis'), GLOBALCUBE_DEZEMBER_2025.get('betriebsergebnis')))
        results.append(analyze_position("Neutrales Ergebnis", bwa_werte.get('neutral')))
        results.append(analyze_position("Unternehmensergebnis", bwa_werte.get('unternehmensergebnis')))
        
        # YTD bis Dezember 2025
        print(f"\n{'='*80}")
        print("YTD BIS DEZEMBER 2025")
        print(f"{'='*80}")
        
        results.append(analyze_position("Umsatz YTD", bwa_ytd.get('umsatz')))
        results.append(analyze_position("Einsatz YTD", bwa_ytd.get('einsatz')))
        results.append(analyze_position("DB1 YTD", bwa_ytd.get('db1')))
        results.append(analyze_position("Variable Kosten YTD", bwa_ytd.get('variable')))
        results.append(analyze_position("DB2 YTD", bwa_ytd.get('db2')))
        results.append(analyze_position("Direkte Kosten YTD", bwa_ytd.get('direkte'), GLOBALCUBE_YTD_DEZEMBER_2025.get('direkte')))
        results.append(analyze_position("DB3 YTD", bwa_ytd.get('db3')))
        results.append(analyze_position("Indirekte Kosten YTD", bwa_ytd.get('indirekte'), GLOBALCUBE_YTD_DEZEMBER_2025.get('indirekte')))
        results.append(analyze_position("Betriebsergebnis YTD", bwa_ytd.get('betriebsergebnis'), GLOBALCUBE_YTD_DEZEMBER_2025.get('betriebsergebnis')))
        results.append(analyze_position("Neutrales Ergebnis YTD", bwa_ytd.get('neutral')))
        results.append(analyze_position("Unternehmensergebnis YTD", bwa_ytd.get('unternehmensergebnis')))
        
        # 2. Detaillierte Konten-Analyse für problematische Positionen
        print(f"\n{'='*80}")
        print("2. DETAILLIERTE KONTEN-ANALYSE")
        print(f"{'='*80}")
        
        # Variable Kosten - Kontenbereiche
        variable_kosten_ranges = [
            (415100, 415199),
            (435500, 435599),
            (455000, 456999),
            (487000, 487099),
            (491000, 497899),
            (891000, 891099)
        ]
        
        variable_total, variable_details = analyze_konten_detail(
            cursor, "Variable Kosten",
            variable_kosten_ranges,
            datum_von, datum_bis,
            firma_filter_kosten, guv_filter,
            "CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END"
        )
        
        # Direkte Kosten - Kontenbereiche
        # Direkte Kosten sind: 4xxxxx mit KST 1-7, aber ohne Variable Kosten
        # Wir analysieren die wichtigsten Bereiche
        direkte_kosten_ranges = [
            (400000, 400999),  # KST 1-7
            (410000, 410999),  # KST 1-7 (ohne 410021, 411xxx)
            (420000, 420999),  # KST 1-7
            (430000, 430999),  # KST 1-7
            (440000, 440999),  # KST 1-7
            (450000, 450999),  # KST 1-7
            (460000, 460999),  # KST 1-7
            (470000, 470999),  # KST 1-7
            (480000, 480999),  # KST 1-7 (ohne 489xxx)
        ]
        
        direkte_total, direkte_details = analyze_konten_detail(
            cursor, "Direkte Kosten",
            direkte_kosten_ranges,
            datum_von, datum_bis,
            firma_filter_kosten, guv_filter,
            "CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END"
        )
        
        # Indirekte Kosten - Kontenbereiche
        indirekte_kosten_ranges = [
            (400000, 499999),  # KST 0
            (424000, 424999),  # Spezielle Konten
            (438000, 438999),  # Spezielle Konten
            (498000, 499999),  # Umlagekosten (inkl. 498001)
            (891000, 896999),  # 89xxxx (ohne 8932xx, ohne 8910xx)
        ]
        
        indirekte_total, indirekte_details = analyze_konten_detail(
            cursor, "Indirekte Kosten",
            indirekte_kosten_ranges,
            datum_von, datum_bis,
            firma_filter_kosten, guv_filter,
            "CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END"
        )
        
        # 3. Spezielle Konten prüfen
        print(f"\n{'='*80}")
        print("3. SPEZIELLE KONTEN PRÜFUNG")
        print(f"{'='*80}")
        
        spezielle_konten = [
            (410021, "Gehälter Verkauf GW"),
            (411000, 411999, "Ausbildungsvergütung"),
            (489000, 489999, "Sonstige Kosten"),
            (498001, "Umlagekosten"),
            (743002, "EW Fremdleistungen für Kunden"),
        ]
        
        for konto_info in spezielle_konten:
            if len(konto_info) == 2:
                konto, bezeichnung = konto_info
                konto_von = konto
                konto_bis = konto
            else:
                konto_von, konto_bis, bezeichnung = konto_info
            
            query = f"""
                SELECT 
                    SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert,
                    COUNT(*) as anzahl
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN {konto_von} AND {konto_bis}
                  {firma_filter_kosten}
                  {guv_filter}
            """
            
            cursor.execute(convert_placeholders(query), (datum_von, datum_bis))
            row = cursor.fetchone()
            if row:
                r = row_to_dict(row)
                wert = float(r['wert'] or 0)
                anzahl = int(r['anzahl'] or 0)
                
                print(f"\n  {bezeichnung} ({konto_von}-{konto_bis}):")
                print(f"    Wert: {format_currency(wert)}")
                print(f"    Anzahl Buchungen: {anzahl}")
        
        # 4. Zusammenfassung
        print(f"\n{'='*80}")
        print("4. ZUSAMMENFASSUNG")
        print(f"{'='*80}")
        
        be_diff = bwa_werte.get('betriebsergebnis', 0) - (GLOBALCUBE_DEZEMBER_2025.get('betriebsergebnis') or 0)
        be_ytd_diff = bwa_ytd.get('betriebsergebnis', 0) - (GLOBALCUBE_YTD_DEZEMBER_2025.get('betriebsergebnis') or 0)
        
        print(f"\nBetriebsergebnis Monat Dezember 2025:")
        print(f"  DRIVE:      {format_currency(bwa_werte.get('betriebsergebnis'))}")
        print(f"  GlobalCube: {format_currency(GLOBALCUBE_DEZEMBER_2025.get('betriebsergebnis'))}")
        print(f"  Differenz:  {format_currency(be_diff)}")
        
        print(f"\nBetriebsergebnis YTD bis Dezember 2025:")
        print(f"  DRIVE:      {format_currency(bwa_ytd.get('betriebsergebnis'))}")
        print(f"  GlobalCube: {format_currency(GLOBALCUBE_YTD_DEZEMBER_2025.get('betriebsergebnis'))}")
        print(f"  Differenz:  {format_currency(be_ytd_diff)}")
        
        print(f"\n{'='*80}")
        print("ANALYSE ABGESCHLOSSEN")
        print(f"{'='*80}")


if __name__ == '__main__':
    main()
