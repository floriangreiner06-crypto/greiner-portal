# DRIVE Portal - Installationsanleitung für Leo

**Version:** 2.0  
**Datum:** 2026-01-09  
**Ziel:** Installation auf eigenem Server mit eigener Locosoft-Datenbank

---

## 📋 ÜBERSICHT

Diese Anleitung beschreibt die vollständige Installation des DRIVE Portal Systems auf einem neuen Server. Das System ist ein internes Management-Portal für Autohäuser mit Locosoft-Integration.

**Tech-Stack:**
- Flask 3.0 + Gunicorn
- PostgreSQL (Hauptdatenbank)
- PostgreSQL Locosoft (extern, read-only)
- LDAP/Active Directory (optional)
- Celery + Redis (für Background-Tasks)

---

## 🚀 VORAUSSETZUNGEN

### Server-Anforderungen
- **OS:** Linux (Ubuntu 20.04+ oder Debian 11+ empfohlen)
- **RAM:** Minimum 4GB, empfohlen 8GB+
- **Disk:** Minimum 50GB freier Speicher
- **Python:** 3.10 oder höher
- **PostgreSQL:** 13 oder höher

### Externe Dependencies
- **Locosoft PostgreSQL-Datenbank** (read-only Zugriff erforderlich)
- **LDAP/Active Directory** (optional, für Authentifizierung)
- **Redis** (für Celery)

---

## 📦 SCHRITT 1: SYSTEM-VORBEREITUNG

### 1.1 System aktualisieren

```bash
sudo apt update
sudo apt upgrade -y
```

### 1.2 Python 3.10+ installieren

```bash
sudo apt install python3 python3-pip python3-venv -y
python3 --version  # Sollte 3.10+ sein
```

### 1.3 PostgreSQL installieren

```bash
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 1.4 PostgreSQL-Datenbank erstellen

```bash
# Als postgres-User einloggen
sudo -u postgres psql

# In PostgreSQL:
CREATE DATABASE drive_portal;
CREATE USER drive_user WITH PASSWORD 'DEIN_PASSWORT_HIER';
GRANT ALL PRIVILEGES ON DATABASE drive_portal TO drive_user;
\q
```

### 1.5 Redis installieren (für Celery)

```bash
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

---

## 📥 SCHRITT 2: CODE INSTALLIEREN

### 2.1 Projekt-Verzeichnis erstellen

```bash
sudo mkdir -p /opt/greiner-portal
sudo chown $USER:$USER /opt/greiner-portal
cd /opt/greiner-portal
```

### 2.2 Code kopieren

Kopiere alle Dateien aus dem bereitgestellten Code-Paket nach `/opt/greiner-portal/`:

```bash
# Beispiel: Via SCP von lokalem Rechner
scp -r drive-portal-code/* user@dein-server:/opt/greiner-portal/

# Oder: Git-Repository klonen (falls vorhanden)
# git clone <repository-url> /opt/greiner-portal
```

### 2.3 Virtual Environment erstellen

```bash
cd /opt/greiner-portal
python3 -m venv venv
source venv/bin/activate
```

### 2.4 Python-Dependencies installieren

```bash
pip install --upgrade pip
pip install -r requirements.txt

# Zusätzliche Dependencies (falls nicht in requirements.txt):
pip install psycopg2-binary
pip install ldap3
pip install celery[redis]
pip install flower
pip install python-dotenv
pip install gunicorn
```

---

## ⚙️ SCHRITT 3: KONFIGURATION

### 3.1 Datenbank-Migration durchführen

```bash
# PostgreSQL-Schema importieren
cd /opt/greiner-portal
source venv/bin/activate

# Schema-Datei finden und importieren (siehe migrations/)
psql -h localhost -U drive_user -d drive_portal -f migrations/phase1/schema.sql
```

### 3.2 Konfigurationsdateien anpassen

**WICHTIG:** Siehe `CONFIGURATION_CHECKLIST.md` für vollständige Liste aller Anpassungen!

#### 3.2.1 `.env` Datei erstellen

```bash
cd /opt/greiner-portal/config
cp .env.example .env
nano .env
```

**Minimale Konfiguration:**

