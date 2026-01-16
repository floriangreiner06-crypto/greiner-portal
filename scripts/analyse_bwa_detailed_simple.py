#!/usr/bin/env python3
"""
Detaillierte BWA Position-für-Position Analyse (Einfache Version)
===================================================================
TAG 196: Analysiert alle BWA-Positionen direkt via SQL

Ziel: Identifizieren der Ursache für 50.100,63 € Differenz im Betriebsergebnis (Dezember 2025)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

# GlobalCube Referenzwerte (aus Dokumentation TAG 188)
GLOBALCUBE_DEZEMBER_2025 = {
    'betriebsergebnis': -116248.00,
}

GLOBALCUBE_YTD_DEZEMBER_2025 = {
    'direkte': 659229.00,
    'indirekte': 838944.00,
    'betriebsergebnis': -245733.00,
}


def format_currency(value):
    """Formatiert Betrag als Währung"""
    if value is None:
        return "N/A"
    return f"{value:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.')


def berechne_bwa_position(position_name, query, cursor, datum_von, datum_bis):
    """Berechnet eine BWA-Position"""
    cursor.execute(convert_placeholders(query), (datum_von, datum_bis))
    row = cursor.fetchone()
    if row:
        r = row_to_dict(row)
        wert = float(r.get('wert', 0) or 0)
        return wert
    return 0.0


def main():
    """Hauptfunktion"""
    print("="*80)
    print("DETAILLIERTE BWA POSITION-FÜR-POSITION ANALYSE")
    print("TAG 196 - Dezember 2025")
    print("="*80)
    
    monat = 12
    jahr = 2025
    
    datum_von = f"{jahr}-{monat:02d}-01"
    datum_bis = f"{jahr+1}-01-01"
    
    print(f"\nAnalyse für: {monat}/{jahr}")
    print(f"Zeitraum: {datum_von} bis {datum_bis}")
    print(f"Filter: Alle Firmen, Alle Standorte")
    
    # G&V-Filter (Abschlussbuchungen ausschließen)
    guv_filter = """AND NOT (
        (nominal_account_number BETWEEN 890000 AND 899999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9')
        OR (nominal_account_number BETWEEN 490000 AND 499999 AND substr(CAST(nominal_account_number AS TEXT), 4, 1) = '9')
    )"""
    
    # Gesamtsumme Filter (firma=0, standort=0)
    firma_filter_umsatz = "AND ((branch_number = 1 AND subsidiary_to_company_ref = 1) OR (branch_number = 2 AND subsidiary_to_company_ref = 2) OR (branch_number = 3 AND subsidiary_to_company_ref = 1))"
    firma_filter_einsatz = """AND (
        ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
        OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
        OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
    )"""
    firma_filter_kosten = "AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1))"
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        print(f"\n{'='*80}")
        print("1. GESAMT-BWA WERTE (MONAT DEZEMBER 2025)")
        print(f"{'='*80}")
        
        # Umsatz
        umsatz_query = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
              {firma_filter_umsatz}
              {guv_filter}
        """
        umsatz = berechne_bwa_position("Umsatz", umsatz_query, cursor, datum_von, datum_bis)
        print(f"Umsatz: {format_currency(umsatz)}")
        
        # Einsatz
        einsatz_query = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 700000 AND 799999
              AND nominal_account_number != 743002
              {firma_filter_einsatz}
              {guv_filter}
        """
        einsatz = berechne_bwa_position("Einsatz", einsatz_query, cursor, datum_von, datum_bis)
        print(f"Einsatz: {format_currency(einsatz)}")
        
        db1 = umsatz - einsatz
        print(f"DB1 (Umsatz - Einsatz): {format_currency(db1)}")
        
        # Variable Kosten
        variable_query = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND (
                nominal_account_number BETWEEN 415100 AND 415199
                OR nominal_account_number BETWEEN 435500 AND 435599
                OR (nominal_account_number BETWEEN 455000 AND 456999
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                OR (nominal_account_number BETWEEN 487000 AND 487099
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                OR nominal_account_number BETWEEN 491000 AND 497899
                OR nominal_account_number BETWEEN 891000 AND 891099
              )
              AND (
                (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1)
                OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
                OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2 AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
              )
              {guv_filter}
        """
        variable = berechne_bwa_position("Variable Kosten", variable_query, cursor, datum_von, datum_bis)
        print(f"Variable Kosten: {format_currency(variable)}")
        
        db2 = db1 - variable
        print(f"DB2 (DB1 - Variable): {format_currency(db2)}")
        
        # Direkte Kosten
        direkte_query = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
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
                OR nominal_account_number BETWEEN 489000 AND 489999
                OR nominal_account_number BETWEEN 491000 AND 497999
              )
              {firma_filter_kosten}
              {guv_filter}
        """
        direkte = berechne_bwa_position("Direkte Kosten", direkte_query, cursor, datum_von, datum_bis)
        print(f"Direkte Kosten: {format_currency(direkte)}")
        
        db3 = db2 - direkte
        print(f"DB3 (DB2 - Direkte): {format_currency(db3)}")
        
        # Indirekte Kosten
        indirekte_query = f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
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
                    AND NOT (nominal_account_number BETWEEN 893200 AND 893299)
                    AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
              )
              {firma_filter_kosten}
              {guv_filter}
        """
        indirekte = berechne_bwa_position("Indirekte Kosten", indirekte_query, cursor, datum_von, datum_bis)
        print(f"Indirekte Kosten: {format_currency(indirekte)}")
        
        be = db3 - indirekte
        print(f"\nBetriebsergebnis: {format_currency(be)}")
        print(f"GlobalCube Referenz: {format_currency(GLOBALCUBE_DEZEMBER_2025.get('betriebsergebnis'))}")
        diff = be - GLOBALCUBE_DEZEMBER_2025.get('betriebsergebnis', 0)
        print(f"Differenz: {format_currency(diff)}")
        
        # Spezielle Konten prüfen
        print(f"\n{'='*80}")
        print("2. SPEZIELLE KONTEN PRÜFUNG")
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
                
                print(f"\n{bezeichnung} ({konto_von}-{konto_bis}):")
                print(f"  Wert: {format_currency(wert)}")
                print(f"  Anzahl Buchungen: {anzahl}")
        
        print(f"\n{'='*80}")
        print("ANALYSE ABGESCHLOSSEN")
        print(f"{'='*80}")


if __name__ == '__main__':
    main()
