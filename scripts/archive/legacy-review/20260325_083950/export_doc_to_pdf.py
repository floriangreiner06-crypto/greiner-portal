#!/usr/bin/env python3
"""
Exportiert ein Markdown-Dokument als PDF (Reportlab, wie pdf_generator.py).
Verwendung:
  python scripts/export_doc_to_pdf.py docs/workstreams/werkstatt/TESTANLEITUNG_EDITH_OFFENE_AUFTRAEGE.md
  python scripts/export_doc_to_pdf.py <eingabe.md> [ausgabe.pdf]
Ohne zweites Argument: Ausgabe = gleicher Basisname mit .pdf im gleichen Ordner.
"""
import os
import sys

# Projekt-Root für Imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.doc_to_pdf import md_to_pdf


def main():
    if len(sys.argv) < 2:
        print("Verwendung: export_doc_to_pdf.py <eingabe.md> [ausgabe.pdf]", file=sys.stderr)
        sys.exit(1)

    md_path = os.path.abspath(sys.argv[1])
    if not os.path.isfile(md_path):
        print(f"Datei nicht gefunden: {md_path}", file=sys.stderr)
        sys.exit(2)

    if len(sys.argv) >= 3:
        pdf_path = os.path.abspath(sys.argv[2])
    else:
        base = os.path.splitext(md_path)[0]
        pdf_path = base + ".pdf"

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    pdf_bytes = md_to_pdf(md_text)

    os.makedirs(os.path.dirname(pdf_path) or ".", exist_ok=True)
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"PDF erstellt: {pdf_path} ({len(pdf_bytes)} Bytes)")


if __name__ == "__main__":
    main()
