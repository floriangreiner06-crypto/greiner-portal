#!/usr/bin/env python3
"""
KONTENPLAN SYSTEMATISCHE ANALYSE - FÜR SERVER
==============================================
Analysiert Kontenplan und FIBU-Buchungen um die fehlenden 181k € Kosten zu finden.

WICHTIG: Dieses Script auf dem SERVER ausführen!
Pfad: /opt/greiner-portal/scripts/analysis/analyse_kontenplan_systematisch.py

Verwendung:
    cd /opt/greiner-portal
    python3 scripts/analysis/analyse_kontenplan_systematisch.py
"""

import csv
import sqlite3
import os
from collections import defaultdict
from datetime import datetime

# ============================================================================
# KONFIGURATION
# ============================================================================

# Server-Pfade
BASE_DIR = '/opt/greiner-portal'
KONTENPLAN_PATH = os.path.join(BASE_DIR, 'L394PR-ALTERNATIVKONTEN-OPEL-01-001.csv')
DB_PATH = os.path.join(BASE_DIR, 'data/greiner_controlling.db')
ANALYSIS_PERIOD_START = '2025-09-01'
ANALYSIS_PERIOD_END = '2025-10-31'

# ============================================================================
# 1. KONTENPLAN LADEN
# ============================================================================

def load_kontenplan():
    """Lädt und analysiert den Kontenplan."""
    
    print("=" * 100)
    print("📋 SCHRITT 1: KONTENPLAN LADEN")
    print("=" * 100)
    
    if not os.path.exists(KONTENPLAN_PATH):
        print(f"❌ Kontenplan nicht gefunden: {KONTENPLAN_PATH}")
        print("💡 Bitte Datei hochladen oder Pfad anpassen!")
        return {}, {}
    
    konten = {}
    bereiche = defaultdict(list)
    
    with open(KONTENPLAN_PATH, 'r', encoding='latin1') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        for row in reader:
            kontonr = row['Kontonr EIGEN'].strip()
            bezeichnung = row['Kontobezeichnung (rein informativ!) EIGEN'].strip()
            
            if kontonr and kontonr != '-':
                try:
                    nr = int(kontonr)
                    konten[nr] = bezeichnung
                    
                    # Bereich ermitteln (erste 2 Ziffern)
                    bereich_key = str(nr)[:2]
                    bereiche[bereich_key].append({
                        'nr': nr,
                        'bezeichnung': bezeichnung
                    })
                except:
                    pass
    
    print(f"\n✅ {len(konten)} Konten geladen")
    
    # Wichtige Bereiche anzeigen
    wichtige = ['31', '32', '33', '41', '42', '43', '44', '45', '46', '47', '48', '49', '71', '72', '81', '82']
    print(f"\n📊 WICHTIGE KONTEN-BEREICHE:")
    for b in wichtige:
        if b in bereiche:
            print(f"  {b}xxxx: {len(bereiche[b]):4d} Konten")
    
    return konten, bereiche


# ============================================================================
# 2. FIBU-BUCHUNGEN ANALYSIEREN
# ============================================================================

