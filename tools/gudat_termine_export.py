#!/usr/bin/env python3
"""
GUDAT - Vollständiger Termin-Export mit Locosoft-Auftragsnummer
"""

import json
import sys
sys.path.insert(0, '/opt/greiner-portal/tools')

from gudat_client import GudatClient

USERNAME = "florian.greiner@auto-greiner.de"
PASSWORD = "Hyundai2025!"

print("=" * 70)
print("GUDAT - TERMINE MIT LOCOSOFT AUFTRAGSNUMMERN")
print("=" * 70)

client = GudatClient(USERNAME, PASSWORD)

if not client.login():
    print("Login fehlgeschlagen!")
    exit(1)

# Hole Termine für Montag 08.12.2025
print("\n📅 Termine am 08.12.2025:")
print("=" * 70)

query = '''
query GetAppointmentsWithOrders {
    appointments(
        first: 20, 
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
                vehicle {
                    id
                    license_plate
                }
                orders {
                    id
                    number
                }
                states {
                    id
                    name
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
    
    print(f"\n{'Zeit':<12} {'Kennzeichen':<15} {'Locosoft-Nr':<12} {'Typ':<15} {'Status'}")
    print("-" * 70)
    
    for apt in appointments:
        dossier = apt.get('dossier', {}) or {}
        vehicle = dossier.get('vehicle', {}) or {}
        orders = dossier.get('orders', []) or []
        states = dossier.get('states', []) or []
        
        time = apt['start_date_time'].split(' ')[1][:5] if apt.get('start_date_time') else '?'
        plate = vehicle.get('license_plate', '-')
        order_num = orders[0].get('number', '-') if orders else '-'
        apt_type = apt.get('type', '-')
        status_list = [s.get('name', '') for s in states[:2]]
        status = ', '.join(status_list)[:30] if status_list else '-'
        
        print(f"{time:<12} {plate:<15} {order_num:<12} {apt_type:<15} {status}")

# Zeige Struktur für ML/Integration
print("\n" + "=" * 70)
print("📊 DATENSTRUKTUR FÜR INTEGRATION:")
print("=" * 70)

print("""
Gudat → Locosoft Mapping:
========================
Gudat Appointment
  └─ dossier
       ├─ vehicle
       │    └─ license_plate    → Fahrzeug-Kennzeichen
       ├─ orders[]
       │    └─ number           → LOCOSOFT AUFTRAGSNUMMER ⭐
       └─ states[]
            └─ name             → Vorgangsstatus

Beispiel SQL für Join:
=====================
SELECT 
    g.appointment_time,
    g.license_plate,
    g.locosoft_order_number,
    l.auftrag_id,
    l.kunde_name
FROM gudat_termine g
JOIN locosoft_auftraege l ON g.locosoft_order_number = l.auftrag_nr
""")

# Export als JSON für weitere Verarbeitung
print("\n" + "=" * 70)
print("💾 Export als JSON...")

export_data = []
for apt in appointments:
    dossier = apt.get('dossier', {}) or {}
    vehicle = dossier.get('vehicle', {}) or {}
    orders = dossier.get('orders', []) or []
    states = dossier.get('states', []) or []
    
    export_data.append({
        'gudat_appointment_id': apt.get('id'),
        'start_time': apt.get('start_date_time'),
        'end_time': apt.get('end_date_time'),
        'type': apt.get('type'),
        'license_plate': vehicle.get('license_plate'),
        'locosoft_order_number': orders[0].get('number') if orders else None,
        'gudat_order_id': orders[0].get('id') if orders else None,
        'gudat_dossier_id': dossier.get('id'),
        'status': [s.get('name') for s in states]
    })

with open('/tmp/gudat_termine_export.json', 'w') as f:
    json.dump(export_data, f, indent=2, ensure_ascii=False)

print(f"   Gespeichert: /tmp/gudat_termine_export.json ({len(export_data)} Termine)")

# Zeige ein paar Beispiele
print("\n   Beispiel-Datensatz:")
if export_data:
    print(json.dumps(export_data[0], indent=4, ensure_ascii=False))
