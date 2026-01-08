#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Vacation Entitlements
============================
Prüft ob Urlaubsansprüche vorhanden sind und ob die View korrekt funktioniert.

TAG 167: Debug für fehlende Urlaubsansprüche (alle zeigen 0 Tage)
"""

import sys
from pathlib import Path

# Projekt-Root hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.db_utils import db_session

def check_entitlements():
    """Prüft vacation_entitlements Tabelle"""
    print("=" * 70)
    print("🔍 URLAUBSANSPRÜCHE CHECK")
    print("=" * 70)
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # 1. Prüfe ob Tabelle existiert
        print("\n1. Prüfe Tabelle vacation_entitlements...")
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'vacation_entitlements'
        """)
        table_exists = cursor.fetchone()[0] > 0
        print(f"   ✅ Tabelle existiert: {table_exists}")
        
        if not table_exists:
            print("   ❌ FEHLER: Tabelle vacation_entitlements existiert nicht!")
            return
        
        # 2. Anzahl Einträge
        cursor.execute("SELECT COUNT(*) FROM vacation_entitlements")
        total_count = cursor.fetchone()[0]
        print(f"   📊 Gesamt Einträge: {total_count}")
        
        # 3. Einträge pro Jahr
        cursor.execute("""
            SELECT year, COUNT(*) as count, SUM(total_days) as total_days_sum
            FROM vacation_entitlements
            GROUP BY year
            ORDER BY year DESC
        """)
        print("\n2. Einträge pro Jahr:")
        for row in cursor.fetchall():
            print(f"   Jahr {row[0]}: {row[1]} Einträge, {row[2]} Tage gesamt")
        
        # 4. Mitarbeiter ohne Anspruch
        cursor.execute("""
            SELECT 
                e.id,
                e.first_name || ' ' || e.last_name as name,
                e.aktiv
            FROM employees e
            LEFT JOIN vacation_entitlements ve ON e.id = ve.employee_id AND ve.year = 2025
            WHERE e.aktiv = true AND ve.id IS NULL
            ORDER BY e.last_name
            LIMIT 10
        """)
        missing = cursor.fetchall()
        print(f"\n3. Mitarbeiter OHNE Anspruch für 2025: {len(missing)}")
        if missing:
            print("   Erste 10:")
            for row in missing:
                print(f"   - {row[1]} (ID={row[0]})")
        
        # 5. View prüfen
        print("\n4. Prüfe View v_vacation_balance_2025...")
        try:
            cursor.execute("SELECT COUNT(*) FROM v_vacation_balance_2025")
            view_count = cursor.fetchone()[0]
            print(f"   ✅ View existiert: {view_count} Zeilen")
            
            # Mitarbeiter mit 0 Anspruch in View
            cursor.execute("""
                SELECT employee_id, name, anspruch, verbraucht, geplant, resturlaub
                FROM v_vacation_balance_2025
                WHERE anspruch = 0
                LIMIT 10
            """)
            zero_anspruch = cursor.fetchall()
            print(f"\n5. Mitarbeiter mit 0 Anspruch in View: {len(zero_anspruch)}")
            if zero_anspruch:
                print("   Erste 10:")
                for row in zero_anspruch:
                    print(f"   - {row[1]} (ID={row[0]}): Anspruch={row[2]}, Verbraucht={row[3]}, Geplant={row[4]}, Rest={row[5]}")
            
            # Mitarbeiter mit Anspruch > 0
            cursor.execute("""
                SELECT COUNT(*) as count, SUM(anspruch) as total_anspruch
                FROM v_vacation_balance_2025
                WHERE anspruch > 0
            """)
            with_anspruch = cursor.fetchone()
            print(f"\n6. Mitarbeiter MIT Anspruch: {with_anspruch[0]}, Gesamt: {with_anspruch[1]} Tage")
            
        except Exception as e:
            print(f"   ❌ FEHLER beim Zugriff auf View: {e}")
            print(f"   Hinweis: View muss möglicherweise neu erstellt werden (PostgreSQL-Syntax!)")
        
        # 6. View-Definition prüfen
        print("\n7. Prüfe View-Definition...")
        cursor.execute("""
            SELECT definition
            FROM pg_views
            WHERE viewname = 'v_vacation_balance_2025'
        """)
        view_def = cursor.fetchone()
        if view_def:
            definition = view_def[0]
            if 'strftime' in definition:
                print("   ⚠️  WARNUNG: View verwendet SQLite-Syntax (strftime)!")
                print("   → Muss auf PostgreSQL-Syntax (EXTRACT) umgestellt werden")
            elif 'EXTRACT' in definition:
                print("   ✅ View verwendet PostgreSQL-Syntax (EXTRACT)")
            else:
                print("   ⚠️  View-Definition unklar")
        else:
            print("   ❌ View existiert nicht!")
    
    print("\n" + "=" * 70)
    print("✅ CHECK ABGESCHLOSSEN")
    print("=" * 70)

if __name__ == '__main__':
    try:
        check_entitlements()
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

