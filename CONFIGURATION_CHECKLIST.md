# Konfigurations-Checkliste für Leo

**Zweck:** Vollständige Liste aller zu ändernden Werte für die Installation auf eigenem Server

---

## 🔴 KRITISCH - MUSS ANGEPASST WERDEN

### 1. Datenbank-Credentials

**Dateien:**
- `config/.env`
- `scripts/sync/bwa_berechnung.py` (Zeile 44-50)

**Zu ändern:**
- `DB_PASSWORD` → Dein PostgreSQL-Passwort
- `DB_USER` → Dein PostgreSQL-User (kann `drive_user` bleiben)
- `DB_NAME` → Dein Datenbank-Name (kann `drive_portal` bleiben)

---

### 2. Locosoft-Datenbank-Verbindung

**Dateien:**
- `config/credentials.json`
- `config/.env` (LOCOSOFT_* Variablen)
- `api/db_utils.py` (Zeile 100-105 - Fallback-Werte)
- `utils/locosoft_helpers.py` (Zeile 49-54)

**Zu ändern:**
- `LOCOSOFT_HOST` → IP-Adresse deines Locosoft-Servers (statt `10.80.80.8`)
- `LOCOSOFT_USER` → Dein Locosoft-DB-User
- `LOCOSOFT_PASSWORD` → Dein Locosoft-DB-Passwort
- `LOCOSOFT_DATABASE` → Dein Locosoft-DB-Name (kann `loco_auswertung_db` bleiben)

---

### 3. LDAP/Active Directory (falls verwendet)

**Dateien:**
- `config/ldap_credentials.env`
- `auth/ldap_connector.py` (Zeile 139 - Domain-Extraktion)

**Zu ändern:**
- `LDAP_SERVER` → Dein AD-Server (statt `srvdc01.auto-greiner.de`)
- `LDAP_BIND_DN` → Dein Service-Account (statt `svc_portal@auto-greiner.de`)
- `LDAP_BIND_PASSWORD` → Dein Service-Account-Passwort
- `LDAP_BASE_DN` → Deine AD-Base-DN (statt `DC=auto-greiner,DC=de`)

**In `auth/auth_manager.py` (Zeile 212):**
- Domain-Extraktion anpassen (statt `@auto-greiner.de`)

---

### 4. Standort-Konfiguration

**Datei:** `api/standort_utils.py`

**Zu ändern:**
- `STANDORT_NAMEN` (Zeile 51-55) → Deine Standort-Namen
- `BETRIEB_NAMEN` (Zeile 60-64) → Deine Betriebsnamen
- `STANDORT_KUERZEL` (Zeile 67-71) → Deine Standort-Kürzel
- `STANDORTE` Dictionary (Zeile 22-48) → Deine Standort-Struktur

**Beispiel:**
```python
STANDORT_NAMEN = {
    1: 'Hauptstandort',
    2: 'Niederlassung 1',
    3: 'Niederlassung 2'
}
```

---

### 5. App-Namen und Domain

**Dateien:**
- `app.py` (Zeile 100) → `'app_name': 'Dein Portal Name'`
- `app.py` (Zeile 101) → `'app_version': '2.0'` (kann bleiben)

**Templates (optional):**
- `templates/base.html` → Titel anpassen
- `templates/login.html` → Portal-Name anpassen

---

### 6. E-Mail-Konfiguration

**Dateien:**
- `celery_app/tasks.py` (Zeile 332) → `sender_email='deine-email@domain.de'`
- `celery_app/tasks.py` (Zeile 320) → Link anpassen (statt `http://drive.auto-greiner.de/...`)
- `celery_app/tasks.py` (Zeile 324) → Footer-Text anpassen

**Suche nach:** `drive@auto-greiner.de` und `auto-greiner.de`

---

### 7. Serviceberater-Konfiguration

**Datei:** `api/serviceberater_api.py` (Zeile 136-146)

**Zu ändern:**
- `SERVICEBERATER_CONFIG` → Deine Serviceberater-IDs und Namen
- `ldap_cn` → Deine LDAP-CN-Namen (falls LDAP verwendet wird)

**Beispiel:**
```python
SERVICEBERATER_CONFIG = {
    4000: {'name': 'Max Mustermann', 'standort': 'hauptstandort', 'ldap_cn': 'Max Mustermann'},
    4001: {'name': 'Anna Schmidt', 'standort': 'hauptstandort', 'ldap_cn': 'Anna Schmidt'},
}
```

---

### 8. Cognos-Konfiguration (falls verwendet)

**Datei:** `scripts/cognos_soap_client.py` (Zeile 20-24)

