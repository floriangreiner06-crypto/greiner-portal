"""
Provisions-PDF: Vorlauf und Endlauf (Provisionsabrechnung pro Verkäufer/Monat).
Seite 1: Deckblatt (Zusammenfassung aller Kategorien).
Seite 2+: Detail-Positionen pro Kategorie inkl. Zusatzleistungen.
"""
import os
from datetime import datetime
from io import BytesIO
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from api.db_utils import db_session, rows_to_list

# Farben (konsistent mit Portal-Design)
NAVY = colors.HexColor('#1e3a5f')
BLUE = colors.HexColor('#2563eb')
LIGHT_BG = colors.HexColor('#f8fafc')
ZEBRA_EVEN = colors.HexColor('#f1f5f9')
HEADER_BG = colors.HexColor('#e2e8f0')
KAT_BG = colors.HexColor('#1e293b')
KAT_TEXT = colors.white
BORDER_COLOR = colors.HexColor('#cbd5e1')

MONAT_NAMEN = [
    'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
    'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
]


def _fmt_eur(value) -> str:
    try:
        return f"{float(value):,.2f} \u20ac".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "0,00 \u20ac"


def _monat_label(monat: str) -> str:
    if len(monat) == 7 and monat[4] == '-':
        try:
            m = int(monat[5:7])
            return f"{MONAT_NAMEN[m - 1]} {monat[:4]}"
        except (ValueError, IndexError):
            pass
    return monat


