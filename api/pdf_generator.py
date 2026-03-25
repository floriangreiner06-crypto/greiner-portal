"""
PDF-Generator für Reports
Greiner Portal DRIVE

Version 3.0 - Mit TEK Daily Reports (TAG132)
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime, date
import re


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


def generate_auftragseingang_komplett_pdf(tag_data: dict, monat_data: dict, datum_display: str, monat_display: str,
                                          nw_tag: list = None, nw_monat: list = None,
                                          werktage: dict = None, prognose: int = None, ae_pro_tag: float = None) -> bytes:
    """
    Generiert PDF für Auftragseingang mit TAG und MONAT kumuliert.
    Design angelehnt an TEK. Datenquelle = VerkaufData (konsistent mit DRIVE online).
    Optional: Werktage/Prognose, NW nach Marke/Modell.

    Args:
        tag_data: Liste Verkäufer für den Tag (aus VerkaufData.get_auftragseingang_detail)
        monat_data: Liste Verkäufer für den Monat
        datum_display: z.B. "26.11.2025"
        monat_display: z.B. "November 2025"
        nw_tag / nw_monat: Optional Neuwagen nach Marke/Modell
        werktage: Optional {gesamt, vergangen, verbleibend} von get_werktage_monat
        prognose: Optional Prognose AE (auf Monatsende hochgerechnet)
        ae_pro_tag: Optional Ø AE/Tag
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
    DRIVE_BLUE = colors.HexColor('#0066cc')
    GRAY = colors.HexColor('#6c757d')
    LIGHT_BG = colors.HexColor('#f8f9fa')
    SUM_BG = colors.HexColor('#e7f1ff')

    def _shorten_model_name(name: str, max_len: int = 24) -> str:
        text = (name or '–').strip()
        if len(text) <= max_len:
            return text
        return text[:max_len - 1].rstrip() + "…"

    def _normalize_model_name(name: str) -> str:
        """
        Vereinheitlicht Modellbezeichnungen für bessere Lesbarkeit im Report.
        Beispiel: "NEW TUCSON Prime 1.6 T-GDI" -> "Tucson".
        """
        raw = (name or '').strip()
        if not raw:
            return 'Unbekannt'
        cleaned = re.sub(r'\s+', ' ', raw).strip()
        upper = cleaned.upper()
        tokens = re.findall(r'[A-Z0-9\-\+]+', upper)
        stopwords = {
            'NEW', 'FACELIFT', 'FL', 'MY', 'MJ', 'PRIME', 'TREND', 'STYLE',
            'SELECT', 'NLINE', 'N-LINE', 'N', 'EDITION', 'BUSINESS', 'PLUS',
            'HYBRID', 'PHEV', 'HEV', 'EV', 'BEV', 'T-GDI', 'CRDI', 'GDI',
            'DCT', 'AT', 'MT', 'AUTOMATIK', 'SCHALTER', '4X4', '2WD',
            'BASIS', 'GS', 'ULTIMATE'
        }
        model_prefixes = [
            'TUCSON', 'KONA', 'I10', 'I20', 'I30', 'BAYON', 'SANTA', 'IONIQ',
            'MOKKA', 'CORSA', 'ASTRA', 'GRANDLAND', 'FRONTERA', 'COMBO',
            'VIVARO', 'ZAFIRA', 'CROSSLAND', 'INSIGNIA',
            'C10', 'T03'
        ]

        for i in range(len(tokens)):
            for pref in model_prefixes:
                if tokens[i].startswith(pref):
                    if pref == 'SANTA' and i + 1 < len(tokens) and tokens[i + 1].startswith('FE'):
                        return 'Santa Fe'
                    if pref == 'GRANDLAND':
                        return 'Grandland'
                    if pref == 'CROSSLAND':
                        return 'Crossland'
                    if pref == 'INSIGNIA':
                        return 'Insignia'
                    if pref == 'VIVARO':
                        return 'Vivaro'
                    if pref == 'ZAFIRA':
                        return 'Zafira'
                    if pref == 'COMBO':
                        return 'Combo'
                    if pref == 'T03':
                        return 'T03'
                    if pref == 'C10':
                        return 'C10'
                    return pref.title().replace('Ioniq', 'IONIQ')

        filtered = [t for t in tokens if t not in stopwords and len(t) > 1]
        if filtered:
            return filtered[0].title().replace('Ioniq', 'IONIQ')
        return _shorten_model_name(cleaned, 20)

    def _build_modelmix_text(vk: dict, max_models: int = 3) -> str:
        mix = {}
        for bucket in ('neu', 'test_vorfuehr', 'gebraucht'):
            for item in (vk.get(bucket) or []):
                norm = _normalize_model_name(item.get('modell'))
                mix[norm] = mix.get(norm, 0) + int(item.get('anzahl', 0) or 0)
        if not mix:
            return '–'
        top = sorted(mix.items(), key=lambda x: x[1], reverse=True)[:max_models]
        return ", ".join([f"{_shorten_model_name(name, 14)} {qty}" for name, qty in top])

    # TEK-ähnliche Styles
    title_style = ParagraphStyle(
        'AETitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_LEFT,
        spaceAfter=4,
        textColor=DRIVE_BLUE,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'AESubtitle',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_LEFT,
        textColor=GRAY,
        spaceAfter=10
    )
    section_style = ParagraphStyle(
        'AESection',
        parent=styles['Heading2'],
        fontSize=11,
        spaceAfter=6,
        spaceBefore=12,
        textColor=DRIVE_BLUE,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )

    # === HEADER (wie TEK) ===
    elements.append(Paragraph("Auftragseingang", title_style))
    line_table = Table([['']], colWidths=[16*cm])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 3, DRIVE_BLUE),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(line_table)
    elements.append(Paragraph(
        f"Monat: {monat_display} · Stand: {datum_display} {datetime.now().strftime('%H:%M')} Uhr",
        subtitle_style
    ))

    # === ÜBERSICHT (ohne Umsatz) ===
    tag_summary = {
        'neu': sum(v.get('summe_neu', 0) for v in tag_data),
        'test_vorfuehr': sum(v.get('summe_test_vorfuehr', 0) for v in tag_data),
        'gebraucht': sum(v.get('summe_gebraucht', 0) for v in tag_data),
        'gesamt': sum(v.get('summe_gesamt', 0) for v in tag_data),
    }
    monat_summary = {
        'neu': sum(v.get('summe_neu', 0) for v in monat_data),
        'test_vorfuehr': sum(v.get('summe_test_vorfuehr', 0) for v in monat_data),
        'gebraucht': sum(v.get('summe_gebraucht', 0) for v in monat_data),
        'gesamt': sum(v.get('summe_gesamt', 0) for v in monat_data),
    }

    overview_data = [
        ['', 'Neuwagen', 'Test/Vorführ', 'Gebraucht', 'GESAMT'],
        [f'Heute ({datum_display})', str(tag_summary['neu']), str(tag_summary['test_vorfuehr']), str(tag_summary['gebraucht']), str(tag_summary['gesamt'])],
        [monat_display, str(monat_summary['neu']), str(monat_summary['test_vorfuehr']), str(monat_summary['gebraucht']), str(monat_summary['gesamt'])]
    ]
    col_widths_overview = [4.5*cm, 2.5*cm, 2.8*cm, 2.5*cm, 2.2*cm]
    overview_table = Table(overview_data, colWidths=col_widths_overview)
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, 1), LIGHT_BG),
        ('BACKGROUND', (0, 2), (-1, 2), colors.white),
        ('FONTNAME', (0, 1), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 1), (-1, 2), 12),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
    ]))
    elements.append(overview_table)

    # Werktage + Prognose (wie DRIVE online)
    if werktage and (prognose is not None or ae_pro_tag is not None):
        wt_para = f"Werktage: {werktage.get('vergangen', 0)} von {werktage.get('gesamt', 0)} vergangen ({werktage.get('verbleibend', 0)} verbleibend)"
        if ae_pro_tag is not None:
            wt_para += f" · Ø {ae_pro_tag} AE/Tag"
        if prognose is not None:
            wt_para += f" · Prognose: {prognose} AE"
        prog_style = ParagraphStyle('AEProg', parent=styles['Normal'], fontSize=9, textColor=GRAY, spaceAfter=6)
        elements.append(Paragraph(wt_para, prog_style))
    elements.append(Spacer(1, 8))

    # === NEUWAGEN NACH MARKE UND MODELL (normalisiert) ===
    if nw_tag or nw_monat:
        elements.append(Paragraph("Neuwagen nach Marke und Modelltyp (normalisiert)", section_style))
        # Eine Tabelle: Marke | Modelltyp | Heute | Monat
        nw_tag_map = {}
        for r in (nw_tag or []):
            key = (r.get('marke', ''), _normalize_model_name(r.get('modell', '')))
            nw_tag_map[key] = nw_tag_map.get(key, 0) + int(r.get('anzahl', 0) or 0)
        nw_monat_map = {}
        for r in (nw_monat or []):
            key = (r.get('marke', ''), _normalize_model_name(r.get('modell', '')))
            nw_monat_map[key] = nw_monat_map.get(key, 0) + int(r.get('anzahl', 0) or 0)
        nw_all_keys = set(nw_tag_map.keys()) | set(nw_monat_map.keys())
        nw_rows = [['Marke', 'Modelltyp', f'Heute ({datum_display})', monat_display]]
        for (marke, modell) in sorted(nw_all_keys, key=lambda x: (x[0] or '', x[1] or '')):
            nw_rows.append([
                marke or '–',
                _shorten_model_name(modell or '–', 26),
                str(nw_tag_map.get((marke, modell), 0)),
                str(nw_monat_map.get((marke, modell), 0))
            ])
        if len(nw_rows) > 1:
            col_nw = [3.5*cm, 5*cm, 2.5*cm, 2.5*cm]
            nw_table = Table(nw_rows, colWidths=col_nw)
            nw_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ]))
            elements.append(nw_table)
        elements.append(Spacer(1, 8))

    # === HEUTE – nach Verkäufer mit Modellmix ===
    elements.append(Paragraph(f"Heute ({datum_display}) – nach Verkäufer", section_style))
    if tag_data:
        tag_table_data = [['Verkäufer', 'NW', 'T/V', 'GW', 'Ges.', 'Modellmix (Top)']]
        for vk in sorted(tag_data, key=lambda x: x.get('summe_gesamt', 0), reverse=True):
            if vk.get('summe_gesamt', 0) > 0:
                tag_table_data.append([
                    vk.get('verkaufer_name', 'Unbekannt')[:25],
                    str(vk.get('summe_neu', 0)),
                    str(vk.get('summe_test_vorfuehr', 0)),
                    str(vk.get('summe_gebraucht', 0)),
                    str(vk.get('summe_gesamt', 0)),
                    _build_modelmix_text(vk)
                ])
        if len(tag_table_data) > 1:
            col_widths_detail = [4.8*cm, 1.6*cm, 1.6*cm, 1.6*cm, 1.3*cm, 5.7*cm]
            tag_table = Table(tag_table_data, colWidths=col_widths_detail)
            tag_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (4, -1), 'CENTER'),
                ('ALIGN', (5, 0), (5, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ]))
            elements.append(tag_table)
        else:
            elements.append(Paragraph("Keine Aufträge heute.", styles['Normal']))
    else:
        elements.append(Paragraph("Keine Aufträge heute.", styles['Normal']))

    # === MONAT – nach Verkäufer mit Modellmix ===
    elements.append(Paragraph(f"{monat_display} kumuliert – nach Verkäufer", section_style))
    if monat_data:
        monat_table_data = [['Verkäufer', 'NW', 'T/V', 'GW', 'Ges.', 'Modellmix (Top)']]
        for vk in sorted(monat_data, key=lambda x: x.get('summe_gesamt', 0), reverse=True):
            if vk.get('summe_gesamt', 0) > 0:
                monat_table_data.append([
                    vk.get('verkaufer_name', 'Unbekannt')[:25],
                    str(vk.get('summe_neu', 0)),
                    str(vk.get('summe_test_vorfuehr', 0)),
                    str(vk.get('summe_gebraucht', 0)),
                    str(vk.get('summe_gesamt', 0)),
                    _build_modelmix_text(vk)
                ])
        monat_table_data.append([
            'GESAMT',
            str(monat_summary['neu']),
            str(monat_summary['test_vorfuehr']),
            str(monat_summary['gebraucht']),
            str(monat_summary['gesamt']),
            '–'
        ])
        col_widths_detail = [4.8*cm, 1.6*cm, 1.6*cm, 1.6*cm, 1.3*cm, 5.7*cm]
        monat_table = Table(monat_table_data, colWidths=col_widths_detail)
        monat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (4, -1), 'CENTER'),
            ('ALIGN', (5, 0), (5, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, LIGHT_BG]),
            ('BACKGROUND', (0, -1), (-1, -1), SUM_BG),
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


