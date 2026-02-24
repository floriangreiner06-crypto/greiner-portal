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
from flask_login import login_required, current_user
from decorators.auth_decorators import admin_required, role_required
from datetime import datetime, date, timedelta
import json

# Zentrale DB-Utilities (TAG 117 - Migration abgeschlossen)
from api.db_utils import db_session, row_to_dict, rows_to_list

# PostgreSQL/SQLite Kompatibilitäts-Helper (TAG 136 - PostgreSQL Migration)
from api.db_connection import (
    get_db_type,
    sql_year,
    convert_placeholders,
    sql_placeholder
)

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

# TAG 219: Whitelist für Jahr (SQL-Injection-Schutz bei dynamischem View-Namen)
ALLOWED_YEARS = range(2020, 2031)

# Rollout SSOT: Kein pauschaler Weihnachten/Silvester-Abzug mehr.
# Halbe Tage (24.12., 31.12.) werden als normale Urlaubsbuchungen im Planer erfasst und in verbraucht gezählt.


def _validate_vacation_year(year):
    """Prüft Jahr gegen Whitelist. Returns (year, None) oder (None, error_response)."""
    if year is None or year not in ALLOWED_YEARS:
        return None, (jsonify({"error": "Ungültiges Jahr"}), 400)
    return year, None


def _check_substitute_vacation_conflict(cursor, substitute_employee_id, dates_list):
    """
    Vertretungsregel: Der Vertreter darf in dem Zeitraum keinen Urlaub buchen,
    in dem die von ihm vertretene Person abwesend ist (Urlaub/Abwesenheit).
    substitute_employee_id = Mitarbeiter, der buchen will (ist Vertreter).
    dates_list = Liste von Datumsstrings 'YYYY-MM-DD'.
    Returns: None wenn OK; sonst (blocked_dates, vertretene_name) für Fehlermeldung.
    """
    if not dates_list:
        return None
    try:
        # Wen vertritt dieser Mitarbeiter? (employee_id = vertretene Person)
        cursor.execute("""
            SELECT sr.employee_id, e.first_name || ' ' || COALESCE(e.last_name, '') as vertretene_name
            FROM substitution_rules sr
            JOIN employees e ON e.id = sr.employee_id
            WHERE sr.substitute_id = %s
        """, (substitute_employee_id,))
        substituted = cursor.fetchall()
        if not substituted:
            return None
        placeholders = ','.join(['%s'] * len(dates_list))
        blocked = []
        # Name der Person, die an den blockierten Tagen tatsächlich Urlaub hat (für Fehlermeldung)
        conflict_vertretene_name = None
        for row in substituted:
            vertretene_id = row[0]
            vname = row[1] if len(row) > 1 else 'Mitarbeiter'
            cursor.execute(f"""
                SELECT booking_date FROM vacation_bookings
                WHERE employee_id = %s AND booking_date IN ({placeholders})
                AND status IN ('pending', 'approved')
            """, (vertretene_id,) + tuple(dates_list))
            found = cursor.fetchall()
            for r in found:
                blocked.append(str(r[0]))
                if conflict_vertretene_name is None:
                    conflict_vertretene_name = vname
        if blocked:
            return (sorted(set(blocked)), conflict_vertretene_name or (substituted[0][1] if substituted else 'Mitarbeiter'))
        return None
    except Exception:
        # Tabelle substitution_rules kann fehlen (Legacy)
        return None


def _check_max_absence_per_dept_location(cursor, employee_id, dates_list, vacation_type_id):
    """
    Max. Abwesenheit pro Abteilung und Standort (nur planbar: Urlaub + Schulung; Krankheit nicht).
    Prüft ob durch die neue Buchung die Grenze (Default 50%, editierbar pro Abteilung/Standort) überschritten würde.
    vacation_type_id: 1 = Urlaub, 9 = Schulung (nur diese prüfen).
    Returns: None wenn OK; sonst (blocked_dates, max_percent, current_absent, total) für Fehlermeldung.
    """
    if not dates_list or vacation_type_id not in (1, 9):
        return None
    try:
        q = "SELECT department_name, COALESCE(NULLIF(TRIM(location), ''), 'Deggendorf') as loc FROM employees WHERE id = " + sql_placeholder() + " AND aktiv = true"
        cursor.execute(convert_placeholders(q), (employee_id,))
        row = cursor.fetchone()
        if not row:
            return None
        department_name, location = row[0], (row[1] or '') or 'Deggendorf'
        # Standort: Landau vs Deggendorf (einheitlich für Abgleich)
        loc_normalized = 'Landau' if location and 'landau' in str(location).lower() else 'Deggendorf'

        # Max-% aus Tabelle (Default 50)
        max_percent = 50
        try:
            cursor.execute(convert_placeholders("""
                SELECT max_absence_percent FROM department_absence_limits
                WHERE department_name = """ + sql_placeholder() + """ AND location = """ + sql_placeholder()),
                (department_name, loc_normalized))
            r = cursor.fetchone()
            if r:
                max_percent = int(r[0])
        except Exception:
            pass

        # SQL: Standort = Landau wenn location "landau" enthält, sonst Deggendorf
        loc_case = "CASE WHEN LOWER(COALESCE(e.location,'')) LIKE '%landau%' THEN 'Landau' ELSE 'Deggendorf' END"
        ph = sql_placeholder()
        cursor.execute(convert_placeholders(f"""
            SELECT COUNT(*) FROM employees e
            WHERE e.department_name = {ph}
              AND {loc_case} = {ph}
              AND e.aktiv = true
        """), (department_name, loc_normalized))
        total = cursor.fetchone()[0] or 0
        if total == 0:
            return None

        blocked = []
        first_absent = 0
        for d in dates_list:
            cursor.execute(convert_placeholders(f"""
                SELECT COUNT(DISTINCT vb.employee_id)
                FROM vacation_bookings vb
                JOIN employees e ON e.id = vb.employee_id
                WHERE e.department_name = {ph}
                  AND {loc_case} = {ph}
                  AND e.aktiv = true
                  AND vb.booking_date = {ph}
                  AND vb.vacation_type_id IN (1, 9)
                  AND vb.status IN ('pending', 'approved')
            """), (department_name, loc_normalized, d))
            absent = cursor.fetchone()[0] or 0
            if (absent + 1) / total > max_percent / 100.0:
                blocked.append(d)
                if first_absent == 0:
                    first_absent = absent
        if blocked:
            return (sorted(blocked), max_percent, first_absent, total)
        return None
    except Exception:
        # Tabelle department_absence_limits kann fehlen
        return None


# E-Mail-Konfiguration
HR_EMAIL = 'hr@auto-greiner.de'  # HR-Mailbox für Locosoft-Einträge
DRIVE_EMAIL = 'drive@auto-greiner.de'  # Absender

# ============================================================================
# ERROR HANDLERS (TAG 136 - PostgreSQL Migration Bug Fix)
# ============================================================================

@vacation_api.errorhandler(Exception)
def handle_vacation_error(e):
    """
    Globaler Error Handler für Vacation API.
    Stellt sicher, dass alle Fehler als JSON zurückgegeben werden.
    """
    import traceback
    return jsonify({
        'success': False,
        'error': str(e),
        'traceback': traceback.format_exc()
    }), 500


def get_employee_from_session():
    """Holt employee_id aus Flask-Login Session via ldap_employee_mapping."""
    user_id = session.get('_user_id')
    ldap_username = None

    if not user_id:
        ldap_username = (
            session.get('username') or
            session.get('user') or
            session.get('ldap_user') or
            session.get('sAMAccountName')
        )
        if not ldap_username and getattr(current_user, 'is_authenticated', False):
            ldap_username = getattr(current_user, 'username', None)
        if not ldap_username:
            return None, None, None

        ldap_username = (ldap_username or '').strip()
        ldap_username = ldap_username.split('@')[0] if '@' in ldap_username else ldap_username
    else:
        with db_session() as conn:
            cursor = conn.cursor()

            query = f"SELECT username FROM users WHERE id = {sql_placeholder()}"
            query = convert_placeholders(query)
            cursor.execute(query, (user_id,))
            user_row = cursor.fetchone()

            if not user_row:
                return None, None, None

            username = user_row[0]
            ldap_username = username.split('@')[0] if '@' in username else username

    ldap_username = (ldap_username or '').strip().lower()

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
            WHERE LOWER(TRIM(COALESCE(lem.ldap_username, ''))) = %s AND e.aktiv = true
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


