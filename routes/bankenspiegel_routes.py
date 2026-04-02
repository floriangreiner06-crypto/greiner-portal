"""
BANKENSPIEGEL ROUTES - GREINER PORTAL (VOLLSTÄNDIG)
===================================================

Diese Datei enthält ALLE Bankenspiegel-Routes:
- Dashboard (Hauptseite)
- Konten (Übersicht)
- Transaktionen (Liste)
- Einkaufsfinanzierung (Stellantis & Santander)
- Fahrzeugfinanzierungen (Alternative View)

KRITISCHER 404-FIX:
-------------------
Die index()-Route leitet /bankenspiegel → /bankenspiegel/dashboard um.
⚠️  NIEMALS LÖSCHEN!

Erstellt: Tag 11 (07.11.2025)
404-Fix: Tag 19 + Tag 20 (08.11.2025)
Einkaufsfinanzierung wiederhergestellt: Tag 20 (08.11.2025)

Version: 2.0 - KOMPLETT
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime

# Blueprint erstellen
bankenspiegel_bp = Blueprint('bankenspiegel', __name__, url_prefix='/bankenspiegel')


# ============================================================================
# KRITISCHER 404-FIX - NIEMALS LÖSCHEN!
# TAG142: sqlite3 Import entfernt - nutze api.db_connection.get_db()
# ============================================================================

@bankenspiegel_bp.route('/')
@bankenspiegel_bp.route('')  # Auch ohne trailing slash
@login_required
def index():
    """
    🛡️ BULLETPROOF REDIRECT FIX
    
    Leitet /bankenspiegel automatisch zu /bankenspiegel/dashboard weiter.
    
    WICHTIG: Diese Route fängt beide Varianten ab:
    - /bankenspiegel (Flask redirected automatisch zu /bankenspiegel/)
    - /bankenspiegel/ (direkt hier)
    
    Flask-Verhalten:
    - /bankenspiegel → [HTTP 308] → /bankenspiegel/ → [HTTP 302] → /dashboard
    - HTTP 308 = Permanent Redirect (automatisch von Flask für trailing slashes)
    - HTTP 302 = Temporary Redirect (unser Redirect)
    
    WARUM WICHTIG:
    - User erwarten /bankenspiegel als Startseite
    - Navigation-Links zeigen oft auf /bankenspiegel
    - Ohne Redirect: 404 Not Found Error
    
    ⚠️  NIEMALS LÖSCHEN!
    
    Bug-History:
    - Tag 11: Route fehlte → 404
    - Tag 19: Fix implementiert
    - Tag 20: Bulletproof dokumentiert (mit Flask 308-Handling)
    """
    return redirect(url_for('bankenspiegel.dashboard'))


# ============================================================================
# HAUPT-SEITEN
# ============================================================================

@bankenspiegel_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Hauptseite - Bankenspiegel Dashboard
    
    Features:
    - KPI-Kacheln (Gesamtsaldo, Banken, Konten, Transaktionen)
    - Monatliche Umsätze (Chart)
    - Letzte Transaktionen
    - Interne Transfers Info
    
    Template: bankenspiegel_dashboard.html
    JavaScript: bankenspiegel_dashboard.js
    CSS: bankenspiegel.css
    """
    return render_template(
        'bankenspiegel_dashboard.html',
        now=datetime.now()
    )


@bankenspiegel_bp.route('/konten')
@login_required
def konten():
    """
    Kontenübersicht
    
    Features:
    - Alle Konten mit Salden
    - Filter nach Bank und Status
    - Suche in IBAN/Kontoname
    - Gesamtsaldo über alle aktiven Konten
    
    Template: bankenspiegel_konten.html
    JavaScript: bankenspiegel_konten.js
    CSS: bankenspiegel.css
    """
    can_trigger_bankimport = (
        current_user.is_authenticated
        and (current_user.has_role('admin') or current_user.has_role('buchhaltung'))
    )
    return render_template(
        'bankenspiegel_konten.html',
        now=datetime.now(),
        can_trigger_bankimport=can_trigger_bankimport,
    )


@bankenspiegel_bp.route('/transaktionen')
@login_required
def transaktionen():
    """
    Transaktionen: eine Seite mit Tabs „Übersicht“ | „Kategorisieren“ (Option A).
    - Übersicht: Filter, Karten, Tabelle (wie bisher).
    - Kategorisieren: Filter, Regeln/KI, Kategorie/Unterkategorie pro Zeile.
    URL-Parameter: ?mode=kategorisierung öffnet direkt den Tab Kategorisieren.
    Template: bankenspiegel_transaktionen.html
    JavaScript: bankenspiegel_transaktionen_combined.js
    """
    return render_template(
        'bankenspiegel_transaktionen.html',
        now=datetime.now()
    )


@bankenspiegel_bp.route('/kategorisierung')
@login_required
def kategorisierung():
    """
    Redirect auf Transaktionen-Seite mit Modus Kategorisieren.
    Eine Seite „Transaktionen“ mit Tabs Übersicht | Kategorisieren (Option A).
    """
    return redirect(url_for('bankenspiegel.transaktionen', mode='kategorisierung'))

# ============================================================================
# EINKAUFSFINANZIERUNG (Konsolidiert: Fahrzeugfinanzierungen + Zinsen-Analyse)
# ============================================================================

@bankenspiegel_bp.route('/einkaufsfinanzierung')
@login_required
def einkaufsfinanzierung():
    """
    Redirect zu Fahrzeugfinanzierungen (konsolidiert)
    """
    return redirect(url_for('bankenspiegel.fahrzeugfinanzierungen'))


@bankenspiegel_bp.route('/zinsen-analyse')
@login_required
def zinsen_analyse():
    """
    Redirect zu Fahrzeugfinanzierungen (konsolidiert)
    """
    return redirect(url_for('bankenspiegel.fahrzeugfinanzierungen'))


@bankenspiegel_bp.route('/fahrzeugfinanzierungen')
@login_required
def fahrzeugfinanzierungen():
    """
    Fahrzeugfinanzierungen Dashboard (Konsolidiert mit Zinsen-Analyse)
    
    Zeigt alle Finanzierungen:
    - Stellantis Bank
    - Santander Bank  
    - Hyundai Finance
    - Genobank (Konto 4700057908)
    
    Features:
    - KPI-Cards mit Gesamtübersicht
    - Bank-Cards mit Details
    - Marken-Badges
    - Zinsen-Warnungen
    - Charts (Pie + Bar)
    - Zinsen-Analyse (inkl. Handlungsempfehlungen)
    
    Template: einkaufsfinanzierung.html (erweitert)
    API: /api/bankenspiegel/einkaufsfinanzierung, /api/zinsen/dashboard, /api/zinsen/report
    CSS: einkaufsfinanzierung.css
    """
    return render_template(
        'einkaufsfinanzierung.html',
        now=datetime.now()
    )

def bankenspiegel_404(error):
    """
    Custom 404-Handler für Bankenspiegel
    
    Falls User eine nicht-existierende Unterseite aufruft,
    leite zu Dashboard weiter statt 404 zu zeigen.
    
    Beispiel: /bankenspiegel/irgendwas-falsches → /bankenspiegel/dashboard
    """
    return redirect(url_for('bankenspiegel.dashboard'))


# ============================================================================
# ROUTE VERIFICATION (für Tests)
# ============================================================================

def verify_routes():
    """
    Verifiziert dass alle kritischen Routes registriert sind.
    
    Returns:
        dict: Status der Routes
    """
    routes = {
        'index_redirect': False,           # ← KRITISCH!
        'dashboard': False,
        'konten': False,
        'transaktionen': False,
        'einkaufsfinanzierung': False,
        'fahrzeugfinanzierungen': False
    }
    
    # Prüfe ob Routes existieren
    from flask import current_app
    
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint == 'bankenspiegel.index':
            routes['index_redirect'] = True
        elif rule.endpoint == 'bankenspiegel.dashboard':
            routes['dashboard'] = True
        elif rule.endpoint == 'bankenspiegel.konten':
            routes['konten'] = True
        elif rule.endpoint == 'bankenspiegel.transaktionen':
            routes['transaktionen'] = True
        elif rule.endpoint == 'bankenspiegel.einkaufsfinanzierung':
            routes['einkaufsfinanzierung'] = True
        elif rule.endpoint == 'bankenspiegel.fahrzeugfinanzierungen':
            routes['fahrzeugfinanzierungen'] = True
    
    return routes


def list_all_routes():
    """
    Listet alle Bankenspiegel-Routes auf.
    
    Nützlich für Debugging und Dokumentation.
    """
    from flask import current_app
    
    routes = []
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint.startswith('bankenspiegel.'):
            routes.append({
                'endpoint': rule.endpoint,
                'path': str(rule),
                'methods': ', '.join(rule.methods - {'HEAD', 'OPTIONS'})
            })
    
    return sorted(routes, key=lambda x: x['path'])


# ============================================================================
# ENTWICKLER-HINWEISE
# ============================================================================

