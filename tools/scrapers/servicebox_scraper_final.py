#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Service Box Scraper - FINAL mit JavaScript-Navigation
"""

import os
import sys
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

BASE_DIR = "/opt/greiner-portal"
CREDENTIALS_PATH = f"{BASE_DIR}/config/credentials.json"
SCREENSHOTS_DIR = f"{BASE_DIR}/logs/servicebox_screenshots"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_scraper.log"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def load_credentials():
    log("📋 Lade Credentials...")
    with open(CREDENTIALS_PATH, 'r') as f:
        creds = json.load(f)
    sb_creds = creds['external_systems']['stellantis_servicebox']
    log(f"✅ Credentials geladen: {sb_creds['username']}")
    return sb_creds

def setup_driver():
    log("🔧 Initialisiere Chrome WebDriver...")
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=de-DE')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)
    log("✅ WebDriver bereit")
    return driver

def take_screenshot(driver, name):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{name}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    driver.save_screenshot(filepath)
    log(f"📸 Screenshot: {filename}")

def save_page_source(driver, name):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{name}.html"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    log(f"💾 HTML gespeichert: {filename}")

def login_and_switch_to_frame(driver, credentials):
    """Login via Basic Auth und wechsel zu frameHub"""
    log("\n🔐 LOGIN & FRAME-WECHSEL")
    log("="*80)
    
    username = credentials['username']
    password = credentials['password']
    base_url = credentials['portal_url']
    
    if '://' in base_url:
        protocol, rest = base_url.split('://', 1)
        auth_url = f"{protocol}://{username}:{password}@{rest}"
    else:
        auth_url = f"https://{username}:{password}@{base_url}"
    
    log(f"🌐 Öffne mit Basic Auth...")
    
    try:
        driver.get(auth_url)
        time.sleep(8)
        
        log("🔍 Suche Frames...")
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
        )
        log("✅ In frameHub gewechselt!")
        time.sleep(3)
        
        take_screenshot(driver, "01_inside_framehub")
        
        return True
        
    except Exception as e:
        log(f"❌ Fehler beim Login: {e}")
        return False

def navigate_to_warenkorb(driver):
    """Navigation zum Warenkorb via JavaScript"""
    log("\n📂 NAVIGATION ZUM WARENKORB")
    log("="*80)
    
    try:
        log("🔍 Suche 'LOKALE VERWALTUNG' für Hover...")
        
        lokale_verwaltung = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "LOKALE VERWALTUNG"))
        )
        log("✅ 'LOKALE VERWALTUNG' gefunden")
        
        log("🖱️  HOVER über 'LOKALE VERWALTUNG'...")
        actions = ActionChains(driver)
        actions.move_to_element(lokale_verwaltung).perform()
        time.sleep(2)
        
        take_screenshot(driver, "02_dropdown_menu_opened")
        
        # Statt zu klicken: JavaScript direkt ausführen!
        log("🔧 Führe JavaScript aus: goTo('/panier/')")
        driver.execute_script("goTo('/panier/')")
        time.sleep(5)
        
        take_screenshot(driver, "03_warenkorb_page")
        save_page_source(driver, "03_warenkorb_page")
        
        log("✅ Warenkorb-Seite geladen via JavaScript!")
        
        # Suche "IN DEN WARENKORB ÜBERTRAGEN"
        log("\n🔍 Suche 'IN DEN WARENKORB ÜBERTRAGEN'...")
        
        try:
            # Warte kurz
            time.sleep(2)
            
            # Suche nach dem Link
            historie_link = driver.find_element(By.LINK_TEXT, "IN DEN WARENKORB ÜBERTRAGEN")
            log("✅ 'IN DEN WARENKORB ÜBERTRAGEN' gefunden!")
            
            log("🖱️  Klicke Link...")
            historie_link.click()
            time.sleep(5)
            
            take_screenshot(driver, "04_bestellungen_page")
            save_page_source(driver, "04_bestellungen_page")
            
            log("✅ Bestellungen-Seite geladen!")
            
        except NoSuchElementException:
            log("ℹ️  'IN DEN WARENKORB ÜBERTRAGEN' nicht gefunden - evtl. bereits auf richtiger Seite")
        
        return True
        
    except Exception as e:
        log(f"❌ Fehler bei Navigation: {e}")
        take_screenshot(driver, "error_navigation")
        save_page_source(driver, "error_navigation")
        return False

def analyze_bestellungen_page(driver):
    """Analysiert die Bestellübersicht"""
    log("\n🔍 ANALYSE DER BESTELLSEITE")
    log("="*80)
    
    try:
        log("📊 Suche Bestellungs-Tabellen...")
        tables = driver.find_elements(By.TAG_NAME, "table")
        log(f"Gefundene Tabellen: {len(tables)}")
        
        for idx, table in enumerate(tables):
            log(f"\n📋 Tabelle {idx+1}:")
            try:
                headers = table.find_elements(By.TAG_NAME, "th")
                if headers:
                    header_texts = [h.text for h in headers if h.text]
                    if header_texts:
                        log(f"   Spalten: {', '.join(header_texts)}")
                
                rows = table.find_elements(By.TAG_NAME, "tr")
                log(f"   Zeilen: {len(rows)}")
                
                for row_idx, row in enumerate(rows[:5], 1):
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if cells:
                        cell_texts = [c.text[:50] for c in cells if c.text]
                        if cell_texts:
                            log(f"   Zeile {row_idx}: {' | '.join(cell_texts)}")
            except Exception as e:
                log(f"   Fehler: {e}")
        
        log("\n🔗 Suche Bestellungs-Links...")
        links = driver.find_elements(By.TAG_NAME, "a")
        
        bestellung_links = []
        for link in links:
            link_text = link.text.strip()
            link_href = link.get_attribute('href')
            if link_text and link_href:
                if any(x in link_text.upper() for x in ['JAG', '1AG', 'BESTELL']):
                    bestellung_links.append((link_text, link_href))
                    log(f"   📎 {link_text}")
        
        if bestellung_links:
            log(f"\n✅ {len(bestellung_links)} Bestellungs-Links gefunden!")
        else:
            log("ℹ️  Keine Bestellungs-Links gefunden")
        
        return True
        
    except Exception as e:
        log(f"❌ Fehler bei Analyse: {e}")
        return False

def main():
    log("\n" + "="*80)
    log("🚀 STELLANTIS SERVICE BOX SCRAPER - WITH JAVASCRIPT NAV")
    log("="*80)
    
    driver = None
    
    try:
        credentials = load_credentials()
        driver = setup_driver()
        
        if not login_and_switch_to_frame(driver, credentials):
            log("\n❌ Login fehlgeschlagen!")
            return False
        
        if not navigate_to_warenkorb(driver):
            log("\n❌ Navigation fehlgeschlagen!")
            return False
        
        if not analyze_bestellungen_page(driver):
            log("\n❌ Analyse fehlgeschlagen!")
            return False
        
        log("\n" + "="*80)
        log("✅ SCRAPER ERFOLGREICH!")
        log("="*80)
        
        return True
        
    except Exception as e:
        log(f"❌ Fehler: {e}")
        if driver:
            take_screenshot(driver, "error_unexpected")
        return False
        
    finally:
        if driver:
            log(f"\n📂 Screenshots: {SCREENSHOTS_DIR}")
            log("\n🔚 Schließe Browser...")
            driver.quit()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
