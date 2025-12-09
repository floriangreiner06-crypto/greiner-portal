#!/usr/bin/env python3
"""
Quick Check: Locosoft journal_accountings Spaltenstruktur
"""
import json
import psycopg2

# Credentials laden
with open('/opt/greiner-portal/config/credentials.json', 'r') as f:
    creds = json.load(f)

locosoft = creds['databases']['locosoft']

# Verbinden
conn = psycopg2.connect(
    host=locosoft['host'],
    database=locosoft['database'],
    user=locosoft['user'],
    password=locosoft['password']
)

cursor = conn.cursor()

# Spalten-Info holen
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'journal_accountings'
    ORDER BY ordinal_position;
""")

print("=" * 60)
print("SPALTEN DER TABELLE journal_accountings:")
print("=" * 60)
for row in cursor.fetchall():
    print(f"{row[0]:30s} {row[1]}")

print("\n" + "=" * 60)
print("ERSTE ZEILE (Beispiel-Daten):")
print("=" * 60)

cursor.execute("SELECT * FROM journal_accountings LIMIT 1")
row = cursor.fetchone()
cols = [desc[0] for desc in cursor.description]

for col, val in zip(cols, row):
    print(f"{col:30s} {val}")

conn.close()
