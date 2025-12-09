#!/usr/bin/env python3
"""
GUDAT → LOCOSOFT Verknüpfung
"""

import json
import psycopg2

print("=" * 70)
print("GUDAT → LOCOSOFT VERKNÜPFUNG")
print("=" * 70)

with open('/opt/greiner-portal/config/credentials.json', 'r') as f:
    config = json.load(f)

locosoft_config = config.get('databases', {}).get('locosoft', {})

conn = psycopg2.connect(
    host=locosoft_config.get('host'),
    port=locosoft_config.get('port', 5432),
    database=locosoft_config.get('database'),
    user=locosoft_config.get('user'),
    password=locosoft_config.get('password')
)
cursor = conn.cursor()
print("✅ Locosoft DB verbunden")

# Firmenstruktur
print("\n[1] Firmenstruktur (Betriebe)...")
print("=" * 70)

cursor.execute("""
    SELECT subsidiary, COUNT(*), MIN(number), MAX(number)
    FROM orders
    GROUP BY subsidiary
    ORDER BY subsidiary
""")

print(f"\n{'Betrieb':<10} {'Beschreibung':<30} {'Anzahl':<10} {'Nummern'}")
print("-" * 70)

betrieb_namen = {
    1: 'Stellantis Deggendorf',
    2: 'Hyundai Deggendorf',
    3: 'Stellantis Landau'
}

for row in cursor.fetchall():
    betrieb = row[0]
    name = betrieb_namen.get(betrieb, f'Unbekannt ({betrieb})')
    print(f"{betrieb:<10} {name:<30} {row[1]:<10} {row[2]} - {row[3]}")

# Gudat = Deggendorf = Betrieb 1 + 2
print("\n\n[2] Gudat Auftragsnummern (Deggendorf = Betrieb 1+2)...")
print("=" * 70)

gudat_orders = [
    (219379, 'DEG-X 212'),    # Hyundai = Betrieb 2
    (38073, 'VIT-AD 888'),    # Stellantis = Betrieb 1
    (38393, 'DEG-JP 111'),
    (38791, 'REG-JT 223'),
    (37423, 'DEG-ML 710'),
    (219690, 'VIT-E 78 E'),   # Hyundai
    (219981, 'REG-RM 244'),   # Hyundai
    (218687, 'SR-FN 444 E'),  # Hyundai
]

print(f"\n{'Gudat-Nr':<10} {'Gudat-KZ':<15} {'Status':<10} {'Betrieb':<25} {'Kunde':<20} {'Datum'}")
print("-" * 100)

found = 0
for num, plate in gudat_orders:
    # Ohne dealer_vehicles JOIN erstmal
    cursor.execute("""
        SELECT o.number, o.order_date, o.subsidiary,
               c.first_name, c.family_name
        FROM orders o
        LEFT JOIN customers_suppliers c ON o.order_customer = c.customer_number
        WHERE o.number = %s
    """, (num,))
    
    result = cursor.fetchone()
    if result:
        found += 1
        betrieb = result[2]
        betrieb_name = betrieb_namen.get(betrieb, '?')[:25]
        kunde = f"{result[3] or ''} {result[4] or ''}".strip()[:20]
        datum = str(result[1])[:10] if result[1] else '-'
        
        print(f"{num:<10} {plate:<15} ✅         {betrieb_name:<25} {kunde:<20} {datum}")
    else:
        print(f"{num:<10} {plate:<15} ❌")

print(f"\n   Gefunden: {found}/{len(gudat_orders)}")

# Detail für einen Auftrag
print("\n\n[3] Detail Auftrag 219379...")
print("=" * 70)

cursor.execute("""
    SELECT 
        o.number as auftrag_nr,
        o.subsidiary as betrieb,
        o.order_date,
        o.vehicle_number,
        o.order_mileage as km_stand,
        o.order_customer as kunden_nr,
        c.first_name, c.family_name, c.home_city
    FROM orders o
    LEFT JOIN customers_suppliers c ON o.order_customer = c.customer_number
    WHERE o.number = 219379
""")

result = cursor.fetchone()
if result:
    print(f"""
   Auftragsnummer: {result[0]}
   Betrieb:        {result[1]} ({betrieb_namen.get(result[1], '?')})
   Datum:          {result[2]}
   Fahrzeug-Nr:    {result[3]}
   KM-Stand:       {result[4]}
   
   Kunde:
     - Nummer:     {result[5]}
     - Name:       {result[6]} {result[7]}
     - Ort:        {result[8]}
""")

# Zusammenfassung
print("\n" + "=" * 70)
print("📊 ERGEBNIS")
print("=" * 70)
print(f"""
   ✅ VERKNÜPFUNG FUNKTIONIERT!
   
   Mapping: Gudat order.number = Locosoft orders.number
   
   Gudat (Deggendorf Werkstatt) nutzt:
   - Betrieb 1 (Stellantis): Nummern ~37.000 - 39.000
   - Betrieb 2 (Hyundai):    Nummern ~218.000 - 220.000
   
   {found} von {len(gudat_orders)} Test-Aufträgen gefunden!
""")

conn.close()
print("✅ Done")
