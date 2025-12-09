#!/usr/bin/env python3
"""
DT-Standard Telefonanlage Explorer
Erkundet die Admin-Oberfläche und sucht nach Anrufstatistiken (Inbound/Outbound)

Verwendung:
    python dt_standard_explorer.py
"""

import requests
from bs4 import BeautifulSoup
import urllib3
import json
import re
from urllib.parse import urljoin, urlparse
import sys

# SSL-Warnungen unterdrücken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DTStandardExplorer:
    def __init__(self):
        self.base_url = "https://admin.dt-standard.de"
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
        })
        self.visited_urls = set()
        self.found_pages = {}
        self.interesting_keywords = [
            'statistik', 'statistic', 'report', 'bericht', 
            'call', 'anruf', 'cdr', 'log', 'protokoll',
            'inbound', 'outbound', 'eingehend', 'ausgehend',
            'auswertung', 'analyse', 'dashboard', 'übersicht'
        ]
        
    def explore_page(self, url, soup, depth=0):
        """Analysiert eine Seite und extrahiert relevante Infos"""
        indent = "  " * depth
        
        # Titel
        title = soup.find('title')
        title_text = title.text.strip() if title else "Kein Titel"
        print(f"{indent}📄 Seite: {title_text}")
        
        # Navigation/Menü suchen
        nav_elements = soup.find_all(['nav', 'ul', 'div'], class_=re.compile(r'nav|menu|sidebar', re.I))
        
        if nav_elements:
            print(f"{indent}📋 Navigation gefunden:")
            for nav in nav_elements[:3]:  # Max 3 Nav-Elemente
                links = nav.find_all('a')
                for link in links[:20]:  # Max 20 Links pro Nav
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    if text and href:
                        full_url = urljoin(url, href)
                        # Interessant?
                        is_interesting = any(kw in text.lower() or kw in href.lower() 
                                            for kw in self.interesting_keywords)
                        marker = "⭐" if is_interesting else "  "
                        print(f"{indent}   {marker} {text}: {href}")
                        
                        if is_interesting:
                            self.found_pages[full_url] = text
        
        # Alle Links sammeln
        all_links = soup.find_all('a', href=True)
        print(f"{indent}🔗 Gefundene Links: {len(all_links)}")
        
        # Formulare analysieren
        forms = soup.find_all('form')
        if forms:
            print(f"{indent}📝 Formulare: {len(forms)}")
            for form in forms:
                action = form.get('action', '')
                method = form.get('method', 'GET')
                print(f"{indent}   - Action: {action}, Method: {method}")
        
        # Frames/iFrames
        frames = soup.find_all(['frame', 'iframe'])
        if frames:
            print(f"{indent}🖼️ Frames: {len(frames)}")
            for frame in frames:
                src = frame.get('src', '')
                name = frame.get('name', '')
                print(f"{indent}   - {name}: {src}")
                
        return all_links

    def login(self, username, password):
        """Login zur Telefonanlage"""
        print(f"\n{'='*70}")
        print("🔐 DT-STANDARD LOGIN")
        print(f"{'='*70}")
        
        # Startseite holen
        print(f"\n📡 Lade: {self.base_url}")
        try:
            response = self.session.get(self.base_url, timeout=30)
            print(f"   ✓ Status: {response.status_code}")
            print(f"   ✓ Final-URL: {response.url}")
            print(f"   ✓ Größe: {len(response.text)} Bytes")
        except Exception as e:
            print(f"   ❌ Fehler: {e}")
            return False
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Login-Formular finden
        forms = soup.find_all('form')
        print(f"\n📋 Gefundene Formulare: {len(forms)}")
        
        login_form = None
        login_action = None
        form_data = {}
        
        for form in forms:
            inputs = form.find_all('input')
            has_password = any(inp.get('type') == 'password' for inp in inputs)
            
            if has_password:
                login_form = form
                login_action = form.get('action', '')
                
                print(f"\n🔑 Login-Formular gefunden!")
                print(f"   Action: {login_action}")
                print(f"   Method: {form.get('method', 'GET')}")
                print(f"   Input-Felder:")
                
                for inp in inputs:
                    name = inp.get('name', '')
                    inp_type = inp.get('type', 'text')
                    value = inp.get('value', '')
                    placeholder = inp.get('placeholder', '')
                    
                    print(f"      - {name}: type={inp_type}")
                    
                    if name:
                        if inp_type == 'hidden':
                            form_data[name] = value
                        elif inp_type == 'password':
                            form_data[name] = password
                        elif 'user' in name.lower() or 'login' in name.lower() or 'id' in name.lower():
                            form_data[name] = username
                        elif inp_type in ['text', 'email']:
                            # Könnte Username-Feld sein
                            if not any(k for k in form_data.keys() if 'user' in k.lower()):
                                form_data[name] = username
                break
        
        if not login_form:
            print("\n⚠️ Kein Login-Formular gefunden!")
            print("\nSeiten-Inhalt (Ausschnitt):")
            print("-" * 50)
            print(response.text[:2000])
            return False
        
        # Login durchführen
        login_url = urljoin(response.url, login_action) if login_action else response.url
        print(f"\n🚀 Sende Login an: {login_url}")
        print(f"   Daten: {json.dumps({k: '***' if 'pass' in k.lower() else v for k, v in form_data.items()}, indent=2)}")
        
        try:
            login_response = self.session.post(login_url, data=form_data, timeout=30)
            print(f"\n   ✓ Status: {login_response.status_code}")
            print(f"   ✓ Final-URL: {login_response.url}")
            print(f"   ✓ Größe: {len(login_response.text)} Bytes")
            
            # Cookies anzeigen
            if self.session.cookies:
                print(f"\n   🍪 Cookies:")
                for cookie in self.session.cookies:
                    print(f"      - {cookie.name}: {cookie.value[:30]}...")
            
            return login_response
            
        except Exception as e:
            print(f"\n   ❌ Login-Fehler: {e}")
            return False

    def explore(self, start_response):
        """Erkundet die Anwendung nach dem Login"""
        print(f"\n{'='*70}")
        print("🔍 EXPLORATION")
        print(f"{'='*70}")
        
        soup = BeautifulSoup(start_response.text, 'html.parser')
        
        # Startseite analysieren
        print("\n📄 STARTSEITE NACH LOGIN:")
        self.explore_page(start_response.url, soup)
        
        # Nach interessanten Seiten suchen
        if self.found_pages:
            print(f"\n{'='*70}")
            print("⭐ INTERESSANTE SEITEN GEFUNDEN:")
            print(f"{'='*70}")
            
            for url, title in self.found_pages.items():
                print(f"\n🔗 {title}")
                print(f"   URL: {url}")
                
                # Diese Seiten direkt abrufen
                try:
                    print(f"   📡 Lade Seite...")
                    resp = self.session.get(url, timeout=30)
                    if resp.status_code == 200:
                        page_soup = BeautifulSoup(resp.text, 'html.parser')
                        self.explore_page(url, page_soup, depth=1)
                except Exception as e:
                    print(f"   ❌ Fehler: {e}")
        
        # Frameset erkunden
        frames = soup.find_all(['frame', 'iframe'])
        if frames:
            print(f"\n{'='*70}")
            print("🖼️ FRAMES ERKUNDEN:")
            print(f"{'='*70}")
            
            for frame in frames:
                src = frame.get('src', '')
                if src:
                    frame_url = urljoin(start_response.url, src)
                    print(f"\n📡 Lade Frame: {frame_url}")
                    try:
                        frame_resp = self.session.get(frame_url, timeout=30)
                        if frame_resp.status_code == 200:
                            frame_soup = BeautifulSoup(frame_resp.text, 'html.parser')
                            self.explore_page(frame_url, frame_soup, depth=1)
                    except Exception as e:
                        print(f"   ❌ Fehler: {e}")
        
        # Zusammenfassung
        print(f"\n{'='*70}")
        print("📊 ZUSAMMENFASSUNG")
        print(f"{'='*70}")
        print(f"   Besuchte Seiten: {len(self.visited_urls)}")
        print(f"   Interessante Seiten: {len(self.found_pages)}")
        
        if self.found_pages:
            print(f"\n   ⭐ Für Anruf-Statistiken relevante Seiten:")
            for url, title in self.found_pages.items():
                print(f"      - {title}: {url}")


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║           DT-STANDARD TELEFONANLAGE EXPLORER                         ║
║           Sucht nach Inbound/Outbound Anrufstatistiken               ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    explorer = DTStandardExplorer()
    
    # Login
    response = explorer.login(
        username="KCIDP",
        password="Hyundai2021!"
    )
    
    if response and response.status_code == 200:
        # Erkunden
        explorer.explore(response)
    else:
        print("\n❌ Login fehlgeschlagen!")
        sys.exit(1)


if __name__ == "__main__":
    main()
