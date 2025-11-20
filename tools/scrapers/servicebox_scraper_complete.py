#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Service Box Scraper - COMPLETE mit korrekten Pagination-Buttons
"""

import os
import sys
import time
import json
import re
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
OUTPUT_FILE = f"{BASE_DIR}/logs/servicebox_bestellungen.json"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def load_credentials():
    with open(CREDENTIALS_PATH, 'r') as f:
        creds = json.load(f)
    return creds['external_systems']['stellantis_servicebox']

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

def login_and_navigate(driver, credentials):
    """Login und Navigation zur Historie-Seite"""
    log("\n🔐 LOGIN & NAVIGATION")
    log("="*80)
    
    username = credentials['username']
    password = credentials['password']
    base_url = credentials['portal_url']
    
    if '://' in base_url:
        protocol, rest = base_url.split('://', 1)
        auth_url = f"{protocol}://{username}:{password}@{rest}"
    else:
        auth_url = f"https://{username}:{password}@{base_url}"
    
    try:
        driver.get(auth_url)
        time.sleep(8)
        
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
        )
        log("✅ In frameHub gewechselt")
        time.sleep(3)
        
        # Hover + JavaScript Navigation
        lokale = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "LOKALE VERWALTUNG"))
        )
        ActionChains(driver).move_to_element(lokale).perform()
        time.sleep(2)
        
        driver.execute_script("goTo('/panier/')")
        time.sleep(5)
        log("✅ Warenkorb geladen")
        
        # Klick auf "Historie der Bestellungen"
        historie_link = driver.find_element(By.LINK_TEXT, "Historie der Bestellungen")
        historie_link.click()
        time.sleep(5)
        
        log("✅ Historie-Seite geladen")
        return True
        
    except Exception as e:
        log(f"❌ Fehler: {e}")
        take_screenshot(driver, "error_navigation")
        return False

def extract_bestellungen_from_page(driver):
    """Extrahiert Bestellnummern von aktueller Seite"""
    html = driver.page_source
    pattern = r'1[A-Z]{3}[A-Z0-9]{5}'
    bestellungen = re.findall(pattern, html)
    return list(set(bestellungen))

def scrape_all_pages(driver):
    """Iteriert durch alle Pagination-Seiten"""
    log("\n📄 SCRAPE ALLE SEITEN")
    log("="*80)
    
    all_bestellungen = []
    page_num = 1
    
    while page_num <= 10:  # Max 10 Seiten als Safety
        log(f"\n📄 Seite {page_num}")
        log("-" * 40)
        
        time.sleep(2)  # Kurz warten damit Seite geladen ist
        take_screenshot(driver, f"page_{page_num}")
        
        # Extrahiere Bestellungen
        bestellungen = extract_bestellungen_from_page(driver)
        log(f"   Gefunden: {len(bestellungen)} Bestellungen")
        
        for b in bestellungen:
            if b not in all_bestellungen:
                all_bestellungen.append(b)
                log(f"   ✅ {b}")
        
        # Suche "Weiter"-Button (bt-arrow-right)
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "input.bt-arrow-right")
            
            # Prüfe ob inactive (disabled)
            classes = next_button.get_attribute('class') or ''
            if 'inactive' in classes:
                log("   ℹ️  'Weiter'-Button inactive - letzte Seite erreicht")
                break
            
            log("   🖱️  Klicke 'Weiter' (bt-arrow-right)...")
            next_button.click()
            time.sleep(3)
            page_num += 1
            
        except NoSuchElementException:
            log("   ℹ️  'Weiter'-Button nicht gefunden - letzte Seite")
            break
        except Exception as e:
            log(f"   ℹ️  Fehler bei Navigation: {e}")
            break
    
    log(f"\n📊 GESAMT: {len(all_bestellungen)} Bestellungen auf {page_num} Seiten")
    return sorted(all_bestellungen)

def save_results(bestellungen):
    """Speichert Ergebnisse als JSON"""
    log(f"\n💾 SPEICHERE ERGEBNISSE")
    log("="*80)
    
    data = {
        'timestamp': datetime.now().isoformat(),
        'anzahl_bestellungen': len(bestellungen),
        'bestellungen': [
            {'nummer': b, 'status': 'unbekannt'}
            for b in bestellungen
        ]
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    log(f"✅ Gespeichert: {OUTPUT_FILE}")

def main():
    log("\n" + "="*80)
    log("🚀 STELLANTIS SERVICE BOX - COMPLETE SCRAPER V3")
    log("="*80)
    
    driver = None
    
    try:
        credentials = load_credentials()
        driver = setup_driver()
        
        if not login_and_navigate(driver, credentials):
            log("\n❌ Login/Navigation fehlgeschlagen!")
            return False
        
        bestellungen = scrape_all_pages(driver)
        
        if bestellungen:
            save_results(bestellungen)
            
            log("\n" + "="*80)
            log("✅ SCRAPER ERFOLGREICH!")
            log("="*80)
            log(f"\n📋 BESTELLUNGEN ({len(bestellungen)}):")
            for idx, b in enumerate(bestellungen, 1):
                log(f"  {idx:2}. {b}")
        else:
            log("\n⚠️  Keine Bestellungen gefunden!")
        
        return True
        
    except Exception as e:
        log(f"\n❌ Fehler: {e}")
        if driver:
            take_screenshot(driver, "error_unexpected")
        return False
        
    finally:
        if driver:
            log(f"\n📂 Ergebnisse: {OUTPUT_FILE}")
            log(f"📂 Screenshots: {SCREENSHOTS_DIR}")
            log("\n🔚 Schließe Browser...")
            driver.quit()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
