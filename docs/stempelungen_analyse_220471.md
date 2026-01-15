# Stempelungen-Analyse für Auftrag 220471

**Datum:** 2026-01-14  
**Mechaniker:** 5018 (Jan)  
**Auftrag:** 220471  
**Datum:** 13.01.26

## Problem-Identifikation

### 1. Duplikate in der Datenbank

**Gefunden:** 3 identische Stempelungen für 220471
- Alle: 07:37:46 bis 08:06:39
- Dauer: 28.88 Min (jede)
- Gesamt-Dauer (ohne Deduplizierung): 86.65 Min ❌

**Ursache:**
- Möglicherweise mehrfaches Erfassen an der Stempeluhr
- Oder technisches Problem beim Speichern

**Lösung:**
- Die Deduplizierung in `werkstatt_data.py` korrigiert das automatisch
- Nach Deduplizierung: 1 Stempelung mit 28.88 Min ✅

### 2. Vergleich mit CSV

| Metrik | CSV | Datenbank (nach Deduplizierung) | Status |
|--------|-----|----------------------------------|--------|
| Startzeit | 07:37 | 07:37:46 | ✓ Übereinstimmung |
| Endzeit | 08:06 | 08:06:39 | ✓ Übereinstimmung |
| Dauer | 0:29 (29 Min) | 28.88 Min | ✓ Übereinstimmung (0.12 Min Differenz) |

**Fazit:** Die Stempelungen sind korrekt! ✅

### 3. AW-Berechnung Problem

**Problem:** AW-Ant. ist nicht gleich AuAW
- CSV: AW-Ant. = 0:34 = 0.567 Stunden
- Erwartet: AW-Ant. = AuAW = 1.9 Stunden
- Differenz: 1.333 Stunden

**Ursache:** 
- **NICHT** die Stempelungen (die sind korrekt)
- **Sondern** die AW-Berechnung von Locosoft
- Locosoft berechnet AW-Ant. anders als erwartet

## Weitere Beobachtungen

### Duplikate bei anderen Aufträgen

**Gefunden:** Alle Aufträge haben Duplikate in der Datenbank
- 39413: 11 Stempelungen → 1 nach Deduplizierung
- 39433: 6 Stempelungen → 1 nach Deduplizierung
- 220471: 3 Stempelungen → 1 nach Deduplizierung
- etc.

**Fazit:** Duplikate sind ein systematisches Problem, aber die Deduplizierung funktioniert korrekt.

## Empfehlungen

1. **Stempelungen sind korrekt** - Keine manuellen Korrekturen nötig
2. **Deduplizierung funktioniert** - Keine Änderungen nötig
3. **AW-Berechnung muss weiter analysiert werden** - Das Problem liegt in der Locosoft-Logik

## Nächste Schritte

1. Weiter analysieren, warum Locosoft AW-Ant. = 0.567 Stunden statt 1.9 Stunden berechnet
2. Prüfen, ob es eine spezielle Regel für bestimmte Auftragstypen gibt
3. Kontakt mit Locosoft Support, falls nötig
