#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HypoVereinsbank PDF Parser - FINAL VERSION
Fix: Betrag steht DIREKT in der Buchungszeile, nicht in Folgezeilen!
"""

import pdfplumber
import re
from datetime import datetime

def parse_hypovereinsbank_pdf(pdf_path):
    """Parst HypoVereinsbank PDF und extrahiert Transaktionen"""

    transactions = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            
            # IBAN aus erster Seite
            iban = None
            if pdf.pages:
                first_text = pdf.pages[0].extract_text()
                iban_match = re.search(r'IBAN\s+(DE\d{20})', first_text)
                iban = iban_match.group(1) if iban_match else None

            # Alle Seiten durchgehen
            for page in pdf.pages:
                text = page.extract_text()
                
                if not text:
                    continue
                    
                lines = text.split('\n')

                i = 0
                while i < len(lines):
                    line = lines[i].strip()

                    # NEUE LOGIK: Buchungszeile hat Format:
                    # DD.MM.YYYY DD.MM.YYYY BUCHUNGSTEXT BETRAG EUR
                    # Betrag steht AM ENDE der Zeile!
                    
                    # Suche nach Datum-Pattern mit Betrag am Ende
                    match = re.match(r'^(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\.\d{2}\.\d{4})\s+(.+?)\s+([-]?\d{1,3}(?:\.\d{3})*,\d{2})\s+EUR\s*$', line)

                    if match:
                        buchungsdatum = match.group(1)
                        valutadatum = match.group(2)
                        transaktionstyp = match.group(3).strip()
                        betrag_str = match.group(4)
                        
                        # Parse Betrag
                        betrag = float(betrag_str.replace('.', '').replace(',', '.'))
                        
                        # Sammle Verwendungszweck aus Folgezeilen
                        verwendungszweck_lines = [transaktionstyp]
                        i += 1
                        
                        # Sammle alle Zeilen bis zur nächsten Buchung
                        while i < len(lines):
                            next_line = lines[i].strip()
                            
                            # Stopp wenn nächste Buchungszeile beginnt
                            if re.match(r'^\d{2}\.\d{2}\.\d{4}\s+\d{2}\.\d{2}\.\d{4}', next_line):
                                break
                            
                            # Stopp bei Seitenumbruch oder Footer
                            if not next_line or 'Seite' in next_line or 'https://' in next_line:
                                i += 1
                                break
                                
                            # Normale Verwendungszweck-Zeile
                            if next_line:
                                verwendungszweck_lines.append(next_line)
                            
                            i += 1

                        verwendungszweck = ' '.join(verwendungszweck_lines)

                        # Kürze überlange Verwendungszwecke
                        if len(verwendungszweck) > 500:
                            verwendungszweck = verwendungszweck[:497] + "..."

                        transactions.append({
                            'buchungsdatum': buchungsdatum,
                            'valutadatum': valutadatum,
                            'verwendungszweck': verwendungszweck,
                            'betrag': betrag,
                            'iban': iban
                        })
                    else:
                        i += 1

            return transactions

    except Exception as e:
        print(f"❌ Fehler beim Parsen: {e}")
        import traceback
        traceback.print_exc()
        return []


# Test
if __name__ == "__main__":
    import os
    
    pdf_path = '/share/CACHEDEV1_DATA/remote_shares/srvrdb01_allgemein/Buchhaltung/Kontoauszüge/Hypovereinsbank/HV Kontoauszug 01.08.24.pdf'

    print("🔍 Parsing HypoVereinsbank PDF (FINAL)...")
    print("="*70)
    print(f"PDF: {os.path.basename(pdf_path)}\n")

    transactions = parse_hypovereinsbank_pdf(pdf_path)

    print(f"✅ {len(transactions)} Transaktionen gefunden!\n")

    # Zeige erste 10
    for i, t in enumerate(transactions[:10], 1):
        print(f"{i:2d}. {t['buchungsdatum']} | {t['betrag']:>12,.2f} EUR | {t['verwendungszweck'][:60]}")

    # Suche AMAZON
    for t in transactions:
        if 'AMAZON' in t['verwendungszweck'].upper():
            print(f"\n🔍 AMAZON TRANSAKTION:")
            print(f"   Datum: {t['buchungsdatum']}")
            print(f"   Betrag: {t['betrag']:,.2f} EUR")
            print(f"   Text: {t['verwendungszweck'][:80]}")
            
            if abs(t['betrag']) < 100:
                print(f"   ✅ BETRAG KORREKT!")
            else:
                print(f"   ❌ BETRAG FALSCH!")
            break

    if transactions:
        print(f"\n💰 Summe: {sum(t['betrag'] for t in transactions):,.2f} EUR")
