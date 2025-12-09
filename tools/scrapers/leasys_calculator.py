"""
Leasys Kalkulations-Scraper
===========================
Automatisiert die Leasing-Kalkulation auf e-touch.leasys.com

Erstellt: 2025-11-28
"""

import json
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class LeasysCalculator:
    """
    Automatisiert Leasing-Kalkulationen auf Leasys Touch.
    """
    
    def __init__(self, username=None, password=None, headless=False):
        self.username = username
        self.password = password
        self.headless = headless
        self.driver = None
        self.logged_in = False
        self.base_url = "https://e-touch.leasys.com"
        
    def _setup_driver(self):
        """Chrome WebDriver konfigurieren."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--lang=de-DE")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.implicitly_wait(10)
        
    def login(self):
        """Bei Leasys Touch einloggen."""
        if self.driver is None:
            self._setup_driver()
            
        print("🔐 Starte Leasys Login...")
        self.driver.get(self.base_url)
        time.sleep(3)
        
        try:
            # Username eingeben
            username_field = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "userNameInput"))
            )
            username_field.clear()
            username_field.send_keys(self.username)
            print(f"   ✅ Username eingegeben")
            
            # Password eingeben
            password_field = self.driver.find_element(By.ID, "passwordInput")
            password_field.clear()
            password_field.send_keys(self.password)
            print(f"   ✅ Password eingegeben")
            
            # Submit - verschiedene Methoden versuchen
            try:
                submit_btn = self.driver.find_element(By.ID, "submitButton")
                submit_btn.click()
            except:
                password_field.send_keys(Keys.RETURN)
            
            print("   ⏳ Warte auf Login...")
            time.sleep(8)
            
            # Prüfe ob Login erfolgreich
            if "touch" in self.driver.current_url.lower() or "dashboard" in self.driver.page_source.lower():
                self.logged_in = True
                print("✅ Login erfolgreich!")
                return True
            else:
                print("❌ Login möglicherweise fehlgeschlagen")
                print(f"   URL: {self.driver.current_url}")
                return False
                
        except Exception as e:
            print(f"❌ Login-Fehler: {e}")
            return False
    
    def navigate_to_new_estimate(self, master_agreement_id):
        """
        Navigiert zum Kalkulationsformular mit der gewählten MA-ID.
        """
        if not self.logged_in:
            if not self.login():
                return False
        
        print(f"\n📋 Navigiere zu New Estimate mit MA {master_agreement_id}...")
        
        try:
            # Klick auf "New Estimate" im Menü
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'New Estimate')]"))
            ).click()
            time.sleep(2)
            
            # Oder über URL direkt
            # self.driver.get(f"{self.base_url}/#/newEstimate")
            
            print("   ✅ New Estimate geöffnet")
            return True
            
        except Exception as e:
            print(f"❌ Navigation fehlgeschlagen: {e}")
            return False
    
    def select_master_agreement(self, ma_id):
        """Master Agreement auswählen."""
        print(f"   🔍 Suche Master Agreement {ma_id}...")
        
        try:
            # Warte auf MA-Liste
            time.sleep(2)
            
            # Suche nach dem MA in der Liste
            ma_element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{ma_id}')]"))
            )
            ma_element.click()
            print(f"   ✅ MA {ma_id} ausgewählt")
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"   ❌ MA nicht gefunden: {e}")
            return False
    
    def fill_vehicle_data(self, brand, model, fuel_type="Benzin"):
        """
        Fahrzeugdaten eingeben.
        
        Args:
            brand: Marke (z.B. "Opel")
            model: Modell (z.B. "Corsa")
            fuel_type: Kraftstoff (Benzin, Diesel, Elektro, Hybrid)
        """
        print(f"\n🚗 Fahrzeugdaten: {brand} {model} ({fuel_type})")
        
        try:
            # Marke auswählen
            brand_dropdown = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//mat-select[@formcontrolname='brand'] | //select[contains(@id, 'brand')]"))
            )
            brand_dropdown.click()
            time.sleep(1)
            
            # Marke in Dropdown finden
            brand_option = self.driver.find_element(By.XPATH, f"//mat-option[contains(., '{brand}')] | //option[contains(., '{brand}')]")
            brand_option.click()
            print(f"   ✅ Marke: {brand}")
            time.sleep(1)
            
            # Modell auswählen
            model_dropdown = self.driver.find_element(By.XPATH, "//mat-select[@formcontrolname='model'] | //select[contains(@id, 'model')]")
            model_dropdown.click()
            time.sleep(1)
            
            model_option = self.driver.find_element(By.XPATH, f"//mat-option[contains(., '{model}')] | //option[contains(., '{model}')]")
            model_option.click()
            print(f"   ✅ Modell: {model}")
            time.sleep(1)
            
            return True
            
        except Exception as e:
            print(f"   ❌ Fahrzeugdaten-Fehler: {e}")
            return False
    
    def fill_financial_data(self, list_price, duration_months=36, annual_km=10000, residual_value=None):
        """
        Finanzierungsdaten eingeben.
        
        Args:
            list_price: Listenpreis in EUR
            duration_months: Laufzeit in Monaten
            annual_km: Jährliche Kilometer
            residual_value: Restwert (optional, sonst automatisch)
        """
        print(f"\n💰 Finanzierungsdaten: {list_price}€, {duration_months} Monate, {annual_km} km/Jahr")
        
        try:
            # Listenpreis
            price_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@formcontrolname, 'price') or contains(@id, 'price') or contains(@name, 'price')]"))
            )
            price_field.clear()
            price_field.send_keys(str(list_price))
            print(f"   ✅ Listenpreis: {list_price}€")
            
            # Laufzeit
            duration_field = self.driver.find_element(By.XPATH, "//input[contains(@formcontrolname, 'duration') or contains(@id, 'duration') or contains(@name, 'months')]")
            duration_field.clear()
            duration_field.send_keys(str(duration_months))
            print(f"   ✅ Laufzeit: {duration_months} Monate")
            
            # Kilometer
            km_field = self.driver.find_element(By.XPATH, "//input[contains(@formcontrolname, 'mileage') or contains(@id, 'km') or contains(@name, 'mileage')]")
            km_field.clear()
            km_field.send_keys(str(annual_km))
            print(f"   ✅ Kilometer: {annual_km}/Jahr")
            
            # Restwert (optional)
            if residual_value:
                rv_field = self.driver.find_element(By.XPATH, "//input[contains(@formcontrolname, 'residual') or contains(@id, 'residual')]")
                rv_field.clear()
                rv_field.send_keys(str(residual_value))
                print(f"   ✅ Restwert: {residual_value}€")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Finanzierungsdaten-Fehler: {e}")
            return False
    
    def calculate(self):
        """Kalkulation durchführen und Rate auslesen."""
        print("\n🧮 Starte Kalkulation...")
        
        try:
            # Berechnen-Button klicken
            calc_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(text(), 'Berechnen') or contains(text(), 'Calculate') or contains(text(), 'Kalkulieren')]"
                    " | //button[contains(@class, 'calculate')]"
                ))
            )
            calc_button.click()
            print("   ⏳ Berechnung läuft...")
            time.sleep(3)
            
            # Rate auslesen
            rate_element = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, 
                    "//*[contains(@class, 'rate') or contains(@class, 'monthly')]"
                    " | //*[contains(text(), '€') and contains(@class, 'result')]"
                ))
            )
            
            rate_text = rate_element.text
            print(f"   ✅ Rate gefunden: {rate_text}")
            
            # Rate parsen
            import re
            rate_match = re.search(r'(\d+[.,]\d+)', rate_text.replace('.', '').replace(',', '.'))
            if rate_match:
                monthly_rate = float(rate_match.group(1))
                return {
                    "success": True,
                    "monthly_rate": monthly_rate,
                    "rate_text": rate_text,
                    "timestamp": datetime.now().isoformat()
                }
            
            return {
                "success": True,
                "rate_text": rate_text,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"   ❌ Kalkulation-Fehler: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def full_calculation(self, ma_id, brand, model, list_price, 
                         duration_months=36, annual_km=10000, residual_value=None):
        """
        Komplette Kalkulation durchführen.
        
        Args:
            ma_id: Master Agreement ID (z.B. "1000026115")
            brand: Marke
            model: Modell
            list_price: Listenpreis
            duration_months: Laufzeit
            annual_km: Jahreskilometer
            residual_value: Restwert (optional)
            
        Returns:
            dict mit Ergebnis
        """
        print("\n" + "=" * 60)
        print("🚗 LEASYS KALKULATION")
        print("=" * 60)
        print(f"MA: {ma_id}")
        print(f"Fahrzeug: {brand} {model}")
        print(f"Preis: {list_price}€")
        print(f"Laufzeit: {duration_months} Monate")
        print(f"Kilometer: {annual_km}/Jahr")
        print("=" * 60)
        
        result = {
            "input": {
                "ma_id": ma_id,
                "brand": brand,
                "model": model,
                "list_price": list_price,
                "duration_months": duration_months,
                "annual_km": annual_km,
                "residual_value": residual_value
            },
            "success": False
        }
        
        try:
            # Login
            if not self.logged_in:
                if not self.login():
                    result["error"] = "Login fehlgeschlagen"
                    return result
            
            # Navigiere zu New Estimate
            if not self.navigate_to_new_estimate(ma_id):
                result["error"] = "Navigation fehlgeschlagen"
                return result
            
            # MA auswählen
            if not self.select_master_agreement(ma_id):
                result["error"] = "MA-Auswahl fehlgeschlagen"
                return result
            
            # Fahrzeugdaten
            if not self.fill_vehicle_data(brand, model):
                result["error"] = "Fahrzeugdaten fehlgeschlagen"
                return result
            
            # Finanzierungsdaten
            if not self.fill_financial_data(list_price, duration_months, annual_km, residual_value):
                result["error"] = "Finanzierungsdaten fehlgeschlagen"
                return result
            
            # Berechnen
            calc_result = self.calculate()
            result.update(calc_result)
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            return result
    
    def screenshot(self, filename="leasys_screenshot.png"):
        """Screenshot speichern."""
        if self.driver:
            self.driver.save_screenshot(filename)
            print(f"📸 Screenshot: {filename}")
    
    def close(self):
        """Browser schließen."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logged_in = False
            print("🔒 Browser geschlossen")


