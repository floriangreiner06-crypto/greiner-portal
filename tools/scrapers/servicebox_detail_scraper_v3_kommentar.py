#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Service Box Detail-Scraper V3.1
MIT KOMMENTAR WERKSTATT FELD + VERBESSERTES PARSING

Version: TAG83 v3.1
Datum: 25.11.2025

FIX: Kundennummer wird jetzt auch aus Lokale Bestell-Nr. erkannt!
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
LOG_FILE = f"{BASE_DIR}/logs/servicebox_detail_scraper_v3.log"
OUTPUT_FILE = f"{BASE_DIR}/logs/servicebox_bestellungen_v3.json"
PROGRESS_FILE = f"{BASE_DIR}/logs/servicebox_scraper_progress_v3.json"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# KONFIGURATION
TEST_MODE = False   # True = nur erste 5 Bestellungen
MAX_TEST = 5       # Anzahl im Test-Mode
MAX_PAGES = 20     # Maximum Seiten (Safety)

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

# ============================================================================
# VIN & KUNDENNUMMER PARSER
# ============================================================================

def ist_kundennummer(text):
    """Prüft ob Text eine Kundennummer ist (6-7 Ziffern)"""
    if not text:
        return False
    return bool(re.match(r'^\d{6,7}$', text.strip()))

def ist_werkstattauftrag(text):
    """Prüft ob Text ein Werkstattauftrag ist (A + 5 Ziffern)"""
    if not text:
        return False
    return bool(re.match(r'^A\d{5}$', text.strip(), re.IGNORECASE))

def extract_vin_from_text(text):
    """Extrahiert VIN (17-stellig) aus Freitext"""
    if not text:
        return None
    vin_pattern = r'\b([A-HJ-NPR-Z0-9]{17})\b'
    match = re.search(vin_pattern, text.upper())
    if match:
        return match.group(1)
    return None

def extract_kundennummer_from_text(text):
    """Extrahiert Kundennummer (6-7 Ziffern) aus Freitext"""
    if not text:
        return None
    numbers = re.findall(r'\b(\d{6,7})\b', text)
    return numbers[0] if numbers else None

def extract_werkstattauftrag_from_text(text):
    """Extrahiert Werkstattauftrag (A + 5 Ziffern) aus Freitext"""
    if not text:
        return None
    wa_match = re.search(r'\b(A\d{5})\b', text, re.IGNORECASE)
    if wa_match:
        return wa_match.group(1).upper()
    return None

def parse_kommentar_felder(lokale_nr, kommentar_werkstatt, kd_bestell_nr=None):
    """
    Parst alle Kommentar-Felder intelligent.
    
    LOGIK:
    1. Wenn lokale_nr eine 6-7 stellige Zahl ist → Kundennummer
    2. Wenn lokale_nr A+5Ziffern ist → Werkstattauftrag
    3. VIN aus kommentar_werkstatt extrahieren (17-stellig)
    4. Kundennummer aus kommentar_werkstatt extrahieren (falls noch nicht gefunden)
    """
    result = {
        'vin': None,
        'kundennummer': None,
        'werkstattauftrag': None,
        'sonstiges': None
    }
    
    lokale_nr = (lokale_nr or '').strip()
    kommentar_ws = (kommentar_werkstatt or '').strip()
    kd_nr = (kd_bestell_nr or '').strip()
    
    # 1. Lokale Bestell-Nr. prüfen
    if ist_kundennummer(lokale_nr):
        result['kundennummer'] = lokale_nr
    elif ist_werkstattauftrag(lokale_nr):
        result['werkstattauftrag'] = lokale_nr
    
    # 2. Kommentar Werkstatt parsen
    if kommentar_ws:
        # VIN extrahieren
        vin = extract_vin_from_text(kommentar_ws)
        if vin:
            result['vin'] = vin
        
        # Werkstattauftrag (falls noch nicht gefunden)
        if not result['werkstattauftrag']:
            wa = extract_werkstattauftrag_from_text(kommentar_ws)
            if wa:
                result['werkstattauftrag'] = wa
        
        # Kundennummer (falls noch nicht gefunden)
        if not result['kundennummer']:
            kd = extract_kundennummer_from_text(kommentar_ws)
            if kd:
                result['kundennummer'] = kd
        
        # Rest als sonstiges
        remaining = kommentar_ws
        if result['vin']:
            remaining = remaining.replace(result['vin'], '')
        if result['werkstattauftrag']:
            remaining = re.sub(result['werkstattauftrag'], '', remaining, flags=re.IGNORECASE)
        if result['kundennummer']:
            remaining = remaining.replace(result['kundennummer'], '')
        remaining = ' '.join(remaining.split()).strip()
        if remaining and len(remaining) > 1:
            result['sonstiges'] = remaining
    
    # 3. Bestellungsnummer des Kunden (Fallback)
    if not result['kundennummer'] and ist_kundennummer(kd_nr):
        result['kundennummer'] = kd_nr
    
    return result

