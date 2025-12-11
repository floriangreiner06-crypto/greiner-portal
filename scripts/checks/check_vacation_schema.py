#!/usr/bin/env python3
"""
Quick Check: vacation_approval_rules Schema + Frontend Admin Check
"""

import sqlite3

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 70)
print("1. VACATION_APPROVAL_RULES SCHEMA")
print("=" * 70)

try:
    cursor.execute("PRAGMA table_info(vacation_approval_rules)")
    columns = cursor.fetchall()
    print("\nSpalten:")
    for col in columns:
        print(f"   {col['name']} ({col['type']}) {'NOT NULL' if col['notnull'] else ''}")
    
    print("\nInhalt:")
    cursor.execute("SELECT * FROM vacation_approval_rules")
    rows = cursor.fetchall()
    for row in rows:
        print(f"   {dict(row)}")
except Exception as e:
    print(f"Fehler: {e}")

print()
print("=" * 70)
print("2. WIE PRÜFT vacation_approver_service.py ADMIN-RECHTE?")
print("=" * 70)

# Zeige relevanten Code-Ausschnitt
print("""
Aus vacation_approver_service.py (TAG 107):

    ad_groups = json.loads(row['ad_groups']) if row['ad_groups'] else []
    is_admin = 'GRP_Urlaub_Admin' in ad_groups
    
    if is_admin:
        # Admin sieht ALLE Mitarbeiter
        cursor.execute("SELECT ... FROM employees WHERE aktiv = 1")

Die Logik ist korrekt - aber wird sie im Frontend aufgerufen?
""")

print()
print("=" * 70)
print("3. SESSION-CHECK: Was ist in der Flask-Session?")
print("=" * 70)

print("""
Das Frontend ruft wahrscheinlich /api/vacation/approver-summary auf.
Dieser Endpoint prüft is_approver() und get_approver_summary().

MÖGLICHES PROBLEM:
- Das Frontend zeigt Admin-Buttons nur wenn eine bestimmte Bedingung erfüllt ist
- Diese Bedingung könnte falsch sein (z.B. prüft auf "admin" statt "GRP_Urlaub_Admin")
""")

conn.close()
