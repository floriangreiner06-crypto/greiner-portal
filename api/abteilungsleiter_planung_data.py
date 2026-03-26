"""
ABTEILUNGSLEITER-PLANUNG Data Module - SSOT für Bottom-Up Planung
==================================================================
TAG 165: Single Source of Truth für Abteilungsleiter-Planung (10 Fragen pro KST)

Architektur:
- Class-based Pattern (AbteilungsleiterPlanungData)
- Statische Methoden für wiederverwendbare Berechnungen
- Alle Business-Logik hier (SSOT)
- Nach Freigabe: Ziele in kst_ziele schreiben

Consumer:
- api/abteilungsleiter_planung_api.py (REST-Endpoints)
- routes/planung_routes.py (HTML-Routes)
- scripts/planung_reports.py (Reports, später)

Pattern: docs/DATENMODUL_PATTERN.md
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from decimal import Decimal

from api.db_connection import get_db
from api.db_utils import db_session, row_to_dict
from api.aufhol_logik import apply_aufhol_auf_kst_ziel, get_aufhol_beitrag_fuer_kst
from api.unternehmensplan_data import get_current_geschaeftsjahr

# SSOT: Standort-Namen
from api.standort_utils import STANDORT_NAMEN

logger = logging.getLogger(__name__)

# =============================================================================
# KONSTANTEN
# =============================================================================

# Zinssatz für Zinskosten-Berechnung (5% p.a.)
ZINSSATZ_JAHR = 0.05

# Bereichs-Mapping
BEREICH_NAMEN = {
    'NW': 'Neuwagen',
    'GW': 'Gebrauchtwagen',
    'Teile': 'Teile',
    'Werkstatt': 'Werkstatt',
    'Sonstige': 'Sonstige'
}

# STANDORT_NAMEN wird jetzt aus standort_utils importiert (SSOT)

# =============================================================================
# HILFSFUNKTIONEN: WERKSTATT-KPIs AUS werkstatt_data.py
# =============================================================================

def berechne_werkstatt_kpis_fuer_zeitraum(
    von_datum: str,
    bis_datum: str,
    standort: int
) -> Dict[str, float]:
    """
    Berechnet Werkstatt-KPIs (Produktivität, Leistungsgrad, Auslastung) 
    für einen Zeitraum aus werkstatt_data.py.
    
    Args:
        von_datum: Startdatum (YYYY-MM-DD)
        bis_datum: Enddatum (YYYY-MM-DD)
        standort: 1=DEG, 2=HYU, 3=LAN
    
    Returns:
        dict: {
            'produktivitaet': float (in %),
            'leistungsgrad': float (in %),
            'auslastung': float (in %),
            'stempelzeit': float (Minuten),
            'anwesenheit': float (Minuten),
            'aw': float,
            'verfuegbare_stunden': float
        }
    """
    from api.werkstatt_data import WerkstattData
    from datetime import datetime
    
    try:
        # Datum parsen
        von = datetime.strptime(von_datum, '%Y-%m-%d').date()
        bis = datetime.strptime(bis_datum, '%Y-%m-%d').date()
        
        # Betrieb aus Standort ableiten
        # Standort 1 = Deggendorf (Betrieb 1), Standort 2 = Hyundai DEG (Betrieb 2), Standort 3 = Landau (Betrieb 3)
        betrieb = standort
        
        # Mechaniker-Leistung aus werkstatt_data.py laden
        leistung_data = WerkstattData.get_mechaniker_leistung(
            von=von,
            bis=bis,
            betrieb=betrieb,
            inkl_ehemalige=False
        )
        
        gesamt = leistung_data.get('gesamt', {}) or {}
        
        # KPIs extrahieren (None-sicher: .get liefert sonst None bei vorhandenem Key)
        produktivitaet = gesamt.get('produktivitaet') or 0   # Bereits in %
        leistungsgrad = gesamt.get('leistungsgrad') or 0    # Bereits in %
        stempelzeit = gesamt.get('stempelzeit') or 0        # Minuten
        anwesenheit = gesamt.get('anwesenheit') or 0        # Minuten
        aw = gesamt.get('aw') or 0                          # AW
        
        # Auslastung berechnen: Anwesend / Verfügbare
        # Verfügbare Stunden = Anzahl Mechaniker × Arbeitstage × 8 Stunden
        anzahl_mechaniker = leistung_data.get('anzahl_mechaniker') or 0
        anzahl_tage = leistung_data.get('anzahl_tage') or 0
        
        if anzahl_tage > 0:
            # Verfügbare Stunden pro Mechaniker pro Tag (Standard: 8h)
            stunden_pro_tag = 8.0
            verfuegbare_stunden_gesamt = anzahl_mechaniker * anzahl_tage * stunden_pro_tag
            verfuegbare_minuten_gesamt = verfuegbare_stunden_gesamt * 60
            
            # Auslastung = Anwesenheit / Verfügbare
            if verfuegbare_minuten_gesamt > 0:
                auslastung = (anwesenheit / verfuegbare_minuten_gesamt) * 100
            else:
                auslastung = 0.0
        else:
            auslastung = 0.0
            verfuegbare_stunden_gesamt = 0.0
        
        return {
            'produktivitaet': round(produktivitaet, 1),
            'leistungsgrad': round(leistungsgrad, 1),
            'auslastung': round(auslastung, 1),
            'stempelzeit': round(stempelzeit, 0),
            'anwesenheit': round(anwesenheit, 0),
            'aw': round(aw, 1),
            'verfuegbare_stunden': round(verfuegbare_stunden_gesamt, 1)
        }
    
    except Exception as e:
        logger.error(f"Fehler beim Berechnen der Werkstatt-KPIs: {str(e)}")
        # Fallback: Placeholder-Werte
        return {
            'produktivitaet': 0.0,
            'leistungsgrad': 0.0,
            'auslastung': 0.0,
            'stempelzeit': 0.0,
            'anwesenheit': 0.0,
            'aw': 0.0,
            'verfuegbare_stunden': 0.0
        }


# =============================================================================
# HILFSFUNKTIONEN: IST-WERTE FÜR ABGELAUFENE MONATE
# =============================================================================

def ist_monat_abgelaufen(geschaeftsjahr: str, monat: int) -> bool:
    """
    Prüft ob ein Monat im Geschäftsjahr bereits abgelaufen ist.
    
    Args:
        geschaeftsjahr: z.B. '2025/26'
        monat: GJ-Monat (1=Sep, 2=Okt, ..., 12=Aug)
    
    Returns:
        True wenn Monat bereits abgelaufen, sonst False
    """
    from datetime import date
    
    heute = date.today()
    start_jahr = int(geschaeftsjahr.split('/')[0])
    
    # GJ-Monat zu Kalendermonat konvertieren
    if monat <= 4:  # Sep-Dez (Monate 1-4)
        kal_monat = monat + 8  # Sep=9, Okt=10, Nov=11, Dez=12
        kal_jahr = start_jahr
    else:  # Jan-Aug (Monate 5-12)
        kal_monat = monat - 4  # Jan=1, Feb=2, ..., Aug=8
        kal_jahr = start_jahr + 1
    
    # Prüfen ob Monat bereits vergangen
    if kal_jahr < heute.year:
        return True
    elif kal_jahr == heute.year and kal_monat < heute.month:
        return True
    else:
        return False


def lade_ist_werte_fuer_monat(
    geschaeftsjahr: str,
    monat: int,
    bereich: str,
    standort: int,
    konsolidiert: bool = False
) -> Dict[str, Any]:
    """
    Lädt IST-Werte aus Locosoft für einen abgelaufenen Monat.
    
    Args:
        geschaeftsjahr: z.B. '2025/26'
        monat: GJ-Monat (1-12)
        bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
        standort: 1, 2, oder 3
        konsolidiert: True = Service Deggendorf (Standort 1+2 zusammen), False = Normal
    
    Returns:
        dict: IST-Werte für Planung (analog zu Planungsdaten)
    """
    from api.db_utils import get_locosoft_connection
    from datetime import date
    
    # GJ-Monat zu Kalendermonat konvertieren
    start_jahr = int(geschaeftsjahr.split('/')[0])
    if monat <= 4:  # Sep-Dez
        kal_monat = monat + 8
        kal_jahr = start_jahr
    else:  # Jan-Aug
        kal_monat = monat - 4
        kal_jahr = start_jahr + 1
    
    von_datum = f"{kal_jahr}-{kal_monat:02d}-01"
    if kal_monat == 12:
        bis_datum = f"{kal_jahr+1}-01-01"
    else:
        bis_datum = f"{kal_jahr}-{kal_monat+1:02d}-01"
    
    result = {
        'umsatz_ist': 0,
        'db1_ist': 0,
        'db2_ist': 0,
        'stueck_ist': 0,
        'standzeit_ist': 0,
        'stunden_verkauft_ist': 0,
        'stundensatz_ist': 0,
        'lagerumschlag_ist': 0,
        'penner_quote_ist': 0,
        'servicegrad_ist': 0,
        'ist_quelle': 'locosoft'
    }
    
    try:
        # Standort-Filter
        # WICHTIG: Für Werkstatt, Teile, Sonstige keine Marken-Unterscheidung, nur Standort!
        # WICHTIG: Hyundai hat branch_number = 2, Stellantis Deggendorf hat branch_number = 1
        # TAG 177: Konsolidierte Ansicht unterstützen (Service Deggendorf = Standort 1+2)
        if bereich in ['Werkstatt', 'Teile', 'Sonstige']:
            # Werkstatt/Teile/Sonstige: Nur nach Standort filtern (Deggendorf oder Landau), nicht nach Marke
            if standort == 1:
                if konsolidiert:
                    # Service Deggendorf (konsolidiert): Beide Standorte zusammen
                    firma_filter_umsatz = "AND ((branch_number = 1 AND SUBSTRING(nominal_account_number::TEXT, 5, 1) = '1') OR (branch_number = 2 AND subsidiary_to_company_ref = 2))"
                    firma_filter_einsatz = "AND ((SUBSTRING(nominal_account_number::TEXT, 5, 1) = '1' AND subsidiary_to_company_ref = 1) OR (SUBSTRING(nominal_account_number::TEXT, 5, 1) = '2' AND subsidiary_to_company_ref = 2))"
                    subsidiary_filter = "AND (o.subsidiary = 1 OR o.subsidiary = 2)"  # Beide Firmen (für Locosoft-Tabellen)
                else:
                    # Deggendorf: Stellantis (branch=1, subsidiary_to_company_ref=1) + Hyundai (branch=2, subsidiary_to_company_ref=2)
                    firma_filter_umsatz = "AND ((branch_number = 1 AND SUBSTRING(nominal_account_number::TEXT, 5, 1) = '1') OR (branch_number = 2 AND subsidiary_to_company_ref = 2))"
                    firma_filter_einsatz = "AND ((SUBSTRING(nominal_account_number::TEXT, 5, 1) = '1' AND subsidiary_to_company_ref = 1) OR (SUBSTRING(nominal_account_number::TEXT, 5, 1) = '2' AND subsidiary_to_company_ref = 2))"
                    subsidiary_filter = "AND (o.subsidiary = 1 OR o.subsidiary = 2)"  # Beide Firmen (für Locosoft-Tabellen)
            elif standort == 3:
                # Landau: branch_number = 3 (nur Stellantis, Hyundai hat keinen Standort in Landau)
                firma_filter_umsatz = "AND branch_number = 3 AND subsidiary_to_company_ref = 1"
                firma_filter_einsatz = "AND SUBSTRING(nominal_account_number::TEXT, 5, 1) = '2' AND subsidiary_to_company_ref = 1"
                subsidiary_filter = "AND o.subsidiary = 3"  # Landau: subsidiary=3 (LANO location)
            else:
                # Standort 2 (Hyundai) oder andere: Alle Werte
                firma_filter_umsatz = ""
                firma_filter_einsatz = ""
                subsidiary_filter = ""
        else:
            # Andere Bereiche: Normale Standort-Filterung
            if standort == 1:
                if konsolidiert:
                    # Service Deggendorf (konsolidiert): Beide Standorte zusammen
                    firma_filter_umsatz = "AND (branch_number = 1 OR branch_number = 2 OR (nominal_account_number BETWEEN 810000 AND 819999 AND (SUBSTRING(nominal_account_number::TEXT, 5, 1) = '1' OR SUBSTRING(nominal_account_number::TEXT, 5, 1) = '2')))"
                    firma_filter_einsatz = "AND (SUBSTRING(nominal_account_number::TEXT, 5, 1) = '1' OR SUBSTRING(nominal_account_number::TEXT, 5, 1) = '2')"
                    subsidiary_filter = "AND (subsidiary = 1 OR subsidiary = 2)"
                else:
                    firma_filter_umsatz = "AND (branch_number = 1 OR (nominal_account_number BETWEEN 810000 AND 819999 AND SUBSTRING(nominal_account_number::TEXT, 5, 1) = '1'))"
                    firma_filter_einsatz = "AND (SUBSTRING(nominal_account_number::TEXT, 5, 1) = '1')"
                    subsidiary_filter = "AND subsidiary = 1"
            elif standort == 2:
                firma_filter_umsatz = "AND subsidiary = 2"
                firma_filter_einsatz = "AND subsidiary = 2"
                subsidiary_filter = "AND subsidiary = 2"
            elif standort == 3:
                firma_filter_umsatz = "AND branch_number = 3 AND subsidiary_to_company_ref = 1"
                firma_filter_einsatz = "AND SUBSTRING(nominal_account_number::TEXT, 5, 1) = '2' AND subsidiary_to_company_ref = 1"
                subsidiary_filter = "AND subsidiary = 3"  # Landau: subsidiary=3 (LANO location)
            else:
                firma_filter_umsatz = ""
                firma_filter_einsatz = ""
                subsidiary_filter = ""
        
        # 1. Umsatz und DB1 aus DRIVE Portal (loco_journal_accountings)
        conn = get_db()
        cursor = conn.cursor()
        
        # Bereichs-spezifische Konten
        if bereich == 'NW':
            umsatz_konten = "BETWEEN 810000 AND 819999"
            einsatz_konten = "BETWEEN 710000 AND 719999"
        elif bereich == 'GW':
            umsatz_konten = "BETWEEN 820000 AND 829999"
            einsatz_konten = "BETWEEN 720000 AND 729999"
        elif bereich == 'Teile':
            umsatz_konten = "BETWEEN 830000 AND 839999"
            einsatz_konten = "BETWEEN 730000 AND 739999"
        elif bereich == 'Werkstatt':
            umsatz_konten = "BETWEEN 840000 AND 849999"
            einsatz_konten = "BETWEEN 740000 AND 749999"
        elif bereich == 'Sonstige':
            umsatz_konten = "BETWEEN 860000 AND 869999"
            einsatz_konten = "BETWEEN 760000 AND 769999"
        else:
            conn.close()
            return result
        
        # Umsatz
        cursor.execute(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END
            ) / 100.0, 0) as umsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number {umsatz_konten}
              {firma_filter_umsatz}
        """, (von_datum, bis_datum))
        row = cursor.fetchone()
        result['umsatz_ist'] = float(row[0] or 0) if row else 0
        
        # Einsatz
        cursor.execute(f"""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END
            ) / 100.0, 0) as einsatz
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number {einsatz_konten}
              {firma_filter_einsatz}
        """, (von_datum, bis_datum))
        row = cursor.fetchone()
        einsatz = float(row[0] or 0) if row else 0
        
        # DB1 = Umsatz - Einsatz
        result['db1_ist'] = result['umsatz_ist'] - einsatz
        result['db2_ist'] = result['db1_ist']  # Vereinfacht (DB2 = DB1 - direkte Kosten)
        
        conn.close()
        
        # 2. Locosoft-spezifische Daten
        conn_loco = get_locosoft_connection()
        cursor_loco = conn_loco.cursor()
        
        if bereich in ['NW', 'GW']:
            # Stückzahl
            # NW: dealer_vehicle_type IN ('N', 'V') - Neuwagen + Vorführwagen
            # GW: dealer_vehicle_type IN ('G', 'D') - Gebrauchtwagen + Demo
            if bereich == 'NW':
                typ_filter = "dealer_vehicle_type IN ('N', 'V')"
            else:  # GW
                typ_filter = "dealer_vehicle_type IN ('G', 'D')"
            
            # Standort-Filter für dealer_vehicles: out_subsidiary verwenden
            # TAG 177: Konsolidierte Ansicht unterstützen
            from api.standort_utils import build_consolidated_filter
            standort_filter = build_consolidated_filter(standort, konsolidiert, filter_type='verkauf')
            
            cursor_loco.execute(f"""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND {typ_filter}
                  {standort_filter}
            """, (von_datum, bis_datum))
            row = cursor_loco.fetchone()
            result['stueck_ist'] = int(row[0] or 0) if row else 0
            
            # Durchschnittliche Standzeit (nur wenn Stückzahl > 0)
            if result['stueck_ist'] > 0:
                cursor_loco.execute(f"""
                    SELECT AVG(out_invoice_date - in_arrival_date) as avg_standzeit
                    FROM dealer_vehicles
                    WHERE out_invoice_date >= %s AND out_invoice_date < %s
                      AND out_invoice_date IS NOT NULL
                      AND in_arrival_date IS NOT NULL
                      AND {typ_filter}
                      {standort_filter}
                """, (von_datum, bis_datum))
                row = cursor_loco.fetchone()
                if row and row[0]:
                    result['standzeit_ist'] = int(row[0] or 0)
                else:
                    result['standzeit_ist'] = 0
            else:
                result['standzeit_ist'] = 0
        
        elif bereich == 'Werkstatt':
            # Stunden verkauft (verrechnet) - über invoices JOIN
            # TAG 177: Konsolidierte Filter für orders verwenden
            from api.standort_utils import build_consolidated_filter
            orders_filter = build_consolidated_filter(standort, konsolidiert, filter_type='orders')
            cursor_loco.execute(f"""
                SELECT COALESCE(SUM(l.time_units), 0) as aw_verkauft
                FROM labours l
                JOIN invoices i ON l.invoice_number = i.invoice_number 
                    AND l.invoice_type = i.invoice_type
                JOIN orders o ON l.order_number = o.number
                WHERE i.invoice_date >= %s AND i.invoice_date < %s
                  AND l.is_invoiced = true
                  AND i.is_canceled = false
                  {orders_filter}
            """, (von_datum, bis_datum))
            row = cursor_loco.fetchone()
            aw_verkauft = float(row[0] or 0) if row else 0
            # AW zu Stunden umrechnen: 1 AW = 6 Minuten = 0.1 Stunden
            result['stunden_verkauft_ist'] = aw_verkauft / 10.0
            
            # Stundensatz = Umsatz / Stunden (nicht AW!)
            if result['stunden_verkauft_ist'] > 0:
                result['stundensatz_ist'] = result['umsatz_ist'] / result['stunden_verkauft_ist']
            else:
                result['stundensatz_ist'] = 0.0
            
            # Werkstatt-KPIs aus werkstatt_data.py laden
            kpis = berechne_werkstatt_kpis_fuer_zeitraum(von_datum, bis_datum, standort)
            result['produktivitaet_ist'] = kpis.get('produktivitaet', 105.0)
            result['leistungsgrad_ist'] = kpis.get('leistungsgrad', 90.0)
            result['auslastung_ist'] = kpis.get('auslastung', 75.0)
        
        elif bereich == 'Teile':
            # Lagerumschlag berechnen (wenn Lagerwert bekannt)
            # Lagerumschlag = Umsatz / Lagerwert
            # Für jetzt: Placeholder (wird später aus teile_data.py geladen)
            if result['umsatz_ist'] > 0:
                # Annahme: Lagerwert = Umsatz / 4 (4x Umschlag)
                lagerwert_geschätzt = result['umsatz_ist'] / 4
                result['lagerumschlag_ist'] = 4.0  # Default
            else:
                result['lagerumschlag_ist'] = 0.0
            
            # TODO: Penner-Quote, Servicegrad aus teile_data.py laden
            result['penner_quote_ist'] = 18.0  # Default
            result['servicegrad_ist'] = 95.0  # Default
        
        conn_loco.close()
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der IST-Werte: {str(e)}")
    
    return result

