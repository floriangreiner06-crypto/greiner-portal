#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
URLAUBSPLANER KOMPLETT-SETUP - FINAL
========================================
Version: 2.0
Datum: 11.11.2025

Features:
- Sync 71 aktiver Mitarbeiter aus LocoSoft (>= 1000)
- 27 Tage Standard-Urlaubsanspruch
- Import aller 2025 Buchungen aus absence_calendar
- Manager-Erkennung via is_business_executive
- LDAP-Mapping Vorbereitung
"""

import json
import sqlite3
import psycopg2
from datetime import datetime
import sys

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
CREDS_PATH = '/opt/greiner-portal/config/credentials.json'

STANDARD_VACATION_DAYS = 27.0
YEAR = 2025

def normalize_text(text):
    """Normalisiert Umlaute für Email"""
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.lower().replace(' ', '')

def parse_name(name):
    """Parst 'Nachname,Vorname' aus LocoSoft"""
    if ',' in name:
        parts = name.split(',', 1)
        return parts[1].strip(), parts[0].strip()
    parts = name.strip().split()
    return ' '.join(parts[:-1]) if len(parts) > 1 else '', parts[-1] if parts else ''

def main():
    print("="*70)
    print("🚀 URLAUBSPLANER KOMPLETT-SETUP")
    print("="*70)
    print(f"Standard Urlaubstage: {STANDARD_VACATION_DAYS}")
    print(f"Jahr: {YEAR}")
    print(f"Filter: Nur Mitarbeiter >= 1000 (keine Admin-Accounts)")
    
    try:
        # VERBINDUNGEN
        print("\n🔌 Verbinde zu Datenbanken...")
        with open(CREDS_PATH, 'r') as f:
            creds = json.load(f)['databases']['locosoft']
        
        pg_conn = psycopg2.connect(**creds)
        pg_cursor = pg_conn.cursor()
        
        sqlite_conn = sqlite3.connect(DB_PATH)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        
        print("  ✅ Verbindungen hergestellt")
        
        # SCHRITT 1: MITARBEITER SYNC
        print("\n" + "="*70)
        print("👥 SCHRITT 1: MITARBEITER SYNCHRONISIEREN")
        print("="*70)
        
        pg_cursor.execute("""
            SELECT 
                employee_number,
                name,
                subsidiary,
                is_business_executive,
                salesman_number,
                mechanic_number
            FROM employees_history
            WHERE employee_number >= 1000
              AND is_latest_record = true
              AND leave_date IS NULL
            ORDER BY employee_number
        """)
        
        locosoft_employees = pg_cursor.fetchall()
        print(f"\n📊 {len(locosoft_employees)} aktive Mitarbeiter in LocoSoft gefunden")
        
        synced_new = 0
        synced_updated = 0
        
        for emp in locosoft_employees:
            emp_num, name, subsidiary, is_exec, sales_num, mech_num = emp
            
            # Name parsen
            first_name, last_name = parse_name(name)
            email = f"{normalize_text(first_name)}.{normalize_text(last_name)}@auto-greiner.de"
            
            # Department-Mapping (vereinfacht)
            dept_id = None
            if sales_num:
                dept_id = 1  # Verkauf
            elif mech_num:
                dept_id = 2  # Werkstatt
            
            # Prüfe ob bereits vorhanden
            sqlite_cursor.execute("SELECT id FROM employees WHERE locosoft_id = ?", (emp_num,))
            existing = sqlite_cursor.fetchone()
            
            if existing:
                # Update
                sqlite_cursor.execute("""
                    UPDATE employees 
                    SET first_name = ?, last_name = ?, email = ?,
                        department_id = ?, aktiv = 1, is_manager = ?,
                        personal_nr = ?
                    WHERE locosoft_id = ?
                """, (first_name, last_name, email, dept_id, 1 if is_exec else 0, 
                      str(emp_num), emp_num))
                synced_updated += 1
            else:
                # Insert
                try:
                    sqlite_cursor.execute("""
                        INSERT INTO employees (
                            locosoft_id, first_name, last_name, email,
                            department_id, aktiv, personal_nr, is_manager,
                            password_hash
                        ) VALUES (?, ?, ?, ?, ?, 1, ?, ?, 'LDAP_AUTH')
                    """, (emp_num, first_name, last_name, email, dept_id, 
                          str(emp_num), 1 if is_exec else 0))
                    synced_new += 1
                except sqlite3.IntegrityError as e:
                    print(f"  ⚠️  Duplikat: {name} ({emp_num}) - {e}")
        
        sqlite_conn.commit()
        print(f"\n✅ Mitarbeiter-Sync abgeschlossen:")
        print(f"   • Neu erstellt: {synced_new}")
        print(f"   • Aktualisiert: {synced_updated}")
        print(f"   • Gesamt: {synced_new + synced_updated}")
        
        # SCHRITT 2: URLAUBSANSPRÜCHE
        print("\n" + "="*70)
        print(f"📅 SCHRITT 2: URLAUBSANSPRÜCHE {YEAR}")
        print("="*70)
        
        sqlite_cursor.execute("""
            INSERT OR IGNORE INTO vacation_entitlements 
            (employee_id, year, total_days, carried_over, added_manually)
            SELECT 
                id,
                ?,
                ?,
                0.0,
                0.0
            FROM employees
            WHERE aktiv = 1
        """, (YEAR, STANDARD_VACATION_DAYS))
        
        entitlements_created = sqlite_cursor.rowcount
        sqlite_conn.commit()
        
        print(f"\n✅ {entitlements_created} Urlaubsansprüche erstellt")
        print(f"   Standard: {STANDARD_VACATION_DAYS} Tage pro Mitarbeiter")
        
        # SCHRITT 3: BUCHUNGEN IMPORTIEREN
        print("\n" + "="*70)
        print(f"📥 SCHRITT 3: URLAUBSBUCHUNGEN {YEAR} IMPORTIEREN")
        print("="*70)
        
        pg_cursor.execute("""
            SELECT 
                ac.employee_number,
                ac.date,
                ac.day_contingent,
                ac.reason
            FROM absence_calendar ac
            JOIN absence_reasons ar ON ac.reason = ar.id
            WHERE ar.is_annual_vacation = true
              AND EXTRACT(YEAR FROM ac.date) = %s
              AND ac.type = 'R'
              AND ac.employee_number >= 1000
            ORDER BY ac.employee_number, ac.date
        """, (YEAR,))
        
        locosoft_bookings = pg_cursor.fetchall()
        print(f"\n📊 {len(locosoft_bookings)} Urlaubsbuchungen in LocoSoft gefunden")
        
        imported = 0
        skipped_no_employee = 0
        skipped_duplicate = 0
        
        for locosoft_id, booking_date, day_cont, reason in locosoft_bookings:
            # Finde employee_id
            sqlite_cursor.execute("SELECT id FROM employees WHERE locosoft_id = ?", (locosoft_id,))
            emp = sqlite_cursor.fetchone()
            
            if not emp:
                skipped_no_employee += 1
                continue
            
            employee_id = emp[0]
            day_part = 'full' if day_cont >= 1.0 else 'half'
            
            # Prüfe ob bereits vorhanden
            sqlite_cursor.execute("""
                SELECT id FROM vacation_bookings
                WHERE employee_id = ? AND booking_date = ?
            """, (employee_id, booking_date))
            
            if sqlite_cursor.fetchone():
                skipped_duplicate += 1
                continue
            
            # Insert booking
            try:
                sqlite_cursor.execute("""
                    INSERT INTO vacation_bookings (
                        employee_id, booking_date, vacation_type_id,
                        day_part, status, created_at
                    ) VALUES (?, ?, 1, ?, 'approved', ?)
                """, (employee_id, booking_date, day_part, datetime.now().isoformat()))
                imported += 1
            except sqlite3.IntegrityError:
                skipped_duplicate += 1
        
        sqlite_conn.commit()
        
        print(f"\n✅ Buchungen-Import abgeschlossen:")
        print(f"   • Importiert: {imported}")
        if skipped_no_employee > 0:
            print(f"   • Übersprungen (MA nicht gefunden): {skipped_no_employee}")
        if skipped_duplicate > 0:
            print(f"   • Übersprungen (Duplikate): {skipped_duplicate}")
        
        # SCHRITT 4: MANAGER
        print("\n" + "="*70)
        print("👔 SCHRITT 4: MANAGER-ZUORDNUNG")
        print("="*70)
        
        sqlite_cursor.execute("""
            SELECT 
                id, first_name, last_name
            FROM employees
            WHERE is_manager = 1 AND aktiv = 1
            ORDER BY last_name
        """)
        
        managers = sqlite_cursor.fetchall()
        print(f"\n📊 {len(managers)} Manager identifiziert:")
        for mgr in managers:
            print(f"   • {mgr[1]} {mgr[2]}")
        
        # SCHRITT 5: STATISTIKEN
        print("\n" + "="*70)
        print("📊 SETUP ABGESCHLOSSEN - STATISTIKEN")
        print("="*70)
        
        # Mitarbeiter
        sqlite_cursor.execute("SELECT COUNT(*) FROM employees WHERE aktiv = 1")
        total_emp = sqlite_cursor.fetchone()[0]
        
        sqlite_cursor.execute("SELECT COUNT(*) FROM employees WHERE is_manager = 1 AND aktiv = 1")
        manager_count = sqlite_cursor.fetchone()[0]
        
        # Ansprüche
        sqlite_cursor.execute("""
            SELECT 
                COUNT(*) as mitarbeiter,
                SUM(total_days) as gesamt_tage,
                AVG(total_days) as durchschnitt
            FROM vacation_entitlements
            WHERE year = ?
        """, (YEAR,))
        vac_stats = sqlite_cursor.fetchone()
        
        # Buchungen
        sqlite_cursor.execute("""
            SELECT 
                COUNT(*) as buchungen,
                SUM(CASE WHEN day_part = 'full' THEN 1.0 ELSE 0.5 END) as tage
            FROM vacation_bookings
            WHERE strftime('%Y', booking_date) = ?
              AND status = 'approved'
        """, (str(YEAR),))
        booking_stats = sqlite_cursor.fetchone()
        
        print(f"\n👥 MITARBEITER:")
        print(f"   • Gesamt aktiv: {total_emp}")
        print(f"   • Manager: {manager_count}")
        
        print(f"\n📅 URLAUBSANSPRUCH {YEAR}:")
        print(f"   • Mitarbeiter mit Anspruch: {vac_stats[0]}")
        print(f"   • Gesamt-Urlaubstage: {vac_stats[1]:.1f}")
        print(f"   • Durchschnitt: {vac_stats[2]:.1f} Tage/MA")
        
        print(f"\n📊 BUCHUNGEN {YEAR}:")
        print(f"   • Anzahl Buchungen: {booking_stats[0]}")
        print(f"   • Gebuchte Tage: {booking_stats[1]:.1f}")
        print(f"   • Verfügbar (ca.): {vac_stats[1] - booking_stats[1]:.1f}")
        
        # Top 10 Resturlaub
        sqlite_cursor.execute("""
            SELECT 
                e.first_name || ' ' || e.last_name as name,
                ve.total_days,
                COALESCE(SUM(CASE 
                    WHEN vb.day_part = 'full' THEN 1.0
                    WHEN vb.day_part = 'half' THEN 0.5
                    ELSE 0
                END), 0) as genommen,
                ve.total_days - COALESCE(SUM(CASE 
                    WHEN vb.day_part = 'full' THEN 1.0
                    WHEN vb.day_part = 'half' THEN 0.5
                    ELSE 0
                END), 0) as verbleibend
            FROM vacation_entitlements ve
            JOIN employees e ON ve.employee_id = e.id
            LEFT JOIN vacation_bookings vb ON vb.employee_id = e.id 
                AND strftime('%Y', vb.booking_date) = CAST(ve.year AS TEXT)
                AND vb.status = 'approved'
            WHERE ve.year = ?
            GROUP BY ve.id, e.first_name, e.last_name, ve.total_days
            ORDER BY verbleibend DESC
            LIMIT 10
        """, (YEAR,))
        
        print(f"\n🏆 TOP 10 - MEISTER RESTURLAUB:")
        print(f"{'Name':<30} {'Anspruch':>10} {'Genommen':>10} {'Rest':>10}")
        print("-" * 70)
        for row in sqlite_cursor.fetchall():
            print(f"{row[0]:<30} {row[1]:>10.1f} {row[2]:>10.1f} {row[3]:>10.1f}")
        
        # NÄCHSTE SCHRITTE
        print("\n" + "="*70)
        print("✅ NÄCHSTE SCHRITTE")
        print("="*70)
        print("\n1. 🔧 Individuelle Ansprüche anpassen:")
        print("   UPDATE vacation_entitlements")
        print("   SET total_days = 32")
        print("   WHERE employee_id = (SELECT id FROM employees WHERE locosoft_id = 4003);")
        
        print("\n2. 🧪 API testen:")
        print("   curl http://localhost:5000/api/vacation/balance?employee_id=1")
        
        print("\n3. 🔐 LDAP-Mapping einrichten:")
        print("   Siehe: ldap_employee_mapping Tabelle")
        
        print("\n4. 🎨 Frontend testen:")
        print("   http://10.80.80.20/urlaubsplaner/v2")
        
        print("\n5. 🔄 Flask neu starten:")
        print("   sudo systemctl restart greiner-portal")
        
        print("\n" + "="*70)
        print("🎉 SETUP ERFOLGREICH ABGESCHLOSSEN!")
        print("="*70)
        
        pg_conn.close()
        sqlite_conn.close()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