```env
# Datenbank (DRIVE Portal)
DB_TYPE=postgresql
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=drive_portal
DB_USER=drive_user
DB_PASSWORD=DEIN_PASSWORT_HIER

# Locosoft-Datenbank (extern)
LOCOSOFT_HOST=DEIN_LOCOSOFT_SERVER_IP
LOCOSOFT_PORT=5432
LOCOSOFT_DATABASE=loco_auswertung_db
LOCOSOFT_USER=dein_locosoft_user
LOCOSOFT_PASSWORD=dein_locosoft_passwort

# Flask
SECRET_KEY=generiere-ein-sicheres-secret-key-hier
FLASK_ENV=production

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

#### 3.2.2 LDAP-Konfiguration (falls LDAP verwendet wird)

```bash
cd /opt/greiner-portal/config
cp ldap_credentials.env.example ldap_credentials.env
nano ldap_credentials.env
```

**Beispiel:**

```env
LDAP_SERVER=dein-ad-server.de
LDAP_PORT=389
LDAP_USE_SSL=False
LDAP_BIND_DN=svc_portal@dein-domain.de
LDAP_BIND_PASSWORD=dein-passwort
LDAP_BASE_DN=DC=dein-domain,DC=de
LDAP_VALIDATE_CERT=False
```

#### 3.2.3 `credentials.json` erstellen (für Locosoft)

```bash
cd /opt/greiner-portal/config
nano credentials.json
```

**Beispiel:**

```json
{
  "locosoft_postgresql": {
    "host": "DEIN_LOCOSOFT_SERVER_IP",
    "port": 5432,
    "database": "loco_auswertung_db",
    "user": "dein_locosoft_user",
    "password": "dein_locosoft_passwort"
  }
}
```

### 3.3 Standort-Konfiguration anpassen

**Datei:** `api/standort_utils.py`

Passe die Standort-Mappings an deine Standorte an:

```python
STANDORT_NAMEN = {
    1: 'Dein Standort 1',
    2: 'Dein Standort 2',
    3: 'Dein Standort 3'
}

BETRIEB_NAMEN = {
    1: 'Standort 1',
    2: 'Standort 2',
    3: 'Standort 3'
}

STANDORT_KUERZEL = {
    1: 'S1',
    2: 'S2',
    3: 'S3'
}
```

### 3.4 App-Namen anpassen

**Datei:** `app.py` (Zeile ~100)

```python
'app_name': 'Dein Portal Name',  # Statt 'Greiner Portal'
```

### 3.5 E-Mail-Konfiguration (falls E-Mails versendet werden)

Suche nach `drive@auto-greiner.de` und ersetze mit deiner E-Mail-Adresse.

**Dateien:**
- `celery_app/tasks.py` (Zeile ~332)
- Weitere Dateien siehe `CONFIGURATION_CHECKLIST.md`

---

## 🔧 SCHRITT 4: SYSTEMD-SERVICES EINRICHTEN

### 4.1 Flask/Gunicorn Service

```bash
sudo nano /etc/systemd/system/drive-portal.service
```

**Inhalt:**

```ini
[Unit]
Description=DRIVE Portal Flask Application
After=network.target postgresql.service

[Service]
Type=notify
User=dein-user
Group=dein-group
WorkingDirectory=/opt/greiner-portal
Environment="PATH=/opt/greiner-portal/venv/bin"
ExecStart=/opt/greiner-portal/venv/bin/gunicorn \
    --config /opt/greiner-portal/config/gunicorn.conf.py \
    app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Service aktivieren:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable drive-portal
sudo systemctl start drive-portal
sudo systemctl status drive-portal
```

### 4.2 Celery Worker Service

```bash
sudo nano /etc/systemd/system/celery-worker.service
```

**Inhalt:**

```ini
[Unit]
Description=Celery Worker für DRIVE Portal
After=network.target redis.service

[Service]
Type=forking
User=dein-user
Group=dein-group
WorkingDirectory=/opt/greiner-portal
Environment="PATH=/opt/greiner-portal/venv/bin"
ExecStart=/opt/greiner-portal/venv/bin/celery \
    -A celery_app.celery_config worker \
    --loglevel=info \
    --logfile=/opt/greiner-portal/logs/celery-worker.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Service aktivieren:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-worker
