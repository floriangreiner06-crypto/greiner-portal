#!/usr/bin/env python3
"""
Vollständige HAR-Exploration
Extrahiert ALLE Details aus HAR-Datei

Erstellt: TAG 182
"""

import json
import re
from collections import defaultdict
from html.parser import HTMLParser
from typing import Dict, List, Optional

# Suche nach neuestem HAR-File (Hyundai, Landau oder alle)
import os
import glob

HAR_DIR = "/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/globalcube_analyse"

# Suche nach Hyundai-HAR zuerst, dann Landau, dann alle
har_file = None
if os.path.exists(HAR_DIR):
    # Hyundai
    hyundai_files = glob.glob(f"{HAR_DIR}/*hyundai*.har")
    if hyundai_files:
        har_file = max(hyundai_files, key=os.path.getmtime)
    else:
        # Landau
        landau_files = glob.glob(f"{HAR_DIR}/*landau*.har")
        if landau_files:
            har_file = max(landau_files, key=os.path.getmtime)
        else:
            # Fallback: Neueste HAR-Datei
            all_hars = glob.glob(f"{HAR_DIR}/*.har")
            if all_hars:
                har_file = max(all_hars, key=os.path.getmtime)

HAR_FILE = har_file or "/mnt/buchhaltung/Greiner Portal/Greiner_Portal_NEU/globalcube_analyse/f03_bwa_vj_vergleich_alle_beriebe_angehackt.har"


def parse_german_number(value_str: str) -> Optional[float]:
    """
    Parst deutsche Zahl (Punkt = Tausender, Komma = Dezimal)
    """
    if not value_str:
        return None
    
    # Entferne alles außer Zahlen, Komma, Punkt, Minus
    cleaned = re.sub(r'[^\d.,-]', '', value_str)
    
    if not cleaned:
        return None
    
    # Prüfe ob Minus
    is_negative = '-' in cleaned
    cleaned = cleaned.replace('-', '')
    
    # Deutsches Format
    if ',' in cleaned:
        # Komma = Dezimal
        cleaned = cleaned.replace('.', '').replace(',', '.')
    else:
        # Nur Punkte = Tausender
        cleaned = cleaned.replace('.', '')
    
    if is_negative:
        cleaned = '-' + cleaned
    
    try:
        return float(cleaned)
    except:
        return None


def extract_all_tables(html: str) -> List[Dict]:
    """
    Extrahiert alle Tabellen aus HTML mit vollständigen Daten
    """
    tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.I)
    
    all_tables = []
    
    for table_idx, table in enumerate(tables, 1):
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.I)
        
        table_data = {
            'index': table_idx,
            'rows': []
        }
        
        for row_idx, row in enumerate(rows, 1):
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.I)
            
            if cells:
                clean_cells = []
                for cell in cells:
                    clean = re.sub(r'<[^>]+>', '', cell)
                    clean = re.sub(r'\s+', ' ', clean).strip()
                    clean_cells.append(clean)
                
                # Prüfe ob Daten-Zeile
                has_data = any(parse_german_number(cell) is not None for cell in clean_cells) or len(clean_cells) > 1
                
                if has_data:
                    # Parse Werte
                    parsed_values = []
                    for cell in clean_cells:
                        value = parse_german_number(cell)
                        parsed_values.append(value)
                    
                    row_data = {
                        'row': row_idx,
                        'cells': clean_cells,
                        'values': parsed_values
                    }
                    
                    table_data['rows'].append(row_data)
        
        all_tables.append(table_data)
    
    return all_tables


