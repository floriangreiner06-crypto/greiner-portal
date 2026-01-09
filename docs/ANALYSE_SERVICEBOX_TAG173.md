# ServiceBox Feature - Vollständige Analyse TAG 173

**Datum:** 2026-01-09  
**Status:** 🔴 KRITISCH - Feature funktioniert nicht

---

## 🎯 Executive Summary

**Hauptprobleme:**
1. ❌ **2 Scripts verwenden noch SQLite** statt PostgreSQL
2. ❌ **Scraper findet keine Bestellungen** ("0 eindeutige Bestellungen gefunden")
3. ❌ **Letzter Sync vor 16 Tagen** (23.12.2025)
4. ⚠️ **TEST_MODE aktiv** im Scraper

---

## 📊 Feature-Architektur

### ServiceBox-Workflow

```
1. Scraper (servicebox_scraper)
   └─> Holt Bestellungen aus ServiceBox Portal
   └─> Speichert: /opt/greiner-portal/logs/servicebox_bestellungen_details_final.json

2. Matcher (servicebox_matcher)
   └─> Verknüpft Bestellungen mit Locosoft-Daten
   └─> Speichert: /opt/greiner-portal/logs/servicebox_matched.json

3. Import (servicebox_import)
   └─> Importiert in PostgreSQL
   └─> Tabellen: stellantis_bestellungen, stellantis_positionen
```

### Aktuelle Status

| Komponente | Status | Letzter Lauf | Problem |
|------------|--------|--------------|---------|
| **Scraper** | ❌ Fehlgeschlagen | 09.01.2026 08:32 | Findet 0 Bestellungen |
| **Matcher** | ✅ Erfolgreich | 09.01.2026 08:31 | Verwendet SQLite |
| **Import** | ⚠️ Nicht getestet | - | Verwendet SQLite |
| **Master** | ✅ Erfolgreich | 09.01.2026 08:24 | Findet Bestellungen |

---

## 🐛 Gefundene Probleme

### Problem 1: SQLite statt PostgreSQL

#### `match_servicebox.py`
- **Aktuell:** Verwendet `sqlite3.connect(SQLITE_PATH)`
- **Soll:** PostgreSQL via `get_db()` oder `get_locosoft_connection()`
- **Tabellen:** `customers_suppliers`, `sales` (aus Locosoft)
- **Status:** ❌ Muss migriert werden

#### `import_servicebox_to_db.py`
- **Aktuell:** Verwendet `sqlite3.connect(DB_PATH)`
- **Soll:** PostgreSQL via `get_db()`
- **Tabellen:** `stellantis_bestellungen`, `stellantis_positionen`, `sync_status`
- **Status:** ❌ Muss migriert werden

### Problem 2: Scraper findet keine Bestellungen

**Symptom:**
```
📊 0 eindeutige Bestellungen gefunden
❌ Keine Bestellnummern gefunden!
```

**Mögliche Ursachen:**
1. **TEST_MODE = True** - Scraper läuft im Test-Modus
2. **Seitenstruktur geändert** - XPath findet keine Links
3. **Keine neuen Bestellungen** - Historie-Seite leer
4. **Filter-Problem** - Historie zeigt nur alte Bestellungen

**Scraper-Logik:**
```python
# Zeile 112-120
links = driver.find_elements(By.XPATH, "//a[contains(@href, 'commandeDetailRepAll.do')]")
for link in links:
    text = link.text.strip()
    if text and text.startswith('1JA') and len(text) == 9:
        # Bestellung gefunden
```

### Problem 3: Master-Scraper funktioniert

**Interessant:** `servicebox_master` (servicebox_scraper_complete.py) läuft erfolgreich und findet Bestellungen!

**Unterschied:**
- **Master:** Komplett neu laden (alle Bestellungen)
- **Detail-Scraper:** Nur neue Bestellungen (Historie-Seite)

---

## 🔍 Script-Analyse

### Script-Pfade

| Task | Script-Pfad | Status |
|------|------------|--------|
| `servicebox_scraper` | `/opt/greiner-portal/tools/scrapers/servicebox_detail_scraper_final.py` | ✅ Existiert |
| `servicebox_matcher` | `/opt/greiner-portal/scripts/scrapers/match_servicebox.py` | ✅ Existiert (SQLite) |
| `servicebox_import` | `/opt/greiner-portal/scripts/imports/import_servicebox_to_db.py` | ✅ Existiert (SQLite) |
| `servicebox_master` | `/opt/greiner-portal/tools/scrapers/servicebox_scraper_complete.py` | ✅ Existiert |

### Datenbank-Tabellen

**PostgreSQL:**
- ✅ `stellantis_bestellungen` - Existiert
- ✅ `stellantis_positionen` - Existiert
- ✅ `sync_status` - Existiert

**Daten:**
- 379 Bestellungen (letzte: 09.12.2025)
- 189 gematcht (49.9%)
- Letzter Sync: 23.12.2025

---

## ✅ Action Items

### Sofort (Kritisch)

1. **`match_servicebox.py` auf PostgreSQL migrieren**
   - SQLite → PostgreSQL
   - `customers_suppliers` → Locosoft DB
   - `sales` → Locosoft DB

2. **`import_servicebox_to_db.py` auf PostgreSQL migrieren**
   - SQLite → PostgreSQL
   - `stellantis_bestellungen` → PostgreSQL
   - `sync_status` → PostgreSQL

3. **Scraper-Problem beheben**
   - TEST_MODE deaktivieren
   - Prüfen warum keine Bestellungen gefunden werden
   - Screenshots analysieren

### Kurzfristig

4. **Workflow prüfen**
   - Warum verwendet Matcher SQLite statt Locosoft?
   - Soll Matcher Locosoft-Daten verwenden?

5. **Monitoring verbessern**
   - Bessere Fehlerbehandlung
   - Logs strukturieren

---

## 📝 Migration-Plan

### `match_servicebox.py` → PostgreSQL

**Änderungen:**
1. `sqlite3.connect()` → `get_locosoft_connection()` (für customers_suppliers, sales)
2. `?` → `%s` (Placeholder)
3. `sqlite_master` → `information_schema.tables`
4. `UPPER(vin) = UPPER(?)` → `UPPER(vin) = UPPER(%s)`

### `import_servicebox_to_db.py` → PostgreSQL

**Änderungen:**
1. `sqlite3.connect()` → `get_db()`
2. `?` → `%s` (Placeholder)
3. `CURRENT_TIMESTAMP` → `NOW()`
4. `cursor.lastrowid` → `RETURNING id` (PostgreSQL)

---

**Erstellt:** 2026-01-09  
**TAG:** 173  
**Autor:** Claude (Auto)
