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
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from api.db_utils import db_session, rows_to_list

# Farbpalette
PRIMARY = colors.HexColor('#2563eb')
PRIMARY_DARK = colors.HexColor('#1e40af')
DARK = colors.HexColor('#1e293b')
TEXT = colors.HexColor('#334155')
TEXT_LIGHT = colors.HexColor('#64748b')
TEXT_MUTED = colors.HexColor('#94a3b8')
BG_LIGHT = colors.HexColor('#f8fafc')
BG_HEADER = colors.HexColor('#f1f5f9')
BORDER = colors.HexColor('#e2e8f0')
ACCENT = colors.HexColor('#2563eb')  # Einheitliche Akzentfarbe
WHITE = colors.white

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
    """Liest Lauf + Positionen + Zusatzleistungen + Jahresuebersicht aus DB."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, verkaufer_id, verkaufer_name, abrechnungsmonat, status,
                   summe_kat_i, summe_kat_ii, summe_kat_iii, summe_kat_iv, summe_kat_v,
                   summe_stueckpraemie, summe_tw_praemie, tw_praemie_stueck, summe_gesamt, belegnummer, endlauf_am
            FROM provision_laeufe WHERE id = %s
        """, (lauf_id,))
        lauf = cur.fetchone()
        if not lauf:
            return None
        cur.execute("""
            SELECT kategorie, vin, modell, kaeufer_name, einkaeufer_name,
                   rg_netto, deckungsbeitrag, bemessungsgrundlage, provisionssatz,
                   provision_berechnet, provision_final, rg_datum, locosoft_rg_nr,
                   vorbesitzer_name
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
# Seite 1: Deckblatt
# =============================================================================

def _build_deckblatt(elements, lauf, positionen, zusatzleistungen, styles, kum_daten=None):
    vk_name = lauf.get('verkaufer_name') or '-'
    monat_label = _monat_label(lauf.get('abrechnungsmonat') or '')
    belegnummer = lauf.get('belegnummer') or ''

    # Header-Block: blaue Linie oben + Titel
    elements.append(HRFlowable(width='100%', thickness=3, color=PRIMARY, spaceAfter=12))
    elements.append(Paragraph('Provisionsabrechnung',
                    ParagraphStyle('T', fontName='Helvetica-Bold', fontSize=20, textColor=DARK, leading=24)))
    elements.append(Spacer(1, 0.15 * cm))
    elements.append(Paragraph(f'{vk_name}  \u2014  {monat_label}',
                    ParagraphStyle('S', fontName='Helvetica', fontSize=12, textColor=colors.black, leading=15)))
    if belegnummer:
        elements.append(Spacer(1, 0.1 * cm))
        elements.append(Paragraph(f'Belegnummer {belegnummer}',
                        ParagraphStyle('B', fontName='Helvetica-Bold', fontSize=10, textColor=PRIMARY, leading=13)))
    elements.append(Spacer(1, 0.5 * cm))

    # Styles
    lbl = ParagraphStyle('L', fontName='Helvetica', fontSize=10, textColor=colors.black, leading=13)
    lbl_b = ParagraphStyle('LB', fontName='Helvetica-Bold', fontSize=10, textColor=colors.black, leading=13)
    val_r = ParagraphStyle('VR', fontName='Helvetica-Bold', fontSize=11, textColor=colors.black, leading=14, alignment=TA_RIGHT)

    by_kat = {}
    for p in positionen:
        by_kat.setdefault(p.get('kategorie') or '', []).append(p)

    def summary_row(accent_color, title, stueck, bezeichnung, provision):
        """Kompakte Kategorie-Zeile mit farbigem Akzent links."""
        data = [[
            Paragraph(f'<b>{title}</b>', lbl_b),
            Paragraph(f'{stueck} Stk.' if isinstance(stueck, (int, float)) else str(stueck), lbl),
            Paragraph(bezeichnung, lbl),
            Paragraph(_fmt_eur(provision), val_r),
        ]]
        t = Table(data, colWidths=[5.5 * cm, 2 * cm, 5.5 * cm, 3.5 * cm])
        t.setStyle(TableStyle([
            ('LINEBEFORE', (0, 0), (0, 0), 3, accent_color),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (0, 0), 10),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, BORDER),
        ]))
        return t, float(provision) if provision else 0

    totals = []

    # Kategorien
    nw = by_kat.get('I_neuwagen', [])
    nw_prov = sum(float(p.get('provision_final') or 0) for p in nw)
    t, _ = summary_row(ACCENT, 'I. Neuwagen', len(nw), 'Verkäufe', nw_prov)
    elements.append(t)
    totals.append(nw_prov)

    stueck_prov = float(lauf.get('summe_stueckpraemie') or 0)
    if kum_daten:
        if kum_daten['kum_erfuellt']:
            ziel_stk = 'erfüllt'
            if kum_daten['monats_ueber'] > 0:
                ziel_stk += f" / +{kum_daten['monats_ueber']} Stk."
        else:
            ziel_stk = 'nicht erfüllt'
    else:
        if stueck_prov > 0:
            ziel_stk = f'erfüllt / {len(nw)}'
        else:
            ziel_stk = 'nicht erfüllt'
    t, _ = summary_row(ACCENT, 'Ia. Zielprämie NW', ziel_stk, 'Zielprämie', stueck_prov)
    elements.append(t)
    totals.append(stueck_prov)

    tw = by_kat.get('II_testwagen', [])
    tw_prov = sum(float(p.get('provision_final') or 0) for p in tw)
    t, _ = summary_row(ACCENT, 'II. Testwagen / VFW', len(tw), 'Verkäufe', tw_prov)
    elements.append(t)
    totals.append(tw_prov)

    tw_praemie = float(lauf.get('summe_tw_praemie') or 0)
    tw_praemie_stk = int(lauf.get('tw_praemie_stueck') or 0)
    t, _ = summary_row(ACCENT, 'IIa. TW/VFW-Prämie', tw_praemie_stk, 'Prämie', tw_praemie)
    elements.append(t)
    totals.append(tw_praemie)

    gw = by_kat.get('III_gebrauchtwagen', [])
    gw_prov = sum(float(p.get('provision_final') or 0) for p in gw)
    t, _ = summary_row(ACCENT, 'III. Gebrauchtwagen', len(gw), 'Verkäufe', gw_prov)
    elements.append(t)
    totals.append(gw_prov)

    gwb = by_kat.get('IV_gw_bestand', [])
    gwb_prov = sum(float(p.get('provision_final') or 0) for p in gwb)
    t, _ = summary_row(ACCENT, 'IV. GW aus Bestand', len(gwb), 'Bruttoertragsprovision', gwb_prov)
    elements.append(t)
    totals.append(gwb_prov)

    zl_total = float(lauf.get('summe_kat_v') or 0)
    zl_count = len(zusatzleistungen or [])
    t, _ = summary_row(ACCENT, 'V. Zusatzleistungen', zl_count, 'Finanzdienstleistung', zl_total)
    elements.append(t)
    totals.append(zl_total)

    # Gesamtsumme
    elements.append(Spacer(1, 0.3 * cm))
    gesamt = sum(totals)
    g_data = [[
        Paragraph('Gesamtprovision', ParagraphStyle('GL', fontName='Helvetica-Bold', fontSize=12, textColor=WHITE, leading=15)),
        Paragraph(_fmt_eur(gesamt), ParagraphStyle('GV', fontName='Helvetica-Bold', fontSize=14, textColor=WHITE, leading=17, alignment=TA_RIGHT)),
    ]]
    g_t = Table(g_data, colWidths=[10 * cm, 6.5 * cm])
    g_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (0, 0), 12),
        ('RIGHTPADDING', (-1, 0), (-1, 0), 12),
    ]))
    elements.append(g_t)

    # Footer
    elements.append(Spacer(1, 1 * cm))
    endlauf_am = lauf.get('endlauf_am')
    parts = []
    if endlauf_am:
        datum_str = endlauf_am.strftime('%d.%m.%Y') if hasattr(endlauf_am, 'strftime') else str(endlauf_am)[:10]
        parts.append(f'Abgerechnet am {datum_str}')
    else:
        parts.append(f'Erstellt am {datetime.now().strftime("%d.%m.%Y")}')
    if belegnummer:
        parts.append(f'Belegnummer {belegnummer}')
    elements.append(Paragraph(' \u00b7 '.join(parts),
                    ParagraphStyle('F', fontName='Helvetica', fontSize=8, textColor=TEXT_MUTED, alignment=TA_CENTER, leading=10)))
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

    # Header
    elements.append(HRFlowable(width='100%', thickness=2, color=PRIMARY, spaceAfter=8))
    elements.append(Paragraph(f'Provisionsabrechnung {monat_label}',
                    ParagraphStyle('DT', fontName='Helvetica-Bold', fontSize=13, textColor=DARK, leading=16, alignment=TA_CENTER)))
    elements.append(Paragraph(f'{vk_name} \u2014 {typ_label}',
                    ParagraphStyle('DS', fontName='Helvetica', fontSize=10, textColor=colors.black, leading=13, alignment=TA_CENTER)))
    if belegnummer:
        elements.append(Paragraph(f'Belegnummer: {belegnummer}',
                        ParagraphStyle('DB', fontName='Helvetica-Bold', fontSize=9, textColor=PRIMARY, leading=12, alignment=TA_CENTER, spaceBefore=2)))
    elements.append(Spacer(1, 0.4 * cm))

    # Tabellen-Styles
    th = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=TEXT, leading=11)
    th_r = ParagraphStyle('THR', fontName='Helvetica-Bold', fontSize=8.5, textColor=TEXT, leading=11, alignment=TA_RIGHT)
    td = ParagraphStyle('TD', fontName='Helvetica', fontSize=9, textColor=colors.black, leading=12)
    td_r = ParagraphStyle('TDR', fontName='Helvetica', fontSize=9, textColor=colors.black, leading=12, alignment=TA_RIGHT)
    td_rb = ParagraphStyle('TDRB', fontName='Helvetica-Bold', fontSize=9, textColor=colors.black, leading=12, alignment=TA_RIGHT)

    by_kat = {}
    for p in positionen:
        by_kat.setdefault(p.get('kategorie') or 'Sonstige', []).append(p)

    kat_config = [
        ('I_neuwagen', 'I. Neuwagen', ACCENT),
        ('II_testwagen', 'II. Testwagen / VFW', ACCENT),
        ('III_gebrauchtwagen', 'III. Gebrauchtwagen', ACCENT),
        ('IV_gw_bestand', 'IV. GW aus Bestand', ACCENT),
    ]
    col_widths = [5.5 * cm, 4.5 * cm, 2.5 * cm, 3 * cm]

    for kat_key, kat_label, kat_color in kat_config:
        rows = by_kat.get(kat_key, [])
        if not rows:
            continue

        # Kategorie-Header + Tabelle + Summe als Block (kein Seitenumbruch dazwischen)
        kat_sum = sum(float(p.get('provision_final') or 0) for p in rows)
        kat_elements = []
        kat_elements.append(HRFlowable(width='100%', thickness=2, color=kat_color, spaceAfter=2))
        kat_hdr = Table([
            [Paragraph(f'<b>{kat_label}</b>  <font size="8" color="#334155">({len(rows)} Fahrzeuge)</font>',
                        ParagraphStyle('KH', fontName='Helvetica-Bold', fontSize=9, textColor=DARK, leading=12)),
             Paragraph(f'<b>Gesamt: {_fmt_eur(kat_sum)}</b>', td_rb)]
        ], colWidths=[12.5 * cm, 3 * cm])
        kat_hdr.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (-1, 0), (-1, 0), 4),
        ]))
        kat_elements.append(kat_hdr)

        is_gw_bestand = (kat_key == 'IV_gw_bestand')
        if is_gw_bestand:
            table_data = [[
                Paragraph('MODELL', th), Paragraph('KÄUFER', th),
                Paragraph('VORBESITZER', th), Paragraph('BE II', th_r), Paragraph('PROVISION', th_r),
            ]]
            for p in rows:
                table_data.append([
                    Paragraph((p.get('modell') or '-')[:40], td),
                    Paragraph((p.get('kaeufer_name') or '-')[:35], td),
                    Paragraph((p.get('vorbesitzer_name') or '-')[:35], td),
                    Paragraph(_fmt_eur(p.get('bemessungsgrundlage')), td_r),
                    Paragraph(_fmt_eur(p.get('provision_final')), td_rb),
                ])
            gw_col_widths = [4.5 * cm, 3.5 * cm, 3.5 * cm, 2 * cm, 2 * cm]
        else:
            table_data = [[
                Paragraph('MODELL', th), Paragraph('KÄUFER', th),
                Paragraph('ERLÖS', th_r), Paragraph('PROVISION', th_r),
            ]]
            for p in rows:
                table_data.append([
                    Paragraph((p.get('modell') or '-')[:50], td),
                    Paragraph((p.get('kaeufer_name') or '-')[:45], td),
                    Paragraph(_fmt_eur(p.get('bemessungsgrundlage')), td_r),
                    Paragraph(_fmt_eur(p.get('provision_final')), td_rb),
                ])
            gw_col_widths = col_widths

        t = Table(table_data, colWidths=gw_col_widths)
        style_cmds = [
            ('LINEBELOW', (0, 0), (-1, 0), 0.75, BORDER),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]
        for i in range(1, len(table_data)):
            style_cmds.append(('LINEBELOW', (0, i), (-1, i), 0.25, BORDER))
            if i % 2 == 0:
                style_cmds.append(('BACKGROUND', (0, i), (-1, i), BG_HEADER))
            else:
                style_cmds.append(('BACKGROUND', (0, i), (-1, i), BG_LIGHT))
        t.setStyle(TableStyle(style_cmds))
        kat_elements.append(t)
        kat_elements.append(Spacer(1, 0.4 * cm))
        elements.append(KeepTogether(kat_elements))

    # V. Zusatzleistungen
    zl = zusatzleistungen or []
    if zl:
        zl_sum = sum(float(z.get('provision_verkaufer') or 0) for z in zl)
        zl_elements = []
        zl_elements.append(HRFlowable(width='100%', thickness=2, color=ACCENT, spaceAfter=2))
        zl_hdr = Table([
            [Paragraph(f'<b>V. Zusatzleistungen</b>  <font size="8" color="#334155">({len(zl)} Positionen)</font>',
                        ParagraphStyle('ZH', fontName='Helvetica-Bold', fontSize=9, textColor=DARK, leading=12)),
             Paragraph(f'<b>Gesamt: {_fmt_eur(zl_sum)}</b>', td_rb)]
        ], colWidths=[12 * cm, 3.5 * cm])
        zl_hdr.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (-1, 0), (-1, 0), 4),
        ]))
        zl_elements.append(zl_hdr)

        zl_widths = [4 * cm, 5 * cm, 3 * cm, 3.5 * cm]
        zl_data = [[Paragraph('BANK', th), Paragraph('NAME', th), Paragraph('DATUM', th), Paragraph('PROVISION', th_r)]]
        for z in zl:
            datum = ''
            if z.get('beleg_datum'):
                d = z['beleg_datum']
                datum = d.strftime('%d.%m.%Y') if hasattr(d, 'strftime') else str(d)[:10]
            zl_data.append([
                Paragraph((z.get('beleg_referenz') or '-')[:30], td),
                Paragraph((z.get('bezeichnung') or '-')[:40], td),
                Paragraph(datum, td),
                Paragraph(_fmt_eur(z.get('provision_verkaufer')), td_rb),
            ])
        t_zl = Table(zl_data, colWidths=zl_widths)
        zl_cmds = [
            ('LINEBELOW', (0, 0), (-1, 0), 0.75, BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]
        for i in range(1, len(zl_data)):
            zl_cmds.append(('LINEBELOW', (0, i), (-1, i), 0.25, BORDER))
            if i % 2 == 0:
                zl_cmds.append(('BACKGROUND', (0, i), (-1, i), BG_HEADER))
            else:
                zl_cmds.append(('BACKGROUND', (0, i), (-1, i), BG_LIGHT))
        t_zl.setStyle(TableStyle(zl_cmds))
        zl_elements.append(t_zl)
        zl_elements.append(Spacer(1, 0.4 * cm))
        elements.append(KeepTogether(zl_elements))

    # Jahresuebersicht
    if jahresuebersicht:
        j = jahresuebersicht
        elements.append(Spacer(1, 1.2 * cm))
        elements.append(HRFlowable(width='100%', thickness=2, color=PRIMARY, spaceAfter=8))
        elements.append(Paragraph(f'Jahresübersicht {j["jahr"]}',
                        ParagraphStyle('JT', fontName='Helvetica-Bold', fontSize=12, textColor=colors.black, leading=15, spaceAfter=6)))

        jc = ParagraphStyle('JC', fontName='Helvetica', fontSize=10, textColor=colors.black, leading=13)
        jv = ParagraphStyle('JV', fontName='Helvetica-Bold', fontSize=10, textColor=colors.black, leading=13, alignment=TA_RIGHT)
        jh_data = [
            [Paragraph('Neuwagen', jc), Paragraph(f'{j["stueck_nw"]} Stück', jv)],
            [Paragraph('Testwagen / VFW', jc), Paragraph(f'{j["stueck_tw"]} Stück', jv)],
            [Paragraph('Gebrauchtwagen', jc), Paragraph(f'{j["stueck_gw"]} Stück', jv)],
            [Paragraph(f'Gesamtprovision {j["jahr"]}',
                       ParagraphStyle('JP', fontName='Helvetica-Bold', fontSize=11, textColor=WHITE, leading=14)),
             Paragraph(_fmt_eur(j['provision_jahr']),
                       ParagraphStyle('JPV', fontName='Helvetica-Bold', fontSize=12, textColor=WHITE, leading=15, alignment=TA_RIGHT))],
        ]
        jh_t = Table(jh_data, colWidths=[11 * cm, 5.5 * cm])
        jh_t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('BACKGROUND', (0, 0), (-1, 0), BG_HEADER),
            ('BACKGROUND', (0, 1), (-1, 1), BG_LIGHT),
            ('BACKGROUND', (0, 2), (-1, 2), BG_HEADER),
            ('LINEBELOW', (0, 0), (-1, 0), 0.25, BORDER),
            ('LINEBELOW', (0, 1), (-1, 1), 0.25, BORDER),
            ('LINEBELOW', (0, 2), (-1, 2), 0.25, BORDER),
            ('BACKGROUND', (0, -1), (-1, -1), PRIMARY_DARK),
            ('LEFTPADDING', (0, -1), (0, -1), 10),
            ('RIGHTPADDING', (-1, -1), (-1, -1), 10),
            ('TOPPADDING', (0, -1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 9),
        ]))
        elements.append(KeepTogether([jh_t]))

    # Fusszeile
    elements.append(Spacer(1, 0.8 * cm))
    parts = []
    endlauf_am = lauf.get('endlauf_am')
    if endlauf_am:
        datum_str = endlauf_am.strftime('%d.%m.%Y') if hasattr(endlauf_am, 'strftime') else str(endlauf_am)[:10]
        parts.append(f'Abgerechnet am {datum_str}')
    else:
        parts.append(f'Erstellt am {datetime.now().strftime("%d.%m.%Y")}')
    if belegnummer:
        parts.append(f'Belegnummer {belegnummer}')
    elements.append(Paragraph(' \u00b7 '.join(parts),
                    ParagraphStyle('DF', fontName='Helvetica', fontSize=8, textColor=TEXT_MUTED, alignment=TA_CENTER, leading=10)))


# =============================================================================
# PDF generieren
# =============================================================================

def generate_provision_pdf(lauf_id: int, typ: str = 'vorlauf') -> Optional[str]:
    """Erstellt PDF: Seite 1 = Deckblatt, Seite 2+ = Detail-Positionen."""
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

    # Kumulierte Zielprämie-Daten
    kum_daten = None
    if lauf.get('abrechnungsmonat') and vkb:
        from api.provision_service import get_provision_config_for_monat, get_kumulierte_zielpraemie_daten
        cfg_i = get_provision_config_for_monat(lauf['abrechnungsmonat']).get('I_neuwagen') or {}
        if cfg_i.get('use_kumuliert') and cfg_i.get('use_zielpraemie'):
            kum_daten = get_kumulierte_zielpraemie_daten(vkb, lauf['abrechnungsmonat'], cfg_i)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    elements = []
    styles = getSampleStyleSheet()

    _build_deckblatt(elements, lauf, positionen, zusatzleistungen, styles, kum_daten=kum_daten)
    _build_detail(elements, lauf, positionen, zusatzleistungen, styles, typ, data.get('jahresuebersicht'))

    doc.build(elements)
    with open(filepath, 'wb') as f:
        f.write(buffer.getvalue())
    return rel_path
