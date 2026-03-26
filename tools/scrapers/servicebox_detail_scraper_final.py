#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Service Box Detail-Scraper - FINAL V2
Mit korrektem Pattern für Teilenummern MIT Zusatztext
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

BASE_DIR = "/opt/greiner-portal"
CREDENTIALS_PATH = f"{BASE_DIR}/config/credentials.json"
SCREENSHOTS_DIR = f"{BASE_DIR}/logs/servicebox_detail_screenshots"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_detail_scraper_final.log"
OUTPUT_FILE = f"{BASE_DIR}/logs/servicebox_bestellungen_details_final.json"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

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

def setup_driver():
    log("🔧 Initialisiere Chrome WebDriver...")
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
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
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{name}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    driver.save_screenshot(filepath)
    log(f"📸 Screenshot: {filename}")

def login_and_navigate(driver, credentials):
    log("\n🔐 LOGIN & NAVIGATION")
    log("="*80)

    username = credentials['username']
    password = credentials['password']
    base_url = credentials['portal_url']
    protocol, rest = base_url.split('://', 1)
    auth_url = f"{protocol}://{username}:{password}@{rest}"

    try:
        driver.get(auth_url)
        time.sleep(8)
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
        )
        log("✅ In frameHub gewechselt")
        time.sleep(3)

        lokale = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "LOKALE VERWALTUNG"))
        )
        ActionChains(driver).move_to_element(lokale).perform()
        time.sleep(2)

        driver.execute_script("goTo('/panier/')")
        time.sleep(5)
        log("✅ Warenkorb geladen")

        historie_link = driver.find_element(By.LINK_TEXT, "Historie der Bestellungen")
        historie_link.click()
        time.sleep(5)

        log("✅ Historie-Seite geladen")
        take_screenshot(driver, "historie_loaded")
        return True

    except Exception as e:
        log(f"❌ Fehler: {e}")
        take_screenshot(driver, "error_navigation")
        return False

def extract_bestellungen_from_current_page(driver):
    """Extrahiert Bestellungen von der aktuellen Seite"""
    try:
        # TAG173: Flexibler Pattern wie im Master-Scraper (1[A-Z]{3}[A-Z0-9]{5})
        import re
        
        # Methode 1: Links mit XPath finden
        links = driver.find_elements(By.XPATH, "//a[contains(@href, 'commandeDetailRepAll.do')]")
        
        bestellungen_mit_urls = []
        bestellnummer_pattern = re.compile(r'1[A-Z]{3}[A-Z0-9]{5}')
        
        # Methode 1a: Aus Link-Text extrahieren
        for link in links:
            text = link.text.strip()
            href = link.get_attribute('href')
            
            # Prüfe ob Text eine Bestellnummer ist
            match = bestellnummer_pattern.match(text)
            if match:
                nummer = match.group(0)
                bestellungen_mit_urls.append({'nummer': nummer, 'url': href})
            else:
                # Prüfe ob Bestellnummer im href ist
                href_match = bestellnummer_pattern.search(href)
                if href_match:
                    nummer = href_match.group(0)
                    bestellungen_mit_urls.append({'nummer': nummer, 'url': href})
        
        # Methode 2: Fallback - Regex auf gesamter Seite (wie Master-Scraper)
        if len(bestellungen_mit_urls) == 0:
            html = driver.page_source
            all_matches = bestellnummer_pattern.findall(html)
            unique_numbers = list(set(all_matches))
            
            # Versuche URLs für jede Bestellnummer zu finden
            for nummer in unique_numbers:
                try:
                    link = driver.find_element(By.XPATH, f"//a[contains(@href, '{nummer}') or contains(text(), '{nummer}')]")
                    href = link.get_attribute('href')
                    if href and 'commandeDetailRepAll.do' in href:
                        bestellungen_mit_urls.append({'nummer': nummer, 'url': href})
                except:
                    pass
        
        # Deduplizieren
        seen = set()
        unique = []
        for item in bestellungen_mit_urls:
            if item['nummer'] not in seen:
                seen.add(item['nummer'])
                unique.append(item)
        
        return unique
        
    except Exception as e:
        log(f"❌ Fehler beim Extrahieren: {e}")
        return []


