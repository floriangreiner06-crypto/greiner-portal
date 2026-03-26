"""
API: Garantieaufträge-Übersicht
================================
TAG 181: Übersicht aller offenen Garantieaufträge mit Garantieakte-Status
"""
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
import json
import logging

from datetime import date, timedelta

from api.db_utils import locosoft_session
from api.standort_utils import BETRIEB_NAMEN

logger = logging.getLogger(__name__)

# Gudat Center aus Standort: 1/2 = Deggendorf, 3 = Landau
def _gudat_center_from_subsidiary(subsidiary):
    return 'landau' if subsidiary == 3 else 'deggendorf'


def _normalize_order_num(num) -> str:
    """Einheitliche Darstellung für Set-Vergleich."""
    if num is None:
        return ""
    s = str(num).strip()
    return s.lstrip("0") or "0"


def _normalize_kennzeichen(kz) -> str:
    """Kennzeichen für Abgleich normalisieren (Leerzeichen weg, Großbuchstaben)."""
    if kz is None or not str(kz).strip():
        return ""
    return str(kz).strip().upper().replace(" ", "").replace("-", "")


def _gudat_auftragsnummern_mit_dossier(center: str) -> dict:
    """
    Holt einmalig alle Auftragsnummern und Kennzeichen, die in Gudat (für dieses Center) ein Dossier haben.
    Returns: {"order_numbers": set(str), "license_plates": set(str)} (normalisiert).
    """
    order_numbers = set()
    license_plates = set()
    try:
        from api.gudat_api import get_gudat_client
        client = get_gudat_client(center)
    except Exception as e:
        logger.debug("Gudat-Client für Batch-Check nicht verfügbar: %s", e)
        return {"order_numbers": set(), "license_plates": set()}

    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    try:
        headers["X-XSRF-TOKEN"] = client._get_xsrf()
    except Exception:
        pass

    query_tasks = """
    query GetWorkshopTasks($page: Int!, $itemsPerPage: Int!, $where: QueryWorkshopTasksWhereWhereConditions) {
      workshopTasks(first: $itemsPerPage, page: $page, where: $where) {
        data { id, dossier { id, orders { number }, vehicle { license_plate } } }
      }
    }
    """
    start_date = (date.today() - timedelta(days=90)).isoformat()
    end_date = (date.today() + timedelta(days=30)).isoformat()
    # Appointments: reines Datum (YYYY-MM-DD), Gudat akzeptiert das zuverlässiger als mit Uhrzeit
    apt_start = start_date
    apt_end = end_date

    def collect_from_tasks(tasks):
        for task in tasks or []:
            dossier = task.get("dossier") or {}
            for order in dossier.get("orders", []) or []:
                n = order.get("number")
                if n is not None:
                    order_numbers.add(_normalize_order_num(n))
                    order_numbers.add(str(n).strip())
            vehicle = dossier.get("vehicle") or {}
            lp = vehicle.get("license_plate")
            if lp and str(lp).strip():
                license_plates.add(_normalize_kennzeichen(lp))

    # 1) Heute
    try:
        r = client.session.post(
            f"{client.BASE_URL}/graphql",
            json={
                "operationName": "GetWorkshopTasks",
                "query": query_tasks,
                "variables": {
                    "page": 1,
                    "itemsPerPage": 200,
                    "where": {"AND": [{"column": "START_DATE", "operator": "EQ", "value": date.today().isoformat()}]},
                },
            },
            headers=headers,
        )
        data = r.json()
        if "errors" not in data:
            collect_from_tasks((data.get("data") or {}).get("workshopTasks", {}).get("data", []))
    except Exception as e:
        logger.debug("Gudat workshopTasks (heute) Batch: %s", e)

    # 2) 90 Tage zurück + 30 vor, max 5 Seiten
    for page in range(1, 6):
        try:
            r = client.session.post(
                f"{client.BASE_URL}/graphql",
                json={
                    "operationName": "GetWorkshopTasks",
                    "query": query_tasks,
                    "variables": {
                        "page": page,
                        "itemsPerPage": 200,
                        "where": {
                            "AND": [
                                {"column": "START_DATE", "operator": "GTE", "value": start_date},
                                {"column": "START_DATE", "operator": "LTE", "value": end_date},
                            ]
                        },
                    },
                },
                headers=headers,
            )
            data = r.json()
            if data.get("errors"):
                break
            tasks = (data.get("data") or {}).get("workshopTasks", {}).get("data", []) or []
            if not tasks:
                break
            collect_from_tasks(tasks)
        except Exception as e:
            logger.debug("Gudat workshopTasks (Range) Batch Seite %s: %s", page, e)

    # 3) Appointments-Fallback (Dossier „abgeholt“ etc.), max 20 Seiten
    first_per_page = 200
    query_apt_inline = (
        """
    query GetAppointmentsByDate {
      appointments(first: %d, page: %d, where: {
        AND: [
          {column: START_DATE_TIME, operator: GTE, value: "%s"},
          {column: START_DATE_TIME, operator: LTE, value: "%s"}
        ]
      }) {
        data { id, dossier { id, orders { number }, vehicle { license_plate } } }
      }
    }
    """
    )
    for page in range(1, 21):
        try:
            query_apt = query_apt_inline % (first_per_page, page, apt_start, apt_end)
            r = client.session.post(
                f"{client.BASE_URL}/graphql",
                json={"operationName": "GetAppointmentsByDate", "query": query_apt},
                headers=headers,
            )
            apt_data = r.json()
            if apt_data.get("errors"):
                break
            appointments = (apt_data.get("data") or {}).get("appointments", {}).get("data", []) or []
            if not appointments:
                break
            for apt in appointments:
                dossier = apt.get("dossier") or {}
                for order in dossier.get("orders", []) or []:
                    n = order.get("number")
                    if n is not None:
                        order_numbers.add(_normalize_order_num(n))
                        order_numbers.add(str(n).strip())
                vehicle = dossier.get("vehicle") or {}
                lp = vehicle.get("license_plate")
                if lp and str(lp).strip():
                    license_plates.add(_normalize_kennzeichen(lp))
            if len(appointments) < first_per_page:
                break
        except Exception as e:
            logger.debug("Gudat Appointments Batch Seite %s: %s", page, e)

    return {"order_numbers": order_numbers, "license_plates": license_plates}


