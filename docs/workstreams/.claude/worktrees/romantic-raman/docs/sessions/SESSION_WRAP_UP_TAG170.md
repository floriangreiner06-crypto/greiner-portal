# Session Wrap-Up TAG 170

**Datum:** 2026-01-08  
**Session:** GW-Planung V2 - Multi-Standort-Ansicht & Standort-Filter-Probleme

---

## 📋 ZUSAMMENFASSUNG

Diese Session fokussierte sich auf die Implementierung der Multi-Standort-Ansicht für die GW-Planung (KST 20) und die Korrektur von DB1-Werten. Es gab mehrere Probleme mit der Standort-Filter-Logik, insbesondere für Landau.

**Hauptprobleme:**
1. ❌ **Landau-Filter falsch:** Locosoft Standort- und Marken-Logik wurde missachtet
2. ❌ **Kumulierte VJ-Werte fehlten:** Reihenfolge beim Laden der Vorjahreswerte war falsch
3. ❌ **Hyundai VJ-Werte fehlten:** API-Aufruf funktionierte, aber Anzeige hatte Probleme
4. ⚠️ **Mehrere Cursor-Abstürze:** Instabilität der Entwicklungsumgebung

---

## ✅ ERLEDIGTE AUFGABEN

### 1. Multi-Standort-Ansicht für GW-Planung implementiert
- **Neue Route:** `/planung/v2/gw/gesamt` für Gesamtbetrieb-Ansicht
- **Neues Template:** `templates/planung/v2/gw_planung_gesamt.html`
  - Zeigt alle Standorte nebeneinander: Opel DEG, Leapmotor Deg, Hyundai Deg, Landau
  - Kumulierte Spalte am Ende
  - Vorjahreswerte für jeden Standort
- **API erweitert:** `api/gewinnplanung_v2_gw_api.py`
  - `nur_stellantis` Parameter für Standort 1 (Opel DEG vs. Deggendorf gesamt)
  - Gesamtbetrieb-Endpoint (`standort=0`) aggregiert alle Standorte

### 2. DB1-Werte korrigiert
- **Problem:** Opel DEG zeigte falschen DB1 (3.311.559,35 € statt 200.355,90 €)
- **Ursache:** `nur_stellantis` Parameter wurde nicht korrekt verarbeitet
- **Lösung:** API-Datei auf Server aktualisiert, Server neu gestartet
- **Verifizierung:** Test-Script `test_opel_deg_db1.py` bestätigt korrekte Werte

### 3. Kumulierte VJ-Werte implementiert
- **Problem:** Kumulierte Vorjahreswerte wurden nicht angezeigt
- **Ursache:** `anzeigeVorjahre()` wurde aufgerufen, bevor Gesamtbetrieb-Vorjahr geladen wurde
- **Lösung:** Reihenfolge korrigiert: Gesamtbetrieb wird VOR `anzeigeVorjahre()` geladen
- **Ergänzt:** Bruttoertrag pro Fahrzeug und Standzeit für kumulierte VJ-Werte

### 4. BWA-Berechnung verifiziert
- **Test:** `test_gw_db1_august_2025.py` bestätigt:
  - GW DB1 August 2025 (Monat): -116.347,23 € ✅ (DRIVE BWA: -116.347,00 €)
  - GW DB1 YTD (Sep 2024 - Aug 2025): 611.016,12 € ✅ (DRIVE BWA: 611.016,00 €)
- **Ergebnis:** BWA-Berechnung ist korrekt für Gesamtbetrieb

### 5. Standort-Filter SSOT implementiert (KRITISCH)
- **Problem:** Standort-Filter-Logik war verstreut und inkonsistent über verschiedene Dateien
- **Lösung:** Zentrale Filter-Funktionen in `api/standort_utils.py` erstellt
  - `build_bwa_filter()` - Wrapper für BWA-Filter (loco_journal_accountings)
  - `build_locosoft_filter_verkauf()` - Locosoft dealer_vehicles (Verkäufe)
  - `build_locosoft_filter_bestand()` - Locosoft dealer_vehicles (Bestand)
  - `build_locosoft_filter_orders()` - Locosoft orders/invoices
- **Migration:** `api/gewinnplanung_v2_gw_data.py` nutzt jetzt zentrale Funktionen
- **Dokumentation:** `docs/STANDORT_LOGIK_SSOT.md` erstellt (autoritative Quelle)
- **Migrations-Dokumentation:** `docs/MIGRATION_STANDORT_SSOT.md` erstellt

---

## ❌ BEKANNTE PROBLEME

