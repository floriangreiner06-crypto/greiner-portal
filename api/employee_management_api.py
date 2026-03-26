#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMPLOYEE MANAGEMENT API - Umfassende Mitarbeiterverwaltung
TAG 213: Nach Muster "Digitale Personalakte"
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from datetime import datetime
import json

from api.db_utils import db_session, locosoft_session, row_to_dict, rows_to_list

employee_management_api = Blueprint('employee_management_api', __name__, url_prefix='/api/employee-management')


def is_admin():
    """Prüft ob User Admin-Rechte hat"""
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
    
    # Fallback: Hardcoded Admin-Liste
    allowed_users = ['florian.greiner', 'vanessa.groll', 'christian.aichinger', 'sandra.brendel']
    username = getattr(current_user, 'username', '') or ''
    username_clean = username.lower().split('@')[0]
    
    return username_clean in allowed_users


# ============================================================================
# MITARBEITER-ÜBERSICHT (Liste)
# ============================================================================

@employee_management_api.route('/employees', methods=['GET'])
@login_required
def get_employees_list():
    """
    GET /api/employee-management/employees
    
    Gibt Liste aller Mitarbeiter zurück (für Sidebar)
    """
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    e.id,
                    e.first_name,
                    e.last_name,
                    e.department_name,
                    e.location,
                    e.aktiv,
                    e.locosoft_id,
                    e.entry_date,
                    e.exit_date,
                    e.email
                FROM employees e
                ORDER BY e.aktiv DESC, e.department_name, e.last_name, e.first_name
            """)
            
            employees = []
            for row in cursor.fetchall():
                row_dict = row_to_dict(row)
                employees.append({
                    'id': row_dict['id'],
                    'name': f"{row_dict['first_name']} {row_dict['last_name']}",
                    'first_name': row_dict['first_name'],
                    'last_name': row_dict['last_name'],
                    'department': row_dict['department_name'],
                    'location': row_dict['location'],
                    'active': bool(row_dict['aktiv']),
                    'locosoft_id': row_dict['locosoft_id'],
                    'entry_date': row_dict['entry_date'].isoformat() if row_dict['entry_date'] else None,
                    'exit_date': row_dict['exit_date'].isoformat() if row_dict['exit_date'] else None,
                    'email': row_dict['email']
                })
            
            return jsonify({
                'success': True,
                'employees': employees,
                'count': len(employees)
            })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================================
# MITARBEITER-DETAIL (Einzelner Mitarbeiter)
# ============================================================================

@employee_management_api.route('/employee/<int:employee_id>', methods=['GET'])
@login_required
def get_employee_detail(employee_id):
    """
    GET /api/employee-management/employee/<id>
    
    Gibt alle Daten eines Mitarbeiters zurück (inkl. Arbeitszeitmodelle, Ausnahmen, etc.)
    """
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            
            # 1. Grunddaten aus employees + Mapping (Locosoft-ID für Filter „nur eigene“)
            cursor.execute("""
                SELECT 
                    e.*,
                    lem.ldap_username,
                    lem.locosoft_id AS mapping_locosoft_id
                FROM employees e
                LEFT JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
                WHERE e.id = %s
            """, (employee_id,))
            
            emp_row = cursor.fetchone()
            if not emp_row:
                return jsonify({'success': False, 'error': 'Mitarbeiter nicht gefunden'}), 404
            
            emp_dict = row_to_dict(emp_row)
            
            # 2. Arbeitszeitmodelle
            cursor.execute("""
                SELECT * FROM employee_working_time_models
                WHERE employee_id = %s
                ORDER BY start_date DESC
            """, (employee_id,))
            working_time_models = rows_to_list(cursor.fetchall())
            
            # 3. Ausnahmen
            cursor.execute("""
                SELECT * FROM employee_working_time_exceptions
                WHERE employee_id = %s
                ORDER BY from_date DESC
            """, (employee_id,))
            exceptions = rows_to_list(cursor.fetchall())
            
            # 4. Urlaubsplaner-Einstellungen
            cursor.execute("""
                SELECT * FROM employee_vacation_settings
                WHERE employee_id = %s
            """, (employee_id,))
            vacation_settings_row = cursor.fetchone()
            vacation_settings = row_to_dict(vacation_settings_row) if vacation_settings_row else None
            
            # 5. Zeiten ohne Urlaubsanspruch
            cursor.execute("""
                SELECT * FROM employee_periods_without_vacation
                WHERE employee_id = %s
                ORDER BY from_date DESC
            """, (employee_id,))
            periods_no_vacation = rows_to_list(cursor.fetchall())
            
            # 6. Terminkonten
            cursor.execute("""
                SELECT * FROM employee_appointment_accounts
                WHERE employee_id = %s
                ORDER BY appointment_type
            """, (employee_id,))
            appointment_accounts = rows_to_list(cursor.fetchall())
            
            # 7. Urlaubsansprüche (alle Jahre)
            cursor.execute("""
                SELECT * FROM vacation_entitlements
                WHERE employee_id = %s
                ORDER BY year DESC
            """, (employee_id,))
            vacation_entitlements = rows_to_list(cursor.fetchall())
            
            # Datum-Objekte zu Strings konvertieren
            def date_to_str(d):
                if d is None:
                    return None
                if isinstance(d, datetime):
                    return d.date().isoformat()
                if hasattr(d, 'isoformat'):
                    return d.isoformat()
                return str(d)
            
            def datetime_to_str(dt):
                if dt is None:
                    return None
                if isinstance(dt, datetime):
                    return dt.isoformat()
                return str(dt)
            
            # Grunddaten aufbereiten
            employee_data = {
                'id': emp_dict['id'],
                'first_name': emp_dict['first_name'],
                'last_name': emp_dict['last_name'],
                'email': emp_dict['email'],
                'birthday': date_to_str(emp_dict.get('birthday')),
                'entry_date': date_to_str(emp_dict.get('entry_date')),
                'exit_date': date_to_str(emp_dict.get('exit_date')),
                'department_id': emp_dict.get('department_id'),
                'department_name': emp_dict.get('department_name'),
                'location': emp_dict.get('location'),
                'locosoft_id': emp_dict.get('locosoft_id'),
                'mapping_locosoft_id': emp_dict.get('mapping_locosoft_id'),  # für Filter Auftragseingang/Leistungsübersicht
                'personal_nr': emp_dict.get('personal_nr'),
                'aktiv': bool(emp_dict.get('aktiv', True)),
                'ldap_username': emp_dict.get('ldap_username'),
                
                # Neue Felder
                'gender': emp_dict.get('gender'),
                'title': emp_dict.get('title'),
                'salutation': emp_dict.get('salutation'),
                
                # Kontaktdaten (privat)
                'private_street': emp_dict.get('private_street'),
                'private_city': emp_dict.get('private_city'),
                'private_postal_code': emp_dict.get('private_postal_code'),
                'private_country': emp_dict.get('private_country', 'Deutschland'),
                'private_phone': emp_dict.get('private_phone'),
                'private_mobile': emp_dict.get('private_mobile'),
                'private_fax': emp_dict.get('private_fax'),
                'private_email': emp_dict.get('private_email'),
                
                # Kontaktdaten (Firma)
                'company_phone': emp_dict.get('company_phone'),
                'company_mobile': emp_dict.get('company_mobile'),
                'company_fax': emp_dict.get('company_fax'),
                'company_email': emp_dict.get('company_email'),
                'personal_nr_1': emp_dict.get('personal_nr_1'),
                'personal_nr_2': emp_dict.get('personal_nr_2'),
                
                # Vertragsdaten
                'company': emp_dict.get('company'),
                'hired_as': emp_dict.get('hired_as'),
                'activity': emp_dict.get('activity'),
                'probation_end': date_to_str(emp_dict.get('probation_end')),
                'limited_until': date_to_str(emp_dict.get('limited_until')),
                'notice_period_employer': emp_dict.get('notice_period_employer'),
                'notice_period_employee': emp_dict.get('notice_period_employee'),
                'country': emp_dict.get('country', 'Deutschland'),
                'federal_state': emp_dict.get('federal_state'),
                'deactivate_after_exit': bool(emp_dict.get('deactivate_after_exit', False)),
                'provision_aktiv': bool(emp_dict.get('provision_aktiv', True)),
                
                # Zugehörige Daten
                'working_time_models': working_time_models,
                'exceptions': exceptions,
                'vacation_settings': vacation_settings,
                'periods_without_vacation': periods_no_vacation,
                'appointment_accounts': appointment_accounts,
                'vacation_entitlements': vacation_entitlements
            }
            
            return jsonify({
                'success': True,
                'employee': employee_data
            })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================================
# MITARBEITER AKTUALISIEREN
# ============================================================================

@employee_management_api.route('/employee/<int:employee_id>', methods=['PUT'])
@login_required
def update_employee(employee_id):
    """
    PUT /api/employee-management/employee/<id>
    
    Aktualisiert Mitarbeiterdaten
    """
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        data = request.get_json()
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Prüfe ob Mitarbeiter existiert
            cursor.execute("SELECT id FROM employees WHERE id = %s", (employee_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Mitarbeiter nicht gefunden'}), 404
            
            # Update employees Tabelle
            update_fields = []
            update_values = []
            
            # Grunddaten
            if 'first_name' in data:
                update_fields.append('first_name = %s')
                update_values.append(data['first_name'])
            if 'last_name' in data:
                update_fields.append('last_name = %s')
                update_values.append(data['last_name'])
            if 'email' in data:
                update_fields.append('email = %s')
                update_values.append(data['email'])
            if 'birthday' in data:
                update_fields.append('birthday = %s')
                update_values.append(data['birthday'] if data['birthday'] else None)
            if 'entry_date' in data:
                update_fields.append('entry_date = %s')
                update_values.append(data['entry_date'] if data['entry_date'] else None)
            if 'exit_date' in data:
                update_fields.append('exit_date = %s')
                update_values.append(data['exit_date'] if data['exit_date'] else None)
            if 'department_name' in data:
                update_fields.append('department_name = %s')
                update_values.append(data['department_name'])
            if 'location' in data:
                update_fields.append('location = %s')
                update_values.append(data['location'])
            if 'personal_nr' in data:
                update_fields.append('personal_nr = %s')
                update_values.append(data['personal_nr'])
            if 'aktiv' in data:
                update_fields.append('aktiv = %s')
                update_values.append(data['aktiv'])
            
            # Neue Felder
            if 'gender' in data:
                update_fields.append('gender = %s')
                update_values.append(data['gender'])
            if 'title' in data:
                update_fields.append('title = %s')
                update_values.append(data['title'])
            if 'salutation' in data:
                update_fields.append('salutation = %s')
                update_values.append(data['salutation'])
            
            # Kontaktdaten (privat)
            if 'private_street' in data:
                update_fields.append('private_street = %s')
                update_values.append(data['private_street'])
            if 'private_city' in data:
                update_fields.append('private_city = %s')
                update_values.append(data['private_city'])
            if 'private_postal_code' in data:
                update_fields.append('private_postal_code = %s')
                update_values.append(data['private_postal_code'])
            if 'private_country' in data:
                update_fields.append('private_country = %s')
                update_values.append(data['private_country'])
            if 'private_phone' in data:
                update_fields.append('private_phone = %s')
                update_values.append(data['private_phone'])
            if 'private_mobile' in data:
                update_fields.append('private_mobile = %s')
                update_values.append(data['private_mobile'])
            if 'private_fax' in data:
                update_fields.append('private_fax = %s')
                update_values.append(data['private_fax'])
            if 'private_email' in data:
                update_fields.append('private_email = %s')
                update_values.append(data['private_email'])
            
            # Kontaktdaten (Firma)
            if 'company_phone' in data:
                update_fields.append('company_phone = %s')
                update_values.append(data['company_phone'])
            if 'company_mobile' in data:
                update_fields.append('company_mobile = %s')
                update_values.append(data['company_mobile'])
            if 'company_fax' in data:
                update_fields.append('company_fax = %s')
                update_values.append(data['company_fax'])
            if 'company_email' in data:
                update_fields.append('company_email = %s')
                update_values.append(data['company_email'])
            if 'personal_nr_1' in data:
                update_fields.append('personal_nr_1 = %s')
                update_values.append(data['personal_nr_1'])
            if 'personal_nr_2' in data:
                update_fields.append('personal_nr_2 = %s')
                update_values.append(data['personal_nr_2'])
            
            # Vertragsdaten
            if 'company' in data:
                update_fields.append('company = %s')
                update_values.append(data['company'])
            if 'hired_as' in data:
                update_fields.append('hired_as = %s')
                update_values.append(data['hired_as'])
            if 'activity' in data:
                update_fields.append('activity = %s')
                update_values.append(data['activity'])
            if 'probation_end' in data:
                update_fields.append('probation_end = %s')
                update_values.append(data['probation_end'] if data['probation_end'] else None)
            if 'limited_until' in data:
                update_fields.append('limited_until = %s')
                update_values.append(data['limited_until'] if data['limited_until'] else None)
            if 'notice_period_employer' in data:
                update_fields.append('notice_period_employer = %s')
                update_values.append(data['notice_period_employer'])
            if 'notice_period_employee' in data:
                update_fields.append('notice_period_employee = %s')
                update_values.append(data['notice_period_employee'])
            if 'country' in data:
                update_fields.append('country = %s')
                update_values.append(data['country'])
            if 'federal_state' in data:
                update_fields.append('federal_state = %s')
                update_values.append(data['federal_state'])
            if 'deactivate_after_exit' in data:
                update_fields.append('deactivate_after_exit = %s')
                update_values.append(data['deactivate_after_exit'])
                # Mail-Anfrage: Haken soll MA im Urlaubsplaner ausblenden → aktiv = False/True
                update_fields.append('aktiv = %s')
                update_values.append(not data['deactivate_after_exit'])  # True = aktiv, False = ausgeblendet
            if 'provision_aktiv' in data:
                update_fields.append('provision_aktiv = %s')
                update_values.append(bool(data['provision_aktiv']))
            
            if update_fields:
                update_values.append(employee_id)
                query = f"UPDATE employees SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(query, update_values)
                conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Mitarbeiter aktualisiert'
            })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================================
# ARBEITSZEITMODELLE
# ============================================================================

@employee_management_api.route('/employee/<int:employee_id>/working-time-models', methods=['GET'])
@login_required
def get_working_time_models(employee_id):
    """GET /api/employee-management/employee/<id>/working-time-models"""
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM employee_working_time_models
                WHERE employee_id = %s
                ORDER BY start_date DESC
            """, (employee_id,))
            models = rows_to_list(cursor.fetchall())
            return jsonify({'success': True, 'models': models})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@employee_management_api.route('/employee/<int:employee_id>/working-time-models', methods=['POST'])
