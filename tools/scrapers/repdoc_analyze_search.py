#!/usr/bin/env python3
"""Analysiere RepDoc Suchergebnisse HTML-Struktur"""

import time
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

def analyze_search_results():
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    service = Service(executable_path='/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Login
        print("=== Login ===")
        driver.get(BASE_URL)
        time.sleep(3)
        
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginInputUser"))
        )
        username_field.send_keys(USERNAME)
        
        password_field = driver.find_element(By.ID, "loginInputPassword")
        password_field.send_keys(PASSWORD)
        
        login_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'LOGIN')]"))
        )
        login_button.click()
        time.sleep(5)
        
        print("✅ Login erfolgreich")
        
        # Suche
        print("\n=== Suche nach 1109AL ===")
        driver.get("https://www2.repdoc.com/DE")
        time.sleep(3)
        
        # Suche nach Suchfeld
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
                        print(f"✅ Suchfeld gefunden: {selector}")
                        break
                if search_input:
                    break
            except:
                continue
        
        if not search_input:
            print("❌ Suchfeld nicht gefunden - versuche alle Inputs")
            all_inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in all_inputs:
                if inp.is_displayed():
                    print(f"  - type={inp.get_attribute('type')}, id={inp.get_attribute('id')}, placeholder={inp.get_attribute('placeholder')}")
        
        if search_input:
            search_input.clear()
            search_input.send_keys("1109AL")
            time.sleep(0.5)
            search_input.send_keys(Keys.RETURN)
            time.sleep(8)
        
        # Analysiere Ergebnisse
        print("\n=== HTML-Struktur Analyse ===")
        html = driver.page_source
        
        # Speichere HTML
        with open('/tmp/repdoc_search_results.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("HTML gespeichert in /tmp/repdoc_search_results.html")
        
        # Suche nach Tabellen
        print("\n=== Tabellen ===")
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"Anzahl Tabellen: {len(tables)}")
        
        for i, table in enumerate(tables):
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"Tabelle {i+1}: {len(rows)} Zeilen")
            if len(rows) > 0:
                # Erste Zeile analysieren
                first_row = rows[0]
                cells = first_row.find_elements(By.TAG_NAME, "td")
                if len(cells) == 0:
                    cells = first_row.find_elements(By.TAG_NAME, "th")
                print(f"  Erste Zeile: {len(cells)} Zellen")
                if len(cells) > 0:
                    print(f"  Zell-Text: {[c.text[:30] for c in cells[:5]]}")
        
        # Suche nach Ergebnis-Containern
        print("\n=== Ergebnis-Container ===")
        container_selectors = [
            ".result",
            ".search-result",
            ".product",
            ".article",
            "[data-part]",
            "[class*='result']",
            "[class*='product']",
            "[class*='article']"
        ]
        
        for selector in container_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ {selector}: {len(elements)} Element(e)")
                    if len(elements) > 0:
                        print(f"   Erster Text: {elements[0].text[:100]}")
            except:
                pass
        
        # Suche nach Preisen im HTML
        print("\n=== Preise im HTML ===")
        import re
        price_matches = re.findall(r'(\d+[,.]?\d*)\s*€', html)
        if price_matches:
            print(f"Gefundene Preise: {price_matches[:10]}")
        
        # Zeige URL
        print(f"\nAktuelle URL: {driver.current_url}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_search_results()
