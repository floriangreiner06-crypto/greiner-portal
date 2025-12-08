#!/usr/bin/env python3
"""
Analyse des Leerlauf-Auftrags in Locosoft
TAG 101 - 2025-12-07
"""

import psycopg2
from datetime import datetime, timedelta

# Locosoft DB Connection
conn = psycopg2.connect(
    host="10.80.80.9",
    database="greaborx",
    user="flexreader",
    password="flex"
)

print("=" * 70)
print("ANALYSE: LEERLAUF-AUFTRAG IN LOCOSOFT")
print("=" * 70)

# 1. Suche nach Leerlauf-Auftrag
print("\n1. SUCHE NACH LEERLAUF-AUFTRAG")
print("-" * 50)

cur = conn.cursor()

# Suche in Aufträgen nach "Leerlauf"
cur.execute("""
    SELECT aufnr, aufart, aufstat, kundenname, fahrzeug, bemerkung, 
           anldat, anlzeit
    FROM auftrag 
    WHERE LOWER(kundenname) LIKE '%leerlauf%'
       OR LOWER(bemerkung) LIKE '%leerlauf%'
       OR LOWER(fahrzeug) LIKE '%leerlauf%'
    ORDER BY anldat DESC
    LIMIT 20
""")

rows = cur.fetchall()
if rows:
    print(f"Gefunden: {len(rows)} Aufträge mit 'Leerlauf'")
    for r in rows:
        print(f"  AufNr: {r[0]}, Art: {r[1]}, Status: {r[2]}, Kunde: {r[3]}")
        print(f"    Fahrzeug: {r[4]}, Bemerkung: {r[5]}")
        print(f"    Angelegt: {r[6]} {r[7]}")
        print()
else:
    print("Keine Aufträge mit 'Leerlauf' im Namen gefunden")

# 2. Suche nach festem/internem Auftrag
print("\n2. SUCHE NACH INTERNEN/FESTEN AUFTRÄGEN")
print("-" * 50)

cur.execute("""
    SELECT aufnr, aufart, aufstat, kundenname, fahrzeug, bemerkung
    FROM auftrag 
    WHERE aufart IN ('I', 'INTERN', 'INT')
       OR kundenname LIKE '%Intern%'
       OR aufnr LIKE 'INT%'
       OR aufnr LIKE '0000%'
    ORDER BY anldat DESC
    LIMIT 20
""")

rows = cur.fetchall()
if rows:
    print(f"Gefunden: {len(rows)} interne Aufträge")
    for r in rows:
        print(f"  AufNr: {r[0]}, Art: {r[1]}, Kunde: {r[3]}, Bemerkung: {r[5]}")
else:
    print("Keine internen Aufträge gefunden")

# 3. Stempelungen auf spezielle Aufträge
print("\n3. STEMPELUNGEN NACH AUFTRAGSTYP (letzte 7 Tage)")
print("-" * 50)

cur.execute("""
    SELECT 
        a.aufnr,
        a.kundenname,
        a.aufart,
        COUNT(*) as stempelungen,
        COUNT(DISTINCT z.persnr) as mechaniker
    FROM zeiterfassung z
    JOIN auftrag a ON z.aufnr = a.aufnr
    WHERE z.datum >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY a.aufnr, a.kundenname, a.aufart
    ORDER BY stempelungen DESC
    LIMIT 30
""")

rows = cur.fetchall()
print(f"{'AufNr':<12} {'Kunde':<25} {'Art':<6} {'Stempel':>8} {'Mech':>5}")
print("-" * 60)
for r in rows:
    print(f"{r[0]:<12} {str(r[1])[:25]:<25} {str(r[2]):<6} {r[3]:>8} {r[4]:>5}")

# 4. Gibt es Stempelungen ohne produktiven Auftrag?
print("\n4. STEMPELUNGEN OHNE PRODUKTIVEN AUFTRAG")
print("-" * 50)

cur.execute("""
    SELECT 
        z.persnr,
        p.name,
        z.aufnr,
        a.kundenname,
        z.datum,
        z.von,
        z.bis,
        EXTRACT(EPOCH FROM (z.bis - z.von))/60 as minuten
    FROM zeiterfassung z
    LEFT JOIN personal p ON z.persnr = p.persnr
    LEFT JOIN auftrag a ON z.aufnr = a.aufnr
    WHERE z.datum >= CURRENT_DATE - INTERVAL '7 days'
      AND z.bis IS NOT NULL
      AND (a.aufnr IS NULL 
           OR LOWER(a.kundenname) LIKE '%leerlauf%'
           OR LOWER(a.kundenname) LIKE '%intern%'
           OR a.aufart IN ('I', 'INTERN'))
    ORDER BY z.datum DESC, z.von DESC
    LIMIT 30
""")

rows = cur.fetchall()
if rows:
    print(f"{'PersNr':<8} {'Name':<20} {'AufNr':<12} {'Kunde':<20} {'Datum':<12} {'Min':>6}")
    print("-" * 80)
    for r in rows:
        print(f"{r[0]:<8} {str(r[1])[:20]:<20} {str(r[2]):<12} {str(r[3])[:20]:<20} {r[4]} {r[7]:>6.0f}")
else:
    print("Keine Stempelungen auf Leerlauf/Intern gefunden")

# 5. Alle Auftragsarten
print("\n5. ALLE AUFTRAGSARTEN IN LOCOSOFT")
print("-" * 50)

cur.execute("""
    SELECT aufart, COUNT(*) as anzahl
    FROM auftrag
    WHERE anldat >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY aufart
    ORDER BY anzahl DESC
""")

rows = cur.fetchall()
for r in rows:
    print(f"  {str(r[0]):<15} {r[1]:>8} Aufträge")

# 6. Spezielle Auftragsnummern-Bereiche
print("\n6. AUFTRAGSNUMMERN-BEREICHE")
print("-" * 50)

cur.execute("""
    SELECT 
        LEFT(aufnr, 2) as prefix,
        COUNT(*) as anzahl,
        MIN(aufnr) as beispiel_min,
        MAX(aufnr) as beispiel_max
    FROM auftrag
    WHERE anldat >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY LEFT(aufnr, 2)
    ORDER BY anzahl DESC
    LIMIT 15
""")

rows = cur.fetchall()
print(f"{'Prefix':<8} {'Anzahl':>8} {'Beispiel Min':<15} {'Beispiel Max':<15}")
print("-" * 50)
for r in rows:
    print(f"{r[0]:<8} {r[1]:>8} {r[2]:<15} {r[3]:<15}")

# 7. Suche nach Auftrag mit niedrigster/spezieller Nummer
print("\n7. AUFTRÄGE MIT SPEZIELLEN NUMMERN (potentiell fest)")
print("-" * 50)

cur.execute("""
    SELECT aufnr, kundenname, aufart, aufstat, bemerkung
    FROM auftrag
    WHERE aufnr ~ '^[0-9]+$'  -- Nur numerische
      AND CAST(aufnr AS INTEGER) < 1000
    ORDER BY CAST(aufnr AS INTEGER)
    LIMIT 20
""")

rows = cur.fetchall()
if rows:
    for r in rows:
        print(f"  AufNr: {r[0]}, Kunde: {r[1]}, Art: {r[2]}, Status: {r[3]}")
        if r[4]:
            print(f"    Bemerkung: {r[4]}")
else:
    print("Keine Aufträge mit niedriger Nummer gefunden")

cur.close()
conn.close()

print("\n" + "=" * 70)
print("ANALYSE ABGESCHLOSSEN")
print("=" * 70)
