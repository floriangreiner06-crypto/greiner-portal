#!/usr/bin/env python3
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

PORTAL_URL = "https://fiona.hyundaifinance.eu/#/dealer-portal"
USERNAME = "Christian.aichinger@auto-greiner.de"
PASSWORD = "Hyundaikona2020!"

chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)

try:
    # Login
    driver.get(PORTAL_URL)
    time.sleep(5)
    
    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(USERNAME)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(5)
    
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(10)
    
    # Standort
    driver.find_element(By.XPATH, "//div[contains(text(), 'Auto Greiner')]").click()
    time.sleep(3)
    driver.find_element(By.XPATH, "//button[contains(., 'Standort auswählen')]").click()
    time.sleep(10)
    
    # EKF Portal
    driver.find_element(By.XPATH, "//div[contains(., 'Einkaufsfinanzierung')]").click()
    time.sleep(10)
    
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
    
    # Bestandsliste
    driver.get("https://ekf.hyundaifinance.eu/account/stocklist/search")
    time.sleep(10)
    
    # Speichere HTML
    html = driver.page_source
    with open('/tmp/hyundai_screenshots/bestandsliste_complete.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ HTML gespeichert")
    
    # Suche nach Download-relevanten Elementen
    print("\n🔍 Suche Download-Elemente...")
    
    # Alle mat-icons
    icons = driver.find_elements(By.TAG_NAME, "mat-icon")
    print(f"\nGefundene mat-icons: {len(icons)}")
    for i, icon in enumerate(icons[:20]):
        print(f"  {i+1}. Text: '{icon.text}' | Class: {icon.get_attribute('class')}")
    
    # Alle Buttons
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"\nGefundene buttons: {len(buttons)}")
    for i, btn in enumerate(buttons[:20]):
        text = btn.text.strip()
        if text or 'download' in btn.get_attribute('class').lower():
            print(f"  {i+1}. Text: '{text}' | Class: {btn.get_attribute('class')}")
    
    driver.save_screenshot('/tmp/hyundai_screenshots/debug_bestandsliste.png')
    
finally:
    driver.quit()
