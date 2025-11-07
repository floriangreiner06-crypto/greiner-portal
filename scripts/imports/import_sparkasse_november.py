#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sparkasse November-Import für Greiner Portal
============================================
Importiert November-Daten von Sparkasse Deggendorf (Konto 76003647)

Usage:
    python3 import_sparkasse_november.py [--dry-run]

Author: Claude AI
Version: 1.0
Date: 2025-11-07
"""

import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import re

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_sparkasse_november.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Pfade
BASE_DIR = Path("/opt/greiner-portal")
DB_PATH = BASE_DIR / "data" / "greiner_controlling.db"
SPARKASSE_DIR = Path("/mnt/buchhaltung/Buchhaltung/Kontoauszüge/Sparkasse/")

class SparkasseNovemberImporter:
    """Importiert Sparkasse November-Daten"""
    
    def __init__(self, db_path: Path, pdf_dir: Path, dry_run: bool = False):
        self.db_path = db_path
        self.pdf_dir = pdf_dir
        self.dry_run = dry_run
        self.conn = None
        self.cursor = None
        
    def __enter__(self):
        """Context Manager - Verbindung öffnen"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.cursor = self.conn.cursor()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager - Verbindung schließen"""
        if self.conn:
            if exc_type is None and not self.dry_run:
                self.conn.commit()
            self.conn.close()
    
    def find_november_pdfs(self) -> List[Path]:
        """Findet alle November-PDFs"""
        logger.info("🔍 Suche nach Sparkasse November-PDFs...")
        
        patterns = [
            "*2025*11*.pdf",
            "*Nov*2025*.pdf",
            "*11.25*.pdf",
            "*0760036467*2025*.pdf"  # Kontonummer
        ]
        
        pdf_files = []
        for pattern in patterns:
            pdf_files.extend(self.pdf_dir.glob(pattern))
        
        # Duplikate entfernen und sortieren
        pdf_files = sorted(set(pdf_files))
        
        logger.info(f"✅ {len(pdf_files)} PDF-Dateien gefunden")
        for pdf in pdf_files:
            logger.info(f"   📄 {pdf.name}")
        
        return pdf_files
    
    def get_konto_id(self, iban: str = "DE87741500000760036467") -> Optional[int]:
        """Holt Konto-ID für Sparkasse"""
        self.cursor.execute("""
            SELECT id FROM konten 
            WHERE iban = ? OR kontoname LIKE '%76003647%' OR kontoname LIKE '%Sparkasse%'
            LIMIT 1
        """, (iban,))
        
        result = self.cursor.fetchone()
        if result:
            logger.info(f"✅ Konto-ID gefunden: {result[0]}")
            return result[0]
        
        logger.error(f"❌ Kein Konto gefunden für IBAN: {iban}")
        return None
    
    def parse_sparkasse_pdf(self, pdf_path: Path) -> List[Dict]:
        """
        Parst Sparkasse-PDF mit einfachem Parser
        
        Sparkasse-Format:
            DD.MM.YYYY Verwendungszweck... Betrag
        """
        logger.info(f"📄 Parse: {pdf_path.name}")
        
        try:
            import pdfplumber
            
            transactions = []
            
            with pdfplumber.open(str(pdf_path)) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
            
            # IBAN extrahieren
            iban_match = re.search(r'(DE\d{20})', full_text)
            iban = iban_match.group(1) if iban_match else None
            
            logger.debug(f"IBAN: {iban}")
            
            # Zeilen verarbeiten
            lines = full_text.split('\n')
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                # Suche nach Datum am Zeilenanfang
                date_match = re.match(r'^(\d{2}\.\d{2}\.\d{4})', line)
                
                if date_match:
                    datum_str = date_match.group(1)
                    
                    # Betrag am Zeilenende (mit - für Soll)
                    amount_match = re.search(r'([-]?\d{1,3}(?:\.\d{3})*,\d{2})\s*$', line)
                    
                    if amount_match:
                        betrag_str = amount_match.group(1)
                        
                        # Verwendungszweck ist zwischen Datum und Betrag
                        verwendungszweck_match = re.match(
                            r'^\d{2}\.\d{2}\.\d{4}\s+(.+?)\s+[-]?\d{1,3}(?:\.\d{3})*,\d{2}\s*$', 
                            line
                        )
                        
                        if verwendungszweck_match:
                            verwendungszweck = verwendungszweck_match.group(1).strip()
                            
                            # Sammle Folgezeilen (mehrzeiliger Verwendungszweck)
                            j = i + 1
                            while j < len(lines):
                                next_line = lines[j].strip()
                                
                                # Stop wenn neue Transaktion oder Leerzeile
                                if re.match(r'^\d{2}\.\d{2}\.\d{4}', next_line) or not next_line:
                                    break
                                
                                # Kein Betrag am Ende = Verwendungszweck
                                if not re.search(r'[-]?\d{1,3}(?:\.\d{3})*,\d{2}\s*$', next_line):
                                    verwendungszweck += " " + next_line
                                    j += 1
                                else:
                                    break
                            
                            # Datum parsen
                            try:
                                buchungsdatum = datetime.strptime(datum_str, '%d.%m.%Y').date()
                            except ValueError:
                                logger.warning(f"⚠️ Ungültiges Datum: {datum_str}")
                                i += 1
                                continue
                            
                            # Betrag parsen
                            betrag_str = betrag_str.replace('.', '').replace(',', '.')
                            betrag = float(betrag_str)
                            
                            # Transaktion speichern
                            transaction = {
                                'buchungsdatum': buchungsdatum,
                                'valutadatum': buchungsdatum,  # Sparkasse hat oft nur ein Datum
                                'verwendungszweck': verwendungszweck[:500],  # Max 500 Zeichen
                                'betrag': betrag,
                                'iban': iban,
                                'pdf_quelle': pdf_path.name
                            }
                            
                            transactions.append(transaction)
                            logger.debug(f"✓ {buchungsdatum} | {betrag:.2f} EUR | {verwendungszweck[:50]}...")
                            
                            i = j
                            continue
                
                i += 1
            
            logger.info(f"✅ {len(transactions)} Transaktionen gefunden")
            return transactions
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Parsen: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def import_transactions(self, transactions: List[Dict], konto_id: int) -> Dict:
        """Importiert Transaktionen in DB"""
        stats = {
            'imported': 0,
            'duplicates': 0,
            'errors': 0
        }
        
        for trans in transactions:
            try:
                # Prüfe auf Duplikat
                self.cursor.execute("""
                    SELECT COUNT(*) FROM transaktionen
                    WHERE konto_id = ?
                    AND buchungsdatum = ?
                    AND betrag = ?
                    AND verwendungszweck = ?
                """, (
                    konto_id,
                    trans['buchungsdatum'],
                    trans['betrag'],
                    trans['verwendungszweck']
                ))
                
                if self.cursor.fetchone()[0] > 0:
                    logger.debug(f"⊘ Duplikat: {trans['buchungsdatum']} | {trans['betrag']:.2f} EUR")
                    stats['duplicates'] += 1
                    continue
                
                # Importieren
                if not self.dry_run:
                    self.cursor.execute("""
                        INSERT INTO transaktionen (
                            konto_id, buchungsdatum, valutadatum,
                            verwendungszweck, betrag, waehrung,
                            pdf_quelle, importiert_am
                        ) VALUES (?, ?, ?, ?, ?, 'EUR', ?, ?)
                    """, (
                        konto_id,
                        trans['buchungsdatum'],
                        trans['valutadatum'],
                        trans['verwendungszweck'],
                        trans['betrag'],
                        trans['pdf_quelle'],
                        datetime.now()
                    ))
                
                stats['imported'] += 1
                logger.debug(f"✓ Importiert: {trans['buchungsdatum']} | {trans['betrag']:.2f} EUR")
                
            except Exception as e:
                logger.error(f"❌ Fehler beim Import: {e}")
                stats['errors'] += 1
        
        return stats
    
    def get_current_status(self, konto_id: int) -> Dict:
        """Holt aktuellen Status des Kontos"""
        # Anzahl Transaktionen
        self.cursor.execute("""
            SELECT COUNT(*) FROM transaktionen WHERE konto_id = ?
        """, (konto_id,))
        total_trans = self.cursor.fetchone()[0]
        
        # November-Transaktionen
        self.cursor.execute("""
            SELECT COUNT(*) FROM transaktionen 
            WHERE konto_id = ? AND buchungsdatum >= '2025-11-01'
        """, (konto_id,))
        nov_trans = self.cursor.fetchone()[0]
        
        # Aktueller Saldo
        self.cursor.execute("""
            SELECT SUM(betrag) FROM transaktionen WHERE konto_id = ?
        """, (konto_id,))
        saldo = self.cursor.fetchone()[0] or 0.0
        
        # Letztes Datum
        self.cursor.execute("""
            SELECT MAX(buchungsdatum) FROM transaktionen WHERE konto_id = ?
        """, (konto_id,))
        letztes_datum = self.cursor.fetchone()[0]
        
        return {
            'total_trans': total_trans,
            'nov_trans': nov_trans,
            'saldo': saldo,
            'letztes_datum': letztes_datum
        }
    
    def run(self):
        """Hauptprozess"""
        logger.info("🚀 SPARKASSE NOVEMBER-IMPORT")
        logger.info(f"{'='*70}")
        
        if self.dry_run:
            logger.info("⚠️  DRY-RUN MODUS - Keine Änderungen werden gespeichert")
        
        # 1. Konto-ID holen
        konto_id = self.get_konto_id()
        if not konto_id:
            logger.error("❌ Konto nicht gefunden - Abbruch")
            return
        
        # 2. Status VORHER
        status_vorher = self.get_current_status(konto_id)
        logger.info(f"\n📊 STATUS VORHER:")
        logger.info(f"   Transaktionen gesamt: {status_vorher['total_trans']}")
        logger.info(f"   November-Transaktionen: {status_vorher['nov_trans']}")
        logger.info(f"   Aktueller Saldo: {status_vorher['saldo']:,.2f} EUR")
        logger.info(f"   Letztes Datum: {status_vorher['letztes_datum']}")
        
        # 3. PDFs finden
        pdf_files = self.find_november_pdfs()
        if not pdf_files:
            logger.warning("⚠️  Keine November-PDFs gefunden")
            return
        
        # 4. PDFs verarbeiten
        logger.info(f"\n📄 VERARBEITE {len(pdf_files)} PDF-DATEIEN:")
        logger.info(f"{'-'*70}")
        
        total_stats = {
            'imported': 0,
            'duplicates': 0,
            'errors': 0
        }
        
        for pdf_file in pdf_files:
            logger.info(f"\n📄 {pdf_file.name}")
            
            # Parse PDF
            transactions = self.parse_sparkasse_pdf(pdf_file)
            
            if not transactions:
                logger.warning("⚠️  Keine Transaktionen gefunden")
                continue
            
            # Importiere Transaktionen
            stats = self.import_transactions(transactions, konto_id)
            
            logger.info(f"   ✅ Importiert: {stats['imported']}")
            logger.info(f"   ⊘ Duplikate: {stats['duplicates']}")
            if stats['errors'] > 0:
                logger.info(f"   ❌ Fehler: {stats['errors']}")
            
            # Summiere Stats
            for key in total_stats:
                total_stats[key] += stats[key]
        
        # 5. Status NACHHER
        if not self.dry_run:
            status_nachher = self.get_current_status(konto_id)
            logger.info(f"\n📊 STATUS NACHHER:")
            logger.info(f"   Transaktionen gesamt: {status_nachher['total_trans']}")
            logger.info(f"   November-Transaktionen: {status_nachher['nov_trans']}")
            logger.info(f"   Aktueller Saldo: {status_nachher['saldo']:,.2f} EUR")
            logger.info(f"   Letztes Datum: {status_nachher['letztes_datum']}")
            
            logger.info(f"\n📈 ÄNDERUNGEN:")
            logger.info(f"   Neue Transaktionen: +{status_nachher['total_trans'] - status_vorher['total_trans']}")
            logger.info(f"   Neue November-Trans.: +{status_nachher['nov_trans'] - status_vorher['nov_trans']}")
            logger.info(f"   Saldo-Änderung: {status_nachher['saldo'] - status_vorher['saldo']:+,.2f} EUR")
        
        # 6. Zusammenfassung
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ IMPORT ABGESCHLOSSEN")
        logger.info(f"{'='*70}")
        logger.info(f"Importiert:  {total_stats['imported']}")
        logger.info(f"Duplikate:   {total_stats['duplicates']}")
        if total_stats['errors'] > 0:
            logger.info(f"Fehler:      {total_stats['errors']}")

def main():
    """Hauptfunktion"""
    # Parse Arguments
    dry_run = '--dry-run' in sys.argv
    
    # Prüfe Abhängigkeiten
    try:
        import pdfplumber
    except ImportError:
        logger.error("❌ pdfplumber nicht installiert!")
        logger.error("   Installieren mit: pip install pdfplumber --break-system-packages")
        sys.exit(1)
    
    # Prüfe Pfade
    if not DB_PATH.exists():
        logger.error(f"❌ Datenbank nicht gefunden: {DB_PATH}")
        sys.exit(1)
    
    if not SPARKASSE_DIR.exists():
        logger.error(f"❌ Sparkasse-Verzeichnis nicht gefunden: {SPARKASSE_DIR}")
        sys.exit(1)
    
    # Run
    try:
        with SparkasseNovemberImporter(DB_PATH, SPARKASSE_DIR, dry_run) as importer:
            importer.run()
    except Exception as e:
        logger.error(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
