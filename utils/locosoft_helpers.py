#!/usr/bin/env python3
"""
LOCOSOFT HELPERS - Daten aus PostgreSQL (gesynct von Locosoft)
=============================================================
Zentrale Funktionen für Auftragsarten, SVS und Klassifizierung.
Daten werden aus PostgreSQL gelesen (Sync-Tabellen).

Für Live-Daten (Auftragsdetails) wird Locosoft direkt abgefragt.

Sync-Script: scripts/imports/sync_charge_types.py

Funktionen:
- SVS (Stundenverrechnungssätze) aus charge_types_sync
- Auftragsart-Klassifizierung
- Fremdleistungs-Margen
- Abteilungs-Mapping

Author: Claude
Date: 2025-12-09 (TAG 110)
Updated: 2026-01-10 (TAG 177) - PostgreSQL Migration

⚠️ WICHTIG: Dieses Modul verwendet jetzt PostgreSQL statt SQLite!
"""

import os
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, date
from pathlib import Path

# SSOT: Standort/Betriebsnamen
from api.standort_utils import BETRIEB_NAMEN

# SSOT: DB-Verbindung (PostgreSQL)
from api.db_connection import get_db

logger = logging.getLogger(__name__)

# Projekt-Root-Pfad (basierend auf aktueller Datei)
PROJECT_ROOT = Path(__file__).parent.parent


def get_locosoft_connection():
    """Verbindung zu Locosoft PostgreSQL (nur für Live-Daten)"""
    import psycopg2
    from dotenv import load_dotenv
    
    env_path = PROJECT_ROOT / 'config' / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    
    return psycopg2.connect(
        host=os.getenv('LOCOSOFT_HOST'),
        port=os.getenv('LOCOSOFT_PORT', 5432),
        database=os.getenv('LOCOSOFT_DATABASE'),
        user=os.getenv('LOCOSOFT_USER'),
        password=os.getenv('LOCOSOFT_PASSWORD')
    )


# =============================================================================
# KONSTANTEN & MAPPINGS
# =============================================================================

# BETRIEB_NAMEN wird jetzt aus api.standort_utils importiert (SSOT)

# Abteilungen (department in charge_types)
ABTEILUNG_NAMEN = {
    1: 'Werkstatt',
    2: 'Karosserie',
    3: 'Lackierung',
    4: 'Intern',
    6: 'Garantie',
    9: 'Fremdleistung'
}

# Charge Type Kategorien (Fallback wenn nicht in DB)
CHARGE_TYPE_KATEGORIEN = {
    10: 'werkstatt_mechanik',
    11: 'werkstatt_wartung',
    15: 'werkstatt_elektrik',
    16: 'elektrofahrzeug',
    18: 'elektrofahrzeug_karosserie',
    12: 'leasing_alphabet',
    13: 'leasing_stellantis_bank',
    14: 'leasing_allgemein',
    17: 'leasing_ofl_ald',
    20: 'karosserie',
    30: 'lackierung',
    40: 'intern',
    88: 'intern_tuev',
    60: 'garantie',
    68: 'kulanz_gw',
    69: 'kulanz_nw',
    72: 'garantie_greiner',
    90: 'fremdleistung',
    91: 'fremdleistung_garantie',
}

# Labour Type Kategorien
LABOUR_TYPE_KATEGORIEN = {
    'W': 'werkstatt',
    'WA': 'werkstatt_abschlepp',
    'WE': 'werkstatt_garantie_verkauf',
    'WP': 'werkstatt_pannenhilfe',
    'WS': 'werkstatt_schnellservice',
    'WT': 'werkstatt_tankung',
    'WV': 'werkstatt_versicherung',
    'G': 'garantie',
    'GS': 'garantie_service',
    'K': 'kulanz_kunde',
    'k': 'kulanz_hersteller',
    'Ik': 'kulanz_intern',
    'I': 'intern',
    'Is': 'intern_service',
    'V': 'versicherung',
    'VA': 'versicherung_folge',
    'VG': 'versicherung_gw',
    'VN': 'versicherung_nw',
    'VO': 'versicherung_ohne_aufschlag',
    'R': 'reklamation',
    'M': 'mietwagen',
    'MV': 'mietwagen_vorfuehr',
    'MW': 'mietwagen_ersatz',
    'B': 'barverkauf',
    'T': 'teileverkauf',
    'F': 'fahrzeugverkauf',
    's': 'service_anbieter',
    'S': 'service_kunde',
}

