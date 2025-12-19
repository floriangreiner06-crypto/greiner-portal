"""
Locosoft SOAP API Konfiguration
================================
Dokumentiert am: 2025-12-19 (TAG 128)

SOAP-Endpunkt für DMS-Integration (Werkstatt, Termine, Aufträge)
"""

# === SOAP ENDPUNKT ===
LOCOSOFT_SOAP_HOST = "10.80.80.7"
LOCOSOFT_SOAP_PORT = "8086"
LOCOSOFT_SOAP_URL = f"http://{LOCOSOFT_SOAP_HOST}:{LOCOSOFT_SOAP_PORT}/"
LOCOSOFT_WSDL_URL = f"{LOCOSOFT_SOAP_URL}?wsdl"

# === AUTHENTIFIZIERUNG ===
# HTTP Basic Auth
LOCOSOFT_SOAP_USER = "9001"
LOCOSOFT_SOAP_PASSWORD = "Max2024"

# === VERSION 2.2 HEADER ===
# Diese Header sind PFLICHT für writeAppointment und andere v2.2 Funktionen!
LOCOSOFT_INTERFACE_KEY = "GENE-AUTO"  # Lizenzschlüssel von Loco-Soft
LOCOSOFT_INTERFACE_VERSION = "2.2"

# HTTP-Headers für alle Requests
LOCOSOFT_SOAP_HEADERS = {
    "Content-Type": "text/xml; charset=utf-8",
    "locosoftinterface": LOCOSOFT_INTERFACE_KEY,
    "locosoftinterfaceversion": LOCOSOFT_INTERFACE_VERSION,
}


# === VERFÜGBARE OPERATIONEN ===

# Lesen (funktionieren ohne v2.2 Header)
READ_OPERATIONS = [
    "listWorkshops",           # Werkstätten (ID 1, 2, 3)
    "listWorkGroups",          # Arbeitsgruppen (MON, SB, VKB...)
    "listLaborRates",          # Stundensätze
    "listOpenWorkOrders",      # Offene Aufträge
    "listAvailableTimes",      # Kapazitäten pro Tag
    "listCustomers",           # Kundensuche
    "listVehicles",            # Fahrzeugsuche
    "listCustomerVehicles",    # Fahrzeuge eines Kunden
    "listSparePartTypes",      # Teilearten
    "listCustomerInvoices",    # Kundenrechnungen
    "readCustomer",            # Kundendaten
    "readVehicle",             # Fahrzeugdaten
    "readWorkOrderDetails",    # Auftragsdetails
    "readAppointment",         # Termindetails
]

# Schreiben (funktionieren ohne v2.2 Header)
WRITE_OPERATIONS_V1 = [
    "writeWorkOrderDetails",   # Auftrag erstellen/ändern
    "writeWorkOrderTimes",     # Arbeitszeiten buchen
    "writeWorkTimes",          # Stempelzeiten
    "writeCustomerDetails",    # Kundendaten ändern
    "writeVehicleDetails",     # Fahrzeugdaten ändern
    "writePotential",          # Verkaufspotential
]

# Schreiben (BRAUCHEN v2.2 Header!)
WRITE_OPERATIONS_V22 = [
    "writeAppointment",             # Termin anlegen/ändern
    "writeAppointmentNotification", # Terminbenachrichtigung
]


# === BEISPIEL-USAGE ===
"""
import requests
from config.locosoft_soap_config import *

# SOAP-Request mit Version 2.2
response = requests.post(
    LOCOSOFT_SOAP_URL,
    auth=(LOCOSOFT_SOAP_USER, LOCOSOFT_SOAP_PASSWORD),
    headers=LOCOSOFT_SOAP_HEADERS,
    data=soap_envelope_xml
)
"""


# === CURL BEISPIEL ===
"""
curl -X POST "http://10.80.80.7:8086/" \
  -u "9001:Max2024" \
  -H "Content-Type: text/xml" \
  -H "locosoftinterface: GENE-AUTO" \
  -H "locosoftinterfaceversion: 2.2" \
  -d '<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:soap="http://soap.loco_soft.de/">
  <soapenv:Body>
    <soap:writeAppointment>
      <appointment>
        <number>0</number>
        <text>Neuer Termin</text>
        <vehicle><number>59085</number></vehicle>
        <customer><number>1046889</number></customer>
        <bringDateTime>2025-12-20T09:00:00</bringDateTime>
        <returnDateTime>2025-12-20T16:00:00</returnDateTime>
        <type>loose</type>
      </appointment>
    </soap:writeAppointment>
  </soapenv:Body>
</soapenv:Envelope>'
"""
