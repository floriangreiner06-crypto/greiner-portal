"""
PDF-Generator für Verkaufsreports
Greiner Portal DRIVE

Version 2.0 - Mit Tag UND Monat kumuliert
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
        "Greiner Portal DRIVE - Automatisch generiert",
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
        "Greiner Portal DRIVE - Automatisch generiert",
        footer_style
    ))
    
    # PDF generieren
    doc.build(elements)
    
    return buffer.getvalue()
