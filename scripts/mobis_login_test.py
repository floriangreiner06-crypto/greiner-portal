#!/usr/bin/env python3
"""
Mobis EDMOS Login Test
======================
Testet den Login-Prozess und analysiert die Kommunikation.
"""

import requests
import re
import json
from urllib.parse import urljoin, urlparse

BASE_URL = 'https://edos.mobiseurope.com'
LOGIN_URL = f'{BASE_URL}/EDMOSN/gen/index.jsp'
USERNAME = 'G2403Koe'
PASSWORD = 'Greiner3!'

def test_login():
    """Testet den Login-Prozess."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*',
        'Accept-Language': 'de-DE,de;q=0.9',
        'Referer': LOGIN_URL
    })
    
    print("=" * 80)
    print("MOBIS EDMOS LOGIN TEST")
    print("=" * 80)
    
    # 1. Hole Login-Seite
    print("\n[1] Hole Login-Seite...")
    r = session.get(LOGIN_URL, timeout=30)
    print(f"   Status: {r.status_code}")
    print(f"   Cookies: {list(session.cookies.keys())}")
    
    # 2. Suche nach Nexacro-Endpunkten
    print("\n[2] Suche nach Nexacro-Endpunkten...")
    
    # Nexacro verwendet oft .xjs oder .xadl Dateien
    nexacro_patterns = [
        r'["\']([^"\']*\.xjs[^"\']*)["\']',
        r'["\']([^"\']*\.xadl[^"\']*)["\']',
        r'["\']([^"\']*\.do[^"\']*)["\']',
        r'url\s*[:=]\s*["\']([^"\']+)["\']',
    ]
    
    found_endpoints = set()
    for pattern in nexacro_patterns:
        matches = re.findall(pattern, r.text, re.IGNORECASE)
        for match in matches:
            if match and not match.startswith('http'):
                full_url = urljoin(BASE_URL, match)
                found_endpoints.add(full_url)
    
    print(f"   Gefundene Endpunkte: {len(found_endpoints)}")
    for endpoint in sorted(found_endpoints)[:20]:
        print(f"     - {endpoint}")
    
    # 3. Versuche verschiedene Login-Methoden
    print("\n[3] Versuche Login-Methoden...")
    
    # Methode 1: POST zu Login-URL
    print("\n   Methode 1: POST zu Login-URL")
    login_data_1 = {
        'userid': USERNAME,
        'password': PASSWORD
    }
    r1 = session.post(LOGIN_URL, data=login_data_1, timeout=30, allow_redirects=True)
    print(f"     Status: {r1.status_code}")
    print(f"     URL: {r1.url}")
    print(f"     Cookies: {list(session.cookies.keys())}")
    
    # Methode 2: POST zu /login.do
    print("\n   Methode 2: POST zu /login.do")
    login_url_2 = f"{BASE_URL}/EDMOSN/gen/login.do"
    login_data_2 = {
        'userid': USERNAME,
        'password': PASSWORD,
        'userId': USERNAME,
        'userPassword': PASSWORD
    }
    r2 = session.post(login_url_2, data=login_data_2, timeout=30, allow_redirects=True)
    print(f"     Status: {r2.status_code}")
    print(f"     URL: {r2.url}")
    
    # Methode 3: Nexacro-spezifischer Login
    print("\n   Methode 3: Nexacro Transaction")
    # Nexacro verwendet oft SSV-Format (Server Side Values)
    transaction_url = f"{BASE_URL}/EDMOSN/gen/transaction.do"
    
    # SSV-Format: SSV:utf-8\u001ekey1=value1\u001ekey2=value2
    ssv_data = f"SSV:utf-8\u001euserid={USERNAME}\u001epassword={PASSWORD}\u001e"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    r3 = session.post(transaction_url, data=ssv_data, headers=headers, timeout=30)
    print(f"     Status: {r3.status_code}")
    print(f"     Response (erste 200 Zeichen): {r3.text[:200]}")
    
    # 4. Analysiere Response nach Login-Versuchen
    print("\n[4] Analysiere Responses...")
    
    for i, response in enumerate([r1, r2, r3], 1):
        print(f"\n   Response {i}:")
        print(f"     Status: {response.status_code}")
        print(f"     Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        # Prüfe auf Erfolg-Indikatoren
        text_lower = response.text.lower()
        if 'error' in text_lower or 'fehler' in text_lower:
            print("     ⚠️  Fehler-Indikator gefunden")
        if 'success' in text_lower or 'welcome' in text_lower:
            print("     ✅ Erfolg-Indikator gefunden")
        if 'dashboard' in response.url.lower() or 'main' in response.url.lower():
            print("     ✅ Dashboard-URL erkannt")
        
        # Suche nach weiteren Endpunkten in Response
        endpoint_patterns = [
            r'["\']([^"\']*\.do[^"\']*)["\']',
            r'["\']([^"\']*\/api\/[^"\']*)["\']',
            r'url\s*[:=]\s*["\']([^"\']+)["\']',
        ]
        
        response_endpoints = set()
        for pattern in endpoint_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            for match in matches:
                if match and ('api' in match.lower() or '.do' in match.lower() or 'service' in match.lower()):
                    response_endpoints.add(match)
        
        if response_endpoints:
            print(f"     Endpunkte in Response: {len(response_endpoints)}")
            for ep in list(response_endpoints)[:5]:
                print(f"       - {ep}")
    
    print("\n" + "=" * 80)
    print("TEST ABGESCHLOSSEN")
    print("=" * 80)
    
    return session


if __name__ == "__main__":
    test_login()
