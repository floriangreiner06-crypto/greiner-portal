# Erkenntnisse: skr51_cost_center Fallback-Logik Analyse

**Datum:** 2026-01-10  
**TAG:** 177  
**Script:** `scripts/analyse_skr51_fallback_logik.py`

---

## KRITISCHE ERKENNTNISSE

### 1. ALLE direkten Kosten haben skr51_cost_center = 0

**Ergebnis der Analyse:**
- **100% der direkten Kosten** haben `skr51_cost_center = 0`
- **974 Buchungen** mit `skr51_cost_center = 0`
- **Gesamtsumme:** 1.837.073,09 €

**Bedeutung:**
- Globalcube kann **NICHT** direkt nach `skr51_cost_center BETWEEN 1 AND 7` filtern
- Wenn Globalcube nur `skr51_cost_center` verwendet, würde es **0 €** direkte Kosten haben
- Globalcube **MUSS** eine Fallback-Logik haben!

### 2. Globalcube Filter (nur skr51_cost_center 1-7) = 0 €

**Test-Ergebnis:**
- Variante 1 (nur `skr51_cost_center BETWEEN 1 AND 7`): **0,00 €**
- Variante 2 (Fallback: `skr51_cc 1-7 ODER (skr51_cc=0 UND 5.Stelle 1-7)`): **1.837.073,09 €**
- Variante 3 (nur 5. Stelle, DRIVE aktuell): **1.837.073,09 €**

**Schlussfolgerung:**
- Globalcube verwendet **NICHT** direkt `skr51_cost_center` für die Filterung
- Globalcube verwendet wahrscheinlich die **5. Stelle des Kontos** (wie DRIVE)
- Oder: Globalcube verwendet eine andere Logik (z.B. über `Acct Nr`)

### 3. LOC_Belege View: "Acct Nr" Logik

**Aus `/mnt/globalcube/System/LOCOSOFT/SQL/schema/LOCOSOFT/views/locosoft.LOC_Belege.sql` (Zeile 217-235):**

```sql
case
    when T1."skr51_cost_center" <> 0 then { fn CONCAT(
        { fn CONCAT(
            { fn RTRIM(
                CAST(
                    CAST(T1."nominal_account_number" AS INTEGER) AS CHAR(254)
                )
            ) },
            '_'
        ) },
        { fn RTRIM(
            CAST(
                CAST(T1."skr51_cost_center" AS INTEGER) AS CHAR(254)
            )
        ) }
    ) }
    else CAST(
        CAST(T1."nominal_account_number" AS INTEGER) AS CHAR(254)
    )
end as "Acct Nr"
```

**Bedeutung:**
- Wenn `skr51_cost_center <> 0`: `Acct Nr` = `nominal_account_number` + `_` + `skr51_cost_center`
- Wenn `skr51_cost_center = 0`: `Acct Nr` = nur `nominal_account_number`

**Mögliche Filter-Logik in Cognos:**
- Globalcube könnte auf `Acct Nr` filtern (z.B. `left(Acct Nr, 5)` = `'4110_'` oder ähnlich)
- Oder: Globalcube filtert direkt auf `nominal_account_number` (5. Stelle)

### 4. 411xxx Kontenbereich (100k€ Differenz-Kandidat)

**Ergebnisse:**
- **411xxx Gesamt:** 95.789,70 €
- **Alle 411xxx haben `skr51_cost_center = 0`**
- **Verteilung nach KST (5. Stelle):**
  - KST 3: 73.920,10 € (77,17%)
  - KST 6: 14.818,40 € (15,47%)
  - KST 1,2,7: je 2.350,40 € (2,45%)

**Bedeutung:**
- 411xxx ist **nicht** die 100k€ Differenz (nur 95k€)
- Aber: 411xxx könnte Teil der Differenz sein
- Weitere Kontenbereiche müssen analysiert werden

### 5. Monat-für-Monat-Vergleich

