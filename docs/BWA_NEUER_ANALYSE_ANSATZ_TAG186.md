# BWA Neuer Analyse-Ansatz - TAG 186

**Datum:** 2026-01-13  
**Status:** 🔄 Systematischer Neustart

---

## 🎯 PROBLEM-ZUSAMMENFASSUNG

Wir drehen uns seit mehreren Sessions im Kreis:
- **TAG 177 (August 2025):** 23,99 € Differenz ✅ (fast perfekt!)
- **TAG 182 (Dezember 2025):** 19.256 € Differenz ❌ (massiv)
- **TAG 184:** Excel-Analysen, aber keine Lösung
- **TAG 186:** Immer noch große Differenzen

**Kernfrage:** Warum hatten wir bei August 2025 nur 23,99 € Differenz, aber bei Dezember 2025 19.256 €?

---

## 💡 NEUER SYSTEMATISCHER ANSATZ

### Phase 1: Locosoft-Spiegelung validieren

**Frage:** Haben wir ALLE Daten aus Locosoft PostgreSQL?

**Prüfungen:**
1. ✅ **Anzahl Buchungen:** Locosoft vs. DRIVE `loco_journal_accountings`
2. ✅ **Zeitraum:** Vollständigkeit der Daten (Sep-Dez 2025)
3. ✅ **Konten:** Alle Konten vorhanden?
4. ✅ **Beträge:** Summen identisch?

**Script:** `scripts/validiere_locosoft_spiegelung.py`

---

### Phase 2: Rohdaten-Vergleich (ohne Filter)

**Frage:** Stimmen die Rohdaten überein?

**Vergleich:**
- **Locosoft PostgreSQL:** Direkte Abfrage `journal_accountings`
- **DRIVE PostgreSQL:** Abfrage `loco_journal_accountings`
- **GlobalCube:** Referenz-Werte aus Screenshots

**Prüfungen:**
1. Umsatz (8xxxxx): Summe identisch?
2. Einsatz (7xxxxx): Summe identisch?
3. Kosten (4xxxxx): Summe identisch?
4. Neutral (2xxxxx): Summe identisch?

**Script:** `scripts/vergleiche_rohdaten_locosoft_drive.py`

---

### Phase 3: Filter-Logik validieren (August 2025)

**Frage:** Welche Filter-Logik führte zu 23,99 € Differenz?

**Rekonstruktion:**
1. ✅ **TAG 177 Logik identifizieren** (aus Dokumentation)
2. ✅ **August 2025 mit TAG 177 Logik berechnen**
3. ✅ **Mit GlobalCube August 2025 vergleichen**
4. ✅ **Bestätigen: 23,99 € Differenz**

**Erkenntnis:** Diese Logik war korrekt!

---

### Phase 4: Filter-Logik auf Dezember 2025 anwenden

**Frage:** Warum funktioniert TAG 177 Logik nicht für Dezember 2025?

**Vorgehen:**
1. ✅ **TAG 177 Logik auf Dezember 2025 anwenden**
2. ✅ **Mit GlobalCube Dezember 2025 vergleichen**
3. ✅ **Differenz analysieren**
4. ✅ **Unterschiede identifizieren**

**Mögliche Ursachen:**
- Neue Konten in Dezember 2025?
- Andere Kategorisierung?
- Filter-Logik geändert?

---

### Phase 5: Konten-Differenz-Analyse

**Frage:** Welche Konten fehlen oder sind falsch zugeordnet?

**Vorgehen:**
1. ✅ **Alle Konten für Dezember 2025 auflisten** (Locosoft)
2. ✅ **Alle Konten für Dezember 2025 auflisten** (DRIVE)
3. ✅ **Vergleichen:** Welche Konten fehlen?
4. ✅ **Kategorisierung prüfen:** Variable/Direkte/Indirekte

**Script:** `scripts/analysiere_konten_differenz.py`

---

## 🔍 WICHTIGE ERKENNTNISSE AUS VORHERIGEN SESSIONS

### TAG 177 (August 2025) - ERFOLG ✅

**Logik:**
- Direkte Kosten: 411xxx + 489xxx + 410021 **AUSGESCHLOSSEN**
- Indirekte Kosten: 8910xx **AUSGESCHLOSSEN**

**Ergebnis:**
- Unternehmensergebnis YTD: 23,99 € Differenz ✅

**Dokumentation:**
- `docs/BWA_MAPPING_KORREKTUR_TAG182.md`
- `docs/BWA_DIFFERENZ_ANALYSE_TAG182.md`

---

### TAG 182 (Dezember 2025) - PROBLEM ❌

**Änderungen:**
- Direkte Kosten: 411xxx + 410021 **ENTHALTEN**, 489xxx **AUSGESCHLOSSEN**
- Indirekte Kosten: 8910xx **AUSGESCHLOSSEN** (unverändert)

**Ergebnis:**
- Betriebsergebnis YTD: 19.256 € Differenz ❌

**Problem:** Warum funktioniert TAG 177 Logik nicht mehr?

---

### TAG 184 (Excel-Analyse)

