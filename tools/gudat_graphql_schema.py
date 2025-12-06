#!/usr/bin/env python3
"""
GUDAT - GraphQL Schema Introspection
Finde die korrekten Felder für Dossiers und Appointments
"""

import json
import sys
sys.path.insert(0, '/opt/greiner-portal/tools')

from gudat_client import GudatClient

USERNAME = "florian.greiner@auto-greiner.de"
PASSWORD = "Hyundai2025!"

print("=" * 70)
print("GUDAT GRAPHQL SCHEMA INTROSPECTION")
print("=" * 70)

client = GudatClient(USERNAME, PASSWORD)

if not client.login():
    print("Login fehlgeschlagen!")
    exit(1)

# GraphQL Introspection Query
introspection_query = '''
query IntrospectionQuery {
    __schema {
        types {
            name
            kind
            fields {
                name
                type {
                    name
                    kind
                }
            }
        }
    }
}
'''

print("\n[1] Schema Introspection...")
response = client._api_request(
    'POST',
    '/graphql',
    json={
        'operationName': 'IntrospectionQuery',
        'query': introspection_query,
        'variables': {}
    }
)

if response.status_code == 200:
    data = response.json()
    
    # Speichere vollständiges Schema
    with open('/tmp/gudat_graphql_schema.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("   Schema gespeichert: /tmp/gudat_graphql_schema.json")
    
    # Suche nach interessanten Types
    interesting_types = ['Dossier', 'Appointment', 'Order', 'Event', 'Vehicle', 'Customer']
    
    types = data.get('data', {}).get('__schema', {}).get('types', [])
    
    for t in types:
        type_name = t.get('name', '')
        if type_name in interesting_types or any(x in type_name for x in interesting_types):
            print(f"\n{'='*50}")
            print(f"📋 Type: {type_name}")
            print(f"{'='*50}")
            
            fields = t.get('fields') or []
            for field in fields:
                field_name = field.get('name', '')
                field_type = field.get('type', {}).get('name', 'Unknown')
                print(f"   - {field_name}: {field_type}")
else:
    print(f"   ❌ Fehler: {response.status_code}")

# Teste Query für Dossier mit korrigierten Feldern
print("\n" + "=" * 70)
print("[2] Teste Dossier Query")
print("=" * 70)

# Einfache Query zuerst
dossier_query = '''
query GetDossiers {
    dossiers(first: 3) {
        data {
            id
        }
    }
}
'''

response = client._api_request(
    'POST',
    '/graphql',
    json={
        'operationName': 'GetDossiers',
        'query': dossier_query,
        'variables': {}
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"   Response: {json.dumps(data, indent=2)[:500]}")
    
    # Wenn wir IDs haben, hole Details zu einem Dossier
    dossiers = data.get('data', {}).get('dossiers', {}).get('data', [])
    if dossiers:
        dossier_id = dossiers[0].get('id')
        print(f"\n   Hole Details für Dossier {dossier_id}...")
        
        detail_query = f'''
        query GetDossierDetail {{
            dossier(id: {dossier_id}) {{
                id
            }}
        }}
        '''
        
        response = client._api_request(
            'POST',
            '/graphql',
            json={
                'operationName': 'GetDossierDetail',
                'query': detail_query,
                'variables': {}
            }
        )
        
        if response.status_code == 200:
            detail_data = response.json()
            print(f"   Detail: {json.dumps(detail_data, indent=2)[:500]}")

# Teste Appointment Query
print("\n" + "=" * 70)
print("[3] Teste Appointment Query")
print("=" * 70)

appointment_query = '''
query GetAppointments {
    appointments(first: 3) {
        data {
            id
            start_date_time
        }
    }
}
'''

response = client._api_request(
    'POST',
    '/graphql',
    json={
        'operationName': 'GetAppointments',
        'query': appointment_query,
        'variables': {}
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"   Response: {json.dumps(data, indent=2)[:500]}")
