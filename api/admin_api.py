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
from flask_login import current_user, login_required
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

            # User mit Rollen laden (inkl. portal_role_override für granulare Rechte)
            cursor.execute(f'''
                SELECT
                    u.id,
                    u.username,
                    u.display_name,
                    u.ou,
                    u.title,
                    u.last_login,
                    u.portal_role_override,
                    {concat_func} as roles
                FROM users u
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                GROUP BY u.id, u.username, u.display_name, u.ou, u.title, u.last_login, u.portal_role_override
                ORDER BY u.display_name
            ''')

            users = []
            for row in cursor.fetchall():
                row_dict = row_to_dict(row)
                user_id = row_dict['id']
                dashboard_config = dashboard_configs.get(user_id, {})
                roles_str = row_dict['roles'] or 'keine'
                # Option B: Wirksame Portal-Rolle nur aus DB – Admin > zugewiesene Rolle > Default mitarbeiter
                if roles_str and 'admin' in [r.strip() for r in roles_str.split(',')]:
                    effective_portal_role = 'admin'
                elif row_dict.get('portal_role_override'):
                    effective_portal_role = (row_dict['portal_role_override'] or '').strip() or 'mitarbeiter'
                else:
                    effective_portal_role = 'mitarbeiter'
                
                users.append({
                    'id': user_id,
                    'username': row_dict['username'],
                    'display_name': row_dict['display_name'],
                    'ou': row_dict['ou'],
                    'title': row_dict['title'],
                    'last_login': row_dict['last_login'],
                    'roles': roles_str,
                    'portal_role_override': row_dict.get('portal_role_override'),
                    'effective_portal_role': effective_portal_role or 'mitarbeiter',
                    'dashboard_url': dashboard_config.get('url'),
                    'dashboard_name': dashboard_config.get('name')
                })

            # Verfügbare Rollen (DB-Rollen für user_roles)
            cursor.execute('SELECT id, name, description FROM roles ORDER BY name')
            roles = rows_to_list(cursor.fetchall())

            from config.roles_config import PORTAL_ROLES_FOR_ADMIN

        return jsonify({
            'users': users,
            'available_roles': roles,
            'available_portal_roles': PORTAL_ROLES_FOR_ADMIN,
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


@admin_api.route('/api/admin/user/<int:user_id>/portal-role', methods=['POST'])
@admin_required
def set_user_portal_role(user_id):
    """Portal-Rolle (Override) für User setzen – granulare Rechteverwaltung.
    Bestimmt die wirksame Rolle für Navi + Feature-Zugriff (sofern User nicht Admin).
    Body: { "portal_role": "verkauf" } oder { "portal_role": null } um auf LDAP zurückzusetzen.
    """
    try:
        data = request.get_json() or {}
        portal_role = data.get('portal_role')
        if portal_role is not None and portal_role != '':
            portal_role = str(portal_role).strip()
            if not portal_role:
                portal_role = None
        else:
            portal_role = None

        ph = sql_placeholder()
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_placeholders('UPDATE users SET portal_role_override = ? WHERE id = ?'),
                (portal_role, user_id)
            )
            if cursor.rowcount == 0:
                return jsonify({'error': 'User nicht gefunden'}), 404
            conn.commit()

        msg = f'Portal-Rolle auf "{portal_role}" gesetzt' if portal_role else 'Portal-Rolle zurückgesetzt (aus LDAP)'
        return jsonify({'message': msg, 'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/user/<int:user_id>/effective-rights', methods=['GET'])
@admin_required
def get_user_effective_rights(user_id):
    """Rechte & Navi für einen User (nur Anzeige). Liefert wirksame Rolle, Feature-Liste und sichtbare Navigation."""
    try:
        from config.roles_config import get_allowed_features
        from api.navigation_utils import get_navigation_for_role

        ph = sql_placeholder()
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT u.id, u.display_name, u.portal_role_override,
                       (SELECT 1 FROM user_roles ur JOIN roles r ON ur.role_id = r.id
                        WHERE ur.user_id = u.id AND r.name = 'admin' LIMIT 1) AS is_admin
                FROM users u WHERE u.id = {ph}
            ''', (user_id,))
            row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'User nicht gefunden'}), 404

        row_dict = row_to_dict(row)
        is_admin = row_dict.get('is_admin') is not None
        effective_role = 'admin' if is_admin else (
            (row_dict.get('portal_role_override') or '').strip() or 'mitarbeiter'
        )
        allowed_features = get_allowed_features(effective_role)
        if is_admin:
            from config.roles_config import get_feature_access_from_db
            allowed_features = sorted(get_feature_access_from_db().keys())
        features_list = sorted(allowed_features) if isinstance(allowed_features, (list, set)) else []
        nav_tree = get_navigation_for_role(effective_role, set(features_list))

        def nav_to_serializable(items):
            out = []
            for it in items:
                node = {'label': it.get('label'), 'url': it.get('url'), 'icon': it.get('icon')}
                if it.get('children'):
                    node['children'] = nav_to_serializable(it['children'])
                out.append(node)
            return out

        return jsonify({
            'display_name': row_dict.get('display_name'),
            'effective_role': effective_role,
            'features': features_list,
            'navigation': nav_to_serializable(nav_tree)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/feature-access', methods=['GET'])
@admin_required
def get_feature_access():
    """Feature-Zugriffs-Matrix für Rechteverwaltung: nur aus DB, kein Merge mit Config.
    Redundanz entfernt: get_feature_access_from_db() mischt FEATURE_ACCESS (Config) mit DB
    und kann dadurch gelöschte Rollen wieder anzeigen. Hier lesen wir nur die Tabelle feature_access.
    """
    try:
        from config.roles_config import TITLE_TO_ROLE, FEATURE_ACCESS, clear_feature_access_cache
        from flask import make_response

        clear_feature_access_cache()

        # Nur DB lesen – keine Zusammenführung mit FEATURE_ACCESS (keine Redundanz)
        db_access = {}
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute('SELECT feature_name, role_name FROM feature_access ORDER BY feature_name, role_name')
            for row in cur.fetchall():
                fn = row.get('feature_name', row[0]) if hasattr(row, 'get') else row[0]
                rn = row.get('role_name', row[1]) if hasattr(row, 'get') else row[1]
                if fn not in db_access:
                    db_access[fn] = []
                db_access[fn].append(rn)

        # Alle Feature-Keys (Config + Nav), Werte nur aus DB – fehlende Features = []
        all_keys = set(FEATURE_ACCESS.keys())
        try:
            with db_session() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT DISTINCT requires_feature FROM navigation_items
                    WHERE active = true AND requires_feature IS NOT NULL AND TRIM(requires_feature) != ''
                """)
                for row in cur.fetchall():
                    f = (row[0] if hasattr(row, '__getitem__') else getattr(row, 'requires_feature', None) or '').strip()
                    if f:
                        all_keys.add(f)
        except Exception:
            pass
        feature_access = {f: db_access.get(f, []) for f in sorted(all_keys)}

        resp = make_response(jsonify({
            'feature_access': feature_access,
            'title_to_role': TITLE_TO_ROLE
        }))
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        return resp

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
        from config.roles_config import clear_feature_access_cache
        clear_feature_access_cache()
        return jsonify({
            'message': f'Feature "{feature}" aktualisiert',
            'success': True
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/role/<role_name>/features', methods=['POST'])
@admin_required
def set_role_features(role_name):
    """Feature-Zugriff für eine Rolle setzen (Rollen-Ansicht).
    Body: { "features": ["bankenspiegel", "controlling", ...] }
    Ersetzt alle Feature-Zuordnungen für diese Rolle in der DB.
    """
    try:
        # Admin: portal_role == 'admin' ODER can_access_feature('admin') (admin-Feature in allowed_features)
        is_admin = getattr(current_user, 'portal_role', '') == 'admin'
        if not is_admin and not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('admin')):
            return jsonify({'error': 'Keine Berechtigung'}), 403
        data = request.get_json() or {}
        features = data.get('features', [])
        if not isinstance(features, list):
            return jsonify({'error': 'features muss eine Liste sein'}), 400
        features = [f for f in features if f and isinstance(f, str)]
        ph = sql_placeholder()
        created_by = getattr(current_user, 'username', None) or 'admin'
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f'DELETE FROM feature_access WHERE role_name = {ph}',
                (role_name,)
            )
            for feature in features:
                cursor.execute(
                    f'''
                    INSERT INTO feature_access (feature_name, role_name, created_by, created_at)
                    VALUES ({ph}, {ph}, {ph}, {ph})
                    ON CONFLICT (feature_name, role_name) DO NOTHING
                    ''',
                    (feature, role_name, created_by, datetime.now().isoformat())
                )
            conn.commit()
        from config.roles_config import clear_feature_access_cache
        clear_feature_access_cache()
        return jsonify({
            'message': f'Rolle "{role_name}": {len(features)} Features gesetzt',
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# FEATURE FILTER MODE (Listen mit Verkäufer-Filter: nur eigene / auflösbar / alle)
# =============================================================================

# Features, die einen Verkäufer-Filter haben und konfigurierbar sind
from api.feature_filter_mode import get_filter_mode as _get_filter_mode, FEATURE_FILTER_FEATURES


@admin_api.route('/api/admin/feature-filter-modes', methods=['GET'])
@admin_required
def get_feature_filter_modes():
    """Alle Filter-Modi für Rechteverwaltung (Admin)."""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT feature_name, role_name, filter_mode
                FROM feature_filter_mode
                ORDER BY feature_name, role_name
            ''')
            rows = cursor.fetchall()
        modes = [{'feature_name': r[0], 'role_name': r[1], 'filter_mode': r[2]} for r in rows]
        return jsonify({'success': True, 'modes': modes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/feature-filter-mode', methods=['POST'])
@admin_required
def set_feature_filter_mode():
    """Filter-Modus für Feature + Rolle setzen. Body: feature_name, role_name, filter_mode."""
    try:
        data = request.get_json() or {}
        feature_name = (data.get('feature_name') or '').strip()
        role_name = (data.get('role_name') or '').strip()
        filter_mode = (data.get('filter_mode') or '').strip()
        if feature_name not in FEATURE_FILTER_FEATURES:
            return jsonify({'error': f'Unbekanntes Feature für Filter-Modus: {feature_name}'}), 400
        if filter_mode not in ('own_only', 'own_default', 'all_filterable'):
            return jsonify({'error': 'filter_mode muss own_only, own_default oder all_filterable sein'}), 400
        ph = sql_placeholder()
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                INSERT INTO feature_filter_mode (feature_name, role_name, filter_mode)
                VALUES ({ph}, {ph}, {ph})
                ON CONFLICT (feature_name, role_name) DO UPDATE SET filter_mode = EXCLUDED.filter_mode
            ''', (feature_name, role_name, filter_mode))
            conn.commit()
        return jsonify({'success': True, 'message': f'{feature_name} / {role_name}: {filter_mode}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/feature-filter-mode/<feature_name>', methods=['GET'])
@login_required
def get_my_feature_filter_mode(feature_name):
    """Filter-Modus für aktuellen User und Feature (für Seiten mit Verkäufer-Filter)."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Nicht angemeldet'}), 401
    if feature_name not in FEATURE_FILTER_FEATURES:
        return jsonify({'filter_mode': 'all_filterable'}), 200
    role = getattr(current_user, 'portal_role', '') or 'mitarbeiter'
    mode = _get_filter_mode(role, feature_name)
    return jsonify({'filter_mode': mode})


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
            
            # Wirksame Portal-Rolle des Ziel-Users ermitteln
            cursor.execute(f'''
                SELECT u.portal_role_override,
                    (SELECT 1 FROM user_roles ur JOIN roles r ON ur.role_id = r.id WHERE ur.user_id = u.id AND r.name = 'admin' LIMIT 1) AS has_admin
                FROM users u WHERE u.id = {ph}
            ''', (user_id,))
            user_row = cursor.fetchone()
            if not user_row:
                return jsonify({'error': 'User nicht gefunden'}), 404
            override = (user_row[0] or '').strip() if user_row[0] else ''
            has_admin = user_row[1] is not None
            effective_role = 'admin' if has_admin else (override or 'mitarbeiter')
            
            # Dashboard-Zeile und requires_feature prüfen
            cursor.execute(f'''
                SELECT requires_feature, role_restriction FROM available_dashboards
                WHERE active = true AND url = {ph}
            ''', (target_url,))
            dash_row = cursor.fetchone()
            if dash_row:
                req_feature = (dash_row[0] or '').strip() if dash_row[0] else ''
                role_restriction = (dash_row[1] or '').strip() if dash_row[1] else ''
                if req_feature:
                    from config.roles_config import get_feature_access_from_db
                    fa = get_feature_access_from_db()
                    allowed_roles = fa.get(req_feature, [])
                    if effective_role != 'admin' and effective_role not in allowed_roles and '*' not in allowed_roles:
                        return jsonify({
                            'error': f'Die Rolle "{effective_role}" hat keinen Zugriff auf diese Startseite (Feature: {req_feature}). Zuweisung nicht erlaubt.'
                        }), 400
                if role_restriction and effective_role != 'admin' and effective_role != role_restriction:
                    return jsonify({
                        'error': f'Diese Startseite ist auf die Rolle "{role_restriction}" beschränkt. User hat Rolle "{effective_role}".'
                    }), 400
            
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
            
            raw = rows_to_list(cursor.fetchall())
            # JSON-sicher: bool/None explizit (PostgreSQL kann sonst nicht serialisierbar liefern)
            items = []
            for row in raw:
                items.append({
                    'id': int(row['id']) if row.get('id') is not None else None,
                    'parent_id': int(row['parent_id']) if row.get('parent_id') is not None else None,
                    'label': str(row['label']) if row.get('label') is not None else None,
                    'url': str(row['url']) if row.get('url') is not None else None,
                    'icon': str(row['icon']) if row.get('icon') is not None else None,
                    'order_index': int(row['order_index']) if row.get('order_index') is not None else 0,
                    'requires_feature': str(row['requires_feature']) if row.get('requires_feature') is not None else None,
                    'role_restriction': str(row['role_restriction']) if row.get('role_restriction') is not None else None,
                    'is_dropdown': bool(row.get('is_dropdown')),
                    'is_header': bool(row.get('is_header')),
                    'is_divider': bool(row.get('is_divider')),
                    'active': bool(row.get('active', True)),
                    'category': str(row['category']) if row.get('category') is not None else 'main',
                })
        
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
