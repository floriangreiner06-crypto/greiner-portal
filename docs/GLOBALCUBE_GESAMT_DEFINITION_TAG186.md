# GlobalCube "Gesamt" Definition TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ✅ **DEFINITION KLAR**

---

## 🎯 GLOBALCUBE "GESAMT" DEFINITION

**GlobalCube "Gesamt" = Opel DEG + Hyundai DEG + Opel LAN**

Das bedeutet:
- **Deggendorf Opel** (Autohaus Greiner GmbH): `subsidiary=1, branch=1`
- **Deggendorf Hyundai** (Auto Greiner GmbH): `subsidiary=2, branch=2`
- **Landau** (Autohaus Greiner GmbH): `subsidiary=1, branch=3`

**NICHT enthalten:**
- Alle anderen Standorte/Kombinationen

---

## 📊 AKTUELLE DRIVE-FILTER-LOGIK

**Für Gesamtbetrieb (firma='0', standort='0'):**

```sql
firma_filter_einsatz = """AND (
    ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' OR (nominal_account_number BETWEEN 740000 AND 749999 AND branch_number = 1)) AND subsidiary_to_company_ref = 1 AND branch_number != 3)
    OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
    OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2)
)"""
```

**Zerlegung:**
1. **Deggendorf Opel:** `6. Ziffer='1' OR (74xxxx AND branch=1) AND subsidiary=1 AND branch != 3`
2. **Landau:** `branch=3 AND subsidiary=1`
3. **Deggendorf Hyundai:** `6. Ziffer='1' AND subsidiary=2`

---

## 📋 ERGEBNISSE

### Standort-Zerlegung (DRIVE):

| Standort | Wert | Filter |
|----------|------|--------|
| Deggendorf Opel | 13,409,446.48 € | `6.Ziffer='1' OR (74xxxx AND branch=1) AND subsidiary=1 AND branch != 3` |
| Deggendorf Hyundai | 8,958,535.51 € | `6.Ziffer='1' AND subsidiary=2` |
| Landau | 3,655,537.42 € | `branch=3 AND subsidiary=1` |
| **Summe** | **26,023,519.41 €** | |

### Vergleich mit GlobalCube:

| Quelle | Wert |
|--------|------|
| **DRIVE (Summe)** | **26,023,519.41 €** |
| **GlobalCube** | **9,191,864.00 €** |
| **Differenz** | **+16,831,655.41 €** |

---

## 🔍 PROBLEM-ANALYSE

**Die Filter-Logik erfasst korrekt die drei Standorte:**
- ✅ Deggendorf Opel: 13.4 Mio. €
- ✅ Deggendorf Hyundai: 9.0 Mio. €
- ✅ Landau: 3.7 Mio. €
- ✅ Keine falsch erfassten Konten

**Aber:** GlobalCube zeigt nur 9.2 Mio. €, während DRIVE 26.0 Mio. € zeigt.

**Das Problem muss also woanders liegen:**
- Möglicherweise verwendet GlobalCube andere Filter für Einsatzwerte?
- Z.B. nur bestimmte Konten-Bereiche (71xxxx, 72xxxx)?
- Oder andere Standort-Logik?

---

## 🎯 NÄCHSTE SCHRITTE

1. **Prüfe, ob GlobalCube nur bestimmte Konten-Bereiche verwendet:**
   - Nur 71xxxx (NW Einsatz)?
   - Nur 72xxxx (GW Einsatz)?
   - Nur 71xxxx + 72xxxx?

2. **Prüfe, ob GlobalCube andere Standort-Filter verwendet:**
   - Vielleicht nur Deggendorf (ohne Landau)?
   - Oder andere Kombinationen?

3. **Prüfe, ob GlobalCube andere Buchungs-Typen verwendet:**
   - Nur SOLL-Buchungen (ohne HABEN)?
   - Oder andere Logik?

---

**KRITISCHE ERKENNTNIS:** Die Standort-Filter sind korrekt! Das Problem muss in anderen Filtern liegen (Konten-Bereiche, Buchungs-Typen, etc.)!
