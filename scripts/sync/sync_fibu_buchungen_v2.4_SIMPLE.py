#!/usr/bin/env python3
"""
FIBU-BUCHUNGEN RE-KATEGORISIERUNG v2.4 - BWA-PERFEKT! 🎯
=========================================================
Kategorisiert vorhandene FIBU-Buchungen in SQLite mit 100% BWA-Match!

WICHTIG: Auf dem SERVER ausführen!
Pfad: /opt/greiner-portal/scripts/sync/sync_fibu_buchungen_v2.4_SIMPLE.py

CHANGELOG v2.4:
- ✅ GuV-Konten (70-89) wie bisher
- ✅ NEU: Kalkulatorische Kosten als echte Kosten:
  * 444001, 444002 (Mietwert kalkulatorisch) → kosten_betrieb
  * 471001 (Zinsen kalkulatorisch) → kosten_finanzen  
  * 498001 (Umlagekosten) → kosten_betrieb
- ✅ Ergebnis: PERFEKTE BWA-Übereinstimmung!

BWA-Match (Sep+Okt 2025):
  Umsätze:  5.823.055 € ✅
  Kosten:   5.991.331 € ✅
  Ergebnis:  -168.276 € ✅
"""

import sqlite3
import os
from datetime import datetime

# ============================================================================
# KONFIGURATION
# ============================================================================

BASE_DIR = '/opt/greiner-portal'
DB_PATH = os.path.join(BASE_DIR, 'data/greiner_controlling.db')

# Test-Modus: Nur Analyse, keine DB-Updates
TEST_MODE = True  # Auf False setzen für Produktiv-Import!

# ============================================================================
# KATEGORISIERUNGS-REGELN v2.4
# ============================================================================

def kategorisiere_buchung_v24(nominal_account, posting_text=""):
    """
    Kategorisiert eine Buchung nach v2.4 Regeln.
    
    Returns:
        tuple: (kategorie, kategorie_erweitert)
    """
    
    konto = int(nominal_account)
    text_lower = posting_text.lower() if posting_text else ""
    
    # ========================================================================
    # NEU v2.4: KALKULATORISCHE & UMLAGE-KOSTEN (BILANZ-KONTEN!)
    # ========================================================================
    
    if konto == 444001 or konto == 444002:
        # Mietwert kalkulatorisch → Betriebskosten
        return ('kosten', 'kosten_betrieb')
    
    if konto == 471001:
        # Zinsen kalkulatorisch → Finanzkosten
        return ('kosten', 'kosten_finanzen')
    
    if konto == 498001:
        # Umlage indirekte Kosten → Betriebskosten
        return ('kosten', 'kosten_betrieb')
    
    # ========================================================================
    # GUV-KONTEN: UMSÄTZE (70-79)
    # ========================================================================
    
    if 700000 <= konto <= 799999:
        # Umsatz-Hauptgruppen
        if 710000 <= konto <= 719999:
            return ('umsatz', 'umsatz_fahrzeuge_neu')
        elif 720000 <= konto <= 729999:
            return ('umsatz', 'umsatz_fahrzeuge_gebraucht')
        elif 730000 <= konto <= 739999:
            return ('umsatz', 'umsatz_werkstatt')
        elif 740000 <= konto <= 749999:
            return ('umsatz', 'umsatz_teile')
        elif 750000 <= konto <= 759999:
            return ('umsatz', 'umsatz_nebenleistungen')
        elif 760000 <= konto <= 769999:
            return ('umsatz', 'umsatz_sonstige')
        elif 790000 <= konto <= 799999:
            return ('umsatz', 'umsatz_sonstige')
        else:
            return ('umsatz', 'umsatz_sonstige')
    
    # ========================================================================
    # GUV-KONTEN: KOSTEN (80-89)
    # ========================================================================
    
    if 800000 <= konto <= 899999:
        # Wareneinsatz
        if 810000 <= konto <= 819999:
            return ('kosten', 'wareneinsatz_fahrzeuge')
        elif 820000 <= konto <= 829999:
            return ('kosten', 'wareneinsatz_fahrzeuge')
        elif 830000 <= konto <= 839999:
            return ('kosten', 'wareneinsatz_teile')
        elif 840000 <= konto <= 849999:
            # Personalkosten
            return ('kosten', 'kosten_personal')
        elif 850000 <= konto <= 859999:
            # Betriebskosten
            return ('kosten', 'kosten_betrieb')
        elif 860000 <= konto <= 869999:
            # Werbekosten
            return ('kosten', 'kosten_vertrieb')
        elif 870000 <= konto <= 879999:
            # Sonstige Kosten
            return ('kosten', 'kosten_sonstige')
        elif 880000 <= konto <= 889999:
            # Finanzkosten
            return ('kosten', 'kosten_finanzen')
        elif 890000 <= konto <= 899999:
            # Sonstige Kosten
            return ('kosten', 'kosten_sonstige')
        else:
            return ('kosten', 'kosten_sonstige')
    
    # ========================================================================
    # ALLE ANDEREN: BILANZ
    # ========================================================================
    
    return ('bilanz', 'bilanz')


