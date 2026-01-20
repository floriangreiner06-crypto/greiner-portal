# VOLLSTÄNDIGE DOKUMENTATION: Werkstatt-KPI-Berechnungen

**Datum:** 2026-01-18  
**Status:** 🔍 **ZU ÜBERPRÜFEN**

---

## 📊 PROBLEM

Dashboard zeigt falsche Werte:
- "Stempelzeit": 2.113,3 Std (sollte St-Anteil sein, ist aber Vorgabezeit)
- "Anwesenheit": 626,4 Std (sollte echte Anwesenheit sein, ist aber St-Anteil)
- Einzelne Mechaniker-Werte sind ebenfalls falsch

---

## 🔍 DATENQUELLEN

### 1. `get_st_anteil_position_basiert(von, bis)`

**Datei:** `api/werkstatt_data.py` (Zeile 941-973)

**SQL-Query:**
```sql
SELECT 
    employee_number,
    ROUND(SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60 * 0.75)::numeric, 0) as stempelanteil_minuten
FROM (
    SELECT DISTINCT ON (employee_number, order_number, order_position, order_position_line, start_time, end_time)
        employee_number,
        start_time,
        end_time
    FROM times
    WHERE type = 2
      AND end_time IS NOT NULL
      AND order_number > 31
      AND order_position IS NOT NULL
      AND order_position_line IS NOT NULL
      AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
) t
GROUP BY employee_number
```

**Rückgabe:** `Dict[int, float]` - `{employee_number: stempelanteil_minuten}`

**Beispiel-Werte (01.01.2026 - 18.01.2026):**
- MA 5007: 14.926 Min = 248,8 Std
- Summe alle: 126.798 Min = 2.113,3 Std

**⚠️ PROBLEM:** Diese Funktion gibt **AW-Anteil (Vorgabezeit)** zurück, nicht St-Anteil!

---

### 2. `get_anwesenheit_rohdaten(von, bis)`

**Datei:** `api/werkstatt_data.py` (Zeile 870-939)

**SQL-Query:**
```sql
SELECT
    employee_number,
    DATE(start_time) as datum,
    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as anwesend_min
FROM times
WHERE type = 1
  AND end_time IS NOT NULL
  AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
GROUP BY employee_number, DATE(start_time)
```

**Rückgabe:** `Dict[int, Dict[str, Any]]` - `{employee_number: {tage, anwesend_min}}`

**Beispiel-Werte (01.01.2026 - 18.01.2026):**
- MA 5007: 4.365 Min = 72,7 Std
- Summe alle: 37.584 Min = 626,4 Std

**⚠️ PROBLEM:** Diese Funktion gibt **St-Anteil (Stempelzeit)** zurück, nicht Anwesenheit!

---

### 3. `get_aw_verrechnet(von, bis)`

**Datei:** `api/werkstatt_data.py` (Zeile 976-1040)

**SQL-Query:**
```sql
WITH auftraege_mit_stempelung AS (
    SELECT DISTINCT
        t.employee_number,
        t.order_number
    FROM times t
    WHERE t.type = 2
      AND t.end_time IS NOT NULL
      AND t.order_number > 31
      AND t.start_time >= %s 
      AND t.start_time < %s + INTERVAL '1 day'
),
aw_pro_mechaniker AS (
    SELECT
        ams.employee_number,
        SUM(l.time_units) as aw_gesamt,
        SUM(l.net_price_in_order) as umsatz_gesamt
    FROM auftraege_mit_stempelung ams
    JOIN labours l ON ams.order_number = l.order_number
    WHERE l.time_units > 0
    GROUP BY ams.employee_number
)
SELECT
    employee_number,
    aw_gesamt as aw,
    umsatz_gesamt as umsatz
FROM aw_pro_mechaniker
```

**Rückgabe:** `Dict[int, Dict[str, float]]` - `{employee_number: {aw, umsatz}}`

**Beispiel-Werte (01.01.2026 - 18.01.2026):**
- MA 5007: 646,5 AW = 646,5 × 6 / 60 = 64,7 Std
- Summe alle: 5.641,7 AW = 564,2 Std

**✅ KORREKT:** Diese Funktion gibt korrekte AW-Einheiten zurück.

---

### 4. `get_stempelzeit_locosoft(von, bis, leerlauf_filter)`

**Datei:** `api/werkstatt_data.py` (Zeile 764-797)

