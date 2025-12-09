#!/usr/bin/env python3
"""
Zeigt Mitarbeiter aus bestimmten Abteilungen
"""

import sys
import psycopg2
from pathlib import Path

def load_env_file(env_path='config/.env'):
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

def show_department_members(dept_codes):
    env = load_env_file('config/.env')
    
    conn = psycopg2.connect(
        host=env['LOCOSOFT_HOST'],
        port=int(env['LOCOSOFT_PORT']),
        database=env['LOCOSOFT_DATABASE'],
        user=env['LOCOSOFT_USER'],
        password=env['LOCOSOFT_PASSWORD']
    )
    
    cursor = conn.cursor()
    
    for dept_code in dept_codes:
        print(f"\n{'='*80}")
        print(f"ABTEILUNG: {dept_code}")
        print(f"{'='*80}\n")
        
        cursor.execute("""
            SELECT DISTINCT
                eh.employee_number,
                eh.name,
                eh.employment_date,
                eh.mechanic_number,
                eh.salesman_number,
                egm.grp_code
            FROM employees_history eh
            JOIN employees_group_mapping egm ON eh.employee_number = egm.employee_number
            WHERE eh.is_latest_record = true
            AND eh.employee_number >= 1000
            AND (eh.leave_date IS NULL OR eh.leave_date > CURRENT_DATE)
            AND egm.grp_code = %s
            ORDER BY eh.employee_number
        """, (dept_code,))
        
        results = cursor.fetchall()
        
        if not results:
            print(f"  Keine Mitarbeiter in {dept_code} gefunden.\n")
            continue
        
        print(f"  Anzahl Mitarbeiter: {len(results)}\n")
        
        for emp_num, name, emp_date, mech, sales, grp in results:
            # Name splitten
            if ',' in name:
                parts = name.split(',', 1)
                nachname = parts[0].strip()
                vorname = parts[1].strip() if len(parts) > 1 else ""
            else:
                nachname = name
                vorname = ""
            
            print(f"  #{emp_num}: {vorname} {nachname}")
            print(f"    Eintritt:    {emp_date or 'N/A'}")
            print(f"    Mechaniker:  {mech or '-'}")
            print(f"    Verkäufer:   {sales or '-'}")
            print()
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    # Zeige SER und A-L
    show_department_members(['SER', 'A-L'])
