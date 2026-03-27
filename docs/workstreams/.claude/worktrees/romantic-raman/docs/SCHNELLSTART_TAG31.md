# 🚀 GREINER PORTAL - KOMPLETT-ÜBERSICHT FÜR NEUE CHAT-SESSION
## Stand: 11.11.2025 (Ende Tag 30)

**Zweck:** Schneller Einstieg für Claude in neuer Chat-Session  
**Letzter Stand:** Verkaufs-Deduplizierung fertig, Deckungsbeitrag in Planung

---

## 📋 QUICK START - LIES ZUERST

### 1. Server-Zugang
```bash
ssh ag-admin@10.80.80.20
Password: OHL.greiner2025

cd /opt/greiner-portal
source venv/bin/activate
```

### 2. Wichtigste Dateien im Projekt-Ordner
```
/mnt/project/
├── SESSION_WRAP_UP_TAG30.md          ← LIES ZUERST! Letzte Session
├── PROJEKT_STRUKTUR_TAG29.md          ← System-Überblick
├── VERZEICHNISSTRUKTUR.md             ← Dateistruktur
├── QUICK_REFERENCE_SERVER.md          ← Befehle & Paths
└── INDEX.md                           ← Alle Dokus
```

### 3. Aktuelle Git-Commits prüfen
```bash
git log --oneline -10
git status
```

---

## 🏗️ SYSTEM-ARCHITEKTUR

### Tech-Stack
```
Frontend:  HTML/CSS/JS (Bootstrap 5, jQuery)
Backend:   Python Flask 3.0
Database:  SQLite (greiner_controlling.db)
Server:    Ubuntu 24, NGINX, Gunicorn
Auth:      LDAP (Active Directory)
```

### Port-Konfiguration (WICHTIG!)
```
NGINX:     Port 80 → proxy_pass http://127.0.0.1:5000
Gunicorn:  Port 5000 (9 workers)

⚠️ Alles muss auf Port 5000 zeigen! (Unified seit Tag 29)
```

### Verzeichnis-Struktur
```
/opt/greiner-portal/
├── app.py                          # Flask Main
├── config/
│   ├── credentials.json            # DB-Zugänge (600 Permissions!)
│   ├── ldap_credentials.env        # LDAP-Config
│   └── gunicorn.conf.py           # Port 5000
├── api/
│   ├── verkauf_api.py             # ⭐ v2.1-dedup (gerade gefixt!)
│   ├── bankenspiegel_api.py
│   └── vacation_api.py
├── routes/
│   ├── verkauf_routes.py
│   ├── bankenspiegel_routes.py
│   └── vacation_routes.py
├── templates/                      # Jinja2 HTML
├── static/
│   ├── css/
│   └── js/
├── data/
│   └── greiner_controlling.db     # SQLite
├── scripts/
│   ├── imports/                    # Import-Scripts
│   └── analysis/                   # Analyse-Scripts
├── docs/
│   ├── sessions/                   # Session Wrap-Ups
│   └── sql/                        # SQL-Dokus
└── venv/                          # Python Virtual Environment
```

---

## 💾 DATENBANK-STRUKTUR

### Wichtigste Tabellen

#### sales (LocoSoft-Sync via PostgreSQL)
```sql
-- Verkaufsdaten, ~2.500 Einträge
id, vin, dealer_vehicle_type, model_description,
out_sales_contract_date,  -- Vertragsdatum (Auftragseingang)
out_invoice_date,         -- Rechnungsdatum (Auslieferung)
out_sale_price,           -- Verkaufspreis (Brutto)
netto_price,              -- Einkaufspreis (Netto)
salesman_number,          -- VK-Nr → employees.locosoft_id
make_number,              -- 27=Hyundai, 40=Opel
out_subsidiary,           -- 1=Deggendorf, 2=Landau
synced_at

-- Fahrzeugtypen:
-- N = Neuwagen
-- T = Testfahrzeug
-- V = Vorführwagen
-- G = Gebraucht
-- D = Gebraucht (Demo)
```

