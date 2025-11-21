#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Service Box Detail-Scraper - 2-PHASEN-ANSATZ V2
Version: TAG70 - Mit Validierung nach "Mehr Bestellungen anzeigen"

VERBESSERUNGEN:
- Längere Wartezeit nach Button-Klick (15 Sek)
- Validierung dass Seite neu geladen wurde (Anzahl > 100)
- Retry-Logik falls Seite nicht sofort lädt
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
LOG_FILE = f"{BASE_DIR}/logs/servicebox_detail_scraper_2phase_v2.log"
OUTPUT_FILE = f"{BASE_DIR}/logs/servicebox_bestellungen_details_complete.json"
PROGRESS_FILE = f"{BASE_DIR}/logs/servicebox_scraper_progress.json"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# KONFIGURATION
TEST_MODE = False  # True = nur erste 3 Bestellungen GESAMT
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

def login_and_navigate(driver, credentials):
    """Login und Navigation zur Historie-Seite"""
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

def get_total_bestellungen_count(driver):
    """Extrahiert die Gesamtzahl der Bestellungen aus dem HTML"""
    try:
        html = driver.page_source
        # Suche nach "Anzahl der präsentierten Elemente 1 - 10 / XXX"
        match = re.search(r'Anzahl\s+der\s+präsentierten\s+Elemente\s+\d+\s*-\s*\d+\s*/\s*(\d+)', html, re.IGNORECASE)
        if match:
            total = int(match.group(1))
            return total
        return 0
    except Exception as e:
        log(f"   ⚠️ Fehler beim Zählen: {e}")
        return 0

def click_mehr_bestellungen_mit_validierung(driver):
    """Klickt auf 'Mehr Bestellungen anzeigen' und validiert dass Seite neu geladen wurde"""
    log("\n🔽 KLICKE 'MEHR BESTELLUNGEN ANZEIGEN' (MIT VALIDIERUNG)")
    log("-"*80)
    
    try:
        # Zähle Bestellungen VORHER
        count_before = get_total_bestellungen_count(driver)
        log(f"   📊 Bestellungen VORHER: {count_before}")
        
        # Button finden und klicken
        selectors = [
            (By.XPATH, "//input[@value='Mehr Bestellungen anzeigen']"),
            (By.CSS_SELECTOR, "input.bt-plus[onclick*='displayAll']"),
            (By.XPATH, "//input[@type='button' and contains(@value, 'Mehr Bestellungen')]"),
            (By.CSS_SELECTOR, "input[value*='Mehr Bestellungen']")
        ]
        
        button_found = False
        for by, selector in selectors:
            try:
                mehr_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((by, selector))
                )
                log(f"   ✅ Button gefunden via: {selector}")
                mehr_button.click()
                button_found = True
                break
            except:
                continue
        
        if not button_found:
            log("   ⚠️  'Mehr Bestellungen' Button nicht gefunden")
            return False
        
        # WARTE UND VALIDIERE
        log("   ⏳ Warte 10 Sekunden auf Neuladen...")
        time.sleep(10)
        take_screenshot(driver, "nach_mehr_bestellungen_10s")
        
        # Prüfe Anzahl
        count_after = get_total_bestellungen_count(driver)
        log(f"   📊 Bestellungen NACHHER: {count_after}")
        
        # Validierung
        if count_after > count_before and count_after > 100:
            log(f"   ✅ ERFOLG! Anzahl gestiegen: {count_before} → {count_after}")
            return True
        else:
            log(f"   ⚠️  Anzahl nicht wie erwartet. Warte weitere 5 Sekunden...")
            time.sleep(5)
            count_retry = get_total_bestellungen_count(driver)
            log(f"   📊 Bestellungen NACH RETRY: {count_retry}")
            
            if count_retry > count_before and count_retry > 100:
                log(f"   ✅ ERFOLG nach Retry! Anzahl: {count_retry}")
                return True
            else:
                log(f"   ⚠️  Seite hat sich nicht korrekt neu geladen!")
                take_screenshot(driver, "validierung_fehlgeschlagen")
                return False
        
    except Exception as e:
        log(f"   ❌ Fehler: {e}")
        return False

