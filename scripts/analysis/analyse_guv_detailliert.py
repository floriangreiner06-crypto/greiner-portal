#!/usr/bin/env python3
"""
GUV-DETAILANALYSE FÜR BWA-VERGLEICH
====================================
Analysiert EXAKT die GuV-Konten (70-89) und findet fehlende Beträge.

WICHTIG: Auf dem SERVER ausführen!
Pfad: /opt/greiner-portal/scripts/analysis/analyse_guv_detailliert.py
"""

import sqlite3
import os
from datetime import datetime

# ============================================================================
# KONFIGURATION
# ============================================================================

BASE_DIR = '/opt/greiner-portal'
DB_PATH = os.path.join(BASE_DIR, 'data/greiner_controlling.db')
ANALYSIS_PERIOD_START = '2025-09-01'
ANALYSIS_PERIOD_END = '2025-10-31'

# BWA-Soll-Werte
BWA_UMSATZ_SOLL = 5823055
BWA_KOSTEN_SOLL = 5991331

# ============================================================================
# 1. GUV-KONTEN DETAILLIERT ANALYSIEREN
# ============================================================================

def analyse_guv_konten_detailliert():
    """Analysiert alle GuV-Konten (70-89) im Detail."""
    
    print("=" * 120)
    print("📊 SCHRITT 1: GUV-KONTEN (70-89) DETAILLIERT")
    print("=" * 120)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ========================================================================
    # UMSÄTZE (70-79)
    # ========================================================================
    
    print("\n" + "=" * 120)
    print("💰 UMSATZ-KONTEN (70-79)")
    print("=" * 120)
    
    cursor.execute("""
        SELECT 
            nominal_account,
            ROUND(SUM(CASE 
                WHEN debit_credit = 'S' THEN -amount 
                WHEN debit_credit = 'H' THEN amount 
            END), 2) as umsatz,
            COUNT(*) as anzahl,
            MIN(accounting_date) as erste,
            MAX(accounting_date) as letzte
        FROM fibu_buchungen
        WHERE accounting_date >= ?
          AND accounting_date <= ?
          AND nominal_account BETWEEN 700000 AND 799999
        GROUP BY nominal_account
        HAVING ABS(umsatz) > 100
        ORDER BY nominal_account
    """, (ANALYSIS_PERIOD_START, ANALYSIS_PERIOD_END))
    
    umsatz_konten = cursor.fetchall()
    
    print(f"\n📋 {len(umsatz_konten)} Umsatz-Konten gefunden:")
    print("\n" + "-" * 120)
    print(f"{'Konto':<10} | {'Umsatz (H-S)':<20} | {'Buchungen':<10} | {'Erste':<12} | {'Letzte':<12}")
    print("-" * 120)
    
    gesamt_umsatz = 0
    umsatz_70 = 0
    umsatz_71 = 0
    umsatz_72 = 0
    umsatz_73 = 0
    umsatz_74 = 0
    umsatz_75_79 = 0
    
    for konto, umsatz, anzahl, erste, letzte in umsatz_konten:
        print(f"{konto:<10} | {umsatz:>18,.2f} € | {anzahl:>10} | {erste:<12} | {letzte:<12}")
        gesamt_umsatz += umsatz
        
        # Gruppierung nach Bereich
        if 700000 <= konto < 710000:
            umsatz_70 += umsatz
        elif 710000 <= konto < 720000:
            umsatz_71 += umsatz
        elif 720000 <= konto < 730000:
            umsatz_72 += umsatz
        elif 730000 <= konto < 740000:
            umsatz_73 += umsatz
        elif 740000 <= konto < 750000:
            umsatz_74 += umsatz
        else:
            umsatz_75_79 += umsatz
    
    print("-" * 120)
    print(f"{'GESAMT UMSÄTZE (70-79)':<10} | {gesamt_umsatz:>18,.2f} € | {sum(a[2] for a in umsatz_konten):>10}")
    print("-" * 120)
    
    print("\n📊 UMSATZ-BEREICHE:")
    print(f"  70xxxx: {umsatz_70:>15,.2f} €")
    print(f"  71xxxx: {umsatz_71:>15,.2f} €")
    print(f"  72xxxx: {umsatz_72:>15,.2f} €")
    print(f"  73xxxx: {umsatz_73:>15,.2f} €")
    print(f"  74xxxx: {umsatz_74:>15,.2f} €")
    print(f"  75-79:  {umsatz_75_79:>15,.2f} €")
    print(f"  {'─'*25}")
    print(f"  GESAMT: {gesamt_umsatz:>15,.2f} €")
    
    print("\n🎯 BWA-VERGLEICH UMSÄTZE:")
    print(f"  BWA Soll:     {BWA_UMSATZ_SOLL:>15,.2f} €")
    print(f"  GuV Ist:      {gesamt_umsatz:>15,.2f} €")
    differenz_umsatz = gesamt_umsatz - BWA_UMSATZ_SOLL
    print(f"  Differenz:    {differenz_umsatz:>15,.2f} € {'✅' if abs(differenz_umsatz) < 1000 else '❌ FEHLEN!'}")
    
    # ========================================================================
    # KOSTEN (80-89)
    # ========================================================================
    
    print("\n" + "=" * 120)
    print("💸 KOSTEN-KONTEN (80-89)")
    print("=" * 120)
    
    cursor.execute("""
        SELECT 
            nominal_account,
            ROUND(SUM(CASE 
                WHEN debit_credit = 'S' THEN amount 
                WHEN debit_credit = 'H' THEN -amount 
            END), 2) as kosten,
            COUNT(*) as anzahl,
            MIN(accounting_date) as erste,
            MAX(accounting_date) as letzte
        FROM fibu_buchungen
        WHERE accounting_date >= ?
          AND accounting_date <= ?
          AND nominal_account BETWEEN 800000 AND 899999
        GROUP BY nominal_account
        HAVING ABS(kosten) > 100
        ORDER BY nominal_account
    """, (ANALYSIS_PERIOD_START, ANALYSIS_PERIOD_END))
    
    kosten_konten = cursor.fetchall()
    
    print(f"\n📋 {len(kosten_konten)} Kosten-Konten gefunden:")
    print("\n" + "-" * 120)
    print(f"{'Konto':<10} | {'Kosten (S-H)':<20} | {'Buchungen':<10} | {'Erste':<12} | {'Letzte':<12}")
    print("-" * 120)
    
    gesamt_kosten = 0
    kosten_80 = 0
    kosten_81 = 0
    kosten_82 = 0
    kosten_83 = 0
    kosten_84 = 0
    kosten_85_89 = 0
    
    for konto, kosten, anzahl, erste, letzte in kosten_konten:
        print(f"{konto:<10} | {kosten:>18,.2f} € | {anzahl:>10} | {erste:<12} | {letzte:<12}")
        gesamt_kosten += kosten
        
        # Gruppierung nach Bereich
        if 800000 <= konto < 810000:
            kosten_80 += kosten
        elif 810000 <= konto < 820000:
            kosten_81 += kosten
        elif 820000 <= konto < 830000:
            kosten_82 += kosten
        elif 830000 <= konto < 840000:
            kosten_83 += kosten
        elif 840000 <= konto < 850000:
            kosten_84 += kosten
        else:
            kosten_85_89 += kosten
    
    print("-" * 120)
    print(f"{'GESAMT KOSTEN (80-89)':<10} | {gesamt_kosten:>18,.2f} € | {sum(a[2] for a in kosten_konten):>10}")
    print("-" * 120)
    
    print("\n📊 KOSTEN-BEREICHE:")
    print(f"  80xxxx: {kosten_80:>15,.2f} €")
    print(f"  81xxxx: {kosten_81:>15,.2f} €")
    print(f"  82xxxx: {kosten_82:>15,.2f} €")
    print(f"  83xxxx: {kosten_83:>15,.2f} €")
    print(f"  84xxxx: {kosten_84:>15,.2f} €")
    print(f"  85-89:  {kosten_85_89:>15,.2f} €")
    print(f"  {'─'*25}")
    print(f"  GESAMT: {gesamt_kosten:>15,.2f} €")
    
    print("\n🎯 BWA-VERGLEICH KOSTEN:")
    print(f"  BWA Soll:     {BWA_KOSTEN_SOLL:>15,.2f} €")
    print(f"  GuV Ist:      {gesamt_kosten:>15,.2f} €")
    differenz_kosten = gesamt_kosten - BWA_KOSTEN_SOLL
    print(f"  Differenz:    {differenz_kosten:>15,.2f} € {'✅' if abs(differenz_kosten) < 1000 else '❌ FEHLEN!'}")
    
    conn.close()
    
    return gesamt_umsatz, gesamt_kosten, differenz_umsatz, differenz_kosten


