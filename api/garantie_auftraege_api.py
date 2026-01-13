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

from api.db_utils import locosoft_session
from api.standort_utils import BETRIEB_NAMEN

logger = logging.getLogger(__name__)

bp = Blueprint('garantie_auftraege_api', __name__, url_prefix='/api/garantie/auftraege')


def get_garantieakte_metadata(order_number: int, kunde_name: str) -> dict:
    """
    Prüft ob Garantieakte existiert und holt Metadaten.
    
    Returns:
        {
            'existiert': bool,
            'erstelldatum': str oder None,
            'ersteller': str oder None,
            'ordner_path': str oder None,
            'windows_path': str oder None
        }
    """
    from api.garantieakte_workflow import BASE_PATH_OPTIONS, FALLBACK_PATH, sanitize_filename
    
    # Prüfe verschiedene Pfade
    base_path = None
    for path_option in BASE_PATH_OPTIONS:
        base_dir = os.path.dirname(path_option)
        if os.path.exists(base_dir):
            base_path = path_option
            break
    
    if not base_path:
        base_path = FALLBACK_PATH
    
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
    
    # Windows-Pfad generieren
    windows_path = None
    if '/hyundai-garantie' in ordner_path:
        windows_path = ordner_path.replace('/mnt/hyundai-garantie', r'\\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie')
        windows_path = windows_path.replace('/', '\\')
    elif '/buchhaltung/DigitalesAutohaus' in ordner_path:
        windows_path = ordner_path.replace('/mnt/buchhaltung/DigitalesAutohaus', r'\\srvrdb01\Allgemein\DigitalesAutohaus')
        windows_path = windows_path.replace('/', '\\')
    elif '/DigitalesAutohaus' in ordner_path:
        windows_path = ordner_path.replace('/mnt/DigitalesAutohaus', r'\\srvrdb01\Allgemein\DigitalesAutohaus')
        windows_path = windows_path.replace('/', '\\')
    elif '/greiner-portal-sync' in ordner_path:
        windows_path = ordner_path.replace('/mnt/greiner-portal-sync', r'\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server')
        windows_path = windows_path.replace('/', '\\')
    else:
        windows_path = ordner_path.replace('/', '\\')
    
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
                     'true' = nur komplett gestempelte (offen_aw = 0)
                     'false' = alle (auch noch nicht fertige)
    
    Returns:
        Liste von Aufträgen mit:
        - Auftragsdaten (Nummer, Kunde, Fahrzeug, etc.)
        - Garantieakte-Status (existiert, erstelldatum, ersteller)
    """
    try:
        from flask import request
        marke_filter = request.args.get('marke', 'alle').lower()
        fertig_filter = request.args.get('fertig', 'false').lower() == 'true'
        
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
                )
                SELECT
                    g.auftrag_nr,
                    g.betrieb,
                    g.order_date,
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
                WHERE g.ist_garantie = true
                  AND g.wird_bearbeitet = true
            """
            
            # Filter nach Betrieb hinzufügen
            if betriebe_filter:
                placeholders = ','.join(['%s'] * len(betriebe_filter))
                query += f" AND g.betrieb IN ({placeholders})"
            
            # Filter nach "fertig" hinzufügen (komplett gestempelt = gestempelt_aw >= total_aw)
            # Toleranz: 95% reicht (wegen Rundungen)
            if fertig_filter:
                query += """ AND CASE 
                        WHEN st.gestempelt_min IS NULL THEN 0.0
                        ELSE st.gestempelt_min / 6.0
                    END >= COALESCE(s.total_aw, 0) * 0.95"""
            
            query += " ORDER BY g.order_date DESC"
            
            if betriebe_filter:
                cursor.execute(query, betriebe_filter)
            else:
                cursor.execute(query)
            auftraege = cursor.fetchall()
            
            # Für jeden Auftrag: Prüfe Garantieakte-Status
            result = []
            for auftrag in auftraege:
                auftrag_nr = auftrag['auftrag_nr']
                kunde = auftrag['kunde'] or f'Kunde_{auftrag_nr}'
                
                # Prüfe ob Garantieakte existiert
                akte_info = get_garantieakte_metadata(auftrag_nr, kunde)
                
                result.append({
                    'auftrag_nr': auftrag_nr,
                    'betrieb': auftrag['betrieb'],
                    'betrieb_name': BETRIEB_NAMEN.get(auftrag['betrieb'], 'Unbekannt'),
                    'order_date': auftrag['order_date'].strftime('%Y-%m-%d') if auftrag['order_date'] else None,
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
                })
            
            return jsonify({
                'success': True,
                'auftraege': result,
                'anzahl': len(result),
                'filter': {
                    'marke': marke_filter,
                    'betriebe': betriebe_filter,
                    'fertig': fertig_filter
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
