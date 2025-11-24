"""
ROLLEN-KONFIGURATION - GREINER PORTAL
======================================
Mapping von LDAP-Titles zu Portal-Rollen und Feature-Zugriff

Erstellt: TAG 76 (24.11.2025)
"""

# =============================================================================
# LDAP TITLE → PORTAL-ROLLE MAPPING
# =============================================================================
# Wenn ein User sich einloggt, wird sein LDAP "title" auf eine Portal-Rolle gemappt

TITLE_TO_ROLE = {
    # Führung → admin (sieht alles)
    'Geschäftsleitung': 'admin',
    'Filialleitung': 'admin',
    
    # Verkauf
    'Verkaufsleitung': 'verkauf_leitung',
    'Geprüfter Automobilverkäufer': 'verkauf',
    'geprüfter Automobilverkäufer - Hyundai Produkt Coach': 'verkauf',
    'Verkäufer': 'verkauf',
    'Verkaufsberaterin': 'verkauf',
    'Automobilkauffrau': 'verkauf',
    'Automobilkaufmann': 'verkauf',
    'Flottenspezialist - Nutzfahrzeuge': 'verkauf',
    
    # Werkstatt
    'Werkstattleiter': 'werkstatt_leitung',
    'Werkstattleitung': 'werkstatt_leitung',
    'Mechatroniker': 'werkstatt',
    'Servicetechniker': 'werkstatt',
    'zertifizierter Opel Servicetechniker': 'werkstatt',
    
    # Service
    'Serviceberater': 'service',
    'Serviceassistentin': 'service',
    'Servicemitarbeiterin': 'service',
    'Garantiesachbearbeiter': 'service',
    
    # Disposition / Fahrzeuge
    'Disponentin': 'disposition',
    'Fahrzeugkoordination': 'disposition',
    
    # Lager & Teile
    'Teile & Zubehör': 'lager',
    
    # Sonstige
    'Callcenter': 'callcenter',
    'CRM & Marketing': 'marketing',
}

# Fallback-Rolle wenn Title nicht gefunden
DEFAULT_ROLE = 'mitarbeiter'


# =============================================================================
# FEATURE-ZUGRIFF PRO ROLLE
# =============================================================================
# Welche Rolle darf welche Features sehen?
# '*' bedeutet: alle Rollen haben Zugriff

FEATURE_ACCESS = {
    # Controlling / Finanzen - nur Führung
    'bankenspiegel': ['admin'],
    'controlling': ['admin'],
    'zinsen': ['admin'],
    
    # Einkaufsfinanzierung - Führung + Disposition
    'einkaufsfinanzierung': ['admin', 'disposition'],
    'fahrzeugfinanzierungen': ['admin', 'disposition'],
    
    # Verkauf - Führung + Verkauf + Disposition
    'auftragseingang': ['admin', 'verkauf_leitung', 'verkauf', 'disposition'],
    'auslieferungen': ['admin', 'verkauf_leitung', 'verkauf', 'disposition'],
    'verkauf_dashboard': ['admin', 'verkauf_leitung', 'verkauf', 'disposition'],
    
    # Fahrzeuge / Bestand
    'fahrzeuge': ['admin', 'verkauf_leitung', 'verkauf', 'disposition'],
    'stellantis_bestand': ['admin', 'verkauf_leitung', 'verkauf', 'disposition'],
    
    # Urlaubsplaner - alle
    'urlaubsplaner': ['*'],
    
    # After Sales / Teile
    'teilebestellungen': ['admin', 'lager', 'werkstatt', 'werkstatt_leitung', 'service', 'disposition'],
    'aftersales': ['admin', 'werkstatt', 'werkstatt_leitung', 'service'],
    
    # Team-Genehmigungen - nur Leitungen
    'urlaub_genehmigen': ['admin', 'verkauf_leitung', 'werkstatt_leitung', 'service_leitung'],
}


# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def get_role_from_title(title: str) -> str:
    """
    Ermittelt Portal-Rolle aus LDAP-Title
    
    Args:
        title: LDAP title-Attribut
        
    Returns:
        Portal-Rolle (z.B. 'admin', 'verkauf', etc.)
    """
    if not title:
        return DEFAULT_ROLE
    return TITLE_TO_ROLE.get(title, DEFAULT_ROLE)


def has_feature_access(role: str, feature: str) -> bool:
    """
    Prüft ob eine Rolle Zugriff auf ein Feature hat
    
    Args:
        role: Portal-Rolle des Users
        feature: Feature-Name (z.B. 'bankenspiegel')
        
    Returns:
        True wenn Zugriff erlaubt
    """
    if feature not in FEATURE_ACCESS:
        return False
    
    allowed_roles = FEATURE_ACCESS[feature]
    
    # '*' = alle haben Zugriff
    if '*' in allowed_roles:
        return True
    
    return role in allowed_roles


def get_allowed_features(role: str) -> list:
    """
    Gibt alle Features zurück, auf die eine Rolle Zugriff hat
    
    Args:
        role: Portal-Rolle
        
    Returns:
        Liste von Feature-Namen
    """
    allowed = []
    for feature, roles in FEATURE_ACCESS.items():
        if '*' in roles or role in roles:
            allowed.append(feature)
    return allowed


# =============================================================================
# ROLLEN-HIERARCHIE (für Urlaubsplaner)
# =============================================================================
# Wer darf wessen Urlaub genehmigen?

ROLE_HIERARCHY = {
    'admin': ['*'],  # Kann alle genehmigen
    'verkauf_leitung': ['verkauf'],
    'werkstatt_leitung': ['werkstatt'],
    'service_leitung': ['service'],
}

def can_approve_for_role(approver_role: str, employee_role: str) -> bool:
    """
    Prüft ob approver_role Urlaub für employee_role genehmigen kann
    """
    if approver_role not in ROLE_HIERARCHY:
        return False
    
    can_approve = ROLE_HIERARCHY[approver_role]
    return '*' in can_approve or employee_role in can_approve
