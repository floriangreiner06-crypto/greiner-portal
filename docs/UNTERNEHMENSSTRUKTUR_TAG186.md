# Unternehmensstruktur - Autohaus Greiner Gruppe TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** ✅ **STRUKTUR DOKUMENTIERT**

---

## 🏢 RECHTLICHE STRUKTUR

### Unternehmen

1. **Autohaus Greiner GmbH & Co. KG** (Stellantis)
   - **subsidiary_to_company_ref = 1**
   - Standorte:
     - Deggendorf Opel (branch_number = 1)
     - Landau (branch_number = 3)

2. **Auto Greiner GmbH & Co. KG** (Hyundai)
   - **subsidiary_to_company_ref = 2**
   - Standorte:
     - Deggendorf Hyundai (branch_number = 2)

---

## 📍 STANDORTE

### Standort-Mapping

| Standort-ID | Name | Firma | branch_number | subsidiary_to_company_ref | Kürzel |
|-------------|------|-------|---------------|---------------------------|--------|
| **1** | Deggendorf Opel | Stellantis | 1 | 1 | DEG |
| **2** | Deggendorf Hyundai | Hyundai | 2 | 2 | HYU |
| **3** | Landau | Stellantis | 3 | 1 | LAN |

### Standort-Namen

```python
STANDORT_NAMEN = {
    1: 'Deggendorf Opel',
    2: 'Deggendorf Hyundai',
    3: 'Landau Opel'
}
```

---

## 🔢 FILTER-LOGIK

### subsidiary_to_company_ref (Firma)

- **1 = Stellantis** (Autohaus Greiner GmbH & Co. KG)
  - Deggendorf Opel (branch_number = 1)
  - Landau (branch_number = 3)

- **2 = Hyundai** (Auto Greiner GmbH & Co. KG)
  - Deggendorf Hyundai (branch_number = 2)

### branch_number (Physischer Standort)

- **1 = Deggendorf** (Stellantis/Opel)
- **2 = Deggendorf** (Hyundai)
- **3 = Landau** (Stellantis/Opel)

### BWA-Filter-Parameter

**firma:**
- `'0'` = Alle Firmen
- `'1'` = Stellantis (Autohaus Greiner)
- `'2'` = Hyundai (Auto Greiner)

**standort:**
- `'0'` = Alle Standorte
- `'1'` = Deggendorf (nur Stellantis, wenn firma='1')
- `'2'` = Landau (nur Stellantis, wenn firma='1')
- `'deg-both'` = Deggendorf (Stellantis + Hyundai)

---

## 📊 KONTEN-ZUORDNUNG

### Umsatz (8xxxxx)

**Filter-Logik:**
- **Deggendorf Opel:** `branch_number = 1 AND subsidiary_to_company_ref = 1`
- **Deggendorf Hyundai:** `branch_number = 2 AND subsidiary_to_company_ref = 2`
- **Landau:** `branch_number = 3 AND subsidiary_to_company_ref = 1`

### Einsatz (7xxxxx)

**Filter-Logik:**
- **Deggendorf Opel:** `6. Ziffer = '1' AND subsidiary_to_company_ref = 1 AND branch_number != 3`
- **Deggendorf Hyundai:** `6. Ziffer = '1' AND subsidiary_to_company_ref = 2`
- **Landau:** `branch_number = 3 AND subsidiary_to_company_ref = 1`

### Kosten (4xxxxx)

**Filter-Logik:**
- **Deggendorf Opel:** `branch_number = 1 AND 6. Ziffer = '1' AND subsidiary_to_company_ref = 1`
- **Deggendorf Hyundai:** `6. Ziffer = '1' AND subsidiary_to_company_ref = 2`
- **Landau:** `branch_number = 3 AND subsidiary_to_company_ref = 1` (oder `6. Ziffer = '2'` für bestimmte Kostenarten)

---

## 🎯 GESAMTBETRIEB (firma='0', standort='0')

**Kombination:**
- Deggendorf Opel (branch=1, subsidiary=1)
- Deggendorf Hyundai (branch=2, subsidiary=2)
- Landau (branch=3, subsidiary=1)

**Filter:**
```sql
-- Umsatz
(branch_number = 1 AND subsidiary_to_company_ref = 1) 
OR (branch_number = 2 AND subsidiary_to_company_ref = 2) 
OR (branch_number = 3 AND subsidiary_to_company_ref = 1)

-- Einsatz
((6. Ziffer='1' AND subsidiary=1 AND branch != 3) OR (74xxxx AND branch=1 AND subsidiary=1))
OR (branch_number = 3 AND subsidiary_to_company_ref = 1)
OR (6. Ziffer='1' AND subsidiary_to_company_ref = 2)

-- Kosten
(6. Ziffer='1' AND subsidiary IN (1,2)) 
OR (6. Ziffer='2' AND subsidiary=1)
```

---

## 📋 ZUSAMMENFASSUNG

### Rechtliche Einheiten

1. **Autohaus Greiner GmbH & Co. KG** (Stellantis)
   - Deggendorf Opel
   - Landau

2. **Auto Greiner GmbH & Co. KG** (Hyundai)
   - Deggendorf Hyundai

### Physische Standorte

1. **Deggendorf** (2 Betriebe)
   - Autohaus Greiner (Opel/Stellantis)
   - Auto Greiner (Hyundai)

2. **Landau** (1 Betrieb)
   - Autohaus Greiner (Opel/Stellantis)

---

## 🔍 WICHTIGE ERKENNTNISSE

1. **Zwei separate rechtliche Einheiten:**
   - Autohaus Greiner GmbH & Co. KG (Stellantis)
   - Auto Greiner GmbH & Co. KG (Hyundai)

2. **Drei physische Standorte:**
   - Deggendorf Opel (branch=1)
   - Deggendorf Hyundai (branch=2)
   - Landau (branch=3)

3. **Filter-Logik ist komplex:**
   - Umsatz: via branch_number
   - Einsatz: via 6. Ziffer (Konto-Endziffer)
   - Kosten: via branch_number ODER 6. Ziffer (abhängig von Standort)

---

**NÄCHSTER SCHRITT:** Diese Struktur verstehen, um die "blank" Konten-Filter-Logik zu analysieren!
