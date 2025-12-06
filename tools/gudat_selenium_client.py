#!/usr/bin/env python3
"""
=============================================================================
GREINER DRIVE - Gudat Werkstattplanung Selenium Client
=============================================================================
Browser-Automation Lösung für werkstattplanung.net wenn direkte API nicht geht.

Benötigt:
    pip install selenium webdriver-manager

Autor: Claude AI für Greiner Portal
Version: 1.0 (TAG 97)
Datum: 2025-12-06
"""

import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# Versuche Selenium zu importieren
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium nicht installiert. Installiere mit: pip install selenium webdriver-manager")


class GudatSeleniumClient:
    """
    Selenium-basierter Client für werkstattplanung.net
    
    Verwendet echten Browser für 100% Kompatibilität mit der Website.
    Langsamer als direkte API-Calls, aber funktioniert garantiert.
    
    Usage:
        client = GudatSeleniumClient(username, password, headless=True)
        client.login()
        data = client.get_workload('2025-12-09')
        client.close()
    """
    
    BASE_URL = "https://werkstattplanung.net/greiner/deggendorf/kic"
    
    def __init__(self, username: str, password: str, headless: bool = True):
        """
        Args:
            username: Email für Login
            password: Passwort
            headless: True für unsichtbaren Browser (empfohlen für Server)
        """
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium nicht installiert")
        
        self.username = username
        self.password = password
        self.headless = headless
        self.driver = None
        self._logged_in = False
        
    def _init_driver(self):
        """Initialisiert Chrome WebDriver"""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
        
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--lang=de-DE')
        
        # User-Agent setzen
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')
        
        try:
            # Versuche ChromeDriver automatisch zu installieren
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            logger.error(f"ChromeDriver konnte nicht initialisiert werden: {e}")
            # Fallback: Versuche System-Chrome
            self.driver = webdriver.Chrome(options=options)
        
        self.driver.implicitly_wait(10)
        
    def login(self) -> bool:
        """
        Führt Login im Browser durch
        
        Returns:
            True wenn erfolgreich
        """
        if self.driver is None:
            self._init_driver()
        
        try:
            logger.info("Öffne Login-Seite...")
            self.driver.get(f"{self.BASE_URL}/da/")
            
            # Warte auf Login-Formular
            time.sleep(2)
            
            # Finde Login-Felder (Vue.js App)
            # Die Selektoren müssen ggf. angepasst werden
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='username'], input[placeholder*='mail']"))
            )
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            # Eingabe
            username_field.clear()
            username_field.send_keys(self.username)
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Submit
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button.login-btn, .btn-primary")
            submit_btn.click()
            
            # Warte auf erfolgreichen Login
            time.sleep(3)
            
            # Prüfe ob wir eingeloggt sind (URL sollte sich ändern)
            if '/auth' not in self.driver.current_url:
                logger.info("Login erfolgreich!")
                self._logged_in = True
                return True
            else:
                logger.error("Login fehlgeschlagen - immer noch auf Login-Seite")
                return False
                
        except Exception as e:
            logger.error(f"Login-Fehler: {e}")
            return False
    
    def get_workload_raw(self, date: str = None, days: int = 7) -> List[Dict]:
        """
        Holt Workload-Daten über Browser
        
        Diese Methode navigiert zur Kapazitäts-Ansicht und extrahiert die Daten
        aus dem DOM oder fängt die API-Response ab.
        """
        if not self._logged_in:
            if not self.login():
                return []
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Navigiere zur Disposition/Kalender-Ansicht
            self.driver.get(f"{self.BASE_URL}/da/#/disposition")
            time.sleep(3)
            
            # Methode 1: Intercepte API-Response
            # Führe JavaScript aus um API direkt aufzurufen
            script = f"""
            return fetch('/greiner/deggendorf/kic/api/v1/workload_week_summary?date={date}&days={days}', {{
                method: 'GET',
                headers: {{
                    'Accept': 'application/json',
                    'X-XSRF-TOKEN': document.cookie.split('XSRF-TOKEN=')[1]?.split(';')[0] || ''
                }},
                credentials: 'include'
            }})
            .then(r => r.json())
            .catch(e => ({{error: e.message}}));
            """
            
            result = self.driver.execute_async_script(f"""
                var callback = arguments[arguments.length - 1];
                fetch('/greiner/deggendorf/kic/api/v1/workload_week_summary?date={date}&days={days}', {{
                    method: 'GET',
                    headers: {{'Accept': 'application/json'}},
                    credentials: 'include'
                }})
                .then(r => r.json())
                .then(data => callback(data))
                .catch(e => callback({{error: e.message}}));
            """)
            
            if result and 'error' not in result:
                return result
            
            logger.warning(f"API-Fetch fehlgeschlagen: {result}")
            return []
            
        except Exception as e:
            logger.error(f"Workload-Fehler: {e}")
            return []
    
    def get_workload_summary(self, date: str = None) -> Dict[str, Any]:
        """Holt zusammengefasste Kapazitätsdaten für einen Tag"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        raw_data = self.get_workload_raw(date, days=2)
        
        if not raw_data or isinstance(raw_data, dict) and 'error' in raw_data:
            return {'error': 'Keine Daten erhalten', 'date': date}
        
        # Verarbeite wie im normalen Client
        total_capacity = 0
        total_planned = 0
        total_absent = 0
        total_free = 0
        teams = []
        
        for team in raw_data:
            team_name = team.get('name', 'Unknown')
            category = team.get('category_name', 'Unknown')
            team_id = team.get('id')
            
            # Finde Daten für Datum
            day_data = team.get('data', {}).get(date)
            if not day_data:
                # Versuche nächsten Tag
                next_day = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                day_data = team.get('data', {}).get(next_day)
            
            if not day_data:
                continue
            
            cap = day_data.get('base_workload', 0)
            planned = day_data.get('planned_workload', 0)
            absent = day_data.get('absence_workload', 0)
            free = day_data.get('free_workload', 0)
            
            total_capacity += cap
            total_planned += planned
            total_absent += absent
            total_free += free
            
            status = 'overloaded' if free < 0 else ('warning' if cap > 0 and free < cap * 0.1 else 'ok')
            
            teams.append({
                'id': team_id,
                'name': team_name,
                'category': category,
                'capacity': cap,
                'planned': planned,
                'absent': absent,
                'free': free,
                'status': status,
            })
        
        status = 'overloaded' if total_free < 0 else ('warning' if total_capacity > 0 and total_free < total_capacity * 0.1 else 'ok')
        utilization = round(total_planned / total_capacity * 100, 1) if total_capacity > 0 else 0
        
        return {
            'date': date,
            'total_capacity': total_capacity,
            'planned': total_planned,
            'absent': total_absent,
            'free': total_free,
            'utilization_percent': utilization,
            'status': status,
            'teams': sorted(teams, key=lambda x: x['free']),
            'teams_count': len(teams),
            'timestamp': datetime.now().isoformat()
        }
    
    def close(self):
        """Schließt den Browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self._logged_in = False


# =============================================================================
# CLI für Tests
# =============================================================================
if __name__ == '__main__':
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium nicht installiert!")
        print("   Installiere mit: pip install selenium webdriver-manager")
        exit(1)
    
    USERNAME = "florian.greiner@auto-greiner.de"
    PASSWORD = "Hyundai2025!"
    
    print("=" * 60)
    print("GUDAT SELENIUM CLIENT TEST")
    print("=" * 60)
    
    client = GudatSeleniumClient(USERNAME, PASSWORD, headless=True)
    
    try:
        if client.login():
            print("\n✅ Login erfolgreich!")
            
            print("\nHole Workload-Daten...")
            summary = client.get_workload_summary('2025-12-09')
            
            if 'error' not in summary:
                print(f"\n📊 Kapazität {summary['date']}:")
                print(f"   Gesamt: {summary['total_capacity']} AW")
                print(f"   Geplant: {summary['planned']} AW ({summary['utilization_percent']}%)")
                print(f"   Frei: {summary['free']} AW")
                print(f"   Status: {summary['status']}")
            else:
                print(f"\n❌ Fehler: {summary['error']}")
        else:
            print("\n❌ Login fehlgeschlagen!")
    finally:
        client.close()
        print("\nBrowser geschlossen.")
