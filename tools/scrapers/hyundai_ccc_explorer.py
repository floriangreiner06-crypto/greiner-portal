#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyundai CCC Portal Explorer (2FA mit Remote-Debugging)
=======================================================
Startet Chrome mit Remote-Debugging-Port.
Du kannst dann von deinem lokalen PC aus:
  chrome://inspect oder http://SERVER_IP:9222 

Oder: Nutze VNC/RDP zum Server.

Alternative: Headless mit manueller Code-Eingabe in Konsole.

Version: 1.1 - Remote Debug / Konsolen-2FA
Erstellt: 2025-12-04
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

# ============================================================================
# KONFIGURATION
# ============================================================================

CCC_URL = "https://ccc.hyundai.com"
USERNAME = "david.moser@auto-greiner.de"
PASSWORD = "LuisaSandra092025!!"

# Output-Verzeichnis
OUTPUT_DIR = Path("/opt/greiner-portal/data/hyundai_ccc")
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"

# ============================================================================
# BROWSER SETUP
# ============================================================================

def create_browser_headless():
    """Erstellt Chrome im Headless-Modus für Server ohne Display"""
    
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def save_screenshot(driver, name):
    """Speichert Screenshot"""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = SCREENSHOT_DIR / f"{timestamp}_{name}.png"
    driver.save_screenshot(str(filepath))
    print(f"📸 Screenshot: {filepath}")
    return filepath


def save_json(data, name):
    """Speichert JSON"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = OUTPUT_DIR / f"{timestamp}_{name}.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"💾 JSON: {filepath}")
    return filepath


def save_html(driver, name):
    """Speichert HTML"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = OUTPUT_DIR / f"{timestamp}_{name}.html"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"📄 HTML: {filepath}")
    return filepath


# ============================================================================
# LOGIN MIT KONSOLEN-2FA
# ============================================================================

