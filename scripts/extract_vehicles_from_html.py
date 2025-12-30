#!/usr/bin/env python3
"""
Extrahiert Fahrzeugdaten aus kfzuebersicht.html
Analysiert Links und Tabellen-Struktur
"""

from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs

with open('/tmp/kfzuebersicht.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Methode 1: Extrahiere Fahrzeugdaten aus Links
print('=== METHODE 1: LINKS ANALYSIEREN ===')
links = soup.find_all('a', href=re.compile(r'kfz|fahrzeug|vehicle|detail', re.I))
print(f'Gefundene Links: {len(links)}')

vehicle_links = []
for link in links:
    href = link.get('href', '')
    text = link.get_text(strip=True)
    
    # Suche nach Links die auf einzelne Fahrzeuge verweisen
    if 'kfz' in href.lower() and ('detail' in href.lower() or 'id=' in href.lower() or 'intnr=' in href.lower()):
        vehicle_links.append({
            'href': href,
            'text': text,
            'parent': link.parent.get_text(strip=True)[:100] if link.parent else ''
        })

print(f'Fahrzeug-Links: {len(vehicle_links)}')
if vehicle_links:
    print('Beispiele:')
    for v in vehicle_links[:5]:
        print(f"  {v['href'][:60]} -> {v['text'][:40]}")

# Methode 2: Suche nach Tabellen mit Fahrzeugdaten (viele Zeilen, viele Spalten)
print('\n=== METHODE 2: TABELLEN MIT FAHRZEUGDATEN ===')
tables = soup.find_all('table')

for i, table in enumerate(tables):
    rows = table.find_all('tr')
    if len(rows) > 20:  # Tabellen mit vielen Zeilen
        print(f'\nTabelle {i+1}: {len(rows)} Zeilen')
        
        # Analysiere Header
        if rows[0]:
            header = rows[0]
            header_cells = header.find_all(['th', 'td'])
            header_texts = [h.get_text(strip=True) for h in header_cells]
            
            # Prüfe ob Header Fahrzeug-relevante Spalten hat
            relevant_keywords = ['marke', 'modell', 'preis', 'hereinnahme', 'standzeit', 'intnr', 'vin']
            has_relevant = any(keyword in ' '.join(header_texts).lower() for keyword in relevant_keywords)
            
            if has_relevant or len(header_cells) > 15:
                print(f'  Header: {len(header_cells)} Spalten')
                print(f'  Header-Texts: {header_texts[:10]}')
                
                # Zeige erste 3 Datenzeilen
                for row_idx in range(1, min(4, len(rows))):
                    row = rows[row_idx]
                    cells = row.find_all(['td', 'th'])
                    cell_texts = [c.get_text(strip=True) for c in cells]
                    
                    # Prüfe ob Zeile Fahrzeugdaten enthält (Preis, Datum, Marke)
                    has_price = any('€' in t or (t.replace('.', '').replace(',', '').isdigit() and len(t) > 4) for t in cell_texts)
                    has_date = any(re.search(r'\d{2}[.-]\d{2}[.-]\d{4}', t) for t in cell_texts)
                    has_brand = any(brand in ' '.join(cell_texts) for brand in ['BMW', 'Mercedes', 'Audi', 'VW', 'Opel', 'Ford'])
                    
                    if has_price or has_date or has_brand:
                        print(f'\n  Zeile {row_idx} (Fahrzeug-Kandidat):')
                        print(f'    Spalten: {len(cells)}')
                        for j, text in enumerate(cell_texts[:10]):
                            if text:
                                print(f'      {j}: {text[:50]}')

# Methode 3: Suche nach divs mit Fahrzeugdaten
print('\n=== METHODE 3: DIVS MIT FAHRZEUGDATEN ===')
# Suche nach divs die Preise oder Daten enthalten
all_divs = soup.find_all('div')
vehicle_divs = []

for div in all_divs:
    text = div.get_text()
    # Prüfe ob div Fahrzeugdaten enthält
    has_price = '€' in text and re.search(r'\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*€', text)
    has_date = re.search(r'\d{2}[.-]\d{2}[.-]\d{4}', text)
    has_brand = any(brand in text for brand in ['BMW', 'Mercedes', 'Audi', 'VW', 'Opel'])
    
    if (has_price or has_date) and has_brand:
        vehicle_divs.append({
            'text': text[:200],
            'class': div.get('class', [])
        })

print(f'Gefundene Fahrzeug-divs: {len(vehicle_divs)}')
if vehicle_divs:
    print('Beispiele:')
    for v in vehicle_divs[:3]:
        print(f"  {v['text'][:100]}")

