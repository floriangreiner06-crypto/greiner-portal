"""
Analysiert Query-Requests aus motocost HAR-Datei
Extrahiert Datenstruktur und Query-Details

TAG: 212
"""

import json
import sys

def analyze_queries(har_file_path):
    """Analysiert Query-Requests aus HAR"""
    
    print("="*60)
    print("QUERY-ANALYSE")
    print("="*60)
    print()
    
    # Lade HAR-Datei
    with open(har_file_path, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    # Finde alle /api/ds/query Requests
    queries = []
    for entry in har['log']['entries']:
        url = entry['request'].get('url', '')
        if '/api/ds/query' in url:
            method = entry['request'].get('method', '')
            status = entry['response'].get('status', 0)
            
            # Request-Body
            post_data = entry['request'].get('postData', {})
            request_body = post_data.get('text', '')
            
            # Response
            response_content = entry['response'].get('content', {})
            response_text = response_content.get('text', '')
            
            # Cookies
            cookies = entry['response'].get('cookies', [])
            
            queries.append({
                'url': url,
                'method': method,
                'status': status,
                'request_body': request_body,
                'response': response_text,
                'cookies': cookies
            })
    
    print(f'Gefundene Query-Requests: {len(queries)}\n')
    
    # Analysiere jeden Query
    all_fields = set()
    query_details = []
    
    for i, query in enumerate(queries, 1):
        print(f'='*60)
        print(f'QUERY {i}')
        print(f'='*60)
        print(f'URL: {query["url"]}')
        print(f'Status: {query["status"]}')
        
        # Request-Body analysieren
        if query['request_body']:
            try:
                req_data = json.loads(query['request_body'])
                print(f'\nRequest-Body:')
                print(f'  Queries: {len(req_data.get("queries", []))}')
                
                query_info = {
                    'query_num': i,
                    'queries': []
                }
                
                for j, q in enumerate(req_data.get('queries', [])):
                    ref_id = q.get('refId', '')
                    datasource = q.get('datasource', {})
                    ds_uid = datasource.get('uid', '')
                    expr = q.get('expr', '')
                    raw_sql = q.get('rawSql', '')
                    
                    print(f'    Query {j+1} (RefId: {ref_id}):')
                    print(f'      Datasource UID: {ds_uid}')
                    if expr:
                        print(f'      Expr: {expr[:200]}')
                    if raw_sql:
                        print(f'      RawSql: {raw_sql[:200]}')
                    
                    query_info['queries'].append({
                        'refId': ref_id,
                        'datasource': ds_uid,
                        'expr': expr,
                        'rawSql': raw_sql
                    })
                
                query_details.append(query_info)
                
            except Exception as e:
                print(f'  Request-Body (raw, erste 300 Zeichen):')
                print(f'    {query["request_body"][:300]}')
                print(f'  Parse-Fehler: {e}')
        
        # Response analysieren
        if query['response']:
            try:
                resp_data = json.loads(query['response'])
                print(f'\nResponse:')
                results = resp_data.get('results', {})
                print(f'  Results: {len(results)}')
                
                for ref_id, result in list(results.items())[:3]:
                    print(f'    {ref_id}:')
                    frames = result.get('frames', [])
                    print(f'      Frames: {len(frames)}')
                    
                    for frame_idx, frame in enumerate(frames[:2]):
                        schema = frame.get('schema', {})
                        fields = schema.get('fields', [])
                        print(f'      Frame {frame_idx+1}: {len(fields)} Fields')
                        
                        for field in fields[:10]:
                            name = field.get('name', '')
                            ftype = field.get('type', '')
                            all_fields.add(name)
                            print(f'        - {name}: {ftype}')
                        
                        # Daten (erste Zeile)
                        data = frame.get('data', {})
                        if data:
                            print(f'      Data-Keys: {list(data.keys())[:5]}')
                            # Erste Werte
                            for key in list(data.keys())[:3]:
                                values = data.get(key, [])
                                if values:
                                    print(f'        {key}[0]: {values[0] if len(values) > 0 else "N/A"}')
                
            except Exception as e:
                print(f'  Response (raw, erste 500 Zeichen):')
                print(f'    {query["response"][:500]}')
                print(f'  Parse-Fehler: {e}')
        
        print()
    
    # Zusammenfassung
    print("="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)
    print(f"Alle gefundenen Felder ({len(all_fields)}):")
    for field in sorted(all_fields):
        print(f"  - {field}")
    
    # Speichere Details
    output = {
        'total_queries': len(queries),
        'all_fields': sorted(list(all_fields)),
        'query_details': query_details
    }
    
    output_file = har_file_path.replace('.har', '_queries_analysis.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n[+] Query-Analyse gespeichert: {output_file}")
    
    return output


if __name__ == '__main__':
    har_file = sys.argv[1] if len(sys.argv) > 1 else '/mnt/greiner-portal-sync/docs/dashboard.motocost.com.har'
    analyze_queries(har_file)
