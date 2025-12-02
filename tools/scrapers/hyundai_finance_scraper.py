#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyundai Finance Scraper V5.1 - FIX: Download-Button mit mat-icon-button
"""

import os
import sys
import time
import json
import csv
import glob
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

# Konfiguration
PORTAL_URL = "https://fiona.hyundaifinance.eu/#/dealer-portal"
USERNAME = "Christian.aichinger@auto-greiner.de"
PASSWORD = "Hyundaikona2020!"
STANDORT_NAME = "Auto Greiner"
BASE_DIR = "/opt/greiner-portal"
SCREENSHOTS_DIR = "/tmp/hyundai_screenshots"

WAIT_SHORT = 5
WAIT_MEDIUM = 10
WAIT_LONG = 30
WAIT_DOWNLOAD = 20

def setup_driver():
    print("🔧 Initialisiere WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=de-DE')
    
    prefs = {
        'download.default_directory': SCREENSHOTS_DIR,
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'safebrowsing.enabled': False
    }
    chrome_options.add_experimental_option('prefs', prefs)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)
    print("✅ WebDriver bereit")
    return driver

def take_screenshot(driver, name):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{name}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    driver.save_screenshot(filepath)
    print(f"   📸 {filename}")

def wait_for_csv_download(timeout=WAIT_DOWNLOAD):
    print(f"   ⏳ Warte auf CSV-Download (max {timeout}s)...")
    start_time = time.time()
    initial_files = set(glob.glob(os.path.join(SCREENSHOTS_DIR, "*.csv")))
    
    while time.time() - start_time < timeout:
        current_files = set(glob.glob(os.path.join(SCREENSHOTS_DIR, "*.csv")))
        new_files = current_files - initial_files
        
        if new_files:
            csv_file = list(new_files)[0]
            time.sleep(2)
            print(f"   ✅ CSV heruntergeladen: {os.path.basename(csv_file)}")
            return csv_file
        time.sleep(1)
    
    return None

def parse_csv_file(csv_file):
    print(f"\n📊 Parse CSV-Datei: {os.path.basename(csv_file)}")
    vehicles = []
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                sample = f.read(1024)
                f.seek(0)
                delimiter = ';' if sample.count(';') > sample.count(',') else ','
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for row in reader:
                    vin = None
                    for key, value in row.items():
                        if value and len(str(value)) == 17 and str(value).isalnum():
                            vin = str(value).upper()
                            break
                    
                    if vin:
                        vehicles.append({'vin': vin, 'raw_data': dict(row)})
                
                print(f"   ✅ {len(vehicles)} Fahrzeuge gefunden")
                print(f"   ℹ️  Encoding: {encoding}, Delimiter: '{delimiter}'")
                
                if vehicles:
                    print(f"\n   📋 Erste VINs:")
                    for i, v in enumerate(vehicles[:3], 1):
                        print(f"      {i}. {v['vin']}")
                
                return vehicles
        except:
            continue
    
    return []

def scrape_hyundai_finance():
    print("\n" + "="*60)
    print("🚗 HYUNDAI FINANCE SCRAPER V5.1")
    print("="*60)
    
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    driver = None
    
    try:
        driver = setup_driver()
        wait = WebDriverWait(driver, WAIT_MEDIUM)
        
        # LOGIN
        print("\n🔐 Login...")
        driver.get(PORTAL_URL)
        time.sleep(WAIT_SHORT)
        
        driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(USERNAME)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(WAIT_SHORT)
        
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(WAIT_MEDIUM)
        
        take_screenshot(driver, "01_nach_login")
        print("✅ Login erfolgreich")
        
        # STANDORT
        print("\n🏢 Standort auswählen...")
        standort_card = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[contains(text(), '{STANDORT_NAME}')]")))
        standort_card.click()
        time.sleep(WAIT_SHORT)
        
        select_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Standort auswählen')]")))
        select_button.click()
        time.sleep(WAIT_MEDIUM)
        
        take_screenshot(driver, "02_standort_gewählt")
        print("✅ Standort ausgewählt")
        
        # EKF PORTAL
        print("\n🔄 Wechsel zu EKF Portal...")
        ekf_tile = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(., 'Einkaufsfinanzierung')]")))
        ekf_tile.click()
        time.sleep(WAIT_MEDIUM)
        
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(WAIT_SHORT)
        
        take_screenshot(driver, "03_ekf_portal")
        print("✅ EKF Portal geöffnet")
        
        # BESTANDSLISTE
        print("\n📋 Navigation zur BESTANDSLISTE...")
        driver.get("https://ekf.hyundaifinance.eu/account/stocklist/search")
        time.sleep(WAIT_MEDIUM)
        
        take_screenshot(driver, "04_bestandsliste")
        print("✅ Bestandsliste geladen")
        
        # CSV DOWNLOAD - NEUE STRATEGIE
        print("\n📥 Download Bestandsliste CSV...")
        print("   → Suche Download-Button (mat-icon-button mit download_file)...")
        
        # STRATEGIE: Finde button mit mat-icon-button class der download_file enthält
        download_button = wait.until(
            EC.element_to_be_clickable((
                By.XPATH, 
                "//button[contains(@class, 'mat-icon-button')]//mat-icon[text()='download_file']/.."
            ))
        )
        
        print("   ✓ Download-Button gefunden!")
        download_button.click()
        print("   ✓ Download-Button geklickt")
        
        time.sleep(WAIT_SHORT)
        take_screenshot(driver, "05_download_geklickt")
        
        # POPUP-HANDLING
        print("\n💬 Popup-Dialog für Download...")
        try:
            popup = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'CSV-Datei')]")))
            print("   ✓ Popup erschienen")
            time.sleep(2)
            take_screenshot(driver, "06_popup_erschienen")
            
            popup_download_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Download')]")))
            popup_download_button.click()
            print("   ✓ Download-Button im Popup geklickt")
            
            time.sleep(2)
            take_screenshot(driver, "07_popup_download_geklickt")
            
        except TimeoutException:
            print("   ℹ️  Kein Popup - direkter Download")
        
        # WARTE AUF CSV
        csv_file = wait_for_csv_download(timeout=WAIT_DOWNLOAD)
        
        if not csv_file:
            existing_csvs = glob.glob(os.path.join(SCREENSHOTS_DIR, "*.csv"))
            if existing_csvs:
                csv_file = max(existing_csvs, key=os.path.getctime)
                print(f"\n   → Verwende neueste CSV: {os.path.basename(csv_file)}")
        
        # CSV PARSEN
        if csv_file and os.path.exists(csv_file):
            vehicles = parse_csv_file(csv_file)
            
            if vehicles:
                print(f"\n✅ CSV ERFOLGREICH GEPARST!")
                print(f"   📊 {len(vehicles)} Fahrzeuge gefunden")
                
                json_file = csv_file.replace('.csv', '_parsed.json')
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(vehicles, f, indent=2, ensure_ascii=False)
                print(f"   💾 JSON gespeichert: {os.path.basename(json_file)}")
                
                return vehicles
            else:
                print("\n⚠️  Keine Fahrzeuge in CSV gefunden")
                return []
        else:
            print("\n❌ CSV-Datei nicht gefunden!")
            return []
        
    except Exception as e:
        print(f"\n❌ FEHLER: {str(e)}")
        if driver:
            take_screenshot(driver, "99_error")
        import traceback
        traceback.print_exc()
        return []
        
    finally:
        if driver:
            driver.quit()
            print("\n🔚 Browser geschlossen")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 HYUNDAI FINANCE SCRAPER V5.1 - START")
    print("="*60)
    print(f"⏰ Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Screenshots: {SCREENSHOTS_DIR}")
    print("="*60)
    
    vehicles = scrape_hyundai_finance()
    
    print("\n" + "="*60)
    if vehicles:
        print(f"✅ SCRAPING ERFOLGREICH!")
        print(f"📊 {len(vehicles)} Fahrzeuge gefunden")
    else:
        print("⚠️  KEINE FAHRZEUGE GEFUNDEN")
    print("="*60)
    
    sys.exit(0 if vehicles else 1)
