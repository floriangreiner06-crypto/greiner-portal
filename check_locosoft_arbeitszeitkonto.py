#!/usr/bin/env python3
"""Prüft Arbeitszeitkonto-Daten in Locosoft"""

import psycopg2

conn = psycopg2.connect(
    host='10.80.80.8',
    port=5432,
    database='loco_auswertung_db',
    user='loco_auswertung_benutzer',
    password='loco'
)
cursor = conn.cursor()

print("\n🔍 SUCHE ARBEITSZEITKONTO / URLAUBS-TABELLEN")
print("="*70)

# 1. Alle Tabellen mit Zeit/Stunden/Konto
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
      AND (table_name LIKE '%time%' 
           OR table_name LIKE '%hour%'
           OR table_name LIKE '%konto%'
           OR table_name LIKE '%account%'
           OR table_name LIKE '%absence%'
           OR table_name LIKE '%abwesenheit%')
    ORDER BY table_name
""")

tables = cursor.fetchall()
print(f"\n📋 Gefundene Tabellen ({len(tables)}):")
for t in tables:
    print(f"   • {t[0]}")

# 2. Prüfe ob es Daten für Sandra Brendel gibt (Mitarbeiter 1016)
print("\n🔍 Suche Daten für Sandra Brendel (1016):")

if tables:
    for table in tables[:5]:  # Erste 5 Tabellen testen
        table_name = table[0]
        try:
            # Prüfe ob employee_number Spalte existiert
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                  AND column_name LIKE '%employee%'
                LIMIT 1
            """)
            
            emp_col = cursor.fetchone()
            if emp_col:
                # Suche nach Mitarbeiter 1016
                cursor.execute(f"""
                    SELECT * FROM {table_name}
                    WHERE {emp_col[0]} = 1016
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                if row:
                    print(f"\n   ✓ Daten in {table_name}:")
                    # Zeige Spalten
                    cursor.execute(f"""
                        SELECT column_name 
                        FROM information_schema.columns
                        WHERE table_name = '{table_name}'
                        ORDER BY ordinal_position
                    """)
                    cols = [c[0] for c in cursor.fetchall()]
                    for i, col in enumerate(cols[:10]):  # Erste 10 Spalten
                        print(f"      {col}: {row[i] if i < len(row) else 'N/A'}")
        except Exception as e:
            pass  # Ignoriere Fehler

conn.close()
print("\n" + "="*70)
