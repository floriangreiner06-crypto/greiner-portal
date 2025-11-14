#!/usr/bin/env python3
import sqlite3
import pandas as pd

# Excel laden
excel = pd.read_excel('/opt/greiner-portal/data/Kontoaufstellung.xlsx')
excel['IBAN_clean'] = excel['IBAN'].astype(str).str.replace(' ', '')

# Soll-Limits aus Excel extrahieren
soll_limits = {}
for idx, row in excel.iterrows():
    if pd.notna(row['IBAN_clean']) and row['IBAN_clean'] != 'nan':
        iban = row['IBAN_clean']
        limit = row['Limit'] if pd.notna(row['Limit']) else 0
        soll_limits[iban] = limit

# DB-Limits abfragen
conn = sqlite3.connect('/opt/greiner-portal/data/greiner_controlling.db')
cursor = conn.cursor()
cursor.execute("""
    SELECT 
        id,
        kontoname,
        iban,
        kreditlinie
    FROM konten
    WHERE iban IS NOT NULL
    ORDER BY id
""")

print("=" * 100)
print("📊 VERGLEICH: DB-LIMITS vs. EXCEL-LIMITS")
print("=" * 100)
print()

updates_needed = []

for row in cursor.fetchall():
    konto_id, kontoname, iban, db_limit = row
    db_limit = db_limit or 0
    soll_limit = soll_limits.get(iban, 0)
    
    if db_limit == soll_limit:
        status = "✅ OK"
    else:
        status = "❌ FEHLT"
        updates_needed.append((konto_id, kontoname, iban, db_limit, soll_limit))
    
    print(f"{status:8s} | ID {konto_id:2d} | {kontoname:30s} | DB: {db_limit:>10.0f} | SOLL: {soll_limit:>10.0f}")

conn.close()

print()
print("=" * 100)
print("🔧 BENÖTIGTE UPDATES")
print("=" * 100)

if updates_needed:
    print(f"\n{len(updates_needed)} Konten benötigen Limit-Korrektur:\n")
    for konto_id, kontoname, iban, db_limit, soll_limit in updates_needed:
        diff = soll_limit - db_limit
        print(f"ID {konto_id:2d} | {kontoname:30s} | +{diff:>10.0f} EUR")
else:
    print("\n✅ Alle Limits sind korrekt!")
