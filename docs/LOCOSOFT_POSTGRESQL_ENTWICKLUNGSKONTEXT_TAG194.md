# Locosoft PostgreSQL - Entwicklungs-Kontext

**Datum:** TAG 194  
**Zweck:** Vollständiger Kontext zu unseren Locosoft PostgreSQL-Entwicklungen

---

## 📊 Übersicht

### Architektur

```
┌─────────────────────────────────────────────────────────────┐
│  Locosoft PostgreSQL (10.80.80.8:5432)                      │
│  Database: loco_auswertung_db                                │
│  User: loco_auswertung_benutzer (read-only)                 │
│  Schema: 102 Tabellen                                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Read-only Zugriff
                          │
┌─────────────────────────────────────────────────────────────┐
│  DRIVE Portal PostgreSQL (127.0.0.1:5432)                   │
│  Database: drive_portal                                      │
│  User: drive_user                                            │
│  Schema: Gespiegelte Tabellen (loco_*)                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ API Zugriff
                          │
┌─────────────────────────────────────────────────────────────┐
│  DRIVE Portal Flask App                                      │
│  - api/werkstatt_data.py (Live-Daten)                        │
│  - api/controlling_api.py (BWA)                              │
│  - api/verkauf_api.py (Verkauf)                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Datenbank-Verbindungen

### 1. Locosoft PostgreSQL (Externe DB)

**Konfiguration:**
- **Host:** 10.80.80.8:5432
- **Database:** `loco_auswertung_db`
- **User:** `loco_auswertung_benutzer`
- **Password:** `loco` (aus `config/credentials.json`)
- **Berechtigung:** Read-only

**Verwendung:**
```python
from api.db_utils import locosoft_session

with locosoft_session() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE ...")
```

**Datei:** `api/db_utils.py` (Zeile 77-113)

### 2. DRIVE Portal PostgreSQL (Lokale DB)

**Konfiguration:**
- **Host:** 127.0.0.1:5432
- **Database:** `drive_portal`
- **User:** `drive_user`
- **Password:** `DrivePortal2024`

**Verwendung:**
```python
from api.db_connection import get_db

conn = get_db()
cursor = conn.cursor()
cursor.execute("SELECT * FROM loco_orders WHERE ...")
```

**Datei:** `api/db_connection.py`

---

## 📅 Entwicklungs-Historie

### TAG 1 (Anfang 2024): Erste Locosoft-Integration
- **Commit:** `637b5f4 Tag 1: Locosoft-Integration & Mitarbeiter-Sync`
- **Ziel:** Grundlegende Verbindung zu Locosoft PostgreSQL
- **Ergebnis:** Read-only Zugriff auf Locosoft-DB

### TAG 18 (März 2024): Sales-Sync-System
- **Commit:** `92cf022 feat(verkauf): TAG 18 - Sales-Sync-System komplett`
- **Ziel:** Verkaufsdaten aus Locosoft synchronisieren
- **Ergebnis:** `scripts/sync/sync_sales.py` erstellt

### TAG 90 (Dezember 2024): Werkstatt-Zeiten Sync
- **Commit:** `4ed84b5 TAG 90: Scripts logisch umbenannt für Job-Scheduler`
- **Ziel:** Werkstatt-Stempelzeiten synchronisieren
- **Ergebnis:** `scripts/sync/sync_werkstatt_zeiten.py` erstellt
- **Problem:** `loco_times` war leer (0 Zeilen)

### TAG 109-110 (Dezember 2024): Celery Migration
- **Commit:** `99c1011 feat(TAG109-110): Celery Migration + Werkstatt Dashboard Fixes`
- **Ziel:** SQLite → PostgreSQL Migration
- **Ergebnis:** Vollständige PostgreSQL-Migration

### TAG 136 (23.12.2024): PostgreSQL Migration abgeschlossen
- **Commit:** `780da9d chore: Sync TAG146 - TEK Refactoring`
- **Ziel:** Alle SQLite-Abhängigkeiten entfernen
- **Ergebnis:**
  - `locosoft_mirror.py` erstellt (Version 2.0)
  - `INCLUDE_VIEWS = ['times', 'employees']` hinzugefügt
  - Täglicher Sync um 19:00 Uhr

### TAG 148 (30.12.2024): Werkstatt Data Module
- **Commit:** `ac2096b fix: Sync TAG148 RealDictCursor Fix`
- **Ziel:** Werkstatt-Daten direkt aus Locosoft
- **Ergebnis:** `api/werkstatt_data.py` refactored
- **Architektur:** Nutzt `locosoft_session()` für Live-Daten

### TAG 185 (Januar 2025): Locosoft-kompatible Stempelzeit-Berechnung
- **Commit:** `5a5eefd feat: Locosoft-kompatible Stempelzeit-Berechnung implementiert (TAG 185)`
- **Ziel:** Stempelzeit-Berechnung analog zu Locosoft
- **Ergebnis:** Neue Funktionen in `werkstatt_data.py`

### TAG 194 (16.01.2025): `times` VIEW Problem
- **Problem:** `public.times` VIEW existiert nicht
- **Ursache:** VIEW wurde gelöscht oder nie erstellt
- **Status:** ❌ Funktioniert nicht

---

## 🔄 Daten-Synchronisation

### Locosoft Mirror (`locosoft_mirror.py`)

**Zweck:** Spiegelt ALLE Locosoft-Tabellen nach DRIVE Portal PostgreSQL

**Architektur:**
```
Locosoft PostgreSQL (10.80.80.8)
    ↓ (Read-only)
