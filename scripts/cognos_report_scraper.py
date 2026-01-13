#!/usr/bin/env python3
"""
IBM Cognos Report Scraper
Scraped BWA-Reports direkt aus Cognos Portal und extrahiert Filter-Logik

Erstellt: TAG 182
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse, parse_qs

# Cognos Konfiguration
COGNOS_BASE_URL = "http://10.80.80.10:9300"
COGNOS_BI_URL = f"{COGNOS_BASE_URL}/bi"
COGNOS_USER = "Greiner"
COGNOS_PASS = "Hawaii#22"

# Session für Authentifizierung
session = requests.Session()
session.auth = (COGNOS_USER, COGNOS_PASS)
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})


def find_bwa_reports_in_portal():
    """
    Findet BWA-Reports im Cognos Portal durch HTML-Scraping
    """
    print("=== BWA-REPORTS IM PORTAL FINDEN ===\n")
    
    try:
        # Lade Hauptseite
        response = session.get(COGNOS_BI_URL, timeout=10)
        if response.status_code != 200:
            print(f"❌ Fehler beim Laden der Hauptseite: {response.status_code}")
            return []
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Suche nach Links zu Reports
        bwa_reports = []
        
        # Suche nach Links mit BWA-relevanten Begriffen
        bwa_keywords = ['bwa', 'guv', 'betriebswirtschaft', 'ergebnis', 'kosten', 'umsatz']
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            link_text = link.get_text(strip=True).lower()
            
            # Prüfe ob BWA-relevant
            if any(kw in link_text for kw in bwa_keywords) or any(kw in href.lower() for kw in bwa_keywords):
                full_url = urljoin(COGNOS_BI_URL, href)
                bwa_reports.append({
                    'name': link.get_text(strip=True),
                    'url': full_url,
                    'href': href
                })
                print(f"✅ Gefunden: {link.get_text(strip=True)}")
                print(f"   URL: {full_url}")
        
        # Suche nach JavaScript mit Report-URLs
        for script in soup.find_all('script'):
            if script.string:
                # Suche nach Report-URLs in JavaScript
                report_urls = re.findall(r'["\']([^"\']*(?:report|bwa|guv)[^"\']*)["\']', script.string, re.I)
                for url in report_urls:
                    if url not in [r['href'] for r in bwa_reports]:
                        full_url = urljoin(COGNOS_BI_URL, url)
                        bwa_reports.append({
                            'name': 'Report (aus JavaScript)',
                            'url': full_url,
                            'href': url
                        })
                        print(f"✅ Gefunden (JS): {url}")
        
        return bwa_reports
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return []


def scrape_report_page(report_url: str):
    """
    Scraped eine Report-Seite und extrahiert Filter-Logik
    """
    print(f"\n=== REPORT SCRAPEN ===\n")
    print(f"URL: {report_url}\n")
    
    try:
        response = session.get(report_url, timeout=10)
        if response.status_code != 200:
            print(f"❌ Fehler: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Speichere HTML für Analyse
        html_file = f"/tmp/cognos_report_{hash(report_url)}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"✅ HTML gespeichert: {html_file}\n")
        
        # Suche nach Filter-Elementen
        print("=== FILTER-ELEMENTE ===")
        filters = {}
        
        # Suche nach Select-Elementen (Dropdowns)
        for select in soup.find_all('select'):
            name = select.get('name', '')
            id_attr = select.get('id', '')
            if name or id_attr:
                options = [opt.get('value', opt.get_text(strip=True)) for opt in select.find_all('option')]
                filter_key = name or id_attr
                filters[filter_key] = {
                    'type': 'select',
                    'options': options
                }
                print(f"Select: {filter_key}")
                print(f"  Optionen: {options[:5]}")
        
        # Suche nach Input-Feldern
        for input_elem in soup.find_all('input'):
            input_type = input_elem.get('type', '')
            name = input_elem.get('name', '')
            value = input_elem.get('value', '')
            
            if input_type in ['text', 'number', 'date'] and name:
                filters[name] = {
                    'type': input_type,
                    'value': value
                }
                print(f"Input ({input_type}): {name} = {value}")
        
        # Suche nach JavaScript mit Filter-Logik
        print(f"\n=== JAVASCRIPT FILTER-LOGIK ===")
        for script in soup.find_all('script'):
            if script.string:
                script_text = script.string
                
                # Suche nach Filter-Funktionen
                if 'filter' in script_text.lower() or 'konto' in script_text.lower():
                    print(f"JavaScript mit Filter-Logik gefunden (Länge: {len(script_text)})")
                    
                    # Extrahiere relevante Zeilen
                    lines = script_text.split('\n')
                    for i, line in enumerate(lines):
                        if any(kw in line.lower() for kw in ['filter', 'konto', '411', '489', '410021', 'ausschluss', 'not']):
                            print(f"\nZeile {i+1}:")
                            print(f"  {line.strip()[:200]}")
                            # Zeige Kontext
                            for j in range(max(0, i-2), min(len(lines), i+3)):
                                if j != i:
                                    print(f"  {j+1}: {lines[j].strip()[:150]}")
                            break
        
        # Suche nach Report-Daten (Tabellen)
        print(f"\n=== REPORT-DATEN (TABELLEN) ===")
        tables = soup.find_all('table')
        if tables:
            print(f"Gefundene Tabellen: {len(tables)}")
            for i, table in enumerate(tables[:3]):  # Erste 3 Tabellen
                print(f"\nTabelle {i+1}:")
                rows = table.find_all('tr')
                print(f"  Zeilen: {len(rows)}")
                
                # Zeige erste 10 Zeilen
                for row_idx, row in enumerate(rows[:10], 1):
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        row_data = [cell.get_text(strip=True)[:30] for cell in cells[:10]]
                        if any(cell for cell in row_data):
                            print(f"  Zeile {row_idx}: {' | '.join(row_data)}")
        
        # Suche nach BWA-Werten in Text
        print(f"\n=== BWA-WERTE IM TEXT ===")
        text = soup.get_text()
        
        # Suche nach Zahlen in der Nähe von BWA-Begriffen
        bwa_patterns = [
            r'(direkte\s+kosten)[:\s]+([\d.,\s]+)',
            r'(indirekte\s+kosten)[:\s]+([\d.,\s]+)',
            r'(betriebsergebnis)[:\s]+([\d.,\s-]+)',
            r'(umsatzerlöse)[:\s]+([\d.,\s]+)',
        ]
        
        for pattern in bwa_patterns:
            matches = re.findall(pattern, text, re.I)
            if matches:
                print(f"Gefunden ({pattern}):")
                for match in matches[:5]:
                    print(f"  {match[0]}: {match[1]}")
        
        return {
            'filters': filters,
            'html_file': html_file,
            'tables_count': len(tables)
        }
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_filter_logic_from_html(html_file: str):
    """
    Extrahiert Filter-Logik aus gespeichertem HTML
    """
    print(f"\n=== FILTER-LOGIK EXTRAHIEREN ===\n")
    print(f"Datei: {html_file}\n")
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Suche nach Cognos-spezifischen Elementen
        print("=== COGNOS-SPEZIFISCHE ELEMENTE ===")
        
        # Suche nach Report-Parametern in URLs
        urls = re.findall(r'href=["\']([^"\']+)["\']', content)
        for url in urls:
            if 'report' in url.lower() or 'bwa' in url.lower():
                parsed = urlparse(url)
                params = parse_qs(parsed.query)
                if params:
                    print(f"\nURL: {url}")
                    print(f"  Parameter: {params}")
        
        # Suche nach JavaScript-Variablen mit Filter-Logik
        print(f"\n=== JAVASCRIPT-VARIABLEN ===")
        for script in soup.find_all('script'):
            if script.string:
                # Suche nach Variablen mit Filter/Account/Konto
                var_patterns = [
                    r'var\s+(\w*[Ff]ilter\w*)\s*=\s*([^;]+)',
                    r'var\s+(\w*[Kk]onto\w*)\s*=\s*([^;]+)',
                    r'var\s+(\w*[Aa]ccount\w*)\s*=\s*([^;]+)',
                    r'(\w*[Ff]ilter\w*)\s*[:=]\s*([^;,\n]+)',
                ]
                
                for pattern in var_patterns:
                    matches = re.findall(pattern, script.string)
                    if matches:
                        print(f"Gefunden ({pattern}):")
                        for var_name, var_value in matches[:10]:
                            print(f"  {var_name} = {var_value.strip()[:100]}")
        
        # Suche nach SQL-ähnlichen Ausdrücken
        print(f"\n=== SQL-ÄHNLICHE AUSDRÜCKE ===")
        sql_patterns = [
            r'(?:WHERE|AND|OR)\s+([^;]+)',
            r'(?:nominal_account_number|konto)\s*(?:BETWEEN|IN|>=|<=|>|<|=)\s*([^;,\s]+)',
            r'(?:411\d{3}|489\d{3}|410021)',
        ]
        
        for pattern in sql_patterns:
            matches = re.findall(pattern, content, re.I)
            if matches:
                print(f"Gefunden ({pattern}):")
                for match in matches[:10]:
                    print(f"  {match[:200]}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")


def main():
    """
    Hauptfunktion: Scraped BWA-Reports und extrahiert Filter-Logik
    """
    print("=" * 80)
    print("IBM COGNOS REPORT SCRAPER")
    print("=" * 80)
    
    # 1. Finde BWA-Reports
    bwa_reports = find_bwa_reports_in_portal()
    
    if not bwa_reports:
        print("\n⚠️  Keine BWA-Reports gefunden")
        print("Versuche alternative Methoden...\n")
        
        # Versuche bekannte Report-URLs
        known_urls = [
            f"{COGNOS_BI_URL}/reports/bwa",
            f"{COGNOS_BI_URL}/bwa",
            f"{COGNOS_BI_URL}/reporting/bwa",
            f"{COGNOS_BI_URL}/guv",
        ]
        
        for url in known_urls:
            try:
                response = session.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ Gefunden: {url}")
                    bwa_reports.append({
                        'name': 'BWA Report',
                        'url': url,
                        'href': url
                    })
            except:
                pass
    
    # 2. Scrape Reports
    if bwa_reports:
        print(f"\n✅ {len(bwa_reports)} BWA-Reports gefunden\n")
        
        for report in bwa_reports[:5]:  # Erste 5 Reports
            print(f"\n{'='*80}")
            print(f"REPORT: {report['name']}")
            print(f"{'='*80}")
            
            result = scrape_report_page(report['url'])
            
            if result and result.get('html_file'):
                extract_filter_logic_from_html(result['html_file'])
    else:
        print("\n⚠️  Keine BWA-Reports gefunden")
        print("Mögliche Ursachen:")
        print("  - Reports sind in Unterordnern")
        print("  - Reports haben andere Namen")
        print("  - Portal-Struktur ist anders")
        print("\nAlternative: Struktur-Dateien weiter analysieren")
    
    print("\n" + "=" * 80)
    print("✅ Scraping abgeschlossen")
    print("=" * 80)


if __name__ == '__main__':
    main()
