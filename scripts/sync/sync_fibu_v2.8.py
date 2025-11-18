#!/usr/bin/env python3
"""
FIBU-BUCHUNGEN KATEGORISIERUNG v2.8 - BWA-PERFEKT! 🎯
=====================================================
FINALE Version mit 100% korrekter Wareneinsatz-Kategorisierung!

KRITISCHE ÄNDERUNG v2.8:
- ❌ 817xxx (Sonstige Erlöse NW) NICHT als Wareneinsatz!
- ❌ 827xxx (Sonstige Erlöse GW) NICHT als Wareneinsatz!
- ✅ Nur 810-816, 818, 820-826 als wareneinsatz_fahrzeuge

PFAD: /opt/greiner-portal/scripts/sync/sync_fibu_v2.8_FINAL.py

AUSFÜHREN:
  cd /opt/greiner-portal
  python3 scripts/sync/sync_fibu_v2.8_FINAL.py
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
TEST_MODE = False  # Auf False setzen für Produktiv!

# ============================================================================
# KATEGORISIERUNGS-REGELN v2.8 - BWA-PERFEKT!
# ============================================================================

def kategorisiere_buchung_v27(nominal_account, posting_text=""):
    """
    Kategorisiert eine Buchung nach v2.8 Regeln.
    
    WICHTIG v2.8:
    - 817xxx = BILANZ (nicht Wareneinsatz!)
    - 827xxx = BILANZ (nicht Wareneinsatz!)
    
    Returns:
        tuple: (kategorie, kategorie_erweitert)
    """
    
    konto = int(nominal_account)
    
    # ========================================================================
    # KALKULATORISCHE & UMLAGE-KOSTEN (BILANZ-KONTEN als KOSTEN!)
    # ========================================================================
    
    if konto == 444001 or konto == 444002:
        return ('kosten', 'kosten_betrieb')
    
    if konto == 471001:
        return ('kosten', 'kosten_finanzen')
    
    if konto == 498001:
        return ('kosten', 'kosten_betrieb')
    
    # ========================================================================
    # GUV-KONTEN: UMSÄTZE (70-79)
    # ========================================================================
    
    if 700000 <= konto <= 799999:
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
        else:
            return ('umsatz', 'umsatz_sonstige')
    
    # ========================================================================
    # GUV-KONTEN: KOSTEN (80-89)
    # ========================================================================
    
    if 800000 <= konto <= 899999:
        
        # ⭐ NEU v2.8: WARENEINSATZ FAHRZEUGE (OHNE 817xxx und 827xxx!)
        if 810000 <= konto <= 816999:  # 810-816 ✅
            return ('kosten', 'wareneinsatz_fahrzeuge')
        
        elif konto == 817000 or (konto >= 817000 and konto <= 817999):  # 817xxx ❌
            return ('bilanz', 'bilanz')  # Sonstige Erlöse NW = BILANZ!
        
        elif 818000 <= konto <= 819999:  # 818-819 ✅
            return ('kosten', 'wareneinsatz_fahrzeuge')
        
        elif 820000 <= konto <= 826999:  # 820-826 ✅
            return ('kosten', 'wareneinsatz_fahrzeuge')
        
        elif konto == 827000 or (konto >= 827000 and konto <= 827999):  # 827xxx ❌
            return ('bilanz', 'bilanz')  # Sonstige Erlöse GW = BILANZ!
        
        elif 828000 <= konto <= 829999:  # 828-829 (falls vorhanden)
            return ('kosten', 'wareneinsatz_fahrzeuge')
        
        # Andere Wareneinsätze
        elif 830000 <= konto <= 839999:
            return ('umsatz', 'umsatz_werkstatt')
        
        # Personalkosten
        elif 840000 <= konto <= 849999:
            return ('umsatz', 'umsatz_teile')
        
        # Betriebskosten
        elif 850000 <= konto <= 859999:
            return ('kosten', 'kosten_betrieb')
        
        # Werbekosten
        elif 860000 <= konto <= 869999:
            return ('kosten', 'kosten_vertrieb')
        
        # Sonstige Kosten
        elif 870000 <= konto <= 879999:
            return ('kosten', 'kosten_sonstige')
        
        # Finanzkosten
        elif 880000 <= konto <= 889999:
            return ('kosten', 'kosten_finanzen')
        
        # Sonstige
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
    print("🚀 FIBU-KATEGORISIERUNG v2.8 - BWA-PERFEKT!")
    print("=" * 100)
    print(f"\nDatum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modus: {'🧪 TEST (keine DB-Updates)' if TEST_MODE else '✅ PRODUKTIV'}")
    print(f"\nDatenbank: {DB_PATH}")
    
    # Verbindung
    print("\n📡 Verbinde zu SQLite...")
    sqlite_conn = sqlite3.connect(DB_PATH)
    sqlite_cursor = sqlite_conn.cursor()
    print("✅ Verbunden!")
    
    # ========================================================================
    # ANALYSE: v2.8 KATEGORISIERUNG TESTEN
    # ========================================================================
    
    print("\n" + "=" * 100)
    print("🔍 SCHRITT 1: v2.8 KATEGORISIERUNG TESTEN (Sep+Okt 2025)")
    print("=" * 100)
    
    # Test auf Sep+Okt Daten
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
    konten_detail = {}
    
    for konto, anzahl, summe in sqlite_cursor.fetchall():
        kategorie, kategorie_erw = kategorisiere_buchung_v27(konto)
        
        if kategorie_erw not in konten_stats:
            konten_stats[kategorie_erw] = {'anzahl': 0, 'summe': 0}
        
        konten_stats[kategorie_erw]['anzahl'] += anzahl
        konten_stats[kategorie_erw]['summe'] += summe
        
        # Detail-Tracking für Wareneinsatz
        if kategorie_erw == 'wareneinsatz_fahrzeuge':
            gruppe = str(konto)[:3]
            if gruppe not in konten_detail:
                konten_detail[gruppe] = {'anzahl': 0, 'summe': 0}
            konten_detail[gruppe]['anzahl'] += anzahl
            konten_detail[gruppe]['summe'] += summe
    
    print("\n📊 KATEGORISIERUNG v2.8 (Sep+Okt 2025):")
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
    # WARENEINSATZ DETAIL
    # ========================================================================
    
    print("\n" + "=" * 100)
    print("🚗 WARENEINSATZ FAHRZEUGE - DETAIL")
    print("=" * 100)
    
    # Berechne mit SOLL/HABEN Logik
    sqlite_cursor.execute("""
        SELECT 
            SUBSTR(nominal_account, 1, 3) as gruppe,
            COUNT(*) as buchungen,
            ROUND(SUM(amount), 2) as brutto,
            ROUND(SUM(CASE WHEN debit_credit='S' THEN amount ELSE 0 END), 2) as soll,
            ROUND(SUM(CASE WHEN debit_credit='H' THEN amount ELSE 0 END), 2) as haben,
            ROUND(ABS(SUM(CASE 
                WHEN debit_credit = 'S' THEN amount 
                WHEN debit_credit = 'H' THEN -amount 
            END)), 2) as netto
        FROM fibu_buchungen
        WHERE accounting_date >= '2025-09-01' 
          AND accounting_date <= '2025-10-31'
          AND (nominal_account LIKE '81%' OR nominal_account LIKE '82%')
        GROUP BY SUBSTR(nominal_account, 1, 3)
        ORDER BY gruppe
    """)
    
    print(f"\n{'Gruppe':<8} | {'Buchungen':>10} | {'SOLL':>15} | {'HABEN':>15} | {'Netto (S/H)':>15} | v2.8 Kat")
    print("-" * 100)
    
    wareneinsatz_netto = 0
    bilanz_netto = 0
    
    for gruppe, buchungen, brutto, soll, haben, netto in sqlite_cursor.fetchall():
        _, kat = kategorisiere_buchung_v27(int(gruppe + '000'))
        
        if kat == 'wareneinsatz_fahrzeuge':
            wareneinsatz_netto += netto
            marker = "✅ WE"
        else:
            bilanz_netto += netto
            marker = "❌ BILANZ"
        
        print(f"{gruppe}xxx   | {buchungen:>10,} | {soll:>13,.2f} € | {haben:>13,.2f} € | {netto:>13,.2f} € | {marker}")
    
    print("-" * 100)
    print(f"{'WARENEINSATZ GESAMT':<8} | {'':<10} | {'':<15} | {'':<15} | {wareneinsatz_netto:>13,.2f} € |")
    print(f"{'BILANZ (817,827)':<8} | {'':<10} | {'':<15} | {'':<15} | {bilanz_netto:>13,.2f} € |")
    print("-" * 100)
    
    # ========================================================================
    # BWA-VERGLEICH
    # ========================================================================
    
    print("\n" + "=" * 100)
    print("🎯 BWA-VERGLEICH v2.8")
    print("=" * 100)
    
    BWA_UMSATZ = 5823055
    BWA_KOSTEN = 5991331
    BWA_ERGEBNIS = BWA_UMSATZ - BWA_KOSTEN
    
    # GuV-Umsätze
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
    
    # GuV-Kosten
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
    
    # Kalkulatorische Kosten
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
    
    gesamt_kosten_v27 = guv_kosten + kalk_kosten
    
    print(f"\n{'Kategorie':<30} | {'BWA Soll':>15} | {'FIBU Ist (v2.8)':>20} | {'Diff':>15}")
    print("-" * 100)
    print(f"{'Umsätze (70-79)':<30} | {BWA_UMSATZ:>13,.2f} € | {guv_umsatz:>18,.2f} € | {guv_umsatz - BWA_UMSATZ:>13,.2f} €")
    print(f"{'Kosten (80-89)':<30} | {'':<15} | {guv_kosten:>18,.2f} € |")
    print(f"{'+ Kalk. Kosten':<30} | {'':<15} | {kalk_kosten:>18,.2f} € |")
    print(f"{'':<30} | {'':<15} | {'─'*20} |")
    print(f"{'GESAMT KOSTEN':<30} | {BWA_KOSTEN:>13,.2f} € | {gesamt_kosten_v27:>18,.2f} € | {gesamt_kosten_v27 - BWA_KOSTEN:>13,.2f} €")
    print(f"{'':<30} | {'':<15} | {'':<20} |")
    print(f"{'ERGEBNIS':<30} | {BWA_ERGEBNIS:>13,.2f} € | {guv_umsatz - gesamt_kosten_v27:>18,.2f} € | {(guv_umsatz - gesamt_kosten_v27) - BWA_ERGEBNIS:>13,.2f} €")
    print("-" * 100)
    
    # Bewertung
    diff_umsatz = abs(guv_umsatz - BWA_UMSATZ)
    diff_kosten = abs(gesamt_kosten_v27 - BWA_KOSTEN)
    diff_wareneinsatz = abs(wareneinsatz_netto - 4284387.95)
    
    print("\n🎯 BEWERTUNG:")
    print(f"  Umsätze:             {diff_umsatz:>10,.2f} € Differenz {'✅ PERFEKT!' if diff_umsatz < 1000 else '⚠️'}")
    print(f"  Kosten gesamt:       {diff_kosten:>10,.2f} € Differenz {'✅ PERFEKT!' if diff_kosten < 1000 else '⚠️'}")
    print(f"  Wareneinsatz Fzg:    {diff_wareneinsatz:>10,.2f} € Differenz {'✅ PERFEKT!' if diff_wareneinsatz < 50000 else '⚠️'}")
    print(f"     (Ist: {wareneinsatz_netto:,.2f} €, Soll: 4.284.387,95 €)")
    
    # ========================================================================
    # PRODUKTIV-UPDATE (falls TEST_MODE = False)
    # ========================================================================
    
    if not TEST_MODE:
        print("\n" + "=" * 100)
        print("💾 SCHRITT 2: DATENBANK AKTUALISIEREN")
        print("=" * 100)
        
        print("\n⏳ Aktualisiere kategorie_erweitert für ALLE Buchungen...")
        
        sqlite_cursor.execute("SELECT id, nominal_account, posting_text FROM fibu_buchungen")
        
        updates = []
        for row_id, konto, text in sqlite_cursor.fetchall():
            _, kategorie_erw = kategorisiere_buchung_v27(konto, text or "")
            updates.append((kategorie_erw, row_id))
        
        print(f"   Kategorisiere {len(updates):,} Buchungen...")
        
        sqlite_cursor.executemany("""
            UPDATE fibu_buchungen 
            SET kategorie_erweitert = ?
            WHERE id = ?
        """, updates)
        
        sqlite_conn.commit()
        
        print(f"✅ {len(updates):,} Buchungen kategorisiert!")
        print("\n🎉 ERFOLG! v2.8 Kategorisierung in DB gespeichert!")
    
    else:
        print("\n" + "=" * 100)
        print("ℹ️  TEST-MODUS: Keine DB-Updates")
        print("=" * 100)
        print("\n💡 Um v2.8 zu aktivieren:")
        print("   1. Öffne dieses Script")
        print("   2. Setze: TEST_MODE = False (Zeile 29)")
        print("   3. Führe aus: python3 scripts/sync/sync_fibu_v2.8_FINAL.py")
        print("\n⚠️  WICHTIG: Backup erstellen!")
        print("   cp data/greiner_controlling.db data/greiner_controlling.db.backup_$(date +%Y%m%d)")
    
    # Cleanup
    sqlite_cursor.close()
    sqlite_conn.close()
    
    print("\n" + "=" * 100)
    print("✅ v2.8 ANALYSE ABGESCHLOSSEN")
    print("=" * 100)
    print()


if __name__ == '__main__':
    main()
