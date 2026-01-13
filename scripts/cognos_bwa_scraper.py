#!/usr/bin/env python3
"""
Cognos BWA Report Scraper
Extrahiert BWA-Werte direkt aus dem Cognos Portal

Erstellt: TAG 182
Ziel: Exakte BWA-Werte für alle Standorte/Marken scrapen
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse, parse_qs
import time

# GlobalCube Cognos Portal
COGNOS_BASE_URL = "http://10.80.80.10:9300"
COGNOS_BI_URL = f"{COGNOS_BASE_URL}/bi/"
LOGIN_USERNAME = "Greiner"
LOGIN_PASSWORD = "Hawaii#22"

# Session für Login
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
})


def login_cognos():
    """
    Login ins Cognos Portal
    """
    print(f"\n=== Cognos Login ===")
    print(f"URL: {COGNOS_BI_URL}")
    print(f"User: {LOGIN_USERNAME}")
    
    try:
        # 1. Hole Login-Seite
        response = session.get(COGNOS_BI_URL, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"URL nach Redirect: {response.url}")
        
        if response.status_code != 200:
            print(f"❌ Fehler: Status {response.status_code}")
            return False
        
        # 2. Prüfe ob Login-Formular vorhanden
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Suche nach Login-Formular
        login_form = soup.find('form', {'method': 'POST'}) or soup.find('form', {'id': 'loginForm'})
        
        if not login_form:
            # Möglicherweise bereits eingeloggt oder andere Struktur
            print("⚠️  Kein Login-Formular gefunden")
            print("Mögliche Ursachen:")
            print("  - Bereits eingeloggt")
            print("  - Andere Login-Struktur")
            print("  - JavaScript-basiertes Login")
            
            # Prüfe ob wir bereits eingeloggt sind
            if 'cognos' in response.text.lower() or 'dashboard' in response.text.lower():
                print("✅ Möglicherweise bereits eingeloggt")
                return True
            
            return False
        
        # 3. Extrahiere Login-Parameter
        action = login_form.get('action', '')
        if not action.startswith('http'):
            action = urljoin(COGNOS_BI_URL, action)
        
        # Suche nach Input-Feldern
        username_field = login_form.find('input', {'type': 'text'}) or login_form.find('input', {'name': re.compile(r'user|login|username', re.I)})
        password_field = login_form.find('input', {'type': 'password'})
        
        if not username_field or not password_field:
            print("❌ Login-Felder nicht gefunden")
            return False
        
        username_name = username_field.get('name', 'username')
        password_name = password_field.get('name', 'password')
        
        # 4. Login durchführen
        login_data = {
            username_name: LOGIN_USERNAME,
            password_name: LOGIN_PASSWORD
        }
        
        print(f"Login-Daten: {username_name}={LOGIN_USERNAME}, {password_name}=***")
        print(f"Action: {action}")
        
        response = session.post(action, data=login_data, allow_redirects=True, timeout=10)
        print(f"Login-Response Status: {response.status_code}")
        print(f"URL nach Login: {response.url}")
        
        # 5. Prüfe ob Login erfolgreich
        if response.status_code == 200:
            if 'error' in response.text.lower() or 'invalid' in response.text.lower() or 'falsch' in response.text.lower():
                print("❌ Login fehlgeschlagen (Fehlermeldung gefunden)")
                return False
            
            if 'cognos' in response.text.lower() or 'dashboard' in response.text.lower() or 'reports' in response.text.lower():
                print("✅ Login erfolgreich")
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ Fehler beim Login: {e}")
        import traceback
        traceback.print_exc()
        return False


def find_bwa_reports():
    """
    Findet BWA-Reports im Cognos Portal
    """
    print(f"\n=== Suche BWA-Reports ===")
    
    try:
        # Navigiere zur Hauptseite
        response = session.get(COGNOS_BI_URL, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Fehler: Status {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Suche nach Links zu Reports
        # Mögliche Patterns: "BWA", "Betriebswirtschaft", "GuV", "F.03"
        report_links = []
        
        # Suche nach Links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Prüfe ob BWA-relevant
            if any(keyword in text.lower() for keyword in ['bwa', 'betriebswirtschaft', 'guv', 'f.03', 'vorjahres']):
                full_url = urljoin(COGNOS_BI_URL, href)
                report_links.append({
                    'url': full_url,
                    'text': text,
                    'href': href
                })
                print(f"✅ Gefunden: {text} -> {full_url}")
        
        # Suche auch in JavaScript
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Suche nach URLs in JavaScript
                urls = re.findall(r'["\']([^"\']*bwa[^"\']*|F\.03[^"\']*)["\']', script.string, re.I)
                for url in urls:
                    if url not in [r['url'] for r in report_links]:
                        full_url = urljoin(COGNOS_BI_URL, url)
                        report_links.append({
                            'url': full_url,
                            'text': 'BWA (aus JavaScript)',
                            'href': url
                        })
                        print(f"✅ Gefunden (JS): {full_url}")
        
        return report_links
        
    except Exception as e:
        print(f"❌ Fehler beim Suchen: {e}")
        import traceback
        traceback.print_exc()
        return []


def scrape_bwa_report(report_url, standort=None, monat=None, jahr=None):
    """
    Scraped einen BWA-Report mit optionalen Filtern
    """
    print(f"\n=== Scrape BWA-Report ===")
    print(f"URL: {report_url}")
    if standort:
        print(f"Standort: {standort}")
    if monat and jahr:
        print(f"Zeitraum: {monat}/{jahr}")
    
    try:
        # Baue URL mit Parametern
        params = {}
        if standort:
            params['standort'] = standort
        if monat:
            params['monat'] = monat
        if jahr:
            params['jahr'] = jahr
        
        response = session.get(report_url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Fehler: Status {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Suche nach Tabellen mit BWA-Daten
        tables = soup.find_all('table')
        
        bwa_data = {}
        
        for table in tables:
            # Prüfe ob Tabelle BWA-Daten enthält
            headers = table.find_all('th')
            rows = table.find_all('tr')
            
            # Suche nach BWA-relevanten Spalten
            relevant_columns = []
            for i, header in enumerate(headers):
                text = header.get_text(strip=True)
                if any(keyword in text.lower() for keyword in ['umsatz', 'einsatz', 'kosten', 'betriebsergebnis', 'deckungsbeitrag']):
                    relevant_columns.append(i)
            
            if relevant_columns:
                print(f"✅ BWA-Tabelle gefunden mit {len(rows)} Zeilen")
                
                # Extrahiere Daten
                for row in rows[1:]:  # Überspringe Header
                    cells = row.find_all(['td', 'th'])
                    if len(cells) > max(relevant_columns):
                        row_data = {}
                        for col_idx in relevant_columns:
                            header_text = headers[col_idx].get_text(strip=True)
                            cell_value = cells[col_idx].get_text(strip=True)
                            row_data[header_text] = cell_value
                        
                        # Identifiziere Position (erste Spalte)
                        if cells:
                            position = cells[0].get_text(strip=True)
                            if position:
                                bwa_data[position] = row_data
        
        return bwa_data
        
    except Exception as e:
        print(f"❌ Fehler beim Scrapen: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """
    Hauptfunktion
    """
    print("=" * 60)
    print("Cognos BWA Report Scraper")
    print("=" * 60)
    
    # 1. Login
    if not login_cognos():
        print("\n❌ Login fehlgeschlagen. Abbruch.")
        return
    
    # 2. Finde BWA-Reports
    reports = find_bwa_reports()
    
    if not reports:
        print("\n⚠️  Keine BWA-Reports gefunden")
        print("Mögliche Ursachen:")
        print("  - Reports sind in Unterordnern")
        print("  - JavaScript-basierte Navigation")
        print("  - Andere URL-Struktur")
        
        # Versuche direkten Zugriff auf bekannte Reports
        known_reports = [
            f"{COGNOS_BI_URL}reports/bwa",
            f"{COGNOS_BI_URL}reports/F.03",
            f"{COGNOS_BI_URL}reports/guv",
        ]
        
        for url in known_reports:
            print(f"\nVersuche: {url}")
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ Erreichbar: {url}")
                reports.append({'url': url, 'text': 'BWA (direkt)', 'href': url})
    
    # 3. Scrape Reports
    if reports:
        print(f"\n=== Scrape {len(reports)} Report(s) ===")
        
        for report in reports:
            # Scrape für verschiedene Standorte
            for standort in [None, 'Landau', 'Deggendorf', 'Hyundai']:
                data = scrape_bwa_report(report['url'], standort=standort, monat=12, jahr=2025)
                
                if data:
                    print(f"\n✅ Daten für {standort or 'Alle'}:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    
                    # Speichere in Datei
                    filename = f"/tmp/bwa_scraped_{standort or 'alle'}_{int(time.time())}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"💾 Gespeichert: {filename}")
    else:
        print("\n❌ Keine Reports zum Scrapen gefunden")
        print("\nNächste Schritte:")
        print("  1. Manuell im Browser navigieren und URL kopieren")
        print("  2. XML-Strukturen analysieren")
        print("  3. Excel-Exports verwenden")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"\n\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
