#!/usr/bin/env python3
"""
============================================================================
LOCOSOFT EMPLOYEES_HISTORY ANALYSE
============================================================================
Erstellt: 06.11.2025
Zweck: Detaillierte Analyse der employees_history Tabelle
============================================================================
"""

import sys
import psycopg2
from pathlib import Path

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

def analyze_employees():
    """Analysiert employees_history Tabelle"""
    
    log("=" * 80)
    log("EMPLOYEES_HISTORY TABELLE - DETAILANALYSE")
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
    
    # 1. ALLE SPALTEN ANZEIGEN
    log("1️⃣  ALLE SPALTEN:")
    log("-" * 80)
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'employees_history'
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    for col_name, data_type, max_len, nullable in columns:
        max_len_str = f"({max_len})" if max_len else ""
        null_str = "NULL" if nullable == 'YES' else "NOT NULL"
        log(f"  • {col_name:30} {data_type}{max_len_str:15} {null_str}")
    
    log("")
    
    # 2. AKTUELLE MITARBEITER (is_latest_record = true)
    log("2️⃣  AKTUELLE MITARBEITER (is_latest_record = true):")
    log("-" * 80)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM employees_history 
        WHERE is_latest_record = true
    """)
    current_count = cursor.fetchone()[0]
    log(f"  Anzahl aktuelle Mitarbeiter: {current_count}")
    log("")
    
    # 3. BEISPIEL-DATENSÄTZE (erste 5 aktuelle Mitarbeiter)
    log("3️⃣  BEISPIEL-DATENSÄTZE (erste 5 aktuelle Mitarbeiter):")
    log("-" * 80)
    cursor.execute("""
        SELECT 
            employee_number,
            name,
            initials,
            validity_date,
            subsidiary,
            has_constant_salary,
            customer_number,
            employee_personnel_no
        FROM employees_history 
        WHERE is_latest_record = true
        ORDER BY employee_number
        LIMIT 5
    """)
    
    rows = cursor.fetchall()
    for row in rows:
        log(f"  Mitarbeiter #{row[0]}:")
        log(f"    Name:           {row[1]}")
        log(f"    Initialen:      {row[2]}")
        log(f"    Gültig ab:      {row[3]}")
        log(f"    Subsidiary:     {row[4]}")
        log(f"    Festgehalt:     {row[5]}")
        log(f"    Kundennr:       {row[6]}")
        log(f"    Personalnr:     {row[7]}")
        log("")
    
    # 4. ZUSÄTZLICHE INFOS CHECKEN
    log("4️⃣  ZUSÄTZLICHE TABELLEN PRÜFEN:")
    log("-" * 80)
    
    # employees_group_mapping
    cursor.execute("""
        SELECT 
            eg.employee_number,
            eg.grp_code,
            eh.name
        FROM employees_group_mapping eg
        JOIN employees_history eh ON eg.employee_number = eh.employee_number
        WHERE eh.is_latest_record = true
        LIMIT 5
    """)
    
    log("  employees_group_mapping (erste 5):")
    for emp_num, grp_code, name in cursor.fetchall():
        log(f"    • {name} (#{emp_num}): Gruppe '{grp_code}'")
    log("")
    
    # 5. MAPPING-VORSCHLAG
    log("=" * 80)
    log("5️⃣  MAPPING-VORSCHLAG: Locosoft → SQLite")
    log("=" * 80)
    log("")
    log("  Locosoft (employees_history)  →  SQLite (employees)")
    log("  " + "-" * 76)
    log("  employee_number               →  locosoft_id")
    log("  name                          →  first_name + last_name (splitten!)")
    log("  initials                      →  Nicht verwenden")
    log("  employee_personnel_no         →  personal_nr")
    log("  subsidiary                    →  location (?)") 
    log("  validity_date                 →  entry_date")
    log("  is_latest_record = true       →  aktiv = 1")
    log("")
    log("  employees_group_mapping:")
    log("  grp_code                      →  department_name (Mapping erstellen)")
    log("")
    
    # 6. WICHTIGE HINWEISE
    log("=" * 80)
    log("⚠️  WICHTIGE HINWEISE:")
    log("=" * 80)
    log("")
    log("  1. NAME SPLITTEN:")
    log("     Locosoft hat nur 'name' Feld")
    log("     → Muss in first_name + last_name gesplittet werden")
    log("     → Format vermutlich: 'Nachname, Vorname' oder 'Vorname Nachname'")
    log("")
    log("  2. ABTEILUNG:")
    log("     → Aus employees_group_mapping / grp_code ableiten")
    log("     → Eventuell Mapping-Tabelle erstellen")
    log("")
    log("  3. EMAIL:")
    log("     → Nicht in Locosoft vorhanden")
    log("     → Muss generiert werden (z.B. vorname.nachname@greiner.de)")
    log("")
    log("  4. PASSWORT:")
    log("     → Nicht in Locosoft")
    log("     → Initial-Passwort generieren")
    log("")
    
    log("=" * 80)
    log("✅ ANALYSE ABGESCHLOSSEN")
    log("=" * 80)
    log("")
    log("NÄCHSTER SCHRITT:")
    log("  → Mitarbeiter-Sync-Script erstellen")
    log("  → Mapping implementieren")
    log("  → Test-Import durchführen")
    log("")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    try:
        analyze_employees()
    except Exception as e:
        log(f"❌ Fehler: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
