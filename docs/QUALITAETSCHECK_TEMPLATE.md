# Qualitätscheck-Template für Neuentwicklungen

**Datum:** [DATUM]  
**TAG:** [TAG-NUMMER]  
**Feature/Änderung:** [BESCHREIBUNG]

---

## 🔍 QUALITÄTSCHECK

### 1. Redundanzen

#### Doppelte Dateien
- [ ] Geprüft: Gibt es doppelte Dateien?
- [ ] Ergebnis: [BESCHREIBUNG]
- [ ] Aktion: [WAS WURDE GEMACHT]

**Beispiel:**
- ❌ Gefunden: `standort_utils.py` in Root und `api/`
- ✅ Aktion: Root-Version gelöscht, `api/standort_utils.py` ist SSOT

#### Doppelte Funktionen
- [ ] Geprüft: Gibt es doppelte Funktionen?
- [ ] Ergebnis: [BESCHREIBUNG]
- [ ] Aktion: [WAS WURDE GEMACHT]

**Beispiel:**
- ❌ Gefunden: Lokale `get_db()` in `routes/controlling_routes.py`
- ✅ Aktion: Entfernt, verwendet `api/db_connection.get_db()`

#### Doppelte Mappings/Konstanten
- [ ] Geprüft: Gibt es doppelte Mappings?
- [ ] Ergebnis: [BESCHREIBUNG]
- [ ] Aktion: [WAS WURDE GEMACHT]

**Beispiel:**
- ❌ Gefunden: `STANDORTE` in `gw_planung_gesamt.html` (JavaScript)
- ✅ Aktion: Sollte `api/standort_utils.py` verwenden

---

### 2. SSOT-Konformität

#### Zentrale Funktionen verwendet?
- [ ] Standort-Logik: `api/standort_utils.py` verwendet?
- [ ] DB-Verbindungen: `api/db_connection.py` / `api/db_utils.py` verwendet?
- [ ] Lagerbestand: `api/teile_stock_utils.py` verwendet? (falls relevant)
- [ ] Andere: [BESCHREIBUNG]

**Beispiel:**
- ✅ Standort-Filter: Verwendet `api/standort_utils.get_subsidiary_filter()`
- ❌ Lagerbestand: Eigene Query statt `api/teile_stock_utils.get_stock_level_for_subsidiary()`

#### Lokale Implementierungen statt SSOT?
- [ ] Geprüft: Gibt es lokale Implementierungen?
- [ ] Ergebnis: [BESCHREIBUNG]
- [ ] Aktion: [WAS WURDE GEMACHT]

---

### 3. Code-Duplikate

#### Kopierte Code-Blöcke
- [ ] Geprüft: Gibt es kopierte Code-Blöcke?
- [ ] Ergebnis: [BESCHREIBUNG]
- [ ] Aktion: [WAS WURDE GEMACHT]

**Beispiel:**
- ❌ Gefunden: Gleiche Error-Handling-Logik in 3 Dateien
- ✅ Aktion: In `api/db_utils.py` als Funktion ausgelagert

---

### 4. Konsistenz

#### DB-Verbindungen
- [ ] PostgreSQL: `get_db()` verwendet?
- [ ] Locosoft: `get_locosoft_connection()` verwendet?
- [ ] SQL-Syntax: PostgreSQL-kompatibel? (`%s`, `true`, `CURRENT_DATE`)

#### Imports
- [ ] Zentrale Utilities importiert?
- [ ] Konsistente Import-Struktur?

#### Error-Handling
- [ ] Konsistentes Pattern? (try/except/finally)
- [ ] Logging verwendet?

---

### 5. Dokumentation

- [ ] Neue Features dokumentiert?
- [ ] API-Endpoints dokumentiert?
- [ ] Breaking Changes dokumentiert?
- [ ] Code-Kommentare vorhanden?

---

## ✅ ERGEBNIS

### Gefundene Probleme
1. [PROBLEM 1]
2. [PROBLEM 2]
3. [PROBLEM 3]

### Behobene Probleme
1. ✅ [PROBLEM 1] - [LÖSUNG]
2. ✅ [PROBLEM 2] - [LÖSUNG]

### Offene Probleme
1. ⚠️ [PROBLEM 1] - [GRUND]
2. ⚠️ [PROBLEM 2] - [GRUND]

---

## 📝 EMPFEHLUNGEN

1. [EMPFOHLUNG 1]
2. [EMPFOHLUNG 2]
3. [EMPFOHLUNG 3]

---

**Status:** ✅ Qualitätscheck abgeschlossen  
**Nächste Schritte:** [WAS SOLLTE ALS NÄCHSTES GEMACHT WERDEN]
