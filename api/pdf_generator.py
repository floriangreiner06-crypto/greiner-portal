"""
PDF-Generator für Reports
Greiner Portal DRIVE

Version 3.0 - Mit TEK Daily Reports (TAG132)
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime


def format_currency(value):
    """Formatiert als Euro"""
    try:
        return f"{float(value):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00 €"


def generate_auftragseingang_pdf(data: dict) -> bytes:
    """
    Generiert PDF für Auftragseingang (nur ein Zeitraum)
    
    Args:
        data: Dict mit Keys: 
            - datum: str (z.B. "26.11.2025" oder "November 2025")
            - zeitraum: str ("Tag" oder "Monat")
            - summary: dict mit neu, test_vorfuehr, gebraucht, gesamt, umsatz_gesamt
            - verkaufer: list of dicts
    
    Returns:
        bytes: PDF-Inhalt
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=20
    )
    
    # Titel
    elements.append(Paragraph("Auftragseingang", title_style))
    elements.append(Paragraph(
        f"{data.get('zeitraum', 'Tag')}: {data.get('datum', 'Unbekannt')}<br/>Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr",
        subtitle_style
    ))
    
    # Zusammenfassung
    summary = data.get('summary', {})
    summary_data = [
        ['Neuwagen', 'Test/Vorführ', 'Gebrauchtwagen', 'GESAMT'],
        [
            str(summary.get('neu', 0)),
            str(summary.get('test_vorfuehr', 0)),
            str(summary.get('gebraucht', 0)),
            str(summary.get('gesamt', 0))
        ],
        [
            format_currency(summary.get('umsatz_neu', 0)),
            format_currency(summary.get('umsatz_tv', 0)),
            format_currency(summary.get('umsatz_gw', 0)),
            format_currency(summary.get('umsatz_gesamt', 0))
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[4.5*cm, 4.5*cm, 4.5*cm, 4.5*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e6f2ff')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Verkäufer-Details
    elements.append(Paragraph("Auftragseingang nach Verkäufer", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    # Verkäufer-Tabelle
    verkaufer_header = ['Verkäufer', 'NW', 'T/V', 'GW', 'Gesamt', 'Umsatz']
    verkaufer_data = [verkaufer_header]
    
    for vk in data.get('verkaufer', []):
        verkaufer_data.append([
            vk.get('verkaufer_name', 'Unbekannt'),
            str(vk.get('summe_neu', 0)),
            str(vk.get('summe_test_vorfuehr', 0)),
            str(vk.get('summe_gebraucht', 0)),
            str(vk.get('summe_gesamt', 0)),
            format_currency(vk.get('umsatz_gesamt', 0))
        ])
    
    # Summenzeile
    verkaufer_data.append([
        'GESAMT',
        str(summary.get('neu', 0)),
        str(summary.get('test_vorfuehr', 0)),
        str(summary.get('gebraucht', 0)),
        str(summary.get('gesamt', 0)),
        format_currency(summary.get('umsatz_gesamt', 0))
    ])
    
    col_widths = [6*cm, 1.8*cm, 1.8*cm, 1.8*cm, 2*cm, 3.5*cm]
    verkaufer_table = Table(verkaufer_data, colWidths=col_widths)
    verkaufer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        # Letzte Zeile (Summe) hervorheben
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        # Alternating rows
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    
    elements.append(verkaufer_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(
        "Automatisch generiert von DRIVE",
        footer_style
    ))

    # PDF generieren
    doc.build(elements)

    return buffer.getvalue()


def generate_auftragseingang_komplett_pdf(tag_data: dict, monat_data: dict, datum_display: str, monat_display: str) -> bytes:
    """
    Generiert PDF für Auftragseingang mit TAG und MONAT kumuliert
    
    Args:
        tag_data: Dict mit verkaufer list für den Tag
        monat_data: Dict mit verkaufer list für den Monat
        datum_display: z.B. "26.11.2025"
        monat_display: z.B. "November 2025"
    
    Returns:
        bytes: PDF-Inhalt
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        leftMargin=1.2*cm,
        rightMargin=1.2*cm,
        topMargin=1.2*cm,
        bottomMargin=1.2*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=5,
        textColor=colors.HexColor('#333333')
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=15
    )
    
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=15,
        textColor=colors.HexColor('#0066cc')
    )
    
    # === HEADER ===
    elements.append(Paragraph("📊 Auftragseingang", title_style))
    elements.append(Paragraph(
        f"Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr",
        subtitle_style
    ))
    
    # === ÜBERSICHT: TAG vs MONAT ===
    tag_summary = {
        'neu': sum(v.get('summe_neu', 0) for v in tag_data),
        'test_vorfuehr': sum(v.get('summe_test_vorfuehr', 0) for v in tag_data),
        'gebraucht': sum(v.get('summe_gebraucht', 0) for v in tag_data),
        'gesamt': sum(v.get('summe_gesamt', 0) for v in tag_data),
        'umsatz': sum(v.get('umsatz_gesamt', 0) for v in tag_data)
    }
    
    monat_summary = {
        'neu': sum(v.get('summe_neu', 0) for v in monat_data),
        'test_vorfuehr': sum(v.get('summe_test_vorfuehr', 0) for v in monat_data),
        'gebraucht': sum(v.get('summe_gebraucht', 0) for v in monat_data),
        'gesamt': sum(v.get('summe_gesamt', 0) for v in monat_data),
        'umsatz': sum(v.get('umsatz_gesamt', 0) for v in monat_data)
    }
    
    # Kompakte Übersichtstabelle
    overview_data = [
        ['', 'Neuwagen', 'Test/Vorführ', 'Gebraucht', 'GESAMT', 'Umsatz'],
        [
            f'📅 Heute ({datum_display})',
            str(tag_summary['neu']),
            str(tag_summary['test_vorfuehr']),
            str(tag_summary['gebraucht']),
            str(tag_summary['gesamt']),
            format_currency(tag_summary['umsatz'])
        ],
        [
            f'📆 {monat_display}',
            str(monat_summary['neu']),
            str(monat_summary['test_vorfuehr']),
            str(monat_summary['gebraucht']),
            str(monat_summary['gesamt']),
            format_currency(monat_summary['umsatz'])
        ]
    ]
    
    col_widths_overview = [4.5*cm, 2.2*cm, 2.5*cm, 2.2*cm, 2*cm, 3.5*cm]
    overview_table = Table(overview_data, colWidths=col_widths_overview)
    overview_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        # Heute-Zeile
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e6f2ff')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 1), (-2, 1), 14),
        # Monat-Zeile
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#fff3cd')),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 2), (-2, 2), 14),
        # Allgemein
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
    ]))
    
    elements.append(overview_table)
    
    # === DETAILS HEUTE ===
    elements.append(Paragraph(f"🚗 Heute ({datum_display}) - nach Verkäufer", section_style))
    
    if tag_data:
        tag_table_data = [['Verkäufer', 'NW', 'T/V', 'GW', 'Ges.', 'Umsatz']]
        for vk in sorted(tag_data, key=lambda x: x.get('summe_gesamt', 0), reverse=True):
            if vk.get('summe_gesamt', 0) > 0:
                tag_table_data.append([
                    vk.get('verkaufer_name', 'Unbekannt')[:25],
                    str(vk.get('summe_neu', 0)),
                    str(vk.get('summe_test_vorfuehr', 0)),
                    str(vk.get('summe_gebraucht', 0)),
                    str(vk.get('summe_gesamt', 0)),
                    format_currency(vk.get('umsatz_gesamt', 0))
                ])
        
        if len(tag_table_data) > 1:
            col_widths_detail = [5.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 3.2*cm]
            tag_table = Table(tag_table_data, colWidths=col_widths_detail)
            tag_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            elements.append(tag_table)
        else:
            elements.append(Paragraph("Keine Aufträge heute.", styles['Normal']))
    else:
        elements.append(Paragraph("Keine Aufträge heute.", styles['Normal']))
    
    # === DETAILS MONAT ===
    elements.append(Paragraph(f"📈 {monat_display} kumuliert - nach Verkäufer", section_style))
    
    if monat_data:
        monat_table_data = [['Verkäufer', 'NW', 'T/V', 'GW', 'Ges.', 'Umsatz']]
        for vk in sorted(monat_data, key=lambda x: x.get('summe_gesamt', 0), reverse=True):
            if vk.get('summe_gesamt', 0) > 0:
                monat_table_data.append([
                    vk.get('verkaufer_name', 'Unbekannt')[:25],
                    str(vk.get('summe_neu', 0)),
                    str(vk.get('summe_test_vorfuehr', 0)),
                    str(vk.get('summe_gebraucht', 0)),
                    str(vk.get('summe_gesamt', 0)),
                    format_currency(vk.get('umsatz_gesamt', 0))
                ])
        
        # Summenzeile
        monat_table_data.append([
            'GESAMT',
            str(monat_summary['neu']),
            str(monat_summary['test_vorfuehr']),
            str(monat_summary['gebraucht']),
            str(monat_summary['gesamt']),
            format_currency(monat_summary['umsatz'])
        ])
        
        col_widths_detail = [5.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 3.2*cm]
        monat_table = Table(monat_table_data, colWidths=col_widths_detail)
        monat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#cc8800')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f5f5')]),
            # Summenzeile
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(monat_table)

    # Footer
    elements.append(Spacer(1, 25))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(
        "Automatisch generiert von DRIVE",
        footer_style
    ))

    # PDF generieren
    doc.build(elements)

    return buffer.getvalue()


def format_percent(value):
    """Formatiert als Prozent"""
    try:
        return f"{float(value):.1f}%".replace(".", ",")
    except:
        return "0,0%"


def format_currency_short(value):
    """Formatiert als Euro (deutsches Format ohne k-Notation)"""
    try:
        v = float(value)
        # Deutsches Format: 1.500 € statt 1,5k
        return f"{v:,.0f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0 €"


def generate_tek_daily_pdf(data: dict) -> bytes:
    """
    Generiert PDF für TEK (Tägliche Erfolgskontrolle) - V3 Querformat mit detaillierter Aufschlüsselung
    TAG 215: Querformat, detaillierte Struktur wie Global Cube F.04
    
    Args:
        data: Dict mit Keys:
            - datum: str (z.B. "22.12.2025")
            - monat: str (z.B. "Dezember 2025")
            - gesamt: dict mit db1, marge, prognose, breakeven, breakeven_abstand
            - bereiche: list of dicts (bereich, umsatz, einsatz, db1, marge)
            - vormonat: dict mit db1, marge (optional)
            - vorjahr: dict mit db1, marge (optional)
            - firma, standort_api, monat_num, jahr_num: Für API-Calls

    Returns:
        bytes: PDF-Inhalt
    """
    buffer = BytesIO()
    # TAG 215: Querformat für detaillierte Darstellung
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=0.5*cm,
        rightMargin=0.5*cm,
        topMargin=0.6*cm,
        bottomMargin=0.6*cm
    )

    elements = []
    styles = getSampleStyleSheet()

    # DRIVE CI Color Palette (aus Greiner Corporate Identity)
    DRIVE_BLUE = colors.HexColor('#0066cc')    # DRIVE Primärfarbe Blau
    DRIVE_GREEN = colors.HexColor('#28a745')   # DRIVE Sekundärfarbe Grün
    WARNING = colors.HexColor('#ffc107')       # Gelb/Orange
    DANGER = colors.HexColor('#dc3545')        # Rot
    GRAY_DARK = colors.HexColor('#2c3e50')     # Dunkelgrau
    GRAY = colors.HexColor('#6c757d')          # Grau
    GRAY_LIGHT = colors.HexColor('#f8f9fa')    # Hellgrau

    # Moderne Farbpalette für elegantes Design
    MODERN_BLUE = colors.HexColor('#1e40af')   # Tiefes Blau
    MODERN_BLUE_LIGHT = colors.HexColor('#3b82f6')  # Helles Blau
    MODERN_GRAY = colors.HexColor('#64748b')   # Modernes Grau
    MODERN_GRAY_LIGHT = colors.HexColor('#f1f5f9')  # Sehr helles Grau
    MODERN_BG = colors.HexColor('#ffffff')     # Weiß
    MODERN_ACCENT = colors.HexColor('#e0e7ff') # Sanftes Blau für Highlights

    # Aliase für Kompatibilität
    PRIMARY = DRIVE_BLUE
    SUCCESS = DRIVE_GREEN

    # Custom Styles
    title_style = ParagraphStyle(
        'ModernTitle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=3,
        textColor=GRAY_DARK,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'ModernSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=GRAY,
        spaceAfter=20
    )

    section_style = ParagraphStyle(
        'ModernSection',
        parent=styles['Heading2'],
        fontSize=11,
        spaceAfter=8,
        spaceBefore=12,
        textColor=MODERN_BLUE,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )

    # === HEADER MIT LOGO ===
    from reportlab.platypus import Image as RLImage
    import os

    logo_path = '/opt/greiner-portal/static/images/greiner-logo.png'

    # Header-Tabelle mit Logo + Titel
    logo = None
    if os.path.exists(logo_path):
        try:
            # Logo mit preserveAspectRatio laden (verhindert Verzerrung)
            from reportlab.lib.utils import ImageReader
            img_reader = ImageReader(logo_path)
            img_width, img_height = img_reader.getSize()
            aspect_ratio = img_width / img_height
            
            # Maximale Breite: 3cm, Höhe proportional
            logo_width = 3*cm
            logo_height = logo_width / aspect_ratio
            logo = RLImage(logo_path, width=logo_width, height=logo_height, preserveAspectRatio=True)
        except:
            logo = None

    if logo:
        # Header mit Logo links, Titel rechts
        header_data = [[logo, Paragraph("<b>TEK - Tägliche Erfolgskontrolle</b>", title_style)]]
        header_table = Table(header_data, colWidths=[4*cm, 14*cm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DRIVE_BLUE),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (0, 0), 15),
            ('RIGHTPADDING', (1, 0), (1, 0), 15),
        ]))
    else:
        # Fallback ohne Logo
        header_data = [[Paragraph("<b>📊 TEK - Tägliche Erfolgskontrolle</b>", title_style)]]
        header_table = Table(header_data, colWidths=[18*cm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DRIVE_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))

    elements.append(header_table)
    elements.append(Spacer(1, 2))

    # Subtitle Box (bei Filiale: Standort anzeigen)
    monat_text = data.get('monat', 'Aktueller Monat')
    standort_name = (data.get('standort_name') or '').strip()
    if standort_name and standort_name.lower() != 'gesamt':
        subtitle_text = f"<b>Standort {standort_name}</b> • {monat_text} • Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr"
    else:
        subtitle_text = f"<b>{monat_text}</b> • Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr"
    subtitle_data = [[Paragraph(subtitle_text, subtitle_style)]]
    subtitle_table = Table(subtitle_data, colWidths=[18*cm])
    subtitle_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GRAY_LIGHT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(subtitle_table)
    elements.append(Spacer(1, 10))

    # === VORMONAT / VORJAHR VERGLEICH (PROMINENT OBEN!) ===
    # TAG 215: Performance-Vergleich mit HOCHGERECHNETER Prognose (nicht absolut)
    gesamt = data.get('gesamt', {})
    vormonat = data.get('vormonat', {})
    vorjahr = data.get('vorjahr', {})
    
    # Hochgerechnete Prognose für Vergleich verwenden
    prognose_db1 = gesamt.get('prognose', gesamt.get('db1', 0))

    if vormonat or vorjahr:
        # Vergleichs-Header
        elements.append(Paragraph("📈 Performance-Vergleich (Prognose vs. Abschluss)", section_style))

        vergleich_data = [['', 'DB1', 'Trend', 'Δ DB1']]

        # Vormonat
        if vormonat:
            vm_db1 = vormonat.get('db1', 0)
            diff_db1_vm = prognose_db1 - vm_db1 if vm_db1 else 0
            diff_percent_vm = ((prognose_db1 / vm_db1 - 1) * 100) if vm_db1 else 0

            if diff_db1_vm > 0:
                trend_vm = '↑'
                trend_color_vm = SUCCESS
                diff_text_vm = f"+{format_currency_short(diff_db1_vm)}"
            elif diff_db1_vm < 0:
                trend_vm = '↓'
                trend_color_vm = DANGER
                diff_text_vm = format_currency_short(diff_db1_vm)
            else:
                trend_vm = '→'
                trend_color_vm = GRAY
                diff_text_vm = "±0 €"

            vergleich_data.append([
                '🔸 vs. Vormonat',
                format_currency_short(vm_db1),
                trend_vm,
                diff_text_vm
            ])

        # Vorjahr (gleicher Monat)
        if vorjahr:
            vj_db1 = vorjahr.get('db1', 0)
            diff_db1_vj = prognose_db1 - vj_db1 if vj_db1 else 0
            diff_percent_vj = ((prognose_db1 / vj_db1 - 1) * 100) if vj_db1 else 0

            if diff_db1_vj > 0:
                trend_vj = '↑'
                trend_color_vj = SUCCESS
                diff_text_vj = f"+{format_currency_short(diff_db1_vj)}"
            elif diff_db1_vj < 0:
                trend_vj = '↓'
                trend_color_vj = DANGER
                diff_text_vj = format_currency_short(diff_db1_vj)
            else:
                trend_vj = '→'
                trend_color_vj = GRAY
                diff_text_vj = "±0 €"

            vergleich_data.append([
                '🔹 vs. Vorjahresmonat',
                format_currency_short(vj_db1),
                trend_vj,
                diff_text_vj
            ])

        vergleich_table = Table(vergleich_data, colWidths=[5*cm, 4*cm, 2.5*cm, 6.5*cm])
        vergleich_style_list = [
            ('BACKGROUND', (0, 0), (-1, 0), GRAY_DARK),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRAY_LIGHT]),
        ]

        # Trend-Farben
        row = 1
        if vormonat:
            diff_db1_vm = prognose_db1 - vormonat.get('db1', 0)
            trend_color_vm = SUCCESS if diff_db1_vm > 0 else (DANGER if diff_db1_vm < 0 else GRAY)
            vergleich_style_list.append(('TEXTCOLOR', (2, row), (2, row), trend_color_vm))
            vergleich_style_list.append(('FONTSIZE', (2, row), (2, row), 18))
            vergleich_style_list.append(('TEXTCOLOR', (3, row), (3, row), trend_color_vm))
            row += 1

        if vorjahr:
            diff_db1_vj = prognose_db1 - vorjahr.get('db1', 0)
            trend_color_vj = SUCCESS if diff_db1_vj > 0 else (DANGER if diff_db1_vj < 0 else GRAY)
            vergleich_style_list.append(('TEXTCOLOR', (2, row), (2, row), trend_color_vj))
            vergleich_style_list.append(('FONTSIZE', (2, row), (2, row), 18))
            vergleich_style_list.append(('TEXTCOLOR', (3, row), (3, row), trend_color_vj))

        vergleich_table.setStyle(TableStyle(vergleich_style_list))
        elements.append(vergleich_table)
        elements.append(Spacer(1, 10))

    # === GESAMT KPIs (MODERN CARD DESIGN) ===
    # TAG 215: Marge für Gesamtbeträge entfernt, Breakeven hochgerechnet
    elements.append(Paragraph("💰 Aktuelle Kennzahlen", section_style))

    prognose_db1 = gesamt.get('prognose', gesamt.get('db1', 0))
    breakeven_absolut = gesamt.get('breakeven', 0)
    
    # Breakeven-Abstand: Prognose vs. Breakeven (hochgerechnet, nicht absolut)
    breakeven_abstand = prognose_db1 - breakeven_absolut

    # Card-Style KPI-Box (ohne Marge für Gesamt)
    kpi_data = [
        ['', 'DB1 Aktuell', 'Prognose', 'Breakeven', 'Abstand'],
        [
            '💵',
            format_currency_short(gesamt.get('db1', 0)),
            format_currency_short(prognose_db1),
            format_currency_short(breakeven_absolut),
            format_currency_short(breakeven_abstand)
        ]
    ]

    kpi_table = Table(kpi_data, colWidths=[1.5*cm, 3.8*cm, 3.8*cm, 3.8*cm, 5.1*cm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (0, 1), 20),  # Icon größer
        ('FONTSIZE', (1, 1), (-1, 1), 18),  # Zahlen groß
        ('FONTNAME', (1, 1), (-1, 1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1.5, colors.white),
        ('BACKGROUND', (0, 1), (-1, 1), GRAY_LIGHT),
        # Abstand-Farbe
        ('TEXTCOLOR', (4, 1), (4, 1), SUCCESS if breakeven_abstand >= 0 else DANGER),
    ]))

    elements.append(kpi_table)
    elements.append(Spacer(1, 12))

    # Breakeven-Status-Box (mit Icon) - hochgerechnet
    if breakeven_abstand >= 0:
        be_color = SUCCESS
        be_icon = '✅'
        be_text = f"{be_icon} +{format_currency_short(breakeven_abstand)} ÜBER Breakeven (Prognose)"
    else:
        be_color = DANGER
        be_icon = '⚠️'
        be_text = f"{be_icon} {format_currency_short(breakeven_abstand)} UNTER Breakeven (Prognose)"

    be_status_data = [[be_text]]
    be_status_table = Table(be_status_data, colWidths=[18*cm])
    be_status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), be_color),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(be_status_table)
    elements.append(Spacer(1, 20))

    # === TAG 215: DETAILLIERTE AUFSCHLÜSSELUNG (wie Global Cube F.04) ===
    # Querformat ermöglicht detaillierte Darstellung mit Heute und Monat nebeneinander
    # Überschrift - kompakt und passend zum Design
    elements.append(Paragraph("📊 KST-Aufschlüsselung", section_style))
    
    # Helper-Funktion: Holt detaillierte Daten direkt aus PostgreSQL
    def get_tek_absatzwege_direct(bereich, firma, standort, monat, jahr, heute_datum=None):
        """Holt Absatzwege-Daten direkt aus DRIVE DB (drive_portal) - Single Source of Truth (nur für NW/GW)"""
        from api.db_connection import get_db, convert_placeholders
        import psycopg2.extras
        from datetime import datetime, date, timedelta
        import re
        
        # Nur für NW/GW
        if bereich not in ['1-NW', '2-GW']:
            return {'absatzwege': []}
        
        try:
            # Fallback für monat/jahr wenn None
            if not monat or not jahr:
                heute = date.today()
                monat = monat or heute.month
                jahr = jahr or heute.year
            
            # Datum-Strings
            von = f"{jahr}-{monat:02d}-01"
            bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"
            
            # Heute-Datum parsen
            if heute_datum:
                if isinstance(heute_datum, str):
                    if '.' in heute_datum:
                        heute_str = datetime.strptime(heute_datum, '%d.%m.%Y').strftime('%Y-%m-%d')
                    else:
                        heute_str = heute_datum
                else:
                    heute_str = heute_datum.strftime('%Y-%m-%d')
            else:
                heute_str = date.today().strftime('%Y-%m-%d')
            
            morgen_str = (datetime.strptime(heute_str, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Firma/Standort-Filter
            firma_filter = ""
            if firma == '1':
                firma_filter = "AND j.subsidiary_to_company_ref = 1"
                if standort == '1':
                    firma_filter += " AND j.branch_number = 1"
                elif standort == '2':
                    firma_filter += " AND j.branch_number = 3"
            elif firma == '2':
                firma_filter = "AND j.subsidiary_to_company_ref = 2"
            
            # Bereichs-Konten
            bereich_konten = {
                '1-NW': {'umsatz': (810000, 819999), 'einsatz': (710000, 719999)},
                '2-GW': {'umsatz': (820000, 829999), 'einsatz': (720000, 729999)}
            }
            ranges = bereich_konten[bereich]
            
            # Parse-Funktionen (vereinfacht aus controlling_routes.py)
            def parse_modell_aus_kontobezeichnung(bezeichnung: str) -> dict:
                if not bezeichnung:
                    return {'modell': 'Sonstige', 'kundentyp': '', 'verkaufsart': ''}
                bez = bezeichnung.strip()
                
                # GW-Sonderbehandlung
                gw_match = re.match(r'(?:VE |EW )?GW (?:aus |a\.)?([\w/]+)\s+(?:an\s+)?(.+)', bez)
                if gw_match:
                    herkunft_raw = gw_match.group(1)
                    rest = gw_match.group(2).strip()
                    herkunft_mapping = {'Eint': 'Eintausch', 'Zuk': 'Zukauf', 'Leasing': 'Leasing', 'Rent/VW': 'Rent/Vermitwg', 'Rent': 'Rent/Vermitwg'}
                    herkunft = herkunft_mapping.get(herkunft_raw, herkunft_raw)
                    modell = f"GW {herkunft}"
                    kundentyp = ''
                    verkaufsart = ''
                    kundentyp_patterns = [('Gewerbekd ', 'Gewerbe'), ('Gewdkd ', 'Gewerbe'), ('Gewkd ', 'Gewerbe'), ('Großkunden ', 'Großkunde'), ('Großkd ', 'Großkunde'), ('Kunden ', 'Privat'), ('KD ', 'Privat'), ('Kd ', 'Privat'), ('Händler ', 'Händler')]
                    for pattern, typ in kundentyp_patterns:
                        if rest.startswith(pattern) or f' {pattern}' in f' {rest}':
                            kundentyp = typ
                            rest = rest.replace(pattern.strip(), '').strip()
                            break
                    verkaufsart = rest.strip()
                    return {'modell': modell, 'kundentyp': kundentyp, 'verkaufsart': verkaufsart}
                
                # NW-Verarbeitung
                for prefix in ['NW VE ', 'NW EW ', 'GW VE ', 'GW EW ', 'VE ', 'EW ']:
                    if bez.startswith(prefix):
                        bez = bez[len(prefix):]
                        break
                
                kundentyp_patterns = [('Gewerbekd ', 'Gewerbe'), ('Gewdkd ', 'Gewerbe'), ('Gewkd ', 'Gewerbe'), ('Großkunden ', 'Großkunde'), ('Großkd ', 'Großkunde'), ('Kunden ', 'Privat'), ('KD ', 'Privat'), ('Kd ', 'Privat'), ('Händler ', 'Händler')]
                modell = bez
                kundentyp = ''
                verkaufsart = ''
                
                for pattern, typ in kundentyp_patterns:
                    idx = bez.find(f' {pattern.strip()}')
                    if idx == -1:
                        idx = bez.find(pattern.strip())
                    if idx != -1:
                        modell = bez[:idx].strip()
                        rest = bez[idx:].strip()
                        kundentyp = typ
                        rest = rest.replace(pattern.strip(), '').strip()
                        verkaufsart = rest
                        break
                
                return {'modell': modell, 'kundentyp': kundentyp, 'verkaufsart': verkaufsart}
            
            def normalisiere_kundentyp(kundentyp: str) -> str:
                mapping = {'Privat': 'Privat', 'Gewerbe': 'Gewerbe', 'Großkunde': 'Sonstige', 'Händler': 'Sonstige'}
                return mapping.get(kundentyp, 'Sonstige')
            
            def normalisiere_verkaufsart(verkaufsart: str) -> str:
                verkaufsart_lower = verkaufsart.lower()
                if 'leas' in verkaufsart_lower:
                    return 'Leasing'
                elif 'kauf' in verkaufsart_lower:
                    return 'Kauf'
                elif 'reg' in verkaufsart_lower or 'regulär' in verkaufsart_lower:
                    return 'reg'
                else:
                    return 'Sonstige'
            
            absatzweg_stats = {}
            
            # TAG 215: Nutze DRIVE DB (drive_portal) als Single Source of Truth
            db = get_db()
            cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # 1. Umsatz-Konten (aus DRIVE DB mit JOIN zu loco_nominal_accounts für Bezeichnungen)
            cur.execute(convert_placeholders(f"""
                SELECT
                    j.nominal_account_number as konto,
                    COALESCE(n.account_description, MIN(j.posting_text), '') as bezeichnung,
                    SUM(CASE WHEN j.debit_or_credit = 'H' THEN j.posted_value ELSE -j.posted_value END) / 100.0 as betrag,
                    COUNT(DISTINCT SUBSTRING(j.vehicle_reference FROM 'FG:([A-Z0-9]+)')) as stueck
                FROM loco_journal_accountings j
                LEFT JOIN loco_nominal_accounts n
                    ON j.nominal_account_number = n.nominal_account_number
                    AND j.subsidiary_to_company_ref = n.subsidiary_to_company_ref
                WHERE j.accounting_date >= %s AND j.accounting_date < %s
                  AND j.nominal_account_number BETWEEN %s AND %s
                  {firma_filter}
                GROUP BY j.nominal_account_number, n.account_description
            """), (von, bis, ranges['umsatz'][0], ranges['umsatz'][1]))
            
            for row in cur.fetchall():
                r = dict(row)
                konto = r.get('konto', 0)
                bezeichnung = r.get('bezeichnung', '') or ''
                betrag = float(r.get('betrag', 0) or 0)
                stueck = int(r.get('stueck', 0) or 0)
                
                parsed = parse_modell_aus_kontobezeichnung(bezeichnung)
                kundentyp = normalisiere_kundentyp(parsed['kundentyp'])
                verkaufsart = normalisiere_verkaufsart(parsed['verkaufsart'])
                absatzweg = f"{kundentyp} {verkaufsart}".strip() or 'Sonstige'
                
                if absatzweg not in absatzweg_stats:
                    absatzweg_stats[absatzweg] = {'absatzweg': absatzweg, 'stueck_monat': 0, 'umsatz_monat': 0, 'einsatz_monat': 0, 'konten': []}
                
                absatzweg_stats[absatzweg]['stueck_monat'] += stueck
                absatzweg_stats[absatzweg]['umsatz_monat'] += betrag
                absatzweg_stats[absatzweg]['konten'].append({
                    'konto': konto,
                    'bezeichnung': bezeichnung,
                    'umsatz_monat': betrag,
                    'einsatz_monat': 0,
                    'stueck_monat': stueck,
                    'umsatz_heute': 0,
                    'einsatz_heute': 0,
                    'stueck_heute': 0
                })
            
            # 2. Einsatz-Konten (aus DRIVE DB mit JOIN zu loco_nominal_accounts für Bezeichnungen)
            cur.execute(convert_placeholders(f"""
                SELECT
                    j.nominal_account_number as konto,
                    COALESCE(n.account_description, MIN(j.posting_text), '') as bezeichnung,
                    SUM(CASE WHEN j.debit_or_credit = 'S' THEN j.posted_value ELSE -j.posted_value END) / 100.0 as betrag
                FROM loco_journal_accountings j
                LEFT JOIN loco_nominal_accounts n
                    ON j.nominal_account_number = n.nominal_account_number
                    AND j.subsidiary_to_company_ref = n.subsidiary_to_company_ref
                WHERE j.accounting_date >= %s AND j.accounting_date < %s
                  AND j.nominal_account_number BETWEEN %s AND %s
                  {firma_filter}
                GROUP BY j.nominal_account_number, n.account_description
            """), (von, bis, ranges['einsatz'][0], ranges['einsatz'][1]))
            
            for row in cur.fetchall():
                r = dict(row)
                bezeichnung = r.get('bezeichnung', '') or ''
                betrag = float(r.get('betrag', 0) or 0)
                konto = r.get('konto', 0)
                
                parsed = parse_modell_aus_kontobezeichnung(bezeichnung)
                kundentyp = normalisiere_kundentyp(parsed['kundentyp'])
                verkaufsart = normalisiere_verkaufsart(parsed['verkaufsart'])
                absatzweg = f"{kundentyp} {verkaufsart}".strip() or 'Sonstige'
                
                if absatzweg not in absatzweg_stats:
                    absatzweg_stats[absatzweg] = {'absatzweg': absatzweg, 'stueck_monat': 0, 'umsatz_monat': 0, 'einsatz_monat': 0, 'konten': []}
                
                absatzweg_stats[absatzweg]['einsatz_monat'] += betrag
                
                # Konto finden und Einsatz hinzufügen
                konto_gefunden = False
                for k in absatzweg_stats[absatzweg]['konten']:
                    if k['konto'] == konto:
                        k['einsatz_monat'] += betrag
                        konto_gefunden = True
                        break
                if not konto_gefunden:
                    absatzweg_stats[absatzweg]['konten'].append({
                        'konto': konto,
                        'bezeichnung': bezeichnung,
                        'umsatz_monat': 0,
                        'einsatz_monat': betrag,
                        'stueck_monat': 0,
                        'umsatz_heute': 0,
                        'einsatz_heute': 0,
                        'stueck_heute': 0
                    })
            
            # 3. Heute-Daten (Umsatz) (aus DRIVE DB mit JOIN zu loco_nominal_accounts für Bezeichnungen)
            cur.execute(convert_placeholders(f"""
                SELECT
                    j.nominal_account_number as konto,
                    COALESCE(n.account_description, MIN(j.posting_text), '') as bezeichnung,
                    SUM(CASE WHEN j.debit_or_credit = 'H' THEN j.posted_value ELSE -j.posted_value END) / 100.0 as betrag,
                    COUNT(DISTINCT SUBSTRING(j.vehicle_reference FROM 'FG:([A-Z0-9]+)')) as stueck
                FROM loco_journal_accountings j
                LEFT JOIN loco_nominal_accounts n
                    ON j.nominal_account_number = n.nominal_account_number
                    AND j.subsidiary_to_company_ref = n.subsidiary_to_company_ref
                WHERE j.accounting_date >= %s AND j.accounting_date < %s
                  AND j.nominal_account_number BETWEEN %s AND %s
                  {firma_filter}
                GROUP BY j.nominal_account_number, n.account_description
            """), (heute_str, morgen_str, ranges['umsatz'][0], ranges['umsatz'][1]))
            
            for row in cur.fetchall():
                r = dict(row)
                konto = r.get('konto', 0)
                bezeichnung = r.get('bezeichnung', '') or ''
                betrag = float(r.get('betrag', 0) or 0)
                stueck = int(r.get('stueck', 0) or 0)
                
                parsed = parse_modell_aus_kontobezeichnung(bezeichnung)
                kundentyp = normalisiere_kundentyp(parsed['kundentyp'])
                verkaufsart = normalisiere_verkaufsart(parsed['verkaufsart'])
                absatzweg = f"{kundentyp} {verkaufsart}".strip() or 'Sonstige'
                
                if absatzweg in absatzweg_stats:
                    # Konto finden und Heute-Daten hinzufügen
                    for k in absatzweg_stats[absatzweg]['konten']:
                        if k['konto'] == konto:
                            k['umsatz_heute'] += betrag
                            k['stueck_heute'] += stueck
                            break
            
            # 4. Heute-Daten (Einsatz) (aus DRIVE DB mit JOIN zu loco_nominal_accounts für Bezeichnungen)
            cur.execute(convert_placeholders(f"""
                SELECT
                    j.nominal_account_number as konto,
                    COALESCE(n.account_description, MIN(j.posting_text), '') as bezeichnung,
                    SUM(CASE WHEN j.debit_or_credit = 'S' THEN j.posted_value ELSE -j.posted_value END) / 100.0 as betrag
                FROM loco_journal_accountings j
                LEFT JOIN loco_nominal_accounts n
                    ON j.nominal_account_number = n.nominal_account_number
                    AND j.subsidiary_to_company_ref = n.subsidiary_to_company_ref
                WHERE j.accounting_date >= %s AND j.accounting_date < %s
                  AND j.nominal_account_number BETWEEN %s AND %s
                  {firma_filter}
                GROUP BY j.nominal_account_number, n.account_description
            """), (heute_str, morgen_str, ranges['einsatz'][0], ranges['einsatz'][1]))
            
            for row in cur.fetchall():
                r = dict(row)
                konto = r.get('konto', 0)
                betrag = float(r.get('betrag', 0) or 0)
                
                # Konto in allen Absatzwegen finden
                for absatzweg_key, absatzweg_data in absatzweg_stats.items():
                    for k in absatzweg_data['konten']:
                        if k['konto'] == konto:
                            k['einsatz_heute'] += betrag
                            break
            
            # Absatzwege in Liste umwandeln
            absatzwege = []
            for a in absatzweg_stats.values():
                if a['umsatz_monat'] > 0 or a['einsatz_monat'] > 0:
                    # Heute-Summen berechnen
                    stueck_heute = sum(k['stueck_heute'] for k in a['konten'])
                    umsatz_heute = sum(k['umsatz_heute'] for k in a['konten'])
                    einsatz_heute = sum(k['einsatz_heute'] for k in a['konten'])
                    
                    absatzwege.append({
                        'absatzweg': a['absatzweg'],
                        'stueck_monat': a['stueck_monat'],
                        'umsatz_monat': round(a['umsatz_monat'], 2),
                        'einsatz_monat': round(a['einsatz_monat'], 2),
                        'db1_monat': round(a['umsatz_monat'] - a['einsatz_monat'], 2),
                        'stueck_heute': stueck_heute,
                        'umsatz_heute': round(umsatz_heute, 2),
                        'einsatz_heute': round(einsatz_heute, 2),
                        'db1_heute': round(umsatz_heute - einsatz_heute, 2),
                        'konten': a['konten']
                    })
            
            absatzwege.sort(key=lambda x: x['absatzweg'])
            
            db.close()
            return {'absatzwege': absatzwege}
        except Exception as e:
            print(f"⚠️  Fehler beim Abrufen von Absatzwege-Daten für {bereich}: {e}")
            import traceback
            traceback.print_exc()
            if 'db' in locals():
                db.close()
        return {'absatzwege': []}
    
    def get_tek_detail_data_direct(bereich, firma, standort, monat, jahr, heute_datum=None):
        """Holt detaillierte TEK-Daten direkt aus DRIVE DB (drive_portal) - Single Source of Truth (umsatz_gruppen + einsatz_gruppen)"""
        from api.db_connection import get_db, convert_placeholders
        import psycopg2.extras
        from datetime import datetime, date, timedelta
        
        try:
            # Fallback für monat/jahr wenn None
            if not monat or not jahr:
                heute = date.today()
                monat = monat or heute.month
                jahr = jahr or heute.year
            
            # Datum-Strings
            von = f"{jahr}-{monat:02d}-01"
            bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"
            
            # Heute-Datum parsen
            if heute_datum:
                if isinstance(heute_datum, str):
                    # Format: "DD.MM.YYYY" oder "YYYY-MM-DD"
                    if '.' in heute_datum:
                        heute_str = datetime.strptime(heute_datum, '%d.%m.%Y').strftime('%Y-%m-%d')
                    else:
                        heute_str = heute_datum
                else:
                    heute_str = heute_datum.strftime('%Y-%m-%d')
            else:
                heute_str = date.today().strftime('%Y-%m-%d')
            
            morgen_str = (datetime.strptime(heute_str, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Firma/Standort-Filter
            firma_filter = ""
            if firma == '1':
                firma_filter = "AND subsidiary_to_company_ref = 1"
                if standort == '1':
                    firma_filter += " AND branch_number = 1"
                elif standort == '2':
                    firma_filter += " AND branch_number = 3"
            elif firma == '2':
                firma_filter = "AND subsidiary_to_company_ref = 2"
            
            # Bereichs-Mapping
            bereich_konten = {
                '1-NW': {'umsatz': (810000, 819999), 'einsatz': (710000, 719999)},
                '2-GW': {'umsatz': (820000, 829999), 'einsatz': (720000, 729999)},
                '3-Teile': {'umsatz': (830000, 839999), 'einsatz': (730000, 739999)},
                '4-Lohn': {'umsatz': (840000, 849999), 'einsatz': (740000, 749999)},
                '5-Sonst': {'umsatz': (860000, 869999), 'einsatz': (760000, 769999)}
            }
            
            if bereich not in bereich_konten:
                return {'monat': {'umsatz_gruppen': [], 'einsatz_gruppen': []}, 'heute': {'umsatz_gruppen': [], 'einsatz_gruppen': []}}
            
            ranges = bereich_konten[bereich]
            
            # TAG 215: Nutze DRIVE DB (drive_portal) als Single Source of Truth
            db = get_db()
            
            def hole_gruppen(konto_range, vorzeichen_typ, datum_von, datum_bis):
                """Holt Gruppen-Daten für einen Zeitraum"""
                if vorzeichen_typ == 'einsatz':
                    vorzeichen = "CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END"
                else:
                    vorzeichen = "CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END"
                
                cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute(convert_placeholders(f"""
                    SELECT * FROM (
                        SELECT
                            substr(CAST(nominal_account_number AS TEXT), 1, 2) as gruppe,
                            SUM({vorzeichen}) / 100.0 as betrag
                        FROM loco_journal_accountings
                        WHERE accounting_date >= %s AND accounting_date < %s
                          AND nominal_account_number BETWEEN %s AND %s
                          {firma_filter}
                        GROUP BY substr(CAST(nominal_account_number AS TEXT), 1, 2)
                    ) sub WHERE betrag != 0
                    ORDER BY gruppe
                """), (datum_von, datum_bis, konto_range[0], konto_range[1]))
                
                gruppen = []
                for row in cur.fetchall():
                    gruppen.append({
                        'gruppe': row['gruppe'],
                        'betrag': round(float(row['betrag'] or 0), 2)
                    })
                return gruppen
            
            # Monat-Daten
            umsatz_gruppen_monat = hole_gruppen(ranges['umsatz'], 'umsatz', von, bis)
            einsatz_gruppen_monat = hole_gruppen(ranges['einsatz'], 'einsatz', von, bis)
            
            # Heute-Daten
            umsatz_gruppen_heute = hole_gruppen(ranges['umsatz'], 'umsatz', heute_str, morgen_str)
            einsatz_gruppen_heute = hole_gruppen(ranges['einsatz'], 'einsatz', heute_str, morgen_str)
            
            db.close()
            return {
                'monat': {
                    'umsatz_gruppen': umsatz_gruppen_monat,
                    'einsatz_gruppen': einsatz_gruppen_monat
                },
                'heute': {
                    'umsatz_gruppen': umsatz_gruppen_heute,
                    'einsatz_gruppen': einsatz_gruppen_heute
                }
            }
        except Exception as e:
            print(f"⚠️  Fehler beim Abrufen von Detail-Daten für {bereich}: {e}")
            import traceback
            traceback.print_exc()
            if 'db' in locals():
                db.close()
        return {'monat': {'umsatz_gruppen': [], 'einsatz_gruppen': []}, 'heute': {'umsatz_gruppen': [], 'einsatz_gruppen': []}}
    
    # KST-Mapping
    KST_MAPPING = {
        '1-NW': {'kst': '1', 'name': 'Neuwagen', 'order': 1, 'show_stueck': True},
        '2-GW': {'kst': '2', 'name': 'Gebrauchtwagen', 'order': 2, 'show_stueck': True},
        '4-Lohn': {'kst': '3', 'name': 'Service/Werkstatt', 'order': 3, 'show_stueck': False},
        '3-Teile': {'kst': '6', 'name': 'Teile & Zubehör', 'order': 4, 'show_stueck': False},
        '5-Sonst': {'kst': '7', 'name': 'Sonstige', 'order': 5, 'show_stueck': False}
    }
    
    # Bereiche nach KST-Reihenfolge sortieren
    bereiche_sorted = sorted(
        data.get('bereiche', []),
        key=lambda b: KST_MAPPING.get(b.get('bereich', ''), {}).get('order', 99)
    )
    
    # TAG 215: Detaillierte Tabelle im Querformat (wie Global Cube F.04)
    # Struktur: Bereich -> Absatzweg -> Marke (wo verfügbar)
    # Spalten: Heute (Menge, Umsatzerlöse, Einsatzwerte, DB 1 ber., DB 1 in % ber.) | Monat kumuliert (gleiche Spalten)
    # Datum parsen: "DD.MM.YYYY" -> "YYYY-MM-DD"
    datum_str = data.get('datum', '')
    if datum_str:
        try:
            # Format: "06.02.2026" -> "2026-02-06"
            heute_datum = datetime.strptime(datum_str, '%d.%m.%Y').strftime('%Y-%m-%d')
        except:
            heute_datum = datetime.now().strftime('%Y-%m-%d')
    else:
        heute_datum = datetime.now().strftime('%Y-%m-%d')
    
    # Haupttabelle mit detaillierter Struktur
    # TAG 215: Für NW/GW zusätzliche Spalte "DB/Stück" vor "DB1 %"
    # Überschriften: kurze, eindeutige Labels damit keine Überlappung mit Nachbarspalten
    detail_header = ['', '', 'Heute', '', '', '', '', '', 'Monat kumuliert', '', '', '', '', '']
    _sub_labels = ['KST', 'Bereich/Absatzweg', 'Menge', 'Umsatzerlöse', 'Einsatzwerte', 'DB 1 ber.', 'DB/Stück', 'DB1 %', 'Menge', 'Umsatzerlöse', 'Einsatzwerte', 'DB 1 ber.', 'DB/Stück', 'DB1 %']
    subheader_style = ParagraphStyle(
        'TEKSubHeader',
        parent=getSampleStyleSheet()['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        wordWrap='CJK'  # Umbruch innerhalb der Zelle
    )
    detail_subheader = [Paragraph(t, subheader_style) for t in _sub_labels]
    detail_data = [detail_header, detail_subheader]
    
    # Gesamt-Summen
    gesamt_heute_stueck = 0
    gesamt_heute_umsatz = 0
    gesamt_heute_einsatz = 0
    gesamt_heute_db1 = 0
    gesamt_monat_stueck = 0
    gesamt_monat_umsatz = 0
    gesamt_monat_einsatz = 0
    gesamt_monat_db1 = 0
    
    # Cache für Absatzweg-Daten (NW/GW), um doppelten Abruf zu vermeiden
    _aw_cache = {}
    
    # Für jeden Bereich: Detaillierte Daten holen und strukturieren
    for b in bereiche_sorted:
        bkey = b.get('bereich', '')
        cfg = KST_MAPPING.get(bkey, {'kst': '-', 'name': bkey, 'show_stueck': False})
        
        # Monat/Jahr früh ermitteln (für NW/GW Absatzweg-Summe vor Bereichs-Zeile)
        monat_num = data.get('monat_num')
        jahr_num = data.get('jahr_num')
        if not monat_num or not jahr_num:
            datum_str = data.get('datum', '')
            if datum_str:
                try:
                    datum_obj = datetime.strptime(datum_str, '%d.%m.%Y')
                    monat_num = monat_num or datum_obj.month
                    jahr_num = jahr_num or datum_obj.year
                except Exception:
                    pass
            if not monat_num or not jahr_num:
                heute = date.today()
                monat_num = monat_num or heute.month
                jahr_num = jahr_num or heute.year
        
        # Basis-Daten aus data (TAG 215: Jetzt mit allen Daten aus /api/tek wie Online-Version!)
        heute_umsatz = b.get('heute_umsatz', 0)
        heute_einsatz = b.get('heute_einsatz', 0) if 'heute_einsatz' in b else (heute_umsatz - b.get('heute_db1', 0))
        heute_db1 = b.get('heute_db1', 0)
        
        # TAG 215: Stückzahlen – für NW/GW aus Absatzweg-Summe (damit Bereichszeile und Summenzeile übereinstimmen)
        heute_stueck = b.get('heute_stueck', 0) if cfg['show_stueck'] else 0
        monat_stueck = b.get('stueck', 0) if cfg['show_stueck'] else 0
        if bkey in ['1-NW', '2-GW']:
            if bkey not in _aw_cache:
                _aw_cache[bkey] = get_tek_absatzwege_direct(
                    bkey, data.get('firma', '0'), data.get('standort_api', '0'),
                    monat_num, jahr_num, heute_datum
                )
            aw_list = _aw_cache[bkey].get('absatzwege', [])
            sum_aw_heute = sum(aw.get('stueck_heute', 0) or 0 for aw in aw_list)
            sum_aw_monat = sum(aw.get('stueck_monat', 0) or 0 for aw in aw_list)
            heute_stueck = sum_aw_heute
            monat_stueck = sum_aw_monat
        
        monat_umsatz = b.get('umsatz', 0)
        monat_einsatz = b.get('einsatz', 0)
        monat_db1 = b.get('db1', 0)
        
        # Marge berechnen
        heute_marge = (heute_db1 / heute_umsatz * 100) if heute_umsatz > 0 else 0
        monat_marge = (monat_db1 / monat_umsatz * 100) if monat_umsatz > 0 else 0
        
        # DB/Stück berechnen (nur für NW/GW)
        heute_db_pro_stueck = (heute_db1 / heute_stueck) if (cfg['show_stueck'] and heute_stueck > 0) else 0
        monat_db_pro_stueck = (monat_db1 / monat_stueck) if (cfg['show_stueck'] and monat_stueck > 0) else 0
        
        # Bereichs-Zeile (Hauptzeile) – bei NW/GW mit Stück aus Absatzweg-Summe
        detail_data.append([
            cfg['kst'],
            cfg['name'],
            str(heute_stueck) if cfg['show_stueck'] else "-",
            format_currency_short(heute_umsatz),
            format_currency_short(heute_einsatz),
            format_currency_short(heute_db1),
            format_currency_short(heute_db_pro_stueck) if cfg['show_stueck'] else "-",
            format_percent(heute_marge),
            str(monat_stueck) if cfg['show_stueck'] else "-",
            format_currency_short(monat_umsatz),
            format_currency_short(monat_einsatz),
            format_currency_short(monat_db1),
            format_currency_short(monat_db_pro_stueck) if cfg['show_stueck'] else "-",
            format_percent(monat_marge)
        ])
        
        # TAG 215: Detaillierte Aufschlüsselung - ALLE Kostenstellen-Gruppen (wie Global Cube F.04)
        detail_info = get_tek_detail_data_direct(
            bkey,
            data.get('firma', '0'),
            data.get('standort_api', '0'),
            monat_num,
            jahr_num,
            heute_datum
        )
        
        # Gruppen-Namen-Mapping
        gruppen_namen = {
            '81': 'Erlöse Neuwagen', '82': 'Erlöse Gebrauchtwagen',
            '83': 'Erlöse Teile', '84': 'Erlöse Lohn',
            '85': 'Erlöse Lack', '86': 'Sonstige Erlöse', '88': 'Erlöse Vermietung',
            '89': 'Sonstige betriebliche Erträge',
            '71': 'Einsatz Neuwagen', '72': 'Einsatz Gebrauchtwagen',
            '73': 'Einsatz Teile', '74': 'Einsatz Lohn',
            '75': 'Einsatz Lack', '76': 'Sonstiger Einsatz', '78': 'Einsatz Vermietung',
        }
        
        # TAG 215: Für NW/GW: Absatzwege mit Konten anzeigen (wie DRIVE) – nutze gecachte Daten
        if bkey in ['1-NW', '2-GW']:
            absatzwege_data = _aw_cache.get(bkey)
            if not absatzwege_data:
                absatzwege_data = get_tek_absatzwege_direct(
                    bkey,
                    data.get('firma', '0'),
                    data.get('standort_api', '0'),
                    monat_num,
                    jahr_num,
                    heute_datum
                )
                _aw_cache[bkey] = absatzwege_data
            
            absatzwege = absatzwege_data.get('absatzwege', [])
            # Stück-Summen aus den angezeigten Absatzwegen (nicht aus API-Bereich), damit Summenzeile zur Tabelle passt
            sum_stueck_heute = sum(aw.get('stueck_heute', 0) or 0 for aw in absatzwege)
            sum_stueck_monat = sum(aw.get('stueck_monat', 0) or 0 for aw in absatzwege)
            
            # Für jeden Absatzweg
            for aw in absatzwege:
                aw_stueck_heute = aw.get('stueck_heute', 0)
                aw_umsatz_heute = aw.get('umsatz_heute', 0)
                aw_einsatz_heute = aw.get('einsatz_heute', 0)
                aw_db1_heute = aw.get('db1_heute', 0)
                aw_marge_heute = (aw_db1_heute / aw_umsatz_heute * 100) if aw_umsatz_heute > 0 else 0
                
                aw_stueck_monat = aw.get('stueck_monat', 0)
                aw_umsatz_monat = aw.get('umsatz_monat', 0)
                aw_einsatz_monat = aw.get('einsatz_monat', 0)
                aw_db1_monat = aw.get('db1_monat', 0)
                aw_marge_monat = (aw_db1_monat / aw_umsatz_monat * 100) if aw_umsatz_monat > 0 else 0
                
                # DB/Stück berechnen
                aw_db_pro_stueck_heute = (aw_db1_heute / aw_stueck_heute) if aw_stueck_heute > 0 else 0
                aw_db_pro_stueck_monat = (aw_db1_monat / aw_stueck_monat) if aw_stueck_monat > 0 else 0
                
                # Absatzweg-Zeile (eingerückt)
                detail_data.append([
                    '',  # KST leer
                    f"  {aw['absatzweg']}",  # Eingerückt
                    str(aw_stueck_heute),
                    format_currency_short(aw_umsatz_heute),
                    format_currency_short(aw_einsatz_heute),
                    format_currency_short(aw_db1_heute),
                    format_currency_short(aw_db_pro_stueck_heute),
                    format_percent(aw_marge_heute),
                    str(aw_stueck_monat),
                    format_currency_short(aw_umsatz_monat),
                    format_currency_short(aw_einsatz_monat),
                    format_currency_short(aw_db1_monat),
                    format_currency_short(aw_db_pro_stueck_monat),
                    format_percent(aw_marge_monat)
                ])
                
                # Konten unter Absatzweg (doppelt eingerückt)
                konten = aw.get('konten', [])
                for konto in konten:
                    k_umsatz_heute = konto.get('umsatz_heute', 0)
                    k_einsatz_heute = konto.get('einsatz_heute', 0)
                    k_db1_heute = k_umsatz_heute - k_einsatz_heute
                    k_marge_heute = (k_db1_heute / k_umsatz_heute * 100) if k_umsatz_heute > 0 else 0
                    
                    k_umsatz_monat = konto.get('umsatz_monat', 0)
                    k_einsatz_monat = konto.get('einsatz_monat', 0)
                    k_db1_monat = k_umsatz_monat - k_einsatz_monat
                    k_marge_monat = (k_db1_monat / k_umsatz_monat * 100) if k_umsatz_monat > 0 else 0
                    
                    # DB/Stück für Konten (aus stueck_heute/stueck_monat)
                    k_stueck_heute = konto.get('stueck_heute', 0)
                    k_stueck_monat = konto.get('stueck_monat', 0)
                    k_db_pro_stueck_heute = (k_db1_heute / k_stueck_heute) if k_stueck_heute > 0 else 0
                    k_db_pro_stueck_monat = (k_db1_monat / k_stueck_monat) if k_stueck_monat > 0 else 0
                    
                    bezeichnung = konto.get('bezeichnung', f"Konto {konto.get('konto', '')}")
                    # Kürzen falls zu lang (jetzt mehr Platz durch breitere Spalte)
                    if len(bezeichnung) > 70:
                        bezeichnung = bezeichnung[:67] + "..."
                    
                    # Verwende Paragraph für Textumbruch bei langen Bezeichnungen
                    konto_text = f"    {konto.get('konto', '')}: {bezeichnung}"
                    # Einfacher Text statt Paragraph (Paragraph würde zusätzliche Formatierung benötigen)
                    detail_data.append([
                        '',  # KST leer
                        konto_text,  # Doppelt eingerückt
                        "-",  # Menge nur auf Absatzweg-Ebene
                        format_currency_short(k_umsatz_heute),
                        format_currency_short(k_einsatz_heute),
                        format_currency_short(k_db1_heute),
                        format_currency_short(k_db_pro_stueck_heute) if k_stueck_heute > 0 else "-",
                        format_percent(k_marge_heute),
                        "-",
                        format_currency_short(k_umsatz_monat),
                        format_currency_short(k_einsatz_monat),
                        format_currency_short(k_db1_monat),
                        format_currency_short(k_db_pro_stueck_monat) if k_stueck_monat > 0 else "-",
                        format_percent(k_marge_monat)
                    ])
            
            # TAG 215: Kumulationszeile für KST nach allen Absatzwegen
            # Stück = Summe der angezeigten Absatzweg-Stückzahlen (nicht API-Bereich), damit Summe zur Tabelle passt
            summe_db_pro_stueck_heute = (heute_db1 / sum_stueck_heute) if sum_stueck_heute > 0 else 0
            summe_db_pro_stueck_monat = (monat_db1 / sum_stueck_monat) if sum_stueck_monat > 0 else 0
            detail_data.append([
                cfg['kst'],  # KST wieder anzeigen
                f"Summe {cfg['name']}",  # "Summe Neuwagen"
                str(sum_stueck_heute),
                format_currency_short(heute_umsatz),
                format_currency_short(heute_einsatz),
                format_currency_short(heute_db1),
                format_currency_short(summe_db_pro_stueck_heute) if sum_stueck_heute > 0 else "-",
                format_percent(heute_marge),
                str(sum_stueck_monat),
                format_currency_short(monat_umsatz),
                format_currency_short(monat_einsatz),
                format_currency_short(monat_db1),
                format_currency_short(summe_db_pro_stueck_monat) if sum_stueck_monat > 0 else "-",
                format_percent(monat_marge)
            ])
        else:
            # Für andere Bereiche: Gruppen anzeigen (wie bisher)
            # Kombiniere Umsatz- und Einsatz-Gruppen (nach Gruppen-Nummer sortiert)
            umsatz_gruppen_monat = {g['gruppe']: g['betrag'] for g in detail_info.get('monat', {}).get('umsatz_gruppen', [])}
            einsatz_gruppen_monat = {g['gruppe']: g['betrag'] for g in detail_info.get('monat', {}).get('einsatz_gruppen', [])}
            umsatz_gruppen_heute = {g['gruppe']: g['betrag'] for g in detail_info.get('heute', {}).get('umsatz_gruppen', [])}
            einsatz_gruppen_heute = {g['gruppe']: g['betrag'] for g in detail_info.get('heute', {}).get('einsatz_gruppen', [])}
            
            # Alle Gruppen (Kombination aus Umsatz und Einsatz)
            alle_gruppen = sorted(set(list(umsatz_gruppen_monat.keys()) + list(einsatz_gruppen_monat.keys())))
            
            # Zeige jede Kostenstellen-Gruppe an
            for gruppe in alle_gruppen:
                umsatz_monat = umsatz_gruppen_monat.get(gruppe, 0)
                einsatz_monat = einsatz_gruppen_monat.get(gruppe, 0)
                db1_monat = umsatz_monat - einsatz_monat
                marge_monat = (db1_monat / umsatz_monat * 100) if umsatz_monat > 0 else 0
                
                umsatz_heute = umsatz_gruppen_heute.get(gruppe, 0)
                einsatz_heute = einsatz_gruppen_heute.get(gruppe, 0)
                db1_heute = umsatz_heute - einsatz_heute
                marge_heute = (db1_heute / umsatz_heute * 100) if umsatz_heute > 0 else 0
                
                gruppe_name = gruppen_namen.get(gruppe, f'Gruppe {gruppe}')
                
                # Gruppen-Zeile (eingerückt)
                detail_data.append([
                    '',  # KST leer
                    f"  {gruppe_name}",  # Eingerückt
                    "-",  # Menge nur bei NW/GW auf Absatzweg-Ebene
                    format_currency_short(umsatz_heute),
                    format_currency_short(einsatz_heute),
                    format_currency_short(db1_heute),
                    "-",  # DB/Stück nur für NW/GW
                    format_percent(marge_heute),
                    "-",
                    format_currency_short(umsatz_monat),
                    format_currency_short(einsatz_monat),
                    format_currency_short(db1_monat),
                    "-",  # DB/Stück nur für NW/GW
                    format_percent(marge_monat)
                ])
            
            # TAG 215: Kumulationszeile für KST nach allen Gruppen
            # Summe der KST (verwendet die Werte aus der Bereichs-Zeile)
            detail_data.append([
                cfg['kst'],  # KST wieder anzeigen
                f"Summe {cfg['name']}",  # "Summe Service/Werkstatt"
                str(heute_stueck) if cfg['show_stueck'] else "-",
                format_currency_short(heute_umsatz),
                format_currency_short(heute_einsatz),
                format_currency_short(heute_db1),
                format_currency_short(heute_db_pro_stueck) if cfg['show_stueck'] else "-",
                format_percent(heute_marge),
                str(monat_stueck) if cfg['show_stueck'] else "-",
                format_currency_short(monat_umsatz),
                format_currency_short(monat_einsatz),
                format_currency_short(monat_db1),
                format_currency_short(monat_db_pro_stueck) if cfg['show_stueck'] else "-",
                format_percent(monat_marge)
            ])
        
        # Summen für Gesamt
        gesamt_heute_stueck += heute_stueck
        gesamt_heute_umsatz += heute_umsatz
        gesamt_heute_einsatz += heute_einsatz
        gesamt_heute_db1 += heute_db1
        gesamt_monat_stueck += monat_stueck
        gesamt_monat_umsatz += monat_umsatz
        gesamt_monat_einsatz += monat_einsatz
        gesamt_monat_db1 += monat_db1
    
    # Gesamt-Marge
    gesamt_heute_marge = (gesamt_heute_db1 / gesamt_heute_umsatz * 100) if gesamt_heute_umsatz > 0 else 0
    gesamt_monat_marge = (gesamt_monat_db1 / gesamt_monat_umsatz * 100) if gesamt_monat_umsatz > 0 else 0
    
    # Gesamt-DB/Stück berechnen
    gesamt_db_pro_stueck_heute = (gesamt_heute_db1 / gesamt_heute_stueck) if gesamt_heute_stueck > 0 else 0
    gesamt_db_pro_stueck_monat = (gesamt_monat_db1 / gesamt_monat_stueck) if gesamt_monat_stueck > 0 else 0
    
    # Gesamt-Zeile
    detail_data.append([
        '', 'GESAMT',
        str(gesamt_heute_stueck),
        format_currency_short(gesamt_heute_umsatz),
        format_currency_short(gesamt_heute_einsatz),
        format_currency_short(gesamt_heute_db1),
        format_currency_short(gesamt_db_pro_stueck_heute),
        format_percent(gesamt_heute_marge),
        str(gesamt_monat_stueck),
        format_currency_short(gesamt_monat_umsatz),
        format_currency_short(gesamt_monat_einsatz),
        format_currency_short(gesamt_monat_db1),
        format_currency_short(gesamt_db_pro_stueck_monat),
        format_percent(gesamt_monat_marge)
    ])
    
    # Tabelle im Querformat erstellen (mehr Platz für Spalten)
    # Querformat: 29.7cm breit, 21cm hoch
    # Mit reduzierten Seitenrändern (0.5cm links/rechts) = 28.7cm verfügbar
    # Spaltenbreiten: DB/Stück und DB1 % etwas breiter, damit Überschriften nicht in Nachbarspalten laufen
    col_widths_detail = [0.9*cm, 4.6*cm, 1.1*cm, 2.2*cm, 2.2*cm, 2.0*cm, 1.7*cm, 1.5*cm, 1.1*cm, 2.2*cm, 2.2*cm, 2.0*cm, 1.7*cm, 1.5*cm]
    detail_table = Table(detail_data, colWidths=col_widths_detail)
    
    # Modernes, elegantes Styling für detaillierte Tabelle
    detail_style = [
        # Header-Zeile 1 (Heute, Monat kumuliert) - Moderner Gradient-Effekt
        ('SPAN', (2, 0), (7, 0)),  # Heute (6 Spalten: Menge, Umsatz, Einsatz, DB1, DB/Stück, DB%)
        ('SPAN', (8, 0), (13, 0)),  # Monat kumuliert (6 Spalten)
        ('BACKGROUND', (0, 0), (-1, 0), MODERN_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('LEFTPADDING', (0, 0), (-1, 0), 6),
        ('RIGHTPADDING', (0, 0), (-1, 0), 6),
        # Subheader-Zeile 2 (Spalten-Namen) - Elegant und subtil
        ('BACKGROUND', (0, 1), (-1, 1), MODERN_GRAY_LIGHT),
        ('TEXTCOLOR', (0, 1), (-1, 1), MODERN_GRAY),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 8),
        ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 6),
        ('TOPPADDING', (0, 1), (-1, 1), 6),
        ('LEFTPADDING', (0, 1), (-1, 1), 4),
        ('RIGHTPADDING', (0, 1), (-1, 1), 4),
        # Daten-Zeilen - Modern, luftig, ohne dicke Linien
        ('FONTSIZE', (0, 2), (-1, -2), 7),
        ('FONTNAME', (0, 2), (-1, -2), 'Helvetica'),
        ('ALIGN', (0, 2), (0, -2), 'CENTER'),  # KST
        ('ALIGN', (1, 2), (1, -2), 'LEFT'),  # Bereich/Absatzweg
        ('ALIGN', (2, 2), (-1, -2), 'RIGHT'),  # Zahlen rechts
        ('BOTTOMPADDING', (0, 2), (-1, -2), 5),
        ('TOPPADDING', (0, 2), (-1, -2), 5),
        ('LEFTPADDING', (0, 2), (-1, -2), 4),
        ('RIGHTPADDING', (0, 2), (-1, -2), 4),
        # Moderne Grid-Linien - sehr dünn und subtil
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, MODERN_BLUE),
        ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.HexColor('#e2e8f0')),
        ('LINEBELOW', (0, 2), (-1, -2), 0.3, colors.HexColor('#f1f5f9')),  # Sehr dünne Trennlinien
        # Moderne Zeilen-Hintergründe - sanfte Alternierung
        ('ROWBACKGROUNDS', (0, 2), (-1, -2), [MODERN_BG, MODERN_GRAY_LIGHT]),
        # Bereichs-Zeilen (Hauptzeilen) - Leicht hervorgehoben
        # Gesamt-Zeile - Moderner Abschluss
        ('BACKGROUND', (0, -1), (-1, -1), MODERN_BLUE),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
        ('TOPPADDING', (0, -1), (-1, -1), 8),
        ('LEFTPADDING', (0, -1), (-1, -1), 6),
        ('RIGHTPADDING', (0, -1), (-1, -1), 6),
        ('LINEABOVE', (0, -1), (-1, -1), 1, MODERN_BLUE),
    ]
    
    # TAG 215: KST-Summenzeilen stylen (alle Zeilen mit "Summe" im Bereich/Absatzweg)
    for row_idx in range(2, len(detail_data) - 1):  # Skip Header und Gesamt-Zeile
        if len(detail_data[row_idx]) > 1 and isinstance(detail_data[row_idx][1], str) and 'Summe' in detail_data[row_idx][1]:
            detail_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#e8f4f8')))  # Hellblau
            detail_style.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
            detail_style.append(('FONTSIZE', (0, row_idx), (1, row_idx), 7))  # Bereich/Absatzweg etwas größer
            detail_style.append(('BOTTOMPADDING', (0, row_idx), (-1, row_idx), 4))
            detail_style.append(('TOPPADDING', (0, row_idx), (-1, row_idx), 4))
    
    detail_table.setStyle(TableStyle(detail_style))
    elements.append(detail_table)
    elements.append(Spacer(1, 10))
    
    # Alte Bereichs-Tabelle (kompakt, optional - auskommentiert)
    # bereich_header = ['Bereich', 'Umsatz', 'Einsatz', 'DB1', 'Marge', 'Status']
    # bereich_data = [bereich_header]

    # Benchmarks für Status
    BENCHMARKS = {
        '1-NW': {'ziel': 12, 'warnung': 8},
        '2-GW': {'ziel': 10, 'warnung': 7},
        '3-Teile': {'ziel': 32, 'warnung': 25},
        '4-Lohn': {'ziel': 50, 'warnung': 45},
        '5-Sonst': {'ziel': 10, 'warnung': 5}
    }

    # Alte Bereiche-Tabelle entfernt - jetzt verwenden wir abteilungen_data (siehe oben)

    # === TAG204: DRILL-DOWNS für Verkauf (NW/GW) ===
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("🚗 Verkauf - Drill-Down", section_style))
    
    # Helper-Funktionen für Drill-Down APIs
    def get_absatzwege_drill_down(bereich, firma, standort, monat, jahr):
        """Holt Absatzwege-Daten via API /api/tek/detail"""
        import requests
        try:
            params = {
                'bereich': bereich,
                'firma': firma,
                'standort': standort,
                'monat': monat,
                'jahr': jahr,
                'ebene': 'gruppen'
            }
            response = requests.get('http://127.0.0.1:5000/api/tek/detail', params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get('absatzwege', [])
        except Exception as e:
            print(f"⚠️  Fehler beim Abrufen von Absatzwegen: {e}")
        return []
    
    def get_modelle_drill_down(bereich, firma, standort, monat, jahr):
        """Holt Modell-Daten via API /api/tek/modelle"""
        import requests
        try:
            params = {
                'bereich': bereich,
                'firma': firma,
                'standort': standort,
                'monat': monat,
                'jahr': jahr,
                'gruppierung': 'modell'
            }
            response = requests.get('http://127.0.0.1:5000/api/tek/modelle', params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get('modelle', [])
        except Exception as e:
            print(f"⚠️  Fehler beim Abrufen von Modellen: {e}")
        return []
    
    # Neuwagen Drill-Down
    nw = next((b for b in bereiche_sorted if b.get('bereich') == '1-NW'), None)
    if nw and nw.get('umsatz', 0) > 0:
        elements.append(Paragraph("📊 Neuwagen - Nach Absatzwegen (Monat kumuliert)", styles['Heading3']))
        
        absatzwege_nw = get_absatzwege_drill_down(
            bereich='1-NW',
            firma=data.get('firma', '0'),
            standort=data.get('standort_api', '0'),
            monat=data.get('monat_num'),
            jahr=data.get('jahr_num')
        )
        
        if absatzwege_nw:
            absatzwege_data = [['Absatzweg', 'Stück', 'Erlöse', 'DB1', 'DB1/Stk']]
            for aw in sorted(absatzwege_nw, key=lambda x: x.get('umsatz', 0), reverse=True):
                absatzwege_data.append([
                    aw.get('absatzweg', 'Unbekannt'),
                    str(aw.get('stueck', 0)),
                    format_currency_short(aw.get('umsatz', 0)),
                    format_currency_short(aw.get('db1', 0)),
                    format_currency_short(aw.get('db1_pro_stueck', 0))
                ])
            # Gesamt-Zeile
            absatzwege_data.append([
                'GESAMT',
                str(nw.get('stueck', 0)),
                format_currency_short(nw.get('umsatz', 0)),
                format_currency_short(nw.get('db1', 0)),
                format_currency_short(nw.get('db1_pro_stueck', 0))
            ])
            
            absatzwege_table = Table(absatzwege_data, colWidths=[5*cm, 2*cm, 3*cm, 3*cm, 3*cm])
            absatzwege_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')]),
                ('BACKGROUND', (0, -1), (-1, -1), GRAY_DARK),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(absatzwege_table)
            elements.append(Spacer(1, 15))
        
        # Modelle
        modelle_nw = get_modelle_drill_down(
            bereich='1-NW',
            firma=data.get('firma', '0'),
            standort=data.get('standort_api', '0'),
            monat=data.get('monat_num'),
            jahr=data.get('jahr_num')
        )
        
        if modelle_nw:
            elements.append(Paragraph("📊 Neuwagen - Nach Modellen (Monat kumuliert)", styles['Heading3']))
            modelle_data = [['Modell', 'Stück', 'Erlöse', 'DB1', 'DB1/Stk']]
            for m in sorted(modelle_nw, key=lambda x: x.get('umsatz', 0), reverse=True)[:10]:  # Top 10
                modelle_data.append([
                    m.get('modell', 'Unbekannt'),
                    str(m.get('stueck', 0)),
                    format_currency_short(m.get('umsatz', 0)),
                    format_currency_short(m.get('db1', 0)),
                    format_currency_short(m.get('db1_pro_stueck', 0))
                ])
            # Gesamt-Zeile
            modelle_data.append([
                'GESAMT',
                str(nw.get('stueck', 0)),
                format_currency_short(nw.get('umsatz', 0)),
                format_currency_short(nw.get('db1', 0)),
                format_currency_short(nw.get('db1_pro_stueck', 0))
            ])
            
            modelle_table = Table(modelle_data, colWidths=[5*cm, 2*cm, 3*cm, 3*cm, 3*cm])
            modelle_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')]),
                ('BACKGROUND', (0, -1), (-1, -1), GRAY_DARK),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(modelle_table)
            elements.append(Spacer(1, 20))
    
    # Gebrauchtwagen Drill-Down
    gw = next((b for b in bereiche_sorted if b.get('bereich') == '2-GW'), None)
    if gw and gw.get('umsatz', 0) > 0:
        absatzwege_gw = get_absatzwege_drill_down(
            bereich='2-GW',
            firma=data.get('firma', '0'),
            standort=data.get('standort_api', '0'),
            monat=data.get('monat_num'),
            jahr=data.get('jahr_num')
        )
        
        if absatzwege_gw:
            elements.append(Paragraph("📊 Gebrauchtwagen - Nach Absatzwegen (Monat kumuliert)", styles['Heading3']))
            absatzwege_data = [['Absatzweg', 'Stück', 'Erlöse', 'DB1', 'DB1/Stk']]
            for aw in sorted(absatzwege_gw, key=lambda x: x.get('umsatz', 0), reverse=True):
                absatzwege_data.append([
                    aw.get('absatzweg', 'Unbekannt'),
                    str(aw.get('stueck', 0)),
                    format_currency_short(aw.get('umsatz', 0)),
                    format_currency_short(aw.get('db1', 0)),
                    format_currency_short(aw.get('db1_pro_stueck', 0))
                ])
            absatzwege_data.append([
                'GESAMT',
                str(gw.get('stueck', 0)),
                format_currency_short(gw.get('umsatz', 0)),
                format_currency_short(gw.get('db1', 0)),
                format_currency_short(gw.get('db1_pro_stueck', 0))
            ])
            
            absatzwege_table = Table(absatzwege_data, colWidths=[5*cm, 2*cm, 3*cm, 3*cm, 3*cm])
            absatzwege_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')]),
                ('BACKGROUND', (0, -1), (-1, -1), GRAY_DARK),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(absatzwege_table)
            elements.append(Spacer(1, 15))
        
        modelle_gw = get_modelle_drill_down(
            bereich='2-GW',
            firma=data.get('firma', '0'),
            standort=data.get('standort_api', '0'),
            monat=data.get('monat_num'),
            jahr=data.get('jahr_num')
        )
        
        if modelle_gw:
            elements.append(Paragraph("📊 Gebrauchtwagen - Nach Modellen (Monat kumuliert)", styles['Heading3']))
            modelle_data = [['Modell', 'Stück', 'Erlöse', 'DB1', 'DB1/Stk']]
            for m in sorted(modelle_gw, key=lambda x: x.get('umsatz', 0), reverse=True)[:10]:  # Top 10
                modelle_data.append([
                    m.get('modell', 'Unbekannt'),
                    str(m.get('stueck', 0)),
                    format_currency_short(m.get('umsatz', 0)),
                    format_currency_short(m.get('db1', 0)),
                    format_currency_short(m.get('db1_pro_stueck', 0))
                ])
            modelle_data.append([
                'GESAMT',
                str(gw.get('stueck', 0)),
                format_currency_short(gw.get('umsatz', 0)),
                format_currency_short(gw.get('db1', 0)),
                format_currency_short(gw.get('db1_pro_stueck', 0))
            ])
            
            modelle_table = Table(modelle_data, colWidths=[5*cm, 2*cm, 3*cm, 3*cm, 3*cm])
            modelle_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')]),
                ('BACKGROUND', (0, -1), (-1, -1), GRAY_DARK),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(modelle_table)
            elements.append(Spacer(1, 20))

    # Footer (modern mit DRIVE Branding)
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'ModernFooter',
        parent=styles['Normal'],
        fontSize=8,
        textColor=GRAY,
        alignment=TA_CENTER
    )
    footer_data = [[Paragraph(
        "Automatisch generiert von <b>DRIVE</b> • Greiner Autohaus-Gruppe • drive.auto-greiner.de",
        footer_style
    )]]
    footer_table = Table(footer_data, colWidths=[18*cm])
    footer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GRAY_LIGHT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(footer_table)

    # PDF generieren
    doc.build(elements)

    return buffer.getvalue()


def generate_tek_bereich_pdf(data: dict, bereich_key: str) -> bytes:
    """
    Generiert kompakten PDF-Report für einen einzelnen Bereich.
    Für Abteilungsleiter (NW, GW, Teile, Werkstatt).

    TAG140: Neuer Bereichs-Report

    Args:
        data: Vollständige TEK-Daten (wie bei generate_tek_daily_pdf)
        bereich_key: z.B. '1-NW', '2-GW', '3-Teile', '4-Lohn'

    Returns:
        bytes: PDF-Inhalt
    """
    BEREICH_NAMEN = {
        '1-NW': 'Neuwagen',
        '2-GW': 'Gebrauchtwagen',
        '3-Teile': 'Teile',
        '4-Lohn': 'Werkstatt',
        '5-Sonst': 'Sonstige'
    }

    BENCHMARKS = {
        '1-NW': {'ziel': 12, 'warnung': 8},
        '2-GW': {'ziel': 10, 'warnung': 7},
        '3-Teile': {'ziel': 32, 'warnung': 25},
        '4-Lohn': {'ziel': 50, 'warnung': 45},
        '5-Sonst': {'ziel': 10, 'warnung': 5}
    }

    bereich_name = BEREICH_NAMEN.get(bereich_key, bereich_key)
    benchmark = BENCHMARKS.get(bereich_key, {'ziel': 10, 'warnung': 5})

    # Bereichs-Daten finden
    bereich_data = None
    for b in data.get('bereiche', []):
        if b.get('bereich') == bereich_key:
            bereich_data = b
            break

    if not bereich_data:
        bereich_data = {'umsatz': 0, 'einsatz': 0, 'db1': 0, 'marge': 0}

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    elements = []
    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        alignment=TA_CENTER,
        spaceAfter=5,
        textColor=colors.HexColor('#0066cc')
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=20
    )

    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        spaceBefore=15,
        textColor=colors.HexColor('#333333')
    )

    # === HEADER ===
    elements.append(Paragraph(f"TEK {bereich_name}", title_style))
    elements.append(Paragraph(
        f"{data.get('monat', 'Aktueller Monat')}<br/>Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr",
        subtitle_style
    ))

    # === HAUPT-KPIs (groß) ===
    marge = bereich_data.get('marge', 0)
    if marge >= benchmark['ziel']:
        marge_color = colors.HexColor('#28a745')
        status_text = "Ziel erreicht"
    elif marge >= benchmark['warnung']:
        marge_color = colors.HexColor('#ffc107')
        status_text = "Warnung"
    else:
        marge_color = colors.HexColor('#dc3545')
        status_text = "Unter Ziel"

    kpi_data = [
        ['DB1', 'Marge', 'Status'],
        [
            format_currency_short(bereich_data.get('db1', 0)),
            format_percent(marge),
            status_text
        ]
    ]

    kpi_table = Table(kpi_data, colWidths=[6*cm, 5*cm, 5*cm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, 1), 20),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (1, 1), (1, 1), marge_color),
        ('TEXTCOLOR', (2, 1), (2, 1), marge_color),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 15))

    # === DETAIL-ZAHLEN ===
    elements.append(Paragraph("Details", section_style))

    detail_data = [
        ['Kennzahl', 'Wert'],
        ['Umsatz', format_currency_short(bereich_data.get('umsatz', 0))],
        ['Einsatz', format_currency_short(bereich_data.get('einsatz', 0))],
        ['DB1 (Rohertrag)', format_currency_short(bereich_data.get('db1', 0))],
        ['Marge', format_percent(marge)],
        ['Ziel-Marge', f"{benchmark['ziel']}%"],
    ]

    # Stückzahlen falls vorhanden (NW/GW)
    if bereich_key in ['1-NW', '2-GW'] and bereich_data.get('stueck'):
        detail_data.append(['Stückzahlen', str(bereich_data.get('stueck', 0))])
        if bereich_data.get('db1_pro_stueck'):
            detail_data.append(['DB1/Stück', format_currency_short(bereich_data.get('db1_pro_stueck', 0))])

    detail_table = Table(detail_data, colWidths=[8*cm, 8*cm])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c757d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    elements.append(detail_table)

    # === VERGLEICH ===
    gesamt = data.get('gesamt', {})
    vormonat = data.get('vormonat', {})
    vorjahr = data.get('vorjahr', {})

    if vormonat or vorjahr:
        elements.append(Paragraph("Vergleich Gesamt-Unternehmen", section_style))

        current_db1 = gesamt.get('db1', 0)

        vergleich_data = [['Zeitraum', 'DB1 Gesamt', 'Differenz']]
        vergleich_data.append(['Aktuell', format_currency_short(current_db1), '-'])

        if vormonat:
            vm_db1 = vormonat.get('db1', 0)
            diff = current_db1 - vm_db1
            trend = '+' if diff > 0 else ''
            vergleich_data.append(['Vormonat', format_currency_short(vm_db1), f"{trend}{format_currency_short(diff)}"])

        if vorjahr:
            vj_db1 = vorjahr.get('db1', 0)
            diff = current_db1 - vj_db1
            trend = '+' if diff > 0 else ''
            vergleich_data.append(['Vorjahr', format_currency_short(vj_db1), f"{trend}{format_currency_short(diff)}"])

        vergleich_table = Table(vergleich_data, colWidths=[5*cm, 5*cm, 6*cm])
        vergleich_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#495057')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ]))
        elements.append(vergleich_table)

    # Footer
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(
        f"TEK {bereich_name} - Automatisch generiert von DRIVE",
        footer_style
    ))

    doc.build(elements)
    return buffer.getvalue()


def generate_tek_filiale_pdf(data: dict) -> bytes:
    """
    Generiert PDF für Filialleiter mit allen Bereichen eines Standorts.

    Nutzt dasselbe Layout wie TEK Tagesreport (Gesamt): Querformat, Performance-Vergleich,
    Kennzahlen, KST-Aufschlüsselung. Daten sind bereits standortgefiltert; im Subtitle
    wird „Standort {name}“ angezeigt.

    TAG140: Report für Filialleiter (z.B. Rolf)
    Anpassung: Gleiche Basis wie tek_daily (korrigierte Überschriften, einheitliches Layout).

    Args:
        data: TEK-Daten mit 'standort_name' (z.B. 'Landau'), bereits für diesen Standort gefiltert.

    Returns:
        bytes: PDF-Inhalt
    """
    return generate_tek_daily_pdf(data)


def generate_tek_verkauf_pdf(data: dict, standort_name: str = None) -> bytes:
    """
    Generiert PDF für TEK Verkauf (NW+GW kombiniert) - TAG 215
    
    Args:
        data: TEK-Daten mit bereiche (1-NW, 2-GW)
        standort_name: 'Gesamt', 'Deggendorf', 'Landau' (optional)
    
    Returns:
        bytes: PDF-Inhalt
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.2*cm,
        bottomMargin=1.2*cm
    )

    elements = []
    styles = getSampleStyleSheet()

    # DRIVE CI Color Palette
    DRIVE_BLUE = colors.HexColor('#0066cc')
    DRIVE_GREEN = colors.HexColor('#28a745')
    WARNING = colors.HexColor('#ffc107')
    DANGER = colors.HexColor('#dc3545')
    GRAY_DARK = colors.HexColor('#2c3e50')
    GRAY = colors.HexColor('#6c757d')
    GRAY_LIGHT = colors.HexColor('#f8f9fa')

    # Custom Styles
    title_style = ParagraphStyle(
        'ModernTitle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=3,
        textColor=GRAY_DARK,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'ModernSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=GRAY,
        spaceAfter=20
    )

    section_style = ParagraphStyle(
        'ModernSection',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        spaceBefore=20,
        textColor=DRIVE_BLUE,
        fontName='Helvetica-Bold'
    )

    # === HEADER ===
    standort_suffix = f" - {standort_name}" if standort_name and standort_name != 'Gesamt' else ""
    elements.append(Paragraph(f"TEK Verkauf{standort_suffix}", title_style))
    elements.append(Paragraph(
        f"{data.get('monat', 'Aktueller Monat')}<br/>Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr",
        subtitle_style
    ))
    elements.append(Spacer(1, 15))

    # === VERKAUF-DATEN AGGREGIEREN (NW + GW) ===
    nw = next((b for b in data.get('bereiche', []) if b.get('bereich') == '1-NW'), None)
    gw = next((b for b in data.get('bereiche', []) if b.get('bereich') == '2-GW'), None)
    
    verkauf_umsatz = (nw.get('umsatz', 0) if nw else 0) + (gw.get('umsatz', 0) if gw else 0)
    verkauf_einsatz = (nw.get('einsatz', 0) if nw else 0) + (gw.get('einsatz', 0) if gw else 0)
    verkauf_db1 = verkauf_umsatz - verkauf_einsatz
    verkauf_marge = (verkauf_db1 / verkauf_umsatz * 100) if verkauf_umsatz > 0 else 0
    
    verkauf_stueck = (nw.get('stueck', 0) if nw else 0) + (gw.get('stueck', 0) if gw else 0)
    verkauf_db1_stk = (verkauf_db1 / verkauf_stueck) if verkauf_stueck > 0 else 0
    
    verkauf_heute_umsatz = (nw.get('heute_umsatz', 0) if nw else 0) + (gw.get('heute_umsatz', 0) if gw else 0)
    verkauf_heute_db1 = (nw.get('heute_db1', 0) if nw else 0) + (gw.get('heute_db1', 0) if gw else 0)

    # === HAUPT-KPIs ===
    elements.append(Paragraph("Kernkennzahlen", section_style))
    
    kpi_data = [
        ['Kennzahl', 'Wert'],
        ['Erlös (Monat)', format_currency_short(verkauf_umsatz)],
        ['Einsatz (Monat)', format_currency_short(verkauf_einsatz)],
        ['DB1 (Monat)', format_currency_short(verkauf_db1)],
        ['Marge', format_percent(verkauf_marge)],
        ['Stück (Monat)', str(verkauf_stueck)],
        ['DB1/Stück', format_currency_short(verkauf_db1_stk)],
        ['Erlös (Heute)', format_currency_short(verkauf_heute_umsatz)],
        ['DB1 (Heute)', format_currency_short(verkauf_heute_db1)]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[6*cm, 10*cm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRAY_LIGHT]),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 20))

    # === DETAIL: NW vs GW ===
    elements.append(Paragraph("Bereiche im Detail", section_style))
    
    detail_data = [['Bereich', 'Erlös', 'Einsatz', 'DB1', 'Marge', 'Stück', 'DB1/Stk']]
    
    if nw:
        detail_data.append([
            'Neuwagen',
            format_currency_short(nw.get('umsatz', 0)),
            format_currency_short(nw.get('einsatz', 0)),
            format_currency_short(nw.get('db1', 0)),
            format_percent(nw.get('marge', 0)),
            str(nw.get('stueck', 0)),
            format_currency_short(nw.get('db1_pro_stueck', 0))
        ])
    
    if gw:
        detail_data.append([
            'Gebrauchtwagen',
            format_currency_short(gw.get('umsatz', 0)),
            format_currency_short(gw.get('einsatz', 0)),
            format_currency_short(gw.get('db1', 0)),
            format_percent(gw.get('marge', 0)),
            str(gw.get('stueck', 0)),
            format_currency_short(gw.get('db1_pro_stueck', 0))
        ])
    
    # Gesamt-Zeile
    detail_data.append([
        'GESAMT',
        format_currency_short(verkauf_umsatz),
        format_currency_short(verkauf_einsatz),
        format_currency_short(verkauf_db1),
        format_percent(verkauf_marge),
        str(verkauf_stueck),
        format_currency_short(verkauf_db1_stk)
    ])
    
    detail_table = Table(detail_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2*cm, 1.5*cm, 2*cm])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GRAY_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -2), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, GRAY_LIGHT]),
        ('BACKGROUND', (0, -1), (-1, -1), GRAY_DARK),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(detail_table)

    # === Verkauf Drill-Down: Absatzwege + Modellen (wie TEK Gesamt) ===
    monat_num = data.get('monat_num')
    jahr_num = data.get('jahr_num')
    if not monat_num or not jahr_num:
        try:
            monat_str = data.get('monat', '')
            if ' - ' in monat_str:
                monat_str = monat_str.split(' - ')[-1]
            datum_obj = datetime.strptime(monat_str.strip()[:7], '%Y-%m') if len(monat_str) >= 7 else None
            if datum_obj:
                monat_num = monat_num or datum_obj.month
                jahr_num = jahr_num or datum_obj.year
        except Exception:
            pass
        heute = datetime.now()
        monat_num = monat_num or heute.month
        jahr_num = jahr_num or heute.year

    def get_absatzwege_drill_down(bereich, firma, standort, monat, jahr):
        """Holt Absatzwege-Daten via API /api/tek/detail"""
        import requests
        try:
            params = {
                'bereich': bereich,
                'firma': firma,
                'standort': standort,
                'monat': monat,
                'jahr': jahr,
                'ebene': 'gruppen'
            }
            response = requests.get('http://127.0.0.1:5000/api/tek/detail', params=params, timeout=30)
            if response.status_code == 200:
                return response.json().get('absatzwege', [])
        except Exception as e:
            print(f"⚠️  Fehler beim Abrufen von Absatzwegen: {e}")
        return []

    def get_modelle_drill_down(bereich, firma, standort, monat, jahr):
        """Holt Modell-Daten via API /api/tek/modelle"""
        import requests
        try:
            params = {
                'bereich': bereich,
                'firma': firma,
                'standort': standort,
                'monat': monat,
                'jahr': jahr,
                'gruppierung': 'modell'
            }
            response = requests.get('http://127.0.0.1:5000/api/tek/modelle', params=params, timeout=30)
            if response.status_code == 200:
                return response.json().get('modelle', [])
        except Exception as e:
            print(f"⚠️  Fehler beim Abrufen von Modellen: {e}")
        return []

    firma_api = data.get('firma', '0')
    standort_api = data.get('standort_api', '0')
    heading3_style = ParagraphStyle(
        'Heading3Verkauf',
        parent=styles['Heading3'],
        fontSize=11,
        spaceAfter=8,
        spaceBefore=12,
        textColor=DRIVE_BLUE,
        fontName='Helvetica-Bold'
    )

    elements.append(Spacer(1, 25))
    elements.append(Paragraph("Verkauf – Nach Absatzwegen und Modellen", section_style))

    if nw and nw.get('umsatz', 0) > 0:
        absatzwege_nw = get_absatzwege_drill_down('1-NW', firma_api, standort_api, monat_num, jahr_num)
        if absatzwege_nw:
            elements.append(Paragraph("Neuwagen – Nach Absatzwegen (Monat kumuliert)", heading3_style))
            aw_data = [['Absatzweg', 'Stück', 'Erlöse', 'DB1', 'DB1/Stk']]
            for aw in sorted(absatzwege_nw, key=lambda x: x.get('umsatz', 0), reverse=True):
                aw_data.append([
                    aw.get('absatzweg', 'Unbekannt'),
                    str(aw.get('stueck', 0)),
                    format_currency_short(aw.get('umsatz', 0)),
                    format_currency_short(aw.get('db1', 0)),
                    format_currency_short(aw.get('db1_pro_stueck', 0))
                ])
            aw_data.append([
                'GESAMT',
                str(nw.get('stueck', 0)),
                format_currency_short(nw.get('umsatz', 0)),
                format_currency_short(nw.get('db1', 0)),
                format_currency_short(nw.get('db1_pro_stueck', 0))
            ])
            aw_table = Table(aw_data, colWidths=[5*cm, 2*cm, 3*cm, 3*cm, 3*cm])
            aw_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, GRAY_LIGHT]),
                ('BACKGROUND', (0, -1), (-1, -1), GRAY_DARK),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(aw_table)
            elements.append(Spacer(1, 12))

        modelle_nw = get_modelle_drill_down('1-NW', firma_api, standort_api, monat_num, jahr_num)
        if modelle_nw:
            elements.append(Paragraph("Neuwagen – Nach Modellen (Monat kumuliert, Top 10)", heading3_style))
            mod_data = [['Modell', 'Stück', 'Erlöse', 'DB1', 'DB1/Stk']]
            for m in sorted(modelle_nw, key=lambda x: x.get('umsatz', 0), reverse=True)[:10]:
                mod_data.append([
                    m.get('modell', 'Unbekannt'),
                    str(m.get('stueck', 0)),
                    format_currency_short(m.get('umsatz', 0)),
                    format_currency_short(m.get('db1', 0)),
                    format_currency_short(m.get('db1_pro_stueck', 0))
                ])
            mod_data.append([
                'GESAMT',
                str(nw.get('stueck', 0)),
                format_currency_short(nw.get('umsatz', 0)),
                format_currency_short(nw.get('db1', 0)),
                format_currency_short(nw.get('db1_pro_stueck', 0))
            ])
            mod_table = Table(mod_data, colWidths=[5*cm, 2*cm, 3*cm, 3*cm, 3*cm])
            mod_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, GRAY_LIGHT]),
                ('BACKGROUND', (0, -1), (-1, -1), GRAY_DARK),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(mod_table)
            elements.append(Spacer(1, 18))

    if gw and gw.get('umsatz', 0) > 0:
        absatzwege_gw = get_absatzwege_drill_down('2-GW', firma_api, standort_api, monat_num, jahr_num)
        if absatzwege_gw:
            elements.append(Paragraph("Gebrauchtwagen – Nach Absatzwegen (Monat kumuliert)", heading3_style))
            aw_data = [['Absatzweg', 'Stück', 'Erlöse', 'DB1', 'DB1/Stk']]
            for aw in sorted(absatzwege_gw, key=lambda x: x.get('umsatz', 0), reverse=True):
                aw_data.append([
                    aw.get('absatzweg', 'Unbekannt'),
                    str(aw.get('stueck', 0)),
                    format_currency_short(aw.get('umsatz', 0)),
                    format_currency_short(aw.get('db1', 0)),
                    format_currency_short(aw.get('db1_pro_stueck', 0))
                ])
            aw_data.append([
                'GESAMT',
                str(gw.get('stueck', 0)),
                format_currency_short(gw.get('umsatz', 0)),
                format_currency_short(gw.get('db1', 0)),
                format_currency_short(gw.get('db1_pro_stueck', 0))
            ])
            aw_table = Table(aw_data, colWidths=[5*cm, 2*cm, 3*cm, 3*cm, 3*cm])
            aw_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, GRAY_LIGHT]),
                ('BACKGROUND', (0, -1), (-1, -1), GRAY_DARK),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(aw_table)
            elements.append(Spacer(1, 12))

        modelle_gw = get_modelle_drill_down('2-GW', firma_api, standort_api, monat_num, jahr_num)
        if modelle_gw:
            elements.append(Paragraph("Gebrauchtwagen – Nach Modellen (Monat kumuliert, Top 10)", heading3_style))
            mod_data = [['Modell', 'Stück', 'Erlöse', 'DB1', 'DB1/Stk']]
            for m in sorted(modelle_gw, key=lambda x: x.get('umsatz', 0), reverse=True)[:10]:
                mod_data.append([
                    m.get('modell', 'Unbekannt'),
                    str(m.get('stueck', 0)),
                    format_currency_short(m.get('umsatz', 0)),
                    format_currency_short(m.get('db1', 0)),
                    format_currency_short(m.get('db1_pro_stueck', 0))
                ])
            mod_data.append([
                'GESAMT',
                str(gw.get('stueck', 0)),
                format_currency_short(gw.get('umsatz', 0)),
                format_currency_short(gw.get('db1', 0)),
                format_currency_short(gw.get('db1_pro_stueck', 0))
            ])
            mod_table = Table(mod_data, colWidths=[5*cm, 2*cm, 3*cm, 3*cm, 3*cm])
            mod_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, GRAY_LIGHT]),
                ('BACKGROUND', (0, -1), (-1, -1), GRAY_DARK),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(mod_table)
            elements.append(Spacer(1, 18))

    # Footer
    elements.append(Spacer(1, 20))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(
        f"TEK Verkauf{standort_suffix} - Automatisch generiert von DRIVE",
        footer_style
    ))

    doc.build(elements)
    return buffer.getvalue()


