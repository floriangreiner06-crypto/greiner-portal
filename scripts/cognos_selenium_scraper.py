#!/usr/bin/env python3
"""
Cognos Selenium Scraper
Ruft BWA-Reports über Browser-Automation auf und extrahiert Daten

Erstellt: TAG 182
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import re
from html.parser import HTMLParser
from typing import Dict, List, Optional
import json

# Cognos Konfiguration
COGNOS_BASE_URL = "http://10.80.80.10:9300"
COGNOS_BI_URL = f"{COGNOS_BASE_URL}/bi"
LOGIN_USERNAME = "Greiner"
LOGIN_PASSWORD = "Hawaii#22"

# Report-ID aus HAR-Analyse
REPORT_ID = "i176278575AB142B18A70E1BDFAE95614"


class CognosSeleniumScraper:
    """
    Selenium-basierter Scraper für Cognos BWA-Reports
    """
    
    def __init__(self, headless: bool = False):
        """
        Initialisiert Selenium WebDriver
        
        Args:
            headless: Wenn True, Browser läuft im Hintergrund
        """
        self.headless = headless
        self.driver = None
        self.logged_in = False
    
    def setup_driver(self):
        """
        Erstellt Chrome WebDriver
        """
        print("=== Setup Chrome WebDriver ===\n")
        
        chrome_options = Options()
        
        # Server-Umgebung Optionen
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        
        if self.headless:
            chrome_options.add_argument('--headless=new')  # Neue Headless-Mode
        
        # Verstecke Automation
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Realistischer User-Agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--lang=de-DE')
        
        # Remote Debugging Port (falls nötig)
        chrome_options.add_argument('--remote-debugging-port=9222')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(60)
            
            # Verstecke WebDriver-Eigenschaften
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                '''
            })
            
            print("✅ Chrome WebDriver erstellt\n")
            return True
        except Exception as e:
            print(f"❌ Fehler beim Erstellen des WebDrivers: {e}")
            print("\n⚠️  Versuche mit headless=True...")
            
            # Versuche mit headless
            try:
                chrome_options.add_argument('--headless=new')
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.implicitly_wait(10)
                self.driver.set_page_load_timeout(60)
                print("✅ Chrome WebDriver erstellt (headless)\n")
                return True
            except Exception as e2:
                print(f"❌ Auch headless fehlgeschlagen: {e2}")
                print("\n⚠️  Mögliche Lösungen:")
                print("   1. Chrome/Chromium installieren: sudo apt-get install chromium-browser")
                print("   2. ChromeDriver installieren: sudo apt-get install chromium-chromedriver")
                print("   3. Oder: DISPLAY=:0 setzen für X11")
                return False
    
    def login(self) -> bool:
        """
        Loggt sich ins Cognos Portal ein
        """
        print("=== Cognos Login ===\n")
        
        if not self.driver:
            print("❌ WebDriver nicht initialisiert")
            return False
        
        try:
            # Lade Hauptseite
            print(f"Lade: {COGNOS_BI_URL}/")
            self.driver.get(f"{COGNOS_BI_URL}/")
            time.sleep(2)
            
            # Prüfe ob Login erforderlich
            if 'login' in self.driver.current_url.lower() or 'anmeldung' in self.driver.page_source.lower():
                print("⚠️  Login erforderlich")
                
                # Suche nach Login-Feldern
                try:
                    # Versuche verschiedene Login-Feld-Namen
                    username_selectors = [
                        "input[name='username']",
                        "input[name='user']",
                        "input[name='login']",
                        "input[type='text']",
                        "#username",
                        "#user",
                    ]
                    
                    password_selectors = [
                        "input[name='password']",
                        "input[name='pass']",
                        "input[type='password']",
                        "#password",
                    ]
                    
                    username_field = None
                    password_field = None
                    
                    for selector in username_selectors:
                        try:
                            username_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                            break
                        except:
                            continue
                    
                    for selector in password_selectors:
                        try:
                            password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                            break
                        except:
                            continue
                    
                    if username_field and password_field:
                        print("✅ Login-Felder gefunden")
                        username_field.send_keys(LOGIN_USERNAME)
                        password_field.send_keys(LOGIN_PASSWORD)
                        
                        # Suche nach Submit-Button
                        submit_selectors = [
                            "button[type='submit']",
                            "input[type='submit']",
                            "button:contains('Login')",
                            "button:contains('Anmelden')",
                        ]
                        
                        for selector in submit_selectors:
                            try:
                                submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                                submit_button.click()
                                break
                            except:
                                continue
                        
                        time.sleep(3)
                    else:
                        print("⚠️  Login-Felder nicht gefunden, versuche Basic Auth")
                        # Basic Auth über URL
                        auth_url = f"http://{LOGIN_USERNAME}:{LOGIN_PASSWORD}@10.80.80.10:9300/bi/"
                        self.driver.get(auth_url)
                        time.sleep(2)
                
                except Exception as e:
                    print(f"⚠️  Fehler beim Login: {e}")
                    # Versuche Basic Auth
                    auth_url = f"http://{LOGIN_USERNAME}:{LOGIN_PASSWORD}@10.80.80.10:9300/bi/"
                    self.driver.get(auth_url)
                    time.sleep(2)
            
            # Prüfe ob Login erfolgreich
            if 'cognos' in self.driver.page_source.lower() or 'dashboard' in self.driver.page_source.lower():
                print("✅ Login erfolgreich\n")
                self.logged_in = True
                return True
            else:
                print("⚠️  Login-Status unklar, versuche trotzdem...")
                self.logged_in = True
                return True
        
        except Exception as e:
            print(f"❌ Fehler beim Login: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _format_date_range(self, monat: int, jahr: int) -> tuple:
        """
        Formatiert Datumsbereich für Cognos (YYYYMMDD-YYYYMMDD)
        """
        from datetime import datetime, timedelta
        
        date_from = datetime(jahr, monat, 1)
        if monat == 12:
            date_to = datetime(jahr + 1, 1, 1) - timedelta(days=1)
        else:
            date_to = datetime(jahr, monat + 1, 1) - timedelta(days=1)
        
        return date_from.strftime('%Y%m%d'), date_to.strftime('%Y%m%d')
    
    def _get_standort_code(self, standort: str) -> str:
        """
        Konvertiert Standort-Name zu Cognos-Code
        """
        standort_mapping = {
            '1': '00',  # Deggendorf Opel
            '2': '01',  # Deggendorf Hyundai
            '3': '02',  # Landau
            'deggendorf': '00',
            'deggendorf_opel': '00',
            'deggendorf_hyundai': '01',
            'hyundai': '01',
            'landau': '02',
        }
        
        return standort_mapping.get(standort.lower(), standort)
    
    def get_bwa_report(self, monat: int = 12, jahr: int = 2025, 
                      standort: str = None) -> Optional[Dict]:
        """
        Ruft BWA-Report ab
        
        Args:
            monat: Monat (1-12)
            jahr: Jahr
            standort: Standort ('1', '2', '3', '00', '01', '02', oder Name)
        
        Returns:
            Dict mit HTML-Content oder None
        """
        print(f"\n=== BWA-Report abrufen ===")
        print(f"Monat: {monat}, Jahr: {jahr}, Standort: {standort}\n")
        
        if not self.logged_in:
            print("❌ Nicht eingeloggt")
            return None
        
        try:
            # Schritt 1: Navigiere zu Report-App
            report_app_url = f"{COGNOS_BI_URL}/pat/rsapp.htm"
            print(f"Schritt 1: Lade Report-App...")
            self.driver.get(report_app_url)
            time.sleep(3)
            
            # Schritt 2: Versuche Report zu öffnen
            # Option A: Direkte URL mit Report-ID
            report_url = f"{COGNOS_BI_URL}/v1/disp/r/{REPORT_ID}"
            print(f"Schritt 2: Öffne Report: {report_url}")
            
            try:
                self.driver.get(report_url)
            except Exception as e:
                # Prüfe ob Alert vorhanden
                try:
                    alert = self.driver.switch_to.alert
                    alert_text = alert.text
                    print(f"⚠️  Alert gefunden: {alert_text[:100]}")
                    alert.accept()  # Schließe Alert
                    time.sleep(2)
                except:
                    pass
            
            time.sleep(5)
            
            # Schritt 3: Prüfe ob Prompt/Filter vorhanden
            print("Schritt 3: Prüfe Filter/Prompts...")
            
            # Suche nach Prompt-Elementen
            prompt_selectors = [
                "input[type='text']",
                "select",
                "button:contains('Ausführen')",
                "button:contains('Run')",
                ".prompt",
                "[id*='prompt']",
            ]
            
            prompts_found = False
            for selector in prompt_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        prompts_found = True
                        print(f"✅ Prompt-Elemente gefunden: {len(elements)}")
                        break
                except:
                    continue
            
            # Schritt 4: Setze Filter falls vorhanden
            if prompts_found and standort:
                print("Schritt 4: Setze Filter...")
                
                # Versuche Standort-Filter zu setzen
                standort_code = self._get_standort_code(standort)
                
                # Suche nach Select-Elementen (Dropdowns)
                selects = self.driver.find_elements(By.TAG_NAME, "select")
                for select in selects:
                    try:
                        # Prüfe ob Standort-Dropdown
                        if 'betrieb' in select.get_attribute('name').lower() or 'standort' in select.get_attribute('name').lower():
                            from selenium.webdriver.support.ui import Select
                            select_obj = Select(select)
                            # Versuche Option zu wählen
                            try:
                                select_obj.select_by_value(standort_code)
                                print(f"✅ Standort-Filter gesetzt: {standort_code}")
                            except:
                                # Versuche nach Text
                                try:
                                    standort_names = {
                                        '00': 'Deggendorf',
                                        '01': 'Deggendorf HYU',
                                        '02': 'Landau'
                                    }
                                    select_obj.select_by_visible_text(standort_names.get(standort_code, standort_code))
                                    print(f"✅ Standort-Filter gesetzt: {standort_names.get(standort_code)}")
                                except:
                                    pass
                    except:
                        continue
            
            # Schritt 5: Setze Zeitraum-Filter
            if prompts_found:
                date_from, date_to = self._format_date_range(monat, jahr)
                print(f"Schritt 5: Setze Zeitraum: {date_from} - {date_to}")
                
                # Suche nach Datums-Feldern
                date_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='date'], input[type='text']")
                for input_elem in date_inputs:
                    name = input_elem.get_attribute('name') or ''
                    if 'datum' in name.lower() or 'date' in name.lower() or 'zeit' in name.lower():
                        try:
                            input_elem.clear()
                            input_elem.send_keys(f"{date_from}-{date_to}")
                            print(f"✅ Zeitraum-Filter gesetzt")
                            break
                        except:
                            continue
            
            # Schritt 6: Führe Report aus
            print("Schritt 6: Führe Report aus...")
            
            # Suche nach Ausführen-Button
            run_button_selectors = [
                "button:contains('Ausführen')",
                "button:contains('Run')",
                "input[value*='Ausführen']",
                "input[value*='Run']",
                "button[type='submit']",
                ".runButton",
                "[id*='run']",
            ]
            
            for selector in run_button_selectors:
                try:
                    if ':contains(' in selector:
                        # XPath für Text-Suche
                        xpath = f"//button[contains(text(), 'Ausführen') or contains(text(), 'Run')]"
                        buttons = self.driver.find_elements(By.XPATH, xpath)
                    else:
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if buttons:
                        buttons[0].click()
                        print("✅ Report gestartet")
                        time.sleep(10)  # Warte auf Report-Generierung
                        break
                except:
                    continue
            
            # Schritt 7: Warte auf Report-Loading
            print("Schritt 7: Warte auf Report...")
            time.sleep(5)
            
            # Prüfe ob Report geladen ist
            max_wait = 30
            waited = 0
            while waited < max_wait:
                if 'table' in self.driver.page_source.lower() or 'report' in self.driver.page_source.lower():
                    print("✅ Report geladen")
                    break
                time.sleep(2)
                waited += 2
            
            # Extrahiere HTML
            html_content = self.driver.page_source
            
            return {
                'status': 'success',
                'html': html_content,
                'url': self.driver.current_url,
                'parameters': {
                    'monat': monat,
                    'jahr': jahr,
                    'standort': standort
                }
            }
        
        except Exception as e:
            print(f"❌ Fehler beim Abrufen des Reports: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def drill_down_on_position(self, position_name: str, max_depth: int = 2) -> Optional[Dict]:
        """
        Drilled auf eine BWA-Position auf
        
        Args:
            position_name: Name der Position (z.B. "Direkte Kosten", "Umsatzerlöse")
            max_depth: Maximale Drill-Down-Tiefe
        
        Returns:
            Dict mit detaillierten Daten oder None
        """
        print(f"\n=== Drill-Down: {position_name} ===\n")
        
        if not self.driver:
            print("❌ WebDriver nicht initialisiert")
            return None
        
        try:
            # Suche nach klickbaren Elementen (Links, Buttons) in der Nähe der Position
            # BWA-Positionen sind oft als Links formatiert, die auf Details führen
            
            # Strategie 1: Suche nach Links mit Position-Name
            link_selectors = [
                f"//a[contains(text(), '{position_name}')]",
                f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{position_name.lower()}')]",
                f"//td[contains(text(), '{position_name}')]/following-sibling::td//a",
                f"//tr[contains(., '{position_name}')]//a",
            ]
            
            clickable_element = None
            for selector in link_selectors:
                try:
                    if selector.startswith('//'):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        clickable_element = elements[0]
                        print(f"✅ Klickbares Element gefunden: {selector[:50]}")
                        break
                except:
                    continue
            
            # Strategie 2: Suche nach Tabellen-Zellen mit Position-Name und klicke auf Zahlen
            if not clickable_element:
                print("Versuche Strategie 2: Suche nach Tabellen-Zellen...")
                try:
                    # Suche nach Tabellen
                    tables = self.driver.find_elements(By.TAG_NAME, "table")
                    
                    for table in tables:
                        # Suche nach Zeilen mit Position-Name
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        
                        for row in rows:
                            row_text = row.text.lower()
                            if position_name.lower() in row_text:
                                # Suche nach Links in dieser Zeile
                                links = row.find_elements(By.TAG_NAME, "a")
                                if links:
                                    clickable_element = links[0]  # Erster Link in der Zeile
                                    print(f"✅ Link in Zeile gefunden")
                                    break
                        
                        if clickable_element:
                            break
                except Exception as e:
                    print(f"⚠️  Fehler bei Strategie 2: {e}")
            
            # Strategie 3: Suche nach JavaScript-Links (onclick)
            if not clickable_element:
                print("Versuche Strategie 3: Suche nach JavaScript-Links...")
                try:
                    # Suche nach Elementen mit onclick-Attribut
                    js_elements = self.driver.find_elements(By.XPATH, "//*[@onclick]")
                    
                    for elem in js_elements:
                        if position_name.lower() in elem.text.lower():
                            clickable_element = elem
                            print(f"✅ JavaScript-Link gefunden")
                            break
                except Exception as e:
                    print(f"⚠️  Fehler bei Strategie 3: {e}")
            
            if not clickable_element:
                print(f"⚠️  Kein klickbares Element für '{position_name}' gefunden")
                return None
            
            # Klicke auf Element
            print(f"Klicke auf Element...")
            try:
                # Scroll zu Element
                self.driver.execute_script("arguments[0].scrollIntoView(true);", clickable_element)
                time.sleep(1)
                
                # Klicke
                clickable_element.click()
                print("✅ Element angeklickt")
                
                # Warte auf Details-Loading
                print("Warte auf Details...")
                time.sleep(5)
                
                # Prüfe ob neue Daten geladen wurden
                max_wait = 30
                waited = 0
                while waited < max_wait:
                    # Prüfe ob neue Tabellen/Details vorhanden
                    new_tables = self.driver.find_elements(By.TAG_NAME, "table")
                    if len(new_tables) > 0:
                        # Prüfe ob sich Inhalt geändert hat
                        current_html = self.driver.page_source
                        if 'detail' in current_html.lower() or len(new_tables) > 1:
                            print("✅ Details geladen")
                            break
                    time.sleep(2)
                    waited += 2
                
                # Extrahiere detaillierte Daten
                detail_html = self.driver.page_source
                detail_values = self.extract_bwa_values(detail_html, is_drill_down=True)
                
                return {
                    'position': position_name,
                    'detail_html': detail_html,
                    'detail_values': detail_values,
                    'url': self.driver.current_url
                }
            
            except Exception as e:
                print(f"❌ Fehler beim Klicken: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        except Exception as e:
            print(f"❌ Fehler beim Drill-Down: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def extract_bwa_values(self, html_content: str = None, is_drill_down: bool = False) -> Dict:
        """
        Extrahiert BWA-Werte aus HTML
        
        Args:
            html_content: HTML-Content (wenn None, verwendet driver.page_source)
            is_drill_down: Wenn True, extrahiert Drill-Down-Details
        """
        if html_content is None:
            if not self.driver:
                return {}
            html_content = self.driver.page_source
        
        print("\n=== Extrahiere BWA-Werte ===\n")
        
        bwa_values = {}
        
        # Suche nach Tabellen
        table_pattern = r'<table[^>]*>(.*?)</table>'
        tables = re.findall(table_pattern, html_content, re.DOTALL | re.I)
        
        print(f"Gefundene Tabellen: {len(tables)}\n")
        
        # Parse Tabellen
        for table_idx, table in enumerate(tables, 1):
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.I)
            
            print(f"Tabelle {table_idx}: {len(rows)} Zeilen")
            
            # Extrahiere BWA-Positionen
            bwa_keywords = {
                'umsatzerlöse': ['umsatz', 'umsatzerlöse'],
                'einsatzwerte': ['einsatz', 'einsatzwerte'],
                'variable_kosten': ['variable', 'variable kosten'],
                'direkte_kosten': ['direkte', 'direkte kosten'],
                'indirekte_kosten': ['indirekte', 'indirekte kosten'],
                'betriebsergebnis': ['betriebsergebnis', 'betriebs-ergebnis'],
                'unternehmensergebnis': ['unternehmensergebnis', 'unternehmens-ergebnis'],
                'bruttoertrag': ['bruttoertrag', 'brutto-ertrag'],
                'deckungsbeitrag_1': ['deckungsbeitrag 1', 'db1'],
                'deckungsbeitrag_2': ['deckungsbeitrag 2', 'db2'],
                'deckungsbeitrag_3': ['deckungsbeitrag 3', 'db3'],
            }
            
            for row_idx, row in enumerate(rows[:100], 1):  # Erste 100 Zeilen
                cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.I)
                
                if cells:
                    clean_cells = []
                    for cell in cells:
                        clean = re.sub(r'<[^>]+>', '', cell)
                        clean = re.sub(r'\s+', ' ', clean).strip()
                        clean_cells.append(clean)
                    
                    row_text = ' '.join(clean_cells).lower()
                    
                    # Prüfe ob BWA-relevant
                    for key, keywords in bwa_keywords.items():
                        if any(kw in row_text for kw in keywords):
                            # Suche nach Zahlen (mit € oder ohne)
                            numbers = re.findall(r'([\d.,\s-]+)\s*€?', ' '.join(clean_cells))
                            # Bereinige Zahlen (entferne Leerzeichen, behalte Komma/Punkt)
                            cleaned_numbers = []
                            for num in numbers:
                                cleaned = re.sub(r'[^\d.,-]', '', num)
                                if cleaned:
                                    cleaned_numbers.append(cleaned)
                            
                            if cleaned_numbers:
                                # Speichere mit Tabelle-Index für Drill-Down
                                value_key = f"{key}_table{table_idx}" if is_drill_down else key
                                bwa_values[value_key] = {
                                    'table': table_idx,
                                    'row': row_idx,
                                    'cells': clean_cells,
                                    'values': cleaned_numbers[:10],  # Erste 10 Werte
                                    'is_drill_down': is_drill_down
                                }
                                print(f"✅ {key}: {cleaned_numbers[0] if cleaned_numbers else 'N/A'}")
        
        return bwa_values
    
    def close(self):
        """
        Schließt Browser
        """
        if self.driver:
            self.driver.quit()
            print("\n✅ Browser geschlossen")


def main():
    """
    Test-Funktion
    """
    print("=" * 80)
    print("Cognos Selenium Scraper - Test")
    print("=" * 80)
    
    # Versuche zuerst headless, falls das nicht funktioniert, mit Display
    import os
    display = os.environ.get('DISPLAY')
    
    # Versuche headless zuerst (schneller auf Server)
    scraper = CognosSeleniumScraper(headless=True)
    
    if not scraper.setup_driver():
        print("\n⚠️  Headless fehlgeschlagen, versuche mit Display...")
        scraper = CognosSeleniumScraper(headless=False)
    
    try:
        # Setup
        if not scraper.setup_driver():
            print("❌ WebDriver konnte nicht erstellt werden")
            return
        
        # Login
        if not scraper.login():
            print("❌ Login fehlgeschlagen")
            return
        
        # Test: Verschiedene Reports
        test_cases = [
            {'monat': 12, 'jahr': 2025, 'standort': '3', 'name': 'Landau'},
            {'monat': 12, 'jahr': 2025, 'standort': '1', 'name': 'Deggendorf Opel'},
            {'monat': 12, 'jahr': 2025, 'standort': '2', 'name': 'Deggendorf Hyundai'},
            {'monat': 12, 'jahr': 2025, 'standort': None, 'name': 'Alle Standorte'},
        ]
        
        all_results = {}
        
        for i, test_case in enumerate(test_cases, 1):
            print("\n" + "=" * 80)
            print(f"Test {i}: {test_case['name']} - {test_case['monat']}/{test_case['jahr']}")
            print("=" * 80)
            
            result = scraper.get_bwa_report(
                monat=test_case['monat'],
                jahr=test_case['jahr'],
                standort=test_case['standort']
            )
            
            if result:
                # Extrahiere BWA-Werte
                bwa_values = scraper.extract_bwa_values(result['html'])
                
                # Speichere HTML
                filename = f"/tmp/cognos_bwa_{test_case['name'].lower().replace(' ', '_')}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(result['html'])
                print(f"\n💾 HTML gespeichert: {filename}")
                
                # Speichere BWA-Werte
                all_results[test_case['name']] = {
                    'parameters': result['parameters'],
                    'bwa_values': bwa_values
                }
                
                # Drill-Down auf wichtige Positionen
                print("\n" + "-" * 80)
                print("DRILL-DOWN auf wichtige Positionen")
                print("-" * 80)
                
                drill_down_positions = [
                    'Direkte Kosten',
                    'Indirekte Kosten',
                    'Variable Kosten',
                    'Betriebsergebnis',
                ]
                
                drill_down_results = {}
                for position in drill_down_positions:
                    print(f"\nVersuche Drill-Down: {position}...")
                    drill_result = scraper.drill_down_on_position(position)
                    
                    if drill_result:
                        drill_down_results[position] = drill_result
                        
                        # Speichere Drill-Down HTML
                        drill_filename = f"/tmp/cognos_bwa_{test_case['name'].lower().replace(' ', '_')}_drill_{position.lower().replace(' ', '_')}.html"
                        with open(drill_filename, 'w', encoding='utf-8') as f:
                            f.write(drill_result['detail_html'])
                        print(f"💾 Drill-Down HTML gespeichert: {drill_filename}")
                        
                        # Warte zwischen Drill-Downs
                        time.sleep(3)
                    else:
                        print(f"⚠️  Drill-Down für '{position}' nicht möglich")
                
                # Füge Drill-Down-Ergebnisse hinzu
                if drill_down_results:
                    all_results[test_case['name']]['drill_down'] = drill_down_results
                
                # Warte zwischen Requests
                if i < len(test_cases):
                    print("\n⏳ Warte 5 Sekunden vor nächstem Request...")
                    time.sleep(5)
        
        # Speichere alle BWA-Werte
        with open('/tmp/cognos_bwa_all_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Alle BWA-Werte gespeichert: /tmp/cognos_bwa_all_results.json")
        
        # Zusammenfassung
        print("\n" + "=" * 80)
        print("ZUSAMMENFASSUNG")
        print("=" * 80)
        for name, data in all_results.items():
            print(f"\n{name}:")
            if data.get('bwa_values'):
                for key, value in data['bwa_values'].items():
                    if not value.get('is_drill_down'):  # Nur Hauptwerte anzeigen
                        print(f"  {key}: {value.get('values', ['N/A'])[0] if value.get('values') else 'N/A'}")
            
            # Zeige Drill-Down-Ergebnisse
            if data.get('drill_down'):
                print(f"  Drill-Down:")
                for position, drill_data in data['drill_down'].items():
                    if drill_data.get('detail_values'):
                        print(f"    {position}:")
                        for key, value in drill_data['detail_values'].items():
                            if value.get('is_drill_down'):
                                print(f"      {key}: {value.get('values', ['N/A'])[0] if value.get('values') else 'N/A'}")
            
            if not data.get('bwa_values'):
                print("  ⚠️  Keine BWA-Werte gefunden")
    
    finally:
        # Schließe Browser
        try:
            scraper.close()
        except:
            pass


if __name__ == '__main__':
    main()
