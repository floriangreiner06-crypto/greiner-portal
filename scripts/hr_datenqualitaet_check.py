#!/usr/bin/env python3
"""
HR DATENQUALITÄTS-CHECK FÜR LOCOSOFT
=====================================
Erstellt: 08.12.2025 (TAG 102) - FINAL
Für: Vanessa (HR)

KONTEXT-DOKUMENTATION:
- Siehe: docs/HR_LOCOSOFT_DATENPFLEGE_ANLEITUNG_V2.md
- Schema: docs/DB_SCHEMA_LOCOSOFT.md

Ausführung:
  cd /opt/greiner-portal
  source venv/bin/activate
  python3 scripts/hr_datenqualitaet_check.py
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import psycopg2
from datetime import datetime
from dotenv import load_dotenv

env_path = PROJECT_ROOT / 'config' / '.env'
load_dotenv(env_path)

LOCOSOFT_CONFIG = {
    'host': os.getenv('LOCOSOFT_HOST', '10.80.80.8'),
    'port': int(os.getenv('LOCOSOFT_PORT', 5432)),
    'database': os.getenv('LOCOSOFT_DATABASE', 'loco_auswertung_db'),
    'user': os.getenv('LOCOSOFT_USER', 'loco_auswertung_benutzer'),
    'password': os.getenv('LOCOSOFT_PASSWORD', 'loco')
}

# System-User die ignoriert werden (keine echten Mitarbeiter)
SYSTEM_USERS = [991, 994, 999, 9000, 9001]
SYSTEM_USER_FILTER = f"AND eh.employee_number NOT IN ({','.join(map(str, SYSTEM_USERS))})"


def get_connection():
    return psycopg2.connect(**LOCOSOFT_CONFIG)


def check_arbeitszeiten(conn):
    """
    Prüft: Haben alle MA Arbeitszeiten für Mo-Fr?
    """
    print("\n" + "="*70)
    print("1️⃣  ARBEITSZEITEN-CHECK (Pr. 811 → Arbeitszeitregelungen)")
    print("="*70)
    
    query = f"""
    WITH aktive_ma AS (
        SELECT DISTINCT eh.employee_number, eh.name
        FROM employees_history eh
        WHERE eh.is_latest_record = true
          AND eh.leave_date IS NULL
          {SYSTEM_USER_FILTER}
    ),
    arbeitszeiten AS (
        SELECT DISTINCT employee_number, dayofweek
        FROM employees_worktimes
        WHERE work_duration > 0
    )
    SELECT 
        am.employee_number,
        am.name,
        COALESCE(string_agg(
            CASE az.dayofweek 
                WHEN 1 THEN 'Mo'
                WHEN 2 THEN 'Di'
                WHEN 3 THEN 'Mi'
                WHEN 4 THEN 'Do'
                WHEN 5 THEN 'Fr'
                WHEN 6 THEN 'Sa'
            END, ', ' ORDER BY az.dayofweek
        ), 'KEINE') as vorhandene_tage,
        COUNT(DISTINCT az.dayofweek) as anzahl_tage
    FROM aktive_ma am
    LEFT JOIN arbeitszeiten az ON am.employee_number = az.employee_number
    GROUP BY am.employee_number, am.name
    HAVING COUNT(DISTINCT az.dayofweek) < 5
    ORDER BY COUNT(DISTINCT az.dayofweek), am.name
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    if results:
        print(f"\n⚠️  {len(results)} Mitarbeiter mit UNVOLLSTÄNDIGEN Arbeitszeiten:\n")
        print(f"{'MA-Nr':<8} {'Name':<30} {'Vorhandene Tage':<25} {'Anzahl'}")
        print("-" * 75)
        for row in results:
            ma_nr, name, tage, anzahl = row
            name_str = name[:29] if name else '-'
            print(f"{ma_nr:<8} {name_str:<30} {tage:<25} {anzahl}/5")
        
        print(f"\n📋 AKTION in Locosoft:")
        print(f"   → Pr. 811 öffnen → F9 (MA suchen)")
        print(f"   → Tab 'Arbeitszeitregelungen'")
        print(f"   → Fehlende Wochentage nachtragen")
        print(f"   → Tipp: F5 übernimmt Daten aus Vorzeile!")
    else:
        print("\n✅ Alle aktiven MA haben Arbeitszeiten für Mo-Fr")
    
    return results


