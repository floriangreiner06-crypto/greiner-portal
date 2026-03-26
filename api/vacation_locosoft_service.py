#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
VACATION LOCOSOFT SERVICE
========================================
TAG 103 - Abwesenheitsdaten aus Locosoft

Holt echte Abwesenheitsdaten aus Locosoft PostgreSQL:
- Urlaub (Url, BUr) – nur diese mindern den Resturlaub im Portal (Rest = min(Portal-Rest, Anspruch − Locosoft-Urlaub))
- Zeitausgleich (ZA.) – wird getrennt geführt und mindert den Resturlaub nicht
- Krank (Krn)
- Sonstige (Sch, Sem, Snd, etc.)
"""

from typing import Dict, List, Optional
from functools import lru_cache
from datetime import datetime

# Zentrale DB-Utilities (TAG117)
from api.db_utils import get_locosoft_connection


def get_absences_for_employee(locosoft_id: int, year: int = 2025) -> Dict:
    """
    Holt Abwesenheitsdaten für einen Mitarbeiter aus Locosoft
    
    Args:
        locosoft_id: employee_number aus Locosoft
        year: Jahr
        
    Returns:
        {
            'urlaub': 27.0,      # Url + BUr
            'zeitausgleich': 5.0, # ZA.
            'krank': 3.0,         # Krn
            'sonstige': 0.0,      # Sch, Sem, Snd, etc.
            'details': {...}       # Aufschlüsselung nach reason
        }
    """
    if not locosoft_id:
        return {
            'urlaub': 0,
            'zeitausgleich': 0,
            'krank': 0,
            'sonstige': 0,
            'details': {}
        }
    
    try:
        conn = get_locosoft_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                reason,
                COALESCE(SUM(day_contingent), 0) as tage
            FROM absence_calendar
            WHERE employee_number = %s
              AND date >= %s AND date <= %s
            GROUP BY reason
        """, (locosoft_id, f'{year}-01-01', f'{year}-12-31'))
        
        details = {}
        urlaub = 0
        zeitausgleich = 0
        krank = 0
        sonstige = 0
        
        for row in cur.fetchall():
            reason = row[0]
            tage = float(row[1] or 0)
            details[reason] = tage
            if reason in ('Url', 'BUr'):
                urlaub += tage
            elif reason == 'ZA.':
                zeitausgleich += tage
            elif reason == 'Krn':
                krank += tage
            else:
                sonstige += tage
        
        conn.close()
        
        return {
            'urlaub': round(urlaub, 2),
            'zeitausgleich': round(zeitausgleich, 2),
            'krank': round(krank, 2),
            'sonstige': round(sonstige, 2),
            'details': details
        }
        
    except Exception as e:
        print(f"Locosoft-Fehler für {locosoft_id}: {e}")
        return {
            'urlaub': 0,
            'zeitausgleich': 0,
            'krank': 0,
            'sonstige': 0,
            'details': {},
            'error': str(e)
        }


def get_absences_for_employees(locosoft_ids: List[int], year: int = 2025) -> Dict[int, Dict]:
    """
    Holt Abwesenheitsdaten für mehrere Mitarbeiter (Bulk-Query)
    
    Args:
        locosoft_ids: Liste von employee_numbers
        year: Jahr
        
    Returns:
        {
            1001: {'urlaub': 27, 'zeitausgleich': 5, ...},
            1002: {'urlaub': 30, 'zeitausgleich': 0, ...},
            ...
        }
    """
    if not locosoft_ids:
        return {}
    
    try:
        conn = get_locosoft_connection()
        cur = conn.cursor()
        
        placeholders = ','.join(['%s'] * len(locosoft_ids))
        
        cur.execute(f"""
            SELECT 
                employee_number,
                reason,
                COALESCE(SUM(day_contingent), 0) as tage
            FROM absence_calendar
            WHERE employee_number IN ({placeholders})
              AND date >= %s AND date <= %s
            GROUP BY employee_number, reason
        """, (*locosoft_ids, f'{year}-01-01', f'{year}-12-31'))
        
        # Initialisiere Result-Dict
        result = {emp_id: {
            'urlaub': 0,
            'zeitausgleich': 0,
            'krank': 0,
            'sonstige': 0,
            'details': {}
        } for emp_id in locosoft_ids}
        
        for row in cur.fetchall():
            emp_num = row[0]
            reason = row[1]
            tage = float(row[2] or 0)
            
            if emp_num not in result:
                continue
            
            result[emp_num]['details'][reason] = tage
            if reason in ('Url', 'BUr'):
                result[emp_num]['urlaub'] += tage
            elif reason == 'ZA.':
                result[emp_num]['zeitausgleich'] += tage
            elif reason == 'Krn':
                result[emp_num]['krank'] += tage
            else:
                result[emp_num]['sonstige'] += tage
        
        # Runde Werte
        for emp_id in result:
            for key in ['urlaub', 'zeitausgleich', 'krank', 'sonstige']:
                result[emp_id][key] = round(result[emp_id][key], 2)
        
        conn.close()
        return result
        
    except Exception as e:
        print(f"Locosoft Bulk-Query Fehler: {e}")
        return {emp_id: {
            'urlaub': 0,
            'zeitausgleich': 0,
            'krank': 0,
            'sonstige': 0,
            'details': {},
            'error': str(e)
        } for emp_id in locosoft_ids}


