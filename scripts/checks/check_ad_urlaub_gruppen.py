#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AD Urlaubs-Gruppen Check
========================
Zeigt alle AD-Gruppen mit "Urlaub" im Namen und deren Mitglieder.
Nutzt dieselbe LDAP-Config wie das Portal: config/ldap_credentials.env

Ausführen:
    python3 /opt/greiner-portal/scripts/checks/check_ad_urlaub_gruppen.py
"""

import os
import ldap3
from ldap3 import Server, Connection, ALL, SUBTREE

LDAP_CONFIG_PATH = '/opt/greiner-portal/config/ldap_credentials.env'


def load_ldap_config():
    """Lädt LDAP-Config aus ldap_credentials.env (wie Portal und Sync-Scripts)."""
    config = {}
    if not os.path.isfile(LDAP_CONFIG_PATH):
        return config
    with open(LDAP_CONFIG_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    return config


def main():
    print("=" * 70)
    print("AD URLAUBS-GRUPPEN CHECK")
    print("=" * 70)
    print()

    ldap_config = load_ldap_config()
    if not ldap_config.get('LDAP_BIND_DN') or not ldap_config.get('LDAP_BIND_PASSWORD'):
        print(f"❌ Config nicht gefunden oder unvollständig: {LDAP_CONFIG_PATH}")
        print("   Bitte LDAP_BIND_DN und LDAP_BIND_PASSWORD setzen.")
        return

    server_name = ldap_config.get('LDAP_SERVER', 'srvdc01.auto-greiner.de')
    port = int(ldap_config.get('LDAP_PORT', '389'))
    bind_dn = ldap_config['LDAP_BIND_DN']
    bind_password = ldap_config['LDAP_BIND_PASSWORD']
    base_dn = ldap_config.get('LDAP_BASE_DN', 'DC=auto-greiner,DC=de')

    # 1. Verbindung herstellen
    print(f"Verbinde zu {server_name}...")
    try:
        server = Server(server_name, port=port, get_info=ALL)
        conn = Connection(server, user=bind_dn, password=bind_password, auto_bind=True)
        print(f"✅ Verbunden als {bind_dn}")
    except Exception as e:
        print(f"❌ Verbindungsfehler: {e}")
        return
    
    print()
    
    # 2. Alle Gruppen mit "Urlaub" im Namen suchen
    print("-" * 70)
    print("GRUPPEN MIT 'URLAUB' IM NAMEN:")
    print("-" * 70)
    
    conn.search(
        search_base=base_dn,
        search_filter='(&(objectClass=group)(cn=*Urlaub*))',
        search_scope=SUBTREE,
        attributes=['cn', 'description', 'member', 'distinguishedName']
    )
    
    urlaub_gruppen = []
    for entry in conn.entries:
        gruppe = {
            'name': str(entry.cn),
            'dn': str(entry.distinguishedName),
            'description': str(entry.description) if entry.description else '-',
            'members': []
        }
        
        # Mitglieder parsen
        if entry.member:
            for member_dn in entry.member:
                # CN aus DN extrahieren
                if 'CN=' in str(member_dn):
                    member_name = str(member_dn).split('CN=')[1].split(',')[0]
                    gruppe['members'].append(member_name)
        
        urlaub_gruppen.append(gruppe)
    
    if not urlaub_gruppen:
        print("❌ Keine Gruppen mit 'Urlaub' im Namen gefunden!")
    else:
        for g in sorted(urlaub_gruppen, key=lambda x: x['name']):
            print(f"\n📁 {g['name']}")
            print(f"   Beschreibung: {g['description']}")
            print(f"   Mitglieder ({len(g['members'])}):")
            if g['members']:
                for m in sorted(g['members']):
                    print(f"      - {m}")
            else:
                print(f"      (keine)")
    
    print()
    print("-" * 70)
    print("ALLE GRP_* GRUPPEN (Portal-relevant):")
    print("-" * 70)
    
    # 3. Alle GRP_* Gruppen suchen
    conn.search(
        search_base=base_dn,
        search_filter='(&(objectClass=group)(cn=GRP_*))',
        search_scope=SUBTREE,
        attributes=['cn', 'description', 'member']
    )
    
    grp_gruppen = []
    for entry in conn.entries:
        gruppe = {
            'name': str(entry.cn),
            'description': str(entry.description) if entry.description else '-',
            'member_count': len(entry.member) if entry.member else 0,
            'members': []
        }
        if entry.member:
            for member_dn in entry.member:
                if 'CN=' in str(member_dn):
                    member_name = str(member_dn).split('CN=')[1].split(',')[0]
                    gruppe['members'].append(member_name)
        grp_gruppen.append(gruppe)
    
    for g in sorted(grp_gruppen, key=lambda x: x['name']):
        print(f"\n📁 {g['name']} ({g['member_count']} Mitglieder)")
        if g['members']:
            for m in sorted(g['members'])[:10]:  # Max 10 zeigen
                print(f"      - {m}")
            if len(g['members']) > 10:
                print(f"      ... und {len(g['members']) - 10} weitere")
    
    print()
    print("-" * 70)
    print("SPEZIFISCHE PRÜFUNG: Wer hat welche Urlaubs-Berechtigung?")
    print("-" * 70)
    
    # 4. Bestimmte User prüfen (aus Vanessas Feedback)
    test_users = [
        'vanessa.groll',
        'christian.aichinger', 
        'sandra.brendel',
        'florian.greiner',
        'peter.greiner',
        'matthias.koenig',
        'anton.suess'
    ]
    
    for username in test_users:
        conn.search(
            search_base=base_dn,
            search_filter=f'(&(objectClass=user)(sAMAccountName={username}))',
            search_scope=SUBTREE,
            attributes=['cn', 'displayName', 'memberOf', 'manager', 'department']
        )
        
        if conn.entries:
            user = conn.entries[0]
            print(f"\n👤 {username}")
            print(f"   Name: {user.displayName}")
            print(f"   Abteilung: {user.department if user.department else '-'}")
            
            # Manager
            if user.manager:
                manager_dn = str(user.manager)
                if 'CN=' in manager_dn:
                    manager_name = manager_dn.split('CN=')[1].split(',')[0]
                    print(f"   Manager: {manager_name}")
            else:
                print(f"   Manager: (keiner)")
            
            # Urlaubs-Gruppen
            urlaub_groups = []
            if user.memberOf:
                for group_dn in user.memberOf:
                    group_cn = str(group_dn).split('CN=')[1].split(',')[0] if 'CN=' in str(group_dn) else str(group_dn)
                    if 'Urlaub' in group_cn or 'GRP_' in group_cn:
                        urlaub_groups.append(group_cn)
            
            if urlaub_groups:
                print(f"   Urlaubs-Gruppen: {', '.join(sorted(urlaub_groups))}")
            else:
                print(f"   Urlaubs-Gruppen: ❌ KEINE!")
        else:
            print(f"\n👤 {username} - ❌ NICHT GEFUNDEN")
    
    print()
    print("=" * 70)
    print("CHECK ABGESCHLOSSEN")
    print("=" * 70)
    
    conn.unbind()

if __name__ == '__main__':
    main()
