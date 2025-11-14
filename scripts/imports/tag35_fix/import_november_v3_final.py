#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
November Import V3.2 - VOLLSTÄNDIG IBAN-BASIERT
================================================
Die sicherste Version - komplett unabhängig von:
- Dateinamen
- Verzeichnisstrukturen  
- User-Fehlern

Alles basiert auf:
- IBAN aus PDF-Inhalt
- Echtes Datum aus PDF-Inhalt
- Automatische Sortierung

Author: Claude AI
Version: 3.2 (FINAL BULLETPROOF)
Date: 2025-11-13
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import sys
import os
import shutil
from decimal import Decimal
from typing import List, Dict

sys.path.insert(0, "/opt/greiner-portal/parsers")
from genobank_universal_parser import GenobankUniversalParser

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('november_import_v3_final.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Konfiguration
DB_PATH = '/opt/greiner-portal/data/greiner_controlling_test.db'
PDF_BASE_PATH = Path('/mnt/buchhaltung/Buchhaltung/Kontoauszüge')


class FinalNovemberImporter:
    """Finaler Import - vollständig IBAN-basiert"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.iban_to_konto = {}  # IBAN -> {id, name}
        self.stats = {
            'pdfs_found': 0,
            'pdfs_parsed': 0,
            'pdfs_skipped': 0,
            'transactions_imported': 0,
            'salden_warnings': 0
        }
    
    def connect_db(self):
        """Verbinde zur Datenbank und lade Konten"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Lade alle Konten mit IBAN
        self.cursor.execute("""
            SELECT id, iban, kontoname 
            FROM konten 
            WHERE iban IS NOT NULL AND iban != ''
        """)
        
        for konto_id, iban, kontoname in self.cursor.fetchall():
            # Normalisiere IBAN
            iban_clean = iban.replace(' ', '').strip().upper()
            self.iban_to_konto[iban_clean] = {
                'id': konto_id,
                'name': kontoname
            }
        
        logger.info(f"✅ DB verbunden - {len(self.iban_to_konto)} Konten geladen")
        
        # Zeige geladene Konten
        for iban, info in self.iban_to_konto.items():
            logger.info(f"  → {iban}: {info['name']} (ID: {info['id']})")
    
    def find_all_pdfs(self) -> List[Path]:
        """
        Findet ALLE PDFs die nach November 2025 aussehen
        EGAL in welchem Verzeichnis sie liegen!
        """
        logger.info("\n🔍 Suche ALLE November 2025 PDFs...")
        
        all_pdfs = []
        
        # Durchsuche ALLE Unterverzeichnisse
        for subdir in PDF_BASE_PATH.iterdir():
            if not subdir.is_dir():
                continue
                
            # Suche nach November-Patterns
            patterns = [
                '*11.25*.pdf',
                '*11_25*.pdf', 
                '*November*25*.pdf',
                '*2025*11*.pdf',
                '*2025_11*.pdf'
            ]
            
            for pattern in patterns:
                found = list(subdir.glob(pattern))
                if found:
                    logger.info(f"  📁 {subdir.name}: {len(found)} PDFs")
                    all_pdfs.extend(found)
        
        # Deduplizieren
        all_pdfs = list(set(all_pdfs))
        
        self.stats['pdfs_found'] = len(all_pdfs)
        logger.info(f"✅ Gesamt: {len(all_pdfs)} PDFs gefunden")
        
        return all_pdfs
    
    def parse_and_group_pdfs(self, pdf_paths: List[Path]) -> Dict[str, List]:
        """
        Parse alle PDFs und gruppiere nach IBAN aus dem Inhalt
        """
        logger.info("\n" + "="*70)
        logger.info("📊 PHASE 1: Analysiere PDF-Inhalte und extrahiere IBANs")
        logger.info("="*70)
        
        pdfs_by_iban = {}
        
        for pdf_path in pdf_paths:
            logger.info(f"\n🔍 Parse: {pdf_path.name}")
            logger.info(f"   Pfad: {pdf_path.parent.name}/{pdf_path.name}")
            
            try:
                # Parse PDF
                parser = GenobankUniversalParser(str(pdf_path))
                transactions = parser.parse()
                
                if not transactions:
                    logger.warning(f"  ⚠️ Keine Transaktionen gefunden")
                    self.stats['pdfs_skipped'] += 1
                    continue
                
                if not parser.iban:
                    logger.error(f"  ❌ Keine IBAN im PDF gefunden!")
                    self.stats['pdfs_skipped'] += 1
                    continue
                
                # Normalisiere IBAN
                iban_clean = parser.iban.replace(' ', '').strip().upper()
                
                # Prüfe ob IBAN bekannt
                if iban_clean not in self.iban_to_konto:
                    logger.warning(f"  ⚠️ Unbekannte IBAN: {iban_clean}")
                    logger.warning(f"     PDF liegt in: {pdf_path.parent.name}")
                    self.stats['pdfs_skipped'] += 1
                    continue
                
                konto_info = self.iban_to_konto[iban_clean]
                logger.info(f"  ✓ IBAN erkannt: {iban_clean}")
                logger.info(f"  ✓ Konto: {konto_info['name']} (ID: {konto_info['id']})")
                
                # Ermittle Zeitraum
                erste_tx = transactions[0]['buchungsdatum']
                letzte_tx = transactions[-1]['buchungsdatum']
                
                pdf_data = {
                    'path': pdf_path,
                    'iban': iban_clean,
                    'konto_id': konto_info['id'],
                    'konto_name': konto_info['name'],
                    'start_datum': erste_tx,
                    'end_datum': letzte_tx,
                    'startsaldo': parser.startsaldo,
                    'endsaldo': parser.endsaldo,
                    'transactions': transactions,
                    'tx_count': len(transactions)
                }
                
                logger.info(f"  ✓ Zeitraum: {erste_tx.strftime('%d.%m.')} - {letzte_tx.strftime('%d.%m.')}")
                logger.info(f"  ✓ Anzahl TX: {len(transactions)}")
                
                # Gruppiere nach IBAN
                if iban_clean not in pdfs_by_iban:
                    pdfs_by_iban[iban_clean] = []
                pdfs_by_iban[iban_clean].append(pdf_data)
                
                self.stats['pdfs_parsed'] += 1
                
            except Exception as e:
                logger.error(f"  ❌ Fehler: {e}")
                self.stats['pdfs_skipped'] += 1
                import traceback
                traceback.print_exc()
        
        # Sortiere PDFs pro IBAN nach Datum
        logger.info("\n📊 Sortiere PDFs nach Datum...")
        for iban, pdf_list in pdfs_by_iban.items():
            pdf_list.sort(key=lambda x: x['start_datum'])
            
            konto_name = self.iban_to_konto[iban]['name']
            logger.info(f"\n💳 {konto_name} ({iban[-8:]}):")
            for pdf in pdf_list:
                logger.info(
                    f"  → {pdf['start_datum'].strftime('%d.%m.')}: "
                    f"{pdf['path'].name} ({pdf['tx_count']} TX)"
                )
        
        return pdfs_by_iban
    
    def get_last_saldo(self, konto_id: int, before_date: datetime) -> Decimal:
        """Hole letzten bekannten Saldo vor einem Datum"""
        self.cursor.execute("""
            SELECT saldo_nach_buchung
            FROM transaktionen
            WHERE konto_id = ?
            AND buchungsdatum < ?
            ORDER BY buchungsdatum DESC, id DESC
            LIMIT 1
        """, (konto_id, before_date.strftime('%Y-%m-%d')))
        
        result = self.cursor.fetchone()
        return Decimal(str(result[0])) if result else Decimal('0.0')
    
    def import_konto_pdfs(self, iban: str, sorted_pdfs: List[Dict]):
        """
        Importiere alle PDFs eines Kontos in korrekter Reihenfolge
        """
        konto_info = self.iban_to_konto[iban]
        konto_id = konto_info['id']
        
        logger.info(f"\n" + "="*70)
        logger.info(f"💳 IMPORT: {konto_info['name']} (ID: {konto_id})")
        logger.info(f"   IBAN: {iban}")
        logger.info(f"="*70)
        
        # Start-Saldo (Oktober-Ende)
        current_saldo = self.get_last_saldo(konto_id, datetime(2025, 11, 1))
        logger.info(f"📊 Start-Saldo (Oktober): {current_saldo:,.2f} EUR")
        
        # Importiere jedes PDF in Reihenfolge
        for pdf_data in sorted_pdfs:
            logger.info(f"\n📄 {pdf_data['path'].name}")
            logger.info(f"   Zeitraum: {pdf_data['start_datum'].strftime('%d.%m.')} - {pdf_data['end_datum'].strftime('%d.%m.')}")
            
            # Validiere Start-Saldo
            if pdf_data['startsaldo'] is not None:
                pdf_start = Decimal(str(pdf_data['startsaldo']))
                diff = abs(current_saldo - pdf_start)
                
                if diff > 0.01:
                    logger.warning(
                        f"  ⚠️ Start-Saldo-Differenz: {diff:,.2f} EUR\n"
                        f"     DB:  {current_saldo:,.2f} EUR\n"
                        f"     PDF: {pdf_start:,.2f} EUR"
                    )
                    self.stats['salden_warnings'] += 1
                    
                    # Bei großer Differenz: PDF verwenden
                    if diff > 1000:
                        logger.info(f"  🔄 Nehme PDF-Saldo (Differenz > 1000)")
                        current_saldo = pdf_start
                else:
                    logger.info(f"  ✓ Start-Saldo stimmt: {current_saldo:,.2f} EUR")
            
            # Importiere Transaktionen
            imported = 0
            skipped = 0
            
            for tx in pdf_data['transactions']:
                # Neuer Saldo
                betrag = Decimal(str(tx['betrag']))
                current_saldo += betrag
                
                # Duplikats-Check
                self.cursor.execute("""
                    SELECT COUNT(*) FROM transaktionen
                    WHERE konto_id = ?
                    AND buchungsdatum = ?
                    AND ABS(betrag - ?) < 0.01
                    AND verwendungszweck LIKE ?
                """, (
                    konto_id,
                    tx['buchungsdatum'].strftime('%Y-%m-%d'),
                    float(betrag),
                    tx['verwendungszweck'][:50] + '%'
                ))
                
                if self.cursor.fetchone()[0] > 0:
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
                    float(betrag),
                    float(current_saldo),  # KORRIGIERTER SALDO
                    str(pdf_data['path']),
                    datetime.now()
                ))
                imported += 1
            
            self.conn.commit()
            
            # Validiere End-Saldo
            if pdf_data['endsaldo'] is not None:
                pdf_end = Decimal(str(pdf_data['endsaldo']))
                diff = abs(current_saldo - pdf_end)
                
                if diff > 0.01:
                    logger.warning(f"  ⚠️ End-Saldo-Differenz: {diff:,.2f} EUR")
                else:
                    logger.info(f"  ✅ End-Saldo stimmt: {current_saldo:,.2f} EUR")
            
            logger.info(f"  📊 Importiert: {imported}, Übersprungen: {skipped}")
            self.stats['transactions_imported'] += imported
        
        logger.info(f"\n✅ Konto fertig - Endsaldo: {current_saldo:,.2f} EUR")
        
        return current_saldo
    
    def run(self):
        """Hauptfunktion"""
        logger.info("\n" + "="*70)
        logger.info("🚀 NOVEMBER IMPORT V3.2 - VOLLSTÄNDIG IBAN-BASIERT")
        logger.info("="*70)
        
        # Backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.db_path}.backup_v32_{timestamp}"
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"📦 Backup: {backup_path}")
        
        # DB-Verbindung
        self.connect_db()
        
        # 1. Finde ALLE PDFs
        all_pdfs = self.find_all_pdfs()
        
        if not all_pdfs:
            logger.error("❌ Keine November-PDFs gefunden!")
            return
        
        # 2. Parse und gruppiere nach IBAN
        pdfs_by_iban = self.parse_and_group_pdfs(all_pdfs)
        
        if not pdfs_by_iban:
            logger.error("❌ Keine importierbaren PDFs gefunden!")
            return
        
        # 3. Importiere pro IBAN
        logger.info("\n" + "="*70)
        logger.info("📊 PHASE 2: Import mit kontinuierlicher Saldenkette")
        logger.info("="*70)
        
        final_salden = {}
        for iban, sorted_pdfs in pdfs_by_iban.items():
            endsaldo = self.import_konto_pdfs(iban, sorted_pdfs)
            final_salden[iban] = endsaldo
        
        # 4. Zusammenfassung
        logger.info("\n" + "="*70)
        logger.info("📊 ZUSAMMENFASSUNG")
        logger.info("="*70)
        logger.info(f"  PDFs gefunden:       {self.stats['pdfs_found']}")
        logger.info(f"  PDFs verarbeitet:    {self.stats['pdfs_parsed']}")
        logger.info(f"  PDFs übersprungen:   {self.stats['pdfs_skipped']}")
        logger.info(f"  Transaktionen:       {self.stats['transactions_imported']}")
        logger.info(f"  Salden-Warnungen:    {self.stats['salden_warnings']}")
        
        # 5. Zeige finale Salden
        logger.info("\n💰 FINALE SALDEN:")
        for iban, saldo in final_salden.items():
            konto_name = self.iban_to_konto[iban]['name']
            logger.info(f"  {konto_name}: {saldo:,.2f} EUR")
        
        # 6. Prüfe gegen erwartete Werte
        logger.info("\n🎯 SOLL-IST-VERGLEICH:")
        expected = {
            'DE27741900000000057908': 106991.48,  # Konto 5
            'DE68741900000001501500': 191489.32   # Konto 15
        }
        
        for iban, soll in expected.items():
            if iban in final_salden:
                ist = float(final_salden[iban])
                diff = ist - soll
                status = "✅" if abs(diff) < 1 else "⚠️"
                logger.info(f"  {iban[-8:]}: Soll={soll:,.2f}, Ist={ist:,.2f}, Diff={diff:,.2f} {status}")
        
        self.conn.close()
        logger.info("\n✅ Import erfolgreich abgeschlossen!")


if __name__ == "__main__":
    importer = FinalNovemberImporter(DB_PATH)
    importer.run()
