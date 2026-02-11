# Session Wrap-Up TAG 197

**Datum:** 2026-01-XX  
**TAG:** 197  
**Fokus:** CSV-Analyse und AW-Anteil-Berechnung für Leistungsgrad

---

## Was wurde erledigt

### 1. CSV-Analyse für Dezember (Tobias 5007)
- **Script erstellt:** `scripts/analyse_csv_dezember_tobias.py`
  - Analysiert Locosoft CSV-Dateien für Dezember
  - Extrahiert Werte für Tobias (5007)
  - Problem: CSV enthält hauptsächlich Januar-Daten, nicht Dezember

### 2. Konkrete Abweichungen identifiziert
- **Script erstellt:** `scripts/vergleiche_drive_locosoft_dezember.py`
  - Vergleicht DRIVE vs. Locosoft-UI vs. verschiedene Hypothesen
  - **Ergebnisse:**
    - AW-Anteil: DRIVE 2581 Min vs. Locosoft 5106 Min (-49.5% → nach Fix -27.0%)
    - Stmp.Anteil: DRIVE 8536 Min vs. Locosoft 8543 Min (-0.1%) ✅ **Sehr gut!**
    - Leistungsgrad: DRIVE 30.2% → 43.7% (besser, aber noch nicht 59.8%)

### 3. AW-Anteil-Berechnung analysiert
- **7 Hypothesen getestet:**
  1. invoice_date + mechanic_no: -69.0% Abweichung
  2. Proportional zur Stempelzeit: -48.7% Abweichung
  3. ALLE Positionen von Aufträgen mit Stempelung: -27.0% Abweichung ✅ **Beste**
  4. start_time + invoice_date: -70.4% Abweichung
  5. start_time + invoice_date (auch unfakturiert): -69.6% Abweichung
  6. invoice_date + mechanic_no (nur externe): -69.0% Abweichung
  7. ALLE Positionen (ohne invoice_date Filter): -27.0% Abweichung

- **Erkenntnis:** Faktor 1.369 würde passen, deutet aber auf andere Locosoft-Logik hin

### 4. Stmp.Anteil-Berechnung bestätigt
- **75%-Formel für Dezember bestätigt**
- Abweichung: -0.1% ✅ **Korrekt implementiert**

### 5. Implementierung korrigiert
- **Datei:** `api/werkstatt_data.py`
- **Funktion:** `get_aw_verrechnet()`
- **Änderung:** Verwendet jetzt ALLE Positionen von Aufträgen mit Stempelung (ohne Mechaniker-Filter)
- **Ergebnis:** AW-Anteil verbessert von 430.1 AW auf 621.5 AW, Leistungsgrad von 30.2% auf 43.7%

### 6. Locosoft-Support-Frage erstellt
- **Datei:** `docs/LOCOSOFT_SUPPORT_FRAGE_AW_ANTEIL.md`
- Detaillierte Frage mit allen getesteten Hypothesen
- Konkrete Fragen zur Locosoft-Logik
- Technische Details und Beispiel-Szenarien

---

## Geänderte Dateien

### Code-Änderungen
- `api/werkstatt_data.py`
  - `get_aw_verrechnet()`: Logik geändert von proportionaler Verteilung zu ALLE Positionen
  - Kommentare aktualisiert mit Analyse-Ergebnissen

### Neue Scripts
- `scripts/analyse_csv_dezember_tobias.py` - CSV-Analyse für Dezember
- `scripts/vergleiche_drive_locosoft_dezember.py` - Vergleich DRIVE vs. Locosoft

### Neue Dokumentation
- `docs/LOCOSOFT_SUPPORT_FRAGE_AW_ANTEIL.md` - Frage an Locosoft-Support

### Temporäre Analyse-Scripts (nicht committen)
- `scripts/analyse_csv_final.py`
- `scripts/analyse_csv_zeit_strings.py`
- `scripts/analyse_excel_detailliert.py`
- `scripts/analyse_excel_final.py`
- `scripts/analyse_excel_neu.py`
- `scripts/analyse_leistungsgrad_detailliert.py`
- `scripts/analyse_locosoft_csv_komplett.py`
- `scripts/analyse_locosoft_final.py`
- `scripts/analyse_locosoft_korrigiert.py`
- `scripts/analyse_st_anteil_neu.py`
- `scripts/locosoft_analyse_export.csv`

