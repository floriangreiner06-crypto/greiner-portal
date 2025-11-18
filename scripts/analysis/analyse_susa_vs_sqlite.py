#!/usr/bin/env python3
"""
SUSA vs SQLite VERGLEICH
=========================
Vergleicht die SUSA (Wirtschaftsjahr 09/2024-08/2025) mit SQLite-Daten
um herauszufinden welche 81xxxx/82xxxx Konten als Wareneinsatz kategorisiert werden sollen.
"""

import sqlite3

print("=" * 100)
print("🔍 SUSA vs SQLite VERGLEICH (Wirtschaftsjahr 09/2024 - 08/2025)")
print("=" * 100)
print()

# SUSA-Daten (manuell aus der hochgeladenen Datei übertragen)
# Nur die relevanten 81xxxx und 82xxxx Konten mit ihren Salden
SUSA_KONTEN = {
    # 810xxx - Neuwagen VE
    '810101': 18848.23,
    '810111': 83263.79,
    '810112': 104183.46,
    '810122': 16593.70,
    '810132': 22672.29,
    '810141': 55361.13,
    '810151': 18067.81,
    '810601': -512.46,
    '810611': 116994.70,
    '810621': 24300.50,
    '810631': 22388.73,
    '810641': 170021.71,
    '810642': 20606.76,
    '810651': 84604.65,
    '810851': 31602.53,
    '810911': 181249.53,
    '810912': 30575.62,
    '810931': 65834.53,
    '810941': 62007.58,
    '810942': 24243.70,
    '810951': 111942.11,
    
    # 811xxx - Neuwagen VE
    '811201': 22402.53,
    '811202': 20756.31,
    '811211': 24906.24,
    '811212': 25492.92,
    '811222': 21788.07,
    '811241': 41868.91,
    '811721': 62304.37,
    '811741': 181304.19,
    '811751': 77151.56,
    '811901': 35294.12,
    '811911': 920.17,
    '811951': 60305.05,
    '811962': 30150.02,
    
    # 812xxx - Neuwagen VE
    '812011': 28225.17,
    '812021': 57907.67,
    '812031': 54228.13,
    '812041': 177799.24,
    '812051': 60146.02,
    '812121': 116426.91,
    '812131': 59867.04,
    '812141': 318390.75,
    '812151': 117769.52,
    
    # 813xxx - Neuwagen VE
    '813011': 66899.16,
    '813101': 16666.93,
    '813111': 116613.48,
    
    # 817xxx - SONSTIGE ERLÖSE (NICHT Wareneinsatz!)
    '817001': 18119.51,
    '817051': 275000.00,
    '817101': 56432.22,
    '817102': 149.99,
    '817501': 13397.90,
    '817502': 2116.05,
    '817901': 19922.06,
    
    # 818xxx - Vorführwagen VE
    '818001': 2570801.96,
    '818002': 496285.63,
    
    # 820xxx - Gebrauchtwagen VE
    '820201': 85252.09,
    '820202': 27647.06,
    '820301': 673916.53,
    '820302': 254759.71,
    '820351': 122498.71,
    '820352': 40790.16,
    
    # 821xxx - Gebrauchtwagen VE
    '821201': 1400718.49,
    '821202': 1837650.73,
    '821301': 101770.38,
    '821351': 26436.65,
    
    # 823xxx - Gebrauchtwagen VE
    '823101': 1385624.32,
    '823102': 190901.48,
    
    # 824xxx - Gebrauchtwagen VE
    '824201': 697932.94,
    '824202': 119242.85,
    
    # 827xxx - SONSTIGE ERLÖSE (NICHT Wareneinsatz!)
    '827001': 14894.34,
    '827002': -5972.83,
    '827011': 59410.66,
    '827012': 923.00,
    '827051': 275000.00,
    '827101': -29809.05,
    '827102': -13325.94,
    '827201': -46.18,
    '827501': 10019.96,
    '827502': 3372.20,
}

print(f"📊 SUSA-Daten geladen: {len(SUSA_KONTEN)} Konten")
print()

# SQLite abfragen
print("💾 Lade SQLite-Daten (09/2024 - 08/2025)...")
conn = sqlite3.connect('data/greiner_controlling.db')
c = conn.cursor()

c.execute("""
    SELECT 
        nominal_account,
        ROUND(SUM(amount), 2) as summe
    FROM fibu_buchungen
    WHERE accounting_date >= '2024-09-01'
      AND accounting_date <= '2025-08-31'
      AND nominal_account IN ({})
    GROUP BY nominal_account
    ORDER BY nominal_account
""".format(','.join(['?' for _ in SUSA_KONTEN.keys()])), list(SUSA_KONTEN.keys()))

