#!/usr/bin/env python3
"""
Mobis EDMOS Selenium-basierte API-Analyse
==========================================
Verwendet Selenium mit Chrome DevTools Protocol, um Network-Requests zu erfassen.
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

BASE_URL = 'https://edos.mobiseurope.com'
LOGIN_URL = f'{BASE_URL}/EDMOSN/gen/index.jsp'
USERNAME = 'G2403Koe'
PASSWORD = 'Greiner3!'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MobisSeleniumAnalyzer:
    def __init__(self):
        self.driver = None
        self.network_requests = []
        self.api_endpoints = []
        self.teilebezug_endpoints = []
        
    def setup_driver(self):
        """Erstellt Chrome-Driver mit Network-Logging."""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Enable Performance Logging für Network-Requests
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        chrome_options.set_capability('goog:chromeOptions', {
            'perfLoggingPrefs': {
                'enableNetwork': True,
                'enablePage': True
            },
            'args': ['--enable-logging', '--v=1']
        })
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome Driver erstellt")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Chrome Drivers: {str(e)}")
            return False
    
    def capture_network_requests(self):
        """Erfasst alle Network-Requests."""
        try:
            logs = self.driver.get_log('performance')
            logger.info(f"Erfasse {len(logs)} Performance-Logs...")
            
            for log in logs:
                try:
                    message = json.loads(log['message'])
                    message_type = message.get('message', {}).get('method', '')
                    
                    if message_type in ['Network.requestWillBeSent', 'Network.responseReceived']:
                        params = message.get('message', {}).get('params', {})
                        request = params.get('request', {})
                        response = params.get('response', {})
                        
                        url = request.get('url') or response.get('url', '')
                        method = request.get('method', 'GET')
                        
                        if url:
                            request_data = {
                                'url': url,
                                'method': method,
                                'timestamp': log.get('timestamp', 0),
                                'type': message_type,
                                'headers': request.get('headers', {}),
                                'postData': request.get('postData', ''),
                                'status': response.get('status', 0),
                                'mimeType': response.get('mimeType', '')
                            }
                            
                            # Prüfe ob bereits vorhanden
                            if url not in [r['url'] for r in self.network_requests]:
                                self.network_requests.append(request_data)
                            
                            # Filtere API-Endpunkte
                            if any(keyword in url.lower() for keyword in ['.do', '/api/', '/ajax/', 'transaction']):
                                if url not in [ep['url'] for ep in self.api_endpoints]:
                                    self.api_endpoints.append(request_data)
                                    logger.info(f"API-Endpunkt gefunden: {method} {url}")
                            
                            # Filtere Teilebezug-relevante Endpunkte
                            teile_keywords = ['teil', 'part', 'bestell', 'order', 'liefer', 'deliver', 'lager', 'stock', 'spare']
                            if any(keyword in url.lower() for keyword in teile_keywords):
                                if url not in [ep['url'] for ep in self.teilebezug_endpoints]:
                                    self.teilebezug_endpoints.append(request_data)
                                    logger.info(f"✅ Teilebezug-Endpunkt gefunden: {method} {url}")
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.warning(f"Fehler beim Erfassen von Network-Requests: {str(e)}")
        
        # Zusätzlich: Erfasse auch über JavaScript (XHR/Fetch)
        try:
            xhr_script = """
            // Erfasse alle XHR/Fetch-Requests über Performance API
            var entries = performance.getEntriesByType('resource');
            var requests = [];
            for (var i = 0; i < entries.length; i++) {
                var entry = entries[i];
                if (entry.name.includes('.do') || entry.name.includes('/api/') || entry.name.includes('transaction')) {
                    requests.push({
                        url: entry.name,
                        method: entry.initiatorType || 'unknown',
                        duration: entry.duration
                    });
                }
            }
            return requests;
            """
            xhr_requests = self.driver.execute_script(xhr_script)
            if xhr_requests:
                logger.info(f"Performance API: {len(xhr_requests)} Requests gefunden")
                for req in xhr_requests:
                    url = req.get('url', '')
                    if url and url not in [r['url'] for r in self.network_requests]:
                        self.network_requests.append({
                            'url': url,
                            'method': req.get('method', 'GET'),
                            'timestamp': 0,
                            'type': 'PerformanceAPI',
                            'headers': {},
                            'postData': '',
                            'status': 0,
                            'mimeType': ''
                        })
        except:
            pass
    
    def login(self):
        """Führt Login durch."""
        logger.info("Starte Login-Prozess...")
        
        try:
            # Öffne Login-Seite
            self.driver.get(LOGIN_URL)
            
            # Warte auf Seite-Laden (Nexacro braucht Zeit)
            logger.info("Warte auf Seite-Laden...")
            time.sleep(10)  # Länger warten für Nexacro
            
            # Erfasse initiale Requests
            self.capture_network_requests()
            
            # Mache Screenshot für Debugging
            try:
                self.driver.save_screenshot('/tmp/mobis_login_page.png')
                logger.info("Screenshot gespeichert: /tmp/mobis_login_page.png")
            except:
                pass
            
            # Suche nach Login-Feldern mit JavaScript (Nexacro verwendet Canvas/JavaScript)
            logger.info("Suche nach Login-Feldern mit JavaScript...")
            
            # Versuche alle Input-Felder zu finden
            find_inputs_script = """
            var inputs = document.querySelectorAll('input');
            var result = [];
            for (var i = 0; i < inputs.length; i++) {
                result.push({
                    type: inputs[i].type,
                    name: inputs[i].name,
                    id: inputs[i].id,
                    className: inputs[i].className,
                    placeholder: inputs[i].placeholder
                });
            }
            return result;
            """
            
            inputs = self.driver.execute_script(find_inputs_script)
            logger.info(f"Gefundene Input-Felder: {len(inputs)}")
            for inp in inputs:
                logger.info(f"  - {inp}")
            
            # Versuche Login mit JavaScript (direkt in Felder eingeben)
            login_script = f"""
            var inputs = document.querySelectorAll('input');
            var usernameSet = false;
            var passwordSet = false;
            
            for (var i = 0; i < inputs.length; i++) {{
                var inp = inputs[i];
                if (inp.type === 'text' || inp.type === 'email' || 
                    (inp.name && inp.name.toLowerCase().includes('user')) ||
                    (inp.id && inp.id.toLowerCase().includes('user'))) {{
                    inp.value = '{USERNAME}';
                    inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    usernameSet = true;
                    console.log('Username gesetzt in:', inp.name || inp.id);
                }}
                if (inp.type === 'password') {{
                    inp.value = '{PASSWORD}';
                    inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    passwordSet = true;
                    console.log('Password gesetzt in:', inp.name || inp.id);
                }}
            }}
            
            return {{usernameSet: usernameSet, passwordSet: passwordSet}};
            """
            
            result = self.driver.execute_script(login_script)
            logger.info(f"Login-Felder gesetzt: {result}")
            
            if not result['usernameSet'] or not result['passwordSet']:
                logger.warning("Konnte Login-Felder nicht finden, versuche alternative Methode...")
                # Versuche POST direkt
                return self.login_via_post()
            
            # Suche nach Submit-Button oder Form
            submit_script = """
            // Versuche Form zu finden und zu submitten
            var forms = document.querySelectorAll('form');
            if (forms.length > 0) {
                forms[0].submit();
                return true;
            }
            
            // Versuche Button zu finden
            var buttons = document.querySelectorAll('button, input[type="submit"]');
            for (var i = 0; i < buttons.length; i++) {
                var btn = buttons[i];
                if (btn.textContent.toLowerCase().includes('login') || 
                    btn.textContent.toLowerCase().includes('anmelden') ||
                    btn.type === 'submit') {
                    btn.click();
                    return true;
                }
            }
            
            // Versuche Enter-Taste zu simulieren
            var passwordField = document.querySelector('input[type="password"]');
            if (passwordField) {
                var event = new KeyboardEvent('keydown', {
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true
                });
                passwordField.dispatchEvent(event);
                return true;
            }
            
            return false;
            """
            
            submitted = self.driver.execute_script(submit_script)
            logger.info(f"Submit ausgeführt: {submitted}")
            
            # Warte auf Navigation/Response
            logger.info("Warte auf Login-Response...")
            time.sleep(10)  # Länger warten für Nexacro
            
            # Erfasse Requests nach Login
            self.capture_network_requests()
            
            # Prüfe ob Login erfolgreich
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            logger.info(f"Aktuelle URL: {current_url}")
            logger.info(f"Page Source Länge: {len(page_source)}")
            
            if 'error' not in page_source and 'fehler' not in page_source:
                logger.info(f"Login möglicherweise erfolgreich. URL: {current_url}")
                return True
            else:
                logger.warning("Login möglicherweise fehlgeschlagen")
                return False
                
        except Exception as e:
            logger.error(f"Fehler beim Login: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def login_via_post(self):
        """Alternative Login-Methode: Direkter POST-Request."""
        logger.info("Versuche Login via POST-Request...")
        
        try:
            # Hole Session-Cookie
            self.driver.get(LOGIN_URL)
            time.sleep(5)
            
            # Mache POST-Request mit Selenium (via JavaScript)
            post_script = f"""
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '{BASE_URL}/EDMOSN/gen/login.do', false);
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
            xhr.send('userid={USERNAME}&password={PASSWORD}');
            return {{
                status: xhr.status,
                responseText: xhr.responseText.substring(0, 500),
                responseURL: xhr.responseURL
            }};
            """
            
            result = self.driver.execute_script(post_script)
            logger.info(f"POST-Response: Status {result.get('status')}")
            
            if result.get('status') == 200:
                # Lade Seite neu
                self.driver.get(LOGIN_URL)
                time.sleep(5)
                return True
            
            return False
        except Exception as e:
            logger.error(f"Fehler bei POST-Login: {str(e)}")
            return False
    
    def search_parts_functionality(self):
        """Sucht nach Teilebezug-Funktionalität."""
        logger.info("Suche nach Teilebezug-Funktionalität...")
        
        try:
            # Warte bis Seite geladen ist
            time.sleep(5)
            
            # Suche nach Teilebezug in Nexacro-Menü
            logger.info("Suche nach Menü-Elementen...")
            
            # Versuche Menü zu finden und zu navigieren
            menu_script = """
            // Suche nach allen klickbaren Elementen mit Teilebezug-Text
            var allElements = document.querySelectorAll('*');
            var teileElements = [];
            var keywords = ['teil', 'part', 'bestell', 'order', 'liefer', 'deliver', 'lager', 'stock', 'spare'];
            
            for (var i = 0; i < allElements.length; i++) {
                var el = allElements[i];
                var text = (el.textContent || '').toLowerCase();
                var id = (el.id || '').toLowerCase();
                var className = (el.className || '').toLowerCase();
                
                // Prüfe ob Text Keywords enthält
                for (var j = 0; j < keywords.length; j++) {
                    if (text.includes(keywords[j]) && text.length < 100) {  // Nicht zu lange Texte
                        teileElements.push({
                            tag: el.tagName,
                            text: el.textContent.substring(0, 50),
                            id: el.id,
                            className: el.className,
                            element: el
                        });
                        break;
                    }
                }
            }
            
            return teileElements.slice(0, 20);  // Max 20
            """
            
            teile_elements = self.driver.execute_script(menu_script)
            logger.info(f"Gefundene Teilebezug-Elemente: {len(teile_elements)}")
            
            for elem in teile_elements[:5]:
                logger.info(f"  - {elem.get('text', '')[:50]} (ID: {elem.get('id', 'N/A')})")
            
            # Versuche auf Elemente zu klicken
            if teile_elements:
                logger.info("Versuche auf Teilebezug-Elemente zu klicken...")
                
                for i, elem_info in enumerate(teile_elements[:3]):  # Max 3 versuchen
                    try:
                        elem_id = elem_info.get('id', '')
                        if elem_id:
                            logger.info(f"Klicke auf Element {i+1}: {elem_info.get('text', '')[:50]}")
                            
                            # Versuche Element zu finden und zu klicken
                            click_script = f"""
                            var element = document.getElementById('{elem_id}');
                            if (element) {{
                                element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                element.click();
                                return true;
                            }}
                            return false;
                            """
                            
                            clicked = self.driver.execute_script(click_script)
                            if clicked:
                                logger.info("  ✅ Klick erfolgreich")
                                time.sleep(5)  # Warte auf Navigation
                                
                                # Erfasse Requests
                                self.capture_network_requests()
                                
                                # Mache Screenshot
                                try:
                                    self.driver.save_screenshot(f'/tmp/mobis_teilebezug_{i+1}.png')
                                except:
                                    pass
                            else:
                                logger.warning("  ⚠️  Klick fehlgeschlagen")
                    except Exception as e:
                        logger.warning(f"Fehler beim Klicken: {str(e)}")
            
            # Suche auch nach Menü-Struktur
            logger.info("Analysiere Menü-Struktur...")
            menu_structure_script = """
            // Suche nach Menü-Komponenten (Nexacro verwendet oft spezielle Komponenten)
            var menuElements = [];
            
            // Suche nach Divs mit Menü-ähnlichen Klassen
            var divs = document.querySelectorAll('div[class*="menu"], div[class*="Menu"], div[class*="tree"], div[class*="Tree"]');
            for (var i = 0; i < divs.length; i++) {
                var text = divs[i].textContent || '';
                if (text.toLowerCase().includes('teil') || text.toLowerCase().includes('part')) {
                    menuElements.push({
                        type: 'menu',
                        text: text.substring(0, 100),
                        id: divs[i].id
                    });
                }
            }
            
            return menuElements;
            """
            
            menu_structure = self.driver.execute_script(menu_structure_script)
            if menu_structure:
                logger.info(f"Menü-Struktur gefunden: {len(menu_structure)} Elemente")
            
        except Exception as e:
            logger.error(f"Fehler beim Suchen nach Teilebezug: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def analyze(self):
        """Führt vollständige Analyse durch."""
        print("=" * 80)
        print("MOBIS EDMOS SELENIUM-ANALYSE")
        print("=" * 80)
        
        if not self.setup_driver():
            print("❌ Konnte Chrome Driver nicht erstellen")
            return None
        
        try:
            # 1. Login
            if self.login():
                print("\n✅ Login erfolgreich!")
                
                # 2. Suche nach Teilebezug
                self.search_parts_functionality()
                
                # 3. Warte etwas für weitere Requests
                time.sleep(5)
                self.capture_network_requests()
                
                # 4. Ergebnisse ausgeben
                print("\n" + "=" * 80)
                print("ANALYSE-ERGEBNISSE")
                print("=" * 80)
                
                print(f"\nGesamte Network-Requests: {len(self.network_requests)}")
                print(f"API-Endpunkte (.do, /api/, etc.): {len(self.api_endpoints)}")
                print(f"Teilebezug-relevante Endpunkte: {len(self.teilebezug_endpoints)}")
                
                if self.api_endpoints:
                    print("\n📋 API-Endpunkte:")
                    for ep in self.api_endpoints[:20]:
                        print(f"  - {ep['method']} {ep['url']}")
                        if ep.get('postData'):
                            print(f"    POST Data: {ep['postData'][:200]}")
                
                if self.teilebezug_endpoints:
                    print("\n🔧 Teilebezug-Endpunkte:")
                    for ep in self.teilebezug_endpoints:
                        print(f"  ✅ {ep['method']} {ep['url']}")
                        print(f"     Status: {ep.get('status', 'N/A')}")
                        print(f"     MIME: {ep.get('mimeType', 'N/A')}")
                        if ep.get('postData'):
                            print(f"     POST Data: {ep['postData'][:300]}")
                
                # 5. Speichere Ergebnisse
                results = {
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_requests': len(self.network_requests),
                    'api_endpoints': self.api_endpoints,
                    'teilebezug_endpoints': self.teilebezug_endpoints,
                    'all_requests': self.network_requests[:100]  # Erste 100 Requests
                }
                
                with open('/tmp/mobis_selenium_analysis.json', 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                
                print(f"\n✅ Ergebnisse gespeichert: /tmp/mobis_selenium_analysis.json")
                
                return results
            else:
                print("\n❌ Login fehlgeschlagen")
                return None
                
        finally:
            if self.driver:
                self.driver.quit()
                print("\nBrowser geschlossen")


def main():
    analyzer = MobisSeleniumAnalyzer()
    results = analyzer.analyze()
    
    if results and results.get('teilebezug_endpoints'):
        print("\n" + "=" * 80)
        print("✅ TEILEBEZUG-ENDPUNKTE GEFUNDEN!")
        print("=" * 80)
        print("\nDiese Endpunkte können für die Integration verwendet werden.")
    else:
        print("\n⚠️  Keine Teilebezug-Endpunkte gefunden.")
        print("Möglicherweise ist manuelle Navigation nötig.")


if __name__ == "__main__":
    main()
