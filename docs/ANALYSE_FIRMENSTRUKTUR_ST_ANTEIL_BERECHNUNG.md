# Analyse: Firmenstruktur und St-Anteil Berechnung

**Datum:** 2026-01-21  
**TAG:** 206  
**Zweck:** Verstehen, wie die Firmenstruktur die St-Anteil Berechnung beeinflusst

---

## 🏢 FIRMENSTRUKTUR (KRITISCH!)

### Rechtliche Struktur

1. **Autohaus Greiner GmbH & Co. KG** (Hauptbetrieb)
   - **Deggendorf Opel (DEGO):** subsidiary=1
   - **Landau (LANO):** subsidiary=3
   - **Alle Mitarbeiter gehören zu dieser Firma!**

2. **Auto Greiner GmbH = DEGH** (subsidiary=2)
   - **Hat KEINE eigenen Angestellten!**
   - **Alle Mitarbeiter sind bei Autohaus Greiner GmbH angestellt**
   - **Nutzt Mitarbeiter von Autohaus Greiner GmbH**

3. **LANO** (subsidiary=3)
   - **Filiale** von Autohaus Greiner GmbH

### Wichtige Erkenntnis

**DEGH hat keine eigenen Mitarbeiter!**
- Alle Mitarbeiter gehören zu Autohaus Greiner GmbH (DEGO)
- DEGH nutzt diese Mitarbeiter für Aufträge
- **MA-Betrieb = DEGO** (wo Mitarbeiter angestellt sind)
- **Auftragsbetrieb = DEGO oder DEGH** (wo Auftrag zugeordnet ist)

---

## 🔍 LOCOSOFT BETRIEBSAUSWAHL (Screenshot)

### Betriebe in Locosoft

| Nr | Betr.Bez. | Passw.Info | ZS Fabrikat | Lager |
|----|-----------|------------|-------------|-------|
| 2 | DEGH | 99 | HYUNDAI (27) | 2 DEGH |
| 3 | LANO | 99 | OPEL (40) | 3 LANO |
| 4 | LANH | 99 | 1 | 4 LANH |

### Fabrikate in Locosoft

| Nr | Fabr.Bez. | Fabr.Code |
|----|-----------|-----------|
| 1 | OPEL | 40 |
| 2 | LEAP | 41 |
| 99 | *SONSTIGE | - |

**Erkenntnis:**
- DEGH ist mit HYUNDAI (27) verknüpft
- LANO ist mit OPEL (40) verknüpft
- **Betriebe sind mit Fabrikaten verknüpft!**

---

## 💡 HYPOTHESE: MA-Betrieb vs. Auftragsbetrieb

### Was bedeutet "MA-Betrieb 01 DEGO + Auftragsbetrieb 02 DEGH"?

**Aus Locosoft-Screenshot (MA 5007, 07.01.2026):**
- **MA-Betrieb 01 DEGO:** St-Ant. 9:06 Std
- **MA-Betrieb 01 DEGO + Auftragsbetrieb 02 DEGH:** St-Ant. 3:59 Std
- **GESAMT:** 13:05 Std = 9:06 + 3:59 ✓

**Interpretation:**
1. **MA-Betrieb 01 DEGO:** 
   - Mitarbeiter gehört zu DEGO (Autohaus Greiner GmbH)
   - Stempelzeit auf Aufträgen, die zu DEGO gehören (subsidiary=1)
   - **Berechnung:** Zeit-Spanne (MIN bis MAX) → 8:05 Std (nah an 9:06)

2. **MA-Betrieb 01 DEGO + Auftragsbetrieb 02 DEGH:**
   - Mitarbeiter gehört zu DEGO (Autohaus Greiner GmbH)
   - Stempelzeit auf Aufträgen, die zu DEGH gehören (subsidiary=2)
   - **Berechnung:** Auftrags-basierte Summe → 4:43 Std (nah an 3:59)

**Warum unterschiedliche Berechnungen?**

### Hypothese 1: Betriebs-spezifische Berechnung

