# TEK DB1-Abweichung: Drive vs. Globalcube — Analyse

**Stand:** 2026-02-13  
**Workstream:** Controlling  
**Ausgangslage:** Erlöse/Umsätze zwischen Drive-TEK und Referenzsystem Globalcube stimmen überein; **DB1 weicht ab.**  
**Auftrag:** Abweichung identifizieren, noch keine Code-Änderungen.

---

## 1. Hinweis zu den angehängten PDFs

Die genannten Dateien  
`TEK_20260212.pdf` (Drive) und  
`F.04 Tägliche Erfolgskontrolle KST.pdf` (Globalcube)  
liegen unter Windows-Pfaden (`C:\Users\...\Temp\...`) und sind im Projekt/auf dem Server nicht zugreifbar.  
Die folgende Analyse basiert auf:

- **Code:** TEK-Datenquelle und DB1-Berechnung in Drive
- **Bestehende Doku:** `docs/TEK_VERGLEICH_GLOBALCUBE_METABASE_NW_DEG_OPEL.md`

Für eine zahlenmäßige Prüfung bitte entweder die konkreten Werte (z. B. pro Bereich: Umsatz, Einsatz, DB1) aus beiden PDFs hier eintragen oder die PDFs auf den Server legen.

---

## 2. Definition DB1 (beide Systeme)

- **DB1 = Umsatz (Erlöse) − Einsatz**
- Wenn **Umsatz gleich** ist und **DB1 unterschiedlich** → die Differenz kommt ausschließlich aus dem **Einsatz**.

Damit ist die Abweichung eine **Einsatz-Abweichung** (andere Konten, andere Filter oder andere Zeit-/Buchungslogik).

---

## 3. Wie Drive die TEK (und damit DB1) berechnet

### 3.1 Datenquelle

- **TEK-Web-UI und TEK-PDF/Report:** `api/controlling_data.get_tek_data()`
- **Datenbank:** Locosoft, Tabelle `loco_journal_accountings`
- **Zeit:** `accounting_date` (Buchungsdatum), Monat `von`/`bis`

### 3.2 Umsatz (Erlöse) in get_tek_data

- **Konten:**  
  - 800.000–889.999  
  - 893.200–893.299 (Sonderumsatz)
- **Bereiche:** 81→1-NW, 82→2-GW, 83→3-Teile, 84→4-Lohn, 86→5-Sonst
- **Buchungslogik:** Haben (H) positiv, Soll (S) negativ
- **Filter:** `firma_filter_umsatz` (branch_number / subsidiary_to_company_ref), optional Umlage-Erlöse ausschließen
- **G&V-Filter:** **wird nicht angewendet** (kein `get_guv_filter()` in `controlling_data.py`)

### 3.3 Einsatz in get_tek_data

- **Konten:** 700.000–799.999, aufgeteilt in:
  - 71xxxx → 1-NW  
  - 72xxxx → 2-GW  
  - 73xxxx → 3-Teile  
  - 74xxxx → 4-Lohn  
  - 76xxxx → 5-Sonst  
  - (75xxxx und andere 70–79 → „9-Andere“, in der TEK-Auswertung nicht als eigener Bereich geführt)
- **Buchungslogik:** Soll (S) positiv, Haben (H) negativ
- **Filter:** nur `firma_filter_umsatz` (gleiche Standort-/Firmenlogik wie Umsatz)
- **G&V-Filter:** **wird nicht angewendet**
- **Konto 743002:** **wird nicht ausgeschlossen** (743002 „EW Fremdleistungen für Kunden“ ist in 74xxxx und geht voll in 4-Lohn-Einsatz ein)

### 3.4 Besonderheit 4-Lohn (laufender Monat)

- Im **laufenden Monat** verwendet Drive für 4-Lohn **keinen** reinen FIBU-Einsatz, sondern einen **kalkulatorischen Einsatz** (6-Monats-Quote):
  - Einsatz_kalk = Umsatz_aktuell × (Einsatz_6M / Umsatz_6M)
  - DB1 und Marge 4-Lohn werden daraus berechnet.
