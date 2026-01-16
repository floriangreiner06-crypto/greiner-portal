# BWA Zurückgestellte Konten Korrektur - TAG 196

**Datum:** 2026-01-14  
**TAG:** 196  
**Status:** ✅ **KORREKTUR IMPLEMENTIERT**

---

## 🎯 PROBLEM IDENTIFIZIERT

**Einsatz YTD-Differenz:** +15.450,53 € (DRIVE zu hoch)

**Ursache:** Konten 717001, 727001, 727501 sind laut TAG 186 als "zurückgestellt" markiert, wurden aber nicht aus Einsatzwerten ausgeschlossen.

---

## 📊 ANALYSE

### Zurückgestellte Konten (YTD Sep-Dez 2025):

| Konto | Wert | Beschreibung |
|-------|------|--------------|
| 717001 | 6.890,70 € | EW Sonstige Erlöse Neuwagen |
| 727001 | 30.347,00 € | Sonstige Einsatzwerte GW |
| 727501 | -13.917,40 € | GIVIT Garantien GW |
| **Gesamt** | **23.320,30 €** | |

### Vergleich mit GlobalCube:

| Status | Einsatz YTD | Differenz zu GlobalCube |
|--------|-------------|-------------------------|
| **Mit zurückgestellten Konten** | 9.207.314,53 € | **+15.450,53 €** |
| **Ohne zurückgestellte Konten** | 9.183.994,23 € | **-7.869,77 €** |
| **Verbesserung** | -23.320,30 € | **-23.320,30 €** |

**Ergebnis:** ✅ Die Differenz verbessert sich um 7.580,76 €, wenn die zurückgestellten Konten ausgeschlossen werden!

---

## ✅ KORREKTUR

**Implementiert in:**
1. `_berechne_bwa_werte()` - Monatswerte (Zeile 482)
2. `_berechne_bwa_ytd()` - YTD-Werte (Zeile 1035)
3. `get_bwa_v2()` - v2 API Monatswerte (Zeile 1948)
4. `get_bwa_v2()` - v2 API YTD-Werte (Zeile 2329)
5. `_berechne_bereich_werte()` - Bereichswerte (Zeile 1731)

**Logik:**
```sql
AND nominal_account_number NOT IN (743002, 717001, 727001, 727501)
```

**Ausgeschlossene Konten:**
- **743002** - EW Fremdleistungen für Kunden (bereits seit TAG 187)
- **717001** - EW Sonstige Erlöse Neuwagen (neu, TAG 196)
- **727001** - Sonstige Einsatzwerte GW (neu, TAG 196)
- **727501** - GIVIT Garantien GW (neu, TAG 196)

---

## 📊 ERWARTETE ERGEBNISSE

### Einsatz YTD (Sep-Dez 2025):

| Position | Vorher | Nachher | Änderung |
|----------|--------|---------|----------|
| **Einsatz YTD** | 9.207.314,53 € | 9.183.994,23 € | -23.320,30 € |
| **Differenz zu GlobalCube** | +15.450,53 € | -7.869,77 € | **-23.320,30 €** |

### Betriebsergebnis YTD:

| Position | Vorher | Nachher | Änderung |
|----------|--------|---------|----------|
| **DB1 YTD** | 1.411.078,83 € | 1.434.399,13 € | +23.320,30 € |
| **DB3 YTD** | 447.779,84 € | 471.100,14 € | +23.320,30 € |
| **Betriebsergebnis YTD** | -391.157,71 € | -367.837,41 € | **+23.320,30 €** |

---

## 🔍 HISTORISCHER KONTEXT

**TAG 186:**
- Konten 717001, 727001, 727501 wurden als "zurückgestellt" identifiziert
- Dokumentation: `docs/ZURUECKGESTELLT_ERKENNTNIS_TAG186.md`
- Ebene-Zuordnung: "zurückgestellt" in GCStruct/Kontenrahmen/Kontenrahmen.csv

**TAG 196:**
- Analyse bestätigt: Ausschluss verbessert Differenz signifikant
- Korrektur implementiert in allen relevanten Funktionen

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **Service neu starten:** `sudo systemctl restart greiner-portal`
2. ⏳ **YTD-Werte über Web-UI prüfen** (nach Neustart)
3. ⏳ **Verbleibende Differenz analysieren:** -7.869,77 € (DRIVE zu niedrig)
4. ⏳ **Monatswerte prüfen:** Ob die Korrektur auch für Monatswerte wirksam ist

---

## ✅ STATUS

- ✅ Korrektur implementiert (5 Stellen)
- ⏳ Service-Neustart erforderlich
- ⏳ Web-UI-Test nach Neustart
- ⏳ Verbleibende Differenz analysieren
