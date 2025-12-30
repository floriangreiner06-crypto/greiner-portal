#!/usr/bin/env python3
"""
Locosoft SOAP Client für DRIVE
==============================
Vollständiger Client für die Locosoft DMS SOAP-Schnittstelle.

Features:
- Alle READ-Operationen (list*, read*)
- Alle WRITE-Operationen (write*) mit v2.2 Header
- Connection Pooling & Retry-Logik
- Caching für häufige Abfragen
- Singleton-Pattern für einfache Nutzung

Erstellt: TAG 129 (2025-12-19)
"""

import os
import sys
import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Any, Union
from functools import lru_cache
import threading

# Zeep SOAP-Client
try:
    from zeep import Client, Settings
    from zeep.transports import Transport
    from zeep.plugins import HistoryPlugin
    from zeep.exceptions import Fault, TransportError
    from requests import Session
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("Bitte zeep und requests installieren: pip install zeep requests")
    sys.exit(1)

# Logging
logger = logging.getLogger(__name__)

# =============================================================================
# KONFIGURATION
# =============================================================================

# Aus config/locosoft_soap_config.py oder Environment
LOCOSOFT_SOAP_HOST = os.getenv('LOCOSOFT_SOAP_HOST', '10.80.80.7')
LOCOSOFT_SOAP_PORT = os.getenv('LOCOSOFT_SOAP_PORT', '8086')
LOCOSOFT_SOAP_USER = os.getenv('LOCOSOFT_SOAP_USER', '9001')
LOCOSOFT_SOAP_PASSWORD = os.getenv('LOCOSOFT_SOAP_PASSWORD', 'Max2024')

# v2.2 Header für writeAppointment etc.
LOCOSOFT_INTERFACE_KEY = os.getenv('LOCOSOFT_INTERFACE_KEY', 'GENE-AUTO')
LOCOSOFT_INTERFACE_VERSION = os.getenv('LOCOSOFT_INTERFACE_VERSION', '2.2')

WSDL_URL = f"http://{LOCOSOFT_SOAP_HOST}:{LOCOSOFT_SOAP_PORT}/?wsdl"
SOAP_URL = f"http://{LOCOSOFT_SOAP_HOST}:{LOCOSOFT_SOAP_PORT}/"


# =============================================================================
# SOAP CLIENT KLASSE
# =============================================================================

