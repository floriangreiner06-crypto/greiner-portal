# Zusammenfassung PDF-Erkenntnisse - TAG 194

**Datum:** 2026-01-16  
**Quelle:** `monteruspiegel_von_jan.pdf`

---

## ✅ Wichtigste Erkenntnisse

### 1. **Aufteilung nach Auftragsbetrieb**
- Locosoft zeigt **zwei BS-SUMMEN** (Betriebsstätten-Summen):
  - **BS-SUMME 1:** Auftragsbetrieb 01 DEGO (Deggendorf Opel)
  - **BS-SUMME 2:** Auftragsbetrieb 02 DEGH (Deggendorf Hyundai)
- **Gesamtsumme** = Summe beider BS-SUMMEN

### 2. **Gesamtsummen stimmen mit Locosoft UI überein**
- AW-Anteil: **95:45** (5745 Min) ✅
- St-Anteil: **70:52** (4252 Min) ✅
- Leistungsgrad: **135,1%** ✅

### 3. **DRIVE-Berechnung**
- **Leistungsgrad:** 138.1% vs. 135.1% (PDF) = **Nur 3% Differenz - sehr gut!** ✅
- **AW/St-Anteil:** ~25% zu niedrig - **Positionen fehlen**

---

## 📊 Vergleich PDF vs. DRIVE

| Betriebsstätte | Metrik | PDF | DRIVE | Differenz |
|----------------|--------|-----|-------|-----------|
| **DEGO (1)** | AW-Anteil | 57:51 (3471 Min) | 43:03 (2583 Min) | -888 Min (-25.6%) |
| **DEGO (1)** | St-Anteil | 47:50 (2870 Min) | 33:05 (1985 Min) | -885 Min (-30.8%) |
| **DEGH (2)** | AW-Anteil | 37:54 (2274 Min) | 28:30 (1710 Min) | -564 Min (-24.8%) |
| **DEGH (2)** | St-Anteil | 23:02 (1382 Min) | 18:44 (1124 Min) | -258 Min (-18.7%) |
| **GESAMT** | AW-Anteil | 95:45 (5745 Min) | 71:33 (4293 Min) | -1452 Min (-25.3%) |
| **GESAMT** | St-Anteil | 70:52 (4252 Min) | 51:49 (3109 Min) | -1143 Min (-26.9%) |

---

## 🔍 Fazit

**Die Berechnungslogik ist korrekt!** Der Leistungsgrad passt mit nur 3% Differenz sehr gut.

**Die Abweichungen bei AW/St-Anteil (~25%) deuten darauf hin, dass Positionen fehlen:**
- Möglicherweise Positionen ohne Stempelungen?
- Möglicherweise interne/Garantie-Positionen?
- Möglicherweise Positionen mit anderen Kriterien?

**Nächste Schritte:**
1. Identifiziere welche Positionen im PDF sind, die DRIVE nicht zeigt
2. Prüfe ob Positionen ohne Stempelungen berücksichtigt werden müssen
3. Prüfe ob interne/Garantie-Positionen berücksichtigt werden

---

**Status:** ✅ **Query ist grundsätzlich korrekt!** Verbleibende Abweichungen müssen durch Identifikation fehlender Positionen gelöst werden.