**Erkenntnisse:**
- Excel "Fertigmachen" summiert DEG + Landau (alle branches)
- DRIVE Filter ist korrekt (nur Landau)
- Excel zeigt falsche Werte für Landau Variable Kosten

**Fazit:** Excel ist nicht die Referenz, sondern GlobalCube Screenshots!

---

## 🚀 NEUER ANSATZ - SCHRITT FÜR SCHRITT

### Schritt 1: Locosoft-Spiegelung validieren

**Ziel:** Sicherstellen, dass alle Daten korrekt gespiegelt werden

**Prüfungen:**
```sql
-- Locosoft PostgreSQL
SELECT COUNT(*), SUM(posted_value), MIN(accounting_date), MAX(accounting_date)
FROM journal_accountings
WHERE accounting_date >= '2025-09-01' AND accounting_date < '2026-01-01';

-- DRIVE PostgreSQL
SELECT COUNT(*), SUM(posted_value), MIN(accounting_date), MAX(accounting_date)
FROM loco_journal_accountings
WHERE accounting_date >= '2025-09-01' AND accounting_date < '2026-01-01';
```

**Erwartung:** Identische Werte!

---

### Schritt 2: Rohdaten-Vergleich (ohne Filter)

**Ziel:** Prüfen, ob die Rohdaten übereinstimmen

**Vergleich:**
- Umsatz (8xxxxx): Locosoft vs. DRIVE
- Einsatz (7xxxxx): Locosoft vs. DRIVE
- Kosten (4xxxxx): Locosoft vs. DRIVE

**Erwartung:** Identische Summen!

---

### Schritt 3: TAG 177 Logik rekonstruieren

**Ziel:** Die erfolgreiche Logik von August 2025 identifizieren

**Quellen:**
- `docs/BWA_MAPPING_KORREKTUR_TAG182.md`
- `docs/BWA_DIFFERENZ_ANALYSE_TAG182.md`
- Code-Version von TAG 177 (Git-History?)

**Erwartung:** Logik identifiziert, die zu 23,99 € führte

---

### Schritt 4: TAG 177 Logik auf Dezember 2025 anwenden

**Ziel:** Prüfen, ob die Logik auch für Dezember 2025 funktioniert

**Vorgehen:**
1. TAG 177 Logik implementieren
2. Dezember 2025 berechnen
3. Mit GlobalCube vergleichen

**Erwartung:** Entweder funktioniert es (23,99 € Differenz) oder wir sehen, was sich geändert hat

---

### Schritt 5: Konten-Differenz-Analyse

**Ziel:** Identifizieren, welche Konten fehlen oder falsch zugeordnet sind

**Vorgehen:**
1. Alle Konten für Dezember 2025 auflisten (Locosoft)
2. Alle Konten für Dezember 2025 auflisten (DRIVE)
3. Differenz identifizieren
4. Kategorisierung prüfen

---

## 📋 CHECKLISTE

### Phase 1: Locosoft-Spiegelung ✅
- [ ] Anzahl Buchungen vergleichen
- [ ] Zeitraum vollständig?
- [ ] Summen identisch?
- [ ] Alle Konten vorhanden?

### Phase 2: Rohdaten-Vergleich ✅
- [ ] Umsatz identisch?
- [ ] Einsatz identisch?
- [ ] Kosten identisch?
- [ ] Neutral identisch?

### Phase 3: TAG 177 Logik ✅
- [ ] Logik identifiziert
- [ ] August 2025 validiert (23,99 €)
- [ ] Dokumentation vorhanden

### Phase 4: Dezember 2025 mit TAG 177 ✅
- [ ] TAG 177 Logik angewendet
- [ ] Mit GlobalCube verglichen
- [ ] Differenz analysiert

### Phase 5: Konten-Analyse ✅
- [ ] Alle Konten aufgelistet
- [ ] Differenzen identifiziert
- [ ] Kategorisierung geprüft

---

## 💡 ERWARTETE ERGEBNISSE

**Wenn Locosoft-Spiegelung korrekt:**
- ✅ Rohdaten identisch
- ✅ Filter-Logik ist das Problem

**Wenn Locosoft-Spiegelung fehlerhaft:**
- ❌ Rohdaten unterschiedlich
- ❌ Spiegelung muss korrigiert werden

**Wenn TAG 177 Logik funktioniert:**
- ✅ Dezember 2025: ~24 € Differenz
- ✅ Problem gelöst!

**Wenn TAG 177 Logik nicht funktioniert:**
- ❌ Konten-Differenz-Analyse erforderlich
- ❌ Neue Konten oder geänderte Kategorisierung

---

## 🎯 NÄCHSTER SCHRITT

**SOFORT:** Locosoft-Spiegelung validieren!

**Script erstellen:** `scripts/validiere_locosoft_spiegelung.py`

**Prüfungen:**
1. Anzahl Buchungen
2. Summen
3. Zeitraum
4. Konten

**Erwartung:** Identische Werte zwischen Locosoft PostgreSQL und DRIVE PostgreSQL!

---

*Erstellt: TAG 186 | Autor: Claude AI*
