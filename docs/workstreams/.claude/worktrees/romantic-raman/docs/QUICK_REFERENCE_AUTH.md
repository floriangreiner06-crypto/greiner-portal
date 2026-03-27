# 🚀 QUICK REFERENCE - AUTH-SYSTEM

**Stand:** 2025-11-09  
**Version:** 2.1.0-auth  
**Status:** ✅ Production-Ready

---

## 📍 WICHTIGE URLS

```
Production:    http://10.80.80.20
Login:         http://10.80.80.20/login
Logout:        http://10.80.80.20/logout

Bankenspiegel: http://10.80.80.20/bankenspiegel/dashboard
Verkauf:       http://10.80.80.20/verkauf/auftragseingang
Urlaubsplaner: http://10.80.80.20/urlaubsplaner/v2
```

---

## 🔐 LOGIN

**Username-Formate (beide funktionieren):**
- `florian.greiner@auto-greiner.de`
- `florian.greiner`

**Password:** Dein AD-Passwort

**Session:** 8 Stunden (mit "Angemeldet bleiben": 30 Tage)

---

## 🛠️ SERVICE-MANAGEMENT

### Status prüfen:
```bash
sudo systemctl status greiner-portal
sudo systemctl status nginx
```

### Service starten/stoppen:
```bash
sudo systemctl start greiner-portal
sudo systemctl stop greiner-portal
sudo systemctl restart greiner-portal
```

### Service neu laden (nach Code-Änderungen):
```bash
sudo systemctl restart greiner-portal
```

### Hard-Restart (bei Problemen):
```bash
sudo systemctl stop greiner-portal
sudo pkill -9 -f gunicorn
sleep 3
sudo systemctl start greiner-portal
```

---

## 📊 LOGS

### Live-Logs ansehen:
```bash
# Systemd Journal (empfohlen):
sudo journalctl -u greiner-portal -f

# Gunicorn Access-Log:
tail -f /opt/greiner-portal/logs/gunicorn-access.log

# Gunicorn Error-Log:
tail -f /opt/greiner-portal/logs/gunicorn-error.log

# Nginx Access-Log:
sudo tail -f /var/log/nginx/access.log
```

### Letzte Fehler anzeigen:
```bash
sudo journalctl -u greiner-portal --since "10 minutes ago" | grep ERROR
```

### Login-Events:
```bash
sudo journalctl -u greiner-portal | grep "Login erfolgreich"
```

---

## 🗄️ DATENBANK

### User-Liste anzeigen:
```bash
sqlite3 /opt/greiner-portal/data/greiner_portal.db \
  "SELECT id, username, display_name, ou, last_login FROM users;"
```

### Aktive Sessions:
```bash
sqlite3 /opt/greiner-portal/data/greiner_portal.db \
  "SELECT username, last_login FROM users WHERE is_active=1;"
```

### Login-History (Audit-Log):
```bash
sqlite3 /opt/greiner-portal/data/greiner_portal.db \
  "SELECT timestamp, username, event_type, success, ip_address 
   FROM auth_audit_log 
   ORDER BY timestamp DESC 
   LIMIT 10;"
```

### User-Rollen anzeigen:
```bash
sqlite3 /opt/greiner-portal/data/greiner_portal.db \
  "SELECT username, display_name, ou, ad_groups FROM users;"
```

---

## 🔧 TROUBLESHOOTING

### Problem: Login schlägt fehl

**1. Check LDAP:**
```bash
cd /opt/greiner-portal
source venv/bin/activate
python auth/ldap_connector.py
```

**2. Check Logs:**
```bash
sudo journalctl -u greiner-portal -n 50 | grep -i "error\|ldap"
```

**3. Check DB-Schema:**
```bash
sqlite3 data/greiner_portal.db "PRAGMA table_info(users);" | grep -E "ou|ad_groups"
```

---

### Problem: Service startet nicht

**1. Check Config:**
```bash
sudo systemctl status greiner-portal
```

**2. Check Syntax:**
```bash
cd /opt/greiner-portal
source venv/bin/activate
python -m py_compile app.py
```

