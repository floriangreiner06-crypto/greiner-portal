#!/usr/bin/env python3
"""
Teile-Stock Utilities - SSOT für Lagerbestand
==============================================
Zentrale Funktionen für Lagerbestand-Abfragen aus Locosoft.

⚠️ WICHTIG: Dies ist die EINZIGE autoritative Quelle für Lagerbestand-Logik!
Alle Module MÜSSEN diese Funktionen verwenden - NIEMALS eigene Lagerbestand-Queries schreiben!

TAG 176: Erstellt als SSOT für teile_status_api
"""

import logging
from typing import Optional, Dict, List
from psycopg2.extras import RealDictCursor

from api.db_utils import get_locosoft_connection

logger = logging.getLogger(__name__)


# Stock-No Mapping (Standort → stock_no)
# WICHTIG: stock_no kann mehrere Werte haben (1, 2, 3) für verschiedene Lager
# Für Teile-Status: Aggregieren wir über ALLE stock_no des Standorts
# (Ein Teil kann in mehreren Lagern sein, wir summieren den Bestand)
STOCK_NO_MAPPING = {
    1: [1, 2, 3],  # Deggendorf Opel: Alle Lager (stock_no 1, 2, 3)
    2: [1, 2, 3],  # Deggendorf Hyundai: Alle Lager (stock_no 1, 2, 3)
    3: [1, 2, 3],  # Landau: Alle Lager (stock_no 1, 2, 3)
}


def get_stock_level_for_subsidiary(part_number: str, subsidiary: int, required_amount: float = 0, use_soap: bool = True) -> Dict:
    """
    Prüft Lagerbestand für ein Teil an einem Standort.
    
    SSOT: Versucht zuerst SOAP, dann DB-Fallback.
    
    Args:
        part_number: Teilenummer
        subsidiary: Standort (1=Deggendorf Opel, 2=Deggendorf Hyundai, 3=Landau)
        required_amount: Benötigte Menge (optional, für "ist genug vorhanden?" Prüfung)
        use_soap: True wenn SOAP versucht werden soll (default: True)
    
    Returns:
        Dict mit:
        - stock_level: Lagerbestand (float)
        - is_available: True wenn genug vorhanden (stock_level >= required_amount)
        - stock_no: stock_no des Standorts
        - source: 'soap' oder 'db'
    """
    # Versuche 1: SOAP (wenn verfügbar)
    if use_soap:
        soap_result = get_stock_level_via_soap(part_number, subsidiary)
        if soap_result and 'stock_level' in soap_result:
            stock_level = float(soap_result['stock_level'])
            is_available = stock_level >= required_amount if required_amount > 0 else stock_level > 0
            return {
                'stock_level': stock_level,
                'is_available': is_available,
                'stock_no': None,  # SOAP gibt möglicherweise kein stock_no zurück
                'required_amount': required_amount,
                'source': 'soap'
            }
    
    # Fallback: DB
    try:
        conn = get_locosoft_connection()
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Stock-No für Standort ermitteln
        stock_nos = STOCK_NO_MAPPING.get(subsidiary, [1])  # Fallback: stock_no 1
        
        # Query: Summe über alle stock_no des Standorts
        # WICHTIG: Ein Teil kann in mehreren Lagern sein (stock_no 1, 2, 3)
        # Für Teile-Status: Aggregieren wir über alle stock_no des Standorts
        placeholders = ','.join(['%s'] * len(stock_nos))
        query = f"""
            SELECT 
                COALESCE(SUM(ps.stock_level), 0) as stock_level,
                MAX(ps.stock_no) as stock_no
            FROM parts_stock ps
            WHERE ps.part_number = %s
            AND ps.stock_no IN ({placeholders})
        """
        
        params = [part_number] + stock_nos
        cur.execute(query, params)
        row = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if row:
            stock_level = float(row['stock_level'] or 0)
            is_available = stock_level >= required_amount if required_amount > 0 else stock_level > 0
            
            return {
                'stock_level': stock_level,
                'is_available': is_available,
                'stock_no': row['stock_no'],
                'required_amount': required_amount,
                'source': 'db'
            }
        else:
            # Teil nicht in parts_stock → kein Lagerbestand
            return {
                'stock_level': 0.0,
                'is_available': False,
                'stock_no': None,
                'required_amount': required_amount,
                'source': 'db'
            }
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Lagerbestands für {part_number} (subsidiary={subsidiary}): {e}")
        return {
            'stock_level': 0.0,
            'is_available': False,
            'stock_no': None,
            'error': str(e),
            'source': 'db'
        }