def get_tek_cleanpark_direct(firma, standort, von_heute, bis_heute, von_monat, bis_monat):
    """Holt Clean-Park-Erlöse (847301) und -Aufwand (747301) für TEK-KST-Zeile. Returns dict mit heute_umsatz, heute_einsatz, monat_umsatz, monat_einsatz."""
    from api.db_connection import get_db, convert_placeholders
    firma_filter = ""
    if firma == '1':
        firma_filter = "AND subsidiary_to_company_ref = 1"
        if standort == '1':
            firma_filter += " AND branch_number = 1"
        elif standort == '2':
            firma_filter += " AND branch_number = 3"
    elif firma == '2':
        firma_filter = "AND subsidiary_to_company_ref = 2"
    try:
        db = get_db()
        cur = db.cursor()
        res = {'heute_umsatz': 0, 'heute_einsatz': 0, 'monat_umsatz': 0, 'monat_einsatz': 0}
        for label, von, bis in [('heute', von_heute, bis_heute), ('monat', von_monat, bis_monat)]:
            cur.execute(convert_placeholders(f"""
                SELECT SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s AND nominal_account_number = 847301 {firma_filter}
            """), (von, bis))
            row = cur.fetchone()
            res[f'{label}_umsatz'] = float(row[0] or 0) if row else 0
            cur.execute(convert_placeholders(f"""
                SELECT SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as einsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s AND nominal_account_number = 747301 {firma_filter}
            """), (von, bis))
            row = cur.fetchone()
            res[f'{label}_einsatz'] = float(row[0] or 0) if row else 0
        db.close()
        return res
    except Exception:
        if 'db' in locals():
            db.close()
        return {'heute_umsatz': 0, 'heute_einsatz': 0, 'monat_umsatz': 0, 'monat_einsatz': 0}


