#!/usr/bin/env python3
"""
Analyse: Garantieakte 220266 Aidenberger
========================================
TAG 173: Analysiert eine vollständige Garantieakte zur Automatisierung
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.locosoft_helpers import get_locosoft_connection
from tools.gudat_client import GudatClient
from datetime import date

ORDER_NUMBER = 220266

GUDAT_CONFIG = {
    'username': 'florian.greiner@auto-greiner.de',
    'password': 'Hyundai2025!'
}


def analyse_locosoft_daten(order_number):
    """Analysiert Locosoft-Daten für den Auftrag"""
    print(f"\n{'='*80}")
    print(f"LOCOSOFT-DATEN für Auftrag {order_number}")
    print(f"{'='*80}\n")
    
    conn = get_locosoft_connection()
    cursor = conn.cursor()
    
    # Auftrag
    cursor.execute("""
        SELECT 
            o.number,
            o.order_date,
            o.order_taking_employee_no,
            eh_sb.name as serviceberater,
            o.vehicle_number,
            o.order_customer
        FROM orders o
        LEFT JOIN employees_history eh_sb ON o.order_taking_employee_no = eh_sb.employee_number 
            AND eh_sb.is_latest_record = true
        WHERE o.number = %s
    """, [order_number])
    
    auftrag = cursor.fetchone()
    if not auftrag:
        print(f"❌ Auftrag {order_number} nicht gefunden")
        conn.close()
        return None
    
    print(f"✅ Auftrag gefunden:")
    print(f"   Nummer: {auftrag[0]}")
    print(f"   Datum: {auftrag[1]}")
    print(f"   Serviceberater: {auftrag[3]}")
    
    # Arbeitspositionen
    cursor.execute("""
        SELECT 
            l.order_position,
            l.order_position_line,
            l.labour_operation_id,
            l.text_line,
            l.time_units,
            l.mechanic_no,
            eh_mech.name as mechaniker,
            l.is_invoiced
        FROM labours l
        LEFT JOIN employees_history eh_mech ON l.mechanic_no = eh_mech.employee_number 
            AND eh_mech.is_latest_record = true
        WHERE l.order_number = %s
        ORDER BY l.order_position, l.order_position_line
    """, [order_number])
    
    positionen = cursor.fetchall()
    print(f"\n✅ {len(positionen)} Arbeitsposition(en) gefunden:")
    for pos in positionen[:10]:
        print(f"   Pos {pos[0]}.{pos[1]}: {pos[2] or 'N/A'} - {pos[3][:50] if pos[3] else 'N/A'}...")
        print(f"      AW: {pos[4]}, Mechaniker: {pos[6] or 'N/A'}")
    
    # Stempelzeiten
    cursor.execute("""
        SELECT 
            t.employee_number,
            eh.name as mechaniker,
            t.start_time,
            t.end_time,
            t.duration_minutes,
            t.type,
            t.order_position,
            t.order_position_line
        FROM times t
        LEFT JOIN employees_history eh ON t.employee_number = eh.employee_number 
            AND eh.is_latest_record = true
        WHERE t.order_number = %s
          AND t.type = 2
        ORDER BY t.start_time
    """, [order_number])
    
    stempelzeiten = cursor.fetchall()
    print(f"\n✅ {len(stempelzeiten)} Stempelzeit(en) gefunden:")
    
    # Gruppiere nach Position
    by_position = {}
    unzugeordnet = []
    
    for st in stempelzeiten:
        pos = st[6]  # order_position
        pos_line = st[7]  # order_position_line
        
        if pos and pos_line:
            key = f"{pos}.{pos_line}"
            if key not in by_position:
                by_position[key] = []
            by_position[key].append(st)
        else:
            unzugeordnet.append(st)
    
    print(f"   Zugeordnet zu Positionen: {len(by_position)}")
    for key, zeiten in list(by_position.items())[:5]:
        total_min = sum(z[4] for z in zeiten)
        print(f"   Pos {key}: {len(zeiten)} Zeiten, {total_min} Min gesamt")
    
    if unzugeordnet:
        print(f"   ⚠️  {len(unzugeordnet)} unzugeordnete Stempelzeiten")
        for st in unzugeordnet[:3]:
            print(f"      {st[1]}: {st[2]} - {st[3]} ({st[4]} Min)")
    
    # Teile
    cursor.execute("""
        SELECT 
            p.part_number,
            pm.description,
            p.amount,
            p.sum,
            p.is_invoiced
        FROM parts p
        LEFT JOIN parts_master pm ON p.part_number = pm.part_number
        WHERE p.order_number = %s
        ORDER BY p.order_position
    """, [order_number])
    
    teile = cursor.fetchall()
    print(f"\n✅ {len(teile)} Teil(e) gefunden:")
    for teil in teile[:5]:
        print(f"   {teil[0]}: {teil[1][:50] if teil[1] else 'N/A'}...")
        print(f"      Menge: {teil[2]}, Preis: {teil[3]:.2f}€")
    
    conn.close()
    
    return {
        'auftrag': auftrag,
        'positionen': positionen,
        'stempelzeiten': stempelzeiten,
        'stempelzeiten_by_position': by_position,
        'unzugeordnete_stempelzeiten': unzugeordnet,
        'teile': teile
    }


def analyse_gudat_daten(order_number):
    """Analysiert GUDAT-Daten für den Auftrag"""
    print(f"\n{'='*80}")
    print(f"GUDAT-DATEN für Auftrag {order_number}")
    print(f"{'='*80}\n")
    
    try:
        client = GudatClient(GUDAT_CONFIG['username'], GUDAT_CONFIG['password'])
        if not client.login():
            print("❌ GUDAT-Login fehlgeschlagen")
            return None
        
        print("✅ GUDAT-Login erfolgreich")
        
        # Suche Dossier
        target_date = date.today().isoformat()
        
        query_tasks = """
        query GetWorkshopTasks($page: Int!, $itemsPerPage: Int!, $where: QueryWorkshopTasksWhereWhereConditions) {
          workshopTasks(first: $itemsPerPage, page: $page, where: $where) {
            data {
              id
              description
              dossier {
                id
                orders { number }
              }
            }
          }
        }
        """
        
        variables = {
            "page": 1,
            "itemsPerPage": 200,
            "where": {
                "AND": [{"column": "START_DATE", "operator": "EQ", "value": target_date}]
            }
        }
        
        response = client.session.post(
            f"{client.BASE_URL}/graphql",
            json={"operationName": "GetWorkshopTasks", "query": query_tasks, "variables": variables},
            headers={
                'Accept': 'application/json',
                'X-XSRF-TOKEN': client._get_xsrf(),
                'Content-Type': 'application/json'
            }
        )
        
        data = response.json()
        
        if 'errors' in data:
            print(f"❌ GraphQL-Fehler: {data['errors']}")
            return None
        
        tasks = data.get('data', {}).get('workshopTasks', {}).get('data', [])
        
        # Finde dossier_id
        dossier_id = None
        for task in tasks:
            orders = task.get('dossier', {}).get('orders', [])
            for order in orders:
                if order.get('number') == str(order_number):
                    dossier_id = task.get('dossier', {}).get('id')
                    break
        
        if not dossier_id:
            print(f"⚠️  Dossier für Auftrag {order_number} nicht gefunden")
            return None
        
        print(f"✅ Dossier gefunden (ID: {dossier_id})")
        
        # Hole vollständige Dossier-Daten
        query_dossier = """
        query GetDossierDrawerData($id: ID!) {
          dossier(id: $id) {
            id
            note
            workshopTasks {
              id
              description
              work_load
              work_state
            }
            attachments {
              id
              name
              file_name
              mime_type
              size
              created_at
            }
          }
        }
        """
        
        response = client.session.post(
            f"{client.BASE_URL}/graphql",
            json={"operationName": "GetDossierDrawerData", "query": query_dossier, "variables": {"id": str(dossier_id)}},
            headers={
                'Accept': 'application/json',
                'X-XSRF-TOKEN': client._get_xsrf(),
                'Content-Type': 'application/json'
            }
        )
        
        data = response.json()
        
        if 'errors' in data:
            print(f"❌ GraphQL-Fehler: {data['errors']}")
            return None
        
        dossier = data.get('data', {}).get('dossier')
        
        if not dossier:
            print(f"❌ Dossier-Daten nicht gefunden")
            return None
        
        tasks = dossier.get('workshopTasks', [])
        attachments = dossier.get('attachments', [])
        
        print(f"\n✅ {len(tasks)} Task(s) gefunden:")
        for task in tasks:
            print(f"   Task {task.get('id')}: {task.get('description', '')[:60]}...")
        
        print(f"\n✅ {len(attachments)} Attachment(s) gefunden:")
        bilder = [a for a in attachments if a.get('mime_type', '').startswith('image/')]
        andere = [a for a in attachments if not a.get('mime_type', '').startswith('image/')]
        
        print(f"   Bilder: {len(bilder)}")
        for att in bilder[:5]:
            print(f"      - {att.get('name', 'N/A')} ({att.get('file_name', 'N/A')})")
            print(f"        Typ: {att.get('mime_type', 'N/A')}, Größe: {att.get('size', 0)} Bytes")
        
        if andere:
            print(f"   Andere Dateien: {len(andere)}")
            for att in andere[:3]:
                print(f"      - {att.get('name', 'N/A')} ({att.get('file_name', 'N/A')})")
        
        return {
            'dossier_id': dossier.get('id'),
            'dossier_note': dossier.get('note'),
            'tasks': tasks,
            'attachments': attachments,
            'bilder': bilder,
            'andere_dateien': andere
        }
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print(f"\n{'='*80}")
    print(f"ANALYSE: GARANTIEAKTE {ORDER_NUMBER}")
    print(f"{'='*80}\n")
    
    # Locosoft
    locosoft_daten = analyse_locosoft_daten(ORDER_NUMBER)
    
    # GUDAT
    gudat_daten = analyse_gudat_daten(ORDER_NUMBER)
    
    # Zusammenfassung
    print(f"\n{'='*80}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*80}\n")
    
    if locosoft_daten:
        print(f"✅ Locosoft: {len(locosoft_daten['positionen'])} Positionen, {len(locosoft_daten['stempelzeiten'])} Stempelzeiten")
        print(f"   Unzugeordnete Stempelzeiten: {len(locosoft_daten['unzugeordnete_stempelzeiten'])}")
    
    if gudat_daten:
        print(f"✅ GUDAT: {len(gudat_daten['tasks'])} Tasks, {len(gudat_daten['attachments'])} Attachments")
        print(f"   Bilder: {len(gudat_daten['bilder'])}")
    
    print(f"\n{'='*80}")
    print("AUTOMATISIERUNGS-POTENZIAL")
    print(f"{'='*80}\n")
    
    print("1. ✅ Stempelzeiten-Verteilung:")
    print("   - write_work_order_times() unterstützt workOrderLineNumber")
    print("   - Kann unzugeordnete Stempelzeiten auf Positionen verteilen")
    
    print("\n2. ✅ Bilder aus GUDAT:")
    print("   - attachments[] mit mime_type='image/*' verfügbar")
    print("   - Kann in PDF eingebunden werden")
    
    print("\n3. ✅ Vollständige Akte:")
    print("   - Arbeitskarte-PDF (bereits implementiert)")
    print("   - Bilder aus GUDAT")
    print("   - Alle Dokumente kombinieren")


if __name__ == '__main__':
    main()
