#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check: users-Tabelle vs. AD-Gruppen
===================================
Vergleicht was in der Portal-DB steht mit dem was im AD ist.
"""

import sqlite3
import json

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

def main():
    print("=" * 70)
    print("PORTAL DB vs. AD-GRUPPEN CHECK")
    print("=" * 70)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Alle Users mit ad_groups
    print("-" * 70)
    print("1. USERS-TABELLE: Urlaubs-Gruppen")
    print("-" * 70)
    
    cursor.execute("""
        SELECT username, display_name, ad_groups, last_ad_sync, is_active
        FROM users
        ORDER BY display_name
    """)
    
    users_with_urlaub = []
    users_without_urlaub = []
    
    for row in cursor.fetchall():
        username = row['username']
        display_name = row['display_name']
        ad_groups_raw = row['ad_groups']
        last_sync = row['last_ad_sync']
        is_active = row['is_active']
        
        ad_groups = json.loads(ad_groups_raw) if ad_groups_raw else []
        urlaub_groups = [g for g in ad_groups if 'Urlaub' in g]
        
        if urlaub_groups:
            users_with_urlaub.append({
                'username': username,
                'name': display_name,
                'groups': urlaub_groups,
                'last_sync': last_sync,
                'active': is_active
            })
        else:
            users_without_urlaub.append({
                'username': username,
                'name': display_name,
                'last_sync': last_sync
            })
    
    print(f"\n✅ Users MIT Urlaubs-Gruppen ({len(users_with_urlaub)}):")
    for u in users_with_urlaub:
        groups_str = ', '.join(u['groups'])
        active_str = "✅" if u['active'] else "❌"
        print(f"   {active_str} {u['name']}")
        print(f"      Username: {u['username']}")
        print(f"      Gruppen: {groups_str}")
        print(f"      Letzter Sync: {u['last_sync']}")
        print()
    
    print(f"\n❌ Users OHNE Urlaubs-Gruppen ({len(users_without_urlaub)}):")
    for u in users_without_urlaub[:10]:  # Nur erste 10
        print(f"   - {u['name']} ({u['username']})")
    if len(users_without_urlaub) > 10:
        print(f"   ... und {len(users_without_urlaub) - 10} weitere")
    
    # 2. Spezifische User prüfen
    print()
    print("-" * 70)
    print("2. SPEZIFISCHE USER-PRÜFUNG")
    print("-" * 70)
    
    test_users = [
        'vanessa.groll@auto-greiner.de',
        'christian.aichinger@auto-greiner.de',
        'sandra.brendel@auto-greiner.de',
        'florian.greiner@auto-greiner.de'
    ]
    
    for username in test_users:
        cursor.execute("""
            SELECT u.*, lem.employee_id, lem.locosoft_id
            FROM users u
            LEFT JOIN ldap_employee_mapping lem ON lem.ldap_username = REPLACE(u.username, '@auto-greiner.de', '')
            WHERE u.username = ? OR u.username = ?
        """, (username, username.replace('@auto-greiner.de', '')))
        
        row = cursor.fetchone()
        if row:
            ad_groups = json.loads(row['ad_groups']) if row['ad_groups'] else []
            urlaub_groups = [g for g in ad_groups if 'Urlaub' in g]
            
            print(f"\n👤 {row['display_name']}")
            print(f"   Username: {row['username']}")
            print(f"   Employee-ID: {row['employee_id']}")
            print(f"   Locosoft-ID: {row['locosoft_id']}")
            print(f"   Aktiv: {'✅' if row['is_active'] else '❌'}")
            print(f"   Letzter AD-Sync: {row['last_ad_sync']}")
            print(f"   Urlaubs-Gruppen: {urlaub_groups if urlaub_groups else '❌ KEINE!'}")
            
            # Ist Admin?
            is_admin = 'GRP_Urlaub_Admin' in ad_groups
            print(f"   IST ADMIN: {'✅ JA' if is_admin else '❌ NEIN'}")
        else:
            print(f"\n👤 {username} - ❌ NICHT IN DB!")
    
    # 3. vacation_approval_rules prüfen (falls vorhanden)
    print()
    print("-" * 70)
    print("3. VACATION_APPROVAL_RULES (falls vorhanden)")
    print("-" * 70)
    
    try:
        cursor.execute("SELECT * FROM vacation_approval_rules ORDER BY department_filter, priority")
        rules = cursor.fetchall()
        
        if rules:
            print(f"\n{len(rules)} Regeln gefunden:")
            for r in rules:
                active_str = "✅" if r['active'] else "❌"
                print(f"   {active_str} {r['approver_name']} für {r['department_filter'] or 'ALLE'}")
                print(f"      LDAP: {r['approver_ldap_username']}, Prio: {r['priority']}")
        else:
            print("   Keine Regeln gefunden (Tabelle leer)")
    except Exception as e:
        print(f"   Tabelle existiert nicht oder Fehler: {e}")
    
    # 4. Rollen-Tabelle prüfen
    print()
    print("-" * 70)
    print("4. ROLES & USER_ROLES")
    print("-" * 70)
    
    try:
        cursor.execute("""
            SELECT r.name, r.display_name, COUNT(ur.user_id) as user_count
            FROM roles r
            LEFT JOIN user_roles ur ON r.id = ur.role_id
            GROUP BY r.id
            ORDER BY r.name
        """)
        
        for row in cursor.fetchall():
            print(f"   {row['name']}: {row['user_count']} User")
    except Exception as e:
        print(f"   Fehler: {e}")
    
    conn.close()
    
    print()
    print("=" * 70)
    print("CHECK ABGESCHLOSSEN")
    print("=" * 70)

if __name__ == '__main__':
    main()
