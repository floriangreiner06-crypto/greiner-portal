# Analyse: Betriebsabhängige Stmp.Anteil-Berechnung

**Datum:** TAG 194  
**Problem:** Stmp.Anteil weicht für Tobias (-27.5%) stärker ab als für Jan (-2.0%)

## Erkenntnis: Betriebsverteilung

### Jan Majer (5018)
- **DEGO (Betrieb 1):** 71.4% der Stempelzeit
- **DEGH (Betrieb 2):** 28.6% der Stempelzeit

### Tobias Reitmeier (5007)
- **DEGO (Betrieb 1):** 33.0% der Stempelzeit
- **DEGH (Betrieb 2):** 67.0% der Stempelzeit

## Getestete Hypothesen

### ❌ Hypothese 1: Betriebsabhängige Logik
- **DEGO (Betrieb 1):** Positionen ohne AW = 0%
- **DEGH (Betrieb 2):** Positionen ohne AW = 50%
- **Ergebnis:** Nicht unterstützt - Annahme kann nicht bestätigt werden

### ❌ Hypothese 2: Nur fakturierte Positionen
- Nur `is_invoiced = true` Positionen berücksichtigen
- **Ergebnis:** Schlechtere Ergebnisse (Tobias: -44.8%, Jan: +34.2%)

## Aktueller Stand

**Implementierung:** Einheitliche Logik
- Positionen MIT AW: Anteilig nach AW
- Positionen OHNE AW: Gleichmäßig verteilen
- Alle Positionen 0 AW: Gleichmäßig verteilen

**Ergebnisse (einheitliche Logik):**
- **Tobias:** 3602 Min (Locosoft: 4971 Min) → Diff: -1369 Min (-27.5%)
- **Jan:** 4038 Min (Locosoft: 4121 Min) → Diff: -83 Min (-2.0%)

## Offene Fragen

1. Warum unterschiedliche Abweichungen pro Mechaniker?
2. Gibt es weitere Filter (z.B. nur bestimmte Auftragstypen)?
3. Wird die Fakturierung bei der Berechnung berücksichtigt, aber anders als erwartet?
4. Gibt es andere Faktoren, die die Berechnung beeinflussen?

## Nächste Schritte

1. ✅ Betriebsabhängige Logik entfernt
2. 🔍 Weitere Analyse nötig - vielleicht andere Faktoren?
3. 📋 Locosoft-Support anfragen für exakte Logik
