#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Service Box - Hybrid API Client
===========================================
Verwendet Selenium nur für Login, dann Requests mit korrekten Session-Cookies
und Form-Parametern.

Die VIN wird aufgesplittet wie im JavaScript:
- wmi = VIN[0:3]  (World Manufacturer Identifier)
- vds = VIN[3:9]  (Vehicle Descriptor Section)
- vis = VIN[9:17] (Vehicle Identifier Section)
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
LOG_FILE = f"{BASE_DIR}/logs/servicebox_hybrid_api.log"
OUTPUT_DIR = f"{BASE_DIR}/logs/servicebox_hybrid"

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


def split_vin(vin):
    """Splittet VIN wie im Servicebox-JavaScript"""
    return {
        'jvin': vin,              # Volle VIN
        'wmi': vin[0:3],          # World Manufacturer Identifier
        'vds': vin[3:9],          # Vehicle Descriptor Section
        'vis': vin[9:17],         # Vehicle Identifier Section
        'shortvin': vin,          # Eingabefeld
        'rechImmat': 'false'      # Keine Kennzeichen-Suche
    }


def get_authenticated_session(credentials, headless=True):
    """Login via Selenium, extrahiere Cookies UND versteckte Felder"""
    log("=== SELENIUM LOGIN ===")

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

        # Wechsle in Frame
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
        )
        log("In frameHub")
        time.sleep(3)

        # Extrahiere versteckte Felder
        hidden_fields = {}
        try:
            brand_id = driver.find_element(By.ID, "brandIdHub").get_attribute('value')
            hidden_fields['brandId'] = brand_id
            log(f"  brandId: {brand_id}")
        except:
            pass

        try:
            rrdi = driver.find_element(By.ID, "rrdiIdHub").get_attribute('value')
            hidden_fields['rrdi'] = rrdi
            log(f"  rrdi: {rrdi}")
        except:
            pass

        # Extrahiere Cookies
        selenium_cookies = driver.get_cookies()
        log(f"Cookies: {len(selenium_cookies)}")

        # Erstelle requests Session
        session = requests.Session()

        for cookie in selenium_cookies:
            session.cookies.set(
                cookie['name'],
                cookie['value'],
                domain=cookie.get('domain', 'servicebox.mpsa.com').lstrip('.'),
                path=cookie.get('path', '/')
            )

        # Setze Standard-Headers wie ein Browser
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        # Aktuelle URL für Referer
        current_url = driver.current_url.replace(f'{username}:{password}@', '')

        return session, hidden_fields, current_url

    finally:
        driver.quit()


def search_vin_via_api(session, vin, hidden_fields, referer):
    """VIN-Suche via direktem POST Request"""
    log(f"\n=== VIN-SUCHE VIA API: {vin} ===")

    # VIN aufsplitten
    vin_parts = split_vin(vin)
    log(f"  WMI: {vin_parts['wmi']}")
    log(f"  VDS: {vin_parts['vds']}")
    log(f"  VIS: {vin_parts['vis']}")

    # Baue Form-Daten wie das echte JavaScript
    form_data = {
        'shortvin': vin,
        'jvin': vin,
        'wmi': vin_parts['wmi'],
        'vds': vin_parts['vds'],
        'vis': vin_parts['vis'],
        'rechImmat': 'false',
        'VIN_OK_BUTTON.x': '10',  # Image-Submit koordinaten
        'VIN_OK_BUTTON.y': '10',
    }

    # Setze korrekte Headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://servicebox.mpsa.com',
        'Referer': 'https://servicebox.mpsa.com/docapvpr/',
    }

    url = 'https://servicebox.mpsa.com/do/ok'

    log(f"POST {url}")
    log(f"  Form-Daten: {form_data}")

    try:
        resp = session.post(url, data=form_data, headers=headers, timeout=30, allow_redirects=True)

        log(f"  Status: {resp.status_code}")
        log(f"  Content-Length: {len(resp.content)}")
        log(f"  Final URL: {resp.url}")

        # Prüfe ob VIN in Response
        if vin in resp.text:
            log("  VIN in Response gefunden!")
        else:
            log("  VIN NICHT in Response")

        # Prüfe auf Login-Seite
        if 'login' in resp.text.lower() and 'password' in resp.text.lower():
            log("  WARNUNG: Login-Seite zurückgegeben")
            return None

        # Speichere Response
        output_file = os.path.join(OUTPUT_DIR, f"vin_search_{vin}.html")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(resp.text)
        log(f"  Gespeichert: {output_file}")

        return resp

    except Exception as e:
        log(f"  FEHLER: {e}")
        return None


