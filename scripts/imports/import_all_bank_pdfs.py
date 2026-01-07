#!/usr/bin/env python3
"""
UNIVERSAL BANK PDF IMPORT - Alle Banken
========================================
Importiert PDFs von allen Banken aus dem Mount-Verzeichnis.

Unterstützte Banken:
- Hypovereinsbank (HVB)
- Sparkasse (SPK)
- VR Bank Landau
- Genobank Auto Greiner
- Genobank Autohaus Greiner

Läuft 3x täglich via Cron: 08:00, 12:00, 17:00

Version: 2.0 (TAG 165) - PostgreSQL Migration
Erstellt: 25.11.2025
Updated: 2026-01-03 (PostgreSQL Support)
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta

# Parser-Pfad hinzufügen (Projekt-Root, nicht parsers-Ordner!)
sys.path.insert(0, '/opt/greiner-portal')

# PostgreSQL DB-Connection (TAG 165)
from api.db_connection import get_db, sql_placeholder, convert_placeholders, get_db_type

# ============================================================================
# KONFIGURATION
# ============================================================================

BASE_PATH = '/mnt/buchhaltung/Buchhaltung/Kontoauszüge'

# Bank-Konfigurationen: (Ordner, Parser-Klasse, IBAN-Muster, Datei-Prefix)
BANK_CONFIGS = {
    'hvb': {
        'folder': 'Hypovereinsbank',
        'parser_module': 'parsers.hypovereinsbank_parser_v2',
        'parser_class': 'HypoVereinsbankParser',
        'file_pattern': r'HV.*Kontoauszug.*(\d{2}\.\d{2}\.\d{2})\.pdf',
        'iban': 'DE22741200710006407420'
    },
    'sparkasse': {
        'folder': 'Sparkasse',
        'parser_module': 'parsers.sparkasse_parser',
        'parser_class': 'SparkasseParser',
        'file_pattern': r'SPK.*Auszug.*(\d{2}\.\d{2}\.\d{2})\.pdf',
        'iban': 'DE63741500000760036467'
    },
    'vrbank': {
        'folder': 'VR Bank Landau',
        'parser_module': 'parsers.vrbank_landau_parser',
        'parser_class': 'VRBankLandauParser',
        'file_pattern': r'VR.*Bank.*Auszug.*(\d{2}\.\d{2}\.\d{2})\.pdf',
        'iban': 'DE76741910000000303585'
    },
    'genobank_auto': {
        'folder': 'Genobank Auto Greiner',
        'parser_module': 'parsers.genobank_universal_parser',
        'parser_class': 'GenobankUniversalParser',
        'file_pattern': r'Genobank.*Auto.*Greiner.*(\d{2}\.\d{2}\.\d{2})\.pdf',
        'iban': 'DE68741900000001501500'
    },
    'genobank_autohaus': {
        'folder': 'Genobank Autohaus Greiner',
        'parser_module': 'parsers.genobank_universal_parser',
        'parser_class': 'GenobankUniversalParser',
        'file_pattern': r'Genobank.*Autohaus.*Greiner.*(\d{2}\.\d{2}\.\d{2})\.pdf',
        'iban': 'DE27741900000000057908'
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_konto_id_by_iban(conn, iban):
    """Konto-ID anhand IBAN ermitteln"""
    cursor = conn.cursor()
    ph = sql_placeholder()
    cursor.execute(f"SELECT id, kontoname FROM konten WHERE iban = {ph}", (iban,))
    result = cursor.fetchone()
    if result:
        # HybridRow unterstützt sowohl Index als auch Dict-Zugriff
        return (result[0] if hasattr(result, '__getitem__') else result['id'], 
                result[1] if hasattr(result, '__getitem__') else result['kontoname'])
    return (None, None)

def transaction_exists(conn, konto_id, buchungsdatum, betrag, verwendungszweck):
    """Prüfen ob Transaktion bereits existiert"""
    cursor = conn.cursor()
    # Vereinfachter Check: Datum + Betrag + erste 50 Zeichen Verwendungszweck
    vzweck_short = verwendungszweck[:50] if verwendungszweck else ''
    ph = sql_placeholder()
    
    # PostgreSQL: SUBSTRING() statt SUBSTR()
    is_pg = get_db_type() == 'postgresql'
    substr_func = 'SUBSTRING' if is_pg else 'SUBSTR'
    
    query = f"""
        SELECT COUNT(*) FROM transaktionen 
        WHERE konto_id = {ph} 
        AND buchungsdatum = {ph} 
        AND ABS(betrag - {ph}) < 0.01
        AND {substr_func}(verwendungszweck, 1, 50) = {ph}
    """
    cursor.execute(query, (konto_id, buchungsdatum, betrag, vzweck_short))
    result = cursor.fetchone()
    count = result[0] if hasattr(result, '__getitem__') else result['count']
    return count > 0

def saldo_exists(conn, konto_id, datum):
    """Prüfen ob Saldo für Datum bereits existiert"""
    cursor = conn.cursor()
    ph = sql_placeholder()
    cursor.execute(
        f"SELECT COUNT(*) FROM salden WHERE konto_id = {ph} AND datum = {ph}",
        (konto_id, datum)
    )
    result = cursor.fetchone()
    count = result[0] if hasattr(result, '__getitem__') else result['count']
    return count > 0

def get_last_import_date(conn, konto_id):
    """Letztes Import-Datum für ein Konto ermitteln"""
    cursor = conn.cursor()
    ph = sql_placeholder()
    cursor.execute(f"SELECT MAX(datum) FROM salden WHERE konto_id = {ph}", (konto_id,))
    result = cursor.fetchone()
    if result:
        max_date = result[0] if hasattr(result, '__getitem__') else result['max']
        return max_date
    return None

def parse_date_from_filename(filename, pattern):
    """Datum aus Dateiname extrahieren (DD.MM.YY Format)"""
    match = re.search(pattern, filename)
    if match:
        date_str = match.group(1)
        try:
            return datetime.strptime(date_str, '%d.%m.%y').date()
        except:
            return None
    return None

def get_parser(bank_config):
    """Parser-Instanz für eine Bank erstellen"""
    module_name = bank_config['parser_module']
    module = __import__(module_name, fromlist=[bank_config['parser_class']])
    parser_class = getattr(module, bank_config['parser_class'])
    return parser_class

# ============================================================================
# IMPORT FUNCTIONS
# ============================================================================

def import_single_pdf(pdf_path, bank_key, bank_config):
    """Einzelnes PDF importieren"""
    filename = os.path.basename(pdf_path)
    print(f"\n  📄 {filename}")
    
    try:
        # Parser laden und PDF parsen
        ParserClass = get_parser(bank_config)
        parser = ParserClass(pdf_path)
        result = parser.parse()
        
        # IBAN aus Config verwenden falls Parser keine liefert
        iban = (result.get('iban') if isinstance(result, dict) else None) or bank_config['iban']
        
        if not iban:
            print(f"     ❌ Keine IBAN gefunden")
            return {'imported': 0, 'skipped': 0, 'error': 'Keine IBAN'}
        
        # DB-Verbindung (PostgreSQL via api.db_connection)
        conn = get_db()
        cursor = conn.cursor()
        ph = sql_placeholder()
        
        try:
            # Konto-ID ermitteln
            konto_id, kontoname = get_konto_id_by_iban(conn, iban)
            
            if not konto_id:
                print(f"     ❌ Konto nicht gefunden: {iban}")
                return {'imported': 0, 'skipped': 0, 'error': f'Konto {iban} nicht gefunden'}
            
            # Transaktionen importieren
            tx_imported = 0
            tx_skipped = 0
            
            transactions = result.get('transactions', []) if isinstance(result, dict) else result
            
            for tx in transactions:
                # Unterstütze sowohl dicts als auch Transaction-Objekte
                if hasattr(tx, 'buchungsdatum'):
                    # Transaction-Objekt
                    buchungsdatum = tx.buchungsdatum
                    betrag = tx.betrag
                    verwendungszweck = tx.verwendungszweck or ''
                    valutadatum = tx.valutadatum or buchungsdatum
                else:
                    # Dict
                    buchungsdatum = tx.get('buchungsdatum') or tx.get('datum')
                    betrag = tx.get('betrag', 0)
                    verwendungszweck = tx.get('verwendungszweck', '')
                    valutadatum = tx.get('valutadatum') or buchungsdatum
                
                if not buchungsdatum:
                    continue
                
                # Duplikat-Check
                if transaction_exists(conn, konto_id, buchungsdatum, betrag, verwendungszweck):
                    tx_skipped += 1
                    continue
                
                # Transaktion einfügen (PostgreSQL: %s statt ?)
                query = f"""
                    INSERT INTO transaktionen (
                        konto_id, buchungsdatum, valutadatum, betrag,
                        verwendungszweck, import_quelle, import_datei
                    ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                """
                cursor.execute(query, (
                    konto_id, buchungsdatum, valutadatum, betrag,
                    verwendungszweck, 'PDF', filename
                ))
                tx_imported += 1
            
            # Saldo importieren
            saldo_imported = False
            endsaldo = result.get('endsaldo') if isinstance(result, dict) else (parser.endsaldo if hasattr(parser, 'endsaldo') else None)
            saldo_datum = result.get('saldo_datum') if isinstance(result, dict) else None
            
            # Falls kein saldo_datum, letztes Buchungsdatum verwenden
            if endsaldo is not None and not saldo_datum and transactions:
                last_tx = transactions[-1]
                saldo_datum = last_tx.buchungsdatum if hasattr(last_tx, 'buchungsdatum') else last_tx.get('buchungsdatum')
            
            if endsaldo is not None and saldo_datum:
                if not saldo_exists(conn, konto_id, saldo_datum):
                    query = f"""
                        INSERT INTO salden (konto_id, datum, saldo, quelle, import_datei)
                        VALUES ({ph}, {ph}, {ph}, {ph}, {ph})
                    """
                    cursor.execute(query, (konto_id, saldo_datum, endsaldo, 'PDF', filename))
                    saldo_imported = True
            
            conn.commit()
        finally:
            conn.close()
        
        # Status ausgeben
        status_parts = []
        if tx_imported > 0:
            status_parts.append(f"{tx_imported} TX")
        if tx_skipped > 0:
            status_parts.append(f"{tx_skipped} skip")
        if saldo_imported:
            status_parts.append(f"Saldo {endsaldo:,.2f}€")
        
        if status_parts:
            print(f"     ✅ {' | '.join(status_parts)}")
        else:
            print(f"     ⏭️  Bereits importiert")
        
        return {'imported': tx_imported, 'skipped': tx_skipped, 'saldo': saldo_imported}
        
    except Exception as e:
        print(f"     ❌ Fehler: {e}")
        return {'imported': 0, 'skipped': 0, 'error': str(e)}

def import_bank(bank_key, days_back=7):
    """Alle neuen PDFs einer Bank importieren"""
    if bank_key not in BANK_CONFIGS:
        print(f"❌ Unbekannte Bank: {bank_key}")
        return
    
    config = BANK_CONFIGS[bank_key]
    folder_path = os.path.join(BASE_PATH, config['folder'])
    
    print(f"\n{'='*60}")
    print(f"📁 {config['folder']}")
    print(f"{'='*60}")
    
    if not os.path.exists(folder_path):
        print(f"   ❌ Ordner nicht gefunden: {folder_path}")
        return
    
    # Alle PDFs finden
    pdf_files = list(Path(folder_path).glob('*.pdf'))
    
    if not pdf_files:
        print(f"   Keine PDFs gefunden")
        return
    
    # Nach Datum filtern (nur letzte X Tage)
    cutoff_date = datetime.now().date() - timedelta(days=days_back)
    
    relevant_pdfs = []
    for pdf in pdf_files:
        file_date = parse_date_from_filename(pdf.name, config['file_pattern'])
        if file_date and file_date >= cutoff_date:
            relevant_pdfs.append((pdf, file_date))
    
    # Nach Datum sortieren
    relevant_pdfs.sort(key=lambda x: x[1])
    
    print(f"   📋 {len(relevant_pdfs)} PDFs der letzten {days_back} Tage")
    
    total_imported = 0
    total_skipped = 0
    
    for pdf_path, file_date in relevant_pdfs:
        result = import_single_pdf(str(pdf_path), bank_key, config)
        total_imported += result.get('imported', 0)
        total_skipped += result.get('skipped', 0)
    
    print(f"\n   📊 Gesamt: {total_imported} importiert, {total_skipped} übersprungen")

def import_all_banks(days_back=7):
    """Alle Banken importieren"""
    print("\n" + "="*70)
    print("🏦 UNIVERSAL BANK PDF IMPORT")
    print(f"   Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Zeitraum: Letzte {days_back} Tage")
    print("="*70)
    
    for bank_key in BANK_CONFIGS.keys():
        try:
            import_bank(bank_key, days_back)
        except Exception as e:
            print(f"\n❌ Fehler bei {bank_key}: {e}")
    
    print("\n" + "="*70)
    print("✅ IMPORT ABGESCHLOSSEN")
    print("="*70 + "\n")

def import_today():
    """Nur heutige PDFs importieren (für häufige Cron-Läufe)"""
    print("\n" + "="*70)
    print("🏦 BANK PDF IMPORT - HEUTE")
    print(f"   Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    today = datetime.now().date()
    
    for bank_key, config in BANK_CONFIGS.items():
        folder_path = os.path.join(BASE_PATH, config['folder'])
        
        if not os.path.exists(folder_path):
            continue
        
        print(f"\n📁 {config['folder']}")
        
        # Alle PDFs finden
        pdf_files = list(Path(folder_path).glob('*.pdf'))
        
        for pdf in pdf_files:
            file_date = parse_date_from_filename(pdf.name, config['file_pattern'])
            
            # Nur heute oder gestern (falls vor 8 Uhr)
            if file_date and file_date >= today - timedelta(days=1):
                import_single_pdf(str(pdf), bank_key, config)
    
    print("\n" + "="*70)
    print("✅ IMPORT ABGESCHLOSSEN")
    print("="*70 + "\n")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Universal Bank PDF Import')
    parser.add_argument('--bank', choices=list(BANK_CONFIGS.keys()) + ['all'],
                        default='all', help='Welche Bank importieren')
    parser.add_argument('--days', type=int, default=7,
                        help='Wie viele Tage zurück (default: 7)')
    parser.add_argument('--today', action='store_true',
                        help='Nur heutige/gestrige PDFs')
    
    args = parser.parse_args()
    
    if args.today:
        import_today()
    elif args.bank == 'all':
        import_all_banks(args.days)
    else:
        import_bank(args.bank, args.days)
