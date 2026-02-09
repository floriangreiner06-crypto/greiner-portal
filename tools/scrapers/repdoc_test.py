#!/usr/bin/env python3
"""Schneller RepDoc Test - Login + eine Suche"""

import time
import logging
from repdoc_scraper import RepDocScraper

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

scraper = RepDocScraper()

print("=== RepDoc Test ===")
print(f"Username: {scraper.username}")

# Login testen
print("\n1. Login testen...")
login_ok = scraper._do_login()
print(f"Login: {'✅ Erfolgreich' if login_ok else '❌ Fehlgeschlagen'}")

if login_ok:
    # Eine Suche testen
    print("\n2. Suche testen (1109AL)...")
    start = time.time()
    result = scraper.search("1109AL")
    elapsed = time.time() - start
    
    print(f"Zeit: {elapsed:.1f}s")
    print(f"Erfolg: {result.get('success')}")
    print(f"Anzahl Ergebnisse: {result.get('anzahl', 0)}")
    
    if result.get('ergebnisse'):
        print("\nErgebnisse:")
        for i, r in enumerate(result['ergebnisse'][:3], 1):
            print(f"  {i}. {r.get('teilenummer')}: {r.get('beschreibung', '')[:50]}")
            print(f"     Preis: {r.get('preis')}€, Verfügbar: {r.get('verfuegbar')}")
    elif result.get('error'):
        print(f"Fehler: {result['error']}")
    
    # HTML-Struktur analysieren (für Debugging)
    if not result.get('ergebnisse'):
        print("\n⚠️ Keine Ergebnisse - HTML-Struktur analysieren...")
        driver = scraper._ensure_driver()
        html = driver.page_source[:2000]  # Erste 2000 Zeichen
        print(f"HTML-Ausschnitt: {html[:500]}...")

RepDocScraper.force_close()
print("\n=== Test abgeschlossen ===")
