#!/usr/bin/env python3
# Endsaldo-Extraktion für Sparkasse Online-Banking PDFs

import sys
import sqlite3
import re
from pathlib import Path
from datetime import datetime
import pdfplumber

def extract_endsaldo(pdf_path):
    """Extrahiert Endsaldo aus Sparkasse PDF"""
    with pdfplumber.open(str(pdf_path)) as pdf:
        text = pdf.pages[0].extract_text()
        
        # Suche nach: "7,46 EUR *" oder "2.274,58 EUR *"
        match = re.search(r'([\d.,]+)\s*EUR\s*\*', text)
        
        if match:
            betrag_str = match.group(1).replace('.', '').replace(',', '.')
            return float(betrag_str)
    
    return None

def save_endsaldo(konto_id, datum, saldo):
    """Speichert Endsaldo in kontostand_historie"""
    db_path = Path("/opt/greiner-portal/data/greiner_controlling.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Prüfe ob bereits vorhanden
    cursor.execute("""
        SELECT COUNT(*) FROM kontostand_historie
        WHERE konto_id = ? AND datum = ? AND quelle = 'PDF_Import'
    """, (konto_id, datum))
    
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO kontostand_historie (konto_id, datum, saldo, quelle, erfasst_am)
            VALUES (?, ?, ?, 'PDF_Import', ?)
        """, (konto_id, datum, saldo, datetime.now()))
        conn.commit()
        print(f"✅ Endsaldo gespeichert: {datum} | {saldo:.2f} EUR")
    else:
        print(f"⊘ Endsaldo bereits vorhanden: {datum}")
    
    conn.close()

# Test mit allen November-PDFs
pdf_dir = Path("/mnt/buchhaltung/Buchhaltung/Kontoauszüge/Sparkasse/")
for pdf_file in sorted(pdf_dir.glob("*Auszug*11.25*.pdf")):
    # Datum aus Dateinamen extrahieren: "SPK Auszug 17.11.25.pdf" -> 2025-11-17
    match = re.search(r'(\d{2})\.(\d{2})\.(\d{2})', pdf_file.name)
    if match:
        day, month, year = match.groups()
        datum = f"20{year}-{month}-{day}"
        
        endsaldo = extract_endsaldo(pdf_file)
        if endsaldo:
            print(f"📄 {pdf_file.name} | {datum} | {endsaldo:.2f} EUR")
            save_endsaldo(1, datum, endsaldo)  # konto_id=1 = Sparkasse
