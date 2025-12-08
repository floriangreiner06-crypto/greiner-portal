#!/usr/bin/env python3
"""
POC v2: Locosoft → Gudat Sync via WorkshopTasks
NUR LESEN
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')
sys.path.insert(0, '/opt/greiner-portal/tools')

import os
import json
import psycopg2
from datetime import datetime, date
from gudat_client import GudatClient

GUDAT_CONFIG = {
    'username': 'florian.greiner@auto-greiner.de',
    'password': 'Hyundai2025!'
}

def get_active_stampings():
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
    SELECT DISTINCT
        t.employee_number,
        eh.name as mechaniker_name,
        t.order_number,
        v.license_plate as kennzeichen,
        MIN(t.start_time) as start_time
    FROM times t
    JOIN employees_history eh ON t.employee_number = eh.employee_number 
        AND eh.is_latest_record = true
    LEFT JOIN orders o ON t.order_number = o.number
    LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
    WHERE t.type = 2
      AND t.end_time IS NULL
      AND t.order_number > 31
      AND DATE(t.start_time) = CURRENT_DATE
      AND eh.subsidiary IN (1, 2)
    GROUP BY t.employee_number, eh.name, t.order_number, v.license_plate
    ORDER BY t.order_number
    """
    
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    return [{
        'employee_number': r[0],
        'mechaniker_name': r[1],
        'order_number': r[2],
        'kennzeichen': r[3] or '?',
        'start_time': r[4]
    } for r in rows]

def get_workshop_tasks(client, target_date=None):
    if target_date is None:
        target_date = date.today().isoformat()
    
    # Query basierend auf HAR - vehicle ist unter dossier!
    query = """
    query GetWorkshopTasks($page: Int!, $itemsPerPage: Int!, $where: QueryWorkshopTasksWhereWhereConditions) {
      workshopTasks(
        first: $itemsPerPage
        page: $page
        where: $where
      ) {
        data {
          id
          start_date
          work_load
          work_state
          description
          workshopService {
            id
            name
          }
          resource {
            id
            name
          }
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
          }
        }
        paginatorInfo {
          total
        }
      }
    }
    """
    
    variables = {
        "page": 1,
        "itemsPerPage": 200,
        "where": {
            "AND": [
                {
                    "column": "START_DATE",
                    "operator": "EQ",
                    "value": target_date
                }
            ]
        }
    }
    
    response = client.session.post(
        f"{GudatClient.BASE_URL}/graphql",
        json={
            "operationName": "GetWorkshopTasks",
            "query": query,
            "variables": variables
        },
        headers={
            'Accept': 'application/json',
            'X-XSRF-TOKEN': client._get_xsrf(),
            'Content-Type': 'application/json'
        }
    )
    
    data = response.json()
    
    if 'errors' in data:
        print(f"GraphQL Fehler: {json.dumps(data['errors'], indent=2)}")
        return []
    
    return data.get('data', {}).get('workshopTasks', {}).get('data', [])

def find_task_by_kennzeichen(tasks, kennzeichen):
    if not kennzeichen or kennzeichen == '?':
        return None
    
    kz_norm = kennzeichen.replace(' ', '').replace('-', '').upper()
    
    for task in tasks:
        dossier = task.get('dossier')
        if dossier:
            vehicle = dossier.get('vehicle')
            if vehicle:
                task_kz = vehicle.get('license_plate', '')
                task_kz_norm = task_kz.replace(' ', '').replace('-', '').upper()
                if kz_norm == task_kz_norm:
                    return task
    return None

def find_task_by_order(tasks, order_number):
    for task in tasks:
        dossier = task.get('dossier')
        if dossier:
            for o in dossier.get('orders', []):
                if str(o.get('number')) == str(order_number):
                    return task
    return None

def main():
    print("=" * 70)
    print("POC v2: Locosoft → Gudat Sync via WorkshopTasks")
    print("=" * 70)
    print(f"Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Modus: NUR LESEN")
    print("=" * 70)
    
    print("\n[1] LOCOSOFT: Aktive Stempelungen...")
    stampings = get_active_stampings()
    
    if not stampings:
        print("    Keine aktiven Stempelungen gefunden.")
        return
    
    print(f"    Gefunden: {len(stampings)} Aufträge")
    for s in stampings:
        print(f"    - {s['mechaniker_name']:20} | Auftrag {s['order_number']:6} | {s['kennzeichen']}")
    
    print("\n[2] GUDAT: Login...")
    client = GudatClient(GUDAT_CONFIG['username'], GUDAT_CONFIG['password'])
    if not client.login():
        print("    FEHLER!")
        return
    print("    OK")
    
    print("\n[3] GUDAT: Lade WorkshopTasks für heute...")
    tasks = get_workshop_tasks(client)
    print(f"    Gefunden: {len(tasks)} Tasks")
    
    if tasks:
        print("\n    Alle heutigen Tasks:")
        for t in tasks:
            res = t.get('resource')
            res_name = res.get('name', '-') if res else '-'
            
            dossier = t.get('dossier', {})
            vehicle = dossier.get('vehicle', {}) if dossier else {}
            lp = vehicle.get('license_plate', '?') if vehicle else '?'
            
            orders = dossier.get('orders', []) if dossier else []
            order_nr = orders[0].get('number', '?') if orders else '?'
            
            state = t.get('work_state', '?')
            icon = {'NEW': '⚪', 'IN_WORK': '🔵', 'DONE': '✅', 'PAUSED': '⏸️'}.get(state, '❓')
            print(f"      {icon} {t['id']:5} | {lp:15} | Order {order_nr:>6} | {res_name}")
    
    print("\n[4] MAPPING: Locosoft → Gudat")
    print("-" * 70)
    
    for s in stampings:
        order_nr = s['order_number']
        kz = s['kennzeichen']
        mech = s['mechaniker_name']
        
        print(f"\n    {mech}: Auftrag {order_nr} ({kz})")
        
        task = find_task_by_order(tasks, order_nr)
        if not task and kz != '?':
            task = find_task_by_kennzeichen(tasks, kz)
            if task:
                print(f"      (via Kennzeichen gefunden)")
        
        if not task:
            print(f"      ❌ Kein WorkshopTask gefunden")
            continue
        
        task_id = task['id']
        state = task.get('work_state', '?')
        res = task.get('resource')
        res_name = res.get('name', '?') if res else 'Nicht zugewiesen'
        
        print(f"      ✓ Task ID: {task_id}")
        print(f"      ✓ Status: {state}")
        print(f"      ✓ Resource: {res_name}")
        
        print(f"\n      📋 WÜRDE AUSFÜHREN:")
        if state == 'IN_WORK':
            print(f"         Nichts - bereits IN_WORK")
        else:
            print(f"         → updateWorkshopTask(id: {task_id}, work_state: IN_WORK)")
    
    print("\n" + "=" * 70)
    print("POC FERTIG - Keine Änderungen")
    print("=" * 70)

if __name__ == '__main__':
    main()
