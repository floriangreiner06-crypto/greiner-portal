#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vacation API Blueprint
======================
REST-API für Urlaubsplaner V2
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, date
import sqlite3
import sys
from pathlib import Path

# VacationCalculator importieren
sys.path.append(str(Path(__file__).parent.parent))
from vacation_v2.utils.vacation_calculator import VacationCalculator

# Blueprint erstellen
vacation_api = Blueprint('vacation_api', __name__, url_prefix='/api/vacation')

# Hilfsfunktionen
def get_db():
    """DB-Verbindung"""
    conn = sqlite3.connect('data/greiner_controlling.db')
    conn.row_factory = sqlite3.Row
    return conn

def json_response(data, status=200):
    """Standard JSON Response"""
    response = jsonify(data)
    response.status_code = status
    return response

def error_response(message, status=400):
    """Fehler Response"""
    return json_response({'error': message}, status)


# ============================================================================
# ENDPOINTS - Urlaubssaldo
# ============================================================================

@vacation_api.route('/balance/<int:employee_id>', methods=['GET'])
def get_vacation_balance(employee_id):
    """
    GET /api/vacation/balance/:employee_id
    
    Gibt Urlaubssaldo für einen Mitarbeiter zurück
    
    Query-Parameter:
    - year (optional): Jahr (default: aktuelles Jahr)
    
    Response:
    {
        "employee_id": 1,
        "year": 2025,
        "anspruch": 30.0,
        "verbraucht": 5.0,
        "geplant": 3.0,
        "resturlaub": 22.0
    }
    """
    year = request.args.get('year', datetime.now().year, type=int)
    
    calc = VacationCalculator()
    balance = calc.get_vacation_balance(employee_id, year)
    
    return json_response({
        'employee_id': employee_id,
        **balance
    })


@vacation_api.route('/balance', methods=['GET'])
def get_all_balances():
    """
    GET /api/vacation/balance
    
    Gibt Urlaubssalden für alle Mitarbeiter zurück
    
    Query-Parameter:
    - year (optional): Jahr (default: 2025)
    - department (optional): Filter nach Abteilung
    """
    year = request.args.get('year', 2025, type=int)
    department = request.args.get('department', None)
    
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
    """
    
    if department:
        query += " WHERE department_name = ?"
        cursor.execute(query, (department,))
    else:
        cursor.execute(query)
    
    balances = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return json_response({
        'year': year,
        'count': len(balances),
        'balances': balances
    })


# ============================================================================
# ENDPOINTS - Urlaubsanträge
# ============================================================================

@vacation_api.route('/request', methods=['POST'])
def create_vacation_request():
    """
    POST /api/vacation/request
    
    Erstellt einen neuen Urlaubsantrag
    
    Request Body:
    {
        "employee_id": 1,
        "start_date": "2025-07-01",
        "end_date": "2025-07-14",
        "vacation_type_id": 1,
        "comment": "Sommerurlaub"
    }
    
    Response:
    {
        "success": true,
        "request_id": "...",
        "working_days": 10,
        "bookings": [...]
    }
    """
    data = request.get_json()
    
    # Validierung
    required = ['employee_id', 'start_date', 'end_date']
    for field in required:
        if field not in data:
            return error_response(f"Pflichtfeld fehlt: {field}")
    
    try:
        employee_id = data['employee_id']
        start_date = date.fromisoformat(data['start_date'])
        end_date = date.fromisoformat(data['end_date'])
        vacation_type_id = data.get('vacation_type_id', 1)
        comment = data.get('comment', '')
        
        # VacationCalculator Validierung
        calc = VacationCalculator()
        is_valid, message, details = calc.validate_vacation_request(
            employee_id, start_date, end_date, vacation_type_id
        )
        
        if not is_valid:
            return error_response(message, 400)
        
        # Buchungen generieren
        bookings = calc.request_to_bookings(start_date, end_date, vacation_type_id)
        
        # In DB speichern
        conn = get_db()
        cursor = conn.cursor()
        
        created_at = datetime.now().isoformat()
        booking_ids = []
        
        for booking in bookings:
            cursor.execute("""
                INSERT INTO vacation_bookings 
                (employee_id, booking_date, vacation_type_id, day_part, 
                 status, comment, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?, ?)
            """, (employee_id, booking['booking_date'], booking['vacation_type_id'],
                  booking['day_part'], comment, created_at))
            
            booking_ids.append(cursor.lastrowid)
        
        conn.commit()
        conn.close()
        
        return json_response({
            'success': True,
            'message': 'Urlaubsantrag erstellt',
            'working_days': len(bookings),
            'booking_ids': booking_ids,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }, 201)
        
    except ValueError as e:
        return error_response(f"Ungültiges Datum: {e}")
    except Exception as e:
        return error_response(f"Fehler: {e}", 500)


@vacation_api.route('/requests', methods=['GET'])
def get_vacation_requests():
    """
    GET /api/vacation/requests
    
    Listet Urlaubsanträge
    
    Query-Parameter:
    - employee_id (optional): Filter nach Mitarbeiter
    - status (optional): Filter nach Status (pending, approved, rejected)
    - year (optional): Filter nach Jahr
    """
    employee_id = request.args.get('employee_id', type=int)
    status = request.args.get('status')
    year = request.args.get('year', type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            vb.id,
            vb.employee_id,
            e.first_name || ' ' || e.last_name as employee_name,
            vb.booking_date,
            vb.vacation_type_id,
            vt.name as vacation_type,
            vb.day_part,
            vb.status,
            vb.comment,
            vb.created_at
        FROM vacation_bookings vb
        JOIN employees e ON vb.employee_id = e.id
        JOIN vacation_types vt ON vb.vacation_type_id = vt.id
        WHERE 1=1
    """
    
    params = []
    
    if employee_id:
        query += " AND vb.employee_id = ?"
        params.append(employee_id)
    
    if status:
        query += " AND vb.status = ?"
        params.append(status)
    
    if year:
        query += " AND strftime('%Y', vb.booking_date) = ?"
        params.append(str(year))
    
    query += " ORDER BY vb.booking_date DESC LIMIT 100"
    
    cursor.execute(query, params)
    requests = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return json_response({
        'count': len(requests),
        'requests': requests
    })


