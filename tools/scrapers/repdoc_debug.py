#!/usr/bin/env python3
"""
RepDoc Debug - Analysiere Login-Seite HTML-Struktur
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://www2.repdoc.com/DE/Login#Start"

def analyze_login_page():
    """Lade Login-Seite und analysiere HTML-Struktur"""
    
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    service = Service(executable_path='/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print("=== Lade RepDoc Login-Seite ===")
        driver.get(BASE_URL)
        time.sleep(5)
        
        print(f"\nURL: {driver.current_url}")
        print(f"Titel: {driver.title}")
        
        # Speichere HTML für Analyse
        html = driver.page_source
        with open('/tmp/repdoc_login.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("\nHTML gespeichert in /tmp/repdoc_login.html")
        
        # Suche nach Input-Feldern
        print("\n=== Input-Felder ===")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for i, inp in enumerate(inputs):
            print(f"{i+1}. type={inp.get_attribute('type')}, name={inp.get_attribute('name')}, id={inp.get_attribute('id')}, placeholder={inp.get_attribute('placeholder')}")
        
        # Suche nach Buttons
        print("\n=== Buttons ===")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for i, btn in enumerate(buttons):
            print(f"{i+1}. type={btn.get_attribute('type')}, text={btn.text[:50]}, class={btn.get_attribute('class')}")
        
        # Suche nach Formularen
        print("\n=== Formulare ===")
        forms = driver.find_elements(By.TAG_NAME, "form")
        for i, form in enumerate(forms):
            print(f"{i+1}. action={form.get_attribute('action')}, method={form.get_attribute('method')}")
            form_inputs = form.find_elements(By.TAG_NAME, "input")
            for inp in form_inputs:
                print(f"   - input: type={inp.get_attribute('type')}, name={inp.get_attribute('name')}, id={inp.get_attribute('id')}")
        
        # Suche nach iframes (könnte Login in iframe sein)
        print("\n=== iframes ===")
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for i, iframe in enumerate(iframes):
            print(f"{i+1}. src={iframe.get_attribute('src')}, id={iframe.get_attribute('id')}")
        
        # Suche nach spezifischen Selektoren
        print("\n=== Spezifische Selektoren ===")
        selectors = [
            "input[name*='user']",
            "input[name*='pass']",
            "input[name*='login']",
            "input[type='text']",
            "input[type='password']",
            "input[id*='user']",
            "input[id*='pass']",
            "input[placeholder*='Benutzer']",
            "input[placeholder*='Passwort']",
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ {selector}: {len(elements)} Element(e) gefunden")
                    for el in elements:
                        print(f"   - name={el.get_attribute('name')}, id={el.get_attribute('id')}, visible={el.is_displayed()}")
            except:
                pass
        
        print("\n=== Seite vollständig geladen ===")
        print(f"Seitenlänge: {len(html)} Zeichen")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_login_page()
