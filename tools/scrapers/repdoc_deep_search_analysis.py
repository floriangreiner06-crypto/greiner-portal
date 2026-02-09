#!/usr/bin/env python3
"""
RepDoc Deep Search Analysis
===========================
Tiefere Analyse: Prüft JavaScript, AJAX-Requests und alle möglichen API-Calls.
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

def deep_analysis():
    """Tiefere Analyse mit längerer Wartezeit und JavaScript-Monitoring"""
    
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    service = Service(executable_path='/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    all_requests = []
    
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
        time.sleep(8)
        
        # Leere Logs
        driver.get_log('performance')
        
        # Finde Suchfeld und führe Suche aus
        print("\n=== 3. Führe Suche aus ===")
        search_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='search']")
        search_done = False
        
        for inp in search_inputs:
            try:
                if inp.is_displayed() and inp.is_enabled():
                    inp.clear()
                    inp.send_keys("1109AL")
                    time.sleep(1)
                    inp.send_keys(Keys.RETURN)
                    search_done = True
                    print("✅ Suche ausgeführt")
                    break
            except:
                continue
        
        if not search_done:
            print("⚠️ Suche nicht ausgeführt - versuche JavaScript")
            driver.execute_script("""
                var inputs = document.querySelectorAll('input[type="text"], input[type="search"]');
                for(var i=0; i<inputs.length; i++) {
                    if(inputs[i].offsetParent !== null) {
                        inputs[i].value = '1109AL';
                        inputs[i].dispatchEvent(new Event('input', { bubbles: true }));
                        var form = inputs[i].closest('form');
                        if(form) form.submit();
                        break;
                    }
                }
            """)
        
        # Warte länger und sammle ALLE Requests
        print("\n=== 4. Sammle alle Network-Requests (20 Sekunden) ===")
        for i in range(20):
            time.sleep(1)
            try:
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
                            
                            # Sammle ALLE Requests (nicht nur API)
                            if url and url not in [r['url'] for r in all_requests]:
                                all_requests.append({
                                    'url': url,
                                    'method': request.get('method', 'GET'),
                                    'headers': request.get('headers', {}),
                                    'postData': request.get('postData', ''),
                                    'timestamp': time.time()
                                })
                    except:
                        continue
                        
                if i % 5 == 0:
                    print(f"  ... {i}/20 Sekunden, {len(all_requests)} Requests gesammelt")
            except:
                continue
        
        # Analysiere Requests
        print(f"\n=== 5. Analysiere {len(all_requests)} Requests ===")
        
        api_requests = []
        search_related = []
        json_responses = []
        
        for req in all_requests:
            url = req['url']
            
            # API-Requests
            if any(x in url.lower() for x in ['lite.repdoc.com', '/api/', 'dataservice', '.json', 'ajax']):
                api_requests.append(req)
            
            # Such-bezogene Requests
            if any(x in url.lower() for x in ['search', 'suche', 'query', '1109al', 'teile', 'ersatzteil', 'parts']):
                search_related.append(req)
            
            # JSON-Responses
            if '.json' in url or 'application/json' in str(req.get('headers', {})).lower():
                json_responses.append(req)
        
        # Speichere alle Requests
        with open('/tmp/repdoc_all_requests.json', 'w') as f:
            json.dump({
                'all_requests': all_requests,
                'api_requests': api_requests,
                'search_related': search_related,
                'json_responses': json_responses
            }, f, indent=2)
        
        print(f"\n=== 6. Ergebnisse ===")
        print(f"Alle Requests: {len(all_requests)}")
        print(f"API-Requests: {len(api_requests)}")
        print(f"Such-bezogene: {len(search_related)}")
        print(f"JSON-Responses: {len(json_responses)}")
        
        if api_requests:
            print("\n✅ API-REQUESTS GEFUNDEN:")
            for i, req in enumerate(api_requests[:10], 1):
                print(f"\n{i}. {req['method']} {req['url']}")
                if 'Authorization' in req['headers']:
                    print(f"   Auth: {req['headers']['Authorization'][:50]}...")
        
        if search_related:
            print("\n🔍 SUCH-BEZOGENE REQUESTS:")
            for i, req in enumerate(search_related[:10], 1):
                print(f"\n{i}. {req['method']} {req['url']}")
        
        # Prüfe auch die aktuelle URL
        current_url = driver.current_url
        print(f"\nAktuelle URL nach Suche: {current_url}")
        
        # Prüfe ob Suchergebnisse vorhanden sind
        try:
            results = driver.find_elements(By.CSS_SELECTOR, "table, .result, .search-result, .product, [class*='result']")
            print(f"Suchergebnis-Elemente gefunden: {len(results)}")
        except:
            print("Keine Suchergebnis-Elemente gefunden")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    print("🔍 RepDoc Deep Search Analysis")
    print("=" * 70)
    deep_analysis()
