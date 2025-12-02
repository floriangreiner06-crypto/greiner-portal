#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIBU-Buchungen Sync v2.2 - MIT TEXT-BASIERTER KATEGORISIERUNG
============================================================

Synchronisiert FIBU-Buchungen von Locosoft PostgreSQL nach SQLite
und kategorisiert sie ERWEITERT - auch Bilanzkonten!

WICHTIGE ÄNDERUNGEN v2.2:
- Text-basierte Erkennung für Personalkosten (Konto 187001)
- Text-basierte Erkennung für Wareneinsatz (Konten 160001, 171201)
- Hart-codierte Sonderkonten
- Löst das "853k € fehlen"-Problem aus TAG 45!

Author: Claude (TAG 46)
Date: 2025-11-15
"""

import psycopg2
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# ============================================================================
# KONFIGURATION
# ============================================================================

# Pfade (relativ zum Projekt-Root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "config" / "credentials.json"
SQLITE_DB = PROJECT_ROOT / "data" / "greiner_controlling.db"

# ============================================================================
# KEYWORD-KATEGORIEN (NEU v2.2!)
# ============================================================================

KEYWORD_KATEGORIEN = {
    'kosten_personal': [
        'aok', 'lohn', 'gehalt', 'lohnsteuer', 'lst', 
        'solz', 'sozial', 'krankenkasse', 'berufsgenossenschaft',
        'bg bau', 'rentenversicherung', 'arbeitslosenversicherung',
        'bgbau', 'rvbeitrag', 'krankenvers', 'sozialvers'
    ],
    
    'wareneinsatz_fahrzeuge': [
        'stellantis', 'hyundai', 'opel', 'peugeot', 'citroën', 'citroen',
        'netting', 'fahrzeug', 'pkw', 'auto', 'kfz',
        'lagerwagenfinanzierung', 'automobile gmbh', 'motor deutschland',
        'psa bank', 'hyundai bank', 'fahrzeugfinanzierung'
    ],
    
    'wareneinsatz_teile': [
        'dekra', 'tüv', 'tuev', 'teile', 'ersatzteile', 
        'kroschke', 'zulassung', 'autoteile', 'kfz teile'
    ],
}

# Hart-codierte Sonderkonten (v2.2)
SPECIAL_ACCOUNTS = {
    187001: 'kosten_personal',          # Personalkosten-Verbindlichkeiten
    160001: 'wareneinsatz_fahrzeuge',   # Hauptlieferant (Opel, Hyundai)
    171201: 'wareneinsatz_fahrzeuge',   # Stellantis Bank Netting
}

# ============================================================================
# HILFSFUNKTIONEN
# ============================================================================

def load_credentials():
    """Lädt Credentials aus JSON-Datei"""
    with open(CREDENTIALS_FILE, 'r') as f:
        creds = json.load(f)
    return creds['databases']['locosoft']

def calculate_wirtschaftsjahr(date):
    """
    Berechnet Wirtschaftsjahr (01.09. - 31.08.)
    
    Beispiele:
    - 2024-08-31 -> "2023/2024"
    - 2024-09-01 -> "2024/2025"
    - 2025-01-15 -> "2024/2025"
    """
    year = date.year
    month = date.month
    
    if month >= 9:  # Sep-Dez
        return f"{year}/{year+1}"
    else:  # Jan-Aug
        return f"{year-1}/{year}"

def kategorisiere_erweitert_v2(nominal_account, posting_text, debit_credit):
    """
    Erweiterte Kategorisierung v2.2
    
    NEU: Text-basierte Erkennung für Bilanzkonten!
    
    Logik:
    1. GuV-Konten (70-89): Nach Bereich kategorisieren (wie v2.1)
    2. Bilanzkonten: Text-basierte Erkennung + Hart-codierte Konten
    3. Rest: 'bilanz'
    """
    bereich = nominal_account // 10000
    text = posting_text.lower() if posting_text else ""
    
    # ========================================================================
    # 1. GuV-KONTEN (70-89) - WIE v2.1
    # ========================================================================
    
    if 70 <= bereich <= 79:
        # KOSTEN (70-79)
        if bereich == 71:
            return 'kosten_sonstige'
        elif bereich == 72:
            return 'kosten_personal'
        elif bereich == 73:
            return 'kosten_betrieb'
        elif bereich == 74:
            return 'kosten_vertrieb'
        elif bereich == 75:
            return 'kosten_abschreibungen'
        elif bereich == 76:
            return 'kosten_finanzen'
        else:
            return 'kosten_sonstige'
    
    elif 80 <= bereich <= 89:
        # UMSÄTZE (80-89)
        if bereich == 81:
            return 'umsatz_fahrzeuge_neu'
        elif bereich == 82:
            return 'umsatz_fahrzeuge_gebraucht'
        elif bereich == 83:
            return 'umsatz_werkstatt'
        elif bereich == 84:
            return 'umsatz_teile'
        elif bereich == 85:
            return 'umsatz_sonstige_leistungen'
        elif bereich == 86:
            return 'umsatz_sonstige'
        elif bereich == 87:
            return 'umsatz_provisionen'
        elif bereich == 88:
            return 'umsatz_nebenleistungen'
        else:
            return 'umsatz_sonstige'
    
    # ========================================================================
    # 2. NEU v2.2: BILANZKONTEN MIT TEXT-ERKENNUNG!
    # ========================================================================
    
    # 2a) Hart-codierte Sonderkonten (höchste Priorität!)
    if nominal_account in SPECIAL_ACCOUNTS:
        return SPECIAL_ACCOUNTS[nominal_account]
    
    # 2b) Text-basierte Erkennung
    
    # Personalkosten erkennen (oft in Bereich 18 - Verbindlichkeiten)
    if any(kw in text for kw in KEYWORD_KATEGORIEN['kosten_personal']):
        return 'kosten_personal'
    
    # Wareneinsatz Fahrzeuge (oft in Bereich 16/17 - Lieferanten/Netting)
    if any(kw in text for kw in KEYWORD_KATEGORIEN['wareneinsatz_fahrzeuge']):
        return 'wareneinsatz_fahrzeuge'
    
    # Wareneinsatz Teile (Bereich 16 - Lieferanten)
    if any(kw in text for kw in KEYWORD_KATEGORIEN['wareneinsatz_teile']):
        return 'wareneinsatz_teile'
    
    # ========================================================================
    # 3. REST = BILANZ (Durchlaufposten, Anlagen, etc.)
    # ========================================================================
    
    return 'bilanz'

# ============================================================================
# HAUPTFUNKTIONEN
# ============================================================================

def sync_fibu_buchungen():
    """
    Hauptfunktion: Synchronisiert FIBU-Buchungen von Locosoft nach SQLite
    """
    print("=" * 80)
    print("FIBU-BUCHUNGEN SYNC v2.2 - MIT TEXT-BASIERTER KATEGORISIERUNG")
    print("=" * 80)
    print()
    
    # Credentials laden
    print("📋 Lade Credentials...")
    locosoft_creds = load_credentials()
    
    # PostgreSQL Connection
    print("🔌 Verbinde mit Locosoft PostgreSQL...")
    pg_conn = psycopg2.connect(
        host=locosoft_creds['host'],
        port=locosoft_creds['port'],
        database=locosoft_creds['database'],
        user=locosoft_creds['user'],
        password=locosoft_creds['password']
    )
    pg_cursor = pg_conn.cursor()
    
    # SQLite Connection
    print("🔌 Verbinde mit SQLite...")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Buchungen aus Locosoft holen
    print("📥 Lade Buchungen aus Locosoft...")
    pg_cursor.execute("""
        SELECT 
            document_number,
            position_in_document,
            accounting_date,
            nominal_account_number,
            posted_value,
            debit_or_credit,
            posting_text
        FROM journal_accountings
        ORDER BY accounting_date, document_number, position_in_document
    """)
    
    buchungen = pg_cursor.fetchall()
    print(f"✅ {len(buchungen):,} Buchungen geladen")
    print()
    
    # Statistik
    stats = {
        'gesamt': len(buchungen),
        'neu': 0,
        'duplikat': 0,
        'kategorien': {}
    }
    
    # Buchungen verarbeiten
    print("⚙️  Verarbeite Buchungen...")
    print()
    
    for i, row in enumerate(buchungen, 1):
        doc_num, pos, acc_date, nominal_acc, posted_val, debit_credit, posting_text = row
        
        # Betrag von Cents nach Euro konvertieren
        amount_euro = posted_val / 100.0
        
        # Wirtschaftsjahr berechnen
        wj = calculate_wirtschaftsjahr(acc_date)
        
        # Kategorisierung v2.2
        kategorie = kategorisiere_erweitert_v2(nominal_acc, posting_text, debit_credit)
        
        # Statistik
        stats['kategorien'][kategorie] = stats['kategorien'].get(kategorie, 0) + 1
        
        # In SQLite einfügen (oder Skip bei Duplikat)
        try:
            sqlite_cursor.execute("""
                INSERT INTO fibu_buchungen (
                    locosoft_doc_number,
                    locosoft_position,
                    accounting_date,
                    nominal_account,
                    amount,
                    debit_credit,
                    posting_text,
                    kategorie_erweitert,
                    wirtschaftsjahr,
                    synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                doc_num,
                pos,
                acc_date,
                nominal_acc,
                amount_euro,
                debit_credit,
                posting_text,
                kategorie,
                wj
            ))
            stats['neu'] += 1
        except sqlite3.IntegrityError:
            # Duplikat - Update der Kategorie!
            sqlite_cursor.execute("""
                UPDATE fibu_buchungen
                SET kategorie_erweitert = ?,
                    wirtschaftsjahr = ?
                WHERE locosoft_doc_number = ?
                  AND locosoft_position = ?
            """, (kategorie, wj, doc_num, pos))
            stats['duplikat'] += 1
        
        # Fortschritt
        if i % 10000 == 0:
            print(f"  ⏳ {i:,} / {len(buchungen):,} verarbeitet...")
    
    # Commit
    print()
    print("💾 Speichere Änderungen...")
    sqlite_conn.commit()
    
    # Cleanup
    pg_cursor.close()
    pg_conn.close()
    sqlite_cursor.close()
    sqlite_conn.close()
    
    # Ergebnis
    print()
    print("=" * 80)
    print("✅ SYNC ERFOLGREICH ABGESCHLOSSEN!")
    print("=" * 80)
    print()
    print(f"📊 STATISTIK:")
    print(f"  Gesamt verarbeitet:  {stats['gesamt']:,}")
    print(f"  Neu eingefügt:       {stats['neu']:,}")
    print(f"  Duplikate (Update):  {stats['duplikat']:,}")
    print()
    print(f"📈 KATEGORIEN (Top 15):")
    sorted_kat = sorted(stats['kategorien'].items(), key=lambda x: x[1], reverse=True)
    for kat, count in sorted_kat[:15]:
        pct = (count / stats['gesamt'] * 100)
        print(f"  {kat:30s} {count:8,} ({pct:5.1f}%)")
    
    if len(sorted_kat) > 15:
        rest_count = sum(count for kat, count in sorted_kat[15:])
        rest_pct = (rest_count / stats['gesamt'] * 100)
        print(f"  {'... weitere ...':30s} {rest_count:8,} ({rest_pct:5.1f}%)")
    
    print()
    print(f"🕒 Sync abgeschlossen: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    try:
        sync_fibu_buchungen()
    except Exception as e:
        print()
        print("❌ FEHLER:")
        print(f"  {e}")
        import traceback
        traceback.print_exc()
        exit(1)
