# BWA Analyse Zusammenfassung - TAG 186

**Datum:** 2026-01-13  
**Status:** ✅ Locosoft-Spiegelung validiert | 🔄 Neuer systematischer Ansatz

---

## ✅ WICHTIGE ERKENNTNISSE

### 1. Locosoft-Spiegelung ist KORREKT ✅

**Validierung:**
- ✅ Anzahl Buchungen: Identisch (86.770)
- ✅ Summe posted_value: Identisch (16.776.554.150 Cent)
- ✅ Umsatz (8xxxxx): Identisch (10.603.687,48 €)
- ✅ Einsatz (7xxxxx): Identisch (9.191.864,14 €)
- ✅ Kosten (4xxxxx): Identisch (1.827.403,84 €)
- ✅ Neutral (2xxxxx): Identisch (130.171,89 €)

**Fazit:** Das Problem liegt **NICHT** in der Daten-Spiegelung, sondern in der **Filter-Logik**!

---

### 2. Historische Erfolge

**TAG 177 (August 2025):**
- ✅ **Unternehmensergebnis YTD:** 23,99 € Differenz (fast perfekt!)
- ✅ **Logik:** 411xxx + 489xxx + 410021 aus direkten Kosten ausgeschlossen
- ✅ **Dokumentation:** `docs/BWA_MAPPING_KORREKTUR_TAG182.md`

**TAG 182 (Dezember 2025):**
- ❌ **Betriebsergebnis YTD:** 19.256 € Differenz (massiv)
- ❌ **Logik geändert:** 411xxx + 410021 enthalten, 489xxx ausgeschlossen
- ❌ **Problem:** Warum funktioniert TAG 177 Logik nicht mehr?

---

### 3. Aktuelle Abweichungen (Dezember 2025)

#### Landau:
- **Monat:** Betriebsergebnis +2.355 € (DRIVE zu positiv)
- **YTD:** Betriebsergebnis +19.256 € (DRIVE zu positiv)
- **Hauptproblem:** Variable Kosten zu niedrig (-13.256 € YTD)

#### Gesamtbetrieb:
- **Monat:** Betriebsergebnis +387.242 € (DRIVE zu positiv) 🚨
- **YTD:** Betriebsergebnis -30.652 € (DRIVE zu negativ)
- **Hauptproblem:** Direkte Kosten Monat -189.138 € (99,6% zu niedrig!)

---

## 🎯 NEUER SYSTEMATISCHER ANSATZ

### Phase 1: TAG 177 Logik rekonstruieren ✅

**Ziel:** Die erfolgreiche Logik von August 2025 identifizieren

**Quellen:**
- `docs/BWA_MAPPING_KORREKTUR_TAG182.md`
- `docs/BWA_DIFFERENZ_ANALYSE_TAG182.md`
- Git-History (falls verfügbar)

**Erwartung:** Logik identifiziert, die zu 23,99 € führte

---

### Phase 2: TAG 177 Logik auf Dezember 2025 anwenden

**Ziel:** Prüfen, ob die Logik auch für Dezember 2025 funktioniert

**Vorgehen:**
1. TAG 177 Logik implementieren (411xxx + 489xxx + 410021 ausgeschlossen)
2. Dezember 2025 berechnen
3. Mit GlobalCube vergleichen

**Erwartung:** 
- **Wenn funktioniert:** ~24 € Differenz ✅
- **Wenn nicht:** Konten-Differenz-Analyse erforderlich

---

### Phase 3: Konten-Differenz-Analyse (falls nötig)

**Ziel:** Identifizieren, welche Konten fehlen oder falsch zugeordnet sind

**Vorgehen:**
1. Alle Konten für Dezember 2025 auflisten (Locosoft)
2. Alle Konten für Dezember 2025 auflisten (DRIVE)
3. Differenz identifizieren
4. Kategorisierung prüfen

---

## 📋 NÄCHSTE SCHRITTE

### SOFORT:

1. **TAG 177 Logik rekonstruieren**
   - Aus Dokumentation extrahieren
   - Code-Version identifizieren
   - August 2025 validieren (23,99 €)

2. **TAG 177 Logik auf Dezember 2025 anwenden**
   - Code anpassen
   - Berechnen
   - Mit GlobalCube vergleichen

3. **Ergebnis analysieren**
   - Wenn ~24 €: Problem gelöst! ✅
   - Wenn nicht: Konten-Differenz-Analyse

---

## 💡 HYPOTHESE

**Warum hatte TAG 177 nur 23,99 € Differenz?**

**Mögliche Erklärungen:**
1. ✅ **Richtige Filter-Logik** (411xxx + 489xxx + 410021 ausgeschlossen)
2. ✅ **Konsistente Kategorisierung** (Variable/Direkte/Indirekte)
3. ✅ **Korrekte Standort-Filter** (branch_number, 6. Ziffer)

**Warum funktioniert es nicht für Dezember 2025?**

**Mögliche Ursachen:**
1. ❌ **Logik wurde geändert** (TAG 182: 411xxx + 410021 enthalten)
2. ❌ **Neue Konten** in Dezember 2025?
3. ❌ **Andere Kategorisierung** in GlobalCube?

---

## 🔍 WICHTIGE DOKUMENTATION

### Erfolgreiche Sessions:
- **TAG 177:** 23,99 € Differenz (August 2025) ✅
- **TAG 184:** Excel-Analyse (Landau Variable Kosten erklärt)

### Problem-Sessions:
- **TAG 182:** Logik geändert, aber immer noch Differenzen
- **TAG 186:** Immer noch große Differenzen

---

## 🚀 EMPFOHLENER ANSATZ

**Zurück zu TAG 177 Logik!**

1. ✅ **TAG 177 Logik rekonstruieren**
2. ✅ **Auf Dezember 2025 anwenden**
3. ✅ **Mit GlobalCube vergleichen**
4. ✅ **Wenn ~24 €: Problem gelöst!**
5. ✅ **Wenn nicht: Konten-Differenz-Analyse**

**Vorteil:** Wir wissen, dass TAG 177 Logik funktioniert hat (23,99 €)!

---

*Erstellt: TAG 186 | Autor: Claude AI*
