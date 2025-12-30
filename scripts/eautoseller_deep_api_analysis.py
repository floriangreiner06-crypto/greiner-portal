#!/usr/bin/env python3
"""
eAutoseller Tiefe API-Analyse
Analysiert JavaScript-Dateien und verschiedene Seiten nach API-Calls
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
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
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'de-DE,de;q=0.9',
})

def login():
    """Login"""
    print("🔐 Login...")
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

def extract_all_api_patterns(content):
    """Extrahiert alle API-Patterns aus Content"""
    patterns = {
        'api_urls': set(),
        'ajax_calls': set(),
        'fetch_calls': set(),
        'xmlhttp': set(),
        'base_urls': set(),
        'endpoints': set(),
    }
    
    # API URLs
    for match in re.findall(r'["\'](/api/[^"\']+)["\']', content, re.I):
        patterns['api_urls'].add(match)
    for match in re.findall(r'["\'](api/[^"\']+)["\']', content, re.I):
        patterns['api_urls'].add('/' + match)
    
    # REST URLs
    for match in re.findall(r'["\'](/rest/[^"\']+)["\']', content, re.I):
        patterns['api_urls'].add(match)
    
    # XML/JSON URLs
    for match in re.findall(r'["\'](/(?:xml|json|soap)[^"\']*)["\']', content, re.I):
        patterns['api_urls'].add(match)
    
    # AJAX Calls
    for match in re.findall(r'\.ajax\([^)]*url["\']?\s*[:=]\s*["\']([^"\']+)["\']', content, re.I):
        patterns['ajax_calls'].add(match)
    for match in re.findall(r'\$\.(get|post)\(["\']([^"\']+)["\']', content, re.I):
        patterns['ajax_calls'].add(match[1])
    for match in re.findall(r'axios\.(get|post|put|delete)\(["\']([^"\']+)["\']', content, re.I):
        patterns['ajax_calls'].add(match[1])
    
    # Fetch Calls
    for match in re.findall(r'fetch\(["\']([^"\']+)["\']', content, re.I):
        patterns['fetch_calls'].add(match)
    for match in re.findall(r'fetch\(`([^`]+)`', content, re.I):
        patterns['fetch_calls'].add(match)
    
    # XMLHttpRequest
    for match in re.findall(r'\.open\(["\'](GET|POST|PUT|DELETE)["\'],\s*["\']([^"\']+)["\']', content, re.I):
        patterns['xmlhttp'].add(match[1])
    
    # Base URLs / Config
    for match in re.findall(r'(?:api|API)[_ ]?url["\']?\s*[:=]\s*["\']([^"\']+)["\']', content, re.I):
        patterns['base_urls'].add(match)
    for match in re.findall(r'baseURL["\']?\s*[:=]\s*["\']([^"\']+)["\']', content, re.I):
        patterns['base_urls'].add(match)
    for match in re.findall(r'endpoint["\']?\s*[:=]\s*["\']([^"\']+)["\']', content, re.I):
        patterns['endpoints'].add(match)
    
    # ASP/ASHX Endpoints (typisch für eAutoseller)
    for match in re.findall(r'["\']([^"\']*\.(?:asp|ashx|aspx)[^"\']*)["\']', content, re.I):
        if 'api' in match.lower() or 'data' in match.lower() or 'json' in match.lower():
            patterns['endpoints'].add(match)
    
    return patterns

def analyze_javascript_files(html_content, base_url):
    """Analysiert alle JavaScript-Dateien"""
    print("\n" + "=" * 60)
    print("JAVASCRIPT-DATEIEN ANALYSE")
    print("=" * 60)
    
    # JavaScript-Dateien finden
    js_files = re.findall(r'<script[^>]*src=["\']([^"\']*\.js[^"\']*)["\']', html_content, re.I)
    
    print(f"📜 {len(js_files)} JavaScript-Dateien gefunden")
    
    all_patterns = {
        'api_urls': set(),
        'ajax_calls': set(),
        'fetch_calls': set(),
        'xmlhttp': set(),
        'base_urls': set(),
        'endpoints': set(),
    }
    
    for js_file in js_files:
        try:
            if js_file.startswith('http'):
                js_url = js_file
            elif js_file.startswith('/'):
                js_url = urljoin(base_url, js_file)
            else:
                js_url = urljoin(base_url, js_file)
            
            print(f"\n   📄 {js_url}")
            
            resp = session.get(js_url, timeout=10)
            if resp.status_code == 200:
                patterns = extract_all_api_patterns(resp.text)
                
                # Patterns sammeln
                for key in all_patterns:
                    all_patterns[key].update(patterns[key])
                
                total = sum(len(v) for v in patterns.values())
                if total > 0:
                    print(f"      ✅ {total} API-Patterns gefunden")
                    if patterns['api_urls']:
                        print(f"         → API URLs: {list(patterns['api_urls'])[:3]}")
                    if patterns['ajax_calls']:
                        print(f"         → AJAX: {list(patterns['ajax_calls'])[:3]}")
        except Exception as e:
            pass
    
    return all_patterns

def explore_navigation(html_content, base_url):
    """Erkundet Navigation und findet weitere Seiten"""
    print("\n" + "=" * 60)
    print("NAVIGATION ERKUNDUNG")
    print("=" * 60)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()
    
    # Alle Links finden
    for tag in soup.find_all(['a', 'form', 'link']):
        href = tag.get('href') or tag.get('action')
        if href:
            if href.startswith('http'):
                links.add(href)
            elif href.startswith('/'):
                links.add(urljoin(base_url, href))
            elif not href.startswith('#'):
                links.add(urljoin(base_url, href))
    
    print(f"📎 {len(links)} Links gefunden")
    
    # Wichtige Seiten identifizieren
    important_keywords = ['fahrzeug', 'vehicle', 'kfz', 'auto', 'liste', 'list', 'verwaltung', 'admin', 'data', 'json', 'xml']
    important_links = [l for l in links if any(kw in l.lower() for kw in important_keywords)]
    
    print(f"🔗 {len(important_links)} wichtige Links gefunden")
    
    return important_links[:20]  # Erste 20 analysieren

def analyze_pages(links):
    """Analysiert mehrere Seiten"""
    print("\n" + "=" * 60)
    print("SEITEN-ANALYSE")
    print("=" * 60)
    
    all_patterns = {
        'api_urls': set(),
        'ajax_calls': set(),
        'fetch_calls': set(),
        'xmlhttp': set(),
        'base_urls': set(),
        'endpoints': set(),
    }
    
    for i, link in enumerate(links, 1):
        try:
            print(f"\n[{i}/{len(links)}] Analysiere: {link}")
            resp = session.get(link, timeout=10)
            
            if resp.status_code == 200:
                patterns = extract_all_api_patterns(resp.text)
                
                # Patterns sammeln
                for key in all_patterns:
                    all_patterns[key].update(patterns[key])
                
                total = sum(len(v) for v in patterns.values())
                if total > 0:
                    print(f"   ✅ {total} API-Patterns gefunden")
                    
                    # JavaScript-Dateien dieser Seite analysieren
                    js_patterns = analyze_javascript_files(resp.text, link)
                    for key in all_patterns:
                        all_patterns[key].update(js_patterns[key])
        except Exception as e:
            print(f"   ❌ Fehler: {str(e)[:50]}")
    
    return all_patterns

def test_api_endpoints(all_patterns):
    """Testet alle gefundenen API-Endpoints"""
    print("\n" + "=" * 60)
    print("API-ENDPOINT TEST")
    print("=" * 60)
    
    # Alle Endpoints sammeln
    all_endpoints = set()
    
    for pattern_set in all_patterns.values():
        for endpoint in pattern_set:
            if endpoint.startswith('/'):
                all_endpoints.add(urljoin(BASE_URL, endpoint))
            elif endpoint.startswith('http'):
                all_endpoints.add(endpoint)
            elif not endpoint.startswith('.'):
                all_endpoints.add(urljoin(BASE_URL, '/' + endpoint))
    
    # Bekannte eAutoseller Endpoints hinzufügen
    known_endpoints = [
        '/eaxml',
        '/flashxml',
        '/api/flashxml',
        '/kfz/data.asp',
        '/kfz/json.asp',
        '/kfz/xml.asp',
        '/administration/data.asp',
        '/administration/json.asp',
    ]
    
    for ep in known_endpoints:
        all_endpoints.add(urljoin(BASE_URL, ep))
    
    print(f"🧪 Teste {len(all_endpoints)} Endpoints...")
    
    working_apis = []
    
    for endpoint in sorted(all_endpoints)[:50]:  # Erste 50 testen
        try:
            resp = session.get(endpoint, timeout=5, allow_redirects=False)
            
            status = resp.status_code
            content_type = resp.headers.get('Content-Type', '')
            
            if status == 200:
                print(f"✅ {endpoint}")
                print(f"   Status: {status}, Type: {content_type}, Size: {len(resp.text)}")
                
                # Prüfe Format
                if 'json' in content_type.lower():
                    try:
                        data = resp.json()
                        print(f"   → JSON: Keys: {list(data.keys())[:5]}")
                    except:
                        pass
                elif 'xml' in content_type.lower():
                    print(f"   → XML-Format")
                    # Erste Zeile zeigen
                    first_line = resp.text.split('\n')[0][:100]
                    print(f"   → {first_line}")
                
                working_apis.append({
                    'url': endpoint,
                    'status': status,
                    'content_type': content_type,
                    'size': len(resp.text),
                    'sample': resp.text[:500] if len(resp.text) < 5000 else resp.text[:200]
                })
            elif status == 401:
                print(f"🔒 {endpoint} - Auth erforderlich (401)")
                working_apis.append({
                    'url': endpoint,
                    'status': status,
                    'auth_required': True
                })
            elif status == 403:
                print(f"🚫 {endpoint} - Zugriff verweigert (403)")
            elif status == 404:
                pass  # Stille 404s
            else:
                if status < 500:  # Nur Client-Fehler zeigen
                    print(f"⚠️  {endpoint} - Status: {status}")
        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            pass
    
    return working_apis

def generate_final_report(working_apis, all_patterns):
    """Erstellt finalen Bericht"""
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    
    print(f"\n📊 GEFUNDENE PATTERNS:")
    print(f"   API URLs: {len(all_patterns['api_urls'])}")
    print(f"   AJAX Calls: {len(all_patterns['ajax_calls'])}")
    print(f"   Fetch Calls: {len(all_patterns['fetch_calls'])}")
    print(f"   XMLHttpRequest: {len(all_patterns['xmlhttp'])}")
    print(f"   Base URLs: {len(all_patterns['base_urls'])}")
    print(f"   Endpoints: {len(all_patterns['endpoints'])}")
    
    print(f"\n✅ FUNKTIONIERENDE APIs: {len([a for a in working_apis if a.get('status') == 200])}")
    print(f"🔒 AUTH ERFORDERLICH: {len([a for a in working_apis if a.get('auth_required')])}")
    
    if working_apis:
        print(f"\n📋 API-DETAILS:")
        for api in working_apis:
            if api.get('status') == 200:
                print(f"\n   ✅ {api['url']}")
                print(f"      Type: {api['content_type']}")
                print(f"      Size: {api['size']} Bytes")
                if api.get('sample'):
                    sample = api['sample'].replace('\n', ' ')[:150]
                    print(f"      Sample: {sample}...")
    
    # Speichere Ergebnisse
    results = {
        'working_apis': working_apis,
        'patterns': {k: list(v) for k, v in all_patterns.items()}
    }
    
    return results

if __name__ == '__main__':
    print("🔍 eAutoseller Tiefe API-Analyse")
    print()
    
    if login():
        print("✅ Login erfolgreich!")
        
        # Hauptseite analysieren
        main_resp = session.get(BASE_URL + 'administration/index.asp')
        
        # JavaScript-Dateien analysieren
        js_patterns = analyze_javascript_files(main_resp.text, BASE_URL)
        
        # Navigation erkunden
        important_links = explore_navigation(main_resp.text, BASE_URL)
        
        # Weitere Seiten analysieren
        page_patterns = analyze_pages(important_links)
        
        # Alle Patterns kombinieren
        all_patterns = js_patterns
        for key in all_patterns:
            all_patterns[key].update(page_patterns[key])
        
        # API-Endpoints testen
        working_apis = test_api_endpoints(all_patterns)
        
        # Finaler Bericht
        results = generate_final_report(working_apis, all_patterns)
        
        # Ergebnisse speichern
        try:
            with open('/tmp/eautoseller_api_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Ergebnisse gespeichert: /tmp/eautoseller_api_results.json")
        except:
            pass
        
    else:
        print("❌ Login fehlgeschlagen")
    
    print("\n✅ Analyse abgeschlossen")

