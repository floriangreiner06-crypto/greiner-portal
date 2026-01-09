#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ServiceBox Bestellungen Network Analyzer
=========================================
Analysiert die Network-Requests beim Laden der Bestellhistorie
um API-Endpoints zu finden, die wir direkt nutzen können.
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
OUTPUT_DIR = f"{BASE_DIR}/logs/servicebox_network"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_bestellungen_network.log"

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


def setup_driver_with_network_logging(headless=True):
    """Chrome mit Performance-Logging für Network-Analyse"""
    log("🔧 Initialisiere Chrome mit Network-Logging...")

    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=de-DE')

    # Aktiviere Performance-Logging für Network-Requests
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(120)
    
    log("✅ Chrome mit Network-Logging bereit")
    return driver


def extract_network_requests(driver):
    """Extrahiere alle Network-Requests aus Chrome Performance-Logs"""
    try:
        logs = driver.get_log('performance')
    except Exception as e:
        log(f"⚠️  Fehler beim Lesen der Logs: {e}")
        return [], []

    requests = []
    responses = []

    for entry in logs:
        try:
            message = json.loads(entry['message'])['message']
            method = message.get('method', '')

            if method == 'Network.requestWillBeSent':
                req = message.get('params', {}).get('request', {})
                url = req.get('url', '')
                if url:
                    requests.append({
                        'url': url,
                        'method': req.get('method', 'GET'),
                        'headers': req.get('headers', {}),
                        'postData': req.get('postData', ''),
                        'timestamp': entry.get('timestamp', 0)
                    })

            elif method == 'Network.responseReceived':
                resp = message.get('params', {}).get('response', {})
                url = resp.get('url', '')
                if url:
                    responses.append({
                        'url': url,
                        'status': resp.get('status', 0),
                        'mimeType': resp.get('mimeType', ''),
                        'headers': resp.get('headers', {}),
                        'timestamp': entry.get('timestamp', 0)
                    })

        except Exception as e:
            continue

    return requests, responses


def analyze_bestellungen_requests(requests, responses):
    """Analysiere Requests speziell für Bestellungen"""
    log("\n" + "="*80)
    log("📊 ANALYSE DER BESTELLUNGEN-REQUESTS")
    log("="*80)

    # Interessante Patterns für Bestellungen
    interesting_patterns = [
        'panier', 'commande', 'bestellung', 'order', 'historie',
        'ajax', 'json', 'api', 'rest', '.do', 'liste', 'detail'
    ]

    bestellungen_requests = []
    api_requests = []
    ajax_requests = []

    for req in requests:
        url = req['url'].lower()
        
        # Bestellungen-relevante Requests
        if any(pattern in url for pattern in interesting_patterns):
            bestellungen_requests.append(req)
            
            # API/AJAX Requests
            if 'ajax' in url or 'json' in url or 'api' in url or 'rest' in url:
                api_requests.append(req)
            elif req.get('headers', {}).get('x-requested-with', '').lower() == 'xmlhttprequest':
                ajax_requests.append(req)

    log(f"\n📦 Bestellungen-relevante Requests: {len(bestellungen_requests)}")
    log(f"🔌 API/AJAX Requests: {len(api_requests)}")
    log(f"📡 AJAX (X-Requested-With): {len(ajax_requests)}")

    # Detaillierte Analyse
    if bestellungen_requests:
        log("\n" + "-"*80)
        log("🔍 DETAILLIERTE ANALYSE")
        log("-"*80)

        for req in bestellungen_requests[:20]:  # Erste 20
            url = req['url']
            # Entferne Credentials aus URL
            if '@' in url:
                url = url.split('@')[-1]
            
            log(f"\n  {req['method']} {url[:120]}")
            
            # Wichtige Headers
            headers = req.get('headers', {})
            important_headers = ['content-type', 'x-requested-with', 'referer', 'accept']
            
            for key, value in headers.items():
                if key.lower() in important_headers:
                    log(f"    {key}: {value[:80]}")
            
            # POST Data
            if req.get('postData'):
                post_data = req['postData'][:200]
                log(f"    POST Data: {post_data}")

    # API-Endpoints extrahieren
    if api_requests or ajax_requests:
        log("\n" + "-"*80)
        log("🎯 POTENTIELLE API-ENDPOINTS")
        log("-"*80)
        
        all_api = api_requests + ajax_requests
        unique_endpoints = {}
        
        for req in all_api:
            url = req['url']
            if '@' in url:
                url = url.split('@')[-1]
            
            # Extrahiere Basis-URL
            if '?' in url:
                base = url.split('?')[0]
            else:
                base = url
            
            if base not in unique_endpoints:
                unique_endpoints[base] = {
                    'method': req['method'],
                    'full_url': url,
                    'headers': req.get('headers', {}),
                    'postData': req.get('postData', '')
                }
        
        for endpoint, info in sorted(unique_endpoints.items()):
            log(f"\n  {info['method']} {endpoint}")
            if info.get('postData'):
                log(f"    POST: {info['postData'][:100]}")

    return bestellungen_requests, api_requests, ajax_requests


