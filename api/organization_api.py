#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
ORGANIZATION API - Organigramm & Vertretungsregeln
========================================
Version: 1.0 - TAG 113
Datum: 11.12.2025

Features:
- /api/organization/tree - Organigramm-Baum aus AD/DB
- /api/organization/departments - Abteilungen mit Mitarbeitern
- /api/organization/substitutes - Vertretungsregeln
- /api/organization/approval-chains - Genehmiger-Ketten
"""

from flask import Blueprint, request, jsonify, session
import sqlite3
from datetime import datetime, date
import json

organization_api = Blueprint('organization_api', __name__, url_prefix='/api/organization')

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'


def get_db():
    """Erstellt DB-Verbindung"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_current_user():
    """Holt aktuellen User aus Session"""
    user_id = session.get('_user_id')
    if not user_id:
        return None, None
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, ad_groups FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        groups = json.loads(row[1]) if row[1] else []
        is_admin = 'GRP_Urlaub_Admin' in groups
        return row[0], is_admin
    return None, False


# ============================================================================
# ORGANIGRAMM ENDPOINTS
# ============================================================================

@organization_api.route('/health', methods=['GET'])
def health_check():
    """Health Check"""
    return jsonify({
        'status': 'ok',
        'service': 'organization-api',
        'version': '1.0',
        'timestamp': datetime.now().isoformat()
    })


