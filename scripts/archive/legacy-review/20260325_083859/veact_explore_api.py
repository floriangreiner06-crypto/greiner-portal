#!/usr/bin/env python3
"""
Veact: Nach Login Netzwerk-Logs und Page-Source nach API-Endpunkten durchsuchen.
Nutzt Chrome Performance-Log (Network-Requests) + Quelltext-Scan.
Zugangsdaten: VEACT_EMAIL, VEACT_PASSWORD (Umgebungsvariablen).
"""

import json
import os
import re
import sys
import time
from urllib.parse import quote

sys.path.insert(0, "/opt/greiner-portal")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("Selenium nicht verfügbar.")
    sys.exit(1)

# Nach Login auf asmc.veact.net (Kampagnen Manager) landen
REDIRECT_URI = "https://asmc.veact.net/organisation/646c5ffae49ebe10c9e40ef0/cm/"
LOGIN_URL = "https://accounts.veact.net/v1/oauth2/auth?client_id=asmc.4385903485&redirect_uri=" + quote(REDIRECT_URI, safe="")
OUT_DIR = "/opt/greiner-portal/docs/workstreams/marketing"


def extract_urls_from_performance_log(driver):
    """Extrahiert alle Request-URLs aus Chrome Performance-Log."""
    urls = set()
    try:
        for entry in driver.get_log("performance"):
            try:
                msg = json.loads(entry["message"])["message"]
                method = msg.get("method", "")
                params = msg.get("params", {})
                if method == "Network.requestWillBeSent":
                    req = params.get("request", {})
                    u = req.get("url", "").strip()
                    if u:
                        urls.add(u)
                elif method == "Network.responseReceived":
                    res = params.get("response", {})
                    u = res.get("url", "").strip()
                    if u:
                        urls.add(u)
            except (KeyError, json.JSONDecodeError):
                continue
    except Exception as e:
        print("  Performance-Log Fehler:", e)
    return urls


def is_api_like(url):
    """Filtert URLs die nach API-Endpunkten aussehen."""
    u = url.lower()
    if any(x in u for x in ["/api/", "/v1/", "/v2/", "/graphql", "/rest/", "api.veact", "api.veact.net"]):
        return True
    if "veact.net" in u and any(x in u for x in ["/organisations/", "/organisation/", "/campaigns/", "/campaign/", "/users/", "/auth/"]):
        return True
    # XHR/fetch oft für APIs
    if "veact" in u and not u.endswith((".js", ".css", ".png", ".jpg", ".ico", ".woff2", ".map")):
        if "static" not in u and "chunk" not in u and "runtime" not in u:
            return True
    return False


def scan_page_source_for_api(html):
    """Sucht im HTML/JS nach API-Base-URLs und Endpoint-Mustern."""
    found = set()
    # Base URLs, env, config
    for pattern in [
        r'["\']https?://[^"\']*api[^"\']*["\']',
        r'["\']https?://[^"\']*veact\.net[^"\']*["\']',
        r'baseURL\s*[:=]\s*["\']([^"\']+)["\']',
        r'apiUrl\s*[:=]\s*["\']([^"\']+)["\']',
        r'API_URL\s*[:=]\s*["\']([^"\']+)["\']',
        r'["\']/(api|v1|v2|graphql)[^"\']*["\']',
        r'fetch\s*\(\s*["\']([^"\']+)["\']',
        r'axios\.(get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']',
        r'\.get\s*\(\s*["\']([^"\']+)["\']',
        r'url:\s*["\']([^"\']+)["\']',
        r'"/v\d+/[^"]*"',
        r'"/api/[^"]*"',
    ]:
        for m in re.finditer(pattern, html, re.IGNORECASE):
            g = (m.group(1) if m.lastindex and m.lastindex >= 1 else m.group(0)) or ""
            g = g.strip('"\' ')
            if len(g) < 4:
                continue
            if "veact" in g.lower() or g.startswith("/api") or g.startswith("/v"):
                found.add(g)
    return found


