#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug-Script: Historie-Seite HTML analysieren
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
from selenium.webdriver.chrome.options import Options

BASE_DIR = "/opt/greiner-portal"
CREDENTIALS_PATH = f"{BASE_DIR}/config/credentials.json"

def load_credentials():
    with open(CREDENTIALS_PATH, 'r') as f:
        creds = json.load(f)
    return creds['external_systems']['stellantis_servicebox']

def setup_driver():
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver

def main():
    print("🔍 ANALYSIERE HISTORIE-SEITE")
    print("="*80)
    
    credentials = load_credentials()
    driver = setup_driver()
    
    try:
        # Login
        username = credentials['username']
        password = credentials['password']
        base_url = credentials['portal_url']
        
        protocol, rest = base_url.split('://', 1)
        auth_url = f"{protocol}://{username}:{password}@{rest}"
        
        driver.get(auth_url)
        time.sleep(8)
        
        # Frame wechseln
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
        )
        time.sleep(3)
        
        # Navigation
        lokale = driver.find_element(By.LINK_TEXT, "LOKALE VERWALTUNG")
        ActionChains(driver).move_to_element(lokale).perform()
        time.sleep(2)
        
        driver.execute_script("goTo('/panier/')")
        time.sleep(5)
        
        historie_link = driver.find_element(By.LINK_TEXT, "Historie der Bestellungen")
        historie_link.click()
        time.sleep(5)
        
        print("✅ Historie-Seite geladen\n")
        
        # HTML speichern
        html = driver.page_source
        html_file = f"{BASE_DIR}/logs/historie_page.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"📄 HTML gespeichert: {html_file}\n")
        
        # Alle Links finden
        print("🔗 ALLE LINKS AUF DER SEITE:")
        print("-"*80)
        links = driver.find_elements(By.TAG_NAME, "a")
        for i, link in enumerate(links[:20], 1):  # Erste 20 Links
            text = link.text.strip()
            href = link.get_attribute('href')
            if text or href:
                print(f"{i:2}. Text: '{text[:50]}' | href: {href}")
        
        print("\n" + "="*80)
        
        # Tabellen finden
        print("\n📊 TABELLEN AUF DER SEITE:")
        print("-"*80)
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"Gefunden: {len(tables)} Tabellen\n")
        
        for i, table in enumerate(tables, 1):
            print(f"\nTabelle {i}:")
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"  Zeilen: {len(rows)}")
            
            if rows:
                # Erste Zeile analysieren
                first_row = rows[0]
                cells = first_row.find_elements(By.TAG_NAME, "td")
                if not cells:
                    cells = first_row.find_elements(By.TAG_NAME, "th")
                
                print(f"  Spalten: {len(cells)}")
                if cells:
                    print(f"  Header: {[c.text.strip()[:30] for c in cells]}")
                
                # Erste Datenzeile
                if len(rows) > 1:
                    data_row = rows[1]
                    data_cells = data_row.find_elements(By.TAG_NAME, "td")
                    if data_cells:
                        print(f"  Beispiel: {[c.text.strip()[:30] for c in data_cells]}")
        
        # Screenshot
        screenshot = f"{BASE_DIR}/logs/servicebox_screenshots/debug_historie.png"
        driver.save_screenshot(screenshot)
        print(f"\n📸 Screenshot: {screenshot}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
