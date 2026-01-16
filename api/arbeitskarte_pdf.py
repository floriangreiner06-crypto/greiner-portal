"""
Arbeitskarte PDF-Generator
==========================
TAG 173: Generiert PDF der Arbeitskarte (Rückseite des Werkstattauftrages)
"""

# Importiere reportlab (sollte verfügbar sein, da pdf_generator.py es verwendet)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY

from io import BytesIO
from datetime import datetime


def format_date(dt):
    """Formatiert Datum als DD.MM.YYYY"""
    if not dt:
        return ""
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt[:10], "%Y-%m-%d")
        except:
            return dt
    return dt.strftime("%d.%m.%Y")


def format_datetime(dt_str):
    """Formatiert DateTime-String als DD.MM.YYYY HH:MM"""
    if not dt_str:
        return ""
    try:
        dt = datetime.strptime(dt_str[:16], "%Y-%m-%d %H:%M")
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return dt_str


def generate_arbeitskarte_pdf(data: dict) -> bytes:
    """
    Generiert PDF der Arbeitskarte für Garantieauftrag
    
    Args:
        data: Dict mit Keys:
            - order_number: int
            - locosoft: dict mit auftrag, kunde, fahrzeug, positionen, stempelzeiten, teile
            - gudat: dict mit tasks (Anmerkungen)
    
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
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#0066cc')
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        spaceBefore=10,
        textColor=colors.HexColor('#333333')
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_LEFT
    )
    
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#666666')
    )
    
    # ========================================================================
    # VORDERSEITE: Werkstattauftrag
    # ========================================================================
    
    elements.append(Paragraph("Werkstattauftrag", title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    auftrag = data.get('locosoft', {}).get('auftrag', {})
    kunde = data.get('locosoft', {}).get('kunde', {})
    fahrzeug = data.get('locosoft', {}).get('fahrzeug', {})
    
    # TAG 192: None-Checks für Paragraph (verhindert 'NoneType' object has no attribute 'split')
    def safe_paragraph(text, style):
        """Erstellt Paragraph nur wenn text nicht None ist"""
        if text is None:
            return ''
        return Paragraph(str(text), style)
    
    # Kopf-Daten
    # TAG 189: Verwende Paragraph für lange Texte (automatische Umbrüche)
    kopf_data = [
        ['Auftragsnummer:', str(auftrag.get('nummer', '')), 'Auftragseröffnungsdatum:', format_date(auftrag.get('datum'))],
        ['Kunde:', safe_paragraph(kunde.get('name'), normal_style), 'Telefon:', kunde.get('telefon', '') or ''],
        ['Adresse:', safe_paragraph(kunde.get('adresse'), normal_style), 'E-Mail:', safe_paragraph(kunde.get('email'), normal_style)],
        ['Kennzeichen:', fahrzeug.get('kennzeichen', '') or '', 'VIN:', fahrzeug.get('vin', '') or ''],
        ['Fahrzeugtyp:', safe_paragraph(fahrzeug.get('marke_modell'), normal_style), 'Erstzulassung:', format_date(fahrzeug.get('erstzulassung'))],
        ['Kilometerstand:', f"{fahrzeug.get('kilometerstand', 0):,} km" if fahrzeug.get('kilometerstand') else '', 
         'Serviceberater:', safe_paragraph(auftrag.get('serviceberater'), normal_style)],
    ]
    
    # Job-Beschreibung hinzufügen, falls vorhanden
    job_beschreibung = auftrag.get('job_beschreibung')
    if job_beschreibung:
        # Job-Beschreibung über volle Breite (4 Spalten) - mit Paragraph für Umbrüche
        kopf_data.append(['Job-Beschreibung:', safe_paragraph(job_beschreibung, normal_style), '', ''])
    
    kopf_table = Table(kopf_data, colWidths=[4*cm, 6*cm, 4*cm, 3*cm])
    # Style für Kopf-Tabelle
    style_list = [
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#666666')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    
    # Job-Beschreibung über volle Breite (falls vorhanden)
    if job_beschreibung:
        job_row_idx = len(kopf_data) - 1
        style_list.append(('SPAN', (1, job_row_idx), (3, job_row_idx)))  # Job-Beschreibung über Spalten 1-3
    
    kopf_table.setStyle(TableStyle(style_list))
    
    elements.append(kopf_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Arbeitspositionen
    positionen = data.get('locosoft', {}).get('positionen', [])
    if positionen:
        elements.append(Paragraph("Arbeitspositionen", heading_style))
        
        pos_data = [['Pos.', 'Arbeitsnummer', 'Beschreibung', 'AW', 'Mechaniker']]
        for pos in positionen:
            text_line = pos.get('text_line', '') or ''
            # TAG 192: None-Check für Paragraph (verhindert 'NoneType' object has no attribute 'split')
            text_para = safe_paragraph(text_line, normal_style) if text_line else ''
            
            pos_data.append([
                str(pos.get('position', '')),
                pos.get('operation', '') or '',
                text_para,
                f"{pos.get('aw', 0):.1f}" if pos.get('aw') else '0.0',
                pos.get('mechaniker', '') or ''
            ])
        
        pos_table = Table(pos_data, colWidths=[1*cm, 2.5*cm, 8*cm, 1.5*cm, 3*cm])
        pos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        
        elements.append(pos_table)
        elements.append(Spacer(1, 0.5*cm))
    
    # Seitenumbruch
    elements.append(PageBreak())
    
    # ========================================================================
    # RÜCKSEITE: ARBEITSKARTE
    # ========================================================================
    
    elements.append(Paragraph("ARBEITSKARTE", title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Diagnose durch Arbeitsausführenden (aus GUDAT)
    gudat = data.get('gudat')
    gudat_tasks = gudat.get('tasks', []) if gudat else []
    if gudat_tasks:
        elements.append(Paragraph("Diagnose durch Arbeitsausführenden", heading_style))
        
        for task in gudat_tasks:
            desc = task.get('description', '') or ''
            if desc:
                # Ersetze Zeilenumbrüche
                desc_lines = desc.split('\n')
                for line in desc_lines:
                    if line.strip():
                        elements.append(Paragraph(line.strip(), normal_style))
                elements.append(Spacer(1, 0.3*cm))
    
    # Reparaturmaßnahme
    if positionen:
        elements.append(Paragraph("Reparaturmaßnahme", heading_style))
        
        for pos in positionen:
            text_line = pos.get('text_line', '') or ''
            operation = pos.get('operation', '') or ''
            if text_line and operation:
                elements.append(Paragraph(
                    f"<b>{operation}</b>: {text_line}",
                    normal_style
                ))
                elements.append(Spacer(1, 0.2*cm))
    
    # Verwendete Teile
    teile = data.get('locosoft', {}).get('teile', [])
    if teile:
        # TAG 189: Marke dynamisch aus data holen
        brand = data.get('brand', 'hyundai')
        if brand == 'hyundai':
            teile_ueberschrift = "Verwendete Hyundai Original-Teile"
        elif brand == 'stellantis':
            teile_ueberschrift = "Verwendete Original-Teile"
        else:
            teile_ueberschrift = "Verwendete Original-Teile"
        
        elements.append(Paragraph(teile_ueberschrift, heading_style))
        
        teile_data = [['Teilenummer', 'Beschreibung', 'Menge', 'Preis']]
        for teil in teile:
            beschreibung = teil.get('beschreibung', '')
            # TAG 192: None-Check für Paragraph (verhindert 'NoneType' object has no attribute 'split')
            beschreibung_para = safe_paragraph(beschreibung, normal_style) if beschreibung else ''
            
            teile_data.append([
                teil.get('teilenummer', ''),
                beschreibung_para,
                f"{teil.get('menge', 0):.2f}",
                f"{teil.get('preis', 0):.2f} €"
            ])
        
        teile_table = Table(teile_data, colWidths=[3*cm, 8*cm, 2*cm, 2.5*cm])
        teile_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            # TAG 189: Bessere Zeilenhöhe für Paragraphs
            ('WORDWRAP', (1, 1), (1, -1)),  # Beschreibung umbrechen
        ]))
        
        elements.append(teile_table)
        elements.append(Spacer(1, 0.5*cm))
    
    # Arbeitszeit nach Monteur (TT-Zeiten)
    stempelzeiten = data.get('locosoft', {}).get('stempelzeiten', [])
    if stempelzeiten:
        elements.append(Paragraph("Angewandte Arbeitszeit nach Monteur (TT-Zeiten)", heading_style))
        
        # Gruppiere nach Mechaniker
        by_mechaniker = {}
        for st in stempelzeiten:
            mech = st.get('mechaniker', 'Unbekannt')
            if mech not in by_mechaniker:
                by_mechaniker[mech] = []
            by_mechaniker[mech].append(st)
        
        for mech, zeiten in by_mechaniker.items():
            elements.append(Paragraph(f"<b>{mech}</b>", normal_style))
            
            zeit_data = [['Von', 'Bis', 'Dauer (Min)', 'Dauer (AW)']]
            total_min = 0
            for zeit in zeiten:
                start = format_datetime(zeit.get('start', ''))
                ende = format_datetime(zeit.get('ende', ''))
                dauer_min = zeit.get('dauer_min', 0)
                dauer_aw = dauer_min / 6.0
                total_min += dauer_min
                zeit_data.append([start, ende, str(dauer_min), f"{dauer_aw:.2f}"])
            
            # Gesamt - verwende Paragraph für fette Formatierung
            bold_style = ParagraphStyle(
                'Bold',
                parent=normal_style,
                fontName='Helvetica-Bold'
            )
            total_aw = total_min / 6.0
            zeit_data.append([
                '', 
                '', 
                Paragraph(f"<b>{total_min}</b>", bold_style), 
                Paragraph(f"<b>{total_aw:.2f}</b>", bold_style)
            ])
            
            zeit_table = Table(zeit_data, colWidths=[4*cm, 4*cm, 3*cm, 3*cm])
            zeit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            
            elements.append(zeit_table)
            elements.append(Spacer(1, 0.3*cm))
    
    # Schadenverursachendes Teil
    if teile:
        schaden_teil = teile[0] if len(teile) > 0 else None
        if schaden_teil:
            elements.append(Paragraph("Schadenverursachendes Teil", heading_style))
            teilenummer = schaden_teil.get('teilenummer', '') or ''
            beschreibung = schaden_teil.get('beschreibung', '') or ''
            elements.append(Paragraph(
                f"<b>{teilenummer}</b>: {beschreibung}",
                normal_style
            ))
            elements.append(Spacer(1, 0.5*cm))
    
    # Weitere Feststellungen
    if gudat and gudat_tasks:
        elements.append(Paragraph("Weitere Feststellungen", heading_style))
        for task in gudat_tasks:
            desc = task.get('description', '') or ''
            if desc and len(desc) > 100:  # Nur längere Anmerkungen
                elements.append(Paragraph(desc.replace('\n', '<br/>'), normal_style))
                elements.append(Spacer(1, 0.3*cm))
    
    # Endkontrolle (Platzhalter)
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph("Endkontrolle", heading_style))
    endkontrolle_data = [
        ['Datum:', '_________________', 'Endkilometerstand:', '_________________'],
        ['Unterschrift:', '_________________', '', '']
    ]
    endkontrolle_table = Table(endkontrolle_data, colWidths=[3*cm, 5*cm, 3*cm, 4*cm])
    endkontrolle_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(endkontrolle_table)
    
    # Footer
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(
        f"<i>Erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr | Auftrag #{data.get('order_number', '')}</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=7, textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    # PDF generieren
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
