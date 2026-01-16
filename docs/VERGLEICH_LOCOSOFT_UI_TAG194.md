# Vergleich Locosoft UI vs. DRIVE - TAG 194

**Datum:** 2026-01-16  
**Mechaniker:** 5018 (Jan Majer)  
**Zeitraum:** 01.01.26 - 16.01.26

---

## 📊 Locosoft UI Einstellungen

**Wichtig aus UI:**
- ✅ **"Alle Auftragspositionen"** - NICHT nur fakturierte!
- ✅ Filter: Nur externe Aufträge (labour_type != 'I')
- ✅ Anteilige Verteilung bei mehreren Positionen/Mechanikern

---

## 📊 Locosoft UI Werte

| Metrik | Wert |
|--------|------|
| **AW-Anteil** | 95:45 (5745 Min = 95.75 Stunden) |
| **St-Anteil** | 70:52 (4252 Min = 70.87 Stunden) |
| **Leistungsgrad** | 135.1% |
| **Abwesenheit** | 0.5 Tage |
| **Sollzeit** | 76:00 (4560 Min) |
| **Anwesend** | 72:22 (4342 Min) |
| **Produktiv** | 63:55 (3835 Min) |
| **A-Grad** | 95% |
| **P-Grad** | 88% |

---

## 📊 DRIVE-Berechnung (aktuell)

| Metrik | DRIVE | Locosoft UI | Differenz | Status |
|--------|-------|-------------|-----------|--------|
| **AW-Anteil** | 4293 Min (71:33) | 5745 Min (95:45) | -1452 Min (-25.3%) | ⚠️ Zu niedrig |
| **St-Anteil** | 3110 Min (51:50) | 4252 Min (70:52) | -1142 Min (-26.9%) | ⚠️ Zu niedrig |
| **Leistungsgrad** | 138.1% | 135.1% | +3.0% | ✅ Sehr gut! |

---

## 🔍 Analyse

### ✅ Was funktioniert:
1. **Leistungsgrad-Berechnung:** Nur 3.0% Differenz - **sehr gut!**
2. **Anteilige Verteilung:** Implementiert und funktioniert
3. **Filter:** Nur externe Aufträge (labour_type != 'I')

### ⚠️ Was noch nicht passt:
1. **AW-Anteil:** DRIVE zeigt 25.3% weniger als Locosoft UI
2. **St-Anteil:** DRIVE zeigt 26.9% weniger als Locosoft UI

### Mögliche Ursachen:

1. **Fehlende Positionen:**
   - DRIVE berücksichtigt möglicherweise nicht alle Positionen
   - Vielleicht fehlen Positionen ohne Stempelungen?

2. **Zeitraum:**
   - Prüfe ob Zeitraum korrekt ist (01.01-16.01 inklusive)

3. **Filter:**
   - Prüfe ob alle Filter korrekt sind
   - Vielleicht fehlen bestimmte Positionen?

---

## 📝 Nächste Schritte

1. ✅ **Filter korrigiert:** Kein Filter auf `is_invoiced` (Locosoft zeigt "Alle Auftragspositionen")
2. ⚠️ **Abweichungen analysieren:**
   - Warum zeigt DRIVE weniger AW-Anteil?
   - Warum zeigt DRIVE weniger St-Anteil?
3. 🔧 **Weitere Korrekturen:**
   - Prüfe ob alle Positionen berücksichtigt werden
   - Prüfe Zeitraum-Filter

---

**Status:** ⚠️ **Leistungsgrad passt sehr gut (3% Diff), aber AW/St-Anteil zeigen noch Abweichungen (~25%)**
