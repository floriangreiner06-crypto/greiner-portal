# Analyse Locosoft Stempelzeiten-Übersicht Excel-Datei

**Datum:** 2026-01-16 (TAG 194)  
**Datei:** `Stempelzeiten-Übersicht 01.01.26 - 15.01.26.csv`

---

## 📊 Datei-Struktur

### Spalten (Header-Zeile 6):
0. `<@@B;BorderB=t @@>` - Formatierung
1. `von` - Stempelzeit Start
2. `bis` - Stempelzeit Ende
3. (leer)
4. `Dauer` - Dauer der Stempelung
5. `MA` - Mitarbeiter-Nummer
6. `Name` - Mitarbeiter-Name
7. `Auftrag` - Auftragsnummer
8. `Pos. Art Text` - Position (z.B. "1,04 W  SYSTEMATISCHE WARTUNGSARBEITEN")
9. `AuAW` - Auftrags-AW (Vorgabe)
10. `AW-Ant.` - **AW-Anteil** (was der Mechaniker bekommt)
11. `St-Ant.` - **Stempelanteil** (Stempelzeit auf Position)
12. `%Lstgrad` - Leistungsgrad
13. `Anwes.` - Anwesenheit
14. `Produkt.` - Produktivität
15. `Pause` - Pause

---

## ✅ Erkenntnisse

### Beispiel: Jan Majer (5018), Auftrag 39276, Position 1,04 W

**Rohdaten:**
- `von`: 09:03
- `bis`: 10:00
- `Dauer`: 0:57 (57 Minuten)
- `Auftrag`: 39276
- `Pos. Art Text`: "1,04 W  Inspektion nach 180000 km ohne SWS auff."
- `AuAW`: 1:06 (66 Minuten = 1.1 Stunden)
- `AW-Ant.`: 1:06 (66 Minuten = 1.1 Stunden)
- `St-Ant.`: 0:33 (33 Minuten)
- `%Lstgrad`: 200,0%

**Berechnung:**
- Leistungsgrad = (AW-Ant. / St-Ant.) × 100
- Leistungsgrad = (66 Min / 33 Min) × 100 = **200%** ✅

**Interpretation:**
- Der Mechaniker hat **1:06 Stunden AW-Anteil** (gleich AuAW, da nur er an der Position arbeitet)
- Er hat **0:33 Stunden Stempelanteil** (33 Minuten gestempelt)
- Er war **2x schneller** als die Vorgabe (200% Leistungsgrad)

---

## 🔍 Wichtige Erkenntnisse

### 1. AW-Anteil = Stempelungen auf Positionen

**Bestätigt:** Die Locosoft-Erklärung ist korrekt:
> "Der Stmp Anteil ergibt sich aus der Summe aller Stempelungen des Monteurs auf Auftragspositionen."

**Beispiel:**
- Position 1,04 W: AW-Ant. = 1:06, St-Ant. = 0:33
- Position 1,05 W: AW-Ant. = 0:06, St-Ant. = 0:03
- **Summe:** AW-Ant. = 1:12, St-Ant. = 0:36

### 2. Anteilige Verteilung bei mehreren Mechanikern

**Wenn mehrere Mechaniker auf eine Position stempeln:**
- AW-Anteil wird **anteilig** basierend auf Stempelzeit verteilt
- Stempelanteil = Summe aller Stempelungen des Mechanikers auf die Position

**Beispiel (hypothetisch):**
- Position hat 10 AW Vorgabe
- Mechaniker A stempelt 60 Min, Mechaniker B stempelt 40 Min
- Mechaniker A: AW-Ant. = 6 AW, St-Ant. = 60 Min
- Mechaniker B: AW-Ant. = 4 AW, St-Ant. = 40 Min

### 3. Position-basierte Berechnung

**Wichtig:** Jede Zeile in der Excel-Datei entspricht:
- **Einer Stempelung** auf **einer Position**
- Nicht einer Stempelung auf einem Auftrag!

**Das bedeutet:**
- Wenn ein Mechaniker auf mehrere Positionen eines Auftrags stempelt → mehrere Zeilen
- Wenn mehrere Mechaniker auf eine Position stempeln → mehrere Zeilen (mit anteiliger AW-Verteilung)

---

## 📝 Nächste Schritte

### 1. SQL-Query anpassen

**Aktuell (DRIVE):**
- Berechnet Stempelzeit pro Auftrag
- Berechnet AW pro Mechaniker (direkt aus `labours.mechanic_no`)

**Soll (Locosoft-kompatibel):**
- Berechnet Stempelzeit pro Position/Mechaniker
- Berechnet AW-Anteil pro Position/Mechaniker (anteilige Verteilung)

### 2. Implementierung

**SQL-Ansatz:**
```sql
-- Stempelungen auf Positionen zuordnen
WITH stempelungen_mit_positionen AS (
    SELECT
        t.employee_number,
        t.order_number,
        COALESCE(t.order_position, l.order_position) as order_position,
        COALESCE(t.order_position_line, l.order_position_line) as order_position_line,
        t.start_time,
        t.end_time,
        EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 60 as stempel_minuten
    FROM times t
    JOIN labours l ON t.order_number = l.order_number
    WHERE t.type = 2
        AND t.end_time IS NOT NULL
        AND t.order_number > 31
        -- Wenn order_position NULL: Alle Positionen des Auftrags
        -- Anteilige Verteilung basierend auf AW
)
```

### 3. Validierung

**Test mit Excel-Daten:**
- Mechaniker 5018 (Jan Majer)
- Zeitraum: 01.01.26 - 15.01.26
- Vergleich: Excel vs. DRIVE-Berechnung

---

## 📊 Excel-Daten-Zusammenfassung

**Datei:** `Stempelzeiten-Übersicht 01.01.26 - 15.01.26.csv`
- **Zeilen gesamt:** 1.479
- **Zeilen mit Auftrag und MA:** 374
- **Jan Majer (5018) Zeilen:** 65

**Format:**
- Encoding: ISO-8859-1 / Latin-1
- Separator: Tab (`\t`)
- Header-Zeile: 6
- Zeit-Format: Stunden:Minuten (z.B. "1:06" = 66 Minuten)

---

**Status:** ✅ Excel-Daten erfolgreich analysiert - Bereit für SQL-Implementierung