def get_all_absences(year: int = 2025) -> Dict[int, Dict]:
    """
    Holt Abwesenheitsdaten für ALLE Mitarbeiter
    
    Returns:
        {employee_number: {'urlaub': ..., 'zeitausgleich': ..., ...}, ...}
    """
    try:
        conn = get_locosoft_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                a.employee_number,
                a.reason,
                COALESCE(SUM(a.day_contingent), 0) as tage
            FROM absence_calendar a
            JOIN employees e ON a.employee_number = e.employee_number
            WHERE a.date >= %s AND a.date <= %s
            GROUP BY a.employee_number, a.reason
        """, (f'{year}-01-01', f'{year}-12-31'))
        
        result = {}
        
        for row in cur.fetchall():
            emp_num = row[0]
            reason = row[1]
            tage = float(row[2] or 0)
            
            if emp_num not in result:
                result[emp_num] = {
                    'urlaub': 0,
                    'zeitausgleich': 0,
                    'krank': 0,
                    'sonstige': 0,
                    'details': {}
                }
            
            result[emp_num]['details'][reason] = tage
            if reason in ('Url', 'BUr'):
                result[emp_num]['urlaub'] += tage
            elif reason == 'ZA.':
                result[emp_num]['zeitausgleich'] += tage
            elif reason == 'Krn':
                result[emp_num]['krank'] += tage
            else:
                result[emp_num]['sonstige'] += tage
        
        # Runde Werte
        for emp_id in result:
            for key in ['urlaub', 'zeitausgleich', 'krank', 'sonstige']:
                result[emp_id][key] = round(result[emp_id][key], 2)
        
        conn.close()
        return result
        
    except Exception as e:
        print(f"Locosoft All-Query Fehler: {e}")
        return {}


def get_absence_days_for_employee(locosoft_id: int, year: int = 2025) -> List[Dict]:
    """
    Holt einzelne Abwesenheitstage für einen Mitarbeiter aus Locosoft.
    Wichtig für Kalenderanzeige mit halben Tagen (24./31.12).
    
    TAG 113: Neu für halbe Tage Darstellung
    
    Args:
        locosoft_id: employee_number aus Locosoft
        year: Jahr
        
    Returns:
        [
            {'date': '2025-12-24', 'day_contingent': 0.5, 'reason': 'Url', 'is_half_day': True},
            {'date': '2025-12-25', 'day_contingent': 1.0, 'reason': 'Url', 'is_half_day': False},
            ...
        ]
    """
    if not locosoft_id:
        return []
    
    try:
        conn = get_locosoft_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                date::text,
                day_contingent,
                reason,
                time_from,
                time_to
            FROM absence_calendar
            WHERE employee_number = %s
              AND date >= %s AND date <= %s
            ORDER BY date
        """, (locosoft_id, f'{year}-01-01', f'{year}-12-31'))
        
        days = []
        for row in cur.fetchall():
            day_contingent = float(row[1] or 1.0)
            days.append({
                'date': row[0],
                'day_contingent': day_contingent,
                'reason': row[2],
                'time_from': row[3].strftime('%H:%M') if row[3] else None,
                'time_to': row[4].strftime('%H:%M') if row[4] else None,
                'is_half_day': day_contingent < 1.0
            })
        
        conn.close()
        return days
        
    except Exception as e:
        print(f"Locosoft-Fehler für {locosoft_id} (Tage): {e}")
        return []


def get_absence_days_for_employees(locosoft_ids: List[int], year: int = 2025) -> Dict[int, List[Dict]]:
    """
    Holt einzelne Abwesenheitstage für mehrere Mitarbeiter (Bulk).
    
    TAG 113: Neu für Kalenderanzeige aller Mitarbeiter
    
    Args:
        locosoft_ids: Liste von employee_numbers
        year: Jahr
        
    Returns:
        {
            1001: [{'date': '2025-12-24', 'day_contingent': 0.5, ...}, ...],
            1002: [...],
            ...
        }
    """
    if not locosoft_ids:
        return {}
    
    try:
        conn = get_locosoft_connection()
        cur = conn.cursor()
        
        placeholders = ','.join(['%s'] * len(locosoft_ids))
        
        cur.execute(f"""
            SELECT 
                employee_number,
                date::text,
                day_contingent,
                reason,
                time_from,
                time_to
            FROM absence_calendar
            WHERE employee_number IN ({placeholders})
              AND date >= %s AND date <= %s
            ORDER BY employee_number, date
        """, (*locosoft_ids, f'{year}-01-01', f'{year}-12-31'))
        
        result = {emp_id: [] for emp_id in locosoft_ids}
        
        for row in cur.fetchall():
            emp_num = row[0]
            day_contingent = float(row[2] or 1.0)
            
            if emp_num in result:
                result[emp_num].append({
                    'date': row[1],
                    'day_contingent': day_contingent,
                    'reason': row[3],
                    'time_from': row[4].strftime('%H:%M') if row[4] else None,
                    'time_to': row[5].strftime('%H:%M') if row[5] else None,
                    'is_half_day': day_contingent < 1.0
                })
        
        conn.close()
        return result
        
    except Exception as e:
        print(f"Locosoft Bulk-Days Fehler: {e}")
        return {emp_id: [] for emp_id in locosoft_ids}


# Export
__all__ = [
    'get_absences_for_employee',
    'get_absences_for_employees',
    'get_all_absences',
    'get_absence_days_for_employee',
    'get_absence_days_for_employees'
]
