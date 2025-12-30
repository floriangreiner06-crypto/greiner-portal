#!/usr/bin/env python3
"""
eAutoseller API Exploration
Erforscht die verfügbaren APIs von eAutoseller
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import re

# Login-Credentials
BASE_URL = "https://greiner.eautoseller.de/"
USERNAME = "fGreiner"
PASSWORD = "fGreiner12"

# Session für Login
session = requests.Session()
session.verify = True  # SSL-Verifizierung

def test_login():
    """Testet Login auf eAutoseller"""
    print("=" * 60)
    print("1. LOGIN TEST")
    print("=" * 60)
    
    try:
        # Login-Seite abrufen
        login_url = urljoin(BASE_URL, "login")
        response = session.get(login_url)
        print(f"✅ Login-Seite erreichbar: {response.status_code}")
        print(f"   URL: {login_url}")
        
        # Prüfe ob bereits eingeloggt oder Login-Formular vorhanden
        if "login" in response.text.lower() or "anmelden" in response.text.lower():
            print("   → Login-Formular gefunden")
            
            # Versuche Login (falls Formular vorhanden)
            # Hinweis: Formular-Felder müssen analysiert werden
            print("   ⚠️  Login-Formular erkannt - manuelle Analyse nötig")
        else:
            print("   → Bereits eingeloggt oder andere Seite")
            
        return response
        
    except Exception as e:
        print(f"❌ Fehler beim Login-Test: {e}")
        return None


def explore_api_endpoints():
    """Erforscht bekannte eAutoseller API-Endpoints"""
    print("\n" + "=" * 60)
    print("2. API-ENDPOINTS ERKUNDEN")
    print("=" * 60)
    
    # Bekannte eAutoseller API-Endpoints (basierend auf Web-Recherche)
    api_endpoints = [
        # flashXML API (XML-basiert)
        "/api/flashxml",
        "/flashxml",
        "/eaxml",
        "/api/xml",
        
        # REST API (falls vorhanden)
        "/api/v1/vehicles",
        "/api/vehicles",
        "/api/fahrzeuge",
        
        # SOAP (falls vorhanden)
        "/soap",
        "/api/soap",
        
        # Upload API
        "/api/upload",
        "/upload",
        
        # Weitere mögliche Endpoints
        "/api",
        "/api/v1",
        "/rest",
    ]
    
    found_endpoints = []
    
    for endpoint in api_endpoints:
        try:
            url = urljoin(BASE_URL, endpoint)
            response = session.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - Status: {response.status_code}")
                found_endpoints.append(endpoint)
                
                # Prüfe Content-Type
                content_type = response.headers.get('Content-Type', '')
                print(f"   Content-Type: {content_type}")
                
                # Prüfe ob XML, JSON oder HTML
                if 'xml' in content_type.lower():
                    print(f"   → XML-Response erkannt")
                    try:
                        root = ET.fromstring(response.text)
                        print(f"   → XML-Root: {root.tag}")
                    except:
                        pass
                elif 'json' in content_type.lower():
                    print(f"   → JSON-Response erkannt")
                    try:
                        data = response.json()
                        print(f"   → JSON-Keys: {list(data.keys())[:5]}")
                    except:
                        pass
                elif 'html' in content_type.lower():
                    # Prüfe ob API-Dokumentation
                    if 'api' in response.text.lower() or 'documentation' in response.text.lower():
                        print(f"   → Mögliche API-Dokumentation")
                
            elif response.status_code == 401:
                print(f"🔒 {endpoint} - Authentifizierung erforderlich (401)")
                found_endpoints.append((endpoint, "auth_required"))
            elif response.status_code == 403:
                print(f"🚫 {endpoint} - Zugriff verweigert (403)")
            elif response.status_code == 404:
                print(f"❌ {endpoint} - Nicht gefunden (404)")
            else:
                print(f"⚠️  {endpoint} - Status: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️  {endpoint} - Timeout")
        except requests.exceptions.ConnectionError:
            print(f"🔌 {endpoint} - Verbindungsfehler")
        except Exception as e:
            print(f"❌ {endpoint} - Fehler: {str(e)[:50]}")
    
    return found_endpoints


def test_flashxml_api():
    """Testet die flashXML API (bekannte eAutoseller API)"""
    print("\n" + "=" * 60)
    print("3. FLASHXML API TEST")
    print("=" * 60)
    
    # Bekannte flashXML Parameter (basierend auf Dokumentation)
    flashxml_endpoints = [
        "/eaxml",
        "/flashxml",
        "/api/flashxml",
    ]
    
    # Mögliche Parameter
    params_variants = [
        {},  # Ohne Parameter
        {"authcode": "test"},  # Mit AuthCode
        {"action": "list"},  # Liste abrufen
        {"action": "vehicles"},  # Fahrzeuge
        {"format": "xml"},  # Format
        {"format": "json"},  # JSON-Format
    ]
    
    for endpoint in flashxml_endpoints:
        url = urljoin(BASE_URL, endpoint)
        
        for params in params_variants:
            try:
                response = session.get(url, params=params, timeout=5)
                
                if response.status_code == 200:
                    print(f"✅ {endpoint} mit {params} - Status: 200")
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'xml' in content_type.lower():
                        print(f"   → XML-Response erhalten")
                        # Erste Zeilen anzeigen
                        lines = response.text.split('\n')[:10]
                        print(f"   → Erste Zeilen: {lines[0] if lines else 'leer'}")
                    elif 'json' in content_type.lower():
                        print(f"   → JSON-Response erhalten")
                        try:
                            data = response.json()
                            print(f"   → Keys: {list(data.keys())[:5]}")
                        except:
                            pass
                    else:
                        print(f"   → Response: {response.text[:200]}")
                        
            except Exception as e:
                pass  # Stille Fehler für Varianten-Tests


def analyze_javascript():
    """Analysiert JavaScript-Dateien auf API-Calls"""
    print("\n" + "=" * 60)
    print("4. JAVASCRIPT-ANALYSE")
    print("=" * 60)
    
    try:
        # Hauptseite abrufen
        response = session.get(BASE_URL)
        
        # Suche nach JavaScript-Dateien
        js_files = re.findall(r'<script[^>]*src=["\']([^"\']*\.js[^"\']*)["\']', response.text, re.IGNORECASE)
        
        print(f"✅ {len(js_files)} JavaScript-Dateien gefunden")
        
        # Suche nach API-Calls im HTML
        api_patterns = [
            r'/api/[^"\']+',
            r'\.ajax\([^)]+url["\']:["\']([^"\']+)',
            r'fetch\(["\']([^"\']+)',
            r'axios\.(get|post)\(["\']([^"\']+)',
        ]
        
        found_apis = []
        for pattern in api_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            if matches:
                found_apis.extend(matches if isinstance(matches[0], str) else [m[1] if len(m) > 1 else m[0] for m in matches])
        
        if found_apis:
            print(f"✅ {len(found_apis)} mögliche API-Calls gefunden:")
            for api in set(found_apis[:10]):  # Erste 10 unique
                print(f"   → {api}")
        else:
            print("   ⚠️  Keine API-Calls im HTML gefunden")
            
    except Exception as e:
        print(f"❌ Fehler bei JavaScript-Analyse: {e}")


def test_authenticated_endpoints():
    """Testet Endpoints mit Authentifizierung"""
    print("\n" + "=" * 60)
    print("5. AUTHENTIFIZIERTE ENDPOINTS TEST")
    print("=" * 60)
    
    # Versuche Basic Auth
    auth = HTTPBasicAuth(USERNAME, PASSWORD)
    
    test_endpoints = [
        "/api/vehicles",
        "/api/fahrzeuge",
        "/api/data",
        "/rest/vehicles",
    ]
    
    for endpoint in test_endpoints:
        try:
            url = urljoin(BASE_URL, endpoint)
            response = session.get(url, auth=auth, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} mit Basic Auth - Status: 200")
                print(f"   → Response-Länge: {len(response.text)}")
            elif response.status_code == 401:
                print(f"🔒 {endpoint} - Auth fehlgeschlagen (401)")
            else:
                print(f"⚠️  {endpoint} - Status: {response.status_code}")
                
        except Exception as e:
            pass


def generate_report(found_endpoints):
    """Erstellt einen Bericht"""
    print("\n" + "=" * 60)
    print("6. ZUSAMMENFASSUNG")
    print("=" * 60)
    
    print("\n📋 GEFUNDENE ENDPOINTS:")
    if found_endpoints:
        for ep in found_endpoints:
            if isinstance(ep, tuple):
                print(f"   ✅ {ep[0]} ({ep[1]})")
            else:
                print(f"   ✅ {ep}")
    else:
        print("   ⚠️  Keine Endpoints gefunden")
    
    print("\n📚 BEKANNTE EAUTOSELLER APIs (aus Recherche):")
    print("   1. flashXML API - XML-basiert, für Datenabfragen")
    print("      → Benötigt AuthCode")
    print("      → URL: /eaxml oder /flashxml")
    print("   2. Upload API - CSV-Format")
    print("      → URL: /api/upload oder /upload")
    
    print("\n💡 NÄCHSTE SCHRITTE:")
    print("   1. AuthCode von eAutoseller Support anfordern")
    print("   2. flashXML API mit AuthCode testen")
    print("   3. API-Dokumentation anfordern")
    print("   4. Beispiel-Requests dokumentieren")


if __name__ == '__main__':
    print("🔍 eAutoseller API Exploration")
    print(f"URL: {BASE_URL}")
    print(f"User: {USERNAME}")
    print()
    
    # 1. Login testen
    login_response = test_login()
    
    # 2. API-Endpoints erkunden
    found_endpoints = explore_api_endpoints()
    
    # 3. flashXML API testen
    test_flashxml_api()
    
    # 4. JavaScript analysieren
    analyze_javascript()
    
    # 5. Authentifizierte Endpoints testen
    test_authenticated_endpoints()
    
    # 6. Zusammenfassung
    generate_report(found_endpoints)
    
    print("\n✅ Exploration abgeschlossen")
    print("\n📝 Tipp: Prüfe die Browser-Entwicklertools (Network-Tab)")
    print("   beim Login und bei der Nutzung von eAutoseller,")
    print("   um echte API-Calls zu identifizieren.")

