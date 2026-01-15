# Locosoft Support-Anfrage: AW-Ant. Berechnung

**Betreff:** Dringend - AW-Ant. Berechnung weicht ab, benötige exakte Formel

**Priorität:** Hoch  
**Datum:** 2026-01-14  
**System:** Greiner Portal DRIVE (Integration mit Locosoft)

---

## Problem

Wir versuchen, die AW-Ant. (AW-Anteil) Berechnung aus Locosoft in unserem System nachzubilden. Trotz Zugriff auf die gleichen Rohdaten (labours, times, invoices) weichen unsere Ergebnisse ab:

| Metrik | DRIVE | Locosoft | Differenz |
|--------|-------|----------|-----------|
| AW | 9.6 | 10.0 | -0.4 AW |
| Stempelzeit | 452 Min | 451 Min | +1 Min |
| Leistungsgrad | 123.5% | 133.0% | -9.5% |

**WICHTIG:** Wir haben die Stempelungen geprüft - diese sind korrekt. Das Problem liegt eindeutig in der AW-Berechnung.

---

## Konkretes Beispiel

**Mechaniker:** 5018 (Jan)  
**Datum:** 13.01.26  
**Auftrag:** 220471, Position 1

### CSV-Werte (Locosoft):
- **AuAW:** 1:54 (1.9 Stunden)
- **AW-Ant.:** 0:34 (0.567 Stunden) ← **PROBLEM**
- **St-Ant.:** 0:29 (0.483 Stunden)
- **Leistungsgrad:** 117.2%

### Datenbank-Werte:
- **time_units:** 19.00 AW = 1.9 Stunden
- **Stempelzeit:** 28.88 Min (0.481 Stunden)
- **Nur ein Mechaniker** arbeitet an diesem Auftrag

### Frage:
**Wie wird AW-Ant. = 0:34 (0.567 Stunden) aus diesen Werten berechnet?**

Wir erwarten: AW-Ant. = AuAW = 1.9 Stunden (da nur ein Mechaniker arbeitet)

---

## Unsere Annahmen (die nicht funktionieren)

1. **AW-Ant. = time_units_Position** (wenn nur ein Mechaniker)
   - ❌ Funktioniert nicht für 220471

2. **AW-Ant. = time_units_Position * (Stempelzeit_Mechaniker / Gesamt-Stempelzeit_Auftrag)**
   - ❌ Funktioniert nicht für 220471

3. **AW-Ant. = St-Ant. * Faktor**
   - ❌ Faktor ist unbekannt

---

## Was wir benötigen

1. **Exakte Formel** für die AW-Ant. Berechnung
2. **SQL-Query** oder **Pseudocode**, der die Berechnung beschreibt
3. **Konkrete Beispiele** mit Datenbankwerten und erwarteten Ergebnissen
4. **Dokumentation** zu allen verwendeten Filterkriterien

---

## Detaillierte Fragen

Siehe: `locosoft_aw_anteil_fragenkatalog.md`

---

## Dringlichkeit

Wir benötigen dringend eine Antwort, da die Leistungsgrad-Berechnung für unsere Mechaniker-Bewertung kritisch ist. Aktuell weichen unsere Werte um bis zu 9.5% ab, was für faire Bewertungen nicht akzeptabel ist.

**Vielen Dank für Ihre Unterstützung!**