@vacation_api.route('/request/<int:booking_id>', methods=['DELETE'])
def cancel_vacation_request(booking_id):
    """
    DELETE /api/vacation/request/:id
    
    Storniert einen Urlaubsantrag (nur Status: pending)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Prüfe Status
    cursor.execute("SELECT status FROM vacation_bookings WHERE id = ?", (booking_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return error_response("Buchung nicht gefunden", 404)
    
    if row['status'] != 'pending':
        conn.close()
        return error_response("Nur pending-Anträge können storniert werden", 400)
    
    # Lösche
    cursor.execute("DELETE FROM vacation_bookings WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()
    
    return json_response({
        'success': True,
        'message': 'Urlaubsantrag storniert'
    })


# ============================================================================
# ENDPOINTS - Team-Kalender
# ============================================================================

@vacation_api.route('/calendar', methods=['GET'])
def get_team_calendar():
    """
    GET /api/vacation/calendar
    
    Team-Kalender für einen Zeitraum
    
    Query-Parameter:
    - start_date (required): Startdatum (YYYY-MM-DD)
    - end_date (required): Enddatum (YYYY-MM-DD)
    - department (optional): Filter nach Abteilung
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    department = request.args.get('department')
    
    if not start_date or not end_date:
        return error_response("start_date und end_date erforderlich")
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT *
        FROM v_team_calendar
        WHERE booking_date BETWEEN ? AND ?
    """
    
    params = [start_date, end_date]
    
    if department:
        query += " AND department_name = ?"
        params.append(department)
    
    query += " ORDER BY booking_date, employee_name"
    
    cursor.execute(query, params)
    calendar = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return json_response({
        'start_date': start_date,
        'end_date': end_date,
        'count': len(calendar),
        'calendar': calendar
    })


# ============================================================================
# HEALTH CHECK
# ============================================================================

@vacation_api.route('/health', methods=['GET'])
def health_check():
    """API Health Check"""
    return json_response({
        'status': 'healthy',
        'version': '2.0',
        'timestamp': datetime.now().isoformat()
    })
