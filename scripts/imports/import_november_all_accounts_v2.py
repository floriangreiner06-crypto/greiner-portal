#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
November 2025 - Multi-Account Import Script V2 (IBAN-basiert)
==============================================================
KRITISCHER FIX: Nutzt IBAN aus PDF statt Verzeichnis-Mapping

Problem in V1:
- Verzeichnis "Genobank Autohaus Greiner" + Mapping "22225"
- → Falsche Zuordnung zu Immobilien-Konto
- Ursache: Zwei Konten mit ähnlichen letzten Stellen

Lösung in V2:
- Parser extrahiert IBAN aus PDF
- Matching gegen vollständige IBAN in konten-Tabelle
- Kein Verzeichnis-basiertes Mapping mehr

Author: Claude AI
Version: 2.0 (IBAN-basiert)
Date: 2025-11-07
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import sys
import os
import shutil

sys.path.insert(0, "/opt/greiner-portal/parsers")
from genobank_universal_parser import GenobankUniversalParser

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('november_import_v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Konfiguration
DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
PDF_BASE_PATH = Path('/mnt/buchhaltung/Buchhaltung/Kontoauszüge')

# Verzeichnisse zum Durchsuchen (ohne Kontonummer-Mapping!)
VERZEICHNISSE = [
    'Genobank Auto Greiner',
    'Genobank Autohaus Greiner',
    'Genobank Darlehenskonten',
    'Genobank Greiner Immob.Verw',
    'Hypovereinsbank',
    'Sparkasse'
]


class NovemberImporterV2:
    """Multi-Account November PDF Importer - IBAN-basiert"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.iban_cache = {}  # Cache: IBAN -> konto_id
        self.stats = {
            'total_pdfs': 0,
            'total_transactions': 0,
            'skipped_duplicates': 0,
            'errors': 0,
            'by_account': {}
        }
    
    def connect_db(self):
        """Verbinde zur Datenbank und lade IBAN-Cache"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"✅ Datenbankverbindung hergestellt: {self.db_path}")
            
            # Lade alle IBANs in Cache
            self.cursor.execute("""
                SELECT id, iban, kontoname, inhaber
                FROM konten
                WHERE iban IS NOT NULL
            """)
            
            for konto_id, iban, kontoname, inhaber in self.cursor.fetchall():
                self.iban_cache[iban] = {
                    'id': konto_id,
                    'name': kontoname,
                    'inhaber': inhaber
                }
            
            logger.info(f"✅ IBAN-Cache geladen: {len(self.iban_cache)} Konten")
            
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
        Findet alle November-PDFs in allen Verzeichnissen
        
        Returns:
            Dict: {verzeichnis: [pdf_files]}
        """
        logger.info("🔍 Suche November-PDFs...")
        found_pdfs = {}
        
        for verzeichnis in VERZEICHNISSE:
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
    
    def get_konto_id_by_iban(self, iban: str) -> dict:
        """
        Ermittelt konto_id anhand IBAN
        
        Args:
            iban: IBAN aus PDF (z.B. "DE27741900000000057908")
        
        Returns:
            Dict mit id, name, inhaber oder None
        """
        if not iban:
            return None
        
        # Entferne Leerzeichen und normalisiere
        iban = iban.replace(' ', '').strip().upper()
        
        # Direkt aus Cache
        if iban in self.iban_cache:
            return self.iban_cache[iban]
        
        logger.warning(f"⚠️ IBAN nicht in DB gefunden: {iban}")
        return None
    
    def transaction_exists(self, konto_id: int, buchungsdatum: datetime, 
                          betrag: float, verwendungszweck: str) -> bool:
        """
        Prüft ob Transaktion bereits existiert
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
    
    def import_pdf(self, pdf_path: Path) -> tuple:
        """
        Importiert eine PDF-Datei mit IBAN-basiertem Matching
        
        Args:
            pdf_path: Pfad zur PDF
        
        Returns:
            (anzahl_importiert, konto_info_dict)
        """
        logger.info(f"📄 Importiere: {pdf_path.name}")
        
        try:
            # Parse PDF mit Universal-Parser
            parser = GenobankUniversalParser(str(pdf_path))
            transactions = parser.parse()
            
            if not transactions:
                logger.warning(f"  ⚠️ Keine Transaktionen gefunden")
                return 0, None
            
            # KRITISCH: Ermittle konto_id anhand IBAN aus PDF
            iban = parser.iban
            if not iban:
                logger.error(f"  ❌ Keine IBAN im PDF gefunden!")
                return 0, None
            
            konto_info = self.get_konto_id_by_iban(iban)
            if not konto_info:
                logger.error(f"  ❌ Konto nicht gefunden für IBAN: {iban}")
                return 0, None
            
            konto_id = konto_info['id']
            logger.info(f"  ✓ IBAN-Match: {iban} → Konto {konto_id} ({konto_info['name']})")
            
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
            
            return imported, konto_info
            
        except Exception as e:
            logger.error(f"  ❌ Fehler bei {pdf_path.name}: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
            return 0, None
    
    def import_directory(self, verzeichnis: str, pdfs: list):
        """
        Importiert alle PDFs aus einem Verzeichnis
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"📁 {verzeichnis}")
        logger.info(f"{'='*70}")
        
        dir_stats = {
            'pdfs': len(pdfs),
            'transactions': 0,
            'konten': set()  # Welche Konten betroffen
        }
        
        for pdf_path in pdfs:
            imported, konto_info = self.import_pdf(pdf_path)
            dir_stats['transactions'] += imported
            
            if konto_info:
                dir_stats['konten'].add(f"{konto_info['id']} ({konto_info['name']})")
        
        # Zusammenfassung
        logger.info(f"\n📊 Verzeichnis-Zusammenfassung:")
        logger.info(f"  PDFs: {dir_stats['pdfs']}")
        logger.info(f"  Transaktionen: {dir_stats['transactions']}")
        logger.info(f"  Betroffene Konten: {', '.join(dir_stats['konten']) if dir_stats['konten'] else 'keine'}")
        
        self.stats['by_account'][verzeichnis] = dir_stats
        self.stats['total_transactions'] += dir_stats['transactions']
        self.stats['total_pdfs'] += dir_stats['pdfs']
    
    def run(self):
        """Hauptfunktion: Import aller November-PDFs"""
        logger.info("\n" + "="*70)
        logger.info("🚀 NOVEMBER 2025 - MULTI-ACCOUNT IMPORT V2 (IBAN-BASIERT)")
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
        
        # 4. Import pro Verzeichnis
        for verzeichnis, pdfs in november_pdfs.items():
            self.import_directory(verzeichnis, pdfs)
        
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
        logger.info(f"  PDFs verarbeitet:       {self.stats['total_pdfs']}")
        logger.info(f"  Transaktionen neu:      {self.stats['total_transactions']}")
        logger.info(f"  Duplikate übersprungen: {self.stats['skipped_duplicates']}")
        logger.info(f"  Fehler:                 {self.stats['errors']}")
        
        if self.stats['by_account']:
            logger.info(f"\n📁 Pro Verzeichnis:")
            for verzeichnis, stats in self.stats['by_account'].items():
                logger.info(f"  {verzeichnis}:")
                logger.info(f"    PDFs: {stats['pdfs']}, Transaktionen: {stats['transactions']}")
                if stats.get('konten'):
                    logger.info(f"    Konten: {', '.join(stats['konten'])}")
        
        # Validierung
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
        importer = NovemberImporterV2(DB_PATH)
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
