#!/usr/bin/env python3
"""
Analyse: parts_master - Preise und Marken (Stellantis + Hyundai)
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor

with open('/opt/greiner-portal/config/credentials.json') as f:
    creds = json.load(f)['databases']['locosoft']

print("🔍 PARTS_MASTER - MARKEN & PREISE ANALYSE")
print("=" * 70)

conn = psycopg2.connect(
    host=creds['host'],
    port=creds['port'],
    database=creds['database'],
    user=creds['user'],
    password=creds['password']
)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Welche Marken/Hersteller gibt es? (via Teilenummern-Muster)
print("\n📋 TEILENUMMERN-MUSTER ANALYSE:")

# Stellantis-Muster (10-stellig, beginnt mit 98, 16, etc.)
cursor.execute("""
    SELECT COUNT(*) as cnt FROM parts_master 
    WHERE part_number ~ '^[0-9]{10}$'
""")
stellantis_count = cursor.fetchone()['cnt']
print(f"   10-stellige Nummern (Stellantis-Stil): {stellantis_count:,}")

# Hyundai-Muster (meist mit Buchstaben oder speziellem Format)
cursor.execute("""
    SELECT LEFT(part_number, 2) as prefix, COUNT(*) as cnt 
    FROM parts_master 
    GROUP BY LEFT(part_number, 2)
    ORDER BY cnt DESC
    LIMIT 20
""")
prefixes = cursor.fetchall()
print(f"\n   Top 20 Teilenummer-Präfixe:")
for p in prefixes:
    print(f"      {p['prefix']}: {p['cnt']:,}")

# 2. Hyundai spezifisch suchen
print("\n" + "=" * 70)
print("📋 SUCHE HYUNDAI-TEILE:")

# Typische Hyundai-Nummern haben oft Buchstaben
cursor.execute("""
    SELECT part_number, description, rr_price
    FROM parts_master 
    WHERE part_number LIKE '%HYU%'
    OR description ILIKE '%hyundai%'
    OR description ILIKE '%tucson%'
    OR description ILIKE '%i20%'
    OR description ILIKE '%i30%'
    LIMIT 10
""")
hyundai = cursor.fetchall()
if hyundai:
    print(f"   ✅ {len(hyundai)} Hyundai-Treffer:")
    for h in hyundai:
        print(f"      {h['part_number']}: {h['description']} | {h['rr_price']}€")
else:
    print("   ⚠️ Keine direkten Hyundai-Treffer")
    
    # Alternative: Suche nach typischen Hyundai-Teilenummern-Mustern
    print("\n   Suche nach Hyundai-typischen Mustern...")
    cursor.execute("""
        SELECT part_number, description, rr_price
        FROM parts_master 
        WHERE part_number ~ '^[0-9]{5}[A-Z]'
        OR part_number ~ '^[A-Z]{2}[0-9]'
        LIMIT 15
    """)
    alt = cursor.fetchall()
    if alt:
        print(f"   Muster-Treffer ({len(alt)}):")
        for a in alt:
            print(f"      {a['part_number']}: {a['description']}")

# 3. Marken via parts_type oder manufacturer unterscheiden?
print("\n" + "=" * 70)
print("📋 PARTS_TYPE VERTEILUNG:")
cursor.execute("""
    SELECT parts_type, COUNT(*) as cnt 
    FROM parts_master 
    GROUP BY parts_type
    ORDER BY cnt DESC
""")
types = cursor.fetchall()
for t in types:
    print(f"   Type {t['parts_type']}: {t['cnt']:,} Teile")

# 4. part_types Tabelle (Referenz)
print("\n" + "=" * 70)
print("📋 PART_TYPES REFERENZ-TABELLE:")
cursor.execute("SELECT * FROM part_types ORDER BY 1")
pt = cursor.fetchall()
for p in pt:
    print(f"   {p}")

# 5. Beispiel-Teile mit Preisen
print("\n" + "=" * 70)
print("📋 BEISPIEL-TEILE MIT PREISEN:")
cursor.execute("""
    SELECT 
        part_number,
        description,
        rr_price,
        rebate_code,
        manufacturer_parts_type,
        last_import_date
    FROM parts_master 
    WHERE rr_price > 0 
    AND rr_price < 1000
    ORDER BY RANDOM()
    LIMIT 15
""")
rows = cursor.fetchall()
for row in rows:
    print(f"   {row['part_number']}: {row['description'][:35]:35} | {row['rr_price']:>8.2f}€ | {row['rebate_code']} | {row['manufacturer_parts_type']}")

# 6. Gibt es eine separate Hyundai-Datenbank/Schema?
print("\n" + "=" * 70)
print("📋 SUCHE NACH HYUNDAI-SPEZIFISCHEN TABELLEN:")
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    AND (
        table_name ILIKE '%hyundai%'
        OR table_name ILIKE '%kia%'
        OR table_name ILIKE '%hyu%'
    )
""")
hyu_tables = cursor.fetchall()
if hyu_tables:
    for t in hyu_tables:
        print(f"   ✅ {t['table_name']}")
else:
    print("   ❌ Keine Hyundai-spezifischen Tabellen")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("✅ Analyse abgeschlossen!")
