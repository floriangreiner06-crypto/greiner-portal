#!/usr/bin/env python3
"""Final Fix: days_total -> total_days"""

import sqlite3

db_path = 'data/greiner_controlling.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔧 Ersetze 'days_total' durch 'total_days' in Views...")

views_to_fix = [
    'v_vacation_balance_2025',
    'v_employee_vacation_summary',
]

for view in views_to_fix:
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='view' AND name=?", (view,))
    result = cursor.fetchone()
    if result:
        view_sql = result[0]
        # Ersetze days_total durch total_days
        new_sql = view_sql.replace('days_total', 'total_days')
        
        # View neu erstellen
        cursor.execute(f"DROP VIEW IF EXISTS {view}")
        cursor.execute(new_sql)
        print(f"   ✓ {view}")

conn.commit()

# Finale Tests
print("\n🔍 Teste alle Views...")

test_queries = [
    ("v_vacation_balance_2025", "SELECT COUNT(*) FROM v_vacation_balance_2025"),
    ("v_pending_approvals", "SELECT COUNT(*) FROM v_pending_approvals"),
    ("v_team_calendar", "SELECT COUNT(*) FROM v_team_calendar"),
    ("v_employee_vacation_summary", "SELECT COUNT(*) FROM v_employee_vacation_summary"),
    ("v_department_capacity", "SELECT COUNT(DISTINCT department_name) FROM v_department_capacity"),
]

all_ok = True
for view_name, query in test_queries:
    try:
        cursor.execute(query)
        result = cursor.fetchone()[0]
        print(f"   ✓ {view_name}: {result}")
    except Exception as e:
        print(f"   ❌ {view_name}: {e}")
        all_ok = False

conn.close()

if all_ok:
    print("\n✅ Alle Views funktionieren!")
else:
    print("\n⚠️  Einige Views haben noch Probleme")
