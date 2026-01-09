# Refactoring Start-Plan TAG 176

**Datum:** 2026-01-09  
**Ziel:** Systematische Bereinigung und SSOT-Migration

---

## 🎯 EMPFOHLENE REIHENFOLGE

### Phase 1: Quick Wins (30-60 Min) - SOFORT STARTEN ✅

**Warum zuerst:**
- Schnell, risikoarm
- Schafft Klarheit
- Keine Code-Änderungen nötig

#### 1.1 Doppelte Dateien bereinigen

**Status-Check:**
- ✅ `standort_utils.py` = `api/standort_utils.py` (identisch, kann gelöscht werden)
- ⚠️ `vacation_api.py` ≠ `api/vacation_api.py` (unterschiedlich, prüfen!)
- ⚠️ `gewinnplanung_v2_*.py` (Root) vs `api/` oder `routes/` (prüfen!)

**Aktionen:**
1. Alle Root-Dateien mit `diff` gegen korrekte Location prüfen
2. Identische Dateien: Root-Version löschen
3. Unterschiedliche Dateien: Merge-Strategie definieren
4. Git-History prüfen um zu verstehen warum Duplikate entstanden

**Erwartetes Ergebnis:**
- Klare Struktur
- Keine Verwirrung mehr bei Imports
- ~7-9 Dateien bereinigt

---

### Phase 2: SSOT-Migration (2-3 Stunden) - NACH PHASE 1

**Warum danach:**
- Basiert auf bereinigter Struktur
- Systematische Migration
- Testbar

#### 2.1 BETRIEB_NAMEN zentralisieren

**Problem:** `BETRIEB_NAMEN` wird in 3+ Dateien definiert.

**Aktion:**
1. `BETRIEB_NAMEN` in `api/standort_utils.py` hinzufügen
2. Als Alias für `STANDORT_NAMEN` oder separate Konstante
3. Alle Module auf zentrale Definition umstellen:
   - `api/werkstatt_data.py`
   - `api/werkstatt_live_api.py`
   - `utils/locosoft_helpers.py`

**Erwartetes Ergebnis:**
- Eine zentrale Definition von `BETRIEB_NAMEN`
- Alle Module importieren aus `standort_utils.py`

---

#### 2.2 STANDORT_NAMEN Migration

**Problem:** 10+ Dateien definieren eigene `STANDORT_NAMEN`.

**Priorität:**
1. **HOCH:** APIs die aktiv verwendet werden
   - `api/gewinnplanung_v2_gw_data.py`
   - `api/abteilungsleiter_planung_data.py`
   - `api/stundensatz_kalkulation_api.py`

2. **MITTEL:** Scripts und Utilities
   - `scripts/vergleiche_bwa_csv.py`
   - `routes/planung_routes.py`

3. **NIEDRIG:** Templates (JavaScript)
   - `templates/planung/v2/gw_planung_gesamt.html`
   - (Später: API-Endpunkt für Standort-Namen)

**Aktion pro Datei:**
1. Import hinzufügen: `from api.standort_utils import STANDORT_NAMEN, get_standort_name`
2. Lokale Definition entfernen
3. Verwendungen auf `STANDORT_NAMEN` oder `get_standort_name()` umstellen
4. Testen!

---

### Phase 3: DB-Verbindungen (1-2 Stunden) - NACH PHASE 2

**Warum danach:**
- Weniger kritisch als SSOT
- Kann parallel zu Phase 2 gemacht werden

#### 3.1 get_db() Redundanzen entfernen

**Aktion:**
1. Alle lokalen `get_db()` Funktionen identifizieren
2. Durch `from api.db_connection import get_db` ersetzen
3. Oder besser: `db_session()` Context Manager verwenden

**Betroffene Dateien:**
- `routes/controlling_routes.py`
- `scheduler/routes.py`
- `send_daily_tek.py`
- `scripts/send_*.py`
- `models/carloop_models.py`
- `reports/registry.py`

