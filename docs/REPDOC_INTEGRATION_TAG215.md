# RepDoc (WM SE / Trost) Integration in DRIVE

**Datum:** 2026-01-27  
**TAG:** 215  
**Status:** ⏸️ **Auf Eis gelegt** - Entscheidung Teile & Zubehör ausstehend

---

## 📋 ÜBERSICHT

**RepDoc** ist ein Katalog-System von WM SE (Trost) für Fahrzeugteile. Die Integration ermöglicht es, RepDoc als weitere Quelle im Teile-Preisvergleich zu nutzen.

**URL:** https://www2.repdoc.com/DE/Login#Start

**Zugangsdaten:**
- Benutzername: `1042953`
- Passwort: `Greiner1`

---

## 🔧 IMPLEMENTIERUNG

### 1. RepDoc Scraper

**Datei:** `tools/scrapers/repdoc_scraper.py`

**Funktionen:**
- `RepDocScraper` - Singleton-Pattern (ähnlich Dello)
- `login()` - Automatischer Login bei RepDoc
- `search(teilenummer)` - Suche nach Teilenummer
- `_parse_results()` - Parse HTML-Ergebnisse

**Technologie:**
- Selenium mit Chrome headless
- Automatisches Login
- HTML-Parsing für Suchergebnisse

### 2. Integration in Teile-API

**Datei:** `api/teile_api.py`

**Endpoint:** `GET /api/teile/vergleich/<teilenummer>?repdoc=true`

**Query-Parameter:**
- `repdoc=true` - RepDoc einbeziehen (optional, Standard: false)

**Beispiel:**
```
GET /api/teile/vergleich/1109AL?repdoc=true
```

**Response:**
```json
{
  "success": true,
  "teilenummer": "1109AL",
  "quellen": {
    "locosoft": {...},
    "schaeferbarthold": {...},
    "repdoc": {
      "name": "RepDoc (WM SE / Trost)",
      "teilenummer": "1109AL",
      "beschreibung": "...",
      "preis": 12.50,
      "ek": 12.50,
      "verfuegbar": true,
      "alle_ergebnisse": 1
    }
  },
  "empfehlung": {
    "guenstigster": "RepDoc (WM SE / Trost)",
    "preis": 12.50
  }
}
```

---

## 🔐 ZUGANGSDATEN

### Umgebungsvariablen (empfohlen)

Die Zugangsdaten sollten als Umgebungsvariablen gesetzt werden:

```bash
export REPDOC_USERNAME="1042953"
export REPDOC_PASSWORD="Greiner1"
```

**Oder in `/opt/greiner-portal/config/.env`:**
```
REPDOC_USERNAME=1042953
REPDOC_PASSWORD=Greiner1
```

### Fallback

Falls keine Umgebungsvariablen gesetzt sind, verwendet der Scraper Hardcoded-Werte (nur für Entwicklung!).

**⚠️ WICHTIG:** Zugangsdaten NICHT im Code committen!

---

## 🧪 TESTING

### 1. Scraper direkt testen

```bash
cd /opt/greiner-portal
python3 tools/scrapers/repdoc_scraper.py
```

**Erwartete Ausgabe:**
```
=== RepDoc Scraper Test ===
Login: True
✅ RepDoc Login erfolgreich

=== Suche Test ===
Suche: 1109AL
Zeit: 8.5s
Erfolg: True
Anzahl: 1
  1109AL: Beschreibung... - 12.50€
```

### 2. API-Endpoint testen

```bash
curl "http://10.80.80.20:5000/api/teile/vergleich/1109AL?repdoc=true"
```

**Erwartete Response:**
- `quellen.repdoc` sollte vorhanden sein
- `preis` sollte gesetzt sein
- `empfehlung` sollte RepDoc berücksichtigen

### 3. Frontend testen

**URL:** `http://10.80.80.20:5000/werkstatt/teile-vergleich?repdoc=true`

