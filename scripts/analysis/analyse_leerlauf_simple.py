#!/usr/bin/env python3
"""
Einfache Leerlauf-Analyse - TAG 101
"""

import psycopg2

conn = psycopg2.connect(
    host="10.80.80.9",
    database="greaborx",
    user="flexreader",
    password="flex"
)
cur = conn.cursor()

print("=" * 60)
print("LEERLAUF-ANALYSE")
print("=" * 60)

# 1. Suche Leerlauf im Auftragsnamen
print("\n1. Aufträge mit 'Leerlauf' im Namen:")
print("-" * 40)
cur.execute("""
    SELECT aufnr, kundenname, aufart, aufstat
    FROM auftrag 
    WHERE LOWER(kundenname) LIKE '%leerlauf%'
    LIMIT 10
""")
for r in cur.fetchall():
    print(f"  {r[0]} | {r[1]} | Art: {r[2]} | Status: {r[3]}")

# 2. Auftragsarten
print("\n2. Auftragsarten (letzte 30 Tage):")
print("-" * 40)
cur.execute("""
    SELECT aufart, COUNT(*) 
    FROM auftrag
    WHERE anldat >= CURRENT_DATE - 30
    GROUP BY aufart
    ORDER BY COUNT(*) DESC
""")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# 3. Niedrige Auftragsnummern
print("\n3. Aufträge mit niedriger Nummer (<100):")
print("-" * 40)
cur.execute("""
    SELECT aufnr, kundenname, aufart
    FROM auftrag
    WHERE aufnr ~ '^[0-9]+$'
    ORDER BY aufnr::integer
    LIMIT 15
""")
for r in cur.fetchall():
    print(f"  {r[0]} | {r[1]} | {r[2]}")

cur.close()
conn.close()
print("\nFertig.")
