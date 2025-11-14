#!/usr/bin/env python3
"""
============================================================================
URLAUBSBUCHUNGEN LÖSCHEN
============================================================================
Erstellt: 06.11.2025
Zweck: Löscht alte Urlaubsbuchungen vom Prototyp
Grund: Frischer Start mit Locosoft-Mitarbeitern
============================================================================
"""

import sqlite3
import sys

DB_PATH = "data/greiner_controlling.db"

def delete_vacation_bookings(confirm=False):
    """Löscht alle Urlaubsbuchungen"""
    
    print("="*80)
    print("URLAUBSBUCHUNGEN LÖSCHEN")
    print("="*80)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Anzahl prüfen
        cursor.execute("SELECT COUNT(*) as count FROM vacation_bookings")
        count = cursor.fetchone()['count']
        
        print(f"📊 Aktuelle Buchungen: {count}")
        print()
        
        if count == 0:
            print("ℹ️  Keine Buchungen vorhanden - nichts zu löschen")
            return True
        
        # Statistik zeigen
        print("📋 Verteilung:")
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM vacation_bookings 
            GROUP BY status
        """)
        for row in cursor.fetchall():
            print(f"  • {row['status']:15} {row['count']:5} Buchungen")
        
        print()
        print("-"*80)
        
        if not confirm:
            print()
            print("⚠️  WARNUNG: Dies löscht ALLE Urlaubsbuchungen!")
            print()
            print("   Betroffene Buchungen: " + str(count))
            print()
            print("🔒 SICHERHEITS-MODUS aktiv")
            print("   → Führe erneut aus mit: python3 delete_bookings.py --confirm")
            print()
            return False
        
        # LÖSCHEN
        print("🗑️  Lösche alle Urlaubsbuchungen...")
        cursor.execute("DELETE FROM vacation_bookings")
        deleted = cursor.rowcount
        
        conn.commit()
        
        print(f"✅ {deleted} Buchungen gelöscht")
        
        # Verifizieren
        cursor.execute("SELECT COUNT(*) as count FROM vacation_bookings")
        remaining = cursor.fetchone()['count']
        
        print()
        print("="*80)
        print("✅ LÖSCHEN ABGESCHLOSSEN")
        print("="*80)
        print()
        print(f"  Gelöscht:    {deleted}")
        print(f"  Verbleibend: {remaining}")
        print()
        
        if remaining == 0:
            print("✅ Alle Urlaubsbuchungen erfolgreich gelöscht!")
            print()
            print("NÄCHSTE SCHRITTE:")
            print("  → Urlaubsplaner-Funktionen übernehmen")
            print("  → VacationCalculator implementieren")
            print("  → Feiertage prüfen")
            print("  → REST-API entwickeln")
        else:
            print("⚠️  Warnung: Es sind noch Buchungen vorhanden!")
        
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
    # Prüfe ob --confirm übergeben wurde
    confirm = len(sys.argv) > 1 and sys.argv[1] == '--confirm'
    
    try:
        success = delete_vacation_bookings(confirm=confirm)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Kritischer Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
