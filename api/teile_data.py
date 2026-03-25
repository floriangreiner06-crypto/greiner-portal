"""
TEILE Data Module - SSOT für Lager & Teile-Daten
=================================================

TAG 154: Erstellt als Teil der DRIVE SSOT-Architektur

ARCHITEKTUR-HINWEIS:
====================
Dieses Modul ist die Single Source of Truth für alle Lager/Teile-Abfragen.

Consumer:
- renner_penner_api.py (Lagerumschlag-Analyse)
- parts_api.py (Teile-Bestellungen)
- teile_api.py (Teile-Preise)
- controlling_data.py (Lager-KPIs)

Datenquellen:
- Locosoft PostgreSQL: parts_stocks, parts, parts_sales
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal

from api.db_utils import get_locosoft_connection
from psycopg2.extras import RealDictCursor

# SSOT: Standort/Betriebsnamen
from api.standort_utils import BETRIEB_NAMEN

logger = logging.getLogger(__name__)


# =============================================================================
# KONSTANTEN
# =============================================================================

PARTS_TYPE_NAMES = {
    0: 'Opel/Stellantis',
    1: 'Opel AT',
    5: 'Hyundai',
    6: 'Hyundai Zubehör',
    10: 'Fremdteil',
    30: 'Öl/Schmierstoff',
    60: 'Opel (AT)',
    65: 'Hyundai (AT)'
}

# BETRIEB_NAMEN wird jetzt aus standort_utils importiert (SSOT)

# Ausgeschlossene Teile-Typen (Garantie, Kautionen etc.)
EXCLUDE_TYPES = {1, 60, 65}  # AT-Teile (Austauschteile)


class TeileData:
    """
    Single Source of Truth für Lager- und Teile-Daten.

    Methoden:
    - get_lagerbestand(): Aktueller Lagerbestand mit Werten
    - get_lagerwert_summary(): Zusammenfassung nach Kategorien
    - get_umschlag_analyse(): Renner/Penner/Leichen Analyse
    - kategorisiere_teil(): Teil-Kategorisierung nach Umschlag
    """

    @staticmethod
    def get_base_query() -> str:
        """
        Basis-Query für Lagerbestand mit allen relevanten Feldern.

        Berechnet:
        - lagerwert (Bestand * Einstandspreis)
        - verkauf_12m (Verkäufe letzte 12 Monate, gewichtet)
        - tage_seit_abgang (Tage seit letztem Verkauf)

        Tabellen:
        - parts_stock (ps) - Lagerbestand pro Betrieb
        - parts_master (pm) - Teilestammdaten

        Returns:
            SQL Query String (ohne ORDER BY)
        """
        return """
            SELECT
                ps.stock_no as betrieb,
                pm.parts_type as teile_typ,
                ps.part_number as teilenummer,
                pm.description as bezeichnung,
                ps.stock_level as bestand,
                ps.usage_value as ek_preis,
                pm.rr_price as vk_preis,
                ROUND((ps.stock_level * ps.usage_value)::numeric, 2) as lagerwert,
                ps.minimum_stock_level as mindestbestand,
                ps.last_outflow_date as letzter_abgang,
                ps.last_inflow_date as letzter_zugang,
                -- Verkauf 12 Monate (aktuell + anteilig Vorjahr)
                COALESCE(ps.sales_current_year, 0) +
                    (COALESCE(ps.sales_previous_year, 0) *
                     (EXTRACT(MONTH FROM CURRENT_DATE)::numeric / 12)) as verkauf_12m,
                -- Tage seit letztem Abgang
                (CURRENT_DATE - ps.last_outflow_date) as tage_seit_abgang
            FROM parts_stock ps
            JOIN parts_master pm ON ps.part_number = pm.part_number
            WHERE ps.stock_level > 0
            -- Garantie/Gewährleistung ausschließen:
            AND pm.parts_type NOT IN (1, 60, 65)  -- AT-Teile
            AND UPPER(pm.description) NOT LIKE '%KAUTION%'
            AND UPPER(pm.description) NOT LIKE '%RUECKLAUFTEIL%'
        """

    @staticmethod
    def kategorisiere_teil(row: Dict) -> Dict[str, Any]:
        """
        Kategorisiert ein Teil basierend auf Umschlag und Reichweite.

        Args:
            row: Dict mit bestand, verkauf_12m, lagerwert, tage_seit_abgang

        Returns:
            Dict mit kategorie, status_icon, prioritaet, empfehlung,
            reichweite_monate, umschlag_jahr, verkauf_monat_avg
        """
        bestand = float(row.get('bestand') or 0)
        verkauf_12m = float(row.get('verkauf_12m') or 0)
        lagerwert = float(row.get('lagerwert') or 0)
        tage_seit_abgang = row.get('tage_seit_abgang')

        # Monatlicher Durchschnittsverkauf
        verkauf_monat = verkauf_12m / 12 if verkauf_12m > 0 else 0

        # Reichweite in Monaten
        reichweite = bestand / verkauf_monat if verkauf_monat > 0 else 999

        # Umschlagshäufigkeit pro Jahr
        umschlag = verkauf_12m / bestand if bestand > 0 else 0

        result = {
            'reichweite_monate': round(reichweite, 1) if reichweite < 999 else None,
            'umschlag_jahr': round(umschlag, 2),
            'verkauf_monat_avg': round(verkauf_monat, 2)
        }

        # LEICHE: Kein Verkauf seit 24+ Monaten
        if tage_seit_abgang and tage_seit_abgang > 730:
            result['kategorie'] = 'leiche'
            result['status_icon'] = '💀'
            result['prioritaet'] = 1
            result['empfehlung'] = 'Rückgabe an Lieferant oder Abschreibung prüfen'
            return result

        # PENNER: Kein/kaum Verkauf oder sehr lange Reichweite
        if tage_seit_abgang and tage_seit_abgang > 365:
            result['kategorie'] = 'penner'
            result['status_icon'] = '🔴'
            result['prioritaet'] = 2
            result['empfehlung'] = 'Preisreduzierung oder Rückgabe prüfen'
            return result

        # Bei Verkäufen: Nach Reichweite kategorisieren
        # PENNER (Reichweite > 24) nur wenn nicht kürzlich verkauft (≤90 Tage = aktiver Abverkauf)
        if verkauf_12m > 0:
            if reichweite > 24:
                tage_ok = tage_seit_abgang is None or (isinstance(tage_seit_abgang, (int, float)) and tage_seit_abgang > 90)
                if tage_ok:
                    result['kategorie'] = 'penner'
                    result['status_icon'] = '🟠'
                    result['prioritaet'] = 3
                    result['empfehlung'] = 'Überbestand reduzieren'
                else:
                    result['kategorie'] = 'normal'
                    result['status_icon'] = '🟡'
                    result['prioritaet'] = 4
                    result['empfehlung'] = 'Bestand hoch, Abverkauf aktiv - beobachten'
                    return result
            elif reichweite > 12:
                result['kategorie'] = 'normal'
                result['status_icon'] = '🟡'
                result['prioritaet'] = 4
                result['empfehlung'] = 'Bestand beobachten'
            elif reichweite > 3:
                result['kategorie'] = 'normal'
                result['status_icon'] = '🟢'
                result['prioritaet'] = 5
                result['empfehlung'] = 'Guter Umschlag'
            else:
                result['kategorie'] = 'renner'
                result['status_icon'] = '⭐'
                result['prioritaet'] = 6
                result['empfehlung'] = 'Top-Performer! Verfügbarkeit sicherstellen'
        else:
            # Kein Verkauf aber noch kein Jahr alt
            if tage_seit_abgang:
                result['kategorie'] = 'normal'
                result['status_icon'] = '🟡'
                result['prioritaet'] = 4
                result['empfehlung'] = 'Neuware - beobachten'
            else:
                result['kategorie'] = 'normal'
                result['status_icon'] = '⚪'
                result['prioritaet'] = 5
                result['empfehlung'] = 'Keine Verkaufsdaten'

        return result

    @classmethod
    def get_lagerwert_summary(cls, betrieb: Optional[int] = None) -> Dict[str, Any]:
        """
        Zusammenfassung des Lagerwerts nach Kategorien.

        Args:
            betrieb: Optional Filter (1=DEG, 2=HYU, 3=LAN)

        Returns:
            {
                'total_lagerwert': 527929.0,
                'total_positionen': 4521,
                'kategorien': {
                    'renner': {'anzahl': 234, 'lagerwert': 45000.0},
                    'normal': {'anzahl': 2100, 'lagerwert': 242000.0},
                    'penner': {'anzahl': 890, 'lagerwert': 71000.0},
                    'leiche': {'anzahl': 1297, 'lagerwert': 169000.0}
                },
                'betriebe': {...}
            }
        """
        try:
            conn = get_locosoft_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = cls.get_base_query()

            if betrieb:
                query += f" AND ps.stock_no = {betrieb}"

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            # Kategorisieren
            kategorien = {
                'renner': {'anzahl': 0, 'lagerwert': 0.0},
                'normal': {'anzahl': 0, 'lagerwert': 0.0},
                'penner': {'anzahl': 0, 'lagerwert': 0.0},
                'leiche': {'anzahl': 0, 'lagerwert': 0.0}
            }

            betriebe = {}
            total_lagerwert = 0.0

            for row in rows:
                kat_info = cls.kategorisiere_teil(row)
                kat = kat_info['kategorie']
                lagerwert = float(row.get('lagerwert') or 0)
                betr = row.get('betrieb', 0)

                kategorien[kat]['anzahl'] += 1
                kategorien[kat]['lagerwert'] += lagerwert
                total_lagerwert += lagerwert

                # Pro Betrieb
                if betr not in betriebe:
                    betriebe[betr] = {
                        'name': BETRIEB_NAMEN.get(betr, f'Betrieb {betr}'),
                        'lagerwert': 0.0,
                        'positionen': 0
                    }
                betriebe[betr]['lagerwert'] += lagerwert
                betriebe[betr]['positionen'] += 1

            # Runden
            for kat in kategorien.values():
                kat['lagerwert'] = round(kat['lagerwert'], 2)
            for betr in betriebe.values():
                betr['lagerwert'] = round(betr['lagerwert'], 2)

            return {
                'success': True,
                'total_lagerwert': round(total_lagerwert, 2),
                'total_positionen': len(rows),
                'kategorien': kategorien,
                'betriebe': betriebe,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Fehler bei Lagerwert-Summary: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @classmethod
    def get_top_penner(cls, limit: int = 50, min_wert: float = 100,
                       betrieb: Optional[int] = None) -> Dict[str, Any]:
        """
        Top Penner (Langsamdreher) nach Lagerwert.

        Args:
            limit: Max. Anzahl Ergebnisse
            min_wert: Mindest-Lagerwert
            betrieb: Optional Filter

        Returns:
            {'success': True, 'penner': [...], 'total_lagerwert': ...}
        """
        try:
            conn = get_locosoft_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = cls.get_base_query()
            query += f" AND (ps.stock_level * ps.usage_value) >= {min_wert}"

            if betrieb:
                query += f" AND ps.stock_no = {betrieb}"

            # Nur Teile ohne Verkauf > 365 Tage
            query += """
                AND (
                    ps.last_outflow_date IS NULL
                    OR ps.last_outflow_date < CURRENT_DATE - INTERVAL '365 days'
                )
            """

            query += f" ORDER BY lagerwert DESC LIMIT {limit}"

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            penner = []
            total_lagerwert = 0.0

            for row in rows:
                kat_info = cls.kategorisiere_teil(row)
                lagerwert = float(row.get('lagerwert') or 0)
                total_lagerwert += lagerwert

                penner.append({
                    'teilenummer': row['teilenummer'],
                    'bezeichnung': row['bezeichnung'],
                    'teile_typ': PARTS_TYPE_NAMES.get(row.get('teile_typ'), '?'),
                    'betrieb': BETRIEB_NAMEN.get(row['betrieb'], '?'),
                    'bestand': int(row['bestand']),
                    'lagerwert': lagerwert,
                    'tage_seit_abgang': row['tage_seit_abgang'],
                    **kat_info
                })

            return {
                'success': True,
                'penner': penner,
                'total_lagerwert': round(total_lagerwert, 2),
                'anzahl': len(penner),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Fehler bei Top-Penner: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @classmethod
    def get_top_renner(cls, limit: int = 50, betrieb: Optional[int] = None) -> Dict[str, Any]:
        """
        Top Renner (Schnelldreher) nach Umschlagshäufigkeit.

        Args:
            limit: Max. Anzahl Ergebnisse
            betrieb: Optional Filter

        Returns:
            {'success': True, 'renner': [...], 'total_lagerwert': ...}
        """
        try:
            conn = get_locosoft_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = cls.get_base_query()
            query += " AND (ps.stock_level * ps.usage_value) >= 20"  # Mindest-Wert

            if betrieb:
                query += f" AND ps.stock_no = {betrieb}"

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            # Filter auf echte Renner (Reichweite < 3 Monate)
            renner = []
            total_lagerwert = 0.0

            for row in rows:
                kat_info = cls.kategorisiere_teil(row)

                if kat_info['kategorie'] == 'renner':
                    lagerwert = float(row.get('lagerwert') or 0)
                    total_lagerwert += lagerwert

                    renner.append({
                        'teilenummer': row['teilenummer'],
                        'bezeichnung': row['bezeichnung'],
                        'teile_typ': PARTS_TYPE_NAMES.get(row.get('teile_typ'), '?'),
                        'betrieb': BETRIEB_NAMEN.get(row['betrieb'], '?'),
                        'bestand': int(row['bestand']),
                        'lagerwert': lagerwert,
                        'verkauf_12m': int(row['verkauf_12m']),
                        **kat_info
                    })

            # Nach Umschlag sortieren
            renner.sort(key=lambda x: x.get('umschlag_jahr', 0), reverse=True)
            renner = renner[:limit]

            return {
                'success': True,
                'renner': renner,
                'total_lagerwert': round(total_lagerwert, 2),
                'anzahl': len(renner),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Fehler bei Top-Renner: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_lagerwert_summary(betrieb: Optional[int] = None) -> Dict[str, Any]:
    """Wrapper für TeileData.get_lagerwert_summary()."""
    return TeileData.get_lagerwert_summary(betrieb)


def get_top_penner(limit: int = 50, min_wert: float = 100,
                   betrieb: Optional[int] = None) -> Dict[str, Any]:
    """Wrapper für TeileData.get_top_penner()."""
    return TeileData.get_top_penner(limit, min_wert, betrieb)


def get_top_renner(limit: int = 50, betrieb: Optional[int] = None) -> Dict[str, Any]:
    """Wrapper für TeileData.get_top_renner()."""
    return TeileData.get_top_renner(limit, betrieb)