def scrape_all_pages(driver):
    """TAG173: Iteriert durch alle Pagination-Seiten (wie Master-Scraper)"""
    log("\n📄 SCRAPE ALLE SEITEN MIT PAGINATION")
    log("="*80)
    
    all_bestellungen = []
    page_num = 1
    max_pages = 20  # Safety-Limit
    
    while page_num <= max_pages:
        log(f"\n📄 Seite {page_num}")
        log("-" * 40)
        
        time.sleep(2)  # Kurz warten damit Seite geladen ist
        take_screenshot(driver, f"page_{page_num}")
        
        # Extrahiere Bestellungen von aktueller Seite
        bestellungen = extract_bestellungen_from_current_page(driver)
        log(f"   Gefunden: {len(bestellungen)} Bestellungen")
        
        for item in bestellungen:
            # Prüfe ob bereits vorhanden (nach Nummer)
            if not any(b['nummer'] == item['nummer'] for b in all_bestellungen):
                all_bestellungen.append(item)
                log(f"   ✅ {item['nummer']}")
        
        # Suche "Weiter"-Button (bt-arrow-right)
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "input.bt-arrow-right")
            
            # Prüfe ob inactive (disabled)
            classes = next_button.get_attribute('class') or ''
            if 'inactive' in classes:
                log("   ℹ️  'Weiter'-Button inactive - letzte Seite erreicht")
                break
            
            log("   🖱️  Klicke 'Weiter' (bt-arrow-right)...")
            next_button.click()
            time.sleep(3)
            page_num += 1
            
        except NoSuchElementException:
            log("   ℹ️  'Weiter'-Button nicht gefunden - letzte Seite")
            break
        except Exception as e:
            log(f"   ⚠️  Fehler bei Navigation: {e}")
            take_screenshot(driver, f"error_pagination_page_{page_num}")
            break
    
    log(f"\n📊 GESAMT: {len(all_bestellungen)} eindeutige Bestellungen auf {page_num} Seiten")
    
    # Warnung wenn keine gefunden
    if len(all_bestellungen) == 0:
        log("   ⚠️  KEINE BESTELLUNGEN GEFUNDEN!")
        log("   💡 Mögliche Ursachen:")
        log("      - Keine neuen Bestellungen vorhanden")
        log("      - Seitenstruktur geändert")
        log("      - Filter aktiv (z.B. Datum)")
        take_screenshot(driver, "debug_no_orders")
    
    return all_bestellungen

def safe_get_text(element):
    try:
        return element.text.strip() if element else ""
    except:
        return ""

