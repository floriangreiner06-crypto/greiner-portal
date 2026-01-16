# KPI-Berechnung Kontext - Locosoft vs. DRIVE

**Datum:** 2026-01-16 (TAG 194)  
**Status:** 🔴 Problem identifiziert - Abweichungen zu Locosoft  
**Priorität:** Hoch

---

## 📋 Executive Summary

**Problem:** Die Leistungsgrad- und KPI-Berechnungen in DRIVE weichen nach wie vor von Locosoft ab, trotz mehrerer Anpassungen in den letzten Tagen.

**Locosoft Support-Antwort (16.01.2026):**
> "Der Stmp Anteil ergibt sich aus der Summe aller Stempelungen des Monteurs auf Auftragspositionen. Somit haben Sie einen Vergleich der Stempelungen eines Monteurs zu den AW laut Auftrag.
> 
> Wenn mehrere Monteure auf eine Position oder ein Monteur auf mehrere Positionen stempelt, wird dies anteilige verteilt. Daher der Begriff Stempel Anteil."

**Kernproblem:** DRIVE berechnet Stempelanteil und AW-Anteil nicht korrekt nach Locosoft-Logik.

---

## 🎯 Locosoft Stempelanteil-Berechnung (offizielle Erklärung)

### Definition

**Stempelanteil (Stmp Anteil) = Summe aller Stempelungen des Monteurs auf Auftragspositionen**

### Wichtige Punkte

1. **Stempelungen auf Positionen, nicht auf Aufträge**
   - Stempelungen werden **pro Position** (order_position, order_position_line) zugeordnet
   - Nicht nur pro Auftrag (order_number)

2. **Anteilige Verteilung bei mehreren Monteuren**
   - Wenn **mehrere Monteure** auf eine Position stempeln → **anteilige Verteilung**
   - Beispiel: Position hat 10 AW, Monteur A stempelt 60 Min, Monteur B stempelt 40 Min
     - Monteur A: 6 AW (60% der Stempelzeit)
     - Monteur B: 4 AW (40% der Stempelzeit)

3. **Anteilige Verteilung bei mehreren Positionen**
   - Wenn **ein Monteur** auf mehrere Positionen stempelt → **anteilige Verteilung**
   - Beispiel: Monteur stempelt 100 Min auf Auftrag mit 2 Positionen (10 AW + 5 AW)
     - Position 1: 6.67 AW (10 AW × 100 Min / 150 Min Gesamt-AW)
     - Position 2: 3.33 AW (5 AW × 100 Min / 150 Min Gesamt-AW)

4. **Vergleich Stempelungen vs. AW**
   - Stempelanteil = Summe der Stempelungen auf Positionen
   - AW-Anteil = Summe der AW auf Positionen (nach anteiliger Verteilung)
   - **Leistungsgrad = (AW-Anteil / Stempelanteil) × 100**

---

## 📊 Aktuelle DRIVE-Implementierung

### Datei: `api/werkstatt_data.py` → `get_mechaniker_leistung()`

#### 1. Stempelzeit-Berechnung (Zeilen 300-433)

**Aktueller Ansatz:**
```sql
-- Stempelzeit nach Locosoft-Logik pro Mechaniker/Tag (für Anzeige)
stempelzeit_locosoft AS (
    SELECT
        ts.employee_number,
        ts.datum,
        ts.auftraege,
        ROUND((ts.spanne_minuten 
               - COALESCE(l.luecken_minuten, 0) 
               - COALESCE(p.pausen_minuten, 0))::numeric, 0) as stempel_min
    FROM tages_spannen ts
    ...
)
```

**Problem:**
- Berechnet Stempelzeit **pro Tag** (erste bis letzte Stempelung)
- **NICHT pro Position** wie Locosoft
- **KEINE anteilige Verteilung** auf Positionen

#### 2. Stempelzeit für Leistungsgrad (Zeilen 399-422)

