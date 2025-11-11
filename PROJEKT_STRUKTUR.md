# GREINER PORTAL - PROJEKT-STRUKTUR

**Letzte Aktualisierung:** 11.11.2025 (TAG 28)  
**Status:** Produktiv - 3 EK-Banken integriert

---

## 📋 ÜBERSICHT

Greiner Portal ist ein Controlling & Buchhaltungs-System für Auto Greiner GmbH mit:
- Liquiditäts-Dashboard
- Bankenspiegel (Kontoauszüge)
- Fahrzeugfinanzierungen (3 EK-Banken)
- REST API (11 Endpoints)

---

## 🗂️ VERZEICHNIS-STRUKTUR
```
/opt/greiner-portal/
│
├── data/
│   ├── greiner_controlling.db          # Haupt-Datenbank (SQLite)
│   └── greiner_portal.db                # Auth-Datenbank
│
├── scripts/
│   ├── imports/                         # Import-Scripts
│   │   ├── import_bank_pdfs.py          # Bank-PDFs → DB
│   │   ├── import_stellantis.py         # Stellantis ZIP → DB
│   │   ├── import_santander_bestand.py  # Santander CSV → DB
│   │   └── import_hyundai_finance.py    # Hyundai CSV → DB ⭐ NEU
│   │
│   ├── tests/                           # Test-Scripts
│   ├── setup/                           # Setup-Scripts
│   ├── analysis/                        # Analyse-Tools
│   └── maintenance/                     # Wartungs-Scripts
│
├── tools/
│   └── scrapers/                        # Web-Scraper
│       └── hyundai_finance_scraper.py   # Hyundai Portal Scraper
│
├── migrations/
│   └── phase1/                          # DB-Migrationen Phase 1
│       ├── 001_add_kontostand_historie.sql
│       ├── 002_add_kreditlinien.sql
│       ├── 003_add_kategorien.sql
│       ├── 004_add_pdf_imports.sql
│       ├── 005_add_views.sql
│       └── 006_add_santander_support.sql
│
├── config/
│   ├── credentials.json                 # Bank-Zugangsdaten (GEHEIM!)
│   ├── .env                             # Umgebungsvariablen
│   └── ldap_credentials.env             # LDAP-Config
│
├── parsers/                             # PDF-Parser
│   ├── hypovereinsbank_parser.py
│   ├── sparkasse_parser.py
│   ├── vrbank_parser.py
│   └── parser_factory.py
│
├── templates/                           # HTML-Templates
├── static/                              # CSS/JS/Images
├── routes/                              # Flask-Routes
├── api/                                 # REST API
└── docs/
    └── sessions/                        # Session-Dokumentation
```

---

## 🗄️ DATENBANK-STRUKTUR

### fahrzeugfinanzierungen (WICHTIG!)

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

## 📊 AKTUELLE ZAHLEN (11.11.2025)
```
Stellantis:      107 Fz.  →  3,04 Mio € Saldo
Santander:        41 Fz.  →  0,82 Mio € Saldo
Hyundai Finance:  46 Fz.  →  1,42 Mio € Saldo
────────────────────────────────────────────────
GESAMT:          194 Fz.  →  5,29 Mio € Saldo
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

### Alle Spaltennamen anzeigen
```bash
sqlite3 data/greiner_controlling.db "PRAGMA table_info(fahrzeugfinanzierungen);"
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

---

## 🐛 BEKANNTE BUGS (TAG 28)

1. ❌ Urlaubsplaner nicht aufrufbar
2. ❌ API-Placeholder angezeigt
3. ❌ Bankenspiegel → Fahrzeugfinanzierungen fehlt (WICHTIG!)
4. ❌ Verkauf → Auftragseingang Detail 404
5. ❌ Verkauf → Auslieferungen Detail 404

**Details:** Siehe `docs/sessions/SESSION_WRAP_UP_TAG28.md`

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
2. /mnt/project/docs/sessions/SESSION_WRAP_UP_TAG28.md
3. git log --oneline -10

AKTUELLER STAND:
- 3 EK-Banken integriert (194 Fz, 5,29 Mio EUR)
- Branch: feature/bankenspiegel-komplett
```

---

**Version:** 1.0  
**Erstellt:** 11.11.2025 (TAG 28)  
**Status:** ✅ Produktiv
