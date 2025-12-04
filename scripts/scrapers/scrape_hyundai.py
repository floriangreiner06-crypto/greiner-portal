#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyundai Finance - Bestandsliste CSV Scraper
============================================
Lädt die Bestandsliste inkl. Zinsbeginn als CSV herunter
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
LOG_DIR = os.path.join(BASE_DIR, "logs")

def load_credentials():
    """Lädt Hyundai Finance Credentials aus credentials.json"""
    with open(CREDENTIALS_FILE, 'r') as f:
        creds = json.load(f)
    
    hyundai = creds.get('external_systems', {}).get('hyundai_finance', {})
    
    if not hyundai:
        raise ValueError("Hyundai Finance Credentials nicht gefunden!")
    
    return hyundai

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
        # Ignoriere temporäre Downloads
        csv_files = [f for f in csv_files if not f.endswith('.crdownload')]
        if csv_files:
            # Neueste Datei
            newest = max(csv_files, key=os.path.getctime)
            time.sleep(2)  # Warten bis Download komplett
            return newest
        time.sleep(1)
    return None

def scrape_bestandsliste():
    """Hauptfunktion: Login, Navigation, CSV-Download"""
    
    print("\n" + "="*70)
    print("🚗 HYUNDAI FINANCE - BESTANDSLISTE SCRAPER")
    print("="*70)
    print(f"⏰ Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verzeichnisse erstellen
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Alte Downloads löschen
    for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
        os.remove(f)
    
    # Credentials laden
    print("\n📋 Lade Credentials...")
    creds = load_credentials()
    print(f"   Portal: {creds['dealer_portal_url']}")
    print(f"   User: {creds['username']}")
    print(f"   Standort: {creds['standort']}")
    
    driver = None
    csv_file = None
    
    try:
        # WebDriver starten
        print("\n🔧 Starte WebDriver...")
        driver = setup_driver(DOWNLOAD_DIR)
        wait = WebDriverWait(driver, 20)
        
        # === LOGIN ===
        print("\n🔐 SCHRITT 1: Login...")
        driver.get(creds['dealer_portal_url'])
        time.sleep(5)
        
        # Email eingeben
        email_field = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='email']")
        ))
        email_field.send_keys(creds['username'])
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        
        # Passwort eingeben
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
                (By.XPATH, f"//*[contains(text(), 'Auto Greiner')]")
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
            print(f"   ⚠️ Standort-Auswahl: {e}")
        
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
            ekf_url = creds['ekf_portal_url'] + creds['endpoints']['home']
            driver.get(ekf_url)
            time.sleep(5)
            print("   ✅ Direkt zu EKF navigiert")
        
        # === BESTANDSLISTE ===
        print("\n📋 SCHRITT 4: Bestandsliste laden...")
        stocklist_url = creds['ekf_portal_url'] + creds['endpoints']['stocklist']
        driver.get(stocklist_url)
        time.sleep(5)
        
        # Anzahl Fahrzeuge
        try:
            count_elem = driver.find_element(By.XPATH, "//*[contains(text(), 'von')]")
            count_text = count_elem.text
            print(f"   📊 {count_text}")
        except:
            pass
        
        driver.save_screenshot(os.path.join(DOWNLOAD_DIR, "01_bestandsliste.png"))
        
        # === CSV DOWNLOAD ===
        print("\n📥 SCHRITT 5: CSV herunterladen...")
        
        # Download-Button finden (mat-icon mit download_file)
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
            
            # Kopieren nach Output-Dir mit Timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest_file = os.path.join(OUTPUT_DIR, f"hyundai_bestandsliste_{timestamp}.csv")
            shutil.copy(csv_file, dest_file)
            print(f"   💾 Gespeichert: {dest_file}")
            
            # Auch als "latest" speichern
            latest_file = os.path.join(OUTPUT_DIR, "hyundai_bestandsliste_latest.csv")
            shutil.copy(csv_file, latest_file)
            print(f"   💾 Latest: {latest_file}")
            
            # CSV analysieren
            print("\n📊 CSV-Analyse:")
            with open(csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    # Header
                    header = lines[0].strip()
                    delimiter = ';' if ';' in header else ','
                    columns = header.split(delimiter)
                    print(f"   Spalten ({len(columns)}): {columns[:8]}...")
                    print(f"   Zeilen: {len(lines) - 1} Fahrzeuge")
                    
                    # Wichtige Spalten suchen
                    important = ['VIN', 'Zinsbeginn', 'Saldo', 'Finanzierungsbeginn', 'Finanzierungsende']
                    found = [c for c in columns if any(i.lower() in c.lower() for i in important)]
                    print(f"   Wichtige Spalten: {found}")
            
            return dest_file
        else:
            print("   ❌ CSV-Download fehlgeschlagen!")
            driver.save_screenshot(os.path.join(DOWNLOAD_DIR, "error_no_csv.png"))
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
    print("\n" + "="*70)
    print("🚀 HYUNDAI BESTANDSLISTE SCRAPER - START")
    print("="*70)
    
    result = scrape_bestandsliste()
    
    print("\n" + "="*70)
    if result:
        print(f"✅ ERFOLG!")
        print(f"📁 CSV: {result}")
    else:
        print("❌ FEHLGESCHLAGEN")
    print("="*70)
    
    sys.exit(0 if result else 1)
