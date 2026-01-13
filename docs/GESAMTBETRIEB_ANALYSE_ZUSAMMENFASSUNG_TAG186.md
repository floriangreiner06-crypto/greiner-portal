# Gesamtbetrieb Analyse Zusammenfassung - TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Status:** 🔍 **IN ANALYSE**

---

## 🎯 ZIEL

Gesamtbetrieb monatliche BWA für Dezember 2025 korrekt berechnen.

---

## 📊 ERGEBNISSE

### YTD (Kumuliert Sep-Dez 2025) ✅ **SEHR GUT!**

| Position | DRIVE | GlobalCube | Differenz | Status |
|----------|-------|------------|-----------|--------|
| Direkte Kosten | 625.530,17 € | 659.229,00 € | -33.698,83 € | ⚠️ |
| Betriebsergebnis | -374.008,68 € | -375.905,00 € | +1.896,32 € | ✅ |
| Unternehmensergebnis | -243.836,79 € | -245.733,00 € | +1.896,21 € | ✅ |

**Ergebnis:** ✅ **YTD-Werte sind sehr nah an GlobalCube!**
- Betriebsergebnis: Nur 1.896,32 € Differenz (0,50%)
- Verbesserung: Von -14.611,99 € (TAG 182) auf +1.896,32 €

### Monat Dezember 2025 🚨 **PROBLEM**

| Position | DRIVE API | DRIVE SQL | GlobalCube | Status |
|----------|-----------|-----------|------------|--------|
| Direkte Kosten | 728,41 € | 181.216,91 € | 189.866,00 € | 🚨 |
| Betriebsergebnis | 270.993,82 € | ? | -116.248,00 € | 🚨 |

**Ergebnis:** 🚨 **API zeigt falsche Werte!**
- API: 728,41 € (99,6% zu wenig!)
- SQL direkt: 181.216,91 € (4,6% Differenz zu GlobalCube)
- **Problem:** API-Logik ist falsch, SQL direkt ist korrekt!

---

## 🔍 ANALYSE

### 1. SQL-Direktabfrage (korrekt) ✅

**Query:**
```sql
SELECT COALESCE(SUM(...)/100.0, 0) as wert
FROM loco_journal_accountings
WHERE accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
  AND nominal_account_number BETWEEN 400000 AND 489999
  AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
  AND NOT (410021, 411xxx, 489xxx, ...)
  AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)) 
       OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1))
  AND (posting_text IS NULL OR posting_text NOT LIKE '%G&V-Abschluss%')
```

**Ergebnis:** 181.216,91 € ✅

### 2. API-Abfrage (falsch) ❌

**Code in `_berechne_bwa_werte()`:**
```python
if standort == '2' and firma == '1':
    direkte_kosten_filter = "AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1"
else:
    direkte_kosten_filter = firma_filter_kosten  # ← Für Gesamtbetrieb sollte das korrekt sein
```

**Für Gesamtbetrieb (firma='0', standort='0'):**
- `firma_filter_kosten` = `"AND ((substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref IN (1, 2)) OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1))"`

**Ergebnis:** 728,41 € ❌ (nur 0,4% von erwartetem Wert!)

---

## 💡 HYPOTHESEN

### Hypothese 1: Filter wird nicht korrekt angewendet
- `firma_filter_kosten` wird möglicherweise nicht korrekt in die Query eingefügt
- Oder es gibt ein Problem mit der String-Interpolation in f-Strings

### Hypothese 2: `convert_placeholders` Problem
- `convert_placeholders` könnte die Filter-Strings falsch verarbeiten
- Aber: `convert_placeholders` konvertiert nur `?` zu `%s`, sollte kein Problem sein

### Hypothese 3: Andere Filter überschreiben
- Möglicherweise gibt es zusätzliche Filter, die die direkten Kosten reduzieren
- Oder die Query wird mehrfach ausgeführt mit unterschiedlichen Filtern

### Hypothese 4: YTD vs. Monat Unterschied
- YTD funktioniert korrekt (625.530,17 €)
- Monat funktioniert nicht (728,41 € statt 181.216,91 €)
- **Frage:** Warum funktioniert YTD, aber Monat nicht?

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **API-Logik debuggen:**
   - Prüfen, was `firma_filter_kosten` für Gesamtbetrieb tatsächlich enthält
   - Prüfen, ob der Filter korrekt in die Query eingefügt wird
   - Prüfen, ob `convert_placeholders` die Filter korrekt verarbeitet

2. ⏳ **Vergleich YTD vs. Monat:**
   - YTD-Werte sind korrekt (625.530,17 €)
   - Warum funktioniert YTD, aber Monat nicht?
   - Gibt es einen Unterschied in der Query-Logik zwischen YTD und Monat?

3. ⏳ **Direkte SQL-Abfrage vs. API:**
   - Warum zeigt SQL direkt 181.216,91 €, aber API nur 728,41 €?
   - Gibt es einen Unterschied in der Query-Logik?

---

## 🔧 MÖGLICHE LÖSUNGEN

**Option 1:** Filter-Logik für Gesamtbetrieb überprüfen
- Sicherstellen, dass `firma_filter_kosten` für Gesamtbetrieb korrekt ist
- Sicherstellen, dass der Filter korrekt in die Query eingefügt wird

**Option 2:** Query-Logik vereinfachen
- Direkte SQL-Abfrage verwenden (wie in Test-Script)
- Oder Filter-Logik explizit für Gesamtbetrieb implementieren

**Option 3:** YTD-Logik auf Monat übertragen
- YTD funktioniert korrekt, Monat nicht
- Vielleicht gibt es einen Unterschied in der Logik, der behoben werden muss

---

## 📊 STATUS

- ✅ SQL-Direktabfrage funktioniert (181.216,91 €)
- ✅ YTD-Werte sind korrekt (625.530,17 €)
- ❌ API monatliche Werte funktionieren nicht (728,41 €)
- ⏳ Ursache identifizieren
- ⏳ Lösung implementieren

---

**Nächster Schritt:** API-Logik debuggen und Unterschied zwischen YTD und Monat identifizieren.