def generate_tek_service_pdf(data: dict, standort_name: str = None) -> bytes:
    """
    Generiert PDF für TEK Service (Teile+Werkstatt kombiniert) - TAG 215
    
    Args:
        data: TEK-Daten mit bereiche (3-Teile, 4-Lohn)
        standort_name: 'Gesamt', 'Deggendorf', 'Landau' (optional)
    
    Returns:
        bytes: PDF-Inhalt
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.2*cm,
        bottomMargin=1.2*cm
    )

    elements = []
    styles = getSampleStyleSheet()

    # DRIVE CI Color Palette
    DRIVE_BLUE = colors.HexColor('#0066cc')
    DRIVE_GREEN = colors.HexColor('#28a745')
    WARNING = colors.HexColor('#ffc107')
    DANGER = colors.HexColor('#dc3545')
    GRAY_DARK = colors.HexColor('#2c3e50')
    GRAY = colors.HexColor('#6c757d')
    GRAY_LIGHT = colors.HexColor('#f8f9fa')

    # Custom Styles
    title_style = ParagraphStyle(
        'ModernTitle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=3,
        textColor=GRAY_DARK,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'ModernSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=GRAY,
        spaceAfter=20
    )

    section_style = ParagraphStyle(
        'ModernSection',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        spaceBefore=20,
        textColor=DRIVE_BLUE,
        fontName='Helvetica-Bold'
    )

    # === HEADER ===
    standort_suffix = f" - {standort_name}" if standort_name and standort_name != 'Gesamt' else ""
    elements.append(Paragraph(f"TEK Service{standort_suffix}", title_style))
    elements.append(Paragraph(
        f"{data.get('monat', 'Aktueller Monat')}<br/>Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr",
        subtitle_style
    ))
    elements.append(Spacer(1, 15))

    # === SERVICE-DATEN AGGREGIEREN (Teile + Werkstatt) ===
    teile = next((b for b in data.get('bereiche', []) if b.get('bereich') == '3-Teile'), None)
    werkstatt = next((b for b in data.get('bereiche', []) if b.get('bereich') == '4-Lohn'), None)
    
    service_umsatz = (teile.get('umsatz', 0) if teile else 0) + (werkstatt.get('umsatz', 0) if werkstatt else 0)
    service_einsatz = (teile.get('einsatz', 0) if teile else 0) + (werkstatt.get('einsatz', 0) if werkstatt else 0)
    service_db1 = service_umsatz - service_einsatz
    service_marge = (service_db1 / service_umsatz * 100) if service_umsatz > 0 else 0
    
    service_heute_umsatz = (teile.get('heute_umsatz', 0) if teile else 0) + (werkstatt.get('heute_umsatz', 0) if werkstatt else 0)
    service_heute_db1 = (teile.get('heute_db1', 0) if teile else 0) + (werkstatt.get('heute_db1', 0) if werkstatt else 0)

    # === HAUPT-KPIs ===
    elements.append(Paragraph("Kernkennzahlen", section_style))
    
    kpi_data = [
        ['Kennzahl', 'Wert'],
        ['Erlös (Monat)', format_currency_short(service_umsatz)],
        ['Einsatz (Monat)', format_currency_short(service_einsatz)],
        ['DB1 (Monat)', format_currency_short(service_db1)],
        ['Marge', format_percent(service_marge)],
        ['Erlös (Heute)', format_currency_short(service_heute_umsatz)],
        ['DB1 (Heute)', format_currency_short(service_heute_db1)]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[6*cm, 10*cm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRAY_LIGHT]),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 20))

    # === DETAIL: Teile vs Werkstatt ===
    elements.append(Paragraph("Bereiche im Detail", section_style))
    
    detail_data = [['Bereich', 'Erlös', 'Einsatz', 'DB1', 'Marge']]
    
    if teile:
        detail_data.append([
            'Teile & Zubehör',
            format_currency_short(teile.get('umsatz', 0)),
            format_currency_short(teile.get('einsatz', 0)),
            format_currency_short(teile.get('db1', 0)),
            format_percent(teile.get('marge', 0))
        ])
    
    if werkstatt:
        detail_data.append([
            'Werkstatt',
            format_currency_short(werkstatt.get('umsatz', 0)),
            format_currency_short(werkstatt.get('einsatz', 0)),
            format_currency_short(werkstatt.get('db1', 0)),
            format_percent(werkstatt.get('marge', 0))
        ])
    
    # Gesamt-Zeile
    detail_data.append([
        'GESAMT',
        format_currency_short(service_umsatz),
        format_currency_short(service_einsatz),
        format_currency_short(service_db1),
        format_percent(service_marge)
    ])
    
    detail_table = Table(detail_data, colWidths=[4*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GRAY_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -2), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, GRAY_LIGHT]),
        ('BACKGROUND', (0, -1), (-1, -1), GRAY_DARK),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(detail_table)

    # Footer
    elements.append(Spacer(1, 20))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(
        f"TEK Service{standort_suffix} - Automatisch generiert von DRIVE",
        footer_style
    ))

    doc.build(elements)
    return buffer.getvalue()