def _lauf_daten(lauf_id: int) -> Optional[dict]:
    """Liest Lauf + Positionen + Zusatzleistungen aus DB."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, verkaufer_id, verkaufer_name, abrechnungsmonat, status,
                   summe_kat_i, summe_kat_ii, summe_kat_iii, summe_kat_iv, summe_kat_v,
                   summe_stueckpraemie, summe_gesamt, belegnummer, endlauf_am
            FROM provision_laeufe WHERE id = %s
        """, (lauf_id,))
        lauf = cur.fetchone()
        if not lauf:
            return None
        cur.execute("""
            SELECT kategorie, vin, modell, kaeufer_name, einkaeufer_name,
                   rg_netto, deckungsbeitrag, bemessungsgrundlage, provisionssatz,
                   provision_berechnet, provision_final, rg_datum, locosoft_rg_nr
            FROM provision_positionen WHERE lauf_id = %s
            ORDER BY CASE kategorie
                WHEN 'I_neuwagen' THEN 1 WHEN 'II_testwagen' THEN 2
                WHEN 'III_gebrauchtwagen' THEN 3 WHEN 'IV_gw_bestand' THEN 4 ELSE 5 END,
                rg_datum DESC NULLS LAST
        """, (lauf_id,))
        positionen = rows_to_list(cur.fetchall())
        cur.execute("""
            SELECT bezeichnung, beleg_referenz, beleg_datum, provision_verkaufer
            FROM provision_zusatzleistungen WHERE lauf_id = %s
            ORDER BY beleg_datum DESC NULLS LAST
        """, (lauf_id,))
        zusatzleistungen = rows_to_list(cur.fetchall())

        # Jahresuebersicht: alle Laeufe desselben Verkaefers im selben Jahr
        vkb = lauf['verkaufer_id']
        monat = lauf['abrechnungsmonat'] or ''
        jahr = monat[:4] if len(monat) >= 4 else str(datetime.now().year)
        cur.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN pp.kategorie = 'I_neuwagen' THEN 1 ELSE 0 END), 0) AS stueck_nw,
                COALESCE(SUM(CASE WHEN pp.kategorie = 'II_testwagen' THEN 1 ELSE 0 END), 0) AS stueck_tw,
                COALESCE(SUM(CASE WHEN pp.kategorie = 'III_gebrauchtwagen' THEN 1 ELSE 0 END), 0) AS stueck_gw
            FROM provision_positionen pp
            JOIN provision_laeufe pl ON pp.lauf_id = pl.id
            WHERE pl.verkaufer_id = %s AND pl.abrechnungsmonat LIKE %s
        """, (vkb, f'{jahr}-%'))
        row_j = cur.fetchone()
        cur.execute("""
            SELECT COALESCE(SUM(summe_gesamt), 0) AS provision_jahr
            FROM provision_laeufe
            WHERE verkaufer_id = %s AND abrechnungsmonat LIKE %s
        """, (vkb, f'{jahr}-%'))
        row_p = cur.fetchone()
        jahresuebersicht = {
            'jahr': jahr,
            'stueck_nw': int(row_j['stueck_nw']) if row_j else 0,
            'stueck_tw': int(row_j['stueck_tw']) if row_j else 0,
            'stueck_gw': int(row_j['stueck_gw']) if row_j else 0,
            'provision_jahr': float(row_p['provision_jahr']) if row_p else 0,
        }
    return {'lauf': dict(lauf), 'positionen': positionen, 'zusatzleistungen': zusatzleistungen, 'jahresuebersicht': jahresuebersicht}


# =============================================================================
# Seite 1: Deckblatt (Zusammenfassung)
# =============================================================================

def _build_deckblatt(elements, lauf, positionen, zusatzleistungen, styles):
    vk_name = lauf.get('verkaufer_name') or '-'
    monat_label = _monat_label(lauf.get('abrechnungsmonat') or '')
    belegnummer = lauf.get('belegnummer') or ''

    # --- Titel ---
    title_style = ParagraphStyle('DeckTitle', fontName='Helvetica-Bold',
                                 fontSize=18, spaceAfter=4, textColor=NAVY, leading=22)
    elements.append(Paragraph('Provisionsabrechnung', title_style))
    elements.append(Spacer(1, 0.2 * cm))

    # --- Name / Monat / Belegnummer ---
    info_style = ParagraphStyle('DeckInfo', fontName='Helvetica', fontSize=10, leading=13)
    info_bold = ParagraphStyle('DeckInfoB', fontName='Helvetica-Bold', fontSize=10, leading=13)
    info_data = [
        [Paragraph('<b>Name:</b>', info_bold), Paragraph(vk_name, info_style),
         Paragraph('<b>Monat/Jahr:</b>', info_bold), Paragraph(monat_label, info_style)],
    ]
    if belegnummer:
        info_data.append([
            Paragraph('<b>Belegnummer:</b>', info_bold),
            Paragraph(f'<font color="#2563eb"><b>{belegnummer}</b></font>', info_style), '', ''])

    info_t = Table(info_data, colWidths=[3 * cm, 5.5 * cm, 3 * cm, 5 * cm])
    info_t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, 0), 1, BORDER_COLOR),
    ]))
    elements.append(info_t)
    elements.append(Spacer(1, 0.6 * cm))

    # --- Shared Styles (alle Helvetica) ---
    cell = ParagraphStyle('DC', fontName='Helvetica', fontSize=9, leading=11)
    cell_b = ParagraphStyle('DCB', fontName='Helvetica-Bold', fontSize=9, leading=11)
    cell_r = ParagraphStyle('DCR', fontName='Helvetica', fontSize=9, leading=11, alignment=TA_RIGHT)
    cell_rb = ParagraphStyle('DCRB', fontName='Helvetica-Bold', fontSize=9, leading=11, alignment=TA_RIGHT)

    by_kat = {}
    for p in positionen:
        by_kat.setdefault(p.get('kategorie') or '', []).append(p)

    def kat_row(title, stueck, bezeichnung, provision):
        """Eine Kategorie-Zeile fuer das Deckblatt."""
        data = [
            # Header
            [Paragraph(f'<b>{title}</b>', ParagraphStyle('KH', parent=cell_b, textColor=KAT_TEXT, fontSize=9)),
             '', ''],
            # Spalten-Header
            [Paragraph('<b>Stück</b>', cell_b),
             Paragraph('<b>Bezeichnung</b>', cell_b),
             Paragraph('<b>Provision</b>', cell_rb)],
            # Daten
            [Paragraph(str(stueck), cell),
             Paragraph(bezeichnung, cell),
             Paragraph(_fmt_eur(provision), cell_r)],
            # Summe
            [Paragraph('', cell), Paragraph('', cell),
             Paragraph(f'<b>{_fmt_eur(provision)}</b>', cell_rb)],
        ]
        t = Table(data, colWidths=[2.5 * cm, 9 * cm, 5 * cm])
        t.setStyle(TableStyle([
            ('SPAN', (0, 0), (-1, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), KAT_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), KAT_TEXT),
            ('BACKGROUND', (0, 1), (-1, 1), HEADER_BG),
            ('BACKGROUND', (0, 3), (-1, 3), LIGHT_BG),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('INNERGRID', (0, 1), (-1, -1), 0.25, BORDER_COLOR),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        return t

    totals = []

    # I. Neuwagen
    nw = by_kat.get('I_neuwagen', [])
    nw_prov = sum(float(p.get('provision_final') or 0) for p in nw)
    elements.append(kat_row('I. Neuwagen', len(nw), 'Verkäufe', nw_prov))
    elements.append(Spacer(1, 0.3 * cm))
    totals.append(nw_prov)

    # Ia. Zielprämie
    stueck_prov = float(lauf.get('summe_stueckpraemie') or 0)
    elements.append(kat_row('Ia. Zielprämie Neuwagen', len(nw), 'Zielprämie', stueck_prov))
    elements.append(Spacer(1, 0.3 * cm))
    totals.append(stueck_prov)

    # II. Testwagen / VFW
    tw = by_kat.get('II_testwagen', [])
    tw_prov = sum(float(p.get('provision_final') or 0) for p in tw)
    elements.append(kat_row('II. Testwagen / VFW', len(tw), 'Verkäufe', tw_prov))
    elements.append(Spacer(1, 0.3 * cm))
    totals.append(tw_prov)

    # III. Gebrauchtwagen
    gw = by_kat.get('III_gebrauchtwagen', [])
    gw_prov = sum(float(p.get('provision_final') or 0) for p in gw)
    elements.append(kat_row('III. Gebrauchtwagen', len(gw), 'Verkäufe', gw_prov))
    elements.append(Spacer(1, 0.3 * cm))
    totals.append(gw_prov)

    # IV. GW aus Bestand
    gwb = by_kat.get('IV_gw_bestand', [])
    gwb_prov = sum(float(p.get('provision_final') or 0) for p in gwb)
    elements.append(kat_row('IV. GW aus Bestand', len(gwb), 'Bruttoertragsprovision', gwb_prov))
    elements.append(Spacer(1, 0.3 * cm))
    totals.append(gwb_prov)

    # V. Zusatzleistungen — nur "Finanzdienstleistung" + Gesamtsumme
    zl_total = float(lauf.get('summe_kat_v') or 0)
    zl_count = len(zusatzleistungen or [])
    elements.append(kat_row('V. Zusatzleistungen', zl_count, 'Finanzdienstleistung', zl_total))
    elements.append(Spacer(1, 0.5 * cm))
    totals.append(zl_total)

    # --- Gesamtsumme ---
    gesamt = sum(totals)
    gesamt_label = ParagraphStyle('GL', fontName='Helvetica-Bold', fontSize=11, textColor=colors.white, leading=14)
    gesamt_val = ParagraphStyle('GV', fontName='Helvetica-Bold', fontSize=12, textColor=colors.white, leading=14, alignment=TA_RIGHT)
    total_data = [
        [Paragraph('Gesamtprovision', gesamt_label),
         Paragraph(_fmt_eur(gesamt), gesamt_val)],
    ]
    total_t = Table(total_data, colWidths=[11.5 * cm, 5 * cm])
    total_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('BOX', (0, 0), (-1, -1), 1, NAVY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))
    elements.append(total_t)

    # --- Footer auf Deckblatt ---
    elements.append(Spacer(1, 0.8 * cm))
    endlauf_am = lauf.get('endlauf_am')
    footer_text = ''
    if endlauf_am:
        datum_str = endlauf_am.strftime('%d.%m.%Y') if hasattr(endlauf_am, 'strftime') else str(endlauf_am)[:10]
        footer_text = f'Abgerechnet am {datum_str}'
        if belegnummer:
            footer_text += f' \u00b7 Belegnummer {belegnummer}'
    else:
        footer_text = f'Erstellt am {datetime.now().strftime("%d.%m.%Y")}'
    footer_style = ParagraphStyle('DF', fontName='Helvetica', fontSize=8,
                                  alignment=TA_CENTER, textColor=colors.HexColor('#64748b'), leading=10)
    elements.append(Paragraph(footer_text, footer_style))

    elements.append(PageBreak())


# =============================================================================
# Seite 2+: Detail-Positionen
# =============================================================================

def _build_detail(elements, lauf, positionen, zusatzleistungen, styles, typ, jahresuebersicht=None):
    vk_name = lauf.get('verkaufer_name') or '-'
    monat = lauf.get('abrechnungsmonat') or ''
    monat_label = _monat_label(monat)
    belegnummer = lauf.get('belegnummer') or ''
    typ_label = 'Endlauf' if typ == 'endlauf' else 'Vorlauf'

    # Styles (alle Helvetica)
    title_style = ParagraphStyle('DTitle', fontName='Helvetica-Bold',
                                 fontSize=14, alignment=TA_CENTER, spaceAfter=4, textColor=NAVY, leading=18)
    subtitle_style = ParagraphStyle('DSub', fontName='Helvetica',
                                    fontSize=10, alignment=TA_CENTER, spaceAfter=2, textColor=colors.grey, leading=13)
    beleg_style = ParagraphStyle('DBeleg', fontName='Helvetica-Bold',
                                 fontSize=11, alignment=TA_CENTER, spaceAfter=8, textColor=BLUE, leading=14)
    cell = ParagraphStyle('DCell', fontName='Helvetica', fontSize=8, leading=10, wordWrap='LTR')
    cell_r = ParagraphStyle('DCellR', fontName='Helvetica', fontSize=8, leading=10, alignment=TA_RIGHT)

    # Header
    elements.append(Paragraph(f'Provisionsabrechnung {monat_label}', title_style))
    elements.append(Paragraph(f'{vk_name} \u2014 {typ_label}', subtitle_style))
    if belegnummer:
        elements.append(Paragraph(f'Belegnummer: {belegnummer}', beleg_style))
    elements.append(Spacer(1, 0.4 * cm))

    # Positionen nach Kategorie
    by_kat = {}
    for p in positionen:
        by_kat.setdefault(p.get('kategorie') or 'Sonstige', []).append(p)

    kat_names = {
        'I_neuwagen': 'I. Neuwagen',
        'II_testwagen': 'II. Testwagen / VFW',
        'III_gebrauchtwagen': 'III. Gebrauchtwagen',
        'IV_gw_bestand': 'IV. GW aus Bestand'
    }
    col_widths = [5.5 * cm, 4.5 * cm, 2.5 * cm, 2.5 * cm]

    for kat in ['I_neuwagen', 'II_testwagen', 'III_gebrauchtwagen', 'IV_gw_bestand']:
        rows = by_kat.get(kat, [])
        if not rows:
            continue

        kat_label = kat_names.get(kat, kat)
        table_data = [[Paragraph(f'<b>{kat_label}</b>',
                       ParagraphStyle('KL', parent=cell, textColor=KAT_TEXT, fontName='Helvetica-Bold')),
                       '', '', '']]
        table_data.append([
            Paragraph('<b>Modell</b>', cell),
            Paragraph('<b>Käufer</b>', cell),
            Paragraph('<b>Rg.Nr.</b>', cell),
            Paragraph('<b>Provision</b>', cell_r),
        ])

        for p in rows:
            table_data.append([
                Paragraph((p.get('modell') or '-')[:50], cell),
                Paragraph((p.get('kaeufer_name') or '-')[:45], cell),
                Paragraph((p.get('locosoft_rg_nr') or '-')[:15], cell),
                Paragraph(_fmt_eur(p.get('provision_final')), cell_r),
            ])

        t = Table(table_data, colWidths=col_widths)
        style_cmds = [
            ('SPAN', (0, 0), (-1, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), KAT_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), KAT_TEXT),
            ('BACKGROUND', (0, 1), (-1, 1), HEADER_BG),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.25, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]
        for i in range(2, len(table_data)):
            if i % 2 == 0:
                style_cmds.append(('BACKGROUND', (0, i), (-1, i), ZEBRA_EVEN))
        t.setStyle(TableStyle(style_cmds))
        elements.append(t)
        elements.append(Spacer(1, 0.3 * cm))

    # --- V. Zusatzleistungen (Einzelpositionen) ---
    zl = zusatzleistungen or []
    if zl:
        zl_col_widths = [4 * cm, 5 * cm, 3 * cm, 3 * cm]
        zl_data = [[Paragraph('<b>V. Zusatzleistungen</b>',
                    ParagraphStyle('ZLH', parent=cell, textColor=KAT_TEXT, fontName='Helvetica-Bold')),
                    '', '', '']]
        zl_data.append([
            Paragraph('<b>Bank</b>', cell),
            Paragraph('<b>Name</b>', cell),
            Paragraph('<b>Datum</b>', cell),
            Paragraph('<b>Provision</b>', cell_r),
        ])
        for z in zl:
            datum = ''
            if z.get('beleg_datum'):
                d = z['beleg_datum']
                datum = d.strftime('%d.%m.%Y') if hasattr(d, 'strftime') else str(d)[:10]
            zl_data.append([
                Paragraph((z.get('beleg_referenz') or '-')[:30], cell),
                Paragraph((z.get('bezeichnung') or '-')[:40], cell),
                Paragraph(datum, cell),
                Paragraph(_fmt_eur(z.get('provision_verkaufer')), cell_r),
            ])

        t_zl = Table(zl_data, colWidths=zl_col_widths)
        zl_cmds = [
            ('SPAN', (0, 0), (-1, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), KAT_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), KAT_TEXT),
            ('BACKGROUND', (0, 1), (-1, 1), HEADER_BG),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.25, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]
        for i in range(2, len(zl_data)):
            if i % 2 == 0:
                zl_cmds.append(('BACKGROUND', (0, i), (-1, i), ZEBRA_EVEN))
        t_zl.setStyle(TableStyle(zl_cmds))
        elements.append(KeepTogether([t_zl, Spacer(1, 0.3 * cm)]))

    # --- Jahresuebersicht ---
    if jahresuebersicht:
        j = jahresuebersicht
        elements.append(Spacer(1, 0.6 * cm))
        jh_title = ParagraphStyle('JHT', fontName='Helvetica-Bold', fontSize=10,
                                  textColor=NAVY, leading=13)
        elements.append(Paragraph(f'Jahresübersicht {j["jahr"]}', jh_title))
        elements.append(Spacer(1, 0.2 * cm))

        jh_cell = ParagraphStyle('JHC', fontName='Helvetica', fontSize=9, leading=11)
        jh_cell_b = ParagraphStyle('JHCB', fontName='Helvetica-Bold', fontSize=9, leading=11)
        jh_cell_r = ParagraphStyle('JHCR', fontName='Helvetica-Bold', fontSize=9, leading=11, alignment=TA_RIGHT)
        jh_data = [
            [Paragraph('Neuwagen', jh_cell), Paragraph(f'{j["stueck_nw"]} Stück', jh_cell_r)],
            [Paragraph('Testwagen / VFW', jh_cell), Paragraph(f'{j["stueck_tw"]} Stück', jh_cell_r)],
            [Paragraph('Gebrauchtwagen', jh_cell), Paragraph(f'{j["stueck_gw"]} Stück', jh_cell_r)],
        ]
        # Gesamtprovision Jahr
        jh_ges_l = ParagraphStyle('JGL', fontName='Helvetica-Bold', fontSize=10, textColor=colors.white, leading=13)
        jh_ges_r = ParagraphStyle('JGR', fontName='Helvetica-Bold', fontSize=10, textColor=colors.white, leading=13, alignment=TA_RIGHT)
        jh_data.append([
            Paragraph(f'Gesamtprovision {j["jahr"]}', jh_ges_l),
            Paragraph(_fmt_eur(j['provision_jahr']), jh_ges_r),
        ])

        jh_t = Table(jh_data, colWidths=[11 * cm, 5.5 * cm])
        jh_cmds = [
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -2), 0.25, BORDER_COLOR),
            ('BACKGROUND', (0, 0), (-1, 0), ZEBRA_EVEN),
            ('BACKGROUND', (0, 2), (-1, 2), ZEBRA_EVEN),
            ('BACKGROUND', (0, -1), (-1, -1), NAVY),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('LINEABOVE', (0, -1), (-1, -1), 1, NAVY),
            ('BOX', (0, -1), (-1, -1), 1, NAVY),
        ]
        jh_t.setStyle(TableStyle(jh_cmds))
        elements.append(KeepTogether([jh_t]))

    # --- Fusszeile ---
    elements.append(Spacer(1, 0.8 * cm))
    footer_parts = []
    endlauf_am = lauf.get('endlauf_am')
    if endlauf_am:
        datum_str = endlauf_am.strftime('%d.%m.%Y') if hasattr(endlauf_am, 'strftime') else str(endlauf_am)[:10]
        footer_parts.append(f'Abgerechnet am {datum_str}')
    else:
        footer_parts.append(f'Erstellt am {datetime.now().strftime("%d.%m.%Y")}')
    if belegnummer:
        footer_parts.append(f'Belegnummer {belegnummer}')
    footer_style = ParagraphStyle('DFooter', fontName='Helvetica', fontSize=8,
                                  alignment=TA_CENTER, textColor=colors.HexColor('#64748b'), leading=10)
    elements.append(Paragraph(' \u00b7 '.join(footer_parts), footer_style))


# =============================================================================
# PDF generieren
# =============================================================================

def generate_provision_pdf(lauf_id: int, typ: str = 'vorlauf') -> Optional[str]:
    """
    Erstellt PDF: Seite 1 = Deckblatt (Zusammenfassung), Seite 2+ = Detail-Positionen.
    Speicherort: data/provision_pdf/<jahr>/<monat>/<verkaufer_id>_<typ>.pdf
    """
    data = _lauf_daten(lauf_id)
    if not data:
        return None
    lauf = data['lauf']
    positionen = data['positionen']
    zusatzleistungen = data.get('zusatzleistungen', [])
    monat = lauf.get('abrechnungsmonat') or ''
    if len(monat) == 7:
        jahr, mm = monat.split('-')
    else:
        jahr, mm = datetime.now().strftime('%Y-%m').split('-')
    vkb = lauf.get('verkaufer_id') or 0
    dir_path = os.path.join('data', 'provision_pdf', jahr, mm)
    os.makedirs(dir_path, exist_ok=True)
    filename = f"{vkb}_{typ}.pdf"
    filepath = os.path.join(dir_path, filename)
    rel_path = f"provision_pdf/{jahr}/{mm}/{filename}"

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm
    )
    elements = []
    styles = getSampleStyleSheet()

    # Seite 1: Deckblatt
    _build_deckblatt(elements, lauf, positionen, zusatzleistungen, styles)

    # Seite 2+: Detail-Positionen
    jahresuebersicht = data.get('jahresuebersicht')
    _build_detail(elements, lauf, positionen, zusatzleistungen, styles, typ, jahresuebersicht)

    doc.build(elements)
    with open(filepath, 'wb') as f:
        f.write(buffer.getvalue())
    return rel_path