def check_pausen(conn):
    """
    Prüft: Haben alle MA Pausen für jeden Arbeitstag?
    """
    print("\n" + "="*70)
    print("2️⃣  PAUSEN-CHECK (Pr. 811 → Arbeitszeitregelungen)")
    print("="*70)
    
    query = f"""
    WITH aktive_ma AS (
        SELECT DISTINCT eh.employee_number, eh.name
        FROM employees_history eh
        WHERE eh.is_latest_record = true
          AND eh.leave_date IS NULL
          {SYSTEM_USER_FILTER}
    ),
    pausen AS (
        SELECT DISTINCT employee_number, dayofweek
        FROM employees_breaktimes
        WHERE break_start IS NOT NULL
    ),
    arbeitszeiten AS (
        SELECT DISTINCT employee_number, dayofweek
        FROM employees_worktimes
        WHERE work_duration > 0
    )
    SELECT 
        am.employee_number,
        am.name,
        COUNT(DISTINCT az.dayofweek) as arbeits_tage,
        COUNT(DISTINCT p.dayofweek) as pausen_tage
    FROM aktive_ma am
    LEFT JOIN arbeitszeiten az ON am.employee_number = az.employee_number
    LEFT JOIN pausen p ON am.employee_number = p.employee_number
    GROUP BY am.employee_number, am.name
    HAVING COUNT(DISTINCT p.dayofweek) < COUNT(DISTINCT az.dayofweek)
       AND COUNT(DISTINCT az.dayofweek) > 0
    ORDER BY (COUNT(DISTINCT az.dayofweek) - COUNT(DISTINCT p.dayofweek)) DESC, am.name
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    if results:
        print(f"\n⚠️  {len(results)} Mitarbeiter mit FEHLENDEN Pausen:\n")
        print(f"{'MA-Nr':<8} {'Name':<30} {'Arbeitstage':<12} {'Pausentage':<12} {'Fehlen'}")
        print("-" * 75)
        for row in results:
            ma_nr, name, arbeits, pausen = row
            fehlend = arbeits - pausen
            name_str = name[:29] if name else '-'
            print(f"{ma_nr:<8} {name_str:<30} {arbeits:<12} {pausen:<12} {fehlend}")
        
        print(f"\n📋 AKTION in Locosoft:")
        print(f"   → Pr. 811 öffnen → F9 (MA suchen)")
        print(f"   → Tab 'Arbeitszeitregelungen'")
        print(f"   → Für JEDEN Arbeitstag Pause eintragen")
        print(f"   → Standard: 12:00 - 12:44 (44 Min)")
        print(f"\n⚠️  WICHTIG: Fehlende Pausen = falsche Überstunden-Berechnung!")
    else:
        print("\n✅ Alle aktiven MA haben Pausen für alle Arbeitstage")
    
    return results


def check_produktivitaet(conn):
    """
    Prüft: Haben produktive MA einen Leistungsfaktor > 0?
    """
    print("\n" + "="*70)
    print("3️⃣  PRODUKTIVITÄTSFAKTOR-CHECK (Pr. 811 → Kennzahlen/Indizes)")
    print("="*70)
    
    query = f"""
    SELECT 
        eh.employee_number,
        eh.name,
        eh.mechanic_number,
        COALESCE(eh.productivity_factor, 0) as faktor,
        eh.schedule_index,
        string_agg(DISTINCT g.grp_code, ', ') as gruppen
    FROM employees_history eh
    LEFT JOIN employees_group_mapping g ON eh.employee_number = g.employee_number
    WHERE eh.is_latest_record = true
      AND eh.leave_date IS NULL
      {SYSTEM_USER_FILTER}
      AND (
          eh.mechanic_number IS NOT NULL
          OR eh.schedule_index > 0
          OR g.grp_code IN ('MON', 'A-W', 'SB')
      )
    GROUP BY eh.employee_number, eh.name, eh.mechanic_number, 
             eh.productivity_factor, eh.schedule_index
    HAVING COALESCE(eh.productivity_factor, 0) = 0
    ORDER BY eh.schedule_index DESC NULLS LAST, eh.name
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Aufteilen nach schedule_index
    produktiv_100 = [r for r in results if r[4] == 100]
    andere = [r for r in results if r[4] != 100]
    
    if produktiv_100:
        print(f"\n⚠️  {len(produktiv_100)} PRODUKTIVE MA (schedule_index=100) mit Leistungsfaktor = 0:\n")
        print(f"{'MA-Nr':<8} {'Name':<25} {'Mont-Nr':<8} {'Gruppen'}")
        print("-" * 60)
        for row in produktiv_100:
            ma_nr, name, mont_nr, faktor, sched_idx, gruppen = row
            mont_str = str(mont_nr) if mont_nr else '-'
            gruppen_str = gruppen if gruppen else '-'
            name_str = name[:24] if name else '-'
            print(f"{ma_nr:<8} {name_str:<25} {mont_str:<8} {gruppen_str}")
        
        print(f"\n📋 AKTION in Locosoft:")
        print(f"   → Pr. 811 → Tab 'Kennzahlen/Indizes'")
        print(f"   → Leistungsfaktor setzen:")
        print(f"      • Mechaniker/Meister: 1.0")
        print(f"      • Azubi 3. LJ: 0.8")
        print(f"      • Azubi 2. LJ: 0.5")
        print(f"      • Azubi 1. LJ: 0.3")
    
    if andere:
        print(f"\nℹ️  {len(andere)} weitere MA (schedule_index≠100) - evtl. korrekt so:")
        for row in andere[:5]:
            print(f"   {row[0]}: {row[1]} (Gruppe: {row[5]})")
        if len(andere) > 5:
            print(f"   ... und {len(andere) - 5} weitere")
    
    if not results:
        print("\n✅ Alle produktiven MA haben Leistungsfaktor > 0")
    
    return produktiv_100  # Nur die wirklich produktiven zurückgeben


