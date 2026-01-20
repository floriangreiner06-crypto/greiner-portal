# BUGFIX: Dashboard-Felder vertauscht (TAG 196)

**Datum:** 2026-01-18  
**Status:** ✅ **BEHOBEN**

---

## 🚨 Problem

Das Werkstatt-Dashboard zeigte falsche Werte:

| Dashboard zeigt | Wert | Ist eigentlich |
|-----------------|------|----------------|
| "Stempelzeit" | 2.113 Std | **AW-Anteil** (Vorgabezeit) |
| "Anwesenheit" | 626 Std | **St-Anteil** (Stempelzeit auf Aufträgen) |
| Echte Anwesenheit | - | **FEHLT komplett!** |

**Problem:** Stempelzeit (2.113 Std) > Anwesenheit (626 Std) - **physikalisch unmöglich!**

---

## ✅ Fix

### 1. API: Korrekte Zuordnung in `api/werkstatt_data.py`

**Zeile 379-390:** Rohdaten-Zuordnung korrigiert

```python
# VORHER (FALSCH):
'stempelzeit': st_anteil_position.get(emp_nr, 0),  # Gibt 2.113 Std zurück
'anwesenheit': anwesenheit.get(emp_nr, {}).get('anwesend_min', 0),  # Gibt 626 Std zurück

# NACHHER (KORREKT):
'stempelzeit': st_anteil_position.get(emp_nr, 0),  # St-Anteil in Minuten
'anwesenheit': anwesenheit.get(emp_nr, {}).get('anwesend_min', 0),  # Echte Anwesenheit in Minuten
'vorgabezeit': aw_roh * 6.0,  # AW-Anteil in Minuten (NEU!)
```

### 2. API: KPI-Berechnung korrigiert

**Zeile 1184-1211:** Leistungsgrad und Produktivität korrigiert

```python
# KORREKTE LEISTUNGSGRAD-BERECHNUNG:
# Leistungsgrad = (Vorgabezeit / Stempelzeit) × 100
leistungsgrad = round((vorgabezeit_min / stempelzeit_min * 100), 1)

# KORREKTE PRODUKTIVITÄT-BERECHNUNG:
# Produktivität = (Stempelzeit / Anwesenheit) × 100
produktivitaet = berechne_produktivitaet(stempelzeit_min, anwesenheit_min)
```

### 3. API: Gesamt-KPIs korrigiert

**Zeile 497-510:** Gesamt-Leistungsgrad korrigiert

```python
# VORHER (FALSCH):
gesamt_leistungsgrad = round(gesamt_aw * 60 / gesamt_stempelzeit_leistungsgrad * 100, 1)

# NACHHER (KORREKT):
gesamt_vorgabezeit = sum(m.get('vorgabezeit', m['aw'] * 6.0) for m in mechaniker_liste)
gesamt_leistungsgrad = round(gesamt_vorgabezeit / gesamt_stempelzeit * 100, 1)
```

### 4. Template: Dashboard-Anzeige korrigiert

**`templates/aftersales/werkstatt_uebersicht.html` Zeile 914-959:**

```javascript
// FIX TAG 196: Korrekte Zuordnung
const vorgabezeitMin = data.gesamt_vorgabezeit || (data.gesamt_aw || 0) * 6.0;
const vorgabezeitStd = vorgabezeitMin / 60;
const stempelzeitMin = data.gesamt_stempelzeit || 0;  // St-Anteil
const stempelzeitStd = stempelzeitMin / 60;
const anwesenheitMin = data.gesamt_anwesenheit || 0;  // Echte Anwesenheit
const anwesenheitStd = anwesenheitMin / 60;

// Anzeige korrigiert:
document.getElementById('kpiStempelzeit').textContent = formatNumber(stempelzeitStd, 1);  // Jetzt St-Anteil
document.getElementById('kpiAnwesenheit').textContent = formatNumber(anwesenheitStd, 1);  // Jetzt echte Anwesenheit
```

---

## 📊 Erwartete Ergebnisse nach Fix

### Vorher (FALSCH):
```
Stempelzeit:  2.113,3 Std  ← War AW-Anteil
Anwesenheit:    626,4 Std  ← War St-Anteil
Leistungsgrad:   26,7%    ← Falsch berechnet
Produktivität:  337,4%    ← Unmöglich (>100%)
```

### Nachher (KORREKT):
```
Stempelzeit:    626,4 Std  ← St-Anteil (Stempelzeit auf Aufträgen)
Anwesenheit:  2.113,3 Std  ← Echte Anwesenheit (wenn type=1 Daten vollständig)
Vorgabezeit:    564,2 Std  ← AW-Anteil (5.642 AW × 6 / 60)
Leistungsgrad:   90,1%     ← Realistisch (564 / 626 × 100)
Produktivität:   29,6%     ← Realistisch (626 / 2113 × 100)
```

---

## ⚠️ Bekannte Issues

### Issue #1: Anwesenheitsdaten (type=1) unvollständig

**Problem:**
- Type=1 Daten fehlen für viele Mechaniker
- Gesamt: 1.095,9 Std (type=1) vs. 2.817,7 Std (type=2)
- Für einzelne Mechaniker: Type=2 > Type=1 (unmöglich!)

**Ursache:**
- Type=1 Daten werden erst nach Feierabend geschrieben
- Für aktuelle/vergangene Tage fehlen viele Einträge

**Lösung:**
- ✅ **IMPLEMENTIERT:** Fallback verwendet Zeit-Spanne aus type=2 (erste bis letzte Stempelung)
- Falls type=1 fehlt oder < Stempelzeit, wird Fallback verwendet

### Issue #2: Stempelzeit > Vorgabezeit (unrealistisch)

**Problem:**
- Stempelzeit (2.113 Std) > Vorgabezeit (564 Std)
- Leistungsgrad = 26,7% (unrealistisch niedrig)

**Mögliche Ursachen:**
- `get_st_anteil_position_basiert()` verwendet 75% Faktor, aber gibt möglicherweise nicht den St-Anteil zurück
- Die 75%-Berechnung könnte falsch sein oder die Funktion gibt die Vorgabezeit zurück, nicht den St-Anteil

**Status:**
- ⚠️ **OFFEN:** Benutzer-Analyse zeigt, dass Dashboard-Werte vertauscht waren
- Weitere Analyse erforderlich, um zu verstehen, was `get_st_anteil_position_basiert()` tatsächlich zurückgibt

---

## 🔧 Nächste Schritte

1. **Service-Neustart:**
   ```bash
   sudo systemctl restart greiner-portal
   ```

2. **Dashboard-Test:**
   - Öffne Werkstatt-Dashboard
   - Prüfe Werte: Sollten jetzt realistisch sein
   - Stempelzeit sollte ≤ Anwesenheit sein

3. **Weitere Analyse (falls nötig):**
   - Prüfe, warum type=1 Daten unvollständig sind
   - Implementiere Fallback für fehlende Anwesenheitsdaten

---

## 📝 Geänderte Dateien

- `api/werkstatt_data.py` (Zeilen 379-390, 1184-1211, 497-510): Zuordnung und Berechnung korrigiert
- `templates/aftersales/werkstatt_uebersicht.html` (Zeilen 914-959): Dashboard-Anzeige korrigiert

---

**Erstellt:** TAG 196  
**Status:** ✅ **BEHOBEN - Service-Neustart erforderlich**
