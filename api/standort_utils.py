#!/usr/bin/env python3
"""
Standort-Utilities - Zentrale Standort-Konfiguration (SSOT)
============================================================
Zentrale Definition von Standort-Mappings und Filter-Funktionen für alle Module.

⚠️ WICHTIG: Dies ist die EINZIGE autoritative Quelle für Standort-Filter-Logik!
Alle Module MÜSSEN diese Funktionen verwenden - NIEMALS eigene Filter-Logik schreiben!

TAG 170: Erweitert um BWA- und Locosoft-Filter-Funktionen
TAG 164: Zentralisiert aus serviceberater_api, kundenzentrale_api, budget_api

Standorte:
- 1 = Deggendorf Opel (DEG) - Stellantis, subsidiary=1
- 2 = Deggendorf Hyundai (HYU) - Hyundai, subsidiary=2
- 3 = Landau (LAN) - Stellantis, subsidiary=? ⚠️

Siehe auch: docs/STANDORT_LOGIK_SSOT.md
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
        'name': 'Landau Opel',
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

# Standort-Namen Mapping (konsistent: Deggendorf Opel, Deggendorf Hyundai, Landau Opel)
STANDORT_NAMEN = {
    1: 'Deggendorf Opel',
    2: 'Deggendorf Hyundai',
    3: 'Landau Opel'
}

# Betriebsnamen (Legacy/Alias für STANDORT_NAMEN)
# ⚠️ SSOT: Dies ist die EINZIGE Definition von BETRIEB_NAMEN!
# Alle Module MÜSSEN diese Definition verwenden - NIEMALS eigene Definitionen!
BETRIEB_NAMEN = {
    1: 'Deggendorf',
    2: 'Hyundai DEG',
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


# =============================================================================
# BWA-FILTER (loco_journal_accountings) - SSOT
# =============================================================================

def build_bwa_filter(firma: str, standort: str):
    """
    Baut Firma/Standort-Filter für BWA-Queries (loco_journal_accountings).
    
    ⚠️ SSOT: Dies ist die EINZIGE Funktion für BWA-Filter!
    Nutze diese Funktion IMMER, niemals eigene Filter-Logik schreiben!
    
    TAG170: Wrapper um build_firma_standort_filter() aus controlling_api.py
    für zentrale Verwendung.
    
    Args:
        firma: '0'=Alle, '1'=Stellantis, '2'=Hyundai
        standort: '0'=Alle, '1'=Deggendorf, '2'=Landau, 'deg-both'=Deggendorf (beide)
    
    Returns:
        tuple: (firma_filter_umsatz, firma_filter_einsatz, firma_filter_kosten, standort_name)
    
    Beispiel:
        >>> umsatz_filter, einsatz_filter, kosten_filter, name = build_bwa_filter('1', '1')
        >>> # umsatz_filter: "AND subsidiary_to_company_ref = 1 AND branch_number = 1"
    """
    from api.controlling_api import build_firma_standort_filter
    return build_firma_standort_filter(firma, standort)


# =============================================================================
# LOCOSOFT-FILTER (dealer_vehicles, orders, invoices) - SSOT
# =============================================================================

def build_locosoft_filter_verkauf(standort: int, nur_stellantis: bool = False) -> str:
    """
    Baut Standort-Filter für Locosoft dealer_vehicles (Verkäufe).
    
    ⚠️ SSOT: Dies ist die EINZIGE Funktion für Locosoft Verkaufs-Filter!
    Nutze diese Funktion IMMER, niemals eigene Filter-Logik schreiben!
    
    Args:
        standort: 1=Deggendorf, 2=Hyundai, 3=Landau, 0=Alle
        nur_stellantis: Für standort=1: Nur Stellantis (True) oder beide (False)
    
    Returns:
        str: SQL WHERE-Clause (z.B. "AND out_subsidiary = 1")
    
    Beispiel:
        >>> filter = build_locosoft_filter_verkauf(standort=1, nur_stellantis=True)
        >>> # "AND out_subsidiary = 1"
        >>> filter = build_locosoft_filter_verkauf(standort=1, nur_stellantis=False)
        >>> # "AND (out_subsidiary = 1 OR out_subsidiary = 2)"
    """
    if standort == 0:
        return ""  # Alle Standorte
    
    if standort == 1:
        if nur_stellantis:
            # Opel DEG: Nur Stellantis (subsidiary=1)
            return "AND out_subsidiary = 1"
        else:
            # Deggendorf: Stellantis (subsidiary=1) + Hyundai (subsidiary=2)
            return "AND (out_subsidiary = 1 OR out_subsidiary = 2)"
    elif standort == 2:
        # Hyundai: Nur Hyundai (subsidiary=2)
        return "AND out_subsidiary = 2"
    elif standort == 3:
        # Landau: subsidiary=3 (LANO location)
        # VERIFIZIERT: analyse_landau_locosoft.py zeigt subsidiary=3 für LANO
        return "AND out_subsidiary = 3"
    else:
        return ""  # Unbekannter Standort


def build_locosoft_filter_bestand(standort: int, nur_stellantis: bool = False) -> str:
    """
    Baut Standort-Filter für Locosoft dealer_vehicles (Bestand).
    
    ⚠️ SSOT: Dies ist die EINZIGE Funktion für Locosoft Bestands-Filter!
    Nutze diese Funktion IMMER, niemals eigene Filter-Logik schreiben!
    
    Args:
        standort: 1=Deggendorf, 2=Hyundai, 3=Landau, 0=Alle
        nur_stellantis: Für standort=1: Nur Stellantis (True) oder beide (False)
    
    Returns:
        str: SQL WHERE-Clause (z.B. "AND in_subsidiary = 1")
    
    Beispiel:
        >>> filter = build_locosoft_filter_bestand(standort=1, nur_stellantis=True)
        >>> # "AND in_subsidiary = 1"
    """
    if standort == 0:
        return ""  # Alle Standorte
    
    if standort == 1:
        if nur_stellantis:
            # Opel DEG: Nur Stellantis (subsidiary=1)
            return "AND in_subsidiary = 1"
        else:
            # Deggendorf: Stellantis (subsidiary=1) + Hyundai (subsidiary=2)
            return "AND (in_subsidiary = 1 OR in_subsidiary = 2)"
    elif standort == 2:
        # Hyundai: Nur Hyundai (subsidiary=2)
        return "AND in_subsidiary = 2"
    elif standort == 3:
        # Landau: subsidiary=3 (LANO location)
        # VERIFIZIERT: analyse_landau_locosoft.py zeigt subsidiary=3 für LANO
        return "AND in_subsidiary = 3"
    else:
        return ""  # Unbekannter Standort


def build_locosoft_filter_orders(standort: int) -> str:
    """
    Baut Standort-Filter für Locosoft orders/invoices.
    
    ⚠️ SSOT: Dies ist die EINZIGE Funktion für Locosoft Orders-Filter!
    Nutze diese Funktion IMMER, niemals eigene Filter-Logik schreiben!
    
    Args:
        standort: 1=Deggendorf, 2=Hyundai, 3=Landau, 0=Alle
    
    Returns:
        str: SQL WHERE-Clause (z.B. "AND o.subsidiary = 1")
    
    Beispiel:
        >>> filter = build_locosoft_filter_orders(standort=1)
        >>> # "AND (o.subsidiary = 1 OR o.subsidiary = 2)"
    """
    if standort == 0:
        return ""  # Alle Standorte
    
    if standort == 1:
        # Deggendorf: Stellantis (subsidiary=1) + Hyundai (subsidiary=2)
        return "AND (o.subsidiary = 1 OR o.subsidiary = 2)"
    elif standort == 2:
        # Hyundai: Nur Hyundai (subsidiary=2)
        return "AND o.subsidiary = 2"
    elif standort == 3:
        # Landau: subsidiary=3 (LANO location)
        # VERIFIZIERT: analyse_landau_locosoft.py zeigt subsidiary=3 für LANO
        return "AND o.subsidiary = 3"
    else:
        return ""  # Unbekannter Standort


# =============================================================================
# KONSOLIDIERTE FILTER (Service Deggendorf = Standort 1 + 2) - SSOT
# =============================================================================

def get_standorte_fuer_bereich(bereich: str) -> list:
    """
    Gibt verfügbare Standorte für einen Bereich zurück.
    
    ⚠️ SSOT: Zentrale Logik für Standort-Filter pro Bereich!
    
    Args:
        bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
    
    Returns:
        list: Liste von Standort-IDs (z.B. [1, 2, 3] oder [1, 3])
    
    Beispiel:
        >>> get_standorte_fuer_bereich('Werkstatt')
        >>> # [1, 3]  # Deggendorf + Landau (Hyundai hat keine eigene Werkstatt)
    """
    if bereich in ['Teile', 'Werkstatt']:
        # Teile/Werkstatt: Nur Standort 1 (Deggendorf) und 3 (Landau)
        # Standort 2 (Hyundai DEG) wird auf Standort 1 gemappt
        return [1, 3]
    else:
        # NW/GW/Sonstige: Alle Standorte
        return [1, 2, 3]


def build_consolidated_filter(standort: int, konsolidiert: bool, filter_type: str = 'verkauf') -> str:
    """
    Baut konsolidierten Filter für "Service Deggendorf" (Standort 1 + 2 zusammen).
    
    ⚠️ SSOT: Zentrale Funktion für konsolidierte Filter-Logik!
    
    Args:
        standort: 1=Deggendorf, 2=Hyundai, 3=Landau
        konsolidiert: True = Service Deggendorf (1+2 zusammen), False = Normal
        filter_type: 'verkauf' (out_subsidiary), 'bestand' (in_subsidiary), 'orders' (o.subsidiary)
    
    Returns:
        str: SQL WHERE-Clause
    
    Beispiel:
        >>> # Service Deggendorf (konsolidiert) für Verkäufe
        >>> filter = build_consolidated_filter(standort=1, konsolidiert=True, filter_type='verkauf')
        >>> # "AND (out_subsidiary = 1 OR out_subsidiary = 2)"
        
        >>> # Service Deggendorf (konsolidiert) für Orders
        >>> filter = build_consolidated_filter(standort=1, konsolidiert=True, filter_type='orders')
        >>> # "AND (o.subsidiary = 1 OR o.subsidiary = 2)"
    """
    if not konsolidiert:
        # Normale Filter-Logik
        if filter_type == 'verkauf':
            return build_locosoft_filter_verkauf(standort)
        elif filter_type == 'bestand':
            return build_locosoft_filter_bestand(standort)
        elif filter_type == 'orders':
            return build_locosoft_filter_orders(standort)
        else:
            return ""
    
    # Konsolidiert: Service Deggendorf = Standort 1 + 2
    if standort == 1:
        # Service Deggendorf: Beide Standorte zusammen
        if filter_type == 'verkauf':
            return "AND (out_subsidiary = 1 OR out_subsidiary = 2)"
        elif filter_type == 'bestand':
            return "AND (in_subsidiary = 1 OR in_subsidiary = 2)"
        elif filter_type == 'orders':
            return "AND (o.subsidiary = 1 OR o.subsidiary = 2)"
        else:
            return ""
    elif standort == 2:
        # Standort 2 allein (nicht konsolidiert)
        if filter_type == 'verkauf':
            return "AND out_subsidiary = 2"
        elif filter_type == 'bestand':
            return "AND in_subsidiary = 2"
        elif filter_type == 'orders':
            return "AND o.subsidiary = 2"
        else:
            return ""
    elif standort == 3:
        # Landau: Normal (keine Konsolidierung)
        if filter_type == 'verkauf':
            return "AND out_subsidiary = 3"
        elif filter_type == 'bestand':
            return "AND in_subsidiary = 3"
        elif filter_type == 'orders':
            return "AND o.subsidiary = 3"
        else:
            return ""
    else:
        return ""

