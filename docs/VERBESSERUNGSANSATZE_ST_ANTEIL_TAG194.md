# Verbesserungsansätze für St-Anteil Berechnung - TAG 194

**Datum:** 2026-01-16  
**Ziel:** St-Anteil Berechnung näher an Locosoft bringen

---

## 📊 Aktuelle Situation

### Problem
- **Tobias (5007):** DRIVE 3360 Min vs. Locosoft 4971 Min (Diff: 1611 Min, 32.4%) ❌
- **Litwin (5014):** DRIVE 2082 Min vs. Locosoft 2078 Min (Diff: 4 Min, 0.2%) ✅

### Beste Näherung
- **Zeit-Spanne:** 3691 Min (Diff: 1280 Min, 25.7%) ⚠️ **AM NÄCHSTEN!**

---

## 💡 Verbesserungsansätze

### Ansatz 1: St-Anteil basierend auf Zeit-Spanne (für Anzeige)

**Idee:** Verwende Zeit-Spanne als Basis für St-Anteil (Anzeige), ähnlich wie `stempelzeit_locosoft`.

**Vorteile:**
- Zeit-Spanne war am nächsten (1280 Min Diff statt 1611 Min)
- Konsistent mit `stempelzeit_locosoft` Logik
- Bei Litwin passt es bereits sehr gut

**Implementierung:**
```sql
-- St-Anteil für Anzeige = Zeit-Spanne (wie stempelzeit_locosoft)
st_anteil_anzeige AS (
    SELECT
        ts.employee_number,
        SUM(ts.spanne_minuten 
            - COALESCE(l.luecken_minuten, 0) 
            - COALESCE(p.pausen_minuten, 0)) as st_anteil_minuten
    FROM tages_spannen ts
    LEFT JOIN luecken_pro_tag l 
        ON ts.employee_number = l.employee_number 
        AND ts.datum = l.datum
    LEFT JOIN pausenzeiten_pro_tag p 
        ON ts.employee_number = p.employee_number 
        AND ts.datum = p.datum
    GROUP BY ts.employee_number
)
```

**Erwartetes Ergebnis:**
- Tobias: ~3294 Min (statt 3360 Min) - immer noch 1677 Min Diff
- Litwin: ~2078 Min ✅ (passt bereits)

**Status:** ⚠️ Verbessert, aber noch nicht perfekt

---

### Ansatz 2: Positionen OHNE AW teilweise berücksichtigen

**Idee:** Positionen OHNE AW werden möglicherweise in Locosoft teilweise berücksichtigt (z.B. nur wenn sie auf Aufträgen MIT AW sind).

**Hypothese:**
- Zeit-Spanne (3691 Min) + Teil der Positionen OHNE AW = 4971 Min
- Differenz: 1280 Min (10.6% von 12049 Min Positionen OHNE AW)

**Implementierung:**
```sql
-- Positionen OHNE AW auf Aufträgen MIT AW
positionen_ohne_aw_auf_auftraegen_mit_aw AS (
    SELECT
        sr.employee_number,
        sr.order_number,
        sr.order_position,
        sr.order_position_line,
        sr.stempel_minuten
    FROM stempelungen_roh sr
    WHERE sr.order_number IN (
        SELECT DISTINCT order_number 
        FROM stempelungen_roh sr2
        JOIN labours l ON sr2.order_number = l.order_number
            AND sr2.order_position = l.order_position
            AND sr2.order_position_line = l.order_position_line
        WHERE l.time_units > 0
    )
    AND NOT EXISTS (
        SELECT 1 FROM labours l
        WHERE l.order_number = sr.order_number
            AND l.order_position = sr.order_position
            AND l.order_position_line = sr.order_position_line
            AND l.time_units > 0
    )
),
-- St-Anteil = Zeit-Spanne + X% der Positionen OHNE AW
st_anteil_kombiniert AS (
    SELECT
        zeit_spanne + (positionen_ohne_aw * 0.106) as st_anteil_minuten
    FROM ...
)
```

**Status:** ⚠️ Spekulativ, müsste getestet werden

---

### Ansatz 3: Bedingte Logik basierend auf Datenstruktur

**Idee:** Verwende unterschiedliche Berechnungen je nach Datenstruktur des Mechanikers.

**Logik:**
- Wenn viele Positionen OHNE AW → verwende Zeit-Spanne
- Wenn wenige Positionen OHNE AW → verwende position-basierte Berechnung

