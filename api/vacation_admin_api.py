#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VACATION ADMIN API V2 - Mit Locosoft Abwesenheiten
TAG 103 - Separate Spalten: Urlaub | ZA | Krank | Sonstige
Updated: TAG 118 - Migration auf db_session/locosoft_session
"""

from flask import Blueprint, jsonify, request, Response
from flask_login import current_user, login_required
from datetime import datetime
import csv
import io
import json

# Zentrale DB-Utilities (TAG118)
from api.db_utils import db_session, locosoft_session
from api.vacation_approver_service import is_approver as is_vacation_approver
from api.vacation_api import _check_substitute_vacation_conflict, _check_max_absence_per_dept_location

vacation_admin_api = Blueprint('vacation_admin_api', __name__, url_prefix='/api/vacation/admin')

def is_vacation_admin():
    """Prüft ob User in GRP_Urlaub_Admin ist oder Portal-Admin."""
    if not current_user.is_authenticated:
        return False
    
    if getattr(current_user, 'portal_role', '') == 'admin':
        return True
    
    user_groups = getattr(current_user, 'groups', []) or []
    if isinstance(user_groups, str):
        try:
            user_groups = json.loads(user_groups)
        except:
            user_groups = []
    
    if 'GRP_Urlaub_Admin' in user_groups:
        return True
    
    allowed_users = ['florian.greiner', 'vanessa.groll', 'christian.aichinger', 'sandra.brendel']
    username = getattr(current_user, 'username', '') or ''
    username_clean = username.lower().split('@')[0]
    
    return username_clean in allowed_users


def can_manage_vacation_blocks():
    """Urlaubssperren lesen/erstellen/löschen: Urlaub-Admin oder Portal-Admin (explizit für Löschen)."""
    if not current_user.is_authenticated:
        return False
    if is_vacation_admin():
        return True
    if getattr(current_user, 'portal_role', None) == 'admin':
        return True
    return False


@vacation_admin_api.route('/employees', methods=['GET'])
@login_required
def get_employees():
    """
    GET /api/vacation/admin/employees?year=2025
    
    Gibt alle MA mit Urlaubsdaten + Locosoft Abwesenheiten zurück
    """
    if not is_vacation_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        year = request.args.get('year', 2025, type=int)

        # 1. Locosoft Abwesenheiten pro Mitarbeiter holen
        loco_absences = {}
        try:
            with locosoft_session() as loco_conn:
                loco_cur = loco_conn.cursor()

                loco_cur.execute("""
                    SELECT
                        e.employee_number,
                        e.name,
                        COALESCE(SUM(CASE WHEN a.reason IN ('Url', 'BUr') THEN a.day_contingent ELSE 0 END), 0) as urlaub,
                        COALESCE(SUM(CASE WHEN a.reason = 'ZA.' THEN a.day_contingent ELSE 0 END), 0) as zeitausgleich,
                        COALESCE(SUM(CASE WHEN a.reason = 'Krn' THEN a.day_contingent ELSE 0 END), 0) as krank,
                        COALESCE(SUM(CASE WHEN a.reason NOT IN ('Url', 'BUr', 'ZA.', 'Krn') THEN a.day_contingent ELSE 0 END), 0) as sonstige
                    FROM employees e
                    LEFT JOIN absence_calendar a ON e.employee_number = a.employee_number
                        AND a.date >= %s AND a.date <= %s
                    WHERE e.is_latest_record = true OR e.is_latest_record IS NULL
                    GROUP BY e.employee_number, e.name
                """, (f'{year}-01-01', f'{year}-12-31'))

                for row in loco_cur.fetchall():
                    emp_num = row[0]
                    loco_absences[emp_num] = {
                        'loco_name': row[1],
                        'urlaub': float(row[2] or 0),
                        'zeitausgleich': float(row[3] or 0),
                        'krank': float(row[4] or 0),
                        'sonstige': float(row[5] or 0)
                    }
        except Exception as e:
            print(f"Locosoft-Fehler: {e}")
        
        # 2. SQLite Mitarbeiter + Ansprüche
        with db_session() as conn:
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT
                    e.id as employee_id,
                    e.first_name || ' ' || e.last_name as name,
                    e.aktiv,
                    e.locosoft_id,
                    COALESCE(ve.total_days, 27.0) as anspruch,
                    COALESCE(ve.carried_over, 0) as uebertrag,
                    COALESCE(ve.added_manually, 0) as korrektur,
                    COALESCE(e.location, 'Unbekannt') as standort,
                    e.department_name as grp_code
                FROM employees e
                LEFT JOIN vacation_entitlements ve ON e.id = ve.employee_id AND ve.year = {year}
                WHERE e.aktiv = true
                ORDER BY e.last_name, e.first_name
            """)

            employees = []
            totals = {'count': 0, 'anspruch': 0, 'urlaub': 0, 'za': 0, 'krank': 0}

            for row in cursor.fetchall():
                locosoft_id = row['locosoft_id']
                anspruch = row['anspruch'] or 27.0
                uebertrag = row['uebertrag'] or 0
                korrektur = row['korrektur'] or 0
                gesamt_anspruch = anspruch + uebertrag + korrektur

                # Locosoft Abwesenheiten
                loco = loco_absences.get(locosoft_id, {})
                urlaub = loco.get('urlaub', 0)
                zeitausgleich = loco.get('zeitausgleich', 0)
                krank = loco.get('krank', 0)
                sonstige = loco.get('sonstige', 0)

                # Verfügbar = Anspruch - nur Urlaub (nicht ZA!)
                verfuegbar = round(gesamt_anspruch - urlaub, 1)

                employees.append({
                    'employee_id': row['employee_id'],
                    'name': row['name'],
                    'aktiv': bool(row['aktiv']),
                    'standort': row['standort'],
                    'grp_code': row['grp_code'],
                    'locosoft_id': locosoft_id,
                    'anspruch': anspruch,
                    'uebertrag': uebertrag,
                    'korrektur': korrektur,
                    'urlaub': urlaub,
                    'zeitausgleich': zeitausgleich,
                    'krank': krank,
                    'sonstige': sonstige,
                    'verfuegbar': verfuegbar
                })

                totals['count'] += 1
                totals['anspruch'] += anspruch
                totals['urlaub'] += urlaub
                totals['za'] += zeitausgleich
                totals['krank'] += krank

            # Statistiken
            if totals['count'] > 0:
                stats = {
                    'count': totals['count'],
                    'avg_anspruch': round(totals['anspruch'] / totals['count'], 1),
                    'avg_urlaub': round(totals['urlaub'] / totals['count'], 1),
                    'avg_za': round(totals['za'] / totals['count'], 1),
                    'avg_krank': round(totals['krank'] / totals['count'], 1),
                    'total_urlaub': round(totals['urlaub'], 1),
                    'total_za': round(totals['za'], 1),
                    'total_krank': round(totals['krank'], 1)
                }
            else:
                stats = {'count': 0, 'avg_anspruch': 0, 'avg_urlaub': 0, 'avg_za': 0, 'avg_krank': 0}

            return jsonify({
                'success': True,
                'year': year,
                'employees': employees,
                'stats': stats
            })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_admin_api.route('/update-entitlement', methods=['POST'])
