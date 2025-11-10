#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyundai Finance Scraper V4.5 - MIT CSV-DOWNLOAD
===========================================
Lädt die Bestandsliste als CSV herunter und parst sie

Author: Claude AI + Testing
Version: 4.5
Date: 2025-11-10
"""

import os
import sys
import time
import sqlite3
import json
import csv
import glob
from datetime import datetime
from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Pfade
DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
CREDENTIALS_PATH = '/opt/greiner-portal/config/credentials.json'
SCREENSHOTS_DIR = '/tmp/hyundai_screenshots'

class HyundaiFinanceScraper:
    """Produktions-Scraper für Hyundai Finance Portal"""

    def __init__(self, headless=True, dry_run=False):
        self.headless = headless
        self.dry_run = dry_run
        self.driver = None
        self.credentials = self._load_credentials()

        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

        print("\n" + "="*70)
        print("🚗 HYUNDAI FINANCE SCRAPER V4.5 - CSV-DOWNLOAD")
        print("="*70)
        if self.dry_run:
            print("⚠️  DRY RUN MODE - Keine DB-Änderungen")
        print()

    def _load_credentials(self) -> Dict:
        """Lädt Credentials"""
        if os.path.exists(CREDENTIALS_PATH):
            with open(CREDENTIALS_PATH, 'r') as f:
                creds = json.load(f)
            if 'external_systems' in creds and 'hyundai_finance' in creds['external_systems']:
                return creds['external_systems']['hyundai_finance']

        # Fallback
        return {
            'portal_url': 'https://fiona.hyundaifinance.eu/#/dealer-portal',
            'username': 'Christian.aichinger@auto-greiner.de',
            'password': 'Hyundaikona2020!'
        }

    def init_driver(self):
        """Initialisiert Chrome WebDriver"""
        print("🔧 Initialisiere Chrome WebDriver...")

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
        
        # Download-Verzeichnis setzen
        prefs = {
            'download.default_directory': SCREENSHOTS_DIR,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True
        }
        chrome_options.add_experimental_option('prefs', prefs)

        self.driver = webdriver.Chrome(options=chrome_options)
        print("✅ WebDriver bereit\n")

    def _screenshot(self, name: str):
        """Screenshot speichern"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(SCREENSHOTS_DIR, f"{timestamp}_{name}.png")
        self.driver.save_screenshot(filepath)
        print(f"   📸 {name}.png")

    def login(self) -> bool:
        """Login auf FIONA Portal"""
        print("🔐 Login auf FIONA Portal...")

        try:
            self.driver.get(self.credentials['portal_url'])
            time.sleep(5)

            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            if len(inputs) < 2:
                raise Exception("Login-Felder nicht gefunden")

            inputs[0].send_keys(self.credentials['username'])
            inputs[1].send_keys(self.credentials['password'])

            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if "login" in btn.text.lower():
                    btn.click()
                    break

            time.sleep(8)
            self._screenshot("01_nach_login")

            print("✅ Login erfolgreich\n")
            return True

        except Exception as e:
            print(f"❌ Login fehlgeschlagen: {e}")
            return False

    def select_location(self) -> bool:
        """Standort auswählen"""
        print("📍 Standort auswählen...")

        try:
            time.sleep(3)

            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Auto Greiner')]")

            if not elements:
                print("   ⚠️  Keine Standortauswahl nötig")
                return True

            # JavaScript-Click
            self.driver.execute_script("arguments[0].click();", elements[0])
            time.sleep(2)

            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if "auswähl" in btn.text.lower():
                    self.driver.execute_script("arguments[0].click();", btn)
                    break

            time.sleep(10)
            self._screenshot("02_standort_gewählt")

            print("✅ Standort ausgewählt\n")
            return True

        except Exception as e:
            print(f"❌ Standortauswahl fehlgeschlagen: {e}")
            return False

    def open_ekf_portal(self) -> bool:
        """Öffnet EKF Portal via Einkaufsfinanzierung-Kachel"""
        print("🏢 Öffne EKF Portal...")

        try:
            # Klick auf "Einkaufsfinanzierung" Kachel
            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Einkaufsfinanzierung')]")

            if not elements:
                raise Exception("Einkaufsfinanzierung-Kachel nicht gefunden")

            self.driver.execute_script("arguments[0].click();", elements[0])
            time.sleep(5)

            # Wechsle zu neuem Tab (EKF Portal)
            if len(self.driver.window_handles) < 2:
                raise Exception("EKF Portal Tab nicht geöffnet")

            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(10)

            print(f"   URL: {self.driver.current_url}")
            self._screenshot("03_ekf_portal")

            print("✅ EKF Portal geöffnet\n")
            return True

        except Exception as e:
            print(f"❌ EKF Portal öffnen fehlgeschlagen: {e}")
            return False

    def navigate_to_bestandsliste(self) -> bool:
        """Navigation zur BESTANDSLISTE"""
        print("📋 Navigation zur BESTANDSLISTE...")

        try:
            time.sleep(5)

            # Suche BESTANDSLISTE Link
            links = self.driver.find_elements(By.TAG_NAME, "a")
            bestand_links = [l for l in links if "BESTAND" in l.text.upper()]

            if not bestand_links:
                raise Exception("BESTANDSLISTE nicht gefunden")

            self.driver.execute_script("arguments[0].click();", bestand_links[0])
            time.sleep(8)

            print(f"   URL: {self.driver.current_url}")
            self._screenshot("04_bestandsliste")

            print("✅ Bestandsliste geladen\n")
            return True

        except Exception as e:
            print(f"❌ Navigation fehlgeschlagen: {e}")
            return False

    def download_and_parse_csv(self) -> List[Dict]:
        """Lädt CSV herunter und parst sie"""
        print("📥 Download Bestandsliste CSV...")

        vertraege = []

        try:
            time.sleep(3)

            # DETAILSUCHE öffnen
            print("   → Öffne Detailsuche...")
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if "detail" in btn.text.lower():
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(3)
                    break

            # FILTER SETZEN: Breites Rechnungsdatum
            print("   → Setze Filter (Rechnungsdatum)...")
            try:
                heute = datetime.now()
                vor_2_jahren = datetime(heute.year - 2, 1, 1)
                
                date_from = self.driver.find_element(By.ID, "mat-date-range-input-0")
                date_from.clear()
                date_from.send_keys(vor_2_jahren.strftime("%d.%m.%Y"))
                time.sleep(1)
                
                parent = date_from.find_element(By.XPATH, "./ancestor::mat-date-range-input[1]")
                date_inputs = parent.find_elements(By.TAG_NAME, "input")
                if len(date_inputs) > 1:
                    date_inputs[1].clear()
                    date_inputs[1].send_keys(heute.strftime("%d.%m.%Y"))
                    time.sleep(1)
                
                print(f"      ✓ Rechnungsdatum: {vor_2_jahren.strftime('%d.%m.%Y')} - {heute.strftime('%d.%m.%Y')}")
                
            except Exception as e:
                print(f"      ⚠️  Filter setzen fehlgeschlagen: {e}")

            # SUCHEN-Button klicken
            time.sleep(2)
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            search_buttons = [b for b in buttons if b.text.strip() == "Suchen"]

            if search_buttons:
                print(f"   → Klicke 'Suchen'...")
                self.driver.execute_script("arguments[0].click();", search_buttons[0])
                time.sleep(8)
                self._screenshot("07_nach_suche")

            # DOWNLOAD-Button klicken
            print("   → Suche Download-Button...")
            
            # Suche nach allen Buttons und filtere nach Download
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            download_button = None
            
            for btn in all_buttons:
                try:
                    # Suche nach mat-icon mit "download"
                    icons = btn.find_elements(By.TAG_NAME, "mat-icon")
                    for icon in icons:
                        if "download" in icon.text.lower():
                            download_button = btn
                            break
                    if download_button:
                        break
                except:
                    continue
            
            if download_button:
                print(f"   → Klicke Download-Button...")
                
                # Lösche alte CSVs
                old_csvs = glob.glob(os.path.join(SCREENSHOTS_DIR, "*.csv"))
                for f in old_csvs:
                    os.remove(f)
                
                self.driver.execute_script("arguments[0].click();", download_button)
                
                # Warte auf Download
                print("   → Warte auf Download...")
                csv_file = None
                for i in range(15):  # 15 Sekunden warten
                    time.sleep(1)
                    csvs = glob.glob(os.path.join(SCREENSHOTS_DIR, "*.csv"))
                    if csvs:
                        csv_file = csvs[0]
                        break
                
                self._screenshot("08_nach_download")
                
                if csv_file:
                    print(f"   ✓ CSV gefunden: {os.path.basename(csv_file)}")
                    vertraege = self._parse_csv(csv_file)
                else:
                    print("   ⚠️  CSV nicht gefunden - prüfe Download-Verzeichnis")
                    print(f"      Verzeichnis: {SCREENSHOTS_DIR}")
                    return []
                
            else:
                print("   ❌ Download-Button nicht gefunden!")
                return []

            return vertraege

        except Exception as e:
            print(f"❌ CSV-Download fehlgeschlagen: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _parse_csv(self, csv_file: str) -> List[Dict]:
        """Parst die CSV-Datei"""
        vertraege = []
        
        try:
            # Versuche verschiedene Encodings
            for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'iso-8859-1']:
                try:
                    with open(csv_file, 'r', encoding=encoding) as f:
                        # Teste ersten Delimiter
                        first_line = f.readline()
                        delimiter = ';' if ';' in first_line else ','
                        
                        f.seek(0)
                        reader = csv.DictReader(f, delimiter=delimiter)
                        
                        if reader.fieldnames:
                            print(f"   CSV Encoding: {encoding}, Delimiter: '{delimiter}'")
                            print(f"   Spalten: {', '.join(list(reader.fieldnames)[:6])}...")
                            
                            for idx, row in enumerate(reader, 1):
                                # Suche VIN-Spalte
                                vin = ''
                                for key in row.keys():
                                    if key and ('VIN' in key.upper() or 'FAHRZEUG' in key.upper() or 'FIN' in key.upper()):
                                        vin = row[key].strip()
                                        if len(vin) == 17:
                                            break
                                
                                if not vin or len(vin) != 17:
                                    continue
                                
                                vertrag = {
                                    'vin': vin,
                                    'finanzierungsnummer': row.get('Auftragskorb', row.get('Auftragsnr', row.get('Finanzierungsnr.', ''))),
                                    'dokumentenstatus': row.get('Dokumentenstatus', ''),
                                    'finanzierungsstatus': row.get('Finanzierungsstatus', 'Finanziert'),
                                    'modell': row.get('Modell', ''),
                                    'produkt': row.get('Produkt', ''),
                                    'finanz_betrag': 0.0,
                                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                }
                                
                                vertraege.append(vertrag)
                                
                                if idx <= 5:
                                    print(f"   ✓ {idx}: VIN={vertrag['vin']} | {vertrag['modell'][:40]}")
                            
                            break  # Encoding funktioniert
                except UnicodeDecodeError:
                    continue
        
            print(f"\n✅ {len(vertraege)} Verträge aus CSV gelesen\n")
        
        except Exception as e:
            print(f"   ❌ CSV-Parsing fehlgeschlagen: {e}")
            import traceback
            traceback.print_exc()
        
        return vertraege

    def save_to_database(self, vertraege: List[Dict]) -> Dict[str, int]:
        """Speichert in DB"""
        print("💾 Speichere in Datenbank...")

        if self.dry_run:
            print("⚠️  DRY RUN - Keine DB-Änderungen")
            return {'imported': len(vertraege), 'updated': 0, 'errors': 0}

        if not vertraege:
            print("⚠️  Keine Verträge")
            return {'imported': 0, 'updated': 0, 'errors': 0}

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        stats = {'imported': 0, 'updated': 0, 'errors': 0}

        try:
            cursor.execute("DELETE FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Hyundai Finance'")

            for vertrag in vertraege:
                try:
                    cursor.execute("""
                        INSERT INTO fahrzeugfinanzierungen (
                            finanzinstitut, rrdi, vin, modell, produktfamilie,
                            finanzierungsnummer, finanzierungsstatus, dokumentstatus,
                            aktueller_saldo, original_betrag, datei_quelle, import_datum
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        'Hyundai Finance', 'AUTO_GREINER', vertrag['vin'], vertrag.get('modell', ''),
                        vertrag.get('produkt', ''), vertrag.get('finanzierungsnummer', ''), 
                        vertrag['finanzierungsstatus'], vertrag.get('dokumentenstatus', ''),
                        vertrag['finanz_betrag'], vertrag['finanz_betrag'], 
                        'Hyundai Finance Portal Scraper V4.5 (CSV)', vertrag['scraped_at']
                    ))
                    stats['imported'] += 1
                except Exception as e:
                    stats['errors'] += 1

            conn.commit()
            print(f"✅ Importiert: {stats['imported']}")

        except Exception as e:
            print(f"❌ DB-Fehler: {e}")
            conn.rollback()
        finally:
            conn.close()

        return stats

    def run(self) -> bool:
        """Hauptfunktion"""
        try:
            self.init_driver()

            if not self.login():
                return False

            if not self.select_location():
                return False

            if not self.open_ekf_portal():
                return False

            if not self.navigate_to_bestandsliste():
                return False

            vertraege = self.download_and_parse_csv()

            if not vertraege:
                print("⚠️  Keine Verträge gefunden!")
                return False

            stats = self.save_to_database(vertraege)

            self._screenshot("99_final")

            print("\n" + "="*70)
            print("✅ SCRAPING ERFOLGREICH!")
            print("="*70)
            print(f"📊 Verträge: {len(vertraege)}")
            print(f"💾 Gespeichert: {stats['imported']}")
            print(f"📂 Screenshots: {SCREENSHOTS_DIR}")

            return True

        except Exception as e:
            print(f"\n❌ FEHLER: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            if self.driver:
                self.driver.quit()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Hyundai Finance Scraper V4.5')
    parser.add_argument('--no-headless', action='store_true', help='Browser sichtbar')
    parser.add_argument('--dry-run', action='store_true', help='Keine DB-Änderungen')
    args = parser.parse_args()

    scraper = HyundaiFinanceScraper(
        headless=not args.no_headless,
        dry_run=args.dry_run
    )

    success = scraper.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
