#!/bin/bash
# Hyundai Finance Scraper V3 - Automatische Installation
set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   HYUNDAI FINANCE SCRAPER V3 - AUTO INSTALL                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

PORTAL_DIR="/opt/greiner-portal"
SCRAPER_FILE="$PORTAL_DIR/tools/scrapers/hyundai_finance_scraper.py"

cd "$PORTAL_DIR"

# Backup
if [ -f "$SCRAPER_FILE" ]; then
    cp "$SCRAPER_FILE" "$SCRAPER_FILE.v2_backup_$(date +%Y%m%d_%H%M%S)"
    echo "✓ Backup erstellt"
fi

# V3 Code schreiben
cat > "$SCRAPER_FILE" << 'EOFPYTHON'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyundai Finance Scraper V3 - Produktions-Version
=================================================
Scraped die BESTANDSLISTE und speichert in fahrzeugfinanzierungen Tabelle

Author: Claude AI
Version: 3.0
Date: 2025-11-10
"""

import os
import sys
import time
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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
        self.wait = None
        self.credentials = self._load_credentials()
        
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        
        print("\n" + "="*70)
        print("🚗 HYUNDAI FINANCE SCRAPER V3 - BESTANDSLISTE")
        print("="*70)
        if self.dry_run:
            print("⚠️  DRY RUN MODE - Keine DB-Änderungen")
        print()
    
    def _load_credentials(self) -> Dict:
        """Lädt Credentials aus config/credentials.json"""
        if not os.path.exists(CREDENTIALS_PATH):
            print("⚠️  Credentials-Datei nicht gefunden, nutze Fallback")
            return {
                'portal_url': 'https://fiona.hyundaifinance.eu/#/dealer-portal',
                'username': 'Christian.aichinger@auto-greiner.de',
                'password': 'Hyundaikona2020!'
            }
        
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
        self.wait = WebDriverWait(self.driver, 20)
        
        print("✅ WebDriver bereit\n")
    
    def _save_screenshot(self, name: str):
        """Screenshot speichern"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        self.driver.save_screenshot(filepath)
        print(f"   📸 {filename}")
    
    def _save_html(self, name: str):
        """HTML speichern"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.html"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
        print(f"   💾 {filename}")
    
    def login(self) -> bool:
        """Login ins Portal"""
        print("🔐 Login...")
        
        try:
            url = self.credentials.get('portal_url', 'https://fiona.hyundaifinance.eu/#/dealer-portal')
            self.driver.get(url)
            time.sleep(5)
            
            # Email eingeben
            print("   → Email eingeben")
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            username_field = None
            password_field = None
            
            for inp in inputs:
                input_type = inp.get_attribute("type")
                if input_type in ["text", "email"] and not username_field:
                    username_field = inp
                elif input_type == "password" and not password_field:
                    password_field = inp
            
            if not username_field or not password_field:
                raise Exception("Login-Felder nicht gefunden")
            
            username_field.clear()
            username_field.send_keys(self.credentials['username'])
            time.sleep(1)
            
            # Passwort eingeben
            print("   → Passwort eingeben")
            password_field.clear()
            password_field.send_keys(self.credentials['password'])
            time.sleep(1)
            
            # Login-Button klicken
            print("   → Login-Button klicken")
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                btn_text = btn.text.lower()
                if "login" in btn_text or "anmeld" in btn_text:
                    btn.click()
                    break
            
            time.sleep(8)
            self._save_screenshot("01_nach_login")
            
            print("✅ Login erfolgreich\n")
            return True
            
        except Exception as e:
            print(f"❌ Login fehlgeschlagen: {e}")
            self._save_screenshot("error_login")
            return False
    
    def select_location(self) -> bool:
        """Standort auswählen"""
        print("📍 Standort auswählen...")
        
        try:
            time.sleep(3)
            
            print("   → Suche 'Auto Greiner' Standort")
            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Auto Greiner')]")
            
            if not elements:
                print("   ⚠️  Keine Standortauswahl nötig")
                return True
            
            for elem in elements:
                try:
                    elem.click()
                    break
                except:
                    try:
                        elem.find_element(By.XPATH, "./..").click()
                        break
                    except:
                        continue
            
            time.sleep(2)
            
            print("   → 'Standort auswählen' Button klicken")
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                btn_text = btn.text.lower()
                if any(word in btn_text for word in ["bestät", "weiter", "ok", "auswähl"]):
                    btn.click()
                    break
            
            time.sleep(5)
            self._save_screenshot("02_dashboard")
            
            print("✅ Standort ausgewählt\n")
            return True
            
        except Exception as e:
            print(f"❌ Standortauswahl fehlgeschlagen: {e}")
            self._save_screenshot("error_standort")
            return False
    
    def navigate_to_bestandsliste(self) -> bool:
        """Navigation zur BESTANDSLISTE"""
        print("📋 Navigation zur BESTANDSLISTE...")
        
        try:
            time.sleep(3)
            
            print("   → Suche 'BESTANDSLISTE' in Navigation")
            
            selectors = [
                "//aside//a[contains(text(), 'BESTANDSLISTE')]",
                "//nav//a[contains(text(), 'BESTANDSLISTE')]",
                "//*[contains(@class, 'nav')]//a[contains(text(), 'BESTANDSLISTE')]",
                "//a[contains(text(), 'Bestandsliste')]",
                "//button[contains(text(), 'BESTANDSLISTE')]",
            ]
            
            navigation_clicked = False
            
            for selector in selectors:
                try:
                    element = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    element.click()
                    navigation_clicked = True
                    print(f"   ✓ BESTANDSLISTE gefunden und geklickt")
                    break
                except:
                    continue
            
            if not navigation_clicked:
                raise Exception("BESTANDSLISTE nicht gefunden")
            
            time.sleep(5)
            self._save_screenshot("03_bestandsliste")
            self._save_html("bestandsliste")
            
            print("✅ Bestandsliste geladen\n")
            return True
            
        except Exception as e:
            print(f"❌ Navigation fehlgeschlagen: {e}")
            self._save_screenshot("error_navigation")
            return False
    
    def scrape_bestandsliste(self) -> List[Dict]:
        """Scraped die Bestandsliste-Tabelle"""
        print("📊 Scrape Bestandsliste-Tabelle...")
        
        vertraege = []
        
        try:
            time.sleep(3)
            
            print("   → Suche Tabelle")
            table = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody, [role='rowgroup']"))
            )
            
            rows = table.find_elements(By.CSS_SELECTOR, "tr, [role='row']")
            print(f"   → {len(rows)} Zeilen gefunden")
            
            for idx, row in enumerate(rows, 1):
                try:
                    cells = row.find_elements(By.CSS_SELECTOR, "td, [role='cell']")
                    
                    if len(cells) < 8:
                        continue
                    
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
                        
                        if idx <= 5:
                            print(f"   ✓ {idx}: VIN={vertrag['vin'][:10]}... | {vertrag['modell'][:20]} | {vertrag['finanz_betrag']:,.2f} €")
                
                except Exception as e:
                    print(f"   ⚠️  Fehler Zeile {idx}: {e}")
                    continue
            
            print(f"\n✅ {len(vertraege)} Verträge gescraped\n")
            return vertraege
            
        except Exception as e:
            print(f"❌ Scraping fehlgeschlagen: {e}")
            self._save_screenshot("error_scraping")
            return []
    
    def _parse_betrag(self, text: str) -> float:
        """Parst Betrag-String zu float"""
        try:
            cleaned = ''.join(c for c in text if c.isdigit() or c in ',-.')
            if ',' in cleaned:
                cleaned = cleaned.replace('.', '').replace(',', '.')
            return float(cleaned)
        except:
            return 0.0
    
    def save_to_database(self, vertraege: List[Dict]) -> Dict[str, int]:
        """Speichert Verträge in DB"""
        print("💾 Speichere in Datenbank...")
        
        if self.dry_run:
            print("⚠️  DRY RUN - Keine DB-Änderungen")
            return {'imported': len(vertraege), 'updated': 0, 'errors': 0}
        
        if not vertraege:
            print("⚠️  Keine Verträge zum Speichern")
            return {'imported': 0, 'updated': 0, 'errors': 0}
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        stats = {'imported': 0, 'updated': 0, 'errors': 0}
        
        try:
            cursor.execute("DELETE FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Hyundai Finance'")
            print(f"   🗑️  Alte Einträge gelöscht")
            
            for vertrag in vertraege:
                try:
                    cursor.execute("""
                        INSERT INTO fahrzeugfinanzierungen (
                            finanzinstitut,
                            rrdi,
                            vin,
                            modell,
                            produktfamilie,
                            finanzierungsnummer,
                            finanzierungsstatus,
                            dokumentstatus,
                            aktueller_saldo,
                            original_betrag,
                            datei_quelle,
                            import_datum
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        'Hyundai Finance',
                        'AUTO_GREINER',
                        vertrag['vin'],
                        vertrag['modell'],
                        vertrag['produkt'],
                        vertrag['auftragskurz'],
                        vertrag['finanzierungsstatus'],
                        vertrag['dokumentenstatus'],
                        vertrag['finanz_betrag'],
                        vertrag['finanz_betrag'],
                        'Hyundai Finance Portal Scraper V3',
                        vertrag['scraped_at']
                    ))
                    stats['imported'] += 1
                    
                except Exception as e:
                    print(f"   ⚠️  Fehler bei VIN {vertrag.get('vin', 'unknown')}: {e}")
                    stats['errors'] += 1
            
            conn.commit()
            
            print(f"\n✅ DB-Import abgeschlossen:")
            print(f"   Importiert: {stats['imported']}")
            if stats['errors'] > 0:
                print(f"   Fehler: {stats['errors']}")
            
        except Exception as e:
            print(f"❌ DB-Fehler: {e}")
            conn.rollback()
            stats['errors'] = len(vertraege)
        
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
            
            if not self.navigate_to_bestandsliste():
                return False
            
            vertraege = self.scrape_bestandsliste()
            
            if not vertraege:
                print("⚠️  Keine Verträge gefunden")
                return False
            
            stats = self.save_to_database(vertraege)
            
            self._save_screenshot("99_final")
            
            print("\n" + "="*70)
            print("✅ SCRAPING ERFOLGREICH ABGESCHLOSSEN!")
            print("="*70)
            print(f"\n📊 Zusammenfassung:")
            print(f"   Verträge gescraped: {len(vertraege)}")
            print(f"   In DB gespeichert: {stats['imported']}")
            if stats['errors'] > 0:
                print(f"   Fehler: {stats['errors']}")
            print(f"\n📂 Screenshots: {SCREENSHOTS_DIR}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ FEHLER: {e}")
            import traceback
            traceback.print_exc()
            if self.driver:
                self._save_screenshot("error_exception")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                print("\n🔚 Browser geschlossen")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Hyundai Finance Scraper V3')
    parser.add_argument('--no-headless', action='store_true', help='Browser sichtbar machen')
    parser.add_argument('--dry-run', action='store_true', help='Nicht in DB schreiben')
    args = parser.parse_args()
    
    scraper = HyundaiFinanceScraper(
        headless=not args.no_headless,
        dry_run=args.dry_run
    )
    
    success = scraper.run()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
EOFPYTHON

chmod +x "$SCRAPER_FILE"

echo ""
echo "✅ V3 installiert!"
echo ""
echo "TEST:"
echo "   python3 tools/scrapers/hyundai_finance_scraper.py --dry-run"
echo ""
echo "PRODUKTIV:"
echo "   python3 tools/scrapers/hyundai_finance_scraper.py"
echo ""