def extract_bestellungen_from_current_page(driver):
    """Extrahiert Bestellnummern und URLs von aktueller Seite"""
    try:
        links = driver.find_elements(By.XPATH, "//a[contains(@href, 'commandeDetailRepAll.do')]")
        bestellungen_mit_urls = []

        for link in links:
            text = link.text.strip()
            if text and text.startswith('1JA') and len(text) == 9:
                href = link.get_attribute('href')
                bestellungen_mit_urls.append({'nummer': text, 'url': href})

        # Duplikate entfernen
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

# ============================================================================
# PHASE 1: SAMMLE ALLE URLs VON ALLEN SEITEN
# ============================================================================

def phase1_collect_all_urls(driver):
    """Phase 1: Sammle alle Bestellnummer-URLs von allen Seiten"""
    log("\n" + "="*80)
    log("📋 PHASE 1: SAMMLE ALLE BESTELLNUMMER-URLs")
    log("="*80)

    all_bestellungen = []
    page_num = 1

    while page_num <= MAX_PAGES:
        log(f"\n📄 Seite {page_num}")
        log("-" * 40)

        time.sleep(2)
        take_screenshot(driver, f"phase1_page_{page_num}")

        # Extrahiere Bestellungen
        bestellungen = extract_bestellungen_from_current_page(driver)
        log(f"   Gefunden: {len(bestellungen)} Bestellungen")

        for b in bestellungen:
            # Prüfe ob schon vorhanden (über alle Seiten)
            if not any(x['nummer'] == b['nummer'] for x in all_bestellungen):
                all_bestellungen.append(b)
                log(f"   ✅ {b['nummer']}")

        # Suche "Weiter"-Button
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "input.bt-arrow-right")

            # Prüfe ob inactive (disabled)
            classes = next_button.get_attribute('class') or ''
            if 'inactive' in classes:
                log(f"\n   ℹ️  'Weiter'-Button inactive - letzte Seite erreicht")
                break

            log(f"\n   🖱️  Klicke 'Weiter' (Seite {page_num} → {page_num+1})...")
            next_button.click()
            time.sleep(3)
            page_num += 1

        except NoSuchElementException:
            log(f"\n   ℹ️  'Weiter'-Button nicht gefunden - letzte Seite")
            break
        except Exception as e:
            log(f"\n   ⚠️  Fehler bei Navigation: {e}")
            break

    log(f"\n{'='*80}")
    log(f"📊 PHASE 1 ABGESCHLOSSEN:")
    log(f"   - {len(all_bestellungen)} eindeutige Bestellungen gefunden")
    log(f"   - Von {page_num} Seiten")
    log(f"{'='*80}")

    return all_bestellungen

# ============================================================================
# PHASE 2: SCRAPE DETAILS FÜR ALLE URLs
# ============================================================================

def safe_get_text(element):
    """Sicher Text aus Element holen"""
    try:
        return element.text.strip() if element else ""
    except:
        return ""

