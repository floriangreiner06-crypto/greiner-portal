# BWA Mechanik+Karo Differenz-Analyse - 3.203,11 €

**Datum:** 2026-01-16  
**TAG:** 196  
**Status:** ⏳ **ANALYSE FÜR BUCHHALTER CHRISTIAN**

---

## 📋 EXECUTIVE SUMMARY

**Problem:**
- **GlobalCube:** "Mechanik+Karo" = 86.419,00 €
- **DRIVE:** Mechanik + Karosserie = 89.622,11 €
- **Differenz:** +3.203,11 € (DRIVE zu hoch, 3,7% Abweichung)

**Hauptursache (vermutet):**
- **Konto 743001/74300:** Vorzeichen-Unterschied
  - DRIVE: +34.778,12 € (SOLL-Buchungen verringern Einsatz)
  - GlobalCube: -37.981,00 € (SOLL-Buchungen erhöhen Einsatz)
  - **Summe aller 74300x Konten (inkl. 743002):** 37.980,92 € entspricht fast genau GlobalCube's -37.981,00 €
  - **Nur das Vorzeichen ist unterschiedlich!**

**Nächste Schritte:**
1. Prüfen ob SOLL-Buchungen auf 74300x den Einsatz erhöhen (negativ) oder verringern (positiv) sollen
2. Prüfen ob 743002 in GlobalCube enthalten ist oder ausgeschlossen wird
3. Konten-Liste aus GlobalCube für direkten Vergleich anfordern

**Dateien:**
- 📄 Diese Dokumentation: `docs/BWA_MECHANIK_KARO_DIFFERENZ_3203_TAG196.md`
- 📊 CSV-Export aller Konten: `docs/BWA_MECHANIK_KARO_KONTEN_DEZ2025.csv`

---

## 🎯 PROBLEM (DETAILLIERT)

**GlobalCube zeigt:** "Mechanik+Karo" = 86.419,00 €  
**DRIVE zeigt:** Mechanik + Karosserie = 89.622,11 €  
**Differenz:** +3.203,11 € (DRIVE zu hoch, 3,7% Abweichung)

---

## ✅ IMPLEMENTIERTE STRUKTUR

### Mechanik (inkl. Clean Park buchhalterisch):

**Erlös-Konten (84xxxx):**
- 84xxxx (ohne 84100/84170/84180 = Karosserie)
- 84060x (Lackierung - gehört zu Mechanik)
- 84705, 84708, 84709, 84720, 84700 (gehören zu Mechanik, nicht Clean Park)
- **NICHT enthalten:** 84100/84170/84180 (Karosserie), 847xxx Rest (Clean Park separat)

**Einsatz-Konten (74xxxx):**
- 74xxxx (ohne 74100/74170/74180 = Karosserie, ohne 746xxx = Lackierung)
- 74700x, 74720x (gehören zu Mechanik, nicht Clean Park)
- **NICHT enthalten:** 743002 (EW Fremdleistungen), 74100/74170/74180 (Karosserie), 746xxx (Lackierung), 747xxx Rest (Clean Park separat)

### Karosserie:

**Erlös-Konten:**
- 84100x (841001, 841002)
- 84170x (keine Buchungen)
- 84180x (841801)

**Einsatz-Konten:**
- 74100x, 74170x, 74180x (keine Buchungen)

### Clean Park (separat angezeigt):

**Erlös-Konten:**
- 847xxx (ohne 84705/84708/84709/84720/84700)
- 837051

**Einsatz-Konten:**
- 747xxx (ohne 74700/74720)

**Hinweis:** Clean Park gehört buchhalterisch zu Mechanik, wird aber fürs Controlling separat ausgewiesen.

---

## 📊 DETAILLIERTE KONTEN-AUFLISTUNG

### Mechanik Erlös-Konten (Dezember 2025):

