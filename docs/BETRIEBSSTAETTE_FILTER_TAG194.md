# Betriebsstätten-Filter Analyse - TAG 194

**Datum:** 2026-01-16  
**Frage:** Werden die Zeiten von Betrieb DEGH (Deggendorf) berücksichtigt?

---

## ✅ Ergebnis

**Jan Majer (5018) hat:**
- Betriebsstätte: 1 (DEG = Deggendorf)
- Alle Stempelungen sind von Betriebsstätte 1

**Alle Aufträge mit Stempelungen:**
- Alle Aufträge haben `subsidiary = 1` (Deggendorf)
- Keine Aufträge von subsidiary 2 (HYU) oder 3 (LAN)

---

## 📊 Aktuelle DRIVE-Berechnung

**Ohne Betriebsstätten-Filter:**
- AW-Anteil: 4293 Min (71:33)
- St-Anteil: 3110 Min (51:50)
- Leistungsgrad: 138.1%

**Locosoft UI:**
- AW-Anteil: 5745 Min (95:45)
- St-Anteil: 4252 Min (70:52)
- Leistungsgrad: 135.1%

---

## 🔍 Fazit

**Die Abweichung liegt NICHT an einem Betriebsstätten-Filter!**

- ✅ Alle Stempelungen sind von Betriebsstätte 1 (DEG)
- ✅ Alle Aufträge sind von subsidiary 1 (DEG)
- ✅ Es gibt keine Aufträge von anderen Betriebsstätten

**Die Abweichung (~25% bei AW/St-Anteil) muss andere Ursachen haben:**
1. Fehlende Positionen (möglicherweise Positionen ohne Stempelungen?)
2. Andere Filterkriterien
3. Unterschiedliche Berechnungslogik

---

**Status:** ✅ Betriebsstätten-Filter ist nicht die Ursache der Abweichung