- Grund: FIBU-Einsatz 74xxxx kommt oft mit Verzögerung; ohne Kalkulation wäre die Marge im laufenden Monat verzerrt.

### 3.5 DB1 in Drive

- Pro Bereich: `DB1 = Umsatz − Einsatz` (mit obigen Umsatz-/Einsatz-Definitionen).
- Gesamt-DB1 = Summe der Bereichs-DB1 (bzw. Gesamt-Umsatz − Gesamt-Einsatz).

---

## 4. Vergleich: BWA in Drive vs. TEK in Drive

Die **BWA** (`controlling_api._berechne_bwa_werte` bzw. vergleichbare Routen) nutzt:

- **G&V-Filter:** `get_guv_filter()` für Umsatz und Einsatz (G&V-Abschlussbuchungen werden ausgeschlossen).
- **Einsatz:** gleicher Kontenbereich 700.000–799.999, **aber** Konto **743002 wird ausgeschlossen**.

Die **TEK** (`get_tek_data`) nutzt:

- **keinen** G&V-Filter,
- **keinen** 743002-Ausschluss.

→ Allein dadurch kann der **Einsatz** in der TEK höher sein als in der BWA (wenn 743002 und/oder G&V-Buchungen ins Spiel kommen), damit **DB1 in der TEK niedriger** (oder negativer) als in der BWA/Globalcube.

---

## 5. Mögliche Ursachen für DB1-Abweichung (Drive TEK vs. Globalcube)

| Nr. | Ursache | Erklärung | Wirkung auf DB1 (Drive vs. Referenz) |
|-----|--------|-----------|--------------------------------------|
| 1 | **Konto 743002** | Globalcube schließt 743002 (EW Fremdleistungen für Kunden) vermutlich aus dem Einsatz aus; Drive TEK nicht. | Drive: höherer Einsatz → **niedrigerer DB1** |
| 2 | **G&V-Abschlussbuchungen** | Drive TEK schließt G&V-Abschluss nicht aus; wenn Globalcube das tut, unterscheiden sich die Einsatz-Werte. | Je nach Vorzeichen der G&V-Einsatz-Buchungen: Drive DB1 kann abweichen (meist **niedriger** wenn G&V-Einsatz positiv gebucht wird). |
| 3 | **4-Lohn im laufenden Monat** | Drive nutzt kalkulatorischen Einsatz (6-Monats-Quote); Globalcube ggf. reinen FIBU-Einsatz oder andere Methode. | Differenz vor allem bei **4-Lohn** und damit im **Gesamt-DB1**. |
| 4 | **Konten-Abgrenzung Einsatz** | Unterschiede bei 75xxxx, 77–79xxxx oder Randkonten (inkl. „9-Andere“). | Mögliche Differenz je nach Zuordnung in Globalcube. |
| 5 | **Zeitbasis** | Beide nutzen Buchungsdatum; wenn Globalcube an einer Stelle Rechnungsdatum oder anderes Datum nutzt, können Umsatz/Einsatz verschoben sein. | Würde i. d. R. auch Umsatz betreffen; da Umsatz gleich ist, eher unwahrscheinlich, aber prüfbar. |
| 6 | **Datenquelle / Zeitstand** | Drive nutzt Portal-Spiegel `loco_journal_accountings`; Globalcube ggf. Locosoft direkt oder anderen Sync. Spiegel kann zeitverzögert oder anders befüllt sein. | Wenn Globalcube z. B. im Februar Werte hat und der Spiegel 0: Abweichung erklärt sich aus Datenquelle, nicht aus 743002-Logik. |

---

## 6. Empfohlene Schritte zur genauen Identifikation

