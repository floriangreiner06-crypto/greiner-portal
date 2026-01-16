# BWA 743002 Korrektur - TAG 196

**Datum:** 2026-01-16  
**Status:** ✅ Korrektur implementiert

---

## 🐛 PROBLEM IDENTIFIZIERT

**YTD Betriebsergebnis bis Dezember 2025:**
- DRIVE: -407.613,15 €
- GlobalCube: -375.905,00 €
- **Differenz: -31.708,15 €** (DRIVE zu negativ)

**Ursache:** 743002 wurde nicht aus Einsatz YTD in der v2 API ausgeschlossen!

---

## 🔍 ANALYSE

### Einsatz YTD-Differenz

**Problem:**
- Einsatz YTD (API): 9.223.769,97 €
- Einsatz YTD (direkte Query mit 743002-Ausschluss): 9.207.314,53 €
- **Differenz: 16.455,44 €**

**743002 YTD:**
- Wert: 16.455,44 €
- **Genau die Differenz zwischen API und direkter Query!**

**Erkenntnis:**
- 743002 wird in `_berechne_bwa_ytd()` korrekt ausgeschlossen (Zeile 1035)
- 743002 wird in `get_bwa_v2()` YTD-Berechnung **NICHT** ausgeschlossen (Zeile 2327)
- Das erklärt die Differenz!

---

## ✅ KORREKTUR

**Änderung:** 743002 wird jetzt auch in der v2 API YTD-Berechnung ausgeschlossen.

**Geändert in:**
- ✅ `get_bwa_v2()` YTD Einsatz-Berechnung (Zeile 2327)

**SQL-Filter:**
```sql
AND nominal_account_number != 743002
```

---

## 📊 ERWARTETE AUSWIRKUNG

### YTD bis Dezember 2025

**Vor Korrektur:**
- Einsatz YTD: 9.223.769,97 €
- DB1 YTD: 1.394.623,39 €
- DB3 YTD: 431.324,40 €
- Betriebsergebnis YTD: -407.613,15 €
- Differenz zu GlobalCube: -31.708,15 €

**Nach Korrektur (erwartet):**
- Einsatz YTD: 9.207.314,53 € (9.223.769,97 - 16.455,44)
- DB1 YTD: 1.410.078,83 € (1.394.623,39 + 16.455,44)
- DB3 YTD: 447.779,84 € (431.324,40 + 16.455,44)
- Betriebsergebnis YTD: -391.157,71 € (-407.613,15 + 16.455,44)
- Differenz zu GlobalCube: -15.252,71 € (besser!)

**GlobalCube Referenz:**
- Betriebsergebnis YTD: -375.905,00 €
- **Erwartete Differenz nach Korrektur: -15.252,71 €** (statt -31.708,15 €)

---

## 🔧 TECHNISCHE DETAILS

### Geänderte Stelle

**Datei:** `api/controlling_api.py`  
**Funktion:** `get_bwa_v2()`  
**Zeile:** 2327

**Vorher:**
```sql
AND nominal_account_number BETWEEN 700000 AND 799999
{firma_filter_einsatz}
{guv_filter}
```

**Nachher:**
```sql
AND nominal_account_number BETWEEN 700000 AND 799999
AND nominal_account_number != 743002
{firma_filter_einsatz}
{guv_filter}
```

---

## 📋 NÄCHSTE SCHRITTE

1. ✅ **Service neu starten** - Erledigt
2. ⏳ **YTD-Werte erneut prüfen**
3. ⏳ **Prüfen ob BE YTD jetzt -391.157,71 € ist**
4. ⏳ **Weitere Differenzen analysieren** (verbleibende -15.252,71 €)

---

*Erstellt: TAG 196 | Autor: Claude AI*
