#!/usr/bin/env python3
"""
ANALYSE: employees_worktimes - Warum keine Daten?
==================================================
TAG 94 - Prüft die Arbeitszeiten-Tabelle in Locosoft
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# .env laden
env_path = '/opt/greiner-portal/config/.env'
load_dotenv(env_path)

def get_connection():
    return psycopg2.connect(
        host=os.getenv('LOCOSOFT_HOST'),
        port=os.getenv('LOCOSOFT_PORT', 5432),
        database=os.getenv('LOCOSOFT_DATABASE'),
        user=os.getenv('LOCOSOFT_USER'),
        password=os.getenv('LOCOSOFT_PASSWORD')
    )

def main():
    print("=" * 70)
    print("ANALYSE: employees_worktimes")
    print("=" * 70)
    print(f"Zeitpunkt: {datetime.now()}")
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # =========================================================================
    # 1. TABELLEN-STRUKTUR
    # =========================================================================
    print("\n" + "=" * 70)
    print("1. TABELLEN-STRUKTUR employees_worktimes")
    print("=" * 70)
    
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'employees_worktimes'
        ORDER BY ordinal_position
    """)
    
    cols = cur.fetchall()
    print("\nSpalten:")
    for c in cols:
        print(f"  {c['column_name']:25} | {c['data_type']:20} | Nullable: {c['is_nullable']}")
    
    # =========================================================================
    # 2. ANZAHL DATENSÄTZE
    # =========================================================================
    print("\n" + "=" * 70)
    print("2. ANZAHL DATENSÄTZE")
    print("=" * 70)
    
    cur.execute("SELECT COUNT(*) as cnt FROM employees_worktimes")
    cnt = cur.fetchone()['cnt']
    print(f"\nGesamt: {cnt} Datensätze")
    
    cur.execute("SELECT COUNT(*) as cnt FROM employees_worktimes WHERE is_latest_record = true")
    cnt_latest = cur.fetchone()['cnt']
    print(f"Davon is_latest_record=true: {cnt_latest}")
    
    # =========================================================================
    # 3. ALLE DATEN ANZEIGEN (wenn wenig)
    # =========================================================================
    print("\n" + "=" * 70)
    print("3. ALLE DATENSÄTZE (erste 50)")
    print("=" * 70)
    
    cur.execute("""
        SELECT 
            ew.*,
            eh.name as mitarbeiter_name
        FROM employees_worktimes ew
        LEFT JOIN employees_history eh ON ew.employee_number = eh.employee_number
            AND eh.is_latest_record = true
        ORDER BY ew.employee_number, ew.dayofweek
        LIMIT 50
    """)
    
    rows = cur.fetchall()
    print(f"\n{len(rows)} Zeilen:")
    print("-" * 100)
    
    for r in rows:
        dow_name = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'][r['dayofweek']] if r['dayofweek'] is not None else '?'
        print(f"  MA {r['employee_number']:5} | {r['mitarbeiter_name'] or 'N/A':25} | "
              f"Tag {r['dayofweek']} ({dow_name}) | "
              f"Dauer: {r['work_duration']} | "
              f"Von: {r['worktime_start']} | Bis: {r['worktime_end']} | "
              f"Gültig ab: {r['validity_date']} | Latest: {r['is_latest_record']}")
    
    # =========================================================================
    # 4. WELCHE MITARBEITER HABEN ARBEITSZEITEN?
    # =========================================================================
    print("\n" + "=" * 70)
    print("4. MITARBEITER MIT ARBEITSZEITEN")
    print("=" * 70)
    
    cur.execute("""
        SELECT DISTINCT 
            ew.employee_number,
            eh.name,
            eh.subsidiary,
            COUNT(*) as anzahl_eintraege
        FROM employees_worktimes ew
        LEFT JOIN employees_history eh ON ew.employee_number = eh.employee_number
            AND eh.is_latest_record = true
        GROUP BY ew.employee_number, eh.name, eh.subsidiary
        ORDER BY ew.employee_number
    """)
    
    ma_mit_zeit = cur.fetchall()
    print(f"\n{len(ma_mit_zeit)} Mitarbeiter haben Arbeitszeiten:")
    for m in ma_mit_zeit:
        print(f"  MA {m['employee_number']:5} | {m['name'] or 'N/A':25} | Betrieb {m['subsidiary']} | {m['anzahl_eintraege']} Einträge")
    
    # =========================================================================
    # 5. MECHANIKER OHNE ARBEITSZEITEN
    # =========================================================================
    print("\n" + "=" * 70)
    print("5. MECHANIKER (5000-5999) OHNE ARBEITSZEITEN")
    print("=" * 70)
    
    cur.execute("""
        SELECT 
            eh.employee_number,
            eh.name,
            eh.subsidiary,
            eh.mechanic_number
        FROM employees_history eh
        WHERE eh.is_latest_record = true
          AND eh.employee_number BETWEEN 5000 AND 5999
          AND eh.mechanic_number IS NOT NULL
          AND eh.subsidiary > 0
          AND (eh.leave_date IS NULL OR eh.leave_date > CURRENT_DATE)
          AND NOT EXISTS (
              SELECT 1 FROM employees_worktimes ew 
              WHERE ew.employee_number = eh.employee_number
          )
        ORDER BY eh.subsidiary, eh.name
    """)
    
    ohne_zeit = cur.fetchall()
    print(f"\n{len(ohne_zeit)} Mechaniker OHNE Arbeitszeiten:")
    for m in ohne_zeit:
        print(f"  MA {m['employee_number']:5} | {m['name']:25} | Betrieb {m['subsidiary']} | Mech-Nr: {m['mechanic_number']}")
    
    # =========================================================================
    # 6. PRÜFE ANDERE TABELLEN FÜR ARBEITSZEITEN
    # =========================================================================
    print("\n" + "=" * 70)
    print("6. ALTERNATIVE QUELLEN FÜR ARBEITSZEITEN?")
    print("=" * 70)
    
    # employees_history hat schedule_index - vielleicht gibt es eine schedule-Tabelle?
    cur.execute("""
        SELECT DISTINCT schedule_index, COUNT(*) as cnt
        FROM employees_history
        WHERE is_latest_record = true
          AND employee_number BETWEEN 5000 AND 5999
        GROUP BY schedule_index
        ORDER BY schedule_index
    """)
    
    schedules = cur.fetchall()
    print("\nschedule_index in employees_history:")
    for s in schedules:
        print(f"  Schedule {s['schedule_index']}: {s['cnt']} Mitarbeiter")
    
    # Gibt es eine schedule-Tabelle?
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
          AND (table_name LIKE '%schedule%' OR table_name LIKE '%work%' OR table_name LIKE '%zeit%')
    """)
    
    tables = cur.fetchall()
    print("\nTabellen mit 'schedule', 'work' oder 'zeit':")
    for t in tables:
        print(f"  - {t['table_name']}")
    
    # =========================================================================
    # 7. EMPLOYEES_HISTORY - PRODUKTIVITÄTSFAKTOR
    # =========================================================================
    print("\n" + "=" * 70)
    print("7. PRODUKTIVITÄTSFAKTOR IN EMPLOYEES_HISTORY")
    print("=" * 70)
    
    cur.execute("""
        SELECT 
            employee_number,
            name,
            subsidiary,
            productivity_factor,
            is_flextime
        FROM employees_history
        WHERE is_latest_record = true
          AND employee_number BETWEEN 5000 AND 5999
          AND mechanic_number IS NOT NULL
          AND subsidiary > 0
          AND (leave_date IS NULL OR leave_date > CURRENT_DATE)
        ORDER BY subsidiary, name
    """)
    
    faktoren = cur.fetchall()
    print("\nProduktivitätsfaktoren der Mechaniker:")
    for f in faktoren:
        print(f"  MA {f['employee_number']:5} | {f['name']:25} | Betrieb {f['subsidiary']} | "
              f"Faktor: {f['productivity_factor']} | Gleitzeit: {f['is_flextime']}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("ANALYSE ABGESCHLOSSEN")
    print("=" * 70)


if __name__ == '__main__':
    main()
