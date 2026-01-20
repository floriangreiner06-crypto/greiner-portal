#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vacation Year Utilities - Automatische Jahreswechsel-Logik
==========================================================
TAG 198: Erstellt automatisch vacation_entitlements und Views für neues Jahr
"""

import logging
from datetime import datetime

from api.db_utils import db_session

logger = logging.getLogger(__name__)

# Standard-Urlaubsanspruch
DEFAULT_VACATION_DAYS = 27.0


def ensure_vacation_year_setup(year: int) -> bool:
    """
    Stellt sicher, dass für ein Jahr alle notwendigen Daten existieren:
    1. vacation_entitlements Einträge (Standard 27 Tage)
    2. View v_vacation_balance_{year}
    
    Args:
        year: Jahr (z.B. 2026, 2027)
    
    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            
            # 1. Prüfe ob View existiert
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.views 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """, (f'v_vacation_balance_{year}',))
            
            view_exists = cursor.fetchone()[0]
            
            # 2. Prüfe ob vacation_entitlements für Jahr existieren
            cursor.execute("""
                SELECT COUNT(*) 
                FROM vacation_entitlements 
                WHERE year = %s
            """, (year,))
            
            entitlements_count = cursor.fetchone()[0]
            
            # 3. Hole Anzahl aktiver Mitarbeiter
            cursor.execute("""
                SELECT COUNT(*) 
                FROM employees 
                WHERE aktiv = true
            """)
            
            active_employees_count = cursor.fetchone()[0]
            
            # 4. Erstelle vacation_entitlements für alle aktiven Mitarbeiter (wenn nicht vorhanden)
            if entitlements_count < active_employees_count:
                logger.info(f"Erstelle vacation_entitlements für {year}...")
                
                # TAG 198: Vereinfachte Version - Standard 27 Tage, Resturlaub wird später berechnet
                # Verwende die einfache Funktion
                return ensure_vacation_year_setup_simple(year)
            
            # 5. Erstelle View (wenn nicht vorhanden)
            if not view_exists:
                logger.info(f"Erstelle View v_vacation_balance_{year}...")
                
                # Verwende die Funktion aus dem Migration-Script
                cursor.execute(f"""
                    SELECT create_vacation_balance_view({year})
                """)
                
                logger.info(f"✅ View v_vacation_balance_{year} erstellt")
                conn.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"Fehler bei ensure_vacation_year_setup({year}): {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def ensure_vacation_year_setup_simple(year: int) -> bool:
    """
    Vereinfachte Version: Erstellt nur Standard-Ansprüche (27 Tage) ohne Resturlaub-Berechnung.
    Wird verwendet wenn Resturlaub-Berechnung fehlschlägt.
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Erstelle vacation_entitlements für alle aktiven Mitarbeiter
            cursor.execute("""
                INSERT INTO vacation_entitlements (employee_id, year, total_days, carried_over, added_manually, updated_at)
                SELECT 
                    e.id,
                    %s as year,
                    %s as total_days,
                    0 as carried_over,
                    0 as added_manually,
                    CURRENT_TIMESTAMP
                FROM employees e
                WHERE e.aktiv = true
                  AND e.id NOT IN (
                      SELECT employee_id 
                      FROM vacation_entitlements 
                      WHERE year = %s
                  )
                ON CONFLICT DO NOTHING
            """, (year, DEFAULT_VACATION_DAYS, year))
            
            created_count = cursor.rowcount
            
            # Erstelle View (wenn nicht vorhanden)
            try:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.views 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, (f'v_vacation_balance_{year}',))
                view_exists = cursor.fetchone()[0]
                
                if not view_exists:
                    cursor.execute(f"""
                        SELECT create_vacation_balance_view({year})
                    """)
                    logger.info(f"✅ View v_vacation_balance_{year} erstellt")
            except Exception as view_error:
                logger.warning(f"⚠️ View-Erstellung fehlgeschlagen (möglicherweise existiert sie bereits): {view_error}")
            
            conn.commit()
            logger.info(f"✅ {created_count} vacation_entitlements für {year} erstellt (Standard)")
            return True
            
    except Exception as e:
        logger.error(f"Fehler bei ensure_vacation_year_setup_simple({year}): {e}")
        return False
