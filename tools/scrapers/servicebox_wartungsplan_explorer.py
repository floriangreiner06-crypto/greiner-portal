#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Service Box - Wartungsplan Explorer
===============================================
Erkundet die Servicebox-Struktur um Wartungs-/Inspektionspläne zu finden.

ZIEL:
- Navigation zu Wartungsplänen finden
- VIN-basierte Suche testen
- PDF/Dokument-Download identifizieren

Version: TAG 129 - Explorer
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
SCREENSHOTS_DIR = f"{BASE_DIR}/logs/servicebox_wartungsplan_screenshots"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_wartungsplan_explorer.log"
OUTPUT_FILE = f"{BASE_DIR}/logs/servicebox_wartungsplan_struktur.json"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Test-VIN (ein bekanntes Fahrzeug aus dem Bestand)
TEST_VIN = None  # Wird später gesetzt oder als Parameter übergeben


def log(message):
    """Logging mit Timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')


def load_credentials():
    """Lädt Servicebox-Credentials"""
    with open(CREDENTIALS_PATH, 'r') as f:
        creds = json.load(f)
    return creds['external_systems']['stellantis_servicebox']


def setup_driver(headless=True):
    """Initialisiert Chrome WebDriver"""
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
    """Speichert Screenshot"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{name}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    driver.save_screenshot(filepath)
    log(f"📸 Screenshot: {filename}")
    return filepath