def is_vacation_admin(ldap_username=None):
    """
    Prüft ob User Urlaubs-Admin ist (TAG 127)
    Admins können für andere Mitarbeiter Abwesenheiten eintragen
    """
    from flask_login import current_user

    if not current_user.is_authenticated:
        return False

    # Portal-Admin ist immer auch Urlaubs-Admin
    if getattr(current_user, 'portal_role', '') == 'admin':
        return True

    # GRP_Urlaub_Admin Gruppe
    user_groups = getattr(current_user, 'groups', []) or []
    if isinstance(user_groups, str):
        try:
            user_groups = json.loads(user_groups)
        except:
            user_groups = []

    if 'GRP_Urlaub_Admin' in user_groups:
        return True

    # Explizit erlaubte User
    allowed_users = ['florian.greiner', 'vanessa.groll', 'christian.aichinger', 'sandra.brendel']
    username = ldap_username or getattr(current_user, 'username', '') or ''
    username_clean = username.lower().split('@')[0]

    return username_clean in allowed_users


def _compute_rest_display(anspruch, resturlaub_view, loco_urlaub=0):
    """
    SSOT für Resturlaub-Anzeige: min(Portal-Rest, Anspruch − Locosoft-Urlaub).
    Locosoft liefert nur 'urlaub' (Url, BUr); Zeitausgleich (ZA) mindert Rest nicht.
    """
    anspruch = float(anspruch or 0)
    rest = max(0.0, round(float(resturlaub_view or 0), 1))
    loco = float(loco_urlaub or 0)
    if loco > 0:
        capped = max(0.0, round(anspruch - loco, 1))
        rest = min(rest, capped)
    return max(0.0, round(rest, 1))


def _get_available_rest_days_for_validation(cursor, employee_id, booking_year, locosoft_id=None):
    """
    Berechnet verfügbaren Resturlaub für Validierung – gleiche Logik wie Balance-Anzeige.
    Verhindert „Liste zeigt 16 Rest, Buchung sagt zu wenig“ (Sandra) und „0 Rest, Buchung möglich“ (Herbert).
    Returns: (available_days: float, resturlaub_info: dict | None)
    """
    booking_year, _ = _validate_vacation_year(booking_year)
    if not booking_year:
        return 0.0, None
    try:
        view_name = f'v_vacation_balance_{booking_year}'
        query = f"""
            SELECT anspruch, verbraucht, geplant, resturlaub
            FROM {view_name}
            WHERE employee_id = {sql_placeholder()}
        """
        query = convert_placeholders(query)
        cursor.execute(query, (employee_id,))
        row = cursor.fetchone()
        if not row:
            return 0.0, None
        anspruch_raw = float(row[0] or 0)
        anspruch = max(0.0, round(float(anspruch_raw), 1))
        resturlaub_view_raw = float(row[3]) if row[3] is not None else (anspruch_raw - (float(row[1] or 0) + float(row[2] or 0)))
        resturlaub_view = max(0.0, round(float(resturlaub_view_raw), 1))
        loco_urlaub = 0
        if LOCOSOFT_AVAILABLE and locosoft_id:
            try:
                loco = get_absences_for_employee(locosoft_id, booking_year)
                loco_urlaub = (loco or {}).get('urlaub', 0) or 0
            except Exception:
                pass
        available_days = _compute_rest_display(anspruch, resturlaub_view, loco_urlaub)
        info = {'anspruch': anspruch, 'resturlaub_view': resturlaub_view, 'verfuegbar': available_days}
        return available_days, info
    except Exception as e:
        print(f"⚠️ _get_available_rest_days_for_validation: {e}")
        return 0.0, None


