"""
KST-Planung Bottom-Up - Basis-Planung pro Kostenstelle
======================================================
TAG 165: Bottom-Up Planung für konkrete, greifbare Ziele

Berechnet realistische Basis-Ziele pro KST basierend auf:
- Werkstatt: Stunden × Stundensatz
- NW/GW: Stück × Durchschnittspreis
- Teile/Sonstige: Historischer Durchschnitt × Wachstumsfaktor
"""

from typing import Dict, Any, Optional
from api.db_connection import get_db
from api.db_utils import locosoft_session
from api.serviceberater_api import SB_DEGGENDORF, SB_LANDAU


def get_anzahl_mitarbeiter(bereich: str, standort: int) -> int:
    """
    Ermittelt Anzahl aktiver Mitarbeiter pro Bereich und Standort.
    
    Args:
        bereich: 'Werkstatt', 'NW', 'GW', etc.
        standort: 1=DEG, 2=HYU, 3=LAN
    
    Returns:
        Anzahl Mitarbeiter
    """
    conn = get_db()
    cursor = conn.cursor()
    
    if bereich == 'Werkstatt':
        # Serviceberater aus Config
        if standort in [1, 2]:
            return len(SB_DEGGENDORF)
        elif standort == 3:
            return len(SB_LANDAU)
        else:
            return len(SB_DEGGENDORF) + len(SB_LANDAU)
    
    elif bereich in ['NW', 'GW']:
        # Verkäufer aus employees Tabelle
        # Nur Mitarbeiter aus Verkaufs-Abteilungen zählen
        standort_filter = ""
        if standort == 1:
            standort_filter = "AND location = 'Deggendorf'"
        elif standort == 2:
            standort_filter = "AND location = 'Deggendorf'"  # Hyundai auch Deggendorf
        elif standort == 3:
            standort_filter = "AND location = 'Landau a.d. Isar'"
        
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM employees 
            WHERE active = 1
              AND department_name IN ('Verkauf', 'Verkauf NW', 'Verkauf GW', 'Disposition', 'Fahrzeuge')
              {standort_filter}
        """)
        count = cursor.fetchone()[0]
        conn.close()
        return max(count, 1)  # Mindestens 1
    
    else:
        # Teile/Sonstige: Keine spezifischen Mitarbeiter
        conn.close()
        return 1


def get_planungsparameter(geschaeftsjahr: str, bereich: str, standort: int) -> Dict[str, Any]:
    """
    Holt Planungsparameter aus kst_planung_parameter Tabelle.
    
    Args:
        geschaeftsjahr: z.B. '2025/26'
        bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
        standort: 1=DEG, 2=HYU, 3=LAN (oder 0 für Alle)
    
    Returns:
        Dict mit Planungsparametern
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Für Deggendorf: Standort 1 oder 2 → beide verwenden Standort 1 Parameter
    standort_param = 1 if standort in [1, 2] else standort
    
    cursor.execute("""
        SELECT stunden_pro_sb, stundensatz, auslastung_ziel,
               stueck_pro_vk, durchschnittspreis, marge_ziel,
               wachstumsfaktor
        FROM kst_planung_parameter
        WHERE geschaeftsjahr = %s 
          AND bereich = %s 
          AND standort = %s
    """, (geschaeftsjahr, bereich, standort_param))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'stunden_pro_sb': float(row[0] or 0),
            'stundensatz': float(row[1] or 0),
            'auslastung_ziel': float(row[2] or 0),
            'stueck_pro_vk': float(row[3] or 0),
            'durchschnittspreis': float(row[4] or 0),
            'marge_ziel': float(row[5] or 0),
            'wachstumsfaktor': float(row[6] or 1.0)
        }
    
    # Fallback: Default-Werte
    defaults = {
        'Werkstatt': {
            'stunden_pro_sb': 120,
            'stundensatz': 150,
            'auslastung_ziel': 85
        },
        'NW': {
            'stueck_pro_vk': 5,
            'durchschnittspreis': 30000,
            'marge_ziel': 8.0
        },
        'GW': {
            'stueck_pro_vk': 3,
            'durchschnittspreis': 25000,
            'marge_ziel': 6.0
        },
        'Teile': {
            'wachstumsfaktor': 1.05
        },
        'Sonstige': {
            'wachstumsfaktor': 1.0
        }
    }
    
    return defaults.get(bereich, {})


