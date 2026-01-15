# Rohdaten-Interpretation Fehler - Analyse TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🔍 **ANALYSE LÄUFT**

---

## 🎯 PROBLEM

**GlobalCube ist korrekt. Wir interpretieren die Rohdaten aus Locosoft falsch!**

- **DRIVE:** 26,023,519.41 €
- **GlobalCube:** 9,191,864.00 €
- **Differenz:** +16,831,655.41 € (+183%)

---

## ✅ WAS WIR BEREITS GEPRÜFT HABEN

### 1. debit_or_credit Logik ✅

**DRIVE:**
```sql
CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
```

**GlobalCube LOC_Belege View:**
```sql
CASE WHEN debit_or_credit = 'H' THEN (posted_value / 100) * -1 
     ELSE (posted_value / 100) END
```

**Ergebnis:** Beide Logiken sind identisch! ✅

### 2. is_profit_loss_account Filter ✅

**GlobalCube LOC_Belege View filtert nach:**
```sql
WHERE T2."is_profit_loss_account" = 'J'
```

**Ergebnis:** Alle 7xxxxx Konten sind bereits P&L-Konten. Filter ändert nichts. ✅

### 3. JOIN-Logik ✅

**GlobalCube LOC_Belege View:**
```sql
INNER JOIN nominal_accounts ON 
    nominal_account_number = nominal_account_number
    AND subsidiary_to_company_ref = subsidiary_to_company_ref
```

**Ergebnis:** Keine Konten ohne Match. Keine Duplikate. ✅

### 4. Konten-Bereiche ✅

| Bereich | Wert (mit is_profit_loss_account) |
|---------|-----------------------------------|
| 71xxxx (NW) | 10,834,760.81 € |
| 72xxxx (GW) | 10,674,255.21 € |
| 73xxxx (Teile) | 3,136,156.36 € |
| 74xxxx (Lohn) | 1,279,700.98 € |
| Andere | 98,646.05 € |
| **GESAMT** | **26,023,519.41 €** |

**Nur 71xxxx + 72xxxx:** 21,509,016.02 € (immer noch zu viel!)

---

## 🔍 MÖGLICHE URSACHEN

### Hypothese 1: Falsche Standort-Filter ⭐⭐⭐

**Aktuelle DRIVE-Filter (Gesamtbetrieb):**
```sql
AND (
    ((6. Ziffer='1' OR (74xxxx AND branch=1)) AND subsidiary=1 AND branch != 3)
    OR (branch=3 AND subsidiary=1)
    OR (6. Ziffer='1' AND subsidiary=2)
)
```

**Mögliche Probleme:**
- Filter erfasst zu viele Standorte?
- Filter erfasst falsche Kombinationen?
- GlobalCube verwendet andere Filter-Logik?

### Hypothese 2: Falsche Firma-Filter ⭐⭐

**Aktuelle DRIVE-Filter:**
- Deggendorf Opel (subsidiary=1, branch=1)
- Landau (subsidiary=1, branch=3)
- Deggendorf Hyundai (subsidiary=2, branch=2)

**Vermutung:**
- Hyundai (8.96 Mio. €) ist sehr nah an GlobalCube (9.19 Mio. €)!
- **Möglicherweise erfasst GlobalCube NUR Hyundai?**

### Hypothese 3: Falsche Konten-Bereiche ⭐

**Aktuelle DRIVE-Filter:**
- Alle 7xxxxx Konten (700000-799999)

**Mögliche Probleme:**
- GlobalCube schließt bestimmte Bereiche aus?
- Z.B. nur 71xxxx, 72xxxx, aber nicht 73xxxx, 74xxxx?

### Hypothese 4: Falscher Zeitraum ⭐

**Aktuelle DRIVE-Filter:**
- Jan-Dez 2025 (Kalenderjahr)

**Mögliche Probleme:**
- GlobalCube verwendet Wirtschaftsjahr (Sep 2024 - Aug 2025)?
- Oder andere Datums-Logik?

---

## 📋 NÄCHSTE SCHRITTE

1. **Prüfe Standort-für-Standort:**
   - Deggendorf Opel (DRIVE) vs. GlobalCube
   - Deggendorf Hyundai (DRIVE) vs. GlobalCube
   - Landau (DRIVE) vs. GlobalCube

2. **Prüfe Firma-für-Firma:**
   - Stellantis (DRIVE) vs. GlobalCube
   - Hyundai (DRIVE) vs. GlobalCube

3. **Prüfe Konten-Bereiche:**
   - Welche Bereiche erfasst GlobalCube?
   - Werden 73xxxx, 74xxxx ausgeschlossen?

4. **Prüfe Zeitraum:**
   - Welcher Zeitraum wird in GlobalCube verwendet?
   - Kalenderjahr oder Wirtschaftsjahr?

---

**KRITISCHE ERKENNTNIS:** Die debit_or_credit Logik ist korrekt. Der is_profit_loss_account Filter ändert nichts. Das Problem muss in den **Standort- oder Firma-Filtern** liegen!
