#!/usr/bin/env python3
"""
POC: Locosoft → Gudat Stempeluhr-Sync
Phase 1: NUR LESEN
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')
sys.path.insert(0, '/opt/greiner-portal/tools')

import os
import json
import psycopg2
from datetime import datetime
from gudat_client import GudatClient

GUDAT_CONFIG = {
    'username': 'florian.greiner@auto-greiner.de',
    'password': 'Hyundai2025!'
}

def get_active_stampings():
    """Holt alle aktiven Stempelungen"""
    
    env_path = '/opt/greiner-portal/config/.env'
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, val = line.strip().split('=', 1)
                os.environ[key] = val
    
    conn = psycopg2.connect(
        host=os.environ['LOCOSOFT_HOST'],
        database=os.environ['LOCOSOFT_DATABASE'],
        user=os.environ['LOCOSOFT_USER'],
        password=os.environ['LOCOSOFT_PASSWORD']
    )
    
    query = """
    SELECT 
        t.employee_number,
        eh.name as mechaniker_name,
        t.order_number,
        v.license_plate as kennzeichen,
        t.start_time
    FROM times t
    JOIN employees_history eh ON t.employee_number = eh.employee_number 
        AND eh.is_latest_record = true
    LEFT JOIN orders o ON t.order_number = o.number
    LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
    WHERE t.type = 2
      AND t.end_time IS NULL
      AND t.order_number > 31
      AND DATE(t.start_time) = CURRENT_DATE
    ORDER BY t.start_time DESC
    """
    
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            'employee_number': row[0],
            'mechaniker_name': row[1],
            'order_number': row[2],
            'kennzeichen': row[3] or '?',
            'start_time': row[4]
        })
    
    return results

def find_gudat_order(client, locosoft_order_number):
    """Sucht Order in Gudat"""
    
    for page in range(100, 110):
        query = f"""
        query {{
          orders(first: 200, page: {page}) {{
            data {{ id number }}
          }}
        }}
        """
        
        response = client.session.post(
            f"{GudatClient.BASE_URL}/graphql",
            json={"query": query},
            headers={
                'Accept': 'application/json',
                'X-XSRF-TOKEN': client._get_xsrf(),
                'Content-Type': 'application/json'
            }
        )
        
        data = response.json()
        orders = data.get('data', {}).get('orders', {}).get('data', [])
        
        if not orders:
            continue
        
        for o in orders:
            if str(o.get('number')) == str(locosoft_order_number):
                return {'id': o['id'], 'number': o['number']}
    
    return None

def find_gudat_dossier(client, order_id):
    """Findet Dossier für Order"""
    
    query = """
    query {
      dossiers(first: 100, orderBy: [{column: UPDATED_AT, order: DESC}]) {
        data {
          id
          vehicle { license_plate }
          orders { id number }
          states { id name category { id name } }
        }
      }
    }
    """
    
    response = client.session.post(
        f"{GudatClient.BASE_URL}/graphql",
        json={"query": query},
        headers={
            'Accept': 'application/json',
            'X-XSRF-TOKEN': client._get_xsrf(),
            'Content-Type': 'application/json'
        }
    )
    
    data = response.json()
    dossiers = data.get('data', {}).get('dossiers', {}).get('data', [])
    
    for d in dossiers:
        for o in d.get('orders', []):
            if str(o.get('id')) == str(order_id):
                return {
                    'id': d['id'],
                    'kennzeichen': d.get('vehicle', {}).get('license_plate') if d.get('vehicle') else None,
                    'states': d.get('states', [])
                }
    
    return None

def get_mechanik_state(dossier):
    """Extrahiert Mechanik-Status"""
    if not dossier:
        return None
    
    for state in dossier.get('states', []):
        cat = state.get('category', {})
        if cat and cat.get('name') == 'Mechanik':
            return state
    return None

def main():
    print("=" * 70)
    print("POC: Locosoft → Gudat Stempeluhr-Sync")
    print("=" * 70)
    print(f"Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Modus: NUR LESEN")
    print("=" * 70)
    
    print("\n[1] LOCOSOFT: Aktive Stempelungen...")
    stampings = get_active_stampings()
    
    if not stampings:
        print("    Keine aktiven Stempelungen gefunden.")
        return
    
    print(f"    Gefunden: {len(stampings)} aktive Stempelungen")
    for s in stampings:
        print(f"    - {s['mechaniker_name']}: Auftrag {s['order_number']} ({s['kennzeichen']})")
    
    print("\n[2] GUDAT: Login...")
    client = GudatClient(GUDAT_CONFIG['username'], GUDAT_CONFIG['password'])
    if not client.login():
        print("    FEHLER: Login fehlgeschlagen!")
        return
    print("    OK")
    
    print("\n[3] MAPPING: Locosoft → Gudat")
    print("-" * 70)
    
    for s in stampings:
        order_nr = s['order_number']
        print(f"\n    Auftrag {order_nr} ({s['kennzeichen']}):")
        
        gudat_order = find_gudat_order(client, order_nr)
        
        if not gudat_order:
            print(f"      ❌ Order NICHT in Gudat gefunden")
            continue
        
        print(f"      ✓ Gudat Order-ID: {gudat_order['id']}")
        
        dossier = find_gudat_dossier(client, gudat_order['id'])
        
        if not dossier:
            print(f"      ❌ Dossier NICHT in aktuellen 100 gefunden")
            continue
        
        print(f"      ✓ Gudat Dossier-ID: {dossier['id']}")
        
        mech_state = get_mechanik_state(dossier)
        if mech_state:
            print(f"      → Mechanik-Status: [{mech_state['id']}] {mech_state['name']}")
        else:
            print(f"      → Kein Mechanik-Status")
        
        print(f"\n      📋 WÜRDE AUSFÜHREN:")
        if mech_state and mech_state['id'] == '18':
            print(f"         Nichts - bereits 'Mechanik in Arbeit'")
        else:
            print(f"         → setStatable(dossier: {dossier['id']}, state: 18)")
    
    print("\n" + "=" * 70)
    print("POC FERTIG - Keine Änderungen")
    print("=" * 70)

if __name__ == '__main__':
    main()
