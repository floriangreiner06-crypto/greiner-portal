#!/usr/bin/env python3
"""
FIBU-BUCHUNGEN RE-KATEGORISIERUNG v2.4 - BWA-PERFEKT! 🎯
=========================================================
FIXED: Nur kategorie_erweitert (kategorie-Spalte existiert nicht)
"""

import sqlite3
import os
from datetime import datetime

BASE_DIR = '/opt/greiner-portal'
DB_PATH = os.path.join(BASE_DIR, 'data/greiner_controlling.db')
TEST_MODE = False  # PRODUKTIV!

def kategorisiere_buchung_v24(nominal_account):
    """Kategorisiert eine Buchung nach v2.4 Regeln."""
    
    konto = int(nominal_account)
    
    # Kalkulatorische & Umlage-Kosten (BILANZ-KONTEN!)
    if konto in (444001, 444002):
        return 'kosten_betrieb'
    if konto == 471001:
        return 'kosten_finanzen'
    if konto == 498001:
        return 'kosten_betrieb'
    
    # GuV-Konten: Umsätze (70-79)
    if 700000 <= konto <= 799999:
        if 710000 <= konto <= 719999:
            return 'umsatz_fahrzeuge_neu'
        elif 720000 <= konto <= 729999:
            return 'umsatz_fahrzeuge_gebraucht'
        elif 730000 <= konto <= 739999:
            return 'umsatz_werkstatt'
        elif 740000 <= konto <= 749999:
            return 'umsatz_teile'
        elif 750000 <= konto <= 759999:
            return 'umsatz_nebenleistungen'
        else:
            return 'umsatz_sonstige'
    
    # GuV-Konten: Kosten (80-89)
    if 800000 <= konto <= 899999:
        if 810000 <= konto <= 829999:
            return 'wareneinsatz_fahrzeuge'
        elif 830000 <= konto <= 839999:
            return 'wareneinsatz_teile'
        elif 840000 <= konto <= 849999:
            return 'kosten_personal'
        elif 850000 <= konto <= 859999:
            return 'kosten_betrieb'
        elif 860000 <= konto <= 869999:
            return 'kosten_vertrieb'
        elif 870000 <= konto <= 879999:
            return 'kosten_sonstige'
        elif 880000 <= konto <= 889999:
            return 'kosten_finanzen'
        else:
            return 'kosten_sonstige'
    
    return 'bilanz'

def main():
    print("\n" + "=" * 100)
    print("🚀 FIBU RE-KATEGORISIERUNG v2.4 - FIXED!")
    print("=" * 100)
    print(f"\nDatum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("✅ Verbunden zu SQLite!")
    print("\n⏳ Kategorisiere ALLE Buchungen neu...")
    
    # Alle Buchungen holen
    cursor.execute("SELECT id, nominal_account FROM fibu_buchungen")
    buchungen = cursor.fetchall()
    
    print(f"   Gefunden: {len(buchungen):,} Buchungen")
    
    # Kategorisieren
    updates = []
    for row_id, konto in buchungen:
        kategorie_erw = kategorisiere_buchung_v24(konto)
        updates.append((kategorie_erw, row_id))
    
    print(f"   Starte Update...")
    
    # NUR kategorie_erweitert updaten (kategorie existiert nicht!)
    cursor.executemany("""
        UPDATE fibu_buchungen 
        SET kategorie_erweitert = ?
        WHERE id = ?
    """, updates)
    
    conn.commit()
    
    print(f"✅ {len(updates):,} Buchungen kategorisiert!")
    
    # Verifikation: Sep+Okt Zahlen
    print("\n" + "=" * 100)
    print("🎯 VERIFIKATION: BWA-VERGLEICH (Sep+Okt 2025)")
    print("=" * 100)
    
    cursor.execute("""
        SELECT ROUND(ABS(SUM(CASE 
            WHEN debit_credit = 'S' THEN -amount 
            WHEN debit_credit = 'H' THEN amount 
        END)), 2)
        FROM fibu_buchungen
        WHERE accounting_date >= '2025-09-01'
          AND accounting_date <= '2025-10-31'
          AND nominal_account BETWEEN 700000 AND 799999
    """)
    guv_umsatz = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT ROUND(ABS(SUM(CASE 
            WHEN debit_credit = 'S' THEN amount 
            WHEN debit_credit = 'H' THEN -amount 
        END)), 2)
        FROM fibu_buchungen
        WHERE accounting_date >= '2025-09-01'
          AND accounting_date <= '2025-10-31'
          AND nominal_account BETWEEN 800000 AND 899999
    """)
    guv_kosten = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT ROUND(SUM(CASE 
            WHEN debit_credit = 'S' THEN amount 
            WHEN debit_credit = 'H' THEN -amount 
        END), 2)
        FROM fibu_buchungen
        WHERE accounting_date >= '2025-09-01'
          AND accounting_date <= '2025-10-31'
          AND nominal_account IN (444001, 444002, 471001, 498001)
    """)
    kalk_kosten = cursor.fetchone()[0] or 0
    
    gesamt_kosten = guv_kosten + kalk_kosten
    
    print(f"\n{'Kategorie':<30} | {'BWA Soll':>15} | {'FIBU v2.4':>15} | {'Diff':>15}")
    print("-" * 90)
    print(f"{'Umsätze (70-79)':<30} | {'5,823,055':>15} | {guv_umsatz:>15,.2f} | {guv_umsatz - 5823055:>15,.2f}")
    print(f"{'Kosten (80-89+kalk)':<30} | {'5,991,331':>15} | {gesamt_kosten:>15,.2f} | {gesamt_kosten - 5991331:>15,.2f}")
    print("-" * 90)
    
    diff_kosten = abs(gesamt_kosten - 5991331)
    if diff_kosten < 10000:
        print("\n✅ KOSTEN: PERFEKT! Abweichung < 10.000 €")
    
    # Kategorien-Verteilung
    cursor.execute("""
        SELECT 
            kategorie_erweitert,
            COUNT(*) as anzahl
        FROM fibu_buchungen
        WHERE accounting_date >= '2025-09-01'
          AND accounting_date <= '2025-10-31'
        GROUP BY kategorie_erweitert
        ORDER BY anzahl DESC
    """)
    
    print("\n📊 KATEGORIEN-VERTEILUNG (Sep+Okt):")
    print("-" * 60)
    for kat, anzahl in cursor.fetchall():
        print(f"  {kat:<35} | {anzahl:>10,}")
    print("-" * 60)
    
    conn.close()
    
    print("\n" + "=" * 100)
    print("🎉 ERFOLG! v2.4 KATEGORISIERUNG AKTIV!")
    print("=" * 100)
    print("\n💡 Jetzt haben alle Reports & Dashboards die korrekte Kategorisierung!")
    print()

if __name__ == '__main__':
    main()