# ============================================================================
# LOGIN & NAVIGATION
# ============================================================================

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

# ============================================================================
# MEHR BESTELLUNGEN LADEN
# ============================================================================

def get_total_bestellungen_count(driver):
    try:
        html = driver.page_source
        match = re.search(r'Anzahl\s+der\s+präsentierten\s+Elemente\s+\d+\s*-\s*\d+\s*/\s*(\d+)', html, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 0
    except:
        return 0

def click_mehr_bestellungen(driver):
    log("\n🔽 KLICKE 'MEHR BESTELLUNGEN ANZEIGEN'")
    log("-"*80)
    
    try:
        count_before = get_total_bestellungen_count(driver)
        log(f"   📊 Bestellungen VORHER: {count_before}")
        
        selectors = [
            (By.XPATH, "//input[@value='Mehr Bestellungen anzeigen']"),
            (By.CSS_SELECTOR, "input.bt-plus[onclick*='displayAll']"),
            (By.XPATH, "//input[@type='button' and contains(@value, 'Mehr Bestellungen')]"),
        ]
        
        for by, selector in selectors:
            try:
                mehr_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((by, selector))
                )
                mehr_button.click()
                log(f"   ✅ Button geklickt")
                break
            except:
                continue
        
        log("   ⏳ Warte 10 Sekunden...")
        time.sleep(10)
        
        count_after = get_total_bestellungen_count(driver)
        log(f"   📊 Bestellungen NACHHER: {count_after}")
        
        return count_after > count_before
        
    except Exception as e:
        log(f"   ⚠️ Fehler: {e}")
        return False

# ============================================================================
# URL SAMMLUNG (PHASE 1)
# ============================================================================

def extract_bestellungen_from_current_page(driver):
    try:
        links = driver.find_elements(By.XPATH, "//a[contains(@href, 'commandeDetailRepAll.do')]")
        bestellungen = []

        for link in links:
            text = link.text.strip()
            if text and text.startswith('1J') and len(text) == 9:
                href = link.get_attribute('href')
                bestellungen.append({'nummer': text, 'url': href})

        seen = set()
        unique = []
        for item in bestellungen:
            if item['nummer'] not in seen:
                seen.add(item['nummer'])
                unique.append(item)

        return unique

    except Exception as e:
        log(f"❌ Fehler: {e}")
        return []

def phase1_collect_all_urls(driver):
    log("\n" + "="*80)
    log("📋 PHASE 1: SAMMLE ALLE URLs")
    log("="*80)

    all_bestellungen = []
    page_num = 1

    while page_num <= MAX_PAGES:
        log(f"\n📄 Seite {page_num}")
        time.sleep(2)

        bestellungen = extract_bestellungen_from_current_page(driver)
        log(f"   Gefunden: {len(bestellungen)}")

        for b in bestellungen:
            if not any(x['nummer'] == b['nummer'] for x in all_bestellungen):
                all_bestellungen.append(b)

        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "input.bt-arrow-right")
            classes = next_button.get_attribute('class') or ''
            if 'inactive' in classes:
                log(f"   ℹ️ Letzte Seite erreicht")
                break
            next_button.click()
            time.sleep(3)
            page_num += 1
        except:
            break

    log(f"\n📊 PHASE 1: {len(all_bestellungen)} Bestellungen gefunden")
    return all_bestellungen

