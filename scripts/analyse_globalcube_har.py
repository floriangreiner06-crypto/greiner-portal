#!/usr/bin/env python3
"""
GlobalCube HAR-Datei Analyse
Extrahiert alle relevanten Informationen aus HAR-Datei für Reverse Engineering

Erstellt: TAG 182
"""

import json
import sys
from urllib.parse import urlparse, parse_qs
import re
from collections import defaultdict

HAR_FILE = "/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/globalcube_analyse/f03_bwa_vj_vergleich_alle_beriebe_angehackt.har"


def load_har(har_file):
    """
    Lädt HAR-Datei
    """
    print(f"=== Lade HAR-Datei ===\n")
    print(f"Datei: {har_file}\n")
    
    try:
        with open(har_file, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        log = har_data.get('log', {})
        entries = log.get('entries', [])
        
        print(f"✅ HAR-Datei geladen")
        print(f"Version: {log.get('version', 'N/A')}")
        print(f"Browser: {log.get('browser', {}).get('name', 'N/A')} {log.get('browser', {}).get('version', '')}")
        print(f"Anzahl Requests: {len(entries)}\n")
        
        return har_data, entries
        
    except Exception as e:
        print(f"❌ Fehler beim Laden: {e}")
        import traceback
        traceback.print_exc()
        return None, []


def analyze_login(entries):
    """
    Analysiert Login-Requests
    """
    print("=== LOGIN-ANALYSE ===\n")
    
    login_requests = []
    
    for entry in entries:
        url = entry.get('request', {}).get('url', '')
        method = entry.get('request', {}).get('method', '')
        
        if 'login' in url.lower() or 'auth' in url.lower() or method == 'POST':
            request = entry.get('request', {})
            post_data = request.get('postData', {})
            
            login_info = {
                'url': url,
                'method': method,
                'headers': {h['name']: h['value'] for h in request.get('headers', [])},
                'post_data': post_data.get('text', '') if post_data else None,
                'cookies': request.get('cookies', []),
            }
            
            login_requests.append(login_info)
            
            print(f"✅ {method} {url}")
            if post_data:
                print(f"   Post-Data: {post_data.get('text', '')[:200]}")
            print()
    
    return login_requests


def analyze_bwa_requests(entries):
    """
    Analysiert BWA-relevante Requests
    """
    print("=== BWA-REQUESTS ANALYSE ===\n")
    
    bwa_requests = []
    
    for entry in entries:
        url = entry.get('request', {}).get('url', '')
        method = entry.get('request', {}).get('method', '')
        
        # Prüfe ob BWA-relevant
        bwa_keywords = ['bwa', 'guv', 'f.03', 'report', 'cognos', 'betriebswirtschaft', 
                       'ergebnis', 'kosten', 'umsatz', 'vorjahres']
        
        if any(kw in url.lower() for kw in bwa_keywords):
            request = entry.get('request', {})
            response = entry.get('response', {})
            
            # Parse URL
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            # Extrahiere Response
            response_content = response.get('content', {})
            response_text = response_content.get('text', '')
            
            bwa_info = {
                'url': url,
                'method': method,
                'status': response.get('status', 0),
                'content_type': response_content.get('mimeType', ''),
                'params': params,
                'headers': {h['name']: h['value'] for h in request.get('headers', [])},
                'response_size': response_content.get('size', 0),
                'has_response': bool(response_text),
            }
            
            bwa_requests.append(bwa_info)
            
            print(f"✅ {method} {url}")
            print(f"   Status: {response.get('status', 0)}")
            print(f"   Content-Type: {response_content.get('mimeType', '')}")
            print(f"   Response-Größe: {response_content.get('size', 0)} bytes")
            
            if params:
                print(f"   Parameter:")
                for key, values in list(params.items())[:10]:
                    print(f"     {key} = {', '.join(values)}")
            
            # Prüfe ob HTML oder JSON
            if 'html' in response_content.get('mimeType', '').lower():
                print(f"   → HTML-Response (kann BWA-Daten enthalten)")
            elif 'json' in response_content.get('mimeType', '').lower():
                print(f"   → JSON-Response")
                if response_text:
                    try:
                        json_data = json.loads(response_text)
                        print(f"   → JSON-Daten gefunden (Keys: {list(json_data.keys())[:5]})")
                    except:
                        pass
            
            print()
    
    print(f"\nGefundene BWA-Requests: {len(bwa_requests)}\n")
    
    return bwa_requests


def extract_report_urls(entries):
    """
    Extrahiert Report-URLs und Parameter
    """
    print("=== REPORT-URLS EXTRAHIEREN ===\n")
    
    report_urls = []
    
    for entry in entries:
        url = entry.get('request', {}).get('url', '')
        
        # Prüfe ob Report-URL
        if 'report' in url.lower() or 'cognos' in url.lower() or 'bi' in url.lower():
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            report_urls.append({
                'url': url,
                'base_url': f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}",
                'params': params,
            })
    
    # Gruppiere nach Base-URL
    grouped = defaultdict(list)
    for report in report_urls:
        grouped[report['base_url']].append(report)
    
    print(f"Gefundene Report-URLs: {len(report_urls)}\n")
    
    for base_url, reports in list(grouped.items())[:10]:
        print(f"Base-URL: {base_url}")
        print(f"  Anzahl Varianten: {len(reports)}")
        if reports:
            print(f"  Beispiel-Parameter:")
            for key, values in list(reports[0]['params'].items())[:5]:
                print(f"    {key} = {', '.join(values)}")
        print()
    
    return report_urls


