#!/usr/bin/env python3
"""
============================================================================
MITARBEITER-SYNC: Locosoft PostgreSQL → SQLite
============================================================================
Erstellt: 06.11.2025
Zweck: Synchronisiert aktive Mitarbeiter aus Locosoft
Filter: employee_number >= 1000 AND (leave_date IS NULL OR > today)
============================================================================
"""

import sys
import os
import psycopg2
import sqlite3
from pathlib import Path
from datetime import date
import hashlib

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
        last_name = full_name.strip()
        first_name = ""
    
    return first_name or "N/A", last_name or "N/A"

def map_subsidiary_to_location(subsidiary):
    """Mappt Subsidiary-Code zu Standort"""
    if subsidiary in [0, 1]:
        return "Deggendorf"
    elif subsidiary == 3:
        return "Landau a.d. Isar"
    else:
        return "Deggendorf"  # Default

def map_grp_code_to_department(grp_code):
    """Mappt Locosoft Gruppenprofil zu Abteilungsname"""
    mapping = {
        'MON': 'Werkstatt',
        'VKB': 'Verkauf',
        'SER': 'Service & Empfang',
        'SB': 'Service',
        'CC': 'Call-Center',
        'LAG': 'Lager & Teile',
        'DIS': 'Disposition',
        'FA': 'Fahrzeuge',
        'VER': 'Verwaltung',
        'MAR': 'Marketing',
        'GL': 'Geschäftsführung',
        'FL': 'Disposition',
        'FZ': 'Fahrzeuge',
        'A-W': 'Werkstatt',
        'A-L': 'Verwaltung',
        'G': 'Geschäftsführung',
        'HM': 'Verwaltung'
    }
    return mapping.get(grp_code, 'Sonstige')

def generate_email(first_name, last_name):
    """Generiert Email-Adresse"""
    # Umlaute ersetzen
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue',
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue',
        'ß': 'ss'
    }
    
    first = first_name.lower()
    last = last_name.lower()
    
    for old, new in replacements.items():
        first = first.replace(old, new)
        last = last.replace(old, new)
    
    # Nur Buchstaben und Zahlen
    first = ''.join(c for c in first if c.isalnum())
    last = ''.join(c for c in last if c.isalnum())
    
    if not first or not last:
        return "mitarbeiter@auto-greiner.de"
    
    return f"{first}.{last}@auto-greiner.de"

def generate_initial_password():
    """Generiert Initial-Passwort"""
    return "Greiner2025!"

def hash_password(password):
    """Erstellt Passwort-Hash"""
    return hashlib.sha256(password.encode()).hexdigest()

