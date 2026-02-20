"""
DAT (SilverDAT) myClaim – VIN-Lookup über die interne Dispatcher-API.
Nutzt Session-Login (DAT_USER, DAT_PASSWORD) und POST doVinRequest.
Konfiguration: config/.env (DAT_URL, DAT_USER, DAT_PASSWORD, optional DAT_CUSTOMER_NUMBER).
Siehe docs/workstreams/werkstatt/Fahrzeuganlage/DAT_VIN_ABFRAGE_RECHERCHE.md
"""

import json
import os
import re
import logging
from typing import Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


def _load_dat_config() -> dict:
    """Lädt DAT-Konfiguration aus Umgebung (config/.env)."""
    url = os.environ.get("DAT_URL", "").rstrip("/")
    user = os.environ.get("DAT_USER", "")
    password = os.environ.get("DAT_PASSWORD", "")
    customer = os.environ.get("DAT_CUSTOMER_NUMBER", "")
    return {"base_url": url, "username": user, "password": password, "customer_number": customer}


def _dispatcher_url(base_url: str, component: str, action: str) -> str:
    """Baut die Dispatcher-URL: /myClaim/dispatcher--/call/{component}/{action}."""
    path = f"/myClaim/dispatcher--/call/{component}/{action}"
    return urljoin(base_url + "/", path.lstrip("/"))


def _parse_kba_list(kba_raw: str) -> list[tuple[str, str]]:
    """Parst KBA-Strings wie '1889/AFH, 1889/AGU, 2525/AAV' zu [(hsn, tsn), ...]."""
    if not kba_raw or not isinstance(kba_raw, str):
        return []
    out = []
    for part in kba_raw.replace(" ", "").split(","):
        part = part.strip()
        if "/" in part:
            a, b = part.split("/", 1)
            if a.isdigit() and len(b) >= 2:
                out.append((a, b.strip().upper()[:3]))
    return out


# JWT-Erkennung in Response (Token für myClaim)
_JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")


def _extract_jwt_from_response(response) -> Optional[str]:
    """Sucht in Response-Text, -URL und -Headers nach einem JWT."""
    text = (response.text or "") + (response.url or "") + str(response.headers)
    m = _JWT_RE.search(text)
    return m.group(0) if m else None


