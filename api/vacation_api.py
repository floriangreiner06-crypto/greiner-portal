#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
VACATION API - MIT LDAP-INTEGRATION
========================================
Version: 2.4 - TAG 104
Datum: 08.12.2025

Features:
- /my-balance: Persönlicher Urlaubsstand (aus LDAP-Session)
- /my-team: Team-Übersicht für Genehmiger (basiert auf vacation_approval_rules)
- /my-approvers: Wer genehmigt meinen Urlaub?
- /approver-summary: Genehmiger-Dashboard-Daten
- /balance: Alle Mitarbeiter (Admin/HR)
- /my-bookings: Eigene Urlaubsbuchungen
- /requests: Urlaubsanträge (für JavaScript-Kompatibilität)
- /pending-approvals: Offene Genehmigungen für Genehmiger
- /book: Urlaubsbuchungen verwalten
- /approve: Urlaub genehmigen (NEU: mit E-Mail an HR + Kalender)
- /reject: Urlaub ablehnen (NEU: mit E-Mail an Mitarbeiter)

CHANGES TAG 104:
- E-Mail-Workflow bei Genehmigung/Ablehnung
- Outlook Team-Kalender Integration
- Graph API Integration für E-Mails und Kalender
"""

from flask import Blueprint, request, jsonify, session
import sqlite3
from datetime import datetime, date, timedelta
import json

# Approver Service importieren
from api.vacation_approver_service import (
    get_approvers_for_employee,
    get_team_for_approver,
    is_approver,
    get_approver_summary
)

# Locosoft Abwesenheits-Service (TAG 103)
try:
    from api.vacation_locosoft_service import (
        get_absences_for_employee,
        get_absences_for_employees
    )
    LOCOSOFT_AVAILABLE = True
except ImportError:
    LOCOSOFT_AVAILABLE = False
    print("⚠️ vacation_locosoft_service nicht verfügbar")

# Graph Mail Connector für E-Mails und Kalender (TAG 104)
try:
    from api.graph_mail_connector import GraphMailConnector
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False
    print("⚠️ graph_mail_connector nicht verfügbar")

# Vacation Calendar Service (TAG 104)
try:
    from api.vacation_calendar_service import VacationCalendarService
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False
    print("⚠️ vacation_calendar_service nicht verfügbar")

vacation_api = Blueprint('vacation_api', __name__, url_prefix='/api/vacation')

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

# E-Mail-Konfiguration
HR_EMAIL = 'hr@auto-greiner.de'  # HR-Mailbox für Locosoft-Einträge
DRIVE_EMAIL = 'drive@auto-greiner.de'  # Absender

def get_db():
    """Erstellt DB-Verbindung"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_employee_from_session():
    """
    Holt employee_id aus Flask-Login Session via ldap_employee_mapping
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
        
        ldap_username = ldap_username.split('@')[0] if '@' in ldap_username else ldap_username
    else:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            conn.close()
            return None, None, None
        
        username = user_row[0]
        ldap_username = username.split('@')[0] if '@' in username else username
        conn.close()
    
    # Lookup in ldap_employee_mapping
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
# E-MAIL HELPER FUNKTIONEN (TAG 104)
# ============================================================================

def send_approval_email_to_hr(booking_details: dict, approver_name: str):
    """
    Sendet E-Mail an HR wenn Urlaub genehmigt wurde.
    HR soll den Urlaub in Locosoft eintragen.
    """
    if not GRAPH_AVAILABLE:
        print("⚠️ Graph nicht verfügbar - keine E-Mail gesendet")
        return False
    
    try:
        graph = GraphMailConnector()
        
        # Formatiere Datum schön
        booking_date = booking_details.get('date', '')
        try:
            date_obj = datetime.strptime(booking_date, '%Y-%m-%d')
            date_formatted = date_obj.strftime('%d.%m.%Y')
            weekday = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'][date_obj.weekday()]
        except:
            date_formatted = booking_date
            weekday = ''
        
        employee_name = booking_details.get('employee_name', 'Unbekannt')
        vacation_type = booking_details.get('vacation_type', 'Urlaub')
        day_part = 'Ganzer Tag' if booking_details.get('day_part') == 'full' else 'Halber Tag'
        department = booking_details.get('department', '')
        
        subject = f"✅ Urlaub genehmigt: {employee_name} - {date_formatted}"
        
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px;">
            <h2 style="color: #28a745;">✅ Urlaubsantrag genehmigt</h2>
            
            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <tr style="background: #f8f9fa;">
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Mitarbeiter</td>
                    <td style="padding: 10px; border: 1px solid #dee2e6;">{employee_name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Abteilung</td>
                    <td style="padding: 10px; border: 1px solid #dee2e6;">{department}</td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Datum</td>
                    <td style="padding: 10px; border: 1px solid #dee2e6;">{weekday}, {date_formatted}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Art</td>
                    <td style="padding: 10px; border: 1px solid #dee2e6;">{vacation_type}</td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Umfang</td>
                    <td style="padding: 10px; border: 1px solid #dee2e6;">{day_part}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Genehmigt von</td>
                    <td style="padding: 10px; border: 1px solid #dee2e6;">{approver_name}</td>
                </tr>
            </table>
            
            <p style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                <strong>📋 Aktion erforderlich:</strong><br>
                Bitte diesen Urlaub in <strong>Locosoft</strong> eintragen.
            </p>
            
            <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
            <p style="color: #6c757d; font-size: 12px;">
                Diese E-Mail wurde automatisch vom Greiner DRIVE Portal gesendet.
            </p>
        </div>
        """
        
        result = graph.send_mail(
            sender_email=DRIVE_EMAIL,
            to_emails=[HR_EMAIL],
            subject=subject,
            body_html=body_html
        )
        
        if result:
            print(f"✅ HR-E-Mail gesendet für {employee_name} ({booking_date})")
        return result
        
    except Exception as e:
        print(f"❌ Fehler beim Senden der HR-E-Mail: {e}")
        return False


