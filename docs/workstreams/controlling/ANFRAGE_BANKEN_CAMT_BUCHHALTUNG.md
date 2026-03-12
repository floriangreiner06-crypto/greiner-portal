# Anfrage an die Banken: Elektronische Kontoauszüge (CAMT)

**An:** Buchhaltung  
**Betreff:** Was wir bei den Hausbanken beantragen bzw. erfragen sollten  
**Zweck:** DRIVE-Portal soll alle Kontoumsätze automatisch importieren – ohne fehleranfälliges PDF-Parsing. Dafür brauchen wir einheitlich **CAMT**-Dateien von allen Banken.

---

## Hintergrund (kurz)

- **MT940** wird von der Deutschen Kreditwirtschaft nicht mehr angeboten (Abschaltung November 2025).
- **Hypovereinsbank** liefert uns aktuell nur **PDF**-Kontoauszüge → Import ist aufwendig und fehleranfällig (z. B. fehlende Zeilen).
- Die modernen Formate **camt.052 / camt.053 / camt.054** (XML, ISO 20022) werden von allen unseren Hausbanken angeboten und sind für die Automatisierung geeignet.

**Ziel:** Von **allen** Hausbanken die Kontoauszüge im **CAMT-Format** (per EBICS oder Download) beziehen, damit das DRIVE-Portal sie zuverlässig und vollständig importieren kann.

---

## Unsere Hausbanken (zur Einordnung)

| Bank | Konto / Verwendung | Aktuell in DRIVE |
|------|--------------------|-------------------|
| Hypovereinsbank (UniCredit) | Hypovereinsbank KK | PDF-Import (fehleranfällig) |
| Sparkasse | 760036467 | MT940-Dateien (aus Kontoauszüge-Ordner) |
| Genobank (Volksbanken) | 57908 KK, 1501500 HYU KK, 4700057908 (Sollzinsen) | MT940-Dateien |
| VR Bank Landau | 303585 | MT940-Dateien |

---

## Was bei den Banken beantragen / erfragen

### 1. Hypovereinsbank (UniCredit)

**Ansprechpartner:** Geschäftskundenbetreuung / Cash Management (z. B. cashmanagement@unicredit.de)

**Zu beantragen / zu erfragen:**

- Wir möchten für unser **Geschäftskonto (Hypovereinsbank KK)** die **elektronischen Kontoauszüge im CAMT-Format** (camt.053 und ggf. camt.054) statt nur PDF.
- **Frage:** Ist für unser Konto bereits ein **EBICS-Zugang** eingerichtet? Wenn nein: EBICS-Zugang für Geschäftskunden beantragen.
- **Frage:** Welche **EBICS-Auftragsart** bzw. welches **Format** müssen wir für den Abruf von Tagesauszügen (Kontoumsätze) nutzen? (Erwartung: camt.053.001.08 – „C53“ o. ä.)
- **Frage:** Können wir die **CAMT-Dateien (camt.053)** täglich automatisch per EBICS abrufen und in unser Rechenzentrum/unsere Anwendung liefern?
- **Frage:** Gibt es eine **Anleitung oder Checkliste** zur Umstellung von PDF-Auszug auf CAMT-Abruf (Berechtigungen, Software-Voraussetzungen)?

**Was wir brauchen (technisch):**

- EBICS-Zugang (falls noch nicht vorhanden) mit Berechtigung zum **Abruf von Kontoinformationen (camt.052 / camt.053 / camt.054)**.
- Kurzbeschreibung: Welche Dateien liefert die Bank (camt.053 für Tagesauszug, camt.054 für Sammelbuchungen?), in welchem Ordner/auf welchem Weg kommen sie bei uns an (z. B. Ablage im gleichen Netzwerk-Ordner wie bisher die MT940/PDF)?

---

### 2. Sparkasse

**Hinweis:** Die Umsätze für Konto 760036467 erhalten wir aktuell als MT940-Dateien (z. B. aus dem Ordner Kontoauszüge/mt940). Die Banken haben MT940 eingestellt; die Sparkassen stellen auf **camt.053** um.

**Zu erfragen:**

