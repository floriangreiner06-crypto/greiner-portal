#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMPLOYEE SYNC SERVICE - LDAP/Locosoft Auto-Füllung
TAG 213: Synchronisiert Mitarbeiterdaten aus LDAP und Locosoft
"""

from typing import Dict, Optional, List, Tuple
from datetime import datetime, date
import logging

from api.db_utils import db_session, locosoft_session, row_to_dict

logger = logging.getLogger(__name__)

# Lazy Import für LDAP (optional)
def get_ldap_connector():
    """Lazy Import für LDAP-Connector"""
    try:
        from auth.ldap_connector import get_ldap_connector as _get_ldap_connector
        return _get_ldap_connector()
    except ImportError:
        logger.warning("LDAP3 nicht verfügbar - LDAP-Sync deaktiviert")
        return None

# Standort-Mapping
STANDORT_MAPPING = {
    1: 'Deggendorf',  # DEG
    2: 'Deggendorf',  # HYU (Hyundai)
    3: 'Landau a.d. Isar',  # LAN
    4: 'Landau a.d. Isar'  # Fallback
}

LDAP_COMPANY_MAPPING = {
    'DEG': 'Deggendorf',
    'HYU': 'Deggendorf',
    'LAN': 'Landau a.d. Isar'
}


def parse_locosoft_name(name: str) -> Dict[str, str]:
    """
    Parst Locosoft-Name-Format: 'Nachname,Vorname' oder 'Nachname Vorname'
    
    Args:
        name: Name aus Locosoft (z.B. "Huber,Herbert" oder "Huber Herbert")
        
    Returns:
        Dict mit 'first_name' und 'last_name'
    """
    if not name:
        return {'first_name': '', 'last_name': ''}
    
    name = name.strip()
    
    # Format: "Nachname,Vorname"
    if ',' in name:
        parts = name.split(',', 1)
        return {
            'last_name': parts[0].strip(),
            'first_name': parts[1].strip() if len(parts) > 1 else ''
        }
    
    # Format: "Nachname Vorname" (Fallback)
    parts = name.split(' ', 1)
    if len(parts) == 2:
        return {
            'last_name': parts[0].strip(),
            'first_name': parts[1].strip()
        }
    
    # Nur ein Wort: als Nachname behandeln
    return {
        'last_name': name,
        'first_name': ''
    }


def sync_from_ldap(employee_id: int, ldap_username: str, overwrite: bool = False) -> Dict:
    """
    Lädt Daten aus LDAP und füllt leere Felder (oder überschreibt bei overwrite=True)
    
    Args:
        employee_id: ID des Mitarbeiters
        ldap_username: LDAP-Username (sAMAccountName)
        overwrite: Wenn True, überschreibt auch vorhandene Felder
        
    Returns:
        Dict mit:
            - 'success': bool
            - 'changes': Dict mit geänderten Feldern
            - 'error': Optional[str]
    """
    try:
        # Hole LDAP-Daten
        ldap_connector = get_ldap_connector()
        if not ldap_connector:
            return {
                'success': False,
                'error': 'LDAP-Connector nicht verfügbar',
                'changes': {}
            }
        
        ldap_data = ldap_connector.get_user_details(ldap_username)
        
        if not ldap_data:
            return {
                'success': False,
                'error': f'LDAP-User nicht gefunden: {ldap_username}',
                'changes': {}
            }
        
        # Hole aktuelle Mitarbeiterdaten
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM employees WHERE id = %s
            """, (employee_id,))
            emp_row = cursor.fetchone()
            
            if not emp_row:
                return {
                    'success': False,
                    'error': f'Mitarbeiter nicht gefunden: {employee_id}',
                    'changes': {}
                }
            
            emp_dict = row_to_dict(emp_row)
            
            # Bereite Änderungen vor
            changes = {}
            update_fields = []
            update_values = []
            
            # Email (Firmen-Email)
            if overwrite or not emp_dict.get('email'):
                if ldap_data.get('email') and ldap_data['email'] != emp_dict.get('email'):
                    changes['email'] = {'old': emp_dict.get('email'), 'new': ldap_data['email']}
                    update_fields.append('email = %s')
                    update_values.append(ldap_data['email'])
            
            # Abteilung (AD = führend: immer übernehmen wenn LDAP Wert hat, auch bei Restwert wie "Wer")
            if overwrite or not emp_dict.get('department_name'):
                if ldap_data.get('department') and ldap_data['department'] != emp_dict.get('department_name'):
                    changes['department_name'] = {'old': emp_dict.get('department_name'), 'new': ldap_data['department']}
                    update_fields.append('department_name = %s')
                    update_values.append(ldap_data['department'])
            
            # Standort (location) – aus AD company
            if overwrite or not emp_dict.get('location'):
                if ldap_data.get('company'):
                    location = LDAP_COMPANY_MAPPING.get(ldap_data['company'], ldap_data['company'])
                    if location != emp_dict.get('location'):
                        changes['location'] = {'old': emp_dict.get('location'), 'new': location}
                        update_fields.append('location = %s')
                        update_values.append(location)
            
            # Titel
            if overwrite or not emp_dict.get('title'):
                if ldap_data.get('title') and ldap_data['title'] != emp_dict.get('title'):
                    changes['title'] = {'old': emp_dict.get('title'), 'new': ldap_data['title']}
                    update_fields.append('title = %s')
                    update_values.append(ldap_data['title'])
            
            # Firma (company): AD ist führend – immer aus LDAP übernehmen wenn vorhanden (auch bei Teil-Eingabe wie "Aut")
            if ldap_data.get('company') and ldap_data['company'] != emp_dict.get('company'):
                changes['company'] = {'old': emp_dict.get('company'), 'new': ldap_data['company']}
                update_fields.append('company = %s')
                update_values.append(ldap_data['company'])
            
            # Company Email
            if overwrite or not emp_dict.get('company_email'):
                if ldap_data.get('email') and ldap_data['email'] != emp_dict.get('company_email'):
                    changes['company_email'] = {'old': emp_dict.get('company_email'), 'new': ldap_data['email']}
                    update_fields.append('company_email = %s')
                    update_values.append(ldap_data['email'])
            
            # Activity (aus title)
            if overwrite or not emp_dict.get('activity'):
                if ldap_data.get('title') and ldap_data['title'] != emp_dict.get('activity'):
                    changes['activity'] = {'old': emp_dict.get('activity'), 'new': ldap_data['title']}
                    update_fields.append('activity = %s')
                    update_values.append(ldap_data['title'])
            
            # Speichere Änderungen
            if update_fields:
                update_values.append(employee_id)
                query = f"UPDATE employees SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(query, update_values)
                conn.commit()
            
            return {
                'success': True,
                'changes': changes,
                'count': len(changes)
            }
    
    except Exception as e:
        logger.error(f"Fehler beim LDAP-Sync für Mitarbeiter {employee_id}: {e}")
        import traceback
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
            'changes': {}
        }


