#!/usr/bin/env python3
import sqlite3
from datetime import datetime

DB_PATH = "/opt/greiner-portal/data/greiner_controlling.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("="*100)
print("📊 NOVEMBER-STATUS - ALLE KONTEN")
print("="*100)
print(f"Stand: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")

c.execute("""
    SELECT 
        k.kontoname,
        b.bank_name,
        COUNT(t.id) as total,
        SUM(CASE WHEN t.buchungsdatum >= '2025-11-01' THEN 1 ELSE 0 END) as nov,
        SUM(t.betrag) as saldo,
        MAX(t.buchungsdatum) as letztes,
        MIN(CASE WHEN t.buchungsdatum >= '2025-11-01' THEN t.buchungsdatum END) as nov_start,
        MAX(CASE WHEN t.buchungsdatum >= '2025-11-01' THEN t.buchungsdatum END) as nov_ende
    FROM konten k
    LEFT JOIN banken b ON k.bank_id = b.id
    LEFT JOIN transaktionen t ON k.id = t.konto_id
    WHERE k.aktiv = 1
    GROUP BY k.id
    ORDER BY b.bank_name, k.kontoname
""")

banks = {}
gesamt_nov = 0
gesamt_trans = 0
gesamt_saldo = 0.0
ohne_nov = 0

for row in c.fetchall():
    name, bank, total, nov, saldo, letztes, nov_start, nov_ende = row
    bank = bank or "Unbekannt"
    
    if bank not in banks:
        banks[bank] = []
    
    banks[bank].append({
        'name': name,
        'nov': nov or 0,
        'saldo': saldo or 0.0,
        'letztes': letztes,
        'nov_start': nov_start,
        'nov_ende': nov_ende
    })
    
    gesamt_trans += total
    gesamt_nov += (nov or 0)
    gesamt_saldo += (saldo or 0.0)
    if not nov or nov == 0:
        ohne_nov += 1

for bank in sorted(banks.keys()):
    print(f"\n🏦 {bank}")
    print("-"*100)
    
    for konto in banks[bank]:
        name = konto['name'][:30]
        if konto['nov'] > 0:
            print(f"✅ {name:<30} | {konto['saldo']:>15,.2f} EUR | {konto['nov']} Trans. | {konto['nov_start']} bis {konto['nov_ende']}")
        else:
            print(f"⏳ {name:<30} | {konto['saldo']:>15,.2f} EUR | Noch keine November-Daten (Stand: {konto['letztes'] or 'N/A'})")

print(f"\n{'='*100}")
print("📈 GESAMT-STATISTIK")
print("="*100)
print(f"Transaktionen gesamt:     {gesamt_trans:,}")
print(f"November-Transaktionen:   {gesamt_nov:,}")
print(f"Gesamt-Saldo:             {gesamt_saldo:,.2f} EUR")

if ohne_nov > 0:
    print(f"\n⏳ KONTEN OHNE NOVEMBER-DATEN: {ohne_nov}")
else:
    print(f"\n✅ ALLE KONTEN HABEN NOVEMBER-DATEN!")

print("="*100)

conn.close()
