# Fragenkatalog für Locosoft Support - AW-Ant. Berechnung

**Datum:** 2026-01-14  
**Thema:** AW-Ant. (AW-Anteil) Berechnung in der Stempelzeiten-Übersicht  
**Ziel:** Exakte Nachbildung der Locosoft-Berechnung in DRIVE

## Kontext

Wir versuchen, die AW-Ant. Berechnung aus Locosoft in unserem System nachzubilden. Wir haben Zugriff auf die gleichen Rohdaten (labours, times, invoices), aber die Ergebnisse weichen ab:

- **DRIVE:** 9.6 AW, Leistungsgrad 123.5%
- **Locosoft:** 10.0 AW, Leistungsgrad 133.0%

**WICHTIG:** Wir haben die Stempelungen geprüft - diese sind korrekt. Das Problem liegt eindeutig in der AW-Berechnung von Locosoft.

## Fragen

### 1. Zeiteinheiten

- In welcher Einheit wird **AW-Ant.** berechnet? (Stunden, Minuten, AW?)
- In welcher Einheit wird **time_units** in der `labours` Tabelle gespeichert? (AW = 6-Minuten-Einheiten?)
- Wie wird AW-Ant. in der UI angezeigt? (z.B. "10:00" = 10 Stunden oder 10 AW?)
- Gibt es eine Konvertierung zwischen verschiedenen Zeiteinheiten?

### 2. Berechnungslogik

- Wird AW-Ant. **pro Auftrag** oder **pro Position** (mit `order_position_line`) berechnet?
- Wie wird AW-Ant. berechnet, wenn **mehrere Mechaniker** an einem Auftrag arbeiten?
- Wie wird AW-Ant. berechnet, wenn ein Mechaniker an **mehreren Positionen** eines Auftrags arbeitet?
- Gibt es eine **proportionale Verteilung** basierend auf Stempelzeit? Wenn ja, wie genau?
- **WICHTIG:** Warum ist AW-Ant. manchmal gleich AuAW (z.B. Auftrag 39413, Position 1) und manchmal nicht (z.B. Auftrag 220471, Position 1)?

### 3. Filterkriterien

- Welche **Filterkriterien** werden für die AW-Ant. Berechnung verwendet?
- Werden nur **fakturierte Positionen** berücksichtigt? (`is_invoiced = true`)
- Werden nur Positionen berücksichtigt, bei denen der Mechaniker **tatsächlich gearbeitet hat**? (basierend auf `times`)
- Gibt es weitere Filter (z.B. Status, Typ, etc.)?
- Werden Positionen mit `time_units = 0` ausgeschlossen?

### 4. Stempelzeit

- Welche **Stempelzeit** wird für die AW-Ant. Berechnung verwendet?
- Wird die Stempelzeit **pro Auftrag** oder **pro Position** verwendet?
- Wie wird die Stempelzeit berechnet, wenn mehrere Mechaniker an einem Auftrag arbeiten?
- Werden **Pausen** oder **Lücken** in der Stempelzeit berücksichtigt?
- Gibt es eine **separate Stempelzeit** für die Leistungsgrad-Berechnung?
- **WICHTIG:** Was bedeutet "St-Ant." (Stempelzeit-Anteil) in der CSV-Datei? Ist das die Stempelzeit pro Position oder pro Auftrag?

### 5. Konkretes Beispiel 1

**Auftrag 220471, Position 1, Zeile 1, Mechaniker 5018, Datum 13.01.26:**

- **CSV zeigt:**
  - Position: "1,01 I"
  - AuAW = 1:54 (1.9 Stunden)
  - AW-Ant. = 0:34 (0.567 Stunden)
  - St-Ant. = 0:29 (0.483 Stunden)
  - Leistungsgrad = 117.2%

- **Datenbank:**
  - `order_position` = 1, `order_position_line` = 1
  - `time_units` = 19.00 AW = 1.9 Stunden
  - Stempelzeit pro Auftrag = 28.88 Min (0.481 Stunden)
  - Nur ein Mechaniker arbeitet an diesem Auftrag

**Frage:** Wie wird AW-Ant. = 0:34 aus diesen Werten berechnet?

### 5.1. Konkretes Beispiel 2

**Auftrag 39413, Position 1, Zeile 2, Mechaniker 5018, Datum 13.01.26:**

- **CSV zeigt:**
  - Position: "1,02 W"
  - AuAW = 1:00 (1.0 Stunden)
  - AW-Ant. = 1:00 (1.0 Stunden)
  - St-Ant. = 0:26 (0.433 Stunden)
  - Leistungsgrad = 230.8%

- **Datenbank:**
  - `order_position` = 1, `order_position_line` = 2
  - `time_units` = 10.00 AW = 1.0 Stunden
  - Stempelzeit pro Auftrag = 57.02 Min (0.95 Stunden)
  - Gesamt-time_units des Auftrags = 21.00 AW = 2.1 Stunden
  - Nur ein Mechaniker arbeitet an diesem Auftrag

**Frage:** Warum ist AW-Ant. = 1:00 (gleich AuAW), obwohl St-Ant. = 0:26 (nicht die gesamte Stempelzeit)?

### 6. Leistungsgrad

- Wie wird der **Leistungsgrad** berechnet?
- Formel: `Leistungsgrad = (AW-Ant. / St-Ant.) * 100`?
- Oder: `Leistungsgrad = (AW-Ant. * 6 / St-Ant.) * 100`?
- Welche **Stempelzeit** wird für den Leistungsgrad verwendet?
- Gibt es eine **separate Stempelzeit** für den Leistungsgrad (z.B. mit Pausenabzug)?

### 7. UI-Interpretation

- Wie interpretiert das **Locosoft UI** die AW-Ant. Werte?
- Werden die Werte in der UI anders dargestellt als in der Datenbank?
- Gibt es **Rundungen** oder **Formatierungen**, die die Anzeige beeinflussen?
- Wird "10:00" als 10 Stunden oder 10 AW interpretiert?

### 8. Dokumentation

- Gibt es eine **offizielle Dokumentation** zur AW-Ant. Berechnung?
- Gibt es **SQL-Beispiele** oder **Formeln**, die die Berechnung beschreiben?
- Gibt es **API-Dokumentation** oder **Datenbank-Schema-Dokumentation**?

### 9. Weitere Details

- Gibt es **Unterschiede** zwischen verschiedenen Locosoft-Versionen?
- Gibt es **Konfigurationsoptionen**, die die Berechnung beeinflussen?
- Gibt es **bekannte Bugs** oder **Workarounds** in der Berechnung?

## Erwartete Antworten

Wir benötigen:
1. **Exakte Formel** für die AW-Ant. Berechnung
2. **SQL-Query** oder **Pseudocode**, der die Berechnung beschreibt
3. **Konkrete Beispiele** mit Datenbankwerten und erwarteten Ergebnissen
4. **Dokumentation** zu allen verwendeten Filterkriterien

## Dringlichkeit

Wir benötigen dringend eine Antwort, da die Leistungsgrad-Berechnung für unsere Mechaniker-Bewertung kritisch ist. Aktuell weichen unsere Werte um bis zu 9.5% ab, was für faire Bewertungen nicht akzeptabel ist.

## Kontakt

Bei Rückfragen bitte kontaktieren Sie uns unter: [Ihre Kontaktdaten]

---

**Erstellt am:** 2026-01-14  
**Von:** Greiner Portal DRIVE System  
**Status:** Dringend - Blockiert korrekte KPI-Berechnung
