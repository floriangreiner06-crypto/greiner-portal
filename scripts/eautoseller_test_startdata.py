#!/usr/bin/env python3
"""
Testet startdata.asp mit korrekten Parametern
"""

import requests
from bs4 import BeautifulSoup
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
        print("✅ Login erfolgreich!")
        
        # start.asp laden um time-Parameter zu bekommen
        resp = session.get(BASE_URL + 'administration/start.asp')
        
        # time-Parameter extrahieren
        import re
        time_match = re.search(r'startdata\.asp\?id=\d+&time=(\d+)', resp.text)
        if time_match:
            time_param = time_match.group(1)
            print(f"✅ Time-Parameter gefunden: {time_param}")
        else:
            time_param = '4729'  # Fallback
        
        # IDs testen
        test_ids = [201, 202, 203, 204, 205, 206, 207, 210, 211, 212, 215, 225, 226, 228, 229, 231, 293, 294, 295, 296]
        
        print(f"\n🧪 Teste {len(test_ids)} startdata.asp Endpoints...")
        
        working = []
        
        for test_id in test_ids:
            url = f"{BASE_URL}administration/startdata.asp?id={test_id}&time={time_param}"
            
            try:
                resp = session.get(url, timeout=5)
                
                if resp.status_code == 200:
                    response_text = resp.text.strip()
                    
                    if response_text != "NoWarnCookie Found" and len(response_text) > 20:
                        print(f"✅ ID {test_id}: {len(response_text)} Bytes")
                        print(f"   → {response_text[:200]}")
                        working.append({
                            'id': test_id,
                            'url': url,
                            'response': response_text,
                            'size': len(response_text)
                        })
                    else:
                        print(f"⚠️  ID {test_id}: {response_text}")
            except Exception as e:
                pass
        
        print(f"\n✅ {len(working)} funktionierende Endpoints gefunden")
        
        if working:
            print(f"\n📋 ERGEBNISSE:")
            for w in working:
                print(f"\n   ID {w['id']}:")
                print(f"   URL: {w['url']}")
                print(f"   Response: {w['response'][:300]}...")