**Zu ändern:**
- `COGNOS_BASE_URL` → Dein Cognos-Server (statt `http://10.80.80.10:9300`)
- `LOGIN_USERNAME` → Dein Cognos-User
- `LOGIN_PASSWORD` → Dein Cognos-Passwort
- `REPORT_ID` → Deine Report-ID (falls unterschiedlich)

---

### 9. Pfade (falls Server-Struktur anders)

**Dateien:**
- `api/db_connection.py` (Zeile 185) → `SQLITE_PATH = '/opt/greiner-portal/data/...'`
- `celery_app/tasks.py` → Alle `/opt/greiner-portal/` Pfade prüfen

**Suche nach:** `/opt/greiner-portal/`

---

### 10. Systemd-Services

**Dateien:**
- `/etc/systemd/system/drive-portal.service`
- `/etc/systemd/system/celery-worker.service`
- `/etc/systemd/system/celery-beat.service`

**Zu ändern:**
- `User=` → Dein Linux-User
- `Group=` → Deine Linux-Gruppe
- `WorkingDirectory=` → Falls anderer Pfad

---

## 🟡 OPTIONAL - KANN ANGEPASST WERDEN

### 11. Gunicorn-Konfiguration

**Datei:** `config/gunicorn.conf.py`

**Zu ändern:**
- `bind` → Port ändern (Standard: `127.0.0.1:5000`)
- `workers` → Anzahl Worker anpassen (Standard: 4)

---

### 12. Celery-Konfiguration

**Datei:** `celery_app/celery_config.py`

**Zu ändern:**
- `broker_url` → Falls Redis nicht auf localhost
- `result_backend` → Falls Redis nicht auf localhost

---

### 13. Logging-Konfiguration

**Dateien:**
- Verschiedene Python-Dateien mit `logging.basicConfig()`

**Zu ändern:**
- Log-Level (INFO, DEBUG, WARNING)
- Log-Datei-Pfade

---

### 14. Session-Konfiguration

**Datei:** `app.py` (Zeile 58-61)

**Zu ändern:**
- `SESSION_COOKIE_SECURE` → `True` für HTTPS
- `PERMANENT_SESSION_LIFETIME` → Session-Dauer anpassen

---

## 🔍 SUCHBEFEHLE ZUM FINDEN ALLER HARDCODED WERTE

### Greiner-spezifische Werte finden:

```bash
cd /opt/greiner-portal

# Domain-Namen
grep -r "auto-greiner" --include="*.py" --include="*.html" --include="*.md"

# IP-Adressen
grep -r "10\.80\.80\." --include="*.py"

# Standort-Namen
grep -r "Deggendorf\|Landau" --include="*.py" -i

# E-Mail-Adressen
grep -r "drive@auto-greiner\|@auto-greiner" --include="*.py"

# Serviceberater-Namen
grep -r "Herbert Huber\|Andreas Kraus\|Leonhard Keidl" --include="*.py" -i
```

---

## ✅ CHECKLISTE DURCHGEHEN

- [ ] Datenbank-Credentials angepasst (`.env`, `bwa_berechnung.py`)
- [ ] Locosoft-Verbindung konfiguriert (`credentials.json`, `.env`, `db_utils.py`)
- [ ] LDAP-Konfiguration angepasst (`ldap_credentials.env`, `auth_manager.py`)
- [ ] Standort-Konfiguration angepasst (`standort_utils.py`)
- [ ] App-Namen geändert (`app.py`)
- [ ] E-Mail-Adressen angepasst (`celery_app/tasks.py`)
- [ ] Serviceberater konfiguriert (`serviceberater_api.py`)
- [ ] Cognos-Konfiguration angepasst (falls verwendet)
- [ ] Systemd-Services konfiguriert
- [ ] Alle Greiner-spezifischen Werte ersetzt
- [ ] Datenbank-Migration durchgeführt
- [ ] Services gestartet und getestet

---

## 📝 NOTIZEN

**Wichtige Dateien für Konfiguration:**
- `config/.env` - Hauptkonfiguration
- `config/credentials.json` - Externe Credentials
- `config/ldap_credentials.env` - LDAP-Credentials
- `api/standort_utils.py` - Standort-Mappings
- `app.py` - App-Namen und Session-Konfiguration

**Dateien mit vielen Hardcodierungen:**
- `celery_app/tasks.py` - E-Mails, Pfade, Serviceberater
- `api/serviceberater_api.py` - Serviceberater-Namen
- `scripts/cognos_soap_client.py` - Cognos-Server
- `api/db_utils.py` - Locosoft-Fallback-Werte

---

**Stand:** 2026-01-09  
**Version:** 1.0
