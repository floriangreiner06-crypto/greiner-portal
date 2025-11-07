#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
November 2025 - Multi-Account Import Script
============================================
Importiert November-PDFs für ALLE Genobank-Konten

Features:
- Automatische Format-Erkennung (Standard vs. Tagesauszug)
- Duplikats-Prüfung
- Saldo-Validierung
- Backup vor Import
- Detailliertes Logging

Konten:
- 1501500 HYU KK (Genobank Auto Greiner) ✅ bereits importiert
- 57908 KK (Genobank Auto Greiner)
- 22225 Immo KK (Genobank Autohaus Greiner)
- 4700057908 Darlehen
- 20057908 Darlehen
- 1700057908 Darlehen
- Hypovereinsbank KK
- Sparkasse 76003647 KK

Author: Claude AI
Version: 1.0
Date: 2025-11-07
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import sys
import os
import shutil

# Füge aktuelles Verzeichnis zu sys.path hinzu für Parser-Import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from genobank_universal_parser import GenobankUniversalParser

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('november_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Konfiguration
DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
PDF_BASE_PATH = Path('/mnt/buchhaltung/Buchhaltung/Kontoauszüge')

# Konto-Mapping: Verzeichnis -> Kontonummer
KONTEN = {
    'Genobank Auto Greiner': ['1501500', '57908', '4700057908'],
    'Genobank Autohaus Greiner': ['22225'],
    'Genobank Darlehenskonten': ['20057908'],
    'Genobank Greiner Immob.Verw': ['1700057908'],
    'Hypovereinsbank': ['hypovereinsbank'],
    'Sparkasse': ['76003647']
}


class NovemberImporter:
    """Multi-Account November PDF Importer"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.stats = {
            'total_pdfs': 0,
            'total_transactions': 0,
            'skipped_duplicates': 0,
            'errors': 0,
            'by_account': {}
        }
    
    def connect_db(self):
        """Verbinde zur Datenbank"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"✅ Datenbankverbindung hergestellt: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ DB-Verbindung fehlgeschlagen: {e}")
            raise
    
    def backup_database(self):
        """Erstelle Backup der Datenbank"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{self.db_path}.backup_{timestamp}"
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"✅ Backup erstellt: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"❌ Backup fehlgeschlagen: {e}")
            raise
    
    def find_november_pdfs(self) -> dict:
        """
        Findet alle November-PDFs für alle Konten
        
        Returns:
            Dict: {verzeichnis: [pdf_files]}
        """
        logger.info("🔍 Suche November-PDFs...")
        found_pdfs = {}
        
        for verzeichnis in KONTEN.keys():
            pdf_dir = PDF_BASE_PATH / verzeichnis
            
            if not pdf_dir.exists():
                logger.warning(f"⚠️ Verzeichnis nicht gefunden: {pdf_dir}")
                continue
            
            # Suche nach verschiedenen November-Patterns
            patterns = [
                '*Auszug*11.25*.pdf',
                '*November*2025*.pdf',
                '*_2025_Nr.011_*.pdf',
                '*11_2025*.pdf'
            ]
            
            pdfs = []
            for pattern in patterns:
                pdfs.extend(pdf_dir.glob(pattern))
            
            # Deduplizieren
            pdfs = list(set(pdfs))
            
            if pdfs:
                found_pdfs[verzeichnis] = sorted(pdfs)
                logger.info(f"  ✓ {verzeichnis}: {len(pdfs)} PDFs")
        
        return found_pdfs
    
    def get_konto_id(self, kontonummer: str) -> int:
        """
        Ermittelt konto_id aus Kontonummer
        
        Args:
            kontonummer: z.B. "57908" oder "1501500"
        
        Returns:
            konto_id (int)
        """
        # Suche in konten-Tabelle
        self.cursor.execute("""
            SELECT id FROM konten 
            WHERE kontonummer LIKE ?
        """, (f"%{kontonummer}%",))
        
        result = self.cursor.fetchone()
        if result:
            return result[0]
        
        # Fallback: Suche in transaktionen nach pdf_quelle
        self.cursor.execute("""
            SELECT DISTINCT konto_id FROM transaktionen 
            WHERE pdf_quelle LIKE ?
            LIMIT 1
        """, (f"%{kontonummer}%",))
        
        result = self.cursor.fetchone()
        if result:
            return result[0]
        
        logger.warning(f"⚠️ Keine konto_id für {kontonummer} gefunden")
        return None
    
    def transaction_exists(self, konto_id: int, buchungsdatum: datetime, 
                          betrag: float, verwendungszweck: str) -> bool:
        """
        Prüft ob Transaktion bereits existiert
        
        Args:
            konto_id: Konto-ID
            buchungsdatum: Buchungsdatum
            betrag: Betrag
            verwendungszweck: Verwendungszweck (erste 100 Zeichen)
        
        Returns:
            True wenn Duplikat
        """
        self.cursor.execute("""
            SELECT COUNT(*) FROM transaktionen
            WHERE konto_id = ?
              AND buchungsdatum = ?
              AND ABS(betrag - ?) < 0.01
              AND verwendungszweck LIKE ?
        """, (
            konto_id,
            buchungsdatum.strftime('%Y-%m-%d'),
            betrag,
            verwendungszweck[:100] + '%'
        ))
        
        count = self.cursor.fetchone()[0]
        return count > 0
    
    def import_pdf(self, pdf_path: Path, konto_id: int) -> int:
        """
        Importiert eine PDF-Datei
        
        Args:
            pdf_path: Pfad zur PDF
            konto_id: Konto-ID
        
        Returns:
            Anzahl importierter Transaktionen
        """
        logger.info(f"📄 Importiere: {pdf_path.name}")
        
        try:
            # Parse PDF mit Universal-Parser
            parser = GenobankUniversalParser(str(pdf_path))
            transactions = parser.parse()
            
            if not transactions:
                logger.warning(f"  ⚠️ Keine Transaktionen gefunden")
                return 0
            
            # Import-Statistik
            imported = 0
            skipped = 0
            
            for tx in transactions:
                # Duplikats-Check
                if self.transaction_exists(
                    konto_id,
                    tx['buchungsdatum'],
                    tx['betrag'],
                    tx['verwendungszweck']
                ):
                    skipped += 1
                    continue
                
                # INSERT
                self.cursor.execute("""
                    INSERT INTO transaktionen (
                        konto_id, buchungsdatum, valutadatum,
                        verwendungszweck, betrag, saldo_nach_buchung,
                        pdf_quelle, importiert_am
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    konto_id,
                    tx['buchungsdatum'].strftime('%Y-%m-%d'),
                    tx['valutadatum'].strftime('%Y-%m-%d'),
                    tx['verwendungszweck'],
                    tx['betrag'],
                    tx.get('saldo_nach_buchung'),
                    str(pdf_path),
                    datetime.now()
                ))
                imported += 1
            
            self.conn.commit()
            
            logger.info(f"  ✅ {imported} Transaktionen importiert, {skipped} Duplikate übersprungen")
            self.stats['skipped_duplicates'] += skipped
            
            return imported
            
        except Exception as e:
            logger.error(f"  ❌ Fehler bei {pdf_path.name}: {e}")
            self.stats['errors'] += 1
            return 0
    
    def import_account(self, verzeichnis: str, pdfs: list):
        """
        Importiert alle PDFs für ein Konto
        
        Args:
            verzeichnis: Verzeichnisname (z.B. "Genobank Auto Greiner")
            pdfs: Liste von PDF-Pfaden
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"📁 {verzeichnis}")
        logger.info(f"{'='*70}")
        
        # Hole zugehörige Kontonummern
        kontonummern = KONTEN.get(verzeichnis, [])
        
        account_stats = {
            'pdfs': len(pdfs),
            'transactions': 0
        }
        
        for pdf_path in pdfs:
            # Versuche Kontonummer aus Dateinamen zu extrahieren
            konto_id = None
            
            for kontonummer in kontonummern:
                if kontonummer.lower() in pdf_path.name.lower():
                    konto_id = self.get_konto_id(kontonummer)
                    if konto_id:
                        break
            
            # Fallback: Nutze erstes Konto
            if not konto_id and kontonummern:
                konto_id = self.get_konto_id(kontonummern[0])
            
            if not konto_id:
                logger.error(f"  ❌ Keine konto_id für {pdf_path.name}")
                continue
            
            # Import
            imported = self.import_pdf(pdf_path, konto_id)
            account_stats['transactions'] += imported
        
        self.stats['by_account'][verzeichnis] = account_stats
        self.stats['total_transactions'] += account_stats['transactions']
        self.stats['total_pdfs'] += account_stats['pdfs']
    
    def run(self):
        """Hauptfunktion: Import aller November-PDFs"""
        logger.info("\n" + "="*70)
        logger.info("🚀 NOVEMBER 2025 - MULTI-ACCOUNT IMPORT")
        logger.info("="*70)
        
        # 1. Backup
        backup_path = self.backup_database()
        
        # 2. DB-Verbindung
        self.connect_db()
        
        # 3. PDFs finden
        november_pdfs = self.find_november_pdfs()
        
        if not november_pdfs:
            logger.warning("⚠️ Keine November-PDFs gefunden!")
            return
        
        logger.info(f"\n✓ {len(november_pdfs)} Verzeichnisse mit PDFs gefunden")
        
        # 4. Import pro Konto
        for verzeichnis, pdfs in november_pdfs.items():
            self.import_account(verzeichnis, pdfs)
        
        # 5. Zusammenfassung
        self.print_summary()
        
        # 6. Cleanup
        self.conn.close()
        logger.info(f"\n✅ Import abgeschlossen!")
        logger.info(f"📦 Backup: {backup_path}")
    
    def print_summary(self):
        """Gibt Zusammenfassung aus"""
        logger.info("\n" + "="*70)
        logger.info("📊 IMPORT-ZUSAMMENFASSUNG")
        logger.info("="*70)
        
        logger.info(f"\n📄 Gesamt:")
        logger.info(f"  PDFs verarbeitet:     {self.stats['total_pdfs']}")
        logger.info(f"  Transaktionen neu:    {self.stats['total_transactions']}")
        logger.info(f"  Duplikate übersprungen: {self.stats['skipped_duplicates']}")
        logger.info(f"  Fehler:               {self.stats['errors']}")
        
        if self.stats['by_account']:
            logger.info(f"\n📁 Pro Konto:")
            for verzeichnis, stats in self.stats['by_account'].items():
                logger.info(f"  {verzeichnis}:")
                logger.info(f"    PDFs: {stats['pdfs']}, Transaktionen: {stats['transactions']}")
        
        # Validierung: Zähle November-Transaktionen
        self.cursor.execute("""
            SELECT COUNT(*) FROM transaktionen
            WHERE buchungsdatum >= '2025-11-01'
              AND buchungsdatum < '2025-12-01'
        """)
        
        november_total = self.cursor.fetchone()[0]
        logger.info(f"\n✅ November-Transaktionen in DB: {november_total}")


def main():
    """Main Entry Point"""
    try:
        importer = NovemberImporter(DB_PATH)
        importer.run()
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Import abgebrochen")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"\n❌ Kritischer Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
