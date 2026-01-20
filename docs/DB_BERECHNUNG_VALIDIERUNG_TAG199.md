# DB-Berechnung Validierung - Test-Fahrzeuge

**TAG:** 199  
**Datum:** 2026-01-19  
**Status:** Validierung der DB-Berechnung

---

## Test-Fahrzeug 1: 111282 (Regelbesteuert)

**Screenshot-Daten:**
- VK brutto: 25.980,00 €
- MwSt: 4.148,07 €
- VK netto: 21.831,93 €
- Einsatzwert: 21.453,28 €
- Variable Kosten: 30,35 €
- Kalkulierter Gesamteinsatz: 21.483,63 €
- **DB: 348,30 €** ✅

**Berechnung:**
```
VK_netto = 25.980 / 1.19 = 21.831,93 €
Kalkulierter Gesamteinsatz = 21.453,28 + 30,35 = 21.483,63 €
DB = 21.831,93 - 21.483,63 = 348,30 € ✅
```

---

## Test-Fahrzeug 2: 211217 (Regelbesteuert, Verlust)

**Screenshot-Daten:**
- VK brutto: 52.084 €
- EK: 57.248 € (vermutlich Einsatzwert)
- **DB: -5.261 €** (negativ, rot markiert)

**Berechnung (erwartet):**
```
VK_netto = 52.084 / 1.19 = 43.768,07 €
Einsatzwert = 57.248 € (vermutlich)
Variable Kosten = ? (nicht sichtbar im Screenshot)
Kalkulierter Gesamteinsatz = Einsatzwert + variable Kosten
DB = VK_netto - Kalkulierter Gesamteinsatz
```

**Problem:** DB sollte negativ sein, aber der Wert (-5.261 €) passt nicht zur einfachen Berechnung.

**Mögliche Erklärungen:**
1. Variable Kosten sind im Einsatzwert bereits enthalten?
2. EK (57.248 €) ist nicht der Einsatzwert, sondern ein anderer Wert?
3. Es gibt weitere Kosten, die berücksichtigt werden müssen?

---

## Implementierte Formel

**Regelbesteuerung:**
```sql
DB = ROUND(VK_brutto / 1.19, 2) - (
    calc_basic_charge + calc_accessory + calc_extra_expenses
    + calc_usage_value_encr_internal + calc_usage_value_encr_external
    + calc_cost_internal_invoices + calc_cost_other
)
```

**Differenzbesteuerung:**
```sql
DB = ROUND(
    GREATEST(VK_brutto - (calc_basic_charge + ...), 0) / 1.19, 2
) - (calc_cost_internal_invoices + calc_cost_other)
```

---

## Nächste Schritte

1. ✅ Prüfen: Welche Felder werden für EK verwendet?
2. ✅ Prüfen: Sind variable Kosten bereits im Einsatzwert enthalten?
3. ✅ Validieren: DB-Berechnung mit echten Daten testen

---

## Status

⚠️ **Validierung erforderlich**

Die Formel sollte korrekt sein, aber die Werte müssen mit echten Locosoft-Daten validiert werden.
