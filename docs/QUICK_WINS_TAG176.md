# Quick Wins - Schnell und gefahrlos fixbar (TAG 176)

**Datum:** 2026-01-09  
**Ziel:** Kritische Probleme schnell fixen, ohne Risiko  
**Zeitrahmen:** Vor User-Testing am Montag

---

## ✅ QUICK WINS (Schnell & Gefahrlos)

### 1. Doppelte identische Dateien löschen ⏱️ 5 Min

**Status:** ✅ Identisch bestätigt, kein Risiko

#### 1.1 `standort_utils.py` (Root) löschen
- ✅ Identisch mit `api/standort_utils.py`
- ✅ Keine Imports verwenden Root-Version
- ✅ Alle Imports: `from api.standort_utils import ...`
- **Risiko:** ❌ Kein Risiko - identisch, nicht verwendet

**Aktion:**
```bash
rm /opt/greiner-portal/standort_utils.py
```

---

#### 1.2 `gewinnplanung_v2_gw_api.py` (Root) löschen
- ✅ Identisch mit `api/gewinnplanung_v2_gw_api.py`
- ✅ `app.py` importiert: `from api.gewinnplanung_v2_gw_api import ...`
- **Risiko:** ❌ Kein Risiko - identisch, nicht verwendet

**Aktion:**
```bash
rm /opt/greiner-portal/gewinnplanung_v2_gw_api.py
```

---

### 2. vacation_api.py Jahr-Problem fixen ⏱️ 15 Min ⚠️ VORSICHT

**Status:** ⚠️ Unterschiedlich, aber Root-Version hat wichtige Fixes

**Problem:**
- API-Version: `year = request.args.get('year', 2025, type=int)` (6x hardcoded)
- Root-Version: `year = request.args.get('year', datetime.now().year, type=int)` (6x korrekt)
- **→ Erklärt Bug: "Jahr-Übergang funktioniert nicht"**

**Unterschiede:**
- ✅ Root hat `datetime.now().year` (korrekt für 2026/2027)
- ✅ Root hat mehr Debug-Logging
- ⚠️ Root ist 9 Tage neuer

**Risiko:** ⚠️ Mittel - könnte andere Änderungen haben

**Empfehlung:**
1. **Option A (Sicher):** Nur Jahr-Fixes übernehmen (6 Zeilen ändern)
2. **Option B (Schnell):** Root-Version komplett kopieren (aber erst prüfen!)

**Aktion (Option A - Sicher):**
```python
# In api/vacation_api.py, 6 Stellen ändern:
# VORHER:
year = request.args.get('year', 2025, type=int)

# NACHHER:
year = request.args.get('year', datetime.now().year, type=int)
```

**Stellen:**
- Zeile 856: `/my-balance`
- Zeile 990: `/my-team`
- Zeile 1440: `/all-bookings`
- Zeile 1541: `/my-bookings`
- Zeile 1688: `/requests`
- Zeile 1812: `/approver-summary`

---

## ⚠️ MITTLERE RISIKEN (Nur mit Prüfung)

### 3. Weitere doppelte Dateien prüfen ⏱️ 10 Min

**Status:** ⚠️ Nicht geprüft

#### 3.1 `gewinnplanung_v2_gw_data.py` (Root)
- ⚠️ Nicht geprüft
- **Aktion:** Erst diff prüfen, dann entscheiden

#### 3.2 `gewinnplanung_v2_routes.py` (Root)
- ⚠️ Nicht geprüft
- **Aktion:** Erst diff prüfen, dann entscheiden

#### 3.3 Templates im Root
- ⚠️ Nicht geprüft
- **Aktion:** Erst prüfen welche verwendet werden

---

## ❌ NICHT JETZT (Refactoring später)

### 4. SSOT-Migration
- ⏱️ 2-3 Stunden
- ⚠️ Risiko: Breaking Changes
- **→ Auf TODO für später**

### 5. get_db() Redundanzen
- ⏱️ 1-2 Stunden
- ⚠️ Risiko: DB-Verbindungen
- **→ Auf TODO für später**

### 6. SQL-Syntax standardisieren
- ⏱️ 2-3 Stunden
- ⚠️ Risiko: SQL-Fehler
- **→ Auf TODO für später**

---

## 📋 EMPFOHLENE REIHENFOLGE (Heute)

### Phase 1: Quick Wins (20 Min) ✅

1. ✅ `standort_utils.py` (Root) löschen - 2 Min
2. ✅ `gewinnplanung_v2_gw_api.py` (Root) löschen - 2 Min
3. ✅ `vacation_api.py` Jahr-Fixes (Option A) - 15 Min
   - 6 Zeilen ändern: `2025` → `datetime.now().year`
   - Service neu starten
   - Testen

**Erwartetes Ergebnis:**
- ✅ Jahr-Problem behoben (2026/2027 funktionieren)
- ✅ Doppelte Dateien bereinigt
- ✅ Kein Risiko

---

### Phase 2: Prüfung (10 Min) ⚠️ Optional

4. ⚠️ Weitere doppelte Dateien prüfen
   - `gewinnplanung_v2_gw_data.py`
   - `gewinnplanung_v2_routes.py`
   - Templates

**Nur wenn Zeit:** Prüfen und ggf. bereinigen

---

## 🎯 KONKRETE AKTIONEN (Jetzt)

### 1. standort_utils.py löschen
```bash
cd /opt/greiner-portal
rm standort_utils.py
```

### 2. gewinnplanung_v2_gw_api.py löschen
```bash
cd /opt/greiner-portal
rm gewinnplanung_v2_gw_api.py
```

### 3. vacation_api.py Jahr-Fixes
```python
# In api/vacation_api.py, 6 Stellen ändern:
# Zeile 856, 990, 1440, 1541, 1688, 1812

# VORHER:
year = request.args.get('year', 2025, type=int)

# NACHHER:
year = request.args.get('year', datetime.now().year, type=int)
```

**Wichtig:** `datetime` muss importiert sein (ist bereits da: `from datetime import datetime`)

---

## ✅ ERFOLGSKRITERIEN

### Nach Quick Wins:
- [ ] `standort_utils.py` (Root) gelöscht
- [ ] `gewinnplanung_v2_gw_api.py` (Root) gelöscht
- [ ] `vacation_api.py` hat `datetime.now().year` (6x)
- [ ] Service neu gestartet
- [ ] Urlaubsplaner zeigt 2026 korrekt an
- [ ] Keine Import-Fehler

---

## 🚨 WICHTIGE HINWEISE

1. **NICHT alles auf einmal!**
   - Schrittweise vorgehen
   - Nach jedem Schritt testen

2. **Backup erstellen:**
   ```bash
   cp api/vacation_api.py api/vacation_api.py.backup_tag176
   ```

3. **Service neu starten nach Änderungen:**
   ```bash
   sudo systemctl restart greiner-portal
   ```

4. **Logs prüfen:**
   ```bash
   journalctl -u greiner-portal -f
   ```

---

## 📊 ZEITSCHÄTZUNG

- **Phase 1 (Quick Wins):** 20 Min
- **Phase 2 (Prüfung):** 10 Min (optional)
- **Gesamt:** 20-30 Min

---

**Status:** ✅ Plan erstellt - Bereit für Quick Wins!