---

## Qualitätscheck

### Redundanzen
- ✅ **Keine doppelten Dateien gefunden**
- ✅ **Keine doppelten Funktionen** (get_aw_verrechnet ist eindeutig)
- ✅ **Mappings korrekt:** Verwendet zentrale Mappings aus `api/standort_utils.py`

### SSOT-Konformität
- ✅ **DB-Verbindungen:** Verwendet `locosoft_session()` aus `api/db_utils.py`
- ✅ **Imports:** Korrekte Imports von zentralen Utilities
- ✅ **Keine lokalen Implementierungen** statt SSOT

### Code-Duplikate
- ⚠️ **Viele Analyse-Scripts** mit ähnlicher Logik (parse_zeit, parse_prozent)
  - **Empfehlung:** Könnten in gemeinsames Utility-Modul ausgelagert werden
  - **Priorität:** Niedrig (nur Analyse-Scripts, nicht produktiver Code)

### Konsistenz
- ✅ **DB-Verbindungen:** PostgreSQL-kompatibel (`%s` statt `?`)
- ✅ **SQL-Syntax:** Korrekt (`true` statt `1`, `CURRENT_DATE` statt `date('now')`)
- ✅ **Error-Handling:** Konsistentes Pattern mit try/except/finally

### Dokumentation
- ✅ **Neue Features dokumentiert:** Locosoft-Support-Frage erstellt
- ✅ **Code-Kommentare:** Erweitert mit Analyse-Ergebnissen

---

## Bekannte Issues

### 1. AW-Anteil-Berechnung noch nicht vollständig korrekt
- **Status:** Verbessert, aber noch -27.0% Abweichung
- **Ursache:** Locosoft-Logik nicht vollständig verstanden
- **Lösung:** Warten auf Antwort von Locosoft-Support
- **Workaround:** Aktuelle Implementierung ist beste Annäherung

### 2. CSV-Analyse findet keine Dezember-Daten
- **Status:** CSV-Datei enthält hauptsächlich Januar-Daten
- **Ursache:** CSV-Datei "01.12.25 - 15.01.26" enthält gemischte Daten
- **Lösung:** Separate CSV-Datei für Dezember verwenden oder Summen-Zeilen analysieren

### 3. Viele temporäre Analyse-Scripts
- **Status:** Nicht produktiver Code
- **Empfehlung:** Könnten in `scripts/archive/` verschoben werden
- **Priorität:** Niedrig

---

## Nächste Schritte

1. **Locosoft-Support kontaktieren** mit erstellter Frage
2. **Antwort abwarten** und Implementierung entsprechend anpassen
3. **Weitere Tests** mit anderen Mechanikern und Zeiträumen
4. **CSV-Analyse verbessern** für bessere Daten-Extraktion

---

## Metriken

- **Dateien geändert:** 1 (api/werkstatt_data.py)
- **Neue Scripts:** 2
- **Neue Dokumentation:** 1
- **Temporäre Analyse-Scripts:** 11
- **Code-Zeilen geändert:** -100 (Code vereinfacht)
- **Hypothesen getestet:** 7
- **Beste Abweichung:** -27.0% (AW-Anteil), -0.1% (Stmp.Anteil)

---

## Git-Status

**Geänderte Dateien:**
- `api/werkstatt_data.py` (modifiziert)

**Neue Dateien (sollten committet werden):**
- `docs/LOCOSOFT_SUPPORT_FRAGE_AW_ANTEIL.md`
- `scripts/analyse_csv_dezember_tobias.py`
- `scripts/vergleiche_drive_locosoft_dezember.py`

**Temporäre Dateien (nicht committen):**
- Alle `scripts/analyse_*.py` (außer den beiden oben)
- `scripts/locosoft_analyse_export.csv`
