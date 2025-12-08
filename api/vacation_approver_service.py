#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
VACATION APPROVER SERVICE
========================================
Version: 1.0 - TAG 103
Datum: 08.12.2025

Findet automatisch den richtigen Genehmiger für einen Mitarbeiter
basierend auf:
1. Locosoft grp_code + subsidiary
2. AD-Gruppen (GRP_Urlaub_Genehmiger_*)

Features:
- get_approvers_for_employee(): Findet Genehmiger für MA
- get_team_for_approver(): Findet Team für Genehmiger
- is_approver(): Prüft ob User Genehmiger ist
"""

import sqlite3
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'


def get_db():
    """Erstellt DB-Verbindung"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_approvers_for_employee(employee_id: int) -> List[Dict]:
    """
    Findet alle Genehmiger für einen Mitarbeiter.
    
    Basiert auf:
    - Locosoft grp_code des Mitarbeiters
    - Locosoft subsidiary (Standort)
    - vacation_approval_rules Tabelle
    
    WICHTIG: Wenn der Mitarbeiter selbst Genehmiger ist (z.B. Abteilungsleiter),
    wird er übersprungen und stattdessen GL (Geschäftsleitung) zurückgegeben.
    
    Args:
        employee_id: ID des Mitarbeiters (employees.id)
    
    Returns:
        Liste von Genehmigern, sortiert nach Priorität
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 1. Hole grp_code und subsidiary des Mitarbeiters
        cursor.execute("""
            SELECT DISTINCT
                gm.grp_code,
                le.subsidiary
            FROM employees e
            JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
            JOIN loco_employees le ON lem.locosoft_id = le.employee_number
            JOIN loco_employees_group_mapping gm ON le.employee_number = gm.employee_number
            WHERE e.id = ? AND e.aktiv = 1
        """, (employee_id,))
        
        employee_groups = cursor.fetchall()
        
        if not employee_groups:
            logger.warning(f"Keine Locosoft-Zuordnung für employee_id={employee_id}")
            return []
        
        # 2. Finde passende Genehmiger-Regeln
        approvers = []
        seen_approvers = set()  # Vermeidet Duplikate
        employee_is_own_approver = False
        
        for row in employee_groups:
            grp_code = row['grp_code']
            subsidiary = row['subsidiary']
            
            # Suche Regeln: Exakter Match ODER subsidiary=NULL (alle Standorte)
            cursor.execute("""
                SELECT 
                    ar.id as rule_id,
                    ar.loco_grp_code,
                    ar.subsidiary as rule_subsidiary,
                    ar.approver_employee_id,
                    ar.approver_ldap_username,
                    ar.priority,
                    ar.notes,
                    e.first_name || ' ' || e.last_name as approver_name,
                    e.email as approver_email
                FROM vacation_approval_rules ar
                JOIN ldap_employee_mapping lem ON ar.approver_ldap_username = lem.ldap_username
                JOIN employees e ON lem.employee_id = e.id
                WHERE ar.loco_grp_code = ?
                  AND (ar.subsidiary IS NULL OR ar.subsidiary = ?)
                  AND ar.active = 1
                ORDER BY ar.priority ASC
            """, (grp_code, subsidiary))
            
            for approver_row in cursor.fetchall():
                # WICHTIG: Überspringe wenn Mitarbeiter sein eigener Genehmiger wäre
                if approver_row['approver_employee_id'] == employee_id:
                    employee_is_own_approver = True
                    logger.info(f"Employee {employee_id} ist selbst Genehmiger für {grp_code} - überspringe")
                    continue
                
                approver_key = (approver_row['approver_employee_id'], grp_code)
                
                if approver_key not in seen_approvers:
                    seen_approvers.add(approver_key)
                    approvers.append({
                        'approver_id': approver_row['approver_employee_id'],
                        'approver_name': approver_row['approver_name'],
                        'approver_ldap': approver_row['approver_ldap_username'],
                        'approver_email': approver_row['approver_email'],
                        'priority': approver_row['priority'],
                        'rule_grp_code': grp_code,
                        'rule_subsidiary': approver_row['rule_subsidiary'],
                        'notes': approver_row['notes']
                    })
        
        # 3. Wenn Mitarbeiter selbst Genehmiger ist und keine anderen Genehmiger gefunden:
        #    Eskaliere zu Geschäftsleitung (GL)
        if employee_is_own_approver and not approvers:
            logger.info(f"Employee {employee_id} ist Abteilungsleiter - eskaliere zu GL")
            cursor.execute("""
                SELECT 
                    ar.approver_employee_id,
                    ar.approver_ldap_username,
                    ar.priority,
                    ar.notes,
                    e.first_name || ' ' || e.last_name as approver_name,
                    e.email as approver_email
                FROM vacation_approval_rules ar
                JOIN ldap_employee_mapping lem ON ar.approver_ldap_username = lem.ldap_username
                JOIN employees e ON lem.employee_id = e.id
                WHERE ar.loco_grp_code IN ('GL', 'FL')
                  AND ar.active = 1
                  AND ar.approver_employee_id != ?
                ORDER BY ar.priority ASC
            """, (employee_id,))
            
            for gl_row in cursor.fetchall():
                if gl_row['approver_employee_id'] not in seen_approvers:
                    seen_approvers.add(gl_row['approver_employee_id'])
                    approvers.append({
                        'approver_id': gl_row['approver_employee_id'],
                        'approver_name': gl_row['approver_name'],
                        'approver_ldap': gl_row['approver_ldap_username'],
                        'approver_email': gl_row['approver_email'],
                        'priority': gl_row['priority'],
                        'rule_grp_code': 'GL',
                        'rule_subsidiary': None,
                        'notes': gl_row['notes'] or 'Geschäftsleitung (Eskalation)'
                    })
        
        # Sortiere nach Priorität
        approvers.sort(key=lambda x: x['priority'])
        
        return approvers
        
    except Exception as e:
        logger.error(f"Fehler bei get_approvers_for_employee: {e}")
        raise
    finally:
        conn.close()


def get_team_for_approver(approver_ldap_username: str) -> List[Dict]:
    """
    Findet alle Mitarbeiter, für die ein User Genehmiger ist.
    
    Args:
        approver_ldap_username: LDAP-Username des Genehmigers (z.B. 'w.scheingraber')
    
    Returns:
        Liste von Team-Mitgliedern
        [
            {
                'employee_id': 42,
                'name': 'Andreas Dederer',
                'ldap_username': 'andreas.dederer',
                'grp_code': 'MON',
                'subsidiary': 1,
                'standort': 'Deggendorf',
                'approver_priority': 1
            },
            ...
        ]
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT DISTINCT
                e.id as employee_id,
                e.first_name || ' ' || e.last_name as name,
                lem.ldap_username,
                lem.locosoft_id,
                gm.grp_code,
                le.subsidiary,
                CASE le.subsidiary 
                    WHEN 1 THEN 'Deggendorf'
                    WHEN 3 THEN 'Landau'
                    ELSE 'Unbekannt'
                END as standort,
                ar.priority as approver_priority
            FROM vacation_approval_rules ar
            JOIN loco_employees_group_mapping gm ON ar.loco_grp_code = gm.grp_code
            JOIN loco_employees le ON gm.employee_number = le.employee_number
                AND (ar.subsidiary IS NULL OR ar.subsidiary = le.subsidiary)
            JOIN ldap_employee_mapping lem ON le.employee_number = lem.locosoft_id
            JOIN employees e ON lem.employee_id = e.id
            WHERE ar.approver_ldap_username = ?
              AND ar.active = 1
              AND e.aktiv = 1
              AND lem.ldap_username != ?  -- Nicht sich selbst
            ORDER BY ar.priority, e.last_name, e.first_name
        """, (approver_ldap_username, approver_ldap_username))
        
        team = []
        seen = set()
        
        for row in cursor.fetchall():
            if row['employee_id'] not in seen:
                seen.add(row['employee_id'])
                team.append({
                    'employee_id': row['employee_id'],
                    'name': row['name'],
                    'ldap_username': row['ldap_username'],
                    'locosoft_id': row['locosoft_id'],  # NEU: Für Locosoft-Abfragen
                    'grp_code': row['grp_code'],
                    'subsidiary': row['subsidiary'],
                    'standort': row['standort'],
                    'approver_priority': row['approver_priority']
                })
        
        return team
        
    except Exception as e:
        logger.error(f"Fehler bei get_team_for_approver: {e}")
        raise
    finally:
        conn.close()


def is_approver(ldap_username: str) -> bool:
    """
    Prüft ob ein User Genehmiger-Rechte hat.
    
    Args:
        ldap_username: LDAP-Username (z.B. 'matthias.koenig')
    
    Returns:
        True wenn User mindestens eine aktive Genehmiger-Regel hat
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT COUNT(*) as cnt
            FROM vacation_approval_rules
            WHERE approver_ldap_username = ? AND active = 1
        """, (ldap_username,))
        
        result = cursor.fetchone()
        return result['cnt'] > 0
        
    except Exception as e:
        logger.error(f"Fehler bei is_approver: {e}")
        return False
    finally:
        conn.close()


def get_approver_summary(ldap_username: str) -> Dict:
    """
    Gibt eine Zusammenfassung für einen Genehmiger zurück.
    
    Returns:
        {
            'is_approver': True,
            'team_size': 12,
            'groups': ['MON', 'SB', 'SER'],
            'pending_requests': 3
        }
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Ist Genehmiger?
        if not is_approver(ldap_username):
            return {
                'is_approver': False,
                'team_size': 0,
                'groups': [],
                'pending_requests': 0
            }
        
        # Team-Größe
        team = get_team_for_approver(ldap_username)
        team_size = len(team)
        
        # Gruppen
        cursor.execute("""
            SELECT DISTINCT loco_grp_code
            FROM vacation_approval_rules
            WHERE approver_ldap_username = ? AND active = 1
            ORDER BY loco_grp_code
        """, (ldap_username,))
        groups = [row['loco_grp_code'] for row in cursor.fetchall()]
        
        # Offene Anträge (pending) für das Team
        team_ids = [m['employee_id'] for m in team]
        pending_count = 0
        
        if team_ids:
            placeholders = ','.join('?' * len(team_ids))
            cursor.execute(f"""
                SELECT COUNT(*) as cnt
                FROM vacation_bookings
                WHERE employee_id IN ({placeholders})
                  AND status = 'pending'
            """, team_ids)
            pending_count = cursor.fetchone()['cnt']
        
        return {
            'is_approver': True,
            'team_size': team_size,
            'groups': groups,
            'pending_requests': pending_count
        }
        
    except Exception as e:
        logger.error(f"Fehler bei get_approver_summary: {e}")
        return {
            'is_approver': False,
            'team_size': 0,
            'groups': [],
            'pending_requests': 0,
            'error': str(e)
        }
    finally:
        conn.close()