# ============================================================================
# DETAIL-EXTRAKTION (PHASE 2)
# ============================================================================

def safe_get_text(element):
    try:
        return element.text.strip() if element else ""
    except:
        return ""

def extract_bestellung_details(driver, bestellung_info):
    bestellnummer = bestellung_info['nummer']
    detail_url = bestellung_info['url']

    details = {
        'bestellnummer': bestellnummer,
        'url': detail_url,
        'absender': {},
        'empfaenger': {},
        'benutzer': None,
        'historie': {},
        'positionen': [],
        'summen': {},
        'kommentare': {
            'lokale_bestell_nr': None,
            'kommentar_werkstatt': None,
            'bestellungsnummer_des_kunden': None,
            'dringlichkeit': None
        },
        'parsed': {
            'vin': None,
            'kundennummer': None,
            'werkstattauftrag': None,
            'sonstiges': None
        }
    }

    try:
        driver.get(detail_url)
        time.sleep(4)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        page_text = driver.page_source

        # ABSENDER
        try:
            match = re.search(r'Absender.*?Code Vertragspartner\s*:\s*</td>\s*<td[^>]*>\s*([A-Z0-9]+)', page_text, re.DOTALL | re.IGNORECASE)
            if match:
                details['absender']['code'] = match.group(1)
            match = re.search(r'Absender.*?Name\s*:\s*</td>\s*<td[^>]*>\s*([^<]+)', page_text, re.DOTALL | re.IGNORECASE)
            if match:
                details['absender']['name'] = match.group(1).strip()
            match = re.search(r'Benutzer\s*:\s*</td>\s*<td[^>]*>\s*([^<]+)', page_text, re.IGNORECASE)
            if match:
                details['benutzer'] = match.group(1).strip()
        except:
            pass

        # EMPFÄNGER
        try:
            match = re.search(r'Empfänger.*?Code Vertragspartner\s*:\s*</td>\s*<td[^>]*>\s*([A-Z0-9]+)', page_text, re.DOTALL | re.IGNORECASE)
            if match:
                details['empfaenger']['code'] = match.group(1)
        except:
            pass

        # HISTORIE
        try:
            match = re.search(r'Bestelldatum\s*:\s*</td>\s*<td[^>]*>\s*(\d{2}\.\d{2}\.\d{2},?\s*\d{2}:\d{2})', page_text, re.IGNORECASE)
            if match:
                details['historie']['bestelldatum'] = match.group(1)
        except:
            pass

        # KOMMENTARE-BEREICH
        try:
            match = re.search(r'Lokale Bestell-Nr\.\s*:\s*</td>\s*<td[^>]*>\s*([^<]+)', page_text, re.IGNORECASE)
            if match:
                details['kommentare']['lokale_bestell_nr'] = match.group(1).strip()
                log(f"      📋 Lokale Bestell-Nr.: {details['kommentare']['lokale_bestell_nr']}")
        except:
            pass

        try:
            match = re.search(r'Kommentar Werkstatt\s*:\s*</td>\s*<td[^>]*>\s*([^<]+)', page_text, re.IGNORECASE)
            if match:
                details['kommentare']['kommentar_werkstatt'] = match.group(1).strip()
                log(f"      💬 Kommentar Werkstatt: {details['kommentare']['kommentar_werkstatt']}")
        except:
            pass

        try:
            match = re.search(r'Bestellungsnummer des Kunden\s*:\s*</td>\s*<td[^>]*>\s*([^<]+)', page_text, re.IGNORECASE)
            if match:
                details['kommentare']['bestellungsnummer_des_kunden'] = match.group(1).strip()
        except:
            pass

        try:
            match = re.search(r'Dringlichkeit\s*:\s*</td>\s*<td[^>]*>\s*([^<]+)', page_text, re.IGNORECASE)
            if match:
                details['kommentare']['dringlichkeit'] = match.group(1).strip()
        except:
            pass

        # INTELLIGENTES PARSING
        parsed = parse_kommentar_felder(
            details['kommentare']['lokale_bestell_nr'],
            details['kommentare']['kommentar_werkstatt'],
            details['kommentare']['bestellungsnummer_des_kunden']
        )
        details['parsed'] = parsed
        
        if parsed.get('vin'):
            log(f"      🚗 VIN erkannt: {parsed['vin']}")
        if parsed.get('kundennummer'):
            log(f"      👤 Kundennummer erkannt: {parsed['kundennummer']}")
        if parsed.get('werkstattauftrag'):
            log(f"      🔧 Werkstattauftrag: {parsed['werkstattauftrag']}")

        # POSITIONEN
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            seen_positions = set()

            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 6:
                        first_col = safe_get_text(cols[0])
                        teilenummer_match = re.search(r'^\s*(\d{7,10})', first_col)
                        if teilenummer_match:
                            teilenummer = teilenummer_match.group(1)
                            beschreibung = safe_get_text(cols[1])
                            position_key = (teilenummer, beschreibung)
                            if position_key in seen_positions:
                                continue
                            seen_positions.add(position_key)
                            position = {
                                'teilenummer': teilenummer,
                                'beschreibung': beschreibung,
                                'menge': safe_get_text(cols[2]),
                                'menge_in_lieferung': safe_get_text(cols[3]),
                                'menge_in_bestellung': safe_get_text(cols[4]),
                                'preis_ohne_mwst': safe_get_text(cols[5]),
                                'preis_mit_mwst': safe_get_text(cols[6]) if len(cols) > 6 else "",
                                'summe_inkl_mwst': safe_get_text(cols[7]) if len(cols) > 7 else ""
                            }
                            details['positionen'].append(position)
        except:
            pass

        # SUMMEN
        try:
            match = re.search(r'Summe zzgl\. MwSt\s*:\s*([\d.,]+)\s*EUR', page_text, re.IGNORECASE)
            if match:
                details['summen']['zzgl_mwst'] = match.group(1)
            match = re.search(r'Summe inkl\. MwSt\s*:\s*([\d.,]+)\s*EUR', page_text, re.IGNORECASE)
            if match:
                details['summen']['inkl_mwst'] = match.group(1)
        except:
            pass

        return details

    except Exception as e:
        log(f"      ❌ Fehler: {e}")
        return details

