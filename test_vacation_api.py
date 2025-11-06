#!/usr/bin/env python3
"""
Schneller API-Test (ohne Flask-Server)
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.vacation_api import get_db
from vacation_v2.utils.vacation_calculator import VacationCalculator
from datetime import date

print("\n" + "="*70)
print("🧪 VACATION API - QUICK TEST")
print("="*70)

# Test 1: DB-Verbindung
print("\n1️⃣ Test DB-Verbindung...")
try:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM employees WHERE aktiv = 1")
    count = cursor.fetchone()[0]
    print(f"   ✓ DB OK: {count} aktive Mitarbeiter")
    conn.close()
except Exception as e:
    print(f"   ❌ Fehler: {e}")

# Test 2: VacationCalculator
print("\n2️⃣ Test VacationCalculator Import...")
try:
    calc = VacationCalculator()
    balance = calc.get_vacation_balance(1, 2025)
    print(f"   ✓ Calculator OK")
    print(f"      Beispiel Balance: {balance}")
except Exception as e:
    print(f"   ❌ Fehler: {e}")

# Test 3: View abfragen
print("\n3️⃣ Test v_vacation_balance_2025...")
try:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, anspruch FROM v_vacation_balance_2025 LIMIT 3")
    rows = cursor.fetchall()
    print(f"   ✓ View OK: {len(rows)} Zeilen")
    for row in rows:
        print(f"      • {row['name']}: {row['anspruch']} Tage")
    conn.close()
except Exception as e:
    print(f"   ❌ Fehler: {e}")

# Test 4: API-Funktion simulieren
print("\n4️⃣ Test API Balance-Funktion...")
try:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT employee_id, name, anspruch, resturlaub
        FROM v_vacation_balance_2025
        WHERE employee_id = 1
    """)
    row = cursor.fetchone()
    if row:
        print(f"   ✓ API-Query OK")
        print(f"      Employee: {row['name']}")
        print(f"      Anspruch: {row['anspruch']} Tage")
        print(f"      Resturlaub: {row['resturlaub']} Tage")
    conn.close()
except Exception as e:
    print(f"   ❌ Fehler: {e}")

print("\n" + "="*70)
print("✅ QUICK TEST ABGESCHLOSSEN")
print("="*70)
print("\n💡 Für Live-Test:")
print("   python3 app.py")
print("   curl http://localhost:5000/api/vacation/health")
print()
