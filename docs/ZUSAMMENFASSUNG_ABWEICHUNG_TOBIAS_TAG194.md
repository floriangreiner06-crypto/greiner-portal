# Zusammenfassung: Analyse Abweichung bei Tobias - TAG 194

**Datum:** 2026-01-16  
**Problem:** St-Anteil bei Tobias (5007) zeigt große Abweichung (32.4%)

---

## 📊 Vergleich Tobias vs. Litwin

| Metrik | Tobias (5007) | Litwin (5014) |
|--------|---------------|---------------|
| **Stempelungen** | 300 | 176 |
| **Positionen** | 206 | 148 |
| **Positionen OHNE AW** | 203 (12049 Min) | ? |
| **Stempelungen auf mehrere Positionen** | 43 von 57 (75.4%) | 19 von 24 (79.2%) |
| **Stempelzeit auf mehrere Positionen** | 2585 Min | 1935 Min |
| **Position-basierte St-Anteil** | 3360 Min | 2257 Min |
| **St-Anteil OHNE anteilige Verteilung** | 3602 Min | 2257 Min |
| **Locosoft St-Anteil** | 4971 Min | 2078 Min |
| **Differenz** | 1611 Min (32.4%) | 179 Min (8.6%) |

---

## 🔍 Erkenntnisse

### 1. Tobias hat viele Positionen OHNE AW
- **203 Positionen OHNE AW** mit **12049 Min** Stempelzeit
- Diese Positionen werden möglicherweise in Locosoft anders behandelt

### 2. St-Anteil OHNE anteilige Verteilung
- **Tobias:** 3602 Min (vs. Locosoft 4971 Min, Diff: 1369 Min, 27.5%)
- **Litwin:** 2257 Min (vs. Locosoft 2078 Min, Diff: 179 Min, 8.6%)

**Fazit:** Bei Litwin passt es besser OHNE anteilige Verteilung, bei Tobias immer noch große Abweichung.

### 3. Mögliche Ursachen

#### A) Positionen OHNE AW werden anders behandelt
- Vielleicht werden Positionen OHNE AW in Locosoft mit der **gesamten Stempelzeit** gezählt
- Nicht anteilig verteilt

#### B) Zusätzliche Stempelzeit bei Tobias
- Locosoft zeigt 4971 Min, unsere Berechnung OHNE anteilige Verteilung: 3602 Min
- **Differenz: 1369 Min** (ca. 22.8 Stunden)
- Möglicherweise werden bei Tobias zusätzliche Stempelungen berücksichtigt?

#### C) Unterschiedliche Deduplizierung
- Vielleicht verwendet Locosoft eine andere Deduplizierungslogik?
- Oder berücksichtigt Locosoft Stempelungen, die wir ausschließen?

---

## 💡 Hypothesen

### Hypothese 1: Positionen OHNE AW werden mit gesamter Stempelzeit gezählt
- Positionen MIT AW: anteilig verteilt
- Positionen OHNE AW: gesamte Stempelzeit

### Hypothese 2: Locosoft verwendet andere Deduplizierung
- Vielleicht werden Stempelungen anders dedupliziert?
- Oder werden Stempelungen berücksichtigt, die wir ausschließen?

### Hypothese 3: Zusätzliche Filter oder Kriterien
- Vielleicht gibt es bei Tobias spezielle Fälle (z.B. interne Aufträge, bestimmte Auftragsarten)?
- Oder werden bestimmte Positionen anders behandelt?

---

## 📝 Nächste Schritte

1. ⚠️ **Prüfe Positionen OHNE AW:**
   - Werden diese in Locosoft mit der gesamten Stempelzeit gezählt?
   - Oder werden sie anders behandelt?

2. 🔍 **Prüfe Deduplizierung:**
   - Verwendet Locosoft eine andere Deduplizierungslogik?
   - Werden Stempelungen berücksichtigt, die wir ausschließen?

3. 📊 **Weitere Tests:**
   - Prüfe andere Mechaniker mit ähnlichen Datenstrukturen
   - Prüfe ob es spezielle Fälle bei Tobias gibt

---

**Status:** ⚠️ **Abweichung bei Tobias noch nicht vollständig erklärt - weitere Analyse nötig**
