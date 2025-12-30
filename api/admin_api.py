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
import os
import json

from api.db_utils import db_session, row_to_dict, rows_to_list
from api.db_connection import convert_placeholders, sql_placeholder, get_db_type

admin_api = Blueprint('admin_api', __name__)


@admin_api.route('/api/admin/logs', methods=['GET'])
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
                users.append({
                    'id': row_dict['id'],
                    'username': row_dict['username'],
                    'display_name': row_dict['display_name'],
                    'ou': row_dict['ou'],
                    'title': row_dict['title'],
                    'last_login': row_dict['last_login'],
                    'roles': row_dict['roles'] or 'keine'
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
def get_feature_access():
    """Feature-Zugriffs-Matrix laden"""
    try:
        from config.roles_config import FEATURE_ACCESS, TITLE_TO_ROLE

        return jsonify({
            'feature_access': FEATURE_ACCESS,
            'title_to_role': TITLE_TO_ROLE
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# REPORT SUBSCRIPTIONS - TAG 135
# =============================================================================

@admin_api.route('/api/admin/reports', methods=['GET'])
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


@admin_api.route('/api/admin/reports/employees', methods=['GET'])
def get_employees_for_reports():
    """Mitarbeiter-Liste für Autocomplete beim Hinzufügen
    TAG 136: PostgreSQL-kompatibel
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT DISTINCT
                    LOWER(username || '@auto-greiner.de') as email,
                    display_name as name
                FROM users
                WHERE username IS NOT NULL
                ORDER BY display_name
            ''')

            employees = rows_to_list(cursor.fetchall())

        return jsonify({'employees': employees})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
