# St-Anteil-Berechnung - Neue Logik basierend auf Excel-Analyse

**Datum:** 2026-01-XX  
**Status:** ✅ Implementierung basierend auf Benutzer-Hinweisen

---

## Logik (aus Benutzer-Hinweisen)

### 1. Ein Mechaniker stempelt auf mehrere Positionen eines Auftrags

**Szenario:** Ein Mechaniker stempelt bei einem Auftrag mit gängigen Tätigkeiten gleich 3 Positionen auf einmal an.

**Berechnung:**
- Die Realzeit wird **gleichmäßig auf die drei Vorgabezeiten (AuAW) verteilt**
- St-Anteil pro Position = Realzeit × (AuAW_Position / Summe_AuAW_Auftrag)

**Beispiel:**
- Mechaniker stempelt 60 Min auf Auftrag mit 3 Positionen:
  - Position 1: AuAW = 30 Min
  - Position 2: AuAW = 20 Min
  - Position 3: AuAW = 10 Min
  - Summe AuAW = 60 Min
- St-Anteil:
  - Position 1: 60 × (30/60) = 30 Min
  - Position 2: 60 × (20/60) = 20 Min
  - Position 3: 60 × (10/60) = 10 Min

### 2. Mehrere Mechaniker stempeln auf verschiedene Positionen eines Auftrags

**Szenario:** Mehrere Mechaniker stoppen auf einen Auftrag auf verschiedene Positionen.

**Berechnung:**
- Dann gilt die **Vorgabezeit/AW der Position**
- AW-Anteil = AuAW_Position (direkt, keine Verteilung)

### 3. Positionen ohne Vorgabe (AuAW)

**Szenario:** Gibt es keine Vorgabe (AuAW = 0), wird anteilig nach Realzeit verteilt.

**Berechnung:**
- Für die Zeit, die der Mechaniker auf der Position ohne AW-Vorgabe war
- St-Anteil = Realzeit × (Realzeit_Position / Summe_Realzeit_Auftrag)

---

## Implementierung

**Datei:** `api/werkstatt_data.py` → `get_st_anteil_position_basiert()`

**Logik:**
1. Stempelungen deduplizieren (pro Mechaniker/Auftrag/Zeit)
2. Für jede Stempelung:
   - Wenn Positionen MIT AuAW: St-Anteil = Realzeit × (AuAW_Position / Summe_AuAW_Auftrag)
   - Wenn Positionen OHNE AuAW: St-Anteil = Realzeit × (Realzeit_Position / Summe_Realzeit_Auftrag)
3. Summe pro Mechaniker

---

**Status:** ✅ Implementierung in Arbeit