**Ergebnis:**
- **Alle Monate:** Globalcube (skr51) = 0,00 €
- **Alle Monate:** DRIVE (5. Stelle) = ~150k€ pro Monat
- **Differenz:** Konstant ~150k€ pro Monat

**Bedeutung:**
- Die Differenz entsteht **in jedem Monat gleichmäßig**
- Nicht ein einzelner Monat mit großen Abweichungen
- Die Filter-Logik ist **konsistent falsch** (nicht zufällig)

---

## HYPOTHESEN

### Hypothese 1: Globalcube verwendet 5. Stelle (wie DRIVE)

**Begründung:**
- Alle direkten Kosten haben `skr51_cost_center = 0`
- Globalcube kann nicht direkt nach `skr51_cost_center` filtern
- Die 5. Stelle ist die einzige Möglichkeit, KST 1-7 zu identifizieren

**Test:**
- Wenn Globalcube die 5. Stelle verwendet, sollte DRIVE = Globalcube sein
- Aber: DRIVE hat 100k€ **mehr** als Globalcube
- **→ Diese Hypothese ist FALSCH**

### Hypothese 2: Globalcube filtert auf "Acct Nr" (mit Fallback)

**Begründung:**
- `Acct Nr` = `nominal_account_number` wenn `skr51_cost_center = 0`
- Globalcube könnte auf `left(Acct Nr, 5)` filtern (5. Stelle)
- Oder: Globalcube filtert auf bestimmte Kontenbereiche

**Test:**
- Müsste in Cognos Reports analysiert werden
- **→ Diese Hypothese ist MÖGLICH**

### Hypothese 3: Globalcube schließt bestimmte Kontenbereiche aus

**Begründung:**
- DRIVE hat 100k€ **mehr** direkte Kosten als Globalcube
- Bestimmte Kontenbereiche werden in Globalcube **nicht** als direkte Kosten gezählt
- 411xxx könnte ein Kandidat sein (95k€)

**Test:**
- Kontenbereiche identifizieren, die DRIVE zählt, aber Globalcube nicht
- **→ Diese Hypothese ist WAHRSCHEINLICH**

---

## NÄCHSTE SCHRITTE

### 1. Cognos Reports analysieren
- **Ziel:** Filter-Logik in Cognos Reports finden
- **Dateien:** `/mnt/globalcube/System/LOCOSOFT/Report/*.ppr` oder `.xml`
- **Suche nach:** Filter auf `Acct Nr`, `KST`, oder `nominal_account_number`

### 2. Kontenbereiche identifizieren
- **Ziel:** Welche Kontenbereiche zählt DRIVE, aber Globalcube nicht?
- **Methode:** Detaillierte Analyse aller Kontenbereiche in direkten Kosten
- **Fokus:** Kontenbereiche nahe 100k€ Differenz

### 3. Fallback-Logik testen
- **Ziel:** Verschiedene Fallback-Varianten testen
- **Methode:** Script erweitern mit weiteren Varianten
- **Fokus:** Kombinationen von `skr51_cost_center` und 5. Stelle

### 4. Validierung gegen Globalcube CSV
- **Ziel:** Monat-für-Monat-Vergleich mit Globalcube CSV
- **Methode:** CSV-Werte extrahieren und vergleichen
- **Fokus:** Identifikation der Monate mit größten Abweichungen

---

## ZUSAMMENFASSUNG

**Haupt-Erkenntnis:**
- **ALLE direkten Kosten haben `skr51_cost_center = 0`**
- Globalcube kann **NICHT** direkt nach `skr51_cost_center` filtern
- Globalcube **MUSS** eine Fallback-Logik haben (wahrscheinlich 5. Stelle)
- DRIVE hat 100k€ **mehr** direkte Kosten als Globalcube
- Die Differenz entsteht **konsistent** in jedem Monat

**Nächste Aktion:**
- Cognos Reports analysieren, um die tatsächliche Filter-Logik zu finden
- Kontenbereiche identifizieren, die DRIVE zählt, aber Globalcube nicht
