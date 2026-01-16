# Leerlaufaufträge Aktualisierung - TAG 194

**Datum:** 2026-01-16  
**Status:** ✅ Aktualisiert (SSOT)

---

## 📋 Änderung

**Historische Leerlaufaufträge:**
- DEGO (Deggendorf Opel): Order 31
- DEGH (Deggendorf Hyundai): Keine
- LANO (Landau): Order 300014

**Neue Leerlaufaufträge (Serviceleiter-Umstellung):**
- **DEGO (Deggendorf Opel):** Order **39406** (statt 31)
- **DEGH (Deggendorf Hyundai):** Order **220710** (statt keine)
- **LANO (Landau):** Order **313666** (statt 300014)

---

## ✅ Durchgeführte Änderungen

### 1. Konstante aktualisiert (`api/werkstatt_data.py`)

```python
LEERLAUF_AUFTRAEGE_PRO_BETRIEB = {
    1: [39406],   # DEGO (Deggendorf Opel): Order 39406 (historisch: 31)
    2: [220710],  # DEGH (Deggendorf Hyundai): Order 220710 (historisch: keine)
    3: [313666]   # LANO (Landau): Order 313666 (historisch: 300014)
}
```

### 2. SSOT-Funktionen erstellt

**`build_leerlauf_filter(betrieb)`** - Für WHERE-Klauseln:
```python
# Beispiel: "AND t.order_number != ALL(ARRAY[39406,220710,313666])"
```

**`build_leerlauf_filter_equals(betrieb)`** - Für FILTER (WHERE ...) Klauseln:
```python
# Beispiel: "FILTER (WHERE t.order_number = ANY(ARRAY[39406,220710,313666]))"
```

### 3. Aktualisierte Stellen

1. ✅ `get_mechaniker_leistung()` - Verwendet jetzt `build_leerlauf_filter()`
2. ✅ `get_stempeluhr()` - Leerlauf-Query verwendet dynamische Liste
3. ✅ `get_anwesenheit_rohdaten()` - Leerlauf-Filter in FILTER-Klausel
4. ✅ `werkstatt_live_api.py` - Leerlauf-Filter aktualisiert

---

## ⚠️ Verbleibende Stellen mit `order_number > 31`

**14 Stellen** verwenden noch `order_number > 31` als generischen Filter.

**Status:** Diese sind OK, da sie als generischer Filter dienen (schließen kleine Test-Aufträge aus). Die Leerlaufaufträge werden zusätzlich durch `build_leerlauf_filter()` ausgeschlossen.

**Beispiel:**
```sql
WHERE t.order_number > 31  -- Generischer Filter
  AND t.order_number != ALL(ARRAY[39406,220710,313666])  -- Leerlauf-Filter
```

---

## 🔍 Verwendung in anderen Modulen

**SSOT-Prinzip:** Die Konstante `LEERLAUF_AUFTRAEGE_PRO_BETRIEB` ist die **Single Source of Truth** für Leerlaufaufträge.

**Verwendet in:**
- ✅ `api/werkstatt_data.py` - Stempelzeit-Berechnungen
- ✅ `api/werkstatt_live_api.py` - Live-Dashboard
- ⚠️ Andere Module sollten `build_leerlauf_filter()` verwenden, nicht hardcoded Werte!

---

## 📝 Nächste Schritte

1. ⏳ Prüfe andere Module auf hardcoded `order_number = 31` oder `order_number = 300014`
2. ⏳ Ersetze durch `build_leerlauf_filter()` oder `build_leerlauf_filter_equals()`
3. ⏳ Teste Leerlauf-Warnungen im Dashboard

---

**Status:** ✅ **Leerlaufaufträge aktualisiert, SSOT-Funktionen erstellt**
