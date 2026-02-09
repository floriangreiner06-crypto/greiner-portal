#!/usr/bin/env python3
"""
RepDoc Search Endpoint Finder
=============================
Analysiert Network-Requests während einer echten Teile-Suche,
um den korrekten API-Endpoint zu finden.
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

BASE_URL = "https://www2.repdoc.com/DE/Login#Start"
USERNAME = "Greiner_drive"
PASSWORD = "Drive2026!"

def find_search_endpoint():
    """Finde den tatsächlichen API-Endpoint für Teile-Suche"""
    
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    service = Service(executable_path='/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    search_requests = []
    all_api_requests = []
    
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
        
        # Navigiere zur Suche
        print("\n=== 2. Navigiere zur Suche ===")
        driver.get("https://www2.repdoc.com/DE")
        time.sleep(5)
        
        # Leere Logs vor Suche
        driver.get_log('performance')
        
        # Finde Suchfeld
        print("\n=== 3. Suche nach Teilenummer '1109AL' ===")
        search_input = None
        search_selectors = [
            "input[type='search']",
            "input[type='text']",
            "input[placeholder*='Teile']",
            "input[placeholder*='Suche']",
            "input[placeholder*='Teilenummer']",
            "input[id*='search']",
            "input[name*='search']",
            "#search",
            ".search-input"
        ]
        
        for selector in search_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.is_displayed() and el.is_enabled():
                        search_input = el
                        print(f"✅ Suchfeld gefunden: {selector}")
                        break
                if search_input:
                    break
            except:
                continue
        
        if not search_input:
            print("⚠️ Suchfeld nicht gefunden - versuche alle Inputs")
            all_inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in all_inputs:
                if inp.is_displayed() and inp.is_enabled():
                    print(f"  Input gefunden: type={inp.get_attribute('type')}, id={inp.get_attribute('id')}, placeholder={inp.get_attribute('placeholder')}")
                    # Versuche es trotzdem
                    try:
                        inp.send_keys("1109AL")
                        time.sleep(0.5)
                        inp.send_keys(Keys.RETURN)
                        search_input = inp
                        break
                    except:
                        continue
        
        if search_input:
            search_input.clear()
            search_input.send_keys("1109AL")
            time.sleep(1)
            search_input.send_keys(Keys.RETURN)
            print("✅ Suche ausgeführt")
        else:
            print("❌ Suchfeld nicht gefunden - versuche JavaScript-Suche")
            # JavaScript-Fallback
            driver.execute_script("""
                var inputs = document.querySelectorAll('input[type="text"], input[type="search"]');
                for(var i=0; i<inputs.length; i++) {
                    if(inputs[i].offsetParent !== null) {
                        inputs[i].value = '1109AL';
                        inputs[i].dispatchEvent(new Event('input', { bubbles: true }));
                        inputs[i].dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
                        break;
                    }
                }
            """)
        
        # Warte auf Suchergebnisse und API-Requests
        print("\n=== 4. Warte auf API-Requests (15 Sekunden) ===")
        time.sleep(15)
        
        # Analysiere alle Requests
        print("\n=== 5. Analysiere Network-Requests ===")
        logs = driver.get_log('performance')
        
        for log_entry in logs:
            try:
                message_str = log_entry.get('message', '')
                message = json.loads(message_str) if isinstance(message_str, str) else message_str
                
                method = message.get('message', {}).get('method', '')
                params = message.get('message', {}).get('params', {})
                
                if method == 'Network.requestWillBeSent':
                    request = params.get('request', {})
                    url = request.get('url', '')
                    method_type = request.get('method', 'GET')
                    headers = request.get('headers', {})
                    post_data = request.get('postData', '')
                    
                    # Alle API-Requests sammeln
                    if any(x in url.lower() for x in ['lite.repdoc.com', '/api/', 'dataservice', 'search', 'suche', 'teile', 'ersatzteil', 'parts']):
                        all_api_requests.append({
                            'url': url,
                            'method': method_type,
                            'headers': headers,
                            'postData': post_data
                        })
                        
                        # Speziell für Suche
                        if any(x in url.lower() for x in ['search', 'suche', 'query', 'list', 'teile', 'ersatzteil', 'parts']):
                            search_requests.append({
                                'url': url,
                                'method': method_type,
                                'headers': headers,
                                'postData': post_data
                            })
                            
                            print(f"\n🔍 POTENTIELLER SUCH-ENDPOINT:")
                            print(f"  URL: {url}")
                            print(f"  Method: {method_type}")
                            if 'Authorization' in headers:
                                print(f"  Auth: {headers['Authorization'][:50]}...")
                            if post_data:
                                print(f"  PostData: {post_data[:200]}")
                
                elif method == 'Network.responseReceived':
                    response = params.get('response', {})
                    url = response.get('url', '')
                    status = response.get('status', 0)
                    
                    # Nur erfolgreiche Responses für Suche
                    if status == 200 and any(x in url.lower() for x in ['search', 'suche', 'query', 'list', 'teile', 'ersatzteil', 'parts', 'api']):
                        print(f"\n✅ ERFOLGREICHE RESPONSE:")
                        print(f"  URL: {url}")
                        print(f"  Status: {status}")
                        
            except Exception as e:
                continue
        
        # Speichere alle Requests
        with open('/tmp/repdoc_search_requests.json', 'w') as f:
            json.dump({
                'all_api_requests': all_api_requests,
                'search_requests': search_requests
            }, f, indent=2)
        
        print(f"\n=== 6. Zusammenfassung ===")
        print(f"Alle API-Requests: {len(all_api_requests)}")
        print(f"Potentielle Such-Requests: {len(search_requests)}")
        
        if search_requests:
            print("\n✅ POTENTIELLE SUCH-ENDPOINTS GEFUNDEN!")
            for i, req in enumerate(search_requests, 1):
                print(f"\n{i}. {req['method']} {req['url']}")
        else:
            print("\n⚠️ Keine eindeutigen Such-Endpoints gefunden")
            print("Möglicherweise verwendet RepDoc HTML-Rendering statt API")
            print("\nAlle API-Requests:")
            for i, req in enumerate(all_api_requests[:10], 1):
                print(f"{i}. {req['method']} {req['url']}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    print("🔍 RepDoc Search Endpoint Finder")
    print("=" * 70)
    find_search_endpoint()
