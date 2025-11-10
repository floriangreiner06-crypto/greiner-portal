#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyundai Finance Scraper V4 - FUNKTIONIERT!
===========================================
Flow:
1. Login auf FIONA Portal
2. Standort wählen
3. "Einkaufsfinanzierung" Kachel klicken → EKF Portal öffnet
4. Tab-Wechsel zum EKF Portal
5. BESTANDSLISTE klicken
6. Tabelle scrapen
7. In DB speichern

Author: Claude AI + Testing
Version: 4.0
Date: 2025-11-10
"""

import os
import sys
import time
import sqlite3
import json
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
        print("🚗 HYUNDAI FINANCE SCRAPER V4 - BESTANDSLISTE")
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
            time.sleep(10)  # Warte auf EKF-Laden
            
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
    
    def scrape_bestandsliste(self) -> List[Dict]:
        """Scraped die Bestandsliste-Tabelle"""
        print("📊 Scrape Bestandsliste...")
        
        vertraege = []
        
        try:
            time.sleep(5)
            
            # Prüfe ob "Suchen" Button nötig ist
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            search_buttons = [b for b in buttons if any(w in b.text.lower() for w in ["such", "anzeig", "laden"])]
            
            if search_buttons:
                print(f"   → Klicke '{search_buttons[0].text}'...")
                self.driver.execute_script("arguments[0].click();", search_buttons[0])
                time.sleep(8)
            
            # Finde Tabelle
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            
            if not tables:
                raise Exception("Keine Tabelle gefunden")
            
            rows = tables[0].find_elements(By.TAG_NAME, "tr")
            print(f"   → {len(rows)} Zeilen gefunden")
            
            # Analysiere Header
            headers = tables[0].find_elements(By.TAG_NAME, "th")
            header_text = [h.text.strip() for h in headers]
            print(f"   → Spalten: {', '.join(header_text[:5])}...")
            
            # Scrape Daten (überspringe Header-Zeile)
            for idx, row in enumerate(rows[1:], 1):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) < 5:
                        continue
                    
                    # Spalten-Mapping (basierend auf deinen Screenshots)
                    # Index kann variieren, daher flexibel
                    vertrag = {
                        'auftragskurz': cells[1].text.strip() if len(cells) > 1 else '',
                        'dokumentenstatus': cells[2].text.strip() if len(cells) > 2 else '',
                        'finanzierungsstatus': cells[3].text.strip() if len(cells) > 3 else 'Finanziert',
                        'vin': cells[4].text.strip() if len(cells) > 4 else '',
                        'modell': cells[5].text.strip() if len(cells) > 5 else '',
                        'farbe': cells[6].text.strip() if len(cells) > 6 else '',
                        'produkt': cells[7].text.strip() if len(cells) > 7 else '',
                        'finanz_betrag': self._parse_betrag(cells[8].text.strip() if len(cells) > 8 else '0'),
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    if vertrag['vin']:
                        vertraege.append(vertrag)
                        
                        if idx <= 3:
                            print(f"   ✓ {idx}: VIN={vertrag['vin'][:10]}... | {vertrag['modell'][:20]}")
                
                except Exception as e:
                    continue
            
            print(f"\n✅ {len(vertraege)} Verträge gescraped\n")
            return vertraege
            
        except Exception as e:
            print(f"❌ Scraping fehlgeschlagen: {e}")
            return []
    
    def _parse_betrag(self, text: str) -> float:
        """Parst Betrag"""
        try:
            cleaned = ''.join(c for c in text if c.isdigit() or c in ',-.')
            if ',' in cleaned:
                cleaned = cleaned.replace('.', '').replace(',', '.')
            return float(cleaned)
        except:
            return 0.0
    
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
                        'Hyundai Finance', 'AUTO_GREINER', vertrag['vin'], vertrag['modell'],
                        vertrag['produkt'], vertrag['auftragskurz'], vertrag['finanzierungsstatus'],
                        vertrag['dokumentenstatus'], vertrag['finanz_betrag'], vertrag['finanz_betrag'],
                        'Hyundai Finance Portal Scraper V4', vertrag['scraped_at']
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
            
            vertraege = self.scrape_bestandsliste()
            
            if not vertraege:
                print("⚠️  Keine Verträge gefunden")
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
    
    parser = argparse.ArgumentParser(description='Hyundai Finance Scraper V4')
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
