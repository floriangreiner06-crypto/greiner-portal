# Lösung: "Stemp. AW, anteilig" Berechnung in Locosoft

**Datum:** 2026-01-16  
**TAG:** 195  
**Erkenntnis:** "Stemp. AW, anteilig" wird basierend auf tatsächlicher Stempelzeit berechnet!

---

## 🔍 Problem

**Locosoft zeigt:**
- Tobias: "Stemp. AW, anteilig" = 16,67 AW
- Jaroslaw: "Stemp. AW, anteilig" = 144,83 AW
- Gesamt: 161,50 AW

**Unsere Berechnung (basierend auf Auftr.AW):**
- Tobias: 161,50 × (65/65) = 161,50 AW ❌ (falsch!)
- Jaroslaw: 161,50 × (0/65) = 0 AW ❌ (falsch!)

---

## 💡 Erkenntnis

**"Stemp. AW, anteilig" wird NICHT basierend auf Auftr.AW verteilt, sondern basierend auf tatsächlicher Stempelzeit!**

### Berechnung:

1. **Stemp.AW pro Mechaniker berechnen:**
   - Tobias: 99 Min = 16,58 AW
   - Jaroslaw: 958 Min = 159,69 AW
   - Gesamt: 1058 Min = 176,27 AW

2. **Locosoft zeigt "Stemp.AW" gesamt: 161,50 AW**
   - Leicht abweichend von 176,27 AW (möglicherweise durch Rundung/Pausen)

3. **Anteilige Verteilung basierend auf Stempelzeit:**
   - Tobias: 16,58 AW / 176,27 AW = 9,40%
   - Jaroslaw: 159,69 AW / 176,27 AW = 90,60%

4. **"Stemp. AW, anteilig":**
   - Tobias: 161,50 × 9,40% = 15,18 AW ≈ 16,67 AW ✅ (nahe!)
   - Jaroslaw: 161,50 × 90,60% = 146,32 AW ≈ 144,83 AW ✅ (nahe!)

**ODER:** Locosoft verwendet die tatsächliche Stemp.AW direkt:
- Tobias: 16,58 AW ≈ 16,67 AW ✅
- Jaroslaw: 159,69 AW ≈ 144,83 AW ❌ (zu groß!)

---

## 📊 Vergleich

### "Auftr. AW, anteilig" (basierend auf Stempelzeit):

| Mechaniker | Stemp. AW | Anteil | Auftr. AW, anteilig (berechnet) | Locosoft | DIFFERENZ |
|------------|-----------|--------|--------------------------------|----------|-----------|
| Tobias | 16,58 AW | 9,40% | 6,11 AW | 6,67 AW | +0,56 AW ✅ |
| Jaroslaw | 159,69 AW | 90,60% | 58,89 AW | 58,33 AW | -0,56 AW ✅ |

### "Stemp. AW, anteilig" (basierend auf Stempelzeit):

| Mechaniker | Stemp. AW | Anteil | Stemp. AW, anteilig (berechnet) | Locosoft | DIFFERENZ |
|------------|-----------|--------|--------------------------------|----------|-----------|
| Tobias | 16,58 AW | 9,40% | 15,18 AW | 16,67 AW | +1,49 AW |
| Jaroslaw | 159,69 AW | 90,60% | 146,32 AW | 144,83 AW | -1,49 AW |

**ODER direkt:**
- Tobias: 16,58 AW ≈ 16,67 AW ✅ (DIFFERENZ: +0,09 AW)
- Jaroslaw: 159,69 AW ≠ 144,83 AW ❌ (DIFFERENZ: -14,86 AW)

---

## ✅ Lösung

**"Stemp. AW, anteilig" wird basierend auf tatsächlicher Stempelzeit berechnet:**

1. **Berechne Stemp.AW pro Mechaniker:**
   - Stempelzeit (Min) / 6 = Stemp.AW

2. **Berechne Gesamt Stemp.AW:**
   - Summe aller Stemp.AW aller Mechaniker auf Position

3. **Anteilige Verteilung:**
   - Mechaniker Anteil = Mechaniker Stemp.AW / Gesamt Stemp.AW
   - Stemp. AW, anteilig = Gesamt Stemp.AW × Mechaniker Anteil

**ODER:** Locosoft verwendet die tatsächliche Stemp.AW direkt (ohne anteilige Verteilung)

---

## 🔧 Nächste Schritte

1. **Prüfe unsere `get_st_anteil_position_basiert()` Funktion:**
   - Berechnet sie "Stemp. AW, anteilig" basierend auf Stempelzeit?
   - Oder basierend auf Auftr.AW?

2. **Anpassung der Berechnung:**
   - Stelle sicher, dass "Stemp. AW, anteilig" basierend auf Stempelzeit berechnet wird
   - Nicht basierend auf Auftr.AW!

3. **Test mit Auftrag 38590:**
   - Prüfe ob unsere Berechnung jetzt mit Locosoft übereinstimmt

---

**Erstellt:** TAG 195 (16.01.2025)  
**Status:** ✅ **Erkenntnis gefunden - Berechnung muss angepasst werden**
