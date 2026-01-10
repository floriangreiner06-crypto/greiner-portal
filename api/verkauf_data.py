"""
Verkauf Data Module - Single Source of Truth (SSOT) für Verkaufsdaten

Dieses Modul enthält alle Datenzugriffsfunktionen für Verkauf/Sales.
Es folgt dem gleichen Muster wie werkstatt_data.py und fahrzeug_data.py.

ARCHITEKTUR:
- VerkaufData: Klasse mit statischen Methoden für alle Verkaufs-Queries
- Alle Funktionen nutzen db_session() für DRIVE Portal DB
- Einige Funktionen nutzen locosoft_session() für Locosoft-Daten
- Rückgabe immer als Dict mit 'success', 'data', 'meta' Struktur

WICHTIG:
- sales-Tabelle: Verkaufsdaten aus Locosoft Mirror (DRIVE Portal DB)
- Dedup-Filter: Verhindert Doppelzählungen bei N→T/V Umsetzungen
- Fahrzeugtypen: N=Neu, G=Gebraucht, D=Demo, T=Tausch, V=Vorführ

Erstellt: TAG 159 (2026-01-02)
Autor: Claude AI
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

from api.db_utils import db_session, locosoft_session
from api.db_connection import sql_placeholder
# SSOT: Standort-Filter
from api.standort_utils import build_locosoft_filter_verkauf

logger = logging.getLogger(__name__)


# ==============================================================================
# KONSTANTEN
# ==============================================================================

# Interne Kundennummern (Autohaus Greiner selbst)
INTERNE_KUNDEN = (3000001, 3000002)

# Marken-Mapping
MARKEN = {
    27: 'Hyundai',
    40: 'Opel',
    41: 'Leapmotor'
}

# Dedup-Filter: Verhindert Doppelzählungen bei N→T/V Umsetzungen
# Regel: Wenn T oder V existiert, ignoriere N für dieselbe VIN am gleichen Datum
DEDUP_FILTER = """
    AND NOT EXISTS (
        SELECT 1
        FROM sales s2
        WHERE s2.vin = s.vin
            AND s2.out_sales_contract_date = s.out_sales_contract_date
            AND s2.dealer_vehicle_type IN ('T', 'V')
            AND s.dealer_vehicle_type = 'N'
    )
