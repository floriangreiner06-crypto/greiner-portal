#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüft Urlaubsdaten in Locosoft
"""

import psycopg2

print("\n" + "="*70)
print("🔍 LOCOSOFT URLAUBSDATEN-CHECK")
print("="*70)

try:
    conn = psycopg2.connect(
        host='10.80.80.8',
        port=5432,
        database='loco_auswertung_db',
        user='loco_auswertung_benutzer',
        password='loco'
    )
    cursor = conn.cursor()
    print("✓ Verbindung zu Locosoft hergestellt")
    
    # 1. Alle Spalten in employees_history anzeigen
    print("\n📋 Alle Spalten in employees_history:")
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'employees_history'
        ORDER BY ordinal_position
    """)
    all_cols = cursor.fetchall()
    for col in all_cols:
        print(f"   • {col[0]} ({col[1]})")
    
    # 2. Prüfe auf Urlaubs-/Resturlaub-Felder
    print("\n🔍 Potenzielle Urlaubsfelder (mit 'rest', 'urlaub', 'days'):")
    interesting = [c for c in all_cols if any(keyword in c[0].lower() 
                   for keyword in ['rest', 'urlaub', 'days', 'vacation', 'leave', 'holiday', 'time_off'])]
    
    if interesting:
        for col in interesting:
            print(f"   • {col[0]} ({col[1]})")
    else:
        print("   ⚠️  Keine offensichtlichen Urlaubsfelder gefunden")
    
    # 3. Beispiel-Daten (erste 3 Mitarbeiter)
    print("\n📝 Beispiel-Daten (erste 3 aktive Mitarbeiter):")
    cursor.execute("""
        SELECT employee_number, name, subsidiary, group_profile
        FROM employees_history
        WHERE employee_number >= 1000
          AND leave_date IS NULL
        ORDER BY employee_number
        LIMIT 3
    """)
    
    rows = cursor.fetchall()
    for row in rows:
        print(f"   • {row[0]}: {row[1]} (Standort: {row[2]}, Gruppe: {row[3]})")
    
    conn.close()
    print("\n✅ Check abgeschlossen")
    
except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
