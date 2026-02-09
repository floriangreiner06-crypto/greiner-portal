#!/usr/bin/env python3
"""
Fügt Queries zum TEK Dashboard hinzu
"""

import requests
import sys

METABASE_URL = "http://localhost:3001"
DASHBOARD_ID = 3
CARD_IDS = [42, 43, 44, 45]  # Die erstellten Query-IDs

def get_session():
    response = requests.post(
        f"{METABASE_URL}/api/session",
        json={"username": "admin@auto-greiner.de", "password": "Drive2026!"}
    )
    return response.json()["id"]

def add_cards():
    session = get_session()
    
    positions = [
        (0, 0, 12, 4),   # TEK Gesamt
        (4, 0, 12, 4),   # TEK nach Standort
        (8, 0, 12, 4),   # TEK Verlauf
        (12, 0, 12, 4),  # TEK Drill-Down
    ]
    
    for i, (card_id, pos) in enumerate(zip(CARD_IDS, positions), 1):
        row, col, size_x, size_y = pos
        response = requests.post(
            f"{METABASE_URL}/api/dashboard/{DASHBOARD_ID}/cards",
            headers={
                "X-Metabase-Session": session,
                "Content-Type": "application/json"
            },
            json={
                "cardId": card_id,
                "row": row,
                "col": col,
                "sizeX": size_x,
                "sizeY": size_y,
                "parameter_mappings": []
            }
        )
        if response.status_code in [200, 201]:
            print(f"✅ Query {i} (ID: {card_id}) hinzugefügt")
        else:
            print(f"❌ Fehler bei Query {i}: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    add_cards()