"""


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def _aggregate_verkaufer_daten(rows: List[Dict]) -> Dict[str, Any]:
    """
    Aggregiert Rohdaten nach Verkäufer.

    Args:
        rows: Liste von Dicts mit salesman_number, verkaufer_name, fahrzeugart, anzahl

    Returns:
        Dict mit 'verkaeufer' (Liste) und 'summe' (Dict)
    """
    verkaufer_dict = {}
    summe = {'nw': 0, 'gw': 0, 'gesamt': 0}

    for row in rows:
        vk_nr = row['salesman_number']
        vk_name = row['verkaufer_name']
        art = row['fahrzeugart']
        anzahl = row['anzahl']

        if vk_nr not in verkaufer_dict:
            verkaufer_dict[vk_nr] = {
                'nummer': vk_nr,
                'name': vk_name,
                'nw': 0,
                'gw': 0,
                'gesamt': 0
            }

        if art == 'NW':
            verkaufer_dict[vk_nr]['nw'] += anzahl
            summe['nw'] += anzahl
        elif art == 'GW':
            verkaufer_dict[vk_nr]['gw'] += anzahl
            summe['gw'] += anzahl

        verkaufer_dict[vk_nr]['gesamt'] += anzahl
        summe['gesamt'] += anzahl

    return {
        'verkaeufer': list(verkaufer_dict.values()),
        'summe': summe
    }


def _convert_decimal(value) -> float:
    """Konvertiert Decimal zu float für JSON-Serialisierung."""
    if isinstance(value, Decimal):
        return float(value)
    return value if value is not None else 0


# ==============================================================================
# VERKAUFDATA KLASSE
# ==============================================================================

class VerkaufData:
    """
    Single Source of Truth für alle Verkaufs-Datenabfragen.

    Methoden:
        get_auftragseingang() - Auftragseingang nach Verkäufern (heute + Periode)
        get_auftragseingang_summary() - Aggregiert nach Marke
        get_auftragseingang_detail() - Detail mit Modellen pro Verkäufer
        get_auftragseingang_fahrzeuge() - Einzelfahrzeuge mit VIN
        get_auslieferung_summary() - Auslieferungen nach Marke
        get_auslieferung_detail() - Auslieferungen mit Einzelfahrzeugen
        get_verkaufer_liste() - Alle bekannten Verkäufer
        get_lieferforecast() - Geplante Lieferungen mit DB1-Prognose
        get_verkaufer_performance() - Performance-Kennzahlen pro Verkäufer
    """

    @staticmethod
    def get_auftragseingang(
        month: int = None,
        year: int = None,
        location: int = None
    ) -> Dict[str, Any]:
        """
        Holt Auftragseingang nach Verkäufern für heute und Periode.

        Args:
            month: Monat (1-12), default: aktueller Monat
            year: Jahr, default: aktuelles Jahr

        Returns:
            Dict mit:
                - success: bool
                - heute: Liste Verkäufer mit Aufträgen heute
                - periode: Liste Verkäufer mit Aufträgen im Monat
                - summe_heute: Aggregierte Summen heute
                - summe_periode: Aggregierte Summen Monat
                - alle_verkaeufer: Liste aller bekannten Verkäufer

        Example:
            >>> data = VerkaufData.get_auftragseingang(month=12, year=2025)
            >>> print(f"Heute: {data['summe_heute']['gesamt']} Aufträge")
        """
        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year

        try:
            with db_session() as conn:
                cursor = conn.cursor()

                # 1. Aufträge HEUTE
                cursor.execute(f"""
                    SELECT
                        s.salesman_number,
                        COALESCE(e.first_name || ' ' || e.last_name,
                                 'Verkäufer #' || s.salesman_number || ' (nicht in LocoSoft)') as verkaufer_name,
                        CASE
                            WHEN s.dealer_vehicle_type IN ('N', 'V') THEN 'NW'
                            WHEN s.dealer_vehicle_type IN ('D', 'G', 'T') THEN 'GW'
                            ELSE 'Sonstige'
                        END as fahrzeugart,
                        COUNT(*) as anzahl
                    FROM sales s
                    LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
                    WHERE DATE(s.out_sales_contract_date) = CURRENT_DATE
                      AND s.salesman_number IS NOT NULL
                      {DEDUP_FILTER}
                    GROUP BY s.salesman_number, verkaufer_name, fahrzeugart
                """)
                heute_raw = [dict(row) for row in cursor.fetchall()]

                # 2. Aufträge PERIODE (ganzer Monat)
                cursor.execute(f"""
                    SELECT
                        s.salesman_number,
                        COALESCE(e.first_name || ' ' || e.last_name,
                                 'Verkäufer #' || s.salesman_number || ' (nicht in LocoSoft)') as verkaufer_name,
                        CASE
                            WHEN s.dealer_vehicle_type IN ('N', 'V') THEN 'NW'
                            WHEN s.dealer_vehicle_type IN ('D', 'G', 'T') THEN 'GW'
                            ELSE 'Sonstige'
                        END as fahrzeugart,
                        COUNT(*) as anzahl
                    FROM sales s
                    LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
                    WHERE EXTRACT(YEAR FROM s.out_sales_contract_date) = %s
                      AND EXTRACT(MONTH FROM s.out_sales_contract_date) = %s
                      AND s.salesman_number IS NOT NULL
                      {DEDUP_FILTER}
                    GROUP BY s.salesman_number, verkaufer_name, fahrzeugart
                """, (str(year), f"{month:02d}"))
                periode_raw = [dict(row) for row in cursor.fetchall()]

                # 3. Alle Verkäufer
                cursor.execute("""
                    SELECT DISTINCT
                        s.salesman_number,
                        COALESCE(e.first_name || ' ' || e.last_name,
                                 'Verkäufer #' || s.salesman_number || ' (nicht in LocoSoft)') as verkaufer_name
                    FROM sales s
                    LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
                    WHERE s.salesman_number IS NOT NULL
                    ORDER BY verkaufer_name
                """)
                alle_verkaeufer = [dict(row) for row in cursor.fetchall()]

                # Aggregieren
                heute_data = _aggregate_verkaufer_daten(heute_raw)
                periode_data = _aggregate_verkaufer_daten(periode_raw)

                return {
                    'success': True,
                    'month': month,
                    'year': year,
                    'heute': heute_data['verkaeufer'],
                    'periode': periode_data['verkaeufer'],
                    'summe_heute': heute_data['summe'],
                    'summe_periode': periode_data['summe'],
                    'alle_verkaeufer': alle_verkaeufer
                }

        except Exception as e:
            logger.error(f"Fehler in get_auftragseingang: {e}")
            return {
                'success': False,
                'error': str(e),
                'heute': [],
                'periode': [],
                'summe_heute': {'nw': 0, 'gw': 0, 'gesamt': 0},
                'summe_periode': {'nw': 0, 'gw': 0, 'gesamt': 0},
                'alle_verkaeufer': []
            }

    @staticmethod
    def get_auftragseingang_summary(
        day: str = None,
        month: int = None,
        year: int = None,
        location: int = None
    ) -> Dict[str, Any]:
        """
        Holt Auftragseingang-Summary nach Marke und Fahrzeugtyp.

        Args:
            day: Spezifischer Tag (YYYY-MM-DD), hat Vorrang vor month/year
            month: Monat (1-12)
            year: Jahr

        Returns:
            Dict mit summary nach Marke (gesamt, neu, test_vorfuehr, gebraucht, umsatz)
        """
        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year

        try:
            with db_session() as conn:
                cursor = conn.cursor()

                # TAG 177: Standort-Filter bauen
                standort_filter = ""
                if location:
                    standort_filter_sql = build_locosoft_filter_verkauf(int(location), nur_stellantis=False)
                    if standort_filter_sql:
                        # Filter-String anpassen: "AND out_subsidiary = X" -> "AND s.out_subsidiary = X"
                        standort_filter = standort_filter_sql.replace("out_subsidiary", "s.out_subsidiary")

                if day:
                    where_clause = f"WHERE DATE(s.out_sales_contract_date) = %s {standort_filter} {DEDUP_FILTER}"
                    params = [day]
                else:
                    where_clause = f"""
                        WHERE EXTRACT(YEAR FROM s.out_sales_contract_date) = %s
                          AND EXTRACT(MONTH FROM s.out_sales_contract_date) = %s
                          {standort_filter}
                          {DEDUP_FILTER}
                    """
                    params = [str(year), f"{month:02d}"]

                cursor.execute(f"""
                    SELECT
                        s.make_number,
                        COUNT(*) as gesamt,
                        SUM(CASE WHEN s.dealer_vehicle_type = 'N' THEN 1 ELSE 0 END) as neu,
                        SUM(CASE WHEN s.dealer_vehicle_type IN ('T', 'V') THEN 1 ELSE 0 END) as test_vorfuehr,
                        SUM(CASE WHEN s.dealer_vehicle_type IN ('G', 'D') THEN 1 ELSE 0 END) as gebraucht,
                        SUM(s.out_sale_price) as umsatz_gesamt
                    FROM sales s
                    {where_clause}
                    GROUP BY s.make_number
                """, params)

                summary = []
                for row in cursor.fetchall():
                    summary.append({
                        'make_number': row['make_number'],
                        'marke': MARKEN.get(row['make_number'], f"Marke {row['make_number']}"),
                        'gesamt': row['gesamt'],
                        'neu': row['neu'] or 0,
                        'test_vorfuehr': row['test_vorfuehr'] or 0,
                        'gebraucht': row['gebraucht'] or 0,
                        'umsatz_gesamt': _convert_decimal(row['umsatz_gesamt'])
                    })

                return {
                    'success': True,
                    'day': day,
                    'month': month if not day else None,
                    'year': year,
                    'summary': summary
                }

        except Exception as e:
            logger.error(f"Fehler in get_auftragseingang_summary: {e}")
            return {'success': False, 'error': str(e), 'summary': []}

    @staticmethod
    def get_auftragseingang_detail(
        day: str = None,
        month: int = None,
        year: int = None,
        location: int = None,
        verkaufer: int = None
    ) -> Dict[str, Any]:
        """
        Holt detaillierten Auftragseingang nach Verkäufer mit Modell-Aufschlüsselung.

        Args:
            day: Spezifischer Tag (YYYY-MM-DD)
            month: Monat (1-12)
            year: Jahr
            location: Standort-Filter (1=LAN, 2=DEG)
            verkaufer: Verkäufer-Nummer Filter

        Returns:
            Dict mit Liste von Verkäufern, jeweils mit neu/test_vorfuehr/gebraucht Listen
        """
        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year

        try:
            with db_session() as conn:
                cursor = conn.cursor()

                where_clauses = ["s.salesman_number IS NOT NULL"]
                params = []

                if day:
                    where_clauses.append("DATE(s.out_sales_contract_date) = %s")
                    params.append(day)
                else:
                    where_clauses.append("EXTRACT(YEAR FROM s.out_sales_contract_date) = %s")
                    where_clauses.append("EXTRACT(MONTH FROM s.out_sales_contract_date) = %s")
                    params.extend([str(year), f"{month:02d}"])

                # TAG 177: SSOT-Filter für Verkäufe (konsolidiert für Standort 1)
                if location:
                    standort_filter = build_locosoft_filter_verkauf(int(location), nur_stellantis=False)
                    if standort_filter:
                        # Filter-String anpassen: "AND out_subsidiary = X" -> "s.out_subsidiary = X"
                        filter_sql = standort_filter.replace("AND ", "").replace("out_subsidiary", "s.out_subsidiary")
                        where_clauses.append(filter_sql)

                if verkaufer:
                    where_clauses.append("s.salesman_number = %s")
                    params.append(int(verkaufer))

                # Dedup-Filter
                where_clauses.append("""
                    NOT EXISTS (
                        SELECT 1 FROM sales s2
                        WHERE s2.vin = s.vin
                            AND s2.out_sales_contract_date = s.out_sales_contract_date
                            AND s2.dealer_vehicle_type IN ('T', 'V')
                            AND s.dealer_vehicle_type = 'N'
                    )
                """)

                where_sql = " AND ".join(where_clauses)

                cursor.execute(f"""
                    SELECT
                        s.salesman_number,
                        COALESCE(e.first_name || ' ' || e.last_name,
                                 'Verkäufer #' || s.salesman_number || ' (nicht in LocoSoft)') as verkaufer_name,
                        s.dealer_vehicle_type,
                        s.model_description,
                        COUNT(*) as anzahl
                    FROM sales s
                    LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
                    WHERE {where_sql}
                    GROUP BY s.salesman_number, verkaufer_name, s.dealer_vehicle_type, s.model_description
                    ORDER BY verkaufer_name, s.dealer_vehicle_type, s.model_description
                """, params)

                rows = cursor.fetchall()

                # Aggregieren nach Verkäufer
                verkaufer_dict = {}
                for row in rows:
                    vk_nr = row['salesman_number']
                    vk_name = row['verkaufer_name']
                    typ = row['dealer_vehicle_type']
                    modell = row['model_description'] or 'Unbekannt'
                    anzahl = row['anzahl']

                    if vk_nr not in verkaufer_dict:
                        verkaufer_dict[vk_nr] = {
                            'verkaufer_nummer': vk_nr,
                            'verkaufer_name': vk_name,
                            'neu': [],
                            'test_vorfuehr': [],
                            'gebraucht': [],
                            'summe_neu': 0,
                            'summe_test_vorfuehr': 0,
                            'summe_gebraucht': 0,
                            'summe_gesamt': 0
                        }

                    modell_info = {'modell': modell, 'anzahl': anzahl}

                    if typ == 'N':
                        verkaufer_dict[vk_nr]['neu'].append(modell_info)
                        verkaufer_dict[vk_nr]['summe_neu'] += anzahl
                    elif typ in ('T', 'V'):
                        verkaufer_dict[vk_nr]['test_vorfuehr'].append(modell_info)
                        verkaufer_dict[vk_nr]['summe_test_vorfuehr'] += anzahl
                    elif typ in ('G', 'D'):
                        verkaufer_dict[vk_nr]['gebraucht'].append(modell_info)
                        verkaufer_dict[vk_nr]['summe_gebraucht'] += anzahl

                    verkaufer_dict[vk_nr]['summe_gesamt'] += anzahl

                return {
                    'success': True,
                    'day': day,
                    'month': month if not day else None,
                    'year': year,
                    'verkaufer': list(verkaufer_dict.values())
                }

        except Exception as e:
            logger.error(f"Fehler in get_auftragseingang_detail: {e}")
            return {'success': False, 'error': str(e), 'verkaufer': []}

    @staticmethod
    def get_auslieferung_summary(
        day: str = None,
        month: int = None,
        year: int = None
    ) -> Dict[str, Any]:
        """
        Holt Auslieferungs-Summary nach Marke (basiert auf Rechnungsdatum).

        Args:
            day: Spezifischer Tag (YYYY-MM-DD)
            month: Monat (1-12)
            year: Jahr

        Returns:
            Dict mit summary nach Marke
        """
        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year

        try:
            with db_session() as conn:
                cursor = conn.cursor()

                if day:
                    where_clause = f"""
                        WHERE DATE(s.out_invoice_date) = %s
                          AND s.out_invoice_date IS NOT NULL
                          {DEDUP_FILTER}
                    """
                    params = [day]
                else:
                    where_clause = f"""
                        WHERE EXTRACT(YEAR FROM s.out_invoice_date) = %s
                          AND EXTRACT(MONTH FROM s.out_invoice_date) = %s
                          AND s.out_invoice_date IS NOT NULL
                          {DEDUP_FILTER}
                    """
                    params = [str(year), f"{month:02d}"]

                cursor.execute(f"""
                    SELECT
                        s.make_number,
                        COUNT(*) as gesamt,
                        SUM(CASE WHEN s.dealer_vehicle_type = 'N' THEN 1 ELSE 0 END) as neu,
                        SUM(CASE WHEN s.dealer_vehicle_type IN ('T', 'V') THEN 1 ELSE 0 END) as test_vorfuehr,
                        SUM(CASE WHEN s.dealer_vehicle_type IN ('G', 'D') THEN 1 ELSE 0 END) as gebraucht,
                        SUM(s.out_sale_price) as umsatz_gesamt
                    FROM sales s
                    {where_clause}
                    GROUP BY s.make_number
                """, params)

                summary = []
                for row in cursor.fetchall():
                    summary.append({
                        'make_number': row['make_number'],
                        'marke': MARKEN.get(row['make_number'], f"Marke {row['make_number']}"),
                        'gesamt': row['gesamt'],
                        'neu': row['neu'] or 0,
                        'test_vorfuehr': row['test_vorfuehr'] or 0,
                        'gebraucht': row['gebraucht'] or 0,
                        'umsatz_gesamt': _convert_decimal(row['umsatz_gesamt'])
                    })

                return {
                    'success': True,
                    'day': day,
                    'month': month if not day else None,
                    'year': year,
                    'summary': summary
                }

        except Exception as e:
            logger.error(f"Fehler in get_auslieferung_summary: {e}")
            return {'success': False, 'error': str(e), 'summary': []}

    @staticmethod
    def get_auslieferung_detail(
        day: str = None,
        month: int = None,
        year: int = None,
        location: int = None,
        verkaufer: int = None,
        vin_search: str = None
    ) -> Dict[str, Any]:
        """
        Holt detaillierte Auslieferungen mit Einzelfahrzeugen und DB-Daten.

        Args:
            day: Spezifischer Tag (YYYY-MM-DD)
            month: Monat (1-12)
            year: Jahr
            location: Standort-Filter
            verkaufer: Verkäufer-Filter
            vin_search: VIN-Teilsuche

        Returns:
            Dict mit Liste von Verkäufern mit Einzelfahrzeugen
        """
        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year

        try:
            with db_session() as conn:
                cursor = conn.cursor()

                where_clauses = [
                    "s.salesman_number IS NOT NULL",
                    "s.out_invoice_date IS NOT NULL"
                ]
                params = []

                if day:
                    where_clauses.append("DATE(s.out_invoice_date) = %s")
                    params.append(day)
                else:
                    where_clauses.append("EXTRACT(YEAR FROM s.out_invoice_date) = %s")
                    where_clauses.append("EXTRACT(MONTH FROM s.out_invoice_date) = %s")
                    params.extend([str(year), f"{month:02d}"])

                # TAG 177: SSOT-Filter für Verkäufe (konsolidiert für Standort 1)
                if location:
                    standort_filter = build_locosoft_filter_verkauf(int(location), nur_stellantis=False)
                    if standort_filter:
                        # Filter-String anpassen: "AND out_subsidiary = X" -> "s.out_subsidiary = X"
                        filter_sql = standort_filter.replace("AND ", "").replace("out_subsidiary", "s.out_subsidiary")
                        where_clauses.append(filter_sql)

                if verkaufer:
                    where_clauses.append("s.salesman_number = %s")
                    params.append(int(verkaufer))

                if vin_search:
                    where_clauses.append("s.vin LIKE %s")
                    params.append(f"%{vin_search}%")

                # Dedup-Filter
                where_clauses.append("""
                    NOT EXISTS (
                        SELECT 1 FROM sales s2
                        WHERE s2.vin = s.vin
                            AND s2.out_sales_contract_date = s.out_sales_contract_date
                            AND s2.dealer_vehicle_type IN ('T', 'V')
                            AND s.dealer_vehicle_type = 'N'
                    )
                """)

                where_sql = " AND ".join(where_clauses)

                cursor.execute(f"""
                    SELECT
                        s.salesman_number,
                        COALESCE(e.first_name || ' ' || e.last_name,
                                 'Verkäufer #' || s.salesman_number || ' (nicht in LocoSoft)') as verkaufer_name,
                        s.dealer_vehicle_type,
                        s.model_description,
                        s.vin,
                        s.out_invoice_date,
                        COALESCE(s.out_sale_price, 0) as umsatz,
                        COALESCE(s.deckungsbeitrag, 0) as deckungsbeitrag,
                        COALESCE(s.db_prozent, 0) as db_prozent
                    FROM sales s
                    LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
                    WHERE {where_sql}
                    ORDER BY verkaufer_name, s.dealer_vehicle_type, s.model_description
                """, params)

                rows = cursor.fetchall()

                # Aggregieren nach Verkäufer mit Einzelfahrzeugen
                verkaufer_dict = {}
                for row in rows:
                    vk_nr = row['salesman_number']
                    vk_name = row['verkaufer_name']
                    typ = row['dealer_vehicle_type']
                    modell = row['model_description'] or 'Unbekannt'
                    vin = row['vin'] or ''
                    invoice_date = row['out_invoice_date']
                    umsatz = _convert_decimal(row['umsatz'])
                    db = _convert_decimal(row['deckungsbeitrag'])
                    db_prozent = _convert_decimal(row['db_prozent'])

                    if vk_nr not in verkaufer_dict:
                        verkaufer_dict[vk_nr] = {
                            'verkaufer_nummer': vk_nr,
                            'verkaufer_name': vk_name,
                            'fahrzeuge': [],
                            'summe_neu': 0,
                            'summe_test_vorfuehr': 0,
                            'summe_gebraucht': 0,
                            'summe_gesamt': 0,
                            'umsatz_gesamt': 0,
                            'db_gesamt': 0
                        }

                    fahrzeug_info = {
                        'typ': typ,
                        'modell': modell,
                        'vin': vin,
                        'vin_kurz': vin[-8:] if len(vin) >= 8 else vin,
                        'datum': str(invoice_date) if invoice_date else None,
                        'umsatz': round(umsatz, 2),
                        'deckungsbeitrag': round(db, 2),
                        'db_prozent': round(db_prozent, 2)
                    }

                    verkaufer_dict[vk_nr]['fahrzeuge'].append(fahrzeug_info)

                    if typ == 'N':
                        verkaufer_dict[vk_nr]['summe_neu'] += 1
                    elif typ in ('T', 'V'):
                        verkaufer_dict[vk_nr]['summe_test_vorfuehr'] += 1
                    elif typ in ('G', 'D'):
                        verkaufer_dict[vk_nr]['summe_gebraucht'] += 1

                    verkaufer_dict[vk_nr]['summe_gesamt'] += 1
                    verkaufer_dict[vk_nr]['umsatz_gesamt'] += umsatz
                    verkaufer_dict[vk_nr]['db_gesamt'] += db

                # DB% berechnen
                for vk_data in verkaufer_dict.values():
                    if vk_data['umsatz_gesamt'] > 0:
                        vk_data['db_prozent_gesamt'] = round(
                            (vk_data['db_gesamt'] / (vk_data['umsatz_gesamt'] / 1.19)) * 100, 2
                        )
                    else:
                        vk_data['db_prozent_gesamt'] = 0

                    vk_data['umsatz_gesamt'] = round(vk_data['umsatz_gesamt'], 2)
                    vk_data['db_gesamt'] = round(vk_data['db_gesamt'], 2)

                verkaufer_list = sorted(
                    verkaufer_dict.values(),
                    key=lambda x: x['verkaufer_name']
                )

                return {
                    'success': True,
                    'day': day,
                    'month': month if not day else None,
                    'year': year,
                    'vin_filter': vin_search,
                    'verkaufer': verkaufer_list
                }

        except Exception as e:
            logger.error(f"Fehler in get_auslieferung_detail: {e}")
            return {'success': False, 'error': str(e), 'verkaufer': []}

    @staticmethod
    def get_verkaufer_liste() -> Dict[str, Any]:
        """
        Holt Liste aller bekannten Verkäufer.

        Returns:
            Dict mit 'verkaufer' Liste (nummer, name)
        """
        try:
            with db_session() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT DISTINCT
                        s.salesman_number as nummer,
                        COALESCE(
                            e.first_name || ' ' || e.last_name,
                            'Verkäufer #' || s.salesman_number || ' (nicht in LocoSoft)'
                        ) as name
                    FROM sales s
                    LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
                    WHERE s.salesman_number IS NOT NULL
                    ORDER BY
                        CASE WHEN e.first_name IS NOT NULL THEN 0 ELSE 1 END,
                        name
                """)

                verkaufer = [dict(row) for row in cursor.fetchall()]

                return {
                    'success': True,
                    'verkaufer': verkaufer
                }

        except Exception as e:
            logger.error(f"Fehler in get_verkaufer_liste: {e}")
            return {'success': False, 'error': str(e), 'verkaufer': []}

    @staticmethod
    def get_lieferforecast(
        von: str = None,
        bis: str = None,
        standort: str = 'all'
    ) -> Dict[str, Any]:
        """
        Holt geplante Fahrzeugauslieferungen mit DB1-Prognose.

        Args:
            von: Start-Datum (YYYY-MM-DD), default: heute
            bis: End-Datum (YYYY-MM-DD), default: +14 Tage
            standort: 'all', 'DEG', 'LAN'

        Returns:
            Dict mit:
                - fahrzeuge: Liste der Fahrzeuge mit DB1
                - tage: Aggregation nach Tag
                - summe: Gesamt-Summen
        """
        if von is None:
            von = date.today().strftime('%Y-%m-%d')
        if bis is None:
            bis = (date.today() + timedelta(days=14)).strftime('%Y-%m-%d')

        try:
            with locosoft_session() as conn:
                cursor = conn.cursor()

                standort_filter = ""
                if standort == 'DEG':
                    standort_filter = "AND v.subsidiary = 2"
                elif standort == 'LAN':
                    standort_filter = "AND v.subsidiary = 1"

                cursor.execute(f"""
                    SELECT
                        v.readmission_date as lieferung,
                        v.vin,
                        v.dealer_vehicle_type as typ,
                        v.dealer_vehicle_number as haendler_nr,
                        v.license_plate as kennzeichen,
                        v.subsidiary as filiale,
                        o.number as auftrag_nr,
                        CASE
                            WHEN o.has_open_positions = true AND o.has_closed_positions = true THEN 'VORFAKTURIERT'
                            WHEN o.has_open_positions = false AND o.has_closed_positions = true THEN 'FAKTURIERT'
                            ELSE 'OFFEN'
                        END as status,
                        COALESCE(SUM(i.total_gross), 0) as brutto,
                        COALESCE(SUM(i.total_net), 0) as netto
                    FROM vehicles v
                    JOIN orders o ON v.dealer_vehicle_number = o.dealer_vehicle_number
                                  AND v.dealer_vehicle_type = o.dealer_vehicle_type
                    LEFT JOIN invoices i ON o.number = i.order_number
                    WHERE v.readmission_date BETWEEN %s AND %s
                      AND v.dealer_vehicle_type IN ('N', 'V', 'T')
                      {standort_filter}
                    GROUP BY v.readmission_date, v.vin, v.dealer_vehicle_type,
                             v.dealer_vehicle_number, v.license_plate, v.subsidiary,
                             o.number, o.has_open_positions, o.has_closed_positions
                    ORDER BY v.readmission_date, v.vin
                """, (von, bis))

                rows = cursor.fetchall()

                # Nach Fahrzeug gruppieren
                fahrzeuge_dict = {}
                for row in rows:
                    vin = row['vin']
                    if vin not in fahrzeuge_dict:
                        fahrzeuge_dict[vin] = {
                            'lieferung': str(row['lieferung']),
                            'vin': vin,
                            'typ': row['typ'],
                            'haendler_nr': row['haendler_nr'],
                            'kennzeichen': row['kennzeichen'],
                            'standort': 'DEG' if row['filiale'] == 2 else 'LAN',
                            'auftraege': [],
                            'brutto_gesamt': 0,
                            'netto_gesamt': 0,
                            'status': 'OFFEN',
                            'db1': 0,
                            'db1_prozent': 0,
                            'marke': '-',
                            'modell': '-'
                        }

                    brutto = float(row['brutto']) if row['brutto'] else 0
                    netto = float(row['netto']) if row['netto'] else 0

                    fahrzeuge_dict[vin]['auftraege'].append({
                        'nummer': row['auftrag_nr'],
                        'status': row['status'],
                        'brutto': round(brutto, 2),
                        'netto': round(netto, 2)
                    })
                    fahrzeuge_dict[vin]['brutto_gesamt'] += brutto
                    fahrzeuge_dict[vin]['netto_gesamt'] += netto

                    if row['status'] == 'VORFAKTURIERT':
                        fahrzeuge_dict[vin]['status'] = 'VORFAKTURIERT'
                    elif row['status'] == 'FAKTURIERT' and fahrzeuge_dict[vin]['status'] != 'VORFAKTURIERT':
                        fahrzeuge_dict[vin]['status'] = 'FAKTURIERT'

                # Runden
                for vin in fahrzeuge_dict:
                    fahrzeuge_dict[vin]['brutto_gesamt'] = round(fahrzeuge_dict[vin]['brutto_gesamt'], 2)
                    fahrzeuge_dict[vin]['netto_gesamt'] = round(fahrzeuge_dict[vin]['netto_gesamt'], 2)

            # DB1-Daten aus DRIVE Portal laden
            if fahrzeuge_dict:
                with db_session() as drive_conn:
                    drive_cursor = drive_conn.cursor()
                    vins = list(fahrzeuge_dict.keys())
                    ph = sql_placeholder()
                    placeholders = ','.join([ph for _ in vins])

                    drive_cursor.execute(f"""
                        SELECT
                            vin,
                            COALESCE(deckungsbeitrag, 0) as db1,
                            COALESCE(db_prozent, 0) as db1_prozent,
                            make_number,
                            model_description
                        FROM sales
                        WHERE vin IN ({placeholders})
                          AND out_invoice_date IS NOT NULL
                    """, vins)

                    for row in drive_cursor.fetchall():
                        vin = row['vin']
                        if vin in fahrzeuge_dict:
                            fahrzeuge_dict[vin]['db1'] = round(float(row['db1']), 2)
                            fahrzeuge_dict[vin]['db1_prozent'] = round(float(row['db1_prozent']), 1)
                            fahrzeuge_dict[vin]['marke'] = MARKEN.get(row['make_number'], f"Marke {row['make_number']}")
                            fahrzeuge_dict[vin]['modell'] = row['model_description'] or '-'

            fahrzeuge = list(fahrzeuge_dict.values())

            # Tages-Aggregation
            tage = {}
            for fz in fahrzeuge:
                tag = fz['lieferung']
                if tag not in tage:
                    tage[tag] = {
                        'datum': tag,
                        'fahrzeuge': 0,
                        'brutto': 0,
                        'vorfakturiert': 0,
                        'fakturiert': 0,
                        'db1': 0
                    }
                tage[tag]['fahrzeuge'] += 1
                tage[tag]['brutto'] += fz['brutto_gesamt']
                tage[tag]['db1'] += fz['db1']
                if fz['status'] == 'VORFAKTURIERT':
                    tage[tag]['vorfakturiert'] += fz['brutto_gesamt']
                elif fz['status'] == 'FAKTURIERT':
                    tage[tag]['fakturiert'] += fz['brutto_gesamt']

            tage_liste = []
            for tag in sorted(tage.keys()):
                tage[tag]['brutto'] = round(tage[tag]['brutto'], 2)
                tage[tag]['vorfakturiert'] = round(tage[tag]['vorfakturiert'], 2)
                tage[tag]['fakturiert'] = round(tage[tag]['fakturiert'], 2)
                tage[tag]['db1'] = round(tage[tag]['db1'], 2)
                tage_liste.append(tage[tag])

            # Summen
            total_db1 = sum(f['db1'] for f in fahrzeuge)
            total_netto = sum(f['netto_gesamt'] for f in fahrzeuge)
            avg_db1_prozent = round((total_db1 / total_netto * 100) if total_netto > 0 else 0, 1)

            summe = {
                'fahrzeuge': len(fahrzeuge),
                'brutto': round(sum(f['brutto_gesamt'] for f in fahrzeuge), 2),
                'netto': round(total_netto, 2),
                'vorfakturiert': round(sum(f['brutto_gesamt'] for f in fahrzeuge if f['status'] == 'VORFAKTURIERT'), 2),
                'fakturiert': round(sum(f['brutto_gesamt'] for f in fahrzeuge if f['status'] == 'FAKTURIERT'), 2),
                'db1': round(total_db1, 2),
                'db1_prozent': avg_db1_prozent
            }

            return {
                'success': True,
                'von': von,
                'bis': bis,
                'standort': standort,
                'fahrzeuge': fahrzeuge,
                'tage': tage_liste,
                'summe': summe
            }

        except Exception as e:
            logger.error(f"Fehler in get_lieferforecast: {e}")
            return {
                'success': False,
                'error': str(e),
                'fahrzeuge': [],
                'tage': [],
                'summe': {}
            }

    @staticmethod
    def get_verkaufer_performance(
        month: int = None,
        year: int = None,
        verkaufer: int = None
    ) -> Dict[str, Any]:
        """
        Holt Performance-Kennzahlen pro Verkäufer.

        Args:
            month: Monat (1-12)
            year: Jahr
            verkaufer: Optional: nur für einen Verkäufer

        Returns:
            Dict mit Performance-Daten pro Verkäufer:
                - auftraege_nw/gw
                - auslieferungen_nw/gw
                - umsatz_nw/gw
                - db1_nw/gw
                - db1_prozent
        """
        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year

        try:
            with db_session() as conn:
                cursor = conn.cursor()

                where_clauses = ["s.salesman_number IS NOT NULL"]
                params = [str(year), f"{month:02d}"]

                if verkaufer:
                    where_clauses.append("s.salesman_number = %s")
                    params.append(int(verkaufer))

                where_clauses.append("""
                    NOT EXISTS (
                        SELECT 1 FROM sales s2
                        WHERE s2.vin = s.vin
                            AND s2.out_sales_contract_date = s.out_sales_contract_date
                            AND s2.dealer_vehicle_type IN ('T', 'V')
                            AND s.dealer_vehicle_type = 'N'
                    )
                """)

                where_sql = " AND ".join(where_clauses)

                # Auftragseingang
                cursor.execute(f"""
                    SELECT
                        s.salesman_number,
                        COALESCE(e.first_name || ' ' || e.last_name,
                                 'Verkäufer #' || s.salesman_number) as verkaufer_name,
                        SUM(CASE WHEN s.dealer_vehicle_type IN ('N', 'V') THEN 1 ELSE 0 END) as auftraege_nw,
                        SUM(CASE WHEN s.dealer_vehicle_type IN ('G', 'D', 'T') THEN 1 ELSE 0 END) as auftraege_gw
                    FROM sales s
                    LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
                    WHERE EXTRACT(YEAR FROM s.out_sales_contract_date) = %s
                      AND EXTRACT(MONTH FROM s.out_sales_contract_date) = %s
                      AND {where_sql}
                    GROUP BY s.salesman_number, verkaufer_name
                """, params)

                auftraege = {row['salesman_number']: dict(row) for row in cursor.fetchall()}

                # Auslieferungen
                cursor.execute(f"""
                    SELECT
                        s.salesman_number,
                        SUM(CASE WHEN s.dealer_vehicle_type IN ('N', 'V') THEN 1 ELSE 0 END) as auslieferungen_nw,
                        SUM(CASE WHEN s.dealer_vehicle_type IN ('G', 'D', 'T') THEN 1 ELSE 0 END) as auslieferungen_gw,
                        SUM(CASE WHEN s.dealer_vehicle_type IN ('N', 'V') THEN COALESCE(s.out_sale_price, 0) ELSE 0 END) as umsatz_nw,
                        SUM(CASE WHEN s.dealer_vehicle_type IN ('G', 'D', 'T') THEN COALESCE(s.out_sale_price, 0) ELSE 0 END) as umsatz_gw,
                        SUM(CASE WHEN s.dealer_vehicle_type IN ('N', 'V') THEN COALESCE(s.deckungsbeitrag, 0) ELSE 0 END) as db1_nw,
                        SUM(CASE WHEN s.dealer_vehicle_type IN ('G', 'D', 'T') THEN COALESCE(s.deckungsbeitrag, 0) ELSE 0 END) as db1_gw
                    FROM sales s
                    WHERE EXTRACT(YEAR FROM s.out_invoice_date) = %s
                      AND EXTRACT(MONTH FROM s.out_invoice_date) = %s
                      AND s.out_invoice_date IS NOT NULL
                      AND {where_sql}
                    GROUP BY s.salesman_number
                """, params)

                auslieferungen = {row['salesman_number']: dict(row) for row in cursor.fetchall()}

                # Zusammenführen
                performance = []
                all_vk = set(auftraege.keys()) | set(auslieferungen.keys())

                for vk_nr in all_vk:
                    ae = auftraege.get(vk_nr, {})
                    al = auslieferungen.get(vk_nr, {})

                    umsatz_nw = _convert_decimal(al.get('umsatz_nw', 0))
                    umsatz_gw = _convert_decimal(al.get('umsatz_gw', 0))
                    db1_nw = _convert_decimal(al.get('db1_nw', 0))
                    db1_gw = _convert_decimal(al.get('db1_gw', 0))

                    total_umsatz = umsatz_nw + umsatz_gw
                    total_db1 = db1_nw + db1_gw

                    performance.append({
                        'verkaufer_nummer': vk_nr,
                        'verkaufer_name': ae.get('verkaufer_name', f'Verkäufer #{vk_nr}'),
                        'auftraege_nw': ae.get('auftraege_nw', 0) or 0,
                        'auftraege_gw': ae.get('auftraege_gw', 0) or 0,
                        'auslieferungen_nw': al.get('auslieferungen_nw', 0) or 0,
                        'auslieferungen_gw': al.get('auslieferungen_gw', 0) or 0,
                        'umsatz_nw': round(umsatz_nw, 2),
                        'umsatz_gw': round(umsatz_gw, 2),
                        'umsatz_gesamt': round(total_umsatz, 2),
                        'db1_nw': round(db1_nw, 2),
                        'db1_gw': round(db1_gw, 2),
                        'db1_gesamt': round(total_db1, 2),
                        'db1_prozent': round((total_db1 / (total_umsatz / 1.19) * 100) if total_umsatz > 0 else 0, 1)
                    })

                performance.sort(key=lambda x: x['verkaufer_name'])

                return {
                    'success': True,
                    'month': month,
                    'year': year,
                    'performance': performance
                }

        except Exception as e:
            logger.error(f"Fehler in get_verkaufer_performance: {e}")
            return {'success': False, 'error': str(e), 'performance': []}