def login_with_console_2fa(driver):
    """
    Login mit 2FA-Code Eingabe über Konsole
    """
    
    print("="*70)
    print("🔐 HYUNDAI CCC PORTAL - LOGIN")
    print("="*70)
    
    # 1. Startseite laden
    print(f"\n1️⃣ Lade {CCC_URL}...")
    driver.get(CCC_URL)
    time.sleep(5)
    
    save_screenshot(driver, "01_startseite")
    save_html(driver, "01_startseite")
    
    print(f"   Titel: {driver.title}")
    print(f"   URL: {driver.current_url}")
    
    # 2. Login-Formular analysieren
    print("\n2️⃣ Analysiere Login-Seite...")
    
    inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"   Input-Felder gefunden: {len(inputs)}")
    
    for i, inp in enumerate(inputs):
        try:
            inp_type = inp.get_attribute("type") or "?"
            inp_id = inp.get_attribute("id") or ""
            inp_name = inp.get_attribute("name") or ""
            is_visible = inp.is_displayed()
            if is_visible:
                print(f"   [{i}] type={inp_type:12} id={inp_id:20} name={inp_name}")
        except:
            pass
    
    # Username/Password Felder finden
    username_field = None
    password_field = None
    
    # Username
    for selector in [
        (By.ID, "userId"), (By.ID, "username"), (By.ID, "loginId"),
        (By.NAME, "userId"), (By.NAME, "username"),
        (By.CSS_SELECTOR, "input[type='text']"),
        (By.CSS_SELECTOR, "input[type='email']"),
    ]:
        try:
            els = driver.find_elements(*selector)
            for el in els:
                if el.is_displayed():
                    username_field = el
                    print(f"\n   ✅ Username-Feld: {selector}")
                    break
            if username_field:
                break
        except:
            pass
    
    # Password
    for selector in [
        (By.ID, "password"), (By.ID, "userPwd"),
        (By.NAME, "password"), (By.NAME, "userPwd"),
        (By.CSS_SELECTOR, "input[type='password']"),
    ]:
        try:
            els = driver.find_elements(*selector)
            for el in els:
                if el.is_displayed():
                    password_field = el
                    print(f"   ✅ Password-Feld: {selector}")
                    break
            if password_field:
                break
        except:
            pass
    
    if not username_field or not password_field:
        print("\n   ❌ Login-Felder nicht gefunden!")
        
        # Prüfe iFrames
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            print(f"   📋 {len(iframes)} iFrames gefunden - versuche ersten...")
            driver.switch_to.frame(iframes[0])
            time.sleep(2)
            save_screenshot(driver, "01b_iframe")
            
            # Rekursiv nochmal versuchen
            inputs = driver.find_elements(By.TAG_NAME, "input")
            print(f"   Input-Felder im iFrame: {len(inputs)}")
            
            for selector in [(By.CSS_SELECTOR, "input[type='text']"), (By.CSS_SELECTOR, "input[type='email']")]:
                try:
                    els = driver.find_elements(*selector)
                    for el in els:
                        if el.is_displayed():
                            username_field = el
                            break
                except:
                    pass
            
            for selector in [(By.CSS_SELECTOR, "input[type='password']")]:
                try:
                    els = driver.find_elements(*selector)
                    for el in els:
                        if el.is_displayed():
                            password_field = el
                            break
                except:
                    pass
    
    if not username_field or not password_field:
        print("\n   ❌ Konnte Login-Felder nicht finden!")
        return False
    
    # 3. Credentials eingeben
    print("\n3️⃣ Gebe Credentials ein...")
    
    username_field.clear()
    time.sleep(0.2)
    username_field.send_keys(USERNAME)
    print(f"   Username: {USERNAME}")
    
    password_field.clear()
    time.sleep(0.2)
    password_field.send_keys(PASSWORD)
    print(f"   Password: {'*' * len(PASSWORD)}")
    
    save_screenshot(driver, "02_credentials")
    
    # 4. Login-Button klicken
    print("\n4️⃣ Klicke Login-Button...")
    
    clicked = False
    for selector in [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "input[type='submit']"),
        (By.CSS_SELECTOR, "button.btn-primary"),
        (By.CSS_SELECTOR, "#loginBtn"),
        (By.XPATH, "//button[contains(text(), 'Login')]"),
        (By.XPATH, "//button[contains(text(), 'LOG IN')]"),
        (By.XPATH, "//button[contains(text(), 'Sign')]"),
    ]:
        try:
            btns = driver.find_elements(*selector)
            for btn in btns:
                if btn.is_displayed():
                    btn.click()
                    print(f"   ✅ Button geklickt: {selector}")
                    clicked = True
                    break
            if clicked:
                break
        except:
            pass
    
    if not clicked:
        print("   ⚠️ Kein Button gefunden, drücke Enter...")
        password_field.send_keys(Keys.RETURN)
    
    # 5. Warten auf 2FA-Dialog
    print("\n5️⃣ Warte auf 2FA-Dialog...")
    time.sleep(5)
    
    save_screenshot(driver, "03_nach_login_click")
    save_html(driver, "03_nach_login_click")
    
    # Prüfe ob 2FA-Feld erscheint
    print("\n" + "="*70)
    print("  🔑 2-FAKTOR-AUTHENTIFIZIERUNG")
    print("="*70)
    
    # Suche nach OTP/2FA Eingabefeld
    otp_field = None
    otp_selectors = [
        (By.ID, "otp"),
        (By.ID, "otpCode"),
        (By.ID, "verificationCode"),
        (By.ID, "authCode"),
        (By.ID, "mfaCode"),
        (By.NAME, "otp"),
        (By.NAME, "otpCode"),
        (By.NAME, "verificationCode"),
        (By.CSS_SELECTOR, "input[placeholder*='OTP']"),
        (By.CSS_SELECTOR, "input[placeholder*='code']"),
        (By.CSS_SELECTOR, "input[placeholder*='Code']"),
        (By.CSS_SELECTOR, "input[maxlength='6']"),
        (By.CSS_SELECTOR, "input[type='tel']"),
    ]
    
    for selector in otp_selectors:
        try:
            els = driver.find_elements(*selector)
            for el in els:
                if el.is_displayed():
                    otp_field = el
                    print(f"\n   ✅ OTP-Feld gefunden: {selector}")
                    break
            if otp_field:
                break
        except:
            pass
    
    if otp_field:
        # 2FA-Code über Konsole eingeben
        print("""
   📱 Öffne deine Authenticator-App und gib den 6-stelligen Code ein:
        """)
        
        otp_code = input("   🔑 2FA-Code eingeben: ").strip()
        
        if otp_code:
            otp_field.clear()
            otp_field.send_keys(otp_code)
            print(f"   Code eingegeben: {otp_code}")
            
            save_screenshot(driver, "04_otp_eingegeben")
            
            # Submit-Button für OTP suchen
            time.sleep(1)
            for selector in [
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "button.btn-primary"),
                (By.XPATH, "//button[contains(text(), 'Verify')]"),
                (By.XPATH, "//button[contains(text(), 'Submit')]"),
                (By.XPATH, "//button[contains(text(), 'Confirm')]"),
                (By.XPATH, "//button[contains(text(), 'OK')]"),
            ]:
                try:
                    btns = driver.find_elements(*selector)
                    for btn in btns:
                        if btn.is_displayed():
                            btn.click()
                            print(f"   ✅ OTP-Button geklickt")
                            break
                except:
                    pass
            
            time.sleep(5)
    else:
        print("\n   ⚠️ Kein OTP-Feld gefunden - vielleicht anderer 2FA-Typ?")
        print("   Schaue in den Screenshot...")
        
        # Zeige alle sichtbaren Inputs
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for inp in inputs:
            if inp.is_displayed():
                print(f"   Input: type={inp.get_attribute('type')} id={inp.get_attribute('id')}")
    
    # 6. Ergebnis prüfen
    time.sleep(3)
    save_screenshot(driver, "05_nach_2fa")
    save_html(driver, "05_nach_2fa")
    
    current_url = driver.current_url
    print(f"\n   Finale URL: {current_url}")
    print(f"   Titel: {driver.title}")
    
    # Erfolg?
    if 'login' not in current_url.lower() or 'portal' in current_url.lower():
        print("\n✅ LOGIN SCHEINT ERFOLGREICH!")
        return True
    else:
        print("\n⚠️ Status unklar - prüfe Screenshots")
        return True  # Weitermachen