def get_employee_by_id(employee_id):
    """Holt Employee-Daten für einen anderen Mitarbeiter (TAG 127)"""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                e.id,
                e.first_name,
                e.last_name,
                e.email,
                e.department_name,
                e.is_manager,
                lem.locosoft_id,
                lem.ldap_username
            FROM employees e
            LEFT JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
            WHERE e.id = %s AND e.aktiv = true
        """, (employee_id,))
        result = cursor.fetchone()

        if result:
            return {
                'employee_id': result[0],
                'first_name': result[1],
                'last_name': result[2],
                'email': result[3],
                'department': result[4],
                'is_manager': bool(result[5]),
                'locosoft_id': result[6],
                'ldap_username': result[7]
            }
        return None


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
@login_required
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
        
        year = request.args.get('year', datetime.now().year, type=int)
        year, err = _validate_vacation_year(year)
        if err:
            return err

        # TAG 198: Automatische Jahreswechsel-Logik - stelle sicher dass Jahr existiert
        try:
            from api.vacation_year_utils import ensure_vacation_year_setup_simple
            ensure_vacation_year_setup_simple(year)
        except Exception as e:
            print(f"⚠️ Jahreswechsel-Setup fehlgeschlagen: {e}")

        with db_session() as conn:
            cursor = conn.cursor()

            # TAG 139: View hat 'department' nicht 'department_name'
            # TAG 198: Prüfe ob View existiert, sonst erstelle sie
            try:
                cursor.execute(f"""
                    SELECT
                        employee_id,
                        name,
                        department,
                        location,
                        anspruch,
                        verbraucht,
                        geplant,
                        resturlaub
                    FROM v_vacation_balance_{year}
                    WHERE employee_id = %s
                """, (employee_id,))
            except Exception as view_error:
                # View existiert nicht - erstelle sie
                if 'does not exist' in str(view_error).lower() or 'relation' in str(view_error).lower():
                    try:
                        from api.vacation_year_utils import ensure_vacation_year_setup_simple
                        ensure_vacation_year_setup_simple(year)
                        # Retry
                        cursor.execute(f"""
                            SELECT
                                employee_id,
                                name,
                                department,
                                location,
                                anspruch,
                                verbraucht,
                                geplant,
                                resturlaub
                            FROM v_vacation_balance_{year}
                            WHERE employee_id = %s
                        """, (employee_id,))
                    except Exception as retry_error:
                        return jsonify({
                            'success': False,
                            'error': f'View für {year} konnte nicht erstellt werden: {str(retry_error)}'
                        }), 500
                else:
                    raise

            row = cursor.fetchone()

        if not row:
            return jsonify({
                'success': False,
                'error': f'Keine Urlaubsdaten für {year}',
                'employee_id': employee_id
            }), 404
        
        anspruch_raw = row[4]
        anspruch = max(0, round(float(anspruch_raw or 0), 1))
        balance = {
            'employee_id': row[0],
            'name': row[1],
            'department': row[2],
            'location': row[3],
            'anspruch': anspruch,
            'verbraucht': row[5],
            'geplant': row[6],
            'resturlaub': row[7]
        }
        # Resturlaub = View-Wert (Portal)
        if balance['resturlaub'] is None:
            balance['resturlaub'] = max(0, round((anspruch_raw or 0) - (balance.get('verbraucht') or 0) - (balance.get('geplant') or 0), 1))
        else:
            balance['resturlaub'] = max(0, round(float(balance['resturlaub']), 1))

        # Locosoft: Rest = min(Portal-Rest, Anspruch − Locosoft-Urlaub), damit Kalender und Rest übereinstimmen
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
                loco_urlaub = locosoft_absences.get('urlaub', 0) or 0
                balance['resturlaub'] = _compute_rest_display(
                    balance.get('anspruch'), balance['resturlaub'], loco_urlaub
                )

        # Genehmiger-Infos: Fehler hier dürfen my-balance nicht zu 500 führen (strukturell entkoppeln)
        try:
            approver_info = get_approver_summary(ldap_username)
            if not approver_info.get('is_approver') and not approver_info.get('is_admin'):
                from flask_login import current_user
                session_username = getattr(current_user, 'username', None)
                if session_username and str(session_username).strip().lower() != (ldap_username or '').strip().lower():
                    approver_info = get_approver_summary(session_username)
        except Exception as e:
            approver_info = {
                'is_approver': False,
                'is_admin': False,
                'team_size': 0,
                'groups': [],
                'pending_requests': 0,
            }
            print(f"⚠️ get_approver_summary fehlgeschlagen (my-balance liefert trotzdem Balance): {e}")

        payload = {
            'success': True,
            'year': year,
            'ldap_username': ldap_username,
            'employee': employee_data,
            'balance': balance,
            'locosoft_absences': locosoft_absences,
            'approver_info': approver_info
        }
        # Debug: warum wird Genehmiger nicht erkannt? ?debug_approver=1 an my-balance hängen
        if request.args.get('debug_approver'):
            from api.vacation_approver_service import _normalize_ldap_username
            norm = _normalize_ldap_username(ldap_username)
            from flask_login import current_user
            session_user = getattr(current_user, 'username', None)
            payload['debug_approver'] = {
                'ldap_username': ldap_username,
                'normalized': norm,
                'session_username': session_user,
                'approver_info_is_approver': approver_info.get('is_approver'),
                'approver_info_is_admin': approver_info.get('is_admin'),
            }
            try:
                with db_session() as conn:
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT id, username, ad_groups FROM users
                        WHERE LOWER(TRIM(SPLIT_PART(COALESCE(username,'') || '@', '@', 1))) = %s
                    """, (norm or '',))
                    row = cur.fetchone()
                    if row:
                        raw = row.get('ad_groups')
                        payload['debug_approver']['user_found'] = True
                        payload['debug_approver']['user_id'] = row.get('id')
                        payload['debug_approver']['username_in_db'] = row.get('username')
                        try:
                            groups = json.loads(raw) if isinstance(raw, str) else (raw if isinstance(raw, list) else [])
                            payload['debug_approver']['ad_groups_count'] = len(groups)
                            payload['debug_approver']['ad_groups_preview'] = [str(g)[:50] for g in (groups or [])[:10]]
                        except Exception as e:
                            payload['debug_approver']['ad_groups_error'] = str(e)
                    else:
                        payload['debug_approver']['user_found'] = False
            except Exception as e:
                payload['debug_approver']['error'] = str(e)

        resp = jsonify(payload)
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        return resp
        
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
@login_required
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
        
        year = request.args.get('year', datetime.now().year, type=int)
        year, err = _validate_vacation_year(year)
        if err:
            return err

        # TAG 198: Automatische Jahreswechsel-Logik
        try:
            from api.vacation_year_utils import ensure_vacation_year_setup_simple
            ensure_vacation_year_setup_simple(year)
        except Exception as e:
            print(f"⚠️ Jahreswechsel-Setup fehlgeschlagen: {e}")
        
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
        placeholders = ','.join(['%s'] * len(team_ids))

        with db_session() as conn:
            cursor = conn.cursor()

            # TAG 139: View hat 'department' nicht 'department_name'
            cursor.execute(f"""
                SELECT
                    employee_id,
                    name,
                    department,
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

                anspruch_raw = row[4] or 27
                anspruch = max(0, round(float(anspruch_raw or 0), 1))
                resturlaub_raw = row[7] if row[7] is not None else (anspruch_raw - (row[5] or 0) - (row[6] or 0))
                resturlaub_view = max(0, round(float(resturlaub_raw or 0), 1))
                resturlaub_display = _compute_rest_display(anspruch, resturlaub_view, urlaub)
                verfuegbar = resturlaub_display
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
                    'resturlaub': resturlaub_display,
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
        
        # TAG 198: Admin-Bypass - Admin kann alle sehen (Prüfung VOR is_approver)
        is_admin = is_vacation_admin(ldap_username)
        
        # TAG 198: Nur prüfen wenn nicht Admin (Admins sind automatisch Approver)
        if not is_admin and not is_approver(ldap_username):
            return jsonify({
                'success': False,
                'error': 'Keine Genehmiger-Berechtigung'
            }), 403
        
        team_members = get_team_for_approver(ldap_username)
        
        # TAG 198: Admin sieht alle pending Buchungen (nicht nur Team)
        if is_admin:
            # Admin: Alle pending Buchungen
            query_filter = "vb.status = 'pending'"
            query_params = []
        else:
            # Normaler Genehmiger: Nur Team-Mitglieder
            if not team_members:
                return jsonify({
                    'success': True,
                    'pending': [],
                    'count': 0
                })
            team_ids = [m['employee_id'] for m in team_members]
            placeholders = ','.join(['%s'] * len(team_ids))
            query_filter = f"vb.employee_id IN ({placeholders}) AND vb.status = 'pending'"
            query_params = team_ids

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
                WHERE {query_filter}
                ORDER BY vb.booking_date ASC
            """, query_params)

            pending = []
            for row in cursor.fetchall():
                # TAG 198: Für Admin kann member_info leer sein (kein Team-Filter)
                member_info = next((m for m in (team_members or []) if m['employee_id'] == row[1]), {})
                
                # TAG 198: Datum korrekt formatieren (Date-Objekt zu String)
                booking_date = row[3]
                if hasattr(booking_date, 'isoformat'):
                    booking_date = booking_date.isoformat()
                elif not isinstance(booking_date, str):
                    booking_date = str(booking_date)

                pending.append({
                    'booking_id': row[0],
                    'employee_id': row[1],
                    'employee_name': row[2],
                    'date': booking_date,  # TAG 198: Immer String-Format
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

        is_admin = is_vacation_admin(ldap_username)
        is_approver_flag = is_approver(ldap_username)

        if not is_admin and not is_approver_flag:
            return jsonify({'success': False, 'error': 'Keine Genehmiger-Berechtigung'}), 403

        data = request.get_json() or {}
        booking_id = data.get('booking_id')
        comment = data.get('comment', '')

        if not booking_id:
            return jsonify({'success': False, 'error': 'booking_id erforderlich'}), 400

        with db_session() as conn:
            cursor = conn.cursor()
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
                WHERE vb.id = %s
            """, (booking_id,))
            booking = cursor.fetchone()

        if not booking:
            return jsonify({'success': False, 'error': 'Buchung nicht gefunden'}), 404

        if not is_admin:
            team_members = get_team_for_approver(ldap_username)
            team_ids = [m['employee_id'] for m in team_members]

            if not team_ids:
                return jsonify({
                    'success': False,
                    'error': 'Kein Team zugeordnet. Bitte Admin kontaktieren.'
                }), 403

            if booking[0] not in team_ids:
                return jsonify({
                    'success': False,
                    'error': f'Keine Berechtigung für diese Buchung. Team-Größe: {len(team_ids)}'
                }), 403

        with db_session() as conn:
            cursor = conn.cursor()

            if booking[1] != 'pending':
                return jsonify({'success': False, 'error': f'Buchung hat bereits Status: {booking[1]}'}), 400

            # Genehmigen
            # TAG 136: PostgreSQL-kompatible Query
            query = f"""
                UPDATE vacation_bookings
                SET status = 'approved',
                    approved_by = {sql_placeholder()},
                    approved_at = {sql_placeholder()},
                    comment = CASE WHEN comment IS NULL OR comment = '' THEN {sql_placeholder()} ELSE comment || ' | Genehmigt: ' || {sql_placeholder()} END
                WHERE id = {sql_placeholder()}
            """
            query = convert_placeholders(query)
            cursor.execute(query, (employee_id, datetime.now().isoformat(), comment, comment, booking_id))

            conn.commit()

        # Ab hier: Buchung ist bereits genehmigt. E-Mails/Kalender dürfen Fehler nicht an den User durchreichen (Margit-Bug).
        approver_name = f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}".strip()
        booking_details = {
            'date': booking[2],
            'day_part': booking[3],
            'vacation_type': booking[5] or 'Urlaub',
            'employee_name': booking[6],
            'employee_email': booking[7],
            'department': booking[8] or ''
        }
        hr_email_sent = False
        employee_email_sent = False
        calendar_added = False

        try:
            hr_email_sent = send_approval_email_to_hr(booking_details, approver_name)
            employee_email_sent = send_approval_notification_to_employee(booking_details, approver_name)
            calendar_result = add_to_team_calendar(booking_details)
            if isinstance(calendar_result, dict):
                calendar_added = calendar_result.get('drive_ok') or bool(calendar_result.get('employee_event_id'))
                if calendar_result.get('employee_event_id') or calendar_result.get('drive_event_id'):
                    update_placeholders = []
                    update_args = []
                    if calendar_result.get('employee_event_id'):
                        update_placeholders.append(f"calendar_event_id_employee = {sql_placeholder()}")
                        update_args.append(calendar_result['employee_event_id'])
                    if calendar_result.get('drive_event_id'):
                        update_placeholders.append(f"calendar_event_id_drive = {sql_placeholder()}")
                        update_args.append(calendar_result['drive_event_id'])
                    if update_placeholders:
                        update_args.append(booking_id)
                        query = f"UPDATE vacation_bookings SET {', '.join(update_placeholders)} WHERE id = {sql_placeholder()}"
                        query = convert_placeholders(query)
                        with db_session() as conn2:
                            cur2 = conn2.cursor()
                            cur2.execute(query, tuple(update_args))
                            conn2.commit()
            else:
                calendar_added = bool(calendar_result)
        except Exception as notify_err:
            import traceback
            print(f"⚠️ Approve: E-Mail/Kalender fehlgeschlagen (Buchung ist trotzdem genehmigt): {notify_err}")
            traceback.print_exc()

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
        
        # TAG 198: Admin-Bypass - Admin kann alle ablehnen (Prüfung VOR is_approver)
        is_admin = is_vacation_admin(ldap_username)
        
        # TAG 198: Nur prüfen wenn nicht Admin (Admins sind automatisch Approver)
        if not is_admin and not is_approver(ldap_username):
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
                WHERE vb.id = %s
            """, (booking_id,))

            booking = cursor.fetchone()

            if not booking:
                return jsonify({'success': False, 'error': 'Buchung nicht gefunden'}), 404

            # TAG 198: Team-Validierung nur für normale Genehmiger (nicht Admin)
            if not is_admin:
                if not team_ids:
                    return jsonify({
                        'success': False, 
                        'error': 'Kein Team zugeordnet. Bitte Admin kontaktieren.'
                    }), 403
                
                if booking[0] not in team_ids:
                    return jsonify({
                        'success': False, 
                        'error': f'Keine Berechtigung für diese Buchung. Team-Größe: {len(team_ids)}'
                    }), 403

            if booking[1] != 'pending':
                return jsonify({'success': False, 'error': f'Buchung hat bereits Status: {booking[1]}'}), 400

            # Ablehnen
            # TAG 136: PostgreSQL-kompatible Query
            query = f"""
                UPDATE vacation_bookings
                SET status = 'rejected',
                    approved_by = {sql_placeholder()},
                    approved_at = {sql_placeholder()},
                    comment = CASE WHEN comment IS NULL OR comment = '' THEN {sql_placeholder()} ELSE comment || ' | Abgelehnt: ' || {sql_placeholder()} END
                WHERE id = {sql_placeholder()}
            """
            query = convert_placeholders(query)
            cursor.execute(query, (employee_id, datetime.now().isoformat(), reason, reason, booking_id))

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
@login_required
def get_all_balances():
    """
    GET /api/vacation/balance

    Gibt Urlaubssalden für alle Mitarbeiter zurück (für Urlaubsplaner-Teamansicht).
    Jeder eingeloggte User darf die Liste laden (hr/admin nur für Admin-Views erforderlich).
    TAG 123: Erweitert um has_ad_mapping Flag für Mitarbeiter ohne AD-Zuordnung.
    Security-Fix: Zuvor @role_required(['hr','admin']) → Mitarbeiter sahen leere Planer-Liste.
    """
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        year, err = _validate_vacation_year(year)
        if err:
            return err
        department = request.args.get('department', None)
        location = request.args.get('location', None)

        # TAG 198: Automatische Jahreswechsel-Logik
        try:
            from api.vacation_year_utils import ensure_vacation_year_setup_simple
            ensure_vacation_year_setup_simple(year)
        except Exception as e:
            print(f"⚠️ Jahreswechsel-Setup fehlgeschlagen: {e}")

        with db_session() as conn:
            cursor = conn.cursor()

            # Erst: Mitarbeiter mit AD-Mapping ermitteln
            cursor.execute("""
                SELECT employee_id FROM ldap_employee_mapping WHERE ldap_username IS NOT NULL
            """)
            employees_with_ad = {row[0] for row in cursor.fetchall()}

            # TAG 213: Mitarbeiter, die im Urlaubsplaner nicht angezeigt werden sollen
            cursor.execute("""
                SELECT employee_id FROM employee_vacation_settings
                WHERE show_in_planner = false
            """)
            hide_in_planner_ids = {row[0] for row in cursor.fetchall()}

            # Dann: Balance-Daten holen
            # TAG 139: View hat 'department' nicht 'department_name'
            query = f"""
                SELECT
                    employee_id,
                    name,
                    department,
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
                query += " AND department = %s"
                params.append(department)

            if location:
                query += " AND location = %s"
                params.append(location)

            query += " ORDER BY name"

            cursor.execute(query, params)
            balance_rows = cursor.fetchall()

            # Locosoft-Urlaub holen, damit Rest = min(Portal-Rest, Anspruch − Locosoft) (Kalender zeigt beides)
            emp_to_loco = {}
            if LOCOSOFT_AVAILABLE and balance_rows:
                cursor.execute("""
                    SELECT id, locosoft_id FROM employees
                    WHERE aktiv = true AND locosoft_id IS NOT NULL
                """)
                emp_to_loco = {row[0]: row[1] for row in cursor.fetchall()}
            loco_urlaub_by_emp = {}
            if emp_to_loco:
                try:
                    loco_to_emp = {v: k for k, v in emp_to_loco.items()}
                    loco_absences = get_absences_for_employees(list(loco_to_emp.keys()), year)
                    for loco_id, data in loco_absences.items():
                        emp_id = loco_to_emp.get(loco_id)
                        if emp_id is not None:
                            loco_urlaub_by_emp[emp_id] = data.get('urlaub', 0) or 0
                except Exception as e:
                    print(f"⚠️ Locosoft für Balance: {e}")

            balances = []
            for row in balance_rows:
                emp_id = row[0]
                if emp_id in hide_in_planner_ids:
                    continue
                has_ad = emp_id in employees_with_ad
                dept_name = row[2]
                anspruch_raw = row[4] or 0
                anspruch = max(0, round(float(anspruch_raw or 0), 1))
                resturlaub_view_raw = row[7] if row[7] is not None else (anspruch_raw - (row[5] or 0) - (row[6] or 0))
                resturlaub_view = max(0, round(float(resturlaub_view_raw or 0), 1))
                loco_u = loco_urlaub_by_emp.get(emp_id, 0) or 0
                resturlaub_display = _compute_rest_display(anspruch, resturlaub_view, loco_u)

                # TAG 123: Mitarbeiter ohne AD-Mapping in spezielle Gruppe
                if not has_ad:
                    display_dept = f"⚠️ {dept_name or 'Ohne Abteilung'} (kein AD)"
                else:
                    display_dept = dept_name

                balances.append({
                    'employee_id': emp_id,
                    'name': row[1],
                    'department_name': display_dept,
                    'department_original': dept_name,  # Original für Filter
                    'location': row[3],
                    'anspruch': anspruch,
                    'verbraucht': row[5],
                    'geplant': row[6],
                    'resturlaub': resturlaub_display,
                    'has_ad_mapping': has_ad
                })

        resp = jsonify({
            'success': True,
            'year': year,
            'count': len(balances),
            'filters': {
                'department': department,
                'location': location
            },
            'balances': balances
        })
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        return resp

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
    TAG 123: Erweitert um Locosoft absence_calendar Daten!

    Kombiniert:
    1. Portal vacation_bookings (approved, pending)
    2. Locosoft absence_calendar (Url, BUr, ZA., Krn, etc.)
    """
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        bookings = []
        booked_dates = {}  # {employee_id: set(dates)} - um Duplikate zu vermeiden

        with db_session() as conn:
            cursor = conn.cursor()

            # 1. Portal-Buchungen (wie bisher)
            # TAG 136: PostgreSQL-kompatible Query mit sql_year() Helper
            query = f"""
                SELECT
                    vb.id,
                    vb.employee_id,
                    vb.booking_date,
                    vb.day_part,
                    vb.status,
                    vb.vacation_type_id
                FROM vacation_bookings vb
                WHERE {sql_year('vb.booking_date')} = {sql_placeholder()}
                  AND vb.status IN ('approved', 'pending')
                ORDER BY vb.booking_date
            """
            query = convert_placeholders(query)
            # TAG 213 FIX: PostgreSQL erwartet Integer für EXTRACT(YEAR FROM ...) Vergleich
            cursor.execute(query, (year,))

            for row in cursor.fetchall():
                emp_id = row[1]
                date = row[2]
                # TAG 136: Konvertiere Date-Objekt zu String (PostgreSQL gibt date zurück)
                if hasattr(date, 'isoformat'):
                    date = date.isoformat()
                elif not isinstance(date, str):
                    date = str(date)

                # Merke gebuchte Daten pro Mitarbeiter
                if emp_id not in booked_dates:
                    booked_dates[emp_id] = set()
                booked_dates[emp_id].add(date)

                bookings.append({
                    'id': row[0],
                    'employee_id': emp_id,
                    'date': date,
                    'day_part': row[3],
                    'status': row[4],
                    'type_id': row[5],
                    'source': 'portal'
                })

            # 2. Locosoft-Mapping holen (employee_id -> locosoft_id)
            # TAG 213 FIX: PostgreSQL verwendet BOOLEAN, nicht INTEGER (aktiv = true statt aktiv = 1)
            cursor.execute("""
                SELECT e.id, e.locosoft_id
                FROM employees e
                WHERE e.aktiv = true AND e.locosoft_id IS NOT NULL
            """)
            emp_to_loco = {row[0]: row[1] for row in cursor.fetchall()}
            loco_to_emp = {v: k for k, v in emp_to_loco.items()}

        # 3. Locosoft-Abwesenheiten laden (nur wenn Service verfügbar)
        if LOCOSOFT_AVAILABLE and loco_to_emp:
            try:
                locosoft_ids = list(loco_to_emp.keys())
                loco_days = get_absence_days_for_employees(locosoft_ids, year)

                # Vacation Type Mapping für Locosoft-Gründe
                # TAG 198: Korrigiert - Frontend CLS: {1:'urlaub', 2:'urlaub', 3:'krank', 5:'krank', 6:'za', 9:'schulung'}
                # Portal: type_id 3 = "Urlaubstag (abgelehnt)", type_id 5 = "Krankheit", type_id 9 = "Schulung"
                LOCO_TYPE_MAP = {
                    'Url': 1,   # Urlaub
                    'BUr': 1,   # Bezahlter Urlaub
                    'ZA.': 6,   # Zeitausgleich
                    'Krn': 5,   # TAG 198: Krank → type_id 5 (Krankheit), nicht 3!
                    'Sch': 9,   # TAG 198: Schulung → type_id 9, nicht 5!
                    'Sem': 9,   # TAG 198: Seminar → type_id 9 (Schulung)
                }

                for loco_id, days in loco_days.items():
                    emp_id = loco_to_emp.get(loco_id)
                    if not emp_id:
                        continue

                    for day in days:
                        date = day['date']

                        # Nur hinzufügen wenn nicht bereits im Portal gebucht
                        if emp_id in booked_dates and date in booked_dates[emp_id]:
                            continue

                        reason = day.get('reason', 'Url')
                        type_id = LOCO_TYPE_MAP.get(reason, 1)
                        day_contingent = day.get('day_contingent', 1.0)

                        # day_part basierend auf day_contingent
                        if day_contingent < 1.0:
                            day_part = 'half'
                        else:
                            day_part = 'full'

                        bookings.append({
                            'id': f"loco_{loco_id}_{date}",  # Pseudo-ID
                            'employee_id': emp_id,
                            'date': date,
                            'day_part': day_part,
                            'status': 'approved',  # Locosoft = bereits genehmigt
                            'type_id': type_id,
                            'source': 'locosoft',
                            'reason': reason,
                            'day_contingent': day_contingent
                        })
            except Exception as loco_err:
                print(f"Locosoft-Fehler in all-bookings: {loco_err}")

        # Sortieren nach Datum (TAG 139: str() für gemischte Typen)
        bookings.sort(key=lambda x: str(x['date']))

        return jsonify({
            'success': True,
            'year': year,
            'count': len(bookings),
            'bookings': bookings,
            'locosoft_included': LOCOSOFT_AVAILABLE
        })

    except Exception as e:
        import traceback
        print(f"❌ ERROR in /all-bookings: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_api.route('/blocks-and-free-days', methods=['GET'])
@login_required
def get_blocks_and_free_days():
    """
    GET /api/vacation/blocks-and-free-days?year=2026
    
    TAG 213: Öffentlicher Endpunkt für Frontend (kombiniert Urlaubssperren und freie Tage)
    Gibt Daten im Format zurück, das das Frontend erwartet.
    """
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        
        blocks_dict = {}  # {date: [{department, reason}]}
        free_days_dict = {}  # {date: {description, affects_entitlement}}
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            # 1. Urlaubssperren laden (department oder employee_ids für spezifische MA)
            cursor.execute("""
                SELECT block_date, department_name, reason, employee_ids
                FROM vacation_blocks
                WHERE EXTRACT(YEAR FROM block_date) = %s
                ORDER BY block_date, department_name
            """, (year,))
            
            for row in cursor.fetchall():
                date_str = row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0])
                if date_str not in blocks_dict:
                    blocks_dict[date_str] = []
                emp_ids = None
                if len(row) > 3 and row[3]:
                    try:
                        emp_ids = [int(x.strip()) for x in str(row[3]).split(',') if x.strip().isdigit()]
                    except (ValueError, AttributeError):
                        pass
                blocks_dict[date_str].append({
                    'department': row[1] or '',
                    'reason': row[2] or '',
                    'employee_ids': emp_ids
                })
            
            # 2. Freie Tage laden
            cursor.execute("""
                SELECT free_date, description, affects_vacation_entitlement
                FROM free_days
                WHERE EXTRACT(YEAR FROM free_date) = %s
                ORDER BY free_date
            """, (year,))
            
            for row in cursor.fetchall():
                date_str = row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0])
                free_days_dict[date_str] = {
                    'description': row[1] or '',
                    'affects_vacation_entitlement': bool(row[2]) if row[2] is not None else True
                }
        
        return jsonify({
            'success': True,
            'year': year,
            'blocks': blocks_dict,
            'free_days': free_days_dict
        })
    
    except Exception as e:
        import traceback
        print(f"❌ ERROR in /blocks-and-free-days: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@vacation_api.route('/my-bookings', methods=['GET'])
@login_required
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
        
        year = request.args.get('year', datetime.now().year, type=int)
        status_filter = request.args.get('status', None)

        # TAG 136: PostgreSQL-kompatible Query
        query = f"""
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
            WHERE vb.employee_id = {sql_placeholder()}
              AND {sql_year('vb.booking_date')} = {sql_placeholder()}
        """

        params = [employee_id, str(year)]

        if status_filter:
            query += f" AND vb.status = {sql_placeholder()}"
            params.append(status_filter)

        query += " ORDER BY vb.booking_date DESC"
        query = convert_placeholders(query)

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
                # TAG 136: Konvertiere Date-Objekt zu String (PostgreSQL gibt date zurück)
                if hasattr(booking_date, 'isoformat'):
                    booking_date = booking_date.isoformat()
                elif isinstance(booking_date, str):
                    pass  # Bereits String
                else:
                    booking_date = str(booking_date)
                
                # Für Locosoft-Vergleich: String-Format verwenden
                booking_date_str = booking_date if isinstance(booking_date, str) else str(booking_date)
                in_locosoft = booking_date_str in locosoft_dates

                bookings.append({
                    'id': row[0],
                    'date': booking_date_str,
                    'day_part': row[2],
                    'status': row[3],
                    'type_id': row[4],
                    'type_name': row[5],
                    'comment': row[6],
                    'created_at': row[7] if not hasattr(row[7], 'isoformat') else row[7].isoformat() if row[7] else None,
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
@login_required
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
        
        year = request.args.get('year', datetime.now().year, type=int)
        status_filter = request.args.get('status', None)

        # TAG 136: PostgreSQL-kompatible Query
        query = f"""
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
            WHERE vb.employee_id = {sql_placeholder()}
              AND {sql_year('vb.booking_date')} = {sql_placeholder()}
        """

        params = [employee_id, str(year)]

        if status_filter:
            query += f" AND vb.status = {sql_placeholder()}"
            params.append(status_filter)

        query += " ORDER BY vb.booking_date DESC"
        query = convert_placeholders(query)

        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            requests_list = []
            for row in cursor.fetchall():
                booking_date = row[1]
                # TAG 136: Konvertiere Date-Objekt zu String (PostgreSQL gibt date zurück)
                if hasattr(booking_date, 'isoformat'):
                    booking_date = booking_date.isoformat()
                elif not isinstance(booking_date, str):
                    booking_date = str(booking_date)
                
                requests_list.append({
                    'id': row[0],
                    'date': booking_date,
                    'day_part': row[2],
                    'status': row[3],
                    'type_id': row[4],
                    'type_name': row[5],
                    'comment': row[6],
                    'created_at': row[7] if not hasattr(row[7], 'isoformat') else row[7].isoformat() if row[7] else None
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
@login_required
def book_vacation():
    """
    POST /api/vacation/book

    Bucht Urlaub für den angemeldeten User.
    TAG 127: Admins können mit for_employee_id für andere Mitarbeiter buchen.
    """
    try:
        # Aktueller User (für Audit)
        current_employee_id, ldap_username, current_employee_data = get_employee_from_session()

        if not current_employee_id:
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

        # TAG 127: Admin-Buchung für anderen Mitarbeiter
        for_employee_id = data.get('for_employee_id')
        booking_for_other = False

        if for_employee_id and for_employee_id != current_employee_id:
            # Prüfe Admin-Rechte
            if not is_vacation_admin(ldap_username):
                return jsonify({
                    'success': False,
                    'error': 'Keine Berechtigung, für andere Mitarbeiter zu buchen'
                }), 403

            # Lade Employee-Daten für Ziel-Mitarbeiter
            target_employee_data = get_employee_by_id(for_employee_id)
            if not target_employee_data:
                return jsonify({
                    'success': False,
                    'error': f'Mitarbeiter {for_employee_id} nicht gefunden'
                }), 404

            employee_id = for_employee_id
            employee_data = target_employee_data
            booking_for_other = True
        else:
            employee_id = current_employee_id
            employee_data = current_employee_data

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

            query = f"SELECT id FROM vacation_bookings WHERE employee_id = {sql_placeholder()} AND booking_date = {sql_placeholder()} AND status IN ('pending', 'approved')"
            query = convert_placeholders(query)
            cursor.execute(query, (employee_id, booking_date))

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
                booking_year, err = _validate_vacation_year(booking_year)
                if err:
                    return err
                try:
                    from api.vacation_year_utils import ensure_vacation_year_setup_simple
                    ensure_vacation_year_setup_simple(booking_year)
                except Exception as e:
                    print(f"⚠️ ensure_vacation_year_setup_simple({booking_year}): {e}")

                # Resturlaub wie in der Anzeige (View + Locosoft-Cap) – Usertest Sandra/Herbert
                available_days, resturlaub_info = _get_available_rest_days_for_validation(
                    cursor, employee_id, booking_year, (employee_data or {}).get('locosoft_id')
                )
                if requested_days > available_days or available_days < 0:
                    return jsonify({
                        'success': False,
                        'error': f'Nicht genug Resturlaub! Verfügbar: {available_days} Tage, angefragt: {requested_days} Tag(e)',
                        'resturlaub_info': resturlaub_info
                    }), 400

            # Vertretungsregel: Vertreter darf in dem Zeitraum keinen Urlaub buchen, in dem die vertretene Person abwesend ist
            if vacation_type_id == 1:
                conflict = _check_substitute_vacation_conflict(cursor, employee_id, [booking_date])
                if conflict:
                    blocked_dates, vertretene_name = conflict
                    return jsonify({
                        'success': False,
                        'error': f'Sie vertreten in diesem Zeitraum {vertretene_name}. Urlaubsbuchung an den Tagen {", ".join(blocked_dates)} ist nicht möglich.'
                    }), 400

            # Max. Abwesenheit pro Abteilung/Standort (Urlaub + Schulung; Default 50%, editierbar)
            cap = _check_max_absence_per_dept_location(cursor, employee_id, [booking_date], vacation_type_id)
            if cap:
                blocked_dates, max_pct, _a, _t = cap
                return jsonify({
                    'success': False,
                    'error': f'Max. Abwesenheit in Ihrer Abteilung/am Standort ({max_pct}%) wäre überschritten. Keine Buchung an: {", ".join(blocked_dates)}.',
                    'blocked_dates': blocked_dates
                }), 400

            # Berechtigung: Krankheit NUR Admin; Schulung Genehmiger oder Admin; ZA nur Admin (Test DRIVE / Testanleitung)
            # vacation_type_id: 5=Krankheit, 6=Zeitausgleich (ZA), 9=Schulung
            is_sickness = vacation_type_id == 5
            is_schulung = vacation_type_id == 9
            is_za = vacation_type_id == 6
            user_is_admin = is_vacation_admin(ldap_username)
            user_is_approver = is_approver(ldap_username) if ldap_username else False

            if is_sickness:
                if not user_is_admin:
                    return jsonify({
                        'success': False,
                        'error': 'Krankheitstage können nur von Admins eingetragen werden'
                    }), 403
            elif is_schulung:
                if not (user_is_admin or user_is_approver):
                    return jsonify({
                        'success': False,
                        'error': 'Schulung kann nur von Genehmiger oder Admin eingetragen werden'
                    }), 403
            elif is_za:
                if not user_is_admin:
                    return jsonify({
                        'success': False,
                        'error': 'Zeitausgleich kann nur von Admins eingetragen werden'
                    }), 403

            is_admin_only_type = is_sickness or is_za or is_schulung  # alle drei direkt approved

            # Status-Logik:
            # - Admin-Buchung für anderen: direkt 'approved' (wird manuell in Locosoft nachgepflegt)
            # - Krankheit/ZA: direkt 'approved'
            # - Normaler Urlaub: 'pending' (braucht Genehmigung)
            if booking_for_other or is_admin_only_type:
                initial_status = 'approved'
            else:
                initial_status = 'pending'

            # TAG 136: PostgreSQL-kompatible Query - verwende ? und convert_placeholders()
            query = """
                INSERT INTO vacation_bookings (
                    employee_id, booking_date, vacation_type_id,
                    day_part, status, comment, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            query = convert_placeholders(query)
            cursor.execute(query, (employee_id, booking_date, vacation_type_id, day_part, initial_status, comment,
                  current_employee_id, datetime.now().isoformat()))

            booking_id = cursor.lastrowid
            conn.commit()

            # Vacation type name für E-Mail holen
            query = f"SELECT name FROM vacation_types WHERE id = {sql_placeholder()}"
            query = convert_placeholders(query)
            cursor.execute(query, (vacation_type_id,))
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
        
        # TAG 127: Unterschiedliche E-Mails und Responses je nach Typ
        target_name = f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}".strip()

        if is_sickness:
            # Krankheit: E-Mail an HR + Teamleitung + GL
            sickness_email_sent = send_sickness_notification(booking_details_for_email, approvers)
            return jsonify({
                'success': True,
                'booking_id': booking_id,
                'message': f'Krankheitstag für {target_name} eingetragen' if booking_for_other else 'Krankheitstag eingetragen',
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

        if is_za or booking_for_other:
            # TAG 127: ZA oder Admin-Buchung für anderen: Direkt approved, E-Mail an HR
            type_name = 'Zeitausgleich' if is_za else vacation_type_name
            return jsonify({
                'success': True,
                'booking_id': booking_id,
                'message': f'{type_name} für {target_name} eingetragen (Status: approved)',
                'booking': {
                    'id': booking_id,
                    'date': booking_date,
                    'day_part': day_part,
                    'status': 'approved',
                    'vacation_type': type_name
                },
                'for_employee': target_name if booking_for_other else None
            }), 201

        # Normaler Urlaub: E-Mail an Genehmiger
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

            # Hole Booking-Details inkl. Kalender-Event-IDs für Storno
            cursor.execute("""
                SELECT
                    vb.employee_id,
                    vb.status,
                    vb.booking_date,
                    vb.day_part,
                    vt.name as vacation_type,
                    e.first_name || ' ' || e.last_name as employee_name,
                    e.department_name,
                    e.email as owner_email,
                    vb.calendar_event_id_employee,
                    vb.calendar_event_id_drive
                FROM vacation_bookings vb
                JOIN employees e ON vb.employee_id = e.id
                LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
                WHERE vb.id = %s
            """, (booking_id,))

            booking = cursor.fetchone()

            if not booking:
                return jsonify({'success': False, 'error': 'Buchung nicht gefunden'}), 404

            # TAG 113: Admins dürfen auch fremde Buchungen stornieren
            booking_owner_id = booking[0]
            is_own_booking = booking_owner_id == employee_id
            owner_email = booking[7]
            calendar_event_id_employee = booking[8] if len(booking) > 8 else None
            calendar_event_id_drive = booking[9] if len(booking) > 9 else None

            # Prüfe ob User Admin ist (GRP_Urlaub_Admin)
            is_admin = False
            cursor.execute("""
                SELECT ad_groups FROM users
                WHERE username LIKE %s OR username = %s
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
            # TAG 136: PostgreSQL-kompatible Query
            query = f"""
                UPDATE vacation_bookings
                SET status = 'cancelled',
                    comment = CASE WHEN comment IS NULL OR comment = '' THEN {sql_placeholder()} ELSE comment || ' | Storniert: ' || {sql_placeholder()} END
                WHERE id = {sql_placeholder()}
            """
            query = convert_placeholders(query)
            cursor.execute(query, (reason, reason, booking_id))

            conn.commit()

        booking_details = {
            'date': booking[2],
            'day_part': booking[3],
            'vacation_type': booking[4] or 'Urlaub',
            'employee_name': booking[5],
            'department': booking[6] or '',
            'employee_email': owner_email
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
        
        # Kalendereintrag löschen (drive@ + Mitarbeiter-Kalender)
        calendar_deleted = False
        if was_approved and CALENDAR_AVAILABLE:
            try:
                calendar_service = VacationCalendarService()
                calendar_deleted = calendar_service.delete_vacation_event(
                    booking_details,
                    calendar_event_id_employee=calendar_event_id_employee,
                    calendar_event_id_drive=calendar_event_id_drive
                )
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

        # TAG 127: Admin-Direktbuchung für anderen Mitarbeiter
        for_employee_id = data.get('for_employee_id')
        admin_direct_booking = data.get('admin_direct_booking', False)
        booking_for_other = False
        target_employee_data = employee_data

        if for_employee_id and for_employee_id != employee_id:
            # Prüfe ob Admin
            if not is_vacation_admin(ldap_username):
                return jsonify({'success': False, 'error': 'Keine Berechtigung für Buchung für andere'}), 403

            target_employee_data = get_employee_by_id(for_employee_id)
            if not target_employee_data:
                return jsonify({'success': False, 'error': f'Mitarbeiter {for_employee_id} nicht gefunden'}), 404

            employee_id = for_employee_id  # Für diese Buchung verwenden
            booking_for_other = True

        # Validierung
        for d in dates:
            try:
                datetime.strptime(d, '%Y-%m-%d')
            except ValueError:
                return jsonify({'success': False, 'error': f'Ungültiges Datum: {d}'}), 400

        with db_session() as conn:
            cursor = conn.cursor()

            # Krankheit (type_id 5) nur für Admins – Korrektur: war fälschlich type_id == 3 (Test DRIVE)
            is_sickness = vacation_type_id == 5
            if is_sickness:
                if not is_vacation_admin(ldap_username):
                    return jsonify({'success': False, 'error': 'Krankheitstage können nur von Admins eingetragen werden'}), 403

            # TAG 198: Prüfe Urlaubssperren
            if vacation_type_id == 1:  # Nur für Urlaub prüfen
                # Hole Abteilung des Mitarbeiters
                cursor.execute("""
                    SELECT department_name FROM employees WHERE id = %s
                """, (employee_id,))
                emp_dept = cursor.fetchone()
                if emp_dept and emp_dept[0]:
                    # Prüfe ob einer der Tage gesperrt ist
                    placeholders = ','.join(['%s'] * len(dates))
                    cursor.execute(f"""
                        SELECT block_date, reason FROM vacation_blocks
                        WHERE department_name = %s AND block_date IN ({placeholders})
                    """, [emp_dept[0]] + dates)
                    blocked_dates = cursor.fetchall()
                    if blocked_dates:
                        blocked_str = ', '.join([str(bd[0]) for bd in blocked_dates])
                        return jsonify({
                            'success': False,
                            'error': f'Urlaub an folgenden Tagen gesperrt: {blocked_str}',
                            'blocked_dates': [str(bd[0]) for bd in blocked_dates]
                        }), 400
            
            # TAG 198: Prüfe freie Tage (Betriebsferien)
            placeholders = ','.join(['%s'] * len(dates))
            cursor.execute(f"""
                SELECT free_date, description FROM free_days
                WHERE free_date IN ({placeholders})
            """, dates)
            free_dates = cursor.fetchall()
            if free_dates:
                free_str = ', '.join([str(fd[0]) for fd in free_dates])
                return jsonify({
                    'success': False,
                    'error': f'An folgenden Tagen sind Betriebsferien: {free_str}',
                    'free_dates': [str(fd[0]) for fd in free_dates]
                }), 400

            # Resturlaub-Validierung für Urlaub (type_id=1) – gleiche Logik wie Anzeige (Usertest Sandra/Herbert)
            if vacation_type_id == 1:
                requested_days = len(dates) * (1.0 if day_part == 'full' else 0.5)
                booking_year = int(dates[0][:4])
                try:
                    from api.vacation_year_utils import ensure_vacation_year_setup_simple
                    ensure_vacation_year_setup_simple(booking_year)
                except Exception as e:
                    print(f"⚠️ ensure_vacation_year_setup_simple({booking_year}): {e}")
                # target_employee_data = Person, für die gebucht wird (bei Admin-Buchung ≠ employee_data)
                available_days, _ = _get_available_rest_days_for_validation(
                    cursor, employee_id, booking_year, (target_employee_data or {}).get('locosoft_id')
                )
                if requested_days > available_days or available_days < 0:
                    return jsonify({
                        'success': False,
                        'error': f'Nicht genug Resturlaub! Verfügbar: {available_days} Tage, angefragt: {requested_days} Tag(e)'
                    }), 400

            # Prüfe ob bereits Buchungen existieren (nur pending/approved blockieren – rejected zählt nicht)
            existing = []
            for d in dates:
                query = f"SELECT id, status FROM vacation_bookings WHERE employee_id = {sql_placeholder()} AND booking_date = {sql_placeholder()} AND status IN ('pending', 'approved')"
                query = convert_placeholders(query)
                cursor.execute(query, (employee_id, d))
                row = cursor.fetchone()
                if row:
                    existing.append(d)

            if existing:
                return jsonify({
                    'success': False,
                    'error': f'Bereits gebucht an: {", ".join(existing)}',
                    'existing_dates': existing
                }), 400

            # Vertretungsregel: Vertreter darf in dem Zeitraum keinen Urlaub buchen, in dem die vertretene Person abwesend ist
            if vacation_type_id == 1:
                conflict = _check_substitute_vacation_conflict(cursor, employee_id, dates)
                if conflict:
                    blocked_dates, vertretene_name = conflict
                    return jsonify({
                        'success': False,
                        'error': f'Sie vertreten in diesem Zeitraum {vertretene_name}. Urlaubsbuchung an den Tagen {", ".join(blocked_dates)} ist nicht möglich.',
                        'blocked_dates': blocked_dates
                    }), 400

            # Max. Abwesenheit pro Abteilung/Standort (Urlaub + Schulung; Default 50%, editierbar)
            cap = _check_max_absence_per_dept_location(cursor, employee_id, dates, vacation_type_id)
            if cap:
                blocked_dates, max_pct, _a, _t = cap
                return jsonify({
                    'success': False,
                    'error': f'Max. Abwesenheit in Ihrer Abteilung/am Standort ({max_pct}%) wäre überschritten. Keine Buchung an: {", ".join(blocked_dates)}.',
                    'blocked_dates': blocked_dates
                }), 400

            # Alle Buchungen einfügen
            # TAG 127: Admin-Direktbuchungen sind sofort genehmigt
            initial_status = 'approved' if (is_sickness or admin_direct_booking) else 'pending'
            booking_ids = []
            # TAG 136: PostgreSQL-kompatible Query - verwende ? und convert_placeholders()
            # WICHTIG: Query als Single-Line String, dann convert_placeholders() aufrufen
            insert_query = "INSERT INTO vacation_bookings (employee_id, booking_date, vacation_type_id, day_part, status, comment, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
            insert_query = convert_placeholders(insert_query)
            # Debug: Prüfe ob Konvertierung funktioniert hat
            if '?' in insert_query:
                print(f"⚠️ WARNUNG: convert_placeholders() hat nicht funktioniert! Query enthält noch ?: {insert_query[:100]}")
                print(f"⚠️ DB_TYPE: {get_db_type()}")
            for d in dates:
                cursor.execute(insert_query, (employee_id, d, vacation_type_id, day_part, initial_status, comment, datetime.now().isoformat()))
                booking_ids.append(cursor.lastrowid)

            # Vacation Type Name holen
            query = f"SELECT name FROM vacation_types WHERE id = {sql_placeholder()}"
            query = convert_placeholders(query)
            cursor.execute(query, (vacation_type_id,))
            vt_row = cursor.fetchone()
            vacation_type_name = vt_row[0] if vt_row else 'Urlaub'

            conn.commit()

        # TAG 127: Bei Admin-Direktbuchung Info-Mail an HR statt Genehmigungsanfrage
        target_employee_name = f"{target_employee_data.get('first_name', '')} {target_employee_data.get('last_name', '')}".strip()
        department = target_employee_data.get('department', '') or target_employee_data.get('department_name', '')

        if admin_direct_booking and booking_for_other:
            # Info-Mail an HR für Locosoft-Eintrag
            email_sent = False
            if GRAPH_AVAILABLE:
                try:
                    graph = GraphMailConnector()

                    # Datums-Formatierung
                    dates_formatted = [datetime.strptime(d, '%Y-%m-%d').strftime('%d.%m.%Y') for d in dates]
                    date_display = dates_formatted[0] if len(dates) == 1 else f"{dates_formatted[0]} - {dates_formatted[-1]} ({len(dates)} Tage)"

                    # Admin-Name für E-Mail
                    admin_name = f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}".strip() if employee_data else ldap_username

                    type_icons = {'Urlaub': '🏖️', 'Zeitausgleich': '⏰', 'Ausgleichstag': '⏰', 'Krankheit': '🤒', 'Schulung': '📚'}
                    icon = type_icons.get(vacation_type_name, '📅')

                    subject = f"ℹ️ Abwesenheit eingetragen: {target_employee_name} - {vacation_type_name}"

                    body_html = f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px;">
                        <h2 style="color: #28a745;">{icon} Abwesenheit eingetragen (Portal)</h2>
                        <p style="background: #d4edda; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745;">
                            <strong>Hinweis:</strong> Diese Abwesenheit wurde direkt im Portal eingetragen und ist bereits genehmigt.
                            Bitte in Locosoft nachtragen.
                        </p>
                        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                            <tr style="background: #f8f9fa;"><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Mitarbeiter</td><td style="padding: 10px; border: 1px solid #dee2e6;">{target_employee_name}</td></tr>
                            <tr><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Abteilung</td><td style="padding: 10px; border: 1px solid #dee2e6;">{department}</td></tr>
                            <tr style="background: #f8f9fa;"><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Zeitraum</td><td style="padding: 10px; border: 1px solid #dee2e6;">{date_display}</td></tr>
                            <tr><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Art</td><td style="padding: 10px; border: 1px solid #dee2e6;">{vacation_type_name}</td></tr>
                            <tr style="background: #f8f9fa;"><td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Eingetragen von</td><td style="padding: 10px; border: 1px solid #dee2e6;">{admin_name}</td></tr>
                        </table>
                        <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
                        <p style="color: #6c757d; font-size: 12px;">Diese E-Mail wurde automatisch vom Greiner DRIVE Portal gesendet.</p>
                    </div>
                    """

                    email_sent = graph.send_mail(sender_email=DRIVE_EMAIL, to_emails=[HR_EMAIL], subject=subject, body_html=body_html)
                    if email_sent:
                        print(f"✅ HR-Info-Mail gesendet für {target_employee_name}: {vacation_type_name}")
                except Exception as e:
                    print(f"❌ HR-Info-Mail Fehler: {e}")

            return jsonify({
                'success': True,
                'booking_ids': booking_ids,
                'message': f'{len(dates)} Tag(e) für {target_employee_name} eingetragen (genehmigt)',
                'email_sent': email_sent
            }), 201

        # EINE E-Mail für alle Tage (E-Mail-Batching) - normaler Antrag
        approvers = get_approvers_for_employee(employee_id)
        employee_name = target_employee_name
        
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
            query = f"SELECT ad_groups FROM users WHERE username LIKE {sql_placeholder()} OR username = {sql_placeholder()}"
            query = convert_placeholders(query)
            cursor.execute(query, (f"%{ldap_username}%", ldap_username))
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
                    WHERE vb.id = %s
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

                # TAG 136: PostgreSQL-kompatible Query
                query = f"""
                    UPDATE vacation_bookings SET status = 'cancelled',
                    comment = CASE WHEN comment IS NULL OR comment = '' THEN {sql_placeholder()} ELSE comment || ' | Storniert: ' || {sql_placeholder()} END
                    WHERE id = {sql_placeholder()}
                """
                query = convert_placeholders(query)
                cursor.execute(query, (reason, reason, bid))

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
            query = f"SELECT locosoft_id FROM employees WHERE id = {sql_placeholder()}"
            query = convert_placeholders(query)
            cursor.execute(query, (employee_id,))
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
@admin_required
def debug_session():
    """Debug-Endpoint: Zeigt Session-Daten (nur für Admins)."""
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
                    WHERE lem.ldap_username = %s AND lgm.portal_feature = 'urlaub_admin'
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
                      AND var.approver_username = %s
                """, (ldap_username,))
            else:
                # Eigene offene Anträge
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM vacation_bookings vb
                    WHERE vb.status = 'pending' AND vb.employee_id = %s
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
