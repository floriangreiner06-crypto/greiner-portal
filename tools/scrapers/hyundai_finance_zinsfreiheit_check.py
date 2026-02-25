#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüft Hyundai-Finance-Portal und exportierte CSV auf Angaben zur Zinsfreiheit.
Nutzt denselben Flow wie hyundai_finance_scraper.py (Login → EKF → Bestandsliste).
"""

import os
import sys
import time
import glob
import csv
from datetime import datetime
from pathlib import Path

# Scraper-Pfad
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

PORTAL_URL = "https://fiona.hyundaifinance.eu/#/dealer-portal"
USERNAME = "Christian.aichinger@auto-greiner.de"
PASSWORD = "Hyundaikona2020!"
STANDORT_NAME = "Auto Greiner"
SCREENSHOTS_DIR = "/tmp/hyundai_zinsfreiheit_check"
WAIT_MEDIUM = 10
WAIT_SHORT = 5
WAIT_DOWNLOAD = 25


def load_credentials():
    """Optional: Credentials aus config/credentials.json"""
    try:
        creds_path = Path("/opt/greiner-portal/config/credentials.json")
        if creds_path.exists():
            import json
            with open(creds_path) as f:
                data = json.load(f)
            for key in ("external_systems", "hyundai_finance", "hyundai"):
                if isinstance(data.get("external_systems", {}).get("hyundai_finance"), dict):
                    c = data["external_systems"]["hyundai_finance"]
                    return c.get("username") or USERNAME, c.get("password") or PASSWORD
            if isinstance(data.get("hyundai"), dict):
                c = data["hyundai"]
                return c.get("username") or USERNAME, c.get("password") or PASSWORD
    except Exception:
        pass
    return USERNAME, PASSWORD


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--lang=de-DE")
    prefs = {
        "download.default_directory": SCREENSHOTS_DIR,
        "download.prompt_for_download": False,
        "safebrowsing.enabled": False,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)
    return driver


def main():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    out_file = Path(SCREENSHOTS_DIR) / "zinsfreiheit_check_result.txt"
    lines = []

    def log(msg):
        print(msg)
        lines.append(msg)

    log("=" * 60)
    log("Hyundai Finance – Prüfung auf Zinsfreiheit im Portal / CSV")
    log("=" * 60)
    log(f"Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    username, password = load_credentials()
    driver = None

    try:
        driver = setup_driver()
        wait = WebDriverWait(driver, WAIT_MEDIUM)

        # Login
        log("Login...")
        driver.get(PORTAL_URL)
        time.sleep(WAIT_SHORT)
        driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(username)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(WAIT_SHORT)
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(WAIT_MEDIUM)

        # Standort
        standort_card = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//div[contains(text(), '{STANDORT_NAME}')]"))
        )
        standort_card.click()
        time.sleep(WAIT_SHORT)
        select_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Standort auswählen')]"))
        )
        select_btn.click()
        time.sleep(WAIT_MEDIUM)

        # EKF Portal
        ekf_tile = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(., 'Einkaufsfinanzierung')]"))
        )
        ekf_tile.click()
        time.sleep(WAIT_MEDIUM)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(WAIT_SHORT)

        # Bestandsliste
        log("Lade Bestandsliste...")
        driver.get("https://ekf.hyundaifinance.eu/account/stocklist/search")
        time.sleep(WAIT_MEDIUM)

        # 1) Sichtbaren Text der Seite prüfen
        page_text = driver.find_element(By.TAG_NAME, "body").text
        page_lower = page_text.lower()
        log("\n--- Prüfung: Kommt 'Zinsfreiheit' / 'Zinsfrei' im Portal vor? ---")
        if "zinsfreiheit" in page_lower or "zinsfrei" in page_lower or "zins-frei" in page_lower:
            log("JA – Im sichtbaren Text der Bestandsliste kommt 'Zinsfreiheit' bzw. 'zinsfrei' vor.")
            # Kontextzeilen
            for line in page_text.splitlines():
                if "zinsfrei" in line.lower() or "zinsbeginn" in line.lower():
                    log(f"  Zeile: {line.strip()[:120]}")
        else:
            log("NEIN – Im sichtbaren Text der Bestandsliste erscheint kein 'Zinsfreiheit' / 'zinsfrei'.")

        # Tabellen-Header (mat-header-cell, th, etc.)
        log("\n--- Tabellen-Header auf der Seite (falls vorhanden) ---")
        headers = []
        for sel in ["mat-header-cell", "th", "[role='columnheader']"]:
            try:
                els = driver.find_elements(By.CSS_SELECTOR, sel)
                for el in els[:50]:
                    t = (el.text or "").strip()
                    if t and t not in headers:
                        headers.append(t)
            except Exception:
                pass
        if headers:
            log("Gefundene Spaltenüberschriften: " + " | ".join(headers))
            if any("zins" in h.lower() or "zinsfrei" in h.lower() for h in headers):
                log("  → Es gibt Spalten mit Zins-/Zinsfreiheit-Bezug.")
        else:
            log("Keine Tabellen-Header gefunden (evtl. Angular-Material oder dynamisch).")

        # 2) CSV-Download auslösen und Spalten prüfen
        log("\n--- CSV-Download auslösen und Spalten prüfen ---")
        try:
            download_btn = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(@class, 'mat-icon-button')]//mat-icon[text()='download_file']/..",
                ))
            )
            download_btn.click()
            time.sleep(2)
            try:
                popup_btn = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Download')]"))
                )
                popup_btn.click()
            except TimeoutException:
                pass
            # Warten auf CSV
            start = time.time()
            csv_path = None
            initial = set(glob.glob(os.path.join(SCREENSHOTS_DIR, "*.csv")))
            while time.time() - start < WAIT_DOWNLOAD:
                current = set(glob.glob(os.path.join(SCREENSHOTS_DIR, "*.csv")))
                new = current - initial
                if new:
                    csv_path = list(new)[0]
                    break
                time.sleep(1)
            if csv_path:
                time.sleep(1)
                with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
                    sample = f.read(2048)
                delim = ";" if sample.count(";") > sample.count(",") else ","
                first_line = sample.splitlines()[0] if sample else ""
                col_names = [c.strip().strip('"') for c in first_line.split(delim)]
                log(f"CSV-Spalten ({len(col_names)}): {col_names}")
                zins_cols = [c for c in col_names if "zins" in c.lower() or "zinsfrei" in c.lower() or "interest" in c.lower()]
                if zins_cols:
                    log(f"Spalten mit Zins-/Zinsfreiheit-Bezug: {zins_cols}")
                else:
                    log("Keine Spalte mit 'Zins' oder 'Zinsfreiheit' im Namen in der CSV.")
            else:
                log("CSV-Download nicht abgeschlossen innerhalb der Wartezeit.")
        except Exception as e:
            log(f"Download/CSV-Prüfung fehlgeschlagen: {e}")

    except Exception as e:
        log(f"Fehler: {e}")
        import traceback
        lines.append(traceback.format_exc())
    finally:
        if driver:
            driver.quit()

    # Ergebnis in Datei
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log(f"\nErgebnis gespeichert: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
