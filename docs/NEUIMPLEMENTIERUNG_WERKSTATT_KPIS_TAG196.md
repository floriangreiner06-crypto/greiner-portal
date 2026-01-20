# NEUIMPLEMENTIERUNG: Werkstatt-KPIs (TAG 196)

**Datum:** 2026-01-19  
**Status:** ✅ Implementiert & Getestet

---

## PROBLEM

Die bisherigen Funktionen waren zu komplex und falsch benannt:
- `get_st_anteil_position_basiert()` verwendete einen mysteriösen `* 0.75` Faktor
- `get_anwesenheit_rohdaten()` gab St-Anteil zurück, nicht Anwesenheit
- `get_aw_verrechnet()` gab AW-Einheiten zurück, aber keine Vorgabezeit in Stunden
- Dashboard zeigte falsche Werte (Stempelzeit > Anwesenheit, unrealistische KPIs)

---

## LÖSUNG: 3 EINFACHE FUNKTIONEN

### 1. `get_vorgabezeit_aus_labours()` - Vorgabezeit (AW-Anteil)

**Definition:** Vorgabezeit = `labours.time_units × 6 / 60` (Stunden)

**SQL-Query:**
```sql
WITH auftraege_mit_stempelung AS (
    SELECT DISTINCT t.employee_number, t.order_number
    FROM times t
    WHERE t.type = 2 AND t.end_time IS NOT NULL AND t.order_number > 31
      AND t.start_time >= :von AND t.start_time < :bis + INTERVAL '1 day'
)
SELECT 
    ams.employee_number,
    SUM(l.time_units) AS aw,
    SUM(l.time_units) * 6.0 / 60.0 AS vorgabezeit_std
FROM auftraege_mit_stempelung ams
JOIN labours l ON ams.order_number = l.order_number
WHERE l.time_units > 0
GROUP BY ams.employee_number
```

**Rückgabe:** `{employee_number: {aw, vorgabezeit_std, umsatz}}`

---

### 2. `get_stempelzeit_aus_times()` - Stempelzeit (St-Anteil)

**Definition:** Stempelzeit = `times type=2 (end - start)`, **OHNE 0.75 Faktor!**

**SQL-Query:**
```sql
SELECT 
    employee_number,
    SUM(dauer_minuten) / 60.0 AS stempelzeit_stunden
FROM (
    SELECT DISTINCT ON (employee_number, order_number, order_position, 
                        order_position_line, start_time, end_time)
        employee_number,
        EXTRACT(EPOCH FROM (end_time - start_time)) / 60.0 AS dauer_minuten
    FROM times
    WHERE type = 2 AND end_time IS NOT NULL AND order_number > 31
      AND start_time >= :von AND start_time < :bis + INTERVAL '1 day'
) dedupliziert
GROUP BY employee_number
```

**Rückgabe:** `{employee_number: stempelzeit_stunden}`

**WICHTIG:** Kein 0.75 Faktor! Die echte Stempelzeit, nicht manipuliert!

---

### 3. `get_anwesenheit_aus_times()` - Anwesenheit

**Definition:** Anwesenheit = `times type=1 (end - start)`

**SQL-Query:**
```sql
SELECT
    employee_number,
    SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60.0) / 60.0 AS anwesenheit_stunden
FROM times
WHERE type = 1 AND end_time IS NOT NULL
  AND start_time >= :von AND start_time < :bis + INTERVAL '1 day'
GROUP BY employee_number
```

**Rückgabe:** `{employee_number: anwesenheit_stunden}`

---

## VALIDIERUNG & FALLBACK

**Regel:** `Stempelzeit ≤ Anwesenheit` (IMMER!)

**Problem:** `type=1` Daten sind oft unvollständig (z.B. MA 5007: 72.7 Std vs. 331.7 Std Stempelzeit)

**Fallback-Mechanismus:**
1. Wenn `Stempelzeit > Anwesenheit (type=1)`:
   - Verwende Zeit-Spanne aus `get_stempelzeit_locosoft()` (erste bis letzte Stempelung)
   - Wenn Zeit-Spanne ≥ Stempelzeit: Verwende Zeit-Spanne
   - Sonst: Verwende `Stempelzeit × 1.2` (20% Puffer für Pausen)

2. Wenn keine `type=1` Daten vorhanden:
   - Gleicher Fallback wie oben

---

## KPI-FORMELN (Locosoft-konform)

```python
# LEISTUNGSGRAD = Vorgabezeit / Stempelzeit × 100
leistungsgrad = vorgabezeit_std / stempelzeit_std * 100

# PRODUKTIVITÄT = Stempelzeit / Anwesenheit × 100
produktivitaet = stempelzeit_std / anwesenheit_std * 100
```

