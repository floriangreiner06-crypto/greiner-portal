#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Service Box - Network Request Analyzer
==================================================
Analysiert die tatsächlichen HTTP-Requests im Browser mittels Selenium DevTools.
Ziel: Finde die echten API-Endpoints und notwendigen Headers.
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
OUTPUT_DIR = f"{BASE_DIR}/logs/servicebox_network"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_network_analyzer.log"

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


def setup_driver_with_logging(headless=True):
    """Chrome mit Performance-Logging für Network-Analyse"""
    log("Initialisiere Chrome mit Network-Logging...")

    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=de-DE')

    # Aktiviere Performance-Logging
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)

    return driver


def extract_network_logs(driver):
    """Extrahiere Network-Requests aus Chrome Performance-Logs"""
    logs = driver.get_log('performance')

    requests = []
    responses = []

    for entry in logs:
        try:
            message = json.loads(entry['message'])['message']
            method = message.get('method', '')

            if method == 'Network.requestWillBeSent':
                req = message.get('params', {}).get('request', {})
                if req.get('url'):
                    requests.append({
                        'url': req.get('url'),
                        'method': req.get('method'),
                        'headers': req.get('headers', {}),
                        'postData': req.get('postData', '')
                    })

            elif method == 'Network.responseReceived':
                resp = message.get('params', {}).get('response', {})
                if resp.get('url'):
                    responses.append({
                        'url': resp.get('url'),
                        'status': resp.get('status'),
                        'headers': resp.get('headers', {})
                    })

        except Exception:
            continue

    return requests, responses


def analyze_servicebox(vin, headless=True):
    """Analysiere die Servicebox-Requests bei VIN-Suche"""
    log("=" * 70)
    log("SERVICEBOX NETWORK ANALYZER")
    log(f"VIN: {vin}")
    log("=" * 70)

    driver = None
    all_requests = []
    all_responses = []

    try:
        credentials = load_credentials()
        driver = setup_driver_with_logging(headless=headless)

        username = credentials['username']
        password = credentials['password']
        base_url = credentials['portal_url']

        protocol, rest = base_url.split('://', 1)
        auth_url = f"{protocol}://{username}:{password}@{rest}"

        # 1. Login
        log("\n=== PHASE 1: Login ===")
        driver.get(auth_url)
        time.sleep(8)

        reqs, resps = extract_network_logs(driver)
        all_requests.extend(reqs)
        all_responses.extend(resps)
        log(f"Requests nach Login: {len(reqs)}")

        # Wechsle in Frame
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
        )
        log("In frameHub")
        time.sleep(3)

        # 2. Navigation zu Tech Doc
        log("\n=== PHASE 2: Navigation zu Tech-Doc ===")

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

            reqs, resps = extract_network_logs(driver)
            all_requests.extend(reqs)
            all_responses.extend(resps)
            log(f"Neue Requests nach Tech-Doc Navigation: {len(reqs)}")

        except Exception as e:
            log(f"Navigation-Fehler: {e}")

        # 3. VIN-Suche
        log("\n=== PHASE 3: VIN-Suche ===")

        try:
            vin_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "short-vin"))
            )
            vin_input.click()
            vin_input.clear()
            time.sleep(0.5)
            vin_input.send_keys(vin)
            time.sleep(1)

            # Suche nach Submit-Button
            submit_selectors = [
                (By.CSS_SELECTOR, "input[name='VIN_OK_BUTTON']"),
                (By.CSS_SELECTOR, "input[type='image'][src*='search']"),
                (By.CSS_SELECTOR, "input[type='submit']"),
            ]

            for by, selector in submit_selectors:
                try:
                    submit_btn = driver.find_element(by, selector)
                    if submit_btn.is_displayed():
                        submit_btn.click()
                        log(f"Klick auf: {selector}")
                        break
                except:
                    continue

            time.sleep(8)  # Warte auf Response

            reqs, resps = extract_network_logs(driver)
            all_requests.extend(reqs)
            all_responses.extend(resps)
            log(f"Requests nach VIN-Suche: {len(reqs)}")

        except Exception as e:
            log(f"VIN-Suche Fehler: {e}")

        # 4. Analyse der Requests
        log("\n" + "=" * 70)
        log("ANALYSE DER REQUESTS")
        log("=" * 70)

        # Interessante Patterns
        api_patterns = ['/api/', '/rest/', '/json/', '/xml/', '.do', '/service/', '/ws/']

        interesting_requests = []

        for req in all_requests:
            url = req['url']
            if any(pattern in url.lower() for pattern in api_patterns):
                interesting_requests.append(req)

        log(f"\nInteressante Requests ({len(interesting_requests)}):")

        for req in interesting_requests:
            url = req['url']
            # Entferne Credentials aus URL
            if '@' in url:
                url = url.split('@')[-1]

            log(f"\n  {req['method']} {url[:100]}")

            # Wichtige Headers
            important_headers = ['content-type', 'x-requested-with', 'x-csrf-token',
                               'authorization', 'cookie', 'referer']

            for key, value in req.get('headers', {}).items():
                if key.lower() in important_headers:
                    log(f"    {key}: {value[:50] if len(str(value)) > 50 else value}")

            if req.get('postData'):
                log(f"    POST Data: {req['postData'][:100]}")

        # 5. Speichere alle Requests
        output_file = os.path.join(OUTPUT_DIR, f"network_analysis_{vin}.json")

        # Bereinige URLs von Credentials
        clean_requests = []
        for req in all_requests:
            clean_req = req.copy()
            if '@' in clean_req.get('url', ''):
                parts = clean_req['url'].split('@')
                clean_req['url'] = parts[0].split('://')[0] + '://' + parts[-1]
            clean_requests.append(clean_req)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'vin': vin,
                'timestamp': datetime.now().isoformat(),
                'total_requests': len(all_requests),
                'interesting_requests': len(interesting_requests),
                'requests': clean_requests[:100],  # Nur erste 100
            }, f, indent=2, ensure_ascii=False)

        log(f"\nGespeichert: {output_file}")

        # 6. Suche nach API-Patterns
        log("\n" + "=" * 70)
        log("API-PATTERN ANALYSE")
        log("=" * 70)

        unique_endpoints = set()
        for req in all_requests:
            url = req['url']
            if '@' in url:
                url = url.split('@')[-1]

            # Extrahiere Basis-URL
            if '?' in url:
                base = url.split('?')[0]
            else:
                base = url

            if '.do' in base or '/api/' in base or '/rest/' in base:
                unique_endpoints.add(base)

        log(f"\nGefundene Endpoints ({len(unique_endpoints)}):")
        for endpoint in sorted(unique_endpoints):
            log(f"  {endpoint}")

        return True

    except Exception as e:
        log(f"FEHLER: {e}")
        import traceback
        log(traceback.format_exc())
        return False

    finally:
        if driver:
            driver.quit()


def main():
    test_vin = "W0L0SDL68A4087224"
    success = analyze_servicebox(test_vin, headless=True)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
