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
- [x] get_mechaniker_leistung() - TAG 148
- [x] get_offene_auftraege() - TAG 149
- [x] get_dashboard_stats() - TAG 149
- [x] get_stempeluhr() - TAG 149
- [x] get_kapazitaetsplanung() - TAG 149
- [x] get_tagesbericht() - TAG 150
- [x] get_auftrag_detail() - TAG 150
- [x] get_problemfaelle() - TAG 150
- [ ] get_anwesenheit() - TODO
"""

from datetime import datetime, timedelta, date, time
from typing import Optional, Dict, List, Any, Tuple
import logging

# Zentrale DB-Utilities
from api.db_utils import locosoft_session, get_locosoft_connection, row_to_dict, rows_to_list
from psycopg2.extras import RealDictCursor

# SSOT: Standort/Betriebsnamen
from api.standort_utils import BETRIEB_NAMEN

# SSOT: KPI-Berechnungen
from utils.kpi_definitions import berechne_anwesenheitsgrad

logger = logging.getLogger(__name__)

# =============================================================================
# KONSTANTEN
# =============================================================================

# Mechaniker-Range (Locosoft-Standard)
MECHANIKER_RANGE_START = 5000
MECHANIKER_RANGE_END = 5999

# Azubis ausschließen
MECHANIKER_EXCLUDE = [5025, 5026, 5028]

# Leerlaufaufträge pro Betrieb (TAG 194 - Aktualisiert)
# Diese Aufträge werden aus der Stempelzeit-Berechnung ausgeschlossen
# SSOT: Single Source of Truth für Leerlaufaufträge - Warnung bei Leerlauf-Stempelungen durch Mechaniker
LEERLAUF_AUFTRAEGE_PRO_BETRIEB = {
    1: [39406],   # DEGO (Deggendorf Opel): Order 39406 (historisch: 31)
    2: [220710],  # DEGH (Deggendorf Hyundai): Order 220710 (historisch: keine)
    3: [313666]   # LANO (Landau): Order 313666 (historisch: 300014)
}

# Standard Arbeitszeiten
ARBEITSZEIT_START = time(7, 0)   # 07:00 Uhr
ARBEITSZEIT_ENDE = time(17, 0)   # 17:00 Uhr
STUNDEN_PRO_TAG = 10.0           # Effektive Arbeitsstunden


# =============================================================================
# HILFSFUNKTIONEN (VOR KLASSE)
# =============================================================================

def build_leerlauf_filter(betrieb: Optional[int] = None) -> str:
    """
    Baut SQL-Filter für Leerlaufaufträge (SSOT - Single Source of Truth).
    
    ⚠️ SSOT: Dies ist die EINZIGE Funktion für Leerlaufauftrags-Filter!
    Nutze diese Funktion IMMER, niemals hardcoded order_number = 31/300014/39406/220710/313666!
    
    Args:
        betrieb: Betrieb-ID (1=DEGO, 2=DEGH, 3=LANO, None=alle)
    
    Returns:
        str: SQL WHERE-Clause (z.B. "AND t.order_number != ALL(ARRAY[39406,220710,313666])")
    
    Beispiel:
        >>> filter = build_leerlauf_filter(betrieb=1)
        >>> # "AND t.order_number != ALL(ARRAY[39406])"
    """
    leerlauf_auftraege = []
    if betrieb and betrieb in LEERLAUF_AUFTRAEGE_PRO_BETRIEB:
        leerlauf_auftraege = LEERLAUF_AUFTRAEGE_PRO_BETRIEB[betrieb]
    else:
        # Alle Betriebe: Alle Leerlaufaufträge sammeln
        for b_leerlauf in LEERLAUF_AUFTRAEGE_PRO_BETRIEB.values():
            leerlauf_auftraege.extend(b_leerlauf)
        leerlauf_auftraege = list(set(leerlauf_auftraege))  # Duplikate entfernen
    
    if leerlauf_auftraege:
        return f"AND t.order_number != ALL(ARRAY[{','.join(map(str, leerlauf_auftraege))}])"
    else:
        # Fallback: Mindestens > 31 (historisch)
        return "AND t.order_number > 31"

def build_leerlauf_filter_equals(betrieb: Optional[int] = None) -> str:
    """
    Baut SQL-Filter für Leerlaufaufträge mit = (für FILTER WHERE).
    
    ⚠️ SSOT: Für FILTER (WHERE ...) Klauseln verwenden!
    
    Args:
        betrieb: Betrieb-ID (1=DEGO, 2=DEGH, 3=LANO, None=alle)
    
    Returns:
        str: SQL FILTER-Clause (z.B. "FILTER (WHERE t.order_number = ANY(ARRAY[39406,220710,313666]))")
    """
    leerlauf_auftraege = []
    if betrieb and betrieb in LEERLAUF_AUFTRAEGE_PRO_BETRIEB:
        leerlauf_auftraege = LEERLAUF_AUFTRAEGE_PRO_BETRIEB[betrieb]
    else:
        # Alle Betriebe: Alle Leerlaufaufträge sammeln
        for b_leerlauf in LEERLAUF_AUFTRAEGE_PRO_BETRIEB.values():
            leerlauf_auftraege.extend(b_leerlauf)
        leerlauf_auftraege = list(set(leerlauf_auftraege))  # Duplikate entfernen
    
    if leerlauf_auftraege:
        return f"FILTER (WHERE t.order_number = ANY(ARRAY[{','.join(map(str, leerlauf_auftraege))}]))"
    else:
        # Fallback: Historisch Order 31
        return "FILTER (WHERE t.order_number = 31)"

def berechne_durchschnittlichen_verrechnungssatz(
    betrieb: Optional[int] = None,
    monate: int = 6
) -> Dict[str, Any]:
    """
    Berechnet den durchschnittlichen Verrechnungssatz (€/Std) aus Locosoft.
    
    Filter:
    - Extern: labour_type != 'I' (nicht intern)
    - Ohne Karosserie: charge_type NOT BETWEEN 20 AND 29
    - Rollierend: letzte N Monate
    - Nur verrechnete Positionen: is_invoiced = true
    
    Args:
        betrieb: Betriebsnummer (1=DEG, 2=HYU, 3=LAN), None = alle
        monate: Anzahl Monate für rollierende Berechnung (default: 6)
    
    Returns:
        {
            'svs': float,              # Durchschnittlicher Verrechnungssatz (€/Std)
            'umsatz_gesamt': float,    # Gesamtumsatz im Zeitraum
            'stunden_gesamt': float,   # Gesamtstunden im Zeitraum
            'anzahl_positionen': int,  # Anzahl verrechneter Positionen
            'zeitraum': {
                'von': str,            # ISO-Format
                'bis': str             # ISO-Format
            },
            'betrieb': int,            # Betriebsnummer (oder None)
            'quelle': 'locosoft_6m_rollierend'
        }
    """
    try:
        bis_datum = date.today()
        von_datum = bis_datum - timedelta(days=monate * 30)  # Ca. N Monate
        
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Filter aufbauen
            betrieb_filter = ""
            params = [von_datum, bis_datum]
            
            if betrieb:
                betrieb_filter = "AND i.subsidiary = %s"
                params.append(betrieb)
            
            # SQL: SUM(net_price_in_order) / SUM(time_units * 6 / 60)
            # time_units = AW, 1 AW = 6 Minuten, daher: time_units * 6 / 60 = Stunden
            query = f"""
                SELECT
                    COUNT(*) as anzahl_positionen,
                    COALESCE(SUM(l.net_price_in_order), 0) as umsatz_gesamt,
                    COALESCE(SUM(l.time_units * 6.0 / 60.0), 0) as stunden_gesamt
                FROM labours l
                JOIN invoices i ON l.invoice_number = i.invoice_number 
                    AND l.invoice_type = i.invoice_type
                WHERE i.invoice_date >= %s 
                  AND i.invoice_date <= %s
                  AND l.is_invoiced = true
                  AND l.labour_type != 'I'  -- Extern (nicht intern)
                  AND (l.charge_type IS NULL OR l.charge_type NOT BETWEEN 20 AND 29)  -- Ohne Karosserie
                  AND l.time_units > 0  -- Nur Positionen mit Stunden
                  {betrieb_filter}
            """
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            if not row:
                return {
                    'svs': 119.0,  # Fallback
                    'umsatz_gesamt': 0.0,
                    'stunden_gesamt': 0.0,
                    'anzahl_positionen': 0,
                    'zeitraum': {
                        'von': von_datum.isoformat(),
                        'bis': bis_datum.isoformat()
                    },
                    'betrieb': betrieb,
                    'quelle': 'locosoft_6m_rollierend',
                    'fehler': 'Keine Daten gefunden'
                }
            
            umsatz_gesamt = float(row['umsatz_gesamt'] or 0)
            stunden_gesamt = float(row['stunden_gesamt'] or 0)
            anzahl_positionen = int(row['anzahl_positionen'] or 0)
            
            # SVS = Umsatz / Stunden
            svs = round(umsatz_gesamt / stunden_gesamt, 2) if stunden_gesamt > 0 else 119.0
            
            return {
                'svs': svs,
                'umsatz_gesamt': round(umsatz_gesamt, 2),
                'stunden_gesamt': round(stunden_gesamt, 2),
                'anzahl_positionen': anzahl_positionen,
                'zeitraum': {
                    'von': von_datum.isoformat(),
                    'bis': bis_datum.isoformat()
                },
                'betrieb': betrieb,
                'quelle': 'locosoft_6m_rollierend'
            }
            
    except Exception as e:
        logger.exception(f"Fehler bei Berechnung Verrechnungssatz: {str(e)}")
        return {
            'svs': 119.0,  # Fallback
            'umsatz_gesamt': 0.0,
            'stunden_gesamt': 0.0,
            'anzahl_positionen': 0,
            'zeitraum': {
                'von': (date.today() - timedelta(days=180)).isoformat(),
                'bis': date.today().isoformat()
            },
            'betrieb': betrieb,
            'quelle': 'locosoft_6m_rollierend',
            'fehler': str(e)
        }


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
        - employees_breaktimes: Konfigurierte Pausenzeiten

        Berechnet (TAG 185 - Locosoft-kompatible Berechnung):
        - Stempelzeit nach Locosoft-Logik:
          * Zeit-Spanne (erste bis letzte Stempelung pro Tag)
          * Minus Lücken zwischen Stempelungen
          * Minus konfigurierte Pausenzeiten (wenn innerhalb der Zeit-Spanne)
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
            
        Note (TAG 185):
            Die Stempelzeit-Berechnung wurde an Locosoft Original angepasst:
            - Zeit-Spanne pro Tag (erste bis letzte Stempelung)
            - Minus Lücken zwischen Stempelungen
            - Minus konfigurierte Pausenzeiten
            Dies entspricht der Berechnung in Locosoft "Tages-Stempelzeiten Übersicht".
        """
        # Default Zeitraum: Aktueller Monat
        if von is None:
            von = date.today().replace(day=1)
        if bis is None:
            bis = date.today()

        # Leerlaufaufträge für Filter bestimmen (TAG 181)
        leerlauf_auftraege = []
        if betrieb and betrieb in LEERLAUF_AUFTRAEGE_PRO_BETRIEB:
            leerlauf_auftraege = LEERLAUF_AUFTRAEGE_PRO_BETRIEB[betrieb]
        elif betrieb is None:
            # Alle Betriebe: Alle Leerlaufaufträge sammeln
            for b_leerlauf in LEERLAUF_AUFTRAEGE_PRO_BETRIEB.values():
                leerlauf_auftraege.extend(b_leerlauf)
            leerlauf_auftraege = list(set(leerlauf_auftraege))  # Duplikate entfernen
        
        # Filter für Leerlaufaufträge aufbauen
        leerlauf_filter = ""
        if leerlauf_auftraege:
            leerlauf_filter = f"AND t.order_number != ALL(ARRAY[{','.join(map(str, leerlauf_auftraege))}])"
        else:
            # Fallback: Nur Order 31 ausschließen (wie bisher)
            leerlauf_filter = "AND t.order_number > 31"

        # TAG 194: REFACTORED - Nutze neue separate Funktionen
        # NEUIMPLEMENTIERUNG TAG 196: Einfache, korrekte Funktionen nach Locosoft-Definition
        # 
        # 1. VORGABEZEIT (AW-Anteil) aus labours
        vorgabezeit_data = WerkstattData.get_vorgabezeit_aus_labours(von, bis)
        
        # 2. STEMPELZEIT (St-Anteil) aus times type=2 - OHNE 0.75 Faktor!
        stempelzeit_data = WerkstattData.get_stempelzeit_aus_times(von, bis)
        
        # 3. ANWESENHEIT aus times type=1
        anwesenheit_data = WerkstattData.get_anwesenheit_aus_times(von, bis)
        
        # Legacy-Funktionen (für Kompatibilität, werden nicht mehr verwendet)
        stempelzeit_locosoft = WerkstattData.get_stempelzeit_locosoft(von, bis, leerlauf_filter)
        stempelzeit_leistungsgrad = WerkstattData.get_stempelzeit_leistungsgrad(von, bis, leerlauf_filter)
        stempelungen_roh = WerkstattData.get_stempelungen_roh(von, bis)
        
        # NEUIMPLEMENTIERUNG TAG 196: Einfache, korrekte Zuordnung
        # 
        # REGEL: Stempelzeit ≤ Anwesenheit (IMMER!)
        # 
        # 1. VORGABEZEIT = labours.time_units × 6 / 60 (Stunden)
        # 2. STEMPELZEIT = times type=2 (end - start), OHNE 0.75 Faktor (Stunden)
        # 3. ANWESENHEIT = times type=1 (end - start) (Stunden)
        #
        rohdaten = {}
        all_emps = set(list(vorgabezeit_data.keys()) + 
                       list(stempelzeit_data.keys()) + 
                       list(anwesenheit_data.keys()) +
                       list(stempelzeit_locosoft.keys()))
        
        for emp_nr in all_emps:
            # Hole Daten aus neuen Funktionen (alle in Stunden!)
            vorgabezeit_std = vorgabezeit_data.get(emp_nr, {}).get('vorgabezeit_std', 0)
            stempelzeit_std = stempelzeit_data.get(emp_nr, 0)
            anwesenheit_std_roh = anwesenheit_data.get(emp_nr, 0)  # type=1 Daten (können unvollständig sein!)
            aw_roh = vorgabezeit_data.get(emp_nr, {}).get('aw', 0)
            umsatz = vorgabezeit_data.get(emp_nr, {}).get('umsatz', 0)
            
            # VALIDIERUNG & FALLBACK: Stempelzeit ≤ Anwesenheit (IMMER!)
            # Problem: type=1 Daten sind oft unvollständig (z.B. MA 5007: 72.7 Std vs. 331.7 Std Stempelzeit)
            # Fallback: Verwende Zeit-Spanne aus type=2 (erste bis letzte Stempelung) als Anwesenheit
            stempelzeit_locosoft_data = stempelzeit_locosoft.get(emp_nr, {})
            anwesenheit_fallback_std = stempelzeit_locosoft_data.get('stempel_min', 0) / 60.0  # Zeit-Spanne in Stunden
            
            if stempelzeit_std > anwesenheit_std_roh:
                # type=1 Daten sind unvollständig, verwende Fallback
                if anwesenheit_fallback_std >= stempelzeit_std:
                    # Fallback ist plausibel (Zeit-Spanne ≥ Stempelzeit)
                    anwesenheit_std = anwesenheit_fallback_std
                    print(f"WerkstattData.get_mechaniker_leistung: MA {emp_nr}: "
                          f"type=1 Daten unvollständig ({anwesenheit_std_roh:.1f} Std < Stempelzeit {stempelzeit_std:.1f} Std). "
                          f"Verwende Fallback: Zeit-Spanne {anwesenheit_std:.1f} Std")
                else:
                    # Letzter Fallback: Stempelzeit + 20% Puffer (für Pausen, Leerlauf)
                    anwesenheit_std = stempelzeit_std * 1.2
                    print(f"WerkstattData.get_mechaniker_leistung: MA {emp_nr}: "
                          f"Keine plausiblen Anwesenheitsdaten. Verwende Stempelzeit × 1.2 = {anwesenheit_std:.1f} Std")
            elif anwesenheit_std_roh == 0 and stempelzeit_std > 0:
                # Keine type=1 Daten vorhanden, verwende Fallback
                if anwesenheit_fallback_std >= stempelzeit_std:
                    anwesenheit_std = anwesenheit_fallback_std
                else:
                    anwesenheit_std = stempelzeit_std * 1.2
            else:
                # type=1 Daten sind plausibel
                anwesenheit_std = anwesenheit_std_roh
            
            # Hole zusätzliche Daten (Tage, Aufträge) aus Legacy-Funktion
            stempelzeit_locosoft_data = stempelzeit_locosoft.get(emp_nr, {})
            
            # Konvertiere für interne Berechnungen in Minuten
            vorgabezeit_min = vorgabezeit_std * 60
            stempelzeit_min = stempelzeit_std * 60
            anwesenheit_min = anwesenheit_std * 60
            
            rohdaten[emp_nr] = {
                'tage': stempelzeit_locosoft_data.get('tage', 0),
                'auftraege': stempelzeit_locosoft_data.get('auftraege', 0),
                'stempelzeit': stempelzeit_min,  # St-Anteil in Minuten (für interne Berechnungen)
                'stempelzeit_std': stempelzeit_std,  # St-Anteil in Stunden (SSOT - für Dashboard)
                'stempelzeit_leistungsgrad': stempelzeit_leistungsgrad.get(emp_nr, 0),
                'anwesenheit': anwesenheit_min,  # Anwesenheit in Minuten (für interne Berechnungen)
                'anwesenheit_std': anwesenheit_std,  # Anwesenheit in Stunden (SSOT - für Dashboard)
                'vorgabezeit': vorgabezeit_min,  # AW-Anteil in Minuten (für interne Berechnungen)
                'vorgabezeit_std': vorgabezeit_std,  # AW-Anteil in Stunden (SSOT - für Dashboard)
                'aw': aw_roh,  # AW-Einheiten (SSOT - für Dashboard)
                'umsatz': umsatz
            }
        
        # Berechne KPIs (mit Zeitraum für korrekte Arbeitstage-Berechnung)
        kpis = WerkstattData.berechne_mechaniker_kpis_aus_rohdaten(rohdaten, von, bis)
        
        # Hole Mechaniker-Details (employees_history)
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Filter für Mechaniker
            emp_filter = ""
            if all_emps:
                emp_filter = f"AND eh.employee_number = ANY(ARRAY[{','.join(map(str, all_emps))}])"
            
            query = f"""
            SELECT
                eh.employee_number as mechaniker_nr,
                eh.name as name,
                eh.subsidiary as betrieb,
                CASE WHEN eh.termination_date IS NULL OR eh.termination_date > CURRENT_DATE THEN true ELSE false END as ist_aktiv
            FROM employees_history eh
            WHERE eh.is_latest_record = true
              {emp_filter}
              AND eh.employee_number != ALL(ARRAY[{','.join(map(str, MECHANIKER_EXCLUDE))}])
            """
            
            # Filter
            conditions = []
            if betrieb is not None:
                conditions.append(f"eh.subsidiary = {int(betrieb)}")
            
            if mechaniker_nr is not None:
                conditions.append(f"eh.employee_number = {int(mechaniker_nr)}")
            
            if not inkl_ehemalige:
                conditions.append("(eh.termination_date IS NULL OR eh.termination_date > CURRENT_DATE)")
            
            if conditions:
                query += " AND " + " AND ".join(conditions)
            
            cursor.execute(query)
            mechaniker_details = {row['mechaniker_nr']: row for row in cursor.fetchall()}
        
        # Kombiniere Rohdaten, KPIs und Mechaniker-Details
        mechaniker_liste = []
        for emp_nr in all_emps:
            # Nur Mechaniker mit Stempelzeit oder AW
            if rohdaten[emp_nr]['stempelzeit'] > 0 or rohdaten[emp_nr]['aw'] > 0:
                # Hole Mechaniker-Details
                mech_detail = mechaniker_details.get(emp_nr)
                if not mech_detail:
                    # Wenn nicht in employees_history, überspringe (nur aktive Mechaniker)
                    continue
                
                kpi_data = kpis.get(emp_nr, {})
                roh_data = rohdaten[emp_nr]
                
                mechaniker_liste.append({
                    'mechaniker_nr': emp_nr,
                    'name': mech_detail['name'],
                    'betrieb': mech_detail['betrieb'],
                    'betrieb_name': BETRIEB_NAMEN.get(mech_detail['betrieb'], 'Unbekannt'),
                    'ist_aktiv': mech_detail['ist_aktiv'],
                    'tage': roh_data['tage'],
                    'auftraege': roh_data['auftraege'],
                    'stempelzeit': round(roh_data['stempelzeit'], 0),  # St-Anteil in Minuten (für Kompatibilität)
                    'stempelzeit_std': round(roh_data.get('stempelzeit_std', roh_data['stempelzeit'] / 60), 1),  # St-Anteil in Stunden (SSOT!)
                    'stempelzeit_leistungsgrad': round(roh_data['stempelzeit_leistungsgrad'], 0),
                    'anwesenheit': round(roh_data['anwesenheit'], 0),  # Anwesenheit in Minuten (für Kompatibilität)
                    'anwesenheit_std': round(roh_data.get('anwesenheit_std', roh_data['anwesenheit'] / 60), 1),  # Anwesenheit in Stunden (SSOT!)
                    'vorgabezeit': round(roh_data.get('vorgabezeit', 0), 0),  # AW-Anteil in Minuten (für Kompatibilität)
                    'vorgabezeit_std': round(roh_data.get('vorgabezeit_std', roh_data.get('vorgabezeit', 0) / 60), 1),  # AW-Anteil in Stunden (SSOT!)
                    'aw': round(roh_data['aw'], 1),  # AW-Einheiten (SSOT!)
                    'umsatz': round(roh_data['umsatz'], 2),
                    'leistungsgrad': kpi_data.get('leistungsgrad'),
                    'produktivitaet': kpi_data.get('produktivitaet')
                })
        
        # Sortierung
        sort_map = {
            'leistungsgrad': lambda x: (x['leistungsgrad'] is not None, x['leistungsgrad'] or 0),
            'stempelzeit': lambda x: x['stempelzeit'],
            'aw': lambda x: x['aw'],
            'auftraege': lambda x: x['auftraege']
        }
        reverse_map = {
            'leistungsgrad': True,
            'stempelzeit': True,
            'aw': True,
            'auftraege': True
        }
        sort_key = sort_map.get(sort_by, sort_map['leistungsgrad'])
        reverse = reverse_map.get(sort_by, True)
        mechaniker_liste.sort(key=sort_key, reverse=reverse)
        
        # NEUIMPLEMENTIERUNG TAG 196: Gesamt-KPIs in Stunden (SSOT!)
        gesamt_auftraege = sum(m['auftraege'] for m in mechaniker_liste)
        gesamt_stempelzeit_std = sum(m.get('stempelzeit_std', m['stempelzeit'] / 60) for m in mechaniker_liste)  # St-Anteil in Stunden
        gesamt_stempelzeit_leistungsgrad = sum(m['stempelzeit_leistungsgrad'] for m in mechaniker_liste)
        gesamt_anwesenheit_std = sum(m.get('anwesenheit_std', m['anwesenheit'] / 60) for m in mechaniker_liste)  # Anwesenheit in Stunden
        gesamt_aw = sum(m['aw'] for m in mechaniker_liste)  # AW-Einheiten
        gesamt_vorgabezeit_std = sum(m.get('vorgabezeit_std', m.get('vorgabezeit', 0) / 60) for m in mechaniker_liste)  # AW-Anteil in Stunden
        gesamt_umsatz = sum(m['umsatz'] for m in mechaniker_liste)
        
        # Gesamt-Leistungsgrad (KORREKT: Vorgabezeit / Stempelzeit)
        # Formel: (Vorgabezeit in Stunden / St-Anteil in Stunden) × 100
        gesamt_leistungsgrad = round(gesamt_vorgabezeit_std / gesamt_stempelzeit_std * 100, 1) if gesamt_stempelzeit_std > 0 else None
        
        # Gesamt-Produktivität (KORREKT: St-Anteil / Anwesenheit)
        # VALIDIERUNG: Stempelzeit kann nicht größer sein als Anwesenheit!
        if gesamt_stempelzeit_std > gesamt_anwesenheit_std and gesamt_anwesenheit_std > 0:
            logging.warning(
                f"WerkstattData.get_mechaniker_leistung: Stempelzeit ({gesamt_stempelzeit_std:.1f} Std) > Anwesenheit ({gesamt_anwesenheit_std:.1f} Std)! "
                f"Das ist physikalisch unmöglich. Mögliche Ursachen: Fehlende Anwesenheitsdaten (type=1) oder falsche Berechnung."
            )
            # Cap auf 100% für Produktivität (kann nicht > 100% sein)
            gesamt_produktivitaet = 100.0
        else:
            gesamt_produktivitaet = round(gesamt_stempelzeit_std / gesamt_anwesenheit_std * 100, 1) if gesamt_anwesenheit_std > 0 else None
        
        # Anzahl Arbeitstage
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT COUNT(DISTINCT DATE(start_time)) as count
                FROM times
                WHERE type = 2 AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
            """, [von, bis])
            anzahl_tage = cursor.fetchone()['count'] or 0

            # Anwesenheitsgrad berechnen (TAG 181 - SSOT)
            # FIX TAG 196: Verwende bereits berechnete anwesenheitsgrad Werte aus kpis,
            # da diese die korrekten Arbeitstage im Zeitraum verwenden!
            # Die Funktion berechne_anwesenheitsgrad_fuer_mechaniker_liste() würde sonst
            # die falschen 'tage' (Tage mit Stempelungen) verwenden.
            gesamt_anwesend_h = sum(m.get('anwesenheit_std', m.get('anwesenheit', 0) / 60) for m in mechaniker_liste)
            # Berechne Gesamt-Bezahlt aus Arbeitstagen im Zeitraum
            arbeitstage_gesamt = 0
            current = von
            while current <= bis:
                if current.weekday() < 5:  # Mo-Fr
                    arbeitstage_gesamt += 1
                current += timedelta(days=1)
            gesamt_bezahlt_h = arbeitstage_gesamt * 8.0 * len(mechaniker_liste)  # Arbeitstage × 8h × Anzahl Mechaniker
            gesamt_anwesenheitsgrad = berechne_anwesenheitsgrad(gesamt_anwesend_h, gesamt_bezahlt_h) if gesamt_bezahlt_h > 0 else None
            
            # Aktualisiere mechaniker_liste mit bereits berechneten anwesenheitsgrad Werten
            for m in mechaniker_liste:
                # anwesenheitsgrad wurde bereits in berechne_mechaniker_kpis_aus_rohdaten() korrekt berechnet
                # Verwende diesen Wert, überschreibe nicht!
                if 'anwesenheitsgrad' not in m:
                    # Fallback: Berechne aus anwesenheit_std und arbeitstagen
                    anwesenheit_std = m.get('anwesenheit_std', m.get('anwesenheit', 0) / 60)
                    bezahlt_h = arbeitstage_gesamt * 8.0
                    m['anwesenheitsgrad'] = berechne_anwesenheitsgrad(anwesenheit_std, bezahlt_h)

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
                    'stempelzeit': round(gesamt_stempelzeit_std * 60, 0),  # St-Anteil in Minuten (für Kompatibilität)
                    'stempelzeit_std': round(gesamt_stempelzeit_std, 1),  # St-Anteil in Stunden (SSOT!)
                    'stempelzeit_leistungsgrad': round(gesamt_stempelzeit_leistungsgrad, 0),  # TAG 192: Für Vergleich mit Locosoft
                    'anwesenheit': round(gesamt_anwesenheit_std * 60, 0),  # Anwesenheit in Minuten (für Kompatibilität)
                    'anwesenheit_std': round(gesamt_anwesenheit_std, 1),  # Anwesenheit in Stunden (SSOT!)
                    'vorgabezeit': round(gesamt_vorgabezeit_std * 60, 0),  # AW-Anteil in Minuten (für Kompatibilität)
                    'vorgabezeit_std': round(gesamt_vorgabezeit_std, 1),  # AW-Anteil in Stunden (SSOT!)
                    'aw': round(gesamt_aw, 1),  # AW-Einheiten (SSOT!)
                    'umsatz': round(gesamt_umsatz, 2),
                    'leistungsgrad': gesamt_leistungsgrad,
                    'produktivitaet': gesamt_produktivitaet,
                    'anwesenheitsgrad': gesamt_anwesenheitsgrad,
                    'bezahlt_h': round(sum(m.get('bezahlt_h', 0) for m in mechaniker_liste), 1),
                    'anwesend_h': round(sum(m.get('anwesend_h', 0) for m in mechaniker_liste), 1)
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
    # REFACTORED KPI FUNCTIONS (TAG 194)
    # =========================================================================
    # Separate Funktionen für bessere Wartbarkeit und Testbarkeit

    @staticmethod
    def get_stempelungen_dedupliziert(
        von: date,
        bis: date,
        leerlauf_filter: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Holt deduplizierte Stempelungen (type=2) für Zeitraum.
        
        Args:
            von: Startdatum
            bis: Enddatum
            leerlauf_filter: SQL-Filter für Leerlaufaufträge (z.B. "AND t.order_number != ALL(ARRAY[...])")
        
        Returns:
            List mit Dicts: {employee_number, datum, start_time, end_time, order_number}
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = f"""
                -- TAG 211: Konsistente Deduplizierung - sekundengleiche Stempelzeiten desselben Mechanikers auf demselben Auftrag nur einmal
                SELECT DISTINCT ON (employee_number, order_number, start_time, end_time)
                    employee_number,
                    DATE(start_time) as datum,
                    start_time,
                    end_time,
                    order_number
                FROM times t
                WHERE type = 2
                  AND end_time IS NOT NULL
                  AND order_number > 0
                  {leerlauf_filter}
                  AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
                ORDER BY employee_number, order_number, start_time, end_time
            """
            
            cursor.execute(query, [von, bis])
            return rows_to_list(cursor.fetchall())

    @staticmethod
    def get_stempelzeit_locosoft(
        von: date,
        bis: date,
        leerlauf_filter: str = ""
    ) -> Dict[int, Dict[str, Any]]:
        """
        Berechnet Stempelzeit nach Locosoft-Logik (Zeit-Spanne - Lücken - Pausen).
        
        Args:
            von: Startdatum
            bis: Enddatum
            leerlauf_filter: SQL-Filter für Leerlaufaufträge
        
        Returns:
            Dict: {employee_number: {tage, auftraege, stempel_min}}
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = f"""
                WITH
                stempelungen_dedupliziert AS (
                    -- TAG 211: Konsistente Deduplizierung - sekundengleiche Stempelzeiten desselben Mechanikers auf demselben Auftrag nur einmal
                    SELECT DISTINCT ON (employee_number, order_number, start_time, end_time)
                        employee_number,
                        DATE(start_time) as datum,
                        start_time,
                        end_time,
                        order_number
                    FROM times t
                    WHERE type = 2
                      AND end_time IS NOT NULL
                      AND order_number > 0
                      {leerlauf_filter}
                      AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
                    ORDER BY employee_number, order_number, start_time, end_time
                ),
                tages_spannen AS (
                    SELECT
                        employee_number,
                        datum,
                        MIN(start_time) as erste_stempelung,
                        MAX(end_time) as letzte_stempelung,
                        COUNT(DISTINCT order_number) as auftraege,
                        EXTRACT(EPOCH FROM (MAX(end_time) - MIN(start_time))) / 60 as spanne_minuten
                    FROM stempelungen_dedupliziert
                    GROUP BY employee_number, datum
                ),
                luecken_pro_tag AS (
                    SELECT
                        s1.employee_number,
                        s1.datum,
                        SUM(EXTRACT(EPOCH FROM (s2.start_time - s1.end_time)) / 60) as luecken_minuten
                    FROM stempelungen_dedupliziert s1
                    JOIN stempelungen_dedupliziert s2 
                        ON s1.employee_number = s2.employee_number 
                        AND s1.datum = s2.datum
                        AND s2.start_time > s1.end_time
                        AND NOT EXISTS (
                            SELECT 1 FROM stempelungen_dedupliziert s3
                            WHERE s3.employee_number = s1.employee_number
                              AND s3.datum = s1.datum
                              AND s3.start_time > s1.end_time
                              AND s3.start_time < s2.start_time
                        )
                    GROUP BY s1.employee_number, s1.datum
                ),
                pausenzeiten_pro_tag AS (
                    SELECT
                        ts.employee_number,
                        ts.datum,
                        SUM(
                            CASE 
                                WHEN eb.break_start IS NOT NULL 
                                     AND eb.break_end IS NOT NULL
                                     AND eb.break_start < eb.break_end
                                     AND (eb.break_start < EXTRACT(HOUR FROM ts.letzte_stempelung)::numeric + EXTRACT(MINUTE FROM ts.letzte_stempelung)::numeric / 60.0)
                                     AND (eb.break_end > EXTRACT(HOUR FROM ts.erste_stempelung)::numeric + EXTRACT(MINUTE FROM ts.erste_stempelung)::numeric / 60.0)
                                THEN (eb.break_end - eb.break_start) * 60.0
                                ELSE 0
                            END
                        ) as pausen_minuten
                    FROM tages_spannen ts
                    LEFT JOIN employees_breaktimes eb 
                        ON ts.employee_number = eb.employee_number
                        AND EXTRACT(DOW FROM ts.datum) = eb.dayofweek
                        AND eb.validity_date <= ts.datum
                        AND (eb.is_latest_record IS NULL OR eb.is_latest_record = true)
                    GROUP BY ts.employee_number, ts.datum
                ),
                stempelzeit_locosoft AS (
                    SELECT
                        ts.employee_number,
                        ts.datum,
                        ts.auftraege,
                        ROUND((ts.spanne_minuten 
                               - COALESCE(l.luecken_minuten, 0) 
                               - COALESCE(p.pausen_minuten, 0))::numeric, 0) as stempel_min
                    FROM tages_spannen ts
                    LEFT JOIN luecken_pro_tag l 
                        ON ts.employee_number = l.employee_number 
                        AND ts.datum = l.datum
                    LEFT JOIN pausenzeiten_pro_tag p 
                        ON ts.employee_number = p.employee_number 
                        AND ts.datum = p.datum
                )
                SELECT
                    employee_number,
                    COUNT(DISTINCT datum) as tage,
                    SUM(auftraege) as auftraege,
                    SUM(stempel_min) as stempel_min
                FROM stempelzeit_locosoft
                WHERE stempel_min > 0
                GROUP BY employee_number
            """
            
            cursor.execute(query, [von, bis])
            result = {}
            for row in cursor.fetchall():
                result[row['employee_number']] = {
                    'tage': int(row['tage']),
                    'auftraege': int(row['auftraege']),
                    'stempel_min': float(row['stempel_min'])
                }
            return result

    @staticmethod
    def get_stempelzeit_leistungsgrad(
        von: date,
        bis: date,
        leerlauf_filter: str = ""
    ) -> Dict[int, float]:
        """
        Berechnet Stempelzeit für Leistungsgrad (Summe aller gestempelten Zeiten).
        
        Args:
            von: Startdatum
            bis: Enddatum
            leerlauf_filter: SQL-Filter für Leerlaufaufträge
        
        Returns:
            Dict: {employee_number: stempel_min_leistungsgrad}
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = f"""
                SELECT
                    t.employee_number,
                    SUM(EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 60) as stempel_min_leistungsgrad
                FROM (
                    -- TAG 211: Konsistente Deduplizierung - sekundengleiche Stempelzeiten desselben Mechanikers auf demselben Auftrag nur einmal
                    SELECT DISTINCT ON (t.employee_number, t.order_number, t.start_time, t.end_time)
                        t.employee_number,
                        t.start_time,
                        t.end_time
                    FROM times t
                    WHERE t.type = 2
                      AND t.end_time IS NOT NULL
                      AND t.order_number > 31
                      {leerlauf_filter}
                      AND t.start_time >= %s AND t.start_time < %s + INTERVAL '1 day'
                    ORDER BY t.employee_number, t.order_number, t.start_time, t.end_time
                ) t
                GROUP BY t.employee_number
            """
            
            cursor.execute(query, [von, bis])
            result = {}
            for row in cursor.fetchall():
                result[row['employee_number']] = float(row['stempel_min_leistungsgrad'] or 0)
            return result

    @staticmethod
    def get_stempelungen_roh(
        von: date,
        bis: date
    ) -> List[Dict[str, Any]]:
        """
        Holt position-basierte Stempelungen (TAG 194).
        
        Args:
            von: Startdatum
            bis: Enddatum
        
        Returns:
            List mit Dicts: {employee_number, order_number, order_position, 
                           order_position_line, start_time, end_time, stempel_minuten}
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                -- TAG 211: Konsistente Deduplizierung - sekundengleiche Stempelzeiten desselben Mechanikers auf demselben Auftrag nur einmal
                -- Position-Informationen werden beibehalten (erste Position bei Duplikaten)
                SELECT DISTINCT ON (t.employee_number, t.order_number, t.start_time, t.end_time)
                    t.employee_number,
                    t.order_number,
                    t.order_position,
                    t.order_position_line,
                    t.start_time,
                    t.end_time,
                    EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 60 as stempel_minuten
                FROM times t
                WHERE t.type = 2
                    AND t.end_time IS NOT NULL
                    AND t.order_number > 31
                    AND t.order_position IS NOT NULL
                    AND t.order_position_line IS NOT NULL
                    AND t.start_time >= %s AND t.start_time < %s + INTERVAL '1 day'
                ORDER BY t.employee_number, t.order_number, t.start_time, t.end_time, t.order_position, t.order_position_line
            """
            
            cursor.execute(query, [von, bis])
            return rows_to_list(cursor.fetchall())

    @staticmethod
    def get_anwesenheit_aus_times(
        von: date,
        bis: date
    ) -> Dict[int, float]:
        """
        NEUIMPLEMENTIERUNG TAG 196: Anwesenheit aus times type=1.
        
        EINFACH & KORREKT nach Locosoft-Definition:
        - Anwesenheit = Gesamte Anwesenheitszeit (Kommt→Geht)
        
        Args:
            von: Startdatum
            bis: Enddatum
        
        Returns:
            Dict: {employee_number: anwesenheit_stunden}
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT
                    employee_number,
                    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60.0) / 60.0 AS anwesenheit_stunden
                FROM times
                WHERE type = 1
                  AND end_time IS NOT NULL
                  AND start_time >= %s
                  AND start_time < %s + INTERVAL '1 day'
                GROUP BY employee_number
            """
            
            cursor.execute(query, [von, bis])
            result = {}
            for row in cursor.fetchall():
                result[row['employee_number']] = float(row['anwesenheit_stunden'] or 0)
            return result

    @staticmethod
    def get_stempelzeit_aus_times(
        von: date,
        bis: date
    ) -> Dict[int, float]:
        """
        NEUIMPLEMENTIERUNG TAG 196: Stempelzeit (St-Anteil) aus times type=2.
        
        Auftrags-basierte Deduplizierung:
        - DISTINCT ON (employee_number, order_number, start_time, end_time)
        - Verschiedene Positionen auf demselben Auftrag zur gleichen Zeit → 1× zählen
        - Verschiedene Aufträge zur gleichen Zeit → separat zählen
        
        Beispiel:
        - 08:00-09:00 (Auftrag A, Pos 1)
        - 08:00-09:00 (Auftrag A, Pos 2)  ← gleicher Auftrag, gleiche Zeit → 1× zählen
        - 08:00-09:00 (Auftrag B)          ← anderer Auftrag, gleiche Zeit → separat zählen
        → Ergebnis: 2 Std (1 Std Auftrag A + 1 Std Auftrag B)
        
        WICHTIG: ALLE Aufträge erfassen - kein Filter auf Betrieb, Auftragsart, order_number!
        Alle Stempelungen type=2 zählen, egal ob DEGO, DEGH, intern, extern, Garantie!
        
        HINWEIS: Pausenzeiten werden NICHT abgezogen, da Locosoft diese auch nicht abzieht.
        Die Diskrepanz zu Locosoft (14.8 Std) deutet auf eine andere Berechnungsmethode hin.
        
        Args:
            von: Startdatum
            bis: Enddatum
        
        Returns:
            Dict: {employee_number: stempelzeit_stunden}
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    employee_number,
                    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 3600.0) AS stempelzeit_stunden
                FROM (
                    -- FIX TAG 196: Auftrags-basierte Deduplizierung!
                    -- DISTINCT ON (employee_number, order_number, start_time, end_time)
                    -- Verschiedene Positionen auf demselben Auftrag zur gleichen Zeit → 1× zählen
                    -- Verschiedene Aufträge zur gleichen Zeit → separat zählen
                    SELECT DISTINCT ON (employee_number, order_number, start_time, end_time)
                        employee_number,
                        start_time,
                        end_time
                    FROM times
                    WHERE type = 2
                      AND end_time IS NOT NULL
                      AND start_time >= %s
                      AND start_time < %s + INTERVAL '1 day'
                    ORDER BY employee_number, order_number, start_time, end_time
                ) t
                GROUP BY employee_number
            """
            
            cursor.execute(query, [von, bis])
            result = {}
            for row in cursor.fetchall():
                result[row['employee_number']] = float(row['stempelzeit_stunden'] or 0)
            return result

    @staticmethod
    def get_vorgabezeit_aus_labours(
        von: date,
        bis: date
    ) -> Dict[int, Dict[str, float]]:
        """
        NEUIMPLEMENTIERUNG TAG 196: Vorgabezeit (AW-Anteil) aus labours-Tabelle.
        
        EINFACH & KORREKT nach Locosoft-Definition:
        - Vorgabezeit = AW-Einheiten × 6 Minuten / 60 = Stunden
        - NUR für Aufträge, an denen der Mechaniker gestempelt hat!
        
        Args:
            von: Startdatum
            bis: Enddatum
        
        Returns:
            Dict: {employee_number: {aw, vorgabezeit_std, umsatz}}
            - aw: AW-Einheiten
            - vorgabezeit_std: Vorgabezeit in Stunden
            - umsatz: Umsatz in EUR
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                WITH auftraege_mit_stempelung AS (
                    SELECT DISTINCT
                        t.employee_number,
                        t.order_number
                    FROM times t
                    WHERE t.type = 2
                      AND t.end_time IS NOT NULL
                      AND t.start_time >= %s 
                      AND t.start_time < %s + INTERVAL '1 day'
                )
                SELECT 
                    ams.employee_number,
                    -- FIX TAG 196: Summiere nur AW, die diesem Mechaniker zugeordnet sind!
                    -- werkstatt_auftraege_abgerechnet summiert auch nur die AW pro Mechaniker.
                    SUM(CASE WHEN l.mechanic_no = ams.employee_number THEN l.time_units ELSE 0 END) AS aw,
                    SUM(CASE WHEN l.mechanic_no = ams.employee_number THEN l.time_units ELSE 0 END) * 6.0 / 60.0 AS vorgabezeit_std,
                    SUM(CASE WHEN l.mechanic_no = ams.employee_number THEN l.net_price_in_order ELSE 0 END) AS umsatz
                FROM auftraege_mit_stempelung ams
                JOIN labours l ON ams.order_number = l.order_number
                WHERE l.time_units > 0
                GROUP BY ams.employee_number
            """
            
            cursor.execute(query, [von, bis])
            result = {}
            for row in cursor.fetchall():
                result[row['employee_number']] = {
                    'aw': float(row['aw'] or 0),  # AW-Einheiten
                    'vorgabezeit_std': float(row['vorgabezeit_std'] or 0),  # Vorgabezeit in Stunden
                    'umsatz': float(row['umsatz'] or 0)  # Umsatz in EUR
                }
            return result

    @staticmethod
    def berechne_st_anteil_hybrid(
        stempelzeit_locosoft: Dict[int, Dict[str, Any]],
        stempelungen_roh: List[Dict[str, Any]]
    ) -> Dict[int, float]:
        """
        Berechnet St-Anteil nach Hybrid-Ansatz (TAG 194):
        - Basis: Zeit-Spanne (aus stempelzeit_locosoft)
        - Plus: 10.6% der Stempelzeit für Positionen OHNE AW auf Aufträgen MIT AW
        
        Args:
            stempelzeit_locosoft: {employee_number: {tage, auftraege, stempel_min}}
            stempelungen_roh: List mit position-basierten Stempelungen
        
        Returns:
            Dict: {employee_number: stempel_min_hybrid}
        """
        # 1. Finde Aufträge mit AW
        auftraege_mit_aw = set()
        for stempelung in stempelungen_roh:
            auftraege_mit_aw.add(stempelung['order_number'])
        
        # 2. Prüfe welche Aufträge tatsächlich AW haben
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if auftraege_mit_aw:
                query = """
                    SELECT DISTINCT order_number
                    FROM labours
                    WHERE order_number = ANY(%s)
                      AND time_units > 0
                """
                cursor.execute(query, [list(auftraege_mit_aw)])
                auftraege_mit_aw = {row['order_number'] for row in cursor.fetchall()}
        
        # 3. Finde Positionen OHNE AW auf Aufträgen MIT AW
        positionen_ohne_aw = {}
        for stempelung in stempelungen_roh:
            if stempelung['order_number'] in auftraege_mit_aw:
                emp_nr = stempelung['employee_number']
                if emp_nr not in positionen_ohne_aw:
                    positionen_ohne_aw[emp_nr] = 0.0
                
                # Prüfe ob Position AW hat
                with locosoft_session() as conn:
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    query = """
                        SELECT COUNT(*) as hat_aw
                        FROM labours
                        WHERE order_number = %s
                          AND order_position = %s
                          AND order_position_line = %s
                          AND time_units > 0
                    """
                    cursor.execute(query, [
                        stempelung['order_number'],
                        stempelung['order_position'],
                        stempelung['order_position_line']
                    ])
                    hat_aw = cursor.fetchone()['hat_aw'] > 0
                    
                    if not hat_aw:
                        positionen_ohne_aw[emp_nr] += float(stempelung['stempel_minuten'])
        
        # 4. Berechne Hybrid: Zeit-Spanne + 10.6% der Positionen ohne AW
        result = {}
        for emp_nr, data in stempelzeit_locosoft.items():
            basis = data['stempel_min']
            zusatz = positionen_ohne_aw.get(emp_nr, 0.0) * 0.106  # 10.6%
            result[emp_nr] = basis + zusatz
        
        return result

    @staticmethod
    def berechne_mechaniker_kpis_aus_rohdaten(
        rohdaten: Dict[int, Dict[str, Any]],
        von: date,
        bis: date
    ) -> Dict[int, Dict[str, Any]]:
        """
        Berechnet alle KPIs für Mechaniker aus Rohdaten.
        Nutzt utils/kpi_definitions.py (SSOT).
        
        Args:
            rohdaten: {
                employee_number: {
                    'tage': int,
                    'auftraege': int,
                    'stempelzeit': float,  # Minuten (Hybrid)
                    'stempelzeit_leistungsgrad': float,  # Minuten
                    'anwesenheit': float,  # Minuten
                    'aw': float,  # Stunden
                    'umsatz': float  # EUR
                }
            }
        
        Returns:
            {
                employee_number: {
                    'leistungsgrad': float,
                    'produktivitaet': float,
                    'anwesenheitsgrad': float,
                    'auslastungsgrad': float,
                    ...
                }
            }
        """
        from utils.kpi_definitions import (
            berechne_leistungsgrad,
            berechne_produktivitaet,
            berechne_anwesenheitsgrad,
            berechne_auslastungsgrad,
            minuten_zu_aw,
            minuten_zu_stunden,
            aw_zu_stunden
        )
        
        result = {}
        
        for emp_nr, data in rohdaten.items():
            # NEUIMPLEMENTIERUNG TAG 196: Einfache, korrekte KPI-Berechnung
            # 
            # Alle Werte sind jetzt in Stunden (SSOT)!
            # - vorgabezeit_std = AW-Anteil in Stunden (aus get_vorgabezeit_aus_labours)
            # - stempelzeit_std = St-Anteil in Stunden (aus get_stempelzeit_aus_times)
            # - anwesenheit_std = Anwesenheit in Stunden (aus get_anwesenheit_aus_times)
            #
            vorgabezeit_std = data.get('vorgabezeit_std', 0)  # AW-Anteil in Stunden (SSOT!)
            stempelzeit_std = data.get('stempelzeit_std', 0)  # St-Anteil in Stunden (SSOT!)
            anwesenheit_std = data.get('anwesenheit_std', 0)  # Anwesenheit in Stunden (SSOT!)
            stempelzeit_leistungsgrad_min = data.get('stempelzeit_leistungsgrad', 0)
            aw_roh = data.get('aw', 0)  # AW-Einheiten (SSOT!)
            tage = data.get('tage', 0)
            
            # KORREKTE LEISTUNGSGRAD-BERECHNUNG (Locosoft-Formel):
            # Leistungsgrad = (Vorgabezeit / Stempelzeit) × 100
            # Beispiel: 200 Std Vorgabe / 150 Std Stempel = 133%
            if stempelzeit_std > 0 and vorgabezeit_std > 0:
                leistungsgrad = round((vorgabezeit_std / stempelzeit_std * 100), 1)
            else:
                leistungsgrad = None
            
            # KORREKTE PRODUKTIVITÄT-BERECHNUNG (Locosoft-Formel):
            # Produktivität = (Stempelzeit / Anwesenheit) × 100
            # Beispiel: 150 Std Stempel / 170 Std Anwesend = 88%
            if anwesenheit_std > 0:
                produktivitaet = round((stempelzeit_std / anwesenheit_std * 100), 1)
            else:
                produktivitaet = None
            
            # Anwesenheitsgrad: Bezahlte Zeit = Arbeitstage im Zeitraum * 8h
            # FIX TAG 196: tage = Anzahl Tage mit Stempelungen, nicht Arbeitstage!
            # Berechne echte Arbeitstage im Zeitraum (Mo-Fr, ohne Feiertage)
            arbeitstage_im_zeitraum = 0
            current = von
            while current <= bis:
                if current.weekday() < 5:  # Mo-Fr (0=Mo, 4=Fr)
                    arbeitstage_im_zeitraum += 1
                current += timedelta(days=1)
            
            bezahlt_h = arbeitstage_im_zeitraum * 8.0
            anwesend_h = anwesenheit_std  # Bereits in Stunden (SSOT!)
            anwesenheitsgrad = berechne_anwesenheitsgrad(anwesend_h, bezahlt_h)
            
            # Auslastungsgrad
            gestempelt_h = stempelzeit_std  # Bereits in Stunden (SSOT!)
            auslastungsgrad = berechne_auslastungsgrad(gestempelt_h, anwesend_h)
            
            result[emp_nr] = {
                'leistungsgrad': leistungsgrad,
                'produktivitaet': produktivitaet,
                'anwesenheitsgrad': anwesenheitsgrad,
                'auslastungsgrad': auslastungsgrad
            }
        
        return result

    # =========================================================================
    # AUFTRÄGE (Jobs / Orders)
    # =========================================================================

    @staticmethod
    def get_offene_auftraege(
        betrieb: Optional[int] = None,
        tage_zurueck: int = 7,
        nur_offen: bool = True,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Holt alle offenen Werkstatt-Aufträge LIVE aus Locosoft.

        WICHTIG: Nutzt echte Locosoft-Tabellen:
        - orders: Werkstatt-Aufträge
        - employees_history: Serviceberater
        - vehicles, makes: Fahrzeugdaten
        - customers_suppliers: Kundendaten
        - labours: Arbeitspositionen (AW)

        Args:
            betrieb: Betrieb-ID (1=DEG, 2=HYU, 3=LAN, None=alle)
            tage_zurueck: Wie viele Tage zurück (default: 7)
            nur_offen: Nur offene Aufträge (default: True)
            limit: Max. Anzahl Ergebnisse (default: 100)

        Returns:
            Dict mit 'auftraege' (Liste) und Metadaten

        Example:
            >>> data = WerkstattData.get_offene_auftraege(betrieb=1, tage_zurueck=14)
            >>> data['auftraege'][0]
            {'auftrag_nr': 12345, 'kennzeichen': 'DEG-XX 123', 'vorgabe_aw': 4.5, ...}
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Basis-Query für Aufträge
            query = """
                SELECT
                    o.number as auftrag_nr,
                    o.subsidiary as betrieb,
                    o.order_date as auftrag_datum,
                    o.order_taking_employee_no as serviceberater_nr,
                    eh.name as serviceberater_name,
                    o.vehicle_number,
                    v.license_plate as kennzeichen,
                    m.description as marke,
                    COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name) as kunde,
                    o.urgency as dringlichkeit,
                    o.has_open_positions as ist_offen,
                    o.has_closed_positions as hat_abgeschlossene,
                    o.estimated_inbound_time as geplant_eingang,
                    o.estimated_outbound_time as geplant_fertig
                FROM orders o
                LEFT JOIN employees_history eh ON o.order_taking_employee_no = eh.employee_number
                    AND eh.is_latest_record = true
                LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
                LEFT JOIN makes m ON v.make_number = m.make_number
                LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
                WHERE o.order_date >= CURRENT_DATE - INTERVAL '%s days'
            """

            params = [tage_zurueck]

            if nur_offen:
                query += " AND o.has_open_positions = true"

            if betrieb is not None:
                query += " AND o.subsidiary = %s"
                params.append(int(betrieb))

            query += f" ORDER BY o.order_date DESC LIMIT {int(limit)}"

            cursor.execute(query, params)
            auftraege_raw = cursor.fetchall()

            # TAG 213 PERFORMANCE FIX: N+1 Query Problem behoben
            # Statt für jeden Auftrag eine separate Query, eine Query für alle Aufträge
            auftrag_nrs = [a['auftrag_nr'] for a in auftraege_raw]
            
            # Eine Query für alle Aufträge (statt N Queries)
            labour_data = {}
            if auftrag_nrs:
                cursor.execute("""
                    SELECT
                        order_number,
                        COALESCE(SUM(time_units), 0) as total_aw,
                        STRING_AGG(DISTINCT CAST(mechanic_no AS TEXT), ', ') as mechaniker
                    FROM labours
                    WHERE order_number = ANY(%s) AND time_units > 0
                    GROUP BY order_number
                """, [auftrag_nrs])
                
                for row in cursor.fetchall():
                    labour_data[row['order_number']] = {
                        'total_aw': float(row['total_aw'] or 0),
                        'mechaniker': row['mechaniker']
                    }

            # Jetzt durch Aufträge iterieren und Daten zuordnen
            auftraege = []
            for auftrag in auftraege_raw:
                # Hole Labour-Daten aus Dictionary (statt Query)
                labour_info = labour_data.get(auftrag['auftrag_nr'], {
                    'total_aw': 0,
                    'mechaniker': None
                })

                # Datum formatieren
                auftrag_datum = auftrag['auftrag_datum']
                datum_str = auftrag_datum.strftime('%d.%m.%Y') if auftrag_datum else None
                uhrzeit_str = auftrag_datum.strftime('%H:%M') if auftrag_datum else None
                geplant_fertig = auftrag['geplant_fertig']
                geplant_fertig_str = geplant_fertig.strftime('%d.%m.%Y %H:%M') if geplant_fertig else None

                auftraege.append({
                    'auftrag_nr': auftrag['auftrag_nr'],
                    'betrieb': auftrag['betrieb'],
                    'betrieb_name': BETRIEB_NAMEN.get(auftrag['betrieb'], 'Unbekannt'),
                    'datum': datum_str,
                    'uhrzeit': uhrzeit_str,
                    'serviceberater': auftrag['serviceberater_name'] or f"MA {auftrag['serviceberater_nr']}",
                    'serviceberater_nr': auftrag['serviceberater_nr'],
                    'kennzeichen': auftrag['kennzeichen'],
                    'marke': auftrag['marke'],
                    'kunde': auftrag['kunde'],
                    'dringlichkeit': auftrag['dringlichkeit'],
                    'ist_offen': auftrag['ist_offen'],
                    'hat_abgeschlossene': auftrag['hat_abgeschlossene'],
                    'geplant_fertig': geplant_fertig_str,
                    'vorgabe_aw': labour_info['total_aw'],
                    'mechaniker': labour_info['mechaniker']
                })

            logger.info(f"WerkstattData.get_offene_auftraege: {len(auftraege)} Aufträge, Betrieb={betrieb}, Tage={tage_zurueck}")

            return {
                'filter': {
                    'betrieb': betrieb,
                    'tage_zurueck': tage_zurueck,
                    'nur_offen': nur_offen
                },
                'anzahl': len(auftraege),
                'auftraege': auftraege
            }

    @staticmethod
    def get_dashboard_stats() -> Dict[str, Any]:
        """
        Kombinierte Dashboard-Übersicht für LIVE-Monitoring.

        WICHTIG: Nutzt echte Locosoft-Tabellen:
        - orders: Werkstatt-Aufträge
        - labours: Arbeitspositionen
        - times: Stempelungen (Feierabend-Status)
        - employees_history: Mitarbeiter-Stammdaten

        Returns:
            Dict mit 'auftraege_pro_betrieb', 'heute', 'aktive_mechaniker', 'serviceberater'

        Example:
            >>> data = WerkstattData.get_dashboard_stats()
            >>> data['heute']['offen']
            15
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 1. Offene Aufträge pro Betrieb
            cursor.execute("""
                SELECT
                    subsidiary as betrieb,
                    COUNT(*) as anzahl_offen,
                    COUNT(CASE WHEN urgency >= 4 THEN 1 END) as anzahl_dringend
                FROM orders
                WHERE has_open_positions = true
                  AND order_date >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY subsidiary
                ORDER BY subsidiary
            """)
            auftraege_pro_betrieb = [
                {
                    'betrieb': r['betrieb'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['betrieb'], 'Unbekannt'),
                    'anzahl_offen': r['anzahl_offen'],
                    'anzahl_dringend': r['anzahl_dringend']
                } for r in cursor.fetchall()
            ]

            # 2. Heutige Aufträge Statistik
            cursor.execute("""
                SELECT
                    COUNT(*) as gesamt,
                    COUNT(CASE WHEN has_open_positions = true AND has_closed_positions = false THEN 1 END) as offen,
                    COUNT(CASE WHEN has_closed_positions = true THEN 1 END) as fertig,
                    COUNT(CASE WHEN has_open_positions = true AND has_closed_positions = true THEN 1 END) as teilweise
                FROM orders
                WHERE DATE(order_date) = CURRENT_DATE
            """)
            heute_row = cursor.fetchone()
            heute_stats = {
                'gesamt': heute_row['gesamt'],
                'offen': heute_row['offen'],
                'fertig': heute_row['fertig'],
                'teilweise': heute_row['teilweise']
            }

            # 3. Aktive Mechaniker (mit zugeordneten offenen Aufträgen, ohne Feierabend)
            cursor.execute("""
                WITH feierabend AS (
                    SELECT employee_number, MAX(end_time) as gegangen_um
                    FROM times
                    WHERE type = 1
                      AND DATE(start_time) = CURRENT_DATE
                      AND end_time IS NOT NULL
                    GROUP BY employee_number
                ),
                heute_gestempelt AS (
                    SELECT DISTINCT employee_number
                    FROM times
                    WHERE type = 2
                      AND DATE(start_time) = CURRENT_DATE
                )
                SELECT
                    l.mechanic_no,
                    eh.name as name,
                    eh.subsidiary as betrieb,
                    COUNT(DISTINCT l.order_number) as anzahl_auftraege,
                    COALESCE(SUM(l.time_units), 0) as summe_aw,
                    f.gegangen_um,
                    CASE WHEN hg.employee_number IS NOT NULL THEN true ELSE false END as heute_gestempelt
                FROM labours l
                JOIN orders o ON l.order_number = o.number
                LEFT JOIN employees_history eh ON l.mechanic_no = eh.employee_number
                    AND eh.is_latest_record = true
                LEFT JOIN feierabend f ON l.mechanic_no = f.employee_number
                LEFT JOIN heute_gestempelt hg ON l.mechanic_no = hg.employee_number
                WHERE l.mechanic_no IS NOT NULL
                  AND o.has_open_positions = true
                  AND o.order_date >= CURRENT_DATE - INTERVAL '2 days'
                  AND f.employee_number IS NULL
                GROUP BY l.mechanic_no, eh.name, eh.subsidiary, f.gegangen_um, hg.employee_number
                ORDER BY anzahl_auftraege DESC
            """)
            aktive_mechaniker = [
                {
                    'mechaniker_nr': r['mechanic_no'],
                    'name': r['name'] or f"MA {r['mechanic_no']}",
                    'betrieb': r['betrieb'],
                    'anzahl_auftraege': r['anzahl_auftraege'],
                    'summe_aw': float(r['summe_aw']),
                    'heute_gestempelt': r.get('heute_gestempelt', False)
                } for r in cursor.fetchall()
            ]

            # 4. Serviceberater mit offenen Aufträgen
            cursor.execute("""
                SELECT
                    o.order_taking_employee_no as sb_nr,
                    eh.name as sb_name,
                    COUNT(*) as anzahl_offen
                FROM orders o
                LEFT JOIN employees_history eh ON o.order_taking_employee_no = eh.employee_number
                    AND eh.is_latest_record = true
                WHERE o.has_open_positions = true
                  AND o.order_date >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY o.order_taking_employee_no, eh.name
                ORDER BY anzahl_offen DESC
                LIMIT 10
            """)
            serviceberater = [
                {
                    'sb_nr': r['sb_nr'],
                    'name': r['sb_name'] or f"MA {r['sb_nr']}",
                    'anzahl_offen': r['anzahl_offen']
                } for r in cursor.fetchall()
            ]

            logger.info(f"WerkstattData.get_dashboard_stats: {len(aktive_mechaniker)} aktive Mechaniker, {heute_stats['offen']} offene Aufträge heute")

            return {
                'auftraege_pro_betrieb': auftraege_pro_betrieb,
                'heute': heute_stats,
                'aktive_mechaniker': aktive_mechaniker,
                'serviceberater': serviceberater
            }

    # =========================================================================
    # KAPAZITÄT (Capacity Planning)
    # =========================================================================

    @staticmethod
    def get_kapazitaetsplanung(
        betrieb: Optional[int] = None,
        tage: int = 7
    ) -> Dict[str, Any]:
        """
        Kapazitätsplanung Werkstatt: Offene Arbeit vs. verfügbare Kapazität.

        Berechnet:
        - Summe aller vorbereiteten/offenen Aufträge in AW
        - Anzahl anwesender Mechaniker (abzgl. Urlaub/Krank)
        - Verfügbare Tageskapazität in AW
        - Auslastungsgrad in Prozent

        Args:
            betrieb: Betrieb-ID (1=DEG, 3=LAN, None=alle). Hinweis: Betrieb 2 hat keine Werkstatt
            tage: Wie viele Tage Aufträge berücksichtigen (default: 7)

        Returns:
            Dict mit Kapazitäts- und Auslastungsdaten

        Example:
            >>> data = WerkstattData.get_kapazitaetsplanung(betrieb=1)
            >>> data['auslastung']['prozent_gesamt']
            85.5
        """
        heute = date.today()
        today_dow = datetime.now().weekday()  # 0=Montag, 4=Freitag

        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # =====================================================================
            # 1. VERFÜGBARE MECHANIKER MIT ARBEITSZEITEN
            # =====================================================================
            mechaniker_query = """
                WITH aktuelle_arbeitszeiten AS (
                    SELECT DISTINCT ON (employee_number, dayofweek)
                        employee_number, dayofweek, work_duration, worktime_start, worktime_end
                    FROM employees_worktimes
                    ORDER BY employee_number, dayofweek, validity_date DESC
                ),
                abwesende AS (
                    SELECT employee_number, reason, type
                    FROM absence_calendar
                    WHERE date = CURRENT_DATE
                )
                SELECT
                    eh.employee_number, eh.name, eh.subsidiary, eh.mechanic_number,
                    aw.work_duration, aw.worktime_start, aw.worktime_end,
                    ab.reason as abwesenheit_grund, ab.type as abwesenheit_typ,
                    CASE WHEN ab.employee_number IS NOT NULL THEN true ELSE false END as ist_abwesend
                FROM employees_history eh
                LEFT JOIN aktuelle_arbeitszeiten aw ON eh.employee_number = aw.employee_number AND aw.dayofweek = %s
                LEFT JOIN abwesende ab ON eh.employee_number = ab.employee_number
                WHERE eh.is_latest_record = true
                  AND eh.employee_number BETWEEN %s AND %s
                  AND eh.mechanic_number IS NOT NULL
                  AND eh.subsidiary > 0
                  AND (eh.leave_date IS NULL OR eh.leave_date > CURRENT_DATE)
            """

            params = [today_dow, MECHANIKER_RANGE_START, MECHANIKER_RANGE_END]
            if betrieb:
                mechaniker_query += " AND eh.subsidiary = %s"
                params.append(int(betrieb))
            mechaniker_query += " ORDER BY eh.subsidiary, eh.name"

            cursor.execute(mechaniker_query, params)
            mechaniker_raw = cursor.fetchall()

            # Mechaniker aufbereiten
            mechaniker = []
            total_stunden = 0
            total_stunden_verfuegbar = 0
            anwesend_count = 0
            abwesend_count = 0

            for m in mechaniker_raw:
                stunden = float(m['work_duration']) if m['work_duration'] else 8.0
                total_stunden += stunden

                if not m['ist_abwesend']:
                    total_stunden_verfuegbar += stunden
                    anwesend_count += 1
                else:
                    abwesend_count += 1

                mechaniker.append({
                    'employee_number': m['employee_number'],
                    'name': m['name'],
                    'betrieb': m['subsidiary'],
                    'betrieb_name': BETRIEB_NAMEN.get(m['subsidiary'], 'Unbekannt'),
                    'arbeitszeit_h': stunden,
                    'ist_abwesend': m['ist_abwesend'],
                    'abwesenheit_grund': m['abwesenheit_grund'] or m['abwesenheit_typ']
                })

            kapazitaet_aw = total_stunden_verfuegbar * 6  # 1h = 6 AW

            # =====================================================================
            # 2. OFFENE AUFTRÄGE MIT VORGABE-AW
            # =====================================================================
            auftraege_query = """
                SELECT
                    o.number as auftrag_nr, o.subsidiary as betrieb,
                    o.estimated_inbound_time as bringen, o.estimated_outbound_time as abholen,
                    o.urgency, v.license_plate as kennzeichen, m.description as marke,
                    COALESCE(cs.family_name, 'Unbekannt') as kunde,
                    COALESCE(SUM(l.time_units), 0) as vorgabe_aw,
                    COUNT(DISTINCT l.order_position) as anzahl_positionen
                FROM orders o
                LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
                LEFT JOIN makes m ON v.make_number = m.make_number
                LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
                LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
                WHERE o.has_open_positions = true
                  AND o.order_date >= CURRENT_DATE - INTERVAL '%s days'
            """

            auftraege_params = [tage]
            if betrieb:
                auftraege_query += " AND o.subsidiary = %s"
                auftraege_params.append(int(betrieb))

            auftraege_query += """
                GROUP BY o.number, o.subsidiary, o.estimated_inbound_time, o.estimated_outbound_time,
                         o.urgency, v.license_plate, m.description, cs.family_name
                HAVING COALESCE(SUM(l.time_units), 0) > 0
                ORDER BY o.estimated_inbound_time NULLS LAST
            """

            cursor.execute(auftraege_query, auftraege_params)
            auftraege_raw = cursor.fetchall()

            # Aufträge nach Kategorie sortieren
            auftraege_heute = []
            auftraege_geplant = []
            auftraege_ohne_termin = []
            total_aw = 0
            total_aw_heute = 0

            def format_dt(dt):
                return dt.strftime('%d.%m. %H:%M') if dt else None

            for a in auftraege_raw:
                aw = float(a['vorgabe_aw'])
                total_aw += aw

                auftrag = {
                    'auftrag_nr': a['auftrag_nr'],
                    'betrieb': a['betrieb'],
                    'betrieb_name': BETRIEB_NAMEN.get(a['betrieb'], 'Unbekannt'),
                    'kennzeichen': a['kennzeichen'],
                    'marke': a['marke'],
                    'kunde': a['kunde'],
                    'vorgabe_aw': aw,
                    'anzahl_positionen': a['anzahl_positionen'],
                    'bringen': format_dt(a['bringen']),
                    'abholen': format_dt(a['abholen']),
                    'dringend': a['urgency'] and a['urgency'] >= 4
                }

                if a['bringen'] and a['bringen'].date() == heute:
                    auftraege_heute.append(auftrag)
                    total_aw_heute += aw
                elif a['bringen']:
                    auftraege_geplant.append(auftrag)
                else:
                    auftraege_ohne_termin.append(auftrag)

            # =====================================================================
            # 3. KAPAZITÄT PRO BETRIEB
            # =====================================================================
            cursor.execute("""
                WITH aktuelle_arbeitszeiten AS (
                    SELECT DISTINCT ON (employee_number, dayofweek)
                        employee_number, dayofweek, work_duration
                    FROM employees_worktimes
                    ORDER BY employee_number, dayofweek, validity_date DESC
                ),
                abwesende AS (
                    SELECT employee_number FROM absence_calendar WHERE date = CURRENT_DATE
                )
                SELECT
                    eh.subsidiary,
                    COUNT(*) as anzahl_mechaniker,
                    COUNT(*) FILTER (WHERE ab.employee_number IS NULL) as anwesend,
                    COALESCE(SUM(COALESCE(aw.work_duration, 8)) FILTER (WHERE ab.employee_number IS NULL), 0) as stunden,
                    COALESCE(SUM(COALESCE(aw.work_duration, 8)) FILTER (WHERE ab.employee_number IS NULL), 0) * 6 as aw
                FROM employees_history eh
                LEFT JOIN aktuelle_arbeitszeiten aw ON eh.employee_number = aw.employee_number AND aw.dayofweek = %s
                LEFT JOIN abwesende ab ON eh.employee_number = ab.employee_number
                WHERE eh.is_latest_record = true
                  AND eh.employee_number BETWEEN %s AND %s
                  AND eh.mechanic_number IS NOT NULL
                  AND eh.subsidiary > 0
                  AND (eh.leave_date IS NULL OR eh.leave_date > CURRENT_DATE)
                GROUP BY eh.subsidiary
                ORDER BY eh.subsidiary
            """, [today_dow, MECHANIKER_RANGE_START, MECHANIKER_RANGE_END])

            betriebe = [
                {
                    'subsidiary': b['subsidiary'],
                    'name': BETRIEB_NAMEN.get(b['subsidiary'], f"Betrieb {b['subsidiary']}"),
                    'mechaniker_gesamt': b['anzahl_mechaniker'],
                    'mechaniker_anwesend': b['anwesend'],
                    'kapazitaet_h': float(b['stunden']),
                    'kapazitaet_aw': float(b['aw'])
                } for b in cursor.fetchall()
            ]

            # =====================================================================
            # 4. AUSLASTUNG BERECHNEN
            # =====================================================================
            if kapazitaet_aw > 0:
                auslastung_gesamt = (total_aw / kapazitaet_aw) * 100
                auslastung_heute = (total_aw_heute / kapazitaet_aw) * 100
                tage_arbeit = total_aw / kapazitaet_aw
            else:
                auslastung_gesamt = 0
                auslastung_heute = 0
                tage_arbeit = 0

            logger.info(f"WerkstattData.get_kapazitaetsplanung: {anwesend_count} MA, {round(kapazitaet_aw, 1)} AW Kapazität, {round(auslastung_gesamt, 1)}% Auslastung")

            wochentage = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']

            return {
                'datum': str(heute),
                'wochentag': wochentage[today_dow],
                'filter': {
                    'betrieb': betrieb,
                    'tage': tage
                },
                'kapazitaet': {
                    'mechaniker_gesamt': len(mechaniker),
                    'mechaniker_anwesend': anwesend_count,
                    'mechaniker_abwesend': abwesend_count,
                    'stunden_verfuegbar': total_stunden_verfuegbar,
                    'aw_verfuegbar': kapazitaet_aw,
                    'pro_betrieb': betriebe
                },
                'arbeit': {
                    'total_aw': round(total_aw, 1),
                    'total_stunden': round(total_aw / 6, 1),
                    'anzahl_auftraege': len(auftraege_raw),
                    'heute_aw': round(total_aw_heute, 1),
                    'heute_anzahl': len(auftraege_heute)
                },
                'auslastung': {
                    'prozent_gesamt': round(auslastung_gesamt, 1),
                    'prozent_heute': round(auslastung_heute, 1),
                    'tage_arbeit': round(tage_arbeit, 1),
                    'status': 'kritisch' if auslastung_gesamt > 150 else 'hoch' if auslastung_gesamt > 100 else 'normal' if auslastung_gesamt > 50 else 'niedrig'
                },
                'mechaniker': mechaniker,
                'auftraege_heute': auftraege_heute,
                'auftraege_geplant': auftraege_geplant[:20],
                'auftraege_ohne_termin': auftraege_ohne_termin[:20]
            }

    # =========================================================================
    # ANWESENHEIT (Attendance / Stempeluhr)
    # =========================================================================

    # Pausenzeiten - Mittagspause wird aus Laufzeit rausgerechnet
    PAUSE_START = time(12, 0)   # 12:00 Uhr
    PAUSE_ENDE = time(12, 45)    # 12:45 Uhr
    PAUSE_DAUER_MIN = 45         # 45 Minuten

    @staticmethod
    def berechne_netto_laufzeit_mit_pause(start_time: datetime) -> int:
        """
        Berechnet die Netto-Arbeitszeit abzüglich Mittagspause (12:00-13:00).
        Wenn ein Auftrag über die Mittagspause läuft, wird diese abgezogen.
        
        Args:
            start_time: Startzeitpunkt der Stempelung
            
        Returns:
            Netto-Laufzeit in Minuten (ohne Pause)
        """
        if not start_time:
            return 0
            
        jetzt = datetime.now()
        brutto_min = (jetzt - start_time).total_seconds() / 60
        
        # Pause heute
        heute = jetzt.date()
        pause_start_dt = datetime.combine(heute, WerkstattData.PAUSE_START)
        pause_ende_dt = datetime.combine(heute, WerkstattData.PAUSE_ENDE)
        
        # Prüfe ob Auftrag über Pause läuft
        if start_time < pause_start_dt and jetzt > pause_ende_dt:
            # Auftrag lief über komplette Pause → 60 min abziehen
            netto_min = brutto_min - WerkstattData.PAUSE_DAUER_MIN
        elif start_time >= pause_start_dt and start_time < pause_ende_dt:
            # Auftrag in Pause gestartet → Start auf Pause-Ende setzen
            netto_min = (jetzt - pause_ende_dt).total_seconds() / 60
            if netto_min < 0:
                netto_min = 0
        elif jetzt > pause_start_dt and jetzt <= pause_ende_dt and start_time < pause_start_dt:
            # Jetzt ist Pause, Auftrag lief vorher → nur Zeit bis Pause-Start
            netto_min = (pause_start_dt - start_time).total_seconds() / 60
        else:
            # Keine Pause-Überschneidung
            netto_min = brutto_min
        
        return int(max(0, netto_min))

    @staticmethod
    def get_stempeluhr(
        datum: Optional[date] = None,
        subsidiaries: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        LIVE Stempeluhr-Übersicht für Mechaniker.

        DUAL-FILTER für Cross-Betrieb Arbeit:
        - Bei subsidiary=1 oder 3: Filter nach MITARBEITER-Betrieb
        - Bei subsidiary=2 (Hyundai): Filter nach AUFTRAGS-Betrieb
          (weil Hyundai keine eigenen Mechaniker hat - die Stellantis-MA machen das!)

        Kategorien:
        - produktiv: Aktive Stempelungen auf Aufträgen
        - leerlauf: Stempelung auf Auftrag 31 (echter Leerlauf)
        - pausiert: Heute gearbeitet, aber gerade keine Stempelung
        - feierabend: Type 1 mit end_time (ausgestempelt)
        - abwesend: Aus absence_calendar

        Args:
            datum: Datum (default: heute)
            subsidiaries: Liste von Betrieb-IDs (optional)

        Returns:
            Dict mit Kategorien und Summary

        Example:
            >>> data = WerkstattData.get_stempeluhr(subsidiaries=[1, 2])
            >>> data['summary']['produktiv']
            8
        """
        if datum is None:
            datum = date.today()

        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # =====================================================================
            # 1. PRODUKTIVE STEMPELUNGEN (Auftrag > 31)
            # =====================================================================
            produktiv_query = """
                WITH aktuelle_stempelungen AS (
                    -- TAG 206: FIX - Deduplizierung auch für aktive Stempelungen
                    -- Problem: Wenn Mechaniker auf mehrere Positionen gleichzeitig stempelt,
                    -- werden diese mehrfach gezählt. Lösung: DISTINCT ON (employee_number, order_number, start_time)
                    SELECT DISTINCT ON (t.employee_number, t.order_number, t.start_time)
                        t.employee_number,
                        t.order_number,
                        t.start_time,
                        -- TAG 211: Pause stoppt die Zeit (12:00-12:45) - Zeit läuft während Pause nicht weiter
                        CASE
                            -- Stempelung startet vor Pause und läuft über Pause hinaus
                            WHEN t.start_time::time < TIME '12:00:00' AND LOCALTIME > TIME '12:45:00' THEN
                                EXTRACT(EPOCH FROM (TIME '12:00:00' - t.start_time::time))/60
                                + EXTRACT(EPOCH FROM (LOCALTIME - TIME '12:45:00'))/60
                            -- Stempelung startet in Pause (12:00-12:45)
                            WHEN t.start_time::time >= TIME '12:00:00' AND t.start_time::time < TIME '12:45:00' THEN
                                CASE
                                    WHEN LOCALTIME > TIME '12:45:00' THEN
                                        EXTRACT(EPOCH FROM (LOCALTIME - TIME '12:45:00'))/60
                                    ELSE 0
                                END
                            -- Stempelung startet vor Pause, jetzt ist in Pause
                            WHEN t.start_time::time < TIME '12:00:00' AND LOCALTIME >= TIME '12:00:00' AND LOCALTIME <= TIME '12:45:00' THEN
                                EXTRACT(EPOCH FROM (TIME '12:00:00' - t.start_time::time))/60
                            -- Normale Berechnung (keine Pause-Überschneidung)
                            ELSE
                                EXTRACT(EPOCH FROM (NOW() - t.start_time))/60
                        END as heute_session_min,
                        COALESCE((
                            SELECT SUM(dur) FROM (
                                -- TAG 194: Korrekte Deduplizierung nach Locosoft-Logik
                                -- DISTINCT ON (employee_number, order_number, start_time, end_time)
                                -- Verschiedene Positionen auf demselben Auftrag zur gleichen Zeit → 1× zählen
                                SELECT DISTINCT ON (employee_number, order_number, start_time, end_time) duration_minutes as dur
                                FROM times t2
                                WHERE t2.order_number = t.order_number
                                  AND t2.employee_number = t.employee_number
                                  AND t2.end_time IS NOT NULL
                                  AND t2.type = 2
                                  AND DATE(t2.start_time) = %s
                                ORDER BY employee_number, order_number, start_time, end_time
                            ) dedup
                        ), 0) as heute_abgeschlossen_min,
                        -- TAG 211: Pause stoppt die Zeit (12:00-12:45) - Zeit läuft während Pause nicht weiter
                        CASE
                            -- Stempelung startet vor Pause und läuft über Pause hinaus
                            WHEN t.start_time::time < TIME '12:00:00' AND LOCALTIME > TIME '12:45:00' THEN
                                EXTRACT(EPOCH FROM (TIME '12:00:00' - t.start_time::time))/60
                                + EXTRACT(EPOCH FROM (LOCALTIME - TIME '12:45:00'))/60
                            -- Stempelung startet in Pause (12:00-12:45)
                            WHEN t.start_time::time >= TIME '12:00:00' AND t.start_time::time < TIME '12:45:00' THEN
                                CASE
                                    WHEN LOCALTIME > TIME '12:45:00' THEN
                                        EXTRACT(EPOCH FROM (LOCALTIME - TIME '12:45:00'))/60
                                    ELSE 0
                                END
                            -- Stempelung startet vor Pause, jetzt ist in Pause
                            WHEN t.start_time::time < TIME '12:00:00' AND LOCALTIME >= TIME '12:00:00' AND LOCALTIME <= TIME '12:45:00' THEN
                                EXTRACT(EPOCH FROM (TIME '12:00:00' - t.start_time::time))/60
                            -- Normale Berechnung (keine Pause-Überschneidung)
                            ELSE
                                EXTRACT(EPOCH FROM (NOW() - t.start_time))/60
                        END
                        + COALESCE((
                            SELECT SUM(dur) FROM (
                                -- TAG 194: Korrekte Deduplizierung nach Locosoft-Logik
                                -- DISTINCT ON (employee_number, order_number, start_time, end_time)
                                -- Verschiedene Positionen auf demselben Auftrag zur gleichen Zeit → 1× zählen
                                SELECT DISTINCT ON (employee_number, order_number, start_time, end_time) duration_minutes as dur
                                FROM times t2
                                WHERE t2.order_number = t.order_number
                                  AND t2.employee_number = t.employee_number
                                  AND t2.end_time IS NOT NULL
                                  AND t2.type = 2
                                  AND DATE(t2.start_time) = %s  -- TAG 193: NUR HEUTE! (nicht alle Tage)
                                ORDER BY employee_number, order_number, start_time, end_time
                            ) dedup
                        ), 0) as laufzeit_min
                    FROM times t
                    WHERE t.end_time IS NULL
                      AND t.type = 2
                      AND t.order_number > 31
                      AND DATE(t.start_time) = %s
                      AND NOT EXISTS (
                          SELECT 1 FROM times t3
                          WHERE t3.employee_number = t.employee_number
                            AND t3.type = 2
                            AND t3.end_time IS NOT NULL
                            AND DATE(t3.start_time) = %s
                            AND t3.start_time > t.start_time
                      )
                    ORDER BY t.employee_number, t.order_number, t.start_time DESC
                )
                SELECT
                    a.employee_number,
                    eh.name as mechaniker,
                    eh.subsidiary as ma_betrieb,
                    o.subsidiary as auftrag_betrieb,
                    a.order_number,
                    a.start_time,
                    ROUND(a.laufzeit_min::numeric, 0) as laufzeit_min,
                    ROUND(a.heute_session_min::numeric, 0) as heute_session_min,
                    ROUND(a.heute_abgeschlossen_min::numeric, 0) as heute_abgeschlossen_min,
                    ROUND((a.heute_session_min + a.heute_abgeschlossen_min)::numeric, 0) as heute_gesamt_min,
                    COALESCE(l.vorgabe_aw, 0) as vorgabe_aw,
                    COALESCE(l.vorgabe_aw * 6, 0) as vorgabe_min,
                    l.auftrags_art,
                    o.order_taking_employee_no as sb_nr,
                    sb.name as sb_name,
                    v.license_plate as kennzeichen,
                    m.description as marke
                FROM aktuelle_stempelungen a
                LEFT JOIN employees_history eh ON a.employee_number = eh.employee_number
                    AND eh.is_latest_record = true
                LEFT JOIN orders o ON a.order_number = o.number
                LEFT JOIN employees_history sb ON o.order_taking_employee_no = sb.employee_number
                    AND sb.is_latest_record = true
                LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
                LEFT JOIN makes m ON v.make_number = m.make_number
                LEFT JOIN LATERAL (
                    -- KORRIGIERT: Verwende GESAMT-AW des Auftrags, nicht nur zugeordnete AW
                    -- Für Fortschrittsberechnung: Mechaniker arbeitet an ALLEN AW des Auftrags
                    SELECT SUM(time_units) as vorgabe_aw,
                           MAX(labour_type) as auftrags_art
                    FROM labours
                    WHERE order_number = a.order_number
                      AND time_units > 0
                ) l ON true
                WHERE 1=1
            """

            produktiv_params = [datum, datum, datum, datum]  # TAG 193: 4 Parameter (heute_abgeschlossen_min, laufzeit_min, start_time, NOT EXISTS)

            # DUAL-FILTER LOGIK
            if subsidiaries:
                if len(subsidiaries) == 1 and subsidiaries[0] == 2:
                    produktiv_query += " AND o.subsidiary = %s"
                    produktiv_params.append(subsidiaries[0])
                elif len(subsidiaries) == 1:
                    produktiv_query += " AND eh.subsidiary = %s"
                    produktiv_params.append(subsidiaries[0])
                else:
                    placeholders = ','.join(['%s'] * len(subsidiaries))
                    produktiv_query += f" AND eh.subsidiary IN ({placeholders})"
                    produktiv_params.extend(subsidiaries)

            produktiv_query += " ORDER BY a.start_time"
            cursor.execute(produktiv_query, produktiv_params)
            produktiv_raw = cursor.fetchall()

            # =====================================================================
            # 2. LEERLAUF-STEMPELUNGEN (TAG 194 - Dynamisch aus LEERLAUF_AUFTRAEGE_PRO_BETRIEB)
            # =====================================================================
            # SSOT: Verwende dynamische Leerlaufaufträge-Liste
            leerlauf_auftraege_alle = []
            for b_leerlauf in LEERLAUF_AUFTRAEGE_PRO_BETRIEB.values():
                leerlauf_auftraege_alle.extend(b_leerlauf)
            leerlauf_auftraege_alle = list(set(leerlauf_auftraege_alle))
            
            # Baue ARRAY-String für PostgreSQL
            leerlauf_array_str = ','.join(map(str, leerlauf_auftraege_alle))
            
            leerlauf_query = f"""
                WITH leerlauf_stempelungen AS (
                    SELECT DISTINCT ON (t.employee_number)
                        t.employee_number,
                        t.start_time,
                        EXTRACT(EPOCH FROM (NOW() - t.start_time))/60 as leerlauf_minuten
                    FROM times t
                    WHERE t.end_time IS NULL
                      AND t.type = 2
                      AND t.order_number = ANY(ARRAY[{leerlauf_array_str}])
                      AND DATE(t.start_time) = %s
                    ORDER BY t.employee_number, t.start_time DESC
                )
                SELECT
                    ls.employee_number,
                    eh.name,
                    eh.subsidiary,
                    ls.start_time as leerlauf_seit,
                    ROUND(ls.leerlauf_minuten::numeric, 0) as leerlauf_minuten
                FROM leerlauf_stempelungen ls
                JOIN employees_history eh ON ls.employee_number = eh.employee_number
                    AND eh.is_latest_record = true
                WHERE eh.leave_date IS NULL
                  AND eh.subsidiary > 0
            """

            leerlauf_params = [datum]
            if subsidiaries:
                if len(subsidiaries) == 1 and subsidiaries[0] == 2:
                    # Nur Hyundai: Keine Leerlauf-Anzeige
                    leerlauf_raw = []
                else:
                    if len(subsidiaries) == 1:
                        leerlauf_query += " AND eh.subsidiary = %s"
                        leerlauf_params.append(subsidiaries[0])
                    else:
                        placeholders = ','.join(['%s'] * len(subsidiaries))
                        leerlauf_query += f" AND eh.subsidiary IN ({placeholders})"
                        leerlauf_params.extend(subsidiaries)
                    leerlauf_query += " ORDER BY ls.leerlauf_minuten DESC"
                    cursor.execute(leerlauf_query, leerlauf_params)
                    leerlauf_raw = cursor.fetchall()
            else:
                leerlauf_query += " ORDER BY eh.subsidiary, ls.leerlauf_minuten DESC"
                cursor.execute(leerlauf_query, leerlauf_params)
                leerlauf_raw = cursor.fetchall()

            # Ausnahmen filtern (Azubis etc.)
            leerlauf_raw = [r for r in leerlauf_raw if r['employee_number'] not in MECHANIKER_EXCLUDE]

            # =====================================================================
            # 3. ABWESENDE MECHANIKER
            # =====================================================================
            abwesend_query = """
                SELECT
                    ac.employee_number,
                    eh.name,
                    eh.subsidiary,
                    ac.reason as grund
                FROM absence_calendar ac
                JOIN employees_history eh ON ac.employee_number = eh.employee_number
                    AND eh.is_latest_record = true
                WHERE ac.date = %s
                  AND ac.employee_number BETWEEN %s AND %s
                  AND eh.leave_date IS NULL
                  AND eh.subsidiary > 0
            """

            abwesend_params = [datum, MECHANIKER_RANGE_START, MECHANIKER_RANGE_END]
            if subsidiaries:
                if len(subsidiaries) == 1 and subsidiaries[0] == 2:
                    abwesend_raw = []
                else:
                    if len(subsidiaries) == 1:
                        abwesend_query += " AND eh.subsidiary = %s"
                        abwesend_params.append(subsidiaries[0])
                    else:
                        placeholders = ','.join(['%s'] * len(subsidiaries))
                        abwesend_query += f" AND eh.subsidiary IN ({placeholders})"
                        abwesend_params.extend(subsidiaries)
                    abwesend_query += " ORDER BY eh.name"
                    cursor.execute(abwesend_query, abwesend_params)
                    abwesend_raw = cursor.fetchall()
            else:
                abwesend_query += " ORDER BY eh.subsidiary, eh.name"
                cursor.execute(abwesend_query, abwesend_params)
                abwesend_raw = cursor.fetchall()

            # =====================================================================
            # 4. PAUSIERT / WARTET
            # =====================================================================
            pausiert_query = """
                WITH
                heute_gearbeitet AS (
                    SELECT DISTINCT employee_number
                    FROM times
                    WHERE type = 2 AND DATE(start_time) = %s AND order_number > 31
                ),
                aktuell_aktiv AS (
                    SELECT DISTINCT employee_number
                    FROM times t
                    WHERE t.end_time IS NULL AND t.type = 2 AND DATE(t.start_time) = %s
                      AND NOT EXISTS (
                          SELECT 1 FROM times t3
                          WHERE t3.employee_number = t.employee_number
                            AND t3.type = 2 AND t3.end_time IS NOT NULL
                            AND DATE(t3.start_time) = %s AND t3.start_time > t.start_time
                      )
                ),
                feierabend AS (
                    SELECT DISTINCT employee_number
                    FROM times
                    WHERE type = 1 AND DATE(start_time) = %s AND end_time IS NOT NULL
                ),
                abwesend_heute AS (
                    SELECT DISTINCT employee_number FROM absence_calendar WHERE date = %s
                ),
                letzte_stempelung AS (
                    SELECT DISTINCT ON (employee_number)
                        employee_number, order_number as letzter_auftrag, end_time as pausiert_seit
                    FROM times
                    WHERE type = 2 AND DATE(start_time) = %s AND end_time IS NOT NULL AND order_number > 31
                    ORDER BY employee_number, end_time DESC
                ),
                tagesarbeit AS (
                    SELECT employee_number, SUM(dur) as heute_min, COUNT(DISTINCT auftrag) as heute_auftraege
                    FROM (
                        SELECT DISTINCT ON (employee_number, start_time, end_time)
                            employee_number, order_number as auftrag, duration_minutes as dur
                        FROM times
                        WHERE type = 2 AND DATE(start_time) = %s AND end_time IS NOT NULL AND order_number > 31
                    ) dedup
                    GROUP BY employee_number
                )
                SELECT
                    hg.employee_number, eh.name, eh.subsidiary,
                    ls.letzter_auftrag, ls.pausiert_seit,
                    COALESCE(ta.heute_min, 0) as heute_min,
                    COALESCE(ta.heute_auftraege, 0) as heute_auftraege
                FROM heute_gearbeitet hg
                JOIN employees_history eh ON hg.employee_number = eh.employee_number AND eh.is_latest_record = true
                LEFT JOIN letzte_stempelung ls ON hg.employee_number = ls.employee_number
                LEFT JOIN tagesarbeit ta ON hg.employee_number = ta.employee_number
                WHERE hg.employee_number NOT IN (SELECT employee_number FROM aktuell_aktiv)
                  AND hg.employee_number NOT IN (SELECT employee_number FROM abwesend_heute)
                  AND hg.employee_number NOT IN (SELECT employee_number FROM feierabend)
                  AND eh.leave_date IS NULL AND eh.subsidiary > 0
            """

            pausiert_params = [datum, datum, datum, datum, datum, datum, datum]
            if subsidiaries:
                if len(subsidiaries) == 1 and subsidiaries[0] == 2:
                    pausiert_raw = []
                else:
                    if len(subsidiaries) == 1:
                        pausiert_query += " AND eh.subsidiary = %s ORDER BY ls.pausiert_seit DESC"
                        pausiert_params.append(subsidiaries[0])
                    else:
                        placeholders = ','.join(['%s'] * len(subsidiaries))
                        pausiert_query += f" AND eh.subsidiary IN ({placeholders}) ORDER BY ls.pausiert_seit DESC"
                        pausiert_params.extend(subsidiaries)
                    cursor.execute(pausiert_query, pausiert_params)
                    pausiert_raw = cursor.fetchall()
            else:
                pausiert_query += " ORDER BY eh.subsidiary, ls.pausiert_seit DESC"
                cursor.execute(pausiert_query, pausiert_params)
                pausiert_raw = cursor.fetchall()

            # =====================================================================
            # 5. FEIERABEND
            # =====================================================================
            feierabend_query = """
                WITH
                heute_gearbeitet AS (
                    SELECT DISTINCT employee_number FROM times
                    WHERE type = 2 AND DATE(start_time) = %s AND order_number > 31
                ),
                feierabend AS (
                    SELECT employee_number, MAX(end_time) as gegangen_um
                    FROM times
                    WHERE type = 1 AND DATE(start_time) = %s AND end_time IS NOT NULL
                    GROUP BY employee_number
                ),
                tagesarbeit AS (
                    SELECT employee_number, SUM(dur) as heute_min, COUNT(DISTINCT auftrag) as heute_auftraege
                    FROM (
                        SELECT DISTINCT ON (employee_number, start_time, end_time)
                            employee_number, order_number as auftrag, duration_minutes as dur
                        FROM times
                        WHERE type = 2 AND DATE(start_time) = %s AND end_time IS NOT NULL AND order_number > 31
                    ) dedup
                    GROUP BY employee_number
                )
                SELECT
                    hg.employee_number, eh.name, eh.subsidiary, f.gegangen_um,
                    COALESCE(ta.heute_min, 0) as heute_min,
                    COALESCE(ta.heute_auftraege, 0) as heute_auftraege
                FROM heute_gearbeitet hg
                JOIN feierabend f ON hg.employee_number = f.employee_number
                JOIN employees_history eh ON hg.employee_number = eh.employee_number AND eh.is_latest_record = true
                LEFT JOIN tagesarbeit ta ON hg.employee_number = ta.employee_number
                WHERE eh.leave_date IS NULL AND eh.subsidiary > 0
            """

            feierabend_params = [datum, datum, datum]
            if subsidiaries:
                if len(subsidiaries) == 1 and subsidiaries[0] == 2:
                    feierabend_raw = []
                else:
                    if len(subsidiaries) == 1:
                        feierabend_query += " AND eh.subsidiary = %s ORDER BY f.gegangen_um DESC"
                        feierabend_params.append(subsidiaries[0])
                    else:
                        placeholders = ','.join(['%s'] * len(subsidiaries))
                        feierabend_query += f" AND eh.subsidiary IN ({placeholders}) ORDER BY f.gegangen_um DESC"
                        feierabend_params.extend(subsidiaries)
                    cursor.execute(feierabend_query, feierabend_params)
                    feierabend_raw = cursor.fetchall()
            else:
                feierabend_query += " ORDER BY eh.subsidiary, f.gegangen_um DESC"
                cursor.execute(feierabend_query, feierabend_params)
                feierabend_raw = cursor.fetchall()

            # =====================================================================
            # FORMATIERUNG
            # =====================================================================
            def format_time(dt):
                return dt.strftime('%H:%M') if dt else None

            def format_datetime_str(dt):
                return dt.strftime('%d.%m.%Y %H:%M') if dt else None

            produktiv = []
            for r in produktiv_raw:
                vorgabe_min = float(r['vorgabe_min'] or 0)
                laufzeit = float(r['laufzeit_min'] or 0)
                fortschritt = int((laufzeit / vorgabe_min * 100) if vorgabe_min > 0 else 0)
                
                # TAG 211: Pause stoppt die Zeit (12:00-12:45) - Zeit läuft während Pause nicht weiter
                # Die SQL-Berechnung berücksichtigt die Pause bereits (laufzeit_min und heute_session_min)
                heute_session_min = int(r['heute_session_min'] or 0)
                heute_abgeschlossen_min = int(r['heute_abgeschlossen_min'] or 0)
                heute_gesamt_min = heute_session_min + heute_abgeschlossen_min

                produktiv.append({
                    'employee_number': r['employee_number'],
                    'name': r['mechaniker'] or f"MA {r['employee_number']}",
                    'betrieb': r['ma_betrieb'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['ma_betrieb'], 'Unbekannt'),
                    'auftrag_betrieb': r['auftrag_betrieb'],
                    'auftrag_betrieb_name': BETRIEB_NAMEN.get(r['auftrag_betrieb'], 'Unbekannt'),
                    'cross_betrieb': r['ma_betrieb'] != r['auftrag_betrieb'],
                    'order_number': r['order_number'],
                    'serviceberater': r['sb_name'] or f"MA {r['sb_nr']}" if r['sb_nr'] else None,
                    'serviceberater_nr': r['sb_nr'],
                    'kennzeichen': r['kennzeichen'],
                    'marke': r['marke'],
                    'start_time': format_datetime_str(r['start_time']),
                    'start_uhrzeit': format_time(r['start_time']),
                    'laufzeit_min': int(r['laufzeit_min'] or 0),
                    'heute_session_min': heute_session_min,  # TAG 194: Brutto-Zeit (wie Locosoft Realzeit)
                    'heute_abgeschlossen_min': heute_abgeschlossen_min,
                    'heute_gesamt_min': heute_gesamt_min,  # TAG 194: Brutto-Zeit (wie Locosoft Realzeit)
                    'vorgabe_aw': float(r['vorgabe_aw'] or 0),
                    'vorgabe_min': int(vorgabe_min),
                    'auftrags_art': r.get('auftrags_art') or '-',
                    'fortschritt_prozent': fortschritt,
                    'status': 'produktiv'
                })

            leerlauf = [
                {
                    'employee_number': r['employee_number'],
                    'name': r['name'] or f"MA {r['employee_number']}",
                    'betrieb': r['subsidiary'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], 'Unbekannt'),
                    'leerlauf_minuten': int(r['leerlauf_minuten']) if r['leerlauf_minuten'] else 0,
                    'leerlauf_seit': format_time(r['leerlauf_seit']),
                    'status': 'leerlauf',
                    'ist_echt': True
                } for r in leerlauf_raw
            ]

            abwesend = [
                {
                    'employee_number': r['employee_number'],
                    'name': r['name'] or f"MA {r['employee_number']}",
                    'betrieb': r['subsidiary'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], 'Unbekannt'),
                    'grund': r['grund'],
                    'status': 'abwesend'
                } for r in abwesend_raw
            ]

            pausiert = [
                {
                    'employee_number': r['employee_number'],
                    'name': r['name'] or f"MA {r['employee_number']}",
                    'betrieb': r['subsidiary'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], 'Unbekannt'),
                    'letzter_auftrag': r['letzter_auftrag'],
                    'pausiert_seit': format_time(r['pausiert_seit']),
                    'heute_min': int(r['heute_min'] or 0),
                    'heute_auftraege': int(r['heute_auftraege'] or 0),
                    'status': 'pausiert'
                } for r in pausiert_raw
            ]

            feierabend = [
                {
                    'employee_number': r['employee_number'],
                    'name': r['name'] or f"MA {r['employee_number']}",
                    'betrieb': r['subsidiary'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], 'Unbekannt'),
                    'gegangen_um': format_time(r['gegangen_um']),
                    'heute_min': int(r['heute_min'] or 0),
                    'heute_auftraege': int(r['heute_auftraege'] or 0),
                    'status': 'feierabend'
                } for r in feierabend_raw
            ]

            # Arbeitszeit-Check
            jetzt_zeit = datetime.now().time()
            ist_arbeitszeit = ARBEITSZEIT_START <= jetzt_zeit <= ARBEITSZEIT_ENDE

            logger.info(f"WerkstattData.get_stempeluhr: {len(produktiv)} produktiv, {len(leerlauf)} leerlauf, {len(pausiert)} pausiert, {len(feierabend)} feierabend")

            return {
                'success': True,  # TAG 204: Fix - success muss explizit auf True gesetzt werden
                'datum': str(datum),
                'subsidiaries': subsidiaries,
                'ist_arbeitszeit': ist_arbeitszeit,
                'aktive_mechaniker': produktiv,
                'leerlauf_mechaniker': leerlauf if ist_arbeitszeit else [],
                'abwesend_mechaniker': abwesend,
                'pausiert_mechaniker': pausiert,
                'feierabend_mechaniker': feierabend,
                'summary': {
                    'produktiv': len(produktiv),
                    'leerlauf': len(leerlauf) if ist_arbeitszeit else 0,
                    'pausiert': len(pausiert),
                    'feierabend': len(feierabend),
                    'abwesend': len(abwesend),
                    'gesamt': len(produktiv) + len(leerlauf) + len(pausiert) + len(feierabend) + len(abwesend)
                }
            }

    # =========================================================================
    # TAGESBERICHT (Daily Control Report)
    # =========================================================================

    @staticmethod
    def get_tagesbericht(
        datum: Optional[date] = None,
        betrieb: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Tagesbericht zur Kontrolle: Stempelungen, Zuweisungen, Überschreitungen.

        Prüft:
        1. Stempelungen OHNE Vorgabe-AW (fehlende Arbeitszuweisung)
        2. Falsche Mechaniker-Zuordnung (gestempelt != zugewiesen)
        3. Überschrittene Vorgabezeiten (>100%)

        Args:
            datum: Datum für den Bericht (default: heute)
            betrieb: Betrieb-ID (1=DEG, 3=LAN, None=alle)

        Returns:
            Dict mit 'ohne_vorgabe', 'falsche_zuweisung', 'ueberschritten', 'alle_aktiv'

        Example:
            >>> data = WerkstattData.get_tagesbericht(betrieb=1)
            >>> data['summary']['ohne_vorgabe']
            3
        """
        if datum is None:
            datum = date.today()

        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 1. STEMPELUNG OHNE VORGABE
            query1 = """
                WITH stempelungen AS (
                    SELECT DISTINCT ON (employee_number)
                        employee_number, order_number, start_time,
                        EXTRACT(EPOCH FROM (NOW() - start_time))/60
                        + COALESCE((
                            SELECT SUM(duration_minutes)
                            FROM times t2
                            WHERE t2.order_number = times.order_number
                              AND t2.employee_number = times.employee_number
                              AND t2.end_time IS NOT NULL
                              AND t2.type = 2
                        ), 0) as laufzeit_min
                    FROM times
                    WHERE type = 2 AND DATE(start_time) = %s
                      AND end_time IS NULL
                    ORDER BY employee_number, start_time DESC
                ),
                mechaniker_aw AS (
                    SELECT order_number, mechanic_no, SUM(time_units) as zugewiesene_aw
                    FROM labours
                    WHERE mechanic_no IS NOT NULL
                    GROUP BY order_number, mechanic_no
                )
                SELECT
                    s.employee_number,
                    eh.name as mechaniker,
                    eh.subsidiary,
                    s.order_number,
                    s.start_time,
                    ROUND(s.laufzeit_min::numeric, 0) as gestempelt_min,
                    COALESCE(m.zugewiesene_aw, 0) as zugewiesene_aw
                FROM stempelungen s
                JOIN employees_history eh ON s.employee_number = eh.employee_number AND eh.is_latest_record = true
                LEFT JOIN mechaniker_aw m ON s.order_number = m.order_number AND s.employee_number = m.mechanic_no
                WHERE COALESCE(m.zugewiesene_aw, 0) = 0
            """
            params1 = [datum]
            if betrieb:
                query1 += " AND eh.subsidiary = %s"
                params1.append(int(betrieb))
            query1 += " ORDER BY s.laufzeit_min DESC"

            cursor.execute(query1, params1)
            ohne_vorgabe_raw = cursor.fetchall()

            # 2. FALSCHE MECHANIKER-ZUORDNUNG
            query2 = """
                WITH stempelungen AS (
                    SELECT DISTINCT ON (employee_number)
                        employee_number, order_number
                    FROM times
                    WHERE type = 2 AND DATE(start_time) = %s AND end_time IS NULL
                    ORDER BY employee_number, start_time DESC
                ),
                auftrags_aw AS (
                    SELECT order_number, mechanic_no, SUM(time_units) as aw
                    FROM labours
                    WHERE time_units > 0 AND mechanic_no IS NOT NULL
                    GROUP BY order_number, mechanic_no
                )
                SELECT
                    s.order_number,
                    s.employee_number as gestempelt_nr,
                    eh1.name as gestempelt_name,
                    eh1.subsidiary,
                    a.mechanic_no as zugewiesen_nr,
                    eh2.name as zugewiesen_name,
                    a.aw as zugewiesene_aw
                FROM stempelungen s
                JOIN auftrags_aw a ON s.order_number = a.order_number AND s.employee_number != a.mechanic_no
                JOIN employees_history eh1 ON s.employee_number = eh1.employee_number AND eh1.is_latest_record = true
                JOIN employees_history eh2 ON a.mechanic_no = eh2.employee_number AND eh2.is_latest_record = true
                WHERE a.aw > 0
            """
            params2 = [datum]
            if betrieb:
                query2 += " AND eh1.subsidiary = %s"
                params2.append(int(betrieb))
            query2 += " ORDER BY a.aw DESC"

            cursor.execute(query2, params2)
            falsche_zuweisung_raw = cursor.fetchall()

            # 3. AKTUELLE STEMPELUNGEN MIT VORGABE-CHECK
            query3 = """
                WITH aktive_stempelungen AS (
                    SELECT DISTINCT ON (employee_number)
                        employee_number, order_number, start_time
                    FROM times
                    WHERE type = 2
                      AND DATE(start_time) = %s
                      AND end_time IS NULL
                    ORDER BY employee_number, start_time DESC
                ),
                vorgaben AS (
                    SELECT order_number, mechanic_no, SUM(time_units) as vorgabe_aw
                    FROM labours
                    WHERE mechanic_no IS NOT NULL AND time_units > 0
                    GROUP BY order_number, mechanic_no
                )
                SELECT
                    s.employee_number,
                    eh.name as mechaniker,
                    eh.subsidiary,
                    s.order_number,
                    s.start_time,
                    COALESCE(v.vorgabe_aw, 0) as vorgabe_aw
                FROM aktive_stempelungen s
                LEFT JOIN vorgaben v ON s.order_number = v.order_number AND s.employee_number = v.mechanic_no
                JOIN employees_history eh ON s.employee_number = eh.employee_number AND eh.is_latest_record = true
                WHERE 1=1
            """
            params3 = [datum]
            if betrieb:
                query3 += " AND eh.subsidiary = %s"
                params3.append(int(betrieb))
            query3 += " ORDER BY s.start_time"

            cursor.execute(query3, params3)
            aktive_raw = cursor.fetchall()

            # Netto-Laufzeit berechnen und Überschreitungen filtern
            def berechne_netto_laufzeit(start_time) -> int:
                """Berechnet Netto-Laufzeit abzgl. Pausen"""
                if not start_time:
                    return 0
                jetzt = datetime.now()
                gesamt_min = (jetzt - start_time).total_seconds() / 60

                # Mittagspause abziehen (12:00-12:30)
                pause_start = start_time.replace(hour=12, minute=0, second=0)
                pause_ende = start_time.replace(hour=12, minute=30, second=0)

                if start_time < pause_start and jetzt > pause_ende:
                    gesamt_min -= 30
                elif start_time < pause_start and pause_start < jetzt < pause_ende:
                    gesamt_min -= (jetzt - pause_start).total_seconds() / 60
                elif pause_start < start_time < pause_ende and jetzt > pause_ende:
                    gesamt_min -= (pause_ende - start_time).total_seconds() / 60

                return max(0, int(gesamt_min))

            ueberschritten = []
            alle_aktiv = []

            for r in aktive_raw:
                ist_min = berechne_netto_laufzeit(r['start_time']) if r['start_time'] else 0
                vorgabe_min = int(float(r['vorgabe_aw'] or 0) * 6)
                prozent = int(ist_min / vorgabe_min * 100) if vorgabe_min > 0 else 0

                eintrag = {
                    'employee_number': r['employee_number'],
                    'mechaniker': r['mechaniker'],
                    'betrieb': r['subsidiary'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], 'Unbekannt'),
                    'order_number': r['order_number'],
                    'start_uhrzeit': r['start_time'].strftime('%H:%M') if r['start_time'] else None,
                    'ist_min': ist_min,
                    'vorgabe_min': vorgabe_min,
                    'vorgabe_aw': float(r['vorgabe_aw'] or 0),
                    'prozent': prozent
                }

                alle_aktiv.append(eintrag)

                if prozent >= 100:
                    ueberschritten.append(eintrag)

            # Formatieren
            ohne_vorgabe = [
                {
                    'employee_number': r['employee_number'],
                    'mechaniker': r['mechaniker'],
                    'betrieb': r['subsidiary'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], 'Unbekannt'),
                    'order_number': r['order_number'],
                    'start_uhrzeit': r['start_time'].strftime('%H:%M') if r['start_time'] else None,
                    'gestempelt_min': int(r['gestempelt_min'] or 0),
                    'zugewiesene_aw': float(r['zugewiesene_aw'] or 0)
                } for r in ohne_vorgabe_raw
            ]

            falsche_zuweisung = [
                {
                    'order_number': r['order_number'],
                    'betrieb': r['subsidiary'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], 'Unbekannt'),
                    'gestempelt_nr': r['gestempelt_nr'],
                    'gestempelt_name': r['gestempelt_name'],
                    'zugewiesen_nr': r['zugewiesen_nr'],
                    'zugewiesen_name': r['zugewiesen_name'],
                    'zugewiesene_aw': float(r['zugewiesene_aw'] or 0)
                } for r in falsche_zuweisung_raw
            ]

            logger.info(f"WerkstattData.get_tagesbericht: {len(ohne_vorgabe)} ohne Vorgabe, {len(falsche_zuweisung)} falsch zugewiesen, {len(ueberschritten)} überschritten")

            return {
                'datum': str(datum),
                'filter': {'betrieb': betrieb},
                'ohne_vorgabe': ohne_vorgabe,
                'falsche_zuweisung': falsche_zuweisung,
                'ueberschritten': sorted(ueberschritten, key=lambda x: x['prozent'], reverse=True),
                'alle_aktiv': alle_aktiv,
                'summary': {
                    'ohne_vorgabe': len(ohne_vorgabe),
                    'falsche_zuweisung': len(falsche_zuweisung),
                    'ueberschritten': len(ueberschritten),
                    'aktiv_gesamt': len(alle_aktiv)
                }
            }

    # =========================================================================
    # AUFTRAG DETAIL (Order Details)
    # =========================================================================

    @staticmethod
    def get_auftrag_detail(auftrag_nr: int) -> Dict[str, Any]:
        """
        Detailansicht eines einzelnen Auftrags mit allen Positionen und Teilen.

        Args:
            auftrag_nr: Auftragsnummer

        Returns:
            Dict mit 'auftrag', 'positionen', 'teile' und Summen

        Example:
            >>> data = WerkstattData.get_auftrag_detail(12345)
            >>> data['auftrag']['kennzeichen']
            'DEG-XX 123'
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Auftrag-Kopfdaten
            cursor.execute("""
                SELECT
                    o.number as auftrag_nr,
                    o.subsidiary as betrieb,
                    o.order_date,
                    o.order_taking_employee_no as serviceberater_nr,
                    eh.name as serviceberater_name,
                    o.vehicle_number,
                    v.license_plate as kennzeichen,
                    v.vin,
                    m.description as marke,
                    mo.description as modell,
                    v.mileage_km as km_stand,
                    COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name) as kunde,
                    cs.customer_number as kunden_nr,
                    o.urgency,
                    o.has_open_positions,
                    o.has_closed_positions,
                    o.estimated_inbound_time,
                    o.estimated_outbound_time
                FROM orders o
                LEFT JOIN employees_history eh ON o.order_taking_employee_no = eh.employee_number
                    AND eh.is_latest_record = true
                LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
                LEFT JOIN makes m ON v.make_number = m.make_number
                LEFT JOIN models mo ON v.make_number = mo.make_number AND v.model_code = mo.model_code
                LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
                WHERE o.number = %s
            """, [auftrag_nr])

            auftrag = cursor.fetchone()

            if not auftrag:
                return {
                    'success': False,
                    'error': f'Auftrag {auftrag_nr} nicht gefunden'
                }

            # Arbeitspositionen (Labours)
            cursor.execute("""
                SELECT
                    l.order_position,
                    l.mechanic_no,
                    mech.name as mechaniker_name,
                    l.time_units as vorgabe_aw,
                    l.text_line as beschreibung,
                    l.is_invoiced as abgerechnet,
                    l.charge_type,
                    l.labour_type
                FROM labours l
                LEFT JOIN employees_history mech ON l.mechanic_no = mech.employee_number
                    AND mech.is_latest_record = true
                WHERE l.order_number = %s
                ORDER BY l.order_position, l.order_position_line
            """, [auftrag_nr])

            positionen = cursor.fetchall()

            # Teile
            cursor.execute("""
                SELECT
                    p.order_position,
                    p.part_number as teilenummer,
                    p.text_line as bezeichnung,
                    p.amount as menge,
                    p.sum as betrag,
                    p.is_invoiced as abgerechnet
                FROM parts p
                WHERE p.order_number = %s
                ORDER BY p.order_position
            """, [auftrag_nr])

            teile = cursor.fetchall()

            # Gestempelte Zeit aus times-Tabelle holen
            cursor.execute("""
                SELECT COALESCE(SUM(minuten), 0) as gestempelt_min
                FROM (
                    SELECT DISTINCT ON (order_number, employee_number, start_time, end_time)
                        EXTRACT(EPOCH FROM (COALESCE(end_time, NOW()) - start_time)) / 60 as minuten
                    FROM times
                    WHERE order_number = %s
                      AND type = 2
                ) dedup
            """, [auftrag_nr])
            
            gestempelt_result = cursor.fetchone()
            gestempelt_min = int(gestempelt_result['gestempelt_min'] or 0) if gestempelt_result else 0

            # Summen berechnen
            total_aw = sum(float(p['vorgabe_aw'] or 0) for p in positionen)
            fakturiert_aw = sum(float(p['vorgabe_aw'] or 0) for p in positionen if p['abgerechnet'])
            offen_aw = sum(float(p['vorgabe_aw'] or 0) for p in positionen if not p['abgerechnet'])
            zugeordnet_aw = sum(float(p['vorgabe_aw'] or 0) for p in positionen if p['mechanic_no'])
            nicht_zugeordnet_aw = sum(float(p['vorgabe_aw'] or 0) for p in positionen if not p['mechanic_no'])
            total_teile = sum(float(p['betrag'] or 0) for p in teile)
            
            # Garantie-Erkennung: Prüfe Positionen und Rechnungen
            ist_garantie = False
            haupt_charge_type = None
            haupt_labour_type = None
            invoice_type = None
            
            # Prüfe Positionen
            for p in positionen:
                ct = p.get('charge_type')
                lt = p.get('labour_type')
                if ct == 60 or lt in ['G', 'GS']:
                    ist_garantie = True
                    if not haupt_charge_type:
                        haupt_charge_type = ct
                        haupt_labour_type = lt
            
            # Prüfe Rechnungen (falls vorhanden)
            if not ist_garantie:
                cursor.execute("""
                    SELECT DISTINCT invoice_type
                    FROM invoices
                    WHERE order_number = %s
                      AND is_canceled = false
                    LIMIT 1
                """, [auftrag_nr])
                invoice_result = cursor.fetchone()
                if invoice_result and invoice_result.get('invoice_type') == 6:
                    ist_garantie = True
                    invoice_type = 6

            def format_dt(dt):
                return dt.strftime('%d.%m.%Y %H:%M') if dt else None

            logger.info(f"WerkstattData.get_auftrag_detail: Auftrag {auftrag_nr}, {len(positionen)} Positionen, {len(teile)} Teile")

            return {
                'success': True,
                'auftrag': {
                    'auftrag_nr': auftrag['auftrag_nr'],
                    'betrieb': auftrag['betrieb'],
                    'betrieb_name': BETRIEB_NAMEN.get(auftrag['betrieb'], 'Unbekannt'),
                    'datum': format_dt(auftrag['order_date']),
                    'serviceberater': auftrag['serviceberater_name'],
                    'serviceberater_nr': auftrag['serviceberater_nr'],
                    'fahrzeug': {
                        'kennzeichen': auftrag['kennzeichen'],
                        'vin': auftrag['vin'],
                        'marke': auftrag['marke'],
                        'modell': auftrag['modell'],
                        'km_stand': auftrag['km_stand']
                    },
                    'kunde': auftrag['kunde'],
                    'kunden_nr': auftrag['kunden_nr'],
                    'status': {
                        'ist_offen': auftrag['has_open_positions'],
                        'hat_abgeschlossene': auftrag['has_closed_positions'],
                        'dringlichkeit': auftrag['urgency']
                    },
                    'garantie': {
                        'ist_garantie': ist_garantie,
                        'charge_type': haupt_charge_type,
                        'labour_type': haupt_labour_type,
                        'invoice_type': invoice_type
                    },
                    'planung': {
                        'eingang': format_dt(auftrag['estimated_inbound_time']),
                        'fertig': format_dt(auftrag['estimated_outbound_time'])
                    },
                    'summen': {
                        'total_aw': total_aw,
                        'fakturiert_aw': fakturiert_aw,
                        'offen_aw': offen_aw,
                        'zugeordnet_aw': zugeordnet_aw,
                        'nicht_zugeordnet_aw': nicht_zugeordnet_aw,
                        'vollstaendig_abgerechnet': offen_aw == 0,
                        'vollstaendig_zugeordnet': nicht_zugeordnet_aw == 0,
                        'anzahl_positionen': len(positionen),
                        'teile_betrag': total_teile,
                        'gestempelt_min': gestempelt_min
                    },
                    'gestempelt_min': gestempelt_min
                },
                'positionen': [
                    {
                        'position': p['order_position'],
                        'mechaniker_nr': p['mechanic_no'],
                        'mechaniker': p['mechaniker_name'] or (f"MA {p['mechanic_no']}" if p['mechanic_no'] else 'Nicht zugeordnet'),
                        'vorgabe_aw': float(p['vorgabe_aw'] or 0),
                        'beschreibung': p['beschreibung'],
                        'abgerechnet': p['abgerechnet'],
                        'typ': p['labour_type']
                    } for p in positionen
                ],
                'teile': [
                    {
                        'position': t['order_position'],
                        'teilenummer': t['teilenummer'],
                        'bezeichnung': t['bezeichnung'],
                        'menge': float(t['menge'] or 0),
                        'betrag': float(t['betrag'] or 0),
                        'abgerechnet': t['abgerechnet']
                    } for t in teile
                ]
            }

    # =========================================================================
    # PROBLEMFÄLLE (Problem Cases / Low Performance)
    # =========================================================================

    @staticmethod
    def get_problemfaelle(
        zeitraum: str = 'monat',
        betrieb: Optional[int] = None,
        max_lg: float = 70.0,
        min_stempelzeit: int = 30,
        von: Optional[str] = None,
        bis: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Problemfälle: Aufträge mit niedrigem Leistungsgrad.

        Zeigt Aufträge wo die Stempelzeit deutlich über der Vorgabezeit liegt.

        Args:
            zeitraum: heute|woche|monat|vormonat|quartal|jahr|custom
            betrieb: Betrieb-ID (optional)
            max_lg: Maximaler Leistungsgrad (default: 70%)
            min_stempelzeit: Minimale Stempelzeit in Minuten (default: 30)
            von/bis: Für zeitraum='custom'

        Returns:
            Dict mit 'auftraege' und 'statistik'

        Example:
            >>> data = WerkstattData.get_problemfaelle(zeitraum='monat', max_lg=50)
            >>> data['statistik']['durchschnitt_lg']
            42.5
        """
        heute = date.today()

        # Datumsbereich berechnen
        if zeitraum == 'custom' and von and bis:
            datum_von, datum_bis = von, bis
        elif zeitraum == 'heute':
            datum_von = datum_bis = heute.isoformat()
        elif zeitraum == 'woche':
            datum_von = (heute - timedelta(days=heute.weekday())).isoformat()
            datum_bis = heute.isoformat()
        elif zeitraum == 'monat':
            datum_von = heute.replace(day=1).isoformat()
            datum_bis = heute.isoformat()
        elif zeitraum == 'vormonat':
            erster_aktuell = heute.replace(day=1)
            letzter_vormonat = erster_aktuell - timedelta(days=1)
            datum_von = letzter_vormonat.replace(day=1).isoformat()
            datum_bis = letzter_vormonat.isoformat()
        elif zeitraum == 'quartal':
            quartal_monat = ((heute.month - 1) // 3) * 3 + 1
            datum_von = heute.replace(month=quartal_monat, day=1).isoformat()
            datum_bis = heute.isoformat()
        elif zeitraum == 'jahr':
            datum_von = heute.replace(month=1, day=1).isoformat()
            datum_bis = heute.isoformat()
        else:
            datum_von = heute.replace(day=1).isoformat()
            datum_bis = heute.isoformat()

        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                WITH
                rechnungen AS (
                    SELECT DISTINCT
                        i.order_number,
                        i.invoice_date,
                        i.subsidiary
                    FROM invoices i
                    WHERE DATE(i.invoice_date) BETWEEN %s AND %s
                      AND i.invoice_type IN (2, 4, 5, 6)
                      AND i.is_canceled = false
                      AND i.job_amount_net > 0
                ),
                labour_summen AS (
                    SELECT
                        l.order_number,
                        SUM(l.time_units) as gesamt_aw,
                        SUM(CASE WHEN l.is_invoiced THEN l.time_units ELSE 0 END) as fakturiert_aw,
                        SUM(CASE WHEN NOT l.is_invoiced THEN l.time_units ELSE 0 END) as offen_aw,
                        SUM(CASE WHEN l.mechanic_no IS NOT NULL THEN l.time_units ELSE 0 END) as zugeordnet_aw,
                        SUM(CASE WHEN l.mechanic_no IS NULL THEN l.time_units ELSE 0 END) as nicht_zugeordnet_aw,
                        STRING_AGG(DISTINCT eh.name, ', ') as mechaniker_namen
                    FROM labours l
                    LEFT JOIN employees_history eh ON l.mechanic_no = eh.employee_number
                        AND eh.is_latest_record = true
                    WHERE l.order_number IN (SELECT order_number FROM rechnungen)
                    GROUP BY l.order_number
                ),
                stempel_summen AS (
                    SELECT
                        order_number,
                        SUM(minuten) as gestempelt_min
                    FROM (
                        SELECT DISTINCT ON (order_number, employee_number, start_time, end_time)
                            order_number,
                            EXTRACT(EPOCH FROM (COALESCE(end_time, NOW()) - start_time)) / 60 as minuten
                        FROM times
                        WHERE type = 2
                          AND order_number IN (SELECT order_number FROM rechnungen)
                    ) dedup
                    GROUP BY order_number
                ),
                details AS (
                    SELECT
                        o.number as order_number,
                        o.order_date,
                        o.subsidiary,
                        v.license_plate as kennzeichen
                    FROM orders o
                    LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
                    WHERE o.number IN (SELECT order_number FROM rechnungen)
                )
                SELECT
                    r.invoice_date as datum,
                    r.order_number as auftrags_nr,
                    d.kennzeichen,
                    l.mechaniker_namen as mechaniker_name,
                    ROUND(COALESCE(l.gesamt_aw, 0)::numeric, 1) as vorgabe_aw,
                    ROUND(COALESCE(l.fakturiert_aw, 0)::numeric, 1) as fakturiert_aw,
                    ROUND(COALESCE(l.offen_aw, 0)::numeric, 1) as offen_aw,
                    ROUND(COALESCE(l.zugeordnet_aw, 0)::numeric, 1) as zugeordnet_aw,
                    ROUND(COALESCE(l.nicht_zugeordnet_aw, 0)::numeric, 1) as nicht_zugeordnet_aw,
                    ROUND(COALESCE(s.gestempelt_min, 0)::numeric, 0) as gestempelt_min,
                    CASE
                        WHEN s.gestempelt_min > 0 AND l.gesamt_aw > 0
                        THEN ROUND((l.gesamt_aw * 6.0 / s.gestempelt_min * 100)::numeric, 1)
                        ELSE NULL
                    END as leistungsgrad,
                    COALESCE(d.subsidiary, r.subsidiary) as betrieb_nr,
                    CASE WHEN l.offen_aw > 0 THEN false ELSE true END as vollstaendig_fakturiert,
                    CASE WHEN l.nicht_zugeordnet_aw > 0 THEN false ELSE true END as vollstaendig_zugeordnet
                FROM rechnungen r
                LEFT JOIN labour_summen l ON r.order_number = l.order_number
                LEFT JOIN stempel_summen s ON r.order_number = s.order_number
                LEFT JOIN details d ON r.order_number = d.order_number
                WHERE s.gestempelt_min >= %s
                  AND l.gesamt_aw > 0
                  AND (l.gesamt_aw * 6.0 / NULLIF(s.gestempelt_min, 0) * 100) < %s
            """

            params = [datum_von, datum_bis, min_stempelzeit, max_lg]

            if betrieb:
                query += " AND COALESCE(d.subsidiary, r.subsidiary) = %s"
                params.append(int(betrieb))

            query += " ORDER BY leistungsgrad ASC NULLS LAST LIMIT 200"

            cursor.execute(query, params)
            auftraege_raw = cursor.fetchall()

            # Aufbereiten
            auftraege = []
            total_verlust_aw = 0
            total_lg = 0

            for a in auftraege_raw:
                betrieb_nr = a['betrieb_nr']
                auftraege.append({
                    'datum': a['datum'].strftime('%d.%m.%Y') if a['datum'] else None,
                    'auftrags_nr': a['auftrags_nr'],
                    'kennzeichen': a['kennzeichen'],
                    'mechaniker_name': a['mechaniker_name'],
                    'vorgabe_aw': float(a['vorgabe_aw'] or 0),
                    'fakturiert_aw': float(a['fakturiert_aw'] or 0),
                    'offen_aw': float(a['offen_aw'] or 0),
                    'zugeordnet_aw': float(a['zugeordnet_aw'] or 0),
                    'nicht_zugeordnet_aw': float(a['nicht_zugeordnet_aw'] or 0),
                    'gestempelt_min': int(a['gestempelt_min'] or 0),
                    'leistungsgrad': float(a['leistungsgrad']) if a['leistungsgrad'] else None,
                    'betrieb_nr': betrieb_nr,
                    'betrieb_name': BETRIEB_NAMEN.get(betrieb_nr, 'Unbekannt'),
                    'vollstaendig_fakturiert': a['vollstaendig_fakturiert'],
                    'vollstaendig_zugeordnet': a['vollstaendig_zugeordnet']
                })

                if a.get('leistungsgrad') and a.get('gestempelt_min') and a.get('vorgabe_aw'):
                    vorgabe_min = float(a['vorgabe_aw']) * 6
                    verlust_min = float(a['gestempelt_min']) - vorgabe_min
                    if verlust_min > 0:
                        total_verlust_aw += verlust_min / 6
                    total_lg += float(a['leistungsgrad'])

            avg_lg = total_lg / len(auftraege) if auftraege else 0
            unvollst_fakturiert = sum(1 for a in auftraege if not a.get('vollstaendig_fakturiert', True))
            unvollst_zugeordnet = sum(1 for a in auftraege if not a.get('vollstaendig_zugeordnet', True))

            logger.info(f"WerkstattData.get_problemfaelle: {len(auftraege)} Problemfälle, Ø LG={round(avg_lg, 1)}%")

            return {
                'auftraege': auftraege,
                'anzahl': len(auftraege),
                'statistik': {
                    'durchschnitt_lg': round(avg_lg, 1),
                    'total_verlust_aw': round(total_verlust_aw, 1),
                    'unvollstaendig_fakturiert': unvollst_fakturiert,
                    'unvollstaendig_zugeordnet': unvollst_zugeordnet
                },
                'filter': {
                    'zeitraum': zeitraum,
                    'datum_von': datum_von,
                    'datum_bis': datum_bis,
                    'max_lg': max_lg,
                    'min_stempelzeit': min_stempelzeit,
                    'betrieb': betrieb
                }
            }

    # =========================================================================
    # NACHKALKULATION - Vorgabe vs. Gestempelt vs. Verrechnet
    # =========================================================================

    # =========================================================================
    # FINANZ-KPIS (Revenue / Costs)
    # =========================================================================

    @staticmethod
    def get_finanz_kpis(
        von: Optional[date] = None,
        bis: Optional[date] = None,
        betrieb: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Holt Finanz-KPIs für Werkstatt aus BWA und Locosoft.
        
        WICHTIG: Nutzt BWA-Daten (loco_journal_accountings) für Erlöse
        und Locosoft-Daten für offene Posten.
        
        Args:
            von: Startdatum (default: Monatserster)
            bis: Enddatum (default: heute)
            betrieb: Betrieb-ID (1=DEG, 2=HYU, 3=LAN, None=alle)
        
        Returns:
            Dict mit Finanz-KPIs:
            - serviceerlöse_gesamt: Serviceerlöse (840000-849999)
            - lohnerlöse: Lohnerlöse (840000-849999)
            - et_erlöse: ET Erlöse (830000-839999)
            - offener_lohn: Offene Rechnungen (Locosoft)
            - offene_teile: Offene Teile-Bestellungen (Locosoft)
            - betriebe_erlöse: Liste mit Erlösen pro Betrieb
        
        Erstellt: TAG 171 - Phase 1: Finanz-KPIs (SSOT)
        """
        from datetime import datetime, timedelta
        from api.db_utils import db_session, row_to_dict
        from api.db_connection import convert_placeholders
        from api.controlling_api import build_firma_standort_filter
        
        # Default Zeitraum: Aktueller Monat
        if von is None:
            von = date.today().replace(day=1)
        if bis is None:
            bis = date.today()
        
        datum_von = von.isoformat()
        datum_bis = bis.isoformat()
        datum_bis_exklusiv = (datetime.strptime(datum_bis, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Standort-Filter bauen (SSOT: build_firma_standort_filter verwendet standort='2' für Landau!)
        # WICHTIG: BWA-Filter verwendet standort='2' für Landau, nicht '3'!
        # Locosoft verwendet subsidiary=3 für Landau, aber BWA verwendet standort='2'
        if betrieb is None:
            firma = '0'
            standort = '0'
        elif betrieb == 1:
            firma = '1'
            standort = '1'  # Deggendorf
        elif betrieb == 2:
            firma = '2'
            standort = '2'  # Hyundai (aber für BWA nicht relevant, da separate Firma)
        elif betrieb == 3:
            firma = '1'
            standort = '2'  # Landau (BWA verwendet standort='2', nicht '3'!)
        else:
            firma = '0'
            standort = '0'
        
        firma_filter_umsatz, _, _, standort_name = build_firma_standort_filter(firma, standort)
        # TAG 179: Zentrale Funktion verwenden
        from api.db_utils import get_guv_filter
        guv_filter = get_guv_filter()
        
        result = {
            'serviceerlöse_gesamt': 0.0,
            'lohnerlöse': 0.0,
            'et_erlöse': 0.0,
            'offener_lohn': 0.0,
            'offene_teile': 0.0,
            'betriebe_erlöse': []
        }
        
        # BWA-Daten aus DRIVE Portal DB
        with db_session() as conn:
            cursor = conn.cursor()
            
            # 1. Serviceerlöse gesamt (840000-849999)
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number BETWEEN 840000 AND 849999
                  {firma_filter_umsatz}
                  {guv_filter}
            """), (datum_von, datum_bis_exklusiv))
            result['serviceerlöse_gesamt'] = float(row_to_dict(cursor.fetchone())['wert'] or 0)
            result['lohnerlöse'] = result['serviceerlöse_gesamt']  # Identisch
            
            # 2. ET Erlöse (830000-839999)
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number BETWEEN 830000 AND 839999
                  {firma_filter_umsatz}
                  {guv_filter}
            """), (datum_von, datum_bis_exklusiv))
            result['et_erlöse'] = float(row_to_dict(cursor.fetchone())['wert'] or 0)
            
            # 3. Betrieb Erlöse zum Ziel (pro Betrieb)
            for betrieb_nr in [1, 2, 3]:
                if betrieb is not None and betrieb != betrieb_nr:
                    continue
                
                # Filter für diesen Betrieb (SSOT: BWA verwendet standort='2' für Landau!)
                if betrieb_nr == 1:
                    b_firma = '1'
                    b_standort = '1'  # Deggendorf
                elif betrieb_nr == 2:
                    b_firma = '2'
                    b_standort = '2'  # Hyundai (aber für BWA nicht relevant, da separate Firma)
                else:  # betrieb_nr == 3
                    b_firma = '1'
                    b_standort = '2'  # Landau (BWA verwendet standort='2', nicht '3'!)
                
                b_firma_filter_umsatz, _, _, b_standort_name = build_firma_standort_filter(b_firma, b_standort)
                
                # Serviceerlöse für diesen Betrieb
                cursor.execute(convert_placeholders(f"""
                    SELECT COALESCE(SUM(
                        CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
                    )/100.0, 0) as wert
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND nominal_account_number BETWEEN 840000 AND 849999
                      {b_firma_filter_umsatz}
                      {guv_filter}
                """), (datum_von, datum_bis_exklusiv))
                betrieb_erlöse = float(row_to_dict(cursor.fetchone())['wert'] or 0)
                
                # TODO: Zielwert aus Planung holen (für jetzt: 100% = Ziel)
                ziel_erlöse = betrieb_erlöse  # Placeholder
                ist_prozent = 100.0 if ziel_erlöse > 0 else 0
                
                result['betriebe_erlöse'].append({
                    'betrieb': betrieb_nr,
                    'betrieb_name': b_standort_name,
                    'erlöse': round(betrieb_erlöse, 2),
                    'ziel': round(ziel_erlöse, 2),
                    'ist_prozent': round(ist_prozent, 2),
                    'status': 'ok' if ist_prozent >= 100 else ('warnung' if ist_prozent >= 90 else 'kritisch')
                })
        
        # 4. Offener Lohn (unfakturierte Arbeitspositionen aus Locosoft)
        # WICHTIG: labours mit invoice_number IS NULL = noch nicht fakturiert!
        try:
            from api.standort_utils import build_locosoft_filter_orders
            
            with locosoft_session() as loco_conn:
                loco_cursor = loco_conn.cursor()
                
                # Standort-Filter für orders (nutzt build_locosoft_filter_orders)
                standort_filter = build_locosoft_filter_orders(betrieb if betrieb else 0)
                
                # Unfakturierte Arbeitspositionen: labours ohne invoice_number
                # WICHTIG: net_price_in_order ist bereits in Euro (nicht in Cent)!
                # PDF-Analyse Auftrag 20853: CSV zeigt 356 EUR, net_price_in_order = 3,56 EUR
                # → net_price_in_order ist bereits in Euro, aber die Werte sind falsch gespeichert
                # Test zeigt: net_price_in_order (ohne Division, time_units > 0) = 115.373 EUR
                # CSV zeigt: 127.075 EUR → näher, aber immer noch unterschiedlich
                # Möglicherweise: net_price_in_order * 1.1 (10% Aufschlag?) oder andere Berechnung
                # VORLÄUFIG: net_price_in_order direkt verwenden (ohne Division), nur time_units > 0
                loco_cursor.execute(f"""
                    SELECT COALESCE(SUM(l.net_price_in_order), 0) as offener_lohn
                    FROM labours l
                    JOIN orders o ON l.order_number = o.number
                    WHERE l.invoice_number IS NULL
                      AND l.time_units > 0
                      {standort_filter}
                """)
                
                row = loco_cursor.fetchone()
                if row:
                    result['offener_lohn'] = float(row[0] or 0)
        except Exception as e:
            logger.warning(f"Offener Lohn konnte nicht geladen werden: {e}")
            result['offener_lohn'] = 0.0
        
        # 5. Offene Teile (unfakturierte Teilepositionen aus Locosoft)
        # WICHTIG: parts mit invoice_number IS NULL = noch nicht fakturiert!
        try:
            from api.standort_utils import build_locosoft_filter_orders
            
            with locosoft_session() as loco_conn:
                loco_cursor = loco_conn.cursor()
                
                # Standort-Filter für orders (nutzt build_locosoft_filter_orders)
                standort_filter = build_locosoft_filter_orders(betrieb if betrieb else 0)
                
                # Unfakturierte Teile: parts ohne invoice_number
                # WICHTIG: CSV zeigt VK-Wert (sum), PDF zeigt Einsatzwert (usage_value)
                # Für "Offene Teile" verwenden wir VK-Wert (sum) wie in CSV
                # sum ist bereits in Euro (nicht in Cent) - keine Division durch 100!
                # Analog zu net_price_in_order: sum direkt verwenden
                loco_cursor.execute(f"""
                    SELECT COALESCE(SUM(p.sum), 0) as offene_teile
                    FROM parts p
                    JOIN orders o ON p.order_number = o.number
                    WHERE p.invoice_number IS NULL
                      {standort_filter}
                """)
                
                row = loco_cursor.fetchone()
                if row:
                    result['offene_teile'] = float(row[0] or 0)
        except Exception as e:
            logger.warning(f"Offene Teile konnten nicht geladen werden: {e}")
            result['offene_teile'] = 0.0
        
        return result

    @staticmethod
    def get_nachkalkulation(datum: Optional[date] = None, betrieb: Optional[int] = None,
                            typ: str = 'alle') -> Dict[str, Any]:
        """
        Auftrags-Nachkalkulation: Vergleich Vorgabe vs. Gestempelt vs. Verrechnet.
        Für Sensibilisierung von Serviceberatern und Fakturisten.

        TAG 151: Migriert von werkstatt_live_api.py (297 LOC -> ~200 LOC)

        Args:
            datum: Datum für Abfrage (default: heute)
            betrieb: Betrieb-ID (1, 2, 3) oder None für alle
            typ: 'alle'|'extern'|'intern'
                 extern = nur externe Kunden (echte Werkstattaufträge)
                 intern = nur interne Aufträge (eigene Fahrzeuge)

        Returns:
            Dict mit auftraege[], summary{}, filter{}

        Example:
            >>> data = WerkstattData.get_nachkalkulation(date(2026, 1, 2), betrieb=1)
            >>> data['summary']['gesamt_leistungsgrad']
            92.5
        """
        if datum is None:
            datum = date.today()

        betrieb_namen = {1: 'Deggendorf', 2: 'Hyundai', 3: 'Landau'}

        with locosoft_session() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            # Heute abgerechnete Werkstatt-Aufträge
            # WICHTIG: Ausschluss von Fahrzeugverkäufen (invoice_type 7, 8)
            # Nur echte Werkstattarbeit: invoice_type 2, 4, 5, 6
            query = """
                WITH heute_rechnungen AS (
                    SELECT
                        i.order_number,
                        i.invoice_number,
                        i.invoice_type,
                        i.invoice_date,
                        i.job_amount_net,
                        i.subsidiary,
                        i.creating_employee,
                        o.order_customer as kunden_nr
                    FROM invoices i
                    LEFT JOIN orders o ON i.order_number = o.number
                    WHERE DATE(i.invoice_date) = %s
                      AND i.invoice_type IN (2, 4, 5, 6)
                      AND i.job_amount_net > 0
                      AND i.is_canceled = false
                ),
                labour_summen AS (
                    SELECT
                        l.order_number,
                        SUM(l.time_units) as gesamt_aw,
                        SUM(CASE WHEN l.is_invoiced THEN l.time_units ELSE 0 END) as fakturiert_aw,
                        SUM(CASE WHEN NOT l.is_invoiced THEN l.time_units ELSE 0 END) as offen_aw,
                        SUM(CASE WHEN l.mechanic_no IS NOT NULL THEN l.time_units ELSE 0 END) as zugeordnet_aw,
                        SUM(CASE WHEN l.mechanic_no IS NULL THEN l.time_units ELSE 0 END) as nicht_zugeordnet_aw,
                        SUM(l.net_price_in_order) as vorgabe_eur,
                        STRING_AGG(DISTINCT eh.name, ', ') as mechaniker_namen,
                        CASE
                            WHEN SUM(l.time_units) > 0 THEN
                                ROUND((SUM(l.time_units * COALESCE(ct.timeunit_rate, 0)) / NULLIF(SUM(l.time_units), 0))::numeric, 2)
                            ELSE 0
                        END as aw_preis_db,
                        CASE
                            WHEN SUM(CASE WHEN NOT l.is_invoiced THEN l.time_units ELSE 0 END) > 0 THEN false
                            ELSE true
                        END as vollstaendig_abgerechnet
                    FROM labours l
                    LEFT JOIN employees_history eh ON l.mechanic_no = eh.employee_number
                        AND eh.is_latest_record = true
                    LEFT JOIN charge_types ct ON l.charge_type = ct.type AND ct.subsidiary = 1
                    WHERE l.order_number IN (SELECT order_number FROM heute_rechnungen)
                    GROUP BY l.order_number
                ),
                stempel_summen AS (
                    SELECT
                        order_number,
                        SUM(minuten) as gestempelt_min
                    FROM (
                        SELECT DISTINCT ON (order_number, employee_number, start_time, end_time)
                            order_number,
                            EXTRACT(EPOCH FROM (COALESCE(end_time, NOW()) - start_time)) / 60 as minuten
                        FROM times
                        WHERE type = 2
                          AND order_number IN (SELECT order_number FROM heute_rechnungen)
                    ) dedup
                    GROUP BY order_number
                ),
                auftrags_details AS (
                    SELECT
                        o.number as order_number,
                        o.order_date,
                        o.order_taking_employee_no as sb_nr,
                        sb.name as sb_name,
                        v.license_plate as kennzeichen,
                        m.description as marke,
                        COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name, 'Unbekannt') as kunde,
                        cs.customer_number as kunden_nr,
                        CASE
                            WHEN cs.customer_number = 3000001 THEN true
                            WHEN LOWER(cs.family_name) LIKE '%%intern%%' THEN true
                            WHEN LOWER(cs.family_name) LIKE '%%greiner%%' AND LOWER(cs.family_name) LIKE '%%auto%%' THEN true
                            ELSE false
                        END as ist_intern
                    FROM orders o
                    LEFT JOIN employees_history sb ON o.order_taking_employee_no = sb.employee_number
                        AND sb.is_latest_record = true
                    LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
                    LEFT JOIN makes m ON v.make_number = m.make_number
                    LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
                    WHERE o.number IN (SELECT order_number FROM heute_rechnungen)
                )
                SELECT
                    r.order_number,
                    r.invoice_number,
                    r.invoice_type,
                    r.subsidiary,
                    ROUND(r.job_amount_net::numeric, 2) as rechnung_eur,
                    ROUND(COALESCE(l.gesamt_aw, 0)::numeric, 1) as vorgabe_aw,
                    ROUND(COALESCE(l.fakturiert_aw, 0)::numeric, 1) as fakturiert_aw,
                    ROUND(COALESCE(l.offen_aw, 0)::numeric, 1) as offen_aw,
                    COALESCE(l.vollstaendig_abgerechnet, true) as vollstaendig_abgerechnet,
                    ROUND(COALESCE(l.vorgabe_eur, 0)::numeric, 2) as vorgabe_eur,
                    ROUND(COALESCE(l.aw_preis_db, 0)::numeric, 2) as aw_preis_db,
                    ROUND(COALESCE(s.gestempelt_min, 0)::numeric / 6, 1) as gestempelt_aw,
                    ROUND(COALESCE(s.gestempelt_min, 0)::numeric, 0) as gestempelt_min,
                    l.mechaniker_namen,
                    a.sb_name,
                    a.sb_nr,
                    a.kennzeichen,
                    a.marke,
                    a.kunde,
                    a.kunden_nr,
                    a.ist_intern,
                    a.order_date
                FROM heute_rechnungen r
                LEFT JOIN labour_summen l ON r.order_number = l.order_number
                LEFT JOIN stempel_summen s ON r.order_number = s.order_number
                LEFT JOIN auftrags_details a ON r.order_number = a.order_number
                WHERE 1=1
            """

            params = [datum]

            # Betrieb-Filter
            if betrieb:
                query += " AND r.subsidiary = %s"
                params.append(betrieb)

            # Intern/Extern Filter
            if typ == 'extern':
                query += " AND a.ist_intern = false"
            elif typ == 'intern':
                query += " AND a.ist_intern = true"

            query += " ORDER BY (COALESCE(s.gestempelt_min, 0) / 6 - COALESCE(l.gesamt_aw, 0)) DESC"

            cur.execute(query, params)
            rows = cur.fetchall()

            # Nachkalkulation berechnen
            auftraege = []
            total_rechnung = 0
            total_vorgabe_aw = 0
            total_gestempelt_aw = 0
            total_verlust = 0
            probleme = 0

            for r in rows:
                vorgabe_aw = float(r['vorgabe_aw'] or 0)
                gestempelt_aw = float(r['gestempelt_aw'] or 0)
                rechnung_eur = float(r['rechnung_eur'] or 0)

                # Differenz berechnen
                diff_aw = gestempelt_aw - vorgabe_aw

                # AW-Preis aus charge_types (DB-Verrechnungssatz) verwenden
                aw_preis_db = float(r.get('aw_preis_db') or 0)

                if aw_preis_db > 0:
                    aw_preis = aw_preis_db
                    verlust_eur = diff_aw * aw_preis
                elif vorgabe_aw > 0:
                    aw_preis = rechnung_eur / vorgabe_aw
                    verlust_eur = diff_aw * aw_preis
                else:
                    aw_preis = 0
                    verlust_eur = 0

                # Leistungsgrad (Vorgabe / Gestempelt * 100)
                if gestempelt_aw > 0:
                    leistungsgrad = vorgabe_aw / gestempelt_aw * 100
                else:
                    leistungsgrad = 0

                # Status bestimmen
                if diff_aw <= 0:
                    status = 'ok'
                elif diff_aw <= 2:
                    status = 'warnung'
                else:
                    status = 'kritisch'
                    probleme += 1

                fakturiert_aw = float(r.get('fakturiert_aw') or 0)
                offen_aw = float(r.get('offen_aw') or 0)
                vollstaendig = r.get('vollstaendig_abgerechnet', True)

                auftraege.append({
                    'order_number': r['order_number'],
                    'invoice_number': r['invoice_number'],
                    'invoice_type': r['invoice_type'],
                    'betrieb': r['subsidiary'],
                    'betrieb_name': betrieb_namen.get(r['subsidiary'], '?'),
                    'rechnung_eur': rechnung_eur,
                    'vorgabe_aw': vorgabe_aw,
                    'fakturiert_aw': fakturiert_aw,
                    'offen_aw': offen_aw,
                    'vollstaendig_abgerechnet': vollstaendig,
                    'gestempelt_aw': gestempelt_aw,
                    'gestempelt_min': int(r['gestempelt_min'] or 0),
                    'diff_aw': round(diff_aw, 1),
                    'aw_preis': round(aw_preis, 2),
                    'verlust_eur': round(verlust_eur, 2),
                    'leistungsgrad': round(leistungsgrad, 1),
                    'status': status,
                    'mechaniker': r['mechaniker_namen'],
                    'serviceberater': r['sb_name'] or f"MA {r['sb_nr']}" if r['sb_nr'] else None,
                    'serviceberater_nr': r['sb_nr'],
                    'kennzeichen': r['kennzeichen'],
                    'marke': r['marke'],
                    'kunde': r['kunde'],
                    'kunden_nr': r['kunden_nr'],
                    'ist_intern': r['ist_intern'],
                    'auftragsdatum': r['order_date'].strftime('%d.%m.%Y') if r['order_date'] else None
                })

                total_rechnung += rechnung_eur
                total_vorgabe_aw += vorgabe_aw
                total_gestempelt_aw += gestempelt_aw
                if verlust_eur > 0:
                    total_verlust += verlust_eur

            # Unvollständig abgerechnete Aufträge zählen
            unvollstaendig = sum(1 for a in auftraege if not a.get('vollstaendig_abgerechnet', True))

            # Gesamt-Leistungsgrad
            if total_gestempelt_aw > 0:
                gesamt_leistungsgrad = total_vorgabe_aw / total_gestempelt_aw * 100
            else:
                gesamt_leistungsgrad = 0

            return {
                'datum': str(datum),
                'filter': {
                    'betrieb': betrieb,
                    'typ': typ
                },
                'auftraege': auftraege,
                'summary': {
                    'anzahl_rechnungen': len(auftraege),
                    'anzahl_probleme': probleme,
                    'anzahl_unvollstaendig': unvollstaendig,
                    'total_rechnung_eur': round(total_rechnung, 2),
                    'total_vorgabe_aw': round(total_vorgabe_aw, 1),
                    'total_gestempelt_aw': round(total_gestempelt_aw, 1),
                    'total_diff_aw': round(total_gestempelt_aw - total_vorgabe_aw, 1),
                    'total_verlust_eur': round(total_verlust, 2),
                    'gesamt_leistungsgrad': round(gesamt_leistungsgrad, 1)
                }
            }

    # =========================================================================
    # ANWESENHEIT - Mechaniker Präsenz & Produktivität
    # =========================================================================

    @staticmethod
    def get_anwesenheit(datum: Optional[date] = None, betrieb: Optional[int] = None) -> Dict[str, Any]:
        """
        Anwesenheits-Report: Wer hat heute gearbeitet?

        TAG 151: Migriert von werkstatt_live_api.py (160 LOC -> ~120 LOC)
        Basiert auf Type 2 (produktive Stempelungen) + Type 1 für Historie.

        Args:
            datum: Datum für Abfrage (default: heute)
            betrieb: Betrieb-ID (1, 2, 3) oder None für alle

        Returns:
            Dict mit anwesend[], abwesend[], aktiv[], statistik{}

        Example:
            >>> data = WerkstattData.get_anwesenheit(date(2026, 1, 2))
            >>> data['statistik']['anwesend']
            12
        """
        if datum is None:
            datum = date.today()

        datum_str = datum.strftime('%Y-%m-%d')
        
        # TAG 194: Leerlaufaufträge dynamisch (SSOT)
        leerlauf_auftraege_alle = []
        for b_leerlauf in LEERLAUF_AUFTRAEGE_PRO_BETRIEB.values():
            leerlauf_auftraege_alle.extend(b_leerlauf)
        leerlauf_auftraege_alle = list(set(leerlauf_auftraege_alle))
        leerlauf_liste_str = ','.join(map(str, leerlauf_auftraege_alle)) if leerlauf_auftraege_alle else '0'

        with locosoft_session() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute(f'''
                WITH stempelungen AS (
                    SELECT
                        t.employee_number,
                        MIN(t.start_time) as erster_start,
                        MAX(COALESCE(t.end_time, NOW())) as letztes_ende,
                        COUNT(DISTINCT t.order_number) FILTER (WHERE t.order_number != ALL(ARRAY[{leerlauf_liste_str}])) as anzahl_auftraege,
                        SUM(EXTRACT(EPOCH FROM (COALESCE(t.end_time, NOW()) - t.start_time))/60)
                            FILTER (WHERE t.order_number != ALL(ARRAY[{leerlauf_liste_str}])) as produktiv_min,
                        SUM(EXTRACT(EPOCH FROM (COALESCE(t.end_time, NOW()) - t.start_time))/60)
                            FILTER (WHERE t.order_number = ANY(ARRAY[{leerlauf_liste_str}])) as leerlauf_min,
                        MAX(CASE WHEN t.end_time IS NULL THEN t.order_number END) as aktiver_auftrag,
                        MAX(CASE WHEN t.end_time IS NULL THEN t.start_time END) as aktiv_seit
                    FROM times t
                    WHERE DATE(t.start_time) = %s
                      AND t.type = 2
                      AND t.employee_number BETWEEN 5000 AND 5999
                    GROUP BY t.employee_number
                ),
                anwesenheit AS (
                    SELECT
                        t.employee_number,
                        MIN(t.start_time) as anwesend_ab,
                        MAX(t.end_time) as anwesend_bis,
                        ROUND(SUM(EXTRACT(EPOCH FROM (t.end_time - t.start_time))/60)::numeric) as anwesend_min
                    FROM times t
                    WHERE DATE(t.start_time) = %s
                      AND t.type = 1
                      AND t.employee_number BETWEEN 5000 AND 5999
                    GROUP BY t.employee_number
                ),
                alle_mechaniker AS (
                    SELECT DISTINCT
                        eh.employee_number,
                        eh.name,
                        eh.subsidiary,
                        CASE eh.subsidiary
                            WHEN 1 THEN 'Deggendorf'
                            WHEN 2 THEN 'Hyundai'
                            WHEN 3 THEN 'Landau'
                        END as betrieb
                    FROM employees_history eh
                    WHERE eh.is_latest_record = true
                      AND eh.employee_number BETWEEN 5000 AND 5999
                      AND (eh.leave_date IS NULL OR eh.leave_date > %s::date)
                      AND eh.subsidiary IN (1, 2, 3)
                ),
                abwesenheiten AS (
                    SELECT
                        ac.employee_number,
                        ac.reason,
                        ac.type as abwesenheit_typ
                    FROM absence_calendar ac
                    WHERE ac.date = %s::date
                )
                SELECT
                    m.employee_number,
                    m.name,
                    m.subsidiary,
                    m.betrieb,
                    s.erster_start,
                    s.letztes_ende,
                    COALESCE(s.anzahl_auftraege, 0) as anzahl_auftraege,
                    COALESCE(ROUND(s.produktiv_min::numeric), 0) as produktiv_min,
                    COALESCE(ROUND(s.leerlauf_min::numeric), 0) as leerlauf_min,
                    s.aktiver_auftrag,
                    s.aktiv_seit,
                    a.anwesend_ab,
                    a.anwesend_bis,
                    COALESCE(a.anwesend_min, 0) as anwesend_min,
                    CASE WHEN s.employee_number IS NOT NULL THEN true ELSE false END as hat_gearbeitet,
                    ab.reason as abwesenheit_grund,
                    ab.abwesenheit_typ
                FROM alle_mechaniker m
                LEFT JOIN stempelungen s ON m.employee_number = s.employee_number
                LEFT JOIN anwesenheit a ON m.employee_number = a.employee_number
                LEFT JOIN abwesenheiten ab ON m.employee_number = ab.employee_number
                ORDER BY m.betrieb, m.name
            ''', (datum_str, datum_str, datum_str, datum_str))

            alle = cur.fetchall()
            cur.close()

            # Filter nach Betrieb
            if betrieb:
                alle = [m for m in alle if m['subsidiary'] == betrieb]

            # Kategorisieren
            anwesend = []
            abwesend = []
            aktiv = []

            for m in alle:
                entry = {
                    'employee_number': m['employee_number'],
                    'name': m['name'],
                    'betrieb': m['betrieb'],
                    'erster_start': m['erster_start'].strftime('%H:%M') if m['erster_start'] else None,
                    'letztes_ende': m['letztes_ende'].strftime('%H:%M') if m['letztes_ende'] else None,
                    'anzahl_auftraege': m['anzahl_auftraege'],
                    'produktiv_min': int(m['produktiv_min']),
                    'produktiv_std': round(m['produktiv_min'] / 60, 1),
                    'leerlauf_min': int(m['leerlauf_min'] or 0),
                    'aktiver_auftrag': m['aktiver_auftrag'],
                    'aktiv_seit': m['aktiv_seit'].strftime('%H:%M') if m['aktiv_seit'] else None,
                    'anwesend_ab': m['anwesend_ab'].strftime('%H:%M') if m['anwesend_ab'] else None,
                    'anwesend_bis': m['anwesend_bis'].strftime('%H:%M') if m['anwesend_bis'] else None,
                    'anwesend_min': int(m['anwesend_min'] or 0),
                    'anwesend_std': round((m['anwesend_min'] or 0) / 60, 1),
                    'abwesenheit_grund': m['abwesenheit_grund'],
                    'abwesenheit_typ': m['abwesenheit_typ']
                }
                if m['hat_gearbeitet']:
                    anwesend.append(entry)
                    if m['aktiver_auftrag']:
                        aktiv.append(entry)
                else:
                    abwesend.append(entry)

            total_produktiv = sum(m['produktiv_min'] for m in anwesend)
            total_leerlauf = sum(m['leerlauf_min'] for m in anwesend)

            return {
                'datum': datum_str,
                'anwesend': anwesend,
                'abwesend': abwesend,
                'aktiv': aktiv,
                'statistik': {
                    'total_mechaniker': len(alle),
                    'anwesend': len(anwesend),
                    'abwesend': len(abwesend),
                    'gerade_aktiv': len(aktiv),
                    'produktiv_std': round(total_produktiv / 60, 1),
                    'leerlauf_std': round(total_leerlauf / 60, 1)
                }
            }

    # =========================================================================
    # HEUTE LIVE - Echtzahlen von heute (Stempelungen + Verrechnet)
    # =========================================================================

    @staticmethod
    def get_heute_live(betrieb: Optional[int] = None) -> Dict[str, Any]:
        """
        Echte Zahlen von heute: Gestempelt, Verrechnet, Aktive Mechaniker.

        TAG 151: Migriert von werkstatt_live_api.py (330 LOC -> ~280 LOC)

        Args:
            betrieb: Betrieb-ID (1, 2, 3) oder None für alle

        Returns:
            Dict mit anwesenheit{}, produktiv{}, aktiv{}, verrechnet{}, kapazitaet{}, produktivitaet{}

        Example:
            >>> data = WerkstattData.get_heute_live(betrieb=1)
            >>> data['produktivitaet']['prozent']
            95.5
        """
        heute = date.today()

        with locosoft_session() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # 1. ANWESENHEIT HEUTE (order_number = 0)
            anwesenheit_query = """
                SELECT
                    COUNT(DISTINCT employee_number) as mechaniker,
                    COALESCE(ROUND(SUM(duration_minutes)::numeric / 60, 1), 0) as stunden
                FROM times
                WHERE DATE(start_time) = CURRENT_DATE
                AND DATE(end_time) = CURRENT_DATE
                AND employee_number BETWEEN 5000 AND 5999
                AND order_number = 0
            """
            cur.execute(anwesenheit_query)
            anwesenheit = cur.fetchone()

            # 2. PRODUKTIVE ARBEIT HEUTE (order_number > 0)
            if betrieb:
                stempel_query = """
                    SELECT
                        COUNT(DISTINCT sub.order_number) as auftraege,
                        COUNT(DISTINCT sub.employee_number) as mechaniker,
                        COALESCE(ROUND(SUM(sub.stunden)::numeric, 1), 0) as stunden,
                        COALESCE(ROUND(SUM(sub.stunden)::numeric * 6, 1), 0) as aw
                    FROM (
                        SELECT t.employee_number, t.order_number, t.start_time,
                               MAX(t.duration_minutes)/60.0 as stunden
                        FROM times t
                        JOIN orders o ON t.order_number = o.number
                        WHERE DATE(t.start_time) = CURRENT_DATE
                        AND DATE(t.end_time) = CURRENT_DATE
                        AND t.employee_number BETWEEN 5000 AND 5999
                        AND t.order_number > 0
                        AND o.subsidiary = %s
                        GROUP BY t.employee_number, t.order_number, t.start_time
                    ) sub
                """
                cur.execute(stempel_query, (betrieb,))
            else:
                stempel_query = """
                    SELECT
                        COUNT(DISTINCT sub.order_number) as auftraege,
                        COUNT(DISTINCT sub.employee_number) as mechaniker,
                        COALESCE(ROUND(SUM(sub.stunden)::numeric, 1), 0) as stunden,
                        COALESCE(ROUND(SUM(sub.stunden)::numeric * 6, 1), 0) as aw
                    FROM (
                        SELECT employee_number, order_number, start_time,
                               MAX(duration_minutes)/60.0 as stunden
                        FROM times
                        WHERE DATE(start_time) = CURRENT_DATE
                        AND DATE(end_time) = CURRENT_DATE
                        AND employee_number BETWEEN 5000 AND 5999
                        AND order_number > 0
                        GROUP BY employee_number, order_number, start_time
                    ) sub
                """
                cur.execute(stempel_query)

            gestempelt = cur.fetchone()

            # 3. AKTUELL AKTIV (gerade am arbeiten)
            aktiv_query = """
                SELECT
                    t.employee_number,
                    e.name as mechaniker_name,
                    t.order_number,
                    t.start_time,
                    v.license_plate as kennzeichen
                FROM times t
                JOIN employees_history e ON t.employee_number = e.employee_number AND e.is_latest_record = true
                LEFT JOIN orders o ON t.order_number = o.number
                LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
                WHERE DATE(t.start_time) = CURRENT_DATE
                AND t.end_time IS NULL
                ORDER BY t.start_time DESC
            """
            cur.execute(aktiv_query)
            aktiv_raw = cur.fetchall()

            # Duplikate entfernen
            aktiv_dict = {}
            for row in aktiv_raw:
                emp_no = row['employee_number']
                if emp_no not in aktiv_dict:
                    aktiv_dict[emp_no] = {
                        'employee_number': emp_no,
                        'name': row['mechaniker_name'],
                        'order_number': row['order_number'],
                        'kennzeichen': row['kennzeichen'],
                        'seit': row['start_time'].strftime('%H:%M') if row['start_time'] else None
                    }
            aktiv_gestempelt = list(aktiv_dict.values())

            # 4. VERRECHNET HEUTE (Werkstatt, ohne Fahrzeugverkauf)
            if betrieb:
                verrechnet_query = """
                    SELECT
                        COUNT(*) as rechnungen,
                        COALESCE(ROUND(SUM(job_amount_net)::numeric, 2), 0) as lohn_netto,
                        COALESCE(ROUND(SUM(part_amount_net)::numeric, 2), 0) as teile_netto,
                        COALESCE(ROUND(SUM(total_net)::numeric, 2), 0) as gesamt_netto
                    FROM invoices
                    WHERE DATE(invoice_date) = CURRENT_DATE
                    AND is_canceled = false
                    AND invoice_type NOT IN (8)
                    AND subsidiary = %s
                """
                cur.execute(verrechnet_query, (betrieb,))
            else:
                verrechnet_query = """
                    SELECT
                        COUNT(*) as rechnungen,
                        COALESCE(ROUND(SUM(job_amount_net)::numeric, 2), 0) as lohn_netto,
                        COALESCE(ROUND(SUM(part_amount_net)::numeric, 2), 0) as teile_netto,
                        COALESCE(ROUND(SUM(total_net)::numeric, 2), 0) as gesamt_netto
                    FROM invoices
                    WHERE DATE(invoice_date) = CURRENT_DATE
                    AND is_canceled = false
                    AND invoice_type NOT IN (8)
                """
                cur.execute(verrechnet_query)

            verrechnet = cur.fetchone()

            # 5. VERRECHNET AW HEUTE
            if betrieb:
                aw_query = """
                    SELECT
                        COUNT(DISTINCT l.order_number) as auftraege,
                        COALESCE(ROUND(SUM(l.time_units)::numeric, 1), 0) as aw_verrechnet
                    FROM invoices i
                    JOIN labours l ON i.order_number = l.order_number
                    WHERE DATE(i.invoice_date) = CURRENT_DATE
                    AND i.is_canceled = false
                    AND i.invoice_type NOT IN (8)
                    AND l.is_invoiced = true
                    AND i.subsidiary = %s
                """
                cur.execute(aw_query, (betrieb,))
            else:
                aw_query = """
                    SELECT
                        COUNT(DISTINCT l.order_number) as auftraege,
                        COALESCE(ROUND(SUM(l.time_units)::numeric, 1), 0) as aw_verrechnet
                    FROM invoices i
                    JOIN labours l ON i.order_number = l.order_number
                    WHERE DATE(i.invoice_date) = CURRENT_DATE
                    AND i.is_canceled = false
                    AND i.invoice_type NOT IN (8)
                    AND l.is_invoiced = true
                """
                cur.execute(aw_query)

            aw_verrechnet = cur.fetchone()

            # 6. KAPAZITÄT HEUTE
            kapazitaet_query = """
                WITH aktuelle_arbeitszeiten AS (
                    SELECT DISTINCT ON (employee_number, dayofweek)
                        employee_number, dayofweek, work_duration
                    FROM employees_worktimes
                    ORDER BY employee_number, dayofweek, validity_date DESC
                )
                SELECT
                    COUNT(DISTINCT eh.employee_number) as mechaniker_gesamt,
                    COALESCE(SUM(COALESCE(aw.work_duration, 8)), 0) as stunden_kapazitaet
                FROM employees_history eh
                LEFT JOIN aktuelle_arbeitszeiten aw
                    ON eh.employee_number = aw.employee_number
                    AND aw.dayofweek = EXTRACT(DOW FROM CURRENT_DATE)
                LEFT JOIN absence_calendar ab
                    ON eh.employee_number = ab.employee_number
                    AND ab.date = CURRENT_DATE
                WHERE eh.is_latest_record = true
                AND eh.employee_number BETWEEN 5000 AND 5999
                AND eh.leave_date IS NULL
                AND ab.employee_number IS NULL
            """
            if betrieb:
                kapazitaet_query = kapazitaet_query.replace(
                    "AND ab.employee_number IS NULL",
                    f"AND ab.employee_number IS NULL AND eh.subsidiary = {betrieb}"
                )

            cur.execute(kapazitaet_query)
            kapazitaet = cur.fetchone()
            cur.close()

            # BERECHNUNGEN
            anwesend_stunden = float(anwesenheit['stunden'] or 0)
            anwesend_mechaniker = int(anwesenheit['mechaniker'] or 0)

            produktiv_aw = float(gestempelt['aw'] or 0)
            produktiv_stunden = float(gestempelt['stunden'] or 0)
            produktiv_auftraege = int(gestempelt['auftraege'] or 0)

            verrechnet_aw_val = float(aw_verrechnet['aw_verrechnet'] or 0)
            mechaniker_anwesend = int(kapazitaet['mechaniker_gesamt'] or 0)

            if anwesend_mechaniker > 0:
                kapazitaet_stunden = anwesend_mechaniker * 8.0
                kapazitaet_aw = kapazitaet_stunden * 6
            else:
                kapazitaet_stunden = float(kapazitaet['stunden_kapazitaet'] or 0)
                kapazitaet_aw = kapazitaet_stunden * 6

            produktivitaet = round((anwesend_stunden / kapazitaet_stunden * 100) if kapazitaet_stunden > 0 else 0, 1)

            # Status
            if produktivitaet >= 110:
                status = 'optimal'
                status_text = 'Ziel erreicht!'
                status_icon = 'green'
            elif produktivitaet >= 90:
                status = 'gut'
                status_text = 'Gut unterwegs'
                status_icon = 'green'
            elif produktivitaet >= 50:
                status = 'normal'
                status_text = 'Normal'
                status_icon = 'blue'
            else:
                status = 'niedrig'
                status_text = 'Unterausgelastet'
                status_icon = 'blue'

            return {
                'datum': str(heute),
                'datum_formatiert': heute.strftime('%d.%m.%Y'),
                'filter': {'betrieb': betrieb},
                'anwesenheit': {
                    'mechaniker': anwesend_mechaniker,
                    'stunden': anwesend_stunden,
                    'aw': round(anwesend_stunden * 6, 1)
                },
                'produktiv': {
                    'auftraege': produktiv_auftraege,
                    'stunden': produktiv_stunden,
                    'aw': produktiv_aw
                },
                'aktiv': {
                    'anzahl': len(aktiv_gestempelt),
                    'mechaniker': aktiv_gestempelt[:20]
                },
                'verrechnet': {
                    'rechnungen': int(verrechnet['rechnungen'] or 0),
                    'auftraege': int(aw_verrechnet['auftraege'] or 0),
                    'aw': float(verrechnet_aw_val),
                    'lohn_netto': float(verrechnet['lohn_netto'] or 0),
                    'teile_netto': float(verrechnet['teile_netto'] or 0),
                    'gesamt_netto': float(verrechnet['gesamt_netto'] or 0)
                },
                'kapazitaet': {
                    'mechaniker': anwesend_mechaniker if anwesend_mechaniker > 0 else mechaniker_anwesend,
                    'stunden_soll': kapazitaet_stunden,
                    'aw': kapazitaet_aw
                },
                'produktivitaet': {
                    'prozent': produktivitaet,
                    'status': status,
                    'status_text': status_text,
                    'status_icon': status_icon,
                    'ziel': 110
                }
            }

    # =========================================================================
    # ANWESENHEIT LEGACY - Type 1 basiert (nach Feierabend)
    # =========================================================================

    @staticmethod
    def get_anwesenheit_legacy(betrieb: Optional[int] = None) -> Dict[str, Any]:
        """
        Anwesenheits-Report Legacy: Wer hat eingestempelt, wer nicht?

        TAG 151: Migriert von werkstatt_live_api.py (130 LOC -> ~100 LOC)
        HINWEIS: Nur nach Feierabend zuverlaessig (Type 1 erst bei Ausstempeln).

        Args:
            betrieb: Betrieb-ID (1, 2, 3) oder None für alle

        Returns:
            Dict mit vergessen[], korrekt[], frueh[], spaet[], statistik{}
        """
        from datetime import time as dt_time

        with locosoft_session() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute('''
                WITH produktiv_heute AS (
                    SELECT DISTINCT
                        t.employee_number,
                        MIN(t.start_time) as erste_produktiv,
                        MAX(COALESCE(t.end_time, NOW())) as letzte_produktiv,
                        COUNT(DISTINCT t.order_number) as anzahl_auftraege
                    FROM times t
                    WHERE DATE(t.start_time) = CURRENT_DATE
                      AND t.type = 2
                      AND t.employee_number BETWEEN 5000 AND 5999
                    GROUP BY t.employee_number
                ),
                anwesend_heute AS (
                    SELECT DISTINCT
                        t.employee_number,
                        MIN(t.start_time) as erste_anwesend,
                        MAX(COALESCE(t.end_time, NOW())) as letzte_anwesend
                    FROM times t
                    WHERE DATE(t.start_time) = CURRENT_DATE
                      AND t.type = 1
                      AND t.employee_number BETWEEN 5000 AND 5999
                    GROUP BY t.employee_number
                )
                SELECT
                    p.employee_number,
                    eh.name,
                    eh.subsidiary,
                    CASE eh.subsidiary
                        WHEN 1 THEN 'Deggendorf'
                        WHEN 2 THEN 'Hyundai'
                        WHEN 3 THEN 'Landau'
                        ELSE 'Unbekannt'
                    END as betrieb_name,
                    p.erste_produktiv,
                    p.letzte_produktiv,
                    p.anzahl_auftraege,
                    a.erste_anwesend,
                    a.letzte_anwesend,
                    CASE WHEN a.employee_number IS NULL THEN true ELSE false END as vergessen
                FROM produktiv_heute p
                LEFT JOIN anwesend_heute a ON p.employee_number = a.employee_number
                JOIN employees_history eh ON p.employee_number = eh.employee_number
                    AND eh.is_latest_record = true
                WHERE (eh.leave_date IS NULL OR eh.leave_date > CURRENT_DATE)
            ''')

            alle = cur.fetchall()
            cur.close()

            # Filter nach Betrieb
            if betrieb:
                alle = [m for m in alle if m['subsidiary'] == betrieb]

            # Kategorisieren
            vergessen = []
            korrekt = []
            frueh = []
            spaet = []

            for m in alle:
                entry = {
                    'employee_number': m['employee_number'],
                    'name': m['name'],
                    'betrieb': m['betrieb_name'],
                    'erste_produktiv': m['erste_produktiv'].strftime('%H:%M') if m['erste_produktiv'] else None,
                    'erste_anwesend': m['erste_anwesend'].strftime('%H:%M') if m['erste_anwesend'] else None,
                    'produktiv_auftraege': m['anzahl_auftraege']
                }

                if m['vergessen']:
                    vergessen.append(entry)
                else:
                    korrekt.append(entry)
                    if m['erste_anwesend']:
                        zeit = m['erste_anwesend'].time()
                        if zeit < dt_time(7, 50):
                            frueh.append(entry)
                        elif zeit > dt_time(8, 5):
                            spaet.append(entry)

            return {
                'vergessen': vergessen,
                'korrekt': korrekt,
                'frueh': frueh,
                'spaet': spaet,
                'statistik': {
                    'total_produktiv': len(alle),
                    'vergessen': len(vergessen),
                    'korrekt': len(korrekt),
                    'frueh': len(frueh),
                    'spaet': len(spaet)
                }
            }

    # =========================================================================
    # KULANZ MONITORING - Revenue Leakage Analyse
    # =========================================================================

    @staticmethod
    def get_kulanz_monitoring(wochen: int = 4, betrieb: Optional[int] = None) -> Dict[str, Any]:
        """
        Kulanz-Monitoring: Wo verlieren wir Geld?

        TAG 151: Migriert von werkstatt_live_api.py (160 LOC -> ~140 LOC)
        Vergleicht gestempelte Zeit mit abgerechneter Zeit pro Charge Type.

        Args:
            wochen: Anzahl Wochen zurueck (default: 4)
            betrieb: Betrieb-ID (1, 2, 3) oder None für alle

        Returns:
            Dict mit statistik{}, by_charge_type[], top_verluste_kulanz[]
        """
        CHARGE_TYPES = {
            10: 'Kunde',
            11: 'Kunde (Rabatt)',
            15: 'Garantie Hersteller',
            16: 'Garantie Haendler',
            40: 'Garantie',
            60: 'Kulanz',
            90: 'Intern'
        }

        with locosoft_session() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            subsidiary_filter = "AND o.subsidiary = %s" if betrieb else ""
            params = [wochen]
            if betrieb:
                params.append(betrieb)

            query = f'''
            WITH unique_times AS (
                SELECT DISTINCT order_number, employee_number, start_time, end_time, duration_minutes
                FROM times
                WHERE order_number > 0
                  AND duration_minutes > 0
                  AND start_time >= NOW() - INTERVAL '%s weeks'
            ),
            gestempelt AS (
                SELECT order_number, SUM(duration_minutes) as stempel_min
                FROM unique_times GROUP BY order_number
            ),
            abgerechnet AS (
                SELECT order_number,
                       MAX(charge_type) as charge_type,
                       SUM(time_units * 6) as abrechn_min
                FROM labours
                WHERE time_units > 0 AND order_number > 0
                GROUP BY order_number
            )
            SELECT
                a.charge_type,
                COUNT(*) as anzahl_auftraege,
                ROUND(SUM(g.stempel_min) / 60.0, 1) as gestempelt_std,
                ROUND(SUM(a.abrechn_min) / 60.0, 1) as abgerechnet_std,
                ROUND((SUM(g.stempel_min) - SUM(a.abrechn_min)) / 60.0, 1) as differenz_std,
                ROUND(100.0 * (SUM(g.stempel_min) - SUM(a.abrechn_min)) / NULLIF(SUM(a.abrechn_min), 0), 1) as differenz_pct
            FROM gestempelt g
            JOIN abgerechnet a ON g.order_number = a.order_number
            JOIN orders o ON g.order_number = o.number
            WHERE o.order_date >= NOW() - INTERVAL '%s weeks'
            {subsidiary_filter}
            GROUP BY a.charge_type
            ORDER BY differenz_std DESC
            '''

            cur.execute(query, params + params[:1])
            by_type = cur.fetchall()

            # Top 20 Verlust-Auftraege (Kulanz)
            query_top = f'''
            WITH unique_times AS (
                -- TAG 211: Konsistente Deduplizierung - sekundengleiche Stempelzeiten desselben Mechanikers auf demselben Auftrag nur einmal
                SELECT DISTINCT ON (employee_number, order_number, start_time, end_time)
                    order_number, employee_number, start_time, end_time, duration_minutes
                FROM times 
                WHERE order_number > 0 
                  AND duration_minutes > 0 
                  AND type = 2
                  AND end_time IS NOT NULL
                  AND start_time >= NOW() - INTERVAL '%s weeks'
                ORDER BY employee_number, order_number, start_time, end_time
            ),
            gestempelt AS (
                SELECT order_number, SUM(duration_minutes) as stempel_min FROM unique_times GROUP BY order_number
            ),
            abgerechnet AS (
                SELECT order_number, MAX(charge_type) as charge_type, SUM(time_units * 6) as abrechn_min
                FROM labours WHERE time_units > 0 GROUP BY order_number
            )
            SELECT
                g.order_number,
                o.order_date,
                a.charge_type,
                v.license_plate as kennzeichen,
                ROUND(g.stempel_min) as gestempelt_min,
                ROUND(a.abrechn_min) as abgerechnet_min,
                ROUND(g.stempel_min - a.abrechn_min) as verlust_min
            FROM gestempelt g
            JOIN abgerechnet a ON g.order_number = a.order_number
            JOIN orders o ON g.order_number = o.number
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            WHERE g.stempel_min > a.abrechn_min
              AND a.charge_type = 60
              {subsidiary_filter}
            ORDER BY (g.stempel_min - a.abrechn_min) DESC
            LIMIT 20
            '''

            cur.execute(query_top, params)
            top_verluste = cur.fetchall()
            cur.close()

            # Statistiken berechnen
            total_gestempelt = sum(float(r['gestempelt_std'] or 0) for r in by_type)
            total_abgerechnet = sum(float(r['abgerechnet_std'] or 0) for r in by_type)
            total_differenz = sum(float(r['differenz_std'] or 0) for r in by_type)

            # Ergebnis formatieren
            result_by_type = []
            for r in by_type:
                ct = r['charge_type']
                result_by_type.append({
                    'charge_type': ct,
                    'charge_type_name': CHARGE_TYPES.get(ct, f'Typ {ct}'),
                    'anzahl_auftraege': r['anzahl_auftraege'],
                    'gestempelt_std': float(r['gestempelt_std'] or 0),
                    'abgerechnet_std': float(r['abgerechnet_std'] or 0),
                    'differenz_std': float(r['differenz_std'] or 0),
                    'differenz_pct': float(r['differenz_pct'] or 0),
                    'verlust_eur': round(float(r['differenz_std'] or 0) * 85, 0) if r['differenz_std'] and r['differenz_std'] > 0 else 0
                })

            return {
                'zeitraum_wochen': wochen,
                'statistik': {
                    'gestempelt_std': round(total_gestempelt, 1),
                    'abgerechnet_std': round(total_abgerechnet, 1),
                    'differenz_std': round(total_differenz, 1),
                    'verlust_eur': round(total_differenz * 85, 0) if total_differenz > 0 else 0,
                    'stundensatz': 85
                },
                'by_charge_type': result_by_type,
                'top_verluste_kulanz': [
                    {
                        'auftrag_nr': r['order_number'],
                        'datum': r['order_date'].isoformat() if r['order_date'] else None,
                        'kennzeichen': r['kennzeichen'],
                        'gestempelt_min': r['gestempelt_min'],
                        'abgerechnet_min': r['abgerechnet_min'],
                        'verlust_min': r['verlust_min'],
                        'verlust_eur': round(r['verlust_min'] / 60 * 85, 0)
                    }
                    for r in top_verluste
                ]
            }

    @staticmethod
    def get_drive_briefing(betrieb: Optional[int] = None) -> Dict[str, Any]:
        """
        DRIVE Tages-Briefing: 5-Minuten-Überblick für Werkstattleiter.

        TAG 152: Migriert aus werkstatt_live_api.py
        Vorher: 165 LOC | Nachher: ~140 LOC

        Enthält:
        - Aktuelle Auslastung mit ML-Korrektur
        - Offene Aufträge (heute fällig)
        - Problemfälle (LG < 70%)
        - Kulanz-Warnung

        Args:
            betrieb: Filter nach Betrieb (1, 2, 3), None = alle

        Returns:
            Dict mit Briefing-Daten für Dashboard
        """
        import json
        from pathlib import Path

        # ML-Korrekturfaktoren laden
        corrections_file = Path('/opt/greiner-portal/data/ml/labour_corrections.json')
        corrections = {'G': 1.24, 'W': 0.94, 'I': 1.08}  # Defaults
        if corrections_file.exists():
            try:
                with open(corrections_file) as f:
                    data = json.load(f)
                    corrections = data.get('by_type', corrections)
            except Exception:
                pass

        heute = date.today()

        with locosoft_session() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # 1. Aktuelle Stempelungen (heute) - über employees_history für Betrieb-Filter
            betrieb_filter_eh = ""
            params = [heute]
            if betrieb:
                betrieb_filter_eh = "AND eh.subsidiary = %s"
                params.append(betrieb)

            cur.execute(f"""
                SELECT
                    COUNT(DISTINCT t.employee_number) as aktive_mechaniker,
                    COALESCE(SUM(CASE WHEN t.end_time IS NULL THEN 1 ELSE 0 END), 0) as aktuell_gestempelt,
                    COALESCE(SUM(t.duration_minutes), 0) as gestempelt_minuten
                FROM times t
                JOIN employees_history eh ON t.employee_number = eh.employee_number AND eh.is_latest_record = true
                WHERE DATE(t.start_time) = %s
                  AND t.type = 2
                  AND t.order_number > 31
                  {betrieb_filter_eh}
            """, params)
            stempelung = cur.fetchone()

            # 2. Verrechnet heute (aus labours - is_invoiced = true)
            betrieb_filter_l = ""
            params2 = [heute]
            if betrieb:
                betrieb_filter_l = "AND l.subsidiary = %s"
                params2.append(betrieb)

            cur.execute(f"""
                SELECT COALESCE(SUM(l.time_units), 0) as verrechnet_aw
                FROM labours l
                JOIN orders o ON l.order_number = o.number
                WHERE DATE(o.order_date) = %s
                  AND l.is_invoiced = true
                  {betrieb_filter_l}
            """, params2)
            verrechnet = cur.fetchone()

            # 3. Offene Aufträge (heute fällig) - has_open_positions = true
            betrieb_filter_o = ""
            params3 = [heute]
            if betrieb:
                betrieb_filter_o = "AND o.subsidiary = %s"
                params3.append(betrieb)

            cur.execute(f"""
                SELECT COUNT(*) as anzahl
                FROM orders o
                WHERE DATE(COALESCE(o.estimated_outbound_time, o.order_date)) = %s
                  AND o.has_open_positions = true
                  AND o.vehicle_number IS NOT NULL
                  {betrieb_filter_o}
            """, params3)
            offene = cur.fetchone()

            # 4. Problemfälle (letzte 7 Tage, LG < 70%)
            params4 = [heute]
            if betrieb:
                params4.append(betrieb)

            cur.execute(f"""
                SELECT COUNT(*) as anzahl
                FROM (
                    SELECT
                        o.number,
                        COALESCE(SUM(l.time_units), 0) as verrechnet,
                        COALESCE(SUM(t.duration_minutes), 0) as gestempelt
                    FROM orders o
                    LEFT JOIN labours l ON o.number = l.order_number
                    LEFT JOIN times t ON o.number = t.order_number AND t.type = 2
                    WHERE DATE(o.order_date) >= %s - INTERVAL '7 days'
                      AND o.has_open_positions = false
                      {betrieb_filter_o}
                    GROUP BY o.number
                    HAVING COALESCE(SUM(t.duration_minutes), 0) > 30
                       AND CASE WHEN COALESCE(SUM(t.duration_minutes), 0) > 0
                           THEN (COALESCE(SUM(l.time_units), 0) * 60) / COALESCE(SUM(t.duration_minutes), 0) * 100
                           ELSE 0 END < 70
                ) sub
            """, params4)
            probleme = cur.fetchone()

            # 5. Kulanz-Verluste (letzte 7 Tage) - charge_type 60 oder 61
            cur.execute(f"""
                SELECT
                    COALESCE(SUM(l.time_units), 0) as kulanz_aw
                FROM labours l
                JOIN orders o ON l.order_number = o.number
                WHERE o.order_date >= CURRENT_DATE - INTERVAL '7 days'
                  AND l.charge_type IN (60, 61)
                  {betrieb_filter_l}
            """, params2)
            kulanz = cur.fetchone()

            cur.close()

        # Berechnung mit ML-Korrektur
        gestempelt_h = (stempelung['gestempelt_minuten'] or 0) / 60.0
        verrechnet_aw = verrechnet['verrechnet_aw'] or 0

        # Durchschnitts-Korrekturfaktor
        avg_correction = (corrections.get('G', 1.24) + corrections.get('W', 0.94) + corrections.get('I', 1.08)) / 3.0
        verrechnet_korrigiert = verrechnet_aw * avg_correction

        auslastung = 0
        if gestempelt_h > 0:
            auslastung = (verrechnet_korrigiert / gestempelt_h) * 100

        return {
            'datum': heute.isoformat(),
            'betrieb': betrieb,
            'stempelung': {
                'aktive_mechaniker': stempelung['aktive_mechaniker'] or 0,
                'aktuell_gestempelt': stempelung['aktuell_gestempelt'] or 0,
                'gestempelt_stunden': round(gestempelt_h, 2)
            },
            'verrechnet': {
                'aw_roh': round(verrechnet_aw, 1),
                'aw_korrigiert': round(verrechnet_korrigiert, 1),
                'korrektur_faktor': round(avg_correction, 2)
            },
            'auslastung': {
                'prozent': round(auslastung, 1),
                'ziel': 110,
                'status': 'gut' if auslastung >= 100 else 'warnung' if auslastung >= 80 else 'kritisch'
            },
            'offene_auftraege': offene['anzahl'] or 0,
            'problemfaelle': probleme['anzahl'] or 0,
            'kulanz_7_tage': {
                'aw': round(kulanz['kulanz_aw'] or 0, 1),
                'eur': round((kulanz['kulanz_aw'] or 0) * 85, 0)
            }
        }

    @staticmethod
    def get_drive_kapazitaet(wochen: int = 4, betrieb: Optional[int] = None) -> Dict[str, Any]:
        """
        DRIVE Kapazitätsplanung: Verfügbare vs. genutzte Kapazität.

        TAG 152: Migriert aus werkstatt_live_api.py
        Vorher: 210 LOC | Nachher: ~180 LOC

        Berechnet:
        - Soll-Kapazität (Mitarbeiter × 8h × Arbeitstage)
        - Abwesenheiten (Urlaub, Krank, Schulung)
        - Effektive Kapazität
        - Genutzte Kapazität (Stempelzeiten)

        Args:
            wochen: Anzahl Wochen zurück (default: 4)
            betrieb: Filter nach Betrieb (1, 2, 3), None = alle

        Returns:
            Dict mit Kapazitäts-Analyse
        """
        heute = date.today()
        von = heute - timedelta(weeks=wochen)

        with locosoft_session() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Betrieb-Filter
            betrieb_filter_eh = ""
            if betrieb:
                betrieb_filter_eh = "AND eh.subsidiary = %s"

            # 1. Aktive Produktiv-Mitarbeiter (5000-5999)
            params1 = [betrieb] if betrieb else []
            cur.execute(f"""
                SELECT
                    COUNT(DISTINCT eh.employee_number) as anzahl_mechaniker
                FROM employees_history eh
                WHERE eh.employee_number BETWEEN 5000 AND 5999
                  AND eh.is_latest_record = true
                  AND eh.leave_date IS NULL
                  {betrieb_filter_eh}
            """, params1)
            mitarbeiter = cur.fetchone()
            anzahl = mitarbeiter['anzahl_mechaniker'] or 0

            # 2. Arbeitstage im Zeitraum (Mo-Fr)
            arbeitstage = 0
            current = von
            while current <= heute:
                if current.weekday() < 5:  # Mo-Fr
                    arbeitstage += 1
                current += timedelta(days=1)

            # 3. Stempelzeiten im Zeitraum
            params_t = [von, heute]
            if betrieb:
                params_t.append(betrieb)

            cur.execute(f"""
                SELECT
                    COUNT(DISTINCT t.employee_number) as aktive_mechaniker,
                    COALESCE(SUM(t.duration_minutes), 0) as gestempelt_minuten,
                    COUNT(DISTINCT DATE(t.start_time)) as tage_mit_stempelung
                FROM times t
                JOIN employees_history eh ON t.employee_number = eh.employee_number AND eh.is_latest_record = true
                WHERE DATE(t.start_time) BETWEEN %s AND %s
                  AND t.type = 2
                  AND t.order_number > 31
                  {betrieb_filter_eh}
            """, params_t)
            stempel = cur.fetchone()

            # 4. Abwesenheiten aus absence_calendar
            params_abw = [von, heute]
            if betrieb:
                params_abw.append(betrieb)

            cur.execute(f"""
                SELECT
                    COALESCE(SUM(ac.day_contingent), 0) as abwesenheit_tage
                FROM absence_calendar ac
                JOIN employees_history eh ON ac.employee_number = eh.employee_number AND eh.is_latest_record = true
                WHERE ac.date BETWEEN %s AND %s
                  AND eh.employee_number BETWEEN 5000 AND 5999
                  {betrieb_filter_eh}
            """, params_abw)
            abwesend = cur.fetchone()
            abwesenheit_tage = float(abwesend['abwesenheit_tage'] or 0)

            cur.close()

        # Berechnungen
        soll_stunden = anzahl * 8 * arbeitstage
        gestempelt_stunden = (stempel['gestempelt_minuten'] or 0) / 60.0

        # Abwesenheit berechnet
        abwesenheit_stunden = abwesenheit_tage * 8
        abwesenheit_faktor = abwesenheit_stunden / soll_stunden if soll_stunden > 0 else 0.10
        effektive_kapazitaet = soll_stunden - abwesenheit_stunden

        auslastung = 0
        if effektive_kapazitaet > 0:
            auslastung = (gestempelt_stunden / effektive_kapazitaet) * 100

        return {
            'zeitraum': {
                'von': von.isoformat(),
                'bis': heute.isoformat(),
                'wochen': wochen,
                'arbeitstage': arbeitstage
            },
            'betrieb': betrieb,
            'mitarbeiter': {
                'gesamt': anzahl,
                'aktiv_gestempelt': stempel['aktive_mechaniker'] or 0
            },
            'kapazitaet': {
                'soll_stunden': round(soll_stunden, 0),
                'abwesenheit_stunden': round(abwesenheit_stunden, 1),
                'abwesenheit_prozent': round(abwesenheit_faktor * 100, 1),
                'effektiv_stunden': round(effektive_kapazitaet, 0)
            },
            'nutzung': {
                'gestempelt_stunden': round(gestempelt_stunden, 1),
                'tage_mit_stempelung': stempel['tage_mit_stempelung'] or 0
            },
            'auslastung': {
                'prozent': round(auslastung, 1),
                'status': 'gut' if auslastung >= 80 else 'warnung' if auslastung >= 60 else 'kritisch'
            }
        }

    @staticmethod
    def get_mechaniker_stempelzeit_analyse(
        mechaniker_nr: int,
        von: Optional[date] = None,
        bis: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Detaillierte Tagesanalyse der Stempelzeiten für einen Mechaniker.
        
        Liefert für jeden Tag im Zeitraum:
        - Datum
        - Anwesend (Stunden)
        - Bezahlt (Stunden, Standard: 8h pro Tag)
        - Differenz (Anwesend - Bezahlt)
        - Anwesenheitsgrad (%)
        
        Args:
            mechaniker_nr: Mechaniker-Nummer (z.B. 5020)
            von: Startdatum (optional, default: 1. des aktuellen Monats)
            bis: Enddatum (optional, default: heute)
            
        Returns:
            Dict mit:
            - mechaniker_nr: Mechaniker-Nummer
            - mechaniker_name: Name
            - zeitraum: {'von': str, 'bis': str}
            - tage: Liste mit Tagesdaten
            - zusammenfassung: Gesamtwerte
        """
        if von is None:
            heute = date.today()
            von = heute.replace(day=1)
        if bis is None:
            bis = date.today()
        
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Mechaniker-Info
            cursor.execute("""
                SELECT name, subsidiary
                FROM employees_history
                WHERE employee_number = %s
                  AND is_latest_record = true
            """, (mechaniker_nr,))
            mechaniker_info = cursor.fetchone()
            
            if not mechaniker_info:
                return {
                    'error': f'Mechaniker {mechaniker_nr} nicht gefunden'
                }
            
            # Tagesweise Anwesenheit (type=1)
            cursor.execute("""
                SELECT
                    DATE(start_time) as datum,
                    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as anwesend_min
                FROM times
                WHERE employee_number = %s
                  AND type = 1
                  AND end_time IS NOT NULL
                  AND DATE(start_time) >= %s
                  AND DATE(start_time) <= %s
                GROUP BY DATE(start_time)
                ORDER BY DATE(start_time)
            """, (mechaniker_nr, von, bis))
            
            tage_daten = cursor.fetchall()
            
            # Tagesweise Stempelzeit (type=2) für zusätzliche Info
            cursor.execute("""
                SELECT
                    DATE(start_time) as datum,
                    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as stempelzeit_min
                FROM (
                    SELECT DISTINCT ON (employee_number, start_time, end_time)
                        employee_number,
                        start_time,
                        end_time,
                        EXTRACT(EPOCH FROM (end_time - start_time)) / 60 as minuten
                    FROM times
                    WHERE employee_number = %s
                      AND type = 2
                      AND end_time IS NOT NULL
                      AND DATE(start_time) >= %s
                      AND DATE(start_time) <= %s
                ) dedup
                GROUP BY DATE(start_time)
                ORDER BY DATE(start_time)
            """, (mechaniker_nr, von, bis))
            
            stempelzeit_daten = {row['datum']: row['stempelzeit_min'] for row in cursor.fetchall()}
            
            # Tagesliste aufbauen
            tage_liste = []
            gesamt_anwesend_h = 0.0
            gesamt_bezahlt_h = 0.0
            
            for tag_row in tage_daten:
                datum = tag_row['datum']
                anwesend_min = float(tag_row['anwesend_min'] or 0)
                anwesend_h = anwesend_min / 60.0
                
                # Bezahlt: Standard 8h pro Tag
                bezahlt_h = 8.0
                
                differenz_h = anwesend_h - bezahlt_h
                anwesenheitsgrad = (anwesend_h / bezahlt_h * 100) if bezahlt_h > 0 else None
                
                stempelzeit_min = stempelzeit_daten.get(datum, 0)
                stempelzeit_h = stempelzeit_min / 60.0 if stempelzeit_min else 0
                
                tage_liste.append({
                    'datum': datum.isoformat() if isinstance(datum, date) else str(datum),
                    'anwesend_h': round(anwesend_h, 2),
                    'bezahlt_h': round(bezahlt_h, 2),
                    'differenz_h': round(differenz_h, 2),
                    'anwesenheitsgrad': round(anwesenheitsgrad, 1) if anwesenheitsgrad else None,
                    'stempelzeit_h': round(stempelzeit_h, 2)
                })
                
                gesamt_anwesend_h += anwesend_h
                gesamt_bezahlt_h += bezahlt_h
            
            # Zusammenfassung
            gesamt_anwesenheitsgrad = (gesamt_anwesend_h / gesamt_bezahlt_h * 100) if gesamt_bezahlt_h > 0 else None
            
            return {
                'mechaniker_nr': mechaniker_nr,
                'mechaniker_name': mechaniker_info['name'],
                'betrieb': mechaniker_info['subsidiary'],
                'zeitraum': {
                    'von': von.isoformat(),
                    'bis': bis.isoformat()
                },
                'tage': tage_liste,
                'zusammenfassung': {
                    'anzahl_tage': len(tage_liste),
                    'gesamt_anwesend_h': round(gesamt_anwesend_h, 2),
                    'gesamt_bezahlt_h': round(gesamt_bezahlt_h, 2),
                    'gesamt_differenz_h': round(gesamt_anwesend_h - gesamt_bezahlt_h, 2),
                    'gesamt_anwesenheitsgrad': round(gesamt_anwesenheitsgrad, 1) if gesamt_anwesenheitsgrad else None
            }
        }

    @staticmethod
    def get_mechaniker_stempelzeit_analyse(
        mechaniker_nr: int,
        von: Optional[date] = None,
        bis: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Detaillierte Tagesanalyse der Stempelzeiten für einen Mechaniker.
        
        Liefert für jeden Tag im Zeitraum:
        - Datum
        - Anwesend (Stunden)
        - Bezahlt (Stunden, Standard: 8h pro Tag)
        - Differenz (Anwesend - Bezahlt)
        - Anwesenheitsgrad (%)
        
        Args:
            mechaniker_nr: Mechaniker-Nummer (z.B. 5020)
            von: Startdatum (optional, default: 1. des aktuellen Monats)
            bis: Enddatum (optional, default: heute)
            
        Returns:
            Dict mit:
            - mechaniker_nr: Mechaniker-Nummer
            - mechaniker_name: Name
            - zeitraum: {'von': str, 'bis': str}
            - tage: Liste mit Tagesdaten
            - zusammenfassung: Gesamtwerte
        """
        if von is None:
            heute = date.today()
            von = heute.replace(day=1)
        if bis is None:
            bis = date.today()
        
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Mechaniker-Info
            cursor.execute("""
                SELECT name, subsidiary
                FROM employees_history
                WHERE employee_number = %s
                  AND is_latest_record = true
            """, (mechaniker_nr,))
            mechaniker_info = cursor.fetchone()
            
            if not mechaniker_info:
                return {
                    'error': f'Mechaniker {mechaniker_nr} nicht gefunden'
                }
            
            # Tagesweise Anwesenheit (type=1)
            cursor.execute("""
                SELECT
                    DATE(start_time) as datum,
                    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as anwesend_min
                FROM times
                WHERE employee_number = %s
                  AND type = 1
                  AND end_time IS NOT NULL
                  AND DATE(start_time) >= %s
                  AND DATE(start_time) <= %s
                GROUP BY DATE(start_time)
                ORDER BY DATE(start_time)
            """, (mechaniker_nr, von, bis))
            
            tage_daten = cursor.fetchall()
            
            # Tagesweise Stempelzeit (type=2) für zusätzliche Info
            cursor.execute("""
                SELECT
                    DATE(start_time) as datum,
                    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as stempelzeit_min
                FROM (
                    SELECT DISTINCT ON (employee_number, start_time, end_time)
                        employee_number,
                        start_time,
                        end_time,
                        EXTRACT(EPOCH FROM (end_time - start_time)) / 60 as minuten
                    FROM times
                    WHERE employee_number = %s
                      AND type = 2
                      AND end_time IS NOT NULL
                      AND DATE(start_time) >= %s
                      AND DATE(start_time) <= %s
                ) dedup
                GROUP BY DATE(start_time)
                ORDER BY DATE(start_time)
            """, (mechaniker_nr, von, bis))
            
            stempelzeit_daten = {row['datum']: row['stempelzeit_min'] for row in cursor.fetchall()}
            
            # Tagesliste aufbauen
            tage_liste = []
            gesamt_anwesend_h = 0.0
            gesamt_bezahlt_h = 0.0
            
            for tag_row in tage_daten:
                datum = tag_row['datum']
                anwesend_min = float(tag_row['anwesend_min'] or 0)
                anwesend_h = anwesend_min / 60.0
                
                # Bezahlt: Standard 8h pro Tag
                bezahlt_h = 8.0
                
                differenz_h = anwesend_h - bezahlt_h
                anwesenheitsgrad = (anwesend_h / bezahlt_h * 100) if bezahlt_h > 0 else None
                
                stempelzeit_min = stempelzeit_daten.get(datum, 0)
                stempelzeit_h = stempelzeit_min / 60.0 if stempelzeit_min else 0
                
                tage_liste.append({
                    'datum': datum.isoformat() if isinstance(datum, date) else str(datum),
                    'anwesend_h': round(anwesend_h, 2),
                    'bezahlt_h': round(bezahlt_h, 2),
                    'differenz_h': round(differenz_h, 2),
                    'anwesenheitsgrad': round(anwesenheitsgrad, 1) if anwesenheitsgrad else None,
                    'stempelzeit_h': round(stempelzeit_h, 2)
                })
                
                gesamt_anwesend_h += anwesend_h
                gesamt_bezahlt_h += bezahlt_h
            
            # Zusammenfassung
            gesamt_anwesenheitsgrad = (gesamt_anwesend_h / gesamt_bezahlt_h * 100) if gesamt_bezahlt_h > 0 else None
            
            return {
                'mechaniker_nr': mechaniker_nr,
                'mechaniker_name': mechaniker_info['name'],
                'betrieb': mechaniker_info['subsidiary'],
                'zeitraum': {
                    'von': von.isoformat(),
                    'bis': bis.isoformat()
                },
                'tage': tage_liste,
                'zusammenfassung': {
                    'anzahl_tage': len(tage_liste),
                    'gesamt_anwesend_h': round(gesamt_anwesend_h, 2),
                    'gesamt_bezahlt_h': round(gesamt_bezahlt_h, 2),
                    'gesamt_differenz_h': round(gesamt_anwesend_h - gesamt_bezahlt_h, 2),
                    'gesamt_anwesenheitsgrad': round(gesamt_anwesenheitsgrad, 1) if gesamt_anwesenheitsgrad else None
                }
            }


    @staticmethod
    def get_alle_mitarbeiter_stempelzeit_analyse(
        von: Optional[date] = None,
        bis: Optional[date] = None,
        betrieb: Optional[int] = None,
        nur_aktive: bool = True
    ) -> Dict[str, Any]:
        """
        Stempelzeit-Analyse für ALLE Mitarbeiter (nicht nur Mechaniker).
        
        Args:
            von: Startdatum (optional, default: 1. des aktuellen Monats)
            bis: Enddatum (optional, default: heute)
            betrieb: Betrieb-ID (optional, 1=DEG, 2=HYU, 3=LAN)
            nur_aktive: Nur aktive Mitarbeiter (default: True)
            
        Returns:
            Dict mit:
            - zeitraum: {'von': str, 'bis': str}
            - mitarbeiter: Liste mit Mitarbeiter-Daten
            - zusammenfassung: Gesamtwerte
        """
        if von is None:
            heute = date.today()
            von = heute.replace(day=1)
        if bis is None:
            bis = date.today()
        
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Alle Mitarbeiter holen
            query_mitarbeiter = """
                SELECT DISTINCT
                    eh.employee_number,
                    eh.name,
                    eh.subsidiary,
                    CASE eh.subsidiary
                        WHEN 1 THEN 'Deggendorf'
                        WHEN 2 THEN 'Hyundai'
                        WHEN 3 THEN 'Landau'
                    END as betrieb_name
                FROM employees_history eh
                WHERE eh.is_latest_record = true
            """
            params_mitarbeiter = []
            
            if nur_aktive:
                query_mitarbeiter += " AND (eh.leave_date IS NULL OR eh.leave_date > %s)"
                params_mitarbeiter.append(bis)
            
            if betrieb:
                query_mitarbeiter += " AND eh.subsidiary = %s"
                params_mitarbeiter.append(betrieb)
            
            query_mitarbeiter += " ORDER BY eh.subsidiary, eh.name"
            
            cursor.execute(query_mitarbeiter, params_mitarbeiter)
            alle_mitarbeiter = cursor.fetchall()
            
            # Für jeden Mitarbeiter die Stempelzeit-Analyse durchführen
            mitarbeiter_liste = []
            gesamt_anwesend_h = 0.0
            gesamt_bezahlt_h = 0.0
            
            for ma in alle_mitarbeiter:
                ma_nr = ma['employee_number']
                
                # Tagesweise Anwesenheit (type=1) MIT Pausen-Berücksichtigung
                cursor.execute("""
                    SELECT
                        DATE(start_time) as datum,
                        MIN(start_time) as erster_start,
                        MAX(end_time) as letztes_ende,
                        SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as gestempelt_min,
                        EXTRACT(EPOCH FROM (MAX(end_time) - MIN(start_time)) / 60) as spanne_min
                    FROM times
                    WHERE employee_number = %s
                      AND type = 1
                      AND end_time IS NOT NULL
                      AND DATE(start_time) >= %s
                      AND DATE(start_time) <= %s
                    GROUP BY DATE(start_time)
                    ORDER BY DATE(start_time)
                """, (ma_nr, von, bis))
                
                tage_daten = cursor.fetchall()
                
                if not tage_daten:
                    # Keine Stempelzeiten im Zeitraum
                    continue
                
                # Tagesliste aufbauen
                tage_liste = []
                ma_anwesend_h = 0.0
                ma_bezahlt_h = 0.0
                
                for tag_row in tage_daten:
                    datum = tag_row['datum']
                    gestempelt_min = float(tag_row['gestempelt_min'] or 0)
                    spanne_min = float(tag_row['spanne_min'] or 0)
                    
                    # Pausen = Spanne - Gestempelt (Lücken zwischen Stempelungen)
                    pause_min = max(0, spanne_min - gestempelt_min)
                    
                    # Anwesenheit = Gestempelt (ohne Pausen)
                    # Alternative: Anwesenheit = Spanne - Pause (wenn Pausen explizit abgezogen werden sollen)
                    anwesend_min = gestempelt_min
                    anwesend_h = anwesend_min / 60.0
                    
                    # Bezahlt: Standard 8h pro Tag
                    bezahlt_h = 8.0
                    
                    differenz_h = anwesend_h - bezahlt_h
                    anwesenheitsgrad = (anwesend_h / bezahlt_h * 100) if bezahlt_h > 0 else None
                    
                    tage_liste.append({
                        'datum': datum.isoformat() if isinstance(datum, date) else str(datum),
                        'anwesend_h': round(anwesend_h, 2),
                        'bezahlt_h': round(bezahlt_h, 2),
                        'differenz_h': round(differenz_h, 2),
                        'anwesenheitsgrad': round(anwesenheitsgrad, 1) if anwesenheitsgrad else None,
                        'pause_min': round(pause_min, 1),
                        'spanne_min': round(spanne_min, 1)
                    })
                    
                    ma_anwesend_h += anwesend_h
                    ma_bezahlt_h += bezahlt_h
                
                # Zusammenfassung pro Mitarbeiter
                ma_anwesenheitsgrad = (ma_anwesend_h / ma_bezahlt_h * 100) if ma_bezahlt_h > 0 else None
                
                mitarbeiter_liste.append({
                    'employee_number': ma_nr,
                    'name': ma['name'],
                    'betrieb': ma['subsidiary'],
                    'betrieb_name': ma['betrieb_name'],
                    'anzahl_tage': len(tage_liste),
                    'gesamt_anwesend_h': round(ma_anwesend_h, 2),
                    'gesamt_bezahlt_h': round(ma_bezahlt_h, 2),
                    'gesamt_differenz_h': round(ma_anwesend_h - ma_bezahlt_h, 2),
                    'anwesenheitsgrad': round(ma_anwesenheitsgrad, 1) if ma_anwesenheitsgrad else None,
                    'tage': tage_liste
                })
                
                gesamt_anwesend_h += ma_anwesend_h
                gesamt_bezahlt_h += ma_bezahlt_h
            
            # Gesamt-Zusammenfassung
            gesamt_anwesenheitsgrad = (gesamt_anwesend_h / gesamt_bezahlt_h * 100) if gesamt_bezahlt_h > 0 else None
            
            return {
                'zeitraum': {
                    'von': von.isoformat(),
                    'bis': bis.isoformat()
                },
                'mitarbeiter': mitarbeiter_liste,
                'zusammenfassung': {
                    'anzahl_mitarbeiter': len(mitarbeiter_liste),
                    'gesamt_anwesend_h': round(gesamt_anwesend_h, 2),
                    'gesamt_bezahlt_h': round(gesamt_bezahlt_h, 2),
                    'gesamt_differenz_h': round(gesamt_anwesend_h - gesamt_bezahlt_h, 2),
                    'gesamt_anwesenheitsgrad': round(gesamt_anwesenheitsgrad, 1) if gesamt_anwesenheitsgrad else None
                }
            }

    @staticmethod
    def get_automatisch_verteilte_stempelungen(
        betrieb: Optional[int] = None,
        tage_zurueck: int = 30,
        min_lines: int = 3
    ) -> Dict[str, Any]:
        """
        Identifiziert Aufträge mit automatisch verteilten Stempelungen (Mehrfachstempelungen).
        
        Kriterien für automatisch verteilte Stempelungen:
        - Mehrere order_position_line zur gleichen Zeit (gleiche start_time, end_time)
        - Verschobene Positionen (z.B. Line 99 = Garantieposition)
        - Mindestens min_lines verschiedene Lines zur gleichen Zeit
        
        Diese Aufträge sollten vom Serviceleiter geprüft und ggf. manuell korrigiert werden.
        
        Args:
            betrieb: Betrieb-ID (1=DEGO, 2=DEGH, 3=LANO, None=alle)
            tage_zurueck: Wie viele Tage zurück (default: 30)
            min_lines: Mindestanzahl Lines für Mehrfachstempelung (default: 3)
        
        Returns:
            Dict mit 'auftraege' (Liste) und Metadaten
        
        Example:
            >>> data = WerkstattData.get_automatisch_verteilte_stempelungen(betrieb=1, tage_zurueck=14)
            >>> data['auftraege'][0]
            {'auftrag_nr': 39527, 'anzahl_mehrfachstempelungen': 1, 'max_lines': 4, ...}
        """
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Basis-Query: Finde Aufträge mit Mehrfachstempelungen
            query = """
                WITH mehrfachstempelungen AS (
                    SELECT 
                        t.employee_number,
                        t.order_number,
                        t.order_position,
                        t.start_time,
                        t.end_time,
                        COUNT(DISTINCT t.order_position_line) as anzahl_lines,
                        COUNT(*) as anzahl_eintraege,
                        EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 60.0 AS dauer_min,
                        STRING_AGG(DISTINCT t.order_position_line::text, ', ' ORDER BY t.order_position_line::text) as lines_liste,
                        BOOL_OR(t.order_position_line = 99) as hat_verschobene_position
                    FROM times t
                    WHERE t.type = 2
                      AND t.end_time IS NOT NULL
                      AND DATE(t.start_time) >= CURRENT_DATE - INTERVAL '%s days'
                    GROUP BY t.employee_number, t.order_number, t.order_position, t.start_time, t.end_time
                    HAVING COUNT(DISTINCT t.order_position_line) >= %s
                ),
                auftrag_aggregiert AS (
                    SELECT 
                        m.order_number,
                        COUNT(DISTINCT (m.order_position, m.start_time, m.end_time)) as anzahl_mehrfachstempelungen,
                        MAX(m.anzahl_lines) as max_lines,
                        SUM(m.dauer_min) as gesamt_dauer_min,
                        SUM(m.dauer_min * m.anzahl_lines) as potenzieller_st_anteil_min,
                        BOOL_OR(m.hat_verschobene_position) as hat_verschobene_positionen,
                        STRING_AGG(DISTINCT m.employee_number::text, ', ' ORDER BY m.employee_number::text) as mitarbeiter_liste
                    FROM mehrfachstempelungen m
                    GROUP BY m.order_number
                )
                SELECT 
                    a.order_number as auftrag_nr,
                    a.anzahl_mehrfachstempelungen,
                    a.max_lines,
                    ROUND(a.gesamt_dauer_min::numeric, 2) as gesamt_dauer_min,
                    ROUND(a.potenzieller_st_anteil_min::numeric, 2) as potenzieller_st_anteil_min,
                    ROUND((a.potenzieller_st_anteil_min / NULLIF(a.gesamt_dauer_min, 0))::numeric, 2) as ueberbewertungs_faktor,
                    a.hat_verschobene_positionen,
                    a.mitarbeiter_liste,
                    o.subsidiary as betrieb,
                    o.order_date as auftrag_datum,
                    v.license_plate as kennzeichen,
                    m.description as marke,
                    COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name) as kunde,
                    eh.name as serviceberater_name,
                    o.has_open_positions as ist_offen
                FROM auftrag_aggregiert a
                JOIN orders o ON a.order_number = o.number
                LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
                LEFT JOIN makes m ON v.make_number = m.make_number
                LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
                LEFT JOIN employees_history eh ON o.order_taking_employee_no = eh.employee_number
                    AND eh.is_latest_record = true
            """
            
            params = [tage_zurueck, min_lines]
            
            if betrieb is not None:
                query += " WHERE o.subsidiary = %s"
                params.append(int(betrieb))
            
            query += """
                ORDER BY a.potenzieller_st_anteil_min DESC, o.order_date DESC
                LIMIT 100
            """
            
            cursor.execute(query, params)
            auftraege = cursor.fetchall()
            
            # Für jeden Auftrag: Detail-Liste der Mehrfachstempelungen
            auftraege_mit_details = []
            for auftrag in auftraege:
                auftrag_nr = auftrag['auftrag_nr']
                
                # Hole Details zu den Mehrfachstempelungen
                cursor.execute("""
                    SELECT 
                        t.employee_number,
                        mech.name as mechaniker_name,
                        t.order_position,
                        t.start_time,
                        t.end_time,
                        COUNT(DISTINCT t.order_position_line) as anzahl_lines,
                        EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 60.0 AS dauer_min,
                        STRING_AGG(DISTINCT t.order_position_line::text, ', ' ORDER BY t.order_position_line::text) as lines_liste,
                        BOOL_OR(t.order_position_line = 99) as hat_verschobene_position
                    FROM times t
                    LEFT JOIN employees_history mech ON t.employee_number = mech.employee_number
                        AND mech.is_latest_record = true
                    WHERE t.type = 2
                      AND t.end_time IS NOT NULL
                      AND t.order_number = %s
                    GROUP BY t.employee_number, mech.name, t.order_position, t.start_time, t.end_time
                    HAVING COUNT(DISTINCT t.order_position_line) >= %s
                    ORDER BY t.start_time DESC
                """, [auftrag_nr, min_lines])
                
                stempelungen_details = cursor.fetchall()
                
                auftrag_dict = dict(auftrag)
                auftrag_dict['stempelungen_details'] = [
                    {
                        'employee_number': s['employee_number'],
                        'mechaniker_name': s['mechaniker_name'],
                        'order_position': s['order_position'],
                        'start_time': s['start_time'].isoformat() if s['start_time'] else None,
                        'end_time': s['end_time'].isoformat() if s['end_time'] else None,
                        'anzahl_lines': s['anzahl_lines'],
                        'dauer_min': float(s['dauer_min']) if s['dauer_min'] else 0,
                        'lines_liste': s['lines_liste'],
                        'hat_verschobene_position': s['hat_verschobene_position']
                    }
                    for s in stempelungen_details
                ]
                
                auftraege_mit_details.append(auftrag_dict)
            
            return {
                'success': True,
                'auftraege': auftraege_mit_details,
                'anzahl': len(auftraege_mit_details),
                'filter': {
                    'betrieb': betrieb,
                    'tage_zurueck': tage_zurueck,
                    'min_lines': min_lines
                }
            }


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
