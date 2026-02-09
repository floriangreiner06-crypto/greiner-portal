#!/usr/bin/env python3
"""
RepDoc API Explorer
==================
Analysiert Netzwerk-Requests von RepDoc, um versteckte API-Endpoints zu finden.
Ähnlich wie servicebox_network_analyzer.py
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

def analyze_network_requests():
    """Analysiere Netzwerk-Requests während Login und Suche"""
    
    # Chrome mit Logging aktivieren
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Performance-Logging aktivieren (neue Syntax)
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    service = Service(executable_path='/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    api_requests = []
    
    try:
        print("=== 1. Login ===")
        driver.get(BASE_URL)
        time.sleep(3)
        
        # Login
        username_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "loginInputUser"))
        )
        username_field.clear()
        username_field.send_keys(USERNAME)
        
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginInputPassword"))
        )
        password_field.clear()
        password_field.send_keys(PASSWORD)
        
        # Login-Button finden (verschiedene Varianten)
        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'LOGIN') or contains(@class, 'mdc-button--raised')]"))
            )
            login_button.click()
        except:
            # Fallback: Suche nach Button mit CSS
            login_button = driver.find_element(By.CSS_SELECTOR, "button.mdc-button--raised, button[type='submit']")
            login_button.click()
        
        time.sleep(8)  # Mehr Zeit für Login
        
        # Analysiere Logs nach Login
        print("\n=== 2. Analysiere Netzwerk-Requests (Login) ===")
        try:
            logs = driver.get_log('performance')
            for log_entry in logs:
                try:
                    message_str = log_entry.get('message', '')
                    message = json.loads(message_str) if isinstance(message_str, str) else message_str
                    
                    # Extrahiere Request-Informationen
                    method = message.get('message', {}).get('method', '')
                    params = message.get('message', {}).get('params', {})
                    request = params.get('request', {})
                    url = request.get('url', '')
                    
                    # Prüfe auf API-Patterns
                    if any(x in url.lower() for x in ['api', 'json', 'ajax', 'rest', '/service/', '/ws/', '.do', 'search', 'suche']):
                        api_requests.append({
                            'url': url,
                            'method': method,
                            'request': request
                        })
                        print(f"  ✅ API-Request: {method} {url[:100]}")
                except:
                    # Fallback: String-Suche
                    message_str = str(log_entry.get('message', ''))
                    if any(x in message_str.lower() for x in ['api', 'json', 'ajax', 'rest', '/service/', '/ws/', '.do']):
                        api_requests.append(log_entry)
                        print(f"  ✅ Potentieller API-Request: {message_str[:200]}")
        except Exception as e:
            print(f"  ⚠️ Fehler beim Lesen der Logs: {e}")
        
        # Suche
        print("\n=== 3. Suche ===")
        driver.get("https://www2.repdoc.com/DE")
        time.sleep(3)
        
        # Finde Suchfeld und suche
        search_selectors = [
            "input[type='search']",
            "input[type='text']",
            "input[placeholder*='Teile']",
            "input[placeholder*='Suche']",
            "#search",
            ".search-input"
        ]
        
        search_input = None
        for selector in search_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.is_displayed():
                        search_input = el
                        break
                if search_input:
                    break
            except:
                continue
        
        if search_input:
            search_input.clear()
            search_input.send_keys("1109AL")
            time.sleep(0.5)
            search_input.send_keys(Keys.RETURN)
        else:
            print("  ⚠️ Suchfeld nicht gefunden - überspringe Suche")
        
        time.sleep(8)
        
        # Analysiere Logs nach Suche
        print("\n=== 4. Analysiere Netzwerk-Requests (Suche) ===")
        try:
            logs = driver.get_log('performance')
            for log_entry in logs:
                try:
                    message_str = log_entry.get('message', '')
                    message = json.loads(message_str) if isinstance(message_str, str) else message_str
                    
                    # Extrahiere Request-Informationen
                    method = message.get('message', {}).get('method', '')
                    params = message.get('message', {}).get('params', {})
                    request = params.get('request', {})
                    url = request.get('url', '')
                    
                    # Prüfe auf API-Patterns
                    if any(x in url.lower() for x in ['api', 'json', 'ajax', 'rest', '/service/', '/ws/', '.do', 'search', 'suche']):
                        api_requests.append({
                            'url': url,
                            'method': method,
                            'request': request
                        })
                        print(f"  ✅ API-Request: {method} {url[:100]}")
                except:
                    # Fallback: String-Suche
                    message_str = str(log_entry.get('message', ''))
                    if any(x in message_str.lower() for x in ['api', 'json', 'ajax', 'rest', '/service/', '/ws/', '.do', 'search', 'suche']):
                        api_requests.append(log_entry)
                        print(f"  ✅ Potentieller API-Request: {message_str[:200]}")
        except Exception as e:
            print(f"  ⚠️ Fehler beim Lesen der Logs: {e}")
        
        # Zusammenfassung
        print(f"\n=== 5. Zusammenfassung ===")
        print(f"Gefundene API-Requests: {len(api_requests)}")
        
        if len(api_requests) == 0:
            print("⚠️ Keine API-Endpoints gefunden - RepDoc verwendet wahrscheinlich nur HTML-Rendering")
        else:
            print("✅ Potenzielle API-Endpoints gefunden!")
            print("\nNächste Schritte:")
            print("1. Requests analysieren und URLs extrahieren")
            print("2. API-Endpoints mit Requests-Bibliothek testen")
            print("3. Falls erfolgreich: Scraper auf API umstellen")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_network_requests()
