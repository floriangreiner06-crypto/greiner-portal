#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VACATION CHEF API - Ergänzung für Chef-Übersicht
TAG 103
Updated: TAG 117 - Migration auf db_session
"""

from flask import Blueprint, jsonify
from datetime import datetime

# Zentrale DB-Utilities (TAG117)
from api.db_utils import db_session

chef_api = Blueprint('vacation_chef_api', __name__, url_prefix='/api/vacation')


# Gruppen-Code zu lesbarem Namen
GRP_NAMES = {
    'VKB': 'Verkaufsberater',
    'MON': 'Monteure/Mechaniker',
    'SB': 'Serviceberater',
    'SER': 'Service Empfang',
    'LAG': 'Lager/Teile',
    'DIS': 'Disposition',
    'CC': 'Callcenter/CRM',
    'VER': 'Verwaltung/Buchhaltung',
    'FA': 'Fahrzeugannahme',
    'FL': 'Filialleitung',
    'GL': 'Geschäftsleitung',
    'A-W': 'Azubi Werkstatt',
    'A-L': 'Azubi Lager',
    'G': 'Gebäude/Hausmeister',
    'HM': 'Hausmeister',
    'FZ': 'Fuhrpark/Zulassung',
    'MAR': 'Marketing'
}

def get_grp_display_name(code):
    return GRP_NAMES.get(code, code)


@chef_api.route('/chef-overview', methods=['GET'])
def get_chef_overview():
    """
    GET /api/vacation/chef-overview

    Gibt alle Genehmiger mit ihren Teams zurück.
    Für die Chef-Übersicht / Admin-Dashboard.
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()

            # Alle Genehmiger mit ihren Regeln
            cursor.execute("""
                SELECT DISTINCT
                    ar.approver_ldap_username,
                    e.first_name || ' ' || e.last_name as approver_name,
                    e.id as approver_id
                FROM vacation_approval_rules ar
                JOIN ldap_employee_mapping lem ON ar.approver_ldap_username = lem.ldap_username
                JOIN employees e ON lem.employee_id = e.id
                WHERE ar.active = 1 AND ar.priority = 1
                ORDER BY e.last_name
            """)

            approvers = cursor.fetchall()
            teams = []
            all_groups = set()
            total_employees = set()
            total_pending = 0

            for approver in approvers:
                approver_ldap = approver['approver_ldap_username']

                # Gruppen des Genehmigers
                cursor.execute("""
                    SELECT DISTINCT
                        loco_grp_code,
                        subsidiary,
                        CASE subsidiary
                            WHEN 1 THEN 'Deggendorf'
                            WHEN 3 THEN 'Landau'
                            ELSE 'Alle'
                        END as standort
                    FROM vacation_approval_rules
                    WHERE approver_ldap_username = ? AND active = 1 AND priority = 1
                """, (approver_ldap,))

                rules = cursor.fetchall()
                grp_codes = list(set([r['loco_grp_code'] for r in rules]))
                all_groups.update(grp_codes)

                # Standort bestimmen (wenn nur ein Standort, dann den, sonst "Alle")
                standorte = list(set([r['standort'] for r in rules]))
                standort = standorte[0] if len(standorte) == 1 else 'Alle'

                # Team-Mitglieder holen (über department_name statt loco_grp_code)
                cursor.execute("""
                    SELECT DISTINCT
                        e.id as employee_id,
                        e.first_name || ' ' || e.last_name as name,
                        e.department_name as grp_code,
                        CASE e.location
                            WHEN 'Deggendorf' THEN 1
                            WHEN 'Landau a.d. Isar' THEN 3
                            ELSE NULL
                        END as subsidiary,
                        COALESCE(e.location, 'Unbekannt') as standort
                    FROM vacation_approval_rules ar
                    JOIN employees e ON e.department_name = ar.loco_grp_code
                        AND (ar.subsidiary IS NULL
                             OR (ar.subsidiary = 1 AND e.location = 'Deggendorf')
                             OR (ar.subsidiary = 3 AND e.location = 'Landau a.d. Isar'))
                    LEFT JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
                    WHERE ar.approver_ldap_username = ?
                      AND ar.active = 1
                      AND ar.priority = 1
                      AND e.aktiv = 1
                      AND (lem.ldap_username IS NULL OR lem.ldap_username != ?)
                    ORDER BY e.last_name
                """, (approver_ldap, approver_ldap))

                members_raw = cursor.fetchall()
                member_ids = list(set([m['employee_id'] for m in members_raw]))
                total_employees.update(member_ids)

                # Urlaubssalden für Mitglieder
                members = []
                if member_ids:
                    placeholders = ','.join('?' * len(member_ids))
                    cursor.execute(f"""
                        SELECT
                            employee_id,
                            anspruch,
                            verbraucht,
                            geplant,
                            resturlaub
                        FROM v_vacation_balance_2025
                        WHERE employee_id IN ({placeholders})
                    """, member_ids)

                    balances = {row['employee_id']: dict(row) for row in cursor.fetchall()}

                    seen_ids = set()
                    for m in members_raw:
                        if m['employee_id'] in seen_ids:
                            continue
                        seen_ids.add(m['employee_id'])

                        balance = balances.get(m['employee_id'], {})
                        members.append({
                            'employee_id': m['employee_id'],
                            'name': m['name'],
                            'grp_code': m['grp_code'],
                            'standort': m['standort'],
                            'anspruch': balance.get('anspruch', 30),
                            'verbraucht': balance.get('verbraucht', 0),
                            'resturlaub': balance.get('resturlaub', 30)
                        })

                # Offene Anträge zählen
                pending_count = 0
                if member_ids:
                    cursor.execute(f"""
                        SELECT COUNT(*) as cnt
                        FROM vacation_bookings
                        WHERE employee_id IN ({placeholders})
                          AND status = 'pending'
                    """, member_ids)
                    pending_count = cursor.fetchone()['cnt']
                    total_pending += pending_count

                teams.append({
                    'approver_ldap': approver_ldap,
                    'approver_name': approver['approver_name'],
                    'approver_id': approver['approver_id'],
                    'grp_codes': grp_codes,
                    'grp_names': [get_grp_display_name(g) for g in grp_codes],
                    'standort': standort,
                    'team_size': len(members),
                    'pending_count': pending_count,
                    'members': members
                })

            return jsonify({
                'success': True,
                'teams': teams,
                'groups': sorted(list(all_groups)),
                'summary': {
                    'approver_count': len(teams),
                    'employee_count': len(total_employees),
                    'pending_count': total_pending,
                    'group_count': len(all_groups)
                }
            })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
