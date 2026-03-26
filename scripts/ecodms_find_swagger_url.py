#!/usr/bin/env python3
"""
ecoDMS – Swagger/OpenAPI-URL finden
===================================
Probiert alle üblichen Pfade auf dem ecoDMS-Server und gibt die erste
funktionierende Spec-URL aus. Diese könnt ihr in config/.env eintragen:
  ECODMS_OPENAPI_SPEC_URL=<ausgegebene URL oder Pfad>

Ausführung (vom Projektroot, damit config/.env geladen wird):
  cd /opt/greiner-portal && python3 scripts/ecodms_find_swagger_url.py
"""

import os
import sys
import requests

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_env_file = os.path.join(_project_root, "config", ".env")
if os.path.isfile(_env_file):
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass

BASE_URL = (os.environ.get("ECODMS_BASE_URL") or "http://10.80.80.3:8180").rstrip("/")
USER = (os.environ.get("ECODMS_USER") or "").strip()
PW = (os.environ.get("ECODMS_PASSWORD") or "").strip()
AUTH = (USER, PW) if (USER and PW) else None

PATHS = (
    "/v3/api-docs",
    "/v2/api-docs",
    "/api-docs",
    "/api/v3/api-docs",
    "/api/v2/api-docs",
    "/swagger-ui/v3/api-docs",
    "/swagger/v3/api-docs",
    "/swagger-resources",
)

def main():
    print("ecoDMS Swagger-URL suchen")
    print("Base URL:", BASE_URL)
    print("Auth:", "ja" if AUTH else "nein (evtl. 401)")
    print()
    for path in PATHS:
        url = BASE_URL + path
        try:
            r = requests.get(url, auth=AUTH, timeout=8, headers={"accept": "application/json"})
            if r.status_code != 200:
                print("  ", path, "->", r.status_code)
                continue
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else None
            if path == "/swagger-resources" and isinstance(data, list):
                for res in data:
                    loc = (res or {}).get("location") or (res or {}).get("url")
                    if loc:
                        full = loc if loc.startswith("http") else BASE_URL + ("/" if not loc.startswith("/") else "") + loc.lstrip("/")
                        r2 = requests.get(full, auth=AUTH, timeout=8, headers={"accept": "application/json"})
                        if r2.status_code == 200:
                            try:
                                spec = r2.json()
                                if isinstance(spec, dict) and (spec.get("paths") or spec.get("openapi") or spec.get("swagger")):
                                    print("  OK (via swagger-resources):", full)
                                    print()
                                    print("In config/.env eintragen:")
                                    if full.startswith(BASE_URL):
                                        print("  ECODMS_OPENAPI_SPEC_URL=" + full[len(BASE_URL):].lstrip("/") or "/")
                                    else:
                                        print("  ECODMS_OPENAPI_SPEC_URL=" + full)
                                    return 0
                            except Exception:
                                pass
                print("  ", path, "-> 200 (keine gültige Spec in locations)")
            elif isinstance(data, dict) and (data.get("paths") or data.get("openapi") or data.get("swagger")):
                print("  OK:", path)
                print()
                print("In config/.env eintragen:")
                print("  ECODMS_OPENAPI_SPEC_URL=" + path)
                return 0
            else:
                print("  ", path, "-> 200 (kein OpenAPI-JSON)")
        except Exception as e:
            print("  ", path, "-> Fehler:", e)
    print()
    print("Keine Swagger-Spec gefunden. ecoDMS liefert die API-Beschreibung an keiner der üblichen Pfade.")
    print("Das Portal nutzt dann die bekannten Endpunkte direkt (z.B. /api/folders).")
    print("Falls Swagger bei euch unter anderem Pfad läuft: URL in ECODMS_OPENAPI_SPEC_URL eintragen.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