| Konto | Wert | Buchungen | Anmerkung |
|-------|------|-----------|-----------|
| 840001 | 59.803,90 € | 386 | Hauptkonto Mechanik |
| 840002 | 15.697,39 € | 107 | |
| 840601 | 11.417,84 € | 150 | Lackierung (gehört zu Mechanik) |
| 840602 | 6.840,10 € | 37 | Lackierung (gehört zu Mechanik) |
| 840701 | 7.205,83 € | 130 | |
| 840702 | 2.481,50 € | 23 | |
| 843001 | 3.388,27 € | 7 | ⚠️ Nahe Differenz (185,16 € Abweichung) |
| 843002 | 588,00 € | 1 | |
| 843601 | 191,47 € | 1 | |
| 843602 | 150,00 € | 2 | |
| 843701 | 1.205,48 € | 3 | |
| 843702 | 853,00 € | 1 | |
| 843801 | 50.852,37 € | 21 | Größtes Konto |
| 847001 | -295,57 € | 4 | Clean Park (gehört zu Mechanik) |
| 847051 | 12.500,00 € | 1 | Clean Park (gehört zu Mechanik) |
| 847081 | 1.169,00 € | 2 | Clean Park (gehört zu Mechanik) |
| 847091 | 1.500,00 € | 5 | Clean Park (gehört zu Mechanik) |
| 847201 | 3.402,19 € | 8 | Clean Park (gehört zu Mechanik) ⚠️ Nahe Differenz (199,08 € Abweichung) |
| **Gesamt Erlös** | **175.537,63 €** | | |

### Mechanik Einsatz-Konten (Dezember 2025):

| Konto | Wert | Buchungen | Anmerkung |
|-------|------|-----------|-----------|
| 740001 | 44.963,79 € | 11 | |
| 740002 | 14.441,79 € | 1 | |
| 743001 | 34.778,12 € | 33 | ⚠️ Laut GlobalCube sollte negativ sein (-37.981 €) |
| 747001 | 2.521,00 € | 30 | Clean Park (gehört zu Mechanik) ⚠️ Nahe Differenz (682,11 € Abweichung) |
| 747002 | 869,84 € | 12 | Clean Park (gehört zu Mechanik) |
| 747201 | 1.617,04 € | 12 | Clean Park (gehört zu Mechanik) |
| **Gesamt Einsatz** | **99.192,58 €** | | |

**Mechanik Bruttoertrag:** 175.537,63 € - 99.192,58 € = **76.345,05 €**

### Karosserie Erlös-Konten (Dezember 2025):

| Konto | Wert | Buchungen | Anmerkung |
|-------|------|-----------|-----------|
| 841001 | 5.116,50 € | 12 | |
| 841002 | 1.281,00 € | 4 | |
| 841801 | 3.525,00 € | 16 | |
| **Gesamt Erlös** | **9.922,50 €** | | |

**Karosserie Bruttoertrag:** 9.922,50 € (kein Einsatz)

### Summe Mechanik+Karo:

**DRIVE:** 76.345,05 € + 9.922,50 € = **86.267,55 €**  
**GlobalCube:** **86.419,00 €**  
**Differenz:** -151,45 €

**⚠️ HINWEIS:** Die API zeigt aktuell 79.699,61 € für Mechanik. Die obige manuelle Berechnung zeigt 76.345,05 €. Die Differenz entsteht durch unterschiedliche Filter-Logik in der API vs. direkter SQL-Berechnung.

**Aktuelle API-Werte (Dezember 2025):**
- Mechanik: 79.699,61 €
- Karosserie: 9.922,50 €
- Summe: 89.622,11 €
- GlobalCube: 86.419,00 €
- **Differenz: +3.203,11 €**

---

## ⚠️ IDENTIFIZIERTE PROBLEME

### 1. Konto 743001 (34.778,12 €) - ⚠️ KRITISCH

**Problem:**
- DRIVE berechnet: +34.778,12 € (nur SOLL-Buchungen, keine HABEN-Buchungen)
- GlobalCube zeigt: -37.981 € (74300 = -22.415 € + 74300_H = -15.566 €)
- **Unterschied:** ~72.759 €