locosoft_mirror.py (Celery Task)
    ↓ (INSERT INTO)
DRIVE Portal PostgreSQL (127.0.0.1)
    ↓ (Prefix: loco_)
loco_orders, loco_labours, loco_times, ...
```

**Schedule:**
- **Zeit:** Täglich 19:00 Uhr
- **Celery Task:** `celery_app.tasks.locosoft_mirror`
- **Dauer:** ~5-15 Minuten

**Konfiguration:**
- **Prefix:** `loco_` (vermeidet Konflikte)
- **Skip-Tabellen:** Große Konfigurator-Tabellen (1.7 Mio+ Zeilen)
- **INCLUDE_VIEWS:** `['times', 'employees']` (sollten als VIEW gespiegelt werden)

**Datei:** `scripts/sync/locosoft_mirror.py`

### Live-Daten Zugriff

**Zweck:** Direkte Abfragen aus Locosoft PostgreSQL (ohne Spiegelung)

**Verwendung:**
- `api/werkstatt_data.py` - Werkstatt-Daten (Live)
- `api/controlling_api.py` - BWA-Daten (Live)
- `api/verkauf_api.py` - Verkaufs-Daten (Live)

**Vorteile:**
- ✅ Immer aktuell (keine Verzögerung)
- ✅ Keine lokale Speicherung nötig

**Nachteile:**
- ⚠️ Abhängig von Locosoft-DB-Verfügbarkeit
- ⚠️ Keine Offline-Verfügbarkeit

---

## 📋 Verfügbare Tabellen

### Locosoft PostgreSQL (102 Tabellen)

**Wichtigste Tabellen:**
- `orders` - Werkstattaufträge (41.048 Zeilen)
- `labours` - Arbeitspositionen (281.117 Zeilen)
- `times` - **Stempelzeiten (VIEW - existiert NICHT in public)**
- `invoices` - Rechnungen (54.219 Zeilen)
- `journal_accountings` - Buchhaltungsbuchungen (599.210 Zeilen)
- `dealer_vehicles` - Fahrzeuge (5.310 Zeilen)
- `employees_history` - Mitarbeiter (124 Zeilen)
- `customers_suppliers` - Kunden (53.524 Zeilen)

**Vollständige Liste:** `docs/DB_SCHEMA_LOCOSOFT.md` (auto-generiert 2025-12-12)

### DRIVE Portal PostgreSQL (Gespiegelte Tabellen)

**Prefix:** `loco_`

**Wichtigste gespiegelte Tabellen:**
- `loco_orders` - Werkstattaufträge
- `loco_labours` - Arbeitspositionen
- `loco_times` - Stempelzeiten (194.004 Zeilen)
- `loco_invoices` - Rechnungen
- `loco_journal_accountings` - Buchhaltungsbuchungen
- `loco_dealer_vehicles` - Fahrzeuge
- `loco_employees` - Mitarbeiter
- `loco_customers_suppliers` - Kunden

**Sync-Status:** Täglich um 19:00 Uhr

---

## 🔧 Aktuelle Probleme

### Problem 1: `times` VIEW existiert nicht ✅ ROOT CAUSE IDENTIFIZIERT

**Symptom:**
- `UndefinedTable: Relation »times« existiert nicht`
- Spinner auf `/werkstatt/stempeluhr`, `/werkstatt/cockpit`

**Root Cause:** ✅ **FEHLERHAFTER LOCOSOFT DB-UPDATE-PROZESS**
- Locosoft-Server wurde neu gestartet (Reboot)
- Locosoft DB-Update-Prozess war **zweimal fehlerhaft**
- VIEW `public.times` wurde nicht erstellt

**Lösung:**
- ✅ **Locosoft DB-Update-Prozess manuell neu starten**
- Prozess läuft normalerweise automatisch nach Server-Reboot
- Nach erfolgreichem Lauf wird VIEW automatisch erstellt

**Status:** ⏳ Wartet auf Locosoft-Admin (manueller Neustart)

**⚠️ WICHTIG:** Dies ist ein **Locosoft-Problem**, nicht ein DRIVE-Problem!
Siehe: `docs/LOCOSOFT_DB_UPDATE_PROBLEM_TAG194.md`

### Problem 2: `locosoft_mirror.py` kann VIEW nicht spiegeln

**Symptom:**
- `locosoft_mirror.py` versucht `times` als VIEW zu spiegeln
- VIEW existiert nicht → kann nicht gespiegelt werden

**Ursache:**
- `INCLUDE_VIEWS = ['times', 'employees']` seit TAG 136
- VIEW wurde nie erstellt oder wurde gelöscht

**Lösung:**
- VIEW erstellen (siehe Problem 1)
- Oder Code auf `loco_times` aus Portal-DB umstellen

---

## 📚 Code-Struktur

### Daten-Module

**1. `api/werkstatt_data.py`**
- **Zweck:** Werkstatt-Daten direkt aus Locosoft
- **Verbindung:** `locosoft_session()` (Live-Daten)
- **Tabellen:** `times`, `orders`, `labours`, `invoices`
- **Funktionen:**
  - `get_mechaniker_leistung()` - KPI-Berechnung
  - `get_stempeluhr()` - Live-Stempeluhr
  - `get_offene_auftraege()` - Offene Aufträge

**2. `api/controlling_api.py`**
- **Zweck:** BWA-Daten aus Locosoft
- **Verbindung:** `locosoft_session()` (Live-Daten)
- **Tabellen:** `journal_accountings`

**3. `api/verkauf_api.py`**
- **Zweck:** Verkaufs-Daten aus Locosoft
- **Verbindung:** `locosoft_session()` (Live-Daten)
- **Tabellen:** `dealer_vehicles`, `invoices`

### Sync-Scripts

**1. `scripts/sync/locosoft_mirror.py`**
- **Zweck:** Komplette Spiegelung aller Tabellen
- **Schedule:** Täglich 19:00 Uhr
- **Celery Task:** `celery_app.tasks.locosoft_mirror`

**2. `scripts/sync/sync_sales.py`**
- **Zweck:** Verkaufs-Daten synchronisieren
- **Schedule:** Stündlich 7-18 Uhr (Mo-Fr)

**3. `scripts/sync/sync_werkstatt_zeiten.py`**
- **Zweck:** Werkstatt-Zeiten synchronisieren
- **Schedule:** Nach `locosoft_mirror` (19:15 Uhr)

---

## 🎯 Best Practices

### 1. Live-Daten vs. Gespiegelte Daten

**Live-Daten verwenden für:**
- ✅ Aktuelle Werkstatt-Daten (Stempeluhr, Live-Board)
- ✅ BWA-Daten (aktueller Monat)
- ✅ Verkaufs-Daten (aktueller Tag)

**Gespiegelte Daten verwenden für:**
- ✅ Historische Analysen
- ✅ Performance-kritische Queries
- ✅ Offline-Verfügbarkeit

### 2. DB-Verbindungen

**Immer verwenden:**
```python
# Für Locosoft-DB:
from api.db_utils import locosoft_session