# Invoice Types
INVOICE_TYPE_NAMEN = {
    2: 'Werkstatt',
    3: 'Reklamation',
    4: 'Intern',
    5: 'Bar-/Teileverkauf',
    6: 'Garantie',
    7: 'Neufahrzeug',
    8: 'Gebrauchtfahrzeug'
}


# =============================================================================
# SVS (STUNDENVERRECHNUNGSSÄTZE) - AUS POSTGRESQL
# =============================================================================

def hole_svs(betrieb: int = 1, charge_type: int = None) -> Dict[str, Any]:
    """
    Holt Stundenverrechnungssätze (AW-Preise) aus PostgreSQL.
    
    Daten werden aus charge_types_sync gelesen (Sync von Locosoft).
    
    Args:
        betrieb: Betriebsnummer (1=Deggendorf, 3=Landau)
        charge_type: Optional - spezifischer charge_type
        
    Returns:
        {
            'standard': 11.90,        # Type 10 (Mechanik)
            'wartung': 11.90,         # Type 11
            'elektrik': 12.90,        # Type 15
            'elektrofahrzeug': 17.90, # Type 16
            'karosserie': 21.00,      # Type 20
            'garantie': 8.43,         # Type 60
            'intern': 6.50,           # Type 40
            'fremdleistung': 15.50,   # Type 90
            'alle': {type: {...}, ...}
        }
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Prüfen ob Sync-Tabelle existiert (PostgreSQL)
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'charge_types_sync'
            )
        """)
        if not cursor.fetchone()[0]:
            conn.close()
            logger.warning("⚠️ charge_types_sync nicht gefunden - bitte sync_charge_types.py ausführen!")
            return _get_fallback_svs()
        
        # Daten laden (PostgreSQL: %s statt ?)
        cursor.execute("""
            SELECT 
                ct.type, 
                ct.timeunit_rate, 
                ct.stundensatz,
                ct.department, 
                ct.abteilung_name,
                ct.kategorie,
                ctd.description
            FROM charge_types_sync ct
            LEFT JOIN charge_type_descriptions_sync ctd ON ct.type = ctd.type
            WHERE ct.subsidiary = %s
            ORDER BY ct.type
        """, [betrieb])
        
        rows = cursor.fetchall()
        
        # Letzten Sync-Zeitpunkt holen
        cursor.execute("SELECT MAX(synced_at) FROM charge_types_sync WHERE subsidiary = %s", [betrieb])
        last_sync_row = cursor.fetchone()
        last_sync = last_sync_row[0] if last_sync_row and last_sync_row[0] else None
        
        conn.close()
        
        if not rows:
            logger.warning(f"⚠️ Keine charge_types für Betrieb {betrieb} gefunden")
            return _get_fallback_svs()
        
        # Ergebnis aufbauen (PostgreSQL HybridRow unterstützt dict-like access)
        alle = {}
        for row in rows:
            type_nr = row['type']
            rate = row['timeunit_rate']
            
            if rate and float(rate) > 0:
                alle[type_nr] = {
                    'aw_preis': float(rate),
                    'stundensatz': float(row['stundensatz'] or rate * 10),
                    'abteilung': row['department'],
                    'abteilung_name': row['abteilung_name'] or ABTEILUNG_NAMEN.get(row['department'], 'Unbekannt'),
                    'beschreibung': row['description'],
                    'kategorie': row['kategorie'] or CHARGE_TYPE_KATEGORIEN.get(type_nr, 'sonstige')
                }
        
        result = {
            'betrieb': betrieb,
            'betrieb_name': BETRIEB_NAMEN.get(betrieb, f'Betrieb {betrieb}'),
            'standard': alle.get(10, {}).get('aw_preis', 11.90),
            'wartung': alle.get(11, {}).get('aw_preis', 11.90),
            'elektrik': alle.get(15, {}).get('aw_preis', 12.90),
            'elektrofahrzeug': alle.get(16, {}).get('aw_preis', 17.90),
            'karosserie': alle.get(20, {}).get('aw_preis', 21.00),
            'lackierung': alle.get(30, {}).get('aw_preis', 0),
            'garantie': alle.get(60, {}).get('aw_preis', 8.43),
            'intern': alle.get(40, {}).get('aw_preis', 6.50),
            'fremdleistung': alle.get(90, {}).get('aw_preis', 15.50),
            'alle': alle,
            'last_sync': last_sync,
            'quelle': 'postgresql'
        }
        
        # Bei Einzelabfrage
        if charge_type:
            return {
                'aw_preis': alle.get(charge_type, {}).get('aw_preis', result['standard']),
                'details': alle.get(charge_type, {})
            }
        
        return result
        
    except Exception as e:
        logger.exception("Fehler beim Laden der SVS aus PostgreSQL")
        return _get_fallback_svs()


