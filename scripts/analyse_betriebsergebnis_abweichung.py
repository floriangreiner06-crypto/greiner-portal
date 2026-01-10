#!/usr/bin/env python3
"""
Analyse: Betriebsergebnis-Abweichung zwischen Globalcube und DRIVE BWA
=======================================================================
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import db_session, row_to_dict
from api.db_connection import convert_placeholders

# Import build_firma_standort_filter aus controlling_api
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Kopiere die Funktion direkt hier (oder importiere sie)
def build_firma_standort_filter(firma: str, standort: str):
    """
    Baut Filter für Firma und Standort.
    Returns: (firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, standort_name)
    """
    # Vereinfachte Version für Analyse
    if firma == '0' and standort == '0':
        return ('', '', '', 'Alle Standorte')
    # TODO: Vollständige Implementierung falls nötig
    return ('', '', '', 'Alle Standorte')

# Globalcube Werte aus CSV (Zeile 46)
# Monat Aug./2025: 689679,69
# Jahr per Aug./2025: 321884,68
# VJ Monat Aug./2024: 552657,22
# VJ Jahr per Aug./2024: 686161,65

globalcube = {
    'monat': 689679.69,
    'jahr': 321884.68,
    'vj_monat': 552657.22,
    'vj_jahr': 686161.65
}

print("=" * 100)
print("ANALYSE: Betriebsergebnis-Abweichung Globalcube vs. DRIVE BWA")
print("=" * 100)
print(f"\nGlobalcube Werte (aus CSV):")
print(f"  Monat Aug./2025:     {globalcube['monat']:,.2f} €")
print(f"  Jahr per Aug./2025:  {globalcube['jahr']:,.2f} €")
print(f"  VJ Monat Aug./2024:  {globalcube['vj_monat']:,.2f} €")
print(f"  VJ Jahr per Aug./2024: {globalcube['vj_jahr']:,.2f} €")

# DRIVE BWA Werte berechnen
monat = 8  # August
jahr = 2025
firma = '0'  # Alle
standort = '0'  # Alle

# Monat Aug./2025
datum_von_monat = f"{jahr}-{monat:02d}-01"
datum_bis_monat = f"{jahr}-{monat+1:02d}-01"

# Jahr per Aug./2025 (WJ-Start: 1. September)
wj_start_jahr = jahr - 1  # Aug 2025 = WJ 2024/25 (Start Sep 2024)
datum_von_jahr = f"{wj_start_jahr}-09-01"
datum_bis_jahr = datum_bis_monat

# VJ Monat Aug./2024
datum_von_vj_monat = f"{jahr-1}-{monat:02d}-01"
datum_bis_vj_monat = f"{jahr-1}-{monat+1:02d}-01"

# VJ Jahr per Aug./2024 (WJ-Start: 1. September)
wj_start_vj_jahr = jahr - 2  # Aug 2024 = WJ 2023/24 (Start Sep 2023)
datum_von_vj_jahr = f"{wj_start_vj_jahr}-09-01"
datum_bis_vj_jahr = datum_bis_vj_monat

print(f"\n" + "=" * 100)
print("DRIVE BWA Berechnung:")
print("=" * 100)

with db_session() as conn:
    cursor = conn.cursor()
    
    # Filter
    firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, _ = build_firma_standort_filter(firma, standort)
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
    def berechne_betriebsergebnis(datum_von, datum_bis, label):
        """Berechnet Betriebsergebnis für einen Zeitraum"""
        # DB3 (Deckungsbeitrag 3)
        # = DB2 - Direkte Kosten
        # = (DB1 - Variable Kosten) - Direkte Kosten
        # = ((Umsatz - Einsatz) - Variable Kosten) - Direkte Kosten
        
        # Umsatz
        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
              {firma_filter_umsatz}
              {guv_filter}
        """), (datum_von, datum_bis))
        umsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        
        # Einsatz
        cursor.execute(convert_placeholders(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 700000 AND 799999
              {firma_filter_einsatz}
              {guv_filter}
        """), (datum_von, datum_bis))
        einsatz = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        
        # Variable Kosten
        cursor.execute(convert_placeholders(f"""
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
              )
              {firma_filter_kosten}
              {guv_filter}
        """), (datum_von, datum_bis))
        variable = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        
        # Direkte Kosten
        cursor.execute(convert_placeholders(f"""
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
                OR nominal_account_number BETWEEN 491000 AND 497999
              )
              {firma_filter_kosten}
              {guv_filter}
        """), (datum_von, datum_bis))
        direkte = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        
        # Indirekte Kosten
        cursor.execute(convert_placeholders(f"""
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
                    AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
              )
              {firma_filter_kosten}
              {guv_filter}
        """), (datum_von, datum_bis))
        indirekte = float(row_to_dict(cursor.fetchone())['wert'] or 0)
        
        # Berechnung
        db1 = umsatz - einsatz
        db2 = db1 - variable
        db3 = db2 - direkte
        be = db3 - indirekte
        
        return {
            'umsatz': umsatz,
            'einsatz': einsatz,
            'db1': db1,
            'variable': variable,
            'db2': db2,
            'direkte': direkte,
            'db3': db3,
            'indirekte': indirekte,
            'betriebsergebnis': be
        }
    
    # Monat Aug./2025
    print(f"\n1. Monat Aug./2025 ({datum_von_monat} - {datum_bis_monat}):")
    monat_werte = berechne_betriebsergebnis(datum_von_monat, datum_bis_monat, "Monat")
    print(f"   Umsatz:        {monat_werte['umsatz']:>15,.2f} €")
    print(f"   Einsatz:       {monat_werte['einsatz']:>15,.2f} €")
    print(f"   DB1:           {monat_werte['db1']:>15,.2f} €")
    print(f"   Variable:      {monat_werte['variable']:>15,.2f} €")
    print(f"   DB2:           {monat_werte['db2']:>15,.2f} €")
    print(f"   Direkte:       {monat_werte['direkte']:>15,.2f} €")
    print(f"   DB3:           {monat_werte['db3']:>15,.2f} €")
    print(f"   Indirekte:     {monat_werte['indirekte']:>15,.2f} €")
    print(f"   Betriebsergebnis: {monat_werte['betriebsergebnis']:>15,.2f} €")
    print(f"   Globalcube:    {globalcube['monat']:>15,.2f} €")
    diff_monat = monat_werte['betriebsergebnis'] - globalcube['monat']
    print(f"   Differenz:     {diff_monat:>15,.2f} € ({diff_monat/globalcube['monat']*100:+.2f}%)")
    
    # Jahr per Aug./2025
    print(f"\n2. Jahr per Aug./2025 ({datum_von_jahr} - {datum_bis_jahr}):")
    jahr_werte = berechne_betriebsergebnis(datum_von_jahr, datum_bis_jahr, "Jahr")
    print(f"   Umsatz:        {jahr_werte['umsatz']:>15,.2f} €")
    print(f"   Einsatz:       {jahr_werte['einsatz']:>15,.2f} €")
    print(f"   DB1:           {jahr_werte['db1']:>15,.2f} €")
    print(f"   Variable:      {jahr_werte['variable']:>15,.2f} €")
    print(f"   DB2:           {jahr_werte['db2']:>15,.2f} €")
    print(f"   Direkte:       {jahr_werte['direkte']:>15,.2f} €")
    print(f"   DB3:           {jahr_werte['db3']:>15,.2f} €")
    print(f"   Indirekte:     {jahr_werte['indirekte']:>15,.2f} €")
    print(f"   Betriebsergebnis: {jahr_werte['betriebsergebnis']:>15,.2f} €")
    print(f"   Globalcube:    {globalcube['jahr']:>15,.2f} €")
    diff_jahr = jahr_werte['betriebsergebnis'] - globalcube['jahr']
    print(f"   Differenz:     {diff_jahr:>15,.2f} € ({diff_jahr/globalcube['jahr']*100:+.2f}%)")
    
    # VJ Monat Aug./2024
    print(f"\n3. VJ Monat Aug./2024 ({datum_von_vj_monat} - {datum_bis_vj_monat}):")
    vj_monat_werte = berechne_betriebsergebnis(datum_von_vj_monat, datum_bis_vj_monat, "VJ Monat")
    print(f"   Betriebsergebnis: {vj_monat_werte['betriebsergebnis']:>15,.2f} €")
    print(f"   Globalcube:    {globalcube['vj_monat']:>15,.2f} €")
    diff_vj_monat = vj_monat_werte['betriebsergebnis'] - globalcube['vj_monat']
    print(f"   Differenz:     {diff_vj_monat:>15,.2f} € ({diff_vj_monat/globalcube['vj_monat']*100:+.2f}%)")
    
    # VJ Jahr per Aug./2024
    print(f"\n4. VJ Jahr per Aug./2024 ({datum_von_vj_jahr} - {datum_bis_vj_jahr}):")
    vj_jahr_werte = berechne_betriebsergebnis(datum_von_vj_jahr, datum_bis_vj_jahr, "VJ Jahr")
    print(f"   Betriebsergebnis: {vj_jahr_werte['betriebsergebnis']:>15,.2f} €")
    print(f"   Globalcube:    {globalcube['vj_jahr']:>15,.2f} €")
    diff_vj_jahr = vj_jahr_werte['betriebsergebnis'] - globalcube['vj_jahr']
    print(f"   Differenz:     {diff_vj_jahr:>15,.2f} € ({diff_vj_jahr/globalcube['vj_jahr']*100:+.2f}%)")
    
    print(f"\n" + "=" * 100)
    print("ZUSAMMENFASSUNG:")
    print("=" * 100)
    print(f"Monat Aug./2025:     {diff_monat:>15,.2f} € ({diff_monat/globalcube['monat']*100:+.2f}%)")
    print(f"Jahr per Aug./2025:  {diff_jahr:>15,.2f} € ({diff_jahr/globalcube['jahr']*100:+.2f}%)")
    print(f"VJ Monat Aug./2024: {diff_vj_monat:>15,.2f} € ({diff_vj_monat/globalcube['vj_monat']*100:+.2f}%)")
    print(f"VJ Jahr per Aug./2024: {diff_vj_jahr:>15,.2f} € ({diff_vj_jahr/globalcube['vj_jahr']*100:+.2f}%)")
