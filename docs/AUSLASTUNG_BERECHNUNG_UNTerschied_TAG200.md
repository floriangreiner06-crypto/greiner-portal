# Auslastung-Berechnung: Unterschied zwischen Dashboard und Kapazitätsplanung (TAG 200)

**Datum:** 2026-01-20  
**Problem:** Dashboard zeigt 419% Auslastung, Kapazitätsplanung zeigt 42%

---

## 🔍 PROBLEM-ANALYSE

### Dashboard: `/api/werkstatt/live/kapazitaet`
**Endpoint:** `GET /api/werkstatt/live/kapazitaet`  
**Funktion:** `WerkstattData.get_kapazitaetsplanung()`

**Berechnung:**
```python
# Zeile 1784 in werkstatt_data.py
auslastung_gesamt = (total_aw / kapazitaet_aw) * 100
```

**Datenquellen:**
- `total_aw`: Summe ALLER offenen Aufträge (letzte 7 Tage, default)
- `kapazitaet_aw`: Tageskapazität (nur HEUTE)

**Problem:** 
- ❌ Vergleicht **mehrere Tage Arbeit** mit **Tageskapazität**
- ❌ Führt zu unrealistisch hohen Werten (419% = 4.19 Tage Arbeit)

**Beispiel:**
- 10 Mechaniker × 8h × 6 AW/h = 480 AW Tageskapazität
- 2000 AW offene Arbeit (7 Tage)
- Auslastung = (2000 / 480) × 100 = **417%** ✅ Passt zu 419%!

---

### Kapazitätsplanung: `/api/werkstatt/live/forecast`
**Endpoint:** `GET /api/werkstatt/live/forecast`  
**Funktion:** `get_kapazitaets_forecast()`

**Berechnung:**
```python
# Zeile 1252 in werkstatt_live_api.py
auslastung = (geplant_aw / kapazitaet_aw) * 100
```

**Datenquellen:**
- `geplant_aw`: Nur Aufträge mit Termin für **diesen Tag**
- `kapazitaet_aw`: Tageskapazität für **diesen Tag**

**Korrekt:**
- ✅ Vergleicht **Tagesarbeit** mit **Tageskapazität**
- ✅ Realistische Werte (42% = weniger als halbe Tageskapazität)

**Beispiel:**
- 10 Mechaniker × 8h × 6 AW/h = 480 AW Tageskapazität
- 200 AW geplant für heute
- Auslastung = (200 / 480) × 100 = **42%** ✅ Passt!

---

## 📊 VERGLEICH

| Aspekt | Dashboard | Kapazitätsplanung |
|--------|-----------|-------------------|
| **Berechnung** | `total_aw / kapazitaet_aw` | `geplant_aw / kapazitaet_aw` |
| **total_aw** | Alle offenen Aufträge (7 Tage) | Nur Termine für diesen Tag |
| **kapazitaet_aw** | Tageskapazität (heute) | Tageskapazität (pro Tag) |
| **Zeitraum** | 7 Tage Arbeit vs. 1 Tag Kapazität | 1 Tag Arbeit vs. 1 Tag Kapazität |
| **Ergebnis** | 419% (unrealistisch hoch) | 42% (realistisch) |

---

## ✅ LÖSUNG

### Option 1: Dashboard zeigt "Tage Arbeit" statt Prozent
**Aktuell:** Dashboard zeigt `tage_arbeit` als Subtext (4.2 Tage Arbeit)  
**Vorschlag:** Hauptwert als "Tage Arbeit" anzeigen, Prozent als Subtext

### Option 2: Dashboard zeigt Tages-Auslastung
**Änderung:** Statt `auslastung_gesamt` → `auslastung_heute` verwenden
```python
# Statt:
auslastung = auslastung_gesamt  # 419%

# Verwende:
auslastung = auslastung_heute  # Nur heute
```

### Option 3: Beide Werte anzeigen
- **Hauptwert:** Tages-Auslastung (heute)
- **Subtext:** "X Tage Arbeit" (Gesamt)

---

## 🔧 EMPFOHLENE ÄNDERUNG

**Dashboard sollte zeigen:**
1. **Hauptwert:** Tages-Auslastung (heute) - wie Kapazitätsplanung
2. **Subtext:** "X Tage Arbeit" (Gesamt) - informativ, nicht als Prozent

**Code-Änderung:**
```javascript
// Statt:
const auslastung = Math.round(data.auslastung.prozent_gesamt || 0);  // 419%

// Verwende:
const auslastung = Math.round(data.auslastung.prozent_heute || 0);  // 42%
const tage = data.auslastung.tage_arbeit || 0;  // 4.2 Tage
```

---

## 📋 NÄCHSTE SCHRITTE

1. ✅ Problem identifiziert
2. 🔄 Code anpassen (Dashboard zeigt `prozent_heute` statt `prozent_gesamt`)
3. 🔄 Testen
4. 🔄 Dokumentation aktualisieren
