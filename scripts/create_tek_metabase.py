#!/usr/bin/env python3
"""
Erstellt TEK-Queries und Dashboard in Metabase
Basierend auf DRIVE Portal Struktur
"""

import requests
import json
import sys

METABASE_URL = "http://localhost:3001"
DB_ID = 2  # DRIVE Portal Database

# Login
def get_session():
    response = requests.post(
        f"{METABASE_URL}/api/session",
        json={"username": "admin@auto-greiner.de", "password": "Drive2026!"}
    )
    if response.status_code != 200:
        print(f"Login fehlgeschlagen: {response.status_code}")
        sys.exit(1)
    return response.json()["id"]

# Query erstellen
def create_query(session_token, name, description, sql, visualization_type="table"):
    response = requests.post(
        f"{METABASE_URL}/api/card",
        headers={"X-Metabase-Session": session_token},
        json={
            "name": name,
            "description": description,
            "dataset_query": {
                "database": DB_ID,
                "type": "native",
                "native": {
                    "query": sql
                }
            },
            "display": visualization_type,
            "visualization_settings": {}
        }
    )
    if response.status_code != 200:
        print(f"Fehler beim Erstellen von '{name}': {response.status_code}")
        print(response.text)
        return None
    return response.json()["id"]

# Dashboard erstellen
def create_dashboard(session_token, name, description):
    response = requests.post(
        f"{METABASE_URL}/api/dashboard",
        headers={"X-Metabase-Session": session_token},
        json={
            "name": name,
            "description": description
        }
    )
    if response.status_code != 200:
        print(f"Fehler beim Erstellen des Dashboards: {response.status_code}")
        print(response.text)
        return None
    return response.json()["id"]

# Query zum Dashboard hinzufügen
def add_card_to_dashboard(session_token, dashboard_id, card_id, row=0, col=0, size_x=6, size_y=4):
    response = requests.post(
        f"{METABASE_URL}/api/dashboard/{dashboard_id}/cards",
        headers={"X-Metabase-Session": session_token},
        json={
            "cardId": card_id,
            "row": row,
            "col": col,
            "sizeX": size_x,
            "sizeY": size_y
        }
    )
    return response.status_code == 200

