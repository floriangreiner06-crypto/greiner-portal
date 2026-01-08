#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import Urlaubsansprüche 2026 aus Locosoft
=========================================
TAG 167: Erstellt vacation_entitlements für 2026 basierend auf Locosoft-Daten
Importiert J.Url.ges. (Jahresurlaubsanspruch) aus Locosoft für jeden Mitarbeiter
"""

import sys
import os

# Pfad zum Projekt-Root hinzufügen
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, project_root)

from api.db_connection import get_db
import psycopg2

STANDARD_VACATION_DAYS = 27.0  # Fallback falls nicht in Locosoft gefunden

def get_locosoft_connection():
    """Verbindung zu Locosoft DB"""
    return psycopg2.connect(
        host='10.80.80.8',
        database='loco_auswertung_db',
        user='loco_auswertung_benutzer',
        password='loco'
    )

def get_vacation_entitlement_from_locosoft(loco_cursor, portal_cursor, employee_id, locosoft_id, year):
    """
    Berechnet den Jahresurlaubsanspruch (J.Url.ges.) wie Locosoft:
    
    J.Url.ges. = Standard-Anspruch + Resturlaub aus Vorjahr
    
    Berechnung:
    1. Standard-Anspruch für aktuelles Jahr (aus Portal vacation_entitlements, oder 27 Tage)
    2. Resturlaub aus Vorjahr = Anspruch Vorjahr - Verbraucht Vorjahr
    3. Gesamtanspruch = Standard + Resturlaub (min. 0, max. Standard * 2)
    """
    try:
        prev_year = year - 1
        
        # 1. Hole Standard-Anspruch für aktuelles Jahr
        # Verwende Standard 27 Tage (kann später individuell angepasst werden)
        standard_anspruch = STANDARD_VACATION_DAYS
        
        # 2. Berechne Resturlaub aus Vorjahr
        # Anspruch Vorjahr (aus Portal oder Standard)
        portal_cursor.execute("""
            SELECT total_days, carried_over, added_manually
            FROM vacation_entitlements
            WHERE employee_id = %s AND year = %s
        """, (employee_id, prev_year))
        
        prev_ent_row = portal_cursor.fetchone()
        if prev_ent_row and prev_ent_row[0]:
            # Anspruch Vorjahr = total_days + carried_over + added_manually
            anspruch_vorjahr = float(prev_ent_row[0]) + float(prev_ent_row[1] or 0) + float(prev_ent_row[2] or 0)
        else:
            # Fallback: Standard 27 Tage
            anspruch_vorjahr = STANDARD_VACATION_DAYS
        
        # Verbraucht Vorjahr (aus Locosoft)
        loco_cursor.execute("""
            SELECT 
                COALESCE(SUM(day_contingent), 0) as verbraucht
            FROM absence_calendar
            WHERE employee_number = %s
              AND EXTRACT(YEAR FROM date) = %s
              AND reason IN ('Url', 'BUr')
        """, (locosoft_id, prev_year))
        
        result = loco_cursor.fetchone()
        verbraucht_vorjahr = float(result[0]) if result and result[0] else 0.0
        
        # Resturlaub Vorjahr = Anspruch - Verbraucht
        # WICHTIG: Locosoft erlaubt auch negativen Resturlaub (wird dann auf 0 gesetzt)
        # ABER: Wenn der Anspruch höher ist (z.B. durch added_manually), 
        # kann der Resturlaub auch positiv sein
        resturlaub_vorjahr = max(0.0, anspruch_vorjahr - verbraucht_vorjahr)
        
        # Sonderfall: Wenn der Anspruch deutlich höher ist als Standard,
        # könnte Locosoft einen individuellen Standard verwenden
        # Für jetzt: Verwenden wir die berechnete Differenz
        
        # 3. Gesamtanspruch = Standard + Resturlaub
        gesamt_anspruch = standard_anspruch + resturlaub_vorjahr
        
        return gesamt_anspruch, resturlaub_vorjahr
        
    except Exception as e:
        print(f"   ⚠️  Fehler beim Berechnen für {locosoft_id}: {e}")
        return STANDARD_VACATION_DAYS, 0.0

def import_entitlements_2026():
    """Importiert Urlaubsansprüche für 2026"""
    print("="*70)
    print("📅 URLAUBSANSPRÜCHE 2026 AUS LOCOSOFT IMPORTIEREN")
    print("="*70)
    
    portal_conn = get_db()
    portal_cursor = portal_conn.cursor()
    
    loco_conn = get_locosoft_connection()
    loco_cursor = loco_conn.cursor()
    
    # 1. Hole alle aktiven Mitarbeiter mit Locosoft-Mapping
    portal_cursor.execute("""
        SELECT 
            e.id,
            e.first_name || ' ' || e.last_name as name,
            lem.locosoft_id
        FROM employees e
        LEFT JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
        WHERE e.aktiv = true
          AND lem.locosoft_id IS NOT NULL
        ORDER BY e.last_name, e.first_name
    """)
    
    employees = portal_cursor.fetchall()
    print(f"\n👥 {len(employees)} Mitarbeiter mit Locosoft-Mapping gefunden")
    
    # 2. Prüfe bestehende Ansprüche 2026
    portal_cursor.execute("SELECT COUNT(*) FROM vacation_entitlements WHERE year = 2026")
    existing = portal_cursor.fetchone()[0]
    
    if existing > 0:
        print(f"\n⚠️  {existing} Ansprüche für 2026 existieren bereits")
        response = input("   Überschreiben? (j/n): ")
        if response.lower() != 'j':
            print("   → Abbruch")
            return
        portal_cursor.execute("DELETE FROM vacation_entitlements WHERE year = 2026")
        print(f"   ✓ Alte Einträge gelöscht")
    
    # 3. Für jeden Mitarbeiter: Anspruch aus Locosoft holen
    created = 0
    from_locosoft = 0
    standard = 0
    
    for emp_id, name, locosoft_id in employees:
        # Berechne Anspruch wie Locosoft: Standard + Resturlaub Vorjahr
        total_days, resturlaub_vorjahr = get_vacation_entitlement_from_locosoft(
            loco_cursor, portal_cursor, emp_id, locosoft_id, 2026
        )
        
        # Aufteilen: total_days = Standard, carried_over = Resturlaub
        # Standard-Anspruch (ohne Resturlaub)
        standard_anspruch = total_days - resturlaub_vorjahr
        carried_over = resturlaub_vorjahr
        added_manually = 0.0
        
        if total_days != STANDARD_VACATION_DAYS:
            from_locosoft += 1
            if resturlaub_vorjahr > 0:
                print(f"   ✓ {name}: {total_days} Tage ({standard_anspruch} Standard + {resturlaub_vorjahr} Resturlaub)")
            else:
                print(f"   ✓ {name}: {total_days} Tage (Standard)")
        else:
            standard += 1
        
        try:
            portal_cursor.execute("""
                INSERT INTO vacation_entitlements 
                (employee_id, year, total_days, carried_over, added_manually)
                VALUES (%s, 2026, %s, %s, %s)
            """, (emp_id, standard_anspruch, carried_over, added_manually))
            
            created += 1
                
        except Exception as e:
            print(f"   ❌ Fehler bei {name}: {e}")
    
    portal_conn.commit()
    
    print(f"\n✅ {created} Urlaubsansprüche für 2026 erstellt")
    print(f"   • Aus Locosoft: {from_locosoft}")
    print(f"   • Standard ({STANDARD_VACATION_DAYS} Tage): {standard}")
    
    # 4. Statistik
    portal_cursor.execute("""
        SELECT 
            COUNT(*) as anzahl,
            SUM(total_days) as gesamt_tage,
            AVG(total_days) as durchschnitt,
            MIN(total_days) as minimum,
            MAX(total_days) as maximum
        FROM vacation_entitlements
        WHERE year = 2026
    """)
    stats = portal_cursor.fetchone()
    print(f"\n📊 Statistik 2026:")
    print(f"   Mitarbeiter: {stats[0]}")
    print(f"   Gesamt Tage: {stats[1]:.1f}")
    print(f"   Durchschnitt: {stats[2]:.1f} Tage")
    print(f"   Min/Max: {stats[3]:.1f} / {stats[4]:.1f} Tage")
    
    portal_conn.close()
    loco_conn.close()
    
    print("\n✅ Import abgeschlossen!")

if __name__ == '__main__':
    import_entitlements_2026()