### 1. Landau-Filter falsch ✅ GELÖST
**Problem:** Landau wurde fälschlicherweise mit `subsidiary = 1` gefiltert, was zu falschen Stückzahlen führte (351 statt 185).

**Lösung:** ✅ **KORRIGIERT**
- Analyse-Script `analyse_landau_locosoft.py` erstellt und ausgeführt
- **Ergebnis:** Landau verwendet `subsidiary = 3` (LANO location), nicht `subsidiary = 1`
- Alle Filter-Funktionen in `api/standort_utils.py` aktualisiert
- `api/gewinnplanung_v2_gw_data.py` nutzt jetzt korrekte Filter (via zentrale Funktionen)
- **Verifizierung:** Landau zeigt jetzt korrekte Stückzahl (185 statt 351)

### 2. Standort-Filter-Logik inkonsistent (TEILWEISE GELÖST)
**Problem:** Verschiedene Dateien verwenden unterschiedliche Logik für Standort-Filter:
- `api/controlling_api.py`: BWA-Filter (branch_number, Konto-Endziffer)
- `api/gewinnplanung_v2_gw_data.py`: Locosoft-Filter (out_subsidiary, in_subsidiary) ✅ **MIGRIERT**
- `api/abteilungsleiter_planung_data.py`: Mischung aus beidem ⚠️ **NOCH ZU MIGRIEREN**
- `routes/controlling_routes.py`: location-Filter (DEGO, DEGH, LANO) ⚠️ **NOCH ZU MIGRIEREN**

**Status:**
- ✅ Zentrale Filter-Funktionen erstellt (`api/standort_utils.py`)
- ✅ `api/gewinnplanung_v2_gw_data.py` migriert
- ⚠️ Weitere Dateien müssen noch migriert werden (siehe `docs/MIGRATION_STANDORT_SSOT.md`)

---

## 📁 GEÄNDERTE DATEIEN

### Backend (Python)
1. `api/gewinnplanung_v2_gw_data.py`
   - `lade_vorjahr_gw()`: `nur_stellantis` Parameter hinzugefügt
   - Standort-Filter für Opel DEG (nur Stellantis) vs. Deggendorf (beide)
   - ✅ **MIGRIERT:** Nutzt jetzt zentrale Filter-Funktionen aus `api/standort_utils.py`
   - ⚠️ **Landau-Filter möglicherweise falsch** (muss noch verifiziert werden)

2. `api/gewinnplanung_v2_gw_api.py`
   - `get_vorjahr()`: `nur_stellantis` Query-Parameter unterstützt
   - Gesamtbetrieb-Endpoint (`standort=0`) implementiert

3. `routes/gewinnplanung_v2_routes.py`
   - Neue Route `/planung/v2/gw/gesamt` für Gesamtbetrieb-Ansicht

4. `api/standort_utils.py` (ERWEITERT)
   - ✅ Neue Filter-Funktionen hinzugefügt (BWA + Locosoft)
   - ✅ SSOT für alle Standort-Filter-Logik

### Frontend (Jinja2 Templates)
4. `templates/planung/v2/gw_planung_gesamt.html`
   - Multi-Standort-Tabelle implementiert
   - JavaScript für Vorjahreswerte-Laden korrigiert (Reihenfolge)
   - Kumulierte VJ-Werte ergänzt (Bruttoertrag, Standzeit)

### Scripts (Test/Debug)
5. `scripts/test_gw_db1_august_2025.py` (neu)
6. `scripts/test_opel_deg_db1.py` (neu)
7. `scripts/test_hyundai_vorjahr.py` (neu)
8. `scripts/analyse_landau_locosoft.py` (neu) - Landau-Filter verifiziert
9. `scripts/test_landau_stueck.py` (neu) - Landau-Stückzahl verifiziert
10. `scripts/berechne_gesamt_aller_fahrzeuge.py` (neu) - Gesamtstückzahl-Analyse
11. `scripts/zaehle_vins.py` (neu) - DISTINCT VINs Analyse
12. `scripts/finde_1069_filter.py` (neu) - Global Cube Filter-Analyse
13. `scripts/finde_1069_preis_filter.py` (neu) - Preis-Filter für Global Cube

### Dokumentation
8. `docs/STANDORT_LOGIK_SSOT.md` (neu)
   - Autoritative Quelle für Standort-Filter-Logik
   - BWA- und Locosoft-Filter dokumentiert
   - Bereichs-spezifische Logik erklärt

9. `docs/MIGRATION_STANDORT_SSOT.md` (neu)
   - Checkliste für Migration weiterer Dateien
   - Prioritäten für noch zu migrierende Dateien

