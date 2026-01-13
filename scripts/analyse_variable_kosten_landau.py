#!/usr/bin/env python3
"""
Variable Kosten Konten-Analyse - Landau
Extrahiert alle Konten die DRIVE als Variable Kosten zählt (Landau, Dez 2025)

Erstellt: TAG 184
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_connection import get_db
from collections import defaultdict
import json
from pathlib import Path

def analyse_variable_kosten_landau():
    """Analysiert Variable Kosten Konten für Landau"""
    print("=" * 80)
    print("VARIABLE KOSTEN KONTEN-ANALYSE - LANDAU (Dez 2025)")
    print("=" * 80)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # DRIVE Variable Kosten Query für Landau
    query = """
        SELECT 
            nominal_account_number,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
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
          AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'
          AND subsidiary_to_company_ref = 1
        GROUP BY nominal_account_number
        ORDER BY nominal_account_number;
    """
    
    datum_von = '2025-12-01'
    datum_bis = '2026-01-01'
    
    cursor.execute(query, (datum_von, datum_bis))
    rows = cursor.fetchall()
    
    konten = {}
    konten_bereiche = defaultdict(float)
    gesamt_summe = 0
    
    print(f"\n=== Konten-Aufschlüsselung (Landau, Dez 2025) ===\n")
    print(f"Zeitraum: {datum_von} bis {datum_bis}\n")
    
    for row in rows:
        konto = row[0]
        wert = float(row[1] or 0)
        
        if abs(wert) > 0.01:  # Nur Konten mit Werten > 0,01 €
            konten[konto] = wert
            gesamt_summe += wert
            
            # Gruppiere nach Konten-Bereichen
            if 415100 <= konto <= 415199:
                konten_bereiche['4151xx (Provisionen Finanz-Vermittlung)'] += wert
            elif 435500 <= konto <= 435599:
                konten_bereiche['4355xx (Trainingskosten)'] += wert
            elif 455000 <= konto <= 456999:
                konten_bereiche['455xx-456xx (Fahrzeugkosten)'] += wert
            elif 487000 <= konto <= 487099:
                konten_bereiche['4870x (Werbekosten)'] += wert
            elif 491000 <= konto <= 497899:
                konten_bereiche['491xx-497xx (Fertigmachen, Provisionen, Kulanz)'] += wert
    
    # Zeige Konten-Bereiche
    print("Konten-Bereiche:")
    print("-" * 80)
    for bereich, summe in sorted(konten_bereiche.items()):
        print(f"  {bereich:<50} {summe:>15,.2f} €")
    print("-" * 80)
    print(f"  {'GESAMT':<50} {gesamt_summe:>15,.2f} €")
    print()
    
    # Zeige Top 20 Konten
    print("Top 20 Konten (nach Wert):")
    print("-" * 80)
    sorted_konten = sorted(konten.items(), key=lambda x: abs(x[1]), reverse=True)
    for konto, wert in sorted_konten[:20]:
        # Bestimme Bereich
        if 415100 <= konto <= 415199:
            bereich = "4151xx"
        elif 435500 <= konto <= 435599:
            bereich = "4355xx"
        elif 455000 <= konto <= 456999:
            bereich = "455xx-456xx"
        elif 487000 <= konto <= 487099:
            bereich = "4870x"
        elif 491000 <= konto <= 497899:
            bereich = "491xx-497xx"
        else:
            bereich = "unbekannt"
        
        print(f"  {konto:>8} ({bereich:<15}) {wert:>15,.2f} €")
    
    if len(sorted_konten) > 20:
        print(f"  ... und {len(sorted_konten) - 20} weitere Konten")
    
    print()
    print(f"Gesamt: {len(konten)} Konten mit Werten")
    print(f"Summe: {gesamt_summe:,.2f} €")
    print(f"Excel 'Fertigmachen': 7.043,73 €")
    print(f"DRIVE Variable Kosten: 6.173,95 €")
    print(f"Differenz: {abs(gesamt_summe - 6173.95):,.2f} € ({((gesamt_summe - 6173.95) / 6173.95 * 100) if 6173.95 != 0 else 0:.2f}%)")
    
    # Speichere Ergebnisse
    output_dir = Path("/opt/greiner-portal/docs/globalcube_analysis")
    output_dir.mkdir(exist_ok=True)
    
    ergebnisse = {
        'datum_von': datum_von,
        'datum_bis': datum_bis,
        'gesamt_summe': gesamt_summe,
        'excel_fertigmachen': 7043.73,
        'drive_variable_kosten': 6173.95,
        'differenz': abs(gesamt_summe - 6173.95),
        'differenz_prozent': ((gesamt_summe - 6173.95) / 6173.95 * 100) if 6173.95 != 0 else 0,
        'konten_bereiche': dict(konten_bereiche),
        'konten': konten,
        'top_konten': dict(sorted_konten[:20])
    }
    
    json_path = output_dir / "kontenanalyse_variable_kosten_landau_tag184.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(ergebnisse, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Ergebnisse gespeichert: {json_path}")
    
    conn.close()
    
    return ergebnisse


if __name__ == '__main__':
    analyse_variable_kosten_landau()