# ============================================================================
# 2. BILANZ-KONTEN BUCHUNGSTEXT-ANALYSE
# ============================================================================

def analyse_bilanz_konten_buchungstexte():
    """Analysiert Buchungstexte der verdächtigen Bilanz-Konten."""
    
    print("\n" + "=" * 120)
    print("🔍 SCHRITT 2: BILANZ-KONTEN BUCHUNGSTEXT-ANALYSE")
    print("=" * 120)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    verdaechtige_konten = [
        (313201, "NW Leapmotor B10", 249547),
        (310101, "NW Corsa", 138484),
        (313101, "NW Leapmotor T03", 112579),
        (172001, "Lagerwagenfinanz. Sant.B. HYU", 256614),
        (310801, "NW Zafira", 62746),
        (311201, "NW Frontera", 23437),
    ]
    
    for konto, bezeichnung, erwarteter_betrag in verdaechtige_konten:
        print(f"\n{'='*120}")
        print(f"📄 KONTO {konto} - {bezeichnung} (Netto-Soll: ~{erwarteter_betrag:,.0f} €)")
        print(f"{'='*120}")
        
        # Buchungen anzeigen
        cursor.execute("""
            SELECT 
                accounting_date,
                debit_credit,
                amount,
                posting_text,
                document_number
            FROM fibu_buchungen
            WHERE accounting_date >= ?
              AND accounting_date <= ?
              AND nominal_account = ?
            ORDER BY accounting_date, document_number
            LIMIT 20
        """, (ANALYSIS_PERIOD_START, ANALYSIS_PERIOD_END, konto))
        
        buchungen = cursor.fetchall()
        
        if buchungen:
            print(f"\n📋 Erste {min(len(buchungen), 20)} Buchungen:")
            print("-" * 120)
            print(f"{'Datum':<12} | {'S/H':<5} | {'Betrag':<15} | {'Buchungstext':<60} | Beleg")
            print("-" * 120)
            
            soll_summe = 0
            haben_summe = 0
            
            for datum, sh, betrag, text, beleg in buchungen[:20]:
                print(f"{datum:<12} | {sh:<5} | {betrag:>13,.2f} € | {text[:60]:<60} | {beleg}")
                
                if sh == 'S':
                    soll_summe += betrag
                else:
                    haben_summe += betrag
            
            print("-" * 120)
            print(f"{'SOLL-Summe':<12} | {'S':<5} | {soll_summe:>13,.2f} €")
            print(f"{'HABEN-Summe':<12} | {'H':<5} | {haben_summe:>13,.2f} €")
            print(f"{'NETTO (S-H)':<12} |       | {soll_summe - haben_summe:>13,.2f} €")
            print("-" * 120)
            
            # Häufigste Buchungstexte
            cursor.execute("""
                SELECT 
                    posting_text,
                    COUNT(*) as anzahl,
                    ROUND(SUM(CASE WHEN debit_credit = 'S' THEN amount ELSE -amount END), 2) as netto
                FROM fibu_buchungen
                WHERE accounting_date >= ?
                  AND accounting_date <= ?
                  AND nominal_account = ?
                GROUP BY posting_text
                ORDER BY anzahl DESC
                LIMIT 5
            """, (ANALYSIS_PERIOD_START, ANALYSIS_PERIOD_END, konto))
            
            haeufige_texte = cursor.fetchall()
            
            if len(haeufige_texte) > 1:
                print("\n📊 Häufigste Buchungstexte:")
                for text, anzahl, netto in haeufige_texte:
                    print(f"  {anzahl:>3}x | {netto:>13,.2f} € | {text[:80]}")
        else:
            print("  ℹ️  Keine Buchungen in diesem Zeitraum")
    
    conn.close()


