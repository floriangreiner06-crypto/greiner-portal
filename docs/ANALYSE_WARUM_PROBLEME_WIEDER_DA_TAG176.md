# Analyse: Warum haben wir wieder Probleme? (TAG 176)

**Datum:** 2026-01-09  
**Kontext:** Qualitätskontrolle hat Redundanzen gefunden, obwohl bereits Refactoring in TAG 164/167/170 stattfand

---

## 📋 WAS WURDE BEREITS GEMACHT?

### TAG 164: Standort-Utils SSOT etabliert
- ✅ `api/standort_utils.py` erstellt als SSOT
- ✅ Zentralisiert aus `serviceberater_api`, `kundenzentrale_api`, `budget_api`
- ✅ Filter-Funktionen für Locosoft und BWA erstellt

### TAG 167: SSOT für BWA und Werkstatt
- ✅ BWA als SSOT für Vorjahreswerte
- ✅ Werkstatt/Teile/Sonstige SSOT (keine Marken-Unterscheidung)
- ✅ YTD direkt aus BWA (SSOT)

### TAG 170: Standort-Utils erweitert
- ✅ BWA- und Locosoft-Filter-Funktionen erweitert
- ✅ Dokumentation `docs/STANDORT_LOGIK_SSOT.md` erstellt

---

## 🔍 WARUM SIND DIE PROBLEME WIEDER DA?

### 1. **Unvollständige Migration** ❌

**Problem:** Nicht alle Module wurden auf SSOT umgestellt.

**Beispiele:**
- `api/gewinnplanung_v2_gw_data.py` - Definiert noch eigenes `STANDORT_NAMEN`
- `api/abteilungsleiter_planung_data.py` - Definiert noch eigenes `STANDORT_NAMEN`
- `api/stundensatz_kalkulation_api.py` - Definiert noch eigenes `standort_namen`
- `api/werkstatt_data.py` - Definiert noch eigenes `BETRIEB_NAMEN`
- `api/werkstatt_live_api.py` - Definiert noch eigenes `BETRIEB_NAMEN` (2x!)

**Grund:**
- Refactoring wurde nur für **bestimmte Module** durchgeführt
- **Neue Module** wurden ohne SSOT erstellt
- **Alte Module** wurden nicht nachträglich migriert

---

### 2. **Keine Enforcement-Mechanismen** ❌

**Problem:** Es gibt keine automatische Prüfung, ob SSOT verwendet wird.

**Fehlende Mechanismen:**
- ❌ Keine Linter-Regeln
- ❌ Keine Pre-Commit-Hooks
- ❌ Keine Code-Review-Checkliste
- ❌ Keine automatische Prüfung in CI/CD

**Folge:**
- Entwickler können weiterhin eigene Mappings definieren
- Keine Warnung bei SSOT-Verstößen
- Probleme werden erst bei Qualitätskontrolle entdeckt

---

### 3. **Doppelte Dateien nicht bereinigt** ❌

**Problem:** Dateien existieren sowohl im Root als auch in korrekten Verzeichnissen.

**Beispiele:**
- `standort_utils.py` (Root) + `api/standort_utils.py` ✅ Identisch
- `vacation_api.py` (Root) + `api/vacation_api.py` ⚠️ Unklar
- `gewinnplanung_v2_*.py` (Root) + `api/` oder `routes/` ⚠️ Unklar

**Grund:**
- Dateien wurden verschoben, aber Root-Kopien nicht gelöscht
- Git-History zeigt möglicherweise Migration, aber Cleanup fehlte
- Verwirrung: Welche Datei ist die "richtige"?

---

### 4. **Neue Features ohne SSOT** ❌

**Problem:** Neue Module/Features wurden ohne SSOT erstellt.

**Beispiele:**
- `api/gewinnplanung_v2_gw_data.py` (TAG 169) - Neues Feature, eigenes Mapping
- `api/abteilungsleiter_planung_data.py` - Neues Feature, eigenes Mapping
- `templates/planung/v2/gw_planung_gesamt.html` - JavaScript-Mapping im Template

**Grund:**
- Entwickler wussten nicht von SSOT
- Keine Dokumentation im Code
- Keine Code-Review-Prüfung

---

### 5. **Inkonsistente Namenskonventionen** ❌

**Problem:** Verschiedene Namen für gleiche Konzepte.

