#!/usr/bin/env python3
"""Dello/Automega Scraper V9 - Formular-Submit mit Singleton"""

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class DelloScraper:
    _instance = None
    _driver = None
    _logged_in = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.base_url = "https://www.automega.biz"
        self.username = "k026939"
        self.password = "automega"
        
    def _ensure_driver(self):
        if DelloScraper._driver is None:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            # Expliziter ChromeDriver-Pfad (nicht im Gunicorn PATH)
            service = Service(executable_path='/usr/local/bin/chromedriver')
            DelloScraper._driver = webdriver.Chrome(service=service, options=options)
            DelloScraper._driver.set_page_load_timeout(30)
            DelloScraper._logged_in = False
        return DelloScraper._driver
        
    def _do_login(self):
        driver = self._ensure_driver()
        try:
            driver.get(self.base_url)
            time.sleep(2)
            dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "logindropdown"))
            )
            dropdown.click()
            time.sleep(1)
            driver.find_element(By.NAME, "KDxLOGON").send_keys(self.username)
            driver.find_element(By.NAME, "KDxPASSWORD").send_keys(self.password)
            driver.find_element(By.CSS_SELECTOR, "button[name*='ACTIONxKDxLOGON']").click()
            time.sleep(2)
            
            if "Kundenkonto" in driver.page_source:
                DelloScraper._logged_in = True
                print("✅ Dello Login")
                try:
                    driver.find_element(By.CSS_SELECTOR, "button[data-dismiss='modal']").click()
                except:
                    pass
                time.sleep(1)
                return True
            return False
        except Exception as e:
            print(f"❌ Login-Fehler: {e}")
            return False
    
    def get_price(self, teilenummer):
        driver = self._ensure_driver()
        
        if not DelloScraper._logged_in:
            if not self._do_login():
                return {'success': False, 'error': 'Login fehlgeschlagen'}
        
        try:
            clean_nr = re.sub(r'[^a-zA-Z0-9]', '', teilenummer)
            query = f"*{clean_nr}*"
            
            # JavaScript Formular-Submit (funktioniert!)
            js_search = f"""
            var forms = document.querySelectorAll('form.search-form');
            var form = null;
            for(var i=0; i<forms.length; i++) {{
                if(forms[i].offsetParent !== null) {{ form = forms[i]; break; }}
            }}
            if(!form) form = forms[0];
            if(!form) return 'no-form';
            var si = form.querySelector('input[name="ARTSUCHExMATCHCODE"]');
            var sq = form.querySelector('input[name="USERxSOLRQUERY"]');
            var ss = form.querySelector('input[name="USERxSEARCH"]');
            if(si) si.value = '{teilenummer}';
            if(sq) sq.value = '{query}';
            if(ss) ss.value = '{teilenummer}';
            form.submit();
            return 'ok';
            """
            result = driver.execute_script(js_search)
            if result != 'ok':
                # Kein Formular - zurück zur Startseite
                driver.get(self.base_url)
                time.sleep(2)
                driver.execute_script(js_search)
            
            # Warte auf Ergebnisse
            time.sleep(4)
            for _ in range(6):
                rows = driver.find_elements(By.CSS_SELECTOR, ".articlelist tr[data-articlenr]")
                if len(rows) > 0:
                    break
                time.sleep(1)
            
            # Parse
            results = []
            rows = driver.find_elements(By.CSS_SELECTOR, ".articlelist tr[data-articlenr]")
            for row in rows:
                try:
                    artikel_nr = row.get_attribute("data-articlenr")
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 9:
                        bezeichnung = cells[3].text.strip()
                        upe = self._parse_price(cells[7].text)
                        ek = self._parse_price(cells[8].text)
                        if upe or ek:
                            results.append({'artikel_nr': artikel_nr, 'bezeichnung': bezeichnung, 'upe': upe, 'ek': ek, 'quelle': 'dello'})
                except:
                    pass
            
            return {'success': True, 'teilenummer': teilenummer, 'ergebnisse': results, 'anzahl': len(results)}
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            DelloScraper._logged_in = False
            return {'success': False, 'error': str(e)}
    
    def _parse_price(self, text):
        if not text: return None
        try:
            clean = re.sub(r'[^\d,.]', '', text).replace(',', '.')
            return float(clean) if clean else None
        except:
            return None
        
    def close(self):
        pass
    
    @classmethod
    def force_close(cls):
        if cls._driver:
            cls._driver.quit()
            cls._driver = None
            cls._logged_in = False

if __name__ == "__main__":
    scraper = DelloScraper()
    
    print("=== 1. Aufruf (Login) ===")
    start = time.time()
    result = scraper.get_price("1109AL")
    print(f"Zeit: {time.time()-start:.1f}s, Treffer: {result.get('anzahl', 0)}")
    for r in result.get('ergebnisse', [])[:3]:
        print(f"  {r['artikel_nr']}: EK={r['ek']}€")
    
    print("\n=== 2. Aufruf (schnell) ===")
    start = time.time()
    result = scraper.get_price("650401")
    print(f"Zeit: {time.time()-start:.1f}s, Treffer: {result.get('anzahl', 0)}")
    
    print("\n=== 3. Aufruf ===")
    start = time.time()
    result = scraper.get_price("93165554")
    print(f"Zeit: {time.time()-start:.1f}s, Treffer: {result.get('anzahl', 0)}")
    
    DelloScraper.force_close()
