
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
STATIC_VERSION = '20251207020000'  # TAG 100 - Teile-Status Dashboard
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

# Vacation Chef API (TAG 103 - Chef-Übersicht)
try:
    from api.vacation_chef_api import chef_api
    app.register_blueprint(chef_api)
    print("✅ Vacation Chef API registriert: /api/vacation/chef-overview")
except Exception as e:
    print(f"⚠️  Vacation Chef API nicht geladen: {e}")

# Vacation Admin API (TAG 103 - HR Administration)
try:
    from api.vacation_admin_api import vacation_admin_api
    app.register_blueprint(vacation_admin_api)
    print("✅ Vacation Admin API registriert: /api/vacation/admin/")
except Exception as e:
    print(f"⚠️  Vacation Chef API nicht geladen: {e}")

# Urlaubsplaner V2 Route
@app.route('/urlaubsplaner/v2')
@login_required
def urlaubsplaner_v2():
    """Moderne Urlaubsplaner Oberfläche (V2)"""
    return render_template('urlaubsplaner_v2.html')

# Urlaubsplaner Chef-Übersicht (TAG 103)
@app.route('/urlaubsplaner/chef')
@login_required
def urlaubsplaner_chef():
    """Chef-Übersicht: Alle Teams und Genehmiger"""
    return render_template('urlaubsplaner_chef.html')

# Urlaubsplaner Admin (TAG 103 - HR Administration)
@app.route('/urlaubsplaner/admin')
@login_required
def urlaubsplaner_admin():
    """HR-Admin: Urlaubsansprüche verwalten"""
    return render_template('urlaubsplaner_admin.html')

# Urlaubsplaner Kurzroute
@app.route('/urlaubsplaner')
@login_required
def urlaubsplaner():
    """Urlaubsplaner - Redirect zu V2"""
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
from api.parts_api import parts_api
from api.admin_api import admin_api
from api.zins_optimierung_api import zins_api
from api.teile_api import teile_api
app.register_blueprint(verkauf_api)
app.register_blueprint(parts_api)
app.register_blueprint(admin_api)
app.register_blueprint(teile_api)
app.register_blueprint(zins_api)
print("✅ Verkauf API registriert: /api/verkauf/")
print("✅ Parts API registriert: /api/stellantis/")
print("✅ Admin API registriert: /api/admin/")

# Mail API (Graph/Office 365)
try:
    from api.mail_api import mail_api
    app.register_blueprint(mail_api)
    print("✅ Mail API registriert: /api/mail/")
except Exception as e:
    print(f"⚠️  Mail API nicht geladen: {e}")

# Leasys Programmfinder API
try:
    from api.leasys_api import leasys_api
    app.register_blueprint(leasys_api)
    print("✅ Leasys API registriert: /api/leasys/")
except Exception as e:
    print(f"⚠️  Leasys API nicht geladen: {e}")

# Verkauf Frontend Routes
from routes.verkauf_routes import verkauf_bp
from routes.controlling_routes import controlling_bp
app.register_blueprint(verkauf_bp)
print("✅ Verkauf Frontend registriert: /verkauf/")
app.register_blueprint(controlling_bp)
print("✅ Controlling registriert: /controlling/")

# Controlling API (BWA)
try:
    from api.controlling_api import controlling_api
    app.register_blueprint(controlling_api)
    print("✅ Controlling API registriert: /api/controlling/")
except Exception as e:
    print(f"⚠️  Controlling API nicht geladen: {e}")

# Jahresprämie API & Routes
try:
    from api.jahrespraemie_api import jahrespraemie_api
    from routes.jahrespraemie_routes import jahrespraemie_bp
    app.register_blueprint(jahrespraemie_api)
    app.register_blueprint(jahrespraemie_bp)
    print("✅ Jahresprämie API registriert: /api/jahrespraemie/")
    print("✅ Jahresprämie Frontend registriert: /jahrespraemie/")
except Exception as e:
    print(f"⚠️  Jahresprämie nicht geladen: {e}")

# ============================================================================
# JOB-SCHEDULER UI (Legacy - wird durch Celery ersetzt)
# ============================================================================
try:
    from scheduler import job_manager, scheduler_bp, init_scheduler_routes
    
    # Blueprint registrieren (für Web-UI unter /admin/jobs/)
    app.register_blueprint(scheduler_bp)
    init_scheduler_routes(job_manager)
    print("✅ Job-Scheduler UI registriert: /admin/jobs/ (Legacy)")
        
except Exception as e:
    print(f"⚠️  Job-Scheduler UI nicht geladen: {e}")

# ============================================================================
# CELERY TASK MANAGEMENT (TAG 110 - Ersetzt APScheduler)
# ============================================================================
try:
    from celery_app.routes import celery_bp
    app.register_blueprint(celery_bp)
    print("✅ Celery Task UI registriert: /admin/celery/")
    print("ℹ️  Flower Dashboard: http://localhost:5555")
except Exception as e:
    print(f"⚠️  Celery Task UI nicht geladen: {e}")

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
from routes.aftersales import serviceberater_routes
from routes.admin_routes import admin_routes
app.register_blueprint(teile_routes.bp)
app.register_blueprint(serviceberater_routes.bp)
app.register_blueprint(admin_routes)
print("✅ Serviceberater Routes registriert: /aftersales/serviceberater/")

# Serviceberater API
try:
    from api.serviceberater_api import serviceberater_api
    app.register_blueprint(serviceberater_api)
    print("✅ Serviceberater API registriert: /api/serviceberater/")
except Exception as e:
    print(f"⚠️  Serviceberater API nicht geladen: {e}")

