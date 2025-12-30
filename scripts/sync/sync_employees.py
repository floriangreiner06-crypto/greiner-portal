#!/usr/bin/env python3
"""
============================================================================
MITARBEITER-SYNC: Locosoft PostgreSQL -> Greiner Portal PostgreSQL
============================================================================
Erstellt: 06.11.2025
Aktualisiert: 2025-12-23 (TAG 136 - PostgreSQL Migration)
Zweck: Synchronisiert aktive Mitarbeiter aus Locosoft
Filter: employee_number >= 1000 AND (leave_date IS NULL OR > today)
============================================================================
"""

import sys
import os
import psycopg2
from pathlib import Path
from datetime import date
import hashlib

# Projekt-Pfad
sys.path.insert(0, '/opt/greiner-portal')

# =============================================================================
# KONFIGURATION
# =============================================================================

# Ziel-Datenbank (unsere PostgreSQL)
TARGET_DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'drive_portal',
    'user': 'drive_user',
    'password': 'DrivePortal2024'
}

# Versuche .env zu laden
try:
    from dotenv import load_dotenv
    load_dotenv('/opt/greiner-portal/config/.env')
    TARGET_DB_CONFIG = {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'drive_portal'),
        'user': os.getenv('DB_USER', 'drive_user'),
        'password': os.getenv('DB_PASSWORD', 'DrivePortal2024')
    }
except ImportError:
    pass


def log(message, level="INFO"):
    """Simple logging"""
    print(f"[{level:5}] {message}")

def load_env_file(env_path='/opt/greiner-portal/config/.env'):
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
        'GL': 'Geschaeftsfuehrung',
        'FL': 'Disposition',
        'FZ': 'Fahrzeuge',
        'A-W': 'Werkstatt',
        'A-L': 'Verwaltung',
        'G': 'Geschaeftsfuehrung',
        'HM': 'Verwaltung'
    }
    return mapping.get(grp_code, 'Sonstige')

