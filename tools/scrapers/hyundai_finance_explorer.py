#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyundai Finance Explorer - Website-Analyse
===========================================
Erforscht alle verfügbaren Bereiche und Funktionen
"""

import os
import sys
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

# Konfiguration
PORTAL_URL = "https://fiona.hyundaifinance.eu/#/dealer-portal"
USERNAME = "Christian.aichinger@auto-greiner.de"
PASSWORD = "Hyundaikona2020!"
STANDORT_NAME = "Auto Greiner"

SCREENSHOTS_DIR = "/tmp/hyundai_explorer"
RESULTS_FILE = "/tmp/hyundai_explorer/exploration_results.json"

class HyundaiExplorer:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "portal_url": PORTAL_URL,
            "pages_found": [],
            "menu_items": [],
            "buttons": [],
            "forms": [],
            "tables": [],
            "download_options": [],
            "screenshots": []
        }
        
    def setup_driver(self):
        print("🔧 Initialisiere WebDriver...")
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--lang=de-DE')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(3)
        self.wait = WebDriverWait(self.driver, 15)
        print("✅ WebDriver bereit")
        
    def screenshot(self, name):
        filename = f"{len(self.results['screenshots']):02d}_{name}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        self.driver.save_screenshot(filepath)
        self.results['screenshots'].append(filename)
        print(f"   📸 {filename}")
        return filepath
        
    def get_page_info(self):
        """Sammelt Informationen über die aktuelle Seite"""
        info = {
            "url": self.driver.current_url,
            "title": self.driver.title,
            "timestamp": datetime.now().isoformat()
        }
        
        # Alle Links finden
        links = []
        for a in self.driver.find_elements(By.TAG_NAME, "a"):
            try:
                href = a.get_attribute("href") or ""
                text = a.text.strip()
                if text or href:
                    links.append({"text": text, "href": href})
            except:
                pass
        info["links"] = links[:20]  # Max 20
        
        # Alle Buttons finden
        buttons = []
        for btn in self.driver.find_elements(By.TAG_NAME, "button"):
            try:
                text = btn.text.strip()
                btn_class = btn.get_attribute("class") or ""
                if text:
                    buttons.append({"text": text, "class": btn_class[:50]})
            except:
                pass
        info["buttons"] = buttons[:20]
        
        # Menü-Items (Angular Material)
        menu_items = []
        for item in self.driver.find_elements(By.CSS_SELECTOR, "mat-nav-list a, mat-list-item, .nav-item, .menu-item"):
            try:
                text = item.text.strip()
                if text:
                    menu_items.append(text)
            except:
                pass
        info["menu_items"] = list(set(menu_items))[:15]
        
        # Tabellen
        tables = []
        for table in self.driver.find_elements(By.TAG_NAME, "table"):
            try:
                headers = [th.text.strip() for th in table.find_elements(By.TAG_NAME, "th")]
                rows = len(table.find_elements(By.TAG_NAME, "tr"))
                if headers:
                    tables.append({"headers": headers[:10], "rows": rows})
            except:
                pass
        info["tables"] = tables
        
        # Mat-Cards (Angular Material Kacheln)
        cards = []
        for card in self.driver.find_elements(By.CSS_SELECTOR, "mat-card, .card, .tile"):
            try:
                text = card.text.strip()[:100]
                if text:
                    cards.append(text)
            except:
                pass
        info["cards"] = cards[:10]
        
        return info
        
    def login(self):
        print("\n" + "="*60)
        print("🔐 SCHRITT 1: LOGIN")
        print("="*60)
        
        self.driver.get(PORTAL_URL)
        time.sleep(5)
        self.screenshot("01_login_page")
        
        # Login-Formular analysieren
        print("\n📋 Login-Seite Analyse:")
        inputs = self.driver.find_elements(By.TAG_NAME, "input")
        for inp in inputs:
            inp_type = inp.get_attribute("type")
            inp_name = inp.get_attribute("name") or inp.get_attribute("id")
            print(f"   Input: type={inp_type}, name={inp_name}")
        
        try:
            # Email eingeben
            email_field = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[formcontrolname='email']")
            ))
            email_field.clear()
            email_field.send_keys(USERNAME)
            print(f"   ✓ Email eingegeben: {USERNAME}")
            time.sleep(1)
            
            # Weiter-Button
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_btn.click()
            print("   ✓ Weiter geklickt")
            time.sleep(3)
            
            self.screenshot("02_after_email")
            
            # Passwort eingeben
            password_field = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='password']")
            ))
            password_field.clear()
            password_field.send_keys(PASSWORD)
            print("   ✓ Passwort eingegeben")
            time.sleep(1)
            
            # Login-Button
            login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_btn.click()
            print("   ✓ Login geklickt")
            time.sleep(5)
            
            self.screenshot("03_after_login")
            
            # Prüfe ob Login erfolgreich
            if "login" in self.driver.current_url.lower():
                print("   ❌ Login möglicherweise fehlgeschlagen")
                return False
                
            print("   ✅ Login erfolgreich!")
            return True
            
        except Exception as e:
            print(f"   ❌ Login-Fehler: {e}")
            self.screenshot("error_login")
            return False
            
    def select_standort(self):
        print("\n" + "="*60)
        print("🏢 SCHRITT 2: STANDORT AUSWÄHLEN")
        print("="*60)
        
        time.sleep(3)
        self.screenshot("04_standort_auswahl")
        
        # Seiten-Info sammeln
        page_info = self.get_page_info()
        print(f"\n📋 Seite: {page_info['url']}")
        print(f"   Titel: {page_info['title']}")
        print(f"   Buttons: {[b['text'] for b in page_info['buttons'][:5]]}")
        print(f"   Cards: {page_info['cards'][:3]}")
        
        try:
            # Standort-Karte suchen
            standort_card = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//*[contains(text(), '{STANDORT_NAME}')]")
            ))
            standort_card.click()
            print(f"   ✓ Standort '{STANDORT_NAME}' angeklickt")
            time.sleep(2)
            
            self.screenshot("05_standort_selected")
            
            # "Standort auswählen" Button
            select_btn = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Standort') or contains(., 'auswählen') or contains(., 'Select')]")
            ))
            select_btn.click()
            print("   ✓ Standort-Button geklickt")
            time.sleep(5)
            
            self.screenshot("06_nach_standort")
            return True
            
        except Exception as e:
            print(f"   ⚠️ Standort-Auswahl: {e}")
            # Vielleicht schon eingeloggt
            return True
            
    def explore_main_portal(self):
        print("\n" + "="*60)
        print("🏠 SCHRITT 3: HAUPTPORTAL ERKUNDEN")
        print("="*60)
        
        self.screenshot("07_hauptportal")
        
        page_info = self.get_page_info()
        self.results['pages_found'].append({
            "name": "Hauptportal",
            "info": page_info
        })
        
        print(f"\n📋 Hauptportal:")
        print(f"   URL: {page_info['url']}")
        print(f"   Menü-Items: {page_info['menu_items']}")
        print(f"   Buttons: {[b['text'] for b in page_info['buttons'][:8]]}")
        
        # Alle Kacheln/Tiles finden
        tiles = self.driver.find_elements(By.CSS_SELECTOR, "mat-card, .tile, .dashboard-item, [class*='tile'], [class*='card']")
        print(f"\n   🎯 Gefundene Kacheln/Tiles: {len(tiles)}")
        
        tile_texts = []
        for tile in tiles[:10]:
            try:
                text = tile.text.strip()[:80]
                if text and len(text) > 3:
                    tile_texts.append(text.replace('\n', ' | '))
                    print(f"      → {text[:60]}...")
            except:
                pass
        
        self.results['menu_items'] = tile_texts
        
        # Suche nach EKF/Einkaufsfinanzierung
        print("\n🔍 Suche nach EKF/Einkaufsfinanzierung...")
        ekf_elements = self.driver.find_elements(By.XPATH, 
            "//*[contains(text(), 'Einkauf') or contains(text(), 'EKF') or contains(text(), 'Finanzierung') or contains(text(), 'Stock')]"
        )
        for el in ekf_elements[:5]:
            try:
                print(f"      → {el.text.strip()[:50]}")
            except:
                pass
                
    def explore_ekf_portal(self):
        print("\n" + "="*60)
        print("💰 SCHRITT 4: EKF PORTAL ERKUNDEN")
        print("="*60)
        
        # Versuche EKF zu öffnen
        try:
            ekf_tile = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'Einkaufsfinanzierung') or contains(text(), 'EKF')]")
            ))
            ekf_tile.click()
            print("   ✓ EKF-Kachel geklickt")
            time.sleep(5)
            
            # Neues Fenster?
            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                print("   ✓ Zu neuem Fenster gewechselt")
                time.sleep(3)
                
        except Exception as e:
            print(f"   ⚠️ EKF-Kachel nicht gefunden: {e}")
            # Direkt zur URL navigieren
            print("   → Versuche direkte Navigation...")
            self.driver.get("https://ekf.hyundaifinance.eu")
            time.sleep(5)
            
        self.screenshot("08_ekf_portal")
        
        page_info = self.get_page_info()
        self.results['pages_found'].append({
            "name": "EKF Portal",
            "info": page_info
        })
        
        print(f"\n📋 EKF Portal:")
        print(f"   URL: {page_info['url']}")
        print(f"   Menü-Items: {page_info['menu_items']}")
        print(f"   Tabellen: {len(page_info['tables'])}")
        
        # Navigation/Sidebar erkunden
        nav_items = self.driver.find_elements(By.CSS_SELECTOR, 
            "mat-nav-list a, .sidebar a, nav a, .menu a, mat-list-item"
        )
        print(f"\n   📌 Navigation ({len(nav_items)} Items):")
        for item in nav_items[:15]:
            try:
                text = item.text.strip()
                href = item.get_attribute("href") or ""
                if text:
                    print(f"      → {text} ({href[-30:] if href else 'no-href'})")
            except:
                pass
                
    def explore_stocklist(self):
        print("\n" + "="*60)
        print("📋 SCHRITT 5: BESTANDSLISTE ERKUNDEN")
        print("="*60)
        
        # Direkt zur Bestandsliste
        self.driver.get("https://ekf.hyundaifinance.eu/account/stocklist/search")
        time.sleep(5)
        
        self.screenshot("09_stocklist")
        
        page_info = self.get_page_info()
        self.results['pages_found'].append({
            "name": "Bestandsliste",
            "info": page_info
        })
        
        print(f"\n📋 Bestandsliste:")
        print(f"   URL: {page_info['url']}")
        
        # Tabellen-Header
        if page_info['tables']:
            print(f"   Tabellen-Spalten: {page_info['tables'][0].get('headers', [])}")
            print(f"   Zeilen: {page_info['tables'][0].get('rows', 0)}")
            self.results['tables'] = page_info['tables']
        
        # Download-Buttons finden
        print("\n   🔽 Download-Optionen:")
        download_btns = self.driver.find_elements(By.XPATH,
            "//button[contains(@class, 'download') or .//mat-icon[contains(text(), 'download')]]"
        )
        for btn in download_btns:
            try:
                print(f"      → Button: {btn.text.strip() or btn.get_attribute('aria-label') or 'icon-button'}")
            except:
                pass
                
        # Mat-Icons für Downloads
        icons = self.driver.find_elements(By.CSS_SELECTOR, "mat-icon")
        download_icons = []
        for icon in icons:
            try:
                icon_text = icon.text.strip().lower()
                if 'download' in icon_text or 'export' in icon_text or 'csv' in icon_text:
                    download_icons.append(icon_text)
                    print(f"      → Icon: {icon_text}")
            except:
                pass
        self.results['download_options'] = download_icons
        
        # Filter-Optionen
        print("\n   🔍 Filter-Optionen:")
        filters = self.driver.find_elements(By.CSS_SELECTOR, 
            "mat-select, mat-form-field, input[type='text'], input[type='date']"
        )
        for f in filters[:10]:
            try:
                label = f.get_attribute("placeholder") or f.get_attribute("aria-label") or f.text.strip()[:30]
                if label:
                    print(f"      → {label}")
            except:
                pass
                
    def explore_other_pages(self):
        print("\n" + "="*60)
        print("🔍 SCHRITT 6: WEITERE SEITEN ERKUNDEN")
        print("="*60)
        
        # Bekannte EKF-Seiten testen
        pages_to_check = [
            ("Dashboard", "https://ekf.hyundaifinance.eu/dashboard"),
            ("Account", "https://ekf.hyundaifinance.eu/account"),
            ("Reports", "https://ekf.hyundaifinance.eu/reports"),
            ("Invoices", "https://ekf.hyundaifinance.eu/invoices"),
            ("Payments", "https://ekf.hyundaifinance.eu/payments"),
            ("Settings", "https://ekf.hyundaifinance.eu/settings"),
            ("Vehicle Details", "https://ekf.hyundaifinance.eu/account/vehicle"),
            ("Finance Overview", "https://ekf.hyundaifinance.eu/account/finance"),
        ]
        
        for name, url in pages_to_check:
            try:
                print(f"\n   🌐 Teste: {name}")
                self.driver.get(url)
                time.sleep(3)
                
                # Prüfe ob Seite existiert (nicht 404 oder redirect zu login)
                current = self.driver.current_url
                if "login" not in current.lower() and "error" not in current.lower():
                    page_info = self.get_page_info()
                    
                    if page_info['buttons'] or page_info['tables'] or page_info['menu_items']:
                        self.screenshot(f"10_{name.lower().replace(' ', '_')}")
                        self.results['pages_found'].append({
                            "name": name,
                            "url": url,
                            "actual_url": current,
                            "info": page_info
                        })
                        print(f"      ✅ Seite gefunden!")
                        print(f"      Buttons: {[b['text'] for b in page_info['buttons'][:3]]}")
                    else:
                        print(f"      ⚠️ Seite leer oder umgeleitet")
                else:
                    print(f"      ❌ Nicht verfügbar (redirect zu {current[:50]})")
                    
            except Exception as e:
                print(f"      ❌ Fehler: {e}")
                
    def save_results(self):
        print("\n" + "="*60)
        print("💾 ERGEBNISSE SPEICHERN")
        print("="*60)
        
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
            
        print(f"\n📄 Ergebnisse: {RESULTS_FILE}")
        print(f"📸 Screenshots: {SCREENSHOTS_DIR}/")
        print(f"\n📊 Zusammenfassung:")
        print(f"   Seiten gefunden: {len(self.results['pages_found'])}")
        print(f"   Screenshots: {len(self.results['screenshots'])}")
        print(f"   Menü-Items: {len(self.results['menu_items'])}")
        print(f"   Download-Optionen: {self.results['download_options']}")
        
    def run(self):
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        
        print("\n" + "="*70)
        print("🔍 HYUNDAI FINANCE EXPLORER - WEBSITE ANALYSE")
        print("="*70)
        print(f"⏰ Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Portal: {PORTAL_URL}")
        print(f"📂 Output: {SCREENSHOTS_DIR}")
        print("="*70)
        
        try:
            self.setup_driver()
            
            if not self.login():
                print("\n❌ Login fehlgeschlagen - Abbruch")
                return False
                
            self.select_standort()
            self.explore_main_portal()
            self.explore_ekf_portal()
            self.explore_stocklist()
            self.explore_other_pages()
            self.save_results()
            
            print("\n" + "="*70)
            print("✅ EXPLORATION ABGESCHLOSSEN!")
            print("="*70)
            return True
            
        except Exception as e:
            print(f"\n❌ FEHLER: {e}")
            import traceback
            traceback.print_exc()
            self.screenshot("error_final")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()
                print("\n🔚 Browser geschlossen")


if __name__ == "__main__":
    explorer = HyundaiExplorer()
    success = explorer.run()
    
    # Ergebnisse ausgeben
    if os.path.exists(RESULTS_FILE):
        print("\n" + "="*70)
        print("📋 GEFUNDENE SEITEN & FUNKTIONEN:")
        print("="*70)
        with open(RESULTS_FILE, 'r') as f:
            results = json.load(f)
            for page in results.get('pages_found', []):
                print(f"\n🌐 {page['name']}:")
                if 'info' in page:
                    print(f"   URL: {page['info'].get('url', 'N/A')}")
                    if page['info'].get('tables'):
                        print(f"   Tabellen: {page['info']['tables']}")
                    if page['info'].get('buttons'):
                        print(f"   Buttons: {[b['text'] for b in page['info']['buttons'][:5]]}")
    
    sys.exit(0 if success else 1)
