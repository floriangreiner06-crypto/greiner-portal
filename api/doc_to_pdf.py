"""
Dokument-Export als PDF (Markdown → PDF).
Nutzt dieselbe Reportlab-Infrastruktur wie api/pdf_generator.py und api/provision_pdf.py.
Für Testanleitungen, Workstream-Docs etc.
"""
import re
from io import BytesIO
from typing import List, Tuple, Optional


def _escape(s: str) -> str:
    """Escape für Reportlab Paragraph (XML-ähnlich)."""
    if not s:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _parse_md_table(lines: List[str], start: int) -> Tuple[List[List[str]], int]:
    """Parst eine Markdown-Tabelle ab Zeile start. Returns (rows, next_line_index)."""
    rows = []
    i = start
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped.startswith("|"):
            break
        # Separator-Zeile (|---|---|) überspringen
        if re.match(r"^\|[\s\-:]+\|", stripped):
            i += 1
            continue
        cells = [c.strip() for c in stripped.split("|") if c.strip() or stripped.count("|") > 1]
        if cells:
            rows.append(cells)
        i += 1
    return rows, i


def _parse_md(md_text: str) -> List[dict]:
    """
    Einfacher Markdown-Parser für Dokumente (Überschriften, Absätze, Tabellen).
    Returns list of blocks: {type: 'h1'|'h2'|'h3'|'p'|'table', content: ...}
    """
    lines = md_text.replace("\r\n", "\n").split("\n")
    blocks = []
    i = 0
    current_para = []

    def flush_para():
        nonlocal current_para
        if current_para:
            text = " ".join(current_para)
            if text.strip():
                blocks.append({"type": "p", "content": text})
            current_para = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("# "):
            flush_para()
            blocks.append({"type": "h1", "content": stripped[2:].strip()})
            i += 1
            continue
        if stripped.startswith("## "):
            flush_para()
            blocks.append({"type": "h2", "content": stripped[3:].strip()})
            i += 1
            continue
        if stripped.startswith("### "):
            flush_para()
            blocks.append({"type": "h3", "content": stripped[4:].strip()})
            i += 1
            continue
        if stripped.startswith("|"):
            flush_para()
            table_rows, i = _parse_md_table(lines, i)
            if table_rows:
                blocks.append({"type": "table", "content": table_rows})
            continue
        if stripped == "---" or stripped == "***":
            flush_para()
            i += 1
            continue
        if stripped:
            # Bold **text** → <b>text</b> für Reportlab
            current_para.append(re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", stripped))
        else:
            flush_para()
        i += 1

    flush_para()
    return blocks


def md_to_pdf(md_text: str, title: Optional[str] = None, subtitle: Optional[str] = None) -> bytes:
    """
    Konvertiert Markdown-Text in ein PDF (Reportlab).
    Nutzt dieselbe Bibliothek wie pdf_generator.py / provision_pdf.py.

    Args:
        md_text: Markdown-Inhalt (## Überschriften, Absätze, | Tabelle |)
        title: Optionaler PDF-Titel (oben)
        subtitle: Optionaler Untertitel (z. B. Stand/Datum)

    Returns:
        bytes: PDF-Dateiinhalt
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    except ImportError as e:
        raise RuntimeError(
            "PDF-Export benötigt 'reportlab'. Bitte installieren mit: pip install reportlab"
        ) from e

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    elements = []

    # Zusätzliche Styles
    h1_style = ParagraphStyle(
        "DocH1",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=12,
    )
    h2_style = ParagraphStyle(
        "DocH2",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=8,
    )
    h3_style = ParagraphStyle(
        "DocH3",
        parent=styles["Heading3"],
        fontSize=11,
        spaceBefore=10,
        spaceAfter=6,
    )
    p_style = ParagraphStyle(
        "DocP",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=6,
    )

    if title:
        elements.append(Paragraph(_escape(title), h1_style))
    if subtitle:
        elements.append(Paragraph(_escape(subtitle), ParagraphStyle(
            "Subtitle", parent=styles["Normal"], fontSize=9, textColor=colors.grey, spaceAfter=12
        )))

    blocks = _parse_md(md_text)
    for block in blocks:
        t = block["type"]
        c = block["content"]
        if t == "h1":
            elements.append(Paragraph(_escape(c), h1_style))
        elif t == "h2":
            elements.append(Paragraph(_escape(c), h2_style))
        elif t == "h3":
            elements.append(Paragraph(_escape(c), h3_style))
        elif t == "p":
            # Einfaches <b> erlauben (wir haben ** zu <b> konvertiert, schließen mit </b>)
            safe = _escape(c).replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
            elements.append(Paragraph(safe, p_style))
        elif t == "table":
            if not c:
                continue
            col_count = max(len(row) for row in c)
            col_width = 16 * cm / col_count if col_count else 4 * cm
            table = Table(c, colWidths=[col_width] * col_count)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            elements.append(table)
            elements.append(Spacer(1, 12))

    doc.build(elements)
    return buffer.getvalue()
