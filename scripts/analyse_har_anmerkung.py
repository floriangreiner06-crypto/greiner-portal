#!/usr/bin/env python3
"""
Analysiert HAR-Datei für Anmerkung/Diagnose-Informationen
TAG 212: Findet die GraphQL-Query die die "Anmerkung" holt
"""

import json
import sys

def analyze_har(har_path):
    with open(har_path, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    entries = har.get('log', {}).get('entries', [])
    print(f"Total entries: {len(entries)}\n")
    
    found_queries = []
    
    for i, entry in enumerate(entries):
        req = entry.get('request', {})
        resp = entry.get('response', {})
        content = resp.get('content', {})
        text = content.get('text', '')
        
        if text:
            try:
                resp_data = json.loads(text)
                # Prüfe ob es ein Array ist (GraphQL Batch)
                if isinstance(resp_data, list):
                    for item in resp_data:
                        if isinstance(item, dict) and 'data' in item:
                            data = item['data']
                            # Suche nach workshopTask mit description
                            if 'workshopTask' in str(data) or ('dossier' in str(data) and 'description' in str(data)):
                                post_data = req.get('postData', {})
                                if post_data:
                                    query_text = post_data.get('text', '')
                                    if query_text:
                                        try:
                                            query_data = json.loads(query_text)
                                            found_queries.append({
                                                'entry': i,
                                                'operation': query_data.get('operationName', 'N/A'),
                                                'query': query_data.get('query', ''),
                                                'variables': query_data.get('variables', {}),
                                                'response': data
                                            })
                                        except:
                                            pass
            except:
                pass
    
    print(f"Found {len(found_queries)} relevant queries\n")
    
    for i, req in enumerate(found_queries, 1):
        print("="*80)
        print(f"QUERY #{i}")
        print("="*80)
        print(f"Operation: {req['operation']}")
        print(f"\nQuery:")
        print(req['query'])
        print(f"\nVariables:")
        print(json.dumps(req['variables'], indent=2))
        
        # Extrahiere description aus Response
        response = req['response']
        if 'workshopTask' in response:
            task = response.get('workshopTask', {})
            desc = task.get('description', '')
            if desc:
                print(f"\n✅ Description gefunden:")
                print(desc[:500])
        elif 'dossier' in response:
            dossier = response.get('dossier', {})
            tasks = dossier.get('workshopTasks', [])
            if tasks:
                print(f"\n✅ {len(tasks)} Tasks gefunden:")
                for j, task in enumerate(tasks, 1):
                    desc = task.get('description', '')
                    if desc:
                        print(f"\n  Task {j} (ID: {task.get('id')}):")
                        print(f"  Description: {desc[:300]}")
        print()

if __name__ == '__main__':
    har_path = sys.argv[1] if len(sys.argv) > 1 else '/mnt/greiner-portal-sync/werkstattplanung_kachel_bild-geoeffnet.har'
    analyze_har(har_path)