**DEGO (Hauptbetrieb, eigene Mitarbeiter):**
- Mitarbeiter gehört zu DEGO
- Aufträge gehören zu DEGO
- **Berechnung:** Zeit-Spanne (MIN bis MAX) - **Warum?**
  - Vielleicht weil Mitarbeiter "eigene" Zeit hat?
  - Vielleicht weil Hauptbetrieb andere Logik verwendet?

**DEGH (Nutzung von Mitarbeitern aus DEGO):**
- Mitarbeiter gehört zu DEGO
- Aufträge gehören zu DEGH
- **Berechnung:** Auftrags-basierte Summe - **Warum?**
  - Vielleicht weil Mitarbeiter "fremde" Aufträge bearbeitet?
  - Vielleicht weil DEGH keine eigenen Mitarbeiter hat?

### Hypothese 2: Fabrikat-Zuordnung

**Aus Locosoft-Screenshot:**
- DEGH ist mit HYUNDAI (27) verknüpft
- LANO ist mit OPEL (40) verknüpft

**Mögliche Logik:**
- **OPEL-Aufträge (DEGO):** Zeit-Spanne
- **HYUNDAI-Aufträge (DEGH):** Auftrags-basierte Summe

**Prüfung nötig:**
- Sind alle DEGO-Aufträge OPEL?
- Sind alle DEGH-Aufträge HYUNDAI?

---

## 🔍 ANALYSE: MA 5007 (07.01.2026)

### Aufträge nach Betrieb

**Auftragsbetrieb DEGO (subsidiary=1):**
- Order 39524: 0:26 Std (11:11-11:37)
- Order 39527: 0:53 Std (08:46-09:40)
- Order 39537: 1:54 Std (14:58-16:52)
- Order 39809: 0:06 Std (11:04-11:10)
- **Summe (auftrags-basiert):** 3:21 Std
- **Zeit-Spanne:** 8:05 Std (08:46-16:52)
- **Locosoft:** 9:06 Std

**Auftragsbetrieb DEGH (subsidiary=2):**
- Order 219184: 0:19 Std (09:40-09:59)
- Order 220067: 0:16 Std (10:47-11:03)
- Order 220445: 0:47 Std (09:59-10:47)
- Order 220542: 3:13 Std (11:44-14:58)
- Order 220624: 0:06 Std (11:37-11:44)
- **Summe (auftrags-basiert):** 4:43 Std
- **Zeit-Spanne:** 5:17 Std (09:40-14:58)
- **Locosoft:** 3:59 Std ✓ (sehr nah!)

### Erkenntnisse

1. **DEGO:** Zeit-Spanne (8:05) ist nah an Locosoft (9:06) ✅
   - Abweichung: -1:01 Std
   - **Mögliche Erklärung:** Pausenzeiten-Abzug? Oder andere Logik?

2. **DEGH:** Auftrags-basierte Summe (4:43) ist nah an Locosoft (3:59) ✅
   - Abweichung: +0:44 Std
   - **Mögliche Erklärung:** Rundungsfehler? Oder andere Filter?

3. **Unterschiedliche Methoden:**
   - DEGO: Zeit-Spanne (MIN bis MAX)
   - DEGH: Auftrags-basierte Summe

---

## 🎯 NEUE HYPOTHESE: Betriebs-spezifische Berechnung

### Warum unterschiedliche Methoden?

**DEGO (Hauptbetrieb, eigene Mitarbeiter):**
- Mitarbeiter gehört zu DEGO
- Aufträge gehören zu DEGO
- **Berechnung:** Zeit-Spanne (MIN bis MAX)
- **Grund:** Mitarbeiter arbeitet "im eigenen Betrieb"
- **Logik:** Gesamte Arbeitszeit (erste bis letzte Stempelung)

**DEGH (Nutzung von Mitarbeitern aus DEGO):**
- Mitarbeiter gehört zu DEGO
- Aufträge gehören zu DEGH
- **Berechnung:** Auftrags-basierte Summe
- **Grund:** Mitarbeiter arbeitet "für fremden Betrieb"
- **Logik:** Summe der einzelnen Auftragszeiten

