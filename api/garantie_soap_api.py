"""
Garantie SOAP API - Schreiben von Arbeiten in Locosoft
======================================================
TAG 173: BASICA00, TT-Zeit, RQ0 per SOAP auf Auftrag schreiben
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

bp = Blueprint('garantie_soap_api', __name__, url_prefix='/api/garantie/soap')

def get_soap_client():
    """Lädt den Locosoft SOAP-Client."""
    try:
        from tools.locosoft_soap_client import get_soap_client as _get_client
        return _get_client()
    except Exception as e:
        logger.error(f"SOAP-Client nicht verfügbar: {e}")
        return None

def read_work_order_details(order_number: int) -> Optional[Dict]:
    """Liest Auftragsdetails aus Locosoft."""
    client = get_soap_client()
    if not client:
        return None
    
    try:
        return client.read_work_order_details(order_number)
    except Exception as e:
        logger.error(f"Fehler beim Lesen von Auftrag {order_number}: {e}")
        return None

def add_labour_to_work_order(
    order_number: int,
    operation_code: str,
    time_units: float,
    description: str,
    charge_type: int = 60,  # Garantie
    labour_type: str = 'G'  # Garantie
) -> Dict[str, Any]:
    """
    Fügt eine Arbeitsposition zu einem Auftrag hinzu.
    
    Args:
        order_number: Auftragsnummer
        operation_code: Arbeitsnummer (z.B. 'BASICA00', '28257RTT')
        time_units: AW (Arbeitseinheiten)
        description: Beschreibung
        charge_type: 60 = Garantie
        labour_type: 'G' = Garantie
    
    Returns:
        Dict mit 'success', 'message', 'labour_number'
    """
    client = get_soap_client()
    if not client:
        return {
            'success': False,
            'message': 'SOAP-Client nicht verfügbar'
        }
    
    # 1. Aktuellen Auftrag lesen
    work_order = read_work_order_details(order_number)
    if not work_order:
        return {
            'success': False,
            'message': f'Auftrag {order_number} nicht gefunden'
        }
    
    # 2. Neue Arbeitsposition erstellen
    # TODO: Struktur von writeWorkOrderDetails prüfen
    # Vermutlich müssen wir den kompletten Auftrag mit allen Positionen senden
    # und die neue Position hinzufügen
    
    try:
        # Neue Position zur Liste hinzufügen
        if 'labours' not in work_order:
            work_order['labours'] = []
        
        # Nächste Position-Nummer finden
        max_position = 0
        if work_order.get('labours'):
            for labour in work_order['labours']:
                if isinstance(labour, dict) and 'orderPosition' in labour:
                    max_position = max(max_position, labour.get('orderPosition', 0))
        
        new_position = max_position + 1
        
        # Neue Arbeitsposition
        new_labour = {
            'orderPosition': new_position,
            'orderPositionLine': 1,
            'operationCode': operation_code,
            'timeUnits': time_units,
            'description': description,
            'chargeType': charge_type,
            'labourType': labour_type,
            'isInvoiced': False
        }
        
        work_order['labours'].append(new_labour)
        
        # 3. Auftrag aktualisieren
        result = client.write_work_order_details(work_order)
        
        if result.get('success'):
            return {
                'success': True,
                'message': f'Arbeitsposition {operation_code} erfolgreich hinzugefügt',
                'labour_number': new_position,
                'operation_code': operation_code,
                'time_units': time_units
            }
        else:
            return {
                'success': False,
                'message': result.get('message', 'Fehler beim Schreiben in Locosoft')
            }
            
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen von Arbeitsposition: {e}")
        return {
            'success': False,
            'message': f'Fehler: {str(e)}'
        }

@bp.route('/add-basica00/<int:order_number>', methods=['POST'])
@login_required
def add_basica00(order_number):
    """
    Fügt BASICA00 (GDS-Grundprüfung) zu einem Auftrag hinzu.
    
    POST /api/garantie/soap/add-basica00/220345
    """
    result = add_labour_to_work_order(
        order_number=order_number,
        operation_code='BASICA00',
        time_units=1.0,
        description='GDS-Grundprüfung',
        charge_type=60,  # Garantie
        labour_type='G'  # Garantie
    )
    
    if result.get('success'):
        return jsonify({
            'success': True,
            'message': 'BASICA00 erfolgreich hinzugefügt',
            'data': result
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': result.get('message', 'Fehler beim Hinzufügen von BASICA00')
        }), 400

@bp.route('/add-tt-zeit/<int:order_number>', methods=['POST'])
@login_required
def add_tt_zeit(order_number):
    """
    Fügt TT-Zeit zu einem Auftrag hinzu.
    
    POST /api/garantie/soap/add-tt-zeit/220345
    Body: {
        "time_units": 0.8,
        "operation_code": "28257RTT",  // Optional, wird generiert wenn nicht angegeben
        "description": "TT-Zeit Diagnose"
    }
    """
    data = request.get_json() or {}
    
    time_units = float(data.get('time_units', 0))
    operation_code = data.get('operation_code')
    description = data.get('description', 'TT-Zeit')
    
    if time_units <= 0:
        return jsonify({
            'success': False,
            'message': 'time_units muss > 0 sein'
        }), 400
    
    # Wenn keine operation_code angegeben, generiere eine
    if not operation_code:
        # TODO: Schadenverursachendes Teil aus Auftrag holen
        # Für jetzt: Generische TT-Zeit
        operation_code = f"TT{int(time_units * 10)}RTT"  # Beispiel: TT8RTT für 0.8 AW
    
    result = add_labour_to_work_order(
        order_number=order_number,
        operation_code=operation_code,
        time_units=time_units,
        description=description,
        charge_type=60,  # Garantie
        labour_type='G'  # Garantie
    )
    
    if result.get('success'):
        return jsonify({
            'success': True,
            'message': 'TT-Zeit erfolgreich hinzugefügt',
            'data': result
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': result.get('message', 'Fehler beim Hinzufügen von TT-Zeit')
        }), 400

@bp.route('/add-rq0/<int:order_number>', methods=['POST'])
@login_required
def add_rq0(order_number):
    """
    Fügt RQ0 (Erweiterte Diagnose) zu einem Auftrag hinzu.
    
    POST /api/garantie/soap/add-rq0/220345
    """
    result = add_labour_to_work_order(
        order_number=order_number,
        operation_code='RQ0',
        time_units=3.0,
        description='Erweiterte Diagnose',
        charge_type=60,  # Garantie
        labour_type='G'  # Garantie
    )
    
    if result.get('success'):
        return jsonify({
            'success': True,
            'message': 'RQ0 erfolgreich hinzugefügt',
            'data': result
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': result.get('message', 'Fehler beim Hinzufügen von RQ0')
        }), 400

@bp.route('/test-connection', methods=['GET'])
@login_required
def test_connection():
    """Testet die SOAP-Verbindung."""
    client = get_soap_client()
    if not client:
        return jsonify({
            'success': False,
            'message': 'SOAP-Client nicht verfügbar'
        }), 503
    
    try:
        result = client.test_connection()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        }), 500
