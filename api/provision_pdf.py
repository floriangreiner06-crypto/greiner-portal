"""
Provisions-PDF: Vorlauf und Endlauf (Provisionsabrechnung pro Verkäufer/Monat).
Nutzt reportlab wie api/pdf_generator.py. Daten aus provision_laeufe + provision_positionen (SSOT).
"""
import os
from datetime import datetime
from io import BytesIO
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from api.db_utils import db_session, rows_to_list

# Farben
NAVY = colors.HexColor('#1e3a5f')
BLUE = colors.HexColor('#1e40af')
LIGHT_BG = colors.HexColor('#f8fafc')
ZEBRA_EVEN = colors.HexColor('#f1f5f9')
HEADER_BG = colors.HexColor('#e2e8f0')
KAT_BG = colors.HexColor('#cbd5e1')

MONAT_NAMEN = [
    'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
    'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
]


def _fmt_eur(value) -> str:
    try:
        return f"{float(value):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "0,00 €"


def _monat_label(monat: str) -> str:
    """'2026-01' → 'Januar 2026'"""
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
    return {'lauf': dict(lauf), 'positionen': positionen, 'zusatzleistungen': zusatzleistungen}


def _build_deckblatt(elements, lauf, positionen, zusatzleistungen, styles):
    """Seite 1: Zusammenfassung im Excel-Stil (Deckblatt)."""
    vk_name = lauf.get('verkaufer_name') or '-'
    monat_label = _monat_label(lauf.get('abrechnungsmonat') or '')

    # Titel
    title_style = ParagraphStyle('DeckTitle', parent=styles['Heading1'],
                                 fontSize=16, spaceAfter=12, textColor=NAVY)
    elements.append(Paragraph('Provisionsabrechnung', title_style))

    # Name + Monat/Jahr als Tabelle
    info_style = ParagraphStyle('DeckInfo', parent=styles['Normal'], fontSize=10)
    info_bold = ParagraphStyle('DeckInfoBold', parent=info_style, fontName='Helvetica-Bold')
    info_data = [
        [Paragraph('<b>Name:</b>', info_bold), Paragraph(vk_name, info_style),
         Paragraph('<b>Monat/Jahr:</b>', info_bold), Paragraph(monat_label, info_style)],
    ]
    info_t = Table(info_data, colWidths=[2.5 * cm, 6 * cm, 3 * cm, 5 * cm])
    info_t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
    ]))
    elements.append(info_t)
    elements.append(Spacer(1, 0.6 * cm))

    cell = ParagraphStyle('DeckCell', parent=styles['Normal'], fontSize=9, leading=11)
    cell_b = ParagraphStyle('DeckCellBold', parent=cell, fontName='Helvetica-Bold')
    cell_r = ParagraphStyle('DeckCellR', parent=cell, alignment=TA_RIGHT)
    cell_rb = ParagraphStyle('DeckCellRB', parent=cell_r, fontName='Helvetica-Bold')

    kat_header_style = ParagraphStyle('KatHeader', parent=cell_b, alignment=TA_CENTER, fontSize=9)

    # Positionen nach Kategorie zaehlen
    by_kat = {}
    for p in positionen:
        k = p.get('kategorie') or ''
        by_kat.setdefault(k, []).append(p)

    def kat_table(title, rows_data):
        """Erstellt eine Kategorie-Tabelle fuer das Deckblatt."""
        data = [[Paragraph(f'<b>{title}</b>', kat_header_style), '', '', '']]
        data.append([
            Paragraph('<b>Stück</b>', cell_b),
            Paragraph('<b>Bezeichnung</b>', cell_b),
            Paragraph('<b>Betrag</b>', cell_rb),
            Paragraph('<b>Provision in €</b>', cell_rb),
        ])
        for rd in rows_data:
            data.append([
                Paragraph(str(rd[0]), cell),
                Paragraph(str(rd[1]), cell),
                Paragraph(str(rd[2]), cell_r),
                Paragraph(str(rd[3]), cell_r),
            ])
        # Summenzeile
        total = sum(float(rd[4]) for rd in rows_data if rd[4] is not None)
        data.append([Paragraph('', cell), Paragraph('', cell), Paragraph('', cell),
                     Paragraph(f'<b>{_fmt_eur(total)}</b>', cell_rb)])

        t = Table(data, colWidths=[2 * cm, 5 * cm, 4 * cm, 4.5 * cm])
        style_cmds = [
            ('SPAN', (0, 0), (-1, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d0d0d0')),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e8e8e8')),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.black),
            ('INNERGRID', (0, 1), (-1, -1), 0.5, colors.HexColor('#999999')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]
        t.setStyle(TableStyle(style_cmds))
        return t, total

    totals = []

    # I. Neuwagen
    nw = by_kat.get('I_neuwagen', [])
    nw_betrag = sum(float(p.get('bemessungsgrundlage') or 0) for p in nw)
    nw_prov = sum(float(p.get('provision_final') or 0) for p in nw)
    t, _ = kat_table('I. Neuwagen', [
        [len(nw), 'Verkäufe', _fmt_eur(nw_betrag), _fmt_eur(nw_prov), nw_prov],
    ])
    elements.append(t)
    elements.append(Spacer(1, 0.4 * cm))
    totals.append(nw_prov)

    # Ia. Zielprämie NW
    stueck = float(lauf.get('summe_stueckpraemie') or 0)
    t_ia, _ = kat_table('Ia. Zielprämie Neuwagen', [
        [len(nw), 'Zielprämie', '', _fmt_eur(stueck), stueck],
    ])
    elements.append(t_ia)
    elements.append(Spacer(1, 0.4 * cm))
    totals.append(stueck)

    # II. Testwagen / VFW
    tw = by_kat.get('II_testwagen', [])
    tw_betrag = sum(float(p.get('bemessungsgrundlage') or 0) for p in tw)
    tw_prov = sum(float(p.get('provision_final') or 0) for p in tw)
    t, _ = kat_table('II. Testwagen / VFW', [
        [len(tw), 'Verkäufe', _fmt_eur(tw_betrag), _fmt_eur(tw_prov), tw_prov],
    ])
    elements.append(t)
    elements.append(Spacer(1, 0.4 * cm))
    totals.append(tw_prov)

    # III. Gebrauchtwagen-Verkäufe
    gw = by_kat.get('III_gebrauchtwagen', [])
    gw_betrag = sum(float(p.get('bemessungsgrundlage') or 0) for p in gw)
    gw_prov = sum(float(p.get('provision_final') or 0) for p in gw)
    t, _ = kat_table('III. Gebrauchtwagen-Verkäufe', [
        [len(gw), 'Verkäufe', _fmt_eur(gw_betrag), _fmt_eur(gw_prov), gw_prov],
    ])
    elements.append(t)
    elements.append(Spacer(1, 0.4 * cm))
    totals.append(gw_prov)

    # IV. Gebrauchtwagen aus Bestand
    gwb = by_kat.get('IV_gw_bestand', [])
    gwb_betrag = sum(float(p.get('bemessungsgrundlage') or 0) for p in gwb)
    gwb_prov = sum(float(p.get('provision_final') or 0) for p in gwb)
    t, _ = kat_table('IV. Gebrauchtwagen-Verkäufe aus Bestand', [
        [len(gwb), 'Bruttoertragsprov.', _fmt_eur(gwb_betrag), _fmt_eur(gwb_prov), gwb_prov],
    ])
    elements.append(t)
    elements.append(Spacer(1, 0.4 * cm))
    totals.append(gwb_prov)

    # V. Zusatzleistungen
    zl = zusatzleistungen or []
    zl_rows = []
    for z in zl:
        bank = z.get('beleg_referenz') or ''
        name = z.get('bezeichnung') or ''
        betrag = float(z.get('provision_verkaufer') or 0)
        label = f"{bank} — {name}" if bank and name else (bank or name or 'Zusatzleistung')
        zl_rows.append([1, label, _fmt_eur(betrag), _fmt_eur(betrag), betrag])
    if not zl_rows:
        zl_rows = [[0, 'Keine', _fmt_eur(0), _fmt_eur(0), 0]]
    t, zl_total = kat_table('V. Zusatzleistungen', zl_rows)
    elements.append(t)
    elements.append(Spacer(1, 0.6 * cm))
    totals.append(zl_total)

    # Total-Zeile
    gesamt = sum(totals)
    total_data = [
        [Paragraph('<b>Total Provision I + Ia + II + III + IV + V</b>',
                   ParagraphStyle('TotalLabel', parent=cell_b, fontSize=10)),
         Paragraph(f'<b>{_fmt_eur(gesamt)}</b>',
                   ParagraphStyle('TotalVal', parent=cell_rb, fontSize=12))],
    ]
    total_t = Table(total_data, colWidths=[11.5 * cm, 4 * cm])
    total_t.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(total_t)

    # Seitenumbruch nach Deckblatt
    from reportlab.platypus import PageBreak
    elements.append(PageBreak())


