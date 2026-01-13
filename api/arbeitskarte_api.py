"""
Arbeitskarte API
================
TAG 173: API-Endpoints für Arbeitskarte-Daten und PDF-Generierung
"""

from flask import Blueprint, jsonify, send_file
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
    
    # Auftragsdaten
    cursor.execute("""
        SELECT 
            o.number,
            o.order_date,
            o.order_taking_employee_no,
            eh_sb.name as serviceberater,
            o.vehicle_number,
            o.order_customer
        FROM orders o
        LEFT JOIN employees_history eh_sb ON o.order_taking_employee_no = eh_sb.employee_number 
            AND eh_sb.is_latest_record = true
        WHERE o.number = %s
    """, [order_number])
    
    auftrag = cursor.fetchone()
    if not auftrag:
        conn.close()
        return None
    
    # Kundendaten
    cursor.execute("""
        SELECT 
            cs.family_name,
            cs.first_name,
            cs.home_street,
            cs.zip_code,
            cs.home_city
        FROM customers_suppliers cs
        WHERE cs.customer_number = %s
    """, [auftrag[5]])
    
    kunde = cursor.fetchone()
    
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
    cursor.execute("""
        SELECT 
            v.license_plate,
            v.vin,
            v.first_registration_date,
            v.mileage_km,
            m.description as marke,
            mo.description as modell
        FROM vehicles v
        LEFT JOIN makes m ON v.make_number = m.make_number
        LEFT JOIN models mo ON v.make_number = mo.make_number AND v.model_code = mo.model_code
        WHERE v.internal_number = %s
    """, [auftrag[4]])
    
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
    
    # Stempelzeiten (DEDUPLIZIERT - gleiche start_time, end_time, employee_number nur einmal)
    cursor.execute("""
        SELECT DISTINCT ON (t.employee_number, t.start_time, t.end_time)
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
        ORDER BY t.employee_number, t.start_time, t.end_time, t.duration_minutes DESC
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
    
    conn.close()
    
    # GUDAT-Daten
    gudat_daten = None
    try:
        client = GudatClient(GUDAT_CONFIG['username'], GUDAT_CONFIG['password'])
        if client.login():
            from datetime import date
            target_date = date.today().isoformat()
            
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
                
                # Finde dossier_id
                dossier_id = None
                for task in tasks:
                    orders = task.get('dossier', {}).get('orders', [])
                    for order in orders:
                        if order.get('number') == str(order_number):
                            dossier_id = task.get('dossier', {}).get('id')
                            break
                
                if dossier_id:
                    # Hole vollständige Dossier-Daten
                    # Versuche zuerst mit comments, falls das fehlschlägt, verwende nur note
                    query_dossier = """
                    query GetDossierDrawerData($id: ID!) {
                      dossier(id: $id) {
                        id
                        note
                        comments {
                          id
                          text
                          created_at
                          user {
                            id
                            name
                          }
                        }
                        workshopTasks {
                          id
                          description
                          work_load
                          work_state
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
                    """
                    
                    # Fallback-Query ohne comments (falls Schema nicht unterstützt)
                    query_dossier_fallback = """
                    query GetDossierDrawerData($id: ID!) {
                      dossier(id: $id) {
                        id
                        note
                        workshopTasks {
                          id
                          description
                          work_load
                          work_state
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
                    
                    # Prüfe auf GraphQL-Fehler
                    if 'errors' in data:
                        logger.warning(f"GraphQL-Fehler beim Holen von Dossier-Daten (mit comments): {data['errors']}")
                        use_fallback = True
                    
                    # Falls Fehler, versuche Fallback-Query ohne comments
                    if use_fallback:
                        response = client.session.post(
                            f"{client.BASE_URL}/graphql",
                            json={"operationName": "GetDossierDrawerData", "query": query_dossier_fallback, "variables": {"id": str(dossier_id)}},
                            headers={
                                'Accept': 'application/json',
                                'X-XSRF-TOKEN': client._get_xsrf(),
                                'Content-Type': 'application/json'
                            }
                        )
                        data = response.json()
                        if 'errors' in data:
                            logger.error(f"GraphQL-Fehler auch bei Fallback-Query: {data['errors']}")
                    
                    dossier = data.get('data', {}).get('dossier')
                    
                    if dossier:
                        all_tasks = dossier.get('workshopTasks', [])
                        tasks_with_desc = [t for t in all_tasks if t.get('description')]
                        
                        # Sammle alle Rückfragen/Nachrichten
                        rueckfragen = []
                        
                        if not use_fallback:
                            # Dossier-Level Kommentare
                            dossier_comments = dossier.get('comments', [])
                            if dossier_comments:
                                for comment in dossier_comments:
                                    rueckfragen.append({
                                        'typ': 'Dossier',
                                        'text': comment.get('text', ''),
                                        'erstellt_am': comment.get('created_at', ''),
                                        'autor': comment.get('user', {}).get('name', 'Unbekannt')
                                    })
                            
                            # Task-Level Kommentare
                            for task in all_tasks:
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
                    else:
                        gudat_daten = None
    except Exception as e:
        print(f"GUDAT-Fehler: {e}")
        gudat_daten = None
    
    # Daten zusammenführen
    return {
        'order_number': order_number,
        'locosoft': {
            'auftrag': {
                'nummer': auftrag[0],
                'datum': str(auftrag[1]) if auftrag[1] else None,
                'serviceberater': auftrag[3],
                'serviceberater_nr': auftrag[2],
                'job_beschreibung': job_beschreibung
            },
            'kunde': {
                'name': f"{kunde[0]}, {kunde[1]}" if kunde and kunde[0] and kunde[1] else None,
                'adresse': f"{kunde[2]}, {kunde[3]} {kunde[4]}" if kunde and kunde[2] and kunde[3] and kunde[4] else None,
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


def _get_arbeitskarte_anhaenge_internal(order_number):
    """
    Interne Funktion: Holt ALLE Anhänge (Dokumente) aus GUDAT für einen Auftrag.
    Inkl. Bilder, PDFs (z.B. Locosoft-Auftrag mit Unterschrift), etc.
    
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
        
        # 1. Versuche zuerst heute
        target_date = date.today().isoformat()
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
            return {
                'success': False,
                'error': f"GraphQL-Fehler: {data['errors']}",
                'anhaenge': []
            }
        
        tasks = data.get('data', {}).get('workshopTasks', {}).get('data', [])
        
        # Finde dossier_id
        for task in tasks:
            orders = task.get('dossier', {}).get('orders', [])
            for order in orders:
                if order.get('number') == str(order_number):
                    dossier_id = task.get('dossier', {}).get('id')
                    break
        
        # 2. Falls nicht gefunden, suche in letzten 30 Tagen
        if not dossier_id:
            logger.info(f"Dossier für Auftrag {order_number} nicht heute gefunden, suche in letzten 30 Tagen...")
            start_date = (date.today() - timedelta(days=30)).isoformat()
            end_date = date.today().isoformat()
            
            variables = {
                "page": 1,
                "itemsPerPage": 500,  # Mehr Ergebnisse für erweiterte Suche
                "where": {
                    "AND": [
                        {"column": "START_DATE", "operator": "GTE", "value": start_date},
                        {"column": "START_DATE", "operator": "LTE", "value": end_date}
                    ]
                }
            }
            
            try:
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
                    for task in tasks:
                        orders = task.get('dossier', {}).get('orders', [])
                        for order in orders:
                            if order.get('number') == str(order_number):
                                dossier_id = task.get('dossier', {}).get('id')
                                logger.info(f"Dossier für Auftrag {order_number} in historischen Daten gefunden")
                                break
                        if dossier_id:
                            break
            except Exception as e:
                logger.warning(f"Fehler bei erweiterter GUDAT-Suche: {e}")
        
        if not dossier_id:
            return {
                'success': True,
                'message': f'Dossier für Auftrag {order_number} nicht gefunden',
                'anhaenge': []
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
                'anhaenge': []
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


def get_arbeitskarte_anhaenge(order_number):
    """
    Öffentliche Funktion: Holt ALLE Anhänge (Dokumente) aus GUDAT für einen Auftrag.
    Inkl. Bilder, PDFs (z.B. Locosoft-Auftrag mit Unterschrift), etc.
    
    Returns:
        Dict mit Liste aller Anhänge
    """
    return _get_arbeitskarte_anhaenge_internal(order_number)


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
    
    Returns:
        JSON mit Erfolg/Fehler und Pfaden
    """
    try:
        from api.garantieakte_workflow import create_garantieakte_vollstaendig
        from api.arbeitskarte_pdf import generate_arbeitskarte_pdf
        
        # 1. Hole Arbeitskarte-Daten
        daten = hole_arbeitskarte_daten(order_number)
        
        if not daten:
            return jsonify({
                'success': False,
                'error': f'Auftrag {order_number} nicht gefunden'
            }), 404
        
        # 2. Generiere Arbeitskarte-PDF (ohne Bilder)
        arbeitskarte_pdf = generate_arbeitskarte_pdf(daten)
        
        # 3. Hole ALLE Anhänge (Bilder, PDFs, etc.)
        anhaenge_response = get_arbeitskarte_anhaenge(order_number)
        anhaenge = []
        dossier_id = None
        gudat_session = None
        
        if anhaenge_response and anhaenge_response.get('success'):
            anhaenge = anhaenge_response.get('anhaenge', [])
            dossier_id = anhaenge_response.get('dossier_id')
            gudat_session = anhaenge_response.get('gudat_session')
        
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
        
        # 5. Kundenname
        kunde_name = daten.get('locosoft', {}).get('kunde', {}).get('name', f'Kunde_{order_number}')
        
        # 6. Erstelle vollständige Akte
        try:
            result = create_garantieakte_vollstaendig(
                order_number=order_number,
                kunde_name=kunde_name,
                arbeitskarte_pdf=arbeitskarte_pdf,
                anhaenge=anhaenge,
                terminblatt_data=terminblatt_data,
                terminblatt_pdf=terminblatt_pdf,
                gudat_session=gudat_session
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
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