def generate_email(first_name, last_name):
    """Generiert Email-Adresse"""
    # Umlaute ersetzen
    replacements = {
        'ae': 'ae', 'oe': 'oe', 'ue': 'ue',
        'Ae': 'Ae', 'Oe': 'Oe', 'Ue': 'Ue',
        'ss': 'ss'
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
    """Synchronisiert Mitarbeiter von Locosoft zu PostgreSQL"""

    log("=" * 80)
    log("MITARBEITER-SYNCHRONISATION (PostgreSQL)")
    log("=" * 80)
    log("")

    if dry_run:
        log("DRY-RUN MODUS - Keine Aenderungen an der Datenbank!", "WARN")
        log("")

    # Verbindungen
    env = load_env_file()

    # PostgreSQL (Locosoft - QUELLE)
    log("Verbinde zu Locosoft PostgreSQL...")
    loco_conn = psycopg2.connect(
        host=env['LOCOSOFT_HOST'],
        port=int(env['LOCOSOFT_PORT']),
        database=env['LOCOSOFT_DATABASE'],
        user=env['LOCOSOFT_USER'],
        password=env['LOCOSOFT_PASSWORD']
    )
    loco_cursor = loco_conn.cursor()
    log("Locosoft verbunden")

    # PostgreSQL (Greiner Portal - ZIEL)
    log("Verbinde zu Greiner Portal PostgreSQL...")
    target_conn = psycopg2.connect(**TARGET_DB_CONFIG)
    target_cursor = target_conn.cursor()
    log(f"PostgreSQL verbunden ({TARGET_DB_CONFIG['host']}:{TARGET_DB_CONFIG['port']}/{TARGET_DB_CONFIG['database']})")
    log("")

    # Mitarbeiter aus Locosoft laden
    log("Lade aktive Mitarbeiter aus Locosoft...")
    loco_cursor.execute("""
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

    locosoft_employees = loco_cursor.fetchall()
    log(f"{len(locosoft_employees)} aktive Mitarbeiter gefunden")
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
                log(f"  -> [DRY-RUN] Wuerde synchronisiert werden")
                stats['inserted'] += 1
                continue

            # Pruefen ob Mitarbeiter bereits existiert
            target_cursor.execute("""
                SELECT id FROM employees WHERE locosoft_id = %s
            """, (emp_num,))

            existing = target_cursor.fetchone()

            if existing:
                employee_id = existing[0]

                # TAG 127: Pruefe ob LDAP-Mapping existiert
                # Wenn ja: department_name NICHT ueberschreiben (LDAP ist Master)
                target_cursor.execute("""
                    SELECT 1 FROM ldap_employee_mapping WHERE employee_id = %s
                """, (employee_id,))
                has_ldap_mapping = target_cursor.fetchone() is not None

                if has_ldap_mapping:
                    # UPDATE OHNE department_name (LDAP ist Master fuer Abteilung)
                    target_cursor.execute("""
                        UPDATE employees SET
                            first_name = %s,
                            last_name = %s,
                            email = %s,
                            entry_date = %s,
                            exit_date = %s,
                            location = %s,
                            personal_nr = %s,
                            aktiv = true
                        WHERE locosoft_id = %s
                    """, (
                        first_name, last_name, email,
                        emp_date, leave_date,
                        location,
                        personnel_no if personnel_no else None,
                        emp_num
                    ))
                    log(f"  -> Aktualisiert (Dept via LDAP)")
                else:
                    # UPDATE MIT department_name (kein LDAP = Locosoft ist Master)
                    target_cursor.execute("""
                        UPDATE employees SET
                            first_name = %s,
                            last_name = %s,
                            email = %s,
                            entry_date = %s,
                            exit_date = %s,
                            location = %s,
                            department_name = %s,
                            personal_nr = %s,
                            aktiv = true
                        WHERE locosoft_id = %s
                    """, (
                        first_name, last_name, email,
                        emp_date, leave_date,
                        location, department,
                        personnel_no if personnel_no else None,
                        emp_num
                    ))
                    log(f"  -> Aktualisiert")
                stats['updated'] += 1
            else:
                # INSERT
                target_cursor.execute("""
                    INSERT INTO employees (
                        locosoft_id, first_name, last_name, email, password_hash,
                        entry_date, exit_date, location, department_name,
                        personal_nr, aktiv, vacation_entitlement, role
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true, 30, 'user')
                """, (
                    emp_num, first_name, last_name, email, password_hash,
                    emp_date, leave_date, location, department,
                    personnel_no if personnel_no else None
                ))
                log(f"  -> Neu angelegt")
                stats['inserted'] += 1

        except Exception as e:
            log(f"  -> Fehler: {e}", "ERROR")
            stats['errors'] += 1
            target_conn.rollback()

    if not dry_run:
        target_conn.commit()
        log("")
        log("Aenderungen gespeichert")

    log("")
    log("=" * 80)
    log("ZUSAMMENFASSUNG")
    log("=" * 80)
    log(f"  Gesamt:        {stats['total']}")
    log(f"  Neu angelegt:  {stats['inserted']}")
    log(f"  Aktualisiert:  {stats['updated']}")
    log(f"  Uebersprungen: {stats['skipped']}")
    log(f"  Fehler:        {stats['errors']}")
    log("")

    if dry_run:
        log("DRY-RUN war aktiv - keine echten Aenderungen!", "WARN")
        log("   Fuehre erneut aus mit: python3 sync_employees.py --real")
    else:
        log("SYNCHRONISATION ABGESCHLOSSEN!")

    log("")

    # Cleanup
    loco_cursor.close()
    loco_conn.close()
    target_cursor.close()
    target_conn.close()

    return stats['errors'] == 0

if __name__ == '__main__':
    # Pruefe Argument
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == '--real':
        dry_run = False

    try:
        success = sync_employees(dry_run=dry_run)
        sys.exit(0 if success else 1)
    except Exception as e:
        log(f"Kritischer Fehler: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
