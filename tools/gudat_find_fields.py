#!/usr/bin/env python3
"""
GUDAT - Erweiterte Feld-Suche mit Relations
"""

import json
import sys
sys.path.insert(0, '/opt/greiner-portal/tools')

from gudat_client import GudatClient

USERNAME = "florian.greiner@auto-greiner.de"
PASSWORD = "Hyundai2025!"

print("=" * 70)
print("GUDAT - ERWEITERTE FELD-SUCHE")
print("=" * 70)

client = GudatClient(USERNAME, PASSWORD)

if not client.login():
    print("Login fehlgeschlagen!")
    exit(1)

# Teste mehr Felder für Appointment
print("\n[1] Teste weitere Appointment-Felder...")

more_fields = [
    # Relations
    'dossier { id }',
    'team { id name }',
    'user { id name }',
    'member { id name }',
    # Mehr Felder
    'title', 'name', 'label',
    'duration', 'workload', 'work_units',
    'color', 'all_day', 'recurring',
    'notes', 'comment', 'description', 'memo',
    'status', 'state',
    'customer_name', 'vehicle_license_plate', 'vehicle_vin',
    'location', 'room',
]

working = ['id', 'start_date_time', 'end_date_time', 'type']

for field in more_fields:
    query = f'''
    query Test {{
        appointments(first: 1) {{
            data {{
                id
                {field}
            }}
        }}
    }}
    '''
    
    response = client._api_request('POST', '/graphql', json={'query': query})
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' not in data:
            working.append(field)
            print(f"   ✅ {field}")

print(f"\n   Alle funktionierenden Felder: {working}")

# Hole Appointments mit Dossier-Relation
print("\n" + "=" * 70)
print("[2] Hole Appointments mit Dossier-Details...")

if 'dossier { id }' in working:
    query = '''
    query GetAppointmentsWithDossier {
        appointments(first: 5, where: {column: START_DATE_TIME, operator: GTE, value: "2025-12-09"}) {
            data {
                id
                start_date_time
                end_date_time
                type
                dossier {
                    id
                    created_at
                    updated_at
                }
            }
        }
    }
    '''
    
    response = client._api_request('POST', '/graphql', json={'query': query})
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False)[:1500])

# Teste Dossier-Felder genauer
print("\n" + "=" * 70)
print("[3] Teste Dossier-Relations...")

dossier_relations = [
    'appointments { id start_date_time }',
    'events { id }',
    'customer { id name }',
    'vehicle { id license_plate }',
    'team { id name }',
    'user { id name }',
    'members { id }',
    'notes { id }',
    'files { id }',
    'tags { id }',
]

working_dossier = ['id', 'created_at', 'updated_at']

for field in dossier_relations:
    query = f'''
    query Test {{
        dossiers(first: 1) {{
            data {{
                id
                {field}
            }}
        }}
    }}
    '''
    
    response = client._api_request('POST', '/graphql', json={'query': query})
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' not in data:
            working_dossier.append(field)
            print(f"   ✅ {field}")

# Hole vollständiges Dossier
print("\n" + "=" * 70)
print("[4] Hole Dossier mit allen Details...")

# Baue Query mit allen funktionierenden Feldern
fields_str = '\n                '.join(working_dossier)
query = f'''
query GetFullDossier {{
    dossiers(first: 3, orderBy: [{{column: UPDATED_AT, order: DESC}}]) {{
        data {{
            {fields_str}
        }}
    }}
}}
'''

response = client._api_request('POST', '/graphql', json={'query': query})

if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
else:
    print(f"   ❌ {response.status_code}: {response.text[:200]}")

# Teste Scheduler-Events (die zeigen die Werkstatt-Termine)
print("\n" + "=" * 70)
print("[5] Teste Scheduler/Event Endpunkte...")

event_queries = [
    ('schedulerEvents', 'schedulerEvents(first: 5) { data { id } }'),
    ('events', 'events(first: 5) { data { id } }'),
    ('orderAppointments', 'orderAppointments(first: 5) { data { id } }'),
    ('serviceAppointments', 'serviceAppointments(first: 5) { data { id } }'),
    ('workOrders', 'workOrders(first: 5) { data { id } }'),
]

for name, query_part in event_queries:
    query = f'query Test {{ {query_part} }}'
    
    response = client._api_request('POST', '/graphql', json={'query': query})
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' not in data:
            print(f"   ✅ {name}: {json.dumps(data)[:100]}")
        else:
            print(f"   ❌ {name}: {data.get('errors', [{}])[0].get('message', '')[:50]}")