def extract_bwa_values_from_responses(entries):
    """
    Extrahiert BWA-Werte aus Response-Bodies
    """
    print("=== BWA-WERTE AUS RESPONSES EXTRAHIEREN ===\n")
    
    bwa_values = {}
    
    for entry in entries:
        url = entry.get('request', {}).get('url', '')
        response = entry.get('response', {})
        response_content = response.get('content', {})
        response_text = response_content.get('text', '')
        
        if not response_text:
            continue
        
        # Suche nach BWA-Werten im Text
        # Pattern: Zahlen in der Nähe von BWA-Begriffen
        patterns = [
            r'(?:Betriebsergebnis|Betriebs-Ergebnis)[:\s]+([\d.,\s-]+)',
            r'(?:Unternehmensergebnis|Unternehmens-Ergebnis)[:\s]+([\d.,\s-]+)',
            r'(?:Direkte\s+Kosten)[:\s]+([\d.,\s-]+)',
            r'(?:Indirekte\s+Kosten)[:\s]+([\d.,\s-]+)',
            r'(?:Variable\s+Kosten)[:\s]+([\d.,\s-]+)',
            r'(?:Umsatzerlöse|Umsatz)[:\s]+([\d.,\s-]+)',
            r'(?:Einsatzwerte|Einsatz)[:\s]+([\d.,\s-]+)',
        ]
        
        found_values = {}
        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.I)
            if matches:
                key = pattern.split('(')[0].strip('?:')
                found_values[key] = matches[:5]  # Erste 5 Matches
        
        if found_values:
            bwa_values[url] = found_values
            print(f"✅ Werte gefunden in: {url[:100]}")
            for key, values in found_values.items():
                print(f"   {key}: {values[:3]}")
            print()
    
    return bwa_values


def extract_javascript_config(entries):
    """
    Extrahiert JavaScript-Konfiguration mit Filter-Logik
    """
    print("=== JAVASCRIPT-KONFIGURATION ===\n")
    
    js_configs = []
    
    for entry in entries:
        url = entry.get('request', {}).get('url', '')
        response_content = entry.get('response', {}).get('content', {})
        response_text = response_content.get('text', '')
        
        if 'javascript' in response_content.get('mimeType', '').lower() or '.js' in url.lower():
            # Suche nach Filter-Logik
            filter_patterns = [
                r'(?:filter|konto|account|411|489|410021|ausschluss)[\s:=]+([^;,\n]+)',
                r'(?:nominal_account_number|konto)[\s]*(?:BETWEEN|IN|>=|<=|>|<|=)[\s]*([^;,\n]+)',
                r'(?:branch_number|subsidiary)[\s=]+([0-9]+)',
            ]
            
            for pattern in filter_patterns:
                matches = re.findall(pattern, response_text, re.I)
                if matches:
                    js_configs.append({
                        'url': url,
                        'pattern': pattern,
                        'matches': matches[:10]
                    })
                    print(f"✅ Filter-Logik gefunden in: {url}")
                    print(f"   Pattern: {pattern[:50]}")
                    print(f"   Matches: {len(matches)}")
                    print()
    
    return js_configs


def main():
    """
    Hauptfunktion
    """
    print("=" * 80)
    print("GlobalCube HAR-Datei Analyse")
    print("=" * 80)
    print()
    
    # 1. Lade HAR-Datei
    har_data, entries = load_har(HAR_FILE)
    
    if not har_data:
        print("❌ HAR-Datei konnte nicht geladen werden")
        return
    
    # 2. Analysiere Login
    login_requests = analyze_login(entries)
    
    # 3. Analysiere BWA-Requests
    bwa_requests = analyze_bwa_requests(entries)
    
    # 4. Extrahiere Report-URLs
    report_urls = extract_report_urls(entries)
    
    # 5. Extrahiere BWA-Werte
    bwa_values = extract_bwa_values_from_responses(entries)
    
    # 6. Extrahiere JavaScript-Konfiguration
    js_configs = extract_javascript_config(entries)
    
    # 7. Speichere Ergebnisse
    results = {
        'login_requests': login_requests,
        'bwa_requests': bwa_requests,
        'report_urls': report_urls,
        'bwa_values': bwa_values,
        'js_configs': js_configs,
    }
    
    output_file = "/tmp/globalcube_har_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("=" * 80)
    print(f"✅ Analyse abgeschlossen")
    print(f"💾 Ergebnisse gespeichert: {output_file}")
    print("=" * 80)
    
    # 8. Zusammenfassung
    print("\n=== ZUSAMMENFASSUNG ===\n")
    print(f"Login-Requests: {len(login_requests)}")
    print(f"BWA-Requests: {len(bwa_requests)}")
    print(f"Report-URLs: {len(report_urls)}")
    print(f"BWA-Werte gefunden: {len(bwa_values)}")
    print(f"JavaScript-Konfigurationen: {len(js_configs)}")


if __name__ == '__main__':
    main()
