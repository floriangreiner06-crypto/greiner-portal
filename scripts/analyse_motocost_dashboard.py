"""
Motocost Dashboard Analyse
Analysiert das motocost.com Dashboard für auto1.com Angebote

TAG: 212
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import json
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class MotocostAnalyzer:
    """Analysiert das motocost Dashboard"""
    
    BASE_URL = "https://dashboard.motocost.com"
    LOGIN_URL = f"{BASE_URL}/login"
    
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.session.verify = False  # SSL-Warnungen ignorieren
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
        })
        self._logged_in = False
        self.analysis_results = {
            'login_success': False,
            'dashboard_urls': [],
            'api_endpoints': [],
            'data_structure': {},
            'available_features': [],
            'errors': []
        }
    
    def login(self):
        """Login zu motocost Dashboard"""
        try:
            print(f"[*] Lade Login-Seite: {self.LOGIN_URL}")
            resp = self.session.get(self.LOGIN_URL, timeout=30)
            
            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}: {resp.reason}")
            
            print(f"[*] Login-Seite geladen ({len(resp.text)} Zeichen)")
            
            # Prüfe ob es Grafana ist
            if 'grafana' in resp.text.lower() or 'Grafana' in resp.text:
                print("[!] Erkannt: Grafana-Dashboard")
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Debug: HTML-Struktur analysieren
                print("[*] Analysiere Login-Formular...")
                forms = soup.find_all('form')
                print(f"  [*] {len(forms)} Formulare gefunden")
                
                # Suche nach Input-Feldern
                inputs = soup.find_all('input')
                print(f"  [*] {len(inputs)} Input-Felder gefunden")
                for inp in inputs:
                    inp_type = inp.get('type', 'text')
                    inp_name = inp.get('name', '')
                    inp_id = inp.get('id', '')
                    print(f"    - {inp_type}: name='{inp_name}' id='{inp_id}'")
                
                # Grafana Login-Felder (verschiedene Varianten probieren)
                login_data = {}
                
                # Variante 1: Standard Grafana
                user_input = soup.find('input', {'name': 'user'}) or soup.find('input', {'id': re.compile('user', re.I)})
                password_input = soup.find('input', {'type': 'password'})
                
                if user_input:
                    login_data[user_input.get('name', 'user')] = self.email
                else:
                    # Fallback: Suche nach Email-Feld
                    email_input = soup.find('input', {'type': 'email'}) or soup.find('input', {'name': re.compile('email|mail|login', re.I)})
                    if email_input:
                        login_data[email_input.get('name', 'email')] = self.email
                    else:
                        login_data['user'] = self.email
                
                if password_input:
                    login_data[password_input.get('name', 'password')] = self.password
                else:
                    login_data['password'] = self.password
                
                # CSRF-Token suchen (falls vorhanden)
                csrf_token = soup.find('input', {'name': 'csrf_token'}) or soup.find('input', {'name': re.compile('csrf', re.I)})
                if csrf_token:
                    token_value = csrf_token.get('value', '')
                    login_data[csrf_token.get('name', 'csrf_token')] = token_value
                    print(f"  [*] CSRF-Token gefunden: {token_value[:20]}...")
                
                # Weitere Hidden-Felder
                for hidden in soup.find_all('input', {'type': 'hidden'}):
                    name = hidden.get('name')
                    value = hidden.get('value', '')
                    if name and name not in login_data:
                        login_data[name] = value
                        print(f"  [*] Hidden-Feld: {name} = {value[:50]}")
                
                print(f"[*] Login-Daten: {list(login_data.keys())}")
                
                # Login durchführen
                login_post_url = f"{self.BASE_URL}/login"
                print(f"[*] Führe Login durch: {login_post_url}")
                print(f"[*] POST-Daten: {dict((k, '***' if 'password' in k.lower() else v) for k, v in login_data.items())}")
                
                resp = self.session.post(login_post_url, data=login_data, allow_redirects=True, timeout=30)
                
                # Prüfe ob Login erfolgreich
                if resp.status_code == 200 and ('dashboard' in resp.url.lower() or 'home' in resp.url.lower()):
                    print("[+] Login erfolgreich!")
                    self._logged_in = True
                    self.analysis_results['login_success'] = True
                    return True
                elif 'login' in resp.url.lower():
                    print("[!] Login-Seite noch sichtbar - möglicherweise fehlgeschlagen")
                    # Prüfe auf Fehlermeldungen
                    if 'error' in resp.text.lower() or 'invalid' in resp.text.lower():
                        print("[!] Fehlermeldung erkannt")
                        # Fehlermeldung extrahieren
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        error_msg = soup.find('div', class_=re.compile('error|alert|warning', re.I))
                        if error_msg:
                            print(f"[!] Fehler: {error_msg.get_text(strip=True)}")
                    return False
                else:
                    print(f"[+] Weiterleitung nach Login: {resp.url}")
                    self._logged_in = True
                    self.analysis_results['login_success'] = True
                    return True
            else:
                # Standard HTML-Formular
                soup = BeautifulSoup(resp.text, 'html.parser')
                form = soup.find('form')
                
                if not form:
                    print("[!] Kein Login-Formular gefunden")
                    print(f"[!] Response-Text (erste 500 Zeichen):\n{resp.text[:500]}")
                    return False
                
                # Login-Daten sammeln
                login_data = {}
                for field in form.find_all(['input', 'select']):
                    name = field.get('name')
                    if not name:
                        continue
                    
                    if field.get('type') == 'email' or 'email' in name.lower():
                        login_data[name] = self.email
                    elif field.get('type') == 'password':
                        login_data[name] = self.password
                    elif field.get('type') == 'hidden':
                        login_data[name] = field.get('value', '')
                    elif field.get('type') == 'checkbox' and field.get('checked'):
                        login_data[name] = field.get('value', '1')
                
                # Login durchführen
                login_url = urljoin(self.BASE_URL, form.get('action', '/login'))
                print(f"[*] Führe Login durch: {login_url}")
                resp = self.session.post(login_url, data=login_data, allow_redirects=True)
                
                if resp.status_code == 200 and 'login' not in resp.url.lower():
                    print("[+] Login erfolgreich!")
                    self._logged_in = True
                    self.analysis_results['login_success'] = True
                    return True
                else:
                    print(f"[!] Login möglicherweise fehlgeschlagen: {resp.url}")
                    return False
                    
        except Exception as e:
            print(f"[!] Login-Fehler: {str(e)}")
            self.analysis_results['errors'].append(f"Login: {str(e)}")
            return False
    
    def analyze_dashboard(self):
        """Analysiert das Dashboard nach Login"""
        if not self._logged_in:
            print("[!] Nicht eingeloggt - versuche Login...")
            if not self.login():
                print("[!] Login fehlgeschlagen - kann Dashboard nicht analysieren")
                return
        
        try:
            # Haupt-Dashboard laden
            dashboard_urls = [
                f"{self.BASE_URL}/",
                f"{self.BASE_URL}/dashboard",
                f"{self.BASE_URL}/home",
            ]
            
            for url in dashboard_urls:
                try:
                    print(f"\n[*] Analysiere: {url}")
                    resp = self.session.get(url, timeout=30)
                    
                    if resp.status_code == 200:
                        print(f"[+] Seite geladen ({len(resp.text)} Zeichen)")
                        self.analysis_results['dashboard_urls'].append({
                            'url': url,
                            'status': resp.status_code,
                            'size': len(resp.text),
                            'content_type': resp.headers.get('Content-Type', '')
                        })
                        
                        # Analysiere Inhalt
                        self._analyze_content(resp.text, url)
                        
                        # Suche nach API-Endpoints
                        self._find_api_endpoints(resp.text)
                        
                        # Suche nach Datenstrukturen
                        self._find_data_structures(resp.text)
                        
                except Exception as e:
                    print(f"[!] Fehler bei {url}: {str(e)}")
                    self.analysis_results['errors'].append(f"{url}: {str(e)}")
            
            # Suche nach Grafana-spezifischen Endpoints
            if 'grafana' in str(self.analysis_results).lower():
                self._analyze_grafana_apis()
                
        except Exception as e:
            print(f"[!] Analyse-Fehler: {str(e)}")
            self.analysis_results['errors'].append(f"Analyse: {str(e)}")
    
    def _analyze_content(self, html, url):
        """Analysiert HTML-Inhalt"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Titel
        title = soup.find('title')
        if title:
            print(f"  Titel: {title.get_text(strip=True)}")
        
        # Grafana-spezifisch
        if 'grafana' in html.lower():
            print("  [*] Grafana-Dashboard erkannt")
            # Suche nach Dashboard-Links
            dashboard_links = soup.find_all('a', href=re.compile('/d/'))
            if dashboard_links:
                print(f"  [*] {len(dashboard_links)} Dashboard-Links gefunden")
                for link in dashboard_links[:5]:  # Erste 5
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    print(f"    - {text}: {href}")
        
        # Suche nach Tabellen (Daten)
        tables = soup.find_all('table')
        if tables:
            print(f"  [*] {len(tables)} Tabellen gefunden")
            for i, table in enumerate(tables[:3]):  # Erste 3
                rows = table.find_all('tr')
                print(f"    Tabelle {i+1}: {len(rows)} Zeilen")
        
        # Suche nach JSON-Daten im HTML
        json_scripts = soup.find_all('script', type='application/json')
        if json_scripts:
            print(f"  [*] {len(json_scripts)} JSON-Script-Tags gefunden")
            for i, script in enumerate(json_scripts[:3]):
                try:
                    data = json.loads(script.string)
                    print(f"    JSON {i+1}: {list(data.keys())[:5]}...")
                except:
                    pass
    
    def _find_api_endpoints(self, html):
        """Findet API-Endpoints im HTML/JavaScript"""
        # Suche nach API-URLs
        api_patterns = [
            r'["\']([^"\']*api[^"\']*)["\']',
            r'["\']([^"\']*\/api\/[^"\']*)["\']',
            r'url:\s*["\']([^"\']*)["\']',
            r'fetch\(["\']([^"\']*)["\']',
            r'axios\.(get|post)\(["\']([^"\']*)["\']',
        ]
        
        found_endpoints = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[-1]  # Letztes Element bei Gruppen
                if match and ('api' in match.lower() or match.startswith('/')):
                    found_endpoints.add(match)
        
        if found_endpoints:
            print(f"  [*] {len(found_endpoints)} potenzielle API-Endpoints gefunden")
            for endpoint in list(found_endpoints)[:10]:  # Erste 10
                print(f"    - {endpoint}")
                self.analysis_results['api_endpoints'].append(endpoint)
    
    def _find_data_structures(self, html):
        """Findet Datenstrukturen im HTML"""
        # Suche nach JSON-Daten
        json_matches = re.findall(r'\{[^{}]*"data"[^{}]*\}', html, re.DOTALL)
        if json_matches:
            print(f"  [*] {len(json_matches)} JSON-Datenstrukturen gefunden")
    
    def _analyze_grafana_apis(self):
        """Analysiert Grafana-spezifische APIs"""
        print("\n[*] Analysiere Grafana APIs...")
        
        grafana_endpoints = [
            '/api/dashboards/home',
            '/api/dashboards/db/home',
            '/api/search',
            '/api/datasources',
            '/api/dashboard/uid/home',
        ]
        
        for endpoint in grafana_endpoints:
            try:
                url = f"{self.BASE_URL}{endpoint}"
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    print(f"  [+] {endpoint}: OK")
                    try:
                        data = resp.json()
                        print(f"    Keys: {list(data.keys())[:5]}")
                    except:
                        pass
                else:
                    print(f"  [-] {endpoint}: {resp.status_code}")
            except Exception as e:
                print(f"  [!] {endpoint}: {str(e)}")
    
    def save_analysis(self, filename='motocost_analysis.json'):
        """Speichert Analyse-Ergebnisse"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.BASE_URL,
            'analysis': self.analysis_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n[+] Analyse gespeichert: {filename}")
        return filename
    
    def print_summary(self):
        """Gibt Zusammenfassung aus"""
        print("\n" + "="*60)
        print("ANALYSE-ZUSAMMENFASSUNG")
        print("="*60)
        print(f"Login erfolgreich: {self.analysis_results['login_success']}")
        print(f"Dashboard-URLs gefunden: {len(self.analysis_results['dashboard_urls'])}")
        print(f"API-Endpoints gefunden: {len(self.analysis_results['api_endpoints'])}")
        print(f"Fehler: {len(self.analysis_results['errors'])}")
        
        if self.analysis_results['api_endpoints']:
            print("\nAPI-Endpoints:")
            for endpoint in self.analysis_results['api_endpoints'][:10]:
                print(f"  - {endpoint}")
        
        if self.analysis_results['errors']:
            print("\nFehler:")
            for error in self.analysis_results['errors']:
                print(f"  - {error}")


def main():
    """Hauptfunktion"""
    print("="*60)
    print("MOTOCOST DASHBOARD ANALYSE")
    print("="*60)
    print()
    
    # Login-Daten
    email = "Florian.greiner@auto-greiner.de"
    password = "fdg547fdgEE"
    
    analyzer = MotocostAnalyzer(email, password)
    
    # Login
    if analyzer.login():
        # Dashboard analysieren
        analyzer.analyze_dashboard()
        
        # Zusammenfassung
        analyzer.print_summary()
        
        # Speichern
        analyzer.save_analysis('docs/motocost_analysis.json')
    else:
        print("\n[!] Login fehlgeschlagen - Analyse nicht möglich")
        analyzer.save_analysis('docs/motocost_analysis_failed.json')


if __name__ == '__main__':
    main()
