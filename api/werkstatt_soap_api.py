"""
Werkstatt SOAP API
==================
TAG 173: Stempelzeiten-Verteilung per SOAP auf Arbeitszeilen
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required
from decorators.auth_decorators import login_required
import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.locosoft_soap_client import LocosoftSOAPClient
from utils.locosoft_helpers import get_locosoft_connection

bp = Blueprint('werkstatt_soap', __name__, url_prefix='/api/werkstatt/soap')
logger = logging.getLogger(__name__)


@bp.route('/verteile-stempelzeiten/<int:order_number>', methods=['POST'])
@login_required
def verteile_stempelzeiten(order_number):
    """
    Verteilt unzugeordnete Stempelzeiten auf Arbeitszeilen per SOAP.
    
    Funktioniert für alle Aufträge, nicht nur Garantie.
    
    Args:
        order_number: Auftragsnummer
        
    Returns:
        JSON mit Erfolg/Fehler und Details
    """
    try:
        # 1. Hole unzugeordnete Stempelzeiten aus Locosoft
        conn = get_locosoft_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
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
              AND (t.order_position IS NULL OR t.order_position_line IS NULL)
              AND t.end_time IS NOT NULL
            ORDER BY t.start_time
        """, [order_number])
        
        unzugeordnete = cursor.fetchall()
        
        if not unzugeordnete:
            conn.close()
            return jsonify({
                'success': True,
                'message': 'Keine unzugeordneten Stempelzeiten gefunden',
                'verteilt': 0
            })
        
        # 2. Hole Arbeitspositionen für Zuordnung
        cursor.execute("""
            SELECT 
                l.order_position,
                l.order_position_line,
                l.mechanic_no,
                l.labour_operation_id,
                l.text_line
            FROM labours l
            WHERE l.order_number = %s
              AND l.mechanic_no IS NOT NULL
            ORDER BY l.order_position, l.order_position_line
        """, [order_number])
        
        positionen = cursor.fetchall()
        
        conn.close()
        
        # 3. SOAP-Client initialisieren
        client = LocosoftSOAPClient()
        
        verteilt = 0
        fehler = []
        
        # 4. Für jede unzugeordnete Stempelzeit
        for st in unzugeordnete:
            employee_number = st[0]
            start_time = st[2]
            end_time = st[3]
            
            # Finde passende Position (gleicher Mechaniker)
            passende_position = None
            for pos in positionen:
                if pos[2] == employee_number:  # mechanic_no
                    passende_position = pos
                    break
            
            if not passende_position:
                fehler.append({
                    'employee': st[1],
                    'start': str(start_time),
                    'message': 'Keine passende Position gefunden'
                })
                continue
            
            # 5. Verteile Stempelzeit auf Position per SOAP
            try:
                result = client.write_work_order_times({
                    'workOrderNumber': order_number,
                    'mechanicId': employee_number,
                    'startTimestamp': start_time,
                    'endTimestamp': end_time,
                    'isFinished': True,
                    'workOrderLineNumber': [
                        passende_position[0] * 1000 + passende_position[1]  # order_position * 1000 + order_position_line
                    ]
                })
                
                if result.get('success'):
                    verteilt += 1
                else:
                    fehler.append({
                        'employee': st[1],
                        'start': str(start_time),
                        'message': result.get('message', 'Unbekannter Fehler')
                    })
            except Exception as e:
                logger.error(f"Fehler beim Verteilen von Stempelzeit: {e}")
                fehler.append({
                    'employee': st[1],
                    'start': str(start_time),
                    'message': str(e)
                })
        
        return jsonify({
            'success': True,
            'message': f'{verteilt} von {len(unzugeordnete)} Stempelzeiten verteilt',
            'verteilt': verteilt,
            'gesamt': len(unzugeordnete),
            'fehler': fehler
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Verteilen von Stempelzeiten: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/stempelzeiten-status/<int:order_number>', methods=['GET'])
@login_required
def stempelzeiten_status(order_number):
    """
    Zeigt Status der Stempelzeiten-Verteilung für einen Auftrag.
    
    Returns:
        JSON mit zugeordneten und unzugeordneten Stempelzeiten
    """
    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor()
        
        # Zugeordnete Stempelzeiten (DEDUPLIZIERT - sekundengleiche Stempelzeiten desselben Mechanikers nur einmal)
        cursor.execute("""
            SELECT DISTINCT ON (t.employee_number, t.order_number, t.start_time, t.end_time)
                t.employee_number,
                eh.name as mechaniker,
                t.start_time,
                t.end_time,
                t.duration_minutes,
                t.order_position,
                t.order_position_line
            FROM times t
            LEFT JOIN employees_history eh ON t.employee_number = eh.employee_number 
                AND eh.is_latest_record = true
            WHERE t.order_number = %s
              AND t.type = 2
              AND t.end_time IS NOT NULL
              AND t.order_position IS NOT NULL
              AND t.order_position_line IS NOT NULL
            ORDER BY t.employee_number, t.order_number, t.start_time, t.end_time, t.duration_minutes DESC
        """, [order_number])
        
        zugeordnet = cursor.fetchall()
        
        # Unzugeordnete Stempelzeiten (DEDUPLIZIERT - sekundengleiche Stempelzeiten desselben Mechanikers nur einmal)
        cursor.execute("""
            SELECT DISTINCT ON (t.employee_number, t.order_number, t.start_time, t.end_time)
                t.employee_number,
                eh.name as mechaniker,
                t.start_time,
                t.end_time,
                t.duration_minutes
            FROM times t
            LEFT JOIN employees_history eh ON t.employee_number = eh.employee_number 
                AND eh.is_latest_record = true
            WHERE t.order_number = %s
              AND t.type = 2
              AND t.end_time IS NOT NULL
              AND (t.order_position IS NULL OR t.order_position_line IS NULL)
            ORDER BY t.employee_number, t.order_number, t.start_time, t.end_time, t.duration_minutes DESC
        """, [order_number])
        
        unzugeordnet = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'order_number': order_number,
            'zugeordnet': [
                {
                    'employee': z[1],
                    'start': str(z[2]),
                    'end': str(z[3]),
                    'duration_minutes': z[4],
                    'position': f"{z[5]}.{z[6]}"
                } for z in zugeordnet
            ],
            'unzugeordnet': [
                {
                    'employee': u[1],
                    'start': str(u[2]),
                    'end': str(u[3]),
                    'duration_minutes': u[4]
                } for u in unzugeordnet
            ],
            'anzahl_zugeordnet': len(zugeordnet),
            'anzahl_unzugeordnet': len(unzugeordnet)
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Stempelzeiten-Status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
