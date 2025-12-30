# TODO: Contrasept-Abrechnung Landau prüfen

**Erstellt:** 2025-12-21
**Für:** Matthias König (Serviceleiter)
**Priorität:** HOCH
**Status:** Offen

---

## Problem

Bei der Analyse der Contrasept-Rangliste (Serviceberater-Wettbewerb) wurde festgestellt, dass **Landau** deutlich weniger Umsatz generiert als Deggendorf/Hyundai.

### Symptome

1. **Arbeit wird mit 0€ berechnet**
   - Landau bucht: "Klimacheck **mit Desinfektion incl.**" → 0,00€
   - Deggendorf bucht: "Desinfektion Pollenfilterkasten" → 13,12€

2. **Teil (Contrasept-Spray) wird kaum verkauft**

| Standort | Desinfektion (Arbeit) | Contrasept-Teil (8835199) | **Quote** |
|----------|----------------------|---------------------------|-----------|
| Deggendorf | 785 | 777 | **99%** |
| Hyundai | 668 | 655 | **98%** |
| **Landau** | 10 | 5 | **50%** |

---

## Analyse

### Verdacht: Teil wird "verschenkt"

In Deggendorf und Hyundai wird bei fast jeder Desinfektion (99%) auch das Contrasept-Spray berechnet.

In Landau wird das Spray nur in **50% der Fälle** berechnet.

### Entgangener Umsatz (geschätzt)

- Contrasept-Spray Ø Preis: **16,27€**
- Fehlende Teil-Buchungen Landau: ca. 5 Stück (50% von 10)
- **Entgangener Umsatz: ~81€** (nur für die 10 erfassten Arbeiten)

Bei korrekter Erfassung (gleiche Anzahl wie DEG/Hyundai relativ zur Werkstattgröße) wäre der entgangene Umsatz deutlich höher.

---

## Betroffene Mitarbeiter

| MA-ID | Name | Standort | Contrasept Dez 2025 | Umsatz |
|-------|------|----------|---------------------|--------|
| 4002 | Leonhard Keidl | Landau | 13 Stück | 0,00€ |
| 4003 | Edith Egner | Landau | 4 Stück | 0,00€ |

---

## Empfohlene Maßnahmen

1. **Schulung Landau**
   - Desinfektion separat buchen (nicht als "inkl.")
   - Contrasept-Spray (8835199) immer mit berechnen

2. **Arbeitswert-Anlage prüfen**
   - Gibt es in Landau einen AW "Desinfektion" mit Preis?
   - Oder nur Paket-AWs ("Klimacheck inkl.")?

3. **Teil-Verknüpfung prüfen**
   - Ist 8835199 im Landauer System hinterlegt?
   - Automatische Teil-Zuordnung bei Desinfektion?

---

## Datenquellen

- **Tabelle:** `labours` (Arbeitspositionen)
- **Tabelle:** `parts` (Teilepositionen)
- **Teil-Nr:** 8835199 (Airco Well Contrasept Spray)
- **Suchbegriffe:** "desinfektion", "contrasept"

---

## SQL für eigene Analyse

```sql
-- Contrasept-Teil Quote pro Standort
WITH arbeit AS (
    SELECT subsidiary, COUNT(*) as arbeit_anzahl
    FROM labours
    WHERE text_line ILIKE '%desinfektion%'
      AND is_invoiced = true
    GROUP BY subsidiary
),
teile AS (
    SELECT subsidiary, COUNT(*) as teil_anzahl
    FROM parts
    WHERE part_number = '8835199'
      AND is_invoiced = true
    GROUP BY subsidiary
)
SELECT
    COALESCE(a.subsidiary, t.subsidiary) as subsidiary,
    COALESCE(a.arbeit_anzahl, 0) as desinfektion_arbeit,
    COALESCE(t.teil_anzahl, 0) as contrasept_teil,
    ROUND(COALESCE(t.teil_anzahl, 0)::numeric / NULLIF(a.arbeit_anzahl, 0) * 100, 1) as teil_quote
FROM arbeit a
FULL OUTER JOIN teile t ON a.subsidiary = t.subsidiary
ORDER BY subsidiary;
```

---

**Erstellt von:** Claude (DRIVE Portal Analyse)
**Tag:** 133
