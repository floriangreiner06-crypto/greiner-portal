# Testanleitung: Serviceberater Controlling – Offene Aufträge

**Für:** Edith (Serviceassistenz)  
**Rolle in DRIVE:** Serviceleiter  
**Stand:** 2026-02-26  
**Workstream:** Werkstatt

**Als PDF:** (1) Auf dem Server: `python scripts/export_doc_to_pdf.py docs/workstreams/werkstatt/TESTANLEITUNG_EDITH_OFFENE_AUFTRAEGE.md` – erzeugt dieselbe PDF wie im Reporting (Reportlab). (2) Alternativ: `TESTANLEITUNG_EDITH_OFFENE_AUFTRAEGE.html` im Browser öffnen → Strg+P → „Als PDF speichern“.

---

## 1. Kurzes Onboarding – DRIVE zum ersten Mal

### 1.1 Was ist DRIVE?

DRIVE ist das interne Portal des Autohauses Greiner. Du arbeitest weiterhin mit **Locosoft**; DRIVE zeigt ausgewählte Daten aus Locosoft (und anderen Quellen) gebündelt im Browser – u. a. **offene Aufträge** pro Serviceberater, damit die Übersicht nicht nur aus den gewohnten Locosoft-PDFs kommt.

### 1.2 Zugang

- **Adresse im Firmennetz:** **http://drive** (im Browser eintippen, keine „www“).
- **Login:** Deine üblichen Windows-/Netzwerk-Daten (wie am PC).
- Nach dem Login siehst du die Startseite und das Menü links bzw. oben (je nach Ansicht).

### 1.3 Deine Rechte als Serviceleiter

Mit der Rolle **Serviceleiter** kannst du u. a.:

- **Serviceberater Controlling** öffnen (Übersicht aller Serviceberater mit Tagesziel und offenen Aufträgen),
- pro Serviceberater die **offenen Aufträge** anzeigen und mit Locosoft vergleichen,
- **Werkstatt Live** nutzen (offene Aufträge, gefiltert nach Serviceberater).

Wenn du einen Menüpunkt nicht siehst, bitte kurz melden – dann prüfen wir die Zuordnung deiner Rolle.

---

## 2. Wo finde ich „Serviceberater Controlling“ und „Offene Aufträge“?

### 2.1 Serviceberater Controlling (Übersicht aller SB)

- Im Menü: **Service** (oder **After Sales**) → **Serviceberater** / **Serviceberater Controlling**.
- **Direkt-URL:** `http://drive/aftersales/serviceberater`

Dort siehst du eine **Tabelle** mit allen konfigurierten Serviceberater:innen:

- Name  
- Heute fakturiert / Ziel / Heute %  
- **Offene Aufträge** (Anzahl, klickbar)  
- Status (Auf Kurs / Knapp / Kritisch)

### 2.2 Offene Aufträge für einen einzelnen Serviceberater

**Variante A – aus der Tabelle:**

- In der Spalte **„Offene Aufträge“** auf die **Zahl** klicken (z. B. „18“).
- Es öffnet sich **Werkstatt Live** – nur mit den offenen Aufträgen **dieses** Serviceberaters (es erscheint ein Hinweis „Nur: [Name]“).

**Variante B – Option „Ohne Bring-Termin in der Zukunft“:**

- In der gleichen Tabelle gibt es die Checkbox **„Ohne Bring-Termin in der Zukunft“**.
- Wenn du sie **anklickst**, werden nur Aufträge gezählt/angezeigt, bei denen der **Bring-Termin** in Locosoft bereits in der Vergangenheit oder heute liegt (keine „vorbereiteten“ mit Bring-Termin in der Zukunft).
- Die Zahlen in der Tabelle und der Link auf „Werkstatt Live“ beziehen sich dann auf diese gefilterte Sicht – vergleichbar mit deinen Locosoft-Auswertungen „ohne vorbereitete Aufträge“.

**Variante C – Mein Bereich (wenn du als ein SB eingeloggt wärst):**

- Unter **Mein Bereich** gibt es den Block **„Offene Aufträge“** mit Anzahl, Option **„Ohne Bring-Termin in der Zukunft“** und **„Alle anzeigen“**.
- **„Alle anzeigen“** führt ebenfalls in **Werkstatt Live**, gefiltert auf diesen einen Serviceberater.

