#!/usr/bin/env python3
"""
BWA-BERECHNUNG aus Locosoft-Mirror (SKR51)
==========================================
Version: 1.0
Datum: 2025-12-02

Berechnet BWA-Werte aus der gespiegelten loco_journal_accountings Tabelle.
100% validiert gegen GlobalCube Oktober + November 2025.

WICHTIG - SKR51 LOGIK:
- 7xxxxx = EINSATZWERTE (nicht Umsatz!)
- 8xxxxx = UMSATZERLÖSE (nicht Einsatz!)
- Vorzeichen: Erlöse = H-S, Aufwand = S-H

Verwendung:
    python bwa_berechnung.py                     # Aktueller Monat
    python bwa_berechnung.py --monat 10          # Oktober
    python bwa_berechnung.py --jahr 2025 --monat 11  # November 2025
    python bwa_berechnung.py --alle              # Sep-aktueller Monat
    python bwa_berechnung.py --print-only        # Nur anzeigen, nicht speichern

Läuft nach locosoft_mirror.py (19:00), geplant: 19:30
"""

import os
import sys
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

# =============================================================================
# KONFIGURATION
# =============================================================================

SQLITE_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

# =============================================================================
# LOGGING
# =============================================================================

def log(msg: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

# =============================================================================
# DATENBANK
# =============================================================================

def connect_sqlite():
    """Verbindung zu SQLite"""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_bwa_tables(conn):
    """Erstellt BWA-Tabellen falls nicht vorhanden"""
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bwa_monatswerte (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jahr INTEGER NOT NULL,
            monat INTEGER NOT NULL,
            position TEXT NOT NULL,
            bezeichnung TEXT,
            betrag REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(jahr, monat, position)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bwa_jahr_monat 
        ON bwa_monatswerte(jahr, monat)
    """)
    
    conn.commit()

# =============================================================================
# BWA-BERECHNUNG (100% VALIDIERT GEGEN GLOBALCUBE OKT+NOV 2025)
# =============================================================================

def berechne_bwa_monat(conn, jahr: int, monat: int) -> dict:
    """
    Berechnet die BWA-Werte für einen Monat.
    Formel validiert gegen GlobalCube Oktober + November 2025.
    """
    cursor = conn.cursor()
    
    # Datumsbereich
    datum_von = f"{jahr}-{monat:02d}-01"
    if monat == 12:
        datum_bis = f"{jahr+1}-01-01"
    else:
        datum_bis = f"{jahr}-{monat+1:02d}-01"
    
    # === 1. UMSATZERLÖSE (8xxxxx) ===
    # Konten: 80-88 + 8932xx, Berechnung: HABEN - SOLL
    cursor.execute("""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value 
                 ELSE -posted_value END
        )/100.0, 0)
        FROM loco_journal_accountings
        WHERE accounting_date >= ? AND accounting_date < ?
          AND ((nominal_account_number BETWEEN 800000 AND 889999)
               OR (nominal_account_number BETWEEN 893200 AND 893299))
    """, (datum_von, datum_bis))
    umsatz = cursor.fetchone()[0] or 0
    
    # === 2. EINSATZWERTE (7xxxxx) ===
    # Konten: 70-79, Berechnung: SOLL - HABEN
    cursor.execute("""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value 
                 ELSE -posted_value END
        )/100.0, 0)
        FROM loco_journal_accountings
        WHERE accounting_date >= ? AND accounting_date < ?
          AND nominal_account_number BETWEEN 700000 AND 799999
    """, (datum_von, datum_bis))
    einsatz = cursor.fetchone()[0] or 0
    
    # === 3. VARIABLE KOSTEN ===
    cursor.execute("""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value 
                 ELSE -posted_value END
        )/100.0, 0)
        FROM loco_journal_accountings
        WHERE accounting_date >= ? AND accounting_date < ?
          AND (
            -- 4151xx: Provisionen Finanz-Vermittlung
            nominal_account_number BETWEEN 415100 AND 415199
            -- 4355xx: Trainingskosten
            OR nominal_account_number BETWEEN 435500 AND 435599
            -- 455xx-456xx: Fahrzeugkosten (nur KST 1-7)
            OR (nominal_account_number BETWEEN 455000 AND 456999 
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            -- 4870x: Werbekosten direkt (nur KST 1-7)
            OR (nominal_account_number BETWEEN 487000 AND 487099 
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
            -- 491xx-497xx: Fertigmachen, Provisionen, Kulanz
            OR nominal_account_number BETWEEN 491000 AND 497899
          )
    """, (datum_von, datum_bis))
    variable = cursor.fetchone()[0] or 0
    
    # === 4. DIREKTE KOSTEN ===
    # KST 1-7 ohne Variable und ohne 424xx, 438xx
    cursor.execute("""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value 
                 ELSE -posted_value END
        )/100.0, 0)
        FROM loco_journal_accountings
        WHERE accounting_date >= ? AND accounting_date < ?
          AND nominal_account_number BETWEEN 400000 AND 489999
          AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
          AND NOT (
            nominal_account_number BETWEEN 415100 AND 415199
            OR nominal_account_number BETWEEN 424000 AND 424999
            OR nominal_account_number BETWEEN 435500 AND 435599
            OR nominal_account_number BETWEEN 438000 AND 438999
            OR nominal_account_number BETWEEN 455000 AND 456999
            OR nominal_account_number BETWEEN 487000 AND 487099
            OR nominal_account_number BETWEEN 491000 AND 497999
          )
    """, (datum_von, datum_bis))
    direkte = cursor.fetchone()[0] or 0
    
    # === 5. INDIREKTE KOSTEN ===
    # KST 0 + 424xx/438xx mit KST 1-7 + 498xx + 89xxxx
    cursor.execute("""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='S' THEN posted_value 
                 ELSE -posted_value END
        )/100.0, 0)
        FROM loco_journal_accountings
        WHERE accounting_date >= ? AND accounting_date < ?
          AND (
            (nominal_account_number BETWEEN 400000 AND 499999 
             AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
            OR (nominal_account_number BETWEEN 424000 AND 424999 
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR (nominal_account_number BETWEEN 438000 AND 438999 
                AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
            OR nominal_account_number BETWEEN 498000 AND 499999
            OR nominal_account_number BETWEEN 891000 AND 896999
          )
    """, (datum_von, datum_bis))
    indirekte = cursor.fetchone()[0] or 0
    
    # === 6. NEUTRALES ERGEBNIS ===
    # Konten 20-28: Außerordentlich, Zinsen, Sonstiges
    # Berechnung: HABEN - SOLL (Erträge - Aufwendungen)
    cursor.execute("""
        SELECT COALESCE(SUM(
            CASE WHEN debit_or_credit='H' THEN posted_value 
                 ELSE -posted_value END
        )/100.0, 0)
        FROM loco_journal_accountings
        WHERE accounting_date >= ? AND accounting_date < ?
          AND nominal_account_number BETWEEN 200000 AND 289999
    """, (datum_von, datum_bis))
    neutral = cursor.fetchone()[0] or 0
    
    # === BERECHNUNGEN ===
    db1 = umsatz - einsatz       # Bruttoertrag
    db2 = db1 - variable         # Bruttoertrag II
    db3 = db2 - direkte          # Deckungsbeitrag
    be = db3 - indirekte         # Betriebsergebnis
    ue = be + neutral            # Unternehmensergebnis
    
    return {
        'umsatz': round(umsatz, 2),
        'einsatz': round(einsatz, 2),
        'db1': round(db1, 2),
        'variable': round(variable, 2),
        'db2': round(db2, 2),
        'direkte': round(direkte, 2),
        'db3': round(db3, 2),
        'indirekte': round(indirekte, 2),
        'betriebsergebnis': round(be, 2),
        'neutral': round(neutral, 2),
        'unternehmensergebnis': round(ue, 2)
    }


def speichere_bwa_monat(conn, jahr: int, monat: int, werte: dict):
    """Speichert die BWA-Werte in der Datenbank."""
    cursor = conn.cursor()
    
    positionen = [
        ('umsatz', 'Umsatzerlöse'),
        ('einsatz', 'Einsatzwerte'),
        ('db1', 'Bruttoertrag (DB1)'),
        ('variable', 'Variable Kosten'),
        ('db2', 'Bruttoertrag II (DB2)'),
        ('direkte', 'Direkte Kosten'),
        ('db3', 'Deckungsbeitrag (DB3)'),
        ('indirekte', 'Indirekte Kosten'),
        ('betriebsergebnis', 'Betriebsergebnis'),
        ('neutral', 'Neutrales Ergebnis'),
        ('unternehmensergebnis', 'Unternehmensergebnis')
    ]
    
    for pos, bez in positionen:
        cursor.execute("""
            INSERT OR REPLACE INTO bwa_monatswerte 
            (jahr, monat, position, bezeichnung, betrag, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (jahr, monat, pos, bez, werte[pos]))
    
    conn.commit()


def print_bwa(jahr: int, monat: int, werte: dict):
    """Gibt die BWA formatiert aus."""
    print(f"\n{'═' * 60}")
    print(f"  BWA {monat:02d}/{jahr}")
    print(f"{'═' * 60}")
    print(f"  Umsatzerlöse:        {werte['umsatz']:>15,.2f} €")
    print(f"  Einsatzwerte:        {werte['einsatz']:>15,.2f} €")
    print(f"  {'─' * 56}")
    print(f"  Bruttoertrag (DB1):  {werte['db1']:>15,.2f} €")
    print(f"  Variable Kosten:     {werte['variable']:>15,.2f} €")
    print(f"  {'─' * 56}")
    print(f"  Bruttoertrag II:     {werte['db2']:>15,.2f} €")
    print(f"  Direkte Kosten:      {werte['direkte']:>15,.2f} €")
    print(f"  {'─' * 56}")
    print(f"  Deckungsbeitrag:     {werte['db3']:>15,.2f} €")
    print(f"  Indirekte Kosten:    {werte['indirekte']:>15,.2f} €")
    print(f"  {'─' * 56}")
    print(f"  Betriebsergebnis:    {werte['betriebsergebnis']:>15,.2f} €")
    print(f"  Neutrales Ergebnis:  {werte['neutral']:>15,.2f} €")
    print(f"  {'─' * 56}")
    print(f"  UNTERNEHMENSERGEBNIS:{werte['unternehmensergebnis']:>15,.2f} €")
    print(f"{'═' * 60}\n")


# =============================================================================
# HAUPTPROGRAMM
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='BWA-Berechnung aus Locosoft-Mirror (SKR51)')
    parser.add_argument('--monat', type=int, help='Monat (1-12)')
    parser.add_argument('--jahr', type=int, help='Jahr (z.B. 2025)')
    parser.add_argument('--alle', action='store_true', help='Alle Monate seit Sep 2025')
    parser.add_argument('--print-only', action='store_true', help='Nur anzeigen, nicht speichern')
    
    args = parser.parse_args()
    
    # Defaults
    heute = datetime.now()
    jahr = args.jahr or heute.year
    monat = args.monat or heute.month
    
    log("=" * 60)
    log("BWA-BERECHNUNG (SKR51)")
    log(f"Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)
    
    # SQLite Verbindung
    conn = connect_sqlite()
    init_bwa_tables(conn)
    
    try:
        if args.alle:
            # Alle Monate seit Sep 2025
            log("Berechne alle Monate seit September 2025...")
            for m in range(9, heute.month + 1):
                werte = berechne_bwa_monat(conn, 2025, m)
                if not args.print_only:
                    speichere_bwa_monat(conn, 2025, m, werte)
                print_bwa(2025, m, werte)
            log(f"Fertig! {heute.month - 8} Monate berechnet.")
        else:
            # Einzelner Monat
            log(f"Berechne BWA {monat:02d}/{jahr}...")
            werte = berechne_bwa_monat(conn, jahr, monat)
            if not args.print_only:
                speichere_bwa_monat(conn, jahr, monat, werte)
                log(f"BWA {monat:02d}/{jahr} gespeichert in bwa_monatswerte")
            print_bwa(jahr, monat, werte)
    
    finally:
        conn.close()
    
    log("Fertig!")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f"Fehler: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
