#!/usr/bin/env python3
"""
Konvertiert Markdown zu PDF mit weasyprint oder reportlab
"""

import sys
import os

# Markdown zu HTML
try:
    import markdown
    from markdown.extensions import codehilite, tables, fenced_code
except ImportError:
    print("Fehler: markdown Modul nicht installiert. Installiere mit: pip install markdown")
    sys.exit(1)

# HTML zu PDF
try:
    from weasyprint import HTML
    USE_WEASYPRINT = True
except ImportError:
    try:
        import pdfkit
        USE_PDFKIT = True
        USE_WEASYPRINT = False
    except ImportError:
        print("Fehler: Weder weasyprint noch pdfkit installiert.")
        print("Installiere mit: pip install weasyprint ODER pip install pdfkit")
        sys.exit(1)

def markdown_to_html(md_file):
    """Konvertiert Markdown zu HTML"""
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Markdown Extensions
    extensions = [
        'codehilite',
        'tables',
        'fenced_code',
        'toc'
    ]
    
    html_body = markdown.markdown(md_content, extensions=extensions)
    
    # Vollständiges HTML-Dokument
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 5px;
            margin-top: 30px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 20px;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding-left: 20px;
            color: #7f8c8d;
        }}
        .page-break {{
            page-break-after: always;
        }}
        @media print {{
            body {{
                max-width: 100%;
            }}
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""
    
    return html

def html_to_pdf(html_content, pdf_file):
    """Konvertiert HTML zu PDF"""
    if USE_WEASYPRINT:
        HTML(string=html_content).write_pdf(pdf_file)
    else:
        # pdfkit verwenden
        pdfkit.from_string(html_content, pdf_file)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Verwendung: python3 convert_md_to_pdf.py <markdown-datei> [pdf-datei]")
        sys.exit(1)
    
    md_file = sys.argv[1]
    if not os.path.exists(md_file):
        print(f"Fehler: Datei nicht gefunden: {md_file}")
        sys.exit(1)
    
    pdf_file = sys.argv[2] if len(sys.argv) > 2 else md_file.replace('.md', '.pdf')
    
    print(f"Konvertiere {md_file} zu {pdf_file}...")
    
    try:
        html = markdown_to_html(md_file)
        html_to_pdf(html, pdf_file)
        print(f"✓ Erfolgreich konvertiert: {pdf_file}")
    except Exception as e:
        print(f"Fehler bei der Konvertierung: {e}")
        sys.exit(1)