#### employees (LocoSoft-Sync)
```sql
-- Mitarbeiter, ~50 Einträge
locosoft_id,              -- ⭐ Verknüpfung zu sales.salesman_number
first_name, last_name, email,
department_id, active, personal_nr
```

#### fahrzeugfinanzierungen
```sql
-- Einkaufsfinanzierungen, ~194 Fahrzeuge
finanzierungsnummer, vin, modell,
aktueller_saldo,          -- ~5,29 Mio EUR gesamt
original_betrag,
finanzinstitut,           -- Stellantis/Santander/Hyundai Finance
rrdi,                     -- Händlercode (DE0154X, DE08250, etc.)
vertragsbeginn, endfaelligkeit,
alter_tage, abbezahlt
```

### Spalten-Namen (häufige Fehler vermeiden!)
```
❌ FALSCH: vertragsnummer, status, finanzierungsbetrag
✅ RICHTIG: finanzierungsnummer, finanzierungsstatus, original_betrag

❌ FALSCH: price, sale_date
✅ RICHTIG: out_sale_price, out_sales_contract_date
```

### Datenbank-Befehle
```bash
# Schema prüfen
sqlite3 data/greiner_controlling.db "PRAGMA table_info(sales);"

# Anzahl Einträge
sqlite3 data/greiner_controlling.db "SELECT COUNT(*) FROM sales;"

# Sync-Status
python3 scripts/analysis/check_db_status.py
```

---

## 🔧 LETZTER STAND (TAG 30)

### ✅ Was wurde erreicht:

#### 1. Verkaufs-Deduplizierung (BUG-FIX)
**Problem:** Fahrzeuge wurden doppelt gezählt bei N→T/V Umsetzungen
```
Beispiel: Corsa VIN S4176742
- ID 4841: Typ 'N' (Neuwagen)
- ID 4858: Typ 'T' (Test/Vorführ)
→ Wurde 2x bei Anton Süß gezählt!
```

**Lösung:** Dedup-Filter in API eingefügt
```sql
AND NOT EXISTS (
    SELECT 1 FROM sales s2 
    WHERE s2.vin = s.vin 
        AND s2.out_sales_contract_date = s.out_sales_contract_date
        AND s2.dealer_vehicle_type IN ('T', 'V')
        AND s.dealer_vehicle_type = 'N'
)
```

**Dateien geändert:**
- `api/verkauf_api.py` (v2.1-dedup)
- 6 SQL-Queries erweitert

**Git-Commits:**
- `8c59548` - fix(verkauf): Deduplizierung
- `da4f0f5` - docs(tag30): Dokumentation

**Status:** ✅ Deployed, getestet, auf GitHub

---

#### 2. Analyse: Deckungsbeitrag/Bruttoertrag

**Ausgangslage:**
- Verkaufsleitung will Deckungsbeitrag sehen
- LocoSoft Excel hat echte DB-Werte
- Unsere DB hat nur: `out_sale_price` und `netto_price`

**Problem erkannt:**
```
Rohertrag = out_sale_price - netto_price
ABER: Das ist NICHT der Deckungsbeitrag!

Deckungsbeitrag = Rohertrag - Kosten
→ Unser Rohertrag wäre ca. 2x zu hoch!
```

**Entscheidung:** Option C - LocoSoft-Import erweitern
- Importiere echte DB-Werte aus Excel/LocoSoft
- Erweitere Schema mit neuen Spalten
- Exakte Werte statt Schätzungen

**Status:** 📋 Geplant für nächste Session (Tag 31+)

---

## 🎯 NÄCHSTE AUFGABE (für neue Session)

### PRIO 1: Deckungsbeitrag-Import implementieren