def send_approval_notification_to_employee(booking_details: dict, approver_name: str):
    """
    Sendet Bestätigungs-E-Mail an Mitarbeiter wenn Urlaub genehmigt wurde.
    """
    if not GRAPH_AVAILABLE:
        return False
    
    employee_email = booking_details.get('employee_email')
    if not employee_email:
        return False
    
    try:
        graph = GraphMailConnector()
        
        booking_date = booking_details.get('date', '')
        try:
            date_obj = datetime.strptime(booking_date, '%Y-%m-%d')
            date_formatted = date_obj.strftime('%d.%m.%Y')
        except:
            date_formatted = booking_date
        
        vacation_type = booking_details.get('vacation_type', 'Urlaub')
        
        subject = f"✅ Dein {vacation_type} wurde genehmigt - {date_formatted}"
        
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px;">
            <h2 style="color: #28a745;">✅ {vacation_type} genehmigt!</h2>
            
            <p>Dein Antrag für <strong>{date_formatted}</strong> wurde von <strong>{approver_name}</strong> genehmigt.</p>
            
            <p style="background: #d4edda; padding: 15px; border-radius: 5px;">
                Der Eintrag wird von HR in Locosoft übernommen.
            </p>
            
            <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
            <p style="color: #6c757d; font-size: 12px;">
                Greiner DRIVE Portal
            </p>
        </div>
        """
        
        return graph.send_mail(
            sender_email=DRIVE_EMAIL,
            to_emails=[employee_email],
            subject=subject,
            body_html=body_html
        )
        
    except Exception as e:
        print(f"❌ Fehler beim Senden der Mitarbeiter-E-Mail: {e}")
        return False


def send_rejection_notification(booking_details: dict, approver_name: str, reason: str):
    """
    Sendet E-Mail an Mitarbeiter wenn Urlaub abgelehnt wurde.
    """
    if not GRAPH_AVAILABLE:
        return False
    
    employee_email = booking_details.get('employee_email')
    if not employee_email:
        return False
    
    try:
        graph = GraphMailConnector()
        
        booking_date = booking_details.get('date', '')
        try:
            date_obj = datetime.strptime(booking_date, '%Y-%m-%d')
            date_formatted = date_obj.strftime('%d.%m.%Y')
        except:
            date_formatted = booking_date
        
        vacation_type = booking_details.get('vacation_type', 'Urlaub')
        
        subject = f"❌ {vacation_type} abgelehnt - {date_formatted}"
        
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px;">
            <h2 style="color: #dc3545;">❌ {vacation_type} abgelehnt</h2>
            
            <p>Dein Antrag für <strong>{date_formatted}</strong> wurde von <strong>{approver_name}</strong> abgelehnt.</p>
            
            <p style="background: #f8d7da; padding: 15px; border-radius: 5px;">
                <strong>Begründung:</strong><br>
                {reason}
            </p>
            
            <p>Bei Fragen wende dich bitte an deinen Vorgesetzten.</p>
            
            <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
            <p style="color: #6c757d; font-size: 12px;">
                Greiner DRIVE Portal
            </p>
        </div>
        """
        
        return graph.send_mail(
            sender_email=DRIVE_EMAIL,
            to_emails=[employee_email],
            subject=subject,
            body_html=body_html
        )
        
    except Exception as e:
        print(f"❌ Fehler beim Senden der Ablehnungs-E-Mail: {e}")
        return False


def add_to_team_calendar(booking_details: dict):
    """
    Fügt genehmigten Urlaub zum Team-Kalender hinzu.
    """
    if not CALENDAR_AVAILABLE:
        return False
    
    try:
        calendar_service = VacationCalendarService()
        return calendar_service.add_vacation_event(booking_details)
    except Exception as e:
        print(f"❌ Fehler beim Kalender-Eintrag: {e}")
        return False


