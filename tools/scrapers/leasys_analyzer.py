#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leasys Touch Analyse-Scraper
============================
Analysiert die Struktur von Leasys Touch für spätere Integration.

Erstellt: 2025-11-28
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

# Konfiguration
PORTAL_URL = "https://e-touch.leasys.com/"
SCREENSHOTS_DIR = "/tmp/leasys_screenshots"

# Timeouts
WAIT_SHORT = 5
WAIT_MEDIUM = 10
WAIT_LONG = 30

def setup_driver(headless=True):
    """Initialisiert den Chrome WebDriver."""
    print("🔧 Initialisiere WebDriver...")
    
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=de-DE')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)
    print("✅ WebDriver bereit")
    return driver


def take_screenshot(driver, name):
    """Speichert einen Screenshot."""
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{name}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    driver.save_screenshot(filepath)
    print(f"   📸 Screenshot: {filename}")
    return filepath


def analyze_page_structure(driver, page_name):
    """Analysiert die Struktur einer Seite."""
    print(f"\n📋 Analysiere Seite: {page_name}")
    print(f"   URL: {driver.current_url}")
    print(f"   Titel: {driver.title}")
    
    # Alle Formulare finden
    forms = driver.find_elements(By.TAG_NAME, "form")
    print(f"   📝 Formulare gefunden: {len(forms)}")
    for i, form in enumerate(forms):
        form_id = form.get_attribute("id") or "ohne ID"
        form_action = form.get_attribute("action") or "ohne Action"
        print(f"      Form {i+1}: ID={form_id}, Action={form_action}")
    
    # Alle Input-Felder
    inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"   📝 Input-Felder gefunden: {len(inputs)}")
    for inp in inputs:
        inp_type = inp.get_attribute("type") or "text"
        inp_name = inp.get_attribute("name") or inp.get_attribute("id") or "unbenannt"
        inp_placeholder = inp.get_attribute("placeholder") or ""
        if inp_type not in ["hidden"]:
            print(f"      - {inp_name} (type={inp_type}) {inp_placeholder}")
    
    # Alle Buttons
    buttons = driver.find_elements(By.TAG_NAME, "button")
    buttons += driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
    print(f"   🔘 Buttons gefunden: {len(buttons)}")
    for btn in buttons:
        btn_text = btn.text or btn.get_attribute("value") or "ohne Text"
        btn_type = btn.get_attribute("type") or "button"
        print(f"      - '{btn_text}' (type={btn_type})")
    
    # Links
    links = driver.find_elements(By.TAG_NAME, "a")
    print(f"   🔗 Links gefunden: {len(links)}")
    
    # Iframes (wichtig für SSO)
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"   🖼️ IFrames gefunden: {len(iframes)}")
    for iframe in iframes:
        iframe_src = iframe.get_attribute("src") or "ohne src"
        iframe_id = iframe.get_attribute("id") or "ohne ID"
        print(f"      - {iframe_id}: {iframe_src[:80]}...")
    
    return {
        "url": driver.current_url,
        "title": driver.title,
        "forms": len(forms),
        "inputs": len(inputs),
        "buttons": len(buttons),
        "iframes": len(iframes)
    }


