"""Analysiere PDF für Auftrag 20853 - wie wird Summe Lohn berechnet?"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

use_pdfplumber = False
try:
    import PyPDF2
    pdf_available = True
except ImportError:
    pdf_available = False
    print("PyPDF2 nicht verfügbar, versuche pdfplumber...")
    try:
        import pdfplumber
        pdf_available = True
        use_pdfplumber = True
    except ImportError:
        print("Weder PyPDF2 noch pdfplumber verfügbar")
        use_pdfplumber = False

pdf_path = '/tmp/20853.pdf'

if not pdf_available:
    print("Keine PDF-Bibliothek verfügbar. Bitte installiere PyPDF2 oder pdfplumber.")
    sys.exit(1)

print(f"Analysiere PDF: {pdf_path}")
print("=" * 80)

if use_pdfplumber:
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"\n--- Seite {i+1} ---")
            text = page.extract_text()
            if text:
                print(text)
else:
    with open(pdf_path, 'rb') as f:
        pdf_reader = PyPDF2.PdfReader(f)
        for i, page in enumerate(pdf_reader.pages):
            print(f"\n--- Seite {i+1} ---")
            text = page.extract_text()
            if text:
                print(text)

