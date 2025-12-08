#!/usr/bin/env python3
"""
LOCOSOFT EMPLOYEE SYNC - TAG 103
================================
Synchronisiert Mitarbeiter zwischen Portal (SQLite) und Locosoft (PostgreSQL)

Aufgaben:
1. Matching Portal-Mitarbeiter mit Locosoft employee_number
2. Update ldap_employee_mapping Tabelle
3. Logging aller Änderungen

Ausführung:
- Manuell: python3 sync_locosoft_employees.py
- Cron: 0 6 * * * /opt/greiner-portal/venv/bin/python3 /opt/greiner-portal/scripts/sync_locosoft_employees.py

Author: Claude AI
Created: 2025-12-08
"""

import sqlite3
import psycopg2
import logging
from datetime import datetime
from pathlib import Path
import re

# Konfiguration
SQLITE_DB = '/opt/greiner-portal/data/greiner_controlling.db'
LOG_FILE = '/opt/greiner-portal/logs/locosoft_sync.log'

LOCOSOFT_CONFIG = {
    'host': '10.80.80.8',
    'database': 'loco_auswertung_db',
    'user': 'loco_auswertung_benutzer',
    'password': 'loco'
}

# Logging Setup
Path('/opt/greiner-portal/logs').mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def normalize_name(name):
    """Normalisiert Namen für Vergleich"""
    if not name:
        return ""
    # Kleinbuchstaben, Umlaute ersetzen, nur Buchstaben behalten
    name = name.lower().strip()
    name = name.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    name = re.sub(r'[^a-z]', '', name)
    return name


