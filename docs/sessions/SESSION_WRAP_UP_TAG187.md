# SESSION WRAP-UP TAG 187

**Datum:** 2025-01-XX  
**Status:** Teilweise erfolgreich - BWA-Verbesserungen, aber noch offene Abweichungen

---

## 📋 WAS WURDE ERREICHT

### Hauptthema: BWA-Abweichungen zwischen DRIVE und GlobalCube analysieren und beheben

### Erfolgreich behoben:
1. **✅ 743002 aus Einsatzwerten ausgeschlossen:**
   - Konto 743002 ("EW Fremdleistungen für Kunden") wurde aus den Einsatzwerten ausgeschlossen
   - **Ergebnis:** Monats-Differenz von 3.222,36 € auf 19,56 € reduziert (99,4% Verbesserung)
   - **Änderungen in:**
     - `_berechne_bwa_werte()` (Monat)
     - `_berechne_bwa_ytd()` (YTD)
     - `get_bwa_v2()` (v2 API Route)

2. **✅ Variable Kosten 8910xx korrigiert:**
   - 8910xx Konten werden jetzt korrekt für Hyundai ausgeschlossen (auch in Gesamtbetrieb)
   - **Ergebnis:** Variable Kosten YTD-Differenz von -14.809,53 € auf -103,65 € reduziert (99,3% Verbesserung)

3. **✅ Einsatzwerte-Filter für Landau korrigiert:**
   - Landau Variable Kosten verwenden jetzt korrekten Filter (branch=3 ODER 6. Ziffer='2')
   - **Ergebnis:** Landau Variable Kosten YTD-Differenz von -13.256,47 € auf < 1 € reduziert

### Teilweise erfolgreich:
4. **⚠️ Monat Dezember 2025 - Betriebsergebnis:**
   - DRIVE: -116.147,37 €
   - GlobalCube: -116.248,00 €
   - **Differenz: 100,63 €** (noch nicht erklärt)
   - DB3 und Indirekte Kosten sind fast identisch, aber BE weicht ab
   - **Hypothese:** GlobalCube hat möglicherweise eine zusätzliche Position, die das BE reduziert

5. **⚠️ YTD Betriebsergebnis:**
   - DRIVE: -407.613,15 €
   - GlobalCube: -245.733,00 €
   - **Differenz: -161.880,15 €** (massive Abweichung!)
   - **Problem:** YTD-Berechnung stimmt nicht mit Summe der Monatswerte überein
   - **Hypothese:** YTD-Berechnung verwendet möglicherweise andere Filter oder schließt 743002 nicht aus

### Nicht gelöst:
6. **❌ Betriebsergebnis-Abweichungen:**
   - Monat: 100,63 € Differenz (unerklärt)
   - YTD: -161.880,15 € Differenz (massiv, unerklärt)
   - **Ursache:** Unbekannt - möglicherweise zusätzliche Positionen in GlobalCube oder falsche Filter in YTD

---

## 📁 GEÄNDERTE DATEIEN

### Code-Änderungen:
1. **`api/controlling_api.py`:**
   - Zeile 472-482: 743002 aus Monats-Einsatzwerten ausgeschlossen
   - Zeile 1024-1034: 743002 aus YTD-Einsatzwerten ausgeschlossen
   - Zeile 1934-1942: 743002 aus v2 API Einsatzwerten ausgeschlossen
   - Zeile 498-504: Variable Kosten 8910xx für Gesamtbetrieb korrigiert
   - Zeile 500-502: Landau Variable Kosten Filter korrigiert

### Neue Dokumentation:
- `docs/VARIABLE_KOSTEN_8910XX_KORREKTUR_TAG186.md` (bereits vorhanden)
- Viele Analyse-Dokumente in `docs/` (siehe Git Status)

### Neue Scripts:
- `scripts/komplette_bwa_analyse_gesamtbetrieb.py`
- `scripts/analysiere_einsatz_variable_kosten_detailed.py`
- `scripts/pruefe_filter_logik_doppelzaehlungen.py`
- `scripts/analysiere_einsatz_haben_buchungen.py`
- Weitere Analyse-Scripts (siehe Git Status)

---

## 🔍 QUALITÄTSCHECK

### ✅ Redundanzen:
- **Keine doppelten Dateien gefunden**
- **Keine doppelten Funktionen gefunden**
- 743002-Ausschluss ist an 3 Stellen implementiert (korrekt, da 3 verschiedene Funktionen)

### ✅ SSOT-Konformität:
- **Zentrale Funktionen werden verwendet:**
  - `db_session()` aus `api/db_utils.py`
  - `row_to_dict()`, `rows_to_list()` aus `api/db_utils.py`
  - `get_guv_filter()` aus `api/db_utils.py`
  - `convert_placeholders()` aus `api/db_connection.py`
- **Keine lokalen Implementierungen statt SSOT**

### ✅ Code-Duplikate:
- 743002-Ausschluss ist an 3 Stellen (Monat, YTD, v2 API) - **korrekt**, da unterschiedliche Funktionen
- Filter-Logik ist zentralisiert in `build_firma_standort_filter()`

### ✅ Konsistenz:
- **DB-Verbindungen:** Korrekt verwendet (`db_session()`, `locosoft_session()`)
- **Imports:** Zentrale Utilities werden importiert
- **SQL-Syntax:** PostgreSQL-kompatibel (`%s`, `true`, etc.)
- **Error-Handling:** Konsistentes Pattern

### ⚠️ Bekannte Probleme:
1. **YTD-Berechnung stimmt nicht mit Summe der Monatswerte überein:**
   - YTD Einsatz: 9.223.769,97 € (API)
   - Summe Monate: 9.207.314,53 € (direkt berechnet)
   - **Differenz: 16.455,44 €**
   - **Ursache:** Unbekannt - möglicherweise unterschiedliche Filter oder Datumsbereiche

