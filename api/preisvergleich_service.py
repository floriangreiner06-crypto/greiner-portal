#!/usr/bin/env python3
"""
Preisvergleich Service für Penner-Teile
=======================================
Automatischer Marktpreis-Abruf von eBay, Daparto etc.

Features:
- eBay.de Scraping (kostenlos, mit Rate-Limits)
- Daparto Preisvergleich
- 24h Cache in PostgreSQL
- Ampel-System für Verkaufschancen

Erstellt: TAG 142 (2025-12-29)
"""

import os
import re
import json
import time
import logging
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from decimal import Decimal
import threading

import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import RealDictCursor

# Logging
logger = logging.getLogger(__name__)

# =============================================================================
# KONFIGURATION
# =============================================================================

# Rate-Limits (Sekunden zwischen Requests)
RATE_LIMIT_EBAY = 2.0
RATE_LIMIT_DAPARTO = 1.5
RATE_LIMIT_GOOGLE = 3.0

# Cache-Dauer
CACHE_DURATION_HOURS = 24

# Mindest-Lagerwert für automatische Abfrage
MIN_LAGERWERT_AUTO = 50.0

# Lagerkosten pro Jahr (10% p.a.)
LAGERKOSTEN_PRO_JAHR = 0.10

# User-Agent für Requests (wichtig für Scraping)
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Drive Portal PostgreSQL
DRIVE_DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'drive_portal',
    'user': 'greiner',
    'password': os.getenv('DRIVE_DB_PASSWORD', 'greiner2024')
}

# Locosoft PostgreSQL
LOCOSOFT_DB_CONFIG = {
    'host': '10.80.80.8',
    'port': 5432,
    'database': 'loco_auswertung_db',
    'user': 'loco_auswertung_benutzer',
    'password': 'loco'
}


# =============================================================================
# DATABASE CONNECTIONS
# =============================================================================

def get_drive_connection():
    """Verbindung zur Drive Portal DB."""
    return psycopg2.connect(**DRIVE_DB_CONFIG)


def get_locosoft_connection():
    """Verbindung zur Locosoft DB."""
    return psycopg2.connect(**LOCOSOFT_DB_CONFIG)


# =============================================================================
# SCRAPING FUNKTIONEN
# =============================================================================

