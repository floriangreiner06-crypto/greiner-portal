#!/usr/bin/env python3
"""
Schäferbarthold Scraper V2 - Strukturierte Preisabfrage
"""

import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
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
        return webdriver.Chrome(options=chrome_options)
    
    def login(self):
        """Login bei Schäferbarthold"""
        if self.logged_in and self.driver:
            return True
            
        self.driver = self._get_driver()
        self.driver.get(BASE_URL)
        time.sleep(3)
        
        if 'auth' in self.driver.current_url:
            username = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username.send_keys(KUNDENNUMMER)
            
            password = self.driver.find_element(By.ID, "password")
            password.send_keys(PASSWORT)
            
            self.driver.find_element(By.ID, "kc-login").click()
            time.sleep(5)
        
        self.logged_in = 'b2b.schaeferbarthold.com' in self.driver.current_url
        return self.logged_in
    
    def search(self, teilenummer):
        """
        Suche Teilenummer und extrahiere alle Preise
        Returns: Liste von Ergebnissen mit Preis, Hersteller, Bezeichnung
        """
        if not self.logged_in:
            self.login()
        
        # Zur Startseite
        self.driver.get(BASE_URL)
        time.sleep(2)
        
        try:
            # Suchfeld finden
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.MuiInputBase-input"))
            )
            
            search_input.clear()
            search_input.send_keys(teilenummer)
            time.sleep(0.5)
            search_input.send_keys(Keys.RETURN)
            
            # Warten auf Ergebnisse
            time.sleep(4)
            
            # HTML parsen
            html = self.driver.page_source
            
            # Ergebnisse extrahieren
            results = self._parse_results(html, teilenummer)
            
            return {
                'success': True,
                'teilenummer': teilenummer,
                'anzahl': len(results),
                'ergebnisse': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'teilenummer': teilenummer,
                'error': str(e)
            }
    
    def _parse_results(self, html, teilenummer):
        """Parse Suchergebnisse aus HTML"""
        results = []
        
        # Muster für Artikel-Karten mit Preis
        # Format: "HERSTELLER - TEILENUMMER" ... "PREIS €"
        
        # Finde alle Preis-Elemente
        price_pattern = r'([\d]+[,.][\d]{2})\s*[€&nbsp;]'
        prices = re.findall(price_pattern, html)
        
        # Finde Hersteller-Teilenummer Kombinationen
        # Beispiel: "MOPAR PARTS - 16 926 472 80" oder "OPEL - 11588731"
        part_pattern = r'aria-label="([A-ZÄÖÜ\s/]+)\s*-\s*([^"]+)"'
        parts = re.findall(part_pattern, html)
        
        # Finde Produktbeschreibungen
        desc_pattern = r'aria-label="([^"]+)"[^>]*>[^<]*</p><p[^>]*class="[^"]*css-b2qvhm[^"]*"[^>]*>([^<]+)</p>'
        
        # Kombiniere Informationen
        seen_parts = set()
        
        for hersteller, teil_nr in parts:
            teil_nr = teil_nr.strip()
            hersteller = hersteller.strip()
            
            # Duplikate vermeiden
            key = f"{hersteller}-{teil_nr}"
            if key in seen_parts:
                continue
            seen_parts.add(key)
            
            # Prüfen ob es zu unserer Suche passt
            teil_clean = teil_nr.replace(' ', '').replace('-', '')
            such_clean = teilenummer.replace(' ', '').replace('-', '')
            
            if such_clean in teil_clean or teil_clean in such_clean:
                # Preis für dieses Teil finden (vereinfacht: erster noch nicht verwendeter Preis)
                preis = None
                if prices:
                    preis = prices.pop(0) if prices else None
                
                results.append({
                    'hersteller': hersteller,
                    'teilenummer': teil_nr,
                    'preis': float(preis.replace(',', '.')) if preis else None,
                    'waehrung': 'EUR'
                })
        
        # Falls keine direkten Treffer, gib zumindest die gefundenen Preise zurück
        if not results and prices:
            for i, preis in enumerate(prices[:5]):
                results.append({
                    'hersteller': 'Unbekannt',
                    'teilenummer': teilenummer,
                    'preis': float(preis.replace(',', '.')),
                    'waehrung': 'EUR',
                    'note': f'Preis {i+1} aus Suchergebnis'
                })
        
        return results
    
    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logged_in = False


def main():
    """Test"""
    print("🔍 SCHÄFERBARTHOLD SCRAPER V2")
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
    
    print("\n✅ Test abgeschlossen!")


if __name__ == "__main__":
    main()
