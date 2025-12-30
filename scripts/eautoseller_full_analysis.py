#!/usr/bin/env python3
"""
eAutoseller Vollständige Analyse nach Login
Analysiert alle Seiten und sucht nach APIs
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

def find_all_links(html, base_url):
    """Findet alle Links"""
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    
    for tag in soup.find_all(['a', 'form', 'link', 'script', 'iframe']):
        href = tag.get('href') or tag.get('action') or tag.get('src')
        if href:
            if href.startswith('http'):
                links.add(href)
            elif href.startswith('/'):
                links.add(urljoin(base_url, href))
            elif not href.startswith('#'):
                links.add(urljoin(base_url, href))
    
    return links

def extract_api_calls(content):
    """Extrahiert API-Calls aus Content"""
    patterns = {
        'api_urls': set(),
        'ajax': set(),
        'fetch': set(),
        'xmlhttp': set(),
    }
    
    # API URLs
    for match in re.findall(r'["\'](/api/[^"\']+)["\']', content, re.I):
        patterns['api_urls'].add(match)
    
    # AJAX
    for match in re.findall(r'\.ajax\([^)]*url["\']?\s*[:=]\s*["\']([^"\']+)["\']', content, re.I):
        patterns['ajax'].add(match)
    
    # Fetch
    for match in re.findall(r'fetch\(["\']([^"\']+)["\']', content, re.I):
        patterns['fetch'].add(match)
    
    # XMLHttpRequest
    for match in re.findall(r'\.open\(["\'](GET|POST)["\'],\s*["\']([^"\']+)["\']', content, re.I):
        patterns['xmlhttp'].add(match[1])
    
    return patterns

def analyze_page(url):
    """Analysiert eine Seite"""
    try:
        resp = session.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        
        patterns = extract_api_calls(resp.text)
        links = find_all_links(resp.text, BASE_URL)
        
        return {
            'url': url,
            'status': resp.status_code,
            'patterns': patterns,
            'links': links,
            'html': resp.text[:5000]  # Erste 5000 Zeichen
        }
    except:
        return None

def explore_site():
    """Erkundet die Site"""
    print("\n" + "=" * 60)
    print("SITE-ERKUNDUNG")
    print("=" * 60)
    
    # Startseite nach Login
    main_page = analyze_page(BASE_URL + 'administration/index.asp')
    if main_page:
        print(f"✅ Hauptseite: {len(main_page['links'])} Links gefunden")
    
    # Alle Links sammeln
    all_links = set()
    if main_page:
        all_links.update(main_page['links'])
    
    # Wichtige Bereiche
    important_paths = [
        '/administration/',
        '/kfz/',
        '/fahrzeuge/',
        '/api/',
        '/xml/',
        '/json/',
        '/rest/',
    ]
    
    print(f"\n🔍 Analysiere wichtige Bereiche...")
    found_apis = set()
    
    for path in important_paths:
        url = urljoin(BASE_URL, path)
        page = analyze_page(url)
        if page:
            print(f"✅ {path} - Status: {page['status']}")
            all_links.update(page['links'])
            
            # API-Patterns sammeln
            for pattern_type, pattern_set in page['patterns'].items():
                if pattern_set:
                    print(f"   → {pattern_type}: {len(pattern_set)} gefunden")
                    found_apis.update(pattern_set)
    
    # Teste gefundene API-URLs
    print(f"\n🧪 Teste {len(found_apis)} gefundene API-URLs...")
    working_apis = []
    
    for api_url in sorted(found_apis)[:20]:
        if api_url.startswith('/'):
            full_url = urljoin(BASE_URL, api_url)
        else:
            full_url = api_url
        
        try:
            resp = session.get(full_url, timeout=5)
            if resp.status_code == 200:
                print(f"✅ {api_url} - Status: 200, Type: {resp.headers.get('Content-Type', 'N/A')}")
                working_apis.append({
                    'url': full_url,
                    'status': 200,
                    'content_type': resp.headers.get('Content-Type', ''),
                    'size': len(resp.text)
                })
            elif resp.status_code == 401:
                print(f"🔒 {api_url} - Auth erforderlich (401)")
            elif resp.status_code != 404:
                print(f"⚠️  {api_url} - Status: {resp.status_code}")
        except:
            pass
    
    return working_apis, all_links

def generate_report(working_apis):
    """Erstellt Bericht"""
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    
    print(f"\n✅ FUNKTIONIERENDE APIs: {len(working_apis)}")
    
    if working_apis:
        print("\n📋 API-DETAILS:")
        for api in working_apis:
            print(f"\n   URL: {api['url']}")
            print(f"   Status: {api['status']}")
            print(f"   Content-Type: {api['content_type']}")
            print(f"   Size: {api['size']} Bytes")
    
    print("\n💡 HINWEIS:")
    print("   APIs werden wahrscheinlich dynamisch via JavaScript geladen.")
    print("   Browser-Entwicklertools (Network-Tab) zeigen echte API-Calls.")

if __name__ == '__main__':
    print("🔍 eAutoseller Vollständige Analyse")
    
    if login():
        print("✅ Login erfolgreich!")
        working_apis, links = explore_site()
        generate_report(working_apis)
    else:
        print("❌ Login fehlgeschlagen")

