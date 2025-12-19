#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Service Box - API Endpoint Test
===========================================
Testet ob wir nach Selenium-Login die Endpoints direkt mit requests ansprechen können.

Ziel: Selenium nur für Login, dann REST-Calls mit Session-Cookies
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
from selenium.webdriver.chrome.options import Options

BASE_DIR = "/opt/greiner-portal"
CREDENTIALS_PATH = f"{BASE_DIR}/config/credentials.json"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_api_test.log"


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


def get_session_cookies_via_selenium(credentials, headless=True):
    """Login via Selenium und extrahiere Session-Cookies"""
    log("=== PHASE 1: Selenium Login ===")

    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    if headless:
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
        time.sleep(8)

        # Warte auf Frame
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
        )
        log("In frameHub - Session aufgebaut")

        # Extrahiere ALLE Cookies
        selenium_cookies = driver.get_cookies()
        log(f"Gefundene Cookies: {len(selenium_cookies)}")

        for cookie in selenium_cookies:
            log(f"  - {cookie['name']}: {cookie['value'][:30]}...")

        # Aktuelle URL
        current_url = driver.current_url
        log(f"Aktuelle URL: {current_url}")

        return selenium_cookies, current_url

    finally:
        driver.quit()


def test_endpoints_with_cookies(cookies, base_url, vin):
    """Teste Endpoints mit den Session-Cookies"""
    log("\n=== PHASE 2: Direct API Calls ===")

    # Baue requests Session mit Cookies
    session = requests.Session()

    for cookie in cookies:
        session.cookies.set(
            cookie['name'],
            cookie['value'],
            domain=cookie.get('domain', '.mpsa.com'),
            path=cookie.get('path', '/')
        )

    # Standard-Headers wie ein Browser
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    })

    # Endpoints zum Testen
    test_endpoints = [
        # Basis-Seiten
        ('GET', 'https://servicebox.mpsa.com/socle/', 'Startseite'),
        ('GET', 'https://servicebox.mpsa.com/do/aide', 'Hilfe'),

        # VIN-Suche (POST mit Formular)
        ('POST', 'https://servicebox.mpsa.com/do/ok', 'VIN-Suche', {
            'shortvin': vin,
            'VIN_OK_BUTTON': 'OK'
        }),

        # Tech-Doc Endpoints
        ('GET', 'https://servicebox.mpsa.com/docapvprovl/initNav.do', 'Neue Auswahl'),
        ('GET', f'https://servicebox.mpsa.com/docapvprovl/caracteristique.do?vin={vin}', 'Charakteristik'),
        ('GET', 'https://servicebox.mpsa.com/docapvprovl/typdoc.do?doc=17', 'Zubehör'),

        # Wartungsplan-spezifische Endpoints (vermutlich)
        ('GET', 'https://servicebox.mpsa.com/docapvprovl/typdoc.do?doc=1', 'Wartungsplan?'),
        ('GET', 'https://servicebox.mpsa.com/docapvprovl/typdoc.do?doc=2', 'Inspektion?'),
        ('GET', 'https://servicebox.mpsa.com/docapvprovl/typdoc.do?doc=3', 'Service?'),
    ]

    results = []

    for test in test_endpoints:
        method = test[0]
        url = test[1]
        name = test[2]
        data = test[3] if len(test) > 3 else None

        log(f"\n--- Test: {name} ---")
        log(f"  {method} {url}")

        try:
            if method == 'GET':
                resp = session.get(url, timeout=30, allow_redirects=True)
            else:
                resp = session.post(url, data=data, timeout=30, allow_redirects=True)

            log(f"  Status: {resp.status_code}")
            log(f"  Content-Type: {resp.headers.get('Content-Type', 'unknown')}")
            log(f"  Content-Length: {len(resp.content)} bytes")
            log(f"  Final URL: {resp.url}")

            # Prüfe auf Erfolg
            success = resp.status_code == 200 and len(resp.content) > 500

            # Suche nach bekannten Strings
            content_lower = resp.text.lower() if resp.status_code == 200 else ''
            has_vin = vin.lower() in content_lower
            has_error = 'error' in content_lower or 'fehler' in content_lower
            has_login = 'login' in content_lower or 'anmelden' in content_lower

            log(f"  VIN gefunden: {has_vin}")
            log(f"  Fehler-Text: {has_error}")
            log(f"  Login-Redirect: {has_login}")

            results.append({
                'name': name,
                'url': url,
                'method': method,
                'status': resp.status_code,
                'success': success and not has_login,
                'has_vin': has_vin,
                'size': len(resp.content)
            })

            # Bei Erfolg: Speichere Response
            if success and not has_login:
                filename = f"/opt/greiner-portal/logs/servicebox_api_{name.replace(' ', '_').replace('?', '')}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(resp.text)
                log(f"  Gespeichert: {filename}")

        except Exception as e:
            log(f"  FEHLER: {e}")
            results.append({
                'name': name,
                'url': url,
                'method': method,
                'status': 0,
                'success': False,
                'error': str(e)
            })

    return results


def main():
    log("\n" + "=" * 70)
    log("SERVICEBOX API ENDPOINT TEST")
    log("Ziel: Selenium nur für Login, dann direkte API-Calls")
    log("=" * 70)

    test_vin = "W0L0SDL68A4087224"

    try:
        credentials = load_credentials()

        # Phase 1: Login via Selenium
        cookies, current_url = get_session_cookies_via_selenium(credentials)

        if not cookies:
            log("FEHLER: Keine Cookies erhalten!")
            return False

        # Phase 2: Teste Endpoints
        results = test_endpoints_with_cookies(cookies, current_url, test_vin)

        # Zusammenfassung
        log("\n" + "=" * 70)
        log("ERGEBNIS")
        log("=" * 70)

        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]

        log(f"Erfolgreich: {len(successful)} / {len(results)}")

        if successful:
            log("\nFunktionierende Endpoints:")
            for r in successful:
                log(f"  {r['method']} {r['name']} ({r['size']} bytes)")

        if failed:
            log("\nFehlgeschlagene Endpoints:")
            for r in failed:
                log(f"  {r['method']} {r['name']} - Status {r.get('status', 'Error')}")

        # Fazit
        log("\n" + "=" * 70)
        if len(successful) > 2:
            log("FAZIT: API-Calls FUNKTIONIEREN mit Session-Cookies!")
            log("       Selenium nur für Login nötig, dann requests nutzen.")
        else:
            log("FAZIT: Session-Cookies reichen nicht aus.")
            log("       Selenium für alle Requests erforderlich.")
        log("=" * 70)

        return len(successful) > 2

    except Exception as e:
        log(f"FEHLER: {e}")
        import traceback
        log(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
