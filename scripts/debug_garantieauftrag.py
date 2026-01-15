#!/usr/bin/env python3
"""
Debug-Script: Prüft warum ein Garantieauftrag nicht angezeigt wird.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor

def debug_garantieauftrag(order_number):
    """Prüft warum ein Garantieauftrag nicht angezeigt wird."""
    try:
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Zuerst prüfen ob Auftrag überhaupt existiert
            check_query = "SELECT number, has_open_positions, subsidiary, order_date FROM orders WHERE number = %s"
            cursor.execute(check_query, (order_number,))
            basic_info = cursor.fetchone()
            
            if not basic_info:
                print(f"❌ Auftrag {order_number} existiert NICHT in der Datenbank")
                print(f"\n💡 Mögliche Gründe:")
                print(f"   • Auftrag wurde gelöscht")
                print(f"   • Auftrag wurde storniert")
                print(f"   • Falsche Auftragsnummer")
                
                # Suche nach ähnlichen Auftragsnummern
                print(f"\n🔍 Suche nach ähnlichen Auftragsnummern...")
                similar_query = """
                    SELECT number, has_open_positions, subsidiary, order_date 
                    FROM orders 
                    WHERE number::text LIKE %s 
                    ORDER BY number DESC 
                    LIMIT 10
                """
                cursor.execute(similar_query, (f'%{order_number}%',))
                similar = cursor.fetchall()
                
                if similar:
                    print(f"   Gefundene ähnliche Aufträge:")
                    for row in similar:
                        print(f"      • {row['number']} (Subsidiary: {row['subsidiary']}, Datum: {row['order_date']}, Offen: {row['has_open_positions']})")
                else:
                    print(f"   Keine ähnlichen Aufträge gefunden")
                
                return
            
            query = """
                SELECT 
                    o.number,
                    o.has_open_positions,
                    o.subsidiary,
                    o.order_date,
                    -- Prüfe ob Garantie-Auftrag
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM labours l 
                            WHERE l.order_number = o.number 
                              AND (l.charge_type = 60 OR l.labour_type IN ('G', 'GS'))
                        ) THEN true
                        WHEN EXISTS (
                            SELECT 1 FROM invoices i 
                            WHERE i.order_number = o.number 
                              AND i.invoice_type = 6 
                              AND i.is_canceled = false
                        ) THEN true
                        ELSE false
                    END as ist_garantie,
                    -- Prüfe ob Auftrag bereits bearbeitet wird
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM times t 
                            WHERE t.order_number = o.number 
                              AND t.type = 2
                        ) THEN true
                        WHEN EXISTS (
                            SELECT 1 FROM labours l 
                            WHERE l.order_number = o.number 
                              AND l.mechanic_no IS NOT NULL
                        ) THEN true
                        ELSE false
                    END as wird_bearbeitet,
                    -- Details
                    (SELECT COUNT(*) FROM labours l WHERE l.order_number = o.number AND (l.charge_type = 60 OR l.labour_type IN ('G', 'GS'))) as garantie_labours,
                    (SELECT COUNT(*) FROM invoices i WHERE i.order_number = o.number AND i.invoice_type = 6 AND i.is_canceled = false) as garantie_invoices,
                    (SELECT COUNT(*) FROM times t WHERE t.order_number = o.number AND t.type = 2) as stempelzeiten_count,
                    (SELECT COUNT(*) FROM labours l WHERE l.order_number = o.number AND l.mechanic_no IS NOT NULL) as zugeordnete_positionen_count
                FROM orders o
                WHERE o.number = %s
            """
            
            cursor.execute(query, (order_number,))
            auftrag = cursor.fetchone()
            
            if not auftrag:
                print(f"❌ Auftrag {order_number} nicht gefunden")
                return
            
            # Prüfe Filter-Bedingungen
            wird_angezeigt = (
                auftrag['has_open_positions'] and 
                auftrag['ist_garantie'] and 
                auftrag['wird_bearbeitet']
            )
            
            print("=" * 80)
            print(f"DEBUG: Garantieauftrag {order_number}")
            print("=" * 80)
            print(f"\n📋 Auftragsdaten:")
            print(f"   Nummer: {auftrag['number']}")
            print(f"   Subsidiary: {auftrag['subsidiary']}")
            print(f"   Auftragsdatum: {auftrag['order_date']}")
            
            print(f"\n🔍 Filter-Status:")
            print(f"   has_open_positions: {auftrag['has_open_positions']} {'✅' if auftrag['has_open_positions'] else '❌'}")
            print(f"   ist_garantie: {auftrag['ist_garantie']} {'✅' if auftrag['ist_garantie'] else '❌'}")
            print(f"   wird_bearbeitet: {auftrag['wird_bearbeitet']} {'✅' if auftrag['wird_bearbeitet'] else '❌'}")
            
            print(f"\n📊 Details:")
            print(f"   Garantie-Positionen (labours): {auftrag['garantie_labours']}")
            print(f"   Garantie-Rechnungen (invoices): {auftrag['garantie_invoices']}")
            print(f"   Stempelzeiten (times): {auftrag['stempelzeiten_count']}")
            print(f"   Zugeordnete Positionen: {auftrag['zugeordnete_positionen_count']}")
            
            print(f"\n🎯 Ergebnis:")
            if wird_angezeigt:
                print(f"   ✅ Auftrag wird ANGEZEIGT")
            else:
                print(f"   ❌ Auftrag wird NICHT angezeigt")
                print(f"\n   Gründe:")
                if not auftrag['has_open_positions']:
                    print(f"      • Auftrag hat keine offenen Positionen mehr (alle abgeschlossen)")
                if not auftrag['ist_garantie']:
                    print(f"      • Auftrag ist nicht als Garantie erkannt")
                    print(f"        (keine charge_type 60, labour_type G/GS, oder invoice_type 6)")
                if not auftrag['wird_bearbeitet']:
                    print(f"      • Auftrag wird nicht bearbeitet")
                    print(f"        (keine Stempelzeiten und keine zugeordneten Positionen)")
            
            print("=" * 80)
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 debug_garantieauftrag.py <order_number>")
        sys.exit(1)
    
    order_number = int(sys.argv[1])
    debug_garantieauftrag(order_number)
