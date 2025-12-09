#!/usr/bin/env python3
"""
Debug: Suchergebnis-HTML speichern und analysieren
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

KUNDENNUMMER = "1003941"
PASSWORT = "AO443494"
BASE_URL = "https://b2b.schaeferbarthold.com"

chrome_options = Options()
chrome_options.binary_location = '/usr/bin/google-chrome'
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(options=chrome_options)

try:
    # Login
    print("🔐 Login...")
    driver.get(BASE_URL)
    time.sleep(3)
    
    if 'auth' in driver.current_url:
        driver.find_element(By.ID, "username").send_keys(KUNDENNUMMER)
        driver.find_element(By.ID, "password").send_keys(PASSWORT)
        driver.find_element(By.ID, "kc-login").click()
        time.sleep(5)
    
    print("✅ Eingeloggt!")
    
    # Suche
    TEIL = "9837096880"
    print(f"\n🔍 Suche: {TEIL}")
    
    search_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input.MuiInputBase-input"))
    )
    search_input.clear()
    search_input.send_keys(TEIL)
    time.sleep(0.5)
    search_input.send_keys(Keys.RETURN)
    
    # Länger warten für Suchergebnisse
    time.sleep(6)
    
    # Screenshot
    driver.save_screenshot('/opt/greiner-portal/logs/sb_debug_search.png')
    
    # HTML speichern
    with open('/opt/greiner-portal/logs/sb_debug_search.html', 'w') as f:
        f.write(driver.page_source)
    
    print("📁 HTML gespeichert: logs/sb_debug_search.html")
    print("📸 Screenshot: logs/sb_debug_search.png")
    
    # Analyse: Suchergebnis-Container finden
    print("\n📋 ANALYSE:")
    
    # Suche nach Suchergebnis-Containern
    containers = driver.find_elements(By.CSS_SELECTOR, "[class*='result'], [class*='Result'], [class*='search'], [class*='Search']")
    print(f"   Container mit 'result/search': {len(containers)}")
    
    # Suche nach Tabellen
    tables = driver.find_elements(By.TAG_NAME, "table")
    print(f"   Tabellen: {len(tables)}")
    
    # Suche nach Listen
    lists = driver.find_elements(By.CSS_SELECTOR, "ul, ol")
    print(f"   Listen: {len(lists)}")
    
    # URL prüfen
    print(f"\n   URL: {driver.current_url}")
    
    # Hat sich die URL geändert nach Suche?
    if TEIL in driver.current_url:
        print("   ✅ Teilenummer in URL!")
    else:
        print("   ⚠️ Teilenummer NICHT in URL - evtl. SPA ohne URL-Update")

finally:
    driver.quit()

# Jetzt HTML analysieren
print("\n" + "=" * 70)
print("📋 HTML-ANALYSE:")

import re

with open('/opt/greiner-portal/logs/sb_debug_search.html', 'r') as f:
    html = f.read()

# Suche nach dem gesuchten Teil im HTML
teil_matches = list(re.finditer(r'9837096880|98.?37.?09.?68.?80', html, re.IGNORECASE))
print(f"\n   Teilenummer im HTML gefunden: {len(teil_matches)} mal")

for i, match in enumerate(teil_matches[:5]):
    start = max(0, match.start() - 50)
    end = min(len(html), match.end() + 100)
    context = html[start:end].replace('\n', ' ')
    print(f"\n   Match {i+1}: ...{context}...")

# Suche nach Preis-Mustern in der Nähe der Teilenummer
print("\n\n   PREISE IN DER NÄHE DER TEILENUMMER:")
for match in teil_matches[:3]:
    # Suche Preise 200 Zeichen nach dem Match
    after = html[match.end():match.end()+500]
    prices = re.findall(r'([\d]+[,.][\d]{2})\s*[€&]', after)
    if prices:
        print(f"   Nach Match: {prices[:3]}")
