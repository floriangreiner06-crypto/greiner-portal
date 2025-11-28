#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leasys Touch API Client
========================
Direkter API-Zugriff auf Leasys SAP OData Services.

Workflow:
1. Selenium-Login um Session-Cookies zu bekommen
2. Requests mit Cookies für API-Calls

Erstellt: 2025-11-28
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Konfiguration
BASE_URL = "https://e-touch.leasys.com"
ODATA_BASE = f"{BASE_URL}/sap/opu/odata/sap/ZNFC_P23_SRV"
SCREENSHOTS_DIR = "/tmp/leasys_screenshots"


class LeasysAPIClient:
    """Client für Leasys Touch API."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.cookies = None
        self.logged_in = False
        
        # Standard Headers für OData
        self.session.headers.update({
            'Accept': 'application/json',
            'Accept-Language': 'de-DE',
            'Content-Type': 'application/json',
        })
    
    def _setup_driver(self, headless: bool = True) -> webdriver.Chrome:
        """Initialisiert den Chrome WebDriver."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--lang=de-DE')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(5)
        return driver
    
    def login(self, headless: bool = True) -> bool:
        """
        Führt Login durch und extrahiert Session-Cookies.
        
        Returns:
            bool: True wenn Login erfolgreich
        """
        print("🔐 Starte Leasys Login...")
        driver = None
        
        try:
            driver = self._setup_driver(headless)
            driver.get(BASE_URL)
            time.sleep(3)
            
            # Username eingeben
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[name='UserName']"))
            )
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Password eingeben
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Submit - verschiedene Selektoren versuchen
            from selenium.webdriver.common.keys import Keys
            
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "#submitButton",
                "span#submitButton",
                ".submit"
            ]
            
            submit_btn = None
            for selector in submit_selectors:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, selector)
                    if btn.is_displayed():
                        submit_btn = btn
                        break
                except:
                    continue
            
            if not submit_btn:
                # Fallback: Alle Inputs durchsuchen
                inputs = driver.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    inp_type = inp.get_attribute("type") or ""
                    inp_value = inp.get_attribute("value") or ""
                    if inp_type == "submit" or "sign" in inp_value.lower():
                        submit_btn = inp
                        break
            
            if submit_btn:
                submit_btn.click()
            else:
                # Letzter Fallback: Enter-Taste im Password-Feld
                password_field.send_keys(Keys.RETURN)
            
            # Warte auf Dashboard
            time.sleep(8)
            
            # Prüfe ob Login erfolgreich (Dashboard geladen)
            if "touch" in driver.current_url.lower() or "dashboard" in driver.page_source.lower():
                print("✅ Login erfolgreich!")
                
                # Cookies extrahieren
                selenium_cookies = driver.get_cookies()
                for cookie in selenium_cookies:
                    self.session.cookies.set(
                        cookie['name'],
                        cookie['value'],
                        domain=cookie.get('domain', ''),
                        path=cookie.get('path', '/')
                    )
                
                self.logged_in = True
                print(f"   📦 {len(selenium_cookies)} Cookies extrahiert")
                return True
            else:
                print("❌ Login fehlgeschlagen")
                return False
                
        except Exception as e:
            print(f"❌ Login-Fehler: {e}")
            return False
            
        finally:
            if driver:
                driver.quit()
    
    def get_master_agreements(self, 
                               sales_area_code: str = "O 50020901",
                               distr_channel: str = "I2",
                               bp_id: str = "1186289565",
                               sales_area_mngr: str = "1185834152") -> list:
        """
        Holt alle verfügbaren Master Agreements.
        
        Args:
            sales_area_code: Sales Area Code (default: Opel Germany)
            distr_channel: Distribution Channel
            bp_id: Business Partner ID (Greiner)
            sales_area_mngr: Sales Area Manager ID
            
        Returns:
            list: Liste der Master Agreements
        """
        if not self.logged_in:
            raise Exception("Nicht eingeloggt! Erst login() aufrufen.")
        
        # OData Filter bauen
        filter_parts = [
            f"salesAreaCode eq '{sales_area_code}'",
            f"distrChannelCode eq '{distr_channel}'",
            f"bpId eq '{bp_id}'",
            f"salesAreaMngr eq '{sales_area_mngr}'",
            "BbSwitch eq false",
            f"SalesMngIdL4 eq '{sales_area_mngr}'",
            "SalesMngIdL5 eq ''",
            "SalesMngIdL6 eq ''",
            "DemoFlag eq false",
            "Vtc eq false"
        ]
        
        filter_str = " and ".join(filter_parts)
        
        url = f"{ODATA_BASE}/QUOT_TYPE('ZEV7')/MAST_AG"
        params = {
            '$skip': 0,
            '$top': 100,
            '$filter': filter_str,
            '$inlinecount': 'allpages'
        }
        
        print(f"📡 API-Call: MAST_AG")
        response = self.session.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('d', {}).get('results', [])
            count = data.get('d', {}).get('__count', 0)
            print(f"   ✅ {count} Master Agreements gefunden")
            return results
        else:
            print(f"   ❌ Fehler: {response.status_code}")
            return []
    
    def get_brands(self, sales_area_code: str = "O 50020901") -> list:
        """Holt alle verfügbaren Marken."""
        if not self.logged_in:
            raise Exception("Nicht eingeloggt!")
        
        url = f"{ODATA_BASE}/BRAND"
        params = {
            '$skip': 0,
            '$top': 200,
            '$filter': f"salesAreaCode eq '{sales_area_code}'",
            '$inlinecount': 'allpages'
        }
        
        print(f"📡 API-Call: BRAND")
        response = self.session.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('d', {}).get('results', [])
            print(f"   ✅ {len(results)} Marken gefunden")
            return results
        else:
            print(f"   ❌ Fehler: {response.status_code}")
            return []
    
    def get_vehicles(self, brand: str = None, model: str = None) -> list:
        """Holt Fahrzeuge (optional gefiltert nach Marke/Modell)."""
        if not self.logged_in:
            raise Exception("Nicht eingeloggt!")
        
        url = f"{ODATA_BASE}/VHL_TYPE"
        params = {
            '$skip': 0,
            '$top': 100,
            '$inlinecount': 'allpages'
        }
        
        if brand:
            params['$filter'] = f"brand eq '{brand}'"
        
        print(f"📡 API-Call: VHL_TYPE")
        response = self.session.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('d', {}).get('results', [])
            print(f"   ✅ {len(results)} Fahrzeuge gefunden")
            return results
        else:
            print(f"   ❌ Fehler: {response.status_code}")
            return []
    
    def search_master_agreement(self, description_contains: str) -> list:
        """
        Sucht Master Agreements nach Beschreibung.
        
        Args:
            description_contains: Suchbegriff in der Beschreibung
            
        Returns:
            list: Gefundene Master Agreements
        """
        all_agreements = self.get_master_agreements()
        
        matches = [
            ma for ma in all_agreements 
            if description_contains.lower() in ma.get('mastAgDescription', '').lower()
        ]
        
        print(f"🔍 Suche '{description_contains}': {len(matches)} Treffer")
        return matches
    
    def get_agreement_details(self, mast_ag_id: str) -> dict:
        """Holt Details zu einem Master Agreement."""
        if not self.logged_in:
            raise Exception("Nicht eingeloggt!")
        
        url = f"{ODATA_BASE}/MAST_AG('{mast_ag_id}')"
        
        print(f"📡 API-Call: MAST_AG({mast_ag_id})")
        response = self.session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('d', {})
        else:
            print(f"   ❌ Fehler: {response.status_code}")
            return {}


