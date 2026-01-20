# Dezember 2025 - Vergleich DRIVE vs. Locosoft

**Datum:** 2026-01-17  
**Zeitraum:** 01.12.2025 - 31.12.2025

---

## 📊 TOBIAS REITMEIER (5007)

### Gesamter Dezember (01.12 - 31.12)
| Metrik | DRIVE | Locosoft | Differenz |
|--------|-------|----------|-----------|
| Stmp.Anteil | 8463 Min (141.05 h) | - | - |
| AW-Anteil | 1023.5 AW (6141 Min) | - | - |
| Leistungsgrad | **72.6%** | - | - |
| Aufträge | 104 | - | - |
| Tage | 15 | - | - |

### Kurzzeitraum (01.12 - 08.12) - Vergleich mit Locosoft Screenshot
| Metrik | DRIVE | Locosoft | Differenz |
|--------|-------|----------|-----------|
| Stmp.Anteil | **3355 Min** (55.92 h) | **8543 Min** (142:23) | **-5188 Min** (-60.7%) ⚠️ |
| AW-Anteil | **2847 Min** (474.5 AW) | **5106 Min** (85:06) | **-2259 Min** (-44.2%) ⚠️ |
| Leistungsgrad | **84.9%** | **59.8%** | **+25.1%** ⚠️ |
| Aufträge | 43 | - | - |
| Tage | 6 | - | - |

**⚠️ KRITISCHE ABWEICHUNG:**
- Stmp.Anteil ist **60.7% zu niedrig** in DRIVE
- AW-Anteil ist **44.2% zu niedrig** in DRIVE
- Leistungsgrad ist **25.1% zu hoch** in DRIVE (weil Stmp.Anteil zu niedrig ist)

---

## 📊 CHRISTIAN RAITH (5002)

### Gesamter Dezember (01.12 - 31.12)
| Metrik | DRIVE | Locosoft | Differenz |
|--------|-------|----------|-----------|
| Stmp.Anteil | 3609 Min (60.15 h) | - | - |
| AW-Anteil | 675.5 AW (4053 Min) | - | - |
| Leistungsgrad | **112.3%** | - | - |
| Aufträge | 42 | - | - |
| Tage | 9 | - | - |

### Kurzzeitraum (01.12 - 08.12) - Vergleich mit Locosoft Screenshot
| Metrik | DRIVE | Locosoft | Differenz |
|--------|-------|----------|-----------|
| Stmp.Anteil | **2085 Min** (34.75 h) | **3676 Min** (61:16) | **-1591 Min** (-43.3%) ⚠️ |
| AW-Anteil | **2352 Min** (392 AW) | **3966 Min** (66:06) | **-1614 Min** (-40.7%) ⚠️ |
| Leistungsgrad | **112.8%** | **107.9%** | **+4.9%** ✓ |
| Aufträge | 25 | - | - |
| Tage | 5 | - | - |

**⚠️ ABWEICHUNG:**
- Stmp.Anteil ist **43.3% zu niedrig** in DRIVE
- AW-Anteil ist **40.7% zu niedrig** in DRIVE
- Leistungsgrad ist **4.9% zu hoch** (noch akzeptabel)

---

## 🔍 ANALYSE

### Problem: Stmp.Anteil ist deutlich zu niedrig

**Mögliche Ursachen:**

1. **Filter-Problem:**
   - Vielleicht werden Positionen ohne AW nicht korrekt berücksichtigt?
   - Oder es gibt einen Filter, der zu viele Daten ausschließt?

2. **Zeitraum-Problem:**
   - Locosoft zeigt 01.12-08.12, aber vielleicht werden in DRIVE andere Tage gezählt?
   - Oder es gibt ein Problem mit der Datumslogik?

3. **Garantie-Logik:**
   - Tobias macht viele Garantie-Aufträge
   - Vielleicht wird die Garantie-Logik nicht korrekt angewendet?

4. **Deduplizierung:**
   - Vielleicht werden Stempelungen zu stark dedupliziert?
   - Oder es gibt ein Problem mit der Gruppierung?

### Vergleich mit Januar (Tobias):
- **Januar (01.01-15.01):** DRIVE 4686 Min vs. Locosoft 4971 Min = **-5.7%** ✓ (gut!)
- **Dezember (01.12-08.12):** DRIVE 3355 Min vs. Locosoft 8543 Min = **-60.7%** ❌ (sehr schlecht!)

**Fazit:** Die Implementierung funktioniert für Januar gut, aber für Dezember gibt es massive Abweichungen!

---

## 🎯 NÄCHSTE SCHRITTE

1. **Prüfe Filter:** Gibt es Filter, die im Dezember anders wirken?
2. **Prüfe Garantie-Logik:** Wird sie korrekt angewendet?
3. **Prüfe Datumslogik:** Werden die richtigen Tage gezählt?
4. **Prüfe Deduplizierung:** Wird zu stark dedupliziert?

---

**Erstellt:** 2026-01-17  
**Quelle:** Test-Script `test_leistungsgrad_fix.py` + Locosoft Screenshots
