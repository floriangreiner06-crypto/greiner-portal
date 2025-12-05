#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
November Import SIMPLE VERSION - Keine Berechnungen!
====================================================
Nach 6+ Stunden Trial & Error die Erkenntnis:
PDFs haben korrekte Salden. Einfach übernehmen. Fertig.

KEIN:
- Fortschreiben
- Berechnen
- Validieren gegen andere Tage

NUR:
- PDF lesen
- Salden übernehmen
- Speichern

Author: Claude AI (nach langem Lernen...)
Version: FINAL SIMPLE
Date: 2025-11-13
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import sys
import shutil

sys.path.insert(0, "/opt/greiner-portal/parsers")
from genobank_universal_parser import GenobankUniversalParser

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Config
DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
PDF_BASE_PATH = Path('/mnt/buchhaltung/Buchhaltung/Kontoauszüge')


def import_november_simple():
    """
    SIMPLER Import - keine Logik, nur Daten aus PDFs übernehmen
    """
    logger.info("="*60)
    logger.info("NOVEMBER IMPORT - SIMPLE VERSION")
    logger.info("="*60)
    
    # Backup
    backup_path = f"{DB_PATH}.backup_simple_{datetime.now().strftime('%H%M%S')}"
    shutil.copy2(DB_PATH, backup_path)
    logger.info(f"Backup: {backup_path}\n")
    
    # DB-Verbindung
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Lade Konto-Mapping
    cursor.execute("SELECT id, iban, kontoname FROM konten WHERE iban IS NOT NULL")
    iban_to_konto = {}
    for konto_id, iban, name in cursor.fetchall():
        iban_clean = iban.replace(' ', '').upper()
        iban_to_konto[iban_clean] = {'id': konto_id, 'name': name}
    
    # Finde ALLE November PDFs
    all_pdfs = []
    for subdir in PDF_BASE_PATH.iterdir():
        if subdir.is_dir():
            patterns = ['*11.25*.pdf', '*11_25*.pdf', '*November*25*.pdf']
            for pattern in patterns:
                all_pdfs.extend(subdir.glob(pattern))
    
    logger.info(f"Gefunden: {len(all_pdfs)} PDFs\n")
    
    # Stats
    total_imported = 0
    total_skipped = 0
    
    # Importiere JEDES PDF einzeln - keine Abhängigkeiten!
    for pdf_path in sorted(all_pdfs):
        logger.info(f"📄 {pdf_path.name}")
        
        try:
            # Parse PDF
            parser = GenobankUniversalParser(str(pdf_path))
            transactions = parser.parse()
            
            if not transactions or not parser.iban:
                logger.info("   ⚠️ Übersprungen (keine Daten)\n")
                total_skipped += 1
                continue
            
            # Finde Konto
            iban_clean = parser.iban.replace(' ', '').upper()
            if iban_clean not in iban_to_konto:
                logger.info(f"   ⚠️ Unbekannte IBAN: {iban_clean}\n")
                total_skipped += 1
                continue
            
            konto = iban_to_konto[iban_clean]
            konto_id = konto['id']
            
            # Importiere Transaktionen - NIMM SALDEN AUS PDF!
            imported = 0
            duplicates = 0
            
            for tx in transactions:
                # Duplikat-Check
                cursor.execute("""
                    SELECT COUNT(*) FROM transaktionen
                    WHERE konto_id = ? 
                    AND buchungsdatum = ?
                    AND ABS(betrag - ?) < 0.01
                    AND verwendungszweck LIKE ?
                """, (
                    konto_id,
                    tx['buchungsdatum'].strftime('%Y-%m-%d'),
                    tx['betrag'],
                    tx['verwendungszweck'][:50] + '%'
                ))
                
                if cursor.fetchone()[0] > 0:
                    duplicates += 1
                    continue
                
                # INSERT - mit Saldo aus PDF!
                cursor.execute("""
                    INSERT INTO transaktionen (
                        konto_id, buchungsdatum, valutadatum,
                        verwendungszweck, betrag, 
                        saldo_nach_buchung,  -- DIREKT AUS PDF!
                        pdf_quelle, importiert_am
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    konto_id,
                    tx['buchungsdatum'].strftime('%Y-%m-%d'),
                    tx['valutadatum'].strftime('%Y-%m-%d'),
                    tx['verwendungszweck'],
                    tx['betrag'],
                    tx.get('saldo_nach_buchung'),  # AUS PDF!
                    str(pdf_path),
                    datetime.now()
                ))
                imported += 1
            
            conn.commit()
            
            # Log
            logger.info(f"   ✓ Konto: {konto['name']}")
            logger.info(f"   ✓ Importiert: {imported}, Duplikate: {duplicates}")
            if parser.endsaldo:
                logger.info(f"   ✓ Endsaldo: {parser.endsaldo:,.2f} EUR")
            logger.info("")
            
            total_imported += imported
            
        except Exception as e:
            logger.error(f"   ❌ Fehler: {e}\n")
            total_skipped += 1
    
    # Zusammenfassung
    logger.info("="*60)
    logger.info("FERTIG!")
    logger.info("="*60)
    logger.info(f"PDFs verarbeitet: {len(all_pdfs)}")
    logger.info(f"Transaktionen importiert: {total_imported}")
    logger.info(f"PDFs übersprungen: {total_skipped}")
    
    # Zeige aktuelle Salden
    logger.info("\nAKTUELLE SALDEN (letzter bekannter Stand):")
    cursor.execute("""
        SELECT 
            k.kontoname,
            MAX(t.buchungsdatum) as datum,
            (SELECT saldo_nach_buchung 
             FROM transaktionen 
             WHERE konto_id = k.id 
             ORDER BY buchungsdatum DESC, id DESC 
             LIMIT 1) as saldo
        FROM konten k
        JOIN transaktionen t ON k.id = t.konto_id
        WHERE t.buchungsdatum >= '2025-11-01'
        GROUP BY k.id
        ORDER BY k.kontoname
    """)
    
    for name, datum, saldo in cursor.fetchall():
        if saldo:
            logger.info(f"  {name:25} ({datum}): {saldo:>12,.2f} EUR")
    
    conn.close()
    logger.info("\n✅ Import abgeschlossen!")


if __name__ == "__main__":
    # Lösche erst alle November-Daten für sauberen Neustart
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM transaktionen WHERE buchungsdatum >= '2025-11-01'")
    count_before = cursor.fetchone()[0]
    
    if count_before > 0:
        logger.info(f"Lösche {count_before} November-Transaktionen für Neuimport...")
        cursor.execute("DELETE FROM transaktionen WHERE buchungsdatum >= '2025-11-01'")
        conn.commit()
    
    conn.close()
    
    # Jetzt simpel importieren
    import_november_simple()
