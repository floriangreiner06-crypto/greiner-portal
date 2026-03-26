# Kosten-Budget pro Konto (unterjährige Planung)

**Frage:** Können wir Kosten ermitteln und hochrechnen (unterjährig planen), z.B. Mittelwert aus aktuell und Vorjahr, sodass am Ende **für jedes Konto ein Budget** vorliegt?

**Kurzantwort:** Ja, mit der bestehenden Datengrundlage machbar.

---

## Datengrundlage

- **Quelle:** `loco_journal_accountings` (Portal-DB, gespiegelt aus Locosoft).
- **Kostenkonten:** Wie in der BWA (vgl. `docs/BWA_KONTEN_MAPPING_FINAL.md`):
  - **Variable Kosten:** 4151xx, 4355xx, 455xx–456xx (KST 1–7), 4870x (KST 1–7), 491xx–4978xx
  - **Direkte Kosten:** 400000–489999, 5. Ziffer 1–7, ohne die variablen Bereiche
  - **Indirekte Kosten:** 4xxxxx mit 5. Ziffer 0, 424xx/438xx (bestimmte KST), 498xxx–499999, 891xxx–896xxx (ohne 8932xx)
- **Bereits vorhanden:** Im BWA v2 Drilldown (`/api/controlling/bwa/v2/drilldown`, typ=direkte/indirekte/variable) wird **pro Konto** (nominal_account_number) summiert – gleiche Logik nutzbar.

Damit können wir **pro Kostenkonto** aus `loco_journal_accountings` auslesen:
- **Vorjahr (VJ):** Summe über das komplette Geschäftsjahr (z.B. 2024/25 = Sep 24 – Aug 25).
- **Aktuell (IST YTD):** Summe von GJ-Start bis zum letzten abgeschlossenen Monat (Buchungsschluss 5. Werktag wie im Unternehmensplan).

---

## Vorschlag: Mittelwert aus Vorjahr und hochgerechnetem IST

Unterjährig haben wir:
- **VJ:** vollständiges Jahr pro Konto → `VJ_k`
- **IST YTD:** nur die bisher abgelaufenen Monate → `IST_ytd_k`

**Hochrechnung aktuelles Jahr (linear):**
- Abgelaufene GJ-Monate = z.B. 6 (Sep–Feb).
- Hochgerechnetes Jahr = `IST_ytd_k * 12 / 6` (bei 6 Monaten).

**Budget pro Konto (Mittelwert):**
```text
Budget_k = (VJ_k + (IST_ytd_k * 12 / Monate_abgelaufen)) / 2
```
- So entsteht ein **Jahresbudget pro Konto**, das Vorjahr und aktuellen Lauf berücksichtigt.
- Alternative (ohne Mittelwert): nur Hochrechnung `Budget_k = IST_ytd_k * 12 / Monate_abgelaufen` oder nur VJ `Budget_k = VJ_k` – je nach gewünschter Logik.

**Monatsbudget (falls benötigt):**
- `Monatsbudget_k = Budget_k / 12` für Vergleich IST vs. Plan pro Monat.

---

## „Am Ende für jedes Konto ein Budget“

- **Rechenebene:** Für jedes **Kostenkonto** mit Buchungen in VJ und/oder IST YTD: ein Wert **Budget_k** (und optional VJ_k, IST_ytd_k, hochgerechnet_k zur Nachvollziehbarkeit).
- **Speicherung:** Noch nicht umgesetzt. Mögliche Wege:
  1. **Neue Tabelle** z.B. `konto_budget` (geschaeftsjahr, standort, konto, budget_jahr, vj_jahr, ist_ytd, berechnungsart, erstellt_am) – dann Abgleich IST vs. Budget pro Konto möglich.
  2. **Report/Export:** Script oder API erzeugt einmalig eine Liste/CSV (Konto, Bezeichnung, VJ, IST_ytd, hochgerechnet, Budget) ohne persistente Tabelle.
- **Standort/Firma:** Wie in der BWA: Filter nach Firma/Standort (subsidiary_to_company_ref, branch_number, 5./6. Ziffer) – dann **pro Standort** ein eigenes Budget pro Konto möglich.

---

## Zusammenfassung

| Punkt | Status |
|-------|--------|
| Daten pro Konto (VJ + IST YTD) | ✅ Aus `loco_journal_accountings` mit bestehender BWA-Kostenlogik |
| Hochrechnung IST auf 12 Monate | ✅ Formel: IST_ytd * 12 / Monate_abgelaufen |
| Mittelwert (VJ + Hochrechnung) | ✅ Formel: (VJ + Hochrechnung) / 2 |
| Ergebnis „ein Budget pro Konto“ | ✅ Berechenbar; Speicherung/Report optional (Tabelle oder Export) |

---

## Ergebnis-Prognose mit aktuellen Daten (Script)

Das Script **`scripts/planung_ergebnis_aus_aktuellen_daten.py`** rechnet mit den vorhandenen IST-Daten (Unternehmensplan-Logik) durch:

- **Umsatz/DB1 Plan:** YTD aktuelles GJ × 12 / abgelaufene Monate (Hochrechnung)
- **Kosten-Budget:** Mittelwert (VJ-Kosten + hochgerechnete YTD-Kosten); falls VJ fehlt: nur Hochrechnung
- **Ergebnis = Plan-DB1 − Kosten-Budget**, Rendite = Ergebnis / Plan-Umsatz

Ausführung: `python3 scripts/planung_ergebnis_aus_aktuellen_daten.py`

**VJ-Daten:** Das Script lädt das Vorjahr zuerst aus der **Portal-DB** (`loco_journal_accountings` = gespiegelte Locosoft-Konten). So werden die **Kosten aus den Locosoft-Konten** für VJ genutzt; nur wenn das Portal für VJ leer ist, wird die Unternehmensplan-API (Locosoft live) verwendet. Eine **GlobalCube Planungs-Excel mit VJ-Werten** liegt unter `docs/workstreams/planung/` (bzw. Windows: `F:\Greiner Portal\...\Server\docs\workstreams\planung`) und dient als Referenz/Abgleich; die Planung stammt aus GlobalCube und ist nicht durch uns freigegeben (Ziel: GlobalCube durch DRIVE ersetzen).
