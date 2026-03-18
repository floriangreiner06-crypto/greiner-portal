
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
STATIC_VERSION = '20260318120000'  # EZ-Spalte Fahrzeugfinanzierungen-Modal (Cache-Bust)
print(f"📦 Static Version: {STATIC_VERSION}")

# Template-Kontext: Macht STATIC_VERSION in allen Templates verfügbar
@app.context_processor
def inject_version():
    return {'STATIC_VERSION': STATIC_VERSION}


# Template-Funktion: Navigation aus DB laden (TAG 190)
@app.context_processor
def inject_navigation():
    """Lädt Navigation-Items aus DB für aktuellen User
    TAG 190: DB-basierte Navigation mit Feature-Filterung
    
    Aktivierung: USE_DB_NAVIGATION=true in .env oder als Environment-Variable
    """
    try:
        # Prüfe ob DB-Navigation aktiviert ist (Config-Flag)
        # Standard: false (Fallback auf hardcoded Navigation)
        # Prüfe zuerst Environment-Variable, dann .env Dateien
        use_db_navigation = os.getenv('USE_DB_NAVIGATION', 'false').lower() == 'true'
        
        # Falls nicht als Environment-Variable gesetzt, .env Dateien direkt lesen
        if not use_db_navigation:
            # Prüfe config/.env (wird von systemd geladen)
            env_files = [
                os.path.join(os.path.dirname(__file__), 'config', '.env'),
                os.path.join(os.path.dirname(__file__), '.env')
            ]
            for env_file in env_files:
                if os.path.exists(env_file):
                    with open(env_file, 'r') as f:
                        for line in f:
                            if line.strip().startswith('USE_DB_NAVIGATION='):
                                value = line.split('=', 1)[1].strip().lower()
                                use_db_navigation = value == 'true'
                                break
                    if use_db_navigation:
                        break
        
        # TAG 192: Debug-Logging entfernt (Performance)
        
        if not use_db_navigation:
            return {'navigation_items': None}  # Fallback auf hardcoded Navigation
        
        if not current_user.is_authenticated:
            return {'navigation_items': []}
        
        from api.navigation_utils import get_navigation_for_user
        items = get_navigation_for_user()
        # TAG 192: Debug-Logging entfernt (Performance)
        # print(f"🔵 Navigation-Items geladen: {len(items)} Top-Level Items")
        return {'navigation_items': items}
        
    except Exception as e:
        print(f"⚠️ Fehler beim Laden der Navigation: {e}")
        import traceback
        traceback.print_exc()
        return {'navigation_items': None}  # Fallback
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

@app.route('/docs/navigation-visualisierung')
def navigation_visualisierung():
    """Navigation-Verbesserungsvorschlag Visualisierung
    TAG 190: Zeigt aktuelle vs. vorgeschlagene Navigation-Struktur
    """
    from flask import send_from_directory
    import os
    docs_dir = os.path.join(os.path.dirname(__file__), 'docs')
    return send_from_directory(docs_dir, 'NAVIGATION_VISUALISIERUNG_TAG190.html')

@app.route('/logout')
@login_required
def logout():
    """Logout und Session beenden"""
    if auth_manager:
        auth_manager.logout_user(current_user)
    logout_user()
    flash('Sie wurden erfolgreich abgemeldet.', 'info')
    return redirect(url_for('login'))


