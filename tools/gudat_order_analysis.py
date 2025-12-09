#!/usr/bin/env python3
"""
GUDAT - Order-Felder finden (dort ist die Locosoft-Auftragsnummer!)
"""

import json
import sys
sys.path.insert(0, '/opt/greiner-portal/tools')

from gudat_client import GudatClient

USERNAME = "florian.greiner@auto-greiner.de"
PASSWORD = "Hyundai2025!"

print("=" * 70)
print("GUDAT - ORDER FELDER ANALYSIEREN")
print("=" * 70)

client = GudatClient(USERNAME, PASSWORD)

if not client.login():
    print("Login fehlgeschlagen!")
    exit(1)

# Teste Order-Felder
print("\n[1] Suche Felder in Order 21584...")

order_fields = [
    # Nummern
    'id', 'number', 'order_number', 'orderNumber', 'no', 'nr',
    'reference', 'ref', 'code', 'identifier',
    'external_id', 'external_number', 'externalId', 'externalNumber',
    'dms_id', 'dms_number', 'erp_id', 'erp_number',
    'locosoft_id', 'locosoft_number',
    'auftragsnummer', 'auftrags_nummer',
    # Basis
    'name', 'title', 'description', 'type', 'status', 'state',
    'created_at', 'updated_at',
    # Zeiten
    'date', 'start', 'end', 'due_date', 'deadline',
    # Arbeit
    'workload', 'duration', 'estimated_time', 'work_units',
    'planned_workload', 'actual_workload',
    # Relations
    'team', 'user', 'member', 'assignee',
    'customer', 'vehicle', 'dossier',
]

working = []

for field in order_fields:
    query = f'''
    query Test {{
        orders(first: 1) {{
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
            order = data.get('data', {}).get('orders', {}).get('data', [{}])[0]
            value = order.get(field)
            if value is not None or field == 'id':
                working.append(field)
                print(f"   ✅ {field}: {value}")

print(f"\n   Funktionierende Felder: {working}")

# Hole Order 21584 mit allen Feldern
print("\n" + "=" * 70)
print("[2] Hole Order 21584 (DEG-X 212) mit allen Feldern...")

if working:
    fields_str = '\n                '.join([f for f in working if '{' not in f])
    query = f'''
    query GetOrder {{
        order(id: 21584) {{
            {fields_str}
        }}
    }}
    '''
    
    response = client._api_request('POST', '/graphql', json={'query': query})
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))

# Teste auch Sub-Relations in Order
print("\n" + "=" * 70)
print("[3] Teste Order Sub-Relations...")

sub_relations = [
    'team { id name }',
    'dossier { id }',
    'vehicle { id license_plate }',
    'customer { id name }',
    'user { id name }',
    'member { id name }',
    'appointments { id }',
    'states { id name }',
    'tags { id }',
    'notes { id }',
    'tasks { id }',
    'items { id }',
    'lines { id }',
    'positions { id }',
    'services { id }',
    'parts { id }',
]

for sub in sub_relations:
    query = f'''
    query Test {{
        order(id: 21584) {{
            id
            {sub}
        }}
    }}
    '''
    
    response = client._api_request('POST', '/graphql', json={'query': query})
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' not in data:
            order = data.get('data', {}).get('order', {})
            field_name = sub.split(' ')[0]
            if order and order.get(field_name):
                print(f"   ✅ {sub}: {json.dumps(order.get(field_name))[:100]}")

# Hole mehrere Orders und schaue nach Mustern
print("\n" + "=" * 70)
print("[4] Hole neueste Orders...")

query = '''
query GetRecentOrders {
    orders(first: 10, orderBy: [{column: ID, order: DESC}]) {
        data {
            id
        }
    }
}
'''

response = client._api_request('POST', '/graphql', json={'query': query})

if response.status_code == 200:
    data = response.json()
    orders = data.get('data', {}).get('orders', {}).get('data', [])
    print(f"   Neueste Order IDs: {[o['id'] for o in orders]}")
    
    # Die Auftragsnummer 219379 aus dem Screenshot...
    # Vielleicht ist die Order-ID selbst die Auftragsnummer?
    print(f"\n   🤔 Vergleich:")
    print(f"      Gudat Order ID: 21584")
    print(f"      Locosoft Auftragsnummer: 219379")
    print(f"      → Unterschiedliche Nummern, also muss es ein Feld geben!")
