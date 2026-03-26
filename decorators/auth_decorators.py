"""
Auth Decorators für Route-Protection
Login-Required, Role-Required, Permission-Required

Author: Claude
Date: 2025-11-08
"""

from functools import wraps
from flask import redirect, url_for, flash, request, jsonify
from flask_login import current_user
import logging
import os
import json
import hashlib
import hmac

logger = logging.getLogger(__name__)


def _load_api_keys() -> dict:
    """
    Lädt erlaubte API-Keys.
    Priorität:
    1) ENV DRIVE_API_KEYS (comma-separated)
    2) config/credentials.json -> api_access.api_keys (Liste)
    """
    keys = {}

    env_keys = os.getenv('DRIVE_API_KEYS', '')
    if env_keys:
        for key in (k.strip() for k in env_keys.split(',') if k.strip()):
            keys[key] = {'ai_query'}

    creds_file = 'config/credentials.json'
    if os.path.exists(creds_file):
        try:
            with open(creds_file, 'r', encoding='utf-8') as f:
                creds = json.load(f)
                api_access = creds.get('api_access') if isinstance(creds, dict) else {}
                json_keys = api_access.get('api_keys', []) if isinstance(api_access, dict) else []
                if isinstance(json_keys, list):
                    for entry in json_keys:
                        if isinstance(entry, str) and entry.strip():
                            keys[entry.strip()] = {'ai_query'}
                        elif isinstance(entry, dict):
                            key_value = str(entry.get('key') or '').strip()
                            if key_value:
                                scopes = entry.get('scopes') or ['ai_query']
                                if isinstance(scopes, list):
                                    keys[key_value] = {str(s).strip() for s in scopes if str(s).strip()}
        except Exception as e:
            logger.warning("API-Key Config konnte nicht geladen werden: %s", e)

    return keys


