#!/usr/bin/env python3
"""Analysiert Locosoft Abwesenheits-Tabellen"""

import psycopg2

conn = psycopg2.connect(
    host='10.80.80.8',
    port=5432,
    database='loco_auswertung_db',
    user='loco_auswertung_benutzer',
    password='loco'
)
cursor = conn.cursor()

print("\n" + "="*70)
print("📊 LOCOSOFT ABWESENHEITS-ANALYSE")
print("="*70)

# 1. ABSENCE_TYPES
print("\n1️⃣ ABSENCE_TYPES")
print("-"*70)
cursor.execute("SELECT * FROM absence_types")
for row in cursor.fetchall():
    print(f"   {row}")

# 2. ABSENCE_REASONS - ALLE
print("\n2️⃣ ABSENCE_REASONS - Alle Gründe")
print("-"*70)
cursor.execute("SELECT id, description, is_annual_vacation FROM absence_reasons ORDER BY id")
for row in cursor.fetchall():
    vacation_flag = "✓ URLAUB" if row[2] else ""
    print(f"   {row[0]:3s} | {row[1]:40s} | {vacation_flag}")

# 3. ABSENCE_CALENDAR Schema
print("\n3️⃣ ABSENCE_CALENDAR - Schema")
print("-"*70)
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'absence_calendar'
    ORDER BY ordinal_position
""")
for row in cursor.fetchall():
    print(f"   • {row[0]} ({row[1]})")

# 4. Sandra Brendel Beispiele 2025
print("\n4️⃣ ABSENCE_CALENDAR - Sandra Brendel (1016) in 2025")
print("-"*70)
cursor.execute("""
    SELECT date, type, day_contingent, reason
    FROM absence_calendar
    WHERE employee_number = 1016
      AND date >= '2025-01-01'
    ORDER BY date
    LIMIT 15
""")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"   {row[0]} | Type: {row[1]} | Tage: {row[2]:.2f} | Grund: {row[3]}")
else:
    print("   (Keine Einträge für 2025)")
    
    # Zeige 2024 Daten
    print("\n   Letzte Einträge (alle Jahre):")
    cursor.execute("""
        SELECT date, type, day_contingent, reason
        FROM absence_calendar
        WHERE employee_number = 1016
        ORDER BY date DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]} | Type: {row[1]} | Tage: {row[2]:.2f} | Grund: {row[3]}")

# 5. Statistik 2024 (als Referenz)
print("\n5️⃣ STATISTIK 2024 - Abwesenheiten")
print("-"*70)
cursor.execute("""
    SELECT 
        ac.reason,
        ar.description,
        ar.is_annual_vacation,
        COUNT(*) as anzahl,
        COUNT(DISTINCT ac.employee_number) as mitarbeiter,
        SUM(ac.day_contingent) as gesamt_tage
    FROM absence_calendar ac
    LEFT JOIN absence_reasons ar ON ac.reason = ar.id
    WHERE ac.date >= '2024-01-01' AND ac.date <= '2024-12-31'
    GROUP BY ac.reason, ar.description, ar.is_annual_vacation
    ORDER BY gesamt_tage DESC
    LIMIT 10
""")
for row in cursor.fetchall():
    vacation = "🏖️" if row[2] else "  "
    print(f"   {vacation} {row[0]:3s} {row[1]:30s} | {row[3]:4d} Einträge | {row[4]:2d} MA | {row[5]:6.1f} Tage")

conn.close()

print("\n" + "="*70)
print("✅ Analyse abgeschlossen")
print("="*70)