---

## 3. Vergleich DRIVE vs. Locosoft – was du prüfen sollst

Bitte vergleiche die **offenen Aufträge** in DRIVE mit den **entsprechenden Listen/PDFs aus Locosoft** (z. B. „Liste unberechneter Aufträge“ pro Serviceberater, mit gleichem Bring-Termin-Filter wie in DRIVE).

### 3.1 Zuordnung zum Serviceberater

- **Prüfung:** Gehören in DRIVE unter „Nur: [Name]“ wirklich nur Aufträge zu diesem Serviceberater?
- **In Locosoft:** Gleiche Auswahl (Annahme-Mitarbeiter / order_taking_employee_no) und gleicher Filter „Bring-Termin“ (z. B. nur vergangen/heute).
- **Rückmeldung:** Stimmt die Zuordnung? Falls ein Auftrag in DRIVE einem anderen SB zugeordnet ist als in Locosoft, bitte Auftragsnummer + SB in DRIVE vs. SB in Locosoft notieren.

### 3.2 AVG (Auftragsverzögerungsgrund)

- **Prüfung:** Zeigt DRIVE den gleichen **AVG-Code** bzw. die gleiche **AVG-Beschreibung** wie Locosoft für die offenen Aufträge?
- **In Locosoft:** z. B. „Teile bestellt“, „Termin bereits vereinbart“, „zur Terminvereinbarung“, „Warten auf Freigabe“ usw.
- **Rückmeldung:** Sind die AVG-Angaben konsistent? Abweichungen (Auftragsnr. + AVG in DRIVE vs. Locosoft) bitte vermerken.

### 3.3 Werte in EUR – Arbeit (Lohn) und Teile

- **Prüfung:** In DRIVE siehst du bei der gefilterten Ansicht (ein SB, ggf. „Ohne Bring-Termin in der Zukunft“) die **Summen**:
  - **Summe Lohn** (Arbeitswert),
  - **Summe Teile** (Ersatzteile VK),
  - **Gesamt**.
- **In Locosoft:** Entsprechende Summen aus der „Übersicht unfakturierter Aufträge“ (Arb. Wert in EUR, ET VK in EUR, Gesamtsummen).
- **Rückmeldung:** Stimmen die Beträge in EUR (gerundet) mit Locosoft überein? Wenn nicht: welche Abweichung (z. B. „DRIVE Summe Lohn 6.342 €, Locosoft 6.290 €“) und für welchen Serviceberater/Filter?

---

## 4. Checkliste für dein Feedback

Du kannst diese Punkte abhaken und kurz kommentieren:

| Nr. | Prüfpunkt | Erledigt? | Anmerkung |
|-----|-----------|-----------|-----------|
| 1 | DRIVE-Login und Menü gefunden | ☐ | |
| 2 | Serviceberater Controlling geöffnet | ☐ | |
| 3 | Spalte „Offene Aufträge“ und Klick auf Zahl getestet | ☐ | |
| 4 | „Ohne Bring-Termin in der Zukunft“ getestet (Anzahl/Summen) | ☐ | |
| 5 | Zuordnung zum SB: DRIVE = Locosoft? | ☐ | |
| 6 | AVG in DRIVE = Locosoft? | ☐ | |
| 7 | Summe Lohn / Summe Teile / Gesamt = Locosoft? | ☐ | |
| 8 | Sonstiges Feedback (Bedienung, Darstellung, Wünsche) | ☐ | |

---

## 5. An wen geht das Feedback?

Bitte dein Feedback (inkl. Checkliste und ggf. Screenshots/Notizen zu Abweichungen) an Florian bzw. das Team geben, das das Portal betreut. Bei Unklarheiten oder fehlenden Rechten einfach melden.

---

## 6. Kurz: Wo liegen die Locosoft-Referenzen?

- Deine gewohnten **Locosoft-PDFs** (z. B. „Liste unberechneter Aufträge“, pro SB, mit Bringtermin-Filter) bleiben die Referenz.
- **DRIVE** zeigt dieselben Daten (aus der gleichen Locosoft-Datenbank), damit du sie im Browser prüfen und mit den PDFs abgleichen kannst.

Vielen Dank für deine Mithilfe beim Test.
