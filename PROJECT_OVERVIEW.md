# 🏢 GREINER PORTAL - KOMPLETTES PROJEKT-OVERVIEW

**Letztes Update:** 2025-11-12  
**Version:** TAG 33  
**Stack:** Flask + SQLite + PostgreSQL (Locosoft) + LDAP + Grafana

---

## 🎯 PROJEKT-ÜBERBLICK

**Greiner Portal** ist ein integriertes ERP-System für ein Autohaus mit folgenden Hauptmodulen:

1. **Bankenspiegel** - Finanz-Controlling
2. **Verkauf** - Auftragseingang & Auslieferungen
3. **Urlaubsplaner V2** - HR-Management
4. **Fahrzeugfinanzierungen** - Zins-Tracking
5. **Auth-System** - LDAP-Integration

---

## 🏗️ ARCHITEKTUR-ÜBERSICHT

```
┌─────────────────────────────────────────────────────────────┐
│                     GREINER PORTAL                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Frontend   │  │   Flask App  │  │   API Layer  │     │
│  │  (Jinja2)    │→ │   (app.py)   │→ │  (3 Modules) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                   │                 │            │
│         └───────────────────┴─────────────────┘            │
│                             ↓                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Datenbanken                         │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ SQLite (lokal)      PostgreSQL (Locosoft extern)    │  │
│  │ - controlling.db    - Mitarbeiter, Verkauf          │  │
│  │ - Transaktionen     - Zeiterfassung                 │  │
│  │ - Konten            - Fahrzeuge                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                             ↓                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Externe Systeme                         │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ LDAP (AD)           Stellantis API                  │  │
│  │ Hyundai Finance     Grafana (Dashboards)           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 PROJEKT-STRUKTUR

```
/opt/greiner-portal/
├── app.py                     ← Haupt-Flask-App
├── config/
│   ├── credentials.json       ← Credentials (LDAP, DB, APIs)
│   └── gunicorn.conf.py       ← Gunicorn-Konfiguration
├── api/                       ← API-Layer (REST APIs)
│   ├── bankenspiegel_api.py   ← Controlling-API
│   ├── verkauf_api.py         ← Verkaufs-API
│   └── vacation_api.py        ← Urlaubsplaner-API
├── routes/                    ← Flask-Routes (HTML-Views)
│   ├── bankenspiegel_routes.py
│   └── verkauf_routes.py
├── auth/                      ← Authentication-System
│   ├── auth_manager.py        ← Session-Management
│   └── ldap_connector.py      ← LDAP/AD-Integration
├── decorators/
│   └── auth_decorators.py     ← @require_auth, @require_role
├── parsers/                   ← PDF-Parser für Bankauszüge
│   ├── base_parser.py
│   ├── sparkasse_parser.py
│   ├── hypovereinsbank_parser.py
│   └── vrbank_parser.py
├── templates/                 ← Jinja2-Templates
│   ├── base.html              ← Master-Template
│   ├── bankenspiegel*.html    ← Controlling-Views
│   ├── verkauf*.html          ← Verkaufs-Views
│   └── urlaubsplaner_v2.html  ← Urlaubsplaner
├── static/                    ← CSS, JS, Images
│   ├── css/
│   ├── js/
│   └── lib/                   ← jQuery, Bootstrap, etc.
├── data/
│   ├── greiner_controlling.db ← SQLite-DB (Hauptdatenbank)
│   └── kontoauszuege/         ← PDF-Imports
├── scripts/
│   ├── imports/               ← Import-Scripts
│   ├── analysis/              ← Analyse-Scripts
│   └── maintenance/           ← Wartungs-Scripts
├── docs/                      ← Dokumentation
├── migrations/                ← DB-Migrations
└── logs/                      ← Log-Files
```

---

## 🔌 API-ENDPOINTS

### **1. Bankenspiegel-API** (`/api/bankenspiegel/...`)

```python
GET /api/bankenspiegel/dashboard
    → Controlling-Dashboard-Daten (Salden, KPIs)

GET /api/bankenspiegel/konten
    → Liste aller Konten mit aktuellen Salden

