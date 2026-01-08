"""
Gewinnplanungstool V2 - KST 2 (GW) Data Module
===============================================
TAG 169: Neues Gewinnplanungstool mit Standzeit und Zinskosten

SSOT für GW-Planung:
- Vorjahreswerte aus BWA (loco_journal_accountings)
- Stückzahlen aus Locosoft dealer_vehicles
- Standzeit aus Locosoft dealer_vehicles
- Zinskosten-Berechnung: Lagerwert × Zinssatz × (Standzeit / 365)

Impact-Analyse:
- Standzeit-Reduktion → Zinskosten-Ersparnis
- Zinskosten-Ersparnis → DB2-Impact
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from decimal import Decimal

from api.db_utils import db_session, locosoft_session, row_to_dict
from api.db_connection import convert_placeholders

logger = logging.getLogger(__name__)

# =============================================================================
# KONSTANTEN
# =============================================================================

# Zinssatz für Zinskosten-Berechnung (5% p.a.)
ZINSSATZ_JAHR = 0.05

# Standort-Mapping
STANDORT_NAMEN = {
    1: 'Deggendorf',
    2: 'Hyundai DEG',
    3: 'Landau'
}

# =============================================================================
# VORJAHRESWERTE LADEN (BWA - SSOT)
# =============================================================================

def lade_vorjahr_gw(
    standort: int,
    geschaeftsjahr: str,
    monat: Optional[int] = None,
    nur_stellantis: bool = False
) -> Dict[str, Any]:
    """
    Lädt Vorjahreswerte für GW aus BWA (SSOT).
    
    Args:
        standort: 1, 2, oder 3
        geschaeftsjahr: z.B. '2025/26'
        monat: 1-12 (GJ-Monat) oder None für ganzes Geschäftsjahr
    
    Returns:
        dict: Vorjahreswerte (Umsatz, DB1, DB2, Stück, Standzeit, Zinskosten)
    """
    # Geschäftsjahr parsen
    gj_start_jahr = int(geschaeftsjahr.split('/')[0])
    vj_gj_start = gj_start_jahr - 1
    
    # Zeitraum bestimmen
    if monat is None:
        # Ganzes Geschäftsjahr (Sep bis Aug)
        vj_von = f"{vj_gj_start}-09-01"
        vj_bis = f"{vj_gj_start + 1}-09-01"
    else:
        # GJ-Monat zu Kalendermonat konvertieren
        if monat <= 4:
            kal_monat = monat + 8
            kal_jahr = vj_gj_start
        else:
            kal_monat = monat - 4
            kal_jahr = vj_gj_start + 1
        
        vj_von = f"{kal_jahr}-{kal_monat:02d}-01"
        if kal_monat == 12:
            vj_bis = f"{kal_jahr+1}-01-01"
        else:
            vj_bis = f"{kal_jahr}-{kal_monat+1:02d}-01"
    
    result = {
        'umsatz': 0,
        'db1': 0,
        'db2': 0,
        'stueck': 0,
        'standzeit': 0,
        'zinskosten': 0,
        'lagerwert': 0
    }
    
    try:
        # 1. Umsatz, DB1, DB2 aus BWA (SSOT)
        with db_session() as conn:
            cursor = conn.cursor()
            
            # BWA-Filter für GW (820000-829999)
            # WICHTIG: Verwende build_firma_standort_filter für Konsistenz mit BWA v2
            from api.controlling_api import build_firma_standort_filter
            
            if standort == 1:
                if nur_stellantis:
                    # Opel DEG: Nur Stellantis (ohne Hyundai)
                    firma_filter_umsatz, firma_filter_einsatz, _, _ = build_firma_standort_filter('1', '1')
                else:
                    # Deggendorf: Verwende 'deg-both' für beide Subsidiaries
                    firma_filter_umsatz, firma_filter_einsatz, _, _ = build_firma_standort_filter('0', 'deg-both')
            elif standort == 2:
                # Hyundai: Nur Hyundai
                firma_filter_umsatz, firma_filter_einsatz, _, _ = build_firma_standort_filter('2', '0')
            elif standort == 3:
                # Landau: Nur Stellantis Landau
                firma_filter_umsatz, firma_filter_einsatz, _, _ = build_firma_standort_filter('1', '2')
            else:
                # Gesamtbetrieb (alle)
                firma_filter_umsatz, firma_filter_einsatz, _, _ = build_firma_standort_filter('0', '0')
            
            # G&V-Abschlussbuchungen ausschließen
            guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
            
            # Umsatz (820000-829999) - identisch zu BWA v2 API
            # WICHTIG: Nutze die gleiche Logik wie _berechne_bereich_werte in controlling_api.py
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END
                ) / 100.0, 0) as umsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 820000 AND 829999
                  {firma_filter_umsatz}
                  {guv_filter}
            """), (vj_von, vj_bis))
            row = cursor.fetchone()
            result['umsatz'] = float(row_to_dict(row)['umsatz'] or 0) if row else 0
            
            # Einsatz (720000-729999) - identisch zu BWA v2 API
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END
                ) / 100.0, 0) as einsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 720000 AND 729999
                  {firma_filter_einsatz}
                  {guv_filter}
            """), (vj_von, vj_bis))
            row = cursor.fetchone()
            einsatz = float(row_to_dict(row)['einsatz'] or 0) if row else 0
            
            # DB1 = Umsatz - Einsatz (BWA-Logik)
            result['db1'] = result['umsatz'] - einsatz
            
            # Debug-Info (kann später entfernt werden)
            logger.info(f"GW DB1-Berechnung: Umsatz={result['umsatz']:,.2f}, Einsatz={einsatz:,.2f}, DB1={result['db1']:,.2f}")
            
            # Variable Kosten (BWA-Logik - identisch zu controlling_api.py)
            # WICHTIG: Korrekte Konten-Bereiche für Variable Kosten
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END
                ) / 100.0, 0) as variable
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND (
                    (nominal_account_number BETWEEN 415100 AND 415199)
                    OR (nominal_account_number BETWEEN 435500 AND 435599)
                    OR (nominal_account_number BETWEEN 455000 AND 456999
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                    OR (nominal_account_number BETWEEN 487000 AND 487099
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                    OR (nominal_account_number BETWEEN 491000 AND 497899)
                  )
                  AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'
                  {guv_filter}
            """), (vj_von, vj_bis))
            row = cursor.fetchone()
            variable = float(row_to_dict(row)['variable'] or 0) if row else 0
            
            # DB2 = DB1 - Variable Kosten
            result['db2'] = result['db1'] - variable
        
        # 2. Stückzahl aus Locosoft dealer_vehicles (SSOT)
        with locosoft_session() as conn_loco:
            cursor_loco = conn_loco.cursor()
            
            # Standort-Filter
            # WICHTIG: in_subsidiary für Bestand, out_subsidiary für Verkäufe
            if standort == 1:
                if nur_stellantis:
                    # Opel DEG: Nur Stellantis (subsidiary=1)
                    standort_filter_verkauf = "AND out_subsidiary = 1"
                    standort_filter_bestand = "AND in_subsidiary = 1"
                else:
                    # Deggendorf: Stellantis (subsidiary=1) + Hyundai (subsidiary=2)
                    standort_filter_verkauf = "AND (out_subsidiary = 1 OR out_subsidiary = 2)"
                    standort_filter_bestand = "AND (in_subsidiary = 1 OR in_subsidiary = 2)"
            elif standort == 2:
                standort_filter_verkauf = "AND out_subsidiary = 2"
                standort_filter_bestand = "AND in_subsidiary = 2"
            elif standort == 3:
                standort_filter_verkauf = "AND out_subsidiary = 1"
                standort_filter_bestand = "AND in_subsidiary = 1"
            else:
                standort_filter_verkauf = ""
                standort_filter_bestand = ""
            
            # Stückzahl (Verkaufte Fahrzeuge im Vorjahr)
            # TAG169: Angepasst an Global Cube - GW = D+G+L (Demo, Gebrauchtwagen, Leihfahrzeug)
            cursor_loco.execute(f"""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('G', 'D', 'L')
                  {standort_filter_verkauf}
            """, (vj_von, vj_bis))
            row = cursor_loco.fetchone()
            result['stueck'] = int(row[0] or 0) if row else 0
            
            # Standzeit des BESTANDES (nicht der verkauften Fahrzeuge!)
            # WICHTIG: Standzeit = Durchschnittliche Lagerdauer des aktuellen Bestands
            # Der Benutzer sagt: "der liegt leider momentan bei ca. 150 tagen"
            # TAG169: Angepasst an Global Cube - GW = D+G+L (Demo, Gebrauchtwagen, Leihfahrzeug)
            cursor_loco.execute(f"""
                SELECT AVG(CURRENT_DATE - COALESCE(in_arrival_date, created_date)) as standzeit
                FROM dealer_vehicles
                WHERE out_invoice_date IS NULL
                  AND dealer_vehicle_type IN ('G', 'D', 'L')
                  AND in_arrival_date IS NOT NULL
                  {standort_filter_bestand}
            """)
            row = cursor_loco.fetchone()
            result['standzeit'] = float(row[0] or 0) if row else 0
        
        # 3. Zinskosten berechnen (Vorjahr)
        if result['stueck'] > 0 and result['umsatz'] > 0:
            # Durchschnittlicher EK-Preis schätzen
            # EK = Umsatz - DB1 (vereinfacht)
            ek_pro_fzg = (result['umsatz'] - result['db1']) / result['stueck'] if result['stueck'] > 0 else 0
            lagerwert = result['stueck'] * ek_pro_fzg
            result['lagerwert'] = lagerwert
            result['zinskosten'] = lagerwert * ZINSSATZ_JAHR * (result['standzeit'] / 365) if result['standzeit'] > 0 else 0
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Vorjahreswerte GW: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return result


