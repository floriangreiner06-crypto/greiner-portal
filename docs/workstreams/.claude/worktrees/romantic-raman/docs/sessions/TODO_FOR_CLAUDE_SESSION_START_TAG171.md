# TODO für Claude - Session Start TAG 171

## 🚨 KRITISCH: Standort-Filter-Logik konsolidieren

### Problem
Die Standort-Filter-Logik ist **inkonsistent** über verschiedene Dateien hinweg:
- Verschiedene Dateien verwenden unterschiedliche Filter-Methoden
- Landau-Filter ist möglicherweise **falsch** (siehe TAG 170)
- Fehlender Kontext: Mapping zwischen BWA und Locosoft Standorten nicht klar dokumentiert
- **Konsequenz:** Inkonsistente Ergebnisse, schwer nachvollziehbare Fehler

---

## 📋 VORGEWHENSWEISE: Standort-Filter konsistent machen

### Phase 1: Mapping dokumentieren (ERSTE PRIORITÄT)

**Ziel:** Klare Dokumentation der Standort-Zuordnungen in beiden Systemen

#### 1.1 BWA-Standort-Mapping dokumentieren
**Datei:** `docs/STANDORT_MAPPING_BWA.md` (neu erstellen)

**Inhalt:**
```markdown
# Standort-Mapping: BWA (loco_journal_accountings)

## Umsatz (820000-829999)
- Deggendorf: `branch_number = 1`
- Landau: `branch_number = 3`
- Hyundai: `branch_number = 2`

## Einsatz/Kosten (720000-729999, 4xxxxx)
- Deggendorf: Konto-Endziffer (6. Ziffer) = '1'
- Landau: Konto-Endziffer (6. Ziffer) = '2'
- Hyundai: `subsidiary_to_company_ref = 2`

## Firma
- Stellantis: `subsidiary_to_company_ref = 1`
- Hyundai: `subsidiary_to_company_ref = 2`
```

#### 1.2 Locosoft-Standort-Mapping dokumentieren
**Datei:** `docs/STANDORT_MAPPING_LOCOSOFT.md` (neu erstellen)

**Vorgehen:**
1. **Test-Script erstellen:** `scripts/analyse_locosoft_standorte.py`
   - Query: `SELECT DISTINCT out_subsidiary, in_subsidiary, location FROM dealer_vehicles WHERE ...`
   - Query: `SELECT DISTINCT subsidiary FROM orders WHERE ...`
   - Query: `SELECT DISTINCT subsidiary FROM invoices WHERE ...`
   - **Ziel:** Alle verwendeten `subsidiary`-Werte und `location`-Werte identifizieren

2. **Mapping erstellen:**
   ```markdown
   # Standort-Mapping: Locosoft
   
   ## dealer_vehicles
   - Deggendorf Stellantis: `out_subsidiary = 1`, `in_subsidiary = 1`
   - Deggendorf Hyundai: `out_subsidiary = 2`, `in_subsidiary = 2`
   - Landau: `out_subsidiary = ?`, `in_subsidiary = ?` ⚠️ ZU PRÜFEN
   
   ## orders/invoices
   - Deggendorf Stellantis: `subsidiary = 1`
   - Deggendorf Hyundai: `subsidiary = 2`
   - Landau: `subsidiary = ?` ⚠️ ZU PRÜFEN
   ```

3. **Landau speziell prüfen:**
   - Query: `SELECT COUNT(*), out_subsidiary, in_subsidiary FROM dealer_vehicles WHERE location LIKE '%LAN%' GROUP BY out_subsidiary, in_subsidiary`
   - **Ziel:** Welche `subsidiary`-Werte haben Landau-Fahrzeuge?

#### 1.3 Cross-Reference erstellen
**Datei:** `docs/STANDORT_CROSS_REFERENCE.md` (neu erstellen)

**Inhalt:**
```markdown
# Standort Cross-Reference: BWA ↔ Locosoft

| Standort | BWA (branch_number) | BWA (Konto-Endziffer) | Locosoft (subsidiary) | Locosoft (location) |
|----------|---------------------|----------------------|----------------------|---------------------|
| Deggendorf Stellantis | 1 | 1 | 1 | DEGO |
| Deggendorf Hyundai | 2 | - | 2 | DEGH |
| Landau | 3 | 2 | ? | LANO |
```

---

### Phase 2: Zentrale Filter-Funktionen erstellen