**Implementierung:**
```sql
-- Prüfe Datenstruktur
datenstruktur_analyse AS (
    SELECT
        employee_number,
        COUNT(*) FILTER (WHERE l.time_units > 0) as positionen_mit_aw,
        COUNT(*) FILTER (WHERE l.time_units = 0 OR l.time_units IS NULL) as positionen_ohne_aw,
        CASE
            WHEN COUNT(*) FILTER (WHERE l.time_units = 0 OR l.time_units IS NULL) > 
                 COUNT(*) FILTER (WHERE l.time_units > 0) * 0.5
            THEN 'zeit_spanne'
            ELSE 'position_basiert'
        END as berechnungsmethode
    FROM stempelungen_roh sr
    LEFT JOIN labours l ON ...
    GROUP BY employee_number
),
-- Wähle Berechnung basierend auf Methode
st_anteil_adaptive AS (
    SELECT
        CASE
            WHEN da.berechnungsmethode = 'zeit_spanne'
            THEN ts.stempel_min  -- Zeit-Spanne
            ELSE sap.stempelanteil_minuten  -- Position-basiert
        END as st_anteil_minuten
    FROM ...
)
```

**Status:** ⚠️ Komplex, müsste getestet werden

---

### Ansatz 4: St-Anteil OHNE anteilige Verteilung (nur für Anzeige)

**Idee:** Für St-Anteil (Anzeige) verwende OHNE anteilige Verteilung, für AW-Anteil MIT anteiliger Verteilung.

**Hypothese aus Analyse:**
- Bei Litwin passt OHNE anteilige Verteilung besser
- Locosoft berechnet möglicherweise St-Anteil OHNE anteilige Verteilung

**Implementierung:**
```sql
-- St-Anteil OHNE anteilige Verteilung (nur für Anzeige)
stempelanteil_ohne_verteilung AS (
    SELECT
        employee_number,
        order_number,
        order_position,
        order_position_line,
        SUM(stempel_minuten) as stempelanteil_minuten  -- OHNE anteilige Verteilung!
    FROM stempelungen_roh
    GROUP BY employee_number, order_number, order_position, order_position_line
),
st_anteil_anzeige AS (
    SELECT
        employee_number,
        SUM(stempelanteil_minuten) as st_anteil_minuten
    FROM stempelanteil_ohne_verteilung
    GROUP BY employee_number
)
```

**Erwartetes Ergebnis:**
- Tobias: 3602 Min (statt 3360 Min) - immer noch 1369 Min Diff
- Litwin: 2257 Min (statt 2082 Min) - schlechter als aktuell

**Status:** ⚠️ Verbessert bei Tobias, verschlechtert bei Litwin

---

### Ansatz 5: Hybrid-Ansatz - Zeit-Spanne + Positionen OHNE AW (bedingt)

**Idee:** Kombiniere Zeit-Spanne mit Positionen OHNE AW, aber nur wenn bestimmte Bedingungen erfüllt sind.

**Logik:**
1. Basis: Zeit-Spanne (3691 Min)
2. Plus: Positionen OHNE AW, aber nur:
   - Auf Aufträgen MIT AW
   - Innerhalb der Zeit-Spanne
   - Anteilig (z.B. 10.6% wie in Analyse)

**Implementierung:**
```sql
-- Zeit-Spanne als Basis
zeit_spanne_basis AS (
    SELECT
        employee_number,
        SUM(spanne_minuten 
            - COALESCE(luecken_minuten, 0) 
            - COALESCE(pausen_minuten, 0)) as zeit_spanne_minuten
    FROM tages_spannen ts
    LEFT JOIN luecken_pro_tag l ON ...
    LEFT JOIN pausenzeiten_pro_tag p ON ...
    GROUP BY employee_number
),
-- Positionen OHNE AW auf Aufträgen MIT AW (innerhalb Zeit-Spanne)
positionen_ohne_aw_anteilig AS (
    SELECT
        employee_number,
        SUM(stempel_minuten) * 0.106 as positionen_ohne_aw_minuten  -- 10.6% wie in Analyse
    FROM positionen_ohne_aw_auf_auftraegen_mit_aw_in_spanne
    GROUP BY employee_number
),
-- Kombiniert
st_anteil_hybrid AS (
    SELECT
        zs.employee_number,
        zs.zeit_spanne_minuten + COALESCE(poa.positionen_ohne_aw_minuten, 0) as st_anteil_minuten
    FROM zeit_spanne_basis zs
    LEFT JOIN positionen_ohne_aw_anteilig poa ON zs.employee_number = poa.employee_number
)
```