def extract_bestellung_details(driver, bestellung_info):
    """Extrahiert vollständige Details einer Bestellung"""
    bestellnummer = bestellung_info['nummer']
    detail_url = bestellung_info['url']

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
        driver.get(detail_url)
        time.sleep(4)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        page_text = driver.page_source

        # Absender extrahieren
        try:
            absender_code_match = re.search(r'Code Vertragspartner\s*:\s*</td>\s*<td[^>]*>\s*([A-Z0-9]+)', page_text)
            if absender_code_match:
                details['absender']['code'] = absender_code_match.group(1)

            absender_name_match = re.search(r'Name\s*:\s*</td>\s*<td[^>]*>\s*([^<]+)', page_text)
            if absender_name_match:
                details['absender']['name'] = absender_name_match.group(1).strip()
        except Exception as e:
            pass

        # Empfänger extrahieren
        try:
            empf_section = re.search(r'Empfänger.*?Code Vertragspartner\s*:\s*</td>\s*<td[^>]*>\s*([A-Z0-9]+)', page_text, re.DOTALL)
            if empf_section:
                details['empfaenger']['code'] = empf_section.group(1)
        except Exception as e:
            pass

        # Bestelldatum
        try:
            datum_match = re.search(r'Bestelldatum\s*:\s*</td>\s*<td[^>]*>\s*(\d{2}\.\d{2}\.\d{2},\s*\d{2}:\d{2})', page_text)
            if datum_match:
                details['historie']['bestelldatum'] = datum_match.group(1)
        except Exception as e:
            pass

        # Positionen extrahieren (mit Duplikat-Entfernung!)
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            seen_positions = set()

            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")

                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")

                    if len(cols) >= 6:
                        first_col = safe_get_text(cols[0])

                        # Extrahiere Teilenummer (7-10 Ziffern, auch mit Zusatztext)
                        teilenummer_match = re.search(r'^\s*(\d{7,10})', first_col)
                        if teilenummer_match:
                            teilenummer = teilenummer_match.group(1)
                            beschreibung = safe_get_text(cols[1])

                            # Duplikat-Check
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

        except Exception as e:
            pass

        # Summen extrahieren
        try:
            summe_zzgl_match = re.search(r'Summe zzgl\. MwSt\s*:\s*</td>\s*<td[^>]*>\s*([\d,]+)\s*EUR', page_text)
            if summe_zzgl_match:
                details['summen']['zzgl_mwst'] = summe_zzgl_match.group(1)

            summe_inkl_match = re.search(r'Summe inkl\. MwSt\s*:\s*</td>\s*<td[^>]*>\s*([\d,]+)\s*EUR', page_text)
            if summe_inkl_match:
                details['summen']['inkl_mwst'] = summe_inkl_match.group(1)
        except Exception as e:
            pass

        # Kommentare
        try:
            kommentar_match = re.search(r'Lokale Bestell-Nr\.\s*:\s*</td>\s*<td[^>]*>\s*([^<]+)', page_text)
            if kommentar_match:
                details['kommentare']['lokale_nr'] = kommentar_match.group(1).strip()
        except Exception as e:
            pass

        return details

    except Exception as e:
        log(f"      ❌ Fehler bei {bestellnummer}: {e}")
        return details

def phase2_scrape_all_details(driver, bestellungen):
    """Phase 2: Scrape Details für alle gesammelten URLs"""
    log("\n" + "="*80)
    log("📋 PHASE 2: SCRAPE DETAILS FÜR ALLE BESTELLUNGEN")
    log("="*80)

    if TEST_MODE:
        bestellungen = bestellungen[:3]
        log(f"⚠️  TEST-MODUS: Nur erste 3 Bestellungen")

    all_details = []
    total = len(bestellungen)
    errors = 0

    for idx, bestellung_info in enumerate(bestellungen, 1):
        log(f"\n[{idx}/{total}] {bestellung_info['nummer']}")
        log("-" * 40)

        try:
            details = extract_bestellung_details(driver, bestellung_info)
            all_details.append(details)

            # Mini-Summary
            log(f"   ✅ Absender: {details['absender'].get('code', 'N/A')}")
            log(f"   ✅ Empfänger: {details['empfaenger'].get('code', 'N/A')}")
            log(f"   ✅ Positionen: {len(details['positionen'])}")
            log(f"   ✅ Datum: {details['historie'].get('bestelldatum', 'N/A')}")

            # Progress
            progress_pct = (idx / total) * 100
            log(f"   📊 Progress: {progress_pct:.1f}% ({idx}/{total})")

            # Progress speichern (alle 10 Bestellungen)
            if idx % 10 == 0:
                save_progress(all_details, idx, total)

        except Exception as e:
            log(f"   ❌ Fehler: {e}")
            errors += 1
            all_details.append({
                'bestellnummer': bestellung_info['nummer'],
                'url': bestellung_info['url'],
                'error': str(e)
            })

        time.sleep(1)

    log(f"\n{'='*80}")
    log(f"📊 PHASE 2 ABGESCHLOSSEN:")
    log(f"   - {len(all_details)} Bestellungen verarbeitet")
    log(f"   - {errors} Fehler")
    log(f"   - Erfolgsrate: {((total-errors)/total*100):.1f}%")
    log(f"{'='*80}")

    return all_details