def _get_request_api_key() -> str:
    """Liest API-Key aus Headern/Query."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.lower().startswith('bearer '):
        token = auth_header[7:].strip()
        if token:
            return token
    return (
        request.headers.get('X-API-Key')
        or ''
    ).strip()


def login_required(f):
    """
    Decorator: Route erfordert Login
    
    Usage:
        @app.route('/dashboard')
        @login_required
        def dashboard():
            return render_template('dashboard.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Bitte melden Sie sich an um fortzufahren.', 'warning')
            # Merke die ursprüngliche URL für Redirect nach Login
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def role_required(roles):
    """
    Decorator: Route erfordert bestimmte Rolle(n)
    
    Args:
        roles: String oder Liste von Rollen-Namen
        
    Usage:
        @app.route('/admin')
        @role_required('admin')
        def admin_panel():
            return render_template('admin.html')
            
        @app.route('/management')
        @role_required(['admin', 'geschaeftsfuehrung'])
        def management():
            return render_template('management.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Bitte melden Sie sich an.', 'warning')
                return redirect(url_for('login', next=request.url))
            
            # Rolle(n) in Liste konvertieren
            required_roles = [roles] if isinstance(roles, str) else roles
            
            # Prüfe ob User eine der erforderlichen Rollen hat
            has_role = any(current_user.has_role(role) for role in required_roles)
            
            if not has_role:
                logger.warning(f"⚠️ Zugriff verweigert: {current_user.username} → {request.path} (Rolle fehlt)")
                flash('Sie haben keine Berechtigung für diesen Bereich.', 'danger')
                return redirect(url_for('portal_home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permission_required(permission):
    """
    Decorator: Route erfordert bestimmte Berechtigung
    
    Args:
        permission: Name der Berechtigung (z.B. 'full_access', 'financials')
        
    Usage:
        @app.route('/finances')
        @permission_required('financials')
        def finances():
            return render_template('finances.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Bitte melden Sie sich an.', 'warning')
                return redirect(url_for('login', next=request.url))
            
            if not current_user.has_permission(permission):
                logger.warning(f"⚠️ Zugriff verweigert: {current_user.username} → {request.path} (Permission fehlt: {permission})")
                flash('Sie haben keine Berechtigung für diesen Bereich.', 'danger')
                return redirect(url_for('portal_home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def module_required(module):
    """
    Decorator: Route erfordert Zugriff auf bestimmtes Modul
    
    Args:
        module: Modul-Name (z.B. 'verkauf', 'bankenspiegel')
        
    Usage:
        @app.route('/verkauf')
        @module_required('verkauf')
        def verkauf():
            return render_template('verkauf.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Bitte melden Sie sich an.', 'warning')
                return redirect(url_for('login', next=request.url))
            
            if not current_user.can_access_module(module):
                logger.warning(f"⚠️ Zugriff verweigert: {current_user.username} → {request.path} (Modul: {module})")
                flash(f'Sie haben keinen Zugriff auf das Modul "{module}".', 'danger')
                return redirect(url_for('portal_home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_key_required(f):
    """
    Decorator: API-Route erfordert gültigen API-Key (für externe Zugriffe)
    
    Usage:
        @app.route('/api/data')
        @api_key_required
        def api_data():
            return jsonify({'data': 'sensitive'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # API-Key aus Header oder Query-Parameter
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            logger.warning(f"⚠️ API-Zugriff ohne Key: {request.path}")
            return jsonify({'error': 'API key required'}), 401
        
        # TODO: API-Key Validierung gegen Datenbank
        # Für jetzt: Nur für eingeloggte User
        if not current_user.is_authenticated:
            logger.warning(f"⚠️ API-Zugriff mit ungültigem Key: {request.path}")
            return jsonify({'error': 'Invalid API key'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def ajax_login_required(f):
    """
    Decorator: AJAX-Route erfordert Login (gibt JSON statt Redirect zurück)
    
    Usage:
        @app.route('/api/ajax-data')
        @ajax_login_required
        def ajax_data():
            return jsonify({'data': 'sensitive'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required', 'redirect': url_for('login')}), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator: Route nur für Admins
    Shortcut für @role_required('admin')
    Bei API-Requests (/api/...) oder Accept: application/json → JSON 401/403 statt Redirect.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.path.startswith('/api/') or 'application/json' in request.accept_mimetypes:
                return jsonify({'error': 'Bitte anmelden.'}), 401
            flash('Bitte melden Sie sich an.', 'warning')
            return redirect(url_for('login', next=request.url))
        
        is_admin = current_user.has_role('admin')
        if not is_admin and hasattr(current_user, 'portal_role') and current_user.portal_role == 'admin':
            is_admin = True
        if not is_admin and hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('admin'):
            is_admin = True

        if not is_admin:
            logger.warning(f"⚠️ Admin-Zugriff verweigert: {current_user.username} → {request.path}")
            if request.path.startswith('/api/') or 'application/json' in request.accept_mimetypes:
                return jsonify({'error': 'Keine Berechtigung (nur für Administratoren).'}), 403
            flash('Dieser Bereich ist nur für Administratoren zugänglich.', 'danger')
            return redirect(url_for('portal_home'))
        
        return f(*args, **kwargs)
    return decorated_function


def login_or_api_key_required(f):
    """
    Decorator: akzeptiert entweder Session-Login oder gültigen API-Key.
    Für API-Workflows immer JSON-Fehler statt Redirect.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            request.environ['drive.auth_mode'] = 'session'
            request.environ['drive.auth_scopes'] = ''
            return f(*args, **kwargs)

        provided_key = _get_request_api_key()
        if not provided_key:
            return jsonify({'success': False, 'error': 'Authentication required (Login oder API-Key).'}), 401

        valid_key_map = _load_api_keys()
        if not valid_key_map:
            logger.warning("API-Key Auth aktiv, aber keine Keys konfiguriert")
            return jsonify({'success': False, 'error': 'API-Key Auth nicht konfiguriert.'}), 503

        # timing-safe Vergleich
        matched_key = None
        for valid_key in valid_key_map.keys():
            if hmac.compare_digest(provided_key, valid_key):
                matched_key = valid_key
                break
        if not matched_key:
            # Zusätzlich Hash im Log für Diagnosen, ohne Key zu leaken
            key_hash = hashlib.sha256(provided_key.encode('utf-8')).hexdigest()[:12]
            logger.warning("Ungültiger API-Key verwendet (hash=%s)", key_hash)
            return jsonify({'success': False, 'error': 'Invalid API key'}), 403

        scopes = valid_key_map.get(matched_key, set())
        request.environ['drive.auth_mode'] = 'api_key'
        request.environ['drive.auth_scopes'] = ','.join(sorted(scopes))

        return f(*args, **kwargs)

    return decorated_function