GET /api/bankenspiegel/transaktionen
    → Transaktionen mit Filter (konto_id, datum_von, datum_bis)

GET /api/bankenspiegel/einkaufsfinanzierung
    → Finanzierungen im Einkauf

GET /api/bankenspiegel/fahrzeuge-mit-zinsen
    → Fahrzeuge mit Zinsberechnungen

GET /api/bankenspiegel/health
    → Health-Check
```

### **2. Verkauf-API** (`/api/verkauf/...`)

```python
GET /api/verkauf/auftragseingang
    → Auftragseingang-Übersicht

GET /api/verkauf/auftragseingang/summary
    → Aggregierte Summary (Anzahl, Summen)

GET /api/verkauf/auftragseingang/detail
    → Detail-Ansicht mit Filtern

GET /api/verkauf/auslieferung/summary
    → Auslieferungs-Summary

GET /api/verkauf/auslieferung/detail
    → Auslieferungs-Details

GET /api/verkauf/verkaufer
    → Liste aller Verkäufer

GET /api/verkauf/health
    → Health-Check
```

### **3. Urlaubsplaner-API** (`/api/vacation/...`)

```python
GET /api/vacation/my-balance
    → Eigenes Urlaubs-Guthaben

GET /api/vacation/my-team
    → Team-Übersicht (für Manager)

GET /api/vacation/balance?employee_id=X
    → Guthaben eines Mitarbeiters

GET /api/vacation/my-bookings
    → Eigene Urlaubs-Buchungen

POST /api/vacation/book
    → Neuen Urlaub buchen

GET /api/vacation/health
    → Health-Check
```

---

## 🎨 FRONTEND-STRUKTUR

### **Base-Template** (`templates/base.html`)
- Master-Layout mit Navigation
- Bootstrap 4
- jQuery, Chart.js
- Responsive Design

### **Hauptseiten:**

| Seite | Template | Beschreibung |
|-------|----------|--------------|
| Dashboard | `dashboard.html` | Hauptübersicht |
| Bankenspiegel | `bankenspiegel_dashboard.html` | Finanz-Dashboard |
| Konten | `bankenspiegel_konten.html` | Konten-Übersicht |
| Transaktionen | `bankenspiegel_transaktionen.html` | Transaktions-Liste |
| Auftragseingang | `verkauf_auftragseingang.html` | Verkaufs-Übersicht |
| Auslieferungen | `verkauf_auslieferung_detail.html` | Auslieferungs-Details |
| Urlaubsplaner | `urlaubsplaner_v2.html` | Urlaubs-Management |
| Fahrzeugfinanzierungen | `fahrzeugfinanzierungen.html` | Finanzierungs-Übersicht |
| Einkaufsfinanzierung | `einkaufsfinanzierung.html` | Einkaufs-Finanzierung |
| Login | `login.html` | Login-Seite |

---

## 🔐 AUTH-SYSTEM

### **Architektur:**
```
LDAP/AD (Active Directory)
    ↓
ldap_connector.py
    ↓
auth_manager.py (Session-Management)
    ↓
auth_decorators.py (@require_auth, @require_role)
    ↓
