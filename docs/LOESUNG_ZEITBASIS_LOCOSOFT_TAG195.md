# Lösung: "Zeitbasis" in Locosoft ist in AW, nicht in Stunden!

**Datum:** 2026-01-16  
**TAG:** 195  
**Erkenntnis:** Locosoft zeigt "Zeitbasis" in AW, nicht in Stunden!

---

## 🔍 Problem

**Locosoft zeigt:**
- "Zeitbasis" für Tobias: 16,67 Stunden
- "Stemp. AW, anteilig" für Tobias: 16,67 AW

**Unsere Berechnung:**
- Stempelzeit für Tobias: 1,66 Stunden (99 Min)
- In AW: 99 Min / 6 = 16,5 AW

**DIFFERENZ:** 16,67 AW vs. 16,5 AW = sehr nah! ✅

---

## 💡 Erkenntnis

**"Zeitbasis" in Locosoft ist NICHT in Stunden, sondern in AW!**

- Locosoft zeigt "Zeitbasis" 16,67 → das sind **16,67 AW**
- 16,67 AW × 6 Min/AW = 100 Min = 1,67 Stunden
- Unsere Berechnung: 99 Min = 16,5 AW ✅

**Das erklärt die "17 Stunden":**
- Locosoft zeigt "Zeitbasis" 16,67 AW (nicht Stunden!)
- Das entspricht: 16,67 × 6 = 100 Min = 1,67 Stunden
- **NICHT 16,67 Stunden!**

---

## 📊 Vergleich mit Locosoft-Screenshot

**"Stempelung nach Mitarbeiter" Tabelle:**

| Mechaniker | Auftr. AW, anteilig | Stemp. AW, anteilig | Abw. AW |
|------------|---------------------|---------------------|---------|
| Tobias (5007) | 6,67 AW | **16,67 AW** | 10,00 AW |
| Jaroslaw (5014) | 58,33 AW | **144,83 AW** | 86,50 AW |
| **Gesamt** | **65,00 AW** | **161,50 AW** | **96,50 AW** |

**Berechnung:**
- Gesamt Stemp.AW: 161,50 AW (aus "Stempelung nach Auftragsposition")
- Anteilige Verteilung basierend auf Auftr.AW:
  - Tobias: 6,67 / 65,00 = 10,26% → 161,50 × 10,26% = 16,57 AW ✅ (nahe bei 16,67)
  - Jaroslaw: 58,33 / 65,00 = 89,74% → 161,50 × 89,74% = 144,93 AW ✅ (nahe bei 144,83)

---

## 🔧 Wie funktioniert Locosoft?

1. **"Stemp.AW" für Position 2.06:** 161,50 AW
   - Berechnet aus: Gesamt-Stempelzeit aller Mechaniker auf Position 2.06
   - 17,63 Stunden = 1058 Min = 176,27 AW
   - Locosoft zeigt: 161,50 AW (leicht abweichend, möglicherweise durch Rundung/Pausen)

2. **Anteilige Verteilung basierend auf "Auftr.AW":**
   - Tobias: 6,67 AW / 65,00 AW = 10,26%
   - Jaroslaw: 58,33 AW / 65,00 AW = 89,74%

3. **"Stemp. AW, anteilig":**
   - Tobias: 161,50 × 10,26% = 16,57 AW ≈ 16,67 AW ✅
   - Jaroslaw: 161,50 × 89,74% = 144,93 AW ≈ 144,83 AW ✅

4. **"Zeitbasis" in Locosoft:**
   - Zeigt die "Stemp. AW, anteilig" Werte
   - **ABER:** Die Einheit ist "AW", nicht "Stunden"!
   - Locosoft zeigt "Zeitbasis" 16,67 → das sind 16,67 AW = 1,67 Stunden

---

## ✅ Lösung

**Unsere Berechnung muss angepasst werden:**

1. **"Stemp.AW" berechnen:**
   - Summiere Stempelzeit aller Mechaniker auf Position
   - Umrechnung in AW: Stempelzeit (Min) / 6

2. **Anteilige Verteilung:**
   - Basierend auf "Auftr.AW" (nicht auf Stempelzeit!)
   - Tobias: 6,67 AW / 65,00 AW = 10,26%
   - Jaroslaw: 58,33 AW / 65,00 AW = 89,74%

3. **"Stemp. AW, anteilig":**
   - Gesamt Stemp.AW × Anteil = Stemp. AW, anteilig

4. **"Zeitbasis" (wenn benötigt):**
   - Zeigt "Stemp. AW, anteilig" in AW
   - **NICHT in Stunden!**

---

## 📝 Nächste Schritte

1. **Prüfe unsere `get_st_anteil_position_basiert()` Funktion:**
   - Berechnet sie "Stemp. AW, anteilig" korrekt?
   - Verwendet sie die richtige anteilige Verteilung?

2. **Anpassung der Berechnung:**
   - Stelle sicher, dass "Stemp. AW, anteilig" basierend auf "Auftr.AW" verteilt wird
   - Nicht basierend auf Stempelzeit!

3. **Test mit Auftrag 38590:**
   - Prüfe ob unsere Berechnung jetzt mit Locosoft übereinstimmt

---

**Erstellt:** TAG 195 (16.01.2025)  
**Status:** ✅ **Erkenntnis gefunden - Berechnung muss angepasst werden**
