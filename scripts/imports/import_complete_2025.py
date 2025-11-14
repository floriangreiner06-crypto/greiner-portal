#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MASTER IMPORT SCRIPT - Komplettes Jahr 2025
Importiert systematisch alle Kontoauszüge mit den richtigen Parsern
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import re

# Pfade
BASE_DIR = Path('/opt/greiner-portal')
DB_PATH = BASE_DIR / 'data' / 'greiner_controlling.db'
PDF_DIR = BASE_DIR / 'data' / 'kontoauszuege'
LOG_DIR = BASE_DIR / 'logs' / 'imports'

# Logging Setup
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / f'master_import_2025_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Parser Imports
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'parsers'))

# ============================================================================
# SPARKASSE PARSER (aus Prototyp)
# ============================================================================
import pdfplumber

def parse_sparkasse_pdf(pdf_path):
    """Sparkasse Parser mit korrektem Format"""
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            # IBAN extrahieren
            iban_match = re.search(r'(DE\d{2}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{2})', full_text)
            iban = iban_match.group(1).replace(" ", "") if iban_match else None
            
            lines = full_text.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Kein Leerzeichen zwischen Datum und Text!
                date_match = re.match(r'^(\d{2}\.\d{2}\.\d{4})(.+)', line)
                
                if date_match:
                    datum = date_match.group(1)
                    rest = date_match.group(2).strip()
                    
                    if 'Kontostand am' in rest or not rest:
                        continue
                    
                    betrag_match = re.search(r'([-]?\d{1,3}(?:\.\d{3})*,\d{2})$', line)
                    
                    if betrag_match:
                        betrag_str = betrag_match.group(1)
                        betrag = float(betrag_str.replace('.', '').replace(',', '.'))
                        
                        verwendungszweck = line[len(datum):betrag_match.start()].strip()
                        
                        # Sammle zusätzliche Zeilen
                        zusatz_lines = []
                        j = i + 1
                        while j < len(lines) and j < i + 5:
                            next_line = lines[j].strip()
                            if re.match(r'^\d{2}\.\d{2}\.\d{4}', next_line):
                                break
                            if not next_line or 'Sparkasse Deggendorf' in next_line:
                                break
                            zusatz_lines.append(next_line)
                            j += 1
                        
                        if zusatz_lines:
                            verwendungszweck = verwendungszweck + " " + " ".join(zusatz_lines)
                        
                        # Datum konvertieren
                        try:
                            datum_obj = datetime.strptime(datum, '%d.%m.%Y')
                            datum_iso = datum_obj.strftime('%Y-%m-%d')
                        except:
                            datum_iso = datum
                        
                        transactions.append({
                            'buchungsdatum': datum_iso,
                            'valutadatum': datum_iso,
                            'verwendungszweck': verwendungszweck[:500],
                            'betrag': betrag,
                            'iban': iban
                        })
            
            return transactions
            
    except Exception as e:
        logger.error(f"Fehler beim Parsen Sparkasse: {e}")
        return []

# ============================================================================
# HYPOVEREINSBANK PARSER (aus Prototyp)
# ============================================================================
def parse_hypovereinsbank_pdf(pdf_path):
    """HypoVereinsbank Parser mit korrektem Format"""
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            iban = None
            if pdf.pages:
                first_text = pdf.pages[0].extract_text()
                iban_match = re.search(r'IBAN\s+(DE\d{20})', first_text)
                iban = iban_match.group(1) if iban_match else None

            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                    
                lines = text.split('\n')
                i = 0
                
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Format: DD.MM.YYYY DD.MM.YYYY TEXT BETRAG EUR
                    match = re.match(r'^(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2}\.\d{4})\s+(.+?)\s+([-]?\d{1,3}(?:\.\d{3})*,\d{2})\s+EUR\s*$', line)
                    
                    if match:
                        buchungsdatum = match.group(1)
                        valutadatum = match.group(2)
                        transaktionstyp = match.group(3).strip()
                        betrag_str = match.group(4)
                        
                        betrag = float(betrag_str.replace('.', '').replace(',', '.'))
                        
                        verwendungszweck_lines = [transaktionstyp]
                        i += 1
                        
                        while i < len(lines):
                            next_line = lines[i].strip()
                            
                            if re.match(r'^\d{2}\.\d{2}\.\d{4}\s+\d{2}\.\d{2}\.\d{4}', next_line):
                                break
                            
                            if not next_line or 'Seite' in next_line or 'https://' in next_line:
                                i += 1
                                break
                                
                            if next_line:
                                verwendungszweck_lines.append(next_line)
                            
                            i += 1

                        verwendungszweck = ' '.join(verwendungszweck_lines)
                        
                        # Datum konvertieren
                        try:
                            datum_obj = datetime.strptime(buchungsdatum, '%d.%m.%Y')
                            datum_iso = datum_obj.strftime('%Y-%m-%d')
                            valuta_obj = datetime.strptime(valutadatum, '%d.%m.%Y')
                            valuta_iso = valuta_obj.strftime('%Y-%m-%d')
                        except:
                            datum_iso = buchungsdatum
                            valuta_iso = valutadatum
                        
                        transactions.append({
                            'buchungsdatum': datum_iso,
                            'valutadatum': valuta_iso,
                            'verwendungszweck': verwendungszweck[:500],
                            'betrag': betrag,
                            'iban': iban
                        })
                    else:
                        i += 1

            return transactions

    except Exception as e:
        logger.error(f"Fehler beim Parsen HypoVereinsbank: {e}")
        return []

