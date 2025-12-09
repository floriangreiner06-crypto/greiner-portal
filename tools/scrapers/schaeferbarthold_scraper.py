#!/usr/bin/env python3
"""
Schäferbarthold Scraper - Funktionierender Prototyp
"""

import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

KUNDENNUMMER = "1003941"
PASSWORT = "AO443494"
BASE_URL = "https://b2b.schaeferbarthold.com"

def get_driver():
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=chrome_options)

def login(driver):
    """Login bei Schäferbarthold"""
    driver.get(BASE_URL)
    time.sleep(3)
    
    if 'auth' in driver.current_url:
        username = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username.send_keys(KUNDENNUMMER)
        
        password = driver.find_element(By.ID, "password")
        password.send_keys(PASSWORT)
        
        driver.find_element(By.ID, "kc-login").click()
        time.sleep(5)
    
    return 'b2b.schaeferbarthold.com' in driver.current_url

def search_part(driver, teilenummer):
    """Suche nach Teilenummer und extrahiere Preis"""
    
    # Warte bis Seite geladen
    time.sleep(2)
    
    # Suchfeld finden (Referenznummer)
    try:
        # Das Feld hat ein dynamisches ID, suche nach Label
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.MuiInputBase-input"))
        )
        
        # Leeren und eingeben
        search_input.clear()
        search_input.send_keys(teilenummer)
        print(f"   ✅ Teilenummer eingegeben: {teilenummer}")
        
        time.sleep(1)
        
        # Enter drücken oder Such-Button finden
        search_input.send_keys(Keys.RETURN)
        print("   ✅ Suche gestartet")
        
        time.sleep(5)
        
        # Screenshot
        driver.save_screenshot(f'/opt/greiner-portal/logs/sb_search_{teilenummer}.png')
        
        # Preise extrahieren
        page_source = driver.page_source
        
        # Suche nach Preis-Pattern
        prices = re.findall(r'([\d,]+)\s*[€&]', page_source)
        
        # Suche nach Artikel-Karten mit Preis
        results = []
        
        # CSS-Klasse für Preise: css-1kx7emu
        price_elements = driver.find_elements(By.CSS_SELECTOR, ".css-1kx7emu")
        
        for pe in price_elements:
            text = pe.text.strip()
            if '€' in text or text.replace(',', '').replace('.', '').isdigit():
                results.append(text)
        
        return {
            'teilenummer': teilenummer,
            'preise_gefunden': results,
            'raw_prices': prices[:10]
        }
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        driver.save_screenshot('/opt/greiner-portal/logs/sb_error.png')
        return None

def main():
    print("🔍 SCHÄFERBARTHOLD SCRAPER")
    print("=" * 70)
    
    driver = get_driver()
    
    try:
        # Login
        print("\n[1] LOGIN...")
        if login(driver):
            print("   ✅ Eingeloggt!")
        else:
            print("   ❌ Login fehlgeschlagen")
            return
        
        # Test-Suche
        test_parts = ["9837096880", "1051610", "13507405"]
        
        for part in test_parts:
            print(f"\n[SUCHE] {part}")
            result = search_part(driver, part)
            if result:
                print(f"   Ergebnis: {json.dumps(result, indent=2)}")
            
            # Zurück zur Startseite
            driver.get(BASE_URL)
            time.sleep(2)
        
    finally:
        driver.quit()
    
    print("\n" + "=" * 70)
    print("✅ Scraper-Test abgeschlossen!")

if __name__ == "__main__":
    main()
