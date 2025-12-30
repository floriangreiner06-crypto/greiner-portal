#!/usr/bin/env python3
"""
Carloop Scraper - Extrahiert Reservierungen aus Carloop Web-UI
==============================================================
Da Carloop keine API hat, scrapen wir die Daten aus der Web-Oberfläche.

Erstellt: TAG 131 (2025-12-20)
"""
import requests
import re
import json
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Carloop Credentials
CARLOOP_URL = "https://www.carloop-vermietsystem.de"
CARLOOP_USER = "admin100328"
CARLOOP_PASS = "Opel1234!"


@dataclass
class CarloopReservierung:
    """Eine Mietwagen-Reservierung aus Carloop."""
    reservierung_id: str
    kennzeichen: str
    fahrzeug_modell: str
    kunde_name: str
    kunde_nr: Optional[str]
    von: datetime
    bis: datetime
    status: str  # reserviert, ausgegeben, zurück
    tarif: Optional[str]
    bemerkung: Optional[str]
    carloop_url: Optional[str]


class CarloopScraper:
    """Scraper für Carloop Mietwagen-System."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
        })
        self._logged_in = False

    def login(self) -> bool:
        """Login bei Carloop."""
        try:
            # Initiale Seite für Cookies
            self.session.get(f"{CARLOOP_URL}/de/Portal/Authentifizierung")
            # Login POST
            r = self.session.post(
                f"{CARLOOP_URL}/de/Portal/Authentifizierung",
                data={
                    "username": CARLOOP_USER,
                    "password": CARLOOP_PASS,
                    "login": "Anmelden"
                },
                allow_redirects=True
            )
            if "Abmelden" in r.text:
                self._logged_in = True
                logger.info("Carloop Login erfolgreich")
                return True
            logger.error("Carloop Login fehlgeschlagen")
            return False
        except Exception as e:
            logger.error(f"Carloop Login Error: {e}")
            return False

    def get_reservierungen(self, von: date = None, bis: date = None) -> List[CarloopReservierung]:
        """
        Holt Reservierungen aus Carloop.

        Args:
            von: Startdatum (default: heute - 7 Tage)
            bis: Enddatum (default: heute + 30 Tage)
        """
        if not self._logged_in:
            if not self.login():
                return []

        if von is None:
            von = date.today() - timedelta(days=7)
        if bis is None:
            bis = date.today() + timedelta(days=30)

        reservierungen = []

        # Methode 1: Vermietungsübersicht scrapen
        try:
            reservierungen = self._scrape_vermietung_uebersicht()
        except Exception as e:
            logger.error(f"Fehler beim Scrapen der Übersicht: {e}")

        # Filter nach Zeitraum
        reservierungen = [
            r for r in reservierungen
            if r.von.date() <= bis and r.bis.date() >= von
        ]

        return reservierungen

    def _scrape_vermietung_uebersicht(self) -> List[CarloopReservierung]:
        """Scrapt die Vermietungsübersicht-Seite."""
        reservierungen = []

        # Verschiedene Status-Seiten durchgehen
        status_urls = [
            "/de/Mobilitaets-Manager/Vermietung/index/group/reservation",  # Reservierungen
            "/de/Mobilitaets-Manager/Vermietung/index/group/handover",     # Ausgegeben
            "/de/Mobilitaets-Manager/Vermietung/index/group/all",          # Alle
        ]

        for url_suffix in status_urls:
            try:
                r = self.session.get(f"{CARLOOP_URL}{url_suffix}")
                if r.status_code != 200:
                    continue

                # Tabellen-Zeilen parsen
                parsed = self._parse_vermietung_tabelle(r.text, url_suffix)

                # Duplikate vermeiden (nach reservierung_id)
                existing_ids = {res.reservierung_id for res in reservierungen}
                for res in parsed:
                    if res.reservierung_id not in existing_ids:
                        reservierungen.append(res)
                        existing_ids.add(res.reservierung_id)

            except Exception as e:
                logger.error(f"Fehler bei {url_suffix}: {e}")

        return reservierungen

    def _parse_vermietung_tabelle(self, html: str, url_suffix: str) -> List[CarloopReservierung]:
        """Parst HTML-Tabelle mit Vermietungen."""
        reservierungen = []

        # Status aus URL ableiten
        if "reservation" in url_suffix:
            default_status = "reserviert"
        elif "handover" in url_suffix:
            default_status = "ausgegeben"
        else:
            default_status = "unbekannt"

        # Tabellen-Body finden
        tbody_match = re.search(r'<tbody[^>]*>(.*?)</tbody>', html, re.DOTALL)
        if not tbody_match:
            return []

        tbody = tbody_match.group(1)

        # Zeilen parsen
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody, re.DOTALL)

        for row in rows:
            try:
                res = self._parse_row(row, default_status)
                if res:
                    reservierungen.append(res)
            except Exception as e:
                logger.debug(f"Zeile übersprungen: {e}")

        return reservierungen

    def _parse_row(self, row_html: str, default_status: str) -> Optional[CarloopReservierung]:
        """Parst eine Tabellenzeile zu einer Reservierung."""
        # Zellen extrahieren
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL)
        if len(cells) < 5:
            return None

        # Bereinigen
        def clean(html):
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

        # Reservierungs-ID aus Link extrahieren
        id_match = re.search(r'rentalId[/=](\d+)', row_html)
        res_id = id_match.group(1) if id_match else f"unknown_{hash(row_html) % 10000}"

        # Kennzeichen finden (Format: XXX-XX 123 oder XXX-XX123)
        plate_match = re.search(r'([A-Z]{2,3}[-\s]?[A-Z]{1,2}[-\s]?\d{1,4})', row_html)
        kennzeichen = plate_match.group(1) if plate_match else ""

        # Fahrzeugmodell (oft in der gleichen Zelle wie Kennzeichen)
        modell = ""
        for cell in cells:
            if kennzeichen and kennzeichen in cell:
                # Text vor/nach Kennzeichen könnte Modell sein
                modell_match = re.search(r'([A-Za-z]+(?:\s+[A-Za-z]+)?)\s*' + re.escape(kennzeichen), cell)
                if modell_match:
                    modell = modell_match.group(1).strip()
                break

        # Kunde (meist Name, Vorname Format)
        kunde_name = ""
        for cell in cells:
            clean_cell = clean(cell)
            if re.match(r'^[A-Za-zäöüÄÖÜß]+,\s*[A-Za-zäöüÄÖÜß]+', clean_cell):
                kunde_name = clean_cell
                break

        # Datums-Felder finden (Format: DD.MM.YYYY oder DD.MM.YYYY HH:MM)
        dates = re.findall(r'(\d{2}\.\d{2}\.\d{4})(?:\s+(\d{2}:\d{2}))?', row_html)

        von = datetime.now()
        bis = datetime.now() + timedelta(days=1)

        if len(dates) >= 1:
            try:
                von_str = dates[0][0]
                von_time = dates[0][1] if dates[0][1] else "08:00"
                von = datetime.strptime(f"{von_str} {von_time}", "%d.%m.%Y %H:%M")
            except:
                pass

        if len(dates) >= 2:
            try:
                bis_str = dates[1][0]
                bis_time = dates[1][1] if dates[1][1] else "18:00"
                bis = datetime.strptime(f"{bis_str} {bis_time}", "%d.%m.%Y %H:%M")
            except:
                pass

        # Status aus Zeilen-Klasse oder Badge
        status = default_status
        if 'status-active' in row_html or 'ausgegeben' in row_html.lower():
            status = "ausgegeben"
        elif 'status-reserved' in row_html or 'reserviert' in row_html.lower():
            status = "reserviert"
        elif 'status-returned' in row_html or 'zurück' in row_html.lower():
            status = "zurück"

        if not kennzeichen:
            return None

        return CarloopReservierung(
            reservierung_id=res_id,
            kennzeichen=kennzeichen,
            fahrzeug_modell=modell,
            kunde_name=kunde_name,
            kunde_nr=None,
            von=von,
            bis=bis,
            status=status,
            tarif=None,
            bemerkung=None,
            carloop_url=f"{CARLOOP_URL}/de/Mobilitaets-Manager/Vermietung/Anzeigen/rentalId/{res_id}"
        )

    def get_fahrzeuge(self) -> List[Dict]:
        """Holt die Fahrzeugliste aus Carloop."""
        if not self._logged_in:
            if not self.login():
                return []

        fahrzeuge = []

        try:
            # Widget-Seite hat die Fahrzeugliste
            r = self.session.get(f"{CARLOOP_URL}/de/Mobilitaets-Manager/Schnittstelle/Bearbeiten/rentWidgetId/455")

            # Fahrzeuge aus Labels extrahieren (Format: "Modell (Kennzeichen)")
            matches = re.findall(r'<label[^>]*>([^<]*\(([A-Z]{2,3}-[A-Z]{2,3}\d+)\)[^<]*)</label>', r.text)

            for full_text, kennzeichen in matches:
                modell = full_text.split('(')[0].strip()
                fahrzeuge.append({
                    'kennzeichen': kennzeichen,
                    'modell': modell,
                })
        except Exception as e:
            logger.error(f"Fehler beim Laden der Fahrzeuge: {e}")

        return fahrzeuge


# Singleton für einfache Nutzung
_scraper: Optional[CarloopScraper] = None

def get_carloop_scraper() -> CarloopScraper:
    """Holt Singleton-Instanz des Scrapers."""
    global _scraper
    if _scraper is None:
        _scraper = CarloopScraper()
    return _scraper


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    scraper = get_carloop_scraper()

    print("=== Carloop Fahrzeuge ===")
    fahrzeuge = scraper.get_fahrzeuge()
    for f in fahrzeuge[:5]:
        print(f"  {f['kennzeichen']}: {f['modell']}")
    print(f"  ... ({len(fahrzeuge)} gesamt)")

    print("\n=== Carloop Reservierungen ===")
    reservierungen = scraper.get_reservierungen()
    for r in reservierungen[:10]:
        print(f"  {r.kennzeichen}: {r.kunde_name} ({r.von.strftime('%d.%m')} - {r.bis.strftime('%d.%m')}) [{r.status}]")
    print(f"  ... ({len(reservierungen)} gesamt)")
