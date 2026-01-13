#!/usr/bin/env python3
"""
Extrahiert BWA-Werte direkt aus HAR-Datei
Alternative zu Selenium, wenn Browser blockiert wird

Erstellt: TAG 182
"""

import json
import re
from html.parser import HTMLParser
from typing import Dict, List, Optional
from datetime import datetime

HAR_FILE = "/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/globalcube_analyse/f03_bwa_vj_vergleich_alle_beriebe_angehackt.har"


def extract_html_from_har(har_file: str) -> List[Dict]:
    """
    Extrahiert HTML-Responses aus HAR-Datei
    """
    print("=== Extrahiere HTML aus HAR ===\n")
    
    with open(har_file, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    entries = har_data.get('log', {}).get('entries', [])
    
    html_responses = []
    
    for entry in entries:
        url = entry.get('request', {}).get('url', '')
        method = entry.get('request', {}).get('method', '')
        
        if method == 'POST' and '/bi/v1/reports' in url:
            response = entry.get('response', {})
            response_content = response.get('content', {})
            response_text = response_content.get('text', '')
            
            if response_text:
                # Prüfe Content-Type
                content_type = response_content.get('mimeType', '').lower()
                
                    # Prüfe ob multipart
                if 'multipart' in content_type:
                    # Parse Multipart
                    # Suche Boundary in Headers
                    boundary = None
                    for header in response.get('headers', []):
                        if header.get('name', '').lower() == 'content-type':
                            ct_value = header.get('value', '')
                            # Boundary kann in Anführungszeichen sein
                            boundary_match = re.search(r'boundary=["\']?([^"\'\s;]+)["\']?', ct_value, re.I)
                            if boundary_match:
                                boundary = boundary_match.group(1)
                                break
                    
                    # Falls nicht in Headers, suche im Text
                    if not boundary:
                        boundary_match = re.search(r'^--([^\r\n]+)', response_text)
                        if boundary_match:
                            boundary = boundary_match.group(1)
                    
                    if boundary:
                        # Entferne Anführungszeichen falls vorhanden
                        boundary = boundary.strip('"\'')
                        
                        # Split nach Boundary (mit -- davor)
                        parts = response_text.split(f'--{boundary}')
                        print(f"Boundary: {boundary[:50]}...")
                        print(f"Parts: {len(parts)}")
                        
                        for i, part in enumerate(parts[1:-1], 1):  # Erste und letzte sind leer
                            # Skip leere Parts
                            if not part.strip():
                                continue
                            
                            # Split Header und Body
                            if '\r\n\r\n' in part:
                                header, body = part.split('\r\n\r\n', 1)
                            elif '\n\n' in part:
                                header, body = part.split('\n\n', 1)
                            else:
                                # Versuche ohne doppelte Newlines
                                if '\r\n' in part:
                                    lines = part.split('\r\n', 1)
                                    if len(lines) > 1:
                                        header, body = lines[0], '\r\n'.join(lines[1:])
                                    else:
                                        continue
                                elif '\n' in part:
                                    lines = part.split('\n', 1)
                                    if len(lines) > 1:
                                        header, body = lines[0], '\n'.join(lines[1:])
                                    else:
                                        continue
                                else:
                                    continue
                            
                            # Prüfe Content-Type im Part-Header
                            if 'text/html' in header.lower():
                                html_responses.append({
                                    'url': url,
                                    'html': body,
                                    'size': len(body),
                                    'part': i
                                })
                                print(f"✅ HTML-Part {i} gefunden: {len(body)} Zeichen")
                            
                            # Auch XML-Parts können interessant sein
                            elif 'text/xml' in header.lower() or body.strip().startswith('<?xml'):
                                print(f"✅ XML-Part {i} gefunden: {len(body)} Zeichen")
                
                # Prüfe ob direkt HTML
                elif 'text/html' in content_type or response_text.strip().startswith('<html'):
                    html_responses.append({
                        'url': url,
                        'html': response_text,
                        'size': len(response_text),
                        'part': 0
                    })
                    print(f"✅ Direktes HTML gefunden: {len(response_text)} Zeichen")
    
    return html_responses


def extract_bwa_values_from_html(html_content: str) -> Dict:
    """
    Extrahiert BWA-Werte aus HTML
    """
    bwa_values = {}
    
    # Suche nach Tabellen
    table_pattern = r'<table[^>]*>(.*?)</table>'
    tables = re.findall(table_pattern, html_content, re.DOTALL | re.I)
    
    print(f"Gefundene Tabellen: {len(tables)}\n")
    
    # BWA-Keywords
    bwa_keywords = {
        'umsatzerlöse': ['umsatz', 'umsatzerlöse', 'erlöse'],
        'einsatzwerte': ['einsatz', 'einsatzwerte'],
        'variable_kosten': ['variable', 'variable kosten'],
        'direkte_kosten': ['direkte', 'direkte kosten'],
        'indirekte_kosten': ['indirekte', 'indirekte kosten'],
        'betriebsergebnis': ['betriebsergebnis', 'betriebs-ergebnis', 'betriebsergebnis'],
        'unternehmensergebnis': ['unternehmensergebnis', 'unternehmens-ergebnis'],
        'bruttoertrag': ['bruttoertrag', 'brutto-ertrag'],
        'deckungsbeitrag_1': ['deckungsbeitrag 1', 'db1', 'deckungsbeitrag i'],
        'deckungsbeitrag_2': ['deckungsbeitrag 2', 'db2', 'deckungsbeitrag ii'],
        'deckungsbeitrag_3': ['deckungsbeitrag 3', 'db3', 'deckungsbeitrag iii'],
    }
    
    # Parse Tabellen
    for table_idx, table in enumerate(tables, 1):
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.I)
        
        for row_idx, row in enumerate(rows[:200], 1):  # Erste 200 Zeilen
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.I)
            
            if cells:
                clean_cells = []
                for cell in cells:
                    clean = re.sub(r'<[^>]+>', '', cell)
                    clean = re.sub(r'\s+', ' ', clean).strip()
                    clean_cells.append(clean)
                
                row_text = ' '.join(clean_cells).lower()
                
                    # Prüfe ob BWA-relevant
                    for key, keywords in bwa_keywords.items():
                        if any(kw in row_text for kw in keywords):
                            cleaned_numbers = []
                            
                            # Suche nach Zahlen (deutsches Format)
                            # Nimm zweite Zelle (sollte Monatswert sein)
                            if len(clean_cells) >= 2:
                                value_str = clean_cells[1]  # Zweite Spalte = Monatswert
                                
                                # Entferne alles außer Zahlen, Komma, Punkt, Minus
                                cleaned = re.sub(r'[^\d.,-]', '', value_str)
                                
                                # Deutsches Format: Punkt = Tausender, Komma = Dezimal
                                if ',' in cleaned:
                                    # Komma = Dezimaltrennzeichen
                                    # Entferne alle Punkte (Tausender)
                                    cleaned = cleaned.replace('.', '').replace(',', '.')
                                else:
                                    # Nur Punkte = Tausender-Trennzeichen
                                    cleaned = cleaned.replace('.', '')
                                
                                if cleaned:
                                    try:
                                        value = float(cleaned)
                                        cleaned_numbers = [str(value)]
                                    except:
                                        cleaned_numbers = []
                            
                            # Fallback: Suche nach Zahlen in allen Zellen
                            if not cleaned_numbers:
                                for cell in clean_cells[1:]:  # Überspringe erste Zelle (Name)
                                    # Suche nach Zahlen
                                    numbers = re.findall(r'([\d.,\s-]+)', cell)
                                    for num in numbers:
                                        cleaned = re.sub(r'[^\d.,-]', '', num)
                                        if cleaned and len(cleaned) > 3:
                                            # Deutsches Format parsen
                                            if ',' in cleaned:
                                                cleaned = cleaned.replace('.', '').replace(',', '.')
                                            else:
                                                cleaned = cleaned.replace('.', '')
                                            try:
                                                float(cleaned)  # Prüfe ob gültig
                                                cleaned_numbers.append(cleaned)
                                                break  # Nimm ersten gültigen Wert
                                            except:
                                                pass
                            
                            if cleaned_numbers:
                                value_key = f"{key}_table{table_idx}"
                                if value_key not in bwa_values:  # Nur erste gefundene
                                    bwa_values[value_key] = {
                                        'table': table_idx,
                                        'row': row_idx,
                                        'cells': clean_cells,
                                        'values': cleaned_numbers[:10],
                                    }
                                    print(f"✅ {key}: {cleaned_numbers[0]}")
    
    return bwa_values


