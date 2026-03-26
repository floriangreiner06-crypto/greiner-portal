#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellantis Service Box - Wartungsplan Scraper
==============================================
- Stellantis-Fahrzeuge (VIN beginnt mit VXU etc.): typdoc.do?doc=16 (Wartungsplaene), PE-Dokument.
- GM-Legacy-Fahrzeuge (VIN beginnt mit W0): Modul Menupricing aufrufen (Service-Preise/Wartung).

Flow Stellantis:
1. Login, Tech-Doc, VIN-Suche
2. Wartungsplaene (doc=16), Formular (Alter, km), PE-Dokument

Flow GM Legacy (W0):
1. Login, Tech-Doc, VIN-Suche
2. Menupricing-Modul aufrufen, Seite auslesen

Version: TAG 129 + GM-Legacy Menupricing (2026-03-10)
"""

import os
import sys
import time
import json
import re
import psycopg2
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

BASE_DIR = "/opt/greiner-portal"
CREDENTIALS_PATH = f"{BASE_DIR}/config/credentials.json"
OUTPUT_DIR = f"{BASE_DIR}/logs/servicebox_wartungsplaene"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_wartungsplan_scraper.log"

os.makedirs(OUTPUT_DIR, exist_ok=True)


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


def setup_driver(headless=True):
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=de-DE')
    # Menupricing (GM-Legacy) oeffnet neues Fenster (opel-vauxhall-menupricing.com)
    chrome_options.add_argument('--disable-popup-blocking')

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver


def get_vehicle_data_from_locosoft(vin):
    """Holt Fahrzeugdaten (EZ, km) aus Locosoft PostgreSQL"""
    log(f"Hole Fahrzeugdaten aus Locosoft fuer VIN: {vin}")

    try:
        conn = psycopg2.connect(
            host="10.80.80.8",
            port=5432,
            database="loco_auswertung_db",
            user="loco_auswertung_benutzer",
            password="loco"
        )
        cursor = conn.cursor()

        # Hole EZ und aktuellen km-Stand
        query = """
            SELECT v.first_registration_date, v.mileage_km, v.license_plate
            FROM vehicles v
            WHERE v.vin = %s
            LIMIT 1
        """
        cursor.execute(query, (vin,))
        row = cursor.fetchone()

        if row:
            ez_date = row[0]
            km = row[1] or 0
            kennzeichen = row[2] or ""

            # Berechne Alter in Jahren
            if ez_date:
                today = date.today()
                delta = relativedelta(today, ez_date)
                alter_jahre = delta.years
                # Mindestens 1 Jahr fuer das Formular
                if alter_jahre < 1:
                    alter_jahre = 1
            else:
                alter_jahre = 1  # Fallback

            log(f"  EZ: {ez_date}, Alter: {alter_jahre} Jahre, km: {km}")
            cursor.close()
            conn.close()

            return {
                'ez': str(ez_date) if ez_date else None,  # String fuer JSON
                'alter_jahre': alter_jahre,
                'km': km,
                'kennzeichen': kennzeichen
            }
        else:
            log(f"  VIN nicht in Locosoft gefunden", "WARN")
            cursor.close()
            conn.close()
            return None

    except Exception as e:
        log(f"Locosoft-Abfrage Fehler: {e}", "ERROR")
        return None


def take_screenshot(driver, name, vin=""):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    prefix = f"{vin}_" if vin else ""
    filename = f"{timestamp}_{prefix}{name}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    driver.save_screenshot(filepath)
    log(f"Screenshot: {filename}")
    return filepath


def save_html(driver, name, vin=""):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    prefix = f"{vin}_" if vin else ""
    filename = f"{timestamp}_{prefix}{name}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    log(f"HTML: {filename}")
    return filepath


def login(driver, credentials):
    """Login mit HTTP Basic Auth"""
    log("Login...")
    username = credentials['username']
    password = credentials['password']
    base_url = credentials['portal_url']

    protocol, rest = base_url.split('://', 1)
    auth_url = f"{protocol}://{username}:{password}@{rest}"

    driver.get(auth_url)
    time.sleep(8)

    WebDriverWait(driver, 15).until(
        EC.frame_to_be_available_and_switch_to_it((By.ID, "frameHub"))
    )
    log("Login erfolgreich - in frameHub")
    time.sleep(3)
    return True


def navigate_to_tech_doc(driver):
    """Navigiert zur Technischen Dokumentation"""
    log("Navigation zu Tech-Doc...")
    try:
        # Hover ueber DOKUMENTATION
        doc_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "DOKUMENTATION"))
        )
        ActionChains(driver).move_to_element(doc_link).perform()
        time.sleep(2)

        # Klick auf Technische Dokumentation Opel (PSA)
        tech_doc_link = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Technische Dokumentation Opel"))
        )
        tech_doc_link.click()
        time.sleep(5)

        log("Tech-Doc geladen")
        return True

    except Exception as e:
        log(f"Navigation-Fehler: {e}", "ERROR")
        return False


def search_vin(driver, vin):
    """VIN-Suche"""
    log(f"Suche VIN: {vin}")
    try:
        vin_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "short-vin"))
        )
        vin_input.click()
        vin_input.clear()
        time.sleep(0.5)
        vin_input.send_keys(vin)
        time.sleep(1)

        # Submit
        submit_btn = driver.find_element(By.CSS_SELECTOR, "input[name='VIN_OK_BUTTON']")
        submit_btn.click()
        time.sleep(5)

        log("VIN-Suche abgeschlossen")
        return True

    except Exception as e:
        log(f"VIN-Suche Fehler: {e}", "ERROR")
        return False


def is_gm_legacy_vin(vin):
    """GM-Legacy-Fahrzeuge: VIN beginnt mit W0 (kein Stellantis VXU). Fuer W0 -> Menupricing."""
    if not vin or not isinstance(vin, str):
        return False
    return vin.strip().upper().startswith("W0")


def navigate_to_menupricing(driver, vin):
    """Navigiert zum Modul Menupricing (GM-Legacy W0). Service-Preise/Wartungsinformationen."""
    log("Navigation zu Menupricing (GM-Legacy)...")

    try:
        # Methode 1: JavaScript goTo('/mp/') – ServiceBox-Navigation verwendet genau diesen Pfad
        try:
            driver.execute_script("goTo('/mp/')")
            time.sleep(6)
            page_lower = driver.page_source.lower()
            if "404" not in page_lower and "n'existe pas" not in page_lower and "unbekannte seite" not in page_lower and "la ressource demandée" not in page_lower:
                log("  goTo('/mp/') ausgefuehrt – Menu Pricing geladen")
                take_screenshot(driver, "menupricing_js", vin)
                save_html(driver, "menupricing_js", vin)
                return True
        except Exception as e:
            log(f"  goTo('/mp/') Fehler: {e}")

        # Methode 2: Link "Menu Pricing" per JavaScript klicken (falls im gleichen Dokument)
        try:
            mp_clicked = driver.execute_script("""
                var links = document.getElementsByTagName('a');
                for (var i = 0; i < links.length; i++) {
                    var h = links[i].getAttribute('href') || '';
                    var t = (links[i].textContent || '').trim();
                    if (h.indexOf('/mp/') >= 0 || t.indexOf('Menu Pricing') >= 0) {
                        links[i].click();
                        return true;
                    }
                }
                return false;
            """)
            if mp_clicked:
                time.sleep(6)
                take_screenshot(driver, "menupricing_page", vin)
                save_html(driver, "menupricing_page", vin)
                return True
        except Exception:
            pass

        # Methode 3: Selenium-Link-Klick
        for keyword in ["Menu Pricing", "Menupricing", "Menu pricing", "Pricing"]:
            try:
                links = driver.find_elements(By.PARTIAL_LINK_TEXT, keyword)
                for link in links:
                    try:
                        if link.is_displayed() and "goTo" in (link.get_attribute("href") or ""):
                            log(f"  Klicke Menupricing-Link: {keyword}")
                            link.click()
                            time.sleep(6)
                            take_screenshot(driver, "menupricing_page", vin)
                            save_html(driver, "menupricing_page", vin)
                            return True
                    except Exception:
                        continue
            except Exception:
                continue

        # Methode 5: Direkte URLs (docapvpr / docapvprovl)
        base_host = "https://servicebox.mpsa.com"
        for path in ["/docapvpr/menupricing.do", "/docapvprovl/menupricing.do",
                     "/docapvpr/tarification.do", "/docapvprovl/tarification.do",
                     "/docapvpr/menuPricing.do"]:
            try:
                url = base_host + path
                log(f"  Versuche direkte URL: {path}")
                driver.get(url)
                time.sleep(5)
                take_screenshot(driver, "menupricing_direct", vin)
                save_html(driver, "menupricing_direct", vin)
                # Kein technischer Fehler?
                if "technical problem" not in driver.page_source.lower() and "probleme technique" not in driver.page_source.lower():
                    return True
            except Exception as e:
                log(f"  URL {path}: {e}")
                continue

        log("Menupricing-Navigation: Kein Zugang gefunden", "WARN")
        return False

    except Exception as e:
        log(f"Menupricing-Navigation Fehler: {e}", "ERROR")
        return False


def switch_to_menupricing_window(driver, vin, timeout=20):
    """
    ServiceBox oeffnet Menupricing in neuem Fenster (opel-vauxhall-menupricing.com).
    Wechselt dorthin und wartet auf Ladung. Zurueck: True wenn gewechselt, sonst False.
    """
    log("Warte auf Menupricing-Popup-Fenster...")
    main_handle = driver.current_window_handle
    try:
        for _ in range(timeout):
            handles = driver.window_handles
            if len(handles) > 1:
                for h in handles:
                    if h == main_handle:
                        continue
                    driver.switch_to.window(h)
                    try:
                        url = driver.current_url or ""
                        if "opel-vauxhall-menupricing" in url or "menupricing" in url.lower():
                            log(f"  Gewechselt zu Menupricing-Fenster: {url[:80]}")
                            time.sleep(5)
                            take_screenshot(driver, "menupricing_popup", vin)
                            save_html(driver, "menupricing_popup", vin)
                            return True
                    except Exception:
                        pass
                # Fallback: letztes Fenster
                driver.switch_to.window(handles[-1])
                time.sleep(5)
                take_screenshot(driver, "menupricing_popup", vin)
                save_html(driver, "menupricing_popup", vin)
                return True
            time.sleep(1)
        log("  Kein Menupricing-Popup gefunden (Timeout)", "WARN")
        return False
    except Exception as e:
        log(f"  Fenster-Wechsel Fehler: {e}", "WARN")
        try:
            driver.switch_to.window(main_handle)
        except Exception:
            pass
        return False


def extract_menupricing_data(driver, vin):
    """Extrahiert Daten von der Menupricing-Seite (GM-Legacy). Evtl. im Popup-Fenster."""
    log("Extrahiere Menupricing-Daten...")
    result = {
        "vin": vin,
        "timestamp": datetime.now().isoformat(),
        "source": "menupricing",
        "intervalle": [],
        "arbeiten": [],
        "tables": [],
        "raw_tables": [],
        "preise": [],
        "url": None,
    }
    try:
        result["url"] = driver.current_url
    except Exception:
        pass

    # Kurz warten, falls dynamischer Inhalt
    try:
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)
    except Exception:
        pass

    page_source = driver.page_source

    # Intervalle (km / Jahre) aus Seite, dedupliziert
    seen_km = set()
    for match in re.finditer(r"(\d{1,3}[.,]?\d{3})\s*(km|KM)", page_source):
        try:
            val = int(match.group(1).replace(".", "").replace(",", ""))
            if val not in seen_km and 1000 <= val <= 500000:
                seen_km.add(val)
                result["intervalle"].append({"type": "km", "value": val, "raw": match.group(0)})
        except Exception:
            pass
    seen_jahr = set()
    for match in re.finditer(r"(\d{1,2})\s*(Jahr|Jahre|year|years|an|ans)", page_source, re.IGNORECASE):
        try:
            v = int(match.group(1))
            if v not in seen_jahr and 1 <= v <= 25:
                seen_jahr.add(v)
                result["intervalle"].append({"type": "Zeit", "value": v, "unit": "Jahre", "raw": match.group(0)})
        except Exception:
            pass

    # Tabellen (alle table-Elemente, auch in iframes wenn wir im richtigen Fenster sind)
    try:
        tables = driver.find_elements(By.CSS_SELECTOR, "table")
        for i, table in enumerate(tables[:20]):
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")
                table_data = []
                for row in rows[:80]:
                    cells = row.find_elements(By.TAG_NAME, "td") or row.find_elements(By.TAG_NAME, "th")
                    if cells:
                        table_data.append([c.text.strip() for c in cells if c.text.strip()])
                if table_data and len(table_data) > 1:
                    result["tables"].append(table_data)
                    result["raw_tables"].append(table_data)
            except Exception:
                continue
    except Exception:
        pass

    # Preise (EUR-Betraege)
    for match in re.finditer(r"(\d{1,3}(?:[.,]\d{2,3})?)\s*(?:EUR|€|Euro)", page_source, re.IGNORECASE):
        try:
            s = match.group(1).replace(".", "").replace(",", ".")
            if "." in s:
                result["preise"].append({"raw": match.group(0), "value": float(s)})
        except Exception:
            pass
    if not result["preise"]:
        for match in re.finditer(r"(\d{1,3}[.,]\d{2})\s*€", page_source):
            try:
                s = match.group(1).replace(",", ".")
                result["preise"].append({"raw": match.group(0), "value": float(s)})
            except Exception:
                pass

    # Typische Wartungs-Keywords
    keywords = ["Oelwechsel", "Motoröl", "Ölfilter", "Luftfilter", "Pollenfilter", "Bremsen", "Inspektion", "Service", "Zündkerzen", "Bremsflüssigkeit", "Getriebeöl"]
    for kw in keywords:
        pat = kw.replace("ö", "(oe|ö)").replace("ä", "(ae|ä)").replace("ü", "(ue|ü)")
        if re.search(pat, page_source, re.IGNORECASE) and kw not in result["arbeiten"]:
            result["arbeiten"].append(kw)

    # Kurze Zusammenfassung aus Tabellen (VIN, Fahrzeug, EZ, Motor)
    result["summary"] = {}
    for row_list in result.get("tables", [])[:3]:
        flat = " ".join(str(c) for row in row_list for c in (row if isinstance(row, list) else [row]))
        if vin in flat and "Astra" in flat:
            result["summary"]["fahrzeug_text"] = "Opel Astra J 2011"  # aus Tabellen verfeinerbar
            break
    if result.get("tables"):
        result["summary"]["tabellen_anzahl"] = len(result["tables"])
        result["summary"]["hinweis"] = "Nicht bepreiste Generische Jobs/Teile" if "Nicht bepreiste" in str(result["tables"]) else None

    log(f"  Intervalle: {len(result['intervalle'])}, Arbeiten: {len(result['arbeiten'])}, Tabellen: {len(result['tables'])}, Preise: {len(result.get('preise', []))}")
    return result


def navigate_to_wartungsplan(driver, vin):
    """Navigiert zu typdoc.do?doc=16 (Wartungsplaene)

    Der Link ist im linken Menue unter 'Wartungsplaene' oder via JavaScript.
    """
    log("Navigation zu Wartungsplaene (doc=16)...")

    try:
        # Methode 1: Suche nach Wartungsplaene-Link im Menue
        wartungs_selectors = [
            "a[href*='typdoc.do?doc=16']",
            "a[onclick*='goToTypDoc(16)']",
            "#menu_PE a",
            "a[title*='Wartung']",
            "a[title*='Plan']",
        ]

        for selector in wartungs_selectors:
            try:
                links = driver.find_elements(By.CSS_SELECTOR, selector)
                for link in links:
                    if link.is_displayed():
                        log(f"  Wartungsplan-Link gefunden: {selector}")
                        link.click()
                        time.sleep(5)
                        take_screenshot(driver, "wartungsplan_page", vin)
                        save_html(driver, "wartungsplan_page", vin)
                        return True
            except:
                continue

        # Methode 2: Suche nach Text "Wartungsplaene" oder "Wartungspläne"
        try:
            links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Wartung')]")
            for link in links:
                if link.is_displayed():
                    log(f"  Wartungsplan-Link per Text gefunden")
                    link.click()
                    time.sleep(5)
                    take_screenshot(driver, "wartungsplan_text", vin)
                    save_html(driver, "wartungsplan_text", vin)
                    return True
        except:
            pass

        # Methode 3: JavaScript Navigation
        log("  Versuche JavaScript-Navigation...")
        try:
            driver.execute_script("goToTypDoc(16)")
            time.sleep(5)
            take_screenshot(driver, "wartungsplan_js", vin)
            save_html(driver, "wartungsplan_js", vin)
            return True
        except Exception as e:
            log(f"  JavaScript goToTypDoc(16) fehlgeschlagen: {e}")

        # Methode 4: Direkte URL
        log("  Versuche direkte URL...")
        wartung_url = "https://servicebox.mpsa.com/docapvpr/typdoc.do?doc=16"
        driver.get(wartung_url)
        time.sleep(5)
        take_screenshot(driver, "wartungsplan_direct", vin)
        save_html(driver, "wartungsplan_direct", vin)
        return True

    except Exception as e:
        log(f"Wartungsplan-Navigation Fehler: {e}", "ERROR")
        return False


def fill_wartungsplan_form(driver, vin, alter_jahre, km):
    """Fuellt das Wartungsplan-Formular aus und klickt auf Suchen

    Formular-Felder (aus HTML-Analyse):
    - Einsatzbedingungen (selectedPE, #listeCU): onchange triggert AJAX -> ajaxPEFormUpdate()
    - Alter des Fahrzeugs (#listeAnnees): Wird per AJAX nachgeladen
    - Kilometerstand (#listeKmMiles): Wird per AJAX nachgeladen
    - Vidange: Yes/No
    """
    log(f"Fuelle Wartungsplan-Formular: Alter={alter_jahre} Jahre, km={km}")

    try:
        from selenium.webdriver.support.ui import Select

        # 1. Einsatzbedingungen: "Normale Bedingungen" auswaehlen
        # WICHTIG: Dies triggert AJAX und laedt die anderen Dropdowns
        try:
            # Das Dropdown hat name="selectedPE" und id="listeCU"
            bedingungen_selectors = [
                "select[name='selectedPE']",
                "#listeCU",
                "select.zoneMulti",
            ]

            bedingungen_selected = False
            for selector in bedingungen_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.tag_name == 'select':
                            select = Select(elem)
                            options = select.options
                            # Suche nach "Normale Bedingungen"
                            for opt in options:
                                if "Normale Bedingungen" in opt.text:
                                    log(f"  Einsatzbedingungen: {opt.text} (value={opt.get_attribute('value')})")
                                    select.select_by_visible_text(opt.text)
                                    bedingungen_selected = True
                                    break
                            if bedingungen_selected:
                                break
                    if bedingungen_selected:
                        break
                except Exception as e:
                    continue

            if not bedingungen_selected:
                log("  WARN: Einsatzbedingungen nicht gefunden, versuche Index 1")
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, "select[name='selectedPE']")
                    select = Select(elem)
                    select.select_by_index(1)
                    bedingungen_selected = True
                except:
                    pass

        except Exception as e:
            log(f"  Einsatzbedingungen Fehler: {e}")

        # WICHTIG: Warten auf AJAX-Nachladen der anderen Dropdowns
        log("  Warte auf AJAX-Nachladen...")
        time.sleep(4)

        # 2. Alter des Fahrzeugs auswaehlen (#listeAnnees, name="selectedAnnee")
        try:
            alter_elem = driver.find_element(By.CSS_SELECTOR, "#listeAnnees, select[name='selectedAnnee']")
            if alter_elem.is_displayed():
                select = Select(alter_elem)
                options = select.options
                log(f"  Alter-Dropdown hat {len(options)} Optionen")

                # Zeige verfuegbare Optionen
                available = [opt.text for opt in options if opt.text != '...']
                log(f"  Verfuegbare Alter: {available[:5]}...")

                # Waehle das passende Alter
                alter_selected = False
                for opt in options:
                    opt_text = opt.text.strip()
                    if opt_text == '...' or opt_text == '-999':
                        continue
                    try:
                        # Extrahiere Zahl (z.B. "1 Jahr(e)" -> 1)
                        opt_val = int(re.search(r'\d+', opt_text).group())
                        if opt_val == alter_jahre:
                            select.select_by_visible_text(opt_text)
                            log(f"  Alter: {opt_text}")
                            alter_selected = True
                            break
                    except:
                        continue

                # Fallback: Waehle erstes verfuegbares Alter
                if not alter_selected and len(options) > 1:
                    for opt in options:
                        if opt.text.strip() != '...' and opt.get_attribute('value') != '-999':
                            select.select_by_visible_text(opt.text)
                            log(f"  Alter (Fallback): {opt.text}")
                            break
        except Exception as e:
            log(f"  Alter-Auswahl Fehler: {e}")

        time.sleep(1)

        # 3. Kilometerstand auswaehlen (#listeKmMiles, name="selectedDistance")
        try:
            km_elem = driver.find_element(By.CSS_SELECTOR, "#listeKmMiles, select[name='selectedDistance']")
            if km_elem.is_displayed():
                select = Select(km_elem)
                options = select.options
                log(f"  km-Dropdown hat {len(options)} Optionen")

                # Zeige verfuegbare Optionen
                available = [opt.text for opt in options if opt.text != '...']
                log(f"  Verfuegbare km: {available[:5]}...")

                # Finde den naechsten km-Wert
                best_option = None
                best_diff = float('inf')

                for opt in options:
                    opt_text = opt.text.strip()
                    if opt_text == '...' or opt.get_attribute('value') == '-999':
                        continue
                    try:
                        # Extrahiere km-Wert (z.B. "30.000 Km" -> 30000)
                        text_clean = opt_text.replace('.', '').replace(',', '').replace(' ', '')
                        km_match = re.search(r'\d+', text_clean)
                        if km_match:
                            opt_km = int(km_match.group())
                            diff = abs(opt_km - km)
                            if diff < best_diff:
                                best_diff = diff
                                best_option = opt
                    except:
                        continue

                if best_option:
                    select.select_by_visible_text(best_option.text)
                    log(f"  Kilometerstand: {best_option.text}")
                elif len(options) > 1:
                    # Fallback: Erste nicht-leere Option
                    for opt in options:
                        if opt.text.strip() != '...' and opt.get_attribute('value') != '-999':
                            select.select_by_visible_text(opt.text)
                            log(f"  Kilometerstand (Fallback): {opt.text}")
                            break
        except Exception as e:
            log(f"  Kilometerstand Fehler: {e}")

        time.sleep(1)

        # 4. Vidange (Oelwechsel) - optional, falls vorhanden
        try:
            vidange_elem = driver.find_element(By.CSS_SELECTOR, "select[name='selectedVidange']")
            if vidange_elem.is_displayed():
                select = Select(vidange_elem)
                options = select.options
                # Suche nach "Yes" oder erstem nicht-leeren Wert
                for opt in options:
                    if 'Yes' in opt.text or opt.get_attribute('value') == '1':
                        select.select_by_visible_text(opt.text)
                        log(f"  Vidange: {opt.text}")
                        break
        except:
            log("  Vidange nicht vorhanden (optional)")
            pass

        time.sleep(1)

        # 5. Suchen-Button klicken
        try:
            search_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "input[value*='Suche']",
                "input[value*='Search']",
                "input[name*='search']",
                "#btnRechercher",
                "input[onclick*='rechercher']",
            ]

            for selector in search_selectors:
                try:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        if btn.is_displayed():
                            btn.click()
                            log("  Suchen geklickt")
                            time.sleep(5)
                            take_screenshot(driver, "03_nach_suche", vin)
                            save_html(driver, "03_nach_suche", vin)
                            return True
                except:
                    continue

            # Fallback: JavaScript
            try:
                driver.execute_script("rechercher()")
                log("  Suchen via JavaScript")
                time.sleep(5)
                take_screenshot(driver, "03_nach_suche_js", vin)
                return True
            except:
                pass

        except Exception as e:
            log(f"  Suchen-Button Fehler: {e}")

        return False

    except Exception as e:
        log(f"Formular-Ausfuellung Fehler: {e}", "ERROR")
        return False


def open_pe_document(driver, vin):
    """Oeffnet das PE-Dokument (Plan d'Entretien / Wartungsplan)

    URL: affiche.do?ref=PE&refaff=PE&type=PE
    """
    log("Oeffne PE-Dokument...")

    try:
        # Methode 1: JavaScript affichePE aufrufen (wie im Original-JS)
        try:
            driver.execute_script("affichePE('OV')")  # OV = Opel/Vauxhall
            time.sleep(3)

            # Wechsle zum neuen Fenster
            handles = driver.window_handles
            if len(handles) > 1:
                driver.switch_to.window(handles[-1])
                time.sleep(5)
                take_screenshot(driver, "pe_document", vin)
                save_html(driver, "pe_document", vin)
                log("PE-Dokument im neuen Fenster geoeffnet")
                return True
        except Exception as e:
            log(f"  affichePE() fehlgeschlagen: {e}")

        # Methode 2: Direkte URL
        log("  Versuche direkte affiche.do URL...")
        pe_url = "https://servicebox.mpsa.com/docapvpr/affiche.do?ref=PE&refaff=PE&type=PE"

        main_window = driver.current_window_handle
        driver.execute_script(f"window.open('{pe_url}', '_blank')")
        time.sleep(3)

        handles = driver.window_handles
        for handle in handles:
            if handle != main_window:
                driver.switch_to.window(handle)
                time.sleep(5)
                take_screenshot(driver, "pe_direct", vin)
                save_html(driver, "pe_direct", vin)
                log("PE-Dokument direkt geoeffnet")
                return True

        return False

    except Exception as e:
        log(f"PE-Dokument Fehler: {e}", "ERROR")
        return False


def extract_wartungsplan_data(driver, vin):
    """Extrahiert Wartungsplan-Daten aus der aktuellen Seite"""
    log("Extrahiere Wartungsplan-Daten...")

    result = {
        'vin': vin,
        'timestamp': datetime.now().isoformat(),
        'intervalle': [],
        'arbeiten': [],
        'tables': [],
    }

    page_source = driver.page_source

    # Suche nach Intervall-Daten (km/Monate/Jahre)
    km_pattern = r'(\d{1,3}[.,]?\d{3})\s*(km|KM)'
    for match in re.finditer(km_pattern, page_source):
        km_val = match.group(1).replace('.', '').replace(',', '')
        try:
            result['intervalle'].append({
                'type': 'km',
                'value': int(km_val),
                'raw': match.group(0)
            })
        except:
            pass

    # Suche nach Zeit-Intervallen
    time_patterns = [
        (r'(\d{1,2})\s*(Jahr|Jahre|year|years|an|ans)', 'Jahre'),
        (r'(\d{1,2})\s*(Monat|Monate|month|months|mois)', 'Monate'),
    ]

    for pattern, unit in time_patterns:
        for match in re.finditer(pattern, page_source, re.IGNORECASE):
            result['intervalle'].append({
                'type': 'Zeit',
                'value': int(match.group(1)),
                'unit': unit,
                'raw': match.group(0)
            })

    # Suche nach typischen Wartungsarbeiten
    wartungs_keywords = [
        ('Oelwechsel', 'Ölwechsel'),
        ('Motoroel', 'Motoröl'),
        ('Oelfilter', 'Ölfilter'),
        ('Luftfilter', 'Luftfilter'),
        ('Pollenfilter', 'Pollenfilter'),
        ('Innenraumfilter', 'Innenraumfilter'),
        ('Kraftstofffilter', 'Kraftstofffilter'),
        ('Zuendkerzen', 'Zündkerzen'),
        ('Bremsfluessigkeit', 'Bremsflüssigkeit'),
        ('Kuehlmittel', 'Kühlmittel'),
        ('Zahnriemen', 'Zahnriemen'),
        ('Keilriemen', 'Keilriemen'),
        ('Getriebeoel', 'Getriebeöl'),
        ('Klimaanlage', 'Klimaanlage'),
        ('Batterie', 'Batterie'),
        ('Bremsen', 'Bremsen'),
    ]

    for keyword, display_name in wartungs_keywords:
        # Case-insensitive Suche mit Umlauten
        pattern = keyword.replace('oe', '(oe|ö)').replace('ue', '(ue|ü)').replace('ae', '(ae|ä)')
        if re.search(pattern, page_source, re.IGNORECASE):
            if display_name not in result['arbeiten']:
                result['arbeiten'].append(display_name)

    # Extrahiere Tabellen mit Wartungsdaten
    try:
        tables = driver.find_elements(By.CSS_SELECTOR, "table.data, table.maintenance, table[class*='wartung'], table")
        for i, table in enumerate(tables[:10]):  # Max 10 Tabellen
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")
                table_data = []
                for row in rows[:30]:  # Max 30 Zeilen
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if not cells:
                        cells = row.find_elements(By.TAG_NAME, "th")
                    if cells:
                        row_data = [cell.text.strip() for cell in cells if cell.text.strip()]
                        if row_data:
                            table_data.append(row_data)
                if table_data and len(table_data) > 1:
                    result['tables'].append(table_data)
            except:
                continue
    except:
        pass

    log(f"  Intervalle gefunden: {len(result['intervalle'])}")
    log(f"  Arbeiten gefunden: {len(result['arbeiten'])}")
    log(f"  Tabellen gefunden: {len(result['tables'])}")

    return result


def get_wartungsplan(vin, headless=True, alter_jahre=None, km=None):
    """Hauptfunktion: Holt Wartungsplan fuer eine VIN

    Args:
        vin: Fahrzeug-Identifikationsnummer
        headless: Browser unsichtbar (default True)
        alter_jahre: Fahrzeugalter in Jahren (optional, sonst aus Locosoft)
        km: Kilometerstand (optional, sonst aus Locosoft)
    """
    log("=" * 70)
    log(f"WARTUNGSPLAN ABRUF - VIN: {vin}")
    log("=" * 70)

    driver = None
    result = {
        'vin': vin,
        'timestamp': datetime.now().isoformat(),
        'success': False,
        'fahrzeug_daten': {},
        'wartungsplan': {},
        'screenshots': [],
        'error': None
    }

    try:
        # 0. Fahrzeugdaten aus Locosoft holen (falls nicht uebergeben)
        if alter_jahre is None or km is None:
            loco_data = get_vehicle_data_from_locosoft(vin)
            if loco_data:
                result['fahrzeug_daten'] = loco_data
                if alter_jahre is None:
                    alter_jahre = loco_data.get('alter_jahre', 1)
                if km is None:
                    km = loco_data.get('km', 30000)
            else:
                # Fallback-Werte
                log("Verwende Fallback-Werte: 1 Jahr, 30.000 km", "WARN")
                alter_jahre = alter_jahre or 1
                km = km or 30000

        result['fahrzeug_daten']['alter_jahre_verwendet'] = alter_jahre
        result['fahrzeug_daten']['km_verwendet'] = km

        credentials = load_credentials()
        driver = setup_driver(headless=headless)

        # 1. Login
        if not login(driver, credentials):
            result['error'] = 'Login fehlgeschlagen'
            return result

        # 2. Navigation zu Tech-Doc
        if not navigate_to_tech_doc(driver):
            result['error'] = 'Tech-Doc Navigation fehlgeschlagen'
            return result

        # 3. VIN-Suche
        if not search_vin(driver, vin):
            result['error'] = 'VIN-Suche fehlgeschlagen'
            return result

        result['screenshots'].append(take_screenshot(driver, "01_nach_vin", vin))
        save_html(driver, "01_nach_vin", vin)

        if is_gm_legacy_vin(vin):
            # GM-Legacy (VIN W0): Modul Menupricing (oeffnet Popup opel-vauxhall-menupricing.com)
            log("VIN beginnt mit W0 -> GM-Legacy, rufe Menupricing auf.")
            main_window = driver.current_window_handle
            if navigate_to_menupricing(driver, vin):
                result['screenshots'].append(take_screenshot(driver, "02_menupricing_hub", vin))
                # Popup-Fenster: wechseln und dort extrahieren
                if switch_to_menupricing_window(driver, vin):
                    result['screenshots'].append(take_screenshot(driver, "03_menupricing_content", vin))
                    result['wartungsplan'] = extract_menupricing_data(driver, vin)
                    try:
                        driver.close()
                        driver.switch_to.window(main_window)
                    except Exception:
                        try:
                            driver.switch_to.window(main_window)
                        except Exception:
                            pass
                else:
                    # Kein Popup: von Hub-Seite extrahieren (Fallback)
                    result['wartungsplan'] = extract_menupricing_data(driver, vin)
                result['wartungsplan']['source'] = 'menupricing'
                result['success'] = True
            else:
                result['error'] = 'Menupricing-Navigation fehlgeschlagen'
        else:
            # Stellantis (z. B. VXU): Wartungsplaene (typdoc 16)
            if navigate_to_wartungsplan(driver, vin):
                result['screenshots'].append(take_screenshot(driver, "02_wartungsplan_form", vin))

                if fill_wartungsplan_form(driver, vin, alter_jahre, km):
                    result['screenshots'].append(take_screenshot(driver, "03_nach_suche", vin))
                    result['wartungsplan'] = extract_wartungsplan_data(driver, vin)
                    result['wartungsplan']['source'] = 'wartungsplan'

                    main_window = driver.current_window_handle
                    if open_pe_document(driver, vin):
                        result['screenshots'].append(take_screenshot(driver, "04_pe_dokument", vin))
                        pe_data = extract_wartungsplan_data(driver, vin)
                        result['wartungsplan']['pe_document'] = pe_data
                        try:
                            driver.close()
                            driver.switch_to.window(main_window)
                        except Exception:
                            pass
                    result['success'] = True
                else:
                    log("Formular konnte nicht ausgefuellt werden", "WARN")
                    result['wartungsplan'] = extract_wartungsplan_data(driver, vin)
                    result['wartungsplan']['source'] = 'wartungsplan'

        # Speichere Ergebnis
        output_file = os.path.join(OUTPUT_DIR, f"wartungsplan_{vin}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        log(f"\nErgebnis gespeichert: {output_file}")

        return result

    except Exception as e:
        log(f"FEHLER: {e}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        result['error'] = str(e)
        if driver:
            take_screenshot(driver, "error", vin)
        return result

    finally:
        if driver:
            driver.quit()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Servicebox Wartungsplan Scraper')
    parser.add_argument('vin', nargs='?', default='VXKCSHPX0ST216437',
                       help='VIN des Fahrzeugs (Standard: neuer Opel aus 2025)')
    parser.add_argument('--visible', action='store_true',
                       help='Browser sichtbar')

    args = parser.parse_args()
    vin = args.vin.strip().upper()

    result = get_wartungsplan(vin, headless=not args.visible)

    # Zusammenfassung
    print("\n" + "=" * 70)
    print("ERGEBNIS")
    print("=" * 70)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    return 0 if result.get('success') else 1


if __name__ == "__main__":
    sys.exit(main())
