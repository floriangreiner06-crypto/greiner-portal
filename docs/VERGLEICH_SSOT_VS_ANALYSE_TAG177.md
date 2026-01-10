# Vergleich: STANDORT_LOGIK_SSOT.md vs. STANDORT_FILTER_ANALYSE_TAG177.md

**Datum:** 2026-01-10  
**Zweck:** Identifikation von Inkonsistenzen zwischen SSOT-Dokumentation und tatsächlichem Code

---

## ✅ ÜBEREINSTIMMUNGEN

### 1. Standort-Definitionen (Grundlagen)
| Standort | SSOT | Analyse | Status |
|----------|------|---------|--------|
| **1** | Deggendorf Opel, subsidiary=1 | Deggendorf Opel | ✅ Konsistent |
| **2** | Deggendorf Hyundai, subsidiary=2 | Deggendorf Hyundai | ✅ Konsistent |
| **3** | Landau, subsidiary=3 ✅ (verifiziert) | Landau, subsidiary=3 | ✅ Konsistent |

### 2. SQL-Filter-Funktionen
- ✅ Beide dokumentieren `build_locosoft_filter_*()` Funktionen
- ✅ Beide dokumentieren `build_bwa_filter()` Funktion
- ✅ Beide verwenden zentrale Funktionen aus `standort_utils.py`

### 3. Bereichs-Logik (Grundsätze)
- ✅ Werkstatt/Teile: Keine Marken-Unterscheidung
- ✅ NW/GW: Firma + Standort Filterung

---

## ❌ KRITISCHE INKONSISTENZEN / BUGS

### 1. 🔴 KRITISCH: `abteilungsleiter_planung_data.py` - Standort 3 Filter FALSCH!

**SSOT-Dokumentation sagt:**
> Landau = subsidiary = 3 ✅ (VERIFIZIERT durch `scripts/analyse_landau_locosoft.py`)

**Tatsächlicher Code (`abteilungsleiter_planung_data.py`):**

| Zeile | Bereich | Standort | Code | SSOT sagt | Status |
|-------|---------|----------|------|-----------|--------|
| 1130 | Werkstatt/Teile | 3 | `o.subsidiary = 1` | `o.subsidiary = 3` | ❌ **BUG!** |
| 1141 | NW/GW | 3 | `out_subsidiary = 1` | `out_subsidiary = 3` | ❌ **BUG!** |
| 1270 | NW/GW | 3 | `out_subsidiary = 1` | `out_subsidiary = 3` | ❌ **BUG!** |
| 1308 | Standzeit | 3 | `out_subsidiary = 1` | `out_subsidiary = 3` | ❌ **BUG!** |
| 1390 | Werkstatt | 3 | `o.subsidiary = 1` | `o.subsidiary = 3` | ❌ **BUG!** |

**Kommentar im Code (falsch!):**
```python
# Zeile 1141: subsidiary_filter = "AND out_subsidiary = 1"  # Landau ist auch subsidiary 1
```

**Problem:** 
- Code verwendet `subsidiary = 1` für Landau
- SSOT sagt: Landau = `subsidiary = 3` (verifiziert!)
- **Das ist ein BUG - liefert falsche Daten für Landau!**

**Impact:**
- Abteilungsleiter-Planung zeigt falsche Daten für Landau
- Landau-Daten werden mit Deggendorf-Daten vermischt

---

### 2. ⚠️ Orders-Filter: Kein `nur_stellantis` Parameter

**SSOT-Dokumentation:**
> `build_locosoft_filter_orders(standort=1)` = beide Subsidiaries (1,2)  
> Kein `nur_stellantis` Parameter vorhanden

**Analyse zeigt:**
- Orders-Filter verwendet immer beide Subsidiaries für Standort 1
- Keine Möglichkeit, nur Stellantis zu filtern

**Frage:** Ist das gewollt oder ein Design-Problem?

**Vergleich mit anderen Filtern:**
- `build_locosoft_filter_verkauf()` hat `nur_stellantis` Parameter
- `build_locosoft_filter_bestand()` hat `nur_stellantis` Parameter
- `build_locosoft_filter_orders()` hat **KEINEN** `nur_stellantis` Parameter

**Mögliche Inkonsistenz:** Sollte Orders-Filter auch `nur_stellantis` unterstützen?

---

