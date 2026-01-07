"""
Aufhol-Logik SSOT - Single Source of Truth für Gap-Aufhol-Berechnung
====================================================================
TAG 165: Zentrale Funktion für alle KST zur Berechnung des Aufhol-Beitrags

Die Aufhol-Logik berechnet, wie viel jede KST zum Gap-Aufhol beitragen soll,
basierend auf dem Potenzial und der Marge des jeweiligen Bereichs.

Bereiche und ihre typischen Margen:
- NW (Neuwagen): 8% Marge
- GW (Gebrauchtwagen): 5% Marge
- Teile: 28% Marge
- Werkstatt: 55% Marge
- Sonstige: 50% Marge
"""

from typing import Dict, Any, Optional
from api.unternehmensplan_data import get_gap_analyse


# Bereichs-spezifische Margen (für Umsatz-zu-DB1 Umrechnung)
BEREICH_MARGEN = {
    'NW': 0.08,        # 8% Marge
    'GW': 0.05,        # 5% Marge
    'Teile': 0.28,     # 28% Marge
    'Werkstatt': 0.55, # 55% Marge
    'Sonstige': 0.50   # 50% Marge
}

# Bereichs-spezifische Gap-Aufhol-Anteile (nach Potenzial)
# Diese Anteile basieren auf dem Potenzial jedes Bereichs zum Gap-Aufhol
BEREICH_GAP_ANTEILE = {
    'NW': 0.20,        # 20% des Gap-Aufhols
    'GW': 0.30,        # 30% des Gap-Aufhols (höchstes Potenzial)
    'Teile': 0.10,     # 10% des Gap-Aufhols
    'Werkstatt': 0.15, # 15% des Gap-Aufhols
    'Sonstige': 0.25  # 25% des Gap-Aufhols
}


