#!/usr/bin/env python3
"""
Standort-Filter Helper Functions - Zentrale Route-Helpers
==========================================================
Wiederverwendbare Helper-Funktionen für Standort-Filter in Routes.

TAG 177: Erstellt für einheitliche Standort-Filter-Verarbeitung

Verwendung:
    from utils.standort_filter_helpers import parse_standort_params
    
    @route('/mein-feature')
    def mein_feature():
        standort, konsolidiert = parse_standort_params(request)
        # ... verwende standort und konsolidiert
"""

from flask import request
from typing import Tuple, Optional


def parse_standort_params(request_obj) -> Tuple[Optional[int], bool]:
    """
    Parst Standort- und Konsolidierungs-Parameter aus Request.
    
    Args:
        request_obj: Flask request object
    
    Returns:
        tuple: (standort, konsolidiert)
            - standort: 1, 2, 3 oder None (für "Alle")
            - konsolidiert: True wenn konsolidierte Ansicht aktiv
    
    Beispiel:
        >>> standort, konsolidiert = parse_standort_params(request)
        >>> if konsolidiert and standort == 1:
        >>>     # Service Deggendorf (konsolidiert)
    """
    standort = request_obj.args.get('standort', type=int)
    konsolidiert = request_obj.args.get('konsolidiert', 'false').lower() == 'true'
    
    # Konsolidierte Ansicht nur für Standort 1 möglich
    if konsolidiert and standort != 1:
        konsolidiert = False
    
    return standort, konsolidiert


def get_standorte_fuer_query(standort: Optional[int], konsolidiert: bool) -> Optional[list]:
    """
    Gibt Liste von Standort-IDs zurück, die für Query verwendet werden sollen.
    
    Args:
        standort: 1, 2, 3 oder None
        konsolidiert: True wenn konsolidierte Ansicht
    
    Returns:
        list: Liste von Standort-IDs oder None (für "Alle")
    
    Beispiel:
        >>> standorte = get_standorte_fuer_query(standort=1, konsolidiert=True)
        >>> # [1, 2] - für konsolidierte Ansicht beide Standorte
        >>> query = "WHERE standort = ANY(%s)"
        >>> cursor.execute(query, (standorte,))
    """
    if konsolidiert and standort == 1:
        # Service Deggendorf (konsolidiert): Standort 1 + 2
        return [1, 2]
    elif standort:
        return [standort]
    else:
        return None  # Alle Standorte