# =============================================================================
# ABTEILUNGSLEITER-PLANUNG DATA CLASS
# =============================================================================

class AbteilungsleiterPlanungData:
    """
    Single Source of Truth für Abteilungsleiter-Planung.
    
    Bereiche:
    - NW/GW: Stück, Bruttoertrag, Standzeit, Zinskosten
    - Werkstatt: Stunden, Produktivität, Leistungsgrad, Auslastung
    - Teile: Umsatz, Lagerumschlag, Penner-Quote, Servicegrad
    - Impact-Analyse: Standzeit, Produktivität, Lagerumschlag
    - Vorjahres-Referenz: Automatisch laden
    - Hybrid-Berechnung: Basis (Bottom-Up) + Aufhol (Top-Down)
    """

    # =========================================================================
    # NEUWAGEN / GEBRAUCHTWAGEN PLANUNG
    # =========================================================================

    @staticmethod
    def berechne_nw_gw_planung(
        planung_id: Optional[int] = None,
        geschaeftsjahr: Optional[str] = None,
        monat: Optional[int] = None,
        bereich: str = 'NW',
        standort: int = 1,
        planung_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Berechnet NW/GW-Planung aus 10 Fragen.
        
        Args:
            planung_id: ID der Planung (optional, für Update)
            geschaeftsjahr: z.B. '2025/26'
            monat: 1-12
            bereich: 'NW' oder 'GW'
            standort: 1, 2, oder 3
            planung_data: Dict mit Planungsdaten (10 Fragen)
        
        Returns:
            dict: {
                'umsatz_basis': float,
                'db1_basis': float,
                'db2_basis': float,
                'zinskosten': float,
                'direkte_kosten': float,
                'impact': dict,
                'vorjahr': dict
            }
        """
        if not planung_data:
            planung_data = {}
        
        # 1. Basis-Berechnung
        stueck = planung_data.get('plan_stueck', 0) or 0
        bruttoertrag_pro_fzg = float(planung_data.get('plan_bruttoertrag_pro_fzg', 0) or 0)
        variable_kosten_prozent = float(planung_data.get('plan_variable_kosten_prozent', 0) or 0) / 100
        verkaufspreis = float(planung_data.get('plan_verkaufspreis', 0) or 0)
        
        # Umsatz = Stück × Verkaufspreis
        umsatz_basis = stueck * verkaufspreis
        
        # Bruttoertrag = Stück × Bruttoertrag pro Fzg
        bruttoertrag = stueck * bruttoertrag_pro_fzg
        
        # Variable Kosten = Bruttoertrag × Variable Kosten %
        variable_kosten = bruttoertrag * variable_kosten_prozent
        
        # DB1 = Bruttoertrag - Variable Kosten
        db1_basis = bruttoertrag - variable_kosten
        
        # 2. Direkte Kosten
        fertigmachen = float(planung_data.get('plan_fertigmachen_pro_fzg', 0) or 0) * stueck
        werbung = float(planung_data.get('plan_werbung_jahr', 0) or 0) / 12  # Pro Monat
        kulanz = float(planung_data.get('plan_kulanz_jahr', 0) or 0) / 12
        training = float(planung_data.get('plan_training_jahr', 0) or 0) / 12
        
        direkte_kosten = fertigmachen + werbung + kulanz + training
        
        # 3. Zinskosten (Standzeit)
        standzeit_tage = int(planung_data.get('plan_standzeit_tage', 0) or 0)
        ek_preis = float(planung_data.get('plan_ek_preis', 0) or 0)
        
        if ek_preis == 0:
            # Fallback: EK = VK × (1 - Marge)
            marge = (db1_basis / umsatz_basis * 100) if umsatz_basis > 0 else 0
            ek_preis = verkaufspreis * (1 - marge / 100)
        
        lagerwert = stueck * ek_preis
        zinskosten = lagerwert * ZINSSATZ_JAHR * (standzeit_tage / 365)
        
        # DB2 = DB1 - Direkte Kosten - Zinskosten
        db2_basis = db1_basis - direkte_kosten - zinskosten
        
        # 4. Vorjahres-Referenz laden
        vorjahr = AbteilungsleiterPlanungData._lade_vorjahr_referenz(
            bereich, standort, monat, geschaeftsjahr
        )
        
        # 5. Impact-Analyse
        impact = AbteilungsleiterPlanungData._berechne_standzeit_impact(
            standzeit_tage,
            vorjahr.get('standzeit', 0),
            lagerwert,
            vorjahr.get('lagerwert', 0)
        )
        
        return {
            'umsatz_basis': round(umsatz_basis, 2),
            'db1_basis': round(db1_basis, 2),
            'db2_basis': round(db2_basis, 2),
            'zinskosten': round(zinskosten, 2),
            'direkte_kosten': round(direkte_kosten, 2),
            'bruttoertrag': round(bruttoertrag, 2),
            'variable_kosten': round(variable_kosten, 2),
            'lagerwert': round(lagerwert, 2),
            'impact': impact,
            'vorjahr': vorjahr
        }

    # =========================================================================
    # WERKSTATT PLANUNG
    # =========================================================================

    @staticmethod
    def berechne_werkstatt_planung(
        planung_id: Optional[int] = None,
        geschaeftsjahr: Optional[str] = None,
        monat: Optional[int] = None,
        standort: int = 1,
        planung_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Berechnet Werkstatt-Planung aus 10 Fragen.
        
        Args:
            planung_id: ID der Planung (optional)
            geschaeftsjahr: z.B. '2025/26'
            monat: 1-12
            standort: 1, 2, oder 3
            planung_data: Dict mit Planungsdaten (10 Fragen)
        
        Returns:
            dict: {
                'umsatz_basis': float,
                'db1_basis': float,
                'stunden_verkauft': float,
                'impact': dict,
                'vorjahr': dict
            }
        """
        if not planung_data:
            planung_data = {}
        
        # 1. Basis-Parameter
        anzahl_sb = int(planung_data.get('plan_anzahl_sb', 0) or 0)
        stundensatz = float(planung_data.get('plan_stundensatz', 0) or 0)
        produktivitaet = float(planung_data.get('plan_produktivitaet', 0) or 0) / 100
        leistungsgrad = float(planung_data.get('plan_leistungsgrad', 0) or 0) / 100
        # TAG 169: float() verwenden für Dezimalwerte (z.B. 8.5), dann runden
        anzahl_mechaniker = round(float(planung_data.get('plan_anzahl_mechaniker', 0) or 0), 1)  # NEU: Frage 5
        db1_marge = float(planung_data.get('plan_db1_marge', 0) or 0) / 100
        
        # 2. Verfügbare Stunden (pro Monat)
        # Annahme: 22 Werktage × 8 Stunden = 176 Stunden pro Mechaniker/Monat
        stunden_verfuegbar_pro_mechaniker_pro_monat = 176
        stunden_verfuegbar_pro_monat = anzahl_mechaniker * stunden_verfuegbar_pro_mechaniker_pro_monat
        
        # 3. Anwesende Stunden = Verfügbare (alle Mechaniker sind anwesend)
        stunden_anwesend_pro_monat = stunden_verfuegbar_pro_monat
        
        # 4. Stempelzeit = Anwesend × Produktivität
        stunden_gestempelt_pro_monat = stunden_anwesend_pro_monat * produktivitaet
        
        # 5. Verkaufte Stunden = Gestempelt × Leistungsgrad
        stunden_verkauft_pro_monat = stunden_gestempelt_pro_monat * leistungsgrad
        
        # TAG 169: Auf Geschäftsjahr hochrechnen (12 Monate)
        stunden_verkauft_jahr = stunden_verkauft_pro_monat * 12
        
        # 6. Umsatz = Verkaufte Stunden (Jahr) × Stundensatz
        umsatz_basis = stunden_verkauft_jahr * stundensatz
        
        # 7. DB1 = Umsatz × DB1-Marge
        db1_basis = umsatz_basis * db1_marge
        
        # 8. Vorjahres-Referenz laden
        vorjahr = AbteilungsleiterPlanungData._lade_vorjahr_referenz(
            'Werkstatt', standort, monat, geschaeftsjahr
        )
        
        # 9. Impact-Analyse (mit Vorjahres-Daten für detaillierte Berechnung)
        # Auslastung aus Mechaniker-Anzahl berechnen (für Impact-Berechnung)
        anzahl_mechaniker_vj = vorjahr.get('anzahl_mechaniker', 0)
        if anzahl_mechaniker_vj > 0:
            stunden_verfuegbar_vj = anzahl_mechaniker_vj * 176
            auslastung_vj = (vorjahr.get('anwesenheit', 0) / 60) / stunden_verfuegbar_vj * 100 if stunden_verfuegbar_vj > 0 else 0
        else:
            auslastung_vj = vorjahr.get('auslastung', 0)
        
        # Auslastung Plan aus Mechaniker-Anzahl berechnen
        auslastung_plan = 100.0  # Wenn Mechaniker eingegeben, sind sie 100% verfügbar
        
        # Vorjahres-Stunden auf Jahr hochrechnen (für Vergleich)
        stunden_verkauft_vj_jahr = vorjahr.get('stunden_verkauft', 0) * 12 if vorjahr.get('stunden_verkauft', 0) > 0 else 0
        
        impact = AbteilungsleiterPlanungData._berechne_werkstatt_impact(
            produktivitaet * 100,
            leistungsgrad * 100,
            auslastung_plan,
            stundensatz,
            vorjahr.get('produktivitaet', 0),
            vorjahr.get('leistungsgrad', 0),
            auslastung_vj,
            vorjahr.get('stundensatz', 0),
            stunden_verkauft_jahr,  # TAG 169: Jahr statt Monat
            stunden_verkauft_vj_jahr,  # TAG 169: Jahr statt Monat
            db1_marge,
            vorjahr_data=vorjahr  # Vorjahres-Daten für detaillierte Berechnung
        )
        
        return {
            'umsatz_basis': round(umsatz_basis, 2),
            'db1_basis': round(db1_basis, 2),
            'stunden_verkauft': round(stunden_verkauft_jahr, 2),  # TAG 169: Jahr statt Monat
            'stunden_anwesend': round(stunden_anwesend_pro_monat * 12, 2),  # TAG 169: Auf Jahr hochgerechnet
            'stunden_gestempelt': round(stunden_gestempelt_pro_monat * 12, 2),  # TAG 169: Auf Jahr hochgerechnet
            'anzahl_mechaniker': anzahl_mechaniker,  # TAG 169: Für Rückgabe
            'impact': impact,
            'vorjahr': vorjahr
        }

    # =========================================================================
    # TEILE PLANUNG
    # =========================================================================

    @staticmethod
    def berechne_teile_planung(
        planung_id: Optional[int] = None,
        geschaeftsjahr: Optional[str] = None,
        monat: Optional[int] = None,
        standort: int = 1,
        planung_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Berechnet Teile-Planung aus 10 Fragen.
        
        Args:
            planung_id: ID der Planung (optional)
            geschaeftsjahr: z.B. '2025/26'
            monat: 1-12
            standort: 1, 2, oder 3
            planung_data: Dict mit Planungsdaten (10 Fragen)
        
        Returns:
            dict: {
                'umsatz_basis': float,
                'db1_basis': float,
                'db2_basis': float,
                'lagerwert': float,
                'zinskosten_lager': float,
                'impact': dict,
                'vorjahr': dict
            }
        """
        if not planung_data:
            planung_data = {}
        
        # 1. Basis-Parameter
        umsatz_jahr = float(planung_data.get('plan_umsatz', 0) or 0)
        umsatz_basis = umsatz_jahr / 12  # Pro Monat
        marge_prozent = float(planung_data.get('plan_marge_prozent', 0) or 0) / 100
        lagerumschlag = float(planung_data.get('plan_lagerumschlag', 0) or 0)
        penner_quote = float(planung_data.get('plan_penner_quote', 0) or 0) / 100
        servicegrad = float(planung_data.get('plan_servicegrad', 0) or 0) / 100
        direkte_kosten = float(planung_data.get('plan_direkte_kosten', 0) or 0) / 12  # Pro Monat
        
        # 2. DB1 = Umsatz × Marge
        db1_basis = umsatz_basis * marge_prozent
        
        # 3. Lagerwert = Umsatz / Lagerumschlag
        lagerwert = umsatz_basis / lagerumschlag if lagerumschlag > 0 else 0
        
        # 4. Zinskosten Lager = Lagerwert × Zinssatz
        zinskosten_lager = lagerwert * ZINSSATZ_JAHR / 12  # Pro Monat
        
        # 5. DB2 = DB1 - Direkte Kosten - Zinskosten
        db2_basis = db1_basis - direkte_kosten - zinskosten_lager
        
        # 6. Vorjahres-Referenz laden
        vorjahr = AbteilungsleiterPlanungData._lade_vorjahr_referenz(
            'Teile', standort, monat, geschaeftsjahr
        )
        
        # 7. Impact-Analyse
        impact = AbteilungsleiterPlanungData._berechne_teile_impact(
            lagerumschlag,
            penner_quote * 100,
            servicegrad * 100,
            umsatz_basis,
            vorjahr.get('lagerumschlag', 0),
            vorjahr.get('penner_quote', 0),
            vorjahr.get('servicegrad', 0),
            vorjahr.get('umsatz', 0),
            marge_prozent
        )
        
        return {
            'umsatz_basis': round(umsatz_basis, 2),
            'db1_basis': round(db1_basis, 2),
            'db2_basis': round(db2_basis, 2),
            'lagerwert': round(lagerwert, 2),
            'zinskosten_lager': round(zinskosten_lager, 2),
            'direkte_kosten': round(direkte_kosten, 2),
            'impact': impact,
            'vorjahr': vorjahr
        }

    # =========================================================================
    # IMPACT-ANALYSEN
    # =========================================================================

    @staticmethod
    def _berechne_standzeit_impact(
        standzeit_plan: int,
        standzeit_vj: int,
        lagerwert_plan: float,
        lagerwert_vj: float
    ) -> Dict[str, Any]:
        """Berechnet Impact von Standzeit-Änderung auf Zinskosten."""
        if standzeit_vj == 0:
            return {'zinskosten_ersparnis': 0, 'lagerwert_ersparnis': 0}
        
        differenz_tage = standzeit_vj - standzeit_plan
        lagerwert_ersparnis = lagerwert_vj - lagerwert_plan
        zinskosten_ersparnis = lagerwert_ersparnis * ZINSSATZ_JAHR * (differenz_tage / 365)
        
        return {
            'standzeit_plan': standzeit_plan,
            'standzeit_vj': standzeit_vj,
            'differenz_tage': differenz_tage,
            'lagerwert_ersparnis': round(lagerwert_ersparnis, 2),
            'zinskosten_ersparnis': round(zinskosten_ersparnis, 2)
        }

    @staticmethod
    def _berechne_werkstatt_impact(
        produktivitaet_plan: float,
        leistungsgrad_plan: float,
        auslastung_plan: float,
        stundensatz_plan: float,
        produktivitaet_vj: float,
        leistungsgrad_vj: float,
        auslastung_vj: float,
        stundensatz_vj: float,
        stunden_verkauft_plan: float,
        stunden_verkauft_vj: float,
        db1_marge: float,
        vorjahr_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Berechnet Impact von Werkstatt-KPI-Änderungen auf DB.
        
        WICHTIG: Berücksichtigt die Zusammenhänge zwischen KPIs:
        - Leistungsgrad: Bei gleicher Stempelzeit mehr AW verrechnet
        - Produktivität: Bei gleicher Anwesenheit mehr gestempelt
        - Auslastung: Mehr verfügbare Kapazität genutzt
        """
        impact = {}
        
        # Vorjahres-Daten für Berechnungen (falls verfügbar)
        anwesenheit_vj_minuten = vorjahr_data.get('anwesenheit', 0) if vorjahr_data else 0
        stempelzeit_vj_minuten = vorjahr_data.get('stempelzeit', 0) if vorjahr_data else 0
        verfuegbare_stunden_vj = vorjahr_data.get('verfuegbare_stunden', 0) if vorjahr_data else 0
        
        # Fallback: Wenn keine Vorjahres-Daten, aus Stunden verkauft schätzen
        if anwesenheit_vj_minuten == 0 and stunden_verkauft_vj > 0:
            # Schätzung: Anwesenheit = Stunden verkauft / (Produktivität × Leistungsgrad)
            produktivitaet_vj_dez = produktivitaet_vj / 100 if produktivitaet_vj > 0 else 1.0
            leistungsgrad_vj_dez = leistungsgrad_vj / 100 if leistungsgrad_vj > 0 else 1.0
            anwesenheit_vj_stunden = stunden_verkauft_vj / (produktivitaet_vj_dez * leistungsgrad_vj_dez)
            anwesenheit_vj_minuten = anwesenheit_vj_stunden * 60
            stempelzeit_vj_minuten = anwesenheit_vj_minuten * produktivitaet_vj_dez
        
        # 1. LEISTUNGSGRAD-Impact
        # Bei gleicher Stempelzeit werden mehr AW verrechnet
        if leistungsgrad_vj > 0 and stempelzeit_vj_minuten > 0:
            leistungsgrad_diff = leistungsgrad_plan - leistungsgrad_vj
            # AW_mehr = Stempelzeit × (Leistungsgrad_diff) / 100 / 6
            # (6 Minuten = 0,1 AW)
            aw_mehr = stempelzeit_vj_minuten * (leistungsgrad_diff / 100) / 6
            # Stunden_mehr = AW_mehr × 6 / 60 (1 AW = 6 Min = 0,1h)
            stunden_mehr = aw_mehr * 6 / 60
            umsatz_mehr = stunden_mehr * stundensatz_plan
            db1_mehr = umsatz_mehr * db1_marge
            
            impact['leistungsgrad'] = {
                'plan': leistungsgrad_plan,
                'vj': leistungsgrad_vj,
                'differenz': round(leistungsgrad_diff, 1),
                'aw_mehr': round(aw_mehr, 1),
                'stunden_mehr': round(stunden_mehr, 2),
                'umsatz_mehr': round(umsatz_mehr, 2),
                'db1_mehr': round(db1_mehr, 2)
            }
        
        # 2. PRODUKTIVITÄT-Impact
        # Bei gleicher Anwesenheit wird mehr gestempelt
        if produktivitaet_vj > 0 and anwesenheit_vj_minuten > 0:
            produktivitaet_diff = produktivitaet_plan - produktivitaet_vj
            # Stempelzeit_mehr = Anwesenheit × (Produktivität_diff) / 100
            stempelzeit_mehr_minuten = anwesenheit_vj_minuten * (produktivitaet_diff / 100)
            # AW_mehr = Stempelzeit_mehr × Leistungsgrad_plan / 100 / 6
            leistungsgrad_plan_dez = leistungsgrad_plan / 100 if leistungsgrad_plan > 0 else 0
            aw_mehr = stempelzeit_mehr_minuten * leistungsgrad_plan_dez / 6
            # Stunden_mehr = AW_mehr × 6 / 60
            stunden_mehr = aw_mehr * 6 / 60
            umsatz_mehr = stunden_mehr * stundensatz_plan
            db1_mehr = umsatz_mehr * db1_marge
            
            impact['produktivitaet'] = {
                'plan': produktivitaet_plan,
                'vj': produktivitaet_vj,
                'differenz': round(produktivitaet_diff, 1),
                'stempelzeit_mehr': round(stempelzeit_mehr_minuten, 0),
                'aw_mehr': round(aw_mehr, 1),
                'stunden_mehr': round(stunden_mehr, 2),
                'umsatz_mehr': round(umsatz_mehr, 2),
                'db1_mehr': round(db1_mehr, 2)
            }
        
        # 3. AUSLASTUNG-Impact
        # Mehr verfügbare Kapazität wird genutzt
        if auslastung_vj > 0 and verfuegbare_stunden_vj > 0:
            auslastung_diff = auslastung_plan - auslastung_vj
            # Verfügbare_mehr = (Auslastung_diff) / 100 × Verfügbare_Kapazität
            verfuegbare_mehr_stunden = verfuegbare_stunden_vj * (auslastung_diff / 100)
            verfuegbare_mehr_minuten = verfuegbare_mehr_stunden * 60
            # Anwesenheit_mehr = Verfügbare_mehr
            anwesenheit_mehr_minuten = verfuegbare_mehr_minuten
            # Stempelzeit_mehr = Anwesenheit_mehr × Produktivität_plan / 100
            produktivitaet_plan_dez = produktivitaet_plan / 100 if produktivitaet_plan > 0 else 0
            stempelzeit_mehr_minuten = anwesenheit_mehr_minuten * produktivitaet_plan_dez
            # AW_mehr = Stempelzeit_mehr × Leistungsgrad_plan / 100 / 6
            leistungsgrad_plan_dez = leistungsgrad_plan / 100 if leistungsgrad_plan > 0 else 0
            aw_mehr = stempelzeit_mehr_minuten * leistungsgrad_plan_dez / 6
            # Stunden_mehr = AW_mehr × 6 / 60
            stunden_mehr = aw_mehr * 6 / 60
            umsatz_mehr = stunden_mehr * stundensatz_plan
            db1_mehr = umsatz_mehr * db1_marge
            
            impact['auslastung'] = {
                'plan': auslastung_plan,
                'vj': auslastung_vj,
                'differenz': round(auslastung_diff, 1),
                'verfuegbare_mehr': round(verfuegbare_mehr_stunden, 1),
                'aw_mehr': round(aw_mehr, 1),
                'stunden_mehr': round(stunden_mehr, 2),
                'umsatz_mehr': round(umsatz_mehr, 2),
                'db1_mehr': round(db1_mehr, 2)
            }
        
        # 4. STUNDENSATZ-Impact
        # Direkter Impact auf Umsatz bei gleichen verkauften Stunden
        if stundensatz_vj > 0:
            stundensatz_diff = stundensatz_plan - stundensatz_vj
            umsatz_mehr = stunden_verkauft_plan * stundensatz_diff
            db1_mehr = umsatz_mehr * db1_marge
            
            impact['stundensatz'] = {
                'plan': stundensatz_plan,
                'vj': stundensatz_vj,
                'differenz': round(stundensatz_diff, 2),
                'umsatz_mehr': round(umsatz_mehr, 2),
                'db1_mehr': round(db1_mehr, 2)
            }
        
        # Gesamt-Impact (Summe aller Einzel-Impacts)
        gesamt_umsatz = sum([v.get('umsatz_mehr', 0) for v in impact.values() if isinstance(v, dict) and 'umsatz_mehr' in v])
        gesamt_db1 = sum([v.get('db1_mehr', 0) for v in impact.values() if isinstance(v, dict) and 'db1_mehr' in v])
        impact['gesamt'] = {
            'umsatz_mehr': round(gesamt_umsatz, 2),
            'db1_mehr': round(gesamt_db1, 2)
        }
        
        return impact

    @staticmethod
    def _berechne_teile_impact(
        lagerumschlag_plan: float,
        penner_quote_plan: float,
        servicegrad_plan: float,
        umsatz_plan: float,
        lagerumschlag_vj: float,
        penner_quote_vj: float,
        servicegrad_vj: float,
        umsatz_vj: float,
        marge: float
    ) -> Dict[str, Any]:
        """Berechnet Impact von Teile-KPI-Änderungen."""
        impact = {}
        
        # Lagerumschlag-Impact
        if lagerumschlag_vj > 0:
            lagerwert_plan = umsatz_plan / lagerumschlag_plan if lagerumschlag_plan > 0 else 0
            lagerwert_vj = umsatz_vj / lagerumschlag_vj if lagerumschlag_vj > 0 else 0
            lagerwert_ersparnis = lagerwert_vj - lagerwert_plan
            zinskosten_ersparnis = lagerwert_ersparnis * ZINSSATZ_JAHR / 12
            impact['lagerumschlag'] = {
                'plan': lagerumschlag_plan,
                'vj': lagerumschlag_vj,
                'differenz': lagerumschlag_plan - lagerumschlag_vj,
                'lagerwert_ersparnis': round(lagerwert_ersparnis, 2),
                'zinskosten_ersparnis': round(zinskosten_ersparnis, 2)
            }
        
        # Penner-Quote-Impact
        if penner_quote_vj > 0:
            lagerwert_plan = umsatz_plan / lagerumschlag_plan if lagerumschlag_plan > 0 else 0
            penner_lagerwert_plan = lagerwert_plan * (penner_quote_plan / 100)
            penner_lagerwert_vj = lagerwert_plan * (penner_quote_vj / 100)
            penner_ersparnis = penner_lagerwert_vj - penner_lagerwert_plan
            impact['penner_quote'] = {
                'plan': penner_quote_plan,
                'vj': penner_quote_vj,
                'differenz': penner_quote_plan - penner_quote_vj,
                'penner_lagerwert_ersparnis': round(penner_ersparnis, 2)
            }
        
        # Servicegrad-Impact
        if servicegrad_vj > 0 and umsatz_vj > 0:
            servicegrad_diff = servicegrad_plan - servicegrad_vj
            # Annahme: +1% Servicegrad = +1% Umsatz
            umsatz_mehr = umsatz_vj * (servicegrad_diff / 100)
            db1_mehr = umsatz_mehr * marge
            impact['servicegrad'] = {
                'plan': servicegrad_plan,
                'vj': servicegrad_vj,
                'differenz': servicegrad_diff,
                'umsatz_mehr': round(umsatz_mehr, 2),
                'db1_mehr': round(db1_mehr, 2)
            }
        
        # Gesamt-Impact
        gesamt_umsatz = impact.get('servicegrad', {}).get('umsatz_mehr', 0)
        gesamt_db1 = impact.get('servicegrad', {}).get('db1_mehr', 0)
        gesamt_zinskosten = impact.get('lagerumschlag', {}).get('zinskosten_ersparnis', 0)
        impact['gesamt'] = {
            'umsatz_mehr': round(gesamt_umsatz, 2),
            'db1_mehr': round(gesamt_db1, 2),
            'zinskosten_ersparnis': round(gesamt_zinskosten, 2),
            'db2_mehr': round(gesamt_db1 + gesamt_zinskosten, 2)
        }
        
        return impact

    # =========================================================================
    # VORJAHRES-REFERENZ
    # =========================================================================

    @staticmethod
    def _lade_vorjahr_referenz(
        bereich: str,
        standort: int,
        monat: Optional[int],
        geschaeftsjahr: Optional[str]
    ) -> Dict[str, Any]:
        """
        Lädt Vorjahres-Referenz aus Locosoft.
        
        Args:
            bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
            standort: 1, 2, oder 3
            monat: 1-12 (GJ-Monat) oder None für ganzes Geschäftsjahr
            geschaeftsjahr: z.B. '2025/26'
        
        Returns:
            dict: Vorjahres-Werte für alle KPIs
        """
        from api.db_utils import get_locosoft_connection, locosoft_session
        from datetime import date
        
        # Geschäftsjahr parsen (z.B. '2025/26' -> 2025)
        if geschaeftsjahr:
            gj_start_jahr = int(geschaeftsjahr.split('/')[0])
        else:
            heute = date.today()
            gj_start_jahr = heute.year if heute.month >= 9 else heute.year - 1
        
        # Vorjahr = GJ-Start - 1
        vj_gj_start = gj_start_jahr - 1
        
        # Zeitraum bestimmen
        if monat is None:
            # Ganzes Geschäftsjahr laden (Sep bis Aug)
            vj_von = f"{vj_gj_start}-09-01"
            vj_bis = f"{vj_gj_start + 1}-09-01"
        else:
            # GJ-Monat zu Kalendermonat konvertieren
            # GJ-Monat 1-4 = Sep-Dez (Kalender: 9-12)
            # GJ-Monat 5-12 = Jan-Aug (Kalender: 1-8)
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
        
        # BWA-Filter (SSOT) - TAG157: Unterschiedliche Zuordnungslogik!
        # Umsatz (8xxxxx): via branch_number (1=DEG, 3=LAN)
        # Einsatz (7xxxxx): via Konto-Endziffer (6. Ziffer: 1=DEG, 2=LAN)
        # Kosten (4xxxxx): via Konto-Endziffer (6. Ziffer: 1=DEG, 2=LAN)
        # Stellantis = subsidiary_to_company_ref = 1
        # Hyundai = subsidiary_to_company_ref = 2
        
        # WICHTIG: Für Werkstatt, Teile, Sonstige keine Marken-Unterscheidung, nur Standort!
        # WICHTIG: Hyundai hat branch_number = 2, Stellantis Deggendorf hat branch_number = 1
        if bereich in ['Werkstatt', 'Teile', 'Sonstige']:
            # Werkstatt/Teile/Sonstige: Nur nach Standort filtern (Deggendorf oder Landau), nicht nach Marke
            if standort == 1:
                # Deggendorf: Stellantis (branch=1, subsidiary=1) + Hyundai (branch=2, subsidiary=2)
                firma_filter_umsatz = "AND ((branch_number = 1 AND subsidiary_to_company_ref = 1) OR (branch_number = 2 AND subsidiary_to_company_ref = 2))"
                firma_filter_einsatz = "AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 2))"
                firma_filter_kosten = "AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 2))"
            elif standort == 3:
                # Landau: branch_number = 3 (nur Stellantis, Hyundai hat keinen Standort in Landau)
                firma_filter_umsatz = "AND branch_number = 3 AND subsidiary_to_company_ref = 1"
                firma_filter_einsatz = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
                firma_filter_kosten = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
            else:
                # Standort 2 (Hyundai) oder andere: Alle Werte
                firma_filter_umsatz = ""
                firma_filter_einsatz = ""
                firma_filter_kosten = ""
        else:
            # Andere Bereiche: Normale Firma/Standort-Filterung
            # Firma bestimmen (Standort 1,3 = Stellantis, Standort 2 = Hyundai)
            if standort == 2:
                firma = '2'  # Hyundai
            else:
                firma = '1'  # Stellantis
            
            # BWA-Filter bauen (analog zu build_firma_standort_filter)
            if firma == '1':
                # Stellantis (Autohaus Greiner)
                firma_filter_umsatz = "AND subsidiary_to_company_ref = 1"
                firma_filter_einsatz = "AND subsidiary_to_company_ref = 1"
                firma_filter_kosten = "AND subsidiary_to_company_ref = 1"
                if standort == 1:
                    # Deggendorf: branch_number=1 für Umsatz, Konto-Endziffer=1 für Einsatz+Kosten
                    firma_filter_umsatz += " AND branch_number = 1"
                    firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
                    firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
                elif standort == 3:
                    # Landau: branch_number=3 für Umsatz, Konto-Endziffer=2 für Einsatz+Kosten
                    firma_filter_umsatz += " AND branch_number = 3"
                    firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
                    firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
            elif firma == '2':
                # Hyundai (Auto Greiner) - separate Firma
                firma_filter_umsatz = "AND subsidiary_to_company_ref = 2"
                firma_filter_einsatz = "AND subsidiary_to_company_ref = 2"
                firma_filter_kosten = "AND subsidiary_to_company_ref = 2"
            else:
                firma_filter_umsatz = ""
                firma_filter_einsatz = ""
                firma_filter_kosten = ""
        
        # Standort-Filter für Locosoft-Tabellen
        # Für orders/invoices: o.subsidiary oder i.subsidiary
        # Für dealer_vehicles: out_subsidiary
        if bereich in ['Werkstatt', 'Teile', 'Sonstige']:
            # Werkstatt/Teile/Sonstige: orders/invoices haben subsidiary
            if standort == 1:
                # Deggendorf: Stellantis (subsidiary=1) + Hyundai (subsidiary=2)
                subsidiary_filter = "AND (o.subsidiary = 1 OR o.subsidiary = 2)"
            elif standort == 3:
                # Landau: Nur Stellantis (subsidiary=1)
                subsidiary_filter = "AND o.subsidiary = 1"
            else:
                subsidiary_filter = ""
        else:
            # Für NW/GW: dealer_vehicles haben out_subsidiary
            # TAG 177: SSOT-Filter für Verkäufe (konsolidiert für Standort 1)
            from api.standort_utils import build_locosoft_filter_verkauf
            subsidiary_filter = build_locosoft_filter_verkauf(standort, nur_stellantis=False)
        
        result = {
            'umsatz': 0,
            'db1': 0,
            'db2': 0,
            'stueck': 0,
            'standzeit': 0,
            'lagerwert': 0,
            'produktivitaet': 0,
            'leistungsgrad': 0,
            'auslastung': 0,
            'stundensatz': 0,
            'stunden_verkauft': 0,
            'lagerumschlag': 0,
            'penner_quote': 0,
            'servicegrad': 0,
            'zinskosten_lager': 0
        }
        
        try:
            # 1. Umsatz, DB1, DB2 aus BWA (SSOT) - Bereichs-spezifisch
            from api.db_utils import db_session, locosoft_session, row_to_dict
            from api.db_connection import convert_placeholders
            
            with db_session() as conn:
                cursor = conn.cursor()
                
                # Bereichs-spezifische Konten (BWA-Logik)
                if bereich == 'NW':
                    umsatz_konten = "BETWEEN 810000 AND 819999"
                    einsatz_konten = "BETWEEN 710000 AND 719999"
                elif bereich == 'GW':
                    umsatz_konten = "BETWEEN 820000 AND 829999"
                    einsatz_konten = "BETWEEN 720000 AND 729999"
                elif bereich == 'Teile':
                    umsatz_konten = "BETWEEN 830000 AND 839999"
                    einsatz_konten = "BETWEEN 730000 AND 739999"
                elif bereich == 'Werkstatt':
                    umsatz_konten = "BETWEEN 840000 AND 849999"
                    einsatz_konten = "BETWEEN 740000 AND 749999"
                elif bereich == 'Sonstige':
                    umsatz_konten = "BETWEEN 860000 AND 869999"
                    einsatz_konten = "BETWEEN 760000 AND 769999"
                else:
                    return result
                
                # G&V-Abschlussbuchungen ausschließen (BWA-Logik)
                # TAG 179: Zentrale Funktion verwenden
                from api.db_utils import get_guv_filter
                guv_filter = get_guv_filter()
                
                # Umsatz (BWA-Logik: H-S)
                cursor.execute(convert_placeholders(f"""
                    SELECT COALESCE(SUM(
                        CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END
                    ) / 100.0, 0) as umsatz
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND nominal_account_number {umsatz_konten}
                      {firma_filter_umsatz}
                      {guv_filter}
                """), (vj_von, vj_bis))
                row = cursor.fetchone()
                result['umsatz'] = float(row_to_dict(row)['umsatz'] or 0) if row else 0
                
                # Einsatz (BWA-Logik: S-H)
                cursor.execute(convert_placeholders(f"""
                    SELECT COALESCE(SUM(
                        CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END
                    ) / 100.0, 0) as einsatz
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND nominal_account_number {einsatz_konten}
                      {firma_filter_einsatz}
                      {guv_filter}
                """), (vj_von, vj_bis))
                row = cursor.fetchone()
                einsatz = float(row_to_dict(row)['einsatz'] or 0) if row else 0
                
                # DB1 = Umsatz - Einsatz (BWA-Logik)
                result['db1'] = result['umsatz'] - einsatz
                
                # Variable Kosten (BWA-Logik)
                cursor.execute(convert_placeholders(f"""
                    SELECT COALESCE(SUM(
                        CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END
                    ) / 100.0, 0) as variable
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND (
                        nominal_account_number BETWEEN 415100 AND 415199
                        OR nominal_account_number BETWEEN 435500 AND 435599
                        OR (nominal_account_number BETWEEN 455000 AND 456999
                            AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                        OR (nominal_account_number BETWEEN 487000 AND 487099
                            AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                        OR nominal_account_number BETWEEN 491000 AND 497899
                      )
                      {firma_filter_kosten}
                      {guv_filter}
                """), (vj_von, vj_bis))
                row = cursor.fetchone()
                variable = float(row_to_dict(row)['variable'] or 0) if row else 0
                
                # DB2 = DB1 - Variable Kosten (BWA-Logik)
                result['db2'] = result['db1'] - variable
                
                # 2. Stückzahl aus Locosoft dealer_vehicles (SSOT für Fahrzeugzählungen)
                if bereich in ['NW', 'GW']:
                    with locosoft_session() as conn_loco:
                        cursor_loco = conn_loco.cursor()
                        
                        # Typ-Filter
                        # TAG169: Angepasst an Global Cube
                        # NW = N+T+V (Neuwagen, Tageszulassung, Vorführwagen)
                        # GW = D+G+L (Demo, Gebrauchtwagen, Leihfahrzeug)
                        if bereich == 'NW':
                            typ_filter = "dealer_vehicle_type IN ('N', 'T', 'V')"
                        else:  # GW
                            typ_filter = "dealer_vehicle_type IN ('D', 'G', 'L')"
                        
                        # TAG 177: SSOT-Filter für Verkäufe (konsolidiert für Standort 1)
                        from api.standort_utils import build_locosoft_filter_verkauf
                        standort_filter = build_locosoft_filter_verkauf(standort, nur_stellantis=False)
                        
                        # Stückzahl direkt aus Locosoft dealer_vehicles (wie bei IST-Werten)
                        cursor_loco.execute(f"""
                            SELECT COUNT(*) as stueck
                            FROM dealer_vehicles
                            WHERE out_invoice_date >= %s AND out_invoice_date < %s
                              AND out_invoice_date IS NOT NULL
                              AND {typ_filter}
                              {standort_filter}
                        """, (vj_von, vj_bis))
                        row = cursor_loco.fetchone()
                        result['stueck'] = int(row[0] or 0) if row else 0
                
                # 3. Standzeit aus dealer_vehicles (nur wenn Stückzahl > 0)
                if bereich in ['NW', 'GW'] and result['stueck'] > 0:
                    with locosoft_session() as conn_loco:
                        cursor_loco = conn_loco.cursor()
                        
                        # Typ-Filter für Standzeit
                        # TAG169: Angepasst an Global Cube
                        # NW = N+T+V (Neuwagen, Tageszulassung, Vorführwagen)
                        # GW = D+G+L (Demo, Gebrauchtwagen, Leihfahrzeug)
                        if bereich == 'NW':
                            typ_filter_standzeit = "dealer_vehicle_type IN ('N', 'T', 'V')"
                        else:  # GW
                            typ_filter_standzeit = "dealer_vehicle_type IN ('D', 'G', 'L')"
                        
                        # Standort-Filter für Standzeit
                        # TAG169: Korrigiert - Deggendorf muss beide Subsidiaries enthalten
                        if standort == 1:
                            # Deggendorf: Stellantis (subsidiary=1) + Hyundai (subsidiary=2)
                            standort_filter_standzeit = "AND (out_subsidiary = 1 OR out_subsidiary = 2)"
                        elif standort == 2:
                            standort_filter_standzeit = "AND out_subsidiary = 2"
                        elif standort == 3:
                            standort_filter_standzeit = "AND out_subsidiary = 3"  # Landau: subsidiary=3 (LANO location)
                        else:
                            standort_filter_standzeit = ""
                        
                        cursor_loco.execute(f"""
                            SELECT AVG(out_invoice_date - in_arrival_date) as avg_standzeit
                            FROM dealer_vehicles
                            WHERE out_invoice_date >= %s AND out_invoice_date < %s
                              AND out_invoice_date IS NOT NULL
                              AND in_arrival_date IS NOT NULL
                              AND {typ_filter_standzeit}
                              {standort_filter_standzeit}
                        """, (vj_von, vj_bis))
                        row = cursor_loco.fetchone()
                        if row and row[0]:
                            result['standzeit'] = int(row[0] or 0)
                        else:
                            result['standzeit'] = 0
                else:
                    result['standzeit'] = 0
            
                # 4. Werkstatt-spezifische Daten
                if bereich == 'Werkstatt':
                    with locosoft_session() as conn_loco:
                        cursor_loco = conn_loco.cursor()
                        # Stunden verkauft (verrechnet) - über invoices JOIN
                        # Für Werkstatt: subsidiary_filter verwenden (orders haben subsidiary)
                        cursor_loco.execute(f"""
                            SELECT COALESCE(SUM(l.time_units), 0) as aw_verkauft
                            FROM labours l
                            JOIN invoices i ON l.invoice_number = i.invoice_number 
                                AND l.invoice_type = i.invoice_type
                            JOIN orders o ON l.order_number = o.number
                            WHERE i.invoice_date >= %s AND i.invoice_date < %s
                              AND l.is_invoiced = true
                              AND i.is_canceled = false
                              {subsidiary_filter}
                        """, (vj_von, vj_bis))
                        row = cursor_loco.fetchone()
                        aw_verkauft = float(row[0] or 0) if row else 0
                        # AW zu Stunden umrechnen: 1 AW = 6 Minuten = 0.1 Stunden
                        result['stunden_verkauft'] = aw_verkauft / 10.0
                        
                        # Stundensatz = Umsatz / Stunden (nicht AW!)
                        if result['stunden_verkauft'] > 0:
                            result['stundensatz'] = result['umsatz'] / result['stunden_verkauft']
                        else:
                            result['stundensatz'] = 0.0
                        
                        # Produktivität, Leistungsgrad, Auslastung aus werkstatt_data.py laden
                        kpis = berechne_werkstatt_kpis_fuer_zeitraum(vj_von, vj_bis, standort)
                        result['produktivitaet'] = kpis.get('produktivitaet', 105.0)
                        result['leistungsgrad'] = kpis.get('leistungsgrad', 90.0)
                        result['auslastung'] = kpis.get('auslastung', 75.0)
                        # Zusätzliche Daten für Impact-Berechnung
                        result['anwesenheit'] = kpis.get('anwesenheit', 0)  # Minuten
                        result['stempelzeit'] = kpis.get('stempelzeit', 0)  # Minuten
                        result['verfuegbare_stunden'] = kpis.get('verfuegbare_stunden', 0)  # Stunden
                        
                        # Anzahl Mechaniker (für Frage 5)
                        # Berechnung: Verfügbare Stunden / 176 (Stunden pro Mechaniker pro Monat)
                        if result['verfuegbare_stunden'] > 0:
                            result['anzahl_mechaniker'] = round(result['verfuegbare_stunden'] / 176)
                        else:
                            # Fallback: Aus werkstatt_data.py Mechaniker-Anzahl
                            from api.werkstatt_data import WerkstattData
                            from datetime import datetime
                            vj_von_date = datetime.strptime(vj_von, '%Y-%m-%d').date()
                            vj_bis_date = datetime.strptime(vj_bis, '%Y-%m-%d').date()
                            leistung_data = WerkstattData.get_mechaniker_leistung(
                                von=vj_von_date,
                                bis=vj_bis_date,
                                betrieb=standort,
                                inkl_ehemalige=False
                            )
                            result['anzahl_mechaniker'] = leistung_data.get('anzahl_mechaniker', 0)
                        
                        # Frage 8: Durchschnittliche AW pro Auftrag
                        # subsidiary_filter für Werkstatt: o.subsidiary
                        if standort == 1:
                            werkstatt_subsidiary_filter = "AND (o.subsidiary = 1 OR o.subsidiary = 2)"
                        elif standort == 3:
                            werkstatt_subsidiary_filter = "AND o.subsidiary = 3"  # Landau: subsidiary=3 (LANO location)
                        else:
                            werkstatt_subsidiary_filter = ""
                        
                        cursor_loco.execute(f"""
                            SELECT 
                                COUNT(DISTINCT o.number) as anzahl_auftraege,
                                COALESCE(SUM(l.time_units), 0) as gesamt_aw
                            FROM orders o
                            JOIN invoices i ON i.order_number = o.number
                            JOIN labours l ON l.order_number = o.number
                                AND l.invoice_number = i.invoice_number 
                                AND l.invoice_type = i.invoice_type
                            WHERE i.invoice_date >= %s AND i.invoice_date < %s
                              AND l.is_invoiced = true
                              AND i.is_canceled = false
                              {werkstatt_subsidiary_filter}
                        """, (vj_von, vj_bis))
                        row = cursor_loco.fetchone()
                        anzahl_auftraege = int(row[0] or 0) if row else 0
                        gesamt_aw = float(row[1] or 0) if row else 0
                        if anzahl_auftraege > 0:
                            result['avg_aw_pro_auftrag'] = round(gesamt_aw / anzahl_auftraege, 1)
                        else:
                            result['avg_aw_pro_auftrag'] = 0.0
                        
                        # Frage 9: Durchschnittliche Durchlaufzeit (Tage)
                        # TAG 169: Median statt AVG verwenden, um Outlier (z.B. Garantiearbeiten mit langer Teileverfügbarkeit) zu vermeiden
                        # Filter: Nur Aufträge mit realistischer Durchlaufzeit (0-30 Tage)
                        cursor_loco.execute(f"""
                            SELECT 
                                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (i.invoice_date::timestamp - o.order_date::timestamp)) / 86400.0) as durchlaufzeit_tage
                            FROM orders o
                            JOIN invoices i ON i.order_number = o.number
                            WHERE i.invoice_date >= %s AND i.invoice_date < %s
                              AND i.invoice_date IS NOT NULL
                              AND o.order_date IS NOT NULL
                              AND i.is_canceled = false
                              AND EXTRACT(EPOCH FROM (i.invoice_date::timestamp - o.order_date::timestamp)) / 86400.0 BETWEEN 0 AND 30
                              {werkstatt_subsidiary_filter}
                        """, (vj_von, vj_bis))
                        row = cursor_loco.fetchone()
                        if row and row[0]:
                            result['durchlaufzeit_tage'] = round(float(row[0]), 1)
                        else:
                            result['durchlaufzeit_tage'] = 0.0
                        
                        # Frage 10: Wiederkehrrate (Kunden mit >1 Auftrag / Gesamt Kunden)
                        cursor_loco.execute(f"""
                            WITH kunden_auftraege AS (
                                SELECT 
                                    o.order_customer as customer_number,
                                    COUNT(DISTINCT o.number) as anzahl_auftraege
                                FROM orders o
                                JOIN invoices i ON i.order_number = o.number
                                WHERE i.invoice_date >= %s AND i.invoice_date < %s
                                  AND o.order_customer IS NOT NULL
                                  AND i.is_canceled = false
                                  {werkstatt_subsidiary_filter}
                                GROUP BY o.order_customer
                            )
                            SELECT 
                                COUNT(*) FILTER (WHERE anzahl_auftraege > 1) as wiederkehrer,
                                COUNT(*) as gesamt_kunden
                            FROM kunden_auftraege
                        """, (vj_von, vj_bis))
                        row = cursor_loco.fetchone()
                        wiederkehrer = int(row[0] or 0) if row else 0
                        gesamt_kunden = int(row[1] or 0) if row else 0
                        if gesamt_kunden > 0:
                            result['wiederkehrrate'] = round((wiederkehrer / gesamt_kunden) * 100, 1)
                        else:
                            result['wiederkehrrate'] = 0.0
                
                # 5. Teile-spezifische Daten
                if bereich == 'Teile':
                    # Lagerumschlag, Penner-Quote, Servicegrad
                    # TODO: Aus teile_data.py laden (komplexe Berechnung)
                    # Für jetzt: Placeholder
                    if result['umsatz'] > 0:
                        # Annahme: Lagerwert = Umsatz / 4 (4x Umschlag)
                        result['lagerwert'] = result['umsatz'] / 4
                        result['lagerumschlag'] = 4.0
                    result['penner_quote'] = 18.0     # Default
                    result['servicegrad'] = 95.0       # Default
                    result['zinskosten_lager'] = result['lagerwert'] * ZINSSATZ_JAHR / 12
            
        
        except Exception as e:
            logger.error(f"Fehler beim Laden der Vorjahres-Referenz: {str(e)}")
        
        return result

    # =========================================================================
    # BWA YTD (SSOT für kumulierte Werte)
    # =========================================================================

    @staticmethod
    def _lade_bwa_ytd(
        bereich: str,
        standort: int,
        bis_monat: int,
        jahr: int
    ) -> Dict[str, Any]:
        """
        Lädt YTD-Werte direkt aus BWA (SSOT).
        
        Args:
            bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
            standort: 1, 2, oder 3
            bis_monat: Kalendermonat (1-12)
            jahr: Kalenderjahr
        
        Returns:
            Dict mit umsatz, db1, db2 (aus BWA)
        """
        from api.db_utils import db_session, row_to_dict
        from api.db_connection import convert_placeholders
        
        result = {
            'umsatz': 0,
            'db1': 0,
            'db2': 0
        }
        
        # GJ-Start bestimmen (September)
        if bis_monat >= 9:
            gj_start_jahr = jahr
        else:
            gj_start_jahr = jahr - 1
        
        datum_von = f"{gj_start_jahr}-09-01"
        if bis_monat == 12:
            datum_bis = f"{jahr+1}-01-01"
        else:
            datum_bis = f"{jahr}-{bis_monat+1:02d}-01"
        
        # BWA-Filter bauen
        # WICHTIG: Für Werkstatt, Teile, Sonstige keine Marken-Unterscheidung, nur Standort!
        # WICHTIG: Hyundai hat branch_number = 2, Stellantis Deggendorf hat branch_number = 1
        if bereich in ['Werkstatt', 'Teile', 'Sonstige']:
            # Werkstatt/Teile/Sonstige: Nur nach Standort filtern (Deggendorf oder Landau), nicht nach Marke
            if standort == 1:
                # Deggendorf: Stellantis (branch=1, subsidiary=1) + Hyundai (branch=2, subsidiary=2)
                firma_filter_umsatz = "AND ((branch_number = 1 AND subsidiary_to_company_ref = 1) OR (branch_number = 2 AND subsidiary_to_company_ref = 2))"
                firma_filter_einsatz = "AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 2))"
                firma_filter_kosten = "AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 2))"
            elif standort == 3:
                # Landau: branch_number = 3 (nur Stellantis, Hyundai hat keinen Standort in Landau)
                firma_filter_umsatz = "AND branch_number = 3 AND subsidiary_to_company_ref = 1"
                firma_filter_einsatz = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
                firma_filter_kosten = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
            else:
                # Standort 2 (Hyundai) oder andere: Alle Werte
                firma_filter_umsatz = ""
                firma_filter_einsatz = ""
                firma_filter_kosten = ""
        else:
            # Andere Bereiche: Normale Firma/Standort-Filterung
            if standort == 2:
                firma = '2'  # Hyundai
            else:
                firma = '1'  # Stellantis
            
            # BWA-Filter (analog zu build_firma_standort_filter)
            if firma == '1':
                firma_filter_umsatz = "AND subsidiary_to_company_ref = 1"
                firma_filter_einsatz = "AND subsidiary_to_company_ref = 1"
                firma_filter_kosten = "AND subsidiary_to_company_ref = 1"
                if standort == 1:
                    firma_filter_umsatz += " AND branch_number = 1"
                    firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
                    firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
                elif standort == 3:
                    firma_filter_umsatz += " AND branch_number = 3"
                    firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
                    firma_filter_kosten += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
            elif firma == '2':
                firma_filter_umsatz = "AND subsidiary_to_company_ref = 2"
                firma_filter_einsatz = "AND subsidiary_to_company_ref = 2"
                firma_filter_kosten = "AND subsidiary_to_company_ref = 2"
            else:
                firma_filter_umsatz = ""
                firma_filter_einsatz = ""
                firma_filter_kosten = ""
        
        # TAG 179: Zentrale Funktion verwenden
        from api.db_utils import get_guv_filter
        guv_filter = get_guv_filter()
        
        # Bereichs-spezifische Konten
        if bereich == 'NW':
            umsatz_konten = "BETWEEN 810000 AND 819999"
            einsatz_konten = "BETWEEN 710000 AND 719999"
        elif bereich == 'GW':
            umsatz_konten = "BETWEEN 820000 AND 829999"
            einsatz_konten = "BETWEEN 720000 AND 729999"
        elif bereich == 'Teile':
            umsatz_konten = "BETWEEN 830000 AND 839999"
            einsatz_konten = "BETWEEN 730000 AND 739999"
        elif bereich == 'Werkstatt':
            umsatz_konten = "BETWEEN 840000 AND 849999"
            einsatz_konten = "BETWEEN 740000 AND 749999"
        elif bereich == 'Sonstige':
            umsatz_konten = "BETWEEN 860000 AND 869999"
            einsatz_konten = "BETWEEN 760000 AND 769999"
        else:
            return result
        
        try:
            with db_session() as conn:
                cursor = conn.cursor()
                
                # Umsatz YTD
                cursor.execute(convert_placeholders(f"""
                    SELECT COALESCE(SUM(
                        CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END
                    ) / 100.0, 0) as umsatz
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND nominal_account_number {umsatz_konten}
                      {firma_filter_umsatz}
                      {guv_filter}
                """), (datum_von, datum_bis))
                row = cursor.fetchone()
                result['umsatz'] = float(row_to_dict(row)['umsatz'] or 0) if row else 0
                
                # Einsatz YTD
                cursor.execute(convert_placeholders(f"""
                    SELECT COALESCE(SUM(
                        CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END
                    ) / 100.0, 0) as einsatz
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND nominal_account_number {einsatz_konten}
                      {firma_filter_einsatz}
                      {guv_filter}
                """), (datum_von, datum_bis))
                row = cursor.fetchone()
                einsatz = float(row_to_dict(row)['einsatz'] or 0) if row else 0
                
                # DB1 YTD
                result['db1'] = result['umsatz'] - einsatz
                
                # Variable Kosten YTD
                cursor.execute(convert_placeholders(f"""
                    SELECT COALESCE(SUM(
                        CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END
                    ) / 100.0, 0) as variable
                    FROM loco_journal_accountings
                    WHERE accounting_date >= ? AND accounting_date < ?
                      AND (
                        nominal_account_number BETWEEN 415100 AND 415199
                        OR nominal_account_number BETWEEN 435500 AND 435599
                        OR (nominal_account_number BETWEEN 455000 AND 456999
                            AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                        OR (nominal_account_number BETWEEN 487000 AND 487099
                            AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                        OR nominal_account_number BETWEEN 491000 AND 497899
                      )
                      {firma_filter_kosten}
                      {guv_filter}
                """), (datum_von, datum_bis))
                row = cursor.fetchone()
                variable = float(row_to_dict(row)['variable'] or 0) if row else 0
                
                # DB2 YTD
                result['db2'] = result['db1'] - variable
                
        except Exception as e:
            logger.error(f"Fehler beim Laden der BWA YTD-Werte: {str(e)}")
        
        return result

    # =========================================================================
    # HYBRID-BERECHNUNG (Basis + Aufhol)
    # =========================================================================

    @staticmethod
    def berechne_hybrid_ziele(
        umsatz_basis: float,
        db1_basis: float,
        geschaeftsjahr: str,
        bereich: str,
        standort: int
    ) -> Dict[str, Any]:
        """
        Berechnet Hybrid-Ziele (Basis + Aufhol).
        
        Args:
            umsatz_basis: Basis-Umsatz (Bottom-Up)
            db1_basis: Basis-DB1 (Bottom-Up)
            geschaeftsjahr: z.B. '2025/26'
            bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
            standort: 1, 2, oder 3
        
        Returns:
            dict: {
                'umsatz_ziel': float (Basis + Aufhol),
                'db1_ziel': float (Basis + Aufhol),
                'aufhol_umsatz': float,
                'aufhol_db1': float
            }
        """
        # Aufhol-Logik anwenden (SSOT)
        aufhol_result = apply_aufhol_auf_kst_ziel(
            umsatz_basis,
            db1_basis,
            geschaeftsjahr,
            bereich,
            standort=standort
        )
        
        return {
            'umsatz_ziel': aufhol_result['umsatz_ziel_mit_aufhol'],
            'db1_ziel': aufhol_result['db1_ziel_mit_aufhol'],
            'umsatz_basis': umsatz_basis,
            'db1_basis': db1_basis,
            'aufhol_umsatz': aufhol_result['aufhol_beitrag_umsatz'],
            'aufhol_db1': aufhol_result['aufhol_beitrag_db1']
        }

    # =========================================================================
    # FREIGABE (Ziele in kst_ziele schreiben)
    # =========================================================================

    @staticmethod
    def freigeben_planung(
        planung_id: int,
        freigegeben_von: str,
        kommentar: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gibt Planung frei und schreibt Ziele in kst_ziele.
        
        Args:
            planung_id: ID der Planung
            freigegeben_von: LDAP-Username
            kommentar: Optional Kommentar
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            with db_session() as conn:
                cursor = conn.cursor()
                
                # 1. Planung laden
                cursor.execute("""
                    SELECT geschaeftsjahr, monat, bereich, standort,
                           umsatz_basis, db1_basis, db2_basis,
                           aufhol_umsatz, aufhol_db1,
                           umsatz_ziel, db1_ziel, db2_ziel,
                           erstellt_von
                    FROM abteilungsleiter_planung
                    WHERE id = %s
                """, (planung_id,))
                
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'message': 'Planung nicht gefunden'}
                
                # Zu Dict konvertieren
                from api.db_utils import row_to_dict
                planung = row_to_dict(row)
                
                # 2. Status auf 'freigegeben' setzen
                cursor.execute("""
                    UPDATE abteilungsleiter_planung
                    SET status = 'freigegeben',
                        freigegeben_von = %s,
                        freigegeben_am = CURRENT_TIMESTAMP,
                        kommentar = %s
                    WHERE id = %s
                """, (freigegeben_von, kommentar, planung_id))
                
                # 3. Ziele in kst_ziele schreiben (UPSERT)
                cursor.execute("""
                    INSERT INTO kst_ziele
                    (geschaeftsjahr, monat, bereich, standort,
                     umsatz_ziel, db1_ziel,
                     umsatz_basis, db1_basis,
                     aufhol_umsatz, aufhol_db1,
                     planungs_quelle, plan_abteilungsleiter,
                     plan_freigegeben_von, plan_freigegeben_am,
                     erstellt_von)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
                    ON CONFLICT (geschaeftsjahr, monat, bereich, standort)
                    DO UPDATE SET
                        umsatz_ziel = EXCLUDED.umsatz_ziel,
                        db1_ziel = EXCLUDED.db1_ziel,
                        umsatz_basis = EXCLUDED.umsatz_basis,
                        db1_basis = EXCLUDED.db1_basis,
                        aufhol_umsatz = EXCLUDED.aufhol_umsatz,
                        aufhol_db1 = EXCLUDED.aufhol_db1,
                        planungs_quelle = EXCLUDED.planungs_quelle,
                        plan_abteilungsleiter = EXCLUDED.plan_abteilungsleiter,
                        plan_freigegeben_von = EXCLUDED.plan_freigegeben_von,
                        plan_freigegeben_am = EXCLUDED.plan_freigegeben_am,
                        geaendert_am = CURRENT_TIMESTAMP
                """, (
                    planung['geschaeftsjahr'],
                    planung['monat'],
                    planung['bereich'],
                    planung['standort'],
                    planung['umsatz_ziel'],
                    planung['db1_ziel'],
                    planung['umsatz_basis'],
                    planung['db1_basis'],
                    planung['aufhol_umsatz'],
                    planung['aufhol_db1'],
                    'abteilungsleiter',
                    planung['erstellt_von'],
                    freigegeben_von,
                    freigegeben_von
                ))
                
                conn.commit()
                
                return {
                    'success': True,
                    'message': f'Planung freigegeben und Ziele in kst_ziele geschrieben'
                }
        
        except Exception as e:
            logger.error(f"Fehler bei Freigabe: {str(e)}")
            return {'success': False, 'message': str(e)}

    # =========================================================================
    # JAHRESPLANUNG & KUMULIERTE WERTE
    # =========================================================================

    @staticmethod
    def lade_jahresplanung(
        geschaeftsjahr: str,
        bereich: str,
        standort: int
    ) -> Dict[str, Any]:
        """
        Lädt alle Planungen für ein Geschäftsjahr (alle 12 Monate).
        
        Args:
            geschaeftsjahr: z.B. '2025/26'
            bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
            standort: 1, 2, oder 3
        
        Returns:
            Dict mit:
            - monate: Liste aller 12 Monate mit Planungsdaten
            - kumuliert: Kumulierte Werte (YTD)
            - kumuliert_vj: Kumulierte Vorjahres-Werte
        """
        from api.db_utils import db_session, row_to_dict
        
        result = {
            'geschaeftsjahr': geschaeftsjahr,
            'bereich': bereich,
            'standort': standort,
            'monate': [],
            'kumuliert': {
                'umsatz': 0,
                'db1': 0,
                'db2': 0,
                'stueck': 0
            },
            'kumuliert_vj': {
                'umsatz': 0,
                'db1': 0,
                'db2': 0,
                'stueck': 0
            }
        }
        
        try:
            with db_session() as conn:
                cursor = conn.cursor()
                
                # Alle Planungen für dieses Jahr laden
                cursor.execute("""
                    SELECT * FROM abteilungsleiter_planung
                    WHERE geschaeftsjahr = %s AND bereich = %s AND standort = %s
                    ORDER BY monat
                """, (geschaeftsjahr, bereich, standort))
                
                planungen = {row_to_dict(row)['monat']: row_to_dict(row) for row in cursor.fetchall()}
            
            # Für alle 12 GJ-Monate Daten sammeln
            kum_umsatz = 0
            kum_db1 = 0
            kum_db2 = 0
            kum_stueck = 0
            
            kum_umsatz_vj = 0
            kum_db1_vj = 0
            kum_db2_vj = 0
            kum_stueck_vj = 0
            
            for monat in range(1, 13):
                planung = planungen.get(monat)
                
                # Prüfen ob Monat abgelaufen
                monat_abgelaufen = ist_monat_abgelaufen(geschaeftsjahr, monat)
                
                # GJ-Monat zu Kalendermonat konvertieren (für BWA-Abfragen)
                gj_start_jahr = int(geschaeftsjahr.split('/')[0])
                if monat <= 4:  # Sep-Dez
                    kal_monat = monat + 8
                    kal_jahr = gj_start_jahr
                else:  # Jan-Aug
                    kal_monat = monat - 4
                    kal_jahr = gj_start_jahr + 1
                
                # Vorjahres-Referenz laden
                vorjahr = AbteilungsleiterPlanungData._lade_vorjahr_referenz(
                    bereich, standort, monat, geschaeftsjahr
                )
                
                # Monatswerte für Anzeige
                # Für abgelaufene Monate: IMMER IST-Werte aus BWA (SSOT)
                # Für zukünftige Monate: Planungswerte (falls vorhanden)
                if monat_abgelaufen:
                    # Abgelaufener Monat: IST-Werte aus BWA für diesen Monat
                    # Verwende _lade_bwa_ytd für diesen Monat und vorherigen Monat, dann Differenz
                    if monat == 1:  # September (erster Monat)
                        # YTD für September = Monatswert
                        ytd_aktuell = AbteilungsleiterPlanungData._lade_bwa_ytd(
                            bereich, standort, kal_monat, kal_jahr
                        )
                        umsatz_plan = ytd_aktuell.get('umsatz', 0)
                        db1_plan = ytd_aktuell.get('db1', 0)
                        db2_plan = ytd_aktuell.get('db2', 0)
                    else:
                        # YTD für aktuellen Monat
                        ytd_aktuell = AbteilungsleiterPlanungData._lade_bwa_ytd(
                            bereich, standort, kal_monat, kal_jahr
                        )
                        # YTD für vorherigen Monat
                        # GJ-Monat zu Kalendermonat: GJ-Monat 1-4 = Sep-Dez (Kalender 9-12), GJ-Monat 5-12 = Jan-Aug (Kalender 1-8)
                        vorher_gj_monat = monat - 1
                        if vorher_gj_monat <= 4:  # Sep-Dez
                            vorher_kal_monat = vorher_gj_monat + 8
                            vorher_kal_jahr = gj_start_jahr
                        else:  # Jan-Aug
                            vorher_kal_monat = vorher_gj_monat - 4
                            vorher_kal_jahr = gj_start_jahr + 1
                        
                        ytd_vorher = AbteilungsleiterPlanungData._lade_bwa_ytd(
                            bereich, standort, vorher_kal_monat, vorher_kal_jahr
                        )
                        # Monatswert = Differenz zwischen YTD aktuell und YTD vorher
                        umsatz_plan = ytd_aktuell.get('umsatz', 0) - ytd_vorher.get('umsatz', 0)
                        db1_plan = ytd_aktuell.get('db1', 0) - ytd_vorher.get('db1', 0)
                        db2_plan = ytd_aktuell.get('db2', 0) - ytd_vorher.get('db2', 0)
                    
                    # Stückzahl aus lade_ist_werte_fuer_monat (nicht aus BWA)
                    ist_werte = lade_ist_werte_fuer_monat(
                        geschaeftsjahr, monat, bereich, standort
                    )
                    stueck_plan = int(ist_werte.get('stueck_ist', 0) or 0)
                else:
                    # Zukünftiger Monat: Planungswerte (falls vorhanden)
                    umsatz_plan = float(planung.get('umsatz_ziel', 0) or 0) if planung else 0
                    db1_plan = float(planung.get('db1_ziel', 0) or 0) if planung else 0
                    db2_plan = float(planung.get('db2_ziel', 0) or 0) if planung else 0
                    stueck_plan = int(planung.get('plan_stueck', 0) or 0) if planung else 0
                
                # Vorjahreswerte (aus BWA)
                umsatz_vj = float(vorjahr.get('umsatz', 0) or 0)
                db1_vj = float(vorjahr.get('db1', 0) or 0)
                db2_vj = float(vorjahr.get('db2', 0) or 0)
                stueck_vj = int(vorjahr.get('stueck', 0) or 0)
                
                # Kumulieren (Planung)
                kum_umsatz += umsatz_plan
                kum_db1 += db1_plan
                kum_db2 += db2_plan
                kum_stueck += stueck_plan
                
                # VJ-Werte kumulieren (für einzelne Monate)
                kum_umsatz_vj += umsatz_vj
                kum_db1_vj += db1_vj
                kum_db2_vj += db2_vj
                kum_stueck_vj += stueck_vj
                
                # YTD und VJ-YTD direkt aus BWA laden (SSOT)
                # GJ-Monat zu Kalendermonat konvertieren
                gj_start_jahr = int(geschaeftsjahr.split('/')[0])
                if monat <= 4:  # Sep-Dez
                    kal_monat = monat + 8
                    kal_jahr = gj_start_jahr
                else:  # Jan-Aug
                    kal_monat = monat - 4
                    kal_jahr = gj_start_jahr + 1
                
                # YTD aus BWA (vom GJ-Start bis aktuellen Monat)
                # Für abgelaufene Monate: IST-Werte aus BWA (kumuliert)
                # Für zukünftige Monate: IST-Werte aus BWA (bis zum letzten abgelaufenen Monat) + Planungswerte (falls vorhanden)
                if monat_abgelaufen:
                    # Abgelaufener Monat: YTD direkt aus BWA (IST-Werte, kumuliert)
                    ytd_bwa = AbteilungsleiterPlanungData._lade_bwa_ytd(
                        bereich, standort, kal_monat, kal_jahr
                    )
                else:
                    # Zukünftiger Monat: YTD = IST-Werte aus BWA (bis zum letzten abgelaufenen Monat)
                    # + Planungswerte für zukünftige Monate (falls vorhanden)
                    # Finde den letzten abgelaufenen Monat
                    letzter_abgelaufener_monat = None
                    for m in range(monat - 1, 0, -1):
                        if ist_monat_abgelaufen(geschaeftsjahr, m):
                            letzter_abgelaufener_monat = m
                            break
                    
                    if letzter_abgelaufener_monat:
                        # YTD bis zum letzten abgelaufenen Monat aus BWA
                        if letzter_abgelaufener_monat <= 4:  # Sep-Dez
                            letzter_kal_monat = letzter_abgelaufener_monat + 8
                            letzter_kal_jahr = gj_start_jahr
                        else:  # Jan-Aug
                            letzter_kal_monat = letzter_abgelaufener_monat - 4
                            letzter_kal_jahr = gj_start_jahr + 1
                        
                        ytd_bis_letzter = AbteilungsleiterPlanungData._lade_bwa_ytd(
                            bereich, standort, letzter_kal_monat, letzter_kal_jahr
                        )
                        
                        # Kumulierte Planungswerte für zukünftige Monate (vom letzten abgelaufenen Monat + 1 bis aktuellen Monat)
                        kum_planung_zukunft = {
                            'umsatz': 0,
                            'db1': 0,
                            'db2': 0
                        }
                        
                        for m in range(letzter_abgelaufener_monat + 1, monat + 1):
                            planung_m = planungen.get(m)
                            if planung_m:
                                kum_planung_zukunft['umsatz'] += float(planung_m.get('umsatz_ziel', 0) or 0)
                                kum_planung_zukunft['db1'] += float(planung_m.get('db1_ziel', 0) or 0)
                                kum_planung_zukunft['db2'] += float(planung_m.get('db2_ziel', 0) or 0)
                        
                        # YTD = IST-Werte bis letzter abgelaufener Monat + Planungswerte für zukünftige Monate
                        ytd_bwa = {
                            'umsatz': ytd_bis_letzter.get('umsatz', 0) + kum_planung_zukunft['umsatz'],
                            'db1': ytd_bis_letzter.get('db1', 0) + kum_planung_zukunft['db1'],
                            'db2': ytd_bis_letzter.get('db2', 0) + kum_planung_zukunft['db2']
                        }
                    else:
                        # Kein abgelaufener Monat gefunden: YTD = kumulierte Planungswerte
                        ytd_bwa = {
                            'umsatz': kum_umsatz,
                            'db1': kum_db1,
                            'db2': kum_db2
                        }
                
                # VJ-YTD aus BWA (vom VJ-GJ-Start bis entsprechenden Monat)
                vj_gj_start = gj_start_jahr - 1
                if monat <= 4:  # Sep-Dez
                    vj_kal_monat = monat + 8
                    vj_kal_jahr = vj_gj_start
                else:  # Jan-Aug
                    vj_kal_monat = monat - 4
                    vj_kal_jahr = vj_gj_start + 1
                
                vj_ytd_bwa = AbteilungsleiterPlanungData._lade_bwa_ytd(
                    bereich, standort, vj_kal_monat, vj_kal_jahr
                )
                
                # Monatsname
                monatsnamen = ['Sep', 'Okt', 'Nov', 'Dez', 'Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug']
                monat_name = monatsnamen[monat - 1]
                
                result['monate'].append({
                    'monat': monat,
                    'monat_name': monat_name,
                    'planung': planung,
                    'vorjahr': vorjahr,
                    'umsatz_plan': umsatz_plan,
                    'db1_plan': db1_plan,
                    'db2_plan': db2_plan,
                    'stueck_plan': stueck_plan,
                    'umsatz_vj': umsatz_vj,
                    'db1_vj': db1_vj,
                    'db2_vj': db2_vj,
                    'stueck_vj': stueck_vj,
                    'kumuliert': {
                        'umsatz': ytd_bwa.get('umsatz', kum_umsatz),
                        'db1': ytd_bwa.get('db1', kum_db1),
                        'db2': ytd_bwa.get('db2', kum_db2),
                        'stueck': kum_stueck  # Stückzahl weiterhin kumuliert
                    },
                    'kumuliert_vj': {
                        'umsatz': vj_ytd_bwa.get('umsatz', kum_umsatz_vj),
                        'db1': vj_ytd_bwa.get('db1', kum_db1_vj),
                        'db2': vj_ytd_bwa.get('db2', kum_db2_vj),
                        'stueck': kum_stueck_vj  # Stückzahl weiterhin kumuliert
                    },
                    'monat_abgelaufen': monat_abgelaufen,
                    'ist_werte_verwendet': monat_abgelaufen and not planung  # Flag: IST-Werte statt Planung
                })
            
            # Gesamt-Kumulierte Werte (letzter Monat = Gesamt)
            # YTD und VJ-YTD für letzten Monat (August = GJ-Monat 12) direkt aus BWA
            if result['monate']:
                letzter_monat = result['monate'][-1]
                result['kumuliert'] = letzter_monat.get('kumuliert', {
                    'umsatz': kum_umsatz,
                    'db1': kum_db1,
                    'db2': kum_db2,
                    'stueck': kum_stueck
                })
                result['kumuliert_vj'] = letzter_monat.get('kumuliert_vj', {
                    'umsatz': kum_umsatz_vj,
                    'db1': kum_db1_vj,
                    'db2': kum_db2_vj,
                    'stueck': kum_stueck_vj
                })
            else:
                result['kumuliert'] = {
                    'umsatz': kum_umsatz,
                    'db1': kum_db1,
                    'db2': kum_db2,
                    'stueck': kum_stueck
                }
                result['kumuliert_vj'] = {
                    'umsatz': kum_umsatz_vj,
                    'db1': kum_db1_vj,
                    'db2': kum_db2_vj,
                    'stueck': kum_stueck_vj
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Jahresplanung: {str(e)}")
            return {
                'geschaeftsjahr': geschaeftsjahr,
                'bereich': bereich,
                'standort': standort,
                'monate': [],
                'kumuliert': {'umsatz': 0, 'db1': 0, 'db2': 0, 'stueck': 0},
                'kumuliert_vj': {'umsatz': 0, 'db1': 0, 'db2': 0, 'stueck': 0},
                'error': str(e)
            }

    @staticmethod
    def kopiere_vorjahr(
        geschaeftsjahr: str,
        bereich: str,
        standort: int,
        erstellt_von: str
    ) -> Dict[str, Any]:
        """
        Kopiert Vorjahres-Planung als Basis für neues Geschäftsjahr.
        
        Args:
            geschaeftsjahr: z.B. '2025/26'
            bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
            standort: 1, 2, oder 3
            erstellt_von: Username
        
        Returns:
            Dict mit Anzahl kopierter Monate
        """
        from api.db_utils import db_session, row_to_dict
        
        # Vorjahr bestimmen
        vj_start = int(geschaeftsjahr.split('/')[0]) - 1
        vj_geschaeftsjahr = f"{vj_start}/{str(vj_start + 1)[2:]}"
        
        try:
            with db_session() as conn:
                cursor = conn.cursor()
                
                # Vorjahres-Planungen laden
                cursor.execute("""
                    SELECT * FROM abteilungsleiter_planung
                    WHERE geschaeftsjahr = %s AND bereich = %s AND standort = %s
                    ORDER BY monat
                """, (vj_geschaeftsjahr, bereich, standort))
                
                rows = cursor.fetchall()
                
                if not rows:
                    return {
                        'success': False,
                        'message': f'Keine Vorjahres-Planung gefunden für {vj_geschaeftsjahr}'
                    }
                
                # Zu Dict konvertieren
                vj_planungen = [row_to_dict(row) for row in rows]
                
                kopiert = 0
                
                # Für jeden Monat Vorjahres-Planung kopieren
                for vj_planung in vj_planungen:
                    # Basis-Werte aus Vorjahr übernehmen
                    # Aber Ziele neu berechnen (können sich ändern)
                    
                    # Planungsdaten aus Vorjahr extrahieren
                    planung_data = {}
                    for key in ['plan_stueck', 'plan_bruttoertrag_pro_fzg', 'plan_variable_kosten_prozent', 
                               'plan_verkaufspreis', 'plan_standzeit_tage', 'plan_stundensatz',
                               'plan_produktivitaet', 'plan_leistungsgrad', 'plan_anzahl_mechaniker',  # TAG 169: plan_auslastung → plan_anzahl_mechaniker
                               'plan_lagerumschlag', 'plan_penner_quote', 'plan_servicegrad',
                               'plan_umsatz', 'plan_marge_prozent', 'plan_ek_preis', 'plan_vk_preis_teile',
                               'plan_direkte_kosten']:
                        if key in vj_planung:
                            planung_data[key] = vj_planung[key]
                    
                    # Berechnung durchführen (neu, da sich Ziele ändern können)
                    if bereich in ['NW', 'GW']:
                        berechnung = AbteilungsleiterPlanungData.berechne_nw_gw_planung(
                            geschaeftsjahr=geschaeftsjahr,
                            monat=vj_planung['monat'],
                            bereich=bereich,
                            standort=standort,
                            planung_data=planung_data
                        )
                    elif bereich == 'Werkstatt':
                        berechnung = AbteilungsleiterPlanungData.berechne_werkstatt_planung(
                            geschaeftsjahr=geschaeftsjahr,
                            monat=vj_planung['monat'],
                            standort=standort,
                            planung_data=planung_data
                        )
                    elif bereich == 'Teile':
                        berechnung = AbteilungsleiterPlanungData.berechne_teile_planung(
                            geschaeftsjahr=geschaeftsjahr,
                            monat=vj_planung['monat'],
                            standort=standort,
                            planung_data=planung_data
                        )
                    else:
                        continue  # Sonstige noch nicht implementiert
                    
                    # Hybrid-Berechnung
                    hybrid = AbteilungsleiterPlanungData.berechne_hybrid_ziele(
                        berechnung['umsatz_basis'],
                        berechnung['db1_basis'],
                        geschaeftsjahr,
                        bereich,
                        standort
                    )
                    
                    # Zusammenführen
                    insert_data = {
                        'geschaeftsjahr': geschaeftsjahr,
                        'monat': vj_planung['monat'],
                        'bereich': bereich,
                        'standort': standort,
                        'status': 'entwurf',
                        'erstellt_von': erstellt_von,
                        **planung_data,  # Alle Planungsdaten aus Vorjahr
                        'umsatz_basis': berechnung['umsatz_basis'],
                        'db1_basis': berechnung['db1_basis'],
                        'db2_basis': berechnung.get('db2_basis', 0),
                        'aufhol_umsatz': hybrid['aufhol_umsatz'],
                        'aufhol_db1': hybrid['aufhol_db1'],
                        'umsatz_ziel': hybrid['umsatz_ziel'],
                        'db1_ziel': hybrid['db1_ziel'],
                        'db2_ziel': berechnung.get('db2_basis', 0)
                    }
                    
                    # SQL-Query bauen
                    columns = list(insert_data.keys())
                    values = [insert_data[col] for col in columns]
                    placeholders = ', '.join(['%s'] * len(values))
                    
                    query = f"""
                        INSERT INTO abteilungsleiter_planung ({', '.join(columns)})
                        VALUES ({placeholders})
                        ON CONFLICT (geschaeftsjahr, monat, bereich, standort)
                        DO UPDATE SET
                            {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['geschaeftsjahr', 'monat', 'bereich', 'standort']])},
                            geaendert_von = EXCLUDED.erstellt_von,
                            geaendert_am = CURRENT_TIMESTAMP
                    """
                    
                    cursor.execute(query, values)
                    kopiert += 1
                
                conn.commit()
                
                return {
                    'success': True,
                    'message': f'{kopiert} Monate vom Vorjahr kopiert',
                    'kopiert': kopiert
                }
                
        except Exception as e:
            logger.error(f"Fehler beim Kopieren des Vorjahres: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }

