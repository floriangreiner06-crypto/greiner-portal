#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync Fahrzeug-Stammdaten aus Locosoft → PostgreSQL (drive_portal)
Synchronisiert: HSN, TSN, Kennzeichen (Locosoft vehicles.license_plate) in fahrzeugfinanzierungen.
Kein SQLite – siehe docs/NO_SQLITE.md.
Version: 1.0 - TAG 79 | Updated: 2026-02-25 (PostgreSQL)
"""

import json
import sys
from datetime import datetime

sys.path.insert(0, '/opt/greiner-portal')
CREDENTIALS_PATH = '/opt/greiner-portal/config/credentials.json'


def main():
    print("=" * 60)
    print("🔄 FAHRZEUG-STAMMDATEN SYNC (Locosoft → PostgreSQL)")
    print("=" * 60)
    print(f"   Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    with open(CREDENTIALS_PATH) as f:
        creds = json.load(f)['databases']['locosoft']

    from api.db_utils import db_session, get_locosoft_connection

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, vin, hsn, tsn, kennzeichen, finanzinstitut
            FROM fahrzeugfinanzierungen
            WHERE aktiv = true AND vin IS NOT NULL
        """)
        rows = cursor.fetchall()
        fahrzeuge = [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows]

    print(f"📊 Fahrzeuge zu prüfen: {len(fahrzeuge)}\n")

    stats = {'gefunden': 0, 'hsn_updated': 0, 'tsn_updated': 0, 'kennzeichen_updated': 0, 'nicht_gefunden': 0}

    loco = get_locosoft_connection()
    pg_c = loco.cursor()

    with db_session() as conn:
        cursor = conn.cursor()
        for fz in fahrzeuge:
            fz_id, vin, hsn, tsn, kennzeichen_aktuell, finanzinstitut = fz[0], fz[1], fz[2], fz[3], fz[4], fz[5]
            pg_c.execute("""
                SELECT v.german_kba_hsn, v.german_kba_tsn, v.license_plate
                FROM vehicles v
                WHERE v.vin LIKE %s
                LIMIT 1
            """, (f'%{vin[-10:]}',))
            row = pg_c.fetchone()

            if row:
                stats['gefunden'] += 1
                hsn_new, tsn_new, kennzeichen = row[0], row[1], row[2]
                updates = []
                params = []
                if hsn_new and not hsn:
                    updates.append("hsn = %s")
                    params.append(hsn_new)
                    stats['hsn_updated'] += 1
                if tsn_new and not tsn:
                    updates.append("tsn = %s")
                    params.append(tsn_new)
                    stats['tsn_updated'] += 1
                if kennzeichen and (kennzeichen != (kennzeichen_aktuell or '').strip()):
                    updates.append("kennzeichen = %s")
                    params.append((kennzeichen or '').strip()[:20])
                    stats['kennzeichen_updated'] += 1
                if updates:
                    params.append(fz_id)
                    cursor.execute(f"""
                        UPDATE fahrzeugfinanzierungen
                        SET {', '.join(updates)}, aktualisiert_am = NOW()
                        WHERE id = %s
                    """, params)
            else:
                stats['nicht_gefunden'] += 1
        conn.commit()

    loco.close()

    print("=" * 60)
    print("📊 ERGEBNIS:")
    print("=" * 60)
    print(f"   Geprüft:           {len(fahrzeuge)}")
    print(f"   In Locosoft:       {stats['gefunden']}")
    print(f"   Nicht gefunden:    {stats['nicht_gefunden']}")
    print(f"   HSN aktualisiert:  {stats['hsn_updated']}")
    print(f"   TSN aktualisiert:  {stats['tsn_updated']}")
    print(f"   Kennzeichen aktualisiert: {stats['kennzeichen_updated']}")
    print("=" * 60)
    print(f"✅ Sync abgeschlossen: {datetime.now().strftime('%H:%M:%S')}\n")


if __name__ == '__main__':
    main()