**SQL-Query:** (Komplex, mit Zeit-Spanne, Lücken, Pausen)
```sql
-- Vereinfacht: Zeit-Spanne von erster bis letzter Stempelung pro Tag
SELECT
    employee_number,
    COUNT(DISTINCT datum) as tage,
    SUM(auftraege) as auftraege,
    SUM(stempel_min) as stempel_min
FROM stempelzeit_locosoft
WHERE stempel_min > 0
GROUP BY employee_number
```

**Rückgabe:** `Dict[int, Dict[str, Any]]` - `{employee_number: {tage, auftraege, stempel_min}}`

**Verwendung:** Als Fallback für echte Anwesenheit (wenn type=1 fehlt)

---

## 🔄 ZUORDNUNG IN `api/werkstatt_data.py` (Zeile 379-430)

**Aktuelle Zuordnung:**
```python
# FIX TAG 196: BESTÄTIGT - Die Funktionen geben die falschen Werte zurück!
vorgabezeit_min = st_anteil_position.get(emp_nr, 0)  # get_st_anteil_position_basiert() gibt AW-Anteil zurück!
st_anteil_min = anwesenheit.get(emp_nr, {}).get('anwesend_min', 0)  # get_anwesenheit_rohdaten() gibt St-Anteil zurück!

# Fallback für echte Anwesenheit
anwesenheit_fallback_min = stempelzeit_locosoft_data.get('stempel_min', 0)
if st_anteil_min > 0 and anwesenheit_fallback_min >= st_anteil_min:
    anwesenheit_min = anwesenheit_fallback_min
else:
    anwesenheit_min = st_anteil_min * 1.2 if st_anteil_min > 0 else 0

rohdaten[emp_nr] = {
    'stempelzeit': st_anteil_min,  # St-Anteil (aus get_anwesenheit_rohdaten)
    'anwesenheit': anwesenheit_min,  # Echte Anwesenheit (Fallback)
    'vorgabezeit': vorgabezeit_min,  # AW-Anteil (aus get_st_anteil_position_basiert)
    'aw': aw_roh,  # AW-Einheiten (aus get_aw_verrechnet)
}
```

**⚠️ PROBLEM:** Die Zuordnung ist vertauscht, weil die Funktionen falsche Werte zurückgeben!

---

## 📐 KPI-BERECHNUNGEN IN `berechne_mechaniker_kpis_aus_rohdaten()` (Zeile 1201-1235)

**Leistungsgrad:**
```python
# Formel: Leistungsgrad = (Vorgabezeit / Stempelzeit) × 100
leistungsgrad = round((vorgabezeit_min / stempelzeit_min * 100), 1)
```

**Produktivität:**
```python
# Formel: Produktivität = (Stempelzeit / Anwesenheit) × 100
produktivitaet = berechne_produktivitaet(stempelzeit_min, anwesenheit_min)
```

**Anwesenheitsgrad:**
```python
# Formel: Anwesenheitsgrad = (Anwesenheit / Bezahlt) × 100
anwesenheitsgrad = berechne_anwesenheitsgrad(anwesenheit_min, bezahlt_min)
```

---

## 📊 GESAMT-KPIS IN `get_mechaniker_leistung()` (Zeile 497-510)

**Berechnung:**
```python
gesamt_stempelzeit = sum(m['stempelzeit'] for m in mechaniker_liste)  # St-Anteil in Minuten
gesamt_anwesenheit = sum(m['anwesenheit'] for m in mechaniker_liste)  # Echte Anwesenheit in Minuten
gesamt_vorgabezeit = sum(m.get('vorgabezeit', m['aw'] * 6.0) for m in mechaniker_liste)  # AW-Anteil in Minuten

gesamt_leistungsgrad = round(gesamt_vorgabezeit / gesamt_stempelzeit * 100, 1)
gesamt_produktivitaet = round(gesamt_stempelzeit / gesamt_anwesenheit * 100, 1)
```

---

## 🎯 ERWARTETE WERTE (Basierend auf Locosoft-Analyse)

**Für Top 10 Mechaniker (01.01.2026 - 18.01.2026):**
- Stempelzeit (St-Anteil): 626,4 Std
- Anwesenheit (Echte Anwesenheit): ~750 Std (mit Fallback)
- Vorgabezeit (AW-Anteil): 2.113,3 Std
- AW-Einheiten: 5.642 AW

**Leistungsgrad:** `2.113,3 / 626,4 × 100 = 337,4%` (unrealistisch!)

**⚠️ PROBLEM:** Leistungsgrad ist unrealistisch hoch, weil Vorgabezeit > Stempelzeit!

