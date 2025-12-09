#!/usr/bin/env python3
import os, sys, time, json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

SCREENSHOTS_DIR = "/tmp/hyundai_tilgungen"
RESULTS_FILE = "/tmp/hyundai_tilgungen/results.json"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

opts = Options()
opts.add_argument('--headless=new')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--window-size=1920,1080')
driver = webdriver.Chrome(options=opts)
wait = WebDriverWait(driver, 15)
results = {"pages": [], "screenshots": []}

def screenshot(name):
    fn = f"{len(results['screenshots']):02d}_{name}.png"
    driver.save_screenshot(os.path.join(SCREENSHOTS_DIR, fn))
    results['screenshots'].append(fn)
    print(f"   Screenshot: {fn}")

def get_tables():
    tables = []
    for t in driver.find_elements(By.TAG_NAME, "table"):
        headers = [h.text.strip() for h in t.find_elements(By.TAG_NAME, "th") if h.text.strip()]
        rows = [[td.text.strip() for td in tr.find_elements(By.TAG_NAME, "td")] 
                for tr in t.find_elements(By.TAG_NAME, "tr")[1:8]]
        rows = [r for r in rows if any(r)]
        if headers or rows:
            tables.append({"headers": headers, "rows": rows})
    return tables

try:
    # LOGIN
    print("\n=== LOGIN ===")
    driver.get("https://fiona.hyundaifinance.eu/#/dealer-portal")
    time.sleep(5)
    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys("Christian.aichinger@auto-greiner.de")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(3)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys("Hyundaikona2020!")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(5)
    print("   OK")
    
    # STANDORT
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Auto Greiner')]"))).click()
        time.sleep(2)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Standort')]"))).click()
        time.sleep(5)
    except: pass
    
    # EKF
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Einkaufsfinanzierung')]"))).click()
        time.sleep(5)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(3)
    except:
        driver.get("https://ekf.hyundaifinance.eu/account/home")
        time.sleep(5)
    
    # TILGUNGEN
    print("\n=== TILGUNGEN ===")
    driver.get("https://ekf.hyundaifinance.eu/account/installment")
    time.sleep(5)
    screenshot("tilgungen")
    tables = get_tables()
    body = driver.find_element(By.TAG_NAME, "body").text
    results['pages'].append({"name": "Tilgungen", "url": driver.current_url, "tables": tables, "body": body[:2000]})
    print(f"   URL: {driver.current_url}")
    print(f"   Tabellen: {len(tables)}")
    for t in tables:
        print(f"      Headers: {t['headers']}")
        for r in t['rows'][:3]:
            print(f"         {r[:6]}")
    
    # SENDUNGSVERFOLGUNG
    print("\n=== SENDUNGSVERFOLGUNG ===")
    driver.get("https://ekf.hyundaifinance.eu/account/shipment")
    time.sleep(5)
    screenshot("sendung")
    tables = get_tables()
    body = driver.find_element(By.TAG_NAME, "body").text
    results['pages'].append({"name": "Sendung", "url": driver.current_url, "tables": tables, "body": body[:2000]})
    print(f"   Tabellen: {len(tables)}")
    for t in tables:
        print(f"      Headers: {t['headers']}")
    
    # ERINNERUNGEN
    print("\n=== ERINNERUNGEN ===")
    driver.get("https://ekf.hyundaifinance.eu/account/reminder")
    time.sleep(5)
    screenshot("erinnerungen")
    tables = get_tables()
    body = driver.find_element(By.TAG_NAME, "body").text
    results['pages'].append({"name": "Erinnerungen", "url": driver.current_url, "tables": tables, "body": body[:2000]})
    print(f"   Tabellen: {len(tables)}")
    for t in tables:
        print(f"      Headers: {t['headers']}")
        for r in t['rows'][:5]:
            print(f"         {r[:4]}")
    
    # NEUFINANZIERUNG
    print("\n=== NEUFINANZIERUNG ===")
    driver.get("https://ekf.hyundaifinance.eu/account/new-loan")
    time.sleep(5)
    screenshot("neufinanzierung")
    body = driver.find_element(By.TAG_NAME, "body").text
    results['pages'].append({"name": "Neufinanzierung", "url": driver.current_url, "body": body[:2000]})
    print(f"   Body preview: {body[:200]}")
    
    # FAHRZEUG DETAIL
    print("\n=== FAHRZEUG DETAIL ===")
    driver.get("https://ekf.hyundaifinance.eu/account/stocklist/search")
    time.sleep(5)
    try:
        row = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "table tbody tr:first-child")))
        row.click()
        time.sleep(3)
        screenshot("fahrzeug_detail")
        body = driver.find_element(By.TAG_NAME, "body").text
        results['pages'].append({"name": "Detail", "url": driver.current_url, "body": body[:3000]})
        print(f"   URL: {driver.current_url}")
        # Zeige Zeilen mit Geld/Prozent
        for line in body.split('\n'):
            if any(x in line for x in ['€', '%', 'EUR', 'Zins', 'Saldo', 'Betrag', 'Finanz']):
                print(f"   {line.strip()[:70]}")
    except Exception as e:
        print(f"   Fehler: {e}")
    
    # SPEICHERN
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== FERTIG ===")
    print(f"Screenshots: {SCREENSHOTS_DIR}")
    print(f"JSON: {RESULTS_FILE}")
    
finally:
    driver.quit()
