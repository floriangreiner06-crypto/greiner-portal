#!/usr/bin/env python3
"""
Einmalige Veact-Account-Erkundung per Selenium (Chrome).
Zugangsdaten NUR über Umgebungsvariablen: VEACT_EMAIL, VEACT_PASSWORD.
Aufruf: VEACT_EMAIL="..." VEACT_PASSWORD="..." python3 scripts/veact_explore_login.py
"""

import os
import sys
import time

sys.path.insert(0, "/opt/greiner-portal")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("Selenium nicht verfügbar. pip install selenium")
    sys.exit(1)

LOGIN_URL = "https://accounts.veact.net/v1/oauth2/auth?client_id=asmc.4385903485&redirect_uri=https://app.veact.net/organisation/646c5ffae49ebe10c9e40ef0/cm/campaign/692104c8ce852d663e422c83/review"


def main():
    email = os.environ.get("VEACT_EMAIL", "").strip()
    password = os.environ.get("VEACT_PASSWORD", "").strip()
    if not email or not password:
        print("Setze VEACT_EMAIL und VEACT_PASSWORD (Umgebungsvariablen).")
        sys.exit(2)

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")

    driver = None
    try:
        driver = webdriver.Chrome(options=opts)
        driver.set_page_load_timeout(60)

        print("Öffne Veact Login...")
        driver.get(LOGIN_URL)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email'], #email"))
        )
        time.sleep(0.5)

        # Email/Password-Felder (typische Selektoren)
        email_sel = "input[type='email'], input[name='email'], input[placeholder*='mail' i]"
        pw_sel = "input[type='password'], input[name='password']"
        email_el = driver.find_element(By.CSS_SELECTOR, email_sel)
        pw_el = driver.find_element(By.CSS_SELECTOR, pw_sel)
        email_el.clear()
        email_el.send_keys(email)
        pw_el.clear()
        pw_el.send_keys(password)

        # Submit (Button "Log in" oder Formular)
        btn = None
        for sel in ["button[type='submit']", "input[type='submit']"]:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            if els:
                btn = els[0]
                break
        if not btn:
            for b in driver.find_elements(By.TAG_NAME, "button"):
                if "log" in (b.text or "").lower():
                    btn = b
                    break
        if btn:
            btn.click()
        else:
            pw_el.submit()

        print("Warte auf Weiterleitung nach Login...")
        WebDriverWait(driver, 20).until(lambda d: "accounts.veact.net" not in (d.current_url or "") or "app.veact" in (d.current_url or ""))
        time.sleep(2)

        url = driver.current_url
        title = driver.title
        print("\n--- Nach Login ---")
        print("URL:", url)
        print("Titel:", title)

        # Kurz erkunden: Links/Überschriften
        try:
            links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
            seen = set()
            for a in links[:40]:
                href = (a.get_attribute("href") or "").strip()
                text = (a.text or "").strip()[:60]
                if href and href not in seen:
                    seen.add(href)
                    print(f"  Link: {text or '(leer)'} -> {href[:80]}")
        except Exception as e:
            print("  Links:", e)

        try:
            headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3")
            if headings:
                print("\nÜberschriften:", [h.text.strip() for h in headings if h.text.strip()][:15])
        except Exception:
            pass

        # Screenshot für Doku (optional)
        out = "/opt/greiner-portal/docs/workstreams/marketing/veact_nach_login.png"
        try:
            driver.save_screenshot(out)
            print("\nScreenshot:", out)
        except Exception as e:
            print("Screenshot fehlgeschlagen:", e)

    except Exception as e:
        print("Fehler:", e)
        if driver:
            try:
                driver.save_screenshot("/opt/greiner-portal/docs/workstreams/marketing/veact_fehler.png")
                print("Fehler-Screenshot: docs/workstreams/marketing/veact_fehler.png")
            except Exception:
                pass
        raise
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