def get_locosoft_employees():
    """Lädt alle Mitarbeiter aus Locosoft"""
    try:
        conn = psycopg2.connect(**LOCOSOFT_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT employee_number, name 
            FROM employees 
            WHERE employee_number IS NOT NULL 
              AND name IS NOT NULL
              AND name != ''
            ORDER BY name
        """)
        
        employees = {}
        for emp_num, name in cur.fetchall():
            # Name Format: "Nachname,Vorname" oder "Nachname, Vorname"
            parts = name.replace(' ', '').split(',')
            if len(parts) >= 2:
                last_name = parts[0].strip()
                first_name = parts[1].strip()
            else:
                last_name = name.strip()
                first_name = ""
            
            # Normalisierte Keys für Matching
            key_full = normalize_name(first_name + last_name)
            key_last = normalize_name(last_name)
            
            employees[emp_num] = {
                'employee_number': emp_num,
                'name': name,
                'first_name': first_name,
                'last_name': last_name,
                'key_full': key_full,
                'key_last': key_last
            }
        
        conn.close()
        logger.info(f"✅ {len(employees)} Mitarbeiter aus Locosoft geladen")
        return employees
        
    except Exception as e:
        logger.error(f"❌ Locosoft-Verbindung fehlgeschlagen: {e}")
        return {}


def get_portal_employees():
    """Lädt alle Mitarbeiter aus Portal-DB"""
    try:
        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Prüfe welche Spalten existieren
        cur.execute("PRAGMA table_info(employees)")
        columns = [col[1] for col in cur.fetchall()]
        
        # Baue Query dynamisch basierend auf vorhandenen Spalten
        select_cols = ['e.id', 'e.first_name', 'e.last_name']
        if 'ldap_username' in columns:
            select_cols.append('e.ldap_username')
        if 'username' in columns:
            select_cols.append('e.username')
        if 'email' in columns:
            select_cols.append('e.email')
            
        # is_active prüfen
        has_is_active = 'is_active' in columns
        
        query = f"""
            SELECT 
                {', '.join(select_cols)},
                lem.locosoft_id
            FROM employees e
            LEFT JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
            {'WHERE e.is_active = 1 OR e.is_active IS NULL' if has_is_active else ''}
        """
        
        cur.execute(query)
        
        employees = []
        for row in cur.fetchall():
            emp = dict(row)
            first = emp.get('first_name') or ''
            last = emp.get('last_name') or ''
            emp['key_full'] = normalize_name(first + last)
            emp['key_last'] = normalize_name(last)
            employees.append(emp)
        
        conn.close()
        logger.info(f"✅ {len(employees)} Mitarbeiter aus Portal geladen")
        return employees
        
    except Exception as e:
        logger.error(f"❌ SQLite-Verbindung fehlgeschlagen: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def find_locosoft_match(portal_emp, locosoft_employees):
    """Findet passenden Locosoft-Mitarbeiter"""
    portal_key = portal_emp['key_full']
    portal_key_last = portal_emp['key_last']
    
    # 1. Exakter Match (Vor- und Nachname)
    for emp_num, loco_emp in locosoft_employees.items():
        if portal_key and portal_key == loco_emp['key_full']:
            return emp_num, 'exact', loco_emp['name']
    
    # 2. Nachname-Match (falls eindeutig)
    last_name_matches = []
    for emp_num, loco_emp in locosoft_employees.items():
        if portal_key_last and portal_key_last == loco_emp['key_last']:
            last_name_matches.append((emp_num, loco_emp['name']))
    
    if len(last_name_matches) == 1:
        return last_name_matches[0][0], 'lastname', last_name_matches[0][1]
    
    return None, None, None


def sync_employees():
    """Hauptfunktion: Synchronisiert Mitarbeiter"""
    logger.info("=" * 60)
    logger.info("🔄 LOCOSOFT EMPLOYEE SYNC gestartet")
    logger.info("=" * 60)
    
    # Daten laden
    locosoft_employees = get_locosoft_employees()
    if not locosoft_employees:
        logger.error("Keine Locosoft-Mitarbeiter geladen - Abbruch")
        return
    
    portal_employees = get_portal_employees()
    if not portal_employees:
        logger.error("Keine Portal-Mitarbeiter geladen - Abbruch")
        return
    
    # Statistiken
    stats = {
        'total': len(portal_employees),
        'already_mapped': 0,
        'newly_mapped': 0,
        'updated': 0,
        'not_found': 0,
        'errors': 0
    }
    
    # SQLite Verbindung für Updates
    conn = sqlite3.connect(SQLITE_DB)
    cur = conn.cursor()
    
    # Sicherstellen dass Tabelle existiert
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ldap_employee_mapping (
            employee_id INTEGER PRIMARY KEY,
            locosoft_id TEXT,
            match_type TEXT,
            locosoft_name TEXT,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Jeden Portal-Mitarbeiter prüfen
    for emp in portal_employees:
        emp_name = f"{emp['first_name']} {emp['last_name']}"
        
        try:
            # Bereits gemappt?
            if emp['locosoft_id']:
                # Prüfe ob Mapping noch gültig
                if emp['locosoft_id'] in [str(k) for k in locosoft_employees.keys()]:
                    stats['already_mapped'] += 1
                    continue
                else:
                    logger.warning(f"⚠️  {emp_name}: Locosoft-ID {emp['locosoft_id']} existiert nicht mehr")
            
            # Neuen Match suchen
            loco_id, match_type, loco_name = find_locosoft_match(emp, locosoft_employees)
            
            if loco_id:
                # Mapping einfügen/updaten
                cur.execute("""
                    INSERT OR REPLACE INTO ldap_employee_mapping 
                    (employee_id, locosoft_id, match_type, locosoft_name, synced_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (emp['id'], str(loco_id), match_type, loco_name, datetime.now()))
                
                if emp['locosoft_id']:
                    stats['updated'] += 1
                    logger.info(f"🔄 {emp_name}: Update {emp['locosoft_id']} -> {loco_id} ({loco_name})")
                else:
                    stats['newly_mapped'] += 1
                    logger.info(f"✅ {emp_name}: Neu gemappt -> {loco_id} ({loco_name}) [{match_type}]")
            else:
                stats['not_found'] += 1
                logger.warning(f"❓ {emp_name}: Kein Locosoft-Match gefunden")
                
        except Exception as e:
            stats['errors'] += 1
            logger.error(f"❌ {emp_name}: Fehler - {e}")
    
    conn.commit()
    conn.close()
    
    # Zusammenfassung
    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 ZUSAMMENFASSUNG")
    logger.info("=" * 60)
    logger.info(f"   Gesamt Portal-Mitarbeiter:  {stats['total']}")
    logger.info(f"   Bereits gemappt:            {stats['already_mapped']}")
    logger.info(f"   Neu gemappt:                {stats['newly_mapped']}")
    logger.info(f"   Aktualisiert:               {stats['updated']}")
    logger.info(f"   Nicht gefunden:             {stats['not_found']}")
    logger.info(f"   Fehler:                     {stats['errors']}")
    logger.info("=" * 60)
    
    return stats


def show_unmapped():
    """Zeigt alle nicht gemappten Mitarbeiter"""
    conn = sqlite3.connect(SQLITE_DB)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT e.id, e.first_name, e.last_name, e.ldap_username
        FROM employees e
        LEFT JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
        WHERE lem.locosoft_id IS NULL
          AND (e.is_active = 1 OR e.is_active IS NULL)
        ORDER BY e.last_name
    """)
    
    unmapped = cur.fetchall()
    conn.close()
    
    print(f"\n❓ {len(unmapped)} Mitarbeiter ohne Locosoft-Mapping:\n")
    for emp in unmapped:
        print(f"   {emp[1]} {emp[2]} ({emp[3]})")
    
    return unmapped


def manual_map(portal_id, locosoft_id):
    """Manuelles Mapping hinzufügen"""
    conn = sqlite3.connect(SQLITE_DB)
    cur = conn.cursor()
    
    cur.execute("""
        INSERT OR REPLACE INTO ldap_employee_mapping 
        (employee_id, locosoft_id, match_type, synced_at)
        VALUES (?, ?, 'manual', ?)
    """, (portal_id, str(locosoft_id), datetime.now()))
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Manuelles Mapping: Portal-ID {portal_id} -> Locosoft-ID {locosoft_id}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--unmapped':
            show_unmapped()
        elif sys.argv[1] == '--map' and len(sys.argv) == 4:
            manual_map(int(sys.argv[2]), sys.argv[3])
        else:
            print("Verwendung:")
            print("  python3 sync_locosoft_employees.py          # Vollständiger Sync")
            print("  python3 sync_locosoft_employees.py --unmapped   # Zeige nicht gemappte")
            print("  python3 sync_locosoft_employees.py --map <portal_id> <locosoft_id>  # Manuell mappen")
    else:
        sync_employees()