def get_aufhol_beitrag_fuer_kst(geschaeftsjahr: str, bereich: str, 
                                 monat: Optional[int] = None,
                                 standort: Optional[int] = None) -> Dict[str, Any]:
    """
    Berechnet den Aufhol-Beitrag für eine KST basierend auf dem Gap zum 1%-Ziel.
    
    Args:
        geschaeftsjahr: z.B. '2025/26'
        bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
        monat: Optional - Kalendermonat (1-12), falls None wird aktueller Monat verwendet
        standort: Optional - Standort-ID (1=DEG, 2=HYU, 3=LAN) oder None für alle (0)
                 Für Deggendorf (1+2 kombiniert) verwende standort='deggendorf'
    
    Returns:
        Dict mit:
        - aufhol_beitrag_db1: DB1-Beitrag zum Gap-Aufhol (EUR)
        - aufhol_beitrag_umsatz: Umsatz-Beitrag zum Gap-Aufhol (EUR)
        - gap_jahr: Gesamt-Gap zum Jahresende (EUR)
        - monate_verbleibend: Anzahl verbleibender Monate
        - gap_pro_monat: Gap pro Monat (EUR)
        - bereich_anteil: Anteil dieser KST am Gap-Aufhol (%)
        - marge: Marge dieses Bereichs (%)
        - standort: Standort-ID oder 'deggendorf' für kombiniert
    """
    # TAG 165: Standort-spezifische Gap-Analyse
    if standort == 'deggendorf':
        # Deggendorf = Standort 1 (Opel) + Standort 2 (Hyundai) kombiniert
        gap_deg_opel = get_gap_analyse(geschaeftsjahr, standort=1)
        gap_deg_hyu = get_gap_analyse(geschaeftsjahr, standort=2)
        # Gaps kombinieren
        gap_jahr = gap_deg_opel.get('gap_jahresende', 0) + gap_deg_hyu.get('gap_jahresende', 0)
        monate_verbleibend = gap_deg_opel.get('monate_verbleibend', 8)  # Sollte gleich sein
        standort_info = 'deggendorf'
    elif standort == 3:
        # Landau
        gap_analyse = get_gap_analyse(geschaeftsjahr, standort=3)
        gap_jahr = gap_analyse.get('gap_jahresende', 0)
        monate_verbleibend = gap_analyse.get('monate_verbleibend', 8)
        standort_info = 3
    elif standort in [1, 2]:
        # Einzelner Standort
        gap_analyse = get_gap_analyse(geschaeftsjahr, standort=standort)
        gap_jahr = gap_analyse.get('gap_jahresende', 0)
        monate_verbleibend = gap_analyse.get('monate_verbleibend', 8)
        standort_info = standort
    else:
        # Alle Standorte (standort=0 oder None)
        gap_analyse = get_gap_analyse(geschaeftsjahr, standort=0)
        gap_jahr = gap_analyse.get('gap_jahresende', 0)
        monate_verbleibend = gap_analyse.get('monate_verbleibend', 8)
        standort_info = 0
    
    # Wenn kein Gap oder keine verbleibenden Monate: kein Aufhol-Beitrag
    if gap_jahr <= 0 or monate_verbleibend <= 0:
        return {
            'aufhol_beitrag_db1': 0.0,
            'aufhol_beitrag_umsatz': 0.0,
            'gap_jahr': 0.0,
            'monate_verbleibend': monate_verbleibend,
            'gap_pro_monat': 0.0,
            'bereich_anteil': 0.0,
            'marge': BEREICH_MARGEN.get(bereich, 0.10) * 100
        }
    
    # Gap pro Monat
    gap_pro_monat = gap_jahr / monate_verbleibend
    
    # Bereichs-Anteil am Gap-Aufhol
    bereich_anteil = BEREICH_GAP_ANTEILE.get(bereich, 0.10)
    
    # DB1-Beitrag dieser KST zum Gap-Aufhol
    aufhol_beitrag_db1 = gap_pro_monat * bereich_anteil
    
    # Umsatz-Beitrag (DB1 / Marge)
    marge = BEREICH_MARGEN.get(bereich, 0.10)
    aufhol_beitrag_umsatz = aufhol_beitrag_db1 / marge if marge > 0 else 0
    
    return {
        'aufhol_beitrag_db1': round(aufhol_beitrag_db1, 2),
        'aufhol_beitrag_umsatz': round(aufhol_beitrag_umsatz, 2),
        'gap_jahr': round(gap_jahr, 0),
        'monate_verbleibend': monate_verbleibend,
        'gap_pro_monat': round(gap_pro_monat, 2),
        'bereich_anteil': round(bereich_anteil * 100, 1),  # in Prozent
        'marge': round(marge * 100, 1),  # in Prozent
        'standort': standort_info  # TAG 165: Standort-Info
    }


def apply_aufhol_auf_kst_ziel(umsatz_ziel: float, db1_ziel: float, 
                               geschaeftsjahr: str, bereich: str,
                               standort: Optional[int] = None) -> Dict[str, float]:
    """
    Wendet die Aufhol-Logik auf ein KST-Ziel an.
    
    Args:
        umsatz_ziel: Basis-Umsatz-Ziel (ohne Aufhol)
        db1_ziel: Basis-DB1-Ziel (ohne Aufhol)
        geschaeftsjahr: z.B. '2025/26'
        bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
        standort: Optional - Standort-ID (1=DEG, 2=HYU, 3=LAN) oder 'deggendorf' für kombiniert
    
    Returns:
        Dict mit:
        - umsatz_ziel_mit_aufhol: Umsatz-Ziel mit Aufhol-Beitrag
        - db1_ziel_mit_aufhol: DB1-Ziel mit Aufhol-Beitrag
        - aufhol_beitrag_db1: Aufhol-Beitrag DB1
        - aufhol_beitrag_umsatz: Aufhol-Beitrag Umsatz
    """
    aufhol = get_aufhol_beitrag_fuer_kst(geschaeftsjahr, bereich, standort=standort)
    
    return {
        'umsatz_ziel_mit_aufhol': round(umsatz_ziel + aufhol['aufhol_beitrag_umsatz'], 2),
        'db1_ziel_mit_aufhol': round(db1_ziel + aufhol['aufhol_beitrag_db1'], 2),
        'aufhol_beitrag_db1': aufhol['aufhol_beitrag_db1'],
        'aufhol_beitrag_umsatz': aufhol['aufhol_beitrag_umsatz']
    }

