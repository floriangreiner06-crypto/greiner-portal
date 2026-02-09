"""
ROLLEN-KONFIGURATION - GREINER PORTAL
======================================
Mapping von LDAP-Titles zu Portal-Rollen und Feature-Zugriff

Erstellt: TAG 76 (24.11.2025)
Aktualisiert: TAG 77 (24.11.2025) - Buchhaltung + Serviceleitung hinzugefügt
Aktualisiert: TAG 190 (14.01.2026) - DB-basierte Feature-Zugriffsverwaltung
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
    'Gewährleistung und Auftragsvorbereitung': 'service',  # TAG 190: David Moser

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
    
    # QA Dashboard (TAG 192) - alle Mitarbeiter
    'qa_dashboard': ['*'],

    # WhatsApp (TAG 211)
    'whatsapp_teile': ['admin', 'lager', 'werkstatt_leitung', 'service_leitung', 'serviceberater'],  # Teile-Handel
    'whatsapp_verkauf': ['admin', 'verkauf_leitung', 'verkauf'],  # Verkäufer-Chat
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
    
    TAG 192: Verwendet get_feature_access_from_db() für DB-basierte Features
    """
    # Verwende DB-basierte Feature-Zugriffe (mit Cache)
    feature_access = get_feature_access_from_db()
    
    allowed = []
    for feature, roles in feature_access.items():
        if '*' in roles or role in roles:
            allowed.append(feature)
    return allowed


# =============================================================================
# DB-BASIERTE FEATURE-ZUGRIFFSVERWALTUNG (TAG 190)
# =============================================================================

# Cache für Feature-Zugriff (TAG 192: Performance-Optimierung)
_feature_access_cache = None
_cache_timestamp = None
from datetime import datetime, timedelta
CACHE_TTL = timedelta(minutes=5)

def get_feature_access_from_db():
    """
    Lädt Feature-Zugriff aus Datenbank, Fallback auf FEATURE_ACCESS
    
    TAG 190: Hybrid-Ansatz - DB hat Priorität, Config als Fallback
    TAG 192: Mit In-Memory-Cache (5 Min TTL) für Performance
    """
    global _feature_access_cache, _cache_timestamp
    
    # Cache prüfen
    if _feature_access_cache and _cache_timestamp:
        if datetime.now() - _cache_timestamp < CACHE_TTL:
            return _feature_access_cache
    
    try:
        from api.db_connection import get_db
        import logging
        logger = logging.getLogger(__name__)
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT feature_name, role_name 
            FROM feature_access 
            ORDER BY feature_name, role_name
        ''')
        
        db_access = {}
        for row in cursor.fetchall():
            feature = row['feature_name']
            role = row['role_name']
            if feature not in db_access:
                db_access[feature] = []
            db_access[feature].append(role)
        
        conn.close()
        
        # Mit FEATURE_ACCESS zusammenführen (DB hat Priorität)
        merged = FEATURE_ACCESS.copy()
        merged.update(db_access)
        
        # Cache aktualisieren
        _feature_access_cache = merged
        _cache_timestamp = datetime.now()
        
        return merged
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Fehler beim Laden aus DB, verwende Config: {e}")
        return FEATURE_ACCESS


def has_feature_access_db(role: str, feature: str) -> bool:
    """
    Prüft ob eine Rolle Zugriff auf ein Feature hat (DB-basiert)
    
    TAG 190: Verwendet get_feature_access_from_db() statt FEATURE_ACCESS
    """
    feature_access = get_feature_access_from_db()
    
    if feature not in feature_access:
        return False
    
    allowed_roles = feature_access[feature]
    
    if '*' in allowed_roles:
        return True
    
    return role in allowed_roles


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
