#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Service Box - Wartungsplan PDF Extraktion
=====================================================
Navigiert zur Wartungsplan-Seite und extrahiert die PDFs.

Version: TAG 129
"""

import os
import sys
import time
import json
import requests
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
PDF_DIR = f"{OUTPUT_DIR}/pdfs"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_wartungsplan_pdf.log"

os.makedirs(PDF_DIR, exist_ok=True)


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


def setup_driver(headless=True, download_dir=None):
    """Chrome mit PDF-Download-Einstellungen"""
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'

    if headless:
        chrome_options.add_argument('--headless=new')

    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=de-DE')

    # PDF-Download statt Anzeige
    if download_dir:
        prefs = {
            'download.default_directory': download_dir,
            'download.prompt_for_download': False,
            'plugins.always_open_pdf_externally': True,
            'download.directory_upgrade': True,
        }
        chrome_options.add_experimental_option('prefs', prefs)

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


def login(driver, credentials):
    """Login mit HTTP Basic Auth"""
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
    """Navigiert zur Technischen Dokumentation"""
    log("Navigation zu Tech-Doc...")

    try:
        # Hover über DOKUMENTATION
        doc_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "DOKUMENTATION"))
        )
        ActionChains(driver).move_to_element(doc_link).perform()
        time.sleep(2)

        # Klick auf Technische Dokumentation Opel (PSA)
        tech_doc_link = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Technische Dokumentation Opel"))
        )
        tech_doc_link.click()
        time.sleep(5)

        log("Tech-Doc geladen")
        return True

    except Exception as e:
        log(f"Navigation-Fehler: {e}")
        return False


def search_vin(driver, vin):
    """VIN-Suche"""
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

        # Submit
        submit_btn = driver.find_element(By.CSS_SELECTOR, "input[name='VIN_OK_BUTTON']")
        submit_btn.click()
        time.sleep(5)

        log("VIN-Suche abgeschlossen")
        return True

    except Exception as e:
        log(f"VIN-Suche Fehler: {e}")
        return False


def find_and_extract_wartungsplan(driver, vin):
    """Findet Wartungsplan und extrahiert Informationen"""
    log("Suche Wartungsplan...")

    result = {
        'vin': vin,
        'timestamp': datetime.now().isoformat(),
        'vehicle_info': {},
        'wartungsplan_links': [],
        'pdf_links': [],
        'screenshots': []
    }

    try:
        # Screenshot der aktuellen Seite
        take_screenshot(driver, f"{vin}_01_after_vin")

        # Extrahiere Fahrzeuginfo aus der Seite
        page_source = driver.page_source

        # Suche nach Fahrzeugmodell im Seitentitel/Header
        import re

        # Modell finden (z.B. CORSA-D, ASTRA-J)
        model_match = re.search(r'(CORSA|ASTRA|MOKKA|GRANDLAND|CROSSLAND|COMBO|VIVARO|MOVANO)[-\s]?([A-Z0-9])?', page_source, re.IGNORECASE)
        if model_match:
            result['vehicle_info']['model'] = model_match.group(0)

        # Motor finden
        engine_match = re.search(r'MOTEUR\s+(ESSENCE|DIESEL)\s+([\d.]+)', page_source, re.IGNORECASE)
        if engine_match:
            result['vehicle_info']['engine'] = engine_match.group(0)

        # Suche nach Wartungsplan-Menüpunkt
        # Die Wartungspläne sind unter "PE" (Plan d'Entretien) kategorisiert

        # Methode 1: Suche nach direktem Link
        wartung_keywords = ['wartung', 'inspektion', 'service', 'entretien', 'maintenance', 'interval']

        all_links = driver.find_elements(By.TAG_NAME, "a")
        for link in all_links:
            try:
                text = link.text.strip().lower()
                href = (link.get_attribute('href') or '').lower()
                onclick = (link.get_attribute('onclick') or '').lower()

                if any(kw in text or kw in href or kw in onclick for kw in wartung_keywords):
                    result['wartungsplan_links'].append({
                        'text': link.text.strip(),
                        'href': link.get_attribute('href'),
                        'onclick': link.get_attribute('onclick')
                    })
            except:
                continue

        log(f"Gefundene Wartungs-Links: {len(result['wartungsplan_links'])}")

        # Methode 2: Suche nach PDF-Links
        pdf_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='.pdf'], a[onclick*='pdf'], a[href*='getPdf']")
        for link in pdf_links:
            try:
                result['pdf_links'].append({
                    'text': link.text.strip(),
                    'href': link.get_attribute('href'),
                })
            except:
                continue

        log(f"Gefundene PDF-Links: {len(result['pdf_links'])}")

        # Methode 3: Suche in JavaScript nach PE/Wartungsplan URLs
        scripts = driver.find_elements(By.TAG_NAME, "script")
        for script in scripts:
            try:
                content = script.get_attribute('innerHTML') or ''
                # Suche nach PE-URLs
                pe_matches = re.findall(r'["\']([^"\']*(?:PE|wartung|entretien|maintenance)[^"\']*)["\']', content, re.IGNORECASE)
                for match in pe_matches[:5]:  # Max 5
                    if len(match) > 5 and len(match) < 200:
                        result['wartungsplan_links'].append({'from_script': match})
            except:
                continue

        # Versuche zu den Wartungsplänen zu navigieren
        # Suche nach Menüpunkt "Allgemeines" oder "Wartungspläne"

        try:
            # Suche nach Allgemeines-Menü
            allgemein_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Allgemeines")
            log("Klicke auf 'Allgemeines'...")
            allgemein_link.click()
            time.sleep(3)

            take_screenshot(driver, f"{vin}_02_allgemeines")

            # Suche jetzt nach Wartungsplan-Untermenü
            try:
                wartung_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Wartung")
                log("Klicke auf 'Wartung'...")
                wartung_link.click()
                time.sleep(3)
                take_screenshot(driver, f"{vin}_03_wartung")

            except:
                log("Kein 'Wartung' Link gefunden")

        except:
            log("Kein 'Allgemeines' Menü gefunden")

        # Alternative: Suche nach Eingriff -> Mechanik -> Wartungsarbeiten
        try:
            mechanik_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Mechanik")
            if mechanik_link.is_displayed():
                log("Klicke auf 'Mechanik'...")
                mechanik_link.click()
                time.sleep(3)
                take_screenshot(driver, f"{vin}_04_mechanik")

                # Suche nach Untermenüs
                sub_links = driver.find_elements(By.CSS_SELECTOR, "#menu_FCT0001 a, .submenu a")
                for sub in sub_links[:10]:
                    text = sub.text.strip()
                    if text:
                        log(f"  Untermenü: {text}")

        except:
            pass

        # Speichere HTML für weitere Analyse
        html_file = os.path.join(OUTPUT_DIR, f"{vin}_page_source.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        log(f"HTML gespeichert: {html_file}")

        return result

    except Exception as e:
        log(f"Fehler bei Wartungsplan-Suche: {e}")
        import traceback
        log(traceback.format_exc())
        return result


def try_extract_pdf_via_iframe(driver, vin):
    """Versucht PDFs aus iFrames zu extrahieren"""
    log("Suche PDFs in iFrames...")

    pdf_urls = []

    # Zurück zum Haupt-Frame
    driver.switch_to.default_content()

    # Alle Frames finden
    frames = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
    log(f"Gefundene Frames: {len(frames)}")

    for i, frame in enumerate(frames):
        try:
            frame_src = frame.get_attribute('src') or ''
            log(f"  Frame {i}: {frame_src[:80]}")

            if 'pdf' in frame_src.lower():
                pdf_urls.append(frame_src)

            # In Frame wechseln und nach PDFs suchen
            driver.switch_to.frame(frame)

            # Suche nach PDF-Links im Frame
            pdf_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='.pdf'], embed[src*='.pdf'], object[data*='.pdf']")
            for link in pdf_links:
                href = link.get_attribute('href') or link.get_attribute('src') or link.get_attribute('data')
                if href:
                    pdf_urls.append(href)

            driver.switch_to.parent_frame()

        except Exception as e:
            log(f"  Frame {i} Fehler: {e}")
            driver.switch_to.default_content()

    return pdf_urls


def download_pdf_with_session(driver, pdf_url, output_path):
    """Lädt PDF mit der Browser-Session herunter"""
    log(f"Download PDF: {pdf_url[:80]}...")

    try:
        # Hole Cookies vom Browser
        cookies = driver.get_cookies()

        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])

        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })

        resp = session.get(pdf_url, timeout=60)

        if resp.status_code == 200 and 'pdf' in resp.headers.get('Content-Type', '').lower():
            with open(output_path, 'wb') as f:
                f.write(resp.content)
            log(f"PDF gespeichert: {output_path} ({len(resp.content)} bytes)")
            return True
        else:
            log(f"Kein PDF: Status={resp.status_code}, Type={resp.headers.get('Content-Type')}")
            return False

    except Exception as e:
        log(f"Download-Fehler: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Servicebox Wartungsplan PDF Extraktion')
    parser.add_argument('vin', nargs='?', default='W0L0SDL68A4087224',
                       help='VIN des Fahrzeugs')
    parser.add_argument('--visible', action='store_true',
                       help='Browser sichtbar')

    args = parser.parse_args()
    vin = args.vin.strip().upper()

    log("=" * 70)
    log(f"WARTUNGSPLAN PDF EXTRAKTION - VIN: {vin}")
    log("=" * 70)

    driver = None

    try:
        credentials = load_credentials()
        driver = setup_driver(headless=not args.visible, download_dir=PDF_DIR)

        # Login
        if not login(driver, credentials):
            return 1

        # Navigation
        if not navigate_to_tech_doc(driver):
            take_screenshot(driver, f"{vin}_error_nav")
            return 1

        # VIN-Suche
        if not search_vin(driver, vin):
            take_screenshot(driver, f"{vin}_error_vin")
            return 1

        # Wartungsplan finden
        result = find_and_extract_wartungsplan(driver, vin)

        # PDFs aus iFrames
        pdf_urls = try_extract_pdf_via_iframe(driver, vin)
        result['iframe_pdfs'] = pdf_urls

        # PDFs herunterladen
        for i, url in enumerate(pdf_urls[:5]):  # Max 5 PDFs
            pdf_path = os.path.join(PDF_DIR, f"{vin}_wartungsplan_{i+1}.pdf")
            download_pdf_with_session(driver, url, pdf_path)

        # Ergebnis speichern
        output_file = os.path.join(OUTPUT_DIR, f"pdf_extraction_{vin}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        log(f"\nErgebnis gespeichert: {output_file}")

        # Zusammenfassung
        log("\n" + "=" * 70)
        log("ZUSAMMENFASSUNG")
        log("=" * 70)
        log(f"Fahrzeug: {result.get('vehicle_info', {})}")
        log(f"Wartungs-Links: {len(result.get('wartungsplan_links', []))}")
        log(f"PDF-Links: {len(result.get('pdf_links', []))}")
        log(f"iFrame-PDFs: {len(pdf_urls)}")
        log("=" * 70)

        return 0

    except Exception as e:
        log(f"FEHLER: {e}")
        import traceback
        log(traceback.format_exc())
        if driver:
            take_screenshot(driver, f"{vin}_error_final")
        return 1

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    sys.exit(main())
