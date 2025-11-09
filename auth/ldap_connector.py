"""
LDAP CONNECTOR - ACTIVE DIRECTORY INTEGRATION
==============================================

Verbindet das Greiner Portal mit dem Active Directory.

Features:
- User Authentication gegen AD
- Gruppen-Mitgliedschaften auslesen
- User-Suche
- Secure LDAPS (Port 636)

Requires:
    pip install ldap3

Configuration:
    config/ldap_credentials.env

Author: Claude AI
Date: 08.11.2025
Version: 1.0
"""

import os
import logging
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from ldap3 import Server, Connection, ALL, NTLM, SIMPLE, ALL_ATTRIBUTES
from ldap3.core.exceptions import LDAPException, LDAPBindError

# Logger
logger = logging.getLogger(__name__)


class LDAPConnector:
    """
    LDAP/Active Directory Connector
    
    Verwaltet die Verbindung zum AD und stellt Methoden für
    Authentication und Gruppen-Abfragen bereit.
    """
    
    def __init__(self, config_file: str = 'config/ldap_credentials.env'):
        """
        Initialisiert den LDAP-Connector
        
        Args:
            config_file: Pfad zur Config-Datei
        """
        self.config = self._load_config(config_file)
        self.server = self._create_server()
        
    def _load_config(self, config_file: str) -> Dict[str, str]:
        """
        Lädt LDAP-Konfiguration aus .env Datei
        
        Args:
            config_file: Pfad zur Config-Datei
            
        Returns:
            Dict mit Config-Werten
        """
        config = {}
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"LDAP Config nicht gefunden: {config_file}\n"
                f"Bitte erstelle die Datei mit den AD-Credentials!"
            )
        
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        
        # Validiere erforderliche Keys
        required = ['LDAP_SERVER', 'LDAP_BASE_DN', 'LDAP_BIND_DN', 'LDAP_BIND_PASSWORD']
        missing = [k for k in required if k not in config]
        if missing:
            raise ValueError(f"Fehlende Config-Werte: {', '.join(missing)}")
        
        logger.info(f"✅ LDAP Config geladen: {config['LDAP_SERVER']}")
        return config
    
    def _create_server(self) -> Server:
        """
        Erstellt LDAP-Server-Objekt
        
        Returns:
            ldap3.Server Instanz
        """
        use_ssl = self.config.get('LDAP_USE_SSL', 'True').lower() == 'true'
        port = int(self.config.get('LDAP_PORT', '636' if use_ssl else '389'))
        
        server = Server(
            self.config['LDAP_SERVER'],
            port=port,
            use_ssl=use_ssl,
            get_info=ALL
        )
        
        logger.info(f"✅ LDAP Server konfiguriert: {self.config['LDAP_SERVER']}:{port} (SSL: {use_ssl})")
        return server
    
    def _get_service_connection(self) -> Connection:
        """
        Erstellt Connection mit Service-Account
        
        Returns:
            ldap3.Connection mit Service-Account
        """
        conn = Connection(
            self.server,
            user=self.config['LDAP_BIND_DN'],
            password=self.config['LDAP_BIND_PASSWORD'],
            auto_bind=True,
            raise_exceptions=True
        )
        return conn
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Authentifiziert einen User gegen AD
        
        Args:
            username: Username (mit oder ohne @domain)
            password: Passwort
            
        Returns:
            (success: bool, error_message: Optional[str])
        """
        try:
            # Username normalisieren
            if '@' not in username:
                # Ergänze Domain
                domain = self.config['LDAP_SERVER'].split('.', 1)[-1]
                username = f"{username}@{domain}"
            
            # Versuche zu binden
            conn = Connection(
                self.server,
                user=username,
                password=password,
                auto_bind=True,
                raise_exceptions=True
            )
            
            # Erfolgreich!
            conn.unbind()
            logger.info(f"✅ User authentifiziert: {username}")
            return (True, None)
            
        except LDAPBindError as e:
            logger.warning(f"❌ Login fehlgeschlagen für {username}: Ungültige Credentials")
            return (False, "Ungültiger Benutzername oder Passwort")
            
        except LDAPException as e:
            logger.error(f"❌ LDAP-Fehler bei Login von {username}: {e}")
            return (False, f"AD-Verbindungsfehler: {str(e)}")
            
        except Exception as e:
            logger.error(f"❌ Unerwarteter Fehler bei Login von {username}: {e}")
            return (False, "Interner Fehler bei der Anmeldung")
    
    def get_user_details(self, username: str) -> Optional[Dict[str, any]]:
        """
        Holt User-Details aus AD
        
        Args:
            username: Username (SamAccountName oder UPN)
            
        Returns:
            Dict mit User-Details oder None
        """
        try:
            conn = self._get_service_connection()
            
            # Username normalisieren (nur SamAccountName, ohne @domain)
            sam_account = username.split('@')[0] if '@' in username else username
            
            # Suche User
            search_filter = f"(sAMAccountName={sam_account})"
            conn.search(
                search_base=self.config['LDAP_BASE_DN'],
                search_filter=search_filter,
                attributes=['cn', 'displayName', 'mail', 'sAMAccountName', 
                           'memberOf', 'distinguishedName', 'userPrincipalName']
            )
            
            if not conn.entries:
                logger.warning(f"❌ User nicht gefunden: {username}")
                return None
            
            entry = conn.entries[0]
            
            # Extrahiere Gruppen
            groups = []
            if hasattr(entry, 'memberOf'):
                for group_dn in entry.memberOf:
                    # Extrahiere CN aus DN: CN=Verkauf,OU=... → Verkauf
                    cn = group_dn.split(',')[0].replace('CN=', '')
                    groups.append(cn)
            
            user_data = {
                'username': str(entry.sAMAccountName),
                'display_name': str(entry.displayName) if hasattr(entry, 'displayName') else str(entry.cn),
                'email': str(entry.mail) if hasattr(entry, 'mail') else None,
                'upn': str(entry.userPrincipalName) if hasattr(entry, 'userPrincipalName') else None,
                'dn': str(entry.distinguishedName),
                'groups': groups
            }
            
            conn.unbind()
            logger.info(f"✅ User-Details geladen: {username} (Gruppen: {len(groups)})")
            return user_data
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von User-Details für {username}: {e}")
            return None
    
    def get_user_groups(self, username: str) -> List[str]:
        """
        Holt nur die Gruppen eines Users
        
        Args:
            username: Username
            
        Returns:
            Liste von Gruppen-Namen
        """
        user_details = self.get_user_details(username)
        return user_details['groups'] if user_details else []
    
    def search_users(self, search_term: str, max_results: int = 50) -> List[Dict[str, str]]:
        """
        Sucht User im AD
        
        Args:
            search_term: Suchbegriff (Name, Username, Email)
            max_results: Max. Anzahl Ergebnisse
            
        Returns:
            Liste von User-Dicts
        """
        try:
            conn = self._get_service_connection()
            
            # Suche in mehreren Feldern
            search_filter = f"(&(objectClass=user)(|(cn=*{search_term}*)(sAMAccountName=*{search_term}*)(mail=*{search_term}*)))"
            
            conn.search(
                search_base=self.config['LDAP_BASE_DN'],
                search_filter=search_filter,
                attributes=['cn', 'sAMAccountName', 'mail', 'displayName'],
                size_limit=max_results
            )
            
            users = []
            for entry in conn.entries:
                users.append({
                    'username': str(entry.sAMAccountName),
                    'display_name': str(entry.displayName) if hasattr(entry, 'displayName') else str(entry.cn),
                    'email': str(entry.mail) if hasattr(entry, 'mail') else None
                })
            
            conn.unbind()
            logger.info(f"✅ User-Suche '{search_term}': {len(users)} Ergebnisse")
            return users
            
        except Exception as e:
            logger.error(f"❌ Fehler bei User-Suche '{search_term}': {e}")
            return []
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Testet die LDAP-Verbindung
        
        Returns:
            (success: bool, message: str)
        """
        try:
            conn = self._get_service_connection()
            
            # Einfache Suche um Connection zu testen
            conn.search(
                search_base=self.config['LDAP_BASE_DN'],
                search_filter='(objectClass=*)',
                search_scope='BASE',
                attributes=['objectClass']
            )
            
            conn.unbind()
            msg = f"✅ LDAP-Verbindung erfolgreich: {self.config['LDAP_SERVER']}"
            logger.info(msg)
            return (True, msg)
            
        except Exception as e:
            msg = f"❌ LDAP-Verbindung fehlgeschlagen: {str(e)}"
            logger.error(msg)
            return (False, msg)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Globale Instanz (Singleton-Pattern)
