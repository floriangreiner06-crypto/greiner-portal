"""
Mobis Teilebezug API - Über Locosoft SOAP
==========================================
TAG 175: Teilebezug für Hyundai Garantie über Locosoft SOAP

Erkenntnis: Hyundai verwendet Locosoft SOAP auch für Workshop Automation!
Daher können wir über Locosoft SOAP auf Teile-Daten zugreifen.
"""

import logging
from typing import List, Dict, Optional
from flask import Blueprint, jsonify
from flask_login import login_required

logger = logging.getLogger(__name__)

bp = Blueprint('mobis_teilebezug', __name__, url_prefix='/api/mobis/teilebezug')

# Hyundai Original-Teile: parts_type 5, 6, 65
HYUNDAI_ORIGINAL_PARTS_TYPES = [5, 6, 65]


def get_soap_client():
    """Lädt den Locosoft SOAP-Client."""
    try:
        from tools.locosoft_soap_client import get_soap_client as _get_client
        return _get_client()
    except Exception as e:
        logger.error(f"SOAP-Client nicht verfügbar: {e}")
        return None


def get_hyundai_original_parts_for_order(order_number: int) -> List[Dict]:
    """
    Ruft Hyundai Original-Teile für einen Auftrag ab.
    
    Versucht zuerst über Locosoft SOAP, falls nicht verfügbar über DB.
    
    Args:
        order_number: Auftragsnummer
    
    Returns:
        Liste von Teilen mit:
        - part_number: Teilenummer
        - description: Beschreibung
        - amount: Menge
        - sum: Betrag
        - parts_type: 5, 6 oder 65 (Hyundai Original)
        - is_hyundai_original: True
    """
    # Versuche 1: Locosoft SOAP
    client = get_soap_client()
    if client:
        try:
            work_order = client.read_work_order_details(order_number)
            if work_order:
                parts = work_order.get('parts', []) or work_order.get('Parts', [])
                
                if parts:
                    hyundai_parts = []
                    for part in parts:
                        # Verschiedene mögliche Feldnamen
                        parts_type = (
                            part.get('parts_type') or 
                            part.get('partsType') or 
                            part.get('part_type') or
                            part.get('partType')
                        )
                        
                        # Hyundai Original: parts_type = 5, 6, 65
                        if parts_type in HYUNDAI_ORIGINAL_PARTS_TYPES:
                            hyundai_parts.append({
                                'part_number': (
                                    part.get('part_number') or 
                                    part.get('partNumber') or
                                    part.get('part_number')
                                ),
                                'description': (
                                    part.get('description') or 
                                    part.get('text_line') or
                                    part.get('textLine') or
                                    ''
                                ),
                                'amount': float(part.get('amount', 0) or 0),
                                'sum': float(part.get('sum', 0) or 0),
                                'parts_type': parts_type,
                                'is_hyundai_original': True,
                                'source': 'locosoft_soap'
                            })
                    
                    if hyundai_parts:
                        logger.info(f"Hyundai Original-Teile über SOAP gefunden: {len(hyundai_parts)}")
                        return hyundai_parts
        except Exception as e:
            logger.warning(f"Fehler beim Abrufen über SOAP: {e}, versuche DB-Fallback")
    
    # Fallback: Locosoft Datenbank
    try:
        from api.db_utils import get_locosoft_connection
        
        conn = get_locosoft_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.part_number,
                pm.description,
                p.amount,
                p.sum,
                p.parts_type
            FROM parts p
            LEFT JOIN parts_master pm ON p.part_number = pm.part_number
            WHERE p.order_number = %s
              AND p.parts_type IN %s
            ORDER BY p.order_position
        """, [order_number, tuple(HYUNDAI_ORIGINAL_PARTS_TYPES)])
        
        parts = cursor.fetchall()
        conn.close()
        
        hyundai_parts = [
            {
                'part_number': p['part_number'],
                'description': p['description'] or '',
                'amount': float(p['amount'] or 0),
                'sum': float(p['sum'] or 0),
                'parts_type': p['parts_type'],
                'is_hyundai_original': True,
                'source': 'locosoft_db'
            }
            for p in parts
        ]
        
        if hyundai_parts:
            logger.info(f"Hyundai Original-Teile über DB gefunden: {len(hyundai_parts)}")
        
        return hyundai_parts
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen über DB: {e}")
        return []


def verify_hyundai_original_part(part_number: str) -> Dict:
    """
    Prüft ob ein Teil ein Hyundai Original-Teil ist.
    
    Args:
        part_number: Teilenummer
    
    Returns:
        Dict mit:
        - is_hyundai_original: True/False
        - description: Beschreibung
        - parts_type: Teile-Typ
    """
    # Versuche 1: Locosoft SOAP
    client = get_soap_client()
    if client:
        try:
            part_info = client.read_part_information(part_number)
            if part_info:
                parts_type = (
                    part_info.get('parts_type') or 
                    part_info.get('partsType') or
                    part_info.get('part_type')
                )
                
                is_hyundai = parts_type in HYUNDAI_ORIGINAL_PARTS_TYPES
                
                return {
                    'is_hyundai_original': is_hyundai,
                    'description': part_info.get('description', ''),
                    'parts_type': parts_type,
                    'source': 'locosoft_soap'
                }
        except Exception as e:
            logger.warning(f"Fehler beim Prüfen über SOAP: {e}")
    
    # Fallback: Locosoft DB
    try:
        from api.db_utils import get_locosoft_connection
        
        conn = get_locosoft_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                pm.part_number,
                pm.description,
                pm.parts_type
            FROM parts_master pm
            WHERE pm.part_number = %s
            LIMIT 1
        """, [part_number])
        
        part = cursor.fetchone()
        conn.close()
        
        if part:
            parts_type = part['parts_type']
            is_hyundai = parts_type in HYUNDAI_ORIGINAL_PARTS_TYPES
            
            return {
                'is_hyundai_original': is_hyundai,
                'description': part['description'] or '',
                'parts_type': parts_type,
                'source': 'locosoft_db'
            }
        
        return {
            'is_hyundai_original': False,
            'description': '',
            'parts_type': None,
            'source': 'not_found'
        }
        
    except Exception as e:
        logger.error(f"Fehler beim Prüfen über DB: {e}")
        return {
            'is_hyundai_original': False,
            'error': str(e)
        }


@bp.route('/order/<int:order_number>', methods=['GET'])
@login_required
def get_parts_for_order(order_number: int):
    """
    GET /api/mobis/teilebezug/order/<order_number>
    
    Ruft Hyundai Original-Teile für einen Auftrag ab.
    """
    try:
        parts = get_hyundai_original_parts_for_order(order_number)
        
        return jsonify({
            'success': True,
            'order_number': order_number,
            'parts': parts,
            'count': len(parts)
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Teile für Auftrag {order_number}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/verify/<part_number>', methods=['GET'])
@login_required
def verify_part(part_number: str):
    """
    GET /api/mobis/teilebezug/verify/<part_number>
    
    Prüft ob ein Teil ein Hyundai Original-Teil ist.
    """
    try:
        result = verify_hyundai_original_part(part_number)
        
        return jsonify({
            'success': True,
            'part_number': part_number,
            **result
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Prüfen des Teils {part_number}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/health', methods=['GET'])
def health_check():
    """Health-Check für Teilebezug-API."""
    client = get_soap_client()
    
    return jsonify({
        'healthy': client is not None,
        'soap_available': client is not None,
        'hyundai_parts_types': HYUNDAI_ORIGINAL_PARTS_TYPES
    })
