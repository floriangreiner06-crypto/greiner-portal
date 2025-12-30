#!/usr/bin/env python3
"""
Carloop API Explorer
Erkundet die Carloop-Schnittstelle und sucht nach API-Endpunkten
"""
import requests
import re
import json

BASE_URL = "https://www.carloop-vermietsystem.de"
USERNAME = "admin100328"
PASSWORD = "Opel1234!"

def login():
    session = requests.Session()
    session.get(f"{BASE_URL}/de/Portal/Authentifizierung")
    r = session.post(
        f"{BASE_URL}/de/Portal/Authentifizierung",
        data={"username": USERNAME, "password": PASSWORD, "login": "Anmelden"},
        allow_redirects=True
    )
    if "Abmelden" in r.text:
        print("Login OK")
        return session
    else:
        print("Login fehlgeschlagen")
        return None

def explore_plantafel(session):
    """Plantafel erkunden - enthält Fahrzeuge und Reservierungen"""
    r = session.get(f"{BASE_URL}/de/Mobilitaets-Manager/Vermietung/Plantafel")

    # AJAX-URLs suchen
    urls = set()
    for match in re.finditer(r'["\'](/de/[^"\']+)["\']', r.text):
        url = match.group(1)
        if any(x in url.lower() for x in ['ajax', 'api', 'json', 'data', 'get', 'list']):
            urls.add(url)

    print("\nMögliche API-Endpunkte:")
    for url in sorted(urls):
        print(f"  {url}")

    return urls

def explore_fahrzeuge(session):
    """Fahrzeuge-Liste abrufen"""
    r = session.get(f"{BASE_URL}/de/Mobilitaets-Manager/Fahrzeuge/Uebersicht")

    # Tabellen-Daten extrahieren
    # Suche nach Fahrzeug-Zeilen
    rows = re.findall(r'<tr[^>]*class="[^"]*fahrzeug[^"]*"[^>]*>(.*?)</tr>', r.text, re.DOTALL | re.IGNORECASE)
    print(f"\nFahrzeug-Zeilen gefunden: {len(rows)}")

    # Alternativ: Nach Kennzeichen suchen
    kennzeichen = re.findall(r'([A-Z]{1,3}[-\s]?[A-Z]{1,2}[-\s]?\d{1,4})', r.text)
    print(f"Kennzeichen gefunden: {len(set(kennzeichen))}")
    for k in list(set(kennzeichen))[:10]:
        print(f"  {k}")

    return r.text

def explore_api_endpoints(session):
    """Verschiedene potenzielle API-Endpunkte testen"""
    endpoints = [
        "/de/Mobilitaets-Manager/Fahrzeuge/getList",
        "/de/Mobilitaets-Manager/Vermietung/getReservations",
        "/de/Mobilitaets-Manager/api/vehicles",
        "/api/v1/vehicles",
        "/de/Mobilitaets-Manager/Vermietung/Plantafel/getData",
    ]

    print("\nAPI-Endpunkte testen:")
    for ep in endpoints:
        try:
            r = session.get(f"{BASE_URL}{ep}")
            content_type = r.headers.get('Content-Type', '')
            print(f"  {ep}: {r.status_code} ({content_type[:30]})")
            if r.status_code == 200 and 'json' in content_type:
                print(f"    -> {r.text[:200]}")
        except Exception as e:
            print(f"  {ep}: Error - {e}")

def explore_reservierungen(session):
    """Aktuelle Reservierungen/Vermietungen abrufen"""
    r = session.get(f"{BASE_URL}/de/Mobilitaets-Manager/Vermietung/Uebersicht")
    print("\n=== Vermietungs-Übersicht ===")
    print(f"Status: {r.status_code}")

    # Tabellen-Inhalte extrahieren
    # Nach tbody suchen
    tbody = re.search(r'<tbody[^>]*>(.*?)</tbody>', r.text, re.DOTALL)
    if tbody:
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody.group(1), re.DOTALL)
        print(f"Zeilen gefunden: {len(rows)}")
        for row in rows[:5]:
            # Zellen extrahieren
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            clean_cells = [re.sub(r'<[^>]+>', '', c).strip()[:30] for c in cells]
            if clean_cells:
                print(f"  {' | '.join(clean_cells[:6])}")

def explore_vehicle_list(session):
    """Fahrzeugliste als HTML-Tabelle"""
    r = session.get(f"{BASE_URL}/de/Mobilitaets-Manager/Fahrzeuge/Uebersicht")
    print("\n=== Fahrzeug-Übersicht ===")

    # Tabelle finden
    table = re.search(r'<table[^>]*class="[^"]*table[^"]*"[^>]*>(.*?)</table>', r.text, re.DOTALL)
    if table:
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table.group(1), re.DOTALL)
        print(f"Zeilen: {len(rows)}")
        for row in rows[:8]:
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
            clean = [re.sub(r'<[^>]+>', '', c).strip()[:20] for c in cells]
            if clean and any(clean):
                print(f"  {' | '.join(clean[:8])}")

def main():
    session = login()
    if not session:
        return

    explore_vehicle_list(session)
    explore_reservierungen(session)
    explore_api_endpoints(session)

if __name__ == "__main__":
    main()