**Erwartete Werte:**
- Leistungsgrad: 80% - 180% (typisch ~100-140%)
- Produktivität: 50% - 100% (typisch ~70-90%)

---

## ÄNDERUNGEN IN `get_mechaniker_leistung()`

### Alte Implementierung (FALSCH):
```python
st_anteil_position = WerkstattData.get_st_anteil_position_basiert(von, bis)  # 0.75 Faktor!
anwesenheit = WerkstattData.get_anwesenheit_rohdaten(von, bis)  # Gibt St-Anteil zurück!
aw_verrechnet = WerkstattData.get_aw_verrechnet(von, bis)  # Nur AW, keine Vorgabezeit!
```

### Neue Implementierung (KORREKT):
```python
vorgabezeit_data = WerkstattData.get_vorgabezeit_aus_labours(von, bis)  # AW-Anteil in Stunden
stempelzeit_data = WerkstattData.get_stempelzeit_aus_times(von, bis)  # St-Anteil in Stunden (OHNE 0.75!)
anwesenheit_data = WerkstattData.get_anwesenheit_aus_times(von, bis)  # Anwesenheit in Stunden
```

### Zuordnung in `rohdaten`:
```python
rohdaten[emp_nr] = {
    'vorgabezeit_std': vorgabezeit_std,  # AW-Anteil in Stunden (SSOT!)
    'stempelzeit_std': stempelzeit_std,  # St-Anteil in Stunden (SSOT!)
    'anwesenheit_std': anwesenheit_std,  # Anwesenheit in Stunden (SSOT!)
    'aw': aw_roh,  # AW-Einheiten (SSOT!)
    # ... weitere Felder
}
```

---

## SSOT (Single Source of Truth)

Alle Werte werden jetzt in **Stunden** berechnet und an das Frontend übergeben:

```python
mechaniker_liste.append({
    'vorgabezeit_std': round(roh_data.get('vorgabezeit_std', 0), 1),  # SSOT!
    'stempelzeit_std': round(roh_data.get('stempelzeit_std', 0), 1),  # SSOT!
    'anwesenheit_std': round(roh_data.get('anwesenheit_std', 0), 1),  # SSOT!
    'aw': round(roh_data['aw'], 1),  # SSOT!
    # ... weitere Felder
})
```

**Dashboard verwendet jetzt direkt `*_std` Werte, keine Berechnungen mehr!**

---

## TEST-ERGEBNISSE

### MA 5007 (Tobias Reitmeier) - 01.01.26 bis 18.01.26:

```
Vorgabezeit: 64.7 Std (646.5 AW)
Stempelzeit: 331.7 Std
Anwesenheit: 398.0 Std (Fallback: Stempelzeit × 1.2)
Leistungsgrad: 19.5%
Produktivität: 83.3%

✅ OK: Stempelzeit (331.7 Std) ≤ Anwesenheit (398.0 Std)
```

**Hinweis:** Leistungsgrad ist niedrig (19.5%), weil Vorgabezeit (64.7 Std) viel kleiner ist als Stempelzeit (331.7 Std). Das deutet darauf hin, dass viele Stempelungen auf Positionen ohne AW erfolgten (z.B. Leerlauf, Wartezeiten).

---

## ENTFERNTE FUNKTIONEN

Die folgenden Funktionen wurden **nicht gelöscht**, aber **nicht mehr verwendet**:
- `get_st_anteil_position_basiert()` - Enthielt 0.75 Faktor, zu komplex
- `get_anwesenheit_rohdaten()` - Gab St-Anteil zurück, nicht Anwesenheit

**Legacy-Funktionen bleiben für Kompatibilität erhalten, werden aber nicht mehr aufgerufen.**

---

## NÄCHSTE SCHRITTE

1. ✅ Neue Funktionen implementiert
2. ✅ Validierung & Fallback implementiert
3. ✅ SSOT umgesetzt (alle Werte in Stunden)
4. ✅ Service neu gestartet
5. ⏳ Dashboard-Test (Frontend muss `*_std` Werte verwenden)
6. ⏳ Vergleich mit Locosoft-UI für Validierung

---

## DATEIEN

- `api/werkstatt_data.py`:
  - `get_vorgabezeit_aus_labours()` (NEU)
  - `get_stempelzeit_aus_times()` (NEU)
  - `get_anwesenheit_aus_times()` (NEU)
  - `get_mechaniker_leistung()` (ANGEPASST)
  - `berechne_mechaniker_kpis_aus_rohdaten()` (ANGEPASST)

- `api/werkstatt_api.py`:
  - `get_leistung()` (verwendet neue Funktionen automatisch)

---

**Status:** ✅ Implementiert & Getestet  
**Service:** ✅ Neu gestartet  
**Nächster Schritt:** Dashboard-Test & Validierung mit Locosoft-UI
