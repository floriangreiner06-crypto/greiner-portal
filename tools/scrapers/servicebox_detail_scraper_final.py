#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Service Box Detail-Scraper - FINAL V2
Mit korrektem Pattern für Teilenummern MIT Zusatztext
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
SCREENSHOTS_DIR = f"{BASE_DIR}/logs/servicebox_detail_screenshots"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_detail_scraper_final.log"
OUTPUT_FILE = f"{BASE_DIR}/logs/servicebox_bestellungen_details_final.json"

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
    log("\n🔐 LOGIN & NAVIGATION")
    log("="*80)

    username = credentials['username']
    password = credentials['password']
    base_url = credentials['portal_url']
    protocol, rest = base_url.split('://', 1)
    auth_url = f"{protocol}://{username}:{password}@{rest}"

    try:
        driver.get(auth_url)
        time.sleep(8)
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
        )
        log("✅ In frameHub gewechselt")
        time.sleep(3)

        lokale = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "LOKALE VERWALTUNG"))
        )
        ActionChains(driver).move_to_element(lokale).perform()
        time.sleep(2)

        driver.execute_script("goTo('/panier/')")
        time.sleep(5)
        log("✅ Warenkorb geladen")

        historie_link = driver.find_element(By.LINK_TEXT, "Historie der Bestellungen")
        historie_link.click()
        time.sleep(5)

        log("✅ Historie-Seite geladen")
        take_screenshot(driver, "historie_loaded")
        return True

    except Exception as e:
        log(f"❌ Fehler: {e}")
        take_screenshot(driver, "error_navigation")
        return False

def extract_bestellungen_from_current_page(driver):
    log("\n📋 EXTRAHIERE BESTELLNUMMERN VON AKTUELLER SEITE")
    log("-"*80)
    
    try:
        links = driver.find_elements(By.XPATH, "//a[contains(@href, 'commandeDetailRepAll.do')]")
        bestellungen_mit_urls = []
        
        for link in links:
            text = link.text.strip()
            if text and text.startswith('1JA') and len(text) == 9:
                href = link.get_attribute('href')
                bestellungen_mit_urls.append({'nummer': text, 'url': href})
                log(f"   ✅ {text}")
        
        seen = set()
        unique = []
        for item in bestellungen_mit_urls:
            if item['nummer'] not in seen:
                seen.add(item['nummer'])
                unique.append(item)
        
        log(f"\n📊 {len(unique)} eindeutige Bestellungen gefunden")
        return unique
        
    except Exception as e:
        log(f"❌ Fehler beim Extrahieren: {e}")
        return []

def safe_get_text(element):
    try:
        return element.text.strip() if element else ""
    except:
        return ""

def extract_bestellung_details(driver, bestellung_info):
    bestellnummer = bestellung_info['nummer']
    detail_url = bestellung_info['url']
    
    log(f"\n   🔍 Extrahiere Details für {bestellnummer}")
    
    details = {
        'bestellnummer': bestellnummer,
        'url': detail_url,
        'absender': {},
        'empfaenger': {},
        'historie': {},
        'positionen': [],
        'summen': {},
        'kommentare': {}
    }

    try:
        log(f"      🔗 Navigiere zu Detail-Seite...")
        driver.get(detail_url)
        time.sleep(5)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        take_screenshot(driver, f"detail_{bestellnummer}")
        
        # Absender extrahieren
        try:
            page_text = driver.page_source
            
            absender_code_match = re.search(r'Code Vertragspartner\s*:\s*</td>\s*<td[^>]*>\s*([A-Z0-9]+)', page_text)
            if absender_code_match:
                details['absender']['code'] = absender_code_match.group(1)
            
            absender_name_match = re.search(r'Name\s*:\s*</td>\s*<td[^>]*>\s*([^<]+)', page_text)
            if absender_name_match:
                details['absender']['name'] = absender_name_match.group(1).strip()
                
            log(f"      ✅ Absender: {details['absender'].get('code', 'N/A')}")
        except Exception as e:
            log(f"      ⚠️  Absender: {e}")
        
        # Empfänger extrahieren
        try:
            empf_section = re.search(r'Empfänger.*?Code Vertragspartner\s*:\s*</td>\s*<td[^>]*>\s*([A-Z0-9]+)', page_text, re.DOTALL)
            if empf_section:
                details['empfaenger']['code'] = empf_section.group(1)
            log(f"      ✅ Empfänger: {details['empfaenger'].get('code', 'N/A')}")
        except Exception as e:
            log(f"      ⚠️  Empfänger: {e}")
        
        # Bestelldatum
        try:
            datum_match = re.search(r'Bestelldatum\s*:\s*</td>\s*<td[^>]*>\s*(\d{2}\.\d{2}\.\d{2},\s*\d{2}:\d{2})', page_text)
            if datum_match:
                details['historie']['bestelldatum'] = datum_match.group(1)
                log(f"      ✅ Bestelldatum: {datum_match.group(1)}")
        except Exception as e:
            log(f"      ⚠️  Datum: {e}")
        
        # Positionen extrahieren - KORRIGIERT MIT REGEX!
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cols) >= 6:
                        first_col = safe_get_text(cols[0])
                        
                        # KORRIGIERT: Extrahiere Teilenummer auch wenn Zusatztext vorhanden
                        teilenummer_match = re.search(r'^\s*([A-Z0-9]{6,15})', first_col)
                        if teilenummer_match:
                            teilenummer = teilenummer_match.group(1)
                            
                            position = {
                                'teilenummer': teilenummer,
                                'beschreibung': safe_get_text(cols[1]),
                                'menge': safe_get_text(cols[2]),
                                'menge_in_lieferung': safe_get_text(cols[3]),
                                'menge_in_bestellung': safe_get_text(cols[4]),
                                'preis_ohne_mwst': safe_get_text(cols[5]),
                                'preis_mit_mwst': safe_get_text(cols[6]) if len(cols) > 6 else "",
                                'summe_inkl_mwst': safe_get_text(cols[7]) if len(cols) > 7 else ""
                            }
                            details['positionen'].append(position)
            
            log(f"      ✅ {len(details['positionen'])} Positionen extrahiert")
            
        except Exception as e:
            log(f"      ⚠️  Positionen: {e}")
        
        # Summen extrahieren
        try:
            summe_zzgl_match = re.search(r'Summe zzgl\. MwSt\s*:\s*</td>\s*<td[^>]*>\s*([\d,]+)\s*EUR', page_text)
            if summe_zzgl_match:
                details['summen']['zzgl_mwst'] = summe_zzgl_match.group(1)
            
            summe_inkl_match = re.search(r'Summe inkl\. MwSt\s*:\s*</td>\s*<td[^>]*>\s*([\d,]+)\s*EUR', page_text)
            if summe_inkl_match:
                details['summen']['inkl_mwst'] = summe_inkl_match.group(1)
                
            if details['summen']:
                log(f"      ✅ Summen extrahiert: {details['summen'].get('inkl_mwst', 'N/A')} EUR")
        except Exception as e:
            log(f"      ⚠️  Summen: {e}")
        
        # Kommentare
        try:
            kommentar_match = re.search(r'Lokale Bestell-Nr\.\s*:\s*</td>\s*<td[^>]*>\s*([^<]+)', page_text)
            if kommentar_match:
                details['kommentare']['lokale_nr'] = kommentar_match.group(1).strip()
                log(f"      ✅ Lokale Nr: {details['kommentare']['lokale_nr']}")
        except Exception as e:
            log(f"      ⚠️  Kommentare: {e}")
        
        return details

    except Exception as e:
        log(f"      ❌ Fehler bei {bestellnummer}: {e}")
        take_screenshot(driver, f"error_{bestellnummer}")
        return details

