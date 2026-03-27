# 📖 GREINER PORTAL - AUTH-SYSTEM COMPREHENSIVE GUIDE

**Version:** 2.1.0-auth  
**Datum:** 2025-11-09  
**Status:** ✅ Production-Ready  
**Für:** Entwickler, Admins, neue Team-Mitglieder

---

## 📋 INHALTSVERZEICHNIS

1. [Überblick](#überblick)
2. [Architektur](#architektur)
3. [Installation](#installation)
4. [Konfiguration](#konfiguration)
5. [Verwendung](#verwendung)
6. [Rollen & Permissions](#rollen--permissions)
7. [Entwicklung](#entwicklung)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [API-Referenz](#api-referenz)

---

## 🎯 ÜBERBLICK

### Was ist das Auth-System?

Das Greiner Portal nutzt ein **Active Directory-basiertes Authentication-System** mit:

- ✅ **Single Sign-On (SSO)** - Login mit AD-Credentials
- ✅ **LDAP-Integration** - Anbindung an srvdc01.auto-greiner.de
- ✅ **OU-basierte Rollen** - Automatische Rollen-Zuordnung nach Abteilung
- ✅ **Session-Management** - 8 Stunden Sessions, optional "Remember Me"
- ✅ **User-Cache** - Schnelle Logins durch SQLite-Cache
- ✅ **Audit-Logging** - Alle Login-Events werden protokolliert
- ✅ **Flask-Login Integration** - Standard-Framework für Python-Webapps

### Warum Active Directory?

- ✅ Zentrale User-Verwaltung
- ✅ Keine separaten Passwörter
- ✅ Automatische Synchronisation
- ✅ Bestehende Infrastruktur nutzen
- ✅ Sichere Authentifizierung

### Technologie-Stack

```
Frontend:  HTML5, Bootstrap 5, JavaScript
Backend:   Python 3, Flask, Flask-Login
Auth:      LDAP3 (Active Directory)
Cache:     SQLite3
Server:    Gunicorn (WSGI), Nginx (Reverse Proxy)
OS:        Ubuntu 24.04 LTS
```

---

## 🏗️ ARCHITEKTUR

### Komponenten-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                         BROWSER (Client)                        │
│                    http://10.80.80.20                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP/HTTPS
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      NGINX (Port 80/443)                        │
│                    Reverse Proxy + SSL                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Proxy Pass
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                  GUNICORN (Port 8000)                           │
│              9 Worker Processes (WSGI)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    FLASK APPLICATION                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     app.py (Main)                        │  │
│  │  - Flask-Login Manager                                   │  │
│  │  - Session-Management                                    │  │
│  │  - Route-Registrierung                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              auth/auth_manager.py                        │  │
│  │  - User-Management                                       │  │
│  │  - Rollen-Zuordnung                                      │  │
│  │  - User-Cache (SQLite)                                   │  │
│  │  - Audit-Logging                                         │  │
│  └─────────────────────────┬────────────────────────────────┘  │
│                            │                                    │
│  ┌─────────────────────────▼────────────────────────────────┐  │
│  │          auth/ldap_connector.py                          │  │
│  │  - LDAP-Verbindung                                       │  │
│  │  - User-Authentifizierung                                │  │
│  │  - Gruppen-Abfrage                                       │  │
│  │  - OU-Ermittlung                                         │  │
│  └─────────────────────────┬────────────────────────────────┘  │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             │ LDAP (Port 389)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│               ACTIVE DIRECTORY (srvdc01)                        │
│  - User-Accounts                                                │
│  - OUs (Organizational Units)                                   │
│  - Groups (AD-Gruppen)                                          │
│  - Passwort-Validierung                                         │
└─────────────────────────────────────────────────────────────────┘

                             │
┌────────────────────────────▼────────────────────────────────────┐
│              SQLITE DATABASE (greiner_portal.db)                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  users              - User-Cache                         │  │
│  │  roles              - Rollen-Definitionen                │  │
│  │  user_roles         - User → Rollen Mapping              │  │
│  │  auth_audit_log     - Login-Events                       │  │
│  │  ad_group_role_map  - AD-Gruppe → Rolle Mapping          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Authentifizierungs-Flow

```
1. User öffnet http://10.80.80.20
   └─> Nginx empfängt Request

2. Nginx leitet zu Gunicorn weiter (127.0.0.1:8000)
   └─> Gunicorn Worker nimmt Request an

3. Flask prüft Session
   └─> Kein current_user → Redirect zu /login

4. User gibt Credentials ein:
   - Username: florian.greiner@auto-greiner.de
   - Password: <AD-Passwort>

5. auth_manager.authenticate_user() aufgerufen
   └─> ldap_connector.authenticate_user()
       └─> LDAP-Bind zu srvdc01.auto-greiner.de:389
           ├─> Authentifizierung mit Service-Account
           ├─> User-DN ermitteln
           ├─> User-Bind mit User-Credentials
           ├─> Bei Erfolg: User-Details laden
           │   ├─> displayName
           │   ├─> mail
           │   ├─> memberOf (Gruppen)
           │   └─> OU ermitteln
           └─> User-Objekt zurück

6. auth_manager prüft User:
   ├─> OU-basierte Rollen-Zuordnung
   │   (z.B. "Geschäftsleitung" → "admin")
   ├─> User in DB cachen (INSERT/UPDATE)
   └─> Audit-Log erstellen

7. Flask-Login:
   ├─> login_user(user, remember=True/False)
   ├─> Session erstellen (8h)
   └─> Cookie setzen

8. Redirect zu Startseite
   └─> User ist eingeloggt!
```

### Datenbankschema

```sql
-- User-Cache
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,           -- florian.greiner@auto-greiner.de
    upn TEXT,                                 -- User Principal Name
    display_name TEXT NOT NULL,              -- Florian Greiner
    email TEXT,                               -- florian.greiner@auto-greiner.de
    ad_dn TEXT,                               -- Distinguished Name
    ad_groups TEXT,                           -- JSON: AD-Gruppen
    ou TEXT,                                  -- Organizational Unit
    department TEXT,                          -- Abteilung
    title TEXT,                               -- Position
    is_active BOOLEAN DEFAULT 1,
    is_locked BOOLEAN DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    last_login TIMESTAMP,
    last_ad_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rollen
CREATE TABLE roles (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,               -- admin, buchhaltung, etc.
    display_name TEXT,                        -- "Administrator"
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User-Rollen Mapping
CREATE TABLE user_roles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE(user_id, role_id)
);

-- Audit-Log
CREATE TABLE auth_audit_log (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    username TEXT,
    event_type TEXT NOT NULL,                -- login, logout, failed_login
    success BOOLEAN,
    ip_address TEXT,
    user_agent TEXT,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 💻 INSTALLATION

### Voraussetzungen

```bash
# System:
Ubuntu 24.04 LTS
Python 3.11+
Nginx
SQLite3

# Netzwerk:
Zugriff auf Active Directory (srvdc01.auto-greiner.de:389)
Firewall: Port 80/443 offen (für Nginx)
```

### Schritt 1: Repository klonen

```bash
# Via Git:
cd /opt
git clone <repository-url> greiner-portal
cd greiner-portal

# Oder manuell Dateien hochladen
```

### Schritt 2: Python Virtual Environment

```bash
cd /opt/greiner-portal

# venv erstellen:
python3 -m venv venv

# Aktivieren:
source venv/bin/activate

# Dependencies installieren:
pip install -r requirements.txt
pip install -r requirements_auth.txt

# Sollte installieren:
# - Flask 3.0.0
# - Flask-Login
# - ldap3
# - pdfplumber (für andere Module)
```

### Schritt 3: Datenbank initialisieren

```bash
cd /opt/greiner-portal

# Schema anwenden:
sqlite3 data/greiner_portal.db < migrations/auth/001_auth_system_schema.sql

# Prüfen:
sqlite3 data/greiner_portal.db "SELECT name FROM sqlite_master WHERE type='table';"

# Sollte zeigen:
# users
# roles
# user_roles
# ad_group_role_mapping
# auth_audit_log
```

### Schritt 4: LDAP-Konfiguration

```bash
# Config-Datei erstellen:
nano /opt/greiner-portal/config/ldap_credentials.env

# Inhalt:
LDAP_SERVER=srvdc01.auto-greiner.de
LDAP_PORT=389
LDAP_USE_SSL=false
LDAP_BASE_DN=DC=auto-greiner,DC=de
LDAP_BIND_DN=CN=service_account,OU=ServiceAccounts,DC=auto-greiner,DC=de
LDAP_BIND_PASSWORD=<service-account-passwort>

# Berechtigungen setzen:
chmod 600 /opt/greiner-portal/config/ldap_credentials.env
```

### Schritt 5: Secret Key generieren

```bash
# Secret Key generieren:
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> config/.env

# Berechtigungen:
chmod 600 /opt/greiner-portal/config/.env
```

### Schritt 6: Test-Start

```bash
cd /opt/greiner-portal
source venv/bin/activate

# App starten (Test):
python app.py

# Sollte zeigen:
# ✅ Auth-Manager geladen
# ✅ LDAP Config geladen
# ✅ Secret Key: ✅ Geladen
# * Running on http://0.0.0.0:5000

# Im Browser testen:
# http://<server-ip>:5000

# Mit CTRL+C stoppen
```

### Schritt 7: Systemd Service einrichten

```bash
# Service-Datei erstellen:
sudo nano /etc/systemd/system/greiner-portal.service

# Inhalt:
[Unit]
Description=Greiner Portal Flask Application
After=network.target

[Service]
Type=notify
User=ag-admin
Group=ag-admin
WorkingDirectory=/opt/greiner-portal
Environment="PATH=/opt/greiner-portal/venv/bin"
EnvironmentFile=/opt/greiner-portal/config/.env
ExecStart=/opt/greiner-portal/venv/bin/gunicorn \
    --config /opt/greiner-portal/config/gunicorn.conf.py \
    --chdir /opt/greiner-portal \
    app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Service aktivieren:
sudo systemctl daemon-reload
sudo systemctl enable greiner-portal
sudo systemctl start greiner-portal

# Status prüfen:
sudo systemctl status greiner-portal
```

### Schritt 8: Nginx konfigurieren

```bash
# Nginx Config erstellen:
sudo nano /etc/nginx/sites-available/greiner-portal.conf

# Inhalt:
server {
    listen 80;
    server_name 10.80.80.20;  # Oder Domain

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket Support (falls benötigt):
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Symlink erstellen:
sudo ln -s /etc/nginx/sites-available/greiner-portal.conf /etc/nginx/sites-enabled/

# Nginx testen:
sudo nginx -t

# Nginx neu laden:
sudo systemctl reload nginx
```

### Schritt 9: Firewall konfigurieren

```bash
# UFW (Ubuntu Firewall):
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

### Schritt 10: Erster Test

```bash
# Browser öffnen:
http://10.80.80.20

# Sollte zu /login redirecten

# Login testen:
Username: <dein-username>@auto-greiner.de
Password: <dein-ad-passwort>

# Bei Erfolg: Redirect zur Startseite!
```

---

## ⚙️ KONFIGURATION

### LDAP-Einstellungen

**Datei:** `/opt/greiner-portal/config/ldap_credentials.env`

```bash
# LDAP-Server:
LDAP_SERVER=srvdc01.auto-greiner.de        # AD-Domain-Controller
LDAP_PORT=389                               # 389=LDAP, 636=LDAPS
LDAP_USE_SSL=false                          # true für LDAPS

# Base-DN (Suchbasis):
LDAP_BASE_DN=DC=auto-greiner,DC=de

# Service-Account (für LDAP-Binds):
LDAP_BIND_DN=CN=service_account,OU=ServiceAccounts,DC=auto-greiner,DC=de
LDAP_BIND_PASSWORD=<passwort>

# Optional - Search-Filter:
# LDAP_USER_FILTER=(sAMAccountName={username})
# LDAP_GROUP_FILTER=(member={user_dn})
```

### Flask-Session-Einstellungen

**Datei:** `/opt/greiner-portal/app.py`

```python
# Session-Konfiguration:
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SESSION_COOKIE_SECURE'] = False      # True für HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
```

**Ändern der Session-Dauer:**
```python
# Für 4 Stunden:
timedelta(hours=4)

# Für 12 Stunden:
timedelta(hours=12)

# Für 1 Tag:
timedelta(days=1)
```

### Rollen-Mapping anpassen

**Datei:** `/opt/greiner-portal/auth/auth_manager.py`

```python
# OU → Rollen Mapping:
OU_ROLE_MAPPING = {
    'Geschäftsleitung': {
        'role': 'admin',
        'permissions': {
            'all': True
        },
        'modules': ['*']  # Alle Module
    },
    'Buchhaltung': {
        'role': 'buchhaltung',
        'permissions': {
            'financials': True,
            'reports': True
        },
        'modules': ['bankenspiegel', 'reports']
    },
    'Verkauf': {
        'role': 'verkauf',
        'permissions': {
            'sales': True,
            'customers': True
        },
        'modules': ['verkauf', 'auftragseingang']
    },
    'Werkstatt': {
        'role': 'werkstatt',
        'permissions': {
            'workshop': True,
            'vehicles': True
        },
        'modules': ['werkstatt', 'fahrzeuge']
    },
    'Unknown': {  # Fallback
        'role': 'user',
        'permissions': {
            'basic': True
        },
        'modules': []
    }
}
```

**Neue OU hinzufügen:**
```python
'IT-Abteilung': {
    'role': 'it_admin',
    'permissions': {
        'system': True,
        'all': True
    },
    'modules': ['*']
},
```

### Gunicorn-Einstellungen

**Datei:** `/opt/greiner-portal/config/gunicorn.conf.py`

```python
import multiprocessing

# Server:
bind = "127.0.0.1:8000"               # Nur localhost
backlog = 2048

# Workers (Performance):
workers = multiprocessing.cpu_count() * 2 + 1  # CPU-Cores * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30                          # Request-Timeout
keepalive = 2

# Logging:
accesslog = "/opt/greiner-portal/logs/gunicorn-access.log"
errorlog = "/opt/greiner-portal/logs/gunicorn-error.log"
loglevel = "info"                     # debug, info, warning, error
```

**Worker-Anzahl anpassen:**
```python
# Für Server mit 4 CPU-Cores:
workers = 9  # (4 * 2 + 1)

# Manuell setzen:
workers = 4  # Fixe Anzahl
```

---

## 🎮 VERWENDUNG

### Login

**URL:** `http://10.80.80.20/login`

**Username-Formate (beide funktionieren):**
```
florian.greiner@auto-greiner.de
florian.greiner
```

**Features:**
- ☑️ **Angemeldet bleiben** - Session bleibt 30 Tage
- 🔒 **Sicher mit Active Directory** - Verschlüsselte Übertragung

### Logout

**URL:** `http://10.80.80.20/logout`

**Oder im Code:**
```python
from flask import redirect, url_for
from flask_login import logout_user

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sie wurden erfolgreich abgemeldet.', 'info')
    return redirect(url_for('login'))
```

### User-Informationen abrufen

**In Templates:**
```html
{% if current_user.is_authenticated %}
    <p>Angemeldet als: {{ current_user.display_name }}</p>
    <p>Email: {{ current_user.email }}</p>
    <p>Rollen: {{ current_user.roles|join(', ') }}</p>
    <p>OU: {{ current_user.ou }}</p>
{% endif %}
```

**In Python (Routes):**
```python
from flask_login import current_user

@app.route('/profile')
@login_required
def profile():
    username = current_user.username
    display_name = current_user.display_name
    email = current_user.email
    roles = current_user.roles
    ou = current_user.ou
    
    return render_template('profile.html',
        user=current_user
    )
```

### Zugriff prüfen

**Rolle prüfen:**
```python
if current_user.has_role('admin'):
    # Admin-Features
    pass
```

**Permission prüfen:**
```python
if current_user.has_permission('financials'):
    # Finanz-Daten anzeigen
    pass
```

**Modul-Zugriff prüfen:**
```python
if current_user.can_access_module('bankenspiegel'):
    # Bankenspiegel anzeigen
    pass
```

---

## 🛡️ ROLLEN & PERMISSIONS

### Standard-Rollen

| Rolle | Display-Name | Beschreibung | Zugriff |
|-------|--------------|--------------|---------|
| `admin` | Administrator | Voller Systemzugriff | Alles |
| `geschaeftsleitung` | Geschäftsleitung | Vollzugriff auf alle Module | Alles |
| `buchhaltung` | Buchhaltung | Zugriff auf Finanzen | Bankenspiegel, Reports |
| `verkauf` | Verkauf | Zugriff auf Verkaufsmodule | Verkauf, Auftragseingang |
| `werkstatt` | Werkstatt | Zugriff auf Werkstatt-Module | Werkstatt, Fahrzeuge |
| `user` | Benutzer | Basis-Zugriffsrechte | Dashboard |

### OU → Rollen Mapping

| Organizational Unit | Automatische Rolle |
|---------------------|-------------------|
| Geschäftsleitung | admin |
| Buchhaltung | buchhaltung |
| Verkauf | verkauf |
| Werkstatt | werkstatt |
| Andere | user |

### Neue Rolle erstellen

**1. In Datenbank einfügen:**
```sql
INSERT INTO roles (name, display_name, description) VALUES
    ('it_admin', 'IT-Administrator', 'System-Administration und IT-Support');
```

**2. In auth_manager.py mapping hinzufügen:**
```python
OU_ROLE_MAPPING = {
    # ...
    'IT-Abteilung': {
        'role': 'it_admin',
        'permissions': {
            'system': True,
            'all_modules': True
        },
        'modules': ['*']
    }
}
```

**3. Service neu starten:**
```bash
sudo systemctl restart greiner-portal
```

---

## 👨‍💻 ENTWICKLUNG

### Routes schützen

**Einfacher Login-Schutz:**
```python
from flask_login import login_required

@app.route('/protected')
@login_required
def protected_page():
    return 'Nur für eingeloggte User!'
```

**Rollen-basierter Schutz:**
```python
from decorators.auth_decorators import role_required

@app.route('/admin')
@login_required
@role_required('admin')
def admin_panel():
    return 'Nur für Admins!'

# Mehrere Rollen erlauben:
@app.route('/finance')
@login_required
@role_required(['admin', 'buchhaltung'])
def finance_page():
    return 'Für Admins und Buchhaltung!'
```

**Modul-basierter Schutz:**
```python
from decorators.auth_decorators import module_required

@app.route('/bankenspiegel')
@login_required
@module_required('bankenspiegel')
def bankenspiegel():
    return 'Nur mit Bankenspiegel-Zugriff!'
```

**Permission-basierter Schutz:**
```python
from decorators.auth_decorators import permission_required

@app.route('/financials')
@login_required
@permission_required('financials')
def financials():
    return 'Nur mit financials-Permission!'
```

### Verfügbare Decorators

**Datei:** `/opt/greiner-portal/decorators/auth_decorators.py`

```python
@login_required                  # User muss eingeloggt sein

@role_required('admin')          # User braucht Admin-Rolle
@role_required(['admin', 'user']) # User braucht eine dieser Rollen

@module_required('bankenspiegel') # User braucht Modul-Zugriff

@permission_required('financials') # User braucht Permission

@admin_required                   # Shortcut für Admin-only
```

### Custom User-Attribute

**User-Klasse erweitern:**
```python
# In auth/auth_manager.py:

class User(UserMixin):
    def __init__(self, user_id, username, display_name, 
                 email, ou, roles, permissions):
        self.id = user_id
        self.username = username
        self.display_name = display_name
        self.email = email
        self.ou = ou
        self.roles = roles
        self.permissions = permissions
        
        # Custom Attributes:
        self.is_admin = 'admin' in roles
        self.full_access = self.permissions.get('all', False)
    
    def get_initials(self):
        """Initialen des Users (z.B. FG für Florian Greiner)"""
        parts = self.display_name.split()
        return ''.join([p[0] for p in parts if p])
    
    def get_department_display(self):
        """Abteilungs-Anzeigename"""
        dept_map = {
            'Geschäftsleitung': '🏢 Geschäftsleitung',
            'Buchhaltung': '💰 Buchhaltung',
            'Verkauf': '🚗 Verkauf',
            'Werkstatt': '🔧 Werkstatt'
        }
        return dept_map.get(self.ou, self.ou)
```

### Custom Login-Flow

**Eigene Validierung hinzufügen:**
```python
# In app.py:

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Custom Pre-Check:
    if username in BLOCKED_USERS:
        flash('Account gesperrt. Kontaktieren Sie den Administrator.', 'danger')
        return render_template('login.html')
    
    # Auth-Manager:
    user = auth_manager.authenticate_user(username, password)
    
    if user:
        # Custom Post-Login-Logik:
        log_custom_event(user, 'login_success')
        send_notification(user, 'Neuer Login von ' + request.remote_addr)
        
        login_user(user, remember=remember)
        return redirect(url_for('index'))
    else:
        # Custom Fehler-Handling:
        increment_failed_attempts(username)
        flash('Login fehlgeschlagen.', 'danger')
        return render_template('login.html')
```

### Audit-Log erweitern

**Custom Events loggen:**
```python
# In auth/auth_manager.py:

def log_custom_event(self, user_id, event_type, details):
    """Custom Audit-Log Event"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO auth_audit_log 
        (user_id, event_type, success, details, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, event_type, True, details, datetime.now()))
    
    conn.commit()
    conn.close()

# Verwendung:
auth_manager.log_custom_event(
    current_user.id,
    'export_data',
    'User hat Bankenspiegel-Daten exportiert'
)
```

---

## 🔧 TROUBLESHOOTING

### Problem: Login schlägt fehl

**Symptom:** "Ungültiger Benutzername oder Passwort"

**Diagnose:**
```bash
# 1. LDAP-Connection testen:
cd /opt/greiner-portal
source venv/bin/activate
python auth/ldap_connector.py

# 2. Logs prüfen:
sudo journalctl -u greiner-portal -n 50 | grep -i "error\|ldap"

# 3. Manual-Test mit Python:
python3 << 'EOF'
from auth.ldap_connector import LDAPConnector
ldap = LDAPConnector()
result = ldap.authenticate_user("florian.greiner@auto-greiner.de", "DEIN_PASSWORT")
print(f"Result: {result}")
EOF
```

**Lösungen:**
- ✅ Username-Format prüfen (mit/ohne @auto-greiner.de)
- ✅ Passwort korrekt?
- ✅ LDAP-Server erreichbar? `ping srvdc01.auto-greiner.de`
- ✅ Service-Account-Passwort korrekt in config/ldap_credentials.env?
- ✅ Firewall blockiert Port 389?

---

### Problem: "table users has no column named X"

**Symptom:** Error-Log zeigt fehlende Spalte

**Diagnose:**
```bash
# Spalten prüfen:
sqlite3 /opt/greiner-portal/data/greiner_portal.db "PRAGMA table_info(users);"
```

**Lösung:**
```bash
# Fehlende Spalte hinzufügen:
sqlite3 /opt/greiner-portal/data/greiner_portal.db "ALTER TABLE users ADD COLUMN ou TEXT;"

# Service neu starten:
sudo systemctl restart greiner-portal
```

---

### Problem: Session expired / User wird abgemeldet

**Symptom:** User muss sich immer wieder neu einloggen

**Diagnose:**
```bash
# Session-Config prüfen:
grep -r "PERMANENT_SESSION_LIFETIME" /opt/greiner-portal/app.py
```

**Lösungen:**
- ✅ Session-Dauer erhöhen (siehe Konfiguration)
- ✅ SECRET_KEY konstant? (wechselt nicht bei Restart?)
- ✅ Browser-Cookies aktiviert?
- ✅ "Angemeldet bleiben" Checkbox nutzen

---

### Problem: 502 Bad Gateway

**Symptom:** Nginx zeigt 502-Error

**Diagnose:**
```bash
# 1. Gunicorn läuft?
sudo systemctl status greiner-portal

# 2. Port 8000 offen?
sudo netstat -tulpn | grep 8000

# 3. Nginx-Logs:
sudo tail -f /var/log/nginx/error.log
```

**Lösungen:**
- ✅ Service starten: `sudo systemctl start greiner-portal`
- ✅ Gunicorn-Logs prüfen: `sudo journalctl -u greiner-portal -n 50`
- ✅ Python-Fehler in App? Code-Syntax prüfen
- ✅ Nginx neu laden: `sudo systemctl reload nginx`

---

### Problem: Performance / Langsame Logins

**Symptom:** Login dauert >5 Sekunden

**Diagnose:**
```bash
# Worker-Count prüfen:
ps aux | grep gunicorn | wc -l

# Memory-Usage:
free -h

# LDAP-Response-Time:
time python auth/ldap_connector.py
```

**Lösungen:**
- ✅ Mehr Gunicorn-Worker (config/gunicorn.conf.py)
- ✅ LDAP-Cache nutzen (User-Cache in DB)
- ✅ Server-Hardware upgraden
- ✅ LDAP-Server Performance prüfen

---

### Problem: User hat falsche Rollen

**Symptom:** User kann nicht auf Module zugreifen

**Diagnose:**
```bash
# User in DB prüfen:
sqlite3 /opt/greiner-portal/data/greiner_portal.db \
  "SELECT username, ou, ad_groups FROM users WHERE username LIKE '%florian%';"

# Rollen prüfen:
sqlite3 /opt/greiner-portal/data/greiner_portal.db \
  "SELECT u.username, r.name FROM users u 
   JOIN user_roles ur ON u.id = ur.user_id
   JOIN roles r ON ur.role_id = r.id;"
```

**Lösungen:**
- ✅ OU korrekt ermittelt? (AD → OU → Rolle Mapping prüfen)
- ✅ OU_ROLE_MAPPING in auth_manager.py korrekt?
- ✅ User aus Cache löschen (wird beim nächsten Login neu geladen):
  ```bash
  sqlite3 /opt/greiner-portal/data/greiner_portal.db \
    "DELETE FROM users WHERE username='florian.greiner@auto-greiner.de';"
  ```
- ✅ Service neu starten

---

## 📚 BEST PRACTICES

### Security

**1. LDAPS verwenden (SSL/TLS):**
```bash
# In config/ldap_credentials.env:
LDAP_PORT=636
LDAP_USE_SSL=true
```

**2. Secret Key sicher aufbewahren:**
```bash
# Niemals in Git committen!
# Berechtigungen: 600 (nur Owner lesen)
chmod 600 config/.env
```

**3. Service-Account Permissions minimal halten:**
- Nur LDAP-Lese-Rechte
- Kein Admin-Account nutzen
- Separater Account nur für Portal

**4. HTTPS aktivieren (SSL-Zertifikat):**
```nginx
# Nginx mit Let's Encrypt:
server {
    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/portal.auto-greiner.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/portal.auto-greiner.de/privkey.pem;
    # ...
}
```

**5. Rate-Limiting implementieren:**
```python
# Zu viele fehlgeschlagene Logins → Account sperren
# In auth_manager.py bereits vorbereitet:
# - failed_login_attempts
# - is_locked
```

### Performance

**1. User-Cache nutzen:**
- User wird nach erstem Login in DB gecached
- Nächster Login: Schneller (keine LDAP-Abfrage)
- Auto-Sync alle X Stunden

**2. Gunicorn-Worker optimieren:**
```python
# Faustregel: CPU-Cores * 2 + 1
workers = multiprocessing.cpu_count() * 2 + 1
```

**3. Session-Cookies persistent:**
- "Angemeldet bleiben" nutzen
- Weniger LDAP-Requests

**4. Logging-Level anpassen:**
```python
# Production: info oder warning
loglevel = "info"

# Development: debug
loglevel = "debug"
```

### Monitoring

**1. Logs regelmäßig prüfen:**
```bash
# Täglicher Check:
sudo journalctl -u greiner-portal --since today | grep ERROR

# Failed Logins:
sqlite3 /opt/greiner-portal/data/greiner_portal.db \
  "SELECT COUNT(*) FROM auth_audit_log WHERE success=0 AND timestamp > datetime('now', '-24 hours');"
```

**2. Service-Health überwachen:**
```bash
# Cronjob für Health-Check:
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart greiner-portal
```

**3. Disk-Space überwachen:**
```bash
# Datenbank-Größe:
du -h /opt/greiner-portal/data/greiner_portal.db

# Log-Rotation einrichten (logrotate)
```

### Wartung

**1. Regelmäßige Backups:**
```bash
# Täglich um 2:00 Uhr:
0 2 * * * /usr/bin/sqlite3 /opt/greiner-portal/data/greiner_portal.db ".backup '/opt/backups/greiner_portal_$(date +\%Y\%m\%d).db'"
```

**2. User-Cache aufräumen:**
```bash
# Inaktive User löschen (>90 Tage):
sqlite3 /opt/greiner-portal/data/greiner_portal.db \
  "DELETE FROM users WHERE last_login < datetime('now', '-90 days');"
```

**3. Audit-Log aufräumen:**
```bash
# Alte Logs löschen (>1 Jahr):
sqlite3 /opt/greiner-portal/data/greiner_portal.db \
  "DELETE FROM auth_audit_log WHERE timestamp < datetime('now', '-365 days');"
```

**4. Dependencies aktualisieren:**
```bash
# Virtual Environment:
source venv/bin/activate

# Updates prüfen:
pip list --outdated

# Upgrade:
pip install --upgrade flask flask-login ldap3

# requirements.txt aktualisieren:
pip freeze > requirements.txt
```

---

## 📖 API-REFERENZ

### auth_manager.py

**Klasse:** `AuthManager`

```python
from auth.auth_manager import get_auth_manager

auth_manager = get_auth_manager()
```

**Methoden:**

```python
# User authentifizieren:
user = auth_manager.authenticate_user(username, password)
# Returns: User-Objekt oder None

# User aus DB laden:
user = auth_manager.get_user_by_id(user_id)
# Returns: User-Objekt oder None

# User aus Cache löschen:
auth_manager.logout_user(user)
# Returns: None
```

### ldap_connector.py

**Klasse:** `LDAPConnector`

```python
from auth.ldap_connector import LDAPConnector

ldap = LDAPConnector()
```

**Methoden:**

```python
# User authentifizieren:
user_dict = ldap.authenticate_user(username, password)
# Returns: Dict mit User-Details oder None

# User-Details laden:
details = ldap.get_user_details(user_dn)
# Returns: Dict oder None

# Connection-Test:
success = ldap.test_connection()
# Returns: Boolean
```

### User-Objekt

**Attribute:**
```python
current_user.id              # int: User-ID
current_user.username        # str: florian.greiner@auto-greiner.de
current_user.display_name    # str: Florian Greiner
current_user.email           # str: Email-Adresse
current_user.ou              # str: Organizational Unit
current_user.roles           # list: ['admin', 'buchhaltung']
current_user.permissions     # dict: {'all': True, 'financials': True}
```

**Methoden:**
```python
current_user.get_id()                    # str: User-ID als String
current_user.has_role('admin')           # bool: Hat User diese Rolle?
current_user.has_permission('financials') # bool: Hat User diese Permission?
current_user.can_access_module('bankenspiegel') # bool: Darf User dieses Modul nutzen?
current_user.to_dict()                   # dict: User als Dictionary
```

### Decorators

**Datei:** `decorators/auth_decorators.py`

```python
from decorators.auth_decorators import (
    login_required,      # Bereits von Flask-Login
    role_required,
    module_required,
    permission_required,
    admin_required
)

# Verwendung:
@app.route('/admin')
@login_required
@role_required('admin')
def admin_page():
    return 'Admin only!'
```

---

## 📦 APPENDIX

### Verzeichnisstruktur

```
/opt/greiner-portal/
├── app.py                           # Haupt-App
├── auth/
│   ├── __init__.py
│   ├── auth_manager.py              # User-Management
│   └── ldap_connector.py            # LDAP-Anbindung
├── config/
│   ├── .env                         # SECRET_KEY
│   ├── ldap_credentials.env         # LDAP-Config
│   └── gunicorn.conf.py             # Gunicorn-Config
├── decorators/
│   ├── __init__.py
│   └── auth_decorators.py           # @login_required, etc.
├── data/
│   └── greiner_portal.db            # SQLite-Datenbank
├── migrations/
│   └── auth/
│       └── 001_auth_system_schema.sql
├── logs/
│   ├── gunicorn-access.log
│   └── gunicorn-error.log
├── templates/
│   ├── base.html
│   ├── login.html
│   └── ...
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── docs/
│   ├── QUICK_REFERENCE_AUTH.md
│   └── sessions/
│       └── SESSION_WRAP_UP_TAG21_AUTH_KOMPLETT.md
├── venv/                            # Virtual Environment
├── requirements.txt
└── requirements_auth.txt
```

### Nützliche Commands

```bash
# Service-Management:
sudo systemctl start greiner-portal
sudo systemctl stop greiner-portal
sudo systemctl restart greiner-portal
sudo systemctl status greiner-portal

# Logs:
sudo journalctl -u greiner-portal -f
tail -f /opt/greiner-portal/logs/gunicorn-error.log

# Datenbank:
sqlite3 /opt/greiner-portal/data/greiner_portal.db
sqlite3 ... "SELECT * FROM users;"

# LDAP-Test:
cd /opt/greiner-portal
source venv/bin/activate
python auth/ldap_connector.py

# Hard-Restart:
sudo systemctl stop greiner-portal
sudo pkill -9 -f gunicorn
sleep 3
sudo systemctl start greiner-portal
```

### Support & Kontakt

**Bei Fragen:**
1. Siehe [Troubleshooting](#troubleshooting)
2. Logs prüfen
3. Quick-Reference konsultieren
4. IT-Abteilung kontaktieren

**Dokumentation:**
- `QUICK_REFERENCE_AUTH.md` - Schnell-Referenz
- `SESSION_WRAP_UP_TAG21_AUTH_KOMPLETT.md` - Session-Doku
- Dieser Guide - Comprehensive Guide

---

## 📝 CHANGELOG

### Version 2.1.0-auth (2025-11-09)
- ✅ Initial Release - Auth-System komplett
- ✅ Active Directory Integration
- ✅ Flask-Login
- ✅ OU-basierte Rollen
- ✅ User-Cache
- ✅ Audit-Logging
- ✅ Production-Ready

---

**Version:** 1.0  
**Datum:** 2025-11-09  
**Autor:** Claude AI + Florian Greiner  
**Status:** ✅ Complete

**🎉 VIEL ERFOLG MIT DEM AUTH-SYSTEM! 🎉**
