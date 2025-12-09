#!/usr/bin/env python3
"""
GUDAT - Einzelne Termine/Aufträge analysieren
Suche nach Locosoft-Auftragsnummern
"""

import json
import sys
sys.path.insert(0, '/opt/greiner-portal/tools')

from gudat_client import GudatClient

USERNAME = "florian.greiner@auto-greiner.de"
PASSWORD = "Hyundai2025!"

print("=" * 70)
print("GUDAT TERMIN-ANALYSE")
print("=" * 70)

client = GudatClient(USERNAME, PASSWORD)

if not client.login():
    print("Login fehlgeschlagen!")
    exit(1)

# Teste verschiedene API-Endpunkte für Termine
print("\n[1] Teste API-Endpunkte für Termine...")

endpoints = [
    '/api/v1/appointments',
    '/api/v1/orders',
    '/api/v1/dossiers',
    '/api/v1/events',
    '/api/v1/calendar',
    '/api/v1/config',
]

for endpoint in endpoints:
    try:
        response = client._api_request('GET', endpoint, params={'date': '2025-12-09'})
        status = response.status_code
        
        if status == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"   ✅ {endpoint}: {len(data)} Einträge")
                if data:
                    print(f"      Keys: {list(data[0].keys())[:10]}")
            elif isinstance(data, dict):
                print(f"   ✅ {endpoint}: Dict mit Keys: {list(data.keys())[:10]}")
        else:
            print(f"   ❌ {endpoint}: {status}")
    except Exception as e:
        print(f"   ❌ {endpoint}: {e}")

# Teste GraphQL
print("\n[2] Teste GraphQL für Dossiers/Aufträge...")

graphql_queries = [
    {
        'name': 'GetDossiers',
        'query': '''
            query GetDossiers {
                dossiers(first: 5) {
                    data {
                        id
                        order_number
                        external_order_number
                        customer_name
                        vehicle_license_plate
                        status
                    }
                }
            }
        '''
    },
    {
        'name': 'GetAppointments',
        'query': '''
            query GetAppointments {
                appointments(first: 5) {
                    data {
                        id
                        start_time
                        end_time
                        order_number
                        status
                    }
                }
            }
        '''
    }
]

for gq in graphql_queries:
    try:
        response = client._api_request(
            'POST', 
            '/graphql',
            json={
                'operationName': gq['name'],
                'query': gq['query'],
                'variables': {}
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n   ✅ {gq['name']}:")
            print(f"      {json.dumps(data, indent=6)[:500]}...")
        else:
            print(f"   ❌ {gq['name']}: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ {gq['name']}: {e}")

# Teste Disposition-Daten
print("\n[3] Teste Disposition-API...")

dispo_endpoints = [
    '/api/v1/disposition',
    '/api/v1/disposition/events',
    '/api/v1/scheduler/events',
]

for endpoint in dispo_endpoints:
    try:
        response = client._api_request('GET', endpoint, params={
            'start': '2025-12-09',
            'end': '2025-12-09'
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {endpoint}: {type(data).__name__}")
            if isinstance(data, list) and data:
                print(f"      Erster Eintrag Keys: {list(data[0].keys())}")
            elif isinstance(data, dict):
                print(f"      Keys: {list(data.keys())[:10]}")
        else:
            print(f"   ❌ {endpoint}: {response.status_code}")
    except Exception as e:
        print(f"   ❌ {endpoint}: {e}")

print("\n" + "=" * 70)
print("Vollständige Analyse der verfügbaren Endpunkte abgeschlossen")
print("=" * 70)