#### Phase 1: Schema-Erweiterung
```sql
-- Neue Spalten in sales-Tabelle
ALTER TABLE sales ADD COLUMN deckungsbeitrag REAL;
ALTER TABLE sales ADD COLUMN db_prozent REAL;
ALTER TABLE sales ADD COLUMN fahrzeuggrundpreis REAL;
ALTER TABLE sales ADD COLUMN kosten_gesamt REAL;
ALTER TABLE sales ADD COLUMN zubeh

oer REAL;
ALTER TABLE sales ADD COLUMN nebenkosten REAL;
```

#### Phase 2: Import-Script erstellen
```python
# scripts/imports/import_locosoft_verkaufsstatistik.py
# Liest Excel-Dateien (z.B. 1025.xlsx = Oktober)
# Updated sales-Tabelle mit Finanz-Daten
```

#### Phase 3: API & Frontend
```python
# api/verkauf_api.py erweitern
# Neue Endpoints:
# GET /api/verkauf/auslieferung/detail/finanz

# Frontend:
# KPI-Kacheln mit echtem Deckungsbeitrag
# Tabelle mit DB-Spalten
# Farb-Codierung (grün/orange/rot)
```

#### Referenz-Datei:
```
/mnt/user-data/uploads/1762886251368_1025.xlsx
→ LocoSoft Verkaufsstatistik Oktober 2025
→ 129 Verkäufe mit echten DB-Werten
→ Als Vorlage für Import-Script nutzen
```

---

## 📊 REST API-ÜBERSICHT

### Verkauf API (21 Endpoints)
```
GET /api/verkauf/auftragseingang           # Dashboard
GET /api/verkauf/auftragseingang/summary   # Zusammenfassung
GET /api/verkauf/auftragseingang/detail    # Detail nach VK
GET /api/verkauf/auslieferung/summary      # Auslieferungen
GET /api/verkauf/auslieferung/detail       # Detail nach VK
GET /api/verkauf/verkaufer                 # VK-Liste
GET /api/verkauf/health                    # Version: 2.1-dedup

Parameter:
?year=2025&month=11&location=1&verkaufer=2000
```

### Bankenspiegel API
```
GET /api/bankenspiegel/dashboard
GET /api/bankenspiegel/konten
GET /api/bankenspiegel/transaktionen
GET /api/bankenspiegel/fahrzeugfinanzierungen
GET /api/bankenspiegel/health
```

---

## 🔐 CREDENTIALS & ZUGRIFFE

### Datenbank-Credentials
```bash
# Location
/opt/greiner-portal/config/credentials.json

# Permissions (WICHTIG!)
chmod 600 config/credentials.json

# Struktur
{
  "databases": {
    "locosoft": {
      "host": "10.80.80.8",
      "port": 5432,
      "database": "loco_auswertung_db",
      "user": "loco_auswertung_benutzer",
      "password": "..."
    },
    "sqlite": {
      "path": "/opt/greiner-portal/data/greiner_controlling.db"
    }
  }
}
```

### LDAP (Login)
```bash
# Location
/opt/greiner-portal/config/ldap_credentials.env

# Users loggen sich mit Windows-Credentials ein
# Format: nur "benutzername" (ohne Domain)
```

---

## 🚨 WICHTIGE STOLPERFALLEN

### 1. Port-Mismatch
```bash
# Problem: NGINX und Gunicorn auf verschiedenen Ports
# Lösung: ALLES auf Port 5000! (seit Tag 29)

# Prüfen
sudo ss -tlnp | grep :5000
grep "proxy_pass" /etc/nginx/sites-available/greiner-portal.conf
grep "bind" config/gunicorn.conf.py
```

### 2. Doppelzählungen im Verkauf
```bash
# Problem: Fahrzeuge bei N→T/V Umsetzung doppelt
# Lösung: Dedup-Filter (seit Tag 30) ✅

# Prüfen ob aktiv
curl http://localhost:5000/api/verkauf/health
# → {"version":"2.1-dedup"}
```

