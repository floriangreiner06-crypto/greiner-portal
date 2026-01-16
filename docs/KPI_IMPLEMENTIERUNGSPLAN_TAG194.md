# KPI-Berechnung Implementierungsplan - Position-basierte Berechnung

**Datum:** 2026-01-16 (TAG 194)  
**Status:** 🟡 Planung - Bereit für Implementierung  
**Priorität:** Hoch

---

## ✅ Erkenntnisse

### 1. `times` Tabelle HAT Positionen!

**Wichtig:** Die `times` Tabelle hat `order_position` und `order_position_line` Spalten!

**Beweis:**
- `scripts/analyse_garantieakte_220266.py` Zeile 92-93: `t.order_position, t.order_position_line`
- `api/werkstatt_soap_api.py` Zeile 56: `AND (t.order_position IS NULL OR t.order_position_line IS NULL)`
- `docs/DB_SCHEMA_SQLITE.md` Zeile 2128-2129: `order_position INTEGER`, `order_position_line INTEGER`

**Problem:** Nicht alle Stempelungen sind zugeordnet!
- Manche Stempelungen haben `order_position IS NULL`
- Es gibt bereits eine Funktion zum Verteilen: `api/werkstatt_soap_api.py` → `verteile_stempelzeiten()`

### 2. Locosoft-Berechnung (offizielle Erklärung)

**Stempelanteil = Summe aller Stempelungen auf Auftragspositionen**

**Anteilige Verteilung:**
- Wenn mehrere Monteure auf eine Position stempeln → anteilige Verteilung
- Wenn ein Monteur auf mehrere Positionen stempelt → anteilige Verteilung

---

## 🎯 Implementierungsplan

### Phase 1: Stempelungen auf Positionen zuordnen

**Problem:** Nicht alle Stempelungen haben `order_position` gesetzt.

**Lösung:** 
1. **Zugeordnete Stempelungen verwenden** (wo `order_position IS NOT NULL`)
2. **Unzugeordnete Stempelungen verteilen** basierend auf:
   - Mechaniker (`employee_number`)
   - Auftrag (`order_number`)
   - Zeitliche Überlappung mit Positionen
   - AW-Verteilung

**SQL-Ansatz:**
```sql
WITH stempelungen_mit_positionen AS (
    -- 1. Zugeordnete Stempelungen (direkt verwenden)
    SELECT
        t.employee_number,
        t.order_number,
        t.order_position,
        t.order_position_line,
        t.start_time,
        t.end_time,
        EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 60 as stempel_minuten
    FROM times t
    WHERE t.type = 2
        AND t.end_time IS NOT NULL
        AND t.order_number > 31
        AND t.order_position IS NOT NULL
        AND t.order_position_line IS NOT NULL
        AND t.start_time >= %s AND t.start_time < %s + INTERVAL '1 day'
    
    UNION ALL
    
    -- 2. Unzugeordnete Stempelungen (anteilig verteilen)
    SELECT
        t.employee_number,
        t.order_number,
        l.order_position,
        l.order_position_line,
        t.start_time,
        t.end_time,
        -- Anteilige Verteilung basierend auf AW
        EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 60 
            * (l.time_units / NULLIF(SUM(l.time_units) OVER (PARTITION BY t.order_number), 0)) as stempel_minuten
    FROM times t
    JOIN labours l ON t.order_number = l.order_number
    WHERE t.type = 2
        AND t.end_time IS NOT NULL
        AND t.order_number > 31
        AND (t.order_position IS NULL OR t.order_position_line IS NULL)
        AND t.start_time >= %s AND t.start_time < %s + INTERVAL '1 day'
        AND l.time_units > 0
)
```

### Phase 2: Stempelanteil pro Position/Mechaniker berechnen

**Stempelanteil = Summe aller Stempelungen auf Positionen**

```sql
stempelanteil_pro_position AS (
    SELECT
        employee_number,
        order_number,
        order_position,
        order_position_line,
        SUM(stempel_minuten) as stempelanteil_minuten
    FROM stempelungen_mit_positionen
    GROUP BY employee_number, order_number, order_position, order_position_line
)
```

### Phase 3: AW-Anteil pro Position/Mechaniker berechnen (anteilige Verteilung)

**Wenn mehrere Monteure auf eine Position stempeln:**
```sql
-- Gesamt-Stempelzeit pro Position
gesamt_stempelzeit_pro_position AS (
    SELECT
        order_number,
        order_position,
        order_position_line,
        SUM(stempelanteil_minuten) as gesamt_stempel_minuten
    FROM stempelanteil_pro_position
    GROUP BY order_number, order_position, order_position_line
),

-- AW-Anteil pro Mechaniker/Position (anteilige Verteilung)
aw_anteil_pro_position AS (
    SELECT
        sap.employee_number,
        sap.order_number,
        sap.order_position,
        sap.order_position_line,
        l.time_units * (sap.stempelanteil_minuten / NULLIF(gst.gesamt_stempel_minuten, 0)) as aw_anteil
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
        AND (l.labour_type IS NULL OR l.labour_type != 'I')  -- Nur externe Aufträge
)
```

### Phase 4: Aggregation pro Mechaniker

