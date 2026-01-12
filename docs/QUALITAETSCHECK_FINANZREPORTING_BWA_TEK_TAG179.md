# Quality Check: Finanzreporting Cube vs. BWA/TEK - TAG 179

**Datum:** 2026-01-10  
**Zweck:** Redundanzen zwischen Finanzreporting Cube, BWA und TEK identifizieren

---

## 🔍 ÜBERSICHT

### Analysierte Komponenten

1. **Finanzreporting Cube** (`api/finanzreporting_api.py`)
   - Materialized Views: `fact_bwa`, `dim_zeit`, `dim_standort`, `dim_kostenstelle`, `dim_konto`
   - Datenquelle: `loco_journal_accountings` (gespiegelt)
   - Zweck: Vorgeaggregierte Cube-Abfragen

2. **BWA API** (`api/controlling_api.py`)
   - Funktionen: `get_bwa()`, `get_bwa_v2()`, `_berechne_bwa_werte()`
   - Datenquelle: `loco_journal_accountings` (gespiegelt)
   - Zweck: BWA-Berechnungen (Umsatz, Einsatz, Kosten, DB1-3, BE)

3. **TEK API** (`routes/controlling_routes.py`)
   - Funktion: `api_tek()`
   - Datenquelle: `journal_accountings` (direkt aus Locosoft) + `loco_journal_accountings` (gespiegelt)
   - Zweck: Tägliche Erfolgskontrolle

---

## ⚠️ GEFUNDENE REDUNDANZEN

### 1. G&V-Abschluss-Filter (KRITISCH)

**Problem:** Filter-Logik wird in **6+ Dateien** dupliziert

**Aktuell:**
```sql
-- In mehreren Dateien:
guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
```

**Betroffene Dateien:**
- ✅ `api/controlling_api.py` (mehrfach)
- ❌ `api/abteilungsleiter_planung_data.py` (dupliziert)
- ❌ `api/gewinnplanung_v2_gw_data.py` (dupliziert)
- ❌ `api/werkstatt_data.py` (dupliziert)
- ❌ `api/gewinnplanung_v2_gw_api.py` (dupliziert)
- ✅ `migrations/create_finanzreporting_cube_tag178.sql` (in Materialized View)

**Empfehlung:**
- Zentrale Funktion in `api/db_utils.py` oder `api/controlling_api.py`:
```python
def get_guv_filter() -> str:
    """G&V-Abschluss-Filter für BWA-Berechnungen"""
    return "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
```

**Status:** ⚠️ **REDUNDANZ** - Sollte konsolidiert werden

---

### 2. Firma/Standort-Filter (TEILWEISE REDUNDANZ)

**Problem:** Filter-Logik wird in **2 Dateien** dupliziert

**Aktuell:**
- ✅ `api/controlling_api.py` → `build_firma_standort_filter()` (zentral)
- ✅ `api/standort_utils.py` → Wrapper um `build_firma_standort_filter()` (gut!)
- ❌ `api/abteilungsleiter_planung_data.py` → Eigene Implementierung (dupliziert)

**Beispiel-Duplikat:**
```python
# In abteilungsleiter_planung_data.py (Zeile 254-277)
if firma == '0':
    firma_filter_umsatz = "AND ((branch_number = 1 AND SUBSTRING(nominal_account_number::TEXT, 5, 1) = '1') OR ...)"
    # ... ähnliche Logik wie in controlling_api.py
```

**Empfehlung:**
- `abteilungsleiter_planung_data.py` sollte `build_firma_standort_filter()` verwenden

**Status:** ⚠️ **TEILWEISE REDUNDANZ** - Sollte konsolidiert werden

---

### 3. Betrag-Berechnung (TEILWEISE REDUNDANZ)

**Problem:** Ähnliche Logik in mehreren Dateien

**Aktuell:**

**BWA (`controlling_api.py`):**
```sql
CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END / 100.0
```

**TEK (`routes/controlling_routes.py`):**
```sql
CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END / 100.0
```

**Finanzreporting (`fact_bwa` Materialized View):**
```sql
CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END / 100.0 as betrag
```

**Hinweis:** 
- Finanzreporting verwendet bereits vorgeaggregierte Werte (gut!)
- BWA und TEK berechnen on-the-fly (könnte auf Cube umgestellt werden)

**Status:** ✅ **OK** - Finanzreporting nutzt bereits Materialized View

---

### 4. Datenquelle (KEINE REDUNDANZ - DESIGN-ENTSCHEIDUNG)

**Aktuell:**

| Komponente | Datenquelle | Grund |
|------------|-------------|-------|
| **BWA** | `loco_journal_accountings` | Gespiegelte Daten (nach 19:00 Uhr aktuell) |
| **TEK** | `journal_accountings` (direkt) + `loco_journal_accountings` | Heute-Daten direkt, Monatsdaten gespiegelt |
| **Finanzreporting** | `fact_bwa` (Materialized View) | Vorgeaggregiert, schneller |

**Status:** ✅ **OK** - Unterschiedliche Anforderungen, keine Redundanz

---

### 5. Konten-Filter (TEILWEISE REDUNDANZ)

**Problem:** Konten-Ranges werden mehrfach definiert

**Aktuell:**

**BWA (`controlling_api.py`):**
```python
# Umsatz: 800000-889999, 893200-893299
# Einsatz: 700000-799999
# Kosten: 400000-499999 (mit komplexen Filtern)
```

**TEK (`routes/controlling_routes.py`):**
```python
# Umsatz: 800000-899999
# Einsatz: 700000-799999
```

**Finanzreporting (`fact_bwa`):**
- Alle Konten in Materialized View
- Filterung über `konto_ebene3` Parameter

**Status:** ⚠️ **TEILWEISE REDUNDANZ** - Konten-Ranges könnten zentral definiert werden

---

## ✅ POSITIVE ASPEKTE (SSOT-KONFORMITÄT)

### 1. Zentrale DB-Utilities
- ✅ Alle APIs verwenden `api/db_utils.py` → `db_session()`
- ✅ Alle APIs verwenden `api/db_connection.py` → `convert_placeholders()`
- ✅ Keine lokalen DB-Verbindungen

### 2. Standort-Utils
- ✅ `api/standort_utils.py` als Wrapper um `build_firma_standort_filter()`
- ✅ Wird von mehreren Modulen verwendet

### 3. Materialized Views
- ✅ Finanzreporting nutzt vorgeaggregierte Daten (keine Duplikation der Berechnung)
- ✅ `fact_bwa` enthält bereits Betrag-Berechnung

---

## 🎯 EMPFEHLUNGEN

### Priorität 1: G&V-Filter konsolidieren

**Aktion:**
1. Zentrale Funktion in `api/db_utils.py` oder `api/controlling_api.py` erstellen
2. Alle Dateien auf zentrale Funktion umstellen

**Dateien zu ändern:**
- `api/abteilungsleiter_planung_data.py`
- `api/gewinnplanung_v2_gw_data.py`
- `api/werkstatt_data.py`
- `api/gewinnplanung_v2_gw_api.py`

**Vorteil:**
- Einheitliche Logik
- Einfache Wartung
- Weniger Fehlerquellen

---

### Priorität 2: Firma/Standort-Filter konsolidieren

**Aktion:**
1. `api/abteilungsleiter_planung_data.py` auf `build_firma_standort_filter()` umstellen

**Vorteil:**
- Konsistente Filter-Logik
- Weniger Code-Duplikate

---

### Priorität 3: Konten-Ranges zentral definieren

**Aktion:**
1. Zentrale Konstanten in `api/controlling_api.py` oder `api/db_utils.py`:
```python
KONTO_RANGES = {
    'umsatz': (800000, 889999),
    'umsatz_sonder': (893200, 893299),
    'einsatz': (700000, 799999),
    'kosten': (400000, 499999),
    # ...
}
```

**Vorteil:**
- Einheitliche Definitionen
- Einfache Wartung

---

### Priorität 4: Optional - BWA auf Finanzreporting Cube umstellen

**Überlegung:**
- BWA könnte auf `fact_bwa` Materialized View umgestellt werden
- **Vorteil:** Schnellere Abfragen
- **Nachteil:** Abhängigkeit von Materialized View Refresh

**Status:** ⚠️ **OPTIONAL** - Nur wenn Performance-Probleme auftreten

---

## 📊 ZUSAMMENFASSUNG

| Kategorie | Status | Priorität |
|-----------|--------|-----------|
| **G&V-Filter** | ⚠️ Redundanz | 🔴 Hoch |
| **Firma/Standort-Filter** | ⚠️ Teilweise Redundanz | 🟡 Mittel |
| **Betrag-Berechnung** | ✅ OK | - |
| **Datenquelle** | ✅ OK | - |
| **Konten-Ranges** | ⚠️ Teilweise Redundanz | 🟡 Mittel |
| **DB-Utilities** | ✅ SSOT-konform | - |
| **Standort-Utils** | ✅ SSOT-konform | - |

---

## 🔧 NÄCHSTE SCHRITTE

1. **G&V-Filter konsolidieren** (Priorität 1)
2. **Firma/Standort-Filter konsolidieren** (Priorität 2)
3. **Konten-Ranges zentral definieren** (Priorität 3)
4. **Optional: BWA auf Cube umstellen** (nur bei Performance-Problemen)

---

**Status:** ✅ **Quality Check abgeschlossen**  
**Nächste Aktion:** Redundanzen konsolidieren (Priorität 1-3)