# =============================================================================
# PLANUNGS-BERECHNUNG
# =============================================================================

def berechne_gw_planung(
    planung_data: Dict[str, Any],
    vorjahr: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Berechnet GW-Planung mit Impact-Analyse.
    
    Args:
        planung_data: Planungswerte (7 Fragen)
        vorjahr: Vorjahreswerte (aus BWA)
    
    Returns:
        dict: Berechnete Werte + Impact-Analyse
    """
    # 1. Planungswerte extrahieren
    stueck = float(planung_data.get('plan_stueck', 0) or 0)
    bruttoertrag_pro_fzg = float(planung_data.get('plan_bruttoertrag_pro_fzg', 0) or 0)
    variable_kosten_pct = float(planung_data.get('plan_variable_kosten_pct', 0) or 0) / 100
    verkaufspreis = float(planung_data.get('plan_verkaufspreis', 0) or 0)
    standzeit_tage = int(planung_data.get('plan_standzeit_tage', 0) or 0)
    ek_preis = float(planung_data.get('plan_ek_preis', 0) or 0)
    zinssatz_pct = float(planung_data.get('plan_zinssatz_pct', 5.0) or 5.0) / 100
    
    # 2. Basis-Berechnung
    umsatz_plan = stueck * verkaufspreis
    bruttoertrag_plan = stueck * bruttoertrag_pro_fzg
    variable_kosten_plan = bruttoertrag_plan * variable_kosten_pct
    db1_plan = bruttoertrag_plan - variable_kosten_plan
    
    # 3. EK-Preis schätzen (falls nicht angegeben)
    if ek_preis == 0 and verkaufspreis > 0:
        # EK = VK - Bruttoertrag (vereinfacht)
        ek_preis = verkaufspreis - bruttoertrag_pro_fzg
    
    # 4. Lagerwert und Zinskosten
    lagerwert_plan = stueck * ek_preis
    zinskosten_plan = lagerwert_plan * zinssatz_pct * (standzeit_tage / 365) if standzeit_tage > 0 else 0
    
    # 5. Direkte Kosten (vereinfacht - aus Vorjahr übernommen)
    direkte_kosten_plan = vorjahr.get('db1', 0) - vorjahr.get('db2', 0) - vorjahr.get('zinskosten', 0)
    direkte_kosten_plan = direkte_kosten_plan * (stueck / vorjahr.get('stueck', 1)) if vorjahr.get('stueck', 0) > 0 else 0
    
    # 6. DB2 = DB1 - Direkte Kosten - Zinskosten
    db2_plan = db1_plan - direkte_kosten_plan - zinskosten_plan
    
    # 7. Impact-Analyse
    impact = berechne_impact_gw(
        planung_data, vorjahr,
        db1_plan, db2_plan, zinskosten_plan, lagerwert_plan
    )
    
    return {
        'umsatz_plan': round(umsatz_plan, 2),
        'einsatz_plan': round(umsatz_plan - bruttoertrag_plan, 2),
        'bruttoertrag_plan': round(bruttoertrag_plan, 2),
        'variable_kosten_plan': round(variable_kosten_plan, 2),
        'db1_plan': round(db1_plan, 2),
        'direkte_kosten_plan': round(direkte_kosten_plan, 2),
        'lagerwert_plan': round(lagerwert_plan, 2),
        'zinskosten_plan': round(zinskosten_plan, 2),
        'db2_plan': round(db2_plan, 2),
        'impact': impact
    }


# =============================================================================
# IMPACT-ANALYSE
# =============================================================================

def berechne_impact_gw(
    planung_data: Dict[str, Any],
    vorjahr: Dict[str, Any],
    db1_plan: float,
    db2_plan: float,
    zinskosten_plan: float,
    lagerwert_plan: float
) -> Dict[str, Any]:
    """
    Berechnet Impact von Standzeit- und Zinskosten-Änderungen.
    
    Returns:
        dict: Impact-Analyse (Standzeit, Zinskosten, Gesamt)
    """
    impact = {
        'standzeit': {},
        'zinskosten': {},
        'gesamt': {}
    }
    
    # Vorjahreswerte
    standzeit_vj = vorjahr.get('standzeit', 0)
    zinskosten_vj = vorjahr.get('zinskosten', 0)
    db1_vj = vorjahr.get('db1', 0)
    db2_vj = vorjahr.get('db2', 0)
    lagerwert_vj = vorjahr.get('lagerwert', 0)
    
    # Planungswerte
    standzeit_plan = int(planung_data.get('plan_standzeit_tage', 0) or 0)
    zinssatz_plan = float(planung_data.get('plan_zinssatz_pct', 5.0) or 5.0) / 100
    
    # 1. Standzeit-Impact
    if standzeit_vj > 0 and standzeit_plan > 0:
        standzeit_diff = standzeit_vj - standzeit_plan
        standzeit_verbesserung_pct = (standzeit_diff / standzeit_vj * 100) if standzeit_vj > 0 else 0
        
        # Zinskosten-Ersparnis durch Standzeit-Reduktion
        if lagerwert_vj > 0:
            zinskosten_ersparnis_standzeit = lagerwert_vj * ZINSSATZ_JAHR * (standzeit_diff / 365)
        else:
            zinskosten_ersparnis_standzeit = lagerwert_plan * zinssatz_plan * (standzeit_diff / 365)
        
        impact['standzeit'] = {
            'vj': round(standzeit_vj, 1),
            'plan': standzeit_plan,
            'differenz_tage': round(standzeit_diff, 1),
            'verbesserung_pct': round(standzeit_verbesserung_pct, 1),
            'zinskosten_ersparnis': round(zinskosten_ersparnis_standzeit, 2)
        }
    else:
        impact['standzeit'] = {
            'vj': standzeit_vj,
            'plan': standzeit_plan,
            'differenz_tage': 0,
            'verbesserung_pct': 0,
            'zinskosten_ersparnis': 0
        }
    
    # 2. Zinskosten-Impact (gesamt)
    zinskosten_diff = zinskosten_vj - zinskosten_plan
    zinskosten_ersparnis_pct = (zinskosten_diff / zinskosten_vj * 100) if zinskosten_vj > 0 else 0
    
    impact['zinskosten'] = {
        'vj': round(zinskosten_vj, 2),
        'plan': round(zinskosten_plan, 2),
        'differenz': round(zinskosten_diff, 2),
        'ersparnis_pct': round(zinskosten_ersparnis_pct, 1),
        'db2_impact': round(zinskosten_diff, 2)  # Zinskosten-Ersparnis = DB2-Impact
    }
    
    # 3. Gesamt-Impact
    db1_diff = db1_plan - db1_vj
    db2_diff = db2_plan - db2_vj
    
    impact['gesamt'] = {
        'db1_vj': round(db1_vj, 2),
        'db1_plan': round(db1_plan, 2),
        'db1_mehr': round(db1_diff, 2),
        'db1_mehr_pct': round((db1_diff / db1_vj * 100) if db1_vj > 0 else 0, 1),
        'db2_vj': round(db2_vj, 2),
        'db2_plan': round(db2_plan, 2),
        'db2_mehr': round(db2_diff, 2),
        'db2_mehr_pct': round((db2_diff / db2_vj * 100) if db2_vj > 0 else 0, 1),
        'zinskosten_ersparnis': round(zinskosten_diff, 2),
        'standzeit_ersparnis': round(impact['standzeit'].get('zinskosten_ersparnis', 0), 2)
    }
    
    return impact

