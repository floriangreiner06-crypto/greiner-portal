"""
GUDAT Data Module - Abstraktionsschicht für Werkstatt-Disposition

TAG 153: Erstellt als Teil der DRIVE Werkstattplaner-Strategie

ARCHITEKTUR-HINWEIS:
====================
Dieses Modul ist eine ÜBERGANGS-LÖSUNG!

Aktuelle Situation (Phase 1):
- Gudat ist das Dispositionssystem
- Dieses Modul kapselt alle Gudat-Zugriffe
- Consumer: werkstatt_live_api.py, werkstatt_data.py

Ziel-Situation (Phase 2-4):
- DRIVE Werkstattplaner ersetzt Gudat
- Locosoft SOAP wird Single Source of Truth
- Dieses Modul wird zu locosoft_disposition.py migriert

Siehe: docs/DRIVE_WERKSTATTPLANUNG_MACHBARKEITSSTUDIE.md

MIGRATION-PATTERN:
==================
1. Alle Gudat-Zugriffe NUR über dieses Modul
2. Interface bleibt stabil, Backend wird ausgetauscht
3. Wenn Locosoft SOAP ready: Implementierung austauschen

Beispiel:
    # Heute (Gudat)
    GudatData.get_disposition(datum) -> holt von Gudat GraphQL

    # Morgen (Locosoft)
    GudatData.get_disposition(datum) -> holt von Locosoft SOAP
    (oder rename zu DispositionData)
"""

import logging
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Gudat Client Import (optional - graceful degradation)
try:
    from gudat_client import GudatClient
    GUDAT_AVAILABLE = True
except ImportError:
    GUDAT_AVAILABLE = False
    logger.warning("GudatClient nicht verfügbar - Disposition deaktiviert")


