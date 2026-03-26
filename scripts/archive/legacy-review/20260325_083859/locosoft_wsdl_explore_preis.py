#!/usr/bin/env python3
"""
Locosoft-Server erneut erkunden: Roh-WSDL holen und nach Hinweisen auf
Verkaufspreis / Händlerfahrzeug in SOAP durchsuchen.

Läuft auf dem Server (Zugriff auf 10.80.80.7):
  cd /opt/greiner-portal && .venv/bin/python scripts/locosoft_wsdl_explore_preis.py
"""
import os
import re
import sys

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

HOST = os.getenv("LOCOSOFT_SOAP_HOST", "10.80.80.7")
PORT = os.getenv("LOCOSOFT_SOAP_PORT", "8086")
USER = os.getenv("LOCOSOFT_SOAP_USER", "9001")
PASS = os.getenv("LOCOSOFT_SOAP_PASSWORD", "Max2024")
WSDL_URL = f"http://{HOST}:{PORT}/?wsdl"

# Suchbegriffe (case-insensitive)
KEYWORDS = [
    "price", "preis", "sale", "verkauf", "dealer", "haendler",
    "out_sale", "outSale", "sellingPrice", "listPrice", "list_price",
    "invoice_value", "estimated_invoice", "retail", "netto", "brutto",
]

def main():
    print("=" * 70)
    print("Locosoft WSDL – Erkundung auf Verkaufspreis / Händlerfahrzeug")
    print("=" * 70)
    print(f"URL: {WSDL_URL}\n")

    try:
        r = requests.get(WSDL_URL, auth=(USER, PASS), timeout=15)
        r.raise_for_status()
        xml = r.text
    except Exception as e:
        print(f"Fehler beim Laden der WSDL: {e}")
        return 1

    # 1) Alle definierten Operationen (alle Services/Ports)
    print("[1] Alle operation-Namen (alle Ports):")
    ops = re.findall(r'operation\s+name=["\']([^"\']+)["\']', xml)
    uniq_ops = sorted(set(ops))
    for name in uniq_ops:
        print(f"    {name}")
    print(f"    -> {len(uniq_ops)} Operationen gesamt.")
    print()

    # 2) Alle complexType / element-Namen
    print("[2] Alle complexType/element-Namen (Schema):")
    types = re.findall(r'<(?:complexType|element)\s+name="([^"]+)"', xml, re.I)
    for name in sorted(set(types)):
        print(f"    {name}")
    print()

    # 3) Treffer für unsere Suchbegriffe (mit Zeilenkontext)
    print("[3] Treffer im WSDL für: " + ", ".join(KEYWORDS))
    lines = xml.splitlines()
    for i, line in enumerate(lines):
        low = line.lower()
        for kw in KEYWORDS:
            if kw.lower() in low:
                # Eine Zeile Kontext
                ctx = line.strip()
                if len(ctx) > 120:
                    ctx = ctx[:117] + "..."
                print(f"    Zeile {i+1} ({kw}): {ctx}")
                break
    print()

    # 4) Prüfen ob es weitere WSDL-Pfade gibt (andere Services)
    print("[4] Weitere WSDL-Pfade testen (optional):")
    for path in ["/", "/soap", "/Dataquery", "/dataquery", "/ws", "/api"]:
        url = f"http://{HOST}:{PORT}{path}"
        if path == "/":
            test_url = url + "?wsdl"
        else:
            test_url = url + "?wsdl"
        try:
            r2 = requests.get(test_url, auth=(USER, PASS), timeout=5)
            if r2.status_code == 200 and "wsdl" in (r2.headers.get("Content-Type") or "").lower() or "definition" in r2.text[:500]:
                print(f"    {test_url} -> 200 (WSDL-ähnlich)")
            elif r2.status_code == 200:
                print(f"    {test_url} -> 200 (Content-Type: {r2.headers.get('Content-Type', '?')})")
            else:
                print(f"    {test_url} -> {r2.status_code}")
        except Exception as e:
            print(f"    {test_url} -> Fehler: {e}")
    print()

    # 5) message/part-Elemente (welche Typen werden pro Operation verwendet?)
    print("[5] Operation -> Input-Typ (aus message/part):")
    # Typische WSDL-Struktur: operation -> input -> message -> part element/type
    op_inputs = re.findall(r'<operation\s+name="([^"]+)".*?<input[^>]*>.*?<message[^>]*>.*?<part[^>]+(?:element|type)="[^"]*:?([^"]+)"', xml, re.S | re.I)
    for op, typ in op_inputs:
        print(f"    {op} -> {typ}")
    # Alternativ: part element=
    parts = re.findall(r'<part\s+(?:element|type)="[^"]*:?([^"]+)"', xml)
    for p in sorted(set(parts)):
        if "Message" not in p and "Fault" not in p:
            print(f"    (part type) {p}")
    print()

    print("=" * 70)
    print("Fazit: Wenn unter [3] keine Treffer für Verkaufspreis-Felder sind,")
    print("enthält die WSDL keine SOAP-Definition dafür.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
