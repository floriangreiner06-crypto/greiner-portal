# BWA Landau Problem - TAG 182

**Datum:** 2026-01-12  
**Status:** ⚠️ Massiver Unterschied zwischen DRIVE und GlobalCube

---

## 🚨 PROBLEM

**DRIVE BWA für Landau (YTD Sep-Dez 2025):**
- Betriebsergebnis: **193.611,02 €** (positiv)
- Unternehmensergebnis: **193.611,02 €** (positiv)

**GlobalCube BWA für Landau (YTD Sep-Dez 2025):**
- Betriebsergebnis: **-82.219,00 €** (negativ)
- Unternehmensergebnis: **-82.219,00 €** (negativ)

**Differenz:** **275.830,02 €** ⚠️

---

## 📊 DETAILLIERTE WERTE

### DRIVE (Standort 3, firma=1, standort=2):

| Position | Wert YTD |
|----------|----------|
| Umsatzerlöse | 1.385.353,71 € |
| Einsatzwerte | 1.172.273,16 € |
| DB1 | 213.080,55 € |
| Variable Kosten | 13.455,61 € |
| DB2 | 199.624,94 € |
| Direkte Kosten | 2.428,47 € |
| DB3 | 197.196,47 € |
| Indirekte Kosten | 3.585,45 € |
| **Betriebsergebnis** | **193.611,02 €** |
| Neutrales Ergebnis | 0,00 € |
| **Unternehmensergebnis** | **193.611,02 €** |

### GlobalCube Referenz:

| Position | Wert YTD |
|----------|----------|
| **Betriebsergebnis** | **-82.219,00 €** |
| **Unternehmensergebnis** | **-82.219,00 €** |

---

## 🔍 ANALYSE

### Filter-Logik für Landau:

**Aktuell in DRIVE:**
- Umsatz: `branch_number = 3 AND subsidiary_to_company_ref = 1`
- Einsatz: `substr(6. Ziffer) = '2' AND subsidiary_to_company_ref = 1`
- Kosten: `branch_number = 3 AND subsidiary_to_company_ref = 1`

**Ergebnis:**
- Umsatz: 1.385.353,71 €
- Einsatz: 1.172.273,16 €
- Direkte Kosten: 2.428,47 €
- Indirekte Kosten: 3.585,45 €
- **BE: 193.611,02 €** (positiv)

**GlobalCube zeigt:**
- **BE: -82.219,00 €** (negativ)

**Differenz:** 275.830,02 €

---

## 💡 MÖGLICHE URSACHEN

### 1. Falsche Filter-Logik

**Hypothese:** GlobalCube verwendet möglicherweise andere Filter für Landau.

**Mögliche Unterschiede:**
- GlobalCube verwendet `6. Ziffer = '2'` für Kosten (statt `branch_number = 3`)
- GlobalCube verwendet andere `subsidiary`-Filter
- GlobalCube verwendet andere Konten-Bereiche

### 2. Falsche Datenquelle

**Hypothese:** GlobalCube verwendet möglicherweise andere Datenquellen oder Zeiträume.

**Mögliche Unterschiede:**
- GlobalCube verwendet andere Buchungsdaten
- GlobalCube verwendet andere Konten-Mappings
- GlobalCube verwendet andere Zeiträume

### 3. Falsche Berechnungslogik

**Hypothese:** Die BWA-Berechnungslogik für Landau ist anders als für "Alle Standorte".

**Mögliche Unterschiede:**
- Landau hat spezielle Konten, die anders behandelt werden müssen
- Landau hat spezielle Kosten-Zuordnungen
- Landau hat spezielle Umsatz/Einsatz-Zuordnungen

---

## 🔧 NÄCHSTE SCHRITTE

1. ⏳ **GlobalCube Filter-Logik analysieren**
   - Welche Filter verwendet GlobalCube für Landau?
   - Gibt es Unterschiede zu DRIVE?

2. ⏳ **Alternative Filter testen**
   - Test: Kosten mit `6. Ziffer = '2'` (statt `branch_number = 3`)
   - Test: Andere `subsidiary`-Filter
   - Test: Andere Konten-Bereiche

3. ⏳ **Datenquelle validieren**
   - Prüfe ob GlobalCube andere Datenquellen verwendet
   - Prüfe ob GlobalCube andere Zeiträume verwendet

4. ⏳ **Berechnungslogik validieren**
   - Prüfe ob Landau spezielle Berechnungsregeln hat
   - Prüfe ob Konten anders zugeordnet werden müssen

---

## 📝 STATUS

- ⚠️ **Massiver Unterschied:** 275.830,02 € Differenz
- ⏳ **Ursache unbekannt:** Filter-Logik, Datenquelle oder Berechnungslogik?
- ⏳ **Weitere Analyse erforderlich**

---

**Nächster Schritt:** GlobalCube Filter-Logik für Landau analysieren und mit DRIVE vergleichen.