def sync_from_locosoft(employee_id: int, locosoft_id: int, overwrite: bool = False) -> Dict:
    """
    Lädt Daten aus Locosoft und füllt leere Felder (oder überschreibt bei overwrite=True)
    
    Args:
        employee_id: ID des Mitarbeiters
        locosoft_id: Locosoft employee_number
        overwrite: Wenn True, überschreibt auch vorhandene Felder
        
    Returns:
        Dict mit:
            - 'success': bool
            - 'changes': Dict mit geänderten Feldern
            - 'error': Optional[str]
    """
    try:
        # Hole Locosoft-Daten (ALLE verfügbaren Felder)
        with locosoft_session() as loco_conn:
            loco_cursor = loco_conn.cursor()
            
            loco_cursor.execute("""
                SELECT 
                    employee_number,
                    name,
                    initials,
                    customer_number,
                    employee_personnel_no,
                    employment_date,
                    termination_date,
                    leave_date,
                    subsidiary,
                    validity_date,
                    next_validity_date,
                    is_flextime,
                    schedule_index,
                    is_business_executive,
                    is_master_craftsman,
                    is_customer_reception,
                    productivity_factor
                FROM employees
                WHERE employee_number = %s AND is_latest_record = true
            """, (locosoft_id,))
            
            loco_row = loco_cursor.fetchone()
            
            if not loco_row:
                return {
                    'success': False,
                    'error': f'Locosoft-Mitarbeiter nicht gefunden: {locosoft_id}',
                    'changes': {}
                }
            
            loco_dict = row_to_dict(loco_row, loco_cursor)
            
            # Debug: Logge alle verfügbaren Felder
            logger.debug(f"Locosoft-Daten für {locosoft_id}: customer_number={loco_dict.get('customer_number')}, name={loco_dict.get('name')}")
        
        # Hole aktuelle Mitarbeiterdaten
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM employees WHERE id = %s
            """, (employee_id,))
            emp_row = cursor.fetchone()
            
            if not emp_row:
                return {
                    'success': False,
                    'error': f'Mitarbeiter nicht gefunden: {employee_id}',
                    'changes': {}
                }
            
            emp_dict = row_to_dict(emp_row)
            
            # Bereite Änderungen vor
            changes = {}
            update_fields = []
            update_values = []
            
            # Automatik: Bereits vorhandenes Austrittsdatum in der Vergangenheit → deaktivieren (z. B. nachträglicher Sync)
            exit_date_val = emp_dict.get('exit_date')
            if exit_date_val and emp_dict.get('aktiv', True):
                if isinstance(exit_date_val, str):
                    exit_date_val = datetime.strptime(exit_date_val[:10], '%Y-%m-%d').date()
                elif hasattr(exit_date_val, 'date'):
                    exit_date_val = exit_date_val.date()
                if exit_date_val <= date.today():
                    update_fields.append('aktiv = %s')
                    update_values.append(False)
                    update_fields.append('deactivate_after_exit = %s')
                    update_values.append(True)
                    changes['aktiv'] = {'old': True, 'new': False}
                    changes['deactivate_after_exit'] = {'old': False, 'new': True}
            
            # Name parsen
            parsed_name = parse_locosoft_name(loco_dict.get('name', ''))
            
            # First Name
            if overwrite or not emp_dict.get('first_name'):
                if parsed_name.get('first_name') and parsed_name['first_name'] != emp_dict.get('first_name'):
                    changes['first_name'] = {'old': emp_dict.get('first_name'), 'new': parsed_name['first_name']}
                    update_fields.append('first_name = %s')
                    update_values.append(parsed_name['first_name'])
            
            # Last Name
            if overwrite or not emp_dict.get('last_name'):
                if parsed_name.get('last_name') and parsed_name['last_name'] != emp_dict.get('last_name'):
                    changes['last_name'] = {'old': emp_dict.get('last_name'), 'new': parsed_name['last_name']}
                    update_fields.append('last_name = %s')
                    update_values.append(parsed_name['last_name'])
            
            # Eintrittsdatum
            if overwrite or not emp_dict.get('entry_date'):
                if loco_dict.get('employment_date'):
                    emp_date = loco_dict['employment_date']
                    if isinstance(emp_date, str):
                        emp_date = datetime.strptime(emp_date, '%Y-%m-%d').date()
                    elif hasattr(emp_date, 'date'):
                        emp_date = emp_date.date()
                    
                    current_entry = emp_dict.get('entry_date')
                    if current_entry:
                        if isinstance(current_entry, str):
                            current_entry = datetime.strptime(current_entry, '%Y-%m-%d').date()
                        elif hasattr(current_entry, 'date'):
                            current_entry = current_entry.date()
                    
                    if not current_entry or emp_date != current_entry:
                        changes['entry_date'] = {'old': str(current_entry) if current_entry else None, 'new': str(emp_date)}
                        update_fields.append('entry_date = %s')
                        update_values.append(emp_date)
            
            # Austrittsdatum
            if overwrite or not emp_dict.get('exit_date'):
                if loco_dict.get('termination_date'):
                    term_date = loco_dict['termination_date']
                    if isinstance(term_date, str):
                        term_date = datetime.strptime(term_date, '%Y-%m-%d').date()
                    elif hasattr(term_date, 'date'):
                        term_date = term_date.date()
                    
                    current_exit = emp_dict.get('exit_date')
                    if current_exit:
                        if isinstance(current_exit, str):
                            current_exit = datetime.strptime(current_exit, '%Y-%m-%d').date()
                        elif hasattr(current_exit, 'date'):
                            current_exit = current_exit.date()
                    
                    if not current_exit or term_date != current_exit:
                        changes['exit_date'] = {'old': str(current_exit) if current_exit else None, 'new': str(term_date)}
                        update_fields.append('exit_date = %s')
                        update_values.append(term_date)
                        # Automatik: Austritt in der Vergangenheit → im Portal deaktivieren (nicht mehr im Urlaubsplaner)
                        if term_date <= date.today():
                            update_fields.append('aktiv = %s')
                            update_values.append(False)
                            update_fields.append('deactivate_after_exit = %s')
                            update_values.append(True)
                            changes['aktiv'] = {'old': True, 'new': False}
                            changes['deactivate_after_exit'] = {'old': False, 'new': True}
            
            # Personalnummer
            if overwrite or not emp_dict.get('personal_nr'):
                if loco_dict.get('employee_personnel_no'):
                    pers_nr = str(loco_dict['employee_personnel_no'])
                    if pers_nr != '0' and pers_nr != emp_dict.get('personal_nr'):
                        changes['personal_nr'] = {'old': emp_dict.get('personal_nr'), 'new': pers_nr}
                        update_fields.append('personal_nr = %s')
                        update_values.append(pers_nr)
            
            # Personal-Nr. 1
            if overwrite or not emp_dict.get('personal_nr_1'):
                if loco_dict.get('employee_personnel_no'):
                    pers_nr = str(loco_dict['employee_personnel_no'])
                    if pers_nr != '0' and pers_nr != emp_dict.get('personal_nr_1'):
                        changes['personal_nr_1'] = {'old': emp_dict.get('personal_nr_1'), 'new': pers_nr}
                        update_fields.append('personal_nr_1 = %s')
                        update_values.append(pers_nr)
            
            # Standort (location)
            if overwrite or not emp_dict.get('location'):
                if loco_dict.get('subsidiary'):
                    subsidiary = loco_dict['subsidiary']
                    location = STANDORT_MAPPING.get(subsidiary, 'Unbekannt')
                    if location != emp_dict.get('location'):
                        changes['location'] = {'old': emp_dict.get('location'), 'new': location}
                        update_fields.append('location = %s')
                        update_values.append(location)
            
            # Customer Number
            if overwrite or not emp_dict.get('customer_number'):
                if loco_dict.get('customer_number'):
                    cust_nr = loco_dict['customer_number']
                    if cust_nr != 0 and cust_nr != emp_dict.get('customer_number'):
                        changes['customer_number'] = {'old': emp_dict.get('customer_number'), 'new': cust_nr}
                        update_fields.append('customer_number = %s')
                        update_values.append(cust_nr)
            
            # Leave Date (Urlaubsdatum - könnte für exit_date verwendet werden wenn termination_date leer)
            if overwrite or not emp_dict.get('exit_date'):
                if not loco_dict.get('termination_date') and loco_dict.get('leave_date'):
                    leave_date = loco_dict['leave_date']
                    if isinstance(leave_date, str):
                        leave_date = datetime.strptime(leave_date, '%Y-%m-%d').date()
                    elif hasattr(leave_date, 'date'):
                        leave_date = leave_date.date()
                    
                    current_exit = emp_dict.get('exit_date')
                    if current_exit:
                        if isinstance(current_exit, str):
                            current_exit = datetime.strptime(current_exit, '%Y-%m-%d').date()
                        elif hasattr(current_exit, 'date'):
                            current_exit = current_exit.date()
                    
                    if not current_exit or leave_date != current_exit:
                        changes['exit_date'] = {'old': str(current_exit) if current_exit else None, 'new': str(leave_date)}
                        update_fields.append('exit_date = %s')
                        update_values.append(leave_date)
                        if leave_date <= date.today():
                            update_fields.append('aktiv = %s')
                            update_values.append(False)
                            update_fields.append('deactivate_after_exit = %s')
                            update_values.append(True)
                            changes['aktiv'] = {'old': True, 'new': False}
                            changes['deactivate_after_exit'] = {'old': False, 'new': True}
            
            # Speichere Änderungen
            if update_fields:
                update_values.append(employee_id)
                query = f"UPDATE employees SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(query, update_values)
                conn.commit()
            
            # Hole Adressdaten aus customers_suppliers wenn customer_number vorhanden
            customer_number = loco_dict.get('customer_number') or emp_dict.get('customer_number')
            if customer_number and customer_number != 0:
                address_changes = _sync_address_from_customer(employee_id, customer_number, emp_dict, overwrite)
                if address_changes:
                    changes.update(address_changes)
            
            return {
                'success': True,
                'changes': changes,
                'count': len(changes)
            }
    
    except Exception as e:
        logger.error(f"Fehler beim Locosoft-Sync für Mitarbeiter {employee_id}: {e}")
        import traceback
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
            'changes': {}
        }


def sync_preview(employee_id: int, overwrite: bool = False) -> Dict:
    """
    Zeigt Vorschau der Sync-Änderungen ohne zu speichern
    
    Args:
        employee_id: ID des Mitarbeiters
        overwrite: Wenn True, zeigt auch Überschreibungen
        
    Returns:
        Dict mit:
            - 'success': bool
            - 'ldap_changes': Dict (wenn ldap_username vorhanden)
            - 'locosoft_changes': Dict (wenn locosoft_id vorhanden)
            - 'error': Optional[str]
    """
    try:
        # Hole Mitarbeiterdaten
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    e.*,
                    lem.ldap_username,
                    lem.locosoft_id
                FROM employees e
                LEFT JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
                WHERE e.id = %s
            """, (employee_id,))
            
            emp_row = cursor.fetchone()
            
            if not emp_row:
                return {
                    'success': False,
                    'error': f'Mitarbeiter nicht gefunden: {employee_id}'
                }
            
            emp_dict = row_to_dict(emp_row)
            ldap_username = emp_dict.get('ldap_username')
            locosoft_id = emp_dict.get('locosoft_id')
        
        result = {
            'success': True,
            'ldap_username': ldap_username,
            'locosoft_id': locosoft_id,
            'ldap_changes': {},
            'locosoft_changes': {}
        }
        
        # LDAP Preview (nur berechnen, nicht speichern)
        if ldap_username:
            ldap_changes = _calculate_ldap_changes(employee_id, ldap_username, emp_dict, overwrite)
            result['ldap_changes'] = ldap_changes
        
        # Locosoft Preview (nur berechnen, nicht speichern)
        if locosoft_id:
            locosoft_changes = _calculate_locosoft_changes(employee_id, locosoft_id, emp_dict, overwrite)
            result['locosoft_changes'] = locosoft_changes
        
        return result
    
    except Exception as e:
        logger.error(f"Fehler beim Sync-Preview für Mitarbeiter {employee_id}: {e}")
        import traceback
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }


