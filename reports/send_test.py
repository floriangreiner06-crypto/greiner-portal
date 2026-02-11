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


def _send_auftragseingang_test(connector, email: str, heute) -> Tuple[bool, str]:
    """Auftragseingang-Report an eine Adresse senden."""
    try:
        from datetime import datetime
        from scripts.send_daily_auftragseingang import (
            get_auftragseingang_data,
            ABSENDER,
            MONATE,
        )
        from api.pdf_generator import generate_auftragseingang_komplett_pdf

        heute_str = heute.strftime("%Y-%m-%d")
        datum_display = heute.strftime("%d.%m.%Y")
        monat_display = f"{MONATE[heute.month]} {heute.year}"

        tag_data = get_auftragseingang_data(day=heute_str)
        monat_data = get_auftragseingang_data(month=heute.month, year=heute.year)

        tag_gesamt = sum(v.get("summe_gesamt", 0) for v in tag_data)
        monat_gesamt = sum(v.get("summe_gesamt", 0) for v in monat_data)
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
        )
        betreff = f"Auftragseingang {datum_display} - Heute: {tag_gesamt} | Monat: {monat_gesamt}"
        body_html = f"""
        <html><body style="font-family: Arial, sans-serif; color: #333; max-width: 600px;">
            <h2 style="color: #0066cc;">Auftragseingang</h2>
            <p style="color: #666;">Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr</p>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background: #333; color: white;">
                    <th style="padding: 12px;"></th>
                    <th style="padding: 12px; text-align: center;">NW</th>
                    <th style="padding: 12px; text-align: center;">T/V</th>
                    <th style="padding: 12px; text-align: center;">GW</th>
                    <th style="padding: 12px; text-align: center;">GESAMT</th>
                </tr>
                <tr style="background: #e6f2ff;">
                    <td style="padding: 12px; font-weight: bold;">Heute</td>
                    <td style="padding: 12px; text-align: center;">{tag_nw}</td>
                    <td style="padding: 12px; text-align: center;">{tag_tv}</td>
                    <td style="padding: 12px; text-align: center;">{tag_gw}</td>
                    <td style="padding: 12px; text-align: center; font-weight: bold;">{tag_gesamt}</td>
                </tr>
                <tr style="background: #fff3cd;">
                    <td style="padding: 12px; font-weight: bold;">{monat_display}</td>
                    <td style="padding: 12px; text-align: center;">{monat_nw}</td>
                    <td style="padding: 12px; text-align: center;">{monat_tv}</td>
                    <td style="padding: 12px; text-align: center;">{monat_gw}</td>
                    <td style="padding: 12px; text-align: center; font-weight: bold;">{monat_gesamt}</td>
                </tr>
            </table>
            <p>Details im PDF-Anhang.</p>
            <p style="color: #999; font-size: 11px;">Automatisch generiert von DRIVE</p>
        </body></html>
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
