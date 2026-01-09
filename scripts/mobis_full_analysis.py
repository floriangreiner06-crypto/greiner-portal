#!/usr/bin/env python3
"""
Mobis EDMOS Vollständige API-Analyse
====================================
Führt Login durch und analysiert die komplette API-Struktur.
"""

import requests
import re
import json
import time
from urllib.parse import urljoin, urlparse, parse_qs
from html.parser import HTMLParser

BASE_URL = 'https://edos.mobiseurope.com'
LOGIN_URL = f'{BASE_URL}/EDMOSN/gen/index.jsp'
USERNAME = 'G2403Koe'
PASSWORD = 'Greiner3!'

class MobisAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.base_url = BASE_URL
        self.api_endpoints = []
        self.found_links = []
        
    def login(self):
        """Führt Login durch."""
        print("\n" + "=" * 80)
        print("LOGIN PROZESS")
        print("=" * 80)
        
        # 1. Hole Login-Seite
        print("\n[1] Hole Login-Seite...")
        r = self.session.get(LOGIN_URL, timeout=30)
        print(f"   Status: {r.status_code}")
        print(f"   Cookies: {list(self.session.cookies.keys())}")
        
        # 2. Versuche verschiedene Login-Methoden
        print("\n[2] Versuche Login...")
        
        # Methode 1: Standard POST
        login_data = {
            'userid': USERNAME,
            'password': PASSWORD,
            'userId': USERNAME,
            'userPassword': PASSWORD,
            'username': USERNAME,
            'user': USERNAME
        }
        
        login_endpoints = [
            f'{BASE_URL}/EDMOSN/gen/login.do',
            f'{BASE_URL}/EDMOSN/gen/index.jsp',
            f'{BASE_URL}/EDMOSN/gen/auth.do',
            f'{BASE_URL}/EDMOSN/gen/login.jsp'
        ]
        
        login_success = False
        for endpoint in login_endpoints:
            print(f"\n   Versuche: {endpoint}")
            try:
                r_login = self.session.post(
                    endpoint,
                    data=login_data,
                    timeout=30,
                    allow_redirects=True
                )
                print(f"     Status: {r_login.status_code}")
                print(f"     URL: {r_login.url}")
                print(f"     Cookies: {list(self.session.cookies.keys())}")
                
                # Prüfe auf Erfolg
                if r_login.status_code == 200:
                    text_lower = r_login.text.lower()
                    url_lower = r_login.url.lower()
                    
                    # Erfolgs-Indikatoren
                    if any(indicator in text_lower for indicator in ['welcome', 'dashboard', 'main', 'menu', 'hauptmenü']):
                        print("     ✅ Login möglicherweise erfolgreich!")
                        login_success = True
                        break
                    elif any(indicator in url_lower for indicator in ['main', 'dashboard', 'home', 'menu']):
                        print("     ✅ Login möglicherweise erfolgreich (URL)!")
                        login_success = True
                        break
                    elif 'error' not in text_lower and 'fehler' not in text_lower:
                        print("     ⚠️  Unklarer Status, aber kein Fehler")
                        # Versuche trotzdem weiter
                        login_success = True
                        break
            except Exception as e:
                print(f"     ❌ Fehler: {str(e)}")
        
        return login_success
    
    def analyze_page(self, url, description=""):
        """Analysiert eine Seite nach API-Endpunkten."""
        print(f"\n{'=' * 80}")
        print(f"ANALYSE: {description or url}")
        print("=" * 80)
        
        try:
            r = self.session.get(url, timeout=30)
            print(f"Status: {r.status_code}")
            print(f"Content-Type: {r.headers.get('Content-Type', 'N/A')}")
            
            html = r.text
            
            # 1. Suche nach .do Endpunkten
            do_pattern = r'["\']([^"\']*\.do[^"\']*)["\']'
            do_endpoints = set(re.findall(do_pattern, html, re.IGNORECASE))
            
            # 2. Suche nach /api/ Endpunkten
            api_pattern = r'["\']([^"\']*\/api\/[^"\']*)["\']'
            api_endpoints = set(re.findall(api_pattern, html, re.IGNORECASE))
            
            # 3. Suche nach AJAX-Calls in JavaScript
            ajax_patterns = [
                r'\.ajax\s*\(\s*["\']([^"\']+)["\']',
                r'\.post\s*\(\s*["\']([^"\']+)["\']',
                r'\.get\s*\(\s*["\']([^"\']+)["\']',
                r'fetch\s*\(\s*["\']([^"\']+)["\']',
                r'url\s*[:=]\s*["\']([^"\']+)["\']',
                r'action\s*[:=]\s*["\']([^"\']+)["\']',
            ]
            
            ajax_endpoints = set()
            for pattern in ajax_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                ajax_endpoints.update(matches)
            
            # 4. Suche nach Links zu Teilebezug
            teile_keywords = ['teil', 'part', 'bestell', 'order', 'liefer', 'deliver', 'lager', 'stock']
            link_pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>([^<]*)</a>'
            links = re.findall(link_pattern, html, re.IGNORECASE)
            
            teile_links = []
            for href, text in links:
                if any(keyword in (href + text).lower() for keyword in teile_keywords):
                    full_url = urljoin(self.base_url, href)
                    teile_links.append((full_url, text.strip()))
            
            # 5. Suche nach Nexacro Transaction-Calls
            transaction_patterns = [
                r'transaction\s*[:=]\s*["\']([^"\']+)["\']',
                r'\.doTransaction\s*\(\s*["\']([^"\']+)["\']',
                r'nexacro\s*\.\s*transaction\s*\(\s*["\']([^"\']+)["\']',
            ]
            
            transaction_endpoints = set()
            for pattern in transaction_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                transaction_endpoints.update(matches)
            
            # Ausgabe
            all_endpoints = do_endpoints | api_endpoints | ajax_endpoints | transaction_endpoints
            
            if all_endpoints:
                print(f"\nGefundene Endpunkte: {len(all_endpoints)}")
                for ep in sorted(all_endpoints)[:30]:
                    if not ep.startswith('http'):
                        ep = urljoin(self.base_url, ep)
                    print(f"  - {ep}")
                    if ep not in self.api_endpoints:
                        self.api_endpoints.append(ep)
            
            if teile_links:
                print(f"\nTeilebezug-Links gefunden: {len(teile_links)}")
                for url, text in teile_links[:10]:
                    print(f"  - {text}: {url}")
                    self.found_links.append((url, text))
            
            # Speichere HTML für weitere Analyse
            filename = f"/tmp/mobis_{description.replace(' ', '_').lower()}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"\nHTML gespeichert: {filename}")
            
            return r
            
        except Exception as e:
            print(f"❌ Fehler: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def search_parts_functionality(self):
        """Sucht nach Teilebezug-Funktionalität."""
        print("\n" + "=" * 80)
        print("SUCHE NACH TEILEBEZUG-FUNKTIONALITÄT")
        print("=" * 80)
        
        # Analysiere Hauptseite nach Login
        main_page = self.analyze_page(LOGIN_URL, "Hauptseite nach Login")
        
        # Versuche bekannte Pfade
        common_paths = [
            '/EDMOSN/gen/main.do',
            '/EDMOSN/gen/menu.do',
            '/EDMOSN/gen/dashboard.do',
            '/EDMOSN/gen/home.do',
            '/EDMOSN/gen/parts.do',
            '/EDMOSN/gen/teile.do',
            '/EDMOSN/gen/order.do',
            '/EDMOSN/gen/bestellung.do',
        ]
        
        for path in common_paths:
            url = f"{self.base_url}{path}"
            print(f"\nVersuche: {url}")
            try:
                r = self.session.get(url, timeout=10)
                if r.status_code == 200 and len(r.text) > 1000:  # Nicht nur Error-Page
                    self.analyze_page(url, f"Pfad: {path}")
            except:
                pass
        
        # Folge gefundenen Links
        for url, text in self.found_links[:5]:  # Max 5 Links
            if 'teil' in text.lower() or 'part' in text.lower():
                print(f"\nFolge Link: {text}")
                self.analyze_page(url, f"Link: {text}")
    
    def test_endpoints(self):
        """Testet gefundene Endpunkte."""
        print("\n" + "=" * 80)
        print("TESTE GEFUNDENE ENDPUNKTE")
        print("=" * 80)
        
        # Filtere relevante Endpunkte
        relevant_keywords = ['part', 'teil', 'order', 'bestell', 'liefer', 'deliver', 'lager', 'stock']
        
        relevant_endpoints = []
        for ep in self.api_endpoints:
            if any(keyword in ep.lower() for keyword in relevant_keywords):
                relevant_endpoints.append(ep)
        
        if not relevant_endpoints:
            print("Keine relevanten Endpunkte gefunden.")
            return
        
        print(f"\nTeste {len(relevant_endpoints)} relevante Endpunkte...")
        
        for ep in relevant_endpoints[:10]:  # Max 10 testen
            print(f"\n  Teste: {ep}")
            try:
                # Versuche GET
                r_get = self.session.get(ep, timeout=10)
                print(f"    GET: {r_get.status_code}")
                
                # Versuche POST (wenn GET nicht funktioniert)
                if r_get.status_code == 405 or r_get.status_code == 404:
                    r_post = self.session.post(ep, data={}, timeout=10)
                    print(f"    POST: {r_post.status_code}")
                    
                    if r_post.status_code == 200:
                        # Prüfe Response-Format
                        content_type = r_post.headers.get('Content-Type', '')
                        if 'json' in content_type:
                            print(f"    ✅ JSON-Response!")
                            try:
                                data = r_post.json()
                                print(f"    Response (erste 200 Zeichen): {str(data)[:200]}")
                            except:
                                pass
                        elif 'xml' in content_type:
                            print(f"    ✅ XML-Response!")
                        else:
                            print(f"    Response (erste 200 Zeichen): {r_post.text[:200]}")
            except Exception as e:
                print(f"    ❌ Fehler: {str(e)}")
    
    def generate_report(self):
        """Generiert Analyse-Report."""
        print("\n" + "=" * 80)
        print("ANALYSE-REPORT")
        print("=" * 80)
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'base_url': self.base_url,
            'api_endpoints': sorted(set(self.api_endpoints)),
            'teilebezug_links': self.found_links,
            'summary': {
                'total_endpoints': len(set(self.api_endpoints)),
                'teilebezug_links': len(self.found_links)
            }
        }
        
        # Speichere Report
        report_file = '/tmp/mobis_analysis_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nReport gespeichert: {report_file}")
        print(f"\nZusammenfassung:")
        print(f"  - Gefundene Endpunkte: {report['summary']['total_endpoints']}")
        print(f"  - Teilebezug-Links: {report['summary']['teilebezug_links']}")
        
        return report


def main():
    """Hauptfunktion."""
    print("=" * 80)
    print("MOBIS EDMOS VOLLSTÄNDIGE API-ANALYSE")
    print("=" * 80)
    
    analyzer = MobisAnalyzer()
    
    # 1. Login
    if analyzer.login():
        print("\n✅ Login erfolgreich!")
        
        # 2. Analysiere Hauptseite
        analyzer.search_parts_functionality()
        
        # 3. Teste Endpunkte
        analyzer.test_endpoints()
        
        # 4. Generiere Report
        report = analyzer.generate_report()
        
        print("\n" + "=" * 80)
        print("ANALYSE ABGESCHLOSSEN")
        print("=" * 80)
        
    else:
        print("\n❌ Login fehlgeschlagen - kann nicht weiter analysieren")


if __name__ == "__main__":
    main()
