#!/usr/bin/env python3
"""
eAutoseller Komplette Analyse
Analysiert alle Aspekte der Website nach Login
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
    return 'err=' not in resp.url, resp

def analyze_main_page(html):
    """Analysiert die Hauptseite komplett"""
    print("=" * 60)
    print("HAUPTSEITE KOMPLETT-ANALYSE")
    print("=" * 60)
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Alle möglichen API-Hinweise
    findings = {
        'forms': [],
        'iframes': [],
        'scripts': [],
        'links': [],
        'meta_tags': [],
        'data_attributes': [],
    }
    
    # Formulare
    forms = soup.find_all('form')
    print(f"\n📋 {len(forms)} Formulare gefunden")
    for form in forms:
        action = form.get('action', '')
        method = form.get('method', 'GET')
        print(f"   → {method} {action}")
        findings['forms'].append({'action': action, 'method': method})
    
    # iframes
    iframes = soup.find_all('iframe')
    print(f"\n🖼️  {len(iframes)} iframes gefunden")
    for iframe in iframes:
        src = iframe.get('src', '')
        print(f"   → {src}")
        findings['iframes'].append(src)
    
    # Scripts (inline und extern)
    scripts = soup.find_all('script')
    print(f"\n📜 {len(scripts)} Script-Tags gefunden")
    for i, script in enumerate(scripts):
        src = script.get('src', '')
        content = script.string or ''
        
        if src:
            print(f"   [{i+1}] Extern: {src}")
            findings['scripts'].append({'type': 'extern', 'src': src})
        elif content:
            print(f"   [{i+1}] Inline: {len(content)} Zeichen")
            # Suche nach API-Hinweisen
            if any(x in content.lower() for x in ['api', 'ajax', 'fetch', 'xmlhttp', '.asp', '.ashx']):
                print(f"      → Enthält mögliche API-Hinweise")
                # Zeige relevante Zeilen
                lines = content.split('\n')
                relevant = [l.strip() for l in lines if any(x in l.lower() for x in ['api', 'ajax', 'fetch', '.asp', 'url', 'endpoint'])]
                for line in relevant[:5]:
                    print(f"         {line[:100]}")
            findings['scripts'].append({'type': 'inline', 'size': len(content)})
    
    # Links
    links = soup.find_all('a', href=True)
    print(f"\n🔗 {len(links)} Links gefunden")
    
    # Wichtige Links
    important = [a for a in links if any(x in a['href'].lower() for x in ['fahrzeug', 'vehicle', 'kfz', 'data', 'json', 'xml', 'api'])]
    print(f"   → {len(important)} API-relevante Links")
    for link in important[:10]:
        print(f"      {link['href']}")
        findings['links'].append(link['href'])
    
    # Meta-Tags
    meta_tags = soup.find_all('meta')
    print(f"\n🏷️  {len(meta_tags)} Meta-Tags gefunden")
    for meta in meta_tags:
        if meta.get('name') or meta.get('property'):
            findings['meta_tags'].append({
                'name': meta.get('name'),
                'property': meta.get('property'),
                'content': meta.get('content', '')[:100]
            })
    
    # Data-Attribute (oft für AJAX)
    data_attrs = soup.find_all(attrs=lambda x: x and any(k.startswith('data-') for k in x.keys()))
    print(f"\n📊 {len(data_attrs)} Elemente mit data-Attributen gefunden")
    for elem in data_attrs[:10]:
        attrs = {k: v for k, v in elem.attrs.items() if k.startswith('data-')}
        if attrs:
            print(f"   → {elem.name}: {list(attrs.keys())}")
            findings['data_attributes'].append(attrs)
    
    return findings

def test_common_endpoints():
    """Testet häufige eAutoseller Endpoints"""
    print("\n" + "=" * 60)
    print("HÄUFIGE ENDPOINTS TEST")
    print("=" * 60)
    
    common_endpoints = [
        # ASP-Seiten (typisch für eAutoseller)
        '/kfz/default.asp',
        '/kfz/list.asp',
        '/kfz/data.asp',
        '/kfz/json.asp',
        '/kfz/xml.asp',
        '/administration/data.asp',
        '/administration/json.asp',
        '/administration/xml.asp',
        
        # API-Varianten
        '/api/vehicles',
        '/api/fahrzeuge',
        '/api/data',
        '/rest/vehicles',
        
        # XML/JSON
        '/eaxml',
        '/flashxml',
        '/xml',
        '/json',
        
        # ASHX (ASP.NET Handler)
        '/handler.ashx',
        '/api.ashx',
        '/data.ashx',
    ]
    
    working = []
    
    for endpoint in common_endpoints:
        url = urljoin(BASE_URL, endpoint)
        try:
            resp = session.get(url, timeout=5, allow_redirects=False)
            
            if resp.status_code == 200:
                print(f"✅ {endpoint}")
                print(f"   Type: {resp.headers.get('Content-Type', 'N/A')}, Size: {len(resp.text)}")
                
                # Prüfe Format
                if 'json' in resp.headers.get('Content-Type', '').lower():
                    try:
                        data = resp.json()
                        print(f"   → JSON: {list(data.keys())[:5]}")
                    except:
                        pass
                
                working.append({
                    'url': url,
                    'endpoint': endpoint,
                    'status': 200,
                    'content_type': resp.headers.get('Content-Type', ''),
                    'size': len(resp.text),
                    'sample': resp.text[:300]
                })
            elif resp.status_code == 401:
                print(f"🔒 {endpoint} - Auth (401)")
                working.append({'url': url, 'endpoint': endpoint, 'auth_required': True})
            elif resp.status_code == 403:
                print(f"🚫 {endpoint} - Verweigert (403)")
            elif resp.status_code != 404:
                print(f"⚠️  {endpoint} - Status: {resp.status_code}")
        except:
            pass
    
    return working

def simulate_actions():
    """Simuliert typische Aktionen"""
    print("\n" + "=" * 60)
    print("AKTIONEN-SIMULATION")
    print("=" * 60)
    
    # Versuche verschiedene Seiten zu öffnen
    action_urls = [
        '/kfz/',
        '/kfz/default.asp',
        '/administration/',
        '/administration/index.asp',
    ]
    
    all_patterns = set()
    
    for url in action_urls:
        full_url = urljoin(BASE_URL, url)
        try:
            print(f"\n📄 Lade: {full_url}")
            resp = session.get(full_url, timeout=10)
            
            if resp.status_code == 200:
                # Suche nach API-Patterns
                patterns = re.findall(r'["\']([^"\']*(?:api|data|json|xml|asp|ashx)[^"\']*)["\']', resp.text, re.I)
                if patterns:
                    print(f"   ✅ {len(patterns)} Patterns gefunden")
                    for p in patterns[:5]:
                        print(f"      → {p}")
                        all_patterns.add(p)
        except Exception as e:
            print(f"   ❌ Fehler: {str(e)[:50]}")
    
    return all_patterns

def generate_report(findings, working_endpoints, action_patterns):
    """Erstellt finalen Bericht"""
    print("\n" + "=" * 60)
    print("FINALER BERICHT")
    print("=" * 60)
    
    print(f"\n📊 ZUSAMMENFASSUNG:")
    print(f"   Formulare: {len(findings['forms'])}")
    print(f"   iframes: {len(findings['iframes'])}")
    print(f"   Scripts: {len(findings['scripts'])}")
    print(f"   Links: {len(findings['links'])}")
    print(f"   Working Endpoints: {len(working_endpoints)}")
    print(f"   Action Patterns: {len(action_patterns)}")
    
    if working_endpoints:
        print(f"\n✅ FUNKTIONIERENDE ENDPOINTS:")
        for ep in working_endpoints:
            if ep.get('status') == 200:
                print(f"\n   {ep['endpoint']}")
                print(f"   URL: {ep['url']}")
                print(f"   Type: {ep['content_type']}")
                print(f"   Size: {ep['size']} Bytes")
                if ep.get('sample'):
                    sample = ep['sample'].replace('\n', ' ')[:150]
                    print(f"   Sample: {sample}...")
    
    # Speichere Ergebnisse
    results = {
        'findings': findings,
        'working_endpoints': working_endpoints,
        'action_patterns': list(action_patterns)
    }
    
    try:
        with open('/tmp/eautoseller_complete_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n💾 Ergebnisse gespeichert: /tmp/eautoseller_complete_results.json")
    except Exception as e:
        print(f"\n⚠️  Fehler beim Speichern: {e}")
    
    return results

if __name__ == '__main__':
    print("🔍 eAutoseller Komplette Analyse")
    print()
    
    success, login_resp = login()
    if success:
        print("✅ Login erfolgreich!")
        
        # Hauptseite analysieren
        findings = analyze_main_page(login_resp.text)
        
        # Häufige Endpoints testen
        working_endpoints = test_common_endpoints()
        
        # Aktionen simulieren
        action_patterns = simulate_actions()
        
        # Bericht generieren
        results = generate_report(findings, working_endpoints, action_patterns)
        
    else:
        print("❌ Login fehlgeschlagen")
    
    print("\n✅ Analyse abgeschlossen")

