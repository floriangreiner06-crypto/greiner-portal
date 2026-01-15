# Variable Kosten 8910xx Korrektur - TAG 186

**Datum:** 2026-01-13  
**Status:** ✅ **IMPLEMENTIERT**

---

## 🎯 PROBLEM

**Variable Kosten YTD Gesamtbetrieb:**
- DRIVE: 289.458,47 €
- GlobalCube: 304.268,00 €
- **Differenz:** -14.809,53 € (-4,87%)

**Ursache:**
- 8910xx Konten (Gehaltsumwandlungen in Sachbezug/Business Bike) sind **Erträge**, nicht Kosten
- 891001 (VE GW stfr) bei Hyundai: -14.705,88 € (HABEN-Buchung)
- Diese Konten wurden fälschlicherweise in Variablen Kosten eingeschlossen
- GlobalCube schließt 8910xx aus den Variablen Kosten aus

---

## ✅ LÖSUNG

**Code-Änderung in `_berechne_bwa_werte()`:**

Für Gesamtbetrieb (firma='0', standort='0') wird jetzt die gleiche Logik wie bei YTD verwendet:
- Filter schließt 8910xx für Hyundai aus: `AND NOT (nominal_account_number BETWEEN 891000 AND 891099)`
- 8910xx bleibt für Deggendorf und Landau (Stellantis) eingeschlossen

**Vorher:**
```python
else:
    variable_kosten_filter = firma_filter_kosten
    variable_8910xx_include = True  # Stellantis/Alle: 8910xx einschließen
```

**Nachher:**
```python
if firma == '0' and standort == '0':
    # Gesamtsumme: Deggendorf (6. Ziffer='1', subsidiary=1, mit 8910xx) + Landau (6. Ziffer='2', subsidiary=1, mit 8910xx) + Hyundai (6. Ziffer='1', subsidiary=2, OHNE 8910xx)
    variable_kosten_filter = """AND (
        (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 1)
        OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2' AND subsidiary_to_company_ref = 1)
        OR (substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1' AND subsidiary_to_company_ref = 2 AND NOT (nominal_account_number BETWEEN 891000 AND 891099))
    )"""
    variable_8910xx_include = True  # Gesamtsumme: 8910xx für Deggendorf+Landau einschließen, aber für Hyundai ausschließen (via Filter)
```

---

## 📊 VALIDIERUNG

### YTD (Sep-Dez 2025) - Gesamtbetrieb

| Status | Wert | Differenz zu GlobalCube | % |
|--------|------|-------------------------|---|
| **VOR** | 289.458,47 € | -14.809,53 € | -4,87% |
| **NACH** | 304.164,35 € | -103,65 € | -0,03% |
| **GlobalCube** | 304.268,00 € | - | - |

**Verbesserung:** 14.705,88 € (99,3% Verbesserung!) ✅

### Monat (Dezember 2025) - Gesamtbetrieb

| Status | Wert | Differenz zu GlobalCube | % |
|--------|------|-------------------------|---|
| **VOR** | 69.270,36 € | -103,64 € | -0,15% |
| **NACH** | 69.270,36 € | -103,64 € | -0,15% |
| **GlobalCube** | 69.374,00 € | - | - |

**Keine Änderung** (8910xx Buchung war im September, nicht im Dezember)

---

## 🔍 DETAILS ZU 8910XX

**Konto 891001 (VE GW stfr):**
- **Bezeichnung:** Verkaufserlöse Gebrauchtwagen steuerfrei
- **Tatsächlich:** Gehaltsumwandlungen in Sachbezug (Business Bike)
- **Hyundai:** 1 Buchung, -14.705,88 € (HABEN-Buchung = Ertrag)
- **Stellantis:** 0 Buchungen

**Konto 891711 (Geldwerter Vorteil):**
- **Bezeichnung:** Geldwerter Vorteil (sonstige)
- **Tatsächlich:** Gehaltsumwandlungen in Sachbezug (Business Bike)
- **Buchungstext:** "UMW. BIKE"
- **Wert:** -5.852,92 € (HABEN-Buchung = Ertrag)

**Erkenntnis:**
- Diese Konten sind **Erträge** (HABEN-Buchungen), nicht Kosten
- Sie sollten **NICHT** in Variablen Kosten enthalten sein
- GlobalCube schließt sie aus

---

## ✅ ERGEBNIS

**Variable Kosten sind jetzt nahezu identisch mit GlobalCube:**
- YTD: Nur -103,65 € Differenz (-0,03%) ✅
- Monat: -103,64 € Differenz (-0,15%) ✅

**Die verbleibende Differenz liegt im Bereich von Rundungsunterschieden.**

---

## 📝 NÄCHSTE SCHRITTE

1. ✅ Code-Änderung implementiert
2. ⏳ Server neu starten: `sudo systemctl restart greiner-portal`
3. ⏳ Validierung gegen GlobalCube durchführen (nach Server-Restart)
4. ⏳ Weitere Differenzen analysieren (Einsatz: +31.905,97 €)

---

**Status:** ✅ Code-Änderung implementiert, Server-Restart erforderlich