Flask-Routes (geschützt)
```

### **Features:**
- ✅ LDAP/AD-Integration
- ✅ Session-Management (Flask-Session)
- ✅ Role-Based Access Control (RBAC)
- ✅ Gruppen-Mapping (AD-Groups → Portal-Rollen)
- ✅ Employee-Sync (LDAP → SQLite)

### **Rollen:**
```python
- admin          → Volle Rechte
- finance        → Bankenspiegel-Zugriff
- sales          → Verkaufs-Zugriff
- hr             → Urlaubsplaner-Zugriff
- manager        → Team-Management
- employee       → Standard-Zugriff
```

### **Credentials:** (`config/credentials.json`)
```json
{
  "ldap": {
    "server": "ldap://...",
    "base_dn": "DC=...",
    "bind_user": "...",
    "bind_password": "..."
  },
  "locosoft": {
    "host": "...",
    "database": "...",
    "user": "...",
    "password": "..."
  }
}
```

---

## 🗄️ DATENBANKEN

### **1. SQLite - Hauptdatenbank** (`data/greiner_controlling.db`)

**Controlling/Finanzen:**
- `konten` - Bankkonten
- `banken` - Bankinstitute
- `transaktionen` - Kontobewegungen
- `daily_balances` - Tägliche Salden
- `kategorien` - Transaktions-Kategorien
- `kreditlinien` - Kreditlinien

**Verkauf:**
- `sales` - Verkaufs-Transaktionen
- `vehicles` - Fahrzeuge
- `dealer_vehicles` - Händler-Fahrzeuge
- `customers_suppliers` - Kunden/Lieferanten

**Finanzierung:**
- `fahrzeugfinanzierungen` - Fahrzeug-Finanzierungen
- `zinssaetze_historie` - Zinssätze
- `fahrzeuge_mit_zinsen` - Fahrzeuge mit Zinsen

**Urlaubsverwaltung:**
- `employees` - Mitarbeiter
- `departments` - Abteilungen
- `vacation_entitlements` - Urlaubsansprüche
- `vacation_bookings` - Urlaubs-Buchungen
- `vacation_types` - Urlaubsarten
- `holidays` - Feiertage

**Auth/User:**
- `users` - Benutzer
- `roles` - Rollen
- `user_roles` - User-Rollen-Zuordnung
- `sessions` - User-Sessions
- `audit_log` - Audit-Log

**Siehe auch:** `docs/DATABASE_SCHEMA.md` für Details!

---

### **2. PostgreSQL - Locosoft (Extern)**

**Connection:**
- Host: [in credentials.json]
- Database: Locosoft-DB
- Tables: `mitarbeiter`, `zeiterfassung`, `verkauf`, etc.

**Sync-Scripts:**
- `sync_employees.py` → Mitarbeiter-Sync
- `sync_sales.py` → Verkaufs-Daten-Sync

---

## 🔧 EXTERNE SYSTEME

### **1. LDAP/Active Directory**
- **Zweck:** Benutzer-Authentifizierung
- **Connector:** `auth/ldap_connector.py`
- **Sync:** Mitarbeiter-Daten aus AD

### **2. Locosoft (PostgreSQL)**
- **Zweck:** Zeiterfassung, HR-Daten, Verkauf
- **Sync:** Regelmäßiger Daten-Import
- **Scripts:** `sync_employees.py`, `sync_sales.py`

### **3. Stellantis API**
- **Zweck:** Fahrzeug-Bestandsdaten
- **Scripts:** `import_stellantis.py`
- **Templates:** `stellantis_bestand.html`

### **4. Hyundai Finance**
- **Zweck:** Finanzierungs-Daten
- **Scraper:** `tools/scrapers/hyundai_finance_tester.py`
- **Auth:** Credentials in `config/credentials.json`

### **5. Grafana**
- **Zweck:** Visualisierung & Dashboards
- **Port:** 3000
- **Integration:** SQLite-Datenquelle

---

## 📦 WICHTIGE FEATURES

### **1. Bankenspiegel (Controlling)**
- Dashboard mit KPIs
- Konten-Übersicht
- Transaktions-Liste mit Filter
- PDF-Import (Kontoauszüge)
- Kategorisierung
- Einkaufsfinanzierung
- Fahrzeuge mit Zinsen

### **2. Verkauf**
- Auftragseingang-Tracking
- Auslieferungs-Tracking
- Deckungsbeitrags-Berechnung
- Verkäufer-Performance
- Filter nach Datum, Verkäufer, Marke

### **3. Urlaubsplaner V2**
- Urlaubsanträge
- Genehmigungsprozess
- Team-Übersicht (für Manager)
- Urlaubsguthaben
- Feiertage
- Audit-Log

### **4. Fahrzeugfinanzierungen**
- Zinssatz-Tracking
- Finanzierungs-Übersicht
- Zins-Historie

### **5. Auth & Rollen**
- LDAP-Login
- Role-Based Access Control
- Session-Management
- Audit-Logging

---

## ⚙️ KONFIGURATION

### **Ports:**
```
5000  → Flask-App (Gunicorn)
3000  → Grafana
5432  → PostgreSQL (Locosoft, extern)
```

### **Environment:**
```bash
FLASK_ENV=production
FLASK_APP=app.py
SECRET_KEY=[in credentials.json]
```

### **Gunicorn:** (`config/gunicorn.conf.py`)
```python
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
timeout = 120
```

---

## 🚀 DEPLOYMENT

### **Server:**
```
Host:     10.80.80.20 (auto-greiner.de)
User:     ag-admin
Path:     /opt/greiner-portal/
Venv:     /opt/greiner-portal/venv
```

### **Service:**
```bash
# Status
systemctl status greiner-portal

