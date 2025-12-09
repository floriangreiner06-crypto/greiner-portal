#!/usr/bin/env python3
"""
Sync: Gleicht teile_lieferscheine mit Locosoft PostgreSQL ab
Aktualisiert: locosoft_gefunden, locosoft_zugebucht
"""

import json
import sqlite3
import psycopg2
from datetime import datetime, timedelta

SQLITE_DB = "/opt/greiner-portal/data/greiner_controlling.db"
CREDENTIALS = "/opt/greiner-portal/config/credentials.json"

def get_locosoft_connection():
    with open(CREDENTIALS) as f:
        creds = json.load(f)['databases']['locosoft']
    return psycopg2.connect(
        host=creds['host'],
        port=creds['port'],
        database=creds['database'],
        user=creds['user'],
        password=creds['password']
    )

def sync_with_locosoft():
    print("=" * 80)
    print("LOCOSOFT SYNC - Teile-Lieferscheine")
    print(f"Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # SQLite: Alle Positionen der letzten 14 Tage holen
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cur = sqlite_conn.cursor()
    
    cutoff_date = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
    
    sqlite_cur.execute("""
        SELECT id, teilenummer, lieferdatum, lieferschein_nr, lieferanten_note
        FROM teile_lieferscheine
        WHERE lieferdatum >= ?
    """, (cutoff_date,))
    
    positionen = sqlite_cur.fetchall()
    print(f"\n📦 {len(positionen)} Positionen zu prüfen (seit {cutoff_date})")
    
    # Locosoft-Verbindung
    pg_conn = get_locosoft_connection()
    pg_cur = pg_conn.cursor()
    
    # Alle relevanten Locosoft-Einträge holen
    pg_cur.execute("""
        SELECT part_number, delivery_note_date, number_main, deliverers_note, is_veryfied
        FROM parts_inbound_delivery_notes
        WHERE delivery_note_date >= %s
    """, (cutoff_date,))
    
    # Index aufbauen: (teilenummer, datum) -> (gefunden, zugebucht)
    locosoft_index = {}
    for row in pg_cur.fetchall():
        key = (row[0], row[1].strftime('%Y-%m-%d') if row[1] else None)
        # Wenn bereits gefunden und zugebucht, behalten
        if key in locosoft_index:
            existing = locosoft_index[key]
            locosoft_index[key] = (True, existing[1] or row[4])
        else:
            locosoft_index[key] = (True, row[4])
    
    print(f"📊 {len(locosoft_index)} Einträge in Locosoft-Index")
    
    # SQLite aktualisieren
    updated_gefunden = 0
    updated_zugebucht = 0
    
    for pos_id, teilenummer, lieferdatum, ls_nr, lief_note in positionen:
        key = (teilenummer, lieferdatum)
        
        if key in locosoft_index:
            gefunden, zugebucht = locosoft_index[key]
            
            sqlite_cur.execute("""
                UPDATE teile_lieferscheine
                SET locosoft_gefunden = 1,
                    locosoft_zugebucht = ?,
                    locosoft_sync_datum = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (1 if zugebucht else 0, pos_id))
            
            updated_gefunden += 1
            if zugebucht:
                updated_zugebucht += 1
    
    sqlite_conn.commit()
    
    print(f"\n✅ SYNC ERGEBNIS:")
    print(f"   In Locosoft gefunden:  {updated_gefunden}")
    print(f"   Davon zugebucht:       {updated_zugebucht}")
    print(f"   Noch offen:            {updated_gefunden - updated_zugebucht}")
    print(f"   Nicht in Locosoft:     {len(positionen) - updated_gefunden}")
    
    # Status-Übersicht
    print("\n" + "=" * 80)
    print("STATUS-ÜBERSICHT NACH DATUM")
    print("=" * 80)
    
    sqlite_cur.execute("""
        SELECT 
            lieferdatum,
            COUNT(*) as total,
            SUM(CASE WHEN locosoft_gefunden = 1 THEN 1 ELSE 0 END) as gefunden,
            SUM(CASE WHEN locosoft_zugebucht = 1 THEN 1 ELSE 0 END) as zugebucht
        FROM teile_lieferscheine
        WHERE lieferdatum >= ?
        GROUP BY lieferdatum
        ORDER BY lieferdatum DESC
    """, (cutoff_date,))
    
    print(f"\n{'Datum':<12} {'Gesamt':>8} {'In Loco':>10} {'Zugebcht':>10} {'Offen':>8}")
    print("-" * 55)
    
    for row in sqlite_cur.fetchall():
        offen = row[2] - row[3] if row[2] else 0
        status = "🟢" if offen == 0 and row[2] == row[1] else "🟡" if row[2] > 0 else "⚪"
        print(f"{row[0]:<12} {row[1]:>8} {row[2] or 0:>10} {row[3] or 0:>10} {offen:>8} {status}")
    
    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    sync_with_locosoft()