# ============================================================================
# GENOBANK PARSER (existierender)
# ============================================================================
try:
    from parsers.genobank_universal_parser import GenobankUniversalParser
    
    def parse_genobank_pdf(pdf_path):
        """Wrapper für Genobank Parser"""
        parser = GenobankUniversalParser(pdf_path)
        return parser.parse()
except ImportError:
    logger.warning("Genobank Parser nicht gefunden, verwende Fallback")
    def parse_genobank_pdf(pdf_path):
        return []

# ============================================================================
# VR BANK PARSER (existierender oder neu)
# ============================================================================
def parse_vrbank_pdf(pdf_path):
    """VR Bank Parser - ähnlich wie Genobank"""
    # Verwende erstmal Genobank Parser, da Format ähnlich
    return parse_genobank_pdf(pdf_path)

# ============================================================================
# HAUPTFUNKTIONEN
# ============================================================================

def detect_bank_from_pdf(pdf_path: Path) -> Optional[str]:
    """Erkennt Bank aus PDF-Inhalt"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return None
                
            first_page = pdf.pages[0].extract_text()
            if not first_page:
                return None
                
            # Check für verschiedene Banken
            if 'Sparkasse' in first_page:
                return 'sparkasse'
            elif 'HypoVereinsbank' in first_page or 'UniCredit' in first_page:
                return 'hypovereinsbank'
            elif 'Genobank' in first_page or 'Genossenschaftsbank' in first_page:
                return 'genobank'
            elif 'VR Bank' in first_page or 'VR-Bank' in first_page:
                return 'vrbank'
            
            # IBAN-basierte Erkennung
            iban_match = re.search(r'DE\d{2}[\s]?(\d{4})', first_page)
            if iban_match:
                blz = iban_match.group(1)
                if blz == '7415':  # Sparkasse Deggendorf
                    return 'sparkasse'
                elif blz == '7412':  # HypoVereinsbank
                    return 'hypovereinsbank'
                elif blz == '7419':  # Genobank/VR Bank
                    # Weitere Unterscheidung nötig
                    if 'VR Bank' in first_page:
                        return 'vrbank'
                    return 'genobank'
                        
    except Exception as e:
        logger.error(f"Fehler bei Bank-Erkennung: {e}")
    
    return None

def get_parser_for_bank(bank: str):
    """Gibt den richtigen Parser für die Bank zurück"""
    parsers = {
        'sparkasse': parse_sparkasse_pdf,
        'hypovereinsbank': parse_hypovereinsbank_pdf,
        'genobank': parse_genobank_pdf,
        'vrbank': parse_vrbank_pdf
    }
    return parsers.get(bank)

def get_konto_id_from_iban(conn, iban: str) -> Optional[int]:
    """Findet Konto-ID anhand der IBAN"""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM konten WHERE iban = ?", (iban,))
    result = cursor.fetchone()
    return result[0] if result else None

def import_transactions(conn, konto_id: int, transactions: List[Dict]) -> int:
    """Importiert Transaktionen in DB (mit Duplikat-Check)"""
    cursor = conn.cursor()
    imported = 0
    
    for trans in transactions:
        # Check ob bereits existiert
        cursor.execute("""
            SELECT COUNT(*) FROM transaktionen 
            WHERE konto_id = ? 
            AND buchungsdatum = ? 
            AND betrag = ?
            AND verwendungszweck = ?
        """, (konto_id, trans['buchungsdatum'], trans['betrag'], trans['verwendungszweck']))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO transaktionen (
                    konto_id, buchungsdatum, valutadatum, 
                    verwendungszweck, betrag, waehrung
                ) VALUES (?, ?, ?, ?, ?, 'EUR')
            """, (
                konto_id, 
                trans['buchungsdatum'],
                trans.get('valutadatum', trans['buchungsdatum']),
                trans['verwendungszweck'],
                trans['betrag']
            ))
            imported += 1
    
    conn.commit()
    return imported

