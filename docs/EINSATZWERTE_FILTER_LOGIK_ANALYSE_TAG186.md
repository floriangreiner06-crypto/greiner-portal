# Einsatzwerte Filter-Logik Analyse TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🔍 **AKTUELLE LOGIK ANALYSIERT**

---

## 🎯 ZIEL

Die **aktuelle Einsatzwerte-Filter-Logik** verstehen, bevor "blank" Konten geprüft werden.

---

## 📊 AKTUELLE FILTER-LOGIK (Gesamtbetrieb)

### Filter für Gesamtbetrieb (firma='0', standort='0')

```sql
firma_filter_einsatz = """AND (
    ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
    OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
)"""
```

### Zerlegung:

1. **Deggendorf Opel (Stellantis):**
   - `6. Ziffer = '1' OR (74xxxx AND branch=1) AND subsidiary=1 AND branch != 3`

2. **Landau (Stellantis):**
   - `branch_number = 3 AND subsidiary=1`

3. **Deggendorf Hyundai:**
   - `6. Ziffer = '1' AND subsidiary=2`

---

## 📋 ERGEBNISSE

### Gesamtbetrieb Einsatzwerte YTD (Jan-Dez 2025)

**Mit aktueller Filter-Logik:**
- ⏳ Wird berechnet...

**Alle Einsatzwerte (ohne Filter):**
- ⏳ Wird berechnet...

**Ausgeschlossene Konten:**
- ⏳ Wird berechnet...

---

## 🔍 ANALYSE

### Welche Konten werden ausgeschlossen?

**Konten, die NICHT durch Filter erfasst werden:**
- 6. Ziffer != '1' UND nicht 74xxxx mit branch=1 UND subsidiary != 1
- branch_number != 3 UND subsidiary != 1
- 6. Ziffer != '1' UND subsidiary != 2

**Beispiele:**
- Konten mit 6. Ziffer = '2', '3', '4', etc. (außer 74xxxx mit branch=1)
- Konten mit branch_number != 1,2,3
- Konten mit subsidiary != 1,2

---

## 📊 STATUS

- ⏳ Analyse läuft...