class PreisvergleichService:
    """
    Service für automatischen Marktpreis-Abruf.

    Usage:
        service = PreisvergleichService()

        # Einzelnes Teil abfragen
        result = service.get_marktpreis('1K0 615 301 AA')

        # Alle Penner aktualisieren
        service.update_all_penner(min_lagerwert=50)
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton Pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
        })
        self._last_request = {}

    def _rate_limit(self, source: str, delay: float):
        """Rate-Limiting pro Quelle."""
        last = self._last_request.get(source, 0)
        elapsed = time.time() - last
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last_request[source] = time.time()

    # =========================================================================
    # EBAY.DE SCRAPING
    # =========================================================================

    def scrape_ebay(self, teilenummer: str) -> Dict:
        """
        Scraped eBay.de Suchergebnisse.

        Args:
            teilenummer: OE-Nummer des Teils

        Returns:
            {
                'source': 'ebay',
                'success': True/False,
                'anzahl_angebote': int,
                'preis_min': float,
                'preis_max': float,
                'preis_avg': float,
                'angebote': [{'titel': str, 'preis': float, 'url': str}, ...]
            }
        """
        self._rate_limit('ebay', RATE_LIMIT_EBAY)

        result = {
            'source': 'ebay',
            'success': False,
            'anzahl_angebote': 0,
            'preis_min': None,
            'preis_max': None,
            'preis_avg': None,
            'angebote': [],
            'error': None
        }

        try:
            # Teilenummer bereinigen
            tnr_clean = teilenummer.replace(' ', '').replace('-', '')
            url = f"https://www.ebay.de/sch/i.html?_nkw={urllib.parse.quote(tnr_clean)}&_sacat=131090&LH_BIN=1"

            response = self._session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            preise = []
            angebote = []

            # eBay Suchergebnisse parsen
            for item in soup.select('.s-item'):
                # Preis extrahieren
                preis_elem = item.select_one('.s-item__price')
                if not preis_elem:
                    continue

                preis_text = preis_elem.get_text()

                # "EUR 45,99" -> 45.99
                match = re.search(r'(\d+)[,.](\d{2})', preis_text)
                if match:
                    preis = float(f"{match.group(1)}.{match.group(2)}")

                    # Nur realistische Preise (1€ - 5000€)
                    if 1 <= preis <= 5000:
                        preise.append(preis)

                        # Titel und Link
                        titel_elem = item.select_one('.s-item__title')
                        link_elem = item.select_one('.s-item__link')

                        angebote.append({
                            'titel': titel_elem.get_text() if titel_elem else '',
                            'preis': preis,
                            'url': link_elem.get('href') if link_elem else ''
                        })

            if preise:
                result['success'] = True
                result['anzahl_angebote'] = len(preise)
                result['preis_min'] = min(preise)
                result['preis_max'] = max(preise)
                result['preis_avg'] = round(sum(preise) / len(preise), 2)
                result['angebote'] = angebote[:10]  # Max 10 Angebote

            logger.info(f"eBay Scraping {teilenummer}: {len(preise)} Angebote gefunden")

        except requests.RequestException as e:
            result['error'] = f"Request failed: {str(e)}"
            logger.warning(f"eBay Scraping {teilenummer} fehlgeschlagen: {e}")
        except Exception as e:
            result['error'] = str(e)
            logger.exception(f"eBay Scraping {teilenummer} Fehler")

        return result

    # =========================================================================
    # DAPARTO SCRAPING
    # =========================================================================

    def scrape_daparto(self, teilenummer: str) -> Dict:
        """
        Scraped Daparto.de Preisvergleich.

        Args:
            teilenummer: OE-Nummer des Teils

        Returns:
            Dict mit Preisdaten
        """
        self._rate_limit('daparto', RATE_LIMIT_DAPARTO)

        result = {
            'source': 'daparto',
            'success': False,
            'anzahl_angebote': 0,
            'preis_min': None,
            'preis_max': None,
            'preis_avg': None,
            'angebote': [],
            'error': None
        }

        try:
            tnr_clean = teilenummer.replace(' ', '').replace('-', '')
            url = f"https://www.daparto.de/Suche?q={urllib.parse.quote(tnr_clean)}"

            response = self._session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            preise = []
            angebote = []

            # Daparto Produkt-Cards parsen
            for item in soup.select('.product-card, .article-item, [data-price]'):
                # Preis aus data-attribute oder Text
                preis_attr = item.get('data-price')
                if preis_attr:
                    try:
                        preis = float(preis_attr)
                        preise.append(preis)
                        continue
                    except ValueError:
                        pass

                # Fallback: Text parsen
                preis_elem = item.select_one('.price, .product-price')
                if preis_elem:
                    preis_text = preis_elem.get_text()
                    match = re.search(r'(\d+)[,.](\d{2})', preis_text)
                    if match:
                        preis = float(f"{match.group(1)}.{match.group(2)}")
                        if 1 <= preis <= 5000:
                            preise.append(preis)

            if preise:
                result['success'] = True
                result['anzahl_angebote'] = len(preise)
                result['preis_min'] = min(preise)
                result['preis_max'] = max(preise)
                result['preis_avg'] = round(sum(preise) / len(preise), 2)

            logger.info(f"Daparto Scraping {teilenummer}: {len(preise)} Angebote gefunden")

        except requests.RequestException as e:
            result['error'] = f"Request failed: {str(e)}"
            logger.warning(f"Daparto Scraping {teilenummer} fehlgeschlagen: {e}")
        except Exception as e:
            result['error'] = str(e)
            logger.exception(f"Daparto Scraping {teilenummer} Fehler")

        return result

    # =========================================================================
    # MARKTPREIS AGGREGATION
    # =========================================================================

    def get_marktpreis(self, teilenummer: str, use_cache: bool = True,
                        ek_preis: float = None, tage_seit_abgang: int = None) -> Dict:
        """
        Holt Marktpreise aus allen Quellen.

        Args:
            teilenummer: OE-Nummer
            use_cache: Cache verwenden wenn vorhanden
            ek_preis: EK-Preis für Lagerkosten-Berechnung
            tage_seit_abgang: Lagerzeit in Tagen

        Returns:
            {
                'teilenummer': str,
                'timestamp': str,
                'quellen': [...],
                'zusammenfassung': {
                    'anzahl_quellen': int,
                    'anzahl_angebote': int,
                    'preis_min': float,
                    'preis_max': float,
                    'preis_avg': float
                },
                'empfehlung': {
                    'verkaufspreis': float,
                    'plattform': str,
                    'chance': str,  # hoch/mittel/gering/keine
                    'lagerkosten': float,  # angefallene Lagerkosten
                    'mindestpreis': float,  # EK + Lagerkosten
                    'marge_nach_lagerkosten': float
                }
            }
        """
        # Cache prüfen
        if use_cache:
            cached = self._get_from_cache(teilenummer)
            if cached:
                logger.debug(f"Cache-Hit für {teilenummer}")
                return cached

        # Quellen abfragen
        quellen = []

        # 1. eBay
        ebay_result = self.scrape_ebay(teilenummer)
        quellen.append(ebay_result)

        # 2. Daparto
        daparto_result = self.scrape_daparto(teilenummer)
        quellen.append(daparto_result)

        # Zusammenfassung berechnen
        alle_preise = []
        erfolgreiche_quellen = 0

        for q in quellen:
            if q['success'] and q['preis_avg']:
                erfolgreiche_quellen += 1
                alle_preise.extend([q['preis_min'], q['preis_max']])

        zusammenfassung = {
            'anzahl_quellen': erfolgreiche_quellen,
            'anzahl_angebote': sum(q.get('anzahl_angebote', 0) for q in quellen),
            'preis_min': min(alle_preise) if alle_preise else None,
            'preis_max': max(alle_preise) if alle_preise else None,
            'preis_avg': round(sum(alle_preise) / len(alle_preise), 2) if alle_preise else None
        }

        # Empfehlung generieren (mit Lagerkosten-Berechnung wenn Daten verfügbar)
        empfehlung = self._generate_empfehlung(
            zusammenfassung, quellen,
            ek_preis=ek_preis, tage_seit_abgang=tage_seit_abgang
        )

        result = {
            'teilenummer': teilenummer,
            'timestamp': datetime.now().isoformat(),
            'quellen': quellen,
            'zusammenfassung': zusammenfassung,
            'empfehlung': empfehlung
        }

        # In Cache speichern
        self._save_to_cache(teilenummer, result)

        return result

    def _generate_empfehlung(self, zusammenfassung: Dict, quellen: List,
                              ek_preis: float = None, tage_seit_abgang: int = None) -> Dict:
        """
        Generiert Verkaufsempfehlung basierend auf Marktdaten und Lagerkosten.

        Die Empfehlung berücksichtigt:
        - Marktpreise (eBay, Daparto)
        - Lagerkosten (10% p.a. auf EK-Preis)
        - Mindestverkaufspreis = EK + angefallene Lagerkosten

        Args:
            zusammenfassung: Preisstatistik aus Marktdaten
            quellen: Liste der Datenquellen
            ek_preis: Einkaufspreis des Teils
            tage_seit_abgang: Tage seit letztem Verkauf (Lagerzeit)

        Returns:
            Empfehlung mit Verkaufspreis, Plattform, Chance und Lagerkosten-Info
        """
        empfehlung = {
            'verkaufspreis': None,
            'plattform': None,
            'chance': 'unbekannt',
            'lagerkosten': None,
            'mindestpreis': None,
            'marge_nach_lagerkosten': None
        }

        anzahl = zusammenfassung.get('anzahl_angebote', 0)
        preis_avg = zusammenfassung.get('preis_avg')

        if anzahl == 0 or preis_avg is None:
            empfehlung['chance'] = 'keine'
            return empfehlung

        # Beste Plattform ermitteln (mit meisten Angeboten)
        beste_quelle = max(quellen, key=lambda q: q.get('anzahl_angebote', 0))
        empfehlung['plattform'] = beste_quelle.get('source', 'ebay')

        # Lagerkosten berechnen (10% p.a.)
        lagerkosten = 0.0
        mindestpreis = 0.0

        if ek_preis and ek_preis > 0 and tage_seit_abgang and tage_seit_abgang > 0:
            # Lagerkosten = EK * (Tage/365) * 10%
            lagerkosten = ek_preis * (tage_seit_abgang / 365.0) * LAGERKOSTEN_PRO_JAHR
            lagerkosten = round(lagerkosten, 2)

            # Mindestverkaufspreis = EK + Lagerkosten (Breakeven)
            mindestpreis = ek_preis + lagerkosten
            mindestpreis = round(mindestpreis, 2)

            empfehlung['lagerkosten'] = lagerkosten
            empfehlung['mindestpreis'] = mindestpreis

        # Verkaufspreis bestimmen
        # Strategie: 10% unter Marktdurchschnitt, aber nicht unter Mindestpreis
        markt_vk = round(preis_avg * 0.9, 2)

        if mindestpreis > 0 and markt_vk < mindestpreis:
            # Marktpreis zu niedrig - setze auf Mindestpreis
            empfehlung['verkaufspreis'] = mindestpreis
            empfehlung['marge_nach_lagerkosten'] = 0.0
        else:
            empfehlung['verkaufspreis'] = markt_vk
            if mindestpreis > 0:
                empfehlung['marge_nach_lagerkosten'] = round(markt_vk - mindestpreis, 2)

        # Chance bewerten (kombiniert Angebote + Rentabilität)
        if anzahl >= 10:
            if empfehlung['marge_nach_lagerkosten'] is None or empfehlung['marge_nach_lagerkosten'] >= 0:
                empfehlung['chance'] = 'hoch'
            else:
                empfehlung['chance'] = 'mittel'  # Viele Angebote aber unter Lagerkosten
        elif anzahl >= 3:
            if empfehlung['marge_nach_lagerkosten'] is None or empfehlung['marge_nach_lagerkosten'] >= 0:
                empfehlung['chance'] = 'mittel'
            else:
                empfehlung['chance'] = 'gering'
        else:
            empfehlung['chance'] = 'gering'

        return empfehlung

    # =========================================================================
    # CACHE FUNKTIONEN
    # =========================================================================

    def _get_from_cache(self, teilenummer: str) -> Optional[Dict]:
        """Holt Marktpreis aus Cache wenn nicht älter als 24h."""
        try:
            conn = get_drive_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT * FROM penner_marktpreise
                WHERE part_number = %s
                AND abgefragt_am > NOW() - INTERVAL '%s hours'
            """, [teilenummer, CACHE_DURATION_HOURS])

            row = cur.fetchone()
            cur.close()
            conn.close()

            if row:
                return {
                    'teilenummer': row['part_number'],
                    'timestamp': row['abgefragt_am'].isoformat() if row['abgefragt_am'] else None,
                    'cached': True,
                    'zusammenfassung': {
                        'anzahl_quellen': row['anzahl_quellen'],
                        'anzahl_angebote': row['anzahl_angebote'],
                        'preis_min': float(row['preis_min']) if row['preis_min'] else None,
                        'preis_max': float(row['preis_max']) if row['preis_max'] else None,
                        'preis_avg': float(row['preis_avg']) if row['preis_avg'] else None
                    },
                    'empfehlung': {
                        'verkaufspreis': float(row['empf_verkaufspreis']) if row['empf_verkaufspreis'] else None,
                        'plattform': row['empf_plattform'],
                        'chance': row['verkaufschance']
                    },
                    'quellen': json.loads(row['raw_data']) if row['raw_data'] else []
                }

        except Exception as e:
            logger.warning(f"Cache-Abruf fehlgeschlagen: {e}")

        return None

    def _save_to_cache(self, teilenummer: str, data: Dict):
        """Speichert Marktpreis im Cache (inkl. Lagerkosten-Kalkulation)."""
        try:
            conn = get_drive_connection()
            cur = conn.cursor()

            zusammenfassung = data.get('zusammenfassung', {})
            empfehlung = data.get('empfehlung', {})

            cur.execute("""
                INSERT INTO penner_marktpreise (
                    part_number, anzahl_quellen, anzahl_angebote,
                    preis_min, preis_max, preis_avg,
                    empf_verkaufspreis, empf_plattform, verkaufschance,
                    lagerkosten, mindestpreis, marge_nach_lagerkosten,
                    abgefragt_am, aktualisiert_am, raw_data
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s
                )
                ON CONFLICT (part_number)
                DO UPDATE SET
                    anzahl_quellen = EXCLUDED.anzahl_quellen,
                    anzahl_angebote = EXCLUDED.anzahl_angebote,
                    preis_min = EXCLUDED.preis_min,
                    preis_max = EXCLUDED.preis_max,
                    preis_avg = EXCLUDED.preis_avg,
                    empf_verkaufspreis = EXCLUDED.empf_verkaufspreis,
                    empf_plattform = EXCLUDED.empf_plattform,
                    verkaufschance = EXCLUDED.verkaufschance,
                    lagerkosten = EXCLUDED.lagerkosten,
                    mindestpreis = EXCLUDED.mindestpreis,
                    marge_nach_lagerkosten = EXCLUDED.marge_nach_lagerkosten,
                    abgefragt_am = NOW(),
                    aktualisiert_am = NOW(),
                    raw_data = EXCLUDED.raw_data
            """, [
                teilenummer,
                zusammenfassung.get('anzahl_quellen'),
                zusammenfassung.get('anzahl_angebote'),
                zusammenfassung.get('preis_min'),
                zusammenfassung.get('preis_max'),
                zusammenfassung.get('preis_avg'),
                empfehlung.get('verkaufspreis'),
                empfehlung.get('plattform'),
                empfehlung.get('chance', 'unbekannt'),
                empfehlung.get('lagerkosten'),
                empfehlung.get('mindestpreis'),
                empfehlung.get('marge_nach_lagerkosten'),
                json.dumps(data.get('quellen', []))
            ])

            conn.commit()
            cur.close()
            conn.close()

            logger.debug(f"Cache aktualisiert für {teilenummer}")

        except Exception as e:
            logger.exception(f"Cache-Speichern fehlgeschlagen: {e}")

    # =========================================================================
    # BATCH-VERARBEITUNG
    # =========================================================================

    def get_penner_teile(self, min_lagerwert: float = 50.0, limit: int = 500) -> List[Dict]:
        """Holt alle Penner-Teile aus Locosoft."""
        try:
            conn = get_locosoft_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT
                    ps.part_number,
                    pm.description,
                    ps.usage_value as ek_preis,
                    pm.rr_price as vk_preis,
                    ps.stock_level as bestand,
                    ROUND((ps.stock_level * ps.usage_value)::numeric, 2) as lagerwert,
                    (CURRENT_DATE - ps.last_outflow_date) as tage_seit_abgang
                FROM parts_stock ps
                JOIN parts_master pm ON ps.part_number = pm.part_number
                WHERE ps.stock_level > 0
                AND (
                    ps.last_outflow_date < CURRENT_DATE - INTERVAL '365 days'
                    OR ps.last_outflow_date IS NULL
                )
                AND (ps.stock_level * ps.usage_value) >= %s
                AND pm.parts_type NOT IN (1, 60, 65)
                AND UPPER(pm.description) NOT LIKE '%%KAUTION%%'
                AND UPPER(pm.description) NOT LIKE '%%RUECKLAUFTEIL%%'
                ORDER BY (ps.stock_level * ps.usage_value) DESC
                LIMIT %s
            """, [min_lagerwert, limit])

            teile = cur.fetchall()
            cur.close()
            conn.close()

            return [dict(t) for t in teile]

        except Exception as e:
            logger.exception("Fehler beim Laden der Penner-Teile")
            return []

    def update_all_penner(self, min_lagerwert: float = 50.0, limit: int = 100) -> Dict:
        """
        Aktualisiert Marktpreise für alle Penner-Teile.

        Berücksichtigt jetzt auch Lagerkosten (10% p.a.) bei der Empfehlung.

        Args:
            min_lagerwert: Nur Teile mit mindestens diesem Lagerwert
            limit: Maximale Anzahl zu aktualisierender Teile

        Returns:
            {
                'gesamt': int,
                'erfolgreich': int,
                'fehler': int,
                'dauer_sekunden': float
            }
        """
        start = time.time()

        teile = self.get_penner_teile(min_lagerwert, limit)
        logger.info(f"Starte Marktpreis-Update für {len(teile)} Teile (inkl. Lagerkosten-Berechnung)")

        erfolgreich = 0
        fehler = 0

        for i, teil in enumerate(teile):
            try:
                # EK-Preis und Lagerzeit aus Locosoft-Daten für Lagerkosten-Berechnung
                ek_preis = float(teil.get('ek_preis') or 0)
                tage_seit_abgang = int(teil.get('tage_seit_abgang') or 0)

                # Marktpreis abrufen MIT Lagerkosten-Daten
                result = self.get_marktpreis(
                    teil['part_number'],
                    use_cache=False,
                    ek_preis=ek_preis,
                    tage_seit_abgang=tage_seit_abgang
                )

                # Locosoft-Daten in Cache aktualisieren
                self._update_locosoft_data(teil['part_number'], teil)

                if result.get('zusammenfassung', {}).get('anzahl_angebote', 0) > 0:
                    erfolgreich += 1
                else:
                    fehler += 1

                if (i + 1) % 10 == 0:
                    logger.info(f"Fortschritt: {i + 1}/{len(teile)} Teile verarbeitet")

            except Exception as e:
                logger.warning(f"Fehler bei {teil['part_number']}: {e}")
                fehler += 1

        dauer = time.time() - start
        logger.info(f"Update abgeschlossen: {erfolgreich} erfolgreich, {fehler} ohne Angebote, {dauer:.1f}s")

        return {
            'gesamt': len(teile),
            'erfolgreich': erfolgreich,
            'fehler': fehler,
            'dauer_sekunden': round(dauer, 1)
        }

    def _update_locosoft_data(self, teilenummer: str, data: Dict):
        """Aktualisiert Locosoft-Stammdaten im Cache."""
        try:
            conn = get_drive_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE penner_marktpreise SET
                    beschreibung = %s,
                    ek_preis = %s,
                    vk_preis = %s,
                    bestand = %s,
                    lagerwert = %s,
                    tage_seit_abgang = %s
                WHERE part_number = %s
            """, [
                data.get('description'),
                data.get('ek_preis'),
                data.get('vk_preis'),
                data.get('bestand'),
                data.get('lagerwert'),
                data.get('tage_seit_abgang'),
                teilenummer
            ])

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            logger.warning(f"Locosoft-Update fehlgeschlagen: {e}")

    # =========================================================================
    # STATISTIKEN
    # =========================================================================

    def get_verkaufschancen_stats(self) -> Dict:
        """Holt Statistiken zu Verkaufschancen."""
        try:
            conn = get_drive_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT
                    verkaufschance,
                    COUNT(*) as anzahl,
                    ROUND(SUM(lagerwert)::numeric, 2) as lagerwert_gesamt,
                    ROUND(AVG(preis_avg)::numeric, 2) as preis_avg_durchschnitt
                FROM penner_marktpreise
                WHERE lagerwert > 0
                GROUP BY verkaufschance
                ORDER BY
                    CASE verkaufschance
                        WHEN 'hoch' THEN 1
                        WHEN 'mittel' THEN 2
                        WHEN 'gering' THEN 3
                        WHEN 'keine' THEN 4
                        ELSE 5
                    END
            """)

            stats = cur.fetchall()

            # Gesamt
            cur.execute("""
                SELECT
                    COUNT(*) as gesamt_teile,
                    ROUND(SUM(lagerwert)::numeric, 2) as gesamt_lagerwert,
                    COUNT(*) FILTER (WHERE abgefragt_am > NOW() - INTERVAL '24 hours') as aktuell
                FROM penner_marktpreise
            """)
            gesamt = cur.fetchone()

            cur.close()
            conn.close()

            return {
                'nach_chance': [dict(s) for s in stats],
                'gesamt': dict(gesamt) if gesamt else {}
            }

        except Exception as e:
            logger.exception("Fehler bei Statistik-Abfrage")
            return {'nach_chance': [], 'gesamt': {}}


# =============================================================================
# SINGLETON ACCESSOR
# =============================================================================

_service: Optional[PreisvergleichService] = None


def get_preisvergleich_service() -> PreisvergleichService:
    """Holt die Singleton-Instanz des Services."""
    global _service
    if _service is None:
        _service = PreisvergleichService()
    return _service


# =============================================================================
# CLI TEST
# =============================================================================

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

    service = get_preisvergleich_service()

    # Test mit einer Teilenummer
    print("=" * 60)
    print("PREISVERGLEICH TEST")
    print("=" * 60)

    teilenummer = "1K0 615 301"  # VW Bremsscheibe

    print(f"\nSuche Marktpreise für: {teilenummer}")
    result = service.get_marktpreis(teilenummer, use_cache=False)

    print(f"\nQuellen: {result['zusammenfassung']['anzahl_quellen']}")
    print(f"Angebote: {result['zusammenfassung']['anzahl_angebote']}")
    print(f"Preis: {result['zusammenfassung']['preis_min']}€ - {result['zusammenfassung']['preis_max']}€")
    print(f"Durchschnitt: {result['zusammenfassung']['preis_avg']}€")
    print(f"\nEmpfehlung:")
    print(f"  Plattform: {result['empfehlung']['plattform']}")
    print(f"  Verkaufspreis: {result['empfehlung']['verkaufspreis']}€")
    print(f"  Chance: {result['empfehlung']['chance']}")