def _get_fallback_svs() -> Dict[str, Any]:
    """Fallback-Werte wenn DB nicht verfügbar"""
    return {
        'standard': 11.90,
        'wartung': 11.90,
        'elektrik': 12.90,
        'elektrofahrzeug': 17.90,
        'karosserie': 21.00,
        'garantie': 8.43,
        'intern': 6.50,
        'fremdleistung': 15.50,
        'alle': {},
        'quelle': 'fallback',
        'warning': 'Daten aus Fallback - bitte sync_charge_types.py ausführen!'
    }


def hole_aw_preis(betrieb: int, charge_type: int) -> float:
    """
    Holt den AW-Preis für einen spezifischen charge_type.
    Shortcut-Funktion für schnellen Zugriff.
    
    Returns:
        AW-Preis in € (z.B. 11.90)
    """
    result = hole_svs(betrieb, charge_type)
    return result.get('aw_preis', 11.90)


def hole_charge_type_info(charge_type: int, betrieb: int = 1) -> Dict[str, Any]:
    """
    Holt alle Infos zu einem charge_type.
    
    Returns:
        {
            'type': 10,
            'beschreibung': 'Lohn Mechanik',
            'aw_preis': 11.90,
            'stundensatz': 119.00,
            'abteilung': 1,
            'abteilung_name': 'Werkstatt',
            'kategorie': 'werkstatt_mechanik'
        }
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ct.type, 
                ctd.description,
                ct.timeunit_rate,
                ct.stundensatz,
                ct.department,
                ct.abteilung_name,
                ct.kategorie
            FROM charge_types_sync ct
            LEFT JOIN charge_type_descriptions_sync ctd ON ct.type = ctd.type
            WHERE ct.type = %s AND ct.subsidiary = %s
        """, [charge_type, betrieb])
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # PostgreSQL HybridRow unterstützt dict-like access
            return {
                'type': row['type'],
                'beschreibung': row['description'],
                'aw_preis': float(row['timeunit_rate'] or 0),
                'stundensatz': float(row['stundensatz'] or 0),
                'abteilung': row['department'],
                'abteilung_name': row['abteilung_name'],
                'kategorie': row['kategorie']
            }
        else:
            return {
                'type': charge_type,
                'beschreibung': f'Unbekannt ({charge_type})',
                'aw_preis': 11.90,
                'stundensatz': 119.00,
                'abteilung': 1,
                'abteilung_name': 'Werkstatt',
                'kategorie': CHARGE_TYPE_KATEGORIEN.get(charge_type, 'sonstige')
            }
            
    except Exception as e:
        logger.exception(f"Fehler bei hole_charge_type_info({charge_type})")
        return {'error': str(e)}


