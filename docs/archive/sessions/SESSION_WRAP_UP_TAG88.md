# SESSION WRAP-UP TAG 88
**Datum:** 2025-12-02  
**Fokus:** Bank-Import Vereinfachung, Job-Scheduler Fix

---

## ✅ WICHTIGSTE ERKENNTNISSE

### 1. Bank-Import: Alle außer HypoVereinsbank liefern MT940!

| Bank | Format | Quelle |
|------|--------|--------|
| Genobank 57908 | MT940 (.mta) | ✅ Funktioniert |
| Genobank 22225 | MT940 (.mta) | ✅ Funktioniert |
| Genobank 1501500 | MT940 (.mta) | ✅ Funktioniert |
| Sparkasse 760036467 | MT940 (.TXT) | ✅ Funktioniert |
| VR Bank Landau 303585 | MT940 (.mta) | ✅ Funktioniert |
| **HypoVereinsbank** | **PDF** | ✅ Einziger PDF-Import |

**Konsequenz:** PDF-Parser für Sparkasse, VR Bank Landau, Genobank sind überflüssig!

### 2. Gunicorn Multi-Worker Problem gelöst

**Problem:** Jeder Gunicorn-Worker startete seinen eigenen Scheduler → Jobs liefen 4-10x parallel!

**Lösung:** Lock-File (`/tmp/greiner_scheduler.lock`) stellt sicher, dass nur EIN Worker den Scheduler startet.

---

## ✅ ERLEDIGT

### 1. Job-Scheduler Fixes
- ✅ Lock-File Mechanismus implementiert (nur 1 Scheduler-Instanz)
- ✅ Jobs nach Kostenstellen gruppiert (controlling, aftersales, verkauf)
- ✅ Bank-Jobs von 6 auf 4 reduziert

### 2. Bank-Import Vereinfachung
- ✅ MT940 = Standard für 5 von 6 Konten
- ✅ PDF = Nur HypoVereinsbank (08:30)
- ✅ Watcher und redundante PDF-Jobs entfernt

### 3. SQLite Fixes (aus vorheriger Session)
- ✅ WAL-Mode aktiviert
- ✅ CHECK Constraints erweitert (MT940, PDF, MANUAL, CSV)

### 4. Datenstand-Badge
- ✅ API-Endpoint: `/api/bankenspiegel/datenstand`
- ✅ Grün/Gelb/Rot basierend auf Alter

---

## 📁 GEÄNDERTE DATEIEN

```
app.py                           ← Lock-File für Scheduler (WICHTIG!)
scheduler/job_definitions.py     ← Nach Kostenstellen gruppiert, vereinfacht
scripts/imports/import_all_bank_pdfs.py  ← Parser-Module mit parsers. Prefix
api/bankenspiegel_api.py         ← Datenstand-Endpoint
templates/bankenspiegel_konten.html  ← Badge-Container
static/js/bankenspiegel_konten.js    ← loadDatenstand()
```

---

## 📊 JOB-ÜBERSICHT (NEU)

### Kostenstelle: Controlling & Verwaltung (12 Jobs)
| Job | Zeitplan | Beschreibung |
|-----|----------|--------------|
| import_mt940_08/12/17 | 08:00, 12:00, 17:00 | MT940 für alle außer HVB |
| import_hvb_pdf | 08:30 | HypoVereinsbank PDF |
| import_santander | 08:15 | Santander Bestand |
| scrape_hyundai | 08:45 | Hyundai Finance Scraper |
| import_hyundai | 09:00 | Hyundai Finance Import |
| umsatz_bereinigung | 09:30 | Umsatz-Bereinigung |
| leasys_cache_refresh | */30 7-18 | Leasys Cache |
| sync_employees | 06:00 | Mitarbeiter Sync |
| email_auftragseingang | 17:15 | Daily Report |
| db_backup | 03:00 | SQLite Backup |
| cleanup_backups | 03:30 | Alte Backups löschen |

### Kostenstelle: Aftersales (12 Jobs)
| Job | Zeitplan | Beschreibung |
|-----|----------|--------------|
| servicebox_scraper | 09:30, 12:30, 16:30 | ServiceBox Scraper |
| servicebox_matcher | 10:00, 13:00, 17:00 | ServiceBox Matcher |
| servicebox_import | 10:05, 13:05, 17:05 | ServiceBox Import |
| servicebox_master | 20:00 | Full Reload |
| sync_teile_locosoft | */30 | Teile Sync |
| import_teile_lieferscheine | */2h | Lieferscheine |

### Kostenstelle: Verkauf (4 Jobs)
| Job | Zeitplan | Beschreibung |
|-----|----------|--------------|
| sync_sales | stündlich 7-18 | Verkauf Sync |
| import_stellantis | 07:30 | Stellantis Import |
| sync_stammdaten | 09:30 | Fahrzeug-Stammdaten |
| locosoft_mirror | 20:00 | Locosoft Mirror |

---

## 📂 BANK-IMPORT DATEIPFADE

```
MT940-Pfad: /mnt/buchhaltung/Buchhaltung/Kontoauszüge/mt940/
PDF-Pfad:   /mnt/buchhaltung/Buchhaltung/Kontoauszüge/Hypovereinsbank/

Dateien:
- Umsaetze_57908_*.mta     → Genobank KK
- Umsaetze_22225_*.mta     → Genobank Immo
- Umsaetze_1501500_*.mta   → Genobank HYU
- Umsaetze_303585_*.mta    → VR Bank Landau
- *-760036467-umsMT940.TXT → Sparkasse
- HV Kontoauszug *.pdf     → HypoVereinsbank
```

---

## 🧹 AUFRÄUMEN (OPTIONAL - Nächste Session)

Diese PDF-Parser werden nicht mehr benötigt:
```
parsers/sparkasse_parser.py          ← MT940 vorhanden
parsers/vrbank_landau_parser.py      ← MT940 vorhanden  
parsers/genobank_universal_parser.py ← MT940 vorhanden
```

Behalten:
```
parsers/hypovereinsbank_parser_v2.py ← Einziger PDF-Parser
parsers/mt940_parser.py              ← Haupt-Import (import_mt940.py)
```

---

## 🎯 NÄCHSTE SESSION

1. **ServiceBox Scraper beobachten** - Sollte jetzt nur 1x laufen
2. **Leasys Cache Timeout erhöhen** - Aktuell 300s, braucht mehr
3. **Alte PDF-Parser entfernen** (optional)
4. **Login-Seite deployen** (Mockup B)

---

## 📝 KONTEXT FÜR CLAUDE

**Kritische Architektur-Info:**
- Gunicorn läuft mit ~10 Workern
- Scheduler darf nur in EINEM Worker laufen → Lock-File in app.py
- Lock-File: `/tmp/greiner_scheduler.lock`

**Bank-Import ist jetzt einfach:**
- MT940 = Standard für 5 von 6 Konten
- PDF = Nur HypoVereinsbank
- Keine komplexen Parser-Interfaces nötig

**SQLite-Status:**
- WAL-Mode aktiv (bessere Concurrency)
- Constraints erlauben: MT940, PDF, MANUAL, CSV

---

## ⏰ ZEITAUFWAND TAG 88
- Bank-Import Analyse: 30min
- Erkenntnis MT940 für alle: 10min
- Job-Definitionen vereinfachen: 30min
- Gunicorn Multi-Worker Bug finden: 30min
- Lock-File Lösung implementieren: 20min
- Dokumentation: 20min

**Gesamt: ~2.5h**
