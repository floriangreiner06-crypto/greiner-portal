#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync Fahrzeug-Stammdaten aus Locosoft → SQLite
Synchronisiert: HSN, TSN, Kennzeichen
Version: 1.0 - TAG 79
"""

import sqlite3
import json
import psycopg2
from datetime import datetime

# Konfiguration
SQLITE_DB = '/opt/greiner-portal/data/greiner_controlling.db'
CREDENTIALS_PATH = '/opt/greiner-portal/config/credentials.json'

def main():
    print("=" * 60)
    print("🔄 FAHRZEUG-STAMMDATEN SYNC (Locosoft → SQLite)")
    print("=" * 60)
    print(f"   Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Credentials laden
    with open(CREDENTIALS_PATH) as f:
        creds = json.load(f)['databases']['locosoft']

    # Verbindungen
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_c = sqlite_conn.cursor()

    pg_conn = psycopg2.connect(
        host=creds['host'],
        database=creds['database'],
        user=creds['user'],
        password=creds['password']
    )
    pg_c = pg_conn.cursor()

    # Alle aktiven Fahrzeuge aus SQLite holen
    sqlite_c.execute("""
        SELECT id, vin, hsn, tsn, finanzinstitut 
        FROM fahrzeugfinanzierungen 
        WHERE aktiv = 1 AND vin IS NOT NULL
    """)
    fahrzeuge = sqlite_c.fetchall()
    
    print(f"📊 Fahrzeuge zu prüfen: {len(fahrzeuge)}\n")

    stats = {
        'gefunden': 0,
        'hsn_updated': 0,
        'tsn_updated': 0,
        'kennzeichen_updated': 0,
        'nicht_gefunden': 0
    }

    for fz in fahrzeuge:
        fz_id = fz['id']
        vin = fz['vin']
        
        # In Locosoft suchen (letzte 10 Zeichen der VIN)
        pg_c.execute("""
            SELECT 
                v.german_kba_hsn,
                v.german_kba_tsn,
                v.license_plate
            FROM vehicles v
            WHERE v.vin LIKE %s
            LIMIT 1
        """, (f'%{vin[-10:]}',))
        
        row = pg_c.fetchone()
        
        if row:
            stats['gefunden'] += 1
            hsn, tsn, kennzeichen = row
            
            updates = []
            params = []
            
            # HSN updaten wenn vorhanden und noch nicht gesetzt
            if hsn and not fz['hsn']:
                updates.append("hsn = ?")
                params.append(hsn)
                stats['hsn_updated'] += 1
            
            # TSN updaten wenn vorhanden und noch nicht gesetzt
            if tsn and not fz['tsn']:
                updates.append("tsn = ?")
                params.append(tsn)
                stats['tsn_updated'] += 1
            
            # Kennzeichen ist nicht in der Tabelle - könnten wir hinzufügen
            # Erstmal nur zählen
            if kennzeichen:
                stats['kennzeichen_updated'] += 1
            
            # Update ausführen
            if updates:
                params.append(fz_id)
                sqlite_c.execute(f"""
                    UPDATE fahrzeugfinanzierungen 
                    SET {', '.join(updates)}, aktualisiert_am = datetime('now')
                    WHERE id = ?
                """, params)
        else:
            stats['nicht_gefunden'] += 1

    sqlite_conn.commit()
    sqlite_conn.close()
    pg_conn.close()

    # Ergebnis
    print("=" * 60)
    print("📊 ERGEBNIS:")
    print("=" * 60)
    print(f"   Geprüft:           {len(fahrzeuge)}")
    print(f"   In Locosoft:       {stats['gefunden']}")
    print(f"   Nicht gefunden:    {stats['nicht_gefunden']}")
    print(f"   HSN aktualisiert:  {stats['hsn_updated']}")
    print(f"   TSN aktualisiert:  {stats['tsn_updated']}")
    print(f"   Mit Kennzeichen:   {stats['kennzeichen_updated']}")
    print("=" * 60)
    print(f"✅ Sync abgeschlossen: {datetime.now().strftime('%H:%M:%S')}\n")


if __name__ == '__main__':
    main()