**3. Manual Start (Debug):**
```bash
cd /opt/greiner-portal
source venv/bin/activate
python app.py
```

---

### Problem: Änderungen werden nicht übernommen

**1. Hard-Restart:**
```bash
sudo systemctl stop greiner-portal
sudo pkill -9 -f gunicorn
sleep 3
sudo systemctl start greiner-portal
```

**2. Check ob Prozesse tot sind:**
```bash
ps aux | grep gunicorn
```

---

### Problem: 502 Bad Gateway

**1. Check Gunicorn:**
```bash
sudo systemctl status greiner-portal
```

**2. Check Port:**
```bash
sudo netstat -tulpn | grep 8000
```

**3. Check Nginx Config:**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 📁 WICHTIGE DATEIEN

```
/opt/greiner-portal/
├── app.py                               ← Flask-App mit Auth
├── auth/
│   ├── auth_manager.py                  ← User-Management
│   └── ldap_connector.py                ← AD-Anbindung
├── config/
│   ├── .env                             ← SECRET_KEY
│   ├── ldap_credentials.env             ← LDAP-Config
│   └── gunicorn.conf.py                 ← Gunicorn-Config
├── data/
│   └── greiner_portal.db                ← User-Datenbank
├── migrations/auth/
│   └── 001_auth_system_schema.sql       ← DB-Schema
└── logs/
    ├── gunicorn-access.log
    └── gunicorn-error.log

/etc/systemd/system/
└── greiner-portal.service               ← Systemd-Service

/etc/nginx/sites-enabled/
└── greiner-portal.conf                  ← Nginx-Config
```

---

## 🔑 WICHTIGE ENVIRONMENT-VARIABLEN

**In `/opt/greiner-portal/config/.env`:**
```bash
SECRET_KEY=<generierter-key>
```

**In `/opt/greiner-portal/config/ldap_credentials.env`:**
```bash
LDAP_SERVER=srvdc01.auto-greiner.de
LDAP_PORT=389
LDAP_USE_SSL=false
LDAP_BASE_DN=DC=auto-greiner,DC=de
LDAP_BIND_DN=CN=service_account,OU=...
LDAP_BIND_PASSWORD=<password>
```

---

## 👥 ROLLEN-SYSTEM

### OU → Rollen Mapping:

| OU | Rolle | Berechtigung |
|----|-------|--------------|
| Geschäftsleitung | admin | Alles |
| Buchhaltung | buchhaltung | Finanzen, Bankenspiegel |
| Verkauf | verkauf | Verkaufsmodule |
| Werkstatt | werkstatt | Werkstatt-Module |
| Andere | user | Basis-Rechte |

### Verfügbare Decorators:

```python
from flask_login import login_required
from decorators.auth_decorators import role_required, module_required

@app.route('/admin')
@login_required
@role_required('admin')
def admin_panel():
    pass

@app.route('/bankenspiegel')
@login_required
@module_required('bankenspiegel')
def bankenspiegel():
    pass
```

---

## 📦 BACKUP & RESTORE

### Backup erstellen:
```bash
# Datenbank:
cp /opt/greiner-portal/data/greiner_portal.db \
   /opt/greiner-portal/backups/greiner_portal_$(date +%Y%m%d_%H%M%S).db

# Komplettes Verzeichnis:
tar -czf /tmp/greiner-portal-backup-$(date +%Y%m%d).tar.gz \
  /opt/greiner-portal \
  --exclude=venv \
  --exclude=__pycache__
```

### Restore:
```bash
# Service stoppen:
sudo systemctl stop greiner-portal

# Datenbank zurückspielen:
cp /opt/greiner-portal/backups/greiner_portal_YYYYMMDD.db \
   /opt/greiner-portal/data/greiner_portal.db

# Service starten:
sudo systemctl start greiner-portal
```

---

## 🔄 CODE-DEPLOYMENT

### Nach Code-Änderungen:

