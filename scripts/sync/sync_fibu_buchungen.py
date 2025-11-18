#!/usr/bin/env python3
"""
FIBU-Buchungen Sync von Locosoft PostgreSQL → SQLite (Version 2.0)

NEU in v2.0:
- Automatische Bank-Kategorisierung
- Verbesserte Hyundai-Erkennung (HYU Bank)
- Finanzamt-Zinsen getrennt
- Tippfehler-Toleranz (Abshcluss → Abschluss)

Synct ALLE Buchungen aus journal_accountings zur vollständigen FIBU-Übersicht.
Kategorisiert automatisch: zinsen, gebuehren, miete, sonstiges + BANK!

Best Practices übernommen aus sync_sales.py:
- Inkrementelles Update (nur neue/geänderte)
- Deduplizierung via (doc_number, position)
- Detaillierte Statistik
- Fehlerbehandlung
- Logging

Autor: Greiner Portal Team
Datum: 2025-11-14
Version: 2.0
"""

import sys
import json
import sqlite3
import psycopg2
from datetime import datetime, timedelta
from pathlib import Path

# Pfad-Konfiguration
PORTAL_ROOT = Path(__file__).parent.parent.parent
CREDENTIALS_FILE = PORTAL_ROOT / 'config' / 'credentials.json'
SQLITE_DB = PORTAL_ROOT / 'data' / 'greiner_controlling.db'

# Sachkonten-Mapping für Kategorisierung
SACHKONTEN_ZINSEN = {230011, 230101, 230311, 233001}
SACHKONTEN_GEBUEHREN = {234001, 234002, 234003}

def load_credentials():
    """Lädt Credentials aus config/credentials.json"""
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            creds = json.load(f)
            return creds['databases']['locosoft']
    except Exception as e:
        print(f"❌ Fehler beim Laden der Credentials: {e}")
        sys.exit(1)

def connect_locosoft():
    """Verbindung zu Locosoft PostgreSQL"""
    try:
        creds = load_credentials()
        conn = psycopg2.connect(
            host=creds['host'],
            port=creds.get('port', 5432),
            database=creds['database'],
            user=creds['user'],
            password=creds['password']
        )
        return conn
    except Exception as e:
        print(f"❌ Fehler bei Locosoft-Verbindung: {e}")
        sys.exit(1)

def connect_sqlite():
    """Verbindung zu SQLite"""
    try:
        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ Fehler bei SQLite-Verbindung: {e}")
        sys.exit(1)

def kategorisiere_bank(nominal_account, posting_text):
    """
    Kategorisiert Bank basierend auf Sachkonto und Text
    
    Args:
        nominal_account: Sachkonto-Nummer
        posting_text: Buchungstext
        
    Returns:
        str: Bank-Name ('Stellantis Bank', 'Genobank', etc.)
    """
    if not posting_text:
        posting_text = ""
    
    text_lower = posting_text.lower()
    
    # 1. Stellantis Bank
    if 'stellantis bank' in text_lower or 'zinsen stellantis' in text_lower:
        return 'Stellantis Bank'
    
    # 2. Santander Bank
    if 'santander' in text_lower:
        return 'Santander Bank'
    
    # 3. Hyundai Finance (auch "HYU Bank"!)
    if 'hyundai' in text_lower or 'hyu bank' in text_lower or 'hyu-bank' in text_lower:
        return 'Hyundai Finance'
    
    # 4. Genobank (via Sachkonto 233001 ODER Abschluss-Texte)
    if nominal_account == 233001:
        return 'Genobank'
    
    # Auch Tippfehler berücksichtigen!
    if 'abschluss' in text_lower or 'abshcluss' in text_lower:
        return 'Genobank'
    
    # 5. Sparkasse
    if 'sparkasse' in text_lower:
        return 'Sparkasse'
    
    # 6. Finanzamt (Umsatzsteuer-Zinsen)
    if any(kw in text_lower for kw in ['ust-nz', 'umsatzsteuer', 'finanzamt', 'ust nz']):
        return 'Finanzamt (USt)'
    
    # 7. Sonstige
    return 'Sonstige'

