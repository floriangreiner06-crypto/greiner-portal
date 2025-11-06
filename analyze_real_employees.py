#!/usr/bin/env python3
"""
============================================================================
LOCOSOFT MITARBEITER-ANALYSE (KORRIGIERT)
============================================================================
Erstellt: 06.11.2025
Filter: Nur echte Mitarbeiter (>= 1000) ohne leave_date
============================================================================
"""

import sys
import psycopg2
from pathlib import Path
from datetime import date

def log(message, level="INFO"):
    """Simple logging"""
    print(f"[{level:5}] {message}")

def load_env_file(env_path='config/.env'):
    """Liest .env Datei"""
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

def split_name(full_name):
    """Splittet 'Nachname,Vorname' in Vorname und Nachname"""
    if not full_name:
        return "Unknown", "Unknown"
    
    if ',' in full_name:
        parts = full_name.split(',', 1)
        last_name = parts[0].strip()
        first_name = parts[1].strip() if len(parts) > 1 else ""
    else:
        # Falls kein Komma: Alles als Nachname
        last_name = full_name.strip()
        first_name = ""
    
    return first_name or "N/A", last_name or "N/A"

def analyze_real_employees():
    """Analysiert nur echte, aktive Mitarbeiter"""
    
    log("=" * 80)
    log("MITARBEITER-ANALYSE (NUR ECHTE MITARBEITER)")
    log("=" * 80)
    log("")
    
    # .env laden
    env = load_env_file('config/.env')
    
    # Verbinden
    conn = psycopg2.connect(
        host=env['LOCOSOFT_HOST'],
        port=int(env['LOCOSOFT_PORT']),
        database=env['LOCOSOFT_DATABASE'],
        user=env['LOCOSOFT_USER'],
        password=env['LOCOSOFT_PASSWORD']
    )
    
    cursor = conn.cursor()
    
    # 1. STATISTIK
    log("1️⃣  STATISTIK:")
    log("-" * 80)
    
    # Gesamt
    cursor.execute("SELECT COUNT(*) FROM employees_history WHERE is_latest_record = true")
    total = cursor.fetchone()[0]
    log(f"  Gesamt (is_latest_record = true): {total}")
    
    # System-IDs (< 1000)
    cursor.execute("SELECT COUNT(*) FROM employees_history WHERE is_latest_record = true AND employee_number < 1000")
    system_ids = cursor.fetchone()[0]
    log(f"  System-IDs (< 1000):              {system_ids}")
    
    # Echte Mitarbeiter
    cursor.execute("SELECT COUNT(*) FROM employees_history WHERE is_latest_record = true AND employee_number >= 1000")
    real_employees = cursor.fetchone()[0]
    log(f"  Echte Mitarbeiter (>= 1000):      {real_employees}")
    
    # Mit leave_date
    cursor.execute("""
        SELECT COUNT(*) FROM employees_history 
        WHERE is_latest_record = true 
        AND employee_number >= 1000
        AND leave_date IS NOT NULL 
        AND leave_date <= CURRENT_DATE
    """)
    with_leave = cursor.fetchone()[0]
    log(f"  Ausgeschieden (leave_date):       {with_leave}")
    
    # AKTIV
    cursor.execute("""
        SELECT COUNT(*) FROM employees_history 
        WHERE is_latest_record = true 
        AND employee_number >= 1000
        AND (leave_date IS NULL OR leave_date > CURRENT_DATE)
    """)
    active = cursor.fetchone()[0]
    log(f"  ✅ AKTIVE MITARBEITER:             {active}")
    log("")
    
    # 2. AKTIVE MITARBEITER (erste 10)
    log("2️⃣  AKTIVE MITARBEITER (erste 10):")
    log("-" * 80)
    cursor.execute("""
        SELECT 
            employee_number,
            name,
            employment_date,
            leave_date,
            mechanic_number,
            salesman_number,
            subsidiary
        FROM employees_history 
        WHERE is_latest_record = true 
        AND employee_number >= 1000
        AND (leave_date IS NULL OR leave_date > CURRENT_DATE)
        ORDER BY employee_number
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        emp_num, name, emp_date, leave, mech, sales, sub = row
        first_name, last_name = split_name(name)
        
        log(f"  #{emp_num}: {first_name} {last_name}")
        log(f"    Eintritt:    {emp_date or 'N/A'}")
        log(f"    Austritt:    {leave or 'Aktiv'}")
        log(f"    Mechaniker:  {mech or '-'}")
        log(f"    Verkäufer:   {sales or '-'}")
        log(f"    Subsidiary:  {sub or '0'}")
        log("")
    
    # 3. ABTEILUNGEN
    log("3️⃣  ABTEILUNGSZUORDNUNG (employees_group_mapping):")
    log("-" * 80)
    cursor.execute("""
        SELECT DISTINCT grp_code, COUNT(*) as anzahl
        FROM employees_group_mapping egm
        JOIN employees_history eh ON egm.employee_number = eh.employee_number
        WHERE eh.is_latest_record = true
        AND eh.employee_number >= 1000
        AND (eh.leave_date IS NULL OR eh.leave_date > CURRENT_DATE)
        GROUP BY grp_code
        ORDER BY anzahl DESC
    """)
    
    groups = cursor.fetchall()
    log(f"  Anzahl verschiedene Gruppen: {len(groups)}")
    log("")
    for grp_code, count in groups:
        log(f"    • {grp_code:10} {count:3} Mitarbeiter")
    log("")
    
    # 4. GRUPPEN-MAPPING VORSCHLAG
    log("4️⃣  GRUPPEN-MAPPING VORSCHLAG:")
    log("-" * 80)
    
    # Häufigste Codes
    common_groups = {
        'DIS': 'Disposition',
        'FA': 'Fahrzeuge',
        'FL': 'Flottenmanagement',
        'GL': 'Geschäftsleitung',
        'SER': 'Service',
        'VER': 'Verwaltung',
        'VK': 'Verkauf',
        'WS': 'Werkstatt',
        'LAG': 'Lager & Teile',
        'CC': 'Call-Center',
        'MAR': 'Marketing'
    }
    
    log("  Vorgeschlagene Mappings:")
    for code, count in groups[:15]:
        mapped = common_groups.get(code, f"Unbekannt ({code})")
        log(f"    '{code}' → '{mapped}'")
    log("")
    
    # 5. NAME-SPLITTING BEISPIELE
    log("5️⃣  NAME-SPLITTING BEISPIELE:")
    log("-" * 80)
    cursor.execute("""
        SELECT name
        FROM employees_history 
        WHERE is_latest_record = true 
        AND employee_number >= 1000
        AND (leave_date IS NULL OR leave_date > CURRENT_DATE)
        AND name IS NOT NULL
        ORDER BY employee_number
        LIMIT 10
    """)
    
    for (name,) in cursor.fetchall():
        first, last = split_name(name)
        log(f"  '{name}' → Vorname: '{first}', Nachname: '{last}'")
    log("")
    
    # 6. ZUSAMMENFASSUNG
    log("=" * 80)
    log("✅ ZUSAMMENFASSUNG")
    log("=" * 80)
    log("")
    log(f"  Aktive Mitarbeiter zu synchronisieren: {active}")
    log(f"  Ausgeschiedene (ignoriert):            {with_leave}")
    log(f"  System-IDs (ignoriert):                {system_ids}")
    log("")
    log("NÄCHSTER SCHRITT:")
    log("  → Mitarbeiter-Sync-Script erstellen")
    log("  → Filter: employee_number >= 1000 AND (leave_date IS NULL OR > today)")
    log("  → Name splitten: 'Nachname,Vorname'")
    log("  → Abteilung aus grp_code mappen")
    log("")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    try:
        analyze_real_employees()
    except Exception as e:
        log(f"❌ Fehler: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
