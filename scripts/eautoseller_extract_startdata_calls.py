#!/usr/bin/env python3
"""
Extrahiert startdata.asp Calls aus start.asp
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import warnings
warnings.filterwarnings('ignore')

BASE_URL = "https://greiner.eautoseller.de/"
USERNAME = "fGreiner"
PASSWORD = "fGreiner12"

session = requests.Session()
session.verify = False

def login():
    resp = session.get(BASE_URL)
    soup = BeautifulSoup(resp.text, 'html.parser')
    form = soup.find('form')
    
    login_data = {}
    for field in form.find_all(['input', 'select']):
        name = field.get('name')
        if not name:
            continue
        
        if field.name == 'select':
            options = field.find_all('option')
            if options:
                login_data[name] = options[0].get('value', options[0].text.strip())
        elif field.get('type') == 'text' and 'user' in name.lower():
            login_data[name] = USERNAME
        elif field.get('type') == 'password':
            login_data[name] = PASSWORD
        elif field.get('type') == 'checkbox' and field.get('checked'):
            login_data[name] = field.get('value', '1')
    
    resp = session.post(urljoin(BASE_URL, form.get('action', 'login.asp')), data=login_data)
    return 'err=' not in resp.url

if __name__ == '__main__':
    if login():
        resp = session.get(BASE_URL + 'administration/start.asp')
        
        # startdata.asp Calls finden
        startdata_calls = re.findall(r'startdata\.asp[^"\']*', resp.text, re.I)
        
        print("=== STARTDATA.ASP CALLS ===")
        for call in sorted(set(startdata_calls))[:50]:
            print(f"  {call}")
        
        # IDs extrahieren
        ids = re.findall(r'startdata\.asp\?id=(\d+)', resp.text, re.I)
        print(f"\n=== GEFUNDENE IDs ===")
        for id_val in sorted(set(ids)):
            print(f"  ID: {id_val}")

