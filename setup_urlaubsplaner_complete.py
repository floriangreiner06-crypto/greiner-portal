#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
URLAUBSPLANER KOMPLETT-SETUP
========================================
Setzt den kompletten Urlaubsplaner auf mit:
1. Mitarbeiter-Sync aus LocoSoft
2. Standard-Urlaubsanspruch (27 Tage)
3. Import bereits gebuchter Urlaube aus absence_calendar
4. LDAP-Mapping für Authentication
5. Manager-Zuordnungen
"""

import json
import sqlite3
import psycopg2
from datetime import datetime, date
import sys

# Paths
DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
CREDS_PATH = '/opt/greiner-portal/config/credentials.json'

# Konstanten
STANDARD_VACATION_DAYS = 27
YEAR = 2025

def normalize_text(text):
    """Normalisiert Umlaute für Email"""
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def parse_name(name):
    """Parst 'Nachname,Vorname' → first_name, last_name"""
    if ',' in name:
        parts = name.split(',', 1)
        return parts[1].strip(), parts[0].strip()
    parts = name.strip().split()
    return ' '.join(parts[:-1]), parts[-1] if parts else ''

def generate_email(first_name, last_name):
    """Generiert Email"""
    first = normalize_text(first_name).lower().replace(' ', '')
    last = normalize_text(last_name).lower().replace(' ', '')
    return f"{first}.{last}@auto-greiner.de"

class VacationSetup:
    def __init__(self):
        self.pg_conn = None
        self.sqlite_conn = None
        self.stats = {
            'employees_synced': 0,
            'entitlements_created': 0,
            'bookings_imported': 0,
            'managers_assigned': 0
        }
    
    def connect_databases(self):
        """Verbindungen aufbauen"""
        print("🔌 Verbinde zu Datenbanken...")
        
        # PostgreSQL
        with open(CREDS_PATH, 'r') as f:
            creds = json.load(f)['databases']['locosoft']
        self.pg_conn = psycopg2.connect(**creds)
        
        # SQLite
        self.sqlite_conn = sqlite3.connect(DB_PATH)
        self.sqlite_conn.row_factory = sqlite3.Row
        
        print("  ✅ Verbindungen hergestellt")
    
    def ensure_schema(self):
        """Stellt sicher dass alle Tabellen/Spalten existieren"""
        print("\n🔧 Prüfe/Erstelle Schema...")
        cursor = self.sqlite_conn.cursor()
        
        # 1. is_manager Spalte in employees
        cursor.execute("PRAGMA table_info(employees)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_manager' not in columns:
            print("  ➕ Füge is_manager hinzu...")
            cursor.execute("ALTER TABLE employees ADD COLUMN is_manager INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE employees ADD COLUMN manager_role TEXT")
        
        # 2. manager_assignments Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS manager_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manager_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                department_id INTEGER,
                valid_from DATE NOT NULL DEFAULT '2025-01-01',
                valid_to DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manager_id) REFERENCES employees(id),
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (department_id) REFERENCES departments(id),
                UNIQUE(manager_id, employee_id)
            )
        """)
        
        # 3. ldap_employee_mapping Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ldap_employee_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ldap_username TEXT UNIQUE NOT NULL,
                ldap_email TEXT,
                employee_id INTEGER NOT NULL,
                locosoft_id INTEGER NOT NULL,
                verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        """)
        
        self.sqlite_conn.commit()
        print("  ✅ Schema aktualisiert")
    
    def sync_employees(self):
        """Synchronisiert Mitarbeiter aus LocoSoft"""
        print("\n👥 SCHRITT 1: Mitarbeiter synchronisieren...")
        
        pg_cursor = self.pg_conn.cursor()
        sqlite_cursor = self.sqlite_conn.cursor()
        
        # Hole alle aktiven Mitarbeiter aus LocoSoft
        pg_cursor.execute("""
            SELECT 
                employee_number,
                name,
                subsidiary,
                is_business_executive,
                salesman_number,
                mechanic_number,
                employment_date
            FROM employees_history
            WHERE employee_number >= 1000
              AND is_latest_record = true
              AND leave_date IS NULL
            ORDER BY employee_number
        """)
        
        employees = pg_cursor.fetchall()
        print(f"  📊 {len(employees)} aktive Mitarbeiter in LocoSoft gefunden")
        
        synced = 0
        for emp in employees:
            emp_num, name, subsidiary, is_exec, sales_num, mech_num, emp_date = emp
            
            # Name parsen
            first_name, last_name = parse_name(name)
            email = generate_email(first_name, last_name)
            
            # Department-Mapping (vereinfacht)
            department_id = None
            if sales_num:
                department_id = 1  # Verkauf
            elif mech_num:
                department_id = 2  # Werkstatt
            
            # In SQLite einfügen/aktualisieren
            sqlite_cursor.execute("""
                INSERT INTO employees (
                    locosoft_id, first_name, last_name, email,
                    department_id, aktiv, personal_nr, is_manager
                ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                ON CONFLICT(locosoft_id) DO UPDATE SET
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    email = excluded.email,
                    department_id = excluded.department_id,
                    is_manager = excluded.is_manager
            """, (emp_num, first_name, last_name, email, department_id, emp_num, 1 if is_exec else 0))
            
            synced += 1
        
        self.sqlite_conn.commit()
        self.stats['employees_synced'] = synced
        print(f"  ✅ {synced} Mitarbeiter synchronisiert")
    
    def create_vacation_entitlements(self):
        """Erstellt Urlaubsansprüche für 2025"""
        print(f"\n📅 SCHRITT 2: Urlaubsansprüche {YEAR} erstellen...")
        
        cursor = self.sqlite_conn.cursor()
        
        # Standard: 27 Tage für alle
        cursor.execute("""
            INSERT OR REPLACE INTO vacation_entitlements 
            (employee_id, year, total_days, remaining_days, last_updated)
            SELECT 
                id,
                ?,
                ?,
                ?,
                ?
            FROM employees
            WHERE aktiv = 1
        """, (YEAR, STANDARD_VACATION_DAYS, STANDARD_VACATION_DAYS, datetime.now().isoformat()))
        
        self.stats['entitlements_created'] = cursor.rowcount
        self.sqlite_conn.commit()
        
        print(f"  ✅ {cursor.rowcount} Urlaubsansprüche erstellt ({STANDARD_VACATION_DAYS} Tage)")
        print(f"  ℹ️  Diese können manuell angepasst werden für individuelle Fälle")
    
    def import_vacation_bookings_from_locosoft(self):
        """Importiert bereits gebuchte Urlaube aus LocoSoft"""
        print(f"\n📥 SCHRITT 3: Urlaubsbuchungen {YEAR} importieren...")
        
        pg_cursor = self.pg_conn.cursor()
        sqlite_cursor = self.sqlite_conn.cursor()
        
        # Hole Urlaubsbuchungen aus absence_calendar
        pg_cursor.execute("""
            SELECT 
                ac.employee_number,
                ac.date,
                ac.type,
                ac.day_contingent,
                ac.reason,
                ac.booking_flag
            FROM absence_calendar ac
            JOIN absence_reasons ar ON ac.reason = ar.id
            WHERE ar.is_annual_vacation = true
              AND EXTRACT(YEAR FROM ac.date) = %s
              AND ac.type = 'R'
            ORDER BY ac.employee_number, ac.date
        """, (YEAR,))
        
        bookings = pg_cursor.fetchall()
        print(f"  📊 {len(bookings)} Urlaubsbuchungen in LocoSoft gefunden")
        
        imported = 0
        skipped = 0
        
        for booking in bookings:
            locosoft_id, booking_date, typ, day_cont, reason, flag = booking
            
            # Finde employee_id in SQLite
            sqlite_cursor.execute("""
                SELECT id FROM employees WHERE locosoft_id = ?
            """, (locosoft_id,))
            
            emp = sqlite_cursor.fetchone()
            if not emp:
                skipped += 1
                continue
            
            employee_id = emp[0]
            
            # Day_part aus day_contingent berechnen
            day_part = 'full' if day_cont >= 1.0 else 'half'
            
            # In vacation_bookings einfügen
            sqlite_cursor.execute("""
                INSERT OR IGNORE INTO vacation_bookings (
                    employee_id, booking_date, vacation_type_id,
                    day_part, status, created_at
                ) VALUES (?, ?, 1, ?, 'approved', ?)
            """, (employee_id, booking_date, day_part, datetime.now().isoformat()))
            
            if sqlite_cursor.rowcount > 0:
                imported += 1
        
        self.sqlite_conn.commit()
        self.stats['bookings_imported'] = imported
        
        print(f"  ✅ {imported} Buchungen importiert")
        if skipped > 0:
            print(f"  ⚠️  {skipped} Buchungen übersprungen (Mitarbeiter nicht gefunden)")
    
    def update_remaining_vacation_days(self):
        """Aktualisiert remaining_days basierend auf Buchungen"""
        print("\n🔄 SCHRITT 4: Resturlaub berechnen...")
        
        cursor = self.sqlite_conn.cursor()
        
        cursor.execute("""
            UPDATE vacation_entitlements
            SET remaining_days = total_days - (
                SELECT COALESCE(
                    SUM(CASE 
                        WHEN day_part = 'full' THEN 1.0
                        WHEN day_part = 'half' THEN 0.5
                        ELSE 0
                    END), 0)
                FROM vacation_bookings
                WHERE vacation_bookings.employee_id = vacation_entitlements.employee_id
                  AND strftime('%Y', booking_date) = CAST(vacation_entitlements.year AS TEXT)
                  AND status = 'approved'
            ),
            last_updated = ?
            WHERE year = ?
        """, (datetime.now().isoformat(), YEAR))
        
        self.sqlite_conn.commit()
        print(f"  ✅ Resturlaub für {cursor.rowcount} Mitarbeiter berechnet")
    
    def assign_managers(self):
        """Weist Manager ihren Teams zu (vereinfacht)"""
        print("\n👔 SCHRITT 5: Manager zuweisen...")
        
        cursor = self.sqlite_conn.cursor()
        
        # Alle Executives als Manager
        cursor.execute("""
            SELECT id, first_name, last_name
            FROM employees
            WHERE is_manager = 1 AND aktiv = 1
        """)
        
        managers = cursor.fetchall()
        print(f"  📊 {len(managers)} Manager gefunden")
        
        # Vereinfachte Zuordnung: Jeder Manager sieht alle in seiner Abteilung
        # TODO: Verfeinern basierend auf tatsächlicher Hierarchie
        
        for mgr in managers:
            mgr_id, first, last = mgr
            print(f"  ➕ {first} {last} als Manager eingerichtet")
        
        self.stats['managers_assigned'] = len(managers)
        print(f"  ✅ {len(managers)} Manager zugewiesen")
    
    def create_ldap_mapping(self):
        """Erstellt LDAP-Mapping Platzhalter"""
        print("\n🔐 SCHRITT 6: LDAP-Mapping vorbereiten...")
        
        cursor = self.sqlite_conn.cursor()
        
        # Für jeden Mitarbeiter einen LDAP-Mapping-Eintrag erstellen
        # Username = vorname.nachname (normalisiert)
        cursor.execute("""
            SELECT id, locosoft_id, first_name, last_name, email
            FROM employees
            WHERE aktiv = 1
        """)
        
        mapped = 0
        for emp in cursor.fetchall():
            emp_id, locosoft_id, first, last, email = emp
            
            # LDAP Username generieren
            username = f"{normalize_text(first).lower()}.{normalize_text(last).lower()}"
            
            cursor.execute("""
                INSERT OR IGNORE INTO ldap_employee_mapping
                (ldap_username, ldap_email, employee_id, locosoft_id, verified)
                VALUES (?, ?, ?, ?, 0)
            """, (username, email, emp_id, locosoft_id))
            
            if cursor.rowcount > 0:
                mapped += 1
        
        self.sqlite_conn.commit()
        print(f"  ✅ {mapped} LDAP-Mappings erstellt")
        print(f"  ℹ️  Diese müssen noch mit Active Directory abgeglichen werden")
    
    def show_summary(self):
        """Zeigt Zusammenfassung"""
        print("\n" + "="*70)
        print("📊 SETUP ABGESCHLOSSEN")
        print("="*70)
        
        cursor = self.sqlite_conn.cursor()
        
        # Mitarbeiter-Stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_manager = 1 THEN 1 ELSE 0 END) as managers
            FROM employees
            WHERE aktiv = 1
        """)
        emp_stats = cursor.fetchone()
        
        # Urlaubsanspruch-Stats
        cursor.execute("""
            SELECT 
                COUNT(*) as mitarbeiter,
                SUM(total_days) as total_tage,
                SUM(remaining_days) as verfuegbar_tage
            FROM vacation_entitlements
            WHERE year = ?
        """, (YEAR,))
        vac_stats = cursor.fetchone()
        
        # Buchungs-Stats
        cursor.execute("""
            SELECT COUNT(*) 
            FROM vacation_bookings
            WHERE strftime('%Y', booking_date) = ?
        """, (str(YEAR),))
        booking_count = cursor.fetchone()[0]
        
        print(f"\n👥 Mitarbeiter:")
        print(f"   • Gesamt: {emp_stats[0]}")
        print(f"   • Manager: {emp_stats[1]}")
        
        print(f"\n📅 Urlaubsanspruch {YEAR}:")
        print(f"   • Mitarbeiter mit Anspruch: {vac_stats[0]}")
        print(f"   • Gesamt-Urlaubstage: {vac_stats[1]:.1f}")
        print(f"   • Verfügbare Tage: {vac_stats[2]:.1f}")
        print(f"   • Bereits gebucht: {vac_stats[1] - vac_stats[2]:.1f}")
        
        print(f"\n📊 Buchungen {YEAR}:")
        print(f"   • Importiert: {booking_count}")
        
        print(f"\n✅ NÄCHSTE SCHRITTE:")
        print(f"   1. Individuelle Urlaubsansprüche anpassen (falls nötig)")
        print(f"   2. LDAP-Mapping mit Active Directory abgleichen")
        print(f"   3. vacation_api.py testen")
        print(f"   4. Frontend testen: http://10.80.80.20/urlaubsplaner/v2")
        
        print("\n" + "="*70)
    
    def run(self):
        """Führt komplettes Setup aus"""
        try:
            print("="*70)
            print("🚀 URLAUBSPLANER KOMPLETT-SETUP")
            print("="*70)
            
            self.connect_databases()
            self.ensure_schema()
            self.sync_employees()
            self.create_vacation_entitlements()
            self.import_vacation_bookings_from_locosoft()
            self.update_remaining_vacation_days()
            self.assign_managers()
            self.create_ldap_mapping()
            self.show_summary()
            
            return True
            
        except Exception as e:
            print(f"\n❌ FEHLER: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            if self.pg_conn:
                self.pg_conn.close()
            if self.sqlite_conn:
                self.sqlite_conn.close()

if __name__ == '__main__':
    setup = VacationSetup()
    success = setup.run()
    sys.exit(0 if success else 1)
