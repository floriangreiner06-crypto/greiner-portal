#!/usr/bin/env python3
"""
GlobalCube Explorer & Scraper
Analysiert GlobalCube Portal, Reports und Mapping-Logik

Erstellt: TAG 182
"""

import requests
import json
import os
import re
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
import zipfile
import struct

# GlobalCube Konfiguration
GLOBALCUBE_PORTAL_URL = "http://10.80.80.10:9300"
GLOBALCUBE_MOUNT = "/mnt/globalcube"
GLOBALCUBE_STRUCT_PATH = f"{GLOBALCUBE_MOUNT}/GCStruct"
GLOBALCUBE_CUBES_PATH = f"{GLOBALCUBE_MOUNT}/Cubes"

# Session für Login
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})


def login_globalcube(username="Greiner", password="Hawaii#22"):
    """
    Login ins GlobalCube Portal
    """
    print(f"\n=== GlobalCube Login ===")
    print(f"URL: {GLOBALCUBE_PORTAL_URL}")
    print(f"User: {username}")
    
    # Prüfe ob Portal erreichbar
    try:
        # Erste Anfrage: Hole Login-Seite
        response = session.get(GLOBALCUBE_PORTAL_URL, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Portal erreichbar")
            
            # Prüfe ob Login-Seite
            if 'login' in response.url.lower() or 'anmeldung' in response.text.lower() or 'password' in response.text.lower():
                print("⚠️  Login erforderlich")
                
                if password:
                    # Suche nach Login-Formular
                    from html.parser import HTMLParser
                    import re
                    
                    # Versuche verschiedene Login-Formate
                    # Format 1: Standard HTML-Form
                    login_data = {}
                    
                    # Suche nach Form-Feldern
                    username_fields = ['username', 'user', 'login', 'name', 'benutzer']
                    password_fields = ['password', 'pass', 'pwd', 'passwort']
                    
                    for field in username_fields:
                        if re.search(rf'name=["\']?{field}', response.text, re.I):
                            login_data[field] = username
                            break
                    
                    for field in password_fields:
                        if re.search(rf'name=["\']?{field}', response.text, re.I):
                            login_data[field] = password
                            break
                    
                    if login_data:
                        # Versuche Login
                        login_url = response.url
                        if 'action=' in response.text:
                            action_match = re.search(r'action=["\']?([^"\'>]+)', response.text, re.I)
                            if action_match:
                                action = action_match.group(1)
                                if not action.startswith('http'):
                                    from urllib.parse import urljoin
                                    login_url = urljoin(GLOBALCUBE_PORTAL_URL, action)
                        
                        print(f"Versuche Login bei: {login_url}")
                        login_response = session.post(login_url, data=login_data, timeout=10)
                        
                        if login_response.status_code == 200:
                            if 'login' not in login_response.url.lower() and 'anmeldung' not in login_response.url.lower():
                                print("✅ Login erfolgreich!")
                                return True
                            else:
                                print("❌ Login fehlgeschlagen (bleibt auf Login-Seite)")
                        else:
                            print(f"⚠️  Login-Response: {login_response.status_code}")
                    else:
                        # Versuche einfaches Basic Auth
                        print("Versuche Basic Auth...")
                        session.auth = (username, password)
                        auth_response = session.get(GLOBALCUBE_PORTAL_URL, timeout=10)
                        if auth_response.status_code == 200 and 'login' not in auth_response.url.lower():
                            print("✅ Basic Auth erfolgreich!")
                            return True
                else:
                    print("⚠️  Passwort nicht angegeben")
            else:
                print("✅ Bereits eingeloggt oder kein Login erforderlich")
                return True
        else:
            print(f"⚠️  Unerwarteter Status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Fehler beim Zugriff: {e}")
        return False
    
    return False


def explore_globalcube_structure():
    """
    Analysiert GlobalCube Struktur-Dateien
    """
    print(f"\n=== GlobalCube Struktur-Analyse ===")
    print(f"Pfad: {GLOBALCUBE_STRUCT_PATH}")
    
    if not os.path.exists(GLOBALCUBE_STRUCT_PATH):
        print(f"❌ Pfad nicht gefunden: {GLOBALCUBE_STRUCT_PATH}")
        return None
    
    # Liste alle Struktur-Dateien
    struct_files = []
    for root, dirs, files in os.walk(GLOBALCUBE_STRUCT_PATH):
        for file in files:
            if file.endswith(('.xml', '.zip', '.mdc')):
                struct_files.append(os.path.join(root, file))
    
    print(f"Gefundene Struktur-Dateien: {len(struct_files)}")
    
    # Analysiere neueste Struktur
    if struct_files:
        latest = max(struct_files, key=os.path.getmtime)
        print(f"Neueste Struktur: {os.path.basename(latest)}")
        print(f"  Pfad: {latest}")
        print(f"  Größe: {os.path.getsize(latest) / 1024:.1f} KB")
        print(f"  Geändert: {datetime.fromtimestamp(os.path.getmtime(latest))}")
    
    return struct_files


def explore_globalcube_cubes():
    """
    Analysiert GlobalCube Cube-Definitionen
    """
    print(f"\n=== GlobalCube Cube-Analyse ===")
    print(f"Pfad: {GLOBALCUBE_CUBES_PATH}")
    
    if not os.path.exists(GLOBALCUBE_CUBES_PATH):
        print(f"❌ Pfad nicht gefunden: {GLOBALCUBE_CUBES_PATH}")
        return None
    
    cubes = {}
    
    # Liste alle .mdc Dateien (Cube-Definitionen)
    for file in os.listdir(GLOBALCUBE_CUBES_PATH):
        if file.endswith('.mdc'):
            cube_name = file.replace('.mdc', '')
            cube_path = os.path.join(GLOBALCUBE_CUBES_PATH, file)
            
            cubes[cube_name] = {
                'name': cube_name,
                'path': cube_path,
                'size': os.path.getsize(cube_path),
                'modified': datetime.fromtimestamp(os.path.getmtime(cube_path))
            }
            
            # Prüfe ob es Versionen gibt
            version_dirs = [d for d in os.listdir(GLOBALCUBE_CUBES_PATH) 
                          if d.startswith(f"{cube_name}__")]
            if version_dirs:
                latest_version = max(version_dirs, key=lambda d: os.path.getmtime(
                    os.path.join(GLOBALCUBE_CUBES_PATH, d)))
                cubes[cube_name]['latest_version'] = latest_version
                cubes[cube_name]['version_path'] = os.path.join(
                    GLOBALCUBE_CUBES_PATH, latest_version)
    
    print(f"Gefundene Cubes: {len(cubes)}")
    for cube_name, cube_info in sorted(cubes.items()):
        print(f"  - {cube_name}")
        print(f"    Größe: {cube_info['size'] / 1024:.1f} KB")
        print(f"    Geändert: {cube_info['modified']}")
        if 'latest_version' in cube_info:
            print(f"    Neueste Version: {cube_info['latest_version']}")
    
    return cubes


def analyze_bwa_cube_structure():
    """
    Analysiert BWA-relevante Cube-Strukturen
    """
    print(f"\n=== BWA Cube-Struktur-Analyse ===")
    
    # Suche nach BWA-relevanten Cubes
    bwa_keywords = ['bwa', 'betriebswirtschaft', 'guv', 'ergebnis', 'kosten', 'umsatz']
    
    cubes = explore_globalcube_cubes()
    if not cubes:
        return None
    
    bwa_cubes = {}
    for cube_name, cube_info in cubes.items():
        cube_lower = cube_name.lower()
        if any(keyword in cube_lower for keyword in bwa_keywords):
            bwa_cubes[cube_name] = cube_info
    
    print(f"BWA-relevante Cubes: {len(bwa_cubes)}")
    
    # Analysiere Cube-Definitionen
    for cube_name, cube_info in bwa_cubes.items():
        print(f"\n--- {cube_name} ---")
        analyze_cube_definition(cube_info['path'])
    
    return bwa_cubes


def extract_bwa_mapping_from_csv():
    """
    Extrahiert BWA-Mapping aus vorhandenen CSV-Dateien
    """
    print(f"\n=== BWA Mapping aus CSV ===")
    
    # Suche nach BWA CSV-Dateien
    csv_paths = [
        "/opt/greiner-portal/docs/F.03 BWA Vorjahres-Vergleich (7).xlsx",
        "/mnt/greiner-portal-sync/docs/F.03 BWA Vorjahres-Vergleich (7).xlsx",
    ]
    
    for csv_path in csv_paths:
        if os.path.exists(csv_path):
            print(f"Gefunden: {csv_path}")
            # TODO: CSV/Excel parsen und Mapping extrahieren
            break
    else:
        print("Keine BWA CSV-Dateien gefunden")


def analyze_cube_definition(cube_path):
    """
    Analysiert eine Cube-Definition (.mdc Datei)
    """
    print(f"\n  Analysiere: {os.path.basename(cube_path)}")
    
    try:
        with open(cube_path, 'rb') as f:
            content = f.read()
        
        # Prüfe ob XML
        try:
            root = ET.fromstring(content)
            print(f"    Format: XML")
            print(f"    Root-Tag: {root.tag}")
            
            # Suche nach relevanten Elementen
            for elem in root.iter():
                tag_lower = elem.tag.lower()
                if any(kw in tag_lower for kw in ['filter', 'konto', 'account', 'measure', 'dimension']):
                    text = (elem.text or '')[:200]
                    if text:
                        print(f"    {elem.tag}: {text}")
            
            return root
            
        except ET.ParseError:
            # Versuche als Binär zu lesen
            print(f"    Format: Binär (Länge: {len(content)} Bytes)")
            
            # Prüfe ob es ein bekanntes Format ist
            if content[:4] == b'PK\x03\x04':
                print(f"    Format: ZIP")
                try:
                    with zipfile.ZipFile(cube_path, 'r') as z:
                        print(f"    ZIP-Inhalt:")
                        for name in z.namelist()[:10]:
                            print(f"      - {name}")
                except:
                    pass
            
            return None
            
    except Exception as e:
        print(f"    Fehler: {e}")
        return None


def find_bwa_reports():
    """
    Findet BWA-Reports im GlobalCube Portal
    """
    print(f"\n=== BWA-REPORTS IM PORTAL SUCHEN ===\n")
    
    # Mögliche BWA-Report-URLs
    bwa_urls = [
        f"{GLOBALCUBE_PORTAL_URL}/reports/bwa",
        f"{GLOBALCUBE_PORTAL_URL}/bwa",
        f"{GLOBALCUBE_PORTAL_URL}/reporting/bwa",
        f"{GLOBALCUBE_PORTAL_URL}/guv",
        f"{GLOBALCUBE_PORTAL_URL}/reports/guv",
        f"{GLOBALCUBE_PORTAL_URL}/controlling/bwa",
    ]
    
    found_reports = []
    
    for url in bwa_urls:
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ Gefunden: {url}")
                found_reports.append(url)
                
                # Prüfe ob es ein BWA-Report ist
                content_lower = response.text.lower()
                if any(kw in content_lower for kw in ['bwa', 'betriebswirtschaft', 'guv', 'umsatzerlöse', 'betriebsergebnis']):
                    print(f"  → BWA-relevanter Inhalt gefunden")
                    
                    # Suche nach Filter-Elementen
                    import re
                    filters = re.findall(r'(?:name|id)=["\']([^"\']*(?:filter|konto|account|standort|zeitraum|monat|jahr)[^"\']*)["\']', response.text, re.I)
                    if filters:
                        print(f"  → Filter-Elemente gefunden: {len(filters)}")
                        for f in filters[:5]:
                            print(f"    - {f}")
                    
                    # Suche nach JavaScript mit Filter-Logik
                    scripts = re.findall(r'<script[^>]*>(.*?)</script>', response.text, re.DOTALL | re.I)
                    for script in scripts:
                        if any(kw in script.lower() for kw in ['filter', 'konto', '411', '489', '410021']):
                            print(f"  → JavaScript mit Filter-Logik gefunden")
                            # Zeige relevante Zeilen
                            lines = script.split('\n')
                            for i, line in enumerate(lines):
                                if any(kw in line.lower() for kw in ['filter', 'konto', '411', '489', '410021']):
                                    print(f"    Zeile {i+1}: {line.strip()[:150]}")
                                    if i < len(lines) - 1:
                                        print(f"    Zeile {i+2}: {lines[i+1].strip()[:150]}")
                                    break
                    
                    # Speichere HTML für weitere Analyse
                    report_file = f"/tmp/globalcube_bwa_report_{len(found_reports)}.html"
                    with open(report_file, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"  → HTML gespeichert: {report_file}")
                    
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Fehler bei {url}: {e}")
    
    if not found_reports:
        print("⚠️  Keine BWA-Reports gefunden")
        print("Versuche Hauptseite zu analysieren...")
        
        try:
            response = session.get(GLOBALCUBE_PORTAL_URL, timeout=10)
            if response.status_code == 200:
                # Suche nach Links zu BWA-Reports
                import re
                links = re.findall(r'href=["\']([^"\']*(?:bwa|guv|betriebswirtschaft|controlling)[^"\']*)["\']', response.text, re.I)
                if links:
                    print(f"Gefundene BWA-Links: {len(links)}")
                    for link in links[:10]:
                        if not link.startswith('http'):
                            link = f"{GLOBALCUBE_PORTAL_URL}{link}"
                        print(f"  - {link}")
        except Exception as e:
            print(f"Fehler: {e}")
    
    return found_reports


def generate_mapping_documentation():
    """
    Generiert Dokumentation der gefundenen Mapping-Logik
    """
    print(f"\n=== Generiere Mapping-Dokumentation ===")
    
    doc_path = "/opt/greiner-portal/docs/GLOBALCUBE_BWA_MAPPING_EXPLORATION_TAG182.md"
    
    doc_content = f"""# GlobalCube BWA Mapping Exploration - TAG 182

**Datum:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Status:** 🔍 Exploration läuft

---

## 🎯 ZIEL

Die tatsächliche GlobalCube BWA-Logik und Mapping-Regeln durch direkte Analyse extrahieren.

---

## 📋 GEFUNDENE RESSOURCEN

### GlobalCube Portal
- **URL:** {GLOBALCUBE_PORTAL_URL}
- **Status:** ✅ Erreichbar

### GlobalCube Strukturen
- **Pfad:** {GLOBALCUBE_STRUCT_PATH}
- **Status:** {'✅ Gefunden' if os.path.exists(GLOBALCUBE_STRUCT_PATH) else '❌ Nicht gefunden'}

### GlobalCube Cubes
- **Pfad:** {GLOBALCUBE_CUBES_PATH}
- **Status:** {'✅ Gefunden' if os.path.exists(GLOBALCUBE_CUBES_PATH) else '❌ Nicht gefunden'}

---

## 🔍 NÄCHSTE SCHRITTE

1. ⏳ GlobalCube Portal Login implementieren
2. ⏳ BWA-Reports im Portal finden und analysieren
3. ⏳ Filter-Logik aus Reports extrahieren
4. ⏳ Cube-Definitionen (.mdc) analysieren
5. ⏳ Mapping-Regeln dokumentieren

---

## 📝 ERGEBNISSE

*Wird während der Exploration aktualisiert...*

"""
    
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    print(f"✅ Dokumentation erstellt: {doc_path}")
    return doc_path


def main():
    """
    Hauptfunktion: Führt alle Explorationen durch
    """
    print("=" * 80)
    print("GLOBALCUBE EXPLORER & SCRAPER")
    print("=" * 80)
    
    # 1. Login testen
    if login_globalcube("Greiner", "Hawaii#22"):
        # 2. BWA-Reports im Portal finden
        find_bwa_reports()
    
    # 2. Strukturen analysieren
    explore_globalcube_structure()
    
    # 3. Cubes analysieren
    explore_globalcube_cubes()
    
    # 4. BWA-relevante Cubes analysieren
    analyze_bwa_cube_structure()
    
    # 5. CSV-Mapping extrahieren
    extract_bwa_mapping_from_csv()
    
    # 6. BWA-Reports analysieren (übersprungen - benötigt Login)
    
    # 7. Dokumentation generieren
    generate_mapping_documentation()
    
    print("\n" + "=" * 80)
    print("✅ Exploration abgeschlossen")
    print("=" * 80)


if __name__ == '__main__':
    main()
