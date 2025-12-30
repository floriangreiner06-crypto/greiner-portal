#!/usr/bin/env python3
"""
WERKSTATT DATA MODULE - Single Source of Truth für Werkstatt-KPIs
=================================================================
Datenmodul für alle Werkstatt-bezogenen Auswertungen direkt aus Locosoft.

Architektur:
- Class-based Pattern (WerkstattData)
- Statische Methoden für wiederverwendbare Datenabfragen
- Nutzt echte Locosoft-Tabellen (times, labours, invoices, employees_history)
- Keine Business Logic (nur Datenabruf + Aggregation)
- PostgreSQL-kompatibel

Consumer:
- api/werkstatt_live_api.py (Web-UI Endpoints)
- scripts/send_werkstatt_report.py (E-Mail Reports)
- api/controlling_data.py (TEK Bereich "4-Lohn")

Author: Claude Sonnet 4.5
Date: 2025-12-30 (TAG 148)
Pattern: docs/DATENMODUL_PATTERN.md

Migration Status:
- [x] get_mechaniker_leistung() - Basis-Implementierung
- [ ] get_offene_auftraege() - TODO
- [ ] get_auftrag_detail() - TODO
- [ ] get_problemfaelle() - TODO
- [ ] get_kapazitaetsplanung() - TODO
- [ ] get_stempeluhr() - TODO
- [ ] get_anwesenheit() - TODO
"""

from datetime import datetime, timedelta, date, time
from typing import Optional, Dict, List, Any, Tuple
import logging

# Zentrale DB-Utilities
from api.db_utils import locosoft_session, get_locosoft_connection, row_to_dict, rows_to_list
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# =============================================================================
# KONSTANTEN
# =============================================================================

BETRIEB_NAMEN = {
    1: 'Deggendorf',
    2: 'Hyundai DEG',
    3: 'Landau'
}

# Mechaniker-Range (Locosoft-Standard)
MECHANIKER_RANGE_START = 5000
MECHANIKER_RANGE_END = 5999

# Azubis ausschließen
MECHANIKER_EXCLUDE = [5025, 5026, 5028]

# Standard Arbeitszeiten
ARBEITSZEIT_START = time(7, 0)   # 07:00 Uhr
ARBEITSZEIT_ENDE = time(17, 0)   # 17:00 Uhr
STUNDEN_PRO_TAG = 10.0           # Effektive Arbeitsstunden


# =============================================================================
# WERKSTATT DATA CLASS
# =============================================================================

