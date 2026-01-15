# TODO für Claude - Session Start TAG 188

**Datum:** Nach TAG 187  
**Status:** Kritische BWA-Abweichungen müssen behoben werden

---

## 📋 ÜBERGABE VON TAG 187

### Was wurde erreicht:
- ✅ 743002 aus Einsatzwerten ausgeschlossen (99,4% Verbesserung)
- ✅ Variable Kosten 8910xx korrigiert (99,3% Verbesserung)
- ✅ Landau Variable Kosten korrigiert (99,9% Verbesserung)
- ⚠️ Betriebsergebnis-Abweichungen bleiben bestehen (kritisch!)

### Wichtigste Änderungen:
1. **743002-Ausschluss:**
   - Konto 743002 ("EW Fremdleistungen für Kunden") wird jetzt aus Einsatzwerten ausgeschlossen
   - Implementiert in: `_berechne_bwa_werte()`, `_berechne_bwa_ytd()`, `get_bwa_v2()`
   - **Ergebnis:** Einsatzwerte Monat von 3.222,36 € auf 19,56 € Differenz reduziert

2. **Variable Kosten 8910xx:**
   - 8910xx Konten werden jetzt korrekt für Hyundai ausgeschlossen (auch in Gesamtbetrieb)
   - **Ergebnis:** Variable Kosten YTD von -14.809,53 € auf -103,65 € Differenz reduziert

3. **Landau Variable Kosten:**
   - Filter korrigiert (branch=3 ODER 6. Ziffer='2')
   - **Ergebnis:** Landau Variable Kosten YTD von -13.256,47 € auf < 1 € Differenz reduziert

---

## 🚨 KRITISCHE PROBLEME (MUSS BEHOBEN WERDEN)

### Priorität KRITISCH:
1. **YTD Betriebsergebnis ist massiv falsch:**
   - **DRIVE zeigt:** -407.613,15 €
   - **GlobalCube zeigt:** -245.733,00 €
   - **Differenz: -161.880,15 €** (massiv!)
   - **Status:** Unerklärt, benötigt sofortige Analyse
   - **Mögliche Ursachen:**
     - YTD-Berechnung verwendet andere Filter
     - 743002 wird in YTD möglicherweise nicht ausgeschlossen (aber Code zeigt es sollte)
     - YTD-Berechnung stimmt nicht mit Summe der Monatswerte überein
   - **Nächste Schritte:**
     - [ ] Prüfen, ob YTD-Berechnung 743002 korrekt ausschließt
     - [ ] Prüfen, ob YTD-Berechnung andere Filter verwendet
     - [ ] YTD-Werte mit Summe der Monatswerte vergleichen
     - [ ] Direkte DB-Abfrage für YTD-Zeitraum durchführen

2. **Monat Betriebsergebnis hat 100,63 € Differenz:**
   - **DRIVE zeigt:** -116.147,37 €
   - **GlobalCube zeigt:** -116.248,00 €
   - **Differenz: 100,63 €** (unerklärt)
   - **Status:** Unerklärt, benötigt Analyse
   - **Problem:** DB3 und Indirekte Kosten sind fast identisch, aber BE weicht ab
   - **Mögliche Ursachen:**
     - GlobalCube hat zusätzliche Positionen, die das BE reduzieren
     - GlobalCube schließt bestimmte Kosten aus, die wir einschließen
     - GlobalCube hat zusätzliche Erträge, die wir nicht haben
   - **Nächste Schritte:**
     - [ ] Prüfen, ob GlobalCube zusätzliche Positionen im BE hat
     - [ ] Prüfen, ob es Kosten gibt, die wir einschließen, aber GlobalCube ausschließt
     - [ ] Prüfen, ob es Erträge gibt, die GlobalCube hat, aber wir nicht

### Priorität HOCH:
3. **Einsatzwerte Monat: 19,56 € Differenz:**
   - Nach Ausschluss von 743002 noch 19,56 € Differenz
   - **Status:** Möglicherweise Rundungsfehler oder weitere kleine Konten
   - **Nächste Schritte:**
     - [ ] Prüfen, ob es weitere kleine Konten gibt, die ausgeschlossen werden sollten
     - [ ] Prüfen, ob es Rundungsfehler gibt

---

## ⏳ ZU PRÜFEN BEI SESSION-START

### Priorität KRITISCH:
1. **YTD Betriebsergebnis prüfen:**
   - [ ] API-Werte abrufen: `http://localhost:5000/api/controlling/bwa/v2?monat=12&jahr=2025&firma=0&standort=0`
   - [ ] YTD BE-Wert prüfen (sollte -245.733,00 € sein, nicht -407.613,15 €)
   - [ ] YTD-Berechnung mit direkter DB-Abfrage vergleichen
   - [ ] Prüfen, ob 743002 in YTD korrekt ausgeschlossen wird

2. **Monat Betriebsergebnis prüfen:**
   - [ ] API-Werte abrufen (sollte -116.248,00 € sein, nicht -116.147,37 €)
   - [ ] DB3 und Indirekte Kosten prüfen (sind fast identisch, aber BE weicht ab)
   - [ ] Prüfen, ob es zusätzliche Positionen gibt

