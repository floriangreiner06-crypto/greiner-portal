#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
VACATION API - MIT LDAP-INTEGRATION
========================================
Version: 2.2 - TAG 69 FINAL
Datum: 20.11.2025

Features:
- /my-balance: Persönlicher Urlaubsstand (aus LDAP-Session)
- /my-team: Team-Übersicht für Manager
- /balance: Alle Mitarbeiter (Admin/HR)
- /my-bookings: Eigene Urlaubsbuchungen
- /requests: Urlaubsanträge (für JavaScript-Kompatibilität)
- /book: Urlaubsbuchungen verwalten

FIXES TAG 69:
- get_employee_from_session() verwendet jetzt _user_id aus Flask-Login Session
- notes → comment (DB-Spalten-Name korrigiert)
"""

from flask import Blueprint, request, jsonify, session
import sqlite3
from datetime import datetime, date
import json

vacation_api = Blueprint('vacation_api', __name__, url_prefix='/api/vacation')

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

def get_db():
    """Erstellt DB-Verbindung"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_employee_from_session():
    """
    Holt employee_id aus Flask-Login Session via ldap_employee_mapping
    
    Verwendet _user_id aus Flask-Login Session, holt dann username aus users Tabelle,
    und matched gegen ldap_employee_mapping.
    
    Returns:
        tuple: (employee_id, ldap_username, employee_data) oder (None, None, None)
    """
    # 1. Hole user_id aus Flask-Login Session
    user_id = session.get('_user_id')
    
    if not user_id:
        # Fallback: Versuche alte Session-Keys
        ldap_username = (
            session.get('username') or 
            session.get('user') or 
            session.get('ldap_user') or
            session.get('sAMAccountName')
        )
        
        if not ldap_username:
            return None, None, None
        
        # Normalisiere (entferne @domain falls vorhanden)
        ldap_username = ldap_username.split('@')[0] if '@' in ldap_username else ldap_username
    else:
        # 2. Hole username aus users Tabelle
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            conn.close()
            return None, None, None
        
        username = user_row[0]  # z.B. "christian.aichinger@auto-greiner.de"
        
        # 3. Normalisiere zu ldap_username (ohne @domain)
        ldap_username = username.split('@')[0] if '@' in username else username
        
        conn.close()
    
    # 4. Lookup in ldap_employee_mapping
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            lem.employee_id,
            lem.ldap_username,
            lem.locosoft_id,
            e.first_name,
            e.last_name,
            e.email,
            e.department_name,
            e.is_manager
        FROM ldap_employee_mapping lem
        JOIN employees e ON lem.employee_id = e.id
        WHERE lem.ldap_username = ? AND e.aktiv = 1
    """, (ldap_username,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        employee_data = {
            'employee_id': result[0],
            'ldap_username': result[1],
            'locosoft_id': result[2],
            'first_name': result[3],
            'last_name': result[4],
            'email': result[5],
            'department': result[6],
            'is_manager': bool(result[7])
        }
        return result[0], ldap_username, employee_data
    
    return None, ldap_username, None


# ============================================================================
# ROUTES
# ============================================================================

@vacation_api.route('/health', methods=['GET'])
def health_check():
    """Health Check"""
    return jsonify({
        'status': 'ok',
        'service': 'vacation-api',
        'version': '2.2',
        'timestamp': datetime.now().isoformat()
    })


@vacation_api.route('/my-balance', methods=['GET'])
def get_my_balance():
    """
    GET /api/vacation/my-balance
    
    Gibt Urlaubssaldo für den ANGEMELDETEN User zurück
    Holt employee_id automatisch aus LDAP-Session
    
    Query-Parameter:
    - year (optional): Jahr (default: 2025)
    
    Response:
    {
        "success": true,
        "year": 2025,
        "ldap_username": "anton.suess",
        "balance": {
            "employee_id": 67,
            "name": "Anton Süß",
            "department": "Verkauf",
            "location": "Unbekannt",
            "anspruch": 30.0,
            "verbraucht": 0,
            "geplant": 2.0,
            "resturlaub": 30.0
        }
    }
    """
    try:
        employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not employee_id:
            return jsonify({
                'success': False,
                'error': 'Nicht angemeldet oder kein LDAP-Mapping',
                'hint': 'Bitte über LDAP anmelden',
                'debug': {
                    'session_keys': list(session.keys()),
                    'ldap_username': ldap_username
                }
            }), 401
        
        year = request.args.get('year', 2025, type=int)
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT
                employee_id,
                name,
                department_name,
                location,
                anspruch,
                verbraucht,
                geplant,
                resturlaub
            FROM v_vacation_balance_{year}
            WHERE employee_id = ?
        """, (employee_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({
                'success': False,
                'error': f'Keine Urlaubsdaten für {year}',
                'employee_id': employee_id
            }), 404
        
        balance = {
            'employee_id': row[0],
            'name': row[1],
            'department': row[2],
            'location': row[3],
            'anspruch': row[4],
            'verbraucht': row[5],
            'geplant': row[6],
            'resturlaub': row[7]
        }
        
        return jsonify({
            'success': True,
            'year': year,
            'ldap_username': ldap_username,
            'employee': employee_data,
            'balance': balance
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_api.route('/my-team', methods=['GET'])
def get_my_team():
    """
    GET /api/vacation/my-team
    
    Gibt Urlaubssalden für das Team des angemeldeten Managers zurück
    
    Query-Parameter:
    - year (optional): Jahr (default: 2025)
    
    Nur für Manager zugänglich!
    """
    try:
        employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not employee_id:
            return jsonify({
                'success': False,
                'error': 'Nicht angemeldet'
            }), 401
        
        # Prüfen ob Manager
        if not employee_data.get('is_manager'):
            return jsonify({
                'success': False,
                'error': 'Zugriff verweigert - keine Manager-Berechtigung'
            }), 403
        
        year = request.args.get('year', 2025, type=int)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Team-Mitglieder holen
        cursor.execute(f"""
            SELECT
                vb.employee_id,
                vb.name,
                vb.department_name,
                vb.location,
                vb.anspruch,
                vb.verbraucht,
                vb.geplant,
                vb.resturlaub
            FROM v_vacation_balance_{year} vb
            JOIN manager_assignments ma ON vb.employee_id = ma.employee_id
            WHERE ma.manager_id = ?
              AND (ma.valid_to IS NULL OR ma.valid_to >= date('now'))
            ORDER BY vb.name
        """, (employee_id,))
        
        team = []
        for row in cursor.fetchall():
            team.append({
                'employee_id': row[0],
                'name': row[1],
                'department': row[2],
                'location': row[3],
                'anspruch': row[4],
                'verbraucht': row[5],
                'geplant': row[6],
                'resturlaub': row[7]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'year': year,
            'manager': employee_data,
            'team_count': len(team),
            'team': team
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_api.route('/balance', methods=['GET'])
def get_all_balances():
    """
    GET /api/vacation/balance
    
    Gibt Urlaubssalden für alle Mitarbeiter zurück
    
    Query-Parameter:
    - year (optional): Jahr (default: 2025)
    - department (optional): Filter nach Abteilung
    - location (optional): Filter nach Standort
    
    Für HR/Admin gedacht - zeigt alle Mitarbeiter
    """
    try:
        year = request.args.get('year', 2025, type=int)
        department = request.args.get('department', None)
        location = request.args.get('location', None)
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = f"""
            SELECT
                employee_id,
                name,
                department_name,
                location,
                anspruch,
                verbraucht,
                geplant,
                resturlaub
            FROM v_vacation_balance_{year}
            WHERE 1=1
        """
        
        params = []
        
        if department:
            query += " AND department_name = ?"
            params.append(department)
        
        if location:
            query += " AND location = ?"
            params.append(location)
        
        query += " ORDER BY name"
        
        cursor.execute(query, params)
        
        balances = []
        for row in cursor.fetchall():
            balances.append({
                'employee_id': row[0],
                'name': row[1],
                'department_name': row[2],
                'location': row[3],
                'anspruch': row[4],
                'verbraucht': row[5],
                'geplant': row[6],
                'resturlaub': row[7]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'year': year,
            'count': len(balances),
            'filters': {
                'department': department,
                'location': location
            },
            'balances': balances
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_api.route('/my-bookings', methods=['GET'])
def get_my_bookings():
    """
    GET /api/vacation/my-bookings
    
    Gibt alle Urlaubsbuchungen des angemeldeten Users zurück
    
    Query-Parameter:
    - year (optional): Jahr (default: 2025)
    - status (optional): Filter nach Status (pending/approved/rejected)
    """
    try:
        employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not employee_id:
            return jsonify({
                'success': False,
                'error': 'Nicht angemeldet'
            }), 401
        
        year = request.args.get('year', 2025, type=int)
        status_filter = request.args.get('status', None)
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = """
            SELECT
                vb.id,
                vb.booking_date,
                vb.day_part,
                vb.status,
                vb.vacation_type_id,
                vt.name as vacation_type_name,
                vb.comment,
                vb.created_at
            FROM vacation_bookings vb
            LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
            WHERE vb.employee_id = ?
              AND strftime('%Y', vb.booking_date) = ?
        """
        
        params = [employee_id, str(year)]
        
        if status_filter:
            query += " AND vb.status = ?"
            params.append(status_filter)
        
        query += " ORDER BY vb.booking_date DESC"
        
        cursor.execute(query, params)
        
        bookings = []
        for row in cursor.fetchall():
            bookings.append({
                'id': row[0],
                'date': row[1],
                'day_part': row[2],
                'status': row[3],
                'type_id': row[4],
                'type_name': row[5],
                'comment': row[6],
                'created_at': row[7]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'year': year,
            'employee': employee_data,
            'count': len(bookings),
            'bookings': bookings
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_api.route('/requests', methods=['GET'])
def get_requests():
    """
    GET /api/vacation/requests
    
    Gibt Urlaubsanträge zurück (für Manager/Admin oder spezifischen Mitarbeiter)
    
    Query-Parameter:
    - employee_id (optional): Mitarbeiter-ID (falls nicht angegeben: aktueller User)
    - year (optional): Jahr (default: 2025)
    - status (optional): Filter nach Status (pending/approved/rejected)
    
    HINWEIS: Dieser Endpoint ist für JavaScript-Kompatibilität gedacht.
    Er gibt die gleichen Daten zurück wie /my-bookings, nur mit "requests" statt "bookings".
    """
    try:
        # Aktuellen User aus Session holen
        current_employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not current_employee_id:
            return jsonify({
                'success': False,
                'error': 'Nicht angemeldet'
            }), 401
        
        # employee_id aus Query-Parameter (optional)
        requested_employee_id = request.args.get('employee_id', None, type=int)
        
        # Wenn employee_id angegeben: verwende diese, sonst aktuellen User
        employee_id = requested_employee_id if requested_employee_id else current_employee_id
        
        # Prüfe ob User berechtigt ist (entweder eigene Daten oder Manager)
        if employee_id != current_employee_id:
            # Prüfe ob Manager
            if not employee_data or not employee_data.get('is_manager'):
                return jsonify({
                    'success': False,
                    'error': 'Keine Berechtigung - nur Manager können andere Mitarbeiter abfragen'
                }), 403
        
        year = request.args.get('year', 2025, type=int)
        status_filter = request.args.get('status', None)
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = """
            SELECT
                vb.id,
                vb.booking_date,
                vb.day_part,
                vb.status,
                vb.vacation_type_id,
                vt.name as vacation_type_name,
                vb.comment,
                vb.created_at
            FROM vacation_bookings vb
            LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
            WHERE vb.employee_id = ?
              AND strftime('%Y', vb.booking_date) = ?
        """
        
        params = [employee_id, str(year)]
        
        if status_filter:
            query += " AND vb.status = ?"
            params.append(status_filter)
        
        query += " ORDER BY vb.booking_date DESC"
        
        cursor.execute(query, params)
        
        requests = []
        for row in cursor.fetchall():
            requests.append({
                'id': row[0],
                'date': row[1],
                'day_part': row[2],
                'status': row[3],
                'type_id': row[4],
                'type_name': row[5],
                'comment': row[6],
                'created_at': row[7]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'year': year,
            'employee_id': employee_id,
            'count': len(requests),
            'requests': requests
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_api.route('/book', methods=['POST'])
def book_vacation():
    """
    POST /api/vacation/book
    
    Bucht Urlaub für den angemeldeten User
    
    Body:
    {
        "date": "2025-12-24",
        "day_part": "full",  // oder "half"
        "vacation_type_id": 1,
        "comment": "optional"
    }
    """
    try:
        employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not employee_id:
            return jsonify({
                'success': False,
                'error': 'Nicht angemeldet'
            }), 401
        
        data = request.get_json()
        
        if not data or 'date' not in data:
            return jsonify({
                'success': False,
                'error': 'Fehlende Daten: date erforderlich'
            }), 400
        
        booking_date = data['date']
        day_part = data.get('day_part', 'full')
        vacation_type_id = data.get('vacation_type_id', 1)
        comment = data.get('comment', None)
        
        # Validierung
        try:
            datetime.strptime(booking_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Ungültiges Datumsformat (erwartet: YYYY-MM-DD)'
            }), 400
        
        if day_part not in ['full', 'half']:
            return jsonify({
                'success': False,
                'error': 'day_part muss "full" oder "half" sein'
            }), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Prüfe ob bereits Buchung existiert
        cursor.execute("""
            SELECT id FROM vacation_bookings
            WHERE employee_id = ? AND booking_date = ?
        """, (employee_id, booking_date))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Für {booking_date} existiert bereits eine Buchung'
            }), 400
        
        # Buchung einfügen
        cursor.execute("""
            INSERT INTO vacation_bookings (
                employee_id, booking_date, vacation_type_id,
                day_part, status, comment, created_at
            ) VALUES (?, ?, ?, ?, 'pending', ?, ?)
        """, (employee_id, booking_date, vacation_type_id, day_part, comment, datetime.now().isoformat()))
        
        booking_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'booking_id': booking_id,
            'message': 'Urlaubsantrag eingereicht (Status: pending)',
            'booking': {
                'id': booking_id,
                'date': booking_date,
                'day_part': day_part,
                'status': 'pending'
            }
        }), 201
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_api.route('/debug/session', methods=['GET'])
def debug_session():
    """
    GET /api/vacation/debug/session
    
    Debug-Endpoint: Zeigt Session-Daten und LDAP-Mapping
    NUR FÜR DEVELOPMENT!
    """
    employee_id, ldap_username, employee_data = get_employee_from_session()
    
    return jsonify({
        'session': dict(session),
        'ldap_username': ldap_username,
        'employee_id': employee_id,
        'employee_data': employee_data,
        'timestamp': datetime.now().isoformat()
    })


# Export Blueprint
__all__ = ['vacation_api']