---

## 🔍 TECHNISCHE DETAILS

### Standort-Mapping
```
Standort 1 (Deggendorf):
  - Opel DEG (nur Stellantis): nur_stellantis=True → subsidiary=1
  - Deggendorf gesamt: nur_stellantis=False → subsidiary=1 OR subsidiary=2

Standort 2 (Hyundai):
  - Hyundai Deg: subsidiary=2

Standort 3 (Landau):
  - ✅ KORRIGIERT: subsidiary=3 (LANO location) - verifiziert durch Analyse
```

### BWA vs. Locosoft Filter
- **BWA (`loco_journal_accountings`):**
  - Umsatz: `branch_number` (1=DEG, 3=LAN)
  - Einsatz/Kosten: Konto-Endziffer (6. Ziffer: 1=DEG, 2=LAN)
  - Firma: `subsidiary_to_company_ref` (1=Stellantis, 2=Hyundai)

- **Locosoft (`dealer_vehicles`):**
  - Verkäufe: `out_subsidiary` (1=Stellantis, 2=Hyundai, 3=Landau) ✅
  - Bestand: `in_subsidiary` (1=Stellantis, 2=Hyundai, 3=Landau) ✅
  - ✅ **Landau-Zuordnung verifiziert:** `subsidiary = 3` (LANO location)

---

## 📝 HINWEISE FÜR NÄCHSTE SESSION

1. **Standort-Filter-Logik konsolidieren:**
   - Siehe `TODO_FOR_CLAUDE_SESSION_START_TAG171.md` für detaillierte Vorgehensweise
   - Zuerst: Mapping zwischen BWA und Locosoft Standorten dokumentieren
   - Dann: Zentrale Filter-Funktion erstellen

2. **Landau-Filter korrigieren:**
   - Prüfen, welche `subsidiary`-Werte Landau-Fahrzeuge in Locosoft haben
   - Test-Script erstellen, um korrekte Filter zu identifizieren
   - Alle betroffenen Dateien aktualisieren

3. **Stabilität verbessern:**
   - Mehrere Cursor-Abstürze heute - möglicherweise größere Dateien oder komplexe Operationen
   - Bei Problemen: Kleinere, fokussierte Änderungen

---

## 🎯 ERREICHTE ZIELE

✅ Multi-Standort-Ansicht für GW-Planung implementiert  
✅ DB1-Werte für Opel DEG korrigiert  
✅ Kumulierte VJ-Werte angezeigt  
✅ BWA-Berechnung verifiziert (Gesamtbetrieb korrekt)  
✅ **Standort-Filter SSOT implementiert** (zentrale Funktionen + Dokumentation)  
✅ **`api/gewinnplanung_v2_gw_data.py` migriert** (nutzt zentrale Funktionen)  
✅ **Landau-Filter korrigiert** (subsidiary = 3 verifiziert und implementiert)  
✅ **Global Cube Filter analysiert** (wahrscheinlich: DISTINCT VINs mit Preis >= ~6000 €)  

## ⚠️ OFFENE PUNKTE

✅ **Landau-Filter korrigiert** - `subsidiary = 3` verifiziert und implementiert  
⚠️ **Weitere Dateien migrieren** (siehe `docs/MIGRATION_STANDORT_SSOT.md`):
   - `api/abteilungsleiter_planung_data.py` (Priorität 1)
   - `routes/controlling_routes.py` (Priorität 2)

### 3. Global Cube Filter-Differenz (NEU)
**Problem:** Gesamtstückzahl zeigt 1226 Stk. (DRIVE) vs. 1069 Stk. (Global Cube)
- **DRIVE (Locosoft PR 273):** 1226 Stk. (alle Einträge) = 1223 Stk. (DISTINCT VINs)
- **Global Cube:** 1069 Stk.
- **Differenz:** 154 Stk. (12,6%)

**Analyse:**
- Global Cube filtert wahrscheinlich: DISTINCT VINs mit Preis >= ~6000 €
- Bester Match: "Alle mit Preis >= 6000 €" = 1068 Stk. (Differenz: nur 1 Stk.)

**Status:** ⚠️ **OFFEN** - Frage an Global Cube erforderlich
- Welche Filter verwendet Global Cube genau?
- Soll DRIVE die gleichen Filter verwenden?
- Oder ist die aktuelle DRIVE-Logik (alle Fahrzeuge) korrekt?  

---

**Nächste Session:** TAG 171 - Standort-Filter-Logik konsolidieren & Landau korrigieren