def main():
    log("\n" + "="*80)
    log("🚀 SERVICEBOX BESTELLUNGEN NETWORK ANALYZER")
    log("="*80)

    driver = None

    try:
        credentials = load_credentials()
        driver = setup_driver_with_network_logging(headless=True)

        username = credentials['username']
        password = credentials['password']
        base_url = credentials['portal_url']
        protocol, rest = base_url.split('://', 1)
        auth_url = f"{protocol}://{username}:{password}@{rest}"

        # Phase 1: Login
        log("\n" + "="*80)
        log("🔐 PHASE 1: LOGIN")
        log("="*80)
        driver.get(auth_url)
        time.sleep(8)

        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
        )
        log("✅ In frameHub gewechselt")
        time.sleep(3)

        # Phase 2: Navigation zu Warenkorb
        log("\n" + "="*80)
        log("🛒 PHASE 2: NAVIGATION ZU WARENKORB")
        log("="*80)
        
        lokale = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "LOKALE VERWALTUNG"))
        )
        ActionChains(driver).move_to_element(lokale).perform()
        time.sleep(2)

        driver.execute_script("goTo('/panier/')")
        time.sleep(5)
        log("✅ Warenkorb geladen")

        # Phase 3: Navigation zur Historie
        log("\n" + "="*80)
        log("📋 PHASE 3: NAVIGATION ZUR HISTORIE")
        log("="*80)
        
        historie_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Historie der Bestellungen"))
        )
        historie_link.click()
        time.sleep(8)  # Warte auf vollständiges Laden
        
        log("✅ Historie-Seite geladen")

        # Phase 4: Pagination testen (um mehr Requests zu sehen)
        log("\n" + "="*80)
        log("📄 PHASE 4: PAGINATION TEST")
        log("="*80)
        
        try:
            # Versuche "Weiter"-Button zu klicken
            next_button = driver.find_element(By.CSS_SELECTOR, "input.bt-arrow-right")
            classes = next_button.get_attribute('class') or ''
            if 'inactive' not in classes:
                log("🖱️  Klicke 'Weiter'...")
                next_button.click()
                time.sleep(5)
                log("✅ Seite 2 geladen")
        except Exception as e:
            log(f"⚠️  Pagination nicht möglich: {e}")

        # Phase 5: Network-Requests extrahieren
        log("\n" + "="*80)
        log("📡 PHASE 5: NETWORK-REQUESTS EXTRAHIEREN")
        log("="*80)
        
        requests, responses = extract_network_requests(driver)
        log(f"✅ {len(requests)} Requests gefunden")
        log(f"✅ {len(responses)} Responses gefunden")

        # Phase 6: Analyse
        bestellungen_reqs, api_reqs, ajax_reqs = analyze_bestellungen_requests(requests, responses)

        # Phase 7: Speichere Ergebnisse
        log("\n" + "="*80)
        log("💾 PHASE 7: ERGEBNISSE SPEICHERN")
        log("="*80)
        
        output_file = os.path.join(OUTPUT_DIR, f"bestellungen_network_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # Bereinige URLs von Credentials
        clean_requests = []
        for req in requests:
            clean_req = req.copy()
            url = clean_req.get('url', '')
            if '@' in url:
                parts = url.split('@')
                if len(parts) > 1:
                    clean_req['url'] = parts[0].split('://')[0] + '://' + parts[-1]
            clean_requests.append(clean_req)

        result = {
            'timestamp': datetime.now().isoformat(),
            'total_requests': len(requests),
            'total_responses': len(responses),
            'bestellungen_requests': len(bestellungen_reqs),
            'api_requests': len(api_reqs),
            'ajax_requests': len(ajax_reqs),
            'all_requests': clean_requests[:200],  # Erste 200
            'bestellungen_requests_detail': bestellungen_reqs[:50],
            'api_requests_detail': api_reqs,
            'ajax_requests_detail': ajax_reqs
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        log(f"✅ Gespeichert: {output_file}")

        # Zusammenfassung
        log("\n" + "="*80)
        log("📊 ZUSAMMENFASSUNG")
        log("="*80)
        log(f"Gesamt Requests: {len(requests)}")
        log(f"Bestellungen-relevant: {len(bestellungen_reqs)}")
        log(f"API/AJAX Requests: {len(api_reqs) + len(ajax_reqs)}")
        
        if api_reqs or ajax_reqs:
            log("\n✅ POTENTIELLE API-ENDPOINTS GEFUNDEN!")
            log("   Siehe Details oben und in der JSON-Datei.")
        else:
            log("\n⚠️  KEINE API-ENDPOINTS GEFUNDEN")
            log("   ServiceBox verwendet wahrscheinlich nur HTML-Seiten.")

        return True

    except Exception as e:
        log(f"\n❌ FEHLER: {e}")
        import traceback
        log(traceback.format_exc())
        return False

    finally:
        if driver:
            log("\n🔚 Schließe Browser...")
            driver.quit()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