def main():
    email = os.environ.get("VEACT_EMAIL", "").strip()
    password = os.environ.get("VEACT_PASSWORD", "").strip()
    if not email or not password:
        print("Setze VEACT_EMAIL und VEACT_PASSWORD.")
        sys.exit(2)

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    # Performance-Log für Network-Requests
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})

    driver = None
    all_urls = set()
    try:
        driver = webdriver.Chrome(options=opts)
        driver.set_page_load_timeout(90)

        print("Login...")
        driver.get(LOGIN_URL)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[type='password']"))
        )
        time.sleep(0.3)
        email_el = driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[name='email']")
        pw_el = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        email_el.clear()
        email_el.send_keys(email)
        pw_el.clear()
        pw_el.send_keys(password)
        btn = driver.find_elements(By.CSS_SELECTOR, "button[type='submit']") or [
            b for b in driver.find_elements(By.TAG_NAME, "button") if "log" in (b.text or "").lower()
        ]
        if btn:
            btn[0].click()
        else:
            pw_el.submit()

        # Warte auf Redirect (asmc.veact.net oder callback)
        for _ in range(35):
            url = driver.current_url or ""
            if "asmc.veact.net" in url and "oauth/callback" not in url:
                break
            if "accounts.veact.net" not in url:
                time.sleep(2)
                break
            time.sleep(1)
        print("URL nach Login:", driver.current_url)

        # Falls asmc auf user_mgt/login weiterleitet: dort erneut einloggen (gleiche Zugangsdaten)
        if "user_mgt/login" in (driver.current_url or ""):
            print("asmc zeigt user_mgt/login – zweiter Login auf asmc...")
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[type='text']"))
                )
                time.sleep(0.5)
                email_el = driver.find_elements(By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[type='text']")
                pw_el = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
                if email_el and pw_el:
                    email_el[0].clear()
                    email_el[0].send_keys(email)
                    pw_el[0].clear()
                    pw_el[0].send_keys(password)
                    btn = driver.find_elements(By.CSS_SELECTOR, "button[type='submit']") or [b for b in driver.find_elements(By.TAG_NAME, "button") if "log" in (b.text or "").lower() or "submit" in (b.text or "").lower()]
                    if btn:
                        btn[0].click()
                    else:
                        pw_el[0].submit()
                    time.sleep(8)
                    print("URL nach user_mgt Login:", driver.current_url)
            except Exception as e:
                print("user_mgt Login:", e)

        # App: Seite laden und scrollen für weitere API-Requests
        if "asmc.veact.net" in (driver.current_url or "") and "login" not in (driver.current_url or ""):
            time.sleep(4)
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
            except Exception:
                pass
        else:
            try:
                driver.get("https://asmc.veact.net/organisation/646c5ffae49ebe10c9e40ef0/cm/")
                time.sleep(6)
            except Exception as e:
                print("asmc Load:", e)

        # 1) Performance-Log auslesen
        print("\n--- Network-Requests (Performance-Log) ---")
        perf_urls = extract_urls_from_performance_log(driver)
        all_urls.update(perf_urls)
        api_from_perf = sorted(u for u in perf_urls if is_api_like(u))
        for u in api_from_perf:
            print(u)
        if not api_from_perf:
            print("(Keine API-ähnlichen URLs im Log – App-Seite evtl. nicht geladen)")

        # 2) Page Source speichern und nach API-Mustern durchsuchen
        html = driver.page_source or ""
        ps_file = os.path.join(OUT_DIR, "veact_page_source.html")
        with open(ps_file, "w") as f:
            f.write(html)
        print(f"Page-Source ({len(html)} Zeichen) → {ps_file}")

        print("\n--- Page-Source Scan (API-Muster) ---")
        from_source = scan_page_source_for_api(html)
        for u in sorted(from_source):
            if len(u) < 200:
                print(u)
                all_urls.add(u)

        # Alle gesammelten API-ähnlichen URLs dedupliziert ausgeben + speichern
        api_urls = sorted(set(u for u in all_urls if is_api_like(u)))
        out_file = os.path.join(OUT_DIR, "veact_api_endpoints.txt")
        with open(out_file, "w") as f:
            f.write("# Veact – erkannte API-ähnliche URLs (Login + App-Seite)\n")
            f.write("# Quelle: Performance-Log + Page-Source Scan\n\n")
            for u in api_urls:
                f.write(u + "\n")
        print(f"\n--- Gesamt {len(api_urls)} API-URLs → {out_file} ---")

        # Vollständige Request-Liste (alle eindeutigen URLs von veact)
        veact_all = sorted(set(u for u in all_urls if "veact" in u.lower() and "accounts.veact.net/v1/oauth2" not in u))
        out_all = os.path.join(OUT_DIR, "veact_all_requests.txt")
        with open(out_all, "w") as f:
            for u in veact_all:
                f.write(u + "\n")
        print(f"Alle Veact-Requests ({len(veact_all)}) → {out_all}")

    except Exception as e:
        print("Fehler:", e)
        raise
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
