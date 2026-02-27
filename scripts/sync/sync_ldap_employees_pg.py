#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# LDAP -> ldap_employee_mapping (PostgreSQL). Benötigt ldap3.
# Aufruf: .venv/bin/python scripts/sync/sync_ldap_employees_pg.py  (oder Task Manager: Locosoft Employees)

import sys
import os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')
LDAP_CONFIG_PATH = '/opt/greiner-portal/config/ldap_credentials.env'

def load_ldap_config():
    config = {}
    if not os.path.isfile(LDAP_CONFIG_PATH):
        print("Config nicht gefunden:", LDAP_CONFIG_PATH)
        return None
    with open(LDAP_CONFIG_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                config[key.strip()] = val.strip().strip('"').strip("'")
    return config

def main():
    print("=" * 60)
    print("LDAP -> ldap_employee_mapping (PostgreSQL)")
    print("=" * 60)
    ldap_config = load_ldap_config()
    if not ldap_config:
        return 1
    from api.db_connection import get_db
    conn = get_db()
    cur = conn.cursor()
    from ldap3 import Server, Connection, ALL
    server = Server(ldap_config['LDAP_SERVER'], get_info=ALL)
    ldap_conn = Connection(server, user=ldap_config['LDAP_BIND_DN'], password=ldap_config['LDAP_BIND_PASSWORD'], auto_bind=True)
    print("\nHole AD-User...")
    ldap_conn.search(search_base=ldap_config['LDAP_BASE_DN'], search_filter='(&(objectClass=user)(sAMAccountName=*)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))', attributes=['sAMAccountName', 'displayName', 'mail', 'givenName', 'sn'])
    ldap_users = []
    for entry in ldap_conn.entries:
        username = str(entry.sAMAccountName)
        if username.startswith('Admin-') or username.startswith('sa-') or username.startswith('ext-') or '$' in username:
            continue
        display_name = str(entry.displayName) if entry.displayName else ''
        email = str(entry.mail) if entry.mail else username + "@auto-greiner.de"
        first_name = str(entry.givenName) if entry.givenName else ''
        last_name = str(entry.sn) if entry.sn else ''
        ldap_users.append({'username': username, 'display_name': display_name, 'email': email, 'first_name': first_name, 'last_name': last_name})
    print("  ", len(ldap_users), "AD-User")
    print("\nMatching AD <-> Employees...")
    matched = updated = inserted = 0
    unmatched = []
    for u in ldap_users:
        cur.execute("SELECT id, locosoft_id, first_name, last_name, email FROM employees WHERE LOWER(TRIM(email)) = LOWER(TRIM(%s)) AND aktiv = true", (u['email'],))
        row = cur.fetchone()
        if not row and u['display_name'] and ' ' in u['display_name']:
            parts = u['display_name'].strip().split()
            first, last = ' '.join(parts[:-1]), parts[-1]
            cur.execute("SELECT id, locosoft_id, first_name, last_name, email FROM employees WHERE LOWER(TRIM(first_name)) = LOWER(TRIM(%s)) AND LOWER(TRIM(last_name)) = LOWER(TRIM(%s)) AND aktiv = true", (first, last))
            row = cur.fetchone()
        if not row and u['first_name'] and u['last_name']:
            cur.execute("SELECT id, locosoft_id, first_name, last_name, email FROM employees WHERE LOWER(TRIM(first_name)) = LOWER(TRIM(%s)) AND LOWER(TRIM(last_name)) = LOWER(TRIM(%s)) AND aktiv = true", (u['first_name'], u['last_name']))
            row = cur.fetchone()
        # Fallback: E-Mail-Lokalteil (vor @) = sAMAccountName – gleiche Logik wie sync_ad_departments
        if not row and u['username']:
            cur.execute("""
                SELECT id, locosoft_id, first_name, last_name, email FROM employees
                WHERE email IS NOT NULL AND LOWER(TRIM(SPLIT_PART(email, '@', 1))) = LOWER(TRIM(%s))
                AND aktiv = true
                AND id NOT IN (SELECT employee_id FROM ldap_employee_mapping WHERE ldap_username IS NOT NULL)
            """, (u['username'],))
            row = cur.fetchone()
        if not row:
            unmatched.append(u['username'] + " (" + (u['display_name'] or u['email']) + ")")
            continue
        employee_id, locosoft_id = row[0], row[1] if row[1] is not None else 0
        cur.execute("SELECT id FROM ldap_employee_mapping WHERE employee_id = %s", (employee_id,))
        existing = cur.fetchone()
        if existing:
            cur.execute("UPDATE ldap_employee_mapping SET ldap_username = %s, ldap_email = %s, locosoft_id = %s WHERE employee_id = %s", (u['username'], u['email'] or None, locosoft_id, employee_id))
            updated += 1
            print("  Update:", u['username'], "->", row[2], row[3])
        else:
            cur.execute("INSERT INTO ldap_employee_mapping (ldap_username, ldap_email, employee_id, locosoft_id, verified) VALUES (%s, %s, %s, %s, 1)", (u['username'], u['email'] or None, employee_id, locosoft_id))
            inserted += 1
            print("  Neu:", u['username'], "->", row[2], row[3])
        matched += 1
    conn.commit()
    cur.close()
    conn.close()
    print("\n" + "=" * 60)
    print("Zugeordnet:", matched, "(neu:", inserted, ", aktualisiert:", updated, ")")
    if unmatched:
        print("Ohne Match:", len(unmatched))
        for x in unmatched[:15]:
            print(" ", x)
        if len(unmatched) > 15:
            print("  ... und", len(unmatched) - 15, "weitere")
    print()
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print("Fehler:", e)
        import traceback
        traceback.print_exc()
        sys.exit(1)
