#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
LDAP EMPLOYEE SYNC
========================================
Synchronisiert LDAP-User (Active Directory) mit employees-Tabelle
und erstellt ldap_employee_mapping für Authentication

Features:
- Liest alle AD-User aus
- Matched mit employees via Email/Name
- Extrahiert Department aus AD-OU
- Befüllt ldap_employee_mapping
"""

import sqlite3
import ldap3
from ldap3 import Server, Connection, ALL
import re
import sys

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
LDAP_CONFIG_PATH = '/opt/greiner-portal/config/ldap_credentials.env'

# Department-Mapping: LDAP OU → Portal
LDAP_DEPARTMENT_MAPPING = {
    'Geschäftsleitung': 'Geschäftsführung',
    'Geschäftsführung': 'Geschäftsführung',
    'Verkauf': 'Verkauf',
    'Service': 'Service & Empfang',
    'Disposition': 'Disposition',
    'Buchhaltung': 'Verwaltung',
    'Verwaltung': 'Verwaltung',
    'CRM & Marketing': 'Call-Center',
    'Call-Center': 'Call-Center',
    'Kundenzentrale': 'Service & Empfang',
    'Teile und Zubehör': 'Lager & Teile',
    'Lager & Teile': 'Lager & Teile',
    'Werkstatt': 'Werkstatt',
    'Fahrzeuge': 'Fahrzeuge',
}

def load_ldap_config():
    """Lädt LDAP-Config aus env-Datei"""
    config = {}
    try:
        with open(LDAP_CONFIG_PATH, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, val = line.strip().split('=', 1)
                    config[key] = val.strip('"').strip("'")
        return config
    except Exception as e:
        print(f"❌ Fehler beim Laden der LDAP-Config: {e}")
        return None

def extract_department_from_dn(distinguished_name):
    """
    Extrahiert Abteilung aus LDAP distinguishedName
    
    Beispiel:
    CN=Anton Süß,OU=Benutzer,OU=Verkauf,OU=Abteilungen,...
    → "Verkauf"
    """
    match = re.search(r'OU=Benutzer,OU=([^,]+)', distinguished_name)
    if match:
        ldap_dept = match.group(1)
        return LDAP_DEPARTMENT_MAPPING.get(ldap_dept, ldap_dept)
    return None

def normalize_name(name):
    """Normalisiert Namen für Vergleich"""
    if not name:
        return ""
    # Umlaute normalisieren
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue'
    }
    normalized = name.lower()
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return normalized.strip()

def main():
    print("="*70)
    print("🔐 LDAP EMPLOYEE SYNC")
    print("="*70)
    
    # 1. LDAP Config laden
    print("\n📂 Lade LDAP-Konfiguration...")
    ldap_config = load_ldap_config()
    if not ldap_config:
        print("❌ LDAP-Config konnte nicht geladen werden!")
        return 1
    
    print(f"  ✅ Server: {ldap_config.get('LDAP_SERVER', 'N/A')}")
    
    # 2. SQLite verbinden
    print("\n📊 Verbinde zu SQLite...")
    try:
        sqlite_conn = sqlite3.connect(DB_PATH)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        print("  ✅ Verbindung hergestellt")
    except Exception as e:
        print(f"❌ SQLite-Fehler: {e}")
        return 1
    
    # 3. LDAP verbinden
    print("\n🔌 Verbinde zu Active Directory...")
    try:
        server = Server(ldap_config['LDAP_SERVER'], get_info=ALL)
        ldap_conn = Connection(
            server,
            user=ldap_config['LDAP_BIND_DN'],
            password=ldap_config['LDAP_BIND_PASSWORD'],
            auto_bind=True
        )
        print("  ✅ LDAP-Verbindung hergestellt")
    except Exception as e:
        print(f"❌ LDAP-Fehler: {e}")
        return 1
    
    # 4. Alle AD-User holen
    print("\n👥 Hole alle AD-User...")
    try:
        ldap_conn.search(
            search_base=ldap_config['LDAP_BASE_DN'],
            search_filter='(&(objectClass=user)(sAMAccountName=*)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))',
            attributes=['sAMAccountName', 'displayName', 'mail', 'distinguishedName', 'givenName', 'sn']
        )
        
        ldap_users = []
        for entry in ldap_conn.entries:
            username = str(entry.sAMAccountName)
            
            # Überspringe System-Accounts
            if username.startswith('Admin-') or username.startswith('sa-') or username.startswith('ext-') or '$' in username:
                continue
            
            display_name = str(entry.displayName) if entry.displayName else ''
            email = str(entry.mail) if entry.mail else f"{username}@auto-greiner.de"
            dn = str(entry.distinguishedName)
            first_name = str(entry.givenName) if entry.givenName else ''
            last_name = str(entry.sn) if entry.sn else ''
            
            department = extract_department_from_dn(dn)
            
            ldap_users.append({
                'username': username,
                'display_name': display_name,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'department': department,
                'dn': dn
            })
        
        print(f"  ✅ {len(ldap_users)} AD-User gefunden")
        
    except Exception as e:
        print(f"❌ LDAP-Query-Fehler: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 5. Matching mit employees-Tabelle
    print("\n🔄 Matching AD-User ↔ Employees...")
    
    matched = 0
    unmatched = []
    updated = 0
    
    for ldap_user in ldap_users:
        username = ldap_user['username']
        email = ldap_user['email']
        display_name = ldap_user['display_name']
        
        # Versuche Match via Email
        sqlite_cursor.execute("""
            SELECT id, locosoft_id, first_name, last_name, email
            FROM employees
            WHERE LOWER(email) = LOWER(?) AND aktiv = 1
        """, (email,))
        
        emp = sqlite_cursor.fetchone()
        
        if not emp:
            # Fallback: Match via Name
            # Normalisiere displayName
            if ' ' in display_name:
                parts = display_name.split()
                first = ' '.join(parts[:-1])
                last = parts[-1]
            else:
                first = ldap_user['first_name']
                last = ldap_user['last_name']
            
            if first and last:
                sqlite_cursor.execute("""
                    SELECT id, locosoft_id, first_name, last_name, email
                    FROM employees
                    WHERE LOWER(first_name) = LOWER(?) 
                      AND LOWER(last_name) = LOWER(?)
                      AND aktiv = 1
                """, (first, last))
                
                emp = sqlite_cursor.fetchone()
        
        if emp:
            employee_id = emp[0]
            locosoft_id = emp[1]
            
            # In ldap_employee_mapping eintragen
            sqlite_cursor.execute("""
                INSERT OR REPLACE INTO ldap_employee_mapping (
                    ldap_username,
                    ldap_email,
                    employee_id,
                    locosoft_id,
                    verified
                ) VALUES (?, ?, ?, ?, 1)
            """, (username, email, employee_id, locosoft_id))
            
            # Department aktualisieren falls aus LDAP
            if ldap_user['department']:
                sqlite_cursor.execute("""
                    UPDATE employees
                    SET department_name = ?
                    WHERE id = ?
                """, (ldap_user['department'], employee_id))
                if sqlite_cursor.rowcount > 0:
                    updated += 1
            
            matched += 1
            print(f"  ✅ {username:<20} → {emp[2]} {emp[3]} (ID: {employee_id})")
        else:
            unmatched.append(ldap_user)
            print(f"  ⚠️  {username:<20} → Kein Match gefunden")
    
    sqlite_conn.commit()
    
    # 6. Zusammenfassung
    print("\n" + "="*70)
    print("📊 SYNC ABGESCHLOSSEN")
    print("="*70)
    
    print(f"\n✅ Erfolgreich gematcht: {matched}")
    if updated > 0:
        print(f"🔄 Departments aktualisiert: {updated}")
    
    if unmatched:
        print(f"\n⚠️  Nicht gematcht: {len(unmatched)}")
        print("\nUngematchte User (erste 10):")
        for user in unmatched[:10]:
            print(f"  • {user['username']} - {user['display_name']} - {user['email']}")
        
        if len(unmatched) > 10:
            print(f"  ... und {len(unmatched)-10} weitere")
    
    # 7. Statistik
    sqlite_cursor.execute("SELECT COUNT(*) FROM ldap_employee_mapping WHERE verified = 1")
    total_mappings = sqlite_cursor.fetchone()[0]
    
    sqlite_cursor.execute("SELECT COUNT(*) FROM employees WHERE aktiv = 1")
    total_employees = sqlite_cursor.fetchone()[0]
    
    print(f"\n📈 Statistik:")
    print(f"  • LDAP-Mappings gesamt: {total_mappings}")
    print(f"  • Aktive Employees: {total_employees}")
    print(f"  • Coverage: {total_mappings/total_employees*100:.1f}%")
    
    # Beispiele anzeigen
    print(f"\n🔍 Beispiel-Mappings:")
    sqlite_cursor.execute("""
        SELECT 
            lem.ldap_username,
            e.first_name || ' ' || e.last_name as name,
            e.department_name
        FROM ldap_employee_mapping lem
        JOIN employees e ON lem.employee_id = e.id
        WHERE lem.verified = 1
        ORDER BY e.last_name
        LIMIT 10
    """)
    
    print(f"{'LDAP-Username':<25} {'Name':<30} {'Department':<20}")
    print("-" * 75)
    for row in sqlite_cursor.fetchall():
        print(f"{row[0]:<25} {row[1]:<30} {row[2] or 'N/A':<20}")
    
    print("\n✅ Sync erfolgreich abgeschlossen!")
    print("="*70)
    
    ldap_conn.unbind()
    sqlite_conn.close()
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Abgebrochen durch Benutzer")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
