# VKU-Analyse - Ist VKU bereits im Einsatzwert enthalten?

**TAG:** 199  
**Datum:** 2026-01-19  
**Problem:** VKU-Wert (8.114,48 €) kommt zu hoch vor, möglicherweise bereits im Einsatzwert berücksichtigt

---

## Problem

**Fahrzeug 111282 (VIN 013462):**
- VK brutto: 25.980,00 €
- VK netto: 21.831,93 €
- Einsatzwert: 21.453,28 €
- Variable Kosten: 30,35 €
- **VKU (claimed_amount): 8.114,48 €** ⚠️ (31% vom VK!)
- **Erwarteter DB: 348,30 €** (ohne VKU, da unverkauft)

**Beobachtung:**
- VKU von 8.114,48 € ist sehr hoch (31% vom VK brutto)
- Nur dieses eine Fahrzeug hat VKU in der Bestandsliste
- Benutzer vermutet: VKU könnte bereits im Einsatzwert enthalten sein

---

## SSOT-Formel (sync_sales.py)

**Aktuelle Formel (Zeile 223-224):**
```python
# Locosoft-Formel: DB = VK - MwSt - Einsatz - Var.Kosten + VKU
deckungsbeitrag = out_sale_price - mwst - einsatzwert - variable_kosten + verkaufsunterstuetzung
```

**Wichtig:** Diese Formel gilt für **verkaufte** Fahrzeuge (`out_sales_contract_date IS NOT NULL`)

---

## Mögliche Szenarien

### Szenario 1: VKU NICHT im Einsatzwert (aktuell implementiert)
```
DB = VK_netto - Einsatzwert - Variable Kosten + VKU
DB = 21.831,93 - 21.453,28 - 30,35 + 8.114,48 = 8.462,78 €
```
**Problem:** DB wäre 8.462,78 € (mit VKU), aber erwartet ist 348,30 € (ohne VKU)

### Szenario 2: VKU bereits im Einsatzwert enthalten
```
Einsatzwert_ohne_VKU = Einsatzwert - VKU
Einsatzwert_ohne_VKU = 21.453,28 - 8.114,48 = 13.338,80 €
DB = VK_netto - Einsatzwert_ohne_VKU - Variable Kosten
DB = 21.831,93 - 13.338,80 - 30,35 = 8.462,78 €
```
**Problem:** DB wäre immer noch 8.462,78 € (passt nicht zu 348,30 €)

### Szenario 3: VKU sollte NICHT verwendet werden (Bestandsfahrzeuge)
```
DB = VK_netto - Einsatzwert - Variable Kosten
DB = 21.831,93 - 21.453,28 - 30,35 = 348,30 € ✅
```
**Lösung:** VKU wird nur bei verkauften Fahrzeugen addiert (aktuell implementiert)

---

## Analyse der VKU-Daten

**Aus Locosoft `dealer_sales_aid`:**
- `claimed_amount`: 8.114,48 € (geforderte VKU)
- `granted_amount`: 0,00 € (gewährte VKU)
- `was_paid_on`: NULL (noch nicht ausgezahlt)
- `available_until`: 2025-04-25

**Vergleich mit anderen Fahrzeugen:**
- Fahrzeug 111282: **einziger** Bestandsfahrzeug mit VKU
- Alle anderen Bestandsfahrzeuge: VKU = NULL oder 0

---

## Fragen zur Klärung

1. **Ist VKU bereits im Einsatzwert enthalten?**
   - Wenn ja: VKU sollte NICHT zum DB addiert werden
   - Wenn nein: VKU wird nur bei verkauften Fahrzeugen addiert (aktuell korrekt)

2. **Sollte `granted_amount` statt `claimed_amount` verwendet werden?**
   - `claimed_amount`: Geforderte VKU (8.114,48 €)
   - `granted_amount`: Gewährte VKU (0,00 €)
   - Aktuell wird `claimed_amount` verwendet

3. **Warum ist VKU so hoch (31% vom VK)?**
   - Normalerweise sind VKU deutlich niedriger
   - Möglicherweise handelt es sich um einen Sonderfall (z.B. Garantie-Rücknahme)

---

## Aktuelle Implementierung

**In `api/fahrzeug_data.py`:**
- VKU wird nur bei **verkauften** Fahrzeugen zum DB addiert
- Bestandsfahrzeuge (`out_invoice_date IS NULL`): DB ohne VKU ✅
- Verkaufte Fahrzeuge (`out_invoice_date IS NOT NULL`): DB mit VKU

**Formel:**
```sql
DB = VK_netto - (Einsatzwert + Variable Kosten) + VKU (nur wenn verkauft)
```

---

## Empfehlung

**Status:** Aktuelle Implementierung ist korrekt für Bestandsfahrzeuge
- DB = 348,30 € (ohne VKU) ✅

**Offene Frage:** 
- Ist VKU bereits im Einsatzwert enthalten?
- Wenn ja, sollte VKU auch bei verkauften Fahrzeugen NICHT addiert werden?

**Nächste Schritte:**
1. Prüfen: Ist VKU in `calc_basic_charge` oder anderen calc_*-Feldern enthalten?
2. Validieren: DB-Berechnung mit anderen Fahrzeugen vergleichen
3. Dokumentation: Wie wird VKU in Locosoft behandelt?