# Neu starten
systemctl restart greiner-portal

# Logs
journalctl -u greiner-portal -f
```

### **Apache Reverse Proxy:**
```apache
ProxyPass / http://localhost:5000/
ProxyPassReverse / http://localhost:5000/
```

---

## 🔄 ENTWICKLUNGS-WORKFLOW

### **Git-Branches:**
```
main                              ← Produktiv
├── develop                       ← Integration
    ├── feature/controlling-dashboard
    └── feature/verkauf-dashboard
```

### **Neues Feature entwickeln:**
```bash
git checkout develop
git pull
git checkout -b feature/mein-feature-tag34

# Entwickeln...

git commit -m "feat: Beschreibung"
git checkout develop
git merge feature/mein-feature-tag34
git push
```

---

## 📝 WICHTIGE SCRIPTS

### **Imports:**
```bash
# PDFs importieren
scripts/imports/import_bank_pdfs.py

# Stellantis-Bestand
import_stellantis.py

# Locosoft-Sync
sync_employees.py
sync_sales.py
```

### **Maintenance:**
```bash
# Status-Update
update_project_status.py

# DB-Check
check_db_status.py

# Duplikate prüfen
check_verkauf_duplikate.py
```

---

## 🎯 FÜR CLAUDE - QUICK REFERENCE

### **Bei Backend-Entwicklung:**
1. API-Endpoint in `api/*.py` hinzufügen
2. Route in `routes/*.py` (falls HTML-View)
3. Auth-Decorator: `@require_auth` oder `@require_role('admin')`
4. DB-Schema in `docs/DATABASE_SCHEMA.md` prüfen

### **Bei Frontend-Entwicklung:**
1. Template in `templates/` erstellen
2. Von `base.html` erben
3. Static-Files in `static/css/` oder `static/js/`
4. Route in `routes/*.py` registrieren

### **Bei DB-Änderungen:**
1. Migration in `migrations/` erstellen
2. `DATABASE_SCHEMA.md` aktualisieren
3. Testen!
4. `update_project_status.py` ausführen

### **Bei Auth-Änderungen:**
1. `auth/` Module ändern
2. Decorator in `decorators/auth_decorators.py`
3. Credentials in `config/credentials.json`
4. LDAP-Mapping prüfen

---

## 🚨 WICHTIGE DATEIEN FÜR NEUE SESSIONS

**Immer lesen:**
1. `_README_FOR_CLAUDE.md` - Quick-Start
2. `DATABASE_SCHEMA.md` - DB-Struktur
3. `PROJECT_OVERVIEW.md` - Dieses Dokument!
4. `PROJECT_STATUS.md` - Aktueller Stand
5. `SESSION_WRAP_UP_TAG*.md` - Letzte Session

---

## 🎉 ZUSAMMENFASSUNG

**Greiner Portal ist ein:**
- ✅ Multi-Feature ERP-System
- ✅ Flask-basierte Web-App
- ✅ LDAP-integriert
- ✅ Locosoft-synchronisiert
- ✅ PDF-Import-fähig
- ✅ Role-Based Access Control
- ✅ REST-API + HTML-Views
- ✅ Grafana-visualisiert

**Haupt-Features:**
1. Bankenspiegel (Controlling)
2. Verkauf (Auftragseingang, Auslieferungen)
3. Urlaubsplaner V2
4. Fahrzeugfinanzierungen
5. Auth & Rollen

**Tech-Stack:**
- Flask 3.x
- SQLite + PostgreSQL
- Jinja2 Templates
- Bootstrap 4 + jQuery
- LDAP/AD
- Grafana
- Gunicorn + Apache
