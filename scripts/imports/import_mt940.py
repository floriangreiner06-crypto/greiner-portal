#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT940 Import für Bankenspiegel V2 - FINAL CORRECT
TAG 136: PostgreSQL-kompatibel via db_utils
"""

import sys
import argparse
from pathlib import Path
import mt940
import re

# Projekt-Pfad hinzufügen
sys.path.insert(0, '/opt/greiner-portal')
from api.db_utils import db_session, row_to_dict
from api.db_connection import sql_placeholder, get_db_type, get_db

class MT940Importer:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.ph = None  # Placeholder für SQL
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
        # TAG 144: get_db() statt db_session().__enter__() für korrekte PostgreSQL-Verbindung
        self.conn = get_db()
        self.cursor = self.conn.cursor()
        self.ph = sql_placeholder()

    def close(self):
        if self.conn:
            self.conn.close()
    
    def get_konto_id_by_number(self, kontonummer):
        ph = self.ph
        self.cursor.execute(f"SELECT id FROM konten WHERE kontonummer = {ph}", (kontonummer,))
        result = self.cursor.fetchone()
        if result:
            row = row_to_dict(result)
            return row['id']

        # LTRIM funktioniert in beiden DBs
        self.cursor.execute(
            f"SELECT id FROM konten WHERE LTRIM(kontonummer, '0') = LTRIM({ph}, '0')",
            (kontonummer,)
        )
        result = self.cursor.fetchone()
        if result:
            row = row_to_dict(result)
            return row['id']
        return None
    
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
        ph = self.ph
        self.cursor.execute(
            f"""SELECT COUNT(*) as cnt FROM transaktionen
               WHERE konto_id = {ph} AND buchungsdatum = {ph} AND betrag = {ph} AND verwendungszweck = {ph}""",
            (konto_id, buchungsdatum, betrag, verwendungszweck)
        )
        row = row_to_dict(self.cursor.fetchone())
        return row['cnt'] > 0

    def saldo_exists(self, konto_id, datum):
        """Prüft ob Saldo für dieses Datum existiert"""
        ph = self.ph
        self.cursor.execute(
            f"""SELECT COUNT(*) as cnt FROM salden WHERE konto_id = {ph} AND datum = {ph}""",
            (konto_id, datum)
        )
        row = row_to_dict(self.cursor.fetchone())
        return row['cnt'] > 0
    
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
        """Parst Salden aus MT940 - Schlusssaldo (62F) hat Prioritaet ueber Anfangssaldo (60F)"""
        salden_imported = 0
        salden_updated = 0

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Dictionary: Datum -> (saldo, typ) wobei typ = '60F' oder '62F'
            salden_dict = {}

            # :60F: (Anfangssaldo) - wird zuerst gesammelt
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

                # Nur setzen wenn noch nicht vorhanden
                if datum not in salden_dict:
                    salden_dict[datum] = (saldo, '60F')

            # :62F: (Schlusssaldo) - UEBERSCHREIBT immer den Anfangssaldo!
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

                # Schlusssaldo ueberschreibt IMMER den Anfangssaldo
                salden_dict[datum] = (saldo, '62F')

            # Importieren - INSERT oder UPDATE
            ph = self.ph
            for datum, (saldo, typ) in salden_dict.items():
                if not self.saldo_exists(konto_id, datum):
                    # Neuer Eintrag
                    self.cursor.execute(
                        f"""INSERT INTO salden (konto_id, datum, saldo, quelle, import_datei)
                           VALUES ({ph}, {ph}, {ph}, 'MT940', {ph})""",
                        (konto_id, datum, saldo, file_path.name)
                    )
                    salden_imported += 1
                else:
                    # Update wenn 62F (Schlusssaldo)
                    if typ == '62F':
                        self.cursor.execute(
                            f"""UPDATE salden SET saldo = {ph}, import_datei = {ph}
                               WHERE konto_id = {ph} AND datum = {ph}""",
                            (saldo, file_path.name, konto_id, datum)
                        )
                        salden_updated += 1
                    else:
                        self.stats['salden_duplicates'] += 1

            self.stats['salden_imported'] += salden_imported
            if salden_updated > 0:
                print(f"   Salden aktualisiert: {salden_updated} (Schlusssaldo)")
            return salden_imported + salden_updated

        except Exception as e:
            print(f"   Salden-Fehler: {e}")
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

            ph = self.ph
            self.cursor.execute(
                f"""INSERT INTO transaktionen (
                    konto_id, buchungsdatum, valutadatum, betrag, buchungstext,
                    verwendungszweck, gegenkonto_iban, gegenkonto_name,
                    import_quelle, import_datei
                ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, 'MT940', {ph})""",
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
        ph = self.ph
        self.cursor.execute(f"SELECT kontoname FROM konten WHERE id = {ph}", (konto_id,))
        result = self.cursor.fetchone()
        if result:
            row = row_to_dict(result)
            return row['kontoname']
        return "Unbekannt"
    
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
    # --db Argument wird ignoriert, db_session nutzt Umgebungsvariable

    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.exists():
        print(f"❌ Verzeichnis nicht gefunden")
        sys.exit(1)

    importer = MT940Importer()

    try:
        importer.connect()
        importer.import_directory(directory)
        importer.print_statistics()
    finally:
        importer.close()


if __name__ == '__main__':
    main()