def _gudat_dossier_gefunden(order_number: int, subsidiary: int) -> bool:
    """
    Prüft ob in Gudat ein Dossier mit dieser Auftragsnummer existiert (nur Suche, kein Laden).
    Nutzt workshopTasks (heute, dann 90 Tage zurück + 30 vor).
    Returns: True wenn gefunden, False sonst. Bei Fehler: False (kein Abbruch).
    """
    def order_match(order_num, target):
        if order_num is None:
            return False
        a = str(order_num).strip()
        b = str(target).strip()
        if a == b:
            return True
        if a.isdigit() and b.isdigit() and int(a) == int(b):
            return True
        if a.lstrip('0') == b.lstrip('0'):
            return True
        return False

    try:
        from api.gudat_api import get_gudat_client
        center = _gudat_center_from_subsidiary(subsidiary or 1)
        client = get_gudat_client(center)
    except Exception as e:
        logger.debug("Gudat-Client für Dossier-Check nicht verfügbar: %s", e)
        return False

    query_tasks = """
    query GetWorkshopTasks($page: Int!, $itemsPerPage: Int!, $where: QueryWorkshopTasksWhereWhereConditions) {
      workshopTasks(first: $itemsPerPage, page: $page, where: $where) {
        data {
          id
          dossier { id, orders { number } }
        }
      }
    }
    """
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    try:
        headers['X-XSRF-TOKEN'] = client._get_xsrf()
    except Exception:
        pass

    # 1) Heute
    variables = {
        "page": 1,
        "itemsPerPage": 200,
        "where": {"AND": [{"column": "START_DATE", "operator": "EQ", "value": date.today().isoformat()}]}
    }
    try:
        r = client.session.post(
            f"{client.BASE_URL}/graphql",
            json={"operationName": "GetWorkshopTasks", "query": query_tasks, "variables": variables},
            headers=headers
        )
        data = r.json()
        if 'errors' not in data:
            for task in (data.get('data') or {}).get('workshopTasks', {}).get('data', []) or []:
                for order in (task.get('dossier') or {}).get('orders', []) or []:
                    if order_match(order.get('number'), order_number):
                        return True
    except Exception as e:
        logger.debug("Gudat workshopTasks (heute) für Auftrag %s: %s", order_number, e)

    # 2) 90 Tage zurück + 30 vor (max 5 Seiten)
    start_date = (date.today() - timedelta(days=90)).isoformat()
    end_date = (date.today() + timedelta(days=30)).isoformat()
    for page in range(1, 6):
        variables = {
            "page": page,
            "itemsPerPage": 200,
            "where": {
                "AND": [
                    {"column": "START_DATE", "operator": "GTE", "value": start_date},
                    {"column": "START_DATE", "operator": "LTE", "value": end_date}
                ]
            }
        }
        try:
            r = client.session.post(
                f"{client.BASE_URL}/graphql",
                json={"operationName": "GetWorkshopTasks", "query": query_tasks, "variables": variables},
                headers=headers
            )
            data = r.json()
            if 'errors' in data:
                break
            tasks = (data.get('data') or {}).get('workshopTasks', {}).get('data', []) or []
            if not tasks:
                break
            for task in tasks:
                for order in (task.get('dossier') or {}).get('orders', []) or []:
                    if order_match(order.get('number'), order_number):
                        return True
        except Exception as e:
            logger.debug("Gudat workshopTasks (Range) für Auftrag %s: %s", order_number, e)

    # 3) Fallback: Appointments (Dossier z. B. „abgeholt“ – Tasks nicht mehr in workshopTasks)
    try:
        first_per_page = 200
        query_apt_inline = (
            """
        query GetAppointmentsByDate {
          appointments(first: %d, page: %d, where: {
            AND: [
              {column: START_DATE_TIME, operator: GTE, value: "%s"},
              {column: START_DATE_TIME, operator: LTE, value: "%s"}
            ]
          }) {
            data {
              id
              dossier { id, orders { number } }
            }
          }
        }
        """
        )
        for page in range(1, 51):
            query_apt = query_apt_inline % (first_per_page, page, start_date, end_date)
            r = client.session.post(
                f"{client.BASE_URL}/graphql",
                json={"operationName": "GetAppointmentsByDate", "query": query_apt},
                headers=headers,
            )
            apt_data = r.json()
            if apt_data.get('errors'):
                break
            appointments = (apt_data.get('data') or {}).get('appointments', {}).get('data', []) or []
            if not appointments:
                break
            for apt in appointments:
                for order in (apt.get('dossier') or {}).get('orders', []) or []:
                    if order_match(order.get('number'), order_number):
                        return True
            if len(appointments) < first_per_page:
                break
    except Exception as e:
        logger.debug("Gudat Appointments-Fallback für Auftrag %s: %s", order_number, e)

    return False