**Erwartetes Verhalten:**
- RepDoc erscheint als weitere Quelle
- Preise werden angezeigt
- Empfehlung berücksichtigt RepDoc

---

## 🐛 BEKANNTE PROBLEME

### 1. Login-Erkennung

**Problem:** RepDoc verwendet verschiedene Login-Formulare, die automatische Erkennung kann fehlschlagen.

**Lösung:** Scraper versucht mehrere Selektoren und Login-Varianten.

**Workaround:** Falls Login fehlschlägt, manuell prüfen ob Selektoren noch korrekt sind.

### 2. HTML-Struktur

**Problem:** RepDoc kann verschiedene HTML-Strukturen für Suchergebnisse verwenden.

**Lösung:** Scraper versucht mehrere Parsing-Strategien:
- Tabellen-Struktur
- Div-Container
- Alternative Strukturen

**Workaround:** Falls Parsing fehlschlägt, HTML-Struktur manuell analysieren und Selektoren anpassen.

### 3. Performance

**Problem:** Selenium-Scraping ist langsam (~5-10 Sekunden pro Suche).

**Lösung:** 
- RepDoc ist standardmäßig deaktiviert (`repdoc=false`)
- Nur bei expliziter Anfrage aktivieren
- Singleton-Pattern für Session-Wiederverwendung

---

## 📊 ARCHITEKTUR

### Datenfluss

```
Frontend → /api/teile/vergleich/<tnr>?repdoc=true
    ↓
teile_api.py::teile_vergleich()
    ↓
repdoc_scraper.py::RepDocScraper.search()
    ↓
Selenium → https://www2.repdoc.com
    ↓
HTML-Parsing → Strukturierte Daten
    ↓
Response JSON
```

### SSOT-Konformität

✅ **Verwendet zentrale Funktionen:**
- `api/db_utils.py` für Locosoft-Verbindungen
- `api/standort_utils.py` für Standort-Mappings (falls benötigt)

✅ **Keine Redundanzen:**
- RepDoc-Scraper ist eigenständig
- Integration in bestehende `teile_api.py`
- Keine Code-Duplikate

---

## 🔄 NÄCHSTE SCHRITTE

### Optional (niedrige Priorität):

1. **API-Integration** (falls RepDoc API verfügbar)
   - Direkte API-Anbindung statt Scraping
   - Schneller und zuverlässiger

2. **Caching**
   - Suchergebnisse cachen (z.B. Redis)
   - Reduziert Selenium-Aufrufe

3. **Frontend-Integration**
   - Checkbox "RepDoc einbeziehen" im Frontend
   - Standardmäßig aktivieren (falls gewünscht)

4. **Error-Handling verbessern**
   - Detailliertere Fehlermeldungen
   - Retry-Logik bei Login-Fehlern

---

## 📚 RELEVANTE DATEIEN

- `tools/scrapers/repdoc_scraper.py` - RepDoc Scraper
- `api/teile_api.py` - Teile-API (Integration)
- `docs/REPDOC_INTEGRATION_TAG215.md` - Diese Dokumentation

**Referenzen:**
- `tools/scrapers/schaeferbarthold_scraper_v3.py` - Ähnlicher Scraper
- `tools/scrapers/dello_scraper.py` - Ähnlicher Scraper
- `docs/ANALYSE_HOTAS_INTEGRATION_DRIVE_TAG209.md` - Ähnliche Integration

---

## ✅ CHECKLISTE

- [x] RepDoc-Scraper erstellt
- [x] Integration in `teile_api.py`
- [x] Zugangsdaten aus Umgebungsvariablen
- [x] Dokumentation erstellt
- [ ] **Testing erforderlich** (Login + Suche)
- [ ] Frontend-Integration (optional)
- [ ] Performance-Tests

---

**Status:** ✅ **Implementiert** - Testing erforderlich  
**Nächster Schritt:** Scraper testen und Login/Suche validieren