def _calculate_ldap_changes(employee_id: int, ldap_username: str, emp_dict: Dict, overwrite: bool) -> Dict:
    """Berechnet LDAP-Änderungen ohne zu speichern"""
    changes = {}
    
    try:
        ldap_connector = get_ldap_connector()
        if not ldap_connector:
            return changes
        
        ldap_data = ldap_connector.get_user_details(ldap_username)
        if not ldap_data:
            return changes
        
        # Email
        if overwrite or not emp_dict.get('email'):
            if ldap_data.get('email') and ldap_data['email'] != emp_dict.get('email'):
                changes['email'] = {'old': emp_dict.get('email'), 'new': ldap_data['email']}
        
        # Abteilung
        if overwrite or not emp_dict.get('department_name'):
            if ldap_data.get('department') and ldap_data['department'] != emp_dict.get('department_name'):
                changes['department_name'] = {'old': emp_dict.get('department_name'), 'new': ldap_data['department']}
        
        # Standort
        if overwrite or not emp_dict.get('location'):
            if ldap_data.get('company'):
                location = LDAP_COMPANY_MAPPING.get(ldap_data['company'], ldap_data['company'])
                if location != emp_dict.get('location'):
                    changes['location'] = {'old': emp_dict.get('location'), 'new': location}
        
        # Titel
        if overwrite or not emp_dict.get('title'):
            if ldap_data.get('title') and ldap_data['title'] != emp_dict.get('title'):
                changes['title'] = {'old': emp_dict.get('title'), 'new': ldap_data['title']}
        
        # Firma (company): AD führend – immer anzeigen/übernehmen wenn LDAP Wert hat
        if ldap_data.get('company') and ldap_data['company'] != emp_dict.get('company'):
            changes['company'] = {'old': emp_dict.get('company'), 'new': ldap_data['company']}
        
        # Company Email
        if overwrite or not emp_dict.get('company_email'):
            if ldap_data.get('email') and ldap_data['email'] != emp_dict.get('company_email'):
                changes['company_email'] = {'old': emp_dict.get('company_email'), 'new': ldap_data['email']}
        
        # Activity
        if overwrite or not emp_dict.get('activity'):
            if ldap_data.get('title') and ldap_data['title'] != emp_dict.get('activity'):
                changes['activity'] = {'old': emp_dict.get('activity'), 'new': ldap_data['title']}
    
    except Exception as e:
        logger.error(f"Fehler bei LDAP-Preview: {e}")
    
    return changes


