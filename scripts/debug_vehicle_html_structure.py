#!/usr/bin/env python3
"""
Debug: Analysiert die HTML-Struktur von kfzuebersicht.asp detailliert
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.eautoseller_client import EAutosellerClient
from bs4 import BeautifulSoup
import re
import json

# Credentials
try:
    with open('config/credentials.json', 'r') as f:
        creds = json.load(f)
        if 'eautoseller' in creds:
            username = creds['eautoseller']['username']
            password = creds['eautoseller']['password']
        else:
            raise KeyError('eautoseller')
except:
    username = 'fGreiner'
    password = 'fGreiner12'

client = EAutosellerClient(username=username, password=password)
client.login()

url = client.BASE_URL + 'administration/kfzuebersicht.asp?start=1&txtAktiv=1'
resp = client.session.get(url, timeout=15)

soup = BeautifulSoup(resp.text, 'html.parser')

# Finde die Haupttabelle
tables = soup.find_all('table')
print(f"Gefundene Tabellen: {len(tables)}\n")

for i, table in enumerate(tables):
    rows = table.find_all('tr')
    if len(rows) < 5:
        continue
    
    print(f"=" * 80)
    print(f"TABELLE {i+1}: {len(rows)} Zeilen")
    print(f"=" * 80)
    
    # Header analysieren
    header_row = rows[0]
    header_cells = header_row.find_all(['th', 'td'])
    header_texts = [h.get_text(strip=True) for h in header_cells]
    
    print(f"\nHeader ({len(header_texts)} Spalten):")
    for j, h in enumerate(header_texts[:25]):
        if h:
            print(f"  {j:2d}: {h[:60]}")
    
    # Erste 3 Datenzeilen analysieren
    print(f"\nErste 3 Datenzeilen:")
    for row_idx in range(1, min(4, len(rows))):
        row = rows[row_idx]
        cells = row.find_all(['td', 'th'])
        cell_texts = [c.get_text(strip=True) for c in cells]
        
        print(f"\nZeile {row_idx} ({len(cells)} Spalten):")
        for j, text in enumerate(cell_texts[:25]):
            if text:
                # Prüfe ob es ein Link ist
                link = cells[j].find('a', href=True) if j < len(cells) else None
                link_info = f" [LINK: {link.get('href', '')[:40]}]" if link else ""
                print(f"  {j:2d}: {text[:60]}{link_info}")
        
        # Prüfe ob Zeile Links zu Fahrzeugdetails hat
        links = row.find_all('a', href=True)
        if links:
            print(f"  Links in Zeile:")
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if 'kfz' in href.lower() or 'detail' in href.lower():
                    print(f"    → {href[:80]}")
                    print(f"      Text: {text[:60]}")
    
    # Prüfe ob das die richtige Tabelle ist (viele Zeilen, viele Spalten)
    if len(rows) > 20 and len(header_cells) > 10:
        print(f"\n✅ Diese Tabelle sieht nach der Fahrzeugliste aus!")
        print(f"   Zeilen: {len(rows)}")
        print(f"   Spalten: {len(header_cells)}")
        break

# Suche nach Links zu Fahrzeugdetails
print("\n" + "=" * 80)
print("LINKS ZU FAHRZEUGDETAILS")
print("=" * 80)

all_links = soup.find_all('a', href=True)
vehicle_detail_links = []

for link in all_links:
    href = link.get('href', '')
    if 'kfzdetail' in href.lower() or ('detail' in href.lower() and 'intnr' in href.lower()):
        vehicle_detail_links.append({
            'href': href,
            'text': link.get_text(strip=True),
            'parent': link.find_parent('tr')
        })

print(f"Gefundene Links zu Fahrzeugdetails: {len(vehicle_detail_links)}\n")

if vehicle_detail_links:
    print("Erste 5 Links:")
    for i, link_info in enumerate(vehicle_detail_links[:5], 1):
        print(f"\n{i}. {link_info['href'][:80]}")
        print(f"   Text: {link_info['text'][:60]}")
        
        if link_info['parent']:
            cells = link_info['parent'].find_all(['td', 'th'])
            cell_texts = [c.get_text(strip=True) for c in cells]
            print(f"   Zeile mit {len(cells)} Spalten:")
            for j, text in enumerate(cell_texts[:15]):
                if text:
                    print(f"      {j:2d}: {text[:60]}")

