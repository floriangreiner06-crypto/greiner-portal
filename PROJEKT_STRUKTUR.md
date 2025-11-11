# GREINER PORTAL - PROJEKT-STRUKTUR

**Letzte Aktualisierung:** 11.11.2025 (TAG 29)  
**Status:** Produktiv - 3 EK-Banken integriert, 4 Bugs gefixt

---

## 📋 ÜBERSICHT

Greiner Portal ist ein Controlling & Buchhaltungs-System für Auto Greiner GmbH mit:
- Liquiditäts-Dashboard
- Bankenspiegel (Kontoauszüge)
- Fahrzeugfinanzierungen (3 EK-Banken)
- Verkaufs-Modul (Auftragseingang & Auslieferungen)
- Urlaubsplaner (in Arbeit)
- REST API (21+ Endpoints)

---

## 🗂️ VERZEICHNIS-STRUKTUR

```
/opt/greiner-portal/
│
├── data/
│   ├── greiner_controlling.db          # Haupt-Datenbank (SQLite)
│   │   ├── fahrzeugfinanzierungen      # 194 Fahrzeuge, 5,29 Mio EUR
│   │   ├── sales                       # Verkaufsdaten aus LocoSoft
│   │   ├── employees                   # Mitarbeiter aus LocoSoft
│   │   └── konten, transaktionen       # Bank-Daten
│   └── greiner_portal.db               # Auth-Datenbank
│
├── scripts/
│   ├── imports/                        # Import-Scripts
│   │   ├── import_bank_pdfs.py         # Bank-PDFs → DB
│   │   ├── import_stellantis.py        # Stellantis ZIP → DB
│   │   ├── import_santander_bestand.py # Santander CSV → DB
│   │   └── import_hyundai_finance.py   # Hyundai CSV → DB
│   │
│   ├── analysis/                       # Analyse-Tools
│   │   ├── sync_employees.py           # ⭐ LocoSoft Sync (PostgreSQL → SQLite)
│   │   ├── analyze_employees.py
│   │   └── check_db_status.py
│   │
│   ├── tests/                          # Test-Scripts
│   ├── setup/                          # Setup-Scripts
│   └── maintenance/                    # Wartungs-Scripts
│
├── tools/
│   └── scrapers/                       # Web-Scraper
│       └── hyundai_finance_scraper.py  # Hyundai Portal Scraper
│
├── migrations/
│   └── phase1/                         # DB-Migrationen Phase 1
│       ├── 001_add_kontostand_historie.sql
│       ├── 002_add_kreditlinien.sql
│       ├── 003_add_kategorien.sql
│       ├── 004_add_pdf_imports.sql
│       ├── 005_add_views.sql
│       └── 006_add_santander_support.sql
│
├── config/
│   ├── credentials.json                # Bank-Zugangsdaten (GEHEIM!)
│   ├── .env                            # Umgebungsvariablen
│   ├── ldap_credentials.env            # LDAP-Config
│   └── gunicorn.conf.py                # ⭐ Port 5000 (unified)
│
├── parsers/                            # PDF-Parser
│   ├── hypovereinsbank_parser.py
│   ├── sparkasse_parser.py
│   ├── vrbank_parser.py
│   └── parser_factory.py
│
├── templates/                          # HTML-Templates (Jinja2)
│   ├── base.html                       # ⭐ Navigation (vereinfacht)
│   ├── verkauf_auftragseingang.html    # ⭐ Mit Filtern (Tag/Monat/Standort/Verkäufer)
│   ├── verkauf_auslieferung_detail.html # ⭐ Mit Filtern
│   ├── fahrzeugfinanzierungen.html
│   └── urlaubsplaner_v2.html
│
├── static/                             # CSS/JS/Images
│   ├── css/
│   └── js/
│       ├── verkauf_auftragseingang_detail.js
│       └── verkauf_auslieferung_detail.js
│
├── routes/                             # Flask-Routes
│   ├── bankenspiegel_routes.py
│   ├── verkauf_routes.py               # ⭐ 3 Routes (auftragseingang + 2 detail)
│   └── __init__.py
│
├── api/                                # REST API
│   ├── bankenspiegel_api.py
│   ├── verkauf_api.py                  # ⭐ 7 Endpoints
│   ├── vacation_api.py
│   └── __init__.py
│
└── docs/
    └── sessions/                       # Session-Dokumentation
        └── SESSION_WRAP_UP_TAG29.md    # ⭐ Heute!
```