_ldap_connector = None

def get_ldap_connector() -> LDAPConnector:
    """
    Holt die globale LDAP-Connector-Instanz
    
    Returns:
        LDAPConnector Instanz
    """
    global _ldap_connector
    if _ldap_connector is None:
        _ldap_connector = LDAPConnector()
    return _ldap_connector


# ============================================================================
# CLI-TOOL ZUM TESTEN
# ============================================================================

if __name__ == '__main__':
    """
    Test-Script für LDAP-Connector
    
    Usage:
        python auth/ldap_connector.py
    """
    import sys
    
    # Logging setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("="*70)
    print("🔐 LDAP CONNECTOR TEST")
    print("="*70)
    print()
    
    try:
        # Connector erstellen
        print("1️⃣ Initialisiere LDAP-Connector...")
        connector = LDAPConnector()
        print("   ✅ Connector erstellt")
        print()
        
        # Connection testen
        print("2️⃣ Teste LDAP-Verbindung...")
        success, message = connector.test_connection()
        print(f"   {message}")
        print()
        
        if not success:
            print("❌ Verbindung fehlgeschlagen! Prüfe Config.")
            sys.exit(1)
        
        # User-Input für Test-Login
        print("3️⃣ Test-Login (optional):")
        print("   Drücke Enter zum Überspringen oder gib Username ein")
        username = input("   Username: ").strip()
        
        if username:
            password = input("   Password: ").strip()
            
            print()
            print("   Authentifiziere...")
            success, error = connector.authenticate_user(username, password)
            
            if success:
                print("   ✅ Login erfolgreich!")
                print()
                print("   Lade User-Details...")
                details = connector.get_user_details(username)
                if details:
                    print(f"   ✅ User: {details['display_name']}")
                    print(f"      Email: {details['email']}")
                    print(f"      Gruppen: {', '.join(details['groups']) if details['groups'] else 'Keine'}")
            else:
                print(f"   ❌ Login fehlgeschlagen: {error}")
        
        print()
        print("="*70)
        print("✅ LDAP CONNECTOR TEST ABGESCHLOSSEN")
        print("="*70)
        
    except Exception as e:
        print()
        print("="*70)
        print(f"❌ FEHLER: {e}")
        print("="*70)
        import traceback
        traceback.print_exc()
        sys.exit(1)