def send_cancellation_notification_to_approvers(booking_details: dict, approvers: list, reason: str, was_approved: bool):
    """
    Sendet E-Mail an Genehmiger wenn ein Urlaubsantrag storniert wurde.
    """
    if not GRAPH_AVAILABLE:
        return False
    
    if not approvers:
        return False
    
    try:
        graph = GraphMailConnector()
        
        booking_date = booking_details.get('date', '')
        try:
            date_obj = datetime.strptime(booking_date, '%Y-%m-%d')
            date_formatted = date_obj.strftime('%d.%m.%Y')
        except:
            date_formatted = booking_date
        
        employee_name = booking_details.get('employee_name', 'Unbekannt')
        vacation_type = booking_details.get('vacation_type', 'Urlaub')
        
        status_text = "genehmigten" if was_approved else "beantragten"
        subject = f"🚫 {vacation_type} storniert: {employee_name} - {date_formatted}"
        
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px;">
            <h2 style="color: #dc3545;">🚫 {vacation_type} storniert</h2>
            
            <p><strong>{employee_name}</strong> hat den {status_text} {vacation_type} für <strong>{date_formatted}</strong> storniert.</p>
            
            <p style="background: #f8d7da; padding: 15px; border-radius: 5px;">
                <strong>Grund:</strong> {reason}
            </p>
            
            <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
            <p style="color: #6c757d; font-size: 12px;">
                Greiner DRIVE Portal - Automatische Benachrichtigung
            </p>
        </div>
        """
        
        approver_emails = [a.get('approver_email') for a in approvers if a.get('approver_email') and a.get('priority') == 1]
        if not approver_emails:
            approver_emails = [a.get('approver_email') for a in approvers if a.get('approver_email')]
        
        if not approver_emails:
            return False
        
        return graph.send_mail(
            sender_email=DRIVE_EMAIL,
            to_emails=approver_emails,
            subject=subject,
            body_html=body_html
        )
        
    except Exception as e:
        print(f"❌ Fehler beim Senden der Stornierungs-E-Mail: {e}")
        return False


def send_cancellation_email_to_hr(booking_details: dict, employee_name: str, reason: str):
    """
    Sendet E-Mail an HR wenn ein bereits genehmigter Urlaub storniert wurde.
    HR muss den Eintrag in Locosoft löschen.
    """
    if not GRAPH_AVAILABLE:
        return False
    
    try:
        graph = GraphMailConnector()
        
        booking_date = booking_details.get('date', '')
        try:
            date_obj = datetime.strptime(booking_date, '%Y-%m-%d')
            date_formatted = date_obj.strftime('%d.%m.%Y')
        except:
            date_formatted = booking_date
        
        vacation_type = booking_details.get('vacation_type', 'Urlaub')
        department = booking_details.get('department', '')
        
        subject = f"🚫 STORNO: {employee_name} - {date_formatted}"
        
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px;">
            <h2 style="color: #dc3545;">🚫 Genehmigter Urlaub storniert</h2>
            
            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <tr style="background: #f8f9fa;">
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Mitarbeiter</td>
                    <td style="padding: 10px; border: 1px solid #dee2e6;">{employee_name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Abteilung</td>
                    <td style="padding: 10px; border: 1px solid #dee2e6;">{department}</td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Datum</td>
                    <td style="padding: 10px; border: 1px solid #dee2e6;">{date_formatted}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Art</td>
                    <td style="padding: 10px; border: 1px solid #dee2e6;">{vacation_type}</td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Grund</td>
                    <td style="padding: 10px; border: 1px solid #dee2e6;">{reason}</td>
                </tr>
            </table>
            
            <p style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                <strong>📋 Aktion erforderlich:</strong><br>
                Bitte diesen Eintrag in <strong>Locosoft löschen</strong>.
            </p>
            
            <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
            <p style="color: #6c757d; font-size: 12px;">
                Greiner DRIVE Portal - Automatische Benachrichtigung
            </p>
        </div>
        """
        
        return graph.send_mail(
            sender_email=DRIVE_EMAIL,
            to_emails=[HR_EMAIL],
            subject=subject,
            body_html=body_html
        )
        
    except Exception as e:
        print(f"❌ Fehler beim Senden der HR-Storno-E-Mail: {e}")
        return False


