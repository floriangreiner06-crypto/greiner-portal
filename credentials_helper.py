#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Credentials Helper für Greiner Portal
Liest Credentials aus config/credentials.json
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class CredentialsManager:
    """
    Verwaltet den Zugriff auf Credentials
    
    Usage:
        creds = CredentialsManager()
        
        # Datenbank-Credentials
        db_config = creds.get_database('locosoft')
        
        # Stellantis ZIP-Passwort
        stellantis_pwd = creds.get_stellantis_password()
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialisiert den Credentials Manager
        
        Args:
            credentials_path: Pfad zu credentials.json
                             Default: /opt/greiner-portal/config/credentials.json
        """
        if credentials_path is None:
            # Versuche verschiedene Pfade
            possible_paths = [
                '/opt/greiner-portal/config/credentials.json',
                'config/credentials.json',
                '../config/credentials.json'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    credentials_path = path
                    break
            
            if credentials_path is None:
                raise FileNotFoundError(
                    "credentials.json nicht gefunden. Pfade geprüft:\n" +
                    "\n".join(f"  - {p}" for p in possible_paths)
                )
        
        self.credentials_path = Path(credentials_path)
        self._credentials = None
        self.load()
    
    def load(self) -> Dict[str, Any]:
        """Lädt Credentials aus JSON-Datei"""
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Credentials-Datei nicht gefunden: {self.credentials_path}"
            )
        
        with open(self.credentials_path, 'r') as f:
            self._credentials = json.load(f)
        
        return self._credentials
    
    def get_database(self, db_name: str) -> Dict[str, Any]:
        """
        Holt Datenbank-Credentials
        
        Args:
            db_name: Name der Datenbank (z.B. 'locosoft', 'sqlite')
            
        Returns:
            Dict mit DB-Config (host, port, user, password, etc.)
            
        Raises:
            KeyError: Wenn Datenbank nicht in credentials.json
        """
        if 'databases' not in self._credentials:
            raise KeyError("'databases' nicht in credentials.json gefunden")
        
        if db_name not in self._credentials['databases']:
            available = list(self._credentials['databases'].keys())
            raise KeyError(
                f"Datenbank '{db_name}' nicht gefunden. "
                f"Verfügbar: {', '.join(available)}"
            )
        
        return self._credentials['databases'][db_name]
    
    def get_stellantis_password(self, rrdi: str = None) -> str:
        """
        Holt Stellantis ZIP-Passwort
        
        Args:
            rrdi: Optional - RRDI für spezifischen Account (z.B. 'DE0154X', 'DE08250')
                  Falls None, wird das erste verfügbare Passwort zurückgegeben
            
        Returns:
            Passwort als String
            
        Raises:
            KeyError: Wenn Stellantis-Config fehlt
        """
        if 'external_systems' not in self._credentials:
            raise KeyError(
                "'external_systems' nicht in credentials.json gefunden. "
                "Bitte Stellantis-Konfiguration hinzufügen."
            )
        
        if 'stellantis' not in self._credentials['external_systems']:
            raise KeyError(
                "'stellantis' nicht in external_systems gefunden. "
                "Bitte Stellantis-Konfiguration hinzufügen."
            )
        
        stellantis_config = self._credentials['external_systems']['stellantis']
        
        # Neue Struktur mit accounts
        if 'accounts' in stellantis_config:
            if rrdi:
                # Spezifisches Passwort für RRDI
                if rrdi not in stellantis_config['accounts']:
                    available = list(stellantis_config['accounts'].keys())
                    raise KeyError(
                        f"RRDI '{rrdi}' nicht gefunden. "
                        f"Verfügbar: {', '.join(available)}"
                    )
                return stellantis_config['accounts'][rrdi]['zip_password']
            else:
                # Erstes verfügbares Passwort
                first_account = list(stellantis_config['accounts'].values())[0]
                return first_account['zip_password']
        
        # Legacy: Alte Struktur mit nur einem Passwort
        elif 'zip_password' in stellantis_config:
            return stellantis_config['zip_password']
        
        else:
            raise KeyError(
                "'zip_password' oder 'accounts' nicht in Stellantis-Config gefunden"
            )
    
    def get_stellantis_accounts(self) -> dict:
        """
        Holt alle Stellantis-Accounts
        
        Returns:
            Dict mit RRDIs als Keys und Account-Configs als Values
            Beispiel: {'DE0154X': {'rrdi': 'DE0154X', 'zip_password': '...', ...}}
        """
        if 'external_systems' not in self._credentials:
            raise KeyError("'external_systems' nicht in credentials.json gefunden")
        
        if 'stellantis' not in self._credentials['external_systems']:
            raise KeyError("'stellantis' nicht in external_systems gefunden")
        
        stellantis_config = self._credentials['external_systems']['stellantis']
        
        if 'accounts' not in stellantis_config:
            raise KeyError("'accounts' nicht in Stellantis-Config gefunden")
        
        return stellantis_config['accounts']
    
    def get_stellantis_config(self) -> Dict[str, str]:
        """
        Holt komplette Stellantis-Konfiguration
        
        Returns:
            Dict mit zip_password, source_path, etc.
        """
        if 'external_systems' not in self._credentials:
            raise KeyError("'external_systems' nicht in credentials.json gefunden")
        
        if 'stellantis' not in self._credentials['external_systems']:
            raise KeyError("'stellantis' nicht in external_systems gefunden")
        
        return self._credentials['external_systems']['stellantis']
    
    def get_all(self) -> Dict[str, Any]:
        """Gibt alle Credentials zurück (für Debug)"""
        return self._credentials


# Für schnellen Zugriff
def get_credentials() -> CredentialsManager:
    """Factory-Funktion für CredentialsManager"""
    return CredentialsManager()


if __name__ == '__main__':
    """Test-Script"""
    try:
        creds = get_credentials()
        print("✓ Credentials erfolgreich geladen")
        print(f"\nVerfügbare Datenbanken: {list(creds._credentials.get('databases', {}).keys())}")
        
        # Test Stellantis
        try:
            accounts = creds.get_stellantis_accounts()
            print(f"\n✓ Stellantis-Accounts gefunden: {len(accounts)}")
            for rrdi, account in accounts.items():
                pwd = account['zip_password']
                desc = account.get('description', 'N/A')
                print(f"  • {rrdi}: {'*' * len(pwd)} ({desc})")
        except KeyError as e:
            print(f"⚠ Stellantis-Config fehlt: {e}")
        
    except Exception as e:
        print(f"✗ Fehler: {e}")