# Alias für Kompatibilität
hole_svs_aus_locosoft = hole_svs  # Deprecated, nutze hole_svs()


# =============================================================================
# AUFTRAGSART-KLASSIFIZIERUNG
# =============================================================================

def klassifiziere_auftragsart(
    charge_type: int = None,
    labour_type: str = None,
    invoice_type: int = None,
    marke: str = None
) -> Dict[str, Any]:
    """
    Klassifiziert einen Auftrag nach verschiedenen Kriterien.
    
    Args:
        charge_type: Berechnungsart (10, 60, 90, ...)
        labour_type: Arbeitsart (W, G, I, ...)
        invoice_type: Rechnungsart (2, 4, 6, ...)
        marke: Fahrzeugmarke (optional für Hersteller-Erkennung)
        
    Returns:
        {
            'kategorie': 'werkstatt_kunde',
            'kategorie_label': 'Werkstatt Kunde',
            'ist_garantie': False,
            'ist_intern': False,
            'ist_leasing': False,
            'ist_elektro': False,
            'ist_fremdleistung': False,
            'ist_versicherung': False,
            'abteilung': 'Werkstatt',
            'hersteller': 'Stellantis'  # bei Garantie
        }
    """
    result = {
        'kategorie': 'werkstatt_kunde',
        'kategorie_label': 'Werkstatt Kunde',
        'ist_garantie': False,
        'ist_kulanz': False,
        'ist_intern': False,
        'ist_leasing': False,
        'ist_elektro': False,
        'ist_fremdleistung': False,
        'ist_versicherung': False,
        'ist_karosserie': False,
        'ist_lackierung': False,
        'abteilung': 'Werkstatt',
        'hersteller': None
    }
    
    # Nach charge_type klassifizieren
    if charge_type:
        # Hole Kategorie aus DB (falls vorhanden)
        ct_info = hole_charge_type_info(charge_type)
        ct_kat = ct_info.get('kategorie', CHARGE_TYPE_KATEGORIEN.get(charge_type, ''))
        
        # Garantie
        if charge_type in range(60, 68) or ct_kat.startswith('garantie'):
            result['ist_garantie'] = True
            result['kategorie'] = 'garantie'
            result['kategorie_label'] = 'Garantie'
            result['abteilung'] = 'Garantie'
            
            # Hersteller aus Marke ableiten
            if marke:
                marke_lower = marke.lower()
                if any(m in marke_lower for m in ['opel', 'peugeot', 'citroen', 'fiat', 'jeep', 'alfa']):
                    result['hersteller'] = 'Stellantis'
                elif 'hyundai' in marke_lower:
                    result['hersteller'] = 'Hyundai'
                else:
                    result['hersteller'] = marke
        
        # Kulanz
        elif charge_type in [68, 69]:
            result['ist_kulanz'] = True
            result['kategorie'] = 'kulanz_gw' if charge_type == 68 else 'kulanz_nw'
            result['kategorie_label'] = 'Kulanz GW' if charge_type == 68 else 'Kulanz NW'
        
        # Intern
        elif charge_type in range(40, 50) or charge_type == 88:
            result['ist_intern'] = True
            result['kategorie'] = 'intern'
            result['kategorie_label'] = 'Intern'
            result['abteilung'] = 'Intern'
        
        # Leasing
        elif charge_type in [12, 13, 14, 17]:
            result['ist_leasing'] = True
            result['kategorie'] = ct_kat
            leasing_namen = {
                12: 'Alphabet',
                13: 'Stellantis Bank',
                14: 'Allg. Leasing',
                17: 'OFL/ALD'
            }
            result['kategorie_label'] = f'Leasing ({leasing_namen.get(charge_type, "")})'
        
        # Elektrofahrzeug
        elif charge_type in [16, 18]:
            result['ist_elektro'] = True
            result['kategorie'] = 'elektrofahrzeug'
            result['kategorie_label'] = 'Elektrofahrzeug'
        
        # Karosserie
        elif charge_type in range(20, 30):
            result['ist_karosserie'] = True
            result['kategorie'] = 'karosserie'
            result['kategorie_label'] = 'Karosserie'
            result['abteilung'] = 'Karosserie'
        
        # Lackierung
        elif charge_type in range(30, 40):
            result['ist_lackierung'] = True
            result['kategorie'] = 'lackierung'
            result['kategorie_label'] = 'Lackierung'
            result['abteilung'] = 'Lackierung'
        
        # Fremdleistung
        elif charge_type in range(90, 100):
            result['ist_fremdleistung'] = True
            result['kategorie'] = 'fremdleistung'
            result['kategorie_label'] = 'Fremdleistung'
            result['abteilung'] = 'Fremdleistung'
    
    # Nach labour_type verfeinern
    if labour_type:
        if labour_type in ['G', 'GS']:
            result['ist_garantie'] = True
            if not result['kategorie'].startswith('garantie'):
                result['kategorie'] = 'garantie'
                result['kategorie_label'] = 'Garantie'
        
        elif labour_type in ['K', 'k', 'Ik']:
            result['ist_kulanz'] = True
        
        elif labour_type in ['I', 'Is']:
            result['ist_intern'] = True
        
        elif labour_type in ['V', 'VA', 'VG', 'VN', 'VO', 'WV']:
            result['ist_versicherung'] = True
            if not result['kategorie'].startswith(('garantie', 'kulanz')):
                result['kategorie'] = 'versicherung'
                result['kategorie_label'] = 'Versicherung'
    
    # Nach invoice_type
    if invoice_type:
        if invoice_type == 6:
            result['ist_garantie'] = True
        elif invoice_type == 4:
            result['ist_intern'] = True
    
    return result


