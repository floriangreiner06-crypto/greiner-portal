"""
HAR-Datei Analyse für motocost Dashboard
Analysiert HTTP-Requests aus Browser HAR-Export

TAG: 212
"""

import json
import sys
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

def analyze_har(har_file_path):
    """Analysiert HAR-Datei"""
    
    print("="*60)
    print("HAR-DATEI ANALYSE")
    print("="*60)
    print()
    
    # HAR-Datei laden
    try:
        with open(har_file_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
    except Exception as e:
        print(f"[!] Fehler beim Laden der HAR-Datei: {e}")
        return
    
    print(f"[+] HAR-Datei geladen: {har_file_path}")
    
    # HAR-Struktur analysieren
    if 'log' not in har_data:
        print("[!] Ungültige HAR-Struktur: 'log' fehlt")
        return
    
    log = har_data['log']
    entries = log.get('entries', [])
    
    print(f"[+] {len(entries)} HTTP-Requests gefunden")
    print()
    
    # Kategorisiere Requests
    categories = defaultdict(list)
    api_endpoints = []
    login_requests = []
    dashboard_requests = []
    
    for entry in entries:
        request = entry.get('request', {})
        response = entry.get('response', {})
        url = request.get('url', '')
        method = request.get('method', '')
        status = response.get('status', 0)
        
        # URL analysieren
        parsed = urlparse(url)
        path = parsed.path
        
        # Kategorisieren
        if 'login' in path.lower():
            login_requests.append({
                'url': url,
                'method': method,
                'status': status,
                'request': request,
                'response': response
            })
        elif '/api/' in path:
            api_endpoints.append({
                'url': url,
                'method': method,
                'status': status,
                'path': path,
                'request': request,
                'response': response
            })
        elif 'dashboard' in path.lower() or 'grafana' in path.lower():
            dashboard_requests.append({
                'url': url,
                'method': method,
                'status': status
            })
        
        # Nach Domain kategorisieren
        domain = parsed.netloc
        categories[domain].append({
            'url': url,
            'method': method,
            'status': status
        })
    
    # Ergebnisse ausgeben
    print("="*60)
    print("LOGIN-REQUESTS")
    print("="*60)
    for req in login_requests:
        print(f"\n[{req['method']}] {req['url']}")
        print(f"  Status: {req['status']}")
        
        # Request-Body analysieren
        request = req['request']
        post_data = request.get('postData', {})
        if post_data:
            print(f"  Post-Data: {post_data.get('text', '')[:200]}")
        
        # Request-Headers
        headers = request.get('headers', [])
        print(f"  Headers:")
        for header in headers[:5]:
            print(f"    {header.get('name', '')}: {header.get('value', '')[:100]}")
        
        # Response analysieren
        response = req['response']
        content = response.get('content', {})
        if content:
            text = content.get('text', '')
            if text:
                print(f"  Response (erste 300 Zeichen):")
                print(f"    {text[:300]}")
        
        # Cookies
        cookies = response.get('cookies', [])
        if cookies:
            print(f"  Cookies ({len(cookies)}):")
            for cookie in cookies[:5]:
                print(f"    {cookie.get('name', '')} = {cookie.get('value', '')[:50]}")
    
    print("\n" + "="*60)
    print("API-ENDPOINTS")
    print("="*60)
    
    # Gruppiere nach Endpoint
    endpoints = defaultdict(list)
    for api in api_endpoints:
        endpoints[api['path']].append(api)
    
    for path, requests in sorted(endpoints.items()):
        print(f"\n{path} ({len(requests)} Requests)")
        for req in requests[:3]:  # Erste 3
            print(f"  [{req['method']}] Status: {req['status']}")
            
            # Response-Body analysieren
            response = req['response']
            content = response.get('content', {})
            if content:
                text = content.get('text', '')
                if text:
                    try:
                        # Versuche JSON zu parsen
                        data = json.loads(text)
                        print(f"    Response-Keys: {list(data.keys())[:10]}")
                    except:
                        print(f"    Response: {text[:200]}")
    
    print("\n" + "="*60)
    print("DASHBOARD-REQUESTS")
    print("="*60)
    for req in dashboard_requests[:10]:
        print(f"  [{req['method']}] {req['url']} - Status: {req['status']}")
    
    print("\n" + "="*60)
    print("DOMAIN-ÜBERSICHT")
    print("="*60)
    for domain, requests in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {domain}: {len(requests)} Requests")
    
    # Wichtige Erkenntnisse extrahieren
    print("\n" + "="*60)
    print("WICHTIGE ERKENNTNISSE")
    print("="*60)
    
    # Login-Methode
    if login_requests:
        login_req = login_requests[0]
        print(f"\n1. Login-Methode:")
        print(f"   URL: {login_req['url']}")
        print(f"   Method: {login_req['method']}")
        post_data = login_req['request'].get('postData', {})
        if post_data:
            print(f"   Post-Data-Type: {post_data.get('mimeType', '')}")
            print(f"   Post-Data: {post_data.get('text', '')}")
    
    # API-Endpoints
    if api_endpoints:
        print(f"\n2. API-Endpoints gefunden: {len(api_endpoints)}")
        unique_paths = set(api['path'] for api in api_endpoints)
        print(f"   Eindeutige Endpoints: {len(unique_paths)}")
        for path in sorted(unique_paths)[:10]:
            print(f"     - {path}")
    
    # Cookies nach Login
    if login_requests:
        login_resp = login_requests[0].get('response', {})
        cookies = login_resp.get('cookies', [])
        if cookies:
            print(f"\n3. Cookies nach Login ({len(cookies)}):")
            for cookie in cookies:
                name = cookie.get('name', '')
                value = cookie.get('value', '')
                http_only = cookie.get('httpOnly', False)
                secure = cookie.get('secure', False)
                print(f"   {name}: {value[:30]}... (httpOnly={http_only}, secure={secure})")
    
    # Grafana-spezifische Endpoints
    grafana_apis = [api for api in api_endpoints if 'grafana' in api['path'].lower() or '/api/' in api['path']]
    if grafana_apis:
        print(f"\n4. Grafana-APIs: {len(grafana_apis)}")
        for api in grafana_apis[:10]:
            print(f"   [{api['method']}] {api['path']} - Status: {api['status']}")
    
    # Speichere Analyse-Ergebnisse
    analysis_result = {
        'har_file': har_file_path,
        'total_requests': len(entries),
        'login_requests': len(login_requests),
        'api_endpoints': len(api_endpoints),
        'unique_api_paths': list(unique_paths) if api_endpoints else [],
        'domains': list(categories.keys()),
        'summary': {
            'login_method': login_requests[0]['method'] if login_requests else None,
            'login_url': login_requests[0]['url'] if login_requests else None,
            'api_paths': sorted(unique_paths)[:20] if api_endpoints else []
        }
    }
    
    output_file = har_file_path.replace('.har', '_analysis.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, indent=2, ensure_ascii=False)
    
    print(f"\n[+] Analyse gespeichert: {output_file}")


def main():
    """Hauptfunktion"""
    if len(sys.argv) < 2:
        print("Usage: python3 analyse_har_file.py <har_file_path>")
        print("\nBeispiel:")
        print("  python3 analyse_har_file.py dashboard.motocost.com.har")
        print("  python3 analyse_har_file.py docs/dashboard.motocost.com.har")
        sys.exit(1)
    
    har_file = sys.argv[1]
    analyze_har(har_file)


if __name__ == '__main__':
    main()