def send_new_request_notification_to_approvers(booking_details: dict, approvers: list):
    """Sendet E-Mail an Genehmiger wenn ein neuer Urlaubsantrag eingegangen ist."""
    if not GRAPH_AVAILABLE:
        return False
    if not approvers:
        return False
    
    try:
        graph = GraphMailConnector()
        
        booking_date = booking_details.get('date', '')
        try:
            date_obj = datetime.strptime(booking_date, '%Y-%m-%d')
            date_formatted = date_obj.strftime('%d.%m.%Y')
            weekday = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'][date_obj.weekday()]
        except:
            date_formatted = booking_date
            weekday = ''
        
        employee_name = booking_details.get('employee_name', 'Unbekannt')
        vacation_type = booking_details.get('vacation_type', 'Urlaub')
        day_part = 'Ganzer Tag' if booking_details.get('day_part') == 'full' else 'Halber Tag'
        department = booking_details.get('department', '')
        comment = booking_details.get('comment', '')
        
        type_icons = {'Urlaub': '🏖️', 'Zeitausgleich': '⏰', 'Krankheit': '🤒', 'Schulung': '📚', 'Sonderurlaub': '👶', 'Arzttermin': '🏥'}
        icon = type_icons.get(vacation_type, '📅')
        
        subject = f"📋 Neuer Urlaubsantrag: {employee_name} - {date_formatted}"
        
        comment_row = f'<tr><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Kommentar</td><td style="padding: 10px; border: 1px solid #dee2e6;">{comment}</td></tr>' if comment else ''
        
        body_html = f"""<div style="font-family: Arial, sans-serif; max-width: 600px;">
            <h2 style="color: #007bff;">{icon} Neuer Urlaubsantrag</h2>
            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <tr style="background: #f8f9fa;"><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Mitarbeiter</td><td style="padding: 10px; border: 1px solid #dee2e6;">{employee_name}</td></tr>
                <tr><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Abteilung</td><td style="padding: 10px; border: 1px solid #dee2e6;">{department}</td></tr>
                <tr style="background: #f8f9fa;"><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Datum</td><td style="padding: 10px; border: 1px solid #dee2e6;">{weekday}, {date_formatted}</td></tr>
                <tr><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Art</td><td style="padding: 10px; border: 1px solid #dee2e6;">{vacation_type}</td></tr>
                <tr style="background: #f8f9fa;"><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Umfang</td><td style="padding: 10px; border: 1px solid #dee2e6;">{day_part}</td></tr>
                {comment_row}
            </table>
            <p style="background: #cce5ff; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;">
                <strong>📋 Aktion erforderlich:</strong><br>
                Bitte im <a href="https://drive.auto-greiner.de/urlaubsplaner">Greiner DRIVE Portal</a> genehmigen oder ablehnen.
            </p>
            <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
            <p style="color: #6c757d; font-size: 12px;">Diese E-Mail wurde automatisch vom Greiner DRIVE Portal gesendet.</p>
        </div>"""
        
        approver_emails = [a.get('approver_email') for a in approvers if a.get('approver_email') and a.get('priority') == 1]
        if not approver_emails:
            approver_emails = [a.get('approver_email') for a in approvers if a.get('approver_email')]
        if not approver_emails:
            return False
        
        result = graph.send_mail(sender_email=DRIVE_EMAIL, to_emails=approver_emails, subject=subject, body_html=body_html)
        if result:
            print(f"✅ Genehmiger-E-Mail gesendet an {approver_emails}")
        return result
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False


# ============================================================================
# ROUTES
# ============================================================================

@vacation_api.route('/health', methods=['GET'])
def health_check():
    """Health Check"""
    return jsonify({
        'status': 'ok',
        'service': 'vacation-api',
        'version': '2.4',
        'features': {
            'locosoft': LOCOSOFT_AVAILABLE,
            'graph_mail': GRAPH_AVAILABLE,
            'calendar': CALENDAR_AVAILABLE
        },
        'timestamp': datetime.now().isoformat()
    })