**Stempelanteil = Summe über alle Positionen:**
```sql
stempelanteil_mechaniker AS (
    SELECT
        employee_number,
        SUM(stempelanteil_minuten) as stempelanteil_minuten
    FROM stempelanteil_pro_position
    GROUP BY employee_number
)
```

**AW-Anteil = Summe über alle Positionen:**
```sql
aw_anteil_mechaniker AS (
    SELECT
        employee_number,
        SUM(aw_anteil) as aw_anteil
    FROM aw_anteil_pro_position
    GROUP BY employee_number
)
```

### Phase 5: Leistungsgrad berechnen

**Leistungsgrad = (AW-Anteil / Stempelanteil) × 100:**
```sql
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

## 📝 Implementierungsschritte

### Schritt 1: SQL-Query erstellen (Test-Query)

**Datei:** `docs/sql/kpi_position_based_test.sql` (neu)

**Zweck:** 
- Test-Query für Position-basierte Berechnung
- Validierung mit bekannten Beispielen (z.B. Mechaniker 5018, November 2025)

### Schritt 2: Integration in `api/werkstatt_data.py`

**Datei:** `api/werkstatt_data.py` → `get_mechaniker_leistung()`

**Änderungen:**
1. Ersetze `stempelzeit_leistungsgrad` CTE durch Position-basierte Berechnung
2. Ersetze `aw_verrechnet` CTE durch `aw_anteil_mechaniker`
3. Verwende `stempelanteil_mechaniker` statt `stempelzeit_leistungsgrad`

**Zeilen:** ~399-516

### Schritt 3: Testen mit bekannten Beispielen

**Test-Szenarien:**
1. **Mechaniker 5018, November 2025**
   - Locosoft: Stempelanteil = 8.483 Min, AW-Anteil = 205:55 (≈2.059 AW)
   - DRIVE: Sollte identisch sein

2. **Mehrere Mechaniker auf eine Position**
   - Auftrag mit 2 Mechanikern
   - Stempelanteil und AW-Anteil sollten anteilig verteilt werden

3. **Ein Mechaniker auf mehrere Positionen**
   - Auftrag mit mehreren Positionen
   - Stempelanteil und AW-Anteil sollten anteilig verteilt werden

### Schritt 4: Performance-Optimierung

**Indizes:**
```sql
CREATE INDEX IF NOT EXISTS idx_times_order_position 
    ON times(order_number, order_position, order_position_line) 
    WHERE order_position IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_labours_order_position 
    ON labours(order_number, order_position, order_position_line);
```

**Caching:**
- Für wiederholte Abfragen (z.B. Dashboard)
- TTL: 5 Minuten

---

## ⚠️ Herausforderungen

### 1. Unzugeordnete Stempelungen

**Problem:** Nicht alle Stempelungen haben `order_position` gesetzt.

**Lösung:**
- **Option A:** Anteilige Verteilung basierend auf AW (siehe Phase 1)
- **Option B:** Nur zugeordnete Stempelungen verwenden (konservativer Ansatz)
- **Option C:** SOAP-API verwenden, um Stempelungen zuzuordnen (langsam)

**Empfehlung:** Option A (anteilige Verteilung)

### 2. Performance

**Problem:** Position-basierte Berechnung ist rechenintensiver.

**Lösung:**
- **CTEs** für bessere Performance
- **Indizes** auf `times` und `labours`
- **Caching** für wiederholte Abfragen
- **Inkrementelle Berechnung** (nur neue/geänderte Stempelungen)

### 3. Validierung

**Problem:** Wie validieren wir die Berechnung?

**Lösung:**
- **Locosoft-Exporte** als Referenz
- **Unit-Tests** mit bekannten Beispielen
- **Vergleich** mit aktueller Implementierung (Differenz-Analyse)

---

## 🚀 Nächste Schritte

### Sofort (TAG 194)

1. ✅ **Kontext-Dokument erstellt** (`docs/KPI_BERECHNUNG_KONTEXT_LOCOSOFT_TAG194.md`)
2. ✅ **Implementierungsplan erstellt** (dieses Dokument)
3. ⏳ **SQL-Query erstellen** (Test-Query)
4. ⏳ **Testen mit bekannten Beispielen**

### Kurzfristig (TAG 195-196)

1. **SQL-Query implementieren** in `api/werkstatt_data.py`
2. **Unit-Tests** erstellen
3. **Performance-Optimierung** (Indizes, Caching)
4. **Validierung** mit Locosoft-Exporten

### Mittelfristig (TAG 197+)

1. **Monitoring** für Abweichungen
2. **Dokumentation** aktualisieren
3. **Weitere Optimierungen** (falls nötig)

---

## 📚 Referenzen

- `docs/KPI_BERECHNUNG_KONTEXT_LOCOSOFT_TAG194.md` - Kontext-Dokument
- `api/werkstatt_data.py` - Aktuelle Implementierung
- `api/werkstatt_soap_api.py` - Stempelungen verteilen
- `docs/DB_SCHEMA_LOCOSOFT.md` - Datenbank-Schema

---

**Status:** 🟡 Bereit für Implementierung - SQL-Query erstellen und testen