def extract_bestellung_details(driver, bestellung_info):
    bestellnummer = bestellung_info['nummer']
    detail_url = bestellung_info.get('url')
    
    log(f"\n   🔍 Extrahiere Details für {bestellnummer}")
    
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

    try:
        # TAG173: Wenn keine URL vorhanden, versuche Link zu finden
        if not detail_url:
            log(f"      ⚠️  Keine URL vorhanden, suche Link für {bestellnummer}...")
            try:
                link = driver.find_element(By.XPATH, f"//a[contains(@href, '{bestellnummer}') or contains(text(), '{bestellnummer}')]")
                detail_url = link.get_attribute('href')
                if detail_url:
                    log(f"      ✅ Link gefunden: {detail_url[:80]}...")
                else:
                    log(f"      ❌ Kein Link für {bestellnummer} gefunden, überspringe")
                    return details
            except:
                log(f"      ❌ Kein Link für {bestellnummer} gefunden, überspringe")
                return details
        
        log(f"      🔗 Navigiere zu Detail-Seite...")
        driver.get(detail_url)
        time.sleep(5)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        take_screenshot(driver, f"detail_{bestellnummer}")
        
        # Absender extrahieren
        try:
            page_text = driver.page_source
            
            absender_code_match = re.search(r'Code Vertragspartner\s*:\s*</td>\s*<td[^>]*>\s*([A-Z0-9]+)', page_text)
            if absender_code_match:
                details['absender']['code'] = absender_code_match.group(1)
            
            absender_name_match = re.search(r'Name\s*:\s*</td>\s*<td[^>]*>\s*([^<]+)', page_text)
            if absender_name_match:
                details['absender']['name'] = absender_name_match.group(1).strip()
                
            log(f"      ✅ Absender: {details['absender'].get('code', 'N/A')}")
        except Exception as e:
            log(f"      ⚠️  Absender: {e}")
        
        # Empfänger extrahieren
        try:
            empf_section = re.search(r'Empfänger.*?Code Vertragspartner\s*:\s*</td>\s*<td[^>]*>\s*([A-Z0-9]+)', page_text, re.DOTALL)
            if empf_section:
                details['empfaenger']['code'] = empf_section.group(1)
            log(f"      ✅ Empfänger: {details['empfaenger'].get('code', 'N/A')}")
        except Exception as e:
            log(f"      ⚠️  Empfänger: {e}")
        
        # Bestelldatum
        try:
            datum_match = re.search(r'Bestelldatum\s*:\s*</td>\s*<td[^>]*>\s*(\d{2}\.\d{2}\.\d{2},\s*\d{2}:\d{2})', page_text)
            if datum_match:
                details['historie']['bestelldatum'] = datum_match.group(1)
                log(f"      ✅ Bestelldatum: {datum_match.group(1)}")
        except Exception as e:
            log(f"      ⚠️  Datum: {e}")
        
        # Positionen extrahieren - KORRIGIERT MIT REGEX!
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cols) >= 6:
                        first_col = safe_get_text(cols[0])
                        
                        # KORRIGIERT: Extrahiere Teilenummer auch wenn Zusatztext vorhanden
                        teilenummer_match = re.search(r'^\s*([A-Z0-9]{6,15})', first_col)
                        if teilenummer_match:
                            teilenummer = teilenummer_match.group(1)
                            
                            position = {
                                'teilenummer': teilenummer,
                                'beschreibung': safe_get_text(cols[1]),
                                'menge': safe_get_text(cols[2]),
                                'menge_in_lieferung': safe_get_text(cols[3]),
                                'menge_in_bestellung': safe_get_text(cols[4]),
                                'preis_ohne_mwst': safe_get_text(cols[5]),
                                'preis_mit_mwst': safe_get_text(cols[6]) if len(cols) > 6 else "",
                                'summe_inkl_mwst': safe_get_text(cols[7]) if len(cols) > 7 else ""
                            }
                            details['positionen'].append(position)
            
            log(f"      ✅ {len(details['positionen'])} Positionen extrahiert")
            
        except Exception as e:
            log(f"      ⚠️  Positionen: {e}")
        
        # Summen extrahieren
        try:
            summe_zzgl_match = re.search(r'Summe zzgl\. MwSt\s*:\s*</td>\s*<td[^>]*>\s*([\d,]+)\s*EUR', page_text)
            if summe_zzgl_match:
                details['summen']['zzgl_mwst'] = summe_zzgl_match.group(1)
            
            summe_inkl_match = re.search(r'Summe inkl\. MwSt\s*:\s*</td>\s*<td[^>]*>\s*([\d,]+)\s*EUR', page_text)
            if summe_inkl_match:
                details['summen']['inkl_mwst'] = summe_inkl_match.group(1)
                
            if details['summen']:
                log(f"      ✅ Summen extrahiert: {details['summen'].get('inkl_mwst', 'N/A')} EUR")
        except Exception as e:
            log(f"      ⚠️  Summen: {e}")
        
        # Kommentare & Parsed-Daten
        try:
            # TAG173: Kommentar-Feld extrahieren (enthält Kunden-Info)
            kommentar_full = None
            kommentar_patterns = [
                r'<td[^>]*>Kommentar</td>\s*<td[^>]*>\s*([^<]+)',  # <td>Kommentar</td><td>Wert</td>
                r'Kommentar[^<]*</td>\s*<td[^>]*>\s*([^<]+)',  # Kommentar</td><td>Wert</td>
                r'Kommentar\s*:\s*</td>\s*<td[^>]*>\s*([^<]+)',  # Mit Doppelpunkt
                r'Kommentare[^<]*</td>\s*<td[^>]*>\s*([^<]+)',
                r'Bemerkung[^<]*</td>\s*<td[^>]*>\s*([^<]+)',
            ]
            
            for pattern in kommentar_patterns:
                kommentar_match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
                if kommentar_match:
                    kommentar_full = kommentar_match.group(1).strip()
                    # Entferne HTML-Tags und Whitespace
                    kommentar_full = re.sub(r'<[^>]+>', '', kommentar_full).strip()
                    # Entferne &nbsp; und andere HTML-Entities
                    kommentar_full = kommentar_full.replace('&nbsp;', ' ').strip()
                    if kommentar_full and len(kommentar_full) > 2:
                        details['kommentare']['kommentar'] = kommentar_full
                        log(f"      ✅ Kommentar gefunden: {kommentar_full[:80]}...")
                        break
            
            # Fallback: Suche nach "Kommentar" im gesamten Text
            if not kommentar_full:
                kommentar_section = re.search(r'Kommentar[^>]*>([^<]+)', page_text, re.IGNORECASE)
                if kommentar_section:
                    kommentar_full = kommentar_section.group(1).strip()
                    kommentar_full = re.sub(r'<[^>]+>', '', kommentar_full).strip()
                    if kommentar_full and len(kommentar_full) > 2:
                        details['kommentare']['kommentar'] = kommentar_full
                        log(f"      ✅ Kommentar gefunden (Fallback): {kommentar_full[:80]}...")
            
            # Lokale Bestell-Nr extrahieren
            lokale_nr = None
            lokale_match = re.search(r'Lokale Bestell-Nr\.\s*:\s*</td>\s*<td[^>]*>\s*([^<]+)', page_text)
            if lokale_match:
                lokale_nr = lokale_match.group(1).strip()
                details['kommentare']['lokale_nr'] = lokale_nr
                log(f"      ✅ Lokale Nr: {lokale_nr}")
            
            # TAG173: Parse Daten aus Kommentar-Feld (Kunde wird hier gespeichert)
            # Format: "A39915 Rose ber.ber W0L0AHL35A2036973" oder "LokaleNr Kundenname VIN"
            if kommentar_full:
                # Entferne VIN (17 Zeichen) und lokale_nr (A + Zahlen) am Anfang
                kommentar_clean = kommentar_full.strip()
                
                # Entferne VIN am Ende (falls vorhanden)
                vin_at_end = re.search(r'\b([A-HJ-NPR-Z0-9]{17})\s*$', kommentar_clean)
                if vin_at_end:
                    kommentar_clean = kommentar_clean[:vin_at_end.start()].strip()
                
                # Entferne lokale_nr am Anfang (A + Zahlen oder nur Zahlen)
                lokale_at_start = re.match(r'^(A?\d{4,7})\s+', kommentar_clean)
                if lokale_at_start:
                    kommentar_clean = kommentar_clean[lokale_at_start.end():].strip()
                
                # Was übrig bleibt ist der Kundenname
                if kommentar_clean and len(kommentar_clean) > 2:
                    details['parsed'] = details.get('parsed', {})
                    details['parsed']['kunde_name'] = kommentar_clean
                    log(f"      ✅ Kundenname gefunden: {kommentar_clean}")
            
            # VIN extrahieren (17 Zeichen, alphanumerisch)
            vin_pattern = re.compile(r'\b([A-HJ-NPR-Z0-9]{17})\b')
            vin_match = vin_pattern.search(page_text)
            if vin_match:
                details['parsed'] = details.get('parsed', {})
                details['parsed']['vin'] = vin_match.group(1)
                log(f"      ✅ VIN gefunden: {details['parsed']['vin']}")
            
            # Kundennummer extrahieren (aus Kommentar oder Seite)
            kdnr_found = False
            if kommentar_full:
                # Suche nach Kundennummer im Kommentar (4-6 stellige Zahl)
                kdnr_pattern = re.compile(r'\b(\d{4,6})\b')
                kdnr_matches = kdnr_pattern.findall(kommentar_full)
                for match in kdnr_matches:
                    kdnr = int(match)
                    if 1000 <= kdnr <= 999999:
                        details['parsed'] = details.get('parsed', {})
                        details['parsed']['kundennummer'] = match
                        log(f"      ✅ Kundennummer gefunden (aus Kommentar): {match}")
                        kdnr_found = True
                        break
            
            # Fallback: Suche auf gesamter Seite
            if not kdnr_found:
                kdnr_pattern = re.compile(r'\b(\d{4,6})\b')
                kdnr_matches = kdnr_pattern.findall(page_text)
                for match in kdnr_matches:
                    kdnr = int(match)
                    if 1000 <= kdnr <= 999999:
                        details['parsed'] = details.get('parsed', {})
                        details['parsed']['kundennummer'] = match
                        log(f"      ✅ Kundennummer gefunden: {match}")
                        break
            
            # Werkstattauftrag = lokale_nr (wenn es eine Nummer ist)
            if lokale_nr:
                auftrag_pattern = re.compile(r'^A?\d{4,7}$')
                if auftrag_pattern.match(lokale_nr):
                    details['parsed'] = details.get('parsed', {})
                    details['parsed']['werkstattauftrag'] = lokale_nr
                    log(f"      ✅ Werkstattauftrag: {lokale_nr}")
        except Exception as e:
            log(f"      ⚠️  Kommentare/Parsing: {e}")
        
        return details

    except Exception as e:
        log(f"      ❌ Fehler bei {bestellnummer}: {e}")
        take_screenshot(driver, f"error_{bestellnummer}")
        return details

