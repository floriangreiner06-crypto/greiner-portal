# Gesamtbetrieb Monatlich Problem - TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🔍 **IN ANALYSE**

---

## 🐛 PROBLEM

**Monatliche BWA für Gesamtbetrieb Dezember 2025:**
- **DRIVE API:** 728,41 € direkte Kosten
- **DRIVE SQL direkt:** 181.216,91 € direkte Kosten
- **GlobalCube Referenz:** 189.866,00 € direkte Kosten

**Differenz:**
- API vs. SQL direkt: -180.488,50 € (99,6% zu wenig!)
- SQL direkt vs. GlobalCube: -8.649,09 € (4,6% Differenz)

---

## 🔍 ANALYSE

### 1. SQL-Direktabfrage (korrekt)

```sql
SELECT COALESCE(SUM(
    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
)/100.0, 0) as wert
FROM loco_journal_accountings
WHERE accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
  AND nominal_account_number BETWEEN 400000 AND 489999
  AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
  AND NOT (
    nominal_account_number = 410021
    OR nominal_account_number BETWEEN 411000 AND 411999
    OR nominal_account_number BETWEEN 415100 AND 415199
    OR nominal_account_number BETWEEN 424000 AND 424999
    OR nominal_account_number BETWEEN 435500 AND 435599
    OR nominal_account_number BETWEEN 438000 AND 438999
    OR nominal_account_number BETWEEN 455000 AND 456999
    OR nominal_account_number BETWEEN 487000 AND 487099
    OR nominal_account_number BETWEEN 489000 AND 489999
    OR nominal_account_number BETWEEN 491000 AND 497999
  )
  AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)) 
       OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1))
  AND (posting_text IS NULL OR posting_text NOT LIKE '%G&V-Abschluss%')
```

**Ergebnis:** 181.216,91 € ✅

### 2. API-Abfrage (falsch)

**Code in `_berechne_bwa_werte()`:**
```python
if standort == '2' and firma == '1':
    direkte_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
else:
    direkte_kosten_filter = firma_filter_kosten  # ← Für Gesamtbetrieb sollte das korrekt sein
```

**Für Gesamtbetrieb (firma='0', standort='0'):**
- `firma_filter_kosten` sollte sein: `"AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1))"`

**Ergebnis:** 728,41 € ❌

---

## 💡 HYPOTHESEN

### Hypothese 1: `convert_placeholders` Problem
- `convert_placeholders` könnte die Filter-Strings falsch verarbeiten
- Möglicherweise werden `%s` Platzhalter in den Filter-Strings falsch interpretiert

### Hypothese 2: Filter wird nicht korrekt angewendet
- `firma_filter_kosten` wird möglicherweise nicht korrekt in die Query eingefügt
- Oder es gibt ein Problem mit der String-Interpolation

### Hypothese 3: Andere Filter überschreiben
- Möglicherweise gibt es zusätzliche Filter, die die direkten Kosten reduzieren
- Oder die Query wird mehrfach ausgeführt mit unterschiedlichen Filtern

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **API-Logik debuggen:**
   - Prüfen, was `firma_filter_kosten` für Gesamtbetrieb tatsächlich enthält
   - Prüfen, ob `convert_placeholders` die Filter korrekt verarbeitet
   - Prüfen, ob die Query korrekt ausgeführt wird

2. ⏳ **Vergleich mit YTD:**
   - YTD-Werte sind korrekt (625.530,17 €)
   - Warum funktioniert YTD, aber Monat nicht?

3. ⏳ **Direkte SQL-Abfrage vs. API:**
   - Warum zeigt SQL direkt 181.216,91 €, aber API nur 728,41 €?
   - Gibt es einen Unterschied in der Query-Logik?

---

## 🔧 MÖGLICHE LÖSUNG

**Option 1:** `convert_placeholders` Problem beheben
- Filter-Strings direkt in Query einfügen, ohne `convert_placeholders`
- Oder `convert_placeholders` so anpassen, dass es Filter-Strings korrekt verarbeitet

**Option 2:** Filter-Logik für Gesamtbetrieb überprüfen
- Sicherstellen, dass `firma_filter_kosten` für Gesamtbetrieb korrekt ist
- Sicherstellen, dass der Filter korrekt in die Query eingefügt wird

**Option 3:** Query-Logik vereinfachen
- Direkte SQL-Abfrage verwenden (wie in Test-Script)
- Oder Filter-Logik explizit für Gesamtbetrieb implementieren

---

## 📊 STATUS

- ✅ SQL-Direktabfrage funktioniert (181.216,91 €)
- ❌ API-Abfrage funktioniert nicht (728,41 €)
- ⏳ Ursache identifizieren
- ⏳ Lösung implementieren

---

**Nächster Schritt:** API-Logik debuggen und Ursache identifizieren.
