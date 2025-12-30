#!/usr/bin/env python3
"""
Tiefe eAutoseller Analyse
Analysiert die Website vollständig nach APIs
"""

import requests
import re
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import json
import xml.etree.ElementTree as ET

BASE_URL = "https://greiner.eautoseller.de/"
USERNAME = "fGreiner"
PASSWORD = "fGreiner12"

session = requests.Session()
session.verify = False  # SSL-Zertifikat möglicherweise problematisch

def get_page(url):
    """Holt eine Seite"""
    try:
        response = session.get(url, timeout=10)
        return response
    except Exception as e:
        print(f"❌ Fehler bei {url}: {e}")
        return None

def find_all_links(html_content, base_url):
    """Findet alle Links auf der Seite"""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()
    
    for tag in soup.find_all(['a', 'form', 'link', 'script']):
        href = tag.get('href') or tag.get('action') or tag.get('src')
        if href:
            if href.startswith('http'):
                links.add(href)
            elif href.startswith('/'):
                links.add(urljoin(base_url, href))
            elif not href.startswith('#'):
                links.add(urljoin(base_url, href))
    
    return links

def extract_api_patterns(content):
    """Extrahiert API-Patterns aus Content"""
    patterns = {
        'api_urls': [],
        'ajax_calls': [],
        'fetch_calls': [],
        'config_objects': []
    }
    
    # API URLs
    api_patterns = [
        r'["\'](/api/[^"\']+)["\']',
        r'["\'](api/[^"\']+)["\']',
        r'["\'](/rest/[^"\']+)["\']',
        r'["\'](/v[0-9]+/[^"\']+)["\']',
        r'["\'](/soap[^"\']*)["\']',
        r'["\'](/xml[^"\']*)["\']',
        r'["\'](/json[^"\']*)["\']',
    ]
    
    for pattern in api_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        patterns['api_urls'].extend(matches)
    
    # AJAX Calls
    ajax_patterns = [
        r'\.ajax\([^)]*url["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        r'\$\.(get|post)\(["\']([^"\']+)["\']',
        r'axios\.(get|post|put|delete)\(["\']([^"\']+)["\']',
    ]
    
    for pattern in ajax_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                patterns['ajax_calls'].append(match[-1])
            else:
                patterns['ajax_calls'].append(match)
    
    # Fetch Calls
    fetch_patterns = [
        r'fetch\(["\']([^"\']+)["\']',
        r'fetch\(`([^`]+)`',
    ]
    
    for pattern in fetch_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        patterns['fetch_calls'].extend(matches)
    
    # Config Objects
    config_patterns = [
        r'(?:api|API)[_ ]?url["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        r'baseURL["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        r'endpoint["\']?\s*[:=]\s*["\']([^"\']+)["\']',
    ]
    
    for pattern in config_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        patterns['config_objects'].extend(matches)
    
    return patterns

def analyze_main_page():
    """Analysiert die Hauptseite"""
    print("=" * 60)
    print("HAUPTSEITE ANALYSE")
    print("=" * 60)
    
    response = get_page(BASE_URL)
    if not response:
        return None
    
    print(f"✅ Status: {response.status_code}")
    print(f"✅ Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"✅ Content-Length: {len(response.text)}")
    
    # Links finden
    links = find_all_links(response.text, BASE_URL)
    print(f"\n📎 {len(links)} Links gefunden")
    
    # API-Patterns extrahieren
    patterns = extract_api_patterns(response.text)
    
    print(f"\n🔍 API-Patterns gefunden:")
    print(f"   API URLs: {len(patterns['api_urls'])}")
    print(f"   AJAX Calls: {len(patterns['ajax_calls'])}")
    print(f"   Fetch Calls: {len(patterns['fetch_calls'])}")
    print(f"   Config Objects: {len(patterns['config_objects'])}")
    
    # Wichtige Links anzeigen
    api_links = [l for l in links if 'api' in l.lower() or 'rest' in l.lower() or 'xml' in l.lower()]
    if api_links:
        print(f"\n🔗 API-relevante Links:")
        for link in sorted(api_links)[:10]:
            print(f"   → {link}")
    
    return response, patterns, links

def test_known_endpoints():
    """Testet bekannte eAutoseller Endpoints"""
    print("\n" + "=" * 60)
    print("BEKANNTE ENDPOINTS TEST")
    print("=" * 60)
    
    endpoints = [
        # flashXML
        "/eaxml",
        "/flashxml",
        "/api/flashxml",
        "/xml",
        "/api/xml",
        
        # REST
        "/api/vehicles",
        "/api/fahrzeuge",
        "/api/v1/vehicles",
        "/rest/vehicles",
        "/api/data",
        
        # SOAP
        "/soap",
        "/api/soap",
        "/wsdl",
        
        # Upload
        "/api/upload",
        "/upload",
        "/api/import",
        
        # Weitere
        "/api",
        "/api/v1",
        "/rest",
        "/json",
        "/api/json",
    ]
    
    results = []
    
    for endpoint in endpoints:
        url = urljoin(BASE_URL, endpoint)
        response = get_page(url)
        
        if response:
            status = response.status_code
            content_type = response.headers.get('Content-Type', '')
            
            result = {
                'url': url,
                'status': status,
                'content_type': content_type,
                'size': len(response.text)
            }
            
            if status == 200:
                print(f"✅ {endpoint}")
                print(f"   Status: {status}, Type: {content_type}, Size: {len(response.text)}")
                
                # Prüfe Format
                if 'xml' in content_type.lower():
                    print(f"   → XML-Format erkannt")
                    try:
                        root = ET.fromstring(response.text[:1000])
                        print(f"   → Root-Element: {root.tag}")
                    except:
                        pass
                elif 'json' in content_type.lower():
                    print(f"   → JSON-Format erkannt")
                    try:
                        data = response.json()
                        print(f"   → Keys: {list(data.keys())[:5]}")
                    except:
                        pass
                
                results.append(result)
            elif status == 401:
                print(f"🔒 {endpoint} - Auth erforderlich (401)")
                results.append({**result, 'auth_required': True})
            elif status == 403:
                print(f"🚫 {endpoint} - Zugriff verweigert (403)")
            elif status == 404:
                print(f"❌ {endpoint} - Nicht gefunden (404)")
            else:
                print(f"⚠️  {endpoint} - Status: {status}")
    
    return results

def analyze_javascript_files(html_content, base_url):
    """Analysiert JavaScript-Dateien"""
    print("\n" + "=" * 60)
    print("JAVASCRIPT-ANALYSE")
    print("=" * 60)
    
    # JavaScript-Dateien finden
    js_files = re.findall(r'<script[^>]*src=["\']([^"\']*\.js[^"\']*)["\']', html_content, re.IGNORECASE)
    
    print(f"📜 {len(js_files)} JavaScript-Dateien gefunden")
    
    all_patterns = {
        'api_urls': [],
        'ajax_calls': [],
        'fetch_calls': [],
        'config_objects': []
    }
    
    for js_file in js_files[:15]:  # Erste 15 analysieren
        try:
            if js_file.startswith('http'):
                js_url = js_file
            elif js_file.startswith('/'):
                js_url = urljoin(base_url, js_file)
            else:
                js_url = urljoin(base_url, js_file)
            
            print(f"\n   📄 {js_url}")
            
            response = get_page(js_url)
            if response and response.status_code == 200:
                patterns = extract_api_patterns(response.text)
                
                all_patterns['api_urls'].extend(patterns['api_urls'])
                all_patterns['ajax_calls'].extend(patterns['ajax_calls'])
                all_patterns['fetch_calls'].extend(patterns['fetch_calls'])
                all_patterns['config_objects'].extend(patterns['config_objects'])
                
                total = sum(len(v) for v in patterns.values())
                if total > 0:
                    print(f"      ✅ {total} API-Patterns gefunden")
        except Exception as e:
            pass
    
    return all_patterns

def generate_final_report(main_patterns, js_patterns, endpoint_results):
    """Erstellt finalen Bericht"""
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    
    # Alle Patterns kombinieren
    all_api_urls = set(main_patterns.get('api_urls', []) + js_patterns.get('api_urls', []))
    all_ajax = set(main_patterns.get('ajax_calls', []) + js_patterns.get('ajax_calls', []))
    all_fetch = set(main_patterns.get('fetch_calls', []) + js_patterns.get('fetch_calls', []))
    all_config = set(main_patterns.get('config_objects', []) + js_patterns.get('config_objects', []))
    
    print(f"\n📊 GEFUNDENE API-PATTERNS:")
    print(f"   API URLs: {len(all_api_urls)}")
    print(f"   AJAX Calls: {len(all_ajax)}")
    print(f"   Fetch Calls: {len(all_fetch)}")
    print(f"   Config Objects: {len(all_config)}")
    
    print(f"\n✅ FUNKTIONIERENDE ENDPOINTS: {len([e for e in endpoint_results if e.get('status') == 200])}")
    print(f"🔒 AUTH ERFORDERLICH: {len([e for e in endpoint_results if e.get('auth_required')])}")
    
    print(f"\n📋 EINDEUTIGE API-URLS:")
    for url in sorted(all_api_urls)[:20]:
        print(f"   → {url}")
    
    print(f"\n📋 AJAX-CALLS:")
    for call in sorted(all_ajax)[:15]:
        print(f"   → {call}")
    
    print(f"\n📋 FETCH-CALLS:")
    for call in sorted(all_fetch)[:15]:
        print(f"   → {call}")
    
    print(f"\n💡 EMPFEHLUNGEN:")
    print("   1. Browser-Entwicklertools für detaillierte Analyse nutzen")
    print("   2. Network-Tab während Nutzung prüfen")
    print("   3. AuthCode von eAutoseller Support anfordern")
    print("   4. flashXML API mit AuthCode testen")

if __name__ == '__main__':
    print("🔍 Tiefe eAutoseller Analyse")
    print(f"URL: {BASE_URL}")
    print()
    
    # Hauptseite analysieren
    main_result = analyze_main_page()
    if main_result:
        main_response, main_patterns, links = main_result
        
        # JavaScript analysieren
        js_patterns = analyze_javascript_files(main_response.text, BASE_URL)
        
        # Bekannte Endpoints testen
        endpoint_results = test_known_endpoints()
        
        # Finaler Bericht
        generate_final_report(main_patterns, js_patterns, endpoint_results)
    
    print("\n✅ Analyse abgeschlossen")