def get_historischer_durchschnitt(bereich: str, standort: int, monate: int = 12) -> Dict[str, float]:
    """
    Berechnet historischen Durchschnitts-Umsatz pro Bereich.
    
    Args:
        bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
        standort: 1=DEG, 2=HYU, 3=LAN
        monate: Anzahl Monate für Durchschnitt (default: 12)
    
    Returns:
        Dict mit 'umsatz' und 'db1' Durchschnitt
    """
    # Bereichs-Konten-Mapping
    bereich_konten = {
        'NW': (810000, 819999),
        'GW': (820000, 829999),
        'Teile': (830000, 839999),
        'Werkstatt': (840000, 849999),
        'Sonstige': (860000, 869999)
    }
    
    if bereich not in bereich_konten:
        return {'umsatz': 0, 'db1': 0}
    
    konto_von, konto_bis = bereich_konten[bereich]
    
    # Standort-Filter
    standort_filter = ""
    if standort == 1:  # Deggendorf Opel
        standort_filter = "AND subsidiary_to_company_ref = 1 AND branch_number = 1"
    elif standort == 2:  # Hyundai
        standort_filter = "AND subsidiary_to_company_ref = 2"
    elif standort == 3:  # Landau
        standort_filter = "AND subsidiary_to_company_ref = 1 AND branch_number = 3"
    elif standort in [1, 2]:  # Deggendorf kombiniert
        standort_filter = "AND (subsidiary_to_company_ref = 1 AND branch_number = 1) OR (subsidiary_to_company_ref = 2)"
    
    with locosoft_session() as conn:
        cursor = conn.cursor()
        
        # Letzte N Monate
        cursor.execute(f"""
            SELECT 
                SUM(CASE WHEN nominal_account_number BETWEEN {konto_von} AND {konto_bis} 
                    THEN posted_value ELSE 0 END) / 100.0 as umsatz,
                (SUM(CASE WHEN nominal_account_number BETWEEN {konto_von} AND {konto_bis} 
                    THEN posted_value ELSE 0 END) - 
                 SUM(CASE WHEN nominal_account_number BETWEEN {konto_von - 100000} AND {konto_bis - 100000}
                    THEN posted_value ELSE 0 END)) / 100.0 as db1
            FROM journal_accountings
            WHERE nominal_account_number BETWEEN {konto_von} AND {konto_bis}
              {standort_filter}
              AND accounting_date >= CURRENT_DATE - INTERVAL '{monate} months'
        """)
        
        row = cursor.fetchone()
        
        if row and row[0]:
            umsatz_gesamt = float(row[0])
            db1_gesamt = float(row[1] or 0)
            
            return {
                'umsatz': umsatz_gesamt / monate,
                'db1': db1_gesamt / monate
            }
    
    return {'umsatz': 0, 'db1': 0}


def get_basis_planung_pro_kst(geschaeftsjahr: str, bereich: str, 
                               monat: int, standort: int) -> Dict[str, Any]:
    """
    Berechnet Basis-Planung (Bottom-Up) pro KST.
    
    Args:
        geschaeftsjahr: z.B. '2025/26'
        bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
        monat: GJ-Monat (1-12)
        standort: 1=DEG, 2=HYU, 3=LAN
    
    Returns:
        Dict mit:
        - umsatz_basis: Basis-Umsatz-Ziel (EUR)
        - db1_basis: Basis-DB1-Ziel (EUR)
        - stueck_basis: Stück-Ziel (nur für NW/GW)
        - stunden_basis: Stunden-Ziel (nur für Werkstatt)
        - parameter: Planungsparameter
        - anzahl_mitarbeiter: Anzahl Mitarbeiter
    """
    # Planungsparameter laden
    params = get_planungsparameter(geschaeftsjahr, bereich, standort)
    anzahl_mitarbeiter = get_anzahl_mitarbeiter(bereich, standort)
    
    result = {
        'umsatz_basis': 0.0,
        'db1_basis': 0.0,
        'stueck_basis': 0,
        'stunden_basis': 0,
        'parameter': params,
        'anzahl_mitarbeiter': anzahl_mitarbeiter
    }
    
    # Bereichs-spezifische Berechnung
    if bereich == 'Werkstatt':
        # Werkstatt: Stunden × Stundensatz
        stunden_pro_sb = params.get('stunden_pro_sb', 120)
        stundensatz = params.get('stundensatz', 150)
        
        stunden_gesamt = stunden_pro_sb * anzahl_mitarbeiter
        umsatz_basis = stunden_gesamt * stundensatz
        db1_basis = umsatz_basis * 0.55  # 55% Marge Werkstatt
        
        result.update({
            'umsatz_basis': round(umsatz_basis, 2),
            'db1_basis': round(db1_basis, 2),
            'stunden_basis': int(stunden_gesamt)
        })
    
    elif bereich == 'NW':
        # NW: Stück × Durchschnittspreis
        stueck_pro_vk = params.get('stueck_pro_vk', 5)
        durchschnittspreis = params.get('durchschnittspreis', 30000)
        marge = params.get('marge_ziel', 8.0) / 100
        
        stueck_gesamt = int(stueck_pro_vk * anzahl_mitarbeiter)
        umsatz_basis = stueck_gesamt * durchschnittspreis
        db1_basis = umsatz_basis * marge
        
        result.update({
            'umsatz_basis': round(umsatz_basis, 2),
            'db1_basis': round(db1_basis, 2),
            'stueck_basis': stueck_gesamt
        })
    
    elif bereich == 'GW':
        # GW: Stück × Durchschnittspreis
        stueck_pro_vk = params.get('stueck_pro_vk', 3)
        durchschnittspreis = params.get('durchschnittspreis', 25000)
        marge = params.get('marge_ziel', 6.0) / 100
        
        stueck_gesamt = int(stueck_pro_vk * anzahl_mitarbeiter)
        umsatz_basis = stueck_gesamt * durchschnittspreis
        db1_basis = umsatz_basis * marge
        
        result.update({
            'umsatz_basis': round(umsatz_basis, 2),
            'db1_basis': round(db1_basis, 2),
            'stueck_basis': stueck_gesamt
        })
    
    elif bereich in ['Teile', 'Sonstige']:
        # Teile/Sonstige: Historischer Durchschnitt × Wachstumsfaktor
        wachstumsfaktor = params.get('wachstumsfaktor', 1.0)
        historisch = get_historischer_durchschnitt(bereich, standort, monate=12)
        
        umsatz_basis = historisch['umsatz'] * wachstumsfaktor
        db1_basis = historisch['db1'] * wachstumsfaktor
        
        result.update({
            'umsatz_basis': round(umsatz_basis, 2),
            'db1_basis': round(db1_basis, 2)
        })
    
    return result

