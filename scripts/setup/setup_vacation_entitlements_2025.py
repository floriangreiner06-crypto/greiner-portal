#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vacation Entitlements 2025 Setup
=================================
Erstellt Urlaubsansprüche für alle aktiven Mitarbeiter
"""

import sqlite3
from datetime import datetime

print("\n" + "="*70)
print("📅 VACATION ENTITLEMENTS 2025 SETUP")
print("="*70)

db_path = 'data/greiner_controlling.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Prüfe aktuelle Entitlements
cursor.execute("SELECT COUNT(*) FROM vacation_entitlements WHERE year = 2025")
existing = cursor.fetchone()[0]

print(f"\n📊 Status:")
print(f"   Aktuelle Entitlements 2025: {existing}")

if existing > 0:
    response = input(f"\n⚠️  {existing} Einträge existieren bereits. Löschen und neu erstellen? (j/n): ")
    if response.lower() != 'j':
        print("   → Abbruch")
        conn.close()
        exit(0)
    
    cursor.execute("DELETE FROM vacation_entitlements WHERE year = 2025")
    print(f"   ✓ {existing} alte Einträge gelöscht")

# 2. Hole alle aktiven Mitarbeiter
cursor.execute("""
    SELECT id, first_name, last_name, entry_date, vacation_days_total
    FROM employees
    WHERE aktiv = 1
    ORDER BY last_name, first_name
""")

employees = cursor.fetchall()
print(f"\n👥 Mitarbeiter gefunden: {len(employees)}")

# 3. Erstelle Entitlements
print("\n📝 Erstelle Urlaubsansprüche...")

created = 0
anteilig_count = 0

for emp in employees:
    emp_id, first_name, last_name, entry_date, vacation_days = emp
    
    # Standard: 30 Tage (oder aus vacation_days_total falls gesetzt)
    days = vacation_days if vacation_days and vacation_days > 0 else 30.0
    
    # Anteilige Berechnung falls Eintritt im Jahr 2025
    if entry_date and entry_date.startswith('2025'):
        entry_month = int(entry_date.split('-')[1])
        # Anteilige Tage: (13 - Eintrittsmonat) / 12 * Jahresanspruch
        days = round((13 - entry_month) / 12 * days, 1)
        print(f"   • {first_name} {last_name}: {days} Tage (anteilig ab {entry_date})")
        anteilig_count += 1
    
    cursor.execute("""
        INSERT INTO vacation_entitlements 
        (employee_id, year, total_days, carried_over, added_manually)
        VALUES (?, 2025, ?, 0.0, 0.0)
    """, (emp_id, days))
    
    created += 1

conn.commit()

# 4. Zusammenfassung
print(f"\n✅ {created} Urlaubsansprüche erstellt")
print(f"   Davon {anteilig_count} anteilig berechnet")

# 5. Statistik
cursor.execute("""
    SELECT 
        COUNT(*) as anzahl,
        SUM(total_days) as gesamt,
        AVG(total_days) as durchschnitt,
        MIN(total_days) as minimum,
        MAX(total_days) as maximum
    FROM vacation_entitlements
    WHERE year = 2025
""")

stats = cursor.fetchone()
print(f"\n📊 Statistik 2025:")
print(f"   Mitarbeiter:  {stats[0]}")
print(f"   Gesamt Tage:  {stats[1]:.1f}")
print(f"   Durchschnitt: {stats[2]:.1f}")
print(f"   Min/Max:      {stats[3]:.1f} / {stats[4]:.1f}")

# 6. Beispiele
print("\n📋 Beispiele:")
cursor.execute("""
    SELECT 
        e.first_name || ' ' || e.last_name as name,
        e.department_name,
        ve.total_days
    FROM vacation_entitlements ve
    JOIN employees e ON ve.employee_id = e.id
    WHERE ve.year = 2025
    ORDER BY e.last_name
    LIMIT 10
""")

for row in cursor.fetchall():
    dept = row[1] if row[1] else "Keine Abteilung"
    print(f"   • {row[0]:30s} ({dept:20s}): {row[2]:5.1f} Tage")

# 7. View testen
print("\n🔍 Test v_vacation_balance_2025:")
cursor.execute("""
    SELECT name, anspruch, resturlaub
    FROM v_vacation_balance_2025
    ORDER BY name
    LIMIT 5
""")

for row in cursor.fetchall():
    print(f"   • {row[0]:30s}: {row[1]:5.1f} Tage (Rest: {row[2]:5.1f})")

conn.close()

print("\n" + "="*70)
print("✅ SETUP ABGESCHLOSSEN")
print("="*70)
print("\n💡 Nächste Schritte:")
print("   1. Sonderfälle manuell anpassen")
print("   2. Optional: 2024 Resturlaub aus Locosoft importieren")
print("   3. Git Commit + Session Wrap-Up")
print()
