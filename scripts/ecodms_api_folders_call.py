#!/usr/bin/env python3
"""
Direkter API-Call gegen ecoDMS GET /api/folders.
ecoDMS läuft auf 10.80.80.3:8180; /v3/api-docs gibt 404, /api/folders funktioniert.

Verwendung:
  cd /opt/greiner-portal && python3 scripts/ecodms_api_folders_call.py
  # Credentials aus config/.env (ECODMS_USER, ECODMS_PASSWORD)
"""

import os
import requests

# Optional: .env laden
_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", ".env")
if os.path.isfile(_env):
    try:
        from dotenv import load_dotenv
        load_dotenv(_env)
    except ImportError:
        pass

BASE_URL = os.environ.get("ECODMS_BASE_URL", "http://10.80.80.3:8180").rstrip("/")
USER = (os.environ.get("ECODMS_USER") or "").strip()
PASSWORD = (os.environ.get("ECODMS_PASSWORD") or "").strip()
AUTH = (USER, PASSWORD) if (USER and PASSWORD) else None

url = f"{BASE_URL}/api/folders"
r = requests.get(url, auth=AUTH, timeout=10, headers={"accept": "application/json"})
print("GET", url)
print("Status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    print("Anzahl Ordner:", len(data) if isinstance(data, list) else "?")
    for item in (data if isinstance(data, list) else [])[:20]:
        oid = item.get("oId") or item.get("id")
        name = item.get("foldername") or item.get("name")
        print("  ", oid, name)
else:
    print("Body:", r.text[:500])