---

## 🔍 ROOT CAUSE ANALYSIS

**Problem 1: Funktionen geben falsche Werte zurück**
- `get_st_anteil_position_basiert()` gibt **AW-Anteil** zurück, nicht St-Anteil
- `get_anwesenheit_rohdaten()` gibt **St-Anteil** zurück, nicht Anwesenheit

**Problem 2: Zuordnung ist vertauscht**
- Aktuell: `vorgabezeit = st_anteil_position` (korrekt, weil st_anteil_position gibt AW-Anteil zurück)
- Aktuell: `stempelzeit = anwesenheit` (korrekt, weil anwesenheit gibt St-Anteil zurück)
- **ABER:** Die Funktionen sind falsch benannt oder berechnen das Falsche!

**Problem 3: Dashboard zeigt Werte vertauscht**
- Dashboard "Stempelzeit" = Vorgabezeit (2.113 Std)
- Dashboard "Anwesenheit" = Stempelzeit (626 Std)

---

## ✅ LÖSUNG

### Option 1: Funktionen korrigieren
- `get_st_anteil_position_basiert()` sollte **St-Anteil** zurückgeben (nicht AW-Anteil)
- `get_anwesenheit_rohdaten()` sollte **Anwesenheit** zurückgeben (nicht St-Anteil)

### Option 2: Zuordnung korrigieren
- `vorgabezeit = get_aw_verrechnet() × 6` (korrekt)
- `stempelzeit = get_st_anteil_position_basiert()` (korrekt, wenn Funktion korrigiert)
- `anwesenheit = get_anwesenheit_rohdaten()` (korrekt, wenn Funktion korrigiert)

### Option 3: Dashboard korrigieren
- Dashboard "Stempelzeit" = `m.vorgabezeit_std` (zeigt Vorgabezeit)
- Dashboard "Anwesenheit" = `m.stempelzeit_std` (zeigt Stempelzeit)
- Dashboard "Vorgabezeit" = `m.vorgabezeit_std` (zeigt Vorgabezeit)

---

## 📝 SQL-QUERIES ZUM TESTEN

### Test 1: Prüfe was `get_st_anteil_position_basiert()` tatsächlich zurückgibt
```sql
SELECT 
    employee_number,
    ROUND(SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60 * 0.75)::numeric, 0) as stempelanteil_minuten
FROM (
    SELECT DISTINCT ON (employee_number, order_number, order_position, order_position_line, start_time, end_time)
        employee_number,
        start_time,
        end_time
    FROM times
    WHERE type = 2
      AND end_time IS NOT NULL
      AND order_number > 31
      AND order_position IS NOT NULL
      AND order_position_line IS NOT NULL
      AND start_time >= '2026-01-01' AND start_time < '2026-01-19'
) t
WHERE employee_number = 5007
GROUP BY employee_number;
```

### Test 2: Prüfe was `get_anwesenheit_rohdaten()` tatsächlich zurückgibt
```sql
SELECT
    employee_number,
    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as anwesend_min
FROM times
WHERE type = 1
  AND employee_number = 5007
  AND end_time IS NOT NULL
  AND start_time >= '2026-01-01' AND start_time < '2026-01-19'
GROUP BY employee_number;
```

### Test 3: Prüfe was `get_aw_verrechnet()` tatsächlich zurückgibt
```sql
WITH auftraege_mit_stempelung AS (
    SELECT DISTINCT
        t.employee_number,
        t.order_number
    FROM times t
    WHERE t.type = 2
      AND t.employee_number = 5007
      AND t.end_time IS NOT NULL
      AND t.order_number > 31
      AND t.start_time >= '2026-01-01' 
      AND t.start_time < '2026-01-19'
)
SELECT
    ams.employee_number,
    SUM(l.time_units) as aw_gesamt
FROM auftraege_mit_stempelung ams
JOIN labours l ON ams.order_number = l.order_number
WHERE l.time_units > 0
GROUP BY ams.employee_number;
```

---

## 🎯 NÄCHSTE SCHRITTE

1. **Prüfe SQL-Queries** mit echten Daten (z.B. MA 5007)
2. **Vergleiche mit Locosoft-UI** (was zeigt Locosoft für MA 5007?)
3. **Korrigiere Funktionen** oder **Zuordnung**
4. **Teste Dashboard** nach Fix

---

**Erstellt:** TAG 196  
**Status:** 🔍 **ZU ÜBERPRÜFEN**
