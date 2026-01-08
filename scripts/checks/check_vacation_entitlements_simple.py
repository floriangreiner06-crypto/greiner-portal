#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Einfache Version - Prüft Urlaubsansprüche direkt
"""

import sys
import os
from pathlib import Path

# Projekt-Root hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# DB-Verbindung direkt testen
try:
    from api.db_connection import get_db, get_db_type
    
    print("=" * 70)
    print("🔍 URLAUBSANSPRÜCHE CHECK (Einfach)")
    print("=" * 70)
    print(f"\nDB-Typ: {get_db_type()}")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Prüfe vacation_entitlements
    print("\n1. Prüfe vacation_entitlements...")
    cursor.execute("SELECT COUNT(*) FROM vacation_entitlements")
    count = cursor.fetchone()[0]
    print(f"   Einträge: {count}")
    
    if count > 0:
        cursor.execute("SELECT year, COUNT(*) as cnt, SUM(total_days) as total FROM vacation_entitlements GROUP BY year ORDER BY year DESC")
        print("\n   Pro Jahr:")
        for row in cursor.fetchall():
            print(f"   - {row[0]}: {row[1]} Einträge, {row[2]} Tage")
    
    # 2. Prüfe View
    print("\n2. Prüfe View v_vacation_balance_2025...")
    try:
        cursor.execute("SELECT COUNT(*) FROM v_vacation_balance_2025")
        view_count = cursor.fetchone()[0]
        print(f"   View-Zeilen: {view_count}")
        
        cursor.execute("SELECT COUNT(*) FROM v_vacation_balance_2025 WHERE anspruch > 0")
        with_anspruch = cursor.fetchone()[0]
        print(f"   Mit Anspruch > 0: {with_anspruch}")
        
        cursor.execute("SELECT COUNT(*) FROM v_vacation_balance_2025 WHERE anspruch = 0")
        zero_anspruch = cursor.fetchone()[0]
        print(f"   Mit Anspruch = 0: {zero_anspruch}")
        
        # View-Definition prüfen
        if get_db_type() == 'postgresql':
            cursor.execute("SELECT definition FROM pg_views WHERE viewname = 'v_vacation_balance_2025'")
            view_def = cursor.fetchone()
            if view_def:
                definition = view_def[0] if isinstance(view_def, (list, tuple)) else view_def
                if 'strftime' in str(definition):
                    print("\n   ⚠️  WARNUNG: View verwendet SQLite-Syntax!")
                    print("   → Führe fix_vacation_balance_view_postgresql.sql aus")
                elif 'EXTRACT' in str(definition):
                    print("\n   ✅ View verwendet PostgreSQL-Syntax")
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        print("   → View muss neu erstellt werden")
    
    conn.close()
    print("\n✅ CHECK ABGESCHLOSSEN")
    
except Exception as e:
    print(f"❌ FEHLER: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