- **Frage:** Liefern Sie uns die Kontoauszüge für unser Geschäftskonto bereits im **CAMT-Format (camt.053.001.08)**? Wenn ja: Über welchen Kanal (EBICS, Online-Banking-Download, anderer Weg)?
- **Frage:** Falls noch nicht umgestellt: Bis wann erfolgt bei unserer Sparkasse die Umstellung von MT940 auf camt.053? Welche **Auftragsart / welches Format** sollen wir künftig nutzen?
- **Frage:** Können die **CAMT-Dateien** an derselben Stelle abgelegt werden wie bisher die MT940-Dateien (z. B. Netzwerk-Ordner für Buchhaltung/DRIVE), oder ist ein anderer Abholweg nötig?

**Was wir brauchen:**

- Kontoauszüge im Format **camt.053.001.08** (oder die von der Sparkasse genannte aktuelle Version).
- Klarheit, wo die Dateien abgelegt werden bzw. wie wir sie automatisiert ins DRIVE-Portal bringen können.

---

### 3. Genobank / Volksbanken (Konten 57908, 1501500, 4700057908)

**Zu erfragen:**

- **Frage:** Werden die elektronischen Kontoauszüge für unsere Geschäftskonten bereits im **CAMT-Format (camt.053.001.08)** bereitgestellt? Über EBICS oder anderen Weg?
- **Frage:** Welche **EBICS-Auftragsart** (z. B. „C53“ für camt.053) müssen wir für den täglichen Abruf der Kontoumsätze verwenden?
- **Frage:** Können wir die **CAMT-Dateien** wie bisher die MT940-Dateien in unserem gemeinsamen Ordner (z. B. Kontoauszüge) ablegen, damit das DRIVE-Portal sie einlesen kann?

**Was wir brauchen:**

- Kontoauszüge im Format **camt.053.001.08** (und ggf. camt.054, falls für Sammelbuchungen genutzt).
- Kurze Bestätigung: Abruf per EBICS mit welcher Auftragsart, Ablage der Dateien wo (Pfad/Verzeichnis).

---

### 4. VR Bank Landau (Konto 303585)

**Zu erfragen:**

- Entspricht der Ablauf der **Genobank/Volksbanken** (siehe oben): CAMT-Format (camt.053), EBICS-Auftragsart, Ablage der Dateien.
- **Frage:** Wird für unser Konto bereits **camt.053** geliefert? Wenn ja: Wo liegen die Dateien? Wenn nein: Ab wann und was müssen wir beantragen?

**Was wir brauchen:**

- Wie bei Genobank: **camt.053.001.08** (oder aktuelle Version der Bank), klare Angabe zum Abruf und Ablageort.

---

## Zusammenfassung: Was wir insgesamt benötigen

| Was | Beschreibung |
|-----|--------------|
| **Format** | Elektronische Kontoauszüge im **CAMT-Format** (camt.053 für Tagesauszüge, ggf. camt.054 für Sammelbuchungen). Konkret: **camt.053.001.08** (ISO 20022, Version 08). |
| **Kanal** | EBICS-Abruf durch die Buchhaltung (oder durch uns, wenn EBICS beim Rechenzentrum/DRIVE-Server läuft) mit der von der Bank genannten Auftragsart (z. B. C53). |
| **Ablage** | Die **CAMT-XML-Dateien** sollen an einer Stelle abgelegt werden, die das DRIVE-Portal lesen kann (z. B. gleicher oder neuer Ordner wie bisher MT940/PDF, z. B. `Kontoauszüge/camt/` oder pro Bank). |
| **Alle Konten** | Alle unsere Hausbanken (Hypovereinsbank, Sparkasse, Genobank, VR Bank Landau) – damit wir **ein** einheitliches Import-Verfahren (CAMT-Parser) im DRIVE-Portal nutzen und auf PDF-Parsing bei der HVB verzichten können. |

---

## Nächste Schritte (Vorschlag)

1. **Buchhaltung** leitet die Anfragen an die jeweiligen Banken (per E-Mail oder über den Kundenbetreuer) und sammelt die Antworten.
2. **IT/DRIVE** richtet nach Klarheit von der Bank einen **CAMT-Import** im Portal ein (Parser für camt.053/camt.054, Ablageordner, ggf. EBICS-Anbindung falls bei uns).
3. **Gemeinsam:** Einmaliger Test mit echten CAMT-Dateien einer Bank; danach schrittweise Umstellung aller Konten.

---

**Stand:** März 2026  
**Kontakt bei Rückfragen:** [interner Ansprechpartner IT/Controlling]
