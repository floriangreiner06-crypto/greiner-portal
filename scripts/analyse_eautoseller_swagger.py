#!/usr/bin/env python3
"""
e-autoseller Swagger API Analyse
Analysiert die Swagger/OpenAPI-Dokumentation und erstellt eine Zusammenfassung
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Mögliche Pfade für die Swagger-Datei
SWAGGER_PATHS = [
    'scripts/tests/eAutoseller.json',
    'docs/eAutoseller.json',
    'eAutoseller.json',
    '/opt/greiner-portal/scripts/tests/eAutoseller.json',
]

def find_swagger_file():
    """Findet die Swagger-Datei"""
    base_path = Path(__file__).parent.parent
    
    for path in SWAGGER_PATHS:
        full_path = base_path / path if not os.path.isabs(path) else Path(path)
        if full_path.exists():
            return full_path
    
    # Suche rekursiv
    for swagger_file in base_path.rglob('eAutoseller.json'):
        return swagger_file
    
    for swagger_file in base_path.rglob('*swagger*.json'):
        return swagger_file
    
    for swagger_file in base_path.rglob('*openapi*.json'):
        return swagger_file
    
    return None

def analyze_swagger(swagger_data):
    """Analysiert die Swagger-Dokumentation"""
    analysis = {
        'info': {},
        'servers': [],
        'paths': {},
        'components': {},
        'security': [],
        'endpoints': [],
        'summary': {}
    }
    
    # Info
    if 'info' in swagger_data:
        analysis['info'] = {
            'title': swagger_data['info'].get('title', 'N/A'),
            'version': swagger_data['info'].get('version', 'N/A'),
            'description': swagger_data['info'].get('description', 'N/A'),
        }
    
    # Servers
    if 'servers' in swagger_data:
        analysis['servers'] = [s.get('url', 'N/A') for s in swagger_data['servers']]
    
    # Security
    if 'security' in swagger_data:
        analysis['security'] = swagger_data['security']
    
    if 'components' in swagger_data and 'securitySchemes' in swagger_data['components']:
        analysis['security_schemes'] = list(swagger_data['components']['securitySchemes'].keys())
    
    # Paths (Endpoints)
    if 'paths' in swagger_data:
        for path, methods in swagger_data['paths'].items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    endpoint_info = {
                        'path': path,
                        'method': method.upper(),
                        'summary': details.get('summary', 'N/A'),
                        'description': details.get('description', 'N/A'),
                        'operationId': details.get('operationId', 'N/A'),
                        'tags': details.get('tags', []),
                        'parameters': [],
                        'requestBody': None,
                        'responses': {},
                        'security': details.get('security', [])
                    }
                    
                    # Parameters
                    if 'parameters' in details:
                        for param in details['parameters']:
                            if '$ref' in param:
                                # Resolve reference
                                ref_path = param['$ref'].replace('#/', '').split('/')
                                if len(ref_path) == 2:
                                    component_type, component_name = ref_path
                                    if component_type in swagger_data.get('components', {}):
                                        param_data = swagger_data['components'][component_type].get(component_name, {})
                                        endpoint_info['parameters'].append({
                                            'name': param_data.get('name', 'N/A'),
                                            'in': param_data.get('in', 'N/A'),
                                            'required': param_data.get('required', False),
                                            'schema': param_data.get('schema', {})
                                        })
                            else:
                                endpoint_info['parameters'].append({
                                    'name': param.get('name', 'N/A'),
                                    'in': param.get('in', 'N/A'),
                                    'required': param.get('required', False),
                                    'schema': param.get('schema', {})
                                })
                    
                    # Request Body
                    if 'requestBody' in details:
                        endpoint_info['requestBody'] = details['requestBody']
                    
                    # Responses
                    if 'responses' in details:
                        endpoint_info['responses'] = {
                            code: {
                                'description': resp.get('description', 'N/A'),
                                'content': list(resp.get('content', {}).keys()) if 'content' in resp else []
                            }
                            for code, resp in details['responses'].items()
                        }
                    
                    analysis['endpoints'].append(endpoint_info)
    
    # Summary
    analysis['summary'] = {
        'total_endpoints': len(analysis['endpoints']),
        'methods': {},
        'tags': set(),
        'has_authentication': len(analysis['security']) > 0 or 'security_schemes' in analysis,
    }
    
    for endpoint in analysis['endpoints']:
        method = endpoint['method']
        analysis['summary']['methods'][method] = analysis['summary']['methods'].get(method, 0) + 1
        for tag in endpoint['tags']:
            analysis['summary']['tags'].add(tag)
    
    analysis['summary']['tags'] = sorted(list(analysis['summary']['tags']))
    
    return analysis

def print_analysis(analysis):
    """Gibt die Analyse aus"""
    print("=" * 80)
    print("e-autoseller Swagger API Analyse")
    print("=" * 80)
    print()
    
    # Info
    print("📋 API Information:")
    print(f"  Title: {analysis['info'].get('title', 'N/A')}")
    print(f"  Version: {analysis['info'].get('version', 'N/A')}")
    if analysis['info'].get('description'):
        print(f"  Description: {analysis['info']['description'][:100]}...")
    print()
    
    # Servers
    if analysis['servers']:
        print("🌐 Servers:")
        for server in analysis['servers']:
            print(f"  - {server}")
        print()
    
    # Security
    if analysis['security'] or 'security_schemes' in analysis:
        print("🔐 Authentication:")
        if 'security_schemes' in analysis:
            print(f"  Schemes: {', '.join(analysis['security_schemes'])}")
        if analysis['security']:
            print(f"  Default Security: {analysis['security']}")
        print()
    
    # Summary
    print("📊 Summary:")
    print(f"  Total Endpoints: {analysis['summary']['total_endpoints']}")
    print(f"  Methods: {dict(analysis['summary']['methods'])}")
    print(f"  Tags: {', '.join(analysis['summary']['tags'])}")
    print(f"  Has Authentication: {analysis['summary']['has_authentication']}")
    print()
    
    # Endpoints
    print("🔗 Endpoints:")
    print()
    
    # Gruppiere nach Tags
    endpoints_by_tag = {}
    for endpoint in analysis['endpoints']:
        tags = endpoint['tags'] if endpoint['tags'] else ['Untagged']
        for tag in tags:
            if tag not in endpoints_by_tag:
                endpoints_by_tag[tag] = []
            endpoints_by_tag[tag].append(endpoint)
    
    for tag in sorted(endpoints_by_tag.keys()):
        print(f"  📁 {tag}:")
        for endpoint in endpoints_by_tag[tag]:
            print(f"    {endpoint['method']:6} {endpoint['path']}")
            if endpoint['summary'] and endpoint['summary'] != 'N/A':
                print(f"           {endpoint['summary']}")
            if endpoint['parameters']:
                params_str = ', '.join([p['name'] for p in endpoint['parameters']])
                print(f"           Parameters: {params_str}")
            print()
    
    print("=" * 80)

def save_analysis(analysis, output_file='docs/EAUTOSELLER_SWAGGER_ANALYSE.md'):
    """Speichert die Analyse als Markdown"""
    output_path = Path(__file__).parent.parent / output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# e-autoseller Swagger API Analyse\n\n")
        f.write(f"**Erstellt:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Quelle:** eAutoseller.json\n\n")
        f.write("---\n\n")
        
        # Info
        f.write("## 📋 API Information\n\n")
        f.write(f"- **Title:** {analysis['info'].get('title', 'N/A')}\n")
        f.write(f"- **Version:** {analysis['info'].get('version', 'N/A')}\n")
        if analysis['info'].get('description'):
            f.write(f"- **Description:** {analysis['info']['description']}\n")
        f.write("\n")
        
        # Servers
        if analysis['servers']:
            f.write("## 🌐 Servers\n\n")
            for server in analysis['servers']:
                f.write(f"- {server}\n")
            f.write("\n")
        
        # Security
        if analysis['security'] or 'security_schemes' in analysis:
            f.write("## 🔐 Authentication\n\n")
            if 'security_schemes' in analysis:
                f.write(f"**Schemes:** {', '.join(analysis['security_schemes'])}\n\n")
            if analysis['security']:
                f.write(f"**Default Security:** {analysis['security']}\n\n")
        
        # Summary
        f.write("## 📊 Summary\n\n")
        f.write(f"- **Total Endpoints:** {analysis['summary']['total_endpoints']}\n")
        f.write(f"- **Methods:** {dict(analysis['summary']['methods'])}\n")
        f.write(f"- **Tags:** {', '.join(analysis['summary']['tags'])}\n")
        f.write(f"- **Has Authentication:** {analysis['summary']['has_authentication']}\n\n")
        
        # Endpoints
        f.write("## 🔗 Endpoints\n\n")
        
        # Gruppiere nach Tags
        endpoints_by_tag = {}
        for endpoint in analysis['endpoints']:
            tags = endpoint['tags'] if endpoint['tags'] else ['Untagged']
            for tag in tags:
                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []
                endpoints_by_tag[tag].append(endpoint)
        
        for tag in sorted(endpoints_by_tag.keys()):
            f.write(f"### {tag}\n\n")
            for endpoint in endpoints_by_tag[tag]:
                f.write(f"#### {endpoint['method']} {endpoint['path']}\n\n")
                if endpoint['summary'] and endpoint['summary'] != 'N/A':
                    f.write(f"**Summary:** {endpoint['summary']}\n\n")
                if endpoint['description'] and endpoint['description'] != 'N/A':
                    f.write(f"**Description:** {endpoint['description']}\n\n")
                if endpoint['parameters']:
                    f.write("**Parameters:**\n\n")
                    f.write("| Name | In | Required | Type |\n")
                    f.write("|------|----|----------|------|\n")
                    for param in endpoint['parameters']:
                        param_type = 'N/A'
                        if 'schema' in param and param['schema']:
                            if 'type' in param['schema']:
                                param_type = param['schema']['type']
                            elif '$ref' in param['schema']:
                                param_type = param['schema']['$ref'].split('/')[-1]
                        f.write(f"| {param['name']} | {param['in']} | {param['required']} | {param_type} |\n")
                    f.write("\n")
                if endpoint['responses']:
                    f.write("**Responses:**\n\n")
                    for code, resp in endpoint['responses'].items():
                        f.write(f"- **{code}:** {resp['description']}\n")
                        if resp['content']:
                            f.write(f"  - Content Types: {', '.join(resp['content'])}\n")
                    f.write("\n")
                f.write("---\n\n")
        
        f.write(f"\n**Letzte Aktualisierung:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"\n✅ Analyse gespeichert: {output_path}")

def main():
    """Hauptfunktion"""
    print("🔍 Suche nach Swagger-Dokumentation...")
    
    swagger_file = find_swagger_file()
    
    if not swagger_file:
        print("❌ Swagger-Datei nicht gefunden!")
        print("\nMögliche Pfade:")
        for path in SWAGGER_PATHS:
            print(f"  - {path}")
        print("\nBitte stellen Sie sicher, dass die Datei synchronisiert ist.")
        sys.exit(1)
    
    print(f"✅ Swagger-Datei gefunden: {swagger_file}")
    print(f"   Größe: {swagger_file.stat().st_size / 1024:.1f} KB")
    print()
    
    # Lade JSON
    try:
        with open(swagger_file, 'r', encoding='utf-8') as f:
            swagger_data = json.load(f)
        print(f"✅ JSON erfolgreich geladen")
        print()
    except Exception as e:
        print(f"❌ Fehler beim Laden der JSON-Datei: {e}")
        sys.exit(1)
    
    # Analysiere
    print("🔍 Analysiere Swagger-Dokumentation...")
    analysis = analyze_swagger(swagger_data)
    
    # Ausgabe
    print_analysis(analysis)
    
    # Speichere Analyse
    save_analysis(analysis)
    
    print("\n✅ Analyse abgeschlossen!")

if __name__ == '__main__':
    main()