def hole_auftragsdetails(order_number: int) -> Dict[str, Any]:
    """
    Holt komplette Auftragsdetails inkl. Klassifizierung aus Locosoft.
    
    HINWEIS: Diese Funktion greift LIVE auf Locosoft zu (nicht PostgreSQL),
    da Auftragsdetails aktuelle Daten benötigen.
    
    Returns:
        {
            'order_number': 219379,
            'betrieb': 1,
            'kennzeichen': 'DEG-X 212',
            'marke': 'Opel',
            'kunde': 'Mustermann, Max',
            'serviceberater': 'Sandra Müller',
            'positionen': [...],
            'klassifizierung': {...},
            'summen': {...}
        }
    """
    try:
        conn = get_locosoft_connection()
        cur = conn.cursor()
        
        # Auftragskopf
        cur.execute("""
            SELECT 
                o.number,
                o.subsidiary,
                o.order_date,
                o.order_taking_employee_no,
                eh.name as serviceberater,
                v.license_plate,
                m.description as marke,
                mo.description as modell,
                COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name) as kunde
            FROM orders o
            LEFT JOIN employees_history eh ON o.order_taking_employee_no = eh.employee_number 
                AND eh.is_latest_record = true
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN models mo ON v.make_number = mo.make_number AND v.model_code = mo.model_code
            LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
            WHERE o.number = %s
        """, [order_number])
        
        kopf = cur.fetchone()
        if not kopf:
            cur.close()
            conn.close()
            return {'error': f'Auftrag {order_number} nicht gefunden'}
        
        betrieb = kopf[1]
        
        # Positionen
        cur.execute("""
            SELECT 
                l.order_position,
                l.charge_type,
                l.labour_type,
                l.invoice_type,
                l.mechanic_no,
                eh.name as mechaniker,
                l.time_units as aw,
                l.net_price_in_order as netto_vk,
                l.usage_value as einsatzwert,
                l.text_line as beschreibung
            FROM labours l
            LEFT JOIN employees_history eh ON l.mechanic_no = eh.employee_number 
                AND eh.is_latest_record = true
            WHERE l.order_number = %s
            ORDER BY l.order_position, l.order_position_line
        """, [order_number])
        
        positionen_raw = cur.fetchall()
        cur.close()
        conn.close()
        
        # Positionen aufbereiten
        positionen = []
        total_aw = 0
        total_vk = 0
        total_ek = 0
        haupt_charge_type = None
        haupt_labour_type = None
        
        for pos in positionen_raw:
            aw = float(pos[6] or 0)
            vk = float(pos[7] or 0)
            ek = float(pos[8] or 0)
            
            total_aw += aw
            total_vk += vk
            total_ek += ek
            
            # Haupttyp für Klassifizierung (erste Position mit AW)
            if aw > 0 and not haupt_charge_type:
                haupt_charge_type = pos[1]
                haupt_labour_type = pos[2]
            
            # AW-Preis aus PostgreSQL
            ct_info = hole_charge_type_info(pos[1], betrieb)
            
            positionen.append({
                'position': pos[0],
                'charge_type': pos[1],
                'charge_type_name': ct_info.get('beschreibung', f'Type {pos[1]}'),
                'labour_type': pos[2],
                'invoice_type': pos[3],
                'mechaniker_nr': pos[4],
                'mechaniker': pos[5],
                'aw': aw,
                'netto_vk': vk,
                'einsatzwert': ek,
                'marge': vk - ek if ek > 0 else vk,
                'aw_preis': ct_info.get('aw_preis', 11.90),
                'beschreibung': pos[9]
            })
        
        # Klassifizierung
        klassifizierung = klassifiziere_auftragsart(
            charge_type=haupt_charge_type,
            labour_type=haupt_labour_type,
            marke=kopf[6]
        )
        
        return {
            'order_number': kopf[0],
            'betrieb': betrieb,
            'betrieb_name': BETRIEB_NAMEN.get(betrieb, f'Betrieb {betrieb}'),
            'datum': kopf[2].strftime('%Y-%m-%d') if kopf[2] else None,
            'serviceberater_nr': kopf[3],
            'serviceberater': kopf[4],
            'kennzeichen': kopf[5],
            'marke': kopf[6],
            'modell': kopf[7],
            'kunde': kopf[8],
            'klassifizierung': klassifizierung,
            'positionen': positionen,
            'summen': {
                'vorgabe_aw': round(total_aw, 1),
                'netto_vk': round(total_vk, 2),
                'einsatzwert': round(total_ek, 2),
                'marge': round(total_vk - total_ek, 2),
                'marge_prozent': round((total_vk - total_ek) / total_vk * 100, 1) if total_vk > 0 else 0
            }
        }
        
    except Exception as e:
        logger.exception(f"Fehler beim Laden von Auftrag {order_number}")
        return {'error': str(e)}


