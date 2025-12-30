#!/usr/bin/env python3
"""
eAutoseller Frameset-Analyse
Analysiert Framesets und geladene Frames
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

def analyze_frameset(html):
    """Analysiert Frameset-Struktur"""
    print("=" * 60)
    print("FRAMESET-ANALYSE")
    print("=" * 60)
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Framesets finden
    framesets = soup.find_all('frameset')
    print(f"📦 {len(framesets)} Framesets gefunden")
    
    # Frames finden
    frames = soup.find_all(['frame', 'iframe'])
    print(f"🖼️  {len(frames)} Frames gefunden")
    
    frame_urls = []
    
    for frame in frames:
        src = frame.get('src', '')
        name = frame.get('name', 'N/A')
        print(f"\n   Frame: {name}")
        print(f"   Src: {src}")
        
        if src:
            if src.startswith('http'):
                frame_urls.append(src)
            elif src.startswith('/'):
                frame_urls.append(urljoin(BASE_URL, src))
            else:
                frame_urls.append(urljoin(BASE_URL, src))
    
    return frame_urls

def load_and_analyze_frames(frame_urls):
    """Lädt und analysiert Frame-Inhalte"""
    print("\n" + "=" * 60)
    print("FRAME-INHALTE ANALYSE")
    print("=" * 60)
    
    all_api_patterns = set()
    
    for i, url in enumerate(frame_urls, 1):
        try:
            print(f"\n[{i}/{len(frame_urls)}] Lade Frame: {url}")
            resp = session.get(url, timeout=10)
            
            if resp.status_code == 200:
                print(f"   ✅ Status: 200, Size: {len(resp.text)}")
                
                # Suche nach API-Patterns
                patterns = re.findall(r'["\']([^"\']*(?:api|data|json|xml|asp|ashx|ajax)[^"\']*)["\']', resp.text, re.I)
                if patterns:
                    print(f"   → {len(patterns)} API-Patterns gefunden")
                    for p in set(patterns)[:10]:
                        print(f"      {p}")
                        all_api_patterns.add(p)
                
                # Suche nach JavaScript
                js_files = re.findall(r'<script[^>]*src=["\']([^"\']*\.js[^"\']*)["\']', resp.text, re.I)
                if js_files:
                    print(f"   → {len(js_files)} JavaScript-Dateien gefunden")
                    for js in js_files[:5]:
                        print(f"      {js}")
                
                # Suche nach Links
                soup = BeautifulSoup(resp.text, 'html.parser')
                links = [a.get('href') for a in soup.find_all('a', href=True) if a.get('href')]
                important_links = [l for l in links if any(x in l.lower() for x in ['fahrzeug', 'vehicle', 'kfz', 'data', 'json', 'xml'])]
                if important_links:
                    print(f"   → {len(important_links)} wichtige Links")
                    for link in important_links[:5]:
                        print(f"      {link}")
        except Exception as e:
            print(f"   ❌ Fehler: {str(e)[:50]}")
    
    return all_api_patterns

def test_found_endpoints(patterns):
    """Testet gefundene Endpoints"""
    print("\n" + "=" * 60)
    print("ENDPOINT-TEST")
    print("=" * 60)
    
    working = []
    
    for pattern in sorted(patterns)[:30]:
        # Normalisiere URL
        if pattern.startswith('http'):
            url = pattern
        elif pattern.startswith('/'):
            url = urljoin(BASE_URL, pattern)
        else:
            url = urljoin(BASE_URL, '/' + pattern)
        
        try:
            resp = session.get(url, timeout=5, allow_redirects=False)
            
            if resp.status_code == 200:
                print(f"✅ {pattern}")
                print(f"   Type: {resp.headers.get('Content-Type', 'N/A')}, Size: {len(resp.text)}")
                working.append({
                    'pattern': pattern,
                    'url': url,
                    'status': 200,
                    'content_type': resp.headers.get('Content-Type', ''),
                    'size': len(resp.text),
                    'sample': resp.text[:300]
                })
            elif resp.status_code == 401:
                print(f"🔒 {pattern} - Auth (401)")
            elif resp.status_code != 404:
                print(f"⚠️  {pattern} - Status: {resp.status_code}")
        except:
            pass
    
    return working

if __name__ == '__main__':
    print("🔍 eAutoseller Frameset-Analyse")
    print()
    
    if login():
        print("✅ Login erfolgreich!")
        
        # Hauptseite laden
        resp = session.get(BASE_URL + 'administration/index.asp')
        
        # Frameset analysieren
        frame_urls = analyze_frameset(resp.text)
        
        if frame_urls:
            # Frame-Inhalte analysieren
            api_patterns = load_and_analyze_frames(frame_urls)
            
            # Endpoints testen
            working = test_found_endpoints(api_patterns)
            
            print(f"\n✅ {len(working)} funktionierende Endpoints gefunden")
        else:
            print("\n⚠️  Keine Frames gefunden - möglicherweise andere Struktur")
            print("   HTML-Struktur:")
            print(resp.text[:1000])
    else:
        print("❌ Login fehlgeschlagen")
    
    print("\n✅ Analyse abgeschlossen")

