#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ServiceBox Bestellungen API Test
=================================
Testet ob wir den gefundenen Endpoint direkt nutzen können.
"""

import os
import sys
import json
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

BASE_DIR = "/opt/greiner-portal"
CREDENTIALS_PATH = f"{BASE_DIR}/config/credentials.json"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_api_test_bestellungen.log"
OUTPUT_DIR = f"{BASE_DIR}/logs/servicebox_api_test"

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


def get_session_cookies(credentials):
    """Login via Selenium und extrahiere Session-Cookies"""
    log("=== SELENIUM LOGIN ===")

    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        username = credentials['username']
        password = credentials['password']
        base_url = credentials['portal_url']
        protocol, rest = base_url.split('://', 1)
        auth_url = f"{protocol}://{username}:{password}@{rest}"

        log(f"Login zu {base_url}...")
        driver.get(auth_url)
        import time
        time.sleep(8)

        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
        )
        log("✅ In frameHub")
        time.sleep(3)

        # Extrahiere Cookies
        selenium_cookies = driver.get_cookies()
        log(f"✅ {len(selenium_cookies)} Cookies erhalten")

        return selenium_cookies

    finally:
        driver.quit()


def test_list_commandes_endpoint(cookies, rrdi='DE08250'):
    """Teste den listCommandesRepAll.do Endpoint"""
    log("\n=== TEST: listCommandesRepAll.do ===")

    # Baue requests Session
    session = requests.Session()

    for cookie in cookies:
        session.cookies.set(
            cookie['name'],
            cookie['value'],
            domain=cookie.get('domain', 'servicebox.mpsa.com').lstrip('.'),
            path=cookie.get('path', '/')
        )

    # Headers wie Browser
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
        'Referer': 'https://servicebox.mpsa.com/panier/',
    })

    # Teste Endpoint
    url = f'https://servicebox.mpsa.com/panier/listCommandesRepAll.do'
    params = {
        'leftMenu': 'lcra',
        'rrdListStr': rrdi
    }

    log(f"GET {url}")
    log(f"  Params: {params}")

    try:
        resp = session.get(url, params=params, timeout=30)

        log(f"  Status: {resp.status_code}")
        log(f"  Content-Type: {resp.headers.get('Content-Type', 'unknown')}")
        log(f"  Content-Length: {len(resp.content)} bytes")

        # Prüfe auf Bestellnummern
        content = resp.text
        import re
        bestellnummern = re.findall(r'1[A-Z]{3}[A-Z0-9]{5}', content)
        
        log(f"  Gefundene Bestellnummern: {len(bestellnummern)}")
        if bestellnummern:
            log(f"  Erste 5: {bestellnummern[:5]}")

        # Speichere Response
        output_file = os.path.join(OUTPUT_DIR, 'listCommandesRepAll.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        log(f"  ✅ Gespeichert: {output_file}")

        # Prüfe ob HTML oder JSON
        if resp.headers.get('Content-Type', '').startswith('application/json'):
            log("  ✅ JSON Response!")
            try:
                json_data = resp.json()
                log(f"  JSON Keys: {list(json_data.keys())[:10]}")
            except:
                pass
        else:
            log("  ℹ️  HTML Response (kein JSON)")

        return resp.status_code == 200 and len(bestellnummern) > 0

    except Exception as e:
        log(f"  ❌ Fehler: {e}")
        return False


def main():
    log("\n" + "="*80)
    log("🚀 SERVICEBOX BESTELLUNGEN API TEST")
    log("="*80)

    try:
        credentials = load_credentials()

        # 1. Login und Cookies holen
        cookies = get_session_cookies(credentials)

        if not cookies:
            log("❌ Keine Cookies erhalten!")
            return False

        # 2. Teste Endpoint
        success = test_list_commandes_endpoint(cookies)

        # Zusammenfassung
        log("\n" + "="*80)
        log("📊 ZUSAMMENFASSUNG")
        log("="*80)
        if success:
            log("✅ API-ENDPOINT FUNKTIONIERT!")
            log("   Der Endpoint listCommandesRepAll.do kann direkt genutzt werden.")
        else:
            log("⚠️  API-ENDPOINT FUNKTIONIERT NICHT ODER KEINE DATEN")
            log("   Möglicherweise benötigt es zusätzliche Parameter oder Session-State.")
        log("="*80)

        return success

    except Exception as e:
        log(f"❌ FEHLER: {e}")
        import traceback
        log(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
