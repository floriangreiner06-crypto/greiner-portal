#!/usr/bin/env python3
"""
Findet die Tabelle mit Fahrzeugdaten
"""

from bs4 import BeautifulSoup
import re

with open('/tmp/kfzuebersicht.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Suche nach Tabellen
tables = soup.find_all('table')

# Suche nach Tabellen mit vielen Zeilen UND vielen Spalten
for i, table in enumerate(tables):
    rows = table.find_all('tr')
    if len(rows) > 5:
        # Prüfe erste Datenzeile
        if len(rows) > 1:
            first_data_row = rows[1]
            cells = first_data_row.find_all(['td', 'th'])
            if len(cells) > 10:  # Viele Spalten = wahrscheinlich Fahrzeugliste
                print(f'\n=== TABELLE {i+1} (Kandidat für Fahrzeugliste) ===')
                print(f'Zeilen: {len(rows)}')
                print(f'Spalten (erste Datenzeile): {len(cells)}')
                
                # Zeige Header
                if rows[0]:
                    header_cells = rows[0].find_all(['th', 'td'])
                    print(f'\nHeader ({len(header_cells)} Spalten):')
                    for j, h in enumerate(header_cells[:15]):
                        text = h.get_text(strip=True)
                        if text:
                            print(f'  {j}: {text[:50]}')
                
                # Zeige erste 3 Datenzeilen
                print(f'\nErste 3 Datenzeilen:')
                for row_idx in range(1, min(4, len(rows))):
                    row = rows[row_idx]
                    cells = row.find_all(['td', 'th'])
                    print(f'\nZeile {row_idx}:')
                    for j, cell in enumerate(cells[:15]):
                        text = cell.get_text(strip=True)
                        # Zeige nur Zellen mit Inhalt
                        if text and len(text.strip()) > 0:
                            print(f'  Spalte {j}: {text[:60]}')

# Alternative: Suche nach divs mit class="vehicle" oder ähnlich
divs_with_vehicle = soup.find_all('div', class_=lambda x: x and ('vehicle' in str(x).lower() or 'fahrzeug' in str(x).lower() or 'kfz' in str(x).lower()))
print(f'\n=== DIVS MIT VEHICLE-KLASSEN: {len(divs_with_vehicle)} ===')

# Suche nach Links die auf Fahrzeuge verweisen
links = soup.find_all('a', href=re.compile(r'kfz|fahrzeug|vehicle', re.I))
print(f'\n=== LINKS ZU FAHRZEUGEN: {len(links)} ===')
if links:
    print('Beispiel-Links:')
    for link in links[:5]:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        print(f'  {href[:60]} -> {text[:40]}')

