#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transaction Manager fÃ¼r Bankenspiegel 3.0
=========================================
Verwaltet das Speichern von Transaktionen in der Datenbank

Features:
- Duplikats-Check
- Konto-Mapping via IBAN
- Batch-Import
- Transaktions-Validierung
- Statistiken

Author: Claude AI
Version: 3.0
Date: 2025-11-06
"""

import sqlite3
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path

from parsers import Transaction

logger = logging.getLogger(__name__)


class TransactionManager:
    """
    Verwaltet Transaktionen in der Datenbank
    
    Features:
    - Speichern mit Duplikats-Check
    - Konto-Mapping via IBAN
    - Batch-Operationen
    - Statistiken
    
    Usage:
        manager = TransactionManager('data/greiner_controlling.db')
        result = manager.save_transactions(transactions, 'sparkasse_2025.pdf')
    """
    
    def __init__(self, db_path: str = 'data/greiner_controlling.db'):
        """
        Initialisiert den Transaction Manager
        
        Args:
            db_path: Pfad zur SQLite-Datenbank (relativ zum Projekt-Root)
        """
        self.db_path = Path(db_path)
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Datenbank nicht gefunden: {db_path}")
        
        logger.info(f"Transaction Manager initialisiert: {self.db_path}")
    
    def save_transactions(
        self, 
        transactions: List[Transaction], 
        pdf_filename: str,
        skip_duplicates: bool = True
    ) -> Dict[str, int]:
        """
        Speichert Transaktionen in der Datenbank
        
        Args:
            transactions: Liste von Transaction-Objekten
            pdf_filename: Name der PDF-Datei (fÃ¼r Tracking)
            skip_duplicates: Duplikate Ã¼berspringen (default: True)
            
        Returns:
            Dictionary mit Statistiken:
            {
                'imported': Anzahl importierter Transaktionen,
                'duplicates': Anzahl Ã¼bersprungener Duplikate,
                'errors': Anzahl Fehler
            }
        """
        if not transactions:
            logger.warning("Keine Transaktionen zum Speichern")
            return {'imported': 0, 'duplicates': 0, 'errors': 0}
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        imported = 0
        duplicates = 0
        errors = 0
        
        try:
            for transaction in transactions:
                try:
                    # Konto-ID ermitteln (falls nicht gesetzt)
                    if not transaction.konto_id and transaction.iban:
                        transaction.konto_id = self._get_konto_id_by_iban(
                            cursor, transaction.iban
                        )
                    
                    if not transaction.konto_id:
                        logger.warning(
                            f"âš ï¸ Kein Konto gefunden fÃ¼r IBAN: {transaction.iban}"
                        )
                        errors += 1
                        continue
                    
                    # Duplikats-Check
                    if skip_duplicates:
                        if self._is_duplicate(cursor, transaction):
                            duplicates += 1
                            continue
                    
                    # Speichern
                    self._insert_transaction(cursor, transaction, pdf_filename)
                    imported += 1
                    
                except Exception as e:
                    logger.error(f"Fehler beim Speichern: {e}")
                    logger.error(f"Transaktion: {transaction}")
                    errors += 1
            
            # Commit
            conn.commit()
            
            # Log Zusammenfassung
            logger.info(f"âœ… Import abgeschlossen:")
            logger.info(f"   Importiert: {imported}")
            if duplicates > 0:
                logger.info(f"   Duplikate: {duplicates}")
            if errors > 0:
                logger.warning(f"   Fehler: {errors}")
            
        except Exception as e:
            logger.error(f"âŒ Fehler beim Batch-Import: {e}")
            conn.rollback()
            errors = len(transactions)
        
        finally:
            conn.close()
        
        return {
            'imported': imported,
            'duplicates': duplicates,
            'errors': errors
        }
    
    def _get_konto_id_by_iban(self, cursor, iban: str) -> Optional[int]:
        """
        Ermittelt Konto-ID anhand der IBAN
        
        Args:
            cursor: DB-Cursor
            iban: IBAN des Kontos
            
        Returns:
            Konto-ID oder None
        """
        cursor.execute("SELECT id FROM konten WHERE iban = ?", (iban,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def _is_duplicate(self, cursor, transaction: Transaction) -> bool:
        """
        PrÃ¼ft ob Transaktion bereits existiert
        
        Kriterien fÃ¼r Duplikat:
        - Gleiche Konto-ID
        - Gleiches Buchungsdatum
        - Gleicher Betrag
        - Gleicher Verwendungszweck
        
        Args:
            cursor: DB-Cursor
            transaction: Transaction-Objekt
            
        Returns:
            True wenn Duplikat, False sonst
        """
        cursor.execute("""
            SELECT COUNT(*) FROM transaktionen
            WHERE konto_id = ?
              AND buchungsdatum = ?
              AND betrag = ?
              AND verwendungszweck = ?
        """, (
            transaction.konto_id,
            transaction.buchungsdatum,
            transaction.betrag,
            transaction.verwendungszweck
        ))
        
        count = cursor.fetchone()[0]
        return count > 0
    
    def _insert_transaction(
        self, 
        cursor, 
        transaction: Transaction, 
        pdf_filename: str
    ):
        """
        FÃ¼gt Transaktion in Datenbank ein
        
        Args:
            cursor: DB-Cursor
            transaction: Transaction-Objekt
            pdf_filename: Name der PDF-Quelle
        """
        cursor.execute("""
            INSERT INTO transaktionen (
                konto_id,
                buchungsdatum,
                valutadatum,
                buchungstext,
                verwendungszweck,
                betrag,
                waehrung,
                pdf_quelle,
                importiert_am
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction.konto_id,
            transaction.buchungsdatum,
            transaction.valutadatum,
            'PDF-Import',  # Buchungstext
            transaction.verwendungszweck,
            transaction.betrag,
            'EUR',
            pdf_filename,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
    
    def get_account_info(self, iban: Optional[str] = None) -> List[Dict]:
        """
        Gibt Konto-Informationen zurÃ¼ck
        
        Args:
            iban: Optional - filtere nach IBAN
            
        Returns:
            Liste von Konten mit Informationen
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if iban:
            cursor.execute("""
                SELECT k.id, k.iban, k.kontoname, b.bank_name, k.aktiv
                FROM konten k
                LEFT JOIN banken b ON k.bank_id = b.id
                WHERE k.iban = ?
            """, (iban,))
        else:
            cursor.execute("""
                SELECT k.id, k.iban, k.kontoname, b.bank_name, k.aktiv
                FROM konten k
                LEFT JOIN banken b ON k.bank_id = b.id
                WHERE k.aktiv = 1
                ORDER BY b.bank_name, k.kontoname
            """)
        
        accounts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return accounts
    
    def get_transaction_stats(
        self, 
        konto_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict:
        """
        Gibt Transaktions-Statistiken zurÃ¼ck
        
        Args:
            konto_id: Optional - filtere nach Konto
            date_from: Optional - von Datum (YYYY-MM-DD)
            date_to: Optional - bis Datum (YYYY-MM-DD)
            
        Returns:
            Dictionary mit Statistiken
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Query bauen
        query = "SELECT COUNT(*), SUM(betrag), MIN(buchungsdatum), MAX(buchungsdatum) FROM transaktionen WHERE 1=1"
        params = []
        
        if konto_id:
            query += " AND konto_id = ?"
            params.append(konto_id)
        
        if date_from:
            query += " AND buchungsdatum >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND buchungsdatum <= ?"
            params.append(date_to)
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        conn.close()
        
        return {
            'count': row[0] or 0,
            'total_amount': row[1] or 0.0,
            'date_from': row[2],
            'date_to': row[3]
        }
    
    def validate_database(self) -> Dict[str, bool]:
        """
        Validiert die Datenbank-Struktur
        
        Returns:
            Dictionary mit Validierungs-Ergebnissen
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        results = {}
        
        # PrÃ¼fe Tabellen
        required_tables = ['transaktionen', 'konten', 'banken']
        for table in required_tables:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            )
            results[f'table_{table}'] = cursor.fetchone() is not None
        
        # PrÃ¼fe Spalten in transaktionen
        cursor.execute("PRAGMA table_info(transaktionen)")
        columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = [
            'id', 'konto_id', 'buchungsdatum', 'valutadatum',
            'verwendungszweck', 'betrag', 'waehrung'
        ]
        
        for col in required_columns:
            results[f'column_{col}'] = col in columns
        
        conn.close()
        
        # Alle Checks bestanden?
        results['all_valid'] = all(results.values())
        
        return results


# FÃ¼r Testing
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*70)
    print("TRANSACTION MANAGER - TEST")
    print("="*70)
    
    try:
        manager = TransactionManager()
        
        # DB-Validierung
        print("\n1. Datenbank-Validierung:")
        validation = manager.validate_database()
        for key, value in validation.items():
            status = "âœ“" if value else "âœ—"
            print(f"   {status} {key}")
        
        # Konten anzeigen
        print("\n2. VerfÃ¼gbare Konten:")
        accounts = manager.get_account_info()
        for acc in accounts[:5]:
            print(f"   â€¢ {acc['bank_name']:30} | {acc['kontoname']:30} | {acc['iban']}")
        
        # Statistiken
        print("\n3. Gesamt-Statistiken:")
        stats = manager.get_transaction_stats()
        print(f"   Transaktionen: {stats['count']:,}")
        print(f"   Gesamt-Betrag: {stats['total_amount']:,.2f} EUR")
        print(f"   Zeitraum: {stats['date_from']} bis {stats['date_to']}")
        
    except FileNotFoundError as e:
        print(f"\nâŒ Fehler: {e}")
        print("   Stelle sicher dass die Datenbank existiert: data/greiner_controlling.db")
    except Exception as e:
        print(f"\nâŒ Fehler: {e}")
        import traceback
        traceback.print_exc()
