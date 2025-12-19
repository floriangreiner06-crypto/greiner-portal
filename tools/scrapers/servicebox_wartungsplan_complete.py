#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Service Box - Wartungsplan Komplett-Extraktion
==========================================================
Navigiert zu allen relevanten Bereichen und extrahiert Wartungspläne.

Bekannte Pfade für Wartungspläne:
- /docapvpr/ → menu_GENERAL → accesDocGen.do
- Charakteristik enthält Serviceintervalle
- Borddokumentation enthält Wartungsanweisungen

Version: TAG 129
"""

import os
import sys
import time
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

BASE_DIR = "/opt/greiner-portal"
CREDENTIALS_PATH = f"{BASE_DIR}/config/credentials.json"
OUTPUT_DIR = f"{BASE_DIR}/logs/servicebox_wartungsplaene"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_wartungsplan_complete.log"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def log(message):
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
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=de-DE')

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver


def take_screenshot(driver, name):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{name}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    driver.save_screenshot(filepath)
    log(f"Screenshot: {filename}")
    return filepath


def save_html(driver, name):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{name}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    return filepath


def login(driver, credentials):
    log("Login...")
    username = credentials['username']
    password = credentials['password']
    base_url = credentials['portal_url']

    protocol, rest = base_url.split('://', 1)
    auth_url = f"{protocol}://{username}:{password}@{rest}"

    driver.get(auth_url)
    time.sleep(8)

    WebDriverWait(driver, 15).until(
        EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
    )
    log("Login erfolgreich")
    time.sleep(3)
    return True


def navigate_to_tech_doc(driver):
    log("Navigation zu Tech-Doc...")
    try:
        doc_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "DOKUMENTATION"))
        )
        ActionChains(driver).move_to_element(doc_link).perform()
        time.sleep(2)

        tech_doc_link = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Technische Dokumentation Opel (PSA)"))
        )
        tech_doc_link.click()
        time.sleep(5)
        log("Tech-Doc geladen")
        return True
    except Exception as e:
        log(f"Navigation-Fehler: {e}")
        return False


def search_vin(driver, vin):
    log(f"Suche VIN: {vin}")
    try:
        vin_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "short-vin"))
        )
        vin_input.click()
        vin_input.clear()
        time.sleep(0.5)
        vin_input.send_keys(vin)
        time.sleep(1)

        submit_btn = driver.find_element(By.CSS_SELECTOR, "input[name='VIN_OK_BUTTON']")
        submit_btn.click()
        time.sleep(5)
        log("VIN-Suche abgeschlossen")
        return True
    except Exception as e:
        log(f"VIN-Suche Fehler: {e}")
        return False


def click_charakteristik(driver):
    """Klickt auf Charakteristik - enthält Fahrzeugdaten und Serviceinfos"""
    log("Lade Charakteristik...")
    try:
        char_link = driver.find_element(By.CSS_SELECTOR, "#menu_caracteristiques a")
        char_link.click()
        time.sleep(5)
        log("Charakteristik geladen")
        return True
    except Exception as e:
        log(f"Charakteristik-Fehler: {e}")
        return False


def click_allgemeines(driver):
    """Klickt auf Allgemeines (General) Menü"""
    log("Lade Allgemeines...")
    try:
        # Suche nach menu_GENERAL
        general_link = driver.find_element(By.CSS_SELECTOR, "#menu_GENERAL a")
        general_link.click()
        time.sleep(5)
        log("Allgemeines geladen")
        return True
    except Exception as e:
        log(f"Allgemeines-Fehler: {e}")
        # Versuche alternativen Selektor
        try:
            general_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Allgemein")
            general_link.click()
            time.sleep(5)
            return True
        except:
            pass
        return False


def open_borddokumentation(driver):
    """Öffnet Borddokumentation (enthält Wartungsanweisungen)"""
    log("Öffne Borddokumentation...")
    try:
        # Das öffnet ein neues Fenster
        doc_bord = driver.find_element(By.CSS_SELECTOR, "#menu_DocBord a")
        doc_bord.click()
        time.sleep(3)

        # Wechsle zum neuen Fenster
        handles = driver.window_handles
        if len(handles) > 1:
            driver.switch_to.window(handles[-1])
            time.sleep(5)
            log("Borddokumentation in neuem Fenster")
            return True
        return False
    except Exception as e:
        log(f"Borddokumentation-Fehler: {e}")
        return False


def extract_charakteristik_data(driver, vin):
    """Extrahiert Fahrzeug-Charakteristik mit Serviceintervallen"""
    log("Extrahiere Charakteristik-Daten...")

    result = {
        'vin': vin,
        'fahrzeug': {},
        'motor': {},
        'getriebe': {},
        'service_intervall': {},
    }

    page_source = driver.page_source

    # Modell
    model_match = re.search(r'(CORSA|ASTRA|MOKKA|GRANDLAND|CROSSLAND|COMBO|VIVARO|MOVANO)[-\s]?([A-Z0-9])?[^\<]{0,30}', page_source, re.IGNORECASE)
    if model_match:
        result['fahrzeug']['modell'] = model_match.group(0).strip()

    # Baujahr
    year_match = re.search(r'\((\d{2})-(\d{2})\)', page_source)
    if year_match:
        result['fahrzeug']['baujahr_von'] = f"20{year_match.group(1)}"
        result['fahrzeug']['baujahr_bis'] = f"20{year_match.group(2)}"

    # Motor
    engine_patterns = [
        r'MOTEUR\s+(ESSENCE|DIESEL)\s+([\d.]+)',
        r'(\d+\.\d+)\s*(L|l)?\s*(Benzin|Diesel|ESSENCE|DIESEL)',
        r'(\d+)\s*PS',
        r'(\d+)\s*kW',
    ]

    for pattern in engine_patterns:
        match = re.search(pattern, page_source, re.IGNORECASE)
        if match:
            result['motor']['raw'] = match.group(0)
            break

    # Getriebe
    trans_match = re.search(r'(MANUELLE|AUTOMATIQUE|MANUAL|AUTOMATIC)\s*(\d+)\s*(RAPPORTS?|GANG|SPEED)?', page_source, re.IGNORECASE)
    if trans_match:
        result['getriebe']['typ'] = trans_match.group(1)
        result['getriebe']['gaenge'] = trans_match.group(2)

    # Service-Intervall (km und/oder Zeit)
    km_patterns = [
        r'(\d{1,2})[.,]?(\d{3})\s*(km|KM)',
        r'Service.*?(\d+)[.,]?(\d{3})\s*(km|KM)',
        r'Intervall.*?(\d+)[.,]?(\d{3})\s*(km|KM)',
    ]

    for pattern in km_patterns:
        match = re.search(pattern, page_source)
        if match:
            km = match.group(1) + match.group(2)
            result['service_intervall']['km'] = int(km)
            break

    # Zeit-Intervall
    time_patterns = [
        r'(\d+)\s*(Jahr|year|an)',
        r'(\d+)\s*(Monat|month|mois)',
    ]

    for pattern in time_patterns:
        match = re.search(pattern, page_source, re.IGNORECASE)
        if match:
            result['service_intervall']['zeit'] = match.group(0)
            break

    log(f"  Fahrzeug: {result['fahrzeug']}")
    log(f"  Motor: {result['motor']}")
    log(f"  Intervall: {result['service_intervall']}")

    return result


def extract_service_items(driver):
    """Extrahiert Service-Positionen aus der Dokumentation"""
    log("Extrahiere Service-Positionen...")

    items = []
    page_source = driver.page_source

    # Typische Wartungs-Keywords
    service_keywords = [
        ('Ölwechsel', 'Motoröl'),
        ('Ölfilter', 'Ölfilter'),
        ('Luftfilter', 'Luftfilter'),
        ('Pollenfilter', 'Innenraumfilter'),
        ('Kraftstofffilter', 'Kraftstofffilter'),
        ('Zündkerzen', 'Zündkerzen'),
        ('Bremsflüssigkeit', 'Bremsflüssigkeit'),
        ('Kühlflüssigkeit', 'Kühlmittel'),
        ('Zahnriemen', 'Zahnriemen'),
        ('Keilrippenriemen', 'Keilriemen'),
        ('Getriebeöl', 'Getriebeöl'),
        ('Klimaanlage', 'Klimaservice'),
        ('Batterie', 'Batterie'),
        ('Bremsen', 'Bremsbeläge'),
    ]

    for keyword, name in service_keywords:
        if re.search(keyword, page_source, re.IGNORECASE):
            items.append({
                'name': name,
                'keyword_found': keyword
            })

    log(f"  Service-Positionen gefunden: {len(items)}")
    return items


def get_wartungsplan(vin, headless=True):
    """Hauptfunktion: Holt kompletten Wartungsplan für VIN"""
    log("=" * 70)
    log(f"WARTUNGSPLAN KOMPLETT - VIN: {vin}")
    log("=" * 70)

    driver = None
    result = {
        'vin': vin,
        'timestamp': datetime.now().isoformat(),
        'success': False,
        'charakteristik': {},
        'service_items': [],
        'screenshots': [],
        'error': None
    }

    try:
        credentials = load_credentials()
        driver = setup_driver(headless=headless)

        # Login
        if not login(driver, credentials):
            result['error'] = 'Login fehlgeschlagen'
            return result

        # Navigation
        if not navigate_to_tech_doc(driver):
            result['error'] = 'Navigation fehlgeschlagen'
            return result

        # VIN-Suche
        if not search_vin(driver, vin):
            result['error'] = 'VIN-Suche fehlgeschlagen'
            return result

        result['screenshots'].append(take_screenshot(driver, f"{vin}_01_nach_vin"))
        save_html(driver, f"{vin}_01_nach_vin")

        # Charakteristik laden
        if click_charakteristik(driver):
            result['screenshots'].append(take_screenshot(driver, f"{vin}_02_charakteristik"))
            save_html(driver, f"{vin}_02_charakteristik")
            result['charakteristik'] = extract_charakteristik_data(driver, vin)

        # Allgemeines laden
        if click_allgemeines(driver):
            result['screenshots'].append(take_screenshot(driver, f"{vin}_03_allgemeines"))
            save_html(driver, f"{vin}_03_allgemeines")
            result['service_items'] = extract_service_items(driver)

        # Borddokumentation (neues Fenster)
        main_window = driver.current_window_handle
        if open_borddokumentation(driver):
            result['screenshots'].append(take_screenshot(driver, f"{vin}_04_borddokumentation"))
            save_html(driver, f"{vin}_04_borddokumentation")

            # Extrahiere Wartungsplan aus Borddokumentation
            borddoc_items = extract_service_items(driver)
            result['service_items'].extend(borddoc_items)

            # Zurück zum Hauptfenster
            driver.close()
            driver.switch_to.window(main_window)

        result['success'] = True

        # Speichere Ergebnis
        output_file = os.path.join(OUTPUT_DIR, f"wartungsplan_complete_{vin}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        log(f"\nErgebnis gespeichert: {output_file}")

        return result

    except Exception as e:
        log(f"FEHLER: {e}")
        import traceback
        log(traceback.format_exc())
        result['error'] = str(e)
        if driver:
            take_screenshot(driver, f"{vin}_error")
        return result

    finally:
        if driver:
            driver.quit()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Servicebox Wartungsplan Komplett')
    parser.add_argument('vin', nargs='?', default='W0L0SDL68A4087224',
                       help='VIN des Fahrzeugs')
    parser.add_argument('--visible', action='store_true',
                       help='Browser sichtbar')

    args = parser.parse_args()

    result = get_wartungsplan(args.vin, headless=not args.visible)

    # Zusammenfassung
    print("\n" + "=" * 70)
    print("ERGEBNIS")
    print("=" * 70)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    return 0 if result.get('success') else 1


if __name__ == "__main__":
    sys.exit(main())
