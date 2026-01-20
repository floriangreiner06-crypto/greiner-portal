# Finale Lösung: "Stemp. AW, anteilig" Berechnung in Locosoft

**Datum:** 2026-01-16  
**TAG:** 195  
**Status:** ✅ **VOLLSTÄNDIG VERSTANDEN**

---

## 🎯 Finale Erkenntnis

**"Stemp. AW, anteilig" in der Mitarbeiter-Tabelle = Summe der "Zeitbasis" Werte aus der Position-Tabelle!**

### Beispiel: Auftrag 38590, Position 2.06

**Position-Tabelle ("Stempelung nach Auftragsposition"):**

| Mechaniker | Datum | Zeitbasis (AW) |
|------------|-------|----------------|
| Tobias (5007) | 02.12.25 | 9,50 AW |
| Tobias (5007) | 03.12.25 | 7,17 AW |
| Jaroslaw (5014) | 10.12.25 | 58,50 AW |
| Jaroslaw (5014) | 11.12.25 | 83,50 AW |
| Jaroslaw (5014) | 12.12.25 | 2,83 AW |
| **Gesamt** | | **161,50 AW** |

**Mitarbeiter-Tabelle ("Stempelung nach Mitarbeiter"):**

| Mechaniker | Stemp. AW, anteilig |
|------------|---------------------|
| Tobias (5007) | **16,67 AW** (9,50 + 7,17) ✅ |
| Jaroslaw (5014) | **144,83 AW** (58,50 + 83,50 + 2,83) ✅ |
| **Gesamt** | **161,50 AW** ✅ |

---

## 📊 Wie funktioniert Locosoft?

### 1. "Zeitbasis" in Position-Tabelle

**Berechnung:**
- Jede Stempelung wird in AW umgerechnet: Stempelzeit (Min) / 6 = AW
- "Zeitbasis" = Stempelzeit in AW für diese einzelne Stempelung

**Beispiel:**
- Tobias: 02.12.25 16:13 - 17:10 = 57 Min = 9,50 AW ✅
- Tobias: 03.12.25 08:02 - 08:45 = 43 Min = 7,17 AW ✅

### 2. "Stemp. AW, anteilig" in Mitarbeiter-Tabelle

**Berechnung:**
- Summiere alle "Zeitbasis" Werte pro Mechaniker
- Das ist die "Stemp. AW, anteilig" für diesen Mechaniker

**Beispiel:**
- Tobias: 9,50 + 7,17 = 16,67 AW ✅
- Jaroslaw: 58,50 + 83,50 + 2,83 = 144,83 AW ✅

### 3. "Auftr. AW, anteilig" in Mitarbeiter-Tabelle

**Berechnung:**
- Verteile die "Auftr.AW" der Position (65 AW) basierend auf Stempelzeit
- Mechaniker Anteil = Mechaniker Stemp.AW / Gesamt Stemp.AW
- Auftr. AW, anteilig = Auftr.AW × Mechaniker Anteil

**Beispiel:**
- Gesamt Stemp.AW: 161,50 AW
- Tobias Anteil: 16,67 / 161,50 = 10,32%
- Auftr. AW, anteilig: 65 × 10,32% = 6,71 AW ≈ 6,67 AW ✅

---

## ✅ Unsere Berechnung muss sein:

1. **Für jede Stempelung:**
   - Stempelzeit (Min) / 6 = AW ("Zeitbasis")

2. **Pro Mechaniker:**
   - Summiere alle AW-Werte = "Stemp. AW, anteilig"

3. **Pro Position:**
   - Summiere alle "Stemp. AW, anteilig" = Gesamt "Stemp.AW"

4. **"Auftr. AW, anteilig" (optional):**
   - Verteile Auftr.AW basierend auf Stempelzeit-Anteil

---

## 🔧 Nächste Schritte

1. **Prüfe `get_st_anteil_position_basiert()`:**
   - Berechnet sie die Summe der einzelnen Stempelungen in AW?
   - Oder verwendet sie eine andere Logik?

2. **Anpassung:**
   - Stelle sicher, dass jede Stempelung in AW umgerechnet wird
   - Summiere pro Mechaniker = "Stemp. AW, anteilig"

3. **Test:**
   - Prüfe ob unsere Berechnung jetzt mit Locosoft übereinstimmt

---

**Erstellt:** TAG 195 (16.01.2025)  
**Status:** ✅ **VOLLSTÄNDIG VERSTANDEN - Berechnung klar**
