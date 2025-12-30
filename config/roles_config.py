"""
ROLLEN-KONFIGURATION - GREINER PORTAL
======================================
Mapping von LDAP-Titles zu Portal-Rollen und Feature-Zugriff

Erstellt: TAG 76 (24.11.2025)
Aktualisiert: TAG 77 (24.11.2025) - Buchhaltung + Serviceleitung hinzugefügt
"""

# =============================================================================
# LDAP TITLE → PORTAL-ROLLE MAPPING
# =============================================================================

TITLE_TO_ROLE = {
    # Führung → admin (sieht alles)
    'Geschäftsleitung': 'admin',
    'Filialleitung': 'admin',
    
    # Buchhaltung → buchhaltung (Vollzugriff)
    'Buchhaltung': 'buchhaltung',
    'Mitarbeiterin Buchhaltung': 'buchhaltung',
    'Mitarbeiter Buchhaltung': 'buchhaltung',

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
    'Werkstattleitung': 'werkstatt_leitung',
    'Werkstattleiter': 'werkstatt_leitung',
    'Mechatroniker': 'werkstatt',
    'Servicetechniker': 'werkstatt',
    'zertifizierter Opel Servicetechniker': 'werkstatt',
    'KFZ-Mechatroniker': 'werkstatt',

    # Service
    'Serviceleitung': 'service_leitung',
    'Serviceleiter': 'service_leitung',
    'Serviceberater': 'serviceberater',  # TAG121: Eigene Rolle für SB-Dashboard
    'Serviceassistentin': 'service',
    'Servicemitarbeiterin': 'service',
    'Garantiesachbearbeiter': 'service',
    'Gewährleistung': 'service',

    # Disposition / Fahrzeuge
    'Disponentin': 'disposition',
    'Disponent': 'disposition',
    'Dispositionsleitung': 'disposition',
    'Fahrzeugkoordination': 'disposition',
    'Fahrzeugaufbereitung': 'disposition',

    # Lager & Teile
    'Teile & Zubehör': 'lager',
    'Lager': 'lager',
    'Teiledienst': 'lager',

    # Sonstige
    'Callcenter': 'callcenter',
    'CRM & Marketing': 'marketing',
}

# Fallback-Rolle wenn Title nicht gefunden
DEFAULT_ROLE = 'mitarbeiter'


# =============================================================================
# FEATURE-ZUGRIFF PRO ROLLE
# =============================================================================

FEATURE_ACCESS = {
    # Controlling / Finanzen - Führung + Buchhaltung
    'bankenspiegel': ['admin', 'buchhaltung'],
    'controlling': ['admin', 'buchhaltung'],
    'zinsen': ['admin', 'buchhaltung', 'verkauf_leitung', 'disposition'],  # TAG82: +Verkaufsleitung, +Disposition

    # Einkaufsfinanzierung - Führung + Buchhaltung + Disposition
    'einkaufsfinanzierung': ['admin', 'buchhaltung', 'disposition'],
    'fahrzeugfinanzierungen': ['admin', 'buchhaltung', 'disposition'],

    # Verkauf - Führung + Buchhaltung + Verkauf + Disposition
    'auftragseingang': ['admin', 'buchhaltung', 'verkauf_leitung', 'verkauf', 'disposition'],
    'auslieferungen': ['admin', 'buchhaltung', 'verkauf_leitung', 'verkauf', 'disposition'],
    'verkauf_dashboard': ['admin', 'buchhaltung', 'verkauf_leitung', 'verkauf', 'disposition'],

    # Fahrzeuge / Bestand
    'fahrzeuge': ['admin', 'buchhaltung', 'verkauf_leitung', 'verkauf', 'disposition'],
    'stellantis_bestand': ['admin', 'buchhaltung', 'verkauf_leitung', 'verkauf', 'disposition'],

    # Urlaubsplaner - alle
    'urlaubsplaner': ['*'],

    # After Sales / Teile
    'teilebestellungen': ['admin', 'buchhaltung', 'lager', 'werkstatt', 'werkstatt_leitung', 'service', 'service_leitung', 'serviceberater', 'disposition'],
    'aftersales': ['admin', 'buchhaltung', 'werkstatt', 'werkstatt_leitung', 'service', 'service_leitung', 'serviceberater'],

    # SB-Controlling (TAG121)
    'sb_dashboard': ['admin', 'buchhaltung', 'service_leitung', 'serviceberater'],
    'sb_ranking': ['admin', 'buchhaltung', 'service_leitung', 'serviceberater'],
    'werkstatt_live': ['admin', 'buchhaltung', 'werkstatt_leitung', 'service_leitung', 'serviceberater'],

    # Team-Genehmigungen - nur Leitungen
    'urlaub_genehmigen': ['admin', 'buchhaltung', 'verkauf_leitung', 'werkstatt_leitung', 'service_leitung'],
}


# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def get_role_from_title(title: str) -> str:
    """
    Ermittelt Portal-Rolle aus LDAP-Title
    """
    if not title:
        return DEFAULT_ROLE
    return TITLE_TO_ROLE.get(title, DEFAULT_ROLE)


def has_feature_access(role: str, feature: str) -> bool:
    """
    Prüft ob eine Rolle Zugriff auf ein Feature hat
    """
    if feature not in FEATURE_ACCESS:
        return False

    allowed_roles = FEATURE_ACCESS[feature]

    if '*' in allowed_roles:
        return True

    return role in allowed_roles


def get_allowed_features(role: str) -> list:
    """
    Gibt alle Features zurück, auf die eine Rolle Zugriff hat
    """
    allowed = []
    for feature, roles in FEATURE_ACCESS.items():
        if '*' in roles or role in roles:
            allowed.append(feature)
    return allowed


# =============================================================================
# ROLLEN-HIERARCHIE (für Urlaubsplaner)
# =============================================================================

ROLE_HIERARCHY = {
    'admin': ['*'],
    'buchhaltung': ['*'],
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