def try_ajax_endpoints(session, hidden_fields):
    """Teste AJAX-Endpoints mit X-Requested-With Header"""
    log("\n=== TESTE AJAX ENDPOINTS ===")

    ajax_headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'https://servicebox.mpsa.com/socle/?start=true',
    }

    # RRDI aus Login
    rrdi = hidden_fields.get('rrdi', 'DE08250')

    endpoints = [
        ('https://servicebox.mpsa.com/do/WebCache', {'rrdi': rrdi}),
        ('https://servicebox.mpsa.com/do/AjaxHeaderInfoAction', {'rrdi': rrdi, 'multipleContacts': '[]'}),
    ]

    for url, data in endpoints:
        log(f"\nPOST {url}")
        try:
            resp = session.post(url, data=data, headers=ajax_headers, timeout=30)
            log(f"  Status: {resp.status_code}")
            log(f"  Content-Type: {resp.headers.get('Content-Type', 'unknown')}")

            if resp.status_code == 200:
                content = resp.text[:200]
                log(f"  Response: {content}...")

                # Speichere erfolgreiche Responses
                if 'error' not in resp.text.lower():
                    endpoint_name = url.split('/')[-1]
                    output_file = os.path.join(OUTPUT_DIR, f"ajax_{endpoint_name}.json")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(resp.text)
                    log(f"  Gespeichert: {output_file}")

        except Exception as e:
            log(f"  FEHLER: {e}")


def try_docapvpr_navigation(session, vin, hidden_fields):
    """Versuche direkte Navigation zu docapvpr mit VIN"""
    log("\n=== DOCAPVPR NAVIGATION ===")

    # Erster Schritt: Navigiere zu docapvpr
    log("Schritt 1: POST /docapvpr/")

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://servicebox.mpsa.com',
        'Referer': 'https://servicebox.mpsa.com/socle/?start=true',
    }

    try:
        resp = session.post(
            'https://servicebox.mpsa.com/docapvpr/',
            data={'tabControlID': '', 'jbnContext': 'true'},
            headers=headers,
            timeout=30
        )

        log(f"  Status: {resp.status_code}")
        log(f"  Size: {len(resp.content)} bytes")

        # Wenn erfolgreich, versuche VIN-Suche in diesem Kontext
        if resp.status_code == 200 and len(resp.content) > 10000:
            log("\nSchritt 2: VIN-Suche in docapvpr Kontext")

            # Aktualisiere Referer
            headers['Referer'] = 'https://servicebox.mpsa.com/docapvpr/'

            vin_parts = split_vin(vin)
            form_data = {
                'shortvin': vin,
                'jvin': vin,
                'wmi': vin_parts['wmi'],
                'vds': vin_parts['vds'],
                'vis': vin_parts['vis'],
                'rechImmat': 'false',
            }

            resp2 = session.post(
                'https://servicebox.mpsa.com/do/ok',
                data=form_data,
                headers=headers,
                timeout=30,
                allow_redirects=True
            )

            log(f"  Status: {resp2.status_code}")
            log(f"  Size: {len(resp2.content)} bytes")
            log(f"  VIN in Response: {vin in resp2.text}")

            output_file = os.path.join(OUTPUT_DIR, f"docapvpr_vin_{vin}.html")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(resp2.text)
            log(f"  Gespeichert: {output_file}")

            return resp2

    except Exception as e:
        log(f"  FEHLER: {e}")

    return None


def main():
    log("\n" + "=" * 70)
    log("SERVICEBOX HYBRID API TEST")
    log("Selenium für Login, dann Requests für API-Calls")
    log("=" * 70)

    test_vin = "W0L0SDL68A4087224"

    try:
        credentials = load_credentials()

        # 1. Authentifizierte Session holen
        session, hidden_fields, referer = get_authenticated_session(credentials)

        log(f"\nHidden Fields: {hidden_fields}")

        # 2. AJAX-Endpoints testen
        try_ajax_endpoints(session, hidden_fields)

        # 3. VIN-Suche via API
        result = search_vin_via_api(session, test_vin, hidden_fields, referer)

        # 4. Alternative: docapvpr Navigation
        result2 = try_docapvpr_navigation(session, test_vin, hidden_fields)

        # Zusammenfassung
        log("\n" + "=" * 70)
        log("ZUSAMMENFASSUNG")
        log("=" * 70)

        success = False

        if result and result.status_code == 200 and test_vin in result.text:
            log("VIN-Suche via /do/ok: ERFOLGREICH")
            success = True
        else:
            log("VIN-Suche via /do/ok: Fehlgeschlagen")

        if result2 and result2.status_code == 200 and test_vin in result2.text:
            log("docapvpr Navigation: ERFOLGREICH")
            success = True
        else:
            log("docapvpr Navigation: Fehlgeschlagen")

        log("=" * 70)

        return success

    except Exception as e:
        log(f"FEHLER: {e}")
        import traceback
        log(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