class LocosoftSOAPClient:
    """
    Vollständiger SOAP-Client für Locosoft DMS.

    Usage:
        client = LocosoftSOAPClient()

        # Werkstätten auflisten
        workshops = client.list_workshops()

        # Termine für einen Tag
        termine = client.list_appointments_by_date('2025-12-20')

        # Neuen Termin anlegen (v2.2)
        result = client.write_appointment({
            'customer': {'number': 1046889},
            'vehicle': {'number': 59085},
            'bringDateTime': '2025-12-20T09:00:00',
            'text': 'Inspektion'
        })
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton-Pattern für Connection Pooling."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._client = None
        self._history = HistoryPlugin()
        self._setup_client()

    def _setup_client(self):
        """Initialisiert den SOAP-Client mit Retry-Logik."""
        # Session mit Retry-Strategie
        session = Session()

        # Retry bei Verbindungsfehlern
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Basic Auth
        session.auth = (LOCOSOFT_SOAP_USER, LOCOSOFT_SOAP_PASSWORD)

        # v2.2 Header für alle Requests
        session.headers.update({
            'locosoftinterface': LOCOSOFT_INTERFACE_KEY,
            'locosoftinterfaceversion': LOCOSOFT_INTERFACE_VERSION,
        })

        # Transport mit Session
        transport = Transport(session=session, timeout=30)

        # Zeep Settings
        settings = Settings(
            strict=False,
            xml_huge_tree=True
        )

        try:
            self._client = Client(
                WSDL_URL,
                transport=transport,
                settings=settings,
                plugins=[self._history]
            )

            # WICHTIG: Überschreibe den Service-Endpoint!
            # Das WSDL referenziert soap.loco_soft.de, aber der echte Server ist 10.80.80.7
            self._service = self._client.create_service(
                '{http://soap.loco_soft.de/}DataqueryBinding',
                SOAP_URL
            )

            logger.info(f"SOAP-Client initialisiert: {SOAP_URL}")
        except Exception as e:
            logger.error(f"SOAP-Client Initialisierung fehlgeschlagen: {e}")
            raise

    @property
    def service(self):
        """Zugriff auf den SOAP-Service mit korrektem Endpoint."""
        return self._service

    def _to_date(self, d: Union[str, date, datetime]) -> date:
        """Konvertiert zu date-Objekt."""
        if isinstance(d, datetime):
            return d.date()
        if isinstance(d, date):
            return d
        if isinstance(d, str):
            return datetime.fromisoformat(d.replace('Z', '')).date()
        raise ValueError(f"Ungültiges Datum: {d}")

    def _to_datetime(self, dt: Union[str, date, datetime]) -> datetime:
        """Konvertiert zu datetime-Objekt."""
        if isinstance(dt, datetime):
            return dt
        if isinstance(dt, date):
            return datetime.combine(dt, datetime.min.time())
        if isinstance(dt, str):
            return datetime.fromisoformat(dt.replace('Z', ''))
        raise ValueError(f"Ungültiges Datum/Zeit: {dt}")

    # =========================================================================
    # LIST-OPERATIONEN (Lesen von Listen)
    # =========================================================================

    def list_workshops(self) -> List[Dict]:
        """
        Listet alle Werkstätten auf.

        Returns:
            Liste von Werkstätten mit workshopId, description
        """
        try:
            result = self.service.listWorkshops()
            return [self._serialize(ws) for ws in result] if result else []
        except Exception as e:
            logger.error(f"listWorkshops fehlgeschlagen: {e}")
            return []

    def list_work_groups(self) -> List[Dict]:
        """
        Listet alle Arbeitsgruppen auf (MON, SB, VKB, etc.).

        Returns:
            Liste von Arbeitsgruppen mit workGroupId, workGroupDescription
        """
        try:
            result = self.service.listWorkGroups()
            return [self._serialize(wg) for wg in result] if result else []
        except Exception as e:
            logger.error(f"listWorkGroups fehlgeschlagen: {e}")
            return []

    def list_labor_rates(self) -> List[Dict]:
        """
        Listet alle Stundensätze auf.

        Returns:
            Liste von Stundensätzen mit workshopId, rate, rateValue, description
        """
        try:
            result = self.service.listLaborRates()
            return [self._serialize(lr) for lr in result] if result else []
        except Exception as e:
            logger.error(f"listLaborRates fehlgeschlagen: {e}")
            return []

    def list_available_times(
        self,
        work_group_id: str,
        date_from: Union[str, date],
        date_to: Union[str, date]
    ) -> List[Dict]:
        """
        Listet verfügbare Kapazitäten pro Tag für eine Arbeitsgruppe.

        Args:
            work_group_id: Arbeitsgruppen-ID (z.B. 'MON', 'SB')
            date_from: Startdatum
            date_to: Enddatum

        Returns:
            Liste mit date, timeShould, timeCan, timeAvailable pro Tag
        """
        try:
            result = self.service.listAvailableTimes(
                workGroupId=work_group_id,
                dateFrom=self._to_date(date_from),
                dateTo=self._to_date(date_to)
            )
            return [self._serialize(at) for at in result] if result else []
        except Exception as e:
            logger.error(f"listAvailableTimes fehlgeschlagen: {e}")
            return []

    def list_appointments_by_date(
        self,
        date_from: Union[str, date, datetime],
        date_to: Union[str, date, datetime] = None
    ) -> List[Dict]:
        """
        Listet Termine in einem Zeitraum.

        Args:
            date_from: Startdatum/-zeit
            date_to: Enddatum/-zeit (default: date_from + 1 Tag)

        Returns:
            Liste von Terminen mit allen Details inkl. rentalCar
        """
        try:
            dt_from = self._to_datetime(date_from)
            if date_to is None:
                dt_to = dt_from + timedelta(days=1)
            else:
                dt_to = self._to_datetime(date_to)

            result = self.service.listAppointmentsByDate(
                dateFrom=dt_from,
                dateTo=dt_to
            )

            if result and hasattr(result, 'appointments'):
                return [self._serialize(apt) for apt in result.appointments]
            return []
        except Exception as e:
            logger.error(f"listAppointmentsByDate fehlgeschlagen: {e}")
            return []

    def list_open_work_orders(self) -> List[Dict]:
        """
        Listet alle offenen Werkstattaufträge.

        Returns:
            Liste von Aufträgen mit number, status, customer, vehicle
        """
        try:
            result = self.service.listOpenWorkOrders()
            return [self._serialize(wo) for wo in result] if result else []
        except Exception as e:
            logger.error(f"listOpenWorkOrders fehlgeschlagen: {e}")
            return []

    def list_customers(
        self,
        search_type: str,
        search_value: str
    ) -> List[Dict]:
        """
        Sucht Kunden.

        Args:
            search_type: 'NAM' (Name), 'PHN' (Telefon), 'NUM' (Nummer), 'EML' (Email)
            search_value: Suchbegriff

        Returns:
            Liste von Kunden
        """
        try:
            result = self.service.listCustomers({
                'customerSearchType': search_type,
                'customerSearchValue': search_value
            })
            return [self._serialize(c) for c in result] if result else []
        except Exception as e:
            logger.error(f"listCustomers fehlgeschlagen: {e}")
            return []

    def list_vehicles(
        self,
        search_type: str,
        search_value: str
    ) -> List[Dict]:
        """
        Sucht Fahrzeuge.

        Args:
            search_type: 'VIN' oder 'LPL' (License Plate)
            search_value: VIN oder Kennzeichen

        Returns:
            Liste von Fahrzeugen
        """
        try:
            result = self.service.listVehicles({
                'vehicleSearchType': search_type,
                'vehicleSearchValue': search_value
            })
            return [self._serialize(v) for v in result] if result else []
        except Exception as e:
            logger.error(f"listVehicles fehlgeschlagen: {e}")
            return []

    def list_customer_vehicles(self, customer_number: int) -> List[Dict]:
        """
        Listet Fahrzeuge eines Kunden.

        Args:
            customer_number: Kundennummer

        Returns:
            Liste von Fahrzeugen
        """
        try:
            result = self.service.listCustomerVehicles(customerNumber=customer_number)
            return [self._serialize(v) for v in result] if result else []
        except Exception as e:
            logger.error(f"listCustomerVehicles fehlgeschlagen: {e}")
            return []

    def list_spare_part_types(self) -> List[Dict]:
        """Listet alle Teilearten."""
        try:
            result = self.service.listSparePartTypes()
            return [self._serialize(t) for t in result] if result else []
        except Exception as e:
            logger.error(f"listSparePartTypes fehlgeschlagen: {e}")
            return []

    def list_changes(
        self,
        change_type: str,
        since: Union[str, datetime]
    ) -> List[Dict]:
        """
        Listet Änderungen seit einem Zeitpunkt (für Sync).

        Args:
            change_type: 'appointment', 'customer', 'vehicle', 'workOrder'
            since: Zeitstempel

        Returns:
            Liste von Änderungen mit number, changeType (C/D/N), timestamp
        """
        try:
            result = self.service.listChanges(
                listChangeType=change_type,
                listChangesSince=self._to_datetime(since)
            )
            return [self._serialize(c) for c in result] if result else []
        except Exception as e:
            logger.error(f"listChanges fehlgeschlagen: {e}")
            return []

    # =========================================================================
    # READ-OPERATIONEN (Einzelne Datensätze)
    # =========================================================================

    def read_appointment(self, appointment_number: int) -> Optional[Dict]:
        """Liest einen Termin mit allen Details."""
        try:
            result = self.service.readAppointment(number=appointment_number)
            return self._serialize(result) if result else None
        except Exception as e:
            logger.error(f"readAppointment({appointment_number}) fehlgeschlagen: {e}")
            return None

    def read_customer(self, customer_number: int) -> Optional[Dict]:
        """Liest Kundenstammdaten."""
        try:
            result = self.service.readCustomer(number=customer_number)
            return self._serialize(result) if result else None
        except Exception as e:
            logger.error(f"readCustomer({customer_number}) fehlgeschlagen: {e}")
            return None

    def read_vehicle(self, vehicle_number: int) -> Optional[Dict]:
        """Liest Fahrzeugstammdaten."""
        try:
            result = self.service.readVehicle(number=vehicle_number)
            return self._serialize(result) if result else None
        except Exception as e:
            logger.error(f"readVehicle({vehicle_number}) fehlgeschlagen: {e}")
            return None

    def read_work_order_details(self, order_number: int) -> Optional[Dict]:
        """Liest Auftragsdetails mit allen Positionen."""
        try:
            result = self.service.readWorkOrderDetails(orderNumber=order_number)
            return self._serialize(result) if result else None
        except Exception as e:
            logger.error(f"readWorkOrderDetails({order_number}) fehlgeschlagen: {e}")
            return None

    def read_part_information(self, part_number: str) -> Optional[Dict]:
        """Liest Teile-Informationen inkl. Lagerbestand."""
        try:
            result = self.service.readPartInformation(partNumber=part_number)
            return self._serialize(result) if result else None
        except Exception as e:
            logger.error(f"readPartInformation({part_number}) fehlgeschlagen: {e}")
            return None

    # =========================================================================
    # WRITE-OPERATIONEN (Schreiben - benötigt v2.2 Header)
    # =========================================================================

    def write_appointment(self, appointment: Dict) -> Dict:
        """
        Erstellt oder aktualisiert einen Termin.

        Args:
            appointment: Dict mit Termin-Daten:
                - number: 0 für neu, >0 für Update
                - text: Beschreibung
                - customer: {'number': int}
                - vehicle: {'number': int}
                - bringDateTime: ISO-String oder datetime
                - returnDateTime: ISO-String oder datetime (optional)
                - type: 'fix', 'loose', 'indefinite', 'real'
                - rentalCar: {'number': int} (optional, für Ersatzwagen)

        Returns:
            Dict mit 'success', 'number', 'message'
        """
        try:
            # Konvertiere Datumsfelder
            if 'bringDateTime' in appointment and appointment['bringDateTime']:
                appointment['bringDateTime'] = self._to_datetime(appointment['bringDateTime'])
            if 'returnDateTime' in appointment and appointment['returnDateTime']:
                appointment['returnDateTime'] = self._to_datetime(appointment['returnDateTime'])

            # Default number=0 für neue Termine
            if 'number' not in appointment:
                appointment['number'] = 0

            result = self.service.writeAppointment(appointment=appointment)

            return {
                'success': True,
                'number': result if isinstance(result, int) else getattr(result, 'number', None),
                'message': 'Termin erfolgreich gespeichert'
            }
        except Fault as e:
            logger.error(f"writeAppointment SOAP-Fault: {e}")
            return {'success': False, 'number': None, 'message': str(e)}
        except Exception as e:
            logger.error(f"writeAppointment fehlgeschlagen: {e}")
            return {'success': False, 'number': None, 'message': str(e)}

    def write_work_order_details(self, work_order: Dict) -> Dict:
        """
        Erstellt oder aktualisiert einen Auftrag.

        Args:
            work_order: Dict mit Auftrags-Daten

        Returns:
            Dict mit 'success', 'number', 'message'
        """
        try:
            result = self.service.writeWorkOrderDetails(workOrder=work_order)
            return {
                'success': True,
                'number': result if isinstance(result, int) else getattr(result, 'number', None),
                'message': 'Auftrag erfolgreich gespeichert'
            }
        except Fault as e:
            logger.error(f"writeWorkOrderDetails SOAP-Fault: {e}")
            return {'success': False, 'number': None, 'message': str(e)}
        except Exception as e:
            logger.error(f"writeWorkOrderDetails fehlgeschlagen: {e}")
            return {'success': False, 'number': None, 'message': str(e)}

    def write_work_order_times(self, times: Dict) -> Dict:
        """
        Bucht Arbeitszeiten auf einen Auftrag.

        Args:
            times: Dict mit:
                - workOrderNumber: int
                - mechanicId: int
                - startTimestamp: datetime
                - endTimestamp: datetime (optional)
                - isFinished: bool (optional)
                - workOrderLineNumber: int oder List[int]

        Returns:
            Dict mit 'success', 'message'
        """
        try:
            # Konvertiere Timestamps
            if 'startTimestamp' in times:
                times['startTimestamp'] = self._to_datetime(times['startTimestamp'])
            if 'endTimestamp' in times and times['endTimestamp']:
                times['endTimestamp'] = self._to_datetime(times['endTimestamp'])

            self.service.writeWorkOrderTimes(workOrderTime=times)
            return {'success': True, 'message': 'Zeiten erfolgreich gebucht'}
        except Fault as e:
            logger.error(f"writeWorkOrderTimes SOAP-Fault: {e}")
            return {'success': False, 'message': str(e)}
        except Exception as e:
            logger.error(f"writeWorkOrderTimes fehlgeschlagen: {e}")
            return {'success': False, 'message': str(e)}

    def write_customer_details(self, customer: Dict) -> Dict:
        """Erstellt oder aktualisiert Kundendaten."""
        try:
            result = self.service.writeCustomerDetails(customer=customer)
            return {
                'success': True,
                'number': result if isinstance(result, int) else getattr(result, 'number', None),
                'message': 'Kunde erfolgreich gespeichert'
            }
        except Exception as e:
            logger.error(f"writeCustomerDetails fehlgeschlagen: {e}")
            return {'success': False, 'number': None, 'message': str(e)}

    def write_vehicle_details(self, vehicle: Dict) -> Dict:
        """Erstellt oder aktualisiert Fahrzeugdaten."""
        try:
            result = self.service.writeVehicleDetails(vehicle=vehicle)
            return {
                'success': True,
                'number': result if isinstance(result, int) else getattr(result, 'number', None),
                'message': 'Fahrzeug erfolgreich gespeichert'
            }
        except Exception as e:
            logger.error(f"writeVehicleDetails fehlgeschlagen: {e}")
            return {'success': False, 'number': None, 'message': str(e)}

    # =========================================================================
    # HILFSMETHODEN
    # =========================================================================

    def _serialize(self, obj) -> Dict:
        """Konvertiert SOAP-Objekt zu Dict."""
        if obj is None:
            return {}
        if isinstance(obj, dict):
            return obj

        result = {}
        for key in dir(obj):
            if key.startswith('_'):
                continue
            try:
                value = getattr(obj, key)
                if callable(value):
                    continue
                if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                    # Liste von SOAP-Objekten
                    if hasattr(value, '__len__') and len(value) > 0:
                        first = value[0] if len(value) > 0 else None
                        if first and hasattr(first, '__dict__'):
                            result[key] = [self._serialize(v) for v in value]
                        else:
                            result[key] = list(value)
                    else:
                        result[key] = []
                elif hasattr(value, '__dict__') and not isinstance(value, type):
                    # Verschachteltes SOAP-Objekt
                    result[key] = self._serialize(value)
                elif isinstance(value, (datetime, date)):
                    result[key] = value.isoformat()
                else:
                    result[key] = value
            except Exception:
                pass
        return result

    def health_check(self) -> Dict:
        """
        Prüft die Verbindung zur SOAP-API.

        Returns:
            Dict mit 'healthy', 'message', 'workshops_count'
        """
        try:
            workshops = self.list_workshops()
            return {
                'healthy': True,
                'message': 'SOAP-Verbindung OK',
                'workshops_count': len(workshops),
                'endpoint': SOAP_URL
            }
        except Exception as e:
            return {
                'healthy': False,
                'message': str(e),
                'workshops_count': 0,
                'endpoint': SOAP_URL
            }


# =============================================================================
# SINGLETON-ACCESSOR
# =============================================================================

_client: Optional[LocosoftSOAPClient] = None

def get_soap_client() -> LocosoftSOAPClient:
    """
    Holt die Singleton-Instanz des SOAP-Clients.

    Usage:
        from tools.locosoft_soap_client import get_soap_client

        client = get_soap_client()
        workshops = client.list_workshops()
    """
    global _client
    if _client is None:
        _client = LocosoftSOAPClient()
    return _client


# =============================================================================
# CLI FÜR TESTS
# =============================================================================

if __name__ == '__main__':
    import json

    # Logging einschalten
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

    print("=" * 70)
    print("LOCOSOFT SOAP CLIENT TEST")
    print("=" * 70)

    client = get_soap_client()

    # Health Check
    print("\n[1] Health Check...")
    health = client.health_check()
    print(f"    Status: {'✅ OK' if health['healthy'] else '❌ FEHLER'}")
    print(f"    Endpoint: {health['endpoint']}")
    print(f"    Werkstätten: {health['workshops_count']}")

    if not health['healthy']:
        print(f"    Fehler: {health['message']}")
        sys.exit(1)

    # Werkstätten
    print("\n[2] Werkstätten...")
    workshops = client.list_workshops()
    for ws in workshops:
        print(f"    - ID {ws.get('workshopId')}: {ws.get('description')}")

    # Arbeitsgruppen
    print("\n[3] Arbeitsgruppen...")
    groups = client.list_work_groups()
    for wg in groups[:5]:
        print(f"    - {wg.get('workGroupId')}: {wg.get('workGroupDescription')}")
    print(f"    ... ({len(groups)} Gruppen gesamt)")

    # Kapazitäten für MON
    print("\n[4] Kapazitäten (MON, nächste 7 Tage)...")
    today = date.today()
    next_week = today + timedelta(days=7)
    times = client.list_available_times('MON', today, next_week)
    for t in times[:5]:
        print(f"    - {t.get('date')}: Soll={t.get('timeShould')} Kann={t.get('timeCan')} Frei={t.get('timeAvailable')}")

    # Offene Aufträge
    print("\n[5] Offene Aufträge...")
    orders = client.list_open_work_orders()
    print(f"    Anzahl: {len(orders)}")
    for wo in orders[:3]:
        vehicle = wo.get('vehicle', {})
        print(f"    - #{wo.get('number')}: {vehicle.get('licensePlate', '?')} - Status: {wo.get('status')}")

    # Termine heute
    print("\n[6] Termine heute...")
    appointments = client.list_appointments_by_date(today)
    print(f"    Anzahl: {len(appointments)}")
    for apt in appointments[:3]:
        vehicle = apt.get('vehicle', {})
        print(f"    - #{apt.get('number')}: {vehicle.get('licensePlate', '?')} - {apt.get('text', '')[:30]}")

    print("\n" + "=" * 70)
    print("TESTS ABGESCHLOSSEN")
    print("=" * 70)
