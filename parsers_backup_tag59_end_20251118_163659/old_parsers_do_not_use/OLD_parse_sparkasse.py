#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sparkasse PDF Parser (mit pdfplumber) - FIXED
"""

import pdfplumber
import re
from datetime import datetime

def parse_sparkasse_pdf(pdf_path):
    """Parst Sparkasse PDF und extrahiert Transaktionen"""
    
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            # IBAN extrahieren
            iban_match = re.search(r'(DE\d{2}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{2})', full_text)
            iban = iban_match.group(1).replace(" ", "") if iban_match else None
            
            lines = full_text.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # FIXED: Kein Leerzeichen zwischen Datum und Text!
                date_match = re.match(r'^(\d{2}\.\d{2}\.\d{4})(.+)', line)
                
                if date_match:
                    datum = date_match.group(1)
                    rest = date_match.group(2).strip()
                    
                    # Überspringe "Kontostand am..." Zeilen
                    if 'Kontostand am' in rest or not rest:
                        continue
                    
                    # Suche Betrag in der gleichen Zeile (am Ende)
                    betrag_match = re.search(r'([-]?\d{1,3}(?:\.\d{3})*,\d{2})$', line)
                    
                    if betrag_match:
                        betrag_str = betrag_match.group(1)
                        betrag = float(betrag_str.replace('.', '').replace(',', '.'))
                        
                        # Verwendungszweck = alles zwischen Datum und Betrag
                        verwendungszweck = line[len(datum):betrag_match.start()].strip()
                        
                        # Sammle zusätzliche Zeilen (bis zur nächsten Transaktion)
                        zusatz_lines = []
                        j = i + 1
                        while j < len(lines) and j < i + 5:  # Max 5 Zeilen voraus
                            next_line = lines[j].strip()
                            
                            # Stop wenn neue Transaktion beginnt
                            if re.match(r'^\d{2}\.\d{2}\.\d{4}', next_line):
                                break
                            
                            # Stop bei leeren Zeilen oder Fußzeilen
                            if not next_line or 'Sparkasse Deggendorf' in next_line or 'Vorstand' in next_line:
                                break
                            
                            zusatz_lines.append(next_line)
                            j += 1
                        
                        # Kombiniere Verwendungszweck
                        if zusatz_lines:
                            verwendungszweck = verwendungszweck + " " + " ".join(zusatz_lines)
                        
                        # Kürze überlange Verwendungszwecke
                        if len(verwendungszweck) > 500:
                            verwendungszweck = verwendungszweck[:497] + "..."
                        
                        transactions.append({
                            'buchungsdatum': datum,
                            'valutadatum': datum,
                            'verwendungszweck': verwendungszweck,
                            'betrag': betrag,
                            'iban': iban
                        })
            
            return transactions
            
    except Exception as e:
        print(f"❌ Fehler beim Parsen: {e}")
        import traceback
        traceback.print_exc()
        return []


# Test
if __name__ == "__main__":
    pdf_path = '/share/CACHEDEV1_DATA/remote_shares/srvrdb01_allgemein/Buchhaltung/Kontoauszüge/Sparkasse/Konto_0760036467-Auszug_2025_0009.pdf'
    
    print("🔍 Parsing Sparkasse PDF...")
    print("="*70)
    
    transactions = parse_sparkasse_pdf(pdf_path)
    
    print(f"\n✅ {len(transactions)} Transaktionen gefunden!\n")
    
    for i, t in enumerate(transactions, 1):
        print(f"{i}. {t['buchungsdatum']} | {t['betrag']:>10.2f} EUR | {t['verwendungszweck'][:60]}")
    
    if transactions:
        print(f"\n💰 Summe: {sum(t['betrag'] for t in transactions):.2f} EUR")
        print(f"🏦 IBAN: {transactions[0]['iban']}")

