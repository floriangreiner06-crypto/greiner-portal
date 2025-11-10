#!/usr/bin/env python3
"""
Hyundai Finance Portal - Test Scraper (Server Version)
Erstellt Screenshots vom Portal für Analyse
"""

import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class HyundaiFinanceTester:
    """Test-Scraper für Hyundai Finance Portal"""
    
    def __init__(self, username: str, password: str):
        self.url = "https://fiona.hyundaifinance.eu/#/dealer-portal"
        self.username = username
        self.password = password
        self.driver = None
        self.screenshot_dir = "/tmp/hyundai_screenshots"
        
        os.makedirs(self.screenshot_dir, exist_ok=True)
        print(f"📸 Screenshots: {self.screenshot_dir}")
    
    def setup_driver(self):
        """Chrome WebDriver initialisieren"""
        print("🔧 Initialisiere Chrome WebDriver...")
        
        chrome_options = Options()
        
        # Headless Mode für Server
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-setuid-sandbox')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome WebDriver erfolgreich initialisiert")
            return True
        except Exception as e:
            print(f"❌ Fehler: {e}")
            return False
    
    def take_screenshot(self, name: str):
        """Screenshot erstellen"""
        if not self.driver:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.png"
        filepath = os.path.join(self.screenshot_dir, filename)
        
        try:
            self.driver.save_screenshot(filepath)
            print(f"📸 Screenshot: {filename}")
            return filepath
        except Exception as e:
            print(f"❌ Screenshot fehlgeschlagen: {e}")
            return None
    
    def get_page_info(self):
        """Informationen über aktuelle Seite sammeln"""
        if not self.driver:
            return {}
        
        return {
            'url': self.driver.current_url,
            'title': self.driver.title,
            'html_length': len(self.driver.page_source)
        }
    
    def find_login_elements(self):
        """Login-Elemente auf der Seite finden"""
        print("\n🔍 Suche Login-Elemente...")
        
        username_selectors = [
            (By.ID, "username"),
            (By.ID, "email"),
            (By.NAME, "username"),
            (By.NAME, "email"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.CSS_SELECTOR, "input[type='email']"),
        ]
        
        password_selectors = [
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
        ]
        
        button_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Anmelden')]"),
            (By.XPATH, "//button[contains(text(), 'Login')]"),
            (By.XPATH, "//button[contains(text(), 'Sign')]"),
        ]
        
        found_elements = {
            'username': None,
            'password': None,
            'button': None
        }
        
        for selector_type, selector_value in username_selectors:
            try:
                element = self.driver.find_element(selector_type, selector_value)
                found_elements['username'] = (selector_type, selector_value)
                print(f"✅ Username: {selector_type}={selector_value}")
                break
            except NoSuchElementException:
                continue
        
        for selector_type, selector_value in password_selectors:
            try:
                element = self.driver.find_element(selector_type, selector_value)
                found_elements['password'] = (selector_type, selector_value)
                print(f"✅ Password: {selector_type}={selector_value}")
                break
            except NoSuchElementException:
                continue
        
        for selector_type, selector_value in button_selectors:
            try:
                element = self.driver.find_element(selector_type, selector_value)
                found_elements['button'] = (selector_type, selector_value)
                print(f"✅ Button: {selector_type}={selector_value}")
                break
            except NoSuchElementException:
                continue
        
        return found_elements
    
    def test_login_flow(self):
        """Teste den kompletten Login-Flow"""
        print("\n" + "="*60)
        print("🧪 TESTE HYUNDAI FINANCE PORTAL")
        print("="*60)
        
        if not self.setup_driver():
            return False
        
        try:
            # Schritt 1: Seite öffnen
            print(f"\n📍 SCHRITT 1: Öffne Portal...")
            self.driver.get(self.url)
            time.sleep(5)
            
            info = self.get_page_info()
            print(f"   URL: {info['url']}")
            print(f"   Title: {info['title']}")
            
            self.take_screenshot("01_initial_page")
            
            # Schritt 2: Login-Elemente finden
            print(f"\n📍 SCHRITT 2: Analysiere Login-Seite...")
            login_elements = self.find_login_elements()
            
            if not all(login_elements.values()):
                print("\n❌ Nicht alle Login-Elemente gefunden!")
                print("\n🔍 GEFUNDENE ELEMENTE:")
                for key, value in login_elements.items():
                    status = "✅" if value else "❌"
                    print(f"   {status} {key}: {value}")
                
                self.take_screenshot("02_login_elements_not_found")
                
                # Speichere HTML für Analyse
                html_path = os.path.join(self.screenshot_dir, "page_source.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print(f"\n💾 HTML gespeichert: {html_path}")
                
                return False
            
            # Schritt 3: Login durchführen
            print(f"\n📍 SCHRITT 3: Login durchführen...")
            
            try:
                username_field = self.driver.find_element(*login_elements['username'])
                username_field.clear()
                username_field.send_keys(self.username)
                print("   ✓ Username eingegeben")
                
                password_field = self.driver.find_element(*login_elements['password'])
                password_field.clear()
                password_field.send_keys(self.password)
                print("   ✓ Password eingegeben")
                
                self.take_screenshot("03_credentials_entered")
                
                login_button = self.driver.find_element(*login_elements['button'])
                login_button.click()
                print("   ✓ Login-Button geklickt")
                
                print("   ⏳ Warte auf Dashboard...")
                time.sleep(10)
                
                self.take_screenshot("04_after_login")
                
                info = self.get_page_info()
                print(f"\n   Nach Login:")
                print(f"   URL: {info['url']}")
                print(f"   Title: {info['title']}")
                
                if "login" in info['url'].lower():
                    print("\n⚠️  Immer noch auf Login-Seite!")
                    return False
                else:
                    print("\n✅ Login erfolgreich!")
                    
            except Exception as e:
                print(f"\n❌ Login fehlgeschlagen: {e}")
                self.take_screenshot("03_login_failed")
                return False
            
            # Schritt 4: Portal erkunden
            print(f"\n📍 SCHRITT 4: Portal erkunden...")
            time.sleep(5)
            
            try:
                nav_elements = self.driver.find_elements(By.CSS_SELECTOR, "nav a, .nav-link, .menu-item, [role='menuitem']")
                
                if nav_elements:
                    print(f"\n   ✅ {len(nav_elements)} Navigation-Links gefunden:")
                    for i, elem in enumerate(nav_elements[:10], 1):
                        try:
                            text = elem.text.strip()
                            if text:
                                print(f"      {i}. {text}")
                        except:
                            pass
                
                self.take_screenshot("05_dashboard_navigation")
                
            except Exception as e:
                print(f"   ⚠️  Navigation nicht gefunden: {e}")
            
            print("\n   🔍 Suche nach relevanten Bereichen...")
            keywords = ["Bestand", "Finanzierung", "Fahrzeug", "Vehicle", "Contract", "Export"]
            
            for keyword in keywords:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                    if elements:
                        print(f"      ✓ '{keyword}' gefunden ({len(elements)} mal)")
                except:
                    pass
            
            self.take_screenshot("06_final_dashboard")
            
            print("\n" + "="*60)
            print("✅ TEST ERFOLGREICH!")
            print("="*60)
            print(f"\n📸 Screenshots: {self.screenshot_dir}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ FEHLER: {e}")
            self.take_screenshot("error_exception")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()
                print("🔚 Browser geschlossen")


def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║     HYUNDAI FINANCE PORTAL - TEST SCRAPER                  ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    print("⚙️  KONFIGURATION:")
    print("   URL: https://fiona.hyundaifinance.eu/#/dealer-portal")
    print("   User: Christian.aichinger@auto-greiner.de")
    print("   Mode: Headless (Server)")
    
    username = "Christian.aichinger@auto-greiner.de"
    password = "Hyundaikona2020!"
    
    tester = HyundaiFinanceTester(username=username, password=password)
    success = tester.test_login_flow()
    
    if success:
        print("\n✅ Test abgeschlossen!")
        print(f"\n📂 Screenshots ansehen:")
        print(f"   cd /tmp/hyundai_screenshots")
        print(f"   ls -lh")
        return 0
    else:
        print("\n❌ Test fehlgeschlagen!")
        return 1


if __name__ == "__main__":
    exit(main())
