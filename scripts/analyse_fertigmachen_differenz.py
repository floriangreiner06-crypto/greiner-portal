#!/usr/bin/env python3
"""
Analyse: Fertigmachen Differenz Landau
Findet welche Konten in Excel "Fertigmachen" enthalten sind, aber nicht in DRIVE Variable Kosten

Erstellt: TAG 184
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_connection import get_db
from collections import defaultdict
import json
from pathlib import Path

def analyse_fertigmachen_differenz():
    """Analysiert Fertigmachen Differenz"""
    print("=" * 80)
    print("FERTIGMACHEN DIFFERENZ-ANALYSE - LANDAU (Dez 2025)")
    print("=" * 80)
    
    conn = get_db()
    cursor = conn.cursor()
    
    datum_von = '2025-12-01'
    datum_bis = '2026-01-01'
    
    # Excel Fertigmachen = 7.043,73 €
    # DRIVE Variable Kosten = 6.173,95 €
    # Differenz = 869,78 €
    
    print(f"\nExcel Fertigmachen: 7.043,73 €")
    print(f"DRIVE Variable Kosten: 6.173,95 €")
    print(f"Differenz: 869,78 €\n")
    
    # 1. Alle Konten 491xx-497xx für Landau (ohne Filter)
    print("=== 1. Alle Konten 491xx-497xx (Landau, ohne Filter) ===\n")
    
    query_all = """
        SELECT 
            nominal_account_number,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 491000 AND 497899
          AND subsidiary_to_company_ref = 1
        GROUP BY nominal_account_number
        ORDER BY nominal_account_number;
    """
    
    cursor.execute(query_all, (datum_von, datum_bis))
    rows_all = cursor.fetchall()
    
    konten_all = {}
    for row in rows_all:
        konto = row[0]
        wert = float(row[1] or 0)
        if abs(wert) > 0.01:
            konten_all[konto] = wert
    
    summe_all = sum(konten_all.values())
    print(f"Summe alle 491xx-497xx: {summe_all:,.2f} €")
    print(f"Anzahl Konten: {len(konten_all)}\n")
    
    # 2. DRIVE Variable Kosten Konten (mit Filter 6. Ziffer='2')
    print("=== 2. DRIVE Variable Kosten Konten (6. Ziffer='2') ===\n")
    
    query_drive = """
        SELECT 
            nominal_account_number,
            SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as wert
        FROM loco_journal_accountings
        WHERE accounting_date >= %s AND accounting_date < %s
          AND nominal_account_number BETWEEN 491000 AND 497899
          AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'
          AND subsidiary_to_company_ref = 1
        GROUP BY nominal_account_number
        ORDER BY nominal_account_number;
    """
    
    cursor.execute(query_drive, (datum_von, datum_bis))
    rows_drive = cursor.fetchall()
    
    konten_drive = {}
    for row in rows_drive:
        konto = row[0]
        wert = float(row[1] or 0)
        if abs(wert) > 0.01:
            konten_drive[konto] = wert
    
    summe_drive = sum(konten_drive.values())
    print(f"Summe DRIVE (6. Ziffer='2'): {summe_drive:,.2f} €")
    print(f"Anzahl Konten: {len(konten_drive)}\n")
    
    # 3. Konten die in "alle" aber nicht in DRIVE sind
    print("=== 3. Konten die in 'alle' aber nicht in DRIVE sind ===\n")
    
    konten_nicht_in_drive = {k: v for k, v in konten_all.items() if k not in konten_drive}
    summe_nicht_in_drive = sum(konten_nicht_in_drive.values())
    
    print(f"Anzahl Konten: {len(konten_nicht_in_drive)}")
    print(f"Summe: {summe_nicht_in_drive:,.2f} €\n")
    
    # Gruppiere nach 6. Ziffer
    konten_nach_ziffer = defaultdict(list)
    for konto, wert in konten_nicht_in_drive.items():
        konto_str = str(konto)
        if len(konto_str) >= 6:
            ziffer = konto_str[5]
            konten_nach_ziffer[ziffer].append((konto, wert))
    
    print("Gruppiert nach 6. Ziffer:")
    for ziffer in sorted(konten_nach_ziffer.keys()):
        konten_list = konten_nach_ziffer[ziffer]
        summe_ziffer = sum(w for _, w in konten_list)
        print(f"  6. Ziffer='{ziffer}': {len(konten_list)} Konten, Summe: {summe_ziffer:,.2f} €")
    
    # 4. Suche nach Kombination die Excel-Wert ergibt
    print(f"\n=== 4. Suche nach Kombination die Excel-Wert ergibt ===\n")
    
    excel_wert = 7043.73
    ziel = excel_wert - summe_drive  # 2.825,35 €
    
    print(f"Excel Fertigmachen: {excel_wert:,.2f} €")
    print(f"DRIVE (6. Ziffer='2'): {summe_drive:,.2f} €")
    print(f"Ziel (Excel - DRIVE): {ziel:,.2f} €\n")
    
    # Prüfe verschiedene Kombinationen
    # Kombination 1: 6. Ziffer='1' Konten
    konten_ziffer_1 = [w for _, w in konten_nach_ziffer.get('1', [])]
    summe_ziffer_1 = sum(konten_ziffer_1)
    
    print(f"Kombination 1: 6. Ziffer='1'")
    print(f"  Summe: {summe_ziffer_1:,.2f} €")
    print(f"  Differenz zu Ziel: {abs(summe_ziffer_1 - ziel):,.2f} €")
    
    if abs(summe_ziffer_1 - ziel) < 100:
        print(f"  ✅ Nahe Ziel!")
        print(f"  Top Konten:")
        for konto, wert in sorted(konten_nach_ziffer.get('1', []), key=lambda x: abs(x[1]), reverse=True)[:10]:
            print(f"    {konto}: {wert:,.2f} €")
    
    # Kombination 2: Bestimmte Konten-Bereiche
    print(f"\nKombination 2: Bestimmte Konten-Bereiche")
    for bereich_start in [491, 492, 493, 494, 495, 496, 497]:
        konten_bereich = [(k, v) for k, v in konten_nicht_in_drive.items() 
                         if bereich_start * 1000 <= k < (bereich_start + 1) * 1000]
        if konten_bereich:
            summe_bereich = sum(v for _, v in konten_bereich)
            if abs(summe_bereich) > 100:
                diff = abs(summe_bereich - ziel)
                status = "✅" if diff < 100 else "⚠️"
                print(f"  {bereich_start}xx: {summe_bereich:,.2f} € (Diff: {diff:,.2f} €) {status}")
    
    # Kombination 3: Bestimmte Konten die zusammen ~ziel ergeben
    print(f"\nKombination 3: Suche nach Konten die zusammen ~ziel ergeben")
    
    # Sortiere Konten nach Wert
    konten_sorted = sorted(konten_nicht_in_drive.items(), key=lambda x: abs(x[1]), reverse=True)
    
    # Versuche verschiedene Kombinationen
    kandidaten = []
    for i, (konto, wert) in enumerate(konten_sorted[:20]):
        # Prüfe einzelne Konten
        if abs(wert - ziel) < 50:
            kandidaten.append(([konto], wert, abs(wert - ziel)))
        
        # Prüfe Kombinationen mit anderen Konten
        for j, (konto2, wert2) in enumerate(konten_sorted[i+1:i+6]):
            kombi_summe = wert + wert2
            if abs(kombi_summe - ziel) < 50:
                kandidaten.append(([konto, konto2], kombi_summe, abs(kombi_summe - ziel)))
    
    if kandidaten:
        kandidaten.sort(key=lambda x: x[2])  # Sortiere nach Differenz
        print(f"  Top Kandidaten:")
        for konten_list, summe_kombi, diff in kandidaten[:5]:
            konten_str = ', '.join(str(k) for k in konten_list)
            print(f"    Konten {konten_str}: {summe_kombi:,.2f} € (Diff: {diff:,.2f} €)")
    else:
        print(f"  Keine exakte Kombination gefunden")
    
    # Speichere Ergebnisse
    output_dir = Path("/opt/greiner-portal/docs/globalcube_analysis")
    output_dir.mkdir(exist_ok=True)
    
    ergebnisse = {
        'excel_fertigmachen': 7043.73,
        'drive_variable_kosten': 6173.95,
        'differenz': 869.78,
        'summe_all_491xx_497xx': summe_all,
        'summe_drive_6_ziffer_2': summe_drive,
        'summe_nicht_in_drive': summe_nicht_in_drive,
        'konten_nicht_in_drive': dict(konten_nicht_in_drive),
        'konten_nach_ziffer': {k: dict(v) for k, v in konten_nach_ziffer.items()}
    }
    
    json_path = output_dir / "fertigmachen_differenz_analyse_tag184.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(ergebnisse, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Ergebnisse gespeichert: {json_path}")
    
    conn.close()
    
    return ergebnisse


if __name__ == '__main__':
    analyse_fertigmachen_differenz()