**Detaillierte Analyse:**
- **Anzahl Buchungen:** 33 Buchungen im Dezember 2025
- **Alle Buchungen sind SOLL:** 34.778,12 €
- **Keine HABEN-Buchungen:** 0,00 €
- **Branches:** Branch 1 (Subsidiary 1) und Branch 2 (Subsidiary 2)

**Mögliche Ursachen:**
1. **GlobalCube verwendet andere Kontenstruktur:**
   - GlobalCube zeigt "74300" und "74300_H" (ohne letzte Ziffer)
   - DRIVE verwendet "743001" (mit letzter Ziffer)
   - Möglicherweise gibt es mehrere Konten (743001, 743002, etc.) die in GlobalCube zusammengefasst werden

2. **Vorzeichen-Umkehr:**
   - GlobalCube zeigt negative Werte (-37.981 €)
   - DRIVE zeigt positive Werte (+34.778,12 €)
   - Möglicherweise werden SOLL-Buchungen in GlobalCube als negativ behandelt (erhöhen Einsatz)

3. **HABEN-Buchungen fehlen:**
   - DRIVE zeigt keine HABEN-Buchungen auf 743001
   - GlobalCube zeigt "74300_H" mit -15.566 €
   - Möglicherweise gibt es HABEN-Buchungen auf anderen Konten (z.B. 743002, 743003, etc.)

**Alle 74300x Konten im Dezember 2025:**

| Konto | SOLL | HABEN | NETTO | Buchungen | Anmerkung |
|-------|------|-------|-------|-----------|-----------|
| 743001 | 34.778,12 € | 0,00 € | 34.778,12 € | 33 | Hauptkonto |
| 743002 | 3.202,80 € | 0,00 € | 3.202,80 € | 3 | **Ausgeschlossen** (EW Fremdleistungen) |
| **Gesamt (inkl. 743002)** | **37.980,92 €** | **0,00 €** | **37.980,92 €** | **36** | |
| **Gesamt (ohne 743002)** | **34.778,12 €** | **0,00 €** | **34.778,12 €** | **33** | In DRIVE verwendet |

**⚠️ WICHTIGE ERKENNTNIS:**
- **DRIVE Gesamt (ohne 743002):** 34.778,12 €
- **DRIVE Gesamt (inkl. 743002):** 37.980,92 €
- **GlobalCube Gesamt:** -37.981,00 €

**Die Summe aller 74300x Konten (inkl. 743002) entspricht fast genau GlobalCube's -37.981 €!**
- Nur das **Vorzeichen ist unterschiedlich**: DRIVE zeigt +37.980,92 €, GlobalCube zeigt -37.981,00 €
- **Unterschied:** Nur 0,08 € (Rundungsfehler)

**Mögliche Erklärung:**
- GlobalCube behandelt SOLL-Buchungen auf 74300x als **negativ** (erhöhen Einsatz)
- DRIVE behandelt SOLL-Buchungen auf 74300x als **positiv** (verringern Einsatz)
- **743002 wird in DRIVE ausgeschlossen**, aber möglicherweise in GlobalCube enthalten?

**Vergleich mit GlobalCube:**
- GlobalCube: 74300 = -22.415 €, 74300_H = -15.566 €, **Gesamt = -37.981 €**
- DRIVE: 743001 = +34.778,12 € (nur SOLL, keine HABEN)
- **Unterschied:** ~72.759 €

**Zu prüfen durch Buchhalter:**
1. Welche Konten verwendet GlobalCube für "74300" und "74300_H"?
   - Gibt es mehrere Konten (743001, 743002, 743003, etc.) die in GlobalCube zusammengefasst werden?
   - Werden HABEN-Buchungen auf anderen Konten zu "74300_H" gezählt?
2. Gibt es HABEN-Buchungen auf 74300x Konten, die zu "74300_H" gehören?
   - DRIVE zeigt keine HABEN-Buchungen auf 743001
   - GlobalCube zeigt "74300_H" mit -15.566 €