class DatVinClient:
    """Client für DAT myClaim VIN-Abfrage (Session-basiert)."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or _load_dat_config()
        self._session: Optional["requests.Session"] = None

    @property
    def session(self) -> "requests.Session":
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "Mozilla/5.0 (compatible; DRIVE-Portal/1.0)",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            })
        return self._session

    def is_configured(self) -> bool:
        """Prüft, ob URL und Zugangsdaten (Token oder User/Pass) gesetzt sind."""
        c = self.config
        if not c.get("base_url"):
            return False
        if c.get("token") and str(c.get("token", "")).strip():
            return True
        return bool(c.get("username") and c.get("password"))

    def _fetch_token_with_credentials(self) -> Optional[str]:
        """
        Versucht, mit User/Passwort beim DAT-Portal (AuthorizationManager) einen JWT zu erzeugen.
        Portal-Root ist z. B. https://www.dat.de (ohne /myClaim). Probiert typische Login-Endpoints.
        """
        base = self.config.get("base_url", "").rstrip("/")
        # Portal-Root: z. B. https://www.dat.de/myClaim → https://www.dat.de
        if "/myClaim" in base:
            portal_root = base.split("/myClaim")[0] or "https://www.dat.de"
        else:
            portal_root = base
        username = self.config.get("username", "")
        password = self.config.get("password", "")
        customer = self.config.get("customer_number", "")
        if not username or not password:
            return None
        # Typische Login-Pfade (AuthorizationManager / Kundenbereich)
        login_candidates = [
            ("POST", urljoin(portal_root + "/", "AuthorizationManager/authMgr/j_security_check"), {"j_username": username, "j_password": password}),
            ("POST", urljoin(portal_root + "/", "AuthorizationManager/authMgr/login"), {"username": username, "password": password}),
            ("POST", urljoin(portal_root + "/", "AuthorizationManager/api/login"), {"username": username, "password": password}),
            ("POST", urljoin(portal_root + "/", "api/auth/login"), {"username": username, "password": password, "customerNumber": customer}),
            ("POST", urljoin(portal_root + "/", "kunden-login"), {"username": username, "password": password}),
            ("POST", urljoin(portal_root + "/", "j_security_check"), {"j_username": username, "j_password": password}),
            ("POST", urljoin(portal_root + "/", "login"), {"username": username, "password": password}),
        ]
        if customer:
            for _method, _url, data in login_candidates:
                data["customerNumber"] = customer
                data["customer_number"] = customer
        # Zuerst Portal-Seite laden (Cookies)
        try:
            self.session.get(portal_root, timeout=15)
            self.session.get(urljoin(portal_root + "/", "AuthorizationManager/authMgr/"), timeout=15)
        except Exception as e:
            logger.debug("DAT Portal GET: %s", e)
        for method, url, data in login_candidates:
            try:
                r = self.session.post(url, data=data, timeout=15, allow_redirects=True)
                token = _extract_jwt_from_response(r)
                if token:
                    logger.info("DAT-Token aus Response erhalten (Endpoint %s)", url)
                    return token
                # Evtl. Token in Redirect-URL (Fragment/Query)
                if r.history:
                    for resp in r.history:
                        t = _extract_jwt_from_response(resp)
                        if t:
                            return t
            except Exception as e:
                logger.debug("Token-Versuch %s: %s", url, e)
        return None

    def _fetch_token_with_selenium(self) -> Optional[str]:
        """
        Token per Scraping: dat.de Startseite → „Kunden Login“ klicken → Dropdown mit
        DAT-Kundennummer, Benutzer, Passwort ausfüllen → Anmelden → Token aus Page/Storage/Network.
        """
        if not SELENIUM_AVAILABLE:
            return None
        base = self.config.get("base_url", "").rstrip("/")
        if "/myClaim" in base:
            portal_root = base.split("/myClaim")[0] or "https://www.dat.de"
        else:
            portal_root = base
        username = self.config.get("username", "")
        password = self.config.get("password", "")
        customer = self.config.get("customer_number", "") or ""
        if not username or not password:
            return None
        driver = None
        try:
            opts = Options()
            opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--window-size=1920,1080")
            opts.add_argument("--lang=de-DE")
            opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
            if os.environ.get("CHROME_BIN"):
                opts.binary_location = os.environ["CHROME_BIN"]
            driver = webdriver.Chrome(options=opts)
            driver.set_page_load_timeout(45)
            driver.get(portal_root)
            WebDriverWait(driver, 12).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            # Cookie-Banner ausblenden (usercentrics blockiert Klick), ggf. akzeptieren
            try:
                driver.execute_script("var u=document.getElementById('usercentrics-root'); if(u) u.style.display='none';")
            except Exception:
                pass
            try:
                btn = driver.find_element(By.XPATH, "//button[contains(.,'Akzeptieren') or contains(.,'Zustimmen') or contains(.,'Alle')]")
                btn.click()
            except Exception:
                pass
            # „Kunden Login“ öffnen: Button mit Klasse tLogin (öffnet Dropdown; Formular wird evtl. per JS nachgeladen)
            try:
                login_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button.tLogin"))
                )
                driver.execute_script("arguments[0].click();", login_btn)
            except Exception as e:
                logger.debug("Kunden-Login-Button (tLogin) nicht gefunden: %s", e)
                try:
                    login_btn = driver.find_element(By.XPATH, "//button[contains(.,'Kunden Login')]")
                    driver.execute_script("arguments[0].click();", login_btn)
                except Exception as e2:
                    logger.debug("Kunden-Login Fallback: %s", e2)
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    return None
            # Warten auf sichtbares Login-Formular (DAT-Kundennummer, Benutzer, Passwort)
            # Hinweis: Auf dat.de kann das Formular im Headless-Browser nicht erscheinen (nur Such-/Newsletter-Felder).
            import time
            time.sleep(5)
            try:
                WebDriverWait(driver, 12).until(
                    EC.visibility_of_element_located((By.XPATH, "//input[contains(@placeholder,'Benutzer') or contains(@name,'user') or contains(@id,'user') or @type='password']"))
                )
            except Exception:
                # Formular oft nicht im DOM (Headless) – Token dann nur via config/credentials.json (manuell) nutzbar
                logger.debug("Login-Formular (Benutzer/Passwort) nicht sichtbar – evtl. Headless-Einschränkung auf dat.de")
                try:
                    driver.quit()
                except Exception:
                    pass
                return None
            # Felder befüllen: DAT-Kundennummer, Benutzer, Passwort (Labels wie auf dat.de)
            def fill_login_form():
                # DAT-Kundennummer (optional)
                for xpath in [
                    "//label[contains(.,'Kundennummer')]/following-sibling::*//input",
                    "//input[contains(@placeholder,'Kundennummer')]",
                    "//input[contains(@name,'customer') or contains(@id,'customer')]",
                ]:
                    try:
                        inp = driver.find_element(By.XPATH, xpath)
                        if inp.is_displayed() and inp.get_attribute("type") != "password":
                            inp.clear()
                            inp.send_keys(customer)
                            break
                    except Exception:
                        continue
                # Benutzer
                for xpath in [
                    "//label[contains(.,'Benutzer')]/following-sibling::*//input",
                    "//input[contains(@placeholder,'Benutzer')]",
                    "//input[@name='username' or contains(@name,'user')]",
                ]:
                    try:
                        inp = driver.find_element(By.XPATH, xpath)
                        if inp.is_displayed() and inp.get_attribute("type") != "password":
                            inp.clear()
                            inp.send_keys(username)
                            break
                    except Exception:
                        continue
                # Passwort
                pw = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                pw.clear()
                pw.send_keys(password)
                # Anmelden klicken
                sub = driver.find_element(By.XPATH, "//button[contains(.,'Anmelden')] | //input[@value='Anmelden'] | //button[@type='submit']")
                sub.click()
                return True
            try:
                fill_login_form()
            except Exception as e:
                logger.debug("Login-Formular befüllen: %s", e)
                try:
                    driver.quit()
                except Exception:
                    pass
                return None
            # Kurz warten auf Login (Redirect oder Modal schließt)
            time.sleep(3)
            # Token aus Page Source / Storage
            text = driver.page_source or ""
            token = _JWT_RE.search(text)
            if token:
                logger.info("DAT-Token per Selenium aus Page Source")
                return token.group(0)
            for key in ["token", "jwt", "authToken", "dat_token"]:
                try:
                    val = driver.execute_script(f"return window.localStorage.getItem('{key}') || sessionStorage.getItem('{key}');")
                    if val and _JWT_RE.search(val):
                        return _JWT_RE.search(val).group(0)
                except Exception:
                    pass
            # Zu myClaim gehen – Seite sendet oft POST zu json/security/Login mit Token
            driver.get(urljoin(portal_root + "/", "myClaim/"))
            WebDriverWait(driver, 12).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            text2 = driver.page_source or ""
            t2 = _JWT_RE.search(text2)
            if t2:
                return t2.group(0)
            for entry in driver.get_log("performance") or []:
                msg = entry.get("message", "")
                if "json/security/Login" not in msg or "token=" not in msg:
                    continue
                try:
                    m = json.loads(msg).get("message", {})
                    if m.get("method") == "Network.requestWillBeSent":
                        req = (m.get("params") or {}).get("request", {})
                        if "json/security/Login" in (req.get("url") or ""):
                            post = req.get("postData") or ""
                            tok = _JWT_RE.search(post)
                            if tok:
                                logger.info("DAT-Token per Selenium aus Network-Request")
                                return tok.group(0)
                except Exception:
                    continue
        except Exception as e:
            logger.warning("DAT Selenium-Token fehlgeschlagen: %s", e)
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
        return None

    def login(self) -> bool:
        """
        Meldet bei DAT myClaim an.
        - Wenn in der Config ein "token" (JWT) gesetzt ist: POST zu /json/security/Login (HAR ausgewertet).
        - Sonst: Versuch mit Benutzername/Passwort (klassische Form-Pfade).
        """
        if not REQUESTS_AVAILABLE:
            logger.warning("requests nicht installiert – DAT-Login nicht möglich")
            return False
        base = self.config.get("base_url", "").rstrip("/")
        if not base:
            logger.warning("DAT_URL nicht gesetzt")
            return False

        # 1) Login per JWT (myClaim: POST /myClaim/json/security/Login laut HAR)
        token = self.config.get("token") or os.environ.get("DAT_TOKEN")
        if token and isinstance(token, str) and token.strip():
            import time
            login_url = urljoin(base + "/", "json/security/Login")
            params = {"fabrikat": "DAT", "r": str(int(time.time() * 1000))}
            body = {"token": token.strip(), "fabrikat": "DAT", "product": "myClaim"}
            try:
                r = self.session.post(
                    login_url,
                    params=params,
                    data=body,
                    timeout=15,
                    allow_redirects=True,
                    headers={"Content-Type": "application/x-www-form-urlencoded", "Origin": "https://www.dat.de"},
                )
                if r.status_code == 200:
                    # Erfolg: oft Redirect zu inbox oder myClaim-Seite
                    if "login" not in (r.url or "").lower() or "inbox" in (r.url or "").lower():
                        logger.info("DAT-Login per Token erfolgreich (myClaim/json/security/Login)")
                        return True
                logger.debug("DAT Token-Login: %s → %s", r.status_code, r.url)
            except Exception as e:
                logger.warning("DAT Token-Login fehlgeschlagen: %s", e)
            # Token fehlgeschlagen, Fallback auf User/Pass
        else:
            logger.debug("Kein DAT-Token in Config, versuche Token aus User/Passwort zu erzeugen")

        username = self.config.get("username")
        password = self.config.get("password")
        if not username or not password:
            logger.warning("Weder DAT-Token noch DAT_USER/DAT_PASSWORD gesetzt – Login nicht möglich")
            return False

        # 2) Token aus AuthorizationManager/Portal holen (User/Pass → JWT), dann myClaim-Login
        token = self._fetch_token_with_credentials()
        if not token and SELENIUM_AVAILABLE:
            token = self._fetch_token_with_selenium()
        if token:
            import time
            login_url = urljoin(base + "/", "json/security/Login")
            params = {"fabrikat": "DAT", "r": str(int(time.time() * 1000))}
            body = {"token": token, "fabrikat": "DAT", "product": "myClaim"}
            try:
                r = self.session.post(
                    login_url,
                    params=params,
                    data=body,
                    timeout=15,
                    allow_redirects=True,
                    headers={"Content-Type": "application/x-www-form-urlencoded", "Origin": "https://www.dat.de"},
                )
                if r.status_code == 200 and ("login" not in (r.url or "").lower() or "inbox" in (r.url or "").lower()):
                    logger.info("DAT-Login erfolgreich (Token aus User/Passwort erzeugt)")
                    return True
            except Exception as e:
                logger.warning("myClaim-Login mit erzeugtem Token fehlgeschlagen: %s", e)

        # 3) Startseite laden (Cookies). 403 ist OK.
        try:
            r = self.session.get(base, timeout=15)
            if r.status_code not in (200, 403):
                r.raise_for_status()
        except Exception as e:
            logger.warning("DAT Startseite nicht erreichbar: %s", e)
            return False

        # 4) Klassische Login-Pfade (User/Pass direkt an myClaim – oft nicht unterstützt)
        login_paths = ["j_security_check", "/myClaim/j_security_check", "/j_security_check", "login", "/login"]
        login_data = {"j_username": username, "j_password": password, "username": username, "password": password}
        if self.config.get("customer_number"):
            login_data["customerNumber"] = self.config["customer_number"]
            login_data["customer_number"] = self.config["customer_number"]

        for path in login_paths:
            url = urljoin(base + "/", path.lstrip("/"))
            try:
                r = self.session.post(url, data=login_data, timeout=15, allow_redirects=True)
                if r.status_code == 200 and "login" not in (r.url or "").lower():
                    logger.info("DAT-Login erfolgreich (Pfad %s)", path)
                    return True
                if r.status_code == 200:
                    continue
            except Exception as e:
                logger.debug("DAT-Login %s: %s", path, e)
                continue
        logger.warning("DAT-Login konnte nicht bestätigt werden – ggf. Login-URL/Formular anpassen")
        return True  # Trotzdem versuchen, doVinRequest aufzurufen (Session evtl. schon gültig)

    def vin_lookup(self, vin17: str) -> dict:
        """
        Führt VIN-Abfrage über doVinRequest aus.
        vin17: 17-stellige VIN (ohne Leerzeichen).
        Rückgabe: {
            "success": bool,
            "marke": str | None,
            "handelsbezeichnung": str | None,
            "typ_variante_version": str | None,
            "hsn": str | None,
            "tsn": str | None,
            "motor": str | None,
            "kraftstoff": str | None,
            "dat_europa_code": str | None,
            "kba_list": [{"hsn","tsn"}, ...],
            "raw": dict | None,
            "error": str | None
        }
        """
        vin17 = (vin17 or "").strip().upper()
        vin17 = re.sub(r"[\s\-\.]", "", vin17)
        if len(vin17) != 17:
            return {"success": False, "error": "VIN muss 17 Zeichen haben"}

        if not REQUESTS_AVAILABLE:
            return {"success": False, "error": "requests nicht installiert"}

        base = self.config.get("base_url")
        if not base:
            return {"success": False, "error": "DAT_URL nicht konfiguriert"}

        if not self._session:
            if not self.login():
                return {"success": False, "error": "DAT-Login fehlgeschlagen"}

        url = _dispatcher_url(base, "vehicleSelection.modelPanelGroup", "doVinRequest")
        # Verschiedene Payload-Formate ausprobieren (Dispatcher oft JSON oder form-encoded)
        payloads = [
            ({"vin": vin17}, "application/json"),
            ({"VIN": vin17}, "application/json"),
            ({"vinNumber": vin17}, "application/json"),
        ]
        last_error = None
        for payload, content_type in payloads:
            try:
                if content_type == "application/json":
                    r = self.session.post(url, json=payload, timeout=30)
                else:
                    r = self.session.post(url, data=payload, timeout=30)
                if r.status_code != 200:
                    last_error = f"HTTP {r.status_code}"
                    continue
                try:
                    data = r.json()
                except Exception:
                    # Antwort könnte HTML oder anderes Format sein
                    text = (r.text or "")[:500]
                    if "vin" in text.lower() or "vehicle" in text.lower() or "europa" in text.lower():
                        return _parse_dat_response_text(r.text, vin17)
                    last_error = "Antwort ist kein JSON"
                    continue
                result = _parse_dat_response(data, vin17)
                if result.get("success") or result.get("marke") or result.get("dat_europa_code"):
                    return result
                last_error = result.get("error") or "Keine Fahrzeugdaten in Antwort"
            except Exception as e:
                last_error = str(e)
                logger.debug("doVinRequest Versuch %s: %s", payload, e)
                continue

        return {"success": False, "error": last_error or "VIN-Abfrage fehlgeschlagen"}


def _parse_dat_response(data: dict, vin: str) -> dict:
    """Mappt die (vermutete) API-Antwort auf unser Fahrzeuganlage-Format."""
    out = {
        "success": False,
        "marke": None,
        "handelsbezeichnung": None,
        "typ_variante_version": None,
        "hsn": None,
        "tsn": None,
        "motor": None,
        "kraftstoff": None,
        "dat_europa_code": None,
        "kba_list": [],
        "raw": data,
        "error": None,
    }
    if not isinstance(data, dict):
        out["error"] = "Ungültige Antwort"
        return out

    # Verschiedene mögliche Feldnamen (ohne offizielle Doku)
    def get_nested(*keys, default=None):
        for key in keys:
            if isinstance(data, dict) and key in data:
                v = data[key]
                if v is not None and str(v).strip():
                    return str(v).strip()
            if "result" in data and isinstance(data["result"], dict):
                if key in data["result"]:
                    return str(data["result"][key]).strip()
            if "vehicle" in data and isinstance(data["vehicle"], dict):
                if key in data["vehicle"]:
                    return str(data["vehicle"][key]).strip()
        return default

    out["marke"] = get_nested("marke", "make", "manufacturer", "hersteller")
    out["handelsbezeichnung"] = get_nested("handelsbezeichnung", "model", "modell", "typeName", "vehicleType")
    out["typ_variante_version"] = get_nested("typ_variante_version", "type", "variant", "version")
    out["motor"] = get_nested("motor", "engine", "engineDescription")
    out["kraftstoff"] = get_nested("kraftstoff", "fuel", "fuelType")
    out["dat_europa_code"] = get_nested("dat_europa_code", "europaCode", "europa_code", "ecode")

    kba_raw = get_nested("kba", "kbaList", "kba_list", "hsnTsn")
    if kba_raw:
        pairs = _parse_kba_list(kba_raw)
        out["kba_list"] = [{"hsn": h, "tsn": t} for h, t in pairs]
        if pairs:
            out["hsn"] = pairs[0][0]
            out["tsn"] = pairs[0][1]

    if not out["hsn"] and "hsn" in data:
        out["hsn"] = str(data.get("hsn", "")).strip() or None
    if not out["tsn"] and "tsn" in data:
        out["tsn"] = str(data.get("tsn", "")).strip() or None

    if any([out["marke"], out["handelsbezeichnung"], out["dat_europa_code"], out["hsn"]]):
        out["success"] = True
    else:
        out["error"] = "Keine Fahrzeugdaten in DAT-Antwort erkannt (Payload-Struktur ggf. anpassen)"
    return out


def _parse_dat_response_text(text: str, vin: str) -> dict:
    """Fallback: Versucht aus Text/HTML grob KBA und Bezeichnung zu extrahieren."""
    out = {
        "success": False,
        "marke": None,
        "handelsbezeichnung": None,
        "typ_variante_version": None,
        "hsn": None,
        "tsn": None,
        "motor": None,
        "kraftstoff": None,
        "dat_europa_code": None,
        "kba_list": [],
        "raw": None,
        "error": None,
    }
    # KBA-Muster: 1889/AFH oder 2525/AAV
    kba_m = re.findall(r"(\d{4})/([A-Z0-9]{2,3})", text)
    if kba_m:
        out["kba_list"] = [{"hsn": h, "tsn": t} for h, t in kba_m]
        out["hsn"] = kba_m[0][0]
        out["tsn"] = kba_m[0][1]
    # Europa-Code grob
    ec = re.search(r"(\d{2}\s+\d{3}\s+\d{3}\s+\d{4}\s+\w+\s+\d+)", text)
    if ec:
        out["dat_europa_code"] = ec.group(1).strip()
    if out["hsn"] or out["dat_europa_code"]:
        out["success"] = True
    return out
