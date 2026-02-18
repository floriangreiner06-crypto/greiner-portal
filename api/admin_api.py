"""
Admin API - Health & Logs & Rechteverwaltung & Reports
=======================================================
TAG 120: Obsolete Job-Endpoints entfernt (jetzt via Celery)
TAG 134: Rechteverwaltung hinzugefügt
TAG 135: Report-Subscriptions System

Celery Task Management: /admin/celery/
Flower Dashboard: :5555
"""
from flask import Blueprint, jsonify, request
from flask_login import current_user
from datetime import datetime
from decorators.auth_decorators import admin_required
import os
import json

from api.db_utils import db_session, row_to_dict, rows_to_list
from api.db_connection import convert_placeholders, sql_placeholder, get_db_type

admin_api = Blueprint('admin_api', __name__)


@admin_api.route('/api/admin/logs', methods=['GET'])
@admin_required
def list_logs():
    """Liste alle verfügbaren Log-Dateien"""
    log_dir = '/opt/greiner-portal/logs'
    try:
        logs = []
        if os.path.exists(log_dir):
            for f in os.listdir(log_dir):
                if f.endswith('.log'):
                    path = os.path.join(log_dir, f)
                    stat = os.stat(path)
                    logs.append({
                        'name': f,
                        'size_kb': round(stat.st_size / 1024, 1),
                        'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            logs.sort(key=lambda x: x['last_modified'], reverse=True)
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/health', methods=['GET'])
def admin_health():
    """Health-Check Endpoint"""
    return jsonify({
        'status': 'ok',
        'scheduler': 'celery',
        'version': '3.0-tag134',
        'timestamp': datetime.now().isoformat()
    })


# =============================================================================
# RECHTEVERWALTUNG - TAG 134
# =============================================================================

@admin_api.route('/api/admin/users-roles', methods=['GET'])
@admin_required
def get_users_roles():
    """Alle User mit ihren Rollen laden
    TAG 136: PostgreSQL-kompatibel (STRING_AGG statt GROUP_CONCAT)
    """
    try:
        # GROUP_CONCAT (SQLite) vs STRING_AGG (PostgreSQL)
        if get_db_type() == 'postgresql':
            concat_func = "STRING_AGG(r.name, ', ')"
        else:
            concat_func = "GROUP_CONCAT(r.name, ', ')"

        with db_session() as conn:
            cursor = conn.cursor()

            # Dashboard-Konfigurationen zuerst laden
            cursor.execute('''
                SELECT 
                    udc.user_id,
                    udc.target_url,
                    ad.name as dashboard_name
                FROM user_dashboard_config udc
                LEFT JOIN available_dashboards ad ON udc.target_url = ad.url
            ''')
            
            dashboard_configs = {}
            for row in cursor.fetchall():
                row_dict = row_to_dict(row)
                dashboard_configs[row_dict['user_id']] = {
                    'url': row_dict['target_url'],
                    'name': row_dict['dashboard_name']
                }

            # User mit Rollen laden
            cursor.execute(f'''
                SELECT
                    u.id,
                    u.username,
                    u.display_name,
                    u.ou,
                    u.title,
                    u.last_login,
                    {concat_func} as roles
                FROM users u
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                GROUP BY u.id, u.username, u.display_name, u.ou, u.title, u.last_login
                ORDER BY u.display_name
            ''')

            users = []
            for row in cursor.fetchall():
                row_dict = row_to_dict(row)
                user_id = row_dict['id']
                dashboard_config = dashboard_configs.get(user_id, {})
                
                users.append({
                    'id': user_id,
                    'username': row_dict['username'],
                    'display_name': row_dict['display_name'],
                    'ou': row_dict['ou'],
                    'title': row_dict['title'],
                    'last_login': row_dict['last_login'],
                    'roles': row_dict['roles'] or 'keine',
                    'dashboard_url': dashboard_config.get('url'),
                    'dashboard_name': dashboard_config.get('name')
                })

            # Verfügbare Rollen
            cursor.execute('SELECT id, name, description FROM roles ORDER BY name')
            roles = rows_to_list(cursor.fetchall())

        return jsonify({
            'users': users,
            'available_roles': roles
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/user/<int:user_id>/role', methods=['POST'])
@admin_required
def assign_role(user_id):
    """Rolle einem User zuweisen
    TAG 136: PostgreSQL-kompatibel
    """
    try:
        data = request.get_json()
        role_name = data.get('role')

        if not role_name:
            return jsonify({'error': 'Rolle erforderlich'}), 400

        ph = sql_placeholder()

        with db_session() as conn:
            cursor = conn.cursor()

            # Role-ID holen
            cursor.execute(f'SELECT id FROM roles WHERE name = {ph}', (role_name,))
            role_row = cursor.fetchone()

            if not role_row:
                return jsonify({'error': f'Rolle "{role_name}" nicht gefunden'}), 404

            role_dict = row_to_dict(role_row)
            role_id = role_dict['id']

            # Prüfen ob bereits zugewiesen
            cursor.execute(f'''
                SELECT 1 FROM user_roles WHERE user_id = {ph} AND role_id = {ph}
            ''', (user_id, role_id))

            if cursor.fetchone():
                return jsonify({'message': 'Rolle bereits zugewiesen'}), 200

            # Rolle zuweisen
            cursor.execute(f'''
                INSERT INTO user_roles (user_id, role_id, assigned_at)
                VALUES ({ph}, {ph}, {ph})
            ''', (user_id, role_id, datetime.now().isoformat()))

            conn.commit()

        return jsonify({'message': f'Rolle "{role_name}" zugewiesen', 'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/user/<int:user_id>/role', methods=['DELETE'])
@admin_required
def remove_role(user_id):
    """Rolle von User entfernen
    TAG 136: PostgreSQL-kompatibel
    """
    try:
        data = request.get_json()
        role_name = data.get('role')

        if not role_name:
            return jsonify({'error': 'Rolle erforderlich'}), 400

        ph = sql_placeholder()

        with db_session() as conn:
            cursor = conn.cursor()

            # Role-ID holen
            cursor.execute(f'SELECT id FROM roles WHERE name = {ph}', (role_name,))
            role_row = cursor.fetchone()

            if not role_row:
                return jsonify({'error': f'Rolle "{role_name}" nicht gefunden'}), 404

            role_dict = row_to_dict(role_row)
            role_id = role_dict['id']

            # Rolle entfernen
            cursor.execute(f'''
                DELETE FROM user_roles WHERE user_id = {ph} AND role_id = {ph}
            ''', (user_id, role_id))

            conn.commit()

        return jsonify({'message': f'Rolle "{role_name}" entfernt', 'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/feature-access', methods=['GET'])
@admin_required
def get_feature_access():
    """Feature-Zugriffs-Matrix laden (DB + Config-Fallback)
    TAG 190: Erweitert um DB-basierte Verwaltung
    """
    try:
        from config.roles_config import get_feature_access_from_db, TITLE_TO_ROLE
        
        # DB-basierte Feature-Zugriffe laden (mit Fallback auf Config)
        feature_access = get_feature_access_from_db()

        return jsonify({
            'feature_access': feature_access,
            'title_to_role': TITLE_TO_ROLE
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/feature-access/<feature>/role/<role>', methods=['POST'])
@admin_required
def add_feature_access(feature, role):
    """Rolle zu Feature hinzufügen
    TAG 190: Speichert in DB
    """
    try:
        # Prüfe ob User Admin-Rechte hat
        if not (current_user.can_access_feature('admin') if hasattr(current_user, 'can_access_feature') else False):
            return jsonify({'error': 'Keine Berechtigung'}), 403
        
        ph = sql_placeholder()
        created_by = current_user.username if hasattr(current_user, 'username') else 'admin'
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Prüfe ob bereits vorhanden
            cursor.execute(f'''
                SELECT 1 FROM feature_access 
                WHERE feature_name = {ph} AND role_name = {ph}
            ''', (feature, role))
            
            if cursor.fetchone():
                return jsonify({'message': 'Zugriff bereits vorhanden', 'success': True}), 200
            
            # Hinzufügen
            cursor.execute(f'''
                INSERT INTO feature_access (feature_name, role_name, created_by, created_at)
                VALUES ({ph}, {ph}, {ph}, {ph})
            ''', (feature, role, created_by, datetime.now().isoformat()))
            
            conn.commit()
        
        return jsonify({
            'message': f'Rolle "{role}" zu Feature "{feature}" hinzugefügt',
            'success': True
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/feature-access/<feature>/role/<role>', methods=['DELETE'])
@admin_required
def remove_feature_access(feature, role):
    """Rolle von Feature entfernen
    TAG 190: Entfernt aus DB
    """
    try:
        # Prüfe ob User Admin-Rechte hat
        if not (current_user.can_access_feature('admin') if hasattr(current_user, 'can_access_feature') else False):
            return jsonify({'error': 'Keine Berechtigung'}), 403
        
        ph = sql_placeholder()
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Entfernen
            cursor.execute(f'''
                DELETE FROM feature_access 
                WHERE feature_name = {ph} AND role_name = {ph}
            ''', (feature, role))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Zugriff nicht gefunden'}), 404
            
            conn.commit()
        
        return jsonify({
            'message': f'Rolle "{role}" von Feature "{feature}" entfernt',
            'success': True
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/feature-access/<feature>', methods=['POST'])
@admin_required
def update_feature_access(feature):
    """Feature-Zugriff komplett aktualisieren (alle Rollen)
    TAG 190: Ersetzt alle Rollen für ein Feature
    """
    try:
        # Prüfe ob User Admin-Rechte hat
        if not (current_user.can_access_feature('admin') if hasattr(current_user, 'can_access_feature') else False):
            return jsonify({'error': 'Keine Berechtigung'}), 403
        
        data = request.get_json()
        roles = data.get('roles', [])
        
        if not isinstance(roles, list):
            return jsonify({'error': 'roles muss eine Liste sein'}), 400
        
        ph = sql_placeholder()
        created_by = current_user.username if hasattr(current_user, 'username') else 'admin'
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Alte Rollen entfernen
            cursor.execute(f'''
                DELETE FROM feature_access WHERE feature_name = {ph}
            ''', (feature,))
            
            # Neue Rollen hinzufügen
            for role in roles:
                if role:  # Ignoriere leere Strings
                    cursor.execute(f'''
                        INSERT INTO feature_access (feature_name, role_name, created_by, created_at)
                        VALUES ({ph}, {ph}, {ph}, {ph})
                        ON CONFLICT (feature_name, role_name) DO NOTHING
                    ''', (feature, role, created_by, datetime.now().isoformat()))
            
            conn.commit()
        
        return jsonify({
            'message': f'Feature "{feature}" aktualisiert',
            'success': True
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# REPORT SUBSCRIPTIONS - TAG 135
# =============================================================================

@admin_api.route('/api/admin/reports', methods=['GET'])
@admin_required
def get_reports():
    """Alle verfügbaren Reports mit Subscriber-Infos"""
    try:
        from reports.registry import get_all_subscriptions_with_counts

        reports = get_all_subscriptions_with_counts()

        # Nach Kategorie gruppieren
        by_category = {}
        for report_id, report in reports.items():
            cat = report.get('category', 'sonstige')
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(report)

        return jsonify({
            'reports': reports,
            'by_category': by_category,
            'categories': list(by_category.keys())
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/reports/<report_id>', methods=['GET'])
@admin_required
def get_report_detail(report_id):
    """Details zu einem Report inkl. Subscribers"""
    try:
        from reports.registry import get_report, get_subscribers

        report = get_report(report_id)
        if not report:
            return jsonify({'error': f'Report "{report_id}" nicht gefunden'}), 404

        subscribers = get_subscribers(report_id, active_only=False)

        return jsonify({
            'id': report_id,
            **report,
            'subscribers': subscribers,
            'active_count': sum(1 for s in subscribers if s['active'])
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/reports/<report_id>/subscribe', methods=['POST'])
@admin_required
def subscribe_to_report(report_id):
    """Neuen Subscriber hinzufügen"""
    try:
        from reports.registry import add_subscriber, report_exists

        if not report_exists(report_id):
            return jsonify({'error': f'Report "{report_id}" nicht gefunden'}), 404

        data = request.get_json()
        email = data.get('email', '').lower().strip()
        standort = data.get('standort')  # None = alle
        bereiche = data.get('bereiche')  # Liste oder None

        if not email:
            return jsonify({'error': 'E-Mail erforderlich'}), 400

        if '@' not in email:
            return jsonify({'error': 'Ungültige E-Mail-Adresse'}), 400

        # Standort validieren
        if standort == '' or standort == 'alle':
            standort = None

        # Bereiche validieren
        if bereiche and not isinstance(bereiche, list):
            return jsonify({'error': 'Bereiche muss eine Liste sein'}), 400

        created_by = current_user.username if hasattr(current_user, 'username') else 'admin'

        success = add_subscriber(
            report_type=report_id,
            email=email,
            standort=standort,
            bereiche=bereiche,
            created_by=created_by
        )

        if success:
            return jsonify({
                'message': f'{email} zu {report_id} hinzugefügt',
                'success': True
            })
        else:
            return jsonify({
                'message': f'{email} bereits abonniert (reaktiviert)',
                'success': True
            })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/reports/<report_id>/unsubscribe', methods=['POST'])
@admin_required
def unsubscribe_from_report(report_id):
    """Subscriber entfernen (deaktivieren)"""
    try:
        from reports.registry import remove_subscriber

        data = request.get_json()
        email = data.get('email', '').lower().strip()
        standort = data.get('standort')

        if not email:
            return jsonify({'error': 'E-Mail erforderlich'}), 400

        if standort == '' or standort == 'alle':
            standort = None

        success = remove_subscriber(report_id, email, standort)

        if success:
            return jsonify({
                'message': f'{email} von {report_id} entfernt',
                'success': True
            })
        else:
            return jsonify({
                'error': 'Subscription nicht gefunden',
                'success': False
            }), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/reports/subscription/<int:subscription_id>', methods=['DELETE'])
@admin_required
def delete_subscription(subscription_id):
    """Subscription komplett löschen"""
    try:
        from reports.registry import delete_subscriber

        success = delete_subscriber(subscription_id)

        if success:
            return jsonify({'message': 'Gelöscht', 'success': True})
        else:
            return jsonify({'error': 'Nicht gefunden'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/reports/subscription/<int:subscription_id>/toggle', methods=['POST'])
@admin_required
def toggle_subscription(subscription_id):
    """Subscription aktivieren/deaktivieren"""
    try:
        from reports.registry import toggle_subscriber

        success = toggle_subscriber(subscription_id)

        if success:
            return jsonify({'message': 'Status geändert', 'success': True})
        else:
            return jsonify({'error': 'Nicht gefunden'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/reports/migrate', methods=['POST'])
@admin_required
def migrate_subscriptions():
    """Einmalige Migration der hardcoded Empfänger in die DB"""
    try:
        from reports.registry import migrate_existing_subscribers

        migrate_existing_subscribers()

        return jsonify({
            'message': 'Migration abgeschlossen',
            'success': True
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/reports/<report_id>/send-test', methods=['POST'])
@admin_required
def send_report_test_email(report_id):
    """
    Testversand: Report einmalig an eine angegebene E-Mail-Adresse senden.
    Für Admin → E-Mail Reports → Verwalten → Testversand.
    """
    try:
        from reports.registry import report_exists
        from reports.send_test import send_report_test

        if not report_exists(report_id):
            return jsonify({'success': False, 'error': f'Report "{report_id}" nicht gefunden'}), 404

        data = request.get_json() or {}
        email = (data.get('email') or '').strip().lower()
        standort = data.get('standort')  # None, '', 'DEG', 'LAN'

        if not email or '@' not in email:
            return jsonify({'success': False, 'error': 'Gültige E-Mail-Adresse erforderlich'}), 400

        if standort == '':
            standort = None

        success, message = send_report_test(report_id, email, standort)

        if success:
            return jsonify({'success': True, 'message': message})
        return jsonify({'success': False, 'error': message}), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


def _normalize_report_email(username_or_email):
    """Verhindert doppelte Domain (z.B. user@auto-greiner.de@auto-greiner.de)."""
    s = (username_or_email or '').strip().lower()
    while '@auto-greiner.de@auto-greiner.de' in s:
        s = s.replace('@auto-greiner.de@auto-greiner.de', '@auto-greiner.de')
    if s and '@' not in s:
        s = s + '@auto-greiner.de'
    return s if s else None


@admin_api.route('/api/admin/reports/employees', methods=['GET'])
@admin_required
def get_employees_for_reports():
    """Mitarbeiter-Liste für Autocomplete beim Hinzufügen
    TAG 136: PostgreSQL-kompatibel
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()

            # E-Mail: username kann "user", "user@auto-greiner.de" oder fehlerhaft doppelt sein
            cursor.execute('''
                SELECT DISTINCT
                    LOWER(CASE
                        WHEN username LIKE '%@%' THEN TRIM(username)
                        ELSE TRIM(username) || '@auto-greiner.de'
                    END) AS email,
                    display_name AS name
                FROM users
                WHERE username IS NOT NULL AND TRIM(username) != ''
                ORDER BY display_name
            ''')

            rows = rows_to_list(cursor.fetchall(), cursor)
            employees = []
            for r in rows:
                email = _normalize_report_email(r.get('email') or r.get('Email'))
                if email:
                    employees.append({'email': email, 'name': r.get('name') or r.get('Name') or email})

        return jsonify({'employees': employees})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# USER DASHBOARD CONFIGURATION - TAG 190
# =============================================================================

@admin_api.route('/api/admin/dashboards', methods=['GET'])
@admin_required
def get_available_dashboards():
    """Verfügbare Dashboards laden
    TAG 190: Für Admin-Seite - gibt alle Dashboards zurück (Filterung erfolgt im Frontend)
    """
    try:
        ph = sql_placeholder()
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Alle aktiven Dashboards laden
            cursor.execute(f'''
                SELECT 
                    dashboard_key,
                    name,
                    description,
                    url,
                    icon,
                    category,
                    requires_feature,
                    role_restriction,
                    display_order
                FROM available_dashboards
                WHERE active = true
                ORDER BY display_order, name
            ''')
            
            all_dashboards = rows_to_list(cursor.fetchall())
        
        # Für Admin-Seite: Alle Dashboards zurückgeben
        # Filterung nach User-Rollen erfolgt im Frontend
        return jsonify({'dashboards': all_dashboards})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/user/<int:user_id>/dashboard', methods=['GET'])
@admin_required
def get_user_dashboard_config(user_id):
    """User-Dashboard-Konfiguration laden
    TAG 190: Nur für eigenen User oder Admin
    """
    try:
        # Prüfe Berechtigung: Nur eigener User oder Admin
        if user_id != current_user.id:
            # Prüfe Admin-Zugriff: portal_role, can_access_feature oder DB-Rolle
            is_admin = False
            if hasattr(current_user, 'portal_role') and current_user.portal_role == 'admin':
                is_admin = True
            elif hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('admin'):
                is_admin = True
            else:
                # Prüfe DB-Rolle direkt
                ph = sql_placeholder()
                with db_session() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'''
                        SELECT 1 FROM user_roles ur
                        JOIN roles r ON ur.role_id = r.id
                        WHERE ur.user_id = {ph} AND r.name = 'admin'
                    ''', (current_user.id,))
                    if cursor.fetchone():
                        is_admin = True
            
            if not is_admin:
                return jsonify({'error': 'Keine Berechtigung'}), 403
        
        ph = sql_placeholder()
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                SELECT 
                    id,
                    user_id,
                    dashboard_type,
                    target_url,
                    widget_config,
                    layout_config,
                    created_at,
                    updated_at
                FROM user_dashboard_config
                WHERE user_id = {ph}
            ''', (user_id,))
            
            row = cursor.fetchone()
            
            if row:
                config = row_to_dict(row)
                return jsonify({'config': config})
            else:
                return jsonify({'config': None})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/user/<int:user_id>/dashboard', methods=['POST'])
@admin_required
def set_user_dashboard_config(user_id):
    """User-Dashboard-Konfiguration speichern
    TAG 190: Nur für eigenen User oder Admin
    """
    try:
        # Prüfe Berechtigung: Nur eigener User oder Admin
        if user_id != current_user.id:
            # Prüfe Admin-Zugriff: portal_role, can_access_feature oder DB-Rolle
            is_admin = False
            if hasattr(current_user, 'portal_role') and current_user.portal_role == 'admin':
                is_admin = True
            elif hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('admin'):
                is_admin = True
            else:
                # Prüfe DB-Rolle direkt
                ph = sql_placeholder()
                with db_session() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'''
                        SELECT 1 FROM user_roles ur
                        JOIN roles r ON ur.role_id = r.id
                        WHERE ur.user_id = {ph} AND r.name = 'admin'
                    ''', (current_user.id,))
                    if cursor.fetchone():
                        is_admin = True
            
            if not is_admin:
                return jsonify({'error': 'Keine Berechtigung'}), 403
        
        data = request.get_json()
        dashboard_type = data.get('dashboard_type', 'redirect')
        target_url = data.get('target_url')
        
        if not target_url:
            return jsonify({'error': 'target_url erforderlich'}), 400
        
        ph = sql_placeholder()
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Prüfe ob Konfiguration existiert
            cursor.execute(f'''
                SELECT id FROM user_dashboard_config WHERE user_id = {ph}
            ''', (user_id,))
            
            existing = cursor.fetchone()
            
            widget_config = json.dumps(data.get('widget_config', {}))
            layout_config = json.dumps(data.get('layout_config', {}))
            
            if existing:
                # Update
                cursor.execute(f'''
                    UPDATE user_dashboard_config
                    SET dashboard_type = {ph},
                        target_url = {ph},
                        widget_config = {ph}::jsonb,
                        layout_config = {ph}::jsonb,
                        updated_at = {ph}
                    WHERE user_id = {ph}
                ''', (dashboard_type, target_url, widget_config, layout_config, 
                      datetime.now().isoformat(), user_id))
            else:
                # Insert
                cursor.execute(f'''
                    INSERT INTO user_dashboard_config 
                        (user_id, dashboard_type, target_url, widget_config, layout_config, created_at, updated_at)
                    VALUES ({ph}, {ph}, {ph}, {ph}::jsonb, {ph}::jsonb, {ph}, {ph})
                ''', (user_id, dashboard_type, target_url, widget_config, layout_config,
                      datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
        
        return jsonify({
            'message': 'Dashboard-Konfiguration gespeichert',
            'success': True
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# NAVIGATION MANAGEMENT - TAG 190
# =============================================================================

@admin_api.route('/api/admin/navigation', methods=['GET'])
def get_navigation_items():
    """Navigation-Items für aktuellen User laden
    TAG 190: Gefiltert nach Feature-Zugriff und Rollen
    """
    try:
        ph = sql_placeholder()
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Alle aktiven Items laden
            cursor.execute(f'''
                SELECT 
                    id,
                    parent_id,
                    label,
                    url,
                    icon,
                    order_index,
                    requires_feature,
                    role_restriction,
                    is_dropdown,
                    is_header,
                    is_divider,
                    active,
                    category
                FROM navigation_items
                WHERE active = true
                ORDER BY order_index, label
            ''')
            
            all_items = rows_to_list(cursor.fetchall())
        
        # Filter: Nur Items auf die User Zugriff hat
        filtered_items = []
        user_role = getattr(current_user, 'portal_role', 'mitarbeiter') if hasattr(current_user, 'portal_role') else 'mitarbeiter'
        
        for item in all_items:
            # Prüfe Feature-Zugriff
            if item.get('requires_feature'):
                if not (hasattr(current_user, 'can_access_feature') and 
                        current_user.can_access_feature(item['requires_feature'])):
                    continue
            
            # Prüfe Rollen-Restriktion (einzelne Rolle oder kommasep. Liste)
            if item.get('role_restriction'):
                allowed_roles = [r.strip() for r in str(item['role_restriction']).split(',') if r.strip()]
                if user_role not in allowed_roles:
                    if not (hasattr(current_user, 'can_access_feature') and 
                            current_user.can_access_feature('admin')):
                        continue
            
            filtered_items.append(item)
        
        # Struktur als Baum aufbauen
        items_by_id = {item['id']: item for item in filtered_items}
        root_items = []
        
        for item in filtered_items:
            if item['parent_id']:
                parent = items_by_id.get(item['parent_id'])
                if parent:
                    if 'children' not in parent:
                        parent['children'] = []
                    parent['children'].append(item)
            else:
                root_items.append(item)
        
        return jsonify({'items': root_items})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/navigation/all', methods=['GET'])
@admin_required
def get_all_navigation_items():
    """Alle Navigation-Items laden (für Admin-UI)
    TAG 190: Nur für Admins
    """
    try:
        # Prüfe Admin-Zugriff
        is_admin = False
        if hasattr(current_user, 'portal_role') and current_user.portal_role == 'admin':
            is_admin = True
        elif hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('admin'):
            is_admin = True
        
        if not is_admin:
            return jsonify({'error': 'Keine Berechtigung'}), 403
        
        ph = sql_placeholder()
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                SELECT 
                    id,
                    parent_id,
                    label,
                    url,
                    icon,
                    order_index,
                    requires_feature,
                    role_restriction,
                    is_dropdown,
                    is_header,
                    is_divider,
                    active,
                    category
                FROM navigation_items
                ORDER BY order_index, label
            ''')
            
            items = rows_to_list(cursor.fetchall())
        
        return jsonify({'items': items})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/navigation/<int:item_id>', methods=['POST'])
@admin_required
def update_navigation_item(item_id):
    """Navigation-Item aktualisieren
    TAG 190: Nur für Admins
    """
    try:
        # Prüfe Admin-Zugriff
        is_admin = False
        if hasattr(current_user, 'portal_role') and current_user.portal_role == 'admin':
            is_admin = True
        elif hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('admin'):
            is_admin = True
        
        if not is_admin:
            return jsonify({'error': 'Keine Berechtigung'}), 403
        
        data = request.get_json()
        
        ph = sql_placeholder()
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                UPDATE navigation_items
                SET label = {ph},
                    url = {ph},
                    icon = {ph},
                    order_index = {ph},
                    requires_feature = {ph},
                    role_restriction = {ph},
                    is_dropdown = {ph},
                    is_header = {ph},
                    is_divider = {ph},
                    active = {ph},
                    category = {ph},
                    updated_at = {ph}
                WHERE id = {ph}
            ''', (
                data.get('label'),
                data.get('url'),
                data.get('icon'),
                data.get('order_index', 0),
                data.get('requires_feature'),
                data.get('role_restriction'),
                data.get('is_dropdown', False),
                data.get('is_header', False),
                data.get('is_divider', False),
                data.get('active', True),
                data.get('category', 'main'),
                datetime.now().isoformat(),
                item_id
            ))
            
            conn.commit()
        
        return jsonify({'message': 'Navigation-Item aktualisiert', 'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/navigation', methods=['POST'])
@admin_required
def create_navigation_item():
    """Neues Navigation-Item erstellen
    TAG 190: Nur für Admins
    """
    try:
        # Prüfe Admin-Zugriff
        is_admin = False
        if hasattr(current_user, 'portal_role') and current_user.portal_role == 'admin':
            is_admin = True
        elif hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('admin'):
            is_admin = True
        
        if not is_admin:
            return jsonify({'error': 'Keine Berechtigung'}), 403
        
        data = request.get_json()
        
        ph = sql_placeholder()
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                INSERT INTO navigation_items 
                    (parent_id, label, url, icon, order_index, requires_feature, role_restriction,
                     is_dropdown, is_header, is_divider, active, category, created_at, updated_at)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                RETURNING id
            ''', (
                data.get('parent_id'),
                data.get('label'),
                data.get('url'),
                data.get('icon'),
                data.get('order_index', 0),
                data.get('requires_feature'),
                data.get('role_restriction'),
                data.get('is_dropdown', False),
                data.get('is_header', False),
                data.get('is_divider', False),
                data.get('active', True),
                data.get('category', 'main'),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            new_id = cursor.fetchone()[0]
            conn.commit()
        
        return jsonify({'message': 'Navigation-Item erstellt', 'id': new_id, 'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/navigation/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_navigation_item(item_id):
    """Navigation-Item löschen
    TAG 190: Nur für Admins
    """
    try:
        # Prüfe Admin-Zugriff
        is_admin = False
        if hasattr(current_user, 'portal_role') and current_user.portal_role == 'admin':
            is_admin = True
        elif hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('admin'):
            is_admin = True
        
        if not is_admin:
            return jsonify({'error': 'Keine Berechtigung'}), 403
        
        ph = sql_placeholder()
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                DELETE FROM navigation_items WHERE id = {ph}
            ''', (item_id,))
            
            conn.commit()
        
        return jsonify({'message': 'Navigation-Item gelöscht', 'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/user/<int:user_id>/dashboard', methods=['DELETE'])
@admin_required
def reset_user_dashboard_config(user_id):
    """User-Dashboard-Konfiguration zurücksetzen
    TAG 190: Zurück zu rollenbasierter Weiterleitung
    """
    try:
        # Prüfe Berechtigung: Nur eigener User oder Admin
        if user_id != current_user.id:
            # Prüfe Admin-Zugriff: portal_role, can_access_feature oder DB-Rolle
            is_admin = False
            if hasattr(current_user, 'portal_role') and current_user.portal_role == 'admin':
                is_admin = True
            elif hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('admin'):
                is_admin = True
            else:
                # Prüfe DB-Rolle direkt
                ph = sql_placeholder()
                with db_session() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'''
                        SELECT 1 FROM user_roles ur
                        JOIN roles r ON ur.role_id = r.id
                        WHERE ur.user_id = {ph} AND r.name = 'admin'
                    ''', (current_user.id,))
                    if cursor.fetchone():
                        is_admin = True
            
            if not is_admin:
                return jsonify({'error': 'Keine Berechtigung'}), 403
        
        ph = sql_placeholder()
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                DELETE FROM user_dashboard_config WHERE user_id = {ph}
            ''', (user_id,))
            
            conn.commit()
        
        return jsonify({
            'message': 'Dashboard-Konfiguration zurückgesetzt',
            'success': True
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# SERVICEBOX ZUGANG (Teile-Lager / Werkstatt) – Passwort & Ablauf-Erinnerung
# =============================================================================

CREDENTIALS_PATH = '/opt/greiner-portal/config/credentials.json'
SERVICEBOX_KEY = ('external_systems', 'stellantis_servicebox')


def _load_credentials():
    """Lädt credentials.json. Wirft bei Fehler."""
    if not os.path.exists(CREDENTIALS_PATH):
        raise FileNotFoundError('credentials.json nicht gefunden')
    with open(CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_credentials(creds):
    """Speichert credentials.json atomar (temp + rename)."""
    tmp = CREDENTIALS_PATH + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(creds, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CREDENTIALS_PATH)


@admin_api.route('/api/admin/servicebox-config', methods=['GET'])
@admin_required
def get_servicebox_config():
    """
    Liest ServiceBox-Zugangsdaten (ohne Passwort).
    Für Admin-UI: Anzeige Username, Ablaufdatum, Erinnerungs-E-Mails.
    """
    try:
        creds = _load_credentials()
        ext = creds.get('external_systems', {})
        sb = ext.get('stellantis_servicebox', {})
        return jsonify({
            'username': sb.get('username') or '',
            'portal_url': sb.get('portal_url') or 'https://servicebox.mpsa.com',
            'password_expires_at': sb.get('password_expires_at') or None,
            'reminder_emails': sb.get('reminder_emails') or [],
            'configured': bool(sb.get('username')),
        })
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/servicebox-config', methods=['POST'])
@admin_required
def update_servicebox_config():
    """
    Aktualisiert ServiceBox-Passwort und/oder Ablaufdatum und Erinnerungs-E-Mails.
    Body: password (optional), password_expires_at (optional, ISO-Datum),
          reminder_emails (optional, Liste E-Mail-Adressen).
    """
    try:
        creds = _load_credentials()
        if 'external_systems' not in creds:
            creds['external_systems'] = {}
        sb = creds['external_systems'].setdefault('stellantis_servicebox', {})

        data = request.get_json(force=True, silent=True) or {}
        updated = False

        if 'password' in data and data['password'] is not None and str(data['password']).strip():
            sb['password'] = str(data['password']).strip()
            updated = True
        if 'password_expires_at' in data:
            val = data['password_expires_at']
            sb['password_expires_at'] = (val.strip() if isinstance(val, str) and val.strip() else None) or None
            updated = True
        if 'reminder_emails' in data:
            raw = data['reminder_emails']
            if isinstance(raw, list):
                sb['reminder_emails'] = [str(e).strip() for e in raw if str(e).strip()]
            elif isinstance(raw, str):
                sb['reminder_emails'] = [e.strip() for e in raw.split(',') if e.strip()]
            else:
                sb['reminder_emails'] = []
            updated = True

        if not updated:
            return jsonify({'message': 'Nichts geändert', 'success': True})

        _save_credentials(creds)
        return jsonify({
            'message': 'ServiceBox-Zugang aktualisiert',
            'success': True,
            'password_expires_at': sb.get('password_expires_at'),
            'reminder_emails': sb.get('reminder_emails', []),
        })
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
