#!/usr/bin/env python3
"""
Schäferbarthold Scraper V3 - Mit korrekten Selektoren
"""

import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys

KUNDENNUMMER = "1003941"
PASSWORT = "AO443494"
BASE_URL = "https://b2b.schaeferbarthold.com"

class SchaeferbartholdScraper:
    def __init__(self):
        self.driver = None
        self.logged_in = False
    
    def _get_driver(self):
        chrome_options = Options()
        chrome_options.binary_location = '/usr/bin/google-chrome'
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        # Expliziter ChromeDriver-Pfad (nicht im Gunicorn PATH)
        service = Service(executable_path='/usr/local/bin/chromedriver')
        return webdriver.Chrome(service=service, options=chrome_options)
    
    def login(self):
        if self.logged_in and self.driver:
            return True
            
        self.driver = self._get_driver()
        self.driver.get(BASE_URL)
        time.sleep(3)
        
        if 'auth' in self.driver.current_url:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys(KUNDENNUMMER)
            
            self.driver.find_element(By.ID, "password").send_keys(PASSWORT)
            self.driver.find_element(By.ID, "kc-login").click()
            time.sleep(5)
        
        self.logged_in = 'b2b.schaeferbarthold.com' in self.driver.current_url
        return self.logged_in
    
    def search(self, teilenummer):
        """Suche Teilenummer und extrahiere strukturierte Ergebnisse"""
        if not self.logged_in:
            self.login()
        
        self.driver.get(BASE_URL)
        time.sleep(2)
        
        try:
            # Suchfeld finden und Teilenummer eingeben
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.MuiInputBase-input"))
            )
            search_input.clear()
            search_input.send_keys(teilenummer)
            time.sleep(0.5)
            search_input.send_keys(Keys.RETURN)
            
            # Warten auf Suchergebnisse
            time.sleep(5)
            
            # HTML parsen
            html = self.driver.page_source
            
            # Anzahl Treffer extrahieren
            treffer_match = re.search(r"ergab (\d+) Treffer", html)
            anzahl = int(treffer_match.group(1)) if treffer_match else 0
            
            if anzahl == 0:
                return {
                    'success': True,
                    'teilenummer': teilenummer,
                    'anzahl': 0,
                    'ergebnisse': [],
                    'hinweis': 'Keine Treffer gefunden'
                }
            
            # Ergebnisse extrahieren
            ergebnisse = self._parse_results(html, teilenummer)
            
            return {
                'success': True,
                'teilenummer': teilenummer,
                'anzahl': len(ergebnisse),
                'ergebnisse': ergebnisse
            }
            
        except Exception as e:
            return {
                'success': False,
                'teilenummer': teilenummer,
                'error': str(e)
            }
    
    def _parse_results(self, html, teilenummer):
        """Parse strukturierte Ergebnisse aus HTML"""
        ergebnisse = []
        
        # Hersteller + Teilenummer finden
        # Format: "CITROËN / PEUGEOT - 9837096880"
        hersteller_pattern = r'([A-ZÄÖÜ][A-ZÄÖÜ\s/]+)\s*-\s*(' + re.escape(teilenummer) + r')'
        hersteller_match = re.search(hersteller_pattern, html, re.IGNORECASE)
        
        hersteller = hersteller_match.group(1).strip() if hersteller_match else 'Unbekannt'
        
        # Bruttopreis (UVP) finden
        # Format: "Bruttopreis: 111,28 €"
        brutto_pattern = r'Bruttopreis:\s*([\d,]+)\s*[€&]'
        brutto_match = re.search(brutto_pattern, html)
        brutto_preis = float(brutto_match.group(1).replace(',', '.')) if brutto_match else None
        
        # Einkaufspreis finden
        # Format: "Preis:</p><p ...>91,49 € / 1 Stück"
        ek_pattern = r'Preis:</p><p[^>]*>([\d,]+)\s*[€&]'
        ek_match = re.search(ek_pattern, html)
        ek_preis = float(ek_match.group(1).replace(',', '.')) if ek_match else None
        
        # Rabatt finden
        rabatt_pattern = r'productCard-pill-advantage[^>]*>([\d,\.]+)%'
        rabatt_match = re.search(rabatt_pattern, html)
        rabatt = float(rabatt_match.group(1).replace(',', '.')) if rabatt_match else None
        
        # Kategorie finden (z.B. "Ölwanne")
        kategorie_pattern = r'MuiChip-label[^>]*>([^<]+)</span>'
        kategorie_match = re.search(kategorie_pattern, html)
        kategorie = kategorie_match.group(1) if kategorie_match else None
        
        # Verfügbarkeit prüfen
        verfuegbar = 'Auf Lager' in html or 'verfügbar' in html.lower()
        
        ergebnisse.append({
            'hersteller': hersteller,
            'teilenummer': teilenummer,
            'kategorie': kategorie,
            'bruttopreis': brutto_preis,
            'einkaufspreis': ek_preis,
            'rabatt_prozent': rabatt,
            'verfuegbar': verfuegbar,
            'waehrung': 'EUR',
            'quelle': 'Schäferbarthold'
        })
        
        return ergebnisse
    
    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logged_in = False


def main():
    print("🔍 SCHÄFERBARTHOLD SCRAPER V3")
    print("=" * 70)
    
    scraper = SchaeferbartholdScraper()
    
    try:
        test_parts = ["9837096880", "1051610", "13507405"]
        
        for part in test_parts:
            print(f"\n📦 Suche: {part}")
            result = scraper.search(part)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
    finally:
        scraper.close()
    
    print("\n" + "=" * 70)
    print("✅ Test abgeschlossen!")


if __name__ == "__main__":
    main()
