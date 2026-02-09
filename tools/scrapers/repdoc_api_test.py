#!/usr/bin/env python3
"""
RepDoc API Test
==============
Testet die gefundenen API-Endpoints direkt mit Requests.
"""

import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://www2.repdoc.com/DE/Login#Start"
USERNAME = "Greiner_drive"
PASSWORD = "Drive2026!"

# Gefundene API-Endpoints
API_BASE = "https://lite.repdoc.com/WsCloudDataServiceLite/api"
API_ENDPOINTS = {
    'benutzer': f"{API_BASE}/Benutzer/current",
    'arbeitswerte': f"{API_BASE}/Arbeitswerte/list",
    'global_actions': f"{API_BASE}/WsCloudUi/GlobalActions/list?version=5",
}

def get_session_cookies():
    """Login via Selenium und hole Session-Cookies"""
    print("=== 1. Login via Selenium ===")
    
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    service = Service(executable_path='/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get(BASE_URL)
        import time
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
        
        # Hole Cookies
        cookies = driver.get_cookies()
        print(f"✅ Login erfolgreich - {len(cookies)} Cookies erhalten")
        
        # Konvertiere zu Requests-Format
        session_cookies = {c['name']: c['value'] for c in cookies}
        return session_cookies, driver.get_cookies()
        
    finally:
        driver.quit()

def test_api_endpoints(cookies):
    """Teste API-Endpoints mit Session-Cookies"""
    print("\n=== 2. Teste API-Endpoints ===")
    
    session = requests.Session()
    session.cookies.update(cookies)
    
    # Headers (wichtig für API-Calls)
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'de-DE,de;q=0.9',
        'Referer': 'https://www2.repdoc.com/',
        'Origin': 'https://www2.repdoc.com'
    }
    
    results = {}
    
    # Test 1: Benutzer-Info
    print("\n--- Test 1: Benutzer-Info ---")
    try:
        response = session.get(API_ENDPOINTS['benutzer'], headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Erfolg: {json.dumps(data, indent=2)[:500]}")
            results['benutzer'] = data
        else:
            print(f"❌ Fehler: {response.text[:200]}")
            results['benutzer'] = None
    except Exception as e:
        print(f"❌ Exception: {e}")
        results['benutzer'] = None
    
    # Test 2: Arbeitswerte (könnte Teile-Suche sein)
    print("\n--- Test 2: Arbeitswerte-Liste ---")
    try:
        # Versuche verschiedene Parameter
        params = {'PageSize': 10, 'SearchText': '1109AL'}
        response = session.get(API_ENDPOINTS['arbeitswerte'], headers=headers, params=params, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Erfolg: {json.dumps(data, indent=2)[:500]}")
            results['arbeitswerte'] = data
        else:
            print(f"❌ Fehler: {response.text[:200]}")
            results['arbeitswerte'] = None
    except Exception as e:
        print(f"❌ Exception: {e}")
        results['arbeitswerte'] = None
    
    # Test 3: Global Actions
    print("\n--- Test 3: Global Actions ---")
    try:
        response = session.get(API_ENDPOINTS['global_actions'], headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Erfolg: {json.dumps(data, indent=2)[:500]}")
            results['global_actions'] = data
        else:
            print(f"❌ Fehler: {response.text[:200]}")
            results['global_actions'] = None
    except Exception as e:
        print(f"❌ Exception: {e}")
        results['global_actions'] = None
    
    return results

def search_for_parts_api(session, part_number):
    """Suche nach Teilenummer über API"""
    print(f"\n=== 3. Suche nach Teilenummer: {part_number} ===")
    
    # Mögliche Endpoints für Teile-Suche
    search_endpoints = [
        f"{API_BASE}/Teile/search?query={part_number}",
        f"{API_BASE}/Teile/list?SearchText={part_number}",
        f"{API_BASE}/Ersatzteile/search?query={part_number}",
        f"{API_BASE}/Parts/search?query={part_number}",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www2.repdoc.com/',
    }
    
    for endpoint in search_endpoints:
        try:
            print(f"  Teste: {endpoint}")
            response = session.get(endpoint, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Erfolg: {json.dumps(data, indent=2)[:300]}")
                return data
            else:
                print(f"  ⚠️ Status {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"  ❌ Exception: {e}")
    
    return None

if __name__ == "__main__":
    print("🚀 RepDoc API Test")
    print("=" * 70)
    
    # 1. Login und Cookies holen
    session_cookies, raw_cookies = get_session_cookies()
    
    # 2. API-Endpoints testen
    results = test_api_endpoints(session_cookies)
    
    # 3. Teile-Suche testen
    session = requests.Session()
    session.cookies.update(session_cookies)
    search_result = search_for_parts_api(session, "1109AL")
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("=== ZUSAMMENFASSUNG ===")
    print(f"API-Endpoints getestet: {len(results)}")
    print(f"Erfolgreich: {sum(1 for r in results.values() if r is not None)}")
    
    if search_result:
        print("✅ Teile-Suche über API möglich!")
    else:
        print("⚠️ Teile-Suche über API nicht gefunden - weiter mit Scraping")