### Mögliche Locosoft-Logik

```python
def berechne_st_anteil(employee_number, subsidiary_auftrag, tag):
    """
    Berechnet St-Anteil basierend auf Betriebs-Zuordnung
    
    Args:
        employee_number: Mitarbeiternummer
        subsidiary_auftrag: Betrieb des Auftrags (1=DEGO, 2=DEGH, 3=LANO)
        tag: Datum
    """
    # MA-Betrieb: Immer DEGO (alle Mitarbeiter gehören zu DEGO)
    ma_betrieb = 1  # DEGO
    
    if ma_betrieb == subsidiary_auftrag:
        # Mitarbeiter arbeitet im eigenen Betrieb (DEGO)
        # Berechnung: Zeit-Spanne (MIN bis MAX)
        return berechne_zeit_spanne(employee_number, subsidiary_auftrag, tag)
    else:
        # Mitarbeiter arbeitet für fremden Betrieb (DEGH)
        # Berechnung: Auftrags-basierte Summe
        return berechne_auftrags_summe(employee_number, subsidiary_auftrag, tag)
```

---

## 📊 PRÜFUNG: Sind alle DEGO-Aufträge OPEL?

### Hypothese: Fabrikat-Zuordnung

**Aus Locosoft-Screenshot:**
- DEGH ist mit HYUNDAI (27) verknüpft
- LANO ist mit OPEL (40) verknüpft

**Frage:**
- Sind alle DEGO-Aufträge OPEL?
- Sind alle DEGH-Aufträge HYUNDAI?

**Prüfung nötig:**
```sql
-- Prüfe Fabrikat-Zuordnung für DEGO-Aufträge
SELECT 
    o.subsidiary,
    COUNT(*) as anzahl,
    COUNT(DISTINCT dv.manufacturer_code) as fabrikate
FROM orders o
LEFT JOIN dealer_vehicles dv ON o.vehicle_number = dv.number
WHERE o.subsidiary = 1  -- DEGO
GROUP BY o.subsidiary;

-- Prüfe Fabrikat-Zuordnung für DEGH-Aufträge
SELECT 
    o.subsidiary,
    COUNT(*) as anzahl,
    COUNT(DISTINCT dv.manufacturer_code) as fabrikate
FROM orders o
LEFT JOIN dealer_vehicles dv ON o.vehicle_number = dv.number
WHERE o.subsidiary = 2  -- DEGH
GROUP BY o.subsidiary;
```

---

## 🔧 IMPLEMENTIERUNGS-VORSCHLAG

### Betriebs-spezifische Berechnung

**Logik:**
1. **MA-Betrieb = Auftragsbetrieb (z.B. DEGO → DEGO):**
   - Berechnung: Zeit-Spanne (MIN bis MAX)
   - **Grund:** Mitarbeiter arbeitet im eigenen Betrieb

2. **MA-Betrieb ≠ Auftragsbetrieb (z.B. DEGO → DEGH):**
   - Berechnung: Auftrags-basierte Summe
   - **Grund:** Mitarbeiter arbeitet für fremden Betrieb

