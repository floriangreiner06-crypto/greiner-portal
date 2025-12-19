#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Service Box - Technische Dokumentation Explorer
==========================================================
Navigiert zur "Technischen Dokumentation Opel (PSA)" und sucht nach
Wartungs-/Inspektionsplänen mit VIN-Eingabe.

Version: TAG 129 - TechDoc Explorer
Datum: 2025-12-19
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

BASE_DIR = "/opt/greiner-portal"
CREDENTIALS_PATH = f"{BASE_DIR}/config/credentials.json"
SCREENSHOTS_DIR = f"{BASE_DIR}/logs/servicebox_techdoc_screenshots"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_techdoc_explorer.log"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Test-VIN für einen Opel (aus Locosoft Bestand holen)
TEST_VIN = "W0L000000Y2000000"  # Beispiel-VIN, wird später ersetzt


def log(message):
    """Logging mit Timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')


def load_credentials():
    with open(CREDENTIALS_PATH, 'r') as f:
        creds = json.load(f)
    return creds['external_systems']['stellantis_servicebox']


def setup_driver(headless=True):
    log("🔧 Initialisiere Chrome WebDriver...")
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    if headless:
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
    return filepath


def save_html(driver, name):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{name}.html"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    log(f"📄 HTML: {filename}")
    return filepath


def login(driver, credentials):
    log("\n🔐 LOGIN")
    log("=" * 60)

    username = credentials['username']
    password = credentials['password']
    base_url = credentials['portal_url']
    protocol, rest = base_url.split('://', 1)
    auth_url = f"{protocol}://{username}:{password}@{rest}"

    try:
        driver.get(auth_url)
        time.sleep(8)
        take_screenshot(driver, "01_after_login")

        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
        )
        log("✅ In frameHub gewechselt")
        time.sleep(3)
        take_screenshot(driver, "02_in_frame")
        return True

    except Exception as e:
        log(f"❌ Login-Fehler: {e}")
        take_screenshot(driver, "error_login")
        return False


def navigate_to_tech_doc(driver):
    """Navigiert zu DOKUMENTATION → Technische Dokumentation Opel (PSA)"""
    log("\n📂 NAVIGATION ZU TECHNISCHER DOKUMENTATION")
    log("=" * 60)

    try:
        # Schritt 1: Hover über DOKUMENTATION
        log("   Suche DOKUMENTATION...")

        doc_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "DOKUMENTATION"))
        )

        log("   ✅ DOKUMENTATION gefunden")
        ActionChains(driver).move_to_element(doc_link).perform()
        time.sleep(2)

        take_screenshot(driver, "03_hover_dokumentation")

        # Schritt 2: Klick auf "Technische Dokumentation Opel (PSA)"
        log("   Suche 'Technische Dokumentation Opel (PSA)'...")

        # Verschiedene Selektoren probieren
        selectors = [
            (By.PARTIAL_LINK_TEXT, "Technische Dokumentation Opel (PSA)"),
            (By.PARTIAL_LINK_TEXT, "Technische Dokumentation Opel"),
            (By.XPATH, "//a[contains(text(), 'Technische Dokumentation') and contains(text(), 'PSA')]"),
            (By.XPATH, "//a[contains(text(), 'Technische Dokumentation Opel')]"),
        ]

        tech_doc_link = None
        for by, selector in selectors:
            try:
                tech_doc_link = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((by, selector))
                )
                log(f"   ✅ Gefunden mit: {selector}")
                break
            except:
                continue

        if not tech_doc_link:
            log("   ❌ Technische Dokumentation nicht gefunden!")
            # Zeige alle Links unter DOKUMENTATION
            all_links = driver.find_elements(By.TAG_NAME, "a")
            log("   Verfügbare Links:")
            for link in all_links:
                text = link.text.strip()
                if text and 'Technisch' in text or 'Opel' in text or 'Dokumentation' in text:
                    log(f"      - {text}")
            return False

        log("   Klicke auf Technische Dokumentation...")
        tech_doc_link.click()
        time.sleep(5)

        take_screenshot(driver, "04_tech_doc_loaded")
        save_html(driver, "04_tech_doc_loaded")

        return True

    except Exception as e:
        log(f"❌ Fehler bei Navigation: {e}")
        take_screenshot(driver, "error_navigation")
        import traceback
        log(traceback.format_exc())
        return False


def explore_tech_doc_page(driver):
    """Erkundet die Technische Dokumentation Seite"""
    log("\n🔍 ERKUNDE TECH-DOC SEITE")
    log("=" * 60)

    # Prüfe ob neues Fenster/Tab geöffnet wurde
    handles = driver.window_handles
    log(f"   Fenster/Tabs: {len(handles)}")

    if len(handles) > 1:
        log("   Wechsle zu neuem Tab...")
        driver.switch_to.window(handles[-1])
        time.sleep(3)
        take_screenshot(driver, "05_new_tab")
        save_html(driver, "05_new_tab")

    # Suche nach VIN-Eingabefeld
    log("\n   Suche VIN-Eingabefeld...")

    selectors = [
        "input[name*='vin' i]",
        "input[id*='vin' i]",
        "input[placeholder*='VIN' i]",
        "input[placeholder*='Fahrgestell' i]",
        "input[placeholder*='chassis' i]",
        "input[name*='chassis' i]",
        "input[type='text'][maxlength='17']",
        "input[name*='vehicle' i]",
        "#vin",
        "#VIN",
    ]

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                log(f"   ✅ VIN-Feld gefunden: {selector}")
                for elem in elements:
                    name = elem.get_attribute('name') or ''
                    id_ = elem.get_attribute('id') or ''
                    placeholder = elem.get_attribute('placeholder') or ''
                    log(f"      Name: {name}, ID: {id_}, Placeholder: {placeholder}")
                return elements[0]
        except:
            continue

    # Suche nach allen Eingabefeldern
    log("\n   Alle Eingabefelder auf der Seite:")
    inputs = driver.find_elements(By.TAG_NAME, "input")
    for inp in inputs[:20]:  # Max 20 zeigen
        try:
            inp_type = inp.get_attribute('type') or ''
            name = inp.get_attribute('name') or ''
            id_ = inp.get_attribute('id') or ''
            placeholder = inp.get_attribute('placeholder') or ''
            if inp_type in ['text', 'search', '']:
                log(f"      <input type='{inp_type}' name='{name}' id='{id_}' placeholder='{placeholder}'>")
        except:
            continue

    # Suche nach Links/Buttons die relevant sein könnten
    log("\n   Relevante Links/Buttons:")
    keywords = ['wartung', 'inspektion', 'service', 'maintenance', 'intervall',
                'plan', 'fahrzeug', 'vehicle', 'suche', 'search']

    all_links = driver.find_elements(By.TAG_NAME, "a")
    for link in all_links:
        text = link.text.strip().lower()
        href = (link.get_attribute('href') or '').lower()
        if any(kw in text or kw in href for kw in keywords):
            log(f"      ⭐ {link.text.strip()}")

    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        text = btn.text.strip().lower()
        if any(kw in text for kw in keywords):
            log(f"      🔘 {btn.text.strip()}")

    return None


def check_for_iframe(driver):
    """Prüft ob die Seite iFrames enthält und wechselt hinein"""
    log("\n🖼️ PRÜFE IFRAMES")
    log("=" * 60)

    frames = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
    log(f"   Gefundene Frames: {len(frames)}")

    for i, frame in enumerate(frames):
        try:
            frame_id = frame.get_attribute('id') or f"frame_{i}"
            frame_src = frame.get_attribute('src') or ''
            log(f"   [{i}] {frame_id}: {frame_src[:60]}...")

            # Versuche in Frame zu wechseln
            driver.switch_to.frame(frame)
            log(f"       → In Frame gewechselt")
            time.sleep(2)

            take_screenshot(driver, f"06_frame_{frame_id}")

            # Suche VIN-Feld in diesem Frame
            vin_field = explore_tech_doc_page(driver)
            if vin_field:
                return vin_field

            # Zurück zum Parent
            driver.switch_to.parent_frame()

        except Exception as e:
            log(f"       ⚠️ Fehler: {e}")
            driver.switch_to.default_content()

    return None


def main():
    log("\n" + "=" * 70)
    log("🔧 STELLANTIS SERVICE BOX - TECH-DOC EXPLORER")
    log("   Ziel: Navigation zu Wartungsplänen mit VIN-Suche")
    log("=" * 70)

    driver = None

    try:
        credentials = load_credentials()
        driver = setup_driver(headless=True)

        if not login(driver, credentials):
            log("\n❌ Login fehlgeschlagen!")
            return False

        if not navigate_to_tech_doc(driver):
            log("\n❌ Navigation zu Tech-Doc fehlgeschlagen!")
            # Trotzdem weitermachen und erkunden

        # Erkunde die aktuelle Seite
        vin_field = explore_tech_doc_page(driver)

        if not vin_field:
            # Prüfe iFrames
            vin_field = check_for_iframe(driver)

        # Zusammenfassung
        log("\n" + "=" * 70)
        log("📊 ERGEBNIS")
        log("=" * 70)
        if vin_field:
            log("✅ VIN-Eingabefeld gefunden!")
            log("   Nächster Schritt: VIN eingeben und Wartungsplan abrufen")
        else:
            log("❌ Kein VIN-Eingabefeld gefunden")
            log("   → Manuell prüfen: Screenshots in logs/servicebox_techdoc_screenshots/")
        log("=" * 70)

        return vin_field is not None

    except Exception as e:
        log(f"\n❌ Fehler: {e}")
        import traceback
        log(traceback.format_exc())
        if driver:
            take_screenshot(driver, "error_final")
        return False

    finally:
        if driver:
            log("\n🔚 Schließe Browser...")
            driver.quit()
        log(f"\n📂 Screenshots: {SCREENSHOTS_DIR}")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