def extract_bwa_structure(tables: List[Dict]) -> Dict:
    """
    Extrahiert BWA-Struktur aus Tabellen
    """
    bwa_structure = {
        'hauptpositionen': {},
        'unterpositionen': {},
        'bereiche': {},
        'details': []
    }
    
    # BWA-Hauptpositionen
    main_positions = {
        'umsatzerlöse': ['umsatz', 'umsatzerlöse', 'erlöse'],
        'einsatzwerte': ['einsatz', 'einsatzwerte'],
        'bruttoertrag': ['bruttoertrag', 'brutto-ertrag'],
        'variable_kosten': ['variable', 'variable kosten'],
        'direkte_kosten': ['direkte', 'direkte kosten'],
        'indirekte_kosten': ['indirekte', 'indirekte kosten'],
        'deckungsbeitrag_1': ['deckungsbeitrag 1', 'db1', 'deckungsbeitrag i'],
        'deckungsbeitrag_2': ['deckungsbeitrag 2', 'db2', 'deckungsbeitrag ii'],
        'deckungsbeitrag_3': ['deckungsbeitrag 3', 'db3', 'deckungsbeitrag iii'],
        'betriebsergebnis': ['betriebsergebnis', 'betriebs-ergebnis'],
        'unternehmensergebnis': ['unternehmensergebnis', 'unternehmens-ergebnis'],
    }
    
    # Unterpositionen (aufgedrillt)
    sub_positions = {
        'trainingskosten': ['trainingskosten'],
        'fahrzeugkosten': ['fahrzeugkosten'],
        'werbekosten': ['werbekosten'],
        'personalkosten': ['personalkosten'],
        'gemeinkosten': ['gemeinkosten'],
        'raumkosten': ['raumkosten'],
        'kalkulatorische_kosten': ['kalk', 'kalkulatorisch'],
        'umlagekosten': ['umlage'],
    }
    
    for table in tables:
        for row_data in table['rows']:
            cells = row_data['cells']
            values = row_data['values']
            
            if not cells:
                continue
            
            first_cell = cells[0].lower()
            row_text = ' '.join(cells).lower()
            
            # Prüfe Hauptpositionen
            for key, keywords in main_positions.items():
                if any(kw in first_cell for kw in keywords):
                    # Extrahiere Werte
                    monat = values[1] if len(values) > 1 else None
                    vorjahr = values[3] if len(values) > 3 else None
                    ytd = values[7] if len(values) > 7 else None
                    ytd_vorjahr = values[9] if len(values) > 9 else None
                    
                    if key not in bwa_structure['hauptpositionen']:
                        bwa_structure['hauptpositionen'][key] = {
                            'name': cells[0],
                            'monat': monat,
                            'vorjahr': vorjahr,
                            'ytd': ytd,
                            'ytd_vorjahr': ytd_vorjahr,
                            'cells': cells,
                            'table': table['index'],
                            'row': row_data['row']
                        }
            
            # Prüfe Unterpositionen
            for key, keywords in sub_positions.items():
                if any(kw in first_cell for kw in keywords):
                    monat = values[1] if len(values) > 1 else None
                    
                    if key not in bwa_structure['unterpositionen']:
                        bwa_structure['unterpositionen'][key] = {
                            'name': cells[0],
                            'monat': monat,
                            'cells': cells,
                            'table': table['index'],
                            'row': row_data['row']
                        }
            
            # Prüfe Bereiche (NW, GW, etc.)
            if any(bereich in first_cell for bereich in ['nw', 'gw', 'neuwagen', 'gebrauchtwagen', 'service', 'werkstatt']):
                monat = values[1] if len(values) > 1 else None
                
                bereich_key = first_cell[:50]
                if bereich_key not in bwa_structure['bereiche']:
                    bwa_structure['bereiche'][bereich_key] = {
                        'name': cells[0],
                        'monat': monat,
                        'cells': cells,
                        'table': table['index'],
                        'row': row_data['row']
                    }
            
            # Alle Zeilen mit Daten speichern
            if any(v is not None for v in values):
                bwa_structure['details'].append({
                    'cells': cells,
                    'values': values,
                    'table': table['index'],
                    'row': row_data['row']
                })
    
    return bwa_structure


