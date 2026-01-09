#!/usr/bin/env python3
"""
Detaillierte Analyse der Mobis HAR-Datei auf Dokumente/Rechnungen
"""

import json
import base64
import re

har_file = '/mnt/greiner-portal-sync/Hyundai_Garantie/edos.mobiseurope.com.har'

with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

entries = har_data.get('log', {}).get('entries', [])

print('=' * 80)
print('RESPONSE-ANALYSE - PDF/DOKUMENTE')
print('=' * 80)

pdf_found = False
for entry in entries:
    request = entry.get('request', {})
    response = entry.get('response', {})
    url = request.get('url', '')
    method = request.get('method', '')
    status = response.get('status', 0)
    
    # Prüfe Content-Type
    headers = response.get('headers', [])
    content_type = None
    for h in headers:
        if h.get('name', '').lower() == 'content-type':
            content_type = h.get('value', '')
            break
    
    # Prüfe auf PDF oder Dokument
    if content_type and ('pdf' in content_type.lower() or 'application/octet-stream' in content_type.lower()):
        pdf_found = True
        print(f'\n🎯 PDF/DOKUMENT GEFUNDEN:')
        print(f'   {method} {url}')
        print(f'   Status: {status}')
        print(f'   Content-Type: {content_type}')
        
        # Prüfe Response-Body
        content = response.get('content', {})
        text = content.get('text', '')
        if text:
            # Prüfe ob Base64
            if content.get('encoding') == 'base64':
                try:
                    decoded = base64.b64decode(text)
                    print(f'   Größe: {len(decoded)} bytes')
                    # Prüfe PDF-Magic-Number
                    if decoded[:4] == b'%PDF':
                        print('   ✅ PDF-Datei erkannt!')
                except:
                    pass
            else:
                print(f'   Text-Länge: {len(text)}')
    
    # Prüfe auf Download-Header
    for h in headers:
        if h.get('name', '').lower() == 'content-disposition':
            disposition = h.get('value', '')
            if 'attachment' in disposition.lower() or 'filename' in disposition.lower():
                print(f'\n⬇️ DOWNLOAD-HEADER GEFUNDEN:')
                print(f'   {method} {url}')
                print(f'   Status: {status}')
                print(f'   Content-Disposition: {disposition}')

if not pdf_found:
    print('\n❌ Keine PDF-Responses gefunden')

# Prüfe auch alle ServiceController-Requests
print('\n\n' + '=' * 80)
print('SERVICECONTROLLER-REQUESTS (Nexacro)')
print('=' * 80)

service_requests = []
for entry in entries:
    request = entry.get('request', {})
    url = request.get('url', '')
    
    if 'ServiceController' in url:
        method = request.get('method', '')
        status = entry.get('response', {}).get('status', 0)
        
        # Parse act und cmd
        if 'act=' in url:
            act = url.split('act=')[1].split('&')[0]
            cmd = url.split('cmd=')[1].split('&')[0] if 'cmd=' in url else ''
            
            service_requests.append({
                'act': act,
                'cmd': cmd,
                'url': url,
                'method': method,
                'status': status,
                'request': request,
                'response': entry.get('response', {})
            })

print(f'\nGefundene ServiceController-Requests: {len(service_requests)}\n')

for req in service_requests:
    print(f'\n{req["method"]} act={req["act"]} cmd={req["cmd"]}')
    print(f'   URL: {req["url"]}')
    print(f'   Status: {req["status"]}')
    
    # Zeige Request-Body (erste 300 Zeichen)
    post_data = req['request'].get('postData', {})
    if post_data:
        text = post_data.get('text', '')
        if text:
            # Parse XML für Parameter
            if '<Parameter id=' in text:
                params = []
                matches = re.findall(r'<Parameter id="([^"]+)"[^>]*>([^<]+)</Parameter>', text)
                for param_id, param_value in matches[:10]:
                    if param_value.strip():
                        val = param_value.strip()[:50]
                        params.append(f'{param_id}={val}')
                if params:
                    params_str = ', '.join(params[:5])
                    print(f'   Parameter: {params_str}')
            
            # Prüfe auf interessante Keywords
            text_lower = text.lower()
            if any(kw in text_lower for kw in ['pdf', 'document', 'dokument', 'print', 'export', 
                                                'download', 'invoice', 'rechnung', 'delivery', 
                                                'lieferschein', 'file', 'attachment']):
                print(f'   ⭐ Enthält Dokument-Keywords!')
                # Zeige relevanten Teil
                for kw in ['pdf', 'document', 'dokument', 'print', 'export', 'download', 
                          'invoice', 'rechnung', 'delivery', 'lieferschein']:
                    if kw in text_lower:
                        idx = text_lower.find(kw)
                        snippet = text[max(0, idx-50):idx+100]
                        print(f'      ...{snippet}...')
                        break

# Suche nach Response-Inhalten mit Dokumenten-Referenzen
print('\n\n' + '=' * 80)
print('RESPONSE-INHALTE MIT DOKUMENTEN-REFERENZEN')
print('=' * 80)

for entry in entries:
    response = entry.get('response', {})
    content = response.get('content', {})
    text = content.get('text', '')
    
    if text and len(text) > 100:  # Nur größere Responses
        text_lower = text.lower()
        
        # Prüfe auf Dokumenten-Referenzen
        if any(kw in text_lower for kw in ['pdf', '.pdf', 'document', 'dokument', 'file', 
                                            'download', 'attachment', 'invoice', 'rechnung',
                                            'delivery', 'lieferschein', 'print', 'export']):
            request = entry.get('request', {})
            url = request.get('url', '')
            method = request.get('method', '')
            
            print(f'\n{method} {url}')
            
            # Zeige relevante Stellen
            for kw in ['pdf', '.pdf', 'document', 'dokument', 'file', 'download', 
                      'attachment', 'invoice', 'rechnung', 'delivery', 'lieferschein']:
                if kw in text_lower:
                    # Finde alle Vorkommen
                    indices = [i for i in range(len(text_lower)) if text_lower.startswith(kw, i)]
                    for idx in indices[:3]:  # Erste 3
                        snippet = text[max(0, idx-100):idx+200]
                        # Bereinige
                        snippet = snippet.replace('\n', ' ').replace('\r', ' ')
                        if len(snippet) > 200:
                            snippet = snippet[:200] + '...'
                        print(f'   ...{snippet}...')
                    break