def login(driver, username, password):
    """Führt den Login durch."""
    print("\n🔐 Starte Login-Prozess...")
    
    # Zur Login-Seite navigieren
    driver.get(PORTAL_URL)
    time.sleep(3)
    take_screenshot(driver, "01_initial_page")
    
    # Analysiere initiale Seite
    analyze_page_structure(driver, "Initial/Redirect")
    
    # Warte auf ADFS Login-Seite
    print("\n⏳ Warte auf ADFS Login-Seite...")
    time.sleep(5)
    take_screenshot(driver, "02_adfs_page")
    
    # Analysiere ADFS Seite
    analyze_page_structure(driver, "ADFS Login")
    
    # Versuche Username-Feld zu finden
    username_selectors = [
        "input[name='UserName']",
        "input[name='username']",
        "input[name='loginfmt']",
        "input[type='email']",
        "input#userNameInput",
        "input#i0116",
        "#userNameInput"
    ]
    
    username_field = None
    for selector in username_selectors:
        try:
            username_field = driver.find_element(By.CSS_SELECTOR, selector)
            print(f"   ✅ Username-Feld gefunden: {selector}")
            break
        except NoSuchElementException:
            continue
    
    if not username_field:
        print("   ❌ Username-Feld nicht gefunden!")
        # Versuche alle sichtbaren Inputs zu zeigen
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for inp in inputs:
            if inp.is_displayed():
                print(f"      Sichtbares Input: name={inp.get_attribute('name')}, id={inp.get_attribute('id')}, type={inp.get_attribute('type')}")
        return False
    
    # Username eingeben
    print(f"   📝 Gebe Username ein: {username}")
    username_field.clear()
    username_field.send_keys(username)
    time.sleep(1)
    take_screenshot(driver, "03_username_entered")
    
    # Versuche Password-Feld zu finden
    password_selectors = [
        "input[name='Password']",
        "input[name='password']",
        "input[name='passwd']",
        "input[type='password']",
        "input#passwordInput",
        "input#i0118",
        "#passwordInput"
    ]
    
    password_field = None
    for selector in password_selectors:
        try:
            password_field = driver.find_element(By.CSS_SELECTOR, selector)
            print(f"   ✅ Password-Feld gefunden: {selector}")
            break
        except NoSuchElementException:
            continue
    
    if not password_field:
        print("   ❌ Password-Feld nicht gefunden!")
        return False
    
    # Password eingeben
    print("   📝 Gebe Password ein: ********")
    password_field.clear()
    password_field.send_keys(password)
    time.sleep(1)
    take_screenshot(driver, "04_password_entered")
    
    # Submit-Button finden und klicken
    submit_selectors = [
        "input[type='submit']",
        "button[type='submit']",
        "#submitButton",
        "span#submitButton",
        ".submit",
        "button.primary"
    ]
    
    submit_btn = None
    for selector in submit_selectors:
        try:
            submit_btn = driver.find_element(By.CSS_SELECTOR, selector)
            if submit_btn.is_displayed():
                print(f"   ✅ Submit-Button gefunden: {selector}")
                break
        except NoSuchElementException:
            continue
    
    if not submit_btn:
        print("   ❌ Submit-Button nicht gefunden!")
        return False
    
    # Klicken
    print("   🖱️ Klicke auf Login...")
    submit_btn.click()
    time.sleep(5)
    take_screenshot(driver, "05_after_login_click")
    
    # Prüfe ob Login erfolgreich
    print(f"\n   📍 Aktuelle URL nach Login: {driver.current_url}")
    
    # Warte auf mögliche Weiterleitung
    time.sleep(5)
    take_screenshot(driver, "06_final_page")
    
    return True


def explore_portal(driver):
    """Erkundet das Portal nach erfolgreichem Login."""
    print("\n🔍 Erkunde Portal...")
    
    # Analysiere Hauptseite
    analyze_page_structure(driver, "Portal Hauptseite")
    
    # Suche nach Navigation/Menü
    nav_selectors = [
        "nav", ".navbar", ".menu", ".sidebar",
        "[role='navigation']", ".nav-menu"
    ]
    
    for selector in nav_selectors:
        try:
            nav = driver.find_element(By.CSS_SELECTOR, selector)
            print(f"   ✅ Navigation gefunden: {selector}")
            # Links im Menü
            links = nav.find_elements(By.TAG_NAME, "a")
            print(f"      Menü-Links: {len(links)}")
            for link in links[:10]:  # Erste 10
                href = link.get_attribute("href") or ""
                text = link.text.strip() or link.get_attribute("title") or ""
                if text:
                    print(f"         - {text}: {href[:50]}")
        except NoSuchElementException:
            continue
    
    # Suche nach Kalkulations-Bereich
    calc_keywords = ["kalkul", "calcul", "angebot", "offer", "quote", "leasing"]
    all_links = driver.find_elements(By.TAG_NAME, "a")
    
    print("\n   🔍 Suche nach Kalkulations-Links...")
    for link in all_links:
        text = (link.text or "").lower()
        href = (link.get_attribute("href") or "").lower()
        for keyword in calc_keywords:
            if keyword in text or keyword in href:
                print(f"      📌 Gefunden: '{link.text}' -> {link.get_attribute('href')}")
                break


def main():
    """Hauptfunktion."""
    print("=" * 60)
    print("🚗 LEASYS TOUCH ANALYSE-SCRAPER")
    print("=" * 60)
    
    # Credentials aus Argumenten oder Umgebungsvariablen
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
    else:
        username = os.environ.get("LEASYS_USER", "")
        password = os.environ.get("LEASYS_PASS", "")
    
    if not username or not password:
        print("❌ Keine Credentials angegeben!")
        print("   Verwendung: python leasys_analyzer.py USERNAME PASSWORD")
        print("   Oder: LEASYS_USER=xxx LEASYS_PASS=xxx python leasys_analyzer.py")
        sys.exit(1)
    
    driver = None
    try:
        driver = setup_driver(headless=True)
        
        # Login durchführen
        if login(driver, username, password):
            print("\n✅ Login-Prozess abgeschlossen")
            
            # Portal erkunden
            explore_portal(driver)
        else:
            print("\n❌ Login fehlgeschlagen")
        
        print(f"\n📁 Screenshots gespeichert in: {SCREENSHOTS_DIR}")
        
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        if driver:
            take_screenshot(driver, "error")
    
    finally:
        if driver:
            driver.quit()
            print("\n🔧 WebDriver beendet")


if __name__ == "__main__":
    main()