def _calculate_locosoft_changes(employee_id: int, locosoft_id: int, emp_dict: Dict, overwrite: bool) -> Dict:
    """Berechnet Locosoft-Änderungen ohne zu speichern"""
    changes = {}
    
    try:
        logger.debug(f"Berechne Locosoft-Änderungen für employee_id={employee_id}, locosoft_id={locosoft_id}")
        
        # Hole Locosoft-Daten (ALLE verfügbaren Felder)
        with locosoft_session() as loco_conn:
            loco_cursor = loco_conn.cursor()
            
            loco_cursor.execute("""
                SELECT 
                    employee_number,
                    name,
                    initials,
                    customer_number,
                    employee_personnel_no,
                    employment_date,
                    termination_date,
                    leave_date,
                    subsidiary,
                    validity_date,
                    next_validity_date,
                    is_flextime,
                    schedule_index,
                    is_business_executive,
                    is_master_craftsman,
                    is_customer_reception,
                    productivity_factor
                FROM employees
                WHERE employee_number = %s AND is_latest_record = true
            """, (locosoft_id,))
            
            loco_row = loco_cursor.fetchone()
            if not loco_row:
                logger.warning(f"Locosoft-Mitarbeiter nicht gefunden: {locosoft_id}")
                return changes
            
            loco_dict = row_to_dict(loco_row, loco_cursor)
            logger.debug(f"Locosoft-Daten gefunden: customer_number={loco_dict.get('customer_number')}, name={loco_dict.get('name')}")
        
        # Name parsen
        parsed_name = parse_locosoft_name(loco_dict.get('name', ''))
        
        # First Name
        if overwrite or not emp_dict.get('first_name'):
            if parsed_name.get('first_name') and parsed_name['first_name'] != emp_dict.get('first_name'):
                changes['first_name'] = {'old': emp_dict.get('first_name'), 'new': parsed_name['first_name']}
        
        # Last Name
        if overwrite or not emp_dict.get('last_name'):
            if parsed_name.get('last_name') and parsed_name['last_name'] != emp_dict.get('last_name'):
                changes['last_name'] = {'old': emp_dict.get('last_name'), 'new': parsed_name['last_name']}
        
        # Eintrittsdatum
        if overwrite or not emp_dict.get('entry_date'):
            if loco_dict.get('employment_date'):
                emp_date = loco_dict['employment_date']
                if isinstance(emp_date, str):
                    emp_date = datetime.strptime(emp_date, '%Y-%m-%d').date()
                elif hasattr(emp_date, 'date'):
                    emp_date = emp_date.date()
                
                current_entry = emp_dict.get('entry_date')
                if current_entry:
                    if isinstance(current_entry, str):
                        current_entry = datetime.strptime(current_entry, '%Y-%m-%d').date()
                    elif hasattr(current_entry, 'date'):
                        current_entry = current_entry.date()
                
                if not current_entry or emp_date != current_entry:
                    changes['entry_date'] = {'old': str(current_entry) if current_entry else None, 'new': str(emp_date)}
        
        # Austrittsdatum
        if overwrite or not emp_dict.get('exit_date'):
            if loco_dict.get('termination_date'):
                term_date = loco_dict['termination_date']
                if isinstance(term_date, str):
                    term_date = datetime.strptime(term_date, '%Y-%m-%d').date()
                elif hasattr(term_date, 'date'):
                    term_date = term_date.date()
                
                current_exit = emp_dict.get('exit_date')
                if current_exit:
                    if isinstance(current_exit, str):
                        current_exit = datetime.strptime(current_exit, '%Y-%m-%d').date()
                    elif hasattr(current_exit, 'date'):
                        current_exit = current_exit.date()
                
                if not current_exit or term_date != current_exit:
                    changes['exit_date'] = {'old': str(current_exit) if current_exit else None, 'new': str(term_date)}
        
        # Personalnummer
        if overwrite or not emp_dict.get('personal_nr'):
            if loco_dict.get('employee_personnel_no'):
                pers_nr = str(loco_dict['employee_personnel_no'])
                if pers_nr != '0' and pers_nr != emp_dict.get('personal_nr'):
                    changes['personal_nr'] = {'old': emp_dict.get('personal_nr'), 'new': pers_nr}
        
        # Personal-Nr. 1
        if overwrite or not emp_dict.get('personal_nr_1'):
            if loco_dict.get('employee_personnel_no'):
                pers_nr = str(loco_dict['employee_personnel_no'])
                if pers_nr != '0' and pers_nr != emp_dict.get('personal_nr_1'):
                    changes['personal_nr_1'] = {'old': emp_dict.get('personal_nr_1'), 'new': pers_nr}
        
        # Standort
        if overwrite or not emp_dict.get('location'):
            if loco_dict.get('subsidiary'):
                subsidiary = loco_dict['subsidiary']
                location = STANDORT_MAPPING.get(subsidiary, 'Unbekannt')
                if location != emp_dict.get('location'):
                    changes['location'] = {'old': emp_dict.get('location'), 'new': location}
        
        # Customer Number
        if overwrite or not emp_dict.get('customer_number'):
            if loco_dict.get('customer_number'):
                cust_nr = loco_dict['customer_number']
                if cust_nr != 0 and cust_nr != emp_dict.get('customer_number'):
                    changes['customer_number'] = {'old': emp_dict.get('customer_number'), 'new': cust_nr}
        
        # WICHTIG: Adressdaten aus customers_suppliers (muss NACH customer_number Check kommen)
        # Verwende customer_number aus loco_dict (frisch geholt) oder emp_dict (bereits vorhanden)
        customer_number_for_address = loco_dict.get('customer_number') or emp_dict.get('customer_number')
        logger.debug(f"customer_number für Adress-Sync: {customer_number_for_address} (aus loco_dict: {loco_dict.get('customer_number')}, aus emp_dict: {emp_dict.get('customer_number')})")
        
        if customer_number_for_address and customer_number_for_address != 0:
            logger.debug(f"Rufe _calculate_address_changes auf für customer_number={customer_number_for_address}")
            address_changes = _calculate_address_changes(customer_number_for_address, emp_dict, overwrite)
            logger.debug(f"Adress-Änderungen erhalten: {len(address_changes)} Felder")
            if address_changes:
                changes.update(address_changes)
                logger.debug(f"Gesamt-Änderungen nach Adress-Sync: {len(changes)} Felder")
        else:
            logger.warning(f"Keine customer_number verfügbar für Adress-Sync (loco_dict: {loco_dict.get('customer_number')}, emp_dict: {emp_dict.get('customer_number')})")
        
        # Leave Date (Urlaubsdatum - könnte für exit_date verwendet werden wenn termination_date leer)
        if overwrite or not emp_dict.get('exit_date'):
            if not loco_dict.get('termination_date') and loco_dict.get('leave_date'):
                leave_date = loco_dict['leave_date']
                if isinstance(leave_date, str):
                    leave_date = datetime.strptime(leave_date, '%Y-%m-%d').date()
                elif hasattr(leave_date, 'date'):
                    leave_date = leave_date.date()
                
                current_exit = emp_dict.get('exit_date')
                if current_exit:
                    if isinstance(current_exit, str):
                        current_exit = datetime.strptime(current_exit, '%Y-%m-%d').date()
                    elif hasattr(current_exit, 'date'):
                        current_exit = current_exit.date()
                
                if not current_exit or leave_date != current_exit:
                    changes['exit_date'] = {'old': str(current_exit) if current_exit else None, 'new': str(leave_date)}
    
    except Exception as e:
        logger.error(f"Fehler bei Locosoft-Preview: {e}")
    
    return changes


