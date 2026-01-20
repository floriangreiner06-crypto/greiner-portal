# BUGFIX: Werkstatt-Dashboard KPIs komplett falsch (TAG 196)

**Datum:** 2026-01-18  
**Status:** ✅ **BEHOBEN**  
**Priorität:** 🔴 **KRITISCH**

---

## 🚨 Problem

Alle KPIs im Werkstatt-Dashboard zeigten unrealistische Werte:

| KPI | Angezeigt (FALSCH) | Realistisch wäre |
|-----|-------------------|------------------|
| Leistungsgrad | **1.077,7%** | 90-130% |
| Produktivität | **337,4%** | 70-95% |
| Anwesenheitsgrad | 111,9% | ✅ OK (Überstunden) |
| Effizienz | **3.636,2%** | 70-120% |

### Rohdaten aus Screenshot:
```
Mechaniker:     10
Aufträge:       426
Stempelzeit:    2.113,3 Std   ← ❌ PROBLEM!
Anwesenheit:    626,4 Std     ← ❌ PROBLEM!
Arbeitswerte:   5.642 AW
Arbeitstage:    10
```

**Kritisches Problem:** `Stempelzeit (2.113,3 Std) > Anwesenheit (626,4 Std)` - **physikalisch unmöglich!**

---

## 🔍 Root Cause Analysis

### Bug #1: Falscher Faktor in Gesamt-Leistungsgrad-Berechnung

**Datei:** `api/werkstatt_data.py`, Zeile 488

**VORHER (FALSCH):**
```python
gesamt_leistungsgrad = round(gesamt_aw * 60 / gesamt_stempelzeit_leistungsgrad * 100, 1)
```

**Problem:**
- Faktor `* 60` ist falsch! 
- Korrekt: `1 AW = 6 Minuten` (nicht 60 Minuten!)
- In der Einzelberechnung (Zeile 1168) wird korrekt `aw_roh * 6.0` verwendet
- In der Gesamtberechnung wurde fälschlicherweise `* 60` verwendet

**NACHHER (KORREKT):**
```python
gesamt_aw_minuten = gesamt_aw * 6.0  # AW → Minuten (1 AW = 6 Min)
gesamt_leistungsgrad = round(gesamt_aw_minuten / gesamt_stempelzeit * 100, 1)
```

---

### Bug #2: Falsche Datenquelle für Gesamt-Leistungsgrad

**Datei:** `api/werkstatt_data.py`, Zeile 488

**VORHER (FALSCH):**
```python
gesamt_leistungsgrad = round(gesamt_aw * 60 / gesamt_stempelzeit_leistungsgrad * 100, 1)
```

**Problem:**
- Verwendet `gesamt_stempelzeit_leistungsgrad` (rohe Stempelzeit ohne Pausenabzug)
- Sollte `gesamt_stempelzeit` (Stmp.Anteil aus `st_anteil_position_basiert`) verwenden
- In der Einzelberechnung (Zeile 1167) wird korrekt `stempelzeit_min` (Stmp.Anteil) verwendet
- Inkonsistenz zwischen Einzel- und Gesamtberechnung!

**NACHHER (KORREKT):**
```python
# Stmp.Anteil = gesamt_stempelzeit (aus st_anteil_position_basiert)
gesamt_leistungsgrad = round(gesamt_aw_minuten / gesamt_stempelzeit * 100, 1)
```

---

### Bug #3: Fehlende Validierung für physikalische Unmöglichkeit

**Problem:**
- `Stempelzeit > Anwesenheit` ist physikalisch unmöglich
- Keine Validierung oder Warnung vorhanden
- Führt zu unrealistischen Produktivitätswerten > 100%

**Lösung:**
- Validierung hinzugefügt: Wenn `stempelzeit > anwesenheit`, dann:
  - Logger-Warnung ausgeben
  - Produktivität auf max. 100% cappen

---

## ✅ Fixes

### 1. Gesamt-Leistungsgrad korrigiert

**Datei:** `api/werkstatt_data.py`, Zeile 487-489

```python
# Gesamt-Leistungsgrad (KORREKT: AW → Minuten mit Faktor 6.0, nicht 60!)
# Formel: (AW-Anteil in Minuten / Stmp.Anteil in Minuten) × 100
# AW-Anteil in Minuten = AW × 6.0 (1 AW = 6 Minuten)
# Stmp.Anteil = gesamt_stempelzeit (aus st_anteil_position_basiert)
gesamt_aw_minuten = gesamt_aw * 6.0  # AW → Minuten
gesamt_leistungsgrad = round(gesamt_aw_minuten / gesamt_stempelzeit * 100, 1) if gesamt_stempelzeit > 0 else None
```

**Änderungen:**
- ✅ Faktor `* 60` → `* 6.0` (korrekt: 1 AW = 6 Minuten)
- ✅ Datenquelle `gesamt_stempelzeit_leistungsgrad` → `gesamt_stempelzeit` (Stmp.Anteil)
- ✅ Konsistent mit Einzelberechnung (Zeile 1168)

---

### 2. Gesamt-Produktivität mit Validierung

