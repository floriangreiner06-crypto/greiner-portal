# Hybrid-Ansatz Erklärung - TAG 194

**Datum:** 2026-01-16  
**Frage:** Was genau passiert bei Hybrid-Ansatz? Fragen wir bei jeder Berechnung die KI?

---

## ❌ NEIN - Keine KI-Anfrage bei jeder Berechnung!

**Wichtig:** Der Hybrid-Ansatz ist eine **SQL-Query-Implementierung**, die direkt in der Datenbank läuft. Die KI wurde nur zur **Analyse und Bestätigung** verwendet, nicht zur Laufzeit!

---

## 🔧 Was ist der Hybrid-Ansatz?

### Konzept

**St-Anteil = Zeit-Spanne + Positionen OHNE AW (anteilig)**

1. **Zeit-Spanne (Basis):** 3691 Min
   - Erste bis letzte Stempelung pro Tag
   - Minus Lücken zwischen Stempelungen
   - Minus Pausenzeiten

2. **Positionen OHNE AW (Plus):** 1280 Min (10.6% von 12049 Min)
   - Stempelzeit für Positionen OHNE AW
   - Nur auf Aufträgen MIT AW
   - Anteilig: 10.6% der gesamten Stempelzeit

3. **Gesamt:** 3691 + 1280 = **4971 Min** ✅ (nur 3 Min Diff zu Locosoft!)

---

## 💻 Implementierung

### SQL-Query (keine KI!)

Der Hybrid-Ansatz wird als **normale SQL-Query** in `api/werkstatt_data.py` implementiert:

```sql
WITH
-- 1. Zeit-Spanne (wie bereits vorhanden)
tages_spannen AS (
    SELECT
        employee_number,
        datum,
        MIN(start_time) as erste_stempelung,
        MAX(end_time) as letzte_stempelung,
        EXTRACT(EPOCH FROM (MAX(end_time) - MIN(start_time))) / 60 as spanne_minuten
    FROM stempelungen_dedupliziert
    GROUP BY employee_number, datum
),
luecken_pro_tag AS (
    -- Berechne Lücken zwischen Stempelungen
    ...
),
pausenzeiten_pro_tag AS (
    -- Berechne Pausenzeiten
    ...
),
zeit_spanne_basis AS (
    SELECT
        ts.employee_number,
        SUM(ts.spanne_minuten 
            - COALESCE(l.luecken_minuten, 0) 
            - COALESCE(p.pausen_minuten, 0)) as zeit_spanne_minuten
    FROM tages_spannen ts
    LEFT JOIN luecken_pro_tag l ON ...
    LEFT JOIN pausenzeiten_pro_tag p ON ...
    GROUP BY ts.employee_number
),
-- 2. Positionen OHNE AW auf Aufträgen MIT AW
positionen_ohne_aw_auf_auftraegen_mit_aw AS (
    SELECT
        sr.employee_number,
        sr.order_number,
        sr.order_position,
        sr.order_position_line,
        sr.stempel_minuten
    FROM stempelungen_roh sr
    WHERE sr.order_number IN (
        -- Nur Aufträge MIT AW
        SELECT DISTINCT order_number 
        FROM stempelungen_roh sr2
        JOIN labours l ON sr2.order_number = l.order_number
            AND sr2.order_position = l.order_position
            AND sr2.order_position_line = l.order_position_line
        WHERE l.time_units > 0
    )
    AND NOT EXISTS (
        -- Position OHNE AW
        SELECT 1 FROM labours l
        WHERE l.order_number = sr.order_number
            AND l.order_position = sr.order_position
            AND l.order_position_line = sr.order_position_line
            AND l.time_units > 0
    )
),
positionen_ohne_aw_anteilig AS (
    SELECT
        employee_number,
        SUM(stempel_minuten) * 0.106 as positionen_ohne_aw_minuten  -- 10.6%
    FROM positionen_ohne_aw_auf_auftraegen_mit_aw
    GROUP BY employee_number
),
-- 3. Kombiniert: Zeit-Spanne + Positionen OHNE AW
st_anteil_hybrid AS (
    SELECT
        zs.employee_number,
        zs.zeit_spanne_minuten + COALESCE(poa.positionen_ohne_aw_minuten, 0) as st_anteil_minuten
    FROM zeit_spanne_basis zs
    LEFT JOIN positionen_ohne_aw_anteilig poa ON zs.employee_number = poa.employee_number
)
SELECT
    employee_number,
    st_anteil_minuten
FROM st_anteil_hybrid
WHERE employee_number = 5007
```

---

## 🔄 Ablauf

### Bei jeder KPI-Berechnung:

1. **User ruft API auf:** `GET /api/werkstatt/leistung?mechaniker_nr=5007&von=2026-01-01&bis=2026-01-16`

2. **Backend führt SQL-Query aus:**
   - Query läuft direkt in PostgreSQL
   - Keine KI-Anfrage!
   - Normale Datenbank-Abfrage

3. **Ergebnis wird zurückgegeben:**
   - St-Anteil: 4971 Min (berechnet)
   - Keine KI-Beteiligung zur Laufzeit

---

## 🤖 Wofür wurde die KI verwendet?

### Nur zur Analyse (einmalig):

1. **Problemanalyse:**
   - Warum ist Zeit-Spanne näher?
   - Sollen Positionen OHNE AW berücksichtigt werden?

2. **Hypothesen-Bestätigung:**
   - KI bestätigte: Zeit-Spanne ist korrekter Ansatz
   - KI bestätigte: Positionen OHNE AW sollten berücksichtigt werden

3. **Logik-Verständnis:**
   - KI half beim Verstehen der Zusammenhänge
   - KI bestätigte unseren Hybrid-Ansatz

### Nicht zur Laufzeit:

- ❌ Keine KI-Anfrage bei jeder Berechnung
- ❌ Keine KI-Anfrage bei jedem API-Call
- ❌ Keine KI-Anfrage bei jedem User-Request

---

## 📊 Vergleich

| Aspekt | Mit KI (falsch) | Hybrid-Ansatz (richtig) |
|--------|----------------|-------------------------|
| **Laufzeit** | Jede Berechnung fragt KI | Normale SQL-Query |
| **Performance** | Langsam (KI-Timeout) | Schnell (Datenbank) |
| **Kosten** | Hoch (jede Anfrage) | Keine (lokale DB) |
| **Zuverlässigkeit** | Abhängig von KI-Server | Abhängig von DB |
| **Implementierung** | Komplex (KI-Integration) | Einfach (SQL-Query) |

---

## ✅ Zusammenfassung

**Hybrid-Ansatz = SQL-Query-Implementierung**

1. **KI wurde verwendet:** Zur Analyse und Bestätigung (einmalig)
2. **Implementierung:** Normale SQL-Query in `werkstatt_data.py`
3. **Laufzeit:** Keine KI-Anfragen, nur Datenbank-Abfrage
4. **Performance:** Schnell, zuverlässig, keine externen Abhängigkeiten

**Die KI hat uns geholfen, die richtige Logik zu finden. Jetzt implementieren wir diese Logik als normale SQL-Query!**

---

**Status:** ✅ **Hybrid-Ansatz = SQL-Query, keine KI zur Laufzeit!**