def kategorisiere_buchung(nominal_account, posting_text):
    """
    Kategorisiert Buchung basierend auf Sachkonto und Text
    
    Args:
        nominal_account: Sachkonto-Nummer
        posting_text: Buchungstext
        
    Returns:
        str: 'zinsen', 'gebuehren', 'miete', 'sonstiges'
    """
    if not posting_text:
        posting_text = ""
    
    text_lower = posting_text.lower()
    
    # 1. Mietzins ausschließen (WICHTIG!)
    if 'mietzins' in text_lower or 'miete' in text_lower:
        return 'miete'
    
    # 2. Konto-basierte Kategorisierung
    if nominal_account in SACHKONTEN_ZINSEN:
        return 'zinsen'
    
    if nominal_account in SACHKONTEN_GEBUEHREN:
        return 'gebuehren'
    
    # 3. Text-basierte Kategorisierung
    if any(kw in text_lower for kw in ['zins', 'zinsen']):
        return 'zinsen'
    
    if any(kw in text_lower for kw in ['gebühr', 'gebuehr', 'provision']):
        return 'gebuehren'
    
    return 'sonstiges'

def get_last_sync_date(sqlite_conn):
    """
    Ermittelt das Datum der letzten Synchronisation
    
    Returns:
        datetime: Datum der letzten Buchung oder None
    """
    cursor = sqlite_conn.cursor()
    cursor.execute("""
        SELECT MAX(accounting_date) as last_date
        FROM fibu_buchungen
    """)
    row = cursor.fetchone()
    
    if row and row['last_date']:
        return datetime.strptime(row['last_date'], '%Y-%m-%d')
    return None

def fetch_buchungen_from_locosoft(pg_conn, days_back=365):
    """
    Holt ALLE Buchungen aus Locosoft ab einem bestimmten Datum
    
    Args:
        pg_conn: PostgreSQL Connection
        days_back: Anzahl Tage zurück (default: 365)
        
    Returns:
        list: Liste von Buchungen als Dictionaries
    """
    cursor = pg_conn.cursor()
    
    # Datum berechnen
    cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    print(f"📥 Hole ALLE Buchungen seit {cutoff_date}...")
    
    # WICHTIG: posted_value ist in CENTS!
    query = """
        SELECT 
            document_number,
            position_in_document,
            accounting_date,
            nominal_account_number,
            posted_value,
            debit_or_credit,
            posting_text,
            vehicle_reference
        FROM journal_accountings
        WHERE accounting_date >= %s
        ORDER BY accounting_date DESC, document_number, position_in_document
    """
    
    cursor.execute(query, (cutoff_date,))
    rows = cursor.fetchall()
    
    print(f"✅ {len(rows)} Buchungen gefunden")
    
    # In Dictionary-Liste umwandeln
    buchungen = []
    for row in rows:
        buchungen.append({
            'document_number': row[0],
            'position': row[1],
            'accounting_date': row[2],
            'nominal_account': row[3],
            'posted_value': row[4],  # CENTS!
            'debit_credit': row[5],
            'posting_text': row[6] or '',
            'vehicle_reference': row[7] or ''
        })
    
    cursor.close()
    return buchungen