@organization_api.route('/tree', methods=['GET'])
def get_org_tree():
    """
    GET /api/organization/tree
    
    Gibt das komplette Organigramm als Baum-Struktur zurück.
    Basiert auf manager_id Beziehungen in employees.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Alle aktiven Mitarbeiter mit Manager-Info holen
        cursor.execute("""
            SELECT 
                e.id,
                e.first_name,
                e.last_name,
                e.email,
                e.department_name,
                e.manager_role,
                e.location,
                e.is_manager,
                e.supervisor_id,
                e.locosoft_id,
                lem.ldap_username
            FROM employees e
            LEFT JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
            WHERE e.aktiv = 1
            ORDER BY e.department_name, e.last_name
        """)
        
        employees = []
        for row in cursor.fetchall():
            employees.append({
                'id': row[0],
                'name': f"{row[1]} {row[2]}".strip(),
                'first_name': row[1],
                'last_name': row[2],
                'email': row[3],
                'department': row[4],
                'position': row[5],
                'location': row[6],
                'is_manager': bool(row[7]),
                'supervisor_id': row[8],
                'locosoft_id': row[9],
                'ldap_username': row[10],
                'children': []
            })
        
        conn.close()
        
        # Baum-Struktur aufbauen
        emp_dict = {e['id']: e for e in employees}
        roots = []
        
        for emp in employees:
            manager_id = emp['supervisor_id']
            if manager_id and manager_id in emp_dict:
                emp_dict[manager_id]['children'].append(emp)
            else:
                roots.append(emp)
        
        # Sortiere Kinder nach Name
        def sort_children(node):
            node['children'].sort(key=lambda x: x['name'])
            for child in node['children']:
                sort_children(child)
        
        for root in roots:
            sort_children(root)
        
        return jsonify({
            'success': True,
            'tree': roots,
            'total_employees': len(employees),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@organization_api.route('/departments', methods=['GET'])
def get_departments():
    """
    GET /api/organization/departments
    
    Gibt alle Abteilungen mit Mitarbeitern zurück.
    Gruppiert nach department_name.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Abteilungen mit Mitarbeiter-Anzahl
        cursor.execute("""
            SELECT 
                department_name,
                COUNT(*) as count,
                SUM(CASE WHEN is_manager = 1 THEN 1 ELSE 0 END) as manager_count,
                location
            FROM employees
            WHERE aktiv = 1 AND department_name IS NOT NULL
            GROUP BY department_name
            ORDER BY department_name
        """)
        
        departments = []
        for row in cursor.fetchall():
            dept_name = row[0]
            
            # Mitarbeiter dieser Abteilung holen
            cursor.execute("""
                SELECT 
                    e.id,
                    e.first_name || ' ' || e.last_name as name,
                    e.email,
                    e.manager_role,
                    e.is_manager,
                    e.locosoft_id,
                    lem.ldap_username
                FROM employees e
                LEFT JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
                WHERE e.aktiv = 1 AND e.department_name = ?
                ORDER BY e.is_manager DESC, e.last_name
            """, (dept_name,))
            
            members = []
            for emp in cursor.fetchall():
                members.append({
                    'id': emp[0],
                    'name': emp[1],
                    'email': emp[2],
                    'position': emp[3],
                    'is_manager': bool(emp[4]),
                    'locosoft_id': emp[5],
                    'ldap_username': emp[6]
                })
            
            departments.append({
                'name': dept_name,
                'count': row[1],
                'manager_count': row[2],
                'location': row[3],
                'members': members
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'departments': departments,
            'total': len(departments),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@organization_api.route('/employees', methods=['GET'])
def get_employees_list():
    """
    GET /api/organization/employees
    
    Gibt Liste aller aktiven Mitarbeiter zurück (für Dropdowns etc.)
    """
    try:
        department = request.args.get('department', None)
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                e.id,
                e.first_name || ' ' || e.last_name as name,
                e.email,
                e.department_name,
                e.manager_role,
                e.is_manager,
                e.locosoft_id,
                lem.ldap_username,
                e.location
            FROM employees e
            LEFT JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
            WHERE e.aktiv = 1
        """
        params = []
        
        if department:
            query += " AND e.department_name = ?"
            params.append(department)
        
        query += " ORDER BY e.last_name, e.first_name"
        
        cursor.execute(query, params)
        
        employees = []
        for row in cursor.fetchall():
            employees.append({
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'department': row[3],
                'position': row[4],
                'is_manager': bool(row[5]),
                'location': row[8] if len(row) > 8 else None,
                'locosoft_id': row[6],
                'ldap_username': row[7]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'employees': employees,
            'count': len(employees)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# VERTRETUNGSREGELN ENDPOINTS
# ============================================================================

@organization_api.route('/substitutes', methods=['GET'])
def get_substitutes():
    """
    GET /api/organization/substitutes
    
    Gibt alle Vertretungsregeln zurück.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Prüfe ob Tabelle existiert
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='substitution_rules'
        """)
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'success': True,
                'substitutes': [],
                'message': 'Tabelle substitution_rules existiert noch nicht'
            })
        
        cursor.execute("""
            SELECT 
                sr.id,
                sr.employee_id,
                e1.first_name || ' ' || e1.last_name as employee_name,
                e1.department_name,
                sr.substitute_id,
                e2.first_name || ' ' || e2.last_name as substitute_name,
                sr.priority,
                sr.valid_from,
                sr.valid_to,
                sr.created_at
            FROM substitution_rules sr
            JOIN employees e1 ON sr.employee_id = e1.id
            JOIN employees e2 ON sr.substitute_id = e2.id
            WHERE e1.aktiv = 1 AND e2.aktiv = 1
            ORDER BY e1.department_name, e1.last_name, sr.priority
        """)
        
        substitutes = []
        for row in cursor.fetchall():
            substitutes.append({
                'id': row[0],
                'employee_id': row[1],
                'employee_name': row[2],
                'department': row[3],
                'substitute_id': row[4],
                'substitute_name': row[5],
                'priority': row[6],
                'created_at': row[9]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'substitutes': substitutes,
            'count': len(substitutes)
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@organization_api.route('/substitutes', methods=['POST'])
def create_substitute():
    """
    POST /api/organization/substitutes
    
    Erstellt neue Vertretungsregel.
    
    Body:
    {
        "employee_id": 123,
        "substitute_id": 456,
        "priority": 1,
        "valid_from": "2025-01-01",
        "valid_to": "2025-12-31"
    }
    """
    try:
        username, is_admin = get_current_user()
        if not is_admin:
            return jsonify({'success': False, 'error': 'Admin-Berechtigung erforderlich'}), 403
        
        data = request.get_json()
        employee_id = data.get('employee_id')
        substitute_id = data.get('substitute_id')
        priority = data.get('priority', 1)
        valid_from = data.get('valid_from')
        valid_to = data.get('valid_to')
        
        if not employee_id or not substitute_id:
            return jsonify({'success': False, 'error': 'employee_id und substitute_id erforderlich'}), 400
        
        if employee_id == substitute_id:
            return jsonify({'success': False, 'error': 'Mitarbeiter kann nicht sein eigener Vertreter sein'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Tabelle erstellen falls nicht vorhanden
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS substitution_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                substitute_id INTEGER NOT NULL,
                priority INTEGER DEFAULT 1,
                valid_from DATE,
                valid_to DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (substitute_id) REFERENCES employees(id)
            )
        """)
        
        cursor.execute("""
            INSERT INTO substitution_rules (employee_id, substitute_id, priority, valid_from, valid_to, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (employee_id, substitute_id, priority, valid_from, valid_to, username))
        
        rule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'id': rule_id,
            'message': 'Vertretungsregel erstellt'
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@organization_api.route('/substitutes/<int:rule_id>', methods=['DELETE'])
def delete_substitute(rule_id):
    """
    DELETE /api/organization/substitutes/<id>
    
    Löscht eine Vertretungsregel.
    """
    try:
        username, is_admin = get_current_user()
        if not is_admin:
            return jsonify({'success': False, 'error': 'Admin-Berechtigung erforderlich'}), 403
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM substitution_rules WHERE id = ?", (rule_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Regel nicht gefunden'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Vertretungsregel gelöscht'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# GENEHMIGER-KETTEN (APPROVAL CHAINS)
# ============================================================================

@organization_api.route('/approval-rules', methods=['GET'])
def get_approval_rules():
    """Genehmigungsregeln abrufen"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                var.id,
                var.loco_grp_code,
                var.subsidiary,
                var.approver_employee_id,
                var.approver_ldap_username,
                var.priority,
                var.active,
                e.first_name || ' ' || e.last_name as approver_name
            FROM vacation_approval_rules var
            LEFT JOIN employees e ON var.approver_employee_id = e.id
            WHERE var.active = 1
            ORDER BY var.loco_grp_code, var.priority
        """)
        
        rules = []
        for row in cursor.fetchall():
            # subsidiary: 1=Deggendorf, 3=Landau
            standort = None
            if row[2] == 1:
                standort = 'Deggendorf'
            elif row[2] == 3:
                standort = 'Landau a.d. Isar'
            
            rules.append({
                'id': row[0],
                'grp_code': row[1],
                'subsidiary': row[2],
                'standort': standort,
                'approver_id': row[3],
                'approver_ldap': row[4],
                'priority': row[5],
                'active': row[6],
                'approver_name': row[7] or row[4]
            })
        
        conn.close()
        return jsonify({'success': True, 'rules': rules, 'count': len(rules)})
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})


@organization_api.route('/approval-rules', methods=['POST'])
def create_approval_rule():
    """
    POST /api/organization/approval-rules
    
    Erstellt neue Genehmigungsregel.
    
    Body:
    {
        "loco_grp_code": "VK",
        "subsidiary": "Deggendorf",
        "approver_ldap": "christian.aichinger",
        "priority": 1
    }
    """
    try:
        username, is_admin = get_current_user()
        if not is_admin:
            return jsonify({'success': False, 'error': 'Admin-Berechtigung erforderlich'}), 403
        
        data = request.get_json()
        grp_code = data.get('loco_grp_code')
        standort = data.get('subsidiary')
        approver_ldap = data.get('approver_ldap_username')
        priority = data.get('priority', 1)
        
        if not grp_code or not approver_ldap:
            return jsonify({'success': False, 'error': 'grp_code und approver_ldap erforderlich'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO vacation_approval_rules (grp_code, standort, approver_ldap, priority, aktiv, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
        """, (grp_code, standort, approver_ldap, priority, datetime.now().isoformat()))
        
        rule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'id': rule_id,
            'message': 'Genehmigungsregel erstellt'
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@organization_api.route('/approval-rules/<int:rule_id>', methods=['DELETE'])
def delete_approval_rule(rule_id):
    """
    DELETE /api/organization/approval-rules/<id>
    
    Deaktiviert eine Genehmigungsregel.
    """
    try:
        username, is_admin = get_current_user()
        if not is_admin:
            return jsonify({'success': False, 'error': 'Admin-Berechtigung erforderlich'}), 403
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Soft-Delete: aktiv = 0
        cursor.execute("UPDATE vacation_approval_rules SET aktiv = 0 WHERE id = ?", (rule_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Regel nicht gefunden'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Genehmigungsregel deaktiviert'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ABTEILUNGS-KAPAZITÄT (für 35% Regel)
# ============================================================================

@organization_api.route('/department-capacity', methods=['GET'])
def get_department_capacity():
    """
    GET /api/organization/department-capacity?department=Verkauf&date=2025-12-24
    
    Berechnet aktuelle Abwesenheits-Quote einer Abteilung.
    Für 35%-Vertretungsregel.
    """
    try:
        department = request.args.get('department')
        check_date = request.args.get('date', date.today().isoformat())
        
        if not department:
            return jsonify({'success': False, 'error': 'department Parameter erforderlich'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Gesamtzahl Mitarbeiter in Abteilung
        cursor.execute("""
            SELECT COUNT(*) FROM employees 
            WHERE department_name = ? AND aktiv = 1
        """, (department,))
        total = cursor.fetchone()[0]
        
        if total == 0:
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Keine Mitarbeiter in Abteilung {department}'
            }), 404
        
        # Abwesende an diesem Tag (approved bookings)
        cursor.execute("""
            SELECT COUNT(DISTINCT vb.employee_id)
            FROM vacation_bookings vb
            JOIN employees e ON vb.employee_id = e.id
            WHERE e.department_name = ?
              AND e.aktiv = 1
              AND vb.booking_date = ?
              AND vb.status = 'approved'
        """, (department, check_date))
        absent = cursor.fetchone()[0]
        
        # Geplante (pending) an diesem Tag
        cursor.execute("""
            SELECT COUNT(DISTINCT vb.employee_id)
            FROM vacation_bookings vb
            JOIN employees e ON vb.employee_id = e.id
            WHERE e.department_name = ?
              AND e.aktiv = 1
              AND vb.booking_date = ?
              AND vb.status = 'pending'
        """, (department, check_date))
        pending = cursor.fetchone()[0]
        
        conn.close()
        
        # Berechnung
        present = total - absent
        absence_rate = round((absent / total) * 100, 1) if total > 0 else 0
        potential_rate = round(((absent + pending) / total) * 100, 1) if total > 0 else 0
        
        # 35% Schwellwert
        max_absent = int(total * 0.35)
        available_slots = max(0, max_absent - absent)
        
        return jsonify({
            'success': True,
            'department': department,
            'date': check_date,
            'total_employees': total,
            'absent': absent,
            'pending': pending,
            'present': present,
            'absence_rate': absence_rate,
            'potential_rate': potential_rate,
            'max_absent_35_percent': max_absent,
            'available_slots': available_slots,
            'warning': absence_rate >= 35,
            'blocked': absence_rate >= 35
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@organization_api.route('/capacity-settings', methods=['GET'])
def get_capacity_settings():
    """
    GET /api/organization/capacity-settings
    
    Gibt Kapazitäts-Einstellungen pro Abteilung zurück.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Prüfe ob Tabelle existiert
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='department_capacity_settings'
        """)
        
        if not cursor.fetchone():
            # Default-Werte zurückgeben
            cursor.execute("""
                SELECT DISTINCT department_name FROM employees WHERE aktiv = 1 AND department_name IS NOT NULL
            """)
            departments = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return jsonify({
                'success': True,
                'settings': [{
                    'department': d,
                    'max_absence_percent': 35,
                    'is_default': True
                } for d in departments]
            })
        
        cursor.execute("""
            SELECT department_name, max_absence_percent, min_present, notes
            FROM department_capacity_settings
            ORDER BY department_name
        """)
        
        settings = []
        for row in cursor.fetchall():
            settings.append({
                'department': row[0],
                'max_absence_percent': row[1],
                'min_present': row[2],
                'notes': row[3],
                'is_default': False
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'settings': settings
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@organization_api.route('/capacity-settings', methods=['POST'])
def save_capacity_settings():
    """
    POST /api/organization/capacity-settings
    
    Speichert Kapazitäts-Einstellung für eine Abteilung.
    
    Body:
    {
        "department": "Verkauf",
        "max_absence_percent": 35,
        "min_present": 2,
        "notes": "Min. 2 Verkäufer müssen anwesend sein"
    }
    """
    try:
        username, is_admin = get_current_user()
        if not is_admin:
            return jsonify({'success': False, 'error': 'Admin-Berechtigung erforderlich'}), 403
        
        data = request.get_json()
        department = data.get('department')
        max_absence_percent = data.get('max_absence_percent', 35)
        min_present = data.get('min_present')
        notes = data.get('notes')
        
        if not department:
            return jsonify({'success': False, 'error': 'department erforderlich'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Tabelle erstellen falls nicht vorhanden
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS department_capacity_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_name TEXT UNIQUE NOT NULL,
                max_absence_percent INTEGER DEFAULT 35,
                min_present INTEGER,
                notes TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by TEXT
            )
        """)
        
        # Upsert
        cursor.execute("""
            INSERT INTO department_capacity_settings (department_name, max_absence_percent, min_present, notes, updated_by)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(department_name) DO UPDATE SET
                max_absence_percent = excluded.max_absence_percent,
                min_present = excluded.min_present,
                notes = excluded.notes,
                updated_at = CURRENT_TIMESTAMP,
                updated_by = excluded.updated_by
        """, (department, max_absence_percent, min_present, notes, username))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Einstellung für {department} gespeichert'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Export Blueprint
__all__ = ['organization_api']
