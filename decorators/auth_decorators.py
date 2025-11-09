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

logger = logging.getLogger(__name__)


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
    
    Usage:
        @app.route('/admin/users')
        @admin_required
        def manage_users():
            return render_template('admin_users.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Bitte melden Sie sich an.', 'warning')
            return redirect(url_for('login', next=request.url))
        
        if not current_user.has_role('admin'):
            logger.warning(f"⚠️ Admin-Zugriff verweigert: {current_user.username} → {request.path}")
            flash('Dieser Bereich ist nur für Administratoren zugänglich.', 'danger')
            return redirect(url_for('portal_home'))
        
        return f(*args, **kwargs)
    return decorated_function