# ==============================================================================
# STANDALONE WRAPPER FUNCTIONS
# ==============================================================================

def get_auftragseingang(month: int = None, year: int = None) -> Dict[str, Any]:
    """Wrapper für VerkaufData.get_auftragseingang()"""
    return VerkaufData.get_auftragseingang(month, year)

def get_auftragseingang_summary(day: str = None, month: int = None, year: int = None) -> Dict[str, Any]:
    """Wrapper für VerkaufData.get_auftragseingang_summary()"""
    return VerkaufData.get_auftragseingang_summary(day, month, year)

def get_auftragseingang_detail(day: str = None, month: int = None, year: int = None,
                               location: int = None, verkaufer: int = None) -> Dict[str, Any]:
    """Wrapper für VerkaufData.get_auftragseingang_detail()"""
    return VerkaufData.get_auftragseingang_detail(day, month, year, location, verkaufer)

def get_auslieferung_summary(day: str = None, month: int = None, year: int = None) -> Dict[str, Any]:
    """Wrapper für VerkaufData.get_auslieferung_summary()"""
    return VerkaufData.get_auslieferung_summary(day, month, year)

def get_auslieferung_detail(day: str = None, month: int = None, year: int = None,
                            location: int = None, verkaufer: int = None,
                            vin_search: str = None) -> Dict[str, Any]:
    """Wrapper für VerkaufData.get_auslieferung_detail()"""
    return VerkaufData.get_auslieferung_detail(day, month, year, location, verkaufer, vin_search)

def get_verkaufer_liste() -> Dict[str, Any]:
    """Wrapper für VerkaufData.get_verkaufer_liste()"""
    return VerkaufData.get_verkaufer_liste()

def get_lieferforecast(von: str = None, bis: str = None, standort: str = 'all') -> Dict[str, Any]:
    """Wrapper für VerkaufData.get_lieferforecast()"""
    return VerkaufData.get_lieferforecast(von, bis, standort)

def get_verkaufer_performance(month: int = None, year: int = None,
                              verkaufer: int = None) -> Dict[str, Any]:
    """Wrapper für VerkaufData.get_verkaufer_performance()"""
    return VerkaufData.get_verkaufer_performance(month, year, verkaufer)
