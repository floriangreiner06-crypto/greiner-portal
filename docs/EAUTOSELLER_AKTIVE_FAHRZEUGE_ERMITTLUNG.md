# e-autoseller: Wie werden aktive Fahrzeuge ermittelt?

**Datum:** 2026-01-23  
**Problem:** Diskrepanz zwischen verschiedenen Datenquellen

---

## 🔍 Aktuelle Situation

### Verschiedene Datenquellen liefern unterschiedliche Werte:

| Datenquelle | Anzahl Fahrzeuge | Beschreibung |
|-------------|------------------|--------------|
| **eAutoseller Widget 203** | **35** | "Aktive Fahrzeuge" (Bestand) |
| **HTML-API (txtAktiv=1)** | **150** | Mit `txtAktiv=1` Parameter |
| **HTML-API (ohne Filter)** | **150** | Alle Fahrzeuge |
| **Swagger API (/dms/vehicles)** | **367** | Alle Fahrzeuge im System |
| **Swagger API (/dms/vehicles/prices)** | **367** | Sollte "active vehicles" sein, liefert aber alle |

---

## 📊 Analyse

### 1. eAutoseller Widget 203: "Bestand" = 35
- **Quelle:** `startdata.asp?id=203`
- **Bedeutung:** "Aktive Fahrzeuge" (verkaufsbereit)
- **Status:** ✅ Dies ist die autoritative Quelle für "aktive Fahrzeuge"

### 2. HTML-API (`kfzuebersicht.asp`)
- **Parameter:** `txtAktiv=1` (sollte aktive Fahrzeuge filtern)
- **Ergebnis:** 150 Fahrzeuge
- **Problem:** 
  - Liefert mehr als Widget 203 (35)
  - `txtAktiv=1` filtert möglicherweise nicht korrekt
  - Oder: "Aktiv" bedeutet hier etwas anderes

### 3. Swagger API (`/dms/vehicles`)
- **Ergebnis:** 367 Fahrzeuge (alle im System)
- **Status-Feld:** Alle haben `status: {"id": 1, "wording": "Verkaufsbestand"}`
- **Problem:**
  - Kein Filter für "aktive" Fahrzeuge
  - Status-Parameter funktioniert nicht (liefert immer 367)
  - Alle Fahrzeuge haben denselben Status

### 4. Swagger API (`/dms/vehicles/prices`)
- **Dokumentation:** "Get all active vehicles with prices"
- **Ergebnis:** 367 Fahrzeuge (alle)
- **Problem:**
  - Sollte nur aktive liefern, liefert aber alle
  - Möglicherweise API-Bug oder falsche Dokumentation

---

## 🎯 Lösung: Wie aktive Fahrzeuge ermitteln?

### Option 1: eAutoseller Widget 203 verwenden ⭐⭐⭐
**Vorgehen:**
- Widget 203 liefert die Anzahl aktiver Fahrzeuge (35)
- **ABER:** Widget liefert nur die Anzahl, nicht die Liste!

**Problem:**
- Wir wissen, dass es 35 aktive Fahrzeuge gibt
- Aber wir wissen nicht, welche 35 das sind
- Können die Liste nicht filtern

### Option 2: HTML-API mit txtAktiv=1 verwenden ⭐⭐
**Vorgehen:**
- HTML-API mit `txtAktiv=1` liefert 150 Fahrzeuge
- **ABER:** Das sind mehr als die 35 aus Widget 203

**Problem:**
- Diskrepanz: 150 vs. 35
- Möglicherweise bedeutet "Aktiv" in HTML-API etwas anderes
- Oder: HTML-API filtert nicht korrekt

### Option 3: Swagger API + manueller Filter ⭐
**Vorgehen:**
- Swagger API liefert alle 367 Fahrzeuge
- Manuell nach einem Feld filtern (z.B. `pointOfSale`, `category`, etc.)

**Problem:**
- Wir wissen nicht, welches Feld aktive von inaktiven unterscheidet
- Alle haben denselben Status

### Option 4: Kombination ⭐⭐⭐
**Vorgehen:**
- Widget 203 für Anzahl (35)
- Swagger API für Liste (367)
- **Annahme:** Die 35 aktiven sind die neuesten/aktuellsten

**Problem:**
- Wir wissen nicht, welche 35 das sind
- Könnte falsch sein

---

## 🔍 Mögliche Unterscheidungsmerkmale

### Felder in Swagger API, die relevant sein könnten:

1. **`status`** - Alle haben `{"id": 1, "wording": "Verkaufsbestand"}`
   - ❌ Unterscheidet nicht

2. **`pointOfSale`** - Filiale/Standort
   - ⚠️ Könnte relevant sein, aber nicht für aktive vs. inaktive

3. **`category`** - Kategorie
   - ⚠️ Könnte relevant sein

4. **`lastChange`** - Letzte Änderung
   - ⚠️ Könnte relevant sein (aktive = kürzlich geändert?)

5. **`stockEntrance`** - Hereinnahme-Datum
   - ⚠️ Könnte relevant sein

6. **`conditionType`** - Zustand (NEW, USED, etc.)
   - ⚠️ Könnte relevant sein

---

## 💡 Empfohlene Lösung

### Kurzfristig: Widget 203 als Referenz verwenden

**Für KPI-Berechnungen:**
- **Anzahl aktive Fahrzeuge:** Aus Widget 203 (35)
- **Liste aktive Fahrzeuge:** Aus Swagger API (367) - **Problem bleibt**

**Für Widgets:**
- **Lagerwert:** Berechne nur für die ersten 35 Fahrzeuge? ❌ Nicht sinnvoll
- **Verkaufsrate:** Verkäufe (4) / Widget 203 (35) = 11,4% ✅

### Langfristig: eAutoseller Support fragen

**Fragen an Support:**
1. Wie werden "aktive Fahrzeuge" in Widget 203 ermittelt?
2. Welches Feld/Parameter filtert aktive Fahrzeuge in der Swagger API?
3. Warum liefert `/dms/vehicles/prices` alle 367 statt nur aktive?

---

## 🔧 Technische Details

### HTML-API Filter
```python
# lib/eautoseller_client.py
params = {'start': '1'}
if active_only:
    params['txtAktiv'] = '1'  # Filtert auf 150 Fahrzeuge
```

### Swagger API
```python
# Kein Filter für "aktive" Fahrzeuge verfügbar
response = swagger_session.get(
    f"{api_base_url}/dms/vehicles",
    params={}  # Kein Parameter für "aktive"
)
```

### Widget 203
```python
# Liefert nur Anzahl, nicht Liste
widget_203 = kpis['widget_203']['values'][0]  # = 35
```

---

## 📝 Nächste Schritte

1. **eAutoseller Support kontaktieren:**
   - Wie werden aktive Fahrzeuge in Widget 203 ermittelt?
   - Welcher Parameter filtert aktive Fahrzeuge in Swagger API?

2. **Alternative:**
   - Widget 203 (35) als Referenz verwenden
   - Für Berechnungen: Annahme treffen oder beide Werte zeigen

3. **Für jetzt:**
   - Widgets klar kennzeichnen: "Gesamt (367)" vs. "Aktive (35)"
   - Verkaufsrate korrekt berechnen: 4 / 35 = 11,4%

---

**Status:** ⚠️ Unklar, wie aktive Fahrzeuge in Swagger API gefiltert werden  
**Empfehlung:** eAutoseller Support kontaktieren
