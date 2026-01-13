#!/usr/bin/env python3
"""
IBM Cognos API Explorer
Analysiert Cognos REST API und extrahiert BWA-Reports

Erstellt: TAG 182
"""

import requests
import json
from typing import Dict, List, Optional

# Cognos Konfiguration
COGNOS_BASE_URL = "http://10.80.80.10:9300"
COGNOS_USER = "Greiner"
COGNOS_PASS = "Hawaii#22"

# Session für Authentifizierung
session = requests.Session()
session.auth = (COGNOS_USER, COGNOS_PASS)
session.headers.update({
    'Accept': 'application/json',
    'Content-Type': 'application/json'
})


def test_cognos_api():
    """
    Testet verschiedene Cognos API-Endpunkte
    """
    print("=== COGNOS API TEST ===\n")
    
    # Mögliche API-Endpunkte
    api_endpoints = [
        "/bi/v1/disp",
        "/bi/v1/disp/r",
        "/bi/api/v1",
        "/bi/api",
        "/api/v1",
        "/api",
        "/rest/v1",
        "/rest",
    ]
    
    working_endpoints = []
    
    for endpoint in api_endpoints:
        url = f"{COGNOS_BASE_URL}{endpoint}"
        try:
            response = session.get(url, timeout=10)
            print(f"{endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ Erreichbar!")
                working_endpoints.append(endpoint)
                
                # Prüfe ob JSON
                try:
                    data = response.json()
                    print(f"  JSON Response: {str(data)[:200]}")
                except:
                    print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                    print(f"  Content-Length: {len(response.text)}")
            elif response.status_code == 401:
                print(f"  ⚠️  Authentifizierung erforderlich")
            elif response.status_code == 404:
                print(f"  ❌ Nicht gefunden")
            else:
                print(f"  ⚠️  Status: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Fehler: {e}")
    
    return working_endpoints


def find_bwa_reports(api_base: str = "/api/v1"):
    """
    Findet BWA-Reports in Cognos
    """
    print(f"\n=== BWA-REPORTS SUCHEN ===\n")
    
    # Mögliche Endpunkte für Reports
    report_endpoints = [
        f"{api_base}/reports",
        f"{api_base}/folders",
        f"{api_base}/content",
        f"{api_base}/search",
    ]
    
    bwa_reports = []
    
    for endpoint in report_endpoints:
        url = f"{COGNOS_BASE_URL}{endpoint}"
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint}")
                
                try:
                    data = response.json()
                    print(f"  JSON Response gefunden")
                    
                    # Suche nach BWA-relevanten Reports
                    if isinstance(data, dict):
                        items = data.get('items', data.get('results', data.get('data', [])))
                    elif isinstance(data, list):
                        items = data
                    else:
                        items = []
                    
                    for item in items:
                        if isinstance(item, dict):
                            name = item.get('name', item.get('title', ''))
                            name_lower = name.lower()
                            
                            if any(kw in name_lower for kw in ['bwa', 'guv', 'betriebswirtschaft', 'ergebnis']):
                                bwa_reports.append({
                                    'name': name,
                                    'id': item.get('id', item.get('defaultName', '')),
                                    'type': item.get('type', item.get('class', '')),
                                    'endpoint': endpoint
                                })
                                print(f"  → BWA-Report gefunden: {name}")
                except:
                    # Nicht JSON, zeige Text
                    if 'bwa' in response.text.lower() or 'guv' in response.text.lower():
                        print(f"  → BWA-relevanter Inhalt gefunden")
                        print(f"  {response.text[:500]}")
        except Exception as e:
            print(f"  ❌ Fehler: {e}")
    
    return bwa_reports


def get_report_data(report_id: str, api_base: str = "/api/v1"):
    """
    Holt Daten von einem Cognos Report
    """
    print(f"\n=== REPORT-DATEN ABRUFEN ===\n")
    print(f"Report ID: {report_id}\n")
    
    # Mögliche Endpunkte für Report-Daten
    data_endpoints = [
        f"{api_base}/reports/{report_id}",
        f"{api_base}/reports/{report_id}/data",
        f"{api_base}/reports/{report_id}/execute",
        f"{api_base}/content/{report_id}",
    ]
    
    for endpoint in data_endpoints:
        url = f"{COGNOS_BASE_URL}{endpoint}"
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint}")
                
                try:
                    data = response.json()
                    print(f"  JSON Response:")
                    print(json.dumps(data, indent=2)[:1000])
                    return data
                except:
                    print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                    print(f"  Content (erste 500 Zeichen):")
                    print(response.text[:500])
        except Exception as e:
            print(f"  ❌ Fehler: {e}")
    
    return None


def search_cognos_content(query: str = "BWA", api_base: str = "/api/v1"):
    """
    Sucht nach Inhalten in Cognos
    """
    print(f"\n=== COGNOS INHALT SUCHEN ===\n")
    print(f"Query: {query}\n")
    
    search_endpoints = [
        f"{api_base}/search?q={query}",
        f"{api_base}/content?search={query}",
        f"{api_base}/folders?search={query}",
    ]
    
    for endpoint in search_endpoints:
        url = f"{COGNOS_BASE_URL}{endpoint}"
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint}")
                
                try:
                    data = response.json()
                    print(f"  Ergebnisse: {len(data) if isinstance(data, list) else 'N/A'}")
                    print(json.dumps(data, indent=2)[:1000])
                    return data
                except:
                    print(f"  {response.text[:500]}")
        except Exception as e:
            print(f"  ❌ Fehler: {e}")
    
    return None


def main():
    """
    Hauptfunktion: Führt alle API-Explorationen durch
    """
    print("=" * 80)
    print("IBM COGNOS API EXPLORER")
    print("=" * 80)
    
    # 1. API-Endpunkte testen
    working_endpoints = test_cognos_api()
    
    if working_endpoints:
        api_base = working_endpoints[0]
        print(f"\n✅ API-Basis gefunden: {api_base}")
        
        # 2. BWA-Reports suchen
        bwa_reports = find_bwa_reports(api_base)
        
        # 3. Nach BWA suchen
        search_cognos_content("BWA", api_base)
        
        # 4. Report-Daten abrufen (falls Reports gefunden)
        if bwa_reports:
            for report in bwa_reports[:3]:  # Erste 3 Reports
                get_report_data(report['id'], api_base)
    else:
        print("\n⚠️  Keine API-Endpunkte gefunden")
        print("Cognos könnte eine ältere Version sein oder API ist deaktiviert")
        print("\nAlternative: Direkte Portal-Analyse oder SDK verwenden")
    
    print("\n" + "=" * 80)
    print("✅ Exploration abgeschlossen")
    print("=" * 80)


if __name__ == '__main__':
    main()