### Priorität MITTEL:
3. **Einsatzwerte Monat:**
   - [ ] Verbleibende 19,56 € Differenz analysieren
   - [ ] Prüfen, ob es weitere kleine Konten gibt

---

## 🔍 ANALYSE-SCHRITTE

### Für YTD Betriebsergebnis:
1. **YTD-Berechnung prüfen:**
   ```python
   # Prüfe, ob YTD-Berechnung 743002 ausschließt
   # Prüfe, ob YTD-Berechnung andere Filter verwendet
   # Vergleiche YTD-Werte mit Summe der Monatswerte
   ```

2. **Direkte DB-Abfrage:**
   ```sql
   -- YTD-Zeitraum: 2025-09-01 bis 2026-01-01
   -- Prüfe Einsatzwerte mit und ohne 743002
   -- Prüfe alle Kosten-Kategorien
   ```

3. **Monatswerte summieren:**
   ```python
   # Summiere Monatswerte September-Dezember 2025
   # Vergleiche mit YTD-Werten
   # Identifiziere Differenzen
   ```

### Für Monat Betriebsergebnis:
1. **DB3 und Indirekte Kosten prüfen:**
   ```python
   # DB3: 68.910,62 € (DRIVE) vs. 68.911,00 € (GlobalCube) = -0,38 € OK
   # Indirekte: 185.057,99 € (DRIVE) vs. 185.058,00 € (GlobalCube) = -0,01 € OK
   # BE: -116.147,37 € (DRIVE) vs. -116.248,00 € (GlobalCube) = 100,63 € FEHLER
   # → Problem: BE weicht ab, obwohl DB3 und Indirekte fast identisch sind
   ```

2. **Zusätzliche Positionen suchen:**
   ```python
   # Prüfe, ob GlobalCube zusätzliche Kosten hat
   # Prüfe, ob GlobalCube zusätzliche Erträge hat
   # Prüfe, ob es Kosten gibt, die wir einschließen, aber GlobalCube ausschließt
   ```

---

## 📁 WICHTIGE DATEIEN

### Geänderte Dateien (TAG 187):
- `api/controlling_api.py` - 743002-Ausschluss in 3 Funktionen

### Analyse-Scripts (neu erstellt):
- `scripts/komplette_bwa_analyse_gesamtbetrieb.py`
- `scripts/analysiere_einsatz_variable_kosten_detailed.py`
- `scripts/pruefe_filter_logik_doppelzaehlungen.py`
- `scripts/analysiere_einsatz_haben_buchungen.py`

### Dokumentation (neu erstellt):
- Viele Analyse-Dokumente in `docs/` (siehe Git Status)
- Entscheiden, welche behalten werden sollen

---

## 💡 ERINNERUNGEN

1. **743002-Ausschluss:**
   - Wurde in 3 Funktionen implementiert (Monat, YTD, v2 API)
   - **WICHTIG:** Bei zukünftigen Änderungen alle 3 Stellen synchronisieren!

2. **YTD-Berechnung:**
   - Verwendet abweichendes Wirtschaftsjahr (Start: 1. September)
   - **WICHTIG:** Prüfen, ob Filter korrekt angewendet werden

3. **Betriebsergebnis:**
   - Berechnung: BE = DB3 - Indirekte Kosten
   - **Problem:** DB3 und Indirekte sind fast identisch, aber BE weicht ab
   - **Mögliche Ursache:** GlobalCube hat zusätzliche Positionen

4. **Server-Neustart:**
   - Nach Code-Änderungen: `sudo systemctl restart greiner-portal`
   - Passwort: `OHL.greiner2025` (siehe CLAUDE.md)

---

## 🎯 ZIELE FÜR TAG 188

### Muss erreicht werden:
1. ✅ YTD Betriebsergebnis korrigieren (-161.880,15 € Differenz beheben)
2. ✅ Monat Betriebsergebnis analysieren (100,63 € Differenz erklären)

### Sollte erreicht werden:
3. ⚠️ Einsatzwerte Monat: Verbleibende 19,56 € Differenz analysieren
4. ⚠️ Dokumentation aufräumen (viele Analyse-Dokumente)

---

## 📊 AKTUELLE METRIKEN

### Verbesserungen (TAG 187):
- **Einsatzwerte Monat:** 3.222,36 € → 19,56 € (99,4% Verbesserung) ✅
- **Variable Kosten YTD:** -14.809,53 € → -103,65 € (99,3% Verbesserung) ✅
- **Landau Variable Kosten YTD:** -13.256,47 € → < 1 € (99,9% Verbesserung) ✅

### Verbleibende Abweichungen:
- **Monat BE:** 100,63 € (unerklärt) 🚨
- **YTD BE:** -161.880,15 € (massiv, unerklärt) 🚨
- **Einsatzwerte Monat:** 19,56 € (möglicherweise Rundungsfehler) ⚠️

---

*Erstellt: TAG 187 | Autor: Claude AI*