1. **Zahlen aus beiden PDFs übernehmen**  
   Pro Bereich (1-NW, 2-GW, 3-Teile, 4-Lohn, 5-Sonst) und Gesamt:
   - Umsatz, Einsatz, DB1 (und ggf. DB1 %)  
   So sieht man, in welchem Bereich die DB1-Differenz entsteht.

2. **Globalcube-Definition klären**  
   - Welche Konten zählen zum „Einsatz“ (nur 71–76xxxx oder auch 75/77–79)?  
   - Wird **743002** aus dem Einsatz ausgeschlossen?  
   - Werden **G&V-Abschlussbuchungen** beim Einsatz (und ggf. Umsatz) ausgeschlossen?  
   - Wie wird **4-Lohn** im laufenden Monat berechnet (reiner FIBU-Einsatz oder kalkulatorisch)?

3. **Locosoft prüfen**  
   - Volumen auf **743002** im betrachteten Monat (Einsatz-Differenz ≈ dieses Volumen, wenn Globalcube 743002 weglässt).  
   - G&V-Abschlussbuchungen im Monat (posting_text LIKE ‚%G&V-Abschluss%‘) für Umsatz- und Einsatz-Konten.

4. **Anpassung Drive (nach Festlegung)**  
   - Wenn Globalcube 743002 und G&V ausschließt: TEK (`get_tek_data`) an BWA-Logik annähern (G&V-Filter + 743002-Ausschluss beim Einsatz).  
   - 4-Lohn: nur anpassen, wenn gewollt ist, dass Drive im laufenden Monat wie Globalcube (z. B. reiner FIBU-Einsatz) rechnet.

---

## 7. Kurzfassung

- **Erlöse/Umsätze gleich, DB1 unterschiedlich** → Abweichung liegt im **Einsatz**.
- In Drive berechnet die **TEK** den Einsatz inzwischen **mit** G&V-Filter und **mit** Ausschluss von **743002** (wie BWA).
- **Mögliche Ursachen (nicht nur 743002):** (1) 743002-Abgrenzung, (2) G&V-Abschluss, (3) 4-Lohn-Logik (kalk. vs. FIBU), (4) Konten-Abgrenzung (75/77–79xxxx), (5) **unterschiedliche Datenquelle/Zeitstand** (s. u.).

---

## 8. Abfrage-Vergleich Locosoft vs. Portal (2026-02-13)

**Skript:** `scripts/vergleiche_tek_locosoft_vs_portal_feb2026.py`  
**Ergebnis für Februar 2026 (2026-02-01 bis 2026-03-01):**

| Kennzahl | Locosoft | Portal | Diff |
|----------|----------|--------|------|
| 743002 Saldo (€) | 0,00 | 0,00 | 0 |
| 743002 Buchungsanzahl | 0 | 0 | 0 |
| Einsatz 70–79 gesamt (€) | 872.023,08 | 872.023,08 | 0 |
| Einsatz ohne 743002 (€) | 872.023,08 | 872.023,08 | 0 |
| Einsatz mit G&V-Filter (€) | 872.023,08 | 872.023,08 | 0 |
| Umsatz 80–88/8932 (€) | 1.073.030,17 | 1.073.030,17 | 0 |
| DB1 (Umsatz − Einsatz mit G&V) (€) | 201.007,09 | 201.007,09 | 0 |

**Fazit:** Datenquelle ist identisch; Locosoft und Portal-Spiegel stimmen für Februar 2026 exakt überein. 743002 ist in **beiden** 0 (keine Buchungen im Februar). Die DB1-Abweichung zwischen Drive-TEK und Globalcube kommt daher **nicht** von unterschiedlichen Rohdaten und **nicht** von 743002, sondern von **unterschiedlicher Auswertungslogik** (Konten-Abgrenzung, 4-Lohn kalkulatorisch vs. FIBU, Filter oder Darstellung in Globalcube). Nächster Schritt: Einsatz/Umsatz **pro Bereich oder pro Konto** in Globalcube mit Drive abgleichen, um die abweichende Definition zu finden.