def analyse_fibu_bilanzkonten(konten):
    """Analysiert Bilanz-Konten aus FIBU-Buchungen."""
    
    print("\n" + "=" * 100)
    print("💰 SCHRITT 2: BILANZ-KONTEN MIT NETTO-SOLL ANALYSIEREN")
    print("=" * 100)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Datenbank nicht gefunden: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Prüfe ob fibu_buchungen existiert
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='fibu_buchungen'
    """)
    
    if not cursor.fetchone():
        print("❌ Tabelle 'fibu_buchungen' nicht vorhanden!")
        conn.close()
        return
    
    print(f"\n✅ Analysiere Sep+Okt 2025 (Zeitraum: {ANALYSIS_PERIOD_START} - {ANALYSIS_PERIOD_END})")
    
    # Analyse: Alle Bilanz-Konten mit Netto-Soll > 1.000 €
    cursor.execute("""
        SELECT 
            nominal_account,
            ROUND(SUM(CASE 
                WHEN debit_credit = 'S' THEN amount 
                WHEN debit_credit = 'H' THEN -amount 
            END), 2) as netto_soll,
            COUNT(*) as anzahl_buchungen,
            kategorie_erweitert
        FROM fibu_buchungen
        WHERE accounting_date >= ?
          AND accounting_date <= ?
          AND kategorie_erweitert = 'bilanz'
        GROUP BY nominal_account, kategorie_erweitert
        HAVING ABS(netto_soll) > 1000
        ORDER BY netto_soll DESC
    """, (ANALYSIS_PERIOD_START, ANALYSIS_PERIOD_END))
    
    bilanz_konten = cursor.fetchall()
    
    print(f"\n📋 BILANZ-KONTEN MIT |NETTO-SOLL| > 1.000 € (Gesamt: {len(bilanz_konten)} Konten)")
    print("\n" + "-" * 110)
    print(f"{'Konto':<10} | {'Bezeichnung':<45} | {'Netto-Soll':<15} | {'Buchungen':<10} | Bereich")
    print("-" * 110)
    
    # Kategorisiere nach Bereichen
    konten_31 = []
    konten_32 = []
    konten_33 = []
    konten_17 = []
    konten_41_49 = []
    konten_15_19 = []
    konten_sonstige = []
    
    gesamt_netto = 0
    
    for konto, netto, anzahl, kategorie in bilanz_konten[:50]:  # Top 50
        bezeichnung = konten.get(konto, '???')
        bereich = str(konto)[:2]
        
        # Nur Soll-Seite (positive Netto)
        if netto > 1000:
            print(f"{konto:<10} | {bezeichnung[:45]:<45} | {netto:>13,.2f} € | {anzahl:>10} | {bereich}xxxx")
            gesamt_netto += netto
            
            # Kategorisiere
            if 310000 <= konto < 320000:
                konten_31.append((konto, bezeichnung, netto))
            elif 320000 <= konto < 330000:
                konten_32.append((konto, bezeichnung, netto))
            elif 330000 <= konto < 340000:
                konten_33.append((konto, bezeichnung, netto))
            elif 170000 <= konto < 180000:
                konten_17.append((konto, bezeichnung, netto))
            elif 410000 <= konto < 500000:
                konten_41_49.append((konto, bezeichnung, netto))
            elif 150000 <= konto < 200000:
                konten_15_19.append((konto, bezeichnung, netto))
            else:
                konten_sonstige.append((konto, bezeichnung, netto))
    
    print("-" * 110)
    print(f"{'GESAMT NETTO-SOLL (Top 50)':<57} | {gesamt_netto:>13,.2f} €")
    print("-" * 110)
    
    # Detaillierte Zusammenfassung
    print("\n" + "=" * 100)
    print("📊 ZUSAMMENFASSUNG NACH BEREICHEN (Sortiert nach Summe)")
    print("=" * 100)
    
    bereiche_summary = [
        ("31xxxx (Neuwagen)", konten_31),
        ("32xxxx (Gebrauchtwagen?)", konten_32),
        ("33xxxx (Sonstige Waren?)", konten_33),
        ("17xxxx (Finanzierung)", konten_17),
        ("41-49xxxx (Verbindlichkeiten)", konten_41_49),
        ("15-19xxxx (Forderungen)", konten_15_19),
        ("Sonstige", konten_sonstige),
    ]
    
    for name, konten_liste in bereiche_summary:
        if konten_liste:
            summe = sum(n for _, _, n in konten_liste)
            print(f"\n{'='*100}")
            print(f"🔍 {name}: {len(konten_liste)} Konten, Summe: {summe:,.2f} €")
            print(f"{'='*100}")
            
            for konto, bez, netto in sorted(konten_liste, key=lambda x: x[2], reverse=True):
                print(f"   {konto:<10} | {bez[:60]:<60} | {netto:>13,.2f} €")
    
    conn.close()
    
    return {
        '31': konten_31,
        '32': konten_32,
        '33': konten_33,
        '17': konten_17,
        '41-49': konten_41_49,
        '15-19': konten_15_19,
        'sonstige': konten_sonstige
    }


# ============================================================================
# 3. AKTUELLE v2.2 KATEGORISIERUNG PRÜFEN
# ============================================================================

def check_current_categorization():
    """Prüft die aktuelle v2.2 Kategorisierung."""
    
    print("\n" + "=" * 100)
    print("🔍 SCHRITT 3: AKTUELLE KATEGORISIERUNG PRÜFEN (v2.2)")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # GuV-Summen (70-89)
    cursor.execute("""
        SELECT 
            CASE 
                WHEN nominal_account BETWEEN 700000 AND 799999 THEN 'Umsätze (70-79)'
                WHEN nominal_account BETWEEN 800000 AND 899999 THEN 'Kosten (80-89)'
            END as bereich,
            ROUND(SUM(CASE 
                WHEN debit_credit = 'S' THEN -amount 
                WHEN debit_credit = 'H' THEN amount 
            END), 2) as betrag
        FROM fibu_buchungen
        WHERE accounting_date >= ?
          AND accounting_date <= ?
          AND nominal_account BETWEEN 700000 AND 899999
        GROUP BY bereich
    """, (ANALYSIS_PERIOD_START, ANALYSIS_PERIOD_END))
    
    guv_summen = cursor.fetchall()
    
    print("\n📊 GuV-KONTEN (70-89) - Sep+Okt 2025:")
    print("-" * 60)
    for bereich, betrag in guv_summen:
        print(f"{bereich:<30} | {betrag:>15,.2f} €")
    print("-" * 60)
    
    # Kategorisierung-Übersicht
    cursor.execute("""
        SELECT 
            kategorie_erweitert,
            COUNT(*) as anzahl,
            ROUND(SUM(amount), 2) as summe
        FROM fibu_buchungen
        WHERE accounting_date >= ?
          AND accounting_date <= ?
        GROUP BY kategorie_erweitert
        ORDER BY summe DESC
    """, (ANALYSIS_PERIOD_START, ANALYSIS_PERIOD_END))
    
    kategorien = cursor.fetchall()
    
    print("\n📋 KATEGORISIERUNG v2.2:")
    print("-" * 80)
    print(f"{'Kategorie':<35} | {'Anzahl':<10} | {'Summe':<20}")
    print("-" * 80)
    
    gesamt_umsatz = 0
    gesamt_kosten = 0
    
    for kat, anzahl, summe in kategorien:
        print(f"{kat:<35} | {anzahl:>10,} | {summe:>18,.2f} €")
        
        if 'umsatz' in kat:
            gesamt_umsatz += summe
        elif 'kosten' in kat or 'wareneinsatz' in kat:
            gesamt_kosten += summe
    
    print("-" * 80)
    print(f"{'GESAMT UMSÄTZE':<35} | {'':<10} | {gesamt_umsatz:>18,.2f} €")
    print(f"{'GESAMT KOSTEN':<35} | {'':<10} | {gesamt_kosten:>18,.2f} €")
    print(f"{'ERGEBNIS':<35} | {'':<10} | {gesamt_umsatz - gesamt_kosten:>18,.2f} €")
    print("-" * 80)
    
    print("\n🎯 BWA-VERGLEICH:")
    print(f"   Umsätze SOLL:  5.823.055 €")
    print(f"   Umsätze IST:   {gesamt_umsatz:,.2f} €")
    print(f"   Differenz:     {gesamt_umsatz - 5823055:,.2f} € {'✅' if abs(gesamt_umsatz - 5823055) < 1000 else '❌'}")
    print()
    print(f"   Kosten SOLL:   5.991.331 €")
    print(f"   Kosten IST:    {gesamt_kosten:,.2f} €")
    print(f"   Differenz:     {gesamt_kosten - 5991331:,.2f} € {'❌ FEHLEN!' if gesamt_kosten < 5991331 else ''}")
    
    conn.close()


# ============================================================================
# 4. EMPFEHLUNGEN FÜR v2.4
# ============================================================================

def generate_recommendations(bereiche_analyse):
    """Generiert konkrete Empfehlungen basierend auf Analyse."""
    
    print("\n" + "=" * 100)
    print("💡 SCHRITT 4: EMPFEHLUNGEN FÜR v2.4")
    print("=" * 100)
    
    summe_31 = sum(n for _, _, n in bereiche_analyse.get('31', []))
    summe_17 = sum(n for _, _, n in bereiche_analyse.get('17', []))
    summe_41_49 = sum(n for _, _, n in bereiche_analyse.get('41-49', []))
    
    print(f"""
