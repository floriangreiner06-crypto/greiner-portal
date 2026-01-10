# Standort-Filter-Kombinationen Analyse - TAG 177

**Datum:** 2026-01-10  
**Zweck:** Übersicht aller Filterkombinationen und Bezeichnungen vor Zentralisierung

---

## 1. STANDORT-BEZEICHNUNGEN (Verschiedene Varianten)

| Standort-ID | SSOT (standort_utils.py) | stundensatz_kalkulation | planung_routes | gw_planung_gesamt.html | vergleiche_bwa_csv | Verwendung |
|-------------|-------------------------|------------------------|----------------|------------------------|---------------------|------------|
| **1** | **Deggendorf Opel** | Deggendorf | Deggendorf | Opel DEG | Stellantis (DEG+LAN) | JSON-Response, UI-Anzeige |
| **2** | **Deggendorf Hyundai** | Hyundai DEG | Hyundai DEG | Hyundai Deg | Hyundai DEG | JSON-Response, UI-Anzeige |
| **3** | **Landau** | Landau | Landau | Landau | Unbekannt | JSON-Response, UI-Anzeige |

**Inkonsistenzen:**
- Standort 1: "Deggendorf Opel" vs "Deggendorf" vs "Opel DEG" vs "Stellantis (DEG+LAN)"
- Standort 2: "Deggendorf Hyundai" vs "Hyundai DEG" vs "Hyundai Deg"
- Standort 3: Meist "Landau", aber vergleiche_bwa_csv: "Unbekannt"

---

## 2. UI-FILTER-KOMBINATIONEN (Welche Standorte für welche Bereiche)

### 2.1 Abteilungsleiter-Planung (`routes/planung_routes.py`)

| Bereich | Verfügbare Standorte | Filter-Logik | Bemerkung |
|---------|---------------------|--------------|-----------|
| **NW** | 1, 2, 3 (alle) | Alle Standorte | - |
| **GW** | 1, 2, 3 (alle) | Alle Standorte | - |
| **Teile** | 1, 3 (ohne 2) | Nur Deggendorf + Landau | Standort 2 (Hyundai) wird ausgeblendet |
| **Werkstatt** | 1, 3 (ohne 2) | Nur Deggendorf + Landau | Standort 2 (Hyundai) wird ausgeblendet |
| **Sonstige** | 1, 2, 3 (alle) | Alle Standorte | - |

**Besonderheit:** 
- Für Teile/Werkstatt: Standort 2 wird auf Standort 1 gemappt (Zeile 201-202, 632-633)
- Grund: Teile/Werkstatt haben keine separaten Daten für Hyundai DEG

### 2.2 GW-Planung (`templates/planung/v2/gw_planung_gesamt.html`)

| Standort-ID | Name | nur_stellantis | Verwendung |
|-------------|------|----------------|------------|
| **1** | Opel DEG | `true` | Nur Stellantis (subsidiary=1) |
| **1.5** | Leapmotor Deg | - | Neue Marke, kein Vorjahr |
| **2** | Hyundai Deg | `false` | Hyundai (subsidiary=2) |
| **3** | Landau | `false` | Landau (subsidiary=3) |

**Besonderheit:**
- Standort 1.5 (Leapmotor) ist nur in JavaScript definiert, nicht in Backend
- `nur_stellantis` Flag bestimmt SQL-Filter

---

## 3. SQL-FILTER-KOMBINATIONEN (Datenbankabfragen)

### 3.1 Locosoft Filter (`standort_utils.py`)

| Standort | nur_stellantis | Verkaufs-Filter (out_subsidiary) | Bestands-Filter (in_subsidiary) | Orders-Filter (o.subsidiary) |
|----------|----------------|----------------------------------|--------------------------------|------------------------------|
| **1** | `true` | `= 1` | `= 1` | `= 1 OR = 2` (beide) |
| **1** | `false` | `= 1 OR = 2` | `= 1 OR = 2` | `= 1 OR = 2` |
| **2** | - | `= 2` | `= 2` | `= 2` |
| **3** | - | `= 3` | `= 3` | `= 3` |
| **0** | - | (kein Filter) | (kein Filter) | (kein Filter) |

**Inkonsistenz:** Orders-Filter für Standort 1 verwendet immer beide Subsidiaries, unabhängig von `nur_stellantis`

### 3.2 BWA-Filter (`standort_utils.py` → `build_bwa_filter()`)

| Standort-Parameter | Firma | Filter-Logik |
|-------------------|-------|--------------|
| `'1'` (Deggendorf) | `'1'` (Stellantis) | `branch_number = 1 AND subsidiary_to_company_ref = 1` |
| `'deg-both'` | `'0'` (Alle) | Deggendorf beide (subsidiary 1+2) |
| `'2'` (Landau) | `'1'` (Stellantis) | `branch_number = 3 AND subsidiary_to_company_ref = 1` |
| `'0'` (Alle) | `'0'` (Alle) | Kein Filter |

---

## 4. BEREICHS-SPEZIFISCHE FILTER-LOGIK

### 4.1 Abteilungsleiter-Planung (`api/abteilungsleiter_planung_data.py`)

