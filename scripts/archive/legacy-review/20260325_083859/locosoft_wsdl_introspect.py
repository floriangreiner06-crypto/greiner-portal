#!/usr/bin/env python3
"""
Locosoft WSDL-Introspektion: Alle SOAP-Operationen und relevante Typen ausgeben.

Ziel: Herausfinden, ob es eine Operation zum Schreiben von Verkaufspreisen
(Händlerfahrzeug / dealer_vehicles) gibt.

Ausführung auf dem Server (Zugriff auf 10.80.80.7):
  cd /opt/greiner-portal && .venv/bin/python scripts/locosoft_wsdl_introspect.py

Ausgabe: Alle Operationen; bei write* und Typen mit price/dealer/sale/potential
die genaue Signatur.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    try:
        from zeep import Client, Settings
        from zeep.transports import Transport
        from requests import Session
    except ImportError:
        print("Bitte zeep und requests installieren: pip install zeep requests")
        return 1

    host = os.getenv('LOCOSOFT_SOAP_HOST', '10.80.80.7')
    port = os.getenv('LOCOSOFT_SOAP_PORT', '8086')
    user = os.getenv('LOCOSOFT_SOAP_USER', '9001')
    password = os.getenv('LOCOSOFT_SOAP_PASSWORD', 'Max2024')
    url = f"http://{host}:{port}/"
    wsdl_url = f"{url}?wsdl"

    session = Session()
    session.auth = (user, password)
    session.headers.update({
        'locosoftinterface': os.getenv('LOCOSOFT_INTERFACE_KEY', 'GENE-AUTO'),
        'locosoftinterfaceversion': os.getenv('LOCOSOFT_INTERFACE_VERSION', '2.2'),
    })
    transport = Transport(session=session, timeout=30)
    client = Client(wsdl_url, transport=transport, settings=Settings(strict=False, xml_huge_tree=True))

    print("=" * 70)
    print("LOCOSOFT SOAP – Alle Operationen (WSDL)")
    print("=" * 70)
    print(f"WSDL: {wsdl_url}\n")

    # Alle Services/Ports durchgehen und Operationen sammeln
    for service in client.wsdl.services.values():
        for port in service.ports.values():
            print(f"Service: {service.name}, Port: {port.name}")
            for op_name, op in port.binding._operations.items():
                print(f"\n  Operation: {op_name}")
                try:
                    signature = op.input.signature()
                    print(f"    Signatur: {signature}")
                except Exception as e:
                    print(f"    (Signatur nicht lesbar: {e})")
                # Bei write* oder Namen mit vehicle/potential/price/dealer/sale Details ausgeben
                low = op_name.lower()
                if 'write' in low or 'vehicle' in low or 'potential' in low or 'price' in low or 'dealer' in low or 'sale' in low:
                    try:
                        if op.body and op.body.type:
                            print(f"    Body-Typ: {op.body.type.name}")
                            if hasattr(op.body.type, 'elements') and op.body.type.elements:
                                for el in op.body.type.elements:
                                    typ = getattr(el[1], 'type', None)
                                    print(f"      - {el[0]}: {getattr(typ, 'name', typ)}")
                    except Exception as e:
                        print(f"    (Typ-Details: {e})")

    print("\n" + "=" * 70)
    print("Typen (complex types) mit price / sale / dealer / vehicle im Namen:")
    print("=" * 70)
    for name, type_obj in (getattr(client.wsdl.types, 'types', []) or []):
        if not name:
            continue
        n = str(name).lower()
        if 'price' in n or 'sale' in n or 'dealer' in n or 'vehicle' in n or 'potential' in n:
            print(f"\n  {name}")
            try:
                if hasattr(type_obj, 'elements'):
                    for el in type_obj.elements:
                        print(f"    - {el[0]}: {getattr(getattr(el[1], 'type', None), 'name', el[1])}")
            except Exception as e:
                print(f"    (Fehler: {e})")

    # Zeep speichert Typen oft unter client.wsdl.types; alternative Suche
    try:
        from zeep.xsd.types import ComplexType
        for schema in (client.wsdl.types._schemas or []):
            for _type in schema._element_form_default or []:
                if hasattr(_type, 'name') and _type.name:
                    n = str(_type.name).lower()
                    if 'price' in n or 'sale' in n or 'dealer' in n or 'vehicle' in n or 'potential' in n:
                        print(f"\n  Typ (schema): {_type.name}")
    except Exception as e:
        print(f"\n(Schema-Iteration: {e})")

    print("\n" + "=" * 70)
    print("Hinweis: writeVehicleDetails nutzt Typ DMSServiceVehicle (nur Stammdaten, keine Preise).")
    print("Falls eine andere Operation für Händlerfahrzeug-Preise existiert, steht sie oben.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
