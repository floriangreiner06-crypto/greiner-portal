# BWA API Response Analyse - TAG 196

**Datum:** 2026-01-16  
**Status:** 🔍 Analyse der aktuellen API-Response

---

## 📊 API RESPONSE WERTE (Dezember 2025)

### Monat Dezember 2025

| Position | DRIVE (API) | GlobalCube (Screenshot) | Differenz | Status |
|----------|-------------|------------------------|-----------|--------|
| Umsatz | 2.190.718,01 € | 2.190.718,00 € | +0,01 € | ✅ Perfekt |
| Einsatz | 1.862.687,56 € | 1.862.668,00 € | +19,56 € | ✅ Sehr gut |
| DB1 | 328.030,45 € | 328.050,00 € | -19,55 € | ✅ Sehr gut |
| Variable Kosten | 69.270,36 € | 69.374,00 € | -103,64 € | ✅ Sehr gut |
| DB2 | 258.760,09 € | 258.876,00 € | -115,91 € | ✅ Sehr gut |
| Direkte Kosten | 189.849,47 € | 189.866,00 € | -16,53 € | ✅ Sehr gut |
| DB3 | 68.910,62 € | 68.810,00 € | +100,62 € | ✅ Sehr gut |
| Indirekte Kosten | 185.057,99 € | 185.058,00 € | -0,01 € | ✅ Perfekt |
| **Betriebsergebnis** | **-116.147,37 €** | **-116.248,00 €** | **+100,63 €** | ✅ **Sehr gut (0,09%)** |
| Neutrales Ergebnis | 32.628,68 € | 32.629,00 € | -0,32 € | ✅ Sehr gut |
| Unternehmensergebnis | -83.518,69 € | -83.619,00 € | +100,31 € | ✅ Sehr gut |

**Fazit Monat:** ✅ **Sehr gute Übereinstimmung!** Alle Werte sind nahezu identisch.

---

### YTD bis Dezember 2025 (Sep 2025 - Dez 2025)

| Position | DRIVE (API) | GlobalCube (Screenshot) | Differenz | Status |
|----------|-------------|------------------------|-----------|--------|
| Umsatz YTD | 10.618.393,36 € | 10.618.400,00 € | -6,64 € | ✅ Perfekt |
| Einsatz YTD | 9.223.769,97 € | 9.191.864,00 € | +31.905,97 € | ⚠️ |
| DB1 YTD | 1.394.623,39 € | 1.426.536,00 € | -31.912,61 € | ⚠️ |
| Variable Kosten YTD | 304.164,35 € | 304.268,00 € | -103,65 € | ✅ Sehr gut |
| DB2 YTD | 1.090.459,04 € | 1.122.268,00 € | -31.808,96 € | ⚠️ |
| Direkte Kosten YTD | 659.134,64 € | 659.229,00 € | -94,36 € | ✅ Sehr gut |
| DB3 YTD | 431.324,40 € | 463.039,00 € | -31.714,60 € | ⚠️ |
| Indirekte Kosten YTD | 838.937,55 € | 838.944,00 € | -6,45 € | ✅ **Perfekt!** |
| **Betriebsergebnis YTD** | **-407.613,15 €** | **-375.905,00 €** | **-31.708,15 €** | ⚠️ **Problem!** |
| Neutrales Ergebnis YTD | 130.171,89 € | 130.172,00 € | -0,11 € | ✅ Perfekt |
| Unternehmensergebnis YTD | -277.441,26 € | -245.733,00 € | -31.708,26 € | ⚠️ |

---

## 🔍 PROBLEM IDENTIFIZIERT

### Betriebsergebnis YTD-Differenz: -31.708,15 €

**Aktuelle Werte:**
- DRIVE BE YTD: -407.613,15 €
- GlobalCube BE YTD: -375.905,00 €
- **Differenz: -31.708,15 €** (DRIVE zu negativ)

**Analyse:**
- Indirekte Kosten YTD: -6,45 € Differenz ✅ (fast perfekt!)
- Direkte Kosten YTD: -94,36 € Differenz ✅ (sehr gut!)
- **DB3 YTD: -31.714,60 € Differenz** ⚠️ (Hauptproblem!)
- **Einsatz YTD: +31.905,97 € Differenz** ⚠️ (Hauptproblem!)

**Erkenntnis:**
- Das Problem liegt **NICHT** in den indirekten Kosten (die sind fast perfekt!)
- Das Problem liegt in **DB3** und **Einsatz** YTD!
- Die Differenz von -31.708,15 € im Betriebsergebnis kommt hauptsächlich von:
  - Einsatz YTD: +31.905,97 € (DRIVE zu hoch)
  - DB3 YTD: -31.714,60 € (DRIVE zu niedrig)

---

## ✅ ERKENNTNISSE

### 1. 498001 ist korrekt ausgeschlossen ✅

**Beweis:**
- Indirekte Kosten YTD: 838.937,55 € (DRIVE) vs. 838.944,00 € (GlobalCube)
- Differenz: Nur -6,45 € (0,00%) ✅
- Wenn 498001 nicht ausgeschlossen wäre: Differenz wäre ~-200.000 €

**Fazit:** 498001 wird korrekt ausgeschlossen!

### 2. Hauptproblem: Einsatz YTD

**Problem:**
- Einsatz YTD: 9.223.769,97 € (DRIVE) vs. 9.191.864,00 € (GlobalCube)
- Differenz: +31.905,97 € (DRIVE zu hoch)

**Auswirkung:**
- DB1 YTD: -31.912,61 € (weil Einsatz zu hoch)
- DB3 YTD: -31.714,60 € (weil DB1 zu niedrig)
- Betriebsergebnis YTD: -31.708,15 € (weil DB3 zu niedrig)

**Ursache:**
- Möglicherweise werden bestimmte Einsatz-Konten doppelt gezählt
- Oder: GlobalCube schließt bestimmte Konten aus, die DRIVE einschließt
- Oder: Filter-Unterschiede zwischen DRIVE und GlobalCube

---

## 📋 NÄCHSTE SCHRITTE

### Priorität HOCH:
1. **Einsatz YTD analysieren:**
   - Warum +31.905,97 € Differenz?
   - Welche Konten werden doppelt gezählt?
   - Welche Filter-Unterschiede gibt es?

2. **DB3 YTD analysieren:**
   - Warum -31.714,60 € Differenz?
   - Kommt das nur vom Einsatz, oder gibt es weitere Probleme?

### Priorität MITTEL:
3. **Monat Dezember ist perfekt:**
   - Alle Werte stimmen überein ✅
   - Keine Korrekturen nötig für Monat

---

*Erstellt: TAG 196 | Autor: Claude AI*