def generate_provision_pdf(lauf_id: int, typ: str = 'vorlauf') -> Optional[str]:
    """
    Erstellt PDF für einen Provisionslauf (Vorlauf oder Endlauf).
    Speicherort: data/provision_pdf/<jahr>/<monat>/<verkaufer_id>_<typ>.pdf
    Returns: relativer Pfad oder None bei Fehler.
    """
    data = _lauf_daten(lauf_id)
    if not data:
        return None
    lauf = data['lauf']
    positionen = data['positionen']
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
    zusatzleistungen = data.get('zusatzleistungen', [])

    # === Seite 1: Deckblatt (Zusammenfassung) ===
    _build_deckblatt(elements, lauf, positionen, zusatzleistungen, styles)

    # === Seite 2+: Detail-Positionen ===
    # Styles
    title_style = ParagraphStyle('ProvTitle', parent=styles['Heading1'],
                                 fontSize=14, alignment=TA_CENTER, spaceAfter=4,
                                 textColor=NAVY)
    subtitle_style = ParagraphStyle('ProvSubtitle', parent=styles['Normal'],
                                    fontSize=10, alignment=TA_CENTER, spaceAfter=2,
                                    textColor=colors.grey)
    beleg_style = ParagraphStyle('ProvBeleg', parent=styles['Normal'],
                                 fontSize=11, alignment=TA_CENTER, spaceAfter=8,
                                 textColor=BLUE, fontName='Helvetica-Bold')
    cell_style = ParagraphStyle('CellWrap', parent=styles['Normal'],
                                fontSize=8, leading=10, wordWrap='LTR')
    cell_right = ParagraphStyle('CellRight', parent=cell_style, alignment=TA_RIGHT)

    # --- Titel ---
    vk_name = lauf.get('verkaufer_name') or '-'
    monat_label = _monat_label(monat)
    typ_label = 'Endlauf' if typ == 'endlauf' else 'Vorlauf'

    elements.append(Paragraph(f"Provisionsabrechnung {monat_label}", title_style))
    elements.append(Paragraph(f"{vk_name} — {typ_label}", subtitle_style))

    # --- Belegnummer ---
    belegnummer = lauf.get('belegnummer') or ''
    if belegnummer:
        elements.append(Paragraph(f"Belegnummer: {belegnummer}", beleg_style))
    elements.append(Spacer(1, 0.4 * cm))

    # --- Positionen nach Kategorie ---
    by_kat = {}
    for p in positionen:
        k = p.get('kategorie') or 'Sonstige'
        by_kat.setdefault(k, []).append(p)

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

        # Kategorie-Trennzeile (SPAN über alle Spalten)
        table_data = [[Paragraph(f"<b>{kat_label}</b>", cell_style), '', '', '']]

        # Header
        table_data.append([
            Paragraph('<b>Modell</b>', cell_style),
            Paragraph('<b>Käufer</b>', cell_style),
            Paragraph('<b>Rg.Nr.</b>', cell_style),
            Paragraph('<b>Provision</b>', cell_right),
        ])

        for p in rows:
            modell = (p.get('modell') or '-')[:50]
            kaeufer = (p.get('kaeufer_name') or '-')[:45]
            rg_nr = (p.get('locosoft_rg_nr') or '-')[:15]
            table_data.append([
                Paragraph(modell, cell_style),
                Paragraph(kaeufer, cell_style),
                Paragraph(rg_nr, cell_style),
                Paragraph(_fmt_eur(p.get('provision_final')), cell_right),
            ])

        t = Table(table_data, colWidths=col_widths)
        style_cmds = [
            # Kategorie-Trennzeile
            ('SPAN', (0, 0), (-1, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), KAT_BG),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            # Header
            ('BACKGROUND', (0, 1), (-1, 1), HEADER_BG),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            # Allgemein
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#94a3b8')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]
        # Zebra-Stripes für Datenzeilen
        for i in range(2, len(table_data)):
            if i % 2 == 0:
                style_cmds.append(('BACKGROUND', (0, i), (-1, i), ZEBRA_EVEN))

        t.setStyle(TableStyle(style_cmds))
        elements.append(t)
        elements.append(Spacer(1, 0.3 * cm))

    # --- Zusammenfassung ---
    elements.append(Spacer(1, 0.3 * cm))
    sum_labels = [
        ('Kat. I — Neuwagen', lauf.get('summe_kat_i')),
        ('Kat. Ia — Zielprämie NW', lauf.get('summe_stueckpraemie')),
        ('Kat. II — Testwagen / VFW', lauf.get('summe_kat_ii')),
        ('Kat. III — Gebrauchtwagen', lauf.get('summe_kat_iii')),
        ('Kat. IV — GW aus Bestand', lauf.get('summe_kat_iv')),
        ('Kat. V — Zusatzleistungen', lauf.get('summe_kat_v')),
    ]
    sum_data = []
    for label, val in sum_labels:
        sum_data.append([
            Paragraph(label, cell_style),
            Paragraph(_fmt_eur(val), cell_right),
        ])

    # Gesamtbetrag-Zeile
    gesamt_style = ParagraphStyle('GesamtLabel', parent=cell_style,
                                  fontName='Helvetica-Bold', fontSize=10, textColor=colors.white)
    gesamt_val_style = ParagraphStyle('GesamtVal', parent=cell_right,
                                      fontName='Helvetica-Bold', fontSize=10, textColor=colors.white)
    sum_data.append([
        Paragraph('GESAMTBETRAG', gesamt_style),
        Paragraph(_fmt_eur(lauf.get('summe_gesamt')), gesamt_val_style),
    ])

    t2 = Table(sum_data, colWidths=[13 * cm, 4 * cm])
    style_cmds2 = [
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -2), 0.25, colors.HexColor('#94a3b8')),
        # Gesamtzeile: Navy-Hintergrund
        ('BACKGROUND', (0, -1), (-1, -1), NAVY),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, NAVY),
    ]
    # Zebra für Summenzeilen
    for i in range(len(sum_data) - 1):
        if i % 2 == 0:
            style_cmds2.append(('BACKGROUND', (0, i), (-1, i), ZEBRA_EVEN))
    t2.setStyle(TableStyle(style_cmds2))
    elements.append(t2)

    # --- Fußzeile ---
    elements.append(Spacer(1, 1 * cm))
    footer_parts = []
    endlauf_am = lauf.get('endlauf_am')
    if endlauf_am:
        if hasattr(endlauf_am, 'strftime'):
            datum_str = endlauf_am.strftime('%d.%m.%Y')
        else:
            datum_str = str(endlauf_am)[:10]
        footer_parts.append(f"Abgerechnet am {datum_str}")
    else:
        footer_parts.append(f"Erstellt am {datetime.now().strftime('%d.%m.%Y')}")
    if belegnummer:
        footer_parts.append(f"Belegnummer {belegnummer}")
    footer_style = ParagraphStyle('ProvFooter', parent=styles['Normal'],
                                  fontSize=8, alignment=TA_CENTER,
                                  textColor=colors.HexColor('#64748b'))
    elements.append(Paragraph(' · '.join(footer_parts), footer_style))

    doc.build(elements)
    with open(filepath, 'wb') as f:
        f.write(buffer.getvalue())
    return rel_path