# =============================================================================
# FREMDLEISTUNGS-MARGEN
# =============================================================================

def berechne_fremdleistung_marge(
    netto_vk: float, 
    einsatzwert: float
) -> Dict[str, float]:
    """
    Berechnet die Marge bei Fremdleistungen (Lackierer etc.)
    
    Args:
        netto_vk: Verkaufspreis netto (was Kunde zahlt)
        einsatzwert: Einkaufspreis (was es uns kostet)
        
    Returns:
        {
            'marge_eur': 107.60,
            'marge_prozent': 39.7,
            'aufschlag_prozent': 65.9
        }
    """
    if netto_vk is None or einsatzwert is None:
        return {'marge_eur': 0, 'marge_prozent': 0, 'aufschlag_prozent': 0}
    
    marge = netto_vk - einsatzwert
    
    return {
        'marge_eur': round(marge, 2),
        'marge_prozent': round(marge / netto_vk * 100, 1) if netto_vk > 0 else 0,
        'aufschlag_prozent': round(marge / einsatzwert * 100, 1) if einsatzwert > 0 else 0
    }


def hole_fremdleistungen_statistik(
    betrieb: int = None,
    datum_von: date = None,
    datum_bis: date = None
) -> Dict[str, Any]:
    """
    Holt Statistik über Fremdleistungen (charge_type 90-99) aus Locosoft.
    
    Returns:
        {
            'anzahl_positionen': 45,
            'summe_vk': 12500.00,
            'summe_ek': 8200.00,
            'summe_marge': 4300.00,
            'marge_prozent': 34.4,
            'nach_typ': {...}
        }
    """
    try:
        conn = get_locosoft_connection()
        cur = conn.cursor()
        
        query = """
            SELECT 
                l.charge_type,
                COUNT(*) as anzahl,
                SUM(l.net_price_in_order) as summe_vk,
                SUM(l.usage_value) as summe_ek
            FROM labours l
            JOIN invoices i ON l.order_number = i.order_number 
                AND l.invoice_type = i.invoice_type 
                AND l.invoice_number = i.invoice_number
            WHERE l.charge_type BETWEEN 90 AND 99
              AND l.net_price_in_order > 0
              AND i.is_canceled = false
        """
        
        params = []
        if betrieb:
            query += " AND i.subsidiary = %s"
            params.append(betrieb)
        if datum_von:
            query += " AND i.invoice_date >= %s"
            params.append(datum_von)
        if datum_bis:
            query += " AND i.invoice_date <= %s"
            params.append(datum_bis)
        
        query += " GROUP BY l.charge_type ORDER BY l.charge_type"
        
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        total_vk = 0
        total_ek = 0
        total_anzahl = 0
        nach_typ = {}
        
        for row in rows:
            ct, anzahl, vk, ek = row
            vk = float(vk or 0)
            ek = float(ek or 0)
            
            total_anzahl += anzahl
            total_vk += vk
            total_ek += ek
            
            # Beschreibung aus PostgreSQL
            ct_info = hole_charge_type_info(ct)
            
            nach_typ[ct] = {
                'beschreibung': ct_info.get('beschreibung', f'Type {ct}'),
                'anzahl': anzahl,
                'summe_vk': round(vk, 2),
                'summe_ek': round(ek, 2),
                'marge': round(vk - ek, 2),
                'marge_prozent': round((vk - ek) / vk * 100, 1) if vk > 0 else 0
            }
        
        return {
            'anzahl_positionen': total_anzahl,
            'summe_vk': round(total_vk, 2),
            'summe_ek': round(total_ek, 2),
            'summe_marge': round(total_vk - total_ek, 2),
            'marge_prozent': round((total_vk - total_ek) / total_vk * 100, 1) if total_vk > 0 else 0,
            'nach_typ': nach_typ
        }
        
    except Exception as e:
        logger.exception("Fehler bei Fremdleistungs-Statistik")
        return {'error': str(e)}


# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def ist_produktiver_auftrag(charge_type: int, labour_type: str = None) -> bool:
    """
    Prüft ob ein Auftrag als produktive Werkstattarbeit zählt.
    Für Nachkalkulation/Leistungsgrad relevant.
    
    Ausgeschlossen:
    - Erlöse ohne echte Arbeit (50-59, 70-89)
    - Reine Textpositionen (charge_type 0)
    """
    if charge_type is None:
        return False
    
    # Erlöse ohne echte Arbeit
    if charge_type in range(50, 60):
        return False
    if charge_type in range(70, 90):
        return False
    if charge_type == 0:
        return False
    
    # Fahrzeugverkauf
    if labour_type == 'F':
        return False
    
    return True


def hole_abteilung_fuer_charge_type(charge_type: int, betrieb: int = 1) -> Tuple[int, str]:
    """
    Gibt Abteilungsnummer und -name für einen charge_type zurück.
    """
    ct_info = hole_charge_type_info(charge_type, betrieb)
    
    if 'abteilung' in ct_info and ct_info['abteilung']:
        return (ct_info['abteilung'], ct_info.get('abteilung_name', 'Unbekannt'))
    
    # Fallback
    if charge_type in range(20, 30):
        return (2, 'Karosserie')
    elif charge_type in range(30, 40):
        return (3, 'Lackierung')
    elif charge_type in range(40, 50) or charge_type == 88:
        return (4, 'Intern')
    elif charge_type in range(60, 70):
        return (6, 'Garantie')
    elif charge_type in range(90, 100):
        return (9, 'Fremdleistung')
    else:
        return (1, 'Werkstatt')