# Nutzerfreundliche Fehlermeldungen für Passwort-Ändern (keine technischen Begriffe)
PASSWORT_FEHLER_UEBERSETZUNG = {
    'aktuelles_passwort_falsch': 'Das von Ihnen eingegebene aktuelle Passwort stimmt nicht. Bitte prüfen Sie es und versuchen Sie es erneut.',
    'felder_leer': 'Bitte füllen Sie alle Felder aus.',
    'passwort_zu_kurz': 'Das neue Passwort muss mindestens 8 Zeichen haben.',
    'benutzer_nicht_gefunden': 'Ihr Benutzerkonto konnte im Verzeichnis nicht gefunden werden. Bitte wenden Sie sich an die IT.',
    'server_abgelehnt': 'Die Passwortänderung konnte nicht durchgeführt werden. Bitte versuchen Sie es später erneut oder wenden Sie sich an die IT.',
    'richtlinie_oder_verbindung': 'Die Passwortänderung ist an dieser Stelle nicht möglich (z. B. Firmenrichtlinie oder Verbindung). Bitte wenden Sie sich an die IT.',
    'passwortrichtlinie': 'Das neue Passwort erfüllt die Anforderungen nicht (z. B. Länge, Zeichen). Bitte beachten Sie die Passwortrichtlinie Ihres Unternehmens.',
    'verbindung_verzeichnis': 'Die Verbindung zum Verzeichnisdienst ist fehlgeschlagen. Bitte versuchen Sie es später erneut oder wenden Sie sich an die IT.',
    'unerwarteter_fehler': 'Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut oder wenden Sie sich an die IT.',
    'wiederholung_stimmt_nicht': 'Das neue Passwort und die Wiederholung stimmen nicht überein. Bitte geben Sie beide Felder identisch ein.',
    'auth_nicht_verfuegbar': 'Die Anmeldung ist derzeit nicht verfügbar. Bitte versuchen Sie es später erneut oder wenden Sie sich an die IT.',
}


def _passwort_fehler_fuer_anwender(msg_or_key):
    """Übersetzt technische/englische Fehlermeldungen in verständliche deutsche Texte."""
    if not msg_or_key:
        return PASSWORT_FEHLER_UEBERSETZUNG.get('unerwarteter_fehler')
    key = (msg_or_key or '').strip()
    if key in PASSWORT_FEHLER_UEBERSETZUNG:
        return PASSWORT_FEHLER_UEBERSETZUNG[key]
    # Bekannte technische/englische Phrasen abfangen
    lower = key.lower()
    if 'invalid' in lower and ('credential' in lower or 'password' in lower):
        return PASSWORT_FEHLER_UEBERSETZUNG['aktuelles_passwort_falsch']
    if 'unwilling' in lower or 'will_not_perform' in lower:
        return PASSWORT_FEHLER_UEBERSETZUNG['richtlinie_oder_verbindung']
    if 'constraint' in lower or 'policy' in lower:
        return PASSWORT_FEHLER_UEBERSETZUNG['passwortrichtlinie']
    if 'bind' in lower or 'ldap' in lower or 'connection' in lower:
        return PASSWORT_FEHLER_UEBERSETZUNG['verbindung_verzeichnis']
    # Unbekannte Meldung: generisch, technischen Text nicht anzeigen
    return PASSWORT_FEHLER_UEBERSETZUNG['unerwarteter_fehler']


@app.route('/profil/passwort', methods=['GET', 'POST'])
@login_required
def profil_passwort():
    """Self-Service: AD-Passwort ändern. Gilt ab nächster Anmeldung für Windows und Drive."""
    def form_page(error_msg=None, success=False):
        return render_template(
            'profil_passwort.html',
            error=_passwort_fehler_fuer_anwender(error_msg) if error_msg else None,
            show_success=success,
        )

    if request.method == 'POST':
        old = request.form.get('current_password', '')
        new = request.form.get('new_password', '')
        repeat = request.form.get('new_password_repeat', '')
        if new != repeat:
            return form_page(error_msg='wiederholung_stimmt_nicht')
        if not auth_manager:
            return form_page(error_msg='auth_nicht_verfuegbar')
        try:
            success, err = auth_manager.change_password(current_user.username, old, new)
            if success:
                return redirect(url_for('profil_passwort', success=1))
            return form_page(error_msg=err or 'unerwarteter_fehler')
        except Exception as e:
            return form_page(error_msg=str(e))
    # GET: Erfolg von Redirect anzeigen oder Formular
    return form_page(success=(request.args.get('success') == '1'))


# ============================================================================
# MAIN ROUTES
# ============================================================================

@app.route('/health')
def health():
    """Health-Check Endpoint"""
    return jsonify({'status': 'healthy'})