---

## 🌐 SYSTEM-KONFIGURATION

### NGINX (Port 80)
```
Config: /etc/nginx/sites-available/greiner-portal.conf
Status: ✅ Unified - Alle Routes → Port 5000

location / {
    proxy_pass http://127.0.0.1:5000;  # ⭐ Alles auf Port 5000!
}
```

### Gunicorn (Port 5000)
```
Config: /opt/greiner-portal/config/gunicorn.conf.py
Service: greiner-portal.service

bind = "127.0.0.1:5000"  # ⭐ Unified Port
workers = 9 (CPU-basiert)
```

### Service-Befehle
```bash
sudo systemctl status greiner-portal
sudo systemctl restart greiner-portal
journalctl -u greiner-portal -f
```

---

## 🗄️ DATENBANK-STRUKTUR

### sales (LocoSoft-Sync)
```sql
-- Verkaufsdaten aus LocoSoft PostgreSQL
dealer_vehicle_type     -- N (Neu), T/V (Test/Vorführ), G/D (Gebraucht)
out_sales_contract_date -- Auftragsdatum (Vertrag)
out_invoice_date        -- Rechnungsdatum (Auslieferung)
salesman_number         -- Verkäufer-ID (→ employees.locosoft_id)
make_number             -- 27=Hyundai, 40=Opel
model_description       -- Modellname
out_sale_price          -- Verkaufspreis
out_subsidiary          -- Standort (1=Deggendorf, 2=Landau)
```

### employees (LocoSoft-Sync)
```sql
-- Mitarbeiter aus LocoSoft PostgreSQL
locosoft_id             -- ⭐ Verknüpfung zu sales.salesman_number
first_name
last_name
email
department_id
active
personal_nr
```

**⚠️ WICHTIG:** Einige Verkäufer (2008, 2009, 2010, 2011, 9002) haben Verkäufe aber **keine** Employee-Daten!
**Lösung:** `python3 scripts/analysis/sync_employees.py` ausführen

### fahrzeugfinanzierungen

**Korrekte Spaltennamen:**
```sql
- finanzierungsnummer   (NICHT vertragsnummer!)
- endfaelligkeit        (NICHT vertragsende!)
- finanzierungsstatus   (NICHT status!)
- original_betrag       (NICHT finanzierungsbetrag!)
- aktueller_saldo
- vin
- modell
- vertragsbeginn
- finanzinstitut        (Stellantis/Santander/Hyundai Finance)
- rrdi                  (Kontonummer/Händlercode)
- produktfamilie
- alter_tage
- abbezahlt
```

**Häufige Fehler vermeiden:**
```python
# ❌ FALSCH:
cursor.execute("... vertragsnummer, vertragsende, status, finanzierungsbetrag ...")

# ✅ RICHTIG:
cursor.execute("... finanzierungsnummer, endfaelligkeit, finanzierungsstatus, original_betrag ...")
```

---

## 🏦 NETZLAUFWERK-STRUKTUR

### Mount-Point
```
//srvrdb01/Allgemein → /mnt/buchhaltung
```

### Datei-Pfade

**Fahrzeugfinanzierungen:**
```
/mnt/buchhaltung/Kontoauszüge/Stellantis/       # ZIP-Dateien
/mnt/buchhaltung/Kontoauszüge/Santander/        # CSV: Bestandsliste_*.csv
/mnt/buchhaltung/Kontoauszüge/HyundaiFinance/   # CSV: stockList_*.csv
```

**WICHTIG:** Kein doppeltes "Buchhaltung"!
- ❌ `/mnt/buchhaltung/Buchhaltung/...`
- ✅ `/mnt/buchhaltung/Kontoauszüge/...`

---

## 🔄 LOCOSOFT-SYNC

### Employee-Sync (PostgreSQL → SQLite)
```bash
# Mitarbeiter synchronisieren
python3 scripts/analysis/sync_employees.py

# Status prüfen
python3 scripts/analysis/check_db_status.py

# Verkäufer ohne Namen finden
sqlite3 data/greiner_controlling.db "
SELECT DISTINCT s.salesman_number, e.first_name, e.last_name, COUNT(*) 
FROM sales s 
LEFT JOIN employees e ON s.salesman_number = e.locosoft_id 
GROUP BY s.salesman_number;
"
```