def explore_portal(driver):
    """Erkundet das Portal"""
    
    print("\n" + "="*70)
    print("🔍 PORTAL EXPLORATION")
    print("="*70)
    
    data = {
        'timestamp': datetime.now().isoformat(),
        'url': driver.current_url,
        'title': driver.title,
        'links': [],
        'modules': []
    }
    
    # Links sammeln
    print("\n📋 Sammle Links...")
    
    keywords = ['gwms', 'gsw', 'warranty', 'garantie', 'claim', 'vehicle', 
                'vin', 'campaign', 'recall', 'service', 'parts', 'technical']
    
    links = driver.find_elements(By.TAG_NAME, "a")
    for link in links:
        try:
            href = link.get_attribute("href") or ""
            text = link.text.strip()
            if href and text:
                data['links'].append({'text': text, 'href': href})
                if any(kw in text.lower() or kw in href.lower() for kw in keywords):
                    print(f"   🔗 {text[:40]:40} → {href[:50]}")
                    data['modules'].append({'text': text, 'href': href})
        except:
            pass
    
    print(f"\n   Gesamt: {len(data['links'])} Links, {len(data['modules'])} relevante Module")
    
    save_screenshot(driver, "06_portal")
    save_json(data, "exploration")
    
    return data


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*70)
    print("  🚗 HYUNDAI CCC PORTAL EXPLORER")
    print("  (Headless mit Konsolen-2FA)")
    print("="*70)
    print(f"  Zeit:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Portal: {CCC_URL}")
    print(f"  User:   {USERNAME}")
    print("="*70)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    
    driver = None
    
    try:
        print("\n🌐 Starte Chrome (headless)...")
        driver = create_browser_headless()
        
        # Login
        login_success = login_with_console_2fa(driver)
        
        if login_success:
            explore_portal(driver)
        
        print("\n" + "="*70)
        print("✅ FERTIG!")
        print(f"   Screenshots: {SCREENSHOT_DIR}")
        print("="*70)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Abgebrochen")
        return 1
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        if driver:
            save_screenshot(driver, "error")
        return 1
        
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    sys.exit(main())