---

### Phase 4: Enforcement (Optional, aber empfohlen)

**Warum:**
- Verhindert zukünftige Probleme
- Automatische Prüfung

**Aktionen:**
1. Pre-Commit-Hook: Prüft auf SSOT-Verstöße
2. Linter-Regel: Warnt bei eigenen Standort-Definitionen
3. Code-Review-Checkliste: SSOT-Verwendung prüfen

---

## 📋 KONKRETE ERSTE SCHRITTE (JETZT STARTEN)

### Schritt 1: Doppelte Dateien prüfen (10 Min)

```bash
# Alle Root-Dateien gegen korrekte Location prüfen
diff -q standort_utils.py api/standort_utils.py
diff -q vacation_api.py api/vacation_api.py
diff -q gewinnplanung_v2_gw_api.py api/gewinnplanung_v2_gw_api.py
diff -q gewinnplanung_v2_gw_data.py api/gewinnplanung_v2_gw_data.py
diff -q gewinnplanung_v2_routes.py routes/gewinnplanung_v2_routes.py
diff -q abteilungsleiter_planung_data.py api/abteilungsleiter_planung_data.py
```

### Schritt 2: Identische Dateien löschen (5 Min)

```bash
# Nur wenn identisch!
rm standort_utils.py  # ✅ Identisch bestätigt
```

### Schritt 3: Unterschiedliche Dateien analysieren (15 Min)

- `vacation_api.py` vs `api/vacation_api.py` - Welche ist aktuell?
- Git-History prüfen
- Merge-Strategie definieren

### Schritt 4: BETRIEB_NAMEN zentralisieren (30 Min)

1. `api/standort_utils.py` erweitern
2. Erste Datei migrieren (z.B. `api/werkstatt_data.py`)
3. Testen
4. Weitere Dateien migrieren

---

## ✅ ERFOLGSKRITERIEN

### Phase 1 (Quick Wins):
- [ ] Alle identischen Root-Dateien gelöscht
- [ ] Unterschiedliche Dateien analysiert und bereinigt
- [ ] Git-Status sauber

### Phase 2 (SSOT-Migration):
- [ ] `BETRIEB_NAMEN` zentralisiert
- [ ] Alle APIs verwenden `standort_utils.py`
- [ ] Keine lokalen `STANDORT_NAMEN` Definitionen mehr
- [ ] Tests laufen durch

### Phase 3 (DB-Verbindungen):
- [ ] Alle lokalen `get_db()` entfernt
- [ ] `db_session()` Context Manager überall verwendet
- [ ] Keine Memory Leaks mehr

---

## 🚨 RISIKEN & MITIGATION

### Risiko 1: Breaking Changes
**Mitigation:** Schrittweise Migration, nach jedem Schritt testen

### Risiko 2: Import-Fehler
**Mitigation:** Alle Imports prüfen, Import-Pfade dokumentieren

### Risiko 3: Templates brechen
**Mitigation:** Templates zuletzt migrieren, API-Endpunkt für Standort-Namen

---

## 📊 ZEITSCHÄTZUNG

- **Phase 1 (Quick Wins):** 30-60 Min
- **Phase 2 (SSOT-Migration):** 2-3 Stunden
- **Phase 3 (DB-Verbindungen):** 1-2 Stunden
- **Phase 4 (Enforcement):** Optional, 1-2 Stunden

**Gesamt:** ~4-6 Stunden für Phasen 1-3

---

## 🎯 EMPFOHLENER START

**JETZT STARTEN MIT:**
1. ✅ Doppelte Dateien prüfen (10 Min)
2. ✅ Identische Dateien löschen (5 Min)
3. ✅ BETRIEB_NAMEN zentralisieren (30 Min)

**Das gibt uns:**
- Klare Struktur
- Erste SSOT-Migration
- Quick Win für Motivation

---

**Status:** ✅ Plan erstellt - Bereit zum Start!
