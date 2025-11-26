#!/usr/bin/env python3
"""
Analyse: Locosoft PostgreSQL - Teile/Artikel-Tabellen finden
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor

# Credentials laden
with open('/opt/greiner-portal/config/credentials.json') as f:
    creds = json.load(f)['databases']['locosoft']

print("🔍 LOCOSOFT TEILE-TABELLEN ANALYSE")
print("=" * 70)

conn = psycopg2.connect(
    host=creds['host'],
    port=creds['port'],
    database=creds['database'],
    user=creds['user'],
    password=creds['password']
)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 1. Alle Tabellen auflisten die mit Teile/Parts zu tun haben könnten
print("\n📋 SUCHE RELEVANTE TABELLEN...")
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    AND (
        table_name ILIKE '%part%'
        OR table_name ILIKE '%teil%'
        OR table_name ILIKE '%article%'
        OR table_name ILIKE '%artikel%'
        OR table_name ILIKE '%item%'
        OR table_name ILIKE '%product%'
        OR table_name ILIKE '%stock%'
        OR table_name ILIKE '%lager%'
        OR table_name ILIKE '%inventory%'
        OR table_name ILIKE '%spare%'
        OR table_name ILIKE '%material%'
        OR table_name ILIKE '%goods%'
        OR table_name ILIKE '%waren%'
    )
    ORDER BY table_name
""")
teile_tabellen = cursor.fetchall()

if teile_tabellen:
    print(f"\n✅ {len(teile_tabellen)} potenzielle Teile-Tabellen gefunden:")
    for t in teile_tabellen:
        cursor.execute(f"SELECT COUNT(*) as cnt FROM {t['table_name']}")
        cnt = cursor.fetchone()['cnt']
        print(f"   - {t['table_name']}: {cnt:,} Einträge")
else:
    print("   ⚠️ Keine offensichtlichen Teile-Tabellen gefunden")

# 2. Alle Tabellen mit "number" oder "price" Spalten suchen
print("\n📋 TABELLEN MIT PREIS-SPALTEN SUCHEN...")
cursor.execute("""
    SELECT DISTINCT table_name 
    FROM information_schema.columns 
    WHERE table_schema = 'public'
    AND (
        column_name ILIKE '%price%'
        OR column_name ILIKE '%preis%'
        OR column_name ILIKE '%ek%'
        OR column_name ILIKE '%vk%'
        OR column_name ILIKE '%cost%'
    )
    ORDER BY table_name
    LIMIT 20
""")
preis_tabellen = cursor.fetchall()
print(f"   Tabellen mit Preis-Spalten: {len(preis_tabellen)}")
for t in preis_tabellen:
    print(f"   - {t['table_name']}")

# 3. Alle Tabellen auflisten (für Überblick)
print("\n📋 ALLE TABELLEN (alphabetisch, erste 50)...")
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
    LIMIT 50
""")
alle = cursor.fetchall()
for t in alle:
    print(f"   {t['table_name']}")

# 4. Verdächtige Tabellen im Detail analysieren
verdaechtig = ['parts', 'articles', 'items', 'spare_parts', 'stock', 'inventory', 
               'order_items', 'invoice_items', 'order_positions', 'invoice_positions']

print("\n📋 DETAIL-CHECK BEKANNTER TABELLENNAMEN...")
for tabelle in verdaechtig:
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = %s
        )
    """, (tabelle,))
    exists = cursor.fetchone()['exists']
    if exists:
        print(f"   ✅ {tabelle} existiert!")
        # Schema anzeigen
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position
            LIMIT 15
        """, (tabelle,))
        cols = cursor.fetchall()
        for c in cols:
            print(f"      - {c['column_name']}: {c['data_type']}")

# 5. orders und invoices Tabellen prüfen (könnten Positionen haben)
print("\n📋 CHECK: orders / invoices STRUKTUR...")
for tabelle in ['orders', 'invoices', 'order_items', 'invoice_items']:
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = %s
        )
    """, (tabelle,))
    if cursor.fetchone()['exists']:
        cursor.execute(f"SELECT COUNT(*) as cnt FROM {tabelle}")
        cnt = cursor.fetchone()['cnt']
        print(f"\n   📦 {tabelle}: {cnt:,} Einträge")
        
        # Spalten mit "part", "article", "item", "price" suchen
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s
            AND (
                column_name ILIKE '%part%'
                OR column_name ILIKE '%article%'
                OR column_name ILIKE '%item%'
                OR column_name ILIKE '%price%'
                OR column_name ILIKE '%number%'
                OR column_name ILIKE '%description%'
                OR column_name ILIKE '%bezeichnung%'
            )
        """, (tabelle,))
        relevant = cursor.fetchall()
        if relevant:
            print(f"      Relevante Spalten:")
            for c in relevant:
                print(f"        - {c['column_name']}: {c['data_type']}")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("✅ Analyse abgeschlossen!")
