"""
Testversand: Einzelnen Report an eine E-Mail-Adresse senden.
Für Admin-Oberfläche (Rechte → E-Mail Reports → Verwalten → Testversand).

Unterstützte Reports: alle TEK-Varianten, ggf. erweiterbar.
"""

from typing import Optional, Tuple


def send_report_test(
    report_id: str,
    email: str,
    standort: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Sendet genau einen Report an eine E-Mail-Adresse (Testversand).

    Args:
        report_id: Report-ID aus der Registry (z.B. tek_daily, tek_service).
        email: E-Mail-Adresse des Empfängers.
        standort: Optional; bei standortfähigen Reports nur diese Variante (DEG/LAN).

    Returns:
        (success, message)
    """
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        return False, "Ungültige E-Mail-Adresse"

    try:
        from reports.registry import get_report, report_exists
        from api.graph_mail_connector import GraphMailConnector
        from datetime import date
    except ImportError as e:
        return False, f"Import fehlgeschlagen: {e}"

    if not report_exists(report_id):
        return False, f"Report '{report_id}' nicht gefunden"

    report = get_report(report_id)
    script = (report or {}).get("script", "")

    # Nur Report-Typen mit direktem Versand unterstützen (keine Celery-Alarme)
    if "celery_app" in script or "alarm" in report_id.lower():
        return False, "Testversand für diesen Report-Typ nicht verfügbar"

    heute = date.today()

    try:
        connector = GraphMailConnector()
    except Exception as e:
        return False, f"E-Mail-Verbindung fehlgeschlagen: {e}"

    # TEK-Reports (send_daily_tek.py)
    if "send_daily_tek" in script:
        return _send_tek_report_test(
            connector, report_id, email, standort, heute
        )

    # Auftragseingang
    if "send_daily_auftragseingang" in script:
        return _send_auftragseingang_test(connector, email, heute)

    # Werkstatt Tagesbericht
    if "werkstatt_tagesbericht" in script:
        return _send_werkstatt_tagesbericht_test(connector, email, standort, heute)

    # AfA Bestand Abgleich
    if report_id == "afa_bestand_report" or "send_afa_bestand_report" in script:
        return _send_afa_bestand_report_test(connector, email, heute)

    return False, "Testversand für diesen Report noch nicht implementiert"


def _send_tek_report_test(connector, report_id: str, email: str, standort: Optional[str], heute) -> Tuple[bool, str]:
    """TEK-Reports: Dispatcher nach report_id."""
    from scripts.send_daily_tek import (
        send_gesamt_reports,
        send_filiale_reports,
        send_bereich_reports,
        send_verkauf_reports,
        send_service_reports,
        TEK_REPORT_TYPES,
    )

    try:
        count = 0
        if report_id == "tek_daily":
            count = send_gesamt_reports(connector, heute, test_email=email)
        elif report_id == "tek_filiale":
            count = send_filiale_reports(connector, heute, test_email=email, test_standort=standort)
        elif report_id in ("tek_nw", "tek_gw", "tek_teile", "tek_werkstatt"):
            config = TEK_REPORT_TYPES.get(report_id, {})
            bereich_key = config.get("bereich_key")
            if not bereich_key:
                return False, f"Konfiguration für {report_id} fehlt"
            count = send_bereich_reports(
                connector, heute, report_id, bereich_key, test_email=email
            )
        elif report_id == "tek_verkauf":
            count = send_verkauf_reports(
                connector, heute, test_email=email, test_standort=standort
            )
        elif report_id == "tek_service":
            count = send_service_reports(
                connector, heute, test_email=email, test_standort=standort
            )
        else:
            return False, f"Unbekannter TEK-Report: {report_id}"

        if count > 0:
            return True, f"Report wurde an {email} gesendet."
        return False, "Keine E-Mail wurde versendet (kein Inhalt für gewählten Standort?)."
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)


def _send_afa_bestand_report_test(connector, email: str, heute) -> Tuple[bool, str]:
    """AfA Bestand Abgleich – Testversand an eine Adresse."""
    try:
        from scripts.send_afa_bestand_report import send_reports
        count = send_reports(connector, test_email=email)
        if count > 0:
            return True, f"AfA Bestand Report wurde an {email} gesendet."
        return False, "Keine E-Mail versendet."
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)


def _send_auftragseingang_test(connector, email: str, heute) -> Tuple[bool, str]:
    """Auftragseingang-Report an eine Adresse senden (Daten aus VerkaufData, SSOT)."""
    try:
        from datetime import datetime
        from scripts.send_daily_auftragseingang import ABSENDER, MONATE
        from api.pdf_generator import generate_auftragseingang_komplett_pdf
        from api.verkauf_data import VerkaufData
        from utils.werktage import get_werktage_monat

        heute_str = heute.strftime("%Y-%m-%d")
        datum_display = heute.strftime("%d.%m.%Y")
        monat_display = f"{MONATE[heute.month]} {heute.year}"

        res_tag = VerkaufData.get_auftragseingang_detail(day=heute_str)
        res_monat = VerkaufData.get_auftragseingang_detail(month=heute.month, year=heute.year)
        tag_data = res_tag.get("verkaufer", []) if res_tag.get("success") else []
        monat_data = res_monat.get("verkaufer", []) if res_monat.get("success") else []
        get_nw = getattr(VerkaufData, "get_auftragseingang_nw_marke_modell", None)
        if get_nw:
            nw_tag = get_nw(day=heute_str)
            nw_monat = get_nw(month=heute.month, year=heute.year)
        else:
            nw_tag = []
            nw_monat = []
        tag_gesamt = sum(v.get("summe_gesamt", 0) for v in tag_data)
        monat_gesamt = sum(v.get("summe_gesamt", 0) for v in monat_data)
        wt = get_werktage_monat(heute.year, heute.month)
        ae_pro_tag = (monat_gesamt / wt["vergangen"]) if wt["vergangen"] > 0 else 0
        prognose_ae = round(ae_pro_tag * wt["gesamt"]) if wt["vergangen"] > 0 else None
        tag_nw = sum(v.get("summe_neu", 0) for v in tag_data)
        tag_tv = sum(v.get("summe_test_vorfuehr", 0) for v in tag_data)
        tag_gw = sum(v.get("summe_gebraucht", 0) for v in tag_data)
        monat_nw = sum(v.get("summe_neu", 0) for v in monat_data)
        monat_tv = sum(v.get("summe_test_vorfuehr", 0) for v in monat_data)
        monat_gw = sum(v.get("summe_gebraucht", 0) for v in monat_data)

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
        # Aufschlüsselung Heute / Monat nach Verkäufer (wie täglicher Report)
        tag_rows_html = ""
        for vk in sorted(tag_data, key=lambda x: x.get("summe_gesamt", 0), reverse=True):
            if vk.get("summe_gesamt", 0) > 0:
                name = (vk.get("verkaufer_name") or "Unbekannt")[:28]
                tag_rows_html += f"""
                <tr style="background: #f8f9fa;"><td style="padding: 6px 8px;">{name}</td>
                    <td style="padding: 6px 8px; text-align: center;">{vk.get('summe_neu', 0)}</td>
                    <td style="padding: 6px 8px; text-align: center;">{vk.get('summe_test_vorfuehr', 0)}</td>
                    <td style="padding: 6px 8px; text-align: center;">{vk.get('summe_gebraucht', 0)}</td>
                    <td style="padding: 6px 8px; text-align: center; font-weight: bold;">{vk.get('summe_gesamt', 0)}</td></tr>"""
        if not tag_rows_html:
            tag_rows_html = '<tr style="background: #f8f9fa;"><td colspan="5" style="padding: 8px; color: #666;">Keine Aufträge heute.</td></tr>'
        monat_rows_html = ""
        for vk in sorted(monat_data, key=lambda x: x.get("summe_gesamt", 0), reverse=True):
            if vk.get("summe_gesamt", 0) > 0:
                name = (vk.get("verkaufer_name") or "Unbekannt")[:28]
                monat_rows_html += f"""
                <tr style="background: #fff;"><td style="padding: 6px 8px;">{name}</td>
                    <td style="padding: 6px 8px; text-align: center;">{vk.get('summe_neu', 0)}</td>
                    <td style="padding: 6px 8px; text-align: center;">{vk.get('summe_test_vorfuehr', 0)}</td>
                    <td style="padding: 6px 8px; text-align: center;">{vk.get('summe_gebraucht', 0)}</td>
                    <td style="padding: 6px 8px; text-align: center; font-weight: bold;">{vk.get('summe_gesamt', 0)}</td></tr>"""
        monat_rows_html += f"""
                <tr style="background: #e7f1ff; font-weight: bold;"><td style="padding: 6px 8px;">GESAMT</td>
                    <td style="padding: 6px 8px; text-align: center;">{monat_nw}</td>
                    <td style="padding: 6px 8px; text-align: center;">{monat_tv}</td>
                    <td style="padding: 6px 8px; text-align: center;">{monat_gw}</td>
                    <td style="padding: 6px 8px; text-align: center;">{monat_gesamt}</td></tr>"""
        werktage_text = f"Werktage: {wt['vergangen']} von {wt['gesamt']} vergangen ({wt['verbleibend']} verbleibend)"
        if wt["vergangen"] > 0 and prognose_ae is not None:
            ae_pt = round(ae_pro_tag, 1)
            werktage_text += f" · Prognose: <strong>{prognose_ae} AE</strong> (aktuell {ae_pt} AE/Tag)"

        betreff = f"Auftragseingang {datum_display} - Heute: {tag_gesamt} | Monat: {monat_gesamt}"
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

            <p style="margin-top: 12px; font-size: 12px; color: #666;">Neuwagen nach Marke/Modell weiterhin im PDF-Anhang.</p>
            <p style="color: #999; font-size: 11px; margin-top: 24px; border-top: 1px solid #eee; padding-top: 10px;">Automatisch generiert von DRIVE</p>
        </body>
        </html>
        """
        connector.send_mail(
            sender_email=ABSENDER,
            to_emails=[email],
            subject=betreff,
            body_html=body_html,
            attachments=[{
                "name": f"Auftragseingang_{heute.strftime('%Y%m%d')}.pdf",
                "content": pdf_bytes,
                "content_type": "application/pdf",
            }],
        )
        return True, f"Report wurde an {email} gesendet."
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)


def _send_werkstatt_tagesbericht_test(
    connector, email: str, standort: Optional[str], heute
) -> Tuple[bool, str]:
    """Werkstatt Tagesbericht: Testversand noch nicht unterstützt (Script ohne test_email)."""
    return False, "Testversand für Werkstatt Tagesbericht derzeit nicht verfügbar."
