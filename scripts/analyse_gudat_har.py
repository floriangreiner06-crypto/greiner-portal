#!/usr/bin/env python3
"""
HAR-Datei Analyse für GUDAT "Anmerkung"-Feld
=============================================
TAG 173: Findet GraphQL-Queries für Mechaniker-Notizen in GUDAT
"""

import json
import sys
import re
from pathlib import Path

def find_har_file():
    """Sucht HAR-Datei in verschiedenen Pfaden"""
    har_paths = [
        '/mnt/greiner-portal-sync/werkstattplanung_kachel_anmerkung_diag.har',
        '/mnt/greiner-portal-sync/Downloads/werkstattplanung_kachel_anmerkung_diag.har',
        '/opt/greiner-portal/werkstattplanung_kachel_anmerkung_diag.har',
        '/opt/greiner-portal/werkstattplanung_kachel_anmerkung_diag.har',
    ]
    
    for path in har_paths:
        if Path(path).exists():
            return path
    
    return None

def analyze_har(har_path):
    """Analysiert HAR-Datei und extrahiert GraphQL-Queries"""
    print("="*80)
    print("HAR-DATEI ANALYSE: GUDAT 'Anmerkung'-Feld")
    print("="*80)
    print()
    
    with open(har_path, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    entries = har.get('log', {}).get('entries', [])
    print(f"✅ {len(entries)} HTTP-Requests gefunden")
    print()
    
    # 1. Suche GraphQL-Requests
    graphql_requests = []
    for entry in entries:
        request = entry.get('request', {})
        url = request.get('url', '')
        method = request.get('method', '')
        
        # Prüfe POST-Requests (GraphQL)
        if method == 'POST':
            post_data = request.get('postData', {})
            if post_data:
                text = post_data.get('text', '')
                if 'graphql' in url.lower() or 'query' in text or 'mutation' in text:
                    try:
                        query_data = json.loads(text) if text else {}
                        graphql_requests.append({
                            'url': url,
                            'method': method,
                            'query': query_data.get('query', ''),
                            'variables': query_data.get('variables', {}),
                            'operationName': query_data.get('operationName', '')
                        })
                    except:
                        pass
    
    print(f"✅ {len(graphql_requests)} GraphQL-Requests gefunden")
    print()
    
    # 2. Suche nach "Anmerkung" oder ähnlichen Feldern
    print("="*80)
    print("SUCHE NACH 'ANMERKUNG'-FELD")
    print("="*80)
    print()
    
    anmerkung_queries = []
    for req in graphql_requests:
        query = req.get('query', '')
        if any(term in query.lower() for term in ['anmerkung', 'note', 'comment', 'remark', 'description']):
            anmerkung_queries.append(req)
    
    if anmerkung_queries:
        print(f"✅ {len(anmerkung_queries)} Query(s) mit 'Anmerkung'-bezogenen Feldern gefunden:")
        print()
        
        for i, req in enumerate(anmerkung_queries, 1):
            print(f"{'='*80}")
            print(f"QUERY #{i}")
            print(f"{'='*80}")
            print(f"URL: {req['url']}")
            print(f"Operation: {req.get('operationName', 'N/A')}")
            print()
            print("Query:")
            print(req['query'])
            print()
            if req.get('variables'):
                print("Variables:")
                print(json.dumps(req['variables'], indent=2))
                print()
    else:
        print("⚠️  Keine Queries mit 'Anmerkung' gefunden")
        print("   Zeige alle GraphQL-Queries:")
        print()
        for i, req in enumerate(graphql_requests[:5], 1):
            print(f"{'='*80}")
            print(f"QUERY #{i}")
            print(f"{'='*80}")
            print(f"URL: {req['url']}")
            print(f"Operation: {req.get('operationName', 'N/A')}")
            print()
            print("Query (erste 500 Zeichen):")
            print(req['query'][:500])
            print()
    
    # 3. Suche nach Responses mit "Anmerkung"-Daten
    print("="*80)
    print("SUCHE NACH RESPONSES MIT 'ANMERKUNG'-DATEN")
    print("="*80)
    print()
    
    anmerkung_responses = []
    for entry in entries:
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        
        if text and any(term in text.lower() for term in ['anmerkung', 'note', 'comment', 'remark', 'c162078', 'fehlerspeicher']):
            try:
                response_data = json.loads(text)
                anmerkung_responses.append({
                    'url': entry.get('request', {}).get('url', ''),
                    'data': response_data
                })
            except:
                pass
    
    if anmerkung_responses:
        print(f"✅ {len(anmerkung_responses)} Response(s) mit 'Anmerkung'-Daten gefunden:")
        print()
        
        for i, resp in enumerate(anmerkung_responses[:3], 1):
            print(f"{'='*80}")
            print(f"RESPONSE #{i}")
            print(f"{'='*80}")
            print(f"URL: {resp['url']}")
            print()
            print("Data (erste 1000 Zeichen):")
            print(json.dumps(resp['data'], indent=2, ensure_ascii=False)[:1000])
            print()
    else:
        print("⚠️  Keine Responses mit 'Anmerkung'-Daten gefunden")
    
    # 4. Extrahiere Feldnamen
    print("="*80)
    print("EXTRAHIERTE FELDNAMEN")
    print("="*80)
    print()
    
    all_fields = set()
    for req in graphql_requests:
        query = req.get('query', '')
        # Suche nach Feldnamen in GraphQL-Query
        fields = re.findall(r'(\w+)\s*\{', query)
        all_fields.update(fields)
    
    # Filtere relevante Felder
    relevant_fields = [f for f in all_fields if any(term in f.lower() for term in ['note', 'comment', 'remark', 'anmerkung', 'description', 'text'])]
    
    if relevant_fields:
        print("✅ Relevante Felder gefunden:")
        for field in sorted(relevant_fields):
            print(f"   - {field}")
    else:
        print("⚠️  Keine relevanten Felder gefunden")
    
    print()
    print("="*80)
    print("ANALYSE ABGESCHLOSSEN")
    print("="*80)

def main():
    har_path = find_har_file()
    
    if not har_path:
        print("❌ HAR-Datei nicht gefunden!")
        print()
        print("Bitte kopieren Sie die Datei in einen dieser Pfade:")
        print("  - /mnt/greiner-portal-sync/werkstattplanung_kachel_anmerkung_diag.har")
        print("  - /opt/greiner-portal/werkstattplanung_kachel_anmerkung_diag.har")
        print()
        print("Oder geben Sie den Pfad als Argument an:")
        print("  python3 analyse_gudat_har.py /path/to/file.har")
        sys.exit(1)
    
    print(f"✅ HAR-Datei gefunden: {har_path}")
    print()
    
    analyze_har(har_path)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        har_path = sys.argv[1]
        if Path(har_path).exists():
            analyze_har(har_path)
        else:
            print(f"❌ Datei nicht gefunden: {har_path}")
            sys.exit(1)
    else:
        main()
