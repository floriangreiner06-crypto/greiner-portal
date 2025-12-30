#!/usr/bin/env python3
"""
eAutoseller Login Debug
Analysiert die Login-Seite genau
"""

import requests
from bs4 import BeautifulSoup
import re
import warnings
warnings.filterwarnings('ignore')

BASE_URL = "https://greiner.eautoseller.de/"
USERNAME = "fGreiner"
PASSWORD = "fGreiner12"

session = requests.Session()
session.verify = False

# Browser-ähnliche Headers
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
})

def analyze_login_page():
    """Analysiert die Login-Seite genau"""
    print("=" * 60)
    print("LOGIN-SEITE ANALYSE")
    print("=" * 60)
    
    response = session.get(BASE_URL)
    print(f"✅ Status: {response.status_code}")
    
    # HTML speichern für Analyse
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    
    # Login-Formular finden
    forms = soup.find_all('form')
    print(f"\n📋 {len(forms)} Formulare gefunden")
    
    for i, form in enumerate(forms):
        print(f"\n--- Formular {i+1} ---")
        print(f"Action: {form.get('action', 'N/A')}")
        print(f"Method: {form.get('method', 'N/A')}")
        print(f"ID: {form.get('id', 'N/A')}")
        print(f"Class: {form.get('class', 'N/A')}")
        
        # Alle Input-Felder
        inputs = form.find_all(['input', 'textarea', 'select', 'button'])
        print(f"\nInput-Felder ({len(inputs)}):")
        for inp in inputs:
            inp_type = inp.get('type', inp.name)
            inp_name = inp.get('name', 'N/A')
            inp_id = inp.get('id', 'N/A')
            inp_value = inp.get('value', '')
            print(f"   - Type: {inp_type}, Name: {inp_name}, ID: {inp_id}, Value: {inp_value[:50]}")
    
    # JavaScript analysieren
    scripts = soup.find_all('script')
    print(f"\n📜 {len(scripts)} Script-Tags gefunden")
    
    for i, script in enumerate(scripts):
        script_src = script.get('src', '')
        script_content = script.string or ''
        
        if script_src:
            print(f"\n--- Script {i+1} (extern) ---")
            print(f"   Src: {script_src}")
        elif script_content:
            print(f"\n--- Script {i+1} (inline) ---")
            # Suche nach Login-relevantem Code
            if 'login' in script_content.lower() or 'err' in script_content.lower():
                print(f"   → Enthält Login/Error-Logik")
                # Zeige relevante Zeilen
                lines = script_content.split('\n')
                for line in lines:
                    if 'err' in line.lower() or 'login' in line.lower() or 'txtUser' in line or 'txtpwd' in line:
                        print(f"      {line.strip()[:100]}")
    
    # Fehlercodes finden
    err_patterns = [
        r'err\s*=\s*(\d+)',
        r'error\s*=\s*(\d+)',
        r'errCode\s*=\s*(\d+)',
    ]
    
    print(f"\n🔍 Fehlercode-Analyse:")
    for pattern in err_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            print(f"   → Gefunden: {matches}")
    
    # Prüfe ob JavaScript für Login benötigt wird
    if 'onclick' in html or 'onsubmit' in html:
        print(f"\n⚠️  JavaScript-Event-Handler gefunden - möglicherweise JS-Validierung")
    
    return response, soup

def try_login_variants():
    """Versucht verschiedene Login-Varianten"""
    print("\n" + "=" * 60)
    print("LOGIN-VARIANTEN TEST")
    print("=" * 60)
    
    response, soup = analyze_login_page()
    
    # Finde Login-Formular
    login_form = soup.find('form')
    if not login_form:
        print("❌ Kein Formular gefunden")
        return False
    
    action = login_form.get('action', 'login.asp')
    login_url = BASE_URL.rstrip('/') + '/' + action.lstrip('/')
    
    # Basis-Login-Daten
    base_data = {
        'txtUser': USERNAME,
        'txtpwd': PASSWORD,
    }
    
    # Alle Felder aus Formular
    for inp in login_form.find_all(['input', 'select', 'textarea']):
        inp_type = inp.get('type', '').lower()
        name = inp.get('name')
        value = inp.get('value', '')
        
        if not name:
            continue
        
        # Select-Felder
        if inp.name == 'select':
            # Nimm ersten Option-Wert
            options = inp.find_all('option')
            if options:
                value = options[0].get('value', options[0].text.strip())
            base_data[name] = value
            print(f"   → Select-Feld gefunden: {name} = {value}")
        # Checkboxen
        elif inp_type == 'checkbox':
            if inp.get('checked') or value:
                base_data[name] = value or '1'
        # Hidden Fields
        elif inp_type == 'hidden':
            base_data[name] = value
        # Submit-Button (nicht in Daten)
        elif inp_type == 'submit':
            pass  # Nicht in Daten
        # Andere Felder (bereits in base_data)
        elif name not in base_data:
            base_data[name] = value
    
    # Varianten testen
    variants = [
        ('Standard', base_data),
        ('Mit Submit', {**base_data, 'submit': '1'}),
        ('Mit Login-Button', {**base_data, 'btnLogin': 'Anmelden'}),
        ('Mit Login-Button 2', {**base_data, 'Login': 'Anmelden'}),
        ('Mit Action', {**base_data, 'action': 'login'}),
    ]
    
    for name, data in variants:
        print(f"\n🧪 Teste: {name}")
        print(f"   Daten: {list(data.keys())}")
        
        try:
            resp = session.post(login_url, data=data, allow_redirects=True, timeout=10)
            print(f"   Status: {resp.status_code}")
            print(f"   URL: {resp.url}")
            
            if 'err=' not in resp.url:
                print(f"   ✅ KEIN FEHLERCODE - Möglicherweise erfolgreich!")
                # Prüfe ob wir eingeloggt sind
                if 'login' not in resp.url.lower() or 'main' in resp.url.lower() or 'index' in resp.url.lower():
                    print(f"   ✅✅ LOGIN ERFOLGREICH!")
                    return True
            else:
                err = resp.url.split('err=')[1].split('&')[0] if 'err=' in resp.url else 'N/A'
                print(f"   ❌ Fehlercode: err={err}")
        except Exception as e:
            print(f"   ❌ Fehler: {e}")
    
    return False

if __name__ == '__main__':
    print("🔍 eAutoseller Login Debug")
    print()
    
    if try_login_variants():
        print("\n✅ Login erfolgreich!")
    else:
        print("\n❌ Alle Login-Varianten fehlgeschlagen")
        print("\n💡 Mögliche Gründe:")
        print("   - JavaScript-Validierung erforderlich")
        print("   - Captcha vorhanden")
        print("   - Session-Cookie-Problem")
        print("   - Falsche Credentials")
        print("\n📝 Empfehlung: Browser-Analyse durchführen")