def sync_buchungen(buchungen, sqlite_conn):
    """
    Synct Buchungen in SQLite mit Deduplizierung
    
    Args:
        buchungen: Liste von Buchungen
        sqlite_conn: SQLite Connection
        
    Returns:
        dict: Statistik (inserted, updated, skipped, kategorien, banken)
    """
    cursor = sqlite_conn.cursor()
    
    stats = {
        'inserted': 0,
        'updated': 0,
        'skipped': 0,
        'kategorien': {},
        'banken': {}
    }
    
    print(f"\n🔄 Sync von {len(buchungen)} Buchungen...")
    
    for i, buchung in enumerate(buchungen):
        if (i + 1) % 1000 == 0:
            print(f"   ... {i + 1}/{len(buchungen)}")
        
        # Betrag von Cents → Euro konvertieren (WICHTIG!)
        betrag_euro = buchung['posted_value'] / 100.0
        
        # Kategorisierung
        buchungstyp = kategorisiere_buchung(
            buchung['nominal_account'],
            buchung['posting_text']
        )
        
        # Bank-Kategorisierung (NEU!)
        bank = kategorisiere_bank(
            buchung['nominal_account'],
            buchung['posting_text']
        )
        
        # Statistik
        stats['kategorien'][buchungstyp] = stats['kategorien'].get(buchungstyp, 0) + 1
        stats['banken'][bank] = stats['banken'].get(bank, 0) + 1
        
        # Prüfen ob bereits vorhanden
        cursor.execute("""
            SELECT id FROM fibu_buchungen
            WHERE locosoft_doc_number = ? AND locosoft_position = ?
        """, (buchung['document_number'], buchung['position']))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update (falls sich Daten geändert haben)
            cursor.execute("""
                UPDATE fibu_buchungen
                SET accounting_date = ?,
                    nominal_account = ?,
                    amount = ?,
                    debit_credit = ?,
                    posting_text = ?,
                    buchungstyp = ?,
                    bank = ?,
                    vehicle_reference = ?,
                    synced_at = CURRENT_TIMESTAMP
                WHERE locosoft_doc_number = ? AND locosoft_position = ?
            """, (
                buchung['accounting_date'],
                buchung['nominal_account'],
                betrag_euro,
                buchung['debit_credit'],
                buchung['posting_text'],
                buchungstyp,
                bank,
                buchung['vehicle_reference'],
                buchung['document_number'],
                buchung['position']
            ))
            
            if cursor.rowcount > 0:
                stats['updated'] += 1
            else:
                stats['skipped'] += 1
        else:
            # Insert
            cursor.execute("""
                INSERT INTO fibu_buchungen (
                    locosoft_doc_number,
                    locosoft_position,
                    accounting_date,
                    nominal_account,
                    amount,
                    debit_credit,
                    posting_text,
                    buchungstyp,
                    bank,
                    vehicle_reference,
                    synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                buchung['document_number'],
                buchung['position'],
                buchung['accounting_date'],
                buchung['nominal_account'],
                betrag_euro,
                buchung['debit_credit'],
                buchung['posting_text'],
                buchungstyp,
                bank,
                buchung['vehicle_reference']
            ))
            stats['inserted'] += 1
    
    sqlite_conn.commit()
    cursor.close()
    
    return stats

def print_statistics(stats):
    """Druckt schöne Statistik"""
    print("\n" + "="*60)
    print("📊 SYNC-STATISTIK")
    print("="*60)
    print(f"✅ Neu eingefügt:     {stats['inserted']:>6}")
    print(f"🔄 Aktualisiert:      {stats['updated']:>6}")
    print(f"⏭️  Übersprungen:      {stats['skipped']:>6}")
    print(f"📈 Gesamt verarbeitet: {sum([stats['inserted'], stats['updated'], stats['skipped']]):>6}")
    
    print("\n📋 KATEGORIEN:")
    for kategorie, anzahl in sorted(stats['kategorien'].items()):
        print(f"   {kategorie:12} : {anzahl:>6}")
    
    print("\n🏦 BANKEN:")
    for bank, anzahl in sorted(stats['banken'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {bank:20} : {anzahl:>6}")
    
    print("="*60)

def main():
    """Haupt-Funktion"""
    print("="*60)
    print("🚀 FIBU-BUCHUNGEN SYNC v2.0 - Locosoft → Portal")
    print("="*60)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Parameter: Anzahl Tage zurück (default: 365)
    days_back = int(sys.argv[1]) if len(sys.argv) > 1 else 365
    print(f"⏰ Sync-Zeitraum: Letzte {days_back} Tage\n")
    
    # 1. Verbindungen aufbauen
    print("🔌 Verbindungen aufbauen...")
    pg_conn = connect_locosoft()
    sqlite_conn = connect_sqlite()
    print("✅ Verbindungen OK\n")
    
    try:
        # 2. Buchungen aus Locosoft holen
        buchungen = fetch_buchungen_from_locosoft(pg_conn, days_back)
        
        if not buchungen:
            print("ℹ️  Keine neuen Buchungen gefunden")
            return
        
        # 3. In SQLite syncen
        stats = sync_buchungen(buchungen, sqlite_conn)
        
        # 4. Statistik ausgeben
        print_statistics(stats)
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Verbindungen schließen
        pg_conn.close()
        sqlite_conn.close()
    
    print(f"\n✅ SYNC ABGESCHLOSSEN!")
    print(f"Ende: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

if __name__ == '__main__':
    main()
