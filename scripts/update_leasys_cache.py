#!/usr/bin/env python3
"""
Leasys Cache Update Script - PostgreSQL
Holt PKW (Opel + Leapmotor) + E-Nutzfahrzeuge und speichert in drive_portal (PostgreSQL).
Kein SQLite – siehe docs/NO_SQLITE.md.
"""
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, '/opt/greiner-portal')

# Master Agreements aus leasys_programme.json
CACHE_CONFIG = [
    {'brand': 'OPEL', 'fuel': 'B', 'ma_id': '1000026115'},
    {'brand': 'OPEL', 'fuel': 'D', 'ma_id': '1000026115'},
    {'brand': 'OPEL', 'fuel': 'E', 'ma_id': '1000026115'},
    {'brand': 'OPEL', 'fuel': 'E', 'ma_id': '1000023145'},
    {'brand': 'LEAPMOTOR', 'fuel': None, 'ma_id': '1000014601'},
]


def save_to_cache(brand, fuel, ma_id, vehicles):
    """Speichert Fahrzeuge in PostgreSQL leasys_vehicle_cache (drive_portal)."""
    from api.db_utils import db_session
    from api.db_connection import sql_placeholder

    ph = sql_placeholder()
    data_json = json.dumps(vehicles, ensure_ascii=False)
    # Upsert: ON CONFLICT (brand, fuel, ma_id) – gleiche Logik wie api/leasys_api.py
    upsert_sql = f"""
        INSERT INTO leasys_vehicle_cache (brand, fuel, ma_id, data, vehicle_count, created_at)
        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, NOW())
        ON CONFLICT (brand, COALESCE(fuel, ''), ma_id) DO UPDATE SET
            data = EXCLUDED.data,
            vehicle_count = EXCLUDED.vehicle_count,
            created_at = EXCLUDED.created_at
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(upsert_sql, (brand, fuel, ma_id, data_json, len(vehicles)))
        conn.commit()


def update_cache():
    print(f"[{datetime.now()}] Starte Leasys Cache Update (PostgreSQL)...")

    try:
        from tools.scrapers.leasys_full_api import LeasysAPI
        api = LeasysAPI()

        if not api.authenticate():
            print("FEHLER: Authentifizierung fehlgeschlagen")
            return False

        total_count = 0
        for config in CACHE_CONFIG:
            brand = config['brand']
            fuel = config['fuel']
            ma_id = config['ma_id']
            fuel_name = {'B': 'Benzin', 'D': 'Diesel', 'E': 'Elektro', None: 'Alle'}.get(fuel, fuel)
            print(f"\n{brand} {fuel_name} (MA: {ma_id})...")
            vehicles = api.get_vehicles(brand=brand, fuel=fuel, mast_ag_id=ma_id)
            save_to_cache(brand, fuel, ma_id, vehicles)
            print(f"  -> {len(vehicles)} Fahrzeuge gespeichert")
            total_count += len(vehicles)

        print(f"\n[{datetime.now()}] Cache Update erfolgreich!")
        print(f"Gesamt: {total_count} Fahrzeuge in {len(CACHE_CONFIG)} Cache-Einträgen")
        return True

    except Exception as e:
        print(f"FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = update_cache()
    sys.exit(0 if success else 1)
