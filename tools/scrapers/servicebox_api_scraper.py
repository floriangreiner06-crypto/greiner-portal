#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis ServiceBox API Scraper - TAG 173
============================================
Verwendet API-Endpoint statt Selenium für bessere Performance.
- Selenium nur für Login (Session-Cookies)
- Requests für API-Calls (viel schneller)
- BeautifulSoup für HTML-Parsing
"""

import os
import sys
import time
import json
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

BASE_DIR = "/opt/greiner-portal"
CREDENTIALS_PATH = f"{BASE_DIR}/config/credentials.json"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_api_scraper.log"
OUTPUT_FILE = f"{BASE_DIR}/logs/servicebox_bestellungen_details_final.json"

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_msg + '\n')


def load_credentials():
    with open(CREDENTIALS_PATH, 'r') as f:
        creds = json.load(f)
    return creds['external_systems']['stellantis_servicebox']


def get_session_cookies(credentials):
    """Login via Selenium und extrahiere Session-Cookies"""
    log("\n🔐 LOGIN VIA SELENIUM")
    log("="*80)

    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=de-DE')

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)

    try:
        username = credentials['username']
        password = credentials['password']
        base_url = credentials['portal_url']
        protocol, rest = base_url.split('://', 1)
        auth_url = f"{protocol}://{username}:{password}@{rest}"

        log(f"Login zu {base_url}...")
        driver.get(auth_url)
        time.sleep(8)

        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
        )
        log("✅ In frameHub gewechselt")
        time.sleep(3)

        # Extrahiere Cookies
        selenium_cookies = driver.get_cookies()
        log(f"✅ {len(selenium_cookies)} Cookies erhalten")

        # Extrahiere RRDI (für API-Calls)
        rrdi = None
        try:
            rrdi_element = driver.find_element(By.ID, "rrdiIdHub")
            rrdi = rrdi_element.get_attribute('value')
            log(f"✅ RRDI: {rrdi}")
        except:
            log("⚠️  RRDI nicht gefunden, verwende Standard")
            rrdi = 'DE08250'

        return selenium_cookies, rrdi

    finally:
        driver.quit()


def create_requests_session(cookies):
    """Erstelle requests Session mit Cookies"""
    session = requests.Session()

    for cookie in cookies:
        session.cookies.set(
            cookie['name'],
            cookie['value'],
            domain=cookie.get('domain', 'servicebox.mpsa.com').lstrip('.'),
            path=cookie.get('path', '/')
        )

    # Browser-Headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
        'Referer': 'https://servicebox.mpsa.com/panier/',
    })

    return session


def extract_bestellungen_from_html(html):
    """Extrahiere Bestellungen aus HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    bestellungen = []

    # Pattern für Bestellnummern
    bestellnummer_pattern = re.compile(r'1[A-Z]{3}[A-Z0-9]{5}')

    # Methode 1: Links mit commandeDetailRepAll.do
    links = soup.find_all('a', href=re.compile(r'commandeDetailRepAll\.do'))
    
    for link in links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Bestellnummer aus Link-Text oder href extrahieren
        match = bestellnummer_pattern.search(text) or bestellnummer_pattern.search(href)
        if match:
            bestellnummer = match.group(0)
            
            # URL konstruieren
            if href.startswith('http'):
                url = href
            elif href.startswith('/'):
                url = f"https://servicebox.mpsa.com{href}"
            else:
                url = f"https://servicebox.mpsa.com/panier/{href}"
            
            if not any(b['nummer'] == bestellnummer for b in bestellungen):
                bestellungen.append({
                    'nummer': bestellnummer,
                    'url': url
                })

    # Methode 2: Fallback - Regex auf gesamter Seite
    if len(bestellungen) == 0:
        all_matches = bestellnummer_pattern.findall(html)
        unique_numbers = list(set(all_matches))
        
        for nummer in unique_numbers:
            # Versuche URL zu finden
            link = soup.find('a', href=re.compile(nummer))
            if link:
                href = link.get('href', '')
                if href.startswith('http'):
                    url = href
                elif href.startswith('/'):
                    url = f"https://servicebox.mpsa.com{href}"
                else:
                    url = f"https://servicebox.mpsa.com/panier/{href}"
            else:
                url = f"https://servicebox.mpsa.com/panier/commandeDetailRepAll.do?commande={nummer}"
            
            bestellungen.append({
                'nummer': nummer,
                'url': url
            })

    return bestellungen


