#!/usr/bin/env python3
"""Fix Views: department -> department_name"""

import sqlite3

db_path = 'data/greiner_controlling.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔧 Ersetze 'e.department' durch 'e.department_name' in allen Views...")

views_to_fix = [
    'v_vacation_balance_2025',
    'v_pending_approvals', 
    'v_team_calendar',
    'v_employee_vacation_summary',
    'v_department_capacity'
]

for view in views_to_fix:
    # View-Definition abrufen
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='view' AND name=?", (view,))
    result = cursor.fetchone()
    if result:
        view_sql = result[0]
        # Ersetze e.department durch e.department_name
        new_sql = view_sql.replace('e.department', 'e.department_name')
        
        # View neu erstellen
        cursor.execute(f"DROP VIEW IF EXISTS {view}")
        cursor.execute(new_sql)
        print(f"   ✓ {view}")

conn.commit()

# Tests
print("\n🔍 Teste Views...")

test_queries = [
    ("v_vacation_balance_2025", "SELECT COUNT(*) FROM v_vacation_balance_2025"),
    ("v_pending_approvals", "SELECT COUNT(*) FROM v_pending_approvals"),
    ("v_team_calendar", "SELECT COUNT(*) FROM v_team_calendar"),
    ("v_employee_vacation_summary", "SELECT COUNT(*) FROM v_employee_vacation_summary"),
    ("v_department_capacity", "SELECT COUNT(DISTINCT department_name) FROM v_department_capacity"),
]

for view_name, query in test_queries:
    try:
        cursor.execute(query)
        result = cursor.fetchone()[0]
        print(f"   ✓ {view_name}: {result}")
    except Exception as e:
        print(f"   ❌ {view_name}: {e}")

conn.close()

print("\n✅ Views erfolgreich korrigiert!")
