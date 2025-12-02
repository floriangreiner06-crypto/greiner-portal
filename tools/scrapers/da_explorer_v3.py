#!/usr/bin/env python3
"""
DA (Digitales Autohaus) - Vollständige Exploration v3
Geht alle Module durch und dokumentiert die Struktur
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import json
from datetime import datetime

# Konfiguration
DA_URL = "https://werkstattplanung.net/greiner/deggendorf/kic/da/auth.html#/"
DA_USER = "florian.greiner@auto-greiner.de"
DA_PASS = "Hyundai2025!"

OUTPUT_DIR = "/mnt/greiner-portal-sync/DA_Screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    service = Service('/usr/local/bin/chromedriver')
    return webdriver.Chrome(service=service, options=options)

def login(driver, wait):
    """Login durchführen"""
    print("1. Login...")
    driver.get(DA_URL)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']")))
    time.sleep(2)
    
    driver.find_element(By.CSS_SELECTOR, "input[name='username']").send_keys(DA_USER)
    driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys(DA_PASS)
    driver.find_element(By.CSS_SELECTOR, "button[data-testid='LoginView.login-button']").click()
    
    time.sleep(5)
    print("   ✓ Eingeloggt")
    return "auth" not in driver.current_url.lower()

def get_menu_items(driver):
    """Alle Menü-Items aus der Sidebar holen"""
    items = []
    
    # V-list-items in der Navigation
    nav_elements = driver.find_elements(By.CSS_SELECTOR, ".v-navigation-drawer .v-list-item, .v-list-group__header")
    
    for el in nav_elements:
        try:
            text = el.text.strip().split('\n')[0]  # Nur erste Zeile
            if text and len(text) > 1 and len(text) < 30:
                items.append({
                    'text': text,
                    'element': el
                })
        except:
            pass
    
    return items

def explore_module(driver, wait, module_name, timestamp):
    """Ein Modul erkunden und dokumentieren"""
    print(f"\n   → {module_name}")
    
    result = {
        'name': module_name,
        'sub_items': [],
        'tables': [],
        'forms': [],
        'buttons': []
    }
    
    try:
        # Modul anklicken
        el = driver.find_element(By.XPATH, f"//div[contains(@class, 'v-list-item')]//div[contains(text(), '{module_name}')]")
        el.click()
        time.sleep(3)
        
        # Screenshot
        safe_name = "".join(c if c.isalnum() else "_" for c in module_name)[:20]
        screenshot_path = f"{OUTPUT_DIR}/{timestamp}_mod_{safe_name}.png"
        driver.save_screenshot(screenshot_path)
        print(f"      ✓ Screenshot: {safe_name}")
        
        # Sub-Navigation finden
        sub_items = driver.find_elements(By.CSS_SELECTOR, ".v-tabs .v-tab, .v-list-group__items .v-list-item")
        for sub in sub_items:
            try:
                text = sub.text.strip()
                if text and len(text) > 1:
                    result['sub_items'].append(text)
            except:
                pass
        
        # Tabellen finden
        tables = driver.find_elements(By.CSS_SELECTOR, "table, .v-data-table")
        result['tables'] = len(tables)
        
        # Formulare/Inputs finden
        inputs = driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
        result['forms'] = len(inputs)
        
        # Buttons finden
        buttons = driver.find_elements(By.CSS_SELECTOR, "button .v-btn__content, .v-btn")
        for btn in buttons[:10]:
            try:
                text = btn.text.strip()
                if text and len(text) > 1 and len(text) < 30:
                    result['buttons'].append(text)
            except:
                pass
        
        # Unique buttons
        result['buttons'] = list(set(result['buttons']))
        
        if result['sub_items']:
            print(f"      Sub-Items: {', '.join(result['sub_items'][:5])}")
        
    except Exception as e:
        print(f"      ✗ Fehler: {e}")
        result['error'] = str(e)
    
    return result

def main():
    driver = setup_driver()
    wait = WebDriverWait(driver, 20)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    modules_to_explore = [
        "AW Übersicht",
        "Serviceplanung", 
        "Werkstattplanung",
        "Fuhrpark",
        "Räder/Reifen",
        "Kapazitätsplanung",
        "Verwaltung",
        "Kalender",
        "Tabellen",
        "Plantafeln"
    ]
    
    results = {
        'timestamp': timestamp,
        'modules': []
    }
    
    try:
        if not login(driver, wait):
            print("Login fehlgeschlagen!")
            return
        
        # Dashboard Screenshot
        driver.save_screenshot(f"{OUTPUT_DIR}/{timestamp}_00_dashboard.png")
        
        print("\n2. Erkunde Module...")
        
        for module in modules_to_explore:
            result = explore_module(driver, wait, module, timestamp)
            results['modules'].append(result)
            
            # Zurück zum Dashboard (Logo klicken oder Navigation)
            try:
                logo = driver.find_element(By.CSS_SELECTOR, ".v-app-bar .v-image, .v-toolbar__title")
                logo.click()
                time.sleep(2)
            except:
                driver.get("https://werkstattplanung.net/greiner/deggendorf/kic/da/#/")
                time.sleep(3)
        
        # Ergebnisse speichern
        with open(f"{OUTPUT_DIR}/{timestamp}_exploration.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*50}")
        print("ZUSAMMENFASSUNG DA-MODULE:")
        print('='*50)
        
        for mod in results['modules']:
            print(f"\n📁 {mod['name']}")
            if mod.get('sub_items'):
                print(f"   Sub-Items: {', '.join(mod['sub_items'][:5])}")
            if mod.get('tables'):
                print(f"   Tabellen: {mod['tables']}")
            if mod.get('buttons'):
                print(f"   Buttons: {', '.join(mod['buttons'][:5])}")
            if mod.get('error'):
                print(f"   ⚠️ Fehler: {mod['error']}")
        
    except Exception as e:
        print(f"FEHLER: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
    
    print(f"\n✓ Ergebnisse in: {OUTPUT_DIR}/{timestamp}_exploration.json")

if __name__ == "__main__":
    main()