3. Warum zeigt GlobalCube negative Werte, aber DRIVE positive Werte?
   - Möglicherweise werden SOLL-Buchungen in GlobalCube als negativ behandelt (erhöhen Einsatz)
   - Oder es gibt eine Vorzeichen-Umkehr in der Berechnung
4. Sollten SOLL-Buchungen auf 743001 den Einsatz erhöhen (negativ) oder verringern (positiv)?
   - Aktuell behandelt DRIVE SOLL-Buchungen als positiv (verringern Einsatz)
   - GlobalCube zeigt negative Werte (erhöhen Einsatz)

### 2. Konten nahe der Differenz (3.203,11 €)

**Konten die nahe der Differenz sind:**
- 843001: 3.388,27 € (Abweichung: 185,16 €)
- 847201: 3.402,19 € (Abweichung: 199,08 €)
- 840702: 2.481,50 € (Abweichung: 721,61 €)
- 747001: 2.521,00 € (Abweichung: 682,11 €)

**Zu prüfen:**
- Sollten diese Konten ausgeschlossen werden?
- Gibt es Filter-Unterschiede für diese Konten?

### 3. Clean Park Zuordnung

**Aktuell:**
- Clean Park wird separat angezeigt (11.732,81 €)
- Clean Park gehört buchhalterisch zu Mechanik
- Für "Mechanik+Karo" Summe: Mechanik (inkl. Clean Park) + Karosserie

**Zu prüfen:**
- Wird Clean Park in GlobalCube separat ausgewiesen oder zu Mechanik gezählt?
- Wie wird die Summe "Mechanik+Karo" in GlobalCube berechnet?

---

## 🔍 KONKRETE PRÜFPUNKTE FÜR BUCHHALTER

### 1. Konto 743001 / 74300

**Fragen:**
- Welche Konten verwendet GlobalCube für "74300"?
- Gibt es HABEN-Buchungen auf 743001, die ausgeschlossen werden sollten?
- Warum zeigt GlobalCube -37.981 €, aber DRIVE +34.778,12 €?

**Zu prüfen:**
- Alle Buchungen auf 743001 im Dezember 2025
- Gibt es 74300 (ohne letzte Ziffer) als separates Konto?
- Werden HABEN-Buchungen in GlobalCube anders behandelt?

### 2. Filter-Unterschiede

**Zu prüfen:**
- Verwendet GlobalCube andere Filter für Standort/Firma?
- Gibt es Zeitraum-Unterschiede (Buchungsdatum vs. Wertstellungsdatum)?
- Werden bestimmte Buchungstypen ausgeschlossen?

### 3. Konten-Struktur

**Zu prüfen:**
- Werden Konten in GlobalCube anders gruppiert?
- Gibt es Konten die in GlobalCube zu "Mechanik+Karo" gehören, aber in DRIVE fehlen?
- Gibt es Konten die in DRIVE zu "Mechanik+Karo" gehören, aber in GlobalCube ausgeschlossen sind?

### 4. Rundungsfehler

**Zu prüfen:**
- Werden Beträge in GlobalCube anders gerundet?
- Gibt es Cent-Unterschiede die sich summieren?

---

## 📋 NÄCHSTE SCHRITTE

1. **Konto 743001 analysieren:**
   - Alle Buchungen auf 743001 im Dezember 2025 prüfen
   - Vergleich mit GlobalCube "74300" durchführen
   - Vorzeichen-Unterschiede identifizieren

2. **Filter-Vergleich:**
   - GlobalCube Filter-Logik dokumentieren
   - Vergleich mit DRIVE Filter-Logik
   - Unterschiede identifizieren

3. **Konten-Vergleich:**
   - Alle Konten die zu "Mechanik+Karo" gehören in GlobalCube auflisten
   - Vergleich mit DRIVE Konten-Liste
   - Fehlende oder überschüssige Konten identifizieren

4. **Zeitraum-Prüfung:**
   - Prüfen ob GlobalCube andere Zeiträume verwendet
   - Buchungsdatum vs. Wertstellungsdatum prüfen

---

