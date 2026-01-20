# DB-Berechnung Korrektur - Variable Kosten

**TAG:** 199  
**Datum:** 2026-01-19  
**Problem:** DB-Berechnung stimmt nicht mit Locosoft überein

---

## Problem

**Screenshot zeigt:**
- VK brutto: 25.980,00 €
- MwSt: 4.148,07 €
- VK netto: 21.831,93 €
- Einsatzwert: 21.453,28 €
- Variable Kosten: 30,35 €
- **Kalkulierter Gesamteinsatz: 21.483,63 €** (Einsatzwert + variable Kosten)
- **DB: 348,30 €** (VK netto - Kalkulierter Gesamteinsatz)

**Aktuelle Berechnung (FALSCH):**
- DB = VK_netto - EK - Kosten = 21.831,93 - 21.453,28 - 30,35 = **-651,70 €** ❌

**Korrekte Berechnung:**
- DB = VK_netto - (EK + variable Kosten) = 21.831,93 - 21.483,63 = **348,30 €** ✅

---

## Lösung

### Variable Kosten

**Felder:**
- `calc_cost_internal_invoices` - Interne Rechnungen (Werkstatt)
- `calc_cost_other` - Sonstige Kosten

**Variable Kosten = calc_cost_internal_invoices + calc_cost_other**

### DB-Berechnung

**Regelbesteuerung:**
```
VK_netto = VK_brutto / 1.19
Einsatzwert = calc_basic_charge + calc_accessory + calc_extra_expenses 
              + calc_usage_value_encr_internal + calc_usage_value_encr_external
Variable Kosten = calc_cost_internal_invoices + calc_cost_other
Kalkulierter Gesamteinsatz = Einsatzwert + variable Kosten
DB = VK_netto - Kalkulierter Gesamteinsatz
```

**Differenzbesteuerung:**
```
Marge_brutto = VK_brutto - Einsatzwert
Marge_netto = Marge_brutto / 1.19
Variable Kosten = calc_cost_internal_invoices + calc_cost_other
DB = Marge_netto - variable Kosten
```

**WICHTIG:** Bei Regelbesteuerung werden variable Kosten zum Einsatzwert **addiert** (nicht abgezogen)!

---

## Änderungen

**Datei:** `api/fahrzeug_data.py`
- ✅ Variable Kosten: `calc_cost_internal_invoices + calc_cost_other`
- ✅ Regelbesteuerung: DB = VK_netto - (Einsatzwert + variable Kosten)
- ✅ Differenzbesteuerung: DB = Marge_netto - variable Kosten

---

## Test-Fahrzeug (111282)

**Erwartete Werte:**
- VK brutto: 25.980,00 €
- VK netto: 21.831,93 €
- Einsatzwert: 21.453,28 €
- Variable Kosten: 30,35 €
- Kalkulierter Gesamteinsatz: 21.483,63 €
- **DB: 348,30 €** ✅

---

## Status

✅ **Korrigiert**

Die DB-Berechnung sollte jetzt mit Locosoft übereinstimmen.
