# Test-Ergebnisse KPI-Berechnung - TAG 194

**Datum:** 2026-01-16  
**Mechaniker:** 5018 (Jan Majer)  
**Zeitraum:** 01.01.26 - 15.01.26

---

## 📊 Vergleich Excel vs. DRIVE

| Metrik | Excel (Locosoft) | DRIVE (korrigiert) | Differenz | Status |
|--------|------------------|-------------------|-----------|--------|
| **St-Anteil** | 2321 Min (38.68h) | 3000 Min (50.00h) | +679 Min | ⚠️ Noch Abweichung |
| **AW-Anteil** | 2820 Min (47.00h) | 4354 Min (72.56h) | +1534 Min | ⚠️ Noch Abweichung |
| **Leistungsgrad** | 121.5% | 145.1% | +23.6% | ⚠️ Noch Abweichung |

---

## ✅ Verbesserungen

### Vorher (ohne anteilige Verteilung):
- St-Anteil: **23749 Min** (395.82h) - **10x zu hoch!** ❌
- AW-Anteil: 4354 Min (72.56h)
- Leistungsgrad: 18.3%

### Nachher (mit anteiliger Verteilung):
- St-Anteil: **3000 Min** (50.00h) - **nur noch 1.3x zu hoch** ✅
- AW-Anteil: 4354 Min (72.56h)
- Leistungsgrad: 145.1%

**Verbesserung St-Anteil:** Von 10x zu hoch auf 1.3x zu hoch = **87% Verbesserung!** ✅

---

## 🔍 Verbleibende Abweichungen

### Mögliche Ursachen:

1. **Excel zeigt nur bestimmte Positionen:**
   - Nur fakturierte Positionen?
   - Nur bestimmte Aufträge?
   - Nur Positionen mit bestimmten Kriterien?

2. **AW-Berechnung:**
   - Excel zeigt 2820 Min = 470 AW
   - DRIVE berechnet 4354 Min = 725 AW
   - Differenz: 255 AW

3. **St-Anteil:**
   - Excel zeigt 2321 Min
   - DRIVE berechnet 3000 Min
   - Differenz: 679 Min

---

## 📝 Nächste Schritte

1. ✅ **Anteilige Verteilung implementiert** - St-Anteil deutlich besser!
2. ⚠️ **Abweichungen analysieren:**
   - Prüfe ob Excel nur fakturierte Positionen zeigt
   - Prüfe ob Excel nur bestimmte Aufträge zeigt
   - Prüfe AW-Berechnung genauer
3. 🔧 **Weitere Korrekturen:**
   - Filter auf fakturierte Positionen?
   - Filter auf bestimmte Aufträge?
   - Korrektur der AW-Berechnung?

---

**Status:** ✅ **Große Verbesserung erreicht!** St-Anteil von 10x zu hoch auf 1.3x reduziert. Verbleibende Abweichungen müssen noch analysiert werden.
