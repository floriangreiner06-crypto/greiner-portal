#!/usr/bin/env python3
"""
Fügt Queries zu TEK und BWA Dashboards hinzu
Verwendet die korrekte Metabase API-Struktur
"""

import requests
import json

METABASE_URL = "http://localhost:3001"

# Dashboard- und Query-IDs
DASHBOARDS = {
    "TEK": {
        "id": 3,
        "queries": [42, 43, 44]
    },
    "BWA": {
        "id": 8,
        "queries": [49, 50, 51]
    }
}

def get_session():
    """Holt Metabase Session Token"""
    response = requests.post(
        f"{METABASE_URL}/api/session",
        json={"username": "admin@auto-greiner.de", "password": "Drive2026!"}
    )
    if response.status_code == 200:
        return response.json()["id"]
    else:
        print(f"❌ Login fehlgeschlagen: {response.status_code}")
        return None

def get_dashboard(session, dashboard_id):
    """Holt Dashboard-Daten"""
    response = requests.get(
        f"{METABASE_URL}/api/dashboard/{dashboard_id}",
        headers={"X-Metabase-Session": session}
    )
    if response.status_code == 200:
        return response.json()
    return None

def add_card_to_dashboard(session, dashboard_id, card_id, row=0, col=0, size_x=6, size_y=4):
    """Fügt eine Card zu einem Dashboard hinzu"""
    # Hole aktuelle Dashboard-Daten
    dashboard = get_dashboard(session, dashboard_id)
    if not dashboard:
        print(f"  ❌ Dashboard {dashboard_id} nicht gefunden")
        return False
    
    # Prüfe ob Card bereits vorhanden
    existing_cards = dashboard.get("ordered_cards", [])
    for card in existing_cards:
        if card.get("card_id") == card_id:
            print(f"  ⚠️  Query {card_id} bereits im Dashboard")
            return True
    
    # Erstelle neue Card
    card_data = {
        "cardId": card_id,
        "row": row,
        "col": col,
        "sizeX": size_x,
        "sizeY": size_y,
        "parameter_mappings": [],
        "visualization_settings": {}
    }
    
    # Metabase API: POST /api/dashboard/{id}/cards
    response = requests.post(
        f"{METABASE_URL}/api/dashboard/{dashboard_id}/cards",
        headers={
            "X-Metabase-Session": session,
            "Content-Type": "application/json"
        },
        json=card_data
    )
    
    if response.status_code in [200, 201]:
        print(f"  ✅ Query {card_id} hinzugefügt (Position: row={row}, col={col})")
        return True
    else:
        print(f"  ❌ Fehler bei Query {card_id}: {response.status_code}")
        try:
            error = response.json()
            print(f"     Details: {error}")
        except:
            print(f"     Response: {response.text[:200]}")
        return False

def main():
    print("=== Füge Queries zu Dashboards hinzu ===\n")
    
    session = get_session()
    if not session:
        return
    
    # TEK Dashboard
    print("1. TEK Dashboard (ID: 3):")
    tek_dashboard = DASHBOARDS["TEK"]
    for i, query_id in enumerate(tek_dashboard["queries"]):
        row = (i // 2) * 4  # 2 Spalten, 4 Zeilen pro Card
        col = (i % 2) * 6   # 6 Spalten pro Card
        add_card_to_dashboard(session, tek_dashboard["id"], query_id, row, col, 6, 4)
    
    print("\n2. BWA Dashboard (ID: 8):")
    bwa_dashboard = DASHBOARDS["BWA"]
    for i, query_id in enumerate(bwa_dashboard["queries"]):
        row = (i // 2) * 4  # 2 Spalten, 4 Zeilen pro Card
        col = (i % 2) * 6   # 6 Spalten pro Card
        add_card_to_dashboard(session, bwa_dashboard["id"], query_id, row, col, 6, 4)
    
    print("\n" + "="*60)
    print("✅ Fertig!")
    print("="*60)
    print(f"\nTEK Dashboard: {METABASE_URL}/dashboard/3")
    print(f"BWA Dashboard: {METABASE_URL}/dashboard/8")
    print("\nBitte Dashboard im Browser aktualisieren (F5)")

if __name__ == "__main__":
    main()
