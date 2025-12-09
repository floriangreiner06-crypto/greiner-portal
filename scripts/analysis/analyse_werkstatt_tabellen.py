#!/usr/bin/env python3
"""
Analyse der Locosoft-Tabellen für Werkstattplanung
Erstellt: TAG 83+ (Werkstattplanung-Projekt)
"""

import psycopg2
import json
from tabulate import tabulate

# Credentials laden
with open('/opt/greiner-portal/config/credentials.json') as f:
    creds = json.load(f)

db_config = creds.get('databases', {}).get('locosoft', creds.get('locosoft', {}))

conn = psycopg2.connect(
    host=db_config.get('host', '10.80.80.8'),
    port=db_config.get('port', 5432),
    database=db_config.get('database', 'loco_auswertung_db'),
    user=db_config.get('user', 'loco_auswertung_benutzer'),
    password=db_config.get('password')
)

cursor = conn.cursor()

print("=" * 70)
print("LOCOSOFT WERKSTATT-ANALYSE")
print("=" * 70)

# 1. Relevante Tabellen finden
print("\n📋 1. RELEVANTE TABELLEN FÜR WERKSTATT")
print("-" * 50)

cursor.execute("""
    SELECT table_name, 
           (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as spalten
    FROM information_schema.tables t
    WHERE table_schema = 'public' 
    AND (
        LOWER(table_name) LIKE '%order%' 
        OR LOWER(table_name) LIKE '%workshop%'
        OR LOWER(table_name) LIKE '%werkstatt%'
        OR LOWER(table_name) LIKE '%termin%'
        OR LOWER(table_name) LIKE '%appointment%'
        OR LOWER(table_name) LIKE '%service%'
        OR LOWER(table_name) LIKE '%repair%'
        OR LOWER(table_name) LIKE '%auftrag%'
        OR LOWER(table_name) LIKE '%job%'
        OR LOWER(table_name) LIKE '%work%'
    )
    ORDER BY table_name;
""")

tables = cursor.fetchall()
for t in tables:
    # Anzahl Datensätze pro Tabelle
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {t[0]}")
        count = cursor.fetchone()[0]
        print(f"  📁 {t[0]:40} | {t[1]:3} Spalten | {count:,} Datensätze")
    except:
        print(f"  📁 {t[0]:40} | {t[1]:3} Spalten | (Fehler beim Zählen)")

# 2. orders-Tabelle analysieren (die ist LIVE!)
print("\n\n📋 2. ORDERS-TABELLE (LIVE!) - SCHEMA")
print("-" * 50)

cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns 
    WHERE table_name = 'orders'
    ORDER BY ordinal_position;
""")

columns = cursor.fetchall()
for c in columns:
    print(f"  {c[0]:40} | {c[1]:20} | {'NULL' if c[2] == 'YES' else 'NOT NULL'}")

# 3. Beispiel-Daten aus orders
print("\n\n📋 3. BEISPIEL-AUFTRÄGE (letzte 5)")
print("-" * 50)

cursor.execute("""
    SELECT * FROM orders 
    ORDER BY COALESCE(created_at, updated_at, '1900-01-01') DESC 
    LIMIT 5;
""")

rows = cursor.fetchall()
col_names = [desc[0] for desc in cursor.description]

for i, row in enumerate(rows):
    print(f"\n--- Auftrag {i+1} ---")
    for j, val in enumerate(row):
        if val is not None:
            print(f"  {col_names[j]:30}: {val}")

# 4. Statistiken
print("\n\n📋 4. AUFTRAGS-STATISTIKEN")
print("-" * 50)

cursor.execute("""
    SELECT 
        COUNT(*) as gesamt,
        COUNT(CASE WHEN created_at::date = CURRENT_DATE THEN 1 END) as heute,
        COUNT(CASE WHEN created_at::date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as letzte_7_tage,
        COUNT(CASE WHEN created_at::date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as letzte_30_tage
    FROM orders;
""")

stats = cursor.fetchone()
print(f"  Gesamt:         {stats[0]:,}")
print(f"  Heute:          {stats[1]:,}")
print(f"  Letzte 7 Tage:  {stats[2]:,}")
print(f"  Letzte 30 Tage: {stats[3]:,}")

# 5. Suche nach Mietwagen/Ersatzwagen-Tabellen
print("\n\n📋 5. MIETWAGEN / ERSATZWAGEN TABELLEN")
print("-" * 50)

cursor.execute("""
    SELECT table_name
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND (
        LOWER(table_name) LIKE '%miet%' 
        OR LOWER(table_name) LIKE '%rental%'
        OR LOWER(table_name) LIKE '%ersatz%'
        OR LOWER(table_name) LIKE '%replacement%'
        OR LOWER(table_name) LIKE '%loan%'
        OR LOWER(table_name) LIKE '%courtesy%'
    )
    ORDER BY table_name;
""")

rental_tables = cursor.fetchall()
if rental_tables:
    for t in rental_tables:
        print(f"  📁 {t[0]}")
else:
    print("  (keine spezifischen Tabellen gefunden)")

# 6. Alle 103 Tabellen auflisten
print("\n\n📋 6. ALLE LOCOSOFT-TABELLEN (für Referenz)")
print("-" * 50)

cursor.execute("""
    SELECT table_name
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")

all_tables = cursor.fetchall()
for i, t in enumerate(all_tables):
    print(f"  {i+1:3}. {t[0]}")

print(f"\n  GESAMT: {len(all_tables)} Tabellen")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("ANALYSE ABGESCHLOSSEN")
print("=" * 70)
