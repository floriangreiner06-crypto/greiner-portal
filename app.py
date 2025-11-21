
"""
Greiner Portal - Flask Application
Mit Active Directory Authentication
"""
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import timedelta
import os

# ============================================================================
# FLASK APP INITIALISIERUNG
# ============================================================================

app = Flask(__name__)

# ============================================================================
# CACHE-BUSTING KONFIGURATION (siehe docs/CACHING_STRATEGY.md)
# ============================================================================
import os
from datetime import datetime

# Entwicklung: Kein Caching
if os.getenv('FLASK_ENV') == 'development' or app.debug:
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
else:
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 Jahr in Produktion

# Globale Static-Version (ändert sich bei jedem Flask-Neustart)
STATIC_VERSION = datetime.now().strftime('%Y%m%d%H%M%S')
print(f"📦 Static Version: {STATIC_VERSION}")

# Template-Kontext: Macht STATIC_VERSION in allen Templates verfügbar
@app.context_processor
def inject_version():
    return {'STATIC_VERSION': STATIC_VERSION}
# ============================================================================


# ============================================================================
# KONFIGURATION
# ============================================================================

# Secret Key aus .env laden (falls vorhanden)
secret_key_file = 'config/.env'
if os.path.exists(secret_key_file):
    with open(secret_key_file) as f:
        for line in f:
            if line.startswith('SECRET_KEY='):
                app.config['SECRET_KEY'] = line.split('=', 1)[1].strip()
                break

# Fallback Secret Key (falls nicht in .env)
if 'SECRET_KEY' not in app.config:
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-CHANGE-IN-PRODUCTION'

# Session-Konfiguration
app.config['SESSION_COOKIE_SECURE'] = False  # True für HTTPS in Production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

# ============================================================================
# FLASK-LOGIN SETUP
# ============================================================================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Bitte melden Sie sich an um fortzufahren.'
login_manager.login_message_category = 'info'

# Auth-Manager importieren
try:
    from auth.auth_manager import get_auth_manager
    auth_manager = get_auth_manager()
    print("✅ Auth-Manager geladen")
except ImportError as e:
    print(f"⚠️  Auth-Manager nicht gefunden: {e}")
    auth_manager = None

@login_manager.user_loader
def load_user(user_id):
    """Lädt User für Flask-Login Session"""
    if auth_manager:
        return auth_manager.get_user_by_id(int(user_id))
    return None

# ============================================================================
# CONTEXT PROCESSORS
# ============================================================================

@app.context_processor
def inject_globals():
    """Macht Variablen in allen Templates verfügbar"""
    from datetime import datetime
    return {
        'current_user': current_user,
        'now': datetime.now(),
        'app_name': 'Greiner Portal',
        'app_version': '2.0'
    }

# ============================================================================
# AUTH ROUTES
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login-Page und Authentication"""
    # Wenn bereits eingeloggt, redirect zu Home
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        if not username or not password:
            flash('Bitte geben Sie Benutzername und Passwort ein.', 'warning')
            return render_template('login.html')
        
        if auth_manager:
            try:
                user = auth_manager.authenticate_user(username, password)
                
                if user:
                    login_user(user, remember=remember)
                    flash(f'Willkommen zurück, {user.display_name}!', 'success')
                    
                    next_page = request.args.get('next')
                    if next_page and next_page.startswith('/'):
                        return redirect(next_page)
                    return redirect(url_for('dashboard'))
                else:
                    flash('Ungültiger Benutzername oder Passwort.', 'danger')
            except Exception as e:
                print(f"Login-Fehler: {e}")
                flash('Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.', 'danger')
        else:
            flash('Authentication-System nicht verfügbar.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout und Session beenden"""
    if auth_manager:
        auth_manager.logout_user(current_user)
    logout_user()
    flash('Sie wurden erfolgreich abgemeldet.', 'info')
    return redirect(url_for('login'))

# ============================================================================
# MAIN ROUTES
# ============================================================================

@app.route('/health')
def health():
    """Health-Check Endpoint"""
    return jsonify({'status': 'healthy'})

# ============================================================================
# BLUEPRINTS REGISTRIEREN
# ============================================================================

# Vacation API
from api.vacation_api import vacation_api
app.register_blueprint(vacation_api)
print("✅ Vacation API registriert: /api/vacation/")

# Urlaubsplaner V2 Route
@app.route('/urlaubsplaner/v2')
@login_required
def urlaubsplaner_v2():
    """Moderne Urlaubsplaner Oberfläche (V2)"""
    return render_template('urlaubsplaner_v2.html')

# Bankenspiegel API
from api.bankenspiegel_api import bankenspiegel_api
app.register_blueprint(bankenspiegel_api)
print("✅ Bankenspiegel API registriert: /api/bankenspiegel/")

# Bankenspiegel Frontend Routes
from routes.bankenspiegel_routes import bankenspiegel_bp
app.register_blueprint(bankenspiegel_bp)
print("✅ Bankenspiegel Frontend registriert: /bankenspiegel/")

# Verkauf API
from api.verkauf_api import verkauf_api
from api.stellantis_api import stellantis_api
app.register_blueprint(verkauf_api)
app.register_blueprint(stellantis_api)
print("✅ Verkauf API registriert: /api/verkauf/")
print("✅ Stellantis API registriert: /api/stellantis/")

# Verkauf Frontend Routes
from routes.verkauf_routes import verkauf_bp
from routes.controlling_routes import controlling_bp
app.register_blueprint(verkauf_bp)
print("✅ Verkauf Frontend registriert: /verkauf/")
app.register_blueprint(controlling_bp)
print("✅ Controlling registriert: /controlling/")

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(401)
def unauthorized(e):
    """Handler für 401 Unauthorized"""
    flash('Sie müssen sich anmelden um auf diese Seite zuzugreifen.', 'warning')
    return redirect(url_for('login', next=request.url))

@app.errorhandler(403)
def forbidden(e):
    """Handler für 403 Forbidden"""
    flash('Sie haben keine Berechtigung für diesen Bereich.', 'danger')
    return redirect(url_for('dashboard'))

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 GREINER PORTAL STARTET...")
    print("=" * 80)
    print(f"🔐 Auth-System: {'✅ Aktiviert' if auth_manager else '⚠️  Nicht verfügbar'}")
    print(f"🔑 Secret Key: {'✅ Geladen' if app.config.get('SECRET_KEY') else '❌ Fehlt'}")
    print("=" * 80)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

# ========================================
# DASHBOARD (STARTSEITE)
# ========================================

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    """Hauptdashboard - Startseite nach Login"""
    from datetime import datetime
    return render_template('dashboard.html', now=datetime.now())


# After Sales Routes
from routes.aftersales import teile_routes
app.register_blueprint(teile_routes.bp)