def main():
    """
    Hauptfunktion
    """
    print("=" * 80)
    print("BWA-Werte aus HAR extrahieren")
    print("=" * 80)
    print()
    
    # Extrahiere HTML
    html_responses = extract_html_from_har(HAR_FILE)
    
    if not html_responses:
        print("❌ Keine HTML-Responses gefunden")
        return
    
    # Extrahiere BWA-Werte
    all_results = {}
    
    for i, html_response in enumerate(html_responses, 1):
        print(f"\n{'='*80}")
        print(f"HTML-Response {i}")
        print(f"{'='*80}\n")
        
        bwa_values = extract_bwa_values_from_html(html_response['html'])
        
        # Speichere HTML
        html_file = f"/tmp/cognos_bwa_har_{i}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_response['html'])
        print(f"\n💾 HTML gespeichert: {html_file}")
        
        all_results[f"response_{i}"] = {
            'url': html_response['url'],
            'bwa_values': bwa_values,
            'html_file': html_file
        }
    
    # Speichere alle Ergebnisse
    results_file = "/tmp/cognos_bwa_har_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Alle Ergebnisse gespeichert: {results_file}")
    
    # Zusammenfassung
    print("\n" + "=" * 80)
    print("ZUSAMMENFASSUNG")
    print("=" * 80)
    for key, data in all_results.items():
        print(f"\n{key}:")
        if data['bwa_values']:
            for bwa_key, value in data['bwa_values'].items():
                if not value.get('is_drill_down'):
                    print(f"  {bwa_key}: {value.get('values', ['N/A'])[0] if value.get('values') else 'N/A'}")


if __name__ == '__main__':
    main()
