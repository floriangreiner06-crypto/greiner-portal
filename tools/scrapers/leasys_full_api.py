#!/usr/bin/env python3
"""
Leasys Full API Client
======================
Komplette Integration für Fahrzeugsuche und Ratenberechnung.
Basiert auf HAR-Analyse vom 28.11.2024.

Verwendung:
    from leasys_full_api import LeasysAPI
    
    api = LeasysAPI()
    api.authenticate()
    
    # Fahrzeuge suchen
    vehicles = api.get_vehicles(brand="OPEL", fuel="Benzin")
    
    # Rate berechnen (benötigt EVALUATION Flow)
    # rate = api.calculate_rate(product_id, duration=48, mileage=40000)
"""

import json
import time
import pickle
import os
from datetime import datetime
import requests

# Optional: Selenium für Authentifizierung
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class LeasysAPI:
    """Leasys OData API Client."""
    
    BASE_URL = "https://e-touch.leasys.com/sap/opu/odata/sap/ZNFC_P23_SRV"
    COOKIES_FILE = "/tmp/leasys_session.pkl"
    
    # Standard-Parameter (Autohaus Greiner)
    DEFAULTS = {
        "salesAreaCode": "O 50020901",
        "quotTypeCode": "ZEV7",
        "distrChannelCode": "I2",
        "bpId": "1186289565",
        "salesMngId": "1185834152",
        "vhlTypeCode": "ZITRSL1",  # PKW
    }
    
    # Marken-Codes
    BRANDS = {
        "OPEL": "000020",
        "FIAT": "00",
        "JEEP": "57",
        "ALFA ROMEO": "83",
        "LANCIA": "70",
        "ABARTH": "66",
        "CITROEN": "000091",
        "PEUGEOT": "000155",
        "DS": "002775",
        "LEAPMOTOR": "B00151",
    }
    
    # Kraftstoff-Codes
    FUEL_CODES = {
        "Benzin": "B",
        "Diesel": "D",
        "Elektro": "E",
        "Hybrid": "H",
        "PHEV": "P",
    }
    
    # Master Agreements (häufig verwendete)
    MASTER_AGREEMENTS = {
        "KM LEASING Opel 36-60": "1000026115",
        "KM LEASING Opel 24-35": "1000026114",
        "BLACK WEEKS 36-60": "1000026398",
        "BLACK WEEKS 24-35": "1000026397",
    }
    
    def __init__(self, credentials_path="/opt/greiner-portal/config/credentials.json"):
        """Initialisiert den Client."""
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        self.authenticated = False
        self.csrf_token = None
        
        # Credentials laden
        if os.path.exists(credentials_path):
            with open(credentials_path) as f:
                creds = json.load(f)
            self.credentials = creds.get('external_systems', {}).get('leasys', {})
        else:
            self.credentials = {}
    
    def authenticate(self, force=False):
        """
        Authentifiziert via Selenium und speichert Cookies.
        
        Args:
            force: Erzwingt neue Authentifizierung
        
        Returns:
            bool: True wenn erfolgreich
        """
        # Versuche gespeicherte Cookies
        if not force and os.path.exists(self.COOKIES_FILE):
            try:
                with open(self.COOKIES_FILE, 'rb') as f:
                    cookies = pickle.load(f)
                for c in cookies:
                    self.session.cookies.set(c['name'], c['value'])
                
                if self._test_session():
                    self.authenticated = True
                    print("✅ Session aus Cache geladen")
                    return True
            except Exception as e:
                print(f"⚠️ Cookie-Laden fehlgeschlagen: {e}")
        
        # Neue Auth via Selenium
        if not SELENIUM_AVAILABLE:
            print("❌ Selenium nicht verfügbar")
            return False
        
        print("🔐 Authentifizierung via Selenium...")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            driver.get("https://e-touch.leasys.com")
            time.sleep(3)
            
            wait = WebDriverWait(driver, 30)
            username = wait.until(EC.presence_of_element_located((By.ID, "userNameInput")))
            username.send_keys(self.credentials['username'])
            
            password = driver.find_element(By.ID, "passwordInput")
            password.send_keys(self.credentials['password'])
            password.send_keys(Keys.RETURN)
            
            time.sleep(10)
            
            cookies = driver.get_cookies()
            
            with open(self.COOKIES_FILE, 'wb') as f:
                pickle.dump(cookies, f)
            
            for c in cookies:
                self.session.cookies.set(c['name'], c['value'])
            
            self.authenticated = True
            print(f"✅ Authentifiziert ({len(cookies)} Cookies)")
            return True
            
        except Exception as e:
            print(f"❌ Auth fehlgeschlagen: {e}")
            return False
        finally:
            driver.quit()
    
    def _test_session(self):
        """Testet ob Session gültig ist."""
        try:
            resp = self.session.get(f"{self.BASE_URL}/BRAND", params={"$top": 1})
            return resp.status_code == 200 and 'results' in resp.text
        except:
            return False
    
    def get_vehicles(self, brand="OPEL", fuel=None, mast_ag_id="1000026115"):
        """
        Holt Fahrzeugliste mit Preisen.
        
        Args:
            brand: Markenname (OPEL, FIAT, etc.)
            fuel: Kraftstoff (Benzin, Diesel, Elektro) - optional
            mast_ag_id: Master Agreement ID
        
        Returns:
            Liste von Fahrzeugen mit Preisen
        """
        brand_code = self.BRANDS.get(brand.upper(), brand)
        
        filter_parts = [
            f"vhlTypeCode eq '{self.DEFAULTS['vhlTypeCode']}'",
            f"brandCode eq '{brand_code}'",
            f"quotTypeCode eq '{self.DEFAULTS['quotTypeCode']}'",
            f"salesAreaCode eq '{self.DEFAULTS['salesAreaCode']}'",
            f"distrChannelCode eq '{self.DEFAULTS['distrChannelCode']}'",
            f"MaId eq '{mast_ag_id}'",
            f"SoldToParty eq '{self.DEFAULTS['bpId']}'",
            f"SalesMngId eq '{self.DEFAULTS['salesMngId']}'",
            "CanaryFlag eq false",
        ]
        
        if fuel:
            fuel_code = self.FUEL_CODES.get(fuel, fuel)
            filter_parts.append(f"engineCode eq '{fuel_code}'")
        
        resp = self.session.get(
            f"{self.BASE_URL}/VEHICLE",
            params={
                "$skip": 0,
                "$top": 200,
                "$filter": " and ".join(filter_parts),
                "$inlinecount": "allpages"
            }
        )
        
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('d', {}).get('results', [])
            
            vehicles = []
            for v in results:
                vehicles.append({
                    "product_id": v.get("productId"),
                    "brand": v.get("brand"),
                    "model": v.get("bmvs"),
                    "manufacturer_code": v.get("manuf"),
                    "list_price_netto": float(v.get("listPrice") or 0),
                    "list_price_brutto": float(v.get("ListPriceBrutto") or 0),
                    "fuel": v.get("engineCode"),
                    "co2": v.get("co2"),
                    "gamma": v.get("Gamma"),
                    "allestimento": v.get("Allestimento"),
                })
            
            return vehicles
        
        return []
    
    def get_models(self, brand="OPEL"):
        """Holt verfügbare Modelle für eine Marke."""
        brand_code = self.BRANDS.get(brand.upper(), brand)
        
        resp = self.session.get(
            f"{self.BASE_URL}/BRAND('{brand_code}')/VHL_SET",
            params={"$top": 100}
        )
        
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('d', {}).get('results', [])
            return [
                {
                    "code": r.get("vhlSetCode"),
                    "name": r.get("vhlSet"),
                }
                for r in results
            ]
        return []
    
    def get_fuel_types(self):
        """Holt verfügbare Kraftstoffarten."""
        resp = self.session.get(
            f"{self.BASE_URL}/FUEL",
            params={
                "$top": 100,
                "$filter": (
                    f"salesAreaCode eq '{self.DEFAULTS['salesAreaCode']}' and "
                    f"quotTypeCode eq '{self.DEFAULTS['quotTypeCode']}'"
                )
            }
        )
        
        if resp.status_code == 200:
            data = resp.json()
            return data.get('d', {}).get('results', [])
        return []
    
    def get_rate_info(self, product_id, mast_ag_id="1000026115"):
        """
        Holt Basis-Finanzierungsinfos für ein Fahrzeug.
        
        Hinweis: Vollständige Ratenberechnung erfordert EVALUATION-Flow.
        """
        resp = self.session.get(
            f"{self.BASE_URL}/FIN_CALC",
            params={
                "$filter": (
                    f"SoldId eq '{self.DEFAULTS['bpId']}' and "
                    f"MastAgId eq '{mast_ag_id}' and "
                    f"ProcessType eq '{self.DEFAULTS['quotTypeCode']}' and "
                    f"ProductId eq '{product_id}'"
                )
            }
        )
        
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('d', {}).get('results', [])
            if results:
                r = results[0]
                return {
                    "list_price": float(r.get("ListPrice") or 0),
                    "rate_id": r.get("RateId"),
                    "co2": r.get("Co2"),
                }
        return None


# Convenience-Funktion
def get_opel_vehicles(fuel=None):
    """Schnellzugriff auf OPEL-Fahrzeuge."""
    api = LeasysAPI()
    if api.authenticate():
        return api.get_vehicles(brand="OPEL", fuel=fuel)
    return []


if __name__ == "__main__":
    print("🚗 Leasys API Client Test")
    print("=" * 60)
    
    api = LeasysAPI()
    
    if not api.authenticate():
        print("❌ Authentifizierung fehlgeschlagen")
        exit(1)
    
    # Modelle
    print("\n📦 OPEL Modelle:")
    models = api.get_models("OPEL")
    for m in models[:10]:
        print(f"   • {m['name']}")
    
    # Fahrzeuge
    print("\n🚗 OPEL Benzin Fahrzeuge:")
    vehicles = api.get_vehicles(brand="OPEL", fuel="Benzin")
    print(f"   Gefunden: {len(vehicles)}")
    
    for v in vehicles[:5]:
        print(f"\n   {v['model']}")
        print(f"      Brutto: {v['list_price_brutto']:,.2f} €")
        print(f"      ProductID: {v['product_id']}")
    
    print("\n✅ API-Client funktioniert!")
