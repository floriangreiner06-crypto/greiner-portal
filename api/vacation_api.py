#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
VACATION API - MIT LDAP-INTEGRATION
========================================
Version: 2.6 - TAG 117
Datum: 12.12.2025

CHANGES TAG 117:
- Migration auf db_session() Context Manager (keine Connection Leaks mehr)
- Alle manuellen conn.close() Aufrufe entfernt
- Zentrale DB-Utilities aus api.db_utils

CHANGES TAG 113:
- Krankheit nur für Admins (GRP_Urlaub_Admin)
- E-Mail-Storno mit klarerem Text (wer hat storniert)
- Admins können fremde Buchungen stornieren
- /book-batch: Batch-Buchung mit einer E-Mail
- /cancel-batch: Batch-Stornierung mit einer E-Mail
- Mitarbeiter-Benachrichtigung bei Admin-Storno

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
from datetime import datetime, date, timedelta
import json

# Zentrale DB-Utilities (TAG 117 - Migration abgeschlossen)
from api.db_utils import db_session, row_to_dict, rows_to_list

# Approver Service importieren
from api.vacation_approver_service import (
    get_approvers_for_employee,
    get_team_for_approver,
    is_approver,
    get_approver_summary
)

# Locosoft Abwesenheits-Service (TAG 103 + TAG 113)
try:
    from api.vacation_locosoft_service import (
        get_absences_for_employee,
        get_absences_for_employees,
        get_absence_days_for_employee,      # TAG 113: Einzelne Tage mit day_contingent
        get_absence_days_for_employees      # TAG 113: Bulk für Kalender
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

# E-Mail-Konfiguration
HR_EMAIL = 'hr@auto-greiner.de'  # HR-Mailbox für Locosoft-Einträge
DRIVE_EMAIL = 'drive@auto-greiner.de'  # Absender


def get_employee_from_session():
    """
    Holt employee_id aus Flask-Login Session via ldap_employee_mapping
    """
    # 1. Hole user_id aus Flask-Login Session
    user_id = session.get('_user_id')
    ldap_username = None

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
        with db_session() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()

            if not user_row:
                return None, None, None

            username = user_row[0]
            ldap_username = username.split('@')[0] if '@' in username else username

    # Lookup in ldap_employee_mapping
    with db_session() as conn:
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
        
        # TAG 113: Halber Tag mit VM/NM Angabe
        if booking_details.get('day_part') == 'full':
            day_part = 'Ganzer Tag'
        else:
            half_time = booking_details.get('half_day_time', '')
            if half_time == 'am':
                day_part = 'Halber Tag (Vormittag)'
            elif half_time == 'pm':
                day_part = 'Halber Tag (Nachmittag)'
            else:
                day_part = 'Halber Tag'
        
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


def send_cancellation_notification_to_approvers(booking_details: dict, approvers: list, reason: str, was_approved: bool, cancelled_by: str = None):
    """
    Sendet E-Mail an Genehmiger wenn ein Urlaubsantrag storniert wurde.
    TAG 113: cancelled_by Parameter hinzugefügt für klarere E-Mail-Texte
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
        department = booking_details.get('department', '')
        
        status_text = "genehmigten" if was_approved else "beantragten"
        subject = f"🚫 {vacation_type} storniert: {employee_name} - {date_formatted}"
        
        # TAG 113: Klarerer E-Mail-Text - wer hat storniert?
        if cancelled_by and cancelled_by != employee_name:
            action_text = f"<strong>{cancelled_by}</strong> hat den {status_text} {vacation_type} von <strong>{employee_name}</strong> ({department}) für <strong>{date_formatted}</strong> storniert."
        else:
            action_text = f"<strong>{employee_name}</strong> ({department}) hat den {status_text} {vacation_type} für <strong>{date_formatted}</strong> storniert."
        
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px;">
            <h2 style="color: #dc3545;">🚫 {vacation_type} storniert</h2>
            
            <p>{action_text}</p>
            
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
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Status war</td>
                    <td style="padding: 10px; border: 1px solid #dee2e6;">{status_text}</td>
                </tr>
            </table>
            
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


def send_sickness_notification(booking_details: dict, approvers: list):
    """
    Sendet E-Mail an HR, Teamleitung und GL wenn Krankheitstag eingetragen wurde.
    Krankheit braucht keine Genehmigung - nur Benachrichtigung.
    """
    if not GRAPH_AVAILABLE:
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
        department = booking_details.get('department', '')
        
        subject = f"🤒 Krankheitstag eingetragen: {employee_name} - {date_formatted}"
        
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px;">
            <h2 style="color: #F48FB1;">🤒 Krankheitstag eingetragen</h2>
            
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
            </table>
            
            <p style="background: #FCE4EC; padding: 15px; border-radius: 5px; border-left: 4px solid #F48FB1;">
                <strong>📋 Aktion für HR:</strong><br>
                Bitte diesen Krankheitstag in <strong>Locosoft</strong> eintragen.
            </p>
            
            <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
            <p style="color: #6c757d; font-size: 12px;">
                Diese E-Mail wurde automatisch vom Greiner DRIVE Portal gesendet.
            </p>
        </div>
        """
        
        # E-Mail-Empfänger: HR + Teamleitung (Prio 1 Genehmiger) + GL
        recipients = [HR_EMAIL]
        
        # Teamleitung hinzufügen
        if approvers:
            for a in approvers:
                if a.get('approver_email') and a.get('priority') == 1:
                    if a['approver_email'] not in recipients:
                        recipients.append(a['approver_email'])
        
        # GL hinzufügen (florian.greiner@auto-greiner.de)
        gl_email = 'florian.greiner@auto-greiner.de'
        if gl_email not in recipients:
            recipients.append(gl_email)
        
        result = graph.send_mail(
            sender_email=DRIVE_EMAIL,
            to_emails=recipients,
            subject=subject,
            body_html=body_html
        )
        
        if result:
            print(f"✅ Krankheits-E-Mail gesendet an {recipients}")
        return result
        
    except Exception as e:
        print(f"❌ Fehler beim Senden der Krankheits-E-Mail: {e}")
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
        
        # TAG 113: Halber Tag mit VM/NM Angabe
        if booking_details.get('day_part') == 'full':
            day_part = 'Ganzer Tag'
        else:
            half_time = booking_details.get('half_day_time', '')
            if half_time == 'am':
                day_part = 'Halber Tag (Vormittag)'
            elif half_time == 'pm':
                day_part = 'Halber Tag (Nachmittag)'
            else:
                day_part = 'Halber Tag'
        
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
                Bitte im <a href="http://drive.auto-greiner.de/urlaubsplaner">Greiner DRIVE Portal</a> genehmigen oder ablehnen.
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

        with db_session() as conn:
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
        
        team_ids = [m['employee_id'] for m in team_members]
        placeholders = ','.join('?' * len(team_ids))

        with db_session() as conn:
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

        with db_session() as conn:
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

        with db_session() as conn:
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
                return jsonify({'success': False, 'error': 'Buchung nicht gefunden'}), 404

            if booking[0] not in team_ids:
                return jsonify({'success': False, 'error': 'Keine Berechtigung für diese Buchung'}), 403

            if booking[1] != 'pending':
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

        with db_session() as conn:
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
                return jsonify({'success': False, 'error': 'Buchung nicht gefunden'}), 404

            if booking[0] not in team_ids:
                return jsonify({'success': False, 'error': 'Keine Berechtigung für diese Buchung'}), 403

            if booking[1] != 'pending':
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

        with db_session() as conn:
            cursor = conn.cursor()
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


@vacation_api.route('/all-bookings', methods=['GET'])
def get_all_bookings():
    """
    GET /api/vacation/all-bookings
    
    Gibt alle Urlaubsbuchungen aller Mitarbeiter zurück (für Kalenderanzeige).
    Nur approved und pending Buchungen werden zurückgegeben.
    TAG 113: Für Kollegen-Urlaub-Anzeige im Kalender.
    """
    try:
        year = request.args.get('year', 2025, type=int)

        with db_session() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    vb.id,
                    vb.employee_id,
                    vb.booking_date,
                    vb.day_part,
                    vb.status,
                    vb.vacation_type_id
                FROM vacation_bookings vb
                WHERE strftime('%Y', vb.booking_date) = ?
                  AND vb.status IN ('approved', 'pending')
                ORDER BY vb.booking_date
            """, (str(year),))

            bookings = []
            for row in cursor.fetchall():
                bookings.append({
                    'id': row[0],
                    'employee_id': row[1],
                    'date': row[2],
                    'day_part': row[3],
                    'status': row[4],
                    'type_id': row[5]
                })

        return jsonify({
            'success': True,
            'year': year,
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

        with db_session() as conn:
            cursor = conn.cursor()
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

        with db_session() as conn:
            cursor = conn.cursor()
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

        with db_session() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id FROM vacation_bookings
                WHERE employee_id = ? AND booking_date = ? AND status != 'cancelled'
            """, (employee_id, booking_date))

            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': f'Für {booking_date} existiert bereits eine Buchung'
                }), 400

            # ====================================================================
            # RESTURLAUB-VALIDIERUNG (TAG 113)
            # Nur für Urlaub (type_id=1) - ZA/Schulung/Krank nicht prüfen
            # ====================================================================
            resturlaub_info = None

            if vacation_type_id == 1:  # Nur bei echtem Urlaub
                requested_days = 1.0 if day_part == 'full' else 0.5
                booking_year = int(booking_date[:4])

                # Hole aktuellen Resturlaub aus Locosoft (genaueste Quelle)
                available_days = None

                if LOCOSOFT_AVAILABLE and employee_data and employee_data.get('locosoft_id'):
                    try:
                        locosoft_absences = get_absences_for_employee(
                            employee_data['locosoft_id'],
                            booking_year
                        )
                        if locosoft_absences:
                            # Anspruch aus vacation_entitlements holen
                            cursor.execute("""
                                SELECT total_days FROM vacation_entitlements
                                WHERE employee_id = ? AND year = ?
                            """, (employee_id, booking_year))
                            ent_row = cursor.fetchone()
                            anspruch = ent_row[0] if ent_row else 27

                            # Bereits in Locosoft gebuchter Urlaub
                            urlaub_locosoft = locosoft_absences.get('urlaub', 0)

                            # Bereits im Portal pending/approved gebuchter Urlaub (noch nicht in Locosoft)
                            cursor.execute("""
                                SELECT COALESCE(SUM(CASE WHEN day_part = 'full' THEN 1.0 ELSE 0.5 END), 0)
                                FROM vacation_bookings
                                WHERE employee_id = ?
                                  AND strftime('%Y', booking_date) = ?
                                  AND vacation_type_id = 1
                                  AND status IN ('pending', 'approved')
                            """, (employee_id, str(booking_year)))
                            portal_pending = cursor.fetchone()[0] or 0

                            # Verfügbar = Anspruch - Locosoft - Portal-Pending
                            available_days = round(anspruch - urlaub_locosoft - portal_pending, 1)
                            resturlaub_info = {
                                'anspruch': anspruch,
                                'locosoft': urlaub_locosoft,
                                'portal_pending': portal_pending,
                                'verfuegbar': available_days
                            }
                    except Exception as e:
                        print(f"⚠️ Locosoft-Abfrage für Resturlaub fehlgeschlagen: {e}")

                # Fallback: Nur Portal-Daten wenn Locosoft nicht verfügbar
                if available_days is None:
                    cursor.execute(f"""
                        SELECT anspruch, verbraucht, geplant, resturlaub
                        FROM v_vacation_balance_{booking_year}
                        WHERE employee_id = ?
                    """, (employee_id,))
                    bal_row = cursor.fetchone()
                    if bal_row:
                        available_days = bal_row[3] or 0  # resturlaub
                        resturlaub_info = {
                            'anspruch': bal_row[0],
                            'verbraucht': bal_row[1],
                            'geplant': bal_row[2],
                            'verfuegbar': available_days
                        }
                    else:
                        available_days = 27  # Default Anspruch

                # Prüfung: Genug Resturlaub?
                if available_days is not None and requested_days > available_days:
                    return jsonify({
                        'success': False,
                        'error': f'Nicht genug Resturlaub! Verfügbar: {available_days} Tage, angefragt: {requested_days} Tag(e)',
                        'resturlaub_info': resturlaub_info
                    }), 400

            # Krankheit (type_id=3) - nur Admins dürfen Krankheit eintragen (TAG 113)
            is_sickness = vacation_type_id == 3
            if is_sickness:
                # Prüfe ob User Admin ist (GRP_Urlaub_Admin)
                cursor.execute("""
                    SELECT ad_groups FROM users
                    WHERE username LIKE ? OR username = ?
                """, (f"%{ldap_username}%", ldap_username))
                user_row = cursor.fetchone()

                is_admin = False
                if user_row and user_row[0]:
                    try:
                        groups = json.loads(user_row[0]) if isinstance(user_row[0], str) else user_row[0]
                        is_admin = 'GRP_Urlaub_Admin' in groups
                    except:
                        pass

                if not is_admin:
                    return jsonify({
                        'success': False,
                        'error': 'Krankheitstage können nur von Admins eingetragen werden'
                    }), 403

            initial_status = 'approved' if is_sickness else 'pending'

            cursor.execute("""
                INSERT INTO vacation_bookings (
                    employee_id, booking_date, vacation_type_id,
                    day_part, status, comment, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (employee_id, booking_date, vacation_type_id, day_part, initial_status, comment, datetime.now().isoformat()))

            booking_id = cursor.lastrowid
            conn.commit()

            # Vacation type name für E-Mail holen
            cursor.execute("SELECT name FROM vacation_types WHERE id = ?", (vacation_type_id,))
            vt_row = cursor.fetchone()
            vacation_type_name = vt_row[0] if vt_row else 'Urlaub'

        approvers = get_approvers_for_employee(employee_id)
        approver_names = [a['approver_name'] for a in approvers if a['priority'] == 1]
        
        booking_details_for_email = {
            'date': booking_date,
            'day_part': day_part,
            'vacation_type': vacation_type_name,
            'employee_name': f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}".strip(),
            'department': employee_data.get('department', ''),
            'comment': comment
        }
        
        # Unterschiedliche E-Mails je nach Typ
        if is_sickness:
            # Krankheit: E-Mail an HR + Teamleitung + GL
            sickness_email_sent = send_sickness_notification(booking_details_for_email, approvers)
            return jsonify({
                'success': True,
                'booking_id': booking_id,
                'message': 'Krankheitstag eingetragen (Status: approved)',
                'booking': {
                    'id': booking_id,
                    'date': booking_date,
                    'day_part': day_part,
                    'status': 'approved'
                },
                'notifications': {
                    'sickness_email': sickness_email_sent
                }
            }), 201
        else:
            # Normaler Urlaub/ZA/Schulung: E-Mail an Genehmiger
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

        with db_session() as conn:
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
                    e.department_name,
                    e.email as owner_email
                FROM vacation_bookings vb
                JOIN employees e ON vb.employee_id = e.id
                LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
                WHERE vb.id = ?
            """, (booking_id,))

            booking = cursor.fetchone()

            if not booking:
                return jsonify({'success': False, 'error': 'Buchung nicht gefunden'}), 404

            # TAG 113: Admins dürfen auch fremde Buchungen stornieren
            booking_owner_id = booking[0]
            is_own_booking = booking_owner_id == employee_id
            owner_email = booking[7]

            # Prüfe ob User Admin ist (GRP_Urlaub_Admin)
            is_admin = False
            cursor.execute("""
                SELECT ad_groups FROM users
                WHERE username LIKE ? OR username = ?
            """, (f"%{ldap_username}%", ldap_username))
            user_row = cursor.fetchone()
            if user_row and user_row[0]:
                try:
                    groups = json.loads(user_row[0]) if isinstance(user_row[0], str) else user_row[0]
                    is_admin = 'GRP_Urlaub_Admin' in groups
                except:
                    pass

            if not is_own_booking and not is_admin:
                return jsonify({'success': False, 'error': 'Nur eigene Buchungen können storniert werden (oder Admin-Berechtigung erforderlich)'}), 403

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

        booking_details = {
            'date': booking[2],
            'day_part': booking[3],
            'vacation_type': booking[4] or 'Urlaub',
            'employee_name': booking[5],
            'department': booking[6] or ''
        }

        # E-Mail an Genehmiger senden (zur Info)
        # TAG 113: cancelled_by = wer hat storniert (kann Admin sein)
        cancelled_by_name = f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}".strip()

        # TAG 113: Bei Admin-Storno: Approvers des Buchungs-Eigentümers holen, nicht des Admins
        approvers = get_approvers_for_employee(booking_owner_id)

        cancellation_email_sent = send_cancellation_notification_to_approvers(
            booking_details,
            approvers,
            reason,
            was_approved,
            cancelled_by=cancelled_by_name
        )

        # TAG 113: Bei Admin-Storno auch den Mitarbeiter informieren
        employee_email_sent = False
        if not is_own_booking and is_admin and owner_email:
            try:
                graph = GraphMailConnector()
                date_formatted = booking_details['date']
                try:
                    date_obj = datetime.strptime(date_formatted, '%Y-%m-%d')
                    date_formatted = date_obj.strftime('%d.%m.%Y')
                except:
                    pass

                subject = f"🚫 Dein {booking_details['vacation_type']} wurde storniert - {date_formatted}"
                body_html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px;">
                    <h2 style="color: #dc3545;">🚫 {booking_details['vacation_type']} storniert</h2>
                    <p>Dein {'genehmigter' if was_approved else 'beantragter'} {booking_details['vacation_type']} für <strong>{date_formatted}</strong> wurde von <strong>{cancelled_by_name}</strong> storniert.</p>
                    <p style="background: #f8d7da; padding: 15px; border-radius: 5px;"><strong>Grund:</strong> {reason}</p>
                    <p>Bei Fragen wende dich bitte an die Personalabteilung.</p>
                    <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
                    <p style="color: #6c757d; font-size: 12px;">Greiner DRIVE Portal</p>
                </div>
                """
                employee_email_sent = graph.send_mail(
                    sender_email=DRIVE_EMAIL,
                    to_emails=[owner_email],
                    subject=subject,
                    body_html=body_html
                )
            except Exception as e:
                print(f"⚠️ Mitarbeiter-E-Mail bei Admin-Storno fehlgeschlagen: {e}")
        
        # Wenn bereits genehmigt war: auch HR informieren (muss in Locosoft storniert werden)
        hr_email_sent = False
        if was_approved:
            hr_email_sent = send_cancellation_email_to_hr(
                booking_details,
                booking_details['employee_name'],  # Name des Buchungs-Eigentümers
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
            'cancelled_by_admin': not is_own_booking and is_admin,
            'notifications': {
                'approver_email': cancellation_email_sent,
                'employee_email': employee_email_sent,
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


@vacation_api.route('/book-batch', methods=['POST'])
def book_vacation_batch():
    """
    POST /api/vacation/book-batch
    
    TAG 113: Bucht mehrere Tage auf einmal (E-Mail-Batching).
    Sendet EINE E-Mail an Genehmiger für alle Tage.
    
    Body:
    {
        "dates": ["2025-12-10", "2025-12-11", "2025-12-12"],
        "vacation_type_id": 1,
        "day_part": "full",
        "comment": "optional"
    }
    """
    try:
        employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not employee_id:
            return jsonify({'success': False, 'error': 'Nicht angemeldet'}), 401
        
        data = request.get_json()
        
        if not data or 'dates' not in data or not data['dates']:
            return jsonify({'success': False, 'error': 'Fehlende Daten: dates erforderlich'}), 400
        
        dates = sorted(data['dates'])
        day_part = data.get('day_part', 'full')
        half_day_time = data.get('half_day_time', None)  # TAG 113: VM/NM für halbe Tage
        vacation_type_id = data.get('vacation_type_id', 1)
        comment = data.get('comment', None)
        
        # Validierung
        for d in dates:
            try:
                datetime.strptime(d, '%Y-%m-%d')
            except ValueError:
                return jsonify({'success': False, 'error': f'Ungültiges Datum: {d}'}), 400

        with db_session() as conn:
            cursor = conn.cursor()

            # Krankheit nur für Admins (TAG 113)
            is_sickness = vacation_type_id == 3
            if is_sickness:
                cursor.execute("""
                    SELECT ad_groups FROM users WHERE username LIKE ? OR username = ?
                """, (f"%{ldap_username}%", ldap_username))
                user_row = cursor.fetchone()
                is_admin = False
                if user_row and user_row[0]:
                    try:
                        groups = json.loads(user_row[0]) if isinstance(user_row[0], str) else user_row[0]
                        is_admin = 'GRP_Urlaub_Admin' in groups
                    except:
                        pass
                if not is_admin:
                    return jsonify({'success': False, 'error': 'Krankheitstage können nur von Admins eingetragen werden'}), 403

            # Resturlaub-Validierung für Urlaub (type_id=1)
            if vacation_type_id == 1:
                requested_days = len(dates) * (1.0 if day_part == 'full' else 0.5)
                booking_year = int(dates[0][:4])
                available_days = None

                if LOCOSOFT_AVAILABLE and employee_data and employee_data.get('locosoft_id'):
                    try:
                        locosoft_absences = get_absences_for_employee(employee_data['locosoft_id'], booking_year)
                        if locosoft_absences:
                            cursor.execute("SELECT total_days FROM vacation_entitlements WHERE employee_id = ? AND year = ?", (employee_id, booking_year))
                            ent_row = cursor.fetchone()
                            anspruch = ent_row[0] if ent_row else 27
                            urlaub_locosoft = locosoft_absences.get('urlaub', 0)
                            cursor.execute("""
                                SELECT COALESCE(SUM(CASE WHEN day_part = 'full' THEN 1.0 ELSE 0.5 END), 0)
                                FROM vacation_bookings WHERE employee_id = ? AND strftime('%Y', booking_date) = ?
                                AND vacation_type_id = 1 AND status IN ('pending', 'approved')
                            """, (employee_id, str(booking_year)))
                            portal_pending = cursor.fetchone()[0] or 0
                            available_days = round(anspruch - urlaub_locosoft - portal_pending, 1)
                    except Exception as e:
                        print(f"⚠️ Locosoft-Abfrage fehlgeschlagen: {e}")

                if available_days is not None and requested_days > available_days:
                    return jsonify({
                        'success': False,
                        'error': f'Nicht genug Resturlaub! Verfügbar: {available_days} Tage, angefragt: {requested_days} Tag(e)'
                    }), 400

            # Prüfe ob bereits Buchungen existieren
            existing = []
            for d in dates:
                cursor.execute("""
                    SELECT id FROM vacation_bookings WHERE employee_id = ? AND booking_date = ? AND status != 'cancelled'
                """, (employee_id, d))
                if cursor.fetchone():
                    existing.append(d)

            if existing:
                return jsonify({'success': False, 'error': f'Bereits gebucht: {existing[0]}'}), 400

            # Alle Buchungen einfügen
            initial_status = 'approved' if is_sickness else 'pending'
            booking_ids = []
            for d in dates:
                cursor.execute("""
                    INSERT INTO vacation_bookings (employee_id, booking_date, vacation_type_id, day_part, status, comment, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (employee_id, d, vacation_type_id, day_part, initial_status, comment, datetime.now().isoformat()))
                booking_ids.append(cursor.lastrowid)

            # Vacation Type Name holen
            cursor.execute("SELECT name FROM vacation_types WHERE id = ?", (vacation_type_id,))
            vt_row = cursor.fetchone()
            vacation_type_name = vt_row[0] if vt_row else 'Urlaub'

            conn.commit()
        
        # EINE E-Mail für alle Tage (E-Mail-Batching)
        approvers = get_approvers_for_employee(employee_id)
        employee_name = f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}".strip()
        department = employee_data.get('department', '')
        
        email_sent = False
        if GRAPH_AVAILABLE and approvers:
            try:
                graph = GraphMailConnector()
                
                # Datums-Formatierung
                dates_formatted = []
                for d in dates:
                    try:
                        date_obj = datetime.strptime(d, '%Y-%m-%d')
                        dates_formatted.append(date_obj.strftime('%d.%m.%Y'))
                    except:
                        dates_formatted.append(d)
                
                if len(dates) == 1:
                    date_display = dates_formatted[0]
                    subject = f"📋 Neuer Urlaubsantrag: {employee_name} - {date_display}"
                else:
                    date_display = f"{dates_formatted[0]} - {dates_formatted[-1]} ({len(dates)} Tage)"
                    subject = f"📋 Neuer Urlaubsantrag: {employee_name} - {len(dates)} Tage"
                
                type_icons = {'Urlaub': '🏖️', 'Zeitausgleich': '⏰', 'Krankheit': '🤒', 'Schulung': '📚'}
                icon = type_icons.get(vacation_type_name, '📅')
                
                # TAG 113: Umfang mit VM/NM
                if day_part == 'full':
                    umfang = 'Ganzer Tag'
                else:
                    if half_day_time == 'am':
                        umfang = 'Halber Tag (Vormittag)'
                    elif half_day_time == 'pm':
                        umfang = 'Halber Tag (Nachmittag)'
                    else:
                        umfang = 'Halber Tag'
                
                # Tage-Liste für E-Mail
                dates_list_html = '<ul style="margin: 10px 0; padding-left: 20px;">'
                for df in dates_formatted:
                    dates_list_html += f'<li>{df}</li>'
                dates_list_html += '</ul>'
                
                body_html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px;">
                    <h2 style="color: #007bff;">{icon} Neuer Urlaubsantrag</h2>
                    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                        <tr style="background: #f8f9fa;"><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Mitarbeiter</td><td style="padding: 10px; border: 1px solid #dee2e6;">{employee_name}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Abteilung</td><td style="padding: 10px; border: 1px solid #dee2e6;">{department}</td></tr>
                        <tr style="background: #f8f9fa;"><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Zeitraum</td><td style="padding: 10px; border: 1px solid #dee2e6;">{date_display}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Art</td><td style="padding: 10px; border: 1px solid #dee2e6;">{vacation_type_name}</td></tr>
                        <tr style="background: #f8f9fa;"><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Umfang</td><td style="padding: 10px; border: 1px solid #dee2e6;">{umfang}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Tage</td><td style="padding: 10px; border: 1px solid #dee2e6;">{dates_list_html}</td></tr>
                    </table>
                    <p style="background: #cce5ff; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;">
                        <strong>📋 Aktion erforderlich:</strong><br>
                        Bitte im <a href="http://drive.auto-greiner.de/urlaubsplaner">Greiner DRIVE Portal</a> genehmigen oder ablehnen.
                    </p>
                    <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
                    <p style="color: #6c757d; font-size: 12px;">Diese E-Mail wurde automatisch vom Greiner DRIVE Portal gesendet.</p>
                </div>
                """
                
                approver_emails = [a.get('approver_email') for a in approvers if a.get('approver_email') and a.get('priority') == 1]
                if not approver_emails:
                    approver_emails = [a.get('approver_email') for a in approvers if a.get('approver_email')]
                
                if approver_emails:
                    email_sent = graph.send_mail(sender_email=DRIVE_EMAIL, to_emails=approver_emails, subject=subject, body_html=body_html)
                    if email_sent:
                        print(f"✅ Batch-E-Mail gesendet für {len(dates)} Tage an {approver_emails}")
            except Exception as e:
                print(f"❌ Batch-E-Mail Fehler: {e}")
        
        return jsonify({
            'success': True,
            'booking_ids': booking_ids,
            'message': f'{len(dates)} Tag(e) beantragt',
            'email_sent': email_sent
        }), 201
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


@vacation_api.route('/cancel-batch', methods=['POST'])
def cancel_vacation_batch():
    """
    POST /api/vacation/cancel-batch
    
    TAG 113: Storniert mehrere Buchungen auf einmal.
    
    Body:
    {
        "booking_ids": [123, 124, 125],
        "reason": "optional"
    }
    """
    try:
        employee_id, ldap_username, employee_data = get_employee_from_session()
        
        if not employee_id:
            return jsonify({'success': False, 'error': 'Nicht angemeldet'}), 401
        
        data = request.get_json()
        booking_ids = data.get('booking_ids', [])
        reason = data.get('reason', 'Batch-Stornierung')
        
        if not booking_ids:
            return jsonify({'success': False, 'error': 'booking_ids erforderlich'}), 400

        with db_session() as conn:
            cursor = conn.cursor()

            # Prüfe Admin-Status
            is_admin = False
            cursor.execute("SELECT ad_groups FROM users WHERE username LIKE ? OR username = ?", (f"%{ldap_username}%", ldap_username))
            user_row = cursor.fetchone()
            if user_row and user_row[0]:
                try:
                    groups = json.loads(user_row[0]) if isinstance(user_row[0], str) else user_row[0]
                    is_admin = 'GRP_Urlaub_Admin' in groups
                except:
                    pass

            cancelled = []
            errors = []
            was_approved_any = False
            cancelled_dates = []
            booking_owner_name = None

            for bid in booking_ids:
                cursor.execute("""
                    SELECT vb.employee_id, vb.status, vb.booking_date, e.first_name || ' ' || e.last_name
                    FROM vacation_bookings vb
                    JOIN employees e ON vb.employee_id = e.id
                    WHERE vb.id = ?
                """, (bid,))
                row = cursor.fetchone()

                if not row:
                    errors.append(f"Buchung {bid} nicht gefunden")
                    continue

                is_own = row[0] == employee_id
                if not is_own and not is_admin:
                    errors.append(f"Keine Berechtigung für Buchung {bid}")
                    continue

                if row[1] == 'approved':
                    was_approved_any = True

                cursor.execute("""
                    UPDATE vacation_bookings SET status = 'cancelled',
                    comment = CASE WHEN comment IS NULL OR comment = '' THEN ? ELSE comment || ' | Storniert: ' || ? END
                    WHERE id = ?
                """, (reason, reason, bid))

                cancelled.append(bid)
                cancelled_dates.append(row[2])
                if not booking_owner_name:
                    booking_owner_name = row[3]

            conn.commit()
        
        # E-Mail-Benachrichtigung (eine für alle Tage)
        if cancelled and GRAPH_AVAILABLE:
            try:
                graph = GraphMailConnector()
                cancelled_by_name = f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}".strip()
                
                dates_formatted = []
                for d in sorted(cancelled_dates):
                    try:
                        date_obj = datetime.strptime(d, '%Y-%m-%d')
                        dates_formatted.append(date_obj.strftime('%d.%m.%Y'))
                    except:
                        dates_formatted.append(d)
                
                if len(dates_formatted) == 1:
                    date_display = dates_formatted[0]
                else:
                    date_display = f"{dates_formatted[0]} - {dates_formatted[-1]} ({len(dates_formatted)} Tage)"
                
                subject = f"🚫 Urlaub storniert: {booking_owner_name} - {len(cancelled)} Tage"
                
                body_html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px;">
                    <h2 style="color: #dc3545;">🚫 Urlaub storniert</h2>
                    <p><strong>{cancelled_by_name}</strong> hat {'genehmigten' if was_approved_any else 'beantragten'} Urlaub von <strong>{booking_owner_name}</strong> storniert.</p>
                    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                        <tr style="background: #f8f9fa;"><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Mitarbeiter</td><td style="padding: 10px; border: 1px solid #dee2e6;">{booking_owner_name}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Zeitraum</td><td style="padding: 10px; border: 1px solid #dee2e6;">{date_display}</td></tr>
                        <tr style="background: #f8f9fa;"><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Grund</td><td style="padding: 10px; border: 1px solid #dee2e6;">{reason}</td></tr>
                    </table>
                </div>
                """
                
                # E-Mail an HR wenn genehmigt war
                if was_approved_any:
                    graph.send_mail(sender_email=DRIVE_EMAIL, to_emails=[HR_EMAIL], subject=subject, body_html=body_html)
            except Exception as e:
                print(f"⚠️ Batch-Cancel E-Mail Fehler: {e}")
        
        return jsonify({
            'success': True,
            'cancelled': cancelled,
            'errors': errors,
            'message': f'{len(cancelled)} Buchung(en) storniert'
        })
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