def _sync_address_from_customer(employee_id: int, customer_number: int, emp_dict: Dict, overwrite: bool) -> Dict:
    """
    Synchronisiert Adressdaten aus Locosoft customers_suppliers Tabelle
    
    Args:
        employee_id: ID des Mitarbeiters
        customer_number: Locosoft customer_number
        emp_dict: Aktuelle Mitarbeiterdaten
        overwrite: Wenn True, überschreibt auch vorhandene Felder
        
    Returns:
        Dict mit geänderten Adressfeldern
    """
    changes = {}
    update_fields = []
    update_values = []
    
    try:
        # Hole Adressdaten aus customers_suppliers
        with locosoft_session() as loco_conn:
            loco_cursor = loco_conn.cursor()
            
            loco_cursor.execute("""
                SELECT 
                    customer_number,
                    first_name,
                    family_name,
                    home_street,
                    home_city,
                    zip_code,
                    country_code,
                    birthday
                FROM customers_suppliers
                WHERE customer_number = %s
            """, (customer_number,))
            
            cust_row = loco_cursor.fetchone()
            
            if not cust_row:
                logger.warning(f"Kunde nicht gefunden in customers_suppliers: {customer_number}")
                return changes
            
            cust_dict = row_to_dict(cust_row, loco_cursor)
        
        # Update employees Tabelle
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Private Street
            if overwrite or not emp_dict.get('private_street'):
                if cust_dict.get('home_street') and cust_dict['home_street'] != emp_dict.get('private_street'):
                    changes['private_street'] = {'old': emp_dict.get('private_street'), 'new': cust_dict['home_street']}
                    update_fields.append('private_street = %s')
                    update_values.append(cust_dict['home_street'])
            
            # Private City
            if overwrite or not emp_dict.get('private_city'):
                if cust_dict.get('home_city') and cust_dict['home_city'] != emp_dict.get('private_city'):
                    changes['private_city'] = {'old': emp_dict.get('private_city'), 'new': cust_dict['home_city']}
                    update_fields.append('private_city = %s')
                    update_values.append(cust_dict['home_city'])
            
            # Private Postal Code
            if overwrite or not emp_dict.get('private_postal_code'):
                if cust_dict.get('zip_code') and cust_dict['zip_code'] != emp_dict.get('private_postal_code'):
                    changes['private_postal_code'] = {'old': emp_dict.get('private_postal_code'), 'new': cust_dict['zip_code']}
                    update_fields.append('private_postal_code = %s')
                    update_values.append(cust_dict['zip_code'])
            
            # Private Country
            if overwrite or not emp_dict.get('private_country'):
                if cust_dict.get('country_code'):
                    # Mapping: DE -> Deutschland, etc.
                    country = cust_dict['country_code']
                    if country == 'DE' or not country:
                        country = 'Deutschland'
                    if country != emp_dict.get('private_country'):
                        changes['private_country'] = {'old': emp_dict.get('private_country'), 'new': country}
                        update_fields.append('private_country = %s')
                        update_values.append(country)
            
            # Birthday (wenn noch nicht vorhanden)
            if overwrite or not emp_dict.get('birthday'):
                if cust_dict.get('birthday'):
                    bday = cust_dict['birthday']
                    if isinstance(bday, str):
                        bday = datetime.strptime(bday, '%Y-%m-%d').date()
                    elif hasattr(bday, 'date'):
                        bday = bday.date()
                    
                    current_bday = emp_dict.get('birthday')
                    if current_bday:
                        if isinstance(current_bday, str):
                            current_bday = datetime.strptime(current_bday, '%Y-%m-%d').date()
                        elif hasattr(current_bday, 'date'):
                            current_bday = current_bday.date()
                    
                    if not current_bday or bday != current_bday:
                        changes['birthday'] = {'old': str(current_bday) if current_bday else None, 'new': str(bday)}
                        update_fields.append('birthday = %s')
                        update_values.append(bday)
            
            # Speichere Änderungen
            if update_fields:
                update_values.append(employee_id)
                query = f"UPDATE employees SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(query, update_values)
                conn.commit()
            
            return changes
    
    except Exception as e:
        logger.error(f"Fehler beim Adress-Sync für Kunde {customer_number}: {e}")
        return changes