| Bereich | Standort | SQL-Filter | Tabelle |
|---------|----------|------------|---------|
| **Werkstatt/Teile/Sonstige** | 1 | `o.subsidiary = 1 OR = 2` | orders/invoices |
| **Werkstatt/Teile/Sonstige** | 3 | `o.subsidiary = 1` | orders/invoices |
| **NW/GW** | 1 | `out_subsidiary = 1 OR = 2` | dealer_vehicles |
| **NW/GW** | 2 | `out_subsidiary = 2` | dealer_vehicles |
| **NW/GW** | 3 | `out_subsidiary = 1` | dealer_vehicles |

**Inkonsistenz:** 
- Für Werkstatt/Teile: Standort 3 verwendet `subsidiary = 1` (nicht 3!)
- Für NW/GW: Standort 3 verwendet `out_subsidiary = 1` (nicht 3!)

---

## 5. ZUSAMMENFASSUNG DER FILTER-KOMBINATIONEN

### 5.1 UI-Filter (Welche Standorte werden angezeigt)

| Kontext | NW | GW | Teile | Werkstatt | Sonstige |
|---------|----|----|-------|-----------|----------|
| **Abteilungsleiter-Planung** | 1,2,3 | 1,2,3 | 1,3 | 1,3 | 1,2,3 |
| **GW-Planung (JavaScript)** | 1,2,3 | 1,2,3 | - | - | - |
| **Stundensatz-Kalkulation** | 1,2,3 | 1,2,3 | 1,2,3 | 1,2,3 | - |

### 5.2 SQL-Filter (Welche Subsidiaries werden abgefragt)

| Standort | nur_stellantis | Verkaufs | Bestand | Orders | BWA |
|----------|----------------|----------|---------|--------|-----|
| **1** | `true` | 1 | 1 | 1,2 | branch=1, sub=1 |
| **1** | `false` | 1,2 | 1,2 | 1,2 | branch=1, sub=1,2 |
| **2** | - | 2 | 2 | 2 | branch=2, sub=2 |
| **3** | - | 3 | 3 | 3 | branch=3, sub=1 |

---

## 6. IDENTIFIZIERTE PROBLEME

### 6.1 Inkonsistente Bezeichnungen
- **Standort 1:** 4 verschiedene Namen
- **Standort 2:** 3 verschiedene Namen
- **Standort 3:** 2 verschiedene Namen (einer ist "Unbekannt")

### 6.2 Inkonsistente UI-Filter
- **Teile/Werkstatt:** Standort 2 wird ausgeblendet, aber in DB existiert
- **GW-Planung:** Standort 1.5 (Leapmotor) nur in JavaScript, nicht im Backend

### 6.3 Inkonsistente SQL-Filter
- **Orders-Filter:** Standort 1 verwendet immer beide Subsidiaries, unabhängig von `nur_stellantis`
- **Standort 3:** Verwendet `subsidiary = 1` statt `= 3` in einigen Kontexten

### 6.4 Fehlende Zentralisierung
- UI-Filter-Logik ist in `routes/planung_routes.py` hardcoded
- Bezeichnungen sind in mehreren Dateien dupliziert
- Keine zentrale Funktion für "welche Standorte für welchen Bereich"

---

## 7. EMPFOHLENE ZENTRALISIERUNG

### 7.1 Neue Funktionen in `standort_utils.py`

```python
def get_standorte_fuer_bereich(bereich: str) -> Dict[int, str]:
    """
    Gibt verfügbare Standorte für einen Bereich zurück (UI-Filter).
    
    Args:
        bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
    
    Returns:
        {1: 'Deggendorf Opel', 3: 'Landau'}  # für Teile/Werkstatt
        {1: 'Deggendorf Opel', 2: 'Deggendorf Hyundai', 3: 'Landau'}  # für NW/GW/Sonstige
    """
    if bereich in ['Teile', 'Werkstatt']:
        return {1: STANDORT_NAMEN[1], 3: STANDORT_NAMEN[3]}
    else:
        return STANDORT_NAMEN

def get_standort_name_for_display(standort_id: int, context: str = 'default') -> str:
    """
    Gibt Standort-Name für Anzeige zurück (kontextabhängig).
    
    Args:
        standort_id: 1, 2, oder 3
        context: 'default', 'planung', 'gw_planung', 'bwa'
    
    Returns:
        'Deggendorf Opel' (default)
        'Opel DEG' (gw_planung)
        'Deggendorf' (planung)
    """
    # Kontext-spezifische Namen
    pass
```

### 7.2 Migration-Plan

1. **Bezeichnungen zentralisieren:**
   - Alle Dateien auf `STANDORT_NAMEN` oder `BETRIEB_NAMEN` umstellen
   - Kontext-spezifische Namen als Funktion

2. **UI-Filter zentralisieren:**
   - `get_standorte_fuer_bereich()` in `standort_utils.py`
   - `routes/planung_routes.py` verwendet zentrale Funktion

3. **SQL-Filter prüfen:**
   - Orders-Filter Inkonsistenz beheben
   - Standort 3 Filter-Logik vereinheitlichen

---

**Status:** ✅ Analyse abgeschlossen - Bereit für Zentralisierung
