"""
AfA Verkaufsempfehlungen — PDF-Report „20 älteste Fahrzeuge“.
Nutzt reportlab wie api/provision_pdf.py. Daten aus api.afa_api._get_verkaufsempfehlungen_liste (SSOT).
"""
from datetime import date
from io import BytesIO
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER


def _fmt_eur(value) -> str:
    """Geldbetrag: 23.399,84 €"""
    if value is None:
        return "–"
    try:
        return f"{float(value):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "–"


def generate_verkaufsempfehlungen_20_pdf() -> Optional[bytes]:
    """
    Erstellt PDF „20 älteste AfA-Fahrzeuge“ (Standzeit absteigend).
    Returns: PDF-Bytes oder None bei Fehler.
    """
    from api.afa_api import _get_verkaufsempfehlungen_liste

    liste = _get_verkaufsempfehlungen_liste()
    # Nach Standzeit absteigend (längste zuerst), None/0 am Ende
    sorted_list = sorted(
        liste,
        key=lambda f: (f.get('standzeit_tage') is None, -(f.get('standzeit_tage') or 0))
    )
    top20 = sorted_list[:20]

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'AfaReportTitle', parent=styles['Heading1'], fontSize=16, alignment=TA_LEFT, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'AfaReportSubtitle', parent=styles['Normal'], fontSize=11, textColor=colors.grey, spaceAfter=12
    )
    normal_style = ParagraphStyle('AfaReportNormal', parent=styles['Normal'], fontSize=9, spaceAfter=6)

    elements.append(Paragraph("Greiner DRIVE — Verkaufsempfehlungen", title_style))
    elements.append(Paragraph(
        "VFW &amp; Mietwagen · 20 älteste Fahrzeuge nach Standzeit",
        subtitle_style
    ))
    elements.append(Paragraph(
        "<b>Rascher Umschlag und gezielte Vermarktung verbessern Ihren Liquiditätszugang und den Cashflow.</b> "
        "Jedes verkaufte Fahrzeug setzt Buchwert frei, reduziert Zinslast und schafft Spielraum für Neubeschaffung.",
        normal_style
    ))
    elements.append(Paragraph(
        "Die folgenden 20 ältesten Fahrzeuge (längste Standzeit) mit Empfehlung. "
        "Bitte priorisieren Sie die rot markierten Positionen — hier ist die Zinsenrückholung sonst gefährdet.",
        normal_style
    ))
    elements.append(Spacer(1, 0.5*cm))

    # Tabelle: #, Bezeichnung, Tage, Buchwert (€), Aufschlag (€), Empfehlung
    table_data = [['#', 'Bezeichnung', 'Tage', 'Buchwert (€)', 'Aufschlag (€)', 'Empfehlung']]
    for i, f in enumerate(top20, 1):
        bezeichnung = (f.get('fahrzeug_bezeichnung') or '-')[:50]
        tage = f.get('standzeit_tage')
        tage_str = str(tage) if tage is not None else '–'
        buch = _fmt_eur(f.get('buchwert'))
        aufschlag = _fmt_eur(f.get('aufschlag_echter_buchgewinn'))
        empfehlung = (f.get('empfehlung') or '-')[:60]
        table_data.append([str(i), bezeichnung, tage_str, buch, aufschlag, empfehlung])

    col_widths = [1.2*cm, 6*cm, 1.8*cm, 2.2*cm, 2.2*cm, 5*cm]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (4, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.8*cm))
    elements.append(Paragraph(
        f"Stand: {date.today().strftime('%d.%m.%Y')} · Quelle: DRIVE Portal AfA Verkaufsempfehlungen",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    ))

    doc.build(elements)
    return buffer.getvalue()


