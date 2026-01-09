#!/usr/bin/env python3
"""
HAR-Datei Analyse für GUDAT Bild-Download
=========================================
TAG 173: Findet Download-URLs und Request-Struktur für Bilder aus GUDAT
"""

import json
import sys
from pathlib import Path

def find_har_file():
    """Sucht HAR-Datei in verschiedenen Pfaden"""
    har_paths = [
        '/mnt/greiner-portal-sync/*bild*.har',
        '/mnt/greiner-portal-sync/*download*.har',
        '/mnt/greiner-portal-sync/*image*.har',
        '/mnt/greiner-portal-sync/*document*.har',
        '/opt/greiner-portal/*bild*.har',
    ]
    
    import glob
    for pattern in har_paths:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    
    return None

def analyze_har(har_path):
    """Analysiert HAR-Datei und extrahiert Bild-Download-Informationen"""
    print("="*80)
    print("HAR-DATEI ANALYSE: GUDAT Bild-Download")
    print("="*80)
    print()
    
    with open(har_path, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    entries = har.get('log', {}).get('entries', [])
    print(f"✅ {len(entries)} HTTP-Requests gefunden")
    print()
    
    # 1. Suche Bild-Download-Requests
    image_requests = []
    for entry in entries:
        request = entry.get('request', {})
        response = entry.get('response', {})
        url = request.get('url', '')
        method = request.get('method', '')
        content_type = response.get('content', {}).get('mimeType', '')
        
        # Prüfe auf Bild-Requests
        if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']) or \
           content_type.startswith('image/'):
            image_requests.append({
                'url': url,
                'method': method,
                'headers': request.get('headers', []),
                'cookies': request.get('cookies', []),
                'content_type': content_type,
                'status': response.get('status', 0)
            })
    
    print(f"✅ {len(image_requests)} Bild-Request(s) gefunden")
    print()
    
    if image_requests:
        print("="*80)
        print("BILD-DOWNLOAD-REQUESTS")
        print("="*80)
        print()
        
        for idx, req in enumerate(image_requests, 1):
            print(f"[{idx}] {req['method']} {req['url']}")
            print(f"    Status: {req['status']}")
            print(f"    Content-Type: {req['content_type']}")
            
            # Wichtige Headers
            headers = {h['name']: h['value'] for h in req['headers']}
            important_headers = ['Authorization', 'Cookie', 'X-XSRF-TOKEN', 'Referer']
            for header_name in important_headers:
                if header_name in headers:
                    value = headers[header_name]
                    if len(value) > 100:
                        value = value[:100] + '...'
                    print(f"    {header_name}: {value}")
            
            print()
    
    # 2. Suche GraphQL-Queries für Dokumente/Bilder
    graphql_requests = []
    for entry in entries:
        request = entry.get('request', {})
        url = request.get('url', '')
        method = request.get('method', '')
        
        if method == 'POST' and ('graphql' in url.lower() or 'api' in url.lower()):
            post_data = request.get('postData', {})
            if post_data:
                text = post_data.get('text', '')
                if 'document' in text.lower() or 'image' in text.lower() or 'file' in text.lower():
                    try:
                        query_data = json.loads(text) if text else {}
                        graphql_requests.append({
                            'url': url,
                            'query': query_data.get('query', ''),
                            'variables': query_data.get('variables', {}),
                            'response': entry.get('response', {}).get('content', {}).get('text', '')
                        })
                    except:
                        pass
    
    if graphql_requests:
        print("="*80)
        print("GRAPHQL-QUERIES FÜR DOKUMENTE/BILDER")
        print("="*80)
        print()
        
        for idx, req in enumerate(graphql_requests, 1):
            print(f"[{idx}] Query:")
            print(req['query'][:500])
            print()
            
            if req.get('variables'):
                print("Variables:")
                print(json.dumps(req['variables'], indent=2))
                print()
            
            # Versuche Response zu parsen
            try:
                response_data = json.loads(req['response'])
                if 'data' in response_data:
                    print("Response (data):")
                    print(json.dumps(response_data['data'], indent=2)[:1000])
                    print()
            except:
                pass
    
    # 3. Zusammenfassung
    print("="*80)
    print("ZUSAMMENFASSUNG")
    print("="*80)
    print()
    
    if image_requests:
        print("✅ Bild-Download-URLs gefunden:")
        for req in image_requests[:3]:
            print(f"   - {req['url']}")
        print()
        print("💡 Implementierung:")
        print("   1. Verwende GUDAT-Session (mit Cookies)")
        print("   2. GET-Request auf Bild-URL")
        print("   3. Headers: X-XSRF-TOKEN, Cookie")
    else:
        print("⚠️  Keine direkten Bild-Download-URLs gefunden")
        print("   → Möglicherweise werden Bilder über GraphQL-API geladen")
    
    if graphql_requests:
        print()
        print("✅ GraphQL-Queries für Dokumente gefunden")
        print("   → Prüfe Response auf URL-Felder")


def main():
    har_path = find_har_file()
    
    if not har_path:
        print("❌ Keine HAR-Datei gefunden")
        print()
        print("Bitte HAR-Datei ablegen in:")
        print("  - /mnt/greiner-portal-sync/*bild*.har")
        print("  - /mnt/greiner-portal-sync/*download*.har")
        print()
        print("Oder Pfad als Argument übergeben:")
        print("  python3 analyse_gudat_bild_download.py /path/to/file.har")
        return
    
    if len(sys.argv) > 1:
        har_path = sys.argv[1]
    
    if not Path(har_path).exists():
        print(f"❌ HAR-Datei nicht gefunden: {har_path}")
        return
    
    analyze_har(har_path)


if __name__ == '__main__':
    main()