## 📊 ZUSAMMENFASSUNG

**Aktuelle Situation:**
- DRIVE: 89.622,11 €
- GlobalCube: 86.419,00 €
- Differenz: +3.203,11 € (3,7%)

**Hauptprobleme:**
1. **Konto 743001/74300 (KRITISCH):**
   - DRIVE: 743001 = +34.778,12 € (ohne 743002)
   - DRIVE: Alle 74300x = +37.980,92 € (inkl. 743002)
   - GlobalCube: 74300 = -37.981,00 €
   - **Die Summe entspricht fast genau, nur das Vorzeichen ist unterschiedlich!**
   - **Mögliche Ursache:** Vorzeichen-Umkehr in der Berechnung (SOLL erhöht Einsatz = negativ vs. SOLL verringert Einsatz = positiv)
2. Konten nahe der Differenz: 843001, 847201, 840702, 747001
3. Mögliche Filter-Unterschiede (743002 wird in DRIVE ausgeschlossen, möglicherweise in GlobalCube enthalten?)

**Empfehlung:**
- Konto 743001 als erstes analysieren (größter Unterschied)
- Filter-Logik zwischen DRIVE und GlobalCube vergleichen
- Konten-Liste aus GlobalCube für direkten Vergleich anfordern

---

## 📝 ANHANG: SQL-QUERIES FÜR WEITERE ANALYSE

### Alle Mechanik-Konten prüfen:

```sql
SELECT 
    nominal_account_number,
    SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as erlos,
    SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0 as einsatz,
    COUNT(*) as anzahl
FROM loco_journal_accountings
WHERE accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
  AND (
    (nominal_account_number BETWEEN 840000 AND 849999
     AND nominal_account_number NOT BETWEEN 841000 AND 841099
     AND nominal_account_number NOT BETWEEN 841700 AND 841799
     AND nominal_account_number NOT BETWEEN 841800 AND 841899
     AND (nominal_account_number NOT BETWEEN 847000 AND 847999 OR nominal_account_number IN (847051, 847081, 847091, 847201, 847001)))
    OR (nominal_account_number BETWEEN 740000 AND 749999
        AND nominal_account_number != 743002
        AND nominal_account_number NOT BETWEEN 741000 AND 741099
        AND nominal_account_number NOT BETWEEN 741700 AND 741799
        AND nominal_account_number NOT BETWEEN 741800 AND 741899
        AND nominal_account_number NOT BETWEEN 746000 AND 746999
        AND (nominal_account_number NOT BETWEEN 747000 AND 747999 OR nominal_account_number BETWEEN 747000 AND 747099 OR nominal_account_number BETWEEN 747200 AND 747299))
  )
GROUP BY nominal_account_number
ORDER BY nominal_account_number;
```

### Konto 743001 detailliert:

```sql
SELECT 
    accounting_date,
    debit_or_credit,
    posted_value/100.0 as wert,
    branch_number,
    subsidiary_to_company_ref
FROM loco_journal_accountings
WHERE accounting_date >= '2025-12-01' AND accounting_date < '2026-01-01'
  AND nominal_account_number = 743001
ORDER BY accounting_date, debit_or_credit;
```

---

---

## 📎 ANHANG: CSV-EXPORT

**Datei:** `BWA_MECHANIK_KARO_KONTEN_DEZ2025.csv`

Enthält alle Konten die zu "Mechanik+Karo" gehören (Erlös und Einsatz) mit:
- Typ (Erlös/Einsatz)
- Kontonummer
- Wert in €
- Anzahl Buchungen

**Verwendung:** Import in Excel für direkten Vergleich mit GlobalCube-Kontenliste.

---

**Erstellt für:** Buchhalter Christian  
**Zweck:** Detaillierte Analyse der 3.203,11 € Differenz zwischen DRIVE und GlobalCube  
**Nächster Schritt:** Prüfung der identifizierten Probleme durch Buchhalter  
**Kontakt:** Bei Fragen zur technischen Umsetzung bitte Entwickler kontaktieren
