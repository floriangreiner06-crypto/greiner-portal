#!/usr/bin/env python3
"""
RepDoc API Header Analyzer
==========================
Analysiert die tatsächlichen HTTP-Headers der API-Requests.
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

def analyze_api_headers():
    """Analysiere Headers der API-Requests"""
    
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    service = Service(executable_path='/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    api_requests = []
    
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
        
        # Suche nach Suchfeld
        search_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='search']")
        for inp in search_inputs:
            if inp.is_displayed():
                inp.send_keys("1109AL")
                time.sleep(0.5)
                inp.send_keys(Keys.RETURN)
                break
        
        time.sleep(10)  # Warte auf alle Requests
        
        print("\n=== 3. Analysiere API-Requests mit Headers ===")
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
                    
                    # Nur API-Requests
                    if 'lite.repdoc.com' in url or '/api/' in url or 'DataService' in url:
                        headers = request.get('headers', {})
                        post_data = request.get('postData', '')
                        
                        api_requests.append({
                            'url': url,
                            'method': request.get('method', 'GET'),
                            'headers': headers,
                            'postData': post_data
                        })
                        
                        print(f"\n✅ API-Request gefunden:")
                        print(f"  URL: {url}")
                        print(f"  Method: {request.get('method', 'GET')}")
                        print(f"  Headers:")
                        for key, value in headers.items():
                            if key.lower() in ['authorization', 'x-requested-with', 'referer', 'origin', 'cookie']:
                                print(f"    {key}: {value[:100]}")
                        if post_data:
                            print(f"  PostData: {post_data[:200]}")
                
            except Exception as e:
                continue
        
        print(f"\n=== 4. Zusammenfassung ===")
        print(f"Gefundene API-Requests: {len(api_requests)}")
        
        # Speichere für weitere Analyse
        with open('/tmp/repdoc_api_requests.json', 'w') as f:
            json.dump(api_requests, f, indent=2)
        print("API-Requests gespeichert in /tmp/repdoc_api_requests.json")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_api_headers()