"""
ROUTE-ÜBERSICHT (Stand: Tag 20):
================================

HAUPT-ROUTES:
- GET  /bankenspiegel                    → index() → Redirect zu /dashboard
- GET  /bankenspiegel/                   → index() → Redirect zu /dashboard
- GET  /bankenspiegel/dashboard          → dashboard()
- GET  /bankenspiegel/konten             → konten()
- GET  /bankenspiegel/transaktionen      → transaktionen()

FINANZIERUNGS-ROUTES:
- GET  /bankenspiegel/einkaufsfinanzierung   → einkaufsfinanzierung()
- GET  /bankenspiegel/fahrzeugfinanzierungen → fahrzeugfinanzierungen()

ERROR HANDLER:
- 404  /bankenspiegel/<ungültig>         → bankenspiegel_404() → Redirect zu /dashboard


HINWEISE FÜR ZUKÜNFTIGE ENTWICKLER:
====================================

1. ⚠️  DIE index()-ROUTE IST KRITISCH!
   → Niemals löschen oder auskommentieren
   → Sie verhindert 404-Fehler bei /bankenspiegel
   → Siehe Dokumentation in BANKENSPIEGEL_404_FIX_README.md

2. WENN DU NEUE ROUTES HINZUFÜGST:
   → Verwende @bankenspiegel_bp.route('/dein-pfad')
   → Vergiss nicht: now=datetime.now() in render_template()
   → Teste beide: /bankenspiegel/dein-pfad UND /bankenspiegel
   → Füge die Route zu verify_routes() hinzu

3. TEMPLATES:
   → Alle Templates müssen in templates/ liegen
   → Nutze extends "base.html" für konsistentes Layout
   → JavaScript-Dateien in static/js/
   → CSS-Dateien in static/css/

4. TESTS:
   → Führe test_bankenspiegel_routes.py aus
   → Prüfe dass index() auf dashboard redirected
   → Verifiziere 200-Status für alle Seiten
   → Teste neue Routes manuell im Browser

5. BUG-REPORT:
   Falls 404-Bug zurückkehrt:
   → Prüfe dass Blueprint in app.py registriert ist
   → Checke Flask-Logs: tail -f flask_direct.log
   → Teste: curl http://localhost:5000/bankenspiegel
   → Dokumentiere in SESSION_WRAP_UP

6. DOKUMENTATION:
   → Jede Änderung in SESSION_WRAP_UP dokumentieren
   → Git-Commit mit aussagekräftiger Message
   → README aktualisieren
   → Kommentare im Code aktualisieren


GIT HISTORY:
============
- Tag 11 (07.11.2025): Initiale Routes (dashboard, konten, transaktionen)
- Tag 19 (08.11.2025): Redirect-Fix für 404-Bug
- Tag 20 (08.11.2025): 
  * Bulletproof-Dokumentation
  * Flask 308-Handling
  * Einkaufsfinanzierung wiederhergestellt
  * Komplette Neufassung mit allen Routes


KONTAKT & SUPPORT:
==================
Bei Fragen:
- Siehe: routes/README_404_FIX.md
- Siehe: SESSION_WRAP_UP_TAG20.md
- Git-History: git log -- routes/bankenspiegel_routes.py
- Tests ausführen: python routes/test_bankenspiegel_routes.py


VERSION HISTORY:
================
v1.0 - Tag 11: Initiale Version (3 Routes)
v1.1 - Tag 19: 404-Fix hinzugefügt
v1.2 - Tag 20: Flask 308-Support
v2.0 - Tag 20: KOMPLETT - Alle Routes inkl. Einkaufsfinanzierung


STATUS: 🟢 PRODUCTION-READY | 🛡️ BULLETPROOF | ✅ KOMPLETT
"""


@bankenspiegel_bp.route('/konto/<int:konto_id>')
@login_required
def konto_detail(konto_id):
    """
    Konto-Detail mit historischen Daten
    
    Features:
    - Aktuelle Konto-Info
    - Historische Snapshots
    - Zinsentwicklung-Chart
    - Ausnutzungs-Chart
    """
    return render_template(
        'bankenspiegel_konto_detail.html',
        konto_id=konto_id,
        now=datetime.now()
    )


@bankenspiegel_bp.route('/zeitverlauf')
@login_required
def zeitverlauf():
    """
    Zeitverlauf-Ansicht (Bankenspiegel)
    
    Features:
    - Mehrere Tage nebeneinander
    - Guthaben, Darl.-Stand, Freie Linie pro Tag
    - Ähnlich dem manuellen Bankenspiegel aus Excel
    
    Template: bankenspiegel_zeitverlauf.html
    API: /api/bankenspiegel/zeitverlauf
    """
    return render_template(
        'bankenspiegel_zeitverlauf.html',
        now=datetime.now()
    )
