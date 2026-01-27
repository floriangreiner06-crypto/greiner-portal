"""
Customer First (PSA/Stellantis) Client
API-Client für Customer First Integration (Salesforce-basiert)

Customer First ist das Hersteller-System von Opel/Stellantis, in dem
alle Kaufverträge erfasst werden müssen.

URL: https://www.customer360psa.com/s/login/
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import re
import warnings
import logging
from typing import Optional, Dict, List, Any
import json
import time

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Selenium für JavaScript-basierte Login-Seiten
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium nicht verfügbar - JavaScript-basierte Login-Seiten werden nicht unterstützt")


class CustomerFirstClient:
    """Client für Customer First (Salesforce) API-Zugriff"""
    
    BASE_URL = "https://www.customer360psa.com"
    LOGIN_URL = f"{BASE_URL}/s/login/"
    
    def __init__(self, username: str, password: str):
        """
        Initialisiert Customer First Client
        
        Args:
            username: Customer First Benutzername (z.B. DE-001007V.d004)
            password: Customer First Passwort
        """
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False  # SSL-Verifikation deaktiviert (wie eAutoseller)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        self._logged_in = False
        self._instance_url = None
        self._access_token = None
    
    def login(self, saml_url: Optional[str] = None, use_selenium: bool = True) -> bool:
        """
        Login zu Customer First (Salesforce)
        
        Args:
            saml_url: Optional - Direkte SAML-URL für "ID Europe" (falls bekannt)
                      Format: https://sts.fiatgroup.com/adfs/ls/?SAMLRequest=...
        
        Returns:
            bool: True wenn Login erfolgreich
        """
        try:
            logger.info(f"Versuche Login zu Customer First: {self.username}")
            
            # 1. SAML-URL ermitteln
            if not saml_url:
                # Login-Seite laden und SAML-URL extrahieren
                login_params = {
                    'language': 'en_US',
                    'ec': '302',
                    'startURL': '/s/'
                }
                resp = self.session.get(self.LOGIN_URL, params=login_params, timeout=15)
                
                if resp.status_code != 200:
                    raise Exception(f"Login-Seite konnte nicht geladen werden: {resp.status_code}")
                
                logger.debug(f"Login-Seite geladen: {len(resp.text)} Zeichen")
                
                # HTML parsen und SAML-Link suchen
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Suche nach Links zu sts.fiatgroup.com (SAML-Authentifizierung)
                saml_links = soup.find_all('a', href=re.compile(r'sts\.fiatgroup\.com', re.I))
                
                if saml_links:
                    saml_url = saml_links[0].get('href', '')
                    if not saml_url.startswith('http'):
                        saml_url = urljoin(self.BASE_URL, saml_url)
                    logger.info("SAML-URL aus Login-Seite extrahiert")
                else:
                    raise Exception("SAML-URL nicht gefunden. Bitte SAML-URL manuell angeben.")
            else:
                logger.info("Verwende übergebene SAML-URL")
            
            # 2. SAML-Authentifizierungsseite aufrufen
            logger.info(f"Rufe SAML-Authentifizierungsseite auf: {saml_url[:100]}...")
            
            # Prüfe ob Selenium verwendet werden soll (für JavaScript-basierte Seiten)
            if use_selenium and SELENIUM_AVAILABLE:
                return self._login_with_selenium(saml_url)
            
            # Fallback: Standard HTTP-Request (funktioniert nicht für JavaScript-Seiten)
            logger.warning("Selenium nicht verwendet - Login wird wahrscheinlich fehlschlagen (JavaScript erforderlich)")
            resp = self.session.get(saml_url, timeout=15, allow_redirects=True)
            
            if resp.status_code != 200:
                raise Exception(f"SAML-Seite konnte nicht geladen werden: {resp.status_code}")
            
            logger.debug(f"SAML-Seite geladen: {len(resp.text)} Zeichen, URL: {resp.url}")
            
            # 3. HTML parsen und Login-Formular finden
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Da die Seite JavaScript-basiert ist, suche nach SAML-Redirect-URLs oder Europe-Links
            # Alternative: Direkte SAML-URL verwenden (bekannt: sts.fiatgroup.com/adfs/ls/)
            
            # Suche nach Links zu sts.fiatgroup.com (SAML-Authentifizierung)
            saml_links = soup.find_all('a', href=re.compile(r'sts\.fiatgroup\.com', re.I))
            
            if saml_links:
                logger.info("SAML-Authentifizierung gefunden, folge 'ID Europe' Link")
                # Nimm ersten SAML-Link (sollte "ID Europe" sein)
                saml_url = saml_links[0].get('href', '')
                if not saml_url.startswith('http'):
                    saml_url = urljoin(self.BASE_URL, saml_url)
                resp = self.session.get(saml_url, timeout=15)
                soup = BeautifulSoup(resp.text, 'html.parser')
            else:
                # Fallback: Versuche direkte SAML-URL (wenn bekannt)
                # Die URL nach "ID Europe" Klick ist: sts.fiatgroup.com/adfs/ls/?SAMLRequest=...
                # Da wir die genaue URL nicht kennen, müssen wir sie aus der JavaScript-Seite extrahieren
                # Oder: Versuche direkten Zugriff auf ADFS-Login
                logger.debug("Kein SAML-Link gefunden, versuche direkten ADFS-Zugriff")
            
            # 4. Suche nach Login-Formular (ADFS-Format)
            # ADFS verwendet typischerweise Formulare mit id="loginForm" oder ähnlich
            form = (
                soup.find('form', {'id': 'loginForm'}) or
                soup.find('form', {'id': 'theForm'}) or
                soup.find('form', {'name': 'login'}) or
                soup.find('form', {'action': re.compile(r'adfs', re.I)}) or
                soup.find('form')
            )
            
            if not form:
                # Prüfe ob es eine JavaScript-basierte Seite ist
                if 'javascript' in resp.text.lower() and 'required' in resp.text.lower():
                    raise Exception("JavaScript erforderlich - Seite benötigt Browser-Automatisierung (Selenium/Playwright)")
                
                # Versuche direkten Login-POST
                logger.warning("Kein Formular gefunden, versuche direkten Login")
                return self._try_direct_login(resp)
            
            # 5. Login-Daten sammeln
            login_data = {}
            
            # Alle versteckten Input-Felder sammeln (wichtig für SAML!)
            for field in form.find_all('input', type='hidden'):
                name = field.get('name')
                value = field.get('value', '')
                if name:
                    login_data[name] = value
            
            # Username und Password setzen
            # ADFS verwendet typischerweise 'UserName' und 'Password' als Feldnamen
            username_field = (
                form.find('input', {'id': 'userNameInput'}) or
                form.find('input', {'id': 'username'}) or
                form.find('input', {'name': 'UserName'}) or
                form.find('input', {'name': re.compile(r'user', re.I)})
            )
            password_field = (
                form.find('input', {'id': 'passwordInput'}) or
                form.find('input', {'id': 'password'}) or
                form.find('input', {'type': 'password'})
            )
            
            if username_field:
                login_data[username_field.get('name', 'UserName')] = self.username
            else:
                login_data['UserName'] = self.username
            
            if password_field:
                login_data[password_field.get('name', 'Password')] = self.password
            else:
                login_data['Password'] = self.password
            
            # "Keep me signed in" Checkbox (optional)
            keep_signed_in = form.find('input', {'type': 'checkbox', 'name': re.compile(r'remember|keep', re.I)})
            if keep_signed_in:
                login_data[keep_signed_in.get('name')] = 'true'
            
            # 6. Action-URL finden
            action = form.get('action', '')
            if not action or action.startswith('#'):
                # Fallback: Verwende aktuelle Domain (ADFS)
                parsed = urlparse(resp.url)
                login_url = f"{parsed.scheme}://{parsed.netloc}{action}" if action else resp.url
            else:
                # Relative oder absolute URL
                if action.startswith('http'):
                    login_url = action
                else:
                    parsed = urlparse(resp.url)
                    login_url = f"{parsed.scheme}://{parsed.netloc}{action}"
            
            logger.debug(f"Login-URL: {login_url}")
            logger.debug(f"Login-Daten: {list(login_data.keys())}")
            
            # 7. Login durchführen (SAML-Response wird automatisch weitergeleitet)
            resp = self.session.post(login_url, data=login_data, allow_redirects=True, timeout=30)
            
            # 8. Prüfe ob Login erfolgreich und verarbeite SAML-Response
            logger.debug(f"Nach Login - Status: {resp.status_code}, URL: {resp.url}")
            
            if resp.status_code in [200, 302]:
                # Prüfe ob wir auf einer Fehlerseite sind
                if 'error' in resp.url.lower() or ('login' in resp.url.lower() and 'customer360psa.com' not in resp.url.lower()):
                    # Prüfe HTML auf Fehlermeldungen
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    error_msg = (
                        soup.find('div', {'id': 'error'}) or
                        soup.find('div', class_=re.compile(r'error', re.I)) or
                        soup.find('span', class_=re.compile(r'error', re.I)) or
                        soup.find('p', class_=re.compile(r'error', re.I))
                    )
                    if error_msg:
                        error_text = error_msg.get_text(strip=True)
                        if error_text:
                            raise Exception(f"Login fehlgeschlagen: {error_text}")
                    
                    # Keine explizite Fehlermeldung, aber noch auf Login-Seite
                    raise Exception(f"Login fehlgeschlagen: Noch auf Login-Seite ({resp.url})")
                
                # Prüfe ob wir zu Customer First weitergeleitet wurden
                if 'customer360psa.com' in resp.url.lower() or 'salesforce.com' in resp.url.lower():
                    # Erfolgreich eingeloggt
                    self._logged_in = True
                    self._instance_url = self._extract_instance_url(resp)
                    logger.info(f"Login erfolgreich! Instance URL: {self._instance_url}")
                    return True
                
                # Prüfe ob SAML-Response im HTML ist (automatisches Form-Submit)
                soup = BeautifulSoup(resp.text, 'html.parser')
                saml_response_form = soup.find('form', {'action': re.compile(r'customer360psa|salesforce', re.I)})
                
                if saml_response_form:
                    logger.info("SAML-Response-Form gefunden, sende an Customer First...")
                    # Sammle alle Form-Daten (SAMLResponse, RelayState, etc.)
                    saml_data = {}
                    for field in saml_response_form.find_all('input', type='hidden'):
                        name = field.get('name', '')
                        value = field.get('value', '')
                        if name:
                            saml_data[name] = value
                    
                    # Action-URL
                    action = saml_response_form.get('action', '')
                    if not action.startswith('http'):
                        # Relative URL - verwende Customer First Base URL
                        action = urljoin(self.BASE_URL, action)
                    
                    logger.debug(f"Sende SAML-Response an: {action}")
                    # POST SAML-Response an Customer First
                    resp = self.session.post(action, data=saml_data, allow_redirects=True, timeout=30)
                    
                    if 'customer360psa.com' in resp.url.lower() or 'salesforce.com' in resp.url.lower():
                        self._logged_in = True
                        self._instance_url = self._extract_instance_url(resp)
                        logger.info(f"Login erfolgreich nach SAML-Response! Instance URL: {self._instance_url}")
                        return True
                    else:
                        logger.warning(f"SAML-Response gesendet, aber noch nicht bei Customer First: {resp.url}")
                
                # Möglicherweise noch im SAML-Flow (Redirect)
                if resp.status_code == 302:
                    logger.debug(f"302 Redirect erkannt, folge: {resp.headers.get('Location', 'N/A')}")
                    # Session folgt automatisch Redirects, prüfe finale URL
                    if 'customer360psa.com' in resp.url.lower():
                        self._logged_in = True
                        self._instance_url = self._extract_instance_url(resp)
                        logger.info(f"Login erfolgreich nach Redirect! Instance URL: {self._instance_url}")
                        return True
                
                raise Exception(f"Login-Status unklar: URL {resp.url}")
            else:
                raise Exception(f"Login fehlgeschlagen: HTTP {resp.status_code}")
            
        except Exception as e:
            self._logged_in = False
            logger.error(f"Login-Fehler: {str(e)}")
            raise Exception(f"Login-Fehler: {str(e)}")
    
    def _login_with_selenium(self, saml_url: str) -> bool:
        """
        Login mit Selenium (für JavaScript-basierte ADFS-Seiten)
        
        Args:
            saml_url: SAML-Authentifizierungs-URL
            
        Returns:
            bool: True wenn Login erfolgreich
        """
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium nicht verfügbar. Installiere mit: pip install selenium")
        
        driver = None
        try:
            logger.info("Starte Selenium für JavaScript-basierte Login-Seite...")
            
            # Chrome-Optionen (Headless-Modus)
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # ChromeDriver starten
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            
            # SAML-Seite öffnen
            logger.info(f"Öffne SAML-Seite: {saml_url[:100]}...")
            driver.get(saml_url)
            
            # Warte auf Login-Formular (max. 10 Sekunden)
            wait = WebDriverWait(driver, 10)
            
            # Suche nach Username-Feld (verschiedene Varianten)
            username_field = None
            username_selectors = [
                (By.ID, 'userNameInput'),
                (By.ID, 'username'),
                (By.NAME, 'UserName'),
                (By.NAME, 'username'),
                (By.CSS_SELECTOR, 'input[type="text"][name*="user" i]'),
            ]
            
            for by, selector in username_selectors:
                try:
                    username_field = wait.until(EC.presence_of_element_located((by, selector)))
                    logger.info(f"Username-Feld gefunden: {by}={selector}")
                    break
                except TimeoutException:
                    continue
            
            if not username_field:
                # Screenshot für Debugging
                driver.save_screenshot('/tmp/customer_first_login_debug.png')
                logger.error("Username-Feld nicht gefunden. Screenshot gespeichert: /tmp/customer_first_login_debug.png")
                raise Exception("Username-Feld auf ADFS-Login-Seite nicht gefunden")
            
            # Password-Feld finden
            password_field = None
            password_selectors = [
                (By.ID, 'passwordInput'),
                (By.ID, 'password'),
                (By.NAME, 'Password'),
                (By.NAME, 'password'),
                (By.CSS_SELECTOR, 'input[type="password"]'),
            ]
            
            for by, selector in password_selectors:
                try:
                    password_field = driver.find_element(by, selector)
                    logger.info(f"Password-Feld gefunden: {by}={selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                raise Exception("Password-Feld auf ADFS-Login-Seite nicht gefunden")
            
            # Credentials eingeben
            logger.info("Eingabe der Credentials...")
            username_field.clear()
            username_field.send_keys(self.username)
            
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Submit-Button finden und klicken
            submit_button = None
            submit_selectors = [
                (By.ID, 'submitButton'),
                (By.ID, 'loginButton'),
                (By.NAME, 'Submit'),
                (By.CSS_SELECTOR, 'input[type="submit"]'),
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.CSS_SELECTOR, 'button:contains("Sign in")'),
            ]
            
            for by, selector in submit_selectors:
                try:
                    submit_button = driver.find_element(by, selector)
                    logger.info(f"Submit-Button gefunden: {by}={selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not submit_button:
                # Versuche Enter-Taste auf Password-Feld
                logger.warning("Submit-Button nicht gefunden, versuche Enter-Taste")
                from selenium.webdriver.common.keys import Keys
                password_field.send_keys(Keys.RETURN)
            else:
                submit_button.click()
            
            # Warte auf Weiterleitung (max. 30 Sekunden)
            logger.info("Warte auf SAML-Response und Weiterleitung zu Customer First...")
            try:
                wait.until(lambda d: 'customer360psa.com' in d.current_url or 'salesforce.com' in d.current_url or 'sts.fiatgroup.com' not in d.current_url)
            except TimeoutException:
                logger.warning("Timeout beim Warten auf Weiterleitung, prüfe aktuelle URL...")
            
            # Prüfe finale URL
            final_url = driver.current_url
            logger.info(f"Finale URL nach Login: {final_url}")
            
            # Falls SAML-Error, versuche trotzdem Cookies zu extrahieren
            if 'SamlError' in final_url:
                logger.warning("SAML-Error erkannt, versuche trotzdem Session-Cookies zu extrahieren...")
                # Warte kurz, damit Seite vollständig geladen ist
                time.sleep(2)
            
            # Cookies von Selenium zu requests-Session kopieren (immer, auch bei Fehler)
            logger.info("Kopiere Cookies von Selenium zu requests-Session...")
            for cookie in driver.get_cookies():
                try:
                    # Domain anpassen falls nötig
                    domain = cookie.get('domain', '')
                    if domain.startswith('.'):
                        domain = domain[1:]
                    self.session.cookies.set(cookie['name'], cookie['value'], domain=domain)
                    logger.debug(f"Cookie kopiert: {cookie['name']} = {cookie['value'][:20]}...")
                except Exception as e:
                    logger.debug(f"Cookie konnte nicht kopiert werden: {str(e)}")
            
            # Versuche Session-ID aus Cookies zu extrahieren
            session_id = None
            for cookie in driver.get_cookies():
                if 'sid' in cookie['name'].lower() or 'session' in cookie['name'].lower():
                    session_id = cookie['value']
                    self._access_token = session_id
                    logger.info(f"Session-ID aus Cookie extrahiert: {cookie['name']} = {session_id[:30]}...")
                    break
            
            # Versuche OAuth-Token aus JavaScript-Variablen zu extrahieren
            try:
                oauth_token = driver.execute_script("""
                    // Salesforce speichert OAuth-Token oft in window-Variablen
                    if (window.sfdcSessionId) return window.sfdcSessionId;
                    if (window.SfdcApp && window.SfdcApp.sessionId) return window.SfdcApp.sessionId;
                    if (window.sid) return window.sid;
                    // Oder aus localStorage
                    if (window.localStorage) {
                        var keys = Object.keys(window.localStorage);
                        for (var i = 0; i < keys.length; i++) {
                            if (keys[i].includes('sid') || keys[i].includes('session')) {
                                return window.localStorage.getItem(keys[i]);
                            }
                        }
                    }
                    return null;
                """)
                if oauth_token:
                    self._access_token = oauth_token
                    logger.info(f"OAuth-Token aus JavaScript extrahiert: {oauth_token[:20]}...")
            except Exception as e:
                logger.debug(f"OAuth-Token konnte nicht aus JavaScript extrahiert werden: {str(e)}")
            
            # Versuche Session-ID aus URL zu extrahieren
            if 'sid=' in final_url:
                try:
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(final_url)
                    params = parse_qs(parsed.query)
                    if 'sid' in params:
                        session_id = params['sid'][0]
                        self._access_token = session_id
                        logger.info(f"Session-ID aus URL extrahiert: {session_id[:20]}...")
                except Exception as e:
                    logger.debug(f"Session-ID konnte nicht aus URL extrahiert werden: {str(e)}")
            
            # Prüfe ob wir bei Customer First sind (auch bei SamlError)
            if 'customer360psa.com' in final_url.lower() or 'salesforce.com' in final_url.lower():
                self._logged_in = True
                self._instance_url = self._extract_instance_url_from_url(final_url)
                
                if 'SamlError' in final_url:
                    logger.warning("SAML-Error erkannt, aber Session-Cookies wurden extrahiert")
                    logger.info(f"Instance URL: {self._instance_url}")
                    # Versuche trotzdem weiter (Session-Cookies könnten funktionieren)
                    return True
                else:
                    logger.info(f"Login erfolgreich! Instance URL: {self._instance_url}")
                    return True
            else:
                # Prüfe ob Fehlermeldung vorhanden
                try:
                    error_elements = driver.find_elements(By.CSS_SELECTOR, '.error, #error, [class*="error" i]')
                    if error_elements:
                        error_text = error_elements[0].text
                        if error_text:
                            raise Exception(f"Login fehlgeschlagen: {error_text}")
                except Exception as e:
                    if "Login fehlgeschlagen" in str(e):
                        raise
                    pass
                
                raise Exception(f"Login-Status unklar: URL {final_url}")
            
        except TimeoutException as e:
            logger.error(f"Timeout beim Warten auf Element: {str(e)}")
            if driver:
                driver.save_screenshot('/tmp/customer_first_login_timeout.png')
                logger.error("Screenshot gespeichert: /tmp/customer_first_login_timeout.png")
            raise Exception(f"Timeout beim Login: {str(e)}")
        except Exception as e:
            logger.error(f"Selenium-Login-Fehler: {str(e)}")
            if driver:
                try:
                    driver.save_screenshot('/tmp/customer_first_login_error.png')
                    logger.error("Screenshot gespeichert: /tmp/customer_first_login_error.png")
                except:
                    pass
            raise
        finally:
            if driver:
                driver.quit()
                logger.debug("Selenium-Browser geschlossen")
    
    def _extract_instance_url_from_url(self, url: str) -> Optional[str]:
        """
        Extrahiert Instance URL aus URL-String
        
        Args:
            url: URL-String
            
        Returns:
            str: Instance URL oder None
        """
        parsed = urlparse(url)
        if parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return None
    
    def _try_direct_login(self, initial_resp: requests.Response) -> bool:
        """
        Versucht direkten Login (falls kein Formular gefunden)
        
        Args:
            initial_resp: Initiale Response von Login-Seite
            
        Returns:
            bool: True wenn Login erfolgreich
        """
        try:
            # Verschiedene Salesforce Login-Endpoints versuchen
            login_endpoints = [
                f"{self.BASE_URL}/secur/login_after.jsp",
                f"{self.BASE_URL}/secur/login.jsp",
                f"{self.BASE_URL}/s/login",
            ]
            
            login_data = {
                'username': self.username,
                'password': self.password,
            }
            
            # CSRF-Token aus initialer Response extrahieren
            soup = BeautifulSoup(initial_resp.text, 'html.parser')
            
            # Verschiedene Token-Namen versuchen
            token_inputs = [
                soup.find('input', {'name': 'com.salesforce.visualforce.ViewState'}),
                soup.find('input', {'name': re.compile(r'csrf|token|viewstate', re.I)}),
                soup.find('input', {'type': 'hidden', 'value': re.compile(r'.{20,}')}),
            ]
            
            for token_input in token_inputs:
                if token_input:
                    name = token_input.get('name')
                    value = token_input.get('value', '')
                    if name and value:
                        login_data[name] = value
                        break
            
            # Versuche verschiedene Endpoints
            for login_url in login_endpoints:
                try:
                    logger.debug(f"Versuche Login-Endpoint: {login_url}")
                    resp = self.session.post(login_url, data=login_data, allow_redirects=True, timeout=15)
                    
                    logger.debug(f"Response Status: {resp.status_code}, URL: {resp.url}")
                    
                    # Prüfe ob Login erfolgreich
                    if resp.status_code in [200, 302]:
                        # Prüfe ob wir von Login-Seite weggeleitet wurden
                        if 'login' not in resp.url.lower() or resp.status_code == 302:
                            # Prüfe HTML auf Fehlermeldungen
                            if resp.status_code == 200:
                                soup_check = BeautifulSoup(resp.text, 'html.parser')
                                error_elements = soup_check.find_all(['div', 'span'], class_=re.compile(r'error', re.I))
                                if error_elements:
                                    error_text = ' '.join([e.get_text(strip=True) for e in error_elements[:3]])
                                    logger.warning(f"Fehlermeldung gefunden: {error_text}")
                                    continue
                            
                            # Erfolgreich
                            self._logged_in = True
                            self._instance_url = self._extract_instance_url(resp)
                            logger.info(f"Direkter Login erfolgreich! Instance URL: {self._instance_url}")
                            return True
                except Exception as e:
                    logger.debug(f"Endpoint {login_url} fehlgeschlagen: {str(e)}")
                    continue
            
            raise Exception("Alle Login-Endpoints fehlgeschlagen")
            
        except Exception as e:
            logger.error(f"Direkter Login-Fehler: {str(e)}")
            return False
    
    def _extract_instance_url(self, resp: requests.Response) -> Optional[str]:
        """
        Extrahiert Instance URL aus Response
        
        Args:
            resp: Response nach erfolgreichem Login
            
        Returns:
            str: Instance URL oder None
        """
        # Versuche aus URL zu extrahieren
        parsed = urlparse(resp.url)
        if parsed.netloc:
            instance_url = f"{parsed.scheme}://{parsed.netloc}"
            return instance_url
        
        # Versuche aus HTML zu extrahieren
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Suche nach Salesforce-spezifischen Meta-Tags oder Scripts
        instance_script = soup.find('script', string=re.compile(r'instanceUrl|instance_url', re.I))
        if instance_script:
            match = re.search(r'["\']([^"\']*customer360psa[^"\']*)["\']', instance_script.string)
            if match:
                return match.group(1)
        
        # Fallback: Basis-URL
        return self.BASE_URL
    
    def ensure_login(self):
        """Stellt sicher, dass eingeloggt ist"""
        if not self._logged_in:
            self.login()
    
    def get_rest_api_base(self) -> str:
        """
        Gibt die REST API Base URL zurück
        
        Returns:
            str: REST API Base URL
        """
        self.ensure_login()
        
        if self._instance_url:
            # Salesforce REST API ist typischerweise unter /services/data/vXX.0/
            return f"{self._instance_url}/services/data/v58.0"
        
        return f"{self.BASE_URL}/services/data/v58.0"
    
    def get_session_id(self) -> Optional[str]:
        """
        Gibt die Session-ID zurück (für API-Aufrufe)
        
        Returns:
            str: Session-ID oder None
        """
        if self._access_token:
            return self._access_token
        
        # Versuche aus Cookies zu extrahieren
        if 'sid' in self.session.cookies:
            return self.session.cookies['sid']
        
        return None
    
    def get_salesforce_objects(self, object_type: str = None) -> List[Dict[str, Any]]:
        """
        Ruft Salesforce-Objekte ab
        
        Args:
            object_type: Optional - spezifischer Objekt-Typ (z.B. 'Account', 'Opportunity')
            
        Returns:
            List[Dict]: Liste von Objekten
        """
        self.ensure_login()
        
        try:
            # Versuche REST API zu nutzen
            api_base = self.get_rest_api_base()
            
            # Headers mit Session-ID
            headers = {
                'Accept': 'application/json',
            }
            
            # Session-ID hinzufügen (falls vorhanden)
            session_id = self.get_session_id()
            if session_id:
                headers['Authorization'] = f'Bearer {session_id}'
                # Oder als Cookie
                self.session.cookies.set('sid', session_id)
            
            if object_type:
                # Spezifisches Objekt abrufen
                url = f"{api_base}/sobjects/{object_type}/describe"
            else:
                # Alle Objekte auflisten
                url = f"{api_base}/sobjects/"
            
            resp = self.session.get(url, headers=headers, timeout=15)
            
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 401:
                # Nicht authentifiziert - versuche alternative Methoden
                logger.warning("REST API erfordert OAuth-Token")
                
                # Versuche mit Session-Cookie direkt
                if session_id:
                    # Versuche alternative API-Endpoints
                    return self._try_alternative_api_access()
                
                return []
            else:
                logger.warning(f"REST API nicht verfügbar: {resp.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von Salesforce-Objekten: {str(e)}")
            return []
    
    def _try_alternative_api_access(self) -> List[Dict[str, Any]]:
        """
        Versucht alternative Wege, um auf die API zuzugreifen
        
        Returns:
            List[Dict]: Liste von Objekten oder leer
        """
        try:
            # Versuche über die Hauptseite API-Informationen zu extrahieren
            html = self.get_page_content('/s/')
            if html:
                # Suche nach JavaScript-Variablen mit API-Informationen
                import re
                # Suche nach Objekt-Definitionen im JavaScript
                object_matches = re.findall(r'(?:sobject|object|entity)[\s:]*["\']([A-Za-z_][A-Za-z0-9_]*)["\']', html, re.I)
                if object_matches:
                    logger.info(f"Mögliche Objekte im JavaScript gefunden: {object_matches[:10]}")
                    return [{'name': obj} for obj in set(object_matches[:20])]
        except Exception as e:
            logger.debug(f"Alternative API-Zugriff fehlgeschlagen: {str(e)}")
        
        return []
    
    def search_kaufvertraege(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Sucht nach Kaufverträgen (Salesforce SOQL Query)
        
        Args:
            limit: Maximale Anzahl Ergebnisse
            
        Returns:
            List[Dict]: Liste von Kaufverträgen
        """
        self.ensure_login()
        
        try:
            api_base = self.get_rest_api_base()
            
            # Headers mit Session-ID
            headers = {
                'Accept': 'application/json',
            }
            session_id = self.get_session_id()
            if session_id:
                headers['Authorization'] = f'Bearer {session_id}'
                self.session.cookies.set('sid', session_id)
            
            # SOQL Query für Kaufverträge
            # Hinweis: Objekt-Name muss noch ermittelt werden
            # Mögliche Namen: Contract, Opportunity, Order, etc.
            
            # Versuche verschiedene Objekte
            possible_objects = [
                'Contract', 
                'Opportunity', 
                'Order', 
                'Sales_Order__c', 
                'Kaufvertrag__c',
                'Vehicle_Order__c',
                'Vehicle_Sale__c',
                'Dealer_Order__c',
            ]
            
            for obj_name in possible_objects:
                try:
                    # SOQL Query
                    from urllib.parse import quote
                    query = f"SELECT Id, Name, CreatedDate, LastModifiedDate FROM {obj_name} LIMIT {limit}"
                    url = f"{api_base}/query/?q={quote(query)}"
                    
                    resp = self.session.get(url, headers=headers, timeout=15)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        if 'records' in data and len(data['records']) > 0:
                            logger.info(f"Kaufverträge gefunden in Objekt: {obj_name} ({len(data['records'])} Einträge)")
                            return data['records']
                    elif resp.status_code == 401:
                        logger.debug(f"Objekt {obj_name} erfordert OAuth-Token")
                    else:
                        logger.debug(f"Objekt {obj_name} nicht verfügbar: HTTP {resp.status_code}")
                    
                except Exception as e:
                    logger.debug(f"Objekt {obj_name} nicht verfügbar: {str(e)}")
                    continue
            
            # Versuche über HTML-Seite Objekte zu finden
            logger.info("Versuche Objekte über HTML-Seite zu identifizieren...")
            html = self.get_page_content('/s/')
            if html:
                # Suche nach Custom Objects in JavaScript
                import re
                # Salesforce Custom Objects haben oft __c Suffix
                custom_objects = re.findall(r'([A-Za-z_][A-Za-z0-9_]*__c)', html)
                if custom_objects:
                    unique_objects = list(set(custom_objects))[:10]
                    logger.info(f"Custom Objects im HTML gefunden: {unique_objects}")
                    # Versuche diese Objekte abzufragen
                    for obj_name in unique_objects:
                        if obj_name not in possible_objects:
                            try:
                                query = f"SELECT Id, Name FROM {obj_name} LIMIT 5"
                                url = f"{api_base}/query/?q={quote(query)}"
                                resp = self.session.get(url, headers=headers, timeout=15)
                                if resp.status_code == 200:
                                    data = resp.json()
                                    if 'records' in data and len(data['records']) > 0:
                                        logger.info(f"✅ Daten gefunden in Objekt: {obj_name}")
                                        return data['records']
                            except:
                                continue
            
            logger.warning("Keine Kaufverträge gefunden in bekannten Objekten")
            return []
            
        except Exception as e:
            logger.error(f"Fehler beim Suchen von Kaufverträgen: {str(e)}")
            return []
    
    def get_page_content(self, path: str = '/s/') -> Optional[str]:
        """
        Ruft HTML-Inhalt einer Seite ab (für manuelle Analyse)
        
        Args:
            path: Pfad zur Seite (z.B. '/s/')
            
        Returns:
            str: HTML-Inhalt oder None
        """
        self.ensure_login()
        
        try:
            url = urljoin(self.BASE_URL, path)
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code == 200:
                return resp.text
            else:
                logger.warning(f"Seite konnte nicht geladen werden: {resp.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Fehler beim Laden der Seite: {str(e)}")
            return None
    
    def explore_ui_for_objects(self) -> Dict[str, Any]:
        """
        Exploriert die UI nach verfügbaren Objekten und Endpoints
        
        Returns:
            Dict: Gefundene Informationen
        """
        self.ensure_login()
        
        info = {
            'objects_found': [],
            'api_endpoints': [],
            'javascript_vars': [],
        }
        
        try:
            # Hauptseite laden
            html = self.get_page_content('/s/')
            if not html:
                return info
            
            # Suche nach Objekt-Namen in JavaScript
            import re
            
            # Salesforce Custom Objects (endet mit __c)
            custom_objects = re.findall(r'([A-Za-z_][A-Za-z0-9_]*__c)', html)
            if custom_objects:
                info['objects_found'] = list(set(custom_objects))[:20]
                logger.info(f"Custom Objects gefunden: {len(info['objects_found'])}")
            
            # Suche nach API-Endpoints in JavaScript
            api_patterns = [
                r'["\']([^"\']*\/services\/[^"\']*)["\']',
                r'["\']([^"\']*\/api\/[^"\']*)["\']',
                r'["\']([^"\']*\/apexrest\/[^"\']*)["\']',
            ]
            
            for pattern in api_patterns:
                matches = re.findall(pattern, html, re.I)
                for match in matches:
                    if match not in info['api_endpoints']:
                        info['api_endpoints'].append(match)
            
            # Suche nach JavaScript-Variablen mit Objekt-Informationen
            js_var_patterns = [
                r'window\.(\w+)\s*=\s*["\']([^"\']+)["\']',
                r'var\s+(\w+)\s*=\s*["\']([^"\']+)["\']',
            ]
            
            for pattern in js_var_patterns:
                matches = re.findall(pattern, html)
                for var_name, var_value in matches:
                    if 'object' in var_name.lower() or 'api' in var_name.lower():
                        info['javascript_vars'].append({var_name: var_value})
            
            return info
            
        except Exception as e:
            logger.error(f"Fehler beim UI-Exploration: {str(e)}")
            return info
    
    def explore_api(self) -> Dict[str, Any]:
        """
        Exploriert die verfügbare API und gibt Informationen zurück
        
        Returns:
            Dict: API-Informationen
        """
        self.ensure_login()
        
        info = {
            'logged_in': self._logged_in,
            'instance_url': self._instance_url,
            'base_url': self.BASE_URL,
            'rest_api_base': self.get_rest_api_base(),
            'available_objects': [],
            'api_endpoints': [],
        }
        
        # Versuche REST API zu nutzen
        try:
            api_base = self.get_rest_api_base()
            
            # Versuche verschiedene Endpoints
            endpoints_to_try = [
                '/sobjects/',
                '/query/?q=SELECT Id FROM Account LIMIT 1',
                '/limits/',
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    url = f"{api_base}{endpoint}"
                    resp = self.session.get(url, timeout=10)
                    
                    if resp.status_code == 200:
                        info['api_endpoints'].append({
                            'endpoint': endpoint,
                            'status': 'available',
                            'response_type': resp.headers.get('Content-Type', ''),
                        })
                    else:
                        info['api_endpoints'].append({
                            'endpoint': endpoint,
                            'status': f'error_{resp.status_code}',
                        })
                        
                except Exception as e:
                    info['api_endpoints'].append({
                        'endpoint': endpoint,
                        'status': f'error: {str(e)}',
                    })
        
        except Exception as e:
            info['api_error'] = str(e)
        
        return info
