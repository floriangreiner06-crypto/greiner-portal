#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT940 Import für Bankenspiegel V2 - FINAL CORRECT
"""

import sys
import sqlite3
import argparse
from pathlib import Path
import mt940
import re

class MT940Importer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.stats = {
            'files_read': 0,
            'files_imported': 0,
            'transactions_imported': 0,
            'transactions_duplicates': 0,
            'salden_imported': 0,
            'salden_duplicates': 0,
            'errors': 0
        }
    
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def get_konto_id_by_number(self, kontonummer):
        self.cursor.execute("SELECT id FROM konten WHERE kontonummer = ?", (kontonummer,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        
        self.cursor.execute(
            "SELECT id FROM konten WHERE LTRIM(kontonummer, '0') = LTRIM(?, '0')",
            (kontonummer,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def extract_kontonummer(self, filename):
        match = re.search(r'Umsaetze[_\s]+(\d+)[_\s]+', filename, re.IGNORECASE)
        if match:
            return match.group(1)
        
        match = re.search(r'-(\d{6,})-', filename)
        if match:
            return match.group(1)
        
        match = re.search(r'(\d{6,})', filename)
        if match:
            return match.group(1)
        
        return None
    
    def transaction_exists(self, konto_id, buchungsdatum, betrag, verwendungszweck):
        self.cursor.execute(
            """SELECT COUNT(*) FROM transaktionen 
               WHERE konto_id = ? AND buchungsdatum = ? AND betrag = ? AND verwendungszweck = ?""",
            (konto_id, buchungsdatum, betrag, verwendungszweck)
        )
        return self.cursor.fetchone()[0] > 0
    
    def saldo_exists(self, konto_id, datum):
        """Prüft ob Saldo für dieses Datum existiert"""
        self.cursor.execute(
            """SELECT COUNT(*) FROM salden WHERE konto_id = ? AND datum = ?""",
            (konto_id, datum)
        )
        return self.cursor.fetchone()[0] > 0
    
    def date_to_string(self, date_obj):
        if date_obj is None:
            return None
        if isinstance(date_obj, str):
            return date_obj
        if hasattr(date_obj, 'isoformat'):
            return date_obj.isoformat()
        if hasattr(date_obj, 'strftime'):
            return date_obj.strftime('%Y-%m-%d')
        return str(date_obj)
    
    def parse_salden_from_file(self, file_path, konto_id):
        """Parst Salden aus MT940"""
        salden_imported = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Alle Salden sammeln (60F und 62F)
            all_salden = []
            
            # :60F: (Anfangssaldo)
            for match in re.finditer(r':60F:([CD])(\d{6})EUR([\d,\.]+)', content):
                vorzeichen = match.group(1)
                datum_str = match.group(2)
                betrag_str = match.group(3).replace(',', '.')
                
                jahr = '20' + datum_str[0:2]
                monat = datum_str[2:4]
                tag = datum_str[4:6]
                datum = f"{jahr}-{monat}-{tag}"
                
                saldo = float(betrag_str)
                if vorzeichen == 'D':
                    saldo = -saldo
                
                all_salden.append((datum, saldo))
            
            # :62F: (Schlusssaldo)
            for match in re.finditer(r':62F:([CD])(\d{6})EUR([\d,\.]+)', content):
                vorzeichen = match.group(1)
                datum_str = match.group(2)
                betrag_str = match.group(3).replace(',', '.')
                
                jahr = '20' + datum_str[0:2]
                monat = datum_str[2:4]
                tag = datum_str[4:6]
                datum = f"{jahr}-{monat}-{tag}"
                
                saldo = float(betrag_str)
                if vorzeichen == 'D':
                    saldo = -saldo
                
                all_salden.append((datum, saldo))
            
            # Importieren (eindeutige Kombinationen)
            seen = set()
            for datum, saldo in all_salden:
                key = (datum, saldo)
                if key in seen:
                    continue
                seen.add(key)
                
                if not self.saldo_exists(konto_id, datum):
                    self.cursor.execute(
                        """INSERT INTO salden (konto_id, datum, saldo, quelle, import_datei)
                           VALUES (?, ?, ?, 'MT940', ?)""",
                        (konto_id, datum, saldo, file_path.name)
                    )
                    salden_imported += 1
                else:
                    self.stats['salden_duplicates'] += 1
            
            self.stats['salden_imported'] += salden_imported
            return salden_imported
            
        except Exception as e:
            print(f"   ⚠️  Salden-Fehler: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def import_transaction_from_statement(self, konto_id, statement_data, import_datei):
        try:
            buchungsdatum = self.date_to_string(statement_data.get('date'))
            valutadatum = self.date_to_string(statement_data.get('entry_date') or statement_data.get('date'))
            
            amount_obj = statement_data.get('amount')
            if hasattr(amount_obj, 'amount'):
                betrag = float(amount_obj.amount)
            else:
                betrag = float(amount_obj) if amount_obj else 0.0
            
            zweck_parts = []
            if statement_data.get('purpose'):
                zweck_parts.append(statement_data['purpose'])
            if statement_data.get('applicant_name'):
                zweck_parts.append(statement_data['applicant_name'])
            if statement_data.get('recipient_name'):
                zweck_parts.append(statement_data['recipient_name'])
            verwendungszweck = ' '.join(zweck_parts) or 'N/A'
            
            buchungstext = statement_data.get('posting_text') or statement_data.get('transaction_code') or 'N/A'
            gegenkonto_iban = statement_data.get('applicant_iban') or statement_data.get('gvc_applicant_iban')
            gegenkonto_name = statement_data.get('applicant_name') or statement_data.get('recipient_name')
            
            if self.transaction_exists(konto_id, buchungsdatum, betrag, verwendungszweck):
                self.stats['transactions_duplicates'] += 1
                return False
            
            self.cursor.execute(
                """INSERT INTO transaktionen (
                    konto_id, buchungsdatum, valutadatum, betrag, buchungstext,
                    verwendungszweck, gegenkonto_iban, gegenkonto_name,
                    import_quelle, import_datei
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'MT940', ?)""",
                (konto_id, buchungsdatum, valutadatum, betrag, buchungstext, 
                 verwendungszweck, gegenkonto_iban, gegenkonto_name, import_datei)
            )
            self.stats['transactions_imported'] += 1
            return True
            
        except Exception as e:
            print(f"   ⚠️  TX-Fehler: {e}")
            self.stats['errors'] += 1
            return False
    
    def get_konto_name(self, konto_id):
        self.cursor.execute("SELECT kontoname FROM konten WHERE id = ?", (konto_id,))
        result = self.cursor.fetchone()
        return result[0] if result else "Unbekannt"
    
    def import_file(self, file_path):
        print(f"\n{'='*80}")
        print(f"📄 {file_path.name}")
        
        self.stats['files_read'] += 1
        
        kontonummer = self.extract_kontonummer(file_path.name)
        if not kontonummer:
            print(f"   ❌ Kontonummer nicht erkennbar")
            self.stats['errors'] += 1
            return
        
        konto_id = self.get_konto_id_by_number(kontonummer)
        if not konto_id:
            print(f"   ❌ Konto nicht gefunden")
            self.stats['errors'] += 1
            return
        
        konto_name = self.get_konto_name(konto_id)
        print(f"   ✓ {konto_name} (ID {konto_id})")
        
        # SALDEN
        salden_count = self.parse_salden_from_file(file_path, konto_id)
        if salden_count > 0:
            print(f"   💰 Salden: {salden_count}")
        
        # TRANSAKTIONEN
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                statements = mt940.parse(f)
            
            tx_count = 0
            for statement in statements:
                if self.import_transaction_from_statement(konto_id, statement.data, file_path.name):
                    tx_count += 1
            
            if tx_count > 0:
                print(f"   ✅ TX: {tx_count}")
            
            self.stats['files_imported'] += 1
            
        except Exception as e:
            print(f"   ❌ {e}")
            self.stats['errors'] += 1
    
    def import_directory(self, directory):
        files = (list(directory.glob('*.mta')) + 
                list(directory.glob('*.mt940')) + 
                list(directory.glob('*.MT940')) +
                list(directory.glob('*.TXT')) +
                list(directory.glob('*.txt')))
        
        if not files:
            print(f"⚠️ Keine MT940-Dateien")
            return
        
        print(f"\n📂 {directory}")
        print(f"📁 {len(files)} Dateien")
        
        for file_path in sorted(files):
            self.import_file(file_path)
        
        self.conn.commit()
        print(f"\n✅ Gespeichert")
    
    def print_statistics(self):
        print(f"\n{'='*80}")
        print("📊 ZUSAMMENFASSUNG")
        print(f"{'='*80}")
        print(f"Dateien:            {self.stats['files_imported']}/{self.stats['files_read']}")
        print(f"Transaktionen:      {self.stats['transactions_imported']} (Duplikate: {self.stats['transactions_duplicates']})")
        print(f"Salden:             {self.stats['salden_imported']} (Duplikate: {self.stats['salden_duplicates']})")
        print(f"Fehler:             {self.stats['errors']}")
        print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=str)
    parser.add_argument('--db', type=str, default='/opt/greiner-portal/data/greiner_controlling.db')
    
    args = parser.parse_args()
    
    directory = Path(args.directory)
    if not directory.exists():
        print(f"❌ Verzeichnis nicht gefunden")
        sys.exit(1)
    
    importer = MT940Importer(args.db)
    
    try:
        importer.connect()
        importer.import_directory(directory)
        importer.print_statistics()
    finally:
        importer.close()


if __name__ == '__main__':
    main()