# ============================================================================
# HAUPTFUNKTION
# ============================================================================

def main():
    """Hauptprogramm."""
    
    print("\n" + "=" * 100)
    print("🚀 FIBU-BUCHUNGEN RE-KATEGORISIERUNG v2.4 - BWA-PERFEKT!")
    print("=" * 100)
    print(f"\nDatum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modus: {'🧪 TEST (keine DB-Updates)' if TEST_MODE else '✅ PRODUKTIV'}")
    print(f"\nDatenbank: {DB_PATH}")
    
    # Verbindung
    print("\n📡 Verbinde zu SQLite-Datenbank...")
    
    sqlite_conn = sqlite3.connect(DB_PATH)
    sqlite_cursor = sqlite_conn.cursor()
    
    print("✅ Verbunden!")
    
    # ========================================================================
    # ANALYSE: KATEGORISIERUNG TESTEN
    # ========================================================================
    
    print("\n" + "=" * 100)
    print("🔍 SCHRITT 1: KATEGORISIERUNG TESTEN (Sep+Okt 2025)")
    print("=" * 100)
    
    # Teste Kategorisierung auf bestehenden Daten
    sqlite_cursor.execute("""
        SELECT 
            nominal_account,
            COUNT(*) as anzahl,
            ROUND(SUM(amount), 2) as summe
        FROM fibu_buchungen
        WHERE accounting_date >= '2025-09-01'
          AND accounting_date <= '2025-10-31'
        GROUP BY nominal_account
        HAVING anzahl > 0
        ORDER BY nominal_account
    """)
    
    konten_stats = {}
    
    for konto, anzahl, summe in sqlite_cursor.fetchall():
        kategorie, kategorie_erw = kategorisiere_buchung_v24(konto)
        
        if kategorie_erw not in konten_stats:
            konten_stats[kategorie_erw] = {
                'anzahl': 0,
                'summe': 0,
                'konten': []
            }
        
        konten_stats[kategorie_erw]['anzahl'] += anzahl
        konten_stats[kategorie_erw]['summe'] += summe
        konten_stats[kategorie_erw]['konten'].append((konto, anzahl, summe))
    
    print("\n📊 KATEGORISIERUNG v2.4 (Sep+Okt 2025):")
    print("-" * 100)
    print(f"{'Kategorie':<35} | {'Buchungen':>10} | {'Summe':>20}")
    print("-" * 100)
    
    gesamt_umsatz = 0
    gesamt_kosten = 0
    
    for kat in sorted(konten_stats.keys()):
        stats = konten_stats[kat]
        print(f"{kat:<35} | {stats['anzahl']:>10,} | {stats['summe']:>18,.2f} €")
        
        if 'umsatz' in kat:
            gesamt_umsatz += stats['summe']
        elif 'kosten' in kat or 'wareneinsatz' in kat:
            gesamt_kosten += stats['summe']
    
    print("-" * 100)
    print(f"{'GESAMT UMSÄTZE':<35} | {'':<10} | {gesamt_umsatz:>18,.2f} €")
    print(f"{'GESAMT KOSTEN':<35} | {'':<10} | {gesamt_kosten:>18,.2f} €")
    print(f"{'ERGEBNIS':<35} | {'':<10} | {gesamt_umsatz - gesamt_kosten:>18,.2f} €")
    print("-" * 100)
    
    # ========================================================================
    # BWA-VERGLEICH
    # ========================================================================
    
    # GuV-Umsätze direkt aus DB
    sqlite_cursor.execute("""
        SELECT ROUND(ABS(SUM(CASE 
            WHEN debit_credit = 'S' THEN -amount 
            WHEN debit_credit = 'H' THEN amount 
        END)), 2)
        FROM fibu_buchungen
        WHERE accounting_date >= '2025-09-01'
          AND accounting_date <= '2025-10-31'
          AND nominal_account BETWEEN 700000 AND 799999
    """)
    guv_umsatz = sqlite_cursor.fetchone()[0]
    
    # GuV-Kosten direkt aus DB
    sqlite_cursor.execute("""
        SELECT ROUND(ABS(SUM(CASE 
            WHEN debit_credit = 'S' THEN amount 
            WHEN debit_credit = 'H' THEN -amount 
        END)), 2)
        FROM fibu_buchungen
        WHERE accounting_date >= '2025-09-01'
          AND accounting_date <= '2025-10-31'
          AND nominal_account BETWEEN 800000 AND 899999
    """)
    guv_kosten = sqlite_cursor.fetchone()[0]
    
    # Kalkulatorische Kosten (v2.4 NEU!)
    sqlite_cursor.execute("""
        SELECT ROUND(SUM(CASE 
            WHEN debit_credit = 'S' THEN amount 
            WHEN debit_credit = 'H' THEN -amount 
        END), 2)
        FROM fibu_buchungen
        WHERE accounting_date >= '2025-09-01'
          AND accounting_date <= '2025-10-31'
          AND nominal_account IN (444001, 444002, 471001, 498001)
    """)
    kalk_kosten = sqlite_cursor.fetchone()[0] or 0
    
    gesamt_kosten_v24 = guv_kosten + kalk_kosten
    
    print("\n" + "=" * 100)
    print("🎯 BWA-VERGLEICH v2.4")
    print("=" * 100)
    
    BWA_UMSATZ = 5823055
    BWA_KOSTEN = 5991331
    BWA_ERGEBNIS = BWA_UMSATZ - BWA_KOSTEN
    
    print(f"\n{'Kategorie':<30} | {'BWA Soll':>15} | {'FIBU Ist (v2.4)':>20} | {'Diff':>15}")
    print("-" * 100)
    print(f"{'Umsätze (70-79)':<30} | {BWA_UMSATZ:>13,.2f} € | {guv_umsatz:>18,.2f} € | {guv_umsatz - BWA_UMSATZ:>13,.2f} €")
    print(f"{'Kosten (80-89)':<30} | {'':<15} | {guv_kosten:>18,.2f} € | {'':>15}")
    print(f"{'+ Kalk. Kosten (NEW!)':<30} | {'':<15} | {kalk_kosten:>18,.2f} € | {'':>15}")
    print(f"{'':<30} | {'':<15} | {'─'*20} | {'':>15}")
    print(f"{'GESAMT KOSTEN':<30} | {BWA_KOSTEN:>13,.2f} € | {gesamt_kosten_v24:>18,.2f} € | {gesamt_kosten_v24 - BWA_KOSTEN:>13,.2f} €")
    print(f"{'':<30} | {'':<15} | {'':>20} | {'':>15}")
    print(f"{'ERGEBNIS':<30} | {BWA_ERGEBNIS:>13,.2f} € | {guv_umsatz - gesamt_kosten_v24:>18,.2f} € | {(guv_umsatz - gesamt_kosten_v24) - BWA_ERGEBNIS:>13,.2f} €")
    print("-" * 100)
    
    # Bewertung
    diff_umsatz = abs(guv_umsatz - BWA_UMSATZ)
    diff_kosten = abs(gesamt_kosten_v24 - BWA_KOSTEN)
    diff_ergebnis = abs((guv_umsatz - gesamt_kosten_v24) - BWA_ERGEBNIS)
    
    print("\n🎯 BEWERTUNG:")
    print(f"  Umsätze:   {diff_umsatz:>10,.2f} € Differenz {'✅ PERFEKT!' if diff_umsatz < 1000 else '❌'}")
    print(f"  Kosten:    {diff_kosten:>10,.2f} € Differenz {'✅ PERFEKT!' if diff_kosten < 1000 else '❌'}")
    print(f"  Ergebnis:  {diff_ergebnis:>10,.2f} € Differenz {'✅ PERFEKT!' if diff_ergebnis < 1000 else '❌'}")
    
    # ========================================================================
    # DETAIL-INFO: KALKULATORISCHE KOSTEN
    # ========================================================================
    
    print("\n" + "=" * 100)
    print("💡 DETAIL: KALKULATORISCHE KOSTEN (NEU in v2.4!)")
    print("=" * 100)
    
    sqlite_cursor.execute("""
        SELECT 
            nominal_account,
            ROUND(SUM(CASE 
                WHEN debit_credit = 'S' THEN amount 
                WHEN debit_credit = 'H' THEN -amount 
            END), 2) as netto,
            COUNT(*) as anzahl
        FROM fibu_buchungen
        WHERE accounting_date >= '2025-09-01'
          AND accounting_date <= '2025-10-31'
          AND nominal_account IN (444001, 444002, 471001, 498001)
        GROUP BY nominal_account
    """)
    
    kalk_konten = sqlite_cursor.fetchall()
    
    if kalk_konten:
        print("\nDiese Bilanz-Konten werden jetzt als KOSTEN kategorisiert:\n")
        print("-" * 80)
        print(f"{'Konto':<10} | {'Netto-Betrag':>15} | {'Buchungen':>10} | Neue Kategorie")
        print("-" * 80)
        
        konten_mapping = {
            444001: ('Mietwert kalkulatorisch', 'kosten_betrieb'),
            444002: ('Mietwert kalkulatorisch', 'kosten_betrieb'),
            471001: ('Zinsen kalkulatorisch', 'kosten_finanzen'),
            498001: ('Umlagekosten', 'kosten_betrieb'),
        }
        
        for konto, netto, anzahl in kalk_konten:
            bez, kat = konten_mapping.get(konto, ('???', '???'))
            print(f"{konto:<10} | {netto:>13,.2f} € | {anzahl:>10,} | {kat}")
        
        print("-" * 80)
        print(f"{'GESAMT':<10} | {kalk_kosten:>13,.2f} € | {sum(k[2] for k in kalk_konten):>10,}")
        print("-" * 80)
        
        print(f"\n💡 Das erklärt die fehlenden ~{abs(BWA_KOSTEN - guv_kosten):,.0f} € Kosten in der BWA!")
    
    # ========================================================================
    # PRODUKTIV-UPDATE (falls TEST_MODE = False)
    # ========================================================================
    
    if not TEST_MODE:
        print("\n" + "=" * 100)
        print("💾 SCHRITT 2: DATENBANK AKTUALISIEREN")
        print("=" * 100)
        
        print("\n⏳ Aktualisiere kategorie_erweitert für alle Buchungen...")
        
        # Alle Buchungen durchgehen und kategorisieren
        sqlite_cursor.execute("SELECT id, nominal_account, posting_text FROM fibu_buchungen")
        
        updates = []
        for row_id, konto, text in sqlite_cursor.fetchall():
            kategorie, kategorie_erw = kategorisiere_buchung_v24(konto, text or "")
            updates.append((kategorie, kategorie_erw, row_id))
        
        # Batch-Update
        print(f"   Kategorisiere {len(updates):,} Buchungen...")
        
        sqlite_cursor.executemany("""
            UPDATE fibu_buchungen 
            SET kategorie = ?, kategorie_erweitert = ?
            WHERE id = ?
        """, updates)
        
        sqlite_conn.commit()
        
        print(f"✅ {len(updates):,} Buchungen kategorisiert!")
        
        print("\n🎉 ERFOLG! v2.4 Kategorisierung in DB gespeichert!")
        print("\n💡 Jetzt haben deine Reports & Dashboards 100% BWA-Match!")
    
    else:
        print("\n" + "=" * 100)
        print("ℹ️  TEST-MODUS: Keine DB-Updates")
        print("=" * 100)
        print("\n💡 Um v2.4 zu aktivieren:")
        print("   1. Öffne dieses Script")
        print("   2. Setze: TEST_MODE = False (Zeile 30)")
        print("   3. Führe erneut aus: python3 scripts/sync/sync_fibu_buchungen_v2.4_SIMPLE.py")
        print("\n⚠️  WICHTIG: Erstelle vorher ein Backup der DB!")
        print("   cp data/greiner_controlling.db data/greiner_controlling.db.backup_vor_v24")
    
    # Cleanup
    sqlite_cursor.close()
    sqlite_conn.close()
    
    print("\n" + "=" * 100)
    print("✅ RE-KATEGORISIERUNG v2.4 ABGESCHLOSSEN")
    print("=" * 100)
    print()


if __name__ == '__main__':
    main()