# ============================================================================
# 3. GEGENBUCHUNGEN FINDEN
# ============================================================================

def analyse_gegenbuchungen():
    """Analysiert wohin die Bilanz-Konten gebucht werden."""
    
    print("\n" + "=" * 120)
    print("🔄 SCHRITT 3: GEGENBUCHUNGEN-ANALYSE")
    print("=" * 120)
    print("\nFür jedes 31xxxx Konto: Wohin wird gebucht? (Gegen-Konten)")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    verdaechtige_konten = [313201, 310101, 313101, 172001, 310801, 311201]
    
    for konto in verdaechtige_konten:
        # Finde alle Belegnummern für dieses Konto
        cursor.execute("""
            SELECT DISTINCT document_number
            FROM fibu_buchungen
            WHERE accounting_date >= ?
              AND accounting_date <= ?
              AND nominal_account = ?
            LIMIT 10
        """, (ANALYSIS_PERIOD_START, ANALYSIS_PERIOD_END, konto))
        
        belege = [row[0] for row in cursor.fetchall()]
        
        if belege:
            print(f"\n📄 Konto {konto} - Beispiel-Belege:")
            
            for beleg in belege[:3]:  # Erste 3 Belege
                cursor.execute("""
                    SELECT 
                        nominal_account,
                        debit_credit,
                        amount,
                        posting_text
                    FROM fibu_buchungen
                    WHERE document_number = ?
                      AND accounting_date >= ?
                      AND accounting_date <= ?
                    ORDER BY position_in_document
                """, (beleg, ANALYSIS_PERIOD_START, ANALYSIS_PERIOD_END))
                
                beleg_buchungen = cursor.fetchall()
                
                print(f"\n  Beleg {beleg}:")
                for kto, sh, betrag, text in beleg_buchungen:
                    marker = "  ← UNSER KONTO" if kto == konto else "  → GEGENKONTO"
                    print(f"    {kto:<10} {sh} {betrag:>13,.2f} € | {text[:50]:<50} {marker}")
    
    conn.close()


