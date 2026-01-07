#!/usr/bin/env python3
"""
FAHRZEUG DATA MODULE - Single Source of Truth für Fahrzeugbestand
==================================================================
Datenmodul für alle Fahrzeug-bezogenen Auswertungen direkt aus Locosoft.

Architektur:
- Class-based Pattern (FahrzeugData)
- Statische Methoden für wiederverwendbare Datenabfragen
- Nutzt echte Locosoft-Tabellen (dealer_vehicles, vehicles)
- Keine Business Logic (nur Datenabruf + Aggregation)
- PostgreSQL-kompatibel

Consumer:
- api/verkauf_api.py (Verkaufs-Endpoints)
- templates/verkauf/gw_bestand.html (GW-Dashboard)
- scripts/send_gw_standzeit_report.py (E-Mail Reports)

Author: Claude Opus 4.5
Date: 2026-01-02 (TAG 158)
Pattern: Nach Vorbild werkstatt_data.py

Locosoft-Tabellen:
- dealer_vehicles: Händlerfahrzeuge (Bestand, Kalkulation)
- vehicles: Fahrzeug-Stammdaten (FIN, Modell, EZ)

Fahrzeugtypen (dealer_vehicle_type):
- N = Neuwagen
- G = Gebrauchtwagen
- D = Demo/Vorführwagen
- V = Vermietwagen
- T = Tauschfahrzeug
"""

from datetime import datetime, timedelta, date
from typing import Optional, Dict, List, Any
import logging

# Zentrale DB-Utilities
from api.db_utils import locosoft_session, db_session, row_to_dict, rows_to_list
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# =============================================================================
# KONSTANTEN
# =============================================================================

STANDORT_NAMEN = {
    1: 'DEG Opel',
    2: 'DEG Hyundai',
    3: 'Landau'
}

FAHRZEUGTYP_NAMEN = {
    'N': 'Neuwagen',
    'G': 'Gebrauchtwagen',
    'D': 'Vorführwagen',
    'V': 'Vermietwagen',
    'T': 'Tauschfahrzeug'
}

# Standzeit-Kategorien (in Tagen)
# Neutral benannt fuer professionellen Einsatz
STANDZEIT_KATEGORIEN = {
    'frisch': (0, 60),      # 0-60 Tage - Gut
    'normal': (61, 90),     # 61-90 Tage - Normal
    'erhoht': (91, 120),    # 91-120 Tage - Erhoehtes Risiko
    'kritisch': (121, 180), # 121-180 Tage - Kritisch
    'dringend': (181, 9999) # >180 Tage - Dringender Handlungsbedarf
}

STANDZEIT_LABELS = {
    'frisch': '0-60 Tage',
    'normal': '61-90 Tage',
    'erhoht': '91-120 Tage',
    'kritisch': '121-180 Tage',
    'dringend': '>180 Tage'
}

STANDZEIT_FARBEN = {
    'frisch': 'success',
    'normal': 'info',
    'erhoht': 'warning',
    'kritisch': 'danger',
    'dringend': 'dark'
}


# =============================================================================
# FAHRZEUG DATA CLASS
# =============================================================================

