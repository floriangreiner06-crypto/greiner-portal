#!/usr/bin/env python3
"""
Standort-Utilities - Zentrale Standort-Konfiguration
======================================================
Zentrale Definition von Standort-Mappings für alle Module.

TAG 164: Zentralisiert aus serviceberater_api, kundenzentrale_api, budget_api

Standorte:
- 1 = Deggendorf Opel (DEG)
- 2 = Deggendorf Hyundai (HYU)
- 3 = Landau (LAN)
"""

# Standort-Mapping (für Filter)
STANDORTE = {
    'alle': {
        'name': 'Gesamt',
        'subsidiaries': [1, 2, 3],
        'standort_ids': [1, 2, 3]
    },
    'deggendorf': {
        'name': 'Deggendorf',
        'subsidiaries': [1, 2],  # Opel (1) + Hyundai (2)
        'standort_ids': [1, 2]
    },
    'landau': {
        'name': 'Landau',
        'subsidiaries': [3],  # Opel Landau
        'standort_ids': [3]
    },
    'deg_opel': {
        'name': 'Deggendorf Opel',
        'subsidiaries': [1],
        'standort_ids': [1]
    },
    'deg_hyundai': {
        'name': 'Deggendorf Hyundai',
        'subsidiaries': [2],
        'standort_ids': [2]
    }
}

# Standort-Namen Mapping
STANDORT_NAMEN = {
    1: 'Deggendorf Opel',
    2: 'Deggendorf Hyundai',
    3: 'Landau'
}

# Standort-Kürzel
STANDORT_KUERZEL = {
    1: 'DEG',
    2: 'HYU',
    3: 'LAN'
}


def get_standort_config(standort_key: str) -> dict:
    """
    Holt Standort-Konfiguration
    
    Args:
        standort_key: 'alle', 'deggendorf', 'landau', etc.
    
    Returns:
        dict: Standort-Konfiguration oder 'alle' als Fallback
    """
    return STANDORTE.get(standort_key.lower(), STANDORTE['alle'])


def get_standort_name(standort_id: int) -> str:
    """
    Holt Standort-Name aus ID
    
    Args:
        standort_id: 1, 2, oder 3
    
    Returns:
        str: Standort-Name
    """
    return STANDORT_NAMEN.get(standort_id, f'Standort {standort_id}')


def get_standort_kuerzel(standort_id: int) -> str:
    """
    Holt Standort-Kürzel aus ID
    
    Args:
        standort_id: 1, 2, oder 3
    
    Returns:
        str: Standort-Kürzel (DEG, HYU, LAN)
    """
    return STANDORT_KUERZEL.get(standort_id, 'UNK')

