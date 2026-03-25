#!/usr/bin/env python3
"""
Gudat DA API: Resources (Ressourcen/Mechaniker) für ein Center abrufen.

Liest config/credentials.json, holt OAuth-Token für das angegebene Center,
ruft GET /resources auf und gibt die Liste lesbar aus (Tabelle + optional JSON).

Aufruf (aus /opt/greiner-portal):
  python3 scripts/gudat_fetch_resources.py deggendorf
  python3 scripts/gudat_fetch_resources.py landau
  python3 scripts/gudat_fetch_resources.py deggendorf --json
"""
import json
import os
import sys

try:
    import requests
except ImportError:
    print("Fehler: requests nicht installiert. Bitte: pip install requests")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, "config", "credentials.json")


def load_gudat_config():
    """Lädt Gudat-Config aus credentials.json."""
    if not os.path.isfile(CREDENTIALS_PATH):
        print(f"Fehler: Datei nicht gefunden: {CREDENTIALS_PATH}")
        return None
    with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    gudat = data.get("external_systems", {}).get("gudat", {})
    if not gudat:
        print("Fehler: external_systems.gudat nicht gefunden")
        return None
    centers = gudat.get("centers") or {}
    base_url = (gudat.get("api_base_url") or "").rstrip("/")
    group = gudat.get("group") or "greiner"
    if not base_url or not centers:
        print("Fehler: api_base_url oder centers fehlt")
        return None
    return {"base_url": base_url, "group": group, "centers": centers}


def get_token(base_url, group, center, client_id, client_secret, username, password):
    """OAuth Token für Center holen."""
    url = f"{base_url}/oauth/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "group": group,
        "center": center,
    }
    data = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    r = requests.post(url, headers=headers, data=data, timeout=15)
    if r.status_code != 200:
        return None, f"Token fehlgeschlagen: {r.status_code} {r.text[:300]}"
    body = r.json()
    token = body.get("access_token") or body.get("token")
    return token, None


def fetch_resources(base_url, group, center, token):
    """GET /resources mit Bearer Token."""
    url = f"{base_url}/resources"
    headers = {
        "Accept": "application/json",
        "group": group,
        "center": center,
        "Authorization": f"Bearer {token}",
    }
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code != 200:
        return None, f"Resources fehlgeschlagen: {r.status_code} {r.text[:500]}"
    return r.json(), None


def main():
    os.chdir(PROJECT_ROOT)
    center = (sys.argv[1] or "deggendorf").lower().strip()
    want_json = "--json" in sys.argv

    cfg = load_gudat_config()
    if not cfg:
        sys.exit(1)

    if center not in cfg["centers"]:
        print(f"Fehler: Center '{center}' nicht in gudat.centers. Verfügbar: {list(cfg['centers'].keys())}")
        sys.exit(1)

    c = cfg["centers"][center]
    client_id = (c.get("client_id") or "").strip()
    client_secret = (c.get("client_secret") or "").strip()
    username = (c.get("username") or "").strip()
    password = (c.get("password") or "").strip()
    if not all([client_id, client_secret, username, password]) or "PLACEHOLDER" in client_id + client_secret:
        print(f"Fehler: Credentials für Center '{center}' unvollständig oder Platzhalter.")
        sys.exit(1)

    base_url = cfg["base_url"]
    group = cfg["group"]

    print(f"Center: {center} (group={group})")
    print("Hole OAuth-Token …")
    token, err = get_token(base_url, group, center, client_id, client_secret, username, password)
    if err:
        print(err)
        sys.exit(1)
    print("Token OK. Rufe GET /resources auf …")

    data, err = fetch_resources(base_url, group, center, token)
    if err:
        print(err)
        sys.exit(1)

    # Paginierte Antwort: data.data = Liste der Ressourcen
    items = data.get("data") if isinstance(data.get("data"), list) else []
    if not items and isinstance(data, list):
        items = data

    if want_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    print()
    print(f"--- Ressourcen für Center '{center}' ({len(items)} Einträge) ---")
    print()
    # Tabelle: id, name, staff_id, order, is_visible_in_calendar
    col_id = 5
    col_name = 35
    col_staff = 18
    col_order = 6
    col_visible = 10
    header = f"{'ID':<{col_id}} {'Name':<{col_name}} {'staff_id':<{col_staff}} {'order':<{col_order}} {'sichtbar':<{col_visible}}"
    print(header)
    print("-" * (col_id + col_name + col_staff + col_order + col_visible + 4))
    for r in items:
        rid = r.get("id", "")
        name = (r.get("name") or "-")[: col_name - 1]
        staff_id = (r.get("staff_id") or "-")[: col_staff - 1]
        order = r.get("order", "")
        vis = "ja" if r.get("is_visible_in_calendar") else "nein"
        print(f"{rid!s:<{col_id}} {name:<{col_name}} {staff_id:<{col_staff}} {order!s:<{col_order}} {vis:<{col_visible}}")
    print()
    print("Ende.")


if __name__ == "__main__":
    main()