# Werkstatt API (Leistungsübersicht)
try:
    from api.werkstatt_api import werkstatt_api
    app.register_blueprint(werkstatt_api)
    print("✅ Werkstatt API registriert: /api/werkstatt/")
except Exception as e:
    print(f"⚠️  Werkstatt API nicht geladen: {e}")

# Werkstatt LIVE API (Echtzeit-Daten aus Locosoft)
try:
    from api.werkstatt_live_api import werkstatt_live_bp
    app.register_blueprint(werkstatt_live_bp)
    print("✅ Werkstatt LIVE API registriert: /api/werkstatt/live/")
except Exception as e:
    print(f"⚠️  Werkstatt LIVE API nicht geladen: {e}")

# ML API (Machine Learning - Auftragsdauer-Vorhersage)
try:
    from api.ml_api import ml_api
    app.register_blueprint(ml_api)
    print("✅ ML API registriert: /api/ml/")
except Exception as e:
    print(f"⚠️  ML API nicht geladen: {e}")

# Teile-Status API (TAG 100 - Fehlende Teile auf Aufträgen)
try:
    from api.teile_status_api import teile_status_bp
    app.register_blueprint(teile_status_bp)
    print("✅ Teile-Status API registriert: /api/teile/")
except Exception as e:
    print(f"⚠️  Teile-Status API nicht geladen: {e}")

# Gudat Werkstattplanung API (TAG98)
try:
    from api.gudat_api import register_gudat_api
    register_gudat_api(app)
    print("✅ Gudat API registriert: /api/gudat/")
except Exception as e:
    print(f"⚠️  Gudat API nicht geladen: {e}")

# DEBUG Route für TAG76 - später entfernen!
@app.route('/debug/user')
@login_required
def debug_user():
    """Debug: Zeigt aktuelle User-Session-Daten"""
    return {
        'username': current_user.username,
        'display_name': current_user.display_name,
        'title': getattr(current_user, 'title', 'N/A'),
        'portal_role': getattr(current_user, 'portal_role', 'N/A'),
        'allowed_features': getattr(current_user, 'allowed_features', []),
        'roles': current_user.roles
    }

# ========================================
# LEASYS PROGRAMMFINDER
# ========================================

@app.route('/verkauf/leasys-programmfinder')
@login_required
def leasys_programmfinder():
    """Leasys Programmfinder - Hilft Verkäufern das richtige Master Agreement zu finden"""
    return render_template('leasys_programmfinder.html')


# ========================================
# WERKSTATT ÜBERSICHT
# ========================================

@app.route('/werkstatt')
@app.route('/werkstatt/cockpit')
@login_required
def werkstatt_cockpit():
    """Werkstatt Cockpit - Minimalistisch: Ampel + Probleme (TAG 99)"""
    return render_template('aftersales/werkstatt_cockpit.html')


@app.route('/werkstatt/dashboard')
@login_required
def werkstatt_dashboard():
    """Werkstatt Dashboard - Konsolidierte Übersicht (TAG 99)"""
    return render_template('aftersales/werkstatt_dashboard.html')


@app.route('/werkstatt/uebersicht')
@login_required
def werkstatt_uebersicht():
    """Werkstatt-Übersicht - Mechaniker-Leistungsgrade (Legacy)"""
    return render_template('aftersales/werkstatt_uebersicht.html')


@app.route('/werkstatt/live')
@login_required
def werkstatt_live():
    """Werkstatt LIVE-Monitoring - Echtzeit-Auftragsübersicht"""
    return render_template('aftersales/werkstatt_live.html')


@app.route('/werkstatt/stempeluhr')
@login_required
def werkstatt_stempeluhr():
    """Werkstatt Stempeluhr - LIVE Mechaniker-Übersicht"""
    return render_template('aftersales/werkstatt_stempeluhr.html')


@app.route('/werkstatt/intelligence')
@login_required
def werkstatt_intelligence():
    """Werkstatt Intelligence - ML Dashboard"""
    return render_template('werkstatt_intelligence.html')


@app.route('/werkstatt/tagesbericht')
@login_required
def werkstatt_tagesbericht():
    """Werkstatt Tagesbericht - Kontrolle Stempelungen/Zuweisungen"""
    return render_template('aftersales/werkstatt_tagesbericht.html')


@app.route('/werkstatt/auftraege')
@login_required
def werkstatt_auftraege():
    """Werkstatt Aufträge - ML-Analyse (TAG 98)"""
    return render_template('aftersales/werkstatt_auftraege.html')


@app.route('/werkstatt/teile-status')
@login_required
def werkstatt_teile_status():
    """Werkstatt Teile-Status - Fehlende Teile Übersicht (TAG 100)"""
    return render_template('aftersales/werkstatt_teile_status.html')


@app.route('/monitor/stempeluhr')
@app.route('/werkstatt/stempeluhr/monitor')
def werkstatt_stempeluhr_monitor():
    """
    Werkstatt Stempeluhr - MONITOR VERSION (ohne Login)
    Zugriff über Token-Parameter oder interne IP.
    """
    # Monitor-Token (geheim halten!)
    MONITOR_TOKEN = 'Greiner2024Werkstatt!'
    
    # Token aus URL prüfen
    token = request.args.get('token', '')
    
    # IP prüfen
    client_ip = request.remote_addr
    if request.headers.get('X-Forwarded-For'):
        client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    # Zugriff erlauben wenn: korrekter Token ODER interne IP
    is_internal = client_ip.startswith('10.80.80.') or client_ip == '127.0.0.1'
    is_valid_token = token == MONITOR_TOKEN
    
    if not (is_internal or is_valid_token):
        return "Zugriff verweigert. Token erforderlich.", 403
    
    return render_template('aftersales/werkstatt_stempeluhr_monitor.html')
