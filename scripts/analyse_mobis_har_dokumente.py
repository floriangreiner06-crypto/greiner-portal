#!/usr/bin/env python3
"""
Analysiert Mobis EDMOS HAR-Datei auf Dokumente/Rechnungen-Endpunkte
"""

import json
import sys
from collections import defaultdict

har_file = '/mnt/greiner-portal-sync/Hyundai_Garantie/edos.mobiseurope.com.har'

try:
    with open(har_file, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    entries = har_data.get('log', {}).get('entries', [])
    
    print('=' * 80)
    print('MOBIS EDMOS HAR-ANALYSE - DOKUMENTE/RECHNUNGEN')
    print('=' * 80)
    print(f'\nGefundene Requests: {len(entries)}\n')
    
    # Kategorien
    document_endpoints = []
    download_endpoints = []
    pdf_endpoints = []
    invoice_endpoints = []
    delivery_endpoints = []
    print_endpoints = []
    export_endpoints = []
    all_relevant = []
    
    for entry in entries:
        request = entry.get('request', {})
        response = entry.get('response', {})
        url = request.get('url', '')
        method = request.get('method', '')
        status = response.get('status', 0)
        
        # Prüfe auf Dokumente/Rechnungen
        url_lower = url.lower()
        
        if any(keyword in url_lower for keyword in ['document', 'dokument', 'file', 'attachment']):
            document_endpoints.append({
                'url': url,
                'method': method,
                'status': status,
                'request': request
            })
        
        if 'pdf' in url_lower:
            pdf_endpoints.append({
                'url': url,
                'method': method,
                'status': status,
                'request': request
            })
        
        if any(keyword in url_lower for keyword in ['invoice', 'rechnung', 'bill']):
            invoice_endpoints.append({
                'url': url,
                'method': method,
                'status': status,
                'request': request
            })
        
        if any(keyword in url_lower for keyword in ['delivery', 'lieferung', 'lieferschein', 'deliverynote']):
            delivery_endpoints.append({
                'url': url,
                'method': method,
                'status': status,
                'request': request
            })
        
        if any(keyword in url_lower for keyword in ['download', 'downloadfile', 'getfile']):
            download_endpoints.append({
                'url': url,
                'method': method,
                'status': status,
                'request': request
            })
        
        if any(keyword in url_lower for keyword in ['print', 'druck', 'drucken']):
            print_endpoints.append({
                'url': url,
                'method': method,
                'status': status,
                'request': request
            })
        
        if any(keyword in url_lower for keyword in ['export', 'exportfile']):
            export_endpoints.append({
                'url': url,
                'method': method,
                'status': status,
                'request': request
            })
        
        # Alle relevanten
        if any(keyword in url_lower for keyword in ['order', 'bestellung', 'part', 'teil', 'delivery', 
                                                     'lieferung', 'invoice', 'rechnung', 'document', 
                                                     'dokument', 'pdf', 'print', 'export', 'download']):
            all_relevant.append({
                'url': url,
                'method': method,
                'status': status,
                'request': request,
                'response': response
            })
    
    # Ausgabe
    print('\n📄 DOKUMENT-ENDPUNKTE:')
    if document_endpoints:
        for ep in document_endpoints[:15]:
            print(f'  {ep["method"]} {ep["url"][:120]} (Status: {ep["status"]})')
    else:
        print('  Keine gefunden')
    
    print('\n📋 PDF-ENDPUNKTE:')
    if pdf_endpoints:
        for ep in pdf_endpoints[:15]:
            print(f'  {ep["method"]} {ep["url"][:120]} (Status: {ep["status"]})')
    else:
        print('  Keine gefunden')
    
    print('\n🧾 RECHNUNGS-ENDPUNKTE:')
    if invoice_endpoints:
        for ep in invoice_endpoints[:15]:
            print(f'  {ep["method"]} {ep["url"][:120]} (Status: {ep["status"]})')
    else:
        print('  Keine gefunden')
    
    print('\n📦 LIEFERSCHEIN-ENDPUNKTE:')
    if delivery_endpoints:
        for ep in delivery_endpoints[:15]:
            print(f'  {ep["method"]} {ep["url"][:120]} (Status: {ep["status"]})')
    else:
        print('  Keine gefunden')
    
    print('\n⬇️ DOWNLOAD-ENDPUNKTE:')
    if download_endpoints:
        for ep in download_endpoints[:15]:
            print(f'  {ep["method"]} {ep["url"][:120]} (Status: {ep["status"]})')
    else:
        print('  Keine gefunden')
    
    print('\n🖨️ PRINT-ENDPUNKTE:')
    if print_endpoints:
        for ep in print_endpoints[:15]:
            print(f'  {ep["method"]} {ep["url"][:120]} (Status: {ep["status"]})')
    else:
        print('  Keine gefunden')
    
    print('\n📤 EXPORT-ENDPUNKTE:')
    if export_endpoints:
        for ep in export_endpoints[:15]:
            print(f'  {ep["method"]} {ep["url"][:120]} (Status: {ep["status"]})')
    else:
        print('  Keine gefunden')
    
    # Gruppiere nach Basis-URL
    print('\n\n🔍 ALLE RELEVANTEN ENDPUNKTE (gruppiert):')
    grouped = defaultdict(list)
    for ep in all_relevant:
        # Extrahiere Basis-Pfad
        if 'edos.mobiseurope.com' in ep['url']:
            path = ep['url'].split('edos.mobiseurope.com')[-1].split('?')[0]
            grouped[path].append(ep)
    
    print(f'\nGefundene eindeutige Pfade: {len(grouped)}\n')
    for path, endpoints in sorted(grouped.items())[:30]:
        methods = set(e['method'] for e in endpoints)
        methods_str = ', '.join(methods)
        print(f'  {path}')
        print(f'    Methoden: {methods_str}')
        print(f'    Anzahl: {len(endpoints)}')
        
        # Zeige Request-Body für POST-Requests
        for ep in endpoints[:2]:  # Erste 2
            if ep['method'] == 'POST':
                post_data = ep.get('request', {}).get('postData', {})
                if post_data:
                    text = post_data.get('text', '')
                    if text:
                        # Zeige ersten 200 Zeichen
                        print(f'    POST Body: {text[:200]}...')
        print()
    
    # Detaillierte Analyse der vielversprechendsten Endpunkte
    print('\n\n🎯 DETAILLIERTE ANALYSE - VIELVERSPRECHENDSTE ENDPUNKTE:\n')
    
    # Suche nach Endpunkten mit PDF/Download
    promising = []
    for ep in all_relevant:
        url = ep['url'].lower()
        if any(keyword in url for keyword in ['pdf', 'download', 'print', 'export', 'document', 
                                               'invoice', 'delivery', 'rechnung', 'lieferschein']):
            promising.append(ep)
    
    for ep in promising[:10]:
        print(f'\n{ep["method"]} {ep["url"]}')
        print(f'  Status: {ep["status"]}')
        
        # Request Headers
        headers = ep.get('request', {}).get('headers', [])
        print('  Request Headers:')
        for h in headers[:5]:
            print(f'    {h.get("name")}: {h.get("value")}')
        
        # POST Data
        if ep['method'] == 'POST':
            post_data = ep.get('request', {}).get('postData', {})
            if post_data:
                text = post_data.get('text', '')
                if text:
                    print(f'  POST Body: {text[:300]}')
        
        # Response Content-Type
        response_headers = ep.get('response', {}).get('headers', [])
        content_type = None
        for h in response_headers:
            if h.get('name', '').lower() == 'content-type':
                content_type = h.get('value', '')
                break
        if content_type:
            print(f'  Response Content-Type: {content_type}')
        
        print()

except Exception as e:
    print(f'Fehler: {e}')
    import traceback
    traceback.print_exc()