@login_required
def update_entitlement():
    """POST /api/vacation/admin/update-entitlement - Anspruch aktualisieren"""
    if not is_vacation_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        year = data.get('year', 2025)
        anspruch = data.get('anspruch', 27.0)
        uebertrag = data.get('uebertrag', 0)
        korrektur = data.get('korrektur', 0)

        if not employee_id:
            return jsonify({'success': False, 'error': 'employee_id fehlt'}), 400

        with db_session() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO vacation_entitlements (employee_id, year, total_days, carried_over, added_manually, updated_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT(employee_id, year) DO UPDATE SET
                    total_days = excluded.total_days,
                    carried_over = excluded.carried_over,
                    added_manually = excluded.added_manually,
                    updated_at = CURRENT_TIMESTAMP
            """, (employee_id, year, anspruch, uebertrag, korrektur))

            cursor.execute("""
                UPDATE employees
                SET vacation_days_total = %s, vacation_entitlement = %s
                WHERE id = %s
            """, (anspruch, anspruch, employee_id))

            conn.commit()

        return jsonify({'success': True, 'message': 'Urlaubsanspruch aktualisiert'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@vacation_admin_api.route('/bulk-update', methods=['POST'])
@login_required
def bulk_update():
    """POST /api/vacation/admin/bulk-update - Mehrere MA aktualisieren"""
    if not is_vacation_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403

    try:
        data = request.get_json()
        changes = data.get('changes', [])

        if not changes:
            return jsonify({'success': False, 'error': 'Keine Änderungen'}), 400

        with db_session() as conn:
            cursor = conn.cursor()
            updated = 0

            for change in changes:
                employee_id = change.get('employee_id')
                year = change.get('year', 2025)

                if not employee_id:
                    continue

                cursor.execute("""
                    SELECT total_days, carried_over, added_manually
                    FROM vacation_entitlements
                    WHERE employee_id = %s AND year = %s
                """, (employee_id, year))
                current = cursor.fetchone()

                anspruch = change.get('anspruch', current['total_days'] if current else 27.0)
                uebertrag = change.get('uebertrag', current['carried_over'] if current else 0)
                korrektur = change.get('korrektur', current['added_manually'] if current else 0)

                cursor.execute("""
                    INSERT INTO vacation_entitlements (employee_id, year, total_days, carried_over, added_manually, updated_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT(employee_id, year) DO UPDATE SET
                        total_days = excluded.total_days,
                        carried_over = excluded.carried_over,
                        added_manually = excluded.added_manually,
                        updated_at = CURRENT_TIMESTAMP
                """, (employee_id, year, anspruch, uebertrag, korrektur))

                updated += 1

            conn.commit()

        return jsonify({'success': True, 'updated': updated})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@vacation_admin_api.route('/mass-booking', methods=['POST'])
@login_required
def mass_booking():
    """
    POST /api/vacation/admin/mass-booking
    TAG 198: Masseneingabe für Urlaubstage pro Abteilung/alle Mitarbeiter
    Schulung (9) und Krankheit (5): nur Genehmiger oder Admin.
    """
    try:
        data = request.get_json() or {}
        vacation_type_id = data.get('vacation_type_id', 1)
    except Exception:
        vacation_type_id = 1
    # Berechtigung: Krankheit (5) NUR Admin; Schulung (9) Genehmiger oder Admin; sonst nur Admin (Test DRIVE)
    ldap_username = getattr(current_user, 'username', '') or ''
    if not is_vacation_admin():
        if vacation_type_id == 5:
            return jsonify({'success': False, 'error': 'Krankheitstage können nur von Admins eingetragen werden'}), 403
        if vacation_type_id != 9:
            return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
        if not is_vacation_approver(ldap_username):
            return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        dates = data.get('dates', [])
        vacation_type_id = data.get('vacation_type_id', 1)
        day_part = data.get('day_part', 'full')
        employee_ids = data.get('employee_ids', [])
        department = data.get('department')
        all_employees = data.get('all_employees', False)
        auto_approve = data.get('auto_approve', False)
        comment = data.get('comment', '')
        override_substitute_rule = data.get('override_substitute_rule', False)  # Vertretungsregel ignorieren (z. B. 24.12./31.12.)
        
        if not dates:
            return jsonify({'success': False, 'error': 'Keine Daten angegeben'}), 400
        
        # Bestimme Ziel-Mitarbeiter
        target_employee_ids = []
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            if employee_ids:
                # Spezifische Mitarbeiter
                placeholders = ','.join(['%s'] * len(employee_ids))
                cursor.execute(f"""
                    SELECT id FROM employees 
                    WHERE id IN ({placeholders}) AND aktiv = true
                """, employee_ids)
                target_employee_ids = [row[0] for row in cursor.fetchall()]
            elif department:
                # Ganze Abteilung
                cursor.execute("""
                    SELECT id FROM employees 
                    WHERE department_name = %s AND aktiv = true
                """, (department,))
                target_employee_ids = [row[0] for row in cursor.fetchall()]
            elif all_employees:
                # Alle Mitarbeiter
                cursor.execute("""
                    SELECT id FROM employees WHERE aktiv = true
                """)
                target_employee_ids = [row[0] for row in cursor.fetchall()]
            else:
                return jsonify({'success': False, 'error': 'Keine Ziel-Mitarbeiter angegeben'}), 400
            
            if not target_employee_ids:
                return jsonify({'success': False, 'error': 'Keine Mitarbeiter gefunden'}), 404
            
            # TAG 213 DEBUG: Log welche Mitarbeiter gefunden wurden
            print(f"📅 Masseneingabe: {len(target_employee_ids)} Mitarbeiter gefunden: {target_employee_ids[:5]}...")
            
            # Buche für alle Mitarbeiter; Zähler für Überspring-Gründe (Transparenz für User)
            created_count = 0
            skipped_block = 0
            skipped_already_booked = 0
            skipped_substitute = 0
            skipped_max_absence = 0
            status = 'approved' if auto_approve else 'pending'
            
            for emp_id in target_employee_ids:
                # Abteilung des MA für Urlaubssperren-Prüfung (Usertest: Sperre auch für Admins)
                emp_dept = None
                if vacation_type_id == 1:
                    cursor.execute("SELECT department_name FROM employees WHERE id = %s", (emp_id,))
                    row = cursor.fetchone()
                    emp_dept = row[0] if row else None
                
                for date_str in dates:
                    # Urlaubssperre: Abteilung oder spezifische MA (kein Admin-Bypass)
                    if vacation_type_id == 1:
                        cursor.execute("""
                            SELECT 1 FROM vacation_blocks
                            WHERE block_date = %s
                              AND (department_name = %s
                                   OR (employee_ids IS NOT NULL AND (',' || employee_ids || ',') LIKE %s))
                        """, (date_str, emp_dept or '', '%,' + str(emp_id) + ',%'))
                        if cursor.fetchone():
                            skipped_block += 1
                            continue  # Gesperrter Tag – überspringen
                    
                    # Prüfe ob bereits gebucht
                    cursor.execute("""
                        SELECT id FROM vacation_bookings
                        WHERE employee_id = %s AND booking_date = %s AND status != 'cancelled'
                    """, (emp_id, date_str))
                    
                    if cursor.fetchone():
                        skipped_already_booked += 1
                        continue  # Überspringe wenn bereits gebucht
                    
                    # Vertretungsregel: Vertreter darf an Tagen, an denen die vertretene Person abwesend ist, keinen Urlaub buchen
                    # Ausnahme: 24.12. und 31.12. (Betriebsferien) – Vertretungsregel bei Masseneingabe ignorieren
                    # Oder: berechtigter Nutzer hat "Vertretungsregel ignorieren" (Override) aktiviert
                    skip_substitute_check = (
                        override_substitute_rule
                        or (date_str.endswith('-12-24') or date_str.endswith('-12-31'))
                    )
                    if vacation_type_id == 1 and not skip_substitute_check:
                        conflict = _check_substitute_vacation_conflict(cursor, emp_id, [date_str])
                        if conflict:
                            skipped_substitute += 1
                            continue
                    
                    # Max. Abwesenheit pro Abteilung/Standort (Urlaub + Schulung; Default 50%)
                    if vacation_type_id in (1, 9):
                        cap = _check_max_absence_per_dept_location(cursor, emp_id, [date_str], vacation_type_id)
                        if cap:
                            skipped_max_absence += 1
                            continue  # Überspringen (Grenze würde überschritten)
                    
                    # Erstelle Buchung
                    cursor.execute("""
                        INSERT INTO vacation_bookings 
                        (employee_id, booking_date, vacation_type_id, day_part, status, comment, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """, (emp_id, date_str, vacation_type_id, day_part, status, comment))
                    created_count += 1
                    # TAG 213 DEBUG: Log erste 3 Buchungen
                    if created_count <= 3:
                        print(f"  ✅ Buchung erstellt: employee_id={emp_id}, date={date_str}, status={status}")
            
            conn.commit()
            print(f"📅 Masseneingabe abgeschlossen: {created_count} Buchungen für {len(target_employee_ids)} Mitarbeiter erstellt")
        
        return jsonify({
            'success': True,
            'created': created_count,
            'employees': len(target_employee_ids),
            'dates': len(dates),
            'auto_approve': auto_approve,
            'override_substitute_rule': override_substitute_rule,
            'substitute_conflict_skipped': skipped_substitute,
            'skipped': {
                'block': skipped_block,
                'already_booked': skipped_already_booked,
                'substitute': skipped_substitute,
                'max_absence': skipped_max_absence
            }
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_admin_api.route('/year-end-report', methods=['GET'])
@login_required
def year_end_report():
    """
    GET /api/vacation/admin/year-end-report?year=2026
    TAG 198: Jahresend-Report - CSV Export mit genommenen/übrigen Urlaubstagen
    """
    if not is_vacation_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Hole alle Urlaubssalden für das Jahr
            # TAG 198: View hat email als 3. Spalte, daher explizit Spalten auswählen
            cursor.execute(f"""
                SELECT
                    employee_id,
                    name,
                    email,
                    department,
                    location,
                    anspruch,
                    verbraucht,
                    geplant,
                    resturlaub
                FROM v_vacation_balance_{year}
                ORDER BY department, name
            """)
            
            rows = cursor.fetchall()
            
            # Erstelle CSV
            output = io.StringIO()
            # TAG 198: UTF-8 BOM für Excel-Kompatibilität
            output.write('\ufeff')  # UTF-8 BOM
            writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            
            # Header
            writer.writerow([
                'Mitarbeiter',
                'Abteilung',
                'Standort',
                'Urlaubsanspruch',
                'Genommen',
                'Geplant',
                'Resturlaub'
            ])
            
            # Daten (Rollout SSOT: Anspruch/Rest aus View, keine pauschalen Abzüge)
            for row in rows:
                anspruch = round(float(row[5] or 0), 1)
                rest = round(float(row[8] or 0), 1) if row[8] is not None else 0
                writer.writerow([
                    str(row[1]) if row[1] else '',
                    str(row[3]) if row[3] else '',
                    str(row[4]) if row[4] else '',
                    anspruch,
                    round(float(row[6]), 1) if row[6] is not None else 0,
                    round(float(row[7]), 1) if row[7] is not None else 0,
                    rest
                ])
            
            output.seek(0)
            csv_content = output.getvalue()
            
            return Response(
                csv_content.encode('utf-8-sig'),  # UTF-8 mit BOM für Excel
                mimetype='text/csv; charset=utf-8',
                headers={
                    'Content-Disposition': f'attachment; filename=urlaubsreport_{year}.csv'
                }
            )
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================================
# Urlaubs-Report monatlich (Jahresrückstellung) + Export
# ============================================================================

@vacation_admin_api.route('/report-monthly', methods=['GET'])
@login_required
def report_monthly():
    """
    GET /api/vacation/admin/report-monthly?year=2026
    Liefert Urlaubsreport mit monatlicher Aufteilung (Name, Anspruch, Übertrag, Genommen, Rest, Jan–Dez)
    für Mitarbeiterverwaltung Reporte-Modal und Export.
    """
    if not is_vacation_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        
        try:
            from api.vacation_year_utils import ensure_vacation_year_setup_simple
            ensure_vacation_year_setup_simple(year)
        except Exception as e:
            print(f"⚠️ report-monthly: Jahres-Setup {e}")
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Balance aus View (wie /balance)
            cursor.execute(f"""
                SELECT employee_id, name, department, anspruch, verbraucht, resturlaub
                FROM v_vacation_balance_{year}
                ORDER BY department, name
            """)
            balance_rows = cursor.fetchall()
            
            # Personalnummer + Übertrag pro MA
            cursor.execute("""
                SELECT e.id, e.personal_nr, COALESCE(ve.carried_over, 0)
                FROM employees e
                LEFT JOIN vacation_entitlements ve ON e.id = ve.employee_id AND ve.year = %s
                WHERE e.aktiv = true
            """, (year,))
            emp_extra = {row[0]: {'personal_nr': row[1] or '', 'carried_over': float(row[2] or 0)} for row in cursor.fetchall()}
            
            # Urlaubstage pro Monat (nur Urlaub type_id=1, approved+pending)
            cursor.execute("""
                SELECT employee_id, EXTRACT(MONTH FROM booking_date)::integer as month,
                       SUM(CASE WHEN day_part = 'full' THEN 1.0 WHEN day_part IN ('half','am','pm') THEN 0.5 ELSE 1.0 END) as days
                FROM vacation_bookings
                WHERE EXTRACT(YEAR FROM booking_date) = %s AND vacation_type_id = 1
                  AND status IN ('approved', 'pending')
                GROUP BY employee_id, EXTRACT(MONTH FROM booking_date)
            """, (year,))
            monthly = {}
            for row in cursor.fetchall():
                eid, month, days = row[0], int(row[1]), round(float(row[2] or 0), 1)
                if eid not in monthly:
                    monthly[eid] = {}
                monthly[eid][month] = days
            
            rows = []
            for r in balance_rows:
                emp_id, name, dept, anspruch_raw, verbraucht, resturlaub_raw = r[0], r[1], r[2], float(r[3] or 0), float(r[4] or 0), float(r[5] or 0)
                anspruch = round(anspruch_raw, 1)
                resturlaub = max(0, round(resturlaub_raw, 1))
                extra = emp_extra.get(emp_id, {})
                carried = extra.get('carried_over', 0)
                personal_nr = extra.get('personal_nr', '') or ''
                gesamt = anspruch  # effektiver Anspruch (mit Weihnachten/Silvester-Abzug)
                months = monthly.get(emp_id, {})
                row = {
                    'employee_id': emp_id,
                    'personal_nr': personal_nr,
                    'name': name or '',
                    'department': (dept or '').replace('⚠️ ', '').strip(),
                    'anspruch': round(anspruch, 1),
                    'carried_over': round(carried, 1),
                    'gesamt': round(gesamt, 1),
                    'verbraucht': round(verbraucht, 1),
                    'resturlaub': round(resturlaub, 1),
                    'month_1': round(months.get(1, 0), 1),
                    'month_2': round(months.get(2, 0), 1),
                    'month_3': round(months.get(3, 0), 1),
                    'month_4': round(months.get(4, 0), 1),
                    'month_5': round(months.get(5, 0), 1),
                    'month_6': round(months.get(6, 0), 1),
                    'month_7': round(months.get(7, 0), 1),
                    'month_8': round(months.get(8, 0), 1),
                    'month_9': round(months.get(9, 0), 1),
                    'month_10': round(months.get(10, 0), 1),
                    'month_11': round(months.get(11, 0), 1),
                    'month_12': round(months.get(12, 0), 1),
                }
                rows.append(row)
        
        return jsonify({'success': True, 'year': year, 'rows': rows})
    
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


@vacation_admin_api.route('/report-monthly/export', methods=['GET'])
@login_required
def report_monthly_export():
    """
    GET /api/vacation/admin/report-monthly/export?year=2026
    Export als CSV (Jahresrückstellung, monatliche Darstellung).
    """
    if not is_vacation_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        
        # Daten holen (gleiche Logik wie report_monthly)
        with db_session() as conn:
            cursor = conn.cursor()
            try:
                from api.vacation_year_utils import ensure_vacation_year_setup_simple
                ensure_vacation_year_setup_simple(year)
            except Exception:
                pass
            
            cursor.execute(f"""
                SELECT employee_id, name, department, anspruch, verbraucht, resturlaub
                FROM v_vacation_balance_{year}
                ORDER BY department, name
            """)
            balance_rows = cursor.fetchall()
            
            cursor.execute("""
                SELECT e.id, e.personal_nr, COALESCE(ve.carried_over, 0)
                FROM employees e
                LEFT JOIN vacation_entitlements ve ON e.id = ve.employee_id AND ve.year = %s
                WHERE e.aktiv = true
            """, (year,))
            emp_extra = {row[0]: {'personal_nr': row[1] or '', 'carried_over': float(row[2] or 0)} for row in cursor.fetchall()}
            
            cursor.execute("""
                SELECT employee_id, EXTRACT(MONTH FROM booking_date)::integer as month,
                       SUM(CASE WHEN day_part = 'full' THEN 1.0 WHEN day_part IN ('half','am','pm') THEN 0.5 ELSE 1.0 END) as days
                FROM vacation_bookings
                WHERE EXTRACT(YEAR FROM booking_date) = %s AND vacation_type_id = 1
                  AND status IN ('approved', 'pending')
                GROUP BY employee_id, EXTRACT(MONTH FROM booking_date)
            """, (year,))
            monthly = {}
            for row in cursor.fetchall():
                eid, month, days = row[0], int(row[1]), round(float(row[2] or 0), 1)
                if eid not in monthly:
                    monthly[eid] = {}
                monthly[eid][month] = days
            
            output = io.StringIO()
            output.write('\ufeff')
            writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            monatsnamen = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
            writer.writerow([
                'Personalnr', 'Mitarbeiter', 'Abteilung', 'Anspruch', 'Übertrag', 'Gesamt', 'Genommen', 'Rest',
                *monatsnamen
            ])
            
            for r in balance_rows:
                emp_id, name, dept, anspruch_raw, verbraucht, resturlaub_raw = r[0], r[1], r[2], float(r[3] or 0), float(r[4] or 0), float(r[5] or 0)
                anspruch = round(anspruch_raw, 1)
                resturlaub = max(0, round(resturlaub_raw, 1))
                extra = emp_extra.get(emp_id, {})
                carried = extra.get('carried_over', 0)
                personal_nr = extra.get('personal_nr', '') or ''
                dept_clean = (dept or '').replace('⚠️ ', '').strip()
                months = monthly.get(emp_id, {})
                writer.writerow([
                    personal_nr, name or '', dept_clean,
                    round(anspruch, 1), round(carried, 1), round(anspruch, 1),
                    round(verbraucht, 1), round(resturlaub, 1),
                    *[round(months.get(m, 0), 1) for m in range(1, 13)]
                ])
            
            output.seek(0)
            return Response(
                output.getvalue().encode('utf-8-sig'),
                mimetype='text/csv; charset=utf-8',
                headers={'Content-Disposition': f'attachment; filename=Jahresrueckstellung_Urlaub_{year}.csv'}
            )
    
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


# ============================================================================
# TAG 198: Urlaubssperren Management
# ============================================================================

@vacation_admin_api.route('/blocks', methods=['GET'])
@login_required
def get_blocks():
    """GET /api/vacation/admin/blocks?year=2026&department=Service"""
    if not can_manage_vacation_blocks():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        department = request.args.get('department')
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT id, department_name, block_date, reason, created_by, created_at, employee_ids
                FROM vacation_blocks
                WHERE EXTRACT(YEAR FROM block_date) = %s
            """
            params = [year]
            
            if department:
                query += " AND department_name = %s"
                params.append(department)
            
            query += " ORDER BY block_date, department_name"
            
            cursor.execute(query, params)
            blocks = []
            for row in cursor.fetchall():
                emp_ids = row[6] if len(row) > 6 and row[6] else None
                if emp_ids and isinstance(emp_ids, str):
                    emp_ids = [int(x.strip()) for x in emp_ids.split(',') if x.strip().isdigit()]
                elif not emp_ids:
                    emp_ids = None
                blocks.append({
                    'id': row[0],
                    'department': row[1] or '',
                    'date': row[2].isoformat() if hasattr(row[2], 'isoformat') else str(row[2]),
                    'reason': row[3],
                    'created_by': row[4],
                    'created_at': row[5].isoformat() if hasattr(row[5], 'isoformat') else str(row[5]),
                    'employee_ids': emp_ids
                })
        
        return jsonify({'success': True, 'blocks': blocks})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@vacation_admin_api.route('/blocks', methods=['POST'])
@login_required
def create_block():
    """
    POST /api/vacation/admin/blocks - Neue Sperre(n) erstellen
    TAG 213: Unterstützt jetzt mehrere Daten auf einmal (dates array)
    Optional: employee_ids statt department für spezifische Mitarbeiter.
    """
    if not can_manage_vacation_blocks():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        data = request.get_json()
        department = data.get('department') or (None if data.get('employee_ids') else None)
        employee_ids_raw = data.get('employee_ids', [])  # Optional: [1, 2, 3] für spezifische MA
        dates = data.get('dates', [])  # TAG 213: Array von Daten
        date_str = data.get('date')  # Fallback: Einzelnes Datum
        reason = data.get('reason', '')
        created_by = getattr(current_user, 'username', 'admin')
        
        # TAG 213: Konvertiere einzelnes Datum zu Array
        if date_str and not dates:
            dates = [date_str]
        
        # Entweder Abteilung ODER spezifische Mitarbeiter
        use_employees = bool(employee_ids_raw and len(employee_ids_raw) > 0)
        if use_employees:
            department = None
            employee_ids_str = ','.join(str(int(x)) for x in employee_ids_raw)
        else:
            employee_ids_str = None
            if not department:
                return jsonify({'success': False, 'error': 'Bitte Abteilung wählen oder spezifische Mitarbeiter auswählen.'}), 400
        if not dates:
            return jsonify({'success': False, 'error': 'Mindestens ein Datum erforderlich.'}), 400
        
        created_count = 0
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            for date_str in dates:
                try:
                    if use_employees:
                        cursor.execute("""
                            INSERT INTO vacation_blocks (department_name, block_date, reason, created_by, employee_ids)
                            VALUES (NULL, %s, %s, %s, %s)
                        """, (date_str, reason, created_by, employee_ids_str))
                    else:
                        cursor.execute("""
                            INSERT INTO vacation_blocks (department_name, block_date, reason, created_by, employee_ids)
                            VALUES (%s, %s, %s, %s, NULL)
                            ON CONFLICT(department_name, block_date) DO UPDATE SET
                                reason = excluded.reason,
                                created_by = excluded.created_by
                        """, (department, date_str, reason, created_by))
                    created_count += 1
                except Exception as e:
                    print(f"Fehler beim Erstellen der Sperre für {date_str}: {e}")
                    continue
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'{created_count} Sperre(n) erstellt',
            'created': created_count
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_admin_api.route('/blocks/<int:block_id>', methods=['DELETE'])
@login_required
def delete_block(block_id):
    """DELETE /api/vacation/admin/blocks/<id> - Sperre löschen (Admin/Genehmiger)."""
    if not can_manage_vacation_blocks():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vacation_blocks WHERE id = %s", (block_id,))
            conn.commit()
        
        return jsonify({'success': True, 'message': 'Sperre gelöscht'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# TAG 198: Freie Tage Management
# ============================================================================

@vacation_admin_api.route('/free-days', methods=['GET'])
@login_required
def get_free_days():
    """GET /api/vacation/admin/free-days?year=2026"""
    if not is_vacation_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, free_date, description, affects_vacation_entitlement, created_by, created_at
                FROM free_days
                WHERE EXTRACT(YEAR FROM free_date) = %s
                ORDER BY free_date
            """, (year,))
            
            free_days_list = []
            for row in cursor.fetchall():
                free_days_list.append({
                    'id': row[0],
                    'date': row[1].isoformat() if hasattr(row[1], 'isoformat') else str(row[1]),
                    'description': row[2],
                    'affects_vacation_entitlement': row[3],
                    'created_by': row[4],
                    'created_at': row[5].isoformat() if hasattr(row[5], 'isoformat') else str(row[5])
                })
        
        return jsonify({'success': True, 'free_days': free_days_list})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@vacation_admin_api.route('/free-days', methods=['POST'])
@login_required
def create_free_day():
    """POST /api/vacation/admin/free-days - Neuen freien Tag erstellen"""
    if not is_vacation_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        data = request.get_json()
        date_str = data.get('date')
        description = data.get('description', '')
        affects_entitlement = data.get('affects_vacation_entitlement', True)
        created_by = getattr(current_user, 'username', 'admin')
        
        if not date_str:
            return jsonify({'success': False, 'error': 'date erforderlich'}), 400
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO free_days (free_date, description, affects_vacation_entitlement, created_by)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT(free_date) DO UPDATE SET
                    description = excluded.description,
                    affects_vacation_entitlement = excluded.affects_vacation_entitlement
            """, (date_str, description, affects_entitlement, created_by))
            
            conn.commit()
        
        return jsonify({'success': True, 'message': 'Freier Tag erstellt'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@vacation_admin_api.route('/free-days/<int:free_day_id>', methods=['DELETE'])
@login_required
def delete_free_day(free_day_id):
    """DELETE /api/vacation/admin/free-days/<id> - Freien Tag löschen"""
    if not is_vacation_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM free_days WHERE id = %s", (free_day_id,))
            conn.commit()
        
        return jsonify({'success': True, 'message': 'Freier Tag gelöscht'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@vacation_admin_api.route('/export', methods=['GET'])
@login_required
def export_data():
    """GET /api/vacation/admin/export - CSV Export"""
    if not is_vacation_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        year = request.args.get('year', 2025, type=int)
        
        # Hole Daten von der employees-API
        response = get_employees()
        data = response.get_json()
        
        if not data.get('success'):
            return jsonify({'success': False, 'error': 'Daten konnten nicht geladen werden'}), 500
        
        output = io.StringIO()
        # TAG 198: UTF-8 BOM für Excel-Kompatibilität
        output.write('\ufeff')  # UTF-8 BOM
        # TAG 198: QUOTE_MINIMAL - nur wenn nötig, Zahlen ohne Anführungszeichen
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL, lineterminator='\r\n')
        
        # Header
        writer.writerow(['Name', 'Standort', 'Gruppe', 'Anspruch', 'Übertrag', 'Urlaub', 'ZA', 'Krank', 'Sonstige', 'Verfügbar'])
        
        for emp in data['employees']:
            # TAG 198: Konvertiere alle Werte explizit - Zahlen als float, Strings als String
            name = str(emp.get('name', '') or '').strip()
            standort = str(emp.get('standort', '') or '').strip()
            gruppe = str(emp.get('grp_code', '') or '-').strip()
            
            # Zahlen explizit als float konvertieren und runden
            # TAG 198: Punkt als Dezimaltrennzeichen (Standard für CSV mit Semikolon als Feldtrennzeichen)
            anspruch = round(float(emp.get('anspruch', 0) or 0), 1)
            uebertrag = round(float(emp.get('uebertrag', 0) or 0), 1)
            urlaub = round(float(emp.get('urlaub', 0) or 0), 1)
            zeitausgleich = round(float(emp.get('zeitausgleich', 0) or 0), 1)
            krank = round(float(emp.get('krank', 0) or 0), 1)
            sonstige = round(float(emp.get('sonstige', 0) or 0), 1)
            verfuegbar = round(float(emp.get('verfuegbar', 0) or 0), 1)
            
            writer.writerow([
                name,
                standort,
                gruppe,
                anspruch,
                uebertrag,
                urlaub,
                zeitausgleich,
                krank,
                sonstige,
                verfuegbar
            ])
        
        output.seek(0)
        csv_content = output.getvalue()
        
        return Response(
            csv_content.encode('utf-8-sig'),  # UTF-8 mit BOM für Excel
            mimetype='text/csv; charset=utf-8',
            headers={'Content-Disposition': f'attachment; filename=urlaubsuebersicht_{year}.csv'}
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
