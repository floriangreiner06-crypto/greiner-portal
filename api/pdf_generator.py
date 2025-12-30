"""
PDF-Generator für Reports
Greiner Portal DRIVE

Version 3.0 - Mit TEK Daily Reports (TAG132)
"""

from reportlab.lib.pagesizes import A4
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
    Generiert PDF für TEK (Tägliche Erfolgskontrolle) - V2 Modern Design
    TAG146: Redesign mit prominenten Vergleichen und modernem Layout

    Args:
        data: Dict mit Keys:
            - datum: str (z.B. "22.12.2025")
            - monat: str (z.B. "Dezember 2025")
            - gesamt: dict mit db1, marge, prognose, breakeven, breakeven_abstand
            - bereiche: list of dicts (bereich, umsatz, einsatz, db1, marge)
            - vormonat: dict mit db1, marge (optional)
            - vorjahr: dict mit db1, marge (optional)

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

    # DRIVE CI Color Palette (aus Greiner Corporate Identity)
    DRIVE_BLUE = colors.HexColor('#0066cc')    # DRIVE Primärfarbe Blau
    DRIVE_GREEN = colors.HexColor('#28a745')   # DRIVE Sekundärfarbe Grün
    WARNING = colors.HexColor('#ffc107')       # Gelb/Orange
    DANGER = colors.HexColor('#dc3545')        # Rot
    GRAY_DARK = colors.HexColor('#2c3e50')     # Dunkelgrau
    GRAY = colors.HexColor('#6c757d')          # Grau
    GRAY_LIGHT = colors.HexColor('#f8f9fa')    # Hellgrau

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
        fontSize=12,
        spaceAfter=10,
        spaceBefore=20,
        textColor=PRIMARY,
        fontName='Helvetica-Bold'
    )

    # === HEADER MIT LOGO ===
    from reportlab.platypus import Image as RLImage
    import os

    logo_path = '/opt/greiner-portal/static/images/greiner-logo.png'

    # Header-Tabelle mit Logo + Titel
    logo = None
    if os.path.exists(logo_path):
        try:
            logo = RLImage(logo_path, width=3*cm, height=0.8*cm)
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
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
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

    # Subtitle Box
    subtitle_data = [[Paragraph(
        f"<b>{data.get('monat', 'Aktueller Monat')}</b> • Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr",
        subtitle_style
    )]]
    subtitle_table = Table(subtitle_data, colWidths=[18*cm])
    subtitle_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GRAY_LIGHT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(subtitle_table)
    elements.append(Spacer(1, 15))

    # === VORMONAT / VORJAHR VERGLEICH (PROMINENT OBEN!) ===
    gesamt = data.get('gesamt', {})
    vormonat = data.get('vormonat', {})
    vorjahr = data.get('vorjahr', {})

    if vormonat or vorjahr:
        current_db1 = gesamt.get('db1', 0)
        current_marge = gesamt.get('marge', 0)

        # Vergleichs-Header
        elements.append(Paragraph("📈 Performance-Vergleich", section_style))

        vergleich_data = [['', 'DB1', 'Marge', 'Trend', 'Δ DB1']]

        # Vormonat
        if vormonat:
            vm_db1 = vormonat.get('db1', 0)
            vm_marge = vormonat.get('marge', 0)
            diff_db1_vm = current_db1 - vm_db1 if vm_db1 else 0
            diff_percent_vm = ((current_db1 / vm_db1 - 1) * 100) if vm_db1 else 0

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
                format_percent(vm_marge),
                trend_vm,
                diff_text_vm
            ])

        # Vorjahr
        if vorjahr:
            vj_db1 = vorjahr.get('db1', 0)
            vj_marge = vorjahr.get('marge', 0)
            diff_db1_vj = current_db1 - vj_db1 if vj_db1 else 0
            diff_percent_vj = ((current_db1 / vj_db1 - 1) * 100) if vj_db1 else 0

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
                '🔹 vs. Vorjahr',
                format_currency_short(vj_db1),
                format_percent(vj_marge),
                trend_vj,
                diff_text_vj
            ])

        vergleich_table = Table(vergleich_data, colWidths=[4*cm, 3.5*cm, 3*cm, 2.5*cm, 5*cm])
        vergleich_style_list = [
            ('BACKGROUND', (0, 0), (-1, 0), GRAY_DARK),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRAY_LIGHT]),
        ]

        # Trend-Farben
        row = 1
        if vormonat:
            diff_db1_vm = current_db1 - vormonat.get('db1', 0)
            trend_color_vm = SUCCESS if diff_db1_vm > 0 else (DANGER if diff_db1_vm < 0 else GRAY)
            vergleich_style_list.append(('TEXTCOLOR', (3, row), (3, row), trend_color_vm))
            vergleich_style_list.append(('FONTSIZE', (3, row), (3, row), 18))
            vergleich_style_list.append(('TEXTCOLOR', (4, row), (4, row), trend_color_vm))
            row += 1

        if vorjahr:
            diff_db1_vj = current_db1 - vorjahr.get('db1', 0)
            trend_color_vj = SUCCESS if diff_db1_vj > 0 else (DANGER if diff_db1_vj < 0 else GRAY)
            vergleich_style_list.append(('TEXTCOLOR', (3, row), (3, row), trend_color_vj))
            vergleich_style_list.append(('FONTSIZE', (3, row), (3, row), 18))
            vergleich_style_list.append(('TEXTCOLOR', (4, row), (4, row), trend_color_vj))

        vergleich_table.setStyle(TableStyle(vergleich_style_list))
        elements.append(vergleich_table)
        elements.append(Spacer(1, 20))

    # === GESAMT KPIs (MODERN CARD DESIGN) ===
    elements.append(Paragraph("💰 Aktuelle Kennzahlen", section_style))

    breakeven_abstand = gesamt.get('breakeven_abstand', 0)
    marge = gesamt.get('marge', 0)

    # Marge-Farbe
    if marge >= 15:
        marge_color = SUCCESS
    elif marge >= 10:
        marge_color = WARNING
    else:
        marge_color = DANGER

    # Card-Style KPI-Box
    kpi_data = [
        ['', 'DB1 Aktuell', 'Marge', 'Prognose', 'Breakeven'],
        [
            '💵',
            format_currency_short(gesamt.get('db1', 0)),
            format_percent(marge),
            format_currency_short(gesamt.get('prognose', 0)),
            format_currency_short(gesamt.get('breakeven', 0))
        ]
    ]

    kpi_table = Table(kpi_data, colWidths=[1.5*cm, 4.2*cm, 3.5*cm, 4.2*cm, 4.6*cm])
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
        # Marge-Farbe
        ('TEXTCOLOR', (2, 1), (2, 1), marge_color),
    ]))

    elements.append(kpi_table)
    elements.append(Spacer(1, 12))

    # Breakeven-Status-Box (mit Icon)
    if breakeven_abstand >= 0:
        be_color = SUCCESS
        be_icon = '✅'
        be_text = f"{be_icon} +{format_currency_short(breakeven_abstand)} ÜBER Breakeven"
    else:
        be_color = DANGER
        be_icon = '⚠️'
        be_text = f"{be_icon} {format_currency_short(breakeven_abstand)} UNTER Breakeven"

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

    # === BEREICHE ===
    elements.append(Paragraph("Bereiche im Detail", section_style))

    # Bereichs-Tabelle
    bereich_header = ['Bereich', 'Umsatz', 'Einsatz', 'DB1', 'Marge', 'Status']
    bereich_data = [bereich_header]

    # Benchmarks für Status
    BENCHMARKS = {
        '1-NW': {'ziel': 12, 'warnung': 8},
        '2-GW': {'ziel': 10, 'warnung': 7},
        '3-Teile': {'ziel': 32, 'warnung': 25},
        '4-Lohn': {'ziel': 50, 'warnung': 45},
        '5-Sonst': {'ziel': 10, 'warnung': 5}
    }

    BEREICH_NAMEN = {
        '1-NW': 'Neuwagen',
        '2-GW': 'Gebrauchtwagen',
        '3-Teile': 'Teile',
        '4-Lohn': 'Werkstatt',
        '5-Sonst': 'Sonstige'
    }

    for bereich in data.get('bereiche', []):
        b_key = bereich.get('bereich', '')
        b_name = BEREICH_NAMEN.get(b_key, b_key)
        b_marge = bereich.get('marge', 0)

        # Status-Symbol basierend auf Benchmark
        benchmark = BENCHMARKS.get(b_key, {'ziel': 10, 'warnung': 5})
        if b_marge >= benchmark['ziel']:
            status = '●'  # Grün
        elif b_marge >= benchmark['warnung']:
            status = '●'  # Gelb
        else:
            status = '●'  # Rot

        bereich_data.append([
            b_name,
            format_currency_short(bereich.get('umsatz', 0)),
            format_currency_short(bereich.get('einsatz', 0)),
            format_currency_short(bereich.get('db1', 0)),
            format_percent(b_marge),
            status
        ])

    col_widths_bereich = [3.5*cm, 3*cm, 3*cm, 3*cm, 2.3*cm, 2*cm]
    bereich_table = Table(bereich_data, colWidths=col_widths_bereich)

    # Basis-Style
    bereich_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]

    # Farbe für Status-Spalte pro Zeile
    for i, bereich in enumerate(data.get('bereiche', []), start=1):
        b_key = bereich.get('bereich', '')
        b_marge = bereich.get('marge', 0)
        benchmark = BENCHMARKS.get(b_key, {'ziel': 10, 'warnung': 5})

        if b_marge >= benchmark['ziel']:
            color = colors.HexColor('#28a745')  # Grün
        elif b_marge >= benchmark['warnung']:
            color = colors.HexColor('#ffc107')  # Gelb
        else:
            color = colors.HexColor('#dc3545')  # Rot

        bereich_style.append(('TEXTCOLOR', (-1, i), (-1, i), color))
        bereich_style.append(('FONTNAME', (-1, i), (-1, i), 'Helvetica-Bold'))
        bereich_style.append(('FONTSIZE', (-1, i), (-1, i), 16))

    # Modernes Design mit DRIVE-Farben
    bereich_style[0] = ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE)  # Header Blau
    for i, bereich in enumerate(data.get('bereiche', []), start=1):
        b_key = bereich.get('bereich', '')
        b_marge = bereich.get('marge', 0)
        benchmark = BENCHMARKS.get(b_key, {'ziel': 10, 'warnung': 5})

        if b_marge >= benchmark['ziel']:
            color = DRIVE_GREEN  # Grün
        elif b_marge >= benchmark['warnung']:
            color = WARNING  # Gelb
        else:
            color = DANGER  # Rot

        bereich_style.append(('TEXTCOLOR', (-1, i), (-1, i), color))
        bereich_style.append(('FONTNAME', (-1, i), (-1, i), 'Helvetica-Bold'))
        bereich_style.append(('FONTSIZE', (-1, i), (-1, i), 16))

    bereich_table.setStyle(TableStyle(bereich_style))
    elements.append(bereich_table)

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

    TAG140: Report für Filialleiter (z.B. Rolf)

    Args:
        data: TEK-Daten mit 'standort_name' (z.B. 'Deggendorf')

    Returns:
        bytes: PDF-Inhalt
    """
    standort_name = data.get('standort_name', 'Gesamt')

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
        fontSize=13,
        spaceAfter=8,
        spaceBefore=12,
        textColor=colors.HexColor('#0066cc')
    )

    # === HEADER ===
    elements.append(Paragraph(f"TEK Standort {standort_name}", title_style))
    elements.append(Paragraph(
        f"{data.get('monat', 'Aktueller Monat')}<br/>Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr",
        subtitle_style
    ))

    # === GESAMT-KPIs ===
    gesamt = data.get('gesamt', {})
    breakeven_abstand = gesamt.get('breakeven_abstand', 0)

    if breakeven_abstand >= 0:
        be_color = colors.HexColor('#28a745')
        be_text = f"+{format_currency_short(breakeven_abstand)}"
    else:
        be_color = colors.HexColor('#dc3545')
        be_text = format_currency_short(breakeven_abstand)

    marge = gesamt.get('marge', 0)
    if marge >= 15:
        marge_color = colors.HexColor('#28a745')
    elif marge >= 10:
        marge_color = colors.HexColor('#ffc107')
    else:
        marge_color = colors.HexColor('#dc3545')

    kpi_data = [
        ['DB1', 'Marge', 'Prognose', 'Breakeven-Abstand'],
        [
            format_currency_short(gesamt.get('db1', 0)),
            format_percent(marge),
            format_currency_short(gesamt.get('prognose', 0)),
            be_text
        ]
    ]

    kpi_table = Table(kpi_data, colWidths=[4.2*cm, 4.2*cm, 4.2*cm, 4.2*cm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, 1), 16),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f5f5f5')),
        ('TEXTCOLOR', (1, 1), (1, 1), marge_color),
        ('TEXTCOLOR', (3, 1), (3, 1), be_color),
    ]))
    elements.append(kpi_table)

    # === BEREICHE ===
    elements.append(Paragraph("Bereiche im Detail", section_style))

    bereich_header = ['Bereich', 'Umsatz', 'Einsatz', 'DB1', 'Marge', 'Status']
    bereich_table_data = [bereich_header]

    for bereich in data.get('bereiche', []):
        b_key = bereich.get('bereich', '')
        b_name = BEREICH_NAMEN.get(b_key, b_key)
        b_marge = bereich.get('marge', 0)

        benchmark = BENCHMARKS.get(b_key, {'ziel': 10, 'warnung': 5})
        if b_marge >= benchmark['ziel']:
            status = 'OK'
        elif b_marge >= benchmark['warnung']:
            status = '!'
        else:
            status = 'X'

        bereich_table_data.append([
            b_name,
            format_currency_short(bereich.get('umsatz', 0)),
            format_currency_short(bereich.get('einsatz', 0)),
            format_currency_short(bereich.get('db1', 0)),
            format_percent(b_marge),
            status
        ])

    col_widths = [3.5*cm, 3*cm, 3*cm, 3*cm, 2.3*cm, 2*cm]
    bereich_table = Table(bereich_table_data, colWidths=col_widths)

    bereich_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]

    # Status-Farben
    for i, bereich in enumerate(data.get('bereiche', []), start=1):
        b_key = bereich.get('bereich', '')
        b_marge = bereich.get('marge', 0)
        benchmark = BENCHMARKS.get(b_key, {'ziel': 10, 'warnung': 5})

        if b_marge >= benchmark['ziel']:
            color = colors.HexColor('#28a745')
        elif b_marge >= benchmark['warnung']:
            color = colors.HexColor('#ffc107')
        else:
            color = colors.HexColor('#dc3545')

        bereich_style.append(('TEXTCOLOR', (-1, i), (-1, i), color))
        bereich_style.append(('FONTNAME', (-1, i), (-1, i), 'Helvetica-Bold'))

    bereich_table.setStyle(TableStyle(bereich_style))
    elements.append(bereich_table)

    # === VERGLEICH ===
    vormonat = data.get('vormonat', {})
    vorjahr = data.get('vorjahr', {})

    if vormonat or vorjahr:
        elements.append(Paragraph("Vergleich", section_style))

        current_db1 = gesamt.get('db1', 0)
        vergleich_data = [['', 'DB1', 'Marge', 'Differenz']]

        if vormonat:
            vm_db1 = vormonat.get('db1', 0)
            diff = current_db1 - vm_db1
            trend = '+' if diff > 0 else ''
            vergleich_data.append([
                'vs. Vormonat',
                format_currency_short(vm_db1),
                format_percent(vormonat.get('marge', 0)),
                f"{trend}{format_currency_short(diff)}"
            ])

        if vorjahr:
            vj_db1 = vorjahr.get('db1', 0)
            diff = current_db1 - vj_db1
            trend = '+' if diff > 0 else ''
            vergleich_data.append([
                'vs. Vorjahr',
                format_currency_short(vj_db1),
                format_percent(vorjahr.get('marge', 0)),
                f"{trend}{format_currency_short(diff)}"
            ])

        vergleich_table = Table(vergleich_data, colWidths=[4*cm, 4*cm, 3*cm, 5*cm])
        vergleich_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c757d')),
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
    elements.append(Spacer(1, 20))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(
        f"TEK {standort_name} - Automatisch generiert von DRIVE",
        footer_style
    ))

    doc.build(elements)
    return buffer.getvalue()
