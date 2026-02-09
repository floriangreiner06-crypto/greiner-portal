#!/usr/bin/env python3
"""
RepDoc API Client mit JWT-Token
===============================
Extrahiert JWT-Token und testet API-Endpoints.
"""

import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://www2.repdoc.com/DE/Login#Start"
USERNAME = "Greiner_drive"
PASSWORD = "Drive2026!"
API_BASE = "https://lite.repdoc.com/WsCloudDataServiceLite/api"

def extract_auth_token():
    """Extrahiere JWT-Token aus Browser-Requests"""
    
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    service = Service(executable_path='/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    auth_token = None
    
    try:
        print("=== 1. Login ===")
        driver.get(BASE_URL)
        time.sleep(3)
        
        username_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "loginInputUser"))
        )
        username_field.clear()
        username_field.send_keys(USERNAME)
        
        password_field = driver.find_element(By.ID, "loginInputPassword")
        password_field.clear()
        password_field.send_keys(PASSWORD)
        
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'LOGIN') or contains(@class, 'mdc-button--raised')]"))
        )
        login_button.click()
        time.sleep(8)
        
        print("✅ Login erfolgreich")
        
        # Navigiere zur Hauptseite (wo API-Calls gemacht werden)
        print("\n=== 2. Navigiere zur Hauptseite ===")
        driver.get("https://www2.repdoc.com/DE")
        time.sleep(10)  # Warte auf API-Calls
        
        # Analysiere Logs
        print("\n=== 3. Extrahiere Auth-Token ===")
        logs = driver.get_log('performance')
        
        for log_entry in logs:
            try:
                message_str = log_entry.get('message', '')
                message = json.loads(message_str) if isinstance(message_str, str) else message_str
                
                method = message.get('message', {}).get('method', '')
                params = message.get('message', {}).get('params', {})
                
                if method == 'Network.requestWillBeSent':
                    request = params.get('request', {})
                    headers = request.get('headers', {})
                    
                    # Suche nach Authorization-Header
                    if 'Authorization' in headers:
                        auth_token = headers['Authorization']
                        print(f"✅ Token gefunden: {auth_token[:50]}...")
                        break
                        
            except:
                continue
        
        if not auth_token:
            print("⚠️ Kein Token gefunden - versuche erneut...")
            time.sleep(5)
            logs = driver.get_log('performance')
            for log_entry in logs:
                try:
                    message_str = log_entry.get('message', '')
                    message = json.loads(message_str) if isinstance(message_str, str) else message_str
                    method = message.get('message', {}).get('method', '')
                    params = message.get('message', {}).get('params', {})
                    if method == 'Network.requestWillBeSent':
                        request = params.get('request', {})
                        headers = request.get('headers', {})
                        if 'Authorization' in headers:
                            auth_token = headers['Authorization']
                            print(f"✅ Token gefunden (2. Versuch): {auth_token[:50]}...")
                            break
                except:
                    continue
        
    finally:
        driver.quit()
    
    return auth_token

def test_api_with_token(token):
    """Teste API-Endpoints mit Token"""
    print("\n=== 4. Teste API-Endpoints mit Token ===")
    
    headers = {
        'Authorization': token,
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'de-DE,de;q=0.9',
        'Referer': 'https://www.repdoc.com/',
        'Origin': 'https://www.repdoc.com',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    # Test 1: Benutzer-Info
    print("\n--- Test: Benutzer-Info ---")
    try:
        response = requests.get(f"{API_BASE}/Benutzer/current", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Erfolg: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
            return True
        else:
            print(f"❌ Fehler: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    return False

def search_parts_via_api(token, part_number):
    """Suche nach Teilenummer über API"""
    print(f"\n=== 5. Suche nach Teilenummer: {part_number} ===")
    
    headers = {
        'Authorization': token,
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.repdoc.com/',
        'Origin': 'https://www.repdoc.com',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    # Mögliche Endpoints (basierend auf gefundenen Patterns)
    search_endpoints = [
        f"{API_BASE}/Ersatzteile/search?query={part_number}",
        f"{API_BASE}/Ersatzteile/list?SearchText={part_number}",
        f"{API_BASE}/Ersatzteile/list?PageSize=10&SearchText={part_number}",
        f"{API_BASE}/Teile/search?query={part_number}",
        f"{API_BASE}/Parts/search?query={part_number}",
    ]
    
    for endpoint in search_endpoints:
        try:
            print(f"  Teste: {endpoint}")
            response = requests.get(endpoint, headers=headers, timeout=10)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Erfolg!")
                print(f"  Daten: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
                return data
            elif response.status_code == 404:
                print(f"  ⚠️ 404 - Endpoint nicht gefunden")
            else:
                print(f"  ⚠️ {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"  ❌ Exception: {e}")
    
    return None

if __name__ == "__main__":
    print("🚀 RepDoc API Client mit JWT-Token")
    print("=" * 70)
    
    # 1. Token extrahieren
    token = extract_auth_token()
    
    if not token:
        print("\n❌ Kein Token gefunden - API-Zugriff nicht möglich")
        exit(1)
    
    # 2. API testen
    api_works = test_api_with_token(token)
    
    if api_works:
        # 3. Teile-Suche testen
        search_result = search_parts_via_api(token, "1109AL")
        
        if search_result:
            print("\n" + "=" * 70)
            print("✅ ERFOLG: API-Zugriff funktioniert!")
            print("Nächster Schritt: RepDoc-Scraper auf API umstellen")
        else:
            print("\n" + "=" * 70)
            print("⚠️ API funktioniert, aber Teile-Suche-Endpoint nicht gefunden")
            print("Weiter mit Scraping für Teile-Suche")
    else:
        print("\n" + "=" * 70)
        print("❌ API-Zugriff funktioniert nicht - weiter mit Scraping")
