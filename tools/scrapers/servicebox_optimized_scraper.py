#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Service Box - Optimierter Wartungsplan Scraper
==========================================================
Hybrid-Ansatz: Selenium nur für Login, dann Requests mit Session-Cookies.

VORTEIL: ~5x schneller als reines Selenium-Scraping

Version: TAG 129 - Optimized
Datum: 2025-12-19
"""

import os
import sys
import time
import json
import pickle
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from pathlib import Path

BASE_DIR = "/opt/greiner-portal"
CREDENTIALS_PATH = f"{BASE_DIR}/config/credentials.json"
SESSION_CACHE_PATH = f"{BASE_DIR}/data/servicebox_session.pkl"
OUTPUT_DIR = f"{BASE_DIR}/logs/servicebox_wartungsplaene"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_optimized.log"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SESSION_CACHE_PATH), exist_ok=True)


def log(message, level="INFO"):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] [{level}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')


def load_credentials():
    with open(CREDENTIALS_PATH, 'r') as f:
        creds = json.load(f)
    return creds['external_systems']['stellantis_servicebox']


def split_vin(vin):
    """Splittet VIN wie im Servicebox-JavaScript"""
    vin = vin.strip().upper()
    return {
        'jvin': vin,
        'wmi': vin[0:3],
        'vds': vin[3:9],
        'vis': vin[9:17],
        'shortvin': vin,
        'rechImmat': 'false'
    }


class ServiceboxSession:
    """Verwaltet die Servicebox-Session mit Caching"""

    def __init__(self, credentials, headless=True):
        self.credentials = credentials
        self.headless = headless
        self.session = None
        self.hidden_fields = {}
        self.last_login = None
        self.session_valid = False

    def _create_selenium_driver(self):
        """Erstellt Chrome-Driver für Login"""
        chrome_options = Options()
        chrome_options.binary_location = '/usr/bin/google-chrome'
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--lang=de-DE')

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)
        return driver

    def _login_via_selenium(self):
        """Login via Selenium, extrahiere Session-Cookies"""
        log("Selenium-Login gestartet...")

        driver = self._create_selenium_driver()

        try:
            username = self.credentials['username']
            password = self.credentials['password']
            base_url = self.credentials['portal_url']

            protocol, rest = base_url.split('://', 1)
            auth_url = f"{protocol}://{username}:{password}@{rest}"

            driver.get(auth_url)
            time.sleep(8)

            # Wechsle in Frame
            WebDriverWait(driver, 15).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
            )
            log("Login erfolgreich - in frameHub")
            time.sleep(3)

            # Extrahiere Hidden Fields
            try:
                self.hidden_fields['brandId'] = driver.find_element(
                    By.ID, "brandIdHub").get_attribute('value')
                self.hidden_fields['rrdi'] = driver.find_element(
                    By.ID, "rrdiIdHub").get_attribute('value')
            except:
                self.hidden_fields = {'brandId': 'OV', 'rrdi': 'DE08250'}

            # Extrahiere Cookies
            selenium_cookies = driver.get_cookies()

            # Erstelle requests Session
            self.session = requests.Session()

            for cookie in selenium_cookies:
                self.session.cookies.set(
                    cookie['name'],
                    cookie['value'],
                    domain=cookie.get('domain', 'servicebox.mpsa.com').lstrip('.'),
                    path=cookie.get('path', '/')
                )

            # Standard-Headers
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            })

            self.last_login = datetime.now()
            self.session_valid = True

            log(f"Session erstellt - Cookies: {len(selenium_cookies)}")

            # Cache speichern
            self._save_session_cache()

            return True

        except Exception as e:
            log(f"Login-Fehler: {e}", "ERROR")
            return False

        finally:
            driver.quit()

    def _save_session_cache(self):
        """Speichert Session für Wiederverwendung"""
        try:
            cache_data = {
                'cookies': dict(self.session.cookies),
                'hidden_fields': self.hidden_fields,
                'last_login': self.last_login.isoformat(),
            }
            with open(SESSION_CACHE_PATH, 'wb') as f:
                pickle.dump(cache_data, f)
            log("Session gecached")
        except Exception as e:
            log(f"Cache-Fehler: {e}", "WARN")

    def _load_session_cache(self):
        """Lädt gecachte Session wenn noch gültig"""
        try:
            if not os.path.exists(SESSION_CACHE_PATH):
                return False

            with open(SESSION_CACHE_PATH, 'rb') as f:
                cache_data = pickle.load(f)

            last_login = datetime.fromisoformat(cache_data['last_login'])

            # Session gilt 30 Minuten
            if datetime.now() - last_login > timedelta(minutes=30):
                log("Gecachte Session abgelaufen")
                return False

            # Stelle Session wieder her
            self.session = requests.Session()
            for name, value in cache_data['cookies'].items():
                self.session.cookies.set(name, value)

            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            })

            self.hidden_fields = cache_data['hidden_fields']
            self.last_login = last_login
            self.session_valid = True

            log("Session aus Cache geladen")
            return True

        except Exception as e:
            log(f"Cache-Ladefehler: {e}", "WARN")
            return False

    def ensure_logged_in(self):
        """Stellt sicher, dass wir eingeloggt sind"""
        # Versuche Cache zu nutzen
        if self._load_session_cache():
            # Validiere Session
            if self._validate_session():
                return True

        # Sonst neu einloggen
        return self._login_via_selenium()

    def _validate_session(self):
        """Prüft ob die Session noch gültig ist"""
        try:
            # Teste einen einfachen AJAX-Endpoint
            resp = self.session.post(
                'https://servicebox.mpsa.com/do/WebCache',
                data={'rrdi': self.hidden_fields.get('rrdi', 'DE08250')},
                headers={'X-Requested-With': 'XMLHttpRequest'},
                timeout=10
            )

            if resp.status_code == 200 and 'physicalSiteId' in resp.text:
                log("Session validiert")
                return True
            else:
                log("Session ungültig", "WARN")
                return False

        except Exception as e:
            log(f"Session-Validierung fehlgeschlagen: {e}", "WARN")
            return False

    def navigate_to_tech_doc(self):
        """Navigiert zur Technischen Dokumentation"""
        log("Navigiere zu Tech-Doc...")

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://servicebox.mpsa.com',
            'Referer': 'https://servicebox.mpsa.com/socle/?start=true',
        }

        resp = self.session.post(
            'https://servicebox.mpsa.com/docapvpr/',
            data={'tabControlID': '', 'jbnContext': 'true'},
            headers=headers,
            timeout=30
        )

        return resp.status_code == 200 and len(resp.content) > 10000

    def search_vin(self, vin):
        """Sucht VIN und gibt Response zurück"""
        log(f"Suche VIN: {vin}")

        vin_parts = split_vin(vin)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://servicebox.mpsa.com',
            'Referer': 'https://servicebox.mpsa.com/docapvpr/',
        }

        form_data = {
            'shortvin': vin,
            'jvin': vin,
            'wmi': vin_parts['wmi'],
            'vds': vin_parts['vds'],
            'vis': vin_parts['vis'],
            'rechImmat': 'false',
        }

        resp = self.session.post(
            'https://servicebox.mpsa.com/do/ok',
            data=form_data,
            headers=headers,
            timeout=30,
            allow_redirects=True
        )

        return resp

    def get_maintenance_info(self, vin):
        """Holt Wartungsinformationen für eine VIN"""
        log(f"Hole Wartungsinfos für: {vin}")

        # Erst zur Tech-Doc navigieren
        if not self.navigate_to_tech_doc():
            log("Tech-Doc Navigation fehlgeschlagen", "ERROR")
            return None

        # VIN suchen
        resp = self.search_vin(vin)

        if resp.status_code != 200:
            log(f"VIN-Suche fehlgeschlagen: {resp.status_code}", "ERROR")
            return None

        # Prüfe ob VIN erkannt wurde
        if vin not in resp.text:
            log("VIN nicht in Response - möglicherweise ungültig", "WARN")

        # Extrahiere Fahrzeuginfos aus HTML
        result = {
            'vin': vin,
            'timestamp': datetime.now().isoformat(),
            'raw_html_size': len(resp.content),
            'vehicle_info': self._extract_vehicle_info(resp.text),
            'maintenance_links': self._extract_maintenance_links(resp.text),
        }

        return result

    def _extract_vehicle_info(self, html):
        """Extrahiert Fahrzeuginfos aus HTML"""
        import re

        info = {}

        # Suche nach bekannten Patterns
        patterns = {
            'model': r'(CORSA|ASTRA|MOKKA|GRANDLAND|CROSSLAND|COMBO|VIVARO|MOVANO)[-\s]?([A-Z])?',
            'engine': r'MOTEUR\s+([A-Z]+)\s+([\d.]+)',
            'transmission': r'(MANUELLE|AUTOMATIQUE)\s+(\d+)\s+RAPPORTS?',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                info[key] = match.group(0)

        return info

    def _extract_maintenance_links(self, html):
        """Extrahiert Wartungsplan-Links"""
        import re

        links = []

        # Suche nach typdoc.do Links
        pattern = r'href="([^"]*typdoc\.do[^"]*)"'
        for match in re.finditer(pattern, html):
            links.append(match.group(1))

        # Suche nach Wartungs-Keywords
        keywords = ['wartung', 'inspektion', 'service', 'maintenance', 'interval']
        pattern = r'href="([^"]*)"[^>]*>([^<]*(?:' + '|'.join(keywords) + r')[^<]*)'

        for match in re.finditer(pattern, html, re.IGNORECASE):
            links.append({'href': match.group(1), 'text': match.group(2).strip()})

        return links


def get_wartungsplan(vin, headless=True):
    """Hauptfunktion: Holt Wartungsplan für eine VIN"""
    log("=" * 60)
    log(f"WARTUNGSPLAN ABRUF - VIN: {vin}")
    log("=" * 60)

    start_time = time.time()

    try:
        credentials = load_credentials()
        sb = ServiceboxSession(credentials, headless=headless)

        # Login
        if not sb.ensure_logged_in():
            return {'success': False, 'error': 'Login fehlgeschlagen'}

        # Wartungsinfos holen
        result = sb.get_maintenance_info(vin)

        if result:
            result['success'] = True
            result['duration_seconds'] = round(time.time() - start_time, 2)

            # Speichere Ergebnis
            output_file = os.path.join(OUTPUT_DIR, f"optimized_{vin}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            log(f"Gespeichert: {output_file}")

        else:
            result = {'success': False, 'error': 'Keine Daten erhalten'}

        log(f"Dauer: {result.get('duration_seconds', 'N/A')}s")
        return result

    except Exception as e:
        log(f"Fehler: {e}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        return {'success': False, 'error': str(e)}


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Servicebox Optimierter Wartungsplan Scraper')
    parser.add_argument('vin', nargs='?', default='W0L0SDL68A4087224',
                       help='VIN des Fahrzeugs')
    parser.add_argument('--visible', action='store_true',
                       help='Browser sichtbar')

    args = parser.parse_args()

    result = get_wartungsplan(args.vin, headless=not args.visible)

    print("\n" + "=" * 60)
    print("ERGEBNIS")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    return 0 if result.get('success') else 1


if __name__ == "__main__":
    sys.exit(main())
