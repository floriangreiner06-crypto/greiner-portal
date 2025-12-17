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

vacation_admin_api = Blueprint('vacation_admin_api', __name__, url_prefix='/api/vacation/admin')

def is_vacation_admin():
    """Prüft ob User in GRP_Urlaub_Admin ist"""
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
                WHERE e.aktiv = 1
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
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(employee_id, year) DO UPDATE SET
                    total_days = excluded.total_days,
                    carried_over = excluded.carried_over,
                    added_manually = excluded.added_manually,
                    updated_at = CURRENT_TIMESTAMP
            """, (employee_id, year, anspruch, uebertrag, korrektur))

            cursor.execute("""
                UPDATE employees
                SET vacation_days_total = ?, vacation_entitlement = ?
                WHERE id = ?
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
                    WHERE employee_id = ? AND year = ?
                """, (employee_id, year))
                current = cursor.fetchone()

                anspruch = change.get('anspruch', current['total_days'] if current else 27.0)
                uebertrag = change.get('uebertrag', current['carried_over'] if current else 0)
                korrektur = change.get('korrektur', current['added_manually'] if current else 0)

                cursor.execute("""
                    INSERT INTO vacation_entitlements (employee_id, year, total_days, carried_over, added_manually, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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
        writer = csv.writer(output, delimiter=';')
        
        # Header
        writer.writerow(['Name', 'Standort', 'Gruppe', 'Anspruch', 'Übertrag', 'Urlaub', 'ZA', 'Krank', 'Sonstige', 'Verfügbar'])
        
        for emp in data['employees']:
            writer.writerow([
                emp['name'],
                emp['standort'],
                emp['grp_code'] or '-',
                emp['anspruch'],
                emp['uebertrag'],
                emp['urlaub'],
                emp['zeitausgleich'],
                emp['krank'],
                emp['sonstige'],
                emp['verfuegbar']
            ])
        
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=urlaubsuebersicht_{year}.csv'}
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