def test_calculator():
    """Test der Kalkulation."""
    # Credentials laden
    credentials_path = '/opt/greiner-portal/config/credentials.json'
    
    if os.path.exists(credentials_path):
        with open(credentials_path) as f:
            creds = json.load(f)
        leasys_creds = creds.get('external_systems', {}).get('leasys', {})
    else:
        print("❌ credentials.json nicht gefunden!")
        return
    
    calc = LeasysCalculator(
        username=leasys_creds['username'],
        password=leasys_creds['password'],
        headless=False  # False für Debug, True für Produktion
    )
    
    try:
        # Test: Login und Screenshot
        if calc.login():
            calc.screenshot("/tmp/leasys_after_login.png")
            
            # Warte und schaue was auf der Seite ist
            time.sleep(3)
            print("\n📄 Aktuelle URL:", calc.driver.current_url)
            print("📄 Seitentitel:", calc.driver.title)
            
            # Suche nach Navigation/Menü-Elementen
            print("\n🔍 Suche Menü-Elemente...")
            try:
                menu_items = calc.driver.find_elements(By.XPATH, "//nav//a | //mat-nav-list//a | //*[contains(@class, 'menu')]//a")
                for item in menu_items[:10]:
                    print(f"   • {item.text}")
            except:
                pass
            
            calc.screenshot("/tmp/leasys_menu.png")
            
    finally:
        input("\n⏸️ Enter zum Beenden drücken...")
        calc.close()


if __name__ == "__main__":
    test_calculator()
