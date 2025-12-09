#!/usr/bin/env python3
"""
HypoVereinsbank PDF Parser für Bankenspiegel V2
Extrahiert Transaktionen und Salden aus HVB Kontoauszügen
Version: 2.0 (für V2-DB-Struktur)
"""

import re
import pdfplumber
from datetime import datetime
from decimal import Decimal


class HypoVereinsbankParser:
    """Parser für HypoVereinsbank PDF-Kontoauszüge"""
    
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.iban = None
        self.kontonummer = None
        self.saldo_datum = None
        self.endsaldo = None
        self.transactions = []
        
    def parse(self):
        """Hauptmethode zum Parsen des PDFs"""
        with pdfplumber.open(self.pdf_path) as pdf:
            # Erste Seite für Metadaten
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            
            # IBAN extrahieren
            self._extract_iban(text)
            
            # Kontonummer extrahieren
            self._extract_kontonummer(text)
            
            # Saldo extrahieren
            self._extract_saldo(text)
            
            # Transaktionen von allen Seiten extrahieren
            for page in pdf.pages:
                self._extract_transactions_from_page(page)
        
        return {
            'iban': self.iban,
            'kontonummer': self.kontonummer,
            'saldo_datum': self.saldo_datum,
            'endsaldo': self.endsaldo,
            'transactions': self.transactions
        }
    
    def _extract_iban(self, text):
        """IBAN aus Text extrahieren"""
        match = re.search(r'IBAN\s+([A-Z]{2}\d{2}\s?\d+)', text)
        if match:
            self.iban = match.group(1).replace(' ', '')
    
    def _extract_kontonummer(self, text):
        """Kontonummer extrahieren"""
        match = re.search(r'Konto-Nr\.\s+(\d+)', text)
        if match:
            self.kontonummer = match.group(1)
    
    def _extract_saldo(self, text):
        """Kontostand (Endsaldo) extrahieren"""
        # Format: "Kontostand am 18.11.2025 161.007,32 EUR"
        match = re.search(r'Kontostand am (\d{2}\.\d{2}\.\d{4})\s+([-\d.,]+)\s+EUR', text)
        if match:
            # Datum konvertieren
            datum_str = match.group(1)
            self.saldo_datum = datetime.strptime(datum_str, '%d.%m.%Y').date()
            
            # Betrag konvertieren (deutsches Format)
            betrag_str = match.group(2).replace('.', '').replace(',', '.')
            self.endsaldo = float(betrag_str)
    
    def _extract_transactions_from_page(self, page):
        """Transaktionen von einer Seite extrahieren"""
        # Tabelle extrahieren
        tables = page.extract_tables()
        
        if not tables:
            return
        
        # Erste Tabelle nutzen
        table = tables[0]
        
        for row in table:
            if len(row) < 4:
                continue
            
            buchung_str = row[0]
            valuta_str = row[1]
            verwendungszweck = row[2]
            betrag_str = row[3]
            
            # Nur Zeilen mit Datum parsen
            if not buchung_str or not re.match(r'\d{2}\.\d{2}\.\d{4}', buchung_str):
                continue
            
            try:
                # Datum parsen
                buchungsdatum = datetime.strptime(buchung_str.strip(), '%d.%m.%Y').date()
                valutadatum = datetime.strptime(valuta_str.strip(), '%d.%m.%Y').date()
                
                # Betrag parsen (deutsches Format: -2.240,57 EUR)
                betrag_clean = betrag_str.replace('EUR', '').strip()
                betrag_clean = betrag_clean.replace('.', '').replace(',', '.')
                betrag = float(betrag_clean)
                
                # Verwendungszweck aufräumen
                zweck = verwendungszweck.strip() if verwendungszweck else ''
                zweck = ' '.join(zweck.split())  # Mehrfache Leerzeichen entfernen
                
                # Transaktion speichern
                transaction = {
                    'buchungsdatum': buchungsdatum,
                    'valutadatum': valutadatum,
                    'betrag': betrag,
                    'verwendungszweck': zweck,
                    'gegenkonto': None,  # HVB PDFs haben kein IBAN in Tabelle
                }
                
                self.transactions.append(transaction)
                
            except (ValueError, AttributeError) as e:
                # Fehlerhafte Zeile überspringen
                continue
    
    def get_summary(self):
        """Zusammenfassung der Parse-Ergebnisse"""
        return {
            'iban': self.iban,
            'kontonummer': self.kontonummer,
            'saldo_datum': self.saldo_datum,
            'endsaldo': self.endsaldo,
            'anzahl_transaktionen': len(self.transactions),
            'summe_ein': sum(t['betrag'] for t in self.transactions if t['betrag'] > 0),
            'summe_aus': sum(t['betrag'] for t in self.transactions if t['betrag'] < 0),
        }


# Test-Funktion
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 hypovereinsbank_parser_v2.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    print("=" * 80)
    print("HYPOVEREINSBANK PARSER V2 - TEST")
    print("=" * 80)
    
    parser = HypoVereinsbankParser(pdf_path)
    result = parser.parse()
    
    print(f"\n✅ IBAN: {result['iban']}")
    print(f"✅ Kontonummer: {result['kontonummer']}")
    print(f"✅ Saldo-Datum: {result['saldo_datum']}")
    print(f"✅ Endsaldo: {result['endsaldo']:,.2f} EUR")
    print(f"✅ Transaktionen: {len(result['transactions'])}")
    
    if result['transactions']:
        print("\nERSTE 3 TRANSAKTIONEN:")
        for i, tx in enumerate(result['transactions'][:3]):
            print(f"  {i+1}. {tx['buchungsdatum']} | {tx['betrag']:>12,.2f} EUR")
            print(f"     {tx['verwendungszweck'][:60]}...")
        
        print("\nLETZTE 3 TRANSAKTIONEN:")
        for i, tx in enumerate(result['transactions'][-3:]):
            print(f"  {len(result['transactions'])-2+i}. {tx['buchungsdatum']} | {tx['betrag']:>12,.2f} EUR")
            print(f"     {tx['verwendungszweck'][:60]}...")
    
    summary = parser.get_summary()
    print(f"\n📊 ZUSAMMENFASSUNG:")
    print(f"   Eingänge:  {summary['summe_ein']:>12,.2f} EUR")
    print(f"   Ausgänge:  {summary['summe_aus']:>12,.2f} EUR")
    print(f"   Differenz: {summary['summe_ein'] + summary['summe_aus']:>12,.2f} EUR")
    
    print("\n" + "=" * 80)
