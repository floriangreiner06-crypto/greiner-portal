#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyundai Finance - Bestandsliste Filter Debug
============================================
Analysiert die Filter/Input-Felder auf der Bestandsliste-Seite

Author: Claude AI
Date: 2025-11-10
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
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Credentials
FIONA_URL = "https://fiona.hyundaifinance.eu/#/dealer-portal"
USERNAME = "Christian.aichinger@auto-greiner.de"
PASSWORD = "Hyundaikona2020!"
SCREENSHOTS_DIR = "/tmp/hyundai_debug"


class BestandslisteDebugger:
    """Debugger für Bestandsliste-Filter"""
    
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.wait = None
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        print(f"📸 Screenshots: {SCREENSHOTS_DIR}\n")
    
    def setup_driver(self):
        """Chrome initialisieren"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)
        print("✅ Chrome gestartet\n")
    
    def screenshot(self, name):
        """Screenshot speichern"""
        filepath = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
        self.driver.save_screenshot(filepath)
        print(f"📸 {name}.png")
    
    def login_fiona(self):
        """Login auf FIONA Portal"""
        print("🔑 LOGIN auf FIONA Portal...")
        self.driver.get(FIONA_URL)
        time.sleep(2)
        
        # Username
        username_field = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[type='email']"))
        )
        username_field.send_keys(USERNAME)
        
        # Password
        password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_field.send_keys(PASSWORD)
        
        # Login
        login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_btn.click()
        
        time.sleep(3)
        print("✅ Login erfolgreich\n")
        self.screenshot("01_nach_login")
    
    def select_standort(self):
        """Standort 'Auto Greiner' auswählen"""
        print("📍 STANDORT wählen...")
        time.sleep(2)
        
        # Suche Standort-Dropdown oder Liste
        standort_link = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Auto Greiner') or contains(text(), 'Greiner')]"))
        )
        standort_link.click()
        
        time.sleep(2)
        print("✅ Standort gewählt\n")
        self.screenshot("02_standort_gewaehlt")
    
    def open_ekf_portal(self):
        """Einkaufsfinanzierung-Kachel klicken → EKF Portal"""
        print("🏦 ÖFFNE EKF Portal...")
        time.sleep(2)
        
        # Finde "Einkaufsfinanzierung" Kachel
        ekf_tile = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'tile') or contains(@class, 'card')]//span[contains(text(), 'Einkaufsfinanzierung')]"))
        )
        ekf_tile.click()
        
        time.sleep(3)
        
        # Tab-Wechsel zu EKF Portal
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[1])
            print("✅ Tab-Wechsel zu EKF Portal")
        
        time.sleep(2)
        print(f"   URL: {self.driver.current_url}\n")
        self.screenshot("03_ekf_portal")
    
    def navigate_to_bestandsliste(self):
        """Navigation zu BESTANDSLISTE"""
        print("📋 NAVIGATION zu Bestandsliste...")
        time.sleep(2)
        
        # Finde Bestandsliste-Link
        bestandsliste_link = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'BESTANDSLISTE') or contains(text(), 'Bestandsliste')]"))
        )
        bestandsliste_link.click()
        
        time.sleep(3)
        print("✅ Bestandsliste geladen\n")
        self.screenshot("04_bestandsliste")
    
    def analyze_filter_inputs(self):
        """HAUPTFUNKTION: Analysiere alle Input-Felder und Filter"""
        print("\n" + "="*70)
        print("🔍 ANALYSIERE FILTER & INPUT-FELDER")
        print("="*70 + "\n")
        
        filters = {
            'text_inputs': [],
            'select_dropdowns': [],
            'date_inputs': [],
            'checkboxes': [],
            'radio_buttons': [],
            'buttons': []
        }
        
        # 1. TEXT INPUTS
        print("📝 TEXT INPUTS:")
        text_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input:not([type])")
        for idx, inp in enumerate(text_inputs, 1):
            info = {
                'id': inp.get_attribute('id'),
                'name': inp.get_attribute('name'),
                'placeholder': inp.get_attribute('placeholder'),
                'class': inp.get_attribute('class'),
                'value': inp.get_attribute('value')
            }
            filters['text_inputs'].append(info)
            print(f"   {idx}. ID: {info['id']}, Name: {info['name']}, Placeholder: {info['placeholder']}")
        
        # 2. SELECT DROPDOWNS
        print("\n📋 SELECT DROPDOWNS:")
        selects = self.driver.find_elements(By.TAG_NAME, "select")
        for idx, sel in enumerate(selects, 1):
            options = sel.find_elements(By.TAG_NAME, "option")
            option_texts = [opt.text for opt in options]
            info = {
                'id': sel.get_attribute('id'),
                'name': sel.get_attribute('name'),
                'options': option_texts
            }
            filters['select_dropdowns'].append(info)
            print(f"   {idx}. ID: {info['id']}, Name: {info['name']}")
            print(f"       Optionen: {', '.join(option_texts[:5])}...")
        
        # 3. DATE INPUTS
        print("\n📅 DATE INPUTS:")
        date_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='date']")
        for idx, inp in enumerate(date_inputs, 1):
            info = {
                'id': inp.get_attribute('id'),
                'name': inp.get_attribute('name')
            }
            filters['date_inputs'].append(info)
            print(f"   {idx}. ID: {info['id']}, Name: {info['name']}")
        
        # 4. CHECKBOXES
        print("\n☑️  CHECKBOXES:")
        checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        for idx, cb in enumerate(checkboxes, 1):
            info = {
                'id': cb.get_attribute('id'),
                'name': cb.get_attribute('name'),
                'checked': cb.is_selected()
            }
            filters['checkboxes'].append(info)
            print(f"   {idx}. ID: {info['id']}, Name: {info['name']}, Checked: {info['checked']}")
        
        # 5. RADIO BUTTONS
        print("\n🔘 RADIO BUTTONS:")
        radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
        for idx, rb in enumerate(radios, 1):
            info = {
                'id': rb.get_attribute('id'),
                'name': rb.get_attribute('name'),
                'value': rb.get_attribute('value'),
                'checked': rb.is_selected()
            }
            filters['radio_buttons'].append(info)
            print(f"   {idx}. Name: {info['name']}, Value: {info['value']}, Checked: {info['checked']}")
        
        # 6. BUTTONS
        print("\n🔘 BUTTONS:")
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        for idx, btn in enumerate(buttons, 1):
            text = btn.text.strip()
            if text:
                info = {
                    'text': text,
                    'type': btn.get_attribute('type'),
                    'class': btn.get_attribute('class')
                }
                filters['buttons'].append(info)
                print(f"   {idx}. Text: '{text}', Type: {info['type']}")
        
        # HTML speichern für detaillierte Analyse
        html_file = os.path.join(SCREENSHOTS_DIR, "bestandsliste_page.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
        print(f"\n💾 HTML gespeichert: {html_file}")
        
        # JSON speichern
        json_file = os.path.join(SCREENSHOTS_DIR, "filter_analysis.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(filters, f, indent=2, ensure_ascii=False)
        print(f"💾 JSON gespeichert: {json_file}")
        
        self.screenshot("05_bestandsliste_filter_analyse")
        
        return filters
    
    def run(self):
        """Hauptablauf"""
        try:
            print("\n" + "="*70)
            print("🚀 HYUNDAI FINANCE - BESTANDSLISTE FILTER DEBUG")
            print("="*70 + "\n")
            
            self.setup_driver()
            self.login_fiona()
            self.select_standort()
            self.open_ekf_portal()
            self.navigate_to_bestandsliste()
            
            filters = self.analyze_filter_inputs()
            
            print("\n" + "="*70)
            print("✅ ANALYSE ERFOLGREICH!")
            print("="*70)
            print(f"\n📂 Ergebnisse:")
            print(f"   Screenshots: {SCREENSHOTS_DIR}")
            print(f"   HTML: bestandsliste_page.html")
            print(f"   JSON: filter_analysis.json")
            
            # Zusammenfassung
            print(f"\n📊 ZUSAMMENFASSUNG:")
            print(f"   Text Inputs: {len(filters['text_inputs'])}")
            print(f"   Dropdowns: {len(filters['select_dropdowns'])}")
            print(f"   Date Inputs: {len(filters['date_inputs'])}")
            print(f"   Checkboxes: {len(filters['checkboxes'])}")
            print(f"   Radio Buttons: {len(filters['radio_buttons'])}")
            print(f"   Buttons: {len(filters['buttons'])}")
            
            if not self.headless:
                print("\n⏸️  Browser bleibt offen...")
                print("   Drücke Enter zum Schließen...")
                input()
            
        except Exception as e:
            print(f"\n❌ FEHLER: {e}")
            import traceback
            traceback.print_exc()
            self.screenshot("ERROR")
        
        finally:
            if self.driver:
                self.driver.quit()
                print("\n🔚 Browser geschlossen")


def main():
    """Hauptfunktion"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  HYUNDAI FINANCE - BESTANDSLISTE FILTER DEBUG                    ║
║  Analysiert alle Input-Felder auf der Bestandsliste-Seite       ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    debugger = BestandslisteDebugger(headless=False)
    debugger.run()


if __name__ == "__main__":
    main()