**Aktueller Ansatz:**
```sql
stempelzeit_leistungsgrad AS (
    SELECT
        employee_number,
        SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as stempel_min_leistungsgrad
    FROM stempelungen_dedupliziert
    GROUP BY employee_number
)
```

**Problem:**
- Summiert Stempelungen **pro Auftrag** (order_number)
- **NICHT pro Position** wie Locosoft
- **KEINE anteilige Verteilung** auf Positionen

#### 3. AW-Berechnung (Zeilen 446-473)

**Aktueller Ansatz:**
```sql
aw_verrechnet AS (
    SELECT
        l.mechanic_no as employee_number,
        SUM(l.time_units) / 10.0 as aw,  -- In Stunden
        SUM(l.net_price_in_order) as umsatz
    FROM labours l
    WHERE l.time_units > 0
        AND l.mechanic_no IS NOT NULL
        AND (l.labour_type IS NULL OR l.labour_type != 'I')
        AND EXISTS (
            SELECT 1
            FROM times t
            WHERE t.order_number = l.order_number
                AND t.employee_number = l.mechanic_no
                ...
        )
    GROUP BY l.mechanic_no
)
```

**Problem:**
- Summiert AW **direkt aus labours** (mechanic_no)
- **KEINE anteilige Verteilung** basierend auf Stempelzeit
- **KEINE Berücksichtigung** von mehreren Monteuren pro Position

#### 4. Leistungsgrad-Berechnung (Zeilen 505-516)

**Aktueller Ansatz:**
```sql
CASE
    WHEN ms.stempelzeit_leistungsgrad > 0 AND ms.aw > 0
    THEN ROUND((ms.aw * 60 / ms.stempelzeit_leistungsgrad * 100)::numeric, 1)
    ...
END as leistungsgrad
```

**Problem:**
- Verwendet **globale AW** (Summe aller Positionen)
- Verwendet **globale Stempelzeit** (Summe aller Aufträge)
- **KEINE Position-basierte Berechnung** wie Locosoft

---

## 🔍 Unterschiede: Locosoft vs. DRIVE

| Aspekt | Locosoft | DRIVE (aktuell) | Problem |
|--------|----------|-----------------|---------|
| **Stempelanteil** | Summe Stempelungen **auf Positionen** | Summe Stempelungen **auf Aufträge** | ❌ Falsche Granularität |
| **AW-Anteil** | Anteilige Verteilung **pro Position** | Direkt aus `labours.mechanic_no` | ❌ Keine anteilige Verteilung |
| **Mehrere Monteure** | Anteilige Verteilung basierend auf Stempelzeit | Keine Verteilung | ❌ Unfair |
| **Mehrere Positionen** | Anteilige Verteilung basierend auf AW | Keine Verteilung | ❌ Unfair |
| **Leistungsgrad** | (AW-Anteil / Stempelanteil) × 100 | (AW / Stempelzeit) × 100 | ❌ Falsche Formel |

---

## 🎯 Korrekturplan

### Schritt 1: Stempelungen auf Positionen zuordnen

**Problem:** `times` Tabelle hat nur `order_number`, keine `order_position` oder `order_position_line`.

**Lösung:**
1. Stempelungen müssen **Positionen zugeordnet** werden
2. Wenn keine direkte Zuordnung möglich → **anteilige Verteilung** basierend auf:
   - Stempelzeit pro Auftrag
   - AW pro Position
   - Zeitliche Überlappung

**SQL-Ansatz:**
```sql
-- Stempelungen mit Positionen verknüpfen
WITH stempelungen_mit_positionen AS (
    SELECT
        t.employee_number,
        t.order_number,
        t.start_time,
        t.end_time,
        l.order_position,
        l.order_position_line,
        l.time_units,
        -- Anteilige Verteilung basierend auf Stempelzeit
        EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 60 as stempel_minuten
    FROM times t
    JOIN labours l ON t.order_number = l.order_number
    WHERE t.type = 2
        AND t.end_time IS NOT NULL
        AND t.order_number > 31
        AND l.time_units > 0
        -- Zeitliche Überlappung: Stempelung muss innerhalb der Position-Zeit liegen
        -- (vereinfacht: alle Stempelungen eines Auftrags werden auf alle Positionen verteilt)
)
```

