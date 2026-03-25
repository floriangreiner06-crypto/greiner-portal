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

    # AfA Verkaufsempfehlungen (20 älteste)
    if report_id == "afa_verkaufsempfehlungen_report" or "send_afa_verkaufsempfehlungen_report" in script:
        return _send_afa_verkaufsempfehlungen_report_test(connector, email, heute)

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


def _send_afa_verkaufsempfehlungen_report_test(connector, email: str, heute) -> Tuple[bool, str]:
    """AfA Verkaufsempfehlungen (20 älteste) – Testversand an eine Adresse."""
    try:
        from scripts.send_afa_verkaufsempfehlungen_report import send_reports
        count = send_reports(connector, test_email=email)
        if count > 0:
            return True, f"AfA Verkaufsempfehlungen Report wurde an {email} gesendet."
        return False, "Keine E-Mail versendet."
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)


def _send_auftragseingang_test(connector, email: str, heute) -> Tuple[bool, str]:
    """Auftragseingang-Report – identisch zum täglichen Job (SSOT-Builder)."""
    try:
        from scripts.send_daily_auftragseingang import ABSENDER
        from reports.auftragseingang_report_builder import build_auftragseingang_report_package

        pkg = build_auftragseingang_report_package(heute)
        connector.send_mail(
            sender_email=ABSENDER,
            to_emails=[email],
            subject=pkg["subject"],
            body_html=pkg["body_html"],
            attachments=[{
                "name": pkg["filename"],
                "content": pkg["pdf_bytes"],
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