### 3. ⚠️ UI-Filter nicht in SSOT dokumentiert

**SSOT-Dokumentation:**
- Dokumentiert nur SQL-Filter (Datenbankabfragen)
- UI-Filter (welche Standorte in Dropdowns angezeigt werden) fehlt

**Analyse zeigt:**
- **Abteilungsleiter-Planung:** Teile/Werkstatt zeigen nur Standort 1 und 3 (ohne 2)
- **GW-Planung:** Standort 1.5 (Leapmotor) nur in JavaScript
- **Stundensatz-Kalkulation:** Alle Standorte (1, 2, 3)

**Problem:**
- UI-Filter-Logik ist hardcoded in `routes/planung_routes.py`
- Nicht zentralisiert
- Nicht dokumentiert in SSOT

**Empfehlung:**
- UI-Filter-Logik in SSOT dokumentieren
- Zentrale Funktion `get_standorte_fuer_bereich()` erstellen

---

### 4. ⚠️ Inkonsistente Bezeichnungen

**SSOT definiert:**
- `STANDORT_NAMEN = {1: 'Deggendorf Opel', 2: 'Deggendorf Hyundai', 3: 'Landau'}`
- `BETRIEB_NAMEN = {1: 'Deggendorf', 2: 'Hyundai DEG', 3: 'Landau'}`

**Code verwendet:**
- `stundensatz_kalkulation_api.py`: `{1: 'Deggendorf', 2: 'Hyundai DEG', 3: 'Landau'}` ✅ (BETRIEB_NAMEN)
- `planung_routes.py`: `{1: 'Deggendorf', 2: 'Hyundai DEG', 3: 'Landau'}` ✅ (BETRIEB_NAMEN)
- `gw_planung_gesamt.html`: `{1: 'Opel DEG', 2: 'Hyundai Deg', 3: 'Landau'}` ❌ (Abweichung)
- `vergleiche_bwa_csv.py`: `{1: 'Stellantis (DEG+LAN)', 2: 'Hyundai DEG', 3: 'Unbekannt'}` ❌ (Abweichung)

**Status:** Teilweise konsistent, aber einige Abweichungen

---

## 📊 ZUSAMMENFASSUNG

### ✅ Was korrekt ist:
1. Standort-Definitionen (Grundlagen)
2. SQL-Filter-Funktionen existieren und sind dokumentiert
3. Bereichs-Logik (Grundsätze)

### ❌ Was falsch ist:
1. **KRITISCH:** `abteilungsleiter_planung_data.py` filtert Standort 3 mit `subsidiary=1` statt `=3`
2. Orders-Filter hat kein `nur_stellantis` Parameter (Design-Frage)
3. UI-Filter nicht in SSOT dokumentiert
4. Inkonsistente Bezeichnungen in einigen Dateien

### ⚠️ Was fehlt:
1. UI-Filter-Logik in SSOT dokumentieren
2. Zentrale Funktion für "welche Standorte für welchen Bereich"
3. Kontext-spezifische Namen-Funktion

---

## 🎯 EMPFOHLENE NÄCHSTE SCHRITTE

### Priorität 1 (KRITISCH - Bug-Fix):
1. **`abteilungsleiter_planung_data.py` korrigieren:**
   - Zeile 1130: `o.subsidiary = 1` → `o.subsidiary = 3`
   - Zeile 1141: `out_subsidiary = 1` → `out_subsidiary = 3`
   - Alle anderen Stellen (1270, 1308, 1390) korrigieren
   - Kommentare aktualisieren

### Priorität 2 (Wichtig - Zentralisierung):
2. **UI-Filter zentralisieren:**
   - `get_standorte_fuer_bereich()` in `standort_utils.py` erstellen
   - `routes/planung_routes.py` umstellen
   - SSOT-Dokumentation erweitern

3. **Bezeichnungen zentralisieren:**
   - Alle Dateien auf `STANDORT_NAMEN` oder `BETRIEB_NAMEN` umstellen
   - Kontext-spezifische Namen als Funktion

### Priorität 3 (Design-Frage):
4. **Orders-Filter erweitern:**
   - Soll `build_locosoft_filter_orders()` auch `nur_stellantis` Parameter bekommen?
   - Oder ist das Design so gewollt?

---

**Status:** ✅ Vergleich abgeschlossen - Kritische Bugs identifiziert
