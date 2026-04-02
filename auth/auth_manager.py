"""
Auth Manager für Greiner Portal
Verwaltet User-Login, Sessions und OU-basierte Rollen

Author: Claude
Date: 2025-11-08
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

from auth.ldap_connector import LDAPConnector
from api.db_connection import get_db, convert_placeholders
from config.roles_config import get_role_from_title, get_allowed_features, FEATURE_ACCESS

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OU → Rollen Mapping (Sinnvolle Defaults)
OU_ROLE_MAPPING = {
    'Geschäftsleitung': {
        'role': 'admin',
        'display_name': 'Geschäftsführung',
        'modules': ['*'],  # Alle Module
        'permissions': {
            'full_access': True,
            'see_all_data': True,
            'manage_users': True,
            'export_data': True,
            'financials': True
        }
    },
    'Verkauf': {
        'role': 'verkauf',
        'display_name': 'Verkauf',
        'modules': ['verkauf', 'fahrzeuge'],
        'permissions': {
            'see_own_data': True,
            'see_team_data': False,
            'financials': False
        }
    },
    'Buchhaltung': {
        'role': 'buchhaltung',
        'display_name': 'Buchhaltung',
        'modules': ['bankenspiegel', 'controlling'],
        'permissions': {
            'financials': True,
            'see_all_data': True,
            'export_data': True
        }
    },
    'Service': {
        'role': 'werkstatt',
        'display_name': 'Service/Werkstatt',
        'modules': ['werkstatt', 'service', 'aftersales'],
        'permissions': {
            'see_own_data': True,
            'financials': False
        }
    },
    'Disposition': {
        'role': 'disposition',
        'display_name': 'Disposition',
        'modules': ['verkauf', 'werkstatt', 'fahrzeuge'],
        'permissions': {
            'see_all_data': True,
            'coordinate': True,
            'financials': False
        }
    },
    'CRM & Marketing': {
        'role': 'marketing',
        'display_name': 'CRM & Marketing',
        'modules': ['verkauf', 'kunden'],
        'permissions': {
            'reports': True,
            'see_all_data': True,
            'financials': False
        }
    },
    'Kundenzentrale': {
        'role': 'kundendienst',
        'display_name': 'Kundenzentrale',
        'modules': ['service', 'kunden'],
        'permissions': {
            'see_customer_data': True,
            'financials': False
        }
    },
    'Teile und Zubehör': {
        'role': 'teile',
        'display_name': 'Teile & Zubehör',
        'modules': ['teile', 'lager'],
        'permissions': {
            'inventory': True,
            'financials': False
        }
    },
    'Administration': {
        'role': 'admin',
        'display_name': 'Administration',
        'modules': ['*'],
        'permissions': {
            'full_access': True,
            'see_all_data': True,
            'manage_users': True
        }
    }
}


class User(UserMixin):
    """User-Klasse für Flask-Login"""
    
    def __init__(self, user_id: int, username: str, display_name: str, 
                 email: str, ou: str, roles: List[str], permissions: Dict[str, Any],
                 title: str = None, portal_role: str = None, allowed_features: List[str] = None,
                 company: str = None):
        self.id = user_id
        self.username = username
        self.display_name = display_name
        self.email = email
        self.ou = ou
        self.roles = roles
        self.permissions = permissions
        self.title = title
        self.portal_role = portal_role or 'mitarbeiter'
        self.allowed_features = allowed_features or []
        self.company = company  # TAG 109: AD company Attribut
        # TAG 109: Standort aus company ableiten für Stempeluhr-Default
        if company and 'Landau' in company:
            self.standort = 'landau'
            self.standort_subsidiaries = '3'
        else:
            self.standort = 'deggendorf'
            self.standort_subsidiaries = '1,2'
    
    def get_id(self):
        """Flask-Login benötigt diese Methode"""
        return str(self.id)
    
    def has_role(self, role: str) -> bool:
        """Prüft ob User eine bestimmte Rolle hat"""
        return role in self.roles
    
    def has_permission(self, permission: str) -> bool:
        """Prüft ob User eine bestimmte Berechtigung hat"""
        return self.permissions.get(permission, False)

    def can_access_feature(self, feature: str) -> bool:
        """Prüft ob User auf ein Feature zugreifen darf (TAG76)"""
        return feature in self.allowed_features
    
    def can_access_module(self, module: str) -> bool:
        """Prüft ob User auf ein Modul zugreifen darf"""
        for role_name in self.roles:
            role_config = self._get_role_config(role_name)
            if role_config:
                modules = role_config.get('modules', [])
                if '*' in modules or module in modules:
                    return True
        return False
    
    def _get_role_config(self, role_name: str) -> Optional[Dict]:
        """Holt Rollen-Konfiguration aus OU_ROLE_MAPPING"""
        for ou, config in OU_ROLE_MAPPING.items():
            if config['role'] == role_name:
                return config
        return None
    
    def to_dict(self) -> Dict:
        """User als Dictionary für Session-Storage"""
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'email': self.email,
            'ou': self.ou,
            'roles': self.roles,
            'permissions': self.permissions
        }


class AuthManager:
    """Verwaltet Authentication und Authorization"""

    def __init__(self):
        # TAG 142: Keine db_path mehr - nutzt get_db() für PostgreSQL
        self.ldap = LDAPConnector()
        
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authentifiziert User gegen AD und erstellt User-Objekt
        
        Args:
            username: AD-Username (mit oder ohne @auto-greiner.de)
            password: Passwort
            
        Returns:
            User-Objekt wenn erfolgreich, sonst None
        """
        try:
            # Username normalisieren
            if '@' not in username:
                username = f"{username}@auto-greiner.de"
            
            # LDAP-Authentifizierung
            success, error_msg = self.ldap.authenticate_user(username, password)
            if not success:
                logger.warning(f"❌ Login fehlgeschlagen für: {username}: {error_msg}")
                self._log_auth_event(username, 'login_failed', error_msg or 'Invalid credentials')
                return None
            
            # User-Details aus AD holen
            user_details = self.ldap.get_user_details(username)
            if not user_details:
                logger.error(f"❌ Konnte User-Details nicht laden: {username}")
                return None
            
            # OU aus DN extrahieren
            ou = self._extract_ou_from_dn(user_details['dn'])
            
            # Title aus LDAP holen (nur für Anzeige/Cache, nicht für Zugriff)
            ldap_title = user_details.get('title')

            # Rollen basierend auf OU zuweisen (für user_roles, nur admin wirkt für Zugriff)
            roles, permissions = self._get_roles_for_ou(ou)

            # User in Datenbank cachen/updaten
            user_id = self._cache_user(
                username=username,
                display_name=user_details['display_name'],
                email=user_details['email'],
                ou=ou,
                ad_groups=user_details['groups'],
                roles=roles,
                title=ldap_title
            )

            # Option B: Zugriff nur aus Portal – keine LDAP-Rolle für Berechtigung
            # Wirksame Rolle = admin (user_roles) ODER in Rechteverwaltung zugewiesene Rolle ODER Default mitarbeiter
            if self._is_db_admin(user_id):
                portal_role = 'admin'
                roles = ['admin']
                permissions = OU_ROLE_MAPPING['Geschäftsleitung']['permissions']
                # 'admin' in allowed_features damit can_access_feature('admin') für Rechteverwaltung/Speichern etc. True ist
                allowed_features = ['admin'] + list(FEATURE_ACCESS.keys())
                logger.info(f"👑 Admin-Override für {username} - alle Features freigeschaltet")
            else:
                override = self._get_portal_role_override(user_id)
                portal_role = (override or 'mitarbeiter').strip() or 'mitarbeiter'
                allowed_features = get_allowed_features(portal_role)
                logger.info(f"✅ Login: {username} → Portal-Rolle: {portal_role} (aus {'Rechteverwaltung' if override else 'Default'})")

            # User-Objekt erstellen (TAG 109: company für Standort)
            user = User(
                user_id=user_id,
                username=username,
                display_name=user_details['display_name'],
                email=user_details['email'],
                ou=ou,
                roles=roles,
                permissions=permissions,
                title=ldap_title,
                portal_role=portal_role,
                allowed_features=allowed_features,
                company=user_details.get('company')  # TAG 109: Für Standort-Default
            )
            
            # Erfolgreichen Login loggen
            self._log_auth_event(username, 'login_success', f'OU: {ou}, Rollen: {roles}')
            logger.info(f"✅ Login erfolgreich: {user.display_name} ({ou}) → Portal-Rolle: {portal_role}, Features: {len(allowed_features)}")
            
            return user
            
        except Exception as e:
            logger.error(f"❌ Fehler bei User-Authentifizierung: {str(e)}")
            return None
    
    def _extract_ou_from_dn(self, dn: str) -> str:
        """
        Extrahiert die relevante OU aus dem DN
        
        Beispiel:
        CN=Florian Greiner,OU=Benutzer,OU=Geschäftsleitung,OU=Abteilungen,...
        → Geschäftsleitung
        """
        try:
            # DN in Teile splitten
            parts = dn.split(',')
            
            # Suche nach OU= (nicht OU=Benutzer oder OU=Abteilungen)
            for part in parts:
                if part.startswith('OU='):
                    ou_name = part.replace('OU=', '').strip()
                    # Überspringe generische OUs
                    if ou_name not in ['Benutzer', 'Abteilungen', 'AUTO-GREINER']:
                        # Prüfe ob diese OU in unserem Mapping ist
                        if ou_name in OU_ROLE_MAPPING:
                            return ou_name
            
            # Fallback: Erste OU nach CN
            for part in parts:
                if part.startswith('OU='):
                    return part.replace('OU=', '').strip()
            
            return 'Unknown'
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Extrahieren der OU: {str(e)}")
            return 'Unknown'
    
    def _get_roles_for_ou(self, ou: str) -> tuple:
        """
        Gibt Rollen und Permissions für eine OU zurück
        
        Returns:
            (roles: List[str], permissions: Dict)
        """
        if ou in OU_ROLE_MAPPING:
            config = OU_ROLE_MAPPING[ou]
            return ([config['role']], config['permissions'])
        else:
            # Fallback für unbekannte OUs: Basis-Rechte
            logger.warning(f"⚠️ Unbekannte OU: {ou} → Basis-Rechte")
            return (['user'], {'see_own_data': True})

    def _get_portal_role_override(self, user_id: int):
        """
        Granulare Rechte: Liefert die in der Rechteverwaltung gesetzte Portal-Rolle.
        Return: Rolle (str) oder None wenn kein Override.
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                convert_placeholders('SELECT portal_role_override FROM users WHERE id = ?'),
                (user_id,)
            )
            row = cursor.fetchone()
            conn.close()
            if row and row.get('portal_role_override'):
                return row['portal_role_override'].strip()
            return None
        except Exception as e:
            logger.warning(f"portal_role_override lesen: {e}")
            return None

    def _is_db_admin(self, user_id: int) -> bool:
        """
        TAG134: Prüft ob User in user_roles als admin markiert ist.
        Ermöglicht manuelle Admin-Zuweisung unabhängig vom LDAP-Title.
        TAG142: Umgestellt auf PostgreSQL via get_db()
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(convert_placeholders('''
                SELECT 1 FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = ? AND r.name = 'admin'
            '''), (user_id,))
            is_admin = cursor.fetchone() is not None
            conn.close()
            return is_admin
        except Exception as e:
            logger.error(f"❌ Fehler bei Admin-Check: {str(e)}")
            return False

    def _cache_user(self, username: str, display_name: str, email: str,
                    ou: str, ad_groups: List[str], roles: List[str], title: str = None) -> int:
        """
        Speichert/aktualisiert User in DB (Cache)
        TAG142: Umgestellt auf PostgreSQL via get_db()

        Returns:
            user_id
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Prüfe ob User existiert (case-insensitiv: gleiche Person, anderer Schreibweise → Update, kein Doppel-Eintrag)
            cursor.execute(convert_placeholders(
                'SELECT id FROM users WHERE LOWER(TRIM(username)) = LOWER(TRIM(?))'
            ), (username,))
            existing = cursor.fetchone()

            if existing:
                # User updaten
                user_id = existing[0]
                cursor.execute(convert_placeholders('''
                    UPDATE users
                    SET display_name = ?, email = ?, ou = ?, title = ?,
                        ad_groups = ?, last_login = ?
                    WHERE id = ?
                '''), (display_name, email, ou, title, json.dumps(ad_groups),
                      datetime.now().isoformat(), user_id))

                # Rollen aktualisieren - ABER Admin-Rollen behalten!
                # Prüfen ob User bereits Admin ist
                cursor.execute(convert_placeholders('''
                    SELECT 1 FROM user_roles ur
                    JOIN roles r ON ur.role_id = r.id
                    WHERE ur.user_id = ? AND r.name = 'admin'
                '''), (user_id,))
                is_admin = cursor.fetchone() is not None

                if is_admin:
                    # Admin-User: Rollen NICHT überschreiben
                    logger.info(f"👑 User {username} ist Admin - Rolle wird beibehalten")
                    conn.commit()
                    conn.close()
                    return user_id

                # Nicht-Admin: Rollen basierend auf OU aktualisieren
                cursor.execute(convert_placeholders('DELETE FROM user_roles WHERE user_id = ?'), (user_id,))
            else:
                # Neuen User anlegen - PostgreSQL RETURNING für ID
                cursor.execute(convert_placeholders('''
                    INSERT INTO users (username, display_name, email, ou, title, ad_groups, last_login, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    RETURNING id
                '''), (username, display_name, email, ou, title, json.dumps(ad_groups),
                      datetime.now().isoformat(), datetime.now().isoformat()))
                result = cursor.fetchone()
                user_id = result[0] if result else None

            # Rollen zuweisen
            for role_name in roles:
                # Hole role_id
                cursor.execute(convert_placeholders('SELECT id FROM roles WHERE name = ?'), (role_name,))
                role = cursor.fetchone()
                if role:
                    role_id = role[0]
                    cursor.execute(convert_placeholders('''
                        INSERT INTO user_roles (user_id, role_id, assigned_at)
                        VALUES (?, ?, ?)
                    '''), (user_id, role_id, datetime.now().isoformat()))

            conn.commit()
            conn.close()

            return user_id

        except Exception as e:
            logger.error(f"❌ Fehler beim Cachen des Users: {str(e)}")
            raise
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Lädt User aus DB (für Session-Management)
        TAG142: Umgestellt auf PostgreSQL via get_db()

        Args:
            user_id: User-ID

        Returns:
            User-Objekt oder None
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            # User laden
            cursor.execute(convert_placeholders('SELECT * FROM users WHERE id = ?'), (user_id,))
            user_row = cursor.fetchone()

            if not user_row:
                conn.close()
                return None

            # Rollen laden
            cursor.execute(convert_placeholders('''
                SELECT r.name
                FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = ?
            '''), (user_id,))
            roles = [row[0] for row in cursor.fetchall()]

            conn.close()
            
            # Permissions aus Rollen ableiten
            permissions = {}
            for role_name in roles:
                for ou, config in OU_ROLE_MAPPING.items():
                    if config['role'] == role_name:
                        permissions.update(config['permissions'])
            
            # Option B: Portal-Rolle nur aus DB – kein LDAP-Fallback
            from config.roles_config import get_allowed_features, FEATURE_ACCESS
            user_title = user_row['title']
            if 'admin' in roles:
                portal_role = 'admin'
                permissions = OU_ROLE_MAPPING['Geschäftsleitung']['permissions']
                allowed_features = ['admin'] + list(FEATURE_ACCESS.keys())
                logger.info(f"👑 Admin-Override für User {user_id} - alle Features freigeschaltet")
            else:
                override = user_row.get('portal_role_override')
                portal_role = (override or 'mitarbeiter').strip() or 'mitarbeiter'
                allowed_features = get_allowed_features(portal_role)

            # TAG 109: Company aus LDAP holen für Standort-Default
            company = None
            try:
                user_details = self.ldap.get_user_details(user_row['username'])
                if user_details:
                    company = user_details.get('company')
            except:
                pass  # Falls LDAP nicht erreichbar, company bleibt None
            
            # User-Objekt erstellen
            user = User(
                user_id=user_row['id'],
                username=user_row['username'],
                display_name=user_row['display_name'],
                email=user_row['email'],
                ou=user_row['ou'],
                roles=roles,
                permissions=permissions,
                title=user_title,
                portal_role=portal_role,
                allowed_features=allowed_features,
                company=company  # TAG 109: Für Standort-Default
            )
            
            return user
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Users: {str(e)}")
            return None
    
    def _log_auth_event(self, username: str, action: str, details: str,
                        ip_address: str = None):
        """
        Loggt Authentication-Events in Audit-Log
        TAG142: Umgestellt auf PostgreSQL via get_db()
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            # User-ID holen (falls vorhanden, case-insensitiv)
            cursor.execute(convert_placeholders(
                'SELECT id FROM users WHERE LOWER(TRIM(username)) = LOWER(TRIM(?))'
            ), (username,))
            user_row = cursor.fetchone()
            user_id = user_row[0] if user_row else None

            # Event loggen
            success = 'failed' not in action.lower()
            cursor.execute(convert_placeholders('''
                INSERT INTO auth_audit_log (user_id, action, success, ip_address, timestamp, details_json)
                VALUES (?, ?, ?, ?, ?, ?)
            '''), (user_id, action, success, ip_address, datetime.now().isoformat(), details))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"❌ Fehler beim Loggen des Auth-Events: {str(e)}")

    def change_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """
        Ändert das AD-Passwort des Benutzers (Self-Service).
        Das neue Passwort gilt sofort für Windows-Anmeldung und Drive.

        Returns:
            (success: bool, error_message: Optional[str])
        """
        return self.ldap.change_user_password(username, old_password, new_password)
    
    def logout_user(self, user: User):
        """Loggt User aus (für Audit-Trail)"""
        try:
            self._log_auth_event(user.username, 'logout', f'OU: {user.ou}')
            logger.info(f"👋 Logout: {user.display_name}")
        except Exception as e:
            logger.error(f"❌ Fehler beim Logout: {str(e)}")


# Singleton-Instanz
_auth_manager_instance = None

def get_auth_manager() -> AuthManager:
    """Gibt Singleton-Instanz des AuthManagers zurück"""
    global _auth_manager_instance
    if _auth_manager_instance is None:
        _auth_manager_instance = AuthManager()
    return _auth_manager_instance
