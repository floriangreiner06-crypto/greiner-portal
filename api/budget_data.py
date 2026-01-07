"""
BUDGET Data Module - SSOT für Budget-Planung
=============================================

TAG 155: Erstellt als Teil der DRIVE Budget-Planung

ARCHITEKTUR-HINWEIS:
====================
Dieses Modul ist die Single Source of Truth für alle Budget-Planungs-Abfragen.

Consumer:
- budget_api.py (REST-Endpoints)
- controlling_data.py (Vergleich Plan vs. IST)

Datenquellen:
- PostgreSQL DRIVE Portal: budget_plan, budget_history
- IST-Daten: Locosoft PostgreSQL via verkauf_data.py
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal

from api.db_connection import get_db
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


# =============================================================================
# KONSTANTEN
# =============================================================================

KOSTENSTELLEN = {
    0: {'name': 'Verwaltung', 'kuerzel': 'VW', 'aktiv': False},
    1: {'name': 'Neuwagen', 'kuerzel': 'NW', 'aktiv': True},
    2: {'name': 'Gebrauchtwagen', 'kuerzel': 'GW', 'aktiv': True},
    3: {'name': 'Mechanik', 'kuerzel': 'ME', 'aktiv': False},
    4: {'name': 'Karosserie', 'kuerzel': 'KA', 'aktiv': False},
    5: {'name': 'Teile/Zubehör', 'kuerzel': 'TZ', 'aktiv': False},
    6: {'name': 'Carpool', 'kuerzel': 'CP', 'aktiv': False},
    7: {'name': 'Mietwagen', 'kuerzel': 'MW', 'aktiv': False},
    8: {'name': 'Sonstiges', 'kuerzel': 'SO', 'aktiv': False}
}

STANDORTE = {
    1: {'name': 'Deggendorf Opel', 'kuerzel': 'DEG'},
    2: {'name': 'Deggendorf Hyundai', 'kuerzel': 'HYU'},
    3: {'name': 'Landau', 'kuerzel': 'LAN'}
}

# Branchen-Benchmarks (Quellen: DEKRA, ZDK, DAT Report)
BENCHMARKS = {
    'NW': {
        'bruttoertrag_pro_fzg': {'min': 1500, 'max': 2500, 'einheit': '€'},
        'bruttoertrag_marge': {'min': 7, 'max': 10, 'einheit': '%'},
        'variable_kosten_quote': {'min': 25, 'max': 35, 'einheit': '%'},
        'db1_pro_fzg': {'min': 1000, 'max': 2000, 'einheit': '€'},
    },
    'GW': {
        'bruttoertrag_pro_fzg': {'min': 2000, 'max': 3500, 'einheit': '€'},
        'bruttoertrag_marge': {'min': 12, 'max': 15, 'einheit': '%'},
        'variable_kosten_quote': {'min': 20, 'max': 28, 'einheit': '%'},
        'db1_pro_fzg': {'min': 1500, 'max': 2800, 'einheit': '€'},
    }
}

# Greiner 2024 IST-Werte (aus Planung_2025.xlsx extrahiert)
GREINER_IST_2024 = {
    'NW': {
        'gesamt': {
            'stueck': 535,
            'umsatz': 14582964,
            'einsatzwerte': 12889851,
            'bruttoertrag': 1693113,
            'variable_kosten': 577592,
            'direkte_kosten': 288996,
            'betriebsergebnis': 826525
        },
        'standorte': {
            1: {'stueck': 255, 'umsatz': 6522397, 'bruttoertrag': 950130, 'betriebsergebnis': 410705},
            2: {'stueck': 234, 'umsatz': 6921270, 'bruttoertrag': 695724, 'betriebsergebnis': 472041},
            3: {'stueck': 46, 'umsatz': 1139297, 'bruttoertrag': 47259, 'betriebsergebnis': -56221}
        },
        'variable_kosten_detail': {
            'fixum_prov_soz': 291090,
            'provisionen': 66700,
            'fertigmachen': 59260,
            'kulanz': 66943,
            'training': 9023,
            'fahrzeugkosten': 31203,
            'werbung': 53374
        }
    },
    'GW': {
        'gesamt': {
            'stueck': 615,
            'umsatz': 9881621,
            'einsatzwerte': 8777536,
            'bruttoertrag': 1104085,
            'variable_kosten': 282453,
            'direkte_kosten': 273269,
            'betriebsergebnis': 548363
        },
        'standorte': {
            1: {'stueck': 295, 'umsatz': 4658178, 'bruttoertrag': 595550, 'betriebsergebnis': 244596},
            2: {'stueck': 163, 'umsatz': 2885582, 'bruttoertrag': 357285, 'betriebsergebnis': 270273},
            3: {'stueck': 157, 'umsatz': 2337861, 'bruttoertrag': 151249, 'betriebsergebnis': 33494}
        },
        'variable_kosten_detail': {
            'fixum_prov_soz': 174636,
            'provisionen': 38012,
            'fertigmachen': 270,
            'kulanz': 38022,
            'training': 225,
            'fahrzeugkosten': 14601,
            'werbung': 16688
        }
    }
}

# Saisonalisierung (Prozent pro Monat, summiert 100%)
SAISONALISIERUNG = {
    'NW': [6.5, 7.0, 10.5, 9.5, 9.0, 8.5, 7.5, 7.0, 9.0, 9.5, 9.0, 7.0],
    'GW': [7.0, 7.5, 9.5, 9.0, 9.0, 8.5, 8.0, 7.5, 8.5, 9.0, 8.5, 8.0]
}


class BudgetData:
    """
    Single Source of Truth für Budget-Planung.

    Methoden:
    - get_ist_vorjahr(): IST-Werte des Vorjahres
    - get_plan(): Aktueller Budgetplan
    - save_plan(): Budgetplan speichern
    - calculate_monthly(): Plan auf Monate verteilen
    - get_plan_vs_ist(): Plan vs. IST Vergleich
    - get_benchmarks(): Branchen-Benchmarks
    """

    @staticmethod
    def get_kostenstellen_info() -> Dict[int, Dict]:
        """Gibt alle Kostenstellen mit Status zurück."""
        return KOSTENSTELLEN

    @staticmethod
    def get_standorte_info() -> Dict[int, Dict]:
        """Gibt alle Standorte zurück."""
        return STANDORTE

    @staticmethod
    def get_benchmarks(kostenstelle: str) -> Dict[str, Any]:
        """
        Branchen-Benchmarks für eine Kostenstelle.

        Args:
            kostenstelle: 'NW' oder 'GW'

        Returns:
            Dict mit Benchmark-Werten und Einheiten
        """
        return BENCHMARKS.get(kostenstelle, {})

    @staticmethod
    def get_ist_vorjahr(kostenstelle: str, jahr: int = 2024,
                        standort: Optional[int] = None) -> Dict[str, Any]:
        """
        IST-Werte des Vorjahres für Budget-Planung.

        Args:
            kostenstelle: 'NW' oder 'GW'
            jahr: Vorjahr (default 2024)
            standort: Optional Standort-Filter (1, 2, 3)

        Returns:
            Dict mit IST-Werten, KPIs und Empfehlungen
        """
        if kostenstelle not in GREINER_IST_2024:
            return {'success': False, 'error': f'Kostenstelle {kostenstelle} nicht gefunden'}

        ist = GREINER_IST_2024[kostenstelle]
        benchmarks = BENCHMARKS.get(kostenstelle, {})

        if standort and standort in ist['standorte']:
            data = ist['standorte'][standort]
            standort_name = STANDORTE[standort]['name']
        else:
            data = ist['gesamt']
            standort_name = 'AH Greiner Gesamt'
            standort = None

        # KPIs berechnen
        stueck = data['stueck']
        umsatz = data.get('umsatz', 0)
        bruttoertrag = data.get('bruttoertrag', 0)
        betriebsergebnis = data.get('betriebsergebnis', 0)

        kpis = {
            'umsatz_pro_fzg': round(umsatz / stueck, 0) if stueck else 0,
            'bruttoertrag_pro_fzg': round(bruttoertrag / stueck, 0) if stueck else 0,
            'bruttoertrag_marge': round((bruttoertrag / umsatz) * 100, 1) if umsatz else 0,
            'betriebsergebnis_pro_fzg': round(betriebsergebnis / stueck, 0) if stueck else 0
        }

        # Variable Kosten (nur bei Gesamt)
        if not standort and 'variable_kosten' in data:
            kpis['variable_kosten_quote'] = round(
                (data['variable_kosten'] / bruttoertrag) * 100, 1
            ) if bruttoertrag else 0
            kpis['db1'] = bruttoertrag - data['variable_kosten']
            kpis['db1_pro_fzg'] = round(kpis['db1'] / stueck, 0) if stueck else 0

        # Benchmark-Vergleich
        bewertung = {}
        for kpi_name, benchmark in benchmarks.items():
            if kpi_name in kpis:
                wert = kpis[kpi_name]
                if wert >= benchmark['max']:
                    bewertung[kpi_name] = {'status': 'excellent', 'icon': '⭐'}
                elif wert >= benchmark['min']:
                    bewertung[kpi_name] = {'status': 'ok', 'icon': '✅'}
                else:
                    bewertung[kpi_name] = {'status': 'kritisch', 'icon': '⚠️'}

        return {
            'success': True,
            'kostenstelle': kostenstelle,
            'standort': standort,
            'standort_name': standort_name,
            'jahr': jahr,
            'daten': data,
            'kpis': kpis,
            'bewertung': bewertung,
            'benchmarks': benchmarks
        }

    @staticmethod
    def get_empfehlungen(kostenstelle: str, standort: Optional[int] = None) -> List[Dict]:
        """
        Generiert Budget-Empfehlungen basierend auf IST 2024.

        Returns:
            Liste von Empfehlungen mit Priorität
        """
        ist = BudgetData.get_ist_vorjahr(kostenstelle, 2024, standort)
        if not ist.get('success'):
            return []

        empfehlungen = []
        kpis = ist.get('kpis', {})
        bewertung = ist.get('bewertung', {})
        benchmarks = ist.get('benchmarks', {})

        # Stückzahl-Empfehlung
        stueck = ist['daten']['stueck']
        empfehlungen.append({
            'kategorie': 'stueckzahl',
            'titel': 'Stückzahl-Ziel',
            'text': f'Basierend auf {stueck} Fahrzeugen in 2024',
            'empfehlung': {
                'konservativ': int(stueck * 1.00),  # 0% Wachstum
                'moderat': int(stueck * 1.03),      # 3% Wachstum
                'ambitioniert': int(stueck * 1.05)  # 5% Wachstum
            },
            'prioritaet': 1
        })

        # Bruttoertrag-Empfehlung
        be_pro_fzg = kpis.get('bruttoertrag_pro_fzg', 0)
        benchmark = benchmarks.get('bruttoertrag_pro_fzg', {})
        if be_pro_fzg < benchmark.get('min', 0):
            empfehlungen.append({
                'kategorie': 'bruttoertrag',
                'titel': 'Bruttoertrag verbessern',
                'text': f'Aktuell €{be_pro_fzg:,.0f}/Fzg - unter Branchenschnitt',
                'empfehlung': {
                    'konservativ': benchmark.get('min', be_pro_fzg),
                    'moderat': int((benchmark.get('min', 0) + benchmark.get('max', 0)) / 2),
                    'ambitioniert': benchmark.get('max', be_pro_fzg)
                },
                'prioritaet': 2
            })
        else:
            empfehlungen.append({
                'kategorie': 'bruttoertrag',
                'titel': 'Bruttoertrag halten',
                'text': f'Aktuell €{be_pro_fzg:,.0f}/Fzg - über Branchenschnitt! 🌟',
                'empfehlung': {
                    'konservativ': int(be_pro_fzg * 0.95),
                    'moderat': int(be_pro_fzg * 1.00),
                    'ambitioniert': int(be_pro_fzg * 1.05)
                },
                'prioritaet': 3
            })

        # Variable Kosten-Empfehlung (nur bei Gesamt)
        vk_quote = kpis.get('variable_kosten_quote', 0)
        if vk_quote > 0:
            vk_benchmark = benchmarks.get('variable_kosten_quote', {})
            if vk_quote > vk_benchmark.get('max', 100):
                empfehlungen.append({
                    'kategorie': 'variable_kosten',
                    'titel': 'Variable Kosten senken',
                    'text': f'Aktuell {vk_quote}% - über Ziel ({vk_benchmark.get("max", 30)}%)',
                    'empfehlung': {
                        'konservativ': vk_quote - 2,
                        'moderat': vk_quote - 4,
                        'ambitioniert': vk_benchmark.get('max', 30)
                    },
                    'einheit': '%',
                    'prioritaet': 2
                })

        # Standort-spezifische Empfehlung
        if standort == 3:  # Landau
            empfehlungen.append({
                'kategorie': 'standort',
                'titel': '⚠️ Standort Landau kritisch',
                'text': 'Negatives Betriebsergebnis NW in 2024',
                'empfehlung': {
                    'massnahme': 'Volumen erhöhen oder Kostenstruktur anpassen'
                },
                'prioritaet': 1
            })

        return sorted(empfehlungen, key=lambda x: x['prioritaet'])

    @staticmethod
    def calculate_monthly(jahresplan: Dict, kostenstelle: str) -> List[Dict]:
        """
        Verteilt Jahresplan auf Monate basierend auf Saisonalisierung.

        Args:
            jahresplan: Dict mit 'stueck', 'bruttoertrag', etc.
            kostenstelle: 'NW' oder 'GW'

        Returns:
            Liste mit 12 Monats-Dicts
        """
        saisonalisierung = SAISONALISIERUNG.get(kostenstelle, [8.33] * 12)
        monate = []

        monatsnamen = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

        for i, prozent in enumerate(saisonalisierung):
            faktor = prozent / 100
            monat = {
                'monat': i + 1,
                'name': monatsnamen[i],
                'prozent': prozent
            }

            for key, wert in jahresplan.items():
                if isinstance(wert, (int, float)):
                    monat[key] = round(wert * faktor, 2)

            monate.append(monat)

        return monate

    @classmethod
    def save_plan(cls, kostenstelle: str, standort: int, jahr: int,
                  plan_daten: Dict, erstellt_von: str) -> Dict[str, Any]:
        """
        Speichert einen Budgetplan in der Datenbank.

        Args:
            kostenstelle: 'NW' oder 'GW'
            standort: 1, 2, oder 3
            jahr: Planjahr
            plan_daten: Dict mit Plan-Werten
            erstellt_von: Username

        Returns:
            {'success': True, 'plan_id': ...} oder {'success': False, 'error': ...}
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Prüfen ob Plan existiert
            cursor.execute("""
                SELECT id FROM budget_plan
                WHERE kostenstelle = %s AND standort = %s AND jahr = %s
            """, (kostenstelle, standort, jahr))

            existing = cursor.fetchone()

            if existing:
                # Update
                cursor.execute("""
                    UPDATE budget_plan SET
                        stueck_plan = %s,
                        umsatz_plan = %s,
                        bruttoertrag_plan = %s,
                        variable_kosten_plan = %s,
                        betriebsergebnis_plan = %s,
                        notizen = %s,
                        aktualisiert_von = %s,
                        aktualisiert_am = NOW()
                    WHERE id = %s
                """, (
                    plan_daten.get('stueck', 0),
                    plan_daten.get('umsatz', 0),
                    plan_daten.get('bruttoertrag', 0),
                    plan_daten.get('variable_kosten', 0),
                    plan_daten.get('betriebsergebnis', 0),
                    plan_daten.get('notizen', ''),
                    erstellt_von,
                    existing[0]
                ))
                plan_id = existing[0]
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO budget_plan (
                        kostenstelle, standort, jahr,
                        stueck_plan, umsatz_plan, bruttoertrag_plan,
                        variable_kosten_plan, betriebsergebnis_plan,
                        notizen, erstellt_von, erstellt_am
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    RETURNING id
                """, (
                    kostenstelle, standort, jahr,
                    plan_daten.get('stueck', 0),
                    plan_daten.get('umsatz', 0),
                    plan_daten.get('bruttoertrag', 0),
                    plan_daten.get('variable_kosten', 0),
                    plan_daten.get('betriebsergebnis', 0),
                    plan_daten.get('notizen', ''),
                    erstellt_von
                ))
                plan_id = cursor.fetchone()[0]

            conn.commit()
            conn.close()

            return {
                'success': True,
                'plan_id': plan_id,
                'message': 'Budget-Plan gespeichert'
            }

        except Exception as e:
            logger.error(f"Fehler beim Speichern des Budget-Plans: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @classmethod
    def get_plan(cls, kostenstelle: str, standort: Optional[int] = None,
                 jahr: int = 2026) -> Dict[str, Any]:
        """
        Lädt den aktuellen Budgetplan.

        Args:
            kostenstelle: 'NW' oder 'GW'
            standort: Optional Standort-Filter
            jahr: Planjahr

        Returns:
            Dict mit Plan-Daten oder leerer Plan
        """
        try:
            conn = get_db()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            if standort:
                cursor.execute("""
                    SELECT * FROM budget_plan
                    WHERE kostenstelle = %s AND standort = %s AND jahr = %s
                """, (kostenstelle, standort, jahr))
            else:
                cursor.execute("""
                    SELECT * FROM budget_plan
                    WHERE kostenstelle = %s AND jahr = %s
                """, (kostenstelle, jahr))

            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return {
                    'success': True,
                    'plan': None,
                    'message': 'Kein Plan vorhanden'
                }

            return {
                'success': True,
                'plan': [dict(row) for row in rows],
                'anzahl': len(rows)
            }

        except Exception as e:
            logger.error(f"Fehler beim Laden des Budget-Plans: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_ist_vorjahr(kostenstelle: str, jahr: int = 2024,
                    standort: Optional[int] = None) -> Dict[str, Any]:
    """Wrapper für BudgetData.get_ist_vorjahr()."""
    return BudgetData.get_ist_vorjahr(kostenstelle, jahr, standort)


def get_empfehlungen(kostenstelle: str, standort: Optional[int] = None) -> List[Dict]:
    """Wrapper für BudgetData.get_empfehlungen()."""
    return BudgetData.get_empfehlungen(kostenstelle, standort)


def get_benchmarks(kostenstelle: str) -> Dict[str, Any]:
    """Wrapper für BudgetData.get_benchmarks()."""
    return BudgetData.get_benchmarks(kostenstelle)


def calculate_monthly(jahresplan: Dict, kostenstelle: str) -> List[Dict]:
    """Wrapper für BudgetData.calculate_monthly()."""
    return BudgetData.calculate_monthly(jahresplan, kostenstelle)