def sync_employees(dry_run=True):
    """Synchronisiert Mitarbeiter von Locosoft zu SQLite"""
    
    log("=" * 80)
    log("MITARBEITER-SYNCHRONISATION")
    log("=" * 80)
    log("")
    
    if dry_run:
        log("⚠️  DRY-RUN MODUS - Keine Änderungen an der Datenbank!", "WARN")
        log("")
    
    # Verbindungen
    env = load_env_file('config/.env')
    
    # PostgreSQL (Locosoft)
    log("Verbinde zu Locosoft PostgreSQL...")
    pg_conn = psycopg2.connect(
        host=env['LOCOSOFT_HOST'],
        port=int(env['LOCOSOFT_PORT']),
        database=env['LOCOSOFT_DATABASE'],
        user=env['LOCOSOFT_USER'],
        password=env['LOCOSOFT_PASSWORD']
    )
    pg_cursor = pg_conn.cursor()
    log("✅ Locosoft verbunden")
    
    # SQLite (greiner_controlling.db)
    log("Verbinde zu SQLite...")
    sqlite_conn = sqlite3.connect('data/greiner_controlling.db')
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    log("✅ SQLite verbunden")
    log("")
    
    # Mitarbeiter aus Locosoft laden
    log("Lade aktive Mitarbeiter aus Locosoft...")
    pg_cursor.execute("""
        SELECT DISTINCT ON (eh.employee_number)
            eh.employee_number,
            eh.name,
            eh.employment_date,
            eh.leave_date,
            eh.subsidiary,
            eh.employee_personnel_no,
            eh.mechanic_number,
            eh.salesman_number,
            egm.grp_code
        FROM employees_history eh
        LEFT JOIN employees_group_mapping egm 
            ON eh.employee_number = egm.employee_number
        WHERE eh.is_latest_record = true
        AND eh.employee_number >= 1000
        AND (eh.leave_date IS NULL OR eh.leave_date > CURRENT_DATE)
        ORDER BY eh.employee_number, egm.validity_date DESC
    """)
    
    locosoft_employees = pg_cursor.fetchall()
    log(f"✅ {len(locosoft_employees)} aktive Mitarbeiter gefunden")
    log("")
    
    # Statistik
    stats = {
        'total': len(locosoft_employees),
        'inserted': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }
    
    # Mitarbeiter synchronisieren
    log("Starte Synchronisation...")
    log("-" * 80)
    
    for row in locosoft_employees:
        emp_num, name, emp_date, leave_date, subsidiary, personnel_no, mech_num, sales_num, grp_code = row
        
        try:
            # Daten aufbereiten
            first_name, last_name = split_name(name)
            location = map_subsidiary_to_location(subsidiary)
            department = map_grp_code_to_department(grp_code) if grp_code else 'Sonstige'
            email = generate_email(first_name, last_name)
            password_hash = hash_password(generate_initial_password())
            
            log(f"#{emp_num}: {first_name} {last_name} ({department}, {location})")
            
            if dry_run:
                log(f"  → [DRY-RUN] Würde synchronisiert werden")
                stats['inserted'] += 1
                continue
            
            # Prüfen ob Mitarbeiter bereits existiert
            sqlite_cursor.execute("""
                SELECT id FROM employees WHERE locosoft_id = ?
            """, (emp_num,))
            
            existing = sqlite_cursor.fetchone()
            
            if existing:
                # UPDATE
                sqlite_cursor.execute("""
                    UPDATE employees SET
                        first_name = ?,
                        last_name = ?,
                        email = ?,
                        entry_date = ?,
                        exit_date = ?,
                        location = ?,
                        department_name = ?,
                        personal_nr = ?,
                        aktiv = 1
                    WHERE locosoft_id = ?
                """, (
                    first_name, last_name, email,
                    emp_date, leave_date,
                    location, department,
                    personnel_no if personnel_no else None,
                    emp_num
                ))
                log(f"  → Aktualisiert")
                stats['updated'] += 1
            else:
                # INSERT
                sqlite_cursor.execute("""
                    INSERT INTO employees (
                        locosoft_id, first_name, last_name, email, password_hash,
                        entry_date, exit_date, location, department_name,
                        personal_nr, aktiv, vacation_entitlement, role
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 30, 'user')
                """, (
                    emp_num, first_name, last_name, email, password_hash,
                    emp_date, leave_date, location, department,
                    personnel_no if personnel_no else None
                ))
                log(f"  → Neu angelegt")
                stats['inserted'] += 1
        
        except Exception as e:
            log(f"  → ❌ Fehler: {e}", "ERROR")
            stats['errors'] += 1
    
    if not dry_run:
        sqlite_conn.commit()
        log("")
        log("✅ Änderungen gespeichert")
    
    log("")
    log("=" * 80)
    log("ZUSAMMENFASSUNG")
    log("=" * 80)
    log(f"  Gesamt:        {stats['total']}")
    log(f"  Neu angelegt:  {stats['inserted']}")
    log(f"  Aktualisiert:  {stats['updated']}")
    log(f"  Übersprungen:  {stats['skipped']}")
    log(f"  Fehler:        {stats['errors']}")
    log("")
    
    if dry_run:
        log("⚠️  DRY-RUN war aktiv - keine echten Änderungen!", "WARN")
        log("   Führe erneut aus mit: python3 sync_employees.py --real")
    else:
        log("✅ SYNCHRONISATION ABGESCHLOSSEN!", "SUCCESS")
    
    log("")
    
    # Cleanup
    pg_cursor.close()
    pg_conn.close()
    sqlite_cursor.close()
    sqlite_conn.close()
    
    return stats['errors'] == 0

if __name__ == '__main__':
    # Prüfe Argument
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == '--real':
        dry_run = False
    
    try:
        success = sync_employees(dry_run=dry_run)
        sys.exit(0 if success else 1)
    except Exception as e:
        log(f"❌ Kritischer Fehler: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
