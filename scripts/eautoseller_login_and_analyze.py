#!/usr/bin/env python3
"""
eAutoseller Login & Analyse
Loggt sich ein und analysiert dann die APIs
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import json
import warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

BASE_URL = "https://greiner.eautoseller.de/"
USERNAME = "fGreiner"
PASSWORD = "fGreiner12"

session = requests.Session()
session.verify = False  # SSL-Zertifikat ignorieren

def login():
    """Loggt sich bei eAutoseller ein"""
    print("=" * 60)
    print("LOGIN")
    print("=" * 60)
    
    try:
        # Hauptseite abrufen
        print(f"📥 Lade Hauptseite: {BASE_URL}")
        response = session.get(BASE_URL, timeout=10)
        print(f"✅ Status: {response.status_code}")
        
        # Login-Formular finden
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Suche nach Login-Formular
        login_form = soup.find('form')
        if not login_form:
            # Versuche verschiedene Formular-Selektoren
            login_form = soup.find('form', {'method': 'post'})
            login_form = soup.find('form', {'id': re.compile('login', re.I)})
        
        if login_form:
            print("✅ Login-Formular gefunden")
            action = login_form.get('action', '')
            if action:
                login_url = urljoin(BASE_URL, action)
            else:
                login_url = BASE_URL
            
            # Alle Felder aus Formular sammeln
            login_data = {}
            
            for field in login_form.find_all(['input', 'select', 'textarea']):
                field_type = field.get('type', '').lower()
                name = field.get('name')
                
                if not name:
                    continue
                
                # Select-Felder
                if field.name == 'select':
                    options = field.find_all('option')
                    if options:
                        value = options[0].get('value', options[0].text.strip())
                        login_data[name] = value
                        print(f"   → Select-Feld: {name} = {value}")
                # Text-Input (Username)
                elif field_type == 'text':
                    if 'user' in name.lower() or 'login' in name.lower():
                        login_data[name] = USERNAME
                        print(f"   → Username-Feld: {name}")
                # Password-Input
                elif field_type == 'password':
                    login_data[name] = PASSWORD
                    print(f"   → Password-Feld: {name}")
                # Checkboxen
                elif field_type == 'checkbox':
                    value = field.get('value', '1')
                    if field.get('checked') or value:
                        login_data[name] = value
                # Hidden Fields
                elif field_type == 'hidden':
                    value = field.get('value', '')
                    login_data[name] = value
                # Submit-Button ignorieren
                elif field_type == 'submit':
                    pass
            
            print(f"\n📤 Sende Login-Request an: {login_url}")
            print(f"   Daten: {', '.join([f'{k}=***' if 'pass' in k.lower() else f'{k}={v}' for k, v in login_data.items()])}")
            
            # Headers setzen (wichtig für manche Systeme)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': BASE_URL,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            # Login-Request senden
            login_response = session.post(login_url, data=login_data, headers=headers, allow_redirects=True, timeout=10)
            
            print(f"✅ Login-Response: {login_response.status_code}")
            print(f"   Finale URL: {login_response.url}")
            
            # Prüfe Fehlercode in URL
            if 'err=' in login_response.url:
                err_code = login_response.url.split('err=')[1].split('&')[0]
                print(f"   ⚠️  Fehlercode in URL: err={err_code}")
                
                # Versuche verschiedene Login-Varianten
                print("\n🔄 Versuche alternative Login-Methoden...")
                
                # Variante 1: Mit "Anmelden" Button-Name
                login_data_v2 = login_data.copy()
                login_data_v2['btnLogin'] = 'Anmelden'  # Möglicher Button-Name
                
                login_response_v2 = session.post(login_url, data=login_data_v2, headers=headers, allow_redirects=True, timeout=10)
                if 'err=' not in login_response_v2.url and 'login' not in login_response_v2.url.lower():
                    print("✅ Login erfolgreich (Variante 2)!")
                    return True
                
                # Variante 2: Mit "Submit"
                login_data_v3 = login_data.copy()
                login_data_v3['submit'] = '1'
                
                login_response_v3 = session.post(login_url, data=login_data_v3, headers=headers, allow_redirects=True, timeout=10)
                if 'err=' not in login_response_v3.url and 'login' not in login_response_v3.url.lower():
                    print("✅ Login erfolgreich (Variante 3)!")
                    return True
            
            # Prüfe ob Login erfolgreich
            if login_response.status_code == 200:
                # Prüfe ob wir eingeloggt sind (keine Login-Seite mehr)
                if 'err=' not in login_response.url and ('login' not in login_response.url.lower() or 'main' in login_response.url.lower() or 'index' in login_response.url.lower()):
                    print("✅ Login erfolgreich!")
                    return True
                else:
                    print("⚠️  Möglicherweise noch auf Login-Seite")
                    # Prüfe ob Fehlermeldung
                    if 'fehler' in login_response.text.lower() or 'error' in login_response.text.lower():
                        print("   → Fehlermeldung erkannt")
                    return False
            else:
                print(f"⚠️  Unerwarteter Status: {login_response.status_code}")
                return False
                
        else:
            print("⚠️  Kein Login-Formular gefunden")
            print("   → Möglicherweise bereits eingeloggt oder andere Struktur")
            # Prüfe ob wir bereits eingeloggt sind
            if 'login' not in response.text.lower() and 'anmelden' not in response.text.lower():
                print("✅ Bereits eingeloggt oder keine Login-Seite")
                return True
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Login: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_logged_in_page():
    """Analysiert die Seite nach Login"""
    print("\n" + "=" * 60)
    print("ANALYSE NACH LOGIN")
    print("=" * 60)
    
    try:
        # Hauptseite nach Login abrufen
        response = session.get(BASE_URL, timeout=10)
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Content-Length: {len(response.text)}")
        
        # HTML analysieren
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Links finden
        links = set()
        for tag in soup.find_all(['a', 'form', 'link', 'script', 'iframe']):
            href = tag.get('href') or tag.get('action') or tag.get('src')
            if href:
                if href.startswith('http'):
                    links.add(href)
                elif href.startswith('/'):
                    links.add(urljoin(BASE_URL, href))
        
        print(f"\n📎 {len(links)} Links gefunden")
        
        # API-relevante Links
        api_links = [l for l in links if any(x in l.lower() for x in ['api', 'rest', 'xml', 'json', 'soap', 'ajax'])]
        if api_links:
            print(f"\n🔗 API-relevante Links ({len(api_links)}):")
            for link in sorted(api_links)[:20]:
                print(f"   → {link}")
        
        # JavaScript-Dateien finden
        js_files = re.findall(r'<script[^>]*src=["\']([^"\']*\.js[^"\']*)["\']', response.text, re.IGNORECASE)
        print(f"\n📜 {len(js_files)} JavaScript-Dateien gefunden")
        
        # API-Patterns im HTML
        api_patterns = {
            'api_urls': re.findall(r'["\'](/api/[^"\']+)["\']', response.text, re.IGNORECASE),
            'ajax_calls': re.findall(r'\.ajax\([^)]*url["\']?\s*[:=]\s*["\']([^"\']+)["\']', response.text, re.IGNORECASE),
            'fetch_calls': re.findall(r'fetch\(["\']([^"\']+)["\']', response.text, re.IGNORECASE),
        }
        
        print(f"\n🔍 API-Patterns im HTML:")
        print(f"   API URLs: {len(api_patterns['api_urls'])}")
        print(f"   AJAX Calls: {len(api_patterns['ajax_calls'])}")
        print(f"   Fetch Calls: {len(api_patterns['fetch_calls'])}")
        
        if api_patterns['api_urls']:
            print(f"\n   API URLs:")
            for url in set(api_patterns['api_urls'])[:10]:
                print(f"      → {url}")
        
        if api_patterns['ajax_calls']:
            print(f"\n   AJAX Calls:")
            for call in set(api_patterns['ajax_calls'])[:10]:
                print(f"      → {call}")
        
        if api_patterns['fetch_calls']:
            print(f"\n   Fetch Calls:")
            for call in set(api_patterns['fetch_calls'])[:10]:
                print(f"      → {call}")
        
        return response, api_patterns, api_links
        
    except Exception as e:
        print(f"❌ Fehler bei Analyse: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

def test_api_endpoints(api_links, api_patterns):
    """Testet gefundene API-Endpoints"""
    print("\n" + "=" * 60)
    print("API-ENDPOINT TEST")
    print("=" * 60)
    
    # Alle gefundenen Endpoints sammeln
    all_endpoints = set()
    
    # Aus Links
    for link in api_links:
        if 'api' in link.lower() or 'rest' in link.lower():
            all_endpoints.add(link)
    
    # Aus Patterns
    for pattern_list in api_patterns.values():
        for endpoint in pattern_list:
            if endpoint.startswith('/'):
                all_endpoints.add(urljoin(BASE_URL, endpoint))
            elif not endpoint.startswith('http'):
                all_endpoints.add(urljoin(BASE_URL, '/' + endpoint))
    
    # Bekannte Endpoints hinzufügen
    known_endpoints = [
        '/eaxml',
        '/flashxml',
        '/api/vehicles',
        '/api/fahrzeuge',
        '/api/data',
        '/rest/vehicles',
    ]
    
    for ep in known_endpoints:
        all_endpoints.add(urljoin(BASE_URL, ep))
    
    print(f"🧪 Teste {len(all_endpoints)} Endpoints...")
    
    working_endpoints = []
    
    for endpoint in sorted(all_endpoints)[:30]:  # Erste 30 testen
        try:
            response = session.get(endpoint, timeout=5, allow_redirects=False)
            
            status = response.status_code
            content_type = response.headers.get('Content-Type', '')
            
            if status == 200:
                print(f"✅ {endpoint}")
                print(f"   Status: {status}, Type: {content_type}, Size: {len(response.text)}")
                
                # Prüfe Format
                if 'json' in content_type.lower():
                    try:
                        data = response.json()
                        print(f"   → JSON: Keys: {list(data.keys())[:5]}")
                    except:
                        pass
                elif 'xml' in content_type.lower():
                    print(f"   → XML-Format")
                
                working_endpoints.append({
                    'url': endpoint,
                    'status': status,
                    'content_type': content_type,
                    'size': len(response.text)
                })
            elif status == 401:
                print(f"🔒 {endpoint} - Auth erforderlich (401)")
            elif status == 403:
                print(f"🚫 {endpoint} - Zugriff verweigert (403)")
            elif status == 404:
                pass  # Stille 404s
            else:
                print(f"⚠️  {endpoint} - Status: {status}")
                
        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            pass
    
    return working_endpoints

def generate_report(working_endpoints):
    """Erstellt finalen Bericht"""
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    
    print(f"\n✅ FUNKTIONIERENDE API-ENDPOINTS: {len(working_endpoints)}")
    
    if working_endpoints:
        print("\n📋 ENDPOINT-DETAILS:")
        for ep in working_endpoints:
            print(f"\n   URL: {ep['url']}")
            print(f"   Status: {ep['status']}")
            print(f"   Content-Type: {ep['content_type']}")
            print(f"   Size: {ep['size']} Bytes")
    
    print("\n💡 NÄCHSTE SCHRITTE:")
    print("   1. Browser-Entwicklertools für detaillierte Analyse")
    print("   2. Network-Tab während Nutzung prüfen")
    print("   3. Requests exportieren (HAR-Format)")
    print("   4. API-Dokumentation anfordern")

if __name__ == '__main__':
    print("🔍 eAutoseller Login & Analyse")
    print(f"URL: {BASE_URL}")
    print(f"User: {USERNAME}")
    print()
    
    # Login
    if login():
        # Analyse nach Login
        response, api_patterns, api_links = analyze_logged_in_page()
        
        if response:
            # API-Endpoints testen
            working_endpoints = test_api_endpoints(api_links or [], api_patterns or {})
            
            # Bericht generieren
            generate_report(working_endpoints)
        else:
            print("\n⚠️  Analyse nicht möglich")
    else:
        print("\n❌ Login fehlgeschlagen - Analyse nicht möglich")
        print("   Bitte manuell im Browser einloggen und analysieren")
    
    print("\n✅ Analyse abgeschlossen")

