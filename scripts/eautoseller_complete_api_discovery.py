#!/usr/bin/env python3
"""
eAutoseller Komplette API-Entdeckung
Testet alle gefundenen Endpoints mit verschiedenen Parametern
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlencode
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

def test_dataapi_variants():
    """Testet dataApi.asp mit verschiedenen Parametern"""
    print("=" * 60)
    print("DATAAPI.ASP VARIANTEN TEST")
    print("=" * 60)
    
    base_url = f"{BASE_URL}administration/modules/carData/dataApi.asp"
    
    # Verschiedene Parameter-Kombinationen
    param_variants = [
        {'AussSort': '1'},
        {'format': 'json'},
        {'format': 'xml'},
        {'output': 'json'},
        {'output': 'xml'},
        {'type': 'json'},
        {'type': 'xml'},
        {'AussSort': '1', 'format': 'json'},
        {'AussSort': '1', 'output': 'json'},
        {'AussSort': '1', 'type': 'json'},
    ]
    
    working = []
    
    for params in param_variants:
        url = f"{base_url}?{urlencode(params)}"
        try:
            resp = session.get(url, timeout=5)
            
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', '')
                print(f"✅ {params}")
                print(f"   Type: {content_type}, Size: {len(resp.text)}")
                
                # Prüfe ob JSON
                if 'json' in content_type.lower() or resp.text.strip().startswith('{') or resp.text.strip().startswith('['):
                    try:
                        data = json.loads(resp.text)
                        print(f"   → JSON: {list(data.keys())[:5] if isinstance(data, dict) else f'Array[{len(data)}]'}")
                        working.append({
                            'url': url,
                            'params': params,
                            'format': 'json',
                            'data': data
                        })
                    except:
                        pass
                # Prüfe ob XML
                elif 'xml' in content_type.lower() or resp.text.strip().startswith('<'):
                    print(f"   → XML")
                    working.append({
                        'url': url,
                        'params': params,
                        'format': 'xml',
                        'sample': resp.text[:500]
                    })
                else:
                    # Prüfe ob Daten im HTML
                    if len(resp.text) < 10000:  # Kleine Responses könnten Daten sein
                        print(f"   → HTML (klein): {resp.text[:200]}")
        except:
            pass
    
    return working

def search_all_asp_pages():
    """Durchsucht alle ASP-Seiten nach API-Hinweisen"""
    print("\n" + "=" * 60)
    print("ASP-SEITEN DURCHSUCHUNG")
    print("=" * 60)
    
    # Bekannte ASP-Seiten
    asp_pages = [
        'kfzuebersicht.asp',
        'anfragenuebersicht.asp',
        'kontaktuebersicht.asp',
        'useruebersicht.asp',
        'felgenuebersicht.asp',
        'kfzauss.asp',
        'start.asp',
        'navi.asp',
    ]
    
    all_api_endpoints = set()
    
    for page in asp_pages:
        try:
            url = f"{BASE_URL}administration/{page}"
            resp = session.get(url, timeout=10)
            
            if resp.status_code == 200:
                # Suche nach API-Patterns
                patterns = re.findall(r'["\']([^"\']*(?:api|data|json|xml|ashx)[^"\']*(?:\.asp|\.ashx|\.json|\.xml)[^"\']*)["\']', resp.text, re.I)
                
                if patterns:
                    print(f"✅ {page}: {len(set(patterns))} API-Patterns")
                    for p in set(patterns)[:5]:
                        print(f"   → {p}")
                        all_api_endpoints.add(p)
        except:
            pass
    
    return all_api_endpoints

def test_all_endpoints(endpoints):
    """Testet alle gefundenen Endpoints"""
    print("\n" + "=" * 60)
    print("ALLE ENDPOINTS TEST")
    print("=" * 60)
    
    working = []
    
    for endpoint in sorted(endpoints)[:50]:
        # Normalisiere URL
        if endpoint.startswith('http'):
            url = endpoint
        elif endpoint.startswith('./'):
            url = urljoin(BASE_URL + 'administration/', endpoint.replace('./', ''))
        elif endpoint.startswith('../'):
            url = urljoin(BASE_URL + 'administration/', endpoint.replace('../', ''))
        elif endpoint.startswith('/'):
            url = urljoin(BASE_URL, endpoint)
        else:
            url = urljoin(BASE_URL + 'administration/', endpoint)
        
        try:
            resp = session.get(url, timeout=5, allow_redirects=False)
            
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', '')
                print(f"✅ {endpoint}")
                print(f"   Type: {content_type}, Size: {len(resp.text)}")
                
                # Prüfe Format
                is_json = False
                is_xml = False
                
                if 'json' in content_type.lower():
                    is_json = True
                elif resp.text.strip().startswith('{') or resp.text.strip().startswith('['):
                    try:
                        json.loads(resp.text)
                        is_json = True
                    except:
                        pass
                
                if 'xml' in content_type.lower() or resp.text.strip().startswith('<'):
                    is_xml = True
                
                if is_json:
                    try:
                        data = json.loads(resp.text)
                        print(f"   → JSON: {list(data.keys())[:5] if isinstance(data, dict) else f'Array[{len(data)}]'}")
                    except:
                        pass
                elif is_xml:
                    print(f"   → XML")
                
                working.append({
                    'endpoint': endpoint,
                    'url': url,
                    'status': 200,
                    'content_type': content_type,
                    'format': 'json' if is_json else ('xml' if is_xml else 'html'),
                    'size': len(resp.text),
                    'sample': resp.text[:500]
                })
        except:
            pass
    
    return working

def generate_complete_documentation(dataapi_results, all_endpoints, working_endpoints):
    """Erstellt komplette Dokumentation"""
    print("\n" + "=" * 60)
    print("KOMPLETTE API-DOKUMENTATION")
    print("=" * 60)
    
    print(f"\n📊 ZUSAMMENFASSUNG:")
    print(f"   dataApi.asp Varianten: {len(dataapi_results)}")
    print(f"   Gefundene Endpoints: {len(all_endpoints)}")
    print(f"   Funktionierende Endpoints: {len(working_endpoints)}")
    
    # JSON-Endpoints
    json_endpoints = [e for e in working_endpoints if e.get('format') == 'json']
    xml_endpoints = [e for e in working_endpoints if e.get('format') == 'xml']
    
    print(f"   JSON-Endpoints: {len(json_endpoints)}")
    print(f"   XML-Endpoints: {len(xml_endpoints)}")
    
    if json_endpoints:
        print(f"\n✅ JSON-APIs:")
        for ep in json_endpoints:
            print(f"\n   {ep['endpoint']}")
            print(f"   URL: {ep['url']}")
            print(f"   Size: {ep['size']} Bytes")
    
    if xml_endpoints:
        print(f"\n✅ XML-APIs:")
        for ep in xml_endpoints:
            print(f"\n   {ep['endpoint']}")
            print(f"   URL: {ep['url']}")
            print(f"   Size: {ep['size']} Bytes")
    
    # Speichere Dokumentation
    doc = {
        'dataapi_variants': dataapi_results,
        'all_endpoints': list(all_endpoints),
        'working_endpoints': working_endpoints,
        'json_endpoints': json_endpoints,
        'xml_endpoints': xml_endpoints,
    }
    
    try:
        with open('/tmp/eautoseller_complete_api_docs.json', 'w', encoding='utf-8') as f:
            json.dump(doc, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n💾 Dokumentation gespeichert: /tmp/eautoseller_complete_api_docs.json")
    except Exception as e:
        print(f"\n⚠️  Fehler beim Speichern: {e}")
    
    return doc

if __name__ == '__main__':
    print("🔍 eAutoseller Komplette API-Entdeckung")
    print()
    
    if login():
        print("✅ Login erfolgreich!")
        
        # dataApi.asp Varianten testen
        dataapi_results = test_dataapi_variants()
        
        # Alle ASP-Seiten durchsuchen
        all_endpoints = search_all_asp_pages()
        
        # Alle Endpoints testen
        working_endpoints = test_all_endpoints(all_endpoints)
        
        # Dokumentation generieren
        doc = generate_complete_documentation(dataapi_results, all_endpoints, working_endpoints)
        
    else:
        print("❌ Login fehlgeschlagen")
    
    print("\n✅ Analyse abgeschlossen")

