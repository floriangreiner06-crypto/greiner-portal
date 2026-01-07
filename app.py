
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
    # Wenn bereits eingeloggt, redirect zu dynamischer Startseite (TAG122)
    if current_user.is_authenticated:
        return redirect(url_for('start'))
    
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
                    return redirect(url_for('start'))  # TAG122: Dynamische Startseite
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

# Organigramm (TAG 113 - Organisation & Vertretungsregeln)
@app.route('/admin/organigramm')
@login_required
def admin_organigramm():
    """Organigramm mit Vertretungsregeln-Editor"""
    return render_template('organigramm.html')

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

# Fahrzeug API (TAG 160 - Bestand aus Locosoft)
try:
    from api.fahrzeug_api import fahrzeug_api
    app.register_blueprint(fahrzeug_api)
    print("✅ Fahrzeug API registriert: /api/fahrzeug/")
except ImportError as e:
    print(f"⚠️  Fahrzeug API nicht geladen: {e}")
print("✅ Parts API registriert: /api/stellantis/")
print("✅ Admin API registriert: /api/admin/")

# eAutoseller API (TAG 145)
try:
    from api.eautoseller_api import eautoseller_api
    app.register_blueprint(eautoseller_api)
    print("✅ eAutoseller API registriert: /api/eautoseller/")
except ImportError as e:
    print(f"⚠️  eAutoseller API nicht geladen: {e}")

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

# Werkstatt Frontend Routes (TAG 119)
from routes.werkstatt_routes import werkstatt_routes
app.register_blueprint(werkstatt_routes)
print("✅ Werkstatt Frontend registriert: /werkstatt/")

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
# CELERY TASK MANAGER (TAG110 - Celery + RedBeat + Flower)
# APScheduler UI entfernt: TAG120 - Redundant, nur noch Celery
# ============================================================================
try:
    from celery_app.routes import celery_bp
    app.register_blueprint(celery_bp)
    print("✅ Celery Task Manager registriert: /admin/celery/")