### Schritt 2: Anteilige Verteilung implementieren

**Für mehrere Monteure auf eine Position:**
```sql
-- Stempelanteil pro Position/Mechaniker
WITH stempelanteil_pro_position AS (
    SELECT
        l.order_number,
        l.order_position,
        l.order_position_line,
        t.employee_number,
        SUM(EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 60) as stempel_minuten
    FROM times t
    JOIN labours l ON t.order_number = l.order_number
    WHERE t.type = 2
        AND t.end_time IS NOT NULL
        AND t.order_number > 31
        AND l.time_units > 0
    GROUP BY l.order_number, l.order_position, l.order_position_line, t.employee_number
),
-- Gesamt-Stempelzeit pro Position
gesamt_stempelzeit_pro_position AS (
    SELECT
        order_number,
        order_position,
        order_position_line,
        SUM(stempel_minuten) as gesamt_stempel_minuten
    FROM stempelanteil_pro_position
    GROUP BY order_number, order_position, order_position_line
),
-- AW-Anteil pro Mechaniker/Position (anteilige Verteilung)
aw_anteil_pro_position AS (
    SELECT
        sap.order_number,
        sap.order_position,
        sap.order_position_line,
        sap.employee_number,
        l.time_units * (sap.stempel_minuten / gst.gesamt_stempel_minuten) as aw_anteil
    FROM stempelanteil_pro_position sap
    JOIN gesamt_stempelzeit_pro_position gst 
        ON sap.order_number = gst.order_number
        AND sap.order_position = gst.order_position
        AND sap.order_position_line = gst.order_position_line
    JOIN labours l 
        ON sap.order_number = l.order_number
        AND sap.order_position = l.order_position
        AND sap.order_position_line = l.order_position_line
    WHERE l.time_units > 0
)
```

### Schritt 3: Stempelanteil aggregieren

**Stempelanteil = Summe aller Stempelungen auf Positionen:**
```sql
-- Stempelanteil pro Mechaniker (Summe über alle Positionen)
stempelanteil_mechaniker AS (
    SELECT
        employee_number,
        SUM(stempel_minuten) as stempelanteil_minuten
    FROM stempelanteil_pro_position
    GROUP BY employee_number
)
```

### Schritt 4: AW-Anteil aggregieren

**AW-Anteil = Summe aller AW auf Positionen (nach anteiliger Verteilung):**
```sql
-- AW-Anteil pro Mechaniker (Summe über alle Positionen)
aw_anteil_mechaniker AS (
    SELECT
        employee_number,
        SUM(aw_anteil) as aw_anteil
    FROM aw_anteil_pro_position
    GROUP BY employee_number
)
```

### Schritt 5: Leistungsgrad berechnen

**Leistungsgrad = (AW-Anteil / Stempelanteil) × 100:**
```sql
-- Leistungsgrad pro Mechaniker
leistungsgrad_mechaniker AS (
    SELECT
        sam.employee_number,
        sam.stempelanteil_minuten,
        aam.aw_anteil,
        CASE
            WHEN sam.stempelanteil_minuten > 0 AND aam.aw_anteil > 0
            THEN ROUND((aam.aw_anteil * 6 / sam.stempelanteil_minuten * 100)::numeric, 1)
            ELSE NULL
        END as leistungsgrad
    FROM stempelanteil_mechaniker sam
    JOIN aw_anteil_mechaniker aam ON sam.employee_number = aam.employee_number
)
```

---

## ⚠️ Herausforderungen

### 1. Stempelungen ohne Position-Zuordnung

**Problem:** `times` Tabelle hat keine direkte Position-Zuordnung.

