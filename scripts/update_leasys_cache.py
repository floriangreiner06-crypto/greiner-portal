#!/usr/bin/env python3
"""
Leasys Cache Update Script - SQLite Version
============================================
Liest Master Agreements aus leasys_programme.json (Single Source of Truth)
und cached alle Fahrzeuge für Opel + Leapmotor.

Update: 2025-12-04 - MAs aus JSON lesen statt hardcoded
"""
import sys
import os
import json
import sqlite3
from datetime import datetime

sys.path.insert(0, '/opt/greiner-portal')
DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
CONFIG_PATH = '/opt/greiner-portal/config/leasys_programme.json'

# Kraftstoff-Varianten für PKW
FUEL_TYPES = ['B', 'D', 'E']  # Benzin, Diesel, Elektro

# Marken die ohne Fuel-Filter gecached werden (gemischte Antriebe)
BRANDS_WITHOUT_FUEL_FILTER = ['LEAPMOTOR']


def load_master_agreements():
    """Lädt Master Agreements aus der JSON-Konfiguration."""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    programme = config.get('programme', [])
    
    # Gruppiere nach Marke
    by_brand = {}
    for prog in programme:
        marke = prog.get('marke', '').upper()
        if marke not in by_brand:
            by_brand[marke] = []
        by_brand[marke].append({
            'ma_id': prog.get('ma_id'),
            'name': prog.get('name'),
            'fahrzeugtyp': prog.get('fahrzeugtyp'),
            'buyback': prog.get('buyback'),
            'aktiv': prog.get('aktiv', True)
        })
    
    return by_brand


def save_to_cache(brand, fuel, ma_id, vehicles):
    """Speichert Fahrzeuge in SQLite-Cache."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    data_json = json.dumps(vehicles, ensure_ascii=False)
    
    cursor.execute('''
        INSERT OR REPLACE INTO leasys_vehicle_cache 
        (brand, fuel, ma_id, data, vehicle_count, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
    ''', (brand, fuel, ma_id, data_json, len(vehicles)))
    
    conn.commit()
    conn.close()


def update_cache():
    print(f"[{datetime.now()}] Starte Leasys Cache Update (SQLite)...")
    print(f"Lese MAs aus: {CONFIG_PATH}")
    print("=" * 70)
    
    try:
        # MAs aus JSON laden
        mas_by_brand = load_master_agreements()
        
        print(f"\nGefundene Marken: {list(mas_by_brand.keys())}")
        for brand, mas in mas_by_brand.items():
            print(f"  {brand}: {len(mas)} Master Agreements")
        
        # Leasys API Client
        from tools.scrapers.leasys_full_api import LeasysAPI
        api = LeasysAPI()
        
        if not api.authenticate():
            print("\n❌ FEHLER: Authentifizierung fehlgeschlagen")
            return False
        
        total_vehicles = 0
        total_cache_entries = 0
        errors = []
        
        # Jede Marke durchgehen
        for brand, mas in mas_by_brand.items():
            print(f"\n{'=' * 70}")
            print(f"📦 {brand} - {len(mas)} Master Agreements")
            print("=" * 70)
            
            for ma in mas:
                if not ma.get('aktiv', True):
                    print(f"\n⏭️  {ma['name']} - INAKTIV, übersprungen")
                    continue
                
                ma_id = ma['ma_id']
                ma_name = ma['name']
                
                print(f"\n📋 {ma_name}")
                print(f"   MA-ID: {ma_id}")
                
                # Entscheide ob mit oder ohne Fuel-Filter
                if brand in BRANDS_WITHOUT_FUEL_FILTER:
                    # Ohne Fuel-Filter (z.B. Leapmotor - Elektro + REEV gemischt)
                    try:
                        vehicles = api.get_vehicles(brand=brand, fuel=None, mast_ag_id=ma_id)
                        save_to_cache(brand, None, ma_id, vehicles)
                        
                        if vehicles:
                            print(f"   ✅ Alle Kraftstoffe: {len(vehicles)} Fahrzeuge")
                            total_vehicles += len(vehicles)
                        else:
                            print(f"   ⚪ Alle Kraftstoffe: 0 Fahrzeuge")
                        
                        total_cache_entries += 1
                        
                    except Exception as e:
                        print(f"   ❌ Fehler: {e}")
                        errors.append(f"{brand} {ma_name}: {e}")
                else:
                    # Mit Fuel-Filter (Opel - getrennt nach B/D/E)
                    for fuel in FUEL_TYPES:
                        fuel_name = {'B': 'Benzin', 'D': 'Diesel', 'E': 'Elektro'}[fuel]
                        
                        try:
                            vehicles = api.get_vehicles(brand=brand, fuel=fuel, mast_ag_id=ma_id)
                            save_to_cache(brand, fuel, ma_id, vehicles)
                            
                            if vehicles:
                                print(f"   ✅ {fuel_name}: {len(vehicles)} Fahrzeuge")
                                total_vehicles += len(vehicles)
                            else:
                                print(f"   ⚪ {fuel_name}: 0 Fahrzeuge")
                            
                            total_cache_entries += 1
                            
                        except Exception as e:
                            print(f"   ❌ {fuel_name}: Fehler - {e}")
                            errors.append(f"{brand} {ma_name} {fuel_name}: {e}")
        
        # Zusammenfassung
        print(f"\n{'=' * 70}")
        print(f"[{datetime.now()}] Cache Update abgeschlossen!")
        print(f"{'=' * 70}")
        print(f"✅ Gesamt: {total_vehicles} Fahrzeuge in {total_cache_entries} Cache-Einträgen")
        
        if errors:
            print(f"\n⚠️  {len(errors)} Fehler aufgetreten:")
            for err in errors[:10]:  # Max 10 Fehler anzeigen
                print(f"   - {err}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ KRITISCHER FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = update_cache()
    sys.exit(0 if success else 1)
