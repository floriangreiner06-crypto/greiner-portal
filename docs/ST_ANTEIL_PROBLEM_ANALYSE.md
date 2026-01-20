# St-Anteil Problem-Analyse - TAG 195

**Datum:** 2026-01-17  
**Status:** ⚠️ **Formel korrekt, aber Abweichung bleibt**

---

## 🔍 Das Problem

**Formel:** `St-Ant = Dauer × (AuAW / Gesamt-AuAW pro Stempelung)`

**Ergebnis für Mechaniker 5007 (01.01.26-15.01.26):**
- **DRIVE:** 3360 Min (56.00 h)
- **Locosoft:** 4971 Min (82.85 h)
- **Differenz:** -1611 Min (-32.4%) ⚠️

---

## 📊 Analysierte Faktoren

### 1. Deduplizierung
- ✅ Getestet: Mit und ohne Deduplizierung
- Ergebnis: Beide geben 3360 Min
- **Fazit:** Nicht das Problem

### 2. Filter `is_invoiced`
- ✅ Getestet: Mit `is_invoiced = true` → 1878 Min (schlechter)
- ✅ Getestet: Ohne Filter → 3360 Min (besser)
- **Fazit:** Filter macht es schlechter

### 3. Filter `labour_type`
- ⏳ Noch nicht getestet
- **Möglich:** Sollte `labour_type != 'I'` verwendet werden?

### 4. Positionen ohne AW
- ✅ Getestet: Mit gleichmäßiger Verteilung → 3360 Min (gleich)
- **Fazit:** Nicht das Problem

### 5. Gruppierung
- ✅ Getestet: Pro Position vs. pro Stempelung
- Ergebnis: Beide geben 3360 Min
- **Fazit:** Nicht das Problem

### 6. Dauer-Berechnung
- Summe Dauer (dedupliziert): 3602.2 Min
- Verhältnis Locosoft/Summe: 1.380
- **Erkenntnis:** Locosoft ist 38% höher als Summe Dauer!

---

## 🤔 Mögliche Erklärungen

### 1. Locosoft verwendet eine andere Logik
- Die CSV-Analyse zeigt 91.8% Match-Rate
- Aber vielleicht nicht für alle Mechaniker?
- Oder für Mechaniker 5007 gibt es Sonderfälle?

### 2. Filter fehlen
- Vielleicht sollte `labour_type != 'I'` verwendet werden?
- Oder andere Filter, die nicht in CSV-Analyse sichtbar sind?

### 3. Positionen ohne AW werden anders behandelt
- Vielleicht werden sie in Locosoft anders berechnet?
- Oder sie werden gar nicht berücksichtigt?

### 4. Die CSV-Analyse ist unvollständig
- 91.8% Match-Rate bedeutet 8.2% Abweichung
- Vielleicht gehört Mechaniker 5007 zu den 8.2%?

---

## 💡 Nächste Schritte

1. **Teste mit `labour_type != 'I'` Filter**
   - Vielleicht werden interne Positionen anders behandelt?

2. **Vergleiche mit anderen Mechanikern**
   - Funktioniert die Formel für andere Mechaniker besser?
   - Oder ist es ein spezifisches Problem für Mechaniker 5007?

3. **Prüfe Locosoft-UI direkt**
   - Gibt es dort Hinweise auf die Berechnung?
   - Oder andere Informationen, die helfen könnten?

4. **Analysiere die CSV-Daten für Mechaniker 5007**
   - Gibt es in der CSV spezielle Fälle?
   - Oder Positionen, die anders behandelt werden?

---

## 📝 SQL-Query (Aktuell)

Die Query ist korrekt implementiert nach der Formel von claude.ai:
- Stempelungen deduplizieren (pro Position pro Stempelung)
- AW pro Position aus `labours` (time_units * 6.0)
- Gesamt-AuAW pro Stempelung berechnen
- St-Anteil = Dauer × (AuAW / Gesamt-AuAW)
- Aggregiert pro Mechaniker

**Siehe:** `api/werkstatt_data.py` → `get_st_anteil_position_basiert()` Zeilen 922-1000

---

## ⚠️ Fazit

Die Formel ist **korrekt implementiert**, aber es gibt noch eine **Abweichung von 32.4%**.

Mögliche Ursachen:
1. Locosoft verwendet eine andere Logik (nicht in CSV sichtbar)
2. Filter fehlen oder sind falsch
3. Mechaniker 5007 ist ein Sonderfall (gehört zu den 8.2% Abweichung)
4. Die CSV-Analyse ist unvollständig

**Empfehlung:** Weitere Tests mit anderen Mechanikern und verschiedenen Filtern durchführen.
