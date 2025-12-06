#!/usr/bin/env python3
"""
GUDAT - Suche in allen möglichen Strukturen nach Auftragsnummer
"""

import json
import sys
sys.path.insert(0, '/opt/greiner-portal/tools')

from gudat_client import GudatClient

USERNAME = "florian.greiner@auto-greiner.de"
PASSWORD = "Hyundai2025!"

print("=" * 70)
print("GUDAT - TIEFE SUCHE NACH AUFTRAGSNUMMER")
print("=" * 70)

client = GudatClient(USERNAME, PASSWORD)

if not client.login():
    print("Login fehlgeschlagen!")
    exit(1)

# Suche Dossier 18980 (das war DEG-X 212 von vorhin)
print("\n[1] Hole Dossier 18980 (DEG-X 212)...")

# Teste verschiedene Sub-Relations
sub_queries = [
    ('orders', 'orders { id }'),
    ('order', 'order { id }'),
    ('job', 'job { id }'),
    ('jobs', 'jobs { id }'),
    ('work_orders', 'work_orders { id }'),
    ('work_order', 'work_order { id }'),
    ('services', 'services { id }'),
    ('repairs', 'repairs { id }'),
    ('custom_fields', 'custom_fields { key value }'),
    ('customFields', 'customFields { key value }'),
    ('fields', 'fields { key value }'),
    ('metadata', 'metadata'),
    ('meta', 'meta'),
    ('data', 'data'),
    ('attributes', 'attributes'),
    ('properties', 'properties'),
    ('details', 'details'),
    ('info', 'info'),
    ('notes', 'notes { id content }'),
    ('comments', 'comments { id content }'),
    ('history', 'history { id }'),
    ('statuses', 'statuses { id name }'),
    ('status', 'status { id name }'),
    ('states', 'states { id name }'),
    ('processes', 'processes { id name status }'),
    ('workflows', 'workflows { id }'),
]

for name, sub in sub_queries:
    query = f'''
    query Test {{
        dossier(id: 18980) {{
            id
            {sub}
        }}
    }}
    '''
    
    response = client._api_request('POST', '/graphql', json={'query': query})
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' not in data:
            result = data.get('data', {}).get('dossier', {})
            if result and result.get(name.split(' ')[0]):
                print(f"   ✅ {name}: {json.dumps(result)[:200]}")

# Teste ob es einen separaten Query für Orders gibt
print("\n" + "=" * 70)
print("[2] Suche nach Order-bezogenen Queries...")

order_queries = [
    'orders(first: 1) { data { id } }',
    'workOrders(first: 1) { data { id } }',
    'serviceOrders(first: 1) { data { id } }',
    'repairOrders(first: 1) { data { id } }',
    'jobs(first: 1) { data { id } }',
]

for q in order_queries:
    query = f'query Test {{ {q} }}'
    
    response = client._api_request('POST', '/graphql', json={'query': query})
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' not in data:
            print(f"   ✅ {q.split('(')[0]}")

# Prüfe die HAR-Datei oder API-Endpunkte die der Browser nutzt
print("\n" + "=" * 70)
print("[3] Teste REST API Endpunkte für Aufträge...")

endpoints = [
    '/api/v1/orders',
    '/api/v1/work-orders',
    '/api/v1/service-orders',
    '/api/v1/jobs',
    '/api/v1/repairs',
    '/api/v1/dossiers/18980',
    '/api/v1/dossier/18980',
    '/api/v1/dossiers/18980/orders',
    '/api/v1/dossiers/18980/details',
]

for endpoint in endpoints:
    response = client._api_request('GET', endpoint)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ {endpoint}")
        print(f"      {json.dumps(data)[:200]}...")
    elif response.status_code != 404:
        print(f"   ⚠️ {endpoint}: {response.status_code}")

# Hole Termine für Montag und zeige alle Daten
print("\n" + "=" * 70)
print("[4] Hole aktuelle Termine mit allen verfügbaren Feldern...")

query = '''
query GetCurrentAppointments {
    appointments(
        first: 10, 
        where: {
            AND: [
                {column: START_DATE_TIME, operator: GTE, value: "2025-12-08"},
                {column: START_DATE_TIME, operator: LT, value: "2025-12-09"}
            ]
        }
    ) {
        data {
            id
            start_date_time
            end_date_time
            type
            dossier {
                id
                created_at
                updated_at
                vehicle {
                    id
                    license_plate
                }
                appointments {
                    id
                }
                tags {
                    id
                }
            }
        }
    }
}
'''

response = client._api_request('POST', '/graphql', json={'query': query})

if response.status_code == 200:
    data = response.json()
    appointments = data.get('data', {}).get('appointments', {}).get('data', [])
    
    print(f"\n   {len(appointments)} Termine am 08.12.:")
    
    for apt in appointments[:5]:
        dossier = apt.get('dossier', {})
        vehicle = dossier.get('vehicle', {}) if dossier else {}
        plate = vehicle.get('license_plate', '?')
        
        print(f"\n   📅 Termin {apt['id']}")
        print(f"      Zeit: {apt['start_date_time']} - {apt['end_date_time']}")
        print(f"      Typ: {apt['type']}")
        print(f"      Kennzeichen: {plate}")
        print(f"      Dossier ID: {dossier.get('id', '?')}")
        
        # Suche DEG-X 212
        if plate and 'DEG-X' in plate and '212' in plate:
            print(f"\n   🎯 DEG-X 212 GEFUNDEN!")
            print(f"      Dossier: {json.dumps(dossier, indent=6)}")