def is_part_available(part_number: str, subsidiary: int, required_amount: float, use_soap: bool = False) -> bool:
    """
    Prüft ob ein Teil in ausreichender Menge auf Lager ist.
    
    Args:
        part_number: Teilenummer
        subsidiary: Standort (1=Deggendorf Opel, 2=Deggendorf Hyundai, 3=Landau)
        required_amount: Benötigte Menge
        use_soap: True wenn SOAP versucht werden soll (default: False für Performance)
    
    Returns:
        True wenn genug vorhanden, False sonst
    """
    stock_info = get_stock_level_for_subsidiary(part_number, subsidiary, required_amount, use_soap=use_soap)
    return stock_info.get('is_available', False)


def get_missing_parts_for_order(order_number: int, subsidiary: int) -> List[Dict]:
    """
    Ermittelt fehlende Teile für einen Auftrag.
    
    Teile sind "fehlend" wenn:
    - Nicht genug auf Lager für den benötigten Standort
    - Oder gar nicht in parts_stock vorhanden
    
    Args:
        order_number: Auftragsnummer
        subsidiary: Standort des Auftrags
    
    Returns:
        Liste von Dicts mit:
        - part_number
        - bezeichnung
        - menge (benötigt)
        - stock_level (vorhanden)
        - is_available (True/False)
    """
    try:
        conn = get_locosoft_connection()
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Alle Teile des Auftrags
        cur.execute("""
            SELECT 
                p.part_number,
                p.text_line as bezeichnung,
                p.amount as menge,
                p.sum as wert,
                p.sum / NULLIF(p.amount, 0) as stueckpreis
            FROM parts p
            WHERE p.order_number = %s
            AND p.amount > 0
        """, [order_number])
        
        parts = cur.fetchall()
        cur.close()
        conn.close()
        
        missing_parts = []
        for part in parts:
            part_number = part['part_number']
            required_amount = float(part['menge'] or 0)
            
            # SSOT: Lagerbestand prüfen
            stock_info = get_stock_level_for_subsidiary(part_number, subsidiary, required_amount)
            
            if not stock_info['is_available']:
                missing_parts.append({
                    'part_number': part_number,
                    'bezeichnung': part['bezeichnung'],
                    'menge': required_amount,
                    'stock_level': stock_info['stock_level'],
                    'is_available': False,
                    'wert': float(part['wert'] or 0),
                    'stueckpreis': float(part['stueckpreis'] or 0)
                })
        
        return missing_parts
        
    except Exception as e:
        logger.error(f"Fehler beim Ermitteln fehlender Teile für Auftrag {order_number}: {e}")
        return []


def get_stock_level_via_soap(part_number: str, subsidiary: Optional[int] = None) -> Optional[Dict]:
    """
    Versucht Lagerbestand über Locosoft SOAP zu holen (falls verfügbar).
    
    Args:
        part_number: Teilenummer
        subsidiary: Standort (optional, für stock_no Filter)
    
    Returns:
        Dict mit stock_level oder None wenn SOAP nicht verfügbar
    """
    try:
        from tools.locosoft_soap_client import get_soap_client
        
        client = get_soap_client()
        if not client:
            return None
        
        part_info = client.read_part_information(part_number)
        if part_info:
            # SOAP gibt möglicherweise stock_level zurück
            # TODO: Prüfen welche Felder SOAP zurückgibt
            stock_level = (
                part_info.get('stock_level') or
                part_info.get('stockLevel') or
                part_info.get('stock')
            )
            
            if stock_level is not None:
                return {
                    'stock_level': float(stock_level),
                    'source': 'soap'
                }
        
        return None
        
    except Exception as e:
        logger.debug(f"SOAP-Abfrage für {part_number} fehlgeschlagen: {e}")
        return None
