#!/usr/bin/env python3
"""
DA (Digitales Autohaus) Explorer v2
Mit korrekten Selektoren für Vue.js/Vuetify
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
import json
from datetime import datetime

# Konfiguration
DA_URL = "https://werkstattplanung.net/greiner/deggendorf/kic/da/auth.html#/"
DA_USER = "florian.greiner@auto-greiner.de"
DA_PASS = "Hyundai2025!"

# Output in Sync-Verzeichnis
OUTPUT_DIR = "/mnt/greiner-portal-sync/DA_Screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    service = Service('/usr/local/bin/chromedriver')
    return webdriver.Chrome(service=service, options=options)

def explore_da():
    driver = setup_driver()
    wait = WebDriverWait(driver, 20)
    screenshots = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # 1. Login-Seite öffnen
        print("1. Öffne DA...")
        driver.get(DA_URL)
        
        # Warte auf Vue.js App geladen
        print("   Warte auf Vue.js App...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']")))
        time.sleep(2)  # Extra Zeit für Vuetify
        
        screenshot_path = f"{OUTPUT_DIR}/{timestamp}_01_login.png"
        driver.save_screenshot(screenshot_path)
        screenshots.append(screenshot_path)
        print(f"   ✓ Login-Seite geladen")
        
        # 2. Login-Formular ausfüllen
        print("\n2. Fülle Login aus...")
        
        # Username
        user_field = driver.find_element(By.CSS_SELECTOR, "input[name='username']")
        user_field.clear()
        user_field.send_keys(DA_USER)
        print(f"   ✓ User: {DA_USER}")
        
        # Password
        pass_field = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        pass_field.clear()
        pass_field.send_keys(DA_PASS)
        print("   ✓ Passwort eingegeben")
        
        screenshot_path = f"{OUTPUT_DIR}/{timestamp}_02_formular.png"
        driver.save_screenshot(screenshot_path)
        screenshots.append(screenshot_path)
        
        # 3. Login-Button klicken
        print("\n3. Klicke Anmelden...")
        login_btn = driver.find_element(By.CSS_SELECTOR, "button[data-testid='LoginView.login-button']")
        login_btn.click()
        
        # Warte auf Navigation (URL ändert sich nach Login)
        print("   Warte auf Dashboard...")
        time.sleep(5)
        
        # Prüfe ob Login erfolgreich
        current_url = driver.current_url
        print(f"   URL: {current_url}")
        
        screenshot_path = f"{OUTPUT_DIR}/{timestamp}_03_nach_login.png"
        driver.save_screenshot(screenshot_path)
        screenshots.append(screenshot_path)
        
        # HTML speichern
        with open(f"{OUTPUT_DIR}/{timestamp}_03_nach_login.html", 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        
        # 4. Wenn eingeloggt, Navigation erkunden
        if "auth" not in current_url.lower() or "#/" not in current_url:
            print("\n4. ✓ LOGIN ERFOLGREICH!")
            
            # Warte auf Dashboard vollständig geladen
            time.sleep(3)
            
            screenshot_path = f"{OUTPUT_DIR}/{timestamp}_04_dashboard.png"
            driver.save_screenshot(screenshot_path)
            screenshots.append(screenshot_path)
            
            # Navigation sammeln
            print("\n5. Sammle Navigation...")
            nav_items = []
            
            # Alle klickbaren Elemente
            links = driver.find_elements(By.TAG_NAME, "a")
            buttons = driver.find_elements(By.TAG_NAME, "button")
            
            # V-list-items (Vuetify Navigation)
            v_items = driver.find_elements(By.CSS_SELECTOR, ".v-list-item, .v-tab, .v-btn")
            
            for el in links + buttons + v_items:
                try:
                    text = el.text.strip()
                    href = el.get_attribute('href') or ''
                    if text and len(text) < 50:
                        nav_items.append({
                            'text': text,
                            'href': href,
                            'tag': el.tag_name
                        })
                except:
                    pass
            
            # Deduplizieren
            seen = set()
            unique_nav = []
            for item in nav_items:
                key = item['text']
                if key not in seen:
                    seen.add(key)
                    unique_nav.append(item)
            
            print(f"   Gefunden: {len(unique_nav)} Navigation-Elemente")
            for item in unique_nav[:30]:
                print(f"   - {item['text']}")
            
            # Speichern
            with open(f"{OUTPUT_DIR}/{timestamp}_navigation.json", 'w', encoding='utf-8') as f:
                json.dump(unique_nav, f, indent=2, ensure_ascii=False)
            
            # 6. Hauptbereiche erkunden
            print("\n6. Erkunde Hauptbereiche...")
            
            sections_to_find = [
                "Werkstatt", "Planung", "Kalender", "Termin",
                "Ersatzwagen", "Mobilität", "Mietwagen",
                "Auftrag", "Service", "Annahme",
                "Kunde", "Fahrzeug"
            ]
            
            for section in sections_to_find:
                for item in unique_nav:
                    if section.lower() in item['text'].lower():
                        print(f"\n   → Gefunden: {item['text']}")
                        try:
                            # Element finden und klicken
                            el = driver.find_element(By.XPATH, f"//*[contains(text(), '{item['text']}')]")
                            if el.is_displayed():
                                el.click()
                                time.sleep(3)
                                
                                safe_name = "".join(c if c.isalnum() else "_" for c in item['text'])[:20]
                                screenshot_path = f"{OUTPUT_DIR}/{timestamp}_section_{safe_name}.png"
                                driver.save_screenshot(screenshot_path)
                                screenshots.append(screenshot_path)
                                print(f"      ✓ Screenshot: {screenshot_path}")
                                
                                # HTML speichern
                                with open(f"{OUTPUT_DIR}/{timestamp}_section_{safe_name}.html", 'w', encoding='utf-8') as f:
                                    f.write(driver.page_source)
                                
                                # Zurück zum Dashboard
                                driver.back()
                                time.sleep(2)
                        except Exception as e:
                            print(f"      ✗ Fehler: {e}")
                        break
            
        else:
            print("\n4. ✗ LOGIN FEHLGESCHLAGEN - noch auf Login-Seite")
            
            # Prüfe auf Fehlermeldung
            try:
                error = driver.find_element(By.CSS_SELECTOR, ".v-alert, .error, .v-messages__message")
                print(f"   Fehlermeldung: {error.text}")
            except:
                pass
            
    except Exception as e:
        print(f"\nFEHLER: {e}")
        import traceback
        traceback.print_exc()
        
        # Screenshot bei Fehler
        driver.save_screenshot(f"{OUTPUT_DIR}/{timestamp}_error.png")
        
    finally:
        driver.quit()
    
    print(f"\n{'='*50}")
    print(f"FERTIG - {len(screenshots)} Screenshots")
    print(f"Verzeichnis: {OUTPUT_DIR}")
    print(f"{'='*50}")

if __name__ == "__main__":
    explore_da()
