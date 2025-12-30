#!/usr/bin/env python3
"""
Extrahiert Hereinnahme-Datum aus kfzdetail.asp
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.eautoseller_client import EAutosellerClient
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime

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

# Hole erstes Fahrzeug aus der Liste
url = client.BASE_URL + 'administration/kfzuebersicht.asp?start=1&txtAktiv=1'
resp = client.session.get(url, timeout=15)
soup = BeautifulSoup(resp.text, 'html.parser')

# Finde ersten Link zu Fahrzeugdetails
detail_link = soup.find('a', href=re.compile(r'kfzdetail\.asp\?kfzID=', re.I))
if not detail_link:
    print("❌ Kein Fahrzeugdetail-Link gefunden")
    sys.exit(1)

detail_href = detail_link.get('href', '')
detail_url = client.BASE_URL + 'administration/' + detail_href if not detail_href.startswith('http') else detail_href

print(f"🔍 Analysiere Detail-Seite: {detail_url}\n")

detail_resp = client.session.get(detail_url, timeout=15)
detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')

# Suche nach "Hereinnahme" und extrahiere Datum
print("=" * 80)
print("EXTRAHIERE HEREINNAHME-DATUM")
print("=" * 80)

# Methode 1: Suche nach Text "Hereinnahme" und finde nächstes Datum
hereinnahme_found = False
hereinnahme_date = None

# Suche nach allen Elementen die "Hereinnahme" enthalten
hereinnahme_elements = detail_soup.find_all(string=re.compile(r'hereinnahme', re.I))

for elem in hereinnahme_elements:
    parent = elem.parent
    if not parent:
        continue
    
    # Suche in Parent und Geschwister-Elementen nach Datum
    search_text = parent.get_text()
    
    # Suche nach Datum im Text
    date_match = re.search(r'(\d{2})[.-](\d{2})[.-](\d{4})', search_text)
    if date_match:
        date_str = date_match.group(0)
        print(f"✅ Datum gefunden in 'Hereinnahme'-Kontext: {date_str}")
        
        # Parse Datum
        try:
            day, month, year = date_match.groups()
            hereinnahme_date = datetime(int(year), int(month), int(day)).date()
            hereinnahme_found = True
            print(f"   → Parsed: {hereinnahme_date}")
            break
        except:
            pass
    
    # Suche in nächsten Geschwister-Elementen
    next_sibling = parent.find_next_sibling()
    if next_sibling:
        sibling_text = next_sibling.get_text()
        date_match = re.search(r'(\d{2})[.-](\d{2})[.-](\d{4})', sibling_text)
        if date_match:
            date_str = date_match.group(0)
            print(f"✅ Datum gefunden in nächstem Element: {date_str}")
            try:
                day, month, year = date_match.groups()
                hereinnahme_date = datetime(int(year), int(month), int(day)).date()
                hereinnahme_found = True
                print(f"   → Parsed: {hereinnahme_date}")
                break
            except:
                pass

# Methode 2: Suche in Tabellen nach "Hereinnahme" und Datum in derselben Zeile
if not hereinnahme_found:
    print("\nMethode 2: Suche in Tabellen...")
    tables = detail_soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            cell_texts = [c.get_text(strip=True) for c in cells]
            row_text = ' '.join(cell_texts)
            
            # Prüfe ob Zeile "Hereinnahme" enthält
            if 'hereinnahme' in row_text.lower():
                print(f"   Zeile mit 'Hereinnahme' gefunden: {len(cells)} Spalten")
                
                # Suche nach Datum in dieser Zeile
                for text in cell_texts:
                    date_match = re.search(r'(\d{2})[.-](\d{2})[.-](\d{4})', text)
                    if date_match:
                        date_str = date_match.group(0)
                        print(f"   → Datum in Spalte: {date_str}")
                        try:
                            day, month, year = date_match.groups()
                            hereinnahme_date = datetime(int(year), int(month), int(day)).date()
                            hereinnahme_found = True
                            print(f"   → Parsed: {hereinnahme_date}")
                            break
                        except:
                            pass
                
                if hereinnahme_found:
                    break
        
        if hereinnahme_found:
            break

# Methode 3: Suche nach "Standtage" und extrahiere Datum
if not hereinnahme_found:
    print("\nMethode 3: Suche nach 'Standtage'...")
    standtage_elements = detail_soup.find_all(string=re.compile(r'standtage', re.I))
    
    for elem in standtage_elements:
        parent = elem.parent
        if not parent:
            continue
        
        search_text = parent.get_text()
        date_match = re.search(r'(\d{2})[.-](\d{2})[.-](\d{4})', search_text)
        if date_match:
            date_str = date_match.group(0)
            print(f"✅ Datum gefunden in 'Standtage'-Kontext: {date_str}")
            try:
                day, month, year = date_match.groups()
                hereinnahme_date = datetime(int(year), int(month), int(day)).date()
                hereinnahme_found = True
                print(f"   → Parsed: {hereinnahme_date}")
                break
            except:
                pass

if hereinnahme_found:
    print(f"\n✅ Hereinnahme-Datum erfolgreich extrahiert: {hereinnahme_date}")
    today = datetime.now().date()
    standzeit = (today - hereinnahme_date).days
    print(f"   Standzeit: {standzeit} Tage")
else:
    print("\n❌ Hereinnahme-Datum nicht gefunden")
    print("💾 HTML gespeichert für manuelle Analyse: /tmp/kfzdetail.html")
    with open('/tmp/kfzdetail.html', 'w', encoding='utf-8') as f:
        f.write(detail_resp.text)

