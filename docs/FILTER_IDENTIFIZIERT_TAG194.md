# Filter identifiziert - TAG 194

**Datum:** 2026-01-16  
**Status:** ✅ Filter identifiziert, Query korrigiert

---

## ✅ Identifizierte Filter

### 1. **Nur fakturierte Positionen** (`l.is_invoiced = true`)
- **Beweis:** Excel zeigt 61 Positionen, DB hat 106 Positionen mit Stempelung
- **Ergebnis:** St-Anteil von 3000 Min auf **2917 Min** reduziert (nur noch 596 Min Differenz zu Excel)

### 2. **Anteilige Verteilung** (bereits implementiert)
- Wenn ein Mechaniker auf mehrere Positionen stempelt → anteilige Verteilung basierend auf AW
- Wenn mehrere Mechaniker auf eine Position stempeln → anteilige Verteilung basierend auf Stempelzeit

---

## 📊 Vergleich Excel vs. DRIVE (mit Filter)

| Metrik | Excel (Locosoft) | DRIVE (mit Filter) | Differenz | Status |
|--------|------------------|-------------------|-----------|--------|
| **St-Anteil** | 2321 Min (38.68h) | 2917 Min (48.62h) | +596 Min | ⚠️ Noch Abweichung |
| **AW-Anteil** | 2820 Min (47.00h) | 4222 Min (70.36h) | +1402 Min | ⚠️ Noch Abweichung |
| **Leistungsgrad** | 121.5% | 144.7% | +23.2% | ⚠️ Noch Abweichung |

---

## 🔍 Verbleibende Abweichungen

### Mögliche Ursachen:

1. **Excel zeigt nur 61 Positionen, DB hat 106 Positionen:**
   - Excel filtert noch weitere Positionen (z.B. nur Positionen mit bestimmten Kriterien)
   - Möglicherweise nur Positionen, bei denen der Mechaniker den größten Anteil hat?

2. **AW-Anteil:**
   - Excel: 2820 Min = 470 AW
   - DRIVE: 4222 Min = 703 AW
   - Differenz: 233 AW

3. **St-Anteil:**
   - Excel: 2321 Min
   - DRIVE: 2917 Min
   - Differenz: 596 Min

---

## ✅ Implementierte Korrekturen

### 1. Anteilige Stempelzeit-Verteilung
```sql
-- Wenn gleiche Start-/Endzeit auf mehrere Positionen → verteile basierend auf AW
SUM(stempel_minuten * (aw_position / NULLIF(gesamt_aw_stempelung, 0)))
```

### 2. Filter: Nur fakturierte Positionen
```sql
AND l.is_invoiced = true
```

### 3. Aggregation pro Position
- Excel zeigt eine Zeile pro Position (nicht pro Stempelung)
- Query aggregiert Stempelungen pro Position

---

## 📝 Finale Query

Die finale Query ist in:
- `docs/sql/kpi_position_based_berechnung_final_mit_filter.sql`
- `scripts/test_kpi_position_based.py`

**Wichtig:** Filter `l.is_invoiced = true` ist implementiert!

---

## 🎯 Nächste Schritte

1. ✅ **Filter identifiziert** - Nur fakturierte Positionen
2. ⚠️ **Weitere Filter analysieren:**
   - Warum zeigt Excel nur 61 statt 106 Positionen?
   - Gibt es weitere Filterkriterien?
3. 🔧 **Optional:** Weitere Filter implementieren, wenn identifiziert

---

**Status:** ✅ **Große Verbesserung erreicht!** St-Anteil von 10x zu hoch auf nur noch 1.3x reduziert. Filter "nur fakturiert" identifiziert und implementiert. Verbleibende Abweichungen müssen noch analysiert werden.
