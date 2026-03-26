#!/usr/bin/env python3
"""
Prüft die eAutoSeller Swagger-Credentials (X-API-Key, X-CLIENT-KEY).
Liest aus config/credentials.json → eautoseller.api_key, eautoseller.client_secret.
Optional: EAUTOSELLER_API_KEY und EAUTOSELLER_CLIENT_SECRET aus der Umgebung.
"""
import json
import os
import sys
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS_PATH = PROJECT_ROOT / "config" / "credentials.json"


def load_credentials():
    """Lädt eautoseller-Block aus credentials.json. Keine Werte ausgeben.
    Returns: (api_key, client_secret, source) mit source in ('file', 'env', 'mixed').
    """
    if not CREDENTIALS_PATH.exists():
        print(f"Datei nicht gefunden: {CREDENTIALS_PATH}")
        return None, None, None
    try:
        with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Fehler beim Lesen von credentials.json: {e}")
        return None, None, None
    block = data.get("eautoseller") or {}
    from_file_key = (block.get("api_key") or "").strip()
    from_file_secret = (block.get("client_secret") or "").strip()
    from_env_key = (os.getenv("EAUTOSELLER_API_KEY") or "").strip()
    from_env_secret = (os.getenv("EAUTOSELLER_CLIENT_SECRET") or "").strip()
    api_key = from_file_key or from_env_key
    client_secret = from_file_secret or from_env_secret
    if api_key and client_secret:
        if from_file_key and from_file_secret:
            source = "file"
        elif from_env_key and from_env_secret:
            source = "env"
        else:
            source = "mixed"
    else:
        source = None
    return api_key, client_secret, source


def test_api(api_key: str, client_secret: str, vin: str = "KMHKR81EFPU172712") -> bool:
    """Testet einen GET /dms/vehicles mit den übergebenen Keys."""
    url = "https://api.eautoseller.de/dms/vehicles"
    headers = {
        "X-API-Key": api_key,
        "X-CLIENT-KEY": client_secret,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "system-id": "DRIVE-Portal",
    }
    try:
        r = requests.get(url, params={"vin": vin}, headers=headers, timeout=15)
    except Exception as e:
        print(f"Netzwerkfehler: {e}")
        return False
    if r.status_code == 200:
        try:
            data = r.json()
            count = len(data) if isinstance(data, list) else len(data.get("data", []))
            print(f"OK: API antwortet 200, Fahrzeuge für VIN: {count}")
            return True
        except Exception:
            print("OK: API antwortet 200 (Response kein JSON)")
            return True
    print(f"Fehler: API antwortet {r.status_code}")
    try:
        body = r.text[:500] if r.text else "(leer)"
        print(f"Antwort: {body}")
    except Exception:
        pass
    return False


def main():
    print("eAutoSeller Credentials prüfen")
    print("=" * 50)
    api_key, client_secret, source = load_credentials()

    if not api_key or not client_secret:
        print("\nKeine gültigen Keys gefunden.")
        print("\nSo tragen Sie die Keys ein:")
        print(f"  Datei: {CREDENTIALS_PATH}")
        print('  Block "eautoseller" mit api_key und client_secret (Swagger: X-API-Key, X-CLIENT-KEY):')
        print('  {')
        print('    "eautoseller": {')
        print('      "api_key":     "<Ihr X-API-Key>",')
        print('      "client_secret": "<Ihr X-CLIENT-KEY>",')
        print('      "api_base_url": "https://api.eautoseller.de"')
        print("    }")
        print("  }")
        print("\nAlternativ Umgebungsvariablen setzen:")
        print("  export EAUTOSELLER_API_KEY=...")
        print("  export EAUTOSELLER_CLIENT_SECRET=...")
        print("  python scripts/check_eautoseller_credentials.py")
        return 1

    print("Credentials geladen (api_key und client_secret sind gesetzt).")
    print("Quelle: " + ("Datei (credentials.json)" if source == "file" else "Umgebungsvariablen (EAUTOSELLER_*)" if source == "env" else "Datei + Umgebung gemischt"))
    vin = (sys.argv[1:] and sys.argv[1]) or "KMHKR81EFPU172712"
    print(f"Test-Request: GET /dms/vehicles?vin={vin}")
    ok = test_api(api_key, client_secret, vin)
    print("=" * 50)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