def _calculate_address_changes(customer_number: int, emp_dict: Dict, overwrite: bool) -> Dict:
    """
    Berechnet Adress-Änderungen aus customers_suppliers (nur Preview, nicht speichern)
    """
    changes = {}
    
    try:
        logger.debug(f"Berechne Adress-Änderungen für customer_number: {customer_number}")
        
        with locosoft_session() as loco_conn:
            loco_cursor = loco_conn.cursor()
            
            loco_cursor.execute("""
                SELECT 
                    customer_number,
                    first_name,
                    family_name,
                    home_street,
                    home_city,
                    zip_code,
                    country_code,
                    birthday
                FROM customers_suppliers
                WHERE customer_number = %s
            """, (customer_number,))
            
            cust_row = loco_cursor.fetchone()
            if not cust_row:
                logger.warning(f"Kunde nicht gefunden in customers_suppliers: {customer_number}")
                return changes
            
            cust_dict = row_to_dict(cust_row, loco_cursor)
            logger.debug(f"Kunden-Daten gefunden: {cust_dict}")
        
        # Private Street
        current_street = emp_dict.get('private_street') or ''
        new_street = cust_dict.get('home_street') or ''
        if overwrite or not current_street:
            if new_street and new_street != current_street:
                changes['private_street'] = {'old': current_street or None, 'new': new_street}
                logger.debug(f"private_street: '{current_street}' -> '{new_street}'")
        
        # Private City
        current_city = emp_dict.get('private_city') or ''
        new_city = cust_dict.get('home_city') or ''
        if overwrite or not current_city:
            if new_city and new_city != current_city:
                changes['private_city'] = {'old': current_city or None, 'new': new_city}
                logger.debug(f"private_city: '{current_city}' -> '{new_city}'")
        
        # Private Postal Code
        current_postal = emp_dict.get('private_postal_code') or ''
        new_postal = cust_dict.get('zip_code') or ''
        if overwrite or not current_postal:
            if new_postal and new_postal != current_postal:
                changes['private_postal_code'] = {'old': current_postal or None, 'new': new_postal}
                logger.debug(f"private_postal_code: '{current_postal}' -> '{new_postal}'")
        
        # Private Country
        current_country = emp_dict.get('private_country') or ''
        if overwrite or not current_country:
            if cust_dict.get('country_code'):
                country = cust_dict['country_code']
                if country == 'DE' or not country:
                    country = 'Deutschland'
                if country != current_country:
                    changes['private_country'] = {'old': current_country or None, 'new': country}
                    logger.debug(f"private_country: '{current_country}' -> '{country}'")
        
        # Birthday
        if overwrite or not emp_dict.get('birthday'):
            if cust_dict.get('birthday'):
                bday = cust_dict['birthday']
                if isinstance(bday, str):
                    bday = datetime.strptime(bday, '%Y-%m-%d').date()
                elif hasattr(bday, 'date'):
                    bday = bday.date()
                
                current_bday = emp_dict.get('birthday')
                if current_bday:
                    if isinstance(current_bday, str):
                        current_bday = datetime.strptime(current_bday, '%Y-%m-%d').date()
                    elif hasattr(current_bday, 'date'):
                        current_bday = current_bday.date()
                
                if not current_bday or bday != current_bday:
                    changes['birthday'] = {'old': str(current_bday) if current_bday else None, 'new': str(bday)}
                    logger.debug(f"birthday: '{current_bday}' -> '{bday}'")
        
        logger.debug(f"Adress-Änderungen berechnet: {len(changes)} Felder")
    
    except Exception as e:
        logger.error(f"Fehler bei Adress-Preview für Kunde {customer_number}: {e}")
    
    return changes


