"""
Arbeitskarte API
================
TAG 173: API-Endpoints für Arbeitskarte-Daten und PDF-Generierung
"""

from flask import Blueprint, jsonify, send_file, request
from flask_login import login_required
from decorators.auth_decorators import login_required
import sys
import os
import json
import logging
from io import BytesIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.locosoft_helpers import get_locosoft_connection
from tools.gudat_client import GudatClient
from api.arbeitskarte_pdf import generate_arbeitskarte_pdf

# Gudat Center aus Standort: 1/2 = Deggendorf, 3 = Landau (KIC pro Center)
def _gudat_center_from_subsidiary(subsidiary):
    return 'landau' if subsidiary == 3 else 'deggendorf'

bp = Blueprint('arbeitskarte', __name__, url_prefix='/api/arbeitskarte')
logger = logging.getLogger(__name__)

GUDAT_CONFIG = {
    'username': 'florian.greiner@auto-greiner.de',
    'password': 'Hyundai2025!'
}


def hole_arbeitskarte_daten(order_number: int):
    """Holt alle Daten für die Arbeitskarte aus Locosoft + GUDAT"""
    # Locosoft-Daten
    conn = get_locosoft_connection()
    cursor = conn.cursor()
    
    # Auftragsdaten (TAG 189: subsidiary hinzugefügt für Brand-Erkennung)
    # TAG 212: order_mileage hinzugefügt (Kilometerstand zum Zeitpunkt des Auftrags)
    cursor.execute("""
        SELECT 
            o.number,
            o.order_date,
            o.order_taking_employee_no,
            eh_sb.name as serviceberater,
            o.vehicle_number,
            o.order_customer,
            o.subsidiary,
            o.order_mileage
        FROM orders o
        LEFT JOIN employees_history eh_sb ON o.order_taking_employee_no = eh_sb.employee_number 
            AND eh_sb.is_latest_record = true
        WHERE o.number = %s
    """, [order_number])
    
    auftrag = cursor.fetchone()
    if not auftrag:
        conn.close()
        return None
    
    # Kundendaten (TAG 189: COALESCE für besseren Fallback wie in locosoft_helpers.py)
    cursor.execute("""
        SELECT 
            COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name, cs.first_name) as kunde_name,
            cs.family_name,
            cs.first_name,
            cs.home_street,
            cs.zip_code,
            cs.home_city
        FROM customers_suppliers cs
        WHERE cs.customer_number = %s
    """, [auftrag[5]])
    
    kunde = cursor.fetchone()
    
    # TAG 189: Debug-Logging für Kundenname
    if not kunde:
        logger.warning(f"⚠️ Kein Kunde gefunden für customer_number={auftrag[5]} (Auftrag {order_number})")
    else:
        kunde_name_db = kunde[0]  # COALESCE-Ergebnis
        logger.info(f"Kunde gefunden: kunde_name='{kunde_name_db}', family_name='{kunde[1]}', first_name='{kunde[2]}' (Auftrag {order_number})")
    
    # Kontaktdaten
    cursor.execute("""
        SELECT 
            ccn.phone_number,
            ccn.com_type
        FROM customer_com_numbers ccn
        WHERE ccn.customer_number = %s
        ORDER BY ccn.com_type
    """, [auftrag[5]])
    
    kontakt_daten = cursor.fetchall()
    telefon = None
    email = None
    for kontakt in kontakt_daten:
        nummer = kontakt[0]
        typ = kontakt[1] or ''
        if nummer:
            if 'phone' in typ.lower() or 'telefon' in typ.lower() or not email:
                telefon = nummer
            elif 'email' in typ.lower() or 'mail' in typ.lower() or '@' in nummer:
                email = nummer
    
    # Fahrzeugdaten
    # TAG 212: Verwende order_mileage falls vorhanden, sonst vehicles.mileage_km (Kilometerstand zum Zeitpunkt des Auftrags)
    cursor.execute("""
        SELECT 
            v.license_plate,
            v.vin,
            v.first_registration_date,
            COALESCE(o.order_mileage, v.mileage_km) as mileage_km,
            m.description as marke,
            mo.description as modell
        FROM vehicles v
        LEFT JOIN makes m ON v.make_number = m.make_number
        LEFT JOIN models mo ON v.make_number = mo.make_number AND v.model_code = mo.model_code
        LEFT JOIN orders o ON o.vehicle_number = v.internal_number AND o.number = %s
        WHERE v.internal_number = %s
    """, [order_number, auftrag[4]])
    
    fahrzeug = cursor.fetchone()
    
    # Arbeitspositionen
    cursor.execute("""
        SELECT 
            l.order_position,
            l.labour_operation_id,
            l.text_line,
            l.time_units,
            l.mechanic_no,
            eh_mech.name as mechaniker,
            l.is_invoiced,
            l.invoice_type
        FROM labours l
        LEFT JOIN employees_history eh_mech ON l.mechanic_no = eh_mech.employee_number 
            AND eh_mech.is_latest_record = true
        WHERE l.order_number = %s
        ORDER BY l.order_position, l.order_position_line
    """, [order_number])
    
    positionen = cursor.fetchall()
    
    # Stempelzeiten (DEDUPLIZIERT - sekundengleiche Stempelzeiten desselben Mechanikers auf demselben Auftrag nur einmal)
    cursor.execute("""
        SELECT DISTINCT ON (t.employee_number, t.order_number, t.start_time, t.end_time)
            t.employee_number,
            eh.name as mechaniker,
            t.start_time,
            t.end_time,
            t.duration_minutes,
            t.type
        FROM times t
        LEFT JOIN employees_history eh ON t.employee_number = eh.employee_number 
            AND eh.is_latest_record = true
        WHERE t.order_number = %s
          AND t.type = 2
          AND t.end_time IS NOT NULL
        ORDER BY t.employee_number, t.order_number, t.start_time, t.end_time, t.duration_minutes DESC
    """, [order_number])
    
    stempelzeiten = cursor.fetchall()
    
    # Job-Beschreibung aus Auftrag holen (erste Position mit text_line)
    cursor.execute("""
        SELECT l.text_line 
        FROM labours l 
        WHERE l.order_number = %s 
          AND l.text_line IS NOT NULL 
          AND l.text_line != ''
        ORDER BY l.order_position, l.order_position_line
        LIMIT 1
    """, [order_number])
    
    job_beschreibung_row = cursor.fetchone()
    job_beschreibung = job_beschreibung_row[0] if job_beschreibung_row and job_beschreibung_row[0] else None
    
    # Teile
    cursor.execute("""
        SELECT 
            p.part_number,
            pm.description,
            p.amount,
            p.sum,
            p.is_invoiced,
            p.invoice_type
        FROM parts p
        LEFT JOIN parts_master pm ON p.part_number = pm.part_number
        WHERE p.order_number = %s
        ORDER BY p.order_position
    """, [order_number])
    
    teile = cursor.fetchall()
    
    # Standort für Gudat-Center (vor conn.close): 1/2 = Deggendorf, 3 = Landau
    subsidiary = auftrag[6] if len(auftrag) > 6 else 1
    conn.close()
    
    # GUDAT-Daten (KIC pro Center – Landau seit 2026-03 über gudat.centers.landau)
    gudat_daten = None
    try:
        client = None
        try:
            from api.gudat_api import get_gudat_client
            center = _gudat_center_from_subsidiary(subsidiary)
            client = get_gudat_client(center)
        except Exception as e:
            logger.warning("Gudat get_gudat_client(center) fehlgeschlagen, Fallback Deggendorf: %s", e)
            client = GudatClient(GUDAT_CONFIG['username'], GUDAT_CONFIG['password'])
            if not client.login():
                client = None
        if client:
            from datetime import date, timedelta
            
            # TAG 192: Erweiterte Suche - nicht nur heute, sondern auch letzte 90 Tage
            # Hole Auftragsdatum aus Locosoft-Daten für präzisere Suche
            order_date = None
            if 'locosoft' in locals() and locosoft_daten and 'auftrag' in locosoft_daten:
                order_date = locosoft_daten['auftrag'].get('datum')
                if order_date:
                    if isinstance(order_date, str):
                        from datetime import datetime
                        try:
                            if ' ' in order_date:
                                order_date = datetime.strptime(order_date.split()[0], '%Y-%m-%d').date()
                            elif 'T' in order_date:
                                order_date = datetime.fromisoformat(order_date.split('T')[0]).date()
                            else:
                                order_date = datetime.fromisoformat(order_date).date()
                        except:
                            order_date = None
            
            query_tasks = """
            query GetWorkshopTasks($page: Int!, $itemsPerPage: Int!, $where: QueryWorkshopTasksWhereWhereConditions) {
              workshopTasks(first: $itemsPerPage, page: $page, where: $where) {
                data {
                  id
                  description
                  dossier {
                    id
                    orders { number }
                  }
                }
              }
            }
            """
            
            dossier_id = None
            
            # 1. Versuche zuerst heute (schnellste Suche)
            target_date = date.today().isoformat()
            variables = {
                "page": 1,
                "itemsPerPage": 200,
                "where": {
                    "AND": [{"column": "START_DATE", "operator": "EQ", "value": target_date}]
                }
            }
            
            response = client.session.post(
                f"{client.BASE_URL}/graphql",
                json={"operationName": "GetWorkshopTasks", "query": query_tasks, "variables": variables},
                headers={
                    'Accept': 'application/json',
                    'X-XSRF-TOKEN': client._get_xsrf(),
                    'Content-Type': 'application/json'
                }
            )
            
            data = response.json()
            
            if 'errors' not in data:
                tasks = data.get('data', {}).get('workshopTasks', {}).get('data', [])
                
                # Finde dossier_id - erweiterte Vergleichslogik (TAG 192)
                dossier_id = None
                for task in tasks:
                    orders = task.get('dossier', {}).get('orders', [])
                    for order in orders:
                        order_num = order.get('number')
                        order_num_str = str(order_num).strip() if order_num else ""
                        order_number_str = str(order_number).strip()
                        # Vergleich: String, Integer, mit/ohne führende Nullen
                        match = False
                        if order_num_str == order_number_str:
                            match = True
                        elif order_num and str(order_num).isdigit() and str(order_number).isdigit():
                            if int(order_num) == int(order_number):
                                match = True
                            elif order_num_str.lstrip('0') == order_number_str.lstrip('0'):
                                match = True
                        if match:
                            dossier_id = task.get('dossier', {}).get('id')
                            logger.info(f"✅ Dossier gefunden für Auftrag {order_number}: dossier_id={dossier_id}")
                            break
                    if dossier_id:
                        break
                
                # TAG 192: Falls nicht heute gefunden, suche in letzten 90 Tagen + 30 Tage Zukunft (geplante Tasks)
                if not dossier_id:
                    logger.info(f"Dossier für Auftrag {order_number} nicht heute gefunden, suche in letzten 90 Tagen + 30 Tage Zukunft...")
                    start_date = (date.today() - timedelta(days=90)).isoformat()
                    end_date = (date.today() + timedelta(days=30)).isoformat()
                    
                    # Pagination - mehrere Requests
                    max_pages = 10  # Max 10 Seiten = 2000 Tasks
                    for page in range(1, max_pages + 1):
                        variables_range = {
                            "page": page,
                            "itemsPerPage": 200,
                            "where": {
                                "AND": [
                                    {"column": "START_DATE", "operator": "GTE", "value": start_date},
                                    {"column": "START_DATE", "operator": "LTE", "value": end_date}
                                ]
                            }
                        }
                        
                        response = client.session.post(
                            f"{client.BASE_URL}/graphql",
                            json={"operationName": "GetWorkshopTasks", "query": query_tasks, "variables": variables_range},
                            headers={
                                'Accept': 'application/json',
                                'X-XSRF-TOKEN': client._get_xsrf(),
                                'Content-Type': 'application/json'
                            }
                        )
                        
                        data = response.json()
                        if 'errors' in data:
                            logger.warning(f"GraphQL-Fehler bei erweiterter Suche (Seite {page}): {data.get('errors')}")
                            break
                        
                        tasks = data.get('data', {}).get('workshopTasks', {}).get('data', [])
                        if not tasks:
                            break  # Keine weiteren Tasks
                        
                        # Finde dossier_id
                        for task in tasks:
                            orders = task.get('dossier', {}).get('orders', [])
                            for order in orders:
                                order_num = order.get('number')
                                order_num_str = str(order_num).strip() if order_num else ""
                                order_number_str = str(order_number).strip()
                                match = False
                                if order_num_str == order_number_str:
                                    match = True
                                elif order_num and str(order_num).isdigit() and str(order_number).isdigit():
                                    if int(order_num) == int(order_number):
                                        match = True
                                    elif order_num_str.lstrip('0') == order_number_str.lstrip('0'):
                                        match = True
                                if match:
                                    dossier_id = task.get('dossier', {}).get('id')
                                    logger.info(f"✅ Dossier gefunden für Auftrag {order_number}: dossier_id={dossier_id} (Seite {page})")
                                    break
                            if dossier_id:
                                break
                        if dossier_id:
                            break
                
                # Fallback: Suche via Appointments (Auftrag kann nur als Termin in Gudat sein, ohne WorkshopTask mit START_DATE)
                if not dossier_id:
                    logger.info(f"Dossier für Auftrag {order_number} nicht in workshopTasks gefunden, suche in Appointments...")
                    start_date = (date.today() - timedelta(days=90)).isoformat()
                    end_date = (date.today() + timedelta(days=30)).isoformat()
                    order_number_str = str(order_number).strip()
                    # Gudat erlaubt max 200 pro Request ("Maximum number of 200 requested items exceeded")
                    first_per_page = 200
                    query_appointments_inline = (
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
                          dossier {
                            id
                            orders { number }
                          }
                        }
                      }
                    }
                    """
                    )
                    try:
                        all_appointments = []
                        for page in range(1, 51):  # max 50 Seiten = 10000 Termine (Gudat max 200/Request)
                            query_apt = query_appointments_inline % (first_per_page, page, start_date, end_date)
                            resp = client.session.post(
                                f"{client.BASE_URL}/graphql",
                                json={"operationName": "GetAppointmentsByDate", "query": query_apt},
                                headers={'Accept': 'application/json', 'X-XSRF-TOKEN': client._get_xsrf(), 'Content-Type': 'application/json'}
                            )
                            apt_data = resp.json()
                            if 'errors' in apt_data:
                                logger.warning(f"GraphQL-Fehler Appointments-Suche für Auftrag {order_number} (Seite {page}): {apt_data.get('errors')}")
                                break
                            appointments = apt_data.get('data', {}).get('appointments', {}).get('data', [])
                            if not isinstance(appointments, list):
                                break
                            if not appointments:
                                break
                            all_appointments.extend(appointments)
                            if len(appointments) < first_per_page:
                                break
                        if all_appointments and not apt_data.get('errors'):
                            logger.info(f"Appointments-Suche: {len(all_appointments)} Termine im Zeitraum {start_date} bis {end_date}")
                        for apt in all_appointments:
                                dossier = apt.get('dossier', {}) or {}
                                orders = dossier.get('orders', []) or []
                                for order in orders:
                                    order_num = order.get('number')
                                    if order_num is None:
                                        continue
                                    on_str = str(order_num).strip()
                                    match = (on_str == order_number_str or
                                             (str(order_num).isdigit() and str(order_number).isdigit() and int(order_num) == int(order_number)) or
                                             (on_str.lstrip('0') == order_number_str.lstrip('0')))
                                    if match:
                                        dossier_id = dossier.get('id')
                                        logger.info(f"✅ Dossier für Auftrag {order_number} via Appointments gefunden: dossier_id={dossier_id}")
                                        break
                                if dossier_id:
                                    break
                    except Exception as ex:
                        logger.warning(f"Appointments-Suche fehlgeschlagen für Auftrag {order_number}: {ex}")
                
                if dossier_id:
                    # Hole vollständige Dossier-Daten
                    # Versuche zuerst mit comments, falls das fehlschlägt, verwende nur note
                    # TAG 212: Erweitert um workshopTaskPackages (wie in GUDAT UI)
                    query_dossier = """
                    query GetDossierDrawerData($id: ID!) {
                      dossier(id: $id) {
                        id
                        note
                        orders {
                          id
                          number
                          note
                        }
                        states {
                          id
                          name
                        }
                        comments {
                          id
                          text
                          created_at
                          user {
                            id
                            name
                          }
                        }
                        workshopTasks(
                          where: {HAS: {relation: "workshopTaskPackage", amount: 0, operator: EQ, condition: {column: ID, operator: IS_NOT_NULL}}}
                        ) {
                          id
                          description
                          work_load
                          work_state
                          order {
                            id
                            number
                          }
                          comments {
                            id
                            text
                            created_at
                            user {
                              id
                              name
                            }
                          }
                        }
                        workshopTaskPackages {
                          id
                          workshopTasks {
                            id
                            description
                            work_load
                            work_state
                            order {
                              id
                              number
                            }
                            comments {
                              id
                              text
                              created_at
                              user {
                                id
                                name
                              }
                            }
                          }
                        }
                      }
                    }
                    """
                    
                    # Fallback-Query ohne comments (falls Schema nicht unterstützt)
                    # TAG 212: Erweitert um workshopTaskPackages
                    query_dossier_fallback = """
                    query GetDossierDrawerData($id: ID!) {
                      dossier(id: $id) {
                        id
                        note
                        orders {
                          id
                          number
                          note
                        }
                        states {
                          id
                          name
                        }
                        workshopTasks(
                          where: {HAS: {relation: "workshopTaskPackage", amount: 0, operator: EQ, condition: {column: ID, operator: IS_NOT_NULL}}}
                        ) {
                          id
                          description
                          work_load
                          work_state
                          order {
                            id
                            number
                          }
                        }
                        workshopTaskPackages {
                          id
                          workshopTasks {
                            id
                            description
                            work_load
                            work_state
                            order {
                              id
                              number
                            }
                          }
                        }
                      }
                    }
                    """
                    
                    # Fallback-Query ohne order-Feld auf Tasks (falls Schema das nicht unterstützt)
                    # TAG 212: Erweitert um workshopTaskPackages
                    query_dossier_fallback_no_order = """
                    query GetDossierDrawerData($id: ID!) {
                      dossier(id: $id) {
                        id
                        note
                        orders {
                          id
                          number
                          note
                        }
                        states {
                          id
                          name
                        }
                        workshopTasks(
                          where: {HAS: {relation: "workshopTaskPackage", amount: 0, operator: EQ, condition: {column: ID, operator: IS_NOT_NULL}}}
                        ) {
                          id
                          description
                          work_load
                          work_state
                        }
                        workshopTaskPackages {
                          id
                          workshopTasks {
                            id
                            description
                            work_load
                            work_state
                          }
                        }
                      }
                    }
                    """
                    
                    # Versuche zuerst mit comments
                    response = client.session.post(
                        f"{client.BASE_URL}/graphql",
                        json={"operationName": "GetDossierDrawerData", "query": query_dossier, "variables": {"id": str(dossier_id)}},
                        headers={
                            'Accept': 'application/json',
                            'X-XSRF-TOKEN': client._get_xsrf(),
                            'Content-Type': 'application/json'
                        }
                    )
                    
                    data = response.json()
                    use_fallback = False
                    use_fallback_no_order = False
                    
                    # Prüfe auf GraphQL-Fehler (z.B. wenn `order` oder `states` nicht verfügbar)
                    use_fallback_no_states = False
                    if 'errors' in data:
                        errors = data.get('errors', [])
                        error_messages = [str(err) for err in errors]
                        logger.warning(f"GraphQL-Fehler beim Holen von Dossier-Daten: {error_messages}")
                        states_field_error = any(
                            'states' in str(err).lower() or 'field "states"' in str(err) or
                            'Cannot query field "states"' in str(err) or 'Unknown field "states"' in str(err)
                            for err in errors
                        )
                        order_field_error = any(
                            'order' in str(err).lower() or 
                            'field "order"' in str(err) or 
                            'Cannot query field "order"' in str(err) or
                            'Unknown field "order"' in str(err)
                            for err in errors
                        )
                        if order_field_error:
                            logger.warning(f"GraphQL-Fehler: 'order' Feld auf workshopTask nicht verfügbar. Verwende Fallback ohne order-Feld.")
                            use_fallback_no_order = True
                        else:
                            use_fallback = True
                        if states_field_error:
                            use_fallback_no_states = True
                    
                    # Falls Fehler, versuche Fallback-Query ohne comments (und ggf. ohne order)
                    if use_fallback or use_fallback_no_order:
                        fallback_query = query_dossier_fallback_no_order if use_fallback_no_order else query_dossier_fallback
                        response = client.session.post(
                            f"{client.BASE_URL}/graphql",
                            json={"operationName": "GetDossierDrawerData", "query": fallback_query, "variables": {"id": str(dossier_id)}},
                            headers={
                                'Accept': 'application/json',
                                'X-XSRF-TOKEN': client._get_xsrf(),
                                'Content-Type': 'application/json'
                            }
                        )
                        data = response.json()
                        if 'errors' in data:
                            err_str = str(data['errors'])
                            if 'states' in err_str.lower() or use_fallback_no_states:
                                use_fallback_no_states = True
                            logger.error(f"GraphQL-Fehler auch bei Fallback-Query: {data['errors']}")
                        else:
                            use_fallback = True
                    
                    # Wenn Fehler wegen "states": ein letzter Versuch ohne states-Feld (TAG: Gudat-Vorgangsstatus)
                    if use_fallback_no_states and ('errors' in data or not data.get('data', {}).get('dossier')):
                        query_no_states = """
                        query GetDossierDrawerData($id: ID!) {
                          dossier(id: $id) {
                            id
                            note
                            orders { id number note }
                            comments { id text created_at user { id name } }
                            workshopTasks(where: {HAS: {relation: "workshopTaskPackage", amount: 0, operator: EQ, condition: {column: ID, operator: IS_NOT_NULL}}}) {
                              id description work_load work_state order { id number }
                              comments { id text created_at user { id name } }
                            }
                            workshopTaskPackages { id workshopTasks { id description work_load work_state order { id number } } }
                          }
                        }
                        """
                        try:
                            response = client.session.post(
                                f"{client.BASE_URL}/graphql",
                                json={"operationName": "GetDossierDrawerData", "query": query_no_states, "variables": {"id": str(dossier_id)}},
                                headers={'Accept': 'application/json', 'X-XSRF-TOKEN': client._get_xsrf(), 'Content-Type': 'application/json'}
                            )
                            data = response.json()
                            if 'errors' not in data and data.get('data', {}).get('dossier'):
                                dossier = data.get('data', {}).get('dossier')
                                dossier['states'] = []
                                data = {'data': {'dossier': dossier}}
                                logger.info("Dossier ohne states-Feld geladen (Gudat-API unterstützt states nicht).")
                        except Exception as ex:
                            logger.warning(f"Fallback ohne states fehlgeschlagen: {ex}")
                    
                    dossier = data.get('data', {}).get('dossier')
                    
                    if dossier:
                        # TAG 212: Hole Tasks aus beiden Quellen:
                        # 1. workshopTasks (ohne Package) - mit WHERE-Filter wie in GUDAT UI
                        # 2. workshopTaskPackages.workshopTasks (in Packages)
                        all_tasks = dossier.get('workshopTasks', [])
                        
                        # Hole auch Tasks aus Packages
                        packages = dossier.get('workshopTaskPackages', [])
                        for package in packages:
                            package_tasks = package.get('workshopTasks', [])
                            all_tasks.extend(package_tasks)
                        
                        logger.info(f"🔍 Dossier {dossier_id}: {len(dossier.get('workshopTasks', []))} Tasks ohne Package, {sum(len(p.get('workshopTasks', [])) for p in packages)} Tasks in Packages, gesamt: {len(all_tasks)} Tasks")
                        
                        # TAG 189: Filtere Tasks nach Locosoft-Auftragsnummer
                        # Ein GUDAT-Dossier kann mehrere Locosoft-Aufträge enthalten
                        # Jeder Task sollte nur zu einem Auftrag gehören
                        filtered_tasks = []
                        dossier_orders = dossier.get('orders', [])
                        
                        # Wenn order-Feld nicht verfügbar ist (use_fallback_no_order = True), übernehme alle Tasks (wie vorher)
                        # Dies ist der Fall wenn GraphQL-Schema order-Feld auf Tasks nicht unterstützt
                        if use_fallback_no_order:
                            # Fallback: Wenn order-Feld nicht verfügbar, übernehme alle Tasks
                            # (wie vorher, da wir nicht wissen können, welcher Task zu welchem Auftrag gehört)
                            filtered_tasks = all_tasks
                            if len(dossier_orders) > 1:
                                logger.warning(f"⚠️ Dossier hat {len(dossier_orders)} Aufträge ({[o.get('number') for o in dossier_orders]}), aber order-Feld auf Tasks nicht verfügbar. Übernehme alle {len(all_tasks)} Tasks (kann zu falschen Zuordnungen führen).")
                            else:
                                logger.info(f"✅ order-Feld nicht verfügbar, übernehme alle {len(all_tasks)} Tasks (Dossier hat nur einen Auftrag)")
                        else:
                            # order-Feld ist verfügbar - prüfe ob es tatsächlich in Tasks vorhanden ist
                            # Prüfe ob mindestens ein Task ein order-Feld hat
                            has_any_order = any(task.get('order') for task in all_tasks)
                            
                            if not has_any_order:
                                # Alle Tasks haben order: null - übernehme alle (wie vorher)
                                filtered_tasks = all_tasks
                                logger.info(f"✅ order-Feld vorhanden, aber alle {len(all_tasks)} Tasks haben order: null. Übernehme alle Tasks.")
                            else:
                                # order-Feld ist verfügbar und mindestens ein Task hat eine Zuordnung - filtere nach Auftragsnummer
                                for task in all_tasks:
                                    task_order = task.get('order')
                                    if task_order:
                                        # Task hat direkte Zuordnung zu einem Auftrag
                                        task_order_number = task_order.get('number')
                                        if task_order_number:
                                            # Vergleich: String, Integer, mit/ohne führende Nullen
                                            task_order_str = str(task_order_number).strip()
                                            order_number_str = str(order_number).strip()
                                            match = False
                                            if task_order_str == order_number_str:
                                                match = True
                                            elif task_order_str.isdigit() and order_number_str.isdigit():
                                                if int(task_order_str) == int(order_number_str):
                                                    match = True
                                                elif task_order_str.lstrip('0') == order_number_str.lstrip('0'):
                                                    match = True
                                            if match:
                                                filtered_tasks.append(task)
                                                logger.info(f"✅ Task {task.get('id')} zugeordnet zu Auftrag {order_number} (Task-Order: {task_order_number})")
                                    else:
                                        # Task hat keine direkte Zuordnung - prüfe ob Dossier nur einen Auftrag hat
                                        if len(dossier_orders) == 1:
                                            # Nur ein Auftrag im Dossier - Task gehört zu diesem
                                            dossier_order_number = dossier_orders[0].get('number')
                                            if dossier_order_number:
                                                dossier_order_str = str(dossier_order_number).strip()
                                                order_number_str = str(order_number).strip()
                                                match = False
                                                if dossier_order_str == order_number_str:
                                                    match = True
                                                elif dossier_order_str.isdigit() and order_number_str.isdigit():
                                                    if int(dossier_order_str) == int(order_number_str):
                                                        match = True
                                                    elif dossier_order_str.lstrip('0') == order_number_str.lstrip('0'):
                                                        match = True
                                                if match:
                                                    filtered_tasks.append(task)
                                                    logger.info(f"✅ Task {task.get('id')} zugeordnet zu Auftrag {order_number} (Dossier hat nur einen Auftrag: {dossier_order_number})")
                                        else:
                                            # Mehrere Aufträge im Dossier, aber Task hat keine Zuordnung
                                            # WARNUNG: Task wird nicht übernommen, da Zuordnung unklar
                                            logger.warning(f"⚠️ Task {task.get('id')} hat keine Auftrags-Zuordnung, aber Dossier hat {len(dossier_orders)} Aufträge ({[o.get('number') for o in dossier_orders]}). Task wird übersprungen.")
                        
                        tasks_with_desc = [t for t in filtered_tasks if t.get('description')]
                        
                        # TAG 212: Logging für Diagnose-Informationen
                        logger.info(f"GUDAT-Daten für Auftrag {order_number}: {len(filtered_tasks)} gefilterte Tasks, {len(tasks_with_desc)} Tasks mit description")
                        if filtered_tasks and not tasks_with_desc:
                            logger.warning(f"⚠️ Auftrag {order_number}: {len(filtered_tasks)} Tasks gefunden, aber keine mit description - Diagnose-Informationen fehlen!")
                        
                        # Sammle alle Rückfragen/Nachrichten (nur von gefilterten Tasks)
                        rueckfragen = []
                        
                        if not use_fallback:
                            # Dossier-Level Kommentare (gelten für alle Aufträge im Dossier)
                            dossier_comments = dossier.get('comments', [])
                            if dossier_comments:
                                for comment in dossier_comments:
                                    rueckfragen.append({
                                        'typ': 'Dossier',
                                        'text': comment.get('text', ''),
                                        'erstellt_am': comment.get('created_at', ''),
                                        'autor': comment.get('user', {}).get('name', 'Unbekannt')
                                    })
                            
                            # Task-Level Kommentare (nur von gefilterten Tasks)
                            for task in filtered_tasks:
                                task_comments = task.get('comments', [])
                                if task_comments:
                                    for comment in task_comments:
                                        rueckfragen.append({
                                            'typ': 'Task',
                                            'task_id': task.get('id'),
                                            'text': comment.get('text', ''),
                                            'erstellt_am': comment.get('created_at', ''),
                                            'autor': comment.get('user', {}).get('name', 'Unbekannt')
                                        })
                        
                        # Falls keine Kommentare, aber dossier_note vorhanden, verwende diese
                        dossier_note = dossier.get('note')
                        if not rueckfragen and dossier_note and dossier_note.strip():
                            rueckfragen.append({
                                'typ': 'Dossier',
                                'text': dossier_note,
                                'erstellt_am': None,
                                'autor': 'GUDAT'
                            })
                        
                        gudat_daten = {
                            'dossier_id': dossier.get('id'),
                            'dossier_note': dossier_note,
                            'states': dossier.get('states') or [],
                            'rueckfragen': rueckfragen,
                            'tasks': [
                                {
                                    'task_id': task.get('id'),
                                    'description': task.get('description'),
                                    'work_load': task.get('work_load'),
                                    'work_state': task.get('work_state')
                                } for task in tasks_with_desc
                            ]
                        }
                        # Diagnose-Fallback: Wenn keine Task-Beschreibung, aus dossier.note, order.note oder Locosoft
                        if not tasks_with_desc:
                            fallback_desc = None
                            diagnose_quelle = None
                            if dossier_note and dossier_note.strip():
                                fallback_desc = dossier_note.strip()
                                diagnose_quelle = 'gudat_dossier'
                            if not fallback_desc:
                                for ord_obj in dossier.get('orders', []):
                                    if str(ord_obj.get('number', '')).strip() == str(order_number).strip():
                                        onote = ord_obj.get('note')
                                        if onote and onote.strip():
                                            fallback_desc = onote.strip()
                                            diagnose_quelle = 'gudat_order'
                                            break
                            if not fallback_desc and job_beschreibung and job_beschreibung.strip():
                                fallback_desc = job_beschreibung.strip()
                                diagnose_quelle = 'locosoft'
                            if fallback_desc:
                                gudat_daten['tasks'] = [
                                    {'task_id': None, 'description': fallback_desc, 'work_load': None, 'work_state': None}
                                ]
                                gudat_daten['diagnose_quelle'] = diagnose_quelle
                                logger.info(f"Auftrag {order_number}: Diagnose-Fallback verwendet (Quelle: {diagnose_quelle})")
                            else:
                                logger.warning(f"⚠️ Auftrag {order_number}: GUDAT-Dossier gefunden (ID: {dossier.get('id')}), aber keine Tasks mit description - Diagnose-Informationen fehlen in PDF!")
                    else:
                        logger.warning(f"⚠️ Auftrag {order_number}: GUDAT-Dossier nicht gefunden - keine Diagnose-Informationen verfügbar")
                        gudat_daten = None
                        # Locosoft-Fallback: Auch ohne GUDAT Diagnose aus Arbeitspositionen anzeigen
                        if job_beschreibung and job_beschreibung.strip():
                            gudat_daten = {
                                'dossier_id': None,
                                'dossier_note': None,
                                'states': [],
                                'rueckfragen': [],
                                'tasks': [
                                    {'task_id': None, 'description': job_beschreibung.strip(), 'work_load': None, 'work_state': None}
                                ],
                                'diagnose_quelle': 'locosoft'
                            }
                            logger.info(f"Auftrag {order_number}: Diagnose aus Locosoft (kein GUDAT-Dossier)")
    except Exception as e:
        print(f"GUDAT-Fehler: {e}")
        gudat_daten = None
    
    # Brand-Erkennung aus subsidiary (TAG 189)
    subsidiary = auftrag[6] if len(auftrag) > 6 else None
    brand = 'hyundai'  # Default
    if subsidiary == 1 or subsidiary == 3:
        brand = 'stellantis'  # Deggendorf Opel (1) oder Landau (3)
    elif subsidiary == 2:
        brand = 'hyundai'  # Deggendorf Hyundai (2)
    
    # Daten zusammenführen
    return {
        'order_number': order_number,
        'subsidiary': subsidiary,
        'brand': brand,  # TAG 189: Brand für Garantieakte-Erstellung
        'locosoft': {
            'auftrag': {
                'nummer': auftrag[0],
                # TAG 189: Datum als ISO-String formatieren (für GUDAT-Suche)
                'datum': auftrag[1].isoformat() if auftrag[1] and hasattr(auftrag[1], 'isoformat') else (str(auftrag[1]) if auftrag[1] else None),
                'serviceberater': auftrag[3],
                'serviceberater_nr': auftrag[2],
                'job_beschreibung': job_beschreibung
            },
            'kunde': {
                # TAG 189: Verwende COALESCE-Ergebnis aus DB (kunde[0]) statt manueller String-Konstruktion
                'name': kunde[0] if kunde and kunde[0] else None,  # kunde[0] ist bereits COALESCE-Ergebnis
                'adresse': f"{kunde[3]}, {kunde[4]} {kunde[5]}" if kunde and kunde[3] and kunde[4] and kunde[5] else None,  # Indizes verschoben wegen neuem Feld
                'telefon': telefon,
                'email': email
            },
            'fahrzeug': {
                'kennzeichen': fahrzeug[0] if fahrzeug else None,
                'vin': fahrzeug[1] if fahrzeug else None,
                'erstzulassung': str(fahrzeug[2]) if fahrzeug and fahrzeug[2] else None,
                'kilometerstand': fahrzeug[3] if fahrzeug else None,
                'marke_modell': f"{fahrzeug[4]} {fahrzeug[5]}" if fahrzeug else None
            },
            'positionen': [
                {
                    'position': pos[0],
                    'operation': pos[1],
                    'text_line': pos[2],
                    'aw': float(pos[3]) if pos[3] else 0,
                    'mechaniker': pos[5],
                    'abgerechnet': pos[6] if len(pos) > 6 else False,
                    'invoice_type': pos[7] if len(pos) > 7 else None
                } for pos in positionen
            ],
            'stempelzeiten': [
                {
                    'mechaniker': st[1],
                    'start': str(st[2]) if st[2] else None,
                    'ende': str(st[3]) if st[3] else None,
                    'dauer_min': st[4]
                } for st in stempelzeiten
            ],
            'teile': [
                {
                    'teilenummer': teil[0],
                    'beschreibung': teil[1],
                    'menge': float(teil[2]) if teil[2] else 0,
                    'preis': float(teil[3]) if teil[3] else 0,
                    'abgerechnet': teil[4] if len(teil) > 4 else False,
                    'invoice_type': teil[5] if len(teil) > 5 else None
                } for teil in teile
            ]
        },
        'gudat': gudat_daten
    }


@bp.route('/<int:order_number>', methods=['GET'])
@login_required
def get_arbeitskarte_data(order_number):
    """
    Gibt Arbeitskarte-Daten als JSON zurück.
    Inkl. Prüfung ob Unterschrift vorhanden ist.
    """
    try:
        daten = hole_arbeitskarte_daten(order_number)
        
        if not daten:
            return jsonify({
                'success': False,
                'error': f'Auftrag {order_number} nicht gefunden'
            }), 404
        
        # Prüfe Unterschrift
        unterschrift_info = pruefe_unterschrift(order_number)
        daten['unterschrift'] = unterschrift_info
        
        return jsonify({
            'success': True,
            'data': daten
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/<int:order_number>/pdf', methods=['GET'])
@login_required
def get_arbeitskarte_pdf(order_number):
    """Generiert PDF der Arbeitskarte"""
    try:
        daten = hole_arbeitskarte_daten(order_number)
        
        if not daten:
            return jsonify({
                'success': False,
                'error': f'Auftrag {order_number} nicht gefunden'
            }), 404
        
        pdf_bytes = generate_arbeitskarte_pdf(daten)
        
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Arbeitskarte_{order_number}.pdf'
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _get_arbeitskarte_anhaenge_internal(order_number, order_date=None, license_plate=None, vin=None):
    """
    Interne Funktion: Holt ALLE Anhänge (Dokumente) aus GUDAT für einen Auftrag.
    Inkl. Bilder, PDFs (z.B. Locosoft-Auftrag mit Unterschrift), etc.
    
    Args:
        order_number: Auftragsnummer
        order_date: Optionales Auftragsdatum (datetime.date oder ISO-String) für präzisere Suche
        license_plate: Optionales Kennzeichen für alternative Suche
        vin: Optionales VIN für alternative Suche
    
    Returns:
        Dict mit Liste aller Anhänge
    """
    try:
        client = GudatClient(GUDAT_CONFIG['username'], GUDAT_CONFIG['password'])
        if not client.login():
            return {
                'success': False,
                'error': 'GUDAT-Login fehlgeschlagen',
                'anhaenge': []
            }
        
        # Finde Dossier - erweiterte Suche (nicht nur heute)
        # Versuche zuerst heute, dann erweitere Suche auf letzten 30 Tage
        from datetime import date, timedelta
        
        dossier_id = None
        
        # TAG 189: Verwende Auftragsdatum falls vorhanden, sonst heute - 14 Tage
        if order_date:
            if isinstance(order_date, str):
                from datetime import datetime
                try:
                    # Parse datetime-String (z.B. "2026-01-07 11:28:00" oder "2026-01-07")
                    if ' ' in order_date:
                        order_date = datetime.strptime(order_date.split()[0], '%Y-%m-%d').date()
                    elif 'T' in order_date:
                        order_date = datetime.fromisoformat(order_date.split('T')[0]).date()
                    else:
                        order_date = datetime.fromisoformat(order_date).date()
                except Exception as e:
                    logger.warning(f"Fehler beim Parsen von order_date '{order_date}': {e}")
                    order_date = date.today() - timedelta(days=14)
            elif hasattr(order_date, 'date'):
                # Falls es ein datetime-Objekt ist
                order_date = order_date.date()
            elif not isinstance(order_date, date):
                order_date = date.today() - timedelta(days=14)
        else:
            order_date = date.today() - timedelta(days=14)
        
        logger.info(f"GUDAT-Suche: Verwende Auftragsdatum {order_date} (Auftrag {order_number})")
        
        query_tasks = """
        query GetWorkshopTasks($page: Int!, $itemsPerPage: Int!, $where: QueryWorkshopTasksWhereWhereConditions) {
          workshopTasks(first: $itemsPerPage, page: $page, where: $where) {
            data {
              id
              dossier {
                id
                orders { number }
              }
            }
          }
        }
        """
        
        # TAG 193: EINFACHE Suche - suche in letzten 30 Tagen (Dossier ist max 10 Tage alt)
        # Kleinere Zeitraum für bessere Performance, aber groß genug für alle Fälle
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()
        
        dossier_id = None
        max_pages = 20  # Max 20 Seiten = 4000 Tasks (mehr als genug für 30 Tage)
        
        logger.info(f"GUDAT-Suche: Suche in letzten 30 Tagen nach Auftrag {order_number} (max {max_pages} Seiten)")
        
        for page in range(1, max_pages + 1):
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
            
            response = client.session.post(
                f"{client.BASE_URL}/graphql",
                json={"operationName": "GetWorkshopTasks", "query": query_tasks, "variables": variables},
                headers={
                    'Accept': 'application/json',
                    'X-XSRF-TOKEN': client._get_xsrf(),
                    'Content-Type': 'application/json'
                }
            )
            
            data = response.json()
            
            if 'errors' in data:
                logger.warning(f"GraphQL-Fehler bei Suche (Seite {page}): {data.get('errors')}")
                break
            
            tasks = data.get('data', {}).get('workshopTasks', {}).get('data', [])
            if not tasks:
                break  # Keine weiteren Tasks
            
            logger.info(f"GUDAT-Suche (Seite {page}): {len(tasks)} Tasks gefunden")
            
            # Debug: Sammle gefundene Auftragsnummern (nur erste Seite)
            if page == 1:
                found_order_numbers_debug = []
                for task in tasks[:10]:  # Nur erste 10 Tasks für Debug
                    orders = task.get('dossier', {}).get('orders', [])
                    for order in orders:
                        order_num = order.get('number')
                        if order_num:
                            found_order_numbers_debug.append(f"{order_num} (type: {type(order_num).__name__})")
                if found_order_numbers_debug:
                    logger.info(f"🔍 Debug (Seite 1, erste 10 Tasks): Gefundene Auftragsnummern: {found_order_numbers_debug[:10]}")
            
            # Einfache Suche nach Auftragsnummer - erweiterte Vergleichslogik
            for task in tasks:
                orders = task.get('dossier', {}).get('orders', [])
                for order in orders:
                    order_num = order.get('number')
                    if order_num is None:
                        continue
                    
                    # Erweiterte Vergleichslogik: String, Integer, mit/ohne führende Nullen
                    order_num_str = str(order_num).strip()
                    order_number_str = str(order_number).strip()
                    
                    match = False
                    # Exakter String-Vergleich
                    if order_num_str == order_number_str:
                        match = True
                    # Integer-Vergleich (auch wenn einer String ist)
                    try:
                        if int(order_num_str) == int(order_number_str):
                            match = True
                    except (ValueError, TypeError):
                        pass
                    
                    # Prüfe auch ohne führende Nullen (z.B. "039831" == "39831")
                    if not match:
                        order_num_clean = order_num_str.lstrip('0') if order_num_str else ""
                        order_number_clean = order_number_str.lstrip('0') if order_number_str else ""
                        if order_num_clean and order_number_clean and order_num_clean == order_number_clean:
                            match = True
                    
                    # Prüfe auch mit führenden Nullen (z.B. "39831" == "039831")
                    if not match:
                        # Versuche beide mit führenden Nullen auf gleiche Länge zu bringen
                        max_len = max(len(order_num_str), len(order_number_str))
                        order_num_padded = order_num_str.zfill(max_len)
                        order_number_padded = order_number_str.zfill(max_len)
                        if order_num_padded == order_number_padded:
                            match = True
                    
                    if match:
                        dossier_id = task.get('dossier', {}).get('id')
                        logger.info(f"✅ Dossier gefunden für Auftrag {order_number}: dossier_id={dossier_id} (Seite {page}, Match: '{order_num_str}' == '{order_number_str}')")
                        break
                if dossier_id:
                    break
            
            if dossier_id:
                break
            
            # Wenn weniger als 200 Tasks, sind wir am Ende
            if len(tasks) < 200:
                break
        
        if not dossier_id:
            logger.warning(f"⚠️ Dossier für Auftrag {order_number} nicht in letzten 30 Tagen gefunden")
        
        # TAG 189: Alternative Suche nach Kennzeichen/VIN, falls Order-Nummer nicht gefunden
        # WICHTIG: Diese Suche funktioniert auch, wenn Auftrag in GUDAT mit falscher Marke kategorisiert ist!
        if not dossier_id and (license_plate or vin):
            logger.info(f"Order-Nummer {order_number} nicht gefunden, versuche alternative Suche nach Kennzeichen/VIN (unabhängig von Marke)...")
            
            # Erweiterte Query: Suche nach workshopTasks mit vehicle.license_plate oder vehicle.vin
            # Diese Suche durchsucht ALLE Marken, nicht nur die erwartete
            query_tasks_vehicle = """
            query GetWorkshopTasksByVehicle($page: Int!, $itemsPerPage: Int!, $where: QueryWorkshopTasksWhereWhereConditions) {
              workshopTasks(first: $itemsPerPage, page: $page, where: $where) {
                data {
                  id
                  dossier {
                    id
                    vehicle {
                      id
                      license_plate
                    }
                    orders {
                      number
                    }
                  }
                }
              }
            }
            """
            
            try:
                # Suche in letzten 365 Tagen nach Fahrzeug (unabhängig von Marke)
                # TAG 192: Erweitert von 180 auf 365 Tage, da Dossier möglicherweise älter ist
                start_date_alt = (date.today() - timedelta(days=365)).isoformat()
                end_date_alt = date.today().isoformat()
                logger.info(f"Fahrzeug-Suche: Suche in letzten 365 Tagen nach Kennzeichen '{license_plate}' oder VIN '{vin}' (Auftrag {order_number})")
                
                # Suche mit Datumsbereich (ohne Marken-Filter!)
                variables_vehicle = {
                    "page": 1,
                    "itemsPerPage": 200,
                    "where": {
                        "AND": [
                            {"column": "START_DATE", "operator": "GTE", "value": start_date_alt},
                            {"column": "START_DATE", "operator": "LTE", "value": end_date_alt}
                        ]
                    }
                }
                
                # Durchsuche alle Tasks und prüfe Kennzeichen/VIN
                for page in range(1, 11):  # Max 10 Seiten = 2000 Tasks
                    variables_vehicle["page"] = page
                    response_vehicle = client.session.post(
                        f"{client.BASE_URL}/graphql",
                        json={"operationName": "GetWorkshopTasksByVehicle", "query": query_tasks_vehicle, "variables": variables_vehicle},
                        headers={
                            'Accept': 'application/json',
                            'X-XSRF-TOKEN': client._get_xsrf(),
                            'Content-Type': 'application/json'
                        }
                    )
                    data_vehicle = response_vehicle.json()
                    if 'errors' in data_vehicle:
                        logger.warning(f"GraphQL-Fehler bei Fahrzeug-Suche (Seite {page}): {data_vehicle.get('errors')}")
                        break
                    
                    tasks_vehicle = data_vehicle.get('data', {}).get('workshopTasks', {}).get('data', [])
                    if not tasks_vehicle:
                        break
                    
                    logger.info(f"Fahrzeug-Suche (Seite {page}): {len(tasks_vehicle)} Tasks durchsucht")
                    
                    # TAG 192: Debug: Prüfe ob vehicle-Objekt in Tasks vorhanden ist
                    tasks_with_vehicle = 0
                    tasks_without_vehicle = 0
                    for task in tasks_vehicle:
                        dossier_task = task.get('dossier', {})
                        vehicle = dossier_task.get('vehicle')
                        if vehicle:
                            tasks_with_vehicle += 1
                        else:
                            tasks_without_vehicle += 1
                    if page == 1:
                        logger.info(f"🔍 Vehicle-Objekt-Status (Seite 1): {tasks_with_vehicle} Tasks mit vehicle, {tasks_without_vehicle} Tasks ohne vehicle")
                    
                    # Prüfe jedes Task auf passendes Fahrzeug
                    found_license_plates = set()  # Debug: Sammle gefundene Kennzeichen
                    for task in tasks_vehicle:
                        dossier_task = task.get('dossier', {})
                        vehicle = dossier_task.get('vehicle', {})
                        task_license_plate = vehicle.get('license_plate', '').strip().upper() if vehicle and vehicle.get('license_plate') else ""
                        # VIN ist nicht im GUDAT Vehicle-Schema verfügbar - wird nicht abgefragt
                        task_vin = ""
                        orders_task = dossier_task.get('orders', [])
                        
                        # Debug: Sammle alle gefundenen Kennzeichen (nur erste 10 pro Seite)
                        if task_license_plate and len(found_license_plates) < 10:
                            found_license_plates.add(task_license_plate)
                        
                        # Prüfe Kennzeichen-Match (VIN ist nicht verfügbar in GUDAT)
                        match = False
                        search_license_plate = license_plate.strip().upper() if license_plate else ""
                        if not dossier_id and search_license_plate and task_license_plate:
                            # Flexibler Vergleich: Ignoriere Leerzeichen und Bindestriche
                            task_clean = task_license_plate.replace(' ', '').replace('-', '').replace('_', '')
                            search_clean = search_license_plate.replace(' ', '').replace('-', '').replace('_', '')
                            # Exakter Match
                            if task_clean == search_clean or task_license_plate == search_license_plate:
                                match = True
                                logger.info(f"🔍 Kennzeichen-Match gefunden: '{task_license_plate}' == '{search_license_plate}' (Dossier {dossier_task.get('id')}, Orders: {[o.get('number') for o in orders_task]})")
                            # Teil-Match: Prüfe ob beide die gleichen Teile enthalten (z.B. "DEG BO 554" vs "DEG-BO 554")
                            elif not match:
                                task_parts = set([p for p in task_license_plate.replace('-', ' ').split() if len(p) > 1])
                                search_parts = set([p for p in search_license_plate.replace('-', ' ').split() if len(p) > 1])
                                if len(task_parts) >= 2 and len(search_parts) >= 2:
                                    # Wenn mindestens 2 Teile übereinstimmen
                                    common_parts = task_parts.intersection(search_parts)
                                    if len(common_parts) >= 2:
                                        match = True
                                        logger.info(f"🔍 Kennzeichen-Teil-Match gefunden: '{task_license_plate}' ~= '{search_license_plate}' (gemeinsame Teile: {common_parts}, Dossier {dossier_task.get('id')}, Orders: {[o.get('number') for o in orders_task]})")
                        
                        if match:
                            # Prüfe, ob die gesuchte Order-Nummer in den Orders ist
                            found_order_match = False
                            for order in orders_task:
                                order_num = str(order.get('number', '')).strip()
                                order_number_str = str(order_number).strip()
                                if order_num == order_number_str or (order_num.lstrip('0') == order_number_str.lstrip('0')):
                                    dossier_id = dossier_task.get('id')
                                    logger.info(f"✅ Dossier via Kennzeichen gefunden (unabhängig von Marke): dossier_id={dossier_id}, order={order_num}, kennzeichen={task_license_plate}")
                                    found_order_match = True
                                    break
                            
                            # TAG 189: Falls Kennzeichen eindeutig passt, aber Order-Nummer nicht übereinstimmt,
                            # verwende trotzdem das Dossier (z.B. wenn Auftrag in GUDAT mit falscher Marke/Order-Nr erfasst wurde)
                            if not found_order_match and not dossier_id:
                                dossier_id_candidate = dossier_task.get('id')
                                orders_found = [str(o.get('number', '')).strip() for o in orders_task]
                                logger.warning(f"⚠️ Kennzeichen-Match gefunden, aber Order-Nummer stimmt nicht: Dossier {dossier_id_candidate}, gesucht: {order_number}, gefunden: {orders_found}, kennzeichen={task_license_plate}")
                                # Verwende das Dossier trotzdem, wenn Kennzeichen eindeutig passt
                                # (z.B. wenn Auftrag in GUDAT mit falscher Order-Nr erfasst wurde)
                                dossier_id = dossier_id_candidate
                                logger.info(f"✅ Dossier trotzdem verwendet (Kennzeichen eindeutig): dossier_id={dossier_id}, kennzeichen={task_license_plate}")
                            
                            if dossier_id:
                                break
                    
                    # Debug: Zeige gefundene Kennzeichen
                    if page == 1:
                        if found_license_plates:
                            logger.info(f"🔍 Beispiel-Kennzeichen in Tasks (Seite 1): {sorted(list(found_license_plates))[:10]}")
                        # Prüfe auf Teil-Matches (z.B. "DEG-BO" oder "BO 554")
                        if license_plate:
                            search_parts = license_plate.upper().replace('-', ' ').split()
                            for lp in found_license_plates:
                                lp_parts = lp.replace('-', ' ').split()
                                if any(part in lp_parts for part in search_parts if len(part) > 2):
                                    logger.info(f"🔍 Mögliches Teil-Match gefunden: '{lp}' enthält Teile von '{license_plate.upper()}'")
                        # VIN ist nicht verfügbar in GUDAT - keine VIN-Suche möglich
                    
                    # TAG 192: Wenn nach Seite 1 kein Match gefunden, zeige Zusammenfassung
                    if page == 1 and not dossier_id:
                        logger.info(f"🔍 Fahrzeug-Suche Seite 1 abgeschlossen: {len(tasks_vehicle)} Tasks durchsucht, {len(found_license_plates)} Kennzeichen gefunden. Gesucht: Kennzeichen='{license_plate}'")
                    
                    if dossier_id:
                        break
                    
                    # Wenn weniger als 200 Tasks, sind wir am Ende
                    if len(tasks_vehicle) < 200:
                        break
                        
            except Exception as e:
                logger.warning(f"Fehler bei alternativer Suche nach Kennzeichen/VIN: {e}")
                import traceback
                traceback.print_exc()
        
        if not dossier_id:
            return {
                'success': True,
                'message': f'Dossier für Auftrag {order_number} nicht gefunden',
                'anhaenge': [],
                'dossier_id': None,
                'gudat_session': client.session  # TAG 189: Session auch bei keinem Dossier zurückgeben
            }
        
        # Hole ALLE Dokumente (nicht nur Bilder)
        query_dossier = """
        query GetDossierAttachments($id: ID!) {
          dossier(id: $id) {
            id
            documents {
              id
              name
              file_type
            }
          }
        }
        """
        
        response = client.session.post(
            f"{client.BASE_URL}/graphql",
            json={"operationName": "GetDossierAttachments", "query": query_dossier, "variables": {"id": str(dossier_id)}},
            headers={
                'Accept': 'application/json',
                'X-XSRF-TOKEN': client._get_xsrf(),
                'Content-Type': 'application/json'
            }
        )
        
        data = response.json()
        
        if 'errors' in data:
            return {
                'success': False,
                'error': f"GraphQL-Fehler: {data['errors']}",
                'anhaenge': []
            }
        
        dossier = data.get('data', {}).get('dossier')
        
        if not dossier:
            return {
                'success': True,
                'message': 'Dossier-Daten nicht gefunden',
                'anhaenge': [],
                'dossier_id': None,
                'gudat_session': client.session  # TAG 189: Session auch bei keinem Dossier zurückgeben
            }
        
        documents = dossier.get('documents', [])
        # Hole ALLE Dokumente (Bilder, PDFs, etc.)
        anhaenge = documents  # Kein Filter mehr!
        
        # Kategorisiere für Rückgabe
        bilder = [a for a in anhaenge if a.get('file_type', '').startswith('image/')]
        pdfs = [a for a in anhaenge if a.get('file_type', '') == 'application/pdf']
        andere = [a for a in anhaenge if not a.get('file_type', '').startswith('image/') and a.get('file_type', '') != 'application/pdf']
        
        return {
            'success': True,
            'order_number': order_number,
            'dossier_id': dossier.get('id'),
            'anhaenge': anhaenge,
            'anzahl_anhaenge': len(anhaenge),
            'anzahl_bilder': len(bilder),
            'anzahl_pdfs': len(pdfs),
            'anzahl_andere': len(andere),
            'gudat_session': client.session  # Session für Downloads
        }
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Anhänge: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'anhaenge': []
        }


def pruefe_unterschrift(order_number):
    """
    Prüft ob ein Auftrag eine Unterschrift hat.
    Die Unterschrift wird mit Locosoft APP digital erfasst und in 
    \\\\srvloco01\\Loco\\BILDER gespeichert.
    Format: "212-{order_number}-*" (z.B. "212-00220266-01.pdf")
    
    Args:
        order_number: Auftragsnummer
    
    Returns:
        Dict mit 'hat_unterschrift', 'dateien' (Liste der gefundenen Dateien)
    """
    try:
        import glob
        import os
        
        # Mount-Pfad für Locosoft BILDER
        bilder_path = '/mnt/loco-bilder'
        
        if not os.path.exists(bilder_path):
            return {
                'hat_unterschrift': False,
                'fehler': f'Mount-Pfad {bilder_path} existiert nicht'
            }
        
        # Suche nach Dateien mit Format "212-{order_number}-*"
        # Auftragsnummer wird mit führenden Nullen auf 8 Stellen aufgefüllt
        # Format: "212-" + "{8-stellige Auftragsnummer}" + "-*"
        # Beispiel: 209721 -> "212-00209721-*"
        order_str = str(order_number).zfill(8)
        pattern = f'212-{order_str}-*'
        
        # Suche nach allen Dateien mit diesem Pattern
        dateien = glob.glob(os.path.join(bilder_path, pattern))
        
        if dateien:
            # Sortiere und extrahiere Dateinamen
            dateien_namen = sorted([os.path.basename(f) for f in dateien])
            
            # Kategorisiere nach Dateityp
            pdfs = [f for f in dateien_namen if f.endswith('.pdf')]
            bilder = [f for f in dateien_namen if f.endswith(('.jpg', '.jpeg', '.png'))]
            
            return {
                'hat_unterschrift': True,
                'dateien': dateien_namen,
                'anzahl_dateien': len(dateien_namen),
                'pdfs': pdfs,
                'bilder': bilder,
                'pfad': bilder_path,
                'windows_pfad': f'\\\\srvloco01\\Loco\\BILDER'
            }
        else:
            return {
                'hat_unterschrift': False,
                'hinweis': f'Keine Dateien mit Pattern "212-0{order_str}-*" gefunden',
                'gesuchtes_pattern': pattern,
                'pfad': bilder_path
            }
        
    except Exception as e:
        logger.error(f"Fehler beim Prüfen der Unterschrift: {e}")
        import traceback
        traceback.print_exc()
        return {
            'hat_unterschrift': False,
            'fehler': str(e)
        }


def get_arbeitskarte_anhaenge(order_number, order_date=None, license_plate=None, vin=None):
    """
    Öffentliche Funktion: Holt ALLE Anhänge (Dokumente) aus GUDAT für einen Auftrag.
    Inkl. Bilder, PDFs (z.B. Locosoft-Auftrag mit Unterschrift), etc.
    
    Args:
        order_number: Auftragsnummer
        order_date: Optionales Auftragsdatum für präzisere GUDAT-Suche
        license_plate: Optionales Kennzeichen für alternative Suche
        vin: Optionales VIN für alternative Suche
    
    Returns:
        Dict mit Liste aller Anhänge
    """
    return _get_arbeitskarte_anhaenge_internal(order_number, order_date=order_date, license_plate=license_plate, vin=vin)


@bp.route('/<int:order_number>/anhaenge', methods=['GET'])
@login_required
def get_arbeitskarte_anhaenge_route(order_number):
    """
    Flask-Route: Holt ALLE Anhänge (Dokumente) aus GUDAT für einen Auftrag.
    Inkl. Bilder, PDFs (z.B. Locosoft-Auftrag mit Unterschrift), etc.
    
    Returns:
        JSON mit Liste aller Anhänge
    """
    result = get_arbeitskarte_anhaenge(order_number)
    
    if result.get('success'):
        # Entferne Session aus JSON-Response (nicht serialisierbar)
        response_data = {k: v for k, v in result.items() if k != 'gudat_session'}
        return jsonify(response_data)
    else:
        return jsonify(result), 500


@bp.route('/<int:order_number>/unterschrift', methods=['GET'])
@login_required
def pruefe_unterschrift_route(order_number):
    """
    Flask-Route: Prüft ob ein Auftrag eine Unterschrift hat.
    
    Returns:
        JSON mit 'hat_unterschrift', 'pdf_name', 'pdf_id' (falls vorhanden)
    """
    result = pruefe_unterschrift(order_number)
    return jsonify(result)


# Alias für Rückwärtskompatibilität (alte Route)
@bp.route('/<int:order_number>/bilder', methods=['GET'])
@login_required
def get_arbeitskarte_bilder_route(order_number):
    """
    Flask-Route: Holt Bilder aus GUDAT (DEPRECATED - verwende /anhaenge)
    """
    result = get_arbeitskarte_anhaenge(order_number)
    
    if result.get('success'):
        # Filtere nur Bilder für Rückwärtskompatibilität
        bilder = [a for a in result.get('anhaenge', []) if a.get('file_type', '').startswith('image/')]
        response_data = {
            'success': True,
            'order_number': result.get('order_number'),
            'dossier_id': result.get('dossier_id'),
            'bilder': bilder,
            'anzahl_bilder': len(bilder),
            'anzahl_attachments': result.get('anzahl_anhaenge', 0)
        }
        return jsonify(response_data)
    else:
        return jsonify(result), 500


def get_arbeitskarte_bilder(order_number):
    """
    Holt Bilder aus GUDAT für einen Auftrag.
    DEPRECATED: Verwende get_arbeitskarte_anhaenge() für alle Anhänge.
    
    Returns:
        JSON mit Liste der Bilder (Attachments)
    """
    try:
        client = GudatClient(GUDAT_CONFIG['username'], GUDAT_CONFIG['password'])
        if not client.login():
            return jsonify({
                'success': False,
                'error': 'GUDAT-Login fehlgeschlagen'
            }), 500
        
        from datetime import date
        target_date = date.today().isoformat()
        
        # Finde Dossier
        query_tasks = """
        query GetWorkshopTasks($page: Int!, $itemsPerPage: Int!, $where: QueryWorkshopTasksWhereWhereConditions) {
          workshopTasks(first: $itemsPerPage, page: $page, where: $where) {
            data {
              id
              dossier {
                id
                orders { number }
              }
            }
          }
        }
        """
        
        variables = {
            "page": 1,
            "itemsPerPage": 200,
            "where": {
                "AND": [{"column": "START_DATE", "operator": "EQ", "value": target_date}]
            }
        }
        
        response = client.session.post(
            f"{client.BASE_URL}/graphql",
            json={"operationName": "GetWorkshopTasks", "query": query_tasks, "variables": variables},
            headers={
                'Accept': 'application/json',
                'X-XSRF-TOKEN': client._get_xsrf(),
                'Content-Type': 'application/json'
            }
        )
        
        data = response.json()
        
        if 'errors' in data:
            return jsonify({
                'success': False,
                'error': f"GraphQL-Fehler: {data['errors']}"
            }), 500
        
        tasks = data.get('data', {}).get('workshopTasks', {}).get('data', [])
        
        # Finde dossier_id
        dossier_id = None
        for task in tasks:
            orders = task.get('dossier', {}).get('orders', [])
            for order in orders:
                if order.get('number') == str(order_number):
                    dossier_id = task.get('dossier', {}).get('id')
                    break
        
        if not dossier_id:
            return jsonify({
                'success': True,
                'message': f'Dossier für Auftrag {order_number} nicht gefunden',
                'bilder': []
            })
        
        # Hole Attachments
        query_dossier = """
        query GetDossierAttachments($id: ID!) {
          dossier(id: $id) {
            id
            documents {
              id
              name
              file_type
            }
          }
        }
        """
        
        response = client.session.post(
            f"{client.BASE_URL}/graphql",
            json={"operationName": "GetDossierAttachments", "query": query_dossier, "variables": {"id": str(dossier_id)}},
            headers={
                'Accept': 'application/json',
                'X-XSRF-TOKEN': client._get_xsrf(),
                'Content-Type': 'application/json'
            }
        )
        
        data = response.json()
        
        if 'errors' in data:
            return jsonify({
                'success': False,
                'error': f"GraphQL-Fehler: {data['errors']}"
            }), 500
        
        dossier = data.get('data', {}).get('dossier')
        
        if not dossier:
            return jsonify({
                'success': True,
                'message': 'Dossier-Daten nicht gefunden',
                'bilder': []
            })
        
        documents = dossier.get('documents', [])
        # Filtere Bilder nach file_type (z.B. 'image/jpeg', 'image/png')
        bilder = [a for a in documents if a.get('file_type', '').startswith('image/')]
        
        # Füge Download-URL-Info hinzu (document_id wird für Download verwendet)
        for bild in bilder:
            # document_id ist bereits in 'id' enthalten
            bild['download_ready'] = True
        
        return jsonify({
            'success': True,
            'order_number': order_number,
            'dossier_id': dossier.get('id'),
            'bilder': bilder,
            'anzahl_bilder': len(bilder),
            'anzahl_attachments': len(documents)
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Bilder: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/<int:order_number>/speichern', methods=['POST'])
@login_required
def speichere_garantieakte(order_number):
    """
    Speichert vollständige Garantieakte in Ordnerstruktur.
    - Ordner: {kunde}_{Auftragsnummer}
    - Dateien: Arbeitskarte-PDF, Bilder (einzeln), Terminblatt
    
    Args (JSON Body, optional):
        dossier_id: Manuelle Dossier-ID falls automatische Suche fehlschlägt
    
    Returns:
        JSON mit Erfolg/Fehler und Pfaden
    """
    try:
        # TAG 189: Prüfe ob manuelle Dossier-ID übergeben wurde
        request_data = request.get_json() or {}
        manual_dossier_id = request_data.get('dossier_id')
        from api.garantieakte_workflow import create_garantieakte_vollstaendig
        from api.arbeitskarte_pdf import generate_arbeitskarte_pdf
        
        # 1. Hole Arbeitskarte-Daten
        daten = hole_arbeitskarte_daten(order_number)
        
        if not daten:
            return jsonify({
                'success': False,
                'error': f'Auftrag {order_number} nicht gefunden'
            }), 404
        
        # TAG 212: Hole Diagnose-Informationen VOR PDF-Generierung, falls Dossier in Anhänge-Suche gefunden wird
        # (hole_arbeitskarte_daten() findet Dossier manchmal nicht, aber get_arbeitskarte_anhaenge() findet es)
        # Wir holen die Anhänge-Suche VOR der PDF-Generierung, um Diagnose-Informationen zu bekommen
        
        # 2. Hole Anhänge UND Diagnose-Informationen VOR PDF-Generierung
        order_date = daten.get('locosoft', {}).get('auftrag', {}).get('datum')
        license_plate = daten.get('locosoft', {}).get('fahrzeug', {}).get('kennzeichen')
        vin = daten.get('locosoft', {}).get('fahrzeug', {}).get('vin')
        logger.info(f"GUDAT-Suche für Auftrag {order_number}: datum={order_date}, kennzeichen={license_plate}, vin={vin}")
        
        anhaenge = []
        dossier_id = None
        gudat_session = None
        dossier_not_found = False
        
        # TAG 189: Wenn manuelle Dossier-ID übergeben wurde, verwende diese direkt
        if manual_dossier_id:
            logger.info(f"Verwende manuelle Dossier-ID: {manual_dossier_id}")
            from tools.gudat_client import GudatClient
            client = GudatClient(GUDAT_CONFIG['username'], GUDAT_CONFIG['password'])
            if client.login():
                # Hole Anhänge direkt über Dossier-ID (gleiche Query wie in normaler Suche)
                query_dossier = """
                query GetDossierAttachments($id: ID!) {
                  dossier(id: $id) {
                    id
                    documents {
                      id
                      name
                      file_type
                    }
                  }
                }
                """
                try:
                    # TAG 189: Versuche sowohl String als auch Integer für Dossier-ID
                    dossier_id_vars = [str(manual_dossier_id), int(manual_dossier_id) if str(manual_dossier_id).isdigit() else None]
                    dossier_found = False
                    
                    for dossier_id_var in dossier_id_vars:
                        if dossier_id_var is None:
                            continue
                        logger.info(f"Versuche Dossier-ID als {type(dossier_id_var).__name__}: {dossier_id_var}")
                        response = client.session.post(
                            f"{client.BASE_URL}/graphql",
                            json={"operationName": "GetDossierAttachments", "query": query_dossier, "variables": {"id": dossier_id_var}},
                            headers={
                                'Accept': 'application/json',
                                'X-XSRF-TOKEN': client._get_xsrf(),
                                'Content-Type': 'application/json'
                            }
                        )
                        data = response.json()
                        logger.info(f"Manuelle Dossier-ID Query-Response ({type(dossier_id_var).__name__}): {data}")
                        if 'errors' not in data:
                            dossier = data.get('data', {}).get('dossier')
                            logger.info(f"Manuelle Dossier-ID: dossier={dossier}, documents={dossier.get('documents', []) if dossier else 'None'}")
                            if dossier:
                                documents = dossier.get('documents', [])
                                dossier_id = manual_dossier_id
                                gudat_session = client.session
                                dossier_found = True
                                # Konvertiere Documents zu Anhänge-Format
                                # TAG 189: Hole URL separat über document(id) Query (wie in normaler Suche)
                                for doc in documents:
                                    doc_id = doc.get('id')
                                    doc_name = doc.get('name', '')
                                    doc_file_type = doc.get('file_type', '')
                                    
                                    # Hole URL separat (wie in _get_arbeitskarte_anhaenge_internal)
                                    try:
                                        query_doc_url = """
                                        query GetDocumentUrl($id: ID!) {
                                          document(id: $id) {
                                            id
                                            url
                                          }
                                        }
                                        """
                                        response_doc = client.session.post(
                                            f"{client.BASE_URL}/graphql",
                                            json={"operationName": "GetDocumentUrl", "query": query_doc_url, "variables": {"id": str(doc_id)}},
                                            headers={
                                                'Accept': 'application/json',
                                                'X-XSRF-TOKEN': client._get_xsrf(),
                                                'Content-Type': 'application/json'
                                            }
                                        )
                                        data_doc = response_doc.json()
                                        doc_url = None
                                        if 'errors' not in data_doc:
                                            doc_data = data_doc.get('data', {}).get('document', {})
                                            doc_url = doc_data.get('url')
                                        
                                        anhaenge.append({
                                            'id': doc_id,
                                            'name': doc_name,
                                            'file_type': doc_file_type,
                                            'url': doc_url
                                        })
                                    except Exception as e:
                                        logger.warning(f"Fehler beim Holen von URL für Dokument {doc_id}: {e}")
                                        # Füge trotzdem hinzu ohne URL
                                        anhaenge.append({
                                            'id': doc_id,
                                            'name': doc_name,
                                            'file_type': doc_file_type,
                                            'url': None
                                        })
                                logger.info(f"✅ Manuelle Dossier-ID erfolgreich: {len(anhaenge)} Anhänge gefunden")
                                break  # Erfolgreich, beende Schleife
                            else:
                                logger.warning(f"⚠️ Manuelle Dossier-ID {dossier_id_var} (als {type(dossier_id_var).__name__}) nicht gefunden in GUDAT")
                        else:
                            logger.warning(f"⚠️ GraphQL-Fehler bei manueller Dossier-ID ({type(dossier_id_var).__name__}): {data.get('errors')}")
                    
                    if not dossier_found:
                        logger.warning(f"⚠️ Manuelle Dossier-ID {manual_dossier_id} nicht gefunden in GUDAT (beide Formate versucht)")
                        # TAG 193: Prüfe ob Benutzer versehentlich Auftragsnummer eingegeben hat
                        is_likely_order_number = False
                        if str(manual_dossier_id).strip() == str(order_number).strip():
                            is_likely_order_number = True
                            logger.warning(f"⚠️ Benutzer hat wahrscheinlich Auftragsnummer {order_number} statt Dossier-ID eingegeben")
                        
                        # TAG 189: Gebe detaillierte Fehlermeldung zurück
                        if is_likely_order_number:
                            error_message = f'⚠️ WICHTIG: Sie haben die Auftragsnummer "{manual_dossier_id}" eingegeben, aber das ist NICHT die GUDAT Dossier-ID!\n\n' + \
                                          f'Die Dossier-ID ist eine separate Nummer in GUDAT (z.B. 20472), NICHT die Auftragsnummer ({order_number}).\n\n' + \
                                          f'So finden Sie die richtige Dossier-ID:\n' + \
                                          f'1. Öffnen Sie das Dossier in GUDAT\n' + \
                                          f'2. Schauen Sie in die Browser-Adresszeile\n' + \
                                          f'3. Die Dossier-ID steht nach "/dossier/" oder "/dossiers/"\n' + \
                                          f'   Beispiel: .../dossier/20472 → Dossier-ID ist "20472"\n\n' + \
                                          f'Bitte geben Sie die GUDAT Dossier-ID ein (nicht die Auftragsnummer).'
                        else:
                            error_message = f'Die eingegebene Dossier-ID "{manual_dossier_id}" wurde nicht in GUDAT gefunden.\n\n' + \
                                          f'Bitte prüfen Sie:\n' + \
                                          f'- Ist das die richtige Dossier-ID (oben links in GUDAT-UI oder in der Browser-Adresse nach "/dossier/")?\n' + \
                                          f'- Ist das Dossier möglicherweise gelöscht oder archiviert?\n' + \
                                          f'- Haben Sie die richtigen Berechtigungen?\n\n' + \
                                          f'⚠️ WICHTIG: Die Dossier-ID ist NICHT die Auftragsnummer ({order_number}), sondern eine separate Nummer in GUDAT.'
                        
                        return jsonify({
                            'success': False,
                            'error': f'Dossier-ID {manual_dossier_id} nicht in GUDAT gefunden',
                            'dossier_id_not_found': True,
                            'is_likely_order_number': is_likely_order_number,
                            'message': error_message,
                            'order_number': order_number
                        }), 200
                except Exception as e:
                    logger.warning(f"Fehler beim Holen von Anhängen mit manueller Dossier-ID: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            # Normale automatische Suche
            logger.info(f"🔍 Starte Anhänge-Suche für Auftrag {order_number}...")
            anhaenge_response = get_arbeitskarte_anhaenge(order_number, order_date=order_date, license_plate=license_plate, vin=vin)
            logger.info(f"🔍 Anhänge-Response erhalten: success={anhaenge_response.get('success') if anhaenge_response else 'None'}, anhaenge_count={len(anhaenge_response.get('anhaenge', [])) if anhaenge_response else 0}")
            
            if anhaenge_response and anhaenge_response.get('success'):
                anhaenge = anhaenge_response.get('anhaenge', [])
                dossier_id = anhaenge_response.get('dossier_id')
                gudat_session = anhaenge_response.get('gudat_session')
                message = anhaenge_response.get('message', '')
                logger.info(f"✅ Anhänge-Response: {len(anhaenge)} Anhänge, dossier_id={dossier_id}, gudat_session={'vorhanden' if gudat_session else 'None'}, message='{message}'")
                
                # TAG 212: Hole Diagnose-Informationen VOR PDF-Generierung, falls Dossier gefunden wurde
                gudat_has_tasks = daten.get('gudat') and daten.get('gudat', {}).get('tasks')
                logger.info(f"🔍 Diagnose-Check für Auftrag {order_number}: dossier_id={dossier_id}, gudat_session={'vorhanden' if gudat_session else 'None'}, gudat_existiert={'Ja' if daten.get('gudat') else 'Nein'}, gudat_has_tasks={'Ja' if gudat_has_tasks else 'Nein'}")
                
                if dossier_id and gudat_session and not gudat_has_tasks:
                    logger.info(f"⚠️ Dossier {dossier_id} in Anhänge-Suche gefunden, aber keine Diagnose-Informationen in hole_arbeitskarte_daten(). Hole nachträglich...")
                    try:
                        # TAG 212: Erstelle neue Session für Diagnose-Query (gudat_session kann abgelaufen sein)
                        from tools.gudat_client import GudatClient
                        client_diag = GudatClient(GUDAT_CONFIG['username'], GUDAT_CONFIG['password'])
                        if not client_diag.login():
                            logger.warning(f"⚠️ Fehler beim Login für Diagnose-Query")
                            raise Exception("GUDAT-Login fehlgeschlagen")
                        
                        base_url = client_diag.BASE_URL
                        xsrf_token = client_diag._get_xsrf()
                        
                        # TAG 212: Query wie in GUDAT UI - holt Tasks OHNE workshopTaskPackage
                        # (Tasks in Packages werden separat über workshopTaskPackages geholt)
                        query_dossier = """
                        query GetDossierDrawerData($id: ID!) {
                          dossier(id: $id) {
                            id
                            note
                        orders {
                          id
                          number
                          note
                        }
                        workshopTasks(
                              where: {HAS: {relation: "workshopTaskPackage", amount: 0, operator: EQ, condition: {column: ID, operator: IS_NOT_NULL}}}
                            ) {
                              id
                              description
                              work_load
                              work_state
                              order {
                                id
                                number
                              }
                            }
                            workshopTaskPackages {
                              id
                              workshopTasks {
                                id
                                description
                                work_load
                                work_state
                                order {
                                  id
                                  number
                                }
                              }
                            }
                          }
                        }
                        """
                        
                        response = client_diag.session.post(
                            f"{base_url}/graphql",
                            json={"operationName": "GetDossierDrawerData", "query": query_dossier, "variables": {"id": str(dossier_id)}},
                            headers={
                                'Accept': 'application/json',
                                'X-XSRF-TOKEN': xsrf_token,
                                'Content-Type': 'application/json'
                            }
                        )
                        
                        # TAG 212: Prüfe Response-Status und Content-Type vor JSON-Parsing
                        if response.status_code != 200:
                            logger.error(f"⚠️ GraphQL-Response Status {response.status_code} für Dossier {dossier_id}")
                            raise Exception(f"GraphQL-Request fehlgeschlagen: Status {response.status_code}")
                        
                        content_type = response.headers.get('Content-Type', '')
                        if 'application/json' not in content_type:
                            logger.error(f"⚠️ GraphQL-Response ist nicht JSON (Content-Type: {content_type}) für Dossier {dossier_id}")
                            logger.error(f"⚠️ Response-Text (erste 500 Zeichen): {response.text[:500]}")
                            raise Exception(f"GraphQL-Response ist nicht JSON (Content-Type: {content_type})")
                        
                        try:
                            data = response.json()
                        except ValueError as e:
                            logger.error(f"⚠️ JSON-Parsing-Fehler für Dossier {dossier_id}: {e}")
                            logger.error(f"⚠️ Response-Text (erste 500 Zeichen): {response.text[:500]}")
                            raise Exception(f"JSON-Parsing fehlgeschlagen: {e}")
                        
                        logger.info(f"🔍 GraphQL-Response für Dossier {dossier_id}: data.keys()={list(data.keys())}, errors={'vorhanden' if 'errors' in data else 'keine'}, error={'vorhanden' if 'error' in data else 'keine'}")
                        
                        # Prüfe auf Fehler (sowohl 'errors' als auch 'error')
                        if 'errors' in data:
                            logger.warning(f"⚠️ GraphQL-Fehler beim Holen von Diagnose-Informationen: {data.get('errors')}")
                        elif 'error' in data:
                            logger.warning(f"⚠️ GraphQL-Error beim Holen von Diagnose-Informationen: {data.get('error')}")
                        elif 'data' in data:
                            dossier = data.get('data', {}).get('dossier')
                            logger.info(f"🔍 Dossier aus Response: {'vorhanden' if dossier else 'None'}")
                            if dossier:
                                # TAG 212: Hole Tasks aus beiden Quellen:
                                # 1. workshopTasks (ohne Package)
                                # 2. workshopTaskPackages.workshopTasks (in Packages)
                                all_tasks = dossier.get('workshopTasks', [])
                                
                                # Hole auch Tasks aus Packages
                                packages = dossier.get('workshopTaskPackages', [])
                                for package in packages:
                                    package_tasks = package.get('workshopTasks', [])
                                    all_tasks.extend(package_tasks)
                                
                                logger.info(f"🔍 Dossier {dossier_id}: {len(dossier.get('workshopTasks', []))} Tasks ohne Package, {sum(len(p.get('workshopTasks', [])) for p in packages)} Tasks in Packages, gesamt: {len(all_tasks)} Tasks")
                                
                                # Filtere Tasks nach Auftragsnummer
                                filtered_tasks = []
                                for task in all_tasks:
                                    task_order = task.get('order')
                                    if task_order:
                                        task_order_number = task_order.get('number')
                                        if task_order_number and str(task_order_number).strip() == str(order_number).strip():
                                            filtered_tasks.append(task)
                                    # Fallback: Wenn kein order-Feld, übernehme alle Tasks wenn nur ein Auftrag im Dossier
                                    elif len(dossier.get('orders', [])) == 1:
                                        filtered_tasks.append(task)
                                
                                logger.info(f"🔍 Nach Filterung: {len(filtered_tasks)} Tasks für Auftrag {order_number}")
                                
                                tasks_with_desc = [t for t in filtered_tasks if t.get('description')]
                                logger.info(f"🔍 Tasks mit description: {len(tasks_with_desc)} von {len(filtered_tasks)}")
                                
                                if tasks_with_desc:
                                    logger.info(f"✅ Diagnose-Informationen nachträglich geholt: {len(tasks_with_desc)} Tasks mit description")
                                    # Füge Diagnose-Informationen zu daten hinzu
                                    if not daten.get('gudat'):
                                        daten['gudat'] = {}
                                    daten['gudat']['dossier_id'] = dossier.get('id')
                                    daten['gudat']['tasks'] = [
                                        {
                                            'task_id': task.get('id'),
                                            'description': task.get('description'),
                                            'work_load': task.get('work_load'),
                                            'work_state': task.get('work_state')
                                        } for task in tasks_with_desc
                                    ]
                                    logger.info(f"✅ Diagnose-Informationen zu daten hinzugefügt, PDF wird mit Diagnose-Informationen generiert")
                                else:
                                    # Fallback: dossier.note, order.note oder Locosoft job_beschreibung
                                    fallback_desc = None
                                    diagnose_quelle = None
                                    dossier_note = dossier.get('note')
                                    if dossier_note and dossier_note.strip():
                                        fallback_desc = dossier_note.strip()
                                        diagnose_quelle = 'gudat_dossier'
                                    if not fallback_desc:
                                        for ord_obj in dossier.get('orders', []):
                                            if str(ord_obj.get('number', '')).strip() == str(order_number).strip():
                                                onote = ord_obj.get('note')
                                                if onote and onote.strip():
                                                    fallback_desc = onote.strip()
                                                    diagnose_quelle = 'gudat_order'
                                                    break
                                    if not fallback_desc:
                                        job_beschr = (daten.get('locosoft') or {}).get('auftrag', {}).get('job_beschreibung')
                                        if job_beschr and str(job_beschr).strip():
                                            fallback_desc = str(job_beschr).strip()
                                            diagnose_quelle = 'locosoft'
                                    if fallback_desc:
                                        if not daten.get('gudat'):
                                            daten['gudat'] = {}
                                        daten['gudat']['dossier_id'] = dossier.get('id')
                                        daten['gudat']['tasks'] = [
                                            {'task_id': None, 'description': fallback_desc, 'work_load': None, 'work_state': None}
                                        ]
                                        daten['gudat']['diagnose_quelle'] = diagnose_quelle
                                        logger.info(f"✅ Diagnose-Fallback nachträglich gesetzt (Quelle: {diagnose_quelle})")
                                    else:
                                        logger.warning(f"⚠️ Dossier {dossier_id} gefunden, aber keine Tasks mit description")
                    except Exception as e:
                        logger.error(f"⚠️ Fehler beim Nachholen von Diagnose-Informationen: {e}")
                        import traceback
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        traceback.print_exc()
                        # TAG 212: Fehler beim Nachholen von Diagnose-Informationen ist nicht kritisch
                        # - Garantieakte kann trotzdem erstellt werden (ohne Diagnose-Informationen)
                        # - Exception wird nicht weitergeworfen, damit der Workflow fortgesetzt werden kann
                
                if not dossier_id:
                    dossier_not_found = True
                    logger.warning(f"⚠️ Kein Dossier gefunden für Auftrag {order_number} - keine Anhänge verfügbar")
            else:
                dossier_not_found = True
                logger.warning(f"Anhänge-Response fehlgeschlagen oder nicht erfolgreich: {anhaenge_response}")
        
        # 3. Generiere Arbeitskarte-PDF (mit Diagnose-Informationen, falls vorhanden)
        arbeitskarte_pdf = generate_arbeitskarte_pdf(daten)
        
        # 4. Hole Terminblatt
        terminblatt_data = None
        terminblatt_pdf = None
        
        if dossier_id and gudat_session:
            try:
                # Verwende bereits vorhandene Session aus anhaenge_response
                query_dossier = """
                query GetDossierAttachments($id: ID!) {
                  dossier(id: $id) {
                    id
                    documents {
                      id
                      name
                      file_type
                    }
                  }
                }
                """
                
                # Hole Base-URL aus GUDAT-Client
                from tools.gudat_client import GudatClient
                client_temp = GudatClient(GUDAT_CONFIG['username'], GUDAT_CONFIG['password'])
                base_url = client_temp.BASE_URL
                
                response = gudat_session.post(
                    f"{base_url}/graphql",
                    json={"operationName": "GetDossierAttachments", "query": query_dossier, "variables": {"id": str(dossier_id)}},
                    headers={
                        'Accept': 'application/json',
                        'X-XSRF-TOKEN': client_temp._get_xsrf(),
                        'Content-Type': 'application/json'
                    }
                )
                
                data = response.json()
                if 'errors' not in data:
                    dossier = data.get('data', {}).get('dossier')
                    if dossier:
                        documents = dossier.get('documents', [])
                        for att in documents:
                            if att.get('file_type') == 'application/pdf' and 'termin' in att.get('name', '').lower():
                                terminblatt_data = att
                                # Terminblatt-PDF herunterladen
                                from api.arbeitskarte_vollstaendig import download_document
                                terminblatt_pdf = download_document(att.get('id'), gudat_session)
                                if terminblatt_pdf:
                                    logger.info(f"Terminblatt heruntergeladen: {att.get('name')} ({len(terminblatt_pdf) / 1024:.1f} KB)")
                                else:
                                    logger.warning(f"Terminblatt konnte nicht heruntergeladen werden: {att.get('name')}")
                                break
            except Exception as e:
                logger.warning(f"Fehler beim Holen des Terminblatts: {e}")
                import traceback
                traceback.print_exc()
        
        # 5. Kundenname (TAG 189: Fix für None-Werte)
        kunde_name_raw = daten.get('locosoft', {}).get('kunde', {}).get('name')
        kunde_name = kunde_name_raw if kunde_name_raw else f'Kunde_{order_number}'
        logger.info(f"Kundenname für Auftrag {order_number}: '{kunde_name}' (raw: {kunde_name_raw})")
        
        # 6. Brand-Erkennung (TAG 189: Automatisch aus subsidiary)
        brand = daten.get('brand', 'hyundai')  # Default: hyundai für Rückwärtskompatibilität
        
        # TAG 189: Wenn kein Dossier gefunden wurde, gebe Hinweis zurück (nicht Fehler!)
        if dossier_not_found and not manual_dossier_id:
            return jsonify({
                'success': False,
                'error': 'Dossier nicht gefunden',
                'dossier_not_found': True,
                'message': f'Kein Dossier in GUDAT für Auftrag {order_number} gefunden. Bitte Dossier-ID manuell eingeben.',
                'order_number': order_number,
                'license_plate': license_plate,
                'vin': vin
            }), 200  # 200 statt 400, damit Frontend unterscheiden kann
        
        # 7. Erstelle vollständige Akte
        try:
            result = create_garantieakte_vollstaendig(
                order_number=order_number,
                kunde_name=kunde_name,
                arbeitskarte_pdf=arbeitskarte_pdf,
                anhaenge=anhaenge,
                terminblatt_data=terminblatt_data,
                terminblatt_pdf=terminblatt_pdf,
                gudat_session=gudat_session,
                brand=brand  # TAG 189: Brand-Parameter
            )
            
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'message': f'Garantieakte erfolgreich gespeichert',
                    'ordner_path': result.get('ordner_path'),
                    'windows_path': result.get('windows_path'),
                    'dateien': result.get('dateien'),
                    'anzahl_dateien': result.get('anzahl_dateien')
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Unbekannter Fehler')
                }), 500
        except Exception as inner_e:
            logger.error(f"Fehler beim Erstellen der Garantieakte: {inner_e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'Fehler beim Erstellen der Garantieakte: {str(inner_e)}'
            }), 500
    
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Garantieakte: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Traceback: {error_traceback}")
        traceback.print_exc()
        # TAG 212: Stelle sicher, dass immer JSON zurückgegeben wird (nicht HTML)
        try:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        except Exception as json_error:
            # Fallback: Falls jsonify auch fehlschlägt, gebe einfache JSON-Response zurück
            logger.error(f"Kritischer Fehler: jsonify fehlgeschlagen: {json_error}")
            from flask import Response
            return Response(
                f'{{"success": false, "error": "{str(e).replace(chr(34), chr(39))}"}}',
                mimetype='application/json',
                status=500
            )


@bp.route('/<int:order_number>/vollstaendig', methods=['GET'])
@login_required
def get_arbeitskarte_vollstaendig(order_number):
    """
    Generiert vollständige Garantieakte mit Arbeitskarte, Terminblatt und Bildern.
    
    Returns:
        PDF-Datei (max. 20MB)
    """
    try:
        # 1. Hole Arbeitskarte-Daten
        daten = hole_arbeitskarte_daten(order_number)
        
        if not daten:
            return jsonify({
                'success': False,
                'error': f'Auftrag {order_number} nicht gefunden'
            }), 404
        
        # 2. Hole Bilder
        bilder_response = get_arbeitskarte_bilder(order_number)
        bilder = []
        dossier_id = None
        
        if bilder_response and isinstance(bilder_response, dict) and bilder_response.get('success'):
            bilder = bilder_response.get('bilder', [])
            dossier_id = bilder_response.get('dossier_id')
        
        # 3. Hole Terminblatt
        terminblatt = None
        if dossier_id:
            try:
                client = GudatClient(GUDAT_CONFIG['username'], GUDAT_CONFIG['password'])
                if client.login():
                    query_dossier = """
                    query GetDossierAttachments($id: ID!) {
                      dossier(id: $id) {
                        id
                        documents {
                          id
                          name
                          file_name
                          mime_type
                          size
                          url
                        }
                      }
                    }
                    """
                    
                    response = client.session.post(
                        f"{client.BASE_URL}/graphql",
                        json={"operationName": "GetDossierAttachments", "query": query_dossier, "variables": {"id": str(dossier_id)}},
                        headers={
                            'Accept': 'application/json',
                            'X-XSRF-TOKEN': client._get_xsrf(),
                            'Content-Type': 'application/json'
                        }
                    )
                    
                    data = response.json()
                    if 'errors' not in data:
                        dossier = data.get('data', {}).get('dossier')
                        if dossier:
                            documents = dossier.get('documents', [])
                            for att in documents:
                                if att.get('file_type') == 'application/pdf' and 'termin' in att.get('name', '').lower():
                                    terminblatt = att
                                    break
            except Exception as e:
                logger.warning(f"Fehler beim Holen des Terminblatts: {e}")
        
        # 4. Generiere vollständige Akte
        from api.arbeitskarte_vollstaendig import generate_vollstaendige_akte_pdf
        
        # Verwende GUDAT-Session für Bild-Downloads (falls vorhanden)
        gudat_session = None
        try:
            if bilder and client and hasattr(client, '_logged_in') and client._logged_in:
                gudat_session = client.session
        except:
            pass
        
        pdf_bytes = generate_vollstaendige_akte_pdf(
            daten,
            bilder=bilder,
            terminblatt=terminblatt,
            gudat_session=gudat_session
        )
        
        size_mb = len(pdf_bytes) / 1024 / 1024
        
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Garantieakte_{order_number}.pdf'
        )
    
    except Exception as e:
        logger.error(f"Fehler beim Generieren der vollständigen Akte: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
