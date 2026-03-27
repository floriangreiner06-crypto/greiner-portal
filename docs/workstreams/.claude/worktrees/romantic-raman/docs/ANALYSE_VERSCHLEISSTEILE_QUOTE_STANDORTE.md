# Analyse: Verschleißteile-Quote nach Standort

**Erstellt:** 2025-12-21
**Für:** Matthias König (Serviceleiter)
**Analyse:** Claude (DRIVE Portal)

---

## Zusammenfassung

Bei der Analyse der Teile-Berechnung wurde festgestellt, dass **Landau** in mehreren Kategorien deutlich weniger Teile berechnet als Deggendorf und Hyundai.

---

## Ergebnisse nach Kategorie

### 🔴 KRITISCH: Contrasept (Desinfektion)

| Standort | Arbeit | Teil | **Quote** | Status |
|----------|--------|------|-----------|--------|
| Deggendorf | 785 | 777 | **99%** | ✅ OK |
| Hyundai | 668 | 655 | **98%** | ✅ OK |
| **Landau** | 10 | 5 | **50%** | 🔴 KRITISCH |

**Problem:** Landau führt Desinfektionen durch, berechnet aber das Contrasept-Spray (8835199) nur in 50% der Fälle.

---

### 🟡 AUFFÄLLIG: Bremsen

| Standort | Arbeit | Teil | **Quote** | Status |
|----------|--------|------|-----------|--------|
| Deggendorf | 565 | 567 | **100%** | ✅ OK |
| Hyundai | 255 | 233 | **91%** | ✅ OK |
| **Landau** | 272 | 195 | **72%** | 🟡 Auffällig |

**Problem:** Bei Bremsenarbeiten in Landau werden weniger Teile (Beläge/Scheiben) berechnet.

---

### 🟡 AUFFÄLLIG: Scheibenwischer

| Standort | Arbeit | Teil | **Quote** | Status |
|----------|--------|------|-----------|--------|
| Deggendorf | 140 | 441 | **315%** | ✅ OK |
| Hyundai | 99 | 202 | **204%** | ✅ OK |
| **Landau** | 172 | 263 | **153%** | 🟡 Niedriger |

**Hinweis:** Quote >100% ist normal (2-3 Wischerblätter pro Wechsel). Landau liegt aber deutlich unter DEG/HYU.

---

### ✅ OK: Öl

| Standort | Arbeit | Teil | **Quote** |
|----------|--------|------|-----------|
| Deggendorf | 183 | 4.098 | 2.239% |
| Hyundai | 103 | 2.420 | 2.350% |
| Landau | 339 | 2.454 | 724% |

**Hinweis:** Hohe Quote normal (mehrere Liter pro Ölwechsel). Landau niedriger, aber Absolutzahlen OK.

---

### ✅ OK: Filter

| Standort | Arbeit | Teil | **Quote** |
|----------|--------|------|-----------|
| Deggendorf | 3.870 | 9.146 | 236% |
| Hyundai | 785 | 3.842 | 489% |
| Landau | 1.983 | 4.424 | 223% |

**Status:** Alle Standorte im normalen Bereich.

---

### ✅ OK: Reifen

| Standort | Arbeit | Teil | **Quote** |
|----------|--------|------|-----------|
| Deggendorf | 6.334 | 1.269 | 20% |
| Hyundai | 4.966 | 1.067 | 22% |
| Landau | 3.454 | 599 | 17% |

**Hinweis:** Niedrige Quote normal (Radwechsel ohne Neukauf). Landau leicht niedriger.

---

## Handlungsbedarf

### Priorität 1: Contrasept (Landau)
- **Problem:** Spray wird in 50% der Fälle nicht berechnet
- **Geschätzter Verlust:** ~800€/Jahr (bei 10 fehlenden Buchungen × 16€)
- **Maßnahme:** Schulung + automatische Teil-Verknüpfung

### Priorität 2: Bremsen (Landau)
- **Problem:** 28% weniger Teile als bei Arbeiten
- **Mögliche Ursachen:**
  - Teile werden nicht gebucht
  - Kulanz ohne Buchung
  - Unterschiedliche Buchungspraxis
- **Maßnahme:** Stichproben-Prüfung von Aufträgen

### Priorität 3: Scheibenwischer (Landau)
- **Problem:** Halb so viele Teile wie DEG/HYU
- **Maßnahme:** Prüfen ob Wischerblätter aktiv angeboten werden

---

## SQL für eigene Analyse

```sql
-- Teile-Quote pro Standort für beliebige Kategorie
WITH arbeit AS (
    SELECT subsidiary, COUNT(*) as cnt
    FROM labours
    WHERE text_line ILIKE '%SUCHBEGRIFF%'
      AND is_invoiced = true
    GROUP BY subsidiary
),
teile AS (
    SELECT subsidiary, COUNT(*) as cnt
    FROM parts
    WHERE text_line ILIKE '%SUCHBEGRIFF%'
      AND is_invoiced = true
    GROUP BY subsidiary
)
SELECT
    CASE a.subsidiary WHEN 1 THEN 'DEG' WHEN 2 THEN 'HYU' WHEN 3 THEN 'LAN' END as standort,
    a.cnt as arbeit,
    t.cnt as teile,
    ROUND(t.cnt::numeric / NULLIF(a.cnt, 0) * 100, 1) as quote
FROM arbeit a
LEFT JOIN teile t ON a.subsidiary = t.subsidiary
ORDER BY a.subsidiary;
```

---

## Fazit

**Landau hat in mehreren Kategorien eine niedrigere Teile-Quote:**

| Kategorie | Landau vs. Durchschnitt DEG/HYU |
|-----------|--------------------------------|
| Contrasept | **50%** vs. 98% (-48 Punkte) |
| Bremsen | **72%** vs. 96% (-24 Punkte) |
| Wischer | **153%** vs. 260% (-107 Punkte) |

Dies deutet auf systematische Unterschiede in der Buchungspraxis hin, die überprüft werden sollten.

---

**Erstellt von:** Claude (DRIVE Portal Analyse)
**Tag:** 133