# ============================================================================
# TEST
# ============================================================================
if __name__ == '__main__':
    print("=== VACATION APPROVER SERVICE TEST ===\n")
    
    # Test 1: Genehmiger für einen Monteur finden
    print("1. Genehmiger für Employee ID 42 (Beispiel):")
    approvers = get_approvers_for_employee(42)
    for a in approvers:
        print(f"   - {a['approver_name']} (Prio {a['priority']}, Gruppe: {a['rule_grp_code']})")
    
    print()
    
    # Test 2: Team für Wolfgang Scheingraber
    print("2. Team für w.scheingraber:")
    team = get_team_for_approver('w.scheingraber')
    print(f"   Team-Größe: {len(team)}")
    for m in team[:5]:
        print(f"   - {m['name']} ({m['grp_code']}, {m['standort']})")
    if len(team) > 5:
        print(f"   ... und {len(team) - 5} weitere")
    
    print()
    
    # Test 3: Approver Summary für Matthias König
    print("3. Summary für matthias.koenig:")
    summary = get_approver_summary('matthias.koenig')
    print(f"   Ist Genehmiger: {summary['is_approver']}")
    print(f"   Team-Größe: {summary['team_size']}")
    print(f"   Gruppen: {', '.join(summary['groups'])}")
    print(f"   Offene Anträge: {summary['pending_requests']}")