# =============================================================================
# TESTS
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("LOCOSOFT HELPERS - TESTS (PostgreSQL-Version)")
    print("=" * 70)
    
    print("\n1. SVS (Stundenverrechnungssätze) aus PostgreSQL:")
    print("-" * 50)
    svs = hole_svs(betrieb=1)
    
    if svs.get('quelle') == 'fallback':
        print(f"  ⚠️  WARNUNG: {svs.get('warning')}")
    else:
        print(f"  Quelle: {svs.get('quelle', 'unbekannt')}")
        print(f"  Letzter Sync: {svs.get('last_sync', 'unbekannt')}")
    
    print(f"  Standard (Mechanik):  {svs['standard']:>6.2f} €/AW = {svs['standard']*10:>6.2f} €/h")
    print(f"  Elektrik:             {svs['elektrik']:>6.2f} €/AW = {svs['elektrik']*10:>6.2f} €/h")
    print(f"  Elektrofahrzeug:      {svs['elektrofahrzeug']:>6.2f} €/AW = {svs['elektrofahrzeug']*10:>6.2f} €/h")
    print(f"  Karosserie:           {svs['karosserie']:>6.2f} €/AW = {svs['karosserie']*10:>6.2f} €/h")
    print(f"  Garantie:             {svs['garantie']:>6.2f} €/AW = {svs['garantie']*10:>6.2f} €/h")
    print(f"  Intern:               {svs['intern']:>6.2f} €/AW = {svs['intern']*10:>6.2f} €/h")
    print(f"  Fremdleistung:        {svs['fremdleistung']:>6.2f} €/AW = {svs['fremdleistung']*10:>6.2f} €/h")
    
    print("\n2. Charge-Type Info:")
    print("-" * 50)
    for ct in [10, 16, 20, 60, 90]:
        info = hole_charge_type_info(ct)
        print(f"  Type {ct}: {info.get('beschreibung', '-'):<30} | {info.get('aw_preis', 0):.2f} €/AW | {info.get('kategorie', '-')}")
    
    print("\n3. Auftragsart-Klassifizierung:")
    print("-" * 50)
    
    # Werkstatt Kunde
    k1 = klassifiziere_auftragsart(charge_type=10, labour_type='W')
    print(f"  charge_type=10, labour_type=W: {k1['kategorie_label']}")
    
    # Garantie
    k2 = klassifiziere_auftragsart(charge_type=60, labour_type='G', marke='Opel')
    print(f"  charge_type=60, labour_type=G, Opel: {k2['kategorie_label']} ({k2['hersteller']})")
    
    # Elektrofahrzeug
    k3 = klassifiziere_auftragsart(charge_type=16)
    print(f"  charge_type=16: {k3['kategorie_label']}")
    
    # Leasing
    k4 = klassifiziere_auftragsart(charge_type=12)
    print(f"  charge_type=12: {k4['kategorie_label']}")
    
    print("\n4. Fremdleistungs-Marge:")
    print("-" * 50)
    marge = berechne_fremdleistung_marge(netto_vk=270.80, einsatzwert=163.20)
    print(f"  VK: 270,80 € | EK: 163,20 €")
    print(f"  Marge: {marge['marge_eur']:.2f} € ({marge['marge_prozent']:.1f}%)")
    print(f"  Aufschlag: {marge['aufschlag_prozent']:.1f}%")
    
    print("\n" + "=" * 70)
    print("✅ Tests abgeschlossen!")
    print("=" * 70)
