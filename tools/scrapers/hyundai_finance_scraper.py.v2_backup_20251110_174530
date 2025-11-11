#!/usr/bin/env python3
"""
Hyundai Finance Portal - Produktions-Scraper
Navigiert zu Einkaufsfinanzierung und extrahiert Bestandsdaten
"""

import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

class HyundaiFinanceScraper:
    """Produktions-Scraper für Hyundai Finance Portal"""
    
    def __init__(self, username: str, password: str):
        self.url = "https://fiona.hyundaifinance.eu/#/dealer-portal"
        self.username = username
        self.password = password
        self.driver = None
        self.screenshot_dir = "/tmp/hyundai_screenshots"
        
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    def setup_driver(self):
        """Chrome WebDriver initialisieren"""
        print("🔧 Initialisiere WebDriver...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        print("✅ WebDriver bereit")
    
    def take_screenshot(self, name: str):
        """Screenshot erstellen"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.png"
        filepath = os.path.join(self.screenshot_dir, filename)
        self.driver.save_screenshot(filepath)
        print(f"📸 {filename}")
    
    def save_html(self, name: str):
        """HTML speichern"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.html"
        filepath = os.path.join(self.screenshot_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
        print(f"💾 {filename}")
    
    def login(self):
        """Login durchführen"""
        print("\n📍 Login...")
        self.driver.get(self.url)
        time.sleep(5)
        
        inputs = self.driver.find_elements(By.TAG_NAME, "input")
        username_field = None
        password_field = None
        
        for inp in inputs:
            input_type = inp.get_attribute("type")
            if input_type in ["text", "email"] and not username_field:
                username_field = inp
            elif input_type == "password" and not password_field:
                password_field = inp
        
        username_field.clear()
        username_field.send_keys(self.username)
        password_field.clear()
        password_field.send_keys(self.password)
        
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "login" in btn.text.lower() or "anmeld" in btn.text.lower():
                btn.click()
                break
        
        time.sleep(5)
        print("✅ Login erfolgreich")
    
    def select_location(self):
        """Standort auswählen"""
        print("\n📍 Standort auswählen...")
        
        elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Auto Greiner')]")
        
        if elements:
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
            
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                btn_text = btn.text.lower()
                if any(word in btn_text for word in ["bestät", "weiter", "ok", "auswähl"]):
                    btn.click()
                    break
            
            time.sleep(5)
            print("✅ Standort ausgewählt")
        else:
            print("⚠️  Keine Standortauswahl nötig")
    
    def navigate_to_einkaufsfinanzierung(self):
        """Navigiere zu Einkaufsfinanzierung"""
        print("\n📍 Navigiere zu Einkaufsfinanzierung...")
        
        self.take_screenshot("10_dashboard")
        self.save_html("10_dashboard")
        
        elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Einkaufsfinanzierung')]")
        
        if elements:
            print(f"   ✓ {len(elements)} 'Einkaufsfinanzierung' Elemente gefunden")
            
            for elem in elements:
                try:
                    parent = elem.find_element(By.XPATH, "./ancestor::*[contains(@class, 'card') or contains(@class, 'tile') or contains(@class, 'box')]")
                    parent.click()
                    print("   ✓ Einkaufsfinanzierung-Kachel angeklickt")
                    break
                except:
                    try:
                        elem.click()
                        print("   ✓ Einkaufsfinanzierung-Link angeklickt")
                        break
                    except:
                        continue
            
            time.sleep(10)
            
            self.take_screenshot("11_einkaufsfinanzierung")
            self.save_html("11_einkaufsfinanzierung")
            
            print("✅ Navigation erfolgreich")
            return True
        else:
            print("❌ 'Einkaufsfinanzierung' nicht gefunden!")
            return False
    
    def analyze_bestandsliste(self):
        """Analysiere die Bestandsliste"""
        print("\n📍 Analysiere Bestandsliste...")
        
        print(f"   URL: {self.driver.current_url}")
        print(f"   Title: {self.driver.title}")
        
        tables = self.driver.find_elements(By.TAG_NAME, "table")
        print(f"\n   📊 Tabellen gefunden: {len(tables)}")
        
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        print(f"\n   🔍 Suche Export-Button...")
        
        export_keywords = ["export", "download", "excel", "csv", "herunterladen"]
        for btn in buttons:
            btn_text = btn.text.lower()
            for keyword in export_keywords:
                if keyword in btn_text:
                    print(f"      ✓ Gefunden: '{btn.text}'")
        
        links = self.driver.find_elements(By.TAG_NAME, "a")
        print(f"\n   🔗 Links gefunden: {len(links)}")
        
        for i, link in enumerate(links[:10], 1):
            try:
                text = link.text.strip()
                href = link.get_attribute("href")
                if text:
                    print(f"      {i}. {text} → {href}")
            except:
                pass
        
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        keywords = ["VIN", "Fahrzeug", "Finanzierung", "Saldo", "Bestand", "Liste"]
        
        print(f"\n   🔎 Keywords:")
        for keyword in keywords:
            count = body_text.count(keyword)
            if count > 0:
                print(f"      ✓ '{keyword}': {count}x")
    
    def scrape(self):
        """Hauptfunktion"""
        print("\n" + "="*60)
        print("🏢 HYUNDAI FINANCE - EINKAUFSFINANZIERUNG SCRAPER")
        print("="*60)
        
        try:
            self.setup_driver()
            self.login()
            self.select_location()
            
            if self.navigate_to_einkaufsfinanzierung():
                self.analyze_bestandsliste()
                
                time.sleep(5)
                self.take_screenshot("12_final")
                self.save_html("12_final")
                
                print("\n" + "="*60)
                print("✅ SCRAPING ABGESCHLOSSEN!")
                print("="*60)
                print(f"\n📂 Dateien: {self.screenshot_dir}")
                
                return True
            else:
                print("\n❌ Navigation fehlgeschlagen!")
                return False
                
        except Exception as e:
            print(f"\n❌ FEHLER: {e}")
            import traceback
            traceback.print_exc()
            self.take_screenshot("error")
            self.save_html("error")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()


def main():
    username = "Christian.aichinger@auto-greiner.de"
    password = "Hyundaikona2020!"
    
    scraper = HyundaiFinanceScraper(username, password)
    scraper.scrape()


if __name__ == "__main__":
    exit(main())