📌 ANALYSE-ERGEBNIS:

31xxxx (Neuwagen):           {summe_31:>12,.2f} € ({len(bereiche_analyse.get('31', []))} Konten)
17xxxx (Finanzierung):       {summe_17:>12,.2f} € ({len(bereiche_analyse.get('17', []))} Konten)
41-49xxxx (Verbindlichk.):   {summe_41_49:>12,.2f} € ({len(bereiche_analyse.get('41-49', []))} Konten)
                             ──────────────
GESAMT:                      {summe_31 + summe_17 + summe_41_49:>12,.2f} €

🎯 PROBLEM: Wir brauchen nur 181k €, haben aber {summe_31 + summe_17:,.0f} € gefunden!

💡 MÖGLICHE LÖSUNGEN:

Option A: Nur BESTIMMTE 31xxxx Konten nehmen
   → Nicht alle, sondern nur die mit höchsten Beträgen
   → Test: Top 5-10 Konten = ca. 181k?

Option B: Andere Berechnungslogik
   → GlobalCube rechnet vielleicht mit Netto-Veränderung
   → Nicht absoluter Saldo, sondern Delta im Monat?

Option C: Kombination mit anderen Konten
   → 31xxxx teilweise + 17xxxx teilweise
   → Welche Kombination = 181k?

