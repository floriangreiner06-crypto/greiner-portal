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


def _fmt_eur(value) -> str:
    try:
        return f"{float(value):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "0,00 €"


def _lauf_daten(lauf_id: int) -> Optional[dict]:
    """Liest Lauf + Positionen aus DB."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, verkaufer_id, verkaufer_name, abrechnungsmonat, status,
                   summe_kat_i, summe_kat_ii, summe_kat_iii, summe_kat_iv, summe_kat_v, summe_gesamt
            FROM provision_laeufe WHERE id = %s
        """, (lauf_id,))
        lauf = cur.fetchone()
        if not lauf:
            return None
        cur.execute("""
            SELECT kategorie, vin, modell, kaeufer_name, einkaeufer_name, rg_netto, deckungsbeitrag, provision_final, rg_datum
            FROM provision_positionen WHERE lauf_id = %s
            ORDER BY CASE kategorie
                WHEN 'I_neuwagen' THEN 1 WHEN 'II_testwagen' THEN 2
                WHEN 'III_gebrauchtwagen' THEN 3 WHEN 'IV_gw_bestand' THEN 4 ELSE 5 END,
                provision_final DESC NULLS LAST
        """, (lauf_id,))
        positionen = rows_to_list(cur.fetchall())
    return {'lauf': dict(lauf), 'positionen': positionen}


def generate_provision_pdf(lauf_id: int, typ: str = 'vorlauf') -> Optional[str]:
    """
    Erstellt PDF für einen Provisionslauf (Vorlauf oder Endlauf).
    Speicherort: data/provision_pdf/<jahr>/<monat>/<verkaufer_id>_<typ>.pdf
    Returns: relativer Pfad (z.B. provision_pdf/2026/01/2007_vorlauf.pdf) oder None bei Fehler.
    """
    data = _lauf_daten(lauf_id)
    if not data:
        return None
    lauf = data['lauf']
    positionen = data['positionen']
    monat = lauf.get('abrechnungsmonat') or ''
    if len(monat) == 7:  # YYYY-MM
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
        leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('ProvTitle', parent=styles['Heading1'], fontSize=14, alignment=TA_CENTER, spaceAfter=6)
    normal_style = ParagraphStyle('ProvNormal', parent=styles['Normal'], fontSize=9)

    elements.append(Paragraph("AUTOHAUS GREINER – Provisionsabrechnung", title_style))
    elements.append(Paragraph(
        f"Verkäufer: {lauf.get('verkaufer_name') or '-'} &nbsp;&nbsp; Monat: {monat} &nbsp;&nbsp; Status: {typ.upper()} &nbsp;&nbsp; {datetime.now().strftime('%d.%m.%Y')}",
        normal_style
    ))
    elements.append(Spacer(1, 0.5*cm))

    # Positionen nach Kategorie
    by_kat = {}
    for p in positionen:
        k = p.get('kategorie') or 'Sonstige'
        by_kat.setdefault(k, []).append(p)

    for kat in ['I_neuwagen', 'II_testwagen', 'III_gebrauchtwagen', 'IV_gw_bestand']:
        rows = by_kat.get(kat, [])
        if not rows:
            continue
        kat_name = {'I_neuwagen': 'I. Neuwagen', 'II_testwagen': 'II. Testwagen/VFW', 'III_gebrauchtwagen': 'III. Gebrauchtwagen', 'IV_gw_bestand': 'IV. GW aus Bestand'}.get(kat, kat)
        elements.append(Paragraph(kat_name, styles['Heading2']))
        table_data = [['Datum', 'Modell', 'Rg.Netto / DB', 'Provision']]
        for p in rows:
            datum = (p.get('rg_datum') or '')[:10] if p.get('rg_datum') else '-'
            modell = (p.get('modell') or '-')[:40]
            val = p.get('rg_netto') if p.get('rg_netto') is not None else p.get('deckungsbeitrag')
            table_data.append([datum, modell, _fmt_eur(val), _fmt_eur(p.get('provision_final'))])
        t = Table(table_data, colWidths=[2*cm, 8*cm, 3*cm, 2.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.3*cm))

    # Summen
    elements.append(Paragraph("Zusammenfassung", styles['Heading2']))
    sum_data = [
        ['Kat. I Neuwagen', _fmt_eur(lauf.get('summe_kat_i'))],
        ['Kat. II Testwagen/VFW', _fmt_eur(lauf.get('summe_kat_ii'))],
        ['Kat. III Gebrauchtwagen', _fmt_eur(lauf.get('summe_kat_iii'))],
        ['Kat. IV GW Bestand', _fmt_eur(lauf.get('summe_kat_iv'))],
        ['Kat. V Zusatzleistungen', _fmt_eur(lauf.get('summe_kat_v'))],
        ['Gesamt', _fmt_eur(lauf.get('summe_gesamt'))],
    ]
    t2 = Table(sum_data, colWidths=[10*cm, 4*cm])
    t2.setStyle(TableStyle([
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
    ]))
    elements.append(t2)

    doc.build(elements)
    with open(filepath, 'wb') as f:
        f.write(buffer.getvalue())
    return rel_path
