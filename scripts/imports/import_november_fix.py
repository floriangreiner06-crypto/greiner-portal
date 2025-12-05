#!/usr/bin/env python3
"""Einfacher November-Import - funktioniert mit Dicts UND Objects"""
import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
sys.path.insert(0, '/opt/greiner-portal')
from parsers.parser_factory import ParserFactory

DB = Path("/opt/greiner-portal/data/greiner_controlling.db")

def get_attr(obj, key, default=None):
    """Helper: Dict oder Object-Attribut holen"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def import_pdf(pdf_path):
    """Importiert ein PDF"""
    try:
        parser = ParserFactory.create_parser(str(pdf_path))
        result = parser.parse()
        
        # Transaktionen (Dict oder Object)
        transactions = result.get('transactions', []) if isinstance(result, dict) else result
        
        if not transactions:
            print(f"  ⊘ {pdf_path.name}: 0 TX")
            return 0
        
        # IBAN → Konto-ID
        conn = sqlite3.connect(str(DB))
        cursor = conn.cursor()
        
        imported = 0
        for tx in transactions:
            buchung = get_attr(tx, 'buchungsdatum')
            valuta = get_attr(tx, 'valutadatum') or buchung
            zweck = get_attr(tx, 'verwendungszweck', '')[:500]
            betrag = get_attr(tx, 'betrag', 0)
            
            if not buchung:
                continue
            
            # Finde Konto (erste Transaktion hat IBAN)
            if imported == 0:
                # Aus PDF-Text IBAN extrahieren
                import pdfplumber
                with pdfplumber.open(str(pdf_path)) as pdf:
                    text = pdf.pages[0].extract_text() or ""
                    import re
                    ibans = re.findall(r'DE\d{20}', text.replace(' ', ''))
                    if ibans:
                        cursor.execute("SELECT id FROM konten WHERE iban = ?", (ibans[0],))
                        row = cursor.fetchone()
                        if row:
                            konto_id = row[0]
                        else:
                            print(f"  ⊘ IBAN {ibans[0]} nicht gefunden")
                            return 0
                    else:
                        print(f"  ⊘ Keine IBAN gefunden")
                        return 0
            
            # Duplikat-Check
            cursor.execute("""
                SELECT COUNT(*) FROM transaktionen
                WHERE konto_id=? AND buchungsdatum=? AND betrag=?
            """, (konto_id, buchung, betrag))
            
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO transaktionen 
                    (konto_id, buchungsdatum, valutadatum, verwendungszweck, betrag, waehrung, importiert_am)
                    VALUES (?, ?, ?, ?, ?, 'EUR', ?)
                """, (konto_id, buchung, valuta, zweck, betrag, datetime.now()))
                imported += 1
        
        conn.commit()
        conn.close()
        
        print(f"  ✅ {pdf_path.name}: {imported} TX")
        return imported
        
    except Exception as e:
        print(f"  ❌ {pdf_path.name}: {e}")
        return 0

# Hauptprogramm
pdf_dir = Path("/mnt/buchhaltung/Buchhaltung/Kontoauszüge")
total = 0

for bank_dir in pdf_dir.iterdir():
    if not bank_dir.is_dir():
        continue
    
    print(f"\n📁 {bank_dir.name}")
    for pdf in sorted(bank_dir.glob("*.pdf")):
        # Nur November-PDFs
        if '11.25' in pdf.name or '11-25' in pdf.name or 'Nov' in pdf.name:
            total += import_pdf(pdf)

print(f"\n✅ GESAMT: {total} Transaktionen importiert")

# Endsalden speichern
print("\n📊 Extrahiere Endsalden...")

pdf_dir = Path("/mnt/buchhaltung/Buchhaltung/Kontoauszüge")
conn = sqlite3.connect(str(DB))
cursor = conn.cursor()

for bank_dir in pdf_dir.iterdir():
    if not bank_dir.is_dir():
        continue
    
    for pdf in sorted(bank_dir.glob("*11.25*.pdf")):
        try:
            parser = ParserFactory.create_parser(str(pdf))
            result = parser.parse()
            
            # Endsaldo aus Result holen
            endsaldo = result.get('endsaldo') if isinstance(result, dict) else getattr(result, 'endsaldo', None)
            
            if not endsaldo:
                continue
            
            # IBAN → Konto-ID
            import pdfplumber
            with pdfplumber.open(str(pdf)) as pdf_obj:
                text = pdf_obj.pages[0].extract_text() or ""
                import re
                ibans = re.findall(r'DE\d{20}', text.replace(' ', ''))
                if not ibans:
                    continue
                
                cursor.execute("SELECT id FROM konten WHERE iban = ?", (ibans[0],))
                row = cursor.fetchone()
                if not row:
                    continue
                
                konto_id = row[0]
                
                # Datum
                match = re.search(r'(\d{2})\.(\d{2})\.(\d{2})', pdf.name)
                if match:
                    day, month, year = match.groups()
                    datum = f"20{year}-{month}-{day}"
                    
                    # Speichern
                    cursor.execute("""
                        SELECT COUNT(*) FROM kontostand_historie
                        WHERE konto_id = ? AND datum = ?
                    """, (konto_id, datum))
                    
                    if cursor.fetchone()[0] == 0:
                        cursor.execute("""
                            INSERT INTO kontostand_historie (konto_id, datum, saldo, quelle, erfasst_am)
                            VALUES (?, ?, ?, 'PDF_Import', ?)
                        """, (konto_id, datum, endsaldo, datetime.now()))
                        print(f"  ✅ {pdf.name}: {endsaldo:.2f} EUR")
        except:
            pass

conn.commit()
conn.close()
print("\n✅ Endsalden extrahiert!")
