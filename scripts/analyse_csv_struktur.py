"""
CSV-Struktur Analyse
====================
Analysiert die Struktur der Global Cube CSV
"""

import csv
import codecs

csv_path = '/opt/greiner-portal/docs/F.03 BWA Vorjahres-Vergleich (17).csv'

with codecs.open(csv_path, 'r', encoding='utf-16') as f:
    reader = csv.reader(f, delimiter='\t')
    rows = list(reader)
    
    print('CSV-Struktur Analyse:')
    print('=' * 80)
    
    # Header-Zeilen
    for i in range(min(4, len(rows))):
        print(f'\nZeile {i+1}:')
        for j, cell in enumerate(rows[i][:25]):  # Erste 25 Spalten
            if cell.strip():
                print(f'  [{j:2d}] \"{cell[:60]}\"')
    
    # Zeile 4: Neuwagen
    if len(rows) > 3:
        print(f'\nZeile 4 (Neuwagen) - Alle Spalten:')
        row4 = rows[3]
        for j, cell in enumerate(row4):
            cell_clean = cell.strip()
            if cell_clean and (cell_clean.replace(',', '').replace('.', '').replace('-', '').isdigit() or '444' in cell_clean or '537' in cell_clean):
                print(f'  [{j:2d}] \"{cell_clean}\"')
    
    # Zeile 5: Gebrauchtwagen
    if len(rows) > 4:
        print(f'\nZeile 5 (Gebrauchtwagen) - Alle Spalten:')
        row5 = rows[4]
        for j, cell in enumerate(row5):
            cell_clean = cell.strip()
            if cell_clean and (cell_clean.replace(',', '').replace('.', '').replace('-', '').isdigit() or '625' in cell_clean or '614' in cell_clean):
                print(f'  [{j:2d}] \"{cell_clean}\"')