bp = Blueprint('garantie_auftraege_api', __name__, url_prefix='/api/garantie/auftraege')


def get_garantieakte_metadata(order_number: int, kunde_name: str, subsidiary: int = None) -> dict:
    """
    Prüft ob Garantieakte existiert und holt Metadaten.
    
    Args:
        order_number: Auftragsnummer
        kunde_name: Name des Kunden
        subsidiary: Subsidiary (1=Stellantis, 2=Hyundai, 3=Stellantis Landau) - TAG 189
    
    Returns:
        {
            'existiert': bool,
            'erstelldatum': str oder None,
            'ersteller': str oder None,
            'ordner_path': str oder None,
            'windows_path': str oder None
        }
    """
    from api.garantieakte_workflow import BRAND_PATHS, sanitize_filename
    
    # Brand-Erkennung aus subsidiary (TAG 189)
    brand = 'hyundai'  # Default
    if subsidiary == 1 or subsidiary == 3:
        brand = 'stellantis'  # Deggendorf Opel (1) oder Landau (3)
    elif subsidiary == 2:
        brand = 'hyundai'  # Deggendorf Hyundai (2)
    
    brand_config = BRAND_PATHS.get(brand, BRAND_PATHS['hyundai'])
    
    # Prüfe verschiedene Pfade für diese Marke
    base_path = None
    for path_option in brand_config['base_paths']:
        base_dir = os.path.dirname(path_option)
        if os.path.exists(base_dir):
            base_path = path_option
            break
    
    if not base_path:
        base_path = brand_config['fallback']
    
    # Ordner-Name
    kunde_clean = sanitize_filename(kunde_name)
    ordner_name = f"{kunde_clean}_{order_number}"
    ordner_path = os.path.join(base_path, ordner_name)
    
    if not os.path.exists(ordner_path):
        return {
            'existiert': False,
            'erstelldatum': None,
            'ersteller': None,
            'ordner_path': None,
            'windows_path': None
        }
    
    # Windows-Pfad generieren (TAG 189: Brand-spezifisch, None-Check hinzugefügt)
    windows_path = None
    if ordner_path:  # None-Check
        windows_base = brand_config['windows_base']
        
        if f'/{brand}-garantie' in ordner_path:
            # Separater Mount
            mount_name = f'{brand}-garantie'
            windows_path = ordner_path.replace(f'/mnt/{mount_name}', windows_base)
            windows_path = windows_path.replace('/', '\\')
        elif '/buchhaltung/DigitalesAutohaus' in ordner_path:
            # Über buchhaltung Mount
            windows_path = ordner_path.replace('/mnt/buchhaltung/DigitalesAutohaus', r'\\srvrdb01\Allgemein\DigitalesAutohaus')
            windows_path = windows_path.replace('/', '\\')
        elif '/DigitalesAutohaus' in ordner_path:
            # Direkt gemountet
            windows_path = ordner_path.replace('/mnt/DigitalesAutohaus', r'\\srvrdb01\Allgemein\DigitalesAutohaus')
            windows_path = windows_path.replace('/', '\\')
        elif '/greiner-portal-sync' in ordner_path:
            # Fallback
            windows_path = ordner_path.replace('/mnt/greiner-portal-sync', r'\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server')
            windows_path = windows_path.replace('/', '\\')
        else:
            windows_path = ordner_path.replace('/', '\\') if ordner_path else None
    
    # Prüfe Metadaten-Datei
    metadata_file = os.path.join(ordner_path, '.metadata.json')
    
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                return {
                    'existiert': True,
                    'erstelldatum': metadata.get('erstelldatum'),
                    'ersteller': metadata.get('ersteller'),
                    'ordner_path': ordner_path,
                    'windows_path': windows_path
                }
        except Exception as e:
            logger.warning(f"Fehler beim Lesen der Metadaten für Auftrag {order_number}: {e}")
    
    # Fallback: Verwende Ordner-Erstellungsdatum
    try:
        erstelldatum = datetime.fromtimestamp(os.path.getctime(ordner_path)).strftime('%Y-%m-%d %H:%M:%S')
        return {
            'existiert': True,
            'erstelldatum': erstelldatum,
            'ersteller': None,  # Nicht verfügbar
            'ordner_path': ordner_path,
            'windows_path': windows_path
        }
    except Exception as e:
        logger.warning(f"Fehler beim Lesen des Ordner-Datums für Auftrag {order_number}: {e}")
        return {
            'existiert': True,
            'erstelldatum': None,
            'ersteller': None,
            'ordner_path': ordner_path,
            'windows_path': windows_path
        }