**Verbindung:** LocoSoft PostgreSQL → SQLite
- Quell-DB: LocoSoft (PostgreSQL)
- Ziel-DB: greiner_controlling.db (SQLite)
- Tabellen: employees, sales, departments

---

## 📥 IMPORT-WORKFLOWS

### Stellantis
```bash
cd /opt/greiner-portal
source venv/bin/activate
python3 scripts/imports/import_stellantis.py
```

### Santander
```bash
python3 scripts/imports/import_santander_bestand.py
```

### Hyundai Finance
```bash
# 1. CSV manuell herunterladen (Browser)
#    https://fiona.hyundaifinance.eu
#    Login: Christian.aichinger@auto-greiner.de
#    Einkaufsfinanzierung → Bestandsliste → Download

# 2. CSV ins Netzlaufwerk kopieren
#    \\srvrdb01\Allgemein\Kontoauszüge\HyundaiFinance\

# 3. Import ausführen
python3 scripts/imports/import_hyundai_finance.py

# Dry-Run zum Testen:
python3 scripts/imports/import_hyundai_finance.py --dry-run
```

---

## 🔧 CREDENTIALS

**Pfad:** `/opt/greiner-portal/config/credentials.json`

**Hyundai Finance:**
```json
{
  "hyundai_finance": {
    "portal_url": "https://fiona.hyundaifinance.eu/#/dealer-portal",
    "username": "Christian.aichinger@auto-greiner.de",
    "password": "Hyundaikona2020!",
    "standort": "Auto Greiner"
  }
}
```

---

## 🔌 REST API (21+ Endpoints)

### Verkauf API
```
GET /api/verkauf/auftragseingang           # Dashboard (heute + periode)
GET /api/verkauf/auftragseingang/summary   # ⭐ Zusammenfassung nach Typ
GET /api/verkauf/auftragseingang/detail    # ⭐ Detail nach Verkäufer
GET /api/verkauf/auslieferung/summary      # ⭐ Auslieferungen Summary
GET /api/verkauf/auslieferung/detail       # ⭐ Auslieferungen Detail
GET /api/verkauf/verkaufer                 # ⭐ Verkäufer-Liste
GET /api/verkauf/health

Parameter:
?year=2025
&month=10              # Optional: Monats-Ansicht
&day=2025-10-15        # Optional: Tages-Ansicht
&location=1            # Optional: 1=Deggendorf, 2=Landau
&verkaufer=2003        # Optional: Verkäufer-Nummer
```

### Bankenspiegel API
```
GET /api/bankenspiegel/dashboard
GET /api/bankenspiegel/konten
GET /api/bankenspiegel/transaktionen
GET /api/bankenspiegel/einkaufsfinanzierung
GET /api/bankenspiegel/fahrzeuge-mit-zinsen
GET /api/bankenspiegel/health
```

### Vacation API
```
GET /api/vacation/balance
GET /api/vacation/requests
POST /api/vacation/request
GET /api/vacation/health
```

---

## 📊 AKTUELLE ZAHLEN (11.11.2025)

### Fahrzeugfinanzierungen
```
Stellantis:      107 Fz.  →  3,04 Mio € Saldo
Santander:        41 Fz.  →  0,82 Mio € Saldo
Hyundai Finance:  46 Fz.  →  1,42 Mio € Saldo
────────────────────────────────────────────────
GESAMT:          194 Fz.  →  5,29 Mio € Saldo
```

### Verkaufsdaten (Beispiel Oktober 2025)
```
Auftragseingang:  101 Fahrzeuge (Vertragsdatum)
Auslieferungen:   103 Fahrzeuge (Rechnungsdatum)

Differenz zeigt zeitliche Verzögerung zwischen Auftrag und Auslieferung
```

---

## 🔍 WICHTIGE DB-QUERIES

### Fahrzeugfinanzierungen pro Bank
```sql
SELECT
    finanzinstitut,
    COUNT(*) as anzahl,
    ROUND(SUM(aktueller_saldo), 2) as saldo
FROM fahrzeugfinanzierungen
GROUP BY finanzinstitut;
```

### Verkäufer mit/ohne Namen
```sql
SELECT DISTINCT
    s.salesman_number,
    e.first_name || ' ' || e.last_name as name,
    COUNT(*) as anzahl_verkaufe
FROM sales s
LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
GROUP BY s.salesman_number
ORDER BY s.salesman_number;
```