**Beispiele:**
- `STANDORT_NAMEN` vs `BETRIEB_NAMEN` vs `standort_namen`
- "Deggendorf Opel" vs "Deggendorf" vs "Opel DEG"
- "Deggendorf Hyundai" vs "Hyundai DEG" vs "Hyundai Deg"

**Grund:**
- Keine klare Namenskonvention definiert
- Verschiedene Entwickler, verschiedene Präferenzen
- Keine zentrale Dokumentation

---

### 6. **Templates nicht migriert** ❌

**Problem:** JavaScript in Templates verwendet eigene Mappings.

**Beispiele:**
- `templates/planung/v2/gw_planung_gesamt.html`: `STANDORTE = {1: 'Opel DEG', ...}`
- `routes/planung_routes.py`: `standorte = {1: 'Deggendorf', 3: 'Landau'}`

**Grund:**
- Templates wurden nicht in Refactoring einbezogen
- JavaScript kann nicht direkt Python-Module importieren
- Keine API-Endpunkte für Standort-Namen

---

## 🎯 ROOT CAUSE ANALYSIS

### Hauptursachen:

1. **Refactoring war unvollständig**
   - Nur Teil der Codebase migriert
   - Keine vollständige Inventarisierung aller betroffenen Dateien
   - Keine Migration-Strategie für neue Features

2. **Keine Prozesse/Mechanismen**
   - Keine automatische Prüfung
   - Keine Code-Review-Checkliste
   - Keine Dokumentation für neue Entwickler

3. **Fehlende Dokumentation**
   - SSOT nicht prominent genug dokumentiert
   - Keine "Quick Start" Anleitung
   - Keine Beispiele im Code

4. **Keine Cleanup-Phase**
   - Doppelte Dateien nicht entfernt
   - Alte Code-Pfade nicht bereinigt
   - Keine Validierung nach Refactoring

---

## 💡 LÖSUNGSANSÄTZE

### 1. **Vollständige Migration** ✅

**Aktion:**
- Alle Module identifizieren, die eigene Mappings definieren
- Systematisch auf SSOT umstellen
- Migration dokumentieren

**Priorität:** HOCH

---

### 2. **Enforcement-Mechanismen** ✅

**Aktionen:**
- Pre-Commit-Hook: Prüft auf SSOT-Verstöße
- Linter-Regel: Warnt bei eigenen Standort-Definitionen
- Code-Review-Checkliste: SSOT-Verwendung prüfen

**Priorität:** HOCH

---

### 3. **Cleanup** ✅

**Aktionen:**
- Doppelte Root-Dateien prüfen und löschen
- Git-History analysieren um zu verstehen warum Duplikate entstanden
- Import-Pfade prüfen und korrigieren

**Priorität:** MITTEL

---

### 4. **Dokumentation verbessern** ✅

**Aktionen:**
- SSOT prominent in `CLAUDE.md` dokumentieren
- Code-Beispiele in `standort_utils.py` erweitern
- Quick-Start-Anleitung für neue Features

**Priorität:** MITTEL

---

### 5. **Templates migrieren** ✅

**Aktionen:**
- API-Endpunkt für Standort-Namen erstellen
- Templates auf API umstellen
- JavaScript-Mappings entfernen

**Priorität:** NIEDRIG

---

## 📊 ZUSAMMENFASSUNG

### Warum sind die Probleme wieder da?

1. **Unvollständiges Refactoring** - Nur Teil der Codebase migriert
2. **Keine Enforcement** - Keine automatische Prüfung
3. **Neue Features ohne SSOT** - Entwickler wussten nicht von SSOT
4. **Fehlende Cleanup-Phase** - Doppelte Dateien nicht entfernt
5. **Inkonsistente Namenskonventionen** - Keine klaren Regeln

### Was müssen wir tun?

1. ✅ **Vollständige Migration** - Alle Module auf SSOT umstellen
2. ✅ **Enforcement** - Automatische Prüfung einführen
3. ✅ **Cleanup** - Doppelte Dateien entfernen
4. ✅ **Dokumentation** - SSOT prominent dokumentieren
5. ✅ **Templates** - JavaScript-Mappings entfernen

---

## 🎯 NÄCHSTE SCHRITTE

1. **Sofort:** Doppelte Dateien prüfen und bereinigen
2. **Kurzfristig:** Alle Module auf SSOT umstellen
3. **Mittelfristig:** Enforcement-Mechanismen einführen
4. **Langfristig:** Dokumentation und Prozesse verbessern

---

**Status:** ✅ Analyse abgeschlossen - Root Causes identifiziert
