#!/usr/bin/env python3
"""
eAutoseller Frame-Inhalte Analyse
Analysiert navi.asp und start.asp Frames
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

def analyze_frame(url, name):
    """Analysiert einen Frame"""
    print("=" * 60)
    print(f"FRAME: {name}")
    print("=" * 60)
    print(f"URL: {url}")
    
    try:
        resp = session.get(url, timeout=10)
        print(f"✅ Status: {resp.status_code}")
        print(f"✅ Size: {len(resp.text)} Bytes")
        print(f"✅ Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
        
        # HTML-Struktur
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Links finden
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        print(f"\n🔗 {len(links)} Links gefunden")
        
        # Wichtige Links
        important = [l for l in links if l and any(x in l.lower() for x in ['fahrzeug', 'vehicle', 'kfz', 'data', 'json', 'xml', 'api', 'asp', 'ashx'])]
        if important:
            print(f"   → {len(important)} API-relevante Links:")
            for link in important[:15]:
                print(f"      {link}")
        
        # Formulare
        forms = soup.find_all('form')
        print(f"\n📋 {len(forms)} Formulare gefunden")
        for form in forms:
            action = form.get('action', '')
            method = form.get('method', 'GET')
            print(f"   → {method} {action}")
        
        # Scripts
        scripts = soup.find_all('script')
        print(f"\n📜 {len(scripts)} Scripts gefunden")
        for i, script in enumerate(scripts):
            src = script.get('src', '')
            content = script.string or ''
            if src:
                print(f"   [{i+1}] Extern: {src}")
            elif content:
                print(f"   [{i+1}] Inline: {len(content)} Zeichen")
                # Suche nach API-Calls
                if any(x in content.lower() for x in ['api', 'ajax', 'fetch', 'xmlhttp', '.asp', '.ashx']):
                    print(f"      → Enthält API-Hinweise")
                    # Zeige relevante Zeilen
                    lines = content.split('\n')
                    relevant = [l.strip() for l in lines if any(x in l.lower() for x in ['api', 'ajax', 'fetch', '.asp', 'url', 'endpoint', 'data'])]
                    for line in relevant[:10]:
                        if len(line) > 0:
                            print(f"         {line[:120]}")
        
        # API-Patterns
        patterns = re.findall(r'["\']([^"\']*(?:api|data|json|xml|asp|ashx|ajax)[^"\']*)["\']', resp.text, re.I)
        unique_patterns = set(patterns)
        if unique_patterns:
            print(f"\n🔍 {len(unique_patterns)} API-Patterns gefunden:")
            for p in sorted(unique_patterns)[:20]:
                print(f"   → {p}")
        
        # JavaScript-Dateien
        js_files = re.findall(r'<script[^>]*src=["\']([^"\']*\.js[^"\']*)["\']', resp.text, re.I)
        if js_files:
            print(f"\n📄 {len(js_files)} JavaScript-Dateien:")
            for js in js_files[:10]:
                print(f"   → {js}")
        
        return {
            'url': url,
            'status': resp.status_code,
            'links': links,
            'important_links': important,
            'forms': [{'action': f.get('action'), 'method': f.get('method')} for f in forms],
            'scripts': len(scripts),
            'patterns': list(unique_patterns),
            'js_files': js_files
        }
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_links(links):
    """Testet gefundene Links"""
    print("\n" + "=" * 60)
    print("LINK-TEST")
    print("=" * 60)
    
    working = []
    
    for link in sorted(set(links))[:30]:
        if not link or link.startswith('#'):
            continue
        
        # Normalisiere URL
        if link.startswith('http'):
            url = link
        elif link.startswith('/'):
            url = urljoin(BASE_URL, link)
        elif link.startswith('javascript:'):
            continue
        else:
            url = urljoin(BASE_URL, link)
        
        try:
            resp = session.get(url, timeout=5, allow_redirects=False)
            
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', '')
                print(f"✅ {link}")
                print(f"   Type: {content_type}, Size: {len(resp.text)}")
                
                # Prüfe ob API-Response
                if 'json' in content_type.lower():
                    try:
                        data = resp.json()
                        print(f"   → JSON: {list(data.keys())[:5]}")
                    except:
                        pass
                elif 'xml' in content_type.lower():
                    print(f"   → XML")
                
                working.append({
                    'link': link,
                    'url': url,
                    'status': 200,
                    'content_type': content_type,
                    'size': len(resp.text),
                    'sample': resp.text[:300]
                })
            elif resp.status_code == 401:
                print(f"🔒 {link} - Auth (401)")
            elif resp.status_code != 404:
                if resp.status_code < 500:
                    print(f"⚠️  {link} - Status: {resp.status_code}")
        except:
            pass
    
    return working

if __name__ == '__main__':
    print("🔍 eAutoseller Frame-Analyse")
    print()
    
    if login():
        print("✅ Login erfolgreich!")
        
        # Frames analysieren (verschiedene Pfade probieren)
        frame_urls = [
            ('navi.asp?ufilid=', 'navi.asp (root)'),
            ('administration/navi.asp?ufilid=', 'navi.asp (administration)'),
            ('kfz/navi.asp?ufilid=', 'navi.asp (kfz)'),
            ('start.asp', 'start.asp (root)'),
            ('administration/start.asp', 'start.asp (administration)'),
            ('kfz/start.asp', 'start.asp (kfz)'),
        ]
        
        navi_result = None
        start_result = None
        
        for url_suffix, name in frame_urls:
            if 'navi' in url_suffix and not navi_result:
                result = analyze_frame(BASE_URL + url_suffix, name)
                if result and result['status'] == 200:
                    navi_result = result
            elif 'start' in url_suffix and not start_result:
                result = analyze_frame(BASE_URL + url_suffix, name)
                if result and result['status'] == 200:
                    start_result = result
        
        # Alle Links sammeln
        all_links = []
        if navi_result:
            all_links.extend(navi_result.get('important_links', []))
        if start_result:
            all_links.extend(start_result.get('important_links', []))
        
        # Links testen
        if all_links:
            working = test_links(all_links)
            print(f"\n✅ {len(working)} funktionierende Endpoints gefunden")
        else:
            print("\n⚠️  Keine Links zum Testen gefunden")
    else:
        print("❌ Login fehlgeschlagen")
    
    print("\n✅ Analyse abgeschlossen")

