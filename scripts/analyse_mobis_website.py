#!/usr/bin/env python3
"""
Mobis EDMOS Website Analyse
============================
Analysiert die Mobis-Website und identifiziert API-Endpunkte.
"""

import requests
import json
import re
from urllib.parse import urljoin, urlparse

# Mobis Konfiguration
BASE_URL = 'https://edos.mobiseurope.com'
LOGIN_URL = f'{BASE_URL}/EDMOSN/gen/index.jsp'
USERNAME = 'G2403Koe'
PASSWORD = 'Greiner3!'

def analyse_website():
    """Analysiert die Mobis-Website."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8'
    })
    
    print("=" * 80)
    print("MOBIS EDMOS WEBSITE ANALYSE")
    print("=" * 80)
    
    # 1. Öffne Login-Seite
    print("\n[1] Öffne Login-Seite...")
    try:
        r = session.get(LOGIN_URL, timeout=30)
        print(f"   Status: {r.status_code}")
        print(f"   URL: {r.url}")
        print(f"   Cookies: {list(session.cookies.keys())}")
        
        # Analysiere HTML mit Regex
        html = r.text
        
        # Finde Formulare
        form_pattern = r'<form[^>]*action=["\']([^"\']*)["\'][^>]*method=["\']([^"\']*)["\'][^>]*>(.*?)</form>'
        forms = re.findall(form_pattern, html, re.DOTALL | re.IGNORECASE)
        print(f"\n   Formulare gefunden: {len(forms)}")
        
        for i, (action, method, form_content) in enumerate(forms, 1):
            print(f"\n   Form {i}:")
            print(f"     Action: {action or 'N/A'}")
            print(f"     Method: {method or 'N/A'}")
            
            # Finde Inputs im Form
            input_pattern = r'<input[^>]*name=["\']([^"\']*)["\'][^>]*type=["\']([^"\']*)["\'][^>]*>'
            inputs = re.findall(input_pattern, form_content, re.IGNORECASE)
            print(f"     Inputs: {len(inputs)}")
            for name, inp_type in inputs[:10]:
                print(f"       - {name} ({inp_type})")
        
        # Finde JavaScript-Dateien
        script_pattern = r'<script[^>]*src=["\']([^"\']*)["\'][^>]*>'
        scripts = re.findall(script_pattern, html, re.IGNORECASE)
        print(f"\n   JavaScript-Dateien: {len(scripts)}")
        for src in scripts[:10]:
            if src:
                full_url = urljoin(BASE_URL, src)
                print(f"       - {full_url}")
        
        # Finde AJAX-Endpunkte im JavaScript
        print("\n   Suche nach AJAX-Endpunkten im JavaScript...")
        inline_script_pattern = r'<script[^>]*>(.*?)</script>'
        inline_scripts = re.findall(inline_script_pattern, html, re.DOTALL | re.IGNORECASE)
        
        ajax_patterns = [
            r'["\']([^"\']*\.do[^"\']*)["\']',
            r'["\']([^"\']*\/api\/[^"\']*)["\']',
            r'["\']([^"\']*\/ajax\/[^"\']*)["\']',
            r'url\s*[:=]\s*["\']([^"\']+)["\']',
            r'action\s*[:=]\s*["\']([^"\']+)["\']',
        ]
        
        found_endpoints = set()
        for script_text in inline_scripts:
            for pattern in ajax_patterns:
                matches = re.findall(pattern, script_text, re.IGNORECASE)
                for match in matches:
                    if any(keyword in match.lower() for keyword in ['api', 'ajax', '.do', 'service', 'rest']):
                        found_endpoints.add(match)
        
        if found_endpoints:
            print(f"     Gefundene Endpunkte: {len(found_endpoints)}")
            for endpoint in sorted(found_endpoints)[:20]:
                print(f"       - {endpoint}")
        else:
            print("     Keine Endpunkte gefunden")
        
        # 2. Versuche Login
        print("\n[2] Versuche Login...")
        
        # Finde Login-Felder mit Regex
        username_pattern = r'<input[^>]*name=["\']([^"\']*(?:user|login|id)[^"\']*)["\'][^>]*>'
        password_pattern = r'<input[^>]*type=["\']password["\'][^>]*name=["\']([^"\']*)["\'][^>]*>'
        
        username_match = re.search(username_pattern, html, re.IGNORECASE)
        password_match = re.search(password_pattern, html, re.IGNORECASE)
        
        if username_match and password_match:
            username_name = username_match.group(1)
            password_name = password_match.group(1)
            
            # Finde zugehöriges Form
            form_pattern = r'<form[^>]*>(.*?)</form>'
            forms_content = re.findall(form_pattern, html, re.DOTALL | re.IGNORECASE)
            
            login_form = None
            for form_content in forms_content:
                if username_name in form_content and password_name in form_content:
                    login_form = form_content
                    break
            
            if login_form:
                # Finde Form-Action
                form_tag_pattern = r'<form[^>]*action=["\']([^"\']*)["\'][^>]*method=["\']([^"\']*)["\'][^>]*>'
                form_match = re.search(form_tag_pattern, html, re.IGNORECASE)
                
                if form_match:
                    action = form_match.group(1) or LOGIN_URL
                    method = form_match.group(2) or 'post'
                    
                    if not action or action == '#' or action == '':
                        action = LOGIN_URL
                    else:
                        action = urljoin(BASE_URL, action)
                    
                    login_data = {
                        username_name: USERNAME,
                        password_name: PASSWORD
                    }
                    
                    print(f"     Login-Form gefunden:")
                    print(f"       Action: {action}")
                    print(f"       Method: {method}")
                    print(f"       Username-Feld: {username_name}")
                    print(f"       Password-Feld: {password_name}")
                    
                    # Versuche Login
                    if method.lower() == 'post':
                        r_login = session.post(action, data=login_data, timeout=30, allow_redirects=True)
                    else:
                        r_login = session.get(action, params=login_data, timeout=30, allow_redirects=True)
                    
                    print(f"     Login-Response: {r_login.status_code}")
                    print(f"     Redirect-URL: {r_login.url}")
                    print(f"     Cookies nach Login: {list(session.cookies.keys())}")
                    
                    # Prüfe ob Login erfolgreich
                    login_html = r_login.text.lower()
                    if r_login.status_code == 200:
                        if 'error' in login_html or 'invalid' in login_html or 'fehler' in login_html:
                            print("     ⚠️  Möglicherweise Login-Fehler (Error-Text gefunden)")
                        elif 'dashboard' in r_login.url.lower() or 'main' in r_login.url.lower() or 'welcome' in login_html:
                            print("     ✅ Login möglicherweise erfolgreich (Dashboard-URL)")
                        else:
                            print("     ⚠️  Unklarer Login-Status")
                    
                    # Suche nach API-Links/Endpunkten nach Login
                    link_pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>'
                    links = re.findall(link_pattern, r_login.text, re.IGNORECASE)
                    api_links = [link for link in links if any(keyword in link.lower() for keyword in ['api', 'ajax', 'service', 'rest', 'parts', 'order', 'delivery'])]
                    
                    if api_links:
                        print(f"\n     API-ähnliche Links gefunden: {len(api_links)}")
                        for link in api_links[:10]:
                            print(f"       - {link}")
        
        # 3. Suche nach weiteren API-Hinweisen
        print("\n[3] Suche nach weiteren API-Hinweisen...")
        
        # Suche nach JSON-LD oder anderen strukturierten Daten
        json_script_pattern = r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>'
        json_scripts = re.findall(json_script_pattern, html, re.DOTALL | re.IGNORECASE)
        if json_scripts:
            print(f"   JSON-Scripts gefunden: {len(json_scripts)}")
        
        # Suche nach REST/SOAP-Hinweisen
        rest_keywords = ['rest', 'api', 'soap', 'wsdl', 'json', 'xml']
        page_text = r.text.lower()
        for keyword in rest_keywords:
            if keyword in page_text:
                print(f"   Keyword '{keyword}' gefunden in Seite")
        
        # Speichere HTML für weitere Analyse
        print("\n[4] Speichere HTML für weitere Analyse...")
        with open('/tmp/mobis_login_page.html', 'w', encoding='utf-8') as f:
            f.write(r.text)
        print("   HTML gespeichert: /tmp/mobis_login_page.html")
        
        print("\n" + "=" * 80)
        print("ANALYSE ABGESCHLOSSEN")
        print("=" * 80)
        
        return session
        
    except Exception as e:
        print(f"\n❌ Fehler: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    analyse_website()