def scrape_all_details(driver, bestellungen, max_orders=None):
    log("\n📋 SCRAPE ALLE BESTELLUNGS-DETAILS")
    log("="*80)
    
    if max_orders:
        bestellungen = bestellungen[:max_orders]
        log(f"⚠️  TEST-MODUS: Nur erste {max_orders} Bestellungen")
    
    all_details = []
    total = len(bestellungen)
    
    for idx, bestellung_info in enumerate(bestellungen, 1):
        log(f"\n[{idx}/{total}] {bestellung_info['nummer']}")
        log("-" * 40)
        
        details = extract_bestellung_details(driver, bestellung_info)
        all_details.append(details)
        
        progress = (idx / total) * 100
        log(f"   📊 Progress: {progress:.1f}%")
        time.sleep(2)
    
    return all_details

def save_results(details):
    log(f"\n💾 SPEICHERE DETAIL-ERGEBNISSE")
    log("="*80)

    data = {
        'timestamp': datetime.now().isoformat(),
        'anzahl_bestellungen': len(details),
        'bestellungen': details
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    log(f"✅ Gespeichert: {OUTPUT_FILE}")
    
    total_positionen = sum(len(d['positionen']) for d in details)
    bestellungen_mit_positionen = sum(1 for d in details if len(d['positionen']) > 0)
    
    log(f"📊 Statistik:")
    log(f"   - Bestellungen gesamt: {len(details)}")
    log(f"   - Bestellungen mit Positionen: {bestellungen_mit_positionen}")
    log(f"   - Positionen gesamt: {total_positionen}")
    if len(details) > 0:
        log(f"   - Ø Positionen/Bestellung: {total_positionen/len(details):.1f}")

def main():
    log("\n" + "="*80)
    log("🚀 STELLANTIS SERVICE BOX - DETAIL SCRAPER FINAL V2")
    log("="*80)

    driver = None
    TEST_MODE = True
    MAX_ORDERS = 5 if TEST_MODE else None

    try:
        credentials = load_credentials()
        driver = setup_driver()

        if not login_and_navigate(driver, credentials):
            log("\n❌ Login/Navigation fehlgeschlagen!")
            return False

        bestellungen = extract_bestellungen_from_current_page(driver)
        
        if not bestellungen:
            log("❌ Keine Bestellnummern gefunden!")
            return False
        
        if TEST_MODE:
            log(f"\n⚠️  TEST-MODUS: Nur erste {MAX_ORDERS} Bestellungen")

        details = scrape_all_details(driver, bestellungen, MAX_ORDERS)

        if details:
            save_results(details)
            log("\n" + "="*80)
            log("✅ DETAIL-SCRAPER ERFOLGREICH!")
            log("="*80)
        else:
            log("\n⚠️  Keine Details extrahiert!")

        return True

    except Exception as e:
        log(f"\n❌ Fehler: {e}")
        import traceback
        log(traceback.format_exc())
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