🚀 NÄCHSTER SCHRITT:

1. Screenshot von GlobalCube BWA Detail-Ansicht machen
   → "Wareneinsatz Fahrzeuge" → Welche Konten?
   
2. ODER: Test-Kategorisierungen entwickeln:
   → v2.4a: Top 5 31xxxx Konten
   → v2.4b: Top 10 31xxxx Konten
   → v2.4c: 31xxxx + 172001
   
3. Jeweils BWA-Vergleich machen bis wir die richtige Kombination haben!
""")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Hauptprogramm."""
    
    print("\n" + "=" * 100)
    print("🔍 KONTENPLAN SYSTEMATISCHE ANALYSE - BWA v2.4 ENTWICKLUNG")
    print("=" * 100)
    print(f"\nDatum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Zeitraum: {ANALYSIS_PERIOD_START} bis {ANALYSIS_PERIOD_END}")
    print(f"Ziel: Fehlende 181.127 € Kosten identifizieren!")
    print(f"\nServer-Pfade:")
    print(f"  Kontenplan: {KONTENPLAN_PATH}")
    print(f"  Datenbank:  {DB_PATH}")
    
    # 1. Kontenplan laden
    konten, bereiche = load_kontenplan()
    
    if not konten:
        print("\n❌ Abbruch wegen fehlendem Kontenplan!")
        return
    
    # 2. FIBU-Buchungen analysieren
    bereiche_analyse = analyse_fibu_bilanzkonten(konten)
    
    # 3. Aktuelle Kategorisierung prüfen
    check_current_categorization()
    
    # 4. Empfehlungen
    if bereiche_analyse:
        generate_recommendations(bereiche_analyse)
    
    print("\n" + "=" * 100)
    print("✅ ANALYSE ABGESCHLOSSEN")
    print("=" * 100)
    print()


if __name__ == '__main__':
    main()