class GudatData:
    """
    Single Source of Truth für Werkstatt-Disposition (Gudat-Schicht).

    WICHTIG: Diese Klasse wird später durch LocosoftDisposition ersetzt!
    Interface bleibt gleich, nur Backend ändert sich.

    Methoden:
    - get_disposition(): Wer macht heute welchen Auftrag?
    - match_mechaniker_name(): Locosoft-Name <-> Gudat-Name Mapping
    - merge_zeitbloecke(): Gudat-Tasks in bestehende Zeitblöcke mergen
    - get_kapazitaet(): Team-Kapazitäten (Proxy zu Gudat API)
    """

    # Gudat Credentials (aus Config laden wäre besser)
    # TODO: Nach config/gudat.json auslagern
    _config = {
        'username': 'jgreiner',
        'password': 'Greiner2024!'
    }

    # Cache für wiederholte Abfragen (gleicher Tag)
    _disposition_cache: Dict[str, Dict] = {}
    _cache_timestamp: Optional[datetime] = None
    _cache_ttl_seconds = 60  # 1 Minute Cache

    @classmethod
    def get_disposition(cls, target_date: Optional[date] = None) -> Dict[str, List[Dict]]:
        """
        Holt Werkstatt-Disposition aus Gudat (workshopTasks).

        Args:
            target_date: Datum für Disposition (default: heute)

        Returns:
            Dict mit Mechaniker-Namen als Keys und Listen von Tasks als Values:
            {
                "Tobias Reitmeier": [
                    {
                        "gudat_id": "123",
                        "kennzeichen": "DEG-AB 123",
                        "auftrag_nr": 39650,
                        "vorgabe_aw": 2.5,
                        "status": "geplant",
                        "beschreibung": "Inspektion",
                        "service": "Allgemeine Reparatur",
                        "start_date": "2026-01-02 10:30:00"
                    },
                    ...
                ],
                ...
            }

        MIGRATION-NOTE:
            Wenn Locosoft SOAP: Hier listOpenWorkOrders() + readWorkOrderDetails()
            kombinieren um Mechaniker-Zuweisung (labor.mechanicId) zu holen.
        """
        if not GUDAT_AVAILABLE:
            logger.warning("GudatClient nicht verfügbar")
            return {}

        # Datum normalisieren
        if target_date is None:
            target_date = date.today()
        elif isinstance(target_date, datetime):
            target_date = target_date.date()

        date_str = target_date.isoformat()

        # Cache prüfen
        if cls._is_cache_valid(date_str):
            logger.debug(f"Gudat-Disposition aus Cache: {date_str}")
            return cls._disposition_cache.get(date_str, {})

        try:
            client = GudatClient(cls._config['username'], cls._config['password'])
            if not client.login():
                logger.error("Gudat Login fehlgeschlagen")
                return {}

            # GraphQL Query für workshopTasks
            query = """
            query GetWorkshopTasks($page: Int!, $itemsPerPage: Int!, $where: QueryWorkshopTasksWhereWhereConditions) {
              workshopTasks(first: $itemsPerPage, page: $page, where: $where) {
                data {
                  id
                  start_date
                  work_load
                  work_state
                  description
                  workshopService { id name }
                  resource { id name }
                  dossier {
                    id
                    vehicle { id license_plate }
                    orders { id number }
                  }
                }
              }
            }
            """

            variables = {
                "page": 1,
                "itemsPerPage": 200,
                "where": {
                    "AND": [{"column": "START_DATE", "operator": "EQ", "value": date_str}]
                }
            }

            response = client.session.post(
                f"{GudatClient.BASE_URL}/graphql",
                json={"operationName": "GetWorkshopTasks", "query": query, "variables": variables},
                headers={
                    'Accept': 'application/json',
                    'X-XSRF-TOKEN': client._get_xsrf(),
                    'Content-Type': 'application/json'
                }
            )

            data = response.json()
            if 'errors' in data:
                logger.error(f"Gudat GraphQL Fehler: {data['errors']}")
                return {}

            tasks = data.get('data', {}).get('workshopTasks', {}).get('data', [])

            # Gruppiere nach Mechaniker (resource.name)
            by_mechanic = {}
            for task in tasks:
                resource = task.get('resource')
                if not resource:
                    continue
                mech_name = resource.get('name', '').strip()
                if not mech_name:
                    continue

                # Dossier-Daten extrahieren
                dossier = task.get('dossier') or {}
                vehicle = dossier.get('vehicle') or {}
                orders = dossier.get('orders') or []

                task_data = {
                    'gudat_id': task.get('id'),
                    'kennzeichen': vehicle.get('license_plate', ''),
                    'auftrag_nr': orders[0].get('number') if orders else None,
                    'vorgabe_aw': float(task.get('work_load') or 0),
                    'status': task.get('work_state', ''),
                    'beschreibung': task.get('description', ''),
                    'service': (task.get('workshopService') or {}).get('name', ''),
                    'start_date': task.get('start_date')  # Format: "2026-01-02 10:30:00"
                }

                if mech_name not in by_mechanic:
                    by_mechanic[mech_name] = []
                by_mechanic[mech_name].append(task_data)

            # Cache aktualisieren
            cls._disposition_cache[date_str] = by_mechanic
            cls._cache_timestamp = datetime.now()

            logger.info(f"Gudat: {len(tasks)} Tasks für {len(by_mechanic)} Mechaniker geladen")
            return by_mechanic

        except Exception as e:
            logger.error(f"Gudat Fehler: {e}")
            return {}

    @classmethod
    def match_mechaniker_name(cls, locosoft_name: str, gudat_names: List[str]) -> Optional[str]:
        """
        Findet passenden Gudat-Namen für Locosoft-Namen.

        Locosoft Format: "Nachname, Vorname" (z.B. "Reitmeier, Tobias")
        Gudat Format: "Vorname Nachname" (z.B. "Tobias Reitmeier")

        Args:
            locosoft_name: Name im Locosoft-Format
            gudat_names: Liste von Namen im Gudat-Format

        Returns:
            Passender Gudat-Name oder None

        MIGRATION-NOTE:
            Bei Locosoft SOAP entfällt dieses Mapping - mechanicId ist eindeutig!
        """
        if not locosoft_name:
            return None

        # Locosoft: "Reitmeier, Tobias" → parts = ["Reitmeier", "Tobias"]
        parts = [p.strip() for p in locosoft_name.split(',')]
        if len(parts) < 2:
            return None

        nachname = parts[0]
        vorname = parts[1].split()[0]  # Nur erster Vorname

        # Gudat-Patterns zum Matchen
        gudat_pattern1 = f"{vorname} {nachname}"
        gudat_pattern2 = f"{nachname} {vorname}"

        for gn in gudat_names:
            gn_lower = gn.lower()
            # Exakte Matches
            if gudat_pattern1.lower() == gn_lower or gudat_pattern2.lower() == gn_lower:
                return gn
            # Fuzzy: enthält Vor- und Nachname
            if vorname.lower() in gn_lower and nachname.lower() in gn_lower:
                return gn

        return None

    @classmethod
    def create_mechaniker_mapping(cls, locosoft_mechaniker: List[Dict],
                                   gudat_disposition: Dict[str, List]) -> Dict[int, List[Dict]]:
        """
        Erstellt Mapping: Locosoft employee_number -> Gudat Tasks.

        Args:
            locosoft_mechaniker: Liste mit {'employee_number': int, 'name': str}
            gudat_disposition: Output von get_disposition()

        Returns:
            {employee_number: [gudat_tasks]}

        MIGRATION-NOTE:
            Bei Locosoft SOAP: Mapping über labor.mechanicId (direkt, kein Name-Matching)
        """
        mapping = {}
        gudat_names = list(gudat_disposition.keys())

        for mech in locosoft_mechaniker:
            emp_nr = mech.get('employee_number')
            name = mech.get('name', '')

            matched_name = cls.match_mechaniker_name(name, gudat_names)
            if matched_name:
                mapping[emp_nr] = gudat_disposition[matched_name]

        return mapping

    @classmethod
    def merge_zeitbloecke(cls, zeitbloecke: List[Dict], gudat_tasks: List[Dict],
                          datum: date) -> List[Dict]:
        """
        Merged Gudat-Tasks in bestehende Zeitblöcke.

        Logik:
        1. Wenn Auftrag schon existiert: Gudat-Daten ergänzen (Zeit, AW)
        2. Wenn Kennzeichen schon existiert: Gudat-Zeit übernehmen
        3. Sonst: Neuen Zeitblock anlegen (typ='gudat_geplant')

        Args:
            zeitbloecke: Bestehende Zeitblöcke aus Locosoft
            gudat_tasks: Tasks aus get_disposition()
            datum: Referenz-Datum

        Returns:
            Erweiterte Zeitblöcke-Liste

        MIGRATION-NOTE:
            Bei Locosoft SOAP: Diese Funktion wird obsolet - alles aus einer Quelle!
        """
        # Fallback-Startzeit für Tasks ohne Gudat-Zeit
        gudat_start_time = datetime.combine(datum, time(8, 0))

        for zb in zeitbloecke:
            if zb.get('ende_ts'):
                try:
                    ende_dt = datetime.fromisoformat(zb['ende_ts'])
                    if ende_dt > gudat_start_time:
                        gudat_start_time = ende_dt
                except:
                    pass

        for gt in gudat_tasks:
            auftrag_nr = gt.get('auftrag_nr')
            kz = (gt.get('kennzeichen') or '').replace(' ', '').replace('-', '').upper()

            # Prüfen ob Auftrag schon existiert
            existing = next((z for z in zeitbloecke if z.get('auftrag_nr') == auftrag_nr), None)
            if existing:
                cls._merge_gudat_into_existing(existing, gt)
                continue

            # Prüfen ob Kennzeichen schon existiert
            if kz:
                existing_by_kz = next(
                    (z for z in zeitbloecke
                     if (z.get('kennzeichen') or '').replace(' ', '').replace('-', '').upper() == kz),
                    None
                )
                if existing_by_kz:
                    cls._merge_gudat_into_existing(existing_by_kz, gt)
                    continue

            # Neuen Zeitblock anlegen
            task_start_time = gudat_start_time
            if gt.get('start_date'):
                try:
                    start_str = gt['start_date'].replace('T', ' ')
                    task_start_time = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    pass

            # Geschätzte Dauer: AW * 6 Minuten (oder min 30 Min)
            aw = gt.get('vorgabe_aw', 0) or 2
            dauer_min = max(int(aw * 6), 30)
            task_ende_time = task_start_time + timedelta(minutes=dauer_min)

            zeitbloecke.append({
                'auftrag_nr': auftrag_nr,
                'kennzeichen': gt.get('kennzeichen', ''),
                'kunde': '',
                'marke': '',
                'vorgabe_aw': gt.get('vorgabe_aw', 0),
                'beschreibung': gt.get('beschreibung', ''),
                'service': gt.get('service', ''),
                'gudat_status': gt.get('status', ''),
                'start': task_start_time.strftime('%H:%M'),
                'start_ts': task_start_time.isoformat(),
                'ende': task_ende_time.strftime('%H:%M'),
                'ende_ts': task_ende_time.isoformat(),
                'ist_aktiv': False,
                'dauer_min': dauer_min,
                'typ': 'gudat_geplant'
            })

            # Für Fallback-Stacking
            if task_ende_time > gudat_start_time:
                gudat_start_time = task_ende_time

        return zeitbloecke

    @classmethod
    def _merge_gudat_into_existing(cls, existing: Dict, gudat_task: Dict) -> None:
        """Merged Gudat-Daten in bestehenden Zeitblock."""
        # Fehlende Daten ergänzen
        if not existing.get('kennzeichen') and gudat_task.get('kennzeichen'):
            existing['kennzeichen'] = gudat_task.get('kennzeichen')
        if not existing.get('vorgabe_aw') and gudat_task.get('vorgabe_aw'):
            existing['vorgabe_aw'] = gudat_task.get('vorgabe_aw')

        # Gudat-Startzeit hat Vorrang (wenn nicht aktiv)
        if gudat_task.get('start_date') and not existing.get('ist_aktiv'):
            try:
                start_str = gudat_task['start_date'].replace('T', ' ')
                gudat_time = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
                existing['start'] = gudat_time.strftime('%H:%M')
                existing['start_ts'] = gudat_time.isoformat()

                # Ende neu berechnen
                aw = existing.get('vorgabe_aw') or gudat_task.get('vorgabe_aw') or 2
                dauer = max(int(aw * 6), 30)
                ende_time = gudat_time + timedelta(minutes=dauer)
                existing['ende'] = ende_time.strftime('%H:%M')
                existing['ende_ts'] = ende_time.isoformat()
            except (ValueError, TypeError):
                pass

    @classmethod
    def _is_cache_valid(cls, date_str: str) -> bool:
        """Prüft ob Cache noch gültig ist."""
        if cls._cache_timestamp is None:
            return False
        if date_str not in cls._disposition_cache:
            return False
        age = (datetime.now() - cls._cache_timestamp).total_seconds()
        return age < cls._cache_ttl_seconds

    @classmethod
    def clear_cache(cls) -> None:
        """Cache leeren (z.B. nach Änderungen)."""
        cls._disposition_cache = {}
        cls._cache_timestamp = None
        logger.debug("Gudat-Cache geleert")

    @classmethod
    def get_kapazitaet(cls) -> Dict[str, Any]:
        """
        Holt Kapazitäts-Daten aus der Gudat API.

        TAG 153: Aus werkstatt_live_api.py migriert.

        Ruft /api/gudat/workload auf und transformiert die Daten.
        Echte Werkstatt-Kapazität = nur interne Mechanik-Teams:
        - Allgemeine Reparatur (ID 2)
        - Diagnosetechnik (ID 3)
        - NW/GW (ID 5)

        Returns:
            {
                'success': True,
                'kapazitaet': 48.0,
                'geplant': 35.5,
                'frei': 12.5,
                'auslastung': 74.0,
                'status': 'warning',  # ok/warning/critical
                'teams': [...],
                'interne_teams': [...],
                'woche': [...],
                'source': 'gudat'
            }

        MIGRATION-NOTE:
            Bei Locosoft SOAP: listAvailableTimes() für Kapazitäten nutzen.
        """
        import requests

        # Interne Mechanik-Teams (echte Werkstatt-Kapazität)
        INTERNE_TEAMS = {2, 3, 5}  # Allgemeine Reparatur, Diagnosetechnik, NW/GW

        try:
            # Lokalen Gudat-API Endpunkt aufrufen
            response = requests.get(
                'http://localhost:5000/api/gudat/workload',
                timeout=10
            )

            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Gudat API Fehler: {response.status_code}',
                    'source': 'gudat'
                }

            data = response.json()

            if 'error' in data:
                return {
                    'success': False,
                    'error': data['error'],
                    'source': 'gudat'
                }

            # Wochen-Daten holen
            week_response = requests.get(
                'http://localhost:5000/api/gudat/workload/week',
                timeout=10
            )
            week_data = week_response.json() if week_response.status_code == 200 else {}

            # Nur interne Teams für Kapazität zählen
            teams = data.get('teams', [])
            interne_teams = [t for t in teams if t.get('id') in INTERNE_TEAMS]

            # Kapazität nur aus internen Teams berechnen
            intern_kapazitaet = sum(t.get('capacity', 0) for t in interne_teams)
            intern_geplant = sum(t.get('planned', 0) for t in interne_teams)
            intern_frei = sum(t.get('free', 0) for t in interne_teams)
            intern_auslastung = round((intern_geplant / intern_kapazitaet * 100), 1) if intern_kapazitaet > 0 else 0

            # Status basierend auf Auslastung
            if intern_auslastung >= 90:
                status = 'critical'
            elif intern_auslastung >= 70:
                status = 'warning'
            else:
                status = 'ok'

            return {
                'success': True,
                'kapazitaet': intern_kapazitaet,
                'geplant': intern_geplant,
                'frei': intern_frei,
                'auslastung': intern_auslastung,
                'status': status,
                'teams': teams,  # Alle Teams für Detail-Ansicht
                'interne_teams': interne_teams,
                'woche': week_data.get('days', []),
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'hinweis': 'Kapazität = nur Allgemeine Reparatur + Diagnosetechnik + NW/GW',
                'source': 'gudat'
            }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Gudat API Timeout',
                'source': 'gudat'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Gudat API nicht erreichbar',
                'source': 'gudat'
            }
        except Exception as e:
            logger.error(f"Fehler bei Gudat Kapazität: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'gudat'
            }

    @classmethod
    def get_stats(cls, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Statistiken zur Disposition.

        Returns:
            {
                'datum': '2026-01-02',
                'total_tasks': 25,
                'mechaniker_count': 8,
                'mechaniker': ['Tobias Reitmeier', ...],
                'source': 'gudat'  # später 'locosoft'
            }
        """
        disposition = cls.get_disposition(target_date)

        if target_date is None:
            target_date = date.today()

        total_tasks = sum(len(tasks) for tasks in disposition.values())

        return {
            'datum': target_date.isoformat(),
            'total_tasks': total_tasks,
            'mechaniker_count': len(disposition),
            'mechaniker': list(disposition.keys()),
            'source': 'gudat'  # Marker für spätere Migration
        }


# =============================================================================
# CONVENIENCE FUNCTIONS (für einfachen Import)
# =============================================================================

def get_gudat_disposition(target_date: Optional[date] = None) -> Dict[str, List[Dict]]:
    """Wrapper für GudatData.get_disposition()."""
    return GudatData.get_disposition(target_date)


def match_gudat_mechaniker(locosoft_mechaniker: List[Dict],
                           datum: Optional[date] = None) -> Dict[int, List[Dict]]:
    """
    Convenience: Holt Disposition und erstellt Mechaniker-Mapping.

    Args:
        locosoft_mechaniker: Liste mit {'employee_number': int, 'name': str}
        datum: Datum (default: heute)

    Returns:
        {employee_number: [gudat_tasks]}
    """
    disposition = GudatData.get_disposition(datum)
    return GudatData.create_mechaniker_mapping(locosoft_mechaniker, disposition)