### 3. VIN muss bei Filter verwendet werden
```sql
-- Bei Status-Änderungen: VIN + Datum prüfen!
-- NICHT nur nach ID oder Modell filtern
```

### 4. Verkäufer ohne Namen
```bash
# Problem: VK-2008, 2009, etc. nicht in employees
# Lösung: Sync ausführen
python3 scripts/analysis/sync_employees.py
```

---

## 📂 WICHTIGE PFADE

### Auf dem Server
```
Code:           /opt/greiner-portal/
Datenbank:      /opt/greiner-portal/data/greiner_controlling.db
Logs:           /opt/greiner-portal/logs/
Virtual Env:    /opt/greiner-portal/venv/
NGINX Config:   /etc/nginx/sites-available/greiner-portal.conf
Service:        /etc/systemd/system/greiner-portal.service
```

### Netzlaufwerk (Mount)
```
Mount-Point:    /mnt/buchhaltung
Quelle:         //srvrdb01/Allgemein

PDFs:           /mnt/buchhaltung/KontoauszÃ¼ge/[Bank]/
Stellantis:     /mnt/buchhaltung/KontoauszÃ¼ge/Stellantis/
Santander:      /mnt/buchhaltung/KontoauszÃ¼ge/Santander/
Hyundai:        /mnt/buchhaltung/KontoauszÃ¼ge/HyundaiFinance/
```

---

## 🔄 STANDARD-WORKFLOWS

### 1. Code-Änderung deployen
```bash
# 1. Backup
cp api/verkauf_api.py api/verkauf_api.py.backup_$(date +%Y%m%d_%H%M%S)

# 2. Code ändern
nano api/verkauf_api.py

# 3. Testen (lokal)
python3 -m pytest tests/

# 4. Service neustarten
sudo systemctl restart greiner-portal

# 5. Prüfen
sudo systemctl status greiner-portal
curl http://localhost:5000/api/verkauf/health

# 6. Git
git add api/verkauf_api.py
git commit -m "fix: beschreibung"
git push origin HEAD
```

### 2. Datenbank-Migration
```bash
# 1. Backup
cp data/greiner_controlling.db data/greiner_controlling.db.backup_$(date +%Y%m%d_%H%M%S)

# 2. SQL ausführen
sqlite3 data/greiner_controlling.db < migrations/001_neue_spalten.sql

# 3. Testen
sqlite3 data/greiner_controlling.db "PRAGMA table_info(sales);"

# 4. Bei Fehler: Restore
mv data/greiner_controlling.db.backup_TIMESTAMP data/greiner_controlling.db
```

### 3. LocoSoft-Sync
```bash
# Manueller Sync
python3 scripts/analysis/sync_employees.py
python3 master_sync.py

# Status prüfen
python3 scripts/analysis/check_db_status.py
```

---

## 🐛 DEBUGGING

### Service läuft nicht
```bash
# Status
sudo systemctl status greiner-portal

# Logs
journalctl -u greiner-portal -f
tail -f logs/flask.log

# Neustart
sudo systemctl restart greiner-portal
```

### API gibt 500 Error
```bash
# Logs prüfen
tail -f logs/flask.log

# Python-Fehler?
python3 app.py
# → Zeigt Traceback
```

### Datenbank locked
```bash
# Alle Connections schließen
sudo systemctl stop greiner-portal
sqlite3 data/greiner_controlling.db ".timeout 3000"
sudo systemctl start greiner-portal
```

### NGINX 502 Bad Gateway
```bash
# Port-Mismatch!
grep "proxy_pass" /etc/nginx/sites-available/greiner-portal.conf
# → Muss auf Port 5000 zeigen

grep "bind" config/gunicorn.conf.py
# → Muss auch Port 5000 sein
```

---

## 📊 AKTUELLE ZAHLEN (Stand 11.11.2025)

### Verkauf (November 2025)
```
Auftragseingang:   ~31 Fahrzeuge
- Neuwagen:        ~10
- Test/Vorführ:    ~2
- Gebraucht:       ~19
```