@vacation_api.route('/locosoft-days', methods=['GET'])
def get_locosoft_days():
    """
    GET /api/vacation/locosoft-days?employee_id=X&year=2025
    GET /api/vacation/locosoft-days?locosoft_id=1001&year=2025
    
    TAG 113: Holt einzelne Abwesenheitstage aus Locosoft mit day_contingent.
    Wichtig für Kalenderanzeige von halben Tagen (24./31.12).
    
    Returns:
        [
            {'date': '2025-12-24', 'day_contingent': 0.5, 'reason': 'Url', 'is_half_day': True},
            {'date': '2025-12-25', 'day_contingent': 1.0, 'reason': 'Url', 'is_half_day': False},
            ...
        ]
    """
    if not LOCOSOFT_AVAILABLE:
        return jsonify({'success': False, 'error': 'Locosoft nicht verfügbar'}), 503
    
    year = request.args.get('year', datetime.now().year, type=int)
    locosoft_id = request.args.get('locosoft_id', type=int)
    employee_id = request.args.get('employee_id', type=int)
    
    # Wenn employee_id statt locosoft_id gegeben, umwandeln
    if employee_id and not locosoft_id:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT locosoft_id FROM employees WHERE id = ?", (employee_id,))
            row = cursor.fetchone()
            if row:
                locosoft_id = row[0]
    
    if not locosoft_id:
        return jsonify({'success': False, 'error': 'Kein locosoft_id oder employee_id angegeben'}), 400
    
    try:
        days = get_absence_days_for_employee(locosoft_id, year)
        return jsonify({
            'success': True,
            'locosoft_id': locosoft_id,
            'year': year,
            'days': days,
            'count': len(days),
            'half_days': [d for d in days if d.get('is_half_day')]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@vacation_api.route('/locosoft-days-bulk', methods=['POST'])
def get_locosoft_days_bulk():
    """
    POST /api/vacation/locosoft-days-bulk
    Body: {"locosoft_ids": [1001, 1002, 1003], "year": 2025}
    
    TAG 113: Bulk-Abfrage für Kalenderübersicht aller Mitarbeiter.
    
    Returns:
        {
            '1001': [{'date': '2025-12-24', 'day_contingent': 0.5, ...}, ...],
            '1002': [...],
            ...
        }
    """
    if not LOCOSOFT_AVAILABLE:
        return jsonify({'success': False, 'error': 'Locosoft nicht verfügbar'}), 503
    
    data = request.get_json() or {}
    locosoft_ids = data.get('locosoft_ids', [])
    year = data.get('year', datetime.now().year)
    
    if not locosoft_ids:
        return jsonify({'success': False, 'error': 'Keine locosoft_ids angegeben'}), 400
    
    try:
        result = get_absence_days_for_employees(locosoft_ids, year)
        # Keys zu Strings für JSON
        result_str_keys = {str(k): v for k, v in result.items()}
        return jsonify({
            'success': True,
            'year': year,
            'data': result_str_keys,
            'count': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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


# ============================================================
# PENDING-COUNT - TAG 116 (für Dashboard)
# ============================================================

@vacation_api.route('/pending-count', methods=['GET'])
def get_pending_count():
    """
    GET /api/vacation/pending-count
    
    Zählt offene Urlaubsanträge für Dashboard-Badge.
    Für Admins: Alle offenen Anträge
    Für Genehmiger: Nur eigene offenen Genehmigungen
    Für normale User: Eigene offene Anträge
    """
    try:
        employee_id, ldap_username, employee_data = get_employee_from_session()

        with db_session() as conn:
            cursor = conn.cursor()

            # Prüfe ob Admin
            is_admin = False
            if ldap_username:
                cursor.execute("""
                    SELECT COUNT(*) FROM ldap_group_mappings lgm
                    JOIN ldap_employee_mapping lem ON lgm.ldap_group_dn = lem.ldap_group_dn
                    WHERE lem.ldap_username = ? AND lgm.portal_feature = 'urlaub_admin'
                """, (ldap_username,))
                result = cursor.fetchone()
                is_admin = result and result[0] > 0

            if is_admin:
                # Alle offenen Anträge
                cursor.execute("""
                    SELECT COUNT(DISTINCT vb.employee_id || '-' || vb.booking_date)
                    FROM vacation_bookings vb
                    WHERE vb.status = 'pending'
                """)
            elif ldap_username and is_approver(ldap_username):
                # Offene Genehmigungen für diesen Genehmiger
                cursor.execute("""
                    SELECT COUNT(DISTINCT vb.employee_id || '-' || vb.booking_date)
                    FROM vacation_bookings vb
                    JOIN employees e ON vb.employee_id = e.id
                    JOIN vacation_approval_rules var ON var.employee_id = e.id
                    WHERE vb.status = 'pending'
                      AND var.approver_username = ?
                """, (ldap_username,))
            else:
                # Eigene offene Anträge
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM vacation_bookings vb
                    WHERE vb.status = 'pending' AND vb.employee_id = ?
                """, (employee_id,))

            count = cursor.fetchone()[0] or 0

        return jsonify({
            'success': True,
            'count': count,
            'is_admin': is_admin,
            'employee_id': employee_id
        })
        
    except Exception as e:
        return jsonify({'success': True, 'count': 0, 'error': str(e)})