def main():
    print("=== TEK Dashboard in Metabase erstellen ===\n")
    
    # Login
    print("1. Login...")
    session = get_session()
    print("   ✅ Login erfolgreich\n")
    
    # Queries definieren
    queries = [
        {
            "name": "TEK Gesamt - Monat kumuliert",
            "description": "TEK-Daten nach Bereichen, Monat kumuliert",
            "sql": """
SELECT 
    b.name as "Bereich",
    COALESCE(SUM(cd.erloes), 0) as "Erlös (€)",
    COALESCE(SUM(cd.einsatz), 0) as "Einsatz (€)",
    COALESCE(SUM(cd.db1), 0) as "DB1 (€)",
    CASE 
        WHEN SUM(cd.erloes) > 0 
        THEN ROUND(SUM(cd.db1) / SUM(cd.erloes) * 100, 2)
        ELSE 0 
    END as "DB1 (%)",
    COALESCE(SUM(cd.stueck), 0) as "Menge (Stück)"
FROM (
    SELECT 
        bereich_id,
        standort_id,
        jahr,
        monat,
        SUM(erloes) as erloes,
        SUM(einsatz) as einsatz,
        SUM(db1) as db1,
        SUM(stueck) as stueck
    FROM controlling_data
    WHERE jahr = EXTRACT(YEAR FROM CURRENT_DATE)
      AND monat <= EXTRACT(MONTH FROM CURRENT_DATE)
    GROUP BY bereich_id, standort_id, jahr, monat
) cd
JOIN bereiche b ON cd.bereich_id = b.id
GROUP BY b.name, b.sort_order
ORDER BY b.sort_order;
            """,
            "type": "table"
        },
        {
            "name": "TEK nach Standort",
            "description": "TEK-Daten nach Standort und Bereich (aktueller Monat)",
            "sql": """
SELECT 
    s.name as "Standort",
    b.name as "Bereich",
    COALESCE(SUM(cd.erloes), 0) as "Erlös (€)",
    COALESCE(SUM(cd.einsatz), 0) as "Einsatz (€)",
    COALESCE(SUM(cd.db1), 0) as "DB1 (€)",
    CASE 
        WHEN SUM(cd.erloes) > 0 
        THEN ROUND(SUM(cd.db1) / SUM(cd.erloes) * 100, 2)
        ELSE 0 
    END as "DB1 (%)",
    COALESCE(SUM(cd.stueck), 0) as "Menge (Stück)"
FROM (
    SELECT 
        bereich_id,
        standort_id,
        jahr,
        monat,
        SUM(erloes) as erloes,
        SUM(einsatz) as einsatz,
        SUM(db1) as db1,
        SUM(stueck) as stueck
    FROM controlling_data
    WHERE jahr = EXTRACT(YEAR FROM CURRENT_DATE)
      AND monat = EXTRACT(MONTH FROM CURRENT_DATE)
    GROUP BY bereich_id, standort_id, jahr, monat
) cd
JOIN standorte s ON cd.standort_id = s.id
JOIN bereiche b ON cd.bereich_id = b.id
GROUP BY s.name, b.name, s.sort_order, b.sort_order
ORDER BY s.sort_order, b.sort_order;
            """,
            "type": "table"
        },
        {
            "name": "TEK Verlauf",
            "description": "TEK-Verlauf der letzten 12 Monate",
            "sql": """
SELECT 
    TO_CHAR(TO_DATE(jahr || '-' || LPAD(monat::text, 2, '0') || '-01'), 'YYYY-MM') as "Monat",
    COALESCE(SUM(erloes), 0) as "Erlös (€)",
    COALESCE(SUM(einsatz), 0) as "Einsatz (€)",
    COALESCE(SUM(db1), 0) as "DB1 (€)",
    CASE 
        WHEN SUM(erloes) > 0 
        THEN ROUND(SUM(db1) / SUM(erloes) * 100, 2)
        ELSE 0 
    END as "DB1 (%)"
FROM controlling_data
WHERE jahr >= EXTRACT(YEAR FROM CURRENT_DATE) - 1
  AND (jahr < EXTRACT(YEAR FROM CURRENT_DATE) 
       OR (jahr = EXTRACT(YEAR FROM CURRENT_DATE) 
           AND monat <= EXTRACT(MONTH FROM CURRENT_DATE)))
GROUP BY jahr, monat
ORDER BY jahr, monat;
            """,
            "type": "line"
        },
        {
            "name": "TEK Drill-Down NW/GW",
            "description": "TEK Drill-Down: Neuwagen und Gebrauchtwagen nach Absatzweg",
            "sql": """
SELECT 
    b.name as "Bereich",
    COALESCE(aw.name, 'Ohne Absatzweg') as "Absatzweg",
    COALESCE(SUM(cd.erloes), 0) as "Erlös (€)",
    COALESCE(SUM(cd.einsatz), 0) as "Einsatz (€)",
    COALESCE(SUM(cd.db1), 0) as "DB1 (€)",
    COALESCE(SUM(cd.stueck), 0) as "Menge (Stück)",
    CASE 
        WHEN SUM(cd.stueck) > 0 
        THEN ROUND(SUM(cd.db1) / SUM(cd.stueck), 2)
        ELSE 0 
    END as "DB/Stück (€)"
FROM (
    SELECT 
        bereich_id,
        absatzweg_id,
        jahr,
        monat,
        SUM(erloes) as erloes,
        SUM(einsatz) as einsatz,
        SUM(db1) as db1,
        SUM(stueck) as stueck
    FROM controlling_data
    WHERE jahr = EXTRACT(YEAR FROM CURRENT_DATE)
      AND monat = EXTRACT(MONTH FROM CURRENT_DATE)
      AND bereich_id IN (1, 2)  -- Nur NW und GW
    GROUP BY bereich_id, absatzweg_id, jahr, monat
) cd
JOIN bereiche b ON cd.bereich_id = b.id
LEFT JOIN absatzwege aw ON cd.absatzweg_id = aw.id
GROUP BY b.name, aw.name, b.sort_order, aw.sort_order
ORDER BY b.sort_order, aw.sort_order;
            """,
            "type": "table"
        }
    ]
    
    # Queries erstellen
    print("2. Erstelle Queries...")
    card_ids = []
    for i, query in enumerate(queries, 1):
        print(f"   {i}. {query['name']}...")
        card_id = create_query(session, query['name'], query['description'], query['sql'], query['type'])
        if card_id:
            card_ids.append(card_id)
            print(f"      ✅ Erstellt (ID: {card_id})")
        else:
            print(f"      ❌ Fehler")
    print()
    
    # Dashboard erstellen
    print("3. Erstelle Dashboard...")
    dashboard_id = create_dashboard(
        session,
        "TEK Dashboard",
        "Tägliche Erfolgskontrolle - Übersicht nach DRIVE Portal Struktur"
    )
    if not dashboard_id:
        print("   ❌ Dashboard konnte nicht erstellt werden")
        sys.exit(1)
    print(f"   ✅ Dashboard erstellt (ID: {dashboard_id})\n")
    
    # Queries zum Dashboard hinzufügen
    print("4. Füge Queries zum Dashboard hinzu...")
    positions = [
        (0, 0, 12, 4),   # TEK Gesamt - volle Breite
        (4, 0, 12, 4),   # TEK nach Standort - volle Breite
        (8, 0, 12, 4),   # TEK Verlauf - volle Breite
        (12, 0, 12, 4),  # TEK Drill-Down - volle Breite
    ]
    
    for i, (card_id, pos) in enumerate(zip(card_ids, positions), 1):
        row, col, size_x, size_y = pos
        if add_card_to_dashboard(session, dashboard_id, card_id, row, col, size_x, size_y):
            print(f"   {i}. Query {i} hinzugefügt")
        else:
            print(f"   {i}. ❌ Fehler beim Hinzufügen")
    print()
    
    print("=== Fertig! ===")
    print(f"Dashboard URL: {METABASE_URL}/dashboard/{dashboard_id}")

if __name__ == "__main__":
    main()