def save_html(driver, name):
    """Speichert HTML-Quelle"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{name}.html"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    log(f"📄 HTML gespeichert: {filename}")
    return filepath


def login(driver, credentials):
    """Login via HTTP Basic Auth"""
    log("\n🔐 LOGIN")
    log("=" * 60)

    username = credentials['username']
    password = credentials['password']
    base_url = credentials['portal_url']

    # HTTP Basic Auth via URL
    protocol, rest = base_url.split('://', 1)
    auth_url = f"{protocol}://{username}:{password}@{rest}"

    try:
        driver.get(auth_url)
        time.sleep(8)

        take_screenshot(driver, "01_after_login")

        # Wechsle in frameHub
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


def explore_menu_structure(driver):
    """Erkundet die Menüstruktur nach Wartungs-/Inspektionsplänen"""
    log("\n🔍 ERKUNDE MENÜSTRUKTUR")
    log("=" * 60)

    menu_items = {}

    # Suche nach allen Hauptmenü-Links
    try:
        # Methode 1: Alle Links im Menü
        links = driver.find_elements(By.TAG_NAME, "a")

        log(f"\n📋 Gefundene Links: {len(links)}")

        interesting_keywords = [
            'wartung', 'inspektion', 'service', 'plan', 'technical',
            'technisch', 'dokumentation', 'reparatur', 'anleitung',
            'maintenance', 'manual', 'repair', 'diagnos'
        ]

        for link in links:
            try:
                text = link.text.strip()
                href = link.get_attribute('href') or ''
                onclick = link.get_attribute('onclick') or ''

                if text and len(text) > 2:
                    # Prüfe ob interessant
                    is_interesting = any(kw in text.lower() or kw in href.lower()
                                        for kw in interesting_keywords)

                    menu_items[text] = {
                        'href': href,
                        'onclick': onclick,
                        'interesting': is_interesting
                    }

                    if is_interesting:
                        log(f"   ⭐ {text}")
                        log(f"      href: {href[:80]}..." if len(href) > 80 else f"      href: {href}")

            except Exception:
                continue

        # Methode 2: Suche nach Menü-Elementen mit bestimmten Klassen
        menu_elements = driver.find_elements(By.CSS_SELECTOR, ".menu-item, .nav-item, [class*='menu']")
        log(f"\n📋 Menü-Elemente gefunden: {len(menu_elements)}")

        for elem in menu_elements:
            try:
                text = elem.text.strip()
                if text and len(text) > 2:
                    log(f"   - {text[:50]}")
            except:
                continue

    except Exception as e:
        log(f"❌ Fehler bei Menü-Exploration: {e}")

    return menu_items


def find_technical_documentation(driver):
    """Versucht zur technischen Dokumentation zu navigieren"""
    log("\n🔧 SUCHE TECHNISCHE DOKUMENTATION")
    log("=" * 60)

    # Mögliche Menüpunkte für Dokumentation
    doc_keywords = [
        "TECHNISCHE DOKUMENTATION",
        "DOKUMENTATION",
        "TECHNICAL",
        "SERVICE",
        "WARTUNG",
        "REPARATUR",
        "DIAGNOSE"
    ]

    for keyword in doc_keywords:
        try:
            log(f"   Suche nach: {keyword}")

            # Versuche Link zu finden
            elements = driver.find_elements(By.PARTIAL_LINK_TEXT, keyword)

            if elements:
                log(f"   ✅ Gefunden: {len(elements)} Element(e)")

                for elem in elements:
                    text = elem.text.strip()
                    log(f"      → {text}")

                # Hover über erstes Element
                if elements[0].is_displayed():
                    ActionChains(driver).move_to_element(elements[0]).perform()
                    time.sleep(2)
                    take_screenshot(driver, f"03_hover_{keyword.lower().replace(' ', '_')}")

                    # Suche nach Untermenü
                    sub_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='goTo'], a[onclick*='goTo']")
                    for sub in sub_links:
                        sub_text = sub.text.strip()
                        if sub_text:
                            log(f"         Untermenü: {sub_text}")

        except Exception as e:
            log(f"   ⚠️ Fehler bei {keyword}: {e}")
            continue

    return None


def try_navigate_to_wartung(driver):
    """Versucht verschiedene Navigationspfade zu Wartungsplänen"""
    log("\n🚗 VERSUCHE NAVIGATION ZU WARTUNGSPLÄNEN")
    log("=" * 60)

    # Liste von goTo-Pfaden zum Testen
    goto_paths = [
        '/diagnostic/',
        '/serviceBox/',
        '/documentation/',
        '/maintenance/',
        '/repair/',
        '/technical/',
        '/vehicleInfo/',
        '/carInfo/',
    ]

    for path in goto_paths:
        try:
            log(f"   Teste goTo('{path}')...")

            # JavaScript ausführen
            driver.execute_script(f"goTo('{path}')")
            time.sleep(3)

            # Prüfe ob Seite geladen
            page_text = driver.page_source.lower()

            if 'error' not in page_text and 'nicht gefunden' not in page_text:
                log(f"   ✅ Pfad funktioniert: {path}")
                take_screenshot(driver, f"04_goto_{path.replace('/', '_')}")
                save_html(driver, f"04_goto_{path.replace('/', '_')}")

                # Suche nach VIN-Eingabefeld
                vin_fields = driver.find_elements(By.CSS_SELECTOR,
                    "input[name*='vin'], input[name*='VIN'], input[id*='vin'], input[placeholder*='VIN']")

                if vin_fields:
                    log(f"   🎯 VIN-Eingabefeld gefunden!")
                    return path

        except Exception as e:
            log(f"   ⚠️ Fehler bei {path}: {str(e)[:50]}")
            continue

    return None


def explore_all_frames(driver):
    """Erkundet alle iFrames auf der Seite"""
    log("\n🖼️ ERKUNDE FRAMES")
    log("=" * 60)

    # Zurück zum Hauptdokument
    driver.switch_to.default_content()

    frames = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
    log(f"   Gefundene Frames: {len(frames)}")

    frame_info = []

    for i, frame in enumerate(frames):
        try:
            frame_id = frame.get_attribute('id') or f"frame_{i}"
            frame_name = frame.get_attribute('name') or ''
            frame_src = frame.get_attribute('src') or ''

            log(f"   [{i}] ID: {frame_id}, Name: {frame_name}")
            log(f"       Src: {frame_src[:80]}..." if len(frame_src) > 80 else f"       Src: {frame_src}")

            frame_info.append({
                'index': i,
                'id': frame_id,
                'name': frame_name,
                'src': frame_src
            })

        except Exception as e:
            log(f"   ⚠️ Fehler bei Frame {i}: {e}")

    return frame_info


def search_for_vin_input(driver):
    """Sucht nach VIN-Eingabefeldern auf der aktuellen Seite"""
    log("\n🔎 SUCHE VIN-EINGABEFELD")
    log("=" * 60)

    # Verschiedene Selektoren für VIN-Felder
    selectors = [
        "input[name*='vin' i]",
        "input[id*='vin' i]",
        "input[placeholder*='VIN' i]",
        "input[placeholder*='Fahrgestell' i]",
        "input[name*='chassis' i]",
        "input[name*='vehicleId' i]",
        "input[type='text'][maxlength='17']",
    ]

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                log(f"   ✅ Gefunden mit '{selector}': {len(elements)} Element(e)")
                for elem in elements:
                    log(f"      → Name: {elem.get_attribute('name')}, ID: {elem.get_attribute('id')}")
                return elements[0]
        except:
            continue

    log("   ❌ Kein VIN-Eingabefeld gefunden")
    return None


def main():
    """Haupt-Explorer-Routine"""
    log("\n" + "=" * 70)
    log("🔍 STELLANTIS SERVICE BOX - WARTUNGSPLAN EXPLORER")
    log("   Ziel: Navigation zu Inspektionsplänen finden")
    log("=" * 70)

    driver = None
    results = {
        'timestamp': datetime.now().isoformat(),
        'menu_items': {},
        'frames': [],
        'working_paths': [],
        'vin_field_found': False
    }

    try:
        credentials = load_credentials()
        driver = setup_driver(headless=True)

        if not login(driver, credentials):
            log("\n❌ Login fehlgeschlagen!")
            return False

        # 1. Frames erkunden
        results['frames'] = explore_all_frames(driver)

        # Zurück in frameHub
        driver.switch_to.default_content()
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
        )

        # 2. Menüstruktur erkunden
        results['menu_items'] = explore_menu_structure(driver)

        # 3. Technische Dokumentation suchen
        find_technical_documentation(driver)

        # 4. goTo-Pfade testen
        working_path = try_navigate_to_wartung(driver)
        if working_path:
            results['working_paths'].append(working_path)

        # 5. VIN-Eingabefeld suchen
        vin_field = search_for_vin_input(driver)
        results['vin_field_found'] = vin_field is not None

        # Finaler Screenshot
        take_screenshot(driver, "99_final_state")
        save_html(driver, "99_final_state")

        # Ergebnisse speichern
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        log(f"\n💾 Ergebnisse gespeichert: {OUTPUT_FILE}")

        # Zusammenfassung
        log("\n" + "=" * 70)
        log("📊 ZUSAMMENFASSUNG")
        log("=" * 70)
        log(f"   Frames gefunden: {len(results['frames'])}")
        log(f"   Menüpunkte gefunden: {len(results['menu_items'])}")
        interesting = [k for k, v in results['menu_items'].items() if v.get('interesting')]
        log(f"   Interessante Menüpunkte: {len(interesting)}")
        for item in interesting:
            log(f"      ⭐ {item}")
        log(f"   Funktionierende Pfade: {results['working_paths']}")
        log(f"   VIN-Eingabefeld: {'✅ Ja' if results['vin_field_found'] else '❌ Nein'}")
        log("=" * 70)

        return True

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
        log(f"📂 Log: {LOG_FILE}")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