def generate_auktion_zeitnah_pdf(fahrzeuge: list) -> Optional[bytes]:
    """
    PDF für Auktion (Zeitnah): ausgewählte Fahrzeuge mit
    Marke (Locosoft), Typ, EZ, Km Stand, Abverkaufspreis.
    Layout wie DRIVE-Report-Standard (20 älteste / Verkaufsempfehlungen).
    """
    if not fahrzeuge:
        return None

    def _fmt_ez(val):
        if val is None:
            return "–"
        s = str(val)[:10]
        if len(s) >= 10 and s[4] == "-" and s[7] == "-":
            return f"{s[8:10]}.{s[5:7]}.{s[0:4]}"
        return s

    def _fmt_km(val):
        if val is None:
            return "–"
        try:
            return f"{int(val):,}".replace(",", ".")
        except (TypeError, ValueError):
            return "–"

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'AfaReportTitle', parent=styles['Heading1'], fontSize=16, alignment=TA_LEFT, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'AfaReportSubtitle', parent=styles['Normal'], fontSize=11, textColor=colors.grey, spaceAfter=12
    )

    elements.append(Paragraph("Greiner DRIVE — Auktion (Zeitnah)", title_style))
    elements.append(Paragraph(
        f"Verkaufsliste · {len(fahrzeuge)} Fahrzeug(e) · Mindestpreis = Buchwert + 50 % Zinsen (zzgl. MwSt.)",
        subtitle_style
    ))
    elements.append(Spacer(1, 0.5*cm))

    # A4 nutzbar ca. 18 cm → 2 Zeilen pro Fahrzeug: Datenzeile + VIN-Zeile (überspannt)
    table_data = [['Marke', 'Typ', 'EZ', 'Km Stand', 'Mindestpreis zzgl. MwSt.']]
    MWSATZ = 1.19  # 19 % MwSt.
    for f in fahrzeuge:
        marke = (f.get('marke') or '–').strip() or '–'
        typ = (f.get('fahrzeug_bezeichnung') or f.get('modell') or '–').strip()[:45] or '–'
        ez = _fmt_ez(f.get('erstzulassungsdatum'))
        km = _fmt_km(f.get('km_stand'))
        netto = f.get('abverkaufspreis_vorschlag')
        netto_str = _fmt_eur(netto)
        try:
            brutto = round(float(netto or 0) * MWSATZ, 2) if netto is not None else None
        except (TypeError, ValueError):
            brutto = None
        brutto_str = _fmt_eur(brutto)
        # Eine Zelle: zzgl. und inkl. MwSt.
        abverkauf_zelle = f"{netto_str} zzgl.\n{brutto_str} inkl. MwSt." if netto_str != "–" else "–"
        table_data.append([marke, typ, ez, km, abverkauf_zelle])
        vin = (f.get('vin') or '–').strip() or '–'
        table_data.append([f"VIN: {vin}", '', '', '', ''])

    col_widths = [2.4*cm, 7.2*cm, 2.2*cm, 2.4*cm, 3.8*cm]  # Summe 18 cm
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    style_list = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]
    # VIN-Zeilen: Zelle über alle Spalten spannen, kleinere Schrift
    for i in range(len(fahrzeuge)):
        r = 2 + i * 2  # Zeilenindex (0=Header, 1=erste Datenzeile, 2=erste VIN-Zeile, …)
        style_list.append(('SPAN', (0, r), (4, r)))
        style_list.append(('FONTSIZE', (0, r), (4, r), 7))
        style_list.append(('TEXTCOLOR', (0, r), (4, r), colors.HexColor('#555555')))
        style_list.append(('BOTTOMPADDING', (0, r), (4, r), 4))
        style_list.append(('TOPPADDING', (0, r), (4, r), 1))
    t.setStyle(TableStyle(style_list))
    elements.append(t)
    elements.append(Spacer(1, 0.8*cm))
    elements.append(Paragraph(
        f"Stand: {date.today().strftime('%d.%m.%Y')} · Quelle: DRIVE Portal AfA Verkaufsempfehlungen · Auktion Zeitnah",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    ))

    doc.build(elements)
    return buffer.getvalue()
