# Utils Package - Zentrale Hilfsfunktionen
# =========================================
# WICHTIG: Alle KPI-Berechnungen und Locosoft-Helpers hier importieren!

# =============================================================================
# KPI DEFINITIONEN (Single Source of Truth)
# =============================================================================
from .kpi_definitions import (
    # Konstanten
    MINUTEN_PRO_AW,
    STUNDEN_PRO_WOCHE,
    STUNDEN_PRO_TAG,
    ZIEL_ANWESENHEITSGRAD,
    ZIEL_AUSLASTUNGSGRAD,
    ZIEL_LEISTUNGSGRAD,
    ZIEL_EFFIZIENZ,
    ZIEL_STUNDEN_PRO_DURCHGANG,
    SCHWELLEN,
    
    # Kern-Berechnungen
    berechne_anwesenheitsgrad,
    berechne_auslastungsgrad,
    berechne_produktivitaet,  # Alias für Auslastungsgrad
    berechne_leistungsgrad,
    berechne_effizienz,
    berechne_entgangener_umsatz,
    berechne_stunden_pro_durchgang,
    berechne_stundenverrechnungssatz,
    
    # Aggregationen
    berechne_gesamt_leistungsgrad,
    berechne_gesamt_entgangener_umsatz,
    berechne_mechaniker_kpis,
    
    # Konvertierungen
    minuten_zu_aw,
    aw_zu_minuten,
    minuten_zu_stunden,
    stunden_zu_minuten,
    aw_zu_stunden,
    stunden_zu_aw,
    
    # Bewertungen
    bewerte_anwesenheitsgrad,
    bewerte_auslastungsgrad,
    bewerte_produktivitaet,
    bewerte_leistungsgrad,
    bewerte_effizienz,
    
    # Formatierung
    format_euro,
    format_prozent,
    format_aw,
    format_stunden,
    format_zeit_hhmm,
)

# =============================================================================
# LOCOSOFT HELPERS (Daten aus SQLite - gesynct von Locosoft)
# =============================================================================
from .locosoft_helpers import (
    # Konstanten & Mappings
    BETRIEB_NAMEN,
    ABTEILUNG_NAMEN,
    CHARGE_TYPE_KATEGORIEN,
    LABOUR_TYPE_KATEGORIEN,
    INVOICE_TYPE_NAMEN,
    
    # SVS (Stundenverrechnungssätze) - aus SQLite!
    hole_svs,                   # Haupt-Funktion
    hole_svs_aus_locosoft,      # Alias (deprecated)
    hole_aw_preis,
    hole_charge_type_info,
    
    # Auftragsart-Klassifizierung
    klassifiziere_auftragsart,
    hole_auftragsdetails,       # Live aus Locosoft
    
    # Fremdleistungs-Margen
    berechne_fremdleistung_marge,
    hole_fremdleistungen_statistik,
    
    # Hilfsfunktionen
    ist_produktiver_auftrag,
    hole_abteilung_fuer_charge_type,
)

# =============================================================================
# EXPORTS
# =============================================================================
__all__ = [
    # === KPI DEFINITIONEN ===
    # Konstanten
    'MINUTEN_PRO_AW', 'STUNDEN_PRO_WOCHE', 'STUNDEN_PRO_TAG',
    'ZIEL_ANWESENHEITSGRAD', 'ZIEL_AUSLASTUNGSGRAD', 
    'ZIEL_LEISTUNGSGRAD', 'ZIEL_EFFIZIENZ', 'ZIEL_STUNDEN_PRO_DURCHGANG',
    'SCHWELLEN',
    
    # Berechnungen
    'berechne_anwesenheitsgrad', 'berechne_auslastungsgrad',
    'berechne_produktivitaet', 'berechne_leistungsgrad',
    'berechne_effizienz', 'berechne_entgangener_umsatz',
    'berechne_stunden_pro_durchgang', 'berechne_stundenverrechnungssatz',
    'berechne_gesamt_leistungsgrad', 'berechne_gesamt_entgangener_umsatz',
    'berechne_mechaniker_kpis',
    
    # Konvertierungen
    'minuten_zu_aw', 'aw_zu_minuten', 
    'minuten_zu_stunden', 'stunden_zu_minuten',
    'aw_zu_stunden', 'stunden_zu_aw',
    
    # Bewertungen
    'bewerte_anwesenheitsgrad', 'bewerte_auslastungsgrad',
    'bewerte_produktivitaet', 'bewerte_leistungsgrad', 'bewerte_effizienz',
    
    # Formatierung
    'format_euro', 'format_prozent', 'format_aw', 
    'format_stunden', 'format_zeit_hhmm',
    
    # === LOCOSOFT HELPERS ===
    # Konstanten & Mappings
    'BETRIEB_NAMEN', 'ABTEILUNG_NAMEN', 
    'CHARGE_TYPE_KATEGORIEN', 'LABOUR_TYPE_KATEGORIEN', 'INVOICE_TYPE_NAMEN',
    
    # SVS
    'hole_svs',                 # Haupt-Funktion (SQLite)
    'hole_svs_aus_locosoft',    # Alias (deprecated)
    'hole_aw_preis',
    'hole_charge_type_info',
    
    # Auftragsart
    'klassifiziere_auftragsart', 'hole_auftragsdetails',
    
    # Fremdleistungen
    'berechne_fremdleistung_marge', 'hole_fremdleistungen_statistik',
    
    # Hilfsfunktionen
    'ist_produktiver_auftrag', 'hole_abteilung_fuer_charge_type',
]