sqlite_konten = {}
for konto, summe in c.fetchall():
    sqlite_konten[konto] = summe

print(f"✅ SQLite geladen: {len(sqlite_konten)} Konten")
print()

# VERGLEICH
print("=" * 120)
print("📊 VERGLEICH SUSA vs SQLite (Wirtschaftsjahr 09/2024-08/2025)")
print("=" * 120)
print(f"{'Konto':<10} | {'SUSA':>20} | {'SQLite':>20} | {'Diff %':>10} | {'Match':<8}")
print("-" * 120)

matches = 0
total_diff = 0

for konto in sorted(SUSA_KONTEN.keys()):
    susa_val = SUSA_KONTEN[konto]
    sqlite_val = sqlite_konten.get(konto, 0)
    
    if susa_val != 0:
        diff_percent = abs((sqlite_val - susa_val) / susa_val * 100)
    else:
        diff_percent = 0 if sqlite_val == 0 else 100
    
    match = "✅" if diff_percent < 5 else "⚠️"
    if diff_percent < 5:
        matches += 1
    
    total_diff += abs(susa_val - sqlite_val)
    
    print(f"{konto:<10} | {susa_val:>20,.2f} | {sqlite_val:>20,.2f} | {diff_percent:>9.2f}% | {match}")

print("-" * 120)
print(f"MATCHES: {matches}/{len(SUSA_KONTEN)} Konten stimmen überein (< 5% Abweichung)")
print(f"TOTAL DIFF: {total_diff:,.2f} €")
print()

# GRUPPIERUNG
print("=" * 100)
print("📊 GRUPPIERUNG: WELCHE KONTEN SIND WARENEINSATZ?")
print("=" * 100)

gruppen = {
    '810-816': [],
    '817': [],
    '818': [],
    '820-826': [],
    '827': [],
}

for konto in SUSA_KONTEN.keys():
    if '810000' <= konto <= '816999':
        gruppen['810-816'].append(konto)
    elif konto.startswith('817'):
        gruppen['817'].append(konto)
    elif konto.startswith('818'):
        gruppen['818'].append(konto)
    elif '820000' <= konto <= '826999':
        gruppen['820-826'].append(konto)
    elif konto.startswith('827'):
        gruppen['827'].append(konto)

for gruppe, konten in gruppen.items():
    susa_sum = sum(SUSA_KONTEN.get(k, 0) for k in konten)
    sqlite_sum = sum(sqlite_konten.get(k, 0) for k in konten)
    
    if gruppe in ['817', '827']:
        typ = "❌ SONSTIGE ERLÖSE (NICHT Wareneinsatz!)"
    else:
        typ = "✅ WARENEINSATZ"
    
    print(f"{gruppe:>10} | {len(konten):>3} Konten | SUSA: {susa_sum:>15,.2f} | SQLite: {sqlite_sum:>15,.2f} | {typ}")

print()

# FAZIT
print("=" * 100)
print("💡 FAZIT FÜR KATEGORISIERUNG")
print("=" * 100)
print()
print("✅ ALS WARENEINSATZ KATEGORISIEREN:")
print("   - 810000-816999 (Neuwagen VE)")
print("   - 818000-818999 (Vorführwagen VE)")
print("   - 820000-826999 (Gebrauchtwagen VE)")
print()
print("❌ NICHT als Wareneinsatz (sind Erlöse/Bilanz):")
print("   - 817xxx (Sonstige Verkaufserlöse NW, Provisionen)")
print("   - 827xxx (Sonstige Verkaufserlöse GW, GIVIT)")
print()

# Berechne erwarteten Wareneinsatz
wareneinsatz_susa = (
    sum(SUSA_KONTEN.get(k, 0) for k in SUSA_KONTEN.keys() if '810000' <= k <= '816999') +
    sum(SUSA_KONTEN.get(k, 0) for k in SUSA_KONTEN.keys() if k.startswith('818')) +
    sum(SUSA_KONTEN.get(k, 0) for k in SUSA_KONTEN.keys() if '820000' <= k <= '826999')
)

wareneinsatz_sqlite = (
    sum(sqlite_konten.get(k, 0) for k in sqlite_konten.keys() if '810000' <= k <= '816999') +
    sum(sqlite_konten.get(k, 0) for k in sqlite_konten.keys() if k.startswith('818')) +
    sum(sqlite_konten.get(k, 0) for k in sqlite_konten.keys() if '820000' <= k <= '826999')
)

print(f"📊 ERWARTETER WARENEINSATZ FAHRZEUGE (Wirtschaftsjahr):")
print(f"   SUSA:   {wareneinsatz_susa:>15,.2f} €")
print(f"   SQLite: {wareneinsatz_sqlite:>15,.2f} €")
print()

conn.close()
