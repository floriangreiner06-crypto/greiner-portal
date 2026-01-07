#!/usr/bin/env python3
"""
Serviceberater Data Module - Single Source of Truth
===================================================
Datenmodul für Serviceberater-KPIs direkt aus Locosoft.

Architektur:
- Class-based Pattern (ServiceberaterData)
- Statische Methoden für wiederverwendbare Datenabfragen
- Nutzt echte Locosoft-Tabellen (invoices, orders, employees_history)
- Keine Business Logic (nur Datenabruf + Aggregation)
- PostgreSQL-kompatibel

Consumer:
- api/serviceberater_api.py (Web-UI Endpoints)
- scripts/send_daily_serviceberater.py (E-Mail Reports, später)

TAG 164: Initiale Implementierung (SSOT-Refactoring)
Author: Claude AI
Date: 2026-01-03
Pattern: docs/DATENMODUL_PATTERN.md
"""

from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any
from psycopg2.extras import RealDictCursor

from api.db_utils import get_locosoft_connection, locosoft_session, row_to_dict
from api.serviceberater_api import TEK_CONFIG


class ServiceberaterData:
    """
    Single Source of Truth für Serviceberater-Daten aus Locosoft.
    
    Bereiche:
    - Umsatz: get_sb_umsatz_heute(), get_sb_umsatz_monat()
    - Ziele: get_sb_umsatz_ziel_aus_1pct() (in serviceberater_api.py)
    """
    
    @staticmethod
    def get_sb_umsatz_heute(ma_id: int, datum: date) -> Dict[str, Any]:
        """
        Holt Serviceberater-Umsatz für heute.
        
        Args:
            ma_id: Locosoft MA-ID (z.B. 4000)
            datum: Datum (YYYY-MM-DD)
        
        Returns:
            dict: {
                'anzahl_rechnungen': int,
                'umsatz_gesamt': float,
                'umsatz_arbeit': float,
                'umsatz_teile': float,
                'db1': float
            }
        
        Example:
            >>> data = ServiceberaterData.get_sb_umsatz_heute(4000, date(2026, 1, 3))
            >>> print(data['umsatz_gesamt'])
            3200.00
        """
        start_datum = datum.isoformat()
        ende_datum = (datum + timedelta(days=1)).isoformat()
        
        try:
            conn = get_locosoft_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT i.invoice_number) as anzahl_rechnungen,
                    SUM(i.total_gross) as umsatz_gesamt,
                    SUM(i.job_amount_gross) as umsatz_arbeit,
                    SUM(i.part_amount_gross) as umsatz_teile
                FROM invoices i
                JOIN orders o ON i.order_number = o.number
                WHERE o.order_taking_employee_no = %s
                  AND i.invoice_date >= %s
                  AND i.invoice_date < %s
                  AND i.is_canceled = false
                  AND i.total_gross > 0
                  AND i.invoice_type IN (2, 3, 6)
            """, (ma_id, start_datum, ende_datum))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not row:
                return {
                    'anzahl_rechnungen': 0,
                    'umsatz_gesamt': 0.0,
                    'umsatz_arbeit': 0.0,
                    'umsatz_teile': 0.0,
                    'db1': 0.0
                }
            
            umsatz = float(row['umsatz_gesamt'] or 0)
            arbeit = float(row['umsatz_arbeit'] or 0)
            teile = float(row['umsatz_teile'] or 0)
            db1 = (arbeit * TEK_CONFIG['marge_arbeit']) + (teile * TEK_CONFIG['marge_teile'])
            
            return {
                'anzahl_rechnungen': row['anzahl_rechnungen'] or 0,
                'umsatz_gesamt': round(umsatz, 2),
                'umsatz_arbeit': round(arbeit, 2),
                'umsatz_teile': round(teile, 2),
                'db1': round(db1, 2)
            }
            
        except Exception as e:
            print(f"Fehler in get_sb_umsatz_heute: {e}")
            return {
                'anzahl_rechnungen': 0,
                'umsatz_gesamt': 0.0,
                'umsatz_arbeit': 0.0,
                'umsatz_teile': 0.0,
                'db1': 0.0
            }
    
    @staticmethod
    def get_sb_umsatz_monat(ma_id: int, monat: int, jahr: int) -> Dict[str, Any]:
        """
        Holt Serviceberater-Umsatz für Monat.
        
        Args:
            ma_id: Locosoft MA-ID (z.B. 4000)
            monat: Kalendermonat (1-12)
            jahr: Jahr (YYYY)
        
        Returns:
            dict: {
                'anzahl_rechnungen': int,
                'umsatz_gesamt': float,
                'umsatz_arbeit': float,
                'umsatz_teile': float,
                'db1': float
            }
        
        Example:
            >>> data = ServiceberaterData.get_sb_umsatz_monat(4000, 1, 2026)
            >>> print(data['umsatz_gesamt'])
            11454.55
        """
        start_monat = f"{jahr}-{monat:02d}-01"
        if monat == 12:
            ende_monat = f"{jahr+1}-01-01"
        else:
            ende_monat = f"{jahr}-{monat+1:02d}-01"
        
        try:
            conn = get_locosoft_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT i.invoice_number) as anzahl_rechnungen,
                    SUM(i.total_gross) as umsatz_gesamt,
                    SUM(i.job_amount_gross) as umsatz_arbeit,
                    SUM(i.part_amount_gross) as umsatz_teile
                FROM invoices i
                JOIN orders o ON i.order_number = o.number
                WHERE o.order_taking_employee_no = %s
                  AND i.invoice_date >= %s
                  AND i.invoice_date < %s
                  AND i.is_canceled = false
                  AND i.total_gross > 0
                  AND i.invoice_type IN (2, 3, 6)
            """, (ma_id, start_monat, ende_monat))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not row:
                return {
                    'anzahl_rechnungen': 0,
                    'umsatz_gesamt': 0.0,
                    'umsatz_arbeit': 0.0,
                    'umsatz_teile': 0.0,
                    'db1': 0.0
                }
            
            umsatz = float(row['umsatz_gesamt'] or 0)
            arbeit = float(row['umsatz_arbeit'] or 0)
            teile = float(row['umsatz_teile'] or 0)
            db1 = (arbeit * TEK_CONFIG['marge_arbeit']) + (teile * TEK_CONFIG['marge_teile'])
            
            return {
                'anzahl_rechnungen': row['anzahl_rechnungen'] or 0,
                'umsatz_gesamt': round(umsatz, 2),
                'umsatz_arbeit': round(arbeit, 2),
                'umsatz_teile': round(teile, 2),
                'db1': round(db1, 2)
            }
            
        except Exception as e:
            print(f"Fehler in get_sb_umsatz_monat: {e}")
            return {
                'anzahl_rechnungen': 0,
                'umsatz_gesamt': 0.0,
                'umsatz_arbeit': 0.0,
                'umsatz_teile': 0.0,
                'db1': 0.0
            }


