# Übererfassung Analyse - Einsatzwerte TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ✅ **ANALYSE ABGESCHLOSSEN**

---

## 🎯 PROBLEM

**DRIVE zeigt 26.0 Mio. €, GlobalCube zeigt 9.2 Mio. €**
- **Differenz: +16.8 Mio. € (+183%)**
- **Massive Übererfassung in DRIVE!**

---

## 📊 ERKENNTNISSE

### 1. Top 50 Konten

| Rang | Konto | Wert | subsidiary | branch | 6.Ziffer | Bereich |
|------|-------|------|------------|--------|----------|---------|
| 1 | 718001 | 2,608,047.06 € | 2 | 2 | 1 | 71xxxx (NW) |
| 2 | 723101 | 2,255,386.31 € | 2 | 2 | 1 | 72xxxx (GW) |
| 3 | 724201 | 1,965,810.60 € | 2 | 2 | 1 | 72xxxx (GW) |
| 4 | 721201 | 1,740,305.82 € | 2 | 3 | 1 | 72xxxx (GW) |
| 5 | 721202 | 1,623,579.32 € | 1 | 3 | 2 | 72xxxx (GW) |
| ... | ... | ... | ... | ... | ... | ... |

**Summe Top 50:** 23,013,604.49 €  
**Gesamtsumme:** 26,023,519.41 €

---

### 2. Konten-Bereiche

| Bereich | Wert | Konten | Buchungen |
|---------|------|--------|-----------|
| **71xxxx (NW Einsatz)** | **10,834,760.81 €** | 92 | 2,925 |
| **72xxxx (GW Einsatz)** | **10,674,255.21 €** | 19 | 3,141 |
| **73xxxx (Teile Einsatz)** | **3,136,156.36 €** | 48 | 27,506 |
| **74xxxx (Lohn Einsatz)** | **1,279,700.98 €** | 10 | 1,841 |
| 76xxxx | 58,885.47 € | 2 | 52 |
| 79xxxx | 39,760.58 € | 3 | 5 |
| **GESAMT** | **26,023,519.41 €** | | |

**Erkenntnis:** 71xxxx und 72xxxx machen zusammen 21.5 Mio. € aus (83% der Gesamtsumme)!

---

### 3. Hyundai vs. Stellantis

| Standort | Wert | Anteil | Buchungen |
|----------|------|--------|-----------|
| **Hyundai (Deggendorf)** | **8,958,535.51 €** | **34.4%** | 10,033 |
| **Stellantis Deggendorf** | **13,409,446.48 €** | **51.5%** | 18,791 |
| **Stellantis Landau** | **3,655,537.42 €** | **14.0%** | 6,646 |
| **GESAMT** | **26,023,519.41 €** | **100%** | 35,470 |

**KRITISCHE ERKENNTNIS:**
- **Hyundai (8.96 Mio. €) ist sehr nah an GlobalCube (9.19 Mio. €)!**
- **Differenz: -233,328.49 € (nur -2.6%)**
- **Vermutung: GlobalCube erfasst möglicherweise NUR Hyundai?**

---

### 4. SOLL vs. HABEN Buchungen

| Typ | Wert | Buchungen |
|-----|------|-----------|
| **SOLL** | **31,067,430.26 €** | 33,315 |
| **HABEN** | **-5,043,910.85 €** | 2,155 |
| **Gesamt (SOLL - HABEN)** | **36,111,341.11 €** | 35,470 |

**Aktuelle Logik:**
```sql
CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
```

**Ergebnis:** 26,023,519.41 € (korrekt: SOLL - HABEN)

**Vergleich:**
- Wenn GlobalCube NUR SOLL erfasst: 31.07 Mio. € (Differenz: +21.9 Mio. €)
- Wenn GlobalCube NUR HABEN erfasst: -5.04 Mio. € (Differenz: -14.2 Mio. €)

**Erkenntnis:** GlobalCube erfasst definitiv SOLL - HABEN (wie DRIVE), aber möglicherweise mit anderen Filtern!

---

## 🔍 HYPOTHESEN

### Hypothese 1: GlobalCube erfasst NUR Hyundai ⭐⭐⭐

**Begründung:**
- Hyundai (DRIVE): 8,958,535.51 €
- GlobalCube: 9,191,864.00 €
- **Differenz: -233,328.49 € (nur -2.6%!)**

**Test:**
- Prüfe, ob GlobalCube-BWA für "Gesamtbetrieb" tatsächlich alle Standorte enthält
- Oder ob es nur Hyundai ist?

### Hypothese 2: GlobalCube verwendet andere Filter

**Mögliche Unterschiede:**
1. **Standort-Filter:**
   - DRIVE: `6. Ziffer='1'` für Deggendorf, `branch=3` für Landau
   - GlobalCube: Möglicherweise andere Logik?

2. **Konten-Bereiche:**
   - DRIVE: Alle 7xxxxx Konten
   - GlobalCube: Möglicherweise nur bestimmte Bereiche (z.B. nur 71xxxx, 72xxxx)?

3. **Firma-Filter:**
   - DRIVE: Alle Firmen (Stellantis + Hyundai)
   - GlobalCube: Möglicherweise nur eine Firma?

### Hypothese 3: GlobalCube verwendet andere Zeiträume

**Möglichkeit:**
- DRIVE: Jan-Dez 2025 (Kalenderjahr)
- GlobalCube: Möglicherweise Wirtschaftsjahr (Sep 2024 - Aug 2025)?

---

## 📋 NÄCHSTE SCHRITTE

1. **Prüfe GlobalCube-BWA für einzelne Standorte:**
   - Ist "Gesamtbetrieb" wirklich alle Standorte?
   - Oder nur Hyundai?

2. **Vergleiche Standort-für-Standort:**
   - Deggendorf Opel (DRIVE) vs. GlobalCube
   - Deggendorf Hyundai (DRIVE) vs. GlobalCube
   - Landau (DRIVE) vs. GlobalCube

3. **Prüfe Konten-Bereiche:**
   - Welche Bereiche erfasst GlobalCube?
   - Nur 71xxxx, 72xxxx? Oder auch 73xxxx, 74xxxx?

4. **Prüfe Zeitraum:**
   - Welcher Zeitraum wird in GlobalCube verwendet?
   - Kalenderjahr oder Wirtschaftsjahr?

---

**KRITISCHE ERKENNTNIS:** Hyundai (8.96 Mio. €) ist sehr nah an GlobalCube (9.19 Mio. €)! Das deutet darauf hin, dass GlobalCube möglicherweise NUR Hyundai erfasst, nicht alle Standorte!