```bash
# 1. Backup:
cp app.py app.py.backup_$(date +%Y%m%d_%H%M%S)

# 2. Code ändern:
nano app.py

# 3. Syntax-Check:
cd /opt/greiner-portal
source venv/bin/activate
python -m py_compile app.py

# 4. Service neu starten:
sudo systemctl restart greiner-portal

# 5. Logs prüfen:
sudo journalctl -u greiner-portal -f
```

---

## 📊 MONITORING

### Service-Health:
```bash
# Check ob Service läuft:
systemctl is-active greiner-portal

# Check ob Port offen:
curl -I http://localhost:8000

# Check Gunicorn Workers:
ps aux | grep gunicorn | grep -v grep | wc -l
```

### Performance:
```bash
# Worker-Count:
ps aux | grep gunicorn | wc -l

# Memory-Usage:
ps aux | grep gunicorn | awk '{sum+=$6} END {print sum/1024 " MB"}'

# CPU-Usage:
top -b -n 1 | grep gunicorn
```

---

## 🚨 NOTFALL-KOMMANDOS

### Alles killen und neu starten:
```bash
sudo systemctl stop greiner-portal
sudo systemctl stop nginx
sudo pkill -9 -f gunicorn
sudo pkill -9 -f python
sleep 5
sudo systemctl start greiner-portal
sudo systemctl start nginx
```

### Datenbank neu erstellen (VORSICHT!):
```bash
# BACKUP ERSTELLEN!
cp data/greiner_portal.db data/greiner_portal.db.emergency_backup

# Schema neu anwenden:
sqlite3 data/greiner_portal.db < migrations/auth/001_auth_system_schema.sql
```

### Service komplett neu installieren:
```bash
# Siehe: INSTALLATION_ANLEITUNG.md
```

---

## 📞 SUPPORT

### Bei Problemen:

1. **Logs checken:** `sudo journalctl -u greiner-portal -n 100`
2. **Service Status:** `sudo systemctl status greiner-portal`
3. **LDAP testen:** `python auth/ldap_connector.py`
4. **DB prüfen:** `sqlite3 data/greiner_portal.db`
5. **Hard-Restart:** Siehe oben

### Häufige Fehler:

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| 502 Bad Gateway | Gunicorn läuft nicht | `systemctl start greiner-portal` |
| Login failed | LDAP-Problem | LDAP-Config prüfen |
| Port in use | Alte Prozesse | `pkill gunicorn` |
| Column not found | DB-Schema | Schema neu anwenden |

---

## 🎓 WEITERFÜHRENDE DOCS

- `SESSION_WRAP_UP_TAG21_AUTH_KOMPLETT.md` - Komplette Session-Doku
- `INSTALLATION_ANLEITUNG.md` - Installation & Setup
- `README.md` - Projekt-Übersicht
- Auth-Dateien in `/opt/greiner-portal/auth/`

---

## ✅ QUICK HEALTH-CHECK

```bash
# Alles-Check in einem Command:
{
  echo "=== SERVICE STATUS ==="
  systemctl is-active greiner-portal
  
  echo -e "\n=== WORKERS ==="
  ps aux | grep gunicorn | grep -v grep | wc -l
  
  echo -e "\n=== LAST ERROR ==="
  sudo journalctl -u greiner-portal -n 1 | grep ERROR || echo "No errors!"
  
  echo -e "\n=== ACTIVE USERS ==="
  sqlite3 /opt/greiner-portal/data/greiner_portal.db \
    "SELECT COUNT(*) FROM users WHERE is_active=1;"
  
  echo -e "\n=== PORT CHECK ==="
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 || echo "Not responding"
}
```

**Erwartetes Ergebnis:**
```
SERVICE STATUS: active
WORKERS: 9
LAST ERROR: No errors!
ACTIVE USERS: 1
PORT CHECK: 200
```

---

**Version:** 1.0  
**Erstellt:** 2025-11-09  
**Zuletzt aktualisiert:** 2025-11-09

**Bei Fragen:** Siehe SESSION_WRAP_UP oder Claude fragen! 😊
