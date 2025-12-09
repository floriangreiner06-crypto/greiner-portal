#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Liquiditäts-Dashboard V2.2 - mit Kreditlinien & Bestandskonten
================================================================
Übersicht über aktuelle Kontostände, verfügbare Liquidität
und Einkaufsfinanzierung (Stellantis + Santander)

Author: Claude AI + Florian Greiner
Date: 2025-11-08
Version: 2.2 (Fix: Getrennte Anzeige Stellantis/Santander)
"""

import sqlite3
from datetime import datetime, timedelta

# ANSI Farben
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
BOLD = '\033[1m'
RESET = '\033[0m'

def format_currency(amount):
    """Formatiert Betrag mit Farbe"""
    if amount is None:
        return f"{0:>15,.2f} €"
    color = GREEN if amount >= 0 else RED
    return f"{color}{amount:>15,.2f} €{RESET}"

def format_percent(percent):
    """Formatiert Prozent mit Farbe"""
    if percent >= 80:
        color = RED
    elif percent >= 60:
        color = YELLOW
    else:
        color = GREEN
    return f"{color}{percent:>6.1f}%{RESET}"

def print_header(title):
    """Druckt schönen Header"""
    print("\n" + "="*120)
    print(f"{BOLD}{CYAN}{title:^120}{RESET}")
    print("="*120)

def get_aktuelle_salden_mit_limits(conn):
    """Holt aktuelle Salden aller aktiven Konten inkl. Kreditlinien"""
    c = conn.cursor()
    c.execute("""
        SELECT
            b.bank_name,
            k.id,
            k.kontoname,
            k.iban,
            k.kreditlinie,
            (SELECT saldo_nach_buchung
             FROM transaktionen
             WHERE konto_id = k.id
             ORDER BY buchungsdatum DESC, id DESC
             LIMIT 1) as aktueller_saldo,
            (SELECT MAX(buchungsdatum)
             FROM transaktionen
             WHERE konto_id = k.id) as letztes_datum
        FROM konten k
        JOIN banken b ON k.bank_id = b.id
        WHERE k.aktiv = 1
        ORDER BY b.bank_name, k.kontoname
    """)
    return c.fetchall()

def get_november_stats(conn):
    """November-Statistiken"""
    c = conn.cursor()

    c.execute("""
        SELECT
            k.kontoname,
            COUNT(*) as anzahl,
            MIN(t.buchungsdatum) as von,
            MAX(t.buchungsdatum) as bis
        FROM transaktionen t
        JOIN konten k ON t.konto_id = k.id
        WHERE t.buchungsdatum >= '2025-11-01'
        GROUP BY k.id
        ORDER BY anzahl DESC
    """)
    nov_konten = c.fetchall()

    c.execute("""
        SELECT
            COUNT(*) as gesamt,
            SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END) as einnahmen,
            SUM(CASE WHEN betrag < 0 THEN betrag ELSE 0 END) as ausgaben
        FROM transaktionen
        WHERE buchungsdatum >= '2025-11-01'
    """)
    nov_gesamt = c.fetchone()

    return nov_konten, nov_gesamt

def get_einkaufsfinanzierung(conn):
    """Einkaufsfinanzierung - gruppiert nach Institut (Stellantis & Santander)"""
    c = conn.cursor()
    
    # Institute abrufen
    c.execute("""
        SELECT DISTINCT finanzinstitut 
        FROM fahrzeugfinanzierungen 
        ORDER BY finanzinstitut
    """)
    institute = [row[0] for row in c.fetchall()]
    
    ergebnis = {}
    
    for institut in institute:
        # Gesamt-Statistik pro Institut
        c.execute("""
            SELECT
                COUNT(*) as anzahl_fahrzeuge,
                SUM(aktueller_saldo) as gesamt_finanzierung,
                SUM(original_betrag) as gesamt_original,
                AVG(aktueller_saldo) as durchschnitt_saldo,
                MAX(alter_tage) as aeltestes_fahrzeug,
                MIN(zinsfreiheit_tage) as min_zinsfreiheit,
                SUM(original_betrag - aktueller_saldo) as gesamt_abbezahlt
            FROM fahrzeugfinanzierungen
            WHERE finanzinstitut = ?
        """, (institut,))
        stats = c.fetchone()
        
        # Nach RRDI/Hersteller gruppiert
        c.execute("""
            SELECT
                rrdi,
                COUNT(*) as anzahl,
                SUM(aktueller_saldo) as saldo,
                AVG(alter_tage) as durchschnitt_alter
            FROM fahrzeugfinanzierungen
            WHERE finanzinstitut = ?
            GROUP BY rrdi
            ORDER BY anzahl DESC
        """, (institut,))
        nach_marke = c.fetchall()
        
        # Warnung: Zinsfreiheit läuft bald ab (nur Stellantis)
        zinsfreiheit_warnungen = []
        if institut == 'Stellantis':
            c.execute("""
                SELECT
                    vin,
                    modell,
                    zinsfreiheit_tage,
                    aktueller_saldo,
                    alter_tage
                FROM fahrzeugfinanzierungen
                WHERE finanzinstitut = 'Stellantis'
                AND zinsfreiheit_tage IS NOT NULL
                AND zinsfreiheit_tage < 30
                ORDER BY zinsfreiheit_tage ASC
                LIMIT 5
            """)
            zinsfreiheit_warnungen = c.fetchall()
        
        ergebnis[institut] = {
            'stats': stats,
            'nach_marke': nach_marke,
            'zinsfreiheit_warnungen': zinsfreiheit_warnungen
        }
    
    return ergebnis

def main():
    # Header
    print_header("💰 LIQUIDITÄTS-DASHBOARD V2.2 - GREINER PORTAL")
    print(f"\n{BOLD}Stand:{RESET} {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")

    conn = sqlite3.connect('data/greiner_controlling.db')

    # 1. LIQUIDITÄTSÜBERSICHT MIT KREDITLINIEN
    print_header("💳 OPERATIVE LIQUIDITÄT (Bank-Konten mit Kreditlinien)")

    salden = get_aktuelle_salden_mit_limits(conn)

    gesamt_saldo = 0
    gesamt_verfuegbar = 0
    konten_mit_limit = []

    for bank, kid, konto, iban, limit, saldo, datum in salden:
        saldo_val = saldo or 0
        limit_val = limit or 0

        gesamt_saldo += saldo_val

        if limit_val > 0:
            verfuegbar = saldo_val + limit_val
            gesamt_verfuegbar += verfuegbar
            auslastung = abs(min(saldo_val, 0)) / limit_val * 100 if limit_val > 0 else 0
            konten_mit_limit.append((kid, konto, saldo_val, limit_val, verfuegbar, auslastung))

    # Konten mit Kreditlinie
    if konten_mit_limit:
        print(f"\n{BOLD}{'Konto':<35} | {'Saldo':>18} | {'Kreditlinie':>18} | {'Verfügbar':>18} | {'Auslastung'}{RESET}")
        print("-"*120)

        for kid, konto, saldo, limit, verfuegbar, auslastung in konten_mit_limit:
            konto_display = f"[{kid:2d}] {konto}"
            print(f"{konto_display:<35} | {format_currency(saldo)} | {format_currency(limit)} | {format_currency(verfuegbar)} | {format_percent(auslastung)}")

        print("="*120)
        print(f"{BOLD}{'SUMME VERFÜGBARE LIQUIDITÄT':<35}{RESET} | {'':<18} | {'':<18} | {BOLD}{format_currency(gesamt_verfuegbar)}{RESET} |")
        print("="*120)
        print(f"{CYAN}💡 Zweck: Operative Geschäftstätigkeit, laufende Kosten{RESET}")

    # 2. ALLE KONTOSTÄNDE
    print_header("📊 ALLE KONTOSTÄNDE")
    print(f"\n{BOLD}{'Bank':<35} | {'Konto':<30} | {'Saldo':>18} | {'Letztes Datum'}{RESET}")
    print("-"*120)

    current_bank = None
    bank_summe = 0

    for bank, kid, konto, iban, limit, saldo, datum in salden:
        if current_bank and current_bank != bank:
            print("-"*120)
            print(f"{'':<35} | {BOLD}Summe {current_bank}{RESET:<30} | {format_currency(bank_summe)} |")
            print("-"*120)
            bank_summe = 0

        current_bank = bank
        saldo_val = saldo or 0
        bank_summe += saldo_val

        konto_display = f"[{kid:2d}] {konto}"
        datum_display = datum[:10] if datum else "keine Daten"
        limit_info = f" (Limit: {limit:,.0f})" if limit and limit > 0 else ""

        print(f"{bank:<35} | {konto_display:<30} | {format_currency(saldo_val)} | {datum_display}{limit_info}")

    if current_bank:
        print("-"*120)
        print(f"{'':<35} | {BOLD}Summe {current_bank}{RESET:<30} | {format_currency(bank_summe)} |")

    print("="*120)
    print(f"{'':<35} | {BOLD}{CYAN}GESAMT-SALDO (Buchsaldo Bank-Konten){RESET:<30} | {BOLD}{format_currency(gesamt_saldo)}{RESET} |")
    print("="*120)

    # 3. LIQUIDITÄTS-KENNZAHLEN
    if konten_mit_limit:
        print_header("📈 LIQUIDITÄTS-KENNZAHLEN")
        print(f"\n{BOLD}Buchsaldo (aktuell):{RESET}           {format_currency(gesamt_saldo)}")
        print(f"{BOLD}Verfügbare Kreditlinien:{RESET}      {format_currency(sum(k[3] for k in konten_mit_limit))}")
        print(f"{BOLD}Gesamt verfügbare Liquidität:{RESET} {BOLD}{format_currency(gesamt_verfuegbar)}{RESET}")

        if gesamt_saldo < 0:
            print(f"\n{YELLOW}💡 Trotz negativem Buchsaldo: {format_currency(gesamt_verfuegbar)} verfügbar!{RESET}")

    # 4. NOVEMBER-STATISTIK
    print_header("📈 NOVEMBER 2025 - TRANSAKTIONEN")
    nov_konten, nov_gesamt = get_november_stats(conn)

    if nov_gesamt and nov_gesamt[0] > 0:
        gesamt, einnahmen, ausgaben = nov_gesamt
        netto = einnahmen + ausgaben

        print(f"\n{BOLD}Gesamt:{RESET} {gesamt} Transaktionen")
        print(f"{BOLD}Einnahmen:{RESET}  {format_currency(einnahmen)}")
        print(f"{BOLD}Ausgaben:{RESET}   {format_currency(ausgaben)}")
        print(f"{BOLD}Netto:{RESET}      {format_currency(netto)}\n")

        print(f"\n{BOLD}{'Konto':<40} | {'Anzahl':>8} | {'Zeitraum'}{RESET}")
        print("-"*90)
        for konto, anzahl, von, bis in nov_konten[:10]:
            konto_kurz = (konto[:37] + '...') if len(konto) > 40 else konto
            print(f"{konto_kurz:<40} | {anzahl:>8} | {von} - {bis}")

    # 5. EINKAUFSFINANZIERUNG / BESTANDSKONTEN (NEU!)
    print_header("🚗 EINKAUFSFINANZIERUNG / BESTANDSKONTEN")
    
    finanzierung_data = get_einkaufsfinanzierung(conn)
    
    gesamt_fahrzeuge = 0
    gesamt_finanzierung = 0
    alle_zinsfreiheit_warnungen = []
    
    if finanzierung_data:
        for institut, data in finanzierung_data.items():
            stats = data['stats']
            nach_marke = data['nach_marke']
            zinsfreiheit_warnungen = data['zinsfreiheit_warnungen']
            
            if stats and stats[0] > 0:
                anzahl, finanzierung, original, durchschnitt, aeltestes, min_zf, abbezahlt = stats
                
                gesamt_fahrzeuge += anzahl
                gesamt_finanzierung += finanzierung
                
                # Farbe je nach Institut
                farbe = MAGENTA if institut == 'Stellantis' else BLUE
                
                print(f"\n{BOLD}{farbe}{institut.upper()} BANK{RESET}")
                print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
                
                print(f"\n{BOLD}📊 GESAMT-ÜBERSICHT:{RESET}")
                print(f"   Anzahl finanzierte Fahrzeuge:  {BOLD}{anzahl}{RESET}")
                print(f"   Finanzierungssaldo (Schulden): {format_currency(finanzierung)} {RED}← Verbindlichkeit{RESET}")
                print(f"   Original-Kaufpreis gesamt:     {format_currency(original)}")
                print(f"   Bereits abbezahlt:             {format_currency(abbezahlt)} {GREEN}({abbezahlt/original*100:.1f}%){RESET}")
                print(f"   Durchschnitt pro Fahrzeug:     {format_currency(durchschnitt)}")
                if aeltestes:
                    print(f"   Ältestes Fahrzeug im Bestand:  {YELLOW}{aeltestes}{RESET} Tage")
                
                # Aufschlüsselung nach Marke
                if nach_marke:
                    print(f"\n{BOLD}🏷️  AUFSCHLÜSSELUNG NACH MARKE:{RESET}")
                    print(f"{'':>4}{'Marke/RRDI':<20} | {'Fahrzeuge':>12} | {'Finanzierung':>18} | {'Ø Alter'}")
                    print(f"   {'-'*80}")
                    
                    for rrdi, anz, saldo, avg_alter in nach_marke:
                        # Marken-Namen je nach Institut
                        if institut == 'Stellantis':
                            marke = "Leapmotor" if "0154X" in str(rrdi) else "Opel/Hyundai"
                        else:  # Santander
                            marke = str(rrdi) if rrdi else "Unbekannt"
                        
                        alter_display = f"{avg_alter:>6.0f} Tage" if avg_alter else "    - Tage"
                        print(f"   {marke:<20} | {anz:>12} | {format_currency(saldo)} | {alter_display}")
                
                # Zinsfreiheit-Warnungen (nur Stellantis)
                if zinsfreiheit_warnungen:
                    alle_zinsfreiheit_warnungen.extend(zinsfreiheit_warnungen)
                    
                    print(f"\n{BOLD}{RED}⚠️  ZINSFREIHEIT LÄUFT BALD AB:{RESET}")
                    print(f"{'':>4}{'VIN':<18} | {'Modell':<25} | {'Tage übrig':>12} | {'Saldo':>18}")
                    print(f"   {'-'*90}")
                    
                    for vin, modell, tage, saldo, alter in zinsfreiheit_warnungen:
                        vin_kurz = vin[-8:] if vin else "???"
                        modell_kurz = (modell[:22] + '...') if modell and len(modell) > 25 else (modell or "???")
                        tage_display = f"{RED}{tage:>3}{RESET}" if tage < 15 else f"{YELLOW}{tage:>3}{RESET}"
                        print(f"   {vin_kurz:<18} | {modell_kurz:<25} | {tage_display} Tage | {format_currency(saldo)}")
                
                print(f"\n{CYAN}💡 Zweck: Zweckgebunden für Fahrzeug-Einkaufsfinanzierung{RESET}")
                print(f"{CYAN}   → Schulden werden durch Fahrzeugverkauf getilgt{RESET}")
                print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        
        # GESAMT-ÜBERSICHT (wenn mehrere Institute)
        if len(finanzierung_data) > 1:
            print(f"\n{BOLD}{CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════{RESET}")
            print(f"{BOLD}{CYAN}GESAMT EINKAUFSFINANZIERUNG{RESET}")
            print(f"{BOLD}{CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════{RESET}")
            print(f"\n   Anzahl Fahrzeuge (gesamt):     {BOLD}{gesamt_fahrzeuge}{RESET}")
            print(f"   Finanzierung (gesamt):         {BOLD}{format_currency(gesamt_finanzierung)}{RESET} {RED}← Verbindlichkeit{RESET}")
            print()
    else:
        print(f"\n{YELLOW}⚠️  Keine Fahrzeugfinanzierungen in der Datenbank gefunden.{RESET}")

    # 6. WARNUNGEN
    print_header("⚠️  WARNUNGEN & HINWEISE")
    warnungen = []

    for kid, konto, saldo, limit, verfuegbar, auslastung in konten_mit_limit:
        if auslastung >= 80:
            warnungen.append(f"🔴 Konto [{kid}] {konto}: Kreditlinie zu {auslastung:.1f}% ausgelastet!")
        elif auslastung >= 60:
            warnungen.append(f"🟡 Konto [{kid}] {konto}: Kreditlinie zu {auslastung:.1f}% ausgelastet")

    # Konten ohne Kreditlinie mit Negativsaldo
    for bank, kid, konto, iban, limit, saldo, datum in salden:
        if (not limit or limit == 0) and saldo and saldo < -50000:
            warnungen.append(f"❌ Konto [{kid}] {konto}: Hoher Negativsaldo {format_currency(saldo)} (keine Kreditlinie)")

    # Stellantis Zinsfreiheit-Warnungen
    if alle_zinsfreiheit_warnungen:
        anzahl_kritisch = len([w for w in alle_zinsfreiheit_warnungen if w[2] < 15])
        if anzahl_kritisch > 0:
            warnungen.append(f"🔴 KRITISCH: {anzahl_kritisch} Stellantis-Fahrzeuge mit Zinsfreiheit < 15 Tage!")
        elif len(alle_zinsfreiheit_warnungen) > 0:
            warnungen.append(f"🟡 {len(alle_zinsfreiheit_warnungen)} Stellantis-Fahrzeuge mit Zinsfreiheit < 30 Tage")

    if warnungen:
        for warnung in warnungen:
            print(f"\n{warnung}")
    else:
        print(f"\n{GREEN}✅ Liquidität gesund - alle Kennzahlen im grünen Bereich!{RESET}")

    # 7. ZUSAMMENFASSUNG
    print_header("💼 FINANZ-ZUSAMMENFASSUNG")
    
    print(f"\n{BOLD}Bank-Konten (Buchsaldo):{RESET}      {format_currency(gesamt_saldo)}")
    
    # Einkaufsfinanzierung aufschlüsseln
    if finanzierung_data:
        for institut, data in sorted(finanzierung_data.items()):
            stats = data['stats']
            if stats and stats[0] > 0:
                finanzierung = stats[1]
                print(f"{BOLD}{institut} (Finanzierung):{RESET}    {format_currency(finanzierung)} {RED}← Verbindlichkeit{RESET}")
    
    print("─" * 80)
    
    netto_position = gesamt_saldo + gesamt_finanzierung
    print(f"{BOLD}Netto-Vermögensposition:{RESET}     {BOLD}{format_currency(netto_position)}{RESET}")
    
    if gesamt_verfuegbar > 0:
        print(f"\n{CYAN}💡 Operative Liquidität (mit Kreditlinien): {format_currency(gesamt_verfuegbar)}{RESET}")

    conn.close()

    print("\n" + "="*120 + "\n")

if __name__ == '__main__':
    main()