except Exception as e:
    print(f"⚠️  Celery Task Manager nicht geladen: {e}")

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
@app.route('/start')
@login_required
def start():
    """
    Dynamische Startseite nach Login (TAG122)

    Leitet basierend auf portal_role zum passenden Dashboard:
    - serviceberater → Aftersales mit Standort-Filter
    - werkstatt_leitung → Werkstatt Dashboard
    - verkauf/verkauf_leitung → Verkauf Auftragseingang
    - admin/buchhaltung → Allgemeines Dashboard
    """
    role = getattr(current_user, 'portal_role', 'mitarbeiter')
    standort = getattr(current_user, 'standort', 'deggendorf')

    # Serviceberater → Persönlicher Bereich mit Badges
    if role == 'serviceberater':
        return redirect(url_for('mein_bereich'))

    # Werkstatt-Leitung → Werkstatt Dashboard
    if role == 'werkstatt_leitung':
        return redirect(url_for('werkstatt.werkstatt_dashboard'))

    # Service-Leitung → Aftersales Übersicht
    if role == 'service_leitung':
        return redirect(url_for('aftersales_serviceberater.controlling'))

    # Verkauf → Verkauf Auftragseingang
    if role in ['verkauf', 'verkauf_leitung']:
        return redirect(url_for('verkauf.auftragseingang'))

    # Default: Allgemeines Dashboard
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Hauptdashboard - Startseite nach Login"""
    from datetime import datetime
    return render_template('dashboard.html', now=datetime.now())


@app.route('/mein-bereich')
@app.route('/sb/mein-bereich')  # TAG 164: Alternative URL für Kompatibilität
@login_required
def mein_bereich():
    """
    Persönlicher Bereich für Serviceberater (TAG122)
    
    TAG 164: Unterstützt ma_id Parameter für Geschäfts-/Serviceleitung
    Zeigt KPI-Badges und Schnellzugriff auf relevante Bereiche
    """
    from flask import request
    from datetime import datetime
    from flask_login import current_user
    
    # TAG 164: ma_id Parameter für Geschäfts-/Serviceleitung
    ma_id_param = request.args.get('ma_id')
    
    # Prüfe Berechtigung: Wenn ma_id angegeben, muss User admin/controlling sein
    if ma_id_param:
        if not (current_user.can_access_feature('admin') or current_user.can_access_feature('controlling')):
            from flask import abort
            abort(403)
    
    return render_template('sb/mein_bereich.html', 
                         now=datetime.now(),
                         ma_id_param=ma_id_param)


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

# Kundenzentrale API (TAG 164 - Tägliches Fakturierungsziel)
try:
    from api.kundenzentrale_api import kundenzentrale_api
    app.register_blueprint(kundenzentrale_api)
    print("✅ Kundenzentrale API registriert: /api/kundenzentrale/")
except Exception as e:
    print(f"⚠️  Kundenzentrale API nicht geladen: {e}")

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
    
    # TAG 165: Abteilungsleiter-Planung
    try:
        from api.abteilungsleiter_planung_api import planung_bp
        app.register_blueprint(planung_bp)
        print("✅ Abteilungsleiter-Planung API registriert")
    except ImportError as e:
        print(f"⚠️  Abteilungsleiter-Planung API nicht gefunden: {e}")
    
    # TAG 165: Abteilungsleiter-Planung Routes
    try:
        from routes.planung_routes import planung_routes
        app.register_blueprint(planung_routes)
        print("✅ Abteilungsleiter-Planung Routes registriert")
    except ImportError as e:
        print(f"⚠️  Abteilungsleiter-Planung Routes nicht gefunden: {e}")
    print("✅ Werkstatt LIVE API registriert: /api/werkstatt/live/")
except Exception as e:
    print(f"⚠️  Werkstatt LIVE API nicht geladen: {e}")

# Reparaturpotenzial API (TAG 127 - Upselling-Empfehlungen für Serviceberater)
try:
    from api.reparaturpotenzial_api import reparaturpotenzial_api
    app.register_blueprint(reparaturpotenzial_api)
    print("✅ Reparaturpotenzial API registriert: /api/werkstatt/reparaturpotenzial")
except Exception as e:
    print(f"⚠️  Reparaturpotenzial API nicht geladen: {e}")

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
    
    # Portal-Namen Umfrage API
    try:
        from api.portal_name_survey_api import portal_name_survey_bp, init_survey_table
        app.register_blueprint(portal_name_survey_bp, url_prefix='')
        # Tabelle initialisieren
        init_survey_table()
        print("✅ Portal-Namen Umfrage API geladen")
    except ImportError as e:
        print(f"⚠️  Portal-Namen Umfrage API nicht gefunden: {e}")
    except Exception as e:
        print(f"⚠️  Fehler beim Laden der Portal-Namen Umfrage API: {e}")
        import traceback
        traceback.print_exc()
    print("✅ Teile-Status API registriert: /api/teile/")
except Exception as e:
    print(f"⚠️  Teile-Status API nicht geladen: {e}")

# Renner & Penner API (TAG 141 - Lagerumschlag-Analyse)
try:
    from api.renner_penner_api import renner_penner_bp
    app.register_blueprint(renner_penner_bp)
    print("✅ Renner & Penner API registriert: /api/lager/")
except Exception as e:
    print(f"⚠️  Renner & Penner API nicht geladen: {e}")

# Organization API (TAG 113 - Organigramm & Vertretungsregeln)
try:
    from api.organization_api import organization_api
    app.register_blueprint(organization_api)
    print("✅ Organization API registriert: /api/organization/")
except Exception as e:
    print(f"⚠️  Organization API nicht geladen: {e}")

# Gudat Werkstattplanung API (TAG98)
try:
    from api.gudat_api import register_gudat_api
    register_gudat_api(app)
    print("✅ Gudat API registriert: /api/gudat/")
except Exception as e:
    print(f"⚠️  Gudat API nicht geladen: {e}")

# Ersatzwagen-Kalender API (TAG 131 - PoC)
try:
    from api.ersatzwagen_api import ersatzwagen_bp
    app.register_blueprint(ersatzwagen_bp)
    print("✅ Ersatzwagen API registriert: /api/ersatzwagen/")
except Exception as e:
    print(f"⚠️  Ersatzwagen API nicht geladen: {e}")

# Budget-Planung API (TAG 143)
try:
    from api.budget_api import budget_bp
    app.register_blueprint(budget_bp)
    print("✅ Budget API registriert: /api/budget/")
except Exception as e:
    print(f"⚠️  Budget API nicht geladen: {e}")

# Unternehmensplan API - 1%-Rendite Dashboard (TAG 157)
try:
    from api.unternehmensplan_api import unternehmensplan_bp
    app.register_blueprint(unternehmensplan_bp)
    print("✅ Unternehmensplan API registriert: /api/unternehmensplan/")
except Exception as e:
    print(f"⚠️  Unternehmensplan API nicht geladen: {e}")

# KST-Ziele API - Kostenstellenbezogene Zielplanung (TAG 161)
try:
    from api.kst_ziele_api import kst_ziele_bp
    app.register_blueprint(kst_ziele_bp)
    print("✅ KST-Ziele API registriert: /api/kst-ziele/")
except Exception as e:
    print(f"⚠️  KST-Ziele API nicht geladen: {e}")

# Ersatzwagen-Kalender Test-UI (TAG 131)
@app.route('/test/ersatzwagen')
@login_required
def test_ersatzwagen_kalender():
    """Ersatzwagen-Kalender PoC - Test-UI"""
    return render_template('test/ersatzwagen_kalender.html')

# DEBUG Route - nur in Development! (TAG 130)
if os.getenv('FLASK_ENV') == 'development' or app.debug:
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
# WERKSTATT MONITOR-ROUTES (ohne Login, Token-Auth)
# Normale Werkstatt-Routes sind in werkstatt_routes.py (TAG 130)
# ========================================

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


# ========================================
# TAG 126: LIVEBOARD MONITOR (ohne Login)
# ========================================

@app.route('/monitor/liveboard')
@app.route('/monitor/liveboard/gantt')
def werkstatt_liveboard_monitor():
    """
    Werkstatt Live-Board - MONITOR VERSION (ohne Login)
    Zugriff über Token-Parameter oder interne IP.

    URLs:
    - /monitor/liveboard?token=XXX&betrieb=deg        (Karten-Ansicht)
    - /monitor/liveboard/gantt?token=XXX&betrieb=deg  (Gantt-Ansicht)
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

    # Gantt oder Karten-Ansicht?
    if request.path.endswith('/gantt'):
        return render_template('aftersales/werkstatt_liveboard_gantt.html')
    else:
        return render_template('aftersales/werkstatt_liveboard.html')


# TAG 116/130: Kapazitätsplanung + Anwesenheit sind jetzt in werkstatt_routes.py