@app.route('/debug/navigation')
@login_required
def debug_navigation():
    """Debug: Zeigt Navigation-Status
    TAG 190: Prüft ob DB-Navigation aktiviert ist
    """
    import os
    use_db_nav = os.getenv('USE_DB_NAVIGATION', 'NOT SET')
    
    # Prüfe config/.env
    env_value = None
    env_file = os.path.join(os.path.dirname(__file__), 'config', '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip().startswith('USE_DB_NAVIGATION='):
                    env_value = line.split('=', 1)[1].strip()
                    break
    
    # Prüfe ob navigation_items geladen werden
    from api.navigation_utils import get_navigation_for_user
    try:
        items = get_navigation_for_user()
        items_count = len(items) if items else 0
    except Exception as e:
        items_count = f"ERROR: {str(e)}"
    
    return jsonify({
        'env_var': use_db_nav,
        'env_file_value': env_value,
        'env_file_path': env_file,
        'navigation_items_count': items_count,
        'current_user': current_user.username if hasattr(current_user, 'username') else 'unknown'
    })

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

# Employee Management API (TAG 213 - Mitarbeiterverwaltung)
try:
    from api.employee_management_api import employee_management_api
    app.register_blueprint(employee_management_api)
    print("✅ Employee Management API registriert: /api/employee-management/")
except Exception as e:
    print(f"⚠️  Employee Management API nicht geladen: {e}")

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
    base = 'base_embed.html' if request.args.get('embed') else 'base.html'
    return render_template('urlaubsplaner_admin.html', base_template=base)

# Mitarbeiterverwaltung (TAG 213 - Umfassende Mitarbeiterverwaltung)
@app.route('/admin/mitarbeiterverwaltung')
@login_required
def mitarbeiterverwaltung():
    """Umfassende Mitarbeiterverwaltung nach Muster 'Digitale Personalakte'"""
    base = 'base_embed.html' if request.args.get('embed') else 'base.html'
    return render_template('admin/mitarbeiterverwaltung.html', base_template=base)

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
from api.profitabilitaet_api import profitabilitaet_api
from api.parts_api import parts_api
from api.admin_api import admin_api
from api.zins_optimierung_api import zins_api
from api.teile_api import teile_api
from api.gewinnplanung_v2_gw_api import gewinnplanung_v2_gw_api
app.register_blueprint(verkauf_api)
app.register_blueprint(profitabilitaet_api)
app.register_blueprint(parts_api)
app.register_blueprint(admin_api)
app.register_blueprint(teile_api)
app.register_blueprint(zins_api)
app.register_blueprint(gewinnplanung_v2_gw_api)
print("✅ Gewinnplanung V2 GW API registriert: /api/gewinnplanung/v2/gw/")
print("✅ Verkauf API registriert: /api/verkauf/")

# Stundensatz-Kalkulation API (TAG 169)
try:
    from api.stundensatz_kalkulation_api import stundensatz_api
    app.register_blueprint(stundensatz_api)
    print("✅ Stundensatz-Kalkulation API registriert: /api/stundensatz/")
except Exception as e:
    print(f"⚠️  Stundensatz-Kalkulation API nicht geladen: {e}")

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
from routes.afa_routes import afa_bp
app.register_blueprint(verkauf_bp)
print("✅ Verkauf Frontend registriert: /verkauf/")

# Provisionsmodul (Phase 1: Live-Preview, SSOT in api/provision_service)
try:
    from api.provision_api import provision_api
    from routes.provision_routes import provision_bp
    app.register_blueprint(provision_api)
    app.register_blueprint(provision_bp)
    print("✅ Provisionsmodul registriert: /api/provision/, /provision/")
except Exception as e:
    print(f"⚠️  Provisionsmodul nicht geladen: {e}")
app.register_blueprint(controlling_bp)
app.register_blueprint(afa_bp)
print("✅ Controlling registriert: /controlling/")

# Werkstatt Frontend Routes (TAG 119)
from routes.werkstatt_routes import werkstatt_routes
app.register_blueprint(werkstatt_routes)
print("✅ Werkstatt Frontend registriert: /werkstatt/")

# WhatsApp Routes (TAG 211)
try:
    from routes.whatsapp_routes import whatsapp_bp
    app.register_blueprint(whatsapp_bp)
    print("✅ WhatsApp Routes registriert: /whatsapp/")
except Exception as e:
    print(f"⚠️  WhatsApp Routes nicht geladen: {e}")

# Controlling API (BWA)
try:
    from api.controlling_api import controlling_api
    app.register_blueprint(controlling_api)
    
    # Finanzreporting API (TAG 178 - Cube-Funktionalität)
    from api.finanzreporting_api import finanzreporting_api
    app.register_blueprint(finanzreporting_api)
    print("✅ Finanzreporting API registriert: /api/finanzreporting/")
    print("✅ Controlling API registriert: /api/controlling/")
    
    # Kontenmapping API (TAG 181)
    from api.kontenmapping_api import kontenmapping_api
    app.register_blueprint(kontenmapping_api)
    print("✅ Kontenmapping API registriert: /api/kontenmapping/")
    # AfA-Modul Vorführwagen/Mietwagen (2026-02-16)
    from api.afa_api import afa_api
    app.register_blueprint(afa_api)
    print("✅ AfA API registriert: /api/afa/")
    # OPOS – Offene Posten (2026-02-19)
    from api.opos_api import opos_api
    app.register_blueprint(opos_api)
    print("✅ OPOS API registriert: /api/controlling/opos")
except Exception as e:
    print(f"⚠️  Controlling API nicht geladen: {e}")

# Marketing Potenzial / Predictive Scoring (2026-02-21)
try:
    from api.marketing_potenzial_api import marketing_potenzial_api
    from routes.marketing_routes import marketing_bp
    app.register_blueprint(marketing_potenzial_api)
    app.register_blueprint(marketing_bp)
    print("✅ Marketing Potenzial API + Frontend: /api/marketing/potenzial/, /marketing/potenzial")
except Exception as e:
    print(f"⚠️  Marketing Potenzial nicht geladen: {e}")

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
    Dynamische Startseite nach Login (TAG122, TAG190)
    
    TAG 190: Prüft zuerst individuelle Dashboard-Konfiguration,
    dann Fallback auf rollenbasierte Weiterleitung.
    
    Leitet basierend auf:
    1. Individuelle Konfiguration (TAG 190) - hat Priorität
    2. portal_role zum passenden Dashboard:
       - serviceberater → Aftersales mit Standort-Filter
       - werkstatt_leitung → Werkstatt Dashboard
       - verkauf/verkauf_leitung → Verkauf Auftragseingang
       - admin/buchhaltung → Allgemeines Dashboard
    """
    # TAG 190: Prüfe individuelle Dashboard-Konfiguration
    try:
        from api.db_connection import get_db
        from api.db_utils import row_to_dict
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT target_url 
            FROM user_dashboard_config 
            WHERE user_id = %s AND target_url IS NOT NULL
        ''', (current_user.id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            config = row_to_dict(row)
            target_url = config.get('target_url')
            if target_url:
                print(f"🔍 [start()] User {current_user.display_name}: Individuelle Konfiguration → {target_url}")
                return redirect(target_url)
    except Exception as e:
        print(f"⚠️ [start()] Fehler beim Laden der Dashboard-Konfiguration: {e}")
        # Fallback auf rollenbasierte Weiterleitung
    
    # Fallback: Rollenbasierte Weiterleitung (bestehende Logik)
    role = getattr(current_user, 'portal_role', 'mitarbeiter')
    standort = getattr(current_user, 'standort', 'deggendorf')

    # Serviceberater → Persönlicher Bereich mit Badges
    # Prüfe sowohl portal_role als auch Serviceberater-Konfiguration (TAG 171)
    is_serviceberater = False
    if role == 'serviceberater':
        is_serviceberater = True
        print(f"🔍 [start()] User {current_user.display_name}: portal_role='serviceberater' → Weiterleitung zu mein_bereich")
    else:
        # Fallback: Prüfe ob User in SERVICEBERATER_CONFIG ist
        from api.serviceberater_api import get_sb_config_from_ldap
        display_name = getattr(current_user, 'display_name', '')
        if display_name:
            sb_config = get_sb_config_from_ldap(display_name)
            if sb_config:
                is_serviceberater = True
                print(f"🔍 [start()] User {display_name}: In SERVICEBERATER_CONFIG gefunden (MA-ID {sb_config.get('ma_id')}) → Weiterleitung zu mein_bereich")
            else:
                print(f"🔍 [start()] User {display_name}: NICHT in SERVICEBERATER_CONFIG → Weiterleitung zu dashboard")
        else:
            print(f"🔍 [start()] User {current_user.username}: Kein display_name → Weiterleitung zu dashboard")
    
    if is_serviceberater:
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
    
    # Prüfe Berechtigung: Wenn ma_id angegeben, muss User admin, controlling oder service_leitung sein
    if ma_id_param:
        if not (current_user.can_access_feature('admin') or current_user.can_access_feature('controlling')
                or current_user.can_access_feature('service_leitung')):
            from flask import abort
            abort(403)
    
    return render_template('sb/mein_bereich.html', 
                         now=datetime.now(),
                         ma_id_param=ma_id_param)


# After Sales Routes
from routes.aftersales import teile_routes
from routes.aftersales import serviceberater_routes
from routes.aftersales import garantie_routes
from routes.admin_routes import admin_routes
app.register_blueprint(teile_routes.bp)
app.register_blueprint(serviceberater_routes.bp)
app.register_blueprint(garantie_routes.bp)
app.register_blueprint(admin_routes)
print("✅ Serviceberater Routes registriert: /aftersales/serviceberater/")
print("✅ Garantie Routes registriert: /aftersales/garantie/")

# QA API & Routes (TAG 192)
# QA-Feature temporär entfernt (TAG 192 - Performance)
# from api.qa_api import qa_api
# from routes.qa_routes import qa_routes
# app.register_blueprint(qa_api)
# app.register_blueprint(qa_routes)
print("✅ QA API registriert: /api/qa/")
print("✅ QA Routes registriert: /qa/")

# Arbeitskarte API (TAG 173)
try:
    from api.arbeitskarte_api import bp as arbeitskarte_bp
    app.register_blueprint(arbeitskarte_bp)
    print("✅ Arbeitskarte API registriert: /api/arbeitskarte/")
except Exception as e:
    print(f"⚠️  Arbeitskarte API nicht geladen: {e}")

# Werkstatt SOAP API (TAG 173 - Stempelzeiten-Verteilung)
try:
    from api.werkstatt_soap_api import bp as werkstatt_soap_bp
    app.register_blueprint(werkstatt_soap_bp)
    print("✅ Werkstatt SOAP API registriert: /api/werkstatt/soap/")
except Exception as e:
    print(f"⚠️  Werkstatt SOAP API nicht geladen: {e}")

# Garantie SOAP API
try:
    from api.garantie_soap_api import bp as garantie_soap_api
    app.register_blueprint(garantie_soap_api)
    print("✅ Garantie SOAP API registriert: /api/garantie/soap/")
except Exception as e:
    print(f"⚠️  Garantie SOAP API nicht geladen: {e}")

# Garantie Aufträge API (TAG 181)
try:
    from api.garantie_auftraege_api import bp as garantie_auftraege_api
    app.register_blueprint(garantie_auftraege_api)
    print("✅ Garantie Aufträge API registriert: /api/garantie/auftraege/")
except Exception as e:
    print(f"⚠️  Garantie Aufträge API nicht geladen: {e}")

# Garantie-Dokumente (Handbücher, Richtlinien, Rundschreiben) – Liste + Upload
try:
    from api.garantie_dokumente_api import bp as garantie_dokumente_api
    app.register_blueprint(garantie_dokumente_api)
    print("✅ Garantie-Dokumente API registriert: /api/garantie/dokumente")
except Exception as e:
    print(f"⚠️  Garantie-Dokumente API nicht geladen: {e}")

# Mobis Teilebezug API (TAG 175 - Über Locosoft SOAP)
try:
    from api.mobis_teilebezug_api import bp as mobis_teilebezug_api
    app.register_blueprint(mobis_teilebezug_api)
    print("✅ Mobis Teilebezug API registriert: /api/mobis/teilebezug/")
except Exception as e:
    print(f"⚠️  Mobis Teilebezug API nicht geladen: {e}")

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

# Unfall-Rechnungsprüfung – Wissensdatenbank (M4)
try:
    from api.unfall_wissensbasis_api import unfall_wissensbasis_api
    app.register_blueprint(unfall_wissensbasis_api)
    print("✅ Unfall-Wissensdatenbank API registriert: /api/unfall/")
except Exception as e:
    print(f"⚠️  Unfall-Wissensdatenbank API nicht geladen: {e}")

try:
    from api.unfall_rechnungspruefung_api import unfall_rechnungspruefung_api
    app.register_blueprint(unfall_rechnungspruefung_api)
    print("✅ Unfall-Rechnungsprüfung API registriert: /api/unfall/auftraege, /auftrag/<nr>/check")
except Exception as e:
    print(f"⚠️  Unfall-Rechnungsprüfung API nicht geladen: {e}")

# Fahrzeuganlage API (Fahrzeugschein-OCR via AWS Bedrock)
try:
    from api.fahrzeuganlage_api import fahrzeuganlage_api
    app.register_blueprint(fahrzeuganlage_api)
    print("✅ Fahrzeuganlage API registriert: /api/fahrzeuganlage/")
except Exception as e:
    print(f"⚠️  Fahrzeuganlage API nicht geladen: {e}")

# Werkstatt LIVE API (Echtzeit-Daten aus Locosoft)
try:
    from api.werkstatt_live_api import werkstatt_live_bp
    app.register_blueprint(werkstatt_live_bp)
    
    # Gudat → Locosoft Sync API (TAG 200 - Test-Integration)
    try:
        from api.gudat_locosoft_sync_api import bp as gudat_locosoft_sync_bp
        app.register_blueprint(gudat_locosoft_sync_bp)
        print("✅ Gudat-Locosoft Sync API registriert: /api/gudat-locosoft/")
    except Exception as e:
        print(f"⚠️  Gudat-Locosoft Sync API nicht geladen: {e}")
    
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
        
        # Gewinnplanungstool V2 (TAG 169)
        from routes.gewinnplanung_v2_routes import gewinnplanung_v2_routes
        app.register_blueprint(gewinnplanung_v2_routes)
        print("✅ Gewinnplanungstool V2 Routes registriert: /planung/v2/")
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
    
    # AI API (LM Studio Integration) - TAG 195
    try:
        from api.ai_api import ai_api
        app.register_blueprint(ai_api)
        print("✅ AI API (LM Studio) registriert")
    except Exception as e:
        print(f"⚠️  AI API konnte nicht geladen werden: {e}")
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

# Verkäufer-Zielplanung API (Kalenderjahr, NW/GW-Verteilung)
try:
    from api.verkaeufer_zielplanung_api import verkaeufer_zielplanung_bp
    app.register_blueprint(verkaeufer_zielplanung_bp)
    print("✅ Verkäufer-Zielplanung API registriert: /api/verkaeufer-zielplanung/")
except Exception as e:
    print(f"⚠️  Verkäufer-Zielplanung API nicht geladen: {e}")

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

# Hilfe-Modul (Workstream Hilfe – 2026-02-24)
try:
    from api.hilfe_api import hilfe_api
    from routes.hilfe_routes import hilfe_bp
    app.register_blueprint(hilfe_api)
    app.register_blueprint(hilfe_bp)
    print("✅ Hilfe-Modul registriert: /api/hilfe/, /hilfe/")
except Exception as e:
    print(f"⚠️  Hilfe-Modul nicht geladen: {e}")

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


# Werkstatt-Monitor-Ansichten (ohne Login) → routes/werkstatt_routes.py
# /monitor/stempeluhr, /werkstatt/stempeluhr/monitor (Stempeluhr)
# /monitor/liveboard, /monitor/liveboard/gantt (Live-Board)
# Daten: /api/werkstatt/live/stempeluhr, /api/werkstatt/live/board
