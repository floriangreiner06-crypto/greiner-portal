# Kontext: St-Anteil Berechnungsproblem für lokale KI

**Datum:** 2026-01-16  
**Problem:** St-Anteil (Stempel Anteil) Berechnung weicht von Locosoft ab

---

## 🎯 Problem-Zusammenfassung

Bei der Berechnung des "St-Anteil" (Stempel Anteil) für Mechaniker zeigen sich große Abweichungen zwischen unserer DRIVE-Implementierung und Locosoft, insbesondere bei Mechanikern mit vielen Stempelungen auf mehrere Positionen oder Positionen ohne Arbeitswerte (AW).

---

## 📊 Konkretes Beispiel

**Mechaniker:** 5007 (Reitmeier, Tobias)  
**Zeitraum:** 01.01.2026 - 16.01.2026

| Metrik | DRIVE | Locosoft | Differenz | Status |
|--------|-------|----------|-----------|--------|
| **AW-Anteil** | 3192 Min (53:12) | 3155 Min (52:35) | 37 Min (1.2%) | ✅ Sehr gut |
| **St-Anteil** | 3360 Min (56:00) | 4971 Min (82:51) | 1611 Min (32.4%) | ❌ Problem |
| **Leistungsgrad** | 88.5% | 63.5% | 25.0% | ❌ Problem |

**Bei anderem Mechaniker (5014) passt es besser:**
- St-Anteil: DRIVE 2082 Min vs. Locosoft 2078 Min (nur 4 Min Diff, 0.2%) ✅

---

## 🔍 Datenstruktur bei Problem-Mechaniker (5007)

- **300 Stempelungen** auf **206 Positionen**
- **203 Positionen OHNE AW** mit **12049 Min** Stempelzeit
- **43 von 57 Stempelungen** gehen auf **mehrere Positionen** (75.4%)
- **Stempelzeit auf mehrere Positionen:** 2585 Min

---

## 💻 Unsere aktuelle Implementierung

**Position-basierte Berechnung mit anteiliger Verteilung:**

1. **Stempelungen deduplizieren** pro Mechaniker/Auftrag/Position/Zeit
2. **Anteilige Verteilung** bei Stempelungen auf mehrere Positionen:
   - Wenn eine Stempelung auf mehrere Positionen geht, wird die Stempelzeit anteilig nach AW verteilt
   - Beispiel: 60 Min Stempelung auf Position 1.1 (10 AW) und 1.2 (10 AW)
     → 30 Min pro Position = 30 Min St-Anteil
3. **Aggregation** pro Position und Mechaniker

**SQL-Query:** Siehe `api/werkstatt_data.py`, Methode `get_mechaniker_leistung()` (ab Zeile 446)

---

## 🧪 Getestete Berechnungsvarianten

| # | Variante | Ergebnis | Diff zu Locosoft | Status |
|---|----------|----------|------------------|--------|
| 1 | Position-basiert (anteilig verteilt) | 3360 Min | 1611 Min (32.4%) | ❌ |
| 2 | OHNE anteilige Verteilung | 3602 Min | 1369 Min (27.5%) | ❌ |
| **3** | **Zeit-Spanne (erste bis letzte Stempelung)** | **3691 Min** | **1280 Min (25.7%)** | ⚠️ **AM NÄCHSTEN!** |
| 4 | Zeit-Spanne MINUS Lücken | 3602 Min | 1369 Min (27.5%) | ❌ |
| 5 | Zeit-Spanne MINUS Lücken MINUS Pausen | 3294 Min | 1677 Min (33.7%) | ❌ |
| 6 | Pro Position (summiert, nur MIT AW) | 6624 Min | 1653 Min (33.3%) | ❌ |
| 7 | MIT AW anteilig + OHNE AW gesamte Stempelzeit | 15409 Min | 10438 Min (210.0%) | ❌ |

**Keine der Varianten passt genau zu Locosoft's 4971 Min!**

---

## 📁 Relevante Dateien

1. **`api/werkstatt_data.py`** (Zeile 446-588)
   - Methode: `get_mechaniker_leistung()`
   - Enthält die SQL-Query für St-Anteil-Berechnung

2. **`docs/locosoft_anfrage_st_anteil_berechnung_TAG194.md`**
   - Detaillierte Anfrage an Locosoft Support

3. **`docs/ANALYSE_ABWEICHUNG_TOBIAS_TAG194.md`**
   - Analyse warum Abweichung bei Tobias größer ist

4. **`docs/SUCHE_1369_MIN_DIFFERENZ_TAG194.md`**
   - Systematische Suche nach der Differenz

---

## 🗄️ Datenbank-Schema

**Tabellen:**
- `times` - Stempelungen (type=2 = Arbeitszeit)
- `labours` - Arbeitswerte (time_units = AW)
- `orders` - Aufträge

**Filter:**
- `times.type = 2` (Arbeitszeit)
- `times.order_number > 31` (externe Aufträge)
- `times.order_position IS NOT NULL`
- `times.order_position_line IS NOT NULL`

**Wichtige Spalten:**
- `times.employee_number` - Mechaniker-Nr
- `times.order_number` - Auftrags-Nr
- `times.order_position` - Position
- `times.order_position_line` - Positionszeile
- `times.start_time` / `times.end_time` - Stempelzeit
- `labours.time_units` - AW (Arbeitswerte)
- `labours.labour_type` - Typ (z.B. 'I' = intern)

---

## ❓ Offene Fragen

1. **Wie wird "St-Anteil" in Locosoft genau berechnet?**
   - Wird die Stempelzeit anteilig verteilt, wenn eine Stempelung auf mehrere Positionen geht?
   - Oder wird die gesamte Stempelzeit gezählt?

2. **Werden Positionen OHNE AW (time_units = 0) berücksichtigt?**
   - Wenn ja, wie wird die Stempelzeit für diese Positionen berechnet?

3. **Gibt es Unterschiede zwischen "St-Anteil" und "Stmp.Anteil"?**
   - Werden beide gleich berechnet?

4. **Wie werden Stempelungen dedupliziert?**
   - Pro Mechaniker/Auftrag/Position/Zeit?
   - Oder gibt es eine andere Deduplizierungslogik?

5. **Werden bestimmte Aufträge oder Positionen ausgeschlossen?**
   - Gibt es Filter, die wir noch nicht berücksichtigen?

---

## 🎯 Ziel

Die genaue Berechnungslogik von Locosoft's "St-Anteil" verstehen und in DRIVE korrekt nachbilden, damit die KPI-Berechnungen übereinstimmen.

---

## 📝 Nächste Schritte

1. ✅ Anfrage an Locosoft Support erstellt
2. ⏳ Auf Antwort von Locosoft warten
3. 🔍 Weitere Analyse mit lokaler KI (dieses Dokument)
4. 🔧 Anpassung der Berechnung basierend auf Erkenntnissen

---

## 💡 Mögliche Ansätze für lokale KI

1. **SQL-Query-Analyse:**
   - Prüfe ob die SQL-Query-Logik korrekt ist
   - Suche nach möglichen Fehlern in der Deduplizierung oder Aggregation

2. **Alternative Berechnungslogik:**
   - Vielleicht gibt es eine andere Logik, die wir noch nicht getestet haben?
   - Kombinationen verschiedener Ansätze?

3. **Datenanalyse:**
   - Prüfe ob es spezielle Muster in den Daten gibt
   - Warum passt es bei Mechaniker 5014 besser als bei 5007?

4. **Pattern-Matching:**
   - Suche nach Mustern zwischen den verschiedenen Berechnungsvarianten
   - Kann die Differenz (1280 Min) erklärt werden?
