#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Financial Services - Portal Explorer
================================================
Erkundet das Portal und macht Screenshots aller Bereiche
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
from selenium.webdriver.chrome.options import Options

# Pfade
BASE_DIR = "/opt/greiner-portal"
CREDENTIALS_FILE = os.path.join(BASE_DIR, "config/credentials.json")
OUTPUT_DIR = "/tmp/stellantis_explorer"

def load_credentials():
    with open(CREDENTIALS_FILE, 'r') as f:
        creds = json.load(f)
    return creds.get('external_systems', {}).get('stellantis_finance', {})

def setup_driver():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--lang=de-DE')
    
    driver = webdriver.Chrome(options=opts)
    driver.implicitly_wait(5)
    return driver

def explore_portal():
    print("\n" + "="*70)
    print("🔍 STELLANTIS FINANCIAL SERVICES - PORTAL EXPLORER")
    print("="*70)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    creds = load_credentials()
    print(f"\n📋 Portal: {'https://infonet.stellantis-financial-services.de/site/home/'}")
    print(f"   User: {creds['username']}")
    
    driver = None
    results = {'pages': [], 'screenshots': [], 'menus': []}
    
    try:
        driver = setup_driver()
        wait = WebDriverWait(driver, 15)
        
        # === LOGIN ===
        print("\n🔐 SCHRITT 1: Login...")
        driver.get('https://infonet.stellantis-financial-services.de/site/home/')
        time.sleep(3)
        
        # Screenshot Login-Seite
        driver.save_screenshot(os.path.join(OUTPUT_DIR, "00_login_page.png"))
        results['screenshots'].append("00_login_page.png")
        print(f"   📸 Login-Seite")
        
        # Login-Formular finden
        try:
            # Versuche verschiedene Selektoren
            username_field = None
            for selector in ["input[name='username']", "input[name='user']", "input[type='text']", "#username", "#user"]:
                try:
                    username_field = driver.find_element(By.CSS_SELECTOR, selector)
                    if username_field:
                        break
                except:
                    continue
            
            if not username_field:
                # Alle Input-Felder auflisten
                inputs = driver.find_elements(By.TAG_NAME, "input")
                print(f"   🔍 Gefundene Input-Felder: {len(inputs)}")
                for i, inp in enumerate(inputs):
                    print(f"      {i}: type={inp.get_attribute('type')}, name={inp.get_attribute('name')}, id={inp.get_attribute('id')}")
                
                if len(inputs) >= 2:
                    username_field = inputs[0]
                    password_field = inputs[1]
            else:
                password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            username_field.send_keys(creds['username'])
            time.sleep(1)
            password_field.send_keys(creds['password'])
            time.sleep(1)
            
            driver.save_screenshot(os.path.join(OUTPUT_DIR, "01_login_filled.png"))
            results['screenshots'].append("01_login_filled.png")
            
            # Submit
            submit_btn = None
            for selector in ["button[type='submit']", "input[type='submit']", "button.login", ".btn-login", "button"]:
                try:
                    btns = driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in btns:
                        if btn.is_displayed():
                            submit_btn = btn
                            break
                    if submit_btn:
                        break
                except:
                    continue
            
            if submit_btn:
                submit_btn.click()
                time.sleep(5)
                print("   ✅ Login abgeschickt")
            
            driver.save_screenshot(os.path.join(OUTPUT_DIR, "02_after_login.png"))
            results['screenshots'].append("02_after_login.png")
            
        except Exception as e:
            print(f"   ❌ Login-Fehler: {e}")
            driver.save_screenshot(os.path.join(OUTPUT_DIR, "error_login.png"))
        
        # === MENÜ ERKUNDEN ===
        print("\n📋 SCHRITT 2: Menü-Struktur...")
        
        # Menü-Links finden
        menu_links = []
        for selector in ["nav a", ".nav a", ".menu a", "header a", ".navbar a", "a[href*='/']"]:
            try:
                links = driver.find_elements(By.CSS_SELECTOR, selector)
                for link in links:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    if href and text and 'logout' not in href.lower():
                        menu_links.append({'text': text, 'href': href})
            except:
                continue
        
        # Duplikate entfernen
        seen = set()
        unique_menus = []
        for m in menu_links:
            if m['href'] not in seen:
                seen.add(m['href'])
                unique_menus.append(m)
                print(f"   → {m['text']}: {m['href']}")
        
        results['menus'] = unique_menus
        
        # === SEITEN BESUCHEN ===
        print("\n🌐 SCHRITT 3: Seiten erkunden...")
        
        pages_to_visit = [
            {"name": "Einkaufsfinanzierung", "url": 'https://infonet.stellantis-financial-services.de/site/home/' + "/einkaufsfinanzierung/"},
            {"name": "Online Financing", "url": 'https://infonet.stellantis-financial-services.de/site/home/' + "/online-financing/"},
            {"name": "Postfach", "url": 'https://infonet.stellantis-financial-services.de/site/home/' + "/postfach/"},
            {"name": "Bestandsliste", "url": 'https://infonet.stellantis-financial-services.de/site/home/' + "/bestandsliste/"},
            {"name": "Fahrzeuge", "url": 'https://infonet.stellantis-financial-services.de/site/home/' + "/fahrzeuge/"},
        ]
        
        # Auch gefundene Menü-Links besuchen
        for menu in unique_menus[:10]:
            if menu['href'] not in [p['url'] for p in pages_to_visit]:
                pages_to_visit.append({'name': menu['text'], 'url': menu['href']})
        
        for i, page in enumerate(pages_to_visit):
            try:
                print(f"\n   📄 {page['name']}...")
                driver.get(page['url'])
                time.sleep(3)
                
                screenshot_name = f"{i+10:02d}_{page['name'].lower().replace(' ', '_')}.png"
                driver.save_screenshot(os.path.join(OUTPUT_DIR, screenshot_name))
                results['screenshots'].append(screenshot_name)
                
                # Seiteninhalt analysieren
                page_info = {
                    'name': page['name'],
                    'url': driver.current_url,
                    'title': driver.title,
                    'tables': [],
                    'links': [],
                    'buttons': []
                }
                
                # Tabellen finden
                tables = driver.find_elements(By.TAG_NAME, "table")
                if tables:
                    print(f"      📊 {len(tables)} Tabelle(n) gefunden")
                    for t, table in enumerate(tables[:3]):
                        headers = [th.text for th in table.find_elements(By.TAG_NAME, "th")]
                        rows = len(table.find_elements(By.TAG_NAME, "tr"))
                        page_info['tables'].append({'headers': headers, 'rows': rows})
                        if headers:
                            print(f"         Tabelle {t+1}: {headers[:5]}")
                
                # Download-Buttons/Links
                downloads = driver.find_elements(By.XPATH, "//*[contains(@class, 'download') or contains(text(), 'Download') or contains(text(), 'CSV') or contains(text(), 'Export')]")
                if downloads:
                    print(f"      ⬇️ {len(downloads)} Download-Option(en)")
                    for d in downloads[:5]:
                        page_info['buttons'].append(d.text or d.get_attribute('class'))
                
                results['pages'].append(page_info)
                
            except Exception as e:
                print(f"      ❌ Fehler: {e}")
        
        # === ERGEBNIS SPEICHERN ===
        print("\n💾 Ergebnisse speichern...")
        with open(os.path.join(OUTPUT_DIR, "exploration_results.json"), 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Screenshots: {OUTPUT_DIR}/")
        for s in results['screenshots']:
            print(f"   → {s}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        if driver:
            driver.save_screenshot(os.path.join(OUTPUT_DIR, "error.png"))
        return None
        
    finally:
        if driver:
            driver.quit()
            print("\n🔚 Browser geschlossen")

if __name__ == "__main__":
    results = explore_portal()
    
    print("\n" + "="*70)
    if results:
        print(f"✅ Exploration abgeschlossen!")
        print(f"   Screenshots: {len(results['screenshots'])}")
        print(f"   Seiten: {len(results['pages'])}")
        print(f"   Menüs: {len(results['menus'])}")
    else:
        print("❌ Exploration fehlgeschlagen")
    print("="*70)
