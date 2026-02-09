#!/usr/bin/env python3
"""
RepDoc (WM SE / Trost) Scraper
===============================
Scraper für RepDoc Katalog-System zur Teile-Suche und Preisabfrage.

Zugangsdaten:
- Benutzername: 1042953
- Passwort: Greiner1
- URL: https://www2.repdoc.com/DE/Login#Start

TAG 215: Erstellt für Integration in DRIVE Teile-Bereich
"""

import time
import re
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger(__name__)

# Zugangsdaten aus Umgebungsvariablen (TAG 215)
# Fallback auf Hardcoded-Werte für Entwicklung (NICHT für Produktion!)
# DRIVE-spezifischer Zugang: Greiner_drive / Drive2026!
REPDOC_USERNAME = os.getenv("REPDOC_USERNAME", "Greiner_drive")
REPDOC_PASSWORD = os.getenv("REPDOC_PASSWORD", "Drive2026!")
BASE_URL = "https://www2.repdoc.com/DE/Login#Start"
SEARCH_URL = "https://www2.repdoc.com/DE"  # Nach Login


class RepDocScraper:
    """
    RepDoc Scraper für Teile-Suche und Preisabfrage.
    
    Verwendet Selenium mit Chrome headless für Web-Scraping.
    """
    
    _instance = None
    _driver = None
    _logged_in = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.base_url = BASE_URL
        self.username = REPDOC_USERNAME
        self.password = REPDOC_PASSWORD
        
    def _ensure_driver(self):
        """Erstellt Chrome-Driver falls noch nicht vorhanden"""
        if RepDocScraper._driver is None:
            chrome_options = Options()
            chrome_options.binary_location = '/usr/bin/google-chrome'
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Expliziter ChromeDriver-Pfad (nicht im Gunicorn PATH)
            service = Service(executable_path='/usr/local/bin/chromedriver')
            RepDocScraper._driver = webdriver.Chrome(service=service, options=chrome_options)
            RepDocScraper._driver.set_page_load_timeout(30)
            RepDocScraper._logged_in = False
        return RepDocScraper._driver
        
    def _do_login(self):
        """Login bei RepDoc durchführen"""
        driver = self._ensure_driver()
        
        try:
            logger.info("RepDoc: Starte Login...")
            driver.get(self.base_url)
            time.sleep(3)
            
            # Warte auf Login-Formular
            # RepDoc verwendet IDs: loginInputUser, loginInputPassword
            try:
                # Username-Feld
                username_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "loginInputUser"))
                )
                username_field.clear()
                username_field.send_keys(self.username)
                
                # Password-Feld
                password_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "loginInputPassword"))
                )
                password_field.clear()
                password_field.send_keys(self.password)
                
                # Login-Button finden (Button mit Text "LOGIN" oder class "mdc-button--raised")
                login_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'LOGIN') or contains(@class, 'mdc-button--raised')]"))
                )
                login_button.click()
                
            except Exception as e:
                logger.error(f"Login fehlgeschlagen: {e}")
                return False
            
            # Warte auf Login-Erfolg
            time.sleep(5)
            
            # Prüfe ob Login erfolgreich (URL ändert sich oder bestimmte Elemente erscheinen)
            current_url = driver.current_url
            page_source = driver.page_source.lower()
            
            # Login-Erfolg-Indikatoren
            if "login" not in current_url.lower() or "katalog" in page_source or "suche" in page_source:
                RepDocScraper._logged_in = True
                logger.info("✅ RepDoc Login erfolgreich")
                return True
            else:
                logger.warning("⚠️ RepDoc Login unklar - prüfe manuell")
                # Versuche trotzdem weiter (kann sein, dass Login funktioniert hat)
                RepDocScraper._logged_in = True
                return True
                
        except Exception as e:
            logger.error(f"❌ RepDoc Login-Fehler: {e}")
            RepDocScraper._logged_in = False
            return False
    
    def search(self, teilenummer):
        """
        Suche Teilenummer in RepDoc und extrahiere Preise/Verfügbarkeit.
        
        Args:
            teilenummer: Teilenummer zum Suchen
            
        Returns:
            dict: {
                'success': bool,
                'teilenummer': str,
                'anzahl': int,
                'ergebnisse': [{
                    'teilenummer': str,
                    'beschreibung': str,
                    'upe': float,
                    'ek': float,
                    'preis': float,
                    'verfuegbar': bool,
                    'lieferzeit': str
                }],
                'error': str (optional)
            }
        """
        driver = self._ensure_driver()
        
        if not RepDocScraper._logged_in:
            if not self._do_login():
                return {
                    'success': False,
                    'teilenummer': teilenummer,
                    'anzahl': 0,
                    'ergebnisse': [],
                    'error': 'Login fehlgeschlagen'
                }
        
        try:
            logger.info(f"RepDoc: Suche nach {teilenummer}")
            
            # Navigiere zur Suchseite
            driver.get(SEARCH_URL)
            time.sleep(2)
            
            # Suche nach Suchfeld (verschiedene mögliche Selektoren)
            search_selectors = [
                "input[name*='search']",
                "input[name*='suche']",
                "input[name*='teil']",
                "input[type='search']",
                "input[placeholder*='Teile']",
                "input[placeholder*='Suche']",
                "#search",
                ".search-input"
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if search_input and search_input.is_displayed():
                        break
                except:
                    continue
            
            if not search_input:
                # Fallback: Versuche JavaScript-Suche
                logger.warning("Suchfeld nicht gefunden, versuche JavaScript-Suche")
                return self._search_via_javascript(driver, teilenummer)
            
            # Teilenummer eingeben
            search_input.clear()
            search_input.send_keys(teilenummer)
            time.sleep(0.5)
            search_input.send_keys(Keys.RETURN)
            
            # Warte auf Ergebnisse
            time.sleep(5)
            
            # Parse Ergebnisse
            results = self._parse_results(driver, teilenummer)
            
            return {
                'success': True,
                'teilenummer': teilenummer,
                'anzahl': len(results),
                'ergebnisse': results
            }
            
        except Exception as e:
            logger.exception(f"RepDoc Suche-Fehler für {teilenummer}")
            RepDocScraper._logged_in = False  # Login könnte abgelaufen sein
            return {
                'success': False,
                'teilenummer': teilenummer,
                'anzahl': 0,
                'ergebnisse': [],
                'error': str(e)
            }
    
    def _search_via_javascript(self, driver, teilenummer):
        """Fallback: Suche via JavaScript falls Suchfeld nicht gefunden"""
        try:
            # Versuche JavaScript-Suche
            js_search = f"""
            var inputs = document.querySelectorAll('input[type="text"], input[type="search"]');
            for(var i=0; i<inputs.length; i++) {{
                if(inputs[i].offsetParent !== null && 
                   (inputs[i].name.toLowerCase().includes('search') || 
                    inputs[i].name.toLowerCase().includes('suche') ||
                    inputs[i].placeholder.toLowerCase().includes('teil'))) {{
                    inputs[i].value = '{teilenummer}';
                    inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    var form = inputs[i].closest('form');
                    if(form) form.submit();
                    return 'ok';
                }}
            }}
            return 'not-found';
            """
            result = driver.execute_script(js_search)
            if result == 'ok':
                time.sleep(5)
                return self._parse_results(driver, teilenummer)
        except Exception as e:
            logger.error(f"JavaScript-Suche fehlgeschlagen: {e}")
        
        return []
    
    def _parse_results(self, driver, teilenummer):
        """
        Parse Suchergebnisse von RepDoc-Seite.
        
        Versucht verschiedene mögliche HTML-Strukturen zu erkennen.
        """
        results = []
        
        try:
            html = driver.page_source
            
            # Versuche verschiedene Selektoren für Ergebnisse
            result_selectors = [
                "table tbody tr",
                ".result-row",
                ".article-row",
                ".product-row",
                "[data-part-number]",
                ".search-result"
            ]
            
            rows = []
            for selector in result_selectors:
                try:
                    rows = driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(rows) > 0:
                        logger.info(f"RepDoc: {len(rows)} Ergebnisse mit Selektor '{selector}' gefunden")
                        break
                except:
                    continue
            
            if len(rows) == 0:
                # Keine Tabellen-Struktur - versuche andere Patterns
                logger.warning("Keine Tabellen-Struktur gefunden, versuche alternative Parsing")
                return self._parse_alternative_structure(driver, teilenummer)
            
            # Parse jede Zeile
            for row in rows[:10]:  # Max. 10 Ergebnisse
                try:
                    result = self._parse_row(row, teilenummer)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.debug(f"Fehler beim Parsen einer Zeile: {e}")
                    continue
            
            # Falls keine Ergebnisse: Prüfe ob "nicht gefunden" Meldung
            if len(results) == 0:
                if "nicht gefunden" in html.lower() or "keine ergebnisse" in html.lower():
                    logger.info(f"RepDoc: Keine Ergebnisse für {teilenummer}")
                else:
                    logger.warning(f"RepDoc: Unerwartete Struktur für {teilenummer}")
            
        except Exception as e:
            logger.exception(f"Fehler beim Parsen der Ergebnisse: {e}")
        
        return results
    
    def _parse_row(self, row, teilenummer):
        """Parse eine einzelne Ergebnis-Zeile"""
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 3:
                # Versuche div-Struktur
                cells = row.find_elements(By.CSS_SELECTOR, "div")
            
            if len(cells) == 0:
                return None
            
            # Extrahiere Daten (verschiedene mögliche Strukturen)
            result = {
                'teilenummer': teilenummer,
                'beschreibung': '',
                'upe': None,
                'ek': None,
                'preis': None,
                'verfuegbar': True,
                'lieferzeit': None
            }
            
            # Versuche Teilenummer zu finden
            row_text = row.text
            part_match = re.search(r'([A-Z0-9\-]+)', row_text)
            if part_match:
                result['teilenummer'] = part_match.group(1)
            
            # Versuche Preise zu finden
            price_patterns = [
                r'(\d+[,.]?\d*)\s*€',
                r'€\s*(\d+[,.]?\d*)',
                r'(\d+[,.]?\d*)\s*EUR'
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, row_text)
                if matches:
                    try:
                        price_str = matches[0].replace(',', '.')
                        price = float(price_str)
                        if result['preis'] is None:
                            result['preis'] = price
                            result['ek'] = price  # Annahme: EK wenn nicht anders angegeben
                    except:
                        pass
            
            # Beschreibung aus Text extrahieren
            if len(cells) > 1:
                result['beschreibung'] = cells[1].text.strip()[:100]  # Max. 100 Zeichen
            
            # Verfügbarkeit prüfen
            if "nicht verfügbar" in row_text.lower() or "nicht lieferbar" in row_text.lower():
                result['verfuegbar'] = False
            
            return result if result['preis'] or result['beschreibung'] else None
            
        except Exception as e:
            logger.debug(f"Fehler beim Parsen einer Zeile: {e}")
            return None
    
    def _parse_alternative_structure(self, driver, teilenummer):
        """Alternative Parsing-Methode für nicht-tabellarische Strukturen"""
        results = []
        
        try:
            # Versuche alle möglichen Produkt-Container zu finden
            containers = driver.find_elements(By.CSS_SELECTOR, 
                ".product, .article, .item, [class*='product'], [class*='article']")
            
            for container in containers[:10]:
                try:
                    text = container.text
                    if teilenummer.lower() in text.lower():
                        result = {
                            'teilenummer': teilenummer,
                            'beschreibung': text[:100],
                            'preis': None,
                            'verfuegbar': True
                        }
                        
                        # Preis suchen
                        price_match = re.search(r'(\d+[,.]?\d*)\s*€', text)
                        if price_match:
                            try:
                                result['preis'] = float(price_match.group(1).replace(',', '.'))
                                result['ek'] = result['preis']
                            except:
                                pass
                        
                        if result['preis'] or len(result['beschreibung']) > 10:
                            results.append(result)
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"Alternative Parsing fehlgeschlagen: {e}")
        
        return results
        
    def close(self):
        """Schließe Scraper (Singleton bleibt bestehen)"""
        pass
    
    @classmethod
    def force_close(cls):
        """Schließe Driver komplett (für Tests)"""
        if cls._driver:
            cls._driver.quit()
            cls._driver = None
            cls._logged_in = False


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    scraper = RepDocScraper()
    
    print("=== RepDoc Scraper Test ===")
    print(f"Login: {scraper._do_login()}")
    
    print("\n=== Suche Test ===")
    test_parts = ["1109AL", "650401", "93165554"]
    
    for part in test_parts:
        print(f"\nSuche: {part}")
        start = time.time()
        result = scraper.search(part)
        elapsed = time.time() - start
        
        print(f"Zeit: {elapsed:.1f}s")
        print(f"Erfolg: {result.get('success')}")
        print(f"Anzahl: {result.get('anzahl', 0)}")
        
        if result.get('ergebnisse'):
            for r in result['ergebnisse'][:3]:
                print(f"  {r.get('teilenummer')}: {r.get('beschreibung')[:50]} - {r.get('preis')}€")
        elif result.get('error'):
            print(f"  Fehler: {result['error']}")
    
    RepDocScraper.force_close()