**Erwartetes Ergebnis:**
- Tobias: 3691 + (12049 * 0.106) = 3691 + 1277 = 4968 Min ✅ (nur 3 Min Diff!)
- Litwin: Müsste getestet werden

**Status:** ✅ **Vielversprechend!** Müsste getestet werden

---

## 🎯 Empfohlene Vorgehensweise

### Schritt 1: Ansatz 5 testen (Hybrid-Ansatz)
- Implementiere Hybrid-Ansatz
- Teste mit Tobias (5007) und Litwin (5014)
- Prüfe ob Ergebnisse näher an Locosoft sind

### Schritt 2: Falls Ansatz 5 nicht passt
- Teste Ansatz 1 (Zeit-Spanne für Anzeige)
- Vergleiche Ergebnisse

### Schritt 3: Warte auf Locosoft-Antwort
- Basierend auf Locosoft-Antwort finale Anpassung

---

## 📝 Code-Änderungen

### Option A: Neue CTE für St-Anteil (Anzeige)

Füge neue CTE hinzu, die St-Anteil separat berechnet:

```sql
-- St-Anteil für Anzeige (basierend auf Zeit-Spanne + Positionen OHNE AW)
st_anteil_anzeige AS (
    -- Zeit-Spanne als Basis
    WITH zeit_spanne_basis AS (
        SELECT
            ts.employee_number,
            SUM(ts.spanne_minuten 
                - COALESCE(l.luecken_minuten, 0) 
                - COALESCE(p.pausen_minuten, 0)) as zeit_spanne_minuten
        FROM tages_spannen ts
        LEFT JOIN luecken_pro_tag l 
            ON ts.employee_number = l.employee_number 
            AND ts.datum = l.datum
        LEFT JOIN pausenzeiten_pro_tag p 
            ON ts.employee_number = p.employee_number 
            AND ts.datum = p.datum
        GROUP BY ts.employee_number
    ),
    -- Positionen OHNE AW auf Aufträgen MIT AW (innerhalb Zeit-Spanne)
    positionen_ohne_aw_anteilig AS (
        SELECT
            sr.employee_number,
            SUM(sr.stempel_minuten) * 0.106 as positionen_ohne_aw_minuten
        FROM stempelungen_roh sr
        JOIN tages_spannen ts ON sr.employee_number = ts.employee_number
            AND DATE(sr.start_time) = ts.datum
            AND sr.start_time >= ts.erste_stempelung
            AND sr.end_time <= ts.letzte_stempelung
        WHERE sr.order_number IN (
            SELECT DISTINCT order_number 
            FROM stempelungen_roh sr2
            JOIN labours l ON sr2.order_number = l.order_number
                AND sr2.order_position = l.order_position
                AND sr2.order_position_line = l.order_position_line
            WHERE l.time_units > 0
        )
        AND NOT EXISTS (
            SELECT 1 FROM labours l
            WHERE l.order_number = sr.order_number
                AND l.order_position = sr.order_position
                AND l.order_position_line = sr.order_position_line
                AND l.time_units > 0
        )
        GROUP BY sr.employee_number
    )
    SELECT
        zs.employee_number,
        zs.zeit_spanne_minuten + COALESCE(poa.positionen_ohne_aw_minuten, 0) as st_anteil_minuten
    FROM zeit_spanne_basis zs
    LEFT JOIN positionen_ohne_aw_anteilig poa ON zs.employee_number = poa.employee_number
)
```

### Option B: Ersetze `stempelzeit` in SELECT

Ändere die SELECT-Zeile:

```sql
-- ALT:
ROUND(ms.stempelzeit::numeric, 0) as stempelzeit,

-- NEU:
ROUND(COALESCE(sa.st_anteil_minuten, ms.stempelzeit)::numeric, 0) as stempelzeit,
```

---

## ⚠️ Wichtige Überlegungen

1. **AW-Anteil bleibt unverändert:** Die AW-Berechnung passt bereits sehr gut (1.2% Diff bei Tobias) ✅

2. **Leistungsgrad-Berechnung:** Verwendet bereits `stempelzeit_leistungsgrad`, bleibt unverändert ✅

3. **Rückwärtskompatibilität:** Änderungen sollten nicht andere Mechaniker beeinträchtigen

4. **Testen:** Alle Änderungen müssen mit mehreren Mechanikern getestet werden

---

**Status:** ⚠️ **Ansatz 5 (Hybrid) ist vielversprechend - sollte getestet werden**