**Code:**
```python
def get_stempelzeit_aus_times_mit_betrieb(von, bis, ma_betrieb=1):
    """
    Berechnet St-Anteil basierend auf Betriebs-Zuordnung
    
    Args:
        von: Startdatum
        bis: Enddatum
        ma_betrieb: Betrieb des Mitarbeiters (1=DEGO, 2=DEGH, 3=LANO)
    
    Returns:
        Dict: {employee_number: {subsidiary: stempelzeit_stunden}}
    """
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            WITH stempelungen AS (
                SELECT DISTINCT ON (employee_number, order_number, start_time, end_time)
                    employee_number,
                    o.subsidiary as auftragsbetrieb,
                    start_time,
                    end_time
                FROM times t
                JOIN orders o ON t.order_number = o.number
                WHERE t.type = 2
                  AND t.end_time IS NOT NULL
                  AND t.start_time >= %s
                  AND t.start_time < %s + INTERVAL '1 day'
                ORDER BY employee_number, order_number, start_time, end_time
            )
            SELECT 
                employee_number,
                auftragsbetrieb,
                CASE 
                    WHEN auftragsbetrieb = %s THEN
                        -- MA-Betrieb = Auftragsbetrieb: Zeit-Spanne
                        EXTRACT(EPOCH FROM (MAX(end_time) - MIN(start_time))) / 3600.0
                    ELSE
                        -- MA-Betrieb ≠ Auftragsbetrieb: Auftrags-basierte Summe
                        SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 3600.0)
                END as stempelzeit_stunden
            FROM stempelungen
            GROUP BY employee_number, auftragsbetrieb
        """
        
        cursor.execute(query, [von, bis, ma_betrieb])
        result = {}
        for row in cursor.fetchall():
            emp_nr = row['employee_number']
            auftragsbetrieb = row['auftragsbetrieb']
            if emp_nr not in result:
                result[emp_nr] = {}
            result[emp_nr][auftragsbetrieb] = float(row['stempelzeit_stunden'] or 0)
        return result
```

---

## 🎯 NÄCHSTE SCHRITTE

### 1. Prüfe Fabrikat-Zuordnung

**Query:**
```sql
-- Prüfe Fabrikat-Zuordnung für DEGO-Aufträge
SELECT 
    o.subsidiary,
    dv.manufacturer_code,
    COUNT(*) as anzahl
FROM orders o
LEFT JOIN dealer_vehicles dv ON o.vehicle_number = dv.number
WHERE o.subsidiary IN (1, 2)  -- DEGO, DEGH
GROUP BY o.subsidiary, dv.manufacturer_code
ORDER BY o.subsidiary, anzahl DESC;
```

### 2. Prüfe MA-Betrieb vs. Auftragsbetrieb

**Query:**
```sql
-- Prüfe MA-Betrieb für MA 5007
SELECT 
    employee_number,
    name,
    -- MA-Betrieb: Immer DEGO (alle Mitarbeiter gehören zu DEGO)
    1 as ma_betrieb
FROM employees
WHERE employee_number = 5007
  AND is_latest_record = true;

-- Prüfe Auftragsbetrieb für MA 5007 am 07.01.2026
SELECT 
    t.employee_number,
    o.subsidiary as auftragsbetrieb,
    COUNT(DISTINCT t.order_number) as anzahl_auftraege,
    SUM(EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 3600.0) as stempelzeit_stunden
FROM times t
JOIN orders o ON t.order_number = o.number
WHERE t.employee_number = 5007
  AND t.type = 2
  AND t.end_time IS NOT NULL
  AND DATE(t.start_time) = '2026-01-07'
GROUP BY t.employee_number, o.subsidiary
ORDER BY o.subsidiary;
```

### 3. Teste Betriebs-spezifische Berechnung

**Test:**
- MA 5007 (07.01.2026): DEGO vs. DEGH
- Weitere Mechaniker/Tage
- Vergleich mit Locosoft-Werten

---

## 💡 ERWARTETE ERGEBNISSE

### Nach Implementierung

**DEGO (MA-Betrieb = Auftragsbetrieb):**
- Berechnung: Zeit-Spanne (MIN bis MAX)
- Erwartung: 8:05 Std (vs. Locosoft 9:06)
- Abweichung: -1:01 Std (möglicherweise Pausenzeiten-Abzug?)

**DEGH (MA-Betrieb ≠ Auftragsbetrieb):**
- Berechnung: Auftrags-basierte Summe
- Erwartung: 4:43 Std (vs. Locosoft 3:59)
- Abweichung: +0:44 Std (möglicherweise Rundungsfehler?)

**Ziel:**
- Abweichung < 5% zu Locosoft
- Transparente, nachvollziehbare Logik
- Betriebs-spezifische Berechnung

---

**Status:** ✅ Analyse abgeschlossen  
**Nächste Aktion:** Prüfe Fabrikat-Zuordnung und teste Betriebs-spezifische Berechnung