class KundenzentraleData:
    """
    Single Source of Truth für Kundenzentrale-Daten (Fakturierung).
    
    TAG 164: Initiale Implementierung
    """
    
    @staticmethod
    def get_fakturierung_heute(datum: date, subsidiaries: list = None) -> Dict[str, Any]:
        """
        Holt Fakturierung für heute (alle externen Rechnungen).
        
        Args:
            datum: Datum (YYYY-MM-DD)
            subsidiaries: Liste von Standort-IDs [1, 2, 3] oder None für alle
        
        Returns:
            dict: {
                'anzahl_rechnungen': int,
                'umsatz_gesamt': float,
                'umsatz_werkstatt': float,
                'umsatz_verkauf': float,
                'umsatz_teile': float,
                'umsatz_sonstiges': float
            }
        """
        start_datum = datum.isoformat()
        ende_datum = (datum + timedelta(days=1)).isoformat()
        
        # Standort-Filter
        if subsidiaries and len(subsidiaries) < 3:
            standort_filter = "AND i.subsidiary = ANY(%s)"
            params = [start_datum, ende_datum, subsidiaries]
        else:
            standort_filter = ""
            params = [start_datum, ende_datum]
        
        try:
            conn = get_locosoft_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = f"""
                SELECT
                    COUNT(DISTINCT i.invoice_number) as anzahl_rechnungen,
                    SUM(i.total_gross) as umsatz_gesamt,
                    SUM(CASE WHEN i.invoice_type IN (2, 3, 6) THEN i.total_gross ELSE 0 END) as umsatz_werkstatt,
                    SUM(CASE WHEN i.invoice_type IN (7, 8) THEN i.total_gross ELSE 0 END) as umsatz_verkauf,
                    SUM(CASE WHEN i.invoice_type = 1 THEN i.total_gross ELSE 0 END) as umsatz_teile,
                    SUM(CASE WHEN i.invoice_type NOT IN (1, 2, 3, 6, 7, 8) THEN i.total_gross ELSE 0 END) as umsatz_sonstiges
                FROM invoices i
                LEFT JOIN orders o ON i.order_number = o.number
                LEFT JOIN customers_suppliers cs ON COALESCE(o.order_customer, i.customer_number) = cs.customer_number
                WHERE DATE(i.invoice_date) = %s
                  AND i.is_canceled = false
                  AND i.total_gross > 0
                  AND (cs.customer_number IS NULL OR cs.customer_number != 3000001)
                  {standort_filter}
            """
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not row:
                return {
                    'anzahl_rechnungen': 0,
                    'umsatz_gesamt': 0.0,
                    'umsatz_werkstatt': 0.0,
                    'umsatz_verkauf': 0.0,
                    'umsatz_teile': 0.0,
                    'umsatz_sonstiges': 0.0
                }
            
            return {
                'anzahl_rechnungen': row['anzahl_rechnungen'] or 0,
                'umsatz_gesamt': round(float(row['umsatz_gesamt'] or 0), 2),
                'umsatz_werkstatt': round(float(row['umsatz_werkstatt'] or 0), 2),
                'umsatz_verkauf': round(float(row['umsatz_verkauf'] or 0), 2),
                'umsatz_teile': round(float(row['umsatz_teile'] or 0), 2),
                'umsatz_sonstiges': round(float(row['umsatz_sonstiges'] or 0), 2)
            }
            
        except Exception as e:
            print(f"Fehler in get_fakturierung_heute: {e}")
            return {
                'anzahl_rechnungen': 0,
                'umsatz_gesamt': 0.0,
                'umsatz_werkstatt': 0.0,
                'umsatz_verkauf': 0.0,
                'umsatz_teile': 0.0,
                'umsatz_sonstiges': 0.0
            }
    
    @staticmethod
    def get_fakturierung_monat(monat: int, jahr: int, subsidiaries: list = None) -> Dict[str, Any]:
        """
        Holt Fakturierung für Monat (alle externen Rechnungen).
        
        Args:
            monat: Kalendermonat (1-12)
            jahr: Jahr (YYYY)
            subsidiaries: Liste von Standort-IDs [1, 2, 3] oder None für alle
        
        Returns:
            dict: {
                'anzahl_rechnungen': int,
                'umsatz_gesamt': float,
                'umsatz_werkstatt': float,
                'umsatz_verkauf': float,
                'umsatz_teile': float,
                'umsatz_sonstiges': float
            }
        """
        start_monat = f"{jahr}-{monat:02d}-01"
        if monat == 12:
            ende_monat = f"{jahr+1}-01-01"
        else:
            ende_monat = f"{jahr}-{monat+1:02d}-01"
        
        # Standort-Filter
        if subsidiaries and len(subsidiaries) < 3:
            standort_filter = "AND i.subsidiary = ANY(%s)"
            params = [start_monat, ende_monat, subsidiaries]
        else:
            standort_filter = ""
            params = [start_monat, ende_monat]
        
        try:
            conn = get_locosoft_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = f"""
                SELECT
                    COUNT(DISTINCT i.invoice_number) as anzahl_rechnungen,
                    SUM(i.total_gross) as umsatz_gesamt,
                    SUM(CASE WHEN i.invoice_type IN (2, 3, 6) THEN i.total_gross ELSE 0 END) as umsatz_werkstatt,
                    SUM(CASE WHEN i.invoice_type IN (7, 8) THEN i.total_gross ELSE 0 END) as umsatz_verkauf,
                    SUM(CASE WHEN i.invoice_type = 1 THEN i.total_gross ELSE 0 END) as umsatz_teile,
                    SUM(CASE WHEN i.invoice_type NOT IN (1, 2, 3, 6, 7, 8) THEN i.total_gross ELSE 0 END) as umsatz_sonstiges
                FROM invoices i
                LEFT JOIN orders o ON i.order_number = o.number
                LEFT JOIN customers_suppliers cs ON COALESCE(o.order_customer, i.customer_number) = cs.customer_number
                WHERE i.invoice_date >= %s
                  AND i.invoice_date < %s
                  AND i.is_canceled = false
                  AND i.total_gross > 0
                  AND (cs.customer_number IS NULL OR cs.customer_number != 3000001)
                  {standort_filter}
            """
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not row:
                return {
                    'anzahl_rechnungen': 0,
                    'umsatz_gesamt': 0.0,
                    'umsatz_werkstatt': 0.0,
                    'umsatz_verkauf': 0.0,
                    'umsatz_teile': 0.0,
                    'umsatz_sonstiges': 0.0
                }
            
            return {
                'anzahl_rechnungen': row['anzahl_rechnungen'] or 0,
                'umsatz_gesamt': round(float(row['umsatz_gesamt'] or 0), 2),
                'umsatz_werkstatt': round(float(row['umsatz_werkstatt'] or 0), 2),
                'umsatz_verkauf': round(float(row['umsatz_verkauf'] or 0), 2),
                'umsatz_teile': round(float(row['umsatz_teile'] or 0), 2),
                'umsatz_sonstiges': round(float(row['umsatz_sonstiges'] or 0), 2)
            }
            
        except Exception as e:
            print(f"Fehler in get_fakturierung_monat: {e}")
            return {
                'anzahl_rechnungen': 0,
                'umsatz_gesamt': 0.0,
                'umsatz_werkstatt': 0.0,
                'umsatz_verkauf': 0.0,
                'umsatz_teile': 0.0,
                'umsatz_sonstiges': 0.0
            }

