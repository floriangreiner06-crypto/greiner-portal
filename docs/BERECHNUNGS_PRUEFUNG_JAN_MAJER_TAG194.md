# Berechnungs-Prüfung: Jan Majer (5018) TAG 194

**Datum:** 2026-01-16  
**Zeitraum:** 01.01.26 - 15.01.26  
**Vergleich:** DRIVE (Refactored) vs. Locosoft UI

---

## 📊 Vergleichsergebnisse

### ✅ Leistungsgrad
- **DRIVE:** 134.3%
- **Locosoft:** 133.3%
- **Diff:** +1.0%
- **Status:** ✅ **Sehr nah!**

**Berechnung korrigiert:**
- Formel: `(AW * 60) / Stempelzeit_Leistungsgrad * 100`
- AW: 90.40h = 904 AW = 5424 Min
- Stempelzeit (Leistungsgrad): 4038 Min
- Leistungsgrad = 5424 / 4038 * 100 = 134.3% ✅

### ✅ AW-Anteil
- **DRIVE:** 90.40h = 904.0 AW
- **Locosoft:** 91:33 = 91.55h = 915.5 AW
- **Diff:** -1.15h (-1.3%)
- **Status:** ✅ **Sehr nah!**

### ⚠️ Stmp.Anteil
- **DRIVE:** 3643 Min (60.72h) - Basis (Zeit-Spanne)
- **Locosoft:** 4121 Min (68.68h)
- **Diff:** -478 Min (-11.6%)
- **Status:** ⚠️ **Näher als vorher, aber noch Abweichung**

**Entscheidung:**
- Hybrid-Ansatz (Basis + 10.6%): 4951 Min (+20.1% Diff) ❌
- Basis (Zeit-Spanne): 3643 Min (-11.6% Diff) ✅
- **→ Basis (Zeit-Spanne) ist näher an Locosoft!**

### ⚠️ Anwesenheit
- **DRIVE:** 4662 Min (77.70h)
- **Locosoft:** 4227 Min (70.45h)
- **Diff:** +435 Min (+10.3%)
- **Status:** ⚠️ **Abweichung**

**Mögliche Ursachen:**
- Zeitraum-Definition (inkl. vs. exkl. Enddatum)
- Filter (z.B. nur Werktage)
- Abwesenheit (0.5 Tage) wird unterschiedlich behandelt

### ⚠️ Produktivität
- **DRIVE:** 78.1%
- **Locosoft:** 88.0% (P-Grad)
- **Diff:** -9.9%
- **Status:** ⚠️ **Abweichung**

**Hinweis:** Produktivität hängt von Stmp.Anteil und Anwesenheit ab.

---

## 🔧 Durchgeführte Korrekturen

### 1. Leistungsgrad-Berechnung korrigiert
**Problem:** Falsche Umrechnung von AW (Stunden) zu AW (Einheiten)
- **Vorher:** `vorgabe_aw = aw_zu_stunden(aw_stunden) * 10` ❌
- **Nachher:** Direkte Berechnung `(AW * 60) / Stempelzeit_Leistungsgrad * 100` ✅

### 2. Stmp.Anteil: Basis statt Hybrid
**Problem:** Hybrid-Ansatz war zu hoch (+20.1%)
- **Vorher:** Hybrid (Basis + 10.6%): 4951 Min ❌
- **Nachher:** Basis (Zeit-Spanne): 3643 Min ✅
- **Ergebnis:** Näher an Locosoft (-11.6% statt +20.1%)

---

## 📝 Verbleibende Abweichungen

### Stmp.Anteil (-11.6%)
**Mögliche Ursachen:**
1. **Zeitraum-Definition:** Locosoft könnte andere Zeitraum-Logik verwenden
2. **Filter:** Locosoft könnte zusätzliche Filter anwenden
3. **Berechnungslogik:** Unterschiede in der Zeit-Spanne-Berechnung

### Anwesenheit (+10.3%)
**Mögliche Ursachen:**
1. **Zeitraum-Definition:** Inkl. vs. Exkl. Enddatum
2. **Filter:** Nur Werktage, Abwesenheit (0.5 Tage)
3. **Type=1 Stempelungen:** Möglicherweise andere Filter

---

## ✅ Erfolge

1. **Leistungsgrad:** ✅ Korrekt berechnet (134.3% vs. 133.3%)
2. **AW-Anteil:** ✅ Sehr nah (90.40h vs. 91.55h, -1.3%)
3. **Stmp.Anteil:** ✅ Näher mit Basis (von +20.1% auf -11.6%)
4. **Refactoring:** ✅ Keine Parameter-Probleme mehr
5. **Code-Qualität:** ✅ Bessere Wartbarkeit

---

## 🔍 Nächste Schritte

1. ⏳ Prüfe Zeitraum-Definition für Stmp.Anteil
2. ⏳ Prüfe Filter für Anwesenheit
3. ⏳ Vergleich mit anderen Mechanikern
4. ⏳ Vollständiger Vergleich aller KPIs

---

**Status:** ✅ **LEISTUNGSGRAD KORREKT, AW-ANTEIL SEHR NAH, STMP.ANTEIL VERBESSERT**