class WerkstattData:
    """
    Single Source of Truth für Werkstatt-Daten aus Locosoft.

    Bereiche:
    - Leistung: get_mechaniker_leistung()
    - Aufträge: get_offene_auftraege(), get_auftrag_detail(), get_problemfaelle()
    - Kapazität: get_kapazitaetsplanung()
    - Anwesenheit: get_stempeluhr(), get_anwesenheit()
    """

    # =========================================================================
    # LEISTUNG (Performance / Produktivität)
    # =========================================================================

    @staticmethod
    def get_mechaniker_leistung(
        von: Optional[date] = None,
        bis: Optional[date] = None,
        betrieb: Optional[int] = None,
        mechaniker_nr: Optional[int] = None,
        inkl_ehemalige: bool = False,
        sort_by: str = 'leistungsgrad'
    ) -> Dict[str, Any]:
        """
        Holt Leistungsgrad und Produktivität der Mechaniker LIVE aus Locosoft.

        WICHTIG: Nutzt echte Locosoft-Tabellen:
        - times (VIEW): Stempelungen (type=2: Auftragszeit, type=1: Anwesenheit)
        - labours: Verrechnete AW aus Rechnungen
        - invoices: Rechnungsdaten
        - employees_history: Mechaniker-Stammdaten

        Berechnet:
        - Stempelzeit (Minuten aus times where type=2)
        - Anwesenheit (Minuten aus times where type=1)
        - Verrechnete AW (time_units aus labours)
        - Leistungsgrad = (AW * 6 / Stempelzeit) * 100  [6 Min = 0,1 AW]
        - Produktivität = (Stempelzeit / Anwesenheit) * 100

        Args:
            von: Startdatum (default: Monatserster)
            bis: Enddatum (default: heute)
            betrieb: Betrieb-ID (1=DEG, 2=HYU, 3=LAN, None=alle)
            mechaniker_nr: Spezifischer Mechaniker (optional)
            inkl_ehemalige: Ehemalige Mitarbeiter einbeziehen (default: False)
            sort_by: Sortierung ('leistungsgrad', 'stempelzeit', 'aw', 'auftraege')

        Returns:
            Dict mit 'mechaniker' (Liste) und Gesamt-KPIs

        Example:
            >>> data = WerkstattData.get_mechaniker_leistung(
            ...     von=date(2025, 12, 1),
            ...     bis=date(2025, 12, 31),
            ...     betrieb=1
            ... )
            >>> data['mechaniker'][0]
            {'mechaniker_nr': 5001, 'name': 'Max Mustermann', 'leistungsgrad': 85.5, ...}
        """
        # Default Zeitraum: Aktueller Monat
        if von is None:
            von = date.today().replace(day=1)
        if bis is None:
            bis = date.today()

        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # SQL Query - direkt aus werkstatt_live_api.py::get_leistung_live()
            # aber als wiederverwendbare Funktion
            query = """
            WITH
            -- Stempelzeit pro Mechaniker/Tag (DEDUPLIZIERT!)
            stempel_dedupliziert AS (
                SELECT
                    employee_number,
                    DATE(start_time) as datum,
                    SUM(minuten) as stempel_min,
                    COUNT(DISTINCT order_number) as auftraege
                FROM (
                    SELECT DISTINCT ON (employee_number, start_time, end_time)
                        employee_number,
                        order_number,
                        start_time,
                        end_time,
                        EXTRACT(EPOCH FROM (end_time - start_time)) / 60 as minuten
                    FROM times
                    WHERE type = 2
                      AND end_time IS NOT NULL
                      AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
                ) dedup
                GROUP BY employee_number, DATE(start_time)
            ),
            -- Anwesenheit pro Mechaniker/Tag
            anwesenheit AS (
                SELECT
                    employee_number,
                    DATE(start_time) as datum,
                    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as anwesend_min
                FROM times
                WHERE type = 1
                  AND end_time IS NOT NULL
                  AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
                GROUP BY employee_number, DATE(start_time)
            ),
            -- Verrechnete AW pro Mechaniker (aus Rechnungen im Zeitraum)
            aw_verrechnet AS (
                SELECT
                    l.mechanic_no as employee_number,
                    SUM(l.time_units) as aw,
                    SUM(l.net_price_in_order) as umsatz
                FROM labours l
                JOIN invoices i ON l.invoice_number = i.invoice_number AND l.invoice_type = i.invoice_type
                WHERE i.invoice_date >= %s AND i.invoice_date <= %s
                  AND l.is_invoiced = true
                  AND l.mechanic_no IS NOT NULL
                GROUP BY l.mechanic_no
            ),
            -- Mechaniker-Aggregation
            mechaniker_summen AS (
                SELECT
                    COALESCE(s.employee_number, a.employee_number, aw.employee_number) as employee_number,
                    COUNT(DISTINCT COALESCE(s.datum, a.datum)) as tage,
                    COALESCE(SUM(s.auftraege), 0) as auftraege,
                    COALESCE(SUM(s.stempel_min), 0) as stempelzeit,
                    COALESCE(SUM(a.anwesend_min), 0) as anwesenheit,
                    COALESCE(MAX(aw.aw), 0) as aw,
                    COALESCE(MAX(aw.umsatz), 0) as umsatz
                FROM stempel_dedupliziert s
                FULL OUTER JOIN anwesenheit a ON s.employee_number = a.employee_number AND s.datum = a.datum
                LEFT JOIN aw_verrechnet aw ON COALESCE(s.employee_number, a.employee_number) = aw.employee_number
                GROUP BY COALESCE(s.employee_number, a.employee_number, aw.employee_number)
            )
            SELECT
                ms.employee_number as mechaniker_nr,
                eh.name as name,
                eh.subsidiary as betrieb,
                ms.tage,
                ms.auftraege,
                ROUND(ms.stempelzeit::numeric, 0) as stempelzeit,
                ROUND(ms.anwesenheit::numeric, 0) as anwesenheit,
                ROUND(ms.aw::numeric, 1) as aw,
                ROUND(ms.umsatz::numeric, 2) as umsatz,
                CASE
                    WHEN ms.stempelzeit > 0 AND ms.aw > 0
                    THEN ROUND((ms.aw * 6 / ms.stempelzeit * 100)::numeric, 1)
                    ELSE NULL
                END as leistungsgrad,
                CASE
                    WHEN ms.anwesenheit > 0 AND ms.stempelzeit > 0
                    THEN ROUND((ms.stempelzeit / ms.anwesenheit * 100)::numeric, 1)
                    ELSE NULL
                END as produktivitaet,
                CASE WHEN eh.termination_date IS NULL OR eh.termination_date > CURRENT_DATE THEN true ELSE false END as ist_aktiv
            FROM mechaniker_summen ms
            JOIN employees_history eh ON ms.employee_number = eh.employee_number AND eh.is_latest_record = true
            WHERE ms.employee_number BETWEEN %s AND %s
              AND ms.employee_number != ALL(%s)
              AND (ms.stempelzeit > 0 OR ms.aw > 0)
            """

            params = [
                von, bis,  # stempel_dedupliziert
                von, bis,  # anwesenheit
                von, bis,  # aw_verrechnet
                MECHANIKER_RANGE_START, MECHANIKER_RANGE_END,
                MECHANIKER_EXCLUDE
            ]

            # Filter
            conditions = []
            if betrieb is not None:
                conditions.append(f"eh.subsidiary = {int(betrieb)}")

            if mechaniker_nr is not None:
                conditions.append(f"ms.employee_number = {int(mechaniker_nr)}")

            if not inkl_ehemalige:
                conditions.append("(eh.termination_date IS NULL OR eh.termination_date > CURRENT_DATE)")

            if conditions:
                query += " AND " + " AND ".join(conditions)

            # Sortierung
            sort_map = {
                'leistungsgrad': 'leistungsgrad DESC NULLS LAST',
                'stempelzeit': 'stempelzeit DESC',
                'aw': 'aw DESC',
                'auftraege': 'auftraege DESC'
            }
            query += f" ORDER BY {sort_map.get(sort_by, 'leistungsgrad DESC NULLS LAST')}"

            cursor.execute(query, params)
            mechaniker = cursor.fetchall()

            # Convert to list of dicts
            mechaniker_liste = []
            for m in mechaniker:
                mechaniker_liste.append({
                    'mechaniker_nr': m['mechaniker_nr'],
                    'name': m['name'],
                    'betrieb': m['betrieb'],
                    'betrieb_name': BETRIEB_NAMEN.get(m['betrieb'], 'Unbekannt'),
                    'ist_aktiv': m['ist_aktiv'],
                    'tage': int(m['tage'] or 0),
                    'auftraege': int(m['auftraege'] or 0),
                    'stempelzeit': float(m['stempelzeit'] or 0),
                    'anwesenheit': float(m['anwesenheit'] or 0),
                    'aw': float(m['aw'] or 0),
                    'umsatz': float(m['umsatz'] or 0),
                    'leistungsgrad': float(m['leistungsgrad']) if m['leistungsgrad'] else None,
                    'produktivitaet': float(m['produktivitaet']) if m['produktivitaet'] else None
                })

            # Gesamt-KPIs
            gesamt_auftraege = sum(m['auftraege'] for m in mechaniker_liste)
            gesamt_stempelzeit = sum(m['stempelzeit'] for m in mechaniker_liste)
            gesamt_anwesenheit = sum(m['anwesenheit'] for m in mechaniker_liste)
            gesamt_aw = sum(m['aw'] for m in mechaniker_liste)
            gesamt_umsatz = sum(m['umsatz'] for m in mechaniker_liste)

            gesamt_leistungsgrad = round(gesamt_aw * 6 / gesamt_stempelzeit * 100, 1) if gesamt_stempelzeit > 0 else 0
            gesamt_produktivitaet = round(gesamt_stempelzeit / gesamt_anwesenheit * 100, 1) if gesamt_anwesenheit > 0 else 0

            # Anzahl Arbeitstage
            cursor.execute("""
                SELECT COUNT(DISTINCT DATE(start_time)) as count
                FROM times
                WHERE type = 2 AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
            """, [von, bis])
            anzahl_tage = cursor.fetchone()['count'] or 0

            logger.info(f"WerkstattData.get_mechaniker_leistung: {len(mechaniker_liste)} Mechaniker, Zeitraum {von} - {bis}")

            return {
                'zeitraum': {
                    'von': str(von),
                    'bis': str(bis)
                },
                'betrieb': betrieb,
                'mechaniker': mechaniker_liste,
                'anzahl_mechaniker': len(mechaniker_liste),
                'anzahl_tage': anzahl_tage,
                'gesamt': {
                    'auftraege': gesamt_auftraege,
                    'stempelzeit': gesamt_stempelzeit,
                    'anwesenheit': gesamt_anwesenheit,
                    'aw': round(gesamt_aw, 1),
                    'umsatz': round(gesamt_umsatz, 2),
                    'leistungsgrad': gesamt_leistungsgrad,
                    'produktivitaet': gesamt_produktivitaet
                }
            }

    @staticmethod
    def get_leistung_trend(
        von: Optional[date] = None,
        bis: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Holt Leistungsgrad-Trend pro Tag.

        Args:
            von: Startdatum (default: heute - 14 Tage)
            bis: Enddatum (default: heute)

        Returns:
            Liste von {'datum': '2025-12-30', 'leistungsgrad': 85.5}
        """
        if von is None:
            von = date.today() - timedelta(days=14)
        if bis is None:
            bis = date.today()

        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
            WITH stempel_trend AS (
                SELECT
                    DATE(start_time) as datum,
                    SUM(minuten) as stempel_min
                FROM (
                    SELECT DISTINCT ON (employee_number, start_time, end_time)
                        start_time,
                        EXTRACT(EPOCH FROM (end_time - start_time)) / 60 as minuten
                    FROM times
                    WHERE type = 2 AND end_time IS NOT NULL
                      AND start_time >= %s AND start_time <= %s
                ) dedup
                GROUP BY DATE(start_time)
            ),
            aw_trend AS (
                SELECT
                    i.invoice_date as datum,
                    SUM(l.time_units) as aw
                FROM labours l
                JOIN invoices i ON l.invoice_number = i.invoice_number AND l.invoice_type = i.invoice_type
                WHERE i.invoice_date >= %s AND i.invoice_date <= %s
                  AND l.is_invoiced = true AND l.mechanic_no IS NOT NULL
                GROUP BY i.invoice_date
            )
            SELECT
                s.datum,
                ROUND((COALESCE(a.aw, 0) * 6 / NULLIF(s.stempel_min, 0) * 100)::numeric, 1) as leistungsgrad
            FROM stempel_trend s
            LEFT JOIN aw_trend a ON s.datum = a.datum
            ORDER BY s.datum
            """

            cursor.execute(query, [von, bis, von, bis])
            return [
                {'datum': str(r['datum']), 'leistungsgrad': float(r['leistungsgrad'] or 0)}
                for r in cursor.fetchall()
            ]

    # =========================================================================
    # AUFTRÄGE (Jobs / Orders)
    # =========================================================================

    @staticmethod
    def get_offene_auftraege(
        betrieb: Optional[int] = None,
        tage_zurueck: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Holt alle offenen Werkstatt-Aufträge (nicht fakturiert).

        TODO: Implementierung - siehe werkstatt_live_api.py::get_offene_auftraege()

        Args:
            betrieb: Betrieb-ID (optional)
            tage_zurueck: Wie viele Tage zurück (default: 7)

        Returns:
            Liste offener Aufträge
        """
        # TODO TAG149: Implementierung
        logger.warning("WerkstattData.get_offene_auftraege() - NOCH NICHT IMPLEMENTIERT (TODO TAG149)")
        return []

    # =========================================================================
    # KAPAZITÄT (Capacity Planning)
    # =========================================================================

    @staticmethod
    def get_kapazitaetsplanung(
        von: Optional[date] = None,
        bis: Optional[date] = None,
        betrieb: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Berechnet Werkstatt-Kapazität und Auslastung.

        TODO: Implementierung - siehe werkstatt_live_api.py::get_kapazitaetsplanung()

        Args:
            von: Startdatum (default: heute)
            bis: Enddatum (default: +14 Tage)
            betrieb: Betrieb-ID

        Returns:
            Dict mit Kapazitäts-Kennzahlen
        """
        # TODO TAG149: Implementierung
        logger.warning("WerkstattData.get_kapazitaetsplanung() - NOCH NICHT IMPLEMENTIERT (TODO TAG149)")
        return {}

    # =========================================================================
    # ANWESENHEIT (Attendance / Stempeluhr)
    # =========================================================================

    @staticmethod
    def get_stempeluhr(
        datum: Optional[date] = None,
        betrieb: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Holt Stempeluhr-Daten für einen Tag.

        TODO: Implementierung - siehe werkstatt_live_api.py::get_stempeluhr_live()

        Args:
            datum: Datum (default: heute)
            betrieb: Betrieb-ID

        Returns:
            Liste von Mechanikern mit Stempelungen
        """
        # TODO TAG149: Implementierung
        logger.warning("WerkstattData.get_stempeluhr() - NOCH NICHT IMPLEMENTIERT (TODO TAG149)")
        return []


# =============================================================================
# CONVENIENCE FUNCTIONS (für TEK Integration)
# =============================================================================

def get_werkstatt_kpis_fuer_tek(monat: int, jahr: int, betrieb: Optional[int] = None) -> Dict[str, Any]:
    """
    Holt alle wichtigen Werkstatt-KPIs für TEK-Integration (controlling_data.py).

    Nutzt WerkstattData.get_mechaniker_leistung() und aggregiert für TEK Bereich "4-Lohn".

    Args:
        monat: Monat (1-12)
        jahr: Jahr (z.B. 2025)
        betrieb: Betrieb-ID (optional)

    Returns:
        Dict mit aggregierten Werkstatt-KPIs für TEK

    Example:
        >>> kpis = get_werkstatt_kpis_fuer_tek(12, 2025)
        >>> kpis['gesamt_stunden_verrechnet']
        1842.5
    """
    von = date(jahr, monat, 1)

    # Letzter Tag des Monats
    if monat == 12:
        bis = date(jahr + 1, 1, 1) - timedelta(days=1)
    else:
        bis = date(jahr, monat + 1, 1) - timedelta(days=1)

    # Daten holen
    leistung = WerkstattData.get_mechaniker_leistung(von, bis, betrieb)

    return {
        'monat': monat,
        'jahr': jahr,
        'betrieb': betrieb,
        'gesamt_stunden_verrechnet': leistung['gesamt']['aw'],  # AW = Arbeitswerte = verrechnet
        'gesamt_stunden_anwesend': leistung['gesamt']['anwesenheit'] / 60.0,  # Minuten → Stunden
        'durchschnitt_leistungsgrad': leistung['gesamt']['leistungsgrad'],
        'anzahl_mechaniker': leistung['anzahl_mechaniker'],
        'gesamt_umsatz': leistung['gesamt']['umsatz']
    }