with locosoft_session() as conn:
    cursor = conn.cursor()
    # ... Queries
```

**NICHT verwenden:**
```python
# Direkte Verbindung (kein automatisches Cleanup)
conn = get_locosoft_connection()
```

### 3. SQL-Syntax

**PostgreSQL-kompatibel:**
- ✅ `%s` (nicht `?`)
- ✅ `CURRENT_DATE` (nicht `date('now')`)
- ✅ `true` (nicht `1`)
- ✅ `EXTRACT(YEAR FROM col)` (nicht `strftime`)

---

## 📊 Schema-Informationen

### Locosoft PostgreSQL Schema

**Dokumentation:**
- `docs/DB_SCHEMA_LOCOSOFT.md` (auto-generiert 2025-12-12)
- **102 Tabellen** vollständig dokumentiert

**Generierung:**
```bash
python scripts/utils/export_db_schema.py --locosoft
```

### DRIVE Portal PostgreSQL Schema

**Dokumentation:**
- `docs/DB_SCHEMA_POSTGRESQL.md`
- **161 Tabellen** (inkl. gespiegelte Locosoft-Tabellen)

---

## 🔍 Troubleshooting

### Problem: `times` existiert nicht

**Symptom:**
```
psycopg2.errors.UndefinedTable: FEHLER: Relation »times« existiert nicht
```

**Lösung:**
1. Prüfe ob VIEW `public.times` existiert
2. Falls nicht: VIEW erstellen (benötigt DB-Admin)
3. Oder: Code auf `loco_times` umstellen

### Problem: `locosoft_mirror` schlägt fehl

**Symptom:**
- Celery Task `locosoft_mirror` fehlgeschlagen
- Logs zeigen `VIEW 'times' nicht gefunden`

**Lösung:**
- VIEW `public.times` erstellen
- Oder: `INCLUDE_VIEWS` anpassen

### Problem: Verbindungsfehler

**Symptom:**
```
psycopg2.OperationalError: could not connect to server
```

**Lösung:**
1. Prüfe Locosoft-DB-Verfügbarkeit: `ping 10.80.80.8`
2. Prüfe Credentials: `config/credentials.json`
3. Prüfe Firewall-Regeln

---

## 📝 Wichtige Dateien

### Konfiguration
- `config/credentials.json` - Locosoft-DB-Credentials
- `config/.env` - Environment-Variablen

### Code
- `api/db_utils.py` - DB-Verbindungs-Utilities
- `api/werkstatt_data.py` - Werkstatt-Daten-Modul
- `scripts/sync/locosoft_mirror.py` - Mirror-Script

### Dokumentation
- `docs/DB_SCHEMA_LOCOSOFT.md` - Locosoft-Schema
- `docs/DB_SCHEMA_POSTGRESQL.md` - DRIVE Portal-Schema
- `docs/LOCOSOFT_REVERSE_ENGINEERING_EINSCHAETZUNG.md` - Architektur-Übersicht

---

## 🚀 Nächste Schritte

1. **VIEW `public.times` erstellen** (benötigt DB-Admin)
2. **`locosoft_mirror` testen** (nach VIEW-Erstellung)
3. **Code-Änderungen dokumentieren** (falls VIEW nicht erstellt werden kann)

---

**Stand:** TAG 194 (16.01.2025)  
**Status:** ⚠️ `times` VIEW fehlt - Funktionalität eingeschränkt