@login_required
def create_working_time_model(employee_id):
    """POST /api/employee-management/employee/<id>/working-time-models"""
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        data = request.get_json()
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO employee_working_time_models 
                (employee_id, start_date, end_date, hours_per_week, working_days_per_week, 
                 weekly_hours, hourly_wage, gross_wage, description, work_weekdays, half_weekdays)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                employee_id,
                data.get('start_date'),
                data.get('end_date'),
                data.get('hours_per_week'),
                data.get('working_days_per_week', 5),
                data.get('weekly_hours'),
                data.get('hourly_wage'),
                data.get('gross_wage'),
                data.get('description'),
                data.get('work_weekdays'),
                data.get('half_weekdays')
            ))
            model_id = cursor.fetchone()[0]
            conn.commit()
            return jsonify({'success': True, 'id': model_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@employee_management_api.route('/employee/<int:employee_id>/working-time-models/<int:model_id>', methods=['PUT'])
@login_required
def update_working_time_model(employee_id, model_id):
    """PUT /api/employee-management/employee/<id>/working-time-models/<model_id>"""
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        data = request.get_json()
        with db_session() as conn:
            cursor = conn.cursor()
            update_fields = []
            update_values = []
            
            for field in ['start_date', 'end_date', 'hours_per_week', 'working_days_per_week',
                         'weekly_hours', 'hourly_wage', 'gross_wage', 'description',
                         'work_weekdays', 'half_weekdays']:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    update_values.append(data[field])
            
            if update_fields:
                update_values.extend([employee_id, model_id])
                query = f"""
                    UPDATE employee_working_time_models 
                    SET {', '.join(update_fields)}
                    WHERE employee_id = %s AND id = %s
                """
                cursor.execute(query, update_values)
                conn.commit()
            
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@employee_management_api.route('/employee/<int:employee_id>/working-time-models/<int:model_id>', methods=['DELETE'])
@login_required
def delete_working_time_model(employee_id, model_id):
    """DELETE /api/employee-management/employee/<id>/working-time-models/<model_id>"""
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM employee_working_time_models
                WHERE employee_id = %s AND id = %s
            """, (employee_id, model_id))
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# AUSNAHMEN
# ============================================================================

@employee_management_api.route('/employee/<int:employee_id>/exceptions', methods=['GET'])
@login_required
def get_exceptions(employee_id):
    """GET /api/employee-management/employee/<id>/exceptions"""
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM employee_working_time_exceptions
                WHERE employee_id = %s
                ORDER BY from_date DESC
            """, (employee_id,))
            exceptions = rows_to_list(cursor.fetchall())
            return jsonify({'success': True, 'exceptions': exceptions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@employee_management_api.route('/employee/<int:employee_id>/exceptions', methods=['POST'])
@login_required
def create_exception(employee_id):
    """POST /api/employee-management/employee/<id>/exceptions"""
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        data = request.get_json()
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO employee_working_time_exceptions
                (employee_id, from_date, to_date, exception_type, description, affects_vacation_entitlement)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                employee_id,
                data.get('from_date'),
                data.get('to_date'),
                data.get('exception_type'),
                data.get('description'),
                data.get('affects_vacation_entitlement', False)
            ))
            exception_id = cursor.fetchone()[0]
            conn.commit()
            return jsonify({'success': True, 'id': exception_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@employee_management_api.route('/employee/<int:employee_id>/exceptions/<int:exception_id>', methods=['DELETE'])
@login_required
def delete_exception(employee_id, exception_id):
    """DELETE /api/employee-management/employee/<id>/exceptions/<exception_id>"""
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM employee_working_time_exceptions
                WHERE employee_id = %s AND id = %s
            """, (employee_id, exception_id))
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# URLAUBSPLANER-EINSTELLUNGEN
# ============================================================================

@employee_management_api.route('/employee/<int:employee_id>/vacation-settings', methods=['GET'])
@login_required
def get_vacation_settings(employee_id):
    """GET /api/employee-management/employee/<id>/vacation-settings"""
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM employee_vacation_settings
                WHERE employee_id = %s
            """, (employee_id,))
            row = cursor.fetchone()
            if row:
                settings = row_to_dict(row)
                return jsonify({'success': True, 'settings': settings})
            else:
                # Erstelle Default-Einstellungen
                cursor.execute("""
                    INSERT INTO employee_vacation_settings (employee_id)
                    VALUES (%s)
                    RETURNING *
                """, (employee_id,))
                settings = row_to_dict(cursor.fetchone())
                conn.commit()
                return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@employee_management_api.route('/employee/<int:employee_id>/vacation-settings', methods=['PUT'])
@login_required
def update_vacation_settings(employee_id):
    """PUT /api/employee-management/employee/<id>/vacation-settings"""
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        data = request.get_json()
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Prüfe ob Einstellungen existieren
            cursor.execute("SELECT id FROM employee_vacation_settings WHERE employee_id = %s", (employee_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Update
                update_fields = []
                update_values = []
                for field in ['show_in_planner', 'show_birthday', 'vacation_expires', 'max_carry_over',
                             'weekend_limit', 'max_vacation_length', 'max_vacation_exit', 'calculation_method',
                             'valuation_lock', 'entry_from', 'entry_until']:
                    if field in data:
                        update_fields.append(f"{field} = %s")
                        update_values.append(data[field])
                
                if update_fields:
                    update_values.append(employee_id)
                    query = f"""
                        UPDATE employee_vacation_settings
                        SET {', '.join(update_fields)}
                        WHERE employee_id = %s
                    """
                    cursor.execute(query, update_values)
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO employee_vacation_settings
                    (employee_id, show_in_planner, show_birthday, vacation_expires, max_carry_over,
                     weekend_limit, max_vacation_length, max_vacation_exit, calculation_method,
                     valuation_lock, entry_from, entry_until)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    employee_id,
                    data.get('show_in_planner', True),
                    data.get('show_birthday', True),
                    data.get('vacation_expires', False),
                    data.get('max_carry_over', 999.0),
                    data.get('weekend_limit', 0),
                    data.get('max_vacation_length', 14),
                    data.get('max_vacation_exit', 0.0),
                    data.get('calculation_method', 'standard'),
                    data.get('valuation_lock'),
                    data.get('entry_from'),
                    data.get('entry_until')
                ))
            
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ZEITEN OHNE URLAUBSANSPRUCH
# ============================================================================

@employee_management_api.route('/employee/<int:employee_id>/periods-without-vacation', methods=['GET'])
@login_required
def get_periods_without_vacation(employee_id):
    """GET /api/employee-management/employee/<id>/periods-without-vacation"""
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM employee_periods_without_vacation
                WHERE employee_id = %s
                ORDER BY from_date DESC
            """, (employee_id,))
            periods = rows_to_list(cursor.fetchall())
            return jsonify({'success': True, 'periods': periods})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@employee_management_api.route('/employee/<int:employee_id>/periods-without-vacation', methods=['POST'])
@login_required
def create_period_without_vacation(employee_id):
    """POST /api/employee-management/employee/<id>/periods-without-vacation"""
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        data = request.get_json()
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO employee_periods_without_vacation
                (employee_id, from_date, to_date, period_type, description)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                employee_id,
                data.get('from_date'),
                data.get('to_date'),
                data.get('period_type'),
                data.get('description')
            ))
            period_id = cursor.fetchone()[0]
            conn.commit()
            return jsonify({'success': True, 'id': period_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@employee_management_api.route('/employee/<int:employee_id>/periods-without-vacation/<int:period_id>', methods=['DELETE'])
@login_required
def delete_period_without_vacation(employee_id, period_id):
    """DELETE /api/employee-management/employee/<id>/periods-without-vacation/<period_id>"""
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM employee_periods_without_vacation
                WHERE employee_id = %s AND id = %s
            """, (employee_id, period_id))
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# SYNC-FUNKTIONEN (LDAP/Locosoft)
# ============================================================================

@employee_management_api.route('/employee/<int:employee_id>/sync-preview', methods=['GET'])
@login_required
def sync_preview_endpoint(employee_id):
    """
    GET /api/employee-management/employee/<id>/sync-preview
    
    Zeigt Vorschau der Sync-Änderungen ohne zu speichern
    """
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        overwrite = request.args.get('overwrite', 'false').lower() == 'true'
        
        from api.employee_sync_service import sync_preview
        result = sync_preview(employee_id, overwrite)
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@employee_management_api.route('/employee/<int:employee_id>/sync-from-ldap', methods=['POST'])
@login_required
def sync_from_ldap_endpoint(employee_id):
    """
    POST /api/employee-management/employee/<id>/sync-from-ldap
    
    Synchronisiert Daten aus LDAP
    """
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        data = request.get_json() or {}
        overwrite = data.get('overwrite', False)
        
        # Hole ldap_username
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ldap_username FROM ldap_employee_mapping
                WHERE employee_id = %s
            """, (employee_id,))
            mapping_row = cursor.fetchone()
            
            if not mapping_row or not mapping_row[0]:
                return jsonify({
                    'success': False,
                    'error': 'Kein LDAP-Username für diesen Mitarbeiter gefunden'
                }), 400
            
            ldap_username = mapping_row[0]
        
        from api.employee_sync_service import sync_from_ldap
        result = sync_from_ldap(employee_id, ldap_username, overwrite)
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@employee_management_api.route('/employee/<int:employee_id>/sync-from-locosoft', methods=['POST'])
@login_required
def sync_from_locosoft_endpoint(employee_id):
    """
    POST /api/employee-management/employee/<id>/sync-from-locosoft
    
    Synchronisiert Daten aus Locosoft
    """
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        data = request.get_json() or {}
        overwrite = data.get('overwrite', False)
        
        # Hole locosoft_id
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT locosoft_id FROM ldap_employee_mapping
                WHERE employee_id = %s
            """, (employee_id,))
            mapping_row = cursor.fetchone()
            
            if not mapping_row or not mapping_row[0]:
                return jsonify({
                    'success': False,
                    'error': 'Keine Locosoft-ID für diesen Mitarbeiter gefunden'
                }), 400
            
            locosoft_id = mapping_row[0]
        
        from api.employee_sync_service import sync_from_locosoft
        result = sync_from_locosoft(employee_id, locosoft_id, overwrite)
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@employee_management_api.route('/employee/<int:employee_id>/sync-full', methods=['POST'])
@login_required
def sync_full_endpoint(employee_id):
    """
    POST /api/employee-management/employee/<id>/sync-full
    
    Vollständiger Sync aus beiden Quellen (LDAP + Locosoft)
    """
    if not is_admin():
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
    
    try:
        data = request.get_json() or {}
        overwrite = data.get('overwrite', False)
        
        from api.employee_sync_service import sync_full
        result = sync_full(employee_id, overwrite)
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