2. **Betriebsergebnis-Abweichungen:**
   - Monat: 100,63 € (unerklärt)
   - YTD: -161.880,15 € (massiv, unerklärt)
   - **Ursache:** Unbekannt - möglicherweise zusätzliche Positionen in GlobalCube

---

## 🐛 BEKANNTE ISSUES

### Kritisch:
1. **YTD Betriebsergebnis ist massiv falsch:**
   - DRIVE zeigt -407.613,15 €
   - GlobalCube zeigt -245.733,00 €
   - **Differenz: -161.880,15 €**
   - **Status:** Unerklärt, benötigt weitere Analyse

2. **Monat Betriebsergebnis hat 100,63 € Differenz:**
   - DRIVE zeigt -116.147,37 €
   - GlobalCube zeigt -116.248,00 €
   - **Status:** Unerklärt, benötigt weitere Analyse

### Mittel:
3. **Einsatzwerte Monat: 19,56 € Differenz:**
   - Nach Ausschluss von 743002 noch 19,56 € Differenz
   - **Status:** Möglicherweise Rundungsfehler oder weitere kleine Konten

---

## 📊 METRIKEN

### Verbesserungen:
- **Einsatzwerte Monat:** 3.222,36 € → 19,56 € (99,4% Verbesserung)
- **Variable Kosten YTD:** -14.809,53 € → -103,65 € (99,3% Verbesserung)
- **Landau Variable Kosten YTD:** -13.256,47 € → < 1 € (99,9% Verbesserung)

### Verbleibende Abweichungen:
- **Monat BE:** 100,63 € (unerklärt)
- **YTD BE:** -161.880,15 € (massiv, unerklärt)
- **Einsatzwerte Monat:** 19,56 € (möglicherweise Rundungsfehler)

---

## 💡 ERKENNTNISSE

1. **743002 ("EW Fremdleistungen für Kunden") gehört nicht zu normalen Einsatzwerten:**
   - Wert: 3.202,80 € (Dezember 2025)
   - Wurde korrekt ausgeschlossen
   - **Ergebnis:** Massive Verbesserung der Einsatzwerte-Genauigkeit

2. **8910xx Konten sind Erträge, nicht Kosten:**
   - 891001: "VE GW stfr" (Verkaufserlöse Gebrauchtwagen steuerfrei)
   - 891711: "Geldwerter Vorteil (sonstige)" - Gehaltsumwandlungen in Sachbezug (Business Bike)
   - **Ergebnis:** Korrekte Ausschluss-Logik für Hyundai implementiert

3. **YTD-Berechnung hat möglicherweise ein Problem:**
   - YTD-Werte stimmen nicht mit Summe der Monatswerte überein
   - **Mögliche Ursachen:**
     - Unterschiedliche Filter in YTD vs. Monat
     - Unterschiedliche Datumsbereiche
     - 743002 wird in YTD möglicherweise nicht ausgeschlossen (aber Code zeigt es sollte)

---

## 🚀 NÄCHSTE SCHRITTE (für TAG 188)

### Priorität HOCH:
1. **YTD Betriebsergebnis analysieren:**
   - Warum zeigt DRIVE -407.613,15 € statt -245.733,00 €?
   - Prüfen, ob YTD-Berechnung 743002 korrekt ausschließt
   - Prüfen, ob YTD-Berechnung andere Filter verwendet

2. **Monat Betriebsergebnis analysieren:**
   - Warum 100,63 € Differenz?
   - Prüfen, ob GlobalCube zusätzliche Positionen hat
   - Prüfen, ob es Kosten gibt, die wir einschließen, aber GlobalCube ausschließt

### Priorität MITTEL:
3. **Einsatzwerte Monat:**
   - Verbleibende 19,56 € Differenz analysieren
   - Möglicherweise weitere kleine Konten, die ausgeschlossen werden sollten

4. **Dokumentation aufräumen:**
   - Viele Analyse-Dokumente wurden erstellt
   - Entscheiden, welche behalten werden sollen

---

## 📝 WICHTIGE HINWEISE

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

---

## 🔧 TECHNISCHE DETAILS

### Änderungen in `api/controlling_api.py`:

**Zeile 472-482 (Monat Einsatzwerte):**
```python
# TAG187: 743002 ("EW Fremdleistungen für Kunden") ausschließen
AND nominal_account_number != 743002
```

**Zeile 1024-1034 (YTD Einsatzwerte):**
```python
# TAG187: 743002 ("EW Fremdleistungen für Kunden") ausschließen
AND nominal_account_number != 743002
```

**Zeile 1934-1942 (v2 API Einsatzwerte):**
```python
# TAG187: 743002 ("EW Fremdleistungen für Kunden") ausschließen
AND nominal_account_number != 743002
```

---

## ✅ QUALITÄTSCHECK-ERGEBNISSE

### Redundanzen:
- ✅ Keine doppelten Dateien
- ✅ Keine doppelten Funktionen
- ✅ 743002-Ausschluss ist an 3 Stellen (korrekt, da 3 verschiedene Funktionen)

### SSOT-Konformität:
- ✅ Zentrale Funktionen werden verwendet
- ✅ Keine lokalen Implementierungen statt SSOT

### Code-Duplikate:
- ✅ Filter-Logik ist zentralisiert
- ✅ 743002-Ausschluss ist notwendig an 3 Stellen

### Konsistenz:
- ✅ DB-Verbindungen korrekt
- ✅ Imports korrekt
- ✅ SQL-Syntax korrekt
- ✅ Error-Handling konsistent

---

*Erstellt: TAG 187 | Autor: Claude AI*