**Lösung:**
- Stempelungen werden **allen Positionen eines Auftrags** zugeordnet
- **Anteilige Verteilung** basierend auf:
  - AW pro Position
  - Zeitliche Überlappung (falls verfügbar)

### 2. Mehrere Stempelungen auf eine Position

**Problem:** Ein Mechaniker kann mehrmals auf eine Position stempeln.

**Lösung:**
- **Summierung** aller Stempelungen pro Position/Mechaniker
- **Deduplizierung** basierend auf Start-/Endzeit (wie aktuell)

### 3. Performance

**Problem:** Position-basierte Berechnung ist rechenintensiver.

**Lösung:**
- **CTEs** für bessere Performance
- **Indizes** auf `labours(order_number, order_position, order_position_line)`
- **Caching** für wiederholte Abfragen

---

## 📝 Nächste Schritte

### Sofort (TAG 194)

1. ✅ **Kontext-Dokument erstellt** (dieses Dokument)
2. ⏳ **Stempelungen auf Positionen zuordnen** analysieren
3. ⏳ **Anteilige Verteilung** implementieren
4. ⏳ **Testen** mit bekannten Beispielen (z.B. Mechaniker 5018, November 2025)

### Kurzfristig (TAG 195-196)

1. **SQL-Query** für Position-basierte Berechnung erstellen
2. **Unit-Tests** mit Locosoft-Referenzdaten
3. **Performance-Optimierung** (Indizes, Caching)
4. **Integration** in `api/werkstatt_data.py`

### Mittelfristig (TAG 197+)

1. **Validierung** mit Locosoft-Exporten
2. **Dokumentation** aktualisieren
3. **Monitoring** für Abweichungen

---

## 📚 Referenzen

### Locosoft Support-Antwort
- **Datum:** 2026-01-16
- **Thema:** Stempelanteil-Berechnung
- **Kernaussage:** "Stempelungen auf Auftragspositionen, anteilige Verteilung"

### Bestehende Dokumentation
- `docs/leistungsgrad_berechnung_erklaerung.md` - Aktuelle DRIVE-Erklärung
- `docs/locosoft_aw_anteil_fragenkatalog.md` - Fragen an Locosoft
- `docs/ZUSAMMENFASSUNG_LOCOSOFT_BEREchnung_TAG185.md` - Vorherige Analyse
- `docs/ANALYSE_LEISTUNGSGRAD_LOCOSOFT_TAG185.md` - Detaillierte Analyse

### Code-Referenzen
- `api/werkstatt_data.py` - Zeilen 219-600 (get_mechaniker_leistung)
- `utils/kpi_definitions.py` - KPI-Berechnungsfunktionen
- `docs/DB_SCHEMA_LOCOSOFT.md` - Datenbank-Schema

---

## 🔍 Beispiel-Berechnung

### Szenario
- **Auftrag:** 220471
- **Position 1:** 19 AW (1.9 Stunden)
- **Mechaniker:** 5018 (Jan)
- **Stempelzeit:** 28.88 Min (0.481 Stunden)

### Locosoft-Berechnung (erwartet)
1. **Stempelanteil:** 28.88 Min (Stempelungen auf Position 1)
2. **AW-Anteil:** 19 AW = 1.9 Stunden (da nur ein Mechaniker)
3. **Leistungsgrad:** (1.9 × 60 / 28.88) × 100 = **394.7%**

### DRIVE-Berechnung (aktuell)
1. **Stempelzeit:** 28.88 Min (Summe aller Stempelungen)
2. **AW:** 19 AW = 1.9 Stunden (direkt aus labours)
3. **Leistungsgrad:** (1.9 × 60 / 28.88) × 100 = **394.7%** ✅

**Problem:** Bei mehreren Mechanikern oder mehreren Positionen weicht DRIVE ab!

---

**Status:** 🔴 Korrektur erforderlich - Position-basierte Berechnung implementieren
