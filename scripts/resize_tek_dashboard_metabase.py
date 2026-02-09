#!/usr/bin/env python3
"""
Passt die Card-Größen des TEK-Dashboards in Metabase an (breiter/höher, weniger Leerraum).
Dashboard-ID 9 = TEK Dashboard (laut URL 10.80.80.20:3001/dashboard/9-tek-dashboard).
"""

import requests
import json

METABASE_URL = "http://localhost:3001"
TEK_DASHBOARD_ID = 9  # Falls Ihr TEK-Dashboard eine andere ID hat, hier anpassen

# Volle Breite und hohe Cards, damit wenig Leerraum (wie DRIVE TEK).
# Metabase Grid: 18 = volle Breite; size_y = Zeilenhöhe (ca. 50px pro Zeile).
CARD_SIZES = [
    (18, 10),  # Card 1: TEK Gesamt – volle Breite, alle Spalten sichtbar
    (18, 24),  # Card 2: TEK nach Standort – volle Breite, hoch (viele Zeilen + KST-Summen)
    (18, 14),  # Card 3: TEK Verlauf – volle Breite, Chart groß und lesbar
]

def get_session():
    r = requests.post(
        f"{METABASE_URL}/api/session",
        json={"username": "admin@auto-greiner.de", "password": "Drive2026!"}
    )
    r.raise_for_status()
    return r.json()["id"]

def main():
    session = get_session()
    # Dashboard laden
    r = requests.get(
        f"{METABASE_URL}/api/dashboard/{TEK_DASHBOARD_ID}",
        headers={"X-Metabase-Session": session}
    )
    if r.status_code != 200:
        print(f"❌ Dashboard {TEK_DASHBOARD_ID} nicht gefunden: {r.status_code}")
        return
    dash = r.json()
    cards = dash.get("ordered_cards") or dash.get("dashcards") or []
    if not cards:
        print("⚠️  Keine Cards im Dashboard gefunden.")
        return
    # Größen anwenden (nach Reihenfolge; wenn mehr Cards als CARD_SIZES, letztes Größenpaar wiederverwenden)
    for i, dc in enumerate(cards):
        size_x, size_y = CARD_SIZES[min(i, len(CARD_SIZES) - 1)]
        # Metabase verwendet oft sizeX/sizeY (camelCase) in der API
        if "sizeX" in dc:
            dc["sizeX"] = size_x
        if "size_x" in dc:
            dc["size_x"] = size_x
        if "sizeY" in dc:
            dc["sizeY"] = size_y
        if "size_y" in dc:
            dc["size_y"] = size_y
        # Für PUT wird oft das komplette dashcards-Format erwartet
        dc["sizeX"] = size_x
        dc["sizeY"] = size_y
    # Payload für PUT: nur die Felder, die Metabase erwartet
    # Typischerweise: name, description, dashcards (mit id, card_id, row, col, sizeX, sizeY, ...)
    dashcards_payload = []
    row = 0
    for i, dc in enumerate(cards):
        size_x, size_y = CARD_SIZES[min(i, len(CARD_SIZES) - 1)]
        entry = {
            "id": dc.get("id"),
            "card_id": dc.get("card_id"),
            "row": dc.get("row", row),
            "col": dc.get("col", 0),
            "size_x": size_x,
            "size_y": size_y,
            "parameter_mappings": dc.get("parameter_mappings", []),
            "visualization_settings": dc.get("visualization_settings", {}),
        }
        if dc.get("id") is None:
            entry.pop("id", None)
        dashcards_payload.append(entry)
        row += size_y
    # PUT /api/dashboard/:id
    put_r = requests.put(
        f"{METABASE_URL}/api/dashboard/{TEK_DASHBOARD_ID}",
        headers={"X-Metabase-Session": session, "Content-Type": "application/json"},
        json={
            "name": dash.get("name", "TEK Dashboard"),
            "description": dash.get("description"),
            "dashcards": dashcards_payload,
            "parameters": dash.get("parameters", []),
        }
    )
    if put_r.status_code == 200:
        print("✅ TEK-Dashboard Card-Größen angepasst (breiter/höher).")
        print(f"   Dashboard: {METABASE_URL}/dashboard/{TEK_DASHBOARD_ID}")
    else:
        print(f"❌ Update fehlgeschlagen: {put_r.status_code}")
        print(put_r.text[:500])

if __name__ == "__main__":
    main()