def phase2_scrape_all_details(driver, bestellungen):
    log("\n" + "="*80)
    log("📋 PHASE 2: SCRAPE DETAILS (MIT KOMMENTAR WERKSTATT)")
    log("="*80)

    if TEST_MODE:
        bestellungen = bestellungen[:MAX_TEST]
        log(f"⚠️ TEST-MODUS: Nur erste {MAX_TEST} Bestellungen")

    all_details = []
    total = len(bestellungen)
    
    stats = {
        'mit_kommentar_werkstatt': 0,
        'mit_lokale_nr': 0,
        'mit_kundennummer': 0,
        'mit_vin': 0,
        'mit_werkstattauftrag': 0
    }

    for idx, bestellung_info in enumerate(bestellungen, 1):
        log(f"\n[{idx}/{total}] {bestellung_info['nummer']}")
        log("-" * 40)

        try:
            details = extract_bestellung_details(driver, bestellung_info)
            all_details.append(details)

            if details['kommentare'].get('kommentar_werkstatt'):
                stats['mit_kommentar_werkstatt'] += 1
            if details['kommentare'].get('lokale_bestell_nr'):
                stats['mit_lokale_nr'] += 1
            if details['parsed'].get('kundennummer'):
                stats['mit_kundennummer'] += 1
            if details['parsed'].get('vin'):
                stats['mit_vin'] += 1
            if details['parsed'].get('werkstattauftrag'):
                stats['mit_werkstattauftrag'] += 1

            log(f"   📊 Progress: {(idx/total)*100:.1f}%")

            if idx % 10 == 0:
                save_progress(all_details, idx, total, stats)

        except Exception as e:
            log(f"   ❌ Fehler: {e}")
            all_details.append({'bestellnummer': bestellung_info['nummer'], 'error': str(e)})

        time.sleep(1)

    log(f"\n{'='*80}")
    log(f"📊 PHASE 2 STATISTIKEN:")
    log(f"   - Bestellungen gesamt: {len(all_details)}")
    log(f"   - Mit Kommentar Werkstatt: {stats['mit_kommentar_werkstatt']}")
    log(f"   - Mit Lokale Bestell-Nr.: {stats['mit_lokale_nr']}")
    log(f"   - Mit Kundennummer: {stats['mit_kundennummer']}")
    log(f"   - Mit VIN: {stats['mit_vin']}")
    log(f"   - Mit Werkstattauftrag: {stats['mit_werkstattauftrag']}")
    log(f"{'='*80}")

    return all_details, stats