### Alle Spaltennamen anzeigen
```bash
sqlite3 data/greiner_controlling.db "PRAGMA table_info(fahrzeugfinanzierungen);"
sqlite3 data/greiner_controlling.db "PRAGMA table_info(sales);"
sqlite3 data/greiner_controlling.db "PRAGMA table_info(employees);"
```

---

## ⚠️ HÄUFIGE FEHLER & LÖSUNGEN

### 1. "table has no column named vertragsnummer"
**Lösung:** Richtige Spaltennamen verwenden (siehe oben!)

### 2. "Keine CSV-Datei gefunden"
**Lösung:** Pfad prüfen - KEIN doppeltes "Buchhaltung"!

### 3. Deutsches Dezimalformat
**Lösung:**
```python
def parse_german_decimal(value):
    value = str(value).replace('.', '').replace(',', '.')
    return float(value)
```

### 4. "502 Bad Gateway"
**Ursache:** Port-Mismatch zwischen NGINX und Gunicorn
**Lösung:** 
```bash
# Prüfe welcher Port läuft
sudo ss -tlnp | grep :5000

# Prüfe NGINX Config
grep "proxy_pass" /etc/nginx/sites-available/greiner-portal.conf

# Prüfe Gunicorn Config
grep "bind" config/gunicorn.conf.py

# Beide müssen auf Port 5000 zeigen!
```

### 5. Verkäufer ohne Namen in API
**Ursache:** Employee-Sync nicht vollständig
**Lösung:**
```bash
python3 scripts/analysis/sync_employees.py
```

---

## ✅ GELÖSTE BUGS (TAG 29)

1. ✅ Urlaubsplaner nicht aufrufbar → **GEFIXT** (Port unified 8000→5000)
2. ⏳ API-Placeholder angezeigt → Verschoben (DB-Migration nötig)
3. ✅ Bankenspiegel → Fahrzeugfinanzierungen fehlt → **GEFIXT** (Menü)
4. ✅ Verkauf → Auftragseingang Detail 404 → **GEFIXT** (Route + API)
5. ✅ Verkauf → Auslieferungen Detail 404 → **GEFIXT** (Route + API)

**Details:** Siehe `docs/sessions/SESSION_WRAP_UP_TAG29.md`

---

## 🚀 FÜR NEUE CHAT-SESSIONS

**Kontext bereitstellen:**
```
Hallo Claude! Greiner Portal Projekt.

SERVER: ssh ag-admin@10.80.80.20
PFAD: /opt/greiner-portal
VENV: source venv/bin/activate

BITTE LESEN:
1. /mnt/project/PROJEKT_STRUKTUR.md (diese Datei!)
2. /mnt/project/docs/sessions/SESSION_WRAP_UP_TAG29.md
3. git log --oneline -10

AKTUELLER STAND (TAG 29):
- 3 EK-Banken integriert (194 Fz, 5,29 Mio EUR)
- 4 Bugs gefixt (Urlaubsplaner, Verkauf-Detail-Ansichten)
- Port unified (5000)
- Verkauf-Modul mit erweiterten Filtern
- Branch: feature/bankenspiegel-komplett
```

---

## 🎓 WICHTIGE ERKENNTNISSE

### Port-Konfiguration
- **Immer prüfen:** NGINX + Gunicorn müssen auf **gleichen Port** zeigen!
- **Best Practice:** Port 5000 für alles (unified)

### LocoSoft-Integration
- **sales-Tabelle:** Verkaufsdaten (synced)
- **employees-Tabelle:** Mitarbeiter (synced)
- **Sync-Script:** `scripts/analysis/sync_employees.py`
- **Problem:** Verkäufer können existieren aber ohne Employee-Daten

### Verkauf-Daten
- **Auftragseingang:** Basiert auf `out_sales_contract_date` (Vertrag)
- **Auslieferungen:** Basiert auf `out_invoice_date` (Rechnung)
- **Unterschied:** Zeigt zeitliche Verzögerung

### Filter-System
- **Zeitraum:** Monat ODER Tag
- **Standort:** 1=Deggendorf, 2=Landau, leer=Alle
- **Verkäufer:** Dropdown dynamisch aus DB

---

**Version:** 2.0  
**Erstellt:** 11.11.2025 (TAG 29)  
**Status:** ✅ Produktiv - 4 Bugs gefixt