def save_progress(details, current, total):
    """Speichert Zwischenstand"""
    try:
        progress_data = {
            'timestamp': datetime.now().isoformat(),
            'current': current,
            'total': total,
            'progress_pct': (current / total) * 100,
            'details': details
        }
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
        log(f"   💾 Progress gespeichert: {current}/{total}")
    except Exception as e:
        log(f"   ⚠️  Progress-Speicherung fehlgeschlagen: {e}")

def save_results(details):
    """Speichert finale Ergebnisse als JSON"""
    log(f"\n💾 SPEICHERE FINALE ERGEBNISSE")
    log("="*80)

    data = {
        'timestamp': datetime.now().isoformat(),
        'anzahl_bestellungen': len(details),
        'bestellungen': details
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    log(f"✅ Gespeichert: {OUTPUT_FILE}")

    # Statistik
    total_positionen = sum(len(d.get('positionen', [])) for d in details)
    bestellungen_mit_positionen = sum(1 for d in details if len(d.get('positionen', [])) > 0)
    bestellungen_mit_fehlern = sum(1 for d in details if 'error' in d)

    log(f"\n📊 FINALE STATISTIK:")
    log(f"   - Bestellungen gesamt: {len(details)}")
    log(f"   - Bestellungen mit Positionen: {bestellungen_mit_positionen} ({bestellungen_mit_positionen/len(details)*100:.1f}%)")
    log(f"   - Bestellungen mit Fehlern: {bestellungen_mit_fehlern}")
    log(f"   - Positionen gesamt: {total_positionen}")
    if bestellungen_mit_positionen > 0:
        log(f"   - Ø Positionen/Bestellung: {total_positionen/bestellungen_mit_positionen:.1f}")

def main():
    log("\n" + "="*80)
    log("🚀 STELLANTIS SERVICE BOX - 2-PHASEN SCRAPER V2 (MIT VALIDIERUNG)")
    log("="*80)
    log(f"📋 Konfiguration:")
    log(f"   - TEST_MODE: {TEST_MODE}")
    log(f"   - MAX_PAGES: {MAX_PAGES}")
    log("="*80)

    driver = None

    try:
        credentials = load_credentials()
        driver = setup_driver()

        # Login & Navigation
        if not login_and_navigate(driver, credentials):
            log("\n❌ Login/Navigation fehlgeschlagen!")
            return False

        # "Mehr Bestellungen anzeigen" klicken MIT VALIDIERUNG
        if not click_mehr_bestellungen_mit_validierung(driver):
            log("\n⚠️  'Mehr Bestellungen' konnte nicht aktiviert werden!")
            log("   Fahre mit Standard-Ansicht fort...")

        # PHASE 1: Sammle alle URLs
        all_bestellungen = phase1_collect_all_urls(driver)

        if not all_bestellungen:
            log("\n❌ Keine Bestellungen gefunden!")
            return False

        # PHASE 2: Scrape Details
        details = phase2_scrape_all_details(driver, all_bestellungen)

        if details:
            save_results(details)
            log("\n" + "="*80)
            log("✅ 2-PHASEN SCRAPER V2 ERFOLGREICH!")
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
            log(f"📂 Progress: {PROGRESS_FILE}")
            log(f"📂 Screenshots: {SCREENSHOTS_DIR}")
            log(f"📂 Log-File: {LOG_FILE}")
            log("\n🔚 Schließe Browser...")
            driver.quit()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
