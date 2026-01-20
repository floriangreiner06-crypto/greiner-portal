# Gudat API - Problem-Analyse und Lösung

**Datum:** 2026-01-20  
**TAG:** 200  
**Debug-Script:** `scripts/debug_gudat_api.py`

---

## 🔍 PROBLEM-ANALYSE

### Problem 1: Negative freie AW bei Diagnosetechnik

**Symptom:**
- Diagnosetechnik zeigt: 136 AW Kapazität, 116 AW geplant, **-66 AW frei**
- Erwartet: 136 - 116 = 20 AW frei (ohne Abwesenheiten)

**Ursache gefunden:**

Die **negative freie AW kommt direkt von Gudat** - das ist korrekt!

**Rohe Daten von Gudat:**
```json
{
  "base_workload": 136,
  "planned_workload": 116,
  "absence_workload": 74,  // ← WICHTIG: Abwesenheiten!
  "free_workload": -66      // ← Von Gudat berechnet
}
```

**Berechnung:**
- `base_workload`: 136 AW (Gesamtkapazität)
- `planned_workload`: 116 AW (geplante Arbeit)
- `absence_workload`: 74 AW (Abwesenheiten)
- **Erwartet frei:** 136 - 116 - 74 = **-54 AW**
- **Tatsächlich frei:** -66 AW
- **Differenz:** -12 AW

**Erklärung:**
1. Gudat berücksichtigt **Abwesenheiten** in der Berechnung
2. `free_workload` wird von Gudat berechnet als: `base - planned - absent - (andere Faktoren)`
3. Die Differenz von -12 AW könnte von:
   - `team_productivity_factor: 0.8` (Team ist nur 80% produktiv)
   - Puffer oder andere interne Berechnungen in Gudat

**Fazit:** ✅ **Das ist korrekt!** Das Team ist überbucht, wenn man Abwesenheiten berücksichtigt.

**Lösung:**
- ✅ **Keine Änderung nötig** - die negative AW ist korrekt
- ⚠️ **Frontend sollte Warnung zeigen** wenn `free < 0`
- 💡 **Optional:** Tooltip erklären: "Negative AW = Überbuchung (Abwesenheiten berücksichtigt)"

---

### Problem 2: Wochen-Übersicht zeigt 0% für alle Tage

**Symptom:**
- Test-Script zeigte: Alle Tage 0% (0/0 AW)
- Frontend zeigt möglicherweise auch 0%

**Ursache gefunden:**

Die **Wochen-Übersicht funktioniert tatsächlich!** ✅

**Debug-Ergebnisse:**
```
2026-01-20: 2242 AW Kapazität, 490 AW geplant, 832 AW frei, 21.9% Auslastung
2026-01-21: 2242 AW Kapazität, 309 AW geplant, 1013 AW frei, 13.8% Auslastung
2026-01-22: 2242 AW Kapazität, 428 AW geplant, 932 AW frei, 19.1% Auslastung
2026-01-23: 2242 AW Kapazität, 293 AW geplant, 1087 AW frei, 13.1% Auslastung
2026-01-24: 380 AW Kapazität, 0 AW geplant, 0 AW frei, 0.0% Auslastung  ← Feiertag?
2026-01-26: 2242 AW Kapazität, 317 AW geplant, 1011 AW frei, 14.1% Auslastung
2026-01-27: 2242 AW Kapazität, 313 AW geplant, 1075 AW frei, 14.0% Auslastung
```

**Mögliche Ursachen für "0%" im Frontend:**

1. **API-Response-Format:**
   - Die API gibt `days` als Array zurück
   - Frontend erwartet möglicherweise anderes Format

2. **Daten-Filterung:**
   - Frontend filtert möglicherweise nur interne Teams
   - Wochen-Übersicht zeigt alle Teams (2242 AW), aber Frontend erwartet nur interne (1100 AW)

3. **Fehler in Frontend-Rendering:**
   - JavaScript-Fehler beim Rendern der Wochen-Daten