def save_progress(details, current, total, stats):
    try:
        data = {
            'timestamp': datetime.now().isoformat(),
            'current': current,
            'total': total,
            'stats': stats,
            'details': details
        }
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except:
        pass

def save_results(details, stats):
    log(f"\n💾 SPEICHERE ERGEBNISSE")
    log("="*80)

    data = {
        'timestamp': datetime.now().isoformat(),
        'version': 'v3.1_kommentar_werkstatt',
        'anzahl_bestellungen': len(details),
        'statistik': stats,
        'bestellungen': details
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    log(f"✅ Gespeichert: {OUTPUT_FILE}")

    # CSV-Übersicht
    csv_file = OUTPUT_FILE.replace('.json', '_uebersicht.csv')
    try:
        import csv
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow([
                'Bestellnummer', 'Datum', 'Benutzer',
                'Lokale_Bestell_Nr', 'Kommentar_Werkstatt',
                'VIN', 'Kundennummer', 'Werkstattauftrag',
                'Positionen', 'Summe_inkl_MwSt'
            ])
            
            for d in details:
                writer.writerow([
                    d.get('bestellnummer', ''),
                    d.get('historie', {}).get('bestelldatum', ''),
                    d.get('benutzer', ''),
                    d.get('kommentare', {}).get('lokale_bestell_nr', ''),
                    d.get('kommentare', {}).get('kommentar_werkstatt', ''),
                    d.get('parsed', {}).get('vin', ''),
                    d.get('parsed', {}).get('kundennummer', ''),
                    d.get('parsed', {}).get('werkstattauftrag', ''),
                    len(d.get('positionen', [])),
                    d.get('summen', {}).get('inkl_mwst', '')
                ])
        
        log(f"✅ CSV-Übersicht: {csv_file}")
    except Exception as e:
        log(f"⚠️ CSV-Fehler: {e}")

    total_positionen = sum(len(d.get('positionen', [])) for d in details)
    log(f"\n📊 FINALE STATISTIK:")
    log(f"   - Bestellungen: {len(details)}")
    log(f"   - Positionen gesamt: {total_positionen}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    log("\n" + "="*80)
    log("🚀 STELLANTIS SERVICE BOX SCRAPER V3.1")
    log("   MIT VERBESSERTEM KUNDENNUMMER-PARSING")
    log("="*80)
    log(f"📋 TEST_MODE: {TEST_MODE}, MAX_TEST: {MAX_TEST}")
    log("="*80)

    driver = None

    try:
        credentials = load_credentials()
        driver = setup_driver()

        if not login_and_navigate(driver, credentials):
            log("\n❌ Login fehlgeschlagen!")
            return False

        click_mehr_bestellungen(driver)

        all_bestellungen = phase1_collect_all_urls(driver)

        if not all_bestellungen:
            log("\n❌ Keine Bestellungen gefunden!")
            return False

        details, stats = phase2_scrape_all_details(driver, all_bestellungen)

        if details:
            save_results(details, stats)
            log("\n" + "="*80)
            log("✅ SCRAPER V3.1 ERFOLGREICH!")
            log("="*80)

        return True

    except Exception as e:
        log(f"\n❌ Fehler: {e}")
        import traceback
        log(traceback.format_exc())
        if driver:
            take_screenshot(driver, "error_main")
        return False

    finally:
        if driver:
            log(f"\n📂 Output: {OUTPUT_FILE}")
            log(f"📂 Log: {LOG_FILE}")
            log("\n🔚 Schließe Browser...")
            driver.quit()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
