# 📋 TODO FÜR CLAUDE SESSION START - TAG 77

**Letzter Stand:** TAG 76 - LDAP Rollen-System implementiert  
**Datum:** 24. November 2025  
**Branch:** `feature/controlling-charts-tag71`

---

## 🎯 HAUPTZIELE TAG 77

### 🏠 FEATURE 1: Dashboard-Kacheln nach Rolle

**Ziel:** Startseite zeigt nur relevante KPI-Widgets basierend auf Portal-Rolle

**Aktuell:** Jeder sieht alle Kacheln (Liquidität, Zinsen, Umsatz, etc.)

**Gewünscht:**
| Rolle | Sieht auf Dashboard |
|-------|---------------------|
| admin | Alle Kacheln |
| verkauf, verkauf_leitung | Auftragseingang, Auslieferungen, Umsatz-KPIs |
| disposition | Fahrzeugbestand, Einkaufsfinanzierung |
| lager | Teilebestellungen-Übersicht |
| werkstatt, service | After Sales KPIs (später) |
| mitarbeiter | Nur persönliche Infos + Urlaubsstand |

**Zu prüfen:**
```bash
# Dashboard Template analysieren
head -100 /opt/greiner-portal/templates/dashboard.html

# Welche Kacheln gibt es?
grep -n "card\|widget\|kpi" /opt/greiner-portal/templates/dashboard.html
```

**Implementierung:**
1. Dashboard-Template mit Jinja2-Checks versehen
2. `{% if current_user.can_access_feature('bankenspiegel') %}` um Finanz-Kacheln
3. Verkaufs-KPIs für Verkauf-Rollen
4. Persönliche Infos für alle

---

### 👥 FEATURE 2: Urlaubsplaner Team-Filter

**Ziel:** Urlaubsplaner zeigt nur Team-relevante Daten

**Anforderungen:**
| Rolle | Sieht im Urlaubsplaner |
|-------|------------------------|
| mitarbeiter | Eigene Anträge + Team-Kalender (readonly) |
| *_leitung | Eigene + Team-Anträge zur Genehmigung |
| admin/HR | Alle Anträge + Genehmigungsrechte |

**Zu prüfen:**
```bash
# Vacation API
grep -n "def get\|def post" /opt/greiner-portal/api/vacation_api.py | head -20

# Employees mit Abteilung
sqlite3 /opt/greiner-portal/data/greiner_controlling.db \
  "SELECT department_name, COUNT(*) FROM employees WHERE active=1 GROUP BY department_name;"
```

**Implementierung:**
1. API: Filter nach `department_name` des eingeloggten Users
2. Genehmigungslogik: Nur Leitungen können genehmigen
3. UI: Genehmigen-Button nur für Berechtigte
4. Team-Zuordnung: Wer gehört zu wem?

**Fragen zu klären:**
- Welche Abteilungen gehören zu welcher Leitung?
- Gibt es eine Manager-Hierarchie in LDAP?

---

## 🔒 FEATURE 3: Route-Protection (Optional)

**Ziel:** Direkter URL-Zugriff auf geschützte Seiten → 403 Forbidden

**Beispiel:**
- Bruno (lager) ruft `/controlling/dashboard` direkt auf → 403
- Florian (admin) ruft `/controlling/dashboard` auf → OK

**Implementierung:**
```python
# In routes/controlling_routes.py
from functools import wraps

def require_feature(feature):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can_access_feature(feature):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/controlling/dashboard')
@login_required
@require_feature('bankenspiegel')
def controlling_dashboard():
    ...
```

---

## 🧹 AUFRÄUMEN

1. **Debug-Route entfernen:**
```bash
# In app.py die Route /debug/user entfernen
grep -n "debug/user" /opt/greiner-portal/app.py
```

2. **Backup-Dateien löschen:**
```bash
rm -f /opt/greiner-portal/templates/*.bak
rm -rf /opt/greiner-portal/templates/_backup/
```

3. **Restliche Änderungen committen:**
```bash
git status
# api/bankenspiegel_api.py
# scripts/imports/import_mt940.py
# static/js/bankenspiegel_konten.js
# templates/fahrzeugfinanzierungen.html
# etc.
```

---

## 📊 AKTUELLER STAND

### Rollen-System (TAG76):
- ✅ LDAP Title → Portal-Rolle
- ✅ Feature-Zugriff-Config
- ✅ Navigation nach Rolle
- ⏳ Dashboard-Kacheln nach Rolle
- ⏳ Route-Protection
- ⏳ Urlaubsplaner Team-Filter

### Abteilungen im System:
```
Werkstatt: 18 MA
Verkauf: 8 MA
Service & Empfang: 8 MA
Lager & Teile: 7 MA
Verwaltung: 6 MA
Disposition: 6 MA
Fahrzeuge: 5 MA
Call-Center: 5 MA
Service: 4 MA
Geschäftsführung: 2 MA
Sonstige: 2 MA
```

---

## 🔧 QUICK-START BEFEHLE
```bash
cd /opt/greiner-portal
git status

# Service Status
systemctl status greiner-portal

# Logs
journalctl -u greiner-portal -f

# Test Rollen-System
curl -s http://localhost:5000/debug/user  # (nach Login im Browser)

# Rollen-Config prüfen
cat config/roles_config.py
```

---

## 📁 RELEVANTE DATEIEN
```
/opt/greiner-portal/
├── config/
│   └── roles_config.py         ← Rollen-Mapping
├── auth/
│   ├── ldap_connector.py       ← Title aus AD
│   └── auth_manager.py         ← User mit Rolle
├── templates/
│   ├── base.html               ← Navigation (done)
│   ├── dashboard.html          ← Kacheln (TODO)
│   └── urlaubsplaner_v2.html   ← Team-Filter (TODO)
├── api/
│   └── vacation_api.py         ← Team-Filter API (TODO)
└── routes/
    └── controlling_routes.py   ← Route-Protection (TODO)
```

---

## ✅ DEFINITION OF DONE - TAG 77

- [ ] Dashboard zeigt Kacheln nach Rolle
- [ ] Verkäufer sieht nur Verkaufs-KPIs
- [ ] Lager sieht nur Teile-Infos
- [ ] Urlaubsplaner: Team-Filter aktiv
- [ ] Leitungen können Team-Urlaub genehmigen
- [ ] Debug-Route entfernt
- [ ] Git committed

---

**Branch:** `feature/controlling-charts-tag71`  
**Fokus:** Dashboard-Personalisierung + Urlaubsplaner Team-Filter