def get_tek_absatzwege_direct(bereich, firma, standort, monat, jahr, heute_datum=None):
    """Holt Absatzwege-Daten direkt aus DRIVE DB (drive_portal) - Single Source of Truth (nur für NW/GW). Modul-Level für Wiederverwendung in TEK Verkauf-PDF."""
    from api.db_connection import get_db, convert_placeholders
    import psycopg2.extras
    from datetime import datetime, date, timedelta
    import re

    if bereich not in ['1-NW', '2-GW']:
        return {'absatzwege': []}

    try:
        if not monat or not jahr:
            heute = date.today()
            monat = monat or heute.month
            jahr = jahr or heute.year

        von = f"{jahr}-{monat:02d}-01"
        bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"

        if heute_datum:
            if isinstance(heute_datum, str):
                heute_str = datetime.strptime(heute_datum, '%d.%m.%Y').strftime('%Y-%m-%d') if '.' in heute_datum else heute_datum
            else:
                heute_str = heute_datum.strftime('%Y-%m-%d')
        else:
            heute_str = date.today().strftime('%Y-%m-%d')

        morgen_str = (datetime.strptime(heute_str, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

        firma_filter = ""
        if firma == '1':
            firma_filter = "AND j.subsidiary_to_company_ref = 1"
            if standort == '1':
                firma_filter += " AND j.branch_number = 1"
            elif standort == '2':
                firma_filter += " AND j.branch_number = 3"
        elif firma == '2':
            firma_filter = "AND j.subsidiary_to_company_ref = 2"

        bereich_konten = {
            '1-NW': {'umsatz': (810000, 819999), 'einsatz': (710000, 719999)},
            '2-GW': {'umsatz': (820000, 829999), 'einsatz': (720000, 729999)}
        }
        ranges = bereich_konten[bereich]

        def parse_modell_aus_kontobezeichnung(bezeichnung: str) -> dict:
            if not bezeichnung:
                return {'modell': 'Sonstige', 'kundentyp': '', 'verkaufsart': ''}
            bez = bezeichnung.strip()
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
            for prefix in ['NW VE ', 'NW EW ', 'GW VE ', 'GW EW ', 'VE ', 'EW ']:
                if bez.startswith(prefix):
                    bez = bez[len(prefix):]
                    break
            kundentyp_patterns = [('Gewerbekd ', 'Gewerbe'), ('Gewdkd ', 'Gewerbe'), ('Gewkd ', 'Gewerbe'), ('Großkunden ', 'Großkunde'), ('Großkd ', 'Großkunde'), ('Kunden ', 'Privat'), ('KD ', 'Privat'), ('Kd ', 'Privat'), ('Händler ', 'Händler')]
            modell, kundentyp, verkaufsart = bez, '', ''
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
            v = (verkaufsart or '').lower()
            if 'leas' in v:
                return 'Leasing'
            if 'kauf' in v:
                return 'Kauf'
            if 'reg' in v or 'regulär' in v:
                return 'reg'
            return 'Sonstige'

        absatzweg_stats = {}
        db = get_db()
        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

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
            if bereich == '2-GW' and konto in (823101, 823102):
                absatzweg = 'Privat reg'
            if absatzweg not in absatzweg_stats:
                absatzweg_stats[absatzweg] = {'absatzweg': absatzweg, 'stueck_monat': 0, 'umsatz_monat': 0, 'einsatz_monat': 0, 'konten': []}
            absatzweg_stats[absatzweg]['stueck_monat'] += stueck
            absatzweg_stats[absatzweg]['umsatz_monat'] += betrag
            absatzweg_stats[absatzweg]['konten'].append({
                'konto': konto, 'bezeichnung': bezeichnung, 'umsatz_monat': betrag, 'einsatz_monat': 0,
                'stueck_monat': stueck, 'umsatz_heute': 0, 'einsatz_heute': 0, 'stueck_heute': 0
            })

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
            # GW Leasingrücknahme (723101, 723102) → Privat reg
            if bereich == '2-GW' and konto in (723101, 723102):
                absatzweg = 'Privat reg'
            if absatzweg not in absatzweg_stats:
                absatzweg_stats[absatzweg] = {'absatzweg': absatzweg, 'stueck_monat': 0, 'umsatz_monat': 0, 'einsatz_monat': 0, 'konten': []}
            absatzweg_stats[absatzweg]['einsatz_monat'] += betrag
            konto_gefunden = False
            for k in absatzweg_stats[absatzweg]['konten']:
                if k['konto'] == konto:
                    k['einsatz_monat'] += betrag
                    konto_gefunden = True
                    break
            if not konto_gefunden:
                absatzweg_stats[absatzweg]['konten'].append({
                    'konto': konto, 'bezeichnung': bezeichnung, 'umsatz_monat': 0, 'einsatz_monat': betrag,
                    'stueck_monat': 0, 'umsatz_heute': 0, 'einsatz_heute': 0, 'stueck_heute': 0
                })

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
            if bereich == '2-GW' and konto in (823101, 823102):
                absatzweg = 'Privat reg'
            if absatzweg in absatzweg_stats:
                for k in absatzweg_stats[absatzweg]['konten']:
                    if k['konto'] == konto:
                        k['umsatz_heute'] += betrag
                        k['stueck_heute'] += stueck
                        break

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
            for absatzweg_data in absatzweg_stats.values():
                for k in absatzweg_data['konten']:
                    if k['konto'] == konto:
                        k['einsatz_heute'] += betrag
                        break

        absatzwege = []
        for a in absatzweg_stats.values():
            if a['umsatz_monat'] > 0 or a['einsatz_monat'] > 0:
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
        # Sortierung wie Global Cube: Privat Kauf/Leasing, Gewerbe Kauf/Leasing, Sonstige Kauf/Leasing, Privat reg, Privat Sonstige, Sonstige Sonstige
        _aw_order = ['Privat Kauf', 'Privat Leasing', 'Gewerbe Kauf', 'Gewerbe Leasing', 'Sonstige Kauf', 'Sonstige Leasing', 'Privat reg', 'Privat Sonstige', 'Sonstige Sonstige']
        absatzwege.sort(key=lambda x: (_aw_order.index(x['absatzweg']) if x['absatzweg'] in _aw_order else 99, x['absatzweg']))
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
    """Holt detaillierte TEK-Daten (umsatz_gruppen + einsatz_gruppen) aus DRIVE DB. Modul-Level für Wiederverwendung in TEK Service-PDF."""
    from api.db_connection import get_db, convert_placeholders
    import psycopg2.extras
    from datetime import datetime, date, timedelta

    bereich_konten = {
        '1-NW': {'umsatz': (810000, 819999), 'einsatz': (710000, 719999)},
        '2-GW': {'umsatz': (820000, 829999), 'einsatz': (720000, 729999)},
        '3-Teile': {'umsatz': (830000, 839999), 'einsatz': (730000, 739999)},
        '4-Lohn': {'umsatz': (840000, 849999), 'einsatz': (740000, 749999)},
        '5-Sonst': {'umsatz': (860000, 869999), 'einsatz': (760000, 769999)}
    }
    empty = {'monat': {'umsatz_gruppen': [], 'einsatz_gruppen': []}, 'heute': {'umsatz_gruppen': [], 'einsatz_gruppen': []}}
    if bereich not in bereich_konten:
        return empty
    try:
        if not monat or not jahr:
            heute = date.today()
            monat = monat or heute.month
            jahr = jahr or heute.year
        von = f"{jahr}-{monat:02d}-01"
        bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"
        if heute_datum:
            if isinstance(heute_datum, str):
                heute_str = datetime.strptime(heute_datum, '%d.%m.%Y').strftime('%Y-%m-%d') if '.' in heute_datum else heute_datum
            else:
                heute_str = heute_datum.strftime('%Y-%m-%d')
        else:
            heute_str = date.today().strftime('%Y-%m-%d')
        morgen_str = (datetime.strptime(heute_str, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

        firma_filter = ""
        if firma == '1':
            firma_filter = "AND subsidiary_to_company_ref = 1"
            if standort == '1':
                firma_filter += " AND branch_number = 1"
            elif standort == '2':
                firma_filter += " AND branch_number = 3"
        elif firma == '2':
            firma_filter = "AND subsidiary_to_company_ref = 2"

        ranges = bereich_konten[bereich]
        db = get_db()

        def hole_gruppen(konto_range, vorzeichen_typ, datum_von, datum_bis):
            vorz = "CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END" if vorzeichen_typ == 'einsatz' else "CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END"
            cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(convert_placeholders(f"""
                SELECT * FROM (
                    SELECT substr(CAST(nominal_account_number AS TEXT), 1, 2) as gruppe,
                           SUM({vorz}) / 100.0 as betrag
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN %s AND %s
                      {firma_filter}
                    GROUP BY substr(CAST(nominal_account_number AS TEXT), 1, 2)
                ) sub WHERE betrag != 0 ORDER BY gruppe
            """), (datum_von, datum_bis, konto_range[0], konto_range[1]))
            gruppen = [{'gruppe': row['gruppe'], 'betrag': round(float(row['betrag'] or 0), 2)} for row in cur.fetchall()]
            return gruppen

        umsatz_gruppen_monat = hole_gruppen(ranges['umsatz'], 'umsatz', von, bis)
        einsatz_gruppen_monat = hole_gruppen(ranges['einsatz'], 'einsatz', von, bis)
        umsatz_gruppen_heute = hole_gruppen(ranges['umsatz'], 'umsatz', heute_str, morgen_str)
        einsatz_gruppen_heute = hole_gruppen(ranges['einsatz'], 'einsatz', heute_str, morgen_str)
        db.close()
        return {
            'monat': {'umsatz_gruppen': umsatz_gruppen_monat, 'einsatz_gruppen': einsatz_gruppen_monat},
            'heute': {'umsatz_gruppen': umsatz_gruppen_heute, 'einsatz_gruppen': einsatz_gruppen_heute}
        }
    except Exception as e:
        print(f"⚠️  Fehler beim Abrufen von Detail-Daten für {bereich}: {e}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.close()
    return empty


def get_tek_bereich_konten_direct(bereich, firma, standort, monat, jahr, heute_datum=None):
    """Holt Konten-Details für 3-Teile und 4-Lohn (wie Absatzwege für NW/GW): pro Konto Umsatz/Einsatz Heute+Monat, gepaart 83+73 bzw. 84+74."""
    from api.db_connection import get_db, convert_placeholders
    import psycopg2.extras
    from datetime import datetime, date, timedelta

    bereich_konten = {
        '3-Teile': {'umsatz': (830000, 839999), 'einsatz': (730000, 739999), 'label': 'Teile (83/73)'},
        '4-Lohn': {'umsatz': (840000, 849999), 'einsatz': (740000, 749999), 'label': 'Lohn (84/74)'}
    }
    if bereich not in bereich_konten:
        return {'absatzwege': []}
    try:
        if not monat or not jahr:
            heute = date.today()
            monat = monat or heute.month
            jahr = jahr or heute.year
        von = f"{jahr}-{monat:02d}-01"
        bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"
        if heute_datum:
            heute_str = datetime.strptime(heute_datum, '%d.%m.%Y').strftime('%Y-%m-%d') if isinstance(heute_datum, str) and '.' in heute_datum else (heute_datum.strftime('%Y-%m-%d') if hasattr(heute_datum, 'strftime') else str(heute_datum)[:10])
        else:
            heute_str = date.today().strftime('%Y-%m-%d')
        morgen_str = (datetime.strptime(heute_str, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

        firma_filter = ""
        if firma == '1':
            firma_filter = "AND j.subsidiary_to_company_ref = 1"
            if standort == '1':
                firma_filter += " AND j.branch_number = 1"
            elif standort == '2':
                firma_filter += " AND j.branch_number = 3"
        elif firma == '2':
            firma_filter = "AND j.subsidiary_to_company_ref = 2"

        ranges = bereich_konten[bereich]
        db = get_db()
        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Monat: Umsatz pro Konto
        cur.execute(convert_placeholders(f"""
            SELECT j.nominal_account_number as konto,
                   COALESCE(n.account_description, MIN(j.posting_text), '') as bezeichnung,
                   SUM(CASE WHEN j.debit_or_credit = 'H' THEN j.posted_value ELSE -j.posted_value END) / 100.0 as betrag
            FROM loco_journal_accountings j
            LEFT JOIN loco_nominal_accounts n ON j.nominal_account_number = n.nominal_account_number AND j.subsidiary_to_company_ref = n.subsidiary_to_company_ref
            WHERE j.accounting_date >= %s AND j.accounting_date < %s AND j.nominal_account_number BETWEEN %s AND %s {firma_filter}
            GROUP BY j.nominal_account_number, n.account_description
        """), (von, bis, ranges['umsatz'][0], ranges['umsatz'][1]))
        umsatz_monat = {int(r['konto']): {'bezeichnung': r.get('bezeichnung') or '', 'umsatz_monat': float(r.get('betrag') or 0), 'einsatz_monat': 0, 'umsatz_heute': 0, 'einsatz_heute': 0} for r in cur.fetchall()}

        cur.execute(convert_placeholders(f"""
            SELECT j.nominal_account_number as konto,
                   COALESCE(n.account_description, MIN(j.posting_text), '') as bezeichnung,
                   SUM(CASE WHEN j.debit_or_credit = 'S' THEN j.posted_value ELSE -j.posted_value END) / 100.0 as betrag
            FROM loco_journal_accountings j
            LEFT JOIN loco_nominal_accounts n ON j.nominal_account_number = n.nominal_account_number AND j.subsidiary_to_company_ref = n.subsidiary_to_company_ref
            WHERE j.accounting_date >= %s AND j.accounting_date < %s AND j.nominal_account_number BETWEEN %s AND %s {firma_filter}
            GROUP BY j.nominal_account_number, n.account_description
        """), (von, bis, ranges['einsatz'][0], ranges['einsatz'][1]))
        for r in cur.fetchall():
            k = int(r['konto'])
            if k not in umsatz_monat:
                umsatz_monat[k] = {'bezeichnung': r.get('bezeichnung') or '', 'umsatz_monat': 0, 'einsatz_monat': 0, 'umsatz_heute': 0, 'einsatz_heute': 0}
            umsatz_monat[k]['einsatz_monat'] = float(r.get('betrag') or 0)

        cur.execute(convert_placeholders(f"""
            SELECT j.nominal_account_number as konto,
                   SUM(CASE WHEN j.debit_or_credit = 'H' THEN j.posted_value ELSE -j.posted_value END) / 100.0 as betrag
            FROM loco_journal_accountings j
            WHERE j.accounting_date >= %s AND j.accounting_date < %s AND j.nominal_account_number BETWEEN %s AND %s {firma_filter}
            GROUP BY j.nominal_account_number
        """), (heute_str, morgen_str, ranges['umsatz'][0], ranges['umsatz'][1]))
        for r in cur.fetchall():
            k = int(r['konto'])
            if k not in umsatz_monat:
                umsatz_monat[k] = {'bezeichnung': '', 'umsatz_monat': 0, 'einsatz_monat': 0, 'umsatz_heute': 0, 'einsatz_heute': 0}
            umsatz_monat[k]['umsatz_heute'] = float(r.get('betrag') or 0)

        cur.execute(convert_placeholders(f"""
            SELECT j.nominal_account_number as konto,
                   SUM(CASE WHEN j.debit_or_credit = 'S' THEN j.posted_value ELSE -j.posted_value END) / 100.0 as betrag
            FROM loco_journal_accountings j
            WHERE j.accounting_date >= %s AND j.accounting_date < %s AND j.nominal_account_number BETWEEN %s AND %s {firma_filter}
            GROUP BY j.nominal_account_number
        """), (heute_str, morgen_str, ranges['einsatz'][0], ranges['einsatz'][1]))
        for r in cur.fetchall():
            k = int(r['konto'])
            if k not in umsatz_monat:
                umsatz_monat[k] = {'bezeichnung': '', 'umsatz_monat': 0, 'einsatz_monat': 0, 'umsatz_heute': 0, 'einsatz_heute': 0}
            umsatz_monat[k]['einsatz_heute'] = float(r.get('betrag') or 0)

        db.close()

        # Paare bilden: gleiche letzte 4 Ziffern (83xxxx+73xxxx bzw. 84xxxx+74xxxx)
        paired = {}
        for konto, v in umsatz_monat.items():
            key = konto % 10000
            if key not in paired:
                paired[key] = {'erlos': None, 'einsatz': None}
            if ranges['umsatz'][0] <= konto <= ranges['umsatz'][1]:
                paired[key]['erlos'] = {'konto': konto, 'bezeichnung': v['bezeichnung'], 'umsatz_heute': v['umsatz_heute'], 'umsatz_monat': v['umsatz_monat'], 'einsatz_heute': 0, 'einsatz_monat': 0, 'stueck_heute': 0, 'stueck_monat': 0}
            elif ranges['einsatz'][0] <= konto <= ranges['einsatz'][1]:
                paired[key]['einsatz'] = {'konto': konto, 'bezeichnung': v['bezeichnung'], 'umsatz_heute': 0, 'umsatz_monat': 0, 'einsatz_heute': v['einsatz_heute'], 'einsatz_monat': v['einsatz_monat'], 'stueck_heute': 0, 'stueck_monat': 0}

        konten_list = []
        for key in sorted(paired.keys()):
            er, en = paired[key]['erlos'], paired[key]['einsatz']
            ku_h = (er['umsatz_heute'] if er else 0)
            ke_h = (en['einsatz_heute'] if en else 0)
            ku_m = (er['umsatz_monat'] if er else 0)
            ke_m = (en['einsatz_monat'] if en else 0)
            bez = (er['bezeichnung'] if er else (en['bezeichnung'] if en else '')).strip()
            konto_display = (er['konto'] if er else en['konto'])
            konten_list.append({
                'konto': konto_display,
                'bezeichnung': bez or f"Konto {konto_display}",
                'umsatz_heute': round(ku_h, 2), 'einsatz_heute': round(ke_h, 2),
                'umsatz_monat': round(ku_m, 2), 'einsatz_monat': round(ke_m, 2),
                'stueck_heute': 0, 'stueck_monat': 0
            })

        uh = sum(k['umsatz_heute'] for k in konten_list)
        eh = sum(k['einsatz_heute'] for k in konten_list)
        um = sum(k['umsatz_monat'] for k in konten_list)
        em = sum(k['einsatz_monat'] for k in konten_list)
        return {
            'absatzwege': [{
                'absatzweg': ranges['label'],
                'stueck_heute': 0, 'stueck_monat': 0,
                'umsatz_heute': round(uh, 2), 'einsatz_heute': round(eh, 2), 'db1_heute': round(uh - eh, 2),
                'umsatz_monat': round(um, 2), 'einsatz_monat': round(em, 2), 'db1_monat': round(um - em, 2),
                'konten': konten_list
            }]
        }
    except Exception as e:
        print(f"⚠️  get_tek_bereich_konten_direct {bereich}: {e}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            try:
                db.close()
            except Exception:
                pass
    return {'absatzwege': []}


def generate_tek_daily_pdf(data: dict) -> bytes:
    """
    Generiert PDF für TEK (Tägliche Erfolgskontrolle) – Mockup V2 (Vorlage für alle TEK-Reports).
    Struktur: Seite 1 = Übersicht (Tag + Monat, Kern-KPIs, Bereichs-Übersicht), danach eine Seite pro KST.

    Args:
        data: Dict mit Keys:
            - datum: str (z.B. "22.12.2025")
            - monat: str (z.B. "Dezember 2025")
            - gesamt: dict mit db1, marge, prognose, breakeven
            - bereiche: list of dicts (bereich, umsatz, einsatz, db1, marge, heute_umsatz, heute_db1, …)
            - firma, standort_api, monat_num, jahr_num: Für Detail-APIs (Absatzwege, Clean Park)

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
    # Mockup V2: Status-Box positive = hellgrün wie HTML
    SUCCESS_BG = colors.HexColor('#d1e7dd')
    SUCCESS_TEXT = colors.HexColor('#0f5132')

    # Custom Styles (angelehnt an TEK_GESAMT_UEBERSICHT_MOCKUP_V2.html)
    title_style = ParagraphStyle(
        'TEKTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_LEFT,
        spaceAfter=4,
        textColor=DRIVE_BLUE,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'TEKSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_LEFT,
        textColor=GRAY,
        spaceAfter=6
    )
    kpi_label_style = ParagraphStyle(
        'KpiLabel',
        parent=styles['Normal'],
        fontSize=6,
        textColor=GRAY,
        alignment=TA_CENTER,
        spaceAfter=0,
        spaceBefore=0
    )
    kpi_value_style = ParagraphStyle(
        'KpiValue',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=GRAY_DARK,
        alignment=TA_CENTER,
        spaceAfter=0,
        spaceBefore=0
    )
    section_style = ParagraphStyle(
        'TEKSection',
        parent=styles['Heading2'],
        fontSize=11,
        spaceAfter=8,
        spaceBefore=12,
        textColor=DRIVE_BLUE,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    section_style_page1 = ParagraphStyle(
        'TEKSectionPage1',
        parent=section_style,
        fontSize=10,
        spaceAfter=3,
        spaceBefore=4
    )

    # === MOCKUP V2: Seite 1 = Übersicht (Tag + Monat), danach eine Seite pro KST ===
    from reportlab.platypus import Image as RLImage
    import os

    gesamt = data.get('gesamt', {})
    vormonat = data.get('vormonat', {})
    vorjahr = data.get('vorjahr', {})
    prognose_db1 = gesamt.get('prognose', gesamt.get('db1', 0))
    breakeven_absolut = gesamt.get('breakeven', 0)
    breakeven_abstand = prognose_db1 - breakeven_absolut

    # Datum/Heute für Übersicht
    datum_str = data.get('datum', '')
    if datum_str:
        try:
            heute_datum = datetime.strptime(datum_str, '%d.%m.%Y').strftime('%Y-%m-%d')
        except Exception:
            heute_datum = datetime.now().strftime('%Y-%m-%d')
    else:
        heute_datum = datetime.now().strftime('%Y-%m-%d')
    monat_num = data.get('monat_num') or (datetime.strptime(datum_str, '%d.%m.%Y').month if datum_str else datetime.now().month)
    jahr_num = data.get('jahr_num') or (datetime.strptime(datum_str, '%d.%m.%Y').year if datum_str else datetime.now().year)

    # KST-Reihenfolge und Namen (Mockup V2)
    KST_MAPPING = {
        '1-NW': {'kst': '1', 'name': 'Neuwagen', 'order': 1, 'show_stueck': True},
        '2-GW': {'kst': '2', 'name': 'Gebrauchtwagen', 'order': 2, 'show_stueck': True},
        '4-Lohn': {'kst': '3', 'name': 'Service/Werkstatt', 'order': 3, 'show_stueck': False},
        '3-Teile': {'kst': '6', 'name': 'Teile & Zubehör', 'order': 4, 'show_stueck': False},
        '5-Sonst': {'kst': '7', 'name': 'Sonstige', 'order': 5, 'show_stueck': False}
    }
    bereiche_sorted = sorted(
        data.get('bereiche', []),
        key=lambda b: KST_MAPPING.get(b.get('bereich', ''), {}).get('order', 99)
    )

    # Gesamt Heute aus Bereichen (für Kern-KPIs)
    gesamt_heute_db1 = sum(b.get('heute_db1', 0) for b in data.get('bereiche', []))
    gesamt_heute_umsatz = sum(b.get('heute_umsatz', 0) for b in data.get('bereiche', []))
    gesamt_heute_marge = (gesamt_heute_db1 / gesamt_heute_umsatz * 100) if gesamt_heute_umsatz > 0 else 0

    # Header wie Mockup: Titel (blau) + Linie + Untertitel
    elements.append(Paragraph("<b>TEK – Tägliche Erfolgskontrolle</b>", title_style))
    line_table = Table([['']], colWidths=[18*cm])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 3, DRIVE_BLUE),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(line_table)
    monat_text = data.get('monat', 'Aktueller Monat')
    standort_name = (data.get('standort_name') or '').strip()
    stand_str = f"Standort {standort_name} · " if (standort_name and standort_name.lower() != 'gesamt') else ""
    wt = gesamt.get('werktage') or {}
    wt_str = f" · Noch {wt.get('verbleibend', '–')} WT" if wt else ""
    subtitle_text = f"{stand_str}Monat: {monat_text} · Stand: {datum_str or datetime.now().strftime('%d.%m.%Y')} {datetime.now().strftime('%H:%M')} Uhr (Tag){wt_str}"
    elements.append(Paragraph(subtitle_text, subtitle_style))
    elements.append(Spacer(1, 6))

    # Kern-Kennzahlen als 6 Karten (Mockup: Label oben, Wert unten)
    elements.append(Paragraph("Kern-Kennzahlen", section_style_page1))
    kpi_labels = ['DB1 HEUTE', 'DB1 MONAT', 'MARGE HEUTE', 'MARGE MONAT', 'PROGNOSE', 'BREAKEVEN']
    kpi_vals = [
        format_currency_short(gesamt_heute_db1),
        format_currency_short(gesamt.get('db1', 0)),
        format_percent(gesamt_heute_marge),
        format_percent(gesamt.get('marge', 0)),
        format_currency_short(prognose_db1),
        format_currency_short(breakeven_absolut),
    ]
    kpi_row = []
    for i in range(6):
        cell_content = [Paragraph(kpi_labels[i], kpi_label_style), Paragraph(kpi_vals[i], kpi_value_style)]
        kpi_row.append(cell_content)
    kpi_table = Table([kpi_row], colWidths=[2.95*cm]*6)
    kpi_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 4))

    # Status-Box Breakeven (Mockup: positiv = #d1e7dd / #0f5132, negativ = rot)
    if breakeven_abstand >= 0:
        be_text = f"+{format_currency_short(breakeven_abstand)} über Breakeven (Prognose)"
        be_bg, be_fg = SUCCESS_BG, SUCCESS_TEXT
    else:
        be_text = f"{format_currency_short(breakeven_abstand)} unter Breakeven (Prognose)"
        be_bg, be_fg = DANGER, colors.white
    be_para = Paragraph(f'<b>{be_text}</b>', ParagraphStyle('BE', parent=styles['Normal'], fontSize=10, textColor=be_fg, alignment=TA_CENTER, fontName='Helvetica-Bold'))
    be_table = Table([[be_para]], colWidths=[18*cm])
    be_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), be_bg),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(be_table)
    elements.append(Spacer(1, 4))

    # Bereichs-Übersicht Mockup: 9 Spalten (Bereich | Heute: Stück, Erlös, DB1, Marge | Monat: Stück, Erlös, DB1, Marge), keine Summenzeilen pro Bereich
    _aw_cache = {}
    datum_heute_str = datum_str or datetime.now().strftime('%d.%m.%Y')
    monat_name = (data.get('monat') or '').strip()  # z.B. "Februar 2026"
    # Header Zeile 1: Bereich | Heute (DD.MM.) colspan 4 | Monat (Name) colspan 4
    overview_header1 = [
        'Bereich',
        f'Heute ({datum_heute_str[:5]})', '', '', '',  # Platzhalter für colspan 4
        monat_name, '', '', ''  # colspan 4
    ]
    overview_header2 = ['', 'Stück', 'Erlös', 'DB1', 'Marge', 'Stück', 'Erlös', 'DB1', 'Marge']
    overview_data = [overview_header1, overview_header2]
    o_heute_stueck = o_heute_umsatz = o_heute_db1 = 0
    o_monat_stueck = o_monat_umsatz = o_monat_db1 = 0
    col_w = [3.2*cm] + [1.85*cm]*4 + [1.85*cm]*4  # 1 + 4 + 4

    for b in bereiche_sorted:
        bkey = b.get('bereich', '')
        cfg = KST_MAPPING.get(bkey, {'name': bkey, 'show_stueck': False})
        name_display = cfg['name']
        heute_u = b.get('heute_umsatz', 0)
        heute_d = b.get('heute_db1', 0)
        monat_u = b.get('umsatz', 0)
        monat_d = b.get('db1', 0)
        h_stueck = b.get('heute_stueck', 0) if cfg.get('show_stueck') else 0
        m_stueck = b.get('stueck', 0) if cfg.get('show_stueck') else 0
        if bkey in ['1-NW', '2-GW'] and (not h_stueck and not m_stueck):
            if bkey not in _aw_cache:
                _aw_cache[bkey] = get_tek_absatzwege_direct(
                    bkey, data.get('firma', '0'), data.get('standort_api', '0'),
                    monat_num, jahr_num, heute_datum
                )
            aw_list = _aw_cache[bkey].get('absatzwege', [])
            h_stueck = sum(aw.get('stueck_heute', 0) or 0 for aw in aw_list)
            m_stueck = sum(aw.get('stueck_monat', 0) or 0 for aw in aw_list)
        elif bkey in ['1-NW', '2-GW']:
            h_stueck = int(b.get('heute_stueck', 0) or 0)
            m_stueck = int(b.get('stueck', 0) or 0)
        h_marge = (heute_d / heute_u * 100) if heute_u > 0 else 0
        m_marge = (monat_d / monat_u * 100) if monat_u > 0 else 0
        overview_data.append([
            name_display,
            str(h_stueck) if cfg.get('show_stueck') else "—",
            format_currency_short(heute_u), format_currency_short(heute_d), format_percent(h_marge),
            str(m_stueck) if cfg.get('show_stueck') else "—",
            format_currency_short(monat_u), format_currency_short(monat_d), format_percent(m_marge)
        ])
        o_heute_stueck += h_stueck
        o_heute_umsatz += heute_u
        o_heute_db1 += heute_d
        o_monat_stueck += m_stueck
        o_monat_umsatz += monat_u
        o_monat_db1 += monat_d

    o_heute_marge = (o_heute_db1 / o_heute_umsatz * 100) if o_heute_umsatz > 0 else 0
    o_monat_marge = (o_monat_db1 / o_monat_umsatz * 100) if o_monat_umsatz > 0 else 0
    overview_data.append([
        'GESAMT',
        str(o_heute_stueck), format_currency_short(o_heute_umsatz), format_currency_short(o_heute_db1), format_percent(o_heute_marge),
        str(o_monat_stueck), format_currency_short(o_monat_umsatz), format_currency_short(o_monat_db1), format_percent(o_monat_marge)
    ])

    overview_table = Table(overview_data, colWidths=col_w, repeatRows=2)
    overview_table.setStyle(TableStyle([
        ('SPAN', (1, 0), (4, 0)), ('SPAN', (5, 0), (8, 0)),
        ('BACKGROUND', (0, 0), (-1, 1), DRIVE_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 1), colors.white),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (1, 0), (-1, 1), 'CENTER'), ('ALIGN', (1, 2), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('BACKGROUND', (1, 2), (4, -2), colors.HexColor('#f8f9fa')),
        ('BACKGROUND', (5, 2), (8, -2), colors.white),
        ('ROWBACKGROUNDS', (0, 2), (0, -2), [colors.white, colors.HexColor('#f8f9fa')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e7f1ff')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(Paragraph("Bereichs-Übersicht", section_style_page1))
    elements.append(overview_table)

    # Werkstatt-KPIs in Anfangsübersicht (Seite 1) – kompakt, eine Zeile
    werkstatt_bereich = next((b for b in data.get('bereiche', []) if b.get('bereich') == '4-Lohn' or b.get('id') == '4-Lohn'), None)
    if werkstatt_bereich and (werkstatt_bereich.get('produktivitaet') is not None or werkstatt_bereich.get('leistungsgrad') is not None):
        ws_kpi_row = []
        if werkstatt_bereich.get('produktivitaet') is not None:
            ws_kpi_row.append(f"Produktivität (EW): {werkstatt_bereich.get('produktivitaet')} %")
        if werkstatt_bereich.get('leistungsgrad') is not None:
            ws_kpi_row.append(f"Leistungsgrad: {werkstatt_bereich.get('leistungsgrad')} %")
        if ws_kpi_row:
            ws_overview_style = ParagraphStyle(
                'WerkstattKPI', parent=getSampleStyleSheet()['Normal'],
                fontSize=7, textColor=GRAY_DARK, spaceBefore=2, spaceAfter=0
            )
            elements.append(Spacer(1, 2))
            elements.append(Paragraph("<b>Werkstatt-KPIs</b> " + " · ".join(ws_kpi_row), ws_overview_style))

    elements.append(Spacer(1, 6))

    # === Mockup V2: Eine Seite pro KST (detaillierte Blöcke) ===
    gruppen_namen = {
        '81': 'Erlöse Neuwagen', '82': 'Erlöse Gebrauchtwagen', '83': 'Erlöse Teile', '84': 'Erlöse Lohn',
        '85': 'Erlöse Lack', '86': 'Sonstige Erlöse', '88': 'Erlöse Vermietung', '89': 'Sonstige betriebliche Erträge',
        '71': 'Einsatz Neuwagen', '72': 'Einsatz Gebrauchtwagen', '73': 'Einsatz Teile', '74': 'Einsatz Lohn',
        '75': 'Einsatz Lack', '76': 'Sonstiger Einsatz', '78': 'Einsatz Vermietung',
    }
    # Mockup: KST-Tabellenkopf #495057, weiße Schrift
    KST_HEADER_GRAY = colors.HexColor('#495057')
    detail_table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), KST_HEADER_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]

    for b in bereiche_sorted:
        bkey = b.get('bereich', '')
        cfg = KST_MAPPING.get(bkey, {'kst': '-', 'name': bkey, 'show_stueck': False})
        heute_umsatz = b.get('heute_umsatz', 0)
        heute_einsatz = b.get('heute_einsatz', 0) if 'heute_einsatz' in b else (heute_umsatz - b.get('heute_db1', 0))
        heute_db1 = b.get('heute_db1', 0)
        heute_stueck = b.get('heute_stueck', 0) if cfg.get('show_stueck') else 0
        monat_stueck = b.get('stueck', 0) if cfg.get('show_stueck') else 0
        # NW/GW: Stück aus E-Mail-Daten (API) nutzen; nur bei 0 Fallback auf Absatzwege-DB
        if bkey in ['1-NW', '2-GW'] and (not heute_stueck and not monat_stueck):
            if bkey not in _aw_cache:
                _aw_cache[bkey] = get_tek_absatzwege_direct(
                    bkey, data.get('firma', '0'), data.get('standort_api', '0'),
                    monat_num, jahr_num, heute_datum
                )
            aw_list = _aw_cache[bkey].get('absatzwege', [])
            heute_stueck = sum(aw.get('stueck_heute', 0) or 0 for aw in aw_list)
            monat_stueck = sum(aw.get('stueck_monat', 0) or 0 for aw in aw_list)
        elif bkey in ['1-NW', '2-GW']:
            heute_stueck = int(b.get('heute_stueck', 0) or 0)
            monat_stueck = int(b.get('stueck', 0) or 0)
        monat_umsatz = b.get('umsatz', 0)
        monat_einsatz = b.get('einsatz', 0)
        monat_db1 = b.get('db1', 0)
        heute_marge = (heute_db1 / heute_umsatz * 100) if heute_umsatz > 0 else 0
        monat_marge = (monat_db1 / monat_umsatz * 100) if monat_umsatz > 0 else 0
        heute_db_pro_stueck = (heute_db1 / heute_stueck) if (cfg.get('show_stueck') and heute_stueck > 0) else 0
        monat_db_pro_stueck = (monat_db1 / monat_stueck) if (cfg.get('show_stueck') and monat_stueck > 0) else 0

        elements.append(PageBreak())
        # Mockup: blauer Karten-Header (#0066cc, weiße Schrift)
        kst_header_para = Paragraph(
            f"<b>KST {cfg['kst']} – {cfg['name']} (detailliert)</b>",
            ParagraphStyle('KSTCard', parent=styles['Normal'], fontSize=11, textColor=colors.white, fontName='Helvetica-Bold')
        )
        kst_card_table = Table([[kst_header_para]], colWidths=[18*cm])
        kst_card_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DRIVE_BLUE),
            ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(kst_card_table)
        elements.append(Spacer(1, 4))

        # Tabellen-Header (kurz gegen Spaltenüberlauf): DB1 ber., DB1 %
        kst_header = [
            'Position',
            'Menge', 'Umsatzerlöse', 'Einsatzwerte', 'DB1 ber.', 'DB1 %',
            'Menge', 'Umsatzerlöse', 'Einsatzwerte', 'DB1 ber.', 'DB1 %'
        ]
        kst_data = [kst_header]
        # Erste Zeile = Hauptgruppe (z. B. 1 - Neuwagen), grau hinterlegt wie Global Cube
        kst_data.append([
            f"{cfg['kst']} - {cfg['name']}",
            str(heute_stueck) if cfg.get('show_stueck') else "—",
            format_currency_short(heute_umsatz), format_currency_short(heute_einsatz),
            format_currency_short(heute_db1), format_percent(heute_marge),
            str(monat_stueck) if cfg.get('show_stueck') else "—",
            format_currency_short(monat_umsatz), format_currency_short(monat_einsatz),
            format_currency_short(monat_db1), format_percent(monat_marge)
        ])
        kst_negative_cells = []  # (row_idx, col_idx) für rote Darstellung
        kst_subtotal_rows = []   # Zeilen-Indizes für Summenzeilen pro Absatzweg (fett)

        if bkey in ['1-NW', '2-GW', '3-Teile', '4-Lohn']:
            if bkey not in _aw_cache:
                if bkey in ['1-NW', '2-GW']:
                    _aw_cache[bkey] = get_tek_absatzwege_direct(
                        bkey, data.get('firma', '0'), data.get('standort_api', '0'),
                        monat_num, jahr_num, heute_datum
                    )
                else:
                    _aw_cache[bkey] = get_tek_bereich_konten_direct(
                        bkey, data.get('firma', '0'), data.get('standort_api', '0'),
                        monat_num, jahr_num, heute_datum
                    )
            absatzwege = _aw_cache.get(bkey, {}).get('absatzwege', [])
            for aw in absatzwege:
                aw_display = aw.get('absatzweg', '')
                if aw_display == 'Sonstige Sonstige':
                    aw_display = 'Sonstige Erlöse Neuwagen' if bkey == '1-NW' else 'Sonstige Erlöse Gebrauchtwagen'
                aw_sh = aw.get('stueck_heute', 0)
                aw_sm = aw.get('stueck_monat', 0)
                aw_uh = aw.get('umsatz_heute', 0)
                aw_eh = aw.get('einsatz_heute', 0)
                aw_dh = aw.get('db1_heute', 0)
                aw_mh = (aw_dh / aw_uh * 100) if aw_uh > 0 else 0
                aw_um = aw.get('umsatz_monat', 0)
                aw_em = aw.get('einsatz_monat', 0)
                aw_dm = aw.get('db1_monat', 0)
                aw_mm = (aw_dm / aw_um * 100) if aw_um > 0 else 0
                # Absatzweg als Kategorie (eingerückt)
                kst_data.append([
                    f"  {aw_display}",
                    str(aw_sh), format_currency_short(aw_uh), format_currency_short(aw_eh),
                    format_currency_short(aw_dh), format_percent(aw_mh),
                    str(aw_sm), format_currency_short(aw_um), format_currency_short(aw_em),
                    format_currency_short(aw_dm), format_percent(aw_mm)
                ])
                if aw_dh < 0:
                    kst_negative_cells.append((len(kst_data) - 1, 4))
                if aw_mh < 0:
                    kst_negative_cells.append((len(kst_data) - 1, 5))
                if aw_dm < 0:
                    kst_negative_cells.append((len(kst_data) - 1, 9))
                if aw_mm < 0:
                    kst_negative_cells.append((len(kst_data) - 1, 10))
                konten_list = aw.get('konten', [])
                if bkey in ['3-Teile', '4-Lohn']:
                    # Bereits gepaarte Zeilen (ein Eintrag = eine Zeile mit Erlös + Einsatz)
                    for k in konten_list:
                        ku = k.get('umsatz_heute', 0) or 0
                        ke = k.get('einsatz_heute', 0) or 0
                        ku_m = k.get('umsatz_monat', 0) or 0
                        ke_m = k.get('einsatz_monat', 0) or 0
                        kd_h = ku - ke
                        km_h = (kd_h / ku * 100) if ku > 0 else (0 if ke == 0 else 0)
                        kd_m = ku_m - ke_m
                        km_m = (kd_m / ku_m * 100) if ku_m > 0 else (0 if ke_m == 0 else 0)
                        bez = (k.get('bezeichnung') or '').strip()
                        if len(bez) > 42:
                            bez = bez[:39] + '...'
                        pos = f"    {k.get('konto', '')}: {bez}"
                        kst_data.append([
                            pos, '—',
                            format_currency_short(ku), format_currency_short(ke),
                            format_currency_short(kd_h), format_percent(km_h),
                            '—', format_currency_short(ku_m), format_currency_short(ke_m),
                            format_currency_short(kd_m), format_percent(km_m)
                        ])
                        if kd_h < 0:
                            kst_negative_cells.append((len(kst_data) - 1, 4))
                        if km_h < 0:
                            kst_negative_cells.append((len(kst_data) - 1, 5))
                        if kd_m < 0:
                            kst_negative_cells.append((len(kst_data) - 1, 9))
                        if km_m < 0:
                            kst_negative_cells.append((len(kst_data) - 1, 10))
                else:
                    # NW/GW: Erlöskonto (81/82) und Einsatzkonto (71/72) zu EINER Zeile paaren (gleiche letzte 4 Ziffern)
                    paired = {}
                    for k in konten_list:
                        kn = int(k.get('konto', 0) or 0)
                        key = kn % 10000
                        if key not in paired:
                            paired[key] = {'erlos': None, 'einsatz': None}
                        if (810000 <= kn <= 819999) or (820000 <= kn <= 829999):
                            paired[key]['erlos'] = k
                        elif (710000 <= kn <= 719999) or (720000 <= kn <= 729999):
                            paired[key]['einsatz'] = k
                    for pair_key in sorted(paired.keys()):
                        er = paired[pair_key]['erlos']
                        en = paired[pair_key]['einsatz']
                        ku = (er.get('umsatz_heute', 0) or 0) if er else 0
                        ke = (en.get('einsatz_heute', 0) or 0) if en else 0
                        ku_m = (er.get('umsatz_monat', 0) or 0) if er else 0
                        ke_m = (en.get('einsatz_monat', 0) or 0) if en else 0
                        ks_h = (er.get('stueck_heute', 0) or 0) if er else (en.get('stueck_heute', 0) or 0 if en else 0)
                        ks_m = (er.get('stueck_monat', 0) or 0) if er else (en.get('stueck_monat', 0) or 0 if en else 0)
                        kd_h = ku - ke
                        km_h = (kd_h / ku * 100) if ku > 0 else (0 if ke == 0 else 0)
                        kd_m = ku_m - ke_m
                        km_m = (kd_m / ku_m * 100) if ku_m > 0 else (0 if ke_m == 0 else 0)
                        bez = ((er.get('bezeichnung') or '') if er else (en.get('bezeichnung') or '')).strip()
                        if not bez and en:
                            bez = (en.get('bezeichnung') or '').strip()
                        if len(bez) > 42:
                            bez = bez[:39] + '...'
                        konto_display = (er.get('konto', '') if er else en.get('konto', ''))
                        pos = f"    {konto_display}: {bez}" if konto_display else f"    {bez}"
                        kst_data.append([
                            pos,
                            str(ks_h), format_currency_short(ku), format_currency_short(ke),
                            format_currency_short(kd_h), format_percent(km_h),
                            str(ks_m), format_currency_short(ku_m), format_currency_short(ke_m),
                            format_currency_short(kd_m), format_percent(km_m)
                        ])
                        if kd_h < 0:
                            kst_negative_cells.append((len(kst_data) - 1, 4))
                        if km_h < 0:
                            kst_negative_cells.append((len(kst_data) - 1, 5))
                        if kd_m < 0:
                            kst_negative_cells.append((len(kst_data) - 1, 9))
                        if km_m < 0:
                            kst_negative_cells.append((len(kst_data) - 1, 10))
                # Summenzeile pro Absatzweg (fett) wie Global Cube
                kst_data.append([
                    f"  {aw_display}",
                    str(aw_sh), format_currency_short(aw_uh), format_currency_short(aw_eh),
                    format_currency_short(aw_dh), format_percent(aw_mh),
                    str(aw_sm), format_currency_short(aw_um), format_currency_short(aw_em),
                    format_currency_short(aw_dm), format_percent(aw_mm)
                ])
                kst_subtotal_rows.append(len(kst_data) - 1)
        elif bkey == '5-Sonst':
            try:
                from datetime import timedelta
                _hd = datetime.strptime(heute_datum, '%Y-%m-%d')
                _bis_heute = (_hd + timedelta(days=1)).strftime('%Y-%m-%d')
                _von_monat = f"{jahr_num}-{monat_num:02d}-01"
                _bis_monat = f"{jahr_num}-{monat_num+1:02d}-01" if monat_num < 12 else f"{jahr_num+1}-01-01"
                _cp = get_tek_cleanpark_direct(
                    data.get('firma', '0'), data.get('standort_api', '0'),
                    heute_datum, _bis_heute, _von_monat, _bis_monat
                )
                _cp_dh = _cp['heute_umsatz'] - _cp['heute_einsatz']
                _cp_dm = _cp['monat_umsatz'] - _cp['monat_einsatz']
                _cp_mh = (_cp_dh / _cp['heute_umsatz'] * 100) if _cp['heute_umsatz'] > 0 else 0
                _cp_mm = (_cp_dm / _cp['monat_umsatz'] * 100) if _cp['monat_umsatz'] > 0 else 0
                kst_data.append([
                    'Clean Park (847301 / 747301)', '—',
                    format_currency_short(_cp['heute_umsatz']), format_currency_short(_cp['heute_einsatz']),
                    format_currency_short(_cp_dh), format_percent(_cp_mh),
                    '—', format_currency_short(_cp['monat_umsatz']), format_currency_short(_cp['monat_einsatz']),
                    format_currency_short(_cp_dm), format_percent(_cp_mm)
                ])
            except Exception:
                pass

        # Spaltenbreiten: mehr Platz nutzen (Querformat ~28,7 cm), keine Überläufe
        colw_kst = [7.2*cm, 0.95*cm, 2.05*cm, 2.05*cm, 1.6*cm, 1.2*cm, 0.95*cm, 2.05*cm, 2.05*cm, 1.6*cm, 1.2*cm]
        kst_table = Table(kst_data, colWidths=colw_kst, repeatRows=1)
        kst_style = list(detail_table_style)
        # Header wie Global Cube: hellgrauer Hintergrund
        kst_style.append(('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')))
        kst_style.append(('TEXTCOLOR', (0, 0), (-1, 0), GRAY_DARK))
        # Hauptgruppe (Zeile 1): hellgrauer Hintergrund + fett wie Global Cube
        kst_style.append(('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e9ecef')))
        kst_style.append(('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'))
        kst_style.append(('FONTSIZE', (0, 1), (-1, 1), 8))
        # Summenzeilen pro Absatzweg: fett
        for row_idx in kst_subtotal_rows:
            kst_style.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
            kst_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#f8f9fa')))
        # Negative Werte (DB 1 ber., DB 1 in %) in rot
        for (row_idx, col_idx) in kst_negative_cells:
            kst_style.append(('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), DANGER))
        kst_table.setStyle(TableStyle(kst_style))
        elements.append(kst_table)
        if bkey == '4-Lohn':
            # Werkstatt-KPI-Block wie Mockup V2: Produktivität und Leistungsgrad klar sichtbar
            ws_kpi_rows = []
            if b.get('produktivitaet') is not None:
                ws_kpi_rows.append(['Produktivität (EW):', f"{b.get('produktivitaet')} %"])
            if b.get('leistungsgrad') is not None:
                ws_kpi_rows.append(['Leistungsgrad:', f"{b.get('leistungsgrad')} %"])
            if ws_kpi_rows:
                ws_kpi_table = Table(ws_kpi_rows, colWidths=[4*cm, 3*cm])
                ws_kpi_table.setStyle(TableStyle([
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('TEXTCOLOR', (0, 0), (-1, -1), GRAY_DARK),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                    ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(Spacer(1, 6))
                elements.append(ws_kpi_table)
            if b.get('hinweis'):
                hint_style = ParagraphStyle(
                    'WerkstattHint', parent=getSampleStyleSheet()['Normal'],
                    fontSize=8, textColor=GRAY, spaceBefore=6, spaceAfter=0
                )
                elements.append(Paragraph("<b>Hinweis:</b> " + str(b.get('hinweis')), hint_style))
        elements.append(Spacer(1, 8))

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
        '5-Sonst': 'Mietwagen'
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

    # === HAUPT-KPIs (groß) – ohne Status „Ziel erreicht“ (fachlich nicht sinnvoll) ===
    marge = bereich_data.get('marge', 0)

    kpi_data = [
        ['DB1', 'Marge'],
        [
            format_currency_short(bereich_data.get('db1', 0)),
            format_percent(marge),
        ]
    ]

    kpi_table = Table(kpi_data, colWidths=[8*cm, 8*cm])
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
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 15))

    # === DETAIL-ZAHLEN ===
    elements.append(Paragraph("Details", section_style))

    detail_data = [
        ['Kennzahl', 'Wert'],
        ['Erlös (Monat)', format_currency_short(bereich_data.get('umsatz', 0))],
        ['Einsatz (Monat)', format_currency_short(bereich_data.get('einsatz', 0))],
        ['DB1 (Monat)', format_currency_short(bereich_data.get('db1', 0))],
        ['Marge', format_percent(marge)],
    ]
    # Heute-Zahlen wenn vorhanden (wie TEK Gesamt)
    if bereich_data.get('heute_umsatz') is not None or bereich_data.get('heute_db1') is not None:
        detail_data.append(['Erlös (Heute)', format_currency_short(bereich_data.get('heute_umsatz', 0))])
        detail_data.append(['DB1 (Heute)', format_currency_short(bereich_data.get('heute_db1', 0))])
    # Werkstatt-spezifisch: Hinweis kalk. Einsatz, Produktivität, Leistungsgrad
    if bereich_key == '4-Lohn':
        if bereich_data.get('hinweis'):
            detail_data.append(['Hinweis', bereich_data.get('hinweis', '')])
        if bereich_data.get('produktivitaet') is not None:
            detail_data.append(['Produktivität (EW)', f"{bereich_data.get('produktivitaet')} %"])
        if bereich_data.get('leistungsgrad') is not None:
            detail_data.append(['Leistungsgrad', f"{bereich_data.get('leistungsgrad')} %"])

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

    # === KST Verkauf (gleiche Detaillierung wie TEK Gesamt: Heute | Monat, Absatzwege, Konten) ===
    _datum_str = data.get('datum', '')
    _heute_datum = None
    if _datum_str:
        try:
            _heute_datum = datetime.strptime(_datum_str, '%d.%m.%Y').strftime('%Y-%m-%d')
        except Exception:
            pass
    if not _heute_datum:
        _heute_datum = date.today().strftime('%Y-%m-%d')
    _monat_num = data.get('monat_num')
    _jahr_num = data.get('jahr_num')
    if not _monat_num or not _jahr_num:
        _monat_num = _monat_num or date.today().month
        _jahr_num = _jahr_num or date.today().year
    _firma_api = data.get('firma', '0')
    _standort_api = data.get('standort_api', '0')

    _kst_header = ['', '', 'Heute', '', '', '', '', '', 'Monat kumuliert', '', '', '', '', '']
    _kst_sub = ['KST', 'Bereich/Absatzweg', 'Menge', 'Umsatzerlöse', 'Einsatzwerte', 'DB 1 ber.', 'DB/Stück', 'DB1 %', 'Menge', 'Umsatzerlöse', 'Einsatzwerte', 'DB 1 ber.', 'DB/Stück', 'DB1 %']
    _sub_style = ParagraphStyle('TEKVerkaufSub', parent=styles['Normal'], fontSize=7, alignment=TA_CENTER, wordWrap='CJK')
    _kst_subheader = [Paragraph(t, _sub_style) for t in _kst_sub]
    kst_verkauf_data = [_kst_header, _kst_subheader]

    _g_heute_stueck = _g_heute_umsatz = _g_heute_einsatz = _g_heute_db1 = 0
    _g_monat_stueck = _g_monat_umsatz = _g_monat_einsatz = _g_monat_db1 = 0

    for _bkey, _b, _kst_num, _name in [
        ('1-NW', nw, '1', 'Neuwagen'),
        ('2-GW', gw, '2', 'Gebrauchtwagen'),
    ]:
        if not _b:
            continue
        _heute_umsatz = _b.get('heute_umsatz', 0)
        _heute_einsatz = _b.get('heute_einsatz', 0)
        _heute_db1 = _b.get('heute_db1', 0)
        _monat_umsatz = _b.get('umsatz', 0)
        _monat_einsatz = _b.get('einsatz', 0)
        _monat_db1 = _b.get('db1', 0)
        _heute_marge = (_heute_db1 / _heute_umsatz * 100) if _heute_umsatz > 0 else 0
        _monat_marge = (_monat_db1 / _monat_umsatz * 100) if _monat_umsatz > 0 else 0

        _aw_data = get_tek_absatzwege_direct(_bkey, _firma_api, _standort_api, _monat_num, _jahr_num, _heute_datum)
        _absatzwege = _aw_data.get('absatzwege', [])
        _sum_stueck_heute = sum(aw.get('stueck_heute', 0) or 0 for aw in _absatzwege)
        _sum_stueck_monat = sum(aw.get('stueck_monat', 0) or 0 for aw in _absatzwege)
        _heute_stueck = _sum_stueck_heute
        _monat_stueck = _sum_stueck_monat
        _heute_db_stk = (_heute_db1 / _heute_stueck) if _heute_stueck > 0 else 0
        _monat_db_stk = (_monat_db1 / _monat_stueck) if _monat_stueck > 0 else 0

        kst_verkauf_data.append([
            _kst_num, _name,
            str(_heute_stueck), format_currency_short(_heute_umsatz), format_currency_short(_heute_einsatz),
            format_currency_short(_heute_db1), format_currency_short(_heute_db_stk), format_percent(_heute_marge),
            str(_monat_stueck), format_currency_short(_monat_umsatz), format_currency_short(_monat_einsatz),
            format_currency_short(_monat_db1), format_currency_short(_monat_db_stk), format_percent(_monat_marge)
        ])

        for aw in _absatzwege:
            _aw_display = aw.get('absatzweg', '')
            if _aw_display == 'Sonstige Sonstige':
                _aw_display = 'Sonstige Erlöse Neuwagen' if _bkey == '1-NW' else 'Sonstige Erlöse Gebrauchtwagen'
            _aw_sh = aw.get('stueck_heute', 0)
            _aw_uh = aw.get('umsatz_heute', 0)
            _aw_eh = aw.get('einsatz_heute', 0)
            _aw_dh = aw.get('db1_heute', 0)
            _aw_mh = (_aw_dh / _aw_uh * 100) if _aw_uh > 0 else 0
            _aw_sm = aw.get('stueck_monat', 0)
            _aw_um = aw.get('umsatz_monat', 0)
            _aw_em = aw.get('einsatz_monat', 0)
            _aw_dm = aw.get('db1_monat', 0)
            _aw_mm = (_aw_dm / _aw_um * 100) if _aw_um > 0 else 0
            _aw_ds_h = (_aw_dh / _aw_sh) if _aw_sh > 0 else 0
            _aw_ds_m = (_aw_dm / _aw_sm) if _aw_sm > 0 else 0
            kst_verkauf_data.append([
                '', f"  {_aw_display}",
                str(_aw_sh), format_currency_short(_aw_uh), format_currency_short(_aw_eh),
                format_currency_short(_aw_dh), format_currency_short(_aw_ds_h), format_percent(_aw_mh),
                str(_aw_sm), format_currency_short(_aw_um), format_currency_short(_aw_em),
                format_currency_short(_aw_dm), format_currency_short(_aw_ds_m), format_percent(_aw_mm)
            ])
            for k in aw.get('konten', []):
                _ku = k.get('umsatz_heute', 0)
                _ke = k.get('einsatz_heute', 0)
                _kd = _ku - _ke
                _km = (_kd / _ku * 100) if _ku > 0 else 0
                _kum = k.get('umsatz_monat', 0)
                _kem = k.get('einsatz_monat', 0)
                _kdm = _kum - _kem
                _kmm = (_kdm / _kum * 100) if _kum > 0 else 0
                _ksh = k.get('stueck_heute', 0)
                _ksm = k.get('stueck_monat', 0)
                _kds_h = (_kd / _ksh) if _ksh > 0 else 0
                _kds_m = (_kdm / _ksm) if _ksm > 0 else 0
                _bez = (k.get('bezeichnung') or f"Konto {k.get('konto', '')}")
                if len(_bez) > 70:
                    _bez = _bez[:67] + "..."
                kst_verkauf_data.append([
                    '', f"    {k.get('konto', '')}: {_bez}",
                    "-", format_currency_short(_ku), format_currency_short(_ke), format_currency_short(_kd),
                    format_currency_short(_kds_h) if _ksh > 0 else "-", format_percent(_km),
                    "-", format_currency_short(_kum), format_currency_short(_kem), format_currency_short(_kdm),
                    format_currency_short(_kds_m) if _ksm > 0 else "-", format_percent(_kmm)
                ])

        _sum_db_stk_h = (_heute_db1 / _sum_stueck_heute) if _sum_stueck_heute > 0 else 0
        _sum_db_stk_m = (_monat_db1 / _sum_stueck_monat) if _sum_stueck_monat > 0 else 0
        kst_verkauf_data.append([
            _kst_num, f"Summe {_name}",
            str(_sum_stueck_heute), format_currency_short(_heute_umsatz), format_currency_short(_heute_einsatz),
            format_currency_short(_heute_db1), format_currency_short(_sum_db_stk_h) if _sum_stueck_heute > 0 else "-", format_percent(_heute_marge),
            str(_sum_stueck_monat), format_currency_short(_monat_umsatz), format_currency_short(_monat_einsatz),
            format_currency_short(_monat_db1), format_currency_short(_sum_db_stk_m) if _sum_stueck_monat > 0 else "-", format_percent(_monat_marge)
        ])
        _g_heute_stueck += _sum_stueck_heute
        _g_heute_umsatz += _heute_umsatz
        _g_heute_einsatz += _heute_einsatz
        _g_heute_db1 += _heute_db1
        _g_monat_stueck += _sum_stueck_monat
        _g_monat_umsatz += _monat_umsatz
        _g_monat_einsatz += _monat_einsatz
        _g_monat_db1 += _monat_db1

    _g_heute_marge = (_g_heute_db1 / _g_heute_umsatz * 100) if _g_heute_umsatz > 0 else 0
    _g_monat_marge = (_g_monat_db1 / _g_monat_umsatz * 100) if _g_monat_umsatz > 0 else 0
    _g_db_stk_h = (_g_heute_db1 / _g_heute_stueck) if _g_heute_stueck > 0 else 0
    _g_db_stk_m = (_g_monat_db1 / _g_monat_stueck) if _g_monat_stueck > 0 else 0
    kst_verkauf_data.append([
        '', 'GESAMT',
        str(_g_heute_stueck), format_currency_short(_g_heute_umsatz), format_currency_short(_g_heute_einsatz),
        format_currency_short(_g_heute_db1), format_currency_short(_g_db_stk_h), format_percent(_g_heute_marge),
        str(_g_monat_stueck), format_currency_short(_g_monat_umsatz), format_currency_short(_g_monat_einsatz),
        format_currency_short(_g_monat_db1), format_currency_short(_g_db_stk_m), format_percent(_g_monat_marge)
    ])

    _col_w = [0.55*cm, 3.2*cm, 0.7*cm, 1.35*cm, 1.35*cm, 1.2*cm, 1.0*cm, 1.0*cm, 0.7*cm, 1.35*cm, 1.35*cm, 1.2*cm, 1.0*cm, 1.0*cm]
    _kst_table = Table(kst_verkauf_data, colWidths=_col_w)
    _kst_style = [
        ('SPAN', (2, 0), (7, 0)), ('SPAN', (8, 0), (13, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, 1), GRAY_DARK), ('TEXTCOLOR', (0, 1), (-1, 1), colors.white),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'), ('FONTSIZE', (0, 1), (-1, 1), 7),
        ('FONTSIZE', (0, 2), (-1, -2), 6), ('ALIGN', (0, 2), (0, -2), 'CENTER'), ('ALIGN', (1, 2), (1, -2), 'LEFT'), ('ALIGN', (2, 2), (-1, -2), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4), ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#ddd')),
        ('ROWBACKGROUNDS', (0, 2), (-1, -2), [colors.white, GRAY_LIGHT]),
        ('BACKGROUND', (0, -1), (-1, -1), GRAY_DARK), ('TEXTCOLOR', (0, -1), (-1, -1), colors.white), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'), ('FONTSIZE', (0, -1), (-1, -1), 8),
    ]
    for _ri in range(2, len(kst_verkauf_data) - 1):
        if len(kst_verkauf_data[_ri]) > 1 and isinstance(kst_verkauf_data[_ri][1], str) and 'Summe' in kst_verkauf_data[_ri][1]:
            _kst_style.append(('BACKGROUND', (0, _ri), (-1, _ri), colors.HexColor('#e8f4f8')))
            _kst_style.append(('FONTNAME', (0, _ri), (-1, _ri), 'Helvetica-Bold'))
    _kst_table.setStyle(TableStyle(_kst_style))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("KST Verkauf (Heute / Monat kumuliert)", section_style))
    elements.append(_kst_table)
    elements.append(Spacer(1, 18))

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
        # TAG 219: Einsatz/DB1/Marge ggf. kalkulatorisch (laufender Monat) – Werte kommen so aus API/controlling_data
        w_umsatz = werkstatt.get('umsatz', 0)
        w_einsatz = werkstatt.get('einsatz_kalk') or werkstatt.get('einsatz', 0)
        w_db1 = werkstatt.get('db1_kalk') if 'db1_kalk' in werkstatt else werkstatt.get('db1', 0)
        w_marge = werkstatt.get('marge_kalk') if 'marge_kalk' in werkstatt else werkstatt.get('marge', 0)
        detail_data.append([
            'Werkstatt',
            format_currency_short(w_umsatz),
            format_currency_short(w_einsatz),
            format_currency_short(w_db1),
            format_percent(w_marge)
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

    # === WERKSTATT-DETAILS (TAG 219: kalk. Einsatz, KPIs wenn vorhanden) ===
    if werkstatt:
        ws_details = []
        if werkstatt.get('hinweis'):
            ws_details.append(werkstatt.get('hinweis'))
        if werkstatt.get('produktivitaet') is not None:
            ws_details.append(f"Produktivität (EW): {werkstatt.get('produktivitaet')} %")
        if werkstatt.get('leistungsgrad') is not None:
            ws_details.append(f"Leistungsgrad: {werkstatt.get('leistungsgrad')} %")
        if ws_details:
            hint_style = ParagraphStyle(
                'WerkstattHint',
                parent=styles['Normal'],
                fontSize=8,
                textColor=GRAY,
                leftIndent=0,
                spaceBefore=6,
                spaceAfter=0
            )
            elements.append(Paragraph(
                "Werkstatt: " + " | ".join(ws_details),
                hint_style
            ))
            elements.append(Spacer(1, 10))

    # === KST Service (Heute / Monat kumuliert, mit Gruppen wie TEK Gesamt) ===
    _d_str = data.get('datum', '')
    _heute_d = datetime.strptime(_d_str, '%d.%m.%Y').strftime('%Y-%m-%d') if _d_str and '.' in _d_str else date.today().strftime('%Y-%m-%d')
    _mon = data.get('monat_num') or date.today().month
    _jahr = data.get('jahr_num') or date.today().year
    _firma = data.get('firma', '0')
    _standort = data.get('standort_api', '0')

    _gruppen_namen = {
        '81': 'Erlöse Neuwagen', '82': 'Erlöse Gebrauchtwagen',
        '83': 'Erlöse Teile', '84': 'Erlöse Lohn',
        '85': 'Erlöse Lack', '86': 'Sonstige Erlöse', '88': 'Erlöse Vermietung', '89': 'Sonstige betriebliche Erträge',
        '71': 'Einsatz Neuwagen', '72': 'Einsatz Gebrauchtwagen',
        '73': 'Einsatz Teile', '74': 'Einsatz Lohn',
        '75': 'Einsatz Lack', '76': 'Sonstiger Einsatz', '78': 'Einsatz Vermietung',
    }

    _sh = ['', '', 'Heute', '', '', '', '', '', 'Monat kumuliert', '', '', '', '', '']
    _sl = ['KST', 'Bereich/Gruppe', 'Menge', 'Umsatzerlöse', 'Einsatzwerte', 'DB 1 ber.', 'DB/Stück', 'DB1 %', 'Menge', 'Umsatzerlöse', 'Einsatzwerte', 'DB 1 ber.', 'DB/Stück', 'DB1 %']
    _sub_para = ParagraphStyle('TEKServiceSub', parent=styles['Normal'], fontSize=7, alignment=TA_CENTER, wordWrap='CJK')
    kst_svc_data = [_sh, [Paragraph(t, _sub_para) for t in _sl]]

    _gs_h_u = _gs_h_e = _gs_h_d = _gs_m_u = _gs_m_e = _gs_m_d = 0

    for _bkey, _b, _kst, _name in [
        ('3-Teile', teile, '6', 'Teile & Zubehör'),
        ('4-Lohn', werkstatt, '3', 'Service/Werkstatt'),
    ]:
        if not _b:
            continue
        _hu = _b.get('heute_umsatz', 0)
        _he = _b.get('heute_einsatz', 0)
        _hd = _b.get('heute_db1', 0)
        _mu = _b.get('umsatz', 0)
        _me = _b.get('einsatz', 0)
        _md = _b.get('db1', 0)
        _hm = (_hd / _hu * 100) if _hu > 0 else 0
        _mm = (_md / _mu * 100) if _mu > 0 else 0

        kst_svc_data.append([
            _kst, _name,
            "-", format_currency_short(_hu), format_currency_short(_he), format_currency_short(_hd), "-", format_percent(_hm),
            "-", format_currency_short(_mu), format_currency_short(_me), format_currency_short(_md), "-", format_percent(_mm)
        ])

        _detail = get_tek_detail_data_direct(_bkey, _firma, _standort, _mon, _jahr, _heute_d)
        _um = {g['gruppe']: g['betrag'] for g in _detail.get('monat', {}).get('umsatz_gruppen', [])}
        _em = {g['gruppe']: g['betrag'] for g in _detail.get('monat', {}).get('einsatz_gruppen', [])}
        _uh = {g['gruppe']: g['betrag'] for g in _detail.get('heute', {}).get('umsatz_gruppen', [])}
        _eh = {g['gruppe']: g['betrag'] for g in _detail.get('heute', {}).get('einsatz_gruppen', [])}
        _all_gr = sorted(set(list(_um.keys()) + list(_em.keys())))

        for _gr in _all_gr:
            _u_m = _um.get(_gr, 0)
            _e_m = _em.get(_gr, 0)
            _d_m = _u_m - _e_m
            _m_m = (_d_m / _u_m * 100) if _u_m > 0 else 0
            _u_h = _uh.get(_gr, 0)
            _e_h = _eh.get(_gr, 0)
            _d_h = _u_h - _e_h
            _m_h = (_d_h / _u_h * 100) if _u_h > 0 else 0
            _label = _gruppen_namen.get(_gr, f'Gruppe {_gr}')
            kst_svc_data.append([
                '', f"  {_label}",
                "-", format_currency_short(_u_h), format_currency_short(_e_h), format_currency_short(_d_h), "-", format_percent(_m_h),
                "-", format_currency_short(_u_m), format_currency_short(_e_m), format_currency_short(_d_m), "-", format_percent(_m_m)
            ])

        kst_svc_data.append([
            _kst, f"Summe {_name}",
            "-", format_currency_short(_hu), format_currency_short(_he), format_currency_short(_hd), "-", format_percent(_hm),
            "-", format_currency_short(_mu), format_currency_short(_me), format_currency_short(_md), "-", format_percent(_mm)
        ])
        _gs_h_u += _hu
        _gs_h_e += _he
        _gs_h_d += _hd
        _gs_m_u += _mu
        _gs_m_e += _me
        _gs_m_d += _md

    _gs_hm = (_gs_h_d / _gs_h_u * 100) if _gs_h_u > 0 else 0
    _gs_mm = (_gs_m_d / _gs_m_u * 100) if _gs_m_u > 0 else 0
    kst_svc_data.append([
        '', 'GESAMT',
        "-", format_currency_short(_gs_h_u), format_currency_short(_gs_h_e), format_currency_short(_gs_h_d), "-", format_percent(_gs_hm),
        "-", format_currency_short(_gs_m_u), format_currency_short(_gs_m_e), format_currency_short(_gs_m_d), "-", format_percent(_gs_mm)
    ])

    _cw = [0.55*cm, 3.2*cm, 0.7*cm, 1.35*cm, 1.35*cm, 1.2*cm, 1.0*cm, 1.0*cm, 0.7*cm, 1.35*cm, 1.35*cm, 1.2*cm, 1.0*cm, 1.0*cm]
    _tbl = Table(kst_svc_data, colWidths=_cw)
    _sty = [
        ('SPAN', (2, 0), (7, 0)), ('SPAN', (8, 0), (13, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), DRIVE_BLUE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, 1), GRAY_DARK), ('TEXTCOLOR', (0, 1), (-1, 1), colors.white),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'), ('FONTSIZE', (0, 1), (-1, 1), 7),
        ('FONTSIZE', (0, 2), (-1, -2), 6), ('ALIGN', (0, 2), (0, -2), 'CENTER'), ('ALIGN', (1, 2), (1, -2), 'LEFT'), ('ALIGN', (2, 2), (-1, -2), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4), ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#ddd')),
        ('ROWBACKGROUNDS', (0, 2), (-1, -2), [colors.white, GRAY_LIGHT]),
        ('BACKGROUND', (0, -1), (-1, -1), GRAY_DARK), ('TEXTCOLOR', (0, -1), (-1, -1), colors.white), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'), ('FONTSIZE', (0, -1), (-1, -1), 8),
    ]
    for _ri in range(2, len(kst_svc_data) - 1):
        if len(kst_svc_data[_ri]) > 1 and isinstance(kst_svc_data[_ri][1], str) and 'Summe' in kst_svc_data[_ri][1]:
            _sty.append(('BACKGROUND', (0, _ri), (-1, _ri), colors.HexColor('#e8f4f8')))
            _sty.append(('FONTNAME', (0, _ri), (-1, _ri), 'Helvetica-Bold'))
    _tbl.setStyle(TableStyle(_sty))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("KST Service (Heute / Monat kumuliert)", section_style))
    elements.append(_tbl)
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
        f"TEK Service{standort_suffix} - Automatisch generiert von DRIVE",
        footer_style
    ))

    doc.build(elements)
    return buffer.getvalue()
