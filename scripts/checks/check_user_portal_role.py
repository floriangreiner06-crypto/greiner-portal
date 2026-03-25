#!/usr/bin/env python3
"""
Diagnose: Warum greift die Portal-Rolle bei einem User nicht?
- Zeigt users.title (LDAP-Cache), user_roles, abgeleitete portal_role
- Hilft bei Fällen wie "Silvia Eiglmaier: Rolle auf Verkauf geändert, sieht aber noch alles"

Usage:
  python scripts/checks/check_user_portal_role.py
  python scripts/checks/check_user_portal_role.py "Eiglmaier"
"""
import os
import sys

# Projekt-Root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from api.db_connection import get_db
from config.roles_config import get_role_from_title, get_allowed_features, TITLE_TO_ROLE

def main():
    search = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    conn = get_db()
    cursor = conn.cursor()

    # Alle User mit Rollen
    cursor.execute('''
        SELECT u.id, u.username, u.display_name, u.ou, u.title, u.last_login,
               STRING_AGG(r.name, ', ' ORDER BY r.name) AS roles
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        GROUP BY u.id, u.username, u.display_name, u.ou, u.title, u.last_login
        ORDER BY u.display_name
    ''')
    rows = cursor.fetchall()

    if search:
        rows = [r for r in rows if search.lower() in (r.get('display_name') or '').lower() or search.lower() in (r.get('username') or '').lower()]
        if not rows:
            print(f"Kein User gefunden für '{search}'")
            conn.close()
            return

    print("=" * 70)
    print("Portal-Rollen-Diagnose (Title → portal_role; user_roles nur admin wirkt)")
    print("=" * 70)

    for row in rows:
        uid = row['id']
        username = row['username']
        display_name = row['display_name'] or username
        ou = row['ou'] or '-'
        title = row['title'] or '-'
        roles_db = (row['roles'] or '-').strip()
        last_login = row['last_login'] or '-'

        portal_role = get_role_from_title(title)
        is_admin_override = 'admin' in (roles_db or '').split(', ')
        if is_admin_override:
            effective_role = 'admin (Override aus user_roles)'
            allowed = 'alle'
        else:
            effective_role = portal_role
            allowed = get_allowed_features(portal_role)

        print(f"\nUser: {display_name} (ID {uid})")
        print(f"  username:     {username}")
        print(f"  ou (AD):      {ou}")
        print(f"  title (AD→DB): {title}")
        print(f"  user_roles:   {roles_db}")
        print(f"  → portal_role: {effective_role}")
        if not is_admin_override:
            print(f"  → Features:    {len(allowed)} (z.B. {', '.join(sorted(allowed)[:8])}...)")
        else:
            print(f"  → Features:    alle (Admin-Override)")
        print(f"  last_login:   {last_login}")

        if title and title not in TITLE_TO_ROLE and title != '-':
            print(f"  ⚠️  Title '{title}' steht nicht in TITLE_TO_ROLE → DEFAULT_ROLE 'mitarbeiter'")

    conn.close()
    print("\n" + "=" * 70)
    print("Option B: portal_role nur aus Portal – admin (user_roles) oder portal_role_override oder Default mitarbeiter.")
    print("LDAP Title/OU werden für Zugriff nicht mehr verwendet (nur Anzeige).")
    print("=" * 70)

if __name__ == '__main__':
    main()
