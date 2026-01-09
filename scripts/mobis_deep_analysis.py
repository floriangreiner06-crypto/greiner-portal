#!/usr/bin/env python3
"""
Mobis EDMOS Tiefen-Analyse
===========================
Analysiert Nexacro-App-Struktur und findet API-Endpunkte.
"""

import requests
import re
import json
import time

BASE_URL = 'https://edos.mobiseurope.com'
LOGIN_URL = f'{BASE_URL}/EDMOSN/gen/index.jsp'
USERNAME = 'G2403Koe'
PASSWORD = 'Greiner3!'

def analyze_nexacro_app():
    """Analysiert die Nexacro-App-Struktur."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*',
        'Referer': LOGIN_URL
    })
    
    print("=" * 80)
    print("MOBIS EDMOS TIEFEN-ANALYSE")
    print("=" * 80)
    
    # 1. Login
    print("\n[1] Login...")
    login_data = {'userid': USERNAME, 'password': PASSWORD}
    r_login = session.post(f'{BASE_URL}/EDMOSN/gen/login.do', data=login_data, timeout=30)
    print(f"   Status: {r_login.status_code}")
    print(f"   Cookies: {list(session.cookies.keys())}")
    
    # 2. Hole App-Deskriptor
    print("\n[2] Lade Nexacro App-Deskriptor...")
    app_url = f'{BASE_URL}/App_Desktop.xadl.js'
    r_app = session.get(app_url, timeout=30)
    
    if r_app.status_code == 200:
        app_content = r_app.text
        print(f"   Größe: {len(app_content)} Zeichen")
        
        # Speichere für Analyse
        with open('/tmp/App_Desktop.xadl.js', 'w', encoding='utf-8') as f:
            f.write(app_content)
        print("   Gespeichert: /tmp/App_Desktop.xadl.js")
        
        # Suche nach Endpunkten
        print("\n[3] Suche nach API-Endpunkten...")
        
        # Pattern für .do Endpunkte
        do_pattern = r'["\']([^"\']*\.do[^"\']*)["\']'
        do_matches = set(re.findall(do_pattern, app_content, re.IGNORECASE))
        
        # Pattern für Transaction-Calls
        transaction_patterns = [
            r'svcurl\s*[:=]\s*["\']([^"\']+)["\']',
            r'url\s*[:=]\s*["\']([^"\']+\.do)["\']',
            r'serviceurl\s*[:=]\s*["\']([^"\']+)["\']',
            r'endpoint\s*[:=]\s*["\']([^"\']+)["\']',
        ]
        
        transaction_endpoints = set()
        for pattern in transaction_patterns:
            matches = re.findall(pattern, app_content, re.IGNORECASE)
            transaction_endpoints.update(matches)
        
        # Pattern für Teilebezug-relevante Funktionen
        teile_patterns = [
            r'["\']([^"\']*[Tt]eil[^"\']*\.do)["\']',
            r'["\']([^"\']*[Pp]art[^"\']*\.do)["\']',
            r'["\']([^"\']*[Bb]estell[^"\']*\.do)["\']',
            r'["\']([^"\']*[Oo]rder[^"\']*\.do)["\']',
            r'["\']([^"\']*[Ll]iefer[^"\']*\.do)["\']',
            r'["\']([^"\']*[Dd]eliver[^"\']*\.do)["\']',
        ]
        
        teile_endpoints = set()
        for pattern in teile_patterns:
            matches = re.findall(pattern, app_content, re.IGNORECASE)
            teile_endpoints.update(matches)
        
        # Ausgabe
        all_endpoints = do_matches | transaction_endpoints | teile_endpoints
        
        print(f"\n   Gefundene .do Endpunkte: {len(do_matches)}")
        for ep in sorted(do_matches)[:30]:
            if not ep.startswith('http'):
                ep = f"{BASE_URL}/EDMOSN/gen/{ep.lstrip('/')}"
            print(f"     - {ep}")
        
        print(f"\n   Transaction-Endpunkte: {len(transaction_endpoints)}")
        for ep in sorted(transaction_endpoints)[:20]:
            if not ep.startswith('http'):
                ep = f"{BASE_URL}/EDMOSN/gen/{ep.lstrip('/')}"
            print(f"     - {ep}")
        
        print(f"\n   Teilebezug-relevante Endpunkte: {len(teile_endpoints)}")
        for ep in sorted(teile_endpoints):
            if not ep.startswith('http'):
                ep = f"{BASE_URL}/EDMOSN/gen/{ep.lstrip('/')}"
            print(f"     ✅ {ep}")
        
        # 4. Teste Teilebezug-Endpunkte
        if teile_endpoints:
            print("\n[4] Teste Teilebezug-Endpunkte...")
            for ep in sorted(teile_endpoints)[:5]:
                if not ep.startswith('http'):
                    ep = f"{BASE_URL}/EDMOSN/gen/{ep.lstrip('/')}"
                
                print(f"\n   Teste: {ep}")
                try:
                    # GET
                    r_get = session.get(ep, timeout=10)
                    print(f"     GET: {r_get.status_code}")
                    
                    # POST
                    r_post = session.post(ep, data={}, timeout=10)
                    print(f"     POST: {r_post.status_code}")
                    print(f"     Content-Type: {r_post.headers.get('Content-Type', 'N/A')}")
                    
                    if r_post.status_code == 200:
                        # Prüfe Response
                        if 'json' in r_post.headers.get('Content-Type', '').lower():
                            try:
                                data = r_post.json()
                                print(f"     ✅ JSON-Response!")
                                print(f"     Response (erste 300 Zeichen): {str(data)[:300]}")
                            except:
                                print(f"     Response (erste 300 Zeichen): {r_post.text[:300]}")
                        else:
                            print(f"     Response (erste 300 Zeichen): {r_post.text[:300]}")
                except Exception as e:
                    print(f"     ❌ Fehler: {str(e)}")
        
        # 5. Suche nach weiteren Hinweisen
        print("\n[5] Suche nach weiteren Hinweisen...")
        
        # Suche nach Funktionsnamen
        function_pattern = r'function\s+([a-zA-Z_][a-zA-Z0-9_]*[Tt]eil[a-zA-Z0-9_]*)'
        functions = re.findall(function_pattern, app_content)
        if functions:
            print(f"   Teilebezug-Funktionen: {len(set(functions))}")
            for func in sorted(set(functions))[:10]:
                print(f"     - {func}")
        
        # Suche nach Variablennamen
        var_pattern = r'var\s+([a-zA-Z_][a-zA-Z0-9_]*[Tt]eil[a-zA-Z0-9_]*)'
        variables = re.findall(var_pattern, app_content)
        if variables:
            print(f"   Teilebezug-Variablen: {len(set(variables))}")
            for var in sorted(set(variables))[:10]:
                print(f"     - {var}")
        
        return {
            'do_endpoints': sorted(do_matches),
            'transaction_endpoints': sorted(transaction_endpoints),
            'teile_endpoints': sorted(teile_endpoints),
            'all_endpoints': sorted(all_endpoints)
        }
    
    else:
        print(f"   ❌ Fehler beim Laden: {r_app.status_code}")
        return None


if __name__ == "__main__":
    results = analyze_nexacro_app()
    
    if results:
        # Speichere Ergebnisse
        with open('/tmp/mobis_deep_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print("\n✅ Ergebnisse gespeichert: /tmp/mobis_deep_analysis.json")
    
    print("\n" + "=" * 80)
    print("ANALYSE ABGESCHLOSSEN")
    print("=" * 80)