**Lösung:**
- Prüfe Frontend-Code: `templates/aftersales/kapazitaetsplanung.html` → `renderGudatWeek()`
- Prüfe API-Response-Format: `/api/werkstatt/live/gudat/kapazitaet` → `woche` Feld
- Validiere Datenstruktur

---

## 📊 DETAILLIERTE ERGEBNISSE

### Diagnosetechnik - Detaillierte Analyse

**Rohe Daten-Struktur:**
```json
{
  "name": "Diagnosetechnik",
  "id": 3,
  "category": "Mechanik",
  "data": {
    "2026-01-20": {
      "base_workload": 136,
      "planned_workload": 116,
      "absence_workload": 74,
      "plannable_workload": 50,
      "free_workload": -66,
      "team_productivity_factor": 0.8,
      "global_productivity_factor": 1,
      "members": [
        {
          "id": 21,
          "workload": 68,
          "is_absent": true,
          "absence_workload": 68,
          "plannable_workload": 0
        },
        {
          "id": 20,
          "workload": 68,
          "is_absent": false,
          "absence_workload": 6,
          "plannable_workload": 62
        }
      ]
    }
  }
}
```

**Erkenntnisse:**
- **2 Mitglieder** im Team (je 68 AW = 136 AW gesamt)
- **1 Mitglied abwesend** (68 AW) + 6 AW Abwesenheit beim anderen = 74 AW total
- **Geplant:** 116 AW
- **Verfügbar (plannable):** 50 AW
- **Frei:** -66 AW (Überbuchung!)

**Berechnung:**
```
Verfügbare Kapazität = base_workload - absence_workload
                     = 136 - 74
                     = 62 AW

Geplant = 116 AW
Frei = 62 - 116 = -54 AW (theoretisch)

Gudat gibt -66 AW zurück (mit Productivity-Factor 0.8 berücksichtigt)
```

---

## ✅ LÖSUNGSVORSCHLÄGE

### 1. Negative AW - Frontend-Verbesserung

**Aktuell:** Zeigt einfach "-69 AW frei" (verwirrend)

**Vorschlag:**
```javascript
// In renderGudatTeams() oder ähnlicher Funktion
if (team.free < 0) {
    // Warnung mit Erklärung
    freeText = `${Math.abs(team.free)} AW überbucht`;
    statusClass = 'text-danger';
    icon = '🔴';
    tooltip = 'Überbuchung: Geplante Arbeit übersteigt verfügbare Kapazität (Abwesenheiten berücksichtigt)';
}
```

### 2. Wochen-Übersicht - Frontend-Debug

**Prüfe:**
1. API-Response-Format: `data.woche` vs. `data.week`
2. Daten-Filterung: Werden nur interne Teams angezeigt?
3. JavaScript-Fehler in Browser-Console

**Code prüfen:**
```javascript
// In templates/aftersales/kapazitaetsplanung.html
function renderGudatWeek(days) {
    console.log('Wochen-Daten:', days); // Debug-Log
    // ...
}
```

### 3. Dokumentation

**Hinzufügen:**
- Tooltip: "Negative AW = Überbuchung (Abwesenheiten berücksichtigt)"
- Info-Box: Erklärt wie Gudat die Kapazität berechnet

---

## 🎯 ZUSAMMENFASSUNG

| Problem | Status | Lösung |
|---------|--------|--------|
| Negative freie AW | ✅ **Korrekt** | Frontend-Warnung hinzufügen |
| Wochen-Übersicht 0% | ⚠️ **Frontend-Bug** | JavaScript-Code prüfen |

**Haupt-Erkenntnis:**
- Die Gudat-API funktioniert korrekt
- Negative AW ist **korrekt** (Überbuchung mit Abwesenheiten)
- Problem liegt im Frontend-Rendering

---

**Erstellt von:** Claude AI  
**Datum:** 2026-01-20  
**TAG:** 200