class FahrzeugData:
    """
    Single Source of Truth für Fahrzeug-Bestandsdaten aus Locosoft.

    Bereiche:
    - Bestand: get_gw_bestand(), get_nw_pipeline(), get_vfw_bestand()
    - Standzeit: get_standzeit_statistik(), get_standzeit_warnungen()
    - Kalkulation: get_fahrzeug_detail()
    """

    # =========================================================================
    # GW BESTAND
    # =========================================================================

    @staticmethod
    def get_gw_bestand(
        standort: Optional[int] = None,
        kategorie: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Holt aktuellen GW-Bestand aus Locosoft dealer_vehicles.

        Args:
            standort: Standort-Filter (1=DEG Opel, 2=HYU, 3=LAN, None=alle)
            kategorie: Standzeit-Kategorie ('frisch', 'ok', 'risiko', 'penner', 'leiche')
            limit: Max. Anzahl Fahrzeuge

        Returns:
            Dict mit 'fahrzeuge' (Liste) und 'statistik' (Zusammenfassung)

        Example:
            >>> data = FahrzeugData.get_gw_bestand(standort=1, kategorie='penner')
            >>> len(data['fahrzeuge'])
            20
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Filter bauen
            where_parts = [
                "dv.out_invoice_date IS NULL",  # Noch nicht verkauft
                "dv.dealer_vehicle_type = 'G'"  # Gebrauchtwagen
            ]
            params = []

            if standort:
                where_parts.append("dv.in_subsidiary = %s")
                params.append(standort)

            # Standzeit-Kategorie-Filter
            if kategorie and kategorie in STANDZEIT_KATEGORIEN:
                min_tage, max_tage = STANDZEIT_KATEGORIEN[kategorie]
                where_parts.append(
                    f"CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date) BETWEEN {min_tage} AND {max_tage}"
                )

            where_clause = " AND ".join(where_parts)
            limit_clause = f"LIMIT {limit}" if limit else ""

            # Hauptabfrage - mit korrekten Locosoft Kalkulationsfeldern
            # EK = Einsatzwert (Grundpreis + Zubehoer + Fracht/Nebenkosten + Einsatzerhoehungen)
            #
            # Besteuerungsarten (out_sale_type = Verkaufs-Besteuerung):
            # F = Faktura/Regelbesteuerung -> VK/1.19
            # B = Brutto/Differenzbesteuerung §25a -> Marge/1.19
            # L = Leasing
            #
            # DB-Berechnung:
            # Regelbesteuerung (F): DB = VK/1.19 - EK - Kosten
            # Differenz §25a (B): DB = (VK - EK) / 1.19 - Kosten = Marge netto
            query = f"""
                SELECT
                    dv.dealer_vehicle_number,
                    v.license_plate,
                    v.vin,
                    v.free_form_model_text as modell,
                    v.first_registration_date as ez,
                    dv.in_arrival_date as eingang,
                    dv.created_date,
                    CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date) as standzeit_tage,
                    dv.mileage_km as km_stand,
                    dv.in_used_vehicle_buy_type as ankauf_typ,
                    dv.out_sale_type as verkauf_typ,
                    -- EK = Einsatzwert (Grundpreis + Zubehoer + Fracht + Einsatzerhoehungen)
                    COALESCE(dv.calc_basic_charge, 0) + COALESCE(dv.calc_accessory, 0)
                        + COALESCE(dv.calc_extra_expenses, 0)
                        + COALESCE(dv.calc_usage_value_encr_internal, 0)
                        + COALESCE(dv.calc_usage_value_encr_external, 0) as ek_preis,
                    -- VK brutto (inkl. MwSt) - zur Anzeige
                    COALESCE(dv.out_sale_price, 0) as vk_preis_brutto,
                    -- VK effektiv: Bei Regel (F) = VK/1.19, bei Diff (B) = VK - MwSt_auf_Marge
                    CASE
                        WHEN dv.out_sale_type = 'F'
                        THEN ROUND(COALESCE(dv.out_sale_price, 0) / 1.19, 2)
                        ELSE ROUND(COALESCE(dv.out_sale_price, 0) - (
                            GREATEST(COALESCE(dv.out_sale_price, 0) - (
                                COALESCE(dv.calc_basic_charge, 0) + COALESCE(dv.calc_accessory, 0)
                                + COALESCE(dv.calc_extra_expenses, 0)
                                + COALESCE(dv.calc_usage_value_encr_internal, 0)
                                + COALESCE(dv.calc_usage_value_encr_external, 0)
                            ), 0) / 1.19 * 0.19
                        ), 2)
                    END as vk_preis,
                    -- Variable VK-Kosten (Werkstatt-Rechnungen etc.)
                    COALESCE(dv.calc_cost_internal_invoices, 0) as kosten_intern,
                    -- Kalk. DB I (basierend auf out_sale_type)
                    -- Regel (F): VK/1.19 - EK - Kosten
                    -- Diff25a (B): (VK - EK) / 1.19 - Kosten = Marge netto
                    CASE
                        WHEN dv.out_sale_type = 'F'
                        THEN ROUND(COALESCE(dv.out_sale_price, 0) / 1.19, 2) - (
                            COALESCE(dv.calc_basic_charge, 0) + COALESCE(dv.calc_accessory, 0)
                            + COALESCE(dv.calc_extra_expenses, 0)
                            + COALESCE(dv.calc_usage_value_encr_internal, 0)
                            + COALESCE(dv.calc_usage_value_encr_external, 0)
                        ) - COALESCE(dv.calc_cost_internal_invoices, 0)
                        ELSE ROUND(
                            GREATEST(COALESCE(dv.out_sale_price, 0) - (
                                COALESCE(dv.calc_basic_charge, 0) + COALESCE(dv.calc_accessory, 0)
                                + COALESCE(dv.calc_extra_expenses, 0)
                                + COALESCE(dv.calc_usage_value_encr_internal, 0)
                                + COALESCE(dv.calc_usage_value_encr_external, 0)
                            ), 0) / 1.19, 2
                        ) - COALESCE(dv.calc_cost_internal_invoices, 0)
                    END as kalk_db,
                    -- Besteuerungsart fuer Anzeige
                    CASE
                        WHEN dv.out_sale_type = 'F' THEN 'Regel'
                        ELSE 'Diff25a'
                    END as besteuerung,
                    dv.in_subsidiary as standort,
                    dv.location as lagerort,
                    -- Zusatzfelder fuer detaillierte Kalkulation
                    dv.calc_cost_percent_stockingdays as standkosten_pct
                FROM dealer_vehicles dv
                LEFT JOIN vehicles v ON dv.vehicle_number = v.internal_number
                WHERE {where_clause}
                ORDER BY standzeit_tage DESC NULLS LAST
                {limit_clause}
            """

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Fahrzeuge aufbereiten
            fahrzeuge = []
            for row in rows:
                standzeit = row['standzeit_tage'] or 0
                fahrzeug = dict(row)
                fahrzeug['standzeit_kategorie'] = FahrzeugData._get_standzeit_kategorie(standzeit)
                fahrzeug['standort_name'] = STANDORT_NAMEN.get(row['standort'], 'Unbekannt')
                fahrzeuge.append(fahrzeug)

            # Statistik berechnen
            statistik = FahrzeugData._berechne_bestand_statistik(fahrzeuge)

            logger.info(f"FahrzeugData.get_gw_bestand: {len(fahrzeuge)} GW, Standort={standort}, Kategorie={kategorie}")

            return {
                'fahrzeuge': fahrzeuge,
                'statistik': statistik,
                'filter': {
                    'standort': standort,
                    'kategorie': kategorie
                },
                'stand': datetime.now().isoformat()
            }

    # =========================================================================
    # NW PIPELINE
    # =========================================================================

    @staticmethod
    def get_nw_pipeline(
        standort: Optional[int] = None,
        nur_mit_vertrag: bool = False
    ) -> Dict[str, Any]:
        """
        Holt bestellte Neuwagen die noch nicht fakturiert wurden.

        Args:
            standort: Standort-Filter
            nur_mit_vertrag: Nur Fahrzeuge mit Kundenvertrag

        Returns:
            Dict mit 'fahrzeuge' und 'statistik'
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            where_parts = [
                "dv.out_invoice_date IS NULL",
                "dv.dealer_vehicle_type = 'N'"
            ]
            params = []

            if standort:
                where_parts.append("dv.in_subsidiary = %s")
                params.append(standort)

            if nur_mit_vertrag:
                where_parts.append("dv.out_sales_contract_number IS NOT NULL")

            where_clause = " AND ".join(where_parts)

            query = f"""
                SELECT
                    dv.dealer_vehicle_number,
                    v.license_plate,
                    v.free_form_model_text as modell,
                    dv.in_buy_order_no_date as bestell_datum,
                    dv.in_expected_arrival_date as erwartet,
                    dv.in_arrival_date as eingang,
                    dv.in_buy_list_price  as ek_preis,
                    dv.out_recommended_retail_price  as vk_preis,
                    (COALESCE(dv.out_recommended_retail_price, 0) - COALESCE(dv.in_buy_list_price, 0))  as kalk_db,
                    dv.out_sales_contract_number as vertrag_nr,
                    dv.out_sales_contract_date as vertrag_datum,
                    dv.buyer_customer_no as kunde_nr,
                    dv.in_subsidiary as standort
                FROM dealer_vehicles dv
                LEFT JOIN vehicles v ON dv.vehicle_number = v.internal_number
                WHERE {where_clause}
                ORDER BY dv.in_buy_order_no_date DESC NULLS LAST
            """

            cursor.execute(query, params)
            rows = cursor.fetchall()

            fahrzeuge = []
            for row in rows:
                fahrzeug = dict(row)
                fahrzeug['standort_name'] = STANDORT_NAMEN.get(row['standort'], 'Unbekannt')
                fahrzeug['hat_vertrag'] = bool(row['vertrag_nr'])
                fahrzeuge.append(fahrzeug)

            # Statistik
            summe_ek = sum(f['ek_preis'] or 0 for f in fahrzeuge)
            summe_vk = sum(f['vk_preis'] or 0 for f in fahrzeuge)
            summe_db = sum(f['kalk_db'] or 0 for f in fahrzeuge)
            mit_vertrag = sum(1 for f in fahrzeuge if f['hat_vertrag'])

            statistik = {
                'anzahl': len(fahrzeuge),
                'mit_vertrag': mit_vertrag,
                'ohne_vertrag': len(fahrzeuge) - mit_vertrag,
                'summe_ek': round(summe_ek, 2),
                'summe_vk': round(summe_vk, 2),
                'summe_db': round(summe_db, 2),
                'avg_db': round(summe_db / len(fahrzeuge), 2) if fahrzeuge else 0
            }

            logger.info(f"FahrzeugData.get_nw_pipeline: {len(fahrzeuge)} NW, Standort={standort}")

            return {
                'fahrzeuge': fahrzeuge,
                'statistik': statistik,
                'stand': datetime.now().isoformat()
            }

    # =========================================================================
    # VFW BESTAND
    # =========================================================================

    @staticmethod
    def get_vfw_bestand(standort: Optional[int] = None) -> Dict[str, Any]:
        """
        Holt aktuellen Vorführwagen-Bestand.

        Args:
            standort: Standort-Filter

        Returns:
            Dict mit 'fahrzeuge' und 'statistik'
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            where_parts = [
                "dv.out_invoice_date IS NULL",
                "dv.dealer_vehicle_type = 'D'"  # Demo/VFW
            ]
            params = []

            if standort:
                where_parts.append("dv.in_subsidiary = %s")
                params.append(standort)

            where_clause = " AND ".join(where_parts)

            query = f"""
                SELECT
                    dv.dealer_vehicle_number,
                    v.license_plate,
                    v.free_form_model_text as modell,
                    v.first_registration_date as ez,
                    dv.in_arrival_date as eingang,
                    CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date) as alter_tage,
                    dv.mileage_km as km_stand,
                    dv.in_buy_list_price  as ek_preis,
                    dv.in_subsidiary as standort
                FROM dealer_vehicles dv
                LEFT JOIN vehicles v ON dv.vehicle_number = v.internal_number
                WHERE {where_clause}
                ORDER BY alter_tage DESC NULLS LAST
            """

            cursor.execute(query, params)
            rows = cursor.fetchall()

            fahrzeuge = []
            for row in rows:
                fahrzeug = dict(row)
                fahrzeug['standort_name'] = STANDORT_NAMEN.get(row['standort'], 'Unbekannt')
                fahrzeuge.append(fahrzeug)

            statistik = {
                'anzahl': len(fahrzeuge),
                'avg_alter': round(sum(f['alter_tage'] or 0 for f in fahrzeuge) / len(fahrzeuge), 0) if fahrzeuge else 0,
                'avg_km': round(sum(f['km_stand'] or 0 for f in fahrzeuge) / len(fahrzeuge), 0) if fahrzeuge else 0
            }

            logger.info(f"FahrzeugData.get_vfw_bestand: {len(fahrzeuge)} VFW")

            return {
                'fahrzeuge': fahrzeuge,
                'statistik': statistik,
                'stand': datetime.now().isoformat()
            }

    # =========================================================================
    # STANDZEIT STATISTIK
    # =========================================================================

    @staticmethod
    def get_standzeit_statistik(standort: Optional[int] = None) -> Dict[str, Any]:
        """
        Aggregierte Standzeit-Statistik für GW-Bestand.

        Args:
            standort: Standort-Filter

        Returns:
            Dict mit Kategorien und Summen
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            standort_filter = ""
            params = []
            if standort:
                standort_filter = "AND dv.in_subsidiary = %s"
                params.append(standort)

            query = f"""
                SELECT kategorie, anzahl, avg_standzeit, summe_vk
                FROM (
                    SELECT
                        CASE
                            WHEN CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date) <= 60 THEN 'frisch'
                            WHEN CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date) <= 90 THEN 'normal'
                            WHEN CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date) <= 120 THEN 'erhoht'
                            WHEN CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date) <= 180 THEN 'kritisch'
                            ELSE 'dringend'
                        END as kategorie,
                        COUNT(*) as anzahl,
                        ROUND(AVG(CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date))) as avg_standzeit,
                        SUM(COALESCE(dv.out_sale_price, 0))  as summe_vk
                    FROM dealer_vehicles dv
                    WHERE dv.out_invoice_date IS NULL
                      AND dv.dealer_vehicle_type = 'G'
                      {standort_filter}
                    GROUP BY 1
                ) sub
                ORDER BY
                    CASE kategorie
                        WHEN 'frisch' THEN 1
                        WHEN 'normal' THEN 2
                        WHEN 'erhoht' THEN 3
                        WHEN 'kritisch' THEN 4
                        WHEN 'dringend' THEN 5
                    END
            """

            cursor.execute(query, params)
            rows = cursor.fetchall()

            kategorien = {}
            gesamt_anzahl = 0
            gesamt_wert = 0

            for row in rows:
                kat = row['kategorie']
                kategorien[kat] = {
                    'anzahl': row['anzahl'],
                    'avg_standzeit': row['avg_standzeit'] or 0,
                    'summe_vk': round(row['summe_vk'] or 0, 2),
                    'label': STANDZEIT_LABELS.get(kat, kat),
                    'farbe': STANDZEIT_FARBEN.get(kat, 'secondary')
                }
                gesamt_anzahl += row['anzahl']
                gesamt_wert += row['summe_vk'] or 0

            # Problemfaelle zaehlen (erhoht + kritisch + dringend = >90 Tage)
            problem_anzahl = sum(
                kategorien.get(k, {}).get('anzahl', 0)
                for k in ['erhoht', 'kritisch', 'dringend']
            )
            problem_wert = sum(
                kategorien.get(k, {}).get('summe_vk', 0)
                for k in ['erhoht', 'kritisch', 'dringend']
            )

            logger.info(f"FahrzeugData.get_standzeit_statistik: {gesamt_anzahl} GW, {problem_anzahl} Problemfälle")

            return {
                'kategorien': kategorien,
                'gesamt': {
                    'anzahl': gesamt_anzahl,
                    'summe_vk': round(gesamt_wert, 2)
                },
                'problemfaelle': {
                    'anzahl': problem_anzahl,
                    'summe_vk': round(problem_wert, 2),
                    'anteil_pct': round(problem_anzahl / gesamt_anzahl * 100, 1) if gesamt_anzahl else 0
                },
                'standort': standort,
                'stand': datetime.now().isoformat()
            }

    # =========================================================================
    # STANDZEIT WARNUNGEN
    # =========================================================================

    @staticmethod
    def get_standzeit_warnungen(
        min_tage: int = 90,
        standort: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Holt Fahrzeuge die Aufmerksamkeit brauchen (Standzeit > min_tage).

        Args:
            min_tage: Mindest-Standzeit für Warnung (default: 90)
            standort: Standort-Filter

        Returns:
            Dict mit 'warnungen' (Liste) und 'statistik'
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            standort_filter = ""
            params = [min_tage]
            if standort:
                standort_filter = "AND dv.in_subsidiary = %s"
                params.append(standort)

            query = f"""
                SELECT
                    dv.dealer_vehicle_number,
                    v.license_plate,
                    v.free_form_model_text as modell,
                    CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date) as standzeit_tage,
                    dv.out_recommended_retail_price  as vk_preis,
                    dv.in_subsidiary as standort
                FROM dealer_vehicles dv
                LEFT JOIN vehicles v ON dv.vehicle_number = v.internal_number
                WHERE dv.out_invoice_date IS NULL
                  AND dv.dealer_vehicle_type = 'G'
                  AND CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date) >= %s
                  {standort_filter}
                ORDER BY standzeit_tage DESC
            """

            cursor.execute(query, params)
            rows = cursor.fetchall()

            warnungen = []
            for row in rows:
                warnung = dict(row)
                warnung['standort_name'] = STANDORT_NAMEN.get(row['standort'], 'Unbekannt')
                warnung['kategorie'] = FahrzeugData._get_standzeit_kategorie(row['standzeit_tage'])
                warnung['dringlichkeit'] = 'hoch' if row['standzeit_tage'] > 180 else 'mittel'
                warnungen.append(warnung)

            statistik = {
                'anzahl': len(warnungen),
                'summe_vk': round(sum(w['vk_preis'] or 0 for w in warnungen), 2),
                'avg_standzeit': round(sum(w['standzeit_tage'] for w in warnungen) / len(warnungen), 0) if warnungen else 0
            }

            return {
                'warnungen': warnungen,
                'statistik': statistik,
                'min_tage': min_tage,
                'stand': datetime.now().isoformat()
            }

    # =========================================================================
    # BESTAND NACH STANDORT
    # =========================================================================

    @staticmethod
    def get_bestand_nach_standort() -> Dict[str, Any]:
        """
        Bestandsübersicht gruppiert nach Standort.

        Returns:
            Dict mit Standort-Statistiken
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT
                    dv.in_subsidiary as standort,
                    dv.dealer_vehicle_type as typ,
                    COUNT(*) as anzahl,
                    ROUND(AVG(CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date))) as avg_standzeit,
                    SUM(COALESCE(dv.out_recommended_retail_price, 0))  as summe_vk
                FROM dealer_vehicles dv
                WHERE dv.out_invoice_date IS NULL
                GROUP BY dv.in_subsidiary, dv.dealer_vehicle_type
                ORDER BY dv.in_subsidiary, dv.dealer_vehicle_type
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            standorte = {}
            for row in rows:
                standort_id = row['standort']
                if standort_id not in standorte:
                    standorte[standort_id] = {
                        'name': STANDORT_NAMEN.get(standort_id, f'Standort {standort_id}'),
                        'typen': {},
                        'gesamt_anzahl': 0,
                        'gesamt_wert': 0
                    }

                typ = row['typ']
                standorte[standort_id]['typen'][typ] = {
                    'name': FAHRZEUGTYP_NAMEN.get(typ, typ),
                    'anzahl': row['anzahl'],
                    'avg_standzeit': row['avg_standzeit'] or 0,
                    'summe_vk': round(row['summe_vk'] or 0, 2)
                }
                standorte[standort_id]['gesamt_anzahl'] += row['anzahl']
                standorte[standort_id]['gesamt_wert'] += row['summe_vk'] or 0

            return {
                'standorte': standorte,
                'stand': datetime.now().isoformat()
            }

    # =========================================================================
    # HELPER FUNCTIONS
    # =========================================================================

    @staticmethod
    def _get_standzeit_kategorie(tage: int) -> str:
        """Ermittelt Standzeit-Kategorie anhand Tage."""
        if tage is None:
            return 'unbekannt'
        for kat, (min_t, max_t) in STANDZEIT_KATEGORIEN.items():
            if min_t <= tage <= max_t:
                return kat
        return 'leiche'

    # =========================================================================
    # FINANZIERUNG + ZINSEN (aus DRIVE Portal)
    # =========================================================================

    @staticmethod
    def get_gw_mit_finanzierung(standort: Optional[int] = None) -> Dict[str, Any]:
        """
        GW-Bestand mit Finanzierungsdaten aus DRIVE Portal angereichert.

        Verbindet Locosoft dealer_vehicles mit DRIVE fahrzeugfinanzierungen
        ueber VIN-Matching.

        Args:
            standort: Standort-Filter

        Returns:
            Dict mit fahrzeuge (inkl. Finanzierungsdaten) und Zins-Statistik
        """
        # 1. GW-Bestand aus Locosoft
        gw_result = FahrzeugData.get_gw_bestand(standort=standort)
        fahrzeuge = gw_result.get('fahrzeuge', [])

        # VINs sammeln
        vins = [f.get('vin') for f in fahrzeuge if f.get('vin')]

        if not vins:
            return {
                'fahrzeuge': fahrzeuge,
                'finanzierung': {
                    'anzahl_finanziert': 0,
                    'summe_saldo': 0,
                    'summe_zinsen_monat': 0,
                    'institute': {}
                },
                'stand': datetime.now().isoformat()
            }

        # 2. Finanzierungsdaten aus DRIVE Portal
        with db_session() as conn:
            cursor = conn.cursor()

            # Finanzierungen fuer diese VINs
            placeholders = ','.join(['%s'] * len(vins))
            cursor.execute(f"""
                SELECT vin, finanzinstitut, aktueller_saldo,
                       zinsen_letzte_periode, zinsen_gesamt,
                       alter_tage, zinsfreiheit_tage
                FROM fahrzeugfinanzierungen
                WHERE vin IN ({placeholders})
            """, vins)

            finanz_map = {}
            for row in cursor.fetchall():
                r = row_to_dict(row)
                finanz_map[r['vin']] = {
                    'finanzinstitut': r['finanzinstitut'],
                    'finanz_saldo': float(r['aktueller_saldo'] or 0),
                    'zinsen_monat': float(r['zinsen_letzte_periode'] or 0),
                    'zinsen_gesamt': float(r['zinsen_gesamt'] or 0),
                    'finanz_alter_tage': int(r['alter_tage'] or 0),
                    'zinsfreiheit_tage': int(r['zinsfreiheit_tage'] or 0) if r['zinsfreiheit_tage'] else None,
                    'ueber_zinsfreiheit': (
                        int(r['alter_tage'] or 0) > int(r['zinsfreiheit_tage'] or 9999)
                        if r['zinsfreiheit_tage'] else False
                    )
                }

        # 3. Fahrzeuge mit Finanzierungsdaten anreichern
        summe_saldo = 0
        summe_zinsen = 0
        institute = {}

        for f in fahrzeuge:
            vin = f.get('vin')
            if vin and vin in finanz_map:
                fd = finanz_map[vin]
                f.update(fd)
                f['ist_finanziert'] = True

                summe_saldo += fd['finanz_saldo']
                summe_zinsen += fd['zinsen_monat']

                inst = fd['finanzinstitut']
                if inst not in institute:
                    institute[inst] = {'anzahl': 0, 'saldo': 0, 'zinsen': 0}
                institute[inst]['anzahl'] += 1
                institute[inst]['saldo'] += fd['finanz_saldo']
                institute[inst]['zinsen'] += fd['zinsen_monat']
            else:
                f['ist_finanziert'] = False
                f['finanzinstitut'] = None
                f['finanz_saldo'] = 0
                f['zinsen_monat'] = 0

        # Runden
        for inst_data in institute.values():
            inst_data['saldo'] = round(inst_data['saldo'], 2)
            inst_data['zinsen'] = round(inst_data['zinsen'], 2)

        logger.info(
            f"FahrzeugData.get_gw_mit_finanzierung: "
            f"{len(fahrzeuge)} GW, {len(finanz_map)} finanziert, "
            f"{round(summe_zinsen, 2)} EUR Zinsen/Monat"
        )

        return {
            'fahrzeuge': fahrzeuge,
            'finanzierung': {
                'anzahl_finanziert': len(finanz_map),
                'summe_saldo': round(summe_saldo, 2),
                'summe_zinsen_monat': round(summe_zinsen, 2),
                'summe_zinsen_jahr': round(summe_zinsen * 12, 2),
                'institute': institute
            },
            'statistik': gw_result.get('statistik', {}),
            'stand': datetime.now().isoformat()
        }

    @staticmethod
    def _berechne_bestand_statistik(fahrzeuge: List[Dict]) -> Dict[str, Any]:
        """Berechnet Statistik aus Fahrzeugliste."""
        if not fahrzeuge:
            return {
                'anzahl': 0,
                'summe_ek': 0,
                'summe_vk': 0,
                'summe_db': 0,
                'avg_standzeit': 0,
                'kategorien': {}
            }

        summe_ek = sum(f.get('ek_preis') or 0 for f in fahrzeuge)
        summe_vk = sum(f.get('vk_preis') or 0 for f in fahrzeuge)
        summe_db = sum(f.get('kalk_db') or 0 for f in fahrzeuge)
        avg_standzeit = sum(f.get('standzeit_tage') or 0 for f in fahrzeuge) / len(fahrzeuge)

        # Nach Kategorie gruppieren
        kategorien = {}
        for f in fahrzeuge:
            kat = f.get('standzeit_kategorie', 'unbekannt')
            if kat not in kategorien:
                kategorien[kat] = {'anzahl': 0, 'summe_vk': 0}
            kategorien[kat]['anzahl'] += 1
            kategorien[kat]['summe_vk'] += f.get('vk_preis') or 0

        return {
            'anzahl': len(fahrzeuge),
            'summe_ek': round(summe_ek, 2),
            'summe_vk': round(summe_vk, 2),
            'summe_db': round(summe_db, 2),
            'avg_standzeit': round(avg_standzeit, 0),
            'kategorien': kategorien
        }


# =============================================================================
# STANDALONE FUNKTIONEN (für direkten Import)
# =============================================================================

def get_gw_bestand(standort=None, kategorie=None, limit=None):
    """Wrapper für FahrzeugData.get_gw_bestand()"""
    return FahrzeugData.get_gw_bestand(standort, kategorie, limit)

def get_nw_pipeline(standort=None, nur_mit_vertrag=False):
    """Wrapper für FahrzeugData.get_nw_pipeline()"""
    return FahrzeugData.get_nw_pipeline(standort, nur_mit_vertrag)

def get_standzeit_statistik(standort=None):
    """Wrapper für FahrzeugData.get_standzeit_statistik()"""
    return FahrzeugData.get_standzeit_statistik(standort)

def get_standzeit_warnungen(min_tage=90, standort=None):
    """Wrapper für FahrzeugData.get_standzeit_warnungen()"""
    return FahrzeugData.get_standzeit_warnungen(min_tage, standort)