def save_garantieakte_metadata(order_number: int, ordner_path: str, ersteller: str):
    """
    Speichert Metadaten der Garantieakte.
    """
    metadata_file = os.path.join(ordner_path, '.metadata.json')
    
    metadata = {
        'order_number': order_number,
        'erstelldatum': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ersteller': ersteller
    }
    
    try:
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"Metadaten gespeichert: {metadata_file}")
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Metadaten: {e}")


@bp.route('/offen', methods=['GET'])
@login_required
def get_offene_garantieauftraege():
    """
    Holt alle offenen Garantieaufträge mit Garantieakte-Status.
    
    Query-Parameter:
        - marke: Filter nach Marke ('opel', 'hyundai', 'alle') - default: 'alle'
        - fertig: Filter nach fertigen Aufträgen ('true'/'false') - default: 'false'
        - max_tage: Nur Aufträge der letzten N Tage (0 = alle) - default: 0
    
    Returns:
        Liste von Aufträgen mit:
        - Auftragsdaten (Nummer, Kunde, Fahrzeug, etc.)
        - Garantieakte-Status (existiert, erstelldatum, ersteller)
    """
    try:
        from flask import request
        marke_filter = request.args.get('marke', 'alle').lower()
        fertig_filter = request.args.get('fertig', 'false').lower() == 'true'
        max_tage = request.args.get('max_tage', '0', type=lambda x: int(x) if str(x).isdigit() else 0)
        
        # Betriebs-Filter basierend auf Marke
        # Opel = Betrieb 1 (Deggendorf Opel) + 3 (Landau Opel)
        # Hyundai = Betrieb 2 (Deggendorf Hyundai)
        if marke_filter == 'opel':
            betriebe_filter = [1, 3]
        elif marke_filter == 'hyundai':
            betriebe_filter = [2]
        else:
            betriebe_filter = [1, 2, 3]  # Alle
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Offene Garantieaufträge finden
            # Garantie = charge_type 60 ODER labour_type G/GS ODER invoice_type 6
            # Nur Aufträge die bereits bearbeitet werden (Stempelzeiten ODER zugeordnete Positionen)
            query = """
                WITH garantie_auftraege AS (
                    SELECT DISTINCT
                        o.number as auftrag_nr,
                        o.subsidiary as betrieb,
                        o.order_date,
                        o.estimated_inbound_time as termin_bringen,
                        o.clearing_delay_type,
                        o.has_open_positions,
                        o.order_taking_employee_no as sb_nr,
                        sb.name as sb_name,
                        v.license_plate as kennzeichen,
                        m.description as marke,
                        mo.description as modell,
                        COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name) as kunde,
                        cs.customer_number as kunden_nr,
                        -- Prüfe ob Garantie-Auftrag
                        CASE 
                            WHEN EXISTS (
                                SELECT 1 FROM labours l 
                                WHERE l.order_number = o.number 
                                  AND (l.charge_type = 60 OR l.labour_type IN ('G', 'GS'))
                            ) THEN true
                            WHEN EXISTS (
                                SELECT 1 FROM invoices i 
                                WHERE i.order_number = o.number 
                                  AND i.invoice_type = 6 
                                  AND i.is_canceled = false
                            ) THEN true
                            ELSE false
                        END as ist_garantie,
                        -- Prüfe ob Auftrag bereits bearbeitet wird
                        CASE 
                            WHEN EXISTS (
                                SELECT 1 FROM times t 
                                WHERE t.order_number = o.number 
                                  AND t.type = 2
                            ) THEN true
                            WHEN EXISTS (
                                SELECT 1 FROM labours l 
                                WHERE l.order_number = o.number 
                                  AND l.mechanic_no IS NOT NULL
                            ) THEN true
                            ELSE false
                        END as wird_bearbeitet
                    FROM orders o
                    LEFT JOIN employees_history sb ON o.order_taking_employee_no = sb.employee_number
                        AND sb.is_latest_record = true
                    LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
                    LEFT JOIN makes m ON v.make_number = m.make_number
                    LEFT JOIN models mo ON v.make_number = mo.make_number AND v.model_code = mo.model_code
                    LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
                    WHERE o.has_open_positions = true
                ),
                -- Summen pro Auftrag
                auftrag_summen AS (
                    SELECT
                        l.order_number,
                        SUM(l.time_units) as total_aw,
                        SUM(CASE WHEN NOT l.is_invoiced THEN l.time_units ELSE 0 END) as offen_aw
                    FROM labours l
                    WHERE l.order_number IN (SELECT auftrag_nr FROM garantie_auftraege)
                    GROUP BY l.order_number
                ),
                -- Stempelzeiten pro Auftrag (DEDUPLIZIERT - wie in anderen Queries)
                stempel_summen AS (
                    SELECT
                        order_number,
                        SUM(minuten) as gestempelt_min
                    FROM (
                        SELECT DISTINCT ON (order_number, employee_number, start_time, end_time)
                            order_number,
                            EXTRACT(EPOCH FROM (COALESCE(end_time, NOW()) - start_time)) / 60 as minuten
                        FROM times
                        WHERE type = 2
                          AND order_number IN (SELECT auftrag_nr FROM garantie_auftraege)
                        ORDER BY order_number, employee_number, start_time, end_time
                    ) dedup
                    GROUP BY order_number
                ),
                teile_offen AS (
                    SELECT order_number, COUNT(*)::int as anzahl_offen
                    FROM parts p
                    WHERE p.order_number IN (SELECT auftrag_nr FROM garantie_auftraege)
                      AND (p.is_invoiced = false OR p.is_invoiced IS NULL)
                    GROUP BY order_number
                )
                SELECT
                    g.auftrag_nr,
                    g.betrieb,
                    g.order_date,
                    g.termin_bringen,
                    g.clearing_delay_type,
                    COALESCE(te.anzahl_offen, 0) as teile_offen_anzahl,
                    (CURRENT_DATE - (g.order_date::date))::int as tage_offen,
                    g.sb_name,
                    g.kennzeichen,
                    g.marke,
                    g.modell,
                    g.kunde,
                    g.kunden_nr,
                    COALESCE(s.total_aw, 0) as total_aw,
                    COALESCE(s.offen_aw, 0) as offen_aw,
                    CASE 
                        WHEN st.gestempelt_min IS NULL THEN 0.0
                        ELSE st.gestempelt_min / 6.0
                    END as gestempelt_aw
                FROM garantie_auftraege g
                LEFT JOIN auftrag_summen s ON g.auftrag_nr = s.order_number
                LEFT JOIN stempel_summen st ON g.auftrag_nr = st.order_number
                LEFT JOIN teile_offen te ON g.auftrag_nr = te.order_number
                WHERE g.ist_garantie = true
                  AND g.wird_bearbeitet = true
            """
            
            # Filter nach Betrieb hinzufügen
            if betriebe_filter:
                placeholders = ','.join(['%s'] * len(betriebe_filter))
                query += f" AND g.betrieb IN ({placeholders})"
            
            # Filter nach "fertig" hinzufügen (komplett gestempelt = gestempelt_aw >= total_aw)
            if fertig_filter:
                query += """ AND CASE 
                        WHEN st.gestempelt_min IS NULL THEN 0.0
                        ELSE st.gestempelt_min / 6.0
                    END >= COALESCE(s.total_aw, 0) * 0.95"""
            
            # Optional: nur Aufträge der letzten N Tage (reduziert „alte“ Einträge)
            params_list = list(betriebe_filter) if betriebe_filter else []
            if max_tage and max_tage > 0:
                query += " AND g.order_date >= CURRENT_DATE - INTERVAL '1 day' * %s"
                params_list.append(max_tage)
            
            query += " ORDER BY g.order_date DESC"
            
            if params_list:
                cursor.execute(query, params_list)
            else:
                cursor.execute(query)
            auftraege = cursor.fetchall()
            
            # Gudat-Dossier-Status: einmal pro Center alle Auftragsnummern holen (Batch), dann Lookup
            centers = set()
            for auftrag in auftraege:
                betrieb = auftrag.get('betrieb')
                centers.add(_gudat_center_from_subsidiary(betrieb or 1))
            gudat_sets = {}
            for c in centers:
                gudat_sets[c] = _gudat_auftragsnummern_mit_dossier(c)
            
            result = []
            for auftrag in auftraege:
                auftrag_nr = auftrag['auftrag_nr']
                kunde = auftrag['kunde'] or f'Kunde_{auftrag_nr}'
                betrieb = auftrag.get('betrieb')
                center = _gudat_center_from_subsidiary(betrieb or 1)
                gudat = gudat_sets.get(center, {"order_numbers": set(), "license_plates": set()})
                nr_norm = _normalize_order_num(auftrag_nr)
                nr_raw = str(auftrag_nr).strip()
                kz_norm = _normalize_kennzeichen(auftrag.get("kennzeichen"))
                order_ok = nr_norm in gudat.get("order_numbers", set()) or nr_raw in gudat.get("order_numbers", set())
                lp_ok = kz_norm and kz_norm in gudat.get("license_plates", set())
                gudat_dossier_gefunden = order_ok or lp_ok

                akte_info = get_garantieakte_metadata(auftrag_nr, kunde, betrieb)

                termin_ts = auftrag.get('termin_bringen')
                eintrag = {
                    'auftrag_nr': auftrag_nr,
                    'betrieb': auftrag['betrieb'],
                    'betrieb_name': BETRIEB_NAMEN.get(auftrag['betrieb'], 'Unbekannt'),
                    'order_date': auftrag['order_date'].strftime('%Y-%m-%d') if auftrag['order_date'] else None,
                    'tage_offen': int(auftrag.get('tage_offen') or 0),
                    'termin_bringen': termin_ts.strftime('%Y-%m-%d %H:%M') if termin_ts else None,
                    'clearing_delay_type': auftrag.get('clearing_delay_type'),
                    'teile_offen_anzahl': int(auftrag.get('teile_offen_anzahl') or 0),
                    'gudat_dossier_gefunden': gudat_dossier_gefunden,
                    'serviceberater': auftrag['sb_name'],
                    'kennzeichen': auftrag['kennzeichen'],
                    'marke': auftrag['marke'],
                    'modell': auftrag['modell'],
                    'kunde': auftrag['kunde'],
                    'total_aw': float(auftrag['total_aw'] or 0),
                    'offen_aw': float(auftrag['offen_aw'] or 0),
                    'gestempelt_aw': float(auftrag.get('gestempelt_aw', 0) or 0),
                    'garantieakte': {
                        'existiert': akte_info['existiert'],
                        'erstelldatum': akte_info['erstelldatum'],
                        'ersteller': akte_info['ersteller'],
                        'windows_path': akte_info.get('windows_path')
                    }
                }

                # Hintergrund-Precheck (Frist + Empfehlung) aus Cache laden; falls leer: Vorprüfung direkt berechnen
                try:
                    from api.garantie_precheck_service import get_cached_precheck, run_precheck_for_auftrag
                    precheck = get_cached_precheck(auftrag_nr)
                    if not precheck:
                        precheck = run_precheck_for_auftrag(eintrag, with_ai=False)
                    eintrag['precheck'] = precheck
                except Exception as pre_err:
                    logger.debug("Precheck für Auftrag %s nicht verfügbar: %s", auftrag_nr, pre_err)

                result.append(eintrag)
            
            return jsonify({
                'success': True,
                'auftraege': result,
                'anzahl': len(result),
                'filter': {
                    'marke': marke_filter,
                    'betriebe': betriebe_filter,
                    'fertig': fertig_filter,
                    'max_tage': max_tage
                }
            })
            
    except Exception as e:
        logger.error(f"Fehler beim Laden der Garantieaufträge: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/debug/<int:order_number>', methods=['GET'])
@login_required
def debug_garantieauftrag(order_number):
    """
    Debug-Endpoint: Prüft warum ein Garantieauftrag nicht angezeigt wird.
    """
    try:
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    o.number,
                    o.has_open_positions,
                    o.subsidiary,
                    o.order_date,
                    -- Prüfe ob Garantie-Auftrag
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM labours l 
                            WHERE l.order_number = o.number 
                              AND (l.charge_type = 60 OR l.labour_type IN ('G', 'GS'))
                        ) THEN true
                        WHEN EXISTS (
                            SELECT 1 FROM invoices i 
                            WHERE i.order_number = o.number 
                              AND i.invoice_type = 6 
                              AND i.is_canceled = false
                        ) THEN true
                        ELSE false
                    END as ist_garantie,
                    -- Prüfe ob Auftrag bereits bearbeitet wird
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM times t 
                            WHERE t.order_number = o.number 
                              AND t.type = 2
                        ) THEN true
                        WHEN EXISTS (
                            SELECT 1 FROM labours l 
                            WHERE l.order_number = o.number 
                              AND l.mechanic_no IS NOT NULL
                        ) THEN true
                        ELSE false
                    END as wird_bearbeitet,
                    -- Details
                    (SELECT COUNT(*) FROM labours l WHERE l.order_number = o.number AND (l.charge_type = 60 OR l.labour_type IN ('G', 'GS'))) as garantie_labours,
                    (SELECT COUNT(*) FROM invoices i WHERE i.order_number = o.number AND i.invoice_type = 6 AND i.is_canceled = false) as garantie_invoices,
                    -- TAG 211: Deduplizierte Anzahl - sekundengleiche Stempelzeiten desselben Mechanikers auf demselben Auftrag nur einmal
                    (SELECT COUNT(DISTINCT (t.employee_number, t.order_number, t.start_time, t.end_time)) 
                     FROM times t 
                     WHERE t.order_number = o.number AND t.type = 2 AND t.end_time IS NOT NULL) as stempelzeiten_count,
                    (SELECT COUNT(*) FROM labours l WHERE l.order_number = o.number AND l.mechanic_no IS NOT NULL) as zugeordnete_positionen_count
                FROM orders o
                WHERE o.number = %s
            """
            
            cursor.execute(query, (order_number,))
            auftrag = cursor.fetchone()
            
            if not auftrag:
                return jsonify({
                    'success': False,
                    'error': f'Auftrag {order_number} nicht gefunden'
                }), 404
            
            # Prüfe Filter-Bedingungen
            wird_angezeigt = (
                auftrag['has_open_positions'] and 
                auftrag['ist_garantie'] and 
                auftrag['wird_bearbeitet']
            )
            
            # Identifiziere Gründe, warum nicht angezeigt
            gruende = []
            if not auftrag['has_open_positions']:
                gruende.append('Auftrag hat keine offenen Positionen mehr (alle abgeschlossen)')
            if not auftrag['ist_garantie']:
                gruende.append('Auftrag ist nicht als Garantie erkannt (keine charge_type 60, labour_type G/GS, oder invoice_type 6)')
            if not auftrag['wird_bearbeitet']:
                gruende.append('Auftrag wird nicht bearbeitet (keine Stempelzeiten und keine zugeordneten Positionen)')
            
            return jsonify({
                'success': True,
                'auftrag': {
                    'number': auftrag['number'],
                    'subsidiary': auftrag['subsidiary'],
                    'order_date': auftrag['order_date'].strftime('%Y-%m-%d') if auftrag['order_date'] else None,
                    'has_open_positions': auftrag['has_open_positions'],
                    'ist_garantie': auftrag['ist_garantie'],
                    'wird_bearbeitet': auftrag['wird_bearbeitet'],
                    'details': {
                        'garantie_labours': auftrag['garantie_labours'],
                        'garantie_invoices': auftrag['garantie_invoices'],
                        'stempelzeiten_count': auftrag['stempelzeiten_count'],
                        'zugeordnete_positionen_count': auftrag['zugeordnete_positionen_count']
                    }
                },
                'wird_angezeigt': wird_angezeigt,
                'gruende_nicht_angezeigt': gruende if not wird_angezeigt else []
            })
            
    except Exception as e:
        logger.error(f"Fehler beim Debug von Auftrag {order_number}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