**Ziel:** Einheitliche Filter-Funktionen, die von allen Modulen verwendet werden

#### 2.1 BWA-Filter zentralisieren
**Datei:** `api/controlling_api.py` (erweitern)

**Bereits vorhanden:** `build_firma_standort_filter()` ✅

**Ergänzen:**
- Kommentare verbessern
- Dokumentation der Rückgabewerte
- Beispiel-Usage hinzufügen

#### 2.2 Locosoft-Filter zentralisieren
**Datei:** `api/standort_utils.py` (ERWEITERT - ✅ BEREITS ERLEDIGT in TAG 170)

**Funktionen:**
```python
def build_locosoft_standort_filter_verkauf(standort: int, nur_stellantis: bool = False) -> str:
    """
    Baut Standort-Filter für Locosoft dealer_vehicles (Verkäufe).
    
    Args:
        standort: 1=Deggendorf, 2=Hyundai, 3=Landau, 0=Alle
        nur_stellantis: Für standort=1: Nur Stellantis (True) oder beide (False)
    
    Returns:
        SQL WHERE-Clause: "AND out_subsidiary = ..."
    """
    pass

def build_locosoft_standort_filter_bestand(standort: int, nur_stellantis: bool = False) -> str:
    """
    Baut Standort-Filter für Locosoft dealer_vehicles (Bestand).
    
    Args:
        standort: 1=Deggendorf, 2=Hyundai, 3=Landau, 0=Alle
        nur_stellantis: Für standort=1: Nur Stellantis (True) oder beide (False)
    
    Returns:
        SQL WHERE-Clause: "AND in_subsidiary = ..."
    """
    pass

def build_locosoft_standort_filter_orders(standort: int) -> str:
    """
    Baut Standort-Filter für Locosoft orders/invoices.
    
    Args:
        standort: 1=Deggendorf, 2=Hyundai, 3=Landau, 0=Alle
    
    Returns:
        SQL WHERE-Clause: "AND o.subsidiary = ..."
    """
    pass
```

**Status:** ✅ **BEREITS ERLEDIGT in TAG 170**
- Funktionen in `api/standort_utils.py` erstellt:
  - `build_locosoft_filter_verkauf()`
  - `build_locosoft_filter_bestand()`
  - `build_locosoft_filter_orders()`
- ⚠️ **Landau-Filter:** Aktuell `subsidiary=1`, muss noch verifiziert werden

#### 2.3 Alle betroffenen Dateien aktualisieren

**Dateien, die aktualisiert werden müssen:**
1. ✅ `api/gewinnplanung_v2_gw_data.py` - **BEREITS MIGRIERT in TAG 170**
   - Nutzt jetzt `build_locosoft_filter_verkauf()` und `build_locosoft_filter_bestand()`
   - ⚠️ **Landau-Filter:** Muss noch verifiziert werden (nach Phase 1.2)

2. `api/abteilungsleiter_planung_data.py`
   - `_lade_vorjahr_referenz()`: Verwende zentrale Filter-Funktionen
   - `lade_ist_werte_fuer_monat()`: Verwende zentrale Filter-Funktionen

3. `routes/controlling_routes.py`
   - `get_stueckzahlen_locosoft()`: Verwende `build_locosoft_standort_filter_verkauf()`

4. Weitere Dateien nach Bedarf

---

### Phase 3: Tests & Validierung

#### 3.1 Test-Scripts erstellen
1. `scripts/test_standort_filter_bwa.py`
   - Testet alle Standort-Kombinationen für BWA-Filter
   - Vergleicht mit manuellen BWA-Werten

2. `scripts/test_standort_filter_locosoft.py`
   - Testet alle Standort-Kombinationen für Locosoft-Filter
   - Vergleicht Stückzahlen mit manuellen Locosoft-Abfragen

3. `scripts/test_standort_konsistenz.py`
   - Testet, ob BWA- und Locosoft-Filter konsistent sind
   - Beispiel: Deggendorf Stückzahl aus BWA vs. Locosoft

#### 3.2 Validierung
- **Landau speziell:** 
  - Test: Landau DB1 aus BWA vs. Landau Stückzahl aus Locosoft
  - Sollte konsistent sein (gleicher Zeitraum, gleiche Filter)

---

## 📝 KONKRETE AUFGABEN FÜR TAG 171