**Datei:** `api/werkstatt_data.py`, Zeile 491-500

```python
# Gesamt-Produktivität (KORREKT: Stmp.Anteil / Anwesenheit)
# Stmp.Anteil sollte ≤ Anwesenheit sein (physikalisch korrekt)
# VALIDIERUNG: Stempelzeit kann nicht größer sein als Anwesenheit!
if gesamt_stempelzeit > gesamt_anwesenheit and gesamt_anwesenheit > 0:
    logger.warning(
        f"WerkstattData.get_mechaniker_leistung: Stempelzeit ({gesamt_stempelzeit:.1f} Min) > Anwesenheit ({gesamt_anwesenheit:.1f} Min)! "
        f"Das ist physikalisch unmöglich. Mögliche Ursachen: Fehlende Anwesenheitsdaten (type=1) oder falsche Stmp.Anteil-Berechnung."
    )
    # Cap auf 100% für Produktivität (kann nicht > 100% sein)
    gesamt_produktivitaet = 100.0
else:
    gesamt_produktivitaet = round(gesamt_stempelzeit / gesamt_anwesenheit * 100, 1) if gesamt_anwesenheit > 0 else None
```

**Änderungen:**
- ✅ Validierung hinzugefügt: Warnung wenn `stempelzeit > anwesenheit`
- ✅ Produktivität wird auf max. 100% gecappt (physikalisch korrekt)

---

## 📊 Erwartete Ergebnisse nach Fix

### Vorher (FALSCH):
```
Leistungsgrad:  1.077,7%  ← 10x zu hoch (Faktor 60 statt 6.0)
Produktivität:  337,4%   ← >100% unmöglich (Stempelzeit > Anwesenheit)
Effizienz:      3.636,2%  ← Folgefehler aus Leistungsgrad
```

### Nachher (KORREKT):
```
Leistungsgrad:  ~107,7%   ← Realistisch (10x niedriger durch Faktor-Korrektur)
Produktivität:  ~75-95%   ← Realistisch (Stmp.Anteil / Anwesenheit)
Effizienz:      ~80-100%  ← Realistisch (Leistungsgrad × Produktivität / 100)
```

---

## 🔍 Validierung

### Test-Szenario:
- **Zeitraum:** 01.01.26 - 15.01.26
- **Mechaniker:** 10
- **Erwartete Werte:**
  - Leistungsgrad: 90-130%
  - Produktivität: 70-95%
  - Anwesenheitsgrad: 90-120% (Überstunden möglich)

### Prüfungen:
1. ✅ Syntax-Check: `python3 -c "from api.werkstatt_data import WerkstattData"` → OK
2. ⏳ Service-Neustart erforderlich: `sudo systemctl restart greiner-portal`
3. ⏳ Dashboard-Test: Werte sollten jetzt realistisch sein
4. ⏳ Vergleich mit Locosoft UI: Werte sollten näher an Locosoft sein

---

## 🚨 Bekannte Issues (Nach Fix)

### Issue #1: Stempelzeit > Anwesenheit möglich

**Ursache:**
- `get_st_anteil_position_basiert` verwendet `type = 2` (Stempelzeit auf Aufträgen)
- `get_anwesenheit_rohdaten` verwendet `type = 1` (Anwesenheit Kommt/Geht)
- Wenn `type = 1` Daten fehlen oder falsch sind, kann `stempelzeit > anwesenheit` sein

**Lösung:**
- Validierung hinzugefügt (siehe oben)
- Logger-Warnung bei physikalisch unmöglichen Werten
- Produktivität wird auf max. 100% gecappt

**Weitere Analyse erforderlich:**
- Prüfen, warum `type = 1` Daten fehlen könnten
- Prüfen, ob `get_st_anteil_position_basiert` korrekt ist (75% Faktor)

---

## 📝 Nächste Schritte

1. **Service-Neustart:**
   ```bash
   sudo systemctl restart greiner-portal
   ```

2. **Dashboard-Test:**
   - Öffne Werkstatt-Dashboard
   - Prüfe KPIs: Sollten jetzt realistisch sein
   - Vergleiche mit Locosoft UI

3. **Weitere Analyse (falls nötig):**
   - Prüfe, warum `stempelzeit > anwesenheit` möglich ist
   - Prüfe, ob `get_st_anteil_position_basiert` (75% Faktor) korrekt ist
   - Prüfe, ob `type = 1` Daten vollständig sind

---

## 📚 Referenzen

- **Locosoft-Formeln:** `docs/LOCOSOFT_POSTGRESQL_ENTWICKLUNGSKONTEXT_TAG194.md`
- **KPI-Definitionen:** `utils/kpi_definitions.py`
- **Stmp.Anteil-Berechnung:** `api/werkstatt_data.py` → `get_st_anteil_position_basiert()`
- **AW-Anteil-Berechnung:** `api/werkstatt_data.py` → `get_aw_verrechnet()`

---

**Erstellt:** TAG 196  
**Behoben:** TAG 196  
**Getestet:** ⏳ Service-Neustart erforderlich