def sync_full(employee_id: int, overwrite: bool = False) -> Dict:
    """
    Vollständiger Sync aus beiden Quellen (LDAP + Locosoft)
    
    Args:
        employee_id: ID des Mitarbeiters
        overwrite: Wenn True, überschreibt auch vorhandene Felder
        
    Returns:
        Dict mit:
            - 'success': bool
            - 'ldap_changes': Dict
            - 'locosoft_changes': Dict
            - 'error': Optional[str]
    """
    try:
        # Hole Mapping-Daten
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    lem.ldap_username,
                    lem.locosoft_id
                FROM ldap_employee_mapping lem
                WHERE lem.employee_id = %s
            """, (employee_id,))
            
            mapping_row = cursor.fetchone()
            
            if not mapping_row:
                return {
                    'success': False,
                    'error': 'Kein LDAP/Locosoft-Mapping gefunden'
                }
            
            mapping_dict = row_to_dict(mapping_row)
            ldap_username = mapping_dict.get('ldap_username')
            locosoft_id = mapping_dict.get('locosoft_id')
        
        result = {
            'success': True,
            'ldap_changes': {},
            'locosoft_changes': {}
        }
        
        # Sync aus LDAP
        if ldap_username:
            ldap_result = sync_from_ldap(employee_id, ldap_username, overwrite)
            if ldap_result['success']:
                result['ldap_changes'] = ldap_result['changes']
            else:
                result['ldap_error'] = ldap_result.get('error')
        
        # Sync aus Locosoft
        if locosoft_id:
            locosoft_result = sync_from_locosoft(employee_id, locosoft_id, overwrite)
            if locosoft_result['success']:
                result['locosoft_changes'] = locosoft_result['changes']
            else:
                result['locosoft_error'] = locosoft_result.get('error')
        
        return result
    
    except Exception as e:
        logger.error(f"Fehler beim vollständigen Sync für Mitarbeiter {employee_id}: {e}")
        import traceback
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }
