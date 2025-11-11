#!/usr/bin/env python3
"""Vereinfachter Test: Klicke alle mat-icon-buttons"""

import os
import time
import glob
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

PORTAL_URL = "https://fiona.hyundaifinance.eu/#/dealer-portal"
USERNAME = "Christian.aichinger@auto-greiner.de"
PASSWORD = "Hyundaikona2020!"
SCREENSHOTS_DIR = "/tmp/hyundai_screenshots"

chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

prefs = {
    'download.default_directory': SCREENSHOTS_DIR,
    'download.prompt_for_download': False,
    'download.directory_upgrade': True,
}
chrome_options.add_experimental_option('prefs', prefs)

driver = webdriver.Chrome(options=chrome_options)

try:
    print("🔐 Login...")
    driver.get(PORTAL_URL)
    time.sleep(5)
    
    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(USERNAME)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(5)
    
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(10)
    
    print("🏢 Standort...")
    driver.find_element(By.XPATH, "//div[contains(text(), 'Auto Greiner')]").click()
    time.sleep(3)
    driver.find_element(By.XPATH, "//button[contains(., 'Standort auswählen')]").click()
    time.sleep(10)
    
    print("🔄 EKF Portal...")
    driver.find_element(By.XPATH, "//div[contains(., 'Einkaufsfinanzierung')]").click()
    time.sleep(10)
    
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
    
    print("📋 Bestandsliste...")
    driver.get("https://ekf.hyundaifinance.eu/account/stocklist/search")
    time.sleep(10)
    
    # HIER DER TRICK: Finde ALLE mat-icon-buttons
    print("\n🔍 Suche alle mat-icon-buttons...")
    icon_buttons = driver.find_elements(By.CSS_SELECTOR, "button.mat-icon-button")
    print(f"   Gefunden: {len(icon_buttons)} Buttons")
    
    # Speichere CSV-Dateien VOR Klick
    initial_csvs = set(glob.glob(os.path.join(SCREENSHOTS_DIR, "*.csv")))
    
    # Klicke jeden Button und prüfe auf CSV
    for i, btn in enumerate(icon_buttons, 1):
        try:
            print(f"\n   Button {i}:")
            
            # Hole mat-icon Text
            icon = btn.find_element(By.TAG_NAME, "mat-icon")
            icon_text = icon.text
            print(f"     Icon: {icon_text}")
            
            if icon_text == "download_file":
                print(f"     ✓ DOWNLOAD-BUTTON GEFUNDEN!")
                btn.click()
                print(f"     ✓ Geklickt!")
                time.sleep(3)
                
                driver.save_screenshot(f"{SCREENSHOTS_DIR}/after_click_{i}.png")
                
                # Prüfe auf Popup
                try:
                    popup_btn = driver.find_element(By.XPATH, "//button[contains(., 'Download')]")
                    print(f"     ✓ Popup-Button gefunden - klicke...")
                    popup_btn.click()
                    time.sleep(3)
                except:
                    print(f"     ℹ️  Kein Popup")
                
                # Prüfe auf neue CSV
                time.sleep(5)
                current_csvs = set(glob.glob(os.path.join(SCREENSHOTS_DIR, "*.csv")))
                new_csvs = current_csvs - initial_csvs
                
                if new_csvs:
                    print(f"\n✅ CSV HERUNTERGELADEN!")
                    for csv in new_csvs:
                        print(f"   → {os.path.basename(csv)}")
                    break
                else:
                    print(f"     ⚠️  Noch keine CSV...")
                
        except Exception as e:
            print(f"     ⚠️  Fehler: {e}")
            continue
    
    # Finale Prüfung
    print("\n📊 Finale CSV-Prüfung...")
    all_csvs = glob.glob(os.path.join(SCREENSHOTS_DIR, "*.csv"))
    if all_csvs:
        print(f"✅ {len(all_csvs)} CSV-Dateien gefunden:")
        for csv in all_csvs:
            print(f"   → {os.path.basename(csv)}")
    else:
        print("❌ Keine CSV-Dateien gefunden")
    
finally:
    driver.quit()