def check_gruppen_zuordnung(conn):
    """Zeigt Mitarbeiter ohne Gruppen-Zuordnung"""
    print("\n" + "="*70)
    print("4️⃣  GRUPPEN-ZUORDNUNG (Pr. 811 → Tab Gruppen/Profile)")
    print("="*70)
    
    query = f"""
    WITH aktive_ma AS (
        SELECT DISTINCT eh.employee_number, eh.name
        FROM employees_history eh
        WHERE eh.is_latest_record = true
          AND eh.leave_date IS NULL
          {SYSTEM_USER_FILTER}
    )
    SELECT 
        am.employee_number,
        am.name
    FROM aktive_ma am
    LEFT JOIN employees_group_mapping g ON am.employee_number = g.employee_number
    GROUP BY am.employee_number, am.name
    HAVING COUNT(g.grp_code) = 0
    ORDER BY am.name
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    if results:
        print(f"\n⚠️  {len(results)} Mitarbeiter OHNE Gruppen-Zuordnung:\n")
        for row in results:
            name_str = row[1][:40] if row[1] else '-'
            print(f"   {row[0]}: {name_str}")
        
        print(f"\n📋 AKTION in Locosoft:")
        print(f"   → Pr. 811 → Tab 'Gruppen/Profile'")
        print(f"   → Mindestens eine Gruppe zuweisen")
        print(f"\n⚠️  WICHTIG: Ohne Gruppe keine Urlaubsanträge in Pr. 813!")
    else:
        print("\n✅ Alle aktiven MA haben mindestens eine Gruppe")
    
    return results


def show_statistik(conn):
    """Zeigt Gesamtübersicht"""
    print("\n" + "="*70)
    print("📊 ÜBERSICHT")
    print("="*70)
    
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT 
            COUNT(*) FILTER (WHERE is_latest_record = true AND leave_date IS NULL) as aktiv,
            COUNT(*) FILTER (WHERE is_latest_record = true AND leave_date IS NOT NULL) as ausgeschieden,
            COUNT(*) FILTER (WHERE mechanic_number IS NOT NULL AND is_latest_record = true AND leave_date IS NULL) as monteure,
            COUNT(*) FILTER (WHERE schedule_index = 100 AND is_latest_record = true AND leave_date IS NULL) as produktiv
        FROM employees_history eh
        WHERE 1=1 {SYSTEM_USER_FILTER}
    """)
    row = cursor.fetchone()
    
    print(f"\n📊 Mitarbeiter-Statistik (ohne System-User):")
    print(f"   Aktive Mitarbeiter:      {row[0]}")
    print(f"   Davon Monteure:          {row[2]}")
    print(f"   Davon voll produktiv:    {row[3]} (schedule_index=100)")
    
    # Gruppen
    cursor.execute(f"""
        SELECT g.grp_code, COUNT(DISTINCT g.employee_number) as anzahl
        FROM employees_group_mapping g
        JOIN employees_history eh ON g.employee_number = eh.employee_number
        WHERE eh.is_latest_record = true AND eh.leave_date IS NULL
          {SYSTEM_USER_FILTER}
        GROUP BY g.grp_code
        ORDER BY COUNT(DISTINCT g.employee_number) DESC
    """)
    
    print(f"\n📊 Gruppen-Verteilung:")
    for row in cursor.fetchall():
        print(f"   {row[0]:<6}: {row[1]} MA")


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║     HR DATENQUALITÄTS-CHECK FÜR LOCOSOFT                             ║
║     Greiner Portal DRIVE - TAG 102 (FINAL)                           ║
╠══════════════════════════════════════════════════════════════════════╣
║  Dokumentation: docs/HR_LOCOSOFT_DATENPFLEGE_ANLEITUNG_V2.md         ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    print(f"Locosoft: {LOCOSOFT_CONFIG['host']} / {LOCOSOFT_CONFIG['database']}")
    print(f"System-User (ignoriert): {SYSTEM_USERS}")
    
    try:
        conn = get_connection()
        print("\n✅ Verbindung zu Locosoft hergestellt")
        
        show_statistik(conn)
        
        # Checks durchführen
        az_probleme = check_arbeitszeiten(conn)
        pausen_probleme = check_pausen(conn)
        prod_probleme = check_produktivitaet(conn)
        gruppen_probleme = check_gruppen_zuordnung(conn)
        
        conn.close()
        
        # Zusammenfassung
        print("\n" + "="*70)
        print("📋 ZUSAMMENFASSUNG")
        print("="*70)
        
        az_count = len(az_probleme) if az_probleme else 0
        pausen_count = len(pausen_probleme) if pausen_probleme else 0
        prod_count = len(prod_probleme) if prod_probleme else 0
        gruppen_count = len(gruppen_probleme) if gruppen_probleme else 0
        total = az_count + pausen_count + prod_count + gruppen_count
        
        print(f"""
┌─────────────────────────────────────────────────────────────────────┐
│  Check                              │ Probleme │ Priorität          │
├─────────────────────────────────────┼──────────┼────────────────────┤
│  1. Arbeitszeiten unvollständig     │ {az_count:>8} │ 🔴 HOCH            │
│  2. Pausen fehlen                   │ {pausen_count:>8} │ 🔴 HOCH            │
│  3. Produktivitätsfaktor = 0        │ {prod_count:>8} │ 🟡 MITTEL          │
│  4. Keine Gruppe zugewiesen         │ {gruppen_count:>8} │ 🟢 NIEDRIG         │
├─────────────────────────────────────┼──────────┼────────────────────┤
│  GESAMT zu bearbeiten               │ {total:>8} │                    │
└─────────────────────────────────────┴──────────┴────────────────────┘
        """)
        
        if total > 0:
            print("📌 Details siehe: docs/HR_LOCOSOFT_DATENPFLEGE_ANLEITUNG_V2.md")
        else:
            print("🎉 Alle Checks bestanden!")
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