# ============================================================================
# 4. ZUSAMMENFASSUNG & EMPFEHLUNG
# ============================================================================

def generate_final_recommendation(diff_umsatz, diff_kosten):
    """Generiert finale Empfehlung basierend auf Analyse."""
    
    print("\n" + "=" * 120)
    print("💡 SCHRITT 4: ZUSAMMENFASSUNG & EMPFEHLUNG")
    print("=" * 120)
    
    print(f"""
📊 GEFUNDENE DIFFERENZEN:

Umsätze (70-79):
  BWA Soll:  {BWA_UMSATZ_SOLL:>12,.2f} €
  GuV Ist:   {BWA_UMSATZ_SOLL + diff_umsatz:>12,.2f} €
  Differenz: {diff_umsatz:>12,.2f} € {'❌ FEHLEN!' if diff_umsatz < -1000 else '✅'}

Kosten (80-89):
  BWA Soll:  {BWA_KOSTEN_SOLL:>12,.2f} €
  GuV Ist:   {BWA_KOSTEN_SOLL + diff_kosten:>12,.2f} €
  Differenz: {diff_kosten:>12,.2f} € {'❌ FEHLEN!' if diff_kosten < -1000 else '✅'}

═══════════════════════════════════════════════════════════════════════════

🎯 ANALYSE-ERGEBNIS:

Die 31xxxx Konten (Neuwagen) sind BILANZ-Konten:
→ Sie sind KEINE GuV-Konten!
→ Sie erscheinen NICHT in der BWA!
→ Die Differenz liegt IN DEN GUV-KONTEN selbst!

💡 MÖGLICHE URSACHEN:

1. FEHLENDE GUV-KONTEN
   → Es fehlen komplette 70-79 oder 80-89 Konten in der FIBU
   → Bestimmte Umsatz-/Kostenarten werden nicht gebucht

2. BUCHUNGSPERIODE
   → Sep+Okt Buchungen unvollständig?
   → Nachbuchungen im November für Sep/Okt?

3. BWA-BERECHNUNGSLOGIK
   → GlobalCube rechnet anders (Stichtag vs. Periode)
   → Andere Konten-Zuordnung als Standard-SKR

🚀 NÄCHSTE SCHRITTE:

A) GuV-Konten mit GlobalCube vergleichen:
   → Screenshot: Welche 70-79 Konten sind in BWA?
   → Screenshot: Welche 80-89 Konten sind in BWA?
   → Detaillierter Soll-Ist-Vergleich pro Konto!

B) FIBU-Vollständigkeit prüfen:
   → Sind alle Buchungen aus Sep+Okt importiert?
   → Nachbuchungen im November für Sep/Okt?

C) Test-Import mit anderen Konten-Regeln:
   → Vielleicht andere SKR-Zuordnung?
   → Vielleicht andere Berechnungslogik?
""")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Hauptprogramm."""
    
    print("\n" + "=" * 120)
    print("🔍 GUV-DETAILANALYSE FÜR BWA-VERGLEICH")
    print("=" * 120)
    print(f"\nDatum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Zeitraum: {ANALYSIS_PERIOD_START} bis {ANALYSIS_PERIOD_END}")
    print(f"\nBWA-Soll-Werte:")
    print(f"  Umsätze: {BWA_UMSATZ_SOLL:>12,.2f} €")
    print(f"  Kosten:  {BWA_KOSTEN_SOLL:>12,.2f} €")
    print(f"  Ergebnis:{(BWA_UMSATZ_SOLL - BWA_KOSTEN_SOLL):>12,.2f} €")
    
    # 1. GuV-Konten detailliert
    umsatz, kosten, diff_u, diff_k = analyse_guv_konten_detailliert()
    
    # 2. Bilanz-Konten Buchungstexte
    analyse_bilanz_konten_buchungstexte()
    
    # 3. Gegenbuchungen
    analyse_gegenbuchungen()
    
    # 4. Zusammenfassung
    generate_final_recommendation(diff_u, diff_k)
    
    print("\n" + "=" * 120)
    print("✅ DETAILANALYSE ABGESCHLOSSEN")
    print("=" * 120)
    print()


if __name__ == '__main__':
    main()
