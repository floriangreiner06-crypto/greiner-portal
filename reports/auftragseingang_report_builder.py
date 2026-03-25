"""
SSOT Builder für Auftragseingang E-Mail + PDF.

Dieser Builder wird von Daily-Job, Admin-Testversand und manuellem API-Versand
gemeinsam genutzt, damit Betreff/Body/PDF konsistent bleiben.
"""

from datetime import date, datetime
from typing import Dict, Any, List

from api.pdf_generator import generate_auftragseingang_komplett_pdf
from api.verkauf_data import VerkaufData
from utils.werktage import get_werktage_monat


MONATE = [
    "", "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]
MARKEN_ORDER = ["Opel", "Leapmotor", "Hyundai"]


def _build_marken_map(summary_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    marken = {name: {"nw": 0, "vfw": 0, "t": 0} for name in MARKEN_ORDER}
    for row in (summary_rows or []):
        name = (row.get("marke") or "").strip()
        if name not in marken:
            continue
        marken[name]["nw"] = int(row.get("nw") or row.get("neu") or 0)
        marken[name]["vfw"] = int(row.get("vfw") or 0)
        marken[name]["t"] = int(row.get("t") or 0)
    return marken


def _build_marken_rows_html(summary_rows: List[Dict[str, Any]]) -> str:
    marken = _build_marken_map(summary_rows)
    total_nw = total_vfw = total_t = 0
    html_rows = ""
    for name in MARKEN_ORDER:
        vals = marken[name]
        row_sum = vals["nw"] + vals["vfw"] + vals["t"]
        total_nw += vals["nw"]
        total_vfw += vals["vfw"]
        total_t += vals["t"]
        html_rows += f"""
            <tr style="background: #fff;">
                <td style="padding: 6px 8px; font-weight: bold;">{name}</td>
                <td style="padding: 6px 8px; text-align: center;">{vals['nw']}</td>
                <td style="padding: 6px 8px; text-align: center;">{vals['vfw']}</td>
                <td style="padding: 6px 8px; text-align: center;">{vals['t']}</td>
                <td style="padding: 6px 8px; text-align: center; font-weight: bold;">{row_sum}</td>
            </tr>"""
    html_rows += f"""
        <tr style="background: #e7f1ff; font-weight: bold;">
            <td style="padding: 6px 8px;">GESAMT</td>
            <td style="padding: 6px 8px; text-align: center;">{total_nw}</td>
            <td style="padding: 6px 8px; text-align: center;">{total_vfw}</td>
            <td style="padding: 6px 8px; text-align: center;">{total_t}</td>
            <td style="padding: 6px 8px; text-align: center;">{total_nw + total_vfw + total_t}</td>
        </tr>"""
    return html_rows


def _build_marken_subject(summary_rows: List[Dict[str, Any]]) -> str:
    marken = _build_marken_map(summary_rows)
    return " | ".join(
        [f"{name}: {vals['nw']}/{vals['vfw']}/{vals['t']}" for name, vals in marken.items()]
    )


def _build_verkaufer_rows_html(data: List[Dict[str, Any]], with_sum_row: bool = False, sum_values: Dict[str, int] = None) -> str:
    rows = ""
    for vk in sorted(data, key=lambda x: x.get("summe_gesamt", 0), reverse=True):
        if vk.get("summe_gesamt", 0) <= 0:
            continue
        rows += f"""
            <tr style="background: #fff;">
                <td style="padding: 6px 8px;">{(vk.get('verkaufer_name') or 'Unbekannt')[:28]}</td>
                <td style="padding: 6px 8px; text-align: center;">{vk.get('summe_neu', 0)}</td>
                <td style="padding: 6px 8px; text-align: center;">{vk.get('summe_test_vorfuehr', 0)}</td>
                <td style="padding: 6px 8px; text-align: center;">{vk.get('summe_gebraucht', 0)}</td>
                <td style="padding: 6px 8px; text-align: center; font-weight: bold;">{vk.get('summe_gesamt', 0)}</td>
            </tr>"""
    if not rows and not with_sum_row:
        return '<tr style="background: #f8f9fa;"><td colspan="5" style="padding: 8px; color: #666;">Keine Aufträge.</td></tr>'
    if with_sum_row and sum_values:
        rows += f"""
            <tr style="background: #e7f1ff; font-weight: bold;">
                <td style="padding: 6px 8px;">GESAMT</td>
                <td style="padding: 6px 8px; text-align: center;">{sum_values['nw']}</td>
                <td style="padding: 6px 8px; text-align: center;">{sum_values['tv']}</td>
                <td style="padding: 6px 8px; text-align: center;">{sum_values['gw']}</td>
                <td style="padding: 6px 8px; text-align: center;">{sum_values['gesamt']}</td>
            </tr>"""
    return rows


def build_auftragseingang_report_package(anchor_date: date) -> Dict[str, Any]:
    """
    Baut den kompletten Auftragseingang-Report für einen Stichtag.
    Der Stichtag steuert 'Heute'; die Monatsdaten laufen auf den Monat des Stichtags.
    """
    heute_str = anchor_date.strftime("%Y-%m-%d")
    datum_display = anchor_date.strftime("%d.%m.%Y")
    monat = anchor_date.month
    jahr = anchor_date.year
    monat_display = f"{MONATE[monat]} {jahr}"

    res_tag = VerkaufData.get_auftragseingang_detail(day=heute_str)
    res_monat = VerkaufData.get_auftragseingang_detail(month=monat, year=jahr)
    tag_data = res_tag.get("verkaufer", []) if res_tag.get("success") else []
    monat_data = res_monat.get("verkaufer", []) if res_monat.get("success") else []
    nw_tag = VerkaufData.get_auftragseingang_nw_marke_modell(day=heute_str)
    nw_monat = VerkaufData.get_auftragseingang_nw_marke_modell(month=monat, year=jahr)
    res_tag_summary = VerkaufData.get_auftragseingang_summary(day=heute_str)
    res_monat_summary = VerkaufData.get_auftragseingang_summary(month=monat, year=jahr)
    tag_summary_rows = (res_tag_summary or {}).get("summary", [])
    monat_summary_rows = (res_monat_summary or {}).get("summary", [])

    tag_gesamt = sum(v.get("summe_gesamt", 0) for v in tag_data)
    monat_gesamt = sum(v.get("summe_gesamt", 0) for v in monat_data)
    tag_nw = sum(v.get("summe_neu", 0) for v in tag_data)
    tag_tv = sum(v.get("summe_test_vorfuehr", 0) for v in tag_data)
    tag_gw = sum(v.get("summe_gebraucht", 0) for v in tag_data)
    monat_nw = sum(v.get("summe_neu", 0) for v in monat_data)
    monat_tv = sum(v.get("summe_test_vorfuehr", 0) for v in monat_data)
    monat_gw = sum(v.get("summe_gebraucht", 0) for v in monat_data)

    wt = get_werktage_monat(jahr, monat)
    ae_pro_tag = (monat_gesamt / wt["vergangen"]) if wt["vergangen"] > 0 else 0.0
    prognose_ae = round(ae_pro_tag * wt["gesamt"]) if wt["vergangen"] > 0 else None

    pdf_bytes = generate_auftragseingang_komplett_pdf(
        tag_data=tag_data,
        monat_data=monat_data,
        datum_display=datum_display,
        monat_display=monat_display,
        nw_tag=nw_tag,
        nw_monat=nw_monat,
        werktage=wt,
        prognose=prognose_ae,
        ae_pro_tag=round(ae_pro_tag, 1) if wt["vergangen"] > 0 else None,
    )

    tag_rows_html = _build_verkaufer_rows_html(tag_data, with_sum_row=False)
    monat_rows_html = _build_verkaufer_rows_html(
        monat_data,
        with_sum_row=True,
        sum_values={"nw": monat_nw, "tv": monat_tv, "gw": monat_gw, "gesamt": monat_gesamt},
    )
    tag_marken_rows = _build_marken_rows_html(tag_summary_rows)
    monat_marken_rows = _build_marken_rows_html(monat_summary_rows)

    werktage_text = f"Werktage: {wt['vergangen']} von {wt['gesamt']} vergangen ({wt['verbleibend']} verbleibend)"
    if wt["vergangen"] > 0 and prognose_ae is not None:
        werktage_text += f" · Prognose: <strong>{prognose_ae} AE</strong> (aktuell {round(ae_pro_tag, 1)} AE/Tag)"

    tag_marken_subject = _build_marken_subject(tag_summary_rows)
    monat_marken_subject = _build_marken_subject(monat_summary_rows)
    subject = (
        f"📊 Auftragseingang {datum_display} - Heute: {tag_gesamt} | Monat: {monat_gesamt}"
        f" | Heute O/L/H NW-VFW-T {tag_marken_subject}"
        f" | Monat O/L/H NW-VFW-T {monat_marken_subject}"
    )

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 640px;">
        <h2 style="color: #0066cc; font-size: 18px; margin-bottom: 4px;">Auftragseingang</h2>
        <div style="border-bottom: 3px solid #0066cc; margin-bottom: 6px;"></div>
        <p style="color: #6c757d; font-size: 12px; margin: 0 0 12px 0;">Monat: {monat_display} · Stand: {datum_display} {datetime.now().strftime('%H:%M')} Uhr</p>
        <p style="color: #333; font-size: 12px; margin: 0 0 12px 0;">{werktage_text}</p>

        <table style="border-collapse: collapse; width: 100%; margin-bottom: 16px; font-size: 13px;">
            <tr style="background: #0066cc; color: white;">
                <th style="padding: 8px; text-align: left;"></th>
                <th style="padding: 8px; text-align: center;">NW</th>
                <th style="padding: 8px; text-align: center;">T/V</th>
                <th style="padding: 8px; text-align: center;">GW</th>
                <th style="padding: 8px; text-align: center;">GESAMT</th>
            </tr>
            <tr style="background: #f8f9fa;">
                <td style="padding: 8px; font-weight: bold;">Heute ({datum_display})</td>
                <td style="padding: 8px; text-align: center; font-weight: bold;">{tag_nw}</td>
                <td style="padding: 8px; text-align: center; font-weight: bold;">{tag_tv}</td>
                <td style="padding: 8px; text-align: center; font-weight: bold;">{tag_gw}</td>
                <td style="padding: 8px; text-align: center; font-weight: bold;">{tag_gesamt}</td>
            </tr>
            <tr style="background: #fff;">
                <td style="padding: 8px; font-weight: bold;">{monat_display} (Gesamt)</td>
                <td style="padding: 8px; text-align: center; font-weight: bold;">{monat_nw}</td>
                <td style="padding: 8px; text-align: center; font-weight: bold;">{monat_tv}</td>
                <td style="padding: 8px; text-align: center; font-weight: bold;">{monat_gw}</td>
                <td style="padding: 8px; text-align: center; font-weight: bold;">{monat_gesamt}</td>
            </tr>
        </table>

        <h3 style="color: #0066cc; font-size: 12px; margin: 16px 0 6px 0;">Heute – nach Verkäufer</h3>
        <table style="border-collapse: collapse; width: 100%; margin-bottom: 4px; font-size: 12px;">
            <tr style="background: #0066cc; color: white;">
                <th style="padding: 6px 8px; text-align: left;">Verkäufer</th>
                <th style="padding: 6px 8px; text-align: center;">NW</th>
                <th style="padding: 6px 8px; text-align: center;">T/V</th>
                <th style="padding: 6px 8px; text-align: center;">GW</th>
                <th style="padding: 6px 8px; text-align: center;">Ges.</th>
            </tr>
            {tag_rows_html}
        </table>

        <h3 style="color: #0066cc; font-size: 12px; margin: 16px 0 6px 0;">{monat_display} – nach Verkäufer (Gesamt)</h3>
        <table style="border-collapse: collapse; width: 100%; margin-bottom: 4px; font-size: 12px;">
            <tr style="background: #0066cc; color: white;">
                <th style="padding: 6px 8px; text-align: left;">Verkäufer</th>
                <th style="padding: 6px 8px; text-align: center;">NW</th>
                <th style="padding: 6px 8px; text-align: center;">T/V</th>
                <th style="padding: 6px 8px; text-align: center;">GW</th>
                <th style="padding: 6px 8px; text-align: center;">Ges.</th>
            </tr>
            {monat_rows_html}
        </table>

        <h3 style="color: #0066cc; font-size: 12px; margin: 16px 0 6px 0;">Heute – Marken-Split (NW / VFW / T)</h3>
        <table style="border-collapse: collapse; width: 100%; margin-bottom: 4px; font-size: 12px;">
            <tr style="background: #0066cc; color: white;">
                <th style="padding: 6px 8px; text-align: left;">Marke</th>
                <th style="padding: 6px 8px; text-align: center;">NW</th>
                <th style="padding: 6px 8px; text-align: center;">VFW</th>
                <th style="padding: 6px 8px; text-align: center;">T</th>
                <th style="padding: 6px 8px; text-align: center;">Ges.</th>
            </tr>
            {tag_marken_rows}
        </table>

        <h3 style="color: #0066cc; font-size: 12px; margin: 16px 0 6px 0;">{monat_display} – Marken-Split (NW / VFW / T)</h3>
        <table style="border-collapse: collapse; width: 100%; margin-bottom: 4px; font-size: 12px;">
            <tr style="background: #0066cc; color: white;">
                <th style="padding: 6px 8px; text-align: left;">Marke</th>
                <th style="padding: 6px 8px; text-align: center;">NW</th>
                <th style="padding: 6px 8px; text-align: center;">VFW</th>
                <th style="padding: 6px 8px; text-align: center;">T</th>
                <th style="padding: 6px 8px; text-align: center;">Ges.</th>
            </tr>
            {monat_marken_rows}
        </table>

        <p style="margin-top: 12px; font-size: 12px; color: #666;">Weitere Details (z. B. Neuwagen nach Marke/Modell) im PDF-Anhang.</p>
        <p style="color: #999; font-size: 11px; margin-top: 24px; border-top: 1px solid #eee; padding-top: 10px;">
            Automatisch generiert von DRIVE<br>
            <a href="http://drive.auto-greiner.de/verkauf/auftragseingang" style="color: #0066cc;">In DRIVE öffnen</a>
        </p>
    </body>
    </html>
    """

    return {
        "anchor_date": heute_str,
        "datum_display": datum_display,
        "monat_display": monat_display,
        "filename": f"Auftragseingang_{anchor_date.strftime('%Y%m%d')}.pdf",
        "subject": subject,
        "body_html": body_html,
        "pdf_bytes": pdf_bytes,
        "meta": {
            "tag_gesamt": tag_gesamt,
            "monat_gesamt": monat_gesamt,
            "tag_nw": tag_nw,
            "tag_tv": tag_tv,
            "tag_gw": tag_gw,
            "monat_nw": monat_nw,
            "monat_tv": monat_tv,
            "monat_gw": monat_gw,
        },
    }

