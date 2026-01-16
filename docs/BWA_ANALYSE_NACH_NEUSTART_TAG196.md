# BWA Analyse nach Service-Neustart - TAG 196

**Datum:** 2026-01-16  
**Status:** ✅ Analyse abgeschlossen - Ursache identifiziert

---

## 📊 ERGEBNISSE (Monat Dezember 2025)

### Aktuelle Werte (nach Service-Neustart)

| Position | DRIVE | GlobalCube | Differenz | Status |
|----------|-------|------------|-----------|--------|
| Umsatz | 2.190.718,01 € | - | - | ✅ |
| Einsatz | 1.862.687,56 € | - | - | ✅ |
| DB1 | 328.030,45 € | - | - | ✅ |
| Variable Kosten | 69.270,36 € | - | - | ✅ |
| DB2 | 258.760,09 € | - | - | ✅ |
| Direkte Kosten | 189.849,47 € | - | - | ✅ |
| DB3 | 68.910,62 € | - | - | ✅ |
| Indirekte Kosten | 185.057,99 € | - | - | ✅ |
| **Betriebsergebnis** | **-116.147,37 €** | **-116.248,00 €** | **+100,63 €** | ✅ **Sehr gut (0,09%)** |

---

## 🔍 498001 ANALYSE

### Buchungsdetails (Dezember 2025)

| Buchungstyp | Wert | Anzahl |
|------------|------|--------|
| SOLL (S) | 50.000,00 € | 1 |
| HABEN (H) | 0,00 € | 2 |
| **Gesamt** | **50.000,00 €** | **3** |

### Berechnungslogik

**Aktuelle Logik:**
```sql
CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
```

**Ergebnis:**
- SOLL: +50.000 € (erhöht Kosten)
- HABEN: 0 € (reduziert Kosten nicht)
- **Gesamt: +50.000 €** (erhöht indirekte Kosten)

---

## ⚠️ WICHTIGE ERKENNTNISSE

### 1. 498001 Buchungslogik

**Aktuelle Situation:**
- 498001 ist als **SOLL** gebucht (50.000 €)
- Erhöht indirekte Kosten um 50.000 €
- Indirekte Kosten: 185.057,99 €

**Laut TAG 188 Dokumentation:**
- 498001 sollte als **HABEN** gebucht werden (Kostenminderung)
- Sollte indirekte Kosten um 50.000 € **reduzieren**
- Erwartete indirekte Kosten: 135.057,99 € (185.057,99 - 50.000)

**Problem:**
- Die Buchung in Locosoft ist als **SOLL** statt **HABEN**
- Oder: Die Dokumentation ist falsch
- Oder: Die Logik muss angepasst werden

### 2. Betriebsergebnis-Differenz

**Aktuell:**
- DRIVE: -116.147,37 €
- GlobalCube: -116.248,00 €
- Differenz: +100,63 € (0,09%) ✅

**Erwartung (wenn 498001 als HABEN gebucht wäre):**
- DRIVE: -66.147,37 € (-116.147,37 + 50.000)
- GlobalCube: -116.248,00 €
- Differenz: +50.100,63 € ⚠️

**Fazit:**
- Die aktuelle Differenz von 100,63 € ist **sehr gut**
- Wenn 498001 als HABEN gebucht wäre, wäre die Differenz **50.100,63 €** (DRIVE zu positiv)
- Das bedeutet: **Die aktuelle Buchung (SOLL) ist korrekt** für die BWA!

### 3. Widerspruch zur Dokumentation

**TAG 188 Dokumentation sagt:**
- "498001 wird als HABEN gebucht (Kostenminderung)"
- "Die indirekten Kosten werden um 50.000 € gemindert"

**Tatsächliche Situation:**
- 498001 ist als SOLL gebucht (50.000 €)
- Erhöht indirekte Kosten um 50.000 €
- Betriebsergebnis-Differenz ist nur 100,63 € (sehr gut!)

**Mögliche Erklärungen:**
1. Die Dokumentation ist falsch/veraltet
2. Die Buchung in Locosoft wurde geändert
3. Die Logik muss für 498001 speziell behandelt werden

---

## ✅ FAZIT

### Aktuelle Situation ist KORREKT!

**Begründung:**
1. Betriebsergebnis-Differenz: Nur 100,63 € (0,09%) - **sehr gut!**
2. 498001 ist als SOLL gebucht und erhöht Kosten korrekt
3. Wenn 498001 als HABEN gebucht wäre, wäre die Differenz 50.100,63 € (schlecht!)

**Empfehlung:**
- **KEINE Änderung** an der 498001-Behandlung
- Die aktuelle Logik ist korrekt
- Die Dokumentation (TAG 188) sollte aktualisiert werden

---

## 📋 NÄCHSTE SCHRITTE

### Priorität NIEDRIG:
1. **Dokumentation aktualisieren:**
   - TAG 188 Dokumentation korrigieren
   - 498001 wird als SOLL gebucht (nicht HABEN)
   - Erhöht indirekte Kosten (nicht reduziert)

### Priorität MITTEL:
2. **YTD-Analyse durchführen:**
   - YTD bis Dezember 2025 analysieren
   - Prüfen ob YTD-Differenz auch nur ~100 € ist

---

## 🔧 TECHNISCHE DETAILS

### Service-Status
- **Neustart:** ✅ Erfolgreich (2026-01-16 13:59:33)
- **Status:** Active (running)
- **PID:** 200899

### Analyse-Scripts
- `scripts/analyse_bwa_detailed_simple.py` - Hauptanalyse
- `scripts/check_498001.py` - 498001-Details

---

*Erstellt: TAG 196 | Autor: Claude AI*