def main():
    """
    Hauptfunktion
    """
    print("=" * 80)
    print("VOLLSTÄNDIGE HAR-EXPLORATION")
    print("=" * 80)
    print()
    
    # Lade HAR
    with open(HAR_FILE, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    entries = har_data.get('log', {}).get('entries', [])
    
    print(f"Anzahl Requests: {len(entries)}\n")
    
    # Extrahiere alle HTML-Responses
    html_responses = []
    
    for entry in entries:
        url = entry.get('request', {}).get('url', '')
        method = entry.get('request', {}).get('method', '')
        
        if method == 'POST' and '/bi/v1/reports' in url:
            response = entry.get('response', {})
            content = response.get('content', {})
            text = content.get('text', '')
            
            if text and 'multipart' in content.get('mimeType', '').lower():
                # Parse Multipart
                boundary_match = re.search(r'boundary=["\']?([^"\'\s;]+)["\']?', str(response.get('headers', [])), re.I)
                if not boundary_match:
                    boundary_match = re.search(r'^--([^\r\n]+)', text)
                
                if boundary_match:
                    boundary = boundary_match.group(1).strip('"\'')
                    parts = text.split(f'--{boundary}')
                    
                    for i, part in enumerate(parts[1:-1], 1):
                        if '\r\n\r\n' in part:
                            header, body = part.split('\r\n\r\n', 1)
                        elif '\n\n' in part:
                            header, body = part.split('\n\n', 1)
                        else:
                            continue
                        
                        if 'text/html' in header.lower():
                            html_responses.append({
                                'url': url,
                                'html': body,
                                'size': len(body),
                                'part': i
                            })
    
    print(f"Gefundene HTML-Responses: {len(html_responses)}\n")
    
    # Analysiere alle HTML-Responses
    all_results = {}
    
    for idx, html_resp in enumerate(html_responses, 1):
        print(f"{'='*80}")
        print(f"Response {idx}")
        print(f"{'='*80}\n")
        
        # Extrahiere Tabellen
        tables = extract_all_tables(html_resp['html'])
        print(f"Tabellen: {len(tables)}")
        for table in tables:
            print(f"  Tabelle {table['index']}: {len(table['rows'])} Zeilen")
        
        # Extrahiere BWA-Struktur
        bwa_structure = extract_bwa_structure(tables)
        
        print(f"\nHauptpositionen: {len(bwa_structure['hauptpositionen'])}")
        print(f"Unterpositionen: {len(bwa_structure['unterpositionen'])}")
        print(f"Bereiche: {len(bwa_structure['bereiche'])}")
        print(f"Details: {len(bwa_structure['details'])}")
        
        # Zeige Hauptpositionen
        print(f"\n=== HAUPTPOSITIONEN ===\n")
        for key, data in bwa_structure['hauptpositionen'].items():
            print(f"{data['name']}:")
            if data['monat'] is not None:
                print(f"  Monat: {data['monat']:,.2f} €")
            if data['vorjahr'] is not None:
                print(f"  Vorjahr: {data['vorjahr']:,.2f} €")
            if data['ytd'] is not None:
                print(f"  YTD: {data['ytd']:,.2f} €")
            print()
        
        # Zeige Unterpositionen
        if bwa_structure['unterpositionen']:
            print(f"\n=== UNTERPOSITIONEN (AUFGEDRILLT) ===\n")
            for key, data in bwa_structure['unterpositionen'].items():
                if data['monat'] is not None:
                    print(f"{data['name']}: {data['monat']:,.2f} €")
        
        # Speichere HTML
        html_file = f"/tmp/har_response_{idx}_complete.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_resp['html'])
        print(f"\n💾 HTML gespeichert: {html_file}")
        
        all_results[f"response_{idx}"] = {
            'url': html_resp['url'],
            'html_file': html_file,
            'tables_count': len(tables),
            'bwa_structure': bwa_structure
        }
    
    # Speichere vollständige Analyse
    output_file = "/tmp/har_complete_exploration.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n{'='*80}")
    print(f"💾 Vollständige Analyse gespeichert: {output_file}")
    print(f"{'='*80}\n")
    
    # Zusammenfassung
    print("=== ZUSAMMENFASSUNG ===\n")
    print(f"HTML-Responses: {len(html_responses)}")
    total_tables = sum(r['tables_count'] for r in all_results.values())
    print(f"Tabellen gesamt: {total_tables}")
    total_haupt = sum(len(r['bwa_structure']['hauptpositionen']) for r in all_results.values())
    print(f"Hauptpositionen: {total_haupt}")
    total_unter = sum(len(r['bwa_structure']['unterpositionen']) for r in all_results.values())
    print(f"Unterpositionen: {total_unter}")
    total_details = sum(len(r['bwa_structure']['details']) for r in all_results.values())
    print(f"Detail-Zeilen: {total_details}")


if __name__ == '__main__':
    main()