### Priorität 1 (KRITISCH)
- [x] **Phase 1.2:** ✅ **ERLEDIGT** - Landau `subsidiary`-Werte identifiziert (subsidiary = 3)
- [x] **Phase 2.2:** ✅ **ERLEDIGT** - Filter-Funktionen in `api/standort_utils.py` erstellt
- [x] **Phase 2.3:** ✅ **ERLEDIGT** - Landau-Filter in `api/standort_utils.py` korrigiert
- [ ] **Global Cube Filter klären:** Frage an Global Cube, welche Filter verwendet werden

### Priorität 2 (HOCH)
- [ ] **Phase 1.1:** BWA-Standort-Mapping dokumentieren
- [ ] **Phase 2.3:** Weitere betroffene Dateien aktualisieren
- [ ] **Phase 3.1:** Test-Scripts erstellen

### Priorität 3 (MITTEL)
- [ ] **Phase 3.2:** Validierung durchführen
- [ ] **Phase 2.1:** BWA-Filter-Dokumentation verbessern

---

## 🔍 WICHTIGE HINWEISE

1. ✅ **Landau-Filter korrigiert:** `subsidiary = 3` verifiziert und implementiert (TAG 170)

2. **Konsistenz über Systeme:** BWA und Locosoft müssen konsistent sein:
   - Gleicher Zeitraum
   - Gleiche Standort-Definition
   - Gleiche Fahrzeug-Typen (NW = N+T+V, GW = D+G+L)

3. **Dokumentation ist wichtig:** Ohne klare Dokumentation passieren immer wieder Fehler

4. **Test-first approach:** Bevor Filter geändert werden, Tests erstellen, die die erwarteten Werte validieren

---

## 📚 REFERENZEN

- ✅ **`api/standort_utils.py`** - **SSOT für alle Standort-Filter** (TAG 170)
  - `build_bwa_filter()` - BWA-Filter (Wrapper um `build_firma_standort_filter()`)
  - `build_locosoft_filter_verkauf()` - Locosoft dealer_vehicles (Verkäufe)
  - `build_locosoft_filter_bestand()` - Locosoft dealer_vehicles (Bestand)
  - `build_locosoft_filter_orders()` - Locosoft orders/invoices
- ✅ **`docs/STANDORT_LOGIK_SSOT.md`** - Autoritative Dokumentation (TAG 170)
- ✅ **`docs/MIGRATION_STANDORT_SSOT.md`** - Migrations-Checkliste (TAG 170)
- `api/controlling_api.py`: `build_firma_standort_filter()` (BWA-Filter - wird von `build_bwa_filter()` verwendet)
- ✅ `api/gewinnplanung_v2_gw_data.py`: **MIGRIERT** - nutzt jetzt zentrale Funktionen
- ⚠️ `api/abteilungsleiter_planung_data.py`: `_lade_vorjahr_referenz()` - **NOCH ZU MIGRIEREN**
- ⚠️ `routes/controlling_routes.py`: `get_stueckzahlen_locosoft()` - **NOCH ZU MIGRIEREN**

---

**Ziel:** Konsistente, dokumentierte, testbare Standort-Filter-Logik

---

## 🚨 NEU: Global Cube Filter-Differenz

### Problem
- **DRIVE Gesamtstückzahl:** 1226 Stk. (alle Einträge) = 1223 Stk. (DISTINCT VINs)
- **Global Cube:** 1069 Stk.
- **Differenz:** 154 Stk. (12,6%)

### Analyse (TAG 170)
- Global Cube filtert wahrscheinlich: **DISTINCT VINs mit Preis >= ~6000 €**
- Bester Match: "Alle mit Preis >= 6000 €" = 1068 Stk. (Differenz: nur 1 Stk.)
- DRIVE (Locosoft PR 273): 1226 Stk. deckt sich mit Locosoft

### Offene Frage
**⚠️ KRITISCH:** Frage an Global Cube:
1. Welche Filter verwendet Global Cube genau für die Gesamtstückzahl?
2. Filtert Global Cube nach Preis-Schwellen (z.B. >= 6000 €)?
3. Soll DRIVE die gleichen Filter verwenden, oder ist die aktuelle Logik (alle Fahrzeuge) korrekt?
4. Oder macht Global Cube einen Fehler und erfasst nicht alle Fahrzeuge?

### Status
- ⚠️ **OFFEN** - Warte auf Antwort von Global Cube
- DRIVE-Logik ist konsistent (1226 = Summe der Standorte)
- Locosoft PR 273 bestätigt 1226 Stk.