def scrape_all_details(driver, bestellungen, max_orders=None):
    log("\n📋 SCRAPE ALLE BESTELLUNGS-DETAILS")
    log("="*80)
    
    if max_orders:
        bestellungen = bestellungen[:max_orders]
        log(f"⚠️  TEST-MODUS: Nur erste {max_orders} Bestellungen")
    
    all_details = []
    total = len(bestellungen)
    
    for idx, bestellung_info in enumerate(bestellungen, 1):
        log(f"\n[{idx}/{total}] {bestellung_info['nummer']}")
        log("-" * 40)
        
        details = extract_bestellung_details(driver, bestellung_info)
        all_details.append(details)
        
        progress = (idx / total) * 100
        log(f"   📊 Progress: {progress:.1f}%")
        time.sleep(2)
    
    return all_details

def save_results(details):
    log(f"\n💾 SPEICHERE DETAIL-ERGEBNISSE")
    log("="*80)

    data = {
        'timestamp': datetime.now().isoformat(),
        'anzahl_bestellungen': len(details),
        'bestellungen': details
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    log(f"✅ Gespeichert: {OUTPUT_FILE}")
    
    total_positionen = sum(len(d['positionen']) for d in details)
    bestellungen_mit_positionen = sum(1 for d in details if len(d['positionen']) > 0)
    
    log(f"📊 Statistik:")
    log(f"   - Bestellungen gesamt: {len(details)}")
    log(f"   - Bestellungen mit Positionen: {bestellungen_mit_positionen}")
    log(f"   - Positionen gesamt: {total_positionen}")
    if len(details) > 0:
        log(f"   - Ø Positionen/Bestellung: {total_positionen/len(details):.1f}")

def main():
    log("\n" + "="*80)
    log("🚀 STELLANTIS SERVICE BOX - DETAIL SCRAPER FINAL V2")
    log("="*80)

    driver = None
    TEST_MODE = False  # TAG 173: Deaktiviert für Produktion
    MAX_ORDERS = 5 if TEST_MODE else None

    try:
        credentials = load_credentials()
        driver = setup_driver()

        if not login_and_navigate(driver, credentials):
            log("\n❌ Login/Navigation fehlgeschlagen!")
            return False

        # TAG173: Scrape alle Seiten mit Pagination
        bestellungen = scrape_all_pages(driver)
        
        if not bestellungen:
            log("❌ Keine Bestellnummern gefunden!")
            return False
        
        if TEST_MODE:
            log(f"\n⚠️  TEST-MODUS: Nur erste {MAX_ORDERS} Bestellungen")

        details = scrape_all_details(driver, bestellungen, MAX_ORDERS)

        if details:
            save_results(details)
            log("\n" + "="*80)
            log("✅ DETAIL-SCRAPER ERFOLGREICH!")
            log("="*80)
        else:
            log("\n⚠️  Keine Details extrahiert!")

        return True

    except Exception as e:
        log(f"\n❌ Fehler: {e}")
        import traceback
        log(traceback.format_exc())
        if driver:
            take_screenshot(driver, "error_unexpected")
        return False

    finally:
        if driver:
            log(f"\n📂 Ergebnisse: {OUTPUT_FILE}")
            log(f"📂 Screenshots: {SCREENSHOTS_DIR}")
            log("\n🔚 Schließe Browser...")
            driver.quit()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
