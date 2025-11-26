#!/usr/bin/env python3
"""
Analyse: parts_master Schema und Beispieldaten
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor

with open('/opt/greiner-portal/config/credentials.json') as f:
    creds = json.load(f)['databases']['locosoft']

print("🔍 PARTS_MASTER SCHEMA-ANALYSE")
print("=" * 70)

conn = psycopg2.connect(
    host=creds['host'],
    port=creds['port'],
    database=creds['database'],
    user=creds['user'],
    password=creds['password']
)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Komplettes Schema von parts_master
print("\n📋 SCHEMA: parts_master")
cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns 
    WHERE table_name = 'parts_master'
    ORDER BY ordinal_position
""")
cols = cursor.fetchall()
print(f"   {len(cols)} Spalten:")
for c in cols:
    print(f"   - {c['column_name']}: {c['data_type']}")

# 2. Beispieldaten mit einer Stellantis-Teilenummer
print("\n" + "=" * 70)
print("📋 BEISPIEL: Stellantis Teilenummer 9837096880 (Ölwanne)")
cursor.execute("""
    SELECT * FROM parts_master 
    WHERE part_number LIKE '%9837096880%'
    OR part_number LIKE '%98370968%'
    LIMIT 5
""")
rows = cursor.fetchall()
if rows:
    print(f"   ✅ {len(rows)} Treffer!")
    for row in rows:
        print(f"\n   Teilenummer: {row.get('part_number')}")
        for key, val in row.items():
            if val is not None and val != '' and val != 0:
                print(f"      {key}: {val}")
else:
    print("   ⚠️ Keine Treffer - versuche andere Suche...")
    # Alternative Suche
    cursor.execute("""
        SELECT part_number, description, retail_price, purchase_price
        FROM parts_master 
        WHERE description ILIKE '%ölwanne%'
        OR description ILIKE '%oelwanne%'
        LIMIT 5
    """)
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"   - {row}")

# 3. Preis-Spalten identifizieren
print("\n" + "=" * 70)
print("📋 PREIS-RELEVANTE SPALTEN:")
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'parts_master'
    AND (
        column_name ILIKE '%price%'
        OR column_name ILIKE '%preis%'
        OR column_name ILIKE '%cost%'
        OR column_name ILIKE '%retail%'
        OR column_name ILIKE '%purchase%'
        OR column_name ILIKE '%ek%'
        OR column_name ILIKE '%vk%'
    )
""")
preis_cols = cursor.fetchall()
for c in preis_cols:
    print(f"   - {c['column_name']}")

# 4. Beispiel mit Preisen
print("\n" + "=" * 70)
print("📋 BEISPIEL-TEILE MIT PREISEN (erste 10):")
cursor.execute("""
    SELECT 
        part_number,
        description,
        retail_price,
        purchase_price,
        stock_amount
    FROM parts_master 
    WHERE retail_price > 0 
    AND purchase_price > 0
    LIMIT 10
""")
rows = cursor.fetchall()
for row in rows:
    print(f"   {row['part_number']}: {row.get('description', '')[:40]}")
    print(f"      EK: {row.get('purchase_price')} | VK: {row.get('retail_price')} | Bestand: {row.get('stock_amount')}")

# 5. parts_stock Schema
print("\n" + "=" * 70)
print("📋 SCHEMA: parts_stock")
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns 
    WHERE table_name = 'parts_stock'
    ORDER BY ordinal_position
""")
cols = cursor.fetchall()
for c in cols:
    print(f"   - {c['column_name']}: {c['data_type']}")

# 6. parts_supplier_numbers Schema (Cross-Reference)
print("\n" + "=" * 70)
print("📋 SCHEMA: parts_supplier_numbers (Cross-Reference OEM ↔ Aftermarket)")
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns 
    WHERE table_name = 'parts_supplier_numbers'
    ORDER BY ordinal_position
""")
cols = cursor.fetchall()
for c in cols:
    print(f"   - {c['column_name']}: {c['data_type']}")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("✅ Analyse abgeschlossen!")
