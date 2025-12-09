#!/usr/bin/env python3
"""
Schema-Update: Fügt fehlende Spalten zur employees-Tabelle hinzu
"""

import sqlite3
import sys

DB_PATH = "data/greiner_controlling.db"

def check_column_exists(cursor, table, column):
    """Prüft ob Spalte existiert"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

def add_missing_columns():
    """Fügt fehlende Spalten hinzu"""
    
    print("="*80)
    print("SCHEMA-UPDATE: Fehlende Spalten hinzufügen")
    print("="*80)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Prüfen welche Spalten fehlen
        columns_to_add = {
            'locosoft_id': 'INTEGER',
            'aktiv': 'BOOLEAN DEFAULT 1',
            'personal_nr': 'TEXT'
        }
        
        changes = 0
        
        for col_name, col_def in columns_to_add.items():
            if check_column_exists(cursor, 'employees', col_name):
                print(f"✅ Spalte '{col_name}' existiert bereits")
            else:
                print(f"➕ Füge Spalte '{col_name}' hinzu...")
                cursor.execute(f"ALTER TABLE employees ADD COLUMN {col_name} {col_def}")
                print(f"✅ Spalte '{col_name}' hinzugefügt")
                changes += 1
        
        if changes > 0:
            conn.commit()
            print()
            print(f"✅ {changes} Spalte(n) erfolgreich hinzugefügt!")
        else:
            print()
            print("ℹ️  Keine Änderungen nötig - alle Spalten vorhanden")
        
        print()
        print("="*80)
        print("SCHEMA-UPDATE ABGESCHLOSSEN")
        print("="*80)
        print()
        print("NÄCHSTER SCHRITT:")
        print("  → python3 sync_employees.py --real")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    success = add_missing_columns()
    sys.exit(0 if success else 1)