### Fahrzeugfinanzierungen
```
Stellantis:   107 Fzg,  3,04 Mio EUR
Santander:     41 Fzg,  0,82 Mio EUR
Hyundai:       46 Fzg,  1,42 Mio EUR
GESAMT:       194 Fzg,  5,29 Mio EUR
```

### Bankenspiegel
```
Anzahl Banken:    14
Anzahl Konten:    24 (15 aktiv)
Transaktionen:    ~48.500
```

---

## 📚 WICHTIGE DOKUMENTATION

### Im Projekt-Ordner (/mnt/project/)
```
SESSION_WRAP_UP_TAG30.md           ← Letzte Session
PROJEKT_STRUKTUR_TAG29.md          ← System-Übersicht
VERZEICHNISSTRUKTUR.md             ← Dateistruktur
QUICK_REFERENCE_SERVER.md          ← Befehle
INDEX.md                           ← Alle Dokus
```

### Auf dem Server (docs/)
```
docs/sessions/SESSION_WRAP_UP_TAG30.md
docs/sql/verkauf_api_dedup_fix.sql
```

### Externe Dokumente (Downloads)
```
KONZEPT_BRUTTOERTRAG_AUSLIEFERUNGEN.md
VERGLEICH_LOCOSOFT_DB_ANALYSE.md
TESTANLEITUNG_VERKAUF_DEDUP.md
STRESSTEST_KOMPLETT.md
```

---

## 🎯 KONTEXT FÜR NEUE SESSION

### Was Claude wissen sollte:

1. **Letzter Stand:** Verkaufs-Deduplizierung fertig (v2.1-dedup)
2. **Nächstes Ziel:** Deckungsbeitrag-Import aus LocoSoft
3. **Wichtig:** Unsere DB hat NICHT den echten DB, nur Rohertrag möglich
4. **Entscheidung:** Option C gewählt - richtiger Import statt Schätzung
5. **Referenz-Datei:** `/mnt/user-data/uploads/1762886251368_1025.xlsx`

### Typische Einstiegsfrage für neue Session:
```
"Hallo Claude! Greiner Portal Projekt.

Letzter Stand: Tag 30 - Verkaufs-Deduplizierung fertig (v2.1-dedup)
Nächstes Ziel: Deckungsbeitrag aus LocoSoft importieren

Bitte lies:
1. /mnt/project/SESSION_WRAP_UP_TAG30.md
2. /mnt/project/PROJEKT_STRUKTUR_TAG29.md
3. Diese Datei (SCHNELLSTART_TAG31.md)

Dann lass uns mit dem Deckungsbeitrag-Import starten!"
```

---

## ⚡ SCHNELL-REFERENZ

```bash
# Server
ssh ag-admin@10.80.80.20
cd /opt/greiner-portal
source venv/bin/activate

# Service
sudo systemctl status greiner-portal
sudo systemctl restart greiner-portal

# Git
git status
git log --oneline -10

# Datenbank
sqlite3 data/greiner_controlling.db

# API Test
curl http://localhost:5000/api/verkauf/health
```

---

## 🎓 LESSONS LEARNED (TAG 1-30)

1. **Port-Konfiguration:** NGINX + Gunicorn müssen auf GLEICHEN Port
2. **Deduplizierung:** VIN + Datum prüfen, nicht nur Modell
3. **Datenqualität:** Spalten-Namen exakt prüfen (netto_price vs price)
4. **Backup:** Immer vor DB-Migration und Code-Deployment
5. **Git:** Kleine, häufige Commits > große seltene
6. **Dokumentation:** Während der Arbeit, nicht nachträglich
7. **Testing:** SQL-Queries erst testen, dann in API einbauen

---

**Version:** 1.0  
**Erstellt:** 11.11.2025 (Ende Tag 30)  
**Für:** Neue Chat-Session (Tag 31+)  
**Status:** ✅ Bereit für Übergabe
