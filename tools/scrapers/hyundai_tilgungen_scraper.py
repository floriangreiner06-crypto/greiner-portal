#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyundai Finance - Tilgungen CSV Scraper
=======================================
Lädt die Tilgungsliste als CSV herunter
Credentials aus config/credentials.json
"""

import os
import sys
import time
import json
import glob
import shutil
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Pfade
BASE_DIR = "/opt/greiner-portal"
CREDENTIALS_FILE = os.path.join(BASE_DIR, "config/credentials.json")
DOWNLOAD_DIR = "/tmp/hyundai_download"
OUTPUT_DIR = os.path.join(BASE_DIR, "data/hyundai")

def load_credentials():
    """Lädt Hyundai Finance Credentials aus credentials.json"""
    with open(CREDENTIALS_FILE, 'r') as f:
        creds = json.load(f)
    return creds.get('external_systems', {}).get('hyundai_finance', {})

def setup_driver(download_dir):
    """WebDriver mit Download-Einstellungen"""
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--lang=de-DE')
    
    prefs = {
        'download.default_directory': download_dir,
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'safebrowsing.enabled': False
    }
    opts.add_experimental_option('prefs', prefs)
    
    driver = webdriver.Chrome(options=opts)
    driver.implicitly_wait(3)
    return driver

def wait_for_csv(download_dir, timeout=30):
    """Wartet auf CSV-Download"""
    start = time.time()
    while time.time() - start < timeout:
        csv_files = glob.glob(os.path.join(download_dir, "*.csv"))
        csv_files = [f for f in csv_files if not f.endswith('.crdownload')]
        if csv_files:
            newest = max(csv_files, key=os.path.getctime)
            time.sleep(2)
            return newest
        time.sleep(1)
    return None

def scrape_tilgungen():
    """Hauptfunktion: Login, Navigation, CSV-Download"""
    
    print("\n" + "="*70)
    print("💶 HYUNDAI FINANCE - TILGUNGEN SCRAPER")
    print("="*70)
    print(f"⏰ Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Alte Downloads löschen
    for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
        os.remove(f)
    
    # Credentials laden
    print("\n📋 Lade Credentials...")
    creds = load_credentials()
    print(f"   User: {creds['username']}")
    
    driver = None
    
    try:
        print("\n🔧 Starte WebDriver...")
        driver = setup_driver(DOWNLOAD_DIR)
        wait = WebDriverWait(driver, 20)
        
        # === LOGIN ===
        print("\n🔐 SCHRITT 1: Login...")
        driver.get(creds['dealer_portal_url'])
        time.sleep(5)
        
        email_field = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='email']")
        ))
        email_field.send_keys(creds['username'])
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        
        pwd_field = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='password']")
        ))
        pwd_field.send_keys(creds['password'])
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(5)
        print("   ✅ Login erfolgreich")
        
        # === STANDORT ===
        print("\n🏢 SCHRITT 2: Standort auswählen...")
        try:
            standort = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'Auto Greiner')]")
            ))
            standort.click()
            time.sleep(2)
            
            btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Standort')]")
            ))
            btn.click()
            time.sleep(5)
            print("   ✅ Standort ausgewählt")
        except Exception as e:
            print(f"   ⚠️ Standort: {e}")
        
        # === EKF PORTAL ===
        print("\n💰 SCHRITT 3: EKF Portal öffnen...")
        try:
            ekf = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'Einkaufsfinanzierung')]")
            ))
            ekf.click()
            time.sleep(5)
            
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(3)
            print("   ✅ EKF Portal geöffnet")
        except:
            driver.get(creds['ekf_portal_url'] + creds['endpoints']['home'])
            time.sleep(5)
            print("   ✅ Direkt zu EKF navigiert")
        
        # === TILGUNGEN ===
        print("\n📋 SCHRITT 4: Tilgungen laden...")
        tilgungen_url = creds['ekf_portal_url'] + creds['endpoints']['installment']
        driver.get(tilgungen_url)
        time.sleep(5)
        
        # Anzahl Tilgungen
        try:
            count_elem = driver.find_element(By.XPATH, "//*[contains(text(), 'von')]")
            count_text = count_elem.text
            print(f"   📊 {count_text}")
        except:
            pass
        
        driver.save_screenshot(os.path.join(DOWNLOAD_DIR, "01_tilgungen.png"))
        
        # === CSV DOWNLOAD ===
        print("\n📥 SCHRITT 5: CSV herunterladen...")
        
        download_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, 
            "//button[.//mat-icon[text()='download_file']]"
        )))
        print("   ✅ Download-Button gefunden")
        
        download_btn.click()
        print("   ⏳ Download gestartet...")
        time.sleep(2)
        
        driver.save_screenshot(os.path.join(DOWNLOAD_DIR, "02_nach_click.png"))
        
        # Auf CSV warten
        csv_file = wait_for_csv(DOWNLOAD_DIR, timeout=30)
        
        if csv_file:
            file_size = os.path.getsize(csv_file)
            print(f"   ✅ CSV heruntergeladen: {os.path.basename(csv_file)}")
            print(f"   📁 Größe: {file_size:,} Bytes")
            
            # Kopieren nach Output-Dir
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest_file = os.path.join(OUTPUT_DIR, f"hyundai_tilgungen_{timestamp}.csv")
            shutil.copy(csv_file, dest_file)
            print(f"   💾 Gespeichert: {dest_file}")
            
            # Auch als "latest"
            latest_file = os.path.join(OUTPUT_DIR, "hyundai_tilgungen_latest.csv")
            shutil.copy(csv_file, latest_file)
            print(f"   💾 Latest: {latest_file}")
            
            # CSV analysieren
            print("\n📊 CSV-Analyse:")
            with open(csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    header = lines[0].strip()
                    delimiter = ';' if ';' in header else ','
                    columns = header.split(delimiter)
                    print(f"   Spalten ({len(columns)}): {columns[:6]}...")
                    print(f"   Zeilen: {len(lines) - 1} Tilgungen")
            
            return dest_file
        else:
            print("   ❌ CSV-Download fehlgeschlagen!")
            return None
            
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        if driver:
            driver.save_screenshot(os.path.join(DOWNLOAD_DIR, "error.png"))
        return None
        
    finally:
        if driver:
            driver.quit()
            print("\n🔚 Browser geschlossen")

if __name__ == "__main__":
    result = scrape_tilgungen()
    
    print("\n" + "="*70)
    if result:
        print(f"✅ ERFOLG!")
        print(f"📁 CSV: {result}")
    else:
        print("❌ FEHLGESCHLAGEN")
    print("="*70)
    
    sys.exit(0 if result else 1)
