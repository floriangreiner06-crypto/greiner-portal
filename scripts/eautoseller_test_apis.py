#!/usr/bin/env python3
"""
eAutoseller API-Test
Testet die gefundenen API-Endpoints
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import json
import warnings
warnings.filterwarnings('ignore')

BASE_URL = "https://greiner.eautoseller.de/"
USERNAME = "fGreiner"
PASSWORD = "fGreiner12"

session = requests.Session()
session.verify = False
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

def login():
    """Login"""
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

def test_startdata_api():
    """Testet startdata.asp API"""
    print("=" * 60)
    print("STARTDATA.ASP API TEST")
    print("=" * 60)
    
    # Verschiedene IDs testen (aus JavaScript gefunden: 201, 202, 225, etc.)
    test_ids = [201, 202, 225, 226, 227, 228, 229, 230]
    
    working_endpoints = []
    
    for test_id in test_ids:
        # Verschiedene time-Parameter
        for time in ['1926', '1737123456', '']:
            url = f"{BASE_URL}administration/startdata.asp?id={test_id}&time={time}"
            
            try:
                resp = session.get(url, timeout=5)
                
                if resp.status_code == 200:
                    print(f"✅ id={test_id}, time={time}")
                    print(f"   Type: {resp.headers.get('Content-Type', 'N/A')}, Size: {len(resp.text)}")
                    print(f"   Response: {resp.text[:200]}")
                    
                    working_endpoints.append({
                        'url': url,
                        'id': test_id,
                        'time': time,
                        'status': 200,
                        'content_type': resp.headers.get('Content-Type', ''),
                        'size': len(resp.text),
                        'response': resp.text
                    })
                    break  # Erste funktionierende Variante reicht
                elif resp.status_code == 401:
                    print(f"🔒 id={test_id} - Auth (401)")
                elif resp.status_code != 404:
                    print(f"⚠️  id={test_id} - Status: {resp.status_code}")
            except Exception as e:
                pass
    
    return working_endpoints

def test_kfzuebersicht():
    """Testet kfzuebersicht.asp (Fahrzeugliste)"""
    print("\n" + "=" * 60)
    print("KFZUEBERSICHT.ASP TEST")
    print("=" * 60)
    
    # Verschiedene Parameter-Kombinationen
    test_urls = [
        f"{BASE_URL}administration/kfzuebersicht.asp?start=1&txtAktiv=1",
        f"{BASE_URL}administration/kfzuebersicht.asp?start=1&txtAktiv=1&txtOrder=kfz_preis%20ASC",
        f"{BASE_URL}administration/kfzuebersicht.asp?ufilid=&txtorder=6",
    ]
    
    working = []
    
    for url in test_urls:
        try:
            resp = session.get(url, timeout=10)
            
            if resp.status_code == 200:
                print(f"✅ {url}")
                print(f"   Size: {len(resp.text)} Bytes")
                
                # Suche nach JSON/XML in Response
                if 'json' in resp.headers.get('Content-Type', '').lower():
                    try:
                        data = resp.json()
                        print(f"   → JSON: {list(data.keys())[:5]}")
                    except:
                        pass
                
                # Suche nach API-Calls im HTML
                patterns = re.findall(r'["\']([^"\']*(?:api|data|json|xml|asp|ashx)[^"\']*)["\']', resp.text, re.I)
                if patterns:
                    print(f"   → {len(set(patterns))} API-Patterns gefunden")
                    for p in set(patterns)[:5]:
                        print(f"      {p}")
                
                working.append({
                    'url': url,
                    'status': 200,
                    'size': len(resp.text),
                    'patterns': list(set(patterns))
                })
        except Exception as e:
            print(f"   ❌ Fehler: {str(e)[:50]}")
    
    return working

def test_other_asp_pages():
    """Testet andere gefundene ASP-Seiten"""
    print("\n" + "=" * 60)
    print("ANDERE ASP-SEITEN TEST")
    print("=" * 60)
    
    test_pages = [
        'anfragenuebersicht.asp',
        'kontaktuebersicht.asp',
        'useruebersicht.asp',
        'felgenuebersicht.asp',
        'kfzauss.asp',
    ]
    
    working = []
    
    for page in test_pages:
        url = f"{BASE_URL}administration/{page}"
        try:
            resp = session.get(url, timeout=5)
            
            if resp.status_code == 200:
                print(f"✅ {page} - Size: {len(resp.text)}")
                working.append({
                    'page': page,
                    'url': url,
                    'status': 200,
                    'size': len(resp.text)
                })
        except:
            pass
    
    return working

def generate_api_documentation(startdata_results, kfz_results, other_results):
    """Erstellt API-Dokumentation"""
    print("\n" + "=" * 60)
    print("API-DOKUMENTATION")
    print("=" * 60)
    
    print(f"\n✅ GEFUNDENE APIs:")
    print(f"   startdata.asp: {len(startdata_results)} Endpoints")
    print(f"   kfzuebersicht.asp: {len(kfz_results)} Varianten")
    print(f"   Andere ASP-Seiten: {len(other_results)}")
    
    if startdata_results:
        print(f"\n📋 STARTDATA.ASP API:")
        for api in startdata_results:
            print(f"\n   Endpoint: {api['url']}")
            print(f"   ID: {api['id']}")
            print(f"   Response-Format: Pipe-separated (|)")
            print(f"   Sample: {api['response'][:150]}...")
    
    if kfz_results:
        print(f"\n📋 KFZUEBERSICHT.ASP:")
        for kfz in kfz_results:
            print(f"\n   URL: {kfz['url']}")
            print(f"   Size: {kfz['size']} Bytes")
            if kfz.get('patterns'):
                print(f"   API-Patterns: {len(kfz['patterns'])}")
    
    # Speichere Dokumentation
    doc = {
        'startdata_api': startdata_results,
        'kfzuebersicht': kfz_results,
        'other_pages': other_results
    }
    
    try:
        with open('/tmp/eautoseller_api_documentation.json', 'w', encoding='utf-8') as f:
            json.dump(doc, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n💾 Dokumentation gespeichert: /tmp/eautoseller_api_documentation.json")
    except Exception as e:
        print(f"\n⚠️  Fehler beim Speichern: {e}")

if __name__ == '__main__':
    print("🔍 eAutoseller API-Test")
    print()
    
    if login():
        print("✅ Login erfolgreich!")
        
        # startdata.asp testen
        startdata_results = test_startdata_api()
        
        # kfzuebersicht.asp testen
        kfz_results = test_kfzuebersicht()
        
        # Andere Seiten testen
        other_results = test_other_asp_pages()
        
        # Dokumentation generieren
        generate_api_documentation(startdata_results, kfz_results, other_results)
        
    else:
        print("❌ Login fehlgeschlagen")
    
    print("\n✅ Analyse abgeschlossen")

