#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüft Urlaubsanspruch für Bianca Greindl (Teilzeit → 12 Tage).
Ausführung: python3 scripts/checks/check_bianca_greindl_urlaubsanspruch.py
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from api.db_utils import db_session

def main():
    with db_session() as conn:
        cur = conn.cursor()

        # 1. Bianca Greindl finden
        cur.execute("""
            SELECT id, first_name, last_name, email, department_name, locosoft_id, aktiv
            FROM employees
            WHERE last_name ILIKE %s AND first_name ILIKE %s
        """, ('%Greindl%', '%Bianca%'))
        row = cur.fetchone()
        if not row:
            print("Bianca Greindl nicht gefunden.")
            return
        emp_id, first, last, email, dept, locosoft_id, aktiv = row
        print(f"=== {first} {last} (ID={emp_id}, Abt={dept}, Locosoft-ID={locosoft_id}) ===\n")

        # 2. vacation_entitlements
        cur.execute("""
            SELECT year, total_days, carried_over, added_manually, updated_at
            FROM vacation_entitlements
            WHERE employee_id = %s
            ORDER BY year
        """, (emp_id,))
        ents = cur.fetchall()
        print("vacation_entitlements:")
        if not ents:
            print("  (keine Einträge – es wird der Standard 27 verwendet)")
        for r in ents:
            print(f"  Jahr {r[0]}: total_days={r[1]}, Übertrag={r[2]}, Korrektur={r[3]}, updated={r[4]}")

        # 3. Arbeitszeitmodelle (Teilzeit?)
        cur.execute("""
            SELECT id, start_date, end_date, hours_per_week, working_days_per_week, description
            FROM employee_working_time_models
            WHERE employee_id = %s
            ORDER BY start_date
        """, (emp_id,))
        wt = cur.fetchall()
        print("\nArbeitszeitmodelle (employee_working_time_models):")
        if not wt:
            print("  (keine Einträge – Teilzeit wird in DRIVE nicht für Anspruch genutzt)")
        for r in wt:
            print(f"  {r[2]}–{r[3]}: {r[4]} h/Woche, {r[5]} Tage/Woche – {r[6] or '-'}")

        # 4. View-Saldo (v_vacation_balance_2026)
        cur.execute("""
            SELECT anspruch, verbraucht, geplant, resturlaub
            FROM v_vacation_balance_2026
            WHERE employee_id = %s
        """, (emp_id,))
        bal = cur.fetchone()
        print("\nv_vacation_balance_2026:")
        if bal:
            print(f"  Anspruch={bal[0]}, Verbraucht={bal[1]}, Geplant={bal[2]}, Resturlaub={bal[3]}")
        else:
            print("  (kein Eintrag)")

        # 5. Ursache & Korrektur-SQL
        print("\n--- Warum 25? ---")
        print("DRIVE vergibt beim Jahres-Setup für alle Mitarbeiter standardmäßig 27 Tage (Vollzeit).")
        print("Teilzeit (z. B. 12 Tage) wird aktuell NICHT aus Arbeitszeitmodellen berechnet.")
        print("Die angezeigte Zahl ist Resturlaub = Anspruch − Verbraucht − Geplant (ggf. nach Locosoft-Korrektur).")
        print("\n--- Korrektur: Teilzeit 12 Tage (Gesamtanspruch) ---")
        print("-- 2026: total_days=12, carried_over=0 damit Anspruch = 12 (nicht 27+14)")
        print("-- SQL (nach Prüfung ausführen):")
        print(f"UPDATE vacation_entitlements SET total_days = 12, carried_over = 0, updated_at = CURRENT_TIMESTAMP WHERE employee_id = {emp_id} AND year = 2026;")
        for y in [2025, 2027]:
            print(f"UPDATE vacation_entitlements SET total_days = 12, updated_at = CURRENT_TIMESTAMP WHERE employee_id = {emp_id} AND year = {y};")
        print()

if __name__ == '__main__':
    main()
