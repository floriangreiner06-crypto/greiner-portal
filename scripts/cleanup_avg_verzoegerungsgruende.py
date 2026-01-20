#!/usr/bin/env python3
"""
Cleanup: AVG-Verzögerungsgründe bereinigen
===========================================
Entfernt AVG-Gründe von Aufträgen, die:
- Bereits abgerechnet sind
- Termine bereits vorbei sind (optional)

TAG 200
WICHTIG: Dieses Script ändert Daten in Locosoft! Nur ausführen wenn sicher!
"""

import os
import sys
from datetime import datetime, date

sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor

print("=" * 80)
print("AVG-VERZÖGERUNGSGRÜNDE BEREINIGEN")
print("=" * 80)
print(f"Zeitpunkt: {datetime.now()}")
print()
print("⚠️  WICHTIG: Dieses Script ändert Daten in Locosoft!")
print("⚠️  Es entfernt AVG-Gründe von abgerechneten Aufträgen.")
print()

# Sicherheitsabfrage
antwort = input("Möchten Sie fortfahren? (ja/nein): ")
if antwort.lower() != 'ja':
    print("Abgebrochen.")
    sys.exit(0)

heute = date.today()

with locosoft_session() as conn:
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # =============================================================================
    # 1. HOLE ABGERECHNETE AUFTRÄGE MIT AVG-GRÜNDEN
    # =============================================================================
    
    print("=" * 80)
    print("1. ABGERECHNETE AUFTRÄGE MIT AVG-GRÜNDEN FINDEN")
    print("=" * 80)
    print()
    
    query = """
        SELECT DISTINCT
            o.number as auftrag_nr,
            o.clearing_delay_type as avg_code,
            cdt.description as avg_text,
            i.invoice_number,
            i.invoice_date,
            o.subsidiary as betrieb
        FROM orders o
        LEFT JOIN clearing_delay_types cdt ON o.clearing_delay_type = cdt.type
        JOIN invoices i ON o.number = i.order_number
        WHERE o.has_open_positions = true
          AND o.clearing_delay_type IS NOT NULL
          AND o.clearing_delay_type != ''
          AND i.is_canceled = false
    """
    
    cur.execute(query)
    abgerechnet_mit_avg = cur.fetchall()
    
    print(f"✅ {len(abgerechnet_mit_avg)} abgerechnete Aufträge mit AVG-Gründen gefunden")
    print()
    
    if len(abgerechnet_mit_avg) == 0:
        print("Keine Aufträge zum Bereinigen gefunden.")
        sys.exit(0)
    
    # Gruppiere nach AVG-Code
    nach_code = {}
    for a in abgerechnet_mit_avg:
        code = a['avg_code']
        if code not in nach_code:
            nach_code[code] = []
        nach_code[code].append(a)
    
    print("📊 Aufteilung nach AVG-Code:")
    for code in sorted(nach_code.keys()):
        print(f"   {code}: {len(nach_code[code])} Aufträge")
    print()
    
    # =============================================================================
    # 2. BEREINIGUNG DURCHFÜHREN
    # =============================================================================
    
    print("=" * 80)
    print("2. AVG-GRÜNDE ENTFERNEN")
    print("=" * 80)
    print()
    
    update_query = """
        UPDATE orders
        SET clearing_delay_type = NULL
        WHERE number = %s
          AND has_open_positions = true
          AND clearing_delay_type IS NOT NULL
    """
    
    aktualisiert = 0
    fehler = 0
    
    for a in abgerechnet_mit_avg:
        try:
            cur.execute(update_query, (a['auftrag_nr'],))
            aktualisiert += 1
            if aktualisiert % 10 == 0:
                print(f"   ✅ {aktualisiert} Aufträge aktualisiert...")
        except Exception as e:
            fehler += 1
            print(f"   ❌ Fehler bei Auftrag #{a['auftrag_nr']}: {e}")
    
    # Commit
    conn.commit()
    
    print()
    print(f"✅ {aktualisiert} Aufträge erfolgreich aktualisiert")
    if fehler > 0:
        print(f"❌ {fehler} Fehler aufgetreten")
    print()
    
    # =============================================================================
    # 3. ZUSAMMENFASSUNG
    # =============================================================================
    
    print("=" * 80)
    print("3. ZUSAMMENFASSUNG")
    print("=" * 80)
    print()
    
    print(f"📊 Bereinigt:")
    for code in sorted(nach_code.keys()):
        text = nach_code[code][0]['avg_text'] or 'Unbekannt'
        anzahl = len(nach_code[code])
        print(f"   {code} - {text}: {anzahl} Aufträge")
    print()
    
    print("✅ Cleanup abgeschlossen!")
    print("=" * 80)