def get_pagination_info(html):
    """Extrahiere Pagination-Informationen aus HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Suche nach Pagination-Text (z.B. "1 - 10 / 50" oder "Anzahl der präsentierten Elemente 1 - 10 / 50")
    pagination_text = soup.find('td', class_='text', string=re.compile(r'\d+\s*-\s*\d+\s*/\s*\d+'))
    
    if not pagination_text:
        # Alternative: Suche nach Text mit "Anzahl der präsentierten Elemente"
        pagination_text = soup.find('td', string=re.compile(r'Anzahl.*?\d+\s*-\s*\d+\s*/\s*\d+'))
    
    if pagination_text:
        text = pagination_text.get_text(strip=True)
        # "1 - 10 / 50" oder "Anzahl der präsentierten Elemente 1 - 10 / 50" -> current_end=10, total=50
        match = re.search(r'(\d+)\s*-\s*(\d+)\s*/\s*(\d+)', text)
        if match:
            current_start = int(match.group(1))
            current_end = int(match.group(2))
            total = int(match.group(3))
            return {
                'current_start': current_start,
                'current_end': current_end,
                'total': total,
                'has_next': current_end < total,
                'per_page': current_end - current_start + 1
            }
    
    # Fallback: Prüfe ob "Weiter"-Button aktiv ist
    next_button = soup.find('input', class_=re.compile(r'bt-arrow-right'))
    if next_button:
        classes = next_button.get('class', [])
        if isinstance(classes, list):
            has_next = 'inactive' not in classes
        else:
            has_next = 'inactive' not in str(classes)
        return {
            'has_next': has_next,
            'total': None
        }
    
    return {'has_next': False, 'total': None}


def fetch_bestellungen_page(session, rrdi, page=0):
    """Hole eine Seite der Bestellliste"""
    # TAG 173: Pagination funktioniert über sort.do mit pagerPage Parameter
    # Seite 0 = erste Seite (kein Parameter)
    # Seite 1+ = pagerPage Parameter (0-basiert im JavaScript, aber 1-basiert im URL)
    if page == 0:
        url = 'https://servicebox.mpsa.com/panier/listCommandesRepAll.do'
        params = {
            'leftMenu': 'lcra',
            'rrdListStr': rrdi
        }
    else:
        # Ab Seite 2: sort.do mit pagerPage (1-basiert)
        url = 'https://servicebox.mpsa.com/panier/sort.do'
        params = {
            'layoutCollection': '0',
            'layoutCollectionProperty': '',
            'layoutCollectionState': '0',
            'pagerPage': page - 1  # JavaScript ist 0-basiert, aber URL verwendet 1-basiert
        }
    
    log(f"📄 Lade Seite {page + 1}...")
    
    try:
        resp = session.get(url, params=params, timeout=30)
        
        if resp.status_code != 200:
            log(f"⚠️  Status {resp.status_code}")
            return None, None
        
        bestellungen = extract_bestellungen_from_html(resp.text)
        pagination = get_pagination_info(resp.text)
        
        log(f"   ✅ {len(bestellungen)} Bestellungen gefunden")
        
        return bestellungen, pagination
        
    except Exception as e:
        log(f"   ❌ Fehler: {e}")
        return None, None


def fetch_all_bestellungen(session, rrdi, max_pages=500):
    """Hole alle Bestellungen über alle Seiten"""
    log("\n📋 HOLE ALLE BESTELLUNGEN")
    log("="*80)
    
    all_bestellungen = []
    page = 0
    seen_bestellnummern = set()
    total_expected = None
    
    while page < max_pages:
        bestellungen, pagination = fetch_bestellungen_page(session, rrdi, page)
        
        if not bestellungen:
            log(f"⚠️  Keine Bestellungen auf Seite {page + 1}")
            break
        
        # Setze erwartete Gesamtzahl aus erster Seite
        if page == 0 and pagination and pagination.get('total'):
            total_expected = pagination['total']
            log(f"   ℹ️  Erwartete Gesamtzahl: {total_expected} Bestellungen")
        
        # Füge neue Bestellungen hinzu (dedupliziert)
        new_count = 0
        for b in bestellungen:
            if b['nummer'] not in seen_bestellnummern:
                seen_bestellnummern.add(b['nummer'])
                all_bestellungen.append(b)
                new_count += 1
                if len(all_bestellungen) <= 20:  # Nur erste 20 loggen
                    log(f"   ✅ {b['nummer']}")
        
        if new_count == 0:
            log(f"   ⚠️  Keine neuen Bestellungen auf Seite {page + 1} (alle bereits vorhanden)")
            # Wenn keine neuen Bestellungen UND wir haben die erwartete Anzahl erreicht
            if total_expected and len(all_bestellungen) >= total_expected:
                log(f"   ✅ Erwartete Anzahl ({total_expected}) erreicht")
                break
            # Oder nach 10 Seiten ohne neue = Problem
            if page > 10:
                log(f"   ⚠️  Möglicherweise Pagination-Problem, stoppe")
                break
        
        # Prüfe ob es weitere Seiten gibt
        if pagination:
            if pagination.get('total'):
                log(f"   ℹ️  Seite {page + 1}: {pagination['current_end']}/{pagination['total']} Bestellungen (aktuell: {len(all_bestellungen)} gesammelt)")
            
            if not pagination.get('has_next', False):
                log(f"   ℹ️  Letzte Seite erreicht (Seite {page + 1})")
                break
        
        # Prüfe ob wir die erwartete Anzahl erreicht haben
        if total_expected and len(all_bestellungen) >= total_expected:
            log(f"   ✅ Erwartete Anzahl ({total_expected}) erreicht")
            break
        
        page += 1
        time.sleep(0.5)  # Kurze Pause zwischen Requests
    
    log(f"\n📊 GESAMT: {len(all_bestellungen)} eindeutige Bestellungen auf {page + 1} Seiten")
    if total_expected:
        log(f"   Erwartet waren: {total_expected} Bestellungen")
    
    return all_bestellungen


def extract_bestellung_details(session, bestellung_info):
    """Extrahiere Details für eine Bestellung (aus HTML)"""
    bestellnummer = bestellung_info['nummer']
    detail_url = bestellung_info.get('url')
    
    log(f"   🔍 Details für {bestellnummer}...")
    
    details = {
        'bestellnummer': bestellnummer,
        'url': detail_url,
        'absender': {},
        'empfaenger': {},
        'historie': {},
        'positionen': [],
        'summen': {},
        'kommentare': {}
    }
    
    if not detail_url:
        log(f"      ⚠️  Keine URL vorhanden")
        return details
    
    try:
        resp = session.get(detail_url, timeout=30)
        
        if resp.status_code != 200:
            log(f"      ⚠️  Status {resp.status_code}")
            return details
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        page_text = resp.text
        
        # Absender extrahieren
        absender_code_match = re.search(r'Code Vertragspartner\s*:\s*</td>\s*<td[^>]*>\s*([A-Z0-9]+)', page_text)
        if absender_code_match:
            details['absender']['code'] = absender_code_match.group(1)
        
        absender_name_match = re.search(r'Name\s*:\s*</td>\s*<td[^>]*>\s*([^<]+)', page_text)
        if absender_name_match:
            details['absender']['name'] = absender_name_match.group(1).strip()
        
        # Empfänger extrahieren
        empf_section = re.search(r'Empfänger.*?Code Vertragspartner\s*:\s*</td>\s*<td[^>]*>\s*([A-Z0-9]+)', page_text, re.DOTALL)
        if empf_section:
            details['empfaenger']['code'] = empf_section.group(1)
        
        # Bestelldatum
        datum_match = re.search(r'Bestelldatum\s*:\s*</td>\s*<td[^>]*>\s*(\d{2}\.\d{2}\.\d{2},\s*\d{2}:\d{2})', page_text)
        if datum_match:
            details['historie']['bestelldatum'] = datum_match.group(1)
        
        # Positionen (vereinfacht - kann erweitert werden)
        positionen_links = soup.find_all('a', href=re.compile(r'teilenummer|part'))
        # TODO: Detaillierte Positionen-Extraktion
        
        # Kommentare & Parsed-Daten (wie im alten Scraper)
        kommentar_match = re.search(r'Kommentar[^:]*:\s*</td>\s*<td[^>]*>\s*([^<]+)', page_text, re.DOTALL)
        if kommentar_match:
            kommentar = kommentar_match.group(1).strip()
            details['kommentare']['werkstatt'] = kommentar
            
            # Parse VIN, Kundennummer, Werkstattauftrag
            vin_match = re.search(r'VIN[:\s]+([A-Z0-9]{17})', kommentar, re.IGNORECASE)
            if vin_match:
                details['parsed'] = {'vin': vin_match.group(1)}
            
            kunde_match = re.search(r'Kd\.?\s*Nr\.?[:\s]+(\d+)', kommentar, re.IGNORECASE)
            if kunde_match:
                if 'parsed' not in details:
                    details['parsed'] = {}
                details['parsed']['kundennummer'] = kunde_match.group(1)
        
        log(f"      ✅ Details extrahiert")
        
    except Exception as e:
        log(f"      ⚠️  Fehler: {e}")
    
    return details


def scrape_all_details(session, bestellungen, max_orders=None):
    """Extrahiere Details für alle Bestellungen"""
    log("\n🔍 EXTRAHIERE DETAILS")
    log("="*80)
    
    if max_orders:
        bestellungen = bestellungen[:max_orders]
        log(f"⚠️  TEST-MODUS: Nur erste {max_orders} Bestellungen")
    
    details_list = []
    
    for i, bestellung in enumerate(bestellungen, 1):
        log(f"\n[{i}/{len(bestellungen)}] {bestellung['nummer']}")
        details = extract_bestellung_details(session, bestellung)
        details_list.append(details)
        time.sleep(0.5)  # Kurze Pause zwischen Requests
    
    return details_list


def save_results(details_list):
    """Speichere Ergebnisse"""
    data = {
        'timestamp': datetime.now().isoformat(),
        'anzahl_bestellungen': len(details_list),
        'bestellungen': details_list
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    log(f"\n💾 Ergebnisse gespeichert: {OUTPUT_FILE}")


def main():
    log("\n" + "="*80)
    log("🚀 SERVICEBOX API SCRAPER - TAG 173")
    log("="*80)

    try:
        credentials = load_credentials()
        
        # 1. Login via Selenium (nur für Cookies)
        cookies, rrdi = get_session_cookies(credentials)
        
        if not cookies:
            log("❌ Login fehlgeschlagen!")
            return False
        
        # 2. Erstelle requests Session
        session = create_requests_session(cookies)
        
        # 3. Hole alle Bestellungen
        bestellungen = fetch_all_bestellungen(session, rrdi)
        
        if not bestellungen:
            log("❌ Keine Bestellungen gefunden!")
            return False
        
        # 4. Extrahiere Details
        details = scrape_all_details(session, bestellungen)
        
        # 5. Speichere Ergebnisse
        save_results(details)
        
        log("\n" + "="*80)
        log("✅ API-SCRAPER ERFOLGREICH!")
        log("="*80)
        
        return True
        
    except Exception as e:
        log(f"\n❌ FEHLER: {e}")
        import traceback
        log(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