def main():
    """Test-Funktion."""
    print("=" * 60)
    print("🚗 LEASYS API CLIENT TEST")
    print("=" * 60)
    
    # Credentials laden
    with open('/opt/greiner-portal/config/credentials.json') as f:
        creds = json.load(f)
    
    leasys_creds = creds['external_systems']['leasys']
    
    # Client erstellen
    client = LeasysAPIClient(
        username=leasys_creds['username'],
        password=leasys_creds['password']
    )
    
    # Login
    if client.login(headless=True):
        print("\n" + "=" * 60)
        
        # Master Agreements abrufen
        agreements = client.get_master_agreements()
        
        print("\n📋 Verfügbare Master Agreements:")
        print("-" * 60)
        for ma in agreements[:10]:  # Erste 10
            ma_id = ma.get('mastAgId', '')
            desc = ma.get('mastAgDescription', '')
            fav = "⭐" if ma.get('Favorite') == 'X' else "  "
            print(f"   {fav} {ma_id}: {desc}")
        
        if len(agreements) > 10:
            print(f"   ... und {len(agreements) - 10} weitere")
        
        # Suche nach Opel 36-60
        print("\n🔍 Suche 'Opel 36':")
        matches = client.search_master_agreement("Opel 36")
        for ma in matches:
            print(f"   → {ma.get('mastAgId')}: {ma.get('mastAgDescription')}")
    
    print("\n✅ Test abgeschlossen")


if __name__ == "__main__":
    main()
