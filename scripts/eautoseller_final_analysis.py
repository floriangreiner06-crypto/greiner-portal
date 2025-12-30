#!/usr/bin/env python3
"""
eAutoseller Finale Analyse
Analysiert kfzuebersicht.asp und sucht nach JSON/XML APIs
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, parse_qs
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

def analyze_kfzuebersicht():
    """Analysiert kfzuebersicht.asp detailliert"""
    print("=" * 60)
    print("KFZUEBERSICHT.ASP DETAILLIERTE ANALYSE")
    print("=" * 60)
    
    url = f"{BASE_URL}administration/kfzuebersicht.asp?start=1&txtAktiv=1"
    
    try:
        resp = session.get(url, timeout=15)
        print(f"✅ Status: {resp.status_code}, Size: {len(resp.text)} Bytes")
        
        # Suche nach JSON/XML Endpoints
        json_patterns = re.findall(r'["\']([^"\']*\.json[^"\']*)["\']', resp.text, re.I)
        xml_patterns = re.findall(r'["\']([^"\']*\.xml[^"\']*)["\']', resp.text, re.I)
        asp_data_patterns = re.findall(r'["\']([^"\']*data[^"\']*\.asp[^"\']*)["\']', resp.text, re.I)
        ashx_patterns = re.findall(r'["\']([^"\']*\.ashx[^"\']*)["\']', resp.text, re.I)
        
        print(f"\n🔍 API-PATTERNS:")
        print(f"   JSON: {len(set(json_patterns))}")
        print(f"   XML: {len(set(xml_patterns))}")
        print(f"   ASP Data: {len(set(asp_data_patterns))}")
        print(f"   ASHX: {len(set(ashx_patterns))}")
        
        all_patterns = set(json_patterns + xml_patterns + asp_data_patterns + ashx_patterns)
        
        if all_patterns:
            print(f"\n📋 GEFUNDENE API-ENDPOINTS:")
            for p in sorted(all_patterns)[:30]:
                print(f"   → {p}")
        
        # Suche nach AJAX/Fetch Calls
        ajax_calls = re.findall(r'\.ajax\([^)]*url["\']?\s*[:=]\s*["\']([^"\']+)["\']', resp.text, re.I)
        fetch_calls = re.findall(r'fetch\(["\']([^"\']+)["\']', resp.text, re.I)
        xmlhttp_calls = re.findall(r'\.open\(["\'](GET|POST)["\'],\s*["\']([^"\']+)["\']', resp.text, re.I)
        
        print(f"\n📞 API-CALLS:")
        print(f"   AJAX: {len(set(ajax_calls))}")
        print(f"   Fetch: {len(set(fetch_calls))}")
        print(f"   XMLHttpRequest: {len(set([x[1] for x in xmlhttp_calls]))}")
        
        all_calls = set(ajax_calls + fetch_calls + [x[1] for x in xmlhttp_calls])
        
        if all_calls:
            print(f"\n📋 API-CALL-URLS:")
            for call in sorted(all_calls)[:30]:
                print(f"   → {call}")
        
        return {
            'url': url,
            'patterns': list(all_patterns),
            'calls': list(all_calls),
            'html_size': len(resp.text)
        }
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_json_xml_endpoints(patterns, calls):
    """Testet JSON/XML Endpoints"""
    print("\n" + "=" * 60)
    print("JSON/XML ENDPOINT TEST")
    print("=" * 60)
    
    # Alle Endpoints sammeln
    all_endpoints = set(patterns + calls)
    
    # Filter für JSON/XML/Data
    json_xml_endpoints = [e for e in all_endpoints if any(x in e.lower() for x in ['.json', '.xml', 'data', 'api', 'ashx'])]
    
    print(f"🧪 Teste {len(json_xml_endpoints)} JSON/XML/Data Endpoints...")
    
    working = []
    
    for endpoint in sorted(json_xml_endpoints)[:40]:
        # Normalisiere URL
        if endpoint.startswith('http'):
            url = endpoint
        elif endpoint.startswith('/'):
            url = urljoin(BASE_URL, endpoint)
        elif endpoint.startswith('../'):
            url = urljoin(BASE_URL + 'administration/', endpoint.replace('../', ''))
        else:
            url = urljoin(BASE_URL + 'administration/', endpoint)
        
        try:
            resp = session.get(url, timeout=5, allow_redirects=False)
            
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', '')
                print(f"✅ {endpoint}")
                print(f"   Type: {content_type}, Size: {len(resp.text)}")
                
                # Prüfe Format
                if 'json' in content_type.lower():
                    try:
                        data = resp.json()
                        print(f"   → JSON: Keys: {list(data.keys())[:5]}")
                    except:
                        print(f"   → JSON (invalid): {resp.text[:100]}")
                elif 'xml' in content_type.lower():
                    print(f"   → XML")
                    print(f"   → First line: {resp.text.split(chr(10))[0][:100]}")
                else:
                    # Prüfe ob JSON im Text
                    if resp.text.strip().startswith('{') or resp.text.strip().startswith('['):
                        try:
                            data = json.loads(resp.text)
                            print(f"   → JSON (detected): {list(data.keys())[:5] if isinstance(data, dict) else 'Array'}")
                        except:
                            pass
                
                working.append({
                    'endpoint': endpoint,
                    'url': url,
                    'status': 200,
                    'content_type': content_type,
                    'size': len(resp.text),
                    'sample': resp.text[:500]
                })
            elif resp.status_code == 401:
                print(f"🔒 {endpoint} - Auth (401)")
            elif resp.status_code == 403:
                print(f"🚫 {endpoint} - Verweigert (403)")
            elif resp.status_code != 404:
                if resp.status_code < 500:
                    print(f"⚠️  {endpoint} - Status: {resp.status_code}")
        except Exception as e:
            pass
    
    return working

def generate_final_documentation(kfz_analysis, working_endpoints):
    """Erstellt finale Dokumentation"""
    print("\n" + "=" * 60)
    print("FINALE DOKUMENTATION")
    print("=" * 60)
    
    print(f"\n📊 ZUSAMMENFASSUNG:")
    print(f"   kfzuebersicht.asp: {kfz_analysis['html_size'] if kfz_analysis else 0} Bytes")
    print(f"   API-Patterns gefunden: {len(kfz_analysis['patterns']) if kfz_analysis else 0}")
    print(f"   API-Calls gefunden: {len(kfz_analysis['calls']) if kfz_analysis else 0}")
    print(f"   Funktionierende Endpoints: {len(working_endpoints)}")
    
    if working_endpoints:
        print(f"\n✅ FUNKTIONIERENDE API-ENDPOINTS:")
        for ep in working_endpoints:
            print(f"\n   📍 {ep['endpoint']}")
            print(f"   URL: {ep['url']}")
            print(f"   Status: {ep['status']}")
            print(f"   Content-Type: {ep['content_type']}")
            print(f"   Size: {ep['size']} Bytes")
            if ep.get('sample'):
                sample = ep['sample'].replace('\n', ' ')[:200]
                print(f"   Sample: {sample}...")
    
    # Speichere finale Dokumentation
    doc = {
        'kfz_analysis': kfz_analysis,
        'working_endpoints': working_endpoints,
        'summary': {
            'total_endpoints': len(working_endpoints),
            'json_endpoints': len([e for e in working_endpoints if 'json' in e.get('content_type', '').lower()]),
            'xml_endpoints': len([e for e in working_endpoints if 'xml' in e.get('content_type', '').lower()]),
        }
    }
    
    try:
        with open('/tmp/eautoseller_final_api_docs.json', 'w', encoding='utf-8') as f:
            json.dump(doc, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n💾 Finale Dokumentation gespeichert: /tmp/eautoseller_final_api_docs.json")
    except Exception as e:
        print(f"\n⚠️  Fehler beim Speichern: {e}")
    
    return doc

if __name__ == '__main__':
    print("🔍 eAutoseller Finale Analyse")
    print()
    
    if login():
        print("✅ Login erfolgreich!")
        
        # kfzuebersicht.asp analysieren
        kfz_analysis = analyze_kfzuebersicht()
        
        if kfz_analysis:
            # JSON/XML Endpoints testen
            all_endpoints = set(kfz_analysis['patterns'] + kfz_analysis['calls'])
            working_endpoints = test_json_xml_endpoints(kfz_analysis['patterns'], kfz_analysis['calls'])
            
            # Finale Dokumentation
            doc = generate_final_documentation(kfz_analysis, working_endpoints)
        else:
            print("❌ kfzuebersicht.asp Analyse fehlgeschlagen")
    else:
        print("❌ Login fehlgeschlagen")
    
    print("\n✅ Analyse abgeschlossen")