def process_pdf(conn, pdf_path: Path) -> Dict:
    """Verarbeitet ein einzelnes PDF"""
    result = {
        'pdf': pdf_path.name,
        'bank': None,
        'iban': None,
        'konto_id': None,
        'transactions': 0,
        'imported': 0,
        'error': None
    }
    
    try:
        # Bank erkennen
        bank = detect_bank_from_pdf(pdf_path)
        if not bank:
            result['error'] = "Bank nicht erkannt"
            return result
        
        result['bank'] = bank
        
        # Parser holen
        parser = get_parser_for_bank(bank)
        if not parser:
            result['error'] = f"Kein Parser für {bank}"
            return result
        
        # PDF parsen
        transactions = parser(str(pdf_path))
        if not transactions:
            result['error'] = "Keine Transaktionen gefunden"
            return result
        
        result['transactions'] = len(transactions)
        
        # IBAN und Konto-ID
        iban = transactions[0].get('iban')
        if not iban:
            result['error'] = "Keine IBAN gefunden"
            return result
        
        result['iban'] = iban
        
        konto_id = get_konto_id_from_iban(conn, iban)
        if not konto_id:
            result['error'] = f"Konto für IBAN {iban} nicht gefunden"
            return result
        
        result['konto_id'] = konto_id
        
        # Importieren
        imported = import_transactions(conn, konto_id, transactions)
        result['imported'] = imported
        
        if imported > 0:
            logger.info(f"✅ {pdf_path.name}: {imported}/{len(transactions)} importiert")
        
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"❌ {pdf_path.name}: {e}")
    
    return result

def main():
    """Hauptfunktion - importiert alle 2025 PDFs"""
    
    logger.info("="*70)
    logger.info("🚀 MASTER IMPORT 2025 - Start")
    logger.info("="*70)
    
    # DB-Verbindung
    conn = sqlite3.connect(str(DB_PATH))
    
    # Backup erstellen
    backup_path = DB_PATH.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    logger.info(f"📦 Erstelle Backup: {backup_path.name}")
    import shutil
    shutil.copy(DB_PATH, backup_path)
    
    # Alle PDFs sammeln
    all_pdfs = list(PDF_DIR.glob('**/*.pdf'))
    logger.info(f"📄 {len(all_pdfs)} PDFs gefunden")
    
    # Nach 2025 filtern (aus Inhalt, nicht Dateiname!)
    pdfs_2025 = []
    
    for pdf_path in all_pdfs:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if pdf.pages:
                    text = pdf.pages[0].extract_text()
                    if text and '2025' in text:
                        pdfs_2025.append(pdf_path)
        except:
            continue
    
    logger.info(f"📅 {len(pdfs_2025)} PDFs mit 2025-Daten gefunden")
    
    # Statistik
    stats = {
        'total': len(pdfs_2025),
        'success': 0,
        'failed': 0,
        'total_imported': 0
    }
    
    # Alle PDFs verarbeiten
    for i, pdf_path in enumerate(pdfs_2025, 1):
        logger.info(f"\n[{i}/{len(pdfs_2025)}] Verarbeite: {pdf_path.name}")
        
        result = process_pdf(conn, pdf_path)
        
        if result['error']:
            stats['failed'] += 1
            logger.warning(f"   ⚠️ {result['error']}")
        else:
            stats['success'] += 1
            stats['total_imported'] += result['imported']
    
    # Finale Statistik
    logger.info("\n" + "="*70)
    logger.info("📊 IMPORT ABGESCHLOSSEN")
    logger.info("="*70)
    logger.info(f"✅ Erfolgreich: {stats['success']}/{stats['total']} PDFs")
    logger.info(f"❌ Fehler: {stats['failed']} PDFs")
    logger.info(f"💾 Importiert: {stats['total_imported']} Transaktionen")
    
    # Salden-Check
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            k.kontoname,
            COUNT(t.id) as trans_2025,
            MIN(t.buchungsdatum) as von,
            MAX(t.buchungsdatum) as bis
        FROM konten k
        LEFT JOIN transaktionen t ON k.id = t.konto_id 
            AND t.buchungsdatum >= '2025-01-01'
        WHERE k.aktiv = 1
        GROUP BY k.id
        ORDER BY k.kontoname
    """)
    
    logger.info("\n📊 KONTEN-ÜBERSICHT 2025:")
    logger.info("-"*70)
    
    for row in cursor.fetchall():
        if row[1] > 0:
            logger.info(f"{row[0]:<30} {row[1]:>6} Trans. ({row[2]} bis {row[3]})")
        else:
            logger.info(f"{row[0]:<30} {'KEINE':>6} Trans.")
    
    conn.close()
    
    logger.info("\n✅ Master-Import abgeschlossen!")
    logger.info(f"📝 Log: {log_file}")
    
    return stats

if __name__ == "__main__":
    main()
