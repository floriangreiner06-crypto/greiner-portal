#!/usr/bin/env python3
"""
Debug-Script für Customer First Login-Analyse
"""

import sys
import os
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import re

# Projekt-Root zum Python-Pfad hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# SSL-Warnings unterdrücken
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://www.customer360psa.com"
LOGIN_URL = f"{BASE_URL}/s/login/"

session = requests.Session()
session.verify = False
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

# Login-Seite laden
login_params = {
    'language': 'en_US',
    'ec': '302',
    'startURL': '/s/'
}

print("Lade Login-Seite...")
resp = session.get(LOGIN_URL, params=login_params, timeout=15)
print(f"Status: {resp.status_code}")
print(f"URL: {resp.url}")
print(f"HTML-Länge: {len(resp.text)}")

# HTML speichern
html_file = project_root / "docs" / "customer_first_login_page.html"
html_file.parent.mkdir(parents=True, exist_ok=True)
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(resp.text)
print(f"HTML gespeichert: {html_file}")

# HTML parsen
soup = BeautifulSoup(resp.text, 'html.parser')

# Suche nach "ID Europe" oder "Europe"
print("\n=== Suche nach 'ID Europe' / 'Europe' ===")
europe_elements = soup.find_all(string=re.compile(r'Europe|ID Europe', re.I))
print(f"Gefunden: {len(europe_elements)} Elemente")
for i, elem in enumerate(europe_elements[:10]):
    parent = elem.parent
    print(f"\n{i+1}. Text: '{elem.strip()}'")
    print(f"   Tag: {parent.name if parent else 'None'}")
    print(f"   Attributes: {parent.attrs if parent else 'None'}")

# Suche nach Buttons
print("\n=== Alle Buttons ===")
buttons = soup.find_all('button')
print(f"Gefunden: {len(buttons)} Buttons")
for i, btn in enumerate(buttons[:10]):
    text = btn.get_text(strip=True)
    print(f"{i+1}. '{text}' - {btn.attrs}")

# Suche nach Links
print("\n=== Links mit 'Europe' ===")
links = soup.find_all('a', string=re.compile(r'Europe', re.I))
print(f"Gefunden: {len(links)} Links")
for i, link in enumerate(links[:10]):
    print(f"{i+1}. '{link.get_text(strip=True)}' - href: {link.get('href', 'N/A')}")

# Suche nach Forms
print("\n=== Alle Forms ===")
forms = soup.find_all('form')
print(f"Gefunden: {len(forms)} Forms")
for i, form in enumerate(forms):
    print(f"{i+1}. ID: {form.get('id', 'N/A')}, Action: {form.get('action', 'N/A')}")

# Suche nach Input-Feldern
print("\n=== Input-Felder ===")
inputs = soup.find_all('input')
print(f"Gefunden: {len(inputs)} Input-Felder")
for i, inp in enumerate(inputs[:20]):
    print(f"{i+1}. Type: {inp.get('type', 'N/A')}, Name: {inp.get('name', 'N/A')}, ID: {inp.get('id', 'N/A')}")