@vacation_api.route('/my-balance', methods=['GET'])
def get_my_balance():
    """
    GET /api/vacation/my-balance
    
    Gibt Urlaubssaldo für den ANGEMELDETEN User zurück
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
        
        # Locosoft Abwesenheiten hinzufügen
        locosoft_absences = None
        if LOCOSOFT_AVAILABLE and employee_data and employee_data.get('locosoft_id'):
            locosoft_absences = get_absences_for_employee(
                employee_data['locosoft_id'], 
                year
            )
            if locosoft_absences:
                balance['urlaub_locosoft'] = locosoft_absences.get('urlaub', 0)
                balance['zeitausgleich'] = locosoft_absences.get('zeitausgleich', 0)
                balance['krank'] = locosoft_absences.get('krank', 0)
                balance['sonstige'] = locosoft_absences.get('sonstige', 0)
                balance['resturlaub_korrigiert'] = round(
                    balance['anspruch'] - locosoft_absences.get('urlaub', 0), 1
                )
        
        approver_info = get_approver_summary(ldap_username)
        
        return jsonify({
            'success': True,
            'year': year,
            'ldap_username': ldap_username,
            'employee': employee_data,
            'balance': balance,
            'locosoft_absences': locosoft_absences,
            'approver_info': approver_info
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_api.route('/my-approvers', methods=['GET'])
def get_my_approvers():
    """
    GET /api/vacation/my-approvers
    
    Gibt zurück, wer den Urlaub des angemeldeten Users genehmigen kann.
    """
    try:
        employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not employee_id:
            return jsonify({
                'success': False,
                'error': 'Nicht angemeldet'
            }), 401
        
        approvers = get_approvers_for_employee(employee_id)
        
        return jsonify({
            'success': True,
            'employee': employee_data,
            'approvers': approvers,
            'count': len(approvers)
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
    
    Gibt Urlaubssalden für das Team des angemeldeten Genehmigers zurück.
    """
    try:
        employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not employee_id:
            return jsonify({
                'success': False,
                'error': 'Nicht angemeldet'
            }), 401
        
        if not is_approver(ldap_username):
            return jsonify({
                'success': False,
                'error': 'Zugriff verweigert - keine Genehmiger-Berechtigung',
                'hint': 'Sie sind nicht als Urlaubsgenehmiger konfiguriert'
            }), 403
        
        year = request.args.get('year', 2025, type=int)
        
        team_members = get_team_for_approver(ldap_username)
        
        if not team_members:
            return jsonify({
                'success': True,
                'year': year,
                'manager': employee_data,
                'team_count': 0,
                'team': [],
                'message': 'Kein Team zugeordnet'
            })
        
        conn = get_db()
        cursor = conn.cursor()
        
        team_ids = [m['employee_id'] for m in team_members]
        placeholders = ','.join('?' * len(team_ids))
        
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
            WHERE employee_id IN ({placeholders})
            ORDER BY name
        """, team_ids)
        
        locosoft_ids = [m.get('locosoft_id') for m in team_members if m.get('locosoft_id')]
        locosoft_absences = {}
        if LOCOSOFT_AVAILABLE and locosoft_ids:
            locosoft_absences = get_absences_for_employees(locosoft_ids, year)
        
        team = []
        for row in cursor.fetchall():
            member_info = next((m for m in team_members if m['employee_id'] == row[0]), {})
            locosoft_id = member_info.get('locosoft_id')
            
            loco = locosoft_absences.get(locosoft_id, {})
            urlaub = loco.get('urlaub', 0)
            zeitausgleich = loco.get('zeitausgleich', 0)
            krank = loco.get('krank', 0)
            sonstige = loco.get('sonstige', 0)
            
            anspruch = row[4] or 27
            verfuegbar = round(anspruch - urlaub, 1)
            
            team.append({
                'employee_id': row[0],
                'name': row[1],
                'department': row[2],
                'location': row[3],
                'anspruch': anspruch,
                'urlaub': urlaub,
                'zeitausgleich': zeitausgleich,
                'krank': krank,
                'sonstige': sonstige,
                'verfuegbar': verfuegbar,
                'verbraucht': row[5],
                'geplant': row[6],
                'resturlaub': row[7],
                'grp_code': member_info.get('grp_code', ''),
                'standort': member_info.get('standort', '')
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'year': year,
            'manager': employee_data,
            'team_count': len(team),
            'team': team,
            'locosoft_available': LOCOSOFT_AVAILABLE
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_api.route('/approver-summary', methods=['GET'])
def get_approver_summary_route():
    """
    GET /api/vacation/approver-summary
    """
    try:
        employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not employee_id:
            return jsonify({
                'success': False,
                'error': 'Nicht angemeldet'
            }), 401
        
        summary = get_approver_summary(ldap_username)
        
        return jsonify({
            'success': True,
            'ldap_username': ldap_username,
            'summary': summary
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_api.route('/pending-approvals', methods=['GET'])
def get_pending_approvals():
    """
    GET /api/vacation/pending-approvals
    
    Gibt alle offenen Urlaubsanträge zurück, die der angemeldete User genehmigen kann.
    """
    try:
        employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not employee_id:
            return jsonify({
                'success': False,
                'error': 'Nicht angemeldet'
            }), 401
        
        if not is_approver(ldap_username):
            return jsonify({
                'success': False,
                'error': 'Keine Genehmiger-Berechtigung'
            }), 403
        
        team_members = get_team_for_approver(ldap_username)
        
        if not team_members:
            return jsonify({
                'success': True,
                'pending': [],
                'count': 0
            })
        
        team_ids = [m['employee_id'] for m in team_members]
        placeholders = ','.join('?' * len(team_ids))
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT 
                vb.id,
                vb.employee_id,
                e.first_name || ' ' || e.last_name as employee_name,
                vb.booking_date,
                vb.day_part,
                vb.vacation_type_id,
                vt.name as vacation_type_name,
                vb.comment,
                vb.created_at
            FROM vacation_bookings vb
            JOIN employees e ON vb.employee_id = e.id
            LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
            WHERE vb.employee_id IN ({placeholders})
              AND vb.status = 'pending'
            ORDER BY vb.booking_date ASC
        """, team_ids)
        
        pending = []
        for row in cursor.fetchall():
            member_info = next((m for m in team_members if m['employee_id'] == row[1]), {})
            
            pending.append({
                'booking_id': row[0],
                'employee_id': row[1],
                'employee_name': row[2],
                'date': row[3],
                'day_part': row[4],
                'type_id': row[5],
                'type_name': row[6],
                'comment': row[7],
                'created_at': row[8],
                'grp_code': member_info.get('grp_code', ''),
                'standort': member_info.get('standort', '')
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'approver': employee_data,
            'pending': pending,
            'count': len(pending)
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_api.route('/approve', methods=['POST'])
def approve_vacation():
    """
    POST /api/vacation/approve
    
    Genehmigt einen Urlaubsantrag.
    NEU TAG 104: Sendet E-Mail an HR + Mitarbeiter, trägt in Team-Kalender ein.
    
    Body:
    {
        "booking_id": 123,
        "comment": "optional"
    }
    """
    try:
        employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not employee_id:
            return jsonify({'success': False, 'error': 'Nicht angemeldet'}), 401
        
        if not is_approver(ldap_username):
            return jsonify({'success': False, 'error': 'Keine Genehmiger-Berechtigung'}), 403
        
        data = request.get_json()
        booking_id = data.get('booking_id')
        comment = data.get('comment', '')
        
        if not booking_id:
            return jsonify({'success': False, 'error': 'booking_id erforderlich'}), 400
        
        team_members = get_team_for_approver(ldap_username)
        team_ids = [m['employee_id'] for m in team_members]
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Hole Booking-Details für E-Mail
        cursor.execute("""
            SELECT 
                vb.employee_id, 
                vb.status,
                vb.booking_date,
                vb.day_part,
                vb.vacation_type_id,
                vt.name as vacation_type,
                e.first_name || ' ' || e.last_name as employee_name,
                e.email as employee_email,
                e.department_name
            FROM vacation_bookings vb
            JOIN employees e ON vb.employee_id = e.id
            LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
            WHERE vb.id = ?
        """, (booking_id,))
        
        booking = cursor.fetchone()
        
        if not booking:
            conn.close()
            return jsonify({'success': False, 'error': 'Buchung nicht gefunden'}), 404
        
        if booking[0] not in team_ids:
            conn.close()
            return jsonify({'success': False, 'error': 'Keine Berechtigung für diese Buchung'}), 403
        
        if booking[1] != 'pending':
            conn.close()
            return jsonify({'success': False, 'error': f'Buchung hat bereits Status: {booking[1]}'}), 400
        
        # Genehmigen
        cursor.execute("""
            UPDATE vacation_bookings 
            SET status = 'approved',
                approved_by = ?,
                approved_at = ?,
                comment = CASE WHEN comment IS NULL OR comment = '' THEN ? ELSE comment || ' | Genehmigt: ' || ? END
            WHERE id = ?
        """, (employee_id, datetime.now().isoformat(), comment, comment, booking_id))
        
        conn.commit()
        conn.close()
        
        # Booking-Details für E-Mails
        approver_name = f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}".strip()
        
        booking_details = {
            'date': booking[2],
            'day_part': booking[3],
            'vacation_type': booking[5] or 'Urlaub',
            'employee_name': booking[6],
            'employee_email': booking[7],
            'department': booking[8] or ''
        }
        
        # E-Mails senden (TAG 104)
        hr_email_sent = send_approval_email_to_hr(booking_details, approver_name)
        employee_email_sent = send_approval_notification_to_employee(booking_details, approver_name)
        
        # Team-Kalender Eintrag (TAG 104)
        calendar_added = add_to_team_calendar(booking_details)
        
        return jsonify({
            'success': True,
            'message': 'Urlaubsantrag genehmigt',
            'booking_id': booking_id,
            'notifications': {
                'hr_email': hr_email_sent,
                'employee_email': employee_email_sent,
                'calendar': calendar_added
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_api.route('/reject', methods=['POST'])
def reject_vacation():
    """
    POST /api/vacation/reject
    
    Lehnt einen Urlaubsantrag ab.
    NEU TAG 104: Sendet E-Mail an Mitarbeiter mit Begründung.
    
    Body:
    {
        "booking_id": 123,
        "reason": "Grund für Ablehnung"
    }
    """
    try:
        employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not employee_id:
            return jsonify({'success': False, 'error': 'Nicht angemeldet'}), 401
        
        if not is_approver(ldap_username):
            return jsonify({'success': False, 'error': 'Keine Genehmiger-Berechtigung'}), 403
        
        data = request.get_json()
        booking_id = data.get('booking_id')
        reason = data.get('reason', 'Kein Grund angegeben')
        
        if not booking_id:
            return jsonify({'success': False, 'error': 'booking_id erforderlich'}), 400
        
        team_members = get_team_for_approver(ldap_username)
        team_ids = [m['employee_id'] for m in team_members]
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Hole Booking-Details für E-Mail
        cursor.execute("""
            SELECT 
                vb.employee_id, 
                vb.status,
                vb.booking_date,
                vb.day_part,
                vt.name as vacation_type,
                e.first_name || ' ' || e.last_name as employee_name,
                e.email as employee_email
            FROM vacation_bookings vb
            JOIN employees e ON vb.employee_id = e.id
            LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
            WHERE vb.id = ?
        """, (booking_id,))
        
        booking = cursor.fetchone()
        
        if not booking:
            conn.close()
            return jsonify({'success': False, 'error': 'Buchung nicht gefunden'}), 404
        
        if booking[0] not in team_ids:
            conn.close()
            return jsonify({'success': False, 'error': 'Keine Berechtigung für diese Buchung'}), 403
        
        if booking[1] != 'pending':
            conn.close()
            return jsonify({'success': False, 'error': f'Buchung hat bereits Status: {booking[1]}'}), 400
        
        # Ablehnen
        cursor.execute("""
            UPDATE vacation_bookings 
            SET status = 'rejected',
                approved_by = ?,
                approved_at = ?,
                comment = CASE WHEN comment IS NULL OR comment = '' THEN ? ELSE comment || ' | Abgelehnt: ' || ? END
            WHERE id = ?
        """, (employee_id, datetime.now().isoformat(), reason, reason, booking_id))
        
        conn.commit()
        conn.close()
        
        # E-Mail an Mitarbeiter senden (TAG 104)
        approver_name = f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}".strip()
        
        booking_details = {
            'date': booking[2],
            'day_part': booking[3],
            'vacation_type': booking[4] or 'Urlaub',
            'employee_name': booking[5],
            'employee_email': booking[6]
        }
        
        email_sent = send_rejection_notification(booking_details, approver_name, reason)
        
        return jsonify({
            'success': True,
            'message': 'Urlaubsantrag abgelehnt',
            'booking_id': booking_id,
            'reason': reason,
            'notifications': {
                'employee_email': email_sent
            }
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
        
        # Locosoft-Daten für Abgleich holen
        locosoft_dates = set()
        if LOCOSOFT_AVAILABLE and employee_data and employee_data.get('locosoft_id'):
            try:
                import psycopg2
                loco_conn = psycopg2.connect(
                    host='10.80.80.8',
                    database='loco_auswertung_db',
                    user='loco_auswertung_benutzer',
                    password='loco'
                )
                loco_cur = loco_conn.cursor()
                loco_cur.execute("""
                    SELECT date::text FROM absence_calendar
                    WHERE employee_number = %s
                    AND date >= %s AND date <= %s
                """, (employee_data['locosoft_id'], f'{year}-01-01', f'{year}-12-31'))
                locosoft_dates = set(row[0] for row in loco_cur.fetchall())
                loco_conn.close()
            except Exception as e:
                print(f"Locosoft-Abgleich Fehler: {e}")
        
        bookings = []
        for row in cursor.fetchall():
            booking_date = row[1]
            in_locosoft = booking_date in locosoft_dates
            
            bookings.append({
                'id': row[0],
                'date': booking_date,
                'day_part': row[2],
                'status': row[3],
                'type_id': row[4],
                'type_name': row[5],
                'comment': row[6],
                'created_at': row[7],
                'in_locosoft': in_locosoft
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'year': year,
            'employee': employee_data,
            'count': len(bookings),
            'bookings': bookings,
            'locosoft_check': len(locosoft_dates) > 0
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
    """
    try:
        current_employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not current_employee_id:
            return jsonify({
                'success': False,
                'error': 'Nicht angemeldet'
            }), 401
        
        requested_employee_id = request.args.get('employee_id', None, type=int)
        employee_id = requested_employee_id if requested_employee_id else current_employee_id
        
        if employee_id != current_employee_id:
            if not is_approver(ldap_username):
                return jsonify({
                    'success': False,
                    'error': 'Keine Berechtigung'
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
        
        requests_list = []
        for row in cursor.fetchall():
            requests_list.append({
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
            'count': len(requests_list),
            'requests': requests_list
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
        
        cursor.execute("""
            INSERT INTO vacation_bookings (
                employee_id, booking_date, vacation_type_id,
                day_part, status, comment, created_at
            ) VALUES (?, ?, ?, ?, 'pending', ?, ?)
        """, (employee_id, booking_date, vacation_type_id, day_part, comment, datetime.now().isoformat()))
        
        booking_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        approvers = get_approvers_for_employee(employee_id)
        approver_names = [a['approver_name'] for a in approvers if a['priority'] == 1]
        
        # E-Mail an Genehmiger senden (TAG 104b)
        conn2 = get_db()
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT name FROM vacation_types WHERE id = ?", (vacation_type_id,))
        vt_row = cursor2.fetchone()
        vacation_type_name = vt_row[0] if vt_row else 'Urlaub'
        conn2.close()
        
        booking_details_for_email = {
            'date': booking_date,
            'day_part': day_part,
            'vacation_type': vacation_type_name,
            'employee_name': f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}".strip(),
            'department': employee_data.get('department', ''),
            'comment': comment
        }
        approver_email_sent = send_new_request_notification_to_approvers(booking_details_for_email, approvers)
        
        return jsonify({
            'success': True,
            'booking_id': booking_id,
            'message': 'Urlaubsantrag eingereicht (Status: pending)',
            'booking': {
                'id': booking_id,
                'date': booking_date,
                'day_part': day_part,
                'status': 'pending'
            },
            'approvers': approver_names
        }), 201
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_api.route('/cancel', methods=['POST'])
def cancel_vacation():
    """
    POST /api/vacation/cancel
    
    Storniert eine eigene Urlaubsbuchung.
    TAG 104: Sendet E-Mail an Genehmiger + HR (bei approved), löscht Kalendereintrag.
    
    Body:
    {
        "booking_id": 123,
        "reason": "Grund für Stornierung (optional)"
    }
    """
    try:
        employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not employee_id:
            return jsonify({'success': False, 'error': 'Nicht angemeldet'}), 401
        
        data = request.get_json()
        booking_id = data.get('booking_id')
        reason = data.get('reason', 'Vom Mitarbeiter storniert')
        
        if not booking_id:
            return jsonify({'success': False, 'error': 'booking_id erforderlich'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Hole Booking-Details
        cursor.execute("""
            SELECT 
                vb.employee_id, 
                vb.status,
                vb.booking_date,
                vb.day_part,
                vt.name as vacation_type,
                e.first_name || ' ' || e.last_name as employee_name,
                e.department_name
            FROM vacation_bookings vb
            JOIN employees e ON vb.employee_id = e.id
            LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
            WHERE vb.id = ?
        """, (booking_id,))
        
        booking = cursor.fetchone()
        
        if not booking:
            conn.close()
            return jsonify({'success': False, 'error': 'Buchung nicht gefunden'}), 404
        
        # Nur eigene Buchungen stornieren
        if booking[0] != employee_id:
            conn.close()
            return jsonify({'success': False, 'error': 'Nur eigene Buchungen können storniert werden'}), 403
        
        # Bereits genehmigte Buchungen können auch storniert werden (mit Benachrichtigung)
        was_approved = booking[1] == 'approved'
        
        # Status auf 'cancelled' setzen
        cursor.execute("""
            UPDATE vacation_bookings 
            SET status = 'cancelled',
                comment = CASE WHEN comment IS NULL OR comment = '' THEN ? ELSE comment || ' | Storniert: ' || ? END
            WHERE id = ?
        """, (reason, reason, booking_id))
        
        conn.commit()
        conn.close()
        
        booking_details = {
            'date': booking[2],
            'day_part': booking[3],
            'vacation_type': booking[4] or 'Urlaub',
            'employee_name': booking[5],
            'department': booking[6] or ''
        }
        
        # E-Mail an Genehmiger senden (zur Info)
        approvers = get_approvers_for_employee(employee_id)
        cancellation_email_sent = send_cancellation_notification_to_approvers(
            booking_details, 
            approvers, 
            reason,
            was_approved
        )
        
        # Wenn bereits genehmigt war: auch HR informieren (muss in Locosoft storniert werden)
        hr_email_sent = False
        if was_approved:
            hr_email_sent = send_cancellation_email_to_hr(
                booking_details,
                f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}".strip(),
                reason
            )
        
        # Kalendereintrag löschen falls vorhanden
        calendar_deleted = False
        if was_approved and CALENDAR_AVAILABLE:
            try:
                calendar_service = VacationCalendarService()
                calendar_deleted = calendar_service.delete_vacation_event(booking_details)
            except Exception as e:
                print(f"⚠️ Kalender-Löschung fehlgeschlagen: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Urlaubsantrag storniert',
            'booking_id': booking_id,
            'was_approved': was_approved,
            'notifications': {
                'approver_email': cancellation_email_sent,
                'hr_email': hr_email_sent,
                'calendar_deleted': calendar_deleted
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_api.route('/debug/session', methods=['GET'])
def debug_session():
    """Debug-Endpoint: Zeigt Session-Daten"""
    employee_id, ldap_username, employee_data = get_employee_from_session()
    
    return jsonify({
        'session': dict(session),
        'ldap_username': ldap_username,
        'employee_id': employee_id,
        'employee_data': employee_data,
        'is_approver': is_approver(ldap_username) if ldap_username else False,
        'features': {
            'locosoft': LOCOSOFT_AVAILABLE,
            'graph_mail': GRAPH_AVAILABLE,
            'calendar': CALENDAR_AVAILABLE
        },
        'timestamp': datetime.now().isoformat()
    })


# Export Blueprint
__all__ = ['vacation_api']
