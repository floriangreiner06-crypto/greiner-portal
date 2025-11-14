#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kontoauszüge Import Script - Universal (IBAN-basiert)
======================================================

Importiert PDF-Kontoauszüge aller Bankkonten mit:
- Automatischer IBAN-Erkennung aus PDF
- Duplikat-Erkennung
- Kontostand-Historie-Update
- Multi-Bank-Support (Genobank, Sparkasse, HVB, VR Bank, etc.)

Author: Claude AI + User
Version: 2.1
Date: 2025-11-14
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import sys
import os
import shutil

sys.path.insert(0, "/opt/greiner-portal")
from parsers.parser_factory import ParserFactory

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/greiner-portal/logs/imports/bank_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Konfiguration
DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
PDF_BASE_PATH = Path('/mnt/buchhaltung/Buchhaltung/Kontoauszüge')

# Verzeichnisse zum Durchsuchen
VERZEICHNISSE = [
    'Genobank Auto Greiner',
    'Genobank Autohaus Greiner',
    'Genobank Darlehenskonten',
    'Sparkasse',
    'Hypovereinsbank',
    'VR Bank Landau'
]


class KontoauszugImporter:
    """
    Universeller Importer für Kontoauszüge aller Banken
    """
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.stats = {
            'total_pdfs': 0,
            'total_transactions': 0,
            'total_imported': 0,
            'total_skipped': 0,
            'errors': 0,
            'directories': {}
        }

    def connect_db(self):
        """Verbindung zur Datenbank herstellen"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        logger.info("✓ Datenbankverbindung hergestellt")

    def backup_database(self):
        """Backup der Datenbank erstellen"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.db_path}.backup_{timestamp}"
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"✓ Backup erstellt: {backup_path}")
        return backup_path

    def get_konto_id_by_iban(self, iban: str) -> dict:
        """
        Findet Konto anhand IBAN (KRITISCH für korrekte Zuordnung!)
        """
        self.cursor.execute("""
            SELECT k.id, k.kontoname, k.iban, b.bank_name
            FROM konten k
            JOIN banken b ON k.bank_id = b.id
            WHERE k.iban = ? AND k.aktiv = 1
        """, (iban,))
        
        row = self.cursor.fetchone()
        if row:
            return {
                'id': row['id'],
                'name': row['kontoname'],
                'iban': row['iban'],
                'bank': row['bank_name']
            }
        return None

    def update_kontostand_historie(self, konto_id: int, datum: str, saldo: float, quelle: str = 'PDF_Import'):
        """
        Aktualisiert kontostand_historie nach erfolgreichem Import
        
        Args:
            konto_id: ID des Kontos
            datum: Datum des Kontostands (YYYY-MM-DD)
            saldo: Kontostand
            quelle: Quelle des Imports
        """
        try:
            # Prüfe ob Eintrag für dieses Datum bereits existiert
            self.cursor.execute("""
                SELECT id, saldo FROM kontostand_historie 
                WHERE konto_id = ? AND datum = ?
            """, (konto_id, datum))
            
            existing = self.cursor.fetchone()
            
            if existing:
                # Update nur wenn Saldo unterschiedlich
                if abs(existing['saldo'] - saldo) > 0.01:  # Float-Vergleich mit Toleranz
                    self.cursor.execute("""
                        UPDATE kontostand_historie 
                        SET saldo = ?, quelle = ?
                        WHERE konto_id = ? AND datum = ?
                    """, (saldo, quelle, konto_id, datum))
                    logger.info(f"  💾 Kontostand updated: {datum} → {saldo:.2f} € (war: {existing['saldo']:.2f} €)")
                else:
                    logger.debug(f"  ✓ Kontostand unverändert: {saldo:.2f} €")
            else:
                # Insert neuer Eintrag
                self.cursor.execute("""
                    INSERT INTO kontostand_historie (konto_id, datum, saldo, quelle)
                    VALUES (?, ?, ?, ?)
                """, (konto_id, datum, saldo, quelle))
                logger.info(f"  💾 Kontostand gespeichert: {datum} → {saldo:.2f} €")
                
        except Exception as e:
            logger.error(f"  ❌ Fehler beim Kontostand-Update: {e}")

    def import_pdf(self, pdf_path: Path) -> tuple:
        """
        Importiert eine PDF-Datei mit IBAN-basiertem Matching
        
        Returns:
            (anzahl_importiert, konto_info_dict)
        """
        logger.info(f"📄 Importiere: {pdf_path.name}")
        
        try:
            # Parse PDF mit Universal-Parser
            parser = ParserFactory.create_parser(str(pdf_path))
            transactions = parser.parse()
            
            if not transactions:
                logger.warning(f"  ⚠️  Keine Transaktionen gefunden")
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

            # Transaktionen importieren
            imported = 0
            skipped = 0
            
            for tx in transactions:
                # Duplikat-Check
                self.cursor.execute("""
                    SELECT id FROM transaktionen
                    WHERE konto_id = ?
                      AND buchungsdatum = ?
                      AND betrag = ?
                      AND verwendungszweck = ?
                """, (
                    konto_id,
                    tx.buchungsdatum.strftime('%Y-%m-%d'),
                    tx.betrag,
                    tx.verwendungszweck
                ))
                
                if self.cursor.fetchone():
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
                    tx.buchungsdatum.strftime('%Y-%m-%d'),
                    tx.valutadatum.strftime('%Y-%m-%d'),
                    tx.verwendungszweck,
                    tx.betrag,
                    getattr(tx, 'saldo_nach_buchung', None),
                    str(pdf_path),
                    datetime.now()
                ))
                imported += 1

            # COMMIT
            self.conn.commit()
            
            # Kontostand-Historie aktualisieren
            if parser.endsaldo is not None:
                # Neuestes Buchungsdatum ermitteln
                max_datum = max(tx.buchungsdatum for tx in transactions)
                max_datum_str = max_datum.strftime('%Y-%m-%d')
                
                # Kontostand-Historie aktualisieren
                self.update_kontostand_historie(
                    konto_id=konto_id,
                    datum=max_datum_str,
                    saldo=parser.endsaldo,
                )
            elif parser.endsaldo is None:
                logger.warning(f"  ⚠️  Kein Endsaldo im PDF gefunden")
            
            logger.info(f"  ✅ Importiert: {imported}, Übersprungen: {skipped}")
            return imported, konto_info
            
        except Exception as e:
            logger.error(f"  ❌ Fehler: {e}")
            import traceback
            traceback.print_exc()
            return 0, None

    def find_recent_pdfs(self, days_back: int = 30) -> dict:
        """
        Findet PDFs der letzten N Tage in den konfigurierten Verzeichnissen
        
        Args:
            days_back: Wie viele Tage zurück (default: 30)
        """
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_pdfs = {}
        
        for verzeichnis in VERZEICHNISSE:
            dir_path = PDF_BASE_PATH / verzeichnis
            
            if not dir_path.exists():
                logger.warning(f"⚠️  Verzeichnis nicht gefunden: {verzeichnis}")
                continue
            
            # Finde PDFs nach Änderungsdatum
            pdfs = []
            for pdf in dir_path.glob("**/*.pdf"):
                if pdf.stat().st_mtime > cutoff_date.timestamp():
                    pdfs.append(pdf)
            
            if pdfs:
                recent_pdfs[verzeichnis] = sorted(pdfs)
                
        return recent_pdfs

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
            'konten': set()
        }
        
        for pdf in pdfs:
            imported, konto_info = self.import_pdf(pdf)
            
            if imported > 0:
                dir_stats['transactions'] += imported
                if konto_info:
                    dir_stats['konten'].add(f"{konto_info['id']} ({konto_info['name']})")
        
        self.stats['directories'][verzeichnis] = dir_stats
        logger.info(f"  PDFs: {dir_stats['pdfs']}, Transaktionen: {dir_stats['transactions']}")
        if dir_stats['konten']:
            logger.info(f"  Konten: {', '.join(sorted(dir_stats['konten']))}")

    def print_summary(self):
        """
        Gibt Zusammenfassung aus
        """
        logger.info("\n" + "="*70)
        logger.info("📊 ZUSAMMENFASSUNG")
        logger.info("="*70)
        
        total_pdfs = sum(d['pdfs'] for d in self.stats['directories'].values())
        total_trans = sum(d['transactions'] for d in self.stats['directories'].values())
        
        logger.info(f"  PDFs gesamt:            {total_pdfs}")
        logger.info(f"  Transaktionen neu:      {total_trans}")
        
        logger.info("\n📁 Pro Verzeichnis:")
        for verz, stats in self.stats['directories'].items():
            logger.info(f"  {verz}:")
            logger.info(f"    PDFs: {stats['pdfs']}, Transaktionen: {stats['transactions']}")
            if stats['konten']:
                logger.info(f"    Konten: {', '.join(sorted(stats['konten']))}")
        
        # Aktuelle Monat-Transaktionen in DB
        current_month = datetime.now().strftime('%Y-%m')
        self.cursor.execute("""
            SELECT COUNT(*) as anzahl
            FROM transaktionen
            WHERE strftime('%Y-%m', buchungsdatum) = ?
        """, (current_month,))
        logger.info(f"\n✅ {current_month} Transaktionen in DB: {self.cursor.fetchone()['anzahl']}")

    def run(self, days_back: int = 30):
        """
        Hauptfunktion: Import aller Kontoauszüge
        
        Args:
            days_back: PDFs der letzten N Tage importieren (default: 30)
        """
        logger.info("\n" + "="*70)
        logger.info("🚀 KONTOAUSZÜGE IMPORT (Universal)")
        logger.info("="*70)
        logger.info(f"Zeitraum: Letzte {days_back} Tage")
        
        # 1. Backup
        backup_path = self.backup_database()
        
        # 2. DB-Verbindung
        self.connect_db()
        
        # 3. PDFs finden
        recent_pdfs = self.find_recent_pdfs(days_back)
        
        if not recent_pdfs:
            logger.warning(f"⚠️  Keine PDFs der letzten {days_back} Tage gefunden!")
            return
        
        logger.info(f"\n✓ {len(recent_pdfs)} Verzeichnisse mit PDFs gefunden")
        
        # 4. Import pro Verzeichnis
        for verzeichnis, pdfs in recent_pdfs.items():
            self.import_directory(verzeichnis, pdfs)
        
        # 5. Zusammenfassung
        self.print_summary()
        
        # 6. Cleanup
        self.conn.close()
        
        logger.info(f"\n✅ Import abgeschlossen!")
        logger.info(f"📦 Backup: {backup_path}")


def main():
    """Main Entry Point"""
    try:
        # Import der letzten 30 Tage (anpassbar)
        importer = KontoauszugImporter(DB_PATH)
        importer.run(days_back=30)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Import abgebrochen")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Kritischer Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