sudo systemctl start celery-worker
sudo systemctl status celery-worker
```

### 4.3 Celery Beat Service (für Scheduled Tasks)

```bash
sudo nano /etc/systemd/system/celery-beat.service
```

**Inhalt:**

```ini
[Unit]
Description=Celery Beat für DRIVE Portal
After=network.target redis.service

[Service]
Type=simple
User=dein-user
Group=dein-group
WorkingDirectory=/opt/greiner-portal
Environment="PATH=/opt/greiner-portal/venv/bin"
ExecStart=/opt/greiner-portal/venv/bin/celery \
    -A celery_app.celery_config beat \
    --loglevel=info \
    --logfile=/opt/greiner-portal/logs/celery-beat.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Service aktivieren:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-beat
sudo systemctl start celery-beat
sudo systemctl status celery-beat
```

---

## 🌐 SCHRITT 5: NGINX KONFIGURATION (Optional)

Falls Nginx als Reverse Proxy verwendet wird:

```bash
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/drive-portal
```

**Inhalt:**

```nginx
server {
    listen 80;
    server_name dein-domain.de;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static Files
    location /static {
        alias /opt/greiner-portal/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Aktivieren:**

```bash
sudo ln -s /etc/nginx/sites-available/drive-portal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## ✅ SCHRITT 6: TESTEN

### 6.1 Datenbank-Verbindung testen

```bash
cd /opt/greiner-portal
source venv/bin/activate
python3 -c "from api.db_connection import test_connection; print(test_connection())"
```

### 6.2 Locosoft-Verbindung testen

```bash
python3 -c "from api.db_utils import get_locosoft_connection; conn = get_locosoft_connection(); print('✅ Locosoft verbunden'); conn.close()"
```

### 6.3 LDAP-Verbindung testen (falls verwendet)

```bash
python3 auth/ldap_connector.py
```

### 6.4 Web-Interface testen

```bash
# Service-Status prüfen
sudo systemctl status drive-portal

# Logs prüfen
journalctl -u drive-portal -f

# Im Browser öffnen:
# http://dein-server-ip:5000
```

---

## 🔍 TROUBLESHOOTING

### Problem: "Module nicht gefunden"

**Lösung:**
```bash
cd /opt/greiner-portal
source venv/bin/activate
pip install -r requirements.txt
```

### Problem: "Datenbank-Verbindung fehlgeschlagen"

**Lösung:**
1. PostgreSQL-Service prüfen: `sudo systemctl status postgresql`
2. Credentials in `.env` prüfen
3. Firewall-Regeln prüfen

### Problem: "Locosoft-Verbindung fehlgeschlagen"

**Lösung:**
1. Locosoft-Server erreichbar? `ping DEIN_LOCOSOFT_SERVER_IP`
2. PostgreSQL-Port offen? `telnet DEIN_LOCOSOFT_SERVER_IP 5432`
3. Credentials in `credentials.json` prüfen

### Problem: "Service startet nicht"

**Lösung:**
```bash
# Logs prüfen
journalctl -u drive-portal -n 50

# Manuell starten zum Debuggen
cd /opt/greiner-portal
source venv/bin/activate
gunicorn --config config/gunicorn.conf.py app:app
```

---

## 📝 NÄCHSTE SCHRITTE

1. ✅ **Konfigurations-Checkliste durchgehen** (`CONFIGURATION_CHECKLIST.md`)
2. ✅ **Ersten Admin-User anlegen** (via LDAP oder manuell)
3. ✅ **Standort-Daten anpassen** (`api/standort_utils.py`)
4. ✅ **Serviceberater konfigurieren** (`api/serviceberater_api.py`)
5. ✅ **Celery-Tasks konfigurieren** (`celery_app/tasks.py`)
6. ✅ **E-Mail-Versand konfigurieren** (falls benötigt)

---

## 📞 SUPPORT

Bei Fragen oder Problemen:
1. Logs prüfen: `/opt/greiner-portal/logs/` und `journalctl -u drive-portal`
2. Konfigurations-Checkliste durchgehen
3. Datenbank-Verbindungen testen

---

## 📄 LIZENZ

Dieser Code wird zur Verfügung gestellt für den internen Gebrauch.  
Alle Rechte vorbehalten.

---

**Stand:** 2026-01-09  
**Version:** 2.0
